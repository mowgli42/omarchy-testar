# language: en
@gui-exercise
Feature: Exercise the buttons the logic audit associated

  # Future until sim/exercise.py exercises these scenarios.
  # Level 2 clicks. It does not start when the accessibility gate failed.

  @future
  Scenario: Failed accessibility gate skips clicks
    When the accessibility gate has failed
    Then the gui-exercise CTRF status is skipped and the sequence log has no clicks

  @future
  Scenario: Passed gate allows a click
    When the accessibility gate has passed and the action map has one associated button
    Then the sequence log contains a click on that button

  @future
  Scenario: Associated buttons are clicked once
    When the action map lists two associated buttons
    Then the sequence log contains exactly one click per associated button name

  @future
  Scenario: Button without an action is not clicked
    When one enabled button has an action and another enabled button has none
    Then the sequence log contains a click on the associated button only

  @future
  Scenario: Crash during a click fails the run
    When a crash-shaped log line is recorded after a click
    Then the gui-exercise CTRF status is failed and findings.sarif contains oracle/crash-log

  @future
  Scenario: Close click that leaves the panel open fails
    When the action map associates a close control and the panel is still open after that click
    Then the gui-exercise CTRF status is failed and findings.sarif contains exercise/close-still-open

  @future
  Scenario: Close click that hides the panel passes
    When the action map associates a close control and the panel is hidden after that click
    Then findings.sarif contains no exercise/close-still-open

  @future
  Scenario: Exercise artifacts are separate from the logic audit
    When both levels finish
    Then the exercise CTRF test is gui-exercise, the logic-audit CTRF test is logic-audit, and the exercise sequence log exists

  @future
  Scenario: Live walk clicks associated buttons
    When a nested seat shows an app whose accessibility gate passed
    Then each associated button is clicked once and the close click unmaps its window

  @future
  Scenario: Empty tree does not inject input
    When the live accessibility tree is empty
    Then no input is injected and the gui-exercise CTRF status is skipped
