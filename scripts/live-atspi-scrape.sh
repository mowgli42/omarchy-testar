#!/usr/bin/env bash
# Scrape a live AT-SPI tree from a real app inside the nested seat.
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

./scripts/nested-seat.sh run -- /usr/bin/python3 - <<'PY' &
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

win = Gtk.Window(title="testar-scrape")
win.set_default_size(280, 200)
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
box.set_margin_top(12)
box.set_margin_bottom(12)
box.set_margin_start(12)
box.set_margin_end(12)
for label in ("Alpha", "Beta", "Gamma"):
    box.pack_start(Gtk.Button(label=label), True, True, 0)
win.add(box)
win.connect("destroy", Gtk.main_quit)
win.show_all()
GLib.timeout_add(10000, Gtk.main_quit)
Gtk.main()
PY
GTK_PID=$!
sleep 0.8

/usr/bin/python3 sim/atspi.py --live --json | tee "$OUT/live-atspi-tree.json"
/usr/bin/python3 - <<PY
import json
from pathlib import Path
actions = json.loads(Path("$OUT/live-atspi-tree.json").read_text())
names = {a["name"] for a in actions if a.get("role") == "button"}
need = {"Alpha", "Beta", "Gamma"}
assert need <= names, f"missing {need - names}; saw {sorted(names)}"
print(f"live-atspi-scrape ok: {len(actions)} actions; nested buttons {sorted(need)}")
PY
kill "$GTK_PID" 2>/dev/null || true
wait "$GTK_PID" 2>/dev/null || true
