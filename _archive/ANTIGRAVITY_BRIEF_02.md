# Brief for Antigravity #2: Six upgrades to make the Market Intelligence Engine defensible

You built the foundation in Brief #1. It runs, but the last scan exposed real problems: 0 Reddit rows, 3 clusters all of size 1–2, all "DevOps Engineers" ICP, WTP evidence = 0, and every idea scored 8–9 on Feasibility/Distribution (rubber-stamped). This brief adds six upgrades in priority order to fix credibility. Do them **in order** — each builds on the previous.

Ground rules from Brief #1 still apply: no new vault markdown, no paid APIs, no daemons, keep everything in free tiers, ask before touching `opencode.json` or the vault.

**Before you start:** verify Reddit intake actually works end-to-end. Run `python main.py scan --topic "kubernetes" --subreddits devops --limit 20` and print `SELECT COUNT(*) FROM raw_items WHERE source LIKE 'reddit:%'`. If it's 0, fix the miner or storage wiring before anything below. Everything downstream depends on real data.

---

## Upgrade 1 — Datasette on the DB (auditability)

**Why:** right now the output is a card that says "Score: 32/50, trust me." Datasette exposes every row behind that score — clickable URLs, filterable tables, exportable CSV. Turns opinion into audited claim.

**Do:**
- `pip install datasette datasette-cluster-map datasette-vega`
- Add to `requirements.txt`.
- Create `D:\Start\project\metadata.json` with column descriptions, foreign-key links (`pain_points.raw_item_id` → `raw_items.id`, `ideas.cluster_id` → `clusters.id`), and a `queries` section with two canned queries:
  - `top_ideas_with_evidence`: joins ideas → clusters → pain_points → raw_items, returns idea name + score + representative pain + source URL, ordered by `score_total DESC`.
  - `pain_frequency_by_source`: pain count per `(source, date)` for the Vega chart plugin.
- Add a CLI verb: `python main.py inspect` that runs `datasette serve data/intel.db --metadata metadata.json --port 8001 --open`.
- Add a README section: "Audit any idea: `python main.py inspect`, click a row, follow the URLs back to the source."

**Done when:** `python main.py inspect` opens a browser to a running Datasette instance and the two canned queries work.

---

## Upgrade 2 — `instructor` + citation-required scoring (kills LLM freestyle)

**Why:** last scan gave Feasibility=9 and Distribution=8 to every single idea. The LLM is padding because nothing forces it to justify. Fix by enforcing schema *and* requiring every score to cite a specific `pain_point.id`.

**Do:**
- `pip install instructor pydantic`. Add to `requirements.txt`.
- Refactor `src/key_manager.py`: expose a new method `generate_structured(prompt, response_model, system_prompt=None)` that wraps every provider (Groq, Gemini, OpenRouter) via `instructor.from_openai(...)` or `instructor.from_provider(...)`. Keep the cascade behavior — try Groq first, fall back on schema-validation errors too, not just HTTP errors.
- Refactor `src/extractors/pain_extractor.py` to use Pydantic models instead of parsing JSON manually:

  ```python
  class PainPoint(BaseModel):
      summary: str = Field(..., max_length=200)
      incumbent: Optional[str]
      severity: Literal["annoyance", "blocker", "financial_bleed"]
      willingness_to_pay: str  # "$X/mo mentioned", "would switch from Y", or "unknown"
      persona: str
      quote: str = Field(..., max_length=200, description="verbatim snippet from the source")

  class ExtractionResult(BaseModel):
      has_pain: bool
      pains: List[PainPoint]
  ```

- Refactor `src/extractors/idea_ranker.py` — this is the important one. Change the scoring model to force per-axis citation:

  ```python
  class ScoreAxis(BaseModel):
      score: int = Field(..., ge=0, le=10)
      justification: str = Field(..., min_length=20, max_length=300)
      cited_pain_ids: List[int] = Field(..., min_length=1,
          description="pain_point.id values from THIS cluster that support the score")

  class IdeaProposal(BaseModel):
      name: str
      wedge: str
      icp: str
      frequency: ScoreAxis
      wtp: ScoreAxis
      incumbent_weakness: ScoreAxis
      feasibility: ScoreAxis
      distribution: ScoreAxis
      representative_quote: str
  ```

- After the LLM returns, **validate every `cited_pain_ids` actually belongs to the cluster being scored.** If any citation is invalid, reject the whole proposal and retry once. If it fails again, mark the cluster `status='unscoreable'` and move on — do not invent an idea from thin air.

- Add the cluster gate that was skipped last time: `if cluster.size < 5 or cluster.source_diversity < 2: skip and log`. This is not optional. If it results in zero ideas from a scan run, the correct behavior is `print("No qualifying clusters — need more data.")` and exit clean.

**Done when:**
- A rerun on the existing DB produces zero ideas (because current clusters are size 1–2 with single-source diversity) instead of three inflated ones.
- After adding more data (Upgrades 3 + 6), ideas that do appear all have per-axis justifications with valid pain-point citations visible in Datasette.

---

## Upgrade 3 — Two new miners: Shopify App Store + AlternativeTo (breaks devtools bias)

**Why:** every current source biases toward developers. Shopify App Store reviews give you e-commerce SaaS complaints from paying customers. AlternativeTo tells you which incumbents are hated enough that people search for alternatives.

### 3a. `src/miners/shopify_reviews_miner.py`
- Input: an app slug (e.g. `klaviyo-email-marketing`) or a category listing URL.
- Fetch via Jina Reader: `https://r.jina.ai/https://apps.shopify.com/{slug}/reviews?sort_by=newest&filter=1,2,3`.
- Parse the returned markdown for review blocks (title, rating, date, body, merchant name).
- Return the same dict shape every other miner uses. `source = "shopify:{slug}"`, `source_id = "shopify_{slug}_{hash_of_body}"`, `score = 1..5`, `content = body`.
- Add a helper `search_shopify_category(category, limit=20)` that first fetches `https://r.jina.ai/https://apps.shopify.com/categories/{category}` to discover app slugs, then pulls low-star reviews across the top N.
- Rate-limit hard: 1 req / 2 sec, since Jina has a free-tier quota.

### 3b. `src/miners/alternativeto_miner.py`
- Input: an incumbent product name (e.g. `Zendesk`).
- Fetch via Jina: `https://r.jina.ai/https://alternativeto.net/software/{slug}/`.
- Parse: the alternatives list (competitor set), the review comments below (dissatisfaction quotes), the "reasons to consider alternatives" section if present.
- Each comment becomes one raw item with `source = "alternativeto:{slug}"`, quote in `content`, incumbent name in a new nullable `raw_items.mentioned_incumbent` column (add via migration; store NULL for other sources).

### 3c. Wire both into the pipeline
- Extend `main.py` with `--shopify-apps` and `--alternativeto` flags on the `scan` verb.
- Add corresponding MCP tools in `mcp_server.py`: `search_shopify_reviews`, `search_alternativeto`.
- Add both to a new preset domain in the interactive menu: option `5. E-commerce merchant pain (Shopify + AlternativeTo)`.

**Done when:** A `python main.py scan --shopify-apps klaviyo,gorgias,recharge --alternativeto zendesk,mailchimp` run inserts ≥ 50 raw items with `source LIKE 'shopify:%'` or `source LIKE 'alternativeto:%'` and none of them are devtools.

---

## Upgrade 4 — Replace clustering with BERTopic (kills size-1 clusters)

**Why:** current clustering produces size-1 clusters and lets `idea_ranker` score them. BERTopic uses HDBSCAN with proper noise rejection — items that don't fit any cluster get labeled `-1` (outlier) instead of forming a fake cluster of one.

**Do:**
- `pip install bertopic sentence-transformers hdbscan umap-learn`. Add to `requirements.txt`.
- Rewrite `src/extractors/cluster.py`:
  - Load all pains where `cluster_id IS NULL` from `pain_points`.
  - Embed with local `SentenceTransformer("all-MiniLM-L6-v2")` — no HuggingFace API dependency, no rate limits.
  - Fit BERTopic with `min_topic_size=5` (matches your cluster gate) and `nr_topics="auto"`.
  - For each topic (skip `-1` outliers), upsert a row in `clusters` with the BERTopic label (`topic_model.get_topic_info()` gives you a name).
  - Populate `clusters.size`, `clusters.source_diversity` (COUNT DISTINCT source across the cluster's pains via a join back through `raw_items`), `clusters.first_seen` and `last_seen` (MIN/MAX of `raw_items.created_utc` across cluster members), `clusters.wtp_evidence_count` (COUNT pains where `willingness_to_pay != 'unknown'`), and `clusters.avg_severity_score` (mean of severity mapped `annoyance=1, blocker=2, financial_bleed=3`).
  - Set `pain_points.cluster_id` for every clustered pain. Outliers stay NULL.
- Add `python main.py cluster --recluster` flag that clears `cluster_id` on all pains, drops `clusters`, and re-runs from scratch. Default `cluster` command only clusters new pains.

**Done when:**
- Running `cluster --recluster` on the current DB produces zero clusters (11 pains is too few for `min_topic_size=5`) instead of 3 fake ones.
- After scans add more data, every row in `clusters` has non-null `first_seen`, `last_seen`, `source_diversity`, and `wtp_evidence_count`.

---

## Upgrade 5 — `pytrends` sanity check on every candidate wedge

**Why:** an idea can look great on friction data but be about a dying market. Trends is a cheap sanity check.

**Do:**
- `pip install pytrends`. Add to `requirements.txt`.
- New file `src/validators/trend_validator.py`:
  - Function `validate_wedge(wedge_keywords: List[str], timeframe: str = "today 5-y") -> TrendReport`.
  - Fetches Google Trends interest-over-time for the keywords. Handles the 429 rate limit with retry + backoff (pytrends is flaky; wrap with `tenacity`).
  - Returns:
    ```python
    class TrendReport(BaseModel):
        keywords: List[str]
        avg_interest_last_12mo: float      # 0-100
        slope_last_24mo: float             # linear regression slope
        trend_verdict: Literal["rising", "flat", "declining", "insufficient_data"]
        related_rising_queries: List[str]  # top 5 breakout queries
    ```
- Add a new column `ideas.trend_verdict` (nullable text) and `ideas.trend_slope` (nullable real). Migration.
- Modify `idea_ranker.py`: after an idea passes all previous gates, call `validate_wedge([idea.name, idea.wedge_keywords...])`. If verdict is `declining`, cap `score_distribution` at 3 (was hardcoded near 8). If `rising`, allow up to 10. Store the verdict + slope on the idea row.
- Add "Trend" column to `python main.py top` output.

**Done when:** `python main.py top` shows the trend verdict next to every ranked idea, and at least one previously "8-scored" declining topic scores lower after this gate.

---

## Upgrade 6 — YouTube transcript miner (founders confess more on podcasts than Reddit)

**Why:** long-form podcast interviews are the highest-density source of pain and WTP quotes anywhere on the internet, and they're free. Zero of your current signal comes from here.

**Do:**
- `pip install youtube-transcript-api yt-dlp`. Add to `requirements.txt`.
- New file `src/miners/youtube_miner.py`:
  - Input: a list of channel IDs OR a search query.
  - For channels: use `yt-dlp` (via subprocess or Python API) with `--flat-playlist` to list videos from the channel (uploads playlist ID = channel ID with `UU` prefix replacing `UC`). No API key needed.
  - For search queries: `yt-dlp` supports `ytsearch{N}:{query}` — pull the top N results by relevance.
  - For each video, fetch English transcript via `youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id)`. Handles auto-captions and manual subs. Skip videos with no transcript.
  - Chunk transcripts into ~500-word segments with 50-word overlap. Each chunk becomes one raw item with `source = "youtube:{channel_handle}"`, `source_id = "yt_{video_id}_{chunk_idx}"`, `url = "https://youtube.com/watch?v={video_id}&t={start_seconds}s"` (deep-link to the timestamp), `content = chunk_text`, `title = "{video_title} [chunk {idx}]"`.
  - `score` = video like count (via `yt-dlp` metadata) / video count fallback of 0.
  - `created_utc` = video upload date.
- Add a seed list at `D:\Start\project\config\youtube_sources.json` with 10–20 known high-signal channels for founder/ops content, grouped by vertical:
  - SaaS founders: MicroConf, Indie Hackers, Startups For The Rest Of Us
  - E-commerce: Shopify Masters, Ecom Crew, My First Million (has e-com episodes)
  - Vertical SaaS ops: any that surface (leave the file editable — user will add over time)
- Add CLI verb: `python main.py mine-youtube --channels indiehackers,microconf --videos-per-channel 20`. Also honor `--query "shopify billing pain"` for keyword search.
- **Critical:** rate-limit hard. YouTube's transcript endpoint 429s aggressively. 1 request / 3 sec, exponential backoff, cache results in `data/yt_cache/` keyed by video_id so reruns are free.

**Done when:**
- One run against `indiehackers` channel with `--videos-per-channel 10` produces ≥ 50 raw items with `source LIKE 'youtube:%'` and each URL deep-links to the timestamp when clicked.
- Running `python main.py extract` then `cluster --recluster` produces at least one cluster containing pains from both YouTube AND Reddit/HN (cross-source corroboration).

---

## Final integration + verification

After all six are done:

1. Wipe the current DB (`data/intel.db`) — it's poisoned with junk clusters and inflated ideas. Move to `data/intel.db.bak` don't delete.
2. Run a multi-source scan across genuinely different verticals:
   ```
   python main.py scan --topic "shopify checkout billing pain" --shopify-apps recharge,bold-subscriptions --alternativeto stripe,recurly --limit 30
   python main.py scan --topic "dental practice scheduling" --subreddits Dentistry --limit 30
   python main.py scan --topic "freight broker TMS" --subreddits Truckers Logistics --limit 30
   python main.py mine-youtube --channels indiehackers --videos-per-channel 15
   python main.py extract
   python main.py cluster --recluster
   python main.py rank
   python main.py top 10
   python main.py inspect
   ```
3. Report back with: total raw items per source, cluster count that survived the size≥5 + diversity≥2 gate, ideas that passed with valid citations, and a screenshot of Datasette showing one idea drilled down to its source URLs.

If the final `top` command returns 0 ideas because no cluster qualified, **that is a correct result, not a failure.** Report it as-is and tell the user which verticals to scan more of.

Do not celebrate a "working pipeline" until at least one idea has: `source_diversity >= 3`, `wtp_evidence_count >= 5`, `trend_verdict IN ('rising', 'flat')`, and every score axis cites a real pain_point.id. That is the credibility bar.
