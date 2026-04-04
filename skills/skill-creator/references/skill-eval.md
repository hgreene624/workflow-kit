# Skill Eval — Reference

Instructions for running eval suites and iteratively improving skills. You were routed here by the skill-creator router.

## Setup

1. Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Organize by iteration (`iteration-1/`, `iteration-2/`, etc.) and within that, each test case gets a directory (`eval-0/`, `eval-1/`, etc.). Create directories as you go.

## Step 1: Spawn All Runs

2. For each test case, spawn two subagents in the same turn — one with the skill, one without (baseline). Launch everything at once so it finishes around the same time.

3. **With-skill run** prompt:
   ```
   Execute this task:
   - Skill path: <path-to-skill>
   - Task: <eval prompt>
   - Input files: <eval files if any, or "none">
   - Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
   - Outputs to save: <what the user cares about>
   ```

4. **Baseline run** — same prompt, no skill path (for new skills) or old version snapshot (for improvements). Save to `without_skill/` or `old_skill/` respectively.

5. Write an `eval_metadata.json` for each test case with descriptive name, prompt, and empty assertions array.

## Step 2: Draft Assertions While Runs Are In Progress

6. Draft quantitative assertions for each test case while waiting. Good assertions are objectively verifiable with descriptive names.
7. Subjective skills (writing style, design quality) — evaluate qualitatively, don't force assertions.
8. Update `eval_metadata.json` files and `evals/evals.json` with assertions. Explain to the user what they'll see in the viewer.

## Step 3: Capture Timing Data

9. When each subagent completes, the notification contains `total_tokens` and `duration_ms`. Save immediately to `timing.json` in the run directory:
   ```json
   { "total_tokens": 84852, "duration_ms": 23332, "total_duration_seconds": 23.3 }
   ```
   This is the only opportunity — process each notification as it arrives.

## Step 4: Grade, Aggregate, and Launch Viewer

10. **Grade each run** — spawn a grader subagent (or grade inline) using `agents/grader.md`. Save to `grading.json`. Use fields `text`, `passed`, `evidence` (not `name`/`met`/`details`). For programmatically checkable assertions, write and run a script.

11. **Aggregate** — run:
    ```bash
    python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
    ```
    Put each with_skill version before its baseline counterpart.

12. **Analyst pass** — read benchmark data and surface patterns per `agents/analyzer.md`: non-discriminating assertions, high-variance evals, time/token tradeoffs.

13. **Launch viewer**:
    ```bash
    nohup python <skill-creator-path>/eval-viewer/generate_review.py \
      <workspace>/iteration-N \
      --skill-name "my-skill" \
      --benchmark <workspace>/iteration-N/benchmark.json \
      > /dev/null 2>&1 &
    VIEWER_PID=$!
    ```
    For iteration 2+, add `--previous-workspace <workspace>/iteration-<N-1>`.
    For headless/cowork: use `--static <output_path>` for standalone HTML.

14. Tell the user: "I've opened the results in your browser. 'Outputs' lets you review each test case, 'Benchmark' shows quantitative comparison. Come back when done."

## Step 5: Read Feedback

15. When the user says they're done, read `feedback.json`. Empty feedback means the output was fine. Focus improvements on test cases with specific complaints.
16. Kill the viewer: `kill $VIEWER_PID 2>/dev/null`

## Improving the Skill

17. **Generalize from feedback** — the skill will be used across many prompts, not just these examples. Avoid overfitting to test cases. If something is stubborn, try different metaphors or patterns rather than fiddly constraints.

18. **Keep the prompt lean** — read transcripts, not just outputs. Remove instructions that cause unproductive work.

19. **Explain the why** — use reasoning over rigid MUSTs. If you find yourself writing ALWAYS/NEVER in caps, reframe with reasoning.

20. **Look for repeated work** — if all test runs wrote similar helper scripts, bundle that script in `scripts/` and reference it from the skill.

21. After improving: apply changes, rerun all test cases into `iteration-<N+1>/`, launch viewer with `--previous-workspace`, wait for user review, repeat.

22. Keep iterating until: user is happy, feedback is all empty, or no meaningful progress is being made.

## Advanced: Blind Comparison

23. For rigorous A/B comparison: read `agents/comparator.md` and `agents/analyzer.md`. Give two outputs to an independent agent without revealing which is which. Optional — human review loop is usually sufficient.

## Environment-Specific Notes

24. **Claude.ai**: No subagents — run test cases one at a time yourself. Skip baselines and quantitative benchmarking. Present results inline. Skip description optimization.
25. **Cowork**: Subagents work. Use `--static` for viewer. ALWAYS generate the eval viewer before evaluating outputs yourself.
