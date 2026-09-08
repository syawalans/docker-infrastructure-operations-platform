import logging
import signal
import threading

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.monitoring_service import monitoring_service


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger(__name__)


class MonitoringWorker:
    def __init__(self):
        self._stop_event = threading.Event()

    def stop(self) -> None:
        logger.info(
            "Shutdown signal received."
        )
        self._stop_event.set()

    def run(self) -> None:
        poll_seconds = max(
            1,
            settings.MONITORING_SCHEDULER_POLL_SECONDS,
        )

        logger.info(
            "Monitoring worker started. "
            "Poll interval: %s seconds.",
            poll_seconds,
        )

        while not self._stop_event.is_set():
            self._run_cycle()

            self._stop_event.wait(
                poll_seconds
            )

        logger.info(
            "Monitoring worker stopped."
        )

    def _run_cycle(self) -> None:
        db = SessionLocal()

        try:
            result = monitoring_service.run_due_checks(
                db
            )

            if result["checked"] or result["failed"]:
                logger.info(
                    "Monitoring cycle complete: "
                    "checked=%s skipped=%s failed=%s",
                    result["checked"],
                    result["skipped"],
                    result["failed"],
                )

        except Exception:
            db.rollback()

            logger.exception(
                "Monitoring worker cycle failed."
            )

        finally:
            db.close()


worker = MonitoringWorker()


def handle_shutdown(
    signum,
    frame,
) -> None:
    worker.stop()


def main() -> None:
    signal.signal(
        signal.SIGINT,
        handle_shutdown,
    )

    signal.signal(
        signal.SIGTERM,
        handle_shutdown,
    )

    worker.run()


if __name__ == "__main__":
    main()
