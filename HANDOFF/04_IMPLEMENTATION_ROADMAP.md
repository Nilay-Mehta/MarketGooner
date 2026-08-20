# 04 — Implementation Roadmap

This document converts the Target Architecture (`03_TARGET_ARCHITECTURE.md`) into a phased execution plan. It is a sequence of atomic, verifiable steps that an engineer (or an AI agent) can execute one at a time.

**Enforcement Principle:** ONE thing at a time. Every step must be verifiable in isolation. No step depends on assumptions from a step that has not yet been run and verified.

---

## 1. Roadmap Overview

- **Total number of phases:** 10 (Phase 0 through Phase 9)
- **Total number of atomic steps:** 32
- **Estimated wall-clock effort:** ~14 hours of focused engineer time.
- **Critical Path:** Phase 1 (Model Tier Split) and Phase 2 (Specificity Guardrails) must succeed before any orchestration (Phase 4) or deployment (Phases 5-8) begins. If the core logic cannot produce specific, anomaly-based outputs on the deep tier, the rest of the pipeline is moot.

---

## 2. Phase 0 — Preserve and Prepare
*Goal: Secure the existing data and clean the workspace for the new architecture.*

1. **Step 0.1:** Backup `data/intel.db` to `intel.db.bak.YYYYMMDD` (with today's datestamp) to ensure the 1,548 raw items are safe.
2. **Step 0.2:** Confirm all HANDOFF docs (01-05) exist on disk. Run `Test-Path` on each.
3. **Step 0.3:** Archive legacy brief files. Move `ANTIGRAVITY_BRIEF_*.md` to `D:\Start\_archive\`.
4. **Step 0.4:** Clean up legacy code. Delete `mcp_server.py`, `miners/g2_miner.py`, `miners/producthunt_miner.py`, `extractors/gap_synthesizer.py`, and `wipe_extracted.py`.
5. **Step 0.5:** Move root `.docx` living references (`Sahil_Goel_Insights.docx`, `Sahil_Goel_Transcript.docx`) into `Market_Intelligence_Vault\01_Foundations\`. Delete `Market_Intelligence_Engine_Architecture.docx`.

---

## 3. Phase 1 — Model Tier Split
*Goal: Fix the single highest-leverage failure point by routing synthesis to the deep tier.*

6. **Step 1.1:** Modify `src/key_manager.py`. Add the `model_tier: Literal['fast','deep']` parameter with the exact provider cascades specified in Doc 03, Section 4. Add per-call logging showing tier + provider.
7. **Step 1.2:** Modify `src/extractors/idea_ranker.py`. Hardcode `tier='deep'` on every LLM call.
8. **Step 1.3:** Verify Phase 1. Run ONLY `python main.py rank`. Confirm via logs that no deep-tier calls landed on Groq, Cerebras, or Gemini Flash. Read the output. If it contains invented SaaS names (e.g. AgentSphere), Phase 1 has failed (but the wiring succeeded), and Phase 2 becomes urgent.

*Do NOT proceed to Phase 2 until Phase 1 verification passes or the user explicitly confirms the results.*

---

## 4. Phase 2 — Specificity Guardrails
*Goal: Enforce Principle 2 by blocking abstract summaries.*

9. **Step 2.1:** Modify `src/extractors/pain_extractor.py`. Add a Pydantic validator to the extraction schema that rejects the output if it contains generic buckets (like "cost issues") without at least one preserved proper noun or specific $ amount matching the source chunk.
10. **Step 2.2:** Modify `src/extractors/idea_ranker.py`. Replace the startup-idea schema with the **Anomaly Digest Schema**. Must include: repeated proper nouns (3+), specific $ amounts, and verbatim quotes with URLs.
11. **Step 2.3:** End-to-end extraction verify. Run `python main.py extract --re-extract`, then `python main.py cluster --recluster`, then `python main.py rank`. Assert that the output meets Principle 2 (No invented names, specific quotes preserved).

---

## 5. Phase 3 — Budget Manager + Rate-Limit Halt
*Goal: Enforce Principle 4 (Graceful degrade).*

12. **Step 3.1:** Create `src/orchestration/budget_manager.py`. Define the `BudgetManager` class with in-memory `tpd_used` and `rpm_used` tracking dictionaries.
13. **Step 3.2:** Wire `budget_manager.py` into `key_manager.py`. Implement the cascade fallback logic, raising `RateLimitHalt` when all tier providers are exhausted.
14. **Step 3.3:** Implement halt-and-resume orchestration in `main.py`. Catch `RateLimitHalt`, save queue state to disk, and verify by injecting a fake 429 response to assert the pipeline halts and prints the resume CLI verb.

---

## 6. Phase 4 — Multi-Agent Orchestration
*Goal: Introduce the Master, Scout, and Copywriter agents.*

15. **Step 4.1:** Build `src/agents/scout_agent.py`. Implement the human go/no-go prompt (Google Trends check).
16. **Step 4.2:** Build `src/agents/master_agent.py`. Implement dispatch logic to miners based on user input.
17. **Step 4.3:** Build `src/agents/copywriter_agent.py`. Implement the marketing brief generation logic using the Anomaly Digest. Wire all three into `main.py` CLI verbs.

---

## 7. Phase 5 — Local Runtime (llama.cpp)
*Goal: Establish the absolute fallback tier.*

18. **Step 5.1:** Install `llama.cpp` locally on Windows 11 using precompiled binaries.
19. **Step 5.2:** Download Gemma 3n E4B GGUF model via huggingface-cli.
20. **Step 5.3:** Spin up `llama-server`. Register `http://localhost:8080/v1` as the final fallback in the Fast Tier cascade in `key_manager.py`. Verify by triggering a fallback condition.

---

## 8. Phase 6 — Semantic Search Layer
*Goal: Enable Datasette UI auditing.*

21. **Step 6.1:** Install `sqlite-vec` and `sentence-transformers` via pip.
22. **Step 6.2:** Update `src/storage/db.py` to initialize `sqlite-vec` extensions and create the `raw_item_embeddings` virtual table.
23. **Step 6.3:** Build embedding backfill script and add `python main.py search` verb. Verify by querying for a specific semantic string.

---

## 9. Phase 7 — India Geo Expansion
*Goal: Expand target data sources.*

24. **Step 7.1:** Execute Database migration. `ALTER TABLE raw_items ADD COLUMN geo TEXT;` (Backfill existing with 'US').
25. **Step 7.2:** Create `src/miners/india_miner.py` implementing scrapers for `r/IndianEntrepreneur` and Jina API for IndiaMART.
26. **Step 7.3:** Update Master Agent and `scan_verticals.py` to accept `--geo IN` arguments and filter clusters geographically.

---

## 10. Phase 8 — Dual Output Rendering
*Goal: Enforce Principle 5 (Dual output).*

27. **Step 8.1:** Install `python-docx` and update `vault_exporter.py` imports.
28. **Step 8.2:** Implement `.docx` generation routines for the Startup Dossier output shape.
29. **Step 8.3:** Implement `.docx` generation routines for the Marketing Brief output shape. Write both to `Market_Intelligence_Vault\06_Market_Scans\` with date-stamped filenames.

---

## 11. Phase 9 — Handoff Verification
*Goal: Prove success.*

30. **Step 9.1:** Execute `python main.py scout "Toll fraud in Indian logistics"`. Verify Trend check pauses for human input.
31. **Step 9.2:** Execute full run. Confirm gracefully degrades (no silent errors) and produces 2 output shapes.
32. **Step 9.3:** Founder reviews the final dossier. Must meet all 5 criteria in Doc 01, Section 5.

---

## 12. Failure Protocol

When a step fails verification:
1. **Rollback:** Revert the git commit for that specific atomic step.
2. **Diagnose:** Do not guess. Inspect the specific Pydantic validation error, the exact rate limit header, or the SQLite exception.
3. **Halt:** Do not proceed to the next step.
4. **No Parallel Work:** Do not attempt to fix a Phase 4 issue while Phase 2 is broken. Fix the blocker first.

---

## 13. Brief Templates (For Antigravity)

*These briefs are designed to be copy-pasted directly into Antigravity one by one.*

### BRIEF FOR ANTIGRAVITY — Phase 0 Step 1
**Task:** Backup the database.
**Exact commands:** `Copy-Item D:\Start\project\data\intel.db -Destination D:\Start\project\data\intel.db.bak.$(Get-Date -Format 'yyyyMMdd')`
**Verification:** `Test-Path D:\Start\project\data\intel.db.bak.*` must return True.
**Do-not-touch list:** Do not modify any python files.
**Report format:** Provide the terminal output of the verification command.

### BRIEF FOR ANTIGRAVITY — Phase 0 Step 2
**Task:** Verify HANDOFF docs.
**Exact commands:** Run `Test-Path` on `01_VISION_AND_PRINCIPLES.md`, `02_CURRENT_STATE_AUDIT.md`, `03_TARGET_ARCHITECTURE.md`, `04_IMPLEMENTATION_ROADMAP.md`.
**Verification:** All must output True.
**Do-not-touch list:** Do not modify any markdown files.
**Report format:** Provide the terminal output.

### BRIEF FOR ANTIGRAVITY — Phase 0 Step 3
**Task:** Archive historical briefs.
**Exact commands:** `mkdir D:\Start\_archive; Move-Item D:\Start\ANTIGRAVITY_BRIEF_*.md -Destination D:\Start\_archive\`
**Verification:** Confirm the archive folder contains the files.
**Do-not-touch list:** Do not modify any code.
**Report format:** Provide the terminal output of `ls D:\Start\_archive\`.

### BRIEF FOR ANTIGRAVITY — Phase 0 Step 4
**Task:** Delete legacy codebase files.
**Exact commands:** Delete `D:\Start\project\mcp_server.py`, `D:\Start\project\src\miners\g2_miner.py`, `D:\Start\project\src\miners\producthunt_miner.py`, `D:\Start\project\src\extractors\gap_synthesizer.py`, and `D:\Start\project\wipe_extracted.py`.
**Verification:** Run `Test-Path` on each to ensure they return False.
**Do-not-touch list:** Do not delete `reddit_miner.py` or any database files.
**Report format:** Output git status showing deleted files.

### BRIEF FOR ANTIGRAVITY — Phase 0 Step 5
**Task:** Move living references, delete stale architecture doc.
**Exact commands:** Move `Sahil_Goel_Insights.docx` and `Sahil_Goel_Transcript.docx` to `D:\Start\Market_Intelligence_Vault\01_Foundations\`. Delete `D:\Start\Market_Intelligence_Engine_Architecture.docx`.
**Verification:** Run `Test-Path` on the new destinations.
**Do-not-touch list:** Do not touch the vault's markdown notes.
**Report format:** Terminal output of verification.

### BRIEF FOR ANTIGRAVITY — Phase 1 Step 1
**Task:** Implement Model Tier Split in KeyManager.
**Files to modify:** `D:\Start\project\src\key_manager.py`
**Actions:** Add `model_tier: Literal['fast','deep']='fast'` to the generation functions. Implement the cascade: Fast = Groq 70B -> Cerebras -> Gemini Flash. Deep = Gemini Pro -> GitHub GPT-4o -> OpenRouter Claude. Add a print/log statement on every call showing which tier + provider fielded it.
**Verification:** Run `python -c "import src.key_manager"` to check for syntax errors.
**Do-not-touch list:** Do not touch the database logic.
**Report format:** Output the diff of `key_manager.py`.

### BRIEF FOR ANTIGRAVITY — Phase 1 Step 2
**Task:** Route Idea Ranker to Deep Tier.
**Files to modify:** `D:\Start\project\src\extractors\idea_ranker.py`
**Actions:** Find every LLM generation call in the file. Add the `tier='deep'` argument.
**Verification:** Ensure all tests or syntax checks pass.
**Do-not-touch list:** Do not rewrite the ranking logic yet.
**Report format:** Output the diff of `idea_ranker.py`.

### BRIEF FOR ANTIGRAVITY — Phase 1 Step 3
**Task:** Verify Tier Routing.
**Actions:** Run `python main.py rank`. 
**Verification:** Read the terminal output. Assert that the logs from `key_manager` explicitly say `[DEEP]` and route to Gemini Pro / GPT-4o. If they say `[FAST]` or route to Groq, fail.
**Do-not-touch list:** Do not touch code, just execute and read.
**Report format:** Paste the raw terminal output of the rank command. Stop and await human verification.

### BRIEF FOR ANTIGRAVITY — Phase 2 Step 1
**Task:** Specificity Guardrails in Extractor.
**Files to modify:** `D:\Start\project\src\extractors\pain_extractor.py`
**Actions:** Update the Pydantic schema for `PainPoint` to include `@model_validator(mode='after')`. The validator must fail if `proper_nouns_preserved` is empty AND `wtp_evidence` lacks a specific $ amount, while summary contains generic words ("cost", "pricing").
**Verification:** Run `pytest tests/test_extraction_pipeline.py` (or write a quick unit test if it doesn't exist) to assert generic buckets throw a ValidationError.
**Do-not-touch list:** Do not touch miners.
**Report format:** Show the test output.

### BRIEF FOR ANTIGRAVITY — Phase 2 Step 2
**Task:** Anomaly Digest in Ranker.
**Files to modify:** `D:\Start\project\src\extractors\idea_ranker.py`
**Actions:** Replace the `StartupIdea` Pydantic output schema with an `AnomalyDigest` schema (requires `repeated_proper_nouns`, `specific_dollar_amounts`, `verbatim_quotes_with_urls`). Rewrite the system prompt to explicitly forbid inventing SaaS names.
**Verification:** Syntax check the file.
**Do-not-touch list:** Do not touch `cluster.py`.
**Report format:** Output the diff.

### BRIEF FOR ANTIGRAVITY — Phase 2 Step 3
**Task:** End-to-End Extraction Verification.
**Actions:** Run `python main.py extract --re-extract`, then `python main.py cluster --recluster`, then `python main.py rank`.
**Verification:** Inspect the generated database rows or terminal output. Confirm no "AgentSphere" names exist.
**Do-not-touch list:** Do not fetch new data.
**Report format:** Output the final digested ideas.

### BRIEF FOR ANTIGRAVITY — Phase 3 Step 1
**Task:** Build BudgetManager state trackers.
**Files to modify:** `D:\Start\project\src\orchestration\budget_manager.py` (NEW)
**Actions:** Define `BudgetManager` class with dictionaries tracking `tpd_used` and `rpm_used`.
**Verification:** Import the class in python to ensure no syntax errors.
**Do-not-touch list:** Do not wire into `key_manager.py` yet.
**Report format:** Provide file contents.

### BRIEF FOR ANTIGRAVITY — Phase 3 Step 2
**Task:** Wire BudgetManager into cascades.
**Files to modify:** `D:\Start\project\src\key_manager.py`
**Actions:** Wire `budget_manager` into cascade logic. Raise `RateLimitHalt` when limits hit.
**Verification:** Run mock call loop.
**Do-not-touch list:** Do not modify `main.py`.
**Report format:** Diff output.

### BRIEF FOR ANTIGRAVITY — Phase 3 Step 3
**Task:** Orchestrate Halt and Resume.
**Files to modify:** `D:\Start\project\main.py`
**Actions:** Catch `RateLimitHalt`, write state queue to `data/verify_last.json`, and print `--resume` instructions.
**Verification:** Inject a fake 429 response during a dummy run. Confirm halt and resume printout.
**Do-not-touch list:** Do not touch `budget_manager.py`.
**Report format:** Terminal output of the simulated crash.

### BRIEF FOR ANTIGRAVITY — Phase 4 Step 1
**Task:** Build Scout Agent.
**Files to modify:** `D:\Start\project\src\agents\scout_agent.py` (NEW)
**Actions:** Create agent to query `pytrends` and print `Proceed? [Y/n]`.
**Verification:** Run standalone script.
**Do-not-touch list:** Do not wire to main.
**Report format:** Output execution log.

### BRIEF FOR ANTIGRAVITY — Phase 4 Step 2
**Task:** Build Master Agent.
**Files to modify:** `D:\Start\project\src\agents\master_agent.py` (NEW)
**Actions:** Build dispatcher converting user prompts into search vectors for miners.
**Verification:** Syntax check.
**Do-not-touch list:** Do not touch miners.
**Report format:** File dump.

### BRIEF FOR ANTIGRAVITY — Phase 4 Step 3
**Task:** Build Copywriter Agent & CLI verbs.
**Files to modify:** `D:\Start\project\src\agents\copywriter_agent.py` (NEW), `D:\Start\project\main.py`
**Actions:** Build agent for Marketing Briefs. Wire Scout, Master, Copywriter into `main.py` command line arguments.
**Verification:** Run `python main.py --help` and verify new verbs exist.
**Do-not-touch list:** Do not modify DB.
**Report format:** Output of help command.

### BRIEF FOR ANTIGRAVITY — Phase 5 Step 1
**Task:** Install llama.cpp local environment.
**Exact commands:** Download precompiled binary for Windows. 
**Verification:** Run `./llama-server.exe --version`.
**Do-not-touch list:** Do not write python code.
**Report format:** Output version string.

### BRIEF FOR ANTIGRAVITY — Phase 5 Step 2
**Task:** Download Gemma 3n E4B.
**Exact commands:** `huggingface-cli download ...`
**Verification:** `Test-Path` on the `.gguf` file.
**Do-not-touch list:** Do not start server yet.
**Report format:** Output file size.

### BRIEF FOR ANTIGRAVITY — Phase 5 Step 3
**Task:** Wire llama-server into KeyManager.
**Files to modify:** `D:\Start\project\src\key_manager.py`
**Actions:** Add `http://localhost:8080/v1` to the end of the fast cascade.
**Verification:** Synthetically exhaust all fast tier APIs and verify local fallback triggers.
**Do-not-touch list:** Do not touch deep tier.
**Report format:** Log output of local fallback firing.

### BRIEF FOR ANTIGRAVITY — Phase 6 Step 1
**Task:** Install sqlite-vec.
**Exact commands:** `pip install sqlite-vec sentence-transformers`
**Verification:** `pip show sqlite-vec`.
**Do-not-touch list:** Do not touch `db.py`.
**Report format:** Pip output.

### BRIEF FOR ANTIGRAVITY — Phase 6 Step 2
**Task:** DB Schema for Embeddings.
**Files to modify:** `D:\Start\project\src\storage\db.py`
**Actions:** Initialize `sqlite-vec` connection and create `raw_item_embeddings` table.
**Verification:** Run `SELECT vec_version();` in sqlite3.
**Do-not-touch list:** Do not touch existing tables.
**Report format:** Output of SQL version string.

### BRIEF FOR ANTIGRAVITY — Phase 6 Step 3
**Task:** Implement Semantic Search CLI.
**Files to modify:** `D:\Start\project\main.py`
**Actions:** Add a `search "<query>"` verb to embed query and run vector similarity join.
**Verification:** Run `python main.py search "freight pricing"`.
**Do-not-touch list:** Do not touch extraction.
**Report format:** Output of query result.

### BRIEF FOR ANTIGRAVITY — Phase 7 Step 1
**Task:** Add Geo Column.
**Exact commands:** Python script executing `ALTER TABLE raw_items ADD COLUMN geo TEXT DEFAULT 'US';`
**Verification:** Describe table schema.
**Do-not-touch list:** Do not drop data.
**Report format:** Schema dump.

### BRIEF FOR ANTIGRAVITY — Phase 7 Step 2
**Task:** Build India Miner.
**Files to modify:** `D:\Start\project\src\miners\india_miner.py` (NEW)
**Actions:** Implement scrapers for r/IndianEntrepreneur and Jina API.
**Verification:** Run standalone to fetch 5 items.
**Do-not-touch list:** Do not touch US miners.
**Report format:** Output of items.

### BRIEF FOR ANTIGRAVITY — Phase 7 Step 3
**Task:** Update Geo Routing.
**Files to modify:** `D:\Start\project\main.py`, `D:\Start\project\scan_verticals.py`
**Actions:** Add `--geo IN` argument to command line flow. Update SQL queries to filter by `geo`.
**Verification:** Syntax check.
**Do-not-touch list:** Do not touch vault exporter.
**Report format:** Diff outputs.

### BRIEF FOR ANTIGRAVITY — Phase 8 Step 1
**Task:** Install python-docx.
**Exact commands:** `pip install python-docx`
**Verification:** `python -c "import docx"`
**Do-not-touch list:** Do not modify exporters yet.
**Report format:** Command output.

### BRIEF FOR ANTIGRAVITY — Phase 8 Step 2
**Task:** Startup Dossier Docx Export.
**Files to modify:** `D:\Start\project\src\exporters\vault_exporter.py`
**Actions:** Implement `.docx` generator for the Anomaly Digest. Write to `Market_Intelligence_Vault\06_Market_Scans\`.
**Verification:** Run export on existing dummy DB data. Check file creation.
**Do-not-touch list:** Do not modify DB.
**Report format:** `Test-Path` of file.

### BRIEF FOR ANTIGRAVITY — Phase 8 Step 3
**Task:** Marketing Brief Docx Export.
**Files to modify:** `D:\Start\project\src\exporters\vault_exporter.py`
**Actions:** Implement `.docx` generator for Marketing Briefs.
**Verification:** Run export.
**Do-not-touch list:** Do not modify DB.
**Report format:** `Test-Path` of file.

### BRIEF FOR ANTIGRAVITY — Phase 9 Step 1
**Task:** Scout Validation End-to-End.
**Actions:** Run `python main.py scout "Toll fraud in Indian logistics"`.
**Verification:** Ensure it prints Trend Go/No-Go and asks for Proceed.
**Do-not-touch list:** Do not skip manual review.
**Report format:** Terminal interaction log.

### BRIEF FOR ANTIGRAVITY — Phase 9 Step 2
**Task:** Full Execution End-to-End.
**Actions:** Hit 'Y' on scout to initiate the run.
**Verification:** Confirm run completes without silent failure and produces outputs in Vault.
**Do-not-touch list:** Do not interrupt process unless halted.
**Report format:** `ls Market_Intelligence_Vault\06_Market_Scans\` showing output files.

### BRIEF FOR ANTIGRAVITY — Phase 9 Step 3
**Task:** Dossier Review.
**Actions:** None (Human review).
**Verification:** Founder reads dossier. Must meet 5 criteria.
**Do-not-touch list:** NA.
**Report format:** Founder explicit approval.
