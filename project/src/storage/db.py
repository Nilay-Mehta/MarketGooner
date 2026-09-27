import sqlite3
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# =====================================================================
# CANONICAL SCHEMAS (Phase 1)
# =====================================================================

class Evidence(BaseModel):
    """Raw data collected from a source."""
    id: str = Field(description="Unique identifier for the evidence")
    source: str = Field(description="Platform name (e.g., 'reddit', 'youtube')")
    source_id: str = Field(description="Original ID on the platform")
    url: str = Field(description="URL to the original content")
    timestamp: str = Field(description="ISO 8601 timestamp of creation")
    author: str = Field(description="Author or channel name")
    text: str = Field(description="The raw text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific metadata (upvotes, views, etc)")

class Observation(BaseModel):
    """A structured insight extracted from raw Evidence."""
    id: str
    evidence_id: str
    summary: str = Field(description="Brief summary of the insight")
    sentiment: str = Field(description="Positive, Negative, Neutral")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PainPoint(BaseModel):
    """A highly specific user problem extracted from Observations."""
    id: str
    problem: str = Field(description="The core problem described")
    affected_user: str = Field(description="Who is experiencing this problem?")
    category: str = Field(description="High-level category of the problem")
    severity: int = Field(description="1-10 severity score", ge=1, le=10)
    evidence_ids: List[str] = Field(description="List of Evidence IDs backing this pain point")
    workaround: Optional[str] = Field(None, description="What the user is currently doing to solve this")
    embeddings: Optional[List[float]] = Field(None, description="Vector representation for clustering")

class ProblemCluster(BaseModel):
    """Mathematical grouping of similar PainPoints."""
    id: str
    canonical_problem: str = Field(description="The synthesized overarching problem")
    pain_point_ids: List[str] = Field(description="PainPoints belonging to this cluster")
    unique_users: int = Field(description="Number of unique users experiencing this")
    source_diversity: int = Field(description="Number of unique sources/platforms")
    growth_signal: float = Field(default=0.0, description="Calculated momentum of the problem")

class Opportunity(BaseModel):
    """A validated market gap advanced from a ProblemCluster."""
    id: str
    cluster_id: str
    concept: str = Field(description="High-level description of the solution/startup idea")
    target_customer: str
    existing_alternatives: List[str]
    commercial_relevance: int = Field(ge=1, le=10)

# =====================================================================
# STORAGE MANAGER
# =====================================================================

class StorageManager:
    """Manages the persistence of Canonical Schemas into SQLite."""
    
    def __init__(self, db_path: str = "data/market_intelligence.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path, uri=True) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    source TEXT,
                    source_id TEXT,
                    url TEXT,
                    timestamp TEXT,
                    author TEXT,
                    text TEXT,
                    metadata TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pain_points (
                    id TEXT PRIMARY KEY,
                    problem TEXT,
                    affected_user TEXT,
                    category TEXT,
                    severity INTEGER,
                    workaround TEXT,
                    evidence_ids TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS clusters (
                    id TEXT PRIMARY KEY,
                    canonical_problem TEXT,
                    pain_point_ids TEXT,
                    unique_users INTEGER,
                    source_diversity INTEGER,
                    growth_signal REAL
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS opportunities (
                    id TEXT PRIMARY KEY,
                    cluster_id TEXT,
                    concept TEXT,
                    target_customer TEXT,
                    existing_alternatives TEXT,
                    commercial_relevance INTEGER
                )
            ''')
            conn.commit()

    def save_evidence(self, ev: Evidence):
        with sqlite3.connect(self.db_path, uri=True) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO evidence (id, source, source_id, url, timestamp, author, text, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ev.id, ev.source, ev.source_id, ev.url, ev.timestamp, ev.author, ev.text, json.dumps(ev.metadata)))
            conn.commit()
            
    def save_pain_point(self, pp: PainPoint):
        with sqlite3.connect(self.db_path, uri=True) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO pain_points (id, problem, affected_user, category, severity, workaround, evidence_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (pp.id, pp.problem, pp.affected_user, pp.category, pp.severity, pp.workaround, json.dumps(pp.evidence_ids)))
            conn.commit()
            
    def save_cluster(self, cluster: ProblemCluster):
        with sqlite3.connect(self.db_path, uri=True) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO clusters (id, canonical_problem, pain_point_ids, unique_users, source_diversity, growth_signal)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (cluster.id, cluster.canonical_problem, json.dumps(cluster.pain_point_ids), cluster.unique_users, cluster.source_diversity, cluster.growth_signal))
            conn.commit()
            
    def save_opportunity(self, opp: Opportunity):
        with sqlite3.connect(self.db_path, uri=True) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO opportunities (id, cluster_id, concept, target_customer, existing_alternatives, commercial_relevance)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (opp.id, opp.cluster_id, opp.concept, opp.target_customer, json.dumps(opp.existing_alternatives), opp.commercial_relevance))
            conn.commit()

    def get_unprocessed_evidence(self, limit: int = 50):
        import json
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute("""
                SELECT id, source, source_id, url, timestamp, author, text, metadata 
                FROM evidence 
                WHERE id NOT IN (
                    SELECT json_each.value FROM pain_points, json_each(pain_points.evidence_ids)
                ) LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [Evidence(id=r[0], source=r[1], source_id=r[2], url=r[3], timestamp=r[4], author=r[5], text=r[6], metadata=json.loads(r[7])) for r in rows]

    def get_unclustered_pain_points(self):
        import json
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute("""
                SELECT id, problem, affected_user, category, severity, workaround, evidence_ids 
                FROM pain_points 
                WHERE id NOT IN (
                    SELECT json_each.value FROM clusters, json_each(clusters.pain_point_ids)
                )
            """)
            rows = cursor.fetchall()
            return [PainPoint(id=r[0], problem=r[1], affected_user=r[2], category=r[3], severity=r[4], workaround=r[5], evidence_ids=json.loads(r[6])) for r in rows]

    def get_unevaluated_clusters(self):
        import json
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute("""
                SELECT id, canonical_problem, pain_point_ids, unique_users, source_diversity, growth_signal 
                FROM clusters 
                WHERE id NOT IN (SELECT cluster_id FROM opportunities)
            """)
            rows = cursor.fetchall()
            return [ProblemCluster(id=r[0], canonical_problem=r[1], pain_point_ids=json.loads(r[2]), unique_users=r[3], source_diversity=r[4], growth_signal=r[5]) for r in rows]

    def get_opportunities(self):
        import json
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute('SELECT id, cluster_id, concept, target_customer, existing_alternatives, commercial_relevance FROM opportunities')
            rows = cursor.fetchall()
            return [Opportunity(id=r[0], cluster_id=r[1], concept=r[2], target_customer=r[3], existing_alternatives=json.loads(r[4]), commercial_relevance=r[5]) for r in rows]
