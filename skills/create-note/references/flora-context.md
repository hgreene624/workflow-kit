# {{ORG}} Ecosystem -- Technical Context

Single source of truth for the concept-brief skill. Covers every deployed system, its entity model, capabilities, and limitations. Updated by the development team when systems change.

Last updated: 2026-04-13

---

## 1. Platform Overview

The system is a suite of web apps for managing hospitality operations (restaurant group, vacation rentals, real estate) in Baja California, Mexico. All apps live in a single Next.js/Python monorepo and deploy as Docker containers behind Traefik reverse proxy on a VPS at YOUR_DOMAIN. Database: PostgreSQL 17 (`{{PROJECT_DB}}`). Auth: Microsoft Entra ID (Azure AD) via Auth.js. LLM routing: centralized AI Gateway.

**Users:** ~96 people across 4 departments (Farm Living, Hospitality, Trades & Services, Administration). Organizational tiers: owner, executive, manager, lead, staff, external.

---

## 2. Portal (YOUR_DOMAIN/)

The user's home screen. Odoo-style tile grid with 6 tool tiles: Meetings, Inbox, Tasks, Themes, Settings, and a home icon. Each tile launches a workflow-centric app.

**Architecture:** Config-driven tile array (icon, label, route, description). Minimal top bar with tool name + theme toggle. No persistent sidebar. Responsive grid (3 cols mobile, 4+ desktop).

**Design language:** Earth-tone palette applied across portal, CCP, and home. DaisyUI component library.

**Key principle:** Workflow-centric, not source-centric. Each tile represents a functional area ("this is where I do my email"), not a data source.

---

## 3. {{SIGNAL_ENGINE}} (YOUR_DOMAIN/fwis/)

The org's organizational intelligence layer. The authoritative reference is the [[SD - {{SIGNAL_ENGINE}} System Definition]] at `02_Projects/{{ORG}} Intelligence/`. All concept briefs touching {{SIGNAL_ENGINE}} should read the SD. This section is a summary.

### 3.1 What {{SIGNAL_ENGINE}} Is

{{SIGNAL_ENGINE}} builds a structured understanding of the organization by answering three questions:

- **What is the org?** Organizational identity: people, roles, departments, reporting chains, business entities. Fed by systems of record (Odoo HR, accounting) and supplemented by observation. First-class intelligence dimension with position/person separation, temporal assignments, and multi-identifier entity resolution.
- **What is the org doing?** Observed activity attributed to projects, initiatives, and people. Built automatically from work streams (email, meetings, conversations) and work artifacts (documents, KB edits, spreadsheets). Signal velocity measures attention concentration.
- **What did {{ORG}} commit to?** Decisions, delegations, and promises extracted from organizational activity. Each commitment has a lifecycle: requested, promised, in-progress, fulfilled, broken, renegotiated. Say-Do Ratio (delivered/committed) is the core metric.

**Organizational health** is the coherence across all three answers. Divergences reveal misalignment, stale attributions, broken commitments, and capability gaps.

{{SIGNAL_ENGINE}} also serves as the **knowledge layer** that makes every AI system at {{ORG}} more effective: email triage, KB maintenance, document generation, training content all draw on {{SIGNAL_ENGINE}} organizational intelligence.

### 3.2 Dual World Model

{{SIGNAL_ENGINE}} maintains two parallel world models sharing infrastructure:

- **Operational World Model:** Internal work activity. Entities: initiatives, projects, activities, work items, decisions, vulnerabilities. Answers: What is {{ORG}} doing internally?
- **Market World Model:** External relationship activity. Entities: contacts, profiles, households, relationship stages, lead scores. Enriched by external research (web, public records). Answers: Who is {{ORG}} dealing with?

Email is the shared input source. A routing layer forks signals to one or both models.

### 3.3 Operational Model

Information flows through three layers:
- **Signals Up:** Observe and classify work activity (per-signal interpretation)
- **Sensemaking:** Interpret patterns across signals over time (cross-signal interpretation). System escalates proactively when thresholds are crossed. Humans apply judgment at decision points. Corrections feed back.
- **Tasks Down:** Decisions captured, routed to responsible people, tracked through commitment lifecycle.

### 3.4 Key Concepts

- **Recursive viability:** Each project/initiative has its own instance of the three questions. Health nests upward.
- **DRI ownership:** Initiatives have a Directly Responsible Individual with temporal bounds and review cadence.
- **Suggested before adopted:** All AI-generated intelligence starts as a suggestion. Trust earned through corrections.
- **Eight core principles:** See the SD for the full list.

### 3.5 Current Implementation State

- Signal classification pipeline: live, processing email and meetings
- MIP (Meeting Intelligence Pipeline): live, single-prompt consolidated architecture
- Context Assembler: built, 6 dimensions, 4 modes
- Processing Session Review: partially implemented (38/40 tasks)
- Organizational identity: flat people table (needs elevation to dedicated schema per SD)
- Market World Model: sales extension exists but needs reframing per SD
- Commitment lifecycle: work_items table exists but no Winograd-Flores states
- Initiative hierarchy: flat (no parent/child, no DRI ownership)
- Signal velocity: not implemented
- Organizational health metrics: not implemented
- Corpus search: not implemented

### 3.6 {{SIGNAL_ENGINE}} Viewer

22 admin-facing pages. Primary audience: leadership and management. No employee self-view exists.

---

## 4. Meeting Intelligence Pipeline (MIP)

Single-prompt architecture processing Limitless pendant recordings into structured meeting intelligence.

### 4.1 Pipeline

```
Limitless lifelog --> Speechmatics transcription
  --> prefetch.py (9 context datasets in parallel: people roster, aliases, meeting history, pending actions, themes, adjacent lifelogs, pendant owner, corrections, initiatives)
  --> consolidated_llm.py (single Claude call via CLI shim)
      Output: speaker_map + entity_map + outcomes (JSON-schema validated)
  --> context_assembler generates meeting notes
  --> DB writes + signal injection into {{SIGNAL_ENGINE}}
```

### 4.2 Key Facts

- **Input:** Limitless pendant audio (Patrick wears one). Also processes MS Teams calendar meetings.
- **Speaker attribution:** Confidence levels (high=0.9, medium=0.7, low=0.4). Speechmatics per-device enrollment for speaker ID.
- **Outcomes:** decisions, commitments, action items, status updates, follow-ups. Each deduped via SHA-256 hash on stable inputs.
- **Cost:** ~$0.05 per meeting (70% reduction from multi-step approach)
- **Budget:** 30s per meeting, 300s per batch

### 4.3 Limitations

- Speaker attribution not guaranteed (fallback: "Speaker 1")
- Per-device enrollment required for speaker identification
- No conversation scoring against scripts/rubrics
- No training time classification
- No management conversation analytics
- Action items extracted but not tracked as a system

---

## 5. Portal Work Themes

LLM-based clustering of unthemed work items into coherent topic groups. **Separate from {{SIGNAL_ENGINE}} initiatives** -- themes are a UX layer, not part of the entity model.

### 5.1 Entity Model

| Table | Purpose |
|---|---|
| `portal_themes` | Theme records: title, summary, level (personal/department/organizational), status, priority, snooze_until |
| `portal_theme_items` | Items in a theme: source_type (email/meeting_action_item/meeting_decision/lifelog/signal), source_id, status (pending/handled/skipped) |
| `portal_theme_actions` | Audit trail: email_sent, action_item_completed, theme_dismissed/snoozed/completed |

### 5.2 How It Works

Detection engine runs every 2 hours (VPS Python script). LLM clusters related items (emails, meetings, lifelogs) into themes capped at 10 items. User interacts via chat-first interface that leads with questions, not summaries. Agent drives workflow: draft replies, batch approvals, skip items.

### 5.3 Key Distinction

- **Themes:** Bottom-up pattern discovery. Cross-cutting. Ephemeral/regenerated. "What unexpected patterns exist across my work?"
- **Initiatives:** Top-down strategic intent. Hierarchical. Persistent. "What strategic goals are we working toward?"
- No FK between themes and initiatives. Completely independent systems.

---

## 6. Inbox Tool (specced, not yet built)

The next major build. AI email triage tool with 71 functional requirements.

### 6.1 Five-Section Architecture

| Section | Purpose |
|---|---|
| **Inbox** | Emails grouped by AI-generated topic categories. Filter/sort/regroup controls. |
| **Group Review** | AI-driven triage for a category. Streaming briefing (5 subsections: Timeline, Key Players, Open Decisions, Your Relevance, Follow-Up Actions). Email action queue. |
| **Compose/Reply** | Single-action draft generation. Chat refinement. Send/forward/archive. |
| **Noise Review** | Auto-filtered noise emails (Teams notifications, calendar, noreply). Restore/whitelist. |
| **Settings** | Noise rules, whitelists, category management, sync settings. |

### 6.2 {{SIGNAL_ENGINE}} Integration

The Inbox Tool is the primary consumer of the {{SIGNAL_ENGINE}} Context Assembler. Three endpoints:
- `POST /api/context/user` -- user's initiatives, meetings, work items, blockers
- `POST /api/context/email` -- batch sender profiles (tier, department, reporting structure, initiative overlap)
- `POST /api/sales/context` -- sales pipeline data

**Quality bar:** "Output should feel like a well-informed executive assistant wrote it, not generic AI. If it could be generated by any LLM with just the email text, {{SIGNAL_ENGINE}} integration is failing."

### 6.3 Key Design Decisions

- Categories are persistent, user-managed, AI-proposed entities (not ephemeral)
- Classification has 3 dimensions: Priority (High/Medium/Low), Topic Category, Action Type (Reply Needed/FYI/Delegate/Follow Up)
- Corrections feedback loop: user reclassifications become few-shot guidance for future classification
- 8K token budget for LLM context; dynamic allocation based on {{SIGNAL_ENGINE}} data availability

### 6.4 Blockers (Phase 0 Prerequisites)

- {{SIGNAL_ENGINE}} field alignment: `email` vs `user_email`, `reporting_structure` vs `reports_to_email`
- `/api/context/user` queries wrong table (`work_items` with 0 rows instead of `action_items` with 1,048 rows)
- Table name mismatch: code says `email_sync_state`, actual table is `triage_sync_state`

---

## 7. Knowledge Base (YOUR_DOMAIN/kb/)

Company knowledge management platform. Bilingual (EN/ES).

### 7.1 Content Model

```
Knowledge Base (kb.knowledge_bases)
  --> Bucket Group (kb.bucket_groups) -- e.g., "Front of House"
      --> Bucket (kb.buckets) -- e.g., "Service Standards"
          --> Brief (kb.briefs) -- individual articles, TipTap JSON content
              --> Brief Versions (kb.brief_versions) -- version history with rollback
```

4 KBs: Farm Living (Jenny), Hospitality (Manuel), Trades & Services (Manuel), Administration (Luis Galicia).

### 7.2 Features

- **Structure Manager** (admin): tree view with drag-and-drop reorder, CRUD for groups/buckets/briefs. Non-technical staff can reorganize KB structure.
- **Edit workflow:** Editors submit as "Publish" (live) or "Review" (staged). Reviewers see side-by-side word-level diff. Approve/reject with comments.
- **Search:** Hybrid keyword (PostgreSQL tsvector) + semantic (Claude RAG via AI Gateway)
- **AI Chat Widget:** RAG-powered Q&A against KB content. Suggests edits as DB drafts.
- **AI Suggestions:** Context-aware edit suggestions (Sonnet model, sibling brief context)
- **Theming:** Per-KB CSS custom properties, 30 palettes available
- **Version history:** DB-backed rollback to any previous version

### 7.3 Limitations

- No freshness tracking ("last verified accurate" date)
- No signal-to-KB comparison ({{SIGNAL_ENGINE}} doesn't check if work matches KB procedures)
- No drift detection (KB vs actual operations)
- No adherence scoring
- No content health metrics or analytics dashboard
- No translation status dashboard
- No public-facing pages (auth required)

---

## 8. Document Generator (YOUR_DOMAIN/docgen/)

AI-assisted document creation platform.

### 8.1 Features

- 5-phase guided creation: context assembly > clarification > source review > generation > editorial chat
- Template system for SOPs, reports, policies, PIPs
- Bilingual generation (EN/ES) with translate module
- Inline citations with 100% accuracy (citation spike validated)
- Export: DOCX and PDF with citation endnotes
- Editorial chat for post-generation refinement
- Links to KB briefs as reference documents

### 8.2 Entity Model

| Table | Purpose |
|---|---|
| `docgen.documents` | Generated documents with knowledge_base_id, bucket_id links |
| `docgen.templates` | Document type templates |
| `docgen.reviews` | Review/approval records |
| `docgen.ai_traces` | LLM call audit trail |
| `docgen.reference_documents` | Source material links |
| `docgen.generation_jobs` | Async generation tracking |

### 8.3 Limitations

- No reverse flow (document changes don't update KB)
- NotebookLM integration partial (Phases 0-2, blocked on knowledge_base_id)
- Intelligent Content Generation spec ready but not implemented (v2.0)

---

## 9. Culinary Cottages Portal (YOUR_DOMAIN/ccp/)

Vacation rental owner portal for ~260 property owners.

- Property information, documents, financial summaries
- Voting system for community decisions
- Real-time chat rooms per property/topic
- Earth-tone design, Editorial Quiet palette
- Phase 7 cutover in progress: bulk signup emails, Patrick UAT

---

## 10. AI Gateway (internal, port 3456)

Multi-provider LLM routing platform.

### 10.1 Architecture

4 adapters: `claude-api` (Anthropic API, full params), `claude-cli` (Max plan, $0, limited params), `openai` (Chat Completions), `gemini` (Google API).

3 capability tiers: fast (Haiku/gpt-4.1-mini/Flash), reasoning (Sonnet/gpt-4.1/Pro), creative (Opus).

### 10.2 Routing

Evaluates required capabilities (temperature? streaming? tools? json_schema?) + consumer priority (cost/quality/latency) + adapter health. Auto-escalates if preferred adapter lacks capability. Failover on 429/503/timeout.

### 10.3 Key Facts

- 13+ {{ORG}} consumers route through gateway
- Per-consumer cost limits (monthly cap)
- Prompt caching on claude-api (system + last 3 user messages)
- Streaming normalized to OpenAI SSE format
- Response headers: X-{{ORG}}-Provider, X-{{ORG}}-Tier, X-{{ORG}}-Routed-Reason
- Claude CLI adapter cannot forward temperature or structured output (escalates to API)

---

## 11. Infrastructure

- **VPS:** Hostinger, IP YOUR_VPS_IP, Traefik reverse proxy
- **Routing:** Path-based (YOUR_DOMAIN/app/), not subdomains
- **Auth:** Microsoft Entra ID, ForwardAuth middleware
- **DB:** PostgreSQL 17 ({{PROJECT_DB}} database), schemas: public, kb, docgen, sales, inbox (new)
- **CI/CD:** GitHub Actions, workflow_dispatch (push != deploy)
- **Monitoring:** Uptime Kuma, admin error reporting across 14 services
- **MS Graph:** Email, calendar, planner, Teams chat integration
- **Limitless:** REST API for lifelog ingestion from pendant devices

---

## 12. What's Being Built Next

1. **Inbox Tool** -- specced (71 FRs), implementation plan next. Critical path: {{SIGNAL_ENGINE}} field alignment.
2. **CCP Phase 7 Cutover** -- bulk signup to ~260 owners, Patrick UAT
3. **Initiative Hierarchy Redesign** -- add parent/child so initiatives can nest (strategic > project > work item)
4. **KB Signal Matching** -- classify {{SIGNAL_ENGINE}} signals against KB articles for drift detection
5. **Earth-tone design unification** -- extend palette to KB, admin, {{SIGNAL_ENGINE}} viewer

---

## 13. Terminology Guide

| Stakeholder might say | {{ORG}} term | What it actually is |
|---|---|---|
| "The system that reads my emails" | {{SIGNAL_ENGINE}} Signal Engine | Email classification pipeline producing weighted signals |
| "My recording device" | Limitless pendant | Personal audio recorder, NOT called Omi in {{ORG}} |
| "The knowledge base" | {{ORG}} KB | 4-department bilingual KB at YOUR_DOMAIN/kb/ |
| "Documents" / "SOPs" | DocGen | AI-assisted document creation tool |
| "Initiatives" | {{SIGNAL_ENGINE}} initiatives | Currently project-level entities, hierarchy redesign planned |
| "Themes" | Portal Work Themes | LLM-clustered topic groups, separate from initiatives |
| "The portal" | {{ORG}} Portal | Tile-grid launcher at YOUR_DOMAIN/ |
| "The inbox" / "email tool" | Inbox Tool | Specced but not yet built (71 FRs) |
| "Scores" / "ratings" | Signal weights | 0-10 scale, tier x action type |
| "Who reports to who" | People table | reports_to_email field, tier assignments |
| "Scripts" / "conversation scoring" | Does not exist | No script primitive or scoring engine in any {{ORG}} system |
| "PIP" / "performance plans" | Does not exist | No PIP tracking in any {{ORG}} system |
| "Screen monitoring" | Does not exist | No screen capture or activity monitoring |
| "Employee dashboard" | Does not exist | {{SIGNAL_ENGINE}} viewer is admin-only; no employee self-view |
