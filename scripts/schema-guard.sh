#!/usr/bin/env bash
# Pre-write hook: WARN on Write/Edit tool calls to SPC/PL files that assert DB schema
# (qualified table refs, SQL DML/DDL, catalog meta-commands) without citing a schema audit.
#
# Per CLAUDE.md "Verify before modifying OR recommending" rule.
#
# Soft-warn mode (ship state): prints enforcement message to stderr but exits 0.
# After ~7 days observation, promote the high-confidence qualified-table subset to
# blocking (exit 2). Do NOT promote here.
#
# Escape hatch: frontmatter  schema_audit: "n/a (reason)"  passes silently.
# Pass condition: frontmatter or body wikilink to a  RE - * Schema Audit*  file.
#
# Receives the tool input JSON via stdin.
#
# CUSTOMIZE for your org: edit the QUALIFIED_RE schema list below to match the schema
# names in your project's database (e.g. "public", "app", "billing", "analytics").

set -uo pipefail

# Capture stdin (the tool input JSON)
INPUT=$(cat)

# Tool name is in $CLAUDE_TOOL_NAME (set by Claude Code) or extract from JSON
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
if [ -z "$TOOL_NAME" ]; then
    TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name', d.get('toolName', '')))" 2>/dev/null || echo "")
fi

# Only apply to Write/Edit. Migrations come later via a separate hook variant.
case "$TOOL_NAME" in
    Write|Edit) ;;
    *) exit 0 ;;
esac

# Extract content + file_path. Schema differs across tools:
#   Write: tool_input.content
#   Edit:  tool_input.new_string
CONTENT=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
ti = d.get('tool_input', d.get('toolInput', {}))
for key in ('content', 'new_string'):
    if key in ti:
        print(ti[key])
        break
" 2>/dev/null || echo "")

FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
ti = d.get('tool_input', d.get('toolInput', {}))
print(ti.get('file_path', ''))
" 2>/dev/null || echo "")

# Path filter: only SPC - *.md or PL - *.md files
BASENAME="${FILE_PATH##*/}"
case "$BASENAME" in
    "SPC - "*.md|"PL - "*.md) ;;
    *) exit 0 ;;
esac

# Escape hatch: schema_audit: "n/a..." in frontmatter (anywhere in content for a Write;
# for an Edit we may only see a slice, so a missing escape on Edit is acceptable and
# the audit-link check below will still pass if the frontmatter carries it).
if echo "$CONTENT" | grep -qE '^[[:space:]]*schema_audit:[[:space:]]*"?n/a'; then
    exit 0
fi

# Scope tightener: only treat schema CLAIMS as gate-worthy when the file declares a
# data-model section. This reduces false positives on prose mentions in narrative SPCs.
if ! echo "$CONTENT" | grep -qE '^(## Data Model|## Schema|### Tables)\b'; then
    exit 0
fi

# Detection regex set. First match flips MATCHED + records the pattern label.
MATCHED=""
MATCH_LABEL=""

# 1. Qualified table refs (highest confidence).
# CUSTOMIZE: replace {{YOUR_SCHEMAS}} with a pipe-delimited list of your DB schema names.
# Example: '\b(public|app|billing|analytics)\.[a-z_][a-z0-9_]+\b'
QUALIFIED_RE='\b(public|{{YOUR_SCHEMAS}})\.[a-z_][a-z0-9_]+\b'
if echo "$CONTENT" | grep -qE "$QUALIFIED_RE"; then
    MATCHED=1
    MATCH_LABEL=$(echo "$CONTENT" | grep -oE "$QUALIFIED_RE" | head -1)
fi

# 2. SQL DML/DDL with identifier
if [ -z "$MATCHED" ]; then
    SQL_RE='\b(FROM|JOIN|INSERT[[:space:]]+INTO|UPDATE|DELETE[[:space:]]+FROM|ALTER[[:space:]]+TABLE|CREATE[[:space:]]+TABLE)[[:space:]]+[a-z_][a-z0-9_."]+'
    if echo "$CONTENT" | grep -qiE "$SQL_RE"; then
        MATCHED=1
        MATCH_LABEL=$(echo "$CONTENT" | grep -oiE "$SQL_RE" | head -1)
    fi
fi

# 3. Catalog meta-commands
if [ -z "$MATCHED" ]; then
    if echo "$CONTENT" | grep -qE '(\\d\+?[[:space:]]+\w|pg_catalog|information_schema)'; then
        MATCHED=1
        MATCH_LABEL=$(echo "$CONTENT" | grep -oE '(\\d\+?[[:space:]]+\w+|pg_catalog|information_schema)' | head -1)
    fi
fi

# No schema claims under a Data Model heading → pass silently
if [ -z "$MATCHED" ]; then
    exit 0
fi

# Verification-artifact check.
# (a) frontmatter  schema_audit:  field pointing at a wikilink
# (b) any body wikilink whose target filename matches  RE - * Schema Audit*
HAS_AUDIT_LINK=""
if echo "$CONTENT" | grep -qE '^[[:space:]]*schema_audit:[[:space:]]*"?\[\[RE - .*Schema Audit'; then
    HAS_AUDIT_LINK=1
elif echo "$CONTENT" | grep -qE '\[\[RE - [^]]*Schema Audit[^]]*\]\]'; then
    HAS_AUDIT_LINK=1
fi

# Optional: verify the linked file actually exists in the project's reports/ tree.
# Derive project root by walking up to  02_Projects/<project>/
if [ -n "$HAS_AUDIT_LINK" ]; then
    PROJECT_DIR=$(python3 -c "
import sys, os
p = '$FILE_PATH'
parts = p.split('/')
try:
    i = parts.index('02_Projects')
    print('/'.join(parts[:i+2]))
except ValueError:
    print('')
")
    if [ -n "$PROJECT_DIR" ] && [ -d "$PROJECT_DIR/reports" ]; then
        # Extract the audit filename from the first matching wikilink
        AUDIT_NAME=$(echo "$CONTENT" | grep -oE '\[\[RE - [^]|]*Schema Audit[^]|]*' | head -1 | sed 's/^\[\[//')
        if [ -n "$AUDIT_NAME" ]; then
            FOUND=$(find "$PROJECT_DIR/reports" -type f -name "${AUDIT_NAME}*.md" 2>/dev/null | head -1)
            if [ -z "$FOUND" ]; then
                # Linked but file not found — keep warning; soft-warn mode won't block.
                HAS_AUDIT_LINK=""
                MATCH_LABEL="$MATCH_LABEL (linked audit '${AUDIT_NAME}' not found)"
            fi
        fi
    fi
fi

# Decision
if [ -n "$HAS_AUDIT_LINK" ]; then
    exit 0
fi

# Soft-warn: print enforcement message, but proceed.
cat >&2 <<EOF
SCHEMA-GUARD (soft-warn): This SPC/PL asserts DB schema (matched: $MATCH_LABEL)
  but cites no schema audit. Recommended: /schema-audit --spec $FILE_PATH
  then add  schema_audit: "[[RE - <name> Schema Audit]]"  to frontmatter.
  Escape: schema_audit: "n/a (reason)"
  Source: CLAUDE.md "Verify before modifying OR recommending"
EOF

exit 0
