#!/usr/bin/env bash
# Pre-write hook: WARN on Write/Edit/NotebookEdit tool calls that introduce em dashes (U+2014, —)
# into markdown content. Per Vault CLAUDE.md "No em dashes" rule.
#
# Soft-warn mode (set 2026-05-19): hook prints a warning to stderr but exits 0 so writes proceed.
# The rule stays canonical in CLAUDE.md and WP - General; this hook is a reminder, not a gate.
# To restore blocking behavior, change `exit 0` at the bottom back to `exit 2`.
#
# Receives the tool input JSON via stdin.

set -uo pipefail

# Capture stdin (the tool input JSON)
INPUT=$(cat)

# Tool name is in $CLAUDE_TOOL_NAME (set by Claude Code) or extract from JSON
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
if [ -z "$TOOL_NAME" ]; then
    TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name', d.get('toolName', '')))" 2>/dev/null || echo "")
fi

# Only apply to file-writing tools
case "$TOOL_NAME" in
    Write|Edit|NotebookEdit) ;;
    *) exit 0 ;;
esac

# Extract the content that's about to be written.
# Schema differs across tools:
#   Write:        tool_input.content
#   Edit:         tool_input.new_string
#   NotebookEdit: tool_input.new_source
# File path: tool_input.file_path or tool_input.notebook_path
CONTENT=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
ti = d.get('tool_input', d.get('toolInput', {}))
# Try each tool's content key
for key in ('content', 'new_string', 'new_source'):
    if key in ti:
        print(ti[key])
        break
" 2>/dev/null || echo "")

FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
ti = d.get('tool_input', d.get('toolInput', {}))
for key in ('file_path', 'notebook_path'):
    if key in ti:
        print(ti[key])
        break
" 2>/dev/null || echo "")

# Only enforce on markdown files (the rule is about vault docs)
case "$FILE_PATH" in
    *.md|*.MD|*.markdown) ;;
    *) exit 0 ;;
esac

# Scan for U+2014 em dash
if echo "$CONTENT" | grep -q $'\xe2\x80\x94'; then
    # Count occurrences for the warning message
    COUNT=$(echo "$CONTENT" | grep -o $'\xe2\x80\x94' | wc -l | tr -d ' ')
    echo "WARN: $COUNT em dash(es) (U+2014) in content written to $FILE_PATH. Per Vault CLAUDE.md 'No em dashes' rule, prefer commas, periods, or parentheses. (Soft-warn mode; write proceeds.)" >&2
fi

exit 0
