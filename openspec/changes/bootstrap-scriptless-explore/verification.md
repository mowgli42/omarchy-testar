# Verification: bootstrap scriptless explore

| Scenario | Tag | Exercised by |
|----------|-----|----------------|
| Happy path walk emits a sequence | Validated | `python3 sim/explore.py` sequence length and click record |
| Stopping criterion ends the walk | Validated | sequence length 3 in `sim/out/sequence.jsonl` |
| Fatal action fails the run | Validated | CTRF status failed, SARIF result present |
| Three artifacts from one run | Validated | `ctrf.json`, `junit.xml`, `findings.sarif` |
| Launch a GTK app in a nested seat | Future | not exercised |

Command: `python3 sim/explore.py`
