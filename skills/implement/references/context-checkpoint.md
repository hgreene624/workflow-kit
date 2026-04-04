# Context Checkpoint Protocol for Workers

Long-running workers (complex engineering tasks, multi-file refactors, VPS migrations) risk context degradation as their context window fills.

## Protocol

1. PM monitors worker message length and coherence. Signs of context pressure: rushed responses, skipped steps, "I'll handle that later" deferrals, repeated mistakes
2. If a worker is on a task estimated at >1 hour of agent time, PM should proactively request a status checkpoint at the halfway mark
3. **Checkpoint format:** Worker sends PM a structured summary: what's done, what's remaining, current blockers, key decisions made. PM relays to orchestrator.
4. **If context pressure is detected:** Orchestrator shuts down the worker and dispatches a fresh worker with the checkpoint summary + remaining task list. The fresh worker starts with clean context and the full progress artifact.
5. Workers should be instructed to commit frequently to git — progress lives in files and commits, not in context. A fresh worker with access to the git state picks up where the last one left off.
