# language: en
@logic-audit
Feature: Logic audit of the UI code

  # Future until sim/logic_audit.py exercises these scenarios.
  # Level 1 does not click.

  @future
  Scenario: Enabled button without a handler fails
    When the logic audit reads an enabled button with no action binding
    Then SARIF contains logic/button-without-action for that control

  @future
  Scenario: Disabled button without a handler passes
    When the logic audit reads a button with enabled set to false and no action binding
    Then SARIF contains no logic/button-without-action for that control

  @future
  Scenario: Close handler that hides the panel passes
    When an enabled Close control has an action that hides or closes its panel
    Then SARIF contains no logic/close-does-not-close for that control

  @future
  Scenario: Close handler that does other work fails
    When an enabled Close control has an action that does not hide or close its panel
    Then SARIF contains logic/close-does-not-close for that control

  @future
  Scenario: Disabled close control fails
    When a Close control is disabled
    Then SARIF contains logic/close-does-not-close for that control

  @future
  Scenario: Low-contrast literal colors fail
    When literal colors are below 4.5:1 for text under 18pt (under 14pt if bold), or below 3:1 for larger text
    Then SARIF contains logic/text-contrast for that text

  @future
  Scenario: Sufficient literal contrast passes
    When literal text and background colors meet 4.5:1 at 14px and the text is not bold
    Then SARIF contains no logic/text-contrast for that text

  @future
  Scenario: Unresolved theme color warns and does not fail
    When the text color is a theme token or palette binding and no other error-level finding exists
    Then SARIF contains logic/text-color-unresolved at warning and the logic-audit CTRF status is passed

  @future
  Scenario: Explicit undersize font fails
    When text sets font.pixelSize below 12 or font.pointSize below 9
    Then SARIF contains logic/text-too-small for that text

  @future
  Scenario: Omitted font size passes
    When text does not set a font size
    Then SARIF contains no logic/text-too-small for that text

  @future
  Scenario: Clipped body text without a scroll parent fails
    When body text sets clip or a fixed height and has no scroll parent
    Then SARIF contains logic/text-not-scrollable for that text

  @future
  Scenario: Body text inside a scroll parent passes
    When body text that clips sits inside a Flickable or ScrollView
    Then SARIF contains no logic/text-not-scrollable for that text

  @future
  Scenario: Button label may elide
    When a button label clips or elides and has no scroll parent
    Then SARIF contains no logic/text-not-scrollable for that label

  @future
  Scenario: Accessibility on with names passes the gate
    When accessibility is enabled and every enabled button has an accessible role and a non-empty name
    Then the accessibility gate passes

  @future
  Scenario: Accessibility disabled fails the gate
    When accessibility is disabled
    Then SARIF contains logic/a11y-disabled and the accessibility gate fails

  @future
  Scenario: Enabled button missing a name fails the gate
    When an enabled button has no accessible name
    Then SARIF contains logic/a11y-marker-missing and the accessibility gate fails

  @future
  Scenario: Empty accessibility tree fails the gate
    When a live probe of the app returns an empty accessibility tree
    Then SARIF contains logic/a11y-disabled and the accessibility gate fails

  @future
  Scenario: Three artifacts and no clicks
    When the logic audit finishes
    Then ctrf.json, junit.xml, and findings.sarif exist for the logic-audit run and no click sequence is written
