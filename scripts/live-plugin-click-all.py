#!/usr/bin/env python3
"""Live AT-SPI click-all for an Omarchy plugin panel.

  # after unlock + plugin enable + omarchy-restart-shell
  OMARCHY_TESTAR_ALLOW_HOST_SEAT=1 /usr/bin/python3 scripts/live-plugin-click-all.py example.status-panel
  OMARCHY_TESTAR_ALLOW_HOST_SEAT=1 /usr/bin/python3 scripts/live-plugin-click-all.py io.github.mowgli42.snarksentinel

Uses AT-SPI do_action only (no xdotool). Screenshots via grim when available.
Fails the run on crash-shaped lines in SnarkSentinel logs or journalctl.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "sim"
sys.path.insert(0, str(SIM))

from atspi import click_button, scrape_live  # noqa: E402
from oracle import CRASH_RE, scan_log_text, write_reports  # noqa: E402

PLUGINS = {
    "example.status-panel": {
        "out": SIM / "out" / "live-status-panel",
        "required": ["Status", "Refresh", "Close"],
        "optional": False,
        "logs": [],
    },
    "io.github.mowgli42.snarksentinel": {
        "out": SIM / "out" / "live-snarksentinel",
        "required": [
            "SnarkSentinel",
            "Posture",
            "Apps",
            "Scan",
            "Fix prompt",
            "Refresh list",
            "Set net on",
            "Set net off",
            "Regenerate",
            "Copy forensic",
            "Close",
            "Copy",
            "Accept these results",
        ],
        "optional": True,  # skip names not currently in the tree (page / dynamic)
        "logs": [
            Path.home() / ".local/share/snarksentinel/logs",
        ],
    },
}


def sh(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def shell_ping() -> bool:
    return sh("omarchy-shell", "shell", "ping", check=False).returncode == 0


def shell_locked() -> bool:
    raw = sh("omarchy-shell", "lock", "status", check=False).stdout.strip()
    try:
        return bool(json.loads(raw).get("locked"))
    except json.JSONDecodeError:
        return False


def summon(plugin: str) -> None:
    sh("omarchy-shell", "shell", "summon", plugin)


def screenshot(out: Path, seq: int) -> str:
    shots = out / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    rel = f"screenshots/step-{seq:03d}.png"
    path = out / rel
    if sh("bash", "-lc", f"command -v grim >/dev/null && grim {path}", check=False).returncode != 0:
        # 1x1 PNG placeholder
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f"
            b"\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
    return rel


def scan_logs(dirs: list[Path]) -> str | None:
    for d in dirs:
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*")):
            if not path.is_file():
                continue
            hit = scan_log_text(path.read_text(errors="replace"))
            if hit:
                return hit
    try:
        journal = sh(
            "journalctl", "--user", "-n", "100", "--no-pager", check=False
        ).stdout
    except FileNotFoundError:
        journal = ""
    for line in journal.splitlines():
        if CRASH_RE.search(line):
            return line.strip()
    return None


def main() -> None:
    plugin = sys.argv[1] if len(sys.argv) > 1 else "example.status-panel"
    if plugin in {"snarksentinel"}:
        plugin = "io.github.mowgli42.snarksentinel"
    if plugin not in PLUGINS:
        raise SystemExit(
            "usage: live-plugin-click-all.py example.status-panel|io.github.mowgli42.snarksentinel"
        )
    cfg = PLUGINS[plugin]
    out: Path = cfg["out"]
    if out.exists():
        import shutil

        shutil.rmtree(out)
    out.mkdir(parents=True)

    os.environ.setdefault("WAYLAND_DISPLAY", os.environ.get("OMARCHY_TESTAR_HOST_WAYLAND", "wayland-1"))
    os.environ.setdefault("OMARCHY_PATH", "/usr/share/omarchy")
    # AT-SPI never injects into the seat; allow host when exploring the live shell.
    os.environ.setdefault("OMARCHY_TESTAR_ALLOW_HOST_SEAT", "1")
    os.environ.setdefault("OMARCHY_TESTAR_NESTED", "1")

    if not shell_ping():
        print("omarchy-shell is not running", file=sys.stderr)
        raise SystemExit(1)
    if shell_locked():
        print("session is locked; unlock before live plugin click-all", file=sys.stderr)
        raise SystemExit(1)

    summon(plugin)
    import time

    time.sleep(0.7)

    steps: list[dict] = []
    failed = False
    evidence = None
    for name in cfg["required"]:
        tree = {a["name"] for a in scrape_live("quickshell")}
        if name not in tree:
            if cfg["optional"]:
                continue
            raise SystemExit(f"AT-SPI missing required button {name!r}; saw {sorted(tree)}")
        result = click_button(name, app_name="quickshell")
        seq = len(steps) + 1
        rel = screenshot(out, seq)
        hit = scan_logs(cfg["logs"])
        fatal = bool(hit)
        step = {
            "seq": seq,
            "action": "click",
            "role": "button",
            "name": name,
            "screenshot": rel,
            "fatal": fatal,
            "oracle": "crash-log" if fatal else "ok",
            "evidence": hit,
            "actuator": result,
        }
        steps.append(step)
        if fatal:
            failed = True
            evidence = hit
            break

    (out / "sequence.jsonl").write_text("".join(json.dumps(s) + "\n" for s in steps))
    oracle = {
        "ok": not failed,
        "findings": (
            [{"ruleId": "oracle/crash-log", "message": evidence}] if failed else []
        ),
        "steps": steps,
        "plugin": plugin,
    }
    # Reuse oracle report writers into this out dir by temporarily pointing.
    from oracle import OUT as ORACLE_OUT
    import oracle as oracle_mod

    prev = oracle_mod.OUT
    oracle_mod.OUT = out
    try:
        write_reports(oracle)
    finally:
        oracle_mod.OUT = prev
    (out / "summary.json").write_text(json.dumps(oracle, indent=2) + "\n")
    print(json.dumps({"plugin": plugin, "steps": len(steps), "failed": failed}, indent=2))
    if plugin == "example.status-panel" and {s["name"] for s in steps} < set(cfg["required"]):
        raise SystemExit("status-panel click-all did not cover Status/Refresh/Close")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
