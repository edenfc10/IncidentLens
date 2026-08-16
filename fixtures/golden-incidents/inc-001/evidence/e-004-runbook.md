# Payment Service Database Runbook

## Connection pool exhaustion

If database connection acquisition timeouts occur while
`db_pool_in_use` equals `db_pool_max`, investigate database
connection pool exhaustion.

Recommended checks:

1. Compare the current pool size with the previous deployment.
2. Check the number of requests waiting for a connection.
3. Confirm whether the errors began after a configuration change.

Recommended mitigation:

Restore the previous pool size or roll back the configuration change.
After mitigation, monitor the HTTP 500 rate, connection waiters, and
checkout latency.
