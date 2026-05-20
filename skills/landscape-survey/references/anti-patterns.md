# Anti-patterns to refuse

These are the failure modes the skill exists to prevent. Refuse to proceed if you find yourself doing any of them.

## 1. Skipping the manual anchor read

**Why it fails:** Tempting to delegate all candidates to the team cold to save context. The template-establishment value of the manual read is real and disappears if you skip. Subsequent workers without a template produce drift; the synthesis pass cannot reconcile drift.

**Refuse:** Run Phase 4 manually on 1-2 closest peers. No exceptions. The cost is one session; the cost of skipping is fragmented AREs and a synthesis pass that produces a confirmation document instead of a synthesis.

## 2. Multi-worker synthesis

**Why it fails:** Produces a fragmented document where the comparison table from one worker contradicts the per-repo sections from another. Cross-cutting findings (the "multiplicative interactions" that justify the synthesis pass) only emerge when a single mind reconciles the AREs.

**Refuse:** Phase 6 dispatches ONE synthesis worker. If tempted to split the RE across multiple workers for speed, accept the longer single-worker turnaround instead.

## 3. Adding candidates mid-stream after Phase 2 locks

**Why it fails:** Destroys the parallelism of Phase 5. The synthesis worker has to redo its work to include the new candidate. The locked candidate set is a contract.

**Refuse:** Log new candidates as a follow-up survey. The current survey closes with the locked set. If the new candidate is critical, abort the current survey and restart with the expanded set rather than expanding mid-stream.

## 4. Drafting SPC content during the survey

**Why it fails:** The PIC bracket explicitly forbids it. Findings that point at SPC FRs are necessary outputs of the survey, but they belong in the RE's Open Questions section, not in draft SPC text.

**Refuse:** When the synthesis surfaces obvious FRs, capture them as numbered Open Questions with options + recommended defaults. The SPC drafting that follows the survey will use these as the open-decision backlog.

## 5. Q-number collisions

**Why it fails:** Two AREs with overlapping Q-ranges produce confusion at synthesis time. The synthesis worker has to deduplicate and renumber, but they may miss collisions that look like separate questions but are the same concern.

**Refuse:** Pre-allocate Q-ranges per worker in the Phase 5 brief (Worker A: Q1-Q10, Worker B: Q11-Q20, etc). OR pre-commit to "synthesis renumbers globally" and warn workers not to be precious about their Q-numbers. Either path works; ad-hoc Q-numbering does not.

## 6. Reading source for "where" questions

**Why it fails:** Source reads are heavy on context. "Where is X defined?" is a `Grep` or `Glob` question, not a `Read` question. Wasting reads on lookups means less budget for real architectural understanding.

**Refuse:** Reserve `Read` for "how does X work" and "why was X designed this way" questions. Use `Grep` / `Glob` / `find` for "where" and "which file" questions.

## 7. Untracked findings

**Why it fails:** Every architectural observation should land somewhere. Findings that don't make it into Borrow/Adopt/Reject or Open Questions get forgotten. The next session has no idea they ever surfaced.

**Refuse:** Every observation gets one of: a Borrow As Concept entry, an Adopt As Dep entry, a Reject entry, or a numbered Open Question. Nothing floats.

## 8. Writing AREs into the scratch dir

**Why it fails:** Scratch is ephemeral. AREs in scratch disappear when the user deletes the scratch dir after the SPC ships. The survey's findings are lost.

**Refuse:** AREs and the RE always land in the vault at `02_Projects/<project>/reports/<date>/`. Scratch is for source clones only. The frontmatter's `commit_sha` field makes the scratch deterministically reconstructable from the ARE alone.

## 9. Reading the marketing page in place of source code

**Why it fails:** READMEs and project homepages are the level of understanding the survey is meant to surpass. The whole point of deep-read is to go past surface claims. If you find yourself summarizing the README, you have not done the work.

**Refuse:** The ARE adds source-code-deep findings the README doesn't surface. If your ARE could have been written by reading only the README, the read was insufficient.

## 10. Treating the architectural-shape hint as constraint instead of seed

**Why it fails (synthesis worker only):** The team-lead's prose synthesis is a hint, not a constraint. Synthesis workers who treat it as constraint produce confirmation documents instead of synthesis. The whole point of the synthesis pass is to produce findings that did not exist in any single ARE.

**Refuse:** When the synthesis worker brief includes an architectural-shape hint, treat it as a seed. If the AREs contradict the hint, follow the AREs and document the contradiction in the RE.
