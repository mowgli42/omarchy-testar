# Screenshot fallback state source

When AT-SPI returns an empty tree, omarchy-testar can derive click targets from a labeled region map. This is a **separate** state source from AT-SPI — higher false-action rate, opt-in only.

## Rules

- Do not merge screenshot actions into an AT-SPI inventory blindly.
- Prefer AT-SPI whenever the accessibility gate passes.
- Region maps stand in for template / vision match until a real matcher lands.

## Fixture

`sim/fixtures/screenshot_map.json` lists `[x, y, w, h]` boxes and roles. The click point is the box center.

```bash
python3 sim/screenshot_fallback.py
python3 sim/screenshot_fallback.py --json
```

Acceptance: at least one `role=button` action is derived when the map is loaded (the empty-tree case).
