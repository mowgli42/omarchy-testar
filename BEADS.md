# Beads — production rebuild

Not implemented. Prefix `omarchy-testar` when `bd init` is run.

1. **Nested seat.** Run the SUT in a nested Hyprland or a systemd seat so ydotool cannot click the host. Reverse the simulator-only choice.
1b. **Live plugin summon.** `omarchy plugin add` the status panel, `omarchy-shell summon example.status-panel`, read AT-SPI names Status / Refresh / Close.
1c. **Live SnarkSentinel click-all.** Summon `io.github.mowgli42.snarksentinel`, AT-SPI buttons only (same policy as `sim/snarksentinel_click.py`), PNG screenshot after each click, watch `~/.local/share/snarksentinel/logs` + journalctl. Prefer adding `Accessible.name` / `objectName` on Panel.qml buttons so the tree matches the QML labels.
2. **AT-SPI connector.** dogtail or pyatspi against GTK apps. Map roles as in `docs/standards.md`.
3. **Input actuator.** ydotool or EIS, scoped to the nested seat. Do not call xdotool.
4. **Window oracle.** hyprctl: process exit, window unmapped, journalctl error. Crash-log JSONL oracle already prototyped in `sim/snarksentinel_click.py`.
5. **Screenshot fallback.** Apps with an empty accessibility tree. Vision or template match. Higher false-action rate. Keep it a separate state source.
6. **Playwright state source.** Chromium web apps shipped with Omarchy. Same action selector, different scrape.
7. **CTRF attachments.** Screenshots and sequence.jsonl as CTRF attachments, not loose files only.
8. **GitHub Actions.** Upload JUnit XML as the test report and SARIF as code scanning. Fail the job on oracle failure.
9. **Cucumber Messages.** When Gherkin scenarios are executed rather than mirrored, emit ndjson messages. Do not grow the legacy Cucumber JSON formatter.
10. **Open Test Reporting export.** Only after a non-JVM consumer exists in the toolchain.
11. **Action policy.** Replace fixed-seed random with a coverage bias on unvisited roles. TESTAR's research problem. Not needed to prove the report contract.
12. **Replay.** Reconstruct a failing sequence from sequence.jsonl on the same fixture. Live replay waits on stable widget ids across launches.
