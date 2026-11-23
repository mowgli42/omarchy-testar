# Verification

Simulator scenarios: `python3 sim/logic_audit.py --self-test` and `python3 sim/exercise.py --self-test`. Live scenarios stay Future.

| Scenario | Exercised by |
|----------|--------------|
| Enabled button without a handler fails | `button-no-action.json` |
| Disabled button without a handler passes | `button-disabled-no-action.json` |
| Close handler that hides the panel passes | `close-ok.json` |
| Close handler that does other work fails | `close-wrong-action.json` |
| Disabled close control fails | `close-disabled.json` |
| Low-contrast literal colors fail | `contrast-fail.json` |
| Sufficient literal contrast passes | `readable.json` |
| Unresolved theme color warns and does not fail | `theme-color.json` |
| Explicit undersize font fails | `text-too-small.json` |
| Omitted font size passes | `text-no-size.json` |
| Clipped body text without a scroll parent fails | `text-clip-no-scroll.json` |
| Body text inside a scroll parent passes | `text-clip-scroll.json` |
| Button label may elide | `button-label-elide.json` |
| Accessibility on with names passes the gate | `readable.json` |
| Accessibility disabled fails the gate | `a11y-off.json` |
| Enabled button missing a name fails the gate | `a11y-missing-name.json` |
| Empty accessibility tree fails the gate | live AT-SPI probe (Future) |
| Three artifacts and no clicks | `sim/out/logic/{ctrf.json,junit.xml,findings.sarif}` |
| Failed accessibility gate skips clicks | `exercise.py` + `a11y-off.json` |
| Passed gate allows a click | `exercise-two.json` / `readable.json` |
| Associated buttons are clicked once | `exercise-two.json` |
| Button without an action is not clicked | `exercise-mixed.json` |
| Crash during a click fails the run | `--inject-crash` / `exercise-crash.json` |
| Close click that leaves the panel open fails | `exercise-close-stay.json` |
| Close click that hides the panel passes | `exercise-close-hide.json` |
| Exercise artifacts are separate from the logic audit | `sim/out/exercise/` vs `sim/out/logic/` |
| Live walk clicks associated buttons | nested seat (Future) |
| Empty tree does not inject input | nested seat (Future) |
| Accessibility gate skips exploration | gate fail → empty sequence |
| Button without an action is left unclicked | `exercise-mixed.json` |

Reports touched: CTRF JSON, JUnit XML, SARIF 2.1.
