---
name: oracle
description: "Next-gen oracle skill — build, expand, ask, and audit a research-grade, perspective-balanced NotebookLM oracle. Use when the user says build an oracle, forge an oracle, expand/research the oracle, audit the oracle, revalidate the oracle, asks the oracle a grounded question, or says ask the oracle / check with the oracle / what does the oracle say. Also called inline by other skills (create-note, grill, implement) at design decision points. Orchestrates the oracle-forge CLI (deterministic pipeline) + the nlm CLI (synthesis). THE oracle skill — the retired oracle-create / oracle-research / oracle-ask family was superseded 2026-06-10 (P6 cascade)."
---

# Oracle

One skill that **owns the curation pipeline and rents the synthesis.** It builds, expands, queries, and audits an *oracle* — a research-grade, values-aware, perspective-balanced NotebookLM source of truth whose every citation is **developed full-text, never a teaser**, deliberately spanning sources that **build on** the operator's thesis and sources that **challenge** it.

**The skill orchestrates; the tool does the deterministic work.** All gate math, caps, composite scoring, metric formulas, fetch/extract/snapshot/load/audit/revalidate live in the **`oracle-forge` CLI**, never restated here. Synthesis (grounded query, citations) is rented from the **`nlm` CLI** / NotebookLM. This skill wires those two together and runs the human-judgment seams (the Grounding Brief, sub-score review, stance review).

Design authority: [[SPC - 2026-06-06 - Next-Gen Oracle Skill (Full Design Spec)]] (§-references throughout point at it). Carried-forward discipline from the prior system: dual-registry runtime resolution, atomic supersession / no-two-canonicals, the bot-block fallback ladder — all now enforced by `oracle-forge`.

## Scope note (supersession complete — 2026-06-10)

This skill **superseded** `oracle-create` / `oracle-research` / `oracle-ask` + [[SD - Oracle System]] (archived) in the P6 cascade on 2026-06-10. The old family is retired; this skill now owns ALL oracle triggers, including the bare "ask the oracle". Inline callers (`create-note` — which absorbed create-spec/design —, `grill`, `implement`) are repointed to `/oracle ask`; the `create-plan` repoint is operator-owned (backup-only skill). The historical parallel-then-retire sequencing (CL-2) is documented in [[PL - 2026-06-06 - Next-Gen Oracle Skill (oracle-forge) Implementation Plan]].

## The CLI it calls

`oracle-forge` (installed from `~/Repos/oracle-forge`; invoke as `oracle-forge <subcommand>` or `~/Repos/oracle-forge/.venv/bin/oracle-forge`). JSON in / JSON out. The deterministic primitives:

> **Kit prerequisite:** `oracle-forge` is a separate Python CLI, not bundled with the Workflow Kit. Without it, the `build` / `research` / `audit` commands are unavailable — but **`ask` works standalone** (it needs only the `nlm` CLI + your Oracle Registry / PJL `oracles:` blocks), so inline callers (create-note, grill, implement) degrade gracefully.

| Subcommand | What it does (deterministic) |
|---|---|
| `fetch <url>` | Walk the bot-block fallback ladder to the real asset. |
| `extract <path>` | Developed full-text body + structural metrics. |
| `gate <path>` | Gate 0 — the full-text hard gate (§7 dim 0). |
| `qualify` | Composite → letter → caps → disposition from the three sub-scores (§8). |
| `snapshot <path>` | Content-hash + append-only snapshot to the corpus tree. |
| `load` | Push verified full-text to nlm (`--file`/`--text`, **never `--url`**). |
| `audit <oracle>` | All six §12 build outputs + the §11 dashboard. |
| `revalidate <oracle>` | G4 — re-fetch + hash-compare live vs snapshot. |
| `metrics` | The five §11 metrics (anti-Goodhart dashboard). |

The **only** non-deterministic seam is the agent supplying the three judgment **sub-scores** (Authority / Alignment / Depth) and the **stance tags** — which the tool records, gates on, and routes to operator review (§16). Never compute a gate result, a cap, a letter, or a metric by hand — always shell out to `oracle-forge`.

## Commands

### `/oracle build`
Stand up a **new** oracle through the full §6 Phase 0–8 build flow, opening with the 8-question Grounding Brief. The replacement for `oracle-create`.
→ Procedure: `references/build-flow.md`. Grounding Brief: `references/grounding-brief.md`.

### `/oracle research` (alias `/oracle expand`)
**Expand** an existing oracle — add sources / new key-questions — through the **same** §7/§8 gate (re-ingested as full text, never a bare URL). The replacement for `oracle-research`.
→ Procedure: `references/build-flow.md` § "research / expand".

### `/oracle ask`
**Grounded query** with verbatim-quote-then-cite (G3). Returns the standard oracle proposition. **Preserves the `oracle-ask` proposition/return contract** the five inline callers depend on (P6's caller-contract test checks this).
→ Procedure + the exact return contract: `references/ask-contract.md`.

### `/oracle audit` (alias `/oracle revalidate`)
Re-run the six §12 outputs + the G4 scheduled check on an existing oracle via `oracle-forge audit` / `oracle-forge revalidate`. `audit` = full output set + dashboard; `revalidate` = the G4 live-vs-snapshot hash check only.
→ Procedure: `references/build-flow.md` § "audit / revalidate".

## Resolve the oracle at RUNTIME — never hardcode

For every command that targets an **existing** oracle (`ask`, `research`/`expand`, `audit`/`revalidate`), resolve which oracle to use at runtime — **never hardcode a notebook id or a corpus path**:

1. Read the current project's PJL `oracles:` frontmatter **and** the vault Oracle Registry (`04_Reference/Oracle Registry.md`).
2. Match the request's domain against each oracle's `domains` / `scope`. Prefer `status: canonical`.
3. **One match** → use it. **Multiple** (e.g. canonical + candidate) → present them via AskUserQuestion, canonical as default. **None** → say so; for `ask`, exit gracefully (advisory, never blocking); for the others, offer `/oracle build`.
4. **Fail-to-ask on ambiguity.** Never guess an id.

The `oracle-forge` install path (`~/Repos/oracle-forge`) is the *tool* location and may be referenced as such — that is fine. It is the **oracle DATA** (notebook id, corpus tree) that must be resolved at runtime, never baked into a command.

## Honest-claims posture (mandatory — do not soften, do not overclaim)

The perspective-balance / debiasing techniques in this skill (the Grounding Brief's steelman + disconfirmer mandate, devil's-advocacy queries, the stance-balance check) are **procedural forcing functions, not proven bias cures.** The empirical record on whether such procedures actually *reduce* confirmation bias is **mixed** (Dhami 2019; pre-registered studies; T&F 2023). The defensible claim is: *"procedural forcing functions beat good intentions."* This skill **never claims** it achieves a neutral, unbiased, or bias-free corpus — it claims only that it *forces* dissent and full-text grounding into the process and *makes the result auditable.* Report findings in those terms; do not market a debiasing guarantee. (§15.)

## Error handling (advisory, never blocking)

Oracle input is advisory. On any failure — nlm auth expired, query timeout, empty result, oracle-not-found, `oracle-forge` non-zero exit — **exit gracefully and let the calling workflow continue.** For `ask` called inline, return nothing (or a one-line "oracle unavailable") rather than raising, so the five callers never break. For nlm auth, attempt `nlm login` guidance once. Never leave a half-written registry/PJL entry.
