---
name: deep-market-research
description: Multi-source recursive market research skill. Performs iterative search query expansion, cross-validates data across Reddit, Hacker News, G2, and industry publications, and tracks all source citations.
---

# Deep Market Research Skill

Execute iterative, multi-layer market investigations:

## Phase 1: Query Expansion Matrix
For any target domain, generate 5 orthogonal search queries:
1. **Friction:** `"[domain] painful" OR "[domain] broken" OR "[domain] nightmare"`
2. **Alternative Hunting:** `"alternative to [incumbent tool]"`
3. **DIY Hacks:** `"[domain] script" OR "[domain] excel template" OR "[domain] zapier workaround"`
4. **Pricing Complaints:** `"[incumbent tool] expensive" OR "[incumbent tool] pricing increase"`
5. **Feature Requests:** `"why doesn't [incumbent tool] support" OR "wish there was a tool for"`

## Phase 2: Multi-Source Scraping & Verification
- Query Reddit public endpoints across 3-5 relevant niche subreddits.
- Query Hacker News Algolia API for developer discussions and "Ask HN" posts.
- Query competitor documentation and review sites using Jina Reader.

## Phase 3: Cross-Validation Gate
- Require at least **3 independent user complaints** from different users before classifying a pain point as a validated market gap.
