# omarchy-testar

Scriptless GUI explorer for apps on [Omarchy](https://omarchy.org) (Arch + Hyprland + Quickshell). Same loop as [TESTAR](https://github.com/TESTARtool/TESTAR_dev): scrape state, derive actions, pick one, execute, oracle. No recorded scripts for the explorer. Scripted checks stay in Gherkin.

This repo is the OpenSpec plan plus a fixture-driven simulator. Nested-seat scripts and an AT-SPI scrape module are in place; live ydotool runs are still Future.

## Why not port TESTAR

TESTAR scrapes Windows UI Automation and browser DOMs. Omarchy is Wayland. No global coordinates, no unsolicited input injection. The loop is worth keeping. The connector is not.

## Adoption formats

Canonical run report is [CTRF](https://github.com/ctrf-io/ctrf) JSON (schema, attachments, retries). CI compatibility export is JUnit XML. Oracle findings that should show up in code scanning export as SARIF 2.1. Human scenarios are Gherkin. See [docs/standards.md](docs/standards.md).

## Layout

```
openspec/          living specs + the bootstrap change
features/          Gherkin mirror
docs/              standards, nested seat, plugin Accessible markers
BEADS.md           bd-backed production rebuild
sim/               fixture app + explorers
```

## Demo

```bash
python3 sim/explore.py              # generic fixture walk
python3 sim/plugin_ui.py            # Omarchy plugin manifest + panel controls
python3 sim/snarksentinel_click.py  # click-all SnarkSentinel buttons + crash-log oracle
python3 sim/snarksentinel_click.py --inject-crash
python3 sim/snarksentinel_click.py --scrape ../snarksentinel/omarchy-plugin
python3 sim/replay.py --sequence sim/out/sequence.jsonl --app sim/fixture_app.json
python3 sim/atspi.py                              # fixture AT-SPI → button actions
./scripts/nested-seat.sh smoke --config-only       # nested Hyprland config check
```

**Do not** point `ydotool` at the host seat. See [docs/nested-seat.md](docs/nested-seat.md).

Plugin under test: `examples/status-panel` (bar widget summons a panel). SnarkSentinel click-all uses `sim/fixtures/snarksentinel/` (frozen from `Panel.qml` / `BarWidget.qml`). Live `omarchy-shell` summon is not run here.

**Buttons live in QML**, but the explorer does not parse a script of clicks. It derives `role=button` actions (from `Accessible.name` or `Button.text`), clicks each reachable name once, writes a screenshot after every click, then checks JSONL for crash-shaped lines.

**Plugin authors:** mark controls so testar can find them — [docs/plugin-accessible-markers.md](docs/plugin-accessible-markers.md).

## Workflow

Spec, then beads, then implement. [openspec/WORKFLOW.md](openspec/WORKFLOW.md).
