# Source Installation

This guide deploys the source-build model in `compose.yaml`. It is statically validated against the current repository; a fresh-host deployment was not performed here because the existing PostgreSQL volume and application data must remain intact.

## Prerequisites

Use a Linux host with Docker Engine, the Docker Compose plugin, and Git installed. The host needs network access to clone the GitHub repository and obtain the Python base image, PostgreSQL image, operating-system packages, and Python dependencies used during the image build.

## Deploy

Clone the public repository and enter it:

```bash
git clone https://github.com/syawalans/docker-infrastructure-operations-platform.git
cd docker-infrastructure-operations-platform
```

Create the deployment environment file from the development example, then review it before startup:

```bash
cp .env.example .env
```

Set a deployment-appropriate PostgreSQL password and review the database name and user, application identity and host port, worker poll interval, session lifetime, login-throttle limits, and cookie Secure flags. Do not commit `.env`. For local HTTP source deployments, the example cookie flags support non-TLS access; when placing the application behind HTTPS, set both secure-cookie flags appropriately.

Build and start the services:

```bash
docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1:8088/health
```

The health command uses the example file's default application port. If the configured application port differs, use that port instead.

## First startup and Administrator creation

On a new named database volume, PostgreSQL initializes its data directory. When the web application starts, `Base.metadata.create_all()` creates missing mapped tables and the FastAPI lifespan creates missing default system settings without overwriting existing ones.

Create the first Administrator interactively after the web service is healthy:

```bash
docker compose exec web python -m app.cli.create_admin
```

The command runs inside the web container's `/workspace` working directory, where the `app` package and CLI module exist. It creates an Administrator only if no Administrator account exists, then displays a generated temporary password once. Retain it securely, log in through the published web port, and change it when prompted; the account is forced to change its password before normal navigation.

## Safe lifecycle commands

```bash
docker compose logs -f web
docker compose logs -f monitoring-worker
docker compose restart
docker compose stop
docker compose start
docker compose down
```

`docker compose down` removes containers and the Compose network but retains the named `postgres_data` volume by default. Do not use `docker compose down -v` for routine operations: removing that volume destroys persistent PostgreSQL data.

## Rebuilds and upgrades

For source changes that are compatible with the existing data model, rebuild and recreate the application services with `docker compose up -d --build`. Back up PostgreSQL and review release changes before upgrades. The current application has no schema migration framework, so arbitrary future schema changes are not automatically safe for an existing database.

Troubleshooting procedures are planned for a later document. See [Settings](10-settings.md) for configuration boundaries and [Architecture](02-architecture.md) for the deployed service layout.
