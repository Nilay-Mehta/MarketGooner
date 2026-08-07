import os
import sqlite3
import time
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import numpy as np

_embedder = None
_embedding_cache = None
_embedding_ids = None

def _init_embeddings(db_path: str):
    global _embedder, _embedding_cache, _embedding_ids
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer('all-MiniLM-L6-v2')
            with get_db(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT raw_item_id, embedding FROM raw_item_embeddings")
                rows = cursor.fetchall()
                ids = []
                vecs = []
                for row in rows:
                    ids.append(row[0])
                    vecs.append(np.frombuffer(row[1], dtype=np.float32))
                _embedding_ids = ids
                if vecs:
                    _embedding_cache = np.vstack(vecs)
                else:
                    _embedding_cache = np.empty((0, 384), dtype=np.float32)
        except ImportError:
            print("[!] sentence-transformers not installed, semantic dedup disabled.")
            _embedder = False


DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "intel.db"
)

@contextmanager
def get_db(db_path: str = DEFAULT_DB_PATH):
    """Context manager for SQLite connections that ensures commit and proper closing on Windows."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes SQLite tables for market intelligence storage."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Raw Scraped Items Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            content TEXT,
            score INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            created_utc INTEGER DEFAULT 0,
            fetched_at INTEGER NOT NULL,
            topic_query TEXT,
            UNIQUE(source, source_id)
        );
        """)

        # 2. Extracted Pain Points Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pain_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_item_id INTEGER REFERENCES raw_items(id),
            summary TEXT NOT NULL,
            incumbent TEXT,
            severity TEXT,
            willingness_to_pay TEXT,
            wtp_type TEXT DEFAULT 'unknown',
            persona TEXT,
            quote TEXT,
            cluster_id INTEGER,
            extracted_at INTEGER NOT NULL
        );
        """)

        # 2.5 Embeddings Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_item_embeddings (
            raw_item_id INTEGER PRIMARY KEY REFERENCES raw_items(id),
            embedding BLOB NOT NULL
        );
        """)

        # 3. Aggregated Problem Clusters Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            size INTEGER NOT NULL,
            first_seen INTEGER,
            last_seen INTEGER,
            source_diversity INTEGER,
            avg_severity_score REAL,
            wtp_evidence_count INTEGER
        );
        """)

        # 4. Scored Startup Ideas Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_id INTEGER REFERENCES clusters(id),
            name TEXT,
            wedge TEXT,
            icp TEXT,
            score_frequency INTEGER DEFAULT 0,
            score_wtp INTEGER DEFAULT 0,
            score_incumbent_weakness INTEGER DEFAULT 0,
            score_feasibility INTEGER DEFAULT 0,
            score_distribution INTEGER DEFAULT 0,
            score_total INTEGER DEFAULT 0,
            status TEXT DEFAULT 'candidate',
            representative_quote TEXT,
            trend_verdict TEXT,
            trend_slope REAL,
            created_at INTEGER
        );
        """)

        # Safe migrations for existing databases
        # 1. raw_items.mentioned_incumbent
        raw_cols = [row[1] for row in cursor.execute("PRAGMA table_info(raw_items)").fetchall()]
        if "mentioned_incumbent" not in raw_cols:
            cursor.execute("ALTER TABLE raw_items ADD COLUMN mentioned_incumbent TEXT")

        # 2. clusters.status
        cluster_cols = [row[1] for row in cursor.execute("PRAGMA table_info(clusters)").fetchall()]
        if "status" not in cluster_cols:
            cursor.execute("ALTER TABLE clusters ADD COLUMN status TEXT DEFAULT 'active'")

        # 3. ideas.trend_verdict and ideas.trend_slope
        idea_cols = [row[1] for row in cursor.execute("PRAGMA table_info(ideas)").fetchall()]
        if "trend_verdict" not in idea_cols:
            cursor.execute("ALTER TABLE ideas ADD COLUMN trend_verdict TEXT")
        if "trend_slope" not in idea_cols:
            cursor.execute("ALTER TABLE ideas ADD COLUMN trend_slope REAL")

        # 4. pain_points.wtp_type
        pain_cols = [row[1] for row in cursor.execute("PRAGMA table_info(pain_points)").fetchall()]
        if "wtp_type" not in pain_cols:
            cursor.execute("ALTER TABLE pain_points ADD COLUMN wtp_type TEXT DEFAULT 'unknown'")

        conn.commit()

def insert_raw_item(
    source: str,
    source_id: str,
    url: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    score: int = 0,
    comments_count: int = 0,
    created_utc: int = 0,
    topic_query: Optional[str] = None,
    mentioned_incumbent: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Optional[int]:
    """
    Inserts a raw scraped item into SQLite.
    Returns the integer id if newly inserted, or None if item already exists (deduplicated).
    """
    init_db(db_path)
    
    global _embedder, _embedding_cache, _embedding_ids
    if _embedder is None:
        _init_embeddings(db_path)

    # Semantic deduplication check
    embedding_vec = None
    if _embedder:
        text = f"{title or ''} {(content or '')[:200]}".strip()
        if text:
            query_vec = _embedder.encode(text)
            embedding_vec = query_vec.astype(np.float32)
            if _embedding_cache.shape[0] > 0:
                sims = np.dot(_embedding_cache, embedding_vec)
                if np.max(sims) > 0.90:
                    return None  # semantic duplicate

    fetched_at = int(time.time())
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO raw_items (
                source, source_id, url, title, content,
                score, comments_count, created_utc, fetched_at, topic_query, mentioned_incumbent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source, source_id, url, title, content,
                score, comments_count, created_utc, fetched_at, topic_query, mentioned_incumbent
            ))
            new_id = cursor.lastrowid
            
            # Save embedding
            if embedding_vec is not None:
                cursor.execute("""
                INSERT INTO raw_item_embeddings (raw_item_id, embedding)
                VALUES (?, ?)
                """, (new_id, embedding_vec.tobytes()))
                
                # Update in-memory cache
                if _embedding_cache.shape[0] == 0:
                    _embedding_cache = embedding_vec.reshape(1, -1)
                else:
                    _embedding_cache = np.vstack([_embedding_cache, embedding_vec])
                _embedding_ids.append(new_id)

            conn.commit()
            return new_id
        except sqlite3.IntegrityError:
            return None

def insert_pain_point(
    raw_item_id: int,
    summary: str,
    incumbent: Optional[str] = None,
    severity: Optional[str] = "annoyance",
    willingness_to_pay: Optional[str] = "unknown",
    wtp_type: Optional[str] = "unknown",
    persona: Optional[str] = "unknown",
    quote: Optional[str] = None,
    cluster_id: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Inserts a structured pain point extracted from a raw item."""
    init_db(db_path)
    extracted_at = int(time.time())
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO pain_points (
            raw_item_id, summary, incumbent, severity,
            willingness_to_pay, wtp_type, persona, quote, cluster_id, extracted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            raw_item_id, summary, incumbent, severity,
            willingness_to_pay, wtp_type, persona, quote, cluster_id, extracted_at
        ))
        conn.commit()
        return cursor.lastrowid

def upsert_cluster(
    label: str,
    size: int,
    first_seen: Optional[int] = None,
    last_seen: Optional[int] = None,
    source_diversity: int = 1,
    avg_severity_score: float = 0.0,
    wtp_evidence_count: int = 0,
    status: str = "active",
    cluster_id: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Inserts or updates a problem cluster."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        if cluster_id:
            cursor.execute("""
            UPDATE clusters SET
                label = ?, size = ?, first_seen = ?, last_seen = ?,
                source_diversity = ?, avg_severity_score = ?, wtp_evidence_count = ?, status = ?
            WHERE id = ?
            """, (
                label, size, first_seen, last_seen,
                source_diversity, avg_severity_score, wtp_evidence_count, status, cluster_id
            ))
            conn.commit()
            return cluster_id
        else:
            cursor.execute("""
            INSERT INTO clusters (
                label, size, first_seen, last_seen,
                source_diversity, avg_severity_score, wtp_evidence_count, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                label, size, first_seen, last_seen,
                source_diversity, avg_severity_score, wtp_evidence_count, status
            ))
            conn.commit()
            return cursor.lastrowid

def insert_idea(
    cluster_id: int,
    name: str,
    wedge: str,
    icp: str,
    score_frequency: int,
    score_wtp: int,
    score_incumbent_weakness: int,
    score_feasibility: int,
    score_distribution: int,
    representative_quote: Optional[str] = None,
    status: str = "candidate",
    trend_verdict: Optional[str] = None,
    trend_slope: Optional[float] = None,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Inserts a scored startup idea linked to a cluster."""
    init_db(db_path)
    score_total = (
        score_frequency +
        score_wtp +
        score_incumbent_weakness +
        score_feasibility +
        score_distribution
    )
    created_at = int(time.time())
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO ideas (
            cluster_id, name, wedge, icp,
            score_frequency, score_wtp, score_incumbent_weakness,
            score_feasibility, score_distribution, score_total,
            status, representative_quote, trend_verdict, trend_slope, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cluster_id, name, wedge, icp,
            score_frequency, score_wtp, score_incumbent_weakness,
            score_feasibility, score_distribution, score_total,
            status, representative_quote, trend_verdict, trend_slope, created_at
        ))
        conn.commit()
        return cursor.lastrowid

def list_ideas(order_by: str = "score_total", limit: int = 50, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns ranked startup ideas joined with cluster metadata."""
    init_db(db_path)
    valid_orders = ["score_total", "score_wtp", "score_feasibility", "created_at"]
    sort_col = order_by if order_by in valid_orders else "score_total"

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
        SELECT 
            i.*,
            c.label as cluster_label,
            c.size as cluster_size,
            c.source_diversity,
            c.wtp_evidence_count
        FROM ideas i
        LEFT JOIN clusters c ON i.cluster_id = c.id
        ORDER BY i.{sort_col} DESC
        LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_unextracted_raw_items(limit: int = 100, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns raw items that have not yet had pains extracted."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT r.* FROM raw_items r
        LEFT JOIN pain_points p ON r.id = p.raw_item_id
        WHERE p.id IS NULL
        ORDER BY r.score DESC, r.comments_count DESC
        LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_all_pain_points(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns all extracted pain points joined with raw item metadata and timestamps."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            p.*, 
            r.source, 
            r.url, 
            r.title as item_title,
            COALESCE(NULLIF(r.created_utc, 0), r.fetched_at, strftime('%s', 'now')) as created_utc
        FROM pain_points p
        JOIN raw_items r ON p.raw_item_id = r.id
        ORDER BY p.id ASC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_pains_by_cluster(cluster_id: int, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns all pain points associated with a given cluster."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT p.*, r.source, r.url, r.title as item_title
        FROM pain_points p
        JOIN raw_items r ON p.raw_item_id = r.id
        WHERE p.cluster_id = ?
        """, (cluster_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def update_pain_cluster(pain_id: int, cluster_id: int, db_path: str = DEFAULT_DB_PATH) -> None:
    """Updates the cluster assignment of a pain point."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE pain_points SET cluster_id = ? WHERE id = ?", (cluster_id, pain_id))
        conn.commit()

def dedupe_raw_items(db_path: str = DEFAULT_DB_PATH) -> int:
    """Removes any duplicate raw items keeping the earliest fetched."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        DELETE FROM raw_items
        WHERE id NOT IN (
            SELECT MIN(id) FROM raw_items GROUP BY source, source_id
        )
        """)
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
