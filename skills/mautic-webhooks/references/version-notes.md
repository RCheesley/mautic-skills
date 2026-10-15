# Webhooks — version notes

## 5.x / 6.x → 7.x (schema history)

The inputs do not map these migrations to release numbers; dates come from the migration class names. Check `mautic-upgrades-and-versions` for the release mapping.

| Migration | Change | Effect on behaviour |
|---|---|---|
| `Version20221014061125` | Index `webhook_id_date_added` on `webhook_logs` | Faster log trimming and `isSick()` queries |
| `Version20221014081742` | `webhook_queue.payload_compressed` MEDIUMBLOB added | Queued payloads stored gzip-compressed |
| `Version20240228132306` | Drop `webhook_queue.payload`; add `retries`, `date_modified` | Failed rows kept and retried after `webhook_retry_delay` instead of being lost |
| `Version20240607092418` | `webhook_queue.id` → BIGINT | High-volume queues no longer overflow INT |
| `Version20241004132307` | `webhooks.marked_unhealthy_at`, `unhealthy_since` (plus `last_notification_sent_at`) | Health window and throttled failure notifications |

[code: app/migrations/Version20221014061125.php:22 @7.x] [code: app/migrations/Version20221014081742.php:24 @7.x] [code: app/migrations/Version20240228132306.php:24-39 @7.x] [code: app/migrations/Version20240607092418.php:25 @7.x] [code: app/migrations/Version20241004132307.php:26-32 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:165-167 @7.x]

## 5.x and 6.x (from pull requests)

- Release mapping for two of the migrations above: `Version20221014081742` (compressed payload) shipped in 5.0, and `Version20240228132306` (drop `payload`, add `retries`) shipped in 7.0. [PR #11589] [PR #15283]
- 5.0: queue payloads stored compressed; the Webhook UI moved to Twig; `mautic:webhooks:process` exits non-zero on errors (also 4.4.8); `webhook_log_max` cast to int. [PR #11589] [PR #11382] [PR #12203] [PR #11963] [PR #11640]
- 5.1: queue fetched in id order instead of `date_added`; "Send email details" (`webhook_email_details`); range mode `--min-id`/`--max-id`; failed request payloads written to the file log; queue iteration with `toIterable()`. [PR #11424] [PR #13447] [PR #13448] [PR #13815] [PR #13112]
- 6.x: none found in the 158 harvested API and webhooks PRs. [PR #13815]

## 7.x minors

- `formType` on Form objects in payloads is deprecated as of 7.1 ("all Forms function identically"). [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_send.html#unsubscribe-form-properties]
- 7.0.0: failed rows are retried after `webhook_retry_delay`; unhealthy Webhooks are skipped for `webhook_health_check_time`; failure notifications; kills skip Webhooks edited in the last 2 days; `disable_auto_unpublish`. [PR #15283] [PR #15495]
- 7.0.1: the test payload matches real deliveries, and a failed test shows the real error. [PR #15799] [PR #15863]
- 7.1.0: requests send `User-Agent: Webhook` instead of Guzzle's default. [PR #15728]
- 7.2.0: `mautic:webhooks:process` exits 0 when no Webhooks are published; Campaign webhook data with equal values under different keys keeps both. [PR #15135] [PR #16899]
- 7.x adds the API Platform resource `/api/v2/webhooks` alongside v1 `/api/hooks`. [code: app/bundles/WebhookBundle/Entity/Webhook.php:28-121 @7.x]
- 7.2 still exposes `LeadEvents::COMPANY_SOFT_DELETE` (`mautic.company_soft_delete`) for Plugins; it is not a webhook type. [code: app/bundles/LeadBundle/LeadEvents.php:627-633 @7.x]

## 8.x delta (8.x @ 11599729491, unreleased)

- Event dispatch by class name. `WebhookEvents::WEBHOOK_ON_BUILD`, `WEBHOOK_QUEUE_ON_ADD` and `WEBHOOK_ON_REQUEST` constants still exist but are dispatched as `WebhookBuilderEvent`, `WebhookQueueEvent`, `WebhookRequestEvent`. A Plugin keyed on the old constant loads but **never fires**: key on the class. [PR #17202]
- Removed constants and replacements: `WEBHOOK_PRE_SAVE` → `WebhookPreSaveEvent`, `WEBHOOK_POST_SAVE` → `WebhookPostSaveEvent`, `WEBHOOK_PRE_DELETE` → `WebhookPreDeleteEvent`, `WEBHOOK_POST_DELETE` → `WebhookPostDeleteEvent`, `WEBHOOK_KILL` → `WebhookKillEvent`. `WebhookEvent` became `abstract`. [PR #17085] [PR #17202] [PR #17654]
- `ON_CAMPAIGN_TRIGGER_ACTION` removed: the `campaign.sendwebhook` action registers `batchEventName` = `WebhookEvents::ON_CAMPAIGN_BATCH_ACTION` (`mautic.webhook.on_campaign_batch_action`) and listens on `PendingEvent`. [PR #17085] [PR #17654]
- Signature changes: `WebhookModel::getEventWebooksByType(string)`, `processWebhooks(array|Paginator)`, `Webhook::getPayload(): ?array`. [PR #17202]
- Webhook **type identifiers are unchanged**: the strings `mautic.lead_post_save_new`, `mautic.email_on_send`, `mautic.form_on_submit`, etc. remain as kept constants (`LeadEvents::LEAD_POST_SAVE`, `EmailEvents::EMAIL_ON_SEND`, `FormEvents::FORM_ON_SUBMIT`, …), so existing subscriptions and receivers keep working. The underlying domain events are dispatched by class (`LeadPostSaveEvent`, `EmailOpenEvent`, `SubmissionEvent`, `PageHitEvent`, `SmsSendEvent`, …). [PR #17218] [PR #17223]
- `company_soft_delete` is dispatched as `CompanySoftDeleteEvent`; the 8.0 docs state it "isn't a Webhook event type". [devdocs: https://devdocs.mautic.org/en/8.0/webhooks/events/company_soft_delete.html]
- Webhook user docs, getting started, example scripts and event pages are unchanged in 8.0. [devdocs: https://devdocs.mautic.org/en/8.0/webhooks/getting_started.html]
- Devdocs list `WebhookEvent` as `final`; 8.x code has it `abstract` — trust the code. `WebhookBuilderEvent` and `WebhookNotificationEvent` are listed as `final`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- 8.x does not yet contain the 7.2.1 fixes (no forward merge since 7.2.0). [PR #17253]

Plugin porting snippet for 8.x:

```php
public static function getSubscribedEvents(): array
{
    return [
        WebhookBuilderEvent::class => ['onWebhookBuild', 0],   // was WebhookEvents::WEBHOOK_ON_BUILD
        WebhookKillEvent::class    => ['onWebhookKill', 0],    // was WebhookEvents::WEBHOOK_KILL
    ];
}
```
[PR #17202]
