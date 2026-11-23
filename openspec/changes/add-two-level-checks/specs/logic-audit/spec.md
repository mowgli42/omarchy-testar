# logic-audit

## Purpose

Checks an Omarchy UI from its code, before any click: every enabled button has an action, close controls hide the window, text stays readable, and accessibility is on.

## ADDED Requirements

### Requirement: Enabled button has an action

The logic audit SHALL fail an enabled button-role control that has no action binding. A control with enabled set to false SHALL pass this check. The audit SHALL NOT click.

#### Scenario: Enabled button without a handler fails
- **Tag:** Validated
- **WHEN** the logic audit reads an enabled button with no action binding
- **THEN** SARIF contains logic/button-without-action for that control

#### Scenario: Disabled button without a handler passes
- **Tag:** Validated
- **WHEN** the logic audit reads a button with enabled set to false and no action binding
- **THEN** SARIF contains no logic/button-without-action for that control

### Requirement: Close control closes the window

The logic audit SHALL fail a close control that is disabled or whose action does not close or hide its window or panel. A close control is one named Close, Close window, or Close panel, named × or ✕, or with objectName close or dismiss. The audit SHALL NOT click it.

#### Scenario: Close handler that hides the panel passes
- **Tag:** Validated
- **WHEN** an enabled Close control has an action that hides or closes its panel
- **THEN** SARIF contains no logic/close-does-not-close for that control

#### Scenario: Close handler that does other work fails
- **Tag:** Validated
- **WHEN** an enabled Close control has an action that does not hide or close its panel
- **THEN** SARIF contains logic/close-does-not-close for that control

#### Scenario: Disabled close control fails
- **Tag:** Validated
- **WHEN** a Close control is disabled
- **THEN** SARIF contains logic/close-does-not-close for that control

### Requirement: Text contrast meets AA

The logic audit SHALL fail text whose literal color against the nearest literal background is below WCAG 2.2 AA. Unresolved colors SHALL be warnings and SHALL NOT fail the run by themselves.

#### Scenario: Low-contrast literal colors fail
- **Tag:** Validated
- **WHEN** literal colors are below 4.5:1 for text under 18pt (under 14pt if bold), or below 3:1 for larger text
- **THEN** SARIF contains logic/text-contrast for that text

#### Scenario: Sufficient literal contrast passes
- **Tag:** Validated
- **WHEN** literal text and background colors meet 4.5:1 at 14px and the text is not bold
- **THEN** SARIF contains no logic/text-contrast for that text

#### Scenario: Unresolved theme color warns and does not fail
- **Tag:** Validated
- **WHEN** the text color is a theme token or palette binding and no other error-level finding exists
- **THEN** SARIF contains logic/text-color-unresolved at warning and the logic-audit CTRF status is passed

### Requirement: Text size is at least the floor

The logic audit SHALL fail text that sets an explicit font size below 12 pixels or below 9 points.

#### Scenario: Explicit undersize font fails
- **Tag:** Validated
- **WHEN** text sets font.pixelSize below 12 or font.pointSize below 9
- **THEN** SARIF contains logic/text-too-small for that text

#### Scenario: Omitted font size passes
- **Tag:** Validated
- **WHEN** text does not set a font size
- **THEN** SARIF contains no logic/text-too-small for that text

### Requirement: Clipped body text can scroll

The logic audit SHALL fail body text that clips overflow and has no Flickable or ScrollView ancestor. Button labels SHALL be exempt.

#### Scenario: Clipped body text without a scroll parent fails
- **Tag:** Validated
- **WHEN** body text sets clip or a fixed height and has no scroll parent
- **THEN** SARIF contains logic/text-not-scrollable for that text

#### Scenario: Body text inside a scroll parent passes
- **Tag:** Validated
- **WHEN** body text that clips sits inside a Flickable or ScrollView
- **THEN** SARIF contains no logic/text-not-scrollable for that text

#### Scenario: Button label may elide
- **Tag:** Validated
- **WHEN** a button label clips or elides and has no scroll parent
- **THEN** SARIF contains no logic/text-not-scrollable for that label

### Requirement: Accessibility gate

The logic audit SHALL fail the accessibility gate when accessibility is disabled, the live accessibility tree is empty, or an enabled button lacks an accessible role and non-empty name.

#### Scenario: Accessibility on with names passes the gate
- **Tag:** Validated
- **WHEN** accessibility is enabled and every enabled button has an accessible role and a non-empty name
- **THEN** the accessibility gate passes

#### Scenario: Accessibility disabled fails the gate
- **Tag:** Validated
- **WHEN** accessibility is disabled
- **THEN** SARIF contains logic/a11y-disabled and the accessibility gate fails

#### Scenario: Enabled button missing a name fails the gate
- **Tag:** Validated
- **WHEN** an enabled button has no accessible name
- **THEN** SARIF contains logic/a11y-marker-missing and the accessibility gate fails

#### Scenario: Empty accessibility tree fails the gate
- **Tag:** Future
- **WHEN** a live probe of the app returns an empty accessibility tree
- **THEN** SARIF contains logic/a11y-disabled and the accessibility gate fails

### Requirement: Logic audit reports without clicking

The logic audit SHALL write CTRF JSON, JUnit XML, and SARIF 2.1 for its findings and SHALL NOT perform a click.

#### Scenario: Three artifacts and no clicks
- **Tag:** Validated
- **WHEN** the logic audit finishes
- **THEN** ctrf.json, junit.xml, and findings.sarif exist for the logic-audit run and no click sequence is written
