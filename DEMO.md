# Demo

Fixture only. No Hyprland required.

```bash
python3 sim/explore.py
```

Expect:

- `sim/out/sequence.jsonl` — 3 actions, including a click on Open
- `sim/out/ctrf.json` — one failed test (fatal action)
- `sim/out/junit.xml` — one failure, same name
- `sim/out/findings.sarif` — one crash result

The fatal action is deliberate. A green run would not exercise the oracle scenario.

Future live-seat scenario is tagged `@future` and is not part of this demo.
