"""Literal text readability checks for the logic audit.

Contrast uses WCAG 2.2 relative luminance. No screenshot sampling.
"""

from __future__ import annotations

import re

HEX = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
THEME = re.compile(r"^(palette\.|Theme\.|theme\.|Kirigami\.|Material\.)")


def parse_hex(color: str | None) -> tuple[float, float, float] | None:
    if not color or not isinstance(color, str):
        return None
    m = HEX.match(color.strip())
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r / 255.0, g / 255.0, b / 255.0


def is_unresolved_color(color: str | None) -> bool:
    if color is None or color == "":
        return False
    if parse_hex(color) is not None:
        return False
    return bool(THEME.match(color.strip())) or ("." in color) or ("(" in color)


def _channel(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (_channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float | None:
    a = parse_hex(fg)
    b = parse_hex(bg)
    if a is None or b is None:
        return None
    l1 = relative_luminance(a)
    l2 = relative_luminance(b)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def required_contrast(*, font_px: float | None, font_pt: float | None, bold: bool) -> float:
    """WCAG 2.2 AA: 4.5:1 normal, 3:1 large (18pt / 14pt bold)."""
    large = False
    if font_pt is not None:
        large = font_pt >= 18 or (bold and font_pt >= 14)
    elif font_px is not None:
        # 1pt ≈ 1.333px at 96dpi; 18pt ≈ 24px, 14pt ≈ 18.67px
        large = font_px >= 24 or (bold and font_px >= 18.67)
    return 3.0 if large else 4.5


def check_contrast(widget: dict) -> dict | None:
    """Return a finding dict or None. Warnings use level=warning."""
    role = widget.get("role")
    color = widget.get("color")
    background = widget.get("background")
    if role == "button" and color is None and background is None:
        return None
    if color is None and background is None:
        return None
    if is_unresolved_color(color) or is_unresolved_color(background):
        return {
            "ruleId": "logic/text-color-unresolved",
            "level": "warning",
            "message": f"unresolved color on {widget.get('name')!r}: {color!r} / {background!r}",
            "name": widget.get("name"),
        }
    if color is None or background is None:
        return {
            "ruleId": "logic/text-color-unresolved",
            "level": "warning",
            "message": f"missing literal color pair on {widget.get('name')!r}",
            "name": widget.get("name"),
        }
    ratio = contrast_ratio(color, background)
    if ratio is None:
        return {
            "ruleId": "logic/text-color-unresolved",
            "level": "warning",
            "message": f"unparsed colors on {widget.get('name')!r}",
            "name": widget.get("name"),
        }
    need = required_contrast(
        font_px=_num(widget.get("fontPixelSize")),
        font_pt=_num(widget.get("fontPointSize")),
        bold=bool(widget.get("bold")),
    )
    if ratio + 1e-9 < need:
        return {
            "ruleId": "logic/text-contrast",
            "level": "error",
            "message": f"{widget.get('name')!r} contrast {ratio:.2f}:1 below {need}:1",
            "name": widget.get("name"),
        }
    return None


def check_size(widget: dict) -> dict | None:
    px = _num(widget.get("fontPixelSize"))
    pt = _num(widget.get("fontPointSize"))
    if px is None and pt is None:
        return None
    if (px is not None and px < 12) or (pt is not None and pt < 9):
        return {
            "ruleId": "logic/text-too-small",
            "level": "error",
            "message": f"{widget.get('name')!r} font below 12px/9pt",
            "name": widget.get("name"),
        }
    return None


def check_scroll(widget: dict) -> dict | None:
    role = widget.get("role")
    if role == "button":
        return None  # labels may elide
    if role not in {"text", "statictext", "label"}:
        return None
    clipped = bool(widget.get("clip")) or _num(widget.get("height")) is not None
    if not clipped:
        return None
    if widget.get("scrollParent"):
        return None
    return {
        "ruleId": "logic/text-not-scrollable",
        "level": "error",
        "message": f"{widget.get('name')!r} clips without a scroll parent",
        "name": widget.get("name"),
    }


def _num(v) -> float | None:
    if v is None or v is False:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def check_widget(widget: dict) -> list[dict]:
    findings: list[dict] = []
    for fn in (check_contrast, check_size, check_scroll):
        hit = fn(widget)
        if hit:
            findings.append(hit)
    return findings
