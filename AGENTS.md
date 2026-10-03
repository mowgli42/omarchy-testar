# Agent notes

- OpenSpec + Gherkin + beads. Follow `openspec/WORKFLOW.md`.
- Graham-bell while this repo is under 30 days: demo and honest specs over production hardening.
- Do not claim a live Hyprland run is validated. The simulator is the only exercised path.
- Report outputs: CTRF canonical, JUnit XML compatibility, SARIF for findings. Do not add Allure or TAP as a primary format.
- Wayland input is `ydotool` or a virtual seat. Do not depend on `xdotool`.
- Widget identity maps to AT-SPI / WAI-ARIA roles so dogtail and Playwright snapshots can feed the same selector.
