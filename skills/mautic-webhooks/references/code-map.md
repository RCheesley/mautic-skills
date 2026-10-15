# Webhooks — code map (Mautic 7.x)

`WB` = `app/bundles/WebhookBundle`. Line numbers at commit 419a08a9b35.

## Entities and tables

| Entity | File | Table | Key facts |
|---|---|---|---|
| `Webhook` (`FormEntity`, `SkipModifiedInterface`) | `WB/Entity/Webhook.php` | `webhooks` | `webhook_url` TEXT, `secret`, `events_orderby_dir` nullable, health columns `marked_unhealthy_at`, `unhealthy_since`, `last_notification_sent_at` (L135-170); `events` 1:N orphan-removal indexed by `eventType` (L145-152); `logs` 1:N ordered `dateAdded DESC` (L154-160); validation L191-227; `LOGS_DISPLAY_LIMIT = 100` (L50); `wasModifiedRecently()` 2 days (L507-516); API Platform resource (L28-121); JMS group prefix `hook` (L173-188). [code: app/bundles/WebhookBundle/Entity/Webhook.php:28-583 @7.x] |
| `Event` | `WB/Entity/Event.php` | `webhook_events` | `webhook_id` CASCADE, `event_type` string(50) (L39-65). `EventRepository::getEntitiesByEventType()` returns only published Webhooks' events (L15-30). [code: app/bundles/WebhookBundle/Entity/Event.php:39-65 @7.x] [code: app/bundles/WebhookBundle/Entity/EventRepository.php:15-30 @7.x] |
| `Log` | `WB/Entity/Log.php` | `webhook_logs` | `status_code` string(50), `note` ≤190 chars, `runtime` 2 dp; index `webhook_id_date_added` (L38-59, L125-148). [code: app/bundles/WebhookBundle/Entity/Log.php:38-148 @7.x] |
| `WebhookQueue` | `WB/Entity/WebhookQueue.php` | `webhook_queue` | BIGINT `id`, `payload_compressed` MEDIUMBLOB (gzcompress 9), `event_id` CASCADE, `retries` SMALLINT, `date_modified` (L33-117). [code: app/bundles/WebhookBundle/Entity/WebhookQueue.php:33-117 @7.x] |

Repositories: `WebhookQueueRepository` (delete processed rows in chunks, L21-56), `LogRepository` (trim L18-59, success ratio L75-119). [code: app/bundles/WebhookBundle/Entity/WebhookQueueRepository.php:21-56 @7.x] [code: app/bundles/WebhookBundle/Entity/LogRepository.php:18-119 @7.x]

Migrations touching these tables: `Version20221014061125` (log index), `Version20221014081742` (`payload_compressed`), `Version20240228132306` (drop `payload`, add `retries`, `date_modified`), `Version20240607092418` (queue `id` BIGINT), `Version20241004132307` (health columns). [code: app/migrations/Version20221014061125.php:22 @7.x] [code: app/migrations/Version20221014081742.php:24 @7.x] [code: app/migrations/Version20240228132306.php:24-39 @7.x] [code: app/migrations/Version20240607092418.php:25 @7.x] [code: app/migrations/Version20241004132307.php:26-32 @7.x]

## Services and models

| Class | File | Role |
|---|---|---|
| `WebhookModel` | `WB/Model/WebhookModel.php` | Constants `COMMAND_PROCESS`, `IMMEDIATE_PROCESS`, `DELETE_BATCH_LIMIT=5000`, `WEBHOOK_LOG_MAX=1000` (L47-53); `saveEntity` L153-160; `getEvents` L202-215; `queueWebhooksByType` L229-236; `queueWebhooks` L238-257; `queueWebhook` L262-279; `processWebhooks` L286-293; `processWebhook` L295-384; `isSick` L390-400; `killWebhook` L408-414; `markWebhookUnHealthy/Healthy` L416-435; `addLog` L445-463; `getWebhookPayload` L485-527; `getWebhookQueues` L534-606; `getEventsOrderbyDir` L613-622; `serializeData` L666-687; `setConfigProps` L724-735. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:47-735 @7.x] |
| `Http\Client` | `WB/Http/Client.php` | Builds JSON body, headers and HMAC signature; private-address check; `sendRequest` (L23-42). [code: app/bundles/WebhookBundle/Http/Client.php:23-42 @7.x] |
| `Service\WebhookService` | `WB/Service/WebhookService.php` | Health window L19-31; notification throttling L33-69. [code: app/bundles/WebhookBundle/Service/WebhookService.php:19-69 @7.x] |
| `Notificator\WebhookNotificationSender` | `WB/Notificator/WebhookNotificationSender.php` | Veto event, in-app notification, email, recipient rules (L35-120). [code: app/bundles/WebhookBundle/Notificator/WebhookNotificationSender.php:35-120 @7.x] |
| `Notificator\WebhookKillNotificator`, `WebhookFailureNotificator` | `WB/Notificator/` | Subject/body using `webhook-killed` / `webhook-failing` Twig templates (L22-36). [code: app/bundles/WebhookBundle/Notificator/WebhookKillNotificator.php:22-36 @7.x] |
| `Helper\CampaignHelper` | `WB/Helper/CampaignHelper.php` | Campaign "Send a webhook" action (L24-148). [code: app/bundles/WebhookBundle/Helper/CampaignHelper.php:24-148 @7.x] |
| `mautic.http.client` | `app/bundles/CoreBundle/Config/services.php:314` | Plain `GuzzleHttp\Client`, autowired, no options. [code: app/bundles/CoreBundle/Config/services.php:314 @7.x] |

## Events (`WB/WebhookEvents.php`)

| Constant | Name | Event class | Dispatched | Core listener |
|---|---|---|---|---|
| `WEBHOOK_PRE_SAVE` / `WEBHOOK_POST_SAVE` | `mautic.webhook_pre_save` / `_post_save` | `WebhookEvent` | `WebhookModel.php:634-655` | post_save → audit log `WB/EventListener/WebhookSubscriber.php:33-48` |
| `WEBHOOK_PRE_DELETE` / `WEBHOOK_POST_DELETE` | `mautic.webhook_pre_delete` / `_post_delete` | `WebhookEvent` | `WebhookModel.php:640-644` | post_delete → audit log L53-65 |
| `WEBHOOK_KILL` | `mautic.webhook_kill` | `WebhookEvent(webhook, false, reason)` | `WebhookModel::killWebhook` L412-413 | `WebhookSubscriber.php:70-73` → `WebhookKillNotificator` |
| `WEBHOOK_QUEUE_ON_ADD` | `mautic.webhook_queue_on_add` | `WebhookQueueEvent` | `WebhookModel::queueWebhook` L273-276 | EmailBundle strips email bodies, `app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:92-120` |
| `WEBHOOK_ON_BUILD` | `mautic.webhook_on_build` | `WebhookBuilderEvent` | `WebhookModel::getEvents` L209-210 | Lead, Email, Form, Page, Sms `WebhookSubscriber`s |
| `ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.webhook.campaign_on_trigger_action` | `CampaignExecutionEvent` | CampaignBundle | `WB/EventListener/CampaignSubscriber.php:28-38` |
| `WEBHOOK_ON_REQUEST` | `mautic.webhook_on_request` | `WebhookRequestEvent` | `CampaignHelper.php:39-40` | none |
| `WEBHOOK_PRE_EXECUTE` / `WEBHOOK_POST_EXECUTE` | — | (non-existent class) | never | none |
| (class name) | `WebhookNotificationEvent` | `WebhookNotificationEvent` | `WebhookNotificationSender.php:37` | none |

[code: app/bundles/WebhookBundle/WebhookEvents.php:19-110 @7.x] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:209-276,412-413,634-655 @7.x]

Webhook event-type registrations (producers): `app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:50-300`, `app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:48-120`, `app/bundles/FormBundle/EventListener/WebhookSubscriber.php:41-59`, `app/bundles/PageBundle/EventListener/WebhookSubscriber.php:41-58`, `app/bundles/SmsBundle/EventListener/WebhookSubscriber.php:34-53`. Payload tables: `behaviour.md` §3. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:50-300 @7.x]

Sample payloads: `app/bundles/{LeadBundle,FormBundle,EmailBundle,PageBundle}/Assets/WebhookPayload/*.json`. [code: app/bundles/WebhookBundle/Controller/AjaxController.php:103-162 @7.x]

## Controllers, routes and UI

| Concern | Location |
|---|---|
| UI CRUD `/s/webhooks/{page}`, `/s/webhooks/{objectAction}/{objectId}` | `WB/Controller/WebhookController.php`; routes `WB/Config/config.php:7-16` |
| Test payload AJAX `webhook:sendHookTest` | `WB/Controller/AjaxController.php:16-162` |
| v1 API `/api/hooks`, `/api/hooks/triggers` | `WB/Controller/Api/WebhookApiController.php:46-99`; routes `WB/Config/config.php:17-28` |
| v2 API `/api/v2/webhooks` | `WB/Entity/Webhook.php:28-121` (attributes) |
| Webhook form | `WB/Form/Type/WebhookType.php` (secret L68-80, events L82-103, order L126-142) |
| Config form (`webhookconfig`) | `WB/Form/Type/ConfigType.php:19-81` |
| Campaign action form | `WB/Form/Type/CampaignEventSendWebhookType.php:26-101` |
| Templates | `WB/Resources/views/Webhook/{list,form,details}.html.twig`, `Notifications/webhook-{failing,killed}.html.twig` |
| Admin menu "Webhooks" | `WB/Config/config.php:31-43` |

[code: app/bundles/WebhookBundle/Config/config.php:7-43 @7.x] [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php:46-99 @7.x]

## Commands

| Command | File | Notes |
|---|---|---|
| `mautic:webhooks:process` | `WB/Command/ProcessWebhookQueuesCommand.php` | `-i/--webhook-id`, `--min-id`, `--max-id`; no-op unless `queue_mode = command_process` (L59-63). |
| `mautic:webhooks:delete_logs` | `WB/Command/DeleteWebhookLogsCommand.php` | Trims logs above `webhook_log_max` (L36-49); needed only with `clean_webhook_logs_in_background = true`. |

[code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:59-143 @7.x] [code: app/bundles/WebhookBundle/Command/DeleteWebhookLogsCommand.php:36-49 @7.x]

## Configuration parameters (`WB/Config/config.php:45-61`)

| Parameter | Default | UI? | Effect |
|---|---|---|---|
| `queue_mode` | `immediate_process` | yes | `immediate_process` or `command_process` |
| `events_orderby_dir` | `ASC` | yes | Global batch order; per-Webhook override |
| `webhook_email_details` | `true` | yes | Include email bodies/tokens in email payloads |
| `webhook_allowed_private_addresses` | `[]` | yes | Allow-list for private/loopback targets |
| `webhook_limit` | `10` | no | Rows per request; range-mode stride |
| `webhook_time_limit` | `600` s | no | Drain budget per run |
| `webhook_log_max` | `1000` | no | Logs kept per Webhook |
| `clean_webhook_logs_in_background` | `false` | no | Defer log trimming to `delete_logs` |
| `webhook_health_check_time` | `300` s | no | Unhealthy skip window |
| `webhook_retry_delay` | `3600` s | no | Delay before retrying failed rows |
| `webhook_disable_limit` | `100` | no | Log window for `isSick()` |
| `disable_auto_unpublish` | `false` | no | Never kill; only mark unhealthy |
| `first_webhook_failure_notification_time` | `3600` s | no | Unhealthy duration before first failure notice |
| `webhook_failure_notification_interval` | `86400` s | no | Gap between failure notices |
| `webhook_timeout` | `15` s | no | Read but not applied |
| `webhook_send_notification_to_author` (NotificationBundle) | `true` | — | Email the users vs a fixed list |
| `webhook_notification_email_addresses` (NotificationBundle) | `null` | — | CSV list when the above is false |

[code: app/bundles/WebhookBundle/Config/config.php:45-61 @7.x] [code: app/bundles/WebhookBundle/Form/Type/ConfigType.php:19-81 @7.x] [code: app/bundles/NotificationBundle/Config/config.php:123-124 @7.x]

## Permissions

`WB/Security/Permissions/WebhookPermissions.php:16-17`: `webhook:webhooks:{viewown, viewother, editown, editother, create, deleteown, deleteother, publishown, publishother, full}`, `webhook:categories:*`. [code: app/bundles/WebhookBundle/Security/Permissions/WebhookPermissions.php:16-17 @7.x]

## Tests directory

`WB/Tests/` — `Functional/` (`WebhookFunctionalTest`, `CampaignSendWebhookFunctionalTest`, `Command/`, `Controller/`, `Entity/`, `Model/`), `Unit/` (`Controller`, `Entity`, `EventListener`, `Helper`, `Http`, `Model`, `Notificator`), `Form/Type/ConfigTypeFunctionalTest.php`, `Entity/WebhookRepositoryTest.php`. See `test-patterns.md`. [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:24 @7.x]
