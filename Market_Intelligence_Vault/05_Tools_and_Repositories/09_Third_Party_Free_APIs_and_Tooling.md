# Third-Party Free APIs & Tooling (Non-LLM Ecosystem)

To make your Market Intelligence Engine frictionless and powerful, you should not rely on LLMs for raw data fetching, web crawling, or storage. Combining specialized **free developer APIs and non-LLM tools** drastically reduces token consumption, eliminates scraping headaches, and automates notifications.

---

## 1. Web Scraping & Clean Markdown APIs

| Tool / API | Free Tier Allowance | How It Works | Best Used For |
| :--- | :--- | :--- | :--- |
| **[Jina Reader API](https://jina.ai/reader/)** | **100% Free** (No API key required; optional key for higher rate limits) | Prepend `https://r.jina.ai/` to any URL (e.g. `https://r.jina.ai/https://example.com`). Returns clean, LLM-ready Markdown, stripping out ads, scripts, and navigation clutter. | Scraping competitor landing pages, pricing tables, and blog posts without needing Playwright. |
| **[Firecrawl](https://www.firecrawl.dev/)** | **500 free credits/month** | Clean API that converts entire websites or subpages into structured Markdown and clean JSON. | Crawling competitor documentation or changelogs. |
| **[Reddit Native JSON Endpoint](https://www.reddit.com)** | **100% Free** (No API key needed for light-to-moderate use) | Simply append `.json` to any Reddit URL (e.g. `https://www.reddit.com/r/SaaS/comments/xxxx.json`). Returns pure structured JSON containing all comments, upvotes, and authors. | Fetching full Reddit discussions instantly without rendering web pages or running browser automation. |
| **[Hacker News Firebase API](https://github.com/HackerNews/API)** | **100% Free** (Public, official, no rate limit caps) | Official REST API (`https://hacker-news.firebaseio.com/v0/item/{id}.json`). | Mining developer and tech startup pain points from "Ask HN" and "Show HN" threads. |

---

## 2. Search & Social Intelligence APIs

| Tool / API | Free Tier Allowance | How It Works | Best Used For |
| :--- | :--- | :--- | :--- |
| **[Tavily Search API](https://tavily.com/)** | **1,000 free searches/month** | Built specifically for AI agents. Performs web search and returns relevant, extracted content rather than raw HTML. | Real-time fact-checking and automated competitor discovery for Sub-Agent A (The Scout). |
| **[Serper.dev / SerpApi](https://serper.dev/)** | **2,500 free Google searches** (one-time on signup) | High-speed Google Search API returning clean JSON search results. | Running Google Advanced Search queries (`site:reddit.com "I hate" + [niche]`). |
| **[DuckDuckGo Free API / Scrapers](https://duckduckgo.com)** | **100% Free / No auth** | Open-source Python/Node wrappers (e.g., `duckduckgo-search`). | Zero-cost macro search queries without consuming API quotas. |
| **[GitHub GraphQL / REST API](https://docs.github.com/en/rest)** | **5,000 requests/hour** (with free GitHub PAT) | Direct querying of trending repos, issue trackers, and open-source discussion boards. | Mining feature requests and user bugs on competitor open-source repos. |

---

## 3. Serverless Databases & Storage (Free Tiers)

| Service | Free Tier Allowance | Type | Role in Your Engine |
| :--- | :--- | :--- | :--- |
| **[Turso Database](https://turso.tech/)** | **9 GB storage, 500 databases**, 1B row reads/month | Serverless SQLite (libSQL) | Storing extracted pain points, competitor profiles, and validated gaps permanently. |
| **[Supabase](https://supabase.com/)** | **500 MB database**, 50,000 monthly active users, `pgvector` included | Hosted PostgreSQL | Vector search over historical pain points so you never analyze the same Reddit thread twice. |
| **[Upstash Redis](https://upstash.com/)** | **10,000 commands/day** | Serverless Redis | Queue management for sub-agents, rate-limit tracking, and API key rotation state. |

---

## 4. Webhooks, Alerts & Notification Tools

| Tool | Free Tier | Use Case |
| :--- | :--- | :--- |
| **[Discord Webhooks](https://discord.com/developers/docs/resources/webhook)** | **100% Free & Unlimited** | Create a private Discord server. Have your agents post a rich embed whenever they find a high-conviction gap. |
| **[Telegram Bot API](https://core.telegram.org/bots/api)** | **100% Free & Unlimited** | Receive instant mobile notifications on your phone when Sub-Agent D finishes generating a new startup plan. |

---

## 5. Comprehensive Analysis: Advantages, Limitations & Concerns

### Core Advantages
1. **Token Efficiency:** Using Jina Reader or Reddit's `.json` endpoint reduces token consumption by 80–90% compared to feeding raw HTML into an LLM.
2. **Speed & Reliability:** Calling a JSON endpoint takes 50ms, whereas running a full headless browser via Playwright takes 2–5 seconds per page.
3. **Zero Cost Stack:** Combining free search (Tavily/DuckDuckGo), free parsing (Jina), free LLM inference (Groq/Gemini), and free databases (Turso) yields an enterprise-grade engine for **$0**.

### Limitations & Concerns to Manage
* **Reddit IP Throttling:** Rapid unauthenticated requests to `.json` endpoints can lead to temporary IP blocks (HTTP 429). 
  - *Mitigation:* Add a 1–2 second delay between requests, set a custom `User-Agent` header, or use Playwright as a fallback.
* **Monthly Quota Expirations:** Tools like Tavily (1,000/mo) and Firecrawl (500/mo) have hard monthly caps.
  - *Mitigation:* Route high-volume queries through DuckDuckGo/Jina Reader first, reserving Tavily for refined searches.
* **Data Privacy:** Avoid passing proprietary business data into third-party free proxies. (For market research on public Reddit data, this is not an issue).
