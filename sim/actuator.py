#!/usr/bin/env python3
"""Input actuator scoped to the nested seat.

Backends:
  atspi   — invoke the button's AT-SPI action (no host uinput; preferred until
            ydotoold has /dev/uinput access)
  ydotool — absolute pointer click (requires ydotoold + uinput permissions)

Refuses the host seat unless OMARCHY_TESTAR_ALLOW_HOST_SEAT=1.
Never calls xdotool.

  # dry-run
  python3 sim/actuator.py --dry-run --name Probe

  # live AT-SPI click inside nested seat
  source seat/nested/runtime/env
  /usr/bin/python3 sim/actuator.py --live --backend atspi --name Probe
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SIM = Path(__file__).resolve().parent
OUT = SIM / "out" / "actuator"
sys.path.insert(0, str(SIM))


def nested_ok() -> bool:
    return os.environ.get("OMARCHY_TESTAR_NESTED") == "1"


def allow_host() -> bool:
    return os.environ.get("OMARCHY_TESTAR_ALLOW_HOST_SEAT") == "1"


def require_nested() -> None:
    if nested_ok() or allow_host():
        return
    raise SystemExit(
        "actuator: refusing host seat. Start nested seat:\n"
        "  ./scripts/nested-seat.sh start && source seat/nested/runtime/env\n"
        "See docs/nested-seat.md."
    )


def host_signature() -> str:
    return os.environ.get("OMARCHY_TESTAR_HOST_HYPR") or ""


def nested_signature() -> str:
    return os.environ.get("HYPRLAND_INSTANCE_SIGNATURE") or ""


def hypr_active(instance: str) -> dict:
    if not instance:
        return {}
    try:
        raw = subprocess.check_output(
            ["hyprctl", "-i", instance, "activewindow", "-j"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return {}


def ydotool_available() -> bool:
    return shutil.which("ydotool") is not None


def click_ydotool(x: int, y: int) -> dict:
    require_nested()
    if not ydotool_available():
        raise SystemExit("ydotool not on PATH (pacman -S ydotool; start ydotoold)")
    subprocess.run(
        ["ydotool", "mousemove", "--absolute", "-x", str(x), "-y", str(y)],
        check=True,
    )
    subprocess.run(["ydotool", "click", "0xC0"], check=True)
    return {"action": "click", "x": x, "y": y, "backend": "ydotool"}


def click_atspi(name: str, app: str | None = None) -> dict:
    require_nested()
    from atspi import click_button

    return click_button(name, app_name=app)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--backend",
        choices=("atspi", "ydotool"),
        default="atspi",
        help="atspi (default) or ydotool",
    )
    parser.add_argument("--name", default="Probe", help="AT-SPI button name")
    parser.add_argument("--app", help="Optional AT-SPI application name filter")
    parser.add_argument("--x", type=int, default=10)
    parser.add_argument("--y", type=int, default=10)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    if args.dry_run and not args.live:
        os.environ.setdefault("OMARCHY_TESTAR_NESTED", "1")
        step = {
            "action": "click",
            "backend": "dry-run",
            "name": args.name,
            "role": "button",
            "x": args.x,
            "y": args.y,
        }
        (OUT / "last-click.json").write_text(json.dumps(step, indent=2) + "\n")
        print(json.dumps(step, indent=2))
        return

    require_nested()
    host_before = hypr_active(host_signature())
    nest_before = hypr_active(nested_signature())

    if args.backend == "ydotool":
        step = click_ydotool(args.x, args.y)
        step["name"] = args.name
        step["role"] = "button"
    else:
        # Prefer system Python GI stack for AT-SPI.
        if "gi" not in sys.modules:
            try:
                import gi  # noqa: F401
            except ImportError:
                raise SystemExit(
                    "actuator atspi backend needs GI. Re-run with:\n"
                    "  /usr/bin/python3 sim/actuator.py --live --backend atspi --name Probe"
                )
        step = click_atspi(args.name, app=args.app)

    host_after = hypr_active(host_signature())
    nest_after = hypr_active(nested_signature())
    step["host_focus_before"] = {
        "class": host_before.get("class"),
        "title": host_before.get("title"),
    }
    step["host_focus_after"] = {
        "class": host_after.get("class"),
        "title": host_after.get("title"),
    }
    step["nested_focus_before"] = {
        "class": nest_before.get("class"),
        "title": nest_before.get("title"),
    }
    step["nested_focus_after"] = {
        "class": nest_after.get("class"),
        "title": nest_after.get("title"),
    }
    # Host should still be focusing the nested aquamarine window (or unchanged).
    step["host_injection"] = "none-atspi" if args.backend == "atspi" else "ydotool-uinput"
    (OUT / "last-click.json").write_text(json.dumps(step, indent=2) + "\n")
    print(json.dumps(step, indent=2))
    if args.backend == "atspi" and not step.get("ok", True):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
