## ADDED Requirements

### Requirement: Button-only derivation from the plugin UI

The explorer SHALL derive actions only from controls with role `button`, using `Accessible.name` when present otherwise `Button.text` from the SnarkSentinel QML surface (or its frozen fixture).

#### Scenario: Inventory is buttons only
- **Tag:** Validated
- **Given** the SnarkSentinel fixture app
- **When** the explorer derives actions from the initial panel state
- **Then** every derived action has role button
- **And** no text-field or static-text actions are selected

### Requirement: Click-everything coverage policy

The explorer SHALL select unvisited enabled buttons until each reachable button has been clicked once. It SHALL NOT use a recorded script of button names.

#### Scenario: Coverage walk clicks each reachable button once
- **Tag:** Validated
- **Given** the SnarkSentinel fixture app
- **When** the explorer runs with the click-all policy
- **Then** the sequence log contains exactly one click per reachable button name
- **And** the walk stops when no unvisited enabled buttons remain

### Requirement: Screenshot after each click

The explorer SHALL write a screenshot artifact after every executed click and reference its path from the step record and CTRF attachments.

#### Scenario: One screenshot per step
- **Tag:** Validated
- **When** the explorer finishes a click-all run
- **Then** each sequence step names a screenshot file that exists on disk

### Requirement: Crash-log oracle

The explorer SHALL inspect SnarkSentinel-shaped JSONL logs after each click. A crash-shaped line SHALL fail the run, write a SARIF finding, and still emit CTRF and JUnit reports.

#### Scenario: Clean logs pass
- **Tag:** Validated
- **Given** clean fixture logs
- **When** the explorer finishes the click-all walk
- **Then** the CTRF result status is passed

#### Scenario: Crash line fails the run
- **Tag:** Validated
- **Given** a crash line is injected into the watched log after a click
- **When** the oracle runs
- **Then** the CTRF result status is failed and findings.sarif contains oracle/crash-log
