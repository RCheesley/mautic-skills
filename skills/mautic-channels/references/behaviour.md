# Channels: behaviour specification (Mautic 7.x)

Authoritative for 7.x at commit 419a08a9b35. Each item is an observable rule with its source. Code wins over docs for
current behaviour; doc discrepancies are flagged with **Docs differ**.

## Contents
1. Expected behaviour: channel registration and preference centre (C1–C8)
2. Expected behaviour: frequency rules and the message queue (Q1–Q12)
3. Expected behaviour: Marketing Messages (M1–M12)
4. Expected behaviour: broadcasts command (B1–B6)
5. Expected behaviour: SMS / Text Messages (S1–S30)
6. Expected behaviour: web and mobile push notifications (N1–N17)
7. Expected behaviour: Focus Items (F1–F16)
8. Expected behaviour: Social Monitoring and Tweets (T1–T10)
9. Maintenance status: maintained vs legacy/dead
10. Open questions

Terms: **Channel** = a registered way to reach a Contact. **DNC** = a Do Not Contact record (`lead_donotcontact`) per Contact
and channel, with reason `UNSUBSCRIBED=1`, `BOUNCED=2` or `MANUAL=3` [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-32 @7.x].
**Frequency rule** = a per-Contact, per-channel cap of N messages per DAY/WEEK/MONTH, optionally with pause dates.
**Marketing Message** = one logical message with a variant per channel, sent by campaign action `message.send`.
**Focus Item** = an on-site bar/modal/notification/full-page overlay. **Segment SMS** = a `list`-type Text Message.

---

## 1. Expected behaviour: channel registration and preference centre

C1. A channel exists only if a listener of `ChannelEvents::ADD_CHANNEL` calls `ChannelEvent::addChannel($name, $config)`. `$config` is keyed by feature (`marketing_messages`, `contact_preference`, `report`) [code: app/bundles/ChannelBundle/Event/ChannelEvent.php:30-39 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/channels.html#listening-for-channel-features].

C2. `ChannelListHelper` dispatches `ADD_CHANNEL` once per request and caches `channels` and `featureChannels` [code: app/bundles/ChannelBundle/Helper/ChannelListHelper.php:102-112 @7.x]. `MessageModel::getChannels()` caches in a **static** property for the whole PHP process [code: app/bundles/ChannelBundle/Model/MessageModel.php:30,106-141 @7.x].

C3. Core registrations and listener priorities: email (100), sms (90), tweet (80), notification/mobile_notification (70), dynamicContent (0, report only) [code: app/bundles/ChannelBundle/ChannelEvents.php:16 @7.x] [code: app/bundles/DynamicContentBundle/EventListener/ChannelSubscriber.php:21-31 @7.x].

C4. Preference-centre / DNC-UI channels are exactly those with `contact_preference` (`LeadModel::CHANNEL_FEATURE`): `email` and `sms`. Push and tweet register only `marketing_messages`/`report` [code: app/bundles/EmailBundle/EventListener/ChannelSubscriber.php:46 @7.x] [code: app/bundles/SmsBundle/EventListener/ChannelSubscriber.php:47 @7.x] [code: app/bundles/NotificationBundle/EventListener/ChannelSubscriber.php:33-78 @7.x] [code: plugins/MauticSocialBundle/EventListener/ChannelSubscriber.php:32-46 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:101,2285-2288 @7.x].

C5. Conditional registration: `sms` only when an SMS transport is enabled. `notification` and `mobile_notification` only when OneSignal is published; `mobile_notification` also needs the `mobile` feature. `tweet` only when Twitter is published [code: app/bundles/SmsBundle/EventListener/ChannelSubscriber.php:33 @7.x] [code: app/bundles/NotificationBundle/EventListener/ChannelSubscriber.php:30-32,56-58 @7.x] [code: plugins/MauticSocialBundle/EventListener/ChannelSubscriber.php:30-31 @7.x].

C6. Channel labels resolve in order from `mautic.channel.{channel}`, `mautic.{channel}`, `mautic.{channel}.{channel}`, else `ucfirst(channel)` [code: app/bundles/ChannelBundle/Model/MessageModel.php:117-132 @7.x] [code: app/bundles/ChannelBundle/Helper/ChannelListHelper.php:85-92 @7.x].

C7. Bulk "change channels" (contact list button) works as follows. For each editable Contact, each selected channel with a DNC loses that DNC, **unless** the reason is `UNSUBSCRIBED`. Each unselected preference channel gets a DNC with reason `MANUAL` and comment `mautic.lead.event.donotcontact_manual`. Contacts the user cannot edit are skipped [code: app/bundles/ChannelBundle/Model/ChannelActionModel.php:23-71 @7.x] [code: app/bundles/ChannelBundle/Tests/Model/ChannelActionModelTest.php:83-200 @7.x].

C8. Bulk "set frequency" creates or updates a `FrequencyRule` for every preference channel. Number and time are set only when both `frequency_number_{ch}` and `frequency_time_{ch}` are non-empty, otherwise both are nulled. Pause dates are parsed with `new \DateTime()`. The preferred channel defaults to the first channel, and exactly one rule gets `preferred_channel = true` [code: app/bundles/ChannelBundle/Model/FrequencyActionModel.php:39-79 @7.x] [code: app/bundles/ChannelBundle/Tests/Model/FrequencyActionModelTest.php:88 @7.x].

## 2. Expected behaviour: frequency rules and the message queue

Q1. Custom rule: a Contact violates when the count of that channel's stats in the last 1 DAY/WEEK/MONTH is `>= frequency_number` [code: app/bundles/LeadBundle/Entity/FrequencyRuleRepository.php:122-162 @7.x].

Q2. Default rule: applies only when `{channel}_frequency_number` and `{channel}_frequency_time` are both truthy, and only to Contacts **without** any custom rule. It counts stats since `-1 day|week|month` UTC [code: app/bundles/LeadBundle/Entity/FrequencyRuleRepository.php:38-54,168-237 @7.x]. Defaults: `email_frequency_number=0` and `sms_frequency_number=0`, both with time `DAY`, so off [code: app/bundles/EmailBundle/Config/config.php:200-201 @7.x] [code: app/bundles/SmsBundle/Config/config.php:75-76 @7.x].

Q3. `processFrequencyRules()` removes violating Contacts from the send. It either reschedules their existing queue row (when `resend_message_queue` is passed) or queues a new row. The new row has `scheduledDate = now + P1D|P1W|P1M` (first letter of `frequency_time`), the given `maxAttempts` (3 for SMS) and priority, and the campaign event id [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:68-119 @7.x] [code: app/bundles/ChannelBundle/Tests/Model/MessageQueueModelTest.php:82-116 @7.x].

Q4. The deferral is a whole period from now, not until the window frees up [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:99 @7.x].

Q5. `queue()` is idempotent per (channel, channelId, Contact). If any `message_queue` row exists for the triple, whatever its status, no row is added. New rows get `date_published = now`, `scheduled_date = now + interval` and are detached after save [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:148-173 @7.x] [code: app/bundles/ChannelBundle/Entity/MessageQueueRepository.php:18-31 @7.x].

Q6. Row defaults: priority 2 (`PRIORITY_NORMAL`; `PRIORITY_HIGH = 1`), maxAttempts 3, attempts 0, success false, status `pending` [code: app/bundles/ChannelBundle/Entity/MessageQueue.php:14-24,51-71 @7.x].

Q7. Selection for sending: `success = 0`, `attempts < max_attempts`, `last_attempt IS NULL OR < processStarted`, and `scheduled_date <= processStarted`. Rows are ordered by `priority, scheduled_date` and limited to the batch size. **Status is not part of the filter** [code: app/bundles/ChannelBundle/Entity/MessageQueueRepository.php:36-64 @7.x].

Q8. `processMessageQueue()` hydrates Contact fields in one query and drops rows already `sent`. It dispatches one `PROCESS_MESSAGE_QUEUE_BATCH` per (channel, channelId) group, then `PROCESS_MESSAGE_QUEUE` for rows no batch listener marked processed. Rows marked success get `status = sent` and `date_sent = last_attempt = now` and count as sent. Rows marked failed are rescheduled by `PT15M`. Other rows are assumed handled. All rows are saved [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:197-283 @7.x].

Q9. `reschedule()` increments `attempts`, sets `last_attempt = now`, adds the interval to the **previous scheduled date** and sets status `rescheduled` [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:288-313 @7.x].

Q10. Saving a queue row dispatches `ChannelEvents::MESSAGE_QUEUED` instead of a generic post-save event. Nothing in core listens [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:325-352 @7.x].

Q11. Queued messages show in the Contact timeline as `message.queue`. The cancel button (`channel:cancelQueuedMessageEvent`) only sets `status = cancelled`, and because of Q7 a cancelled row is still sent when due [code: app/bundles/ChannelBundle/EventListener/LeadSubscriber.php:31-75 @7.x] [code: app/bundles/ChannelBundle/Controller/AjaxController.php:33-45 @7.x]. `getQueuedChannelCount()` counts `status != 'sent'`, which includes cancelled rows [code: app/bundles/ChannelBundle/Entity/MessageQueueRepository.php:66-97 @7.x].

Q12. `mautic:messages:send` (aliases `mautic:campaigns:messagequeue`, `mautic:campaigns:messages`) loops `sendMessages()` in batches (default 50) until a batch returns 0 or `--limit` is reached. `--message-id` processes one row. It prints `Messages sent: N` and always exits 0. With 60 queued emails it reports 60; with `--limit 2` and three rows it reports 2 [code: app/bundles/ChannelBundle/Command/ProcessMarketingMessagesQueueCommand.php:38-98 @7.x] [code: app/bundles/ChannelBundle/Tests/Command/ProcessMarketingMessagesQueueCommandFunctionalTest.php:25-86 @7.x].

## 3. Expected behaviour: Marketing Messages

M1. A Marketing Message holds one message across channels (Email, SMS, browser and mobile notification, tweet, custom) and is sent by the campaign action "Send Marketing Message" [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#what-are-marketing-messages].

M2. The form always holds one `Channel` row per registered `marketing_messages` channel; missing ones are added disabled. The `channelId` is required only when the channel is enabled, and the properties sub-form is not validated when it is disabled [code: app/bundles/ChannelBundle/Form/Type/MessageType.php:31-45 @7.x] [code: app/bundles/ChannelBundle/Form/Type/ChannelType.php:60-91 @7.x].

M3. `message_channels` has a unique `(message_id, channel)` index, and `setChannelId('')` stores `null` [code: app/bundles/ChannelBundle/Entity/Channel.php:92-95,176-185 @7.x].

M4. Legacy API `/api/messages`: on create/update, registered channels absent from `channels` are stored `isEnabled => 0`. `PATCH` without `channels` leaves channels untouched. Serialization adds each channel's `channelName` [code: app/bundles/ChannelBundle/Controller/Api/MessageApiController.php:56-92 @7.x]. The devdocs page for this API is a stub [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/messages.html].

M5. Only enabled channel rows are used when sending, and lookups list only published messages [code: app/bundles/ChannelBundle/Entity/MessageRepository.php:44-88 @7.x].

M6. `message.send` can follow only decisions that some channel supports: email adds `email.open`, and every channel supports `page.pagehit`, `asset.download` and `form.submit` [code: app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:55-75 @7.x] [code: app/bundles/SmsBundle/EventListener/ChannelSubscriber.php:39-43 @7.x].

M7. Per-Contact order: `PreferenceBuilder` walks `Lead::getChannelRules()` and assigns priorities 1, 2, …, then appends the message's remaining channels at lower priorities. Channels where the Contact has DNC are skipped and `{channel: {failed: 1, dnc: reason}}` is added to the log metadata [code: app/bundles/ChannelBundle/PreferenceBuilder/PreferenceBuilder.php:45-104 @7.x] [code: app/bundles/ChannelBundle/Tests/PreferenceBuilder/PreferenceBuilderTest.php:18-101 @7.x].

M8. `Lead::getChannelRules()` sorts paused rules (now between pause dates) last, then `preferred_channel` first. Among equals, the channel allowing more sends per month comes first (DAY×30, WEEK×4, MONTH×1). DNC channels are appended after all contactable ones [code: app/bundles/LeadBundle/Entity/Lead.php:1754-1872 @7.x].

M9. **Docs differ:** the docs say that with no preference the default channel is Email, and that an exceeded frequency limit moves the send to another channel [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#what-are-marketing-messages]. In code, the order comes from M7/M8. Fallback happens only when a channel's action marks the log with `metadata['failed']`, which `PendingEvent::passWithError()` does [code: app/bundles/CampaignBundle/Event/PendingEvent.php:146-156 @7.x] [code: app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:178-212 @7.x]. The SMS action uses plain `pass()` for every Contact in the send result. An SMS that is DNC-filtered, frequency-queued or missing a number therefore counts as a success, and the Marketing Message does **not** fall back to the next channel [code: app/bundles/SmsBundle/EventListener/CampaignSendSubscriber.php:84-93 @7.x]. Push errors (DNC, not subscribed) use pass-with-error, so they do fall back (N8, N9).

M10. Execution: for each priority, per channel, the subscriber dispatches a pseudo campaign event of type `campaignAction`. It carries the channel's stored properties plus `properties[channelIdField] = channel_id` and runs through the real `ActionDispatcher` with channel `campaign.event`. Channels without `campaignAction` are skipped [code: app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:114-134,152-173 @7.x].

M11. Contacts sent successfully are removed from lower priorities, and the marketing-message log is passed with per-channel metadata copied under the channel key. A result with `metadata['failed']` is a pseudo-failure, so the next channel is tried. Contacts no channel reached fail with `mautic.channel.message.failed` [code: app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:131,136-140,178-238 @7.x] [code: app/bundles/ChannelBundle/Tests/EventListener/CampaignSubscriberTest.php:157-200 @7.x].

M12. The detail page charts `message.send` campaign logs (channel `channel.message`) per actual channel. Save and delete write audit log `bundle=channel, object=message` [code: app/bundles/ChannelBundle/Model/MessageModel.php:180-194 @7.x] [code: app/bundles/ChannelBundle/EventListener/MessageSubscriber.php:30-59 @7.x].

## 4. Expected behaviour: broadcasts command

B1. `mautic:broadcasts:send` options: `--channel/-c`, `--id/-i`, `--min-contact-id`, `--max-contact-id`, `--limit/-l` (default 100), `--batch/-b` (default 50), `--thread-id` and `--max-threads`. The command is a `ModeratedCommand` with lock key `{channel}-{id}-{threadId}-{maxThreads}` [code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:47-98 @7.x] [code: app/bundles/ChannelBundle/Event/ChannelBroadcastEvent.php:34,39 @7.x].

B2. `--thread-id > --max-threads` returns FAILURE. Otherwise the command dispatches `CHANNEL_BROADCAST`, prints a success/failed table per label and always returns SUCCESS, including when there is nothing to send [code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:124-183 @7.x] [code: app/bundles/ChannelBundle/Tests/Command/SendChannelBroadcastCommandTest.php:11-22 @7.x].

B3. Listeners: Email (Segment Emails, A/B) and SMS (Segment SMS) only. No listener exists for push, tweets or focus items. `--channel` filters through `checkContext()` [code: app/bundles/EmailBundle/EventListener/BroadcastSubscriber.php:32-36 @7.x] [code: app/bundles/SmsBundle/EventListener/BroadcastSubscriber.php:26-33 @7.x] [code: app/bundles/ChannelBundle/Event/ChannelBroadcastEvent.php:92-99 @7.x].

B4. The A/B winner sender also dispatches `CHANNEL_BROADCAST` [code: app/bundles/EmailBundle/Model/AbTest/SendWinnerService.php:173 @7.x].

B5. The docs require the "Send Scheduled Broadcasts" cron job for Segment Text Messages [docs: https://docs.mautic.org/en/7.2/channels/sms.html#segment-text-messages]. No frequency is suggested in the repository (see mautic-cron-and-queues).

B6. **Docs differ:** the 7.2 devdocs prose names `CoreEvents::CHANNEL_BROADCAST`, but the event is `ChannelEvents::CHANNEL_BROADCAST`, which the devdocs example also uses [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/channels.html#extending-broadcasts] [code: app/bundles/ChannelBundle/ChannelEvents.php:25 @7.x].

## 5. Expected behaviour: SMS / Text Messages

Types and editing
S1. Template Text Messages (`sms_type = template`) are sent by Campaigns, Forms and Point Triggers. Segment Text Messages (`list`) go to Segments, each Contact once, and keep going to new Segment members [docs: https://docs.mautic.org/en/7.2/channels/sms.html#template-text-messages] [docs: https://docs.mautic.org/en/7.2/channels/sms.html#segment-text-messages].

S2. A `list` SMS requires at least one Segment the user can access. `media` holds at most 10 entries [code: app/bundles/SmsBundle/Entity/Sms.php:227-260 @7.x].

S3. Creating an SMS from the campaign builder forces `smsType = template`. Saving with `isMms` false clears `media` [code: app/bundles/SmsBundle/Controller/SmsController.php:281-283,295-297 @7.x].

S4. Translations are supported (`TranslationEntityTrait`), and an SMS cannot be its own translation parent. A/B variants are not supported: `VariantEntityTrait` is present but no variant metadata is mapped [code: app/bundles/SmsBundle/Entity/Sms.php:65,219,416 @7.x] [code: app/bundles/SmsBundle/Tests/Functional/SmsControllerFunctionalTest.php:16-140 @7.x].

S5. The campaign-builder lookup groups SMS by language and prefixes MMS with `[MMS]` [code: app/bundles/SmsBundle/Model/SmsModel.php:542-570 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/sms.html#sending-multimedia-messages-mms].

Send pipeline (`SmsModel::sendSms`)
S6. The pipeline accepts a Contact, an id or arrays of either. An unpublished SMS gives every Contact `sent=false` with status `mautic.sms.campaign.failed.unpublished` [code: app/bundles/SmsBundle/Model/SmsModel.php:196-229 @7.x].

S7. Filter 1, `DNC_FILTER_CONTACTS_ON_SEND`: Contacts with any `sms` DNC are removed with status `mautic.sms.campaign.failed.not_contactable` [code: app/bundles/SmsBundle/Model/SmsModel.php:231-246 @7.x] [code: app/bundles/SmsBundle/EventListener/SendSmsSubscriber.php:37-46 @7.x].

S8. Filter 2, `QUEUE_FILTER_CONTACTS_ON_SEND`: frequency violators are queued (channel `sms`, channelId = SMS id, maxAttempts 3, normal priority, stat table `sms_message_stats`) with status `mautic.sms.timeline.status.scheduled` [code: app/bundles/SmsBundle/Model/SmsModel.php:248-263 @7.x] [code: app/bundles/SmsBundle/EventListener/SendSmsSubscriber.php:48-68 @7.x].

S9. Filter 3, `FILTER_CONTACTS_ON_SEND`: Contacts with neither `mobile` nor `phone` are removed with `mautic.sms.campaign.failed.missing_number` [code: app/bundles/SmsBundle/Model/SmsModel.php:265-279 @7.x] [code: app/bundles/SmsBundle/EventListener/SendSmsSubscriber.php:70-75 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/sms.html#contact-filtering-events].

S10. For each remaining Contact: the locale's translation is chosen and an unpersisted `Stat` with a unique `tracking_hash` is created. `SMS_ON_SEND` lets listeners change content and feeds the `mautic.sms_on_send` webhook. `TOKEN_REPLACEMENT` runs with clickthrough `{channel: [sms, id], stat: hash}`. Recipients are grouped per translated SMS, giving one batch per language [code: app/bundles/SmsBundle/Model/SmsModel.php:288-317 @7.x] [code: app/bundles/SmsBundle/EventListener/WebhookSubscriber.php:32-53 @7.x] [code: app/bundles/SmsBundle/Tests/Functional/SmsModelFunctionalTest.php:20-130 @7.x].

S11. Tokens: `{contactfield=alias}`, `{pagelink=}`, `{assetlink=}` and owner tokens. URLs become tracked redirects, shortened when `shortener_sms_enable` is on, unless `sms_disable_trackable_urls` is on. There is no `{unsubscribe}` for SMS [code: app/bundles/SmsBundle/EventListener/SmsSubscriber.php:73-113 @7.x] [code: app/bundles/SmsBundle/Controller/AjaxController.php:81-115 @7.x] [code: app/bundles/LeadBundle/EventListener/OwnerSubscriber.php:39 @7.x].

S12. A batch with media goes through `sendMMS()`, otherwise through `sendBatchSms()`. A bulk-capable primary transport gets one call; others are looped per recipient. With no enabled primary transport a warning is logged and partial results are returned [code: app/bundles/SmsBundle/Model/SmsModel.php:322-338 @7.x] [code: app/bundles/SmsBundle/Sms/TransportChain.php:76-117 @7.x].

S13. A result of exactly `true` is a send: `sent_count` is incremented and the stat persisted. Any other result (false or an error string) becomes the status and **no stat row is written** [code: app/bundles/SmsBundle/Model/SmsModel.php:348-378 @7.x].

Twilio
S14. The number is `mobile ?: phone`, parsed with region `US` and formatted E.164. The payload is `messagingServiceSid`, `body` and optional `mediaUrl`. Parse, configuration and API errors are logged and returned as strings; a null number returns `false` [code: app/bundles/SmsBundle/Integration/Twilio/TwilioTransport.php:49-120 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:1573-1576 @7.x].

S15. Configuration needs the integration published, the `username` (Account SID) and `password` (Auth Token) keys, and the feature setting `messaging_service_sid`; otherwise `ConfigurationException` [code: app/bundles/SmsBundle/Integration/Twilio/Configuration.php:71-95 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/twilio.html#mautic-twilio-plugin].

S16. The Twilio integration form shows `frequency_number`/`frequency_time` fields that no code reads. The docs tell users to "configure global frequency rules for the SMS channel" there [code: app/bundles/SmsBundle/Integration/TwilioIntegration.php:68-92 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/twilio.html#mautic-twilio-plugin].

S17. MMS limits: media hosted on Mautic must total ≤ 5,000,000 bytes (external URLs are not counted), with at most 10 entries. Docs: `.gif/.png/.jpg/.jpeg`, MMS only to US/CA/AU numbers, elsewhere the image is sent as a link (Twilio behaviour) [code: app/bundles/SmsBundle/Form/Validator/Constraints/MediaMaxAllowedSizeValidator.php:16,38-66 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/sms.html#sending-multimedia-messages-mms] [docs: https://docs.mautic.org/en/7.2/plugins/twilio.html#enabling-multimedia-messaging-mms].

S18. Transports without `MMSTransportInterface` send plain SMS when media is present, without an error [code: app/bundles/SmsBundle/Sms/TransportChain.php:113-117 @7.x].

Campaign, API, broadcast, queue
S19. Campaign action `sms.send_text_sms` is offered only when a transport is enabled. A missing SMS passes all logs with `failed.missing_entity`, and an unpublished one with `failed.unpublished`. Otherwise every Contact in the results is **passed** with plain `pass()`, even when `sent === false`, and the whole result array (all Contacts) is appended to each log's metadata. Contacts absent from the results fail [code: app/bundles/SmsBundle/EventListener/CampaignSendSubscriber.php:33-93 @7.x] [code: app/bundles/SmsBundle/Tests/EventListener/CampaignSendSubscriberTest.php:39-160 @7.x].

S20. API `/api/smses/{id}/contact/{contactId}/send`: the route declares no HTTP method, so GET (documented) and POST both work. No transport gives a JSON error with code 417 and HTTP 200; a missing SMS gives 404; no edit access to the Contact gives 403. Otherwise the endpoint sends with channel `api` and returns 200 with `success`, `status`, `result` and `errors` [code: app/bundles/SmsBundle/Config/config.php:42-45 @7.x] [code: app/bundles/SmsBundle/Controller/Api/SmsApiController.php:66-111 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/text_messages.html#send-sms-to-contact].

S21. Segment SMS pending set: DISTINCT Contacts in the SMS's published Segments (not manually removed) whose `mobile` or `phone` is not NULL. Each check is `IS NOT NULL OR <> ''`, so an empty string still passes; a Contact with `mobile = ''` is selected [code: app/bundles/SmsBundle/Broadcast/BroadcastQuery.php:47-58 @7.x]. Excluded are Contacts with a stat for this SMS, any `sms` DNC, or any non-sent `sms` queue row for **any** SMS [code: app/bundles/SmsBundle/Broadcast/BroadcastQuery.php:25-112 @7.x].

S22. Broadcast sends only published-by-date `list` SMS (`--id` limits to one), Contact by Contact in `ContactLimiter` batches. An exception aborts that SMS silently, and the counts are reported as `SMS: {name}` [code: app/bundles/SmsBundle/Entity/SmsRepository.php:41-63 @7.x] [code: app/bundles/SmsBundle/Broadcast/BroadcastExecutioner.php:28-79 @7.x].

S23. The pending count in the list is computed by AJAX `sms:getSmsCountStats` and cached under `sms|{id}|pending` [code: app/bundles/SmsBundle/Controller/AjaxController.php:36-79 @7.x].

S24. Queue replay (channel `sms`): a missing or unpublished SMS marks the row failed (retry in 15 min). A Contact without a number is marked **processed and successful**. Other rows are re-sent with `resend_message_queue` [code: app/bundles/SmsBundle/EventListener/MessageQueueSubscriber.php:28-73 @7.x].

Inbound and STOP
S25. `/sms/{transport}/callback` (GET or POST) resolves the callback handler by `getTransportName()`, or returns 404. It marks the request non-trackable and delegates to `ReplyHelper`. `/sms/receive` is a deprecated Twilio alias [code: app/bundles/SmsBundle/Controller/ReplyController.php:24-35 @7.x] [code: app/bundles/SmsBundle/Config/config.php:22-33 @7.x]. The docs set Request, Fallback and Delivery Status URLs to `/sms/twilio/callback` [docs: https://docs.mautic.org/en/7.2/plugins/twilio.html#mautic-twilio-plugin].

S26. Twilio validation: an unpublished or unconfigured integration gives an empty 404. `AccountSid` must match, and `From` and the trimmed `Body` must be non-empty, else 400 `invalid request` [code: app/bundles/SmsBundle/Integration/Twilio/TwilioCallback.php:50-75 @7.x] [code: app/bundles/SmsBundle/Tests/Integration/Twilio/TwilioCallbackTest.php:28-90 @7.x]. Delivery-status callbacks carry no `Body`, so they are rejected with 400 (inferred from the same rule).

S27. Matching: every Contact whose `mobile` or `phone` equals any format of `From` is processed. No match returns 200 [code: app/bundles/SmsBundle/Helper/ContactHelper.php:27-59 @7.x] [code: app/bundles/SmsBundle/Helper/ReplyHelper.php:53-77 @7.x].

S28. Per Contact, `ON_REPLY` is dispatched with the trimmed message, and the last listener that sets a `Response` wins [code: app/bundles/SmsBundle/Helper/ReplyHelper.php:53-89 @7.x].

S29. STOP: only a reply that lower-cases to exactly `stop` adds DNC `sms`/`UNSUBSCRIBED`. **Docs differ:** they list STOP, STOPALL, UNSUBSCRIBE, CANCEL, END and QUIT [code: app/bundles/SmsBundle/EventListener/StopSubscriber.php:25-33 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/sms.html#managing-unsubscribes].

S30. Each reply is written to `lead_event_log` (`sms`/`reply`) and appears in the timeline. It triggers decision `sms.reply`, which matches when the pattern is empty or matches through case-insensitive `fnmatch`, whether or not an SMS was sent first [code: app/bundles/SmsBundle/EventListener/ReplySubscriber.php:36-70 @7.x] [code: app/bundles/SmsBundle/EventListener/CampaignReplySubscriber.php:52-84 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/sms.html#working-with-replies-to-text-messages].

## 6. Expected behaviour: web and mobile push notifications

N1. Setup: create a OneSignal app, upload the SDK files so that `/OneSignalSDKWorker.js` is reachable, enter the keys and choose features [docs: https://docs.mautic.org/en/7.2/channels/web_notifications.html#configuration]. Mautic itself serves `/OneSignalSDKWorker.js` and `/OneSignalSDKUpdaterWorker.js` (`importScripts` of the OneSignal CDN, `Service-Worker-Allowed: /`) and `/manifest.json` [code: app/bundles/NotificationBundle/Controller/JsController.php:14-54 @7.x].

N2. Live configuration is the OneSignal integration: keys `app_id`, `safari_web_id`, `rest_api_key`, `gcm_sender_id`; features `mobile`, `landing_page_enabled`, `welcome_notification_enabled`, `tracking_page_enabled`; settings `subdomain_name`, `platforms`. The `notification_*` parameters are unused [code: app/bundles/NotificationBundle/Integration/OneSignalIntegration.php:25-101 @7.x].

N3. The OneSignal JS is added to `mtc.js` only in the tracking build scope and when OneSignal is published. It has `autoRegister: true`, optional welcome-notification disable, and the HTTP-subdomain flow for non-HTTPS referrers [code: app/bundles/NotificationBundle/EventListener/BuildJsSubscriber.php:32-101 @7.x] [code: app/bundles/NotificationBundle/Helper/NotificationHelper.php:46-165 @7.x].

N4. The script is skipped when cookie `mtc_osid` exists, on landing pages without `landing_page_enabled`, and on tracked external pages without `tracking_page_enabled` [code: app/bundles/NotificationBundle/Helper/NotificationHelper.php:167-196 @7.x] [code: app/bundles/NotificationBundle/EventListener/PageSubscriber.php:26-38 @7.x].

N5. Web subscription: the browser calls `GET /notification/subscribe?osid=…` (CORS `*`). The id is stored as a web `PushID` (enabled, mobile=false) on the currently tracked Contact. Without a tracked Contact it is acknowledged but not stored. A duplicate with the same `enabled` flag is a no-op [code: app/bundles/NotificationBundle/Controller/Api/NotificationApiController.php:58-71 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:1016-1041 @7.x].

N6. Mobile apps `POST /notification/appcallback` with `{email, push_id, enabled, stat?}`. The Contact is found or created by email, the push id stored with `mobile = true`, and a stat optionally recorded. The route has no authentication [code: app/bundles/NotificationBundle/Controller/AppCallbackController.php:33-74 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/push_notifications.html#notification-statistics].

N7. Campaign actions: `notification.send_notification` (when OneSignal is published) and `notification.send_mobile_notification` (with the `mobile` feature), both batch actions. Condition `notification.has.active` checks for an enabled PushID [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:65-106 @7.x] [code: app/bundles/NotificationBundle/EventListener/CampaignConditionSubscriber.php:34-51 @7.x].

N8. A missing or unpublished notification passes all logs with an error. A `notification` DNC passes the log with `failed.not_contactable` (web and mobile share the DNC channel `notification`) [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:117-127,180-189 @7.x].

N9. Push ids are filtered to mobile ids for the mobile action and web ids for the web action; with none, the log passes with `failed.not_subscribed`. `PushID.enabled` is not checked when sending [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:194-217 @7.x].

N10. Content: the locale translation is used, `TOKEN_REPLACEMENT` runs with channel `notification`, and `NOTIFICATION_ON_SEND` may change message and heading. The `url` becomes a tracked redirect with UTM tags [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:219-258 @7.x] [code: app/bundles/NotificationBundle/EventListener/NotificationSubscriber.php:72-109 @7.x].

N11. Batching: with a URL, one request per Contact; without a URL, grouping by `md5(heading+message)` with up to 2000 player ids per request [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:44,131-135,157-178,287-318 @7.x] [code: app/bundles/NotificationBundle/Tests/Functional/EventListener/CampaignSubscriberTest.php:422-470 @7.x].

N12. Response handling: non-200 fails the log with body and status, and the campaign retries. A 200 writes `push_notification_stats` (source `campaign.event`), increments `sent_count` and passes the log with `{status: delivered, …}` [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:260-282 @7.x].

N13. Payload to `https://onesignal.com/api/v1/notifications` with `Authorization: Basic {rest_api_key}`: `include_player_ids`, `contents.en`, `headings.en` and optional `url`. Mobile adds iOS/Android settings and `buttons`. Web adds `web_buttons` only when both button text and URL exist. A missing key throws `MissingApiKeyException` / `MissingAppIDException` [code: app/bundles/NotificationBundle/Api/OneSignalApi.php:16-168 @7.x].

N14. Segment (`list`) notifications cannot be created in the web form or sent, because no broadcast listener exists. The REST API documents no Segment field either [code: app/bundles/NotificationBundle/Form/Type/NotificationType.php @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/notifications.html#create-notification].

N15. `read_count`, `date_read`, `is_clicked` and `retry_count` are never written, so read and click stats stay empty [code: app/bundles/NotificationBundle/Entity/Stat.php:126-166 @7.x].

N16. `/notification/receive` routes to a controller method that does not exist and errors [code: app/bundles/NotificationBundle/Config/config.php:34-37 @7.x].

N17. The menu shows web notifications when OneSignal is enabled, and mobile notifications only with the `mobile` feature as well [code: app/bundles/NotificationBundle/Config/config.php:77-105 @7.x].

## 7. Expected behaviour: Focus Items

F1. Types: `form` (Collect Data; conversion = submission), `notice` (Display a Notice; no conversion) and `link` (Emphasize a link; conversion = click). Styles: `bar`, `modal`, `notification`, `page`. Type and style are required [code: plugins/MauticFocusBundle/Entity/Focus.php:145-166 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#types-of-focus-item].

F2. Bar options: `allow_hide`, `push_page`, `sticky`, placement, and size `large`/`regular` only. Modal, notification and page have placement options [code: plugins/MauticFocusBundle/Form/Type/FocusPropertiesType.php:25-120 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#styles].

F3. Engagement properties: `when` ∈ immediately, scroll_slight, scroll_middle, scroll_bottom, leave; `timeout` in seconds; `frequency` ∈ everypage, once, q2min, q15min, hourly, daily; `stop_after_conversion` (default on), `stop_after_close` (default off), `animate` (default on) [code: plugins/MauticFocusBundle/Form/Type/PropertiesType.php:57-175 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#engagement-options].

F4. Content modes `basic`, `editor` and `html`. In basic mode a form renders only for type `form` [code: plugins/MauticFocusBundle/Form/Type/FocusType.php:76-124 @7.x] [code: plugins/MauticFocusBundle/Model/FocusModel.php:186 @7.x].

F5. `GET /focus/{id}.js` returns minified `application/javascript` for a published item, generated per request for the tracked Contact. Unpublished or missing items get an empty 404. The request is not tracked [code: plugins/MauticFocusBundle/Controller/PublicController.php:27-44 @7.x] [code: plugins/MauticFocusBundle/Model/FocusModel.php:134-176 @7.x].

F6. Triggers in the browser: `immediately` waits `timeout`; scroll triggers fire at 10px, half page or the bottom; `leave` uses `mouseleave` on the document [code: plugins/MauticFocusBundle/Resources/views/Builder/generate.js.twig:200-271,616-641 @7.x].

F7. Frequency: cookie `mautic_focus_{id}` stores the last engagement time and never expires. `once` never shows again; q2min = 120 s, q15min = 900 s, hourly = 3600 s, daily = 86400 s. **Docs differ:** they call `once` "Once per session" [code: plugins/MauticFocusBundle/Resources/views/Builder/generate.js.twig:324-412,492-497,709 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#engagement-options].

F8. A conversion sets the cookie to `-1`. With `stop_after_conversion` the item is never shown again, except that the check is skipped for type `notification`. Because the notice type is stored as `notice`, the skip never applies (see F14). `stop_after_close` checks cookie `mautic_focus_{id}_closed` [code: plugins/MauticFocusBundle/Resources/views/Builder/generate.js.twig:54-55,335-340,414-419,644-683 @7.x].

F9. Views are recorded only by `/focus/{id}/viewpixel.gif` with a published item **and** a tracked Contact. The view writes a `focus_stats` row of type `view` and dispatches `FOCUS_ON_VIEW` [code: plugins/MauticFocusBundle/Controller/PublicController.php:46-65 @7.x].

F10. Clicks come from page hits with source `focus` (the trackable for `link` items) and are recorded as type `click` with the hit id. Submissions need `mauticform[focusId]` and the item's current form, and are recorded as `submission`. All stats need a Contact [code: plugins/MauticFocusBundle/EventListener/StatSubscriber.php:30-65 @7.x] [code: plugins/MauticFocusBundle/Model/FocusModel.php:279-285,419-436 @7.x].

F11. Embedding uses a snippet. The site domain must be allowed in CORS settings, and the builder preview needs SSL without `X-Frame-Options: SAMEORIGIN` [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#deploying-to-a-website] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#using-the-focus-item-builder]. A landing page `{focus=ID}` becomes an async script tag when the item is published or viewable by the user, else an empty string [code: plugins/MauticFocusBundle/EventListener/PageSubscriber.php:55-84 @7.x]. A form-generator request for `mf-{focusId}` is redirected to the focus JS [code: plugins/MauticFocusBundle/EventListener/FocusSubscriber.php:55-74 @7.x].

F12. Campaign action `focus.show` attaches only to the inaction branch of `page.pagehit`. It stores the item in a 1-day per-Contact tracking cache that the next `/mtc/event` call returns and clears. The docs call this route "sometimes unreliable" [code: plugins/MauticFocusBundle/EventListener/CampaignSubscriber.php:33-69 @7.x] [code: app/bundles/PageBundle/Helper/TrackingHelper.php:42-90 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#deploying-through-a-campaign].

F13. Stats chart: views always, clicks for `link`, submissions otherwise. Counts are cached (tag `focus.{id}`) for `cached_data_timeout` minutes [code: plugins/MauticFocusBundle/Model/FocusModel.php:361-417 @7.x] [code: plugins/MauticFocusBundle/Controller/AjaxController.php:42-121 @7.x].

F14. Known defect: the notice type is stored as `notice`, but the stats and JS compare against `notification`, so notice items get a submissions series and conversion logic [code: plugins/MauticFocusBundle/Resources/views/Focus/form.html.twig:153 @7.x] [code: plugins/MauticFocusBundle/Model/FocusModel.php:373 @7.x].

F15. Deleting a form nulls `form_id` on the items that use it (`form_id` is not a foreign key). Form fields are pre-filled from the tracked Contact. UTM tags are appended to links and submissions [code: plugins/MauticFocusBundle/EventListener/FormSubscriber.php:29-46 @7.x] [code: plugins/MauticFocusBundle/Tests/Functional/Model/FocusFormAutoFillTest.php:28 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#measuring-success].

F16. `website_snapshot_url`/`_key` are unused; the builder loads the site in an iframe [code: plugins/MauticFocusBundle/Assets/js/focus.js:238-245 @7.x].

## 8. Expected behaviour: Social Monitoring and Tweets

T1. Monitors are `twitter_handle` (mention, handle without @) or `twitter_hashtag` (without #), with optional "match Contact names", Segments and publish dates. Editing increments `revision` [code: plugins/MauticSocialBundle/Model/MonitoringModel.php:36-45,116-131 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/social_monitoring.html#creating-a-social-monitor].

T2. `mautic:social:monitoring --batch-size=N` (required, numeric) runs `social:monitor:twitter:hashtags` or `:mentions` per published monitor, with `maxPerIterations = ceil(batch/monitors)`. With no monitors it prints `No published monitors found…` and exits 0. It takes no lock [code: plugins/MauticSocialBundle/Command/MauticSocialMonitoringCommand.php:28-138 @7.x] [code: plugins/MauticSocialBundle/Tests/Functional/SocialCommandsTest.php:11-35 @7.x].

T3. Sub-commands exit 1 when Twitter is unpublished (`Twitter plugin not published!`) or unauthorized, or when the monitor is missing. They query Twitter API v1.1 `search/tweets` with `since_id`, recurse until `--max-runs`, then dispatch `MONITOR_POST_PROCESS` [code: plugins/MauticSocialBundle/Command/MonitorTwitterBaseCommand.php:130-226 @7.x].

T4. Contact matching uses the handle in field `twitter_handle_field` (default `twitter`), case-insensitive. With `checknames`, a same-name Contact with an empty handle is matched and its handle filled. Otherwise a Contact is created with the handle, names and `country = location`, added to the monitor's Segments and given a `monitoring_leads` row [code: plugins/MauticSocialBundle/Helper/TwitterCommandHelper.php:82-285 @7.x].

T5. `monitor_post_count` is updated per date only, not per monitor, so counts are shared across monitors [code: plugins/MauticSocialBundle/Model/PostCountModel.php:51-85 @7.x].

T6. Campaign action `twitter.tweet` posts `statuses/update` with tokens and trackables (channel `social_twitter`). It fails with `handle_not_found` when the hard-coded `twitter` field is empty. Success is recorded as a `tweet_stats` row and a `sent_count` increment [code: plugins/MauticSocialBundle/Helper/CampaignEventHelper.php:27-113 @7.x] [code: plugins/MauticSocialBundle/Model/TweetModel.php:86-126 @7.x].

T7. Tweet text has at most 280 characters. The REST API `/api/tweets` requires `name` and `text` and needs Twitter active [code: plugins/MauticSocialBundle/Entity/Tweet.php:133,188 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/tweets.html#create-tweet].

T8. The social login form field and the social config tab exist only when Twitter is published [code: plugins/MauticSocialBundle/EventListener/FormSubscriber.php:26-45 @7.x] [code: plugins/MauticSocialBundle/EventListener/ConfigSubscriber.php:26-40 @7.x].

T9. Menu items are hidden when Twitter is disabled [code: plugins/MauticSocialBundle/Tests/Functional/SocialMonitoringFunctionalTest.php:13-30 @7.x].

T10. Other networks are legacy: Instagram v1, Foursquare `v=20140806`, Facebook Graph, and LinkedIn as templates only [code: plugins/MauticSocialBundle/Integration/InstagramIntegration.php:35-38 @7.x] [code: plugins/MauticSocialBundle/Integration/FoursquareIntegration.php:47-50 @7.x].

## 9. Maintenance status: maintained vs legacy/dead

| Part | Status | Evidence |
|---|---|---|
| Channel registry, Marketing Messages, message queue, broadcasts | Maintained (tests, 7.2 deprecation work) | [code: app/bundles/ChannelBundle/Config/services.php:33-34 @7.x] |
| SMS + Twilio, MMS, replies | Maintained | [code: app/bundles/SmsBundle/Tests/Integration/Twilio/TwilioCallbackTest.php:28-90 @7.x] |
| `SmsEvents::ON_CAMPAIGN_TRIGGER_ACTION`, `/sms/receive`, `sms_enabled/username/password/messaging_service_sid` params, Twilio frequency fields | Dead / deprecated | [code: app/bundles/SmsBundle/SmsEvents.php:78-82 @7.x] [code: app/bundles/SmsBundle/Config/config.php:26-33,70-79 @7.x] |
| Push campaign sending (web + mobile) | Works | [code: app/bundles/NotificationBundle/Tests/Functional/EventListener/CampaignSubscriberTest.php:48-470 @7.x] |
| Segment push, read/click stats, `/notification/receive`, `NOTIFICATION_ON_FORM_ACTION_SEND`, `notification_*` params, `NotificationHelper::unsubscribe()` | Dead | [code: app/bundles/NotificationBundle/NotificationEvents.php:31 @7.x] [code: app/bundles/NotificationBundle/Helper/NotificationHelper.php:33-44 @7.x] |
| Focus Items | Maintained | [code: plugins/MauticFocusBundle/Tests/Model/FocusModelFunctionalTest.php:28 @7.x] |
| Focus `website_snapshot_*` params | Dead | [code: plugins/MauticFocusBundle/Config/config.php:65-68 @7.x] |
| Social Monitoring, Tweets, Social login | Legacy; working against current X API terms is unverified | [code: plugins/MauticSocialBundle/Integration/TwitterIntegration.php:60-86 @7.x] |

## 10. Open questions
1. Should cancelling a queued message stop it (Q11)? The code says no.
2. Should STOP synonyms be handled (S29)? The docs say yes, the code no.
3. Are segment push notifications intended at all (N14)?
4. Is `/notification/appcallback` intentionally unauthenticated (N6)?
5. Notice vs notification type (F14) and "once" vs "once per session" (F7).
6. Should the SMS campaign action use pass-with-error for unsent Contacts so Marketing Message fallback works (M9)? Today it does not.
