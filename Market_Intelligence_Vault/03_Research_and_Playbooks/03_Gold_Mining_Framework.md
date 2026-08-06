# Steph France's Gold Mining Framework

This maps the exact 45-minute process described by Steph France to go from zero ideas to a landing page using 6 tools and 5 prompts.

## Step 1: Find a Market to Explore
- **Focus Areas:** Health, Wealth, Relationship. These are core markets where people are willing to spend money, reducing risk.
- **Tool:** Claude (preferred because it is more "human-like" with better emotional copywriting and reads Markdown accurately).
- **Action:** Paste the **"Market Idea Expander"** prompt into Claude (using Markdown format so the LLM reads it cleanly). Give it a broad market (e.g., "Stress management") and let it drill down into sub-niches (e.g., physical stress relief -> massage therapy -> Swedish massage).

## Step 2: Validate Demand
- **Tools:** Google Search, Keyword Everywhere (Chrome Extension), Google Trends.
- **Action:** 
  - Look up the sub-niche to find search volume (e.g., "Swedish massage near me" = 20,000 searches).
  - Use Google Trends to check if it's stable or growing. Differentiate between a *Search Term* and a *Topic* (Topic includes all related terms globally). 
  - *Example given:* Co-parenting. 40,000 search volume. Searches like "co-parenting apps", "co-parenting counseling", "classes". Google Trends shows a solid, steady, growing trend based on human societal needs, not an AI fad that dies in 3 months.

## Step 3: Gather Data (The Gold Mine)
- **Target:** Reddit. It is the place on the internet where the world shares problems anonymously in long conversations.
- **Action:** Use a specific advanced Google search query designed to filter out general noise and only surface threads where people are expressing pain. 
- **Execution:** Read the threads manually to ensure relevance (e.g., check subreddits like `r/coparenting` or `r/blendedfamilies`). Open a text block, copy the entire Reddit thread, paste it, type `---`, and paste the next thread. Gather as many as possible.

## Step 4: Process the Data
Paste the gathered Reddit data into a fresh Claude chat and run three specific prompts sequentially:
1. **Extraction Prompt:** Extracts all pain points, refines them into categories, and rigidly attaches *direct quotes* from the Reddit users to prove the pain exists (e.g., "It's hard to coparent with your abuser").
2. **Market Gap Generator Prompt:** Takes those pain points and runs them through a framework (new paradigm, new technology, product differentiation) to generate business ideas in a saturated market. *Example given:* "Child-centered custody transition tool" with emotional check-ins and handoff protocols.
3. **Landing Page Prompt Creator:** This prompt was created by ChatGPT doing research on the internet for *Lovable* (an AI app/UI builder) best practices. It converts the chosen business idea and user quotes into an optimized prompt specifically for Lovable.

## Step 5: Build the Landing Page
- Copy the output from Prompt 3.
- Paste it into Lovable.
- *Result:* An instant landing page that feeds the customer's exact pain points back to them using their own wording (e.g., "Transform custody transitions from tearful breakdowns to peaceful goodbyes").
