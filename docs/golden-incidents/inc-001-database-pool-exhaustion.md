# INC-001: Payment Service Database Pool Exhaustion

## Incident Summary

- Incident ID: INC-001
- Service: payment-service
- Environment: production
- Severity: SEV-1
- Status: Resolved
- Started at: 2026-08-15T09:03:00Z
- Resolved at: 2026-08-15T09:18:00Z

Three minutes after deploying payment-service version 2.4.1,
checkout requests began returning HTTP 500 responses.

## User Question

What is the most likely cause of the payment-service failures?

## Ground-Truth Root Cause

The deployment reduced DB_POOL_SIZE from 40 to 5.

Under production traffic, all five database connections became
occupied. New checkout requests timed out while waiting for an
available connection, causing payment-service to return HTTP 500.

## Evidence

### E-001: Deployment Configuration

- Source type: deployment
- Observed at: 2026-08-15T09:00:00Z
- Relevant: yes

Payment-service version 2.4.1 was deployed.

Configuration change:

DB_POOL_SIZE: 40 -> 5

### E-002: Application Logs

- Source type: log
- Observed at: 2026-08-15T09:03:12Z
- Relevant: yes

Checkout requests failed with:

DatabaseConnectionTimeout:
Timed out while waiting for an available database connection.

### E-003: Database Pool Metrics

- Source type: metric
- Observed at: 2026-08-15T09:03:20Z
- Relevant: yes

- db_pool_max: 5
- db_pool_in_use: 5
- db_pool_waiters: 37

### E-004: Payment Service Runbook

- Source type: runbook
- Relevant: yes

The runbook states that connection acquisition timeouts combined
with db_pool_in_use equaling db_pool_max indicate database
connection pool exhaustion.

Recommended mitigation:

Restore the previous pool size or roll back the configuration change.

### E-005: Earlier Stripe Rate-Limit Warning

- Source type: log
- Observed at: 2026-08-15T08:20:00Z
- Relevant: no
- Purpose: distractor

Stripe briefly returned HTTP 429 responses.

The warning ended at 08:23, forty minutes before the current
incident began.

## Expected Answer

The payment-service failures were caused by database connection
pool exhaustion after DB_POOL_SIZE was reduced from 40 to 5 in
deployment version 2.4.1.

All five available connections were occupied, and new checkout
requests timed out while waiting for a connection.

## Required Citations

The answer should cite:

- E-001 for the configuration change.
- E-002 for the connection timeout.
- E-003 for pool saturation.
- E-004 for the operational interpretation and mitigation.

The answer must not use E-005 as the root cause.

## Expected Remediation

Restore DB_POOL_SIZE to 40 or roll back the deployment configuration.

After the rollback, monitor:

- HTTP 500 error rate.
- Database connection pool utilization.
- Database connection waiters.
- Checkout request latency.

## Success Criteria

A successful investigation must:

1. Identify database connection pool exhaustion as the root cause.
2. Connect the failure to the DB_POOL_SIZE change.
3. Cite the relevant evidence.
4. Ignore the unrelated Stripe warning.
5. Avoid introducing facts that are not present in the evidence.