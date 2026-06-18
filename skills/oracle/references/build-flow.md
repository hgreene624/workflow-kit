# Build flow + research/expand + audit/revalidate procedures

The skill orchestrates; **every deterministic step shells out to `oracle-forge`** (gate, qualify, snapshot, load, audit, revalidate, metrics). No gate math, cap, or metric is computed in the skill. The agent's only judgment seam is the three sub-scores (Authority / Alignment / Depth) and the stance tags; these are routed to **operator review** on early builds (§16) before they gate anything. Carried-forward discipline from the prior system (dual-registry resolution, atomic supersession / no-two-canonicals, the bot-block ladder) is now enforced by `oracle-forge`.

---

## `/oracle build` — the §6 Phase 0–8 flow

### Phase 0 — Grounding Brief
Run the 8-question elicitation, one question at a time (`references/grounding-brief.md`). Emits the **charter** (scope/objectives/values), the **labeled thesis-hypothesis**, and the two **mandatory, non-skippable** acquisition tasks (steelman from Q7, disconfirmer from Q8). These tasks go on the build's task list now and are enforced at G2.

### Phase 1 — Taxonomy
Define the buckets by their **key questions** + **required perspective spread** — **NOT a target source count.** Each bucket states: which key questions it must answer, and which stances it must span (it must end with both a `challenging` and a `foundational-neutral` source — that spread, not a number, is the target). The charter's objectives drive the key questions; the hypothesis + its mandated dissent drive the required spread.

### Phase 2 — Candidate discovery
Write **PRISMA inclusion/exclusion criteria up front** (what qualifies a candidate, what disqualifies it) before gathering. Then gather candidates per bucket. **NLM Discover is SCOUT-ONLY** — it surfaces candidates but is **NEVER an auto-load step** (it auto-pulls bare-URL teasers); every candidate it surfaces goes back through the §7/§8 gate and is re-ingested as full text. **De-dup against circular reporting** — many "sources" tracing to one origin count as one.

### Phase 3 — Curation pipeline (owned)  → G1
Per candidate, in order:
1. `oracle-forge fetch <url>` → resolve to the real asset via the bot-block ladder (`--out` to save bytes).
2. `oracle-forge extract <path>` → developed full-text body + metrics.
3. `oracle-forge gate <path>` → **Gate 0, the full-text hard gate.** FAIL → auto-F, reject, **log the rejection reason**, move on (do not ingest).
4. **Agent sub-scores (the ONLY LLM seam) — two masked passes:** score **Authority with the body masked** (byline/masthead only) and **Alignment with the byline masked** (content only), in separate passes; then Depth. Then `oracle-forge qualify --alignment A --authority B --depth C [cap flags]` → composite → letter → caps → disposition. Never compute the letter or cap by hand.
5. **Operator review** of the agent sub-scores + stance on early builds (§16) before they gate.
6. `oracle-forge snapshot <path> ...` → content-hashed, append-only snapshot to the corpus tree.
7. Stamp the record (type · sub-scores · composite · letter · disposition · stance · map-placement · snapshot-ref · rejection-reason). **Log every rejection.**

This is **G1 ingest**: full-text-or-quarantine + snapshot + authority recorded.

### Phase 4 — Load
Push **only verified full-text** sources whose disposition is `citable` into NLM via `oracle-forge load --notebook-id … --file <path>` or `--text <…>` — **NEVER a URL** (the loader refuses non-citable and has no URL path; G4 / §13 forbid bare URLs). Right-size to NLM limits; the loader splits mega-docs.

### Phase 5 — Coverage + balance audit  → G2
Build the question × source matrix: each key question grounded by ≥1 Tier-1 source across the required perspectives; per-bucket balance check. **This is where the steelman + disconfirmer tasks are enforced** — a bucket with no `challenging` source fails G2. Gaps **commission** steelman/disconfirmer curation (loop back to Phase 3 for those). G2 needs ≥0.90 key-Qs grounded across required perspectives.

### Phase 6 — Grounding  → G3
Synthesis queries via the `nlm` CLi with **verbatim-quote-then-cite** discipline: every load-bearing claim traces to a full-text locator; **anti-paraphrase**; **STOP-on-contradiction** (do not synthesize through a contradiction — surface it).

### Phase 7 — Audit outputs
`oracle-forge audit <oracle> --manifest <manifest.json> --input <audit-input.json>` emits **all six §12 outputs** + the §11 dashboard: (1) Source-Quality Audit (2) Perspective-Balance report (3) Coverage/traceability matrix (4) Per-gate pass/fail log (5) metric dashboard (6) Source Qualification Report + 2×2 map. **No clean audit → not canonical.**

### Phase 8 — Maintenance  → G4
Schedule the link-rot / content-drift re-check (`oracle-forge revalidate`); CREW/MUSTIE weeding (the criteria that justify adding justify removing).

### Register (resolve-at-runtime convention)
On a successful build, register the new oracle in **both** the project PJL `oracles:` frontmatter and the vault Oracle Registry (`04_Reference/Oracle Registry.md`) — `status: canonical` for a first build, `candidate` for a same-scope rebuild (no two canonicals; supersession is atomic). Never hardcode the id anywhere; these registries ARE the runtime resolution source.

---

## `/oracle research` (alias `/oracle expand`)

Expand an existing oracle. Resolve the target oracle at runtime (PJL + Registry; fail-to-ask on ambiguity). Then add the new sources / new key-questions through the **SAME §7/§8 gate** as `build` Phase 3 — `fetch → extract → gate → sub-scores → qualify → operator review → snapshot → stamp` — and **re-ingest each as full text via `oracle-forge load` (file/text), never a bare URL.** New key-questions extend the taxonomy and must meet the same required perspective spread (steelman/disconfirmer if the new area is thesis-adjacent). Re-run `oracle-forge audit` after expanding; update the PJL/Registry source counts.

---

## `/oracle audit` (alias `/oracle revalidate`)

Resolve the target oracle at runtime. Then:
- **audit:** `oracle-forge audit <oracle> --manifest <manifest.json> --input <audit-input.json>` → re-emit the six §12 outputs + the §11 dashboard for the existing oracle. Surface any unhealthy metric or gate-fail. (Live counts derive from NLM + the snapshot/manifest, never the registry — the tool enforces this.)
- **revalidate:** `oracle-forge revalidate <oracle> --input <reval-input.json>` → the **G4** scheduled check: re-fetch each source via the live ladder and **hash-compare live vs snapshot** (not just HTTP-200). Flag `rot` (unreachable) / `drift` (bytes changed) and queue re-grounding for anything that needs it.

Both are read-mostly; neither relitigates design. Report results, don't silently fix.
