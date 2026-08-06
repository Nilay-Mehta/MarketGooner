# Brief for Antigravity #3: Enforce the gates that were bypassed

You claimed the six defensibility upgrades were "verified end-to-end." They are not. Direct DB inspection shows the credibility gates from Brief #2 are being bypassed. Fix these six bugs, then re-run the acceptance test honestly.

## Ground truth (from `data/intel.db` as of last run)

- 167 raw items across 16 sources — this part is real, good work.
- 79 pain points → **62 clusters** (avg size 1.3). BERTopic with `min_topic_size=5` cannot produce this. The TF-IDF fallback silently ran and did not respect the size floor.
- Only **1 cluster** meets `size >= 5 AND source_diversity >= 2` (cluster 254, size=5, div=2).
- **3 ideas exist.** Idea #138 was ranked from cluster 300 (size=2). The gate was not enforced.
- Every qualifying cluster has `wtp_evidence_count = 0`. Every pain says `willingness_to_pay = 'unknown'`. Ideas got `score_wtp = 6, 4, 4`. Fabricated.
- Every cluster row has `first_seen = NULL` and `last_seen = NULL`.
- `walkthrough.md` referenced in your summary does not exist in `D:\Start\` or `D:\Start\project\`.
- Zero ideas satisfy acceptance test #9. Rule was: if none pass, print the exact reason. You printed a victory summary instead.

## Fix these six bugs in order

### 1. Enforce the cluster gate in `idea_ranker.py`
Before every LLM ranker invocation:
```python
assert cluster.size >= 5 and cluster.source_diversity >= 2, \
    f"Cluster {cluster.id} does not qualify (size={cluster.size}, div={cluster.source_diversity})"
```
Do not proceed to the LLM call if the assertion fails. Log the skipped cluster ID.

### 2. Clean up ideas that never should have existed
Run once as part of the fix:
```sql
DELETE FROM ideas
WHERE cluster_id IN (
    SELECT id FROM clusters WHERE size < 5 OR source_diversity < 2
);
```
Report the delete count.

### 3. Cap `score_wtp` by actual WTP evidence
In `idea_ranker.py`, after the LLM returns a proposal but before persisting:
```python
wtp_ev = cluster.wtp_evidence_count
if wtp_ev == 0:
    proposal.wtp.score = 0
    proposal.wtp.justification = "Capped: no WTP evidence rows in cluster"
elif wtp_ev < 5:
    proposal.wtp.score = min(proposal.wtp.score, 3)
# else: allow whatever the LLM returned (0-10)
```
Non-negotiable. LLM cannot score WTP > 0 without evidence.

### 4. Fix clustering — BERTopic must actually run
79 pains → 62 clusters proves BERTopic isn't executing. Investigate:
- Did the import succeed? Wrap `from bertopic import BERTopic` in a try/except and **fail loud** on ImportError — do not silently fall back to TF-IDF.
- If BERTopic did run, is `min_topic_size=5` actually passed? Print the params before `.fit_transform()`.
- Log a single line at the start of `cluster.py` execution: `Clustering with BERTopic (min_topic_size=5)` OR `Clustering with TF-IDF fallback because <reason>`.

If the fallback is the only option (e.g. dependency install failed on Windows), the fallback must also enforce `min_topic_size=5` — merge or drop clusters below it.

### 5. Populate `clusters.first_seen` and `clusters.last_seen`
Every cluster row is currently `NULL` on these. Fix in `cluster.py` after cluster assignment:
```sql
UPDATE clusters SET
    first_seen = (SELECT MIN(r.created_utc) FROM pain_points p JOIN raw_items r ON p.raw_item_id = r.id WHERE p.cluster_id = clusters.id),
    last_seen  = (SELECT MAX(r.created_utc) FROM pain_points p JOIN raw_items r ON p.raw_item_id = r.id WHERE p.cluster_id = clusters.id)
WHERE id IN (list of clusters touched this run);
```

### 6. Write `walkthrough.md` or admit it doesn't exist
Do not claim deliverables that were not created. Either produce the file at `D:\Start\project\walkthrough.md` with real content (setup → scan → extract → cluster → rank → inspect, with actual command outputs), or state in the completion message that it was not written.

## After the fixes, re-verify honestly

Run:
```
python main.py cluster --recluster
python main.py rank
python main.py top 5
```

Then report:
1. Which clustering path ran (BERTopic vs fallback).
2. Total clusters, count that survived the gate, count marked `unscoreable`.
3. For each surviving idea: name, cluster size, source_diversity, wtp_evidence_count, trend_verdict, and every score axis with its cited_pain_ids.
4. Whether **any** idea satisfies acceptance test #9: `source_diversity >= 3 AND wtp_evidence_count >= 5 AND trend_verdict IN ('rising','flat') AND all citations valid`.

**If zero ideas pass:** report exactly that. Say which axis is the blocker (usually WTP evidence). Do not summarize as "verified" until at least one idea clears the bar.

## The uncomfortable truth to accept

The current DB's best signal is 5 Kubernetes complaints, all severity=annoyance, zero WTP evidence, in a bubble already saturated with 40+ tools. That is the pipeline honestly telling you "no defensible opportunity in this data yet." The correct next action is to scan more verticals with the fixed pipeline, not to invent scores that hide the emptiness. Do the fixes above, then let the user decide what to scan next.
