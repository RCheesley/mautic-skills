---
name: mautic-cron-and-queues
description: "Mautic background processing: every console command in 7.x (purpose, options, cron frequency, locking), the ModeratedCommand lock (--bypass-locking, --lock_mode, 'Script in progress'), a recommended cron schedule and ordering, Symfony Messenger (email/hit/failed transports, messenger:consume, retries, failure transport, what happens with no worker), and the CacheBundle (filesystem, Redis, Memcached; mautic:cache:clear). Use whenever a task mentions cron, crontab, cron jobs, scheduled tasks, 'nothing happens', emails not sending, campaign not firing, segment not rebuilding, bin/console, mautic:segments:update, mautic:campaigns:trigger, mautic:broadcasts:send, mautic:webhooks:process, messenger:consume, messenger_messages, queue settings, Supervisor workers, Redis or Memcached cache, writing a new console command or plugin background work, or touches app/bundles/CoreBundle/Command/, app/bundles/MessengerBundle/ or app/bundles/CacheBundle/."
---
# Mautic Cron Jobs, Commands, Queues and Cache

## Scope
Mautic does most work outside the web request: console commands run from cron, and Symfony Messenger workers
process queued Emails, email opens and page hits. This skill covers every console command, the shared lock
(`ModeratedCommand`), the cron schedule, Messenger and the application cache
[code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-224 @7.x] [code: app/config/config.php:102-126 @7.x].
Out of scope: what each command does to its domain data (mautic-segments, mautic-campaigns, mautic-emails,
mautic-channels, mautic-webhooks, mautic-reports-and-dashboard, mautic-contacts, mautic-integrations), the
Configuration UI in general (mautic-configuration) and diagnosis playbooks (mautic-troubleshooting).

## Expected behaviour (essentials)
Cron and commands
- Mautic has no internal scheduler. Segments, Campaign membership, Campaign events, Segment Emails/SMS, background
  imports/exports and queued Webhooks only progress when their command runs [kb: https://kb.mautic.org/article/getting-started-with-mautic.html] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html].
- Three jobs are always required: `mautic:segments:update`, `mautic:campaigns:rebuild` (alias `mautic:campaigns:update`)
  and `mautic:campaigns:trigger`. Since 5.0 the Segment rebuild no longer updates Campaign membership [code: UPGRADE-5.0.md:55 @7.x] [code: app/bundles/CampaignBundle/Command/UpdateLeadCampaignsCommand.php:25 @7.x].
- Run them in that order and staggered. A Contact added to a Segment reaches a Campaign only after the Campaign rebuild,
  and its first event only runs on the next trigger [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs].
- `mautic:campaigns:trigger` runs kickoff, then scheduled, then inactive-decision events per Campaign, newest Campaign
  first [code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:243-359 @7.x].
- Segment Emails and Segment SMS are sent only by `mautic:broadcasts:send`. No listener sends Segment notifications,
  tweets or Focus items [code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:136-183 @7.x].
- Several commands are needed only when a "do this in background" setting is on. `contact_export_in_background`
  defaults to **true**, so `mautic:contacts:scheduled_export` is needed by default [code: app/bundles/LeadBundle/Config/config.php:364 @7.x]. See references/code-map.md §3.
- `mautic:webhooks:process` does nothing unless Webhook Queue Mode is `command_process`. The default is `immediate_process` [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:59-63 @7.x] [code: app/bundles/WebhookBundle/Config/config.php:54 @7.x].
- `mautic:emails:send` and `mautic:queue:process` do not exist in 5.x–7.x. Use `messenger:consume email|hit` [code: UPGRADE-5.0.md:16,104-109 @7.x].
- `mautic:maintenance:cleanup` asks for confirmation unless `--no-interaction` or `--dry-run` is passed. It exits 1 when
  neither `--days-old` nor `--gdpr` is given [code: app/bundles/CoreBundle/Command/CleanupMaintenanceCommand.php:100-122 @7.x].

Locking (`ModeratedCommand`)
- Only these commands lock: segments:update, campaigns:rebuild, campaigns:trigger, campaigns:summarize,
  broadcasts:send, messages:send, email:sendwinner, custom-field:create-column, maintenance:cleanup, unusedip:delete [code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:225 @7.x] [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:89 @7.x].
- Every other command (import, webhooks:process, reports:scheduler, email:fetch, integration sync) can overlap with
  itself [code: app/bundles/ReportBundle/Scheduler/Command/ExportSchedulerCommand.php:38-78 @7.x].
- `segments:stat`, `entity:export` and `entity:import` accept the lock options but never lock [code: app/bundles/CoreBundle/Command/EntityExportCommand.php:46-81 @7.x].
- The lock key is the command name plus a moderation key (Segment id, Campaign id + thread, channel/id/thread). Runs with
  different keys run in parallel, including an all-Segments run and a single-Segment run [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:102 @7.x].
- A locked-out run prints `Script in progress. Can force execution by using --bypass-locking.` and exits **0**
  [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:113-117 @7.x].
- `--lock_mode` defaults to `pid`. The lock file is `var/run/sf.<key>.<sha256>.lock` and is honoured while the stored
  pid is alive. Without `posix_getpgid`/`getmypid` the mode silently becomes `flock`. `redis` uses `cache_adapter_redis`
  [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:137-212 @7.x].
- `--timeout` is only a lock TTL in `flock`/`redis` mode (redis default 3600 s). It does nothing in `pid` mode, whatever
  the help text says [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:64,85-88,209 @7.x].
- `--bypass-locking` skips locking entirely. `--force` is its deprecated alias. `file_lock` maps to `flock` in 7.x and is an error in 8.x [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:79-99 @7.x] [code: UPGRADE-8.0.md:267 @8.x].

Messenger
- There are three transports: `email` (outbound `SendEmailMessage`), `hit` (email opens and page hits) and `failed`. Their DSNs are
  `messenger_dsn_email`, `messenger_dsn_hit` and `messenger_dsn_failed` [code: app/config/config.php:102-125 @7.x].
- Both business DSNs default to `sync://`, which means immediate, in-process handling with no worker needed. Any other DSN (`doctrine://default`,
  `redis://…`) queues messages until `messenger:consume <transport>` runs [code: app/bundles/MessengerBundle/Config/config.php:7-8 @7.x].
- With `sync://` the SMTP/API call runs inside the web request or cron command, which marks failures there. With a queue
  the request only stores the message; delivery errors appear in the worker [code: app/bundles/EmailBundle/Helper/MailHelper.php:402-414 @7.x].
- Retries: 3 retries at about 1 s, 2 s and 4 s (delay 1000 ms, multiplier 2, no max delay). After that the message goes to `failed`
  [code: app/bundles/MessengerBundle/Retry/RetryStrategy.php:31-43 @7.x].
- An empty failure DSN resolves to `null://`, so exhausted messages are discarded and `messenger:failed:*` shows nothing
  [code: app/bundles/MessengerBundle/DependencyInjection/EnvProcessor/MessengerNullableEnvVarProcessor.php:11-21 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#queue-for-failures].
- If a queue DSN is set and no worker runs, Emails are not sent and opens are not recorded. Page hits stay as bare rows
  without page, Contact or UTM data, and Campaign "opens email"/"visits page" decisions never fire. Nothing alerts [code: app/bundles/PageBundle/Model/PageModel.php:468-529 @7.x].
- Open and page-hit processing is not idempotent. A redelivered or manually retried message double-counts and re-fires
  Campaign listeners [code: app/bundles/EmailBundle/Model/EmailModel.php:463-544 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:622-711 @7.x].
- A missing page, redirect or Contact in a page-hit message is unrecoverable and goes straight to `failed`. Email-open deadlocks
  are retried. Page-hit persistence errors are swallowed in `prod` [code: app/bundles/MessengerBundle/MessageHandler/PageHitNotificationHandler.php:49-84 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:690-706 @7.x].
- A cron-run `messenger:consume` needs `--limit`, `--time-limit` or `--memory-limit`. Otherwise run it under
  Supervisor or systemd [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#process-email-queue-cron-job].
- A running worker keeps the DSNs and retry settings it booted with. Restart it after changing Queue Settings (inferred
  from boot-time env resolution) [code: app/config/config.php:106,112,117 @7.x].

Cache
- `mautic:cache:clear` empties the Mautic data cache pool (`cache_adapter`, default filesystem under `var/tmp`) and
  exits 1 on failure. It does not touch `var/cache`. Symfony `cache:clear` rebuilds `var/cache` and also clears that pool
  [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:28-31 @7.x] [code: app/bundles/CacheBundle/EventListener/CacheClearSubscriber.php:26-42 @7.x].
- `cache_adapter_tag_aware` must name a tag-aware adapter. Plain `mautic.cache.adapter.redis` breaks dashboards, Forms
  and Focus on first use [code: app/bundles/CacheBundle/Cache/CacheProviderTagAware.php:11-17 @7.x].

### Recommended cron schedule
Order and frequencies, each with its source. Where no source gives a frequency the table says so. Choose a cadence that fits
your volume and keep the lock in mind.

| # | Command | Frequency | Source |
|---|---|---|---|
| 1 | `mautic:segments:update` | minutes 0,15,30,45 (docs example); every 5 min (KB) | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#segment-cron-jobs] [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html] |
| 2 | `mautic:campaigns:rebuild` (`:update`) | minutes 5,20,35,50 (docs); every 5 min (KB) | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs] [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html] |
| 3 | `mautic:campaigns:trigger` | minutes 10,25,40,55 (docs); every 5 min (KB) | same as above |
| 4 | `mautic:broadcasts:send` | no source gives a frequency | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-broadcasts-segment-emails-cron-job] |
| 5 | `mautic:messages:send` (frequency rules) | no source gives a frequency | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs] |
| 6 | `messenger:consume email --time-limit=…` (queue DSN only) | KB: every 10 min with `--limit=60 --time-limit=480 --memory-limit=128M`; KB: every 5 min with `--time-limit=240`; docs: none (prefers Supervisor/systemd) | [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html] [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html] |
| 7 | `messenger:consume hit` (queue hit DSN only) | no source gives a frequency | [code: app/bundles/MessengerBundle/README.md:80-86 @7.x] |
| 8 | `mautic:email:sendwinner` | "on a regular interval" (no number) | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#determine-a-b-test-winner-cron-job] |
| 9 | `mautic:import`, `mautic:contacts:scheduled_export`, `mautic:webhooks:process`, `mautic:email:fetch`, background-mode commands | no source gives a frequency | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html] |
| 10 | `mautic:reports:scheduler` and, staggered, `mautic:reports:scheduler --cleanup-only` | no interval in docs; must run at least daily because schedules fall due at 00:00 (code inference) | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-reports-cron-job] [code: app/bundles/ReportBundle/Scheduler/Builder/SchedulerBuilder.php:46-51 @7.x] |
| 11 | `mautic:maintenance:cleanup --days-old=365 --no-interaction` | daily (KB); docs: none | [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html] |
| 12 | `mautic:donotsell:download` then `mautic:max-mind:purge` | once per week, one after the other | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#maxmind-ccpa-compliance-cron-job] |
| 13 | `mautic:iplookup:download` | after MaxMind's update on the first Tuesday of the month (docs give no cron line) | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#update-maxmind-geolite2-ip-database-cron-job] |

Example crontab built only from the documented values (run as the web-server user, from the Mautic root). Add `--no-interaction --no-ansi`
and log redirection to each line [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#tips-troubleshooting]:
```
0,15,30,45  * * * *  php bin/console mautic:segments:update   --no-interaction --no-ansi >>var/logs/cron.log 2>&1
5,20,35,50  * * * *  php bin/console mautic:campaigns:rebuild --no-interaction --no-ansi >>var/logs/cron.log 2>&1
10,25,40,55 * * * *  php bin/console mautic:campaigns:trigger --no-interaction --no-ansi >>var/logs/cron.log 2>&1
```
The full per-command table (options, exit codes, locks) is in references/commands.md.

## Where it lives
| Concern | Path |
|---|---|
| Lock base class | `app/bundles/CoreBundle/Command/ModeratedCommand.php` |
| Signal handling | `app/bundles/CoreBundle/ProcessSignal/ProcessSignalService.php` |
| Commands | `app/bundles/*/Command/`, `app/bundles/LeadBundle/Field/Command/`, `app/bundles/ReportBundle/Scheduler/Command/`, `plugins/MauticSocialBundle/Command/` |
| Messenger wiring | `app/config/config.php:102-126` (transports, routing, `failure_transport`) |
| Messenger parameters, tab | `app/bundles/MessengerBundle/Config/config.php`, `Form/Type/ConfigType.php`, `/s/config/edit/messengerconfig` |
| Messages, handlers, retry | `app/bundles/MessengerBundle/Message/`, `MessageHandler/`, `Retry/RetryStrategy.php` |
| Dispatch sites | `EmailBundle/Controller/PublicController.php:131-145`, `PageBundle/Model/PageModel.php:468-506`, `EmailBundle/Helper/MailHelper.php:402-414` |
| Cache | `app/bundles/CacheBundle/` (providers, adapters, `mautic:cache:clear`, `CacheClearSubscriber`) |
| Deprecated cache | `app/bundles/CoreBundle/Helper/CacheStorageHelper.php` |
| Legacy queue leftover | `app/bundles/QueueBundle/Config/config.php` (empty, unregistered) |
| Tests | `CoreBundle/Tests/Unit/Command/ModeratedCommandTest.php`, `MessengerBundle/Tests/`, `CacheBundle/Tests/` |

Sources: [code: app/bundles/MessengerBundle/Config/services.php:9-18 @7.x] [code: app/bundles/CacheBundle/Config/services.php:11-48 @7.x]. Full map: references/code-map.md.

## How to change or extend it
- New console command: add `#[AsCommand(name: ..., description: ...)]` (PHPStan-enforced). For cron work, extend
  `ModeratedCommand`, call `parent::configure()`, return `Command::SUCCESS` when `checkRunStatus()` is false, and call
  `completeRun()` on every exit path. Pass a moderation key to allow parallel runs per id [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:76-135 @7.x] [code: .github/prompts/write-test.prompt.md:33-37 @7.x].
- For long loops, use `ProcessSignalService` to stop cleanly on SIGTERM/SIGINT and return `ExitCode::TERMINATED`
  [code: app/bundles/CoreBundle/ProcessSignal/ProcessSignalService.php:22-80 @7.x].
- Prefer a "background" setting plus a command over long work in a request. Declare its default in `Config/config.php` and
  document the cron line [code: app/bundles/LeadBundle/Config/config.php:338-373 @7.x].
- New async work: create a message DTO and an `#[AsMessageHandler]` service. Route it to `email`/`hit` in
  `framework.messenger.routing`; unrouted messages run synchronously (inferred). Make handlers idempotent or accept
  duplicates. Throw `UnrecoverableExceptionInterface` for bad payloads and `RecoverableMessageHandlingException` for transient DB errors
  [code: app/bundles/MessengerBundle/MessageHandler/EmailHitNotificationHandler.php:36-40 @7.x] [code: app/bundles/MessengerBundle/Exceptions/InvalidPayloadException.php:9-18 @7.x].
- New transport scheme: register a `TransportFactoryInterface` service. The DSN validator accepts its scheme automatically
  [code: app/bundles/MessengerBundle/Validator/DsnValidator.php:43-45 @7.x].
- Hook into sending: add an `#[AsMessageHandler]` for `SendEmailMessage` with a priority (pattern
  `RemoveReportAttachmentHandler`, -1000) [code: app/bundles/MessengerBundle/MessageHandler/RemoveReportAttachmentHandler.php:13-22 @7.x].
- Cache: inject `CacheProviderInterface` or `CacheProviderTagAwareInterface`, never `CacheStorageHelper` (removed in 8.x).
  Treat both `null` and `false` as a miss to support 7.x and 8.x [code: app/bundles/CacheBundle/Config/services.php:38-40 @7.x] [code: UPGRADE-8.0.md @8.x].
- Keep BC: command names, aliases and option names are used in customers' crontabs. Add aliases rather than renaming
  (as with `mautic:campaigns:update`, `mautic:segments:rebuild`) [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:22 @7.x].

## How to test it
- Functional command tests: extend `MauticMysqlTestCase`, call `$this->testSymfonyCommand('name', [...])` and assert
  `getStatusCode()` and `getDisplay()`. `--bypass-locking` is added automatically, so test locking in a unit test
  [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:212-216 @7.x].
- Locking: copy `app/bundles/CoreBundle/Tests/Unit/Command/ModeratedCommandTest.php` (pid, flock, redis, bypass)
  [code: app/bundles/CoreBundle/Tests/Unit/Command/ModeratedCommandTest.php:65-359 @7.x].
- Messenger: the tests use `messenger_dsn_email=in-memory://default` (`assertQueuedEmailCount`) and `messenger_dsn_hit=sync://`.
  Set `$this->configParams['messenger_dsn_email'] = 'sync://'` to assert real sends
  [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x].
- Copy from: `WebhookBundle/Tests/Command/DeleteWebhookLogsCommandTest.php`,
  `ReportBundle/Tests/Scheduler/Command/ExportSchedulerCommandTest.php`,
  `MessengerBundle/Tests/MessageHandler/EmailHitNotificationHandlerTest.php`,
  `ReportBundle/Tests/Controller/ReportControllerFunctionalTest.php:553-596` (queue DSN end to end).
- A good regression test asserts the exit code, the side effect in the DB, and for moderated commands that a second run with
  the same key is skipped with exit 0. Details: references/test-patterns.md.

## Version notes
- ≤ 4.x: Swiftmailer spool plus `mautic:emails:send`; QueueBundle (RabbitMQ/Beanstalkd) plus `mautic:queue:process` [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html] [docs: https://docs.mautic.org/en/7.2/queue/queue.html].
- 5.0: Symfony Mailer and Messenger replace both. The Segment rebuild stops updating Campaigns [code: UPGRADE-5.0.md:16,55,104-109 @7.x].
- 5.1: Campaigns are triggered newest first. `mautic:webhooks:process` gains range mode [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs].
- 7.0: the Messenger `TestHandler` is removed, so the test button cannot succeed. `symfony/amqp-messenger` is no longer bundled [code: UPGRADE-7.0.md:15,53 @7.x].
- 8.x: `--lock_mode=file_lock` errors. `CacheStorageHelper` and `cache_items` are removed. `mautic.cache.adapter.*` ids are gone, so use class
  names. A cache miss returns `null`. Symfony 8.1 and PHP 8.4 are required [code: UPGRADE-8.0.md:267 @8.x] [PR #17033] [PR #17155]. See references/version-notes.md.

## Pitfalls
- "Locked" and "ran" both exit 0. A stuck run blocks every later cron run of the same key with no non-zero exit. Check
  `var/run/*.lock` and the stored pid [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:113-117,171-179 @7.x].
- `mautic:email:sendwinner` exits **1** whenever the A/B winner cannot be decided yet. Cron monitors treat this as a failure,
  but it is intended ("try again") [code: app/bundles/EmailBundle/Command/SendWinnerEmailCommand.php:21-77 @7.x].
- `mautic:reports:scheduler` has no lock. Overlapping runs can append twice to the same CSV and send duplicate Report
  Emails [code: app/bundles/ReportBundle/Model/ExportHandler.php:33 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#preventing-duplicate-report-emails].
- The Queue Settings "Send test message" button cannot report success in 7.x, because no handler exists for the test messages
  [code: UPGRADE-7.0.md:15 @7.x] [code: app/bundles/MessengerBundle/Controller/AjaxController.php:26-38 @7.x].
- Docs say only Email uses the queue, but the `hit` transport also queues email opens and page hits [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#purpose-of-the-queuing] [code: app/config/config.php:111-125 @7.x].
- Docs document `mautic:campaigns:trigger --max-events`, which does not exist. The cap is `--campaign-limit` [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs] [code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:84 @7.x].
- Emails count as sent once queued. A dead worker leaves "sent" Emails undelivered [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html].
- KB articles that put a `messenger` → `transports` array in `local.php` do not match 7.x. Set `messenger_dsn_email` etc. or
  use the Queue Settings tab [code: app/bundles/MessengerBundle/Config/config.php:6-14 @7.x] [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html].
- Any DSN other than `sync://` needs a host (`doctrine://default`, not `doctrine://`). Hand-edited DSNs in `local.php` must be
  URL-encoded [code: app/bundles/CoreBundle/Helper/Dsn/Dsn.php:44-58 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#smtp-transport].
- `CacheProvider::clear($prefix)` ignores the prefix and clears the whole pool [code: app/bundles/CacheBundle/Cache/AbstractCacheProvider.php:55-58 @7.x].
- Docs and the CLI page list commands that are not in 7.x (`mautic:citrix:sync`, `mautic:integration:pipedrive:*`,
  `mautic:queue:process`, `mautic:email:send`) [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#mautic-commands] [docs: https://docs.mautic.org/en/7.2/queue/queue.html].
- Open question: the `messenger_messages` table name, `auto_setup` and table-prefix handling come from Symfony's Doctrine
  transport and could not be verified (no `vendor/` in the analysed tree; no migration creates the table) [unverified] [code: app/migrations @7.x].

## Related skills
- mautic-segments: what `mautic:segments:update` does, Segment count caching, `lead:list:count-cache-update`.
- mautic-campaigns: `mautic:campaigns:rebuild/trigger/execute/resume-stuck` semantics, event scheduling.
- mautic-emails: Segment Email sending, A/B winner, `mailer_dsn`, monitored inbox.
- mautic-channels: `mautic:broadcasts:send`, Marketing Messages, frequency rules and `mautic:messages:send`.
- mautic-reports-and-dashboard: `mautic:reports:scheduler`, widget caching.
- mautic-webhooks: Webhook queue mode, `mautic:webhooks:process`, log trimming.
- mautic-integrations: `mautic:integrations:sync`, legacy fetchleads/pushleadactivity, plugin reload.
- mautic-contacts: `mautic:import`, scheduled exports, custom-field column commands, dedupe.
- mautic-configuration: the Configuration UI, `local.php`, env vars, Queue/Cache parameters.
- mautic-dev-environment: running commands through DDEV, the test suite.
- mautic-troubleshooting: "emails not sending", "campaign not firing" diagnosis.
- mautic-upgrades-and-versions: updater commands, `cache:clear` after updates, 8.x migration.

## Reference files
- references/commands.md: the full command inventory (bundle, purpose, options with defaults, cron frequency with source, lock, exit codes). Open it for any question about a specific command.
- references/behaviour.md: the numbered behaviour spec for cron, locking, Messenger, cache and legacy queues.
- references/code-map.md: files, background-mode parameters, Messenger and cache parameters and env vars, tests.
- references/docs-digest.md: what docs.mautic.org and the KB say, and where they disagree with the code.
- references/test-patterns.md: base classes, command and lock tests, Messenger and cache test patterns.
- references/version-notes.md: ≤ 4.x history, 5.x/7.x changes and the 8.x delta.
- references/pr-history.md: not yet generated; PR-derived history is added in a later pass.
