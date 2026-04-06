# Obsidian Troubleshooting

## Vault Path Verification (ALWAYS FIRST)

Before investigating plugin conflicts, CSS issues, template problems, or layout bugs:

1. Check the `.obsidian/` folder exists at the expected vault root
2. Confirm the user has the correct directory open in Obsidian (not a parent or sibling directory)
3. Expected vault paths:
   - Work Vault: `{{VAULT_PATH}}/Work Vault/`
   - Personal Vault: `{{VAULT_PATH}}/Personal Vault/`

**Common mistake:** User opens Obsidian on the parent `Vaults/` directory instead of the specific vault. This causes daily notes to generate in wrong locations, plugins to not find templates, and community plugins to appear missing.

Only proceed to plugin or layout debugging after vault path is confirmed correct.

## Plugin Conflict Diagnosis

- Core plugins (Daily Notes, Templates) take precedence over community plugins
- If both core Daily Notes and Periodic Notes are enabled, behavior is unpredictable - disable one
- Check both enabled/disabled tabs in Settings > Community Plugins
- Hot-reload after plugin changes: Cmd+Shift+R or restart Obsidian

## Workspace Layout Changes

For panel/sidebar/right-pane layout changes, **edit config files directly** instead of giving UI navigation instructions. UI instructions depend on current vault state, plugin order, and pane layout - they break easily.

- **Config location:** `.obsidian/workspace.json`
- After editing, user must reload Obsidian (Cmd+Shift+R) for changes to apply

### Adding a sidebar panel (Calendar, Outline, etc.)

Read the current `workspace.json`, find the appropriate split pane (`right` for right sidebar), and add a leaf node:

```json
{
  "id": "<unique-id>",
  "type": "leaf",
  "state": {
    "type": "calendar",
    "state": {}
  }
}
```

Common view types: `calendar`, `outline`, `graph`, `backlink`, `tag`, `file-explorer`

### When to use UI instructions instead

Only give manual UI instructions when:
- The user explicitly asks for click-by-click guidance
- The change is a one-time toggle (e.g., enabling a plugin in settings)
- The workspace.json structure for that change is unclear

Default to config edits for anything involving panel placement, sidebar composition, or workspace layout.
