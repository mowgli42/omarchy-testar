# Demo

Fixture app, no Hyprland:

```bash
python3 sim/explore.py
```

Plugin UI (example status panel):

```bash
python3 sim/plugin_ui.py
```

Expect `sim/out/plugin-sequence.jsonl` with summon, Refresh, Close, and `sim/out/plugin-walk.html`.

SnarkSentinel click-all (buttons only, screenshots + crash-log oracle):

```bash
python3 sim/snarksentinel_click.py
python3 sim/snarksentinel_click.py --inject-crash
```

Expect `sim/out/snarksentinel/sequence.jsonl`, per-step `screenshots/step-*.svg`, `ctrf.json`, and on `--inject-crash` a failed CTRF with `oracle/crash-log` in `findings.sarif`. Open `sim/out/snarksentinel/walk.html` for the step list.

On a real Omarchy session the same plugin is `omarchy plugin add` of this repo, then `omarchy-shell summon example.status-panel`. SnarkSentinel live seat is tagged `@future`.