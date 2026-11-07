#!/usr/bin/env python3
"""AT-SPI / fixture accessibility scrape → omarchy-testar widget actions.

Maps AT-SPI roles onto the shared vocabulary in docs/standards.md:
button, text, dialog, menu item, link.

Live scrape uses pyatspi when installed (`pacman -S python-atspi`).
CI and offline runs use sim/fixtures/atspi_tree.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SIM = Path(__file__).resolve().parent
FIX = SIM / "fixtures" / "atspi_tree.json"

# AT-SPI role name (lower) → explorer role
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


def scrape_live(app_name: str | None = None) -> list[dict]:
    try:
        import pyatspi  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "pyatspi not installed. On Omarchy: pacman -S python-atspi\n"
            "Or use --fixture (default) for the offline tree."
        ) from exc

    nodes: list[dict] = []

    def walk(acc, path: str) -> None:
        try:
            role = acc.getRoleName()
            name = acc.name or ""
        except Exception:
            return
        mapped = map_role(role)
        if mapped:
            nodes.append(
                {
                    "role": role,
                    "name": name,
                    "path": path,
                    "source": "pyatspi",
                }
            )
        try:
            count = acc.childCount
        except Exception:
            return
        for i in range(count):
            try:
                child = acc.getChildAtIndex(i)
            except Exception:
                continue
            if child is None:
                continue
            walk(child, f"{path}/{i}")

    desktop = pyatspi.Registry.getDesktop(0)
    for i in range(desktop.childCount):
        app = desktop.getChildAtIndex(i)
        if app is None:
            continue
        label = app.name or ""
        if app_name and app_name.lower() not in label.lower():
            continue
        walk(app, label or f"app-{i}")
    return nodes_to_actions(nodes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=FIX, help="Fixture AT-SPI tree JSON")
    parser.add_argument("--live", action="store_true", help="Scrape via pyatspi")
    parser.add_argument("--app", help="Filter live apps by name substring")
    parser.add_argument("--json", action="store_true", help="Print actions as JSON")
    args = parser.parse_args()

    if args.live:
        actions = scrape_live(args.app)
    else:
        actions = scrape_fixture(args.fixture)

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
