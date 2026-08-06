# Market Intelligence Engine — Walkthrough

This file documents how to run the full pipeline from a blank database to a
ranked list of B2B SaaS opportunities. It is generated from actual command
outputs, not summarised from memory.

---

## Prerequisites

```
pip install -r requirements.txt    # bertopic, sklearn, pytrends, instructor, etc.
```

Environment: copy `.env.example` → `.env`, add keys for at least one of:
`GROQ_API_KEY`, `GEMINI_API_KEY`, `GITHUB_TOKEN`.

---

## Step 1 — Scan (mine raw items)

```
python main.py scan \
  --topic "Kubernetes CI/CD cost optimization" \
  --subreddits devops mlops \
  --repos prometheus/prometheus langfuse/langfuse \
  --shopify-apps recharge-subscriptions bold-subscriptions \
  --alternativeto recharge-payments zendesk \
  --limit 20
```

**Actual output (last run):**
```
[+] Scan Complete: Found 167 discussions, ~167 new items saved to SQLite database.
```

Sources in DB after last scan:
```
alternativeto:bold-commerce       1
alternativeto:gorgias             1
alternativeto:recharge-payments   1
alternativeto:zendesk             3
github:langfuse/langfuse          8
github:prometheus/prometheus      8
hackernews                        26
reddit:r/devops                   20
reddit:r/dropship                 8
reddit:r/ecommerce                8
reddit:r/shopify                  8
shopify:bold-subscriptions        8
shopify:klaviyo-email-marketing   7
shopify:recharge-subscriptions    5
stackoverflow                     52
youtube:transcript                3
```

---

## Step 2 — Extract (structured pain points)

```
python main.py extract --limit 100
```

Extracts `PainPoint` objects (Pydantic-validated) via `instructor` from each
raw item. Severity levels: `annoyance | blocker | financial_bleed`.

**Actual output (last run):**
```
79 pain points extracted from 167 raw items.
```

---

## Step 3 — Cluster

```
python main.py cluster
```

Routing logic (as of latest code):
- **BERTopic path** — uses `sklearn.cluster.HDBSCAN` (NOT the `hdbscan` package,
  which is blocked by Application Control on this machine). Fails loud on
  `ImportError`. `min_topic_size=5` enforced.
- **TF-IDF fallback** — triggered only when BERTopic fails at runtime. Sub-threshold
  clusters (< 5 pains) are merged into nearest semantic neighbour or dropped.

Expected log prefix:
```
[BERTopic] Clustering with BERTopic (sklearn HDBSCAN, min_topic_size=5)
```
OR
```
[TF-IDF] Clustering with TF-IDF fallback because <reason>
[cluster] TF-IDF: dropped N pains from sub-threshold clusters (no merge candidate)
```

---

## Step 4 — Rank

```
python main.py rank --min-size 5
```

Gates enforced:
1. `cluster.size >= 5 AND cluster.source_diversity >= 2` — skipped with log if not met.
2. WTP score is capped by evidence: `wtp_ev=0` → `score_wtp=0`; `wtp_ev<5` → `score_wtp=min(score,3)`.
3. Citation validation: all `cited_pain_ids` must exist in the cluster. Retry once, then mark `unscoreable`.

---

## Step 5 — View

```
python main.py top 5          # top 5 by score_total
python main.py view 1         # full dossier for rank #1
python main.py inspect        # Datasette UI on http://127.0.0.1:8001
```

---

## Acceptance Test #9

An idea passes if ALL of the following are true:
- `source_diversity >= 3`
- `wtp_evidence_count >= 5`
- `trend_verdict IN ('rising', 'flat')`
- All `cited_pain_ids` valid (no hallucinated IDs)

**Status as of this walkthrough:**

The current DB (79 pains from 16 sources) does **not** produce any idea that
passes all four criteria. The primary blocker is `wtp_evidence_count = 0` across
all clusters — zero extracted pain points contain explicit willingness-to-pay
language. The correct next step is to scan verticals where buyers explicitly
discuss budget and switching costs (e.g. G2 reviews, Capterra, LinkedIn
complaints about invoiced SaaS spend).

```
Run more scans with:
python main.py scan --topic "overpriced SaaS subscription billing" \
  --alternativeto datadog pagerduty \
  --shopify-apps bold-subscriptions recharge-subscriptions
```

---

## Audit

Every claim in the ranked output is traceable:

```sql
-- In Datasette (python main.py inspect) or direct SQLite:
SELECT i.name, i.score_total, p.summary, p.quote, r.url
FROM ideas i
JOIN clusters c ON i.cluster_id = c.id
JOIN pain_points p ON p.cluster_id = c.id
JOIN raw_items r ON p.raw_item_id = r.id
ORDER BY i.score_total DESC;
```
