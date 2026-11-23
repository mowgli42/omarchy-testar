# Nested seat

Omarchy-testar must not inject clicks into the host Hyprland seat. Exploration runs inside a **nested** Hyprland instance so `ydotool` / EIS only hit the SUT.

## Rules

- Never point `ydotool` at the host `WAYLAND_DISPLAY` while exploring.
- Never call `xdotool`.
- Start the nested seat with `scripts/nested-seat.sh start`, then launch the SUT inside that env.
- Prefer `scripts/nested-seat.sh run -- <cmd>` so the child inherits the nested Wayland display.
- Stop with `scripts/nested-seat.sh stop`.
- AT-SPI `do_action` clicks do not inject seat events; still run them from a nested-seat env (or set `OMARCHY_TESTAR_ALLOW_HOST_SEAT=1` only for host-shell plugin summons).

## Smoke

```bash
./scripts/nested-seat.sh smoke
```

Starts nested Hyprland (if needed) and proves `hyprctl` answers on the **nested** instance signature / `wayland-2` (host stays on `wayland-1`). Use `--config-only` in CI when a compositor must not start.

## Actuator

```bash
./scripts/nested-seat.sh smoke
./scripts/live-actuator-smoke.sh   # GTK Probe + AT-SPI click; host focus unchanged
./scripts/live-atspi-scrape.sh     # live AT-SPI tree from a nested GTK app
```

`sim/actuator.py --live --backend atspi|ydotool` refuses the host seat unless `OMARCHY_TESTAR_ALLOW_HOST_SEAT=1`. ydotool needs `ydotoold` with `/dev/uinput` access.

## Window / journal oracle

```bash
source seat/nested/runtime/env
/usr/bin/python3 sim/oracle.py --kill-nested-window foot
# writes sim/out/oracle/{ctrf.json,findings.sarif} with oracle/window
```

## Layout

| Path | Role |
|------|------|
| `seat/nested/hyprland.conf` | Minimal nested config (no host keybinds) |
| `scripts/nested-seat.sh` | start / stop / status / smoke / run |
| `scripts/live-actuator-smoke.sh` | nested AT-SPI click proof |
| `scripts/live-atspi-scrape.sh` | nested live AT-SPI scrape |
| `scripts/live-plugin-click-all.py` | summon + AT-SPI click-all + PNGs |
| `sim/actuator.py` | atspi / ydotool backends |
| `sim/oracle.py` | window / crash-log oracle → CTRF + SARIF |
| `seat/nested/runtime/` | PID, socket name, logs (gitignored) |
