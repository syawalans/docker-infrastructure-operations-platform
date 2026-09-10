# Authentication and RBAC

## Identity and login

Users are stored in `users`. Login accepts a username or email address, normalizes it in the repository, and rejects unknown or inactive users. `pwdlib`'s recommended password hasher is used with the Argon2 extra. The password policy requires at least 12 characters with lowercase, uppercase, numeric, and configured special-character content.

On successful authentication, the service generates a random URL-safe session token, stores only its SHA-256 hash in `user_sessions`, and sends the raw token in the `infrastructure_ops_session` cookie. The cookie is HTTP-only, `SameSite=Lax`, scoped to `/`, and has a lifetime based on `AUTH_SESSION_LIFETIME_HOURS`. Its `Secure` flag is controlled by `AUTH_COOKIE_SECURE`.

For each protected request, middleware resolves the cookie token through its stored hash and rejects missing, revoked, expired, or inactive-user sessions. It redirects unauthenticated requests to `/login`; permission dependencies return 401 or 403 when invoked without a suitable user. Logout revokes the matching stored session and deletes the browser cookie.

## Password and account lifecycle

New and reset accounts receive generated temporary passwords and set `must_change_password=True`. Successful login directs those users to `/change-password`, and protected middleware prevents normal navigation until the password is changed or the user logs out. A successful password change validates the policy, revokes all of the user's sessions, creates one replacement session, and clears the forced-change flag.

Administrators create, edit, activate or deactivate users, and reset passwords through `/users`. Deactivation revokes the user's active sessions. An administrator cannot deactivate their own account or remove their own Administrator role, and cannot reset their own password through the administrative reset route. The interactive `app/cli/create_admin.py` utility creates the initial Administrator only when no Administrator account exists; it prints a generated temporary password once for the operator to retain.

## Roles and permissions

Roles and permissions are defined in `app/core/constants.py`; the following matrix is derived directly from `ROLE_PERMISSIONS`.

| Permission | Administrator | Operator | Viewer |
| --- | :---: | :---: | :---: |
| `dashboard:view` | Yes | Yes | Yes |
| `asset:view` | Yes | Yes | Yes |
| `asset:create` | Yes | Yes | No |
| `asset:edit` | Yes | Yes | No |
| `asset:delete` | Yes | No | No |
| `monitoring:view` | Yes | Yes | Yes |
| `monitoring:configure` | Yes | Yes | No |
| `monitoring:run_check` | Yes | Yes | No |
| `report:view` | Yes | Yes | Yes |
| `settings:view` | Yes | No | No |
| `settings:edit` | Yes | No | No |
| `user:manage` | Yes | No | No |

`require_permission()` is used as a FastAPI dependency on protected routes for dashboard, assets, monitoring, reports, settings, and users. This is the authorization control; template helpers merely use the same permission mapping to hide or show applicable controls. UI visibility does not grant access to a route.

## Relevant boundaries

The platform implements local database-backed identities only. It has no MFA, SSO, external IAM integration, directory synchronization, or distributed session/cache layer. Login throttling is keyed by `request.client.host` in process memory, so it is not shared between replicas and resets on process restart. CSRF protection is described in [Security](07-security.md); database storage and constraints are described in [Database](05-database.md).
