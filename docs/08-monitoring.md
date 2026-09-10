# Monitoring

## Configuration model

Monitoring is configured against an existing asset. A configuration stores its check type, target, optional port and HTTP path, interval, timeout, and enabled state in `monitoring_configs`. Saving through `/monitoring/assets/{asset_id}/configure` creates a configuration when none is found for the asset or updates the currently selected configuration. Removing it deletes the configuration and its results through the configured cascade.

Supported types are `ICMP`, `TCP`, `HTTP`, and `HTTPS`:

| Type | Behavior |
| --- | --- |
| ICMP | Runs `ping -c 1` with the configured timeout. Port and HTTP path are cleared. |
| TCP | Opens a socket to the target and required port. The HTTP path is cleared. |
| HTTP | Sends a GET request to the target and path; a missing port defaults to 80. |
| HTTPS | Sends a GET request to the target and path; a missing port defaults to 443. |

For HTTP(S), a missing path becomes `/`, and a path without a leading slash is normalized. HTTP status codes from 200 through 399 are `UP`; HTTP errors and connectivity failures are `DOWN`. TCP connection errors and timeouts are `DOWN`; unexpected errors are `UNKNOWN`. ICMP uses the process result to determine `UP` or `DOWN`, with unavailable tooling or unexpected errors reported as `UNKNOWN`.

Configuration validation requires a port from 1 through 65535 where supplied, an interval of at least 10 seconds, and a timeout from 1 through 60 seconds. Enabled configurations participate in scheduled checks; a disabled configuration cannot be run manually.

## Scheduling and execution

Three values have distinct purposes:

| Value | Source | Purpose |
| --- | --- | --- |
| Worker poll interval | `MONITORING_SCHEDULER_POLL_SECONDS` | How often the worker scans enabled configurations; it is clamped to at least one second. |
| Check interval | Per-configuration `interval_seconds` | How long after the latest result a configuration becomes due. |
| Check timeout | Per-configuration `timeout_seconds` | Network-operation timeout supplied to the probe implementation. |

`monitoring-worker` runs `app.workers.monitoring_worker` in a loop. For each enabled configuration, it reads the latest result. A configuration with no result is due immediately; otherwise it is due when `checked_at + interval_seconds` is reached. Individual check exceptions roll back that check's session work and increment the worker failure count without stopping the worker loop.

Each attempt produces a `monitoring_results` row containing the copied probe details, status, check time, optional response time, and optional error message. The overview shows `UNKNOWN` for unconfigured assets or configurations without a result. An authorized user can use Run Check to invoke the same check service synchronously; it also persists a result and audit event.

## Access and deployment boundary

`monitoring:view` permits the overview; `monitoring:configure` permits configuration and removal; `monitoring:run_check` permits manual checks. Administrators and Operators have all three permissions; Viewers have view only.

The worker performs network probes from its own container. The image provides `ping`, and the worker receives `NET_RAW` while the web container does not. Targets must therefore be reachable from the worker's Docker network environment. No monitoring agents, SNMP, Prometheus, Grafana, alert notifications, distributed workers, or external scheduling service are implemented.

The database settings `default_check_type`, `default_interval_seconds`, and `default_timeout_seconds` prefill the monitoring form for a new configuration. They do not replace a saved configuration's values. See [Settings](10-settings.md) for their administration and [Networking](04-networking.md) for connectivity implications.
