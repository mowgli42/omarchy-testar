#!/usr/bin/env python3
"""Screenshot-fallback state source (separate from AT-SPI).

When the accessibility tree is empty, derive click targets from a labeled
region map (template match stand-in). Higher false-action rate — keep this
path opt-in and never merge blindly into AT-SPI results.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SIM = Path(__file__).resolve().parent
FIX = SIM / "fixtures" / "screenshot_map.json"


def derive_actions(mapping: dict, *, buttons_only: bool = True) -> list[dict]:
    actions: list[dict] = []
    for region in mapping.get("regions", []):
        role = region.get("role", "button")
        if buttons_only and role != "button":
            continue
        name = region.get("name")
        if not name:
            continue
        box = region["box"]  # [x, y, w, h]
        x = int(box[0] + box[2] / 2)
        y = int(box[1] + box[3] / 2)
        actions.append(
            {
                "role": role,
                "name": name,
                "action": "click",
                "x": x,
                "y": y,
                "source": "screenshot-fallback",
                "box": box,
            }
        )
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=FIX)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mapping = json.loads(args.map.read_text())
    actions = derive_actions(mapping)
    assert actions, "screenshot fallback produced no actions"
    assert any(a["role"] == "button" for a in actions)
    if args.json:
        print(json.dumps(actions, indent=2))
    else:
        print(f"screenshot-fallback: {len(actions)} actions from {args.map.name}")
        for a in actions:
            print(f"  [{a['role']}] {a['name']} @ ({a['x']},{a['y']})")


if __name__ == "__main__":
    main()
