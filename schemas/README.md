# Schemas

Machine-validatable schemas for the AI-Memory Vault (PL - AI-Memory Vault Phase 1).

## `work-event.schema.json` (Task 2 / FR-1 + FR-3)

The single typed record the event-log writer appends. One unit of logged work =
exactly one work-event. The human daily view and the per-project (PJL-equivalent)
view are both generatable from a stream of these events, so there is no second
hand-authored copy.

- Required: `timestamp` (ISO-8601), `project`, `type` (enum), `summary`, `provenance`.
- `provenance` (FR-3) requires `origin_session` + `author_agent`.
- Optional structured fields: `details`, `paths[]`, `decisions[]`, `tried_and_failed[]`,
  `artifacts[]` (Obsidian wikilinks, `[[...]]`).
- Sample + validation: `examples/work-event.sample.json`.

## `artifacts/<PREFIX>.schema.json` (Task 7 / FR-4)

One frontmatter schema per LIVE Work Vault artifact prefix (44 files). Source of
truth is the File Prefixes table in `Work Vault/CLAUDE.md` plus the create-note
templates' frontmatter additions. These feed the write-time schema-validation hook
(PL task 8).

- Every schema requires the three base fields: `date created`, `tags`, `category`.
- `category` is pinned with `const` to the EXACT table value (getting it wrong
  breaks Obsidian views).
- Type-specific required fields are added only where the table/templates imply them
  (e.g. SPC + PD + PL + DD + SO + KBO add `status` + `source`; PIC adds
  `status` + `project`; SD adds `status` + `version` + `date modified`; IR adds
  `status` + `severity`; HAN adds the delegation fields).
- `additionalProperties: true` — extra frontmatter keys are allowed, so enforcement
  never blocks an operator's conforming write that carries extra fields (L-WFK-3).
- Dead prefixes WS / WA / FR are intentionally excluded (retired by PL task 11).

## Regenerating the artifact schemas

`python3 schemas/_gen_artifact_schemas.py` rewrites `schemas/artifacts/*.json`.
Update the `PREFIXES` / `EXTRA_REQUIRED` maps in that script when the prefix table
changes, then rerun. Do not hand-edit individual artifact schema files.

## Validation

Validated with Python `jsonschema` (Draft 7). No validator was bundled in the repo,
so `jsonschema` was installed locally for the verification runs.
