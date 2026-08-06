# The Opencode Market Intelligence Engine

This document details the precise technical setup for your Market Intelligence Engine, based entirely on the initial "opencode" prompt and updated for the **Free Model (Gemini) Multi-Source Strategy**.

## 1. Profile Constraints
- **Time:** Lean startup profile (15-25 hrs/week).
- **Budget:** $0 - $500.
- **Domain Knowledge:** Strong edge in SaaS, Fintech, and AI/ML Infra.
- **Strategy:** Do not hunt for "everything." Use Opencode to build an engine that finds high-value, low-competition gaps.

## 2. The Tech Stack (Infrastructure)
Upgrade `opencode.json` with the following MCPs (Model Context Protocol extensions). We use a multi-source strategy with environment variables (`.env`) for security and scalability:

- **Playwright (Web Automation):** Scraping competitor pricing, news, and social discussions.
- **GitHub (API access):** Finding emerging open-source projects.
- **Google (Gemini AI):** The core reasoning engine and web search, running on `gemini-1.5-pro-latest` (generous free tier of ~$5/day limit).
- **Twitter (Social Listening):** Pulling top trending hashtags and live complaints in Fintech.

## 3. Required AI Skills
Give the model specialized knowledge by creating these skills:
- **`market-gap-finder`:** Instructs an agent to specifically look for "negative reviews," "feature requests," or "unmet user needs."
- **`competitor-profiler`:** Scrapes a competitor's landing page and generates a feature/pricing matrix.

## 4. The 3-Layer Research Pipeline
1. **Macro Scan:** Use a general agent with websearch to identify high-growth sectors.
2. **Pain Point Mining:** Use Playwright/Twitter MCPs to scrape Reddit, Hacker News, G2, and X (Twitter).
3. **Gap Synthesis:** Use **Gemini 1.5 Pro** to cross-reference complaints with existing products.

## 5. Immediate Action Plan (Code Execution)
To set this up, run the following exactly as provided:

**Step 1: Workspace Structure & Env setup**
```bash
mkdir -p .opencode/skills/market-gap-finder
mkdir -p .opencode/agents/researcher
npm i dotenv
```

**Step 2: Create `.env` file**
In the root directory, create a `.env` file to securely hold your keys:
```env
GOOGLE_KEY=AIzaSy...
TWITTER_BEARER=AAAAAAAA...
```

**Step 3: Create the Skill**
Copy the following template exactly into `.opencode/skills/market-gap-finder/SKILL.md`:
```markdown
---
name: market-gap-finder
description: Use when you want to find unmet user needs or feature gaps in a specific industry.
---
# Market Gap Finder

Use this skill to analyze a specific industry (e.g., "Fintech API") and identify:
1. Common user complaints in recent forum discussions.
2. Features that competitors are missing.
3. Unbundling opportunities (taking one feature from a giant and making it a standalone tool).
```

**Step 4: First Execution**
Restart Opencode with the new configuration, passing specific @source tags if needed:
`@market-gap-finder @source:google @source:twitter Analyze the current friction points in AI/ML Infrastructure deployment for mid-sized SaaS companies.`
