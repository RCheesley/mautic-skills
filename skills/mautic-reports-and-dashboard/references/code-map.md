# Reports, Dashboard and Stats: code map (Mautic 7.x)

All paths are relative to the repo root at 7.2.1. `RB` = `app/bundles/ReportBundle`, `DB` =
`app/bundles/DashboardBundle`, `SB` = `app/bundles/StatsBundle`. Each table row carries its citation.

## Contents
1. Entities and tables
2. Services and models
3. Events
4. Report contexts (full table)
5. Dashboard widget types (full table)
6. Routes, controllers, AJAX, views
7. Console command
8. Configuration parameters
9. Permissions
10. Extension contract
11. Tests

## 1. Entities and tables
| Entity | Table | Columns / notes | Citation |
|---|---|---|---|
| `Mautic\ReportBundle\Entity\Report` (extends `FormEntity`, implements `SchedulerInterface`, `UuidInterface`) | `reports` | `system`, `source`, `columns`, `filters`, `table_order`, `graphs`, `group_by`, `aggregators` (serialized arrays), `settings` (JSON), `is_scheduled`, `schedule_unit` (`NOW/DAILY/WEEKLY/MONTHLY`), `to_address`, `schedule_day` (`MO`..`SU`, `WEEK_DAYS`), `schedule_month_frequency` (`1`/`-1`), `uuid`, plus FormEntity columns. Carries an API Platform `#[ApiResource]` with groups `report:read`/`report:write`. | [code: app/bundles/ReportBundle/Entity/Report.php:28-48,167-217 @7.x] [code: app/bundles/ReportBundle/Scheduler/Enum/SchedulerEnum.php:9-35 @7.x] |
| `Mautic\ReportBundle\Entity\Scheduler` | `reports_schedulers` | `id`, `report_id` (FK, `ON DELETE CASCADE`), `schedule_date`. Immutable; at most one row per Report by convention only. | [code: app/bundles/ReportBundle/Entity/Scheduler.php:18-41 @7.x] |
| `Mautic\DashboardBundle\Entity\Widget` (extends `FormEntity`) | `widgets` | `name`, `type`, `width`, `height`, `cache_timeout`, `ordering`, `params` (array). Runtime-only fields: `template`, `errorMessage`, `cached`, `loadTime`, `templateData`. `toArray()` defines the export JSON shape. | [code: app/bundles/DashboardBundle/Entity/Widget.php:53-104,331-342 @7.x] |
| StatsBundle | none | In-memory DAOs: `StatsDAO`, `StatDAO`, `YearStat`…`HourStat`, `WeekStat` | [code: app/bundles/StatsBundle/Aggregate/Collection/DAO/StatsDAO.php:34-129 @7.x] |

Repositories: `ReportRepository` handles search commands and the widget Report list [code: app/bundles/ReportBundle/Entity/ReportRepository.php:46-135 @7.x]. `SchedulerRepository::getScheduledReportsForExport()` returns due schedulers [code: app/bundles/ReportBundle/Entity/SchedulerRepository.php:16-40 @7.x]. `WidgetRepository::updateOrdering()` [code: app/bundles/DashboardBundle/Entity/WidgetRepository.php:17-41 @7.x].

## 2. Services and models
| Class / service id | Path | Role |
|---|---|---|
| `ReportModel` (`mautic.report.model.report`) | `RB/Model/ReportModel.php:50` | CRUD and events, `buildAvailableReports` (`:187-224`), form lists (`:289-370`), `getReportData` (`:446-666`), `exportResults` (`:382-439`), dependency lookups (`:805-888`), read replica (`:893-901`) [code: app/bundles/ReportBundle/Model/ReportModel.php:50-901 @7.x] |
| `ReportGenerator` (not a service) | `RB/Generator/ReportGenerator.php:52-83` | Instantiates `MauticReportBuilder` and builds the form [code: app/bundles/ReportBundle/Generator/ReportGenerator.php:52-83 @7.x] |
| `MauticReportBuilder` (final, not a service) | `RB/Builder/MauticReportBuilder.php` | Report → DBAL QueryBuilder; `OPERATORS` at `:23-70` [code: app/bundles/ReportBundle/Builder/MauticReportBuilder.php:23-133 @7.x] |
| `ReportDataResult` | `RB/Crate/ReportDataResult.php` | Headers, types, totals across batches [code: app/bundles/ReportBundle/Crate/ReportDataResult.php:42-245 @7.x] |
| `ReportDataAdapter`, `ReportExportOptions`, `ReportExporter`, `ReportFileWriter`, `ExportHandler` | `RB/Adapter/`, `RB/Model/` | Scheduled export pipeline [code: app/bundles/ReportBundle/Model/ReportExporter.php:29-90 @7.x] |
| `CsvExporter`, `ExcelExporter`, `ExportResponse` | `RB/Model/` | UI export formats [code: app/bundles/ReportBundle/Model/CsvExporter.php:24-83 @7.x] |
| `ReportCleanup` | `RB/Model/ReportCleanup.php` | Deletes permanent zips older than 7 days [code: app/bundles/ReportBundle/Model/ReportCleanup.php:9 @7.x] |
| `ScheduleModel`, `SchedulerPlanner`, `DateBuilder`, `SchedulerBuilder` + `Scheduler{Now,Daily,Weekly,Month}Builder`, `SchedulerTemplateFactory` | `RB/Model/`, `RB/Scheduler/**` | RRULE (`simshaun/recurr`) planning [code: app/bundles/ReportBundle/Scheduler/Model/SchedulerPlanner.php:21-49 @7.x] |
| `SendSchedule`, `MessageSchedule`, `FileHandler` | `RB/Scheduler/Model/` | Email, zip, permanent link [code: app/bundles/ReportBundle/Scheduler/Model/SendSchedule.php:26-62 @7.x] |
| `ReportHelper` (Twig alias `report`; id `mautic.report.helper.report` deprecated 7.2) | `RB/Helper/ReportHelper.php` | Type mapping, standard columns, `getMappedObjectColumns()` [code: app/bundles/ReportBundle/Config/services.php:50-51 @7.x] |
| `RelativeDateHelper` (static) | `RB/Helper/RelativeDateHelper.php` | Relative date detection and resolution [code: app/bundles/ReportBundle/Helper/RelativeDateHelper.php:11-93 @7.x] |
| `ReportFilterDataTransformer` | `RB/Form/DataTransformer/` | UTC ⇄ local for filter values [code: app/bundles/ReportBundle/Form/DataTransformer/ReportFilterDataTransformer.php:28-97 @7.x] |
| `DashboardModel` | `DB/Model/DashboardModel.php:34` | Widgets, export, populate, cache, default filter [code: app/bundles/DashboardBundle/Model/DashboardModel.php:84-328 @7.x] |
| `Dashboard\Widget` (`mautic.dashboard.widget`) | `DB/Dashboard/Widget.php` | Owner-checked load; date range to session; `FORMAT_HUMAN = 'M j, Y'` [code: app/bundles/DashboardBundle/Dashboard/Widget.php:15-74 @7.x] |
| `WidgetDetailEventFactory` | `DB/Factory/WidgetDetailEventFactory.php:28-35` | Creates `WidgetDetailEvent` with a tag-aware cache provider [code: app/bundles/DashboardBundle/Factory/WidgetDetailEventFactory.php:28-35 @7.x] |
| `Collector` (`mautic.stats.aggregate.collector`), `StatCollection`, `Calculator`, `FetchOptions` | `SB/Aggregate/`, `SB/Event/Options/` | Stats aggregation [code: app/bundles/StatsBundle/Aggregate/Collector.php:21-32 @7.x] |
| `ChartQuery`, `DateRangeUnitTrait` | `app/bundles/CoreBundle/Helper/Chart/` | Time-bucketed chart queries [code: app/bundles/CoreBundle/Helper/Chart/ChartQuery.php:300-380,575-589 @7.x] |

Other ReportBundle service ids: `.csv_exporter`, `.excel_exporter`, `.report_exporter`, `.schedule_model`, `.report_export_options`, `.report_file_writer`, `.export_handler`, `.scheduler_builder`, `.scheduler_template_factory`, `.scheduler_date_builder`, `.scheduler_planner`, `.send_schedule`, `.file_handler`, `.message_schedule`, `.report_data_adapter` (all prefixed `mautic.report.`), plus `mautic.report.repository.scheduler` and `mautic.report.validator.schedule_is_valid_validator` [code: app/bundles/ReportBundle/Config/services.php:26-51 @7.x].

## 3. Events
### ReportBundle (`RB/ReportEvents.php`)
| Constant (name) | Event class | Dispatched at | Core listeners |
|---|---|---|---|
| `REPORT_PRE_SAVE` (`mautic.report_pre_save`) | `ReportEvent` | `ReportModel.php:152-153` | none |
| `REPORT_POST_SAVE` (`mautic.report_post_save`) | `ReportEvent` | `ReportModel.php:155-156` | `ReportSubscriber::onReportPostSave` (audit), `ReportSchedulerSubscriber::onReportSave` (re-plan) |
| `REPORT_PRE_DELETE` / `REPORT_POST_DELETE` | `ReportEvent` | `ReportModel.php:158-162` | `ReportSubscriber::onReportDelete` (audit) |
| `REPORT_ON_BUILD` (`mautic.report_on_build`) | `ReportBuilderEvent` | `ReportModel.php:198-199` | every context provider (§4) |
| `REPORT_ON_GENERATE` (`mautic.report_on_generate`) | `ReportGeneratorEvent` | `MauticReportBuilder.php:152-155` | every context provider |
| `REPORT_QUERY_PRE_EXECUTE` | `ReportQueryEvent` | `ReportModel.php:578-580` | none (plugin hook) |
| `REPORT_ON_DISPLAY` | `ReportDataEvent` | `ReportModel.php:626-629` | LeadBundle and CoreBundle `ReportSubscriber::onReportDisplay` |
| `REPORT_ON_GRAPH_GENERATE` | `ReportGraphEvent` | `ReportModel.php:563-565` | context providers |
| `REPORT_SCHEDULE_SEND` | `ReportScheduleSendEvent` | `ReportExporter.php:85-87` | `SchedulerSubscriber::onScheduleSend` → `SendSchedule::send` |
| `REPORT_ON_COLUMN_COLLECT` | `ColumnCollectEvent` | `ReportHelper.php:119-120` | LeadBundle `ReportSubscriber::onReportColumnCollect:654-684` |
| `REPORT_PERMANENT_FILE_CREATED` | `PermanentReportFileCreatedEvent` | `SendSchedule.php:50-51` | none |

[code: app/bundles/ReportBundle/ReportEvents.php @7.x] [code: app/bundles/ReportBundle/Model/ReportModel.php:145-629 @7.x]

`AbstractReportEvent::checkContext()` is true when the event has no context, or when its context equals or starts with one of the given contexts. `ReportBuilderEvent::addTable()` stops propagation when the added context equals the requested one [code: app/bundles/ReportBundle/Event/AbstractReportEvent.php:37-53 @7.x] [code: app/bundles/ReportBundle/Event/ReportBuilderEvent.php:90-92 @7.x].

### DashboardBundle (`DB/DashboardEvents.php`)
| Constant (name) | Event | Dispatched at | Listener behaviour |
|---|---|---|---|
| `DASHBOARD_ON_MODULE_LIST_GENERATE` (`mautic.dashboard_on_widget_list_generate`) | `WidgetTypeListEvent` | `Form/Type/WidgetType.php:43-45`, `Controller/Api/WidgetApiController.php:64-66` | base `onWidgetListGenerate` adds the bundle's types if all permissions are granted |
| `DASHBOARD_ON_MODULE_FORM_GENERATE` | `WidgetFormEvent` | `Form/Type/WidgetType.php:105-123` | base sets `formAlias`, stops propagation |
| `DASHBOARD_ON_MODULE_DETAIL_PRE_LOAD` | `WidgetDetailEvent` | `DashboardModel.php:198-203` | base sets `@MauticCore/Helper/chart.html.twig` |
| `DASHBOARD_ON_MODULE_DETAIL_GENERATE` | `WidgetDetailEvent` | `DashboardModel.php:241-245` | each bundle's `onWidgetDetailGenerate` |

[code: app/bundles/DashboardBundle/EventListener/DashboardSubscriber.php:49-102 @7.x]

### StatsBundle
`StatEvents::AGGREGATE_STAT_REQUEST` (`mautic.aggregate_stat_request`), `AggregateStatRequestEvent`, dispatched in `Collector.php:27-29`. Its only listener is `app/bundles/EmailBundle/EventListener/GraphAggregateStatsSubscriber.php` [code: app/bundles/StatsBundle/Aggregate/Collector.php:27-29 @7.x].

## 4. Report contexts (every `addTable` in core and bundled plugins)
| Context (`source`) | Group | Listener file:line | Graphs registered |
|---|---|---|---|
| `audit.log` | itself | `app/bundles/CoreBundle/EventListener/ReportSubscriber.php:18,125` (admin/CLI only `:179-183`) | — |
| `leads` | `contacts` | `app/bundles/LeadBundle/EventListener/ReportSubscriber.php:28,171` | `mautic.lead.graph.line.leads` |
| `lead.pointlog` | `contacts` | same `:30,730` | `mautic.lead.graph.line.leads`, `mautic.lead.graph.line.points`, `mautic.lead.table.most.points`, `.top.countries`, `.top.cities`, `.top.events`, `.top.actions` |
| `contact.attribution.multi` / `.first` / `.last` | `contacts` | same `:32-36,903` | pies `mautic.lead.graph.pie.attribution_stages/_campaigns/_actions/_channels` |
| `contact.frequencyrules` | `contacts` | same `:38,780` | — |
| `companies` | `companies` | same `:42,186` | `mautic.lead.graph.line.companies`, `mautic.lead.graph.pie.companies.industry`, `mautic.lead.table.pie.company.country`, `mautic.lead.company.table.top.cities` |
| `contact.dnc` | `contacts` | `app/bundles/LeadBundle/EventListener/ReportDNCSubscriber.php:18,80` | — |
| `contact.devices` | `contacts` | `app/bundles/LeadBundle/EventListener/ReportDevicesSubscriber.php:17,90` | — |
| `lead.utmTag` | `contacts` | `app/bundles/LeadBundle/EventListener/ReportUtmTagSubscriber.php:16,73` | — |
| `segment.log` | `contacts` | `app/bundles/LeadBundle/EventListener/SegmentLogReportSubscriber.php:13,63` | — |
| `segment.membership` | `contacts` | `app/bundles/LeadBundle/EventListener/SegmentReportSubscriber.php:15,59` | — |
| `emails` | itself | `app/bundles/EmailBundle/EventListener/ReportSubscriber.php:29,273` | `mautic.email.graph.pie.read.ingored.unsubscribed.bounced`, `.pie.sent.read.clicked.unsubscribed`, `mautic.email.table.most.emails.clicks`, `.most.emails.table` |
| `email.stats` | `emails` | same `:31,332` | `mautic.email.graph.line.stats`, `.pie.ignored.read.failed`, tables `most.emails.sent/read/read.percent/unsubscribed/bounced/failed/clicks` |
| `pages` | itself | `app/bundles/PageBundle/EventListener/ReportSubscriber.php:21,118` | — |
| `page.hits` | `pages` | same `:23,260` | lines `mautic.page.graph.line.hits`, `.line.time.on.site`; pies `.pie.time.on.site`, `.pie.new.vs.returning`, `.pie.devices`, `.pie.languages`; tables `mautic.page.table.referrers`, `.most.visited`, `.most.visited.unique` |
| `video.hits` | `videos` | same `:25,354` | — |
| `forms` | itself | `app/bundles/FormBundle/EventListener/ReportSubscriber.php:24,78` | — |
| `form.submissions` | `forms` | same `:26,123` | `mautic.form.graph.line.submissions`, `mautic.form.table.top.referrers`, `.most.submitted` |
| `form.results.<results_table>` (one per Form) | `form.results` | same `:28,170` | — |
| `assets` | itself | `app/bundles/AssetBundle/EventListener/ReportSubscriber.php:18,81` | — |
| `asset.downloads` | `assets` | same `:20,153` | `mautic.asset.graph.line.downloads`, `mautic.asset.table.most.downloaded`, `.top.referrers`, `mautic.asset.graph.pie.statuses` |
| `campaign_lead_event_log` | itself | `app/bundles/CampaignBundle/EventListener/ReportSubscriber.php:19,162` | — (line graph commented out `:165`) |
| `message.channel` | itself | `app/bundles/ChannelBundle/EventListener/ReportSubscriber.php:17,100` | — |
| `group.score` | `contacts` | `app/bundles/PointBundle/EventListener/ReportSubscriber.php:17,81` | — |
| `mobile_notifications` | itself | `app/bundles/NotificationBundle/EventListener/ReportSubscriber.php:17,112` | — |
| `mobile_notifications.stats` | `mobile_notifications` | same `:19,160` | `mautic.mobile_notification.graph.line.stats`, tables `most.mobile_notifications.sent/read/read.percent` |
| `focus_stats` | `focus` | `plugins/MauticFocusBundle/EventListener/ReportSubscriber.php:14,200` | — |
| `focus_leads` | `focus` | same `:16,306` | — |
| (`audit.log` extended with Focus columns) | | `plugins/MauticFocusBundle/EventListener/FocusSubscriber.php:122` | |

Source: code analysis §4.1 (file:line as listed). No other plugin in `plugins/` subscribes to `REPORT_ON_BUILD`. Graph types accepted: `table`, `bar`, `pie`, `line`. Templates exist only for `Line`, `Pie` and `Table` [code: app/bundles/ReportBundle/Event/ReportBuilderEvent.php:22-27,273-283 @7.x].

Docs mapping (UI parent > child) [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data-sources]:
- Assets > Assets, Asset Downloads
- Campaigns > Campaign Events
- Channels Messages > Message Queue
- Emails > Emails, Emails Sent
- Forms > Forms, Form Submissions
- Contacts > Contacts, Multi/First/Last Touch Attributions, Contact Point Log, Frequency Rules, Segment Membership, Do Not Contact, UTM Codes, Group score
- Companies > Companies
- Mobile Notifications > Mobile Notifications, Mobile Notifications Sent
- Pages > Landing Pages, Page hits
- Videos > Video hits

The docs list omits `contact.devices`, `segment.log`, `form.results.*` and the Focus contexts.

## 5. Dashboard widget types (every `DashboardSubscriber` subclass in core; none in `plugins/`)
| Bundle key | Widget types (form type where present) | Permissions (`$permissions`) | Listener file |
|---|---|---|---|
| `core` | `recent.activity` | none | `app/bundles/CoreBundle/EventListener/DashboardSubscriber.php:18,32-34` |
| `asset` | `asset.downloads.in.time`, `unique.vs.repetitive.downloads`, `popular.assets`, `created.assets` | `asset:assets:viewown`, `viewother` | `app/bundles/AssetBundle/EventListener/DashboardSubscriber.php` |
| `campaign` | `events.in.time`, `leads.added.in.time` | `campaign:campaigns:viewown`, `viewother` | `app/bundles/CampaignBundle/EventListener/DashboardSubscriber.php` |
| `email` | `emails.in.time` (`DashboardEmailsInTimeWidgetType`), `sent.email.to.contacts` (form), `most.hit.email.redirects` (form), `ignored.vs.read.emails`, `upcoming.emails`, `most.sent.emails`, `most.read.emails`, `created.emails`, `device.granularity.email` | `email:emails:viewown`, `viewother` | `app/bundles/EmailBundle/EventListener/DashboardSubscriber.php` |
| `email` | `emails.best.hours` (`DashboardBestHoursWidgetType`) | same | `app/bundles/EmailBundle/EventListener/DashboardBestHoursSubscriber.php` |
| `form` | `submissions.in.time`, `top.submission.referrers`, `top.submitters`, `created.forms` | `form:forms:viewown`, `viewother` | `app/bundles/FormBundle/EventListener/DashboardSubscriber.php` |
| `lead` | `created.leads.in.time` (`DashboardLeadsInTimeWidgetType`), `anonymous.vs.identified.leads`, `lead.lifetime` (form), `map.of.leads`, `top.lists`, `segments.build.time` (`DashboardSegmentsBuildTime`), `top.creators`, `top.owners`, `created.leads` | `lead:leads:viewown`, `viewother` | `app/bundles/LeadBundle/EventListener/DashboardSubscriber.php` |
| `page` | `page.hits.in.time` (`DashboardHitsInTimeWidgetType`), `unique.vs.returning.leads`, `dwell.times`, `popular.pages`, `created.pages`, `device.granularity` | `page:pages:viewown`, `viewother` | `app/bundles/PageBundle/EventListener/DashboardSubscriber.php` |
| `point` | `points.in.time` | `point:points:viewown`, `viewother` | `app/bundles/PointBundle/EventListener/DashboardSubscriber.php` |
| `report` | `report` (`ReportWidgetType`) | `report:reports:viewown`, `viewother` | `app/bundles/ReportBundle/EventListener/DashboardSubscriber.php:29-43` |
| `stage` | `stages.in.time` | `stage:stages:viewown`, `viewother` | `app/bundles/StageBundle/EventListener/DashboardSubscriber.php` |

Source: code analysis §4.2 [code: app/bundles/ReportBundle/EventListener/DashboardSubscriber.php:29-43 @7.x]. Widget options documented for three types [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#widgets]:
- Created Contacts over time: all, identified, anonymous, identified vs anonymous, Top Segments, Top Segments × identified/anonymous.
- Emails in time: sent, opened, failed, sent+opened, sent+opened+failed.
- Landing Page visits: total, unique, both.

## 6. Routes, controllers, AJAX, views
### ReportBundle [code: app/bundles/ReportBundle/Config/config.php:6-62 @7.x]
| Route | Path | Controller |
|---|---|---|
| `mautic_report_index` | `/s/reports/{page}` | `ReportController::indexAction` |
| `mautic_report_export` | `/s/reports/view/{objectId}/export/{format}` (default `csv`) | `exportAction` |
| `mautic_report_download` | `/s/reports/download/{reportId}/{format}` | `downloadAction` (permanent zip) |
| `mautic_report_view` | `/s/reports/view/{objectId}/{reportPage}` | `viewAction` |
| `mautic_report_schedule_preview` | `/s/reports/schedule/preview/{isScheduled}/{scheduleUnit}/{scheduleDay}/{scheduleMonthFrequency}` | `ScheduleController::indexAction` |
| `mautic_report_schedule` | `/s/reports/schedule/{reportId}/now` | `ScheduleController::nowAction` |
| `mautic_report_action` | `/s/reports/{objectAction}/{objectId}` | new, edit, clone, delete, batchDelete |
| `mautic_api_reportsstandard` | `/api/reports` (+ `/{id}`, `/new`, `/{id}/edit`, `/{id}/delete`) | `Api/ReportApiController` |

AJAX `report:getSourceData` returns column, filter, operator and graph HTML for a context [code: app/bundles/ReportBundle/Controller/AjaxController.php:25-43 @7.x]. Views live in `RB/Resources/views/Report/*.html.twig`, `Graph/{Line,Pie,Table}.html.twig`, `Schedule/index.html.twig` and `SubscribedEvents/Dashboard/widget.html.twig`.

### DashboardBundle [code: app/bundles/DashboardBundle/Config/config.php:6-47 @7.x]
| Route | Path | Controller |
|---|---|---|
| `mautic_dashboard_index` | `/s/dashboard` | `DashboardController::indexAction` |
| `mautic_dashboard_widget` | `/s/dashboard/widget/{widgetId}` | `widgetAction` (XHR) |
| `mautic_dashboard_action` | `/s/dashboard/{objectAction}/{objectId}` | new, edit, delete, save, export, import, applyDashboardFile, deleteDashboardFile |
| `mautic_widget_types` | `GET /api/data` | `WidgetApiController::getTypesAction` |
| `mautic_widget_data` | `GET /api/data/{type}` | `WidgetApiController::getDataAction` |

The AJAX actions are `viewingVisitors` (last 60 min), `updateWidgetForm`, `updateWidgetOrdering` and `delete` [code: app/bundles/DashboardBundle/Controller/AjaxController.php:37-101 @7.x]. The Dashboard menu entry has priority 100.

StatsBundle has no routes. `GET /api/stats` belongs to the API/Core area (see mautic-rest-api) [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stats.html].

## 7. Console command
`mautic:reports:scheduler` is `RB/Scheduler/Command/ExportSchedulerCommand.php`, with options `--report=<id>` and `--cleanup-only`. It returns 2 for a non-numeric `--report` and FAILURE on `FileIOException`. It has no lock [code: app/bundles/ReportBundle/Scheduler/Command/ExportSchedulerCommand.php:34-78 @7.x]. Nothing in the repo documents a cron interval; run it at least daily, since schedules fall due at 00:00 [code: app/bundles/ReportBundle/Scheduler/Builder/SchedulerBuilder.php:46-51 @7.x]. DashboardBundle and StatsBundle have no commands.

## 8. Configuration parameters
| Parameter | Default | Controls | Citation |
|---|---|---|---|
| `report_temp_dir` | `%mautic.application_dir%/media/files/temp` | Scheduled CSVs and `csv_reports/` permanent zips | [code: app/bundles/ReportBundle/Config/config.php:79-84 @7.x] |
| `report_export_batch_size` | 1000 | Rows per batch (scheduled and UI CSV) | same |
| `report_export_max_filesize_in_bytes` | 5000000 | Attach / zip / link threshold | same |
| `csv_always_enclose` | false | Quote every CSV cell (Configuration → Report settings) | same; [code: app/bundles/ReportBundle/Form/Type/ConfigType.php:18-30 @7.x] |
| `dashboard_import_dir` | `%mautic.application_dir%/app/assets/dashboards` | Global dashboard files | [code: app/bundles/DashboardBundle/Config/config.php:44-47 @7.x] |
| `dashboard_import_user_dir` | `%mautic.application_dir%/media/dashboards` | Per-User saved dashboards (`<dir>/<userId>/`) | same; [code: app/bundles/CoreBundle/Helper/PathsHelper.php:202-215 @7.x] |
| `cached_data_timeout` | 10 (minutes) | Widget cache default | [code: app/bundles/CoreBundle/Config/config.php:698 @7.x] |
| `default_daterange_filter` | `-1 month` | Dashboard default range start | [code: app/bundles/CoreBundle/Config/config.php:709 @7.x] |
| `default_pagelimit` | 30 | Report page size | [code: app/bundles/CoreBundle/Config/config.php:285 @7.x] |
| `default_timezone` | (install) | Relative date resolution, chart bucket offset | [code: app/bundles/CoreBundle/Helper/DateTimeHelper.php:386-391 @7.x] |
| `debug` | | Show SQL in the Report view | [code: app/bundles/CoreBundle/Config/config.php:710 @7.x] |

## 9. Permissions
| Operation | Check | Citation |
|---|---|---|
| List | `viewown` or `viewother`; forced `createdBy = me` without `viewother`; audit-log hidden for non-admins | [code: app/bundles/ReportBundle/Controller/ReportController.php:54-74 @7.x] |
| View / export / download / send now / widget | `hasEntityAccess(viewown, viewother, createdBy)` | [code: app/bundles/ReportBundle/Controller/ReportController.php:555,787,875 @7.x] |
| Export | plus admin or `report:export:enable` | [code: app/bundles/ReportBundle/Controller/ReportController.php:695,789-791 @7.x] |
| Create / clone | `report:reports:create` (+ view for clone) | [code: app/bundles/ReportBundle/Controller/ReportController.php:142-148,434-436 @7.x] |
| Edit | only `viewown/viewother` checked | [code: app/bundles/ReportBundle/Controller/ReportController.php:310-316 @7.x] |
| Delete | `deleteown/deleteother` | [code: app/bundles/ReportBundle/Controller/ReportController.php:179-185,246-251 @7.x] |
| API GET by id | `report:reports:view`, then owner if no `viewother` | [code: app/bundles/ReportBundle/Controller/Api/ReportApiController.php:67-86 @7.x] |
| Dashboard | none (per-owner isolation); widget types gated by bundle permissions | [code: app/bundles/DashboardBundle/Model/DashboardModel.php:60-63 @7.x] |

## 10. Extension contract
- **Context**:
  - `REPORT_ON_BUILD`: `checkContext([...])`, `addTable($context, ['display_name','columns','filters'], $group)`, `addGraph($context, $type, $graphId, $options)`.
  - Column keys: `label`, `type` (required), `alias`, `formula`, `groupByFormula`, `prefix`, `suffix`, `link`, `channelData`, `operators`, `operatorGroup`, `list`, `defaultValue`.
  - Helpers: `getStandardColumns($prefix, $remove, $idLinkRoute)`, `getLeadColumns()`, `getIpColumn()`, `getCategoryColumns()`, `getCampaignByChannelColumns()`, `getChannelColumns()`.

  [code: app/bundles/ReportBundle/Event/ReportBuilderEvent.php:62-283 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html#column-definition]
- **Generate**: `REPORT_ON_GENERATE` → `getQueryBuilder()->from()`, the join helpers, `applyDateFilters()`/`applyDateFiltersWithoutNullValues()`, and optionally `setContentTemplate()`, `setSelectColumns()`, `setFilterExpression()` [code: app/bundles/ReportBundle/Event/ReportGeneratorEvent.php:53-436 @7.x].
- **Graphs**: `REPORT_ON_GRAPH_GENERATE` → `getRequestedGraphs()`, `getOptions($graph)` (`chartQuery`, `dateFrom`, `dateTo`, `translator`), clone the QueryBuilder per graph, then `setGraph($id, $data)` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/reports.html#generating-graphs].
- **Any Report**: `REPORT_QUERY_PRE_EXECUTE` (`setQuery`), `REPORT_ON_DISPLAY` (`setData`, `updateColumnType()`); `REPORT_ON_COLUMN_COLLECT` for mapped object columns [code: app/bundles/ReportBundle/Helper/ReportHelper.php:117-132 @7.x].
- **Delivery**: `REPORT_SCHEDULE_SEND`, `REPORT_PERMANENT_FILE_CREATED`.
- **Widget**: subclass `DashboardSubscriber` (`$bundle`, `$types`, `$permissions`); `onWidgetDetailGenerate` → `checkPermissions`, `isCached`, `setTemplateData`, `setTemplate`, `stopPropagation` [code: app/bundles/DashboardBundle/EventListener/DashboardSubscriber.php:49-102 @7.x].
- **Stats**: listen to `AGGREGATE_STAT_REQUEST`, use `checkContext*`, fill `getStatCollection()`, call `statsCollected()`. Consumers use `Collector::fetchStats()` and then `getCalculator($from,$to)->getSumsByDay()` [code: app/bundles/StatsBundle/Event/AggregateStatRequestEvent.php:28-91 @7.x].

## 11. Tests
Directories: `RB/Tests/` (`Builder/`, `Crate/`, `Entity/`, `Event/`, `Form/`, `Helper/`, `Model/`, `Scheduler/**`, `Unit/`, `Controller/`, `Controller/Api/`, `Functional/`, `Command/`), `DB/Tests/`, `SB/Tests/`. No Codeception coverage was found. See test-patterns.md.
