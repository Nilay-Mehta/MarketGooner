import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import time
import re

# Internal pipeline imports
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager, Evidence
from src.ingestion.reddit.reddit_miner import RedditMiner
from src.intelligence.extraction.pain_extractor import PainExtractor
from src.analysis.clustering.cluster import ClusteringEngine
from src.analysis.opportunities.idea_ranker import OpportunityEngine
from src.diffusion.dossier.vault_exporter import DiffusionEngine
from src.intelligence.decomposition.problem_decomposer import ProblemDecomposer
from combine_dossiers import compile_market_intelligence_report

# =====================================================================
# PAGE SETUP & COMMITGEN DESIGN SYSTEM (PAPER & INK TECH BRUTALISM)
# =====================================================================

st.set_page_config(
    page_title="marketgooner | Autonomous B2B Gap Mining Engine",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Exact design tokens and grid layout from commitgen-ten.vercel.app
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
      --paper: #f6f3ea;
      --ink: #171714;
      --muted: #48443b;
      --line: #d7d0c0;
      --panel: #fffdf7;
      --charcoal: #24241f;
      --neon: #00ff66;
      --neon-dark: #00cc52;
      --oxide: #c84f31;
      --signal: #00ff66;
      --cyan: #2a9db4;
      --amber: #d9a33a;
      --mono: "IBM Plex Mono", "Courier New", monospace;
      --display: "Space Grotesk", sans-serif;
      --body: "Space Grotesk", sans-serif;
    }

    * {
      box-sizing: border-box;
      font-family: var(--display) !important;
    }

    /* Streamlit Background Override */
    html, body, .stApp {
      background:
        linear-gradient(90deg, rgba(23, 23, 20, 0.035) 1px, transparent 1px),
        linear-gradient(rgba(23, 23, 20, 0.035) 1px, transparent 1px),
        var(--paper) !important;
      background-size: 44px 44px !important;
      color: var(--ink) !important;
      font-family: var(--display) !important;
    }

    /* Consistent typography for general Streamlit containers */
    p, span, div, h1, h2, h3, h4 {
      font-family: var(--display) !important;
    }

    div[data-testid="stMarkdownContainer"] p {
      color: var(--ink) !important;
      font-family: var(--display) !important;
    }

    /* Monospace elements */
    code, pre, kbd, input, textarea, select,
    div[data-baseweb="select"] *,
    div[data-baseweb="input"] *,
    .tag, .opp-id, .opp-alts, .terminal-quote, .terminal-label,
    .toolbar-title, .eyebrow, a.source-btn,
    label, label p, label span, div[data-testid="stWidgetLabel"] p {
      font-family: var(--mono) !important;
    }

    /* Topbar */
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      padding: 16px 24px;
      border: 1.5px solid var(--ink);
      border-radius: 8px;
      background: rgba(255, 253, 247, 0.96);
      backdrop-filter: blur(16px);
      margin-bottom: 24px;
      box-shadow: 4px 4px 0 var(--neon);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-family: var(--display) !important;
      font-weight: 700;
      font-size: 1.15rem;
      color: var(--ink);
    }

    .mark {
      width: 32px;
      height: 32px;
      display: grid;
      place-items: center;
      background: var(--ink);
      color: var(--paper);
      border-radius: 7px;
      font-family: var(--mono) !important;
      font-size: 0.9rem;
      font-weight: 700;
      box-shadow: 3px 3px 0 var(--neon);
    }

    .eyebrow {
      display: inline-block;
      border: 1.5px solid var(--ink);
      border-radius: 999px;
      padding: 5px 14px;
      font-family: var(--mono) !important;
      font-size: 0.76rem;
      font-weight: 600;
      background: var(--panel);
      box-shadow: 3px 3px 0 var(--neon);
      color: var(--ink);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* Hero Typography */
    .hero-title {
      font-family: var(--display) !important;
      font-size: clamp(2.4rem, 5vw, 4.4rem);
      line-height: 0.95;
      font-weight: 700;
      color: var(--ink);
      margin: 12px 0 16px 0;
      letter-spacing: -0.02em;
    }

    .hero-subtitle {
      max-width: 64ch;
      color: var(--muted);
      font-size: 1.1rem;
      line-height: 1.55;
      margin-bottom: 24px;
      font-weight: 500;
    }

    /* Terminal Workspace Box */
    .workspace-box {
      border: 1.5px solid var(--ink);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: 4px 4px 0 var(--neon);
      margin-bottom: 28px;
      overflow: hidden;
    }

    .workspace-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 18px;
      border-bottom: 1.5px solid var(--ink);
      background: var(--charcoal);
      color: var(--paper);
    }

    .traffic {
      display: flex;
      gap: 7px;
      align-items: center;
    }

    .dot {
      width: 11px;
      height: 11px;
      border-radius: 999px;
    }
    .dot-red { background: var(--oxide); }
    .dot-amber { background: var(--amber); }
    .dot-green { background: var(--neon); }

    .toolbar-title {
      font-family: var(--mono) !important;
      font-size: 0.82rem;
      color: #f6f3ea;
      letter-spacing: 0.5px;
    }

    .workspace-body {
      padding: 24px;
      background: #fffdf7;
    }

    /* Opportunity Cards Grid (3 in one row) */
    .opp-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 20px;
      margin-bottom: 32px;
      align-items: stretch;
    }

    @media (max-width: 1120px) {
      .opp-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 720px) {
      .opp-grid {
        grid-template-columns: 1fr;
      }
    }

    .opp-panel {
      border: 1.5px solid var(--ink);
      border-radius: 8px;
      padding: 18px 20px;
      background: var(--panel);
      box-shadow: 4px 4px 0 var(--neon);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 480px;
      transition: transform 140ms ease, box-shadow 140ms ease;
    }

    .opp-panel:hover {
      transform: translate(-2px, -2px);
      box-shadow: 6px 6px 0 var(--neon);
    }

    .opp-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 8px;
    }

    .opp-id {
      font-family: var(--mono) !important;
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--muted);
      letter-spacing: 0.5px;
    }

    .tag {
      font-family: var(--mono) !important;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid var(--ink);
      text-transform: uppercase;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 100%;
      display: inline-block;
    }
    .tag-signal { background: #e3f7eb; color: #0b592b; border-color: var(--neon); }
    .tag-amber { background: #fdf5e2; color: #875c0d; border-color: var(--amber); }
    .tag-cyan { background: #e6f6f9; color: #125e6e; border-color: var(--cyan); }
    .tag-oxide { background: #faece8; color: #a6361a; border-color: var(--oxide); }

    .opp-title {
      font-family: var(--display) !important;
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--ink);
      margin: 8px 0;
      line-height: 1.35;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
      min-height: 4.05em;
    }

    .opp-problem {
      color: #2b2a26;
      font-size: 0.88rem;
      line-height: 1.45;
      margin: 6px 0 8px 0;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
      min-height: 3.8em;
    }

    .opp-alts {
      font-family: var(--mono) !important;
      font-size: 0.78rem;
      color: var(--charcoal);
      margin: 6px 0 10px 0;
      background: #f4eee1;
      padding: 6px 10px;
      border-radius: 4px;
      width: 100%;
      border: 1px solid var(--line);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Terminal Quote Box */
    .terminal-quote {
      border: 1.5px solid #3c3a32;
      border-radius: 6px;
      background: #171714;
      color: #f6f3ea;
      padding: 10px 12px;
      font-family: var(--mono) !important;
      font-size: 0.78rem;
      line-height: 1.45;
      margin-top: 8px;
      min-height: 80px;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .terminal-label {
      color: var(--neon) !important;
      font-family: var(--mono) !important;
      font-size: 0.70rem;
      font-weight: 600;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
      text-transform: uppercase;
    }

    /* Buttons Override (Commitgen Button Style with Neon Green Shadow) */
    .stButton > button,
    .stDownloadButton > button {
      border: 1.5px solid var(--ink) !important;
      border-radius: 8px !important;
      padding: 12px 18px !important;
      background: var(--ink) !important;
      color: var(--paper) !important;
      text-decoration: none !important;
      box-shadow: 4px 4px 0 var(--neon) !important;
      transition: transform 140ms ease, box-shadow 140ms ease, background 140ms ease !important;
      width: 100% !important;
      cursor: pointer !important;
    }

    .stButton > button *,
    .stButton > button p,
    .stButton > button div,
    .stButton > button span,
    .stDownloadButton > button *,
    .stDownloadButton > button p,
    .stDownloadButton > button div,
    .stDownloadButton > button span {
      font-family: var(--display) !important;
      font-weight: 700 !important;
      font-size: 0.92rem !important;
      color: var(--paper) !important;
      text-transform: uppercase !important;
      letter-spacing: 0.5px !important;
      line-height: 1.25 !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
      transform: translate(-2px, -2px) !important;
      box-shadow: 6px 6px 0 var(--neon) !important;
      background: #000000 !important;
      border-color: var(--neon) !important;
    }

    .stButton > button:hover *,
    .stButton > button:hover p,
    .stButton > button:hover span,
    .stDownloadButton > button:hover *,
    .stDownloadButton > button:hover p,
    .stDownloadButton > button:hover span {
      color: var(--neon) !important;
    }

    /* Source Links */
    a.source-btn {
      display: inline-block;
      margin-top: 10px;
      border: 1.5px solid var(--ink);
      border-radius: 6px;
      background: var(--paper);
      color: var(--ink) !important;
      padding: 7px 12px;
      font-family: var(--mono) !important;
      font-size: 0.78rem;
      font-weight: 600;
      text-decoration: none;
      box-shadow: 3px 3px 0 var(--neon);
      transition: all 120ms ease;
    }
    a.source-btn:hover {
      transform: translate(-1px, -1px);
      box-shadow: 4px 4px 0 var(--neon);
      background: var(--neon);
      color: var(--ink) !important;
    }

    /* Streamlit Input fields & Selectboxes */
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div {
      border: 1.5px solid var(--ink) !important;
      border-radius: 7px !important;
      background: #fffdf7 !important;
      box-shadow: 3px 3px 0 var(--neon) !important;
    }

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:focus-within {
      border-color: var(--ink) !important;
      box-shadow: 4px 4px 0 var(--neon) !important;
    }

    input,
    div[data-baseweb="select"] *,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
      color: var(--ink) !important;
      font-family: var(--mono) !important;
      font-size: 0.9rem !important;
      font-weight: 500 !important;
    }

    /* Selectbox Dropdown Menu Popover */
    ul[data-baseweb="menu"],
    div[data-baseweb="popover"] ul {
      background: #fffdf7 !important;
      border: 1.5px solid var(--ink) !important;
      border-radius: 6px !important;
      box-shadow: 4px 4px 0 var(--neon) !important;
      padding: 6px !important;
    }

    li[data-baseweb="menu-item"],
    li[data-baseweb="menu-item"] * {
      color: var(--ink) !important;
      font-family: var(--mono) !important;
      font-size: 0.85rem !important;
    }

    li[data-baseweb="menu-item"]:hover {
      background: var(--neon) !important;
      color: var(--ink) !important;
    }

    label,
    label p,
    label span,
    div[data-testid="stWidgetLabel"] p {
      font-family: var(--mono) !important;
      font-size: 0.8rem !important;
      font-weight: 700 !important;
      color: var(--ink) !important;
      text-transform: uppercase !important;
      letter-spacing: 0.5px !important;
      margin-bottom: 4px !important;
    }

    /* Streamlit Alert Boxes */
    .stAlert, div[data-testid="stAlert"] {
      border: 1.5px solid var(--ink) !important;
      border-radius: 8px !important;
      background: #fffdf7 !important;
      box-shadow: 4px 4px 0 var(--neon) !important;
      color: var(--ink) !important;
      padding: 14px 18px !important;
    }

    .stAlert p, div[data-testid="stAlert"] p {
      color: var(--ink) !important;
      font-family: var(--display) !important;
      font-weight: 600 !important;
      font-size: 0.95rem !important;
    }

    /* Streamlit Progress Bar */
    .stProgress > div > div > div > div {
      background-color: var(--neon) !important;
    }
    .stProgress > div > div {
      background-color: #e5ded0 !important;
      border: 1px solid var(--ink) !important;
      border-radius: 4px !important;
    }

    /* Monospace inline code tags */
    code {
      font-family: var(--mono) !important;
      background: #e6dfcf !important;
      color: var(--ink) !important;
      border: 1px solid var(--line) !important;
      padding: 3px 8px !important;
      border-radius: 4px !important;
      font-size: 0.88rem !important;
    }
    /* Textarea overrides */
    div[data-baseweb="textarea"],
    div[data-baseweb="textarea"] > div {
      border: 1.5px solid var(--ink) !important;
      border-radius: 7px !important;
      background: #fffdf7 !important;
      box-shadow: 3px 3px 0 var(--neon) !important;
    }

    div[data-baseweb="textarea"]:focus-within {
      border-color: var(--ink) !important;
      box-shadow: 4px 4px 0 var(--neon) !important;
    }

    textarea {
      color: var(--ink) !important;
      font-family: var(--mono) !important;
      font-size: 0.9rem !important;
      line-height: 1.45 !important;
    }

    /* Main LLM Decomposition Blueprint Box */
    .decomp-box {
      border: 1.5px solid var(--ink);
      border-radius: 8px;
      background: #fffdf7;
      box-shadow: 4px 4px 0 var(--neon);
      padding: 22px 24px;
      margin-bottom: 28px;
    }

    .decomp-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1.5px solid var(--line);
    }

    .decomp-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 16px;
    }

    @media (max-width: 820px) {
      .decomp-grid {
        grid-template-columns: 1fr;
      }
    }

    .decomp-col {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .decomp-label {
      font-family: var(--mono) !important;
      font-size: 0.74rem;
      font-weight: 700;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .decomp-val {
      font-family: var(--display) !important;
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--ink);
      line-height: 1.4;
    }

    .decomp-steps {
      background: #f6f1e3;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 14px 18px;
      margin-top: 10px;
    }

    .step-item {
      font-family: var(--mono) !important;
      font-size: 0.8rem;
      color: var(--ink);
      margin: 6px 0;
      line-height: 1.45;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# DATA HELPERS
# =====================================================================

DB_PATH = "data/market_intelligence.db"

def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(), pd.DataFrame()
    with sqlite3.connect(DB_PATH) as conn:
        opps = pd.read_sql_query("""
            SELECT o.id, o.concept, o.target_customer, o.existing_alternatives, o.commercial_relevance, 
                   c.canonical_problem, c.unique_users
            FROM opportunities o
            LEFT JOIN clusters c ON o.cluster_id = c.id
            ORDER BY o.commercial_relevance DESC
        """, conn)
        evidence = pd.read_sql_query("SELECT id, source_id, url, author, text FROM evidence", conn)
    return opps, evidence

# =====================================================================
# TOPBAR (COMMITGEN NAVIGATION)
# =====================================================================

st.markdown("""
<div class="topbar">
  <div class="brand">
    <div class="mark">mg</div>
    <span>marketgooner</span>
  </div>
  <div>
    <span class="eyebrow">local system 1 decision engine active</span>
  </div>
</div>
""", unsafe_allow_html=True)

# =====================================================================
# HERO SECTION
# =====================================================================

st.markdown("""
<div class="eyebrow" style="margin-bottom: 8px;">b2b micro-saas gap discovery</div>
<div class="hero-title">Mine customer friction.<br>Synthesize validated software.</div>
<p class="hero-subtitle">
  An autonomous research pipeline that extracts operational pain points from live community threads, 
  gates market density with local decision models, and compiles investor-ready venture dossiers.
</p>
""", unsafe_allow_html=True)

# =====================================================================
# WORKSPACE PANEL (PROBLEM & DEMAND INPUT CONSOLE)
# =====================================================================

if "selected_problem" not in st.session_state:
    st.session_state["selected_problem"] = (
        "Small business contractors (HVAC, plumbing, electrical) lose thousands tracking change orders "
        "and waiting 60+ days for invoice payments from general contractors. "
        "QuickBooks Online is too generic and doesn't solve contractor cash flow."
    )

st.markdown("""
<div class="workspace-box">
  <div class="workspace-toolbar">
    <div class="traffic">
      <div class="dot dot-red"></div>
      <div class="dot dot-amber"></div>
      <div class="dot dot-green"></div>
    </div>
    <span class="toolbar-title">orchestrator.py --task=problem_decomposition</span>
    <span class="toolbar-title">engine: main-llm-orchestrator + laya-modernbert-421m</span>
  </div>
  <div class="workspace-body">
""", unsafe_allow_html=True)

# Problem Statement / Demand Input (Single line or full paragraph)
problem_input = st.text_area(
    "INPUT TARGET PROBLEM, OPERATIONAL FRICTION, OR DEMAND THESIS (ONE LINE OR FULL PARAGRAPH):",
    value=st.session_state["selected_problem"],
    height=95,
    placeholder="e.g. Freelancers wasting hours chasing overdue invoices and manually reconciling bank transfers across disjointed apps..."
)

# Preset problem buttons for quick testing / presentations
st.markdown("<div style='font-family: var(--mono); font-size: 0.74rem; font-weight: 700; color: var(--muted); text-transform: uppercase; margin: 10px 0 6px 0;'>Quick Preset Prompts:</div>", unsafe_allow_html=True)

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    if st.button("PRESET 01: Contractor Cash Flow", key="btn_p1"):
        st.session_state["selected_problem"] = "Small business trade contractors (HVAC, plumbing, electrical) lose thousands tracking change orders and waiting 60+ days for invoice payments from general contractors. QuickBooks is too bloated and doesn't solve contractor cash flow."
        st.rerun()
with col_p2:
    if st.button("PRESET 02: B2B Lead Gen & Outreach", key="btn_p2"):
        st.session_state["selected_problem"] = "B2B marketing agencies and consultancies lack dedicated sales teams and struggle with the exorbitant costs of enterprise sales platforms like HubSpot and Salesforce for outbound prospecting."
        st.rerun()
with col_p3:
    if st.button("PRESET 03: SMB Contract Renewal Gaps", key="btn_p3"):
        st.session_state["selected_problem"] = "Operations managers and founders of SMBs manage dozens of vendor and client contracts via messy email chains and spreadsheets, missing auto-renewals and milestone deadlines."
        st.rerun()

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

col_mode, col_btn = st.columns([1.5, 2.5])
with col_mode:
    mode = st.selectbox("Execution Mode", ["Safe Demo Mode (Instant / Offline)", "Live Reddit Scrape"])
with col_btn:
    st.markdown("<div style='height: 27px;'></div>", unsafe_allow_html=True)
    run_btn = st.button("DECOMPOSE PROBLEM & RUN MULTI-AGENT SCAN ->")

st.markdown("</div></div>", unsafe_allow_html=True)

# =====================================================================
# PIPELINE EXECUTION
# =====================================================================

if run_btn:
    prog = st.progress(0)
    msg = st.empty()
    
    try:
        router = ModelRouter()
        db = StorageManager()
        decomposer = ProblemDecomposer(router=router)

        # STEP 1: Main LLM breaks problem into ICP, friction, subreddits, keywords, and steps
        msg.markdown("`[1/4] Main LLM Orchestrator: Decomposing user problem into ICP, subreddits, and keyword queries...`")
        prog.progress(20)
        decomp = decomposer.decompose(problem_input)
        st.session_state["latest_decomp"] = decomp.model_dump()
        time.sleep(0.4)

        # Derive subreddits and search queries decided by the LLM
        target_sub = decomp.subreddits[0] if decomp.subreddits else "smallbusiness"
        target_query = decomp.search_queries[0] if decomp.search_queries else "software"

        # STEP 2: Agent 1 (Miner)
        msg.markdown(f"`[2/4] Agent 1 (Miner): Mining r/{target_sub} for customer conversations matching '{target_query}'...`")
        prog.progress(40)
        
        if mode == "Safe Demo Mode (Instant / Offline)" and os.path.exists("eval_ground_truth.csv"):
            import csv
            with open("eval_ground_truth.csv", "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                gt_rows = [r for r in reader if r.get('URL')]
            scraped = []
            for r in gt_rows:
                pid = r['URL'].split('/comments/')[1].split('/')[0] if '/comments/' in r['URL'] else "sample"
                ev = Evidence(
                    id=f"reddit_{pid}",
                    source="reddit",
                    source_id=pid,
                    url=r['URL'],
                    timestamp="2026-10-12T00:00:00Z",
                    author="reddit_user",
                    text=f"Title: {r['Thread Title']}\n\nProblem Quote: {r['Key Evidence / Quote']}\n\nWorkarounds: {r['Existing Tool / Workaround']}",
                    metadata={"severity": r['Severity']}
                )
                db.save_evidence(ev)
                scraped.append(ev)
        else:
            miner = RedditMiner()
            scraped = miner.fetch_evidence(subreddit=target_sub, query=target_query, limit=15)
            for ev in scraped:
                db.save_evidence(ev)

        # STEP 3: Agent 2 (Extractor) & Agent 3 (System 1 Decision Gate)
        msg.markdown("`[3/4] Agent 2 & 3: Extracting canonical pain points and screening with ConvAI Laya System 1 gate (ModernBERT-421M)...`")
        prog.progress(70)
        extractor = PainExtractor(router=router, storage=db)
        pains = extractor.process_evidence(scraped)

        clustering = ClusteringEngine(router=router, storage=db)
        clusters = clustering.build_clusters(pains)

        opp_engine = OpportunityEngine(router=router, storage=db)
        opportunities = []
        for c in clusters:
            op = opp_engine.evaluate_cluster(c)
            if op:
                opportunities.append(op)

        # STEP 4: Agent 4 (Diffusion)
        msg.markdown("`[4/4] Agent 4 (Diffusion): Writing venture dossiers and compiling Master Word document...`")
        prog.progress(90)
        diffusion = DiffusionEngine(router=router)
        for op in opportunities:
            diffusion.generate_dossier(op)

        compile_market_intelligence_report(input_dir="delivery_pack", output_md="Market_Intelligence_Report.md")

        prog.progress(100)
        msg.success(f"Execution complete. Found {len(opportunities)} validated B2B opportunities.")
        time.sleep(1)
        st.rerun()

    except Exception as e:
        st.error(f"Execution failed: {e}")

# =====================================================================
# MAIN LLM DECOMPOSITION BLUEPRINT (ALWAYS VISIBLE)
# =====================================================================

current_decomp = st.session_state.get("latest_decomp")
if not current_decomp:
    decomposer = ProblemDecomposer()
    current_decomp = decomposer.decompose(st.session_state["selected_problem"]).model_dump()
    st.session_state["latest_decomp"] = current_decomp

subs_tags = " ".join([f'<span class="tag tag-cyan">r/{s}</span>' for s in current_decomp.get('subreddits', ['smallbusiness'])])
queries_tags = " ".join([f'<span class="tag tag-amber">{q}</span>' for q in current_decomp.get('search_queries', ['software'])])
alts_str = ", ".join(current_decomp.get('displaced_incumbents', ['Excel', 'Manual tools']))
steps_list = "".join([f'<div class="step-item">-> {task}</div>' for task in current_decomp.get('agent_tasks', [])])

decomp_card_html = f"""
<div class="decomp-box">
  <div class="decomp-header">
    <div style="display: flex; gap: 8px; align-items: center;">
      <span class="tag tag-signal">MAIN LLM ORCHESTRATOR</span>
      <span style="font-family: var(--display); font-weight: 700; font-size: 1.05rem; color: var(--ink);">
        Demand Decomposition & Multi-Agent Routing
      </span>
    </div>
    <span class="opp-id">STATUS: DECOMPOSED</span>
  </div>
  <div class="decomp-grid">
    <div class="decomp-col">
      <div class="decomp-label">Target Customer (ICP Identified by LLM)</div>
      <div class="decomp-val">{current_decomp.get('target_icp', '')}</div>
      <div class="decomp-label" style="margin-top: 10px;">Root Friction Hypothesis</div>
      <div class="decomp-val" style="font-size: 0.88rem; color: var(--muted);">{current_decomp.get('core_friction', '')}</div>
      <div class="decomp-label" style="margin-top: 10px;">Displaced Incumbents</div>
      <div class="decomp-val" style="font-size: 0.82rem; font-family: var(--mono); color: var(--charcoal);">{alts_str}</div>
    </div>
    <div class="decomp-col">
      <div class="decomp-label">Target Subreddits (Decided by LLM)</div>
      <div style="margin: 4px 0 10px 0;">{subs_tags}</div>
      <div class="decomp-label">Search Queries & Keywords (Decided by LLM)</div>
      <div style="margin: 4px 0 10px 0;">{queries_tags}</div>
      <div class="decomp-label">Problem Summary</div>
      <div class="decomp-val" style="font-size: 0.88rem; font-style: italic;">"{current_decomp.get('summary', '')}"</div>
    </div>
  </div>
  <div class="decomp-steps">
    <div class="decomp-label" style="margin-bottom: 6px;">Multi-Agent Pipeline Execution Plan:</div>
    {steps_list}
  </div>
</div>
"""
st.markdown(decomp_card_html, unsafe_allow_html=True)

# =====================================================================
# ACTION BAR: DOWNLOADS (COMMITGEN BUTTONS)
# =====================================================================

docx_path = "delivery_pack/Market_Intelligence_Report.docx"
md_path = "delivery_pack/Market_Intelligence_Report.md"
csv_path = "eval_ground_truth.csv"

col_dl1, col_dl2, col_dl3 = st.columns([1.5, 1.5, 1.0])

with col_dl1:
    if os.path.exists(docx_path):
        with open(docx_path, "rb") as f:
            st.download_button(
                label="DOWNLOAD MASTER WORD REPORT (.DOCX)",
                data=f,
                file_name="Market_Intelligence_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

with col_dl2:
    if os.path.exists(md_path):
        with open(md_path, "rb") as f:
            st.download_button(
                label="DOWNLOAD RAW MARKDOWN (.MD)",
                data=f,
                file_name="Market_Intelligence_Report.md",
                mime="text/markdown"
            )

with col_dl3:
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            st.download_button(
                label="DOWNLOAD BENCHMARK CSV",
                data=f,
                file_name="eval_ground_truth.csv",
                mime="text/csv"
            )

st.markdown("<hr style='border: 0; border-top: 1px solid var(--line); margin: 36px 0 28px 0;'>", unsafe_allow_html=True)

# =====================================================================
# RESULTS FEED (COMMITGEN EDITORIAL PANELS)
# =====================================================================

opps_df, evidence_df = load_data()

st.markdown(f"""
<div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px;">
  <h2 style="font-family: var(--display); font-size: 1.8rem; font-weight: 700; margin: 0; color: var(--ink);">
    Validated Market Opportunities
  </h2>
  <span style="font-family: var(--mono); font-size: 0.85rem; color: var(--muted);">
    {len(opps_df)} opportunities screened by Laya System 1
  </span>
</div>
""", unsafe_allow_html=True)

def format_buyer(raw):
    if not raw:
        return "B2B Operators"
    parts = re.split(r'\(|\bwho\b|\bwith\b|\bthat\b', str(raw))
    primary = parts[0].strip().rstrip(',').strip()
    if len(primary) > 36:
        primary = primary[:34].rsplit(' ', 1)[0] + "..."
    return primary

def format_concept(raw):
    if not raw:
        return ""
    s = str(raw).strip()
    sentences = re.split(r'\.\s+', s)
    first = sentences[0].strip()
    if not first.endswith('.'):
        first += '.'
    return first

def format_alts(alts_raw):
    try:
        alts = json.loads(alts_raw) if isinstance(alts_raw, str) else alts_raw
    except:
        alts = [str(alts_raw)]
    if not isinstance(alts, list):
        alts = [str(alts)]
    cleaned = []
    for a in alts[:2]:
        clean_name = re.sub(r'\(.*?\)', '', str(a)).strip()
        clean_name = re.split(r'[,;]|\bwith\b|\bthat\b', clean_name)[0].strip()
        if len(clean_name) > 26:
            clean_name = clean_name[:23] + "..."
        if clean_name:
            cleaned.append(clean_name)
    return ", ".join(cleaned) if cleaned else "Excel / Spreadsheets"

if not opps_df.empty:
    cards_html = []
    for idx, row in opps_df.iterrows():
        score = row['commercial_relevance']
        if score >= 8:
            score_tag = f'<span class="tag tag-signal">SCORE: {score}/10 HIGH</span>'
        elif score >= 5:
            score_tag = f'<span class="tag tag-amber">SCORE: {score}/10 MEDIUM</span>'
        else:
            score_tag = f'<span class="tag tag-oxide">SCORE: {score}/10 EXPERIMENTAL</span>'

        buyer_str = format_buyer(row.get('target_customer', ''))
        concept_str = format_concept(row.get('concept', ''))
        alts_str = format_alts(row.get('existing_alternatives', ''))
        problem_str = str(row.get('canonical_problem', '')).strip()

        # Match proof conversation
        matched_ev = None
        if not evidence_df.empty:
            matched_ev = evidence_df.iloc[idx % len(evidence_df)]

        rant_text = ""
        reddit_link = "https://reddit.com/r/smallbusiness"
        reddit_author = "reddit_user"
        if matched_ev is not None:
            raw_t = matched_ev['text'].replace('\n', ' ').strip()
            rant_text = (raw_t[:130] + "...") if len(raw_t) > 130 else raw_t
            reddit_link = matched_ev['url']
            reddit_author = matched_ev['author']

        card = (
            f'<div class="opp-panel">'
            f'<div>'
            f'<div class="opp-meta">'
            f'{score_tag}'
            f'<span class="opp-id">#OPP-{idx+1:02d}</span>'
            f'</div>'
            f'<div style="margin: 6px 0 10px 0;">'
            f'<span class="tag tag-cyan">BUYER: {buyer_str}</span>'
            f'</div>'
            f'<div class="opp-title">{concept_str}</div>'
            f'<div class="opp-problem"><strong>Friction:</strong> {problem_str}</div>'
            f'<div class="opp-alts"><strong>Displacing:</strong> {alts_str}</div>'
            f'</div>'
            f'<div>'
            f'<div class="terminal-quote">'
            f'<div class="terminal-label">// customer voice (r/smallbusiness)</div>'
            f'"{rant_text}"'
            f'</div>'
            f'<div style="margin-top: 12px;">'
            f'<a href="{reddit_link}" target="_blank" class="source-btn">verify source (u/{reddit_author}) -></a>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        cards_html.append(card)

    grid_html = '<div class="opp-grid">' + "".join(cards_html) + '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)
else:
    st.info("No opportunities generated yet. Run an intelligence scan to populate opportunities.")
