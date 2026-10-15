# Emails — PR history

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
   - Sending eligibility, DNC and email type
   - Segment (broadcast) sends
   - Campaign, Form and Point sends, message queue, frequency rules
   - Tokens, dynamic content and plain text
   - Link tracking and UTM
   - Open tracking and bot filtering
   - Unsubscribe, List-Unsubscribe and the Preference Centre
   - Bounces, replies, VERP and the monitored inbox
   - Transports, mailer DSN, embedding and S/MIME
   - From, Reply-To and headers
   - A/B tests, variants, translations and cloning
   - Preview, web view, test sends and drafts
   - Email management UI and API
   - Stats, reports and webhooks
3. Removed, deprecated, replaced
4. Regression catalogue
5. Feature timeline
6. Maintainer norms for this area
7. Open questions
8. Coverage

## 1. How to read this file
Source: merged pull requests on mautic/mautic for the Emails area, harvested 2026-10-15.
Versions are inferred from the base branch, milestone and merge date; where a release tag was checked in the 7.x tree, the tag is cited. "v7.3.0-rc" means merged to 7.x after 7.2.1 and not yet released.
Current behaviour is in behaviour.md. This file explains why and when. Where the two disagree, behaviour.md wins.

## 2. Decisions that shaped current behaviour

### Sending eligibility, DNC and email type
- Contacts with an email Do Not Contact (DNC) entry are not sent emails [PR #591] (v1.1).
- One invalid address must not abort a campaign or batch send. It is recorded as failed and the mailer error is reset so later good addresses still send [PR #351] (v1.0.4) [PR #602] (v1.1).
- A malformed address reached in a broadcast becomes DNC Bounced with the comment "Incorrectly formatted email address" [PR #2259] (v2.2) [PR #5526] (v2.12.2). A transport or connection failure (for example a wrong SMTP port) does not create that DNC [PR #5807] (v2.13).
- A failed send is retried up to 3 times before a DNC row is written. A leftover debug `true` had created DNC on the first retry [PR #13341] (v5.1).
- An unpublished email, one outside its publish window, or one in an unpublished Category cannot be sent from the UI, API or a running broadcast; a running send stops when the email is unpublished [PR #5938] (v2.13.1). From the message queue an unpublished email fails and is retried up to the attempt limit, because unpublishing may be temporary [PR #4761] (v2.10).
- Contacts who unsubscribed from a Category in the Preference Centre do not get Segment or campaign emails in that Category [PR #10879] (v5.1).
- DNC reasons are integer codes and 0 means contactable. Bounce, FBL and unsubscribe processors, bulk "Set DNC", CSV import `doNotEmail` and SMS unsubscribes must pass BOUNCED, MANUAL or UNSUBSCRIBED explicitly [PR #2141] (v2.1); a 3.1 regression that left those Contacts contactable was fixed by [PR #9186] (v3.1.2).
- The DNC exclusion query and stats SQL must work under ANSI `sql_mode` (single-quoted literals). Otherwise DNC Contacts were emailed on managed databases such as Aiven [PR #12919] (v5.1) [PR #15324] (v6.0.4) [PR #15325] (v7.0).
- Email address validation moved from an RFC 2822 regex to `filter_var` with forbidden characters [PR #4158] (v2.8.2), then cleaned `..` and spaces [PR #5078] (v2.11), then allowed apostrophes again [PR #10413] (v4.0). Config sender fields use Symfony `html5` validation, not `strict` [PR #11054] (v4.3).
- MX checking is not automatic. It is the campaign condition "Has valid email address" [PR #5078] (v2.11), which really validates and sends an empty address down "no" [PR #7960] (v2.16), checks DNS/MX [PR #9215] (v3.1.1), and returns false instead of a TypeError for null [PR #13976] (v5.2).
- Subject is required because some providers reject subject-less mail [PR #5557] (v2.12.2).
- Email type history (transactional vs marketing). Originally marketing emails went through frequency rules and the message queue while transactional emails sent immediately [PR #2549] (v2.2). In 5.0 transactional campaign sends and the API direct send ignored DNC as a documented BC break; a third "standard" type was rejected [PR #11786] (v5.0). The constants `MailHelper::EMAIL_TYPE_TRANSACTIONAL`/`EMAIL_TYPE_MARKETING` replaced strings [PR #12654] (v5.0). Because transactional reached unsubscribed Contacts, the campaign form default became Marketing [PR #14145] (v5.2). In 7.2 DNC bypass moved onto the email as "Send to unsubscribed contacts" (`sendToDnc`, permission `email:emails:sendtodnc`), and the campaign switch was relabelled "Repeatable email" [PR #15995] (v7.2).
- Checked in the tags: 5.0.0 to 7.1.0 pass `ignoreDNC = (type === transactional)` [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php @5.0.0] [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php @7.1.0]; 7.2.0 and the 7.x snapshot pass `ignoreDNC = $email->getSendToDnc()` [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:274-286 @7.x]. An event config with no `email_type` is still treated as transactional (repeatable) in 7.x, but that no longer bypasses DNC [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:274 @7.x].
- The API direct send `POST /emails/{id}/contact/{contactId}/send` ignored DNC unconditionally in 5.0 [PR #11786] [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php @5.0.0]; in 7.x it uses the email's `sendToDnc` [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:193 @7.x].
- "Send to unsubscribed contacts" shows a confirmation warning because it is legally risky; the email's value is shown in the campaign action, Point trigger and Form action. Emails with it on do not count towards frequency rules [PR #15995] (v7.2).
- `EmailEvents::EMAIL_PRE_SEND` lets a listener skip or fail one send through `EmailSendEvent` [PR #13360] (v5.1).
- A Contact deleted during a batch send is skipped for the "email send" Point action and the batch continues [PR #16073] (v7.1.2).

### Segment (broadcast) sends
- Pending for a Segment Email means Contacts in its Segments who have not received this email, counted once across Segments, excluding manually removed members, DNC and Contacts with a pending `message_queue` row; stats with NULL `lead_id` must not distort it [PR #392] (v1.1) [PR #722] (v1.2) [PR #1203] [PR #1266] (v1.2.3) [PR #5697] (v2.13) [PR #6592] (v2.15) [PR #11260] (v4.4.1).
- The pending SQL has been rewritten many times for speed (EXISTS, JOIN, NOT IN, NOT EXISTS); 2.15 took a 2M-contact query from 15 min to 53 ms [PR #1400] (v2.0) [PR #5405] (v2.12.1) [PR #6592] (v2.15) [PR #11260] (v4.4.1) [PR #16558] (v7.2). Count queries carry no ORDER BY and must work on MySQL and PostgreSQL [PR #665] (v1.1.3).
- Frequency-queued Contacts are not pending, so a broadcast cannot loop forever [PR #3560] (v2.7).
- Excluded Segments: excluded Contacts are not sent and not pending; the user must have access to every chosen Segment [PR #13458] (v5.1). The excluded-Segment subquery forces the primary index on `lead_lists_leads` (MySQL/MariaDB only, accepted "for now") [PR #15950] (v7.2).
- A Segment Email with a publish-up date is sent by the cron through the generic channel-broadcast event; emails without publish-up are ignored, for BC [PR #2259] (v2.2) [PR #11127] (v5.0). Only Segment-type emails are broadcast [PR #2889] (v2.3).
- The cron command is `mautic:broadcasts:send` with no alias [code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:23 @7.x]. `--min-contact-id`/`--max-contact-id` allow non-overlapping workers [PR #5715] (v2.13); `--max-threads`/`--thread-id` were added for email and SMS [PR #11549] (v5.0). In 5.0 `--limit` caps the total per run and `--batch` sets the batch size, matching SMS (BC break) [PR #11127] (v5.0).
- Manual UI send is batched by `mailer_memory_msg_limit` (default 100); the batch-size input was removed [PR #11167] [PR #11595] (v5.0). Leaving the progress screen stops a manual send; background sending needs dates and cron [PR #15261] (v7.0).
- The Send button is disabled when a published Segment Email's publish-up is past, because a cron send is assumed [PR #11351] (v5.0), and for Segment Emails already sending in the background [PR #11946] (v5.0).
- Scheduling moved to the email detail page ("Send now", "Schedule send"); the per-email option "Continue sending to new contacts" decides whether Contacts added after sending starts also get the email; a migration turned it on for existing emails [PR #14254] (v7.0).
- Publish fields on trigger (template) emails were hidden to match SMS [PR #13818] (v5.2), then shown again so campaign emails can be unpublished on schedule [PR #15506] (v7.0).
- Just before each Segment send Mautic re-checks whether the Contact already has a stat for the email. A race window remains; an atomic stat insert was not done [PR #14531] (v6.0).
- "Send only once per unique email address" was merged and reverted the same day because a threaded-send test broke [PR #13768] [PR #13902] (2024-06-28). It is not in core.
- The pending count is not served stale from cache after Segment membership changes [PR #16442] (v7.1.3), and the Pending card shows only on Segment Emails [PR #16304] (v7.2).
- MailHelper clears message metadata after each successful send to keep large broadcasts in memory [PR #15121] (v5.2.7).
- With mailer-is-owner on, a Segment send where only some Contacts have owners must not send duplicates [PR #4705] (v2.10).
- Each batched recipient gets a unique bounce return path (`+bounce_<hash>`) [PR #1266] (v1.2.3).

### Campaign, Form and Point sends, message queue, frequency rules
- Campaign marketing emails go through `message_queue`; over-limit Contacts are rescheduled to the next frequency period, not dropped [PR #2549] (v2.2) [PR #4761] (v2.10). The queue command is `mautic:messages:send` with alias `mautic:campaigns:messagequeue` [code: app/bundles/ChannelBundle/Command/ProcessMarketingMessagesQueueCommand.php:17-20 @7.x].
- Frequency rules never applied to transactional sends. Two attempts to change that were reverted the same day [PR #6760] [PR #6849] [PR #6896] [PR #6944] (v2.15). Since 7.2 the switch is the email's `sendToDnc` instead of the campaign type [PR #15995] (v7.2).
- A marketing email the Contact already received makes the event pass once with a note and is not rescheduled [PR #7413] (v2.15.2). A marketing email with A/B variants is sent once per Contact even when the campaign has several send actions [PR #14838] (v5.2.5).
- Failed scheduled sends pass the failed Contact IDs back so the log persists and nothing re-sends every trigger run [PR #7733] (v2.15.3).
- Validation errors such as a bad CC/BCC fail the campaign event visibly and notify the owner [PR #3193] (v2.6) [PR #9276] (v3.1.2).
- The action label is "Send or schedule email" because 100% complete may still mean queued [PR #4628] (v2.10).
- Token transport metadata must not accumulate across Contacts; Contact N had carried tokens of Contacts 1..N-1 [PR #3995] (v2.8.1).
- Decisions: "opens email" follows a Send email action [PR #439] (v1.1); "clicks email" with an optional URL filter [PR #3887] (v2.10) matches escaped slashes [PR #5517] (v2.12.2) and URL-encoded URLs [PR #15550] (v7.1); "replies to email" [PR #5194] (v2.12). Conditions match any A/B variant [PR #6765] (v2.15.1).
- The campaign email selector lists only top-level emails, because selecting a translation bypassed language mapping [PR #15745] (v7.1). Its labels are `(<id>) <name>` and search works by ID or name [PR #15183] (v7.0) [PR #16086] (v7.2). Inline "Edit email" keeps the selection [PR #16972] (v7.2).
- "Send email to user" sends to users, the owner and To/CC/BCC with real token values but a fake hash, so unsubscribe and tracked links do not work [PR #4458] (v2.10). Each address gets exactly one email [PR #8768] (v3.0). It accepts `{contactfield=alias}` recipients and skips empty values [PR #9525] (v4.1); deleted users are skipped [PR #6939] (v2.15.1); the Form version requires a user [PR #10243] (v4.0).
- The Form "Send email" action accepts comma-separated To/CC/BCC lists, each validated [PR #16271] (v7.2, no milestone).
- Point-trigger "Send email" fires once per Contact [PR #3854] (v2.8.1) [PR #8619] (v3.0.2).
- Campaign export succeeds with translated or variant emails [PR #15831] (v7.0.1). The campaign Email Metrics tab can be switched off with `campaign_email_stats_enabled` [PR #14414] (v6.0).

### Tokens, dynamic content and plain text
- Tokens are replaced in the subject even when absent from the body [PR #719] (v1.2), and in the online/preview view [PR #679] (v1.1.3).
- `{signature}` originally used the owner's signature whenever global mailer-is-owner applied [PR #1319] (v1.3). Now it renders the owner's signature only when that email has "Use owner as mailer" on, else `default_signature_text` [PR #15931] (v7.2).
- The API direct send accepts custom `tokens` without braces [PR #4365] (v2.9), works for any published email [PR #6581] (v2.14.2), accepts `assetAttachments` [PR #7332] (v2.15.2), and allows HTML in token values; an `html://` opt-in was rejected [PR #12227] (v5.1).
- Plugins must not replace tokens directly in content, because that breaks token (batch) mailers [PR #3995] (v2.8.1).
- New tokens: `{today}` [PR #11722] (v5.0); `{dnc_url}` unsubscribes from all marketing even with the Preference Centre on [PR #14114] (v5.2); `{resubscribe_url}` [PR #14215] [PR #14257] (v5.2). Token names may contain `=` [PR #12657] (v5.1).
- Only owner tokens that are used are stored in `email_stats.tokens` [PR #12167] (v5.0). Web view and unsubscribe must tolerate NULL tokens [PR #15026] (v5.2.7).
- `{ownerfield=*}` inside tracked URLs resolves per Contact at redirect time [PR #15924] (v7.2) through `UrlTokenReplaceEvent` [PR #16199] (v7.2). Company tokens work in preview, examples and Contact sends [PR #14944] (v7.0).
- Custom-header tokens are replaced only in unstructured headers [PR #12912] (v5.0); Reply-To tokens are replaced before validation [PR #12883] (v5.1).
- Dynamic content: first matching variant wins, else the default; no nesting [PR #2574] (v2.2). Later fixes: tokens inside it [PR #2819] (v2.3), `%` in `like` [PR #4748] (v2.10), NULL boolean "!= No" is true [PR #7468] (v2.15.2), contains/starts/ends [PR #9357] (v4.0), company filters skipped without a company [PR #11425] (v4.4.4), Segment-membership filter [PR #13528] (v5.2), decimals [PR #14481] (v6.0), region name or index [PR #15527] (v7.0), deleting a filter really removes it [PR #15953] (v7.0.2) [PR #16484] (v7.2). A variant's filters are ANDed [PR #17404] (v7.3.0-rc).
- A plain-text part is generated from HTML when empty [PR #8645] (v3.1); anchors spanning `<br>` are detected so each recipient gets their own `ct` [PR #15190] (v7.0).
- `<title>` and `<html lang>` are added on send if missing [PR #10402] (v4.2). A Preheader field was added to every send route [PR #13792] (v5.2).
- Native emoji are stored in utf8mb4 columns instead of shortcodes [PR #13337] (v5.1).

### Link tracking and UTM
- All links become trackable redirects automatically; `{externallink}` was dropped [PR #505] (v1.1).
- Per-Contact URLs (`{webview_url}`, `{unsubscribe_url}`) are never trackables, because every recipient once got the first Contact's unsubscribe URL [PR #1310] (v1.2.4).
- Each Contact must get its own content, tokens and tracking hashes, even when `EMAIL_ON_SEND` listeners call `setContent()` [PR #14051] (v5.2) or a builder listener changes the content hash [PR #13965] (v5.2).
- Previews, Send example and emails to users are not link-tracked [PR #595] (v1.1.3) [PR #1696] (v1.4).
- A click marks the stat as read [PR #921] (v1.2.1). Dynamic-content links carry the stat hash so clicks are attributed [PR #6229] (v2.14). Do-not-track bots and IPs are not logged [PR #6591] (v2.15).
- `disable_trackable_urls` (default off) [PR #4223] (v2.9) does not disable UTM tags; UTM is still appended [PR #15748] (v7.0.1).
- UTM tags are appended to trackable links only [PR #3891] (v2.9); `utm_name` became `utm_campaign` [PR #4605] (v2.10.1); values over 191 characters are rejected [PR #11317] (v5.0). Global UTM defaults pre-fill only new emails [PR #15905] (v7.2).
- Links in Segment sends use `site_url`, not the request or CLI host [PR #11919] (v5.0) [PR #17168] (v7.2).
- Whitespace in `href` is trimmed and still tracked [PR #15698] (v7.0.1). Malformed links are left untracked at send so the cron does not crash, and saving an email with one is blocked by `ValidEmailLinks` [PR #16256] (v7.2); `#`, `tel:`, `mailto:`, relative links and tokens pass [PR #16508] (v7.2).
- Clicks while logged into Mautic in the same browser are not tracked [PR #15486] (v7.0).

### Open tracking and bot filtering
- The pixel goes before `</body>` [PR #122] (v1.0) without `display:none`, which Gmail skipped [PR #2316] (v2.1.1). Tracking runs before the image is streamed [PR #1035] [PR #1050] (v1.2.2). It can be turned off with `mailer_append_tracking_pixel` [PR #1632] (v1.4).
- `openDetails` is capped at 1000 entries while `openCount` keeps counting, after 20k hits overloaded MySQL [PR #6183] (v3.2).
- `read_count` increments once per Contact under concurrency [PR #12673] (v5.0) and was repaired with a backfill migration [PR #13915] (v5.1.1).
- Bot ratio (6.0): blocked IPs, blocked user agents and an open within `bot_helper_time_email_threshold` (2 s) of sending are signals; at `bot_helper_bot_ratio_threshold` (0.6) the open is not tracked [PR #14593] (v6.0). The pixel and `ct` carry `sent_time` so a front layer can drop early hits [PR #14816] (v7.0). Matomo device-detector was added and closes issue mautic/mautic#16069 (Gmail image-proxy opens lost in 7.1) [PR #15870] (v7.2).
- Stat and device stat are saved in separate transactions to avoid deadlocks [PR #6843] (v2.15).

### Unsubscribe, List-Unsubscribe and the Preference Centre
- Unsubscribe records "unsubscribed", not bounced [PR #1421] (v1.3), and works for direct sends without an email entity [PR #591] (v1.1.3). Deleted-Contact links return gracefully [PR #6287] [PR #6135] [PR #7089] [PR #7414] (v2.14–v2.15.2).
- The unsubscribe URL `/email/unsubscribe/{idHash}/{urlEmail}/{secretHash}` finds the Contact by address verified with an HMAC-SHA256 of the address when the stat is gone [PR #10846] (v5.1).
- `List-Unsubscribe` uses Mautic's URL even without a monitored inbox [PR #6084] (v2.14) and must not accumulate values across sends [PR #7110] (v2.15.2).
- RFC 8058 one-click: marketing emails carry `List-Unsubscribe-Post: List-Unsubscribe=One-Click`, and a POST with that body unsubscribes without confirmation [PR #13103] (v5.0). The HTTPS URL comes first and `mailto:` second, because Gmail uses the first [PR #13407] (v5.1).
- Header rule history. In 5.0 transactional, direct and API sends lost `List-Unsubscribe`, with no config switch [PR #11787] (v5.0); 5.0.0 to 7.1.0 skip the header when the email type is transactional or there is no email entity [code: app/bundles/EmailBundle/Helper/MailHelper.php:1327 @7.1.0]. From 7.2.0 the header is skipped when the email has `sendToDnc`, when `disable_unsubscribe_link_header` is on (first present in 7.2.0), or when the body has no unsubscribe link [code: app/bundles/EmailBundle/Helper/MailHelper.php:1318-1333 @7.x] [code: app/bundles/EmailBundle/Config/config.php:198 @7.x].
- A HEAD request to the unsubscribe URL never creates a DNC, because link scanners send HEAD [PR #14967] (v7.1.3).
- Unsubscribe and resubscribe links go first to a page where the recipient types their address, which must match the HMAC; opt out with `validate_unsubscribe_emails`. The frictionless default was rejected because the secure default wins [PR #16870] (v7.3.0-rc).
- Preference Centre: custom pages work without `{channelfrequency}` [PR #6265] (v2.14.1); only preference slots are wrapped in the form [PR #6404] (v2.15.2); the success message is a translation string [PR #11468] (v5.0) shown only after submit [PR #15565] (v7.1); clearing "I want to receive email" writes a DNC and rechecking removes it [PR #14175] (v5.2); Segments are listed by public name and only published, Preference-Centre-flagged ones [PR #15850] (v7.2); frequency blocks have `id="frequency_<channel>"` [PR #17669] (v7.2.2).
- The language order is Contact locale, then Preference page language, then user locale, then system locale [PR #14370] (v6.0).
- The global default Preference Centre was first copied onto new emails [PR #15905] (v7.2); it is now resolved live at unsubscribe time: the email's page, then the current global default [PR #16352] (v7.2).
- Changing an email's Preference Centre page is audit-logged [PR #15553] (v7.0).

### Bounces, replies, VERP and the monitored inbox
- Monitored IMAP inboxes are read by `mautic:email:fetch` [PR #797] (v1.2), one folder per purpose, unread only [PR #2303] (v2.1.1), disconnecting between mailboxes [PR #2715] (v2.2.1).
- Bounce and unsubscribe matching takes the part after the last `_` in `+bounce_<hash>` [PR #1021] (v1.2.1). Replies match only the pixel hash [PR #7445] (v2.15.2). Unrecognised bounces create no DNC [PR #2835].
- Parser rules were added over time [PR #1312] [PR #2710] [PR #2835] [PR #3154] [PR #4638] [PR #7462]; Outlook/Exchange codes 5.4.1, 5.7.193, 5.4.317, 5.7.511 and 5.7.606 were mapped in 7.0 [PR #15371] (v7.0).
- FBL/ARF reports become DNC Unsubscribed [PR #2446] (v2.2).
- Replies: the "Replies" folder and `email.reply` decision [PR #5194] (v2.12); UID-range fetch so the decision keeps firing [PR #6376] (v2.14.2); `POST /api/emails/reply/{trackingHash}` [PR #7718] (v3.1); `+alias` addresses [PR #11779] (v5.0).
- `X-EMAIL-ID` on campaign and Segment emails lets provider bounces be attributed [PR #7893] (v2.16.1).
- VERP chain. Mautic authenticates with the configured account, not the randomised bounce address (Postfix 553) [PR #15674] (v7.1). That change set an unconditional `Sender` header, which Symfony prefers over Return-Path, so VERP bounces were lost. `Sender` and Return-Path are now exclusive: with a bounce mailbox or `mailer_return_path`, Return-Path is set and `Sender` removed [PR #16152] (v7.2).
- Multi-folder fetch no longer fails with "IMAP\Connection is already closed" [PR #15364] (v6.0.5); sending no longer fails when IMAP is set but "Monitored address" is empty [PR #16302] (v7.1.3).

### Transports, mailer DSN, embedding and S/MIME
- 5.0 replaced Swiftmailer with Symfony Mailer. All bundled transports left core for plugins, the mailer is one DSN (`mailer_dsn`), queueing goes through Messenger, the file spool was dropped, and callback keys follow the DSN scheme [PR #11613] (v5.0).
- Before 5.0, API transports sent tokenised batches [PR #429] (v1.1) [PR #2284] (v2.1.1) [PR #8703] (v3.0); batch transports implement `TokenTransportInterface` in 7.x [PR #11613].
- DSNs are url-encoded with `%` escaped as `%%` and read by the `urlencoded-dsn` env processor [PR #13255] (v5.0.3). Transport plugins can return their own validation messages [PR #12624] (v5.0).
- The default `mailer_dsn` is `smtp://localhost:1025` (Mailpit/DDEV); production must set its own [PR #15627] (v7.1).
- An over-long "Name <email>" is sent to the bare address (`mailer_address_length_limit`, 320) [PR #14577] (v5.2.3).
- Tokenised transports use the From typed in the direct-send form [PR #14661] (v6.0).
- `mailer_convert_embed_images` (off by default) [PR #1512] (v1.4) was fixed repeatedly: one attachment per image per email [PR #7804] (v2.16) [PR #8600] (v2.16.2) [PR #9080] (v3.2.2), the pixel never embedded [PR #9300] (v3.1.2) [PR #11390] (v4.4.2), and `cid:` embedding under Symfony Mailer [PR #13219] (v5.0.2).
- `minify_email_html` (off by default) minifies HTML [PR #11947] (v5.0). Assets as attachments work again after Symfony 6 [PR #14715] (v6.0).
- S/MIME signing (not encryption) is enabled by `smime_signing_enabled`, with `<email>.crt` and `<email>.pem` per From address; it is reliable only with SMTP [PR #15563] (v7.1). The path is `%kernel.project_dir%/var/smime_certificates`, not the `smime_certificates` named in the PR text [code: app/bundles/EmailBundle/Config/config.php:222-223 @7.x].

### From, Reply-To and headers
- Mailer is owner was global [PR #1319] (v1.3) and applied to campaign [PR #2127] [PR #6163], token-transport [PR #3783] and API sends [PR #11347]. It became per email with the global value as default [PR #6071] (v3.3); the switch warns when it differs from global [PR #13322] (v5.1).
- From precedence: a resolving tokenised From wins, then the owner when "Use owner as mailer" is on, then the email's plain From, then the system default [PR #7811] (v5.1) [PR #16060] (v7.2). In 7.x a token is resolved before the owner is considered, and an empty token falls back to the owner, then the default [code: app/bundles/EmailBundle/Helper/FromEmailHelper.php:42-61 @7.x] [code: app/bundles/EmailBundle/Helper/FromEmailHelper.php:174-196 @7.x].
- A From name with an empty From address uses the custom name and the system address [PR #10222] (v4.0).
- Reply-To chain. The email's From was used when its Reply-To was blank [PR #10471] (v4.1), the global `mailer_reply_to_email` was added [PR #9812] (v4.1), the email's Reply-To beat the owner [PR #12405] (v5.0), and queued sends resolved per owner group [PR #15945] (v7.2). Final rule: email Reply-To, then owner (owner-as-mailer), then email From, then global reply-to or system From, for single and queued sends [PR #17356] (v7.3.0-rc) [code: app/bundles/EmailBundle/Helper/MailHelper.php:1997-2054 @7.x].
- A Form "reply to Contact" setting beats the global reply-to [PR #10773] (v4.2).
- System `mailer_custom_headers` apply only to sends without an email entity [PR #6060] (v2.14); per-email headers support Contact tokens [PR #6060].
- On the direct "send to Contact" form, the form From overrides the template email, which overrides global config [PR #13792] (v5.2).

### A/B tests, variants, translations and cloning
- Weights are honoured, weight 0 is skipped, and weights must total at most 100% [PR #666] (v1.1.3) [PR #948] [PR #1688]. Campaign sends recalculate weights each send [PR #2335] (v2.1.1).
- Winner logic runs through determine-winner events [PR #8145] (v3.0); a manual winner dispatches `ManualWinnerEvent` [PR #15464] (v7.0).
- Segment Emails with zero sends can be converted to an A/B test; at least two variants are needed before scheduling; `mautic:email:sendwinner` picks the winner [PR #15897] (v7.2).
- After the delay the winner goes to remaining Contacts through the normal broadcast pipeline (respecting `--limit`, batch and threads), winners without `publishUp` are picked up, and per-variant counts are rebuilt every call; a manual winner does not email the rest [PR #17296] (v7.3.0-rc).
- Saving a parent must not overwrite translation children [PR #10525] (v4.0.2) [PR #10620] (v4.2.1). API PATCH keeps the translation-parent link [PR #15070] (v7.0). The parent sent count includes translations [PR #15616] (v7.1).
- Translations and variants appear as their own list rows [PR #15407] (v7.1) [PR #15408] (v7.0).
- Cloning creates nothing until save [PR #699], starts with zero stats [PR #5781], resets plain text [PR #12748] (v5.0) and clears publish dates so the clone is not broadcast [PR #12784] (v5.0). Clone permission is checked on the original [PR #14580] (v5.2.3). "Clone with translations and variants" creates an unpublished family [PR #16131] (v7.2).

### Preview, web view, test sends and drafts
- A web view by a logged-in user records no view stat [PR #1445] (v1.3).
- Public preview became a per-email toggle (403 when off) [PR #6679] (v2.15), off by default [PR #10845] (v4.2.1), because email IDs are enumerable. [PR #10971] and [PR #14525] (v5.2.3) made it work for expired and unpublished emails. [PR #17549] (v7.3.0-rc) requires the published flag for anonymous viewers. In the 7.x snapshot anonymous access needs `isPublished` and `publicPreview`; publish-up/down are not checked, so an expired published email still previews [code: app/bundles/EmailBundle/Controller/PublicController.php:561-575 @7.x]. At 7.2.1 only `publicPreview` was checked [code: app/bundles/EmailBundle/Controller/PublicController.php:473 @7.2.1].
- [PR #17549] (v7.3.0-rc) also added the standalone preview page with Contact and Company pickers and "Download HTML"; real Contact tokens show only with Contact view permission.
- Preview of translations and A/B variants needs login and view permission [PR #11719] (v5.1).
- Send example sends to several recipients [PR #2488] (v2.5), prefixes `[TEST]` [PR #8443] (v3.0), has no pixel, tracking or UTM [PR #122] [PR #3891], can render as a chosen Contact [PR #13983] (v5.2) and is available from each list row [PR #16871] (v7.2).
- Drafts (`email_draft_enabled`, off by default) store changes separately; sends always use live content [PR #14028] (v5.2). Discard restores plain text, publish dates and Continue sending [PR #17653] (v7.2.2).

### Email management UI and API
- Optimistic locking rejects a save when the email changed elsewhere [PR #15774] (v7.1); repeated builder "Apply" refreshes the version [PR #15894] (v7.1).
- Without publish permission new emails save unpublished and the API resets publish dates [PR #15543] (v7.0).
- Internal name is at most 190 characters [PR #15147] (v6.0.3).
- Bulk delete deletes only emails; a 5.2 regression deleted Contacts with the same IDs [PR #14335] (v5.2.1).
- "Template email" was renamed "Trigger email" [PR #14084] (v5.2).
- Per-email feature flags go in the JSON `settings` field [PR #16363] (v7.2); `EMAIL_ON_TOGGLE_PUBLISH` was added [PR #16244] (v7.2).

### Stats, reports and webhooks
- Emails to Mautic users get tokens replaced but create no stat and no timeline entry [PR #595] (v1.1.3) [PR #5529] (v2.12.2).
- A stat is saved before the transport call and deleted on failure [PR #5807] (v2.13); failures decrement the sent count [PR #4523] (v2.9.1). `EmailStatModel` is the single save path and dispatches stat events [PR #13341] (v5.1).
- Segment Email stats come from `email_stats`, not current membership [PR #9580] (v3.3.3).
- Delivered = Sent − Bounced − Failed [PR #11965] (v5.0).
- Click graphs use unique clickers [PR #8228] (v3.1.1); template emails show unique clicks [PR #15486] (v7.0).
- Webhook `mautic.email_on_send` fires once per real send, not for test sends [PR #7716] (v3.3) [PR #8619] (v3.0.2). `webhook_email_details` off removes content and tokens from the payload [PR #13447] (v5.1).
- Timeline "Email read" shows the time from send to read [PR #17321] (v7.2.1).
- Reports gained CTR/CTOR [PR #12713] (v5.0) and UTOR [PR #15066] (v7.1).

## 3. Removed, deprecated, replaced

| What | Replaced by | Version | PR |
|---|---|---|---|
| `{externallink}` token | Automatic trackables | v1.1 | [PR #505] |
| Random Contact for example tokens | `[Field Name]` placeholders | v1.2.1 | [PR #920] |
| Single "Send example" | Multi-recipient Send example | v2.5 | [PR #2488] |
| `utm_name` | `utm_campaign` | v2.10.1 | [PR #4605] |
| Email events in calendar | None | v2.15 | [PR #6853] |
| PHP Mailer transport | SMTP or other | v3.0 | [PR #8192] [PR #8193] [PR #8195] |
| Static AbTestHelper | Determine-winner events | v3.0 | [PR #8145] |
| `ON_CAMPAIGN_TRIGGER_ACTION` for send-to-user | `ON_CAMPAIGN_BATCH_ACTION` | v3.0 | [PR #8236] |
| Global-only mailer-is-owner | Per-email setting, global default | v3.3 | [PR #6071] |
| Pending count on email detail | Pending on email list | v4.1 | [PR #10590] |
| Public preview on by default | Off by default | v4.2.1 | [PR #10845] |
| Strict email validation in config | `html5` mode | v4.3 | [PR #11054] |
| Swiftmailer and all core transports | Symfony Mailer, `mailer_dsn`, transport plugins | v5.0 | [PR #11613] |
| File spool, `mautic:emails:send` | Symfony Messenger | v5.0 | [PR #11613] |
| Callback key `amazon_api` | DSN scheme (`ses+api`) | v5.0 | [PR #11613] |
| Batch-size input on manual send | `mailer_memory_msg_limit` | v5.0 | [PR #11167] [PR #11595] |
| Old `--limit`/`--batch` semantics | SMS-consistent semantics | v5.0 | [PR #11127] |
| List-Unsubscribe on transactional/direct mail | No header (until 7.1) | v5.0 | [PR #11787] |
| EmailBundle PHP templates | Twig | v5.0 | [PR #11974] [PR #12126] |
| `EmailRepository::upCount` | `upCountSent` / `incrementRead` | v5.0 | [PR #12673] |
| Emoji shortcodes | utf8mb4 columns | v5.1 | [PR #13337] |
| "Google Analytics UTM tags" label | "UTM tags" | v5.1 | [PR #13581] |
| Campaign default type Transactional | Marketing | v5.2 | [PR #14145] |
| "Template email" wording | "Trigger email" | v5.2 | [PR #14084] |
| `MauticFactory` getters | Dependency injection | v6.0 (disputed, see Open questions) | [PR #14382] [PR #14611] |
| Hidden publish fields on trigger emails | Publish up/down shown | v7.0 | [PR #13818] [PR #15506] |
| `mailer_dsn` `smtp://localhost:25` | `smtp://localhost:1025` | v7.1 | [PR #15627] |
| Campaign "Email type" and transactional DNC bypass | "Repeatable email" + email `sendToDnc` | v7.2 | [PR #15995] |
| Default Preference Centre copied onto emails | Resolved at unsubscribe | v7.2 | [PR #16352] |
| `getLookupResultsWithIdName()` | `getLookupResults()` `(id) name` | v7.2 | [PR #16086] |
| Non-final validators, MonitoredEmail, transports, `PlainTextHelper` | `final` classes | v7.2 | [PR #16886] [PR #16887] [PR #16897] [PR #16941] |
| Single-process A/B winner send | Broadcast pipeline | v7.3.0-rc | [PR #17296] |
| Direct unsubscribe/resubscribe links | Address-validation page first | v7.3.0-rc | [PR #16870] |
| Send once per unique address | Reverted, not in core | 2024-06 | [PR #13768] [PR #13902] |
| Frequency rules on transactional sends | Reverted, no net change | v2.15 | [PR #6760] [PR #6849] [PR #6896] [PR #6944] |

## 4. Regression catalogue
Rows describe contracts still true in 7.x. Sorted by sub-topic.

| Area | Symptom | Expected behaviour | PR | Version |
|---|---|---|---|---|
| Eligibility | Bad address aborted a batch; later good addresses failed | Mark that one failed, reset the error, continue | [PR #351] [PR #602] | v1.0.4/v1.1 |
| Eligibility | Transport error marked the Contact DNC "bad format" | Only malformed addresses become DNC | [PR #5807] | v2.13 |
| Eligibility | Unpublishing mid-send did not stop it | Unpublished emails cannot send | [PR #5938] | v2.13.1 |
| Eligibility | Category-unsubscribed Contacts still mailed | Exclude by Category preference | [PR #10879] | v5.1 |
| DNC | Imported/bulk DNC left Contacts contactable (reason 0) | Always pass an explicit reason | [PR #9186] | v3.1.2 |
| DNC | DNC Contacts emailed on ANSI `sql_mode` databases | DNC SQL is mode-agnostic | [PR #12919] | v5.1 |
| DNC | Failed send created DNC on the first retry | Retry 3 times first | [PR #13341] | v5.1 |
| Campaign | Campaign emails reached unsubscribed Contacts after 5.0 | Default type Marketing; since 7.2 only `sendToDnc` bypasses DNC | [PR #14145] [PR #15995] | v5.2/v7.2 |
| Campaign | Contact N carried tokens of Contacts 1..N-1 | Reset metadata per Contact | [PR #3995] | v2.8.1 |
| Campaign | Already-sent marketing email rescheduled every run | Pass once with a note | [PR #7413] | v2.15.2 |
| Campaign | Failed scheduled email re-sent every trigger run | Persist the failure log | [PR #7733] | v2.15.3 |
| Campaign | Bad CC/BCC: event "executed", nothing sent | Fail visibly | [PR #3193] [PR #9276] | v2.6/v3.1.2 |
| Campaign | A/B variant sent twice in one campaign | Once per Contact | [PR #14838] | v5.2.5 |
| Campaign | Translation selected directly, wrong language | Selector lists top-level emails only | [PR #15745] | v7.1 |
| Campaign | Export failed with translations | Export succeeds | [PR #15831] | v7.0.1 |
| Campaign | "Has valid email" TypeError on null | Returns false | [PR #13976] | v5.2 |
| Frequency | 4th email at 3/week pushed 3 weeks | Next frequency period | [PR #4761] | v2.10 |
| Send to user | CC/BCC not delivered or sent once per To | Exactly one per address | [PR #8768] | v3.0 |
| Send to user | Form action without user mailed the Contact | User required | [PR #10243] | v4.0 |
| Segment | Broadcast looped with frequency-queued Contacts | Queued is not pending | [PR #3560] | v2.7 |
| Segment | Pending 0 when Contact got any other email | Pending is per email | [PR #722] | v1.2 |
| Segment | Deleted recipients hid pending Contacts | NULL `lead_id` ignored | [PR #392] [PR #5697] | v1.1/v2.13 |
| Segment | `--limit=10 --batch=2` sent batches of 10 | Limit total, batch as given | [PR #11127] | v5.0 |
| Segment | Segment sends did nothing on 5.0 | `mailer_memory_msg_limit` default 100 | [PR #11595] | v5.0 |
| Segment | Cloned email broadcast by cron | Clone clears publish dates | [PR #12784] | v5.0 |
| Segment | Duplicates from parallel processes | Re-check just before each send | [PR #14531] | v6.0 |
| Segment | Memory exhausted on large broadcasts | Clear metadata after each send | [PR #15121] | v5.2.7 |
| Segment | Worker crash when Contact deleted mid-send | Skip and continue | [PR #16073] | v7.1.2 |
| Segment | Stale pending count | Not served stale after membership change | [PR #16442] | v7.1.3 |
| Segment | A/B winner OOM on 1M+ Contacts; null publishUp never sent | Batched broadcast; null publishUp included | [PR #17296] | v7.3.0-rc |
| Tracking | Everyone got the first Contact's unsubscribe URL | Per-Contact URLs never trackable | [PR #1310] | v1.2.4 |
| Tracking | Contacts got each other's tokens/hashes with on-send listeners | Per-Contact isolation | [PR #14051] [PR #13965] | v5.2 |
| Tracking | Anchor spanning `<br>` gave everyone the same `ct` | Detect multi-line anchors | [PR #15190] | v7.0 |
| Tracking | `://example.com` crashed the broadcast cron | Skip at send, block on save | [PR #16256] [PR #16508] | v7.2 |
| Tracking | Segment links used the admin host | `site_url` | [PR #11919] [PR #17168] | v5.0/v7.2 |
| Tracking | Disabling trackable URLs dropped UTM | UTM independent | [PR #15748] | v7.0.1 |
| Tracking | Whitespace in href broke tracking | Trim | [PR #15698] | v7.0.1 |
| Tracking | Click decision missed URL-encoded URLs | Match encoded and decoded | [PR #15550] | v7.1 |
| Opens | Gmail opens untracked | No `display:none` on pixel | [PR #2316] | v2.1.1 |
| Opens | 20k pixel hits overloaded MySQL | Cap `openDetails` at 1000 | [PR #6183] | v3.2 |
| Opens | `read_count` never updated | Increment, backfill | [PR #13915] | v5.1.1 |
| Opens | Gmail image-proxy opens dropped in 7.1 | Proxy opens count | [PR #15870] | v7.2 |
| Embed | Nth email carried N-1 extra attachments | One embed per image | [PR #7804] [PR #8600] | v2.16 |
| Embed | Pixel embedded as an empty attachment | Pixel never embedded | [PR #9300] [PR #11390] | v3.1.2/v4.4.2 |
| Unsubscribe | Unsubscribe recorded as bounce | Record unsubscribed | [PR #1421] | v1.3 |
| Unsubscribe | Deleted-Contact links returned 500 | Graceful response | [PR #6287] [PR #7414] | v2.14/v2.15.2 |
| Unsubscribe | Gmail used `mailto:` | HTTPS one-click first | [PR #13407] | v5.1 |
| Unsubscribe | Link scanners unsubscribed Contacts | HEAD never writes DNC | [PR #14967] | v7.1.3 |
| Unsubscribe | Web view 500 on NULL tokens | NULL means no tokens | [PR #15026] | v5.2.7 |
| Pref centre | Email checkbox did not set DNC | Clear writes DNC, recheck removes | [PR #14175] | v5.2 |
| Pref centre | Success message always shown | Only after submit | [PR #15565] | v7.1 |
| Pref centre | Literal PHP in Twig broke frequency controls | `id="frequency_<channel>"` | [PR #17669] | v7.2.2 |
| Headers | List-Unsubscribe grew per send | One value per message | [PR #7110] | v2.15.2 |
| Headers | Owner overrode the email's Reply-To | Email Reply-To wins | [PR #12405] | v5.0 |
| Headers | Global reply-to beat the email's From | Email From wins | [PR #15945] [PR #17356] | v7.2/v7.3.0-rc |
| Headers | Custom Return-Path header gave 500 | Tokens in unstructured headers only | [PR #12912] | v5.0 |
| Headers | Form "reply to Contact" overridden by global reply-to | Form setting wins | [PR #10773] | v4.2 |
| From | Mailer-is-owner ignored in campaign/API/token sends | Owner applied on every path | [PR #2127] [PR #3783] [PR #11347] | v2.1–v4.4 |
| From | `{signature}` ignored the per-email owner switch | Per-email switch decides | [PR #15931] | v7.2 |
| Transport | Tokenised transports ignored direct-send From | Form From used | [PR #14661] | v6.0 |
| Transport | Special characters in DSN broke config | `urlencoded-dsn`, `%%` | [PR #13255] | v5.0.3 |
| Bounces | VERP bounces lost from 7.1.0 | `Sender` removed when Return-Path set | [PR #16152] | v7.2 |
| Bounces | SMTP 553 with bounce-tagged auth | Authenticate with configured account | [PR #15674] | v7.1 |
| Bounces | IMAP "Connection already closed" | Multi-folder fetch completes | [PR #15364] | v6.0.5 |
| Bounces | 500 on send with IMAP set but no monitored address | Send succeeds | [PR #16302] | v7.1.3 |
| Replies | Reply decision stopped after first fetch | UID-range fetch | [PR #6376] | v2.14.2 |
| Stats | User emails appeared in Contact stats | No stat for user emails | [PR #595] [PR #5529] | v1.1.3/v2.12.2 |
| Stats | Failures doubled the sent count | Decrement on failure | [PR #4523] | v2.9.1 |
| Stats | Segment stats lost Contacts who left the Segment | Use `email_stats` | [PR #9580] | v3.3.3 |
| Webhooks | Duplicate `email_on_send` webhooks | One per send | [PR #7716] [PR #8619] | v3.3/v3.0.2 |
| A/B | Campaign sent the same variant to everyone | Recalculate weights per send | [PR #666] [PR #2335] | v1.1.3/v2.1.1 |
| Translations | Saving the parent overwrote children | Skip child content | [PR #10525] [PR #10620] | v4.0.2/v4.2.1 |
| Drafts | Discard draft wiped plain text and dates | Snapshot restores all | [PR #17653] | v7.2.2 |
| Locking | Lock error on second builder Apply | Refresh version after Apply | [PR #15894] | v7.1 |
| Management | Bulk email delete removed Contacts | Only emails deleted | [PR #14335] | v5.2.1 |
| Permissions | Users without publish permission auto-published | Saved unpublished | [PR #15543] | v7.0 |

## 5. Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.x | Pixel, automatic trackables, tokenised API transports, monitored inbox, mailer-is-owner, `{signature}`, image embedding, pixel switch | [PR #122] [PR #505] [PR #429] [PR #797] [PR #1319] [PR #1512] [PR #1632] |
| 2.0–2.5 | Device stats, FBL, message queue and frequency rules, dynamic content, scheduled broadcasts, multi-recipient Send example | [PR #2059] [PR #2446] [PR #2549] [PR #2574] [PR #2259] [PR #2488] |
| 2.6–2.16 | Click decision, send to user, UTM tags, reply processing, public preview toggle, `X-EMAIL-ID`, contact-ID ranges | [PR #3887] [PR #4458] [PR #3891] [PR #5194] [PR #6679] [PR #7893] [PR #5715] |
| 3.x | Determine-winner events, `[TEST]` prefix, plain-text generation, reply API, per-email mailer-is-owner | [PR #8145] [PR #8443] [PR #8645] [PR #7718] [PR #6071] |
| 4.x | Global reply-to, accessibility tags, public preview off by default | [PR #9812] [PR #10402] [PR #10845] |
| 5.0 | Symfony Mailer + Messenger; transactional ignores DNC; no List-Unsubscribe on transactional; RFC 8058 one-click; thread options; `{today}`; minify | [PR #11613] [PR #11786] [PR #11787] [PR #13103] [PR #11549] [PR #11722] [PR #11947] |
| 5.1 | Variant/translation preview, excluded Segments, HTTPS-first List-Unsubscribe, pre-send event, token From, Category opt-out | [PR #11719] [PR #13458] [PR #13407] [PR #13360] [PR #7811] [PR #10879] |
| 5.2 | Campaign default Marketing, Preheader, drafts, `{dnc_url}`, `{resubscribe_url}`, "Trigger email" | [PR #14145] [PR #13792] [PR #14028] [PR #14114] [PR #14215] [PR #14084] |
| 6.0 | Bot ratio, last-moment duplicate check, campaign Email Metrics tab | [PR #14593] [PR #14531] [PR #14414] |
| 7.0 | Schedule send and Continue sending, publish fields back on trigger emails, publish permission, `sent_time` in pixel | [PR #14254] [PR #15506] [PR #15543] [PR #14816] |
| 7.1 | S/MIME signing, optimistic locking, default DSN port 1025, campaign selector top-level only | [PR #15563] [PR #15774] [PR #15627] [PR #15745] |
| 7.1.3 | HEAD never unsubscribes, pending not stale | [PR #14967] [PR #16442] |
| 7.2 | `sendToDnc` and "Repeatable email", Segment A/B tests, tokenised From chain, VERP fix, link validation, global UTM defaults, settings JSON | [PR #15995] [PR #15897] [PR #16060] [PR #16152] [PR #16256] [PR #15905] [PR #16363] |
| 7.2.2 | Discard draft restores all, frequency block ids | [PR #17653] [PR #17669] |
| 7.3.0-rc | Unsubscribe address validation, A/B winner via broadcast, Reply-To final rule, preview page, AND-ed dynamic-content filters | [PR #16870] [PR #17296] [PR #17356] [PR #17549] [PR #17404] |

## 6. Maintainer norms for this area
- BC breaks are acceptable in a major when documented in UPGRADE notes and tooltips, and are preferred over adding switches [PR #11786] [PR #11787].
- New output-changing behaviour defaults to the old behaviour unless a major allows the break [PR #1319] [PR #1632] [PR #2259].
- Secure defaults win over usability; add an opt-out config if needed [PR #16870] [PR #10845].
- No "global" fix for a "localized" bug; merges that break behaviour or tests are reverted the same day [PR #6896] [PR #6849] [PR #13768] [PR #13902].
- Bug fixes need a regression test that fails before the fix [PR #7733] [PR #14967] [PR #17653].
- Fix the root cause and add a save-time constraint, not only a send-time try/catch [PR #16256].
- Defaults must apply on the save path, so the API gets them too, not only in form types [PR #15905].
- Pending and stats queries are tested at million-Contact scale and must work on MySQL and PostgreSQL [PR #1400] [PR #6592] [PR #665].
- Do not write cache from the send path; load heavy stats over AJAX with an off switch [PR #7079] [PR #14414].
- Plugins must not replace tokens directly in content [PR #3995].
- Embedded images, Base64 and the tracking pixel must be tested in every combination [PR #8967] [PR #9080].
- Use `MailHelper::EMAIL_TYPE_*` constants rather than strings [PR #12654].
- Classes without children are `final`; depend on interfaces with constructor injection [PR #16886] [PR #16941].
- Many 7.x features are "unforked" from downstream forks [PR #15897] [PR #15995] [PR #16060] [PR #16870] [PR #17296].
- New tokens and behaviour changes need user documentation and help-modal entries [PR #14114] [PR #14215] [PR #15897].

## 7. Open questions
1. Campaigns skill conflict: the campaigns skill says an event saved without `email_type` is sent as Transactional, "which ignores DNC" [PR #14145]. The default to transactional is true in 7.x, but since 7.2.0 DNC bypass comes only from the email's `sendToDnc` [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:274-286 @7.x]. The "ignores DNC" part holds only for 5.0 to 7.1.
2. `disable_unsubscribe_link_header` first appears in the 7.2.0 tag; the digests do not name the PR that added it. [PR #11787] had argued no switch was needed [code: app/bundles/EmailBundle/Config/config.php:198 @7.x].
3. Public preview: [PR #14525] allowed unpublished emails; [PR #17549] requires the published flag (7.3.0-rc). Drafts and public preview should be checked to agree [PR #14028].
4. Duplicate Segment sends: [PR #14531] leaves a race window; no atomic stat insert followed, and [PR #13768] was not re-landed.
5. Gmail proxy opens: [PR #15870] closes issue mautic/mautic#16069 by stricter bot detection; verify that GoogleImageProxy opens count.
6. `validate_unsubscribe_emails`: its effect on the Preference Centre page and on pre-7.3 links is unclear [PR #16870]. The broader DNC review after [PR #14967] did not ship.
7. Manual A/B winner: the warning implies the rest is never sent automatically [PR #17296].
8. VERP on 7.1.x: the fix merged after 7.1 EOL, so 7.1.x keeps the regression [PR #16152].
9. Link validation applies to emails but not landing pages [PR #16256].
10. Emails created between [PR #15905] and [PR #16352] may store the default Preference Centre explicitly; no migration was mentioned.
11. Resubscribe fails when the stat row is deleted, while unsubscribe falls back to the address [PR #14215].
12. BCC through batch transports: one per transmission or per Contact [PR #4671] [PR #3193].
13. Unrecognised bounces as hard bounces is undecided; `452 4.2.2 over quota` is not caught [PR #2835] [PR #4638].
14. `MauticFactory::getEntityManager` removal: 6.0 milestone vs "bumped to 7.0-alpha" [PR #14611].
15. Minify may create lines over 998 octets; remote-image embedding is a security concern [PR #11947] [PR #13219].
16. A test runs `mautic:broadcast:send`, which works only through Symfony's unambiguous-abbreviation matching, not an alias [code: app/bundles/EmailBundle/Tests/Controller/EmailControllerFunctionalTest.php:1256 @7.x] [code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:23 @7.x]. Earlier PRs write both spellings [PR #5715] [PR #11127].

## 8. Coverage
- 761 PRs were analysed in 10 chunks (472 for 2015 to mid-2024 and 289 for late 2022 to 2026, with some overlap in dates); about 660 were substantive and about 100 were refactors, merge-ups or chores [PR #11613] [PR #17549].
- 869 noise PRs (dependency bumps, CS, all-contributors) were excluded upstream before chunking [PR #11613].
- Pre-5.0 transport code (Swiftmailer, SparkPost, Mandrill, Mailjet, SES, SendGrid, Momentum, Pepipost, Elastic Email) is historical; those fixes live in external plugins if anywhere [PR #11613].
