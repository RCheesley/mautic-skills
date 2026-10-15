# Reports and Dashboard: what the official docs say

Sources:
- User docs Reports: https://docs.mautic.org/en/7.2/reports/reports.html (8.0: https://docs.mautic.org/en/8.0/reports/reports.html, changed)
- User docs Dashboard: https://docs.mautic.org/en/7.2/dashboard/dashboard.html (8.0 identical)
- Roles: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html
- Devdocs Reports extension: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html (8.0 changed)
- REST API: https://devdocs.mautic.org/en/7.2/rest_api/reports.html, https://devdocs.mautic.org/en/7.2/rest_api/stats.html (8.0 identical)

Where the docs disagree with 7.x code, the disagreement is flagged with **Code differs** and the code reference.

## 1. Reports (user docs)
- Open Reports from the left menu; create one with **+New**. The tabs are Details, Data, Graphs and Schedule; the buttons are **Save & Close** and **Apply** [docs: https://docs.mautic.org/en/7.2/reports/reports.html#schedule].
- The Details tab has Name, Data source, Description, Published, Visible for all logged-in users, Owner, and Dynamic filters settings (Opened by default, Hide date range) [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data-sources].
- Published = Yes makes the Report active, "ready to send when scheduled" [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data-sources]. The code agrees: the scheduler skips unpublished Reports [code: app/bundles/ReportBundle/Model/ReportExporter.php:67-68 @7.x].
- Visible for all logged-in users = No limits the Report to its owner and Users who can view others' Reports [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data-sources]. **Code differs**: the `system` flag is not read; visibility depends only on `viewother` and the owner [code: app/bundles/ReportBundle/Controller/ReportController.php:68-70 @7.x].
- Data sources are shown as "<Parent> <Child>". The parent gives a summary; the child gives granular Contact behaviour including Custom Fields [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data-sources].
- Emails columns [docs: https://docs.mautic.org/en/7.2/reports/reports.html#email-report-columns]:
  - Sent count, Read count, Read ratio.
  - Click-through count (unique Contacts who clicked any link), Click-through rate, Click-to-open rate.
  - Unsubscribed, Unsubscribed ratio, Unsubscribe-to-Open ratio.
  - Bounced, Bounced ratio.
  - Clicks (total), Clicks ratio, Unique clicks (sum of per-link unique clicks), Unique clicks ratio.
  - DNC Preferences.
  - For unique clickers, use Click-through count, not Unique clicks.
- Data tab:
  - Click a column to add or remove it. Including ID is recommended.
  - Order supports multiple rows, and "the last one in the Order list is applied first". **Code differs (open question)**: see behaviour.md §14.1.
  - Filters need not be displayed columns.
  - Dynamic = Yes lets viewers change the filter from the Filters panel.
  - Group by gives one row per group.
  - Calculated columns (count, avg, sum, min, max) exist only with a group-by.

  [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data]
- "Exports do not include the totals row" [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data]. **Code differs**: CSV and XLSX write totals after the last row [code: app/bundles/ReportBundle/Model/CsvExporter.php:39-46 @7.x].
- Graphs depend on the source and can be used in Dashboard widgets [docs: https://docs.mautic.org/en/7.2/reports/reports.html#graphs].
- Schedule [docs: https://docs.mautic.org/en/7.2/reports/reports.html#schedule]:
  - Email Report = Yes; To is comma-separated.
  - Every can be: now (once, when saved); day (midnight in your time zone); week (chosen weekday, midnight); month (first/last + weekday, or Weekdays).
  - Since 5.1 a paper-aeroplane icon marks scheduled Reports.
- Cron: `php bin/console mautic:reports:scheduler [--report=ID] [--cleanup-only]` [docs: https://docs.mautic.org/en/7.2/reports/reports.html#cron-job-to-schedule-reports]. The docs do not state the retention period; the code keeps permanent zips for 7 days [code: app/bundles/ReportBundle/Model/ReportCleanup.php:9 @7.x].
- List options: Edit, Clone, **Export & Send** (emails a CSV link to your profile email), Delete [docs: https://docs.mautic.org/en/7.2/reports/reports.html#report-options].
- Quick filters: Today, Yesterday, Last 7/30/90 days [docs: https://docs.mautic.org/en/7.2/reports/reports.html#quick-filters].
- Export to CSV, Excel or HTML from the view dropdown. To download immediately, the docs suggest setting Schedule = No or now, saving, exporting, then resetting. Data is also available through the API [docs: https://docs.mautic.org/en/7.2/reports/reports.html#exporting-reports].
- Export requires the Reports **Export** permission [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#explaining-the-permission-options].

### 8.0 additions (behaviour present on the 7.x branch after 7.2.1, unreleased; [PR #17256] [PR #17449])
- Relative date filters [docs: https://docs.mautic.org/en/8.0/reports/reports.html#relative-date-filters]:
  - Expressions: `today`/`tomorrow`/`yesterday`; `this|last|next week|month|year`; signed intervals (`+1 week`, `-3 months 2 days`, `-2 days 12:34:56`); `N unit ago`; `first day of next month`; `birthday`, `anniversary`, `birthday +2 days`.
  - Not applied with Contains, Doesn't contain, Starts with, Ends with or In list.
  - Is equal to matches a whole period; Is not equal to matches outside it or empty.
  - Greater than and Less than or equal use the period end; Greater than or equal and Less than use the period start.
  - Expressions resolve in `default_timezone`.
  - Expressions are stored as typed.
  - For rolling windows, use Greater than or equal with `-7 days` or `first day of this month`.

  The code matches [code: app/bundles/ReportBundle/Helper/RelativeDateHelper.php:11-93 @7.x] [code: app/bundles/CoreBundle/Helper/DateTimeHelper.php:386-391 @7.x].
- The **Has scheduled Reports** filter and the `is:scheduled` search [docs: https://docs.mautic.org/en/8.0/reports/reports.html#schedule] [code: app/bundles/ReportBundle/Entity/ReportRepository.php:46-68 @7.x].

## 2. Dashboard (user docs)
- Each User composes their own Dashboard [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html].
- A global date range applies to all widgets, defaulting to 30 days ago to today. **Code**: `default_daterange_filter` = `-1 month` [code: app/bundles/CoreBundle/Config/config.php:709 @7.x]. *Upcoming Emails* and *Recent activity* ignore the range [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#date-range-filter].
- Line chart unit: 1 day → hours; 1–31 days → days; 32–100 → weeks; 101–1000 → months; more → years [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#date-range-filter].
- Add widget form: Name (defaults to the type), Type, Width 25/50/75/100% (default 100%; line charts are best at 100%, tables at 50%, pies at 25%), Height (5 presets). Too many widgets slow the page [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#widgets].
- Reorder widgets by dragging the widget name [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#widget-ordering].
- Export writes configuration only, with no data. Import is on the Dashboard Import page. "3 predefined dashboards" exist, and `default.json` is imported automatically when there are no widgets. Preview loads real data without saving; Apply deletes the current widgets [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#dashboard-import]. **Code**: 6 global files ship in `app/assets/dashboards/`.
- Widget cache expiry defaults to 10 minutes. The config key is not named; it is `cached_data_timeout` [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#widget-cache] [code: app/bundles/CoreBundle/Config/config.php:698 @7.x].
- Permissions:
  - Without view own/others for a bundle, a User cannot create widgets for it. Existing widgets show a no-permission message.
  - With view own only, widgets show own data.

  [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#dashboard-permissions] **Code differs**: listing types requires all of the bundle's permissions [code: app/bundles/DashboardBundle/Event/WidgetTypeListEvent.php:60-68 @7.x].

## 3. Developer docs: Reports extension
- 7.2: listen to `ReportEvents::REPORT_ON_BUILD`, `REPORT_ON_GENERATE`, `REPORT_ON_GRAPH_GENERATE`. 8.0: key on `ReportBuilderEvent`, `ReportGeneratorEvent`, `ReportGraphEvent` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/reports.html].
- Build: `checkContext`, `getStandardColumns($prefix)`, `getCategoryColumns()`, `addTable(context, [display_name, columns, filters])`, `addGraph(context, type, name)`. Filters default to the columns [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html#defining-a-report].
- Column keys: `label` and `type` (required), `alias`, `formula`, `link` (a route taking `objectAction`/`objectId`), `prefix`, `suffix`. Put `%` in `suffix`, not in `CONCAT`, or values sort as text (1%, 27%, 3%) [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html#column-definition].
- Filter keys: `list` (for `select`) and `operators` (see `MauticReportBuilder::OPERATORS`) [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html#filter-definition].
- Generate: a DBAL QueryBuilder plus join helpers [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html#generating-the-querybuilder].
- Graphs: check the context, clone the QueryBuilder per graph, use `ChartQuery`/`LineChart`, `getRequestedGraphs()`, `getOptions($graph)`, `setGraph()` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html#generating-graphs].
- Channels can declare `ReportModel::CHANNEL_FEATURE => ['table' => 'emails']` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/channels.html#listening-for-channel-features].
- Known example defects: the example uses the removed `CommonSubscriber`, and has mismatched aliases (`w` vs `v`) and graph ids [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html].

## 4. REST API: Reports and Stats
- `GET /api/reports/ID?dateFrom&dateTo&limit&page`:
  - Response: `totalResults` (the default range is 30 days ago to now), `data` (keyed by alias such as `email1`), `dataColumns`, `limit`, `page`, `dateFrom`, `dateTo`.
  - PHP library: `get($id, $limit, $page, $dateFrom, $dateTo)`.
  - No default `limit` is documented. Code: without `page`/`limit`, all rows are returned [code: app/bundles/ReportBundle/Controller/Api/ReportApiController.php:112-135 @7.x].

  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html#get-report]
- `GET /api/reports` returns `total` and `reports`. The docs say "Contact Reports available to the User" and "This list isn't filterable", and they describe `system` as all Users vs creator only [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html#list-reports].
- `POST /api/reports/new` returns 201 (example: source `email.stats`, columns `es.date_sent`, filters `{column, condition, value}`, graph `mautic.email.graph.line.stats`). `PATCH /api/reports/ID/edit` returns 200 or 404. `PUT` returns 200 or 201 and clears data first. `DELETE /api/reports/ID/delete` returns 200 [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html#create-report].
- The docs say "API won't return graphs" for `graphs`, yet the create/edit examples include `graphs` [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html#list-reports]. Code removes `graphs` only from the data response of `GET /{id}` [code: app/bundles/ReportBundle/Controller/Api/ReportApiController.php:64-101 @7.x].
- Stats API:
  - `GET /api/stats` lists 32 tables and their columns.
  - `GET /api/stats/TABLE` takes `start` (0), `limit` (30), `order[n][col|dir]` and `where[n][col|expr|val]`.
  - `expr` values: eq, neq, lt, lte, gt, gte, isNull, isNotNull, like, notLike, in, notIn, between.
  - "Tables require appropriate User permissions"; the mapping is not documented.

  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stats.html] This endpoint is not part of StatsBundle (see mautic-rest-api).

## 5. Procedures
- **Create a Report**: Reports > +New; fill in Details, then Data (columns, order, filters, group by, calculated columns), Graphs and Schedule; then Save & Close or Apply [docs: https://docs.mautic.org/en/7.2/reports/reports.html].
- **Schedule a Report**: on the Schedule tab set Email Report = Yes, fill in To and Every, and make sure cron runs `mautic:reports:scheduler` [docs: https://docs.mautic.org/en/7.2/reports/reports.html#schedule].
- **Rolling-date filter**: use a date column with Greater than or equal and `-7 days` [docs: https://docs.mautic.org/en/8.0/reports/reports.html#relative-date-filters].
- **Dashboard export/import**: export first, because Apply deletes the current widgets [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#dashboard-import].
- **Fetch report data**: `GET /api/reports/ID?dateFrom=YYYY-MM-DD&dateTo=YYYY-MM-DD&limit=N&page=P` [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html#get-report].

## 6. Terminology
- Capitalise product nouns: Report, Contact, Segment, Campaign, Email, Landing Page, Form, Asset, Focus Item, User, Role [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html].
- "Data source" (UI) = context / `source` (code). "Calculated columns" (UI) = aggregators (code). "Email Report" (UI) = `isScheduled` [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data].
- "Identified" vs "anonymous" Contacts in widget options [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#widgets].

## 7. Gaps in the docs
- The docs have no per-source column lists (except Emails), no operator list, no scheduler file paths, size limits or email template, and no full Report permission matrix [docs: https://docs.mautic.org/en/7.2/reports/reports.html].
- The Dashboard docs have no full widget type list (see code-map.md §5) and do not name the cache config key [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html].
