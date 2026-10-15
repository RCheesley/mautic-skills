# Webhooks - pull-request history

## How to read this file
Source: merged pull requests on github.com/mautic/mautic for WebhookBundle and the "Send a webhook" Campaign action, harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; `~` marks an inference. 7.x versions were checked against the release tags.
Current behaviour lives in behaviour.md (code-verified); this file explains why and when it came to be.

## Decisions that shaped current behaviour

### Webhook model and payloads
- Webhooks subscribe a URL to Mautic events, and each bundle ships a sample payload used by "Send test payload" [PR #791] (~v1.2.0).
- Requests send `Content-Type: application/json` with a JSON body; the header had been form-urlencoded [PR #2318] (~v2.1.1).
- The Webhook URL is required, and its query string is preserved, including for the test button. A blank URL had caused an SQL error [PR #2323] (~v2.1.1).
- The Contact-deleted payload carries a top-level `id`, because a serialised deleted entity has `id: null`. Dropping `contact` to save size was rejected [PR #3633] (~v2.7.1). The duplicate `lead` object was removed from the sample payloads [PR #8397] (~v3.0.0).
- A page-hit Webhook must not break `/r/` redirect URLs; the payload handles Page and Redirect hits [PR #901] (~v1.2.1).
- Every request carries `X-Origin-Base-URL` with the site URL [PR #7725] (~v3.0.0).
- Every Webhook has a secret, and each request carries `Webhook-Signature` = base64(HMAC-SHA256(raw body, secret)) [PR #8397] (~v3.0.0). The secret is generated when the new-Webhook form opens, so the test payload is signed too [PR #8410] (~v3.0.0). Test payloads are signed with the Webhook's own secret; a stray argument had signed them with an empty secret [PR #9839] (~v4.0.0).
- Requests send `User-Agent: Webhook`, not Guzzle's default, which disclosed the library and its version [PR #15728] (v7.1.0).
- "Send email details" (`webhook_email_details`, default on) controls email payload size. When off, `email_on_send` drops `email.customHtml`, `email.plainText`, `content` and `tokens`, and `email_on_open` drops `stat.email.customHtml` and `plainText` [PR #13447] (~v5.1).
- The test payload has the same structure as a real delivery; it used to add an extra timestamp [PR #15799] (v7.0.1). A later PR fixed only the flaky test by normalising the timestamp [PR #16134] (v7.1.2).
- When a test fails, the UI shows the real reason (invalid URL, unresolvable host, blocked private address) instead of "Error Detected!". Hostname resolution moved to `PrivateAddressChecker::resolveHostName` [PR #15863] (v7.0.1).
- Any 2xx counts as success, for deliveries and for the test button; 201 and 202 had been shown as errors in the test [PR #7235] (~v2.15.1).
- `WebhookQueueEvent::getWebhookQueue()` and `getWebhook()` return the queue row and the Webhook [PR #5845] (~v2.13.1).

### Immediate and queued delivery
- Webhooks run immediately in the request or, in queue mode, from `webhook_queue` via `mautic:webhooks:process` [PR #791] [PR #901] (~v1.2.x). `--webhook-id` limits processing to one Webhook [PR #901] (~v1.2.1).
- Immediate-mode Webhooks are sent directly, without persisting through the queue or the Webhook entity. A maintainer agreed that immediate processing should not go through the entity [PR #6987] (~v2.15.0).
- Queuing an event does not update the Webhook row, because per-event writes caused deadlocks on busy sites [PR #6594] (~v2.15.0). The first version broke immediate Webhooks and was reworked by [PR #6987].
- Delivered (2xx) queue rows are deleted, so a payload holds only that delivery's events; payloads had grown on every send [PR #4554] (~v2.9.2).
- Queue rows are deleted with direct queries, not through the Doctrine collection, because ORM 2.7.1 loads the whole collection into memory first [PR #9874] (~v4.0.0).
- Processing stops after `webhook_time_limit` (600 s) even while events keep arriving; recursive processing had never ended under load [PR #9573] (~v3.3.0).
- Queue payloads are stored compressed in `payload_compressed` to save space [PR #11589] (~v5.0). The uncompressed `payload` column was dropped in 7.0 [PR #15283] (v7.0.0).
- Queue order is by queue-row id, not `date_added`. `date_added` has no index, and a 15-million-row queue took over 30 minutes; ordering by id took 82 ms. Adding an index was rejected because it slows inserts [PR #11424] (~v5.1). Behaviour 6.7 shows the 7.x order is `retries`, then `id`.
- Delivery order is chronological (ASC, the default for BC) or reverse chronological, set globally and per Webhook; Zapier needs newest first [PR #4627] (~v2.10.0). The per-Webhook "Default" option means "use the global setting" [PR #13501] (~v5.1).
- Range mode (`--min-id`, `--max-id` with `--webhook-id`) processes one id range, so parallel workers do not send the same rows [PR #13448] (~v5.1).
- Queue iteration uses Doctrine `toIterable()` instead of the deprecated `iterate()` [PR #13112] (~v5.1).

### Failures, retries and auto-unpublish
- A non-2xx response keeps the event queued for the next run; an impossible condition had discarded errored events [PR #6751] (~v2.15.0).
- Failed rows are retried rather than dropped. On failure the batch's rows get `retries + 1` and a new modified date; fresh rows are picked first; a retried row waits for `webhook_retry_delay` (3600 s) [PR #15283] (v7.0.0). The PR describes the wait as `retries × delay`; behaviour 6.7 shows a flat delay (see Open questions).
- Auto-unpublish ("kill") started as REST Hooks support: unpublish after `webhook_disable_limit` (100) bad responses, and at once on HTTP 410 Gone, with a notification [PR #4200] (~v2.9.0). The kill also sends an email to the owner [PR #8782] (~v3.1.0).
- 7.0 added a health state: a failing Webhook is marked unhealthy and skipped for `webhook_health_check_time` (300 s), and it is unpublished only if it was not modified in the last 2 days, so it is not killed while someone works on it [PR #15283] (v7.0.0).
- 7.0 added failure notifications: after `first_webhook_failure_notification_time` (1 h) of failure, then every `webhook_failure_notification_interval` (1 day), with the failure rate, an example error and links [PR #15283] (v7.0.0).
- `disable_auto_unpublish` (default false) keeps failing Webhooks published, for operators who prefer that an integration does not stop silently [PR #15495] (v7.0.0).
- The current rule in 7.x code: a 410 kills the Webhook at once, regardless of `disable_auto_unpublish` or recent edits. Any other failure checks the newest `webhook_disable_limit` (100) logs; if none is 2xx, the Webhook is marked unhealthy, and it is also unpublished unless `disable_auto_unpublish` is true or it was modified in the last 2 days (behaviour 7.2-7.4) [PR #4200] [PR #15283] [PR #15495].
- A failed call also writes the request payload to the file log; the database log note stays truncated [PR #13815] (~v5.1).

### Logs
- Each delivery log records status, note and runtime [PR #4200] (~v2.9.0). Response bodies stored in notes are cleaned to valid UTF-8 so binary bytes cannot cause SQL errors [PR #9967] (~v4.0.0).
- The detail page shows only the latest 100 logs; millions of logs had caused a 500 [PR #10257] (~v4.1).
- Logs over `webhook_log_max` are pruned inline, or by `mautic:webhooks:delete_logs` when `clean_webhook_logs_in_background` is true [PR #10405] (~v4.2.0). The command casts `webhook_log_max` to int [PR #11640] (~v5.0).

### `mautic:webhooks:process` exit codes
- The command returns non-zero on real errors so cron can detect them [PR #11963] (v4.4.8) [PR #12203] (~v5.0). It returns 0 with "There are no published webhooks to process." when nothing is published, because that is a normal state [PR #15135] (v7.2.0). In 7.x the immediate-mode exit is also 0 and only an exception returns `FAILURE` (behaviour 6.1, 6.3).

### Campaign action "Send a webhook"
- The Campaign action calls a URL with GET, POST, PUT, PATCH or DELETE, custom data and custom headers. Reviewers chose the name "Send a webhook", dropped TRACE and OPTIONS, and allowed any header [PR #4357] (~v2.10.0). Success is 200 or 201 (behaviour 11.4).
- The action runs inside Campaign processing and does not use the Webhook queue [PR #6987] (~v2.15.0).
- Data values, headers [PR #4357] and the URL [PR #6494] (~v3.1.0) accept `{contactfield=...}` tokens. `{contactfield=ipAddress}` gives a comma list [PR #6539] (~v2.15.0). Primary-company fields are available as tokens [PR #9371] (~v3.2.0).
- The body is form-encoded by default and JSON only when the user adds `content-type: application/json`. Making JSON the default was rejected as a default-behaviour change that only a major release could make [PR #8959] (~v3.1.0) [PR #10580] (~v4.1).
- Values are encoded once, not twice [PR #5070] (~v2.12.1); `+` is sent as `%2B` [PR #7616] (~v2.16.1); HTML in values is kept [PR #8642] (~v3.1.0).
- The data list is keyed by label: two keys with the same value are both saved, and a repeated key keeps the last value [PR #16899] (v7.2.0).
- Plugins can change the URL, headers and payload through `WebhookRequestEvent` [PR #9475] (~v3.3.0).

### API and UI
- Webhooks have REST CRUD endpoints implementing Zapier REST Hooks [PR #4200] (~v2.9.0).
- The WebhookBundle UI was the pilot for the PHP-to-Twig migration and went into 5.0 because there were no more 4.x feature releases [PR #11382] (v5.0).
- Web-notification permission translations moved out of WebhookBundle into NotificationBundle [PR #11450] (~v5.0).

## Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| JSON body sent with a form-urlencoded header | `Content-Type: application/json` | [PR #2318] | ~2.1.1 |
| Test payload dropped URL query parameters; blank URL gave SQL error | Query kept; URL required | [PR #2323] | ~2.1.1 |
| Deleted-Contact payload had an empty id | Top-level `id` present | [PR #3633] | ~2.7.1 |
| Page-hit Webhook made `/r/` redirects return 500 | Redirect works and Webhook fires | [PR #901] | ~1.2.1 |
| Multi-delete of Contacts gave "Illegal offset type" | No error | [PR #3444] | ~2.6.1 |
| Test payload unsigned or signed with an empty secret | Signed with the Webhook secret | [PR #8410] [PR #9839] | ~3.0.0 / ~4.0.0 |
| Test payload had an extra timestamp | Test and real payloads identical | [PR #15799] | 7.0.1 |
| Webhook test showed only "Error Detected!" | Real validation or DNS error shown | [PR #15863] | 7.0.1 |
| Test with 201/202 showed "Error Detected" | Any 2xx is success | [PR #7235] | ~2.15.1 |
| Payload grew on every send | Delivered rows removed | [PR #4554] | ~2.9.2 |
| Errored queued events discarded | Non-2xx keeps the row queued | [PR #6751] | ~2.15.0 |
| Deadlocks: Webhook row updated per queued event | Queueing does not touch the Webhook row | [PR #6594] | ~2.15.0 |
| Immediate Webhooks never sent | Immediate path bypasses the queue | [PR #6987] | ~2.15.0 |
| Processing never stopped under load | Stops at `webhook_time_limit` | [PR #9573] | ~3.3.0 |
| Queue of millions of rows timed out | Fetched by id order | [PR #11424] | ~5.1 |
| Queue SQL error (missing alias dot) | Command runs | [PR #4452] | ~2.9.1 |
| Invalid UTF-8 in a response gave an SQL error on log insert | Note cleaned to UTF-8 | [PR #9967] | ~4.0.0 |
| Detail page 500 with millions of logs | Latest 100 logs shown | [PR #10257] | ~4.1 |
| String `webhook_log_max` broke log cleanup | Cast to int | [PR #11640] | ~5.0 |
| Killed Webhook sent no email | Email sent | [PR #8782] | ~3.1.0 |
| Process command failed when no Webhooks were published | Exit 0 with a message | [PR #15135] | 7.2.0 |
| `WebhookQueueEvent` getters returned the wrong objects | Return queue row and Webhook | [PR #5845] | ~2.13.1 |
| Campaign webhook data double-encoded | Encoded once | [PR #5070] | ~2.12.1 |
| `+` not encoded in a Campaign webhook | `%2B` | [PR #7616] | ~2.16.1 |
| HTML stripped from Campaign webhook data | HTML kept | [PR #8642] | ~3.1.0 |
| Campaign webhook could not send JSON | JSON when the content-type header is `application/json` | [PR #8959] | ~3.1.0 |
| Company tokens empty in Campaign webhooks | Primary company fields available | [PR #9371] | ~3.2.0 |
| Campaign summary said success, Contact history said failure | Action sends with the chosen method and records success | [PR #10580] | ~4.1 |
| Same value under two keys saved once | Both keys saved | [PR #16899] | 7.2.0 |

## Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.2 | WebhookBundle, queue mode, `--webhook-id` | #791, #901 |
| 2.1-2.7 | JSON content type; URL required; deleted-Contact `id` | #2318, #2323, #3633 |
| 2.9-2.10 | REST Hooks API, logs, auto-disable, 410; "Send a webhook" Campaign action; event order | #4200, #4357, #4627 |
| 2.15-2.16 | Retry on non-2xx; no Webhook-row writes; immediate path; any 2xx; IP token; `+` encoding | #6751, #6594, #6987, #7235, #6539, #7616 |
| 3.0 | `X-Origin-Base-URL`; `Webhook-Signature`; secret on form open | #7725, #8397, #8410 |
| 3.1-3.3 | Kill email; URL tokens; JSON Campaign webhooks; company tokens; `WebhookRequestEvent`; time limit | #8782, #6494, #8959, #9371, #9475, #9573 |
| 4.0-4.2 | Direct queue deletes; UTF-8 notes; signed test; 100-log display; background log cleanup | #9874, #9967, #9839, #10257, #10405 |
| 4.4.8 / 5.0 | Non-zero exit on errors; compressed queue payload; Twig UI | #11963, #12203, #11589, #11382 |
| 5.1 | Id-ordered queue; email-details toggle; range mode; payload in file log | #11424, #13447, #13448, #13815 |
| 7.0.0 | Retries, health state, failure notifications; `payload` column dropped; `disable_auto_unpublish` | #15283, #15495 |
| 7.0.1 | Identical test payload; real test errors | #15799, #15863 |
| 7.1.0 | `User-Agent: Webhook` | #15728 |
| 7.2.0 | Exit 0 with no published Webhooks; Campaign data keyed by label | #15135, #16899 |

## Removed, deprecated, replaced

| What | Replaced by | PR | Version | Note |
|---|---|---|---|---|
| Duplicate `lead` object in sample payloads | `contact` | #8397 | ~3.0.0 | Read `contact` |
| `WebhookSubscriberBase`, `WebhookModelTrait`, `WebhookModel::webhookStart` | DI services | #8061 | ~3.0.0 | BC breaks listed in the PR |
| `Webhook::removeQueue` and ORM collection deletes | Direct deletes | #9874 | ~4.0.0 | UPGRADE-4.0.md |
| Webhook PHP templates | Twig | #11382 | 5.0 | |
| Queue ordering by `date_added` | Ordering by queue id | #11424 | ~5.1 | Deprecations not listed in the notes |
| Doctrine `iterate()` | `toIterable()` | #13112 | ~5.1 | |
| `webhook_queue.payload` | `payload_compressed` | #11589, #15283 | 5.0 / 7.0.0 | Column dropped in 7.0 |
| Guzzle default User-Agent | `User-Agent: Webhook` | #15728 | 7.1.0 | |

## Maintainer norms for this area
- Changing default behaviour is a BC break that only a major release may make; in a minor release make it opt-in, as JSON Campaign webhooks were [PR #8959].
- Avoid ORM collection operations and parent-row writes on the queue and log tables, which can be huge or hot [PR #9874] [PR #6594] [PR #10257].
- Prefer ordering by an indexed auto-increment id over adding indexes to hot queue tables [PR #11424].
- Do not reveal library versions in outgoing headers [PR #15728].
- Commands return a failure code only for real errors; "nothing to do" is success [PR #12203] [PR #15135].
- Fix flaky tests by normalising runtime values such as timestamps, not by loosening assertions [PR #16134].
- Features need user or developer docs and test steps (time limit, log-cleanup cron, JSON webhooks, range mode) [PR #9573] [PR #10405] [PR #8959] [PR #13448].
- Set a PR with a pending change request to "pending feedback" and re-test after code changes [PR #10580].
- Keep `lead` keys for BC until a major release while moving public naming to `contact` [PR #3633].

## Open questions
- Conflict with behaviour.md: [PR #15283] describes the retry wait as `retries × webhook_retry_delay` with a `date_updated` column. The 7.x code uses a flat `webhook_retry_delay` against `date_modified` (behaviour 6.7). behaviour.md wins.
- Conflict with behaviour.md: [PR #4200] made the request timeout 15 s via `webhook_timeout`. Behaviour 4.9 shows `webhook_timeout` is read but never passed to the HTTP client. behaviour.md wins; the PR is historical.
- Conflict with behaviour.md: [PR #4200] described the kill as 100 "consecutive" bad responses. Behaviour 7.3-7.5 shows the rule is "no 2xx among the newest 100 logs", with the 2-day and `disable_auto_unpublish` exceptions from [PR #15283] [PR #15495].
- Minor: [PR #13815] gives the note limit as 191 characters; SKILL.md and behaviour.md say 190.
- [PR #15283] says notifications go to the creator or modifier, else all admins. Behaviour records the modifier with the creator in CC; behaviour.md wins.
- Whether real `lead_post_delete` payloads still carry a `lead` key was not settled; only samples were cleaned [PR #8397].
- The methods deprecated by the id-ordering change are not listed [PR #11424].

## Coverage
The API and webhooks area has 158 merged PRs in two chunks (#125 to #17361, 2015-03 to 2026-09). This file uses the [webhooks] items; API items are in mautic-rest-api.
Chunk 1 has 92 PRs (74 substantive); chunk 2 has 66 (40 substantive, 22 refactor-only, 4 noise).
A further 869 noise PRs across all areas were excluded upstream before chunking.
