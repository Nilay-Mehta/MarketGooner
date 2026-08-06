---
name: github-intel
description: Mines open-source GitHub ecosystems to test market saturation, track star momentum, and extract top upvoted (+1 reactions) feature requests from competitor repositories.
---

# GitHub Intelligence & Saturation Skill

Use your GitHub Personal Access Token (`GITHUB_TOKEN`) to audit open-source competition and uncover unmet feature requests.

## 1. Saturation Check
- Search GitHub repositories for the target keyword.
- If there are >30 active repositories with >1,000 stars doing the exact same thing, flag the niche as **High Saturation (Hard to Monetize as Indie B2B)**.
- If existing repositories have high stars but zero updates in the last 12 months, flag as an **Abandoned Open-Source Commercial Opportunity**.

## 2. Upvoted Issue Mining (Unmet Feature Demand)
- Target the top 2-3 open-source competitors.
- Query issues sorted by `reactions-+1-desc` (most thumbs-up reactions from real users).
- These top upvoted issues are verified, painful missing features that users are begging maintainers to build!
- Use these exact missing features to define the V1 scope of your paid B2B Micro-SaaS.
