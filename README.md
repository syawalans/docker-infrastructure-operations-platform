# Infrastructure Operations Platform

**Current release:** v0.1.0 · **Image platform:** linux/amd64 · **License:** [MIT](LICENSE)

Infrastructure Operations Platform is a technical portfolio project for managing infrastructure assets, running independent availability checks, reviewing operational results, producing reports, and administering access through a server-rendered web application.

## Feature overview

| Area | Implemented capabilities |
| --- | --- |
| Assets | Server, network device, virtual machine, and storage inventory with RBAC-controlled add, edit, and delete actions. |
| Monitoring | Configurable ICMP, TCP, HTTP, and HTTPS checks, executed by a dedicated worker with persisted results. |
| Reporting | Dashboard views, asset, monitoring, and audit CSV exports, plus an executive PDF report. |
| Access control | Authentication, database-backed sessions, forced first-login password change, CSRF protection, login throttling, audit logging, and Administrator, Operator, and Viewer roles. |
| Operations | PostgreSQL persistence, application settings, Docker Compose deployment, and a published production image. |

## Architecture overview

```text
Browser
   |
   v
Web / FastAPI
   |
   +---- PostgreSQL (persistent state)
   |
Monitoring Worker
   |
   +---- Infrastructure monitoring targets
```

The web service and monitoring worker use the same application image; Docker Compose supplies a different command to each service. PostgreSQL holds application state, while the worker performs monitoring checks independently of web requests.

## Technology stack

| Layer | Technologies |
| --- | --- |
| Backend | Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2, Jinja2 |
| Database | PostgreSQL 17 |
| Frontend | Server-rendered Jinja2 templates, HTML, CSS |
| Security | pwdlib with Argon2, CSRF protection, database-backed sessions, login throttling, RBAC, audit logging |
| Reporting | ReportLab and CSV exports |
| Infrastructure | Docker and Docker Compose |

## Quick start: pre-built image

The recommended deployment pulls the published image; the application image is not built on the target host.

Clone the repository and create the production environment file:

```bash
git clone https://github.com/syawalans/docker-infrastructure-operations-platform.git
cd docker-infrastructure-operations-platform
cp .env.production.example .env.production
```

Review and edit `.env.production` before deployment. Set an appropriate PostgreSQL password, retain `DOCKER_IMAGE=syawalans/infrastructure-operations-platform`, and use the immutable release tag `IMAGE_TAG=0.1.0` for controlled deployments.

Pull and start the production stack:

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  pull

docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  up -d

docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  ps
```

Verify the application health on the configured host port (the production example defaults to `8088`):

```bash
curl http://127.0.0.1:8088/health
```

For all production operations, consistently use `--env-file .env.production -f compose.production.yaml`; plain `docker compose` commands select the default Compose configuration instead.

### HTTP and HTTPS cookies

For deployments behind HTTPS, keep the production defaults enabled:

```dotenv
AUTH_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
```

For local or lab HTTP testing only, set both values to `false`. Secure cookies must remain enabled for actual HTTPS production deployments.

### Initial Administrator

When the web service is healthy, create the first Administrator interactively:

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  exec web python -m app.cli.create_admin
```

The command generates a temporary password and requires the Administrator to change it on first login.

## Source-build alternative

For a source-build deployment using `compose.yaml`, see the [Source Installation guide](docs/11-source-installation.md). The [Pre-built Image Installation guide](docs/12-prebuilt-image-installation.md) contains the full image-based procedure, routine operations, upgrades, and data-persistence guidance.

## Security model

The Compose deployment runs the application container as a non-root user with a read-only application filesystem, dropped Linux capabilities, and `no-new-privileges`. The monitoring worker has the narrow `NET_RAW` capability exception required for ICMP checks. Application controls include Argon2 password hashing, CSRF protection, login throttling, database-backed sessions, RBAC, and audit logs. PostgreSQL is not published to a host port in the production Compose configuration.

## RBAC summary

The platform provides three roles:

| Role | Scope |
| --- | --- |
| Administrator | User administration, settings, and full operational access. |
| Operator | Operational access to infrastructure assets, monitoring, and reports within assigned permissions. |
| Viewer | Read-only access to permitted operational information. |

See [Authentication and RBAC](docs/06-authentication-rbac.md) for the implemented permission model.

## Monitoring and reports

The dedicated worker processes scheduled ICMP, TCP, HTTP, and HTTPS monitoring configurations and persists results for the web application and reports. Reporting includes asset, monitoring, and audit CSV exports plus an executive PDF report.

See [Monitoring](docs/08-monitoring.md) and [Reporting](docs/09-reporting.md) for operational details.

## Configuration

Runtime configuration is supplied through environment files. The production deployment uses `.env.production` with `compose.production.yaml`; review image tag, PostgreSQL, application port, monitoring, session, throttling, and cookie settings before startup. Do not commit environment files containing deployment credentials.

## Documentation

The complete documentation index is in [docs/README.md](docs/README.md). Key references include:

- [System Overview](docs/01-system-overview.md)
- [Architecture](docs/02-architecture.md)
- [Authentication and RBAC](docs/06-authentication-rbac.md)
- [Security](docs/07-security.md)
- [Monitoring](docs/08-monitoring.md)
- [Reporting](docs/09-reporting.md)
- [Source Installation](docs/11-source-installation.md)
- [Pre-built Image Installation](docs/12-prebuilt-image-installation.md)

## Release information

Current release: **v0.1.0**.

```bash
docker pull syawalans/infrastructure-operations-platform:0.1.0
```

The `latest` tag is also published for convenience. Prefer a version-pinned image tag for controlled deployments.

## Known limitations and roadmap

- The application has no formal database migration framework yet; SQLAlchemy `Base.metadata.create_all` currently provides schema bootstrap.
- Deployment is currently a single-node Docker Compose model.
- The monitoring worker does not yet expose a dedicated health or heartbeat endpoint.
- The public image is currently validated for linux/amd64.
- HTTPS/TLS termination for production is expected to be provided externally.

## License

This project is licensed under the [MIT License](LICENSE). Copyright © 2026 Achmad Nur Syawaluddin.
