# `/oracle ask` — grounded query + the preserved proposition contract

`ask` queries an existing oracle and returns a grounded **proposition** for the operator to evaluate. The oracle informs; the operator decides. This command **preserves the exact `oracle-ask` proposition/return contract** the inline callers depend on — today `create-note` (which absorbed create-spec/design), `grill`, and `implement`; the `create-plan` repoint is operator-owned. (Verified by P6's named caller-contract test, passed 2026-06-10.)

## Step 1 — resolve the oracle at runtime (never hardcode)

Read the current project's PJL `oracles:` frontmatter **and** the vault Oracle Registry (`04_Reference/Oracle Registry.md`). Match the question's domain against each oracle's `domains` / `scope`; **prefer `status: canonical`**. Never hardcode a notebook id or path.

- **One match** → use it.
- **Multiple** (e.g. canonical + candidate) → present via AskUserQuestion, canonical as default. *(Skip this when called inline — see below; default to canonical.)*
- **None** → standalone: offer `/oracle build`; inline: return nothing and let the caller continue.

## Step 2 — query with G3 discipline (verbatim-quote-then-cite)

Query the resolved notebook via the `nlm` CLI (`nlm` query, or the async start/status path for heavy synthesis). Apply **G3 grounding discipline**:

- **Verbatim-quote-then-cite.** Every load-bearing claim in the answer must trace to a **full-text locator** — quote the supporting passage, then cite its source. No paraphrase drift, no claim beyond the cited passage.
- If the sources do not support a claim, do not make it. **STOP-on-contradiction** — if sources conflict, surface the conflict rather than smoothing it over.

## Step 3 — return in the EXACT proposition shape (do not alter)

Format the answer as the standard oracle proposition — **this exact shape is the contract; preserve it byte-for-byte in structure:**

```
> **Oracle ({source_count} sources):** {insight}
> *Sources: {citation 1}, {citation 2}*
> {question or decision prompt to user}
```

- `{source_count}` — the live source count of the resolved oracle.
- `{insight}` — the grounded synthesis, built under the G3 quote-then-cite rule above.
- `{citation 1}, {citation 2}` — the full-text sources the insight traces to.
- `{question or decision prompt to user}` — the decision the proposition frames (the oracle informs, the operator decides).

## Standalone vs inline

- **Standalone** (`/oracle ask <question>`): if a question was supplied, use it; else ask via AskUserQuestion "What do you want to ask the oracle?" Present the proposition; offer a follow-up loop.
- **Inline** (called from another skill at a decision point): the calling skill supplies the context and question — **skip AskUserQuestion** and **return the formatted proposition back** to the caller, which incorporates it before its own question. The proposition *frames* the caller's question; it never constrains the answer.

## Error handling — advisory, NEVER blocking

Every failure mode exits gracefully so the caller continues; the oracle is advisory, never a blocker:

- **Auth failure** — guide the operator to `nlm login` once; then proceed without oracle input.
- **Query timeout** — "Oracle query timed out; proceeding without oracle input."
- **Empty result** — "No relevant results; the sources may not cover this — consider `/oracle research`." Proceed.
- **Oracle not found / deleted** — say so (offer `/oracle build` or a stale-entry cleanup); proceed.

In all cases, **inline callers get a clean continue** (return nothing or a one-line note) — never an exception that breaks `create-spec` / `design` / `grill` / `create-plan` / `implement`.
