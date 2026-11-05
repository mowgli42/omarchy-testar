# Design: SnarkSentinel click-all

## QML vs accessibility

Buttons **are** declared in QML (`omarchy-plugin/Panel.qml`, `BarWidget.qml`). That is the authoring source, not the runtime selector.

At runtime TESTAR-style discovery uses the accessibility tree (AT-SPI / `Accessible.name`). SnarkSentinel mostly sets `Button { text: "…" }` and does not mark `Accessible.name` / `objectName` the way `examples/status-panel` does. Qt Quick Controls typically expose `text` as the accessible name, so the prototype treats:

1. `Accessible.name` when present
2. else `Button.text` string literals (including both arms of ternary texts)

as the button inventory. Live AT-SPI would see the same names once the panel is summoned.

## Click-everything policy

Not a scripted path. The explorer:

1. Starts from a known initial state (`bar` → summon panel).
2. Derives enabled actions with `role == button` only.
3. Picks the first unvisited enabled button (deterministic coverage).
4. Executes the transition from the fixture state graph.
5. Screenshots, then checks crash logs.
6. Stops when every reachable button has been clicked once, or an oracle fires.

## Oracles

- **Crash log:** JSONL lines with `level` in `{critical, fatal}` or message/exception matching `segfault|SIGSEGV|Aborted|core dumped|Traceback`.
- **Screenshot:** one SVG frame per step under `screenshots/` listed as a CTRF attachment path (placeholder until a live seat captures PNGs).

## Fixture boundary

`sim/fixtures/snarksentinel/app.json` freezes the reachable button graph so the demo runs without a sibling checkout. `sim/snarksentinel_click.py --scrape <plugin-dir>` regenerates the inventory from live QML for comparison.
