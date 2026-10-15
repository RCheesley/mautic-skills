# Webhooks — behaviour specification (Mautic 7.x)

Authoritative for Mautic 7.x (commit 419a08a9b35: release 7.2.1 plus unreleased merged PRs). Paths are relative to the Mautic repo root; `WB` = `app/bundles/WebhookBundle`.
Every item ends with its source. Where docs and code disagree, the code wins and the discrepancy is listed in §10.

## Contents
1. Terms
2. Configuring a Webhook
3. Subscribable event types (with payload-key tables)
4. Payload envelope and HTTP request
5. Immediate vs queued delivery
6. `mautic:webhooks:process`, ordering and retries
7. Failure handling, health, auto-disable and notifications
8. Logs and log limits
9. Webhook REST API (v1 `/api/hooks`, v2 `/api/v2/webhooks`)
10. Doc/code discrepancies
11. Campaign action "Send a webhook" (contrast)
12. Extension points (how a Plugin adds an event type)

---

## 1. Terms

- **Webhook**: a saved configuration (name, POST URL, secret, subscribed event types, publish state) stored in table `webhooks`. [code: app/bundles/WebhookBundle/Entity/Webhook.php:135-170 @7.x]
- **Event type** (also "trigger" in the API): a string such as `mautic.lead_post_save_new` stored per Webhook in `webhook_events.event_type` (max 50 chars). [code: app/bundles/WebhookBundle/Entity/Event.php:39-65 @7.x]
- **Queue row**: one event payload waiting for delivery to one Webhook, table `webhook_queue`. [code: app/bundles/WebhookBundle/Entity/WebhookQueue.php:33-58 @7.x]
- **Log row**: one delivery attempt record, table `webhook_logs`. [code: app/bundles/WebhookBundle/Entity/Log.php:38-59 @7.x]
- **Unhealthy**: a Webhook whose recent deliveries all failed; it is skipped for a cool-down window. **Killed**: the Webhook is unpublished automatically. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:343-353,408-435 @7.x]
- **Contact** = code `Lead`; **Segment** = code `LeadList`; **Channel subscription** = Do Not Contact (DNC) entry. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_new.html]

## 2. Configuring a Webhook

2.1 Create Webhooks under the cog menu → Webhooks → New; the admin route is `/s/webhooks` and the menu entry needs `webhook:webhooks:viewown` or `viewother`. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#creating-a-webhook] [code: app/bundles/WebhookBundle/Config/config.php:7-43 @7.x]

2.2 `name` and `webhookUrl` are required; `webhookUrl` must pass Symfony's `Url` constraint. Saving with no events selected is allowed by the entity validation. [code: app/bundles/WebhookBundle/Entity/Webhook.php:191-227 @7.x]

2.3 `eventsOrderbyDir` must be null, `ASC` or `DESC`; null means "use the global `events_orderby_dir`". [code: app/bundles/WebhookBundle/Entity/Webhook.php:191-227 @7.x] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:613-622 @7.x]

2.4 The form pre-fills `secret` with `EncryptionHelper::generateKey()`; a Webhook saved without a secret (e.g. via API) gets one generated on save. [code: app/bundles/WebhookBundle/Form/Type/WebhookType.php:68-80 @7.x] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:153-160 @7.x]

2.5 Only published Webhooks receive events: event lookup filters `isPublished = 1`. Unpublish a Webhook to pause it. Events raised while it is unpublished are not queued for it. [code: app/bundles/WebhookBundle/Entity/EventRepository.php:15-30 @7.x]

2.6 Global settings (Configuration → Webhook Settings) expose only `queue_mode`, `events_orderby_dir`, `webhook_email_details` and `webhook_allowed_private_addresses`. All limits and timeouts must be set in `config/local.php`. [code: app/bundles/WebhookBundle/Form/Type/ConfigType.php:19-81 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#configuring-webhooks]

2.7 Docs recommend one Webhook per consuming app, to limit where each secret is exposed. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#creating-a-webhook]

2.8 Saving or deleting a Webhook writes an audit-log entry (bundle `webhook`). Changes to the three health columns do not update `date_modified`/`modified_by`. [code: app/bundles/WebhookBundle/EventListener/WebhookSubscriber.php:33-65 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:583 @7.x]

2.9 Deleting a Webhook deletes its events, logs and queued rows through DB cascades. Unchecking an event type in the form deletes that `webhook_events` row (orphan removal) and, by cascade, its queued rows. [code: app/bundles/WebhookBundle/Entity/Webhook.php:145-152 @7.x] [code: app/bundles/WebhookBundle/Entity/WebhookQueue.php:39-52 @7.x]

2.10 **Send Test Payload** (AJAX `webhook:sendHookTest`) posts the sample JSON of each selected event type to the URL in the form, signed with the secret in the form, and reports the status. A missing URL, no selected events, or a private target address produces an error message. [code: app/bundles/WebhookBundle/Controller/AjaxController.php:16-52 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#testing-a-webhook]

2.11 Sample payloads are read from `<Bundle>/Assets/WebhookPayload/<bundle>_<event>.json`. Missing files are skipped silently, so company, segment-change, email-send and SMS events send nothing in the test. Samples exist for the five `lead_*` contact events, `form_on_submit`, `email_on_open` and `page_on_hit`. [code: app/bundles/WebhookBundle/Controller/AjaxController.php:103-162 @7.x]

2.12 Target URLs that resolve to private, loopback or link-local addresses are refused (`PrivateAddressException`, recorded as a failed attempt) unless the address is listed in `webhook_allowed_private_addresses`. [code: app/bundles/WebhookBundle/Http/Client.php:34-39 @7.x]

## 3. Subscribable event types

The list is built by dispatching `WebhookEvents::WEBHOOK_ON_BUILD`; it is cached per PHP process and sorted by translated label; a duplicate key throws. Fetch the live list with `GET /api/hooks/triggers`. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:202-215 @7.x] [code: app/bundles/WebhookBundle/Event/WebhookBuilderEvent.php:26-52 @7.x]

Core registers 14 event types (no plugin under `plugins/` registers any). Every delivered item also gets a `timestamp` key (§4.2). [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:50-128 @7.x] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:485-527 @7.x]

### 3.1 Summary

| # | Event type | Fires when | Registered at |
|---|---|---|---|
| 1 | `mautic.lead_post_save_new` | A Contact save sets `dateIdentified` (anonymous → identified) | `app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:50-56` |
| 2 | `mautic.lead_post_save_update` | Any other Contact save with changes, Contact identified | same, L59-65 |
| 3 | `mautic.lead_points_change` | Contact points change | L68-74 |
| 4 | `mautic.lead_post_delete` | Contact deleted | L77-83 |
| 5 | `mautic.lead_channel_subscription_changed` | DNC / channel subscription status changes | L86-92 |
| 6 | `mautic.lead_company_change` | Contact added to / removed from a Company | L95-101 |
| 7 | `mautic.company_post_save` | Company created or updated | L104-110 |
| 8 | `mautic.company_post_delete` | Company deleted | L113-119 |
| 9 | `mautic.lead_list_change` | Contact added to / removed from a Segment | L122-128 |
| 10 | `mautic.email_on_send` | Email sent to a Contact | `app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:48` |
| 11 | `mautic.email_on_open` | Email open recorded | same, L49 |
| 12 | `mautic.form_on_submit` | Form submitted | `app/bundles/FormBundle/EventListener/WebhookSubscriber.php:41` |
| 13 | `mautic.page_on_hit` | Landing Page or tracked page hit | `app/bundles/PageBundle/EventListener/WebhookSubscriber.php:41` |
| 14 | `mautic.sms_on_send` | Text Message sent | `app/bundles/SmsBundle/EventListener/WebhookSubscriber.php:34-40` |

[code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:50-128 @7.x] [code: app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:48-49 @7.x] [code: app/bundles/FormBundle/EventListener/WebhookSubscriber.php:41 @7.x] [code: app/bundles/PageBundle/EventListener/WebhookSubscriber.php:41 @7.x] [code: app/bundles/SmsBundle/EventListener/WebhookSubscriber.php:34-40 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/index.html]

### 3.2 Payload-key tables per event

Serializer groups decide which nested properties appear. "none" means no groups are passed, so JMS serialises every property that has `*Details` metadata (large payloads). [code: app/bundles/WebhookBundle/Model/WebhookModel.php:666-687 @7.x]

**1–2. `mautic.lead_post_save_new` / `mautic.lead_post_save_update`** — source `LeadEvents::LEAD_POST_SAVE`, listener `onLeadNewUpdate`. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:131-160 @7.x]

| Key | Type | Notes |
|---|---|---|
| `contact` | Contact object | Groups `leadDetails, userList, publishDetails, ipAddress, doNotContactList, tagList` |
| `timestamp` | ISO-8601 string | Added at delivery from the queue `dateAdded` |

- `_new` fires when the save's changes include `dateIdentified`; otherwise `_update`. Anonymous Contacts and saves with no changes fire neither. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:131-160 @7.x]
- Contact object keys (docs): `id`, `isPublished`, `dateAdded`, `createdBy`, `createdByUser`, `dateIdentified`, `dateModified`, `modifiedBy`, `modifiedByUser`, `points`, `color`, `preferredProfileImage`, `fields`, `lastActive`, `owner`, `ipAddresses`, `tags`, `doNotContact`, `frequencyRules`, `utmtags`, `stage`. `frequencyRules`/`utmtags` are "not populated" and `stage` "not fully populated" for webhooks. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_new.html#contact-properties]
- `fields` is grouped by `core`, `social`, `personal`, `professional`, each keyed by field alias with `id, group, label, alias, type, properties, value, normalizedValue`; it is an empty array when no fields exist. Read a value as `contact.fields.core.firstname.value`. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_new.html#custom-field-properties]
- DNC entries: `id`, `reason` (1 unsubscribed by Contact, 2 bounced, 3 manual), `channel`, `channelId`. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_new.html#channel-subscription-properties]

**3. `mautic.lead_points_change`** — source `LEAD_POINTS_CHANGE`. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:162-182 @7.x]

| Key | Type | Notes |
|---|---|---|
| `contact` | Contact object | Same groups as 1–2 |
| `points.old_points` | int | |
| `points.new_points` | int | |
| `timestamp` | ISO-8601 string | |

[devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_points_change.html]

**4. `mautic.lead_post_delete`** — source `LEAD_POST_DELETE`. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:184-201 @7.x]

| Key | Type | Notes |
|---|---|---|
| `id` | int | The deleted Contact's ID (`deletedId`). Use this. |
| `contact` | Contact object | Its own `id` is null after deletion. Groups `leadDetails, userList, publishDetails, doNotContactList, ipAddress` (no `tagList`) |
| `timestamp` | ISO-8601 string | |

[devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_delete.html]

**5. `mautic.lead_channel_subscription_changed`** — source `LeadEvents::CHANNEL_SUBSCRIPTION_CHANGED`. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:203-222 @7.x]

| Key | Type | Notes |
|---|---|---|
| `contact` | Contact object | Same groups as 1–2 |
| `channel` | string | e.g. `email`, `sms` |
| `old_status` | string | `contactable`, `bounced`, `manual`, `unsubscribed` |
| `new_status` | string | same values |
| `timestamp` | ISO-8601 string | |

[devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_channel_subscription_changed.html]

**6. `mautic.lead_company_change`** — source `LEAD_COMPANY_CHANGE`; one queue row per Contact. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:224-242 @7.x]

| Key | Type | Notes |
|---|---|---|
| `added` | bool | true added, false removed |
| `contact` | Contact object | No groups → full `*Details` graph |
| `company` | Company object | No groups |
| `timestamp` | ISO-8601 string | |

[devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_company_change.html]

**7. `mautic.company_post_save`** — source `COMPANY_POST_SAVE`. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:244-252 @7.x]

| Key | Type | Notes |
|---|---|---|
| `company` | Company object | No groups. Docs list `id, isPublished, dateAdded, createdBy, createdByUser, dateModified, modifiedBy, modifiedByUser, name, address1, address2, city, state, zipcode, country, phone, website, industry, score, fields` |
| `timestamp` | ISO-8601 string | |

[devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/company_post_save.html#company-properties]

**8. `mautic.company_post_delete`** — source `COMPANY_POST_DELETE`. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:254-264 @7.x]

| Key | Type | Notes |
|---|---|---|
| `id` | int | Deleted Company ID; use this |
| `company` | Company object | Its `id` is null |
| `timestamp` | ISO-8601 string | |

[devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/company_post_delete.html]

**9. `mautic.lead_list_change`** — sources `LEAD_LIST_CHANGE` and `LEAD_LIST_BATCH_CHANGE`; one queue row per Contact (a batch Segment rebuild produces one row per affected Contact). [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:266-300 @7.x]

| Key | Type | Notes |
|---|---|---|
| `contact` | Contact object | No groups |
| `segment` | Segment object | No groups |
| `action` | string | `added` or `removed` |
| `timestamp` | ISO-8601 string | |

Not documented on devdocs (see §10). [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/index.html]

**10. `mautic.email_on_send`** — source `EMAIL_ON_SEND`. Internal/test sends and sends without a Contact are skipped. [code: app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:52-75 @7.x]

| Key | Type | Notes |
|---|---|---|
| `email` | Email object | No groups; `customHtml`/`plainText` removed when `webhook_email_details` = false |
| `contact` | Contact object | |
| `contentHash` | string | Identifies unique content incl. template |
| `idHash` | string | Unique to this send to this Contact |
| `subject` | string | Rendered subject |
| `source` | array | `[component, id]`, e.g. `["campaign.event", 1]` |
| `headers` | object | Headers set on the sent Email |
| `content` | string | Sent HTML — only when `webhook_email_details` = true |
| `tokens` | object | Personalised token values — only when `webhook_email_details` = true |
| `timestamp` | ISO-8601 string | |

[code: app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:69-72,92-120 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_send.html#event-properties]

**11. `mautic.email_on_open`** — source `EMAIL_ON_OPEN`. [code: app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:77-90 @7.x]

| Key | Type | Notes |
|---|---|---|
| `stat` | Email stat object | Groups `statDetails, leadList, emailDetails`; `stat.email.customHtml`/`plainText` removed when `webhook_email_details` = false |
| `timestamp` | ISO-8601 string | |

Docs say the payload equals `email_on_send`; the code sends only `stat` (§10). Opens may come from proxies or bots. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_open.html]

**12. `mautic.form_on_submit`** — source `FORM_ON_SUBMIT`. [code: app/bundles/FormBundle/EventListener/WebhookSubscriber.php:44-59 @7.x]

| Key | Type | Notes |
|---|---|---|
| `submission` | Submission object | Groups `submissionDetails, ipAddress, leadList, pageList, formList`. Docs: `id, ipAddress, form{id,name,alias,category}, lead, trackingId, dateSubmitted, referer, results{alias: value}, page` (`page` null unless embedded on a Landing Page) |
| `timestamp` | ISO-8601 string | |

[devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/form_on_submit.html]

**13. `mautic.page_on_hit`** — source `PAGE_ON_HIT`. [code: app/bundles/PageBundle/EventListener/WebhookSubscriber.php:44-58 @7.x]

| Key | Type | Notes |
|---|---|---|
| `hit` | Page hit object | Groups `hitDetails, emailDetails, pageList, leadList`. Docs: `id, dateHit, page, lead, ipAddress, country, region, city, isp, organization, code, referer, url, urlTitle, userAgent, remoteHost, pageLanguage, browserLanguages, trackingId, source, sourceId, query, redirect, email` (`email` deprecated; use `source`/`sourceId`) |
| `timestamp` | ISO-8601 string | |

[devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/page_on_hit.html#page-visit-properties]

**14. `mautic.sms_on_send`** — source `SMS_ON_SEND`. [code: app/bundles/SmsBundle/EventListener/WebhookSubscriber.php:43-53 @7.x]

| Key | Type | Notes |
|---|---|---|
| `smsId` | int | Text Message ID |
| `contact` | Contact object | No groups |
| `content` | string | Text sent |
| `timestamp` | ISO-8601 string | |

[devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/sms_on_send.html]

3.3 Dates inside payloads are serialised by JMS in ISO-8601 (`c`) format in UTC, e.g. `2017-06-19T09:31:18+00:00`. [code: app/config/config.php:281-286 @7.x]

3.4 Payloads are serialised **when queued**, not when delivered. A Contact edited between queueing and delivery is delivered with the old values. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:229-279,666-687 @7.x]

3.5 `mautic.company_soft_delete` exists as a Contact-bundle event constant in 7.2 but no webhook subscriber registers it, so it is not a webhook event type. [code: app/bundles/LeadBundle/LeadEvents.php:627-633 @7.x] [devdocs: https://devdocs.mautic.org/en/8.0/webhooks/events/company_soft_delete.html]

## 4. Payload envelope and HTTP request

4.1 A delivery body is a JSON object keyed by event type; each value is a list of event payloads: `{"mautic.lead_post_save_new":[{...,"timestamp":"..."}],"mautic.form_on_submit":[...]}`. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:485-527 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html]

4.2 Each item is the queued payload plus `timestamp` = the queue row's `dateAdded` in ISO-8601. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:485-527 @7.x]

4.3 In queued mode one request may mix up to `webhook_limit` (10) items of different types; in immediate mode each request carries exactly one item. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:485-527,542 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#background-workflow]

4.4 If the Webhook entity has a static `payload` set (API-only field), that payload is sent instead of the queued events. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:485-527 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:28-121 @7.x]

4.5 The request is `POST <webhookUrl>` with headers `Content-Type: application/json`, `X-Origin-Base-URL: <site_url>`, `User-Agent: Webhook` and `Webhook-Signature`. The body is `json_encode($payload)`. [code: app/bundles/WebhookBundle/Http/Client.php:23-41 @7.x] [code: app/bundles/WebhookBundle/Tests/Unit/Http/ClientTest.php:39-75 @7.x]

4.6 **Signature algorithm**: `Webhook-Signature = base64_encode(hash_hmac('sha256', $jsonBody, $secret, true))` — HMAC-SHA256 over the exact body bytes, raw binary digest, then standard base64. When the secret is null the header value is null. [code: app/bundles/WebhookBundle/Http/Client.php:25-30 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#securing-a-webhook]

4.7 Verify by computing the same HMAC over the raw request body before any JSON parsing, and comparing with a constant-time function. Reject mismatches. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/example_scripts.html]

4.8 Use `X-Origin-Base-URL` to tell several Mautic instances apart at one receiver. [code: app/bundles/WebhookBundle/Http/Client.php:29 @7.x]

4.9 **Timeout**: `webhook_timeout` (15 s) is read by the model but never passed to the HTTP client; the request goes through `mautic.http.client`, a `GuzzleHttp\Client` registered with no options. No Mautic-side request timeout is therefore applied [unverified: Guzzle's own default is assumed to be "no timeout"]. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:729 @7.x] [code: app/bundles/WebhookBundle/Http/Client.php:41 @7.x] [code: app/bundles/CoreBundle/Config/services.php:314 @7.x]

## 5. Immediate vs queued delivery

5.1 `queue_mode` = `immediate_process` (default): the queue row is not persisted; it is POSTed synchronously inside the request that raised the event (one HTTP call per event per Webhook). A failure is logged but never retried. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:249-256 @7.x] [code: app/bundles/WebhookBundle/Config/config.php:45-61 @7.x]

5.2 `queue_mode` = `command_process`: the row is persisted to `webhook_queue` (payload gzip-compressed at level 9 in `payload_compressed`) and delivered later by `mautic:webhooks:process`. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:249-256 @7.x] [code: app/bundles/WebhookBundle/Entity/WebhookQueue.php:92-117 @7.x]

5.3 UI labels: "Process Events Immediately" and "Queue Events Only - Process Via CLI Command". [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#configuring-webhooks]

5.4 Delivery guarantee: queued mode is at-least-once (a row is deleted only after a 2xx; a crash between send and delete resends it). Immediate mode is at-most-once. Receivers must be idempotent. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:249-256,319-322 @7.x]

5.5 Immediate mode slows the originating request (a Form submit, a Contact save, a Segment rebuild) by the receiver's response time, for every subscribed Webhook. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:249-256 @7.x]

5.6 In immediate mode, rows left in `webhook_queue` from an earlier queued period are also flushed after a successful send. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:366-381 @7.x]

5.7 `WEBHOOK_QUEUE_ON_ADD` is dispatched for every queue row in both modes, before it is persisted or sent, so listeners can rewrite the payload. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:262-279 @7.x]

## 6. `mautic:webhooks:process`, ordering and retries

6.1 The command exits 0 with a message unless `queue_mode = command_process`. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:59-63 @7.x]

6.2 Options: `--webhook-id|-i` (one Webhook), `--min-id`, `--max-id` (range mode, only with `--webhook-id`). [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php @7.x]

6.3 Without `-i` it loads Webhooks where `isPublished = 1` and (`markedUnhealthyAt IS NULL` or older than `webhook_health_check_time`). With `-i` it processes that Webhook only if it exists, is published and is not in its unhealthy window; otherwise it prints "There are no published webhooks to process." and exits 0. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:71-117 @7.x]

6.4 Each HTTP request carries up to `webhook_limit` (10) queue rows. After a successful batch the model recurses for the same Webhook until its queue is empty or `webhook_time_limit` (600 s) since the run began has elapsed. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:366-381,542,713-719 @7.x]

6.5 Range mode (`-i X --min-id A --max-id B`) processes queue IDs in `[A,B]` in strides of `webhook_limit`; it throws if `webhook_limit < 1`. Use it to replay or to parallelise one Webhook across workers. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:122-134 @7.x] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:588-603 @7.x]

6.6 An exception prints message and trace and returns `Command::FAILURE`. The command takes no lock; overlapping cron runs can send the same rows twice. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:138-143 @7.x]

6.7 **Queue selection**: rows with `retries = 0`, or `retries > 0 AND date_modified < now - webhook_retry_delay` (3600 s), ordered by `retries` then `id` in the Webhook's direction, limited to `webhook_limit`. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:534-606 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/Model/WebhookModelTest.php:27-66 @7.x]

6.8 **Ordering**: default `ASC` sends oldest first ("Chronological"); `DESC` sends newest first ("Reverse Chronological"). Failed rows (`retries > 0`) sort after fresh rows regardless of age. Nothing is guaranteed across Webhooks or across separate runs. Receivers that need order must sort on `timestamp`. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:543-544,613-622 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#configuring-webhooks]

6.9 **Retries**: a non-2xx response increments `retries` on every row in the batch and sets `date_modified = now`. There is no maximum retry count: a row is retried every `webhook_retry_delay` until it succeeds, the Webhook is killed, or the row is deleted. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:309-331,534-606 @7.x]

6.10 On success the processed rows are deleted (in chunks of 5000) and the Webhook is marked healthy. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:309-331 @7.x] [code: app/bundles/WebhookBundle/Entity/WebhookQueueRepository.php:21-56 @7.x]

## 7. Failure handling, health, auto-disable and notifications

7.1 Success means HTTP 2xx. Any other status or transport exception is a failure. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:309-353 @7.x]

7.2 A **410 Gone** response kills (unpublishes) the Webhook immediately, with the reason "the response HTTP code was 410…". [code: app/bundles/WebhookBundle/Model/WebhookModel.php:336-339 @7.x] [code: app/bundles/WebhookBundle/Translations/en_US/messages.ini:37 @7.x]

7.3 After any other failure the Webhook is tested with `isSick()`: take the newest `webhook_disable_limit` (100) log rows; sick = none of them is 2xx. No logs at all = healthy. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:343-353,390-400 @7.x] [code: app/bundles/WebhookBundle/Entity/LogRepository.php:75-119 @7.x]

7.4 A sick Webhook is marked unhealthy and killed (unpublished, saved, `WEBHOOK_KILL` dispatched → "Webhook has been stopped" notification) unless `disable_auto_unpublish = true` or the Webhook was modified within the last 2 days. In those cases it is only marked unhealthy. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:345-350,408-414 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:507-516 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/Model/WebhookModelProcessFailureTest.php:78-115 @7.x]

7.5 Because sickness requires zero successes in the window, a Webhook with one 2xx among its last 100 logs stays published however many failures follow it, until that success leaves the window. [code: app/bundles/WebhookBundle/Tests/Functional/Model/WebhookModelProcessFailureTest.php:37-62 @7.x]

7.6 Marking unhealthy sets `markedUnhealthyAt = now` and `unhealthySince` (if unset). The command skips the Webhook for `webhook_health_check_time` (300 s), then retries; a success clears all three health columns. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:416-435 @7.x] [code: app/bundles/WebhookBundle/Service/WebhookService.php:19-31 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:166-199 @7.x]

7.7 A **failure** notification ("Webhook %name% is failing") is sent only when the Webhook has been unhealthy longer than `first_webhook_failure_notification_time` (3600 s) and the last notification is older than `webhook_failure_notification_interval` (86400 s); `lastNotificationSentAt` records it. [code: app/bundles/WebhookBundle/Service/WebhookService.php:33-69 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:126-162 @7.x]

7.8 Notification recipients: the creator; if a different user last modified it, the modifier with the creator in CC; if there is no creator, all admin users. Each recipient gets an in-app `error` notification and an email. [code: app/bundles/WebhookBundle/Notificator/WebhookNotificationSender.php:47-94 @7.x]

7.9 The email goes to those users when `webhook_send_notification_to_author` is true (default), otherwise to the comma-separated `webhook_notification_email_addresses`. [code: app/bundles/WebhookBundle/Notificator/WebhookNotificationSender.php:106-115 @7.x] [code: app/bundles/NotificationBundle/Config/config.php:123-124 @7.x]

7.10 A `WebhookNotificationEvent` listener can call `setCanSend(false)` to suppress both the in-app notification and the email. [code: app/bundles/WebhookBundle/Notificator/WebhookNotificationSender.php:37-40 @7.x]

7.11 Kill and failure emails render `@MauticWebhook/Notifications/webhook-killed.html.twig` and `webhook-failing.html.twig`. [code: app/bundles/WebhookBundle/Notificator/WebhookKillNotificator.php:22-36 @7.x]

7.12 In immediate mode the same failure path (log, sick check, kill) runs inside the originating request. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:295-384 @7.x]

## 8. Logs and log limits

8.1 Every attempt writes exactly one `webhook_logs` row: `status_code` (string), `runtime` (seconds, 2 dp), `note` (response body or exception message, tags stripped, truncated to 190 chars). [code: app/bundles/WebhookBundle/Entity/Log.php:38-59,125-148 @7.x] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:445-463 @7.x]

8.2 A transport error before a response writes a log with `status_code = 'N/A'` and the exception message. The success-ratio query compares `status_code` numerically (`>= 200 AND < 300`), so `N/A` counts as a failure. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:358-361 @7.x] [code: app/bundles/WebhookBundle/Entity/LogRepository.php:104-105 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/Model/WebhookModelProcessFailureTest.php:63 @7.x]

8.3 Each `addLog` first trims the Webhook's logs to the newest `webhook_log_max` (1000) rows, unless `clean_webhook_logs_in_background = true`; then cron must run `mautic:webhooks:delete_logs`, which deletes the oldest excess rows in batches of 5000 and always exits 0. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:445-463 @7.x] [code: app/bundles/WebhookBundle/Command/DeleteWebhookLogsCommand.php:36-49 @7.x] [code: app/bundles/WebhookBundle/Entity/LogRepository.php:18-59 @7.x]

8.4 The Webhook detail page shows at most 100 logs (`Webhook::LOGS_DISPLAY_LIMIT`). [code: app/bundles/WebhookBundle/Entity/Webhook.php:50,455-461 @7.x]

8.5 `webhook_logs` is exposed through the stats API as a table with `runtime` and `status_code`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stats.html#get-stat-tables]

## 9. Webhook REST API

9.1 v1 resource `/api/hooks` (library key `hooks`), permission base `webhook:webhooks`. Standard endpoints plus `GET /api/hooks/triggers`. [code: app/bundles/WebhookBundle/Config/config.php:17-28 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html]

9.2 `GET /api/hooks/ID` → `hook`; `GET /api/hooks` → `{"total":n,"hooks":{id:{...}}}`. Fields: `id, name, description, webhookUrl, secret, eventsOrderbyDir, category, triggers, isPublished` plus audit fields; `triggers` is a flat list of event-type strings. Serializer groups `hookDetails, categoryList, publishDetails`. [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php:46-62 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:173-188,353-358 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#get-webhook]

9.3 The secret is returned in clear text to any API user with view permission. [code: app/bundles/WebhookBundle/Entity/Webhook.php:173-188 @7.x]

9.4 `POST /api/hooks/new` (201), `PUT /api/hooks/ID/edit` (creates if missing), `PATCH /api/hooks/ID/edit` (404 if missing), `DELETE /api/hooks/ID/delete`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#edit-webhook]

9.5 Pass event types as `triggers: ["mautic.lead_post_save_new", ...]`. Each trigger not yet on the Webhook creates an `Event`. On **PUT**, event types missing from `triggers` are removed; on POST/PATCH existing ones are kept (PATCH cannot remove a trigger). [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php:70-88 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:363-401 @7.x]

9.6 `GET /api/hooks/triggers` returns `{"triggers":{"<eventType>":{"label":"...","description":"..."}}}`. [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php:90-99 @7.x]

9.7 List filter for published state is read from query parameter `published` (docs say `publishedOnly`). [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:167,184 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#list-webhooks]

9.8 v2 resource `/api/v2/webhooks` (API Platform) exposes `id` (read) and `name, description, webhookUrl, secret, category, events, payload, triggers, eventsOrderbyDir` (read+write), permission `webhook:webhooks:*`. [code: app/bundles/WebhookBundle/Entity/Webhook.php:28-121 @7.x]

9.9 Permissions: `webhook:webhooks:{viewown, viewother, editown, editother, create, deleteown, deleteother, publishown, publishother, full}` and `webhook:categories:*`. [code: app/bundles/WebhookBundle/Security/Permissions/WebhookPermissions.php:16-17 @7.x]

## 10. Doc/code discrepancies (code wins)

10.1 `lead_post_delete`: docs show the Contact object under key `company`; code uses `contact`. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:184-201 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_delete.html]

10.2 `email_on_open`: docs say the payload equals `email_on_send`; code sends `{stat}` only. [code: app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:77-90 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_open.html]

10.3 `company_soft_delete` is listed in the events index but is not a selectable webhook event type. [code: app/bundles/LeadBundle/LeadEvents.php:627-633 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/index.html]

10.4 `mautic.lead_list_change` is selectable in code but undocumented. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:122-128 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/index.html]

10.5 REST docs list `triggers` as required on create; the entity accepts zero events. [code: app/bundles/WebhookBundle/Entity/Webhook.php:191-227 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#create-webhook]

10.6 REST docs name the list filter `publishedOnly`; code reads `published`. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:167 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#list-webhooks]

10.7 Doc samples compare signatures with `===` and the PHP sample uses `json_decode($rawData)` then array access. Use `hash_equals` / `timingSafeEqual` and `json_decode($raw, true)`. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/example_scripts.html]

10.8 `page_on_hit` docs list `dateHit` twice (string, and "always null for webhooks"). Not resolved against code. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/page_on_hit.html#page-visit-properties]

10.9 Docs say nothing about timeouts, retries, success codes, logs or auto-disable; §6–§8 come from code. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html]

## 11. Campaign action "Send a webhook" (contrast)

11.1 The Campaign action `campaign.sendwebhook` is a separate feature: it does not use the `Webhook` entity, the queue, the signature header or the private-address check; it calls `mautic.http.client` directly. [code: app/bundles/WebhookBundle/Helper/CampaignHelper.php:24,79-112 @7.x] [code: app/bundles/WebhookBundle/Config/services.php:26-28 @7.x]

11.2 Fields: `url`, `method`, `headers`, `additional_data`, `timeout` (default 10 s; this timeout is applied). URL, headers and values accept `{contactfield=...}` tokens. [code: app/bundles/WebhookBundle/Form/Type/CampaignEventSendWebhookType.php:26-101 @7.x] [code: app/bundles/WebhookBundle/EventListener/CampaignSubscriber.php:43-53 @7.x]

11.3 `get` appends data as a query string; `post`/`put`/`patch` send form params, or JSON when a `Content-Type: application/json` header is configured; `delete` sends headers only. [code: app/bundles/WebhookBundle/Helper/CampaignHelper.php:79-112 @7.x]

11.4 Success requires status 200 or 201; anything else fails the Campaign event (`OutOfRangeException`). [code: app/bundles/WebhookBundle/Helper/CampaignHelper.php:114-116 @7.x]

11.5 `WEBHOOK_ON_REQUEST` lets listeners rewrite contact, url, headers and payload before the request. [code: app/bundles/WebhookBundle/Helper/CampaignHelper.php:39-40 @7.x]

Full Campaign semantics belong to the `mautic-campaigns` skill.

## 12. Extension points (how a Plugin adds an event type)

12.1 Subscribe to `WebhookEvents::WEBHOOK_ON_BUILD` and call `$event->addEvent('<key>', ['label' => ..., 'description' => ...])`. Keys must be unique and at most 50 chars. [code: app/bundles/WebhookBundle/Event/WebhookBuilderEvent.php:26-36 @7.x] [code: app/bundles/WebhookBundle/Entity/Event.php:39-65 @7.x]

12.2 From the Plugin's domain-event listener call `WebhookModel::queueWebhooksByType('<key>', $payload, $serializerGroups)`. The model handles mode, signing, logging and health. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:229-236 @7.x]

12.3 Optionally ship a sample payload for the test button. The plugin branch of `AjaxController::getPayloadPaths` is dead (reversed `strpos` arguments), so plugin samples are looked up under `app/bundles/<Name>Bundle/Assets/WebhookPayload/` and are not found. [code: app/bundles/WebhookBundle/Controller/AjaxController.php:116-130 @7.x]

12.4 Other hooks: `WEBHOOK_QUEUE_ON_ADD` (rewrite queued payload), `WEBHOOK_KILL` (react to auto-disable), `WebhookNotificationEvent` (veto notifications), `WEBHOOK_POST_SAVE`/`POST_DELETE` (CRUD). `WEBHOOK_PRE_EXECUTE`/`WEBHOOK_POST_EXECUTE` are never dispatched. [code: app/bundles/WebhookBundle/WebhookEvents.php:19-110 @7.x]

12.5 The devdocs plugin page for webhooks is a stub with no technical content. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/webhooks.html]
