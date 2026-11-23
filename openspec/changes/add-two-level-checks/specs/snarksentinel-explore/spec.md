## MODIFIED Requirements

### Requirement: Click-everything coverage policy

The explorer SHALL select unvisited enabled buttons that the logic audit associated with an action until each such button has been clicked once. It SHALL NOT click a button that has no associated action. It SHALL NOT use a recorded script of button names.

#### Scenario: Coverage walk clicks each reachable button once

- **Tag:** Validated
- **Given** the SnarkSentinel fixture app
- **When** the explorer runs with the click-all policy
- **Then** the sequence log contains exactly one click per reachable button name
- **And** the walk stops when no unvisited enabled buttons remain

#### Scenario: Button without an action is left unclicked

- **Tag:** Future
- **WHEN** the SnarkSentinel surface has an enabled button with no action and other buttons with actions
- **THEN** the sequence log omits the button that has no action and still clicks the associated buttons
