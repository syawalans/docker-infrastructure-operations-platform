# System Overview

## Purpose

Infrastructure Operations Platform is a containerized, server-rendered web application for maintaining an infrastructure inventory and observing configured infrastructure checks. It brings asset records, monitoring results, operational reports, user administration, audit records, and selected application preferences into one authenticated portal.

Its objectives are to centralize basic infrastructure information, make recent health-check results visible, preserve operational history, and constrain administrative actions through role-based access control.

## Current capabilities

- Asset inventory: create, view, search, filter, edit, and—where permitted—delete records for servers, virtual machines, network devices, storage, and other assets.
- Monitoring: associate one configuration with an asset and perform ICMP, TCP, HTTP, or HTTPS checks on a schedule or on demand. Results include status, timestamp, response time when available, and an error message when applicable.
- Reporting: provide asset, monitoring, audit-activity, and executive views; export CSV reports and generate an executive PDF.
- Access management: authenticate database-backed users, maintain database-backed sessions, enforce Administrator, Operator, and Viewer permissions, require password changes for temporary passwords, and support administrator-managed users and password resets.
- Safeguards and records: protect unsafe requests with CSRF validation, apply an in-process login throttle, and record authentication and administrative activity in audit logs.
- Settings: expose editable general, monitoring-default, and reporting-preference settings, plus read-only runtime security and system-information status in the application UI.

## Runtime components

The active Docker Compose deployment has three services:

- **Web**: the FastAPI application served by Uvicorn, rendering Jinja2 templates and static CSS.
- **Monitoring worker**: a separate process using the same application image and codebase to run due checks and persist results.
- **PostgreSQL**: the relational database for application data.

PostgreSQL data is held in the `postgres_data` named volume. The services communicate on Compose's default bridge network; the web service is the application entry point, while PostgreSQL is bound to loopback only in the source-build Compose file.

## Deployment models

`compose.yaml` is the source-build/development model: it builds `app/Dockerfile`, tags a local application image, and runs the web and worker services from it.

`compose.production.yaml` is the pre-built-image model: it expects an image reference through environment configuration and runs the same web, worker, and PostgreSQL topology. A Docker Hub-oriented production example exists, but image publishing and a concrete Docker Hub image name are not present in this repository.

## Current scope and boundaries

The application is a single FastAPI service with a companion monitoring process, not a distributed operations platform. It has no active Redis, message broker, task queue, Prometheus, Grafana, Kubernetes, React or Node.js frontend, or reverse-proxy deployment. `nginx/nginx.conf` is empty and no Nginx service is defined in either Compose file.

Monitoring is limited to the four built-in probe types and database-stored results. Login throttling is process-local, so its state is not shared between application processes or persisted. Schema creation uses SQLAlchemy metadata creation at web application import, and an idempotent web-startup hook creates any missing default system settings. No migration framework is configured.

For implementation details, see [Architecture](02-architecture.md). For dependency and platform choices, see [Technology Stack](03-technology-stack.md).
