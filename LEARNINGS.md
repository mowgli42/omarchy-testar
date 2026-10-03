# Learnings

- TESTAR's loop (state, derive, select, act, oracle) transfers. Its Windows UI Automation connector does not.
- Wayland is the constraint. A tool that needs xdotool will not run on Omarchy.
- Report adoption is a format problem. CTRF for fidelity, JUnit XML for CI, SARIF for findings. One private JSON is how tools stay unused.
- Random exploration without a nested seat is unsafe. TESTAR documents the same hazard.
