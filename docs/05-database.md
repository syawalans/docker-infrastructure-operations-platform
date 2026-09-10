# Database

## Platform use

PostgreSQL 17 is the persistent store for application records. SQLAlchemy provides the ORM engine and sessions; `psycopg[binary]` is the PostgreSQL driver. `app/core/database.py` loads the database URL from the environment and constructs an engine with `pool_pre_ping=True`, plus a `SessionLocal` factory with `autocommit=False` and `autoflush=False`.

In Compose, web and worker containers receive an internal connection URL using the `postgres` service name. The source-build definition additionally publishes PostgreSQL on loopback for host-local development; the production definition does not publish a database port. Neither documentation nor source includes real credentials.

## Persistence and initialization

The Compose volume `postgres_data` is mounted at PostgreSQL's data directory, so database data survives replacement of the PostgreSQL container while that named volume is retained.

`app/main.py` imports the mapped models and calls `Base.metadata.create_all(bind=engine)` before constructing the FastAPI application. On web startup, its lifespan function opens a database session and calls `SettingsService.initialize_defaults()`. The initializer creates only missing entries from `DEFAULT_SYSTEM_SETTINGS`; existing entries are left unchanged.

This supports a fresh deployment by creating mapped tables and bootstrapping default system settings. It is not a schema migration mechanism. The repository has no Alembic configuration or other migration framework, so changes to existing schemas require an explicit future migration approach. The initial Administrator is created separately through `python -m app.cli.create_admin`.

## Current entities

| Table / model | Responsibility and verified relationships |
| --- | --- |
| `assets` / `AssetModel` | Infrastructure inventory. `hostname` is unique; key classification and status fields are indexed. |
| `users` / `UserModel` | User identity, password hash, role, activity state, password-change state, and timestamps. Username and email are unique. |
| `user_sessions` / `UserSessionModel` | Hashes of session tokens, expiry, revocation, and activity timestamps. Each row references a user; user deletion cascades to sessions. |
| `monitoring_configs` / `MonitoringConfigModel` | Per-asset monitoring configuration, probe details, schedule, timeout, and enabled state. It references `assets`; asset deletion cascades. |
| `monitoring_results` / `MonitoringResultModel` | Historical probe outcomes, timings, target metadata, and error text. It references both an asset and a configuration; configuration deletion cascades to its results. |
| `audit_logs` / `AuditLogModel` | Timestamped security and operational events, actor identifiers, request IP, status, and optional PostgreSQL JSONB details. A deleted user sets `actor_user_id` to null. |
| `system_settings` / `SystemSettingModel` | Typed application preferences and metadata. The `(category, setting_key)` pair has a database uniqueness constraint; `updated_by` references a user and is set to null if that user is deleted. |

Repositories contain the database operations, while services coordinate validation and domain behavior. Authentication sessions, monitoring history, audit logs, and UI-managed settings are all database-backed; they are not stored in the web process.

## Operational boundary

Database backup, restore, retention, access provisioning, and disaster recovery procedures are not defined here and belong in a later operations document. Before any schema evolution beyond new-table creation, a migration and backup strategy should be established.

See [Architecture](02-architecture.md) for layer interaction and [Networking](04-networking.md) for connectivity and exposure.
