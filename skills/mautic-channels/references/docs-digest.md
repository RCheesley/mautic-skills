# Channels: what the official docs say (7.2)

User docs pages are unchanged between 7.2 and 8.0 for SMS, Marketing Messages, web notifications, push
notifications, Focus Items and Social Monitoring [docs: https://docs.mautic.org/en/7.2/channels/sms.html]. Code wins
where the docs differ; each difference is marked **Code differs** with the behaviour.md item.

## Terminology (docs usage)
- UI names: "Text Messages" (SMS), "Web Notifications" / "Browser Notification", "Mobile Notifications", "Marketing Messages", "Focus Items", "Social Monitoring". Capitalised product nouns: Contact, Segment, Campaign, Text Message, Focus Item, Social Monitor, Channel, Do Not Contact (DNC) [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html].
- "Template" Text Message = triggered by Campaigns/Forms/Point Triggers; "Segment" Text Message = broadcast [docs: https://docs.mautic.org/en/7.2/channels/sms.html#template-text-messages].

## Text Messages (SMS)
- SMS needs a transport such as the Twilio plugin [docs: https://docs.mautic.org/en/7.2/channels/sms.html].
- Template messages can't be sent manually to a list. Segment messages can't be edited once sent, keep going to new Segment members, reach each Contact once, and need the "Send Scheduled Broadcasts" cron job [docs: https://docs.mautic.org/en/7.2/channels/sms.html#segment-text-messages].
- Fields: Internal name, Text Message (character counter, `{contactfield=alias}`), Category, Language, Published. Segment type adds Contact Segment, Publish at and Unpublish at [docs: https://docs.mautic.org/en/7.2/channels/sms.html#template-text-message-fields].
- Messages created from the Campaign Builder are Template type [docs: https://docs.mautic.org/en/7.2/channels/sms.html#creating-text-messages-from-campaign-builder].
- MMS: the **Is MMS** toggle, media from Assets or a URL, `.gif/.png/.jpg/.jpeg`, max 10 images, 5 MB total, external URLs not validated, US/CA/AU only (link elsewhere), `[MMS]` prefix in the builder [docs: https://docs.mautic.org/en/7.2/channels/sms.html#sending-multimedia-messages-mms].
- Unsubscribe: STOP, STOPALL, UNSUBSCRIBE, CANCEL, END and QUIT set DNC until manual resubscribe [docs: https://docs.mautic.org/en/7.2/channels/sms.html#managing-unsubscribes]. **Code differs:** only `stop` (behaviour.md S29).
- The reply decision matches against "Pattern the reply should match" and does not require a prior send [docs: https://docs.mautic.org/en/7.2/channels/sms.html#working-with-replies-to-text-messages].
- Numbers must be `+XXXXXXX` in the Mobile field [docs: https://docs.mautic.org/en/7.2/channels/sms.html#important-notes]. Code also falls back to `phone` (behaviour.md S14).

## Twilio plugin
- Account SID and Auth Token go on the Enabled/Auth tab, the Messaging Service SID on the Features tab. Set Request URL, Fallback URL and Delivery Status Callback to `https://<host>/sms/twilio/callback`. Configure SMS frequency rules and publish [docs: https://docs.mautic.org/en/7.2/plugins/twilio.html#mautic-twilio-plugin]. **Code differs:** the frequency fields on the Twilio form are not read (behaviour.md S16).
- MMS must be on in the Twilio Messaging Service. Alphanumeric Sender ID needs a paid account, and recipients can't reply [docs: https://docs.mautic.org/en/7.2/plugins/twilio.html#enabling-multimedia-messaging-mms] [docs: https://docs.mautic.org/en/7.2/plugins/twilio.html#alphanumeric-sender-id].

## Marketing Messages
- One message across Email, SMS, Browser Notification, Mobile Notification, Tweets and custom channels, sent through the "Send Marketing Message" campaign action [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#what-are-marketing-messages].
- Delivery uses the preferred channel, defaulting to Email. An exceeded frequency limit moves the send to another channel, and Contacts can pause channels [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#what-are-marketing-messages]. **Code differs** for SMS (behaviour.md M9).
- Channels appear only once configured [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#creating-a-marketing-message].

## Web and mobile notifications
- Enable the OneSignal plugin. Create a OneSignal app (Website Push, Typical Site), upload the SDK files to the Mautic root, enter the keys from Settings > Keys & IDs, and choose features (mobile, Landing Pages, tracked pages, welcome notification, subdomain) [docs: https://docs.mautic.org/en/7.2/channels/web_notifications.html#configuration].
- Sent by a Campaign action or a Marketing Message [docs: https://docs.mautic.org/en/7.2/channels/web_notifications.html#sending-notifications].
- Mobile apps POST `{"email","push_id","enabled"}` to `/notification/appcallback`, optionally with `stat` [docs: https://docs.mautic.org/en/7.2/channels/push_notifications.html#notification-statistics]. The iOS sample is old (Swift 3.1) [docs: https://docs.mautic.org/en/7.2/channels/push_notifications.html#ios-code-for-onesignal-integration].

## Focus Items
- Types: Collect Data, Display a Notice, Emphasize a link [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#types-of-focus-item].
- Engagement: upon arrival, slight scroll, middle, bottom, exit intent; timeout; frequency every page / once per session / 2 min / 15 min / hour / day; stop after conversion or close; animate [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#engagement-options]. **Code differs:** "once" is permanent (behaviour.md F7).
- Styles: Bar (hide, push down, sticky, top/bottom, Large/Regular), Modal, Notification, Full page [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#styles].
- Colours default to the site snapshot palette [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#colors]. Content modes Basic/Editor/HTML; switching clears data [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#content].
- The preview needs SSL and no `x-frame-options: SAMEORIGIN` [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#using-the-focus-item-builder].
- Deploy with the embed snippet and allow the domain in CORS settings; the campaign route ("Visits a Page" → "Show Focus Item") is "sometimes unreliable" [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#deploying-to-a-website] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#deploying-through-a-campaign].
- UTM tags are applied to links and submissions; "Emphasize a link" reports unique clicks [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#measuring-success].

## Social Monitoring
- Needs the Twitter plugin and the social monitoring cron job. Monitors are Twitter mention or hashtag, with Match Contact names, Active dates and a Contact Segment [docs: https://docs.mautic.org/en/7.2/channels/social_monitoring.html#requirements] [docs: https://docs.mautic.org/en/7.2/channels/social_monitoring.html#creating-a-social-monitor].
- The Twitter plugin page has a title only [docs: https://docs.mautic.org/en/7.2/plugins/twitter.html]. Social Login (X/Twitter, Facebook, LinkedIn) pre-fills forms [docs: https://docs.mautic.org/en/7.2/plugins/social_login.html].

## Developer docs
- SMS transports: `TransportInterface::sendSms(Lead, $content)` returns true or an error string. `BulkTransportInterface::sendBatchSms(RecipientCollection, string)` and `MMSTransportInterface::sendMms(Lead, string, array)` are optional. Tag the service `mautic.sms_transport` explicitly; the `integrationAlias` tag argument names the integration. Callbacks use `mautic.sms_callback_handler` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/sms.html#transport-interfaces] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/sms.html#registering-the-transport].
- `RecipientCollection` iterates `SmsRecipientDTO` (`getLead`, `getFinalMessage`, `getSubstitutionData`, `setResult`) [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/sms.html#bulk-sending-and-recipient-data].
- Three filter events in order: DNC, queue, generic [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/sms.html#contact-filtering-events]. Campaign SMS actions use `ON_CAMPAIGN_TRIGGER_BATCH_ACTION` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/sms.html#batch-action-event].
- Channels: `ADD_CHANNEL` with features; broadcasts through `CHANNEL_BROADCAST` (prose says `CoreEvents`, the example `ChannelEvents`; code: `ChannelEvents`). The page is flagged outdated [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/channels.html#extending-broadcasts].

## REST API docs
- `/api/notifications`: GET one or list, `POST /new`, `PATCH|PUT /ID/edit`, `DELETE /ID/delete`. Fields include heading, message, url, language, readCount and sentCount. The page is flagged outdated [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/notifications.html].
- `/api/smses`: CRUD, plus `GET /smses/ID/contact/CID/send` returning `{"success":1,"status":"Delivered"}`. The page is flagged outdated [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/text_messages.html#send-sms-to-contact]. The code accepts any method (behaviour.md S20).
- `/api/tweets`: CRUD; `name` and `text` (≤280) are required; needs Twitter active [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/tweets.html].
- `/api/focus` and `/api/messages` pages are stubs with no endpoints, so rely on code [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/focus.html] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/messages.html].

## 8.0 devdocs changes
- SMS: filter events are keyed by class (`DncEvent`, `QueueEvent`, `FilterEvent`); new `SmsPreSaveEvent`, `SmsPostSaveEvent`, `SmsPreDeleteEvent`, `SmsPostDeleteEvent` and `ReplyEvent`. The remaining constants are `TOKEN_REPLACEMENT`, `SMS_ON_SEND`, `ON_CAMPAIGN_TRIGGER_BATCH_ACTION` and `ON_CAMPAIGN_REPLY` [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/sms.html#sms-event-constants].
- Channels: subscribe to `ChannelEvent::class` and `ChannelBroadcastEvent::class` [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/channels.html#extending-broadcasts].

## Documentation gaps
No docs cover Twilio character encoding or segment counting, resubscribing an SMS Contact, the web notification UI and stats, the mobile push stat JSON schema, the Focus snippet format, or the full custom-channel contract (preference and Marketing Message hookup) [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/channels.html].
