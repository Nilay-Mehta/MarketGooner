# HANDOFF — Market Intelligence Engine

You've been handed a working-but-flawed pipeline that mines public discussions to surface non-generic business opportunities for a founder. Your job is to finish it per the specifications in this folder.

**Do NOT start coding until you have read all five documents in order.** They are dependency-ordered — later docs assume you know earlier docs.

---

## Reading order (mandatory)

| # | Document | What it tells you | Read time |
|---|---|---|---|
| 1 | [01_VISION_AND_PRINCIPLES.md](01_VISION_AND_PRINCIPLES.md) | Why the project exists, who the user is, the 5 non-negotiable principles, success criteria, scope in/out | 15 min |
| 2 | [02_CURRENT_STATE_AUDIT.md](02_CURRENT_STATE_AUDIT.md) | What's already in `D:\Start\`, what works, what to KEEP/DELETE/REFACTOR, DB state, LOC estimates | 15 min |
| 3 | [03_TARGET_ARCHITECTURE.md](03_TARGET_ARCHITECTURE.md) | Multi-agent design, model tier cascades, local runtime choice (llama.cpp adopted), storage, dual output shape | 20 min |
| 4 | [04_IMPLEMENTATION_ROADMAP.md](04_IMPLEMENTATION_ROADMAP.md) | Phase 0–9 execution plan, 30+ ready-to-paste Antigravity briefs, failure protocol | 25 min |
| 5 | [05_OPERATIONS_AND_ANTIPATTERNS.md](05_OPERATIONS_AND_ANTIPATTERNS.md) | Daily runbook, verification checklist for every AG completion claim, failure catalogue with 12 specific past incidents, trust contract with AG | 20 min |

Total onboarding: **~1.5 hours of reading before you touch code.** Do not skip.

---

## First day action

After reading:

1. **Phase 0 in doc 04** — backup the DB, archive briefs, clean stale files, verify handoff docs exist.
2. **Phase 1 in doc 04** — model tier split in `key_manager.py` + route `idea_ranker.py` to deep tier + verify.

That's it for day 1. Do not do Phase 2 until Phase 1's verification passes.

---

## Rules of engagement (non-negotiable)

1. **One thing at a time.** Every code change is a single atomic step with a verification. No bundling.
2. **Do not trust AG's completion summaries.** Run the verification checklist in doc 05 §2 every time.
3. **No principle violations.** If a proposed change violates any of the 5 principles in doc 01, reject it or rewrite it.
4. **When in doubt, halt.** Escalate to the founder per doc 05 §9 rather than making a call.
5. **No paid APIs. Ever.** Founder constraint. Card-required tiers count as paid.

---

## Where things live

- **Code:** `D:\Start\project\` (Python 3.11+)
- **Data:** `D:\Start\project\data\intel.db` (SQLite — has 1,548 real raw items, 1,146 pain points, 46 real WTP rows — DO NOT WIPE)
- **DB backups:** `D:\Start\project\data\intel.db.bak.YYYYMMDD` (create on day 1)
- **Knowledge vault:** `D:\Start\Market_Intelligence_Vault\` (Obsidian, human-readable playbooks, keep as living reference)
- **Founder's context:** `D:\Start\Sahil_Goel_Insights.docx` (the painkiller/vitamin thesis, 100Cr math, D2C micro-niches)
- **Environment:** `D:\Start\.env` and `D:\Start\project\.env` (LLM provider keys)
- **Reference research:** `D:\Start\RESEARCH_REPO_LANDSCAPE.md` (repo landscape survey)

---

## Where to ask for help

- **Architecture question you can't resolve from these docs:** escalate to the founder (per doc 05 §9).
- **AG produced garbage:** doc 05 §3 (failure catalogue) probably names your symptom. If not, add a new entry once you diagnose it.
- **You want to add a new source / provider / agent:** doc 05 §7 (change management) has the process.

---

## Success criteria (from doc 01 §5, restated so you can't miss them)

You are done when all five are true after a real run:

1. At least one candidate wedge is defensible (5+ WTP evidence from 3+ platforms, preserved proper noun, non-declining trend).
2. The founder can name three humans to DM within an hour of reading the dossier.
3. Every claim in both outputs traces to a source URL.
4. A full run completes in under 60 minutes OR halts honestly with a resume path.
5. A new engineer can produce a valid run within one working day using only these five documents.

Anything less is not "mostly done." It is broken. Fix before shipping the next feature.

---

Now go read [01_VISION_AND_PRINCIPLES.md](01_VISION_AND_PRINCIPLES.md).
