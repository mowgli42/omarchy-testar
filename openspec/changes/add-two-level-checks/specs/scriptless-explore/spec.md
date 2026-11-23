## MODIFIED Requirements

### Requirement: Explore a state graph

The explorer SHALL start from a known initial state, derive enabled actions from the current widget tree, select one action, and advance until a stopping criterion is met. Before the first click, the explorer SHALL run the logic audit and SHALL select actions only from buttons that audit associated with an action. When the accessibility gate fails, the explorer SHALL NOT click and SHALL record the walk as skipped.

#### Scenario: Happy path walk emits a sequence

- **Tag:** Validated
- **Given** a fixture app with a button that opens a second state
- **When** the explorer runs with a fixed seed and a sequence length of at least 2
- **Then** the sequence log contains a click on that button and a later state id

#### Scenario: Stopping criterion ends the walk

- **Tag:** Validated
- **Given** a sequence length of 3
- **When** the explorer runs
- **Then** the sequence log has exactly 3 actions

#### Scenario: Accessibility gate skips exploration

- **Tag:** Future
- **WHEN** the accessibility gate has failed
- **THEN** the sequence log has no actions and the walk result is skipped
