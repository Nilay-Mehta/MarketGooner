# 03 — Target Architecture

This document defines the TARGET architecture for the Market Intelligence Engine. It is the North Star design, representing how the system behaves when fully realized. It is not a migration plan (see document 04 for execution sequencing).

Every structural decision here enforces the 5 core principles outlined in `01_VISION_AND_PRINCIPLES.md`.

---

## 1. Architecture Overview

**What it does:** The engine is an autonomous pipeline that translates a human-selected market wedge into highly specific, source-cited startup opportunities and marketing intelligence briefs by orchestrating a swarm of specialized LLM agents.

**Data Flow:** The human initiates the run via CLI. A fast-tier Master Agent dispatches mining tasks to Ingestors. The raw data streams into a SQLite database. Extractor agents filter and refine the data using strict specificity guardrails. The deep-tier Architect Agent synthesizes the verified rows into anomaly-focused startup dossiers, while the Copywriter Agent spins the same data into marketing briefs.

**Human Intervention:** 
1. **Start:** The human explicitly sets the target and approves the initial validation scan (Principle 1).
2. **Halt/Resume:** If rate limits hit, the human receives instructions to wait and resume, preventing silent failure (Principle 4).
3. **End:** The human reads the final Vault dossiers and initiates real-world validation.

```text
+-------------------+       +-----------------------+       +-------------------+
| Human (CLI)       | ----> | Master Agent (Fast)   | ----> | Scout Agent       |
| Picks Market      |       | Orchestrates Run      |       | Validates Trend   |
+-------------------+       +-----------------------+       +-------------------+
                                     |
                                     v
                            +-----------------------+
                            | Ingestor Agents       |  <--- YouTube, Reddit, HN,
                            | (Fast Tier)           |       StackOverflow, Shopify
                            +-----------------------+
                                     |
                                     v (SQLite raw_items)
                            +-----------------------+
                            | Extractor Agent       |  <--- Rejects generic buckets,
                            | (Fast/Heavy Tier)     |       preserves proper nouns
                            +-----------------------+
                                     |
                                     v (SQLite pain_points & clusters)
                            +-----------------------+
             +--------------| Architect Agent       |---------------+
             |              | (Deep Tier)           |               |
             |              +-----------------------+               |
             |                                                      |
    +-------------------+                                  +-------------------+
    | Startup Dossier   |                                  | Copywriter Agent  |
    | (Obsidian/Docx)   |                                  | (Deep Tier)       |
    +-------------------+                                  +-------------------+
                                                                    |
                                                           +-------------------+
                                                           | Marketing Brief   |
                                                           | (Obsidian/Docx)   |
                                                           +-------------------+
```

---

## 2. Agent Roster

The system uses a 6-agent swarm. All agents rely on a strictly defined cognitive-load tier (Principle 3) to balance reasoning capability against rate limits (Principle 4).

### a) Master Agent
- **Purpose:** Dispatches sub-tasks, plans the extraction routes, and orchestrates the flow.
- **Tier:** Fast
- **Models:** Groq Llama 3.3 70B → Cerebras → Gemini Flash
- **Input:** User's target market string (e.g., "freight brokers india").
- **Output:** Execution plan schema mapping specific sources (subreddits, YouTube query strings) to Ingestors.
- **Failure Mode:** If fast tier exhausts, halts run entirely; no sub-tasks are fired.
- **Usage:** ~1 call per run (low token usage).

### b) Scout Agent
- **Purpose:** Performs a lightweight validation check (Google Trends velocity, initial query hits) before heavy scraping begins. Enforces Principle 1.
- **Tier:** Fast
- **Models:** Groq Llama 3.3 70B → Gemini Flash
- **Input:** Master Agent's search vectors.
- **Output:** Go/No-Go validation schema (Trend trajectory, estimated volume).
- **Failure Mode:** Halts and prompts the user to either override or retry.
- **Usage:** ~1-3 calls per run.

### c) Ingestor Agent
- **Purpose:** Processes bulk unstructured inputs to locate keyword-dense zones (e.g., scanning a 2-hour YouTube transcript for the exact 2 minutes discussing "logistics delays").
- **Tier:** Fast (High throughput required)
- **Models:** Gemini Flash (Primary due to massive context window) → Groq Llama 3.3 70B (Fallback for shorter texts)
- **Input:** Raw text dumps (transcripts, 100+ comment Reddit threads).
- **Output:** Pydantic schema returning `[{"timestamp": "12:04", "chunk": "..."}]`.
- **Failure Mode:** Skips the specific source, marks it "Failed", and continues. Does NOT halt the run unless all ingestors fail.
- **Usage:** 50–200 calls per run.

### d) Extractor Agent
- **Purpose:** Classifies specific pain points and explicitly extracts WTP (Willingness to Pay) signals. Enforces Principle 2 (Preserve Specificity).
- **Tier:** Fast (Heavy reasoning variant)
- **Models:** Groq Llama 3.3 70B → Cerebras
- **Input:** Filtered dense chunks from Ingestor.
- **Output:** Pydantic schema: `class PainPoint(BaseModel): summary: str, proper_nouns_preserved: list[str], wtp_evidence: str, verbatim_quote: str`.
- **Failure Mode:** If rate limits hit, `budget_manager` halts the pipeline, persists state, and provides a resume command (Principle 4).
- **Usage:** 200–500 calls per run.

### e) Architect Agent
- **Purpose:** Synthesizes the extracted clusters into anomaly-first startup opportunities.
- **Tier:** Deep
- **Models:** Gemini 1.5 Pro → GPT-4o (via GitHub) → Claude 3.5 Sonnet (via OpenRouter)
- **Input:** Top 5 highly-coherent clusters with all associated pain points and citations.
- **Output:** Startup Wedge Dossier Schema.
- **Failure Mode:** Halts pipeline. Prompts user: "No deep-tier available. Resume tomorrow or provide a new key."
- **Usage:** 5–10 calls per run.

### f) Copywriter Agent
- **Purpose:** Repackages the Architect's data into a marketing intelligence brief (Principle 5).
- **Tier:** Deep
- **Models:** Gemini 1.5 Pro → GPT-4o (via GitHub) → Claude 3.5 Sonnet
- **Input:** The exact same cluster anomalies passed to the Architect.
- **Output:** Marketing Brief Schema (Trend angles, SEO gaps).
- **Failure Mode:** Output generation skips the marketing brief but successfully saves the startup dossier.
- **Usage:** 3–5 calls per run.

---

## 3. Local Model Runtime Evaluation

To handle the Master/Scout agents locally (and provide a zero-cost backup for the Fast tier) within a **5 GB RAM, CPU-only** Windows 11 constraint, we evaluated three open-source runtimes.

*GitHub stats as of Aug 2026.*

### a) llama.cpp
- **Repo:** `ggml-org/llama.cpp` (123,900 Stars, Updated Aug 14 2026)
- **Footprint:** Extremely minimal (zero external dependencies, pure C/C++).
- **API:** Full OpenAI-compatible server (`llama-server`).
- **Verdict for 5GB/CPU:** **RECOMMENDED.** It is the most robust, memory-efficient way to run a 3B parameter model (like Qwen 2.5 3B or Gemma) in ~2.5 GB of RAM without background daemon bloat.

### b) Ollama
- **Repo:** `ollama/ollama` (178,535 Stars, Updated Aug 14 2026)
- **Footprint:** Moderate (Runs a persistent Go daemon, relies on llama.cpp under the hood).
- **API:** Custom API + OpenAI-compatible wrapper.
- **Verdict for 5GB/CPU:** **REJECTED AS PRIMARY.** While user-friendly, the persistent daemon and slightly higher memory overhead make it risky when running near the absolute 5GB hardware ceiling. Recommended only if local model footprint drops below 1.5GB.

### c) Colibri
- **Repo:** `JustVugg/colibri` (24,674 Stars, Updated Aug 14 2026)
- **Footprint:** Specialized NVMe-streaming engine for massive MoE models.
- **Verdict for 5GB/CPU:** **DISQUALIFIED.** Colibri is built for 744B+ models. It requires a resident "dense backbone" of ~10 GB just to boot GLM-5.2. It fundamentally cannot run on a 5GB machine.

**Final Decision:** Adopt `llama.cpp` via `llama-server` for local fallback execution.

---

## 4. Model Tier Cascade (Principle 3 & 4)

The `KeyManager` operates two isolated cascades. It rotates sequentially through providers when Tokens-Per-Day (TPD) or Requests-Per-Minute (RPM) are exhausted.

### Fast Tier Cascade
1. **Groq (Llama 3.3 70B)**: Primary. Lightning fast. Free tier: 14,400 req/day. *Auth: Header `Authorization: Bearer <GROQ_API_KEY>`*.
2. **Cerebras**: Backup 1. 
3. **Gemini Flash**: Backup 2. Free tier: 1,500 req/day. *Auth: Query param `?key=<GEMINI_API_KEY>`*.
4. **Local Gemma 3n (llama.cpp)**: Final backup. Zero rate limits, bounded by local CPU. *Auth: Localhost endpoint.*

### Deep Tier Cascade
1. **Gemini 1.5 Pro**: Primary. Exceptional context reasoning. Free tier: 50 req/day. 
2. **GPT-4o (GitHub Models)**: Backup 1. *Auth: Header `Authorization: Bearer <GITHUB_TOKEN>`*.
3. **Claude 3.5 Sonnet (OpenRouter)**: Backup 2. *Auth: Header `Authorization: Bearer <OPENROUTER_API_KEY>`*.
4. **Fallback**: Halt. *Do not fall back to Fast Tier.* (Enforces Principle 3).

---

## 5. Storage Architecture

**Primary Store:** SQLite (`data/intel.db`).
**Semantic Search:** Adopt `sqlite-vec`. 
*Reasoning:* It provides fast, zero-dependency vector similarity search directly in SQL without the bloat of Chroma or LanceDB. Keeps the architecture completely local and file-based.
*Chroma/LanceDB Rejected:* We strictly defer adding secondary databases (per doc 01) to avoid memory overhead and deployment complexity.

**Schema Updates Needed:**
- `raw_items`: Add `geo TEXT` (to tag India vs US sources).
- `pain_points`: Add `preserved_nouns TEXT` (JSON list to enforce Principle 2).
- *Note:* `wtp_type` already exists but must be actively populated by the new extraction guardrails.

**Datasette:** Remains the primary audit UI. It natively supports SQLite and will allow the founder to verify the source of every Architect claim.

---

## 6. Budget Manager Design

The `budget_manager.py` (Principle 4) sits inside `KeyManager` and prevents silent failures.

- **Tracking:** Maintains an in-memory dictionary (synced to a local `metrics.json` file) tracking `tpd_used` and `rpm_used` per provider.
- **Halt Protocol:** When `budget_manager` detects that all providers in a tier are exhausted, it raises a `RateLimitHalt` exception.
- **State Persistence:** The orchestrator catches the exception, commits all current SQLite transactions, writes the remaining task queue to `data/verify_last.json`, and prints:
  `[HALT] Deep Tier exhausted. Run: python main.py --resume to continue when quotas reset.`
- **Anti-Pattern Enforcement:** The manager will explicitly raise an error rather than returning a default `{}` or "Auto-Cluster (Fallback)" label.

---

## 7. Data Flow — Full Run Example

**Input:** "AI agent cost governance for freight brokerage in India"

1. **Master & Scout:** Master receives the prompt. Scout queries Google Trends for "freight broker software India". Returns a "Rising" verdict. Human is prompted `Proceed? [Y/n]`. Human hits Y.
2. **Ingestors Fire:** Ingestors hit `r/FreightBrokers` (filtered for India context) and YouTube transcripts of Indian logistics podcasts. 150 items land in `raw_items`.
3. **Extraction:** The Extractor (Groq 70B) reads the chunks. Guardrails enforce that if someone mentions "Rivigo" or "BlackBuck", it is saved verbatim in the `pain_points` table along with any quoted ₹ amounts. 
4. **Clustering:** HDBSCAN groups the pain points. 
5. **Architect Synthesis:** The Architect (Gemini Pro) evaluates Cluster 1. Instead of labeling it "FreightCostSaver", it generates an Anomaly Digest: "3 independent brokerages cited losing ₹50,000/mo to manual toll reconciliation with BlackBuck."
6. **Copywriter Synthesis:** The Copywriter Agent takes the same cluster and writes a Trend Brief: "Why Toll Reconciliation is the Missing API in Indian Logistics."
7. **Output:** Both `.md` and `.docx` files land in `Market_Intelligence_Vault/`.

---

## 8. Dual Output Shape (Principle 5)

**Startup Dossier Example:**
> **Wedge Candidate: Automated Toll Reconciliation API**
> **The Anomaly:** 4 distinct posts this week mentioned manually reconciling FASTag data against GPS logs to prevent driver fraud. 
> **WTP Evidence:** A fleet owner in `r/Truckers` stated: *"I'm bleeding ₹50k a month on fake toll receipts, I'd pay 10% of that just to automate the audit."* [Source: Reddit](#)
> **Validation Experiment:** Cold DM the 4 authors offering a basic CSV-to-FASTag matching script.

**Marketing Brief Example:**
> **Trend Alert: Fleet Toll Fraud**
> **The Gap:** Fleet management content focuses on fuel efficiency, but the actual operator pain point right now is micro-fraud via FASTag.
> **Content Angle:** "How Indian Fleets are Losing 10% Margin to Toll Fraud (And How to Fix It)". Target keywords: `FASTag reconciliation software`, `fleet toll audit API`.

Both documents use Python-docx and standard markdown to cite directly back to the SQLite `raw_items` primary key URL.

---

## 9. Rejected Alternatives

- **Instagram Scraping:** Rejected per scope. High ban risk; poor signal-to-risk ratio.
- **Multi-language Day 1:** Deferred. English/Hinglish sources only to limit embedding model complexity.
- **Chroma/LanceDB:** Rejected. Unnecessary bloat; `sqlite-vec` handles the required scale locally.
- **Autonomous End-to-End:** Rejected (Principle 1). Human must approve the Scout's trend check.
- **Silent Fallbacks:** Rejected (Principle 4). `budget_manager` enforces a hard halt.

---

## 10. Open Architectural Questions

Before implementation begins, the founder must confirm:

1. **Local Runtime:** Do we officially adopt `llama.cpp` for the local fallback, given the 5GB RAM constraint?
2. **Local Model Selection:** For a 5GB ceiling, do we use Gemma 2 2B (Instruct) or Qwen 2.5 3B? (Qwen is slightly heavier but better at logic routing).
3. **WhatsApp Tooling:** Is the `whatsapp-web.js` outreach helper part of the v2.0 roadmap, or pushed to a post-v2.0 standalone repository to avoid polluting the core engine?
