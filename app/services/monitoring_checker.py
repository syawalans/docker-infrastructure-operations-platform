import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class CheckResult:
    status: str
    response_time_ms: float | None
    error_message: str | None


class MonitoringChecker:
    def run(
        self,
        *,
        check_type: str,
        target: str,
        port: int | None,
        http_path: str | None,
        timeout_seconds: int,
    ) -> CheckResult:
        check_type = check_type.upper()

        if check_type == "ICMP":
            return self._check_icmp(
                target=target,
                timeout_seconds=timeout_seconds,
            )

        if check_type == "TCP":
            return self._check_tcp(
                target=target,
                port=port,
                timeout_seconds=timeout_seconds,
            )

        if check_type in {"HTTP", "HTTPS"}:
            return self._check_http(
                scheme=check_type.lower(),
                target=target,
                port=port,
                http_path=http_path,
                timeout_seconds=timeout_seconds,
            )

        return CheckResult(
            status="UNKNOWN",
            response_time_ms=None,
            error_message=f"Unsupported check type: {check_type}",
        )

    def _check_icmp(
        self,
        *,
        target: str,
        timeout_seconds: int,
    ) -> CheckResult:
        started = time.perf_counter()

        try:
            process = subprocess.run(
                [
                    "ping",
                    "-c",
                    "1",
                    "-W",
                    str(timeout_seconds),
                    target,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout_seconds + 1,
                check=False,
            )

            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000

            if process.returncode == 0:
                return CheckResult(
                    status="UP",
                    response_time_ms=elapsed_ms,
                    error_message=None,
                )

            return CheckResult(
                status="DOWN",
                response_time_ms=None,
                error_message="ICMP ping failed.",
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                status="DOWN",
                response_time_ms=None,
                error_message="ICMP check timed out.",
            )

        except FileNotFoundError:
            return CheckResult(
                status="UNKNOWN",
                response_time_ms=None,
                error_message="System ping command is not available.",
            )

        except Exception as exc:
            return CheckResult(
                status="UNKNOWN",
                response_time_ms=None,
                error_message=str(exc),
            )

    def _check_tcp(
        self,
        *,
        target: str,
        port: int | None,
        timeout_seconds: int,
    ) -> CheckResult:
        if port is None:
            return CheckResult(
                status="UNKNOWN",
                response_time_ms=None,
                error_message="TCP check requires a port.",
            )

        started = time.perf_counter()

        try:
            with socket.create_connection(
                (target, port),
                timeout=timeout_seconds,
            ):
                elapsed_ms = (
                    time.perf_counter() - started
                ) * 1000

                return CheckResult(
                    status="UP",
                    response_time_ms=elapsed_ms,
                    error_message=None,
                )

        except (socket.timeout, TimeoutError):
            return CheckResult(
                status="DOWN",
                response_time_ms=None,
                error_message="TCP connection timed out.",
            )

        except OSError as exc:
            return CheckResult(
                status="DOWN",
                response_time_ms=None,
                error_message=str(exc),
            )

        except Exception as exc:
            return CheckResult(
                status="UNKNOWN",
                response_time_ms=None,
                error_message=str(exc),
            )

    def _check_http(
        self,
        *,
        scheme: str,
        target: str,
        port: int | None,
        http_path: str | None,
        timeout_seconds: int,
    ) -> CheckResult:
        path = http_path or "/"

        if not path.startswith("/"):
            path = f"/{path}"

        default_port = (
            443
            if scheme == "https"
            else 80
        )

        selected_port = port or default_port

        if selected_port == default_port:
            url = f"{scheme}://{target}{path}"
        else:
            url = (
                f"{scheme}://{target}:"
                f"{selected_port}{path}"
            )

        started = time.perf_counter()

        try:
            request = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "User-Agent": "Infrastructure-Ops-Monitor/1.0",
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=timeout_seconds,
            ) as response:
                elapsed_ms = (
                    time.perf_counter() - started
                ) * 1000

                status_code = response.getcode()

                if 200 <= status_code < 400:
                    return CheckResult(
                        status="UP",
                        response_time_ms=elapsed_ms,
                        error_message=None,
                    )

                return CheckResult(
                    status="DOWN",
                    response_time_ms=elapsed_ms,
                    error_message=(
                        f"HTTP status code: {status_code}"
                    ),
                )

        except urllib.error.HTTPError as exc:
            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000

            return CheckResult(
                status="DOWN",
                response_time_ms=elapsed_ms,
                error_message=(
                    f"HTTP status code: {exc.code}"
                ),
            )

        except (
            urllib.error.URLError,
            TimeoutError,
            socket.timeout,
        ) as exc:
            return CheckResult(
                status="DOWN",
                response_time_ms=None,
                error_message=str(exc),
            )

        except Exception as exc:
            return CheckResult(
                status="UNKNOWN",
                response_time_ms=None,
                error_message=str(exc),
            )


monitoring_checker = MonitoringChecker()
