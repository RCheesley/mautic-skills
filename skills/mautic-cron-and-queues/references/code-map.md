# Code map — cron commands, locking, Messenger, cache (Mautic 7.x)

Paths are relative to the repo root. The per-command file list is in `commands.md`.

## 1. Command infrastructure

| Concern | Path | Notes |
|---|---|---|
| Lock base class | `app/bundles/CoreBundle/Command/ModeratedCommand.php` | Options 56-74; `checkRunStatus()` 76-120; `completeRun()` 125-135; pid lock 137-192; flock/redis 194-212; `isPidSupported()` 214-224 [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-224 @7.x] |
| Lock files | `var/run/sf.<key>.<sha256>.lock` (`<cache dir>/../run`) | [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:104-110,148-153 @7.x] |
| Redis lock connection | parameter `cache_adapter_redis` (CacheBundle) | [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:194-212 @7.x] |
| Signal handling | `app/bundles/CoreBundle/ProcessSignal/ProcessSignalService.php`, `ProcessSignalState`, `Exception/SignalCaughtException.php` | [code: app/bundles/CoreBundle/ProcessSignal/ProcessSignalService.php:22-80 @7.x] |
| Command registration | `#[AsCommand(name: …, aliases: …)]`; `Command/` directories are autowired | [code: app/bundles/CampaignBundle/Command/UpdateLeadCampaignsCommand.php:25 @7.x] |
| Batch-output helper | `app/bundles/CampaignBundle/Command/WriteCountTrait.php:13-38` | "N events executed / scheduled / rescheduled" [code: app/bundles/CampaignBundle/Command/WriteCountTrait.php:13-38 @7.x] |
| "Still alive" signal for long jobs | `JobExtendTimeEvent` (dispatched by ReportExporter, KickoffExecutioner, ResumeStuckCampaignCommand, ExportHelper) | [code: app/bundles/CampaignBundle/Command/ResumeStuckCampaignCommand.php:256 @7.x] |

Subclasses of `ModeratedCommand`: ChannelBundle `ProcessMarketingMessagesQueueCommand`, `SendChannelBroadcastCommand`;
CampaignBundle `TriggerCampaignCommand`, `SummarizeCommand`, `UpdateLeadCampaignsCommand`; EmailBundle
`SendWinnerEmailCommand`; LeadBundle `Field/Command/CreateCustomFieldCommand`, `SegmentStatCommand`,
`UpdateLeadListsCommand`; CoreBundle `EntityImportCommand`, `EntityExportCommand`, `UnusedIpDeleteCommand`,
`CleanupMaintenanceCommand` [code: app/bundles/*/Command (grep "extends ModeratedCommand") @7.x].

## 2. Command directories

| Bundle | Directory |
|---|---|
| CoreBundle | `app/bundles/CoreBundle/Command/` (+ `Test/PhpUnitConfigCommand.php`) |
| CampaignBundle | `app/bundles/CampaignBundle/Command/` |
| LeadBundle | `app/bundles/LeadBundle/Command/`, `app/bundles/LeadBundle/Field/Command/` |
| ChannelBundle | `app/bundles/ChannelBundle/Command/` |
| EmailBundle | `app/bundles/EmailBundle/Command/` (only `ProcessFetchEmailCommand`, `SendWinnerEmailCommand`) |
| ReportBundle | `app/bundles/ReportBundle/Scheduler/Command/` |
| WebhookBundle | `app/bundles/WebhookBundle/Command/` |
| FormBundle | `app/bundles/FormBundle/Command/` |
| PluginBundle | `app/bundles/PluginBundle/Command/` |
| IntegrationsBundle | `app/bundles/IntegrationsBundle/Command/` |
| MarketplaceBundle | `app/bundles/MarketplaceBundle/Command/` |
| InstallBundle | `app/bundles/InstallBundle/Command/` |
| CacheBundle | `app/bundles/CacheBundle/Command/` |
| Social plugin | `plugins/MauticSocialBundle/Command/` |

No `Command/` directory: Asset, Category, Project, Page, DynamicContent, Point, Stage, User, Dashboard, Stats, Api,
Messenger [code: app/bundles/PointBundle, app/bundles/UserBundle, app/bundles/PageBundle (directory listings) @7.x].

## 3. Background-mode parameters (which command each one requires)

| Parameter | Default | Command it needs | Source |
|---|---|---|---|
| `create_custom_field_in_background` | false (read with fallback) | `mautic:custom-field:create-column` / `update-column` / `delete-column` | [code: app/bundles/LeadBundle/Field/Settings/BackgroundSettings.php:18-21 @7.x] |
| `update_segment_contact_count_in_background` | false | `lead:list:count-cache-update` | [code: app/bundles/LeadBundle/Config/config.php:371 @7.x] |
| `delete_segment_in_background` | false | `mautic:segment:delete` | [code: app/bundles/LeadBundle/Config/config.php:340 @7.x] |
| `update_company_mapping_data_in_background` | false | `mautic:company:delete_company_leads`, `mautic:company:update_lead_company` | [code: app/bundles/LeadBundle/Config/config.php:373 @7.x] |
| `contact_export_in_background` | **true** | `mautic:contacts:scheduled_export` | [code: app/bundles/LeadBundle/Config/config.php:364 @7.x] |
| `background_import_if_more_rows_than` | 0 (docs: 0 = always background) | `mautic:import` | [code: app/bundles/LeadBundle/Config/config.php:338 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#import-settings] |
| `delete_campaign_event_log_in_background` | false | `mautic:campaign:delete-event-logs` | [code: app/bundles/CampaignBundle/Config/config.php:164 @7.x] |
| `clean_webhook_logs_in_background` | false | `mautic:webhooks:delete_logs` | [code: app/bundles/WebhookBundle/Config/config.php:51 @7.x] |
| `queue_mode` | `immediate_process` | `mautic:webhooks:process` when `command_process` | [code: app/bundles/WebhookBundle/Config/config.php:54 @7.x] |
| `webhook_limit`, `webhook_time_limit` | 10, 600 s | batch and time cap of `mautic:webhooks:process` | [code: app/bundles/WebhookBundle/Config/config.php:46-47 @7.x] |
| `campaigns_resume_stuck_records_after` | `2025-10-01 00:00:00` | `mautic:campaigns:resume-stuck` cut-off | [code: app/bundles/CampaignBundle/Config/config.php:174 @7.x] |
| `gdpr_user_purge_threshold` | 1095 days | `mautic:maintenance:cleanup --gdpr` | [code: app/bundles/CoreBundle/Command/CleanupMaintenanceCommand.php:105-108 @7.x] |

## 4. MessengerBundle

| Concern | Path |
|---|---|
| Framework wiring (transports, routing, failure transport) | `app/config/config.php:102-126` [code: app/config/config.php:102-126 @7.x] |
| Parameters (`messenger_dsn_*`, `messenger_retry_strategy_*`) | `app/bundles/MessengerBundle/Config/config.php:6-14` |
| Env-var mapping `MAUTIC_MESSENGER_*` | `app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:13-28`, `app/bundles/CoreBundle/Loader/ParameterLoader.php:66-110` |
| Messages | `app/bundles/MessengerBundle/Message/EmailHitNotification.php`, `PageHitNotification.php`, `TestEmail.php`, `TestHit.php`, `TestFailed.php`, `Traits/MessageRequestTrait.php` |
| Handlers | `app/bundles/MessengerBundle/MessageHandler/EmailHitNotificationHandler.php`, `PageHitNotificationHandler.php`, `RemoveReportAttachmentHandler.php` |
| Retry strategy | `app/bundles/MessengerBundle/Retry/RetryStrategy.php` |
| Null transport (`null://`) | `app/bundles/MessengerBundle/Transport/NullTransportFactory.php`, `NullTransport.php` |
| `messenger-nullable:` env processor | `app/bundles/MessengerBundle/DependencyInjection/EnvProcessor/MessengerNullableEnvVarProcessor.php` |
| `urlencoded-dsn:` env processor | `app/bundles/EmailBundle/DependencyInjection/EnvProcessor/MailerDsnEnvVarProcessor.php:12-22` |
| DSN parser | `app/bundles/CoreBundle/Helper/Dsn/Dsn.php` |
| DSN validator | `app/bundles/MessengerBundle/Validator/DsnValidator.php`, `Validator/Dsn.php` |
| Exceptions | `app/bundles/MessengerBundle/Exceptions/MauticMessengerException.php`, `InvalidPayloadException.php` |
| Config tab "Queue Settings" (`/s/config/edit/messengerconfig`) | `EventListener/ConfigSubscriber.php:14-30`, `Form/Type/ConfigType.php`, `Resources/views/FormTheme/Config/_config_messengerconfig_widget.html.twig` |
| DSN form type, test button | `app/bundles/ConfigBundle/Form/Type/DsnType.php`, `Form/DataTransformer/DsnTransformer.php`, `Assets/js/config.js:54-75` |
| Test-message AJAX (`/s/ajax?action=messenger:sendTestMessage`) | `app/bundles/MessengerBundle/Controller/AjaxController.php:15-39`, `Service/TestMessageFactory.php:19-27` |
| Dispatch sites | `app/bundles/EmailBundle/Controller/PublicController.php:131-145` (opens), `app/bundles/PageBundle/Model/PageModel.php:468-506` (hits), `app/bundles/EmailBundle/Helper/MailHelper.php:402-414` (Email send) |
| README (partly stale) | `app/bundles/MessengerBundle/README.md` |

Sources: [code: app/bundles/MessengerBundle/Config/services.php:9-18 @7.x] and the paths listed.

Messenger parameters and env vars:

| Parameter | Default | Env var |
|---|---|---|
| `messenger_dsn_email` | `sync://` | `MAUTIC_MESSENGER_DSN_EMAIL` |
| `messenger_dsn_hit` | `sync://` | `MAUTIC_MESSENGER_DSN_HIT` |
| `messenger_dsn_failed` | `null` (→ `null://`) | `MAUTIC_MESSENGER_DSN_FAILED` |
| `messenger_retry_strategy_max_retries` | 3 | `MAUTIC_MESSENGER_RETRY_STRATEGY_MAX_RETRIES` |
| `messenger_retry_strategy_delay` | 1000 (ms) | `MAUTIC_MESSENGER_RETRY_STRATEGY_DELAY` |
| `messenger_retry_strategy_multiplier` | 2.0 | `MAUTIC_MESSENGER_RETRY_STRATEGY_MULTIPLIER` |
| `messenger_retry_strategy_max_delay` | 0 (no cap) | `MAUTIC_MESSENGER_RETRY_STRATEGY_MAX_DELAY` |
| `mailer_dsn` (EmailBundle) | `smtp://localhost:1025` | `MAUTIC_MAILER_DSN` |

[code: app/bundles/MessengerBundle/Config/config.php:6-14 @7.x] [code: app/bundles/EmailBundle/Config/config.php:146 @7.x]

Tables: `messenger_messages` for `doctrine://` (created by Symfony, not by a Mautic migration; name configurable via
`table_name`); `page_hits`, `email_stats`, `email_stats_devices`, `lead_devices` written by the handlers
[code: app/bundles/MessengerBundle/MessageHandler/PageHitNotificationHandler.php:38-94 @7.x]
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#how-to-enable-the-queuing].

Events: no Mautic event constants; `EmailEvents::EMAIL_ON_OPEN` and `PageEvents::PAGE_ON_HIT` are dispatched inside the
handlers; no listener for Symfony `WorkerMessageFailedEvent` exists [code: app/bundles/EmailBundle/Model/EmailModel.php:496-499 @7.x]
[code: app/bundles/PageBundle/Model/PageModel.php:708-711 @7.x].

Permissions: none of its own; the config tab uses ConfigBundle permissions; the test AJAX needs only
`IS_AUTHENTICATED_REMEMBERED` [code: app/bundles/CoreBundle/Controller/AjaxController.php:76 @7.x].

## 5. CacheBundle and related

| Concern | Path |
|---|---|
| Providers | `app/bundles/CacheBundle/Cache/CacheProvider.php`, `CacheProviderTagAware.php`, `AbstractCacheProvider.php` |
| Interfaces (autowire these) | `CacheProviderInterface`, `CacheProviderTagAwareInterface` (`Config/services.php:38-40`) |
| Adapters | `app/bundles/CacheBundle/Cache/Adapter/FilesystemTagAwareAdapter.php`, `MemcachedTagAwareAdapter.php`, `RedisAdapter.php`, `RedisTagAwareAdapter.php`, `RedisAdapterTrait.php` |
| Service wiring (all public) | `app/bundles/CacheBundle/Config/services.php:11-48` |
| Parameters | `app/bundles/CacheBundle/Config/config.php:13-37` |
| `cache:clear` hook | `app/bundles/CacheBundle/EventListener/CacheClearSubscriber.php` |
| `mautic:cache:clear` | `app/bundles/CacheBundle/Command/ClearCacheCommand.php` |
| Predis connection (sentinel, cluster) | `app/bundles/CoreBundle/Helper/PRedisConnectionHelper.php` |
| `var/cache` nuke, config refresh | `app/bundles/CoreBundle/Helper/CacheHelper.php` |
| Deprecated DB/file cache | `app/bundles/CoreBundle/Helper/CacheStorageHelper.php` (`<prefix>cache_items`) |
| Doctrine result cache | `app/bundles/CoreBundle/Cache/ResultCacheHelper.php`, `ResultCacheOptions.php`; pool `doctrine_result_cache` in `app/config/config.php:218-221,305-311` |
| Result-cache invalidation | `app/bundles/CoreBundle/EventListener/CacheInvalidateSubscriber.php`, `app/bundles/CoreBundle/Entity/CacheInvalidateInterface.php` |
| Middleware cache warmer (unrelated to data cache) | `app/bundles/CoreBundle/Cache/MiddlewareCacheWarmer.php` |

Cache parameters: `cache_adapter` and `cache_adapter_tag_aware` (`mautic.cache.adapter.filesystem`), `cache_prefix` (`''`),
`cache_lifetime` (86400), `cache_adapter_memcached`, `cache_adapter_redis` (`dsn` `redis://localhost`),
`redis_primary_only` (false), `cached_data_timeout` (10 min), `tmp_path` (`var/tmp`)
[code: app/bundles/CacheBundle/Config/config.php:13-37 @7.x] [code: app/bundles/CoreBundle/Config/config.php:259,698 @7.x].

## 6. Legacy QueueBundle

`app/bundles/QueueBundle/Config/config.php` (0 bytes) is the only file left; the bundle is not in `app/AppKernel.php`
[code: app/AppKernel.php:128-155 @7.x]. Removal documented in `UPGRADE-5.0.md:104-109` [code: UPGRADE-5.0.md:104-109 @7.x].

## 7. Tests

| Area | Path |
|---|---|
| Locking | `app/bundles/CoreBundle/Tests/Unit/Command/ModeratedCommandTest.php` + `src/FakeModeratedCommand.php` |
| Signals | `app/bundles/CoreBundle/Tests/Unit/ProcessSignal/ProcessSignalServiceTest.php` |
| Messenger | `app/bundles/MessengerBundle/Tests/` (`Form/Type/ConfigTypeTest.php`, `Message/*Test.php`, `MessageHandler/*Test.php`) |
| Cache | `app/bundles/CacheBundle/Tests/Cache/CacheProviderTest.php`, `Tests/EventListener/CacheClearSubscriberTest.php` |
| Command examples | `app/bundles/WebhookBundle/Tests/Command/DeleteWebhookLogsCommandTest.php`, `app/bundles/ReportBundle/Tests/Scheduler/Command/ExportSchedulerCommandTest.php`, `app/bundles/LeadBundle/Tests/Command/ImportCommandTest.php`, `ContactScheduledExportCommandTest.php` |
| Async email/report path | `app/bundles/ReportBundle/Tests/Controller/ReportControllerFunctionalTest.php:553-596` |
| Sync hit path | `app/bundles/PageBundle/Tests/Functional/Model/PageHitCookieTest.php` |

[code: app/bundles/CoreBundle/Tests/Unit/Command/ModeratedCommandTest.php:65-359 @7.x]
