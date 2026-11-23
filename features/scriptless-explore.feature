# language: en
@explore
Feature: Scriptless explore on a fixture app

  # Validated by sim/explore.py. Not a Cucumber runner yet.
  @validated
  Scenario: Happy path walk emits a sequence
    Given a fixture app with a button that opens a second state
    When the explorer runs with a fixed seed and a sequence length of at least 2
    Then the sequence log contains a click on that button and a later state id

  @validated
  Scenario: Stopping criterion ends the walk
    Given a sequence length of 3
    When the explorer runs
    Then the sequence log has exactly 3 actions

  @validated
  Scenario: Fatal action fails the run
    Given a fixture action marked fatal
    When the explorer selects that action
    Then the CTRF result status is failed and a SARIF finding is written

  @validated
  Scenario: Three artifacts from one run
    When the explorer finishes a run
    Then ctrf.json, junit.xml, and findings.sarif exist and name the same run

  @future
  Scenario: Launch a GTK app in a nested seat
    Given a nested Hyprland seat and a GTK app with an accessibility tree
    When the explorer launches the app
    Then at least one derived action is executed against that tree

  # Future until the walk consumes the logic-audit action map.
  @future
  Scenario: Accessibility gate skips exploration
    When the accessibility gate has failed
    Then the sequence log has no actions and the walk result is skipped
