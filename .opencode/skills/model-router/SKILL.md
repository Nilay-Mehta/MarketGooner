---
name: model-router
description: Autonomous token optimizer and multi-provider model routing strategy. Directs tasks to Groq, Gemini, or OpenRouter based on context size, speed requirements, and token economy.
---

# Autonomous Model & Token Routing Strategy

To conserve free quotas and maximize intelligence, always route tasks according to this logic:

| Task Type | Optimal Provider & Model | Rationale & Token Strategy |
| :--- | :--- | :--- |
| **High-Speed Filtering & JSON Extraction** | **Groq (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`)** | Uses Groq's 14,400 daily requests and ~500 t/s speed. Keeps high-frequency small queries off Gemini. |
| **Massive Context & Multi-Thread Ingestion** | **Google AI Studio (`gemini-2.0-flash` / `gemini-1.5-pro`)** | Uses Gemini's 1M–2M context window. Feeds 30+ full Reddit threads or lengthy competitor docs in a single request. |
| **Deep Reasoning & Failover Fallback** | **OpenRouter (`deepseek-r1:free`, `qwen-2.5-72b:free`)** | Engages deep chain-of-thought reasoning for market sizing and competitive moats, or acts as fallback if rate limits occur. |

## Fallback Rule:
If any provider returns a rate limit (HTTP 429), automatically failover to the next available provider in sequence (`Groq` -> `Gemini` -> `OpenRouter`).
