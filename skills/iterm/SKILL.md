---
name: iterm
description: >-
  Set iTerm2 tab title and color to reflect the current work context.
  Use this skill when starting work, switching context, loading a pickup,
  or when the user says "set tab", "color tab", "label tab", "iterm",
  or "tag this". Also trigger proactively when the work type is clear
  (e.g., after loading a PIC, starting a feature, triaging a bug).
---

# iTerm — Tab Title & Color

Set the iTerm2 tab title and color so the user can visually distinguish work contexts across tabs at a glance.

## Setup (New Machine)

Run these steps once per machine to enable all features.

### 1. iTerm2 Settings (UI)

- **Settings → Profiles → General → Title** → set to **"Session Name"** (not "Name")
- **Settings → Profiles → General → Initial Directory** → select **"Directory:"** and enter your Vaults path
- **Settings → Profiles → Terminal** → enable **"Flash tab bar when bell occurs"**
- **Settings → Appearance** → enable **Tall Tab Bar** (optional, better visibility)

### 2. Enable Python API

```bash
defaults write com.googlecode.iterm2 EnableAPIServer -bool true
```

Then restart iTerm2 and confirm the consent dialog.

### 3. Install Python venv

```bash
mkdir -p ~/.claude/venvs
python3 -m venv ~/.claude/venvs/iterm2
~/.claude/venvs/iterm2/bin/pip install iterm2
```

### 4. Install scripts

Copy these files from WFK or another machine:

```
~/.claude/scripts/iterm-tab.sh      # Tab color + title by work type
~/.claude/scripts/iterm-notify.sh   # Flash tab when Claude is waiting
```

Make them executable:

```bash
chmod +x ~/.claude/scripts/iterm-tab.sh ~/.claude/scripts/iterm-notify.sh
```

### 5. Shell alias

Add to `~/.zshrc`:

```bash
alias cld='claude --dangerously-skip-permissions --teammate-mode tmux'
```

### 6. Claude Code hooks

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/scripts/iterm-notify.sh flash"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/scripts/iterm-notify.sh clear"
          }
        ]
      }
    ]
  }
}
```

### 7. (Optional) Color scheme

```bash
curl -sL -o /tmp/Spacedust.itermcolors \
  "https://raw.githubusercontent.com/mbadolato/iTerm2-Color-Schemes/master/schemes/Spacedust.itermcolors"
open /tmp/Spacedust.itermcolors
# Then select it in Settings → Profiles → Colors → Color Presets
```

## How it works

- **Tab colors**: iTerm2 escape sequences written directly to the controlling TTY
- **Tab titles**: iTerm2 Python API (`tab.async_set_title()`) — the only method that persists while Claude Code is running, because Claude Code continuously resets the session name via OSC escape sequences
- **Ready flash**: Stop hook fires `iterm-notify.sh flash` → tab pulses gold 3x then stays gold. UserPromptSubmit hook fires `iterm-notify.sh clear` → resets to default color.

### Script locations

| Script | Purpose |
|--------|---------|
| `~/.claude/scripts/iterm-tab.sh` | Set tab color + title by work type |
| `~/.claude/scripts/iterm-notify.sh` | Flash/clear tab for input notifications |

### Work types and colors

| Type      | Color         | RGB           | When to use                                    |
|-----------|---------------|---------------|------------------------------------------------|
| `pickup`  | Steel blue    | 78, 154, 190  | Loading or working on a PIC                    |
| `infra`   | Warm amber    | 190, 120, 50  | VPS, Docker, Traefik, CI/CD, deployment        |
| `feature` | Forest green  | 80, 160, 90   | New feature development                        |
| `bug`     | Muted red     | 190, 60, 60   | Bug fixes, issue triage                        |
| `reset`   | Default       | —             | Clear color, return to neutral                 |

### Usage

```bash
# Set color + title by work type
~/.claude/scripts/iterm-tab.sh <type> [title]

# Set title only (no color change)
~/.claude/scripts/iterm-tab.sh title "My Title"

# Set custom RGB color (no title change)
~/.claude/scripts/iterm-tab.sh color <r> <g> <b>

# Flash tab (waiting notification)
~/.claude/scripts/iterm-notify.sh flash

# Clear flash (return to default)
~/.claude/scripts/iterm-notify.sh clear
```

Examples:
```bash
~/.claude/scripts/iterm-tab.sh pickup "PIC - Flora KB Migration"
~/.claude/scripts/iterm-tab.sh feature "Feature - Meeting Notes Pipeline"
~/.claude/scripts/iterm-tab.sh infra "Infra - Traefik SSL Renewal"
~/.claude/scripts/iterm-tab.sh bug "Bug - Portal Auth Loop"
~/.claude/scripts/iterm-tab.sh reset "Vaults - Claude"
~/.claude/scripts/iterm-tab.sh title "Planning Session"
~/.claude/scripts/iterm-tab.sh color 150 80 200
```

## When to trigger

### Proactive (no user prompt needed)
- **After loading a PIC** → `pickup` type, title = PIC name
- **After /orient when work type is obvious** → set accordingly
- **When user starts a clearly-typed task** → set accordingly

### On request
- User says "set tab", "color tab", "label this", "iterm", "tag this"
- User wants to rename or recolor the current tab

### On context switch
- When pivoting from one work type to another, update the tab to reflect the new context

## Rules

1. Always include a short, descriptive title — not just the type name
2. Title format: `Type - Brief Description` (e.g., `Feature - Email Templates`)
3. When in doubt about type, ask the user
4. Reset the tab when work is complete or session is ending
