import math
import time
from collections import deque
from threading import Lock

from app.core.config import settings


class LoginThrottle:
    def __init__(self) -> None:
        self._attempts: dict[
            str,
            deque[float],
        ] = {}

        self._blocked_until: dict[
            str,
            float,
        ] = {}

        self._lock = Lock()

    def _prune_attempts(
        self,
        client_key: str,
        now: float,
    ) -> None:
        attempts = self._attempts.get(
            client_key
        )

        if attempts is None:
            return

        cutoff = (
            now
            - settings.AUTH_LOGIN_WINDOW_SECONDS
        )

        while (
            attempts
            and attempts[0] <= cutoff
        ):
            attempts.popleft()

        if not attempts:
            self._attempts.pop(
                client_key,
                None,
            )

    def get_retry_after(
        self,
        client_key: str,
    ) -> int:
        now = time.monotonic()

        with self._lock:
            blocked_until = (
                self._blocked_until.get(
                    client_key
                )
            )

            if blocked_until is None:
                return 0

            if blocked_until <= now:
                self._blocked_until.pop(
                    client_key,
                    None,
                )

                self._attempts.pop(
                    client_key,
                    None,
                )

                return 0

            return max(
                1,
                math.ceil(
                    blocked_until - now
                ),
            )

    def record_failure(
        self,
        client_key: str,
    ) -> int:
        now = time.monotonic()

        with self._lock:
            blocked_until = (
                self._blocked_until.get(
                    client_key
                )
            )

            if (
                blocked_until is not None
                and blocked_until > now
            ):
                return max(
                    1,
                    math.ceil(
                        blocked_until - now
                    ),
                )

            if blocked_until is not None:
                self._blocked_until.pop(
                    client_key,
                    None,
                )

            self._prune_attempts(
                client_key,
                now,
            )

            attempts = self._attempts.setdefault(
                client_key,
                deque(),
            )

            attempts.append(now)

            if (
                len(attempts)
                < settings.AUTH_LOGIN_MAX_ATTEMPTS
            ):
                return 0

            blocked_until = (
                now
                + settings.AUTH_LOGIN_BLOCK_SECONDS
            )

            self._blocked_until[
                client_key
            ] = blocked_until

            attempts.clear()

            return settings.AUTH_LOGIN_BLOCK_SECONDS

    def reset(
        self,
        client_key: str,
    ) -> None:
        with self._lock:
            self._attempts.pop(
                client_key,
                None,
            )

            self._blocked_until.pop(
                client_key,
                None,
            )


login_throttle = LoginThrottle()
