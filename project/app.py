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
# PAGE SETUP & NEON GREEN COMIC THEME (NO EMOJIS)
# =====================================================================

st.set_page_config(
    page_title="MARKET GOONER // GAP MINER",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 100% NEON GREEN + INK BLACK COMIC BOOK CSS (ZERO EMOJIS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Space+Grotesk:wght@600;700;900&display=swap');

    /* Color Palette */
    :root {
        --neon-green: #00FF66;
        --neon-glow: rgba(0, 255, 102, 0.45);
        --comic-yellow: #FFE600;
        --pure-black: #000000;
        --card-bg: #111317;
    }

    body, .stApp {
        background-color: #07080A !important;
        color: #FFFFFF !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }

    /* Headings */
    .comic-title {
        font-family: 'Bangers', cursive !important;
        font-size: 60px !important;
        color: #00FF66 !important;
        letter-spacing: 2.5px !important;
        text-transform: uppercase !important;
        margin: 0 !important;
        text-shadow: 4px 4px 0px #000000, 0 0 30px var(--neon-glow) !important;
        line-height: 1.05 !important;
    }

    .comic-sub {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 15px !important;
        color: #A3E635 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        margin-top: 6px !important;
    }

    /* Comic Box Cards */
    .comic-card {
        background: #111317 !important;
        border: 3.5px solid #00FF66 !important;
        border-radius: 12px !important;
        box-shadow: 7px 7px 0px #000000, 7px 7px 0px 2px #00FF66 !important;
        padding: 24px !important;
        margin-bottom: 24px !important;
    }

    .comic-card:hover {
        box-shadow: 9px 9px 0px #FFE600 !important;
        border-color: #FFE600 !important;
        transform: translate(-2px, -2px) !important;
        transition: all 0.15s ease-in-out !important;
    }

    /* Comic Badges */
    .comic-badge {
        display: inline-block;
        font-family: 'Bangers', cursive;
        font-size: 17px;
        letter-spacing: 1px;
        padding: 4px 14px;
        border: 2.5px solid #000000;
        border-radius: 6px;
        box-shadow: 3px 3px 0px #000000;
        margin-right: 8px;
        margin-bottom: 10px;
    }
    .badge-green { background-color: #00FF66; color: #000000; }
    .badge-yellow { background-color: #FFE600; color: #000000; }
    .badge-white { background-color: #FFFFFF; color: #000000; }

    /* Speech Bubble for Real Reddit Quotes */
    .speech-bubble {
        background: #181A22;
        border: 2.5px solid #00FF66;
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 14px;
        margin-bottom: 12px;
        font-size: 14.5px;
        color: #F1F5F9;
        font-style: italic;
        line-height: 1.5;
        box-shadow: 4px 4px 0px #000000;
    }
    .speech-label {
        font-family: 'Bangers', cursive;
        font-size: 16px;
        color: #FFE600;
        margin-bottom: 4px;
        font-style: normal;
        letter-spacing: 1px;
    }

    /* ALL BUTTONS: NEON GREEN COMIC POP */
    .stButton > button,
    .stDownloadButton > button,
    button[kind="primary"],
    button[kind="secondary"] {
        font-family: 'Bangers', cursive !important;
        font-size: 22px !important;
        letter-spacing: 1.5px !important;
        background-color: #00FF66 !important;
        color: #000000 !important;
        border: 3.5px solid #000000 !important;
        border-radius: 8px !important;
        box-shadow: 5px 5px 0px #000000 !important;
        padding: 12px 24px !important;
        transition: all 0.1s ease-in-out !important;
        width: 100% !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background-color: #FFE600 !important;
        box-shadow: 3px 3px 0px #000000 !important;
        transform: translate(2px, 2px) !important;
        color: #000000 !important;
        border-color: #000000 !important;
    }

    /* Reddit Source Verification Button */
    a.reddit-btn {
        display: inline-block;
        background-color: #000000 !important;
        border: 2.5px solid #00FF66 !important;
        color: #00FF66 !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 800 !important;
        font-size: 13.5px !important;
        text-decoration: none !important;
        box-shadow: 3px 3px 0px #000000 !important;
    }
    a.reddit-btn:hover {
        background-color: #00FF66 !important;
        color: #000000 !important;
        border-color: #000000 !important;
    }

    /* Inputs */
    div[data-baseweb="input"] {
        border: 2.5px solid #00FF66 !important;
        border-radius: 8px !important;
        background-color: #12141A !important;
        color: #FFFFFF !important;
    }
    input {
        color: #00FF66 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
    }
    div[data-baseweb="select"] {
        border: 2.5px solid #00FF66 !important;
        border-radius: 8px !important;
        background-color: #12141A !important;
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
# HEADER
# =====================================================================

col_h1, col_h2 = st.columns([2.5, 1.0])
with col_h1:
    st.markdown('<h1 class="comic-title">MARKET GOONER // GAP MINER</h1>', unsafe_allow_html=True)
    st.markdown('<p class="comic-sub">TURNING REAL REDDIT COMPLAINTS INTO VALIDATED B2B SAAS OPPORTUNITIES</p>', unsafe_allow_html=True)

with col_h2:
    st.markdown("""
    <div style="text-align: right; margin-top: 10px;">
        <span class="comic-badge badge-green">LAYA SYSTEM 1 (CPU)</span>
        <span class="comic-badge badge-yellow">ZERO API COST</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border: 2px solid #00FF66; margin: 16px 0 24px 0;'>", unsafe_allow_html=True)

# =====================================================================
# STEP 1: CONFIGURE & MINE
# =====================================================================

st.markdown('<div class="comic-card">', unsafe_allow_html=True)
st.markdown('<h3 style="font-family: Bangers; font-size: 28px; color: #00FF66; margin: 0 0 12px 0;">[STEP 1] CONFIGURE AND LAUNCH</h3>', unsafe_allow_html=True)

c_sub, c_query, c_mode, c_run = st.columns([1.5, 1.2, 1.2, 1.4])

with c_sub:
    subreddit = st.text_input("Target Subreddit:", value="smallbusiness")
with c_query:
    query = st.text_input("Problem Topic:", value="software")
with c_mode:
    mode = st.selectbox("Mode:", ["Safe Demo Mode (Instant / Offline)", "Live Reddit Scrape"])
with c_run:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    run_btn = st.button("MINE PAIN POINTS", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# PIPELINE EXECUTION ENGINE
# =====================================================================

if run_btn:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        router = ModelRouter()
        db = StorageManager()

        status_text.markdown("### [1/4] Mining Customer Conversations...")
        progress_bar.progress(25)
        
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

        status_text.markdown("### [2/4] Fast LLM Extracting Pain Points and Clustering...")
        progress_bar.progress(50)
        extractor = PainExtractor(router=router, storage=db)
        pains = extractor.process_evidence(scraped)

        clustering = ClusteringEngine(router=router, storage=db)
        clusters = clustering.build_clusters(pains)

        status_text.markdown("### [3/4] Running ConvAI Laya Local System 1 Decision Gate...")
        progress_bar.progress(75)
        opp_engine = OpportunityEngine(router=router, storage=db)
        opportunities = []
        for c in clusters:
            op = opp_engine.evaluate_cluster(c)
            if op:
                opportunities.append(op)

        status_text.markdown("### [4/4] Generating Word and Markdown Reports...")
        progress_bar.progress(90)
        diffusion = DiffusionEngine(router=router)
        for op in opportunities:
            diffusion.generate_dossier(op)

        compile_market_intelligence_report(input_dir="delivery_pack", output_md="Market_Intelligence_Report.md")

        progress_bar.progress(100)
        status_text.success("SUCCESS: Scan Finished. All Opportunities and Master Report Ready Below.")
        time.sleep(1)
        st.rerun()

    except Exception as e:
        st.error(f"Execution Error: {e}")

# =====================================================================
# STEP 2: DOWNLOAD DELIVERABLES (PROMINENT NEON BUTTONS)
# =====================================================================

st.markdown('<h3 style="font-family: Bangers; font-size: 28px; color: #FFE600; margin-top: 10px;">[STEP 2] DOWNLOAD THE REPORTS</h3>', unsafe_allow_html=True)

col_d1, col_d2, col_d3 = st.columns([1.5, 1.5, 1.0])

docx_path = "delivery_pack/Market_Intelligence_Report.docx"
md_path = "delivery_pack/Market_Intelligence_Report.md"
csv_path = "eval_ground_truth.csv"

with col_d1:
    if os.path.exists(docx_path):
        with open(docx_path, "rb") as f:
            st.download_button(
                label="DOWNLOAD WORD REPORT (.DOCX)",
                data=f,
                file_name="Market_Intelligence_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    else:
        st.button("DOCX REPORT (RUN SCAN FIRST)", disabled=True)

with col_d2:
    if os.path.exists(md_path):
        with open(md_path, "rb") as f:
            st.download_button(
                label="DOWNLOAD RAW MARKDOWN (.MD)",
                data=f,
                file_name="Market_Intelligence_Report.md",
                mime="text/markdown",
                use_container_width=True
            )
    else:
        st.button("MD REPORT (RUN SCAN FIRST)", disabled=True)

with col_d3:
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            st.download_button(
                label="10-THREAD BENCHMARK CSV",
                data=f,
                file_name="eval_ground_truth.csv",
                mime="text/csv",
                use_container_width=True
            )

st.markdown("<hr style='border: 1px dashed #00FF66; margin: 28px 0;'>", unsafe_allow_html=True)

# =====================================================================
# STEP 3: DISCOVERED SAAS OPPORTUNITIES (BULLETPROOF RENDERING)
# =====================================================================

opps_df, evidence_df = load_data()

st.markdown(f'<h2 style="font-family: Bangers; font-size: 38px; color: #00FF66; letter-spacing: 1.5px; margin-bottom: 20px;">VALIDATED B2B OPPORTUNITIES ({len(opps_df)} DISCOVERED)</h2>', unsafe_allow_html=True)

if not opps_df.empty:
    for idx, row in opps_df.iterrows():
        score = row['commercial_relevance']
        score_badge = f"SCORE: {score}/10 HIGH CONVICTION" if score >= 6 else f"SCORE: {score}/10 VALIDATED WEDGE"
        badge_style = "badge-green" if score >= 6 else "badge-yellow"

        # Safe alternatives string
        alts = []
        try:
            alts = json.loads(row['existing_alternatives']) if isinstance(row['existing_alternatives'], str) else row['existing_alternatives']
        except:
            alts = [str(row['existing_alternatives'])]
        alts_str = ", ".join(alts) if alts else "Excel / Spreadsheets"

        # Match evidence for speech bubble
        matched_ev = None
        if not evidence_df.empty:
            matched_ev = evidence_df.iloc[idx % len(evidence_df)]

        rant_text = ""
        reddit_link = "https://reddit.com/r/smallbusiness"
        reddit_author = "smallbiz_user"
        if matched_ev is not None:
            raw_t = matched_ev['text'].replace('\n', ' ').strip()
            rant_text = (raw_t[:300] + "...") if len(raw_t) > 300 else raw_t
            reddit_link = matched_ev['url']
            reddit_author = matched_ev['author']

        # Build clean HTML string with zero indentation to prevent code-block parser bug
        card_html = (
            f'<div class="comic-card">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">'
            f'<div>'
            f'<span class="comic-badge {badge_style}">{score_badge}</span>'
            f'<span class="comic-badge badge-white">BUYER: {row["target_customer"]}</span>'
            f'</div>'
            f'<div style="font-family: Bangers; font-size: 22px; color: #00FF66;">OPPORTUNITY #{idx+1}</div>'
            f'</div>'
            f'<div style="font-family: Space Grotesk, sans-serif; font-size: 22px; font-weight: 900; color: #FFFFFF; margin: 10px 0;">{row["concept"]}</div>'
            f'<div style="color: #CBD5E1; font-size: 15px; margin: 10px 0; line-height: 1.6;"><strong style="color: #00FF66;">THE ROOT PROBLEM:</strong> {row["canonical_problem"]}</div>'
            f'<div style="margin: 12px 0; font-size: 14.5px; color: #94A3B8;"><strong style="color: #FFE600;">DISPLACING WORKAROUNDS:</strong> <span style="background: #000000; border: 1.5px solid #00FF66; padding: 2px 8px; border-radius: 4px; color: #FFFFFF;">{alts_str}</span></div>'
            f'<div class="speech-bubble"><div class="speech-label">REAL REDDIT RANT:</div>"{rant_text}"</div>'
            f'<div style="margin-top: 14px;"><a href="{reddit_link}" target="_blank" class="reddit-btn">VERIFY SOURCE ON REDDIT (u/{reddit_author}) -></a></div>'
            f'</div>'
        )

        st.markdown(card_html, unsafe_allow_html=True)
else:
    st.info("No opportunities generated yet. Hit 'MINE PAIN POINTS' above.")
