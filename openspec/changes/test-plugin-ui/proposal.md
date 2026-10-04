# Proposal: test an Omarchy plugin UI

## Why

Omarchy UI is plugins inside `omarchy-shell` (Quickshell), not standalone apps. A TESTAR-style tool has to load a manifest, summon a panel, and walk controls.

## What

- Example plugin `examples/status-panel` (bar-widget + panel)
- Walker that validates the manifest and drives Accessible.name controls
- CTRF, JUnit XML, SARIF, and an HTML walk

## Non-goals

- Running Quickshell or Hyprland in this change
- Calling live `omarchy-shell` IPC
- Screenshot diff of a real bar

## Formats touched

CTRF, JUnit XML, SARIF. Gherkin for the scenarios.
