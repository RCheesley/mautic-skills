# Mautic Emails - code map (7.x)

All paths are repo-relative at commit 419a08a9b35 (7.2.1). EmailBundle root: `app/bundles/EmailBundle/`.

## Contents
1. Entities and tables
2. Services and models
3. Events
4. Routes and controllers
5. Console commands
6. Configuration parameters
7. Permissions
8. Tests and fixtures
9. Extension points

## 1. Entities and tables

| Entity | Table | Key facts | Source |
|---|---|---|---|
| `Email` | `emails` | `name`, `subject` (<=190), `preheader_text` (<=130), `from_address`, `from_name`, `reply_to_address`, `bcc_address`, `use_owner_as_mailer`, `send_to_dnc`, `template`, `content` (legacy slots), `utm_tags`, `plain_text`, `custom_html`, `email_type` (`template`/`list`), `publish_up/down`, `continue_sending`, `read_count`, `sent_count`, `variant_sent_count`, `variant_read_count`, `revision`, `headers` (JSON), `public_preview`, `settings` (JSON), `uuid`, `version` (optimistic lock), variant/translation/dynamic-content columns | [code: app/bundles/EmailBundle/Entity/Email.php:366-470 @7.x] |
| `Email` relations | `email_list_xref`, `email_list_excluded`, `email_assets_xref`, `email_projects_xref` | Included Segments, excluded Segments, Asset attachments, projects; `unsubscribeform_id`, `preference_center_id` (SET NULL) | [code: app/bundles/EmailBundle/Entity/Email.php:410-468 @7.x] |
| `Stat` | `email_stats` | `email_id`, `lead_id`, `list_id` (all SET NULL), `email_address`, `date_sent`, `is_read`, `is_failed`, `viewed_in_browser`, `date_read`, `tracking_hash`, `retry_count`, `source`, `source_id`, `tokens`, `copy_id`, `open_count`, `last_opened`, `open_details` (max 1000); generated column `generated_sent_date` | [code: app/bundles/EmailBundle/Entity/Stat.php:125-220 @7.x] [code: app/bundles/EmailBundle/EventListener/GeneratedColumnSubscriber.php:21-28 @7.x] |
| `StatDevice` | `email_stats_devices` | One row per tracked open (`device_id`, `stat_id`, `ip_id`, `date_opened`) | [code: app/bundles/EmailBundle/Entity/StatDevice.php:36-57 @7.x] |
| `Copy` | `email_copies` | MD5 id, `body`, `body_text`, `subject` - rendered content for webview | [code: app/bundles/EmailBundle/Entity/Copy.php:33-52 @7.x] |
| `EmailReply` | `email_stat_replies` | UUID, `stat_id` (CASCADE), `date_replied`, `message_id` | [code: app/bundles/EmailBundle/Entity/EmailReply.php:17-41 @7.x] |
| `EmailDraft` | `emails_draft` | `email_id` (1:1), `html`, `template`, `public_preview` | [code: app/bundles/EmailBundle/Entity/EmailDraft.php:27-47 @7.x] |
| (LeadBundle) `DoNotContact` | `lead_donotcontact` | `channel` `email`, `reason` 1 UNSUBSCRIBED / 2 BOUNCED / 3 MANUAL, `channel_id`, `comments` | [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-91 @7.x] |
| Other tables used | `message_queue`, `lead_frequencyrules`, `lead_lists_leads`, `lead_categories`, `page_redirects`, `channel_url_trackables`, `page_hits`, `messenger_messages` (Doctrine transport) | | [code: app/bundles/PageBundle/Entity/Hit.php:141-169 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#how-to-enable-the-queuing] |

## 2. Services and models

| Class | Path | Role |
|---|---|---|
| `EmailModel` (`mautic.email.model.email`) | `app/bundles/EmailBundle/Model/EmailModel.php` | Save/delete, `getPendingLeads`, `sendEmailToLists`, `sendEmail`, `sendEmailToUser`, `sendSampleEmailToUser`, `hitEmail`, DNC helpers, stats, A/B helpers |
| `SendEmailToContact` | `app/bundles/EmailBundle/Model/SendEmailToContact.php` | Per-contact send loop, stats, failure handling, bad-address DNC |
| `SendEmailToUser` | `app/bundles/EmailBundle/Model/SendEmailToUser.php` | Send-to-user actions |
| `TransportCallback` | `app/bundles/EmailBundle/Model/TransportCallback.php` | Webhook bounce/complaint entry point |
| `EmailStatModel` | `app/bundles/EmailBundle/Model/EmailStatModel.php` | Stat batch save with pre/post events |
| `SendWinnerService`, `EmailStatus` | `app/bundles/EmailBundle/Model/AbTest/` | A/B winner sending and status |
| `MailHelper` (`mautic.helper.mailer`) | `app/bundles/EmailBundle/Helper/MailHelper.php` | Message building, tokens, headers, pixel, stats/copies, batch mode, send |
| `FromEmailHelper` | `app/bundles/EmailBundle/Helper/FromEmailHelper.php` | Owner-as-mailer, tokenized From, signature |
| `PlainTextHelper` | `app/bundles/EmailBundle/Helper/PlainTextHelper.php` | HTML to text |
| `EmailValidator` | `app/bundles/EmailBundle/Helper/EmailValidator.php` | Address validation + `ON_EMAIL_VALIDATION` |
| `BotRatioHelper` | `app/bundles/EmailBundle/Helper/BotRatioHelper.php` | Bot heuristic for opens and clicks |
| `MailHashHelper`, `EmailAddressLinkMatcher` | `app/bundles/EmailBundle/Helper/` | HMAC for unsubscribe links |
| `EmailDefaultsHelper` | `app/bundles/EmailBundle/Helper/EmailDefaultsHelper.php` | Default UTM, default Preference Centre |
| `TransportFactory`, `InvalidTransport`, `TokenTransportInterface`, `BounceProcessorInterface`, `UnsubscriptionProcessorInterface` | `app/bundles/EmailBundle/Mailer/Transport/` | Transport contracts |
| `MauticMessage` | `app/bundles/EmailBundle/Mailer/Message/MauticMessage.php` | Symfony `Email` subclass with per-recipient metadata |
| `Fetcher`, `Mailbox`, processors | `app/bundles/EmailBundle/MonitoredEmail/` | IMAP bounce/unsubscribe/reply/FBL |
| Stat helpers (`mautic.email_stat_helper`) | `app/bundles/EmailBundle/Stats/` | sent/opened/failed/clicked/bounced/unsubscribed series |
| `EmailHitNotificationHandler` | `app/bundles/MessengerBundle/MessageHandler/EmailHitNotificationHandler.php` | Async open processing |
| `MessageQueueModel` | `app/bundles/ChannelBundle/Model/MessageQueueModel.php` | Frequency-rule queueing |

Source for this table: [code: app/bundles/EmailBundle/Config/services.php:46-68 @7.x] plus the files listed.

## 3. Events (`app/bundles/EmailBundle/EmailEvents.php`)

| Constant (name) | Event class | Dispatched at | Notes |
|---|---|---|---|
| `EMAIL_ON_BUILD` (`mautic.email_on_build`) | `EmailBuilderEvent` | `Model/EmailModel.php:566-567` | Register tokens, A/B criteria |
| `EMAIL_ON_SEND` (`mautic.email_on_send`) | `EmailSendEvent` | `Helper/MailHelper.php:1497-1498` | Render per recipient |
| `EMAIL_ON_DISPLAY` (`mautic.email_on_display`) | `EmailSendEvent` | `Model/EmailModel.php:1754`, `:2252` | Previews, internal sends, dynamic content |
| `EMAIL_PRE_SEND` (`mautic.email_pre_send`) | `EmailSendEvent` | `Helper/MailHelper.php:2091-2108` | Skip/fatal/addError |
| `EMAIL_ON_OPEN` (`mautic.email_on_open`) | `EmailOpenEvent` | `Model/EmailModel.php:496-499` | Campaign, points, webhooks |
| `EMAIL_ON_REPLY` | `EmailReplyEvent` | `MonitoredEmail/Processor/Reply.php:121-130` | `email.reply` decision |
| `EMAIL_PRE_SAVE` / `POST_SAVE` / `PRE_DELETE` / `POST_DELETE` / `ON_TOGGLE_PUBLISH` | `EmailEvent` | `Model/EmailModel.php:384-411` | Variant sync, audit log, drafts |
| `ON_EMAIL_EDIT_SUBMIT` | `EmailEditSubmitEvent` | `Controller/EmailController.php:789-797` | Drafts, GrapesJS |
| `MONITORED_EMAIL_CONFIG`, `EMAIL_PRE_FETCH`, `EMAIL_PARSE` | `MonitoredEmailEvent`, `ParseEmailEvent` | `MonitoredEmail/Fetcher.php:40,68` | Inbox folders |
| `ON_TRANSPORT_WEBHOOK` | `TransportWebhookEvent` | `Controller/PublicController.php:539-540` | No core listener |
| `ON_EMAIL_VALIDATION` | `EmailValidationEvent` | `Helper/EmailValidator.php:85-88` | `setInvalid()` |
| `ON_CAMPAIGN_BATCH_ACTION`, `ON_CAMPAIGN_TRIGGER_DECISION`, `ON_CAMPAIGN_TRIGGER_CONDITION` | `PendingEvent`, `CampaignExecutionEvent` | CampaignBundle | `email.send`, `email.send.to.user`, decisions, `email.validate.address` |
| `ON_DETERMINE_OPEN_RATE_WINNER`, `ON_DETERMINE_CLICKTHROUGH_RATE_WINNER` | `DetermineWinnerEvent` | CoreBundle `AbTestResultService` | A/B winner |
| `ON_EMAIL_STAT_PRE_SAVE` / `POST_SAVE` | `EmailStatEvent` | `Model/EmailStatModel.php:33,37` | No core listener |
| `ON_SENT_EMAIL_TO_USER`, `ON_EMAIL_ADDRESS_TOKEN_REPLACEMENT`, `TOKEN_REPLACEMENT` | various | see source | |
| `EMAIL_FAILED`, `EMAIL_RESEND` | `QueueEmailEvent` | never dispatched in 7.x | legacy spool |
| `ON_CAMPAIGN_TRIGGER_ACTION` | - | deprecated 2.13.0, unused | |

Paths in the table are relative to `app/bundles/EmailBundle/`. [code: app/bundles/EmailBundle/EmailEvents.php:238-248 @7.x]

## 4. Routes and controllers

Defined in [code: app/bundles/EmailBundle/Config/config.php:6-119 @7.x].

| Route | Path | Controller |
|---|---|---|
| `mautic_email_index` | `/emails/{page}` | `EmailController::indexAction` |
| `mautic_email_action` | `/emails/{objectAction}/{objectId}` | new, edit, view, clone, cloneWithTranslations, delete, builder, abtest, winner, send, scheduleSend, sendExample |
| `mautic_email_contacts` | `/emails/view/{objectId}/contact/{page}` | `contactsAction` |
| `mautic_abtest_generate` | `/email/abtest/generate/{objectId}` | `ABTestController::generateABTestAction` |
| `mautic_email_tracker` | `/email/{idHash}.gif` | `PublicController::trackingImageAction` |
| `mautic_email_webview` | `/email/view/{idHash}` | `PublicController::indexAction` |
| `mautic_email_unsubscribe` | `/email/unsubscribe/{idHash}/{urlEmail}/{secretHash}` | GET page / POST One-Click |
| `mautic_email_unsubscribe_all` | `/email/dnc/{idHash}/{urlEmail}/{secretHash}` | `unsubscribeAllAction` |
| `mautic_email_resubscribe` | `/email/resubscribe/{idHash}/{urlEmail}/{secretHash}` | `resubscribeAction` |
| `mautic_email_validate_email_form` | `/email/validate/{action}/{secretHash}/{idHash}` | `validateEmailAction` |
| `mautic_mailer_transport_callback` | `/mailer/callback` | `mailerCallbackAction` |
| `mautic_email_preview` / `_download` | `/email/preview/{objectId}/{objectType}`, `/email/download/preview/...` | preview / download |
| `mautic_plugin_tracker` | `/plugin/{integration}/tracking.gif` | Outlook/Gmail plugin opens |
| API `mautic_api_emailstandard` | `/api/emails`, `/api/emails/{id}`, `/new`, `/{id}/edit`, `/{id}/delete`, `/batch/*` | `Api/EmailApiController` |
| API `mautic_api_sendemail` | `POST /api/emails/{id}/send` | Segment send (`lists`, `limit`, `batch`) |
| API `mautic_api_sendcontactemail` | `POST /api/emails/{id}/contact/{leadId}/send` | `tokens`, `assetAttachments` |
| API `mautic_api_reply` | `POST /api/emails/reply/{trackingHash}` | Create reply (201) |
| AJAX `email:*` | `/s/ajax?action=email:<name>` | `sendBatch`, `getEmailCountStats`, `getEmailDeliveredCount`, `generatePlaintText`, `sendTestEmail`, `testMonitoredEmailServerConnection`, `heatmap`, `getEmailUsages`, ... [code: app/bundles/EmailBundle/Controller/AjaxController.php:43-347 @7.x] |

Twig views: `app/bundles/EmailBundle/Resources/views/` (`Email/*`, `Send/*`, `Lead/preference_options.html.twig`, `Tokens/tokens_help_bundle.html.twig`).

## 5. Console commands

| Command | File | Notes |
|---|---|---|
| `mautic:broadcasts:send` | `app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:22-184` | `--channel`, `--id`, `--min-contact-id`, `--max-contact-id`, `--limit` (100), `--batch` (50), `--thread-id`, `--max-threads` |
| `mautic:email:sendwinner` | `app/bundles/EmailBundle/Command/SendWinnerEmailCommand.php:21-77` | `--id`; exit 1 = retry later |
| `mautic:email:fetch` (alias `mautic:emails:fetch`) | `app/bundles/EmailBundle/Command/ProcessFetchEmailCommand.php:16-59` | `--message-limit`; no lock |
| `mautic:messages:send` | `app/bundles/ChannelBundle/Command/ProcessMarketingMessagesQueueCommand.php:17-52` | frequency-rule queue |
| `messenger:consume email` / `hit` | Symfony; routing `app/config/config.php:102-125` | only with non-`sync://` DSNs |
| `mautic:emails:send` | does not exist since 5.0 | [code: UPGRADE-5.0.md:16 @7.x] |

## 6. Configuration parameters

EmailBundle [code: app/bundles/EmailBundle/Config/config.php:137-224 @7.x]:

| Parameter | Default | Controls |
|---|---|---|
| `mailer_dsn` | `smtp://localhost:1025` | Symfony Mailer transport |
| `mailer_from_name` / `mailer_from_email` | `Mautic` / `email@yoursite.com` | System From |
| `mailer_reply_to_email` | null | Global Reply-To |
| `mailer_return_path` | null | Return-Path without a bounce mailbox |
| `mailer_is_owner` | false | Default owner-as-mailer |
| `mailer_address_length_limit` | 320 | Drop display name when exceeded |
| `mailer_append_tracking_pixel` | true | Open tracking |
| `mailer_convert_embed_images` | false | CID images |
| `mailer_custom_headers` | `[]` | Global headers |
| `mailer_memory_msg_limit` | 100 | UI send batch |
| `minify_email_html` | false | Minify on send |
| `disable_trackable_urls` | false | Click tracking off |
| `disable_unsubscribe_link_header` | false | No List-Unsubscribe |
| `validate_unsubscribe_emails` | true | Confirm-address page |
| `unsubscribe_text`, `webview_text`, `unsubscribe_message`, `resubscribe_message`, `default_signature_text` | null | Token/page texts (`\|URL\|`, `\|EMAIL\|`, `\|FROM_NAME\|`) |
| `email_default_preference_center_id` | null | Fallback Preference Centre |
| `show_contact_preferences`, `show_contact_frequency`, `show_contact_pause_dates`, `show_contact_preferred_channels`, `show_contact_categories`, `show_contact_segments` | false | Preference Centre |
| `email_frequency_number` / `email_frequency_time` | 0 / `DAY` | Global frequency rule |
| `email_default_utm_source/medium/campaign/content` | null | Default UTM for new emails |
| `monitored_email` | general + bounces/unsubscribes/replies | IMAP |
| `email_draft_enabled` | false | Drafts (local.php only) |
| `theme_email_default` | `blank` | Default theme |
| `bot_helper_bot_ratio_threshold` / `_time_email_threshold` / `_blocked_user_agents` / `_blocked_ip_addresses` | 0.6 / 2 / samples / `[]` | Bot filter (env `MAUTIC_BOT_HELPER_*`) |
| `smime_signing_enabled` / `smime_certificates_path` | false / `%kernel.project_dir%/var/smime_certificates` | S/MIME |

Messenger [code: app/bundles/MessengerBundle/Config/config.php:6-14 @7.x]: `messenger_dsn_email` (`sync://`), `messenger_dsn_hit` (`sync://`), `messenger_dsn_failed` (null -> `null://`), `messenger_retry_strategy_max_retries` 3, `_delay` 1000, `_multiplier` 2.0, `_max_delay` 0. WebhookBundle: `webhook_email_details` (true) [code: app/bundles/WebhookBundle/Config/config.php:56 @7.x].

## 7. Permissions

`email:categories:*` and `email:emails:{viewown,viewother,editown,editother,create,deleteown,deleteother,publishown,publishother,full}` plus `email:emails:sendtodnc` [code: app/bundles/EmailBundle/Security/Permissions/EmailPermissions.php:18-55 @7.x]. Without publish permission new emails are forced unpublished and publish fields are disabled [code: app/bundles/EmailBundle/Form/Type/EmailType.php:254-267 @7.x]. `sendToDnc` is read-only without `sendtodnc` [code: app/bundles/EmailBundle/Form/Type/EmailType.php:198-199 @7.x]. Contact data in previews needs `lead:leads:viewown|viewother` [code: app/bundles/EmailBundle/Controller/PublicController.php:579-590 @7.x].

## 8. Tests and fixtures

- Directory: `app/bundles/EmailBundle/Tests/` (unit: `PHPUnit\Framework\TestCase`; functional: `Mautic\CoreBundle\Test\MauticMysqlTestCase`).
- Fixture helper: `app/bundles/EmailBundle/Tests/Functional/Fixtures/EmailFixturesHelper.php`.
- Doctrine fixture: `app/bundles/EmailBundle/DataFixtures/ORM/LoadEmailData.php`.
- Test transports: `Tests/Helper/Transport/{BatchTransport,BcInterfaceTokenTransport,SmtpTransport}.php`, `Tests/MonitoredEmail/Transport/TestTransport.php`; sample bounce/FBL mails in `Tests/_data/`.
- Messenger tests: `app/bundles/MessengerBundle/Tests/MessageHandler/EmailHitNotificationHandlerTest.php`.

## 9. Extension points

| Need | Hook |
|---|---|
| New token | `EMAIL_ON_BUILD` + `EMAIL_ON_SEND` + `EMAIL_ON_DISPLAY` |
| Veto a send | `EMAIL_PRE_SEND` |
| A/B criteria | `addAbTestWinnerCriteria()` + `DetermineWinnerEvent` listener |
| Transport | Symfony `TransportFactoryInterface` (tag `mailer.transport_factory`), `TokenTransportInterface` (+`TokenTransportTrait`), `BounceProcessorInterface`, `UnsubscriptionProcessorInterface`, `ON_TRANSPORT_WEBHOOK` + `TransportCallback` |
| Address validation | `ON_EMAIL_VALIDATION` |
| Inbox folder | `MONITORED_EMAIL_CONFIG`, `EMAIL_PRE_FETCH`, `EMAIL_PARSE` |
| Stats | `ON_EMAIL_STAT_PRE_SAVE/POST_SAVE`, services tagged `mautic.email_stat_helper` |
| UI injection | `CoreEvents::VIEW_INJECT_CUSTOM_CONTENT` (`@MauticEmail/Email/details.html.twig` `right.section.start`, `preview.html.twig` `email.preview.buttons`) |
| Search | `SearchQueryEvent` from `EmailRepository::addSearchCommandWhereClause` |
| Hook after sending | Another `#[AsMessageHandler]` for `SendEmailMessage` (pattern: `RemoveReportAttachmentHandler`, priority -1000) |

Sources: [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:66-80 @7.x] [code: app/bundles/EmailBundle/Entity/EmailRepository.php:1032-1038 @7.x] [code: app/bundles/MessengerBundle/MessageHandler/RemoveReportAttachmentHandler.php:13-22 @7.x].
