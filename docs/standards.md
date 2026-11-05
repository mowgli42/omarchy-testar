# Report and spec formats

Picked for adoption, not for elegance. A private sequence log will not get into GitHub Actions, GitLab, or code scanning.

## Use

| Format | Role | Why it helps adoption |
|--------|------|------------------------|
| Gherkin | Human spec and future runner | Already the repo standard. Tags split Validated from Future. |
| CTRF JSON | Canonical test-run report | Published JSON Schema. Attachments, retries, flaky flag. Language-agnostic. |
| JUnit XML | CI compatibility export | Jenkins, GitHub Actions, GitLab, Buildkite all ingest it. No official schema. Treat as lossy. |
| SARIF 2.1 | Oracle findings | OASIS standard. GitHub code scanning uploads it directly. |
| Cucumber Messages | Deferred | Preferred machine format once a Gherkin runner exists. ndjson envelopes. Do not invent a second Gherkin JSON. |
| Open Test Reporting | Deferred | JUnit team's event XML, real schema. Still mostly JVM. Revisit when a consumer we use reads it. |

## Do not adopt as primary

- **Allure results.** Rich steps and attachments, but retries are inferred at report build and the ecosystem is Allure-specific.
- **TAP 13/14.** Prose spec, no attachments, weak on duration and retries.
- **TRX.** Visual Studio only. No public schema.
- **TESTAR OrientDB graph.** Internal model, not an interchange format.
- **GUITAR event-flow graphs.** Useful research idea for action derivation. Not a format other tools read.

## Widget vocabulary

Not a separate standard. Map state-source nodes onto a small set of WAI-ARIA / AT-SPI roles (`button`, `text`, `dialog`, `menu item`, `link`). `sim/atspi.py` performs that map for fixture trees and optional live pyatspi. Playwright snapshots (deferred) and dogtail then feed one selector.

## Internal only

`sequence.jsonl`: `{seq, state_id, action, role, name, fatal}`. Replay for the fixture. Not a published schema. Consumers should read CTRF, JUnit XML, or SARIF.

## Emit order

1. Walk and write `sequence.jsonl`
2. Write CTRF (source of truth for pass/fail, duration, attachment paths)
3. Derive JUnit XML from the CTRF result (one testcase per run, failure message from the oracle)
4. Derive SARIF only when an oracle fires (crash, hang, accessibility violation)
