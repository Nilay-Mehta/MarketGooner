import os
import sys
import argparse
import subprocess
from typing import List, Optional

# Force UTF-8 on Windows consoles to prevent cp1252 emoji encoding errors
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console(force_terminal=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None

from src.key_manager import KeyManager
from src.storage import db
from src.miners.reddit_miner import RedditMiner
from src.miners.hn_miner import HackerNewsMiner
from src.miners.github_miner import GitHubMiner
from src.miners.github_issues_miner import GitHubIssuesMiner
from src.miners.stackoverflow_miner import StackOverflowMiner
from src.miners.g2_miner import G2Miner
from src.miners.shopify_reviews_miner import ShopifyReviewsMiner
from src.miners.alternativeto_miner import AlternativeToMiner
from src.miners.youtube_miner import YouTubeMiner
from src.extractors.pain_extractor import PainExtractor
from src.extractors.cluster import ProblemClusterer
from src.extractors.idea_ranker import IdeaRanker

def print_banner():
    title = "[*] MARKET INTELLIGENCE & GAP MINING ENGINE"
    subtitle = "Zero-Cost Autonomous Research Pipeline (SQLite + Multi-Stage LLM Extraction)"
    if HAS_RICH:
        console.print(Panel.fit(f"[bold cyan]{title}[/bold cyan]\n[dim]{subtitle}[/dim]", border_style="cyan"))
    else:
        print("=" * 70)
        print(f"{title}\n{subtitle}")
        print("=" * 70)

from concurrent.futures import ThreadPoolExecutor, as_completed

def cmd_scan(
    topic: str,
    subreddits: Optional[List[str]] = None,
    repos: Optional[List[str]] = None,
    incumbents: Optional[List[str]] = None,
    shopify_apps: Optional[List[str]] = None,
    alternativeto: Optional[List[str]] = None,
    limit_per_source: int = 12
):
    """Mines raw discussions across all zero-cost sources and stores them into SQLite raw_items."""
    print_banner()
    subreddits = subreddits or ["SaaS", "devops", "startups"]
    
    source_list = [f"Reddit ({', '.join(subreddits)})", "HackerNews", "StackOverflow"]
    if repos: source_list.append(f"GitHub ({', '.join(repos)})")
    if incumbents: source_list.append(f"G2 ({', '.join(incumbents)})")
    if shopify_apps: source_list.append(f"Shopify ({', '.join(shopify_apps)})")
    if alternativeto: source_list.append(f"AlternativeTo ({', '.join(alternativeto)})")

    if HAS_RICH:
        console.print(f"\\n[bold green][+] Target Domain:[/bold green] [yellow]{topic}[/yellow]")
        console.print(f"[bold green][+] Active Sources:[/bold green] {', '.join(source_list)}")
    else:
        print(f"\\nTarget Domain: {topic}")
        print(f"Active Sources: {', '.join(source_list)}")

    total_inserted = 0
    total_found = 0

    def insert_items(items, source_type, *args):
        nonlocal total_inserted, total_found
        total_found += len(items)
        for item in items:
            content = item.get("content", "")
            if source_type != "youtube" and content and len(content) > 1200:
                content = content[:800] + " ... " + content[-400:]
            
            inserted_id = db.insert_raw_item(
                source=item.get("source", ""),
                source_id=item.get("source_id", ""),
                url=item.get("url", ""),
                title=item.get("title", ""),
                content=content,
                score=item.get("score", 0),
                comments_count=item.get("comments_count", 0),
                created_utc=item.get("created_utc", 0),
                topic_query=topic,
                mentioned_incumbent=item.get("mentioned_incumbent")
            )
            if inserted_id:
                total_inserted += 1

    def run_reddit():
        reddit_miner = RedditMiner()
        for sub in subreddits:
            if HAS_RICH: console.print(f"[cyan][>] Mining Reddit r/{sub}...[/cyan]")
            items = reddit_miner.search_subreddit(subreddit=sub, query=topic, limit=limit_per_source)
            for item in items:
                item["source"] = item.get("source", f"reddit:r/{sub}")
                item["source_id"] = item.get("source_id", item.get("permalink", ""))
            insert_items(items, "reddit")

    def run_hn():
        hn_miner = HackerNewsMiner()
        if HAS_RICH: console.print("[cyan][>] Mining Hacker News...[/cyan]")
        items = hn_miner.search_discussions(query=topic, limit=limit_per_source)
        for item in items:
            item["source"] = "hackernews"
            item["source_id"] = f"hn_{item.get('url', '')}"
        insert_items(items, "hn")

    def run_so():
        so_miner = StackOverflowMiner()
        if HAS_RICH: console.print("[cyan][>] Mining StackOverflow...[/cyan]")
        items = so_miner.search_questions(query=topic, limit=limit_per_source)
        for item in items:
            item["source"] = "stackoverflow"
        insert_items(items, "so")

    def run_gh():
        if not repos: return
        gh_issues_miner = GitHubIssuesMiner()
        for r in repos:
            if HAS_RICH: console.print(f"[cyan][>] Mining GitHub {r}...[/cyan]")
            items = gh_issues_miner.search_issues(repo=r, query="bug OR feature OR complaint OR slow", limit=8)
            for item in items:
                item["source"] = item.get("source", f"github:{r}")
            insert_items(items, "gh")

    def run_g2():
        if not incumbents: return
        g2_miner = G2Miner()
        for inc in incumbents:
            if HAS_RICH: console.print(f"[cyan][>] Mining G2 for {inc}...[/cyan]")
            items = g2_miner.fetch_incumbent_complaints(product_slug=inc, limit=5)
            for item in items:
                item["source"] = item.get("source", f"g2:{inc}")
                item["mentioned_incumbent"] = inc
            insert_items(items, "g2")

    def run_shopify():
        if not shopify_apps: return
        shopify_miner = ShopifyReviewsMiner()
        for app in shopify_apps:
            if HAS_RICH: console.print(f"[cyan][>] Mining Shopify {app}...[/cyan]")
            items = shopify_miner.fetch_app_reviews(app_slug=app, limit=limit_per_source)
            for item in items:
                item["source"] = item.get("source", f"shopify:{app}")
            insert_items(items, "shopify")

    def run_alt():
        if not alternativeto: return
        alt_miner = AlternativeToMiner()
        for alt in alternativeto:
            if HAS_RICH: console.print(f"[cyan][>] Mining AlternativeTo {alt}...[/cyan]")
            items = alt_miner.fetch_alternatives(incumbent_name=alt, limit=limit_per_source)
            for item in items:
                item["source"] = item.get("source", f"alternativeto:{alt}")
                item["mentioned_incumbent"] = alt
            insert_items(items, "alt")

    def run_youtube():
        yt_miner = YouTubeMiner()
        if HAS_RICH: console.print(f"[cyan][>] Mining YouTube for {topic}...[/cyan]")
        items = yt_miner.search_pain_transcripts(query=topic, limit=min(4, limit_per_source))
        for item in items:
            item["source"] = item.get("source", "youtube")
        insert_items(items, "youtube")

    tasks = [run_reddit, run_hn, run_so, run_gh, run_g2, run_shopify, run_alt, run_youtube]
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = [executor.submit(t) for t in tasks]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"[!] Miner failed: {e}")

    if HAS_RICH:
        console.print(f"\\n[bold green][+] Scan Complete:[/bold green] Found {total_found} discussions, [bold yellow]{total_inserted} new items[/bold yellow] saved to SQLite database.")
    else:
        print(f"\\n[+] Scan Complete: Found {total_found} discussions, {total_inserted} new items saved to SQLite database.")
def cmd_extract(limit: int = 50):
    """Processes unextracted raw items and saves structured pain points into SQLite."""
    unextracted = db.get_unextracted_raw_items(limit=limit)
    if not unextracted:
        print("[!] No unextracted raw items in SQLite. Run 'scan' first.")
        return

    if HAS_RICH:
        console.print(f"[cyan][*] Extracting pain points from {len(unextracted)} raw items via LLM...[/cyan]")
    else:
        print(f"Extracting pain points from {len(unextracted)} raw items via LLM...")

    extractor = PainExtractor()
    extracted_pains = extractor.extract_pains_from_items(unextracted, batch_size=10)

    if HAS_RICH:
        console.print(f"[bold green][+] Extraction Complete:[/bold green] Saved [bold yellow]{len(extracted_pains)} concrete pain points[/bold yellow] to SQLite.")
    else:
        print(f"[+] Extraction Complete: Saved {len(extracted_pains)} concrete pain points to SQLite.")

def cmd_cluster(threshold: float = 0.35, method: str = "bertopic"):
    """Clusters pain points and updates clusters table using BERTopic or TF-IDF."""
    if HAS_RICH:
        console.print(f"[cyan][*] Clustering pain points (method={method}, threshold={threshold})...[/cyan]")
    else:
        print(f"Clustering pain points (method={method}, threshold={threshold})...")

    clusterer = ProblemClusterer()
    clusters = clusterer.cluster_pain_points(similarity_threshold=threshold, method=method)

    if HAS_RICH:
        console.print(f"[bold green][+] Clustering Complete:[/bold green] Formed [bold yellow]{len(clusters)} problem clusters[/bold yellow].")
    else:
        print(f"[+] Clustering Complete: Formed {len(clusters)} problem clusters.")

def cmd_rank(min_cluster_size: int = 5, min_source_diversity: int = 2):
    """Scores unbundled wedges and stores them in ideas table with strict citation validation."""
    if HAS_RICH:
        console.print(f"[cyan][*] Synthesizing and scoring startup ideas (min_size={min_cluster_size}, min_diversity={min_source_diversity})...[/cyan]")
    else:
        print(f"Synthesizing and scoring startup ideas (min_size={min_cluster_size}, min_diversity={min_source_diversity})...")

    ranker = IdeaRanker()
    ideas = ranker.rank_clusters(min_cluster_size=min_cluster_size, min_source_diversity=min_source_diversity)

    if ideas:
        if HAS_RICH:
            console.print(f"[bold green][+] Ranking Complete:[/bold green] Scored [bold yellow]{len(ideas)} validated startup opportunities[/bold yellow].")
        else:
            print(f"[+] Ranking Complete: Scored {len(ideas)} validated startup opportunities.")
    else:
        print("[!] No ideas generated due to strict cluster gate or citation validation.")

def cmd_top(limit: int = 10, detailed: bool = False):
    """Displays top ranked startup ideas in a rich terminal view."""
    ideas = db.list_ideas(order_by="score_total", limit=limit)
    if not ideas:
        print("[!] No ranked ideas found. Run 'scan', 'extract', 'cluster', and 'rank' first.")
        return

    if HAS_RICH:
        console.print("\n[bold cyan]🏆 TOP VALIDATED B2B SAAS OPPORTUNITIES[/bold cyan]\n")
        for idx, idea in enumerate(ideas, 1):
            trend_info = f"Trend: {idea.get('trend_verdict', 'unknown')}" if idea.get('trend_verdict') else ""
            scores = (
                f"[bold green]{idea.get('score_total')}/50[/bold green] "
                f"([dim]Freq: {idea.get('score_frequency')}/10 | WTP: {idea.get('score_wtp')}/10 | "
                f"Incumbent: {idea.get('score_incumbent_weakness')}/10 | Speed: {idea.get('score_feasibility')}/10 | Dist: {idea.get('score_distribution')}/10 | {trend_info}[/dim])"
            )
            quote = (idea.get('representative_quote') or "").strip().replace("\n", " ")
            
            card = (
                f"[bold yellow]#{idx} {idea.get('name')}[/bold yellow]  •  Score: {scores}\n"
                f"[bold cyan]Wedge:[/bold cyan] {idea.get('wedge')}\n"
                f"[bold magenta]ICP:[/bold magenta] {idea.get('icp')}\n"
                f"[bold red]Verified Quote:[/bold red] [italic]\"{quote}\"[/italic]"
            )
            console.print(Panel(card, border_style="cyan" if idx == 1 else "dim"))

        console.print("\n[dim]💡 Tip: Run 'python main.py view <rank_number>' to see the full dossier and all supporting quotes in that cluster.[/dim]\n")
    else:
        print("\n=== TOP VALIDATED B2B SAAS OPPORTUNITIES ===")
        for idx, idea in enumerate(ideas, 1):
            print(f"\n#{idx} [{idea.get('score_total')}/50] {idea.get('name')}")
            print(f"   Wedge: {idea.get('wedge')}")
            print(f"   ICP:   {idea.get('icp')}")
            print(f"   Quote: \"{idea.get('representative_quote')}\"")
            print(f"   Scores: F={idea.get('score_frequency')}, WTP={idea.get('score_wtp')}, Incumbent={idea.get('score_incumbent_weakness')}, Feasibility={idea.get('score_feasibility')}, Dist={idea.get('score_distribution')}")

def cmd_view(idea_id_or_rank: int):
    """Displays a complete dossier for a specific idea."""
    ideas = db.list_ideas(order_by="score_total", limit=50)
    if not ideas:
        print("[!] No ideas found.")
        return

    # Match by ID or Rank
    target_idea = None
    if 1 <= idea_id_or_rank <= len(ideas):
        target_idea = ideas[idea_id_or_rank - 1]
    else:
        for i in ideas:
            if i.get("id") == idea_id_or_rank:
                target_idea = i
                break

    if not target_idea:
        print(f"[!] Idea #{idea_id_or_rank} not found.")
        return

    pains = db.get_pains_by_cluster(target_idea.get("cluster_id", 0))

    if HAS_RICH:
        content = (
            f"[bold yellow]Product Name:[/bold yellow] [bold white]{target_idea.get('name')}[/bold white]\n"
            f"[bold yellow]Validation Score:[/bold yellow] [bold green]{target_idea.get('score_total')}/50[/bold green] "
            f"([dim]Frequency: {target_idea.get('score_frequency')}/10 | WTP: {target_idea.get('score_wtp')}/10 | "
            f"Incumbent Flaw: {target_idea.get('score_incumbent_weakness')}/10 | Speed to Rev: {target_idea.get('score_feasibility')}/10 | Dist: {target_idea.get('score_distribution')}/10[/dim])\n\n"
            f"[bold cyan]🎯 Target ICP:[/bold cyan] {target_idea.get('icp')}\n"
            f"[bold cyan]🚀 Unbundled Wedge:[/bold cyan] {target_idea.get('wedge')}\n\n"
            f"[bold red]💬 Primary Verified Quote:[/bold red]\n"
            f"  [italic]\"{target_idea.get('representative_quote')}\"[/italic]\n\n"
            f"[bold green]📊 Supporting Pain Signals ({len(pains)} verified quotes in cluster):[/bold green]\n"
        )
        for p in pains[:5]:
            content += f"  • [bold]{p.get('summary')}[/bold] (Severity: {p.get('severity')}/5, WTP: {p.get('willingness_to_pay')})\n"
            content += f"    [dim]Quote: \"{p.get('quote')}\"[/dim]\n"
            content += f"    [dim]Source: {p.get('url')}[/dim]\n"

        console.print(Panel(content, title=f"📋 Opportunity Dossier: {target_idea.get('name')}", border_style="green"))
    else:
        print(f"\n=== Opportunity Dossier: {target_idea.get('name')} ===")
        print(f"Score: {target_idea.get('score_total')}/50")
        print(f"ICP: {target_idea.get('icp')}")
        print(f"Wedge: {target_idea.get('wedge')}")
        print(f"Quote: \"{target_idea.get('representative_quote')}\"")

def cmd_inspect(port: int = 8001):
    """Launches Datasette web UI for full database and citation auditability."""
    db_path = db.DEFAULT_DB_PATH
    meta_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metadata.json")
    print(f"[>] Launching Datasette on http://127.0.0.1:{port}...")
    try:
        cmd = ["datasette", db_path, "-m", meta_path, "--port", str(port), "--open"]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[!] Datasette stopped.")
    except Exception as e:
        print(f"[!] Error launching Datasette: {e}")

def cmd_auto(
    topic: str,
    subreddits: Optional[List[str]] = None,
    repos: Optional[List[str]] = None,
    incumbents: Optional[List[str]] = None,
    shopify_apps: Optional[List[str]] = None,
    alternativeto: Optional[List[str]] = None,
    min_size: int = 5,
    min_diversity: int = 2
):
    """Executes the full pipeline autonomously: Scan -> Extract -> Cluster -> Rank -> Top."""
    cmd_scan(
        topic=topic,
        subreddits=subreddits,
        repos=repos,
        incumbents=incumbents,
        shopify_apps=shopify_apps,
        alternativeto=alternativeto
    )
    cmd_extract()
    cmd_cluster()
    cmd_rank(min_cluster_size=min_size, min_source_diversity=min_diversity)
    print("\n")
    cmd_top(limit=5)

def main():
    parser = argparse.ArgumentParser(description="Market Intelligence & SaaS Opportunity Miner")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Mine raw discussions across Reddit, HN, StackOverflow, GitHub, G2, Shopify, AlternativeTo")
    scan_parser.add_argument("--topic", type=str, required=True, help="Topic or problem domain")
    scan_parser.add_argument("--subreddits", nargs="+", help="Subreddits to search")
    scan_parser.add_argument("--repos", nargs="+", help="GitHub incumbent repositories")
    scan_parser.add_argument("--incumbents", nargs="+", help="Incumbent software names for G2 reviews")
    scan_parser.add_argument("--shopify-apps", nargs="+", help="Shopify app slugs to mine reviews for")
    scan_parser.add_argument("--alternativeto", nargs="+", help="Incumbent software names for AlternativeTo mining")
    scan_parser.add_argument("--limit", type=int, default=12, help="Limit per source")

    # extract
    extract_parser = subparsers.add_parser("extract", help="Extract concrete pain points from stored raw items")
    extract_parser.add_argument("--limit", type=int, default=50, help="Max raw items to process")

    # cluster
    cluster_parser = subparsers.add_parser("cluster", help="Cluster pain points by problem similarity")
    cluster_parser.add_argument("--threshold", type=float, default=0.35, help="Cosine similarity threshold")
    cluster_parser.add_argument("--method", type=str, default="bertopic", choices=["bertopic", "tfidf"], help="Clustering algorithm")

    # rank
    rank_parser = subparsers.add_parser("rank", help="Synthesize and score unbundled SaaS wedges")
    rank_parser.add_argument("--min-size", type=int, default=5, help="Minimum cluster size (gate: >=5)")
    rank_parser.add_argument("--min-diversity", type=int, default=2, help="Minimum distinct sources (gate: >=2)")

    # top
    top_parser = subparsers.add_parser("top", help="Display top ranked startup opportunities")
    top_parser.add_argument("limit", nargs="?", type=int, default=10, help="Number of top ideas to show")
    top_parser.add_argument("--detailed", action="store_true", help="Show full opportunity cards")

    # verify
    verify_parser = subparsers.add_parser("verify", help="Run verification and output metrics")

    # view
    view_parser = subparsers.add_parser("view", help="View deep dossier for a specific idea rank or ID")
    view_parser.add_argument("id", type=int, help="Idea ID or Rank number (e.g. 1)")

    # inspect
    inspect_parser = subparsers.add_parser("inspect", help="Launch Datasette auditability web UI")
    inspect_parser.add_argument("--port", type=int, default=8001, help="Port for Datasette web UI")

    # auto
    auto_parser = subparsers.add_parser("auto", help="Run full pipeline: scan -> extract -> cluster -> rank -> top")
    auto_parser.add_argument("--topic", type=str, required=True, help="Topic or problem domain")
    auto_parser.add_argument("--subreddits", nargs="+", help="Subreddits to search")
    auto_parser.add_argument("--repos", nargs="+", help="GitHub incumbent repositories")
    auto_parser.add_argument("--incumbents", nargs="+", help="Incumbent software names")
    auto_parser.add_argument("--shopify-apps", nargs="+", help="Shopify app slugs")
    auto_parser.add_argument("--alternativeto", nargs="+", help="AlternativeTo incumbent software names")
    auto_parser.add_argument("--min-size", type=int, default=5, help="Minimum cluster size gate")
    auto_parser.add_argument("--min-diversity", type=int, default=2, help="Minimum source diversity gate")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(
            topic=args.topic,
            subreddits=args.subreddits,
            repos=args.repos,
            incumbents=args.incumbents,
            shopify_apps=args.shopify_apps,
            alternativeto=args.alternativeto,
            limit_per_source=args.limit
        )
    elif args.command == "extract":
        cmd_extract(limit=args.limit)
    elif args.command == "cluster":
        cmd_cluster(threshold=args.threshold, method=args.method)
    elif args.command == "rank":
        cmd_rank(min_cluster_size=args.min_size, min_source_diversity=args.min_diversity)
    elif args.command == "top":
        cmd_top(limit=args.limit, detailed=args.detailed)
    elif args.command == "view":
        cmd_view(idea_id_or_rank=args.id)
    elif args.command == "inspect":
        cmd_inspect(port=args.port)
    elif args.command == "auto":
        cmd_auto(
            topic=args.topic,
            subreddits=args.subreddits,
            repos=args.repos,
            incumbents=args.incumbents,
            shopify_apps=args.shopify_apps,
            alternativeto=args.alternativeto,
            min_size=args.min_size,
            min_diversity=args.min_diversity
        )
    elif args.command == "verify":
        cmd_verify()
    else:
        # Default Interactive Mode
        print_banner()
        print("\nSelect an action:")
        print("  1. Run Auto Pipeline for AI / ML Infrastructure & MLOps")
        print("  2. Run Auto Pipeline for B2B SaaS Invoicing & Billing Friction")
        print("  3. Run Auto Pipeline for E-Commerce Merchant Pain (Shopify + AlternativeTo)")
        print("  4. View Top Ranked Opportunities in Database (top)")
        print("  5. Custom Auto Scan")

        choice = input("\nEnter choice [1-5] (default: 1): ").strip() or "1"
        if choice == "1":
            cmd_auto(
                topic="Kubernetes MLOps model deployment cost and egress pain",
                subreddits=["mlops", "devops", "MachineLearning"],
                repos=["prometheus/prometheus", "kubeflow/kubeflow"],
                incumbents=["datadog", "kubeflow"]
            )
        elif choice == "2":
            cmd_auto(
                topic="Stripe billing subscription invoice reconciliation pain",
                subreddits=["SaaS", "entrepreneur", "startups"],
                incumbents=["stripe-billing", "chargebee"]
            )
        elif choice == "3":
            cmd_auto(
                topic="Shopify subscription billing checkout chargeback and inventory sync pain",
                subreddits=["shopify", "ecommerce", "dropship"],
                shopify_apps=["recharge-subscriptions", "bold-subscriptions", "klaviyo-email-marketing"],
                alternativeto=["recharge-payments", "bold-commerce", "gorgias"]
            )
        elif choice == "4":
            cmd_top(limit=10)
        else:
            custom_topic = input("Enter research topic: ").strip()
            subs = input("Enter subreddits (separated by spaces, e.g. 'saas devops'): ").strip().split()
            cmd_auto(topic=custom_topic, subreddits=subs if subs else None)

def cmd_verify():
    """Verifies pipeline completion metrics and gates."""
    import os, json
    db_path = db.DEFAULT_DB_PATH
    db.init_db(db_path)
    
    with db.get_db(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Unprocessed items
        cursor.execute("SELECT COUNT(*) FROM raw_items ri WHERE NOT EXISTS (SELECT 1 FROM pain_points WHERE raw_item_id = ri.id)")
        unprocessed_items = cursor.fetchone()[0]
        
        # 2. Gate funnel
        cursor.execute("SELECT id, size, source_diversity, wtp_evidence_count, status FROM clusters")
        clusters = cursor.fetchall()
        
        total_clusters = len(clusters)
        
        status_counts = {"active": 0, "incoherent": 0, "unscoreable": 0, "scored": 0, "Error": 0, "coherent=false": 0}
        
        coherence_pass = 0
        size_pass = 0
        div_pass = 0
        wtp_pass = 0
        
        for c in clusters:
            status = c["status"] if c["status"] else "unscoreable"
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts[status] = 1
                
            if status not in ["Error", "coherent=false", "unscoreable", "incoherent"]:
                coherence_pass += 1
                if c["size"] >= 8:
                    size_pass += 1
                    if c["source_diversity"] >= 2:
                        div_pass += 1
                        if c["wtp_evidence_count"] is not None and c["wtp_evidence_count"] >= 5:
                            wtp_pass += 1
        
        # Now ideas
        cursor.execute("SELECT i.id, i.score_wtp, i.trend_verdict, i.name, c.size, c.source_diversity, c.wtp_evidence_count FROM ideas i JOIN clusters c ON i.cluster_id = c.id")
        ideas = cursor.fetchall()
        
        trend_pass = 0
        idea_failures = []
        
        for i in ideas:
            failed_gate = None
            trend = i["trend_verdict"]
            
            # The idea itself is only generated if the cluster passed coherence, size, div, wtp
            # BUT the prompt asks for ideas that fail gates.
            # Wait, the idea has its own trend verdict. Does it have its own gates?
            if trend in ["rising", "flat"]:
                trend_pass += 1
            else:
                failed_gate = f"trend={trend}"
            
            if failed_gate:
                idea_failures.append(f"Idea '{i['name']}' (ID {i['id']}) failed on: {failed_gate}")
            else:
                idea_failures.append(f"Idea '{i['name']}' (ID {i['id']}) PASSED all gates")
                
        funnel_str = f"clusters={total_clusters} -> coherence_pass={coherence_pass} -> size>=8={size_pass} -> diversity>=2={div_pass} -> wtp>=5={wtp_pass} -> trend in (rising,flat)={trend_pass}"
        
        print(f"Unprocessed items: {unprocessed_items}")
        print(f"Status breakdown: active={status_counts.get('active', 0) + status_counts.get('scored', 0)}, incoherent={status_counts.get('incoherent', 0) + status_counts.get('coherent=false', 0)}, unscoreable={status_counts.get('unscoreable', 0)}")
        print(f"Funnel: {funnel_str}")
        print("\nIdea Gates:")
        for failure in idea_failures:
            print(f" - {failure}")
            
        if trend_pass == 0:
            print("\nNo ideas passed. Top 5 clusters by (size + diversity + wtp):")
            clusters.sort(key=lambda c: (c["size"] + c["source_diversity"] + (c["wtp_evidence_count"] or 0)), reverse=True)
            for c in clusters[:5]:
                print(f" - Cluster {c['id']}: size={c['size']}, div={c['source_diversity']}, wtp={c['wtp_evidence_count']}, status={c['status']}")


if __name__ == "__main__":
    main()
