---
name: mautic-emails
description: "Mautic Emails (EmailBundle) end to end: template vs Segment (broadcast) emails, why a contact did or did not get an email (the pending query, DNC, frequency rules, category opt-out, publish dates), pending counts, A/B tests and winner sending, tokens ({contactfield}, {unsubscribe_url}, {webview_url}), From/Reply-To resolution, open/click tracking and bot filtering, unsubscribe and the Preference Centre, bounces and the monitored IMAP inbox, transport webhooks, Symfony Mailer DSN and Messenger email queueing, campaign email actions (marketing vs transactional), and the Email REST API. Use whenever a task mentions emails, newsletters, segment emails, broadcasts, mautic:broadcasts:send, mautic:email:fetch, email_stats, pending/sent/read counts, opens or clicks not tracked, unsubscribe links, bounces, mailer_dsn, EmailModel, MailHelper, /api/emails, or asks 'why didn't this contact get the email' or 'why did nothing send', or touches app/bundles/EmailBundle/."
---
# Mautic Emails

## Scope
EmailBundle authors emails, renders them per Contact (a Contact is a person record; code name "lead"), sends them
through Symfony Mailer (optionally queued by Symfony Messenger), records one stat row per recipient, and tracks opens,
clicks, replies, bounces and unsubscribes [code: app/bundles/EmailBundle/Model/EmailModel.php:1347-1571 @7.x]
[code: app/bundles/EmailBundle/Helper/MailHelper.php:402-414 @7.x]. Out of scope: DNC storage and frequency-rule
entities (mautic-contacts), Segment membership building (mautic-segments), campaign execution (mautic-campaigns), click
redirects and page hits (mautic-pages-and-tracking), email themes and the GrapesJS/MJML builder
(mautic-theme-development), and worker/cron setup (mautic-cron-and-queues).

## Expected behaviour (essentials)
Terms: a **Segment Email** (`email_type = list`) is a broadcast to Segments; a **template Email** (`email_type = template`)
is sent by Campaigns, Forms, Points or the API. **DNC** (Do Not Contact) is a `lead_donotcontact` row with channel
`email` and reason 1 unsubscribed, 2 bounced or 3 manual [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-32 @7.x].

- An email saved with an empty type becomes `template`, and a non-Segment email has its Segments cleared on save [code: app/bundles/EmailBundle/Model/EmailModel.php:221-239 @7.x].
- A Segment Email is sent only by `mautic:broadcasts:send` or the UI/API "send"; the cron picks emails that are published, have `publishUp <= now` (not null), and `publishDown` null or in the future [code: app/bundles/EmailBundle/Entity/EmailRepository.php:892-914 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#excluding-segments].
- A Contact is pending for Segment Email E only if it is in an included Segment (not manually removed), has no email DNC of any reason, has no stat for E or any of E's variants/translations, has no unsent `message_queue` row for E, is not in an excluded Segment, has not opted out of E's Category, and has a non-empty email [code: app/bundles/EmailBundle/Entity/EmailRepository.php:183-345 @7.x].
- With **Continue sending** off (default), only Contacts whose Segment membership `date_added` is strictly before `publishUp` are sent; Contacts added later are never sent by that email [code: app/bundles/EmailBundle/Model/EmailModel.php:1021 @7.x] [code: app/bundles/EmailBundle/Entity/EmailRepository.php:285-288 @7.x].
- `publishDown` is ignored for a Segment Email unless Continue sending is on; the date-range validator only rejects `publishDown <= publishUp` when Continue sending is on [code: app/bundles/EmailBundle/Entity/Email.php:933-940 @7.x] [code: app/bundles/EmailBundle/Validator/ScheduleDateRangeValidator.php:14-48 @7.x].
- A Contact in several of the email's Segments receives it once: the pending query is per Contact, and the send path skips anyone with a non-failed stat for that email [code: app/bundles/EmailBundle/Model/EmailModel.php:1507-1514 @7.x].
- After a broadcast pass that sent nothing and leaves nothing pending, a non-continue-sending Segment Email that has sent before is unpublished automatically (thread 1 only) [code: app/bundles/EmailBundle/EventListener/BroadcastSubscriber.php:99-108 @7.x].
- The pending count is cached as `email|<id>|pending`; it is invalidated when an included/excluded Segment changes, but not when a Contact gets a DNC or stats are deleted [code: app/bundles/EmailBundle/Model/EmailModel.php:2394-2431 @7.x] [code: app/bundles/EmailBundle/EventListener/SegmentSubscriber.php:19-30 @7.x].
- `sendEmail()` drops every Contact with any email DNC unless `ignoreDNC` is true; Campaign, API and Form "send to contact" set `ignoreDNC` from the email's **Send to unsubscribed contacts** (`sendToDnc`) flag, and the Form action always ignores DNC [code: app/bundles/EmailBundle/Model/EmailModel.php:1399-1409 @7.x] [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:193 @7.x] [code: app/bundles/EmailBundle/EventListener/FormSubscriber.php:82-88 @7.x].
- With `sendToDnc` on, bounced Contacts are not filtered either: the DNC query ignores the reason (docs say Bounced is still respected - see Pitfalls) [code: app/bundles/EmailBundle/Entity/EmailRepository.php:53-77 @7.x].
- Segment Emails never honour `sendToDnc`: the pending query excludes all email DNC rows regardless of the flag [code: app/bundles/EmailBundle/Entity/EmailRepository.php:197-206 @7.x].
- Frequency rules (per-Contact or the global `email_frequency_number/time`) apply unless `sendToDnc` is on; Contacts over the limit are moved to `message_queue` and sent later by `mautic:messages:send` [code: app/bundles/EmailBundle/Model/EmailModel.php:1412-1425 @7.x] [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:68-119 @7.x].
- Campaign "Send email" has an `email_type`: **marketing** (default) passes without sending when the Contact already has a non-failed stat for the email or any variant child; **transactional** always sends again. Neither type bypasses DNC [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:315-382 @7.x].
- Contacts are shuffled and split across published A/B variants by weight, then routed to a published translation matching `preferred_locale` (exact `xx_YY`, else first `xx`) [code: app/bundles/EmailBundle/Model/EmailModel.php:1442-1494 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:1204-1343 @7.x].
- A stat row is persisted before the message goes to the transport and deleted if the send fails [code: app/bundles/EmailBundle/Model/SendEmailToContact.php:287-298 @7.x].
- An address the mailer rejects as malformed creates DNC `BOUNCED` "Incorrectly formatted email address" [code: app/bundles/EmailBundle/Model/SendEmailToContact.php:270-285 @7.x].
- With `messenger_dsn_email = sync://` (default) the SMTP/API call happens in the sending request or command; with a queue DSN the message is stored and `messenger:consume email` delivers it, so transport errors no longer mark stats failed [code: app/bundles/MessengerBundle/Config/config.php:7-13 @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php:402-414 @7.x].
- There is no `mautic:emails:send` command and no spool in 5.x+; it was removed with Swiftmailer [code: app/bundles/EmailBundle/Command/ProcessFetchEmailCommand.php:16-59 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#queued-delivery].
- From resolution: owner (when `useOwnerAsMailer` and the Contact has an owner), else the email's From, else the system From; `{contactfield=...}` tokens in From are resolved per Contact [code: app/bundles/EmailBundle/Helper/MailHelper.php:1963-1995 @7.x] [code: app/bundles/EmailBundle/Helper/FromEmailHelper.php:42-77 @7.x].
- Reply-To precedence: email Reply-To, then owner (owner-as-mailer), then email From, then global `mailer_reply_to_email`, then system From [code: app/bundles/EmailBundle/Helper/MailHelper.php:1997-2054 @7.x].
- Every link with an `http(s)`/`ftp` URL is rewritten to `/r/<redirect>?ct=...` with UTM tags, unless `disable_trackable_urls` is on or the link has `data-mautic-disable-tracking="true"` [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:228-317 @7.x] [code: app/bundles/PageBundle/Model/TrackableModel.php:740-747 @7.x].
- The open pixel `/email/{idHash}.gif` is appended before `</body>` when `mailer_append_tracking_pixel` is on; the hit goes through Messenger transport `hit` [code: app/bundles/EmailBundle/Helper/MailHelper.php:806-816 @7.x] [code: app/bundles/EmailBundle/Controller/PublicController.php:131-146 @7.x].
- Opens are ignored when the IP is untrackable or the bot heuristic fires (at least 60% of: opened within 2 s of sending, blocked IP, bot user agent) [code: app/bundles/EmailBundle/Model/EmailModel.php:442-452 @7.x] [code: app/bundles/EmailBundle/Helper/BotRatioHelper.php:35-85 @7.x].
- The first valid open sets `is_read`, `date_read` and increments `read_count` once; every open appends to `open_details` (capped at 1000) and writes an `email_stats_devices` row [code: app/bundles/EmailBundle/Model/EmailModel.php:454-548 @7.x].
- A tracked click marks the stat as read if it was not and fires the real-time `email.click` campaign decision [code: app/bundles/EmailBundle/EventListener/PageSubscriber.php:31-65 @7.x].
- `List-Unsubscribe` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` headers are added only when the body uses `{unsubscribe_url}` (or `{unsubscribe_text}` with `|URL|`), `sendToDnc` is off, and `disable_unsubscribe_link_header` is off [code: app/bundles/EmailBundle/Helper/MailHelper.php:1317-1396 @7.x].
- With `validate_unsubscribe_emails` on (default true; 7.x after 7.2.1, unreleased; [PR #16870]), `{unsubscribe_url}`/`{resubscribe_url}` lead to a page where the visitor must type an address matching the link's HMAC before anything changes [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:176-182 @7.x] [code: app/bundles/EmailBundle/Controller/PublicController.php:148-204 @7.x].
- Unsubscribe writes DNC `UNSUBSCRIBED` unless the Preference Centre is enabled (`show_contact_preferences`), in which case the frequency/channel/segment/category form is shown [code: app/bundles/EmailBundle/Controller/PublicController.php:267-352 @7.x].
- Resubscribe removes all email DNC rows (any reason) for every Contact with that address [code: app/bundles/EmailBundle/Model/EmailModel.php:1787-1801 @7.x].
- A later bounce never overrides an existing `UNSUBSCRIBED` DNC [code: app/bundles/LeadBundle/Model/DoNotContact.php:76-136 @7.x].
- Bounces come from the monitored IMAP inbox (`mautic:email:fetch`, matched by `+bounce_<hash>` Return-Path) or from a transport plugin webhook at `POST /mailer/callback`; core ships no webhook listener [code: app/bundles/EmailBundle/MonitoredEmail/Processor/Bounce.php:46-123 @7.x] [code: app/bundles/EmailBundle/Controller/PublicController.php:537-543 @7.x].
- Delivered count = `sent_count` minus failed stats minus BOUNCED DNC rows, floored at 0 [code: app/bundles/EmailBundle/Model/EmailModel.php:1056-1069 @7.x].
- A/B test: `totalWeight` (default 10%) of pending Contacts are split across variants; after `sendWinnerDelay` hours (default 24) `mautic:email:sendwinner` converts the winner to the parent and broadcasts it to the rest; it exits 1 when it is not ready yet [code: app/bundles/EmailBundle/EventListener/BroadcastSubscriber.php:57-85 @7.x] [code: app/bundles/EmailBundle/Model/AbTest/SendWinnerService.php:40-174 @7.x].
- "Send example" and "send to user" are internal sends: no stat, no tracking pixel, no trackable URLs; example subjects start with `[TEST]` [code: app/bundles/EmailBundle/Model/EmailModel.php:1584-1717 @7.x] [code: app/bundles/EmailBundle/Controller/EmailController.php:69 @7.x].
- The API ignores `sendToDnc` without `email:emails:sendtodnc`, and a PUT that omits it resets it to false [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:242-256 @7.x].

## Where it lives
| Concern | Path(s) |
|---|---|
| Entities / tables | `app/bundles/EmailBundle/Entity/Email.php` (`emails`, `email_list_xref`, `email_list_excluded`, `email_assets_xref`), `Stat.php` (`email_stats`), `Copy.php` (`email_copies`), `StatDevice.php` (`email_stats_devices`), `EmailReply.php` (`email_stat_replies`), `EmailDraft.php` (`emails_draft`) |
| Pending / eligibility | `app/bundles/EmailBundle/Entity/EmailRepository.php:183-345` (`getEmailPendingQuery`) |
| Models | `Model/EmailModel.php`, `Model/SendEmailToContact.php`, `Model/SendEmailToUser.php`, `Model/TransportCallback.php`, `Model/AbTest/SendWinnerService.php` |
| Mail building | `Helper/MailHelper.php`, `Helper/FromEmailHelper.php`, `Helper/PlainTextHelper.php`, `Helper/BotRatioHelper.php`, `Helper/MailHashHelper.php` |
| Tokens / content | `EventListener/BuilderSubscriber.php`, `EventListener/TokenSubscriber.php`, `EventListener/DateTimeTokenSubscriber.php`, `EventListener/EmailSubscriber.php` |
| Events | `app/bundles/EmailBundle/EmailEvents.php` |
| Public endpoints | `Controller/PublicController.php` (pixel, webview, unsubscribe, resubscribe, preview, `/mailer/callback`) |
| UI / API | `Controller/EmailController.php`, `Controller/AjaxController.php`, `Controller/Api/EmailApiController.php` |
| Inbox | `MonitoredEmail/` (`Fetcher`, `Mailbox`, `Processor/{Bounce,Unsubscribe,Reply,FeedbackLoop}`) |
| Commands | `Command/ProcessFetchEmailCommand.php` (`mautic:email:fetch`), `Command/SendWinnerEmailCommand.php`; `app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php` (`mautic:broadcasts:send`), `ProcessMarketingMessagesQueueCommand.php` (`mautic:messages:send`) |
| Config | `app/bundles/EmailBundle/Config/config.php:137-224`; Messenger `app/bundles/MessengerBundle/Config/config.php:7-13`; wiring `app/config/config.php:97-125` |
| Permissions | `Security/Permissions/EmailPermissions.php` (`email:emails:*`, `email:emails:sendtodnc`) |
| Tests | `app/bundles/EmailBundle/Tests/` |

Full detail: references/code-map.md.

## How to change or extend it
- Add a token: register it on `EmailEvents::EMAIL_ON_BUILD` and supply values on both `EMAIL_ON_SEND` and `EMAIL_ON_DISPLAY`; use a priority above -9999 if the token emits URLs that must be tracked, and respect `isInternalSend()` and `isDynamicContentParsing()` [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:55-110 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-tokens].
- Veto or alter a send with `EMAIL_PRE_SEND` (`enableSkip()`, `enableFatal()`, `addError()`) [code: app/bundles/EmailBundle/Helper/MailHelper.php:2091-2108 @7.x].
- A transport plugin registers a Symfony `TransportFactoryInterface`; implement `TokenTransportInterface` for batch sends, `BounceProcessorInterface`/`UnsubscriptionProcessorInterface` for inbox parsing, and subscribe to `ON_TRANSPORT_WEBHOOK` calling `TransportCallback` for bounce webhooks [code: app/bundles/EmailBundle/Mailer/Transport/TransportFactory.php:34-41 @7.x] [code: app/bundles/EmailBundle/Model/TransportCallback.php:24-84 @7.x].
- Custom A/B winner criteria: `addAbTestWinnerCriteria()` on the build event plus a `DetermineWinnerEvent` listener [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-a-b-testing].
- Adding a column to `Email` means: entity metadata + migration + `EmailType` form + API serializer groups + translations + REST docs; check that `__clone` resets it if it is per-send state [code: app/bundles/EmailBundle/Entity/Email.php:323-346 @7.x].
- Store per-email feature flags in the `settings` JSON column (`settings_<key>`) instead of new columns [code: app/bundles/EmailBundle/Entity/Email.php:1495-1525 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-settings].
- Any change to `getEmailPendingQuery` must keep the pending count, the UI send loop and `mautic:broadcasts:send` in agreement (they share the query) [code: app/bundles/EmailBundle/Model/EmailModel.php:1024-1034 @7.x].
- For 8.x compatibility subscribe by event class (`EmailSendEvent::class`, `EmailOnBuildEvent::class`, ...) and use `data-mautic-disable-tracking` (see Version notes).
- PR-derived maintainer norms are not yet available (see references/pr-history.md).

## How to test it
- Functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`; its default config uses `mailer_dsn = null://null`, `messenger_dsn_email = in-memory://default`, `messenger_dsn_hit = sync://` [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x].
- Build data with `app/bundles/EmailBundle/Tests/Functional/Fixtures/EmailFixturesHelper.php` (`createEmail`, `emulateEmailSend`, `emulateEmailRead`, `createEmailLink`, `emulateLinkClick`).
- Copy from: `Tests/Entity/PendingQueryFunctionalTest.php`, `Tests/Model/EmailModelFunctionalTest.php`, `Tests/Controller/PublicControllerFunctionalTest.php`, `Tests/Controller/EmailControllerFunctionalTest.php` (schedule + `mautic:broadcasts:send`), `Tests/Functional/EmailVariantInCampaignFunctionalTest.php`, `Tests/Helper/MailHelperTest.php` (all under `app/bundles/EmailBundle/`).
- A good regression test asserts observable rows: `email_stats` (count, `is_failed`, `is_read`), `lead_donotcontact` (reason, channel), `emails.sent_count`/`read_count`, `message_queue`, and the pending count from `/s/ajax?action=email:getEmailCountStats`.

Full detail: references/test-patterns.md.

## Version notes
- 5.0 replaced Swiftmailer and its spool with Symfony Mailer + Messenger; `mautic:emails:send` is gone and all transports share `/mailer/callback` [docs: https://docs.mautic.org/en/7.2/channels/emails.html#webhook-bounce-management] [code: app/bundles/EmailBundle/Config/config.php:99-100 @7.x].
- 5.1 added preview of A/B and translation variants [docs: https://docs.mautic.org/en/7.2/channels/emails.html#translations].
- 7.0 removed `symfony/amqp-messenger` from core dependencies and deleted the Messenger `TestHandler`, so `amqp://` DSNs are rejected until `symfony/amqp-messenger` is installed [code: UPGRADE-7.0.md:15 @7.x] [code: UPGRADE-7.0.md:53 @7.x] [code: app/bundles/MessengerBundle/Validator/DsnValidator.php:31-45 @7.x].
- 7.x deprecates the `mautic:disable-tracking` link attribute in favour of `data-mautic-disable-tracking="true"` [code: app/bundles/PageBundle/Model/TrackableModel.php:740-747 @7.x].
- The 7.x branch (after 7.2.1, unreleased; [PR #16870]) has the unsubscribe email-validation page (`validate_unsubscribe_emails`); 8.x code does not have it yet (arrives with the forward merge) [code: app/bundles/EmailBundle/Config/config.php:137-224 @7.x].
- 8.x dispatches email events by class; 20 `EmailEvents` constants are removed, and `EMAIL_ON_SEND`/`EMAIL_ON_OPEN` survive only as webhook type ids, so listeners keyed on them never fire [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/emails.html#rendering-custom-tokens].
- 8.x makes `MailHelper` `final`, removes `MailHelper::validateEmail()`, and stops honouring `mautic:disable-tracking` [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/emails.html] [docs: https://docs.mautic.org/en/8.0/channels/emails.html#tracking-links-in-emails].

Full detail: references/version-notes.md.

## Pitfalls
- "Contact was added to the Segment but never got the email": Continue sending is off and the Contact joined after `publishUp` [code: app/bundles/EmailBundle/Entity/EmailRepository.php:285-288 @7.x]. The cron docs say later Contacts are sent unless an unpublish date is set; the code does that only with Continue sending on [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-broadcasts-segment-emails-cron-job].
- `sendEmailToLists` returns zeros silently for an unpublished email or one in an unpublished Category [code: app/bundles/EmailBundle/Model/EmailModel.php:1098-1107 @7.x].
- Docs say `sendToDnc` still respects Bounced DNC; 7.2.1 code skips the whole DNC check, so bounced Contacts are sent too [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/emails.html#email-properties] [code: app/bundles/EmailBundle/Model/EmailModel.php:1399-1409 @7.x].
- The KB says transactional emails go to opted-out Contacts since 5.0; in code the campaign "transactional" type only allows re-sends, and only `sendToDnc` bypasses DNC [kb: https://kb.mautic.org/article/understand-the-difference-transactional-and-marketing-emails-in-mautic.html] [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:315-382 @7.x].
- The REST docs name the segment-send body field `listIds`; the controller reads `lists` (plus `limit`, `batch`) [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/emails.html] [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:119-123 @7.x].
- With a queue DSN, "sent" means "queued": stats exist and counters rise even if the worker later fails; nothing marks those stats failed [code: app/bundles/EmailBundle/Helper/MailHelper.php:402-414 @7.x].
- With an async `hit` DSN, opens are recorded only when `messenger:consume hit` runs, and re-processing a message is not idempotent [code: app/bundles/MessengerBundle/MessageHandler/EmailHitNotificationHandler.php:20-41 @7.x].
- Unsubscribe links in "Send example" emails do not work; they render as `.../|URL|` [docs: https://docs.mautic.org/en/7.2/channels/emails.html#unsubscribe-link-doesn-t-work].
- A default SMTP or generic Symfony API transport sends one message per Contact and has no bounce webhook; batch sending needs a transport implementing `TokenTransportInterface`, and none ships in core [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#example-api-transport-installation] [code: app/bundles/EmailBundle/Helper/MailHelper.php:453-490 @7.x].
- The `EMAIL_FAILED`/`EMAIL_RESEND` listeners exist but nothing dispatches those events in 7.x [code: app/bundles/EmailBundle/EventListener/EmailSubscriber.php:126-174 @7.x].
- Deleting an email keeps its stats with `email_id = NULL` [code: app/bundles/EmailBundle/Entity/Stat.php:144-147 @7.x]. The KB says deleting removes send statistics, which only holds for the per-email view [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html].
- 7.2 user docs spell the legacy attribute `mautic:disable:tracking`; the code checks `mautic:disable-tracking` [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tracking-links-in-emails] [code: app/bundles/PageBundle/Model/TrackableModel.php:741 @7.x].
- The devdocs transport example is Swiftmailer-era (`mautic.email_transport` tag, `/mailer/{transport}/callback`); the 7.x route is `/mailer/callback` with a Symfony transport factory [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-transports] [code: app/bundles/EmailBundle/Config/config.php:99-100 @7.x].
- The `sendWinnerDelay` limit differs: 1-24 h in the "generate A/B test" modal and 1-480 h in the variant form [code: app/bundles/EmailBundle/Form/Type/GenerateABTestType.php:87 @7.x] [code: app/bundles/EmailBundle/Form/Type/VariantType.php:87 @7.x].

## Related skills
- mautic-contacts - DNC model and reasons, frequency rules, contact merge, preferred locale.
- mautic-segments - how Segment membership (`lead_lists_leads`) is built and why a Contact is in a Segment.
- mautic-campaigns - campaign executioner, `PendingEvent`, scheduling of the email send action and decisions.
- mautic-channels - channel registration, Marketing Messages, `message_queue`, `mautic:broadcasts:send` for other channels.
- mautic-pages-and-tracking - `/r/` redirects, trackables, page hits, contact tracking cookies.
- mautic-theme-development - email themes, GrapesJS/MJML builder, `email.html.twig`.
- mautic-cron-and-queues - cron schedules, Messenger workers, failure transport.
- mautic-configuration - Email Settings, Queue Settings, `local.php` and `MAUTIC_*` env vars.
- mautic-rest-api - authentication, pagination, API conventions shared by `/api/emails`.
- mautic-testing - test base classes, fixtures, running the suite.
- mautic-troubleshooting - "emails are not sending" runbooks.
- mautic-upgrades-and-versions - full 5.x to 8.x upgrade notes.

## Reference files
- references/behaviour.md - numbered behaviour specification with the full token reference table; open for any "what should happen" question.
- references/code-map.md - entities, tables, services, events, routes, commands, parameters, permissions, tests.
- references/docs-digest.md - what docs.mautic.org, devdocs and the KB say, with URLs, procedures and doc/code discrepancies.
- references/test-patterns.md - base classes, fixtures, representative tests and skeletons for this area.
- references/version-notes.md - 4.x to 5.x mailer change, 7.x minors, and the 8.x delta for EmailBundle.
- references/pr-history.md - not yet generated; PR-derived history is added in a later pass.
