# Channels: version notes

## 5.x / 6.x
- The analysis inputs record no channel-specific behaviour differences for 5.x or 6.x in these bundles. Do not assume any; check the 5.x/6.x tree before claiming one. PR-derived history comes in a later pass (references/pr-history.md).
- Historical leftovers that explain the current code: SMS parameters `sms_username`/`sms_password`/`sms_messaging_service_sid`/`sms_enabled` and the `notification_*` parameters predate the move of credentials into the Twilio and OneSignal integrations, and nothing reads them now [code: app/bundles/SmsBundle/Config/config.php:70-79 @7.x] [code: app/bundles/NotificationBundle/Config/config.php:112-125 @7.x]. `/sms/receive` is the Twilio-specific path kept as an alias of `/sms/{transport}/callback` [code: app/bundles/SmsBundle/Config/config.php:26-33 @7.x]. The `tweet` channel still registers the legacy `MauticSocialBundle:Tweet` repository alias [code: plugins/MauticSocialBundle/EventListener/ChannelSubscriber.php:43 @7.x].

## 7.x (7.0–7.2.1)
- 7.2 deprecates the service alias `mautic.channel.helper.channel_list`; inject `Mautic\ChannelBundle\Helper\ChannelListHelper` [code: app/bundles/ChannelBundle/Config/services.php:33-34 @7.x].
- `NotificationHelper::unsubscribe()` is `@deprecated` with removal planned for 8.0 [code: app/bundles/NotificationBundle/Helper/NotificationHelper.php:33-44 @7.x].
- `SmsEvents::ON_CAMPAIGN_TRIGGER_ACTION` is marked deprecated and is never dispatched [code: app/bundles/SmsBundle/SmsEvents.php:78-82 @7.x].
- API Platform (`/api/v2`) resources exist for `Message`, `Channel`, `Sms`, `Focus` (`/focus_items`) and `Monitoring`, but not for `Notification` [code: app/bundles/SmsBundle/Entity/Sms.php:37-55 @7.x] [code: plugins/MauticSocialBundle/Entity/Monitoring.php:21-39 @7.x].

## 8.x delta (8.x @ 11599729491; 7.2.1 work not yet merged forward)
Platform: PHP 8.4, Symfony 8.1, Doctrine ORM 3 and DBAL 4 [PR #16993] [PR #17392] [PR #17361].

Events (dispatch by class)
- ChannelBundle dispatches its 5 events by class (`ChannelEvent`, `ChannelBroadcastEvent`, `MessageQueueEvent`, `MessageQueueProcessEvent`, `MessageQueueBatchProcessEvent`). The constants are **kept but no longer dispatched by name**, so a listener keyed on `ChannelEvents::ADD_CHANNEL` silently never runs [PR #17201] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/channels.html#extending-broadcasts].
- SmsBundle: 10 constants removed (`DNC_FILTER_CONTACTS_ON_SEND`, `QUEUE_FILTER_CONTACTS_ON_SEND`, `FILTER_CONTACTS_ON_SEND`, `ON_CAMPAIGN_TRIGGER_ACTION`, `ON_REPLY`, `ON_SMS_TOKENS_BUILD`, `SMS_PRE/POST_SAVE`, `SMS_PRE/POST_DELETE`). Subscribe to `DncEvent`, `QueueEvent`, `FilterEvent`, `ReplyEvent`, `TokensBuildEvent` and `SmsPre/PostSave/DeleteEvent`; `SmsEvent` is abstract. Kept: `TOKEN_REPLACEMENT` (still dispatched by name), `SMS_ON_SEND` (dispatched as `SmsSendEvent`), `ON_CAMPAIGN_TRIGGER_BATCH_ACTION` and `ON_CAMPAIGN_REPLY` [PR #17216] [PR #17622] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/sms.html#sms-event-constants].
- NotificationBundle: `NOTIFICATION_ON_SEND` is dispatched as `NotificationSendEvent`; `TOKEN_REPLACEMENT` stays a string dispatch; CRUD groups are still dispatched by name [PR #17216].
- MauticFocusBundle: `TOKEN_REPLACEMENT` → `FocusTokenReplacementEvent`; `FOCUS_ON_VIEW` → `FocusViewEvent`; `ON_CAMPAIGN_TRIGGER_ACTION` → `ON_CAMPAIGN_BATCH_ACTION` (`mautic.focus.on_campaign_batch_action`, listen on `PendingEvent`) [PR #17223] [PR #17782].
- MauticSocialBundle: `SocialEvent` removed; `AbstractMonitorEvent`/`AbstractTweetEvent` plus 8 lifecycle classes; `ON_CAMPAIGN_BATCH_ACTION` (`mautic.social.on_campaign_batch_action`) added; `CampaignEventHelper::sendTweetAction()` takes a `Campaign\Entity\Event`; `SocialIntegration` gets array return types [PR #17544] [PR #17250].
- Legacy campaign actions registered with `eventName`/`callback` no longer run at all; only `batchEventName` actions execute [PR #17097].

Removed routes and APIs
- `/sms/receive` (`mautic_receive_sms`) returns 404; Twilio must use `/sms/twilio/callback` [code: UPGRADE-8.0.md:277 @8.x] [PR #17231].
- `mautic_receive_notification` (`/notification/receive`) is removed; it pointed at a missing controller action [code: UPGRADE-8.0.md:331 @8.x].
- `NotificationHelper::unsubscribe()` is removed, with `LeadRepository` and `DoNotContact` constructor args [code: UPGRADE-8.0.md:232 @8.x].
- Service id `mautic.sms.callback_handler_container` is removed; use the FQCN [code: UPGRADE-8.0.md:177 @8.x].

Signatures
- `MessageModel::getMessageChannels(int)`, `MessageQueueModel::processMessageQueue(array|MessageQueue)`, `Channel::getProperties(): array`, `MessageQueue::getMetadata(): array` [PR #17201].
- `TransportChain::sendSms(…, string)`; typed setters on `Notification`, `PushID` and push `Stat` [PR #17622] [PR #17216].
- Doctrine ORM 3 may not resolve the `MauticSocialBundle:Tweet` alias used by the `tweet` channel (inferred from the code analysis; verify on 8.x) [code: plugins/MauticSocialBundle/EventListener/ChannelSubscriber.php:43 @7.x].

User docs: SMS, Marketing Messages, web and mobile notifications, Focus Items and Social Monitoring are unchanged in 8.0 [docs: https://docs.mautic.org/en/7.2/channels/sms.html].
