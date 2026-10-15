# Reports, Dashboard and Stats: behaviour specification (Mautic 7.x)

Every item states an observable outcome and its source. Code citations are relative to the repo root at 7.2.1
(commit 419a08a9b35). "R" items cover Reports, "D" items the Dashboard, and "S" items StatsBundle.

## Contents
1. Report definition and lifecycle (R1–R14)
2. Visibility and permissions (R15–R22)
3. Query building (R23–R33)
4. Filters and operators (R34–R44)
5. Dates, relative dates and timezones (R45–R53)
6. Running and displaying a Report (R54–R63)
7. Export from the UI (R64–R71)
8. Scheduled Reports (R72–R86)
9. Reports REST API (R87–R92)
10. Dependencies on other entities (R93)
11. Dashboard (D1–D18)
12. Charts (C1–C3)
13. StatsBundle (S1–S4)
14. Open questions and contradictions

## 1. Report definition and lifecycle
R1. A Report stores `source` (context), `columns`, `filters`, `table_order`, `graphs`, `group_by`, `aggregators` (PHP-serialized arrays), and `settings` (JSON: `showGraphsAboveTable`, `showDynamicFilters`, `hideDateRangeFilter`). It also stores schedule fields `is_scheduled`, `schedule_unit`, `to_address`, `schedule_day`, `schedule_month_frequency`, plus `uuid` [code: app/bundles/ReportBundle/Entity/Report.php:167-217 @7.x].
R2. `name` is required. `toAddress` must be a valid list of emails. The class constraint `ScheduleIsValid` validates the schedule [code: app/bundles/ReportBundle/Entity/Report.php:220-227 @7.x].
R3. The Details tab offers Name, Data source, Description, Published, Visible for all logged-in users, Owner, and the Dynamic filters settings "Opened by default" and "Hide date range" [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data-sources].
R4. The source select lists every context from `REPORT_ON_BUILD` for context `all`, grouped by `group`. Columns, filters, aggregators, order and graphs are rebuilt on `PRE_SET_DATA`/`PRE_SUBMIT` for the selected source. A new Report defaults to the first source [code: app/bundles/ReportBundle/Form/Type/ReportType.php:34-126,128-312,380-397 @7.x].
R5. Columns with the same alias in different tables get numeric suffixes (`email`, `email1`, …). Labels are translated, and columns and filters are sorted by label with `strnatcmp` [code: app/bundles/ReportBundle/Model/ReportModel.php:239-270 @7.x] [code: app/bundles/ReportBundle/Event/ReportBuilderEvent.php:62-86 @7.x].
R6. Group-by choices exclude `unsubscribed`, `unsubscribed_ratio` and `unique_ratio` [code: app/bundles/ReportBundle/Model/ReportModel.php:299-301 @7.x].
R7. On edit, columns and graphs are emptied before binding so the submitted order is kept, and restored if the form is invalid. A successful save clears the per-Report session order keys [code: app/bundles/ReportBundle/Controller/ReportController.php:330-331,342-343,372-375,386-388 @7.x].
R8. Saving dispatches `REPORT_PRE_SAVE`/`REPORT_POST_SAVE`. Post-save writes an audit-log entry (`bundle=report, object=report, action=create|update`, with the change set) and re-plans the scheduler. Delete writes `action=delete` [code: app/bundles/ReportBundle/Model/ReportModel.php:145-180 @7.x] [code: app/bundles/ReportBundle/EventListener/ReportSubscriber.php:32-63 @7.x] [code: app/bundles/ReportBundle/Scheduler/EventListener/ReportSchedulerSubscriber.php:17-27 @7.x].
R9. Clone creates an unpublished copy (`id = null`) and requires `create` plus view access [code: app/bundles/ReportBundle/Controller/ReportController.php:137-158 @7.x].
R10. The list defaults to `r.dateModified DESC`; the repository default is `r.name ASC`. Search commands: `is:published`, `is:unpublished`, `is:mine`, `is:scheduled` [code: app/bundles/ReportBundle/Controller/ReportController.php:76-77 @7.x] [code: app/bundles/ReportBundle/Entity/ReportRepository.php:46-101 @7.x].
R11. The description is HTML-cleaned (`CleanFormSubscriber(['description' => 'html'])`) and rendered unescaped [code: app/bundles/ReportBundle/Form/Type/ReportType.php:36 @7.x].
R12. The `system` flag (UI label "Visible for all logged-in users") is stored and shown in the form; no other code reads it [code: app/bundles/ReportBundle/Form/Type/ReportType.php:67-78 @7.x] [code: app/bundles/ReportBundle/Entity/Report.php:172 @7.x].
R13. `hasScheduleChanged` is computed on edit but not persisted, and nothing reads it [code: app/bundles/ReportBundle/Controller/ReportController.php:332-340 @7.x].
R14. Deleting a Report cascades to its `reports_schedulers` row (`ON DELETE CASCADE`) [code: app/bundles/ReportBundle/Entity/Scheduler.php:27-29 @7.x].

## 2. Visibility and permissions
R15. Permissions on `report:reports`: `viewown`, `viewother`, `editown`, `editother`, `create`, `deleteown`, `deleteother`, `publishown`, `publishother`, `full`, plus `report:export:enable` (bit 1024) [code: app/bundles/ReportBundle/Security/Permissions/ReportPermissions.php:15-20 @7.x].
R16. The list needs `viewown` or `viewother`. Without `viewother` it is forced to `createdBy = me`, and non-admins never see `audit.log` Reports [code: app/bundles/ReportBundle/Controller/ReportController.php:54-56,66-74 @7.x].
R17. View, export, download, send-now and the Report widget use `hasEntityAccess(viewown, viewother, createdBy)` [code: app/bundles/ReportBundle/Controller/ReportController.php:555,787,875 @7.x] [code: app/bundles/ReportBundle/Controller/ScheduleController.php:59 @7.x] [code: app/bundles/ReportBundle/EventListener/DashboardSubscriber.php:65 @7.x].
R18. Export buttons and the export action also need admin or `report:export:enable`. The view header shows Export HTML/CSV/XLSX only when there is data or a graph and the User may export [code: app/bundles/ReportBundle/Controller/ReportController.php:695,789-791 @7.x] [code: app/bundles/ReportBundle/Resources/views/Report/details.html.twig:60-90 @7.x].
R19. Create and clone need `report:reports:create`. Delete needs `deleteown/deleteother`. Edit checks only `viewown/viewother` on the entity [code: app/bundles/ReportBundle/Controller/ReportController.php:142-148,179-185,246-251,310-316,434-436 @7.x].
R20. The audit-log context is built and displayed only for admins or CLI [code: app/bundles/CoreBundle/EventListener/ReportSubscriber.php:162,179-183 @7.x].
R21. Report rows are not filtered by entity permissions. No context subscriber checks `viewother` or ownership of the underlying Contacts, Emails, etc. (grep over all `Report*Subscriber.php`; only the audit-log admin guard exists) [code: app/bundles/LeadBundle/EventListener/ReportSubscriber.php:171 @7.x].
R22. The Reports menu entry (priority 20) needs `report:reports:viewown|viewother` [code: app/bundles/ReportBundle/Config/config.php:65-77 @7.x].

## 3. Query building
R23. `getReportData()` dispatches, in order: `REPORT_ON_GENERATE` (inside the builder), `REPORT_ON_GRAPH_GENERATE` (unless `ignoreGraphData`), `REPORT_QUERY_PRE_EXECUTE`, the query itself, then `REPORT_ON_DISPLAY` (unless `ignoreTableData` or no columns) [code: app/bundles/ReportBundle/Model/ReportModel.php:519,535-569,578-580,582-630 @7.x].
R24. The generated query must contain a SELECT; otherwise `InvalidReportQueryException('Only SELECT statements are valid')` is thrown [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:124-133 @7.x].
R25. The context subscriber sets FROM and joins. Helper joins are added only when a used column or filter has the matching prefix: category `c.`; Contact `l.` (also for `i.`, `comp.`, `cmp.name`, `clel.campaign_id`, `dnc_preferences`); IP `i.`; company `comp.`/`companies_lead.` (de-duplicated); campaign-by-channel `clel`/`cmp`; channel tables [code: app/bundles/ReportBundle/Event/ReportGeneratorEvent.php:113-234,422-436 @7.x].
R26. Channel columns (`channel.name`, `.description`, `.category_id`, `.date_added`, `.created_by`, `.created_by_user`) become `CASE WHEN <channel>.col IS NOT NULL THEN … END` across channels that declare the `reporting` feature, which today are Email (`emails`) and Dynamic Content (`dynamic_content`) [code: app/bundles/ReportBundle/Event/ReportBuilderEvent.php:205-268 @7.x] [code: app/bundles/EmailBundle/EventListener/ChannelSubscriber.php:47-49 @7.x] [code: app/bundles/DynamicContentBundle/EventListener/ChannelSubscriber.php:26-28 @7.x].
R27. SELECT rules:
- A plain column is back-tick quoted `` `alias`.`col` ``.
- A `formula` is used verbatim.
- A `groupByFormula` replaces it when the Report groups by that column.
- `prefix`/`suffix` wrap it in `CONCAT()`.
- `alias` adds `AS alias`.
- `{{count}}` inside a formula becomes a `(SELECT COUNT(*) …)` of the same query.

[code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:309-342,401-412,862-867 @7.x]
R28. Aggregators are ignored without a group-by. With a group-by they are selected as `FUNC(col) AS 'FUNC col'`, and a column that is only an aggregator target (not grouped) is left out of the raw SELECT [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:289-307,416-433 @7.x].
R29. GROUP BY completion: every non-aggregated base column in SELECT or ORDER BY is appended to GROUP BY. Literals, subqueries, aggregate arguments and keywords are skipped, and duplicates are removed ignoring quotes and case [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:346-399,466-587 @7.x].
R30. ORDER BY: a session order (column-header click) wins over the saved `tableOrder`. The saved order uses the column `formula` when one is defined [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:210-244 @7.x].
R31. `getReportData()` removes ORDER BY before the graph and count queries. It re-adds each ORDER BY item only when the column is in the allowed list and the direction is ASC/DESC/empty. A formula column orders by the formula, wrapped as `(formula) + 0` when it has a prefix or suffix [code: app/bundles/ReportBundle/Model/ReportModel.php:530-533,571-575,675-748 @7.x].
R32. `options['having']` and `options['groupby']` (when the entity has no group-by) are honoured [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:265-283 @7.x].
R33. If the subscriber calls `setFilterExpression()`, that expression replaces standard filter processing for the WHERE clause [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:202-208 @7.x].

## 4. Filters and operators
R34. Operator sets by type:

| Set | Operators |
|---|---|
| `default` | eq, gt, gte, lt, lte, neq, like, notLike, empty, notEmpty, contains, startsWith, endsWith |
| `bool` | eq, neq |
| `int` | eq, gt, gte, lt, lte, neq |
| `multiselect` | in, notIn |
| `select` | eq, neq |
| `text` | eq, neq, empty, notEmpty, like, notLike, contains, startsWith, endsWith |

A column may override the set with `operators` or choose one with `operatorGroup`. Unknown types use `default` [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:23-70 @7.x] [code: app/bundles/ReportBundle/Model/ReportModel.php:765-785 @7.x].
R35. Filters are ANDed in order. `glue = 'or'` closes the current AND group and starts a new one, and the groups are ORed. A single group gets no extra OR wrapper [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:605-610,747-760 @7.x].
R36. A filter with an empty trimmed value is skipped unless its operator is `empty`, `notEmpty` or `neq` [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:600-603,880-883 @7.x].
R37. `notEmpty` becomes `IS NOT NULL`, plus `<> ''` for non-date types. `empty` becomes `IS NULL`, or `= ''` for non-date types. `neq` becomes `(col IS NULL OR col <> :v)` [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:660-686,873-878 @7.x].
R38. For `text`, `string`, `email`, `url` and `datetime`:
- `like`/`notLike` wrap the value in `%…%` unless it already contains `%`.
- `startsWith` becomes `v%`, `endsWith` becomes `%v` and `contains` becomes `%v%`.

[code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:712-737 @7.x]
R39. A `bool` value greater than 1 (the "clear" button, value 2) is ignored. `int`/`float` values are cast and inlined [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:693-710 @7.x].
R40. The `tag` column filters through `l.id IN/NOT IN (SELECT DISTINCT lead_id FROM lead_tags_xref …)`, with tag ids cast to int [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:766-790 @7.x].
R41. `dnc_preferences` filters through a `lead_donotcontact` subquery with `channel:reason` values; an invalid format throws `InvalidArgumentException` [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:801-855 @7.x].
R42. Dynamic filters (`dynamic = 1`) are overridden at view time from `session['mautic.report.<id>.filters']`, set via `?filterby=&value=`. The override merges onto the saved filter and applies `%` wildcards according to the saved condition. An empty value falls back to `defaultValue` [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:165-199 @7.x] [code: app/bundles/ReportBundle/Controller/ReportController.php:597-651 @7.x] [code: app/bundles/CoreBundle/Controller/CommonController.php:644-663 @7.x].
R43. The dynamic filter form renders `bool` as a yes/no/clear button group, `date`/`datetime` as pickers, `select`/`multiselect` as choices, and everything else as text [code: app/bundles/ReportBundle/Form/Type/DynamicFiltersType.php:64-110 @7.x].
R44. Parameter names are `i<index>c<alnum column>`, so one column may be filtered several times [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:598 @7.x].

## 5. Dates, relative dates and timezones
R45. Datetime and time filter values are converted from local to UTC on submit and back for display (`Y-m-d` for date, `H:i:s` for time). String-like conditions and relative values are left as typed [code: app/bundles/ReportBundle/Form/DataTransformer/ReportFilterDataTransformer.php:28-97 @7.x] [docs: https://docs.mautic.org/en/8.0/reports/reports.html#relative-date-filters].
R46. A value is treated as relative for `date`/`datetime` columns with non-string operators when it matches `today|tomorrow|yesterday`, `(this|last|next) (week|month|year)`, `[+-]…`, `… ago` or `(first|last) day of …`, or contains `anniversary`/`birthday`, and PHP can parse it [code: app/bundles/ReportBundle/Helper/RelativeDateHelper.php:11-37 @7.x].
R47. Resolution rules:
- Relative `eq` matches the whole period (`>= start AND <= end`), and `neq` matches `IS NULL OR < start OR > end`.
- For calendar periods or date-only columns, `gt`/`lte` use the period end and `gte`/`lt` use the period start.
- Any other datetime value is a single instant.
- `this month` means `first day of this month`, and `this year` means `first day of January this year`.

[code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:624-657 @7.x] [code: app/bundles/ReportBundle/Helper/RelativeDateHelper.php:44-93 @7.x] [docs: https://docs.mautic.org/en/8.0/reports/reports.html#relative-date-filters]
R48. Relative periods are computed with `DateTimeHelper(…, 'local')`. That uses the static default from the `default_timezone` parameter, not the session User timezone. Datetime columns are then converted to UTC [code: app/bundles/ReportBundle/Helper/RelativeDateHelper.php:51-59,80-84 @7.x] [code: app/bundles/CoreBundle/Helper/DateTimeHelper.php:47-59,386-391 @7.x] [docs: https://docs.mautic.org/en/8.0/reports/reports.html#relative-date-filters]. (The code analysis input said "user's local timezone". The code read here shows `default_timezone`, which matches the 8.0 docs.)
R49. Anniversary/birthday filters compare `DATE_FORMAT(col, '%m-%d')` with the month-day of the relative date. `empty`/`notEmpty` test the raw column [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:633-637 @7.x].
R50. The UI date range comes from `daterange[date_from|date_to]` or `session['mautic.report.date.from|to']` (stored `Y-m-d`). The model sets `dateTo` to 23:59:59 (to today's 23:59:59 when `dateTo` is today) and converts both dates to UTC [code: app/bundles/ReportBundle/Controller/ReportController.php:561-594,653-663 @7.x] [code: app/bundles/ReportBundle/Model/ReportModel.php:453-473 @7.x].
R51. `applyDateFilters()` with no dates defaults to the last 30 days, and its clause is `col IS NULL OR col BETWEEN :dateFrom AND :dateTo` (`DATE(col)` for date-only). `applyDateFiltersWithoutNullValues()` drops the NULL branch [code: app/bundles/ReportBundle/Event/ReportGeneratorEvent.php:241-261,396-420 @7.x].
R52. The Quick filters dropdown offers Today, Yesterday, Last 7/30/90 days and refreshes the Report [docs: https://docs.mautic.org/en/7.2/reports/reports.html#quick-filters].
R53. Graph queries use separate clones of dateFrom/dateTo (default last 30 days to now) passed to `ChartQuery` [code: app/bundles/ReportBundle/Model/ReportModel.php:449-450,536-537,548-550 @7.x].

## 6. Running and displaying a Report
R54. With `paginate=true`, the limit comes from `session['mautic.report.<id>.limit']` (default `default_pagelimit` = 30) unless `options['limit']` and `options['page']` are given. The total is `SELECT count(*) FROM (<query>) c`, computed once and cached in options. Without pagination the total is the row count [code: app/bundles/ReportBundle/Model/ReportModel.php:582-623,787-800 @7.x].
R55. The current page is remembered in `session['mautic.report.<id>.page']` [code: app/bundles/ReportBundle/Model/ReportModel.php:525-528 @7.x].
R56. Every cell is `html_entity_decode`d in the model; the HTML table escapes again [code: app/bundles/ReportBundle/Model/ReportModel.php:646-650 @7.x].
R57. In `dev` or with `debug=true`, the view shows the interpolated SQL, the count SQL and the query time [code: app/bundles/ReportBundle/Model/ReportModel.php:632-644 @7.x] [code: app/bundles/ReportBundle/Resources/views/Report/_details_content_footer.html.twig:2-7 @7.x].
R58. Settings: `showGraphsAboveTable` moves graphs above the table, `hideDateRangeFilter` hides the date range form, and `showDynamicFilters` opens the filter panel by default [code: app/bundles/ReportBundle/Resources/views/Report/_details_report_content.html.twig:1-16,194 @7.x] [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data-sources].
R59. The Filters panel appears only when the Report has at least one dynamic filter [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data].
R60. A graph renders only when its subscriber set `data`. `line` spans 12 grid columns and the others 4. Templates exist only for `line`, `pie` and `table` [code: app/bundles/ReportBundle/Resources/views/Report/details_data_graphs.html.twig:5-15 @7.x].
R61. A context may replace the details template via `setContentTemplate()`; the default is `@MauticReport/Report/details.html.twig` [code: app/bundles/ReportBundle/Event/ReportGeneratorEvent.php:53-68 @7.x].
R62. Report queries use the read replica when the connection is a `PrimaryReadReplicaConnection` [code: app/bundles/ReportBundle/Model/ReportModel.php:893-901 @7.x].
R63. When calculated columns are selected, a totals row is shown [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data] [code: app/bundles/ReportBundle/Crate/ReportDataResult.php:42-68 @7.x].

## 7. Export from the UI
R64. Formats: CSV, Excel (XLSX) and HTML, from the Report view's top-right dropdown [docs: https://docs.mautic.org/en/7.2/reports/reports.html#exporting-reports] [code: app/bundles/ReportBundle/Config/config.php:6-62 @7.x].
R65. CSV is streamed in batches of `report_export_batch_size` (1000), using the session date range (default last 30 days) and the session dynamic filters. The header is written on page 1 and the totals row after the last batch [code: app/bundles/ReportBundle/Controller/ReportController.php:793-841 @7.x] [code: app/bundles/ReportBundle/Model/CsvExporter.php:24-47 @7.x].
R66. Totals accumulate across batches: SUM and COUNT add up, AVG is divided by the total row count at the end, and MIN/MAX fold [code: app/bundles/ReportBundle/Crate/ReportDataResult.php:150-158,198-245 @7.x].
R67. XLSX and HTML are not batched; the whole result comes from one `getReportData()` call. XLSX throws `No report data to be exported` when empty and decodes entities per cell. HTML renders `@MauticReport/Report/export.html.twig` [code: app/bundles/ReportBundle/Controller/ReportController.php:842-849 @7.x] [code: app/bundles/ReportBundle/Model/ExcelExporter.php:38-50 @7.x] [code: app/bundles/ReportBundle/Model/ReportModel.php:408-418 @7.x].
R68. File name: `<local Y-m-d H:i:s with spaces→_>_<alnum name>.<ext>`, sent as `application/octet-stream` attachment [code: app/bundles/ReportBundle/Model/ReportModel.php:384-385 @7.x] [code: app/bundles/ReportBundle/Model/ExportResponse.php:14-21 @7.x].
R69. Aggregate columns whose key starts with `AVG` are typed `float`, others `int`. An empty first totals cell gets the translated "Totals" label [code: app/bundles/ReportBundle/Crate/ReportDataResult.php:183-193 @7.x] [code: app/bundles/ReportBundle/Model/CsvExporter.php:61-71 @7.x].
R70. With `csv_always_enclose=true`, every cell is wrapped in `"`, but embedded quotes are not escaped. Otherwise `CsvHelper::putCsv` is used [code: app/bundles/ReportBundle/Model/CsvExporter.php:76-83 @7.x].
R71. The list row action **Export & Send** emails a CSV link to the User's profile email [docs: https://docs.mautic.org/en/7.2/reports/reports.html#report-options]. In code, "send now" refuses an already scheduled Report (`mautic.report.scheduled.already`). Otherwise it sets the Report to `NOW` with the current User's email and saves it, so the next cron run sends it [code: app/bundles/ReportBundle/Controller/ScheduleController.php:46-80 @7.x].

## 8. Scheduled Reports
R72. Schedule UI: **Email Report** Yes/No, **To** (comma-separated), **Every** now/day/week/month. Month means first or last + day of week, and "Weekdays" is also available [docs: https://docs.mautic.org/en/7.2/reports/reports.html#schedule].
R73. Form `PRE_SUBMIT` drops `scheduleDay`/`scheduleMonthFrequency` for NOW/DAILY, and drops `scheduleMonthFrequency` for WEEKLY [code: app/bundles/ReportBundle/Form/Type/ReportType.php:399-412 @7.x].
R74. Validation rules:
- Not scheduled: all schedule fields are nulled.
- Scheduled: `toAddress` is required (`mautic.report.schedule.to_address_required`).
- DAILY: day and frequency are cleared.
- WEEKLY: a valid day is required.
- MONTHLY: a valid day and a frequency of `1` or `-1` are required.
- Any other case raises `mautic.report.schedule.notValid`.
- The next event must be computable, otherwise `notValid`/`notSupportedType` is raised.

[code: app/bundles/ReportBundle/Scheduler/Validator/ScheduleIsValidValidator.php:25-87 @7.x]
R75. Every save deletes the Report's scheduler row and inserts one with the next occurrence when there is one. Unscheduled Reports have no row. No DB unique key enforces one row per Report [code: app/bundles/ReportBundle/Scheduler/Model/SchedulerPlanner.php:21-49 @7.x].
R76. Next occurrence:
- Start: now for NOW, otherwise tomorrow 00:00.
- RRULE frequency: SECONDLY (NOW), DAILY, WEEKLY with `BYDAY` (MO..FR for `WEEK_DAYS`), MONTHLY with `BYDAY` prefixed `1`/`-1`.
- `isScheduled=false` raises `NoScheduleException`.

[code: app/bundles/ReportBundle/Scheduler/Builder/SchedulerBuilder.php:39-63 @7.x] [code: app/bundles/ReportBundle/Scheduler/Builder/SchedulerWeeklyBuilder.php:20-37 @7.x] [code: app/bundles/ReportBundle/Scheduler/Builder/SchedulerMonthBuilder.php:20-43 @7.x] [code: app/bundles/ReportBundle/Scheduler/Date/DateBuilder.php:49-62 @7.x]
R77. The schedule preview shows the next 10 dates (1 for NOW) [code: app/bundles/ReportBundle/Scheduler/Date/DateBuilder.php:25-42 @7.x].
R78. `mautic:reports:scheduler [--report=ID] [--cleanup-only]`:
- A non-numeric `--report` returns `INVALID` (2).
- It always runs cleanup first (all Reports, or the one Report).
- `--cleanup-only` stops after cleanup.
- Otherwise it processes exports; a `FileIOException` returns `FAILURE`.

[code: app/bundles/ReportBundle/Scheduler/Command/ExportSchedulerCommand.php:34-78 @7.x] [docs: https://docs.mautic.org/en/7.2/reports/reports.html#cron-job-to-schedule-reports]
R79. The command selects schedulers with `schedule_date <= now`, optionally for one Report [code: app/bundles/ReportBundle/Entity/SchedulerRepository.php:24-40 @7.x].
R80. Per scheduler:
- A NOW Report is unscheduled immediately (direct flush, no events, no audit log).
- A published Report is fetched in batches (`paginate`, `limit=batch`, `ignoreGraphData`) and appended to `<report_temp_dir>/<scheduleDate Y-m-d>_<name>.csv` until `page*batch >= totalResults`. `JobExtendTimeEvent` is dispatched between batches.
- `REPORT_SCHEDULE_SEND` follows.
- Unpublished Reports are skipped but re-planned.

[code: app/bundles/ReportBundle/Model/ReportExporter.php:29-90 @7.x] [code: app/bundles/ReportBundle/Model/ScheduleModel.php:44-49 @7.x] [code: app/bundles/ReportBundle/Model/ReportFileWriter.php:21-52 @7.x]
R81. Export windows are relative to `scheduleDate` at 00:00:00: NOW = 10 years back, DAILY = 1 day, WEEKLY = 7 days, MONTHLY = 1 month. `dateTo` is midnight minus one second [code: app/bundles/ReportBundle/Model/ReportExporter.php:44-65 @7.x]. These mutable `DateTime` values then go through the same 23:59:59 + UTC normalisation as the UI (inferred; no test) [code: app/bundles/ReportBundle/Adapter/ReportDataAdapter.php:19-32 @7.x].
R82. The email goes to `toAddress` split on commas, with subject `Report <name> - <Y-m-d>.` and the body "The report <link> generated at <date> is attached." [code: app/bundles/ReportBundle/Scheduler/Model/SendSchedule.php:26-62 @7.x] [code: app/bundles/ReportBundle/Scheduler/Model/MessageSchedule.php:19-48 @7.x].
R83. Size handling:
- A CSV larger than `report_export_max_filesize_in_bytes` (5,000,000) is zipped, with entry name `report.csv`.
- If the zip is still too large, it moves to `<report_temp_dir>/csv_reports/report_<id>.zip`, the body becomes a download link, and `REPORT_PERMANENT_FILE_CREATED` is dispatched.

[code: app/bundles/ReportBundle/Scheduler/Model/FileHandler.php:17-107 @7.x] [code: app/bundles/ReportBundle/Scheduler/Model/SendSchedule.php:50-51 @7.x]
R84. After Messenger handles the email, `RemoveReportAttachmentHandler` (priority -1000) deletes the attached `.csv`/`.zip` from `report_temp_dir` [code: app/bundles/MessengerBundle/MessageHandler/RemoveReportAttachmentHandler.php:13-50 @7.x].
R85. Permanent zips older than 7 days (file mtime, day granularity) are deleted by the command [code: app/bundles/ReportBundle/Model/ReportCleanup.php:9,16-59 @7.x].
R86. Download behaviour:
- `GET /s/reports/download/{id}/csv` streams `report_<id>.zip` as `report-<id>.zip`.
- If the file is missing and the Report is unscheduled, the Report is set to NOW for the current User and the response is 404 `mautic.report.download.missing.but.scheduled`.
- If the file is missing and the Report is scheduled, the response is 404 `mautic.report.download.missing`.
- Only `csv` is accepted.

[code: app/bundles/ReportBundle/Controller/ReportController.php:860-896 @7.x]

## 9. Reports REST API
R87. Standard entity endpoints: `GET /api/reports`, `GET /api/reports/{id}`, `POST /api/reports/new`, `PUT|PATCH /api/reports/{id}/edit`, `DELETE /api/reports/{id}/delete` [code: app/bundles/ReportBundle/Config/config.php:6-62 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html].
R88. `GET /api/reports/{id}` returns compiled data: `totalResults`, `data` (rows keyed by alias such as `email1`), `dataColumns` (alias → column), `limit`, `page`, `dateFrom`, `dateTo`, `debug` and `aggregatorColumns`, plus `report` metadata. `graphs`, `contentTemplate` and `columns` are removed [code: app/bundles/ReportBundle/Controller/Api/ReportApiController.php:64-101 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html#get-report].
R89. `dateFrom`/`dateTo` get 00:00:00/23:59:59 when the time is missing and are UTC unless the string carries an offset. They are `DateTimeImmutable`, so their time is kept exactly. `page` or `limit` turns pagination on; without either, all rows are returned [code: app/bundles/ReportBundle/Controller/Api/ReportApiController.php:112-135 @7.x].
R90. GET by id requires `report:reports:view`; if `viewother` is not granted, `createdBy` must be the caller [code: app/bundles/ReportBundle/Controller/Api/ReportApiController.php:67-86 @7.x].
R91. The list uses the standard own/other filter and supports `select` [code: app/bundles/ReportBundle/Tests/Controller/Api/ReportApiControllerTest.php:57 @7.x]. The devdocs say the list "isn't filterable" and returns "Contact Reports" [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html#list-reports].
R92. Serialised fields: the list has `id, name, description, system, isScheduled`; detail adds `source, columns, filters, tableOrder, graphs, groupBy, settings, aggregators, scheduleUnit, toAddress, scheduleDay, scheduleMonthFrequency` [code: app/bundles/ReportBundle/Entity/Report.php:232-261 @7.x].

## 10. Dependencies on other entities
R93. `getReportsIdsWithDependenciesOnSegment()`, `…OnEmail()` (sources `emails`/`email.stats`, column `e.id`) and `…OnTag()` search the serialised filters and then verify the values. Other bundles use them to block deleting referenced entities [code: app/bundles/ReportBundle/Model/ReportModel.php:805-888 @7.x].

## 11. Dashboard
D1. Each User has their own widgets. `getWidgets()` forces `createdBy = current user`, and `Dashboard\Widget::get()` throws `AccessDeniedException` for another User's widget [code: app/bundles/DashboardBundle/Model/DashboardModel.php:84-99 @7.x] [code: app/bundles/DashboardBundle/Dashboard/Widget.php:38-41 @7.x] [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html].
D2. There is no dashboard permission class. `dashboard:widgets` is declared as the permission base but never registered [code: app/bundles/DashboardBundle/Model/DashboardModel.php:60-63 @7.x].
D3. A User with no widgets gets `global.default` applied. This loads `<dashboard_import_dir>/default.json`, clears the User's widgets and cache, and saves the file's widgets. The shipped default has `created.leads.in.time` (100%), `page.hits.in.time`, `submissions.in.time`, `recent.activity` and `upcoming.emails` [code: app/bundles/DashboardBundle/Controller/DashboardController.php:47-50,379-422 @7.x] [code: app/assets/dashboards/default.json @7.x].
D4. Global dashboard files: `default`, `alternative-default`, `email-overview`, `forms-and-assets`, `landing-pages`, `stats-overview` [code: app/assets/dashboards/ @7.x].
D5. The date range POST stores `mautic.daterange.form.from` (`Y-m-d`) and `.to` (`Y-m-d 23:59:59`) in the session and clears the dashboard cache [code: app/bundles/DashboardBundle/Controller/DashboardController.php:56-68 @7.x] [code: app/bundles/DashboardBundle/Dashboard/Widget.php:55-74 @7.x].
D6. The default filter is `dateFrom` = session value or `now + default_daterange_filter` (`-1 month`) at 00:00, and `dateTo` = session value or today, always at 23:59:59. A `timezone` param is set to the User's timezone when absent [code: app/bundles/DashboardBundle/Model/DashboardModel.php:228-230,313-328 @7.x] [code: app/bundles/CoreBundle/Config/config.php:709 @7.x].
D7. The *Upcoming Emails* and *Recent activity* widgets ignore the date range [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#date-range-filter].
D8. Rendering a widget:
- The global filter is merged over the widget params, and the filter wins.
- `cacheTimeout` defaults to `cached_data_timeout` (10 min) when unset or `-1`; a global `0` means no cache.
- `DASHBOARD_ON_MODULE_DETAIL_GENERATE` is dispatched.
- Any `Throwable` is logged and the widget shows `mautic.dashboard.widget.load.failed`.

[code: app/bundles/DashboardBundle/Model/DashboardModel.php:210-253 @7.x]
D9. Cache:
- Key: `dashboard.widget.` + unique id, or md5(unique id + dateFrom + dateTo) when dates are present.
- Unique id: `<type>_<md5(params minus dates, width, height, locale)>`.
- Entries are tagged `dashboard_widget` and expire after `cacheTimeout` minutes.
- The legacy filesystem cache is used only when no cache provider is injected.

[code: app/bundles/DashboardBundle/Event/WidgetDetailEvent.php:70-93,201-226,262-315,346-349 @7.x]
D10. `clearDashboardCache()` clears the User's legacy filesystem cache and invalidates the `dashboard_widget` tag for all Users [code: app/bundles/DashboardBundle/Model/DashboardModel.php:258-266 @7.x].
D11. Widget form:
- Width 25/50/75/100% (default 100).
- Height 215/330/445/560/675 px (default 330).
- Name defaults to `mautic.widget.<type>`.
- The type list shows only types whose bundle permissions are all granted.
- A type-specific `params` sub-form appears when the bundle declares a `formAlias`.

[code: app/bundles/DashboardBundle/Form/Type/WidgetType.php:30-158 @7.x] [code: app/bundles/DashboardBundle/Model/DashboardModel.php:298-308 @7.x] [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#widgets]
D12. Listing widget types requires all of the bundle's permissions, while rendering requires any; a missing permission shows `mautic.dashboard.missing.permission` [code: app/bundles/DashboardBundle/Event/WidgetTypeListEvent.php:60-68 @7.x] [code: app/bundles/DashboardBundle/Event/WidgetDetailEvent.php:328-333 @7.x] [code: app/bundles/DashboardBundle/EventListener/DashboardSubscriber.php:85-102 @7.x].
D13. Ordering: drag and drop posts `ordering[]`, which is persisted only for the current User's widgets [code: app/bundles/DashboardBundle/Controller/AjaxController.php:76-84 @7.x] [code: app/bundles/DashboardBundle/Entity/WidgetRepository.php:17-34 @7.x] [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#widget-ordering].
D14. Export and import:
- `export?name=` downloads JSON `{name, description, widgets[]}` (widget config only, no data).
- `save` writes it to `<dashboard_import_user_dir>/<userId>/<name>.json`.
- `import` lists user and global files, accepts a `.json` upload and previews it.
- `applyDashboardFile` replaces the current dashboard, and `deleteDashboardFile` unlinks a file.
- Files are addressed as `user.<name>` or `global.<name>`.

[code: app/bundles/DashboardBundle/Controller/DashboardController.php:296-536 @7.x] [code: app/bundles/DashboardBundle/Model/DashboardModel.php:107-146 @7.x] [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#dashboard-export]
D15. `/s/dashboard/widget/{id}` is XHR-only. It applies a POSTed range, enforces ownership, and returns `{success, widgetId, widgetHtml, widgetWidth, widgetHeight}` [code: app/bundles/DashboardBundle/Controller/DashboardController.php:105-130 @7.x].
D16. `GET /api/data` lists widget types. `GET /api/data/{type}` renders a transient widget with these parameters:
- `dateFrom`/`dateTo` (interpreted in `timezone`), `timeUnit` (default `Y`), `dateFormat`, `limit`, `filter[]`, `dataset[]`.
- `cacheTimeout` (default 0) and `height` (default 300).
- `dataFormat=raw` flattens chart datasets.

It returns `cached`, `execution_time` and `data`, or 404 when there is no data [code: app/bundles/DashboardBundle/Controller/Api/WidgetApiController.php:62-158 @7.x].
D17. The Report widget (`type=report`, param `graph = "<reportId>:<graphId>"`) behaves as follows:
- It requires view access to the Report.
- It runs only that graph, with table data only for table graphs, limited to 10 rows.
- Chart height is the widget height minus 90.
- It links "View Full Report" with the range.
- It offers only published Reports with graphs, limited to the User's own Reports without `viewother`.

[code: app/bundles/ReportBundle/EventListener/DashboardSubscriber.php:15,54-148 @7.x] [code: app/bundles/ReportBundle/Model/ReportModel.php:753-758 @7.x] [code: app/bundles/ReportBundle/Entity/ReportRepository.php:111-135 @7.x]
D18. `recent.activity` shows `round((height-80)/75)` audit-log rows with resolved names and links [code: app/bundles/CoreBundle/EventListener/DashboardSubscriber.php:52-106 @7.x].

## 12. Charts
C1. The unit comes from the range length: `H` for ≤1 day, `d` for ≤31 days, `W` for ≤100, `m` for ≤1000, otherwise `Y` [code: app/bundles/CoreBundle/Helper/Chart/DateRangeUnitTrait.php:10-40 @7.x] [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#date-range-filter].
C2. Buckets use `DATE_FORMAT(CONVERT_TZ(col, '+00:00', <offset>), …)`, where the offset comes from `DateTimeHelper::getLocalTimezoneOffset()` (instance `default_timezone`). When a generated date column exists for the table, it is used directly without `CONVERT_TZ` [code: app/bundles/CoreBundle/Helper/Chart/ChartQuery.php:575-589 @7.x] [code: app/bundles/CoreBundle/Helper/DateTimeHelper.php:381-391 @7.x].
C3. Missing buckets are filled with 0 [code: app/bundles/CoreBundle/Helper/Chart/ChartQuery.php:300-380 @7.x].

## 13. StatsBundle
S1. `Collector::fetchStats($statName, $from, $to, ?FetchOptions)` dispatches `AGGREGATE_STAT_REQUEST` and returns the `StatCollection`. Listeners call `statsCollected()` to stop propagation. The only listener is EmailBundle `GraphAggregateStatsSubscriber` [code: app/bundles/StatsBundle/Aggregate/Collector.php:21-32 @7.x] [code: app/bundles/StatsBundle/Event/AggregateStatRequestEvent.php:28-91 @7.x].
S2. `addStatByDateTime()` converts the (mutable) `DateTime` to UTC before bucketing by `Y/n/j/H`. `addStatByDateTimeStringInUTC()` accepts `Y-m-d H:i:s`, `YYYY WW` (Monday of that ISO week) or `YYYY` [code: app/bundles/StatsBundle/Aggregate/Collection/StatCollection.php:46-79 @7.x].
S3. `Calculator::getSumsByYear/Month/Day/Week` and `getCountsByHour` emit one entry per period between from and to, with gaps filled with 0. Week labels are `Y-W` and padded one week past `to`. `getSum()` returns an empty `StatDAO` [code: app/bundles/StatsBundle/Aggregate/Calculator.php:23-172 @7.x].
S4. `StatDAO::getStat()` throws `InvalidArgumentException` for an unknown key [code: app/bundles/StatsBundle/Aggregate/Collection/DAO/StatDAO.php:25-32 @7.x].

## 14. Open questions and contradictions
1. Saved multi-column order: the docs say the last entry is applied first, with earlier entries breaking ties. The code calls `orderBy()` per saved entry [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:234-243 @7.x] [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data]. With DBAL `orderBy()` replace semantics, only the last entry would apply [unverified: vendor not present in the analysed tree].
2. Totals in exports: the docs say exports exclude the totals row, but the code writes it in CSV and XLSX (R65, R69) [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data].
3. `system` / "Visible for all logged-in users": the docs and API docs describe it as a visibility control; the code ignores it (R12, R16) [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html#list-reports].
4. Edit permission is checked with view permissions (R19).
5. Dashboard "see own" (docs: widgets show own data) vs type listing that requires all permissions (D12) [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#dashboard-permissions].
6. Whether the "midnight" of DAILY/WEEKLY/MONTHLY schedules uses the User timezone (web request PHP timezone at save) or `default_timezone` is unverified; the docs say "your time zone" [docs: https://docs.mautic.org/en/7.2/reports/reports.html#schedule] [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:30-41 @7.x].
7. The widget cache key lacks a user id, while widget data can be permission-filtered (D9) [code: app/bundles/DashboardBundle/Event/WidgetDetailEvent.php:262-280 @7.x].
8. The docs say the dashboard range defaults to 30 days and there are 3 predefined dashboards; the code uses `-1 month` and ships 6 files (D4, D6).
