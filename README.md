<div align="center">
  <img src="assets/logo.png" alt="Logo" width="250" />
  
  <h1>MarketGooner</h1>

  <p>
    <a href="https://github.com/Nilay-Mehta/MarketGooner"><strong>Website</strong></a> ·
    <a href="#"><strong>Discord</strong></a> ·
    <a href="#"><strong>Documentation</strong></a>
  </p>

  <p>
    <img alt="Version" src="https://img.shields.io/badge/version-v1.0.0-blue?style=flat-square" />
    <img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
  </p>
</div>

**MarketGooner** is an autonomous, 100% free-tier B2B market research and gap-mining engine. It is designed to mine customer friction from Reddit, Hacker News, GitHub, and community boards, and synthesize validated Micro-SaaS startup opportunities.

This repository contains two main components:
1. **The Intelligence Engine (`/project`)**: A Python-based CLI pipeline that scans data sources, extracts explicit pain points, clusters them using BERTopic, and synthetically ranks them for WTP (Willingness-to-Pay), Frequency, Feasibility, and search trends.
2. **The Intelligence Vault (`/Market_Intelligence_Vault`)**: A fully organized Obsidian vault containing playbooks, architectural blueprints, landing page kits, and deep market scan dossiers.

---

## Step-by-Step Setup Guide

Follow these instructions to set up the Python engine and the Obsidian vault locally.

### 1. Prerequisites
- **Python 3.10+**: Ensure Python is installed and accessible in your system PATH.
- **Git**: For version control.
- **Obsidian (Optional but Recommended)**: Download from [obsidian.md](https://obsidian.md) to browse the Markdown knowledge vault.

### 2. Clone the Repository
Open your terminal and clone the repository:
```bash
git clone https://github.com/Nilay-Mehta/MarketGooner.git
cd MarketGooner
```

### 3. Setup the Python Environment
It is highly recommended to use a virtual environment to isolate the project dependencies.

**On Windows:**
```powershell
# Navigate into the project folder
cd project

# Create the virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
cd project
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
With your virtual environment activated, install all required packages:
```bash
pip install -r requirements.txt
```
*(This will install requests, rich, dotenv, instructor, pydantic, bertopic, and other essential ML/scraping tools).*

### 5. Configure API Keys (100% Free Tier)
The intelligence engine relies on free LLM APIs (like Groq) to synthesize and score startup ideas.

1. Inside the `project` folder, copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` in a text editor and add your free API keys. You can get these for free:
   - **Groq API Key (Recommended - fastest & highest free limits)**: Get it at [console.groq.com](https://console.groq.com)
   - **Google Gemini API Key**: Get it at [aistudio.google.com](https://aistudio.google.com)
   - **GitHub PAT** *(Optional, for GitHub issue mining)*

---

## Running the Engine

The entire pipeline is driven by the `main.py` CLI script located in the `project/` directory.

### Interactive Mode (Easiest)
Run the script without any arguments to open the interactive menu:
```bash
python main.py
```
From here, you can choose to:
1. **Scan**: Scrape new raw discussions from Reddit, Hacker News, etc.
2. **Extract**: Use LLMs to pull explicit pain points and WTP signals from the raw data.
3. **Cluster**: Group similar pain points using semantic clustering (BERTopic/HDBSCAN).
4. **Rank**: Synthesize validated startup ideas from the clusters and rank them based on trend data and viability.
5. **View/Top**: Inspect the best generated ideas and their underlying citations.

### CLI Pipeline Mode
You can also run specific pipeline stages directly from the command line:
```bash
# 1. Scan a vertical (e.g. Amazon FBA)
python main.py scan

# 2. Extract pain points
python main.py extract

# 3. Cluster pain points (use --recluster to flush old data)
python main.py cluster --recluster

# 4. Rank and synthesize ideas
python main.py rank
```

---

## Using the Obsidian Vault

The `Market_Intelligence_Vault` folder is a complete knowledge base intended to be viewed in Obsidian.

1. Open the **Obsidian** app.
2. Click **"Open folder as vault"**.
3. Select the root folder (`MarketGooner`) or the `Market_Intelligence_Vault` directory.
4. You will instantly have access to formatted dossiers, architectural blueprints, go-to-market strategies, and execution playbooks with working internal links.

---

## Data & Privacy
- **Local SQLite Database**: All scraped data, pain points, and generated ideas are stored strictly locally in `project/data/intel.db`. No proprietary data is sent anywhere other than the stateless LLM API calls.
- **Git Ignore**: The local `.env` and `data/` directories are securely excluded from version control via `.gitignore`.
