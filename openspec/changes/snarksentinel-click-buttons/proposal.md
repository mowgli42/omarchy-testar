# Proposal: SnarkSentinel click-all buttons prototype

## Why

Prove the TESTAR loop against a real Omarchy plugin (SnarkSentinel) without writing per-button scripts: derive accessible buttons, click each once, screenshot after the click, and fail on crash-shaped log lines.

## What

- Scrape `Button` controls from SnarkSentinel QML (`text` / `Accessible.name`) as the button-only action surface.
- Coverage policy: click every enabled unvisited button (no recorded sequence).
- After each click: write a screenshot attachment and run a crash-log oracle.
- Emit CTRF / JUnit / SARIF plus `sequence.jsonl` under `sim/out/snarksentinel/`.

## Non-goals

- Live Hyprland / AT-SPI / ydotool seat (still Future).
- Typing into text fields, menu traversal beyond buttons, or random long walks.
- Mutating the live SnarkSentinel install or applying firewall plans on the host.
