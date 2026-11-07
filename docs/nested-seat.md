# Nested seat

Omarchy-testar must not inject clicks into the host Hyprland seat. Exploration runs inside a **nested** Hyprland instance so `ydotool` / EIS only hit the SUT.

## Rules

- Never point `ydotool` at the host `WAYLAND_DISPLAY` while exploring.
- Start the nested seat with `scripts/nested-seat.sh start`, then launch the SUT inside that env.
- Prefer `scripts/nested-seat.sh run -- <cmd>` so the child inherits the nested Wayland display.
- Stop with `scripts/nested-seat.sh stop`.

## Smoke

```bash
./scripts/nested-seat.sh smoke
```

Passes when the nested compositor answers `hyprctl` (or when `--config-only` verifies the config without starting a compositor — used in CI).

## Layout

| Path | Role |
|------|------|
| `seat/nested/hyprland.conf` | Minimal nested config (no host keybinds) |
| `scripts/nested-seat.sh` | start / stop / status / smoke / run |
| `seat/nested/runtime/` | PID, socket name, logs (gitignored) |
