# Phase 0: Architecture Audit

Based on the mandate: *"Inspect the existing repository and classify every component: KEEP, MERGE, MOVE, REWRITE, DELETE, UNKNOWN. Do not build anything new until we understand what already exists."*

Here is the exhaustive classification of our current repository to align with the new pipeline.

### 🔴 DELETE (or Archive)
*Rule: Do not build 15 data sources before one works end-to-end. Validation comes in Phase 8.*
* `src/miners/alternativeto_miner.py`
* `src/miners/github_issues_miner.py`
* `src/miners/github_miner.py`
* `src/miners/hn_miner.py`
* `src/miners/shopify_reviews_miner.py`
* `src/miners/stackoverflow_miner.py`
* `src/miners/youtube_miner.py`
* `src/validators/trend_validator.py` (Validation layer doesn't exist yet)
* `scan_verticals.py` (Outdated batch script)
* `run_all.ps1`, `run_final.ps1`, `run_rest.ps1` (Outdated orchestration scripts)

### 🟡 REWRITE (Core Architecture Changes)
*Rule: Make the pipeline structurally correct, provider-independent, and cheap.*
* **`main.py`**: Currently a monolithic CLI. Must be rewritten as the core Pipeline Orchestrator that flows linearly: `Reddit → Normalization → Extraction → JEV → Clustering → Opportunity → Deep Reasoning`.
* **`src/key_manager.py`**: Currently mixes routing, fetching, and extraction. Must be rewritten as `orchestration/router/` to purely handle model orchestration (Decision Models vs. Extraction Models).
* **`src/storage/db.py`**: Must be rewritten to support the new Canonical Data Schemas (`Evidence`, `Observation`, `PainPoint`, `Cluster`, `Opportunity`).

### 🔵 MOVE (Refactor to New Folders)
*Rule: Separate evidence, extraction, decisions, analysis, validation, and generation.*
* `src/miners/reddit_miner.py` ➔ MOVE TO `ingestion/reddit/`
* `src/extractors/pain_extractor.py` ➔ MOVE TO `intelligence/extraction/`
* `src/compressor.py` ➔ MOVE TO `intelligence/extraction/`
* `src/extractors/cluster.py` ➔ MOVE TO `analysis/clustering/`
* `src/extractors/idea_ranker.py` ➔ MOVE TO `analysis/opportunities/`
* `src/exporters/vault_exporter.py` ➔ MOVE TO `diffusion/dossier/`
* `src/orchestration/budget_manager.py` ➔ MOVE TO `orchestration/budget/`
* `test_key_manager.py` (root folder) ➔ MOVE TO `tests/`

### 🟢 KEEP (Foundations)
* `.env`, `.gitignore`, `requirements.txt`
* `src/config.py`
* The `tests/` directory architecture (though specific tests will update as files move)
* `data/` directory (for SQLite dbs)

### 🟣 UNKNOWN / TBD
* `src/miners/jina_fetcher.py`: Could be used for generic URL scraping, but might need to be rewritten to fit the generic "Normalization" layer.

---

### Immediate Action Plan
1. Create an `_archive` folder and sweep all the **DELETE** files into it so we don't lose the code permanently, but they are out of the execution path.
2. Create the target directories (`ingestion/`, `intelligence/`, `analysis/`, `diffusion/`, `orchestration/`).
3. Move the **MOVE** files into their new homes.
4. Draft the **Canonical Schemas** in `src/storage/db.py` (Phase 1).
