# omarchy-testar

Scriptless GUI explorer for apps on [Omarchy](https://omarchy.org) (Arch + Hyprland + Quickshell). Same loop as [TESTAR](https://github.com/TESTARtool/TESTAR_dev): scrape state, derive actions, pick one, execute, oracle. No recorded scripts for the explorer. Scripted checks stay in Gherkin.

This repo is the OpenSpec plan plus a fixture-driven simulator. It does not drive a live Hyprland seat yet.

## Why not port TESTAR

TESTAR scrapes Windows UI Automation and browser DOMs. Omarchy is Wayland. No global coordinates, no unsolicited input injection. The loop is worth keeping. The connector is not.

## Adoption formats

Canonical run report is [CTRF](https://github.com/ctrf-io/ctrf) JSON (schema, attachments, retries). CI compatibility export is JUnit XML. Oracle findings that should show up in code scanning export as SARIF 2.1. Human scenarios are Gherkin. See [docs/standards.md](docs/standards.md).

## Layout

```
openspec/          living specs + the bootstrap change
features/          Gherkin mirror
docs/standards.md  format decision
BEADS.md           production rebuild, not implemented
sim/               fixture app + explore.py (validated slice)
```

## Demo

```bash
python3 sim/explore.py          # generic fixture walk
python3 sim/plugin_ui.py        # Omarchy plugin manifest + panel controls
```

Plugin under test: `examples/status-panel` (bar widget summons a panel). Live `omarchy-shell` summon is not run here.

## Workflow

Spec, then beads, then implement. [openspec/WORKFLOW.md](openspec/WORKFLOW.md).
