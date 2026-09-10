from dataclasses import dataclass
from datetime import datetime, time, timezone


class ReportDateValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ReportDateRange:
    date_from: str
    date_to: str
    parsed_date_from: datetime | None
    parsed_date_to: datetime | None
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.error is None


class ReportDateService:
    DATE_FORMAT = "%Y-%m-%d"

    def parse(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> ReportDateRange:
        normalized_from = (date_from or "").strip()
        normalized_to = (date_to or "").strip()

        parsed_from = self._parse_date(
            normalized_from,
            is_end=False,
        )
        if normalized_from and parsed_from is None:
            return ReportDateRange(
                date_from=normalized_from,
                date_to=normalized_to,
                parsed_date_from=None,
                parsed_date_to=None,
                error=(
                    "Invalid start date. "
                    "Use YYYY-MM-DD format."
                ),
            )

        parsed_to = self._parse_date(
            normalized_to,
            is_end=True,
        )
        if normalized_to and parsed_to is None:
            return ReportDateRange(
                date_from=normalized_from,
                date_to=normalized_to,
                parsed_date_from=parsed_from,
                parsed_date_to=None,
                error=(
                    "Invalid end date. "
                    "Use YYYY-MM-DD format."
                ),
            )

        if (
            parsed_from is not None
            and parsed_to is not None
            and parsed_from.date() > parsed_to.date()
        ):
            return ReportDateRange(
                date_from=normalized_from,
                date_to=normalized_to,
                parsed_date_from=parsed_from,
                parsed_date_to=parsed_to,
                error=(
                    "Start date cannot be after end date."
                ),
            )

        return ReportDateRange(
            date_from=normalized_from,
            date_to=normalized_to,
            parsed_date_from=parsed_from,
            parsed_date_to=parsed_to,
        )

    def require_valid(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> ReportDateRange:
        result = self.parse(
            date_from,
            date_to,
        )

        if not result.is_valid:
            raise ReportDateValidationError(
                result.error
                or "Invalid reporting date range."
            )

        return result

    def _parse_date(
        self,
        value: str,
        *,
        is_end: bool,
    ) -> datetime | None:
        if not value:
            return None

        try:
            parsed = datetime.strptime(
                value,
                self.DATE_FORMAT,
            ).date()
        except ValueError:
            return None

        return datetime.combine(
            parsed,
            time.max if is_end else time.min,
            tzinfo=timezone.utc,
        )


report_date_service = ReportDateService()
