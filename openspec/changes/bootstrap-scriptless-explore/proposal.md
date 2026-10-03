# Proposal: bootstrap scriptless explore

## Why

Omarchy has no TESTAR-shaped tool. Porting TESTAR's Windows connector will not work on Hyprland. A plan that picks interchange formats up front is more likely to be adopted than a private log format.

## What

- Living OpenSpec and Gherkin for the explore loop, crash oracle, and report export
- Format decision: CTRF canonical, JUnit XML compatibility, SARIF for findings
- Fixture simulator that exercises the validated scenarios
- Beads for the live seat, screenshot fallback, and CI upload

## Non-goals

- Driving a real Hyprland session in this change
- Porting TESTAR's OrientDB state model
- Allure, TAP, or Open Test Reporting as a primary format
- Mobile (Appium, Maestro)
- Replacing Playwright for scripted web E2E

## Formats touched

CTRF, JUnit XML, SARIF. Gherkin for the human spec. Cucumber Messages deferred until a Gherkin runner exists.
