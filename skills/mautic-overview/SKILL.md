---
name: mautic-overview
description: "Start here for anything about Mautic. Entry point and router for this repository: what Mautic is (open-source marketing automation with Contacts, Segments, Campaigns, Emails, Forms, Landing Pages, Points, Stages, channels and website tracking), which version is authoritative (7.x, 7.2.1) and what changes in 8.x, a glossary that maps each UI term (Contact/Lead, Segment/LeadList, DNC, Focus Item, Point Trigger and more) to its code name, table and owning skill, the cross-cutting rules every agent must follow, and a task-to-skill routing table. Use whenever a task mentions Mautic, mautic/mautic, app/bundles/, a mautic:* command, docs.mautic.org or devdocs.mautic.org and you are not sure which mautic-* skill applies; when translating a Mautic UI term to code or back; when a task spans several areas, such as 'why did this contact not get the email' or 'port my plugin to Mautic 8'; or when you need orientation before opening an area skill."
---
# Mautic overview and skill router

## Scope
This skill orients an agent that knows nothing about Mautic and routes it to the right area skill in this repository.
It holds the product summary, version context, glossary, cross-cutting rules and routing tables; it holds no area
behaviour of its own. Every behaviour claim lives in an area skill's `references/behaviour.md`, and the full product
map lives in `mautic-architecture/references/bundle-map.md`.

## Expected behaviour (essentials)

### What Mautic is
- Mautic is an open-source marketing automation platform built on Symfony and PHP, licensed GPL-3.0. [code: AGENTS.md:7 @7.x] [code: composer.json:3-5 @7.x]
- Its central record is the Contact, a person known or anonymous (code name `Lead`, table `leads`), optionally linked to Companies. [code: app/bundles/LeadBundle/Entity/Lead.php:298 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#website-monitoring]
- Segments group Contacts by filters (rebuilt by cron) or by explicit adds, and feed Campaigns, Segment Emails, SMS and Reports. [code: app/bundles/LeadBundle/Model/ListModel.php:383-633 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html]
- Campaigns are workflows: Contacts enter from Segments or Forms and flow through Actions, Decisions and Conditions. [code: app/bundles/CampaignBundle/Entity/Event.php:54-58 @7.x] [docs: https://docs.mautic.org/en/7.2/campaigns/creating_campaigns.html#create-your-first-campaign]
- Channels deliver messages: Email, SMS, web push, Focus Items and Marketing Messages, which pick a channel per Contact. [code: app/bundles/ChannelBundle/ChannelEvents.php:16 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/marketing_messages.html#what-are-marketing-messages]
- A tracking script and pixel on your website record page hits and identify returning visitors; Forms, Landing Pages and Assets capture and identify Contacts. [code: app/bundles/PageBundle/Model/PageModel.php:410-463 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-script-javascript]
- Points score Contacts and Stages place them in a lifecycle phase; Reports, the Dashboard, Webhooks, the REST API and Integrations expose the data. [code: app/bundles/PointBundle/Model/PointModel.php:173-310 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html] [docs: https://docs.mautic.org/en/7.2/stages/stages.html]
- Most automation runs outside the web request, in console commands driven by cron and in Symfony Messenger workers. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-224 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]

### Version context
- Authoritative: Mautic 7.x at commit `419a08a9b35`: the 7.2.1 release plus 87 merged but unreleased PRs (see [SOURCES.md](../../SOURCES.md) and [post-7.2.1-prs.md](../mautic-upgrades-and-versions/references/post-7.2.1-prs.md)). It runs on PHP 8.2–8.5, Symfony ~7.4, Doctrine ORM 2 and DBAL 3.7, with MySQL ≥ 8.4.0 or MariaDB ≥ 10.11.0. [code: app/composer.json:15-105 @7.x] [code: app/release_metadata.json:4-7 @7.x] [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:177-201 @7.x]
- In development: 8.x moves to PHP 8.4, Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4 and PHPUnit 13. [PR #16993] [PR #17392] [PR #17361] [PR #17004]
- 8.x dispatches almost every event by its event class name, and `CoreEvents` is gone. [PR #17157] [PR #17183] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch]
- 8.x is unreleased: `app/release_metadata.json@8.x` still says 7.2.0. [code: app/release_metadata.json @8.x]
- 5.x replaced Swift Mailer with Symfony Mailer (one `mailer_dsn`) and the old queue with Symfony Messenger; `mautic:emails:send` and `mautic:queue:process` no longer exist. [code: UPGRADE-5.0.md:16,104-109 @7.x]
- 6.x moved to Symfony 6, removed the legacy builder and Froala, and removed `MauticFactory` getters in favour of DI. [code: UPGRADE-6.0.md @7.x] [code: UPGRADE-6.0.md:27-33 @7.x]
- Any version ≥ 5.0.0 can update to 7.x once PHP ≥ 8.2 and MySQL ≥ 8.4.0 / MariaDB ≥ 10.11.0 are in place. [code: app/bundles/CoreBundle/Helper/UpdateHelper.php:166-196 @7.x]
- Full release history, the updater and the 7.x→8.x guide with the event map are in `mautic-upgrades-and-versions`.

### Cross-cutting rules (every agent)
1. Cite every statement with the tags defined in [SOURCES.md](../../SOURCES.md): `[code: path:line @7.x]`, `[code: … @8.x]`, `[docs: URL]`, `[devdocs: URL]`, `[kb: URL]`, `[PR #N]`. Never cite from memory. → mautic-contributing
2. When code and docs disagree about current behaviour, trust the code at the 7.x snapshot, then docs, then PR discussion, and record the discrepancy. Example: the docs say only Administrators are excluded from point scoring, but the code skips every logged-in User. [code: app/bundles/PointBundle/Model/PointModel.php:176-178 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points_troubleshooting.html#page-visits-not-recognized]
3. Write "Contact", not "Lead", and "Segment", not "List", in prose; keep `Lead`/`LeadList` in code identifiers. [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml] → mautic-contributing
4. Logged-in Mautic Users are not tracked: no page hit, no asset download, no points. Test public behaviour in a private window or call `logoutUser()` in tests. [code: app/bundles/PageBundle/Model/PageModel.php:410-412 @7.x] [code: app/bundles/AssetBundle/Model/AssetModel.php:104-116 @7.x] → mautic-pages-and-tracking, mautic-testing
5. Cron is required: Segments, Campaigns, scheduled emails, imports, exports and queued Webhooks only progress when their command runs. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html] [kb: https://kb.mautic.org/article/getting-started-with-mautic.html] → mautic-cron-and-queues
6. Messenger transports default to `sync://` (handled in-process); any queue DSN needs `messenger:consume <transport>` running or nothing is sent. [code: app/bundles/MessengerBundle/Config/config.php:7-8 @7.x] → mautic-cron-and-queues
7. The 8.x silent-listener trap: a subscriber keyed on a 7.x constant that still exists but is no longer dispatched never fires, with no error. Subscribe by event class to support both. [PR #17157] [PR #17183] → mautic-upgrades-and-versions, mautic-plugin-development
8. A Decision's "yes" path runs in real time for a tracked, identified Contact, never from cron. [code: app/bundles/CampaignBundle/Executioner/EventExecutioner.php:258-263 @7.x] [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#green-paths] → mautic-campaigns
9. Table names are stored unprefixed; `db_table_prefix` is prepended at runtime, and tests use the `test_` prefix. [code: app/bundles/CoreBundle/EventListener/DoctrineEventsSubscriber.php:30-109 @7.x] → mautic-architecture, mautic-testing
10. Inside a Mautic checkout, also load upstream `AGENTS.md` and `.agents/skills/mautic-dev/SKILL.md`; they cover development commands and time-wasting pitfalls, and this repository covers behaviour. [code: AGENTS.md @7.x] [code: .agents/skills/mautic-dev/SKILL.md @7.x]

### Glossary (short form)
UI term → code name → main table → owning skill. Definitions and citations for every term: [references/glossary.md](references/glossary.md).

| Term | Code name | Table | Skill |
|---|---|---|---|
| Contact (Lead, Visitor) | `Lead` | `leads` | mautic-contacts |
| Company | `Company` | `companies`, `companies_leads` | mautic-contacts |
| Segment | `LeadList` | `lead_lists`, `lead_lists_leads` | mautic-segments |
| Campaign | `Campaign` | `campaigns`, `campaign_leads` | mautic-campaigns |
| Source / Action / Decision / Condition | `Campaign` lists+forms; `Event` type `action`/`decision`/`condition` | `campaign_events`, `campaign_lead_event_log` | mautic-campaigns |
| Channel | channel key (`email`, `sms`…), `ChannelEvents::ADD_CHANNEL` | — | mautic-channels |
| DNC (Do Not Contact) | `DoNotContact` | `lead_donotcontact` | mautic-contacts |
| Frequency rule | `FrequencyRule` | `lead_frequencyrules` | mautic-contacts |
| Preference Center | `show_contact_preferences`, preference-centre Landing Page | `pages` | mautic-emails, mautic-pages-and-tracking |
| Marketing Message | `ChannelBundle\Entity\Message` | `messages`, `message_channels` | mautic-channels |
| Focus Item | `Focus` (MauticFocusBundle) | `focus`, `focus_stats` | mautic-channels |
| Dynamic Web Content | `DynamicContent` | `dynamic_content` | mautic-pages-and-tracking |
| Landing Page | `Page` | `pages`, `page_hits` | mautic-pages-and-tracking |
| Asset | `Asset` | `assets`, `asset_downloads` | mautic-assets-categories-projects |
| Form / Kiosk mode | `Form`, `inKioskMode` | `forms`, `form_submissions` | mautic-forms |
| Point Action / Trigger / Group | `Point` / `Trigger` / `Group` | `points` / `point_triggers` / `point_groups` | mautic-points-and-stages |
| Stage | `Stage` | `stages` | mautic-points-and-stages |
| Category / Project | `Category` / `Project` | `categories` / `projects` | mautic-assets-categories-projects |
| Tag / UTM tag | `Tag` / `UtmTag` | `lead_tags` / `lead_utmtags` | mautic-contacts |
| Webhook | `Webhook` | `webhooks`, `webhook_queue` | mautic-webhooks |
| Integration / Plugin | `Integration`, `BasicIntegration` / `Plugin` | `plugin_integration_settings` / `plugins` | mautic-integrations / mautic-plugin-development |
| Theme / Builder | `themes/<dir>`, `ThemeHelper` / GrapesJsBuilderBundle | — / `bundle_grapesjsbuilder` | mautic-theme-development |
| Token | `{contactfield=…}`, `{unsubscribe_url}`… | — | mautic-emails |
| Report / Widget | `Report` / `Widget` | `reports` / `widgets` | mautic-reports-and-dashboard |
| User / Role / Permission | `User` / `Role` / `Permission` | `users` / `roles` / `permissions` | mautic-users-and-permissions |
| Audit log | `AuditLog` | `audit_log` | mautic-architecture |
| Messenger transport / Cron | `email`, `hit`, `failed` transports / `mautic:*` commands | — | mautic-cron-and-queues |

Tables in this list are from the bundle map. [code: app/bundles/LeadBundle/Entity/ @7.x] [code: app/bundles/CampaignBundle/Entity/ @7.x] Open the glossary file for per-row citations.

## Where it lives
Each bundle and its owning skill. Full table with entities and tables: `mautic-architecture/references/bundle-map.md`.

| Code location | Owning skill |
|---|---|
| `app/bundles/CoreBundle/`, `CacheBundle` (framework), `StatsBundle` | mautic-architecture (cache: mautic-configuration; stats: mautic-reports-and-dashboard) |
| `app/bundles/LeadBundle/` (Contacts, Companies, fields, DNC, tags, import) | mautic-contacts |
| `app/bundles/LeadBundle/Segment/`, `LeadList*` | mautic-segments |
| `app/bundles/CampaignBundle/` | mautic-campaigns |
| `app/bundles/EmailBundle/` | mautic-emails |
| `app/bundles/FormBundle/` | mautic-forms |
| `app/bundles/PageBundle/`, `DynamicContentBundle/` | mautic-pages-and-tracking |
| `app/bundles/AssetBundle/`, `CategoryBundle/`, `ProjectBundle/`, `plugins/MauticCloudStorageBundle/` | mautic-assets-categories-projects |
| `app/bundles/PointBundle/`, `StageBundle/` | mautic-points-and-stages |
| `app/bundles/ChannelBundle/`, `SmsBundle/`, `NotificationBundle/`, `plugins/MauticFocusBundle/`, `plugins/MauticSocialBundle/` | mautic-channels |
| `app/bundles/ReportBundle/`, `DashboardBundle/` | mautic-reports-and-dashboard |
| `app/bundles/UserBundle/` | mautic-users-and-permissions |
| `app/bundles/ApiBundle/` | mautic-rest-api |
| `app/bundles/WebhookBundle/` | mautic-webhooks |
| `app/bundles/IntegrationsBundle/`, `PluginBundle/` integrations, `MarketplaceBundle/`, CRM and enrichment plugins | mautic-integrations |
| `plugins/<Name>Bundle/` skeleton, `PluginBundle` lifecycle | mautic-plugin-development |
| `themes/`, `plugins/GrapesJsBuilderBundle/` | mautic-theme-development |
| `app/bundles/ConfigBundle/`, `InstallBundle/`, `config/local.php` | mautic-configuration |
| `app/bundles/MessengerBundle/`, `*/Command/`, `QueueBundle` | mautic-cron-and-queues |
| `app/migrations/`, `UPGRADE-*.md`, updater | mautic-upgrades-and-versions |
| `.ddev/`, `.devcontainer/`, `composer.json` scripts | mautic-dev-environment |
| `app/phpunit.xml.dist`, `*/Tests/`, `tests/` (Codeception), `phpstan.neon`, `rector.php` | mautic-testing |
| `.github/PULL_REQUEST_TEMPLATE.md`, `ecs.php`, branch policy | mautic-contributing |

To find the owner of a table, route, permission or event, follow "How to find the owner of something" in the bundle map. [code: app/bundles/CoreBundle/Factory/ModelFactory.php:70-97 @7.x]

## How to change or extend it
- Identify the area from the routing table below, open that skill, and read its "Expected behaviour" and "Pitfalls" before editing.
- For any new subscriber, entity, model or controller, also open mautic-architecture for the framework conventions.
- For code that must run on 7.x and 8.x, open mautic-upgrades-and-versions (`references/event-map-7-to-8.md`) before choosing event names.
- For a change to core, open mautic-contributing for branch targeting (features to 7.x, fixes to 7.2, BC breaks to 8.x) and the schema-change rule (entity metadata and a migration together).
- For an extension outside core, start in mautic-plugin-development; its extension-point catalogue names the feature skill for each hook.
- Common multi-skill tasks are listed under Related skills; 40+ more are in [references/task-routing.md](references/task-routing.md).

## How to test it
- Harness, base classes (`MauticMysqlTestCase`, `AbstractMauticTestCase`), fixtures and static analysis: mautic-testing. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:35-64 @7.x]
- The test oracle for a feature is the area skill's `references/behaviour.md`; representative tests to copy are in its `references/test-patterns.md`.
- Every functional test starts logged in as `admin`, so tracking-dependent behaviour needs `logoutUser()` or a mapped email field. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:35-64, 69-97 @7.x] [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:51-60 @7.x]
- Black-box QA of a running instance: mautic-testing, then mautic-troubleshooting for the symptom-to-cause playbooks.

## Version notes
- 7.x is authoritative; every skill states 5.x/6.x differences and the 8.x delta in its own `references/version-notes.md`.
- The compact history above is from `mautic-upgrades-and-versions/references/version-notes.md`; open that skill for release dates, updater rules, migrations and `references/upgrade-to-8.md`.

## Pitfalls
- Assuming a feature is real-time when it needs cron, or that email is queued when the DSN is `sync://`. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs] [code: app/bundles/MessengerBundle/Config/config.php:7-8 @7.x]
- Testing tracking, points or downloads while logged in to the admin. [code: app/bundles/PointBundle/Model/PointModel.php:176-178 @7.x]
- Searching for "list" or "lead" in docs: the UI says Segment and Contact. [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]
- Using `mautic:emails:send` or `mautic:queue:process` advice from pre-5.x material; use `messenger:consume`. [code: UPGRADE-5.0.md:16,104-109 @7.x]
- A plugin bundle with `MINIMUM_MAUTIC_VERSION` above the running version is silently not registered. [code: app/AppKernel.php:176-181 @7.x]
- A real `MAUTIC_<KEY>` environment variable silently beats the value saved in the Configuration UI. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:91-105 @7.x]
- Treating the 8.x branch as releasable: it is development-only. [code: app/release_metadata.json @8.x]

## Related skills
Routing table: if your task involves … → open …

| If your task involves … | Open |
|---|---|
| How Mautic is built: bundles, DI, events, models, entities, controllers, AJAX, CSRF, translations, admin JS | mautic-architecture |
| Setting up DDEV/Codespaces, installing, building assets, running cron or workers locally | mautic-dev-environment |
| Writing or running PHPUnit/Codeception tests, PHPStan, Rector, black-box QA | mautic-testing |
| Opening a PR against mautic/mautic, branch choice, checklist, terminology, schema rules | mautic-contributing |
| Building a plugin, its config.php, services, migrations, permissions, extension points | mautic-plugin-development |
| Themes, GrapesJS builder, MJML, Twig sandbox, form theming | mautic-theme-development |
| Release history, updating, migrations, the 7.x→8.x guide and event map | mautic-upgrades-and-versions |
| Parameters, `config/local.php`, env vars, Configuration UI, installer | mautic-configuration |
| Console commands, cron schedule, locking, Messenger, cache | mautic-cron-and-queues |
| "X does not work / is stuck / is not tracked" | mautic-troubleshooting |
| Contacts, Companies, custom fields, import, DNC, identification, merge, tags, UTM, frequency rules | mautic-contacts |
| Segment filters, operators, membership, rebuilds | mautic-segments |
| Campaign builder, sources, actions/decisions/conditions, scheduling, execution, new campaign event types | mautic-campaigns |
| Sending eligibility, tokens, opens/clicks, unsubscribe, bounces, transports, A/B tests | mautic-emails |
| Form fields, actions, submissions, kiosk mode, progressive profiling, embedding | mautic-forms |
| Landing Pages, tracking script, page hits, redirects, Dynamic Web Content | mautic-pages-and-tracking |
| Assets and downloads, Categories, Projects | mautic-assets-categories-projects |
| Point Actions, Point Triggers, Point Groups, Stages | mautic-points-and-stages |
| Reports, scheduled reports, Dashboard widgets | mautic-reports-and-dashboard |
| SMS, push, Marketing Messages, Focus Items, social, channel registration | mautic-channels |
| Users, Roles, permissions, login, SAML, audit log of user changes | mautic-users-and-permissions |
| REST API auth, conventions, endpoint inventory | mautic-rest-api |
| Outgoing Webhooks, payloads, delivery, signatures | mautic-webhooks |
| Integrations framework, sync engine, CRM plugins, Marketplace | mautic-integrations |

Common multi-skill tasks:

| Task | Open, in order |
|---|---|
| Write a functional test for a campaign email decision (opens/clicks) | mautic-campaigns + mautic-emails + mautic-testing |
| Why did this Contact not get the email? | mautic-troubleshooting → mautic-emails → mautic-contacts (DNC, frequency) |
| Contact never entered the Campaign | mautic-troubleshooting → mautic-campaigns → mautic-segments → mautic-cron-and-queues |
| Add a custom campaign action in a plugin | mautic-plugin-development + mautic-campaigns + mautic-upgrades-and-versions |
| Port a 7.x plugin to 8.x | mautic-upgrades-and-versions + mautic-plugin-development + mautic-architecture |
| Form submission should create a Contact and start a Campaign | mautic-forms + mautic-contacts + mautic-campaigns |
| Add a field to an entity in core | mautic-architecture + mautic-contributing + mautic-rest-api |
| Page visits or clicks not recorded | mautic-pages-and-tracking + mautic-troubleshooting |

## Reference files
- `references/glossary.md` — full glossary: definition, code name, table, citation and owning skill for every term; open when a term is unfamiliar.
- `references/task-routing.md` — 40+ common tasks mapped to skill combinations and the first file to open; open when the task spans areas.
- `references/pr-history.md` — not yet generated; PR-derived history is added in a later pass.
