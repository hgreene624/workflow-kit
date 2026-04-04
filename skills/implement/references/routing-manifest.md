# Routing Manifest Protocol

Every router skill that dispatches to sub-skills MUST follow this protocol. It ensures no sub-skill is silently skipped during execution.

## On Entry

1. Write a manifest file to `/tmp/routing-manifest-{skill-name}-{timestamp}.json`
2. Manifest contains:
   ```json
   {
     "router": "implement",
     "expected": ["setup", "execute"],
     "completed": [],
     "timestamp": "..."
   }
   ```

## On Sub-Skill Completion

1. Each sub-skill appends its name to the `completed` array
2. Sub-skill writes its output summary to the manifest under a `summaries` key:
   ```json
   {
     "summaries": {
       "setup": "Team created, PM ready, 12 tasks across 3 phases",
       "execute": "All phases complete, 12/12 tasks Done"
     }
   }
   ```

## On Chain End

1. Final sub-skill reads the manifest
2. Compares `expected` vs `completed`
3. If any expected sub-skill is missing: **ALERT the user** — `"WARNING: Sub-skill {name} was skipped. The following steps were not executed: {list}"`
4. Delete the manifest file on success
