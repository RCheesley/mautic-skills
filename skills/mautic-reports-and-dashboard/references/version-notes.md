# Reports, Dashboard and Stats: version notes

## 5.x / 6.x history
- Since 5.1, scheduled Reports show a paper-aeroplane icon in the list [docs: https://docs.mautic.org/en/7.2/reports/reports.html#schedule].
- The Dashboard was introduced in 1.4.0 and enhanced in 2.0 [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html].
- No other 5.x/6.x-specific behaviour differences for this area appear in the inputs. PR-derived history is pending (pr-history.md).

## 7.x
- The 7.x branch, after 7.2.1 and not yet released, contains relative date filters (`RelativeDateHelper`; [PR #17256]) and the `is:scheduled` search command ([PR #17449]). The user docs describe them only on the 8.0 branch [code: app/bundles/ReportBundle/Helper/RelativeDateHelper.php:11-93 @7.x] [code: app/bundles/ReportBundle/Entity/ReportRepository.php:46-68 @7.x] [docs: https://docs.mautic.org/en/8.0/reports/reports.html#relative-date-filters].
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
