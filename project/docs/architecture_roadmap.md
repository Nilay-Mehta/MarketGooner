# Market Intelligence Pipeline — Restructuring Plan

## 1. Objective

We are building a **fully autonomous Market Intelligence Pipeline** that:

1. Collects real-world market signals from the internet.
2. Extracts complaints, problems, needs, and behavioral signals.
3. Groups recurring problems into meaningful market themes.
4. Identifies potential market opportunities.
5. Evaluates opportunities using evidence rather than a single LLM opinion.
6. Generates startup/product concepts from qualified opportunities.
7. Produces product, sales, SEO, and marketing assets automatically.
8. Eventually supports real-world validation experiments.

### Important distinction

The system should **discover opportunities**, not falsely claim that an opportunity is already "validated."

Actual validation requires evidence such as:
- customer interviews
- landing-page tests
- waitlists
- outreach responses
- search demand
- willingness to pay
- competitor/customer behavior

So the terminology should be:
> **Market Intelligence → Opportunity Discovery → Validation → Diffusion**

---

# 2. Proposed High-Level Architecture

```text
                         INTERNET
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
        Reddit           YouTube         Google Trends
          │                 │                 │
          └────────────┬────┴─────────────────┘
                       │
                 INGESTION LAYER
                       │
                       ▼
              NORMALIZATION LAYER
                       │
             ┌─────────┴─────────┐
             │                   │
        Raw Evidence       Clean Evidence
             │                   │
             └─────────┬─────────┘
                       ▼
               EXTRACTION LAYER
                       │
             ┌─────────┴─────────┐
             │                   │
        Generative LLM         JEV
        understanding        decisions
             │                   │
             └─────────┬─────────┘
                       ▼
                 PAIN-POINT STORE
                       │
                       ▼
               ANALYSIS ENGINE
                       │
          ┌────────────┼────────────┐
          │            │            │
      Embeddings   Clustering    Signals
          │            │            │
          └────────────┼────────────┘
                       ▼
              OPPORTUNITY ENGINE
                       │
                       ▼
                JEV DECISION LAYER
                       │
             ┌─────────┴─────────┐
             │                   │
           Reject             Advance
                                 │
                                 ▼
                         DEEP REASONING
                              LLM
                                 │
                                 ▼
                       OPPORTUNITY DOSSIER
                                 │
                                 ▼
                         VALIDATION LAYER
                                 │
                                 ▼
                       VALIDATED SIGNALS
                                 │
                                 ▼
                         DIFFUSION LAYER
                    ┌────────────┼────────────┐
                    │            │            │
                 Product      Marketing      SEO
                 Dossier       Assets       Assets
```

---

# 3. The Most Important Architectural Change

The current system thinks primarily in terms of:
```text
Fast Model
     ↓
Deep Model
```

We should change this. The system should distinguish between **three types of intelligence**:

```text
┌─────────────────────────────────────────┐
│            INTELLIGENCE TYPES            │
├─────────────────────────────────────────┤
│                                         │
│  1. DETERMINISTIC COMPUTATION           │
│     Code / algorithms                   │
│                                         │
│  2. GENERATIVE INTELLIGENCE             │
│     LLMs                                │
│                                         │
│  3. DECISION INTELLIGENCE               │
│     JEV / decision models               │
│                                         │
└─────────────────────────────────────────┘
```

---

# 4. Deterministic Computation

Do **not** use an LLM for things that normal software can do reliably.

Examples:
- URL normalization
- Hashing
- Deduplication
- Text cleaning
- Language detection
- Timestamp processing
- Frequency counting
- Metadata extraction
- Database operations
- Embedding generation
- Vector similarity
- Clustering
- Trend calculations
- Statistical analysis
- Data aggregation

This makes the system cheaper, faster, more reproducible, and easier to debug.

---

# 5. Generative Intelligence

Use normal LLMs when the system actually needs to understand or generate language.

Examples:
- "What is this person complaining about?"
- "Summarize this discussion."
- "What underlying problem is being described?"
- "Extract the user's desired outcome."
- "Explain why this problem exists."
- "Generate a startup concept."
- "Generate a product description."
- "Write a landing page."
- "Generate marketing copy."

This is where the existing **Fast Tier / Deep Tier** concept remains useful. However, we should eventually rename/restructure it around **task complexity**, rather than assuming "fast = everything simple."

---

# 6. Decision Intelligence — JEV

JEV should become a **Decision Engine**, not simply another model in the Fast Tier.

Conceptually:
```text
                    DECISION ENGINE
                          │
                         JEV
                          │
          ┌───────────────┼────────────────┐
          │               │                │
      Extraction       Analysis        Validation
          │               │                │
       Decisions       Decisions        Decisions
```

JEV is particularly useful when we need narrow structured decisions.
For example:
- `Is this actually a complaint?` → YES / NO
- `Which category does this belong to?` → A / B / C / D
- `How severe is the problem?` → 0 → 1
- `Should this candidate continue through the pipeline?` → YES / NO

The key point is:
> **LLMs generate/understand language. JEV makes narrow structured decisions.**

---

# 7. JEV Should Be Used as a Pluggable Component

We should **not hard-code the entire system around JEV**.

Architecture:
```text
                 DECISION INTERFACE
                         │
          ┌──────────────┼──────────────┐
          │              │              │
         JEV        Local Model       LLM
          │              │              │
          └──────────────┼──────────────┘
                         │
                  Decision Result
```

This allows us to change the underlying provider later. The rest of the pipeline shouldn't care whether the decision came from JEV, Local model, Gemini, Groq, or GitHub model. 
This is especially important because our original goal is **minimal/zero API cost**.

---

# 8. Model Router — New Structure

Instead of:
```text
Task → Fast Model OR Deep Model
```
we should move toward:
```text
                       MODEL ROUTER
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
         DECISION       EXTRACTION      GENERATION
          MODELS          MODELS          MODELS
             │              │              │
            JEV         Small LLM       Large LLM
```

The router decides based on: task type, output type, complexity, required confidence, cost, latency, availability, rate limits, and context size.

---

# 9. Ingestion Layer

The ingestion layer is responsible only for **collecting evidence**.

**Reddit / YouTube** primarily provide **Human evidence**:
- complaints, discussions, frustrations, requests, workarounds, product failures

**Google Trends** primarily provides **Market/demand signals**:
- search growth, declining interest, seasonal demand, geographic demand

Google Trends should therefore **not simply be another complaint miner**.

---

# 10. Future Data Sources

We should eventually support additional sources such as: Google Search, GitHub, Product Hunt, App stores, Amazon reviews, G2, Forums, News, etc.

But:
> **Do not build all of these now.**
The first objective is to build one complete vertical pipeline.

---

# 11. Normalization Layer

Every source produces different formats. We need a common internal representation.

Conceptually:
```text
Evidence
├── source
├── source_id
├── URL
├── timestamp
├── author/channel
├── text
├── metadata
└── source-specific fields
```

---

# 12. Extraction Layer

Raw evidence should become structured observations. The extraction system should produce **structured JSON**, which our existing extraction infrastructure already supports.

---

# 13. Extraction Should Not Immediately Become "Startup Ideas"

We should not do: `Reddit post → LLM → "Here's a startup!"`
Instead: `Evidence → Observation → Pain Point → Cluster → Market Signal → Opportunity → Startup Concept`

---

# 14. Pain-Point Store

All extracted pain points should be stored independently with the original evidence attached. This gives us **Traceability**.

---

# 15. Deduplication

Before clustering, we should perform:
`Exact deduplication → Near-duplicate detection → Semantic similarity → Clustering`

---

# 16. Clustering Engine

The clustering engine should answer: "Which extracted problems appear to represent the same underlying problem?"
Pipeline: `Pain Points → Embeddings → Similarity → Clustering → Problem Clusters`

---

# 17. Problem Cluster

Each cluster should contain evidence to give us a mathematical representation of recurring problems.

---

# 18. Market Gap ≠ Cluster

A cluster only tells us: "Many people appear to experience this problem."
It does **not** automatically mean: "Build a company."

---

# 19. Opportunity Engine

The Opportunity Engine combines multiple signals: Frequency, Growth, Severity, Competition, Workarounds, Buyer signal → OPPORTUNITY CANDIDATE.

---

# 20. JEV's Role in Opportunity Analysis

Instead of asking one LLM "Is this a good startup?", break the decision into smaller questions (e.g., Is this a recurring problem? Is the pain commercially relevant?). Each decision produces structured outputs/probabilities.

---

# 21. Deep Reasoning Layer

Only candidates that survive earlier stages should reach expensive reasoning.
Example: `100,000 observations → 2,000 pain points → 100 candidates → JEV filtering → 10 serious opportunities → Deep LLM analysis`

---

# 22. Deep Opportunity Analysis

Output: **Opportunity Dossier** (Problem definition, Target customer, Existing alternatives, Business model, Pricing hypotheses, Distribution, Technical feasibility, Potential MVP).

---

# 23. Validation Layer

A future stage separate from opportunity discovery. Tests demand (Landing page, Waitlist, Cold outreach).

---

# 24. Diffusion Layer

Takes a qualified opportunity and turns it into usable assets.
Outputs:
- **Product Dossier** (MVP specification, Features)
- **Marketing Assets** (Landing page, Ad copy, Sales messaging)
- **SEO Assets** (Keywords, Content clusters)

---

# 25. Existing Smart API Router & 26. Budget Manager

**KEEP.** Responsibility should become **MODEL ORCHESTRATION**.
It should handle provider quotas, rate limits, token budgets, retry delays, fallbacks, provider availability, per-task budgets, and daily budgets to ensure minimal/zero API cost.

---

# 27. Existing Tiered Extraction Engine

**KEEP, BUT REFACTOR.** Make the distinction: `Extraction ≠ Decision ≠ Reasoning ≠ Generation`.

---

# 28. What We Should NOT Do

❌ Build Reddit + YouTube + Trends simultaneously
❌ Generate startup ideas directly from raw posts
❌ Send every observation to an expensive LLM
❌ Use LLMs for deterministic calculations
❌ Treat clustering as market validation
❌ Hard-code JEV into the entire system
❌ Make one giant "market opportunity score"
❌ Build the marketing generator before the opportunity engine works

---

# 29. What We SHOULD Do

Build a **vertical slice** first (e.g., Reddit → Raw Data → Normalization → Extraction → JEV Checks → Pain Points → Embeddings → Clustering → Opportunity Analysis → JEV → Deep Analysis → Opportunity Dossier).

If this works, Reddit becomes one plug-in.

---

# 30. Proposed Repository Structure (Target)

```text
market-intelligence/
├── ingestion/
├── normalization/
├── intelligence/ (extraction, decisions, embeddings, generation)
├── analysis/ (clustering, signals, opportunities)
├── validation/
├── diffusion/
├── orchestration/ (router, budget, retries)
└── storage/
```

---

# 31. Core Data Flow (Mental Model)

```text
SOURCE → EVIDENCE → OBSERVATION → PAIN POINT → PROBLEM CLUSTER → MARKET SIGNAL → OPPORTUNITY CANDIDATE → DECISION FILTER → DEEP OPPORTUNITY ANALYSIS → VALIDATION EXPERIMENT → VALIDATED EVIDENCE → PRODUCT / BUSINESS CONCEPT → DIFFUSION
```

---

# 32. Cost Strategy

**Cheap computation first → cheap intelligence → decision models → expensive reasoning → generation.**

---

# 33. Development Roadmap

## Phase 0 — Architecture Audit
Inspect the existing repository and classify every component. Do not build anything new until we understand what already exists.

## Phase 1 — Canonical Schemas
Define Evidence, Observation, PainPoint, Cluster, MarketSignal, Opportunity, ValidationResult, Asset.

## Phase 2 — Intelligence Architecture
Refactor API Router, Budget Manager, Fast Tier, Deep Tier into Model Router. Add JEV behind a provider interface.

## Phase 3 — First Ingestion Miner
Build **one** source first (Recommended: Reddit).

## Phase 4 — Analysis Engine
Add Deduplication → Embeddings → Clustering → Problem Landscape.

## Phase 5 — Opportunity Engine
Add Clusters → Market Signals → JEV Decisions → Opportunity Candidates.

## Phase 6 — Deep Analysis
Introduce Deep LLM → Opportunity Dossier.

## Phase 7 — Second/Third Sources
YouTube, Google Trends.

## Phase 8 — Validation
Build mechanisms to test Demand, Interest, etc.

## Phase 9 — Diffusion
Opportunity → Product Dossier → Marketing → SEO → Sales → Social.
