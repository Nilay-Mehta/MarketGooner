# Brief for Antigravity: Fix and rebuild the Market Intelligence Engine

You are taking over a broken market-research pipeline at `D:\Start\`. The stated goal is: **help the user find one validated B2B SaaS opportunity to build a business on.** The current system produces low-signal output and cannot rank ideas. Your job is to fix the foundation, then add the missing pieces.

Do the work in the phases below, in order. Do not skip Phase 0 — half of what's in the repo is broken and needs to be triaged before you build on top of it.

---

## Ground truth about what exists

- `D:\Start\project\` — Python engine. Entry: `main.py`. MCP server: `mcp_server.py`.
- `D:\Start\project\src\miners\` — `reddit_miner.py`, `hn_miner.py`, `github_miner.py`, `jina_fetcher.py`.
- `D:\Start\project\src\extractors\gap_synthesizer.py` — single-shot LLM synthesis.
- `D:\Start\project\src\exporters\vault_exporter.py` — writes markdown to `output/` and to the Obsidian vault.
- `D:\Start\project\src\key_manager.py` — round-robin across Groq / Gemini / HuggingFace free tiers.
- `D:\Start\.opencode\` — Opencode agent config (`orchestrator`, `trend-scout`, `social-miner`, `competitor-auditor`, `gap-architect`) + skills.
- `D:\Start\Market_Intelligence_Vault\` — Obsidian vault with playbooks (Steph France Gold Mining, Reddit Teleportation, etc.) and scan outputs.
- `.env` at both root and `project/` holds free-tier keys.

**Do not** rewrite the vault content or the Opencode config until Phase 3. Fix the engine first.

---

## Phase 0 — Triage the broken parts (must do first)

### 0.1 Reddit miner is fake
`src/miners/reddit_miner.py` uses DuckDuckGo (`site:reddit.com/...`) and hardcodes `score=15, comments_count=8` for every result. It never touches Reddit. Rewrite it to hit Reddit's public JSON endpoints (no auth needed for read):

- Search: `https://www.reddit.com/r/{sub}/search.json?q={query}&restrict_sr=1&sort=relevance&t=year&limit={n}`
- Post + top comments: `https://www.reddit.com/r/{sub}/comments/{id}.json?limit=50&sort=top`

Requirements:
- Real `User-Agent` header (Reddit 429s browsers without one). Use `"MarketIntel/0.1 by u/anon"`.
- Real `score`, `num_comments`, `created_utc`, `permalink`, `selftext`, and the top 10 comment bodies concatenated into `content`.
- Rate-limit: 1 req/sec, exponential backoff on 429.
- Return the same dict shape the rest of the pipeline expects, plus new fields: `created_utc`, `top_comments` (list of strings), `subreddit`.
- Keep the pain-keyword tagger but run it over `selftext + top_comments`, not the title.

### 0.2 Delete or clearly mark broken outputs
In `D:\Start\Market_Intelligence_Vault\06_Market_Scans\` and `D:\Start\project\output\`, several files are either empty or contain the *prompt template* saved as content (offline mode failure). Move all files whose body starts with `> [!NOTE]\n> **Offline Synthesis Mode:**` or that are 0 bytes into `06_Market_Scans/_broken/`. Do not delete — the user should see what was junk.

### 0.3 Fix `gap_synthesizer.py` truncation
It hard-caps at `raw_items[:30]` and jams everything into one prompt. Two problems: (a) drops signal, (b) invites hallucination. Do not fix this yet — Phase 2 replaces it entirely. Just add a comment `# TODO: replaced in Phase 2` so nobody edits it.

### 0.4 Sub-agent theater
In `D:\Start\opencode.json`, the sub-agents (`trend-scout`, `social-miner`, `competitor-auditor`, `gap-architect`) have prompts telling them to "search Hacker News" etc. but no tool bindings — they hallucinate from LLM memory. Do not touch `opencode.json` yet. Phase 3 rewires them to the MCP tools.

---

## Phase 1 — Give the system memory

The core failure of the current design is: every scan writes a fresh markdown file. There is no way to answer "which pain point has surfaced across multiple scans?" That is the whole point of comprehension.

### 1.1 Add SQLite
Create `D:\Start\project\src\storage\db.py`. Use stdlib `sqlite3`. DB file at `D:\Start\project\data\intel.db`.

Schema:

```sql
CREATE TABLE IF NOT EXISTS raw_items (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,            -- 'reddit', 'hn', 'github', 'g2', 'producthunt'
  source_id TEXT NOT NULL,         -- reddit permalink, HN objectID, etc.
  url TEXT NOT NULL,
  title TEXT,
  content TEXT,
  score INTEGER,
  comments_count INTEGER,
  created_utc INTEGER,
  fetched_at INTEGER NOT NULL,
  topic_query TEXT,                -- the query that surfaced this item
  UNIQUE(source, source_id)
);

CREATE TABLE IF NOT EXISTS pain_points (
  id INTEGER PRIMARY KEY,
  raw_item_id INTEGER REFERENCES raw_items(id),
  summary TEXT NOT NULL,           -- 1-sentence pain, LLM-extracted
  incumbent TEXT,                  -- product blamed, if any
  severity TEXT,                   -- 'annoyance' | 'blocker' | 'financial_bleed'
  willingness_to_pay TEXT,         -- direct $ mentions or 'unknown'
  persona TEXT,                    -- role/title mentioned
  cluster_id INTEGER,              -- filled in Phase 2 clustering
  extracted_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS clusters (
  id INTEGER PRIMARY KEY,
  label TEXT NOT NULL,             -- LLM-generated cluster name
  size INTEGER NOT NULL,
  first_seen INTEGER,
  last_seen INTEGER,
  source_diversity INTEGER,        -- distinct source count
  avg_severity_score REAL,
  wtp_evidence_count INTEGER
);

CREATE TABLE IF NOT EXISTS ideas (
  id INTEGER PRIMARY KEY,
  cluster_id INTEGER REFERENCES clusters(id),
  name TEXT,
  wedge TEXT,                      -- the specific unbundling angle
  icp TEXT,
  score_frequency INTEGER,         -- 0-10
  score_wtp INTEGER,               -- 0-10
  score_incumbent_weakness INTEGER,-- 0-10
  score_feasibility INTEGER,       -- 0-10
  score_distribution INTEGER,      -- 0-10
  score_total INTEGER,             -- sum
  status TEXT DEFAULT 'candidate', -- candidate | validating | killed | building
  created_at INTEGER
);
```

Provide functions: `insert_raw_item`, `insert_pain_point`, `upsert_cluster`, `list_ideas(order_by='score_total')`, `dedupe_raw_items()`.

### 1.2 Route every miner through storage
`main.py` and `mcp_server.py` currently pass miner output straight to synthesis. Insert every raw item into `raw_items` first. Dedupe on `(source, source_id)`. Only new items go to Phase 2 extraction.

---

## Phase 2 — Two-stage extraction (kill the one-shot synthesis)

Replace `gap_synthesizer.py` with a two-stage flow.

### 2.1 Per-item pain extraction
New file: `src/extractors/pain_extractor.py`.

For each `raw_item`, prompt the LLM to return **strict JSON** (no prose):

```json
{
  "has_pain": true,
  "pains": [
    {
      "summary": "one-sentence description",
      "incumbent": "product name or null",
      "severity": "annoyance|blocker|financial_bleed",
      "willingness_to_pay": "quoted $ amount, or 'unknown'",
      "persona": "role or 'unknown'",
      "quote": "verbatim snippet <= 200 chars"
    }
  ]
}
```

Requirements:
- Use `key_manager` with Groq's Llama 3.3 70B as primary (fastest, cheapest).
- Retry once with Gemini if JSON parse fails.
- Skip items where `has_pain=false`. Log skip reason.
- Batch 5 items per LLM call to save tokens (each item stays a separate JSON object in the response).

Store every extracted pain in `pain_points`.

### 2.2 Clustering across pains
New file: `src/extractors/cluster.py`.

- Embed every pain `summary` with a free embedding model. Use `sentence-transformers/all-MiniLM-L6-v2` via HuggingFace Inference API (already in `key_manager`), or a local `sentence-transformers` install if the user allows the dep.
- Cluster with HDBSCAN (min_cluster_size=3) or, if that dep is heavy, simple cosine-similarity greedy clustering at threshold 0.75.
- For each cluster, ask the LLM to produce a short label. Store in `clusters`.
- Update each `pain_points.cluster_id`.

### 2.3 Idea scoring
New file: `src/extractors/idea_ranker.py`.

For every cluster with `size >= 5` and `source_diversity >= 2`, prompt the LLM to:
1. Propose one unbundling wedge (specific feature the incumbents don't ship).
2. Name an ICP.
3. Return a `score_total` breakdown using the rubric below.

Rubric (0–10 each, sum = 0–50):
- **Frequency:** how many pains in the cluster, log-scaled.
- **WTP evidence:** how many pains had explicit $ amounts or "would switch" statements.
- **Incumbent weakness:** how concrete are the complaints (specific bugs > vague dissatisfaction).
- **Feasibility:** LLM estimates weeks-to-first-paying-customer; ≤4 weeks = 10.
- **Distribution:** does an obvious channel exist (specific subreddit, conference, newsletter)? Yes = 10.

Store in `ideas`. Never let the LLM invent pains that weren't in the source data — pass only the pain quotes for that cluster into the prompt.

---

## Phase 3 — Broaden sources and fix the agents

Only after Phases 0–2 work end-to-end.

### 3.1 New miners
Add under `src/miners/`:
- `producthunt_miner.py` — GraphQL API (`https://api.producthunt.com/v2/api/graphql`), needs free dev token; hit the "makers responded" and "comments" fields.
- `g2_miner.py` — use Jina Reader (`https://r.jina.ai/https://www.g2.com/products/<slug>/reviews?filter=rating:1,2,3`) to pull 1–3 star reviews as clean markdown. Rate-limit hard.
- `stackoverflow_miner.py` — StackExchange API, filter for unanswered questions on a tag.
- `github_issues_miner.py` — extend existing `github_miner.py` to also fetch open issues on named incumbent repos, labelled `bug` or `enhancement`.

Every miner writes through the storage layer from Phase 1.

### 3.2 Rewire Opencode sub-agents to real tools
In `D:\Start\opencode.json`:
- Give each sub-agent an explicit tool budget from the `market_research` MCP. `social-miner` gets `search_reddit`. `trend-scout` gets `search_hackernews`. `competitor-auditor` gets a new MCP tool `search_g2_reviews`. `gap-architect` gets `rank_ideas` and `get_cluster_pains`.
- Add these new tools to `mcp_server.py`. Each just calls the Phase 1/2 storage functions.
- Remove any sub-agent instruction that implies free-form search — they should call tools or return "no data."

### 3.3 New CLI verbs on `main.py`
- `python main.py scan --topic X --subreddits ...` (existing behavior, now writes to DB).
- `python main.py extract` — runs pain extraction on new raw items.
- `python main.py cluster` — re-runs clustering + labeling.
- `python main.py rank` — regenerates the `ideas` table.
- `python main.py top [N]` — prints the top N ideas as a rich table with scores, cluster label, source diversity, and one representative quote.

---

## Phase 4 — Kill the "2-3 week MVP" bias

The current `gap_synthesizer.py` prompt hardcodes "buildable in 2-3 weeks." This filters out most real opportunities. In the new `idea_ranker.py`, replace with **"shortest path to first paying customer"** — which sometimes means a Notion+Zapier hack sold for $200/mo before any code exists. Feasibility scoring should reward *speed to revenue*, not speed to code.

---

## What "done" looks like

The user can run:

```bash
python main.py scan --topic "DevOps observability" --subreddits devops sre kubernetes --limit 50
python main.py scan --topic "B2B invoicing" --subreddits SaaS smallbusiness --limit 50
python main.py scan --topic "legal ops" --subreddits LawFirm legaltech --limit 50
python main.py extract
python main.py cluster
python main.py rank
python main.py top 10
```

…and see a ranked table of ten candidate ideas, each with score breakdown, source diversity, cluster size, and a verbatim quote from a real user. Every claim traces back to a row in `raw_items`. No LLM-invented pains.

---

## Rules of engagement

- **Do not** add new markdown files to the vault. The vault is the user's knowledge base, not your output directory. All new output goes to SQLite + `python main.py top`.
- **Do not** add background daemons, cron jobs, or GitHub Actions. This is a local tool.
- **Do not** add paid APIs. Everything must fit in free tiers.
- **Do** commit `.gitignore` entries for `data/intel.db`, `.env`, and `__pycache__/` before creating those paths.
- **Do** write a smoke test for each new miner: it should hit the real API and assert `len(results) > 0` for a well-known query.
- **Do** ask the user before rewriting `opencode.json` or the vault. Everything else in `D:\Start\project\` is fair game.
- When you finish a phase, print a one-line summary of what changed and what the user should test.

Start with Phase 0.1 — the fake Reddit miner is the single highest-leverage fix.
