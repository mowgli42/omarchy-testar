#!/usr/bin/env python3
"""Window / journal / JSONL crash oracles for nested-seat runs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

SIM = Path(__file__).resolve().parent
OUT = SIM / "out" / "oracle"
CRASH_RE = re.compile(r"segfault|sigsegv|aborted|core dumped|traceback", re.I)


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def hypr_has_window(pattern: str, instance: str | None = None) -> bool | None:
    cmd = ["hyprctl"]
    if instance:
        cmd += ["-i", instance]
    cmd += ["clients", "-j"]
    try:
        raw = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        clients = json.loads(raw)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        return None
    pat = pattern.lower()
    for c in clients if isinstance(clients, list) else []:
        blob = " ".join(
            str(c.get(k, "")) for k in ("class", "title", "initialClass", "initialTitle")
        ).lower()
        if pat in blob:
            return True
    return False


def scan_log_text(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            if CRASH_RE.search(line):
                return line
            continue
        level = str(row.get("level", "")).lower()
        blob = " ".join(str(row.get(k, "")) for k in ("message", "exception", "event", "detail"))
        if level in {"critical", "fatal"} or CRASH_RE.search(blob):
            return line
    return None


def check(
    *,
    pid: int | None = None,
    window: str | None = None,
    log_path: Path | None = None,
    instance: str | None = None,
) -> dict:
    findings: list[dict] = []
    if pid is not None and not process_alive(pid):
        findings.append({"ruleId": "oracle/window", "message": f"process {pid} not running"})
    if window:
        present = hypr_has_window(window, instance=instance)
        if present is False:
            findings.append(
                {"ruleId": "oracle/window", "message": f"window matching {window!r} unmapped"}
            )
    if log_path and log_path.is_file():
        hit = scan_log_text(log_path.read_text())
        if hit:
            findings.append({"ruleId": "oracle/crash-log", "message": hit})
    return {"ok": not findings, "findings": findings}


def write_reports(result: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "last-oracle.json").write_text(json.dumps(result, indent=2) + "\n")
    failed = not result["ok"]
    ctrf = {
        "results": {
            "tool": {"name": "omarchy-testar", "version": "0.2.0"},
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
                    "name": "oracle",
                    "status": "failed" if failed else "passed",
                    "duration": 1,
                    "message": "; ".join(f["message"] for f in result["findings"])
                    or "oracle ok",
                    "trace": json.dumps(result),
                }
            ],
        }
    }
    (OUT / "ctrf.json").write_text(json.dumps(ctrf, indent=2) + "\n")
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "omarchy-testar", "version": "0.2.0"}},
                "results": [
                    {
                        "ruleId": f["ruleId"],
                        "level": "error",
                        "message": {"text": f["message"]},
                    }
                    for f in result["findings"]
                ],
            }
        ],
    }
    (OUT / "findings.sarif").write_text(json.dumps(sarif, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--window")
    parser.add_argument("--log", type=Path)
    parser.add_argument("--fixture-crash", action="store_true")
    parser.add_argument("--fixture-clean", action="store_true")
    parser.add_argument(
        "--kill-nested-window",
        help="Kill clients matching class/title in nested seat, then oracle",
    )
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    log = args.log
    if args.fixture_crash:
        log = SIM / "fixtures" / "snarksentinel" / "events_crash.jsonl"
    if args.fixture_clean:
        log = SIM / "fixtures" / "snarksentinel" / "events_clean.jsonl"

    instance = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    if args.kill_nested_window:
        if not instance or os.environ.get("OMARCHY_TESTAR_NESTED") != "1":
            raise SystemExit("kill-nested-window requires nested seat env")
        # Record pid of matching client then kill it.
        clients = json.loads(
            subprocess.check_output(["hyprctl", "-i", instance, "clients", "-j"], text=True)
        )
        pat = args.kill_nested_window.lower()
        victim = None
        for c in clients:
            blob = " ".join(str(c.get(k, "")) for k in ("class", "title")).lower()
            if pat in blob:
                victim = c
                break
        if not victim:
            raise SystemExit(f"no nested client matching {args.kill_nested_window!r}")
        pid = int(victim["pid"])
        os.kill(pid, 15)
        import time

        time.sleep(0.4)
        result = check(pid=pid, window=args.kill_nested_window, instance=instance)
        write_reports(result)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if not result["ok"] else 1)

    result = check(pid=args.pid, window=args.window, log_path=log, instance=instance)
    write_reports(result)
    print(json.dumps(result, indent=2))
    if args.fixture_crash and result["ok"]:
        raise SystemExit("expected crash fixture to fail oracle")
    if args.fixture_clean and not result["ok"]:
        raise SystemExit("expected clean fixture to pass oracle")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
