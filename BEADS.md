# Beads — production rebuild

Initialized with prefix `omarchy-testar`. Source of truth is `bd`, not this file.

```bash
bd ready                  # claimable work
bd show <id>              # details + acceptance
bd update <id> --claim    # start
bd close <id>             # done
```

Reseed plan (documentation only): `.beads/production-rebuild.graph.json`

## Epic

| ID | Title |
|----|-------|
| `omarchy-testar-mtw` | Production rebuild: live Omarchy seat + report adoption |

## Live seat chain (blocked until nested seat + AT-SPI + actuator)

| ID | Title | Blocked by |
|----|-------|------------|
| `omarchy-testar-c23` | Nested seat for safe GUI exploration | closed (scripts + smoke) |
| `omarchy-testar-9xv` | AT-SPI connector for widget scrape | closed (fixture + optional pyatspi) |
| `omarchy-testar-3sa` | Input actuator (ydotool / EIS) | nested seat |
| `omarchy-testar-1h5` | Live plugin summon (example.status-panel) | seat + AT-SPI + actuator |
| `omarchy-testar-6oo` | Accessible.name on SnarkSentinel Panel buttons | closed (snarksentinel PR) |
| `omarchy-testar-g77` | Live SnarkSentinel click-all | plugin summon + a11y QML |
| `omarchy-testar-9ze` | Window / journal crash oracle | nested seat |
| `omarchy-testar-pgx` | Screenshot fallback state source | AT-SPI |

## Fixture / adoption (can proceed without a live seat)

| ID | Title | Status |
|----|-------|--------|
| `omarchy-testar-4bf` | CTRF attachments for screenshots and sequence.jsonl | closed |
| `omarchy-testar-gmw` | Replay failing sequence from sequence.jsonl | closed |
| `omarchy-testar-9mr` | GitHub Actions: JUnit + SARIF upload | closed |
| `omarchy-testar-enu` | Coverage-biased action policy | closed (`sim/policy.py`) |
| `omarchy-testar-y2z` | Playwright state source for Chromium apps | deferred |
| `omarchy-testar-8pb` | Cucumber Messages when Gherkin executes | open |
| `omarchy-testar-5z7` | Open Test Reporting export (deferred; after Cucumber Messages) | open |
