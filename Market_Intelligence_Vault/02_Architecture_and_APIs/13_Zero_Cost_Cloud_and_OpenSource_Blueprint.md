# Zero-Cost Cloud & Open-Source Architecture Blueprint

This document codifies the core operating mandate for the Market Intelligence Engine: **100% Free of Cost, Cloud-Hosted (No Local Storage Bottlenecks), and Powered by Open-Source & Free Cloud Ecosystems (Hugging Face, GitHub Actions, Supabase, Vercel, Tally).**

Because this is an asynchronous market research engine, latency delays of 5 to 10 seconds per deep query are completely acceptable, allowing us to leverage free serverless tiers and open-source models with zero trade-offs in output quality.

---

## 1. Cloud-Hosted Storage & Compute (Zero Local Clutter)

| Purpose | Tool / Platform | Free Tier Quota | Why It Replaces Paid Software |
| :--- | :--- | :--- | :--- |
| **Cloud Vector & Relational DB** | **[Supabase Cloud](https://supabase.com)** | • **500 MB Database**<br>• `pgvector` extension included<br>• Hosted PostgreSQL | Eliminates local storage. Stores all customer complaints, upvotes, and vector embeddings in the cloud for semantic search. |
| **Edge Serverless Database** | **[Turso Cloud](https://turso.tech)** | • **9 GB Storage**<br>• 500 databases<br>• 1 Billion row reads/mo | Lightning-fast cloud SQLite for structured market scan logs and competitor tables. |
| **Free Cloud Datasets & Space** | **[Hugging Face Hub](https://huggingface.co)** | • **Unlimited private datasets**<br>• **Free 24/7 CPU Spaces** (Docker/Gradio/Streamlit) | Push raw market scan datasets directly to private Hugging Face Datasets via `huggingface_hub`. Run background agents 24/7 on free HF Spaces without leaving your PC running. |
| **Cloud Automation & Cron** | **[GitHub Actions](https://github.com/features/actions)** | • **2,000 free minutes/month** on private repos | Automates nightly scraping and analysis runs in the cloud on GitHub's servers for $0. |

---

## 2. Open-Source & Free AI Inference Ecosystem

| Service | Supported Free Open-Source Models | Limits / Tier | Strategic Advantage |
| :--- | :--- | :--- | :--- |
| **[Hugging Face Serverless API](https://huggingface.co/docs/api-inference)** | `Qwen/Qwen2.5-72B-Instruct`<br>`deepseek-ai/DeepSeek-R1`<br>`BAAI/bge-large-en-v1.5` | Free with standard Hugging Face Token | Access to the entire open-source model ecosystem without local GPU requirements. |
| **[Google AI Studio](https://aistudio.google.com)** | `gemini-2.0-flash`<br>`gemini-1.5-flash`<br>`gemini-1.5-pro` | **1,500 requests/day**<br>1M–2M context window | Handles massive bulk Reddit dumps and full competitor document parsing for $0. |
| **[Groq Console](https://console.groq.com)** | `llama-3.3-70b-versatile`<br>`llama-3.1-8b-instant`<br>`mixtral-8x7b-32768` | **14,400 req/day (8B)**<br>1,000–3,000 req/day (70B) | High-speed structured JSON parsing and classification at ~500 t/s. |
| **[Cerebras Inference](https://cloud.cerebras.ai)** | `llama3.3-70b`, `llama3.1-8b` | **1,000,000 tokens/day** | World-record inference speed (~2,000 t/s) for high-volume batch processing. |
| **[GitHub Models](https://github.com/marketplace/models)** | `gpt-4o`, `gpt-4o-mini`, `phi-4` | 50–150 calls/day high-end | Free access to GPT-4o reasoning via your GitHub Personal Access Token. |

---

## 3. Free Web Scraping & Ingestion Layer

| Task | Free Open-Source / Cloud Tool | Paid Tool It Replaces |
| :--- | :--- | :--- |
| **Clean Web-to-Markdown** | **[Jina Reader API](https://jina.ai/reader/) (`https://r.jina.ai/<URL>`)** | Paid web scrapers / scraping proxies |
| **Reddit Discussion Extraction** | **Reddit Public `.json` Endpoints** | Expensive Reddit API tiers & proxy services |
| **Developer Discussions** | **Hacker News Firebase API** | Paid social listening tools |
| **AI Web Crawler** | **[Crawl4AI](https://github.com/unclecode/crawl4ai)** (run in HF Spaces or GitHub Actions) | Apify / ScrapingBee ($49–$199/mo) |

---

## 4. 100% Free Online Validation & Go-To-Market Stack

| Function | 100% Free Tool | Paid Alternative Replaced |
| :--- | :--- | :--- |
| **Landing Page Hosting** | **[Vercel](https://vercel.com) / [Cloudflare Pages](https://pages.cloudflare.com)** (Unlimited sites, custom domains, global CDN) | Webflow ($29/mo), Framer Pro ($30/mo) |
| **Fake Door Quiz & Survey** | **[Tally.so](https://tally.so)** (Unlimited forms, unlimited responses, custom logic, Webhook integration) | Typeform ($29–$89/mo) |
| **Waitlist & Transactional Email** | **[Resend](https://resend.com)** (3,000 free emails/mo) or **[Brevo](https://brevo.com)** (300 emails/day) | Mailchimp ($20–$50/mo) |
| **Real-time Mobile Alerts** | **Discord Webhooks / Telegram Bot API** (Unlimited push notifications) | PagerDuty / Slack paid integrations |

---

## 5. End-to-End Cloud Data Flow (Zero Local Footprint)

```
[GitHub Actions / HF Spaces] (Scheduled Cloud Scraper)
              |
              v (Fetches clean markdown via Jina Reader & Reddit .json)
[Groq / Gemini 2.0 Flash] (Free AI Extraction of Pain Points)
              |
              v (Saves structured data & embeddings in cloud)
[Supabase / Turso Cloud DB] (Cloud Data Store)
              |
              v (Sends instant notification of high-signal gap)
[Discord / Telegram Webhook] -> (Direct to Your Phone)
              |
              v (Builds free landing page + quiz)
[Vercel + Tally.so] (100% Free Online Fake Door Test)
```

### Summary of Rules:
1. **$0 Spend on Software:** Never pay for databases, hosting, forms, scrapers, or AI APIs.
2. **Cloud-First:** All persistent data lives in Supabase, Turso, or Hugging Face.
3. **10-Second Latency Budget:** We prioritize model size, reasoning depth, and cost ($0) over millisecond conversational latency.
