#!/bin/bash
# iterm-notify.sh — Flash the tab to indicate Claude is waiting for input
# Usage: iterm-notify.sh [flash|clear]
# Called by Claude Code Stop hook (flash) and UserPromptSubmit hook (clear)

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
[ -z "$TTY_PATH" ] && exit 0

ACTION="${1:-flash}"

if [ "$ACTION" = "clear" ]; then
  # Reset to default (no color)
  echo -ne "\033]6;1;bg;*;default\a" > "$TTY_PATH"
  exit 0
fi

# Flash: bright pulse 3 times
for i in 1 2 3; do
  echo -ne "\033]6;1;bg;red;brightness;255\a" > "$TTY_PATH"
  echo -ne "\033]6;1;bg;green;brightness;220\a" > "$TTY_PATH"
  echo -ne "\033]6;1;bg;blue;brightness;100\a" > "$TTY_PATH"
  sleep 0.3
  echo -ne "\033]6;1;bg;*;default\a" > "$TTY_PATH"
  sleep 0.3
done

# Leave a soft gold "ready" indicator
echo -ne "\033]6;1;bg;red;brightness;200\a" > "$TTY_PATH"
echo -ne "\033]6;1;bg;green;brightness;170\a" > "$TTY_PATH"
echo -ne "\033]6;1;bg;blue;brightness;80\a" > "$TTY_PATH"
