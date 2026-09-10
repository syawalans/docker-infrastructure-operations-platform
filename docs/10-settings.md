# Settings

## Configuration boundary

The Settings page separates database-backed application preferences from deployment configuration read from the process environment. Administrators alone have both `settings:view` and `settings:edit`; the routes enforce these permissions independently of which controls are visible in the template.

Database settings are rows in `system_settings`, with string, integer, or boolean value types, an editable flag, timestamps, and an optional updating user. The database enforces uniqueness for `(category, setting_key)`. The FastAPI lifespan calls `SettingsService.initialize_defaults()` after mapped-table creation: it inserts only missing definitions from `DEFAULT_SYSTEM_SETTINGS` and never overwrites an existing value.

| Category | Keys | Validation and use |
| --- | --- | --- |
| General | `platform_display_name`, `organization_name`, `timezone` | Display name is required and length-limited; organization name is length-limited; timezone must be one of the registry's supported values. |
| Monitoring | `default_check_type`, `default_interval_seconds`, `default_timeout_seconds` | Check type must be supported; default interval is 10–86400 seconds; timeout is 1–60 seconds and shorter than the interval. These values prefill new monitoring forms. |
| Reporting | `default_reporting_period_days` | Allowed values are all data (`0`) or 7, 30, 90, 180, or 365 days. It resolves report periods when no explicit period is supplied. |

Updates preserve the row's declared value type and reject non-editable settings. Settings changes are audit logged. UI-managed settings do not rewrite environment variables or Compose configuration.

## Environment and deployment configuration

`app/core/config.py` reads environment values once when the process starts. Compose passes the relevant variables to web and worker services; `.env.example` and `.env.production.example` describe the expected names without providing deployment secrets.

| Category | Relevant values |
| --- | --- |
| Application | `APP_NAME`, `APP_VERSION`, `APP_ENV`; `APP_PORT` controls Compose web-port publishing. |
| PostgreSQL | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `DATABASE_URL`. Compose constructs the application connection URL using the internal `postgres` hostname. |
| Monitoring worker | `MONITORING_SCHEDULER_POLL_SECONDS`. |
| Sessions and login protection | `AUTH_SESSION_LIFETIME_HOURS`, `AUTH_LOGIN_MAX_ATTEMPTS`, `AUTH_LOGIN_WINDOW_SECONDS`, `AUTH_LOGIN_BLOCK_SECONDS`. |
| Cookie transport | `AUTH_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`. |
| Pre-built-image deployment | `DOCKER_IMAGE` and `IMAGE_TAG` in the production Compose model. |

Changing environment-derived values requires recreating or restarting the affected process so its settings object is constructed again; no dynamic reload mechanism exists. The production Compose defaults enable secure cookie flags, while source-build defaults support local HTTP development.

## Read-only status

The Settings page also displays environment-derived security values and system information without editing controls: application version and environment, Python runtime, database query status, and worker state with its latest monitoring activity. Worker state is inferred from enabled configurations and persisted result timestamps; it is not a direct container-health query.

For deployment configuration, see [Source Installation](11-source-installation.md). For the security implications of environment values, see [Security](07-security.md).
