#!/usr/bin/env python3
"""Click-all SnarkSentinel buttons (TESTAR-style, no recorded script).

Derives role=button actions from the fixture state graph (frozen from
Panel.qml / BarWidget.qml), picks unvisited enabled buttons, screenshots
after each click, then checks crash-shaped JSONL logs.

  python3 sim/snarksentinel_click.py
  python3 sim/snarksentinel_click.py --inject-crash
  python3 sim/snarksentinel_click.py --scrape /path/to/snarksentinel/omarchy-plugin
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SIM = Path(__file__).resolve().parent
sys.path.insert(0, str(SIM))
from reports import assert_attachments_resolve, attachments_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIX = SIM / "fixtures" / "snarksentinel"
OUT = SIM / "out" / "snarksentinel"
RUN = "snarksentinel-click-all"
CRASH_RE = re.compile(r"segfault|sigsegv|aborted|core dumped|traceback", re.I)
BUTTON_BLOCK = re.compile(
    r"\bButton\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
    re.M,
)


def load_app() -> dict:
    return json.loads((FIX / "app.json").read_text())


def enabled_buttons(app: dict, state: str) -> list[dict]:
    widgets = app["states"][state]["widgets"]
    buttons = [w for w in widgets if w.get("role") == "button"]
    if any(w.get("role") != "button" for w in widgets):
        raise AssertionError(f"non-button widget in state {state}")
    return buttons


def reachable_button_names(app: dict) -> set[str]:
    """Unique button names across states the coverage walk can enter."""
    seen_states: set[str] = set()
    queue = [app["initial"]]
    names: set[str] = set()
    while queue:
        state = queue.pop(0)
        if state in seen_states:
            continue
        seen_states.add(state)
        for w in enabled_buttons(app, state):
            names.add(w["name"])
            nxt = w.get("next")
            if nxt and nxt not in seen_states:
                queue.append(nxt)
    return names


def pick_unvisited(buttons: list[dict], visited: set[str]) -> dict | None:
    for b in buttons:
        if b["name"] not in visited:
            return b
    return None


def write_screenshot(step: int, state: str, name: str) -> str:
    shots = OUT / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    rel = f"screenshots/step-{step:03d}.svg"
    path = OUT / rel
    path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360">
  <rect width="100%" height="100%" fill="#1a1b1e"/>
  <text x="24" y="48" fill="#eee" font-family="monospace" font-size="18">snarksentinel · {state}</text>
  <text x="24" y="88" fill="#8fbcbb" font-family="monospace" font-size="16">after click: {name}</text>
  <text x="24" y="128" fill="#666" font-family="monospace" font-size="12">step {step}</text>
</svg>
"""
    )
    return rel


def prepare_logs(inject_crash: bool) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    watched = OUT / "watched-events.jsonl"
    src = FIX / ("events_crash.jsonl" if inject_crash else "events_clean.jsonl")
    # Start clean; crash lines are appended only when inject_crash fires on a step.
    shutil.copyfile(FIX / "events_clean.jsonl", watched)
    if inject_crash:
        # Keep crash payload handy for the oracle injector.
        (OUT / "crash-payload.jsonl").write_text((FIX / "events_crash.jsonl").read_text())
    return watched


def crash_in_log(path: Path, after_offset: int) -> tuple[bool, str | None, int]:
    data = path.read_text()
    new = data[after_offset:]
    offset = len(data)
    for line in new.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            if CRASH_RE.search(line):
                return True, line, offset
            continue
        level = str(row.get("level", "")).lower()
        blob = " ".join(
            str(row.get(k, "")) for k in ("message", "exception", "event", "detail")
        )
        if level in {"critical", "fatal", "error"} and (
            CRASH_RE.search(blob) or level in {"critical", "fatal"}
        ):
            if level in {"critical", "fatal"} or CRASH_RE.search(blob):
                return True, line, offset
        if CRASH_RE.search(blob):
            return True, line, offset
    return False, None, offset


def maybe_inject(watched: Path, widget: dict, inject_crash: bool) -> None:
    if not inject_crash or not widget.get("inject_crash"):
        return
    payload = (OUT / "crash-payload.jsonl").read_text().strip().splitlines()[-1]
    with watched.open("a") as fh:
        fh.write(payload + "\n")


def click_all(app: dict, watched: Path, inject_crash: bool) -> list[dict]:
    state = app["initial"]
    visited: set[str] = set()
    steps: list[dict] = []
    log_offset = 0
    # Coverage across the whole reachable graph: a name clicked in one state
    # counts globally so we do not re-click shared tabs forever.
    target = reachable_button_names(app)

    while True:
        buttons = enabled_buttons(app, state)
        choice = pick_unvisited(buttons, visited)
        if choice is None:
            # Local dead-end: jump to any reachable state that still has unvisited buttons.
            progressed = False
            for sid, sdef in app["states"].items():
                leftover = pick_unvisited(enabled_buttons(app, sid), visited)
                if leftover is not None:
                    state = sid
                    progressed = True
                    break
            if not progressed:
                break
            continue

        visited.add(choice["name"])
        maybe_inject(watched, choice, inject_crash)
        crashed, evidence, log_offset = crash_in_log(watched, log_offset)
        seq = len(steps) + 1
        shot = write_screenshot(seq, state, choice["name"])
        step = {
            "seq": seq,
            "state_id": state,
            "action": choice.get("action", "click"),
            "role": "button",
            "name": choice["name"],
            "screenshot": shot,
            "fatal": crashed,
            "oracle": "crash-log" if crashed else "ok",
            "evidence": evidence,
        }
        steps.append(step)
        if crashed:
            break
        state = choice["next"]
        if visited >= target:
            # Still finish if current state has nothing new; loop condition handles it.
            if pick_unvisited(enabled_buttons(app, state), visited) is None:
                # Check remaining states once more next iteration.
                pass
    return steps


def write_reports(steps: list[dict], failed: bool, message: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sequence.jsonl").write_text("".join(json.dumps(s) + "\n" for s in steps))
    attachments = attachments_for(OUT)
    report = {
        "results": {
            "tool": {"name": "omarchy-testar", "version": "0.1.0"},
            "summary": {
                "tests": 1,
                "passed": 0 if failed else 1,
                "failed": 1 if failed else 0,
                "skipped": 0,
                "pending": 0,
                "other": 0,
                "start": 0,
                "stop": len(steps),
            },
            "tests": [
                {
                    "name": RUN,
                    "status": "failed" if failed else "passed",
                    "duration": len(steps),
                    "message": message,
                    "trace": json.dumps(steps),
                    "attachments": attachments,
                }
            ],
        }
    }
    (OUT / "ctrf.json").write_text(json.dumps(report, indent=2) + "\n")
    suite = ET.Element(
        "testsuite",
        name="omarchy-testar",
        tests="1",
        failures="1" if failed else "0",
    )
    case = ET.SubElement(suite, "testcase", name=RUN, classname="sim.snarksentinel_click")
    if failed:
        ET.SubElement(case, "failure", message=message).text = message
    ET.ElementTree(suite).write(OUT / "junit.xml", encoding="unicode", xml_declaration=True)
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "omarchy-testar", "version": "0.1.0"}},
                "results": [],
            }
        ],
    }
    if failed:
        sarif["runs"][0]["results"].append(
            {
                "ruleId": "oracle/crash-log",
                "level": "error",
                "message": {"text": message},
            }
        )
    (OUT / "findings.sarif").write_text(json.dumps(sarif, indent=2) + "\n")
    html = f"""<!doctype html><meta charset=utf-8><title>{RUN}</title>
<style>body{{font:15px/1.45 ui-monospace,monospace;background:#12131a;color:#e8e6e3;padding:24px}}
a{{color:#8fbcbb}} .ok{{color:#a3be8c}} .bad{{color:#bf616a}} li{{margin:6px 0}}</style>
<h1>SnarkSentinel click-all</h1>
<p class="{'bad' if failed else 'ok'}">{message}</p>
<ol>
{''.join(f"<li>#{s['seq']} <b>{s['name']}</b> @ {s['state_id']} → <a href='{s['screenshot']}'>{s['screenshot']}</a> [{s['oracle']}]</li>" for s in steps)}
</ol>
<pre>{json.dumps(steps, indent=2)}</pre>
"""
    (OUT / "walk.html").write_text(html)
    return report


def _text_labels(expr: str) -> list[str]:
    """Pull string literals from a QML `text:` expression only."""
    expr = expr.strip()
    if expr.startswith('"'):
        m = re.match(r'"([^"]*)"', expr)
        return [m.group(1)] if m else []
    # cond ? "A" : "B"
    m = re.search(r'\?\s*"([^"]+)"\s*:\s*"([^"]+)"', expr)
    if m:
        return [m.group(1), m.group(2)]
    return re.findall(r'"([^"]+)"', expr)


def scrape_qml(plugin: Path) -> list[dict]:
    """Extract Button text / Accessible.name from a live plugin directory."""
    found: list[dict] = []
    seen: set[str] = set()

    def add(name: str, source: str) -> None:
        if name and name not in seen:
            seen.add(name)
            found.append({"role": "button", "name": name, "source": source})

    for qml in sorted(plugin.glob("*.qml")):
        text = qml.read_text()
        for block in BUTTON_BLOCK.findall(text):
            acc = re.search(r'Accessible\.name:\s*"([^"]+)"', block)
            if acc:
                add(acc.group(1), qml.name)
                continue
            text_line = re.search(r"(?m)^\s*text:\s*(.+?)\s*$", block)
            if not text_line:
                continue
            for lit in _text_labels(text_line.group(1)):
                add(lit, qml.name)
        for m in re.finditer(
            r"Accessible\.role:\s*Accessible\.Button.*?Accessible\.name:\s*\"([^\"]+)\"",
            text,
            re.S,
        ):
            add(m.group(1), qml.name)
        for m in re.finditer(
            r"Accessible\.name:\s*\"([^\"]+)\".*?Accessible\.role:\s*Accessible\.Button",
            text,
            re.S,
        ):
            add(m.group(1), qml.name)
    out = OUT / "scraped-buttons.json"
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(found, indent=2) + "\n")
    return found


def validate(steps: list[dict], app: dict, failed: bool, expect_fail: bool) -> None:
    assert steps, "no steps"
    assert all(s["role"] == "button" for s in steps)
    assert all((OUT / s["screenshot"]).is_file() for s in steps)
    names = [s["name"] for s in steps]
    assert len(names) == len(set(names)), f"duplicate clicks: {names}"
    if expect_fail:
        assert failed and steps[-1]["fatal"]
        sarif = json.loads((OUT / "findings.sarif").read_text())
        assert any(r["ruleId"] == "oracle/crash-log" for r in sarif["runs"][0]["results"])
    else:
        assert not failed
        target = reachable_button_names(app)
        # Apply is only required when we do not stop early on crash.
        assert set(names) == target, f"missing {target - set(names)}; extra {set(names) - target}"
    for path in ("ctrf.json", "junit.xml", "findings.sarif", "sequence.jsonl"):
        assert (OUT / path).is_file()
    assert_attachments_resolve(OUT, json.loads((OUT / "ctrf.json").read_text()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inject-crash",
        action="store_true",
        help="Append a fatal log line when the Apply button is clicked",
    )
    parser.add_argument(
        "--scrape",
        type=Path,
        help="Also scrape Button texts from a live omarchy-plugin directory",
    )
    args = parser.parse_args()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    if args.scrape:
        scraped = scrape_qml(args.scrape)
        print(f"scraped {len(scraped)} button labels from {args.scrape} -> {OUT / 'scraped-buttons.json'}")

    app = load_app()
    watched = prepare_logs(args.inject_crash)
    steps = click_all(app, watched, args.inject_crash)
    failed = any(s["fatal"] for s in steps)
    if failed:
        fatal = next(s for s in steps if s["fatal"])
        message = f"crash-log after click {fatal['name']}: {fatal.get('evidence')}"
    else:
        message = f"clicked {len(steps)} buttons; no crash-log evidence"
    write_reports(steps, failed, message)
    validate(steps, app, failed, expect_fail=args.inject_crash)
    print(f"{RUN}: {'FAILED' if failed else 'passed'} ({len(steps)} clicks) -> {OUT}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
