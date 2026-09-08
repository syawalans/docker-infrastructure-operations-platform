import logging
import threading

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.monitoring_service import monitoring_service


logger = logging.getLogger(__name__)


class MonitoringScheduler:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if not settings.MONITORING_SCHEDULER_ENABLED:
            logger.info(
                "Monitoring scheduler is disabled."
            )
            return

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run_loop,
            name="monitoring-scheduler",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "Monitoring scheduler started."
        )

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(
                timeout=10,
            )

        logger.info(
            "Monitoring scheduler stopped."
        )

    def _run_loop(self) -> None:
        poll_seconds = max(
            1,
            settings.MONITORING_SCHEDULER_POLL_SECONDS,
        )

        while not self._stop_event.is_set():
            self._run_cycle()

            self._stop_event.wait(
                poll_seconds
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
                "Monitoring scheduler cycle failed."
            )

        finally:
            db.close()


monitoring_scheduler = MonitoringScheduler()
