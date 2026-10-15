# Cron, locking, Messenger and cache — behaviour specification (Mautic 7.x)

Numbered rules. Each ends with its source. "inferred" marks Symfony behaviour that could not be verified because the
analysed tree has no `vendor/`. Per-command details (options, exit codes) are in `commands.md`.

## Contents
- A. Cron in general (A1–A12)
- B. ModeratedCommand locking and signals (B1–B15)
- C. Messenger: transports, routing, configuration (C1–C14)
- D. Messenger: email sending, sync vs async (D1–D7)
- E. Messenger: email-open and page-hit processing (E1–E17)
- F. Messenger: retry, failure, ordering, no consumer (F1–F10)
- G. CacheBundle and other caches (G1–G16)
- H. Legacy QueueBundle and removed commands (H1–H5)

## A. Cron in general

A1. Mautic has no built-in scheduler. Segment rebuilds, Campaign membership, Campaign events, Segment Email/SMS
broadcasts, background imports/exports and queued Webhooks only progress when their console command runs. Without
cron jobs "nothing will happen in Mautic". [kb: https://kb.mautic.org/article/getting-started-with-mautic.html]
[docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]

A2. Cron jobs must be added manually. The docs "HIGHLY" recommend staggering the three required jobs so they do not
start in the same minute; the example is `0,15,30,45` segments:update, `5,20,35,50` campaigns:update,
`10,25,40,55` campaigns:trigger. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]

A3. The docs give only these other frequencies: shared hosts often want "every 15 or 30 minutes"; the MaxMind CCPA pair
"once per week, one after another"; MaxMind updates GeoLite2 "the first Tuesday of the month"; the A/B winner command
"on a regular interval". [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]

A4. KB guidance (newer article): segments:update, campaigns:update, campaigns:trigger and
`messenger:consume email --time-limit=240` every 5 minutes; `mautic:maintenance:cleanup --days-old=365` daily.
[kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html]

A5. Since 5.0, `mautic:segments:update` no longer updates Campaign membership; `mautic:campaigns:update`
(`mautic:campaigns:rebuild`) must run as well. [code: UPGRADE-5.0.md:55 @7.x]

A6. The order segments → campaign membership → campaign trigger matters: a Contact added to a Segment reaches the
Campaign only after the Campaign rebuild, and its first events only run on the next trigger. The docs stagger example
uses exactly this order. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs]
[code: app/bundles/CampaignBundle/Command/UpdateLeadCampaignsCommand.php:162-234 @7.x]

A7. `mautic:campaigns:trigger` runs kickoff, then scheduled, then inactive phases for each published Campaign; when all
Campaigns run they are ordered `dateAdded DESC` (newest first, since 5.1). [code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:243-359 @7.x]
[docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs]

A8. `--exclude` on `mautic:campaigns:trigger`, `mautic:campaigns:rebuild` and `mautic:segments:update` skips the listed
ids, so parallel jobs can split the work. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#exclude-processed-entities]
[code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:123-133 @7.x]

A9. `--thread-id`/`--max-threads` (campaigns:rebuild, campaigns:trigger, broadcasts:send) and
`--min-contact-id`/`--max-contact-id` split one job across processes; `--thread-id > --max-threads` exits 1.
[code: app/bundles/CampaignBundle/Command/UpdateLeadCampaignsCommand.php:150-167 @7.x]
[code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:124-130 @7.x]

A10. Run console commands from the Mautic root as the web-server user, not root; the default environment is `prod`.
[docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#running-update-commands-as-the-web-server-user]
[docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html]

A11. In cron, pass `--no-interaction --no-ansi` and append output to a log file; on hosts whose `php` drops arguments use
`php-cli` or `php -d register_argc_argv=On` (symptom: `Invalid argument supplied for foreach()` in ArgvInput.php).
[docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#tips-troubleshooting]

A12. `mautic:maintenance:cleanup` asks for confirmation unless `--dry-run` or `--no-interaction` is given, and exits 0
without deleting anything when the answer is "no". It writes an audit-log row as user `system` when it deleted data.
[code: app/bundles/CoreBundle/Command/CleanupMaintenanceCommand.php:110-179 @7.x]

## B. ModeratedCommand locking

B1. `ModeratedCommand` adds `--bypass-locking`, `--timeout|-t`, `--lock_mode|-x` (default `pid`) and deprecated
`--force|-f`. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-74 @7.x]

B2. Subclasses must call `parent::configure()`, call `checkRunStatus($input, $output[, $moderationKey])` themselves
and end with `completeRun()`. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:76-135 @7.x]

B3. Commands that lock: `mautic:segments:update`, `mautic:campaigns:rebuild`, `mautic:campaigns:trigger`,
`mautic:campaigns:summarize`, `mautic:broadcasts:send`, `mautic:messages:send`, `mautic:email:sendwinner`,
`mautic:custom-field:create-column`, `mautic:maintenance:cleanup`, `mautic:unusedip:delete`.
[code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:132 @7.x]
[code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:225 @7.x]
[code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:89 @7.x]

B4. `mautic:segments:stat`, `mautic:entity:export` and `mautic:entity:import` extend `ModeratedCommand` but never call
`checkRunStatus()`; their lock options do nothing. [code: app/bundles/LeadBundle/Command/SegmentStatCommand.php:32-52 @7.x]
[code: app/bundles/CoreBundle/Command/EntityExportCommand.php:46-81 @7.x]

B5. All other commands (including `mautic:import`, `mautic:webhooks:process`, `mautic:reports:scheduler`,
`mautic:email:fetch`, `mautic:integrations:sync`, `mautic:integration:fetchleads`) take no lock; overlapping cron runs
execute concurrently. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:59-143 @7.x]
[code: app/bundles/ReportBundle/Scheduler/Command/ExportSchedulerCommand.php:38-78 @7.x]

B6. The lock key is the command name plus the optional moderation key, so runs with different keys run in parallel:
segments `--list-id`; campaigns:rebuild campaign id; campaigns:trigger `"{campaign-id}-{thread-id}"`;
broadcasts `"{channel}-{id}-{threadId}-{maxThreads}"`; messages `channel.channelId.messageId`; sendwinner email id.
An all-Segments run and a single-Segment run do not block each other. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:102 @7.x]
[code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:224 @7.x]
[code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:98 @7.x]

B7. `--bypass-locking` (or `--force`) returns immediately without touching any lock file or Redis key.
[code: app/bundles/CoreBundle/Command/ModeratedCommand.php:79-81 @7.x]

B8. `--lock_mode` accepts `pid`, `flock`, `redis`; `file_lock` is silently mapped to `flock` (deprecated); any other
value prints `Unknown locking method specified.` and the command does not run.
[code: app/bundles/CoreBundle/Command/ModeratedCommand.php:24-27,91-99 @7.x]

B9. `pid` mode writes `var/run/sf.<sanitised key>.<sha256(key)>.lock` (run dir = `<cache dir>/../run`, created on
demand), flocks it while reading, and refuses to run if `posix_getpgid(<stored pid>)` reports a live process
(`Script with pid N in progress.`). A stale pid from a dead process is overwritten and the run proceeds.
[code: app/bundles/CoreBundle/Command/ModeratedCommand.php:104-110,146-192 @7.x]

B10. If `getmypid` or `posix_getpgid` is missing or listed in `disable_functions`, `pid` mode silently becomes `flock`.
[code: app/bundles/CoreBundle/Command/ModeratedCommand.php:137-144,214-224 @7.x]

B11. `flock` mode uses Symfony Lock `FlockStore(var/run)`; `redis` mode uses `RedisStore` built from the
`cache_adapter_redis` parameter (`dsn`, `options`) with TTL `--timeout` or 3600 s. `--timeout` is only a lock TTL in
these store modes; despite its help text it does nothing in pid mode.
[code: app/bundles/CoreBundle/Command/ModeratedCommand.php:64,85-88,194-212 @7.x]

B12. A locked-out run prints `Script in progress. Can force execution by using --bypass-locking.` and every concrete
moderated command then exits **0**, so cron monitoring cannot tell "skipped" from "ran".
[code: app/bundles/CoreBundle/Command/ModeratedCommand.php:113-117 @7.x]
[code: app/bundles/CampaignBundle/Command/UpdateLeadCampaignsCommand.php:156-157 @7.x]

B13. An unwritable run directory or pid file throws `RuntimeException` ("check that the run directory is writable").
[code: app/bundles/CoreBundle/Command/ModeratedCommand.php:104-110,157-163 @7.x]

B14. `completeRun()` releases the Symfony lock and unlinks the pid file; a null lock is tolerated.
[code: app/bundles/CoreBundle/Command/ModeratedCommand.php:125-135 @7.x]

B15. Long-running commands trap SIGTERM/SIGINT through `ProcessSignalService` (only if `pcntl_signal` exists) and stop
cleanly: `mautic:campaigns:trigger` and `mautic:contacts:scheduled_export` exit `ExitCode::TERMINATED`;
`mautic:import` stops after the current row. [code: app/bundles/CoreBundle/ProcessSignal/ProcessSignalService.php:22-80 @7.x]
[code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:166-167,276-280 @7.x]

## C. Messenger: transports, routing, configuration

C1. Three transports exist: `email`, `hit` and `failed`. Their DSNs come from `MAUTIC_MESSENGER_DSN_EMAIL`,
`MAUTIC_MESSENGER_DSN_HIT` and `MAUTIC_MESSENGER_DSN_FAILED`, which the parameter loader derives from
`messenger_dsn_email`, `messenger_dsn_hit`, `messenger_dsn_failed` in `config/local.php`.
[code: app/config/config.php:102-118 @7.x] [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:13-28 @7.x]

C2. Routing: `SendEmailMessage` and `TestEmail` → `email`; `PageHitNotification`, `EmailHitNotification` and `TestHit`
→ `hit`; `TestFailed` → `failed`. Unrouted messages are handled synchronously (inferred).
[code: app/config/config.php:119-125 @7.x]

C3. Both business DSNs default to `sync://`; a fresh install handles everything in-process and needs no worker.
[code: app/bundles/MessengerBundle/Config/config.php:7-8 @7.x]
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mautic-doesn-t-use-queues-by-default]

C4. "Sync vs async" is only the DSN scheme. `sync://` = handled in the dispatching process; anything else
(`doctrine://default`, `redis://…`, `amqp://…`) = stored and handled by `messenger:consume`. There is no
`messenger_type` parameter. [code: app/bundles/MessengerBundle/Config/config.php:6-14 @7.x]

C5. `failure_transport` is hard-wired to `failed`. An empty `messenger_dsn_failed` resolves to `null://` (the
`messenger-nullable` env processor), so messages that exhaust their retries are discarded.
[code: app/config/config.php:103,117 @7.x]
[code: app/bundles/MessengerBundle/DependencyInjection/EnvProcessor/MessengerNullableEnvVarProcessor.php:11-21 @7.x]
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#queue-for-failures]

C6. `sync://` is the only DSN accepted without a host; every other DSN needs `scheme://host`, hence
`doctrine://default`. [code: app/bundles/CoreBundle/Helper/Dsn/Dsn.php:9-11,44-58 @7.x]

C7. The Queue Settings form validates each DSN: empty passes; unparsable → "Invalid DSN"; a scheme no installed
transport factory supports → "Unsupported scheme". `amqp://` therefore fails until `symfony/amqp-messenger` is
installed (removed from core dependencies in 7.0). [code: app/bundles/MessengerBundle/Validator/DsnValidator.php:31-45 @7.x]
[code: UPGRADE-7.0.md:53 @7.x]

C8. Documented transports: Doctrine (table `messenger_messages`, renameable), Redis (PHP ext ≥ 4.3, Redis ≥ 5.0), AMQP
(`composer require symfony/amqp-messenger`), Beanstalkd and Amazon SQS (their Composer packages).
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#how-to-enable-the-queuing]

C9. The `messenger_messages` table is not created by any Mautic migration; Symfony's Doctrine transport creates it
(auto-setup, inferred). [code: app/migrations (no reference to messenger_messages) @7.x]

C10. DSNs stored via the UI escape `%` as `%%`; the `urlencoded-dsn` env processor unescapes them and turns an
unparsable value into `invalid://null`. Values pasted into `local.php` by hand must be URL-encoded.
[code: app/bundles/ConfigBundle/Form/DataTransformer/DsnTransformer.php:79-80 @7.x]
[code: app/bundles/EmailBundle/DependencyInjection/EnvProcessor/MailerDsnEnvVarProcessor.php:12-22 @7.x]
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#smtp-transport]

C11. A real OS/`.env` variable with the same `MAUTIC_*` name overrides `local.php`.
[code: app/bundles/CoreBundle/Loader/ParameterLoader.php:88-110 @7.x]

C12. Saving configuration refreshes opcache/APCu and menu session data only; new DSNs apply on the next request.
A running `messenger:consume` keeps its old DSNs and retry settings until it restarts (inferred).
[code: app/bundles/ConfigBundle/Controller/ConfigController.php:149-154 @7.x]
[code: app/bundles/CoreBundle/Helper/CacheHelper.php:37-42 @7.x]

C13. The "Send test message" button appears only when the saved value parses as a DSN. It dispatches `TestEmail`,
`TestHit` or `TestFailed`, for which no handler exists since 7.0: with `sync://` the dispatch fails and the button
reports failure (inferred); with a queue DSN the message is stored and later fails in the worker.
[code: app/bundles/ConfigBundle/Form/Type/DsnType.php:120-133 @7.x]
[code: app/bundles/MessengerBundle/Controller/AjaxController.php:15-39 @7.x] [code: UPGRADE-7.0.md:15 @7.x]

C14. Messages are serialised with PHP's native serializer; the `Request` is flattened to its bags and rebuilt on
unserialise. [code: app/bundles/MessengerBundle/Message/Traits/MessageRequestTrait.php:32-65 @7.x]

## D. Messenger: email sending, sync vs async

D1. There is no spool in 7.x. `MailHelper::send()` hands the message to Symfony Mailer; Mailer wraps it in
`SendEmailMessage` and Mautic routes it to `email` (wrapping inferred). [code: app/bundles/EmailBundle/Helper/MailHelper.php:402-414 @7.x]
[code: app/config/config.php:120 @7.x]

D2. `mailer_dsn` decides how an Email leaves (SMTP/API); `messenger_dsn_email` decides when and in which process.
[code: app/bundles/EmailBundle/Config/config.php:146 @7.x] [code: app/config/config.php:97-110 @7.x]

D3. With `sync://`, the SMTP/API call runs inside the web request or the cron command (`mautic:broadcasts:send`,
`mautic:campaigns:trigger`); transport errors are caught there and recipients are marked failed.
[code: app/bundles/EmailBundle/Helper/MailHelper.php:405-414 @7.x]

D4. With a queue DSN the request returns once the message is stored; `messenger:consume email` makes the real call.
Transport failures then happen in the worker, are retried (F1) and then parked in `failed` or discarded.
[code: app/bundles/EmailBundle/Helper/MailHelper.php:409-414 @7.x]
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#queued-delivery]

D5. Emails are counted as sent as soon as they are written to the queue; with a browser-initiated send the progress
bar only represents queueing. [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html]
[kb: https://kb.mautic.org/article/how-to-optimize-amazon-ses-send-rate-with-mautic.html]

D6. Scheduled-Report attachments are deleted by `RemoveReportAttachmentHandler`, which runs after the mailer handler
for every `SendEmailMessage` (priority -1000). With a queue DSN the files stay on disk until the worker sends the Email.
[code: app/bundles/MessengerBundle/MessageHandler/RemoveReportAttachmentHandler.php:13-48 @7.x]
[code: app/bundles/ReportBundle/Scheduler/Model/SendSchedule.php:36-62 @7.x]

D7. The KB recommends `messenger:consume email --limit=60 --time-limit=480 --memory-limit=128M` every 10 minutes from a
lock-file-guarded script (540 s stale-lock timeout), and warns that `messenger_messages` can grow quickly.
[kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html]

## E. Messenger: email-open and page-hit processing

E1. The tracking pixel dispatches `EmailHitNotification($idHash, $request)` and always returns the pixel; `eventTime`
is captured at dispatch. [code: app/bundles/EmailBundle/Controller/PublicController.php:131-145 @7.x]

E2. If the dispatch throws (queue unreachable), the error is logged and the open is processed synchronously.
[code: app/bundles/EmailBundle/Controller/PublicController.php:139-142 @7.x]

E3. "View in browser" opens are always processed synchronously and never queued.
[code: app/bundles/EmailBundle/Controller/PublicController.php:85-91 @7.x]

E4. With a `sync://` hit DSN the handler passes `activeRequest=true` (the cookie-tracked Contact is used); with a queue DSN
it passes `false` and `hitEmail` sets the system Contact instead.
[code: app/bundles/MessengerBundle/MessageHandler/EmailHitNotificationHandler.php:24,30-37 @7.x]
[code: app/bundles/EmailBundle/Model/EmailModel.php:465-473 @7.x]

E5. Doctrine `RetryableException` (deadlock, lock-wait timeout) during an open becomes
`RecoverableMessageHandlingException` and is retried; other exceptions propagate unchanged.
[code: app/bundles/MessengerBundle/MessageHandler/EmailHitNotificationHandler.php:36-40 @7.x]

E6. Email-open processing is not idempotent: each run appends to `open_details`, inserts an `email_stats_devices` row
and dispatches `EMAIL_ON_OPEN` again. [code: app/bundles/EmailBundle/Model/EmailModel.php:463-544 @7.x]

E7. `hitPage()` returns without dispatching for logged-in sessions, the `Blocked-Tracking` cookie, untrackable IPs,
bot-classified click-throughs, or when no Contact can be identified. [code: app/bundles/PageBundle/Model/PageModel.php:409-466 @7.x]

E8. A bare `Hit` row is persisted before dispatch so the message carries a real id; the `mautic_referer_id` cookie is
set to it. [code: app/bundles/PageBundle/Model/PageModel.php:468-489 @7.x]

E9. If the page-hit dispatch throws, `processPageHit` runs synchronously. [code: app/bundles/PageBundle/Model/PageModel.php:500-506 @7.x]

E10. Until the message is consumed the hit row has no page/redirect, Contact, URL, title, referrer, UTM, geo or source
data, and the previous hit's `date_left` is not set. [code: app/bundles/PageBundle/Model/PageModel.php:522-664 @7.x]

E11. A missing page/redirect, missing Contact or vanished hit id raises `InvalidPayloadException`
(unrecoverable): the message goes to `failed` without retries. [code: app/bundles/MessengerBundle/MessageHandler/PageHitNotificationHandler.php:49-84 @7.x]
[code: app/bundles/MessengerBundle/Exceptions/InvalidPayloadException.php:9-18 @7.x]

E12. The page-hit handler always passes `activeRequest=false`; listeners of `PAGE_ON_HIT` get the Contact through the
system Contact. [code: app/bundles/MessengerBundle/MessageHandler/PageHitNotificationHandler.php:92 @7.x]

E13. Page-hit processing is not idempotent: hit counters increase and `PAGE_ON_HIT` (Campaign decisions) fires on every
run. [code: app/bundles/PageBundle/Model/PageModel.php:622-654,708-711 @7.x]

E14. Final page-hit persistence errors are logged and swallowed in `prod` (the message is acked, data may be lost) and
rethrown in `dev`; unlike opens, page-hit deadlocks are not retried. [code: app/bundles/PageBundle/Model/PageModel.php:690-706 @7.x]

E15. `lead.last_active` only moves forward (message `eventTime` newer than stored), so out-of-order consumption cannot
move it back. [code: app/bundles/EmailBundle/Model/EmailModel.php:546-548 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:713-732 @7.x]

E16. `/mtc/event` returns `success:1` immediately after `hitPage()`; `ON_CONTACT_TRACKED` fires before the queued hit
is processed. [code: app/bundles/PageBundle/Controller/PublicController.php:400-443 @7.x]

E17. Because the open and page-hit listeners (Campaign "opens email"/"visits page" decisions, Points) run inside the
handler, with a queue DSN they run in the `messenger:consume hit` process. [code: app/bundles/EmailBundle/Model/EmailModel.php:496-499 @7.x]
[code: app/bundles/PageBundle/Model/PageModel.php:708-711 @7.x]

## F. Messenger: retry, failure, ordering, no consumer

F1. Retry for `email` and `hit`: `max_retries=3`, delay 1000 ms, multiplier 2.0, max delay 0 (no cap) → retries after
about 1 s, 2 s, 4 s, then `failed`. Built once per process. [code: app/bundles/MessengerBundle/Retry/RetryStrategy.php:31-43 @7.x]
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#retry-strategy]

F2. Retry decisions ignore the exception type except Symfony's markers: `UnrecoverableExceptionInterface` skips retries;
`RecoverableMessageHandlingException` forces one (inferred Symfony semantics). [code: app/bundles/MessengerBundle/Retry/RetryStrategy.php:21-29 @7.x]

F3. The form rejects a multiplier below 1 and negative values for the other three fields (worker crash mautic/mautic#16017).
[code: app/bundles/MessengerBundle/Form/Type/ConfigType.php:57-124 @7.x]

F4. Max retries `0` disables retries. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#retry-strategy]

F5. `messenger:failed:show|retry|remove` only work with a real failure DSN; with `null://` the transport always returns
nothing. [code: app/bundles/MessengerBundle/Transport/NullTransport.php:12-28 @7.x]

F6. Mautic gives no ordering guarantee between messages and no stamps or partitions.
[code: app/bundles/MessengerBundle/Message/PageHitNotification.php:14-24 @7.x]

F7. Handlers take no application lock; several workers per transport may run in parallel and rely on DB row locks.
[code: app/bundles/MessengerBundle/MessageHandler/EmailHitNotificationHandler.php:30-40 @7.x]

F8. With a queue DSN and no running consumer: tracking endpoints keep answering, page hits exist as bare rows, email
opens are not recorded, Emails are not sent, messages accumulate in the transport, and nothing in Mautic alerts about the
backlog. Symfony Messenger worker events have no Mautic listeners. [code: app/bundles/EmailBundle/Controller/PublicController.php:131-145 @7.x]
[code: app/bundles/PageBundle/Model/PageModel.php:468-506 @7.x]

F9. If `messenger:consume` runs from cron it needs at least one of `--memory-limit`, `--limit`, `--time-limit`, or each
run becomes a long-lived process; otherwise keep workers alive with Supervisor or systemd.
[docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#process-email-queue-cron-job]
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#how-to-consume-messages-from-the-queue]

F10. Mautic ships no Supervisor, systemd or cron unit for the worker and no wrapper command.
[code: app/bundles/MessengerBundle/README.md:80-86 @7.x]

## G. CacheBundle and other caches

G1. `mautic.cache.provider` (`CacheProviderInterface`, PSR-6, plus `getSimpleCache()` PSR-16) resolves its adapter
lazily from the service id in `cache_adapter` and memoises it. [code: app/bundles/CacheBundle/Cache/AbstractCacheProvider.php:31-38,85-93 @7.x]

G2. `mautic.cache.provider_tag_aware` uses `cache_adapter_tag_aware`, which must be tag-aware; pointing it at
`mautic.cache.adapter.redis` fails an assertion on first use. [code: app/bundles/CacheBundle/Cache/CacheProviderTagAware.php:11-17 @7.x]

G3. Adapters: `mautic.cache.adapter.filesystem` (default for both), `.memcached`, `.redis` (not tag-aware),
`.redis_tag_aware`. [code: app/bundles/CacheBundle/Config/services.php:20-47 @7.x]

G4. The filesystem adapter stores items under `var/tmp`, namespace `app_cache_<cache_prefix>`, default TTL
`cache_lifetime` (86400 s); its tag pool uses Symfony's default directory and no TTL.
[code: app/bundles/CacheBundle/Cache/Adapter/FilesystemTagAwareAdapter.php:12-19 @7.x]

G5. Memcached needs `cache_adapter_memcached['servers']`; Redis needs `cache_adapter_redis['dsn']`; otherwise an
`InvalidArgumentException` is thrown. [code: app/bundles/CacheBundle/Cache/Adapter/MemcachedTagAwareAdapter.php:15-17 @7.x]
[code: app/bundles/CacheBundle/Cache/Adapter/RedisAdapterTrait.php:18-20 @7.x]

G6. Redis adapters read env vars directly (`MAUTIC_CACHE_ADAPTER_REDIS`, `MAUTIC_CACHE_PREFIX`,
`MAUTIC_CACHE_LIFETIME`, `MAUTIC_REDIS_PRIMARY_ONLY`); sentinel replication is supported.
[code: app/bundles/CacheBundle/Cache/Adapter/RedisAdapter.php:17-30 @7.x]
[code: app/bundles/CoreBundle/Helper/PRedisConnectionHelper.php:88-126 @7.x]

G7. Set `cache_prefix` when several Mautic instances share a Redis or Memcached server.
[code: app/bundles/CacheBundle/Config/config.php:13-37 @7.x]

G8. `CacheProvider::clear($prefix)` ignores the prefix and clears the whole pool (so SAML `RequestStateStore::clear()`
wipes everything). [code: app/bundles/CacheBundle/Cache/AbstractCacheProvider.php:55-58 @7.x]

G9. `mautic:cache:clear` clears only the non-tag-aware pool and exits 1 on failure; it does not touch `var/cache`.
[code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:28-31 @7.x]

G10. Symfony `cache:clear` rebuilds `var/cache` and clears the Mautic pool via `CacheClearSubscriber`
(`kernel.cache_clearer`), which silently swallows `PDOException`. [code: app/bundles/CacheBundle/EventListener/CacheClearSubscriber.php:26-42 @7.x]

G11. The updater's `DeleteCacheStep` deletes `kernel.cache_dir` and resets opcache/APCu but not the data cache pool.
[code: app/bundles/CoreBundle/Update/Step/DeleteCacheStep.php:31-38 @7.x]

G12. Cache consumers: Segment counts `segment.<id>.lead` and Campaign counts `campaign.<id>.lead` (12 h), DNC
combinations, peak interaction times, Email delivered counts (`cached_data_timeout`, 10 min), anonymous tracking-pixel
events (1 day), DWC slot names (1 day), SAML state (120 s), device detector, and tag-aware dashboard widgets, Form mapped
fields and Focus counters. [code: app/bundles/LeadBundle/Helper/SegmentCountCacheHelper.php:30-116 @7.x]
[code: app/bundles/CampaignBundle/Helper/CampaignContactCountHelper.php:14,65-76 @7.x]
[code: app/bundles/PageBundle/Helper/TrackingHelper.php:42-86 @7.x]

G13. `mautic:campaigns:trigger` recalculates the cached counts of each Campaign's source Segments after the Campaign,
or only invalidates them when `update_segment_contact_count_in_background` is on (then `lead:list:count-cache-update`
must run). [code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:412-424 @7.x]
[code: app/bundles/LeadBundle/Command/SegmentCountCacheCommand.php:34-57 @7.x]

G14. The deprecated `CacheStorageHelper` (`<prefix>cache_items` table or filesystem) is still used by Dashboard, Email,
SMS and Segment code in 7.x. [code: app/bundles/CoreBundle/Helper/CacheStorageHelper.php:9-11,160-178 @7.x]

G15. The Doctrine result cache pool `doctrine_result_cache` is an in-memory array pool, so `ResultCacheHelper` only
de-duplicates within one process; `CacheInvalidateSubscriber` deletes namespaces for User, Role, Permission, LeadField,
Plugin and Integration changes. [code: app/config/config.php:218-221,305-311 @7.x]
[code: app/bundles/CoreBundle/EventListener/CacheInvalidateSubscriber.php:48-85 @7.x]

G16. Every `MauticMysqlTestCase` clears the cache pool in setup. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:385-390 @7.x]

## H. Legacy QueueBundle and removed commands

H1. Up to 4.x, QueueBundle queued page hits and email opens via RabbitMQ or Beanstalkd (`queue_protocol`) and processed
them with `mautic:queue:process -i page_hit|email_hit`. [docs: https://docs.mautic.org/en/7.2/queue/queue.html]

H2. QueueBundle was removed in 5.0 "in favor symfony's messenger"; its events, `QueueService` and
`QueueRequestHelper` have no replacement; `mautic:queue:process` is replaced by `messenger:consume`.
[code: UPGRADE-5.0.md:104-109 @7.x]

H3. Only an empty, unregistered `app/bundles/QueueBundle/Config/config.php` remains. [code: app/bundles/QueueBundle/Config/config.php @7.x]
[code: app/AppKernel.php:128-155 @7.x]

H4. Up to 4.x, queued Email went to a filesystem spool (`var/spool`) and was "considered sent" once written there;
`mautic:emails:send` drained it. 5.0 removed the command; use `messenger:consume email`.
[kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html] [code: UPGRADE-5.0.md:16 @7.x]

H5. The `rabbitmq_*`, `beanstalkd_*` and `queue_protocol` parameters documented on the legacy Queue page have no effect
in 7.x. [docs: https://docs.mautic.org/en/7.2/queue/queue.html] [code: app/bundles/QueueBundle/Config/config.php @7.x]
