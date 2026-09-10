# Pre-built Image Installation

This guide deploys the released application image with `compose.production.yaml`. It is intended for production-style deployments where the target host pulls a published image instead of building the application locally.

## Deployment model

GitHub provides the deployment configuration and Docker Hub provides the pre-built application image. Production Compose uses `${DOCKER_IMAGE}:${IMAGE_TAG:-latest}` for both `web` and `monitoring-worker`, and uses `postgres:17` for PostgreSQL. The application image is pulled on the target host; it is not built there.

## Requirements

Use a Linux host with Docker Engine, the Docker Compose plugin, Git, and network access to GitHub, Docker Hub, and the PostgreSQL image registry. Plan persistent storage, backups, and HTTPS termination before a production deployment.

## Docker image and release information

The validated Docker Hub repository is `syawalans/infrastructure-operations-platform`. Release `0.1.0` is the validated immutable image tag for `linux/amd64`; it is associated with digest `sha256:6717884608f9bd3a1ba8420f2b92e4f392634d6711308c6a7c8334021edc8db1` and source revision `137d2fbb995137a0cc25ce6aad7d76cfb0e275ae`.

Pin `IMAGE_TAG=0.1.0` for a controlled deployment. The `latest` tag is also published as a convenience moving tag and should not be used when repeatability is required.

## Obtain deployment files

Clone the repository and enter it:

```bash
git clone https://github.com/syawalans/docker-infrastructure-operations-platform.git
cd docker-infrastructure-operations-platform
```

Create the production environment file:

```bash
cp .env.production.example .env.production
```

Review `.env.production` and set deployment-appropriate PostgreSQL values. Do not commit this file. Keep the provided Docker image repository and pin the release tag unless intentionally upgrading.

## HTTP and HTTPS cookie configuration

For real production deployments behind HTTPS, keep these production defaults enabled:

```dotenv
AUTH_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
```

Secure cookies do not work over plain HTTP. For an HTTP-only lab or test environment only, set both values to `false`; restore them to `true` for an actual HTTPS production deployment.

## Production Compose command rule

Run production and pre-built-image operations in the production Compose context. Always include both the environment file and production Compose file, including for `config`, `pull`, `up`, `down`, `ps`, `logs`, `exec`, and `restart`:

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  config --quiet
```

Running plain `docker compose` commands uses the default Compose configuration instead. This is an operational command-context issue, so retain the two production options on every command below.

## Validate configuration and pull images

Validate the resolved configuration, then pull the released application image and PostgreSQL image:

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  config --quiet

docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  pull
```

The expected application image is `syawalans/infrastructure-operations-platform:0.1.0` when using the recommended tag.

## Start the stack

Start the pulled services:

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  up -d
```

PostgreSQL is internal to the Compose network and is not published to a host port. The web service publishes port `8088` by default; use the configured `APP_PORT` if it differs.

## Verify service status

Check that PostgreSQL and the web service are healthy and that the monitoring worker is running:

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  ps
```

## Verify health and login endpoints

Use GET requests to verify the application from the host:

```bash
curl -fsS http://127.0.0.1:8088/health
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8088/login
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8088/
```

The health endpoint reports the application health and production identity. The login-page request should return `200`. An unauthenticated request to `/` should return `303` and redirect to `/login`. The login check must use GET rather than HEAD because `/login` accepts GET only.

## Verify database bootstrap

On a fresh named database volume, startup creates the seven mapped application tables and initializes seven default rows in `system_settings`. Default initialization is idempotent: existing values are not overwritten, and missing defaults are created without duplicate category and setting-key pairs.

## Create the initial Administrator

After the web service is healthy, create the first Administrator interactively:

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  exec web python -m app.cli.create_admin
```

The command creates an active Administrator with a temporary password and requires a password change on first login. Retain the generated temporary password securely.

## First login and password change

Open the published application URL, sign in with the temporary Administrator credentials, and complete the required password change. Normal Dashboard access becomes available after the password has been changed.

## Routine production operations

Use the production Compose context for routine status, logs, and restarts:

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  logs -f web

docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  logs -f monitoring-worker

docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  restart
```

## Upgrade or redeploy

Before an upgrade, back up PostgreSQL and review the release notes. Then update `IMAGE_TAG` in `.env.production`, pull the selected image, recreate the services, and verify `ps` and `/health`:

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

The application currently uses SQLAlchemy `Base.metadata.create_all` and has no formal database migration framework. A future release with schema changes must provide an explicit migration procedure before it can be safely applied to an existing production database.

## Safe shutdown and data persistence

To remove the running containers and Compose network while preserving the named PostgreSQL volume, run:

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  down
```

Do not use `down -v` for routine operations: it also removes the named PostgreSQL volume and deletes persistent database data. Use it only when intentionally resetting a disposable fresh test environment.

## Troubleshooting notes

If the web service is not healthy, inspect its logs with the production Compose command context and confirm PostgreSQL is healthy first. If login fails in an HTTP-only lab, verify that both Secure cookie values are set to `false` only for that test environment. For HTTPS production, both values must remain `true`.

## Validation status

This pre-built-image procedure was validated on a separate clean Linux host using image tag `0.1.0`. The pulled production stack had healthy PostgreSQL and web services, a running monitoring worker, healthy HTTP endpoints, a fresh database with seven mapped tables and seven default settings, and a successful initial Administrator and forced-password-change flow.
