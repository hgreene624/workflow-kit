---
date created: {{date:YYYY-MM-DD}}
tags: daily
category: Daily Note
---
# {{date:dddd, MMMM D, YYYY}}

## Recent Work
```dataview
TABLE WITHOUT ID
  file.link AS "Document",
  category AS "Type",
  dateformat(file.mtime, "MMM dd") AS "Modified"
FROM "02_Projects" OR "04_Reference"
WHERE file.mtime >= date(today) - dur(7d)
  AND !contains(file.name, "Template")
  AND !contains(file.name, "agents")
  AND !contains(file.name, "lessons")
  AND !contains(file.path, "data.nosync")
  AND category != null
SORT file.mtime DESC
LIMIT 10
```

## Open Pickups
```dataview
TABLE WITHOUT ID
  file.link AS "Pickup",
  status AS "Status",
  dateformat(date-created, "MMM dd") AS "Created"
FROM "02_Projects" OR "01_Notes"
WHERE category = "Pickup"
  AND (status = "open" OR status = "picked-up")
SORT choice(status = "open", 0, 1) ASC, file.ctime DESC
```

---
## TODO
- [ ]

---
## Meetings
-

---
## Worked on
-

---
## Notes
-
