# ADDED Requirements

See the living spec at `openspec/specs/scriptless-explore/spec.md`. This change adds that capability.

### Requirement: Explore a state graph
The explorer SHALL start from a known initial state, derive enabled actions, select one, and stop at a sequence length.

#### Scenario: Happy path walk emits a sequence
- **Tag:** Validated

### Requirement: Oracle on crash
The explorer SHALL fail the run when a fatal action is taken and SHALL still write reports.

#### Scenario: Fatal action fails the run
- **Tag:** Validated

### Requirement: Report for adoption
The explorer SHALL write CTRF JSON, JUnit XML, and SARIF 2.1.

#### Scenario: Three artifacts from one run
- **Tag:** Validated
