"""Coverage-biased action selection for scriptless explore.

Picks the first unvisited enabled action (deterministic coverage), with an
optional role filter. Shared by explore.py, snarksentinel_click.py, and the
future live seat.
"""

from __future__ import annotations


def filter_actions(
    widgets: list[dict],
    *,
    roles: set[str] | None = None,
) -> list[dict]:
    """Return enabled widgets, optionally restricted to roles."""
    out: list[dict] = []
    for w in widgets:
        if roles is not None and w.get("role") not in roles:
            continue
        out.append(w)
    return out


def pick_unvisited(
    widgets: list[dict],
    visited: set[str],
    *,
    key: str = "name",
    roles: set[str] | None = None,
) -> dict | None:
    """First widget whose key is not in visited (coverage bias)."""
    for w in filter_actions(widgets, roles=roles):
        token = str(w.get(key, ""))
        if token and token not in visited:
            return w
    return None


def mark_visited(visited: set[str], widget: dict, *, key: str = "name") -> None:
    token = str(widget.get(key, ""))
    if token:
        visited.add(token)
