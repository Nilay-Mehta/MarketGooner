<div align="center">
  <img src="assets/logo.png" alt="Logo" width="220" />
  
  <h1>Market Intelligence & Gap Mining Engine</h1>

  <p>
    <em>An autonomous, 100% free-tier research pipeline that mines customer friction across Reddit and community boards, runs local System 1 decision gating, and synthesizes validated B2B SaaS startup opportunities into Executive Word & Markdown reports.</em>
  </p>

  <p>
    <img alt="Version" src="https://img.shields.io/badge/version-v2.0.0-blue?style=flat-square" />
    <img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
    <img alt="Tests" src="https://img.shields.io/badge/tests-5%2F5%20passing-brightgreen?style=flat-square" />
    <img alt="System 1" src="https://img.shields.io/badge/decision%20engine-ConvAI%20Laya%20(Local%20CPU)-purple?style=flat-square" />
  </p>
</div>

---

## ⚡ How to Run (Web Dashboard, 1-Click Bat, or CLI)

### 🌟 Option A: Interactive Web Dashboard (Best for Presentations & Demos)
Double-click **`RUN_DASHBOARD.bat`** (or run `streamlit run app.py`).
* Opens an executive tech web dashboard in your browser (`http://localhost:8501`).
* Features: Visual Funnel Chart, Friction Category Donut, Evidence Provenance Inspector, Ground Truth Benchmark Tab, and 1-Click Word Doc download!
* Includes a **Safe Presentation Demo Mode** that runs in seconds with zero risk of college Wi-Fi or API failure.

### 🖱️ Option B: The 1-Click Desktop Launcher
Simply double-click **`RUN_PIPELINE.bat`** in this directory. 
* It automatically scrapes Reddit, extracts pain points, clusters them, runs Laya's decision gate, and automatically pops open your finalized **Master Word Report** when finished!

### 💻 Option C: The 1-Line CLI Command
```bash
python main.py run-all --subreddit smallbusiness --query "software" --limit 25
```

#### Custom Niche Examples:
* **Target Restaurant Software:**
  ```bash
  python main.py run-all --subreddit restaurantowners --query "inventory" --limit 20
  ```
* **Target E-Commerce / Shopify Pains:**
  ```bash
  python main.py run-all --subreddit ecommerce --query "shipping" --limit 30
  ```
* **Target Trade Contractors:**
  ```bash
  python main.py run-all --subreddit smallbusiness --query "quickbooks sucks" --limit 20
  ```

---

## 📁 Output Deliverables

Whenever the pipeline runs, all validated opportunities are automatically compiled into **one single unified Master Report** in the `output/` directory:

| Deliverable | Location | Description |
|---|---|---|
| **Master Word Report** | `output/Master_Market_Intelligence_Report.docx` | Executive Word document with styled typography, callouts, and full venture dossiers. |
| **Master Markdown** | `output/Master_Market_Intelligence_Report.md` | Single unified Markdown document ready for Obsidian, Notion, or GitHub. |
| **Individual Dossiers** | `output/dossier_<concept>.docx` & `.md` | Standalone briefs for each individual opportunity. |

*(A complete sample deliverable pack is also saved in `delivery_pack/`)*.

---

## 🏗️ The 5-Stage Architecture

```
[Phase 3: Stealth Ingestion]
  └── Mines Reddit OP + Top 20 Comments via zero-key public RSS feeds.
           │
           ▼
[Phase 3.5: Fast Extraction]
  └── Groq (Qwen-27B) / Gemini extracts canonical PainPoints (Category, Severity, Workarounds).
           │
           ▼
[Phase 4: Domain Clustering]
  └── Enforces tight operational problem wedges (prevents broad generic catch-alls).
           │
           ▼
[Phase 5: Opportunity Gate (System 1)]
  └── ConvAI Laya (421M ModernBERT) runs locally on CPU (~35ms) to qualify commercial viability.
           │
           ▼
[Phase 9: Diffusion & Compilation]
  └── Generates complete product dossiers, converts to Word (.docx), and compiles Master Report.
```

---

## 📂 Project Structure

```
.
├── RUN_PIPELINE.bat           # 1-click Windows desktop runner
├── main.py                    # Main pipeline CLI entry point (run-all, mine, extract, etc.)
├── md_to_word.py              # Standalone Markdown to styled Word (DOCX) converter
├── combine_dossiers.py        # Compiles individual dossiers into a single Master Word Report
├── run_ground_truth_benchmark.py # Automated 10-thread benchmark evaluation test
├── eval_ground_truth.csv      # 10 curated benchmark threads with human ground truth
│
├── src/
│   ├── ingestion/
│   │   └── reddit/reddit_miner.py      # Unbreakable zero-key Reddit RSS thread scraper
│   ├── intelligence/
│   │   └── extraction/pain_extractor.py# Canonical pain point extractor
│   ├── analysis/
│   │   ├── clustering/cluster.py       # Domain-specific clustering engine
│   │   └── opportunities/idea_ranker.py# OpportunityEngine powered by Laya System 1 gate
│   ├── diffusion/
│   │   └── dossier/vault_exporter.py   # Synthesizes dossiers and triggers Word conversion
│   ├── orchestration/
│   │   ├── router/model_router.py      # Multi-tier router (Laya Local, Groq, Gemini)
│   │   └── budget/budget_manager.py    # Rate-limit and quota recovery
│   └── storage/
│       └── db.py                       # SQLite storage enforcing strict Pydantic schemas
│
├── data/
│   └── market_intelligence.db # Relational SQLite database
├── output/                    # Generated Master Reports and Dossiers (.docx & .md)
└── tests/                     # 100% green Pytest test suite
```

---

## 🛠️ Step-by-Step Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
pip install laya
```

### Step 2: Configure Environment Keys (`.env`)
Create a `.env` file in the root directory:
```ini
GROQ_API_KEY=your_free_groq_api_key_here
GEMINI_API_KEY=your_free_gemini_api_key_here
USE_LAYA=true
```
*(No Reddit API keys or Developer Accounts required! The miner uses our stealth RSS engine).*

### Step 3: Run Unit Tests
Verify all core components pass:
```bash
python -m pytest tests/
```
*(All 5 tests pass 100% green).*

---

## 📊 Run Ground Truth Benchmark
To verify pipeline extraction and decision gating against our 10-thread human ground truth baseline:
```bash
python run_ground_truth_benchmark.py
```
*(Yields 90.0% extraction entity alignment and outputs qualified venture candidates).*

---

## 📄 Standalone Word Converter Tool
To convert *any* markdown file into an executive Word document anytime:
```bash
python md_to_word.py path/to/file.md [optional_output.docx]
```
