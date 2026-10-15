# Mautic glossary

Each entry gives the user-facing term (as the docs spell it), a one-line definition, the code name, the main table(s),
a citation and the skill that owns the behaviour. Tables are stored unprefixed; `db_table_prefix` is prepended at
runtime [code: app/bundles/CoreBundle/EventListener/DoctrineEventsSubscriber.php:30-109 @7.x]. Table lists come from
`mautic-architecture/references/bundle-map.md`. In prose, use the capitalised feature names from the docs style list
[docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml].

## Contents
1. People and data (Contact … UTM tag)
2. Campaigns
3. Channels and messages
4. Web content and capture
5. Scoring and lifecycle
6. Organisation (Category, Project)
7. Extending and presentation (Webhook … Token)
8. Reporting
9. Access control
10. Background processing
11. Rejected terms → preferred terms

## 1. People and data

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| Contact (formerly Lead) | A person record, identified or anonymous. Code and tables keep "lead". | `Mautic\LeadBundle\Entity\Lead` | `leads` | [code: app/bundles/LeadBundle/Entity/Lead.php:298 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#website-monitoring] | mautic-contacts |
| Visitor | An anonymous Contact created by website tracking. | `Lead` with no identifying field | `leads` | [code: app/bundles/PageBundle/Model/PageModel.php:410-463 @7.x] | mautic-pages-and-tracking, mautic-contacts |
| Company | An organisation; a Contact can belong to several, one of them primary. | `Company` | `companies`, `companies_leads` | [code: app/bundles/LeadBundle/Entity/Company.php:51 @7.x] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#identifying-companies] | mautic-contacts |
| Custom Field | A Contact or Company field defined by an admin; it adds a column to `leads` or `companies`. Marking it unique changes the column to varchar and adds an index. | `LeadField` | `lead_fields` | [code: app/bundles/LeadBundle/Field/SchemaDefinition.php:17-23 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#custom-fields] | mautic-contacts |
| Segment (code: lead list) | A named set of Contacts; dynamic (filters, rebuilt by cron) or static (explicit adds only). | `LeadList` | `lead_lists`, `lead_lists_leads` | [code: app/bundles/LeadBundle/Entity/LeadList.php:137 @7.x] [code: app/bundles/LeadBundle/Model/ListModel.php:383-633 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html] | mautic-segments |
| DNC (Do Not Contact) | A per-channel opt-out on a Contact with a reason (unsubscribed, bounced, manual). | `DoNotContact` (entity and model) | `lead_donotcontact` | [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-32 @7.x] [code: app/bundles/LeadBundle/Model/DoNotContact.php:31-227 @7.x] | mautic-contacts |
| Frequency rule | A cap on how many messages a Contact receives per channel per period; excess sends are deferred or skipped. | `FrequencyRule` | `lead_frequencyrules` | [code: app/bundles/LeadBundle/Entity/FrequencyRule.php:66-98 @7.x] [code: app/bundles/LeadBundle/Entity/FrequencyRuleRepository.php:23-237 @7.x] | mautic-contacts (deferral queue: mautic-channels) |
| Tag | A free-text label on Contacts. | `Tag` | `lead_tags` | [code: app/bundles/LeadBundle/Entity/Tag.php:73-80 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tags] | mautic-contacts |
| UTM tag | A record of the UTM parameters a Contact arrived with. | `UtmTag` | `lead_utmtags` | [code: app/bundles/LeadBundle/Entity/UtmTag.php:78-93 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#utm-code] | mautic-contacts |
| Merge | Combining two Contact records into one. | `Deduplicate\ContactMerger`, `MergeRecord` | `contact_merge_records` | [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#merge-two-contacts] [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php @7.x] | mautic-contacts |
| Import | CSV import of Contacts or Companies, processed in the background. | `Import` | `imports` | [code: app/bundles/LeadBundle/Entity/ @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html] | mautic-contacts |

## 2. Campaigns

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| Campaign | A workflow drawn on a canvas that moves Contacts through events. | `Campaign` | `campaigns`, `campaign_leads` (membership) | [code: app/bundles/CampaignBundle/Entity/Campaign.php:165 @7.x] [docs: https://docs.mautic.org/en/7.2/campaigns/creating_campaigns.html#create-your-first-campaign] | mautic-campaigns |
| Source | Where Contacts enter a Campaign: Segments or Forms (plus manual and API adds). A Form source adds the submitter immediately; a Segment source needs cron. | Campaign `lists` / `forms` associations | `campaign_leadlist_xref`, `campaign_form_xref` | [code: app/bundles/CampaignBundle/Entity/Campaign.php:194-201 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:382-387 @7.x] | mautic-campaigns |
| Action | A campaign event where Mautic does something (send an Email, change a field). | `Event` with type `action` | `campaign_events` | [code: app/bundles/CampaignBundle/Entity/Event.php:54-58 @7.x] | mautic-campaigns |
| Decision | A campaign event that waits for the Contact to do something (open an Email, visit a page); the "yes" path runs in real time, the "no" (inactive) path from cron. | `Event` with type `decision` | `campaign_events`, `campaign_lead_event_log` | [code: app/bundles/CampaignBundle/Entity/Event.php:54-58 @7.x] [code: app/bundles/CampaignBundle/Executioner/EventExecutioner.php:258-263 @7.x] [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#green-paths] | mautic-campaigns |
| Condition | A campaign event where Mautic checks Contact data and branches. | `Event` with type `condition` | `campaign_events` | [code: app/bundles/CampaignBundle/Entity/Event.php:54-58 @7.x] | mautic-campaigns |
| Event log / rotation | One row per event per Contact per pass through the Campaign. | `LeadEventLog` | `campaign_lead_event_log`, `campaign_lead_event_failed_log` | [code: app/bundles/CampaignBundle/Entity/ @7.x] | mautic-campaigns |

## 3. Channels and messages

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| Channel | A medium Mautic uses to reach a Contact (`email`, `sms`, web push, Focus Item, tweet); channels register with ChannelBundle. | channel key; `ChannelEvents::ADD_CHANNEL` | — | [code: app/bundles/ChannelBundle/ChannelEvents.php:16 @7.x] | mautic-channels |
| Email | A template Email (sent by Campaigns, API or forms) or a Segment Email (broadcast to Segments). | `Email` | `emails`, `email_stats` | [code: app/bundles/EmailBundle/Model/EmailModel.php:1347-1571 @7.x] | mautic-emails |
| Text Message (SMS) | An SMS sent through a transport such as Twilio. | `Sms` | `sms_messages`, `sms_message_stats` | [docs: https://docs.mautic.org/en/7.2/channels/sms.html] [code: app/bundles/SmsBundle/Entity/ @7.x] | mautic-channels |
| Marketing Message | One message per channel; on send, channels are tried in the Contact's priority order and the first success wins. | `ChannelBundle\Entity\Message` | `messages`, `message_channels`, `message_queue` | [code: app/bundles/ChannelBundle/Entity/Message.php:27-45 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#what-are-marketing-messages] | mautic-channels |
| Focus Item | A pop-up, bar or modal shown on a tracked website. | `Focus` (plugins/MauticFocusBundle) | `focus`, `focus_stats` | [code: plugins/MauticFocusBundle/Entity/Focus.php:26-43 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/focus_items.html#engagement-options] | mautic-channels |
| Preference Center | The page a Contact sees on unsubscribe when `show_contact_preferences` is on: frequency, channels, Segments and Categories. Without it, unsubscribe writes DNC. | `show_contact_preferences`; preference-centre Landing Page | `pages` | [code: app/bundles/EmailBundle/Controller/PublicController.php:267-352 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#customizing-preference-center] | mautic-emails, mautic-pages-and-tracking |

## 4. Web content and capture

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| Landing Page | A page hosted by Mautic at an alias, with A/B variants and translations. | `Page` | `pages`, `pages_draft` | [code: app/bundles/PageBundle/Entity/Page.php:36-54 @7.x] [docs: https://docs.mautic.org/en/7.2/components/landing_pages.html#creating-a-draft-landing-page] | mautic-pages-and-tracking |
| Page hit / tracking | A row per tracked page view, tracked click or 404; none for logged-in Users. | `Hit` | `page_hits` | [code: app/bundles/PageBundle/Entity/Hit.php:17 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:410-416 @7.x] | mautic-pages-and-tracking |
| Dynamic Web Content (DWC) | A content block chosen per Contact and injected into a slot on a web page. | `DynamicContent` | `dynamic_content`, `dynamic_content_stats` | [code: app/bundles/DynamicContentBundle/Entity/DynamicContent.php:39-57 @7.x] | mautic-pages-and-tracking |
| Asset | A downloadable file (local or remote) served and tracked at `/asset/{slug}`. | `Asset` | `assets`, `asset_downloads` | [code: app/bundles/AssetBundle/Entity/Asset.php:93-97 @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#uploading-an-asset] | mautic-assets-categories-projects |
| Form | A Mautic-hosted web form that identifies or creates a Contact and runs Form actions. | `Form`, `Field`, `Action`, `Submission` | `forms`, `form_fields`, `form_actions`, `form_submissions` | [code: app/bundles/FormBundle/Entity/Form.php:351-384 @7.x] [docs: https://docs.mautic.org/en/7.2/components/forms.html#general] | mautic-forms |
| Kiosk mode | A Form setting for shared devices: no tracked Contact, no cookie, no IP, no progressive profiling. | `Form::$inKioskMode` | `forms` | [code: app/bundles/FormBundle/Entity/Form.php:149 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:935-955 @7.x] | mautic-forms |
| Progressive profiling | Hiding Form fields whose values are already known. | Form field settings | `form_fields` | [docs: https://docs.mautic.org/en/7.2/components/forms.html#limits-of-progressive-profiling] | mautic-forms |

## 5. Scoring and lifecycle

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| Points | A Contact's integer score (`leads.points`). | `Lead::$points` | `leads`, `lead_points_change_log` | [code: app/bundles/LeadBundle/Entity/Lead.php:810-812 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html] | mautic-points-and-stages |
| Point Action | A rule that changes points when a Contact does something (repeatable or once). | `Point` | `points`, `point_lead_action_log` | [code: app/bundles/PointBundle/Entity/Point.php:28-36 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html#point-actions] | mautic-points-and-stages |
| Point Trigger | One-off events run when a Contact's score reaches a threshold. | `Trigger`, `TriggerEvent` | `point_triggers`, `point_trigger_events` | [code: app/bundles/PointBundle/Entity/Trigger.php:67-130 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html#point-triggers] | mautic-points-and-stages |
| Point Group | A separate score scale; an action assigned to a group changes only that group score. | `Group` | `point_groups`, `point_group_contact_score` | [code: app/bundles/PointBundle/Entity/Group.php:18-63 @7.x] [code: app/bundles/PointBundle/Model/PointModel.php:266-274 @7.x] | mautic-points-and-stages |
| Stage | An ordered lifecycle phase with a unique weight; a Contact holds at most one. | `Stage` | `stages`, `lead_stages_change_log` | [code: app/bundles/StageBundle/Entity/Stage.php:112-117 @7.x] [docs: https://docs.mautic.org/en/7.2/stages/stages.html] | mautic-points-and-stages |

## 6. Organisation

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| Category | A label from one shared table, scoped to one component ("bundle") or `global`; Contacts can opt out of Email Categories. | `Category` | `categories`, `lead_categories` | [code: app/bundles/CategoryBundle/Entity/Category.php:87-104 @7.x] [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html] | mautic-assets-categories-projects |
| Project | A named grouping (new in 7.x) that spans many entity types. | `Project` | `projects` | [code: app/bundles/ProjectBundle/Entity/Project.php:28-33 @7.x] [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#creating-projects] | mautic-assets-categories-projects |

## 7. Extending and presentation

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| Webhook | A saved target URL, secret and subscribed event types; Mautic POSTs signed JSON immediately or in batches from cron. | `Webhook` | `webhooks`, `webhook_events`, `webhook_queue`, `webhook_logs` | [code: app/bundles/WebhookBundle/Entity/Webhook.php:28-583 @7.x] | mautic-webhooks |
| Plugin | A Symfony bundle under `plugins/` that extends Mautic. | `Plugin` (registry row); `AbstractPluginBundle` | `plugins` | [code: app/bundles/PluginBundle/Entity/Plugin.php:72-103 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/getting_started.html] | mautic-plugin-development |
| Integration | A configured connection to a third-party system, shipped by a Plugin; two frameworks (legacy `AbstractIntegration`, modern `BasicIntegration`). | `Integration` (settings); `BasicIntegration` | `plugin_integration_settings`, `integration_entity`, `sync_object_mapping` | [code: app/bundles/PluginBundle/Entity/Integration.php:49-85 @7.x] [code: app/bundles/IntegrationsBundle/Integration/BasicIntegration.php:10-40 @7.x] | mautic-integrations |
| Marketplace | In-app installer for plugins via Composer. | MarketplaceBundle | — | [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html] | mautic-integrations |
| Theme | A package of Twig templates under `themes/<dir>/` supplying starting HTML/MJML for Emails, Landing Pages and Forms. | `ThemeHelper` | — (filesystem) | [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:61-103 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html] | mautic-theme-development |
| Builder | The GrapesJS drag-and-drop editor for Emails and Landing Pages; it writes final HTML into the entity's `customHtml`. | `plugins/GrapesJsBuilderBundle` | `bundle_grapesjsbuilder` | [code: plugins/GrapesJsBuilderBundle/Assets/library/js/builder.js:13-47 @7.x] [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#restoring-unsaved-changes] | mautic-theme-development |
| Code Mode | The "no theme, raw HTML" option, stored as the template value `mautic_code_mode`. | `ThemeListType` | — | [code: app/bundles/CoreBundle/Form/Type/ThemeListType.php:25-32 @7.x] | mautic-theme-development |
| Token | A placeholder replaced per Contact at render time, such as `{contactfield=email}`, `{unsubscribe_url}`, `{formfield=}`, `{assetlink=ID}`. | token events per bundle | — | [code: app/bundles/EmailBundle/Helper/MailHelper.php:1963-1995 @7.x] [code: app/bundles/FormBundle/Controller/PublicController.php:639-661 @7.x] | mautic-emails (forms: mautic-forms) |

## 8. Reporting

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| Report | A saved query definition: data source (context), columns, filters, grouping, graphs; can be scheduled by email. | `Report`, `Scheduler` | `reports`, `reports_schedulers` | [code: app/bundles/ReportBundle/Entity/Report.php:167-217 @7.x] [docs: https://docs.mautic.org/en/7.2/reports/reports.html#data-sources] | mautic-reports-and-dashboard |
| Widget | A Dashboard tile, per User, filtered by a date range and cached. | `Widget` | `widgets` | [code: app/bundles/DashboardBundle/Entity/Widget.php:53-104 @7.x] [docs: https://docs.mautic.org/en/7.2/dashboard/dashboard.html#widget-cache] | mautic-reports-and-dashboard |

## 9. Access control

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| User | A back-office login (not a Contact); logged-in Users are never tracked. | `User` | `users` | [code: app/bundles/UserBundle/Entity/ @7.x] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html] | mautic-users-and-permissions |
| Role | A named set of permissions assigned to Users; admin Roles have full access. | `Role` | `roles` | [code: app/bundles/UserBundle/Entity/Role.php:105-128 @7.x] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#explaining-the-permission-options] | mautic-users-and-permissions |
| Permission | A `bundle:name:level` string stored as a bitwise value per Role; the `bundle` segment is the permission class name, not the Symfony bundle. | `Permission`; `CorePermissions` | `permissions` | [code: app/bundles/UserBundle/Entity/Permission.php:81-101 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x] | mautic-users-and-permissions |
| Audit log | A record of who changed which entity and when. | `AuditLog`, `AuditLogModel` | `audit_log` | [code: app/bundles/CoreBundle/Entity/AuditLog.php:66 @7.x] [code: app/bundles/CoreBundle/Model/AuditLogModel.php:34-80 @7.x] | mautic-architecture (user changes: mautic-users-and-permissions) |

## 10. Background processing

| Term | Definition | Code name | Table(s) | Source | Skill |
|---|---|---|---|---|---|
| Cron | The scheduler that runs `mautic:*` console commands (Segment rebuilds, Campaign triggers, broadcasts, imports, webhooks, reports). Nothing in these areas progresses without it. | `ModeratedCommand` (lock) | — | [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-224 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html] | mautic-cron-and-queues |
| Messenger transport | Symfony Messenger queues for `email`, `hit` and `failed`; `sync://` (default) handles in-process, any other DSN needs `messenger:consume <transport>`. | MessengerBundle | — | [code: app/bundles/MessengerBundle/Config/config.php:7-8 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mautic-doesn-t-use-queues-by-default] | mautic-cron-and-queues |
| Lock ("Script in progress") | The per-command lock that stops two runs overlapping (`--bypass-locking`, `--lock_mode`). | `ModeratedCommand` | `var/run` lock files | [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-224 @7.x] | mautic-cron-and-queues |

## 11. Rejected terms → preferred terms
From the docs style list (suggestion level) [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]:

| Avoid | Use |
|---|---|
| lead, leads | Contact, Contacts |
| page, pages | Landing Page, Landing Pages |
| dwc, dynamic content | Dynamic Content |
| publish / published | Activate or Turn On / Active or Available |
| unpublish / unpublished | Deactivate or Turn Off / Unavailable or Deactivated |
| lower-case feature names (segment, campaign, focus item, point trigger …) | Capitalised: Segment, Campaign, Focus Item, Point Trigger … |

Full style rules and the general word list: `mautic-contributing/references/terminology.md`.
