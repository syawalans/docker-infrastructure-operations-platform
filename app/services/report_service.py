from sqlalchemy.orm import Session

from app.repositories.report_repository import (
    report_repository,
)


class ReportService:
    def get_overview(
        self,
        db: Session,
    ) -> dict:
        return {
            "asset_summary": (
                report_repository.get_asset_summary(
                    db
                )
            ),
        }

    def get_asset_inventory_report(
        self,
        db: Session,
    ) -> dict:
        return {
            "summary": (
                report_repository.get_asset_summary(
                    db
                )
            ),
            "assets": (
                report_repository.get_asset_inventory(
                    db
                )
            ),
        }


report_service = ReportService()
