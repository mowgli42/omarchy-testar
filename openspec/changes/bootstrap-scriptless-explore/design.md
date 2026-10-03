# Design: bootstrap scriptless explore

## Choice: CTRF as canonical report

Alternative considered: JUnit XML only, or Allure.

Reason: JUnit XML has no single schema and cannot carry screenshots or retries cleanly. Allure is richer but infers retries at report-build time and locks consumers to Allure. CTRF has a published JSON Schema, first-class retries, and attachments. CI still gets JUnit XML as a lossy export.

Revisit when: Open Test Reporting has non-JVM consumers we actually use. Bead: optional OTR event export.

## Choice: SARIF for findings, not for the run

Alternative considered: stuffing crashes into CTRF only.

Reason: GitHub code scanning and most security dashboards ingest SARIF 2.1. A crash or accessibility violation is a finding. A sequence is a test run. Keep them separate.

## Choice: AT-SPI / ARIA roles as the widget vocabulary

Alternative considered: a private widget schema, or TESTAR's Windows control types.

Reason: dogtail already speaks AT-SPI. Playwright snapshots speak ARIA. Mapping both onto a small role set (`button`, `text`, `dialog`, `menu item`) lets one action selector consume either source.

## Choice: fixture simulator before a live seat

Alternative considered: start on ydotool against the host.

Reason: Wayland input injection can hit the host session. TESTAR's own manual says run in a VM. The simulator proves the report contract. Live driving waits for a nested seat.

## Internal sequence log

Not an interchange standard. JSONL of `{seq, state_id, action, role, name, fatal}`. This is TESTAR's (state, action) pair, enough to replay a fixture. Do not ask other tools to parse it. Export CTRF / JUnit / SARIF instead.

## Discarded

- xdotool. X11 only.
- OrientDB. Operational weight for a graph we can keep as JSONL until replay across machines matters.
- TAP. No attachments, no duration in a useful way.
