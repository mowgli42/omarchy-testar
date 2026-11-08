#!/usr/bin/env python3
"""AT-SPI / fixture accessibility scrape → omarchy-testar widget actions.

Prefer the system interpreter with GI bindings:
  /usr/bin/python3 sim/atspi.py --live

Maps AT-SPI roles onto docs/standards.md vocabulary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SIM = Path(__file__).resolve().parent
FIX = SIM / "fixtures" / "atspi_tree.json"

ROLE_MAP = {
    "push button": "button",
    "button": "button",
    "toggle button": "button",
    "radio button": "button",
    "check box": "button",
    "menu item": "menu item",
    "link": "link",
    "text": "text",
    "entry": "text",
    "password text": "text",
    "dialog": "dialog",
    "alert": "dialog",
    "frame": "dialog",
}


def map_role(raw: str) -> str | None:
    key = str(raw or "").strip().lower().replace("_", " ")
    return ROLE_MAP.get(key)


def nodes_to_actions(nodes: list[dict], *, buttons_only: bool = True) -> list[dict]:
    actions: list[dict] = []
    for node in nodes:
        role = map_role(node.get("role", ""))
        if role is None:
            continue
        if buttons_only and role != "button":
            continue
        name = str(node.get("name") or "").strip()
        if not name:
            continue
        actions.append(
            {
                "role": role,
                "name": name,
                "action": "click" if role in {"button", "menu item", "link"} else "type",
                "source": node.get("source", "atspi"),
                "path": node.get("path"),
            }
        )
    return actions


def scrape_fixture(path: Path = FIX) -> list[dict]:
    data = json.loads(path.read_text())
    return nodes_to_actions(data.get("nodes", []))


def _gi_atspi():
    try:
        import gi

        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi

        Atspi.init()
        return Atspi
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "AT-SPI GI bindings unavailable in this interpreter.\n"
            "Use: /usr/bin/python3 sim/atspi.py --live\n"
            f"Import error: {exc}"
        ) from exc


def scrape_live(app_name: str | None = None) -> list[dict]:
    Atspi = _gi_atspi()
    nodes: list[dict] = []

    def walk(acc, path: str) -> None:
        try:
            role = acc.get_role_name() or ""
            name = acc.get_name() or ""
        except Exception:
            return
        if map_role(role):
            nodes.append({"role": role, "name": name, "path": path, "source": "gi-atspi"})
        try:
            count = acc.get_child_count()
        except Exception:
            return
        for i in range(count):
            try:
                child = acc.get_child_at_index(i)
            except Exception:
                continue
            if child is None:
                continue
            walk(child, f"{path}/{i}")

    desktop = Atspi.get_desktop(0)
    for i in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(i)
        if app is None:
            continue
        label = app.get_name() or f"app-{i}"
        if app_name and app_name.lower() not in label.lower():
            continue
        walk(app, label)
    return nodes_to_actions(nodes)


def find_button(name: str, app_name: str | None = None):
    """Return a live AT-SPI accessible for a named button, or None."""
    Atspi = _gi_atspi()

    def walk(acc):
        try:
            role = (acc.get_role_name() or "").lower()
            n = acc.get_name() or ""
        except Exception:
            return None
        if "button" in role and n == name:
            return acc
        try:
            for i in range(acc.get_child_count()):
                child = acc.get_child_at_index(i)
                if child is None:
                    continue
                hit = walk(child)
                if hit is not None:
                    return hit
        except Exception:
            return None
        return None

    desktop = Atspi.get_desktop(0)
    for i in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(i)
        if app is None:
            continue
        label = app.get_name() or ""
        if app_name and app_name.lower() not in label.lower():
            continue
        hit = walk(app)
        if hit is not None:
            return hit
    return None


def click_button(name: str, app_name: str | None = None) -> dict:
    acc = find_button(name, app_name=app_name)
    if acc is None:
        raise SystemExit(f"AT-SPI button not found: {name!r}")
    n_actions = acc.get_n_actions()
    if n_actions < 1:
        raise SystemExit(f"AT-SPI button {name!r} has no actions")
    ok = acc.do_action(0)
    return {
        "action": "click",
        "backend": "atspi",
        "name": name,
        "role": "button",
        "ok": bool(ok),
        "action_name": acc.get_action_name(0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=FIX)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--app", help="Filter live apps by name substring")
    parser.add_argument("--click", help="Invoke AT-SPI click on a named button")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.click:
        result = click_button(args.click, app_name=args.app)
        print(json.dumps(result, indent=2) if args.json else result)
        raise SystemExit(0 if result.get("ok") else 1)

    if args.live:
        actions = scrape_live(args.app)
    else:
        actions = scrape_fixture(args.fixture)

    if args.live and not actions:
        # Locked sessions / empty trees are a soft miss; callers assert what they need.
        if args.json:
            print("[]")
        else:
            print("atspi: 0 button actions (empty live tree)")
        raise SystemExit(0)
    assert any(a["role"] == "button" for a in actions), "expected at least one button action"
    if args.json:
        print(json.dumps(actions, indent=2))
    else:
        print(f"atspi: {len(actions)} button actions")
        for a in actions:
            print(f"  [{a['role']}] {a['name']}")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
