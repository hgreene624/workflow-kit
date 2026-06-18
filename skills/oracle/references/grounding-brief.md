# Grounding Brief — the 8-question elicitation (Phase 0)

Opens **every** `/oracle build`. A short, non-leading structured interview. Framing is **"no wrong answers"** throughout — this is elicitation, not a test. Use Value-Focused Thinking: probe iteratively for finer grain, and run the **WITI ("Why Is That Important?") ladder** to separate ends from means.

**Ask ONE question at a time** (the kit rule — never bundle). Wait for the answer, reflect it back briefly, then ask the next. Where a question has natural option shapes, offer numbered options, but always allow free text.

The brief emits two artifacts:
- a **charter** — scope · fundamental objectives · means/constraints · values, and
- a **labeled thesis-hypothesis** — the working thesis, explicitly stamped as a HYPOTHESIS UNDER TEST, never as settled fact.

## The two-layer split (the most important control — §9.1)

The brief is deliberately split so a stance can never silently become a retrieval filter:

- **Targeting layer — Q1–Q4 (focus / objectives / means / values).** May constrain **relevance**: it filters on *topic*, never on conclusion. "Is this source about the right subject?" — yes.
- **Stance layer — Q5–Q6 (working thesis / confidence).** A **labeled hypothesis under test, NEVER a retrieval filter.** Sources are never excluded for disagreeing with the thesis. The thesis is something the oracle is built to *stress-test*, not to confirm.

If you ever find yourself filtering candidate sources on whether they agree with Q5, STOP — that is the echo-chamber failure this split exists to prevent.

## The 8 questions

1. **Core focus / domain.** What is this oracle about? *(targeting)*

2. **Fundamental objectives.** What is it ultimately *for*? **Run the WITI ladder:** for each objective the operator gives, ask "why is that important?" until you hit a *fundamental* end (an objective valued for its own sake) vs a *means* (valued only because it serves something else). Record fundamental objectives as the charter's objectives; record means under Q3. *(targeting)*

3. **Means / constraints.** What approaches, resources, limits, or boundary conditions shape how the objectives get met? (Includes the means surfaced by the WITI ladder in Q2.) *(targeting)*

4. **Values & morals.** What values or principles must the corpus respect or foreground? *(targeting)*

5. **Working thesis.** What does the operator currently believe the answer / right approach is? **Log this as a HYPOTHESIS** — label it explicitly ("Working thesis (hypothesis under test): …"). *(stance — NOT a filter)*

6. **Confidence in, and origin of, the thesis.** How strongly held, and where did it come from (experience / a source / intuition)? *(stance — NOT a filter)*

7. **Strongest opposing view — in the operator's own words.** Have the operator articulate the strongest established/traditional case *against* the thesis. (See the anti-filter mechanism below — this auto-emits a mandatory task.)

8. **Disconfirmers.** What would change the operator's mind? What evidence, if found, would falsify the thesis? (Also auto-emits a mandatory task.)

## Anti-filter mechanism — Q7 and Q8 auto-emit non-skippable tasks (§9.1, Task 28)

**You cannot have targeting without dissent.** The same brief that encodes the thesis MUST mandate the challenge. On completing Q7 and Q8, **auto-emit two MANDATORY source-acquisition tasks** the build **cannot skip**:

- **From Q7 → a STEELMAN curation task.** Acquire the strongest *established / traditional counter-case* to the thesis — phrased as a search/curation task, e.g. "Curate the strongest authoritative source(s) arguing {operator's opposing view}." This source set is acquired and runs through the §7/§8 gate like any other.
- **From Q8 → a DISCONFIRMER search task.** Search specifically for evidence that would *falsify* the thesis (the disconfirmers the operator named), and curate what is found.

These two tasks are **gated as non-skippable build steps** — record them on the build's task list at brief-completion, and the **coverage/balance audit (G2) will not pass a bucket that has no `challenging` source** (the balance check is the enforcement). A build that reaches G2 without having executed the steelman + disconfirmer tasks fails the gate. Do not let the build proceed to "done" with these tasks open.

## Emitting the charter + hypothesis

After Q8, write back:
- **Charter** — scope (Q1) · fundamental objectives (Q2, post-WITI) · means/constraints (Q3) · values (Q4).
- **Labeled thesis-hypothesis** — the Q5 thesis stamped "hypothesis under test", with the Q6 confidence/origin noted, and the Q7 steelman + Q8 disconfirmers attached as the mandatory acquisition tasks.

This becomes the input to Phase 1 (Taxonomy). The charter's objectives drive the taxonomy's **key questions**; the hypothesis and its mandated dissent drive the **required perspective spread** — not a target source count.
