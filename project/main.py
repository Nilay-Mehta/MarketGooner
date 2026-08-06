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
        console.print(f"\n[bold green][+] Target Domain:[/bold green] [yellow]{topic}[/yellow]")
        console.print(f"[bold green][+] Active Sources:[/bold green] {', '.join(source_list)}")
    else:
        print(f"\nTarget Domain: {topic}")
        print(f"Active Sources: {', '.join(source_list)}")

    total_inserted = 0
    total_found = 0

    # 1. Reddit
    reddit_miner = RedditMiner()
    for sub in subreddits:
        if HAS_RICH:
            console.print(f"[cyan][>] Mining Reddit r/{sub}...[/cyan]")
        items = reddit_miner.search_subreddit(subreddit=sub, query=topic, limit=limit_per_source)
        total_found += len(items)
        for item in items:
            inserted_id = db.insert_raw_item(
                source=item.get("source", f"reddit:r/{sub}"),
                source_id=item.get("source_id", item.get("permalink", "")),
                url=item.get("url", ""),
                title=item.get("title", ""),
                content=item.get("content", ""),
                score=item.get("score", 0),
                comments_count=item.get("comments_count", 0),
                created_utc=item.get("created_utc", 0),
                topic_query=topic
            )
            if inserted_id:
                total_inserted += 1

    # 2. Hacker News
    hn_miner = HackerNewsMiner()
    if HAS_RICH:
        console.print("[cyan][>] Mining Hacker News Algolia API...[/cyan]")
    hn_items = hn_miner.search_discussions(query=topic, limit=limit_per_source)
    total_found += len(hn_items)
    for item in hn_items:
        inserted_id = db.insert_raw_item(
            source="hackernews",
            source_id=f"hn_{item.get('url', '')}",
            url=item.get("url", ""),
            title=item.get("title", ""),
            content=item.get("content", ""),
            score=item.get("score", 0),
            comments_count=item.get("comments_count", 0),
            topic_query=topic
        )
        if inserted_id:
            total_inserted += 1

    # 3. Stack Overflow
    so_miner = StackOverflowMiner()
    if HAS_RICH:
        console.print("[cyan][>] Mining Stack Overflow Developer Friction...[/cyan]")
    so_items = so_miner.search_questions(query=topic, limit=limit_per_source)
    total_found += len(so_items)
    for item in so_items:
        inserted_id = db.insert_raw_item(
            source="stackoverflow",
            source_id=item.get("source_id", ""),
            url=item.get("url", ""),
            title=item.get("title", ""),
            content=item.get("content", ""),
            score=item.get("score", 0),
            comments_count=item.get("comments_count", 0),
            topic_query=topic
        )
        if inserted_id:
            total_inserted += 1

    # 4. GitHub Issues if repos provided
    if repos:
        gh_issues_miner = GitHubIssuesMiner()
        for r in repos:
            if HAS_RICH:
                console.print(f"[cyan][>] Mining GitHub Issues for {r}...[/cyan]")
            gh_items = gh_issues_miner.search_issues(repo=r, query="bug OR feature OR complaint OR slow", limit=8)
            total_found += len(gh_items)
            for item in gh_items:
                inserted_id = db.insert_raw_item(
                    source=item.get("source", f"github:{r}"),
                    source_id=item.get("source_id", ""),
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0),
                    comments_count=item.get("comments_count", 0),
                    topic_query=topic
                )
                if inserted_id:
                    total_inserted += 1

    # 5. G2 Incumbent Complaints if incumbents provided
    if incumbents:
        g2_miner = G2Miner()
        for inc in incumbents:
            if HAS_RICH:
                console.print(f"[cyan][>] Mining G2 Reviews for {inc}...[/cyan]")
            g2_items = g2_miner.fetch_incumbent_complaints(product_slug=inc, limit=5)
            total_found += len(g2_items)
            for item in g2_items:
                inserted_id = db.insert_raw_item(
                    source=item.get("source", f"g2:{inc}"),
                    source_id=item.get("source_id", ""),
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0),
                    comments_count=item.get("comments_count", 0),
                    topic_query=topic,
                    mentioned_incumbent=inc
                )
                if inserted_id:
                    total_inserted += 1

    # 6. Shopify Reviews if shopify_apps provided
    if shopify_apps:
        shopify_miner = ShopifyReviewsMiner()
        for app in shopify_apps:
            if HAS_RICH:
                console.print(f"[cyan][>] Mining Shopify App Reviews for '{app}'...[/cyan]")
            reviews = shopify_miner.fetch_app_reviews(app_slug=app, limit=limit_per_source)
            total_found += len(reviews)

    # 7. AlternativeTo if alternativeto provided
    if alternativeto:
        alt_miner = AlternativeToMiner()
        for alt in alternativeto:
            if HAS_RICH:
                console.print(f"[cyan][>] Mining AlternativeTo weaknesses for '{alt}'...[/cyan]")
            items = alt_miner.fetch_alternatives(incumbent_name=alt, limit=limit_per_source)
            total_found += len(items)

    # 8. YouTube Transcripts
    yt_miner = YouTubeMiner()
    if HAS_RICH:
        console.print(f"[cyan][>] Mining YouTube founder/operator discussions for '{topic}'...[/cyan]")
    yt_items = yt_miner.search_pain_transcripts(query=topic, limit=min(4, limit_per_source))
    total_found += len(yt_items)

    if HAS_RICH:
        console.print(f"\n[bold green][+] Scan Complete:[/bold green] Found {total_found} discussions, [bold yellow]{total_inserted} new items[/bold yellow] saved to SQLite database.")
    else:
        print(f"\n[+] Scan Complete: Found {total_found} discussions, {total_inserted} new items saved to SQLite database.")

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
    extracted_pains = extractor.extract_pains_from_items(unextracted, batch_size=3)

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

if __name__ == "__main__":
    main()
