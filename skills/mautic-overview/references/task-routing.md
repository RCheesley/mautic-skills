# Task routing: which skills to open

Each row is a common task, the skills to open in order, and the first file to read. Skill names are directories under
`skills/`. "behaviour" means that skill's `references/behaviour.md`; "test-patterns" means `references/test-patterns.md`.
The "Why" column states the cross-area fact that makes the combination necessary, with its source.

## Contents
1. Testing and QA (1–10)
2. Diagnosing problems (11–20)
3. Changing core (21–30)
4. Building plugins, integrations and themes (31–40)
5. Operating an instance (41–48)

## 1. Testing and QA

| # | Task | Open, in order | Start with | Why |
|---|---|---|---|---|
| 1 | Write a functional test for a campaign email decision (open/click) | mautic-campaigns → mautic-emails → mautic-testing | mautic-campaigns behaviour (decisions) | The decision's "yes" path runs in real time when the Email bundle reports the open [code: app/bundles/CampaignBundle/Executioner/RealTimeExecutioner.php:58-112,168-176 @7.x] |
| 2 | Test that a Segment filter selects the right Contacts | mautic-segments → mautic-testing | mautic-segments test-patterns | Dynamic membership is materialised by the rebuild command [code: app/bundles/LeadBundle/Model/ListModel.php:383-633 @7.x] |
| 3 | Test a public form submission creating a Contact | mautic-forms → mautic-contacts → mautic-testing | mautic-forms test-patterns | The test client is logged in, so `ContactTracker` returns null; map an email field [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:51-60 @7.x] |
| 4 | Test page-hit or asset-download tracking | mautic-pages-and-tracking / mautic-assets-categories-projects → mautic-testing | mautic-testing (logoutUser) | Logged-in Users are not tracked [code: app/bundles/PageBundle/Model/PageModel.php:410-412 @7.x] [code: app/bundles/AssetBundle/Model/AssetModel.php:104-116 @7.x] |
| 5 | Test point awards from a page visit or form submit | mautic-points-and-stages → mautic-testing | mautic-points-and-stages pitfalls | Point scoring skips every logged-in User [code: app/bundles/PointBundle/Model/PointModel.php:176-178 @7.x] |
| 6 | Test an API endpoint (CRUD, batch, filters) | mautic-rest-api → area skill → mautic-testing | mautic-rest-api endpoint inventory | Conventions come from `CommonApiController`; resource side effects from the area skill |
| 7 | Test a console command (segments/campaigns/emails) | mautic-cron-and-queues → area skill → mautic-testing | mautic-cron-and-queues command inventory | Commands share the `ModeratedCommand` lock [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-224 @7.x] |
| 8 | Assert an email was sent or queued in a test | mautic-emails → mautic-testing | mautic-testing (mailer and Messenger assertions) | Sending is via Symfony Mailer, optionally through Messenger [code: app/bundles/EmailBundle/Helper/MailHelper.php:402-414 @7.x] |
| 9 | Black-box QA of a running instance | mautic-testing → mautic-dev-environment → area skill behaviour | mautic-testing (black-box section) | Behaviour files are the test oracle |
| 10 | Test a permission check (own vs other) | mautic-users-and-permissions → mautic-testing | mautic-users-and-permissions behaviour | Permission strings resolve through `CorePermissions` [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x] |

## 2. Diagnosing problems

| # | Task | Open, in order | Start with | Why |
|---|---|---|---|---|
| 11 | Contact did not receive an Email | mautic-troubleshooting → mautic-emails → mautic-contacts | mautic-emails behaviour (eligibility) | DNC, frequency rules, category opt-out and publish state all gate sending [code: app/bundles/EmailBundle/Model/EmailModel.php:1098-1107 @7.x] |
| 12 | Emails stuck as pending / never sent | mautic-troubleshooting → mautic-cron-and-queues → mautic-emails | mautic-cron-and-queues (Messenger) | A queue DSN needs `messenger:consume` [code: app/bundles/MessengerBundle/Config/config.php:7-8 @7.x] |
| 13 | Contact never entered a Campaign | mautic-troubleshooting → mautic-campaigns → mautic-segments | mautic-campaigns behaviour (membership) | Segment sources need `mautic:campaigns:update` from cron [code: app/bundles/CampaignBundle/Command/UpdateLeadCampaignsCommand.php:162-234 @7.x] |
| 14 | Campaign event never fires or fires late | mautic-campaigns → mautic-cron-and-queues | mautic-campaigns behaviour (scheduling) | `mautic:campaigns:trigger` runs kickoff, scheduled and inactive phases [code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:243-271 @7.x] |
| 15 | A Contact re-entering (or not) a Campaign | mautic-campaigns | mautic-campaigns behaviour (Allow restart) | Without "Allow restart" a Contact with any event log is never re-added [code: app/bundles/CampaignBundle/Entity/LeadRepository.php:376-378 @7.x] |
| 16 | Segment stuck "building" or wrong count | mautic-troubleshooting → mautic-segments → mautic-cron-and-queues | mautic-segments pitfalls | Membership changes only when the rebuild runs [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#segment-cron-jobs] |
| 17 | Page visits or clicks not recorded | mautic-troubleshooting → mautic-pages-and-tracking | mautic-pages-and-tracking behaviour | No hit for logged-in Users, `Blocked-Tracking`, untrackable requests or bot clicks [code: app/bundles/PageBundle/Model/PageModel.php:410-416,427-433,460-463 @7.x] |
| 18 | Duplicate Contacts or unexpected merges | mautic-contacts → mautic-forms | mautic-contacts behaviour (identification) | Kiosk mode reuses an email match without merging [code: app/bundles/FormBundle/Model/SubmissionModel.php:935-955 @7.x] |
| 19 | Webhook not delivered or auto-unpublished | mautic-webhooks → mautic-cron-and-queues | mautic-webhooks behaviour | Queued delivery depends on `mautic:webhooks:process` from cron [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html] |
| 20 | Setting saved in the UI has no effect | mautic-configuration | mautic-configuration pitfalls | A real `MAUTIC_<KEY>` env var beats `local.php` [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:91-105 @7.x] |

## 3. Changing core

| # | Task | Open, in order | Start with | Why |
|---|---|---|---|---|
| 21 | Add a field or column to a core entity | mautic-architecture → mautic-contributing → mautic-rest-api → mautic-upgrades-and-versions | mautic-contributing (schema-change rules) | Entity metadata and a migration change together |
| 22 | Add a Contact custom-field type or behaviour | mautic-contacts → mautic-segments → mautic-reports-and-dashboard | mautic-contacts code-map | Unique fields change column type and add an index [code: app/bundles/LeadBundle/Field/SchemaDefinition.php:17-23 @7.x] |
| 23 | Add a new Segment filter or operator | mautic-segments → mautic-contacts → mautic-testing | mautic-segments code-map | Filters live in `LeadBundle/Segment/` |
| 24 | Change unsubscribe or Preference Center behaviour | mautic-emails → mautic-contacts → mautic-pages-and-tracking | mautic-emails behaviour | Unsubscribe writes DNC unless the Preference Center is on [code: app/bundles/EmailBundle/Controller/PublicController.php:267-352 @7.x] |
| 25 | Add a new email token | mautic-emails → mautic-theme-development | mautic-emails code-map (token events) | Tokens are resolved per Contact at render time [code: app/bundles/EmailBundle/Helper/MailHelper.php:1963-1995 @7.x] |
| 26 | Add a new console command or cron job | mautic-cron-and-queues → mautic-architecture | mautic-cron-and-queues (ModeratedCommand) | Long-running commands extend the lock base [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-224 @7.x] |
| 27 | Add a new permission to a bundle | mautic-users-and-permissions → mautic-architecture | mautic-users-and-permissions code-map | Stored per Role as bitwise rows [code: app/bundles/UserBundle/Entity/Permission.php:81-101 @7.x] |
| 28 | Add an AJAX action to an admin screen | mautic-architecture → mautic-testing | mautic-architecture (AJAX, CSRF) | An invalid `X-CSRF-Token` returns HTTP 200 with a flashes error [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:27-63 @7.x] |
| 29 | Add a new Report data source or column | mautic-reports-and-dashboard → area skill | mautic-reports-and-dashboard code-map | Bundles contribute contexts through events [code: app/bundles/ReportBundle/Model/ReportModel.php:187-224 @7.x] |
| 30 | Prepare and submit a core PR | mautic-contributing → mautic-testing → mautic-dev-environment | mautic-contributing SKILL | Branch targeting and the checklist decide mergeability |

## 4. Building plugins, integrations and themes

| # | Task | Open, in order | Start with | Why |
|---|---|---|---|---|
| 31 | Create a plugin skeleton | mautic-plugin-development → mautic-architecture | mautic-plugin-development SKILL | Bundles with a too-high `MINIMUM_MAUTIC_VERSION` are silently skipped [code: app/AppKernel.php:176-181 @7.x] |
| 32 | Add a custom campaign action, decision or condition | mautic-plugin-development → mautic-campaigns → mautic-upgrades-and-versions | mautic-campaigns (extension contract) | Register via `CampaignBuilderEvent` [code: app/bundles/CampaignBundle/Event/CampaignBuilderEvent.php:50-196 @7.x] |
| 33 | Add a custom form field or form action | mautic-plugin-development → mautic-forms | mautic-forms code-map | Duplicate validator keys silently overwrite [code: app/bundles/FormBundle/Event/FormBuilderEvent.php:160 @7.x] |
| 34 | Add a new channel (for example, a messaging app) | mautic-channels → mautic-plugin-development → mautic-contacts (DNC) | mautic-channels code-map | Channels register through `ChannelEvents::ADD_CHANNEL` [code: app/bundles/ChannelBundle/ChannelEvents.php:16 @7.x] |
| 35 | Add an SMS transport | mautic-channels → mautic-plugin-development | mautic-channels behaviour (SMS) | Only `MMSTransportInterface` transports send media [code: app/bundles/SmsBundle/Sms/TransportChain.php:113-117 @7.x] |
| 36 | Build a CRM sync integration | mautic-integrations → mautic-plugin-development → mautic-contacts | mautic-integrations SKILL | Modern framework is `BasicIntegration` plus the sync engine [code: app/bundles/IntegrationsBundle/Integration/BasicIntegration.php:10-40 @7.x] |
| 37 | Add a webhook event type from a plugin | mautic-webhooks → mautic-plugin-development | mautic-webhooks code-map | Webhook event subscriptions are stored per Webhook [code: app/bundles/WebhookBundle/Entity/Event.php:39-65 @7.x] |
| 38 | Port a 7.x plugin to 8.x | mautic-upgrades-and-versions → mautic-plugin-development → mautic-architecture | mautic-upgrades-and-versions `references/event-map-7-to-8.md` | 8.x dispatches by event class; stale constant listeners never fire [PR #17157] [PR #17183] |
| 39 | Build an Email or Landing Page theme | mautic-theme-development → mautic-emails / mautic-pages-and-tracking | mautic-theme-development SKILL | Theme templates run in a Twig sandbox [code: app/bundles/PageBundle/Tests/Functional/Controller/ThemeHelperSandboxTest.php:41-119 @7.x] |
| 40 | Extend the GrapesJS builder | mautic-theme-development → mautic-dev-environment | mautic-theme-development code-map | The builder writes final HTML to `customHtml` and needs `gjs-build` [code: plugins/GrapesJsBuilderBundle/Assets/library/js/builder.js:13-47 @7.x] [code: build/gjs_build.php:5-13 @7.x] |

## 5. Operating an instance

| # | Task | Open, in order | Start with | Why |
|---|---|---|---|---|
| 41 | Set up a local dev instance | mautic-dev-environment → mautic-configuration | mautic-dev-environment SKILL | DDEV auto-installs on start [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev] |
| 42 | Write the production cron schedule | mautic-cron-and-queues | mautic-cron-and-queues (schedule) | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html] |
| 43 | Switch email to a queue and run workers | mautic-cron-and-queues → mautic-emails → mautic-configuration | mautic-cron-and-queues (Messenger) | Default `sync://` needs no worker; queues do [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mautic-doesn-t-use-queues-by-default] |
| 44 | Upgrade 5.x/6.x to 7.x | mautic-upgrades-and-versions → mautic-configuration | mautic-upgrades-and-versions SKILL | PHP ≥ 8.2 and MySQL ≥ 8.4.0 / MariaDB ≥ 10.11.0 are pre-checked [code: app/bundles/CoreBundle/Helper/UpdateHelper.php:166-196 @7.x] |
| 45 | Configure SAML SSO or API access | mautic-users-and-permissions / mautic-rest-api | mautic-users-and-permissions (SAML) | API and SAML both resolve to a `User` with a Role [code: app/config/security.php:51-67 @7.x] |
| 46 | Import Contacts from CSV at scale | mautic-contacts → mautic-cron-and-queues | mautic-contacts behaviour (import) | Imports progress only when their command runs [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html] |
| 47 | Schedule a Report by email | mautic-reports-and-dashboard → mautic-cron-and-queues | mautic-reports-and-dashboard behaviour | [docs: https://docs.mautic.org/en/7.2/reports/reports.html#cron-job-to-schedule-reports] |
| 48 | Install a plugin from the Marketplace | mautic-integrations → mautic-plugin-development | mautic-integrations (Marketplace) | [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html#using-the-mautic-marketplace] |

For any task not listed: find the bundle in `mautic-architecture/references/bundle-map.md`, open its owning skill,
and add mautic-testing for tests or mautic-troubleshooting for symptoms.
