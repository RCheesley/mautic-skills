# Channels: version notes

## 5.x / 6.x
- 5.0: Twilio sends with the integration feature setting `messaging_service_sid` instead of `sending_phone_number`, a possible BC break for installs configured with a number [PR #12539].
- 5.0: "Disable trackable URLs" for SMS moved from the Twilio integration to the global Text Message setting `sms_disable_trackable_urls`; a migration moves the value [PR #11683].
- 5.0: LinkedIn was removed from core; only its templates remain [PR #12147]. Twitter monitoring commands were restored after autowiring dropped them [PR #11981].
- 5.0: `mautic:broadcasts:send` gained `--max-threads`/`--thread-id` [PR #11549]. Focus items got conversion rates and timeline events [PR #11945] [PR #11999], and invalid focus LESS became an error [PR #12422] [PR #12442].
- 5.0: channel UIs moved from PHP templates to Twig, so template overrides must be Twig [PR #11866] [PR #11931] [PR #11944].
- 5.1: focus modals and notifications close only with ×; "Stop engaging after closing" (cookie `mautic_focus_{id}_closed`) was added; the form success message stays until closed [PR #12705] [PR #12742] [PR #12706].
- 5.1: SMS token autosuggest [PR #11864], failed-send content on the timeline [PR #13350], batched OneSignal campaign action [PR #13451], and Twitter UI hidden when Twitter is disabled [PR #12778]. `iterator_mode` was deprecated for `iterable_mode` [PR #13112].
- 5.2.x: a queued message is sent once per Contact per window without ORM errors [PR #14247] (5.2.3); empty `push_id` on `/notification/appcallback` is ignored [PR #14480] (5.2.7).
- 6.0: the "Focus Stats" report source was added [PR #14340]. 6.0.1 stopped SMS campaign sends detaching the Lead, which had caused duplicate SMS [PR #14874]. No other channel-specific 6.0 differences were found in 90 PRs of chunk 3.
- Historical leftovers that explain the current code: SMS parameters `sms_username`/`sms_password`/`sms_messaging_service_sid`/`sms_enabled` and the `notification_*` parameters predate the move of credentials into the Twilio and OneSignal integrations, and nothing reads them now [code: app/bundles/SmsBundle/Config/config.php:70-79 @7.x] [code: app/bundles/NotificationBundle/Config/config.php:112-125 @7.x]. `/sms/receive` is the Twilio-specific path kept as an alias of `/sms/{transport}/callback` [code: app/bundles/SmsBundle/Config/config.php:26-33 @7.x]. The `tweet` channel still registers the legacy `MauticSocialBundle:Tweet` repository alias [code: plugins/MauticSocialBundle/EventListener/ChannelSubscriber.php:43 @7.x].

## 7.x (7.0–7.2.2)
- 7.0: SMS and mobile notification translations (`translation_parent_id`) [PR #15481] [PR #15520]; `mautic:messages:send` drains the whole queue with `--limit`/`--batch` (default 50) instead of 50 per run [PR #15333]; the focus rendering cache was removed and focus links redirect once [PR #15502]; "Focus Leads" report source [PR #14923]; `iterator_mode` removed [PR #14896].
- 7.0.1: focus builder parses CSP `frame-ancestors` [PR #15837]; form auto-fill works inside focus items [PR #15860].
- 7.1: Social Monitoring in API v2 [PR #15696]; timeline labels "Text Message Sent/Failed" [PR #15763].
- 7.2: MMS with `BulkTransportInterface` and `MMSTransportInterface` [PR #15999]; SMS stats recorded against the sent translation [PR #15545]; controllers get models by typed injection [PR #16582]; SMS, Social and Notification services autowired [PR #16785] [PR #16790] [PR #16800].
- Fixed on the 7.2 branch after 7.2.2 (milestone 7.2.3, not yet in the 7.x snapshot): forms in focus items show the success message and validation errors again [PR #18115].
- Unreleased on 7.x (7.3.0-rc): send-to-unsubscribed indicator on Marketing Message email selection [PR #17388]; `notification_tracking_page_enabled` removed [PR #17671]. Social Monitoring, Tweets and the social integrations are still shipped in 7.2.2 and on the 7.x branch [code: plugins/MauticSocialBundle/Integration/TwitterIntegration.php:83-86 @7.x].
- 7.2 deprecates the service alias `mautic.channel.helper.channel_list`; inject `Mautic\ChannelBundle\Helper\ChannelListHelper` [code: app/bundles/ChannelBundle/Config/services.php:33-34 @7.x].
- `NotificationHelper::unsubscribe()` is `@deprecated` with removal planned for 8.0 [code: app/bundles/NotificationBundle/Helper/NotificationHelper.php:33-44 @7.x].
- `SmsEvents::ON_CAMPAIGN_TRIGGER_ACTION` is marked deprecated and is never dispatched [code: app/bundles/SmsBundle/SmsEvents.php:78-82 @7.x].
- API Platform (`/api/v2`) resources exist for `Message`, `Channel`, `Sms`, `Focus` (`/focus_items`) and `Monitoring`, but not for `Notification` [code: app/bundles/SmsBundle/Entity/Sms.php:37-55 @7.x] [code: plugins/MauticSocialBundle/Entity/Monitoring.php:21-39 @7.x].

## 8.x delta: 8.x (snapshot pinned in SOURCES.md)
Platform: PHP 8.4, Symfony 8.1, Doctrine ORM 3 and DBAL 4 [PR #16993] [PR #17392] [PR #17361]. 7.2.2 and the 7.x work up to 2026-11-16 are in 8.x through the squash merge [PR #18236]; compare trees, not ancestry. The focus-item form message fix [PR #18115] (7.2 branch after 7.2.2) is not on 8.x yet [code: plugins/MauticFocusBundle/Resources/views/Builder/form.html.twig @8.x].

Removed: Social Monitoring, Tweets and the social integrations
- MauticSocialBundle and `mautic/plugin-social` are removed: the Facebook, Twitter/X, Instagram and Foursquare integrations, Social Monitoring (`mautic:social:monitoring`, `social:monitor:twitter:hashtags|mentions`), Tweets (`/api/tweets`, the `tweet` Marketing Message channel, the `twitter.tweet` campaign action) and the `plugin.loginSocial` form field all go. Social tables and integration settings are kept; `mautic:plugins:reload` marks the plugin missing; saved campaigns and forms are not rewritten, so a retained tweet action can interrupt its campaign [PR #17473] [code: UPGRADE-8.0.md "Social media integrations" @8.x]. Remove the scheduled social monitoring commands before upgrading.

Events (dispatch by class)
- ChannelBundle dispatches its 5 events by class (`ChannelEvent`, `ChannelBroadcastEvent`, `MessageQueueEvent`, `MessageQueueProcessEvent`, `MessageQueueBatchProcessEvent`). The constants are **kept but no longer dispatched by name**, so a listener keyed on `ChannelEvents::ADD_CHANNEL` silently never runs [PR #17201] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/channels.html#extending-broadcasts].
- SmsBundle: 10 constants removed (`DNC_FILTER_CONTACTS_ON_SEND`, `QUEUE_FILTER_CONTACTS_ON_SEND`, `FILTER_CONTACTS_ON_SEND`, `ON_CAMPAIGN_TRIGGER_ACTION`, `ON_REPLY`, `ON_SMS_TOKENS_BUILD`, `SMS_PRE/POST_SAVE`, `SMS_PRE/POST_DELETE`). Subscribe to `DncEvent`, `QueueEvent`, `FilterEvent`, `ReplyEvent`, `TokensBuildEvent` and `SmsPre/PostSave/DeleteEvent`; `SmsEvent` is abstract. Kept: `TOKEN_REPLACEMENT` (still dispatched by name), `SMS_ON_SEND` (dispatched as `SmsSendEvent`), `ON_CAMPAIGN_TRIGGER_BATCH_ACTION` and `ON_CAMPAIGN_REPLY` [PR #17216] [PR #17622] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/sms.html#sms-event-constants].
- NotificationBundle: `NOTIFICATION_ON_SEND` is dispatched as `NotificationSendEvent`; `TOKEN_REPLACEMENT` stays a string dispatch; CRUD groups are still dispatched by name [PR #17216].
- MauticFocusBundle: `TOKEN_REPLACEMENT` → `FocusTokenReplacementEvent`; `FOCUS_ON_VIEW` → `FocusViewEvent`; `ON_CAMPAIGN_TRIGGER_ACTION` → `ON_CAMPAIGN_BATCH_ACTION` (`mautic.focus.on_campaign_batch_action`, listen on `PendingEvent`) [PR #17223] [PR #17782].
- The earlier MauticSocialBundle event work (`SocialEvent` removed, `mautic.social.on_campaign_batch_action`) [PR #17544] [PR #17250] is moot: the whole bundle was removed afterwards [PR #17473].
- Legacy campaign actions registered with `eventName`/`callback` no longer run at all; only `batchEventName` actions execute [PR #17097].

Removed routes and APIs
- `/sms/receive` (`mautic_receive_sms`) returns 404; Twilio must use `/sms/twilio/callback` [code: UPGRADE-8.0.md:368 @8.x] [PR #17231].
- `mautic_receive_notification` (`/notification/receive`) is removed; it pointed at a missing controller action [code: UPGRADE-8.0.md:422 @8.x].
- `NotificationHelper::unsubscribe()` is removed, with `LeadRepository` and `DoNotContact` constructor args [code: UPGRADE-8.0.md:323 @8.x].
- Service id `mautic.sms.callback_handler_container` is removed; use the FQCN [code: UPGRADE-8.0.md:267 @8.x].

Signatures
- `MessageModel::getMessageChannels(int)`, `MessageQueueModel::processMessageQueue(array|MessageQueue)`, `Channel::getProperties(): array`, `MessageQueue::getMetadata(): array` [PR #17201].
- `TransportChain::sendSms(…, string)`; typed setters on `Notification`, `PushID` and push `Stat` [PR #17622] [PR #17216].

OneSignal (push)
- `OneSignalIntegration` extends IntegrationsBundle `BasicIntegration`; keys come from `OneSignalKeysType` (`app_id`, `safari_web_id`, `rest_api_key`, `gcm_sender_id`, required only while published) and features from `OneSignalFeatureSettingsType`. Saved `subdomain_name` and `platforms` move under `featureSettings['integration']` (migration `Version20261109120000`). `CampaignSubscriber`, `ChannelSubscriber`, `PageSubscriber`, `BuildJsSubscriber`, `NotificationHelper` and `MobileNotificationDetailsType` take `OneSignalIntegrationHelper` instead of `IntegrationHelper` [PR #18113] [code: UPGRADE-8.0.md "Changed code" @8.x] [code: app/bundles/NotificationBundle/Helper/OneSignalIntegrationHelper.php @8.x].
- Notification preview CSS moved to Bootstrap utilities; no behaviour change [PR #18287].

User docs: SMS, Marketing Messages, web and mobile notifications and Focus Items are unchanged in 8.0 [docs: https://docs.mautic.org/en/7.2/channels/sms.html]. The 8.0 user docs still carry the Social Monitoring, Social Login and Twitter pages although 8.x removed them [docs: https://docs.mautic.org/en/8.0/channels/social_monitoring.html]; dev docs 8.0 dropped the tweets REST page [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/getting_started.html].
