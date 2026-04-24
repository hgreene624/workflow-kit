# Organization Context -- Technical Reference

This file provides context about your organization's existing systems, projects, and capabilities. The `/create-concept-brief` skill reads this to ground stakeholder ideas against reality.

**To customize:** Replace the sections below with your organization's actual systems. Delete examples. Keep each section concise (3-5 sentences + key facts). This file is loaded into every concept brief session, so brevity matters.

---

## 1. Platform Overview

{Describe your organization's tech stack at a high level. What kind of applications do you run? What's the deployment model? Who are the users?}

Example: "We run a suite of internal web apps for operations management. All apps deploy as Docker containers behind a reverse proxy. Database: PostgreSQL. Auth: SSO via [provider]. ~50 internal users across 3 departments."

## 2. Core Applications

{List each major application with a 2-3 sentence description of what it does and who uses it.}

### App 1
{Description, key features, primary users.}

### App 2
{Description, key features, primary users.}

## 3. Data and Intelligence Layer

{Describe any data pipelines, analytics, or intelligence systems. What data flows exist? What's automated vs manual?}

## 4. Infrastructure

{Key infrastructure details: hosting, deployment pipeline, monitoring, CI/CD.}

- **Hosting:** {provider, deployment model}
- **Database:** {type, major databases}
- **Auth:** {provider, SSO, user management}
- **CI/CD:** {pipeline description}

## 5. Active Projects

{List 3-5 currently active projects with one-line descriptions. This helps the concept brief skill identify overlaps with incoming ideas.}

1. {Project} -- {one-line description}
2. {Project} -- {one-line description}

## 6. Common Stakeholder Terminology

{Table mapping informal terms stakeholders use to actual system names. This is heavily referenced during concept brief creation.}

| Stakeholder might say | System term | What it actually is |
|---|---|---|
| {informal term} | {system name} | {brief explanation} |
| {informal term} | {system name} | {brief explanation} |
