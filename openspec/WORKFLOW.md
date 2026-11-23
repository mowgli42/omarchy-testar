# Agent Workflow: OpenSpec + Gherkin + Beads

Follow this order unless the user explicitly requests otherwise.

## 1. Specification (OpenSpec)

- Add or change behavior under `openspec/changes/<change-id>/`:
  - `proposal.md` — why + what (include Non-goals)
  - `design.md` — architecture decisions
  - `specs/<capability>/spec.md` — `## ADDED Requirements` with **SHALL** and Gherkin scenarios
  - `tasks.md` — phased checkbox steps
  - `verification.md` — scenario → test traceability
- Mirror scenarios in `features/*.feature`
- Validate when CLI is available: `npx @fission-ai/openspec validate <change-id> --strict`

## 2. Task tracking (Beads)

- Beads live in `BEADS.md` until `bd` is initialized
- After `bd init`, create beads from change tasks and link `--spec-id openspec/specs/<capability>/spec.md`
- Work with `bd ready`, `bd update <id> --status in_progress`, `bd close <id>`

## 3. Implementation

- One bead at a time
- Do not implement a live Wayland driver inside a spec-only change

## 4. Validation

- `python3 sim/logic_audit.py --self-test`
- `python3 sim/exercise.py --self-test`
- `python3 sim/explore.py`
- `python3 sim/plugin_ui.py`
- `python3 sim/snarksentinel_click.py` and `python3 sim/snarksentinel_click.py --inject-crash`
- `python3 sim/replay.py --sequence sim/out/sequence.jsonl --app sim/fixture_app.json`
- Confirm `sim/out/logic/` and `sim/out/exercise/` reports, plus `sim/out/ctrf.json` / `sim/out/snarksentinel/`; CTRF tests must list attachments where a sequence exists
- Refresh nothing visual until a live seat exists

## 5. Archiving

- Merge change deltas into `openspec/specs/<capability>/spec.md`

## Living specs

| Capability | Spec |
|------------|------|
| Index | `openspec/specs/README.md` |
| Scriptless explore | `openspec/specs/scriptless-explore/spec.md` |
| SnarkSentinel click-all | `openspec/specs/snarksentinel-explore/spec.md` |
| Two-level checks (in flight) | `openspec/changes/add-two-level-checks/` |
