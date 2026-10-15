# Webhooks — what the official docs say

Sources: developer docs 7.2 (`webhooks/*`, `rest_api/webhooks`, `plugin_extensions/webhooks`). The webhook pages carry the banner "The content for this page requires a major update" — treat them as partially authoritative and prefer code (`behaviour.md`). [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html]

## Concepts

- Webhooks send data about Contacts and their activity to a third party, either in real time or queued and sent in batches by a cron job. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html]
- Envelope: `{"WebhookEventType": [ {WebhookEventPayload} ]}`; queued mode aggregates several types and payloads into one body. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#background-workflow]
- Real-time workflow: save → find Webhooks with the event → sign raw body → deliver. Background workflow: save → queue in DB → cron aggregates, signs, delivers. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#real-time-workflow]
- Nearly every payload item carries `timestamp` (ISO 8601). [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/index.html]

## Procedures

- **Configure delivery mode**: cog → Configuration → Webhook Settings; choose `Queue Mode` ("Process Events Immediately" / "Queue Events Only - Process Via CLI Command") and "Order of the queued events" (Chronological / Reverse Chronological); Save & Close or Apply. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#configuring-webhooks]
- **Create**: cog → Webhooks → New; enter Name, Webhook POST URL, Events; keep or customise the randomly generated secret; Apply. Use one Webhook per consuming app. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#creating-a-webhook]
- **Test**: point at a request bin; Edit → Send Test Payload, or trigger a real workflow. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#testing-a-webhook]
- **Verify**: read the raw body before parsing; compute base64(HMAC-SHA256(raw, secret)); compare with `Webhook-Signature`; ignore mismatches. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html#securing-a-webhook]
- PHP sample: `base64_encode(hash_hmac('sha256', $rawData, $secret, true))` over `php://input`. Node sample: `crypto.createHmac('sha256', SECRET).update(rawBody).digest('base64')`, header read as lower-case `webhook-signature`. Both compare with `===`. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/example_scripts.html]

## Documented event types

The index lists 14: `lead_post_save_new`, `lead_post_save_update`, `lead_points_change`, `lead_post_delete`, `lead_channel_subscription_changed`, `lead_company_change`, `company_post_save`, `company_soft_delete`, `company_post_delete`, `email_on_send`, `email_on_open`, `form_on_submit`, `page_on_hit`, `sms_on_send`. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/index.html]

Code differs: `company_soft_delete` is not a webhook type and `lead_list_change` is missing from the docs (see `behaviour.md` §10). Per-event pages:

| Event | Page |
|---|---|
| `mautic.lead_post_save_new` (Contact object reference) | https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_new.html |
| `mautic.lead_post_save_update` | https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_update.html |
| `mautic.lead_points_change` | https://devdocs.mautic.org/en/7.2/webhooks/events/lead_points_change.html |
| `mautic.lead_post_delete` | https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_delete.html |
| `mautic.lead_channel_subscription_changed` | https://devdocs.mautic.org/en/7.2/webhooks/events/lead_channel_subscription_changed.html |
| `mautic.lead_company_change` | https://devdocs.mautic.org/en/7.2/webhooks/events/lead_company_change.html |
| `mautic.company_post_save` (Company object reference) | https://devdocs.mautic.org/en/7.2/webhooks/events/company_post_save.html |
| `mautic.company_post_delete` | https://devdocs.mautic.org/en/7.2/webhooks/events/company_post_delete.html |
| `company_soft_delete` (Plugin-only event) | https://devdocs.mautic.org/en/7.2/webhooks/events/company_soft_delete.html |
| `mautic.email_on_send` (Email, Category, Asset, Segment, Form object references) | https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_send.html |
| `mautic.email_on_open` | https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_open.html |
| `mautic.form_on_submit` | https://devdocs.mautic.org/en/7.2/webhooks/events/form_on_submit.html |
| `mautic.page_on_hit` | https://devdocs.mautic.org/en/7.2/webhooks/events/page_on_hit.html |
| `mautic.sms_on_send` | https://devdocs.mautic.org/en/7.2/webhooks/events/sms_on_send.html |

Object reference highlights:
- Contact: `points` is "also known as a Behavior Score"; `frequencyRules` and `utmtags` are not populated for webhooks; `stage` is not fully populated. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_new.html#contact-properties]
- Custom field types: boolean, date, datetime, email, country, locale, number, tel, region, select, multiselect, text, textarea, time, timezone, url. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_new.html#custom-field-properties]
- DNC `reason`: 1 unsubscribed by Contact, 2 bounced, 3 manually unsubscribed. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_new.html#channel-subscription-properties]
- Channel status values: `contactable`, `bounced`, `manual`, `unsubscribed`. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_channel_subscription_changed.html]
- Email `emailType`: `template` or `list` (Segment/broadcast). Email `source`: `[component, id]`. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_send.html#email-properties]
- Form `formType` is deprecated since 7.1 ("all Forms function identically"); removal scheduled for 8.0. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_send.html#unsubscribe-form-properties]
- Opens "may not be a reliable metric" (proxies, bots). [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_open.html]

## REST API (`hooks`)

- `GET /hooks/ID` → `hook` with isPublished, audit fields, id, name, description, webhookUrl, secret, eventsOrderbyDir (`asc`|`desc`|null), category, triggers. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#get-webhook]
- `GET /hooks` → `total`, `hooks` keyed by ID; params searchFilter, start (0), limit (30), orderBy (snake_case), orderByDir, publishedOnly, minimal. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#list-webhooks]
- `POST /hooks/new` → 201; required name, webhookUrl, triggers; optional description, secret, isPublished, eventsOrderbyDir, category. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#create-webhook]
- `PUT /hooks/ID/edit` creates if missing; `PATCH` 404 if missing; `DELETE /hooks/ID/delete` returns the deleted Webhook. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#edit-webhook]
- Stats API exposes table `webhook_logs` (runtime, status_code). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stats.html#get-stat-tables]

## Plugin extension docs

- `plugin_extensions/webhooks` is a stub (banner only) in 7.2 and 8.0; how to register a webhook event type is undocumented. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/webhooks.html]

## Gaps (use code instead)

No documentation of: success codes, timeouts, retries, logs, auto-unpublish, notifications, the command name and options, headers other than `Webhook-Signature`, per-Webhook order, log retention. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/getting_started.html]

## Terminology

Capitalise product nouns: Contact, Company, Segment, Form, Landing Page, Email, Text Message, Campaign, Channel, Webhook, Plugin. Code identifiers keep `lead`, `lists`, `doNotContact`. "Channel subscription" = DNC. [devdocs: https://devdocs.mautic.org/en/7.2/webhooks/events/lead_post_save_new.html]
