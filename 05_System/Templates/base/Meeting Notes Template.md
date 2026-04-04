---
date created: {{date:YYYY-MM-DD}}
tags:
  - meeting
category: Meeting
---

## Attendees
-

---
## Agenda / Topics

### Topic title
#### Discussion
-
#### Decisions
-
#### Actions (owned tasks with clear deliverable)
-

---
## Action Items
```dataviewjs
const tasks = dv.current().file.tasks
  .where(t => !t.completed && t.text)
  .sort(t => t.section?.subpath ?? "");
dv.taskList(tasks, false);
```
