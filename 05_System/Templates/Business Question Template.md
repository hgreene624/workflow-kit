---
date created: 2026-03-22
category: Business Question
status: Open
---

# <Question>

## Context
- 

## Reports
Set `business_question: [[BQ - <question>]]` on related reports.

```base
filters:
  and:
    - Category == "Report"
    - business_question.contains("<question>")
views:
  - type: table
    name: Reports
    properties:
      - file
      - date modified
```

## Answer
### YYYY-MM-DD
- Answer:
- Evidence: [[RE - ...]]
