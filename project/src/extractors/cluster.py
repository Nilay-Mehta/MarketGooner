import math
import re
import asyncio
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import random
from pydantic import BaseModel, Field
from src.key_manager import KeyManager
from src.storage import db
from src.config import RANK_SEMAPHORE_LIMIT

class CoherenceCheck(BaseModel):
    coherent: bool = Field(..., description="True if the pain points are all about the same underlying problem")
    dominant_theme: str = Field(..., description="A concise 3-6 word label describing the dominant theme")
    outliers: List[int] = Field(..., description="List of pain point IDs that do not match the dominant theme")


MIN_CLUSTER_SIZE = 8  # Floor enforced by both BERTopic and TF-IDF paths


class ProblemClusterer:
    """
    Stage 2 Extractor: Clusters related pain points using BERTopic (sklearn HDBSCAN)
    or a TF-IDF greedy fallback. Both paths enforce MIN_CLUSTER_SIZE.

    Logging contract:
      - Prints exactly one routing line before fit_transform:
          [BERTopic] Clustering with BERTopic (sklearn HDBSCAN, min_topic_size=5)
        OR
          [TF-IDF]   Clustering with TF-IDF fallback because <reason>
      - Never silently swallows an ImportError on BERTopic.
    """

    def __init__(self, key_manager: Optional[KeyManager] = None, db_path: str = db.DEFAULT_DB_PATH):
        self.km = key_manager or KeyManager()
        self.db_path = db_path
        self.semaphore = asyncio.Semaphore(RANK_SEMAPHORE_LIMIT)

    # -------------------------------------------------------------------------
    # Tokenizer helper
    # -------------------------------------------------------------------------
    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-z0-9_]{3,}\b', text.lower())
        stopwords = {
            "the", "and", "for", "with", "this", "that", "have", "from", "they", "will",
            "would", "there", "their", "what", "about", "which", "when", "make", "like",
            "time", "just", "know", "take", "people", "into", "year", "your", "good",
            "some", "could", "them", "other", "than", "then", "now", "look", "only", "come",
            "its", "over", "think", "also", "back", "after", "use", "two", "how", "our",
            "work", "first", "well", "way", "even", "new", "want", "because", "any", "these",
            "give", "day", "most", "us"
        }
        return [w for w in words if w not in stopwords]

    def _compute_cosine_sim(self, text1: str, text2: str) -> float:
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        if not tokens1 or not tokens2:
            return 0.0
        vec1 = Counter(tokens1)
        vec2 = Counter(tokens2)
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum(vec1[x] * vec2[x] for x in intersection)
        sum1 = sum(v ** 2 for v in vec1.values())
        sum2 = sum(v ** 2 for v in vec2.values())
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        return float(numerator) / denominator

    # -------------------------------------------------------------------------
    # Main entry point
    # -------------------------------------------------------------------------

    async def _check_coherence_async(self, cluster_pains: List[Dict[str, Any]]) -> CoherenceCheck:
        sample_size = len(cluster_pains)
        sample_pains = random.sample(cluster_pains, min(sample_size, len(cluster_pains)))
        pain_text = "\n".join([f"ID: {p['id']}, Summary: {p.get('summary', '')}" for p in sample_pains])
        prompt = f"Here are {len(sample_pains)} randomly sampled pain summaries from a cluster.\n\n{pain_text}\n\nQuestion: Is there a specific, actionable dominant problem/theme across these summaries? REJECT the cluster (set coherent=false) if ANY 2 of the sampled pains are about clearly different domains. The dominant_theme MUST be highly specific (3+ words) and reference a specific product, domain, or workflow. Broad themes like 'Cost and Complexity' are unacceptable and should trigger coherent=false. If it is a garbage bag of unrelated issues, or if the theme is too broad/generic, set coherent=false.\nAnswer strictly in JSON with coherent (true/false), dominant_theme (str), and outliers (list of IDs)."
        system_prompt = "You are a strict B2B SaaS Venture Architect acting as a semantic coherence judge."
        try:
            async with self.semaphore:
                res = await asyncio.to_thread(
                    self.km.generate_structured,
                    prompt=prompt,
                    response_model=CoherenceCheck,
                    system_prompt=system_prompt,
                    task_type="coherence"
                )
            return res
        except Exception as e:
            print(f"[!] Coherence check failed: {e}")
            return CoherenceCheck(coherent=False, dominant_theme="Error", outliers=[])

    def _check_coherence(self, cluster_pains: List[Dict[str, Any]]) -> CoherenceCheck:
        return asyncio.run(self._check_coherence_async(cluster_pains))


    def cluster_pain_points(
        self,
        similarity_threshold: float = 0.35,
        method: str = "bertopic",
        recluster: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Clusters pain points in SQLite, updates the clusters table with metrics
        (including first_seen/last_seen from raw_items.created_utc), and assigns
        cluster_id to each pain point. Both clustering paths enforce MIN_CLUSTER_SIZE.
        """
        if recluster:
            with db.get_db(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clusters")
                cursor.execute("DELETE FROM ideas")
                cursor.execute("UPDATE pain_points SET cluster_id = NULL")
                conn.commit()
            all_pains = db.get_all_pain_points(db_path=self.db_path)
        else:
            with db.get_db(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT
                    p.*,
                    r.source,
                    r.url,
                    COALESCE(NULLIF(r.created_utc, 0), r.fetched_at) as created_utc
                FROM pain_points p
                JOIN raw_items r ON p.raw_item_id = r.id
                WHERE p.cluster_id IS NULL
                ORDER BY p.id ASC
                """)
                all_pains = [dict(r) for r in cursor.fetchall()]

        if not all_pains:
            return []

        clusters_map: List[List[Dict[str, Any]]] = []
        clustering_path = "unknown"

        # ------------------------------------------------------------------
        # Path 1: BERTopic (sklearn HDBSCAN — NOT the hdbscan package which
        #          is DLL-blocked by Application Control on this machine).
        # FAIL LOUD on ImportError — never silently fall back.
        # ------------------------------------------------------------------
        if method == "bertopic":
            if len(all_pains) < MIN_CLUSTER_SIZE * 2:
                reason = f"only {len(all_pains)} pains, need >= {MIN_CLUSTER_SIZE * 2} for BERTopic"
                print(f"[TF-IDF] Clustering with TF-IDF fallback because {reason}")
                clustering_path = "tfidf"
            else:
                try:
                    from sklearn.cluster import HDBSCAN as SklearnHDBSCAN
                    from bertopic import BERTopic
                    clustering_path = "bertopic"
                    
                    print("[BERTopic] Attempt 1 (nr_topics=None, min_topic_size=8)")
                    hdbscan_model = SklearnHDBSCAN(min_cluster_size=8, metric='euclidean', cluster_selection_method='eom')
                    topic_model = BERTopic(hdbscan_model=hdbscan_model, min_topic_size=8, nr_topics=None, calculate_probabilities=False, verbose=False)
                    clusters_map = self._cluster_bertopic(all_pains, topic_model)
                    print(f"[BERTopic] Attempt 1 formed {len(clusters_map)} raw topics.")
                    
                    if len(clusters_map) < 8:
                        print("[BERTopic] Attempt 2 (nr_topics=None, min_topic_size=5)")
                        hdbscan_model = SklearnHDBSCAN(min_cluster_size=5, metric='euclidean', cluster_selection_method='eom')
                        topic_model = BERTopic(hdbscan_model=hdbscan_model, min_topic_size=5, nr_topics=None, calculate_probabilities=False, verbose=False)
                        clusters_map = self._cluster_bertopic(all_pains, topic_model)
                        print(f"[BERTopic] Attempt 2 formed {len(clusters_map)} raw topics.")
                    
                    if len(clusters_map) > 60:
                        print("[BERTopic] Attempt 3 (nr_topics=30, min_topic_size=8)")
                        hdbscan_model = SklearnHDBSCAN(min_cluster_size=8, metric='euclidean', cluster_selection_method='eom')
                        topic_model = BERTopic(hdbscan_model=hdbscan_model, min_topic_size=8, nr_topics=30, calculate_probabilities=False, verbose=False)
                        clusters_map = self._cluster_bertopic(all_pains, topic_model)
                        print(f"[BERTopic] Attempt 3 formed {len(clusters_map)} raw topics.")
                except ImportError as e:
                    # FAIL LOUD — operator must know BERTopic is broken
                    raise RuntimeError(
                        f"[FATAL] BERTopic/sklearn import failed — cannot cluster. "
                        f"Fix the dependency before re-running. Error: {e}"
                    ) from e
                except Exception as e:
                    # Non-import runtime error: log and fall back
                    print(f"[TF-IDF] Clustering with TF-IDF fallback because BERTopic runtime error: {e}")
                    clustering_path = "tfidf"
                    clusters_map = []

        # ------------------------------------------------------------------
        # Path 2: TF-IDF greedy fallback (also enforces MIN_CLUSTER_SIZE)
        # ------------------------------------------------------------------
        if not clusters_map:
            if clustering_path != "tfidf":
                print(f"[TF-IDF] Clustering with TF-IDF fallback because method='{method}' selected")
                clustering_path = "tfidf"
            raw_map = self._cluster_tfidf(all_pains, similarity_threshold)
            clusters_map = self._enforce_min_size(raw_map)

        print(f"[cluster] Path used: {clustering_path} | Raw groups: {len(clusters_map)}")

        # ------------------------------------------------------------------
        # Score & persist each cluster
        # ------------------------------------------------------------------

        saved_clusters = []
        touched_cluster_ids = []
        
        valid_clusters = [c for c in clusters_map if c]
        
        async def _process_all():
            tasks = [self._check_coherence_async(c) for c in valid_clusters]
            results = await asyncio.gather(*tasks)
            return results
            
        coherence_results = asyncio.run(_process_all())

        for cluster_pains, coherence_res in zip(valid_clusters, coherence_results):
            if coherence_res:
                outlier_ids = set(coherence_res.outliers)
            else:
                outlier_ids = set()

            filtered_pains = [p for p in cluster_pains if p["id"] not in outlier_ids]
            
            size = len(filtered_pains)
            if size == 0:
                continue

            distinct_sources = set(p.get("source", "unknown") for p in filtered_pains)
            source_diversity = len(distinct_sources)

            created_times = [
                p.get("created_utc") for p in filtered_pains
                if p.get("created_utc") and int(p.get("created_utc", 0)) > 0
            ]
            first_seen = int(min(created_times)) if created_times else None
            last_seen = int(max(created_times)) if created_times else None

            severity_weights = {"annoyance": 1.0, "blocker": 3.0, "financial_bleed": 5.0}
            total_sev = sum(severity_weights.get(p.get("severity", "annoyance"), 1.0) for p in filtered_pains)
            avg_severity = round(total_sev / size, 2) if size > 0 else 0.0

            wtp_count = sum(
                1 for p in filtered_pains
                if p.get("wtp_type") not in ["unknown", "Unknown", None, ""]
            )

            label = coherence_res.dominant_theme if coherence_res else "Auto-Cluster (Fallback)"
            status = "active" if (coherence_res and coherence_res.coherent) or not coherence_res else "incoherent"

            cluster_id = db.upsert_cluster(
                label=label,
                size=size,
                first_seen=first_seen,
                last_seen=last_seen,
                source_diversity=source_diversity,
                avg_severity_score=avg_severity,
                wtp_evidence_count=wtp_count,
                status=status,
                db_path=self.db_path
            )
            touched_cluster_ids.append(cluster_id)

            for p in filtered_pains:
                db.update_pain_cluster(pain_id=p["id"], cluster_id=cluster_id, db_path=self.db_path)

            for outlier_id in outlier_ids:
                db.update_pain_cluster(pain_id=outlier_id, cluster_id=None, db_path=self.db_path)

            saved_clusters.append({
                "id": cluster_id,
                "label": label,
                "size": size,
                "source_diversity": source_diversity,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "avg_severity_score": avg_severity,
                "wtp_evidence_count": wtp_count,
                "pains": filtered_pains,
                "status": status
            })

        # ------------------------------------------------------------------
        # Bug #5 fix: UPDATE first_seen/last_seen from the JOIN in DB
        # (catches cases where created_utc was missing at clustering time)
        # ------------------------------------------------------------------
        if touched_cluster_ids:
            with db.get_db(self.db_path) as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" * len(touched_cluster_ids))
                cursor.execute(f"""
                UPDATE clusters SET
                    first_seen = (
                        SELECT MIN(COALESCE(NULLIF(r.created_utc, 0), r.fetched_at))
                        FROM pain_points p
                        JOIN raw_items r ON p.raw_item_id = r.id
                        WHERE p.cluster_id = clusters.id
                    ),
                    last_seen = (
                        SELECT MAX(COALESCE(NULLIF(r.created_utc, 0), r.fetched_at))
                        FROM pain_points p
                        JOIN raw_items r ON p.raw_item_id = r.id
                        WHERE p.cluster_id = clusters.id
                    )
                WHERE id IN ({placeholders})
                """, touched_cluster_ids)
                conn.commit()

        return saved_clusters

    # -------------------------------------------------------------------------
    # BERTopic path
    # -------------------------------------------------------------------------
    def _cluster_bertopic(self, pains: List[Dict[str, Any]], topic_model) -> List[List[Dict[str, Any]]]:
        """Fits BERTopic on pain summaries+quotes, filters noise (-1) topics."""
        docs = [f"{p.get('summary', '')} {p.get('quote', '')}" for p in pains]
        topics, _ = topic_model.fit_transform(docs)

        topic_groups: Dict[int, List[Dict]] = defaultdict(list)
        for idx, topic in enumerate(topics):
            if topic == -1:
                continue  # noise — discard
            topic_groups[topic].append(pains[idx])

        result = list(topic_groups.values())
        # BERTopic with min_topic_size already enforces the floor, but double-check
        result = [g for g in result if len(g) >= MIN_CLUSTER_SIZE]
        return result

    # -------------------------------------------------------------------------
    # TF-IDF path
    # -------------------------------------------------------------------------
    def _cluster_tfidf(self, pains: List[Dict[str, Any]], similarity_threshold: float) -> List[List[Dict[str, Any]]]:
        """Greedy TF-IDF cosine similarity clustering (no size floor here — enforced later)."""
        clusters_map: List[List[Dict]] = []
        for pain in pains:
            summary = pain.get("summary", "")
            assigned = False
            for cluster in clusters_map:
                centroid_text = " ".join([p.get("summary", "") for p in cluster])
                sim = self._compute_cosine_sim(summary, centroid_text)
                if sim >= similarity_threshold:
                    cluster.append(pain)
                    assigned = True
                    break
            if not assigned:
                clusters_map.append([pain])
        return clusters_map

    def _enforce_min_size(self, clusters_map: List[List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
        """
        Merges small clusters into their nearest semantic neighbour.
        Clusters that cannot be merged (no neighbours or only small clusters remain)
        are dropped. This ensures every saved cluster has size >= MIN_CLUSTER_SIZE.
        """
        # Separate qualifying and sub-threshold clusters
        large = [c for c in clusters_map if len(c) >= MIN_CLUSTER_SIZE]
        small = [c for c in clusters_map if len(c) < MIN_CLUSTER_SIZE]

        dropped_total = 0
        merged_total = 0

        for small_cluster in small:
            if not large:
                dropped_total += len(small_cluster)
                continue
            # Find nearest large cluster by centroid similarity
            centroid_small = " ".join([p.get("summary", "") for p in small_cluster])
            best_sim = -1.0
            best_idx = 0
            for i, lc in enumerate(large):
                centroid_large = " ".join([p.get("summary", "") for p in lc])
                sim = self._compute_cosine_sim(centroid_small, centroid_large)
                if sim > best_sim:
                    best_sim = sim
                    best_idx = i
            if best_sim >= 0.15:  # loose threshold to allow merge
                large[best_idx].extend(small_cluster)
                merged_total += len(small_cluster)
            else:
                dropped_total += len(small_cluster)

        if dropped_total:
            print(f"[cluster] TF-IDF: dropped {dropped_total} pains from sub-threshold clusters (no merge candidate)")
        if merged_total:
            print(f"[cluster] TF-IDF: merged {merged_total} pains from small clusters into nearest large cluster")

        return large

    # -------------------------------------------------------------------------
    # Label generation (keyword-based, no LLM call to keep clustering fast)
    # -------------------------------------------------------------------------
    def _generate_cluster_label(self, cluster_pains: List[Dict[str, Any]]) -> str:
        """Generates a concise 3-6 word problem domain title from key tokens and incumbents."""
        incumbents = [
            p.get("incumbent") for p in cluster_pains
            if p.get("incumbent") and str(p.get("incumbent")).lower() not in ["none", "null", "unknown", ""]
        ]
        all_text = " ".join([p.get("summary", "") for p in cluster_pains])
        tokens = self._tokenize(all_text)
        counts = Counter(tokens)
        top_words = [word.capitalize() for word, _ in counts.most_common(4) if len(word) > 2]

        if incumbents:
            inc_name = incumbents[0].capitalize()
            if inc_name not in top_words:
                top_words = [inc_name] + top_words[:3]

        if top_words:
            return " ".join(top_words) + " Issues"

        fallback = cluster_pains[0].get("summary", "Market Problem Area")
        fallback = re.sub(r'[>#*\[\]`"\']', '', fallback)
        return fallback[:40].strip()
