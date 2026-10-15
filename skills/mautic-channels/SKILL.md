---
name: mautic-channels
description: "Mautic's non-email channels and the channel abstraction: ChannelBundle (channel registration, preferred channels, Marketing Messages with per-contact channel fallback, the message_queue for frequency-rule deferral, mautic:messages:send), SMS / Text Messages (SmsBundle, Twilio, MMS, STOP replies, SMS tokens), web and mobile push notifications (NotificationBundle, OneSignal), Focus Items (popups, bars, modals, exit intent, /focus/{id}.js, {focus=ID}) and Social Monitoring / Tweets (MauticSocialBundle, Twitter/X). Use whenever a task mentions channels, marketing messages, channel fallback, queued messages, SMS, text messages, Twilio, push or browser notifications, OneSignal, focus items, popups, social monitoring, tweets, /api/smses, /api/notifications, /api/messages or /api/focus, or touches app/bundles/ChannelBundle/, app/bundles/SmsBundle/, app/bundles/NotificationBundle/, plugins/MauticFocusBundle/ or plugins/MauticSocialBundle/."
---
# Mautic channels: marketing messages, SMS, push, focus items, social

## Scope
A Channel is a way Mautic reaches a Contact (email, SMS, web push, mobile push, tweet, focus item); channels register
themselves with ChannelBundle so Marketing Messages, the preference centre, reports and the DNC UI can find them.
This skill covers ChannelBundle, SmsBundle, NotificationBundle, MauticFocusBundle and MauticSocialBundle. Email is out
of scope (see mautic-emails); DNC records and frequency rules as Contact data are in mautic-contacts; campaign
execution mechanics are in mautic-campaigns.

Maintenance status (7.2.1). Maintained and tested: ChannelBundle, SmsBundle with Twilio, MauticFocusBundle
[code: app/bundles/ChannelBundle/Tests/EventListener/CampaignSubscriberTest.php:157 @7.x]
[code: app/bundles/SmsBundle/Tests/Functional/SmsModelFunctionalTest.php:75 @7.x]
[code: plugins/MauticFocusBundle/Tests/Controller/FocusPublicControllerFunctionalTest.php:18-60 @7.x]. Working but
partly dead: NotificationBundle (campaign sending works; segment push, `/notification/receive`, read/click stats and the
`notification_*` parameters are dead) [code: app/bundles/NotificationBundle/Config/config.php:34-37,112-125 @7.x].
Legacy, treat as unmaintained: MauticSocialBundle (Twitter API v1.1, Instagram v1, Foursquare 2014 API, LinkedIn has
templates only) [code: plugins/MauticSocialBundle/Integration/TwitterIntegration.php:83-86 @7.x]
[code: plugins/MauticSocialBundle/Integration/InstagramIntegration.php:35-38 @7.x].

## Expected behaviour (essentials)
Channel abstraction and preference centre
- A channel exists only when a listener of `ChannelEvents::ADD_CHANNEL` calls `addChannel($name, $features)`; features are `marketing_messages`, `contact_preference` and `report` [code: app/bundles/ChannelBundle/Event/ChannelEvent.php:30-39 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/channels.html#listening-for-channel-features].
- Only `email` and `sms` are preference-centre / DNC channels (`contact_preference`); `notification`, `mobile_notification` and `tweet` are Marketing Message channels only [code: app/bundles/SmsBundle/EventListener/ChannelSubscriber.php:47 @7.x] [code: app/bundles/NotificationBundle/EventListener/ChannelSubscriber.php:33-78 @7.x].
- A channel appears only when its integration is published: `sms` needs an enabled SMS transport, push needs OneSignal (mobile also its `mobile` feature), `tweet` needs Twitter [code: app/bundles/SmsBundle/EventListener/ChannelSubscriber.php:33 @7.x] [code: app/bundles/NotificationBundle/EventListener/ChannelSubscriber.php:30-32,56-58 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#creating-a-marketing-message].
- Bulk "change channels" removes DNC from selected channels except when the reason is `UNSUBSCRIBED`, and adds a `MANUAL` DNC to every unselected preference channel [code: app/bundles/ChannelBundle/Model/ChannelActionModel.php:23-71 @7.x].

Marketing Messages (campaign action `message.send`)
- A Marketing Message holds one message per channel; on send, channels are tried in the Contact's priority order and the first success wins; lower priorities are skipped for that Contact [code: app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:114-140 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#what-are-marketing-messages].
- Priority order: paused channels last, then the preferred channel, then the channel allowing more sends per month; channels with DNC are skipped and recorded as `{failed:1, dnc:reason}` in the log metadata [code: app/bundles/LeadBundle/Entity/Lead.php:1754-1872 @7.x] [code: app/bundles/ChannelBundle/PreferenceBuilder/PreferenceBuilder.php:45-104 @7.x].
- Each channel is executed as a pseudo campaign event of the channel's `campaignAction` type (`email.send`, `sms.send_text_sms`, `notification.send_notification`, `twitter.tweet`) through the real ActionDispatcher [code: app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:152-173 @7.x].
- A channel result with `metadata['failed']` counts as failure and the next channel is tried; a Contact that no channel reached fails with `mautic.channel.message.failed` [code: app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:178-212,224-238 @7.x].
- The SMS action passes unsent Contacts (DNC, frequency-queued, no number) with plain `pass()`. The Marketing Message therefore does not fall back from SMS, although the docs promise fallback on frequency; push uses `passWithError()` and does fall back [code: app/bundles/SmsBundle/EventListener/CampaignSendSubscriber.php:84-93 @7.x] [code: app/bundles/CampaignBundle/Event/PendingEvent.php:146-156 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#what-are-marketing-messages].
- Only enabled channel rows of a message are used; on API create/update any registered channel missing from `channels` is written disabled, but PATCH without `channels` leaves them alone [code: app/bundles/ChannelBundle/Entity/MessageRepository.php:70-88 @7.x] [code: app/bundles/ChannelBundle/Controller/Api/MessageApiController.php:56-77 @7.x].

Frequency rules and the message queue
- A Contact over a channel's frequency limit is not sent; a `message_queue` row is created with `scheduled_date = now + 1 day|week|month`, a whole period regardless of when the window frees up [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:68-119 @7.x].
- The default rule (`{channel}_frequency_number`/`_time`) applies only when both are truthy and only to Contacts without a custom rule; `sms_frequency_number` defaults to 0, so it is off [code: app/bundles/LeadBundle/Entity/FrequencyRuleRepository.php:38-54,168-237 @7.x] [code: app/bundles/SmsBundle/Config/config.php:75-76 @7.x].
- `queue()` creates at most one row per (channel, channelId, Contact), whatever that row's status [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:148-150 @7.x].
- `mautic:messages:send` drains due rows (`success=0`, `attempts < max_attempts`, `scheduled_date <= now`); it must run on cron when frequency rules are used [code: app/bundles/ChannelBundle/Entity/MessageQueueRepository.php:36-64 @7.x].
- "Cancel" on a queued timeline entry only sets `status=cancelled`; the drain query ignores status, so cancelled rows are still sent when due [code: app/bundles/ChannelBundle/Controller/AjaxController.php:33-45 @7.x] [code: app/bundles/ChannelBundle/Entity/MessageQueueRepository.php:36-64 @7.x].

Broadcasts
- `mautic:broadcasts:send` only dispatches `CHANNEL_BROADCAST`; in core only Segment Emails and Segment ("list") Text Messages listen. Nothing sends segment push notifications or tweets [code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:136-162 @7.x] [code: app/bundles/SmsBundle/EventListener/BroadcastSubscriber.php:26-33 @7.x].
- A Segment SMS goes to Contacts in its published Segments who have `mobile` or `phone`, have no stat for that SMS, no `sms` DNC and no unsent `sms` queue row for any SMS. Re-runs are idempotent [code: app/bundles/SmsBundle/Broadcast/BroadcastQuery.php:25-112 @7.x].

SMS / Text Messages
- `sendSms()` filters in order: `sms` DNC → frequency queue → missing `mobile` and `phone`; each removed Contact gets a status string, not an exception [code: app/bundles/SmsBundle/Model/SmsModel.php:231-279 @7.x].
- Twilio sends to `mobile ?: phone`, parsed with default region `US` and formatted as E.164 [code: app/bundles/LeadBundle/Entity/Lead.php:1573-1576 @7.x] [code: app/bundles/SmsBundle/Integration/Twilio/TwilioTransport.php:95-101 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/sms.html#important-notes].
- A transport result of exactly `true` is a send; anything else is a failure and no `sms_message_stats` row is written for it [code: app/bundles/SmsBundle/Model/SmsModel.php:348-361 @7.x].
- Only an exact `stop` reply (case-insensitive) adds an `sms` DNC with reason `UNSUBSCRIBED`; the docs' STOPALL/UNSUBSCRIBE/CANCEL/END/QUIT are not handled by Mautic [code: app/bundles/SmsBundle/EventListener/StopSubscriber.php:25-33 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/sms.html#managing-unsubscribes].
- Inbound replies are matched to every Contact whose `mobile` or `phone` matches any format of `From`; each reply is logged and fires the `sms.reply` decision, whose pattern uses case-insensitive `fnmatch` [code: app/bundles/SmsBundle/Helper/ContactHelper.php:27-59 @7.x] [code: app/bundles/SmsBundle/EventListener/CampaignReplySubscriber.php:52-84 @7.x].
- MMS: at most 10 media, at most 5,000,000 bytes total for media hosted on Mautic. Only transports implementing `MMSTransportInterface` send media; others silently send plain SMS [code: app/bundles/SmsBundle/Form/Validator/Constraints/MediaMaxAllowedSizeValidator.php:16,38-66 @7.x] [code: app/bundles/SmsBundle/Sms/TransportChain.php:113-117 @7.x].
- URLs in SMS become tracked redirects unless `sms_disable_trackable_urls` is on; `{unsubscribe}` tokens do not exist for SMS [code: app/bundles/SmsBundle/EventListener/SmsSubscriber.php:73-113 @7.x].

Push notifications (OneSignal)
- A web push needs a web `PushID` on the Contact, created when the browser calls `/notification/subscribe?osid=` while the Contact is tracked; otherwise the log passes with `not_subscribed` [code: app/bundles/NotificationBundle/Controller/Api/NotificationApiController.php:58-71 @7.x] [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:194-217 @7.x].
- Notifications with a URL are sent one API call per Contact; those without a URL are batched by heading and message, up to 2000 player ids per call [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:131-135,287-318 @7.x].
- A non-200 OneSignal response fails the log (the campaign retries it); a 200 writes a stat and increments `sent_count` [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:260-282 @7.x].

Focus items
- `/focus/{id}.js` returns JS for a published item (404 otherwise), personalised for the tracked Contact on every request [code: plugins/MauticFocusBundle/Controller/PublicController.php:27-44 @7.x].
- Frequency is client-side via cookie `mautic_focus_{id}` (last engagement time; `-1` after conversion). `once` never shows again; `stop_after_close` uses `mautic_focus_{id}_closed` [code: plugins/MauticFocusBundle/Resources/views/Builder/generate.js.twig:324-419,492-497 @7.x].
- Views, clicks and submissions are recorded only when a tracked Contact exists. A view comes from the view pixel, a click from a `focus`-sourced redirect hit, and a submission from a form post carrying `mauticform[focusId]` [code: plugins/MauticFocusBundle/Model/FocusModel.php:277-316 @7.x] [code: plugins/MauticFocusBundle/EventListener/StatSubscriber.php:30-65 @7.x].
- The campaign action "Show focus item" works only after a "Visits a page" decision. It is delivered on the Contact's next `mtc.js` event call through a 1-day tracking cache [code: plugins/MauticFocusBundle/EventListener/CampaignSubscriber.php:33-69 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#deploying-through-a-campaign].

Social
- `mautic:social:monitoring` runs per-monitor Twitter hashtag or mention searches and creates or updates Contacts by Twitter handle; it exits 0 when no monitors are published [code: plugins/MauticSocialBundle/Command/MauticSocialMonitoringCommand.php:47-138 @7.x] [code: plugins/MauticSocialBundle/Helper/TwitterCommandHelper.php:82-285 @7.x].

## Where it lives
| Concern | Path(s) |
|---|---|
| Channel registry, Marketing Messages, queue | `app/bundles/ChannelBundle/` (`Event/ChannelEvent.php`, `Helper/ChannelListHelper.php`, `Model/MessageModel.php`, `Model/MessageQueueModel.php`, `PreferenceBuilder/`, `EventListener/CampaignSubscriber.php`) |
| Tables | `messages`, `message_channels`, `message_queue`, `sms_messages`, `sms_message_stats`, `push_notifications`, `push_notification_stats`, `push_ids`, `focus`, `focus_stats`, `monitoring`, `monitoring_leads`, `monitor_post_count`, `tweets`, `tweet_stats` |
| Commands | `mautic:broadcasts:send` (`ChannelBundle/Command/SendChannelBroadcastCommand.php`), `mautic:messages:send` (`ProcessMarketingMessagesQueueCommand.php`), `mautic:social:monitoring` (`plugins/MauticSocialBundle/Command/`) |
| SMS | `app/bundles/SmsBundle/` (`Model/SmsModel.php`, `Sms/TransportChain.php`, `Integration/Twilio/`, `Broadcast/`, `Helper/ReplyHelper.php`, `EventListener/StopSubscriber.php`) |
| Push | `app/bundles/NotificationBundle/` (`Api/OneSignalApi.php`, `Helper/NotificationHelper.php`, `EventListener/CampaignSubscriber.php`, `Integration/OneSignalIntegration.php`) |
| Focus items | `plugins/MauticFocusBundle/` (`Model/FocusModel.php`, `Controller/PublicController.php`, `Resources/views/Builder/generate.js.twig`) |
| Social | `plugins/MauticSocialBundle/` (`Integration/`, `Helper/TwitterCommandHelper.php`, `Helper/CampaignEventHelper.php`) |
| Events | `ChannelEvents`, `SmsEvents`, `NotificationEvents`, `FocusEvents`, `SocialEvents` (each bundle root) |
| Public routes | `/sms/{transport}/callback`, `/notification/subscribe`, `/notification/appcallback`, `/OneSignalSDKWorker.js`, `/manifest.json`, `/focus/{id}.js`, `/focus/{id}/viewpixel.gif` |
| Permissions | `channel:messages:*`, `sms:smses:*`, `notification:notifications:*`, `notification:mobile_notifications:*`, `focus:items:*`, `mauticSocial:monitoring:*`, `mauticSocial:tweets:*` |
| Tests | `app/bundles/{Channel,Sms,Notification}Bundle/Tests/`, `plugins/Mautic{Focus,Social}Bundle/Tests/` |
Full detail: references/code-map.md.

## How to change or extend it
- Add a channel by subscribing to `ChannelEvents::ADD_CHANNEL`. Add `LeadModel::CHANNEL_FEATURE` only if Contacts may opt out of it (it then appears in the preference centre and DNC UI) [code: app/bundles/ChannelBundle/Event/ChannelEvent.php:14-39,56-80 @7.x].
- To make a channel usable by Marketing Messages, give it a `campaignAction` that is a batch action (`PendingEvent`) and reads the message's id from its `channelIdField` property. Report success/failure per log; set `metadata['failed']` to let fallback continue [code: app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:152-212 @7.x].
- Segment sends: listen to `CHANNEL_BROADCAST`, call `checkContext()`, honour limit/batch/min/max id/thread options and call `setResults()`. Copy `app/bundles/SmsBundle/Broadcast/BroadcastExecutioner.php` [code: app/bundles/ChannelBundle/Event/ChannelBroadcastEvent.php:92-99 @7.x].
- Frequency rules for a new channel: call `MessageQueueModel::processFrequencyRules()` with your stat table, declare `{channel}_frequency_number/_time`, and drain with a `PROCESS_MESSAGE_QUEUE_BATCH` listener (template `app/bundles/SmsBundle/EventListener/MessageQueueSubscriber.php`) [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:68-119 @7.x].
- SMS provider: implement `TransportInterface` (optionally `BulkTransportInterface`, `MMSTransportInterface`), tag the service `mautic.sms_transport` with `alias` and `integrationAlias`. Inbound: implement `CallbackInterface`, tag `mautic.sms_callback_handler` [code: app/bundles/SmsBundle/DependencyInjection/Compiler/SmsTransportPass.php:20-27 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/sms.html#registering-the-transport].
- Extra reply keywords (START, HELP): listen to `SmsEvents::ON_REPLY`; do not change `StopSubscriber` semantics without a docs update [code: app/bundles/SmsBundle/Helper/ReplyHelper.php:82-89 @7.x].
- New fields on `Sms`, `Notification`, `Focus` or `Message`: update the entity metadata, add a migration, update the form type, the legacy API serializer and the API Platform groups (`Sms`, `Message`, `Channel`, `Focus`, `Monitoring` carry `#[ApiResource]`; `Notification` does not), and add translations [code: app/bundles/SmsBundle/Entity/Sms.php:37-55 @7.x] [code: plugins/MauticFocusBundle/Entity/Focus.php:26-43 @7.x].
- Code for 8.x must subscribe to event classes (`ChannelBroadcastEvent::class`, `ReplyEvent::class`, `SmsPostSaveEvent::class`, ...). Kept constants such as `ChannelEvents::ADD_CHANNEL` are no longer dispatched by name [PR #17201] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/channels.html#extending-broadcasts].
- Do not inject the deprecated `mautic.channel.helper.channel_list` alias; inject `ChannelListHelper` [code: app/bundles/ChannelBundle/Config/services.php:33-34 @7.x].

## How to test it
- Functional: extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`. Unit: `PHPUnit\Framework\TestCase`. Forms: `TypeTestCase` [code: app/bundles/SmsBundle/Tests/Functional/SmsModelFunctionalTest.php:20 @7.x].
- SMS: use `SmsTestHelperTrait`, which publishes Twilio and swaps in `Tests/ArrayTransport.php` to capture sends [code: app/bundles/SmsBundle/Tests/SmsTestHelperTrait.php:15-49 @7.x].
- Push: use `NotificationTrait`, which publishes OneSignal and exposes a Guzzle `MockHandler` [code: app/bundles/NotificationBundle/Tests/NotificationTrait.php:23-70 @7.x].
- Copy from: `ChannelBundle/Tests/EventListener/CampaignSubscriberTest.php` (fallback), `ChannelBundle/Tests/Command/ProcessMarketingMessagesQueueCommandFunctionalTest.php` (queue drain), `SmsBundle/Tests/EventListener/SendSmsSubscriberTest.php` (filters), `SmsBundle/Tests/Integration/Twilio/TwilioCallbackTest.php` (inbound), `NotificationBundle/Tests/Functional/EventListener/CampaignSubscriberTest.php` (push), `plugins/MauticFocusBundle/Tests/Controller/FocusPublicControllerFunctionalTest.php` (focus JS).
- A good regression test asserts the observable outcome: rows in `sms_message_stats` / `message_queue` / `lead_donotcontact`, the campaign log's passed/failed state and metadata, and the outgoing transport payload.
Full detail: references/test-patterns.md.

## Version notes
- 7.2 deprecated the `mautic.channel.helper.channel_list` alias [code: app/bundles/ChannelBundle/Config/services.php:33-34 @7.x].
- 8.x: channel, SMS, notification, focus and social events are dispatched by class; 10 `SmsEvents` constants are removed; `SmsEvent` becomes abstract with `SmsPre/PostSave/DeleteEvent` [PR #17216] [PR #17622] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/sms.html#sms-event-constants].
- 8.x: `/sms/receive` and `mautic_receive_notification` are removed, so point Twilio at `/sms/twilio/callback`; `NotificationHelper::unsubscribe()` is removed [code: UPGRADE-8.0.md:232,277,331 @8.x] [PR #17231].
- 8.x: Focus and Social campaign actions move to `ON_CAMPAIGN_BATCH_ACTION`; legacy `eventName`/`callback` campaign actions no longer run [PR #17097] [PR #17223] [PR #17544].
- The user docs for SMS, marketing messages, push, focus and social monitoring are unchanged between 7.2 and 8.0 [docs: https://docs.mautic.org/en/7.2/channels/sms.html].
Full detail: references/version-notes.md.

## Pitfalls
- STOP is the only keyword: STOPALL, UNSUBSCRIBE, CANCEL, END and QUIT, which the docs list, do nothing in Mautic. Twilio's own opt-out may still block delivery [code: app/bundles/SmsBundle/EventListener/StopSubscriber.php:25-33 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/sms.html#managing-unsubscribes].
- Segment push notifications cannot be sent: the web form has no Segment field and no broadcast listener exists. `notification_type='list'` is a dead value [code: app/bundles/NotificationBundle/Form/Type/NotificationType.php @7.x].
- Cancelling a queued message does not stop it, and cancelled rows still count as "queued" in `getQueuedChannelCount()` [code: app/bundles/ChannelBundle/Entity/MessageQueueRepository.php:36-97 @7.x].
- Queued SMS for Contacts without a number are marked successful and counted as sent [code: app/bundles/SmsBundle/EventListener/MessageQueueSubscriber.php:46-49 @7.x].
- Failed SMS leave no stat row, so the timeline shows no failure and a broadcast re-run retries them [code: app/bundles/SmsBundle/Model/SmsModel.php:350-353 @7.x].
- Twilio region `US` default mis-parses national-format non-US numbers. Store numbers as `+E.164` [code: app/bundles/SmsBundle/Integration/Twilio/TwilioTransport.php:98 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/sms.html#important-notes].
- `SmsBundle/Entity/StatRepository.php` queries the wrong table name `sms_messages_stats` in `getSentStats()`, and `updateLead()` updates `sms_id`, so Contact merges do not move SMS stats [code: app/bundles/SmsBundle/Entity/StatRepository.php:43,169-176 @7.x].
- The Focus "Display a notice" type is stored as `notice`, but the stats code and JS compare with `notification`. Notice items therefore get a submissions dataset and stop-after-conversion logic [code: plugins/MauticFocusBundle/Resources/views/Focus/form.html.twig:153 @7.x] [code: plugins/MauticFocusBundle/Model/FocusModel.php:373 @7.x].
- Focus frequency `once` is permanent (cookie expires in 9999), not "once per session" as the docs say [code: plugins/MauticFocusBundle/Resources/views/Builder/generate.js.twig:497,709 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#engagement-options].
- The `sms_enabled`, `sms_username`, `sms_password` and all `notification_*` parameters are unused. Configure Twilio and OneSignal in their plugin integrations [code: app/bundles/SmsBundle/Config/config.php:70-79 @7.x].
- `MessageModel::getChannels()` caches in a static property, so long-running workers miss integrations published later [code: app/bundles/ChannelBundle/Model/MessageModel.php:30,108 @7.x].
- `/notification/appcallback` is unauthenticated and creates Contacts by email [code: app/bundles/NotificationBundle/Controller/AppCallbackController.php:33-55 @7.x].
- The tweet action reads the hard-coded `twitter` field, while monitoring uses `twitter_handle_field` [code: plugins/MauticSocialBundle/Helper/CampaignEventHelper.php:45 @7.x].
- Open question: the docs say the SMS send API is `GET /smses/ID/contact/CID/send`, and the code analysis calls it POST. The route declares no method, so both work [code: app/bundles/SmsBundle/Config/config.php:42-45 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/text_messages.html#send-sms-to-contact].

## Related skills
- mautic-emails — email sending, segment emails, A/B tests, email DNC from bounces and unsubscribes.
- mautic-contacts — DNC records and reasons, frequency rules and the preference centre form, `PushID` on the Contact.
- mautic-campaigns — campaign actions and decisions, `PendingEvent`, ActionDispatcher, `mautic:campaigns:trigger`.
- mautic-pages-and-tracking — `mtc.js`, trackables and redirects, landing page tokens, `/mtc/event`.
- mautic-forms — forms embedded in focus items, the social login field.
- mautic-integrations — Twilio, OneSignal and Twitter as `AbstractIntegration` plugins, the integrations UI.
- mautic-cron-and-queues — cron schedules for `mautic:broadcasts:send`, `mautic:messages:send`, `mautic:social:monitoring`.
- mautic-rest-api — `/api/smses`, `/api/notifications`, `/api/messages`, `/api/focus`, `/api/tweets`, API Platform v2.
- mautic-plugin-development — writing transports, channels and event subscribers.
- mautic-testing — test base classes and fixtures.
- mautic-upgrades-and-versions — the 8.0 event-dispatch migration as a whole.

## Reference files
- references/behaviour.md — numbered behaviour specification per channel; open it before testing or changing behaviour.
- references/code-map.md — entities and tables, services, events, routes, commands, parameters, permissions.
- references/docs-digest.md — what docs.mautic.org and devdocs say, with URLs, procedures and terminology.
- references/test-patterns.md — base classes, helper traits, representative tests and test skeletons.
- references/version-notes.md — 5.x/6.x/7.x notes and the 8.x delta for these bundles.
- references/pr-history.md — not yet generated; PR-derived history is added in a later pass.
