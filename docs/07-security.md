# Security

## Application controls

| Control | Current implementation |
| --- | --- |
| Password storage | `pwdlib` recommended hashing with Argon2 support; password policy is enforced for user password changes. |
| Session storage | Random URL-safe session tokens are SHA-256 hashed before storage in PostgreSQL; raw tokens are returned only in the session cookie. |
| Session cookie | `HttpOnly`, `SameSite=Lax`, path `/`, configured lifetime, and environment-controlled `Secure` flag. |
| CSRF | Middleware creates an HTTP-only CSRF cookie and validates unsafe requests against a form field or `X-CSRF-Token` header using constant-time comparison. |
| Login throttling | Per-client-host failure window and block duration, protected by an in-process lock; throttled requests return HTTP 429 with `Retry-After`. |
| Authorization | Database-backed users and route-level role permissions through FastAPI dependencies. |
| Audit trail | Authentication and administrative actions are recorded in `audit_logs`; sensitive detail keys are removed before persistence. |

The CSRF middleware treats GET, HEAD, and OPTIONS as safe. For unsafe requests it accepts a token in the configured form field for URL-encoded forms or in the `X-CSRF-Token` header. Cookie `Secure` settings are environment driven: the production Compose defaults enable both session and CSRF secure flags, while source-build defaults support local HTTP development.

## Container and deployment controls

`app/Dockerfile` runs the application as the non-root `appuser`. In both Compose models, web and worker containers are configured with `no-new-privileges`, drop all capabilities, use a read-only filesystem, and provide `/tmp` as `tmpfs`. The monitoring worker alone adds `NET_RAW`, because ICMP checks invoke `ping`; this is a deliberate exception to the capability drop.

The source-build database port is bound only to `127.0.0.1`. The production Compose definition does not publish PostgreSQL to a host port. The web service is still published on its configured application port, and neither Compose model includes a reverse proxy or TLS termination. Health checks verify PostgreSQL readiness and the web `/health` endpoint, but they do not provide an external security boundary.

Application and deployment configuration is environment driven. Environment files are excluded from image build context and should carry deployment-specific values; the repository provides examples rather than operational secrets. The project does not implement an application secrets manager.

## Boundaries and limitations

- Login throttling is in-process: it is not persistent or shared across replicas.
- There is no MFA, SSO, external IAM, WAF, Redis, distributed session store, or cache layer.
- No reverse proxy, TLS termination, certificate management, or host firewall policy is included.
- Monitoring targets and outbound probe traffic are configured by application users; target-level network policy is external to this repository.
- SQLAlchemy `create_all` creates missing tables, but no schema migration framework is present. Operational schema changes need a separately managed migration and backup process.
- Audit sanitization removes a defined set of sensitive dictionary keys; it is not a general data-classification or secrets-management system.

For identity and permission behavior, see [Authentication and RBAC](06-authentication-rbac.md). For database and port exposure, see [Database](05-database.md) and [Networking](04-networking.md).
