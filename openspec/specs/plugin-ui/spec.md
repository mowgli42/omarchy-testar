# plugin-ui

Test an Omarchy shell plugin by its manifest and the controls in its QML.

## Requirements

### Requirement: Validate the plugin contract

The explorer SHALL reject a plugin whose manifest is missing schemaVersion 1, uses a reserved `omarchy.` id, or points a kind at a missing entry point.

#### Scenario: Manifest is loadable
- **Tag:** Validated
- **Given** a plugin directory with schemaVersion 1 and an unreserved id
- **And** entry point files exist for each declared kind
- **When** the explorer validates the plugin
- **Then** validation produces no errors

### Requirement: Walk panel controls

The explorer SHALL treat `Accessible.name` controls as actions. Summon opens the panel. Close hides it.

#### Scenario: Bar widget summons the panel
- **Tag:** Validated
- **When** the explorer summons the plugin
- **Then** the panel state is visible

#### Scenario: Refresh updates the panel status
- **Tag:** Validated
- **When** the explorer clicks Refresh
- **Then** the status text is Checked

#### Scenario: Close hides the panel
- **Tag:** Validated
- **When** the explorer clicks Close
- **Then** the panel state is hidden

### Requirement: Live shell

The explorer SHALL drive a plugin hosted in `omarchy-shell` via summon IPC and read the resulting tree from AT-SPI.

#### Scenario: Summon through a running omarchy-shell
- **Tag:** Future
- **Given** Omarchy with the plugin enabled
- **When** the explorer calls omarchy-shell summon for the plugin id
- **Then** the panel is visible to AT-SPI
