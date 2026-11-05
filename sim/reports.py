"""Shared CTRF attachment helpers for sim explorers."""

from __future__ import annotations

from pathlib import Path


def attachments_for(out_dir: Path, sequence_name: str = "sequence.jsonl") -> list[dict]:
    """List sequence.jsonl and any screenshots under out_dir as CTRF attachments."""
    items: list[dict] = []
    seq = out_dir / sequence_name
    if seq.is_file():
        items.append({"name": sequence_name, "path": sequence_name})
    shots = out_dir / "screenshots"
    if shots.is_dir():
        for path in sorted(shots.iterdir()):
            if path.is_file():
                rel = f"screenshots/{path.name}"
                items.append({"name": rel, "path": rel})
    return items


def assert_attachments_resolve(out_dir: Path, report: dict) -> None:
    test = report["results"]["tests"][0]
    atts = test.get("attachments") or []
    assert atts, "CTRF test missing attachments"
    names = {a["name"] for a in atts}
    assert any(n.endswith("sequence.jsonl") or n.endswith("plugin-sequence.jsonl") for n in names), names
    for att in atts:
        assert (out_dir / att["path"]).is_file(), att["path"]
