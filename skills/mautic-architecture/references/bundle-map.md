# Bundle map (Mautic 7.x)

One row per core bundle (`app/bundles/`) and bundled plugin (`plugins/`). Tables are the names passed to
`setTable()` in each bundle's `Entity/` mapping (unprefixed; `db_table_prefix` is prepended at runtime
[code: app/bundles/CoreBundle/EventListener/DoctrineEventsSubscriber.php:30-109 @7.x]). Join tables declared inside
associations (for example `lead_ips_xref`) are not listed. "Owning skill" is the skill in this repository to open for
behaviour of that area.

## Core bundles (`app/bundles/`, namespace `Mautic\`)

| Bundle | Purpose | Key entities → tables | Owning skill |
|---|---|---|---|
| ApiBundle | REST API, OAuth2 server, API Platform resources, API controllers and serializer context [code: app/bundles/ApiBundle/ @7.x] | `oAuth2\Client` → `oauth2_clients`, `AccessToken` → `oauth2_accesstokens`, `RefreshToken` → `oauth2_refreshtokens`, `AuthCode` → `oauth2_authcodes` [code: app/bundles/ApiBundle/Entity/oAuth2/Client.php:71 @7.x] | mautic-rest-api |
| AssetBundle | Downloadable Assets and download tracking [code: app/bundles/AssetBundle/Entity/ @7.x] | `assets`, `asset_downloads` | mautic-assets-categories-projects |
| CacheBundle | PSR-6/PSR-16 tag-aware cache provider and adapters (`cache_adapter`) [code: app/bundles/CacheBundle/ @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/cache.html] | none | mautic-configuration |
| CampaignBundle | Campaigns, campaign events, contact membership, event log and execution [code: app/bundles/CampaignBundle/Entity/ @7.x] | `campaigns`, `campaign_events`, `campaign_leads`, `campaign_lead_event_log`, `campaign_lead_event_failed_log`, `campaign_summary` | mautic-campaigns |
| CategoryBundle | Categories shared by many entity types [code: app/bundles/CategoryBundle/Entity/ @7.x] | `categories` | mautic-assets-categories-projects |
| ChannelBundle | Channel registry, Marketing Messages and the message queue [code: app/bundles/ChannelBundle/Entity/ @7.x] | `messages`, `message_channels`, `message_queue` | mautic-channels |
| ConfigBundle | Configuration UI and writing `config/local.php` (`ConfigEvents`) [code: app/bundles/ConfigBundle/ @7.x] | none | mautic-configuration |
| CoreBundle | Framework layer: base entity/repository/model/controllers, DI passes, core events, permissions registry, translations, logging, error handler, admin UI, IP lookup, notifications, audit log [code: app/bundles/CoreBundle/ @7.x] | `AuditLog` → `audit_log`, `IpAddress` → `ip_addresses`, `Notification` → `notifications`, deprecated `Cache` → `cache_items` [code: app/bundles/CoreBundle/Entity/AuditLog.php:66 @7.x] [code: app/bundles/CoreBundle/Entity/Cache.php:10-12 @7.x] | mautic-architecture (this skill) |
| DashboardBundle | Dashboard and widgets [code: app/bundles/DashboardBundle/Entity/ @7.x] | `widgets` | mautic-reports-and-dashboard |
| DynamicContentBundle | Dynamic Web Content and its stats [code: app/bundles/DynamicContentBundle/Entity/ @7.x] | `dynamic_content`, `dynamic_content_lead_data`, `dynamic_content_stats` | mautic-pages-and-tracking |
| EmailBundle | Emails, sending, stats, replies, drafts, devices [code: app/bundles/EmailBundle/Entity/ @7.x] | `emails`, `emails_draft`, `email_copies`, `email_stats`, `email_stats_devices`, `email_stat_replies` | mautic-emails |
| FormBundle | Forms, fields, actions, submissions [code: app/bundles/FormBundle/Entity/ @7.x] | `forms`, `form_fields`, `form_actions`, `form_submissions` | mautic-forms |
| InstallBundle | Web and CLI installer, install fixtures, configurator steps [code: app/bundles/InstallBundle/ @7.x] | none | mautic-configuration (install), mautic-dev-environment |
| IntegrationsBundle | Integrations framework (sync engine, auth providers, config forms) and plugin migrations engine [code: app/bundles/IntegrationsBundle/Entity/ @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations] | `sync_object_mapping`, `sync_object_field_change_report` | mautic-integrations |
| LeadBundle | Contacts (`Lead`), companies, custom fields, segments (`LeadList`), DNC, tags, UTM, notes, devices, frequency rules, import/export [code: app/bundles/LeadBundle/Entity/ @7.x] | `leads`, `companies`, `companies_leads`, `lead_fields`, `lead_lists`, `lead_lists_leads`, `lead_donotcontact`, `lead_tags`, `lead_utmtags`, `lead_notes`, `lead_devices`, `lead_frequencyrules`, `lead_categories`, `lead_event_log`, `lead_points_change_log`, `lead_stages_change_log`, `lead_companies_change_log`, `imports`, `contact_merge_records`, `contact_export_scheduler` | mautic-contacts; segments (`LeadList*`, `Segment/`) in mautic-segments |
| MarketplaceBundle | In-app Marketplace for installing plugins via Composer [code: app/bundles/MarketplaceBundle/Service/ @7.x] | none | mautic-integrations / mautic-plugin-development |
| MessengerBundle | Symfony Messenger integration (async transports for email, hits) [code: app/bundles/MessengerBundle/ @7.x] | none | mautic-cron-and-queues |
| NotificationBundle | Web push notifications channel [code: app/bundles/NotificationBundle/Entity/ @7.x] | `push_notifications`, `push_notification_stats`, `push_ids` | mautic-channels |
| PageBundle | Landing Pages, page hits, redirects/trackables, video hits, tracking endpoints [code: app/bundles/PageBundle/Entity/ @7.x] | `pages`, `pages_draft`, `page_hits`, `page_redirects`, `channel_url_trackables`, `video_hits` | mautic-pages-and-tracking |
| PluginBundle | Plugin manager, legacy `AbstractIntegration` integrations, integration settings [code: app/bundles/PluginBundle/Entity/ @7.x] | `plugins`, `plugin_integration_settings`, `integration_entity` | mautic-plugin-development, mautic-integrations |
| PointBundle | Point actions, triggers, point groups, insights [code: app/bundles/PointBundle/Entity/ @7.x] | `points`, `point_triggers`, `point_trigger_events`, `point_lead_action_log`, `point_lead_event_log`, `point_groups`, `point_group_contact_score`, `point_insights` | mautic-points-and-stages |
| ProjectBundle | Projects that group entities [code: app/bundles/ProjectBundle/ @7.x] | `projects` | mautic-assets-categories-projects |
| QueueBundle | Legacy bundle; contains only `Config/config.php` [code: app/bundles/QueueBundle/Config/config.php @7.x] | none | mautic-cron-and-queues |
| ReportBundle | Reports and scheduled report delivery [code: app/bundles/ReportBundle/Entity/ @7.x] | `reports`, `reports_schedulers` | mautic-reports-and-dashboard |
| SmsBundle | Text Messages channel and stats [code: app/bundles/SmsBundle/Entity/ @7.x] | `sms_messages`, `sms_message_stats` | mautic-channels |
| StageBundle | Stages and stage change log [code: app/bundles/StageBundle/Entity/ @7.x] | `stages`, `stage_lead_action_log` | mautic-points-and-stages |
| StatsBundle | Aggregated stats collection and calculation (`StatEvents`) [code: app/bundles/StatsBundle/Aggregate/ @7.x] | none | mautic-reports-and-dashboard |
| UserBundle | Users, roles, stored permissions, SAML ids, invites and tokens, authentication [code: app/bundles/UserBundle/Entity/ @7.x] | `users`, `roles`, `permissions`, `user_tokens`, `user_invites`, `saml_id_entry` | mautic-users-and-permissions |
| WebhookBundle | Webhooks, event subscriptions, queue and logs [code: app/bundles/WebhookBundle/Entity/ @7.x] | `webhooks`, `webhook_events`, `webhook_queue`, `webhook_logs` | mautic-webhooks |

## Bundled plugins (`plugins/`, namespace `MauticPlugin\`)

| Plugin | Purpose | Key entities → tables | Owning skill |
|---|---|---|---|
| GrapesJsBuilderBundle | GrapesJS drag-and-drop builder for Emails and Landing Pages; own npm build [code: plugins/GrapesJsBuilderBundle/ @7.x] | `bundle_grapesjsbuilder` | mautic-theme-development |
| MauticClearbitBundle | Clearbit enrichment integration (removed in 8.x) [code: plugins/MauticClearbitBundle/Integration/ClearbitIntegration.php @7.x] [PR #17785] | none | mautic-integrations |
| MauticCloudStorageBundle | Amazon S3 remote storage for Assets [code: plugins/MauticCloudStorageBundle/Integration/AmazonS3Integration.php @7.x] | none | mautic-assets-categories-projects |
| MauticCrmBundle | CRM integrations: Salesforce, HubSpot, Dynamics, SugarCRM, Vtiger, Zoho, ConnectWise [code: plugins/MauticCrmBundle/Integration/ @7.x] | none | mautic-integrations |
| MauticEmailMarketingBundle | Mailchimp, Constant Contact, iContact integrations [code: plugins/MauticEmailMarketingBundle/Integration/ @7.x] | none | mautic-integrations |
| MauticFocusBundle | Focus Items (pop-ups, bars, modals) and their stats [code: plugins/MauticFocusBundle/Entity/ @7.x] | `focus`, `focus_stats` | mautic-channels |
| MauticFullContactBundle | FullContact enrichment integration [code: plugins/MauticFullContactBundle/Integration/FullContactIntegration.php @7.x] | none | mautic-integrations |
| MauticGmailBundle | Gmail plugin integration [code: plugins/MauticGmailBundle/Integration/ @7.x] | none | mautic-integrations |
| MauticOutlookBundle | Outlook plugin integration [code: plugins/MauticOutlookBundle/Integration/ @7.x] | none | mautic-integrations |
| MauticSocialBundle | Social integrations (Twitter, Facebook, Instagram, Foursquare), social monitoring and tweets [code: plugins/MauticSocialBundle/Integration/ @7.x] | `monitoring`, `monitoring_leads`, `monitor_post_count`, `tweets`, `tweet_stats` | mautic-channels |
| MauticTagManagerBundle | Tag management screens over contact tags [code: plugins/MauticTagManagerBundle/ @7.x] | `Tag` subclass of LeadBundle's tag → `lead_tags` (removed in 8.x) [PR #17361] | mautic-contacts |
| MauticZapierBundle | Zapier integration (config and assets only) [code: plugins/MauticZapierBundle/ @7.x] | none | mautic-integrations |

## How to find the owner of something
- A table name: grep `setTable('<name>')` under `app/bundles/*/Entity` and `plugins/*/Entity`. [code: app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php @7.x]
- A route name: grep the name in `app/bundles/*/Config/config.php` `routes`. [code: app/bundles/CoreBundle/Config/config.php:6-110 @7.x]
- A permission `bundle:name:level`: the `bundle` segment is `AbstractPermissions::getName()` of a class in `<Bundle>/Security/Permissions/` (for example `lead`, `email`, `core`), not the Symfony bundle name. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x]
- A model key `bundle.name`: the service id `mautic.{bundle}.model.{name}`. [code: app/bundles/CoreBundle/Factory/ModelFactory.php:70-97 @7.x]
- An event: grep the string value or constant in `app/bundles/*/*Events.php`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#available-events]
