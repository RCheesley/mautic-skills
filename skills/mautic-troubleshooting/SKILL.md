---
name: mautic-troubleshooting
description: "Symptom-first diagnostic guide for Mautic 7.x (with 8.x notes). For each common symptom it lists likely causes in order, how to confirm each (log locations, SQL queries, console commands), the fix, and which skill holds the detail. Use whenever someone reports that something in Mautic does not work, is stuck, never fires or is not tracked: emails not sending or stuck pending, opens or clicks not recorded, a Segment stuck on 'Building', Campaign events not firing or Contacts (leads) not entering a Campaign, duplicate anonymous Contacts or unexpected merges, form submissions not creating Contacts, Webhooks failing or auto-disabled, API 401/403/422 errors, 'The site is currently offline', failed updates or migrations, cache or asset problems after a deploy, a plugin not appearing, scheduled Reports not sent, the Messenger queue backing up, cron printing 'Script in progress', or permission surprises. Also use when reading var/logs/mautic_prod*.php."
---
# Mautic troubleshooting

## Scope
This skill maps observed symptoms to causes, checks and fixes across all Mautic areas, for Mautic 7.2.1 with 8.x
notes. It routes to the area skills for the underlying behaviour and does not repeat their full specifications.
Development-environment and test failures are covered only briefly (see mautic-testing, mautic-dev-environment and the
upstream `.agents/skills/mautic-dev/SKILL.md`). [code: .agents/skills/mautic-dev/SKILL.md @7.x]

## Expected behaviour (essentials)

### Symptom index
Start with the first check; the full cause list for each symptom is in references/symptoms.md under the same number.

| # | Symptom | First check | Skill with the detail |
|---|---|---|---|
| 1 | Emails not sending / stuck "pending" | Run `mautic:broadcasts:send` by hand; check Continue sending, DNC and `messenger_dsn_email` | mautic-emails, mautic-cron-and-queues |
| 2 | Opens or clicks not recorded | Is `messenger_dsn_hit` async with no `messenger:consume hit`? Was it a "Send example"? | mautic-emails, mautic-pages-and-tracking |
| 3 | Segment not updating / "Building" | Run `mautic:segments:update --list-id=<id>`; look for "Script in progress", `--max-contacts`, deleted-field filters | mautic-segments |
| 4 | Campaign events not firing / stuck / Contacts not (re-)entering | All three crons in order; Campaign and Segments published; `campaign_leads.manually_removed`; "Allow restart" | mautic-campaigns |
| 5 | Contact not tracked / anonymous duplicates / unexpected merges | Test in a private window; DNT/Sec-GPC; CORS for `/mtc/event`; unique-identifier operator (OR) | mautic-pages-and-tracking, mautic-contacts |
| 6 | Form submission not creating or updating a Contact | Is any field mapped to a Contact field? Any validation error? Form published and under its limit? | mautic-forms |
| 7 | Webhooks not delivered / auto-disabled | Queue mode vs `mautic:webhooks:process`; `webhook_logs` for 410 or 100 non-2xx; private target | mautic-webhooks |
| 8 | API 401 / 403 / 422 | `errors[].type`: `api_disabled`, `access_denied`, `invalid_grant`; Role permissions; `details` | mautic-rest-api |
| 9 | "Site is currently offline" page | `var/logs/mautic_prod-<date>.php`, then the web-server log; file ownership; PHP version | mautic-configuration, mautic-architecture |
| 10 | Update or migration failure | `/s/update/schema`, `doctrine:migrations:status`; clear `var/cache`; run as web-server user | mautic-upgrades-and-versions |
| 11 | Cache and asset problems after deploy | `bin/console cache:clear` (not only `mautic:cache:clear`); assets generated; `media/generation_in_progress.txt` | mautic-dev-environment, mautic-cron-and-queues |
| 12 | Plugin not appearing after install | Directory/namespace match; `MINIMUM_MAUTIC_VERSION`; cache clear; `mautic:plugins:reload` | mautic-plugin-development, mautic-integrations |
| 13 | Scheduled Reports not sent | `mautic:reports:scheduler` on cron (at least daily); `reports_schedulers`; Report published | mautic-reports-and-dashboard |
| 14 | Messenger queue backing up | A worker per non-`sync://` transport with a stop option; DSN has a host; restart after changes | mautic-cron-and-queues |
| 15 | Cron prints "Script in progress" | `var/run/*.lock` pid still alive? Stuck process? | mautic-cron-and-queues |
| 16 | Permission surprises | Test as a non-admin; `view` means `viewown`; `isGranted()` per-request cache | mautic-users-and-permissions |
| 17 | 8.x listener silently not firing | Subscriber keyed on a constant instead of the event class | mautic-plugin-development, mautic-upgrades-and-versions |
| 18 | Development-time failures (tests, PHPStan, DDEV) | `-c app/phpunit.xml.dist`; `composer phpstan`; delete `var/cache` | mautic-testing, mautic-dev-environment |

### Cross-cutting facts behind most symptoms
- Mautic has no internal scheduler; Segments, Campaign membership and events, Segment Emails/SMS, background imports and
  queued Webhooks progress only when their command runs. [kb: https://kb.mautic.org/article/getting-started-with-mautic.html] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]
- Three crons are always required, in this order: `mautic:segments:update`, `mautic:campaigns:rebuild` (alias
  `mautic:campaigns:update`), `mautic:campaigns:trigger`. Since 5.0 the Segment rebuild does not update Campaigns.
  [code: UPGRADE-5.0.md:55 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs]
- A locked-out command prints `Script in progress. Can force execution by using --bypass-locking.` and exits 0, so a
  stuck lock looks like success. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:113-117 @7.x]
- Messenger `email` and `hit` default to `sync://`; any other DSN needs `messenger:consume <transport>`, and without a
  worker Emails are not sent, opens are not recorded and page-visit decisions never fire, with no alert.
  [code: app/bundles/MessengerBundle/Config/config.php:7-8 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:468-529 @7.x]
- With a queue DSN "sent" means "queued"; nothing marks those stats failed later. [code: app/bundles/EmailBundle/Helper/MailHelper.php:402-414 @7.x]
- Logged-in Mautic Users, `Blocked-Tracking` cookies, bots and console contexts are never tracked; test public
  behaviour in a private window. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-60 @7.x]
- `DNT: 1` and `Sec-GPC: 1` requests are never tracked. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:276-309 @7.x]
- Anonymous Contacts never fire Campaign decisions. [code: app/bundles/CampaignBundle/Executioner/RealTimeExecutioner.php:168-176 @7.x]
- A manually removed Contact is never re-added by a Segment rebuild or a Campaign rebuild. [code: app/bundles/LeadBundle/Segment/Query/ContactSegmentQueryBuilder.php:137-156 @7.x] [code: app/bundles/CampaignBundle/Membership/Action/Adder.php:66-82 @7.x]
- The Mautic log is `var/logs/mautic_<env>.php`, rotated daily, 7 files, `notice` and above unless `debug`. [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:12-25 @7.x]
- An uncaught exception in prod renders the "site is currently offline" page with HTTP 500; AJAX gets `{"errors":[...]}`. [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:156-181 @7.x]
- A real `MAUTIC_<KEY>` environment variable beats the value saved in the UI, which still shows the local.php value. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:91-105 @7.x]
- `mautic:cache:clear` clears only the Mautic data cache; compile-time settings need Symfony `cache:clear`. [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:28-31 @7.x] [code: app/config/config.php:35-44 @7.x]
- API errors use `{"errors":[{"code","message","details","type"}]}`; batches report item failures inside a 200/201. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:611-640 @7.x] [code: app/bundles/ApiBundle/Controller/CommonApiController.php:274-331 @7.x]
- Admins pass every well-formed permission check, so permission bugs only show for non-admins. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:220-235 @7.x]
- Plugin load failures are silent: a wrong directory/namespace pair or a too-high `MINIMUM_MAUTIC_VERSION` drops the
  plugin with no error. [code: app/AppKernel.php:170-181 @7.x]
- On 8.x a subscriber keyed on a kept constant loads fine and never fires. [code: 8x-changes §3.2 @8.x]

## Where it lives
| Concern | Location |
|---|---|
| Mautic log | `var/logs/mautic_<env>-<date>.php` [code: app/bundles/CoreBundle/Config/config.php:254-256 @7.x] |
| Cron output | wherever the crontab redirects it, e.g. `var/logs/cron.log` [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#tips-troubleshooting] |
| Command locks | `var/run/sf.<key>.<sha256>.lock` [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:137-212 @7.x] |
| Config | `config/local.php` < `config/parameters_local.php` < `MAUTIC_CONFIG_PARAMETERS` < real `MAUTIC_<KEY>` env [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:186-215 @7.x] |
| Offline page | `app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php` (override `custom_offline.html.twig`) [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:424-514 @7.x] |
| Asset-generation lock | `media/generation_in_progress.txt` [code: app/bundles/CoreBundle/Helper/AssetGenerationHelper.php:121-123 @7.x] |
| Schema check | `/s/update/schema` [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#checking-for-schema-updates] |
| Tables used in checks | `lead_lists_leads`, `lead_lists`, `campaign_leads`, `campaign_lead_event_log`, `email_stats`, `lead_donotcontact`, `message_queue`, `webhook_queue`, `webhook_logs`, `reports_schedulers`, `plugins` (citations in references/symptoms.md) |
| Upstream dev skill | `.agents/skills/mautic-dev/SKILL.md` [code: .agents/skills/mautic-dev/SKILL.md @7.x] |

## How to change or extend it
- Diagnose before fixing: confirm the cause with a log line, query or command output, then apply the fix from
  references/symptoms.md.
- To add a symptom, add a row to the index above and a numbered section to references/symptoms.md with causes in the
  order to check, a "Confirm" and a "Fix" per cause, and the detail skill. Copy citations from the area skill; do not
  invent new ones.
- When a fix needs a code change, switch to the area skill for extension points and maintainer norms, and to
  mautic-contributing for branch and PR rules.
- When a KB or docs procedure disagrees with 7.x, record it in references/docs-digest.md with the code citation.

## How to test it
- Reproduce public behaviour logged out: functional tests start logged in as `admin`, so call `$this->logoutUser()`
  first. [code: app/bundles/EmailBundle/Tests/Functional/EmailClickTrackingTest.php:1-56 @7.x]
- Run commands with `testSymfonyCommand()`, which adds `--bypass-locking` automatically. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:200-223 @7.x]
- Queued sends are counted by `assertQueuedEmailCount()`; set `messenger_dsn_email` to `sync://` for immediate sends. [code: app/bundles/EmailBundle/Tests/Controller/AjaxControllerFunctionalTest.php:79-89 @7.x]
- Outbound HTTP (Webhooks) is mocked; an outbound call that "succeeds" in a test proves nothing unless you queue a
  response with `ClientMockTrait::getClientMockHandler()->append(...)`. [code: app/config/config_test.php:150-154 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:274-290 @7.x]
- A good regression test for a diagnosed bug asserts the observable outcome (row written, status code, Contact state),
  not the internal call path. Full patterns: mautic-testing.

## Version notes
- 5.0 removed the file spool, `mautic:emails:send` and `mautic:queue:process`; use `messenger:consume email|hit`. [code: UPGRADE-5.0.md:16,104-109 @7.x]
- 5.0: the Segment rebuild stopped updating Campaign membership. [code: UPGRADE-5.0.md:55 @7.x]
- Since 5.x the config file is `config/local.php`, not `app/config/local.php`. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:195-216 @7.x]
- 6.0 removed the legacy builder; disabling GrapesJS does not bring it back. [code: app/bundles/CoreBundle/Assets/js/4.builder.js:1-3 @7.x]
- 7.x: the Queue Settings "Send test message" button cannot report success. [code: UPGRADE-7.0.md:15 @7.x]
- 7.x: `index_dev.php` is gone; dev mode is `APP_ENV=dev`. [code: .ddev/.env.local.dist @7.x]
- 8.x: core events dispatch by class; listeners on constants go silent. [code: 8x-changes §3.1-3.2 @8.x]
- 8.x: the `services` array in `config.php` is no longer read. [code: 8x-changes §4 Core "services group ... no longer read" @8.x]
- 8.x: `--lock_mode=file_lock` is an error (7.x maps it to `flock`). [code: UPGRADE-8.0.md:267 @8.x]

## Pitfalls
- "Locked" and "ran" both exit 0, so cron monitoring never alerts on a stuck lock. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:113-117,171-179 @7.x]
- `mautic:email:sendwinner` exits 1 while the A/B winner is undecided; that is intended. [code: app/bundles/EmailBundle/Command/SendWinnerEmailCommand.php:21-77 @7.x]
- `--timeout` does nothing in the default `pid` lock mode. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:64,85-88,209 @7.x]
- `mautic:install` exits 0 when the requirements step fails. [code: app/bundles/InstallBundle/Command/InstallCommand.php:243 @7.x]
- An empty failure DSN discards exhausted Messenger messages, so `messenger:failed:show` is always empty. [code: app/bundles/MessengerBundle/DependencyInjection/EnvProcessor/MessengerNullableEnvVarProcessor.php:11-21 @7.x]
- Retrying open or page-hit messages double-counts and re-fires Campaign listeners. [code: app/bundles/EmailBundle/Model/EmailModel.php:463-544 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:622-711 @7.x]
- A Webhook edited in the last 2 days is never auto-killed, which hides a broken endpoint during testing. [code: app/bundles/WebhookBundle/Entity/Webhook.php:507-516 @7.x]
- A UI AJAX CSRF failure is HTTP 200 with a `flashes` error, not 403. [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:34-63 @7.x]
- The "pending" count of a Segment Email is cached and not refreshed on DNC changes. [code: app/bundles/EmailBundle/Model/EmailModel.php:2394-2431 @7.x]
- Many KB fixes predate 5.0 (spool, `mautic:emails:send`, `app/config/local.php`, a `messenger` array in local.php); check references/docs-digest.md before following one. [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html] [code: app/bundles/MessengerBundle/Config/config.php:6-14 @7.x]
- The docs say only "Administrators" are ignored when testing tracking; code ignores every logged-in User. [code: app/bundles/PointBundle/Model/PointModel.php:176-178 @7.x] [docs: https://docs.mautic.org/en/7.2/campaigns/troubleshooting_campaigns.html#page-visits-aren-t-recognized]
- Maintenance cleanup deletes anonymous Contacts with raw SQL: no delete events, webhooks or audit entries. [code: app/bundles/LeadBundle/EventListener/MaintenanceSubscriber.php:26-83 @7.x]
- Open question: the `messenger_messages` table name and columns come from Symfony's Doctrine transport and were not verified in the analysed tree. [unverified] [code: app/migrations @7.x]
- Open question: the KB says logs moved to `var/logs` in 3.0 and config to `config/local.php` in 4.0, while code analysis says the loader reads `config/local.php` since 5.x. [kb: https://kb.mautic.org/article/troubleshooting-the-site-is-currently-offline-due-to-encountering-an-error-in-mautic.html] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:195-216 @7.x]

## Related skills
- mautic-emails — sending rules, pending logic, DNC, tracking pixel and links.
- mautic-cron-and-queues — every command, locks, Messenger transports and the recommended crontab.
- mautic-segments — rebuild algorithm, filters, "Building".
- mautic-campaigns — membership, rotations, decisions, scheduling, failures.
- mautic-pages-and-tracking — tracking script, hits, cookies, untrackable requests.
- mautic-contacts — identification, duplicates and merges, DNC.
- mautic-forms — submission pipeline and Contact resolution.
- mautic-webhooks — delivery modes, health and signatures.
- mautic-rest-api — authentication, error envelopes, status codes.
- mautic-users-and-permissions — permission strings and own/other rules.
- mautic-reports-and-dashboard — scheduler and exports.
- mautic-plugin-development and mautic-integrations — plugin discovery, reload, integrations.
- mautic-configuration — parameter precedence, installed state, trusted hosts.
- mautic-upgrades-and-versions — update procedures and the 7-to-8 event map.
- mautic-dev-environment and mautic-testing — local and test-time failures.
- mautic-architecture — error handler, logging, model events.

## Reference files
- references/symptoms.md — the full guide: one section per symptom with causes in order, confirm steps (logs, SQL, commands), fixes and the detail skill. Open it once the index above points to a symptom.
- references/docs-digest.md — official troubleshooting pages and KB articles with URLs, and whether each is outdated for 7.x. Open it before following a docs or KB procedure.
- No behaviour.md, code-map.md, test-patterns.md or version-notes.md: this skill routes to the area skills, which hold those.
- references/pr-history.md — not yet generated; PR-derived history is added in a later pass.
