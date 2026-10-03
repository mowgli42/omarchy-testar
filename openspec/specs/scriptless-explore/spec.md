# scriptless-explore

Scriptless GUI exploration and report export for Omarchy apps.

## Requirements

### Requirement: Explore a state graph

The explorer SHALL start from a known initial state, derive enabled actions from the current widget tree, select one action, and advance until a stopping criterion is met.

#### Scenario: Happy path walk emits a sequence

- **Tag:** Validated
- **Given** a fixture app with a button that opens a second state
- **When** the explorer runs with a fixed seed and a sequence length of at least 2
- **Then** the sequence log contains a click on that button and a later state id

#### Scenario: Stopping criterion ends the walk

- **Tag:** Validated
- **Given** a sequence length of 3
- **When** the explorer runs
- **Then** the sequence log has exactly 3 actions

### Requirement: Oracle on crash

The explorer SHALL treat a widget action that the state source marks as fatal as a failed oracle, and SHALL still write reports.

#### Scenario: Fatal action fails the run

- **Tag:** Validated
- **Given** a fixture action marked fatal
- **When** the explorer selects that action
- **Then** the CTRF result status is failed and a SARIF finding is written

### Requirement: Report for adoption

The explorer SHALL write CTRF JSON as the canonical report, JUnit XML as a CI compatibility export, and SARIF 2.1 for oracle findings.

#### Scenario: Three artifacts from one run

- **Tag:** Validated
- **When** the explorer finishes a run
- **Then** `ctrf.json`, `junit.xml`, and `findings.sarif` exist and name the same run

### Requirement: Live Hyprland seat

The explorer SHALL drive a real Omarchy app through AT-SPI or a screenshot fallback and `ydotool`.

#### Scenario: Launch a GTK app in a nested seat

- **Tag:** Future
- **Given** a nested Hyprland seat and a GTK app with an accessibility tree
- **When** the explorer launches the app
- **Then** at least one derived action is executed against that tree

## ADDED note

Living copy of the bootstrap change. Future scenarios are not exercised.
