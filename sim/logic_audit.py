#!/usr/bin/env python3
"""Level 1: logic audit of UI code. No clicks.

Loads a fixture graph (stand-in for QML / AT-SPI), emits findings and an
action map, writes CTRF / JUnit / SARIF under sim/out/logic/.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SIM = Path(__file__).resolve().parent
sys.path.insert(0, str(SIM))
from readability import check_widget  # noqa: E402

FIX = SIM / "fixtures" / "logic"
OUT = SIM / "out" / "logic"
RUN = "logic-audit"
VERSION = "0.3.0"

CLOSE_NAMES = {"Close", "Close window", "Close panel", "×", "✕"}
CLOSE_OBJECT = {"close", "dismiss"}
CLOSE_ACTIONS = {"close", "hide", "quit"}


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text())


def dump_fields(app: dict) -> list[dict]:
    """Normalize widgets to the fields the audit reads."""
    rows: list[dict] = []
    for state_id, state in (app.get("states") or {}).items():
        for w in state.get("widgets") or []:
            rows.append(
                {
                    "state": state_id,
                    "role": w.get("role"),
                    "name": w.get("name"),
                    "objectName": w.get("objectName"),
                    "enabled": w.get("enabled", True),
                    "action": w.get("action"),
                    "closes": w.get("closes"),
                    "color": w.get("color"),
                    "background": w.get("background"),
                    "fontPixelSize": w.get("fontPixelSize"),
                    "fontPointSize": w.get("fontPointSize"),
                    "clip": w.get("clip"),
                    "scrollParent": w.get("scrollParent"),
                    "accessibility": app.get("accessibility", True),
                }
            )
    return rows


def is_enabled(widget: dict) -> bool:
    return widget.get("enabled", True) is not False


def has_action(widget: dict) -> bool:
    action = widget.get("action")
    return isinstance(action, str) and action.strip() != ""


def is_close_control(widget: dict) -> bool:
    name = str(widget.get("name") or "")
    oid = str(widget.get("objectName") or "")
    return name in CLOSE_NAMES or oid in CLOSE_OBJECT


def closes_window(widget: dict) -> bool:
    if widget.get("closes") is True:
        return True
    action = str(widget.get("action") or "").strip().lower()
    return action in CLOSE_ACTIONS


def iter_widgets(app: dict):
    for state_id, state in (app.get("states") or {}).items():
        for w in state.get("widgets") or []:
            yield state_id, w


def audit(app: dict) -> dict:
    findings: list[dict] = []
    action_map: list[dict] = []
    gate_ok = True

    if app.get("accessibility", True) is False:
        gate_ok = False
        findings.append(
            {
                "ruleId": "logic/a11y-disabled",
                "level": "error",
                "message": "accessibility is disabled",
            }
        )

    for state_id, w in iter_widgets(app):
        role = w.get("role")
        name = w.get("name")
        enabled = is_enabled(w)

        if role == "button" and enabled:
            if not has_action(w):
                findings.append(
                    {
                        "ruleId": "logic/button-without-action",
                        "level": "error",
                        "message": f"enabled button {name!r} has no action",
                        "name": name,
                        "state": state_id,
                    }
                )
            else:
                action_map.append(
                    {
                        "state": state_id,
                        "role": "button",
                        "name": name,
                        "objectName": w.get("objectName"),
                        "action": w.get("action"),
                        "next": w.get("next"),
                        "closes": is_close_control(w),
                        "panel_visible": w.get("panel_visible"),
                        "fatal": bool(w.get("fatal")),
                    }
                )

            missing_name = name is None or str(name).strip() == ""
            missing_role = not role
            ignored = bool(w.get("accessibleIgnored") or w.get("Accessible.ignored"))
            if missing_name or missing_role or ignored:
                gate_ok = False
                findings.append(
                    {
                        "ruleId": "logic/a11y-marker-missing",
                        "level": "error",
                        "message": f"enabled button missing accessible name/role: {w.get('objectName')!r}",
                        "name": name,
                        "state": state_id,
                    }
                )

        if is_close_control(w):
            if not enabled or not closes_window(w):
                findings.append(
                    {
                        "ruleId": "logic/close-does-not-close",
                        "level": "error",
                        "message": f"close control {name!r} does not close (enabled={enabled})",
                        "name": name,
                        "state": state_id,
                    }
                )

        if role in {"text", "statictext", "label", "button"}:
            for hit in check_widget(w):
                hit = dict(hit)
                hit["state"] = state_id
                findings.append(hit)

    errors = [f for f in findings if f.get("level", "error") == "error"]
    return {
        "findings": findings,
        "action_map": action_map,
        "gate_ok": gate_ok,
        "ok": not errors,
        "app_id": app.get("id"),
    }


def write_reports(result: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "action-map.json").write_text(json.dumps(result["action_map"], indent=2) + "\n")
    (OUT / "audit.json").write_text(json.dumps(result, indent=2) + "\n")

    failed = not result["ok"]
    errors = [f for f in result["findings"] if f.get("level", "error") == "error"]
    warnings = [f for f in result["findings"] if f.get("level") == "warning"]
    message = (
        "; ".join(f["message"] for f in errors)
        if errors
        else (
            "logic-audit ok"
            if not warnings
            else f"logic-audit ok with {len(warnings)} warning(s)"
        )
    )
    ctrf = {
        "results": {
            "tool": {"name": "omarchy-testar", "version": VERSION},
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
                    "name": RUN,
                    "status": "failed" if failed else "passed",
                    "duration": 1,
                    "message": message,
                    "trace": json.dumps(
                        {
                            "gate_ok": result["gate_ok"],
                            "findings": result["findings"],
                            "action_map": result["action_map"],
                        }
                    ),
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
    )
    case = ET.SubElement(suite, "testcase", name=RUN, classname="sim.logic_audit")
    if failed:
        ET.SubElement(case, "failure", message=message).text = message
    ET.ElementTree(suite).write(OUT / "junit.xml", encoding="unicode", xml_declaration=True)

    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "omarchy-testar", "version": VERSION}},
                "results": [
                    {
                        "ruleId": f["ruleId"],
                        "level": "warning" if f.get("level") == "warning" else "error",
                        "message": {"text": f["message"]},
                    }
                    for f in result["findings"]
                ],
            }
        ],
    }
    (OUT / "findings.sarif").write_text(json.dumps(sarif, indent=2) + "\n")


def rule_ids(result: dict) -> set[str]:
    return {f["ruleId"] for f in result["findings"]}


SELF_TESTS = [
    ("readable.json", {"rules": set(), "gate": True, "ok": True}),
    ("button-no-action.json", {"rules": {"logic/button-without-action"}, "gate": True, "ok": False}),
    ("button-disabled-no-action.json", {"rules": set(), "gate": True, "ok": True}),
    ("close-ok.json", {"rules": set(), "gate": True, "ok": True}),
    (
        "close-wrong-action.json",
        {"rules": {"logic/close-does-not-close"}, "gate": True, "ok": False},
    ),
    (
        "close-disabled.json",
        {"rules": {"logic/close-does-not-close"}, "gate": True, "ok": False},
    ),
    ("contrast-fail.json", {"rules": {"logic/text-contrast"}, "gate": True, "ok": False}),
    (
        "theme-color.json",
        {"rules": {"logic/text-color-unresolved"}, "gate": True, "ok": True},
    ),
    ("text-too-small.json", {"rules": {"logic/text-too-small"}, "gate": True, "ok": False}),
    ("text-no-size.json", {"rules": set(), "gate": True, "ok": True}),
    (
        "text-clip-no-scroll.json",
        {"rules": {"logic/text-not-scrollable"}, "gate": True, "ok": False},
    ),
    ("text-clip-scroll.json", {"rules": set(), "gate": True, "ok": True}),
    ("button-label-elide.json", {"rules": set(), "gate": True, "ok": True}),
    ("a11y-off.json", {"rules": {"logic/a11y-disabled"}, "gate": False, "ok": False}),
    (
        "a11y-missing-name.json",
        {"rules": {"logic/a11y-marker-missing"}, "gate": False, "ok": False},
    ),
]


def self_test() -> int:
    failed = 0
    for name, expect in SELF_TESTS:
        path = FIX / name
        result = audit(load_fixture(path))
        got = rule_ids(result)
        # theme-color ok True despite warning
        want_rules = expect["rules"]
        if want_rules and not want_rules.issubset(got):
            print(f"FAIL {name}: missing {want_rules - got}; got {got}")
            failed += 1
            continue
        if not want_rules and got & {
            "logic/button-without-action",
            "logic/close-does-not-close",
            "logic/text-contrast",
            "logic/text-too-small",
            "logic/text-not-scrollable",
            "logic/a11y-disabled",
            "logic/a11y-marker-missing",
        }:
            print(f"FAIL {name}: unexpected errors {got}")
            failed += 1
            continue
        if result["gate_ok"] != expect["gate"]:
            print(f"FAIL {name}: gate_ok={result['gate_ok']} want {expect['gate']}")
            failed += 1
            continue
        if result["ok"] != expect["ok"]:
            print(f"FAIL {name}: ok={result['ok']} want {expect['ok']}")
            failed += 1
            continue
        # theme warning must be present when expected
        if "logic/text-color-unresolved" in want_rules and "logic/text-color-unresolved" not in got:
            print(f"FAIL {name}: missing warning")
            failed += 1
            continue
        if "logic/text-color-unresolved" not in want_rules and "logic/text-color-unresolved" in got:
            # readable etc should not warn
            print(f"FAIL {name}: unexpected warning {got}")
            failed += 1
            continue
        print(f"ok   {name}")
    return failed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dump",
        type=Path,
        help="Load fixture and print normalized fields as JSON",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=FIX / "readable.json",
        help="Fixture to audit (default: readable.json)",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        n = self_test()
        # Also write reports for the readable fixture after tests.
        write_reports(audit(load_fixture(FIX / "readable.json")))
        raise SystemExit(n)

    if args.dump:
        app = load_fixture(args.dump)
        print(json.dumps(dump_fields(app), indent=2))
        raise SystemExit(0)

    app = load_fixture(args.fixture)
    result = audit(app)
    write_reports(result)
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "gate_ok": result["gate_ok"],
                "findings": len(result["findings"]),
                "action_map": len(result["action_map"]),
                "out": str(OUT),
            }
        )
    )
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
