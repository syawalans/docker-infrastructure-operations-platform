# Infrastructure Operations Platform Documentation

This documentation describes the implementation currently present in the repository. It is organized from platform purpose to implementation and technology choices; later operational documents will cover individual concerns in more depth.

## Available documentation

| Document | Focus |
| --- | --- |
| [System Overview](01-system-overview.md) | Purpose, capabilities, scope, and runtime boundaries. |
| [Architecture](02-architecture.md) | Application layers, flows, containers, deployment, and persistence. |
| [Technology Stack](03-technology-stack.md) | Current technologies and inactive repository scaffold. |
| [Networking](04-networking.md) | Container communication paths, port exposure, and monitoring connectivity. |
| [Database](05-database.md) | PostgreSQL persistence, entities, initialization, and data boundaries. |
| [Authentication and RBAC](06-authentication-rbac.md) | Identity, sessions, passwords, roles, and permissions. |
| [Security](07-security.md) | Implemented application and container controls and their boundaries. |

## Status

The seven documents above are complete. The following are planned and are not yet documentation deliverables: monitoring, reporting, settings, source installation, pre-built-image installation, configuration, backup and restore, operations, failure testing, troubleshooting, and development.

Existing legacy files in this directory are outside this documentation phase and have not been revised.
