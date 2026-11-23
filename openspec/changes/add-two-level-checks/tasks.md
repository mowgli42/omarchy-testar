# Tasks

## 1. Simulator: logic audit

- [x] 1.1 Add `sim/fixtures/logic/` and `sim/logic_audit.py` to load role, name, enabled, action, closes, colors, font size, clip, scroll parent, and the accessibility flag. Verify `python3 sim/logic_audit.py --dump sim/fixtures/logic/readable.json` prints those fields and exits 0.
- [x] 1.2 Fail an enabled button with no action and pass a disabled button with no action. Verify the enabled fixture writes SARIF `logic/button-without-action` and the disabled fixture does not.
- [x] 1.3 Fail a disabled Close control and a Close control whose action does not hide the panel; pass an enabled Close whose action hides it. Verify SARIF `logic/close-does-not-close` on the two failures only.
- [x] 1.4 Check contrast, size, and scroll in `sim/readability.py`. Verify below-AA colors write `logic/text-contrast`, a 4.5:1 pair at 14px does not, a theme token writes warning `logic/text-color-unresolved` and still passes CTRF, `font.pixelSize` 10 writes `logic/text-too-small`, omitted size does not, clipped body text without a scroll parent writes `logic/text-not-scrollable`, a Flickable parent does not, and a clipped button label does not.
- [x] 1.5 Fail the accessibility gate when accessibility is off or an enabled button has no name; pass when accessibility is on and names are present. Verify `logic/a11y-disabled` and `logic/a11y-marker-missing`.
- [x] 1.6 Write `sim/out/logic/ctrf.json`, `junit.xml`, and `findings.sarif` with test name `logic-audit`. Verify the three files exist, JUnit matches the CTRF status, and no click sequence file is written. Retag the covered scenarios in `features/logic-audit.feature` from `@future` to `@validated`.

## 2. Simulator: GUI exercise

- [x] 2.1 Skip clicks when the accessibility gate failed. Verify `python3 sim/exercise.py` on an accessibility-off fixture writes CTRF status `skipped` and an empty sequence.
- [x] 2.2 Click each associated button once and leave a button with no action unclicked. Verify the sequence names match the action map and omit the unassociated name.
- [x] 2.3 Reuse the crash-log oracle and fail `exercise/close-still-open` when a close click leaves the panel open. Verify `--inject-crash` writes `oracle/crash-log` and a stay-open close fixture fails. Verify a hiding close does not write `exercise/close-still-open`.
- [x] 2.4 Write `sim/out/exercise/ctrf.json`, `junit.xml`, `findings.sarif`, and `sequence.jsonl` with test name `gui-exercise`, separate from `sim/out/logic/`. Verify both CTRF test names. Retag the covered scenarios in `features/gui-exercise.feature`, `features/scriptless-explore.feature`, and `features/snarksentinel-click.feature` from `@future` to `@validated`.

## 3. Live Hyprland

- [x] 3.1 Probe an AT-SPI dump and skip exercise when it is empty. Verify `python3 sim/exercise.py --live-gate-smoke` writes skipped with no actuator events on the empty tree, and dry-run clicks on the populated tree (`host_injection: none`).
- [ ] 3.2 Click associated buttons in a real nested Hyprland seat, capture a PNG per click, and fail when the close click leaves the window mapped. (Still Future in Gherkin; dry-run gate is closed.)

## Workflow follow-up

- Archive `add-two-level-checks` into `openspec/specs/` after review.
- Leave the live scenarios tagged Future until group 3 is exercised.
