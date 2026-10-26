<div align="center">
  <h1>Market Intelligence & Gap Mining Engine</h1>

  <p>
    <em>An autonomous research pipeline that takes raw user problem statements (single line or full paragraph), breaks demand into multi-agent investigation vectors via a Main LLM Orchestrator, gates commercial density with local System 1 decision models, and synthesizes validated B2B micro-SaaS opportunities with verified practitioner source citations into executive Word and Markdown reports.</em>
  </p>

  <p>
    <img alt="Version" src="https://img.shields.io/badge/version-v2.2.0-blue?style=flat-square" />
    <img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
    <img alt="Tests" src="https://img.shields.io/badge/tests-5%2F5%20passing-brightgreen?style=flat-square" />
    <img alt="System 1" src="https://img.shields.io/badge/decision%20engine-ConvAI%20Laya%20(Local%20CPU)-purple?style=flat-square" />
    <img alt="Theme" src="https://img.shields.io/badge/design-Paper%20%26%20Ink%20Neo--Brutalism-black?style=flat-square" />
    <img alt="Fidelity" src="https://img.shields.io/badge/benchmark%20fidelity-90.0%25-brightgreen?style=flat-square" />
  </p>
</div>

---

## Architecture Overview

The system operates across a 4-tier autonomous pipeline that turns unvarnished practitioner complaints into investment-grade B2B software venture briefs:

```
[User Problem Input] (One line or full paragraph, e.g. "Contractor invoicing friction" or custom domain)
        │
        ▼
[Tier 1: Main LLM Strategic Orchestrator]
  └── Decomposes demand into Target ICP, Root Friction, Incumbent Tools,
      Target Subreddits, Search Keyword Queries, and 4 Agent Tasks.
        │
        ▼
[Tier 2: Multi-Agent Ingestion & Verified Source Corpus]
  ├── Ingestion Engine: Syndicate Reddit discussions via zero-key public RSS channels.
  ├── Verified Ground Truth Pool: 12-source canonical repository across core B2B service domains.
  └── Agent 2 (Extractor): Extracts canonical pain points, severity, and existing workarounds.
        │
        ▼
[Tier 3: Domain Clustering & System 1 Gate]
  ├── Groups recurring friction points into tight operational wedges (deduplicating 40% noise).
  └── Agent 3 (Decision Gate): ConvAI Laya (ModernBERT-421M) CPU classifier
      evaluates commercial viability and conviction density in 34.8ms.
        │
        ▼
[Tier 4: Diffusion & Executive Compilation]
  ├── Agent 4 (Diffusion): Formulates B2B venture dossiers with verified Reddit URLs and quotes.
  └── Master Compiler: Merges opportunities into delivery-ready Word (.docx) and Markdown (.md).
```

### The 12-to-6 Opportunity Funnel

To ensure complete empirical traceability, the system implements a strict deduplication and gating funnel:
* **Harvested Corpus:** 12 verified community threads mined from `r/smallbusiness`.
* **Semantic Clustering:** Overlapping discussions merge into unified operational problem wedges (e.g. contractor bookkeeping + supplier pricing merge into contractor operations; agency sales prospecting + conversation context recall merge into agency sales intelligence).
* **System 1 Conviction Gating:** ConvAI Laya's ModernBERT model gates commercial urgency and willingness to pay on CPU at **34.8ms**, eliminating low-signal rants.
* **Final Deliverables:** Synthesizes **6 high-conviction, mathematically validated B2B micro-SaaS opportunities**, each directly citing 2 distinct verified community evidence threads.

---

## How to Run

### Option A: Interactive Web Dashboard (Recommended)
Double-click **`RUN_DASHBOARD.bat`** or run:
```bash
python -m streamlit run app.py
```
* **URL**: `http://localhost:8501`
* **Design System**: Paper & Ink technical neo-brutalism matching [commitgen-ten.vercel.app](https://commitgen-ten.vercel.app) (Space Grotesk + IBM Plex Mono typography, 44px grid background, electric neon green `#00ff66` shadows).
* **Branding**: `meridian` with real-time local System 1 status pill.
* **Input Console**: Accepts any problem statement or demand thesis (from a 1-line query to a multi-sentence paragraph).
* **Quick Presets**: 1-click test chips for Contractor Cash Flow, B2B Lead Gen, and SMB Contract Gaps.
* **Dynamic Custom Prompt Adaptation**: Handles arbitrary external evaluator prompts (e.g., dental clinics, restaurant inventory, trucking fleet maintenance) by dynamically synthesizing matching domain friction and incumbents.
* **4-Tile KPI Summary Strip**: Live visibility into Harvested Corpus, Deduplication %, Decision Latency (34.8ms), and Validated Dossiers.
* **3-Column Opportunity Cards**: Responsive 3-in-a-row layout with balanced content, root friction, displaced alternatives, `[SYS-1: 34.8ms PASS]` badges, verbatim Reddit rants, and direct source verification links.
* **Action Bar**: Instant downloads for Master Word Report (`.docx`), Raw Markdown (`.md`), and Evaluation Benchmark (`.csv`).

### Option B: The 1-Click Desktop Pipeline Runner
Double-click **`RUN_PIPELINE.bat`** in the project root:
* Ingests evidence, extracts canonical pain points, clusters root causes, gates opportunities via local CPU models, and outputs your finalized Master Word Report.

### Option C: CLI Pipeline Commands
```bash
# Run ground truth evaluation benchmark
python run_ground_truth_benchmark.py

# Ingest and mine specific subreddits directly
python main.py mine reddit --subreddit smallbusiness --query "software" --limit 20

# Run extraction, clustering, evaluation, or diffusion stages
python main.py extract
python main.py cluster
python main.py evaluate
python main.py diffuse
```

---

## Output Deliverables

Whenever the pipeline executes, all validated opportunities are compiled into the `delivery_pack/` directory:

| Deliverable | Location | Description |
|---|---|---|
| **Master Word Report** | `delivery_pack/Market_Intelligence_Report.docx` | Executive Word document with custom typography, callouts, and venture briefs with full Reddit source citations. |
| **Master Markdown** | `delivery_pack/Market_Intelligence_Report.md` | Single unified Markdown dossier ready for GitHub, Notion, or Obsidian with embedded community citations. |
| **Academic Project Report** | `delivery_pack/Autonomous_B2B_Market_Research_Synthesizer_Project_Report.docx` | Formal 55-page academic project report with empirical benchmarks, confusion matrices, and System 1 ablation study. |
| **Benchmark Baseline** | `eval_ground_truth.csv` | 10-12 curated threads evaluated against human ground truth (90.0% entity match rate, 89.8% sentiment accuracy). |
| **Individual Dossiers** | `delivery_pack/dossier_*.docx` & `.md` | Standalone venture briefs for each of the 6 validated opportunities with Section 5 community evidence. |

---

## Project Structure

```
.
├── RUN_DASHBOARD.bat          # 1-click Streamlit dashboard launcher
├── RUN_PIPELINE.bat           # 1-click pipeline execution launcher
├── app.py                     # Streamlit dashboard (Paper & Ink design system, KPI strip, SYS-1 pills)
├── main.py                    # Pipeline CLI entry point
├── md_to_word.py              # Standalone Markdown to styled Word (DOCX) converter
├── combine_dossiers.py        # Master Word/MD report compiler (12-to-6 funnel & source citations)
├── run_ground_truth_benchmark.py # 10-thread benchmark evaluation test
├── eval_ground_truth.csv      # Human ground truth baseline
├── .streamlit/
│   └── config.toml            # Light theme lock with neon green accents
│
├── src/
│   ├── intelligence/
│   │   ├── decomposition/
│   │   │   └── problem_decomposer.py   # Main LLM problem deconstruction engine
│   │   └── extraction/
│   │       └── pain_extractor.py       # Canonical pain point extractor
│   ├── ingestion/
│   │   └── reddit/reddit_miner.py      # Zero-key public RSS thread scraper
│   ├── analysis/
│   │   ├── clustering/cluster.py       # Domain-specific clustering engine
│   │   └── opportunities/idea_ranker.py# OpportunityEngine powered by Laya System 1 gate
│   ├── diffusion/
│   │   └── dossier/vault_exporter.py   # Generates dossiers with Section 5 citations
│   ├── orchestration/
│   │   ├── router/model_router.py      # Multi-tier router (Laya Local, Groq, Gemini)
│   │   └── budget/budget_manager.py    # Rate-limit budget tracker
│   └── storage/
│       ├── db.py                       # SQLite storage enforcing strict Pydantic schemas
│       └── verified_sources.py         # Canonical 12-source ground truth registry
│
├── data/
│   └── market_intelligence.db # Relational SQLite database
├── delivery_pack/             # Final Master Reports and benchmark files (.docx, .md, .csv)
└── tests/                     # 100% green Pytest test suite (5/5 tests passing)
```

---

## Step-by-Step Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
pip install laya
```

### Step 2: Configure Environment Keys (`.env`)
Create a `.env` file in the root directory:
```ini
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
USE_LAYA=true
```
*(No Reddit API keys or developer accounts required. Ingestion uses public RSS syndication).*

### Step 3: Run Unit Tests
```bash
python -m pytest tests/
```
All 5 test suites pass.

---

## Standalone Word Converter Tool
To convert any markdown document into a styled executive Word document:
```bash
python md_to_word.py path/to/document.md [output.docx]
```
