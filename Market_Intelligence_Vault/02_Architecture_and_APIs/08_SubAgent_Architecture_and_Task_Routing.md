# Multi-Sub-Agent Architecture & Power-Based Task Routing

This document defines a modular **Sub-Agent Orchestration System** for the Market Intelligence Engine. Instead of forcing one model to do everything, each sub-agent is mapped to a dedicated API provider and model selected specifically for the required **Speed**, **Context Window**, or **Reasoning Power**.

```
                           +-------------------------------------+
                           |      Master Dispatcher / User       |
                           +-------------------------------------+
                                              |
     +-------------------+--------------------+--------------------+-------------------+
     |                   |                    |                    |                   |
     v                   v                    v                    v                   v
+------------+     +------------+      +-------------+      +-------------+     +-------------+
| Agent A:   |     | Agent B:   |      | Agent C:    |      | Agent D:    |     | Agent E:    |
| THE SCOUT  |     | INGESTOR   |      | EXTRACTOR   |      | ARCHITECT   |     | COPYWRITER  |
| (Search)   |     | (Scraping) |      | (Filter)    |      | (Synthesis) |     | (Landing)   |
+------------+     +------------+      +-------------+      +-------------+     +-------------+
| Groq 8B    |     | Gemini     |      | Groq /      |      | GitHub      |     | Gemini      |
| ~800 t/s   |     | Flash      |      | Cerebras    |      | GPT-4o /    |     | 1.5 Pro     |
| Cheap/Fast |     | 1M Context |      | 70B Fast    |      | Claude 3.5  |     | High EQ     |
+------------+     +------------+      +-------------+      +-------------+     +-------------+
```

---

## 1. Sub-Agent Breakdown & Provider Allocation

### Sub-Agent A: "The Scout" (Macro Scanner & Trend Identifier)
* **Objective:** Discover emerging sub-niches, check search queries, and scan trending topics.
* **Power Needed:** Low reasoning, high speed, structured JSON output.
* **Allocated Provider & Model:** **Groq (`llama-3.1-8b-instant`)** or **Cerebras (`llama3.1-8b`)**.
* **Key Configuration:** `GROQ_KEY_POOL`.
* **Why:** Delivers results in < 300ms, consumes virtually zero quota (14,400 calls/day free).

### Sub-Agent B: "The Ingestor" (Bulk Reddit & Forum Parser)
* **Objective:** Ingest massive dumps of Reddit threads, G2 reviews, and competitor documentation.
* **Power Needed:** Massive context window (100k–1M+ tokens), low cost, high throughput.
* **Allocated Provider & Model:** **Google AI Studio (`gemini-2.0-flash` / `gemini-1.5-flash`)**.
* **Key Configuration:** `GEMINI_KEY_POOL`.
* **Why:** Ingests 50 to 100 complete Reddit discussion threads in a single prompt without chunking or losing context.

### Sub-Agent C: "The Extractor" (Pain Point & Frustration Classifier)
* **Objective:** Parse ingested data and extract specific customer complaints containing frustration markers (*"I hate..."*, *"This sucks..."*, *"I wish there was..."*), attaching verbatim quotes.
* **Power Needed:** Medium reasoning, high classification precision, fast processing.
* **Allocated Provider & Model:** **Groq (`llama-3.3-70b-versatile`)** or **Cerebras (`llama3.3-70b`)**.
* **Key Configuration:** `GROQ_KEY_POOL` / `CEREBRAS_KEY_POOL`.
* **Why:** Llama 3.3 70B has near-GPT-4 level extraction accuracy and runs at ~400–1,800 tokens/second for free.

### Sub-Agent D: "The Architect" (Gap Synthesis & Startup Concept Design)
* **Objective:** Connect extracted pain points with market dynamics. Identify unbundling opportunities, calculate TAM, design product features, and ensure the concept isn't a clone.
* **Power Needed:** Maximum reasoning IQ, deep strategic nuance.
* **Allocated Provider & Model:** **GitHub Models (`gpt-4o`)** or **Google AI Studio (`gemini-1.5-pro`)**.
* **Key Configuration:** `GITHUB_TOKEN_POOL` or `GEMINI_PRO_KEY`.
* **Why:** Deep reasoning is essential here to turn a vague Reddit complaint into a defensible $1M SaaS architecture.

### Sub-Agent E: "The Copywriter" (Fake Door & Landing Page Generator)
* **Objective:** Generate high-converting landing page prompts (for Lovable or Framer) and craft quiz funnels using exact customer language.
* **Power Needed:** High emotional intelligence, persuasive copywriting, strict Markdown adherence.
* **Allocated Provider & Model:** **Google AI Studio (`gemini-1.5-pro`)** or **Claude 3.5 Sonnet (via OpenRouter/GitHub)**.
* **Key Configuration:** `GEMINI_KEY_POOL`.
* **Why:** Claude and Gemini Pro excel at human-like, empathetic copy that resonates with users' stated frustrations.

---

## 2. Technical Opencode Sub-Agent Directory Structure

To implement this multi-agent system in your workspace, configure dedicated agent directories inside `.opencode/agents/`:

```
D:\Start\.opencode\
├─ opencode.json
├─ skills/
│   └─ market-gap-finder/SKILL.md
└─ agents/
    ├─ scout/CONFIG.md          # Configured for Groq 8B
    ├─ ingestor/CONFIG.md       # Configured for Gemini 2.0 Flash
    ├─ extractor/CONFIG.md      # Configured for Llama 3.3 70B
    ├─ architect/CONFIG.md      # Configured for GPT-4o / Gemini 1.5 Pro
    └─ copywriter/CONFIG.md     # Configured for Gemini 1.5 Pro
```

---

## 3. Advantages, Limitations & Strategic Trade-offs

| Dimension | Dedicated Sub-Agent Architecture | Monolithic Single-Model Architecture |
| :--- | :--- | :--- |
| **Cost** | **$0 (100% Free)** by distributing load across 4 different free tiers. | Hits rate limits quickly; forces paid model upgrades. |
| **Speed** | **Extremely Fast** (Light tasks take 200ms; heavy tasks only run when needed). | Slow (runs high-IQ models on simple tasks). |
| **Context Limit** | **No bottlenecks** (Ingestor gets 1M tokens; Extractor gets fast 128k). | Context bottlenecks or token truncation errors. |
| **Complexity** | Requires managing multiple keys and sub-agent configs in `.env`. | Simple single-key setup. |
| **Failure Risk** | **Low:** If Groq goes down, Gemini handles the pipeline, and vice versa. | **High:** If the single API provider limits you, the entire engine halts. |
