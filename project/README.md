# 🚀 Market Intelligence & Gap Mining Engine

An autonomous, 100% free-tier research pipeline designed to mine customer friction from Reddit, Hacker News, and community boards, and synthesize validated B2B Micro-SaaS startup opportunities.

---

## 📁 Project Structure

```
D:\Start\project\
│
├── .env.example              # Free API key templates (Groq, Gemini, HF)
├── .env                      # Your local keys (ignored in Git)
├── requirements.txt          # Python dependencies (requests, rich, dotenv)
├── main.py                   # Interactive & CLI Entry Point
│
├── src/
│   ├── key_manager.py        # Round-robin key rotation & multi-provider fallback
│   ├── miners/
│   │   ├── reddit_miner.py   # Zero-cost Reddit .json scraper & pain detector
│   │   ├── hn_miner.py       # Free Hacker News Algolia discussion miner
│   │   └── jina_fetcher.py   # Jina Reader API clean web markdown parser
│   ├── extractors/
│   │   └── gap_synthesizer.py# Structured Markdown Dossier generator
│   └── exporters/
│       └── vault_exporter.py # Syncs reports to Obsidian Vault & output/
│
└── output/                   # Generated market research dossiers
```

---

## ⚡ Quick Start (2 Steps)

### Step 1: Install Dependencies
Open your terminal in `D:\Start\project` and run:
```bash
pip install -r requirements.txt
```

### Step 2: (Optional) Add Free AI Keys to `.env`
Open `D:\Start\project\.env` and paste any free key you have:
* **Groq Console (Recommended - 14.4k req/day):** `https://console.groq.com`
* **Google AI Studio (1,500 req/day):** `https://aistudio.google.com`
* **Hugging Face (Serverless):** `https://huggingface.co/settings/tokens`

*(Note: Even without API keys, the engine will still collect and organize all Reddit & Hacker News discussions into raw dossiers!)*

---

## 🎯 How to Run Scans

### Option A: Interactive Mode (Easiest)
```bash
python main.py
```
This opens an interactive menu where you can choose a preset domain (AI/ML Infra, SaaS Billing, Fintech Compliance) or type your own custom niche.

### Option B: Custom CLI Command
```bash
python main.py --topic "AI model deployment CI CD" --subreddits mlops devops MachineLearning --limit 20
```

---

## 🔍 Audit Any Idea
Audit any idea: `python main.py inspect`, click a row, and follow the URLs back to the raw source data (Reddit, GitHub, HN, Shopify reviews, YouTube timestamps).

```bash
python main.py inspect
```
This launches a local Datasette server on `http://127.0.0.1:8001` with canned evidence queries and relational navigation across `ideas -> clusters -> pain_points -> raw_items`.
