---
name: mautic-webhooks
description: "Mautic outgoing webhooks: configuring a Webhook, the subscribable event types and their payloads, immediate vs queued delivery, the mautic:webhooks:process cron command, ordering, retries and timeouts, auto-unpublish after repeated failures and the notification emails, webhook_logs and log limits, the HMAC-SHA256 Webhook-Signature header and how to verify it in a receiver, the /api/hooks and /api/v2/webhooks API, and how a plugin adds a webhook event type. Use whenever a task mentions Mautic webhooks, Webhook-Signature, webhook secret, mautic.lead_post_save_new, mautic.form_on_submit or any mautic.* webhook trigger, queue_mode, webhook_queue, webhook_logs, a webhook that stopped, failed or was unpublished, mautic:webhooks:process, WebhookModel, WebhookEvents, WebhookBuilderEvent, /api/hooks, building a receiver for Mautic events, or touches app/bundles/WebhookBundle/ or any */EventListener/WebhookSubscriber.php."
---
# Mautic Webhooks

## Scope
Outgoing webhooks: Mautic POSTs signed JSON describing Contact, Company, Email, Form, Page and Text Message events to URLs configured as Webhooks, either inside the triggering request or in batches from cron (`app/bundles/WebhookBundle`). Out of scope: the Campaign action "Send a webhook" beyond the contrast in references/behaviour.md §11 (see mautic-campaigns), inbound email-transport callbacks (see mautic-emails), and the general REST framework (see mautic-rest-api).

A **Contact** is a person record (code: `Lead`); a **Segment** is a Contact list (code: `LeadList`); a **Channel subscription** / **DNC** is a Do Not Contact entry. A **Webhook** is a saved target (URL, secret, subscribed event types). **Killed** means Mautic unpublished it automatically.

## Expected behaviour (essentials)
- Only **published** Webhooks receive events. Events raised while a Webhook is unpublished are never queued for it. [code: app/bundles/WebhookBundle/Entity/EventRepository.php:15-30 @7.x]
- Core offers 14 event types: `mautic.lead_post_save_new`, `lead_post_save_update`, `lead_points_change`, `lead_post_delete`, `lead_channel_subscription_changed`, `lead_company_change`, `lead_list_change`, `company_post_save`, `company_post_delete`, `email_on_send`, `email_on_open`, `form_on_submit`, `page_on_hit`, `sms_on_send`. `GET /api/hooks/triggers` returns the live list. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:50-128 @7.x] [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php:90-99 @7.x]
- `lead_post_save_new` means "became identified" (the save set `dateIdentified`), not "row created". Every other changed save of an identified Contact is `_update`. Anonymous Contacts and no-change saves send nothing. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:131-160 @7.x]
- The body is `{"<eventType>": [ {...payload, "timestamp": "<ISO-8601>"} ], ...}`. `timestamp` is when the row was queued. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:485-527 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html]
- Payloads are serialised **at queue time**, so a delayed delivery carries the data as it was when queued. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:229-279 @7.x]
- Each request is `POST` with `Content-Type: application/json`, `User-Agent: Webhook`, `X-Origin-Base-URL: <site_url>` and `Webhook-Signature`. [code: app/bundles/WebhookBundle/Http/Client.php:23-41 @7.x]
- `Webhook-Signature = base64(HMAC-SHA256(raw JSON body, secret))`, using the raw binary digest. A secret is generated automatically if none is given. [code: app/bundles/WebhookBundle/Http/Client.php:25-26 @7.x] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:153-160 @7.x]
- `queue_mode = immediate_process` is the default. Mautic sends one request per event per Webhook, synchronously inside the request that triggered it, and never retries a failure (at most once). [code: app/bundles/WebhookBundle/Model/WebhookModel.php:249-256 @7.x] [code: app/bundles/WebhookBundle/Config/config.php:45-61 @7.x]
- With `queue_mode = command_process`, rows go to `webhook_queue` and only `mautic:webhooks:process` sends them. Each request batches up to `webhook_limit` (10) items, possibly of mixed types. A row is deleted only after a 2xx, so delivery is at least once. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:249-256,319-322,542 @7.x]
- `mautic:webhooks:process` does nothing (exit 0) in immediate mode. It takes no lock. After a successful batch it keeps draining the same Webhook until the queue is empty or `webhook_time_limit` (600 s) has elapsed. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:59-63 @7.x] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:366-381,713-719 @7.x]
- Success means any 2xx. A non-2xx response increments `retries` on every row in the batch. Mautic retries those rows after `webhook_retry_delay` (3600 s), with no maximum retry count. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:309-331,534-606 @7.x]
- Ordering: `ASC` (the default) sends oldest first. Previously failed rows sort **after** fresh rows. Nothing is ordered across Webhooks or across runs, so sort on `timestamp`. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:543-544,613-622 @7.x]
- A `410 Gone` response unpublishes the Webhook immediately. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:336-339 @7.x]
- After any other failure, the Webhook is "sick" when **none** of its newest `webhook_disable_limit` (100) logs is 2xx. A sick Webhook is marked unhealthy and killed. It is not killed when `disable_auto_unpublish` is true or when it was modified in the last 2 days. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:343-353,390-414 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:507-516 @7.x]
- The cron command skips an unhealthy Webhook for `webhook_health_check_time` (300 s). One success clears its health state. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:71-110 @7.x] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:426-435 @7.x]
- A "failing" notification is sent only after 1 h unhealthy, and then at most once per 24 h. A "stopped" notification is sent on kill. Recipients are the creator, or the modifier with the creator in CC, or all admins when there is no creator. Each gets an in-app notification plus an email (or the email goes to `webhook_notification_email_addresses`). [code: app/bundles/WebhookBundle/Service/WebhookService.php:33-69 @7.x] [code: app/bundles/WebhookBundle/Notificator/WebhookNotificationSender.php:47-115 @7.x]
- Each attempt writes exactly one `webhook_logs` row. The note is truncated to 190 chars, and a transport error is stored as `N/A` (counted as a failure). [code: app/bundles/WebhookBundle/Model/WebhookModel.php:358-361,445-463 @7.x] [code: app/bundles/WebhookBundle/Entity/Log.php:125-148 @7.x]
- Logs are trimmed to `webhook_log_max` (1000) per Webhook on every write. With `clean_webhook_logs_in_background`, `mautic:webhooks:delete_logs` does the trimming instead. The UI shows 100. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:445-463 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:50 @7.x]
- `webhook_timeout` (15 s) is **not applied**. The client is a plain Guzzle client with no timeout configured. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:729 @7.x] [code: app/bundles/CoreBundle/Config/services.php:314 @7.x]
- Private, loopback and link-local targets are refused unless listed in `webhook_allowed_private_addresses`. [code: app/bundles/WebhookBundle/Http/Client.php:34-39 @7.x]
- With `webhook_email_details = false`, email payloads drop `content`, `tokens` and `email.customHtml`/`plainText`. [code: app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:69-72,92-120 @7.x]
- API: on v1 `PUT /api/hooks/ID/edit`, `triggers` replaces the event list. On `PATCH`/`POST` it only adds. The API returns the secret in clear text. [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php:70-88 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:173-188 @7.x]

Payload-key tables for every event: references/behaviour.md §3.

### Verifying `Webhook-Signature` in a receiver
The algorithm is defined in `app/bundles/WebhookBundle/Http/Client.php:25-26`: `base64_encode(hash_hmac('sha256', $jsonPayload, $secret, true))`. Hash the **raw** body bytes before parsing JSON, and compare in constant time. [code: app/bundles/WebhookBundle/Http/Client.php:25-26 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/example_scripts.html]

```php
<?php
$secret   = getenv('MAUTIC_WEBHOOK_SECRET');
$raw      = file_get_contents('php://input');
$received = $_SERVER['HTTP_WEBHOOK_SIGNATURE'] ?? '';
$expected = base64_encode(hash_hmac('sha256', $raw, $secret, true));
if (!hash_equals($expected, $received)) {
    http_response_code(401);
    exit;
}
$data = json_decode($raw, true);                       // assoc array
foreach ($data['mautic.form_on_submit'] ?? [] as $item) { /* idempotent handling */ }
http_response_code(200);                               // any 2xx = success; 410 unpublishes the Webhook
```

```js
// Node / Express
const crypto = require('crypto');
const express = require('express');
const app = express();
app.post('/mautic', express.raw({ type: 'application/json' }), (req, res) => {
  const expected = crypto.createHmac('sha256', process.env.MAUTIC_WEBHOOK_SECRET)
    .update(req.body)                                   // Buffer of the raw body
    .digest();                                          // raw bytes
  const received = Buffer.from(req.get('Webhook-Signature') || '', 'base64');
  if (received.length !== expected.length || !crypto.timingSafeEqual(expected, received)) {
    return res.sendStatus(401);
  }
  const data = JSON.parse(req.body.toString('utf8'));
  for (const item of data['mautic.lead_post_save_new'] || []) { /* idempotent handling */ }
  res.sendStatus(200);
});
```
The docs' own samples compare with `===`, and the PHP sample calls `json_decode` without `true`. Do not copy those parts. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/example_scripts.html]

## Where it lives
| Concern | Path |
|---|---|
| Entities / tables | `app/bundles/WebhookBundle/Entity/{Webhook,Event,Log,WebhookQueue}.php` → `webhooks`, `webhook_events`, `webhook_logs`, `webhook_queue` |
| Queue, send, health, logs | `app/bundles/WebhookBundle/Model/WebhookModel.php` |
| HTTP + signature | `app/bundles/WebhookBundle/Http/Client.php` |
| Health window, notification throttle | `app/bundles/WebhookBundle/Service/WebhookService.php`, `Notificator/` |
| Event types (producers) | `app/bundles/{Lead,Email,Form,Page,Sms}Bundle/EventListener/WebhookSubscriber.php` |
| Events | `app/bundles/WebhookBundle/WebhookEvents.php` |
| Commands | `Command/ProcessWebhookQueuesCommand.php` (`mautic:webhooks:process`), `Command/DeleteWebhookLogsCommand.php` (`mautic:webhooks:delete_logs`) |
| UI / AJAX test / API | `Controller/WebhookController.php` (`/s/webhooks`), `Controller/AjaxController.php`, `Controller/Api/WebhookApiController.php` (`/api/hooks`), `Entity/Webhook.php` (`/api/v2/webhooks`) |
| Config params | `app/bundles/WebhookBundle/Config/config.php:45-61`; notification recipients `app/bundles/NotificationBundle/Config/config.php:123-124` |
| Permissions | `Security/Permissions/WebhookPermissions.php` (`webhook:webhooks:*`) |
| Tests | `app/bundles/WebhookBundle/Tests/{Functional,Unit}/` |

[code: app/bundles/WebhookBundle/Config/config.php:7-61 @7.x] [code: app/bundles/WebhookBundle/Security/Permissions/WebhookPermissions.php:16-17 @7.x] Full map: references/code-map.md.

## How to change or extend it
- **Add a webhook event type from a Plugin.** Subscribe to `WebhookEvents::WEBHOOK_ON_BUILD` and call `$event->addEvent('myplugin.thing_happened', ['label' => ..., 'description' => ...])`. Keep the key at 50 chars or fewer and unique, because duplicates throw. [code: app/bundles/WebhookBundle/Event/WebhookBuilderEvent.php:26-36 @7.x] [code: app/bundles/WebhookBundle/Entity/Event.php:39-65 @7.x]
- In your domain listener, call `WebhookModel::queueWebhooksByType('myplugin.thing_happened', ['thing' => $entity], ['thingDetails'])`. Always pass serializer groups, because no groups serialises every `*Details` property. Do not send HTTP yourself: the model handles mode, signing, logging and health. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:229-236,666-687 @7.x]
- To change a queued payload (redact or enrich it), listen to `WEBHOOK_QUEUE_ON_ADD`, as EmailBundle does. Use `WEBHOOK_KILL` to alert on auto-disable. Use `WebhookNotificationEvent::setCanSend(false)` to suppress notices. [code: app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:92-120 @7.x] [code: app/bundles/WebhookBundle/Notificator/WebhookNotificationSender.php:37-40 @7.x]
- On 8.x, key subscribers on `WebhookBuilderEvent::class`, `WebhookQueueEvent::class` and `WebhookKillEvent::class`. Old constant keys load but never fire. [PR #17202]
- Treat event-type strings and payload keys as public API. Renaming a key breaks every receiver and every stored `webhook_events` row. Add keys; do not rename or remove them. [code: app/bundles/WebhookBundle/Entity/Event.php:39-65 @7.x]
- When changing an entity that appears in payloads (Contact, Company, Email, Submission, Hit), check its JMS `*Details` groups: they decide the webhook payload. Update the sample JSON in `Assets/WebhookPayload/` and the devdocs event page together. [code: app/bundles/WebhookBundle/Controller/AjaxController.php:103-162 @7.x]
- A schema change to the four tables needs a migration in `app/migrations/` (see references/version-notes.md for the precedent migrations). [code: app/migrations/Version20241004132307.php:26-32 @7.x]
- New config parameters go in `WB/Config/config.php`. Only add them to `ConfigType` if admins need them in the UI; limits are currently local.php-only. [code: app/bundles/WebhookBundle/Form/Type/ConfigType.php:19-81 @7.x]

## How to test it
- Use `MauticMysqlTestCase` with `ClientMockTrait`, and append Guzzle mock responses to `getClientMockHandler()`. Force `queue_mode = command_process` through `setUpSymfony($this->configParams + [...])`. Run `testSymfonyCommand(ProcessWebhookQueuesCommand::COMMAND_NAME, ['--webhook-id' => $id])`. [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:24-82 @7.x] [code: app/bundles/CoreBundle/Test/Guzzle/ClientMockTrait.php:9-17 @7.x]
- Copy from these tests:
  - `Tests/Functional/WebhookFunctionalTest.php` (queue, range mode, notifications, unhealthy recovery)
  - `Tests/Functional/Model/WebhookModelProcessFailureTest.php` (kill rules)
  - `Tests/Functional/Model/WebhookModelTest.php` (ordering)
  - `Tests/Unit/Http/ClientTest.php` (headers and signature)
  - `Tests/Functional/Controller/AjaxControllerTest.php` (test payload, private address)

  [code: app/bundles/WebhookBundle/Tests/Functional/Model/WebhookModelProcessFailureTest.php:37-115 @7.x]
- A good regression test asserts four things: the queue row count after the trigger; the signature recomputed from the mocked request body; one log row per attempt; and the publish/health state after failures. Skeleton: references/test-patterns.md. [code: app/bundles/WebhookBundle/Tests/Unit/Http/ClientTest.php:39-75 @7.x]

## Version notes
- 7.x schema history includes compressed queue payloads, `retries`/`date_modified` on queue rows (retry after delay), a BIGINT queue id and health columns on `webhooks`. Release mapping is in mautic-upgrades-and-versions. [code: app/migrations/Version20240228132306.php:24-39 @7.x] [code: app/migrations/Version20241004132307.php:26-32 @7.x]
- 7.x adds `/api/v2/webhooks` (API Platform) next to v1 `/api/hooks`. [code: app/bundles/WebhookBundle/Entity/Webhook.php:28-121 @7.x]
- 8.x dispatches by event class. `WEBHOOK_PRE/POST_SAVE`, `PRE/POST_DELETE` and `WEBHOOK_KILL` are removed in favour of `Webhook{Pre,Post}{Save,Delete}Event` and `WebhookKillEvent`. `WebhookEvent` is abstract. The Campaign action moves to `ON_CAMPAIGN_BATCH_ACTION`. [PR #17085] [PR #17202] [PR #17654]
- 8.x keeps the webhook type strings (`mautic.lead_post_save_new`, …), so receivers need no change. [PR #17218]
- In 8.0, `company_soft_delete` is explicitly "not a Webhook event type". [devdocs: https://devdocs.mautic.org/en/8.0/webhooks/events/company_soft_delete.html]

Details: references/version-notes.md.

## Pitfalls
- "Webhook-Signature never matches" usually means the receiver hashed re-serialised JSON instead of the raw body, or hex-encoded the digest. Mautic uses the raw HMAC bytes, base64-encoded. [code: app/bundles/WebhookBundle/Http/Client.php:25-26 @7.x]
- Queued mode with no cron entry for `mautic:webhooks:process` means nothing is ever sent. Immediate mode with the cron entry means the command does nothing. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:59-63 @7.x]
- Immediate mode adds receiver latency to Form submits, Contact saves and Segment rebuilds. A Segment rebuild produces one `lead_list_change` row per Contact per Webhook. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:249-256 @7.x] [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:266-300 @7.x]
- A Webhook edited within the last 2 days is never auto-killed, which can hide a broken endpoint during testing. [code: app/bundles/WebhookBundle/Entity/Webhook.php:507-516 @7.x]
- A single 2xx in the last 100 logs keeps a mostly failing Webhook published. [code: app/bundles/WebhookBundle/Entity/LogRepository.php:75-119 @7.x]
- There is no retry cap and no lock, so overlapping cron runs or crashes cause duplicates. Make receivers idempotent; `email_on_send` has `idHash` for this. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:534-606 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_send.html#event-properties]
- In delete events, use the top-level `id`. The nested object's `id` is null. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:184-201 @7.x]
- Company, Contact-company and Segment-change payloads pass no serializer groups and can be very large. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:224-300 @7.x]
- "Send Test Payload" sends nothing for event types without a sample file, including all Plugin types (the plugin path lookup is broken). [code: app/bundles/WebhookBundle/Controller/AjaxController.php:116-130 @7.x]
- `WEBHOOK_PRE_EXECUTE`/`WEBHOOK_POST_EXECUTE` are dead constants and never fire. [code: app/bundles/WebhookBundle/WebhookEvents.php:73-82 @7.x]
- The Campaign "Send a webhook" action is unsigned and unqueued, and it treats only 200/201 as success. Do not confuse it with Webhooks. [code: app/bundles/WebhookBundle/Helper/CampaignHelper.php:79-116 @7.x]
- Doc vs code (code wins): docs key the deleted Contact as `company` in `lead_post_delete` (the code uses `contact`). Docs say `email_on_open` carries the `email_on_send` payload (the code sends only `stat`). Docs list `company_soft_delete` as a webhook event (it is not selectable) and omit `lead_list_change`. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_delete.html] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_open.html] [code: app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:77-90 @7.x]
- REST docs: `triggers` is documented as required on create, but the entity accepts none. The list filter is documented as `publishedOnly`, but the code reads `published`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#create-webhook] [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:167 @7.x]
- Open question: the effective HTTP timeout for webhook delivery. `webhook_timeout` is unused, and Guzzle's default is assumed to be no timeout [unverified]. [code: app/bundles/CoreBundle/Config/services.php:314 @7.x]
- Open question: the `page_on_hit` docs list `dateHit` twice, once as "always null for webhooks". This is not resolved against code. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/page_on_hit.html#page-visit-properties]

## Related skills
- mautic-rest-api: API auth, v1/v2 conventions and errors behind `/api/hooks` and `/api/v2/webhooks`.
- mautic-contacts: Contact save/identify semantics, DNC and Company links that drive the `lead_*`/`company_*` events.
- mautic-emails: email sending/open tracking behind `email_on_send`/`email_on_open`, and inbound transport callbacks.
- mautic-forms: Form submission behind `form_on_submit`.
- mautic-pages-and-tracking: page hits and tracking behind `page_on_hit`.
- mautic-points-and-stages: points changes behind `lead_points_change`.
- mautic-cron-and-queues: scheduling `mautic:webhooks:process` and `mautic:webhooks:delete_logs`.
- mautic-plugin-development: Plugin bundle structure, subscribers and services for custom webhook event types.
- mautic-testing: `MauticMysqlTestCase`, test DB and running PHPUnit.
- mautic-upgrades-and-versions: release mapping of migrations and the 8.x event-class migration.

## Reference files
- references/behaviour.md: the full numbered specification, with payload-key tables per event, delivery, retries, health, logs, API and doc discrepancies. Open it for any exact rule.
- references/code-map.md: entities/tables, model methods with line ranges, events, routes, commands, every config parameter with defaults, and permissions.
- references/docs-digest.md: what devdocs say, with URLs, procedures, the per-event page index and terminology.
- references/test-patterns.md: base classes, Guzzle mocking, fixtures, a signature regression skeleton and assertions to make.
- references/version-notes.md: schema history migrations, 7.x notes and the 8.x event-class delta, with a porting snippet.
- references/pr-history.md: not yet generated; PR-derived history is added in a later pass.
