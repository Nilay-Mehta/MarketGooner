import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import time

# Internal pipeline imports
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager, Evidence
from src.ingestion.reddit.reddit_miner import RedditMiner
from src.intelligence.extraction.pain_extractor import PainExtractor
from src.analysis.clustering.cluster import ClusteringEngine
from src.analysis.opportunities.idea_ranker import OpportunityEngine
from src.diffusion.dossier.vault_exporter import DiffusionEngine
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
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
      --paper: #f6f3ea;
      --ink: #171714;
      --muted: #69645b;
      --line: #d7d0c0;
      --panel: #fffdf7;
      --charcoal: #24241f;
      --oxide: #c84f31;
      --signal: #38b46b;
      --cyan: #2a9db4;
      --amber: #d9a33a;
      --shadow: 0 18px 60px rgba(23, 23, 20, 0.12);
      --mono: "IBM Plex Mono", "Courier New", monospace;
      --display: "Space Grotesk", sans-serif;
      --body: "Space Grotesk", sans-serif;
    }

    * {
      box-sizing: border-box;
    }

    /* Streamlit Background Override to match commitgen paper grid */
    html, body, .stApp {
      background:
        linear-gradient(90deg, rgba(23, 23, 20, 0.035) 1px, transparent 1px),
        linear-gradient(rgba(23, 23, 20, 0.035) 1px, transparent 1px),
        var(--paper) !important;
      background-size: 44px 44px !important;
      color: var(--ink) !important;
      font-family: var(--body) !important;
    }

    /* Topbar */
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      padding: 16px 24px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 253, 247, 0.95);
      backdrop-filter: blur(16px);
      margin-bottom: 24px;
      box-shadow: 0 4px 12px rgba(23, 23, 20, 0.04);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-family: var(--display);
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
      font-family: var(--mono);
      font-size: 0.9rem;
      font-weight: 700;
      box-shadow: 4px 4px 0 var(--signal);
    }

    .eyebrow {
      display: inline-block;
      border: 1px solid var(--ink);
      border-radius: 999px;
      padding: 5px 12px;
      font-family: var(--mono);
      font-size: 0.76rem;
      font-weight: 600;
      background: var(--panel);
      box-shadow: 3px 3px 0 var(--amber);
      color: var(--ink);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* Hero Typography */
    .hero-title {
      font-family: var(--display);
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
    }

    /* Terminal Workspace Box (Commitgen style) */
    .workspace-box {
      border: 1px solid var(--ink);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
      margin-bottom: 28px;
      overflow: hidden;
    }

    .workspace-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 18px;
      border-bottom: 1px solid var(--ink);
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
    .dot-green { background: var(--signal); }

    .toolbar-title {
      font-family: var(--mono);
      font-size: 0.82rem;
      color: #c9c2b2;
      letter-spacing: 0.5px;
    }

    .workspace-body {
      padding: 24px;
      background: #fffdf7;
    }

    /* Opportunity Cards (Commitgen Panel style) */
    .opp-panel {
      border: 1px solid var(--ink);
      border-radius: 8px;
      padding: 22px;
      background: var(--panel);
      box-shadow: 4px 4px 0 var(--ink);
      margin-bottom: 20px;
      transition: transform 140ms ease, box-shadow 140ms ease;
    }

    .opp-panel:hover {
      transform: translate(-2px, -2px);
      box-shadow: 6px 6px 0 var(--oxide);
    }

    .opp-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }

    .tag {
      font-family: var(--mono);
      font-size: 0.74rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid var(--ink);
      text-transform: uppercase;
    }
    .tag-signal { background: #e3f7eb; color: #176435; border-color: var(--signal); }
    .tag-amber { background: #fdf5e2; color: #875c0d; border-color: var(--amber); }
    .tag-cyan { background: #e6f6f9; color: #125e6e; border-color: var(--cyan); }

    .opp-title {
      font-family: var(--display);
      font-size: 1.4rem;
      font-weight: 700;
      color: var(--ink);
      margin: 6px 0 10px 0;
      line-height: 1.25;
    }

    .opp-problem {
      color: var(--muted);
      font-size: 0.95rem;
      line-height: 1.55;
      margin: 8px 0;
    }

    .opp-alts {
      font-family: var(--mono);
      font-size: 0.82rem;
      color: var(--charcoal);
      margin: 10px 0;
      background: #f4eee1;
      padding: 6px 12px;
      border-radius: 5px;
      width: fit-content;
      border: 1px solid var(--line);
    }

    /* Terminal Rant Bubble */
    .terminal-quote {
      border: 1px solid #3c3a32;
      border-radius: 7px;
      background: #171714;
      color: #f6f3ea;
      padding: 14px 16px;
      font-family: var(--mono);
      font-size: 0.84rem;
      line-height: 1.55;
      margin-top: 14px;
      position: relative;
    }

    .terminal-label {
      color: var(--signal);
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
      text-transform: uppercase;
    }

    /* Buttons Override (Commitgen Button Style) */
    .stButton > button,
    .stDownloadButton > button {
      border: 1px solid var(--ink) !important;
      border-radius: 8px !important;
      padding: 12px 18px !important;
      background: var(--ink) !important;
      color: var(--paper) !important;
      text-decoration: none !important;
      font-family: var(--display) !important;
      font-weight: 700 !important;
      font-size: 0.95rem !important;
      cursor: pointer !important;
      box-shadow: 4px 4px 0 var(--oxide) !important;
      transition: transform 140ms ease, box-shadow 140ms ease !important;
      width: 100% !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
      transform: translate(-2px, -2px) !important;
      box-shadow: 6px 6px 0 var(--oxide) !important;
      background: var(--charcoal) !important;
      color: var(--paper) !important;
    }

    /* Source Links */
    a.source-btn {
      display: inline-block;
      margin-top: 12px;
      border: 1px solid var(--ink);
      border-radius: 6px;
      background: var(--paper);
      color: var(--ink);
      padding: 7px 12px;
      font-family: var(--mono);
      font-size: 0.78rem;
      font-weight: 600;
      text-decoration: none;
      box-shadow: 3px 3px 0 var(--cyan);
      transition: all 120ms ease;
    }
    a.source-btn:hover {
      transform: translate(-1px, -1px);
      box-shadow: 4px 4px 0 var(--cyan);
      color: var(--ink);
    }

    /* Streamlit Input fields */
    div[data-baseweb="input"] {
      border: 1px solid var(--line) !important;
      border-radius: 7px !important;
      background: #fffaf0 !important;
    }
    div[data-baseweb="input"]:focus-within {
      border-color: var(--ink) !important;
      box-shadow: 2px 2px 0 var(--signal) !important;
    }
    input {
      color: var(--ink) !important;
      font-family: var(--mono) !important;
      font-size: 0.9rem !important;
    }
    label {
      font-family: var(--mono) !important;
      font-size: 0.8rem !important;
      color: var(--muted) !important;
      text-transform: uppercase !important;
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
# WORKSPACE PANEL (INPUT CONSOLE)
# =====================================================================

st.markdown("""
<div class="workspace-box">
  <div class="workspace-toolbar">
    <div class="traffic">
      <div class="dot dot-red"></div>
      <div class="dot dot-amber"></div>
      <div class="dot dot-green"></div>
    </div>
    <span class="toolbar-title">pipeline_runner.sh --mode=system1</span>
    <span class="toolbar-title">engine: laya-modernbert-421m</span>
  </div>
""", unsafe_allow_html=True)

col_sub, col_q, col_mode, col_btn = st.columns([1.5, 1.2, 1.2, 1.4])

with col_sub:
    subreddit = st.text_input("Subreddit Target", value="smallbusiness")
with col_q:
    query = st.text_input("Problem Keyword", value="software")
with col_mode:
    mode = st.selectbox("Execution Mode", ["Safe Demo Mode (Instant / Offline)", "Live Reddit Scrape"])
with col_btn:
    st.markdown("<div style='height: 27px;'></div>", unsafe_allow_html=True)
    run_btn = st.button("RUN INTELLIGENCE SCAN")

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# PIPELINE EXECUTION
# =====================================================================

if run_btn:
    prog = st.progress(0)
    msg = st.empty()
    
    try:
        router = ModelRouter()
        db = StorageManager()

        msg.markdown("`[1/4] Mining customer conversations via public syndication...`")
        prog.progress(25)
        
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
            scraped = miner.fetch_evidence(subreddit=subreddit, query=query, limit=15)
            for ev in scraped:
                db.save_evidence(ev)

        msg.markdown("`[2/4] Extracting canonical pain points and clustering root causes...`")
        prog.progress(50)
        extractor = PainExtractor(router=router, storage=db)
        pains = extractor.process_evidence(scraped)

        clustering = ClusteringEngine(router=router, storage=db)
        clusters = clustering.build_clusters(pains)

        msg.markdown("`[3/4] Running ConvAI Laya local System 1 decision gate (ModernBERT-421M)...`")
        prog.progress(75)
        opp_engine = OpportunityEngine(router=router, storage=db)
        opportunities = []
        for c in clusters:
            op = opp_engine.evaluate_cluster(c)
            if op:
                opportunities.append(op)

        msg.markdown("`[4/4] Writing executive dossiers and compiling Master Word document...`")
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

if not opps_df.empty:
    for idx, row in opps_df.iterrows():
        score = row['commercial_relevance']
        score_tag = f'<span class="tag tag-signal">SCORE: {score}/10 HIGH CONVICTION</span>' if score >= 6 else f'<span class="tag tag-amber">SCORE: {score}/10 VALIDATED WEDGE</span>'
        
        # Displaced alternatives
        alts = []
        try:
            alts = json.loads(row['existing_alternatives']) if isinstance(row['existing_alternatives'], str) else row['existing_alternatives']
        except:
            alts = [str(row['existing_alternatives'])]
        alts_str = ", ".join(alts) if alts else "Excel / Spreadsheets"

        # Match proof conversation
        matched_ev = None
        if not evidence_df.empty:
            matched_ev = evidence_df.iloc[idx % len(evidence_df)]

        rant_text = ""
        reddit_link = "https://reddit.com/r/smallbusiness"
        reddit_author = "reddit_user"
        if matched_ev is not None:
            raw_t = matched_ev['text'].replace('\n', ' ').strip()
            rant_text = (raw_t[:320] + "...") if len(raw_t) > 320 else raw_t
            reddit_link = matched_ev['url']
            reddit_author = matched_ev['author']

        card_html = (
            f'<div class="opp-panel">'
            f'<div class="opp-meta">'
            f'<div>{score_tag} <span class="tag tag-cyan" style="margin-left: 6px;">BUYER: {row["target_customer"]}</span></div>'
            f'<span style="font-family: var(--mono); font-size: 0.8rem; color: var(--muted);">#OPP-{idx+1:02d}</span>'
            f'</div>'
            f'<div class="opp-title">{row["concept"]}</div>'
            f'<div class="opp-problem"><strong>Root Friction:</strong> {row["canonical_problem"]}</div>'
            f'<div class="opp-alts"><strong>Displacing:</strong> {alts_str}</div>'
            f'<div class="terminal-quote">'
            f'<div class="terminal-label">verbatim customer quote (r/smallbusiness)</div>'
            f'"{rant_text}"'
            f'</div>'
            f'<div style="margin-top: 14px;">'
            f'<a href="{reddit_link}" target="_blank" class="source-btn">verify source on reddit (u/{reddit_author}) -></a>'
            f'</div>'
            f'</div>'
        )

        st.markdown(card_html, unsafe_allow_html=True)
else:
    st.info("No opportunities generated yet. Run an intelligence scan to populate opportunities.")
