# 01 — Vision & Principles

**Read this first. Do not read the other 4 documents until you have finished this one.**

This document defines what the project exists to do, the non-negotiable principles every implementation decision must respect, and the concrete criteria by which the project is judged successful. It does not contain code, architecture diagrams, or tool choices — those live in documents 02–05.

---

## 1. What this project is

A **Market Intelligence Engine** that helps a founder discover specific, non-generic, defensible business opportunities by mining public discussions across the internet (Reddit, Hacker News, StackOverflow, GitHub, Shopify App Store, AlternativeTo, YouTube transcripts, LinkedIn public posts, TikTok comments, Google Trends).

The end output is not "startup ideas." The end output is **verified anomalies with citations** — specific incidents, specific dollar amounts, specific incumbents named by real people — that a human founder can act on in a validation phase (cold DMs, waitlist landing pages, 15-min customer interviews).

A secondary output shape is a **marketing intelligence brief** — the same underlying data reshaped for marketers/agencies who want trend briefs, content-gap opportunities, and underserved keyword clusters.

Both outputs share the same pipeline. Only the final synthesis stage differs.

---

## 2. Why this project exists

Founders who want to build a bootstrapped business face a specific failure mode: they either (a) build a "vitamin" (a nice-to-have that customers won't pay for), or (b) build a "painkiller" in a space so crowded it doesn't matter that they built it. The way out is to find pain that is **specific, recurring, expensive, and underserved**.

Historically this has been done by hand — reading forums for hours, following creators, working in an industry for a decade. That approach works but scales poorly and depends on the founder already being embedded in a vertical.

This project is an attempt to compress that search using LLMs and structured pipelines. It does not replace human judgment. It **feeds** human judgment with real quotes, real URLs, and real incidents that the founder would not have found by browsing.

**The vision is not "AI decides what to build." The vision is "AI surfaces sharp facts, human decides."**

---

## 3. Who the user is

A single-founder or very small team, technical enough to run a Python CLI and read SQL, non-technical enough to want the tool to do the boring work. Bootstrapping without funding. Time is their primary capital. They have no venture money to burn on paid APIs or SaaS subscriptions.

They may work in a home country (India assumed as the primary "home" geo, given the founder's context and access to Indian communities) but want the tool to also surface opportunities in the US English-speaking market (largest B2B SaaS market, cleanest dollar signals).

They will hand this tool off to a small team ("minions") to maintain and extend. Those maintainers must be able to onboard from these five documents alone, without needing to interview the original founder.

---

## 4. The five non-negotiable principles

Every implementation decision must respect these five principles. If a proposed change violates a principle, reject the change or rewrite it. These principles were derived from watching earlier versions of this pipeline fail in specific ways — the rationale after each principle is not decoration, it is an incident report.

### Principle 1 — Human in the loop at market selection

**The system does not decide what market to explore.** The human picks a market or vertical. The system amplifies human curiosity, it does not replace it.

Every scan starts with a human-provided target (e.g., "freight brokerage in India", "dental clinics in Tier 2 US cities", "Shopify subscription apps"). Before mining begins, the system runs a lightweight validation check (Google Trends velocity, subreddit activity, YouTube video count) and shows the human a go/no-go summary. The human confirms before any expensive scraping starts.

**Why this principle exists:** earlier versions of the pipeline ran fully autonomous batch scans. The output was consistently generic ("Kubernetes cost tool", "SaaS billing optimizer", "cold email SaaS") because autonomous mining across public forums converges on the most-complained-about categories, which are also the most-competed-in categories. A human who has been thinking about a specific vertical for a week produces a 10x better starting point than any LLM's prompt-decomposition.

### Principle 2 — Preserve specificity

**Proper nouns, exact quotes, specific dollar amounts, and specific incidents flow through every stage of the pipeline unchanged.** LLM stages must reference them; they must not abstract them into categories.

Concrete example: if a Reddit user posts *"This company Lanesurf gave $15,000 to an AI agent and lost it all"*, the pipeline must preserve `Lanesurf`, `$15,000`, and the verbatim quote through extraction, clustering, and final output. It is a violation of this principle for the output to say *"a specific AI vendor lost significant money to an agent"* — that is an abstraction into a generic bucket.

Enforcement: the extractor must reject a pain-point classification if it fails to preserve at least one proper noun or specific number from the source. The synthesizer must include verbatim citation strings in every claim. If the citation cannot be traced to a source URL, the claim is rejected.

**Why this principle exists:** earlier versions of the pipeline let the LLM synthesizer paraphrase pain points into categories like "AI agent cost governance" and then invent product names like "AgentSphere" or "CloudCostSaver". The output was indistinguishable from any Y Combinator submission form. The Lanesurf $15k incident — the actual signal a human could act on — was smoothed into a category name and lost. Every LLM stage that summarizes is a specificity-destroying operation. This principle exists to make the pipeline fight that entropy.

### Principle 3 — Model tier by cognitive load

**Fast models classify. Deep models synthesize. Never invert.**

The pipeline uses at least two tiers of LLM:

- **Fast tier** (Groq Llama 3.3 70B, Cerebras, Gemini Flash, or local Gemma 3n on Ollama/llama.cpp/Colibri): handles high-volume, low-reasoning tasks — pain classification per item, batch extraction, relevance filtering, coherence checks. Called thousands of times per run. Cost per call must be near-zero.

- **Deep tier** (Gemini 1.5 Pro via free tier, GPT-4o via GitHub Models, Claude 3.5 Sonnet via OpenRouter): handles low-volume, high-reasoning tasks — cluster synthesis, anomaly identification, final brief writing. Called perhaps 5–20 times per run. Cost per call is allowed to be higher because volume is bounded.

Every LLM call must declare its tier explicitly. The provider cascade for each tier is independent.

**Why this principle exists:** earlier versions of the pipeline ran the synthesis stage on Groq Llama 3.3 70B because it was cheap and fast. Groq Llama 3.3 is a strong extractor but a weak strategist — it consistently produced generic startup-idea names when asked to synthesize. Meanwhile, GPT-4o via GitHub Models sat unused because nothing routed to it. Model choice was the primary cause of generic output, not prompt engineering or clustering.

### Principle 4 — Rate-limit-aware degrade

**When a provider caps out, the pipeline pauses the affected stage, writes state to disk, and prints resume instructions to the human. It does not silently fall back to a lower-tier label, an empty output, or a fabricated success message.**

Every LLM call goes through a `budget_manager` that tracks tokens-per-day and requests-per-minute per provider. When a provider caps, the manager attempts the declared cascade for that tier. If every provider in the cascade is capped, the affected stage halts, the pipeline persists all work-in-progress state, and the human sees a clear message like:

> `Rank stage halted: Gemini Pro TPD exhausted, GPT-4o RPM exhausted, OpenRouter TPD exhausted. 8 clusters unranked. Resume at 06:00 UTC or add a new key to <env var>.`

Silent failures are prohibited. A run that partially completed must be re-runnable to resume, not restarted from scratch.

**Why this principle exists:** earlier versions of the pipeline hit rate limits and silently labeled 27 of 31 clusters as "Auto-Cluster (Fallback)" with status `unscoreable`, then reported "pipeline completed in 27 minutes" (actual wall clock was 5+ hours). Multiple hours of the founder's time were wasted before manual DB inspection revealed the truth. Silent failures are the single most expensive failure mode a founder can suffer.

### Principle 5 — Dual output shape

**The pipeline produces two output shapes from the same underlying data: a startup opportunity dossier and a marketing intelligence brief.**

- **Startup dossier**: for the founder deciding whether to build a product. Contains 3–5 candidate wedges, each with source-cited pain quotes, WTP evidence, competitor mentions, and a proposed validation experiment.

- **Marketing brief**: for content marketers or agencies deciding what to write about. Contains 3–5 trend briefs, gap digests, and content angles. Also source-cited.

Both are rendered in Markdown for Obsidian and `.docx` for sharing. Both link back to the underlying SQLite rows for auditing.

**Why this principle exists:** the founder identified midway through development that the same data could serve a second audience (marketing agencies) with a small change to the final synthesis prompt. Building this in from the start avoids a v3 rewrite later. Also: forcing the pipeline to produce two distinct shapes from the same data is a sanity check on the underlying data quality — if the data cannot support both a startup dossier and a marketing brief, the data is too thin.

---

## 5. Success criteria

The project is judged successful if, and only if, all of these are true after a full pipeline run:

1. **At least one candidate wedge in the final startup dossier is defensible.** "Defensible" means: (a) 5+ WTP evidence rows from 3+ distinct source platforms, (b) at least one preserved proper noun (company, product, or specific incident) that a human could Google-verify in under 60 seconds, (c) Google Trends verdict is `rising` or `flat` (never `declining`).

2. **The founder, reading the dossier for the first time, can name three humans to DM within an hour.** If the dossier doesn't lead to concrete outreach, it has failed regardless of how "well-written" it is.

3. **Every claim in both outputs traces to a source URL.** No orphan claims. No summary-of-summaries. Datasette (or an equivalent audit UI) must be able to resolve every claim back to a raw source row.

4. **A full pipeline run completes in under 60 minutes on free-tier API quotas** OR halts honestly with a resume path (per Principle 4). Runs that take longer than 60 minutes without a halt-and-resume mechanism are a failure of Principle 4, not a "slow but ok" outcome.

5. **The founder can hand the project to a new engineer, and that engineer can produce a valid run within one working day** using only these five documents.

If any of these fail, the pipeline is not "mostly done" — it is broken. Fix before shipping the next feature.

---

## 6. Failure signals (things that mean the pipeline is wrong, even if it "runs")

The pipeline may report "success" while producing garbage. Watch for these signals:

- **Output contains invented product names** (`AgentSphere`, `CloudCostSaver`, `BarOps`). This is the LLM regressing to Y Combinator submission language. Principle 2 violation.
- **Cluster labels are keyword mashups** ("Sas Difficulty Business Not Issues", "Auto-Cluster (Fallback)"). Clustering degraded or coherence check bypassed. Principle 2 and 4 violation.
- **Every idea's ICP is "DevOps Engineers"** (or any other single homogeneous audience). Source bias — the miners are collapsing to a single community's noise. Diversify sources or reject the run.
- **WTP evidence count is > 0 but no `wtp_type` values other than `unknown`**. The extractor is filling in nonsense. Principle 2 violation.
- **Runtime is far under expected** with a suspiciously clean "0 items failed" report. Silent skip. Principle 4 violation.
- **File deliverables (`verification_report.md`, `walkthrough.md`, etc.) are claimed by the tool but do not exist on disk.** LLM hallucination in the reporting layer. Verify with `os.path.exists`, always.
- **The founder reads the dossier and their first thought is "everyone already knows this."** Principle 2 has failed upstream — specificity was destroyed.

Any of these signals should immediately halt the "declare victory" step and trigger diagnosis, not incremental fixing.

---

## 7. Scope: in and out

### In scope

- English-language sources across public web platforms (Reddit, HN, StackOverflow, GitHub, Shopify App Store, AlternativeTo, YouTube transcripts, LinkedIn public posts, TikTok comments)
- Google Trends velocity + related-queries as a trend signal
- **Two geographic focuses:** India (r/india, r/IndianEntrepreneur, IndiaMART product-review pages, JustDial category listings, Hindi-titled YouTube business channels) and US English (existing sources). Every raw item is tagged with a `geo` field.
- Local model inference for master-agent dispatch (via Ollama, llama.cpp, or Colibri — evaluated in document 03)
- API-based inference for extraction and synthesis (Groq, Cerebras, Gemini Free, GitHub Models, OpenRouter)
- SQLite as the primary store, with optional `sqlite-vec` extension for semantic search
- Datasette as the audit UI
- Obsidian vault for human-readable output and note-taking
- Word `.docx` export for sharing
- WhatsApp cold-outreach helper (unofficial `whatsapp-web.js` or `Baileys`) as a downstream tool for the validation phase — **acknowledged as ban-risky and used only for founder's own outreach, not automated at scale**

### Out of scope (do not build)

- Instagram scraping — Meta's anti-scraping is aggressive, account bans are near-certain, signal-to-risk is unfavorable
- Chinese platforms (WeChat, Xiaohongshu) — closed to external access
- Japanese/Korean platforms — require language handling not in current scope
- Middle Eastern platforms — Arabic RTL text and different platform mix
- Paid data providers (Crunchbase Enterprise, PitchBook, DataForSEO paid) — violates zero-cost constraint
- Any tool requiring a credit card for setup — even "free tier" APIs that require card details are excluded because the founder's stated constraint is zero-money
- Autonomous end-to-end runs without a human confirmation step (violates Principle 1)
- Product launch, billing, CRM integration — this project ends when the founder has a validated wedge; downstream tooling is a separate project

### Deferred (not in scope now, revisit after v1 works)

- Multi-language extraction (Hindi, Tamil, Portuguese, Spanish, etc.) — requires per-language embedding models and cultural pain-signal calibration
- UK / AU / EU sources — add after India + US pipelines produce a validated wedge
- SEA (Indonesia, Vietnam, Philippines) — add after India works
- Vector-based semantic search UI beyond Datasette
- Fine-tuning of extraction models on labeled pain-point data

---

## 8. Constraints the design must respect

- **Zero money.** No paid APIs, no paid SaaS, no credit-card-required signups. Every provider must have a free tier accessible without a card, or must run locally.
- **5 GB RAM, CPU-only, on the founder's dev machine.** Any local model must fit this. GPU is not assumed.
- **Windows 11 primary dev environment.** Bash tooling works via Git Bash / WSL, PowerShell also works. Do not assume Linux-only tools.
- **Free-tier rate limits are the actual bottleneck, not compute or code speed.** Design for graceful degrade under rate limits, not for raw throughput.
- **Founder is time-constrained.** They cannot babysit a 5-hour run. Runs must be either short (<60 min) or interruptible+resumable (per Principle 4).

---

## 9. What "done" looks like for this handoff

The minions have delivered the project successfully when:

- All 5 handoff documents (01–05) are read, understood, and referenced during implementation
- The pipeline satisfies all 5 success criteria (§5) on a real run
- The founder can trigger a scan on a new market and receive a valid dossier + marketing brief in under 60 minutes
- The codebase has no violations of the 5 principles (§4)
- A new engineer joining the team can onboard from these documents in one working day
- The `data/intel.db` state is preserved and honored — no destructive resets that lose the ~1,146 pain points already extracted

---

## 10. What to read next

Once you have read this document in full and can answer the following questions from memory, proceed to `02_CURRENT_STATE_AUDIT.md`:

1. Name the 5 principles and give the specific past-failure reason each one exists.
2. What are the two output shapes and who is each for?
3. What are the two geographic focuses and why not "global from day one"?
4. What are the 5 success criteria?
5. What is the constraint on paid APIs and why?

If you cannot answer these, re-read this document. Do not proceed to the other four until you can.

The other four documents in order:
- `02_CURRENT_STATE_AUDIT.md` — what exists in `D:\Start\` today, what works, what to keep vs delete
- `03_TARGET_ARCHITECTURE.md` — multi-agent design, model tiering, runtime evaluation (Colibri vs llama.cpp vs Ollama)
- `04_IMPLEMENTATION_ROADMAP.md` — phased execution, one-thing-at-a-time briefs to hand to Antigravity
- `05_OPERATIONS_AND_ANTIPATTERNS.md` — how to run, how to verify, and every failure mode already encountered so you do not repeat them

Do not skip ahead. The documents are ordered dependency-first.
