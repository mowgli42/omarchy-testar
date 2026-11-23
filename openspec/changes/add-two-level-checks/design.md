# Design: Logic audit, then GUI exercise

## Context

Today one loop scrapes a widget tree, treats every enabled button as an action, clicks, and oracles crashes (`sim/explore.py`, `sim/plugin_ui.py`, `sim/snarksentinel_click.py`). Accessible names are an author checklist (`docs/plugin-accessible-markers.md`), not a gate. See proposal.md for why that loop is the wrong first step.

The fixture graph is the stand-in for QML. A live AT-SPI tree is the same model filled from the accessibility bus. Level 1 does not need a seat. Level 2 on a live app does, and only after the gate passes.

## Goals / Non-Goals

**Goals:**

- Produce an action map: enabled button → action binding. Level 2 may click only names in that map.
- Report logic findings without sending input.
- Skip every click when accessibility is off or an enabled button has no accessible name.
- Keep CTRF, JUnit XML, and SARIF. Separate the two levels' artifacts.

**Non-Goals:**

- Pixel contrast, OCR, or a second action selector.
- Failing the whole click walk because one unrelated label has low contrast. That label is a level-1 finding. The click set is still the associated buttons.
- Treating Cancel, or a button whose visible text is the letter X, as a window close.

## Decisions

### 1. Two stages, one map

Level 1 reads code (fixture JSON now, QML scrape into the same fields, AT-SPI later) and writes findings plus an action map. Level 2 is a consumer of that map. It does not re-derive actions from "whatever is enabled."

```
fixture / QML / AT-SPI
        |
        v
+----------------------------------+
| Level 1  logic audit  (no input) |
|  enabled button -> action        |
|  close/X wiring hides the window |
|  text contrast, size, scroll     |
|  accessibility gate              |
+----------------------------------+
        |  findings: CTRF, JUnit, SARIF
        |  action map
        |
        +-- gate failed --> exercise result = skipped
        |
        v
+----------------------------------+
| Level 2  GUI exercise            |
|  click each associated button    |
|  crash and window oracles        |
|  close click must unmap          |
+----------------------------------+
        |
        v
   CTRF, JUnit, SARIF, sequence.jsonl
```

Alternative: keep one loop and add the checks as oracles after each click. Rejected. A button with no handler, a contrast failure, and an app that never exposed AT-SPI are properties of the code. Clicking cannot see the first two, and must not start on the third.

### 2. What "has an action" means

| Source | Associated when |
|--------|-----------------|
| Fixture widget | `enabled` is not false, role is `button`, and `action` is a non-empty string |
| QML | `enabled` is not the literal `false`, role is button (`Button` or `Accessible.role: Accessible.Button`), and the block has `onClicked`, `onPressed`, or `Accessible.onPressAction` whose body contains a call or an assignment |
| AT-SPI (live, later) | enabled, role button, and a named action or a clickable state. An empty accessible name still fails the gate. |

`enabled` omitted means enabled. A non-literal `enabled:` binding is treated as enabled, so a button that is only sometimes disabled still needs a handler.

A disabled button with no handler passes the action check. It is not put on the map, so level 2 does not click it.

### 3. Close is wiring, then effect

Level 1 asks whether the code closes. A control is a close control when its accessible name or text is `Close`, `Close window`, or `Close panel`, or is `×` or `✕`, or its `objectName` matches `close` or `dismiss`. It passes when it is enabled and its action is a close or hide: fixture `closes: true` or `action` of `close` / `hide` / `quit`; QML body containing `.close(`, `visible = false`, `.hide(`, `.destroy(`, or `Qt.quit`.

Level 1 does not click. Level 2 clicks that associated close control and fails `exercise/close-still-open` if the window or panel is still mapped. A close control with no handler fails level 1 twice (`logic/button-without-action` and `logic/close-does-not-close`) and is not clicked. A close control whose handler does something else fails the wiring check, stays on the map if it has an action, and then fails the effect check when clicked.

### 4. Readable text is three literal checks

Computed from source literals, not from a screenshot.

| Check | Fail | Pass without a finding |
|-------|------|------------------------|
| Contrast | Nearest literal text color against the nearest literal ancestor background is under WCAG 2.2 AA: 4.5:1 below 18pt (below 14pt when bold), otherwise 3:1 | Pair meets the ratio |
| Unresolved color | — | `palette.*`, theme tokens, and bindings emit `logic/text-color-unresolved` at warning. Warnings do not fail the level-1 run |
| Size | Explicit `font.pixelSize` < 12 or `font.pointSize` < 9 | Font size omitted (Qt / shell default) |
| Scroll | Body text (`Text`, `Label`, or role `text`) sets `clip: true` or a fixed `height` and has no `Flickable` or `ScrollView` ancestor | Same text inside a scroll parent. Button labels are exempt; they may elide |

Relative luminance uses the WCAG sRGB formula in the standard library. No new dependency.

Alternative: render and sample pixels. Rejected for the fixture path. It needs a seat and disagrees with "check the code." A later live probe may resolve theme colors; until then unresolved color is a warning, not a silent pass and not a failure.

### 5. Accessibility is the only full skip

The gate fails when the fixture or app sets accessibility off, when a live AT-SPI probe returns an empty tree, or when any enabled button lacks `Accessible.role` plus a non-empty `Accessible.name` (or sets `Accessible.ignored: true`).

On failure, level 2 writes a skipped result and does not call the actuator. Other level-1 findings (contrast, size, scroll, a close control wired wrong) are reported and do not cancel clicks of other associated buttons.

Alternative: skip level 2 on any level-1 error. Rejected. The user asked for the click set to be the associated buttons, and named accessibility as the condition GUI testing needs. A dim label should not hide a crash behind the Scan button.

### 6. Reports stay the adoption set

| Level | Directory | CTRF test | Extra |
|-------|-----------|-----------|-------|
| 1 | `sim/out/logic/` | `logic-audit` | SARIF results, no `sequence.jsonl` |
| 2 | `sim/out/exercise/` | `gui-exercise` | `sequence.jsonl`, screenshot path per click when a seat exists |

SARIF rule ids:

- `logic/button-without-action`
- `logic/close-does-not-close`
- `logic/text-contrast`
- `logic/text-too-small`
- `logic/text-not-scrollable`
- `logic/text-color-unresolved` (warning)
- `logic/a11y-marker-missing`
- `logic/a11y-disabled`
- `oracle/crash-log` and `oracle/window` (existing, reused by level 2)
- `exercise/close-still-open`

Level 1 CTRF status is failed when any error-level finding exists. A run that has only color warnings passes level 1. Level 2 status is `skipped`, `passed`, or `failed`. JUnit is still derived from the CTRF result. One testcase per level, not one testcase per control.

### 7. Fixture shape

`sim/fixtures/logic/` holds small graphs. Fields the audit reads, all optional except `role` and `name`:

```json
{
  "accessibility": true,
  "states": {
    "panel": {
      "widgets": [
        {
          "role": "button",
          "name": "Close",
          "objectName": "close",
          "enabled": true,
          "action": "close",
          "closes": true,
          "next": "hidden"
        },
        {
          "role": "text",
          "name": "Status",
          "color": "#eceff4",
          "background": "#1a1b1e",
          "fontPixelSize": 14,
          "clip": false,
          "scrollParent": true
        }
      ]
    }
  }
}
```

QML scrape fills those fields. It is not a second rule set. Parser gaps are a risk on the scrape path; the fixture path is what the scenarios lock.

### 8. Where the code goes

| Module | Role |
|--------|------|
| `sim/logic_audit.py` | Load fixture or QML model, emit findings and the action map, write level-1 reports. No ydotool |
| `sim/readability.py` | Contrast ratio, size floor, scroll-parent check. Pure functions |
| `sim/exercise.py` | Refuse to start when the gate failed. Click map entries via the fixture transition now, the nested-seat actuator later. Reuse `sim/oracle.py` for crash and window |

`sim/policy.py` stays the "first unvisited name" picker. Its input becomes the action map, not the raw enabled list.

## Risks / Trade-offs

- [QML regex scrape misses a handler] → Fixture scenarios are the contract. Scrape is a projection into the same fields. A `Button` block the scraper cannot read becomes `logic/button-without-action` only when the fixture says there is no action; the scraper must not invent a pass.
- [Unresolved theme colors hide a real contrast bug] → Warning, not pass. A live palette probe is a later bead, not a silent success.
- [Close vocabulary misses an icon font glyph] → Match the accessible name and `objectName`, not the icon font. Authors already owe `Accessible.name` of `Close`.
- [Skipping the walk hides crashes in an inaccessible app] → The skip is a failed gate in level 1 and a skipped level 2, so CI still shows red on `logic/a11y-disabled`. The crash oracle does not run because the clicker is not allowed to poke a tree it cannot see.
- [Two report directories] → CI uploads both. A single merged status would hide which level failed.

## Migration Plan

Add `sim/logic_audit.py` and `sim/exercise.py` beside the current commands. Point `sim/snarksentinel_click.py` and `sim/explore.py` at the action map only in the exercise task, after the fixture scenarios pass. Rollback is to keep calling the old commands. No report schema change beyond new rule ids and a `skipped` status. No host-seat use.

## Beads

Build order is `.beads/two-level-checks.graph.json`. Simulator beads do not wait on a seat. The live bead waits on the accessibility gate and the fixture exercise.
