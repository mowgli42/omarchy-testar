# Verification

| Scenario | Tag | Exercised by |
|----------|-----|----------------|
| Manifest is loadable | Validated | `python3 sim/plugin_ui.py` |
| Bar widget summons the panel | Validated | step 1 panel_visible |
| Refresh updates the panel status | Validated | step 2 status Checked |
| Close hides the panel | Validated | step 3 panel_visible false |
| Summon through a running omarchy-shell | Future | not exercised |

Command: `python3 sim/plugin_ui.py`
