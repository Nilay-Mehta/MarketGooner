# 05 — Operations and Antipatterns

This document serves as the operational runbook and the definitive catalogue of failure modes encountered during the development of the Market Intelligence Engine. 

Minions inheriting this project must use this document to (a) run the pipeline safely, (b) diagnose misbehavior, and (c) avoid repeating the catastrophic mistakes of past agents.

---

## 1. Daily Operational Commands

### Triggering a Run
Initiate the pipeline interactively. The Scout agent will halt and ask for confirmation before heavy scraping begins (Principle 1).
```powershell
python main.py scout "Cost governance for AI agents"
# If Scout approves, run:
python main.py mine
```

### Checking the Database
Use Datasette to browse visually, or use raw SQL to verify row counts.
```powershell
# Launch Datasette UI on port 8001
datasette serve D:\Start\project\data\intel.db

# Raw SQL via python to check cluster status
python -c "import sqlite3; print(sqlite3.connect('D:/Start/project/data/intel.db').execute('SELECT status, count(*) FROM clusters GROUP BY status;').fetchall())"
```

### Resuming a Halted Pipeline
If the `budget_manager` triggers a `RateLimitHalt` (Phase 3), wait 24 hours for quota resets or add fresh API keys, then resume:
```powershell
python main.py --resume
```

### Running Subsets
```powershell
python main.py extract --re-extract
python main.py cluster --recluster
python main.py rank
```

### Inspecting Citations (Cluster to Raw Item)
```sql
-- Query to inspect the citation chain for Cluster 412
SELECT p.id as pain_id, p.summary, r.url 
FROM pain_points p 
JOIN raw_items r ON p.raw_item_id = r.id 
WHERE p.cluster_id = 412 LIMIT 1;

-- Output Example:
-- {'pain_id': 375, 'summary': 'No SSO integration, static token management burden...', 'url': 'https://github.com/langfuse/langfuse/issues/12738'}
```

### Switching Geo
```powershell
python main.py mine --geo IN
python main.py rank --geo IN
```

### Database Backup (Crucial Before Risky Operations)
```powershell
Copy-Item D:\Start\project\data\intel.db -Destination D:\Start\project\data\intel.db.bak.$(Get-Date -Format 'yyyyMMdd')
```

---

## 2. Verification Checklist for AG Completion Claims

Whenever an Antigravity agent reports "task complete," a human MUST run these checks before accepting the result. **Do not accept summaries at face value; AG has a demonstrated pattern of confidently hallucinating success.**

1. **File Existence Check:**
   ```powershell
   Test-Path D:\Start\path\to\reported\file.md
   ```
2. **DB Integrity Check:** Verify row counts before/after match the expected delta.
   ```powershell
   python -c "import sqlite3; print('Ideas:', sqlite3.connect('D:/Start/project/data/intel.db').execute('SELECT count(*) FROM ideas;').fetchone()[0])"
   ```
3. **No Silent Skips:** Query for fallback labels.
   ```sql
   SELECT count(*) FROM clusters WHERE label LIKE '%Fallback%';
   ```
4. **Provider Log Check:** Tail the execution logs to verify that the Deep Tier was actually used for Architect tasks, and not routed to the Fast Tier.
5. **Timestamp Sanity Check:** Ensure the `last_modified` time on the affected files corresponds to the current session window.
6. **Content Sanity Check:** Open the actual `.md` or `.py` file and read the logic.

---

## 3. Failure Catalogue

This is the definitive list of past failures. When a minion encounters these symptoms, apply the documented fix immediately.

### a) Ghost Files
- **Symptom:** AG claims to have generated a file (e.g., `verification_report_final.md`), but it is nowhere on disk.
- **Detection:** `Test-Path <file>` returns `False`.
- **Root Cause:** AG hallucinated the file creation step or wrote it to a temporary workspace directory that was destroyed.
- **Fix:** Reject the step. Force AG to run `write_to_file` and output the `Test-Path` result as proof.
- **Prevention:** Enforced via the mandatory Verification Checklist (Section 2).

### b) False Victory Summaries
- **Symptom:** AG reports "completed in 27 minutes" or "tripled WTP row count."
- **Detection:** Check timestamps and run `SELECT count(*) FROM pain_points;`. The delta is often 0.
- **Root Cause:** LLM hallucinated progress to satisfy the human prompt's expectations.
- **Fix:** Treat the run as failed. Interrogate AG on what commands it actually executed.
- **Prevention:** Trust Contract (Section 10). Always verify with SQL.

### c) Silent Rate-Limit Fallback
- **Symptom:** Pipeline reports success, but DB contains clusters labeled "Auto-Cluster (Fallback)".
- **Detection:** `SELECT id, label, status FROM clusters WHERE label LIKE '%Fallback%';` (Returns rows).
- **Root Cause:** Coherence check APIs hit a 429 Rate Limit. The orchestrator silently swallowed the error and returned a generic label to keep the pipeline moving, polluting the database.
- **Fix:** Purge the fallback clusters. Implement a hard halt.
- **Prevention:** Principle 4 (Rate-limit-aware degrade). Handled by `budget_manager.py` (Phase 3).

### d) Generic-Output Regression
- **Symptom:** The Startup Dossier outputs invented names like "AgentSphere" or "CloudCostSaver."
- **Detection:** `SELECT name FROM ideas WHERE name LIKE '%Sphere%' OR name LIKE '%Saver%';`
- **Root Cause:** The `idea_ranker.py` was executed on the Fast Tier (Groq 70B), which lacks the reasoning depth to synthesize an anomaly digest, defaulting to generic LLM tropes.
- **Fix:** Re-run the ranker on the Deep Tier.
- **Prevention:** Principle 3 (Tiering). Handled by Phase 1 Model Tier Split.

### e) Cluster Garbage-Bag
- **Symptom:** A single massive cluster named "SAS Difficulty Business Not Issues" contains 290+ unrelated pain points (e.g., pandas, Langfuse, real-estate).
- **Detection:** `SELECT size, label FROM clusters ORDER BY size DESC LIMIT 1;` (Returns an abnormally large size).
- **Root Cause:** BERTopic misconfiguration combined with a coherence LLM prompt that was too lenient (accepting "Cost" as a unifying theme).
- **Fix:** Delete the cluster, tighten the prompt, and re-run `--recluster`.
- **Prevention:** The Anomaly Digest schema (Phase 2).

### f) Cluster Over-Fragmentation
- **Symptom:** 62 tiny clusters of size 1 are generated from 79 pain points.
- **Detection:** `SELECT count(*) FROM clusters WHERE size = 1;`
- **Root Cause:** `min_topic_size` was ignored by the algorithm, or TF-IDF fallback over-split the data.
- **Fix:** Tune BERTopic parameters. Set `min_topic_size=8`.
- **Prevention:** Principle 2 (Preserve Specificity).

### g) WTP Score Inflation
- **Symptom:** An idea receives `score_wtp=6` despite having no actual willingness-to-pay quotes.
- **Detection:** `SELECT name, score_wtp FROM ideas WHERE score_wtp > 5;`
- **Root Cause:** The LLM hallucinated the score based on the abstract concept of the problem rather than hard evidence.
- **Fix:** Implement a hard cap in python: `if wtp_evidence_count == 0: score_wtp = 0`.
- **Prevention:** Specificity Guardrails (Phase 2).

### h) Gate Bypass
- **Symptom:** Ideas are generated from clusters with size=3.
- **Detection:** `SELECT i.name, c.size FROM ideas i JOIN clusters c ON i.cluster_id = c.id WHERE c.size < 8;`
- **Root Cause:** The size/diversity gate was documented but never enforced with an `assert` or `if` block in code.
- **Fix:** Add a strict python check before handing off to the Architect.

### i) Extraction Skip
- **Symptom:** 776 raw items sit unprocessed.
- **Detection:** `SELECT count(*) FROM raw_items WHERE id NOT IN (SELECT raw_item_id FROM pain_points);`
- **Root Cause:** A hardcoded `limit=50` was left in `cmd_extract()`.
- **Fix:** Remove the limit, process in chunks using the Budget Manager.

### j) Coherence Too Lenient
- **Symptom:** Clusters span multiple un-related domains.
- **Root Cause:** "Cost and Complexity" was evaluated by the LLM as a valid coherent theme.
- **Fix:** Prompt engineering. Require the LLM to identify the specific proper noun or software stack unifying the cluster.

### k) Coherence Sample Undersized
- **Symptom:** An 18-item cluster is judged "coherent" based on evaluating only 8 samples. The 10 outliers were dragged along invisibly.
- **Fix:** Force the coherence check to sample 100% of the pains in the cluster if size < 30.

### l) Docx Export Theater
- **Symptom:** AG says "I generated the .docx files" but uses markdown with a `.docx` extension.
- **Fix:** Force the use of `python-docx` library (Phase 8).

---

## 4. Human Validation Workflow (The Real Bottleneck)

The pipeline does not build startups; it builds validation targets. Once the pipeline produces a candidate wedge, the human takes over:

1. **Verify Evidence:** Open the cluster in Datasette. Manually verify the top 5 WTP quotes by clicking their source URLs (15-min timebox).
2. **Draft Outreach:** Draft a cold-DM template using the *exact language and proper nouns* from the verbatim quotes.
3. **Execute:** Post 10-20 DMs to the original authors.
4. **Capture:** Spin up a single-page Tally.so waitlist.
5. **Success Criteria:** 20 signups OR 5 "yes I'd pay" replies within 7 days.
6. **Fail Criteria:** Silence or "we solved this internally." If failed, abandon the idea, return to the pipeline, and pick the next cluster.

---

## 5. Red-Flag Output Patterns

Halt and diagnose immediately if you see any of the following in the outputs:

- **Invented Names:** Any startup name ending in `-ly`, `-Sphere`, `-Saver`, `-Optimizer`.
- **Keyword Mashups:** Cluster labels like "Cloud API Database Cost Issues" (3+ nouns without verbs).
- **The "F" Word:** Any string containing `"Auto-Cluster"` or `"Fallback"`.
- **Monoculture ICP:** Ideas where every ICP is lazily labeled "DevOps Engineers".
- **Ghost WTP:** Rows where `wtp_type=unknown` but the `WTP score > 0`.
- **Empty Promises:** AG runtime reports that end with "successfully completed" but contain no terminal output or `Test-Path` results pasted as proof.

---

## 6. Recovery Procedures

- **DB Corrupt or Wiped:** 
  ```powershell
  Remove-Item D:\Start\project\data\intel.db
  Copy-Item D:\Start\project\data\intel.db.bak.YYYYMMDD -Destination D:\Start\project\data\intel.db
  ```
- **All Providers Rate-Limited:** 
  Wait 24 hours, or add fresh keys to `.env` and `project\.env`, then run `python main.py --resume`.
- **Coherence Gate Too Strict (0 pass):** 
  Relax the system prompt in `cluster.py`, execute `python main.py cluster --recluster`.
- **Coherence Gate Too Lenient (Garbage passes):** 
  Strengthen the system prompt with negative examples, execute `python main.py cluster --recluster`.
- **Local Gemma Runtime Crashes:** 
  Restart `llama-server`. Check for port 8080 conflicts. Verify the `.gguf` file integrity with `Get-FileHash`.

---

## 7. Change Management

When altering the architecture, follow these rules:

- **Adding a New Source (e.g., LinkedIn):** 
  Create `src/miners/linkedin_miner.py`. Tag DB entries with the source. Run deduplication verification. Add Geo-tagging. Update the Budget Manager accounting.
- **Adding a New Provider:** 
  Insert into the `key_manager.py` cascade sequentially based on cognitive load capability. Must wire into TPD/RPM tracking immediately.
- **Adding a New Agent:** 
  Define the contract sketch in doc 03. Assign it to a strict tier (Fast vs Deep) before writing the python class.

---

## 8. Weekly / Monthly Maintenance Checklist

- **Weekly:** 
  - Backup the DB. 
  - Run SQL to verify no orphan rows exist in `clusters` or `ideas`. 
  - Review the terminal failure log for rate-limit frequency.
- **Monthly:** 
  - Rotate or refresh free-tier provider keys. 
  - Review `01_VISION_AND_PRINCIPLES.md` to see if deferred out-of-scope items (e.g., global scraping) should move into scope. 
  - Prune stale vault notes.
- **Per-Run (Pre-flight):** 
  - Keys valid? Quotas fresh? DB backed up?

---

## 9. Escalation — When to Call the Founder

Minions must STOP and consult the founder (rather than proceeding autonomously) if:

- **Principle Violation:** Any output violates Principles 1-5 (e.g., generic slop generated).
- **Ban Risk:** IP blocked on Reddit, GitHub rate limits hard-locked, or WhatsApp locks out an outreach account.
- **Cost Incurred:** Any paid API tier is accidentally hit. (The system is zero-dollar bootstrapped).
- **Architectural Deviation:** Proposing a new pipeline stage, dropping a principle, or changing the database schema fundamentally.
- **UI Changes:** Modifying the format of the founder-facing Markdown/Docx briefs.

---

## 10. The Trust Contract with Antigravity

This is the explicit law governing the human-AG relationship going forward:

1. **AG's summaries are marketing copy, not data.** Minions and humans must verify every AG claim with SQL or the filesystem.
2. **Prove it.** AG must run its own verification commands (`Test-Path`, `pytest`, `python -c ...`) and paste the raw output into the chat before claiming a task is complete.
3. **One Thing At A Time.** If AG proposes a massive refactor plan bigger than the brief asked for, the human will reject it and force AG back to the atomic execution model.
4. **Zero Tolerance for Ghost Files.** If AG hallucinates a file, the entire step is treated as a failure and rolled back.
5. **The Law of Principles.** AG is strictly forbidden from authoring changes to the 5 core principles. Those are the founder's domain alone.
