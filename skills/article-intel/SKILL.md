---
name: article-intel
description: >-
  Full-pipeline article intelligence: fetch a web article (or batch of articles),
  extract clean content, generate summaries, store in the vault, then evaluate
  against all active projects for relevance and actionable value. If the assessment
  finds genuine value, dispatches a research team for a deep dive with current best
  practices, implementation recommendations, and project-specific application notes.
  Supports single URLs and multiple URLs processed in parallel.
  Use this skill whenever the user shares an article URL and wants to know if the
  content is useful for their work, says "check this article", "is this worth reading",
  "article intel", "analyze this article", "process this article", "what can we use
  from this", or any variation of wanting web content evaluated against active projects.
  Also trigger when the user pastes an article link with context suggesting they want
  evaluation, e.g. "found this on X, might be useful for {{ORG}}" or "someone shared this,
  looks relevant to the residents portal". Handles simple read-and-store requests
  ("just save this article") as a lightweight path.
---

# Article Intelligence Pipeline

Transform web articles into actionable project intelligence. The pipeline has five phases, each gated so irrelevant content gets triaged fast without wasting time on a deep dive.

**Arguments:** $ARGUMENTS

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve directory references (e.g., `{paths.daily_notes}/`, `{paths.projects}/`, `{paths.reference}/`). If the file doesn't exist, use defaults and warn once.

## Phase 0: Input Parsing

Determine whether the input is a single article or a batch, then route accordingly.

### Detect input type

- **Single URL** -- one URL provided, with or without context (e.g. "might be useful for X")
- **Multiple URLs** -- two or more URLs, separated by spaces, newlines, or commas
- **URL with hint** -- a URL followed by context about which project or topic it relates to. Capture the hint; it biases the relevance assessment in Phase 3

### Single article path

Proceed to Phase 1 with the URL and any hint text.

### Batch path

1. List the articles by number with their URLs
2. Dispatch each article through Phase 1-5 **in parallel** using Agent teammates, one per article. Each teammate runs the full pipeline independently
3. After all teammates complete, aggregate results into a batch report (Phase 5b)

## Phase 1: Fetch and Store

Extract clean article content from the URL.

### 1a. Fetch the article

Use `WebFetch` with the article URL. Request the content in a readable format.

If the initial fetch returns minimal content (under 200 words of body text), try these fallbacks in order:
1. Prepend `https://r.jina.ai/` to the URL and fetch again (Jina Reader provides clean extracted text)
2. Use `WebSearch` for the article title + site to find a cached or alternative version
3. If all fetches fail, report the failure and skip to the next article (in batch mode) or tell the user

### 1b. Clean the content

Strip navigation, ads, sidebars, cookie banners, and other non-article content. Preserve:
- Article title, author, publication date
- All body text with original heading structure
- Code blocks, tables, and lists
- Inline links (convert to markdown format)
- Image alt text (discard the images themselves)
- Pull quotes or callouts

### 1c. Store the article

Save to `Knowledge/Articles/YYYY-MM-DD/<Article-Slug>/AR - <Article Title>.md` where:
- Date folder uses today's date
- Article-Slug is the title in kebab-case, truncated to 60 characters
- Article Title is the original title, cleaned for filesystem safety

**Frontmatter:**
```yaml
---
title: "<Article Title>"
type: article
category: Article
source_url: <full URL>
author: "<Author>"
publication_date: <YYYY-MM-DD if available>
date_fetched: YYYY-MM-DD
domain: "<source domain>"
tags: [<relevant topic tags>]
---
```

Tell the user: "Article saved. Generating summary and scanning projects..."

## Phase 2: Summarise

Read the stored article and generate a structured summary.

**Output:** `Knowledge/Articles/YYYY-MM-DD/<Article-Slug>/AS - <Article Title>.md` (same folder as the article)

**Frontmatter:**
```yaml
---
title: "<Article Title> - Summary"
type: article-summary
category: Article Summary
source: "[[AR - <Article Title>]]"
source_url: <URL>
date_created: YYYY-MM-DD
tags: [<relevant topic tags>]
---
```

**Sections:**

1. **TL;DR** -- 1-2 sentence core takeaway in blockquote
2. **Key Takeaways** -- 5-8 numbered actionable insights. Focus on what is genuinely novel or non-obvious. Filter out hype, repackaged common knowledge, and marketing language.
3. **Summary** -- Organised by `###` topic sections mirroring the article's structure. 2-4 sentences per section.
4. **Notable Details** -- Concrete specifics: tool names, configurations, benchmarks, costs, code patterns. Table or bullet format.
5. **Novelty Assessment** -- One paragraph: what in this article is actually new vs. repackaged conventional wisdom? Be direct and critical. If the article is mostly hype, say so.

Do NOT write the "Relevant To" section yet; Phase 3 handles that with real project context.

## Phase 3: Project Relevance Assessment

This is where the skill earns its keep. Understand what the user is actively working on, then judge whether the article content has genuine value.

### 3a. Scan active projects

Dispatch a **haiku-model Explore subagent** to quickly gather project context. It should:

1. Read `00 Command Centre/active-threads.md` to get the current work landscape
2. Scan `Work Projects/` directory listing to identify active project folders
3. For any project with a `CLAUDE.md`, `README.md`, or `CLAUDE.md`, read the first 50 lines to get the project scope
4. Check for active specs (`SPC - *.md`) or plans (`PL - *.md`) in the most active project folders
5. Return a structured brief: project name, current focus, key technologies, open problems

This scan should take 30-60 seconds. The goal is a lightweight snapshot, not an exhaustive audit.

### 3b. Evaluate relevance

With the project brief and the article summary in hand, assess each active project against the article content. For each project, answer:

- **Direct applicability**: Does the article cover a technology, pattern, or approach that directly solves a current problem or implements a planned feature?
- **Architectural insight**: Does it introduce patterns or best practices that would improve how something is built?
- **Risk/opportunity**: Does it reveal risks in the current approach, or opportunities not yet considered?
- **Knowledge gap**: Does it fill a gap in understanding that would improve decision-making?

If the user provided a **hint** in Phase 0, weight the hinted project more heavily but still assess all projects; sometimes the real value is for a project the user did not expect.

**Scoring** (internal, don't show raw scores to user):
- **3 = High**: Direct, actionable value for an active project. Worth acting on.
- **2 = Medium**: Useful context or background knowledge that informs decisions but does not require immediate action.
- **1 = Low**: Tangentially related. Nice to know, not worth a deep dive.
- **0 = None**: No meaningful connection.

### 3c. Decision gate

- If ANY project scores **3**: Proceed to Phase 3d, then Phase 4 (full deep dive)
- If highest score is **2**: Proceed to Phase 3d, then present the TL;DR and relevance notes. Ask if the user wants a deep dive anyway.
- If all scores are **1 or 0**: Present the TL;DR, note the weak connections, save the summary, done. Skip Phase 3d. Be honest: "Nothing here that moves the needle on your current work."

### 3d. Project Backlinks

For each project that scored **2 or higher**, write a backlink into that project's `CLAUDE.md` under a `## Queued Context` section.

1. Read the project's `CLAUDE.md`
2. Find or create the `## Queued Context` section (place it at the end of the file, before any `## Lessons` section if one exists)
3. Check if a backlink to this summary file already exists (dedup by filename)
4. If not present, append:
   ```
   - [[AS - <Article Title>]] — <one-line reason this matters to the project> (YYYY-MM-DD)
   ```
5. Also update `04_Reference/REF - Topic Index.md` if the article introduces a new topic not yet listed
6. Also update any relevant transcript/article index files

This ensures that when an agent loads a project's context via `/orient` or `/pickup`, relevant ingested content surfaces automatically.

## Phase 4: Deep Dive Team Dispatch

When the assessment finds high-value content, dispatch a research team for comprehensive analysis.

### Team composition

Use `TeamCreate` to spin up a team with these roles:

**1. Researcher** -- Investigates the article's topics against current best practices. Uses WebSearch and WebFetch to find:
- Current state of the art for the technologies/patterns discussed
- Known limitations, gotchas, and production lessons
- Competing approaches the article may not have covered
- Pricing, licensing, and infrastructure requirements
- Whether the claims in the article hold up against other sources

Write findings to `ARE - <Article Title> Research Notes.md` in the same directory as the AR/AS files.

**2. Architect** -- Maps findings to the specific project(s) that scored high. Reads the project's CLAUDE.md, specs, plans, and existing codebase context to produce:
- How to apply the article's insights to the user's specific stack
- What changes would be needed (new dependencies, schema changes, config)
- Implementation phases with effort estimates
- Risks and trade-offs specific to the user's environment

Write findings to `ARE - <Article Title> Architecture Notes.md` in the same directory as the AR/AS files.

**3. Writer** -- Reads the Researcher and Architect outputs and produces the final deep dive. Updates `AS - <Article Title>.md` to include everything from Phase 2 PLUS:

6. **Current Best Practices** -- What the researcher found. Organised by topic with tables comparing options, concrete recommendations, and citations.
7. **Project Application: <Project Name>** -- One section per high-scoring project. Implementation path, recommended tools, code snippets where relevant, estimated costs.
8. **Key Takeaways** -- Updated to reflect the deeper analysis, not just the article content
9. **Sources** -- All research links with brief descriptions

### References file

When a deep dive is produced, save a `REF - <Article Title>.md` file in the same directory. Collect all external links: the original article's references, researcher-found sources, and any supplemental URLs. Organise by topic with brief descriptions per link. Use standard REF frontmatter with `category: Reference`.

### Task coordination

The Researcher and Architect run in parallel (researcher does web research while architect reads project context). The Writer waits for both to complete.

## Phase 5: Present Results

### 5a. Single article briefing

After all phases complete for a single article, present:

```
**Article:** <Title> by <Author> (<Domain>)
**Saved:** [[AR - <Article Title>]] | [[AS - <Article Title>]]

**TL;DR:** <1-2 sentence takeaway>

**Novelty:** <one sentence: genuinely new, mostly rehash, or mixed>

**Relevant to:** <Project names that scored 2+, with one-line reason each>

<If deep dive was run:>
**Deep dive complete.** Key finding: <single most actionable insight>
```

Then ask: "Want to discuss any of the findings, or is the written report sufficient?"

### 5b. Batch report

After all articles in a batch are processed, produce a summary report. Display to the user AND write to the daily note.

**Format:**

```markdown
### Article Intel Batch
- **Processed:** <N> articles
- **High relevance:** <count>
- **Medium relevance:** <count>
- **Low/None:** <count>

| Article | Source | Score | Key Takeaway |
|---------|--------|-------|--------------|
| [[AS - <Title>]] | <domain> | High | <one-line actionable insight> |
| [[AS - <Title>]] | <domain> | Med | <one-line context summary> |
| [[AS - <Title>]] | <domain> | Low | <one-line reason> |
```

**Rules for the table:**
- Sort by score descending (High, Med, Low)
- Link to the AS (summary) file, not the AR (article)
- Key Takeaway is a single phrase, no full sentences, no periods
- If a deep dive was dispatched, append ` (deep dive)` to that row's Key Takeaway

### 5c. Single article daily note entry

For single articles, use a compact format on the daily note:

```markdown
### Article Intel -- <Article Title>
| Article | Source | Score | Key Takeaway |
|---------|--------|-------|--------------|
| [[AS - <Title>]] | <domain> | High | <one-line insight> (deep dive) |
```

## Vault Hygiene

- **Batch reports** go in a dedicated report file: `Knowledge/Articles/YYYY-MM-DD/RE - Article Intel Batch YYYY-MM-DD.md`. The daily note gets a one-liner linking to the report.
- **Single article reports** use the compact format (Phase 5c) directly on the daily note
- If a deep dive was produced, link the summary under the relevant project's heading in the daily note
- Tag summaries with project-relevant tags for Obsidian graph view
- **Deduplication:** Before fetching, check `Knowledge/Articles/` for an existing `AR -` file whose `source_url` matches the URL. If found, skip Phase 1 and use the existing content. Tell the user: "Already processed. Here's the summary: [[AS - <Title>]]"

## Lightweight Actions

### `save <url>` -- Save only

When the user explicitly says "just save" or "save only":
1. Run Phase 1 only (fetch and store)
2. Offer to generate a summary but do not auto-run the project assessment
3. This is the escape hatch for content the user wants archived without evaluation

### `help` -- Show usage

```
/article-intel <url>                    Full pipeline on a single article
/article-intel <url1> <url2> ...        Batch process multiple articles in parallel
/article-intel save <url>               Save article only (no assessment)
/article-intel help                     Show this usage guide
```

Context hints are supported: `/article-intel <url> might be useful for the booking system`

## Edge Cases

- **Paywall or login-gated content**: If WebFetch returns minimal content, try Jina Reader fallback. If still blocked, report the issue and suggest the user paste the article text directly.
- **PDF link**: If the URL points to a PDF, use the Read tool with the fetched file. Adjust content extraction accordingly.
- **Twitter/X thread**: If the URL is a tweet or thread, fetch and reconstruct the thread as a single article. Note in frontmatter: `type: twitter-thread`.
- **Article already processed**: Check for existing AR file by source_url before fetching. Reuse existing content and skip to Phase 2 if the summary is missing, or present existing summary if complete.
- **Empty or error page**: Report the failure clearly. Do not generate a summary from an error page.
- **Non-English content**: Process as normal. Summarise in English.
- **Very long articles (10,000+ words)**: Process normally but note the length in the summary. Consider splitting the summary into more granular topic sections.
- **Redirect chains**: Follow redirects. Store the final URL as `source_url` and the original as `original_url` in frontmatter.
