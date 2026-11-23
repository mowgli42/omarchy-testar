#!/usr/bin/env python3
"""Level 2: click buttons the logic audit associated with an action.

Skips when the accessibility gate failed. Fixture transitions only — no
host-seat input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SIM = Path(__file__).resolve().parent
sys.path.insert(0, str(SIM))
from atspi import nodes_to_actions  # noqa: E402
from logic_audit import FIX, audit, load_fixture  # noqa: E402
from policy import mark_visited, pick_unvisited  # noqa: E402

OUT = SIM / "out" / "exercise"
ACTUATOR_OUT = SIM / "out" / "actuator"
RUN = "gui-exercise"
VERSION = "0.3.0"
CRASH_RE = re.compile(r"segfault|sigsegv|aborted|core dumped|traceback", re.I)
HIDDEN = {"hidden", "closed", "bar"}


def app_from_atspi_nodes(nodes: list[dict]) -> dict:
    """Build a one-state fixture from AT-SPI nodes for the logic audit + exercise."""
    actions = nodes_to_actions(nodes, buttons_only=False)
    widgets: list[dict] = []
    for a in actions:
        w: dict = {
            "role": a["role"],
            "name": a["name"],
            "enabled": True,
        }
        if a["role"] == "button":
            w["action"] = "click"
            w["objectName"] = a["name"].lower().replace(" ", "-")
            if a["name"] in {"Close", "Close window", "Close panel", "×", "✕"}:
                w["action"] = "close"
                w["closes"] = True
                w["next"] = "hidden"
                w["panel_visible"] = False
            else:
                w["next"] = "panel"
        widgets.append(w)
    empty = not any(w.get("role") == "button" for w in widgets)
    return {
        "id": "atspi-live",
        "accessibility": not empty,
        "initial": "panel",
        "states": {
            "panel": {"widgets": widgets},
            "hidden": {"widgets": []},
        },
    }


def clear_actuator_log() -> None:
    ACTUATOR_OUT.mkdir(parents=True, exist_ok=True)
    path = ACTUATOR_OUT / "last-click.json"
    if path.exists():
        path.unlink()
    (ACTUATOR_OUT / "events.jsonl").write_text("")


def record_actuator_dry_run(name: str) -> None:
    ACTUATOR_OUT.mkdir(parents=True, exist_ok=True)
    step = {
        "action": "click",
        "backend": "dry-run",
        "name": name,
        "role": "button",
        "host_injection": "none",
    }
    (ACTUATOR_OUT / "last-click.json").write_text(json.dumps(step, indent=2) + "\n")
    with (ACTUATOR_OUT / "events.jsonl").open("a") as fh:
        fh.write(json.dumps(step) + "\n")


def panel_still_open(entry: dict, next_state: str) -> bool:
    if "panel_visible" in entry and entry["panel_visible"] is not None:
        return bool(entry["panel_visible"])
    return next_state not in HIDDEN


def walk(
    app: dict,
    result: dict,
    *,
    inject_crash: bool = False,
    actuator_dry_run: bool = False,
) -> dict:
    if actuator_dry_run:
        clear_actuator_log()
    if not result["gate_ok"]:
        return {
            "status": "skipped",
            "steps": [],
            "findings": [
                {
                    "ruleId": "logic/a11y-disabled"
                    if any(f["ruleId"] == "logic/a11y-disabled" for f in result["findings"])
                    else "logic/a11y-marker-missing",
                    "level": "error",
                    "message": "accessibility gate failed; no clicks",
                }
            ],
            "message": "skipped: accessibility gate failed",
        }

    # Prefer actions reachable from the initial state, then any remaining map entries.
    by_state: dict[str, list[dict]] = {}
    for entry in result["action_map"]:
        by_state.setdefault(entry["state"], []).append(entry)

    steps: list[dict] = []
    findings: list[dict] = []
    visited: set[str] = set()
    state = app.get("initial") or next(iter(app.get("states") or {"panel"}))
    crash_seen = False

    while True:
        candidates = list(by_state.get(state) or [])
        # Also allow clicking map entries whose state matches current, by name uniqueness.
        pick = pick_unvisited(candidates, visited, roles={"button"})
        if pick is None:
            # Try any unvisited associated name still listed for this state only.
            break
        mark_visited(visited, pick)
        next_state = pick.get("next") or state
        step = {
            "seq": len(steps) + 1,
            "state_id": state,
            "action": pick.get("action") or "click",
            "role": "button",
            "name": pick["name"],
            "fatal": bool(pick.get("fatal")) or (inject_crash and pick["name"] == "Boom"),
            "next": next_state,
        }
        if actuator_dry_run:
            record_actuator_dry_run(str(pick["name"]))
        if pick.get("closes"):
            open_after = panel_still_open(pick, next_state)
            step["panel_visible"] = open_after
            if open_after:
                findings.append(
                    {
                        "ruleId": "exercise/close-still-open",
                        "level": "error",
                        "message": f"close control {pick['name']!r} left the panel open",
                        "name": pick["name"],
                    }
                )
        if step["fatal"] or inject_crash:
            # Inject once when asked, on the first click if no Boom button.
            if inject_crash and not crash_seen:
                crash_seen = True
                findings.append(
                    {
                        "ruleId": "oracle/crash-log",
                        "level": "error",
                        "message": '{"level":"fatal","message":"segfault injected"}',
                    }
                )
                step["fatal"] = True
            elif step["fatal"]:
                findings.append(
                    {
                        "ruleId": "oracle/crash-log",
                        "level": "error",
                        "message": f"fatal action {pick['name']!r}",
                    }
                )
        steps.append(step)
        state = next_state
        if step.get("fatal"):
            break
        # Coverage: stop when every associated name has been clicked once.
        all_names = {e["name"] for e in result["action_map"] if e.get("name")}
        if all_names <= visited:
            break
        # If next state has no unvisited local candidates but other names remain,
        # jump to a state that still has one (fixture coverage walk).
        if pick_unvisited(by_state.get(state) or [], visited, roles={"button"}) is None:
            moved = False
            for sid, widgets in by_state.items():
                if pick_unvisited(widgets, visited, roles={"button"}) is not None:
                    state = sid
                    moved = True
                    break
            if not moved:
                break

    failed = bool(findings)
    return {
        "status": "failed" if failed else "passed",
        "steps": steps,
        "findings": findings,
        "message": (
            "; ".join(f["message"] for f in findings) if findings else "gui-exercise ok"
        ),
    }


def write_reports(run: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    seq_path = OUT / "sequence.jsonl"
    seq_path.write_text("".join(json.dumps(s) + "\n" for s in run["steps"]))

    status = run["status"]
    failed = status == "failed"
    skipped = status == "skipped"
    ctrf = {
        "results": {
            "tool": {"name": "omarchy-testar", "version": VERSION},
            "summary": {
                "tests": 1,
                "passed": 1 if status == "passed" else 0,
                "failed": 1 if failed else 0,
                "skipped": 1 if skipped else 0,
                "pending": 0,
                "other": 0,
                "start": 0,
                "stop": 1,
            },
            "tests": [
                {
                    "name": RUN,
                    "status": status,
                    "duration": 1,
                    "message": run["message"],
                    "trace": json.dumps(run),
                    "attachments": [{"name": "sequence.jsonl", "path": "sequence.jsonl"}],
                }
            ],
        }
    }
    (OUT / "ctrf.json").write_text(json.dumps(ctrf, indent=2) + "\n")

    suite = ET.Element(
        "testsuite",
        name="omarchy-testar",
        tests="1",
        failures="0" if not failed else "1",
        skipped="1" if skipped else "0",
    )
    case = ET.SubElement(suite, "testcase", name=RUN, classname="sim.exercise")
    if failed:
        ET.SubElement(case, "failure", message=run["message"]).text = run["message"]
    if skipped:
        ET.SubElement(case, "skipped", message=run["message"])
    ET.ElementTree(suite).write(OUT / "junit.xml", encoding="unicode", xml_declaration=True)

    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "omarchy-testar", "version": VERSION}},
                "results": [
                    {
                        "ruleId": f["ruleId"],
                        "level": "error",
                        "message": {"text": f["message"]},
                    }
                    for f in run["findings"]
                ],
            }
        ],
    }
    (OUT / "findings.sarif").write_text(json.dumps(sarif, indent=2) + "\n")


def self_test() -> int:
    cases = [
        ("a11y-off.json", {"status": "skipped", "clicks": 0, "rules": set()}),
        ("exercise-two.json", {"status": "passed", "clicks": 2, "names": {"Alpha", "Beta"}}),
        ("exercise-mixed.json", {"status": "passed", "clicks": 1, "names": {"Live"}, "absent": {"Dead"}}),
        ("exercise-close-stay.json", {"status": "failed", "rules": {"exercise/close-still-open"}}),
        ("exercise-close-hide.json", {"status": "passed", "rules": set()}),
        ("exercise-crash.json", {"status": "failed", "rules": {"oracle/crash-log"}}),
        ("readable.json", {"status": "passed", "names": {"Refresh", "Close"}}),
    ]
    failed = 0
    for name, expect in cases:
        app = load_fixture(FIX / name)
        audited = audit(app)
        run = walk(app, audited, inject_crash=False)
        if run["status"] != expect["status"]:
            print(f"FAIL {name}: status {run['status']} want {expect['status']} ({run['message']})")
            failed += 1
            continue
        names = {s["name"] for s in run["steps"]}
        if "clicks" in expect and len(run["steps"]) != expect["clicks"]:
            print(f"FAIL {name}: clicks {len(run['steps'])} want {expect['clicks']}")
            failed += 1
            continue
        if "names" in expect and names != expect["names"]:
            print(f"FAIL {name}: names {names} want {expect['names']}")
            failed += 1
            continue
        if "absent" in expect and names & expect["absent"]:
            print(f"FAIL {name}: clicked absent {names & expect['absent']}")
            failed += 1
            continue
        rules = {f["ruleId"] for f in run["findings"]}
        if "rules" in expect:
            if expect["rules"] and not expect["rules"].issubset(rules):
                print(f"FAIL {name}: missing {expect['rules'] - rules}; got {rules}")
                failed += 1
                continue
            if not expect["rules"] and rules & {"exercise/close-still-open", "oracle/crash-log"}:
                print(f"FAIL {name}: unexpected {rules}")
                failed += 1
                continue
        print(f"ok   {name}")

    # inject-crash path
    app = load_fixture(FIX / "exercise-two.json")
    run = walk(app, audit(app), inject_crash=True)
    rules = {f["ruleId"] for f in run["findings"]}
    if run["status"] != "failed" or "oracle/crash-log" not in rules:
        print(f"FAIL inject-crash: {run}")
        failed += 1
    else:
        print("ok   inject-crash")
    return failed


def live_gate_smoke() -> int:
    """Empty AT-SPI → skip with no actuator events; populated tree → dry-run clicks."""
    empty = json.loads((SIM / "fixtures" / "atspi_empty.json").read_text())
    app = app_from_atspi_nodes(empty.get("nodes") or [])
    audited = audit(app)
    clear_actuator_log()
    run = walk(app, audited, actuator_dry_run=True)
    events = (ACTUATOR_OUT / "events.jsonl").read_text().strip()
    if run["status"] != "skipped" or events:
        print(f"FAIL empty-tree: status={run['status']} events={events!r}")
        return 1
    if (ACTUATOR_OUT / "last-click.json").exists():
        print("FAIL empty-tree: last-click.json should not exist")
        return 1
    print("ok   empty-tree skip (no actuator events)")

    full = json.loads((SIM / "fixtures" / "atspi_tree.json").read_text())
    app = app_from_atspi_nodes(full.get("nodes") or [])
    audited = audit(app)
    run = walk(app, audited, actuator_dry_run=True)
    names = {s["name"] for s in run["steps"]}
    if run["status"] != "passed":
        print(f"FAIL gated-tree: {run}")
        return 1
    if "Close" not in names or "Refresh" not in names:
        print(f"FAIL gated-tree names: {names}")
        return 1
    events_lines = [
        json.loads(line)
        for line in (ACTUATOR_OUT / "events.jsonl").read_text().splitlines()
        if line.strip()
    ]
    if not events_lines or any(e.get("host_injection") not in {None, "none"} for e in events_lines):
        print(f"FAIL gated-tree actuator log: {events_lines}")
        return 1
    close_step = next(s for s in run["steps"] if s["name"] == "Close")
    if close_step.get("panel_visible"):
        print("FAIL gated-tree: Close left panel open")
        return 1
    print("ok   gated-tree dry-run clicks (host injection none)")
    write_reports(run)
    from logic_audit import write_reports as write_logic  # noqa: E402

    write_logic(audited)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=FIX / "readable.json")
    parser.add_argument("--inject-crash", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--live-gate-smoke",
        action="store_true",
        help="Empty vs populated AT-SPI fixtures; actuator dry-run only (no host seat)",
    )
    parser.add_argument("--atspi-fixture", type=Path, help="Build app from AT-SPI JSON dump")
    parser.add_argument(
        "--actuator-dry-run",
        action="store_true",
        help="Record dry-run actuator events (never injects into the host seat)",
    )
    args = parser.parse_args()

    if args.self_test:
        n = self_test()
        # Write a clean exercise report for readable after tests.
        app = load_fixture(FIX / "readable.json")
        write_reports(walk(app, audit(app)))
        raise SystemExit(n)

    if args.live_gate_smoke:
        raise SystemExit(live_gate_smoke())

    if args.atspi_fixture:
        nodes = json.loads(args.atspi_fixture.read_text()).get("nodes") or []
        app = app_from_atspi_nodes(nodes)
    else:
        app = load_fixture(args.fixture)
    audited = audit(app)
    # Always refresh logic reports beside exercise so CI can upload both.
    from logic_audit import write_reports as write_logic  # noqa: E402

    write_logic(audited)
    run = walk(
        app,
        audited,
        inject_crash=args.inject_crash,
        actuator_dry_run=args.actuator_dry_run,
    )
    write_reports(run)
    print(
        json.dumps(
            {
                "status": run["status"],
                "steps": len(run["steps"]),
                "findings": len(run["findings"]),
                "out": str(OUT),
                "logic_out": str(SIM / "out" / "logic"),
            }
        )
    )
    if run["status"] == "failed":
        raise SystemExit(1)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
