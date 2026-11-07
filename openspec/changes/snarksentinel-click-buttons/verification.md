# Verification

| Scenario | Exercised by |
|----------|--------------|
| Derive buttons from QML / fixture | `python3 sim/snarksentinel_click.py` |
| Click-all coverage visits every reachable button once | asserts on visited set vs enabled inventory |
| Screenshot written after each click | `sim/out/snarksentinel/screenshots/step-*.svg` |
| Clean logs → run passes | default fixture logs |
| Crash log line → CTRF failed + SARIF finding | `--inject-crash` |
| Reports emitted | `ctrf.json`, `junit.xml`, `findings.sarif`, `sequence.jsonl` |
