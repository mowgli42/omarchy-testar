# language: en
@snarksentinel @explore
Feature: Click-all SnarkSentinel accessible buttons

  # Validated by sim/snarksentinel_click.py. Buttons come from Panel.qml /
  # BarWidget.qml; the explorer does not follow a recorded script.
  @validated
  Scenario: Inventory is buttons only
    Given the SnarkSentinel fixture app
    When the explorer derives actions from the initial panel state
    Then every derived action has role button
    And no text-field or static-text actions are selected

  @validated
  Scenario: Coverage walk clicks each reachable button once
    Given the SnarkSentinel fixture app
    When the explorer runs with the click-all policy
    Then the sequence log contains exactly one click per reachable button name
    And the walk stops when no unvisited enabled buttons remain

  @validated
  Scenario: One screenshot per step
    When the explorer finishes a click-all run
    Then each sequence step names a screenshot file that exists on disk

  @validated
  Scenario: Clean logs pass
    Given clean fixture logs
    When the explorer finishes the click-all walk
    Then the CTRF result status is passed

  @validated
  Scenario: Crash line fails the run
    Given a crash line is injected into the watched log after a click
    When the oracle runs
    Then the CTRF result status is failed and findings.sarif contains oracle/crash-log

  @future
  Scenario: Live click-all against snarksentinel panel
    Given a nested Hyprland seat with the SnarkSentinel plugin enabled
    When the explorer summons the panel and runs click-all
    Then each AT-SPI button is clicked once with a PNG screenshot and a log oracle check
