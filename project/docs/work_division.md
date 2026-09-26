# Team Work Division (2 Engineers)

To move fast without stepping on each other's toes, the best way to divide this architecture is by **Pipeline Stages**, using the SQLite Database as the "contract" or hand-off point between the two developers.

## The Hand-Off Point: `ProblemCluster`
The database schema is already built. 
* **Engineer 1** is responsible for writing raw data into the DB and grouping it into `ProblemCluster` rows. 
* **Engineer 2** is responsible for reading those `ProblemCluster` rows and turning them into startup dossiers and marketing assets.

---

### 👤 Engineer 1: Data & Discovery Lead (Top of Funnel)
**Goal:** Get raw internet data into the system, extract the pain points, and cluster them mathematically.

**Core Responsibilities:**
* **Phase 3 (Ingestion & Normalization):** Build the Reddit scraper (`src/ingestion/reddit_miner.py`) to pull raw complaints and save them as `Evidence` in the DB.
* **Phase 3.5 (Extraction):** Route the raw evidence to the Fast Tier LLM to extract structured `PainPoint` JSONs.
* **Phase 4 (Clustering Engine):** Build the script that generates embeddings for the pain points and mathematically groups them into `ProblemCluster` entries in the DB.
* **Future (Phase 7):** Expand ingestion to YouTube and Google Trends.

---

### 👤 Engineer 2: Reasoning & Product Lead (Bottom of Funnel)
**Goal:** Take mathematical clusters of complaints and use deep AI reasoning to invent startup concepts and marketing assets.

**Core Responsibilities:**
* **Phase 5 (Opportunity Engine):** Integrate the JEV Decision Model to evaluate the `ProblemCluster` rows (e.g., *Is this commercially relevant?* *Is it specific enough?*) and advance them to `Opportunity` candidates.
* **Phase 6 (Deep Analysis):** Build the prompt chains for the Deep Tier LLM to analyze a qualified Opportunity and invent a full **Opportunity Dossier** (business model, pricing, target user).
* **Phase 9 (Diffusion Layer):** Build the pipelines that take the final Dossier and automatically generate the end-products (SEO briefs, landing page copy, cold emails).
* **Future (Phase 8):** Build the real-world validation scripts (demand testing).

---

### How You Work in Parallel Today:
1. **Engineer 1** starts building `reddit_miner.py` and checking that it successfully inserts `Evidence` into the database.
2. **Engineer 2** doesn't need to wait for Engineer 1. Engineer 2 can manually insert a fake `ProblemCluster` into the database and immediately start building the **Opportunity Engine** and **Diffusion Layer** using that mock data.
