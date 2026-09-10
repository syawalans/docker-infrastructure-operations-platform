# Technology Stack

## Current runtime technologies

| Area | Technology | Responsibility |
| --- | --- | --- |
| Language and image base | Python 3.12 / `python:3.12-slim` | Application and worker runtime. |
| Web application | FastAPI | Routes, dependencies, middleware, and HTTP responses. |
| ASGI server | Uvicorn | Serves the FastAPI web process on port 8088. |
| Presentation | Jinja2, HTML, CSS | Server-rendered portal and static styling. |
| Data access | SQLAlchemy | ORM mappings, sessions, and repository queries. |
| Database and driver | PostgreSQL 17 / `psycopg[binary]` | Persistent relational storage and PostgreSQL connectivity. |
| Form parsing | `python-multipart` | HTML form handling by FastAPI. |
| Password security | `pwdlib[argon2]` | Password hashing and verification using the recommended pwdlib configuration with Argon2 support. |
| Reports | ReportLab | Executive PDF generation; CSV output uses Python standard-library facilities. |
| Monitoring | Python standard library plus `iputils-ping` | TCP sockets, HTTP(S) requests, and ICMP checks from the worker container. |

The application has no separate browser-side framework: Jinja2 renders pages on the server, and the repository's frontend assets are HTML templates and CSS.

## Development and deployment technologies

| Area | Technology | Use in this repository |
| --- | --- | --- |
| Containers | Docker | Packages the shared application image defined by `app/Dockerfile`. |
| Service orchestration | Docker Compose | Defines PostgreSQL, the web service, and the monitoring worker. |
| Persistence | Docker named volume | `postgres_data` retains PostgreSQL data across container replacement. |
| Networking | Docker Compose default bridge network | Lets services address PostgreSQL as `postgres`; only the web port is generally exposed. |
| Configuration | Environment variables and `python-dotenv` | Supplies deployment and local-development values; example files document the expected keys. |
| Source control | Git | Tracks repository history. |
| Source hosting | GitHub | Intended repository hosting platform. |
| Image registry | Docker Hub | Intended registry for the pre-built-image deployment model. |

`compose.yaml` builds the image from source for development. `compose.production.yaml` references a pre-built image supplied through environment configuration. Docker Hub publishing is planned; no published image name is established by the repository.

The web startup hook uses the settings registry to create missing default application settings without overwriting existing values.

## Present but not active

- `nginx/nginx.conf` is an empty scaffold. No Nginx container, reverse proxy, or TLS termination is configured by Compose.
- The project has no active Redis, Celery, message broker, Prometheus, Grafana, Kubernetes, React, Node.js, or JavaScript build tooling.
- SQLAlchemy metadata creation is used for missing tables at web startup; Alembic or another schema-migration tool is not included.

For how these components are arranged, see [Architecture](02-architecture.md). For the capability and scope boundary, see [System Overview](01-system-overview.md).
