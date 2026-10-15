# Docs digest — cron jobs, CLI, queues (docs.mautic.org 7.2, kb.mautic.org)

What the official user docs and the Knowledge Base say. Where code disagrees, the code is right for 7.2.1; the
discrepancies are listed in section 5.

Main pages:
- Cron jobs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html
- CLI: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html
- Queue settings: https://docs.mautic.org/en/7.2/configuration/settings.html#queue-settings
- Legacy queue: https://docs.mautic.org/en/7.2/queue/queue.html
- Message queue (frequency rules): https://docs.mautic.org/en/7.2/queue/message_queue.html

## 1. Cron jobs page (as documented)

- Since Mautic 3 the console path is `bin/console` (2.x: `app/console`) [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html].
- Required jobs must be added manually and should be staggered [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html].
- Staggering example, verbatim order [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]:
  ```
  0,15,30,45  mautic:segments:update
  5,20,35,50  mautic:campaigns:update
  10,25,40,55 mautic:campaigns:trigger
  ```
- "Many shared hosts prefer that you run scripts every 15 or 30 minutes and may even override the scheduled times"
  [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html].

| Command | Required/optional | Documented frequency | Documented options | Anchor |
|---|---|---|---|---|
| `mautic:segments:update` | Required | example 0,15,30,45 | `--batch-limit` (300), `--max-contacts`, `--exclude` | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#segment-cron-jobs] |
| `mautic:campaigns:update` | Required | example 5,20,35,50 | `--batch-limit` (300), `--max-contacts`, `--exclude` | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs] |
| `mautic:campaigns:trigger` | Required | example 10,25,40,55 | `--batch-limit` (100), `--max-events`, `--exclude`; newest → oldest since 5.1 | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs] |
| `mautic:messages:send` | Needed with frequency rules | not stated | — | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs] |
| `mautic:campaigns:resume-stuck <id>` | Manual one-off | n/a | `--dry-run`, `--batch-limit` (100), `--min/max-contact-id`; max 500 records per run | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#resume-stuck-campaign-contacts-cron-job] |
| `mautic:custom-field:create-column`, `delete-column` | Required (background custom fields) | not stated | — | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#custom-field-cron-jobs] |
| `messenger:consume email --time-limit=160` | Optional (queue) | not stated | needs `--memory-limit`, `--limit` or `--time-limit` | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#process-email-queue-cron-job] |
| `mautic:email:fetch` | Optional (bounce management) | not stated | — | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#fetch-and-process-monitored-email-cron-job] |
| `mautic:social:monitoring` | Optional | not stated | — | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#social-monitoring-cron-job] |
| `mautic:import` | Optional | not stated | completion raises a dashboard notification | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#import-contacts-cron-job] |
| `mautic:contacts:scheduled_export` | Optional | not stated | Emails a download link | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#export-contacts-cron-job] |
| `mautic:webhooks:process` | Optional (queued Webhooks) | not stated | `--webhook-id`, `--min-id`, `--max-id` (5.1+); exit 0 with no active Webhooks | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#webhooks-cron-job] |
| `mautic:iplookup:download` | Optional | MaxMind updates on the first Tuesday of the month | — | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#update-maxmind-geolite2-ip-database-cron-job] |
| `mautic:maintenance:cleanup --days-old=365 --dry-run` | Optional | not stated | `--days-old`, `--dry-run`, `--gdpr` (3 years inactive) | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#clean-up-old-data-cron-job] |
| `mautic:donotsell:download` then `mautic:max-mind:purge` | Optional | once per week, one after another | — | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#maxmind-ccpa-compliance-cron-job] |
| `mautic:broadcasts:send [--id] [--channel]` | Optional (needed for scheduled Segment Emails) | not stated | `--limit` (100), `--batch`, `--min/max-contact-id` | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-broadcasts-segment-emails-cron-job] |
| `mautic:email:sendwinner [--id]` | Optional | "regular interval" | `--id` | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#determine-a-b-test-winner-cron-job] |
| `mautic:reports:scheduler [--report] [--cleanup-only]` | Optional | separate, staggered send and cleanup jobs | `--report`, `--cleanup-only` | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-reports-cron-job] |
| `mautic:integration:fetchleads`, `mautic:integration:pushactivity` | Optional | not stated | `--integration=<Name>` per Integration | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#configure-mautic-integration-cron-jobs] |
| `mautic:plugins:reload` | Optional | not stated | — | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#configure-mautic-integration-cron-jobs] |

Other documented facts:
- `mautic:broadcasts:send` only sends published Emails with a publish-up date, only to Contacts who have not received
  them, and also to Contacts added to the source Segments later — set an unpublish date to stop that
  [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-broadcasts-segment-emails-cron-job].
- Running Report send and cleanup at the same time can duplicate Report Emails
  [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#preventing-duplicate-report-emails].
- `--exclude` avoids re-processing for trigger, rebuild and segments:update
  [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#exclude-processed-entities].
- Troubleshooting: append `>>/path/to/file.log 2>&1`, use `--no-interaction --no-ansi`, test over SSH, use `php-cli`
  or `php -d register_argc_argv=On` [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#tips-troubleshooting].

## 2. CLI page

- Run from the Mautic root; default environment `prod`; global options `-n`, `-q`, `-v`, `-e`, `--no-debug`
  [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#options].
- `mautic:cache:clear` "clears the 10-minute Mautic cache" (Segment counts, dashboard widgets)
  [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html].
- Background Company commands apply only when `update_company_mapping_data_in_background` is true
  [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#mautic-commands].
- Aliases listed: `mautic:messages:send` = `mautic:campaigns:messagequeue` = `mautic:campaigns:messages`;
  `mautic:segments:update` = `mautic:segments:rebuild` [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#mautic-commands].

## 3. Queue settings (Messenger)

- Queueing is off by default; a fresh instance uses `sync://` [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mautic-doesn-t-use-queues-by-default].
- With queueing on, Emails are queued and sent by consumers; the page says only Email sending uses the queue
  ("planned to extend") [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#purpose-of-the-queuing].
- Transports and their requirements: Doctrine (`messenger_messages`), Redis, AMQP, Beanstalkd, Amazon SQS
  [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#how-to-enable-the-queuing].
- Consume with `php bin/console messenger:consume email`; keep it alive with Supervisor or systemd (not needed on
  Kubernetes) [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#how-to-consume-messages-from-the-queue].
- Retry strategy: max retries 3 (0 disables), delay 1000 ms, multiplier 2 (< 1 not allowed), max delay 0
  [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#retry-strategy].
- Without a failure queue, a message that fails all retries is discarded
  [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#queue-for-failures].
- Immediate delivery is the default; queued delivery is recommended for high volume or shared-host limits
  [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#immediate-delivery].

## 4. Knowledge Base

- k-doctrine (5.x, 2024): Doctrine transport via Queue Settings (scheme `doctrine`, host `default`, table
  `messenger_messages`); worker `messenger:consume email --limit=60 --time-limit=480 --memory-limit=128M -vvv`
  every 10 min from a lock-file-guarded script with a 540 s stale-lock timeout; the table can fill quickly; Emails are
  marked sent when queued [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html].
- k-hubspot (2026): segments:update, campaigns:update, campaigns:trigger and `messenger:consume email --time-limit=240`
  every 5 min; `mautic:maintenance:cleanup --days-old=365` daily [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html].
- k-sesrate (3.x/4.x, outdated): chain the cron commands sequentially to avoid overlap; uses removed
  `mautic:emails:send` [kb: https://kb.mautic.org/article/how-to-optimize-amazon-ses-send-rate-with-mautic.html].
- k-10things (4.x, outdated): filesystem spool in `var/spool`; Email "considered sent" once spooled; frequency-rule
  "queued" Emails are rescheduled 24 h later [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html].
- k-import: "Import in the background" sets status queued; `mautic:import` processes it
  [kb: https://kb.mautic.org/article/how-to-import-contacts-to-mautic-in-the-background-without-timing-out.html].
- k-getstarted: without cron jobs "nothing will happen in Mautic" [kb: https://kb.mautic.org/article/getting-started-with-mautic.html].

## 5. Where docs and code disagree (7.x)

| Docs say | Code says | Source |
|---|---|---|
| `mautic:campaigns:trigger --max-events` caps events per run | No `--max-events` option; the cap is `--campaign-limit` | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs] [code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:84,177 @7.x] |
| `mautic:campaigns:update` is the command | Real name `mautic:campaigns:rebuild`; `update` is an alias (both work) | [code: app/bundles/CampaignBundle/Command/UpdateLeadCampaignsCommand.php:25 @7.x] |
| Only Email sending uses the queue | The `hit` transport also queues email opens and page hits | [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#purpose-of-the-queuing] [code: app/config/config.php:111-125 @7.x] |
| Queued delivery stores Emails "in the configured spool directory" | No spool; Messenger transport | [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#queued-delivery] [code: UPGRADE-5.0.md:16 @7.x] |
| `mautic:cache:clear` clears the "10-minute Mautic cache" | Clears the whole configured app cache pool (items with many TTLs) | [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html] [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:28-31 @7.x] |
| Legacy queue page: `mautic:queue:process`, `mautic:email:send`, `queue_protocol`, RabbitMQ/Beanstalkd params | Removed in 5.0 | [docs: https://docs.mautic.org/en/7.2/queue/queue.html] [code: UPGRADE-5.0.md:104-109 @7.x] |
| CLI page lists `mautic:citrix:sync`, `mautic:integration:pipedrive:*` | Not registered in 7.x | [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#mautic-commands] [code: app/bundles/*/Command, plugins/*/Command (AsCommand grep) @7.x] |
| k-doctrine: `local.php` key `'messenger' => ['transports' => ['doctrine' => ['dsn' => …]]]` | Mautic reads `messenger_dsn_email` / `messenger_dsn_hit` / `messenger_dsn_failed`; transports are fixed in `app/config/config.php` | [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html] [code: app/bundles/MessengerBundle/Config/config.php:6-14 @7.x] |

## 6. Gaps in the docs

- No frequency for most jobs; no guidance on `messenger:consume hit`, the `failed` transport, `messenger:failed:*`, or
  `messenger_dsn_*` keys [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html].
- No documentation of `ModeratedCommand` locking (`--lock_mode`, `--bypass-locking`, `var/run`) or of exit codes
  [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html].

## 7. Terminology

- Use "Cron job", "Queue", "Segment", "Campaign", "Contact", "Marketing Messages", "Webhook" (capitalised product
  nouns); commands keep their legacy "lead" names [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html].
- "Queue" in the UI ("Queue Settings") means Symfony Messenger transports. "Message queue" means the frequency-rule
  `message_queue` table drained by `mautic:messages:send` [docs: https://docs.mautic.org/en/7.2/queue/message_queue.html].
