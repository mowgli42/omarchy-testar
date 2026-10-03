# omarchy-testar — Project Context

## Purpose

Scriptless exploration of GUI apps on Omarchy. Generate (state, action) sequences, apply oracles, emit reports CI already knows how to ingest.

## Tech stack (planned)

- **Explorer:** Python 3, stdlib only for the simulator
- **Live actuators (future):** AT-SPI2 / dogtail where the app exposes a tree; `ydotool` for input; `hyprctl` for window oracles
- **Web apps:** Playwright accessibility snapshot as a second state source, not a second product
- **Specs:** OpenSpec in `openspec/specs/`
- **Gherkin:** `features/`
- **Beads:** `BEADS.md` until `bd` is initialized (prefix `omarchy-testar`)

## Conventions

- One change under `openspec/changes/<change-id>/`
- Scenarios mirrored in `features/*.feature`
- A scenario is Validated only if `sim/explore.py` or a later E2E harness exercises it
- Reports land in `sim/out/` and are gitignored

## Phase map

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | OpenSpec, Gherkin, format decision, fixture simulator | This change |
| 1 | Live GTK app via AT-SPI in a nested seat | Planned |
| 2 | Screenshot fallback for non-a11y clients | Planned |
| 3 | Playwright snapshot source for Chromium web apps | Planned |
| 4 | CI packaging (GitHub Actions + JUnit + SARIF upload) | Planned |
