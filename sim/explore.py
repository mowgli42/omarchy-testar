#!/usr/bin/env python3
"""Fixture explorer. Proves the report contract, not a live Hyprland seat."""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from policy import mark_visited, pick_unvisited  # noqa: E402
from reports import assert_attachments_resolve, attachments_for  # noqa: E402

OUT = ROOT / "out"
SEQ_LEN = 3
RUN_NAME = "fixture-explore"
BUTTON = {"button"}


def load_app():
    return json.loads((ROOT / "fixture_app.json").read_text())


def walk(app):
    state = app["initial"]
    steps = []
    visited: set[str] = set()
    while len(steps) < SEQ_LEN:
        widgets = app["states"][state]["widgets"]
        widget = pick_unvisited(widgets, visited, roles=BUTTON)
        if widget is None:
            break
        mark_visited(visited, widget)
        steps.append(
            {
                "seq": len(steps) + 1,
                "state_id": state,
                "action": widget["action"],
                "role": widget["role"],
                "name": widget["name"],
                "fatal": bool(widget.get("fatal")),
            }
        )
        state = widget["next"]
        if widget.get("fatal"):
            break
    return steps


def write_ctrf(steps):
    failed = any(s["fatal"] for s in steps)
    fatal = next(s for s in steps if s["fatal"])
    report = {
        "results": {
            "tool": {"name": "omarchy-testar", "version": "0.0.1"},
            "summary": {
                "tests": 1,
                "passed": 0 if failed else 1,
                "failed": 1 if failed else 0,
                "skipped": 0,
                "pending": 0,
                "other": 0,
                "start": 0,
                "stop": 1,
            },
            "tests": [
                {
                    "name": RUN_NAME,
                    "status": "failed" if failed else "passed",
                    "duration": 1,
                    "message": f"fatal action {fatal['name']} in state {fatal['state_id']}",
                    "trace": json.dumps(steps),
                    "attachments": attachments_for(OUT),
                }
            ],
        }
    }
    (OUT / "ctrf.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def write_junit(report):
    test = report["results"]["tests"][0]
    suite = ET.Element("testsuite", name="omarchy-testar", tests="1", failures="1")
    case = ET.SubElement(suite, "testcase", name=RUN_NAME, classname="sim.explore")
    fail = ET.SubElement(case, "failure", message=test["message"])
    fail.text = test["trace"]
    ET.ElementTree(suite).write(OUT / "junit.xml", encoding="unicode", xml_declaration=True)


def write_sarif(steps):
    fatal = next(s for s in steps if s["fatal"])
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "omarchy-testar", "version": "0.0.1"}},
                "results": [
                    {
                        "ruleId": "oracle/fatal-action",
                        "level": "error",
                        "message": {
                            "text": f"{RUN_NAME}: fatal action {fatal['name']} in state {fatal['state_id']}"
                        },
                    }
                ],
            }
        ],
    }
    (OUT / "findings.sarif").write_text(json.dumps(sarif, indent=2) + "\n")


def main():
    OUT.mkdir(exist_ok=True)
    steps = walk(load_app())
    (OUT / "sequence.jsonl").write_text("".join(json.dumps(s) + "\n" for s in steps))
    report = write_ctrf(steps)
    write_junit(report)
    write_sarif(steps)
    assert len(steps) == SEQ_LEN
    assert any(s["name"] == "Open" and s["action"] == "click" for s in steps)
    assert report["results"]["tests"][0]["status"] == "failed"
    assert_attachments_resolve(OUT, report)
    print(f"wrote {len(steps)} steps to {OUT}")


if __name__ == "__main__":
    main()
