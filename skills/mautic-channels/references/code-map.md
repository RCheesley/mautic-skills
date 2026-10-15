# Channels: code map (Mautic 7.x)

Paths are relative to the repository root. B = `app/bundles/`, P = `plugins/` in the prose only; every citation uses full paths.

## Contents
1. Entities and tables
2. Services and models
3. Events (constants, dispatch sites, listeners)
4. Routes, controllers and UI
5. Console commands
6. Configuration parameters
7. Permissions
8. Extension points
9. Cross-bundle touch points

## 1. Entities and tables

| Entity | Table | Key facts | Source |
|---|---|---|---|
| `ChannelBundle\Entity\Message` | `messages` (+ `message_projects_xref`) | FormEntity, Uuid, Project; OneToMany `channels` indexed by `channel`, orphanRemoval; API Platform `channel:messages:*` | [code: app/bundles/ChannelBundle/Entity/Message.php:27-45,104-126 @7.x] |
| `ChannelBundle\Entity\Channel` | `message_channels` | `channel`, `channel_id` (nullable), `properties` JSON, `is_enabled` (default false); unique `(message_id, channel)`; message FK CASCADE | [code: app/bundles/ChannelBundle/Entity/Channel.php:92-110 @7.x] |
| `ChannelBundle\Entity\MessageQueue` | `message_queue` | statuses rescheduled/pending/sent/cancelled; priority 1/2; `event_id`, `lead_id` CASCADE; `options` array with `metadata`; `setOptions()` appends | [code: app/bundles/ChannelBundle/Entity/MessageQueue.php:14-24,117-178,210-213,452-461 @7.x] |
| `SmsBundle\Entity\Sms` | `sms_messages` (+ `sms_message_list_xref`, `sms_projects_xref`) | `message`, `sms_type` (`template`/`list`), `sent_count`, `media` JSON, `is_mms`; Translation trait; Variant trait unmapped; API Platform `sms:smses:*` | [code: app/bundles/SmsBundle/Entity/Sms.php:37-55,132,179-260 @7.x] |
| `SmsBundle\Entity\Stat` | `sms_message_stats` | sms/lead/list SET NULL; `tracking_hash`, `source`, `source_id`, `tokens`, `details`, `is_failed` | [code: app/bundles/SmsBundle/Entity/Stat.php:17,85-132 @7.x] |
| `NotificationBundle\Entity\Notification` | `push_notifications` (+ `push_notification_list_xref`) | `url`, `heading`, `message`, `button`, `utm_tags`, `notification_type`, `read_count`, `sent_count`, `mobile`, `mobileSettings`; no `#[ApiResource]` | [code: app/bundles/NotificationBundle/Entity/Notification.php:186-299 @7.x] |
| `NotificationBundle\Entity\Stat` | `push_notification_stats` | `date_read`, `is_clicked`, `retry_count` never written | [code: app/bundles/NotificationBundle/Entity/Stat.php:16,106-166 @7.x] |
| `NotificationBundle\Entity\PushID` | `push_ids` | `push_id`, `lead_id` SET NULL, `enabled`, `mobile`; owned by `Lead::pushIds` | [code: app/bundles/NotificationBundle/Entity/PushID.php:42-61 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:355-360 @7.x] |
| `MauticFocusBundle\Entity\Focus` | `focus` (+ `focus_projects_xref`) | `focus_type`, `style`, `website`, `properties`, `utm_tags`, `form_id` (plain int), `cache`, `html_mode`, `editor`, `html`; API Platform `/focus_items` | [code: plugins/MauticFocusBundle/Entity/Focus.php:26-43,180-220 @7.x] |
| `MauticFocusBundle\Entity\Stat` | `focus_stats` | types `view`, `click`, `submission`; focus CASCADE, lead SET NULL | [code: plugins/MauticFocusBundle/Entity/Stat.php:14-18,54-72 @7.x] |
| `MauticSocialBundle\Entity\Monitoring` | `monitoring` | `title`, `network_type`, `lists`, `revision`, `stats`, `properties`; API Platform `mauticSocial:monitoring:*` | [code: plugins/MauticSocialBundle/Entity/Monitoring.php:21-39,114-149 @7.x] |
| `MauticSocialBundle\Entity\Lead` | `monitoring_leads` | (monitor_id, lead_id), `date_added` | [code: plugins/MauticSocialBundle/Entity/Lead.php:31-41 @7.x] |
| `MauticSocialBundle\Entity\PostCount` | `monitor_post_count` | `post_date`, `post_count` | [code: plugins/MauticSocialBundle/Entity/PostCount.php:36-47 @7.x] |
| `MauticSocialBundle\Entity\Tweet` / `TweetStat` | `tweets` / `tweet_stats` | text 280; page/asset SET NULL; stat `twitter_tweet_id`, `handle`, `response_details` | [code: plugins/MauticSocialBundle/Entity/Tweet.php:123-150 @7.x] [code: plugins/MauticSocialBundle/Entity/TweetStat.php:71-125 @7.x] |

## 2. Services and models

| Service | Role | Source |
|---|---|---|
| `ChannelBundle\Model\MessageModel` (`mautic.channel.model.message`) | Marketing Message CRUD; `CHANNEL_FEATURE='marketing_messages'`; `getChannels()` (static cache); `getLeadStatsPost()` | [code: app/bundles/ChannelBundle/Model/MessageModel.php:28-231 @7.x] |
| `ChannelBundle\Model\MessageQueueModel` (`mautic.channel.model.queue`) | `processFrequencyRules()`, `queue()`, `sendMessages()`, `processMessageQueue()`, `reschedule()`; `DEFAULT_RESCHEDULE_INTERVAL='PT15M'` | [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:28-352 @7.x] |
| `ChannelActionModel`, `FrequencyActionModel` | Bulk DNC / frequency updates | [code: app/bundles/ChannelBundle/Model/ChannelActionModel.php:23-71 @7.x] [code: app/bundles/ChannelBundle/Model/FrequencyActionModel.php:23-79 @7.x] |
| `PreferenceBuilder\PreferenceBuilder`, `ChannelPreferences` | Per-log channel priority (not autowired) | [code: app/bundles/ChannelBundle/Config/services.php:15-18 @7.x] |
| `Helper\ChannelListHelper` (Twig `channel`; alias `mautic.channel.helper.channel_list` deprecated 7.2) | Channel registry | [code: app/bundles/ChannelBundle/Config/services.php:31-34 @7.x] |
| `SmsBundle\Model\SmsModel` | `sendSms()` pipeline, stats, pending-count cache | [code: app/bundles/SmsBundle/Model/SmsModel.php:90-570 @7.x] |
| `SmsBundle\Sms\TransportChain` (`mautic.sms.transport_chain`) | Transports tagged `mautic.sms_transport`; primary = `sms_transport` param; `getEnabledTransports()` | [code: app/bundles/SmsBundle/Sms/TransportChain.php:62-187 @7.x] |
| `Integration\Twilio\TwilioTransport` (`mautic.sms.twilio.transport`, aliases `sms_api`, `mautic.sms.api`), `Configuration`, `TwilioCallback`, `Integration\TwilioIntegration` | Twilio | [code: app/bundles/SmsBundle/Integration/Twilio/Configuration.php:71-95 @7.x] [code: app/bundles/SmsBundle/Integration/TwilioIntegration.php:12-45 @7.x] |
| `Callback\HandlerContainer` | Callback handlers by transport name | [code: app/bundles/SmsBundle/Callback/HandlerContainer.php:18-44 @7.x] |
| `Helper\ReplyHelper`, `ContactHelper`, `SmsHelper` | Inbound handling, number lookup, `unsubscribe()` | [code: app/bundles/SmsBundle/Helper/ReplyHelper.php:31-89 @7.x] [code: app/bundles/SmsBundle/Helper/SmsHelper.php:30-69 @7.x] |
| `Broadcast\BroadcastExecutioner`, `BroadcastQuery`, `BroadcastResult` | Segment SMS | [code: app/bundles/SmsBundle/Broadcast/BroadcastExecutioner.php:28-79 @7.x] |
| `NotificationBundle\Model\NotificationModel` (final) | CRUD; mobile form when action URL has `mobile_` | [code: app/bundles/NotificationBundle/Model/NotificationModel.php:64-316 @7.x] |
| `Api\OneSignalApi` (`mautic.notification.api`), `Api\AbstractNotificationApi` | OneSignal HTTP client | [code: app/bundles/NotificationBundle/Api/OneSignalApi.php:16-168 @7.x] |
| `Helper\NotificationHelper` (`mautic.helper.notification`) | OneSignal init JS | [code: app/bundles/NotificationBundle/Helper/NotificationHelper.php:33-196 @7.x] |
| `Integration\OneSignalIntegration` | Keys and features | [code: app/bundles/NotificationBundle/Integration/OneSignalIntegration.php:25-101 @7.x] |
| `MauticFocusBundle\Model\FocusModel` | JS generation, content, stats | [code: plugins/MauticFocusBundle/Model/FocusModel.php:74-436 @7.x] |
| `Helper\TokenHelper` (`mautic.focus.helper.token`) | `{focus=ID}` regex | [code: plugins/MauticFocusBundle/Helper/TokenHelper.php:12-56 @7.x] |
| `MauticSocialBundle\Model\MonitoringModel`, `TweetModel`, `PostCountModel` | Monitors, tweet stats | [code: plugins/MauticSocialBundle/Model/MonitoringModel.php:36-141 @7.x] [code: plugins/MauticSocialBundle/Model/TweetModel.php:86-216 @7.x] |
| `Helper\TwitterCommandHelper`, `Helper\CampaignEventHelper` | Tweets → Contacts; tweet action | [code: plugins/MauticSocialBundle/Helper/TwitterCommandHelper.php:82-285 @7.x] |
| `Integration\{Social,Twitter,Facebook,Instagram,Foursquare}Integration` | Legacy social OAuth integrations | [code: plugins/MauticSocialBundle/Integration/TwitterIntegration.php:9,60-86 @7.x] |

## 3. Events

### ChannelEvents (`app/bundles/ChannelBundle/ChannelEvents.php`)
| Constant | Name | Event | Dispatched / listened |
|---|---|---|---|
| `ADD_CHANNEL` | `mautic.add_channel` | `ChannelEvent` | `ChannelListHelper:108`, `MessageApiController:84`; listeners in Email, Sms, Social, Notification, DynamicContent [code: app/bundles/ChannelBundle/ChannelEvents.php:16 @7.x] |
| `CHANNEL_BROADCAST` | `mautic.channel_broadcast` | `ChannelBroadcastEvent` | broadcast command, A/B winner; Email and SMS `BroadcastSubscriber` [code: app/bundles/ChannelBundle/ChannelEvents.php:25 @7.x] |
| `MESSAGE_QUEUED` | `mautic.message_queued` | `MessageQueueEvent` | queue save; no listeners [code: app/bundles/ChannelBundle/ChannelEvents.php:34 @7.x] |
| `PROCESS_MESSAGE_QUEUE` | `mautic.process_message_queue` | `MessageQueueProcessEvent` | no core listeners [code: app/bundles/ChannelBundle/ChannelEvents.php:43 @7.x] |
| `PROCESS_MESSAGE_QUEUE_BATCH` | `mautic.process_message_queue_batch` | `MessageQueueBatchProcessEvent` | Email and SMS `MessageQueueSubscriber` [code: app/bundles/ChannelBundle/ChannelEvents.php:52 @7.x] |
| `ON_CAMPAIGN_BATCH_ACTION` | `mautic.channel.on_campaign_batch_action` | `PendingEvent` | action `message.send` [code: app/bundles/ChannelBundle/ChannelEvents.php:61 @7.x] |
| `MESSAGE_PRE/POST_SAVE`, `MESSAGE_PRE/POST_DELETE` | `mautic.message_*` | `MessageEvent` | audit log [code: app/bundles/ChannelBundle/ChannelEvents.php:71-101 @7.x] |

### SmsEvents (`app/bundles/SmsBundle/SmsEvents.php`)
| Constant | Name | Event | Notes |
|---|---|---|---|
| `TOKEN_REPLACEMENT` | `mautic.sms_token_replacement` | `TokenReplacementEvent` | `SmsSubscriber` [code: app/bundles/SmsBundle/SmsEvents.php:20 @7.x] |
| `SMS_ON_SEND` | `mautic.sms_on_send` | `SmsSendEvent` | before tokens; webhook [code: app/bundles/SmsBundle/SmsEvents.php:30 @7.x] |
| `SMS_PRE/POST_SAVE/DELETE` | `mautic.sms_*` | `SmsEvent` | audit [code: app/bundles/SmsBundle/SmsEvents.php:40-70 @7.x] |
| `ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.sms.on_campaign_trigger_action` | — | never dispatched, deprecated [code: app/bundles/SmsBundle/SmsEvents.php:78-82 @7.x] |
| `ON_CAMPAIGN_TRIGGER_BATCH_ACTION` | `mautic.sms.on_campaign_trigger_batch_action` | `PendingEvent` | `sms.send_text_sms` [code: app/bundles/SmsBundle/SmsEvents.php:92 @7.x] |
| `ON_REPLY` | `mautic.sms.on_reply` | `ReplyEvent` | Stop, Reply, CampaignReply subscribers [code: app/bundles/SmsBundle/SmsEvents.php:101 @7.x] |
| `ON_SMS_TOKENS_BUILD` | `mautic.sms.on_tokens_build` | `TokensBuildEvent` | builder tokens [code: app/bundles/SmsBundle/SmsEvents.php:117 @7.x] |
| `ON_CAMPAIGN_REPLY` | `mautic.sms.on_campaign_reply` | `DecisionEvent` | `sms.reply` [code: app/bundles/SmsBundle/SmsEvents.php:126 @7.x] |
| `DNC_FILTER_CONTACTS_ON_SEND`, `QUEUE_FILTER_CONTACTS_ON_SEND`, `FILTER_CONTACTS_ON_SEND` | `mautic.sms.*_filter_contacts_on_send` | `DncEvent`, `QueueEvent`, `FilterEvent` | `SendSmsSubscriber` [code: app/bundles/SmsBundle/SmsEvents.php:136-156 @7.x] |

### NotificationEvents (`app/bundles/NotificationBundle/NotificationEvents.php`)
| Constant | Name | Notes |
|---|---|---|
| `TOKEN_REPLACEMENT` | `mautic.notification_token_replacement` | [code: app/bundles/NotificationBundle/NotificationEvents.php:20 @7.x] |
| `NOTIFICATION_ON_FORM_ACTION_SEND` | `mautic.notification_form_action_send` | never dispatched [code: app/bundles/NotificationBundle/NotificationEvents.php:31 @7.x] |
| `NOTIFICATION_ON_SEND` | `mautic.notification_on_send` | `NotificationSendEvent`, no core listener [code: app/bundles/NotificationBundle/NotificationEvents.php:41 @7.x] |
| CRUD `NOTIFICATION_PRE/POST_SAVE/DELETE` | `mautic.notification_*` | audit [code: app/bundles/NotificationBundle/NotificationEvents.php:51-81 @7.x] |
| `ON_CAMPAIGN_BATCH_ACTION` | `mautic.notification.on_batch_trigger_action` | web and mobile send [code: app/bundles/NotificationBundle/NotificationEvents.php:91 @7.x] |
| `ON_CAMPAIGN_TRIGGER_CONDITION` | `mautic.notification.on_campaign_trigger_notification` | `notification.has.active` [code: app/bundles/NotificationBundle/NotificationEvents.php:101 @7.x] |

### FocusEvents (`plugins/MauticFocusBundle/FocusEvents.php`)
| Constant | Name | Notes |
|---|---|---|
| `PRE/POST_SAVE`, `PRE/POST_DELETE` | `mautic.focus_*` | audit [code: plugins/MauticFocusBundle/FocusEvents.php:19-46 @7.x] |
| `TOKEN_REPLACEMENT` | `mautic.focus_token_replacement` | clickthrough `focus_id` [code: plugins/MauticFocusBundle/FocusEvents.php:55 @7.x] |
| `ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.focus.on_campaign_trigger_action` | `focus.show` (legacy single action) [code: plugins/MauticFocusBundle/FocusEvents.php:65 @7.x] |
| `FOCUS_ON_VIEW` | `mautic.focus.on_view` | `FocusViewEvent`, no core listener [code: plugins/MauticFocusBundle/FocusEvents.php:75 @7.x] |
| `FocusEventTypes::FOCUS_ON_VIEW/ON_CLICK` | `focus.on_view` / `focus.on_click` | timeline types [code: plugins/MauticFocusBundle/FocusEventTypes.php:14,21 @7.x] |

### SocialEvents (`plugins/MauticSocialBundle/SocialEvents.php`)
`MONITOR_PRE/POST_SAVE/DELETE`, `MONITOR_POST_PROCESS` (`SocialMonitorEvent`), `TWEET_PRE/POST_SAVE/DELETE` have no core listeners. `ON_CAMPAIGN_TRIGGER_ACTION` is used by `twitter.tweet` [code: plugins/MauticSocialBundle/SocialEvents.php:20-110 @7.x].

## 4. Routes, controllers and UI

| Route | Path | Controller | Source |
|---|---|---|---|
| `mautic_message_index/_action/_contacts` | `/messages/...` | `MessageController` (AbstractStandardFormController) | [code: app/bundles/ChannelBundle/Config/config.php:8-19 @7.x] |
| `mautic_channel_batch_contact_set/_view` | `/channels/batch/contact/{set,view}` | `BatchContactController` | [code: app/bundles/ChannelBundle/Config/config.php:20-27 @7.x] |
| API `messages` | `/api/messages` | `Api\MessageApiController` (route id `mautic_api_messagetandard`, sic) | [code: app/bundles/ChannelBundle/Config/config.php:30-35 @7.x] |
| `mautic_sms_index/_action/_contacts` | `/sms/...` | `SmsController` | [code: app/bundles/SmsBundle/Config/config.php:8-19 @7.x] |
| `mautic_sms_callback` | `/sms/{transport}/callback` | `ReplyController::callbackAction` | [code: app/bundles/SmsBundle/Config/config.php:22-25 @7.x] |
| `mautic_receive_sms` (deprecated) | `/sms/receive` | same, transport=twilio | [code: app/bundles/SmsBundle/Config/config.php:26-33 @7.x] |
| API `smses`, `mautic_api_smses_send` | `/api/smses`, `/api/smses/{id}/contact/{contactId}/send` (any method) | `SmsApiController` | [code: app/bundles/SmsBundle/Config/config.php:36-45 @7.x] |
| notifications / mobile_notifications | `/notifications/...`, `/mobile_notifications/...` | `NotificationController`, `MobileNotificationController` | [code: app/bundles/NotificationBundle/Config/config.php:8-31 @7.x] |
| public push | `/notification/receive` (broken), `/notification/subscribe`, `/notification`, `/OneSignalSDKWorker.js`, `/OneSignalSDKUpdaterWorker.js`, `/manifest.json`, `/notification/appcallback` | `NotificationApiController`, `PopupController`, `JsController`, `AppCallbackController` | [code: app/bundles/NotificationBundle/Config/config.php:34-63 @7.x] |
| API `notifications` | `/api/notifications` | standard entity | [code: app/bundles/NotificationBundle/Config/config.php:66-71 @7.x] |
| focus | `/focus/...`; public `/focus/{id}.js`, `/focus/{id}/viewpixel.gif` | `FocusController`, `PublicController` | [code: plugins/MauticFocusBundle/Config/config.php:13-30 @7.x] |
| API focus | `/api/focus`, `POST /api/focus/{id}/js`; v2 `/focus_items` | `FocusApiController` | [code: plugins/MauticFocusBundle/Config/config.php:33-43 @7.x] |
| social | `/monitoring/...`, `/tweets/...`, `/social/generate/{formName}.js`; API `/api/tweets` | `MonitoringController`, `TweetController`, `JsController`, `TweetApiController` | [code: plugins/MauticSocialBundle/Config/config.php:13-46 @7.x] |

AJAX actions: `channel:cancelQueuedMessageEvent` and `channel:getMarketingMessageSendToDncStatus` [code: app/bundles/ChannelBundle/Controller/AjaxController.php:33-76 @7.x]; `sms:getSmsCountStats` and `sms:getBuilderTokens` [code: app/bundles/SmsBundle/Controller/AjaxController.php:36-115 @7.x]; `plugin:focus:generatePreview`, `getViewsCount` and `getClickThroughCount` [code: plugins/MauticFocusBundle/Controller/AjaxController.php:24-121 @7.x]; `plugin:mauticSocial:getNetworkForm` [code: plugins/MauticSocialBundle/Controller/AjaxController.php:17-50 @7.x].

Menu gating: SMS needs Twilio [code: app/bundles/SmsBundle/Config/config.php:51-63 @7.x]; push needs OneSignal (and the `mobile` feature for mobile) [code: app/bundles/NotificationBundle/Config/config.php:77-105 @7.x]; social needs Twitter [code: plugins/MauticSocialBundle/Config/config.php:51-76 @7.x].

## 5. Console commands
| Command | File | Notes |
|---|---|---|
| `mautic:broadcasts:send` | `app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php` | ModeratedCommand; `--channel --id --min-contact-id --max-contact-id --limit --batch --thread-id --max-threads` [code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:22-183 @7.x] |
| `mautic:messages:send` (aliases `mautic:campaigns:messagequeue`, `mautic:campaigns:messages`) | `app/bundles/ChannelBundle/Command/ProcessMarketingMessagesQueueCommand.php` | `--channel --channel-id --message-id --limit --batch(50)` [code: app/bundles/ChannelBundle/Command/ProcessMarketingMessagesQueueCommand.php:16-98 @7.x] |
| `mautic:social:monitoring` | `plugins/MauticSocialBundle/Command/MauticSocialMonitoringCommand.php` | `--mid --batch-size (required) --query-count(100)`; no lock [code: plugins/MauticSocialBundle/Command/MauticSocialMonitoringCommand.php:13-35 @7.x] |
| `social:monitor:twitter:hashtags` / `:mentions` | `plugins/MauticSocialBundle/Command/MonitorTwitter*Command.php` | `--mid` (required) `--max-runs(5) --query-count --show-posts --show-stats` [code: plugins/MauticSocialBundle/Command/MonitorTwitterBaseCommand.php:66-101 @7.x] |

## 6. Configuration parameters
| Parameter | Default | Live? | Source |
|---|---|---|---|
| `sms_transport` | `mautic.sms.twilio.transport` | yes (Configuration → SMS Settings) | [code: app/bundles/SmsBundle/Config/config.php:70-79 @7.x] [code: app/bundles/SmsBundle/Form/Type/ConfigType.php:39-47 @7.x] |
| `sms_disable_trackable_urls` | false | yes | [code: app/bundles/SmsBundle/Helper/SmsHelper.php:66-69 @7.x] |
| `sms_frequency_number` / `sms_frequency_time` | 0 / DAY | yes (not in UI) | [code: app/bundles/SmsBundle/Config/config.php:75-76 @7.x] |
| `sms_enabled`, `sms_username`, `sms_password`, `sms_messaging_service_sid` | — | no | [code: app/bundles/SmsBundle/Config/config.php:70-79 @7.x] |
| `shortener_sms_enable` (Core) | — | yes | [code: app/bundles/SmsBundle/EventListener/SmsSubscriber.php:95 @7.x] |
| `notification_*`, `welcomenotification_enabled` | — | no | [code: app/bundles/NotificationBundle/Config/config.php:112-125 @7.x] |
| `gcm_sender_id` | `482941778795` (inline fallback `446150739532`) | yes, `/manifest.json` | [code: app/bundles/NotificationBundle/Controller/JsController.php:16 @7.x] |
| `campaign_send_notification_to_author`, `campaign_notification_email_addresses`, `webhook_send_notification_to_author`, `webhook_notification_email_addresses` | true/null | yes, but about emailing users, not push | [code: app/bundles/NotificationBundle/Form/Type/NotificationConfigType.php:23-83 @7.x] |
| `website_snapshot_url`, `website_snapshot_key` | — | no | [code: plugins/MauticFocusBundle/Config/config.php:65-68 @7.x] |
| `cached_data_timeout` (Core) | — | focus counters | [code: plugins/MauticFocusBundle/Controller/AjaxController.php:53,97 @7.x] |
| `twitter_handle_field` | `twitter` | monitoring only | [code: plugins/MauticSocialBundle/Config/config.php:87-93 @7.x] |

## 7. Permissions
| Class | Keys | Source |
|---|---|---|
| `ChannelPermissions` | `channel:categories:*`, `channel:messages:{viewown..full}` | [code: app/bundles/ChannelBundle/Security/Permissions/ChannelPermissions.php:8-31 @7.x] |
| `SmsPermissions` | `sms:categories:*`, `sms:smses:*`; send API also needs Contact edit | [code: app/bundles/SmsBundle/Security/Permissions/SmsPermissions.php:8-30 @7.x] [code: app/bundles/SmsBundle/Controller/Api/SmsApiController.php:78-82 @7.x] |
| `NotificationPermissions` | `notification:notifications:*`, `notification:mobile_notifications:*` | [code: app/bundles/NotificationBundle/Security/Permissions/NotificationPermissions.php:8-32 @7.x] |
| `FocusPermissions` | `focus:items:*` | [code: plugins/MauticFocusBundle/Security/Permissions/FocusPermissions.php:8-30 @7.x] |
| `MauticSocialPermissions` | `mauticSocial:monitoring:{view,edit,create,delete,publish,full}` (no own/other), `mauticSocial:tweets:*` | [code: plugins/MauticSocialBundle/Security/Permissions/MauticSocialPermissions.php:10-30 @7.x] |

## 8. Extension points
- New channel: `ADD_CHANNEL` → `addChannel('x', [MessageModel::CHANNEL_FEATURE => [campaignAction, campaignDecisionsSupported, lookupFormType|propertiesFormType, repository, nameColumn, lookupOptions], LeadModel::CHANNEL_FEATURE => [], ReportModel::CHANNEL_FEATURE => ['table' => …]])` [code: app/bundles/ChannelBundle/Event/ChannelEvent.php:14-80 @7.x].
- Broadcast: `CHANNEL_BROADCAST` + `checkContext()` + `setResults()`; template `app/bundles/SmsBundle/Broadcast/BroadcastExecutioner.php` [code: app/bundles/ChannelBundle/Event/ChannelBroadcastEvent.php:92-99 @7.x].
- Queue drain: `PROCESS_MESSAGE_QUEUE_BATCH`; template `app/bundles/SmsBundle/EventListener/MessageQueueSubscriber.php` [code: app/bundles/SmsBundle/EventListener/MessageQueueSubscriber.php:28-73 @7.x].
- SMS transport: tag `mautic.sms_transport` with `alias` and `integrationAlias`; callback handler: tag `mautic.sms_callback_handler` [code: app/bundles/SmsBundle/DependencyInjection/Compiler/SmsTransportPass.php:13-29 @7.x].
- Push provider: extend `AbstractNotificationApi` and re-alias `mautic.notification.api`; the browser JS stays OneSignal-specific [code: app/bundles/NotificationBundle/Config/services.php:35 @7.x].
- Focus: `TOKEN_REPLACEMENT`, `FOCUS_ON_VIEW`; Social: `MONITOR_POST_PROCESS` [code: plugins/MauticFocusBundle/FocusEvents.php:55,75 @7.x].
- Report contexts: `message.channel`, `mobile_notifications`, `mobile_notifications.stats`, `focus_stats`, `focus_leads` [code: app/bundles/ChannelBundle/EventListener/ReportSubscriber.php:17 @7.x] [code: plugins/MauticFocusBundle/EventListener/ReportSubscriber.php:14-16 @7.x].

## 9. Cross-bundle touch points
- Channel ordering and frequency: `app/bundles/LeadBundle/Entity/Lead.php:1754-1872`, `app/bundles/LeadBundle/Entity/FrequencyRuleRepository.php:23-237` [code: app/bundles/LeadBundle/Entity/FrequencyRuleRepository.php:23-237 @7.x].
- Email side of broadcasts and queue: `app/bundles/EmailBundle/EventListener/{BroadcastSubscriber,MessageQueueSubscriber,ChannelSubscriber}.php` [code: app/bundles/EmailBundle/EventListener/BroadcastSubscriber.php:28 @7.x].
- Focus campaign delivery: `app/bundles/PageBundle/Helper/TrackingHelper.php:42-90`, `app/bundles/PageBundle/Controller/PublicController.php:427-442`, `app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:305-311` [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:305-311 @7.x].
- Integration credentials: `app/bundles/PluginBundle/Integration/AbstractIntegration.php:330,421` [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:421 @7.x].
