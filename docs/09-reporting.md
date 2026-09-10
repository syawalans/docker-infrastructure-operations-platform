# Reporting

## Available reports

All report routes require `report:view`, which is available to Administrator, Operator, and Viewer roles. `/reports` is a landing page with an unfiltered asset summary and links to the following on-demand reports.

| Report | Source data and behavior |
| --- | --- |
| Asset Inventory | `assets`, with text, type, environment, status, and location filters plus aggregate asset status counts. |
| Monitoring | Enabled monitoring configurations, their latest results for current status, and filtered historical `monitoring_results` for performance and recent history. |
| Audit Activity | `audit_logs`, filterable by actor, action, resource type, status, and date range. |
| Executive Infrastructure Report | Combines asset inventory, current monitoring state, date-filtered monitoring performance, audit activity, derived findings, and a management summary. |

The report pages use Jinja2 templates. CSV exports are available for asset inventory, monitoring history, and audit activity. The executive view has a PDF download generated with ReportLab; it is generated for the request and returned as a response rather than stored by the application.

## Periods and dates

Monitoring, audit, and executive routes resolve a reporting period from explicit `date_from` and `date_to` parameters, `period=all`, or the database setting `reporting.default_reporting_period_days`. When a default period is used, its end date is calculated in the configured general timezone and its inclusive start date is calculated from the number of days. A zero-day preference resolves to all available data.

Dates must use `YYYY-MM-DD`; start dates are interpreted at the beginning of the UTC day and end dates at the end of the UTC day. Invalid format or an end date before the start date produces an error response. Explicit dates take precedence over the `period` parameter. The monitoring page's current-status items come from the latest result, while its history and performance calculations use the requested date range.

## Exports

CSV responses use `text/csv; charset=utf-8`, include a UTF-8 BOM, and have a UTC-date filename:

- `Asset_Inventory_YYYY-MM-DD.csv`
- `Monitoring_Report_YYYY-MM-DD.csv`
- `Audit_Activity_YYYY-MM-DD.csv`

Before writing a CSV field, the export service prefixes a single quote to values beginning with `=`, `+`, `-`, or `@`, reducing spreadsheet formula-injection risk. The executive PDF filename includes its requested date range, or the current UTC date when no date range is selected.

## Current limits

Reporting has no scheduler, email delivery, persistent report storage, external BI integration, dashboard product, or Excel-native export. Its results reflect data available in PostgreSQL at request time and do not establish retention, archival, or distribution policy.

See [Settings](10-settings.md) for the reporting-period preference and [Database](05-database.md) for report source entities.
