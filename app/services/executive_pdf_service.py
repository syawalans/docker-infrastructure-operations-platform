from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class ExecutivePDFService:
    PAGE_WIDTH = landscape(A4)[0]

    def __init__(self) -> None:
        styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            "ExecutiveTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=3,
        )

        self.subtitle_style = ParagraphStyle(
            "ExecutiveSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=9,
        )

        self.section_style = ParagraphStyle(
            "ExecutiveSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=5,
            spaceAfter=5,
        )

        self.body_style = ParagraphStyle(
            "ExecutiveBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155"),
        )

        self.small_style = ParagraphStyle(
            "ExecutiveSmall",
            parent=self.body_style,
            fontSize=6.8,
            leading=8.5,
            textColor=colors.HexColor("#475569"),
        )

        self.metric_label_style = ParagraphStyle(
            "MetricLabel",
            parent=self.small_style,
            fontSize=6.5,
            leading=8,
            textColor=colors.HexColor("#64748b"),
        )

        self.metric_value_style = ParagraphStyle(
            "MetricValue",
            parent=self.body_style,
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
        )

        self.card_title_style = ParagraphStyle(
            "CardTitle",
            parent=self.body_style,
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#0f172a"),
        )

        self.finding_title_style = ParagraphStyle(
            "FindingTitle",
            parent=self.body_style,
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#0f172a"),
        )

        self.table_header_style = ParagraphStyle(
            "TableHeader",
            parent=self.small_style,
            fontName="Helvetica-Bold",
            fontSize=6.1,
            leading=7.2,
            textColor=colors.HexColor("#0f172a"),
        )

        self.table_cell_style = ParagraphStyle(
            "TableCell",
            parent=self.small_style,
            fontSize=6.1,
            leading=7.4,
            textColor=colors.HexColor("#334155"),
        )

    @staticmethod
    def _safe(value) -> str:
        if value is None or value == "":
            return "-"
        return str(value)

    @staticmethod
    def _format_period(period: dict) -> str:
        date_from = period.get("date_from")
        date_to = period.get("date_to")

        if date_from or date_to:
            return (
                f"{date_from or 'Beginning'} - "
                f"{date_to or 'Present'}"
            )

        return "All Available Data"

    @staticmethod
    def _format_percentage(value) -> str:
        if value is None:
            return "-"
        return f"{value:.2f}%"

    @staticmethod
    def _format_response_time(value) -> str:
        if value is None:
            return "-"
        return f"{value:.2f} ms"

    @staticmethod
    def _status_colors(status: str):
        status = status.upper()

        if status == "HEALTHY":
            return (
                colors.HexColor("#dcfce7"),
                colors.HexColor("#166534"),
            )

        if status == "ATTENTION":
            return (
                colors.HexColor("#fee2e2"),
                colors.HexColor("#991b1b"),
            )

        return (
            colors.HexColor("#fef3c7"),
            colors.HexColor("#92400e"),
        )

    @staticmethod
    def _compact_distribution(
        items: list[dict],
        *,
        limit: int = 5,
    ) -> list[dict]:
        if len(items) <= limit:
            return items

        visible = items[:limit]
        remaining = sum(
            item["count"]
            for item in items[limit:]
        )

        return visible + [
            {
                "label": "Others",
                "count": remaining,
            }
        ]

    def _metric_cell(self, label: str, value):
        return [
            Paragraph(
                label,
                self.metric_label_style,
            ),
            Spacer(1, 1.5),
            Paragraph(
                self._safe(value),
                self.metric_value_style,
            ),
        ]

    def _metric_table(
        self,
        metrics: list[tuple[str, object]],
        *,
        columns: int = 4,
    ) -> Table:
        rows = []

        for index in range(
            0,
            len(metrics),
            columns,
        ):
            row = [
                self._metric_cell(label, value)
                for label, value
                in metrics[index:index + columns]
            ]

            while len(row) < columns:
                row.append("")

            rows.append(row)

        width = 172 * mm / columns

        table = Table(
            rows,
            colWidths=[width] * columns,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.white,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#dbe3ee"),
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#e2e8f0"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        return table

    def _report_metadata(
        self,
        data: dict,
        generated_by: str,
    ) -> Table:
        background, foreground = (
            self._status_colors(
                data["overall_status"]
            )
        )

        table = Table(
            [
                [
                    Paragraph(
                        "<b>Reporting Period</b><br/>"
                        + self._format_period(
                            data["reporting_period"]
                        ),
                        self.body_style,
                    ),
                    Paragraph(
                        "<b>Generated At</b><br/>"
                        + data["generated_at"].strftime(
                            "%Y-%m-%d %H:%M:%S UTC"
                        ),
                        self.body_style,
                    ),
                    Paragraph(
                        "<b>Generated By</b><br/>"
                        + self._safe(generated_by),
                        self.body_style,
                    ),
                    Paragraph(
                        "<b>Overall Status</b><br/>"
                        + data["overall_status"],
                        self.body_style,
                    ),
                ]
            ],
            colWidths=[43 * mm] * 4,
        )

        style = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.HexColor("#f8fafc"),
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.45,
                colors.HexColor("#dbe3ee"),
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor("#e2e8f0"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "BACKGROUND",
                (3, 0),
                (3, 0),
                background,
            ),
            (
                "TEXTCOLOR",
                (3, 0),
                (3, 0),
                foreground,
            ),
        ]

        table.setStyle(
            TableStyle(style)
        )

        return table

    def _distribution_table(
        self,
        distribution: dict,
    ) -> Table:
        groups = [
            ("Asset Type", "asset_type"),
            ("Environment", "environment"),
            ("Operational Status", "status"),
            ("Location", "location"),
        ]

        cards = []

        for title, key in groups:
            items = self._compact_distribution(
                distribution.get(key, [])
            )

            content = [
                Paragraph(
                    title,
                    self.card_title_style,
                ),
                Spacer(1, 3),
            ]

            if not items:
                content.append(
                    Paragraph(
                        "No data",
                        self.small_style,
                    )
                )
            else:
                rows = []

                for item in items:
                    rows.append(
                        [
                            Paragraph(
                                self._safe(
                                    item["label"]
                                ),
                                self.small_style,
                            ),
                            Paragraph(
                                str(item["count"]),
                                self.card_title_style,
                            ),
                        ]
                    )

                inner = Table(
                    rows,
                    colWidths=[
                        31 * mm,
                        7 * mm,
                    ],
                )

                inner.setStyle(
                    TableStyle(
                        [
                            (
                                "VALIGN",
                                (0, 0),
                                (-1, -1),
                                "TOP",
                            ),
                            (
                                "ALIGN",
                                (1, 0),
                                (1, -1),
                                "RIGHT",
                            ),
                            (
                                "TOPPADDING",
                                (0, 0),
                                (-1, -1),
                                2,
                            ),
                            (
                                "BOTTOMPADDING",
                                (0, 0),
                                (-1, -1),
                                2,
                            ),
                            (
                                "LEFTPADDING",
                                (0, 0),
                                (-1, -1),
                                0,
                            ),
                            (
                                "RIGHTPADDING",
                                (0, 0),
                                (-1, -1),
                                0,
                            ),
                        ]
                    )
                )

                content.append(inner)

            cards.append(content)

        table = Table(
            [cards],
            colWidths=[43 * mm] * 4,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#dbe3ee"),
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#e2e8f0"),
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.white,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        return table

    def _affected_assets_block(
        self,
        affected: dict,
    ):
        groups = [
            (
                "Monitoring DOWN",
                affected["monitoring_down"],
            ),
            (
                "Monitoring UNKNOWN",
                affected["monitoring_unknown"],
            ),
            (
                "Under Maintenance",
                affected["maintenance"],
            ),
            (
                "Inactive",
                affected["inactive"],
            ),
        ]

        total = sum(
            len(items)
            for _, items in groups
        )

        if total == 0:
            table = Table(
                [
                    [
                        Paragraph(
                            "<b>No assets currently "
                            "require operational attention."
                            "</b><br/>"
                            "No inactive, maintenance, "
                            "DOWN, or UNKNOWN conditions "
                            "are currently detected.",
                            self.body_style,
                        )
                    ]
                ],
                colWidths=[172 * mm],
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            colors.HexColor("#f0fdf4"),
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#bbf7d0"),
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),
                    ]
                )
            )

            return table

        rows = [
            [
                Paragraph(
                    "Condition",
                    self.table_header_style,
                ),
                Paragraph(
                    "Affected Assets",
                    self.table_header_style,
                ),
            ]
        ]

        for label, items in groups:
            if not items:
                continue

            visible = items[:6]

            asset_text = []

            for item in visible:
                hostname = self._safe(
                    item.get("hostname")
                )

                detail = (
                    item.get("ip_address")
                    or item.get("target")
                    or item.get("environment")
                    or ""
                )

                if detail:
                    asset_text.append(
                        f"{hostname} ({detail})"
                    )
                else:
                    asset_text.append(hostname)

            if len(items) > 6:
                asset_text.append(
                    f"+{len(items) - 6} more"
                )

            rows.append(
                [
                    Paragraph(
                        label,
                        self.table_cell_style,
                    ),
                    Paragraph(
                        "<br/>".join(asset_text),
                        self.table_cell_style,
                    ),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                42 * mm,
                130 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#f1f5f9"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#dbe3ee"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        return table

    def _audit_table(
        self,
        summary: dict,
        categories: dict,
    ) -> Table:
        metrics = [
            (
                "Successful Events",
                summary["success_events"],
            ),
            (
                "Failed Events",
                summary["failure_events"],
            ),
            (
                "Blocked Events",
                summary["blocked_events"],
            ),
            (
                "Authentication",
                categories["authentication"],
            ),
            (
                "Asset Changes",
                categories["assets"],
            ),
            (
                "Monitoring Changes",
                categories["monitoring"],
            ),
            (
                "User Administration",
                categories["users"],
            ),
        ]

        return self._metric_table(
            metrics,
            columns=4,
        )

    def _findings_table(
        self,
        findings: list[dict],
    ) -> Table:
        rows = [
            [
                Paragraph(
                    "Severity",
                    self.table_header_style,
                ),
                Paragraph(
                    "Scope",
                    self.table_header_style,
                ),
                Paragraph(
                    "Category",
                    self.table_header_style,
                ),
                Paragraph(
                    "Finding",
                    self.table_header_style,
                ),
                Paragraph(
                    "Count",
                    self.table_header_style,
                ),
            ]
        ]

        for finding in findings:
            affected = finding.get(
                "affected_assets",
                [],
            )

            affected_text = ""

            if affected:
                names = [
                    self._safe(
                        item.get("hostname")
                    )
                    for item in affected[:5]
                ]

                if len(affected) > 5:
                    names.append(
                        f"+{len(affected) - 5} more"
                    )

                affected_text = (
                    "<br/><font color='#64748b'>"
                    "Affected: "
                    + ", ".join(names)
                    + "</font>"
                )

            rows.append(
                [
                    Paragraph(
                        self._safe(
                            finding["severity"]
                        ),
                        self.table_cell_style,
                    ),
                    Paragraph(
                        self._safe(
                            finding["scope"]
                        ),
                        self.table_cell_style,
                    ),
                    Paragraph(
                        self._safe(
                            finding["category"]
                        ),
                        self.table_cell_style,
                    ),
                    Paragraph(
                        self._safe(
                            finding["title"]
                        )
                        + affected_text,
                        self.finding_title_style,
                    ),
                    Paragraph(
                        str(finding["value"]),
                        self.table_cell_style,
                    ),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                20 * mm,
                22 * mm,
                26 * mm,
                92 * mm,
                12 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#f1f5f9"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#dbe3ee"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "ALIGN",
                        (-1, 1),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        return table

    def _management_summary_block(
        self,
        data: dict,
    ):
        management = data["management_summary"]

        background, foreground = (
            self._status_colors(
                management["status"]
            )
        )

        header = Table(
            [
                [
                    Paragraph(
                        "Overall Infrastructure Status",
                        self.metric_label_style,
                    ),
                    Paragraph(
                        management["status"],
                        self.metric_value_style,
                    ),
                ]
            ],
            colWidths=[
                125 * mm,
                47 * mm,
            ],
        )

        header.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, 0),
                        colors.HexColor("#f8fafc"),
                    ),
                    (
                        "BACKGROUND",
                        (1, 0),
                        (1, 0),
                        background,
                    ),
                    (
                        "TEXTCOLOR",
                        (1, 0),
                        (1, 0),
                        foreground,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#dbe3ee"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        attention = [
            Paragraph(
                "<b>Management Attention</b>",
                self.body_style,
            )
        ]

        for item in management[
            "attention_items"
        ]:
            attention.append(
                Paragraph(
                    "- " + item,
                    self.body_style,
                )
            )

        return KeepTogether(
            [
                header,
                Spacer(1, 5),
                Paragraph(
                    management["statement"],
                    self.body_style,
                ),
                Spacer(1, 5),
                *attention,
            ]
        )

    def _appendix_table(
        self,
        assets: list,
    ) -> Table:
        headers = [
            "Hostname",
            "Name",
            "Type",
            "IP Address",
            "Vendor / Model",
            "Operating System",
            "Environment",
            "Location",
            "Status",
        ]

        rows = [
            [
                Paragraph(
                    value,
                    self.table_header_style,
                )
                for value in headers
            ]
        ]

        for asset in assets:
            vendor_model = " / ".join(
                value
                for value in [
                    asset.vendor,
                    asset.model,
                ]
                if value
            )

            values = [
                asset.hostname,
                asset.name,
                asset.asset_type,
                asset.ip_address,
                vendor_model,
                asset.operating_system,
                asset.environment,
                asset.location,
                asset.status,
            ]

            rows.append(
                [
                    Paragraph(
                        self._safe(value),
                        self.table_cell_style,
                    )
                    for value in values
                ]
            )

        if len(rows) == 1:
            rows.append(
                [
                    Paragraph(
                        "No assets available.",
                        self.table_cell_style,
                    )
                ]
                + [""] * 8
            )

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[
                27 * mm,
                27 * mm,
                19 * mm,
                24 * mm,
                37 * mm,
                31 * mm,
                25 * mm,
                28 * mm,
                20 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#e2e8f0"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.3,
                        colors.HexColor("#dbe3ee"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        3.5,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        3.5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        return table

    @staticmethod
    def _page_footer(canvas, doc):
        canvas.saveState()

        canvas.setStrokeColor(
            colors.HexColor("#dbe3ee")
        )
        canvas.setLineWidth(0.35)

        canvas.line(
            15 * mm,
            12 * mm,
            doc.pagesize[0] - 15 * mm,
            12 * mm,
        )

        canvas.setFont(
            "Helvetica",
            6.8,
        )

        canvas.setFillColor(
            colors.HexColor("#64748b")
        )

        canvas.drawString(
            15 * mm,
            7 * mm,
            "Infrastructure Operations Platform",
        )

        canvas.drawRightString(
            doc.pagesize[0] - 15 * mm,
            7 * mm,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    def generate_pdf(
        self,
        data: dict,
        *,
        generated_by: str,
    ) -> tuple[bytes, str]:
        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=13 * mm,
            bottomMargin=18 * mm,
            title=(
                "Infrastructure Operations "
                "Executive Report"
            ),
            author=generated_by,
        )

        summary = data["executive_summary"]

        story = [
            Paragraph(
                "Infrastructure Operations "
                "Executive Report",
                self.title_style,
            ),
            Paragraph(
                (
                    "High-level infrastructure "
                    "operations, availability, "
                    "and security assessment."
                ),
                self.subtitle_style,
            ),
            self._report_metadata(
                data,
                generated_by,
            ),
            Spacer(1, 7),

            Paragraph(
                "1. Executive Summary",
                self.section_style,
            ),
            self._metric_table(
                [
                    (
                        "Total Assets",
                        summary["total_assets"],
                    ),
                    (
                        "Active Assets",
                        summary["active_assets"],
                    ),
                    (
                        "Monitored Assets",
                        summary["total_monitored"],
                    ),
                    (
                        "Current UP",
                        summary["monitoring_up"],
                    ),
                    (
                        "Current DOWN",
                        summary["monitoring_down"],
                    ),
                    (
                        "Current UNKNOWN",
                        summary["monitoring_unknown"],
                    ),
                    (
                        "Availability",
                        self._format_percentage(
                            summary[
                                "availability_percent"
                            ]
                        ),
                    ),
                    (
                        "Audit Events",
                        summary[
                            "total_audit_events"
                        ],
                    ),
                ]
            ),
            Spacer(1, 6),

            Paragraph(
                "2. Infrastructure Asset Overview",
                self.section_style,
            ),
            self._distribution_table(
                data["asset_overview"][
                    "distribution"
                ]
            ),
            Spacer(1, 6),

            Paragraph(
                "3. Assets Requiring Attention",
                self.section_style,
            ),
            self._affected_assets_block(
                data["affected_assets"]
            ),

            PageBreak(),

            Paragraph(
                "4. Monitoring & Availability",
                self.section_style,
            ),
            self._metric_table(
                [
                    (
                        "Total Checks",
                        summary[
                            "total_monitoring_checks"
                        ],
                    ),
                    (
                        "Successful",
                        summary[
                            "successful_monitoring_checks"
                        ],
                    ),
                    (
                        "Failed",
                        summary[
                            "failed_monitoring_checks"
                        ],
                    ),
                    (
                        "Average Response",
                        self._format_response_time(
                            summary[
                                "average_response_time_ms"
                            ]
                        ),
                    ),
                    (
                        "Availability",
                        self._format_percentage(
                            summary[
                                "availability_percent"
                            ]
                        ),
                    ),
                    (
                        "Current UP",
                        summary["monitoring_up"],
                    ),
                    (
                        "Current DOWN",
                        summary["monitoring_down"],
                    ),
                    (
                        "Current UNKNOWN",
                        summary[
                            "monitoring_unknown"
                        ],
                    ),
                ]
            ),
            Spacer(1, 6),

            Paragraph(
                "5. Security & Audit Activity",
                self.section_style,
            ),
            self._audit_table(
                data["audit_overview"][
                    "summary"
                ],
                data["audit_overview"][
                    "categories"
                ],
            ),
            Spacer(1, 6),

            Paragraph(
                "6. Key Findings",
                self.section_style,
            ),
            self._findings_table(
                data["findings"]
            ),
            Spacer(1, 6),

            Paragraph(
                "7. Management Summary",
                self.section_style,
            ),
            self._management_summary_block(
                data
            ),

            PageBreak(),

            Paragraph(
                "Appendix A - Asset Inventory",
                self.section_style,
            ),
            Paragraph(
                (
                    "Current infrastructure assets "
                    "included in this report. "
                    "Table headers repeat automatically "
                    "when the inventory spans multiple "
                    "pages."
                ),
                self.subtitle_style,
            ),
            self._appendix_table(
                data["asset_overview"]["assets"]
            ),
        ]

        document.build(
            story,
            onFirstPage=self._page_footer,
            onLaterPages=self._page_footer,
        )

        content = buffer.getvalue()
        buffer.close()

        date_from = (
            data["reporting_period"].get(
                "date_from"
            )
        )

        date_to = (
            data["reporting_period"].get(
                "date_to"
            )
        )

        if date_from or date_to:
            filename = (
                "Infrastructure_Operations_"
                "Executive_Report_"
                f"{date_from or 'beginning'}"
                "_to_"
                f"{date_to or 'present'}"
                ".pdf"
            )
        else:
            today = datetime.now(
                timezone.utc
            ).strftime("%Y-%m-%d")

            filename = (
                "Infrastructure_Operations_"
                "Executive_Report_"
                f"{today}.pdf"
            )

        return content, filename


executive_pdf_service = ExecutivePDFService()
