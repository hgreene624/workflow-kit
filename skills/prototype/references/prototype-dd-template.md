---
date created: {today}
category: Design Discussion
source: "[[{spec_filename}]]"
tags: [{relevant_tags}, prototype]
status: Draft
---

# DD - {Spec Name} Prototype

## Product Context
{One paragraph: what this is, who uses it, what problem it solves. Written for a designer who has never seen the spec.}

## User Flows

### Flow: {Flow Name}
**Actor:** {who}
1. {action} -> {result/what they see}
2. {action} -> {result/what they see}
...

## Screen Inventory

### Screen: {Screen Name}
- **Route:** {URL path}
- **Actor:** {who sees this}
- **Purpose:** {one line}
- **Entry points:** {how user gets here}
- **Key content:** {what's displayed}
- **Key actions:** {what user can do}
- **States:** {empty, loading, populated, error if applicable}

## Component Inventory

### Component: {Component Name}
- **Used in:** {screens}
- **Description:** {what it looks like and does}
- **States:** {variants}
- **Data:** {what it displays or accepts}

## Data Model Summary

### Entity: {Entity Name}
- **Displayed as:** {card, row, detail page, etc.}
- **Key fields shown to user:** {field: example value}
- **Relationships:** {visual connections to other entities}

## Interaction Patterns

### Navigation
{How users move between screens}

### Creation Flows
{Wizard vs single page, progressive disclosure}

### Async Operations
{Loading states, polling, return-to-completed}

### Mobile vs Desktop
{Which screens are mobile-first, breakpoints}

### Auth Transitions
{How UI changes between roles}

### Bilingual
{Language switching UX}

### Feedback
{Success/error states, toasts, validation}

### Data Tables
{AG Grid usage, sorting, filtering}
