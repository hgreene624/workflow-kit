#!/bin/bash
# iterm-tab.sh — Set iTerm2 tab title and color by work type
# Usage:
#   iterm-tab.sh <type> [title]       — set color + title
#   iterm-tab.sh title <title>        — set title only (no color change)
#   iterm-tab.sh color <r> <g> <b>    — set custom color (no title change)
# Types: pickup, infra, feature, bug, reset

PYTHON="$HOME/.claude/venvs/iterm2/bin/python3"
VENV_DIR="$HOME/.claude/venvs/iterm2"

# Ensure venv exists
if [ ! -f "$PYTHON" ]; then
  python3 -m venv "$VENV_DIR" && "$VENV_DIR/bin/pip" install -q iterm2
fi

# --- TTY detection (for color escape sequences) ---
TTY_PATH=""
CANDIDATE=$(ps -o tty= -p $(ps -o ppid= -p $(ps -o ppid= -p $$) 2>/dev/null) 2>/dev/null | head -1 | tr -d ' ')
if [ -n "$CANDIDATE" ] && [ -w "/dev/$CANDIDATE" ]; then
  TTY_PATH="/dev/$CANDIDATE"
fi
if [ -z "$TTY_PATH" ]; then
  for t in /dev/ttys{000..010}; do
    if [ -w "$t" ]; then
      TTY_PATH="$t"
      break
    fi
  done
fi

set_title() {
  local title="$1"
  "$PYTHON" - "$title" << 'PYEOF'
import iterm2, sys
async def main(connection):
    app = await iterm2.async_get_app(connection)
    window = app.current_terminal_window
    if window:
        await window.current_tab.async_set_title(sys.argv[1])
iterm2.run_until_complete(main)
PYEOF
}

set_color() {
  local r="$1" g="$2" b="$3"
  if [ -z "$TTY_PATH" ]; then
    echo "ERROR: No writable TTY found for color"
    return 1
  fi
  echo -ne "\033]6;1;bg;red;brightness;${r}\a" > "$TTY_PATH"
  echo -ne "\033]6;1;bg;green;brightness;${g}\a" > "$TTY_PATH"
  echo -ne "\033]6;1;bg;blue;brightness;${b}\a" > "$TTY_PATH"
}

clear_color() {
  [ -n "$TTY_PATH" ] && echo -ne "\033]6;1;bg;*;default\a" > "$TTY_PATH"
}

# --- Title-only mode ---
if [ "$1" = "title" ]; then
  shift
  TITLE="$*"
  if [ -z "$TITLE" ]; then
    echo "Usage: iterm-tab.sh title <title>"
    exit 1
  fi
  set_title "$TITLE"
  echo "Tab title: $TITLE"
  exit 0
fi

# --- Custom color mode ---
if [ "$1" = "color" ]; then
  if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
    echo "Usage: iterm-tab.sh color <r> <g> <b>"
    exit 1
  fi
  set_color "$2" "$3" "$4"
  echo "Tab color: rgb($2, $3, $4)"
  exit 0
fi

# --- Type-based mode ---
TYPE="${1:-reset}"
TITLE="${2:-}"

case "$TYPE" in
  pickup)
    R=78; G=154; B=190   # Steel blue
    [ -z "$TITLE" ] && TITLE="Pickup"
    ;;
  infra)
    R=190; G=120; B=50   # Warm amber
    [ -z "$TITLE" ] && TITLE="Infrastructure"
    ;;
  feature)
    R=80; G=160; B=90    # Forest green
    [ -z "$TITLE" ] && TITLE="Feature Dev"
    ;;
  bug)
    R=190; G=60; B=60    # Muted red
    [ -z "$TITLE" ] && TITLE="Bug Fix"
    ;;
  reset)
    clear_color
    [ -z "$TITLE" ] && TITLE="Vaults"
    set_title "$TITLE"
    echo "Tab reset: $TITLE"
    exit 0
    ;;
  *)
    echo "Unknown type: $TYPE"
    echo "Usage: iterm-tab.sh <pickup|infra|feature|bug|reset> [title]"
    echo "       iterm-tab.sh title <title>"
    echo "       iterm-tab.sh color <r> <g> <b>"
    exit 1
    ;;
esac

set_color "$R" "$G" "$B"
set_title "$TITLE"

echo "Tab set: $TITLE ($TYPE)"
