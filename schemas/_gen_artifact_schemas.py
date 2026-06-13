#!/usr/bin/env python3
"""Generate one frontmatter JSON Schema per LIVE Work Vault artifact prefix.

Source of truth: the File Prefixes table in Work Vault/CLAUDE.md and the
create-note templates' "Frontmatter additions" blocks.

Every artifact requires the three base fields (`date created`, `tags`,
`category`) with `category` pinned to the EXACT enum value from the table.
Type-specific required fields are added only where the table or a template
implies them (e.g. SPC adds status+source, PIC adds status).

DEAD prefixes WS / WA / FR are intentionally excluded (retired by PL task 11).

Run: python3 schemas/_gen_artifact_schemas.py   (writes schemas/artifacts/*.json)
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "artifacts")

# prefix -> (type label, exact category value)
PREFIXES = {
    "DN":  ("Daily Note", "Daily Note"),
    "MN":  ("Meeting Note", "Meeting"),
    "RE":  ("Report", "Report"),
    "IR":  ("Incident Report", "Report"),
    "SPC": ("Spec", "Spec"),
    "PL":  ("Plan", "Plan"),
    "REF": ("Reference doc", "Reference"),
    "IN":  ("Initiative log", "Initiative Log"),
    "TR":  ("Transcript", "Reference"),
    "TS":  ("Transcript Summary", "Reference"),
    "QA":  ("Quality Audit", "Report"),
    "AIS": ("AI Meeting Summary", "Meeting"),
    "TA":  ("Tasting Note", "Report"),
    "LOG": ("Debug/Pipeline Log", "Report"),
    "ST":  ("Status/Tool doc", "Reference"),
    "CO":  ("Comp (competitor research)", "Report"),
    "PJL": ("Project Log", "Reference"),
    "WL":  ("Work Log", "Reference"),
    "ARE": ("Agent Report", "Report"),
    "RET": ("Retrospective", "Report"),
    "HAN": ("Handoff", "Handoff"),
    "PIC": ("Pickup", "Report"),
    "TRI": ("Triage Report", "Report"),
    "QAL": ("QA Log", "Report"),
    "DD":  ("Design Discussion", "Plan"),
    "SO":  ("Structure Outline", "Plan"),
    "PR":  ("Patrick Request", "Report"),
    "SD":  ("System Definition", "System Definition"),
    "TSK": ("Task", "Task"),
    "CS":  ("Case Study", "Report"),
    "PD":  ("Product Definition", "Spec"),
    "FD":  ("Feature Definition", "Feature Definition"),
    "KBO": ("KB Outline", "Plan"),
    "RM":  ("Roadmap (legacy)", "Plan"),
    "MRM": ("Monthly Roadmap", "Report"),
    "WRM": ("Weekly Roadmap", "Report"),
    "KBL": ("KB Log", "Reference"),
    "KBP": ("KB Prompt", "KB Prompt"),
    "KBA": ("KB Analysis", "Report"),
    "CAM": ("Campaign", "Campaign"),
    "PUB": ("Publication", "Report"),
    "EB":  ("Executive Brief", "Report"),
    "SYL": ("Syllabus", "Reference"),
    "AGD": ("Agent Definition", "Agent Definition"),
}

# Reusable property definitions for type-specific fields.
P = {
    "status":             {"type": "string", "description": "Lifecycle status of the document."},
    "source":             {"type": "string", "description": "Wikilink to the source spec/request this derives from."},
    "project":            {"type": "string", "description": "The project this document belongs to."},
    "version":            {"type": "integer", "minimum": 1, "description": "Document version (constitutional docs increment in place)."},
    "date modified":      {"type": "string", "format": "date", "description": "Last-modified date (YYYY-MM-DD)."},
    "severity":           {"type": "string", "description": "Incident severity (e.g. P1/P2/P3)."},
    "work_state":         {"type": "string", "description": "Delegation work state, e.g. ACTIVE / PARKED / BLOCKED."},
    "coordinator_status": {"type": "string", "description": "Coordinator liveness, e.g. live / torn-down."},
    "orchestrator_contact": {"type": "string", "description": "Who the coordinator reports to (orchestrator or operator channel)."},
    "related_pl":         {"type": "string", "description": "Wikilink to the meta-plan / governing plan this HAN binds to."},
    "pickup_date":        {"type": "string", "format": "date", "description": "Next workday this pickup is scheduled for (YYYY-MM-DD)."},
    "ceremony_tier":      {"type": "string", "enum": ["light", "standard", "heavy"], "description": "Plan ceremony tier."},
    "completed":          {"type": "integer", "minimum": 0, "description": "Count of completed tasks."},
    "total":              {"type": "integer", "minimum": 0, "description": "Total task count."},
}

# prefix -> list of EXTRA required field names (beyond the 3 base fields).
EXTRA_REQUIRED = {
    "SPC": ["status", "source"],
    "PD":  ["status", "source"],
    "PL":  ["status", "source"],
    "DD":  ["status", "source"],
    "SO":  ["status", "source"],
    "KBO": ["status", "source"],
    "PIC": ["status", "project"],
    "SD":  ["status", "version", "date modified"],
    "RE":  ["status"],
    "ARE": ["status"],
    "IR":  ["status", "severity"],
    "HAN": ["status", "work_state", "coordinator_status", "orchestrator_contact", "related_pl"],
}

# prefix -> list of OPTIONAL known fields (typed but not required).
EXTRA_OPTIONAL = {
    "PL":  ["ceremony_tier", "completed", "total"],
    "PIC": ["pickup_date"],
    "IR":  ["resolved", "affects"],
    "RE":  ["severity", "resolved", "affects"],
}
P["resolved"] = {"type": "boolean", "description": "Whether the issue is resolved."}
P["affects"]  = {"type": "string", "description": "What the report affects."}

os.makedirs(OUT, exist_ok=True)
written = []
for prefix, (label, category) in sorted(PREFIXES.items()):
    props = {
        "date created": {"type": "string", "format": "date", "description": "Creation date (YYYY-MM-DD)."},
        "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1, "description": "Relevant tags."},
        "category": {"const": category, "description": f"Must be exactly \"{category}\" for a {prefix} document."},
    }
    required = ["date created", "tags", "category"]
    for f in EXTRA_REQUIRED.get(prefix, []):
        props[f] = P[f]
        required.append(f)
    for f in EXTRA_OPTIONAL.get(prefix, []):
        props.setdefault(f, P[f])
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": f"https://workflow-kit/schemas/artifacts/{prefix}.schema.json",
        "title": f"{prefix} frontmatter ({label})",
        "description": f"Required YAML frontmatter for a {prefix} ({label}) document. "
                       f"category MUST be \"{category}\". Extra frontmatter keys are allowed.",
        "type": "object",
        "additionalProperties": True,
        "required": required,
        "properties": props,
    }
    path = os.path.join(OUT, f"{prefix}.schema.json")
    with open(path, "w") as fh:
        json.dump(schema, fh, indent=2)
        fh.write("\n")
    written.append(prefix)

print(f"Wrote {len(written)} artifact frontmatter schemas to schemas/artifacts/")
print("Prefixes:", " ".join(written))
