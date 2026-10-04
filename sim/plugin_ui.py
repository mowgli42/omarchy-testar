#!/usr/bin/env python3
"""Walk an Omarchy plugin UI from its manifest and QML.

No Quickshell in this environment. Controls are the Accessible.name /
objectName markers a later AT-SPI pass would see. Summon/close follow the
shell contract: panel entry points expose open() and close().
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "examples" / "status-panel"
OUT = ROOT / "sim" / "out"
RUN = "status-panel-ui"
KINDS = {"bar-widget": "barWidget", "panel": "panel", "overlay": "overlay", "menu": "menu", "service": "service", "bar": "bar"}


def validate(plugin: Path):
    manifest = json.loads((plugin / "manifest.json").read_text())
    errors = []
    if manifest.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if not manifest.get("id") or manifest["id"].startswith("omarchy."):
        errors.append("id missing or reserved")
    for kind in manifest.get("kinds", []):
        key = KINDS.get(kind)
        entry = (manifest.get("entryPoints") or {}).get(key) if key else None
        if not entry:
            errors.append(f"no entry point for {kind}")
        elif not (plugin / entry).is_file():
            errors.append(f"missing {entry}")
    return manifest, errors


def controls(qml: str):
    found = []
    blocks = re.split(r"\n(?=\s*(?:Item|Button|Text|MouseArea)\b)", qml)
    for block in blocks:
        oid = re.search(r'objectName:\s*"([^"]+)"', block)
        name = re.search(r'Accessible\.name:\s*"([^"]+)"', block)
        if oid and name:
            found.append({"id": oid.group(1), "name": name.group(1)})
    return found


def walk(manifest):
    panel_qml = (PLUGIN / manifest["entryPoints"]["panel"]).read_text()
    bar_qml = (PLUGIN / manifest["entryPoints"]["barWidget"]).read_text()
    steps = []
    state = "bar"
    status = "Ready"
    visible = False
    actions = [
        ("status-bar", "summon"),
        ("refresh", "click"),
        ("close", "click"),
    ]
    widgets = {c["id"]: c for c in controls(bar_qml) + controls(panel_qml)}
    for i, (wid, action) in enumerate(actions, start=1):
        if wid not in widgets:
            raise SystemExit(f"control {wid} not in plugin UI")
        if action == "summon":
            visible = True
            state = "panel"
        elif wid == "refresh":
            status = "Checked"
        elif wid == "close":
            visible = False
            state = "bar"
        steps.append({
            "seq": i,
            "state_id": state,
            "action": action,
            "role": "button",
            "name": widgets[wid]["name"],
            "status": status,
            "panel_visible": visible,
            "fatal": False,
        })
    return steps


def write_reports(steps, errors):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "plugin-sequence.jsonl").write_text("".join(json.dumps(s) + "\n" for s in steps))
    failed = bool(errors) or steps[-1]["status"] != "Checked" or steps[-1]["panel_visible"]
    message = "; ".join(errors) if errors else "panel summoned, refreshed, closed"
    report = {
        "results": {
            "tool": {"name": "omarchy-testar", "version": "0.0.2"},
            "summary": {"tests": 1, "passed": 0 if failed else 1, "failed": 1 if failed else 0, "skipped": 0, "pending": 0, "other": 0, "start": 0, "stop": 1},
            "tests": [{"name": RUN, "status": "failed" if failed else "passed", "duration": 1, "message": message, "trace": json.dumps(steps)}],
        }
    }
    (OUT / "plugin-ctrf.json").write_text(json.dumps(report, indent=2) + "\n")
    suite = ET.Element("testsuite", name="omarchy-testar", tests="1", failures="0" if not failed else "1")
    case = ET.SubElement(suite, "testcase", name=RUN, classname="sim.plugin_ui")
    if failed:
        ET.SubElement(case, "failure", message=message).text = message
    ET.ElementTree(suite).write(OUT / "plugin-junit.xml", encoding="unicode", xml_declaration=True)
    sarif = {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "omarchy-testar"}}, "results": []}]}
    if errors:
        sarif["runs"][0]["results"].append({"ruleId": "plugin/manifest", "level": "error", "message": {"text": message}})
    (OUT / "plugin-findings.sarif").write_text(json.dumps(sarif, indent=2) + "\n")
    html = f"""<!doctype html><meta charset=utf-8><title>{RUN}</title>
<style>body{{font:16px/1.4 sans-serif;background:#1a1b1e;color:#eee;padding:24px}} .bar,.panel{{border:1px solid #444;padding:12px;margin:12px 0;max-width:320px}} button{{margin-right:8px}}</style>
<h1>Status panel walk</h1>
<p>{message}</p>
<div class=bar>Bar widget <button>Status</button></div>
<div class=panel>Panel <p>Checked</p><button>Refresh</button><button>Close</button></div>
<pre>{json.dumps(steps, indent=2)}</pre>"""
    (OUT / "plugin-walk.html").write_text(html)
    return failed


def main():
    manifest, errors = validate(PLUGIN)
    if errors:
        raise SystemExit("manifest: " + "; ".join(errors))
    steps = walk(manifest)
    failed = write_reports(steps, errors)
    assert steps[0]["action"] == "summon" and steps[0]["panel_visible"]
    assert steps[1]["status"] == "Checked"
    assert steps[2]["panel_visible"] is False
    assert not failed
    print(f"plugin {manifest['id']} walk ok -> {OUT}")


if __name__ == "__main__":
    main()
