#!/bin/bash
# iterm-setup.sh — Automated iTerm2 setup for Workflow Kit
# Run after WFK pull when iTerm2 is detected
# Usage: iterm-setup.sh [--quiet]

set -e
QUIET="${1:-}"

log() { [ "$QUIET" != "--quiet" ] && echo "$1"; }

# --- Check iTerm2 is installed ---
ITERM_PATH=$(mdfind "kMDItemKind == 'Application'" 2>/dev/null | grep -i "iTerm.app" | head -1)
if [ -z "$ITERM_PATH" ]; then
  log "iTerm2 not found — skipping iterm setup"
  exit 0
fi
log "Found iTerm2 at $ITERM_PATH"

# --- 1. Enable Python API ---
CURRENT=$(defaults read com.googlecode.iterm2 EnableAPIServer 2>/dev/null || echo "0")
if [ "$CURRENT" != "1" ]; then
  defaults write com.googlecode.iterm2 EnableAPIServer -bool true
  log "✓ Enabled iTerm2 Python API server"
else
  log "· Python API already enabled"
fi

# --- 2. Install Python venv ---
VENV_DIR="$HOME/.claude/venvs/iterm2"
if [ ! -f "$VENV_DIR/bin/python3" ]; then
  log "Installing iTerm2 Python venv..."
  mkdir -p "$HOME/.claude/venvs"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install -q iterm2
  log "✓ Python venv created at $VENV_DIR"
else
  log "· Python venv already exists"
fi

# --- 3. Install scripts ---
SCRIPTS_DIR="$HOME/.claude/scripts"
mkdir -p "$SCRIPTS_DIR"

# Find the WFK repo or skill source for scripts
SOURCES=(
  "/tmp/wfk-repo/scripts"
  "$HOME/.claude/skills/iterm"
)
for src in "${SOURCES[@]}"; do
  if [ -f "$src/iterm-tab.sh" ]; then
    cp "$src/iterm-tab.sh" "$SCRIPTS_DIR/iterm-tab.sh"
    cp "$src/iterm-notify.sh" "$SCRIPTS_DIR/iterm-notify.sh"
    chmod +x "$SCRIPTS_DIR/iterm-tab.sh" "$SCRIPTS_DIR/iterm-notify.sh"
    log "✓ Scripts installed to $SCRIPTS_DIR"
    break
  fi
done

# --- 4. Shell alias ---
ZSHRC="$HOME/.zshrc"
if [ -f "$ZSHRC" ] && grep -q "alias cld=" "$ZSHRC"; then
  log "· cld alias already in .zshrc"
else
  echo "" >> "$ZSHRC"
  echo "# Claude teammate mode" >> "$ZSHRC"
  echo "alias cld='claude --dangerously-skip-permissions --teammate-mode tmux'" >> "$ZSHRC"
  log "✓ Added cld alias to .zshrc"
fi

# --- 5. Claude Code hooks ---
SETTINGS="$HOME/.claude/settings.json"
if [ -f "$SETTINGS" ]; then
  if grep -q "iterm-notify" "$SETTINGS"; then
    log "· iTerm hooks already in settings.json"
  else
    # Use python to merge hooks into existing settings.json
    python3 << 'PYEOF'
import json, sys

settings_path = sys.argv[1] if len(sys.argv) > 1 else "$HOME/.claude/settings.json"
settings_path = "$HOME/.claude/settings.json".replace("$HOME", __import__("os").environ["HOME"])

with open(settings_path) as f:
    settings = json.load(f)

hooks = settings.get("hooks", {})

# Add Stop hook if not present
stop_hooks = hooks.get("Stop", [])
has_notify = any("iterm-notify" in str(h) for h in stop_hooks)
if not has_notify:
    stop_hooks.append({
        "matcher": "",
        "hooks": [{
            "type": "command",
            "command": "~/.claude/scripts/iterm-notify.sh flash"
        }]
    })
    hooks["Stop"] = stop_hooks

# Add UserPromptSubmit hook if not present
prompt_hooks = hooks.get("UserPromptSubmit", [])
has_clear = any("iterm-notify" in str(h) for h in prompt_hooks)
if not has_clear:
    prompt_hooks.append({
        "matcher": "",
        "hooks": [{
            "type": "command",
            "command": "~/.claude/scripts/iterm-notify.sh clear"
        }]
    })
    hooks["UserPromptSubmit"] = prompt_hooks

settings["hooks"] = hooks

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
PYEOF
    log "✓ Added iTerm notification hooks to settings.json"
  fi
else
  log "⚠ No settings.json found — hooks not configured"
fi

# --- 6. iTerm2 profile settings ---
# Set via plist (takes effect on next iTerm2 launch)
PLIST="$HOME/Library/Preferences/com.googlecode.iterm2.plist"
if [ -f "$PLIST" ]; then
  # Find the default/first profile and configure it
  PROFILE_COUNT=$(/usr/libexec/PlistBuddy -c "Print ':New Bookmarks'" "$PLIST" 2>/dev/null | grep -c "Dict" || echo "0")

  for i in $(seq 0 $((PROFILE_COUNT - 1))); do
    PROFILE_NAME=$(/usr/libexec/PlistBuddy -c "Print ':New Bookmarks:${i}:Name'" "$PLIST" 2>/dev/null || echo "")
    # Only configure the Default profile — skip all others
    [ "$PROFILE_NAME" != "Default" ] && continue
    IS_DEFAULT="$PROFILE_NAME"

    # Set Title Components to 1 (Session Name)
    /usr/libexec/PlistBuddy -c "Delete ':New Bookmarks:${i}:Title Components'" "$PLIST" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Add ':New Bookmarks:${i}:Title Components' integer 1" "$PLIST" 2>/dev/null || true

    # Set working directory (only if not already custom)
    CUSTOM=$(/usr/libexec/PlistBuddy -c "Print ':New Bookmarks:${i}:Custom Directory'" "$PLIST" 2>/dev/null || echo "No")
    if [ "$CUSTOM" != "Yes" ]; then
      # Detect vault path
      VAULT_PATH=""
      for candidate in "$HOME/Documents/Vaults" "$HOME/Vaults"; do
        if [ -d "$candidate" ]; then
          VAULT_PATH="$candidate"
          break
        fi
      done
      if [ -n "$VAULT_PATH" ]; then
        /usr/libexec/PlistBuddy -c "Set ':New Bookmarks:${i}:Custom Directory' 'Yes'" "$PLIST" 2>/dev/null || \
          /usr/libexec/PlistBuddy -c "Add ':New Bookmarks:${i}:Custom Directory' string 'Yes'" "$PLIST" 2>/dev/null || true
        /usr/libexec/PlistBuddy -c "Set ':New Bookmarks:${i}:Working Directory' '$VAULT_PATH'" "$PLIST" 2>/dev/null || \
          /usr/libexec/PlistBuddy -c "Add ':New Bookmarks:${i}:Working Directory' string '$VAULT_PATH'" "$PLIST" 2>/dev/null || true
        log "✓ Profile '$IS_DEFAULT': initial directory → $VAULT_PATH"
      fi
    fi
  done
  log "✓ Profile title set to Session Name (restart iTerm2 to apply)"
else
  log "⚠ iTerm2 plist not found — profile settings not configured"
fi

# --- 7. Download Spacedust color scheme ---
COLORS_DIR="$HOME/.claude/iterm-colors"
if [ ! -f "$COLORS_DIR/Spacedust.itermcolors" ]; then
  mkdir -p "$COLORS_DIR"
  curl -sL -o "$COLORS_DIR/Spacedust.itermcolors" \
    "https://raw.githubusercontent.com/mbadolato/iTerm2-Color-Schemes/master/schemes/Spacedust.itermcolors" 2>/dev/null
  if [ -f "$COLORS_DIR/Spacedust.itermcolors" ]; then
    log "✓ Downloaded Spacedust color scheme (run 'open $COLORS_DIR/Spacedust.itermcolors' to install)"
  fi
else
  log "· Spacedust color scheme already downloaded"
fi

# --- Summary ---
echo ""
echo "═══════════════════════════════════════════"
echo " iTerm2 Setup Complete"
echo "═══════════════════════════════════════════"
echo ""
echo " Automated:"
echo "   • Python API enabled"
echo "   • Python venv installed"
echo "   • Scripts installed"
echo "   • Shell alias (cld) configured"
echo "   • Claude Code hooks configured"
echo "   • Profile settings updated (plist)"
echo ""
echo " Manual steps needed (one-time):"
echo "   1. Restart iTerm2 for plist changes"
echo "   2. Confirm Python API consent dialog"
echo "   3. Settings → Profiles → General → Title"
echo "      → verify 'Session Name' is selected"
echo "   4. Settings → Profiles → Terminal"
echo "      → enable 'Flash tab bar when bell occurs'"
echo "   5. (Optional) Install Spacedust theme:"
echo "      open $COLORS_DIR/Spacedust.itermcolors"
echo ""
