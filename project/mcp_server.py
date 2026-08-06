import sys
import json
import os
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.storage import db
from src.key_manager import KeyManager
from src.miners.reddit_miner import RedditMiner
from src.miners.hn_miner import HackerNewsMiner
from src.miners.github_miner import GitHubMiner
from src.miners.github_issues_miner import GitHubIssuesMiner
from src.miners.stackoverflow_miner import StackOverflowMiner
from src.miners.g2_miner import G2Miner
from src.miners.jina_fetcher import JinaFetcher
from src.miners.shopify_reviews_miner import ShopifyReviewsMiner
from src.miners.alternativeto_miner import AlternativeToMiner
from src.miners.youtube_miner import YouTubeMiner
from src.extractors.pain_extractor import PainExtractor
from src.extractors.cluster import ProblemClusterer
from src.extractors.idea_ranker import IdeaRanker

def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handles MCP tool calls for Opencode sub-agents."""
    
    if name == "search_reddit":
        sub = arguments.get("subreddit", "SaaS")
        query = arguments.get("query", "")
        limit = int(arguments.get("limit", 8))
        miner = RedditMiner()
        posts = miner.search_subreddit(subreddit=sub, query=query, limit=limit)
        
        # Save to SQLite raw_items
        for p in posts:
            db.insert_raw_item(
                source=p.get("source", f"reddit:r/{sub}"),
                source_id=p.get("source_id", p.get("permalink", "")),
                url=p.get("url", ""),
                title=p.get("title", ""),
                content=p.get("content", ""),
                score=p.get("score", 0),
                comments_count=p.get("comments_count", 0),
                created_utc=p.get("created_utc", 0),
                topic_query=query
            )

        if not posts:
            return {"content": [{"type": "text", "text": f"No Reddit discussions found in r/{sub} for query: {query}"}]}
        
        lines = [f"### Reddit Signals: r/{sub} (`{query}`)"]
        for p in posts:
            friction = "🔥 [Friction]" if p.get("friction_detected") else ""
            content_snippet = (p.get("content") or "").strip().replace("\n", " ")[:200]
            lines.append(f"- **[{p.get('title')}]({p.get('url')})** (Upvotes: {p.get('score')}, Comments: {p.get('comments_count')}) {friction}")
            if content_snippet:
                lines.append(f"  > \"{content_snippet}...\"")
        
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "search_hackernews":
        query = arguments.get("query", "")
        limit = int(arguments.get("limit", 8))
        miner = HackerNewsMiner()
        discussions = miner.search_discussions(query=query, limit=limit)
        
        for d in discussions:
            db.insert_raw_item(
                source="hackernews",
                source_id=f"hn_{d.get('url', '')}",
                url=d.get("url", ""),
                title=d.get("title", ""),
                content=d.get("content", ""),
                score=d.get("score", 0),
                comments_count=d.get("comments_count", 0),
                topic_query=query
            )

        if not discussions:
            return {"content": [{"type": "text", "text": f"No Hacker News discussions found for query: {query}"}]}
        
        lines = [f"### Hacker News Signals (`{query}`)"]
        for d in discussions:
            content_snippet = (d.get("content") or "").strip().replace("\n", " ")[:200]
            lines.append(f"- **[{d.get('title')}]({d.get('url')})** (Points: {d.get('score')}, Comments: {d.get('comments_count')})")
            if content_snippet:
                lines.append(f"  > \"{content_snippet}...\"")
                
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "search_g2_reviews":
        product = arguments.get("product", "")
        limit = int(arguments.get("limit", 6))
        miner = G2Miner()
        reviews = miner.fetch_incumbent_complaints(product_slug=product, limit=limit)
        
        for r in reviews:
            db.insert_raw_item(
                source=r.get("source", f"g2:{product}"),
                source_id=r.get("source_id", ""),
                url=r.get("url", ""),
                title=r.get("title", ""),
                content=r.get("content", ""),
                score=r.get("score", 0),
                comments_count=0,
                topic_query=product
            )

        if not reviews:
            return {"content": [{"type": "text", "text": f"No G2 review complaints found for: {product}"}]}

        lines = [f"### G2 Customer Dissatisfaction: `{product}`"]
        for r in reviews:
            lines.append(f"- **{r.get('title')}**\n  > {r.get('content')[:250]}...")

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "search_stackoverflow":
        query = arguments.get("query", "")
        limit = int(arguments.get("limit", 6))
        miner = StackOverflowMiner()
        questions = miner.search_questions(query=query, limit=limit)

        for q in questions:
            db.insert_raw_item(
                source="stackoverflow",
                source_id=q.get("source_id", ""),
                url=q.get("url", ""),
                title=q.get("title", ""),
                content=q.get("content", ""),
                score=q.get("score", 0),
                comments_count=q.get("comments_count", 0),
                topic_query=query
            )

        if not questions:
            return {"content": [{"type": "text", "text": f"No Stack Overflow questions found for: {query}"}]}

        lines = [f"### Stack Overflow Bottlenecks (`{query}`)"]
        for q in questions:
            lines.append(f"- **[{q.get('title')}]({q.get('url')})** (Votes: {q.get('score')}, Answers: {q.get('comments_count')})")

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "search_github_issues":
        repo = arguments.get("repo", "")
        query = arguments.get("query", "bug OR feature OR slow")
        limit = int(arguments.get("limit", 6))
        miner = GitHubIssuesMiner()
        issues = miner.search_issues(repo=repo, query=query, limit=limit)

        for iss in issues:
            db.insert_raw_item(
                source=iss.get("source", f"github:{repo}"),
                source_id=iss.get("source_id", ""),
                url=iss.get("url", ""),
                title=iss.get("title", ""),
                content=iss.get("content", ""),
                score=iss.get("score", 0),
                comments_count=iss.get("comments_count", 0),
                topic_query=repo
            )

        if not issues:
            return {"content": [{"type": "text", "text": f"No GitHub issues found in {repo} for: {query}"}]}

        lines = [f"### Unresolved Issues in `{repo}` (`{query}`)"]
        for iss in issues:
            lines.append(f"- **[{iss.get('title')}]({iss.get('url')})** (Reactions/Comments: {iss.get('score')})")

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "search_shopify_reviews":
        app = arguments.get("app", "")
        limit = int(arguments.get("limit", 10))
        miner = ShopifyReviewsMiner()
        reviews = miner.fetch_app_reviews(app_slug=app, limit=limit)
        if not reviews:
            return {"content": [{"type": "text", "text": f"No reviews found for Shopify app: {app}"}]}

        lines = [f"### Shopify Merchant Complaints: `{app}`"]
        for r in reviews:
            lines.append(f"- **{r.get('title')}** (Rating: {r.get('score')}/5)\n  > {r.get('content')[:250]}...")
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "search_alternativeto":
        product = arguments.get("product", "")
        limit = int(arguments.get("limit", 10))
        miner = AlternativeToMiner()
        items = miner.fetch_alternatives(incumbent_name=product, limit=limit)
        if not items:
            return {"content": [{"type": "text", "text": f"No AlternativeTo feedback found for: {product}"}]}

        lines = [f"### AlternativeTo Incumbent Friction: `{product}`"]
        for item in items:
            lines.append(f"- **{item.get('title')}**\n  > {item.get('content')[:250]}...")
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "search_youtube_transcripts":
        query = arguments.get("query", "")
        limit = int(arguments.get("limit", 4))
        miner = YouTubeMiner()
        items = miner.search_pain_transcripts(query=query, limit=limit)
        if not items:
            return {"content": [{"type": "text", "text": f"No YouTube pain transcripts found for: {query}"}]}

        lines = [f"### YouTube Founder/Operator Friction: `{query}`"]
        for item in items:
            lines.append(f"- **[{item.get('title')}]({item.get('url')})**\n  > \"{item.get('content')[:250]}...\"")
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "rank_ideas":
        min_size = int(arguments.get("min_size", 1))
        # 1. Extract
        extractor = PainExtractor()
        unextracted = db.get_unextracted_raw_items(limit=50)
        if unextracted:
            extractor.extract_pains_from_items(unextracted)
        # 2. Cluster
        clusterer = ProblemClusterer()
        clusterer.cluster_pain_points()
        # 3. Rank
        ranker = IdeaRanker()
        ideas = ranker.rank_clusters(min_cluster_size=min_size)

        lines = [f"### Ranked Opportunities (Top {len(ideas)})"]
        for idx, idea in enumerate(ideas[:8], 1):
            lines.append(
                f"**#{idx} [{idea.get('score_total')}/50] {idea.get('name')}**\n"
                f"- **Wedge:** {idea.get('wedge')}\n"
                f"- **ICP:** {idea.get('icp')}\n"
                f"- **Verified Quote:** \"{idea.get('representative_quote')}\"\n"
                f"- **Scores:** F:{idea.get('score_frequency')} | WTP:{idea.get('score_wtp')} | Inc:{idea.get('score_incumbent_weakness')} | Feas:{idea.get('score_feasibility')} | Dist:{idea.get('score_distribution')}\n"
            )

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "list_top_ideas":
        limit = int(arguments.get("limit", 10))
        ideas = db.list_ideas(order_by="score_total", limit=limit)
        if not ideas:
            return {"content": [{"type": "text", "text": "No ranked ideas found in database. Run rank_ideas or main.py auto first."}]}

        lines = [f"### Top {len(ideas)} Stored B2B SaaS Opportunities"]
        for idx, idea in enumerate(ideas, 1):
            lines.append(
                f"**#{idx} [{idea.get('score_total')}/50] {idea.get('name')}**\n"
                f"- **Wedge:** {idea.get('wedge')}\n"
                f"- **ICP:** {idea.get('icp')}\n"
                f"- **Quote:** \"{idea.get('representative_quote')}\"\n"
            )
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "get_cluster_pains":
        cluster_id = int(arguments.get("cluster_id", 1))
        pains = db.get_pains_by_cluster(cluster_id=cluster_id)
        if not pains:
            return {"content": [{"type": "text", "text": f"No pain points found for cluster_id: {cluster_id}"}]}

        lines = [f"### Cluster #{cluster_id} Pain Points ({len(pains)} items)"]
        for p in pains:
            lines.append(f"- **Summary:** {p.get('summary')} (Severity: {p.get('severity')}, WTP: {p.get('willingness_to_pay')})\n  > Quote: \"{p.get('quote')}\"\n  > Source: {p.get('url')}")

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    else:
        return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool: {name}"}]}

def list_tools() -> List[Dict[str, Any]]:
    """Returns available tools for MCP clients and Opencode."""
    return [
        {
            "name": "search_reddit",
            "description": "Searches Reddit subreddits for customer complaints and stores items in SQLite.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "subreddit": {"type": "string", "description": "Target subreddit (e.g. 'mlops')"},
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max items"}
                },
                "required": ["subreddit", "query"]
            }
        },
        {
            "name": "search_hackernews",
            "description": "Searches Hacker News for developer complaints and stores items in SQLite.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max items"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "search_g2_reviews",
            "description": "Fetches 1-3 star negative reviews for an incumbent product from G2 and stores in SQLite.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Incumbent product slug (e.g. 'datadog', 'stripe-billing')"},
                    "limit": {"type": "integer", "description": "Max reviews"}
                },
                "required": ["product"]
            }
        },
        {
            "name": "search_stackoverflow",
            "description": "Searches Stack Overflow developer friction and questions and stores in SQLite.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search terms"},
                    "limit": {"type": "integer", "description": "Max results"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "search_github_issues",
            "description": "Searches competitor GitHub repos for top upvoted feature requests and unresolved user bugs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "query": {"type": "string", "description": "Issue search terms"},
                    "limit": {"type": "integer", "description": "Max results"}
                },
                "required": ["repo"]
            }
        },
        {
            "name": "search_shopify_reviews",
            "description": "Fetches 1-3 star customer complaints from the Shopify App Store for an app slug.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "app": {"type": "string", "description": "Shopify app slug (e.g. 'recharge', 'bold-subscriptions')"},
                    "limit": {"type": "integer", "description": "Max reviews to fetch"}
                },
                "required": ["app"]
            }
        },
        {
            "name": "search_alternativeto",
            "description": "Fetches dissatisfaction and switch reasons for an incumbent product from AlternativeTo.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "description": "Incumbent product name/slug (e.g. 'zendesk', 'stripe')"},
                    "limit": {"type": "integer", "description": "Max items to fetch"}
                },
                "required": ["product"]
            }
        },
        {
            "name": "search_youtube_transcripts",
            "description": "Searches YouTube founder and operator interview transcripts for real SaaS complaints and friction.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (e.g. 'Stripe billing nightmare', 'switching from Datadog')"},
                    "limit": {"type": "integer", "description": "Max videos to inspect"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "rank_ideas",
            "description": "Runs full extraction, clustering, and 5-dimension rubric scoring across gathered market data.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "min_size": {"type": "integer", "description": "Minimum cluster size to evaluate (default 1)"}
                }
            }
        },
        {
            "name": "list_top_ideas",
            "description": "Lists top ranked B2B SaaS opportunities stored in the database.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of ideas to retrieve"}
                }
            }
        },
        {
            "name": "get_cluster_pains",
            "description": "Fetches all verbatim customer quotes and pain points in a specific cluster.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cluster_id": {"type": "integer", "description": "Cluster ID"}
                },
                "required": ["cluster_id"]
            }
        }
    ]

def main():
    """Standard JSON-RPC Stdio MCP Server Loop."""
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "market-intelligence-mcp", "version": "2.0.0"},
                        "capabilities": {"tools": {}}
                    }
                }
            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": list_tools()}
                }
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                args = params.get("arguments", {})
                call_res = handle_call_tool(tool_name, args)
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": call_res
                }
            elif method == "notifications/initialized":
                continue
            else:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method {method} not found"}
                }
            
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"MCP Server Error: {str(e)}\n")

if __name__ == "__main__":
    main()
