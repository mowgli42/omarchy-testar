# Agent notes

- OpenSpec + Gherkin + beads. Follow `openspec/WORKFLOW.md`.
- Graham-bell while this repo is under 30 days: demo and honest specs over production hardening.
- Do not claim a live Hyprland run is validated. The simulator is the only exercised path.
- SnarkSentinel buttons are authored in QML; discovery for click-all uses Accessible.name / Button.text (fixture or `--scrape`). Do not hand-write click scripts.
- Report outputs: CTRF canonical, JUnit XML compatibility, SARIF for findings. Do not add Allure or TAP as a primary format.
- Wayland input is `ydotool` or a virtual seat. Do not depend on `xdotool`.
- Never inject into the host Hyprland seat. Use `scripts/nested-seat.sh` (see `docs/nested-seat.md`).
- Widget identity maps to AT-SPI / WAI-ARIA roles via `sim/atspi.py` / `sim/policy.py` so dogtail and future Playwright snapshots feed the same selector.
- Playwright state source bead is deferred.
