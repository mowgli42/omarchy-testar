#!/usr/bin/env bash
# Prove nested-seat AT-SPI click without injecting into the host seat.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="$ROOT/sim/out/actuator"
mkdir -p "$OUT"

[[ -f seat/nested/runtime/env ]] || {
  echo "start nested seat first: ./scripts/nested-seat.sh smoke" >&2
  exit 1
}
# shellcheck disable=SC1091
source seat/nested/runtime/env

hyprctl -i "${OMARCHY_TESTAR_HOST_HYPR}" activewindow -j >"$OUT/host-before.json"

./scripts/nested-seat.sh run -- /usr/bin/python3 - <<'PY' &
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

win = Gtk.Window(title="testar-nested")
win.set_default_size(320, 160)
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
box.set_margin_top(12)
box.set_margin_bottom(12)
box.set_margin_start(12)
box.set_margin_end(12)
btn = Gtk.Button(label="Probe")
state = {"n": 0}

def on_click(_):
    state["n"] += 1
    btn.set_label(f"Clicked-{state['n']}")
    print(f"CLICKED {state['n']}", flush=True)
    GLib.timeout_add(200, Gtk.main_quit)

btn.connect("clicked", on_click)
box.pack_start(btn, True, True, 0)
win.add(box)
win.connect("destroy", Gtk.main_quit)
win.show_all()
GLib.timeout_add(15000, Gtk.main_quit)
Gtk.main()
PY
GTK_PID=$!
sleep 0.8

/usr/bin/python3 sim/actuator.py --live --backend atspi --name Probe | tee "$OUT/live-smoke.json"
sleep 0.3
wait "$GTK_PID" || true

hyprctl -i "${OMARCHY_TESTAR_HOST_HYPR}" activewindow -j >"$OUT/host-after.json"

/usr/bin/python3 - <<PY
import json
from pathlib import Path
out = Path("$OUT")
before = json.loads((out / "host-before.json").read_text())
after = json.loads((out / "host-after.json").read_text())
step = json.loads((out / "live-smoke.json").read_text())
assert step.get("backend") == "atspi" and step.get("ok"), step
assert step.get("host_injection") == "none-atspi", step
assert before.get("class") == after.get("class"), (before, after)
print("live-actuator-smoke ok: AT-SPI click in nested seat; host focus class unchanged")
PY
