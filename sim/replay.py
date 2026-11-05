#!/usr/bin/env python3
"""Replay a fixture sequence.jsonl against the matching state graph.

  python3 sim/explore.py
  python3 sim/replay.py --sequence sim/out/sequence.jsonl --app sim/fixture_app.json

  python3 sim/snarksentinel_click.py
  python3 sim/replay.py --sequence sim/out/snarksentinel/sequence.jsonl \
      --app sim/fixtures/snarksentinel/app.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_sequence(path: Path) -> list[dict]:
    steps = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            steps.append(json.loads(line))
    if not steps:
        raise SystemExit(f"empty sequence: {path}")
    return steps


def replay(app: dict, recorded: list[dict]) -> list[dict]:
    """Re-execute recorded clicks.

    Coverage walks may jump to another state when the current one has no
    unvisited buttons. Prefer the recorded state_id when present so replay
    matches click-all sequences, not only linear transition paths.
    """
    state = app["initial"]
    played: list[dict] = []
    for i, rec in enumerate(recorded, start=1):
        if rec.get("state_id"):
            state = rec["state_id"]
        if state not in app["states"]:
            raise SystemExit(f"replay broke at seq {i}: unknown state {state!r}")
        widgets = app["states"][state]["widgets"]
        match = next((w for w in widgets if w["name"] == rec["name"]), None)
        if match is None:
            raise SystemExit(
                f"replay broke at seq {i}: no widget named {rec['name']!r} in state {state!r}"
            )
        step = {
            "seq": i,
            "state_id": state,
            "action": match.get("action", "click"),
            "role": match.get("role", "button"),
            "name": match["name"],
            "fatal": bool(match.get("fatal")),
        }
        played.append(step)
        if step["fatal"]:
            break
        state = match["next"]
    return played


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence", type=Path, required=True)
    parser.add_argument("--app", type=Path, required=True)
    args = parser.parse_args()

    recorded = load_sequence(args.sequence)
    app = json.loads(args.app.read_text())
    played = replay(app, recorded)

    rec_names = [s["name"] for s in recorded]
    play_names = [s["name"] for s in played]
    # Crash-injected walks stop early; compare the prefix that was replayed.
    assert play_names == rec_names[: len(play_names)], (play_names, rec_names)

    rec_failed = any(s.get("fatal") for s in recorded)
    # Fixture fatal widgets vs snarksentinel inject_crash (oracle-only at record time).
    play_failed = any(s.get("fatal") for s in played)
    if any(w.get("fatal") for st in app["states"].values() for w in st["widgets"]):
        assert rec_failed == play_failed, (rec_failed, play_failed)

    print(
        f"replay ok: {len(played)} steps from {args.sequence.name} "
        f"({'failed' if rec_failed else 'passed'} run)"
    )


if __name__ == "__main__":
    main()
