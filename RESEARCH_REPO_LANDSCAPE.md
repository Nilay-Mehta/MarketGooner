# Repo landscape for D:\Start\project — 2026-08 research

Scope: pure research; no code changes. Focus is on repos that address the 8 known-remaining gaps of the Market Intelligence & Gap Mining Engine (character-span grounding, cluster labels, cheaper scraping, LLM cost routing, semantic-search UI, waitlist tooling, LLM evals, existing market-research MCPs).

## Quick executive summary

- **Adopt now #1:** `google/langextract` — the only mainstream library that returns exact character offsets per extracted field, directly solving the quote-grounding gap in `pain_extractor.py`.
- **Adopt now #2:** `asg017/sqlite-vec` (already on the roadmap) plus the `datasette-embeddings` plugin — gets the semantic-search UI for free without leaving the SQLite/Datasette stack.
- **Adopt now #3:** `BerriAI/litellm` — one-line drop-in that centralises the existing Groq/Gemini/OpenRouter cascade currently hand-rolled around `key_manager.py`, adds semantic caching hooks, and unlocks any provider without further refactors.
- **Steal patterns from #1:** `stanford-oval/storm` — its perspective-diversification + citation-required drafting is the model for `cluster.py`+`rank.py` output.
- **Steal patterns from #2:** `assafelovic/gpt-researcher` — its recursive-depth "source cascade" and per-source scoring is more mature than what the current gates do.
- **Steal patterns from #3:** `king-of-the-grackles/reddit-research-mcp` — hosted-MCP shape shows what the project could expose to Claude Desktop later.
- **Build ourselves (no good OSS):** a *pain-cluster-to-idea ranking* layer with WTP + Trends + citation evidence. Nothing OSS combines these; existing MCPs return raw signals only.
- **Reject:** BAML, Guidance, Marvin — either wrong-language ergonomics or duplicative of the existing `instructor` stack.
- **Reject:** GPTCache, RouteLLM as standalone deps — LiteLLM subsumes both.
- **Watch, don't adopt yet:** LanceDB (great for >10 M vectors but overkill; sqlite-vec is enough at current scale).

## By category

### 1. Multi-source research agents

| Repo | Stars | Last commit | License | What it does | Fit for D:\Start\project |
|---|---|---|---|---|---|
| assafelovic/gpt-researcher | ~28 k | active (2026) | Apache-2.0 | Autonomous multi-agent research with recursive depth/breadth and cited reports | Steal source-cascade + report-writer patterns; do NOT wholesale adopt (too much runtime overhead) |
| stanford-oval/storm | ~29.6 k | active (2026, MIT) | MIT | LLM-powered knowledge-curation system that writes wiki-style articles with per-fact citations | Steal the perspective-diversification loop for cluster narratives + rank rationales |
| langchain-ai/open_deep_research | ~5 k | active | MIT | LangGraph-based deep-research reference agent, ranks on Deep Research Bench | Reference implementation only; too LangChain-heavy to import |

**Pattern worth stealing:** all three converge on the same shape — *plan → per-perspective sub-queries → per-source citation binding → conflict-aware synthesis*. `pain_extractor` currently binds citations to a raw URL; the STORM/gpt-researcher pattern is a per-sentence citation map that survives into the ranked-idea output. Adopting this pattern (not the code) would let `rank.py` say "idea supported by 12 quotes across 4 sources", which is exactly what the WTP gate wants.

### 2. Structured LLM extraction with grounding

| Repo | Stars | Last commit | License | What it does | Fit for D:\Start\project |
|---|---|---|---|---|---|
| google/langextract | rising (released Jul 2025, high momentum) | active | Apache-2.0 | LLM structured extraction with **character-span provenance** per field, HTML visualiser | **Direct fix for the character-span quote-grounding gap.** Works with Gemini / OpenAI / Ollama. |
| jxnl/instructor | ~11 k | active | MIT | Pydantic-first structured outputs w/ retry loop | Already in use — keep; complement with LangExtract for the spans |
| dottxt-ai/outlines | ~12 k | active | Apache-2.0 | Constrained decoding / guaranteed schema | Consider ONLY if moving to local models |
| BoundaryML/baml | ~4 k | active | Apache-2.0 | Schema-first .baml DSL | Reject — extra build step, TS-oriented |
| stanfordnlp/dspy | ~22 k | active | MIT | Prompt-programming / optimisation | Interesting for optimising the extractor prompt itself; defer |

**Pattern worth stealing:** LangExtract's chunk-parallel-multi-pass pipeline over long documents is a better shape than the current single-shot extraction and would raise recall on long Reddit threads / Shopify review batches.

### 3. LLM-optimised web scraping (Jina Reader alternatives)

| Repo | Stars | Last commit | License | What it does | Fit for D:\Start\project |
|---|---|---|---|---|---|
| unclecode/crawl4ai | ~60 k | active | Apache-2.0 | LLM-friendly async crawler + markdown extractor, ~5× faster than headless-Chromium wrappers | Best free replacement for Jina Reader for JS-light pages |
| adbar/trafilatura | ~4 k+ | active (2.2.x in 2026) | Apache-2.0 | Boilerplate-removing text extractor, top of ScrapingHub bench (F1 ≈ 0.87) | Zero-LLM cheap first pass; fall back to Crawl4AI for JS pages |
| mendableai/firecrawl | ~15 k+ OSS core (larger figures conflate SaaS) | active | AGPL-3.0 (self-host); SaaS otherwise | Managed API + self-host OSS core | Reject direct dep — licence mismatch for the project; use Crawl4AI instead |
| microsoft/markitdown | ~150 k | active | MIT | 15+ file-format → markdown | Adopt for PDF/DOCX inputs the current pipeline can't ingest |
| datalab-to/marker | ~38 k | active | GPL-3.0 (weights CC-BY-NC-SA w/ small-org waiver) | Fast PDF → markdown with layout | Only if PDF quality matters; licence is copyleft |

**Pattern worth stealing:** Crawl4AI's *"fit_markdown"* pass — an LLM-post-filter that keeps only content relevant to a topic — is a template for a topic-scoped scraper that would cut LLM token spend downstream.

### 4. Reddit / HN / community scraping

| Repo | Stars | Last commit | License | What it does | Fit |
|---|---|---|---|---|---|
| praw-dev/praw | ~4.1 k | active (Apr 2026) | BSD-2 | Official-API Reddit wrapper | Keep as primary |
| ArthurHeitmann/arctic_shift | ~500 | active | MIT | Post-Pushshift historical dumps (monthly torrents) | Adopt for historical backfill of subs before creation date |
| maxjo020418/BAScraper | small | active | MIT | Async PullPush + Arctic-Shift wrapper | Adopt in place of DIY HTTP calls |
| santiagobasulto/python-hacker-news | small | old but stable | MIT | Thin wrapper for HN Algolia | Optional; direct HTTP against Algolia is fine |

**Pattern worth stealing:** BAScraper's rate-limit-and-fallback design (PullPush → Arctic dump) is exactly what should live behind `sources/reddit.py`.

### 5. Vector DBs (embedded)

| Repo | Stars | Last commit | License | Fit |
|---|---|---|---|---|
| asg017/sqlite-vec | ~8 k | active | MIT | **Winner — already on your roadmap.** Same process as your existing SQLite. |
| lancedb/lancedb | ~5 k+ | very active | Apache-2.0 | Better at 10 M+ vectors; adds an extra store. Defer. |
| chroma-core/chroma | ~20 k+ | active | Apache-2.0 | Better prototyping DX, but forces a second store. Skip. |
| duckdb VSS extension | n/a | active | MIT | Great if analytical joins matter; overlaps Datasette. Skip. |

**Pattern worth stealing:** none — sqlite-vec's binary-quantisation `vec0` virtual tables are the pattern.

### 6. Topic modeling with better labelling

| Repo | Stars | Last commit | License | Fit |
|---|---|---|---|---|
| MaartenGr/BERTopic | ~7 k+ | active | MIT | Keep — but wire in its **`OpenAI` / `LlamaCPP` representation model** which replaces c-TF-IDF keyword mashups with clean LLM labels in one config line |
| charlesdedampierre/BunkaTopics | small (<1 k) | active | MIT | Small userbase; useful for the visualiser only |
| zhang-yu-wei/ClusterLLM | small | 2024 | MIT | Research code; ideas worth stealing (LLM-guided triplet clustering) |
| TnT-LLM (Microsoft paper, no first-party repo) | — | — | — | Adopt the *summarise-first-then-taxonomy* algorithm; implement in-house — it's ~100 LOC |

**Pattern worth stealing:** TnT-LLM's two-stage "summary → taxonomy" makes labels human-readable and reusable, and slots cleanly on top of the existing BERTopic step without replacing it. This is the highest-leverage single change for cluster-label quality.

### 7. Trend signal APIs (pytrends alternatives)

| Repo | Stars | Last commit | License | Fit |
|---|---|---|---|---|
| GeneralMills/pytrends | ~3 k | intermittent | Apache-2.0 | Still the OSS baseline; rate-limits painful |
| trendspy | small | active | MIT | Newer pytrends fork with better proxy handling |
| DataForSEO free tier | — | — | commercial | Reject — paid |
| Glimpse | — | — | commercial | Reject — paid |

**Reality check:** there is **no** actively maintained OSS project that gives Exploding-Topics-style *emerging-topic detection*. Build a small internal signal from Reddit post-velocity + HN comment-count delta instead of adopting anything here.

### 8. LLM cost routing / caching

| Repo | Stars | Last commit | License | Fit |
|---|---|---|---|---|
| BerriAI/litellm | ~53 k | very active | MIT | **Adopt.** Wraps every provider (Groq, Gemini, OpenRouter, Together, local) behind one call, includes retries, budgeting, and semantic-cache hooks |
| aurelio-labs/semantic-router | ~3.2 k | active | MIT | Adopt lightly — sub-1 ms intent classifier can route trivial extraction paths to smaller / cheaper models |
| zilliztech/GPTCache | ~7.9 k | slower | MIT | Reject as separate dep — LiteLLM's cache subsumes it |
| lm-sys/RouteLLM | ~4 k | quiet since 2025 | Apache-2.0 | Reject — LiteLLM auto-routing covers this |
| portkey-ai/gateway | growing | active (Apache-2.0 since Mar 2026) | Apache-2.0 | Worth watching for observability; not needed now |

**Pattern worth stealing:** LiteLLM Router's *fallback-list-with-per-model-budget* directly maps to the goal of "burn the free Groq quota first, then Gemini free, then OpenRouter paid".

### 9. LLM eval / grounding-check

| Repo | Stars | Last commit | License | Fit |
|---|---|---|---|---|
| explodinggradients/ragas | ~7 k+ | active | Apache-2.0 | *Faithfulness* metric is exactly the grounding check `pain_extractor` needs |
| confident-ai/deepeval | ~5 k+ | very active | Apache-2.0 | 50+ pytest-native metrics; useful for a CI grounding-regression gate |
| promptfoo/promptfoo | ~10.8 k | very active | MIT | Better for prompt A/B + red-team than for grounding |
| truera/trulens | ~2 k+ | active | MIT | OpenTelemetry integration; overkill until there's production traffic |

**Pattern worth stealing:** Ragas' faithfulness score (LLM-as-judge on "is this claim supported by the retrieved context") plus LangExtract's character spans gives a **cheap, automated** grounding gate that could replace the manual coherence step.

### 10. Market-intelligence / idea-generation MCPs

| Repo | Stars | Last commit | License | Fit |
|---|---|---|---|---|
| king-of-the-grackles/reddit-research-mcp | ~226 | active | MIT | Closest analogue: semantic search across 20 k subs, FastMCP + PRAW + ChromaDB. Read as a **reference implementation** for exposing the project as an MCP later. |
| Houseofmvps/reddit-intel-agent-mcp | small | active | MIT (14 tools, no key/signup) | Similar shape; more tools, less polish |
| No general "market-research MCP" with any traction found | — | — | — | Everything else is a paid SaaS wrapper (BigIdeasDB etc.) |

**Conclusion:** *none of these actually do what your project does* — they surface raw Reddit signal, they do not run coherence/WTP/Trends gates and rank ideas. So do NOT replace the stack; instead, consider exposing your DB as an MCP server, treating these repos as templates for the tool schema.

### 11. Fake-door / landing page / waitlist OSS

| Repo | Stars | Last commit | License | Fit |
|---|---|---|---|---|
| formbricks/formbricks | ~12.5 k | very active | AGPL-3.0 | **Best fit.** Self-hosted, event-triggered surveys → perfect for the "post-idea-pick validation" step |
| umami-software/umami | ~25 k+ | very active | MIT | Analytics only — pair with a static waitlist form |
| plausible/analytics | ~22 k+ | active | AGPL-3.0 | Same category as Umami; MIT-preferred means Umami wins |
| PostHog (OSS core) | large | active | MIT (some MIT / Apache mix) | Overkill for one landing page; consider only if adding product analytics |
| raqibnur/quick-waitlist | small | active | MIT | Next.js starter; useful only as scaffolding |

**Pattern worth stealing:** Formbricks' *"in-app survey triggered on event X"* pattern makes it trivial to run price-sensitivity questions on top of a waitlist form.

### 12. Data-quality / schema validation for LLM outputs

| Repo | Stars | Last commit | License | Fit |
|---|---|---|---|---|
| unionai-oss/pandera | ~3 k+ | active | MIT | Adopt for DataFrame-level checks between `extractor` → `cluster` → `rank` |
| great-expectations/great_expectations | ~10 k+ | active | Apache-2.0 | Heavier; only if adding a proper "data contract" step |
| jxnl/instructor (retries) | already in stack | — | MIT | Covers the field-level schema drift |
| guardrails-ai/guardrails | ~4 k+ | active | Apache-2.0 | Overlaps LangExtract + Ragas; skip |

**Pattern worth stealing:** Pandera schemas as *pipeline stage contracts* — each of extractor/cluster/rank asserts the shape of what it receives. Catches drift when a new source is added.

### 13. Semantic search UIs over the pain DB

| Repo | Stars | Last commit | License | Fit |
|---|---|---|---|---|
| simonw/datasette + `datasette-embeddings` plugin | 10 k+ | active | Apache-2.0 | **Winner** — already using Datasette; plugin adds a "semantic search against this table" action with zero new servers |
| Chainlit/chainlit | ~7 k+ | active | Apache-2.0 | Best if a chat-over-DB UI matters (Q&A on pain clusters) |
| streamlit + `st.chat` | very large | active | Apache-2.0 | Familiar; fine for internal dashboards |
| vanna-ai/vanna | ~10 k+ | active | MIT | Text-to-SQL over the pain DB; interesting complement, defer |

**Pattern worth stealing:** Datasette's "table-action plugins" pattern means UI features attach without rewriting the storage layer.

## Kill list (evaluated and rejected)

- **BAML** — extra `.baml` build step; TS-first; duplicates `instructor` for a Python-only pipeline.
- **Marvin** — OpenAI-only; the project needs the multi-provider cascade.
- **Guidance** — mainly serves the constrained-decoding case Outlines already covers.
- **Firecrawl (self-host)** — AGPL-3.0 core forces the whole project to AGPL; Crawl4AI is Apache-2.0.
- **GPTCache, RouteLLM (as standalone deps)** — LiteLLM subsumes both.
- **Chroma / LanceDB** — second storage engine unnecessary while sqlite-vec covers current scale.
- **Marker (PDF)** — GPL-3.0 with a CC-BY-NC-SA weight licence; only worth it if PDFs become a first-class source.
- **DataForSEO / Glimpse / Exploding Topics** — paid SaaS, not OSS.
- **BigIdeasDB MCP** — paid SaaS wearing an MCP badge.
- **Guardrails** — overlapping surface with LangExtract + Ragas.
- **DSPy (now)** — powerful but big commitment; revisit only when the extractor prompt starts drifting.

## Recommended integration order

1. **LangExtract for `pain_extractor.py`** — closes the character-span quote-grounding gap directly; drop-in per-field spans that the verify command can now check. *Est. effort: 4–6 h*.
2. **LiteLLM behind `key_manager.py`** — replaces the hand-rolled Groq/Gemini/OpenRouter cascade with a supported router; unlocks semantic caching for free. *Est. effort: 3–5 h*.
3. **BERTopic `OpenAI` representation model + a TnT-LLM-style two-stage relabel** — clean, human-readable cluster labels. Pure config + ~100 LOC. *Est. effort: 3 h*.
4. **`datasette-embeddings` on top of sqlite-vec** — semantic-search UI without a new frontend. *Est. effort: 1–2 h*.
5. **Ragas `faithfulness` as a nightly gate** — automated grounding regression check on the extractor. *Est. effort: 3 h*.
6. **Crawl4AI as a fallback fetcher behind Trafilatura** — cheaper than Jina Reader for JS-heavy pages; keep Trafilatura as the zero-LLM first pass. *Est. effort: 4 h*.
7. **Arctic-Shift + BAScraper for historical Reddit backfill** — one-time enrichment. *Est. effort: 2 h*.
8. **Formbricks for the validation-phase landing page** — only when a specific idea is picked. *Defer until then*.
9. **Investigate** exposing the project as an MCP server (à la `reddit-research-mcp`) — defer until above are done; the interesting product surface is the ranked-ideas endpoint, not the raw pain DB.
10. **Do NOT adopt** anything else on the researched list.

Total new dependencies if the top 5 are adopted: 4 (LangExtract, LiteLLM, datasette-embeddings, ragas). Crawl4AI at #6 makes 5. Well within the 5-new-dep budget.
