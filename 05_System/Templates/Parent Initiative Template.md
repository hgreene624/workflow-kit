---
date created: YYYY-MM-DD
date modified: YYYY-MM-DD
category: Initiative Log
initiative: <Initiative Name>
status: Active
stage: Planning
owner:
constitution:
spec:
plan:
source_note: []
description: <One-line scope describing the umbrella goal for this parent initiative>
tags:
  - template
---

# <Initiative Name>

## Child Initiatives

```base
filters:
  and:
    - Category == "Initiative Log"
    - parent_initiative.contains("<Initiative Name>")
formulas:
  initiative_link: link(file, initiative)
properties:
  initiative_link:
    displayName: Initiative
  date modified:
    displayName: Last Activity
  description:
    displayName: Description
views:
  - type: table
    name: Children
    groupBy:
      property: date modified
      direction: DESC
    properties:
      - initiative_link
      - date modified
      - description
```

## Log
### YYYY-MM-DD
- <Factual update with source link(s). Example: `[[DN - 2025-12-02#Worked on]]`.>
