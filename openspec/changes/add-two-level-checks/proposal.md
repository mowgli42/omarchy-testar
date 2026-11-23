# Proposal: Two-level checks

## Why

The explorer treats every enabled button as something to click, then looks for a crash. Dead controls, a close button that does not hide the window, unreadable text, and an app with accessibility turned off all survive that loop. Accessibility has to be on before a GUI walk can see the controls.

## What Changes

- Split each run into two levels. Level 1 reads the UI code and does not click. Level 2 clicks only the buttons level 1 associated with an action.
- Level 1 checks four things: every enabled button has an action; a close or X control closes or hides its window; text is readable (contrast, size, scroll); accessibility is enabled.
- Level 2 runs only when the accessibility gate passes. It clicks the associated buttons and fails on a crash or on a close control that leaves the window open.
- The scriptless walk and the SnarkSentinel click-all policy consume that action map. They do not grow a second clicker.

## Capabilities

### New Capabilities

- `logic-audit`: Static checks of the UI code, plus the accessibility gate that level 2 requires.
- `gui-exercise`: Clicks the associated buttons and records runtime failures. Skips the walk when the gate fails.

### Modified Capabilities

- `scriptless-explore`: The walk starts only after the logic audit, selects only associated actions, and records a skipped walk when the accessibility gate fails.
- `snarksentinel-explore`: Click-all visits associated buttons and leaves a button with no action unclicked.

## Impact

- New simulator entry points beside `sim/explore.py`, `sim/plugin_ui.py`, and `sim/snarksentinel_click.py`. Those commands stay until the exercise task points click-all at the action map.
- Reports stay CTRF JSON, JUnit XML, and SARIF 2.1. Each level writes its own trio. Level 2 also writes `sequence.jsonl`.
- Gherkin mirrors live in `features/logic-audit.feature` and `features/gui-exercise.feature`, with one new scenario each on the existing feature files.
- Live Hyprland stays a later task. The fixture graph is the validated stand-in for QML.

## Non-goals

- A full WCAG audit (focus order, keyboard traps, screen-reader announcements).
- Reading text out of screenshots.
- Clicking a button that level 1 did not associate with an action.
- Random long walks, host-seat input, or a Playwright state source.
- Implementing the checkers in this change. This change is the spec, the Gherkin, and the beads plan.
