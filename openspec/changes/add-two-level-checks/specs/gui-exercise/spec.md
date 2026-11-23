# gui-exercise

## Purpose

Clicks the buttons the logic audit associated with actions and records crashes, skipped runs, and close controls that leave the window open.

## ADDED Requirements

### Requirement: Skip exercise when the gate fails

GUI exercise SHALL NOT click when the accessibility gate failed, and SHALL write a skipped result.

#### Scenario: Failed accessibility gate skips clicks
- **Tag:** Future
- **WHEN** the accessibility gate has failed
- **THEN** the gui-exercise CTRF status is skipped and the sequence log has no clicks

#### Scenario: Passed gate allows a click
- **Tag:** Future
- **WHEN** the accessibility gate has passed and the action map has one associated button
- **THEN** the sequence log contains a click on that button

### Requirement: Click associated buttons only

GUI exercise SHALL click each enabled button the logic audit associated with an action, once. It SHALL NOT click a button that has no associated action. It SHALL NOT use a recorded script of button names.

#### Scenario: Associated buttons are clicked once
- **Tag:** Future
- **WHEN** the action map lists two associated buttons
- **THEN** the sequence log contains exactly one click per associated button name

#### Scenario: Button without an action is not clicked
- **Tag:** Future
- **WHEN** one enabled button has an action and another enabled button has none
- **THEN** the sequence log contains a click on the associated button only

### Requirement: Exercise failures

GUI exercise SHALL fail the run when a click crashes the app or when clicking an associated close control leaves its window or panel open. A close click that hides the window SHALL pass this check.

#### Scenario: Crash during a click fails the run
- **Tag:** Future
- **WHEN** a crash-shaped log line is recorded after a click
- **THEN** the gui-exercise CTRF status is failed and findings.sarif contains oracle/crash-log

#### Scenario: Close click that leaves the panel open fails
- **Tag:** Future
- **WHEN** the action map associates a close control and the panel is still open after that click
- **THEN** the gui-exercise CTRF status is failed and findings.sarif contains exercise/close-still-open

#### Scenario: Close click that hides the panel passes
- **Tag:** Future
- **WHEN** the action map associates a close control and the panel is hidden after that click
- **THEN** findings.sarif contains no exercise/close-still-open

### Requirement: Exercise reports

GUI exercise SHALL write CTRF JSON, JUnit XML, and SARIF 2.1 for the exercise run, plus a sequence log of the clicks it performed.

#### Scenario: Exercise artifacts are separate from the logic audit
- **Tag:** Future
- **WHEN** both levels finish
- **THEN** the exercise CTRF test is gui-exercise, the logic-audit CTRF test is logic-audit, and the exercise sequence log exists

### Requirement: Live exercise in a nested seat

GUI exercise SHALL click associated buttons inside a nested Hyprland seat and SHALL NOT inject input when the accessibility tree is empty.

#### Scenario: Live walk clicks associated buttons
- **Tag:** Future
- **WHEN** a nested seat shows an app whose accessibility gate passed
- **THEN** each associated button is clicked once and the close click unmaps its window

#### Scenario: Empty tree does not inject input
- **Tag:** Future
- **WHEN** the live accessibility tree is empty
- **THEN** no input is injected and the gui-exercise CTRF status is skipped
