# language: en
@plugin-ui
Feature: Explore an Omarchy plugin user interface

  # Validated by sim/plugin_ui.py against examples/status-panel.
  @validated
  Scenario: Manifest is loadable
    Given a plugin directory with schemaVersion 1 and an unreserved id
    And entry point files exist for each declared kind
    When the explorer validates the plugin
    Then validation produces no errors

  @validated
  Scenario: Bar widget summons the panel
    Given a bar-widget control named Status
    When the explorer summons the plugin
    Then the panel state is visible

  @validated
  Scenario: Refresh updates the panel status
    Given the panel is open
    When the explorer clicks Refresh
    Then the status text is Checked

  @validated
  Scenario: Close hides the panel
    Given the panel is open
    When the explorer clicks Close
    Then the panel state is hidden

  @future
  Scenario: Summon through a running omarchy-shell
    Given Omarchy with the plugin enabled
    When the explorer calls omarchy-shell summon for the plugin id
    Then the panel is visible to AT-SPI
