# Reports, Dashboard and Stats: PR history

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
3. Regression catalogue
4. Feature timeline
5. Removed, deprecated, replaced
6. Maintainer norms for this area
7. Open questions
8. Coverage

## 1. How to read this file
Source: merged pull requests on mautic/mautic for Reports, the Dashboard and StatsBundle, harvested 2026-10-15.
Versions come from the first release tag in the 7.x tree that contains the merge, or else from the base branch, milestone and merge date. A `~` marks an inferred version. "Unreleased 7.x" means the merge is on the 7.x head after 7.2.1 (milestone 7.3.0-rc) and in no tag.
Current behaviour is in behaviour.md. This file explains why and when. Where the two disagree, behaviour.md wins.

## 2. Decisions that shaped current behaviour

### Filters and operators
- Filters can be grouped with AND/OR glue, mirroring segment filters. Before this, every filter was ANDed [PR #4261] (v2.9.0). An empty OR filter is skipped, and the builder no longer emits empty or single-item OR groups. Why: an empty "Name contains" in an OR group produced invalid SQL [PR #16125] (v7.2.0).
- A filter with an empty value is skipped and the Report still saves. Why: saving returned a 500 [PR #12569] (v5.1.0).
- `neq` also returns rows where the column is NULL. Why: Contacts with an empty `address1` vanished from "address1 != xxx" [PR #10043] (~v4.3).
- `empty` matches NULL or `''` (`IS NULL OR = ''`). Why: the earlier `IS NULL AND != ''` matched nothing [PR #7746] (v2.16.0). On date, datetime and time columns, `empty`/`notEmpty` test only NULL, because MySQL 8 rejects a date compared with `''` (error 1525) [PR #10194] (v4.2.0).
- `like`/`notLike` wrap the value as `%value%` when it has no `%`; a value with `%` is used as typed. Why: parity with segment and dynamic content filters. escopecz proposed a UI hint instead, citing BC and index use; kuzmany argued values with `%` are unchanged, so it is not a BC break [PR #13080] (v5.1.0).
- `contains`, `startsWith` and `endsWith` work on URL columns [PR #6116] (v2.14.0) and on text columns such as UTM fields. Why: they raised "undefined method contains of ExpressionBuilder" [PR #13867] (~v5.2).
- Tag filters (including, excluding, empty, not empty) exist on every Contact-based source. Empty and not empty were added in review to match segment tag filters. A Segment filter was added to Emails Sent, Do Not Contact and UTM codes at the same time [PR #11346] (v5.0.0).
- The tag filter is applied by `MauticReportBuilder`, not by `ReportGeneratorEvent`. Why: it needs the DB connection. The same change fixed AND/OR logic with tags and the error when a tag filter was changed to a text filter [PR #12403] (v5.0.0).
- Tag filter values are cast to integers before they enter the `lead_tags_xref` subquery, so no raw filter value reaches the SQL. This was a security fix (advisory GHSA-m478-p4vf-7j7j). The reviewer preferred Doctrine typed binding; an in-place integer cast was accepted [PR #17129] (v7.2.1) [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:766-790 @7.x].
- Boolean filter columns such as "Is published" show a Yes/No radio, and the choice is saved (issue mautic/mautic#14857). Each filter row needs unique element IDs [PR #14909] (v5.2.6).
- An aggregator on a boolean column no longer limits the operators of other filters. Why: the aggregator field had copied a CSS class that triggered the filter JS [PR #12688] (~v5.0).
- Filters on formula columns [PR #3632] (v2.7.1) and on aggregated ratio columns work; aggregates are never placed in WHERE [PR #7070] (v2.15.1).
- New filter, order and function rows get an index above the highest existing one, not the row count. Why: after a deletion a new row could reuse an index and not save [PR #3635] (v2.7.1) [PR #6252] (v2.14.1).
- Filter rows have a Clone button that copies column and value but not the condition, so users re-check the condition [PR #14132] (~v5.2).
- Only filters marked dynamic appear in the view's Filters panel [PR #4205] (v2.9.0). The value configured in the editor is the dynamic filter's default; a session value overrides it [PR #15160] (v7.0.0). The operator is shown next to each dynamic filter [PR #15366] (v7.1.0).
- Date dynamic filters use the filter's configured operator, not `LIKE`, and redisplay zero-padded dates [PR #4756] (v2.10.1) [PR #4917] (v2.10.1).

### Dates and timezones
- The date range includes rows whose date column is NULL (`col IS NULL OR col BETWEEN …`). Why: NULL-dated records vanished from every Report [PR #5212] (v2.12.0).
- The Page Hits source drops that NULL branch. Why: it slowed reports on page_hits tables of about a million rows ("unforking") [PR #14486] (v6.0.0). In 7.x the Page Hits context calls `applyDateFiltersWithoutNullValues()` [code: app/bundles/PageBundle/EventListener/ReportSubscriber.php:375 @7.x].
- The report date range is interpreted in the configured Mautic timezone, so a single-day range covers that local day [PR #8737] (v3.1.0). A single-day range must not include the next day's rows; this was fixed in 4.4 [PR #11256] (~v4.4.0), ported to 5.x [PR #11841] (v5.0.0), re-backported to 4.4 [PR #12541] (~v4.4.10) and fixed again [PR #15539] (v7.0.0).
- Date filter values are not shifted to UTC; datetime values are. Why: a date at 00:00 moved to the previous or next day in non-UTC instances [PR #10800] (~v4.2.1).
- A datetime filter keeps its time across saves (14:00 stays 14:00). Date columns accept string operators, which compare against the stored UTC string; date operators compare as dates in local time. A tooltip on the value says which applies [PR #15393] (v7.0.1).
- The UI, export, export command and widget push `dateTo` to 23:59:59. The API keeps an exact `dateTo` time. Why: the UI cannot set a time, API callers can [PR #15532] (v7.0.0).
- Relative expressions (`today`, `-2 days`, `last month`) are stored as typed and evaluated on every run. Why: they used to be frozen to fixed dates on save. `equals today` covers the whole day [PR #17256] (unreleased 7.x).
- Report graph widgets on the dashboard and the "Most hit email redirects" widget count to the end of the `dateTo` day [PR #8460] (v3.0.1) [PR #11086] (~v4.4.1).

### Query building: joins, GROUP BY, aggregators, ORDER BY
- Reports support GROUP BY and calculated columns (COUNT, SUM, AVG, MIN, MAX). Every source that joins Contacts exposes all custom Contact fields [PR #3824] (v2.8.0).
- Aggregates run over all rows, without DISTINCT: SUM of 2 on three Contacts is 6 [PR #4398] (v2.9.0).
- AVG is not rounded [PR #11273] (v5.0.0) and is exported as a decimal [PR #11514] (~v5.0). Why: grouped email stats lost all detail. The rounding had arrived as a side effect of an unrelated commit.
- A GROUP_CONCAT aggregator was added [PR #6289] (v2.14.1). It is not a selectable function in 7.x; the aggregator form offers COUNT, AVG, SUM, MIN and MAX. `GROUP_CONCAT` appears only in the builder's list of functions to skip during GROUP BY completion [code: app/bundles/ReportBundle/Form/Type/AggregatorType.php:29-35 @7.x] [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:103-107 @7.x].
- A column used only in an aggregator still triggers its joins [PR #6173] (v2.14.0). A column grouped but not selected does not error [PR #5961] (v2.13.1).
- A column's `groupByFormula` is used only when grouping by that column. Why: submission dates were exported truncated to midnight UTC [PR #7980] (v2.16.1).
- Under `ONLY_FULL_GROUP_BY`, a column selected only as an aggregator target (for example `ph.id` for `COUNT(ph.id)`) and not grouped is left out of the raw SELECT. Every other selected or ordered non-aggregated column is added to GROUP BY, which is rebuilt once from a deduplicated list. Why: Page Hits grouped by URL with `COUNT(ph.id)` returned 500 (issue mautic/mautic#17092). The first approach, dropping every non-grouped column, was rejected in review because it changed the report the user configured [PR #17099] (v7.2.0) [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:301-307,344-399 @7.x].
- When extracting columns from formulas for GROUP BY, single- and double-quoted strings are literals, so `fs.type = "view"` does not add a `view` column [PR #17099] (v7.2.0).
- Reports join a table only when a selected, grouped, ordered or filtered column needs it. Why: unneeded LEFT JOINs made some reports very slow [PR #7411] (v3.3.0). The company join is idempotent [PR #9973] (v4.0.0).
- Campaign columns join `campaign_lead_event_log` through its index [PR #4460] (v2.9.1). Email reports filtered by email ID are pre-filtered for speed [PR #7221] (v2.15.1).
- Totals use a wrapping `SELECT count(*) FROM (…)` query; rows are never loaded into PHP to count them. Why: memory leak on large reports [PR #6530] (v2.14.2).
- Duplicate SELECT aliases get numeric suffixes [PR #6728] (v2.15.0), and generated aliases such as `8e296a06` are sanitised [PR #9062] (v3.1.1).
- ORDER BY and GROUP BY work on computed columns such as clicks or bounced [PR #7085] (v2.15.1).
- Ratio and percentage columns sort numerically. Columns declare `prefix`/`suffix` for display and keep a numeric formula; ORDER BY uses the formula. Invalid ORDER BY expressions are rejected. Why: text sorting gave 1%, 27%, 3% [PR #16126] (v7.2.0).
- Report generator and graph queries use the read replica on primary/replica connections [PR #7201] (v2.15.1).

### Columns and data sources
- Emails reports offer sent count, read, click and unsubscribe ratios, clicks and unique clicks. Click ratios cannot exceed 100% [PR #3071] (~v2.5). Bounced and unsubscribed are separate stats, with bounce ratio and read delay columns [PR #4995] (v2.11.0).
- Asset, Email, Form and Page sources have "Campaign" and "Campaign ID" columns from `campaign_lead_event_log`. Rows can duplicate when an item has several log rows [PR #3780] (v2.8.0).
- ID columns link to the entity's `/view` page. A hard-coded list of entities with view or edit pages was rejected as fragile [PR #9768] (v3.3.3). Numeric aggregate columns [PR #9467] (v3.2.2) and user, owner and stage ID columns [PR #11773] (~v5.0) are not linked.
- Boolean and select Contact fields display 0 [PR #10167] (~v4.0.2). Boolean custom fields show their real Yes/No value; the column type becomes `normalized_bool` to stop double formatting [PR #14782] (v5.2.4).
- Date columns show the configured date format without a time [PR #12168] (~v5.0).
- Form-result sources can include columns from objects mapped to form fields [PR #11927] (~v5.0). `ReportHelper::getStandardColumns()` is reusable outside `ReportBuilderEvent` [PR #10898] (~v4.2.0).
- Page Hits has a "Time Spent" column, empty when `date_left` is not set [PR #15141] (v7.0.0).

### Report view and builder UI
- A new Report loads the default source's columns without switching sources, and the source list shows translated labels [PR #8541] (v3.0.0).
- The "System report?" toggle is labelled "Visible for all logged-in users". "Private report" was rejected as ambiguous [PR #13496] (v5.1.0). behaviour.md records that the flag has no effect on visibility in 7.x [PR #13496].
- The list shows a Data Source column that cannot be sorted, because sorting would use the untranslated key [PR #12749] (~v5.1).
- Column-header sorting works and is kept [PR #14096] (~v5.2), and stays on the current Report [PR #15387] (v7.0.0).
- The SQL query shows on the detail page in dev, and when `debug` is true. Why: to check queries on production [PR #11397] (~v5.0).
- The date range sits above the table, and the Filters panel appears only when there are dynamic filters [PR #16204] (v7.2.0). Quick filters (Today to Last 90 days) fill the range [PR #16205] (v7.2.0).
- The details page shows tags [PR #14832] (v7.0.0) and has a Clone action [PR #17450] (unreleased 7.x). The list has an "Has scheduled reports" quick filter, `is:scheduled` [PR #17449] (unreleased 7.x).

### Export
- CSV and Excel exports include the header and every row [PR #2628] (v2.2.1) [PR #3583] (v2.7.1), and apply the active dynamic filters [PR #3536] (v2.7.1).
- CSV is streamed in batches [PR #3701] (v2.8.0) with no row cap [PR #6530] (v2.14.2). The batch size is `report_export_batch_size` (1000); moving export onto the scheduler classes was deferred, and XLSX stays unbatched [PR #7220] (v3.1.0).
- HTML entities are decoded in the table and in every export format [PR #4088] (v2.9.0).
- `csv_always_enclose` (default off) quotes every CSV field, including empty ones. It is opt-in so default output does not change [PR #7049] (v2.15.1).
- A Totals row appears in the view and in exports when the Report has a calculated column. The AVG total has 4 decimals. Totals are computed in `ReportDataResult` [PR #12104] (v5.0.0).
- Aggregated boolean columns stay numeric in Excel [PR #11298] (~v4.4.1).
- Excel uses PhpSpreadsheet [PR #8286] (v3.0.0), upgraded to 4.x on a patch branch for security [PR #15016] (v5.2.6).
- Long exports dispatch `JobExtendTimeEvent` for hosted job backends ("unforking") [PR #15322] (v7.0.0).

### Scheduled reports
- Scheduling stores only the next run in `reports_schedulers`, and nothing is sent until `mautic:reports:scheduler` runs [PR #5205] (v2.12.0). The 7.x command name is `mautic:reports:scheduler`, with no alias [code: app/bundles/ReportBundle/Scheduler/Command/ExportSchedulerCommand.php:18-21 @7.x].
- The To field must hold valid addresses [PR #5205] (v2.12.0). Validation errors show above the form and highlight the tab [PR #5588] (v2.12.2).
- A scheduled Report covers only its period (a daily Report has the last day). The implementation debate in review was left open [PR #6220] (v2.15.0).
- Unpublished Reports are not sent [PR #8330] (v3.0.1). Each email has only its own attachment [PR #6872] (v2.15.1).
- Aggregator columns use the aggregator alias and type in scheduled exports [PR #7266] (v2.15.2).
- "Send report now" adds a NOW unit that exports once in the background and then unschedules. The button is hidden for scheduled Reports because it would reset the schedule. It went to a feature release, not a patch, under semantic versioning [PR #7432] (v3.3.0).
- Oversized CSVs are zipped. A zip that still does not fit is kept and linked, for logged-in Users only [PR #7432] (v3.3.0). Setting `report_export_max_filesize_in_bytes` to 0 forces a link [PR #11342] (~v5.0).
- Attached files are deleted after sending and linked zips after 7 days. Why: files piled up on disk [PR #13405] (v5.1.0). Under a queued mailer the attachment stays on disk until the queued message is sent [PR #15052] (v5.2.7).
- `--cleanup-only` (`-co`) runs only the 7-day cleanup. Why: a send and a cleanup running at once sent duplicate emails, so cleanup can have its own cron entry [PR #16077] (v7.2.0).
- The Schedule tab shows recipients and example dates for every frequency. Mautic 5 had hidden them (issue mautic/mautic#14665) [PR #14932] (v5.2.5).
- Deleting a Report stops its scheduled emails, and the delete prompt now says so [PR #17446] (unreleased 7.x).

### Reports API
- `GET /api/reports/{id}` returns compiled `data` and `totalResults` [PR #244] (~v1.0). It accepts `limit`, `page`, `dateFrom` and `dateTo`. Why: reports of 500k rows killed requests [PR #6841] (v2.15.0).
- Reports can be created, edited and deleted through the API. No endpoint describes sources and columns [PR #13378] (v5.1.0).
- `isScheduled` is serialised [PR #15131] (v7.0.0).

### Dashboard: layouts, date range and cache
- Exported or uploaded layouts live in a per-User directory; files in the root directory are global. Applying a layout looks in the User directory first [PR #1678] (v1.4.0).
- If no widgets exist and `default.json` cannot be written, the default dashboard still loads. `dashboard_import_user_dir` relocates User layouts [PR #6828] (v2.15.0).
- New installs ship fewer default widgets, because most are not useful to everyone and add database load [PR #7155] (v2.15.1).
- Widgets load one by one over AJAX [PR #9386] (v3.3.0), with placeholder graphs while loading [PR #13392] (v5.1.0).
- Widget data is cached under `cached_data_timeout` minutes (default 10). The TTL was once passed as minutes where seconds were expected [PR #6798] (v2.15.0). The cache key includes the locale [PR #2184] (v2.1.0).
- Changing the date range clears the widget cache [PR #1691] (v1.4.0). It also clears the cache-provider entries, not only the legacy files [PR #13863] (v5.1.1).
- `WidgetDetailEventFactory` builds widget events with a cache provider. escopecz said the legacy filesystem cache would go "in M6" [PR #7785] (v5.1.0). It is still in 7.x: `WidgetDetailEvent` falls back to `CacheStorageHelper` when no provider is injected, and `clearDashboardCache()` always clears the legacy files [code: app/bundles/DashboardBundle/Event/WidgetDetailEvent.php:207-215,346-349 @7.x] [code: app/bundles/DashboardBundle/Model/DashboardModel.php:258-266 @7.x].
- A cache timeout of 0 disables the cache; before, 0 meant never expire. Maintainers changed the code to match the tooltip rather than document -1 [PR #14467] (v5.2.4). In 7.x a global 0 is mapped to -1, and a widget timeout of null or -1 takes that default [code: app/bundles/DashboardBundle/Model/DashboardModel.php:212-221 @7.x].
- The widget menu says "previously stored data" or "just retrieved latest data". Removing cache information altogether was rejected, because users must know data may be stale [PR #13333] (~v5.2).
- Quick date filters apply a preset range to every widget [PR #14014] (~v5.2).

### Dashboard widgets
- One failing widget shows a generic, translatable error and logs the exception. escopecz rejected showing the exception text, which may contain secrets [PR #15989] (v7.1.0).
- Recent activity entries from the system (user ID missing or 0) are not linked. The check uses the ID, not the translated name [PR #14396] (~v5.2.2). Routes that do not exist are not linked [PR #220] (~v1.0).
- A widget whose Report was deleted shows a "deleted / no data" message [PR #5196] (v2.12.0).
- Report graph widgets render pie, table [PR #1968] (~v2.0.1) and line graphs [PR #10209] (~v4.0.2) [PR #11584] (~v5.0). The Emails source has a "Report View (Table)" graph that shows about 10 rows and a "View Full Report" link [PR #14827] (v7.0.0).
- The "Segments build time" widget lists the slowest segment rebuilds; it shows no days [PR #12398] (~v5.0).
- The Upcoming Emails query uses `idx_scheduled_events` and an inner join, and must finish quickly on large instances [PR #16101] (v7.2.0).
- Widget tiles scroll vertically when content is taller than the tile [PR #15888] (v7.2.0), without needless scrollbars on default widgets [PR #17232] (v7.2.1).
- Height options are named with the pixel value in brackets, such as "Extra small (365px)" [PR #13587] (v5.1.0). "Pre-defined dashboard" was preferred over "template" or "preset" [PR #13364] (v5.1.0) [PR #13614] (v5.1.0).
- Pre-defined dashboards state their widget count and purpose [PR #14011] (~v5.2). "Forms and Assets" and "Landing pages" were added [PR #14013] (~v5.2).
- `/api/data/{widget}` rejects an unknown `timeUnit` with HTTP 400 and honours `cacheTimeout=0` [PR #6041] (v2.14.0).

### Charts and stats
- The dashboard map converts English country names to ISO codes whatever the UI language [PR #1321] (~v1.2.4).
- Email graphs count weeks correctly over ranges longer than a month [PR #10543] (~v4.2.0) and put day stats on the right day [PR #11544] (~v4.4.4).
- `StatsBundle` collects chart stats by dispatching an aggregate-stat event, so third parties can inject stats [PR #9757] (v4.0.0).

### Extension points and internals
- `REPORT_QUERY_PRE_EXECUTE` lets plugins alter the query [PR #6036] (v2.14.0), and fires before the count query so totals match [PR #6330] (v2.14.1).
- `Report.system` is a back-ticked column name, because `system` is reserved in MySQL 8 [PR #6936] (v2.15.1).
- Report and Dashboard views moved to Twig [PR #11980] (v5.0.0) [PR #11791] (v5.0.0).
- ReportBundle, Dashboard and related controllers receive models by injection [PR #16620] (v7.2.0) [PR #16634] (v7.2.0). Nine ReportBundle services moved to autowired `services.php` [PR #16786] (v7.2.0).

## 3. Regression catalogue
| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| Several filters failed to save after one was deleted | New rows get unique indices | [PR #6252] | 2.14.1 |
| New filters overwrote existing ones | New filters append | [PR #3635] | 2.7.1 |
| Filter on read ratio was fatal | Formula columns can be filtered | [PR #3632] | 2.7.1 |
| Bounce or unsubscribe ratio filter returned 500 | Aggregated ratio filters work | [PR #7070] | 2.15.1 |
| URL "contains" filter failed | Text operators work on URL columns | [PR #6116] | 2.14.0 |
| UTM "contains" filter returned 500 | Text columns support contains, startsWith, endsWith | [PR #13867] | 5.2 |
| "Empty" filter returned nothing | NULL or `''` matches | [PR #7746] | 2.16.0 |
| Contact with empty field missing from `!=` | `neq` includes NULL | [PR #10043] | 4.3 |
| Date empty/not empty failed on MySQL 8 | IS NULL / IS NOT NULL only | [PR #10194] | 4.2.0 |
| AND/OR with tag filters wrong; error on type change | Correct logic, no error | [PR #12403] | 5.0.0 |
| Empty filter value returned 500 on save | Report saves | [PR #12569] | 5.1.0 |
| Empty OR filter broke the view | Empty filter skipped; no empty OR group | [PR #16125] | 7.2.0 |
| Boolean aggregator limited filter operators | Operators unaffected | [PR #12688] | 5.0 |
| "Is published" filter had no value input | Yes/No radio, saved | [PR #14909] | 5.2.6 |
| Tag filter value reached SQL raw | Values cast to integers | [PR #17129] | 7.2.1 |
| Tag detail page crashed with an empty-tag Report filter | Tag usages load | [PR #15134] | 6.0.3 |
| Disabling "dynamic" on a filter was ignored | Only dynamic filters show | [PR #4205] | 2.9.0 |
| Dynamic filter input empty despite a configured value | Config value is the default | [PR #15160] | 7.0.0 |
| Datetime dynamic filter used LIKE | Configured operator used | [PR #4756] | 2.10.1 |
| NULL-dated rows missing | Included by `applyDateFilters()` | [PR #5212] | 2.12.0 |
| Single-day range included the next day | Only that day | [PR #11256] [PR #15539] | 4.4.0, 7.0.0 |
| Date filter missed Contacts in non-UTC instance | Date values not shifted | [PR #10800] | 4.2.1 |
| Datetime filter time shifted on each save | Time preserved | [PR #15393] | 7.0.1 |
| API `dateTo` with time returned rows to midnight | API keeps the exact time | [PR #15532] | 7.0.0 |
| Relative filters frozen on save | Evaluated on each run | [PR #17256] | unreleased 7.x |
| SUM gave 2 instead of 6 | Aggregates without DISTINCT | [PR #4398] | 2.9.0 |
| AVG rounded to integers | Decimals kept in view and exports | [PR #11273] [PR #11514] | 5.0.0 |
| Saving with calculated columns gave empty `SUM()` | Report saves | [PR #11538] | 5.0 |
| Group by Campaign ID returned 500 | Group-only columns joined | [PR #5961] | 2.13.1 |
| Aggregator-only column caused SQL error | Joins prepared for it | [PR #6173] | 2.14.0 |
| Page Hits GROUP BY + COUNT returned 500 under ONLY_FULL_GROUP_BY | Aggregator-only target not raw-selected; others added to GROUP BY | [PR #17099] | 7.2.0 |
| Order by Clicks: unknown column | Order and group by computed columns | [PR #7085] | 2.15.1 |
| Group by broke pagination | Every page filled | [PR #5921] | 2.13.1 |
| Submission date exported as 10 pm | `groupByFormula` only when grouping by it | [PR #7980] | 2.16.1 |
| Duplicate custom-field aliases broke SQL | Numeric suffixes | [PR #6728] | 2.15.0 |
| Alias like `8e296a06` broke SQL | Aliases sanitised | [PR #9062] | 3.1.1 |
| Contacts report with company field returned 500 | Company join idempotent | [PR #9973] | 4.0.0 |
| Ratio columns sorted as text | Numeric sort | [PR #16126] | 7.2.0 |
| Sorting redirected to Report 1 | Sort stays on the Report | [PR #15387] | 7.0.0 |
| Header sorting did nothing | Sort works and persists | [PR #14096] | 5.2 |
| Plugin query changes missing from totals | Pre-execute event before count | [PR #6330] | 2.14.1 |
| Export capped at 10k; memory leak | Full export; SQL count | [PR #6530] | 2.14.2 |
| Export missing first row | Header plus all rows | [PR #2628] [PR #3583] | 2.2.1, 2.7.1 |
| Export ignored dynamic filters | Active filters applied | [PR #3536] | 2.7.1 |
| `&` shown encoded | Decoded in view and exports | [PR #4088] | 2.9.0 |
| HTML/Excel dropped aggregated columns | Same columns in every format | [PR #7872] | 2.16.1 |
| Excel showed Yes/No for SUM of booleans | Numbers | [PR #11298] | 4.4.1 |
| Boolean custom field always "Yes" | Real value | [PR #14782] | 5.2.4 |
| 0 shown blank for boolean/select fields | 0 shown | [PR #10167] | 4.0.2 |
| Numeric count column linked | Not linked | [PR #9467] | 3.2.2 |
| Stage or owner ID linked to 404 | Not linked | [PR #11773] | 5.0 |
| Unpublished scheduled Report emailed | Skipped | [PR #8330] | 3.0.1 |
| Second scheduled email had both files; queue mode had none | One attachment each | [PR #6872] | 2.15.1 |
| Scheduled Report with COUNT column: undefined index | Aggregator alias and type | [PR #7266] | 2.15.2 |
| Scheduled email failed under queued transport | Sends; file kept until sent | [PR #15052] | 5.2.7 |
| Schedule tab hid recipients and dates | Shown for every frequency | [PR #14932] | 5.2.5 |
| Duplicate emails when send and cleanup overlapped | `--cleanup-only` separates them | [PR #16077] | 7.2.0 |
| `isScheduled` missing from API | Serialised | [PR #15131] | 7.0.0 |
| Report API returned 500k rows | Paginated | [PR #6841] | 2.15.0 |
| Date range change took 10 min to show | Cache cleared on range change | [PR #1691] [PR #13863] | 1.4.0, 5.1.1 |
| Cache timeout 0 cached forever | 0 disables; negatives rejected | [PR #14467] | 5.2.4 |
| Widget cache expired after about a year | TTL in seconds from minutes | [PR #6798] | 2.15.0 |
| Widgets kept old language | Cache varies by locale | [PR #2184] | 2.1.0 |
| One widget error gave a dashboard 500 | Generic error on that widget only | [PR #15989] | 7.1.0 |
| Deleted Report broke its widget | "Deleted / no data" message | [PR #5196] | 2.12.0 |
| Unwritable dashboards dir redirected to import | Default dashboard loads | [PR #6828] | 2.15.0 |
| "Most hit email redirects" widget empty | Empty filters ignored; full end day | [PR #8460] [PR #11086] | 3.0.1, 4.4.1 |
| Best send hour widget failed with a segment filter | Widget loads | [PR #14358] | 5.2.1 |
| System audit entries linked to a missing User | Unlinked, checked by ID | [PR #14396] | 5.2.2 |
| Audit log widget broke after Contact deletion | Widget loads | [PR #14541] | 5.2.3 |
| Upcoming Emails query timed out | Index-backed query | [PR #16101] | 7.2.0 |
| All widgets showed scrollbars | Only oversized ones scroll | [PR #17232] | 7.2.1 |
| Line report graph broken on dashboard | Renders | [PR #10209] [PR #11584] | 4.0.2, 5.0 |
| Invalid `timeUnit` on `/api/data` | HTTP 400 with valid units | [PR #6041] | 2.14.0 |
| Email week graph wrong over a month | Correct counts | [PR #10543] | 4.2.0 |
| Email day graph on previous day | Correct day | [PR #11544] | 4.4.4 |
| MySQL 8: `system` reserved word | Column quoted | [PR #6936] | 2.15.1 |

## 4. Feature timeline
| Version | Change | PR |
|---|---|---|
| 1.x | Reports API; per-User dashboard layouts; widget cache indicator | [PR #244] [PR #1678] [PR #1691] |
| 2.5–2.9 | Email metrics; campaign columns; GROUP BY and calculated columns; AND/OR filter glue | [PR #3071] [PR #3780] [PR #3824] [PR #4261] |
| 2.11–2.12 | Bounce/unsubscribe split; scheduled Reports and `mautic:reports:scheduler` | [PR #4995] [PR #5205] |
| 2.14–2.15 | Query pre-execute event; `/api/data` unit check; API pagination; period-limited schedules; `csv_always_enclose`; read replica | [PR #6036] [PR #6041] [PR #6841] [PR #6220] [PR #7049] [PR #7201] |
| 3.0–3.3 | PhpSpreadsheet; `report_export_batch_size`; AJAX dashboard; Send report now; join only needed tables | [PR #8286] [PR #7220] [PR #9386] [PR #7432] [PR #7411] |
| 4.0 | Aggregate stat service | [PR #9757] |
| 5.0.0 | Tag filters; debug SQL display; Totals in exports; Segments build time widget; Twig views | [PR #11346] [PR #11397] [PR #12104] [PR #12398] [PR #11980] |
| 5.1.0 | Data Source list column; LIKE auto-wildcards; API write endpoints; export cleanup; widget placeholders; height labels; widget event factory | [PR #12749] [PR #13080] [PR #13378] [PR #13405] [PR #13392] [PR #13587] [PR #7785] |
| 5.2 | Friendly cache text; new pre-defined dashboards; dashboard quick dates; clone filter row | [PR #13333] [PR #14013] [PR #14014] [PR #14132] |
| 5.2.4 | Cache timeout 0 disables | [PR #14467] |
| 6.0.0 | Page Hits drops NULL `date_hit` rows | [PR #14486] |
| 7.0.0 | Report View (Table) graph; report tags; `isScheduled` in API; Time Spent; `JobExtendTimeEvent`; exact API `dateTo` | [PR #14827] [PR #14832] [PR #15131] [PR #15141] [PR #15322] [PR #15532] |
| 7.0.1 | String operators and timezone tooltip on date filters | [PR #15393] |
| 7.1.0 | Dynamic filter operator; widget-created flash; per-widget error isolation | [PR #15366] [PR #15378] [PR #15989] |
| 7.2.0 | `--cleanup-only`; prefix/suffix columns; date range above table; quick filters; GROUP BY rebuild; injected models | [PR #16077] [PR #16126] [PR #16204] [PR #16205] [PR #17099] [PR #16620] |
| 7.2.1 | Tag filter integer cast; widget scrollbar fix | [PR #17129] [PR #17232] |
| Unreleased 7.x | Relative date filters; delete warns about schedules; `is:scheduled`; Clone on details | [PR #17256] [PR #17446] [PR #17449] [PR #17450] |

## 5. Removed, deprecated, replaced
| What | Replaced by | PR | Version |
|---|---|---|---|
| PHP-side row counting | Wrapping count query | [PR #6530] | 2.14.2 |
| GROUP_CONCAT aggregator | Not selectable in 7.x | [PR #6289] | 2.14.1 |
| PHPExcel | PhpSpreadsheet (4.x from 5.2.6) | [PR #8286] [PR #15016] | 3.0.0 |
| Oversized scheduled export as link only | Zip, then attach or link | [PR #7432] | 3.3.0 |
| `ReportGeneratorEvent::applyTagFilter` | `MauticReportBuilder` | [PR #12403] | 5.0.0 |
| PHP templates for Report and Dashboard | Twig | [PR #11980] [PR #11791] | 5.0.0 |
| AVG rounded to integer | Unrounded AVG | [PR #11273] | 5.0.0 |
| "System report?" label | "Visible for all logged-in users" | [PR #13496] | 5.1.0 |
| Legacy filesystem widget cache | Cache provider (legacy path still present in 7.x; removed in 8.x) | [PR #7785] | 5.1.0 |
| `cached_data_timeout` 0 = endless | 0 = disabled | [PR #14467] | 5.2.4 |
| `date_hit IS NULL` branch for Page Hits | Removed | [PR #14486] | 6.0.0 |
| `CONCAT(…,'%')` ratio formulas | Numeric formula plus `suffix` | [PR #16126] | 7.2.0 |
| Date range in the Filters panel | Above the table | [PR #16204] | 7.2.0 |
| `getModel('report')` in controllers | Injection | [PR #16620] [PR #16634] | 7.2.0 |
| Relative filters converted on save | Stored relative; older saved Reports keep fixed dates | [PR #17256] | unreleased 7.x |

## 6. Maintainer norms for this area
- Never put raw filter values in SQL; cast or bind them. Typed binding is preferred [PR #17129].
- Never show exception messages in the UI; log them and show a generic message [PR #15989].
- Preserve the Report shape the user configured when fixing SQL validity; add to GROUP BY rather than drop columns [PR #17099].
- Reports must not load full result sets into PHP, should join only what they need, and must use indexes on large tables [PR #6530] [PR #7411] [PR #4460] [PR #16101].
- Make code match a setting's tooltip rather than document a workaround [PR #14467].
- Do not offer sorting on columns that display a translated key [PR #12749].
- Weigh filter-semantics changes for BC and index use; consistency with segment filters decided `like` [PR #13080].
- Put display symbols in `prefix`/`suffix`, not in the SQL formula [PR #16126].
- Bug fixes need a regression test that fails without the fix [PR #15160] [PR #17099] [PR #8541].
- Bug fixes target the patch branch; features go to the next minor, never a patch [PR #7432] [PR #14909] [PR #17129].
- Use "pre-defined dashboard", not "template" or "preset" [PR #13364].
- Do not use double quotes in INI translation strings [PR #14908].
- `app/bundles/ReportBundle/` changes need CODEOWNERS review [PR #17099].

## 7. Open questions
- Resolved: the command is `mautic:reports:scheduler`, with no alias in 7.x. The `mautic:report:scheduler` in the test steps of [PR #6220] is a typo [code: app/bundles/ReportBundle/Scheduler/Command/ExportSchedulerCommand.php:18-21 @7.x].
- Resolved: the legacy dashboard cache promised for removal "in M6" [PR #7785] is still in 7.x as a fallback and in `clearDashboardCache()` [code: app/bundles/DashboardBundle/Event/WidgetDetailEvent.php:346-349 @7.x]. 8.x removes it (see version-notes.md) [PR #7785].
- Resolved: GROUP_CONCAT [PR #6289] is in the 2.14.1 aggregator form but not in 7.x, where it appears only in the builder's aggregate-function list [code: app/bundles/ReportBundle/Form/Type/AggregatorType.php:29-35 @7.x].
- Resolved: [PR #17099] omits from SELECT only a column that is an aggregator target and not grouped [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:301-307 @7.x].
- Resolved: cache timeout 0 maps to -1 in `populateWidgetContent()` [PR #14467] [code: app/bundles/DashboardBundle/Model/DashboardModel.php:212-221 @7.x].
- Conflict with behaviour.md: the [PR #13496] tooltip says "No" limits the Report to its owner and roles with view-other permission. behaviour.md R12/R16 say the flag has no effect. behaviour.md wins [PR #13496].
- Conflict with behaviour.md: [PR #2164] says clearing a boolean dynamic filter sends an empty value. behaviour.md R39 says the clear button sends 2, which is ignored. behaviour.md wins [PR #2164].
- Conflict with behaviour.md: [PR #15393] and [PR #17256] speak of the User's timezone. behaviour.md R48 says relative periods use `default_timezone`. The author of [PR #15393] noted the User timezone is broken (issue mautic/mautic#15226). behaviour.md wins [PR #15393].
- Historical change: [PR #1691] cleared only the current User's cache. behaviour.md D10 says a clear now invalidates the shared tag for all Users [PR #13863].
- [PR #3780]: campaign columns can duplicate rows; no fix is recorded [PR #3780].
- [PR #8737]: whether report display times follow a changed system timezone was not settled [PR #8737].
- [PR #12104]: a reviewer flagged integer totals cast to strings in exports after merge [PR #12104].
- [PR #13080]: the index concern about leading wildcards was not addressed [PR #13080].
- [PR #11538]: calculated columns on unselected columns still produced empty `SUM()` in later testing [PR #11514].
- [PR #14467]: how a per-widget timeout of 0 behaves is not covered by the PR [PR #14467].
- [PR #16205]: whether the dashboard date picker gained the same quick filters is unclear; [PR #14014] already added dashboard quick dates [PR #16205].
- [PR #4088]: Excel row order was reported as reversed; no fix is recorded [PR #4088].

## 8. Coverage
The inputs cover 235 PRs in 3 chunks: 111 (2015–2021, plus [PR #7785] merged 2024), 87 (2021–2025) and 37 (2025–2026).
About 214 are substantive; the rest are refactors, CI or test-only PRs. [PR #14626] and [PR #13422] were misbucketed and are used only as norms.
A further 869 noise PRs (dependency bumps, translations, CI) were excluded upstream before chunking.
