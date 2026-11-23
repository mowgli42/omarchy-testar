# Verification

No scenario below is exercised yet. Tags stay Future until the task command passes.

| Scenario | Will be exercised by |
|----------|----------------------|
| Enabled button without a handler fails | `python3 sim/logic_audit.py` on an enabled button with no action |
| Disabled button without a handler passes | fixture button `enabled: false` |
| Close handler that hides the panel passes | Close with `closes: true` |
| Close handler that does other work fails | Close whose action is not close/hide/quit |
| Disabled close control fails | Close with `enabled: false` |
| Low-contrast literal colors fail | literal pair under 4.5:1 |
| Sufficient literal contrast passes | `#eceff4` on `#1a1b1e` at 14px |
| Unresolved theme color warns and does not fail | `palette.windowText` with no other errors |
| Explicit undersize font fails | `fontPixelSize: 10` |
| Omitted font size passes | text with no font field |
| Clipped body text without a scroll parent fails | `clip: true`, `scrollParent: false` |
| Body text inside a scroll parent passes | `scrollParent: true` |
| Button label may elide | clipped role=button |
| Accessibility on with names passes the gate | `accessibility: true` and names set |
| Accessibility disabled fails the gate | `accessibility: false` |
| Enabled button missing a name fails the gate | button with empty name |
| Empty accessibility tree fails the gate | live AT-SPI probe, group 3 |
| Three artifacts and no clicks | `sim/out/logic/{ctrf.json,junit.xml,findings.sarif}` and no sequence |
| Failed accessibility gate skips clicks | `python3 sim/exercise.py` after a failed gate |
| Passed gate allows a click | one associated button |
| Associated buttons are clicked once | two-button action map |
| Button without an action is not clicked | mixed fixture |
| Crash during a click fails the run | `--inject-crash` |
| Close click that leaves the panel open fails | close `next` stays on the panel |
| Close click that hides the panel passes | close `next` is hidden |
| Exercise artifacts are separate from the logic audit | `sim/out/exercise/` vs `sim/out/logic/` |
| Live walk clicks associated buttons | nested seat, group 3 |
| Empty tree does not inject input | nested seat with a11y off |
| Accessibility gate skips exploration | scriptless walk after a failed gate |
| Button without an action is left unclicked | SnarkSentinel fixture plus one action-less button |

Reports touched: CTRF JSON, JUnit XML, SARIF 2.1.
