# 02 — Current State Audit

This document is a comprehensive audit of the `D:\Start\` ecosystem as it exists today. It evaluates every file, database table, and vault note against the 5 core principles laid out in `01_VISION_AND_PRINCIPLES.md`. 

Every component is tagged **KEEP**, **DELETE**, or **REFACTOR** with a specific justification. A competent engineer with zero context can use this document to safely dismantle the broken parts of the legacy pipeline while preserving its valuable foundations.

---

## 1. Filesystem Inventory

Tree of `D:\Start\` up to depth 3:

```text
D:\Start\
├── HANDOFF\
│   ├── 01_VISION_AND_PRINCIPLES.md (KEEP - Core architecture spec)
├── Market_Intelligence_Vault\
│   ├── 00_Master_Dashboard.md (REFACTOR - Needs dynamic updates from the new pipeline)
│   ├── 01_Foundations\
│   ├── 02_Architecture_and_APIs\
│   ├── 03_Research_and_Playbooks\
│   ├── 04_Validation_and_GTM\
│   ├── 05_Tools_and_Repositories\
│   ├── 06_Market_Scans\ (KEEP - Output destination for marketing briefs)
│   ├── 07_Go_To_Market\
├── project\
│   ├── assets\ (KEEP)
│   ├── config\ (KEEP)
│   ├── data\ (KEEP - Contains intel.db)
│   ├── output\ (DELETE - Shift all outputs to Market_Intelligence_Vault)
│   ├── src\ (REFACTOR - Core pipeline code)
│   ├── tests\ (KEEP)
│   ├── .env (KEEP)
│   ├── main.py (REFACTOR)
│   ├── mcp_server.py (DELETE - Violates zero-cost constraint if it requires paid MCP hosts, or obsolete)
│   ├── scan_verticals.py (REFACTOR)
│   ├── wipe_extracted.py (DELETE - Destructive tool that threatens intel.db state)
├── .opencode\
│   ├── skills\ (KEEP - Agent definitions)
```

**Verdict:** 
The macro structure is sound but fractured. Output artifacts are split between `project/output/` and `Market_Intelligence_Vault/06_Market_Scans/`. We will **REFACTOR** to ensure the vault is the sole destination for pipeline outputs (Principle 5).

---

## 2. Codebase Audit (`D:\Start\project\src\`)

| Component | LOC | Status | Verdict | Reason (Principle) |
| :--- | :--- | :--- | :--- | :--- |
| `main.py` | (Root) | Partially Broken | **REFACTOR** | Hardcodes execution logic without human-in-the-loop market selection (Violates Principle 1). Needs a CLI prompt for trend validation. |
| `mcp_server.py` | (Root) | Dead | **DELETE** | Legacy host interface. Unnecessary complexity for local execution. |
| `compressor.py` | 53 | Works | **KEEP** | Essential for shrinking large HTML chunks before ingestion. |
| `key_manager.py` | 365 | Partially Broken | **REFACTOR** | Current implementation does not cascade based on cognitive load tiering. Must be updated to support `fast` and `deep` literal tiers (Violates Principle 3). |
| `extractors/cluster.py` | 412 | Broken | **REFACTOR** | Current clustering groups into generic buckets (Violates Principle 2). Needs anomaly-first logic. |
| `extractors/idea_ranker.py` | 303 | Broken | **REFACTOR** | Currently generates invented SaaS names (e.g., "AgentSphere"). Needs to output an anomaly digest of specific quotes and dollar amounts (Violates Principle 2). |
| `extractors/pain_extractor.py` | 155 | Broken | **REFACTOR** | Lacks validation guardrails. Fails to reject generic pain points that omit proper nouns or $ amounts (Violates Principle 2). |
| `extractors/gap_synthesizer.py`| 85 | Dead | **DELETE** | Replaced by dual-output functionality in the new architecture. |
| `storage/db.py` | 438 | Works | **KEEP** | Standard SQLite wrapper. Preserves existing 1,146 pain points. |
| `miners/reddit_miner.py` | 224 | Works | **KEEP** | Core ingestion source. |
| `miners/youtube_miner.py` | 151 | Works | **KEEP** | Core ingestion source. |
| `miners/g2_miner.py` | 70 | Dead | **DELETE** | G2 has extremely aggressive anti-scraping blocks, violating zero-money/rate-limit logic (Violates Principle 4/8). |
| `miners/producthunt_miner.py`| 60 | Dead | **DELETE** | Low signal-to-noise ratio. |
| `miners/hn_miner.py` | 39 | Works | **KEEP** | Excellent source for technical signals. |
| `miners/stackoverflow_miner` | 73 | Works | **KEEP** | Excellent technical signal source. |
| `miners/shopify_reviews_miner`| 151 | Works | **KEEP** | Excellent E-commerce signal source. |
| `exporters/vault_exporter.py`| 58 | Works | **REFACTOR** | Needs an update to output both `.docx` and Markdown formats simultaneously (Principle 5). |
| `validators/trend_validator.py`| 87 | Works | **KEEP** | Core requirement for Principle 1 (Go/No-Go human check). |
| `agents/` | 0 | Missing | **REFACTOR** | The folder doesn't exist. Master/Copywriter agents must be created here to support dual output (Principle 5). |
| `orchestration/` | 0 | Missing | **REFACTOR** | The folder doesn't exist. Needs `budget_manager.py` to handle rate-limit degrade (Principle 4). |

---

## 3. Database Audit (`data/intel.db`)

**1. Tables in the DB:**
`raw_items`, `sqlite_sequence`, `pain_points`, `clusters`, `ideas`, `raw_item_embeddings`

**2. Table Counts & Info:**
- `raw_items`: 1,548 rows
- `pain_points`: 1,146 rows 
  *(WTP Type Distribution: unknown (1095), explicit_dollar (30), incumbent_pricing (10), time_cost (8), switching (3))*
- `clusters`: 31 rows
- `ideas`: 2 rows

**3. Source Distribution (Top 10):**
- stackoverflow: 244
- reddit:r/AmazonSeller: 100
- reddit:r/FreightBrokers: 100
- reddit:r/FulfillmentByAmazon: 100
- reddit:r/RealEstate: 100
- reddit:r/Truckers: 100
- reddit:r/bartenders: 100
- reddit:r/realtors: 100
- reddit:r/restaurateur: 100
- reddit:r/smallbusiness: 55

**4. Cluster Funnel:**
- Total Clusters: 31
- Qualified Clusters (`size >= 8 AND source_diversity >= 2 AND wtp_evidence_count >= 5`): **2**

**5. Startup Ideas Status:**
- `candidate`: 2

**Verdict:**
A massive chunk of the DB is real signal (1,548 raw items), but the LLM extraction logic is failing. The fact that 1,095 out of 1,146 pain points have an `unknown` Willingness-to-Pay indicates the extractor is stripping specificity (Violates Principle 2). The data itself is valuable and must be preserved, but the `pain_points` and `clusters` tables should be re-extracted under the new anomaly-first architecture. 

---

## 4. Obsidian Vault Audit (`D:\Start\Market_Intelligence_Vault\`)

- `00_Master_Dashboard.md`: Living Reference - **REFACTOR**
- `01_Foundations/` - `05_Tools_and_Repositories/`: Living Reference - **KEEP**
- `06_Market_Scans/`: Mixed.
  - Legacy `.md` files (e.g., `AI-ML-Infrastructure-MLOps-Deployment-Pain-Points.md`) are stale outputs. **DELETE** to prevent noise.
  - `D2C_and_Logistics_Insights_Sahil_Goel.md`: Living Reference - **KEEP**
  - `_broken/` folder: Junk - **DELETE**
- `07_Go_To_Market/`: Living Reference (e.g. `Zero_Dollar_Bootstrap_Playbook.md`) - **KEEP**

---

## 5. `.opencode` Configuration Audit

- `D:\Start\.opencode.json`: **MISSING** (Needs to be explicitly rebuilt if sub-agent routing is expected at a workspace level).
- `D:\Start\.opencode\skills\`: Contains 8 sub-agent Markdown definitions (`startup-validator`, `model-router`, `market-gap-finder`, etc.).
  - **Verdict**: **REFACTOR**. The agent logic described in the vault (Scout, Ingestor, Extractor, Architect) does not match the actual `.opencode/skills/` configurations present. The current skills violate Principle 3 (Tiering) as they do not enforce model assignment based on cognitive load.

---

## 6. Environment & Credentials Audit

**`D:\Start\.env` Keys:**
- GEMINI_API_KEY=SET
- GOOGLE_API_KEY=SET
- GROQ_API_KEY=SET
- GROQ_API_KEY2=SET
- OPENROUTER_API_KEY=SET
- GITHUB_TOKEN=SET
- TOKENROUTER_API_KEY=SET

**`D:\Start\project\.env` Keys:**
- GEMINI_API_KEY=SET
- GOOGLE_API_KEY=SET
- GEMINI_API_KEYS=SET
- GROQ_API_KEY=SET
- GROQ_API_KEYS=SET
- OPENROUTER_API_KEY=SET
- GITHUB_TOKEN=SET
- VAULT_SCANS_PATH=SET

**Usable Providers:** 
Gemini (via Google API), Groq, OpenRouter, and GitHub Models are correctly configured. Historically, Groq hits RPM (Requests Per Minute) limits aggressively due to the speed of execution, causing silent failures. This makes the introduction of `budget_manager.py` (Principle 4) critical.

---

## 7. External Artifacts Audit

- `Market_Intelligence_Engine_Architecture.docx` - Stale Vision output. **DELETE**.
- `Sahil_Goel_Insights.docx` - Historical. **DELETE**.
- `Sahil_Goel_Transcript.docx` - Historical. **DELETE**.
- `RESEARCH_REPO_LANDSCAPE.md` - (Not found in tree, but conceptually living reference) - **KEEP**.
- `ANTIGRAVITY_BRIEF_*.md` - Historical artifacts. **DELETE** to reduce repo clutter.

---

## 8. Summary Table (The Takeaway)

| Component | Status | Verdict | Reason |
| :--- | :--- | :--- | :--- |
| `mcp_server.py` | Dead | **DELETE** | Obsolete; Violates zero-cost/local-only constraints. |
| `miners/g2_miner.py` | Dead | **DELETE** | G2 anti-scraping blocks violate Principle 4 (Rate Limits). |
| `miners/producthunt_miner.py` | Dead | **DELETE** | Low signal-to-noise ratio; poor time-capital investment. |
| `extractors/gap_synthesizer.py`| Dead | **DELETE** | Replaced by dual-output functionality. |
| `project/output/` | Stale | **DELETE** | Consolidate outputs in the Vault (Principle 5). |
| `.docx` at Root | Stale | **DELETE** | Obsolete generated artifacts. |
| `main.py` | Needs work | **REFACTOR** | Needs CLI trend-check prompt to stop autonomous runs (Principle 1). |
| `key_manager.py` | Needs work | **REFACTOR** | Add `model_tier` cascades (fast/deep) (Principle 3). |
| `pain_extractor.py` | Needs work | **REFACTOR** | Add specificity guardrails; reject generic nouns (Principle 2). |
| `idea_ranker.py` | Needs work | **REFACTOR** | Replace invented SaaS names with anomaly digests (Principle 2). |
| `vault_exporter.py` | Needs work | **REFACTOR** | Update to export both markdown and docx (Principle 5). |
| `.opencode/skills/` | Divergent | **REFACTOR** | Sync sub-agent configs with architecture vision (Principle 3). |
| `miners/reddit, youtube...`| Works | **KEEP** | Core data ingestion infrastructure. |
| `storage/db.py` | Works | **KEEP** | Preserve the database state and schema. |
| `data/intel.db` | Works | **KEEP** | Do not wipe. 1,548 source rows are valuable. |
| `validators/trend_validator.py`| Works | **KEEP** | Needed for human-in-the-loop market checks (Principle 1). |
| `compressor.py` | Works | **KEEP** | Required utility for context window optimization. |

---

## 9. Estimated Line Counts

- **Total Python LOC in `project/`**: ~2,993 LOC
- **LOC to DELETE**: ~315 LOC (`mcp_server.py`, `g2_miner.py`, `producthunt_miner.py`, `gap_synthesizer.py`, `wipe_extracted.py`)
- **LOC to KEEP**: ~1,200 LOC (`db.py`, `compressor.py`, standard miners, `trend_validator.py`)
- **LOC to REFACTOR**: ~1,478 LOC 
  - `key_manager.py` (Low Effort - Inject literal types)
  - `pain_extractor.py` (Medium Effort - Add regex/guardrail loops)
  - `idea_ranker.py` (High Effort - Complete rewrite to anomaly digest)
  - `cluster.py` (High Effort - Complete rewrite for specificity)
  - `main.py` (Medium Effort - Wire in new BudgetManager)
