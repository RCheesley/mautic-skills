# Reports, Dashboard and Stats: version notes

## 5.x / 6.x history
- Since 5.1, scheduled Reports show a paper-aeroplane icon in the list [docs: https://docs.mautic.org/en/7.2/reports/reports.html#schedule].
- The Dashboard was introduced in 1.4.0 and enhanced in 2.0 [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html].
- 5.0.0: Report and Dashboard views move to Twig [PR #11980] [PR #11791]. Tag filters arrive on Contact-based sources, and the tag filter moves from `ReportGeneratorEvent` into `MauticReportBuilder` (UPGRADE-5.0.md) [PR #11346] [PR #12403]. AVG is no longer rounded [PR #11273] [PR #11514]. Exports get a Totals row when there is a calculated column [PR #12104]. The SQL shows on the detail page when `debug` is true [PR #11397]. The Segments build time widget is added [PR #12398]. `report_export_max_filesize_in_bytes = 0` forces a download link [PR #11342].
- 5.1: `like`/`notLike` add `%…%` when the value has no `%` [PR #13080]. Reports get API create, edit and delete [PR #13378]. Sent export files are deleted, and linked zips after 7 days [PR #13405]. "System report?" becomes "Visible for all logged-in users" [PR #13496]. The list gains an unsortable Data Source column [PR #12749]. Widget events come from `WidgetDetailEventFactory` with a cache provider [PR #7785]. Clearing the dashboard cache also clears the provider cache from 5.1.1 [PR #13863].
- 5.2: text columns support contains/startsWith/endsWith [PR #13867]; header sorting works [PR #14096]; filter rows can be cloned [PR #14132]; the dashboard gets quick date filters and two new pre-defined dashboards [PR #14014] [PR #14013].
- 5.2.x patches: from 5.2.4 a `cached_data_timeout` of 0 disables the widget cache (before, it never expired) [PR #14467]; boolean custom fields show real values (5.2.4) [PR #14782]; the Schedule tab shows recipients again (5.2.5) [PR #14932]; boolean filters get a Yes/No input and PhpSpreadsheet moves to 4.x (5.2.6) [PR #14909] [PR #15016]; scheduled emails work with a queued mailer (5.2.7) [PR #15052].
- 6.0.0: Page Hits Reports no longer include rows with a NULL `date_hit` in a date range [PR #14486]. 6.0.3: the tag detail page tolerates Reports with empty tag filters [PR #15134]. No other 6.x differences were found in 235 PRs [PR #14486].

## 7.x
- The 7.x branch, after 7.2.1 and not yet released, contains relative date filters (`RelativeDateHelper`; [PR #17256]) and the `is:scheduled` search command ([PR #17449]). The user docs describe them only on the 8.0 branch [code: app/bundles/ReportBundle/Helper/RelativeDateHelper.php:11-93 @7.x] [code: app/bundles/ReportBundle/Entity/ReportRepository.php:46-68 @7.x] [docs: https://docs.mautic.org/en/8.0/reports/reports.html#relative-date-filters].
- 7.0.0: the API keeps an exact `dateTo` time while the UI uses 23:59:59 [PR #15532]; `isScheduled` is serialised [PR #15131]; Page Hits gains Time Spent [PR #15141]; the Emails source gains a Report View (Table) graph [PR #14827]. 7.0.1: date filters accept string operators, compared against the UTC string [PR #15393].
- 7.1.0: dynamic filters show their operator [PR #15366]; a failing widget shows a generic error instead of breaking the dashboard [PR #15989].
- 7.2.0: `mautic:reports:scheduler --cleanup-only` [PR #16077]; `prefix`/`suffix` columns with numeric sorting [PR #16126]; the date range moves above the table with quick filters [PR #16204] [PR #16205]; GROUP BY is rebuilt for `ONLY_FULL_GROUP_BY` [PR #17099]; Report and Dashboard controllers get injected models [PR #16620] [PR #16634]. 7.2.1: tag filter values are cast to integers (security fix) [PR #17129].
- 7.2 deprecates the service alias `mautic.report.helper.report`; inject `Mautic\ReportBundle\Helper\ReportHelper` instead [code: app/bundles/ReportBundle/Config/services.php:50-51 @7.x].
- 7.x already has a tag-aware cache provider for widgets. The legacy filesystem cache is a fallback used only when no provider is injected [code: app/bundles/DashboardBundle/Event/WidgetDetailEvent.php:289-305,346-349 @7.x].
- `Report` has an API Platform `#[ApiResource]` alongside the legacy `loadApiMetadata`. Which of the two backs `/api/reports` is outside this area (open question) [code: app/bundles/ReportBundle/Entity/Report.php:28-45,232-261 @7.x].
- The Mautic 7.x devdocs say Symfony attribute validation is enabled, so attribute constraints on entities work [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms_advanced.html#using-entity-attribute-constraints].

## 8.x delta (8.x @ 11599729491; three-dot diff from 7.2.1)
Branch caveat: 7.x-only work (7.2.1 and the unreleased PRs after it) is not yet merged forward into 8.x. Do not read features missing on 8.x as removed.
- **Report events by class.** All 8 report events are dispatched by class: `ReportBuilderEvent`, `ReportGeneratorEvent`, `ReportQueryEvent`, `ReportDataEvent`, `ReportGraphEvent`, `ReportScheduleSendEvent`, `ColumnCollectEvent`, `PermanentReportFileCreatedEvent`. The `ReportEvents` constants still exist, so a listener keyed on `ReportEvents::REPORT_ON_BUILD` compiles but never fires [PR #17200] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/reports.html].
- Report CRUD events (`REPORT_PRE_SAVE`, `POST_SAVE`, `PRE_DELETE`, `POST_DELETE`) are still dispatched by name from `ReportModel`, because the 8.x CRUD groups still dispatch with `$name` variables [code: app/bundles/ReportBundle/Model/ReportModel.php @8.x].
- `ReportDataEvent`, `ReportGeneratorEvent` and `ReportGraphEvent` become `final`, so tests must not mock them. `Report::get*()` getters are typed `array`/`?array` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- **Dashboard.** `DashboardEvents` is deleted and replaced by `WidgetTypeListEvent`, `WidgetFormEvent`, `GenerateWidgetDetailEvent` and `PreLoadWidgetDetailEvent`. `WidgetDetailEvent` becomes abstract [PR #17216] [PR #17654].
- **Widget cache.** The legacy filesystem widget cache is removed. `WidgetDetailEvent::setCacheDir()` and `setCacheTimeout()` are removed, `$cacheProvider` is required, and `setTemplateData()` loses `$skipCache` [PR #17033] [PR #17034].
- `WidgetDetailEventFactory` loses its `UserHelper`, `CoreParametersHelper` and `PathsHelper` arguments, and `Widget::getParams()`/`getTemplateData()` return `array` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- On 8.x a cache miss returns `null` (not `false`). Widget cache lives in `cache_adapter` and is dropped by a cache clear [PR #17033] [PR #17155].
- **Stats.** `StatEvents` is deleted; subscribe to `AggregateStatRequestEvent::class` [PR #17654].
- 8.0 user docs add the relative date filter reference and the `is:scheduled` filter. The Dashboard docs are unchanged [docs: https://docs.mautic.org/en/8.0/reports/reports.html#relative-date-filters].
- The REST API docs for reports and stats are unchanged in 8.0 [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/].

## Writing code that runs on 7.x and 8.x
- Key subscriptions on the event class, and add the 7.x constant key guarded by `defined()`:
  ```php
  $events = [ReportBuilderEvent::class => ['onReportBuilder', 0]];
  if (defined(ReportEvents::class.'::REPORT_ON_BUILD')) { // 7.x dispatches by name
      $events[ReportEvents::REPORT_ON_BUILD] = ['onReportBuilder', 0];
  }
  ```
  For `DashboardEvents` and `StatEvents`, which are deleted on 8.x, use string-literal checks such as `defined('Mautic\DashboardBundle\DashboardEvents::DASHBOARD_ON_MODULE_DETAIL_GENERATE')`, and use `class_exists()` for the 8.x-only `GenerateWidgetDetailEvent`. Do not reference these classes unguarded. On 8.x, the shared parent `WidgetDetailEvent` can be type-hinted in handlers [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- Inject `CacheProviderInterface` and treat both `null` and `false` as a miss [PR #17033].
- Do not mock final event classes; build real instances [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- See mautic-upgrades-and-versions for the cross-bundle event table.

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
