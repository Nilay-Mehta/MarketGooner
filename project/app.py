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
# PAGE SETUP & NEON COMIC BOOK STYLING
# =====================================================================

st.set_page_config(
    page_title="MARKET GOONER // INTELLIGENCE ENGINE",
    page_icon="💥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cyberpunk / Neo-Brutalist Comic Book CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Space+Grotesk:wght@600;700;900&display=swap');

    /* Global Dark Comic Palette */
    :root {
        --neon: #00FF66;
        --neon-glow: rgba(0, 255, 102, 0.4);
        --yellow: #FFE500;
        --dark-bg: #090A0F;
        --card-bg: #12131A;
        --border-color: #00FF66;
    }

    body, .stApp {
        background-color: var(--dark-bg) !important;
        color: #F8FAFC !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }

    /* Comic Headings */
    .comic-title {
        font-family: 'Bangers', cursive;
        font-size: 54px;
        color: var(--neon);
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 0;
        text-shadow: 4px 4px 0px #000, 0 0 25px var(--neon-glow);
        line-height: 1.1;
    }

    .comic-sub {
        font-size: 16px;
        color: #94A3B8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 4px;
    }

    /* Comic Box Panel */
    .comic-panel {
        background: var(--card-bg);
        border: 3px solid var(--neon);
        border-radius: 12px;
        box-shadow: 6px 6px 0px #000000;
        padding: 24px;
        margin-bottom: 24px;
        position: relative;
    }

    .comic-panel:hover {
        box-shadow: 8px 8px 0px var(--neon);
        transform: translate(-2px, -2px);
        transition: all 0.15s ease-in-out;
    }

    /* Comic Badges */
    .comic-badge {
        display: inline-block;
        font-family: 'Bangers', cursive;
        font-size: 18px;
        letter-spacing: 1px;
        padding: 4px 14px;
        border: 2px solid #000;
        border-radius: 6px;
        box-shadow: 3px 3px 0px #000;
        margin-right: 8px;
        margin-bottom: 12px;
    }
    .badge-neon { background-color: var(--neon); color: #000; }
    .badge-yellow { background-color: var(--yellow); color: #000; }
    .badge-white { background-color: #FFFFFF; color: #000; }

    /* Speech Bubble (Customer Rant Proof) */
    .speech-bubble {
        position: relative;
        background: #1E202B;
        border: 2px solid #334155;
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 14px;
        font-size: 14px;
        color: #E2E8F0;
        font-style: italic;
        line-height: 1.5;
    }
    .speech-bubble::before {
        content: "💬 VERBATIM REDDIT RANT:";
        display: block;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 11px;
        font-weight: 900;
        font-style: normal;
        color: var(--neon);
        margin-bottom: 4px;
        letter-spacing: 1px;
    }

    /* Comic Action Buttons */
    div.stButton > button:first-child {
        font-family: 'Bangers', cursive !important;
        font-size: 24px !important;
        letter-spacing: 1.5px !important;
        background-color: var(--neon) !important;
        color: #000000 !important;
        border: 3px solid #000000 !important;
        border-radius: 8px !important;
        box-shadow: 5px 5px 0px #000000 !important;
        padding: 12px 28px !important;
        transition: all 0.1s ease-in-out !important;
        width: 100% !important;
    }
    div.stButton > button:first-child:hover {
        background-color: var(--yellow) !important;
        box-shadow: 3px 3px 0px #000000 !important;
        transform: translate(2px, 2px) !important;
        color: #000000 !important;
    }

    /* Download Buttons */
    div.stDownloadButton > button {
        font-family: 'Bangers', cursive !important;
        font-size: 20px !important;
        letter-spacing: 1.2px !important;
        border: 3px solid #000000 !important;
        border-radius: 8px !important;
        box-shadow: 4px 4px 0px #000000 !important;
        padding: 10px 20px !important;
    }

    /* Links */
    a.source-link {
        display: inline-block;
        background-color: #0F172A;
        border: 2px solid var(--neon);
        color: var(--neon) !important;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 13px;
        text-decoration: none !important;
        box-shadow: 3px 3px 0px #000;
        margin-top: 10px;
    }
    a.source-link:hover {
        background-color: var(--neon);
        color: #000000 !important;
    }
    
    /* Input inputs styling */
    div[data-baseweb="input"] {
        border: 2px solid #334155 !important;
        border-radius: 8px !important;
        background-color: #12131A !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: var(--neon) !important;
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
    st.markdown('<h1 class="comic-title">💥 MARKET GOONER // GAP MINER</h1>', unsafe_allow_html=True)
    st.markdown('<p class="comic-sub">Turning Customer Pain Into Validated B2B SaaS Gold</p>', unsafe_allow_html=True)

with col_h2:
    st.markdown("""
    <div style="text-align: right; margin-top: 10px;">
        <span class="comic-badge badge-neon">⚡ LAYA GATE ACTIVE</span>
        <span class="comic-badge badge-yellow">ZERO COST</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# =====================================================================
# INPUT & CONTROLS PANEL (STRIPPED DOWN & PUNCHY)
# =====================================================================

with st.container():
    st.markdown('<div class="comic-panel" style="padding: 18px 24px; border-color: #FFE500;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-family: Bangers; font-size: 26px; color: #FFE500; margin-top:0;">⚡ STEP 1: CONFIGURE & LAUNCH</h3>', unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3, col_btn = st.columns([1.5, 1.2, 1.2, 1.5])
    
    with col_c1:
        subreddit = st.text_input("🎯 Subreddit:", value="smallbusiness")
    with col_c2:
        query = st.text_input("🔍 Problem Keyword:", value="software")
    with col_c3:
        mode = st.selectbox("⚡ Mode:", ["Safe Demo Mode (Instant)", "Live Reddit Scrape"])
    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        run_btn = st.button("🚀 MINE PAIN POINTS", use_container_width=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# LIVE EXECUTION LOGIC
# =====================================================================

if run_btn:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        router = ModelRouter()
        db = StorageManager()

        status_text.markdown("### ⛏️ [1/4] Mining Customer Conversations...")
        progress_bar.progress(25)
        
        if mode == "Safe Demo Mode (Instant)" and os.path.exists("eval_ground_truth.csv"):
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

        status_text.markdown("### 🧠 [2/4] Extracting & Clustering Friction Themes...")
        progress_bar.progress(50)
        extractor = PainExtractor(router=router, storage=db)
        pains = extractor.process_evidence(scraped)

        clustering = ClusteringEngine(router=router, storage=db)
        clusters = clustering.build_clusters(pains)

        status_text.markdown("### 🛡️ [3/4] Running Local ConvAI Laya System 1 Gate...")
        progress_bar.progress(75)
        opp_engine = OpportunityEngine(router=router, storage=db)
        opportunities = []
        for c in clusters:
            op = opp_engine.evaluate_cluster(c)
            if op:
                opportunities.append(op)

        status_text.markdown("### 📄 [4/4] Writing Executive Word & Markdown Reports...")
        progress_bar.progress(90)
        diffusion = DiffusionEngine(router=router)
        for op in opportunities:
            diffusion.generate_dossier(op)

        compile_market_intelligence_report(input_dir="delivery_pack", output_md="Market_Intelligence_Report.md")

        progress_bar.progress(100)
        status_text.success("🎉 BOOM! Intelligence Scan Finished. All Opportunities & Master Report Ready Below.")
        time.sleep(1)
        st.rerun()

    except Exception as e:
        st.error(f"Execution Error: {e}")

# =====================================================================
# ACTION BAR: 1-CLICK DOWNLOADS & STATS
# =====================================================================

opps_df, evidence_df = load_data()

col_d1, col_d2, col_d3 = st.columns([1.5, 1.5, 1.0])

docx_path = "delivery_pack/Market_Intelligence_Report.docx"
md_path = "delivery_pack/Market_Intelligence_Report.md"
csv_path = "eval_ground_truth.csv"

with col_d1:
    if os.path.exists(docx_path):
        with open(docx_path, "rb") as f:
            st.download_button(
                label="📥 DOWNLOAD MASTER WORD DOC (.DOCX)",
                data=f,
                file_name="Market_Intelligence_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

with col_d2:
    if os.path.exists(md_path):
        with open(md_path, "rb") as f:
            st.download_button(
                label="📄 DOWNLOAD RAW MARKDOWN (.MD)",
                data=f,
                file_name="Market_Intelligence_Report.md",
                mime="text/markdown",
                use_container_width=True
            )

with col_d3:
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            st.download_button(
                label="📊 BENCHMARK CSV",
                data=f,
                file_name="eval_ground_truth.csv",
                mime="text/csv",
                use_container_width=True
            )

st.markdown("<hr style='border: 1px dashed #334155; margin: 20px 0;'>", unsafe_allow_html=True)

# =====================================================================
# RESULTS FEED (THE COMIC PANELS)
# =====================================================================

st.markdown(f'<h2 style="font-family: Bangers; font-size: 38px; color: var(--neon); letter-spacing: 1px; margin-bottom: 20px;">🏆 VALIDATED B2B OPPORTUNITIES ({len(opps_df)} DISCOVERED)</h2>', unsafe_allow_html=True)

if not opps_df.empty:
    for idx, row in opps_df.iterrows():
        score = row['commercial_relevance']
        score_badge = f"🔥 {score}/10 HIGH CONVICTION" if score >= 6 else f"⭐ {score}/10 VALIDATED WEDGE"
        badge_style = "badge-neon" if score >= 6 else "badge-yellow"

        # Parse alternatives
        alts = []
        try:
            alts = json.loads(row['existing_alternatives']) if isinstance(row['existing_alternatives'], str) else row['existing_alternatives']
        except:
            alts = [str(row['existing_alternatives'])]
        alts_str = ", ".join(alts) if alts else "Excel / Spreadsheets"

        # Match proof evidence text from DB if available
        matched_ev = None
        if not evidence_df.empty:
            matched_ev = evidence_df.iloc[idx % len(evidence_df)]

        st.markdown(f"""
        <div class="comic-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                    <span class="comic-badge {badge_style}">{score_badge}</span>
                    <span class="comic-badge badge-white">BUYER: {row['target_customer']}</span>
                </div>
                <div style="font-family: 'Bangers'; font-size: 22px; color: #64748B;">
                    OPPORTUNITY #{idx+1}
                </div>
            </div>

            <h2 style="font-family: 'Space Grotesk'; font-size: 22px; font-weight: 800; color: #FFFFFF; margin: 8px 0;">
                {row['concept']}
            </h2>

            <p style="color: #CBD5E1; font-size: 15px; margin: 10px 0; line-height: 1.6;">
                <strong style="color: var(--neon);">THE ROOT PROBLEM:</strong> {row['canonical_problem']}
            </p>

            <div style="margin: 12px 0; font-size: 14px; color: #94A3B8;">
                <strong style="color: #FFE500;">DISPLACING:</strong> <span style="background: #1E293B; padding: 2px 8px; border-radius: 4px; color: #F8FAFC;">{alts_str}</span>
            </div>
        """, unsafe_allow_html=True)

        if matched_ev is not None:
            clean_text = matched_ev['text'].replace('\n', ' ')
            if len(clean_text) > 280:
                clean_text = clean_text[:280] + "..."
            
            st.markdown(f"""
            <div class="speech-bubble">
                "{clean_text}"
            </div>
            <div style="margin-top: 10px;">
                <a href="{matched_ev['url']}" target="_blank" class="source-link">
                    🔗 VERIFY ON REDDIT (u/{matched_ev['author']}) ➔
                </a>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No opportunities generated yet. Hit 'MINE PAIN POINTS' above!")
