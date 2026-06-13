# AI-Memory Retrieval Engine (Phase 1: keyword + wikilink arms)

Standalone, markdown-only retrieval over the Work Vault corpus. Implements
**FR-5** (keyword/BM25 arm) and **FR-6** (wikilink/backlink 1-hop expansion)
of [[SPC - AI-Memory Vault]] / [[PL - AI-Memory Vault Phase 1]] (Tasks 12, 13, 14).

No vector/embedding index (that is Phase 2, FR-10). No Postgres, no DB tier,
no deploy. **Stdlib only** (Python 3.8+, sqlite FTS5 which ships with CPython).

## What it does

- **Keyword arm (FR-5):** sqlite **FTS5** full-text index with **BM25** ranking
  over every `.md` file in the corpus. Returns ranked exact-and-near matches for
  proper nouns, identifiers, codes, and wikilinks. Usable standalone, before any
  vector index exists.
- **Link arm (FR-6):** a wikilink edge table built from `[[...]]` references.
  Given an artifact, returns its **forward links** (what it points to) and
  **backlinks** (what points to it) -- 1-hop neighbors as related context.
- **Agent entry (Task 14):** `aimem.py query` fuses both: ranked keyword hits
  plus the link neighborhood of the top hit, as text or JSON.

## Design notes

- The index is a **disposable cache, never a source of truth** (NFR-2/NFR-3).
  The markdown files are canonical; delete the index and rebuild any time.
  Default location: `~/.cache/ai-memory/index.db` (outside the vault and repo).
- **Identifier-preserving tokenizer.** FTS5 is configured with
  `tokenchars '-_.@'` so identifiers like `flora-postgres`, `myarroyo.com`,
  `cc_portal`, `GATEWAY_FORCE_PROVIDER`, and `@anthropic-ai` survive as single
  tokens. Consequence: `cgroup-saturation` and `cgroup-saturation-driven` are
  distinct tokens (correct identifier behavior; a substring grep would conflate
  them).
- **No daemon, no watcher.** Rebuild is explicit/on-invocation, honoring the
  L-WFK-2 "no detached cross-session watcher" constraint. Incremental refresh is
  Phase 2 (FR-11), out of scope here.

## Files

| File | Role |
|------|------|
| `corpus.py` | walk the corpus, parse markdown title / body / wikilinks |
| `engine.py` | build the sqlite FTS5 + link index; `search`, `neighbors`, `query` |
| `aimem.py`  | CLI entrypoint (the agent interface, Task 14) |

## Build + query commands

```bash
cd retrieval

# 1) Build (or rebuild) the index from the corpus. Disposable; safe to re-run.
python3 aimem.py build
#   defaults: corpus = Work Vault, index = ~/.cache/ai-memory/index.db
#   override: python3 aimem.py build --corpus /path/to/vault --index /tmp/x.db

# 2) Keyword/BM25 search (FR-5)
python3 aimem.py search "cgroup-saturation" --limit 10
python3 aimem.py search "GATEWAY_FORCE_PROVIDER" --json

# 3) Wikilink/backlink 1-hop neighbors (FR-6)
python3 aimem.py links "IR - VPS Outage 2026-05-21"

# 4) Unified agent query: keyword hits + link expansion of top hit (Task 14)
python3 aimem.py query "OCG" --limit 5
python3 aimem.py query "OCG" --json        # machine-readable for an agent

# index status
python3 aimem.py stats
```

Environment overrides: `AIMEM_CORPUS` (corpus root), `AIMEM_INDEX` (index path).
`--json` and `--index` work before or after the subcommand.

## Verification (SAT-4 / SAT-5)

**SAT-4 (FR-5) -- keyword arm returns the N artifacts containing a proper noun.**
Ground truth via grep (token-boundary, matching the FTS5 tokenizer):
```bash
grep -rlP --include='*.md' \
  '(?<![A-Za-z0-9._@-])cgroup-saturation(?![A-Za-z0-9._@-])' \
  "/Users/holdengreene/Documents/Vaults/Work Vault"   # -> 15 files
python3 aimem.py search "cgroup-saturation" --limit 50  # -> same 15, ranked
```
Result: exact set match, 15 artifacts, BM25-ranked.

**SAT-5 (FR-6) -- backlink expansion returns the linkers of an artifact.**
```bash
grep -rlP --include='*.md' '\[\[IR - VPS Outage 2026-05-21(\||#|\]\])' \
  "/Users/holdengreene/Documents/Vaults/Work Vault"   # 48 lines, 47 distinct names
python3 aimem.py links "IR - VPS Outage 2026-05-21"     # -> 47 distinct backlinks
```
Result: exact set match, 47 distinct backlinks (the 48 grep lines include the
duplicate-basename `PJL - Infrastructure` twice; the graph dedups by name).

**Disposability (NFR-2/NFR-3).** `rm ~/.cache/ai-memory/index.db && python3
aimem.py build` reproduces identical results from source.

## Agent skill stub

A thin Claude skill stub that shells out to this engine lives at
`~/.claude/skills/aimem-retrieve/SKILL.md` (a LOCAL file, not part of this repo
branch). It points at the repo checkout and documents the same commands.
