# Symptom guide (Mautic 7.x)

One section per symptom. Each section lists the likely causes in the order to check them. Each cause has a way
to confirm it and a fix. The last line names the skill that holds the detail. Commands assume the Mautic root
as the working directory and run as the web-server user. SQL assumes no table prefix; add yours if you set one.

## Contents
0. [Diagnostic toolkit (read first)](#0-diagnostic-toolkit-read-first)
1. [Emails not sending or stuck "pending"](#1-emails-not-sending-or-stuck-pending)
2. [Opens or clicks not recorded](#2-opens-or-clicks-not-recorded)
3. [Segment not updating or stuck on "Building"](#3-segment-not-updating-or-stuck-on-building)
4. [Campaign events not firing, stuck, or Contacts not entering or re-entering](#4-campaign-events-not-firing-stuck-or-contacts-not-entering-or-re-entering)
5. [Contact not tracked, anonymous duplicates, unexpected merges](#5-contact-not-tracked-anonymous-duplicates-unexpected-merges)
6. [Form submission does not create or update a Contact](#6-form-submission-does-not-create-or-update-a-contact)
7. [Webhooks not delivered or auto-disabled](#7-webhooks-not-delivered-or-auto-disabled)
8. [API errors: 401, 403, 422 (and 400, 409, 500)](#8-api-errors-401-403-422-and-400-409-500)
9. ["The site is currently offline due to encountering an error"](#9-the-site-is-currently-offline-due-to-encountering-an-error)
10. [Update or migration failure](#10-update-or-migration-failure)
11. [Cache and asset problems after a deploy](#11-cache-and-asset-problems-after-a-deploy)
12. [Plugin not appearing after install](#12-plugin-not-appearing-after-install)
13. [Scheduled Reports not sent (or sent twice)](#13-scheduled-reports-not-sent-or-sent-twice)
14. [Messenger queue backing up](#14-messenger-queue-backing-up)
15. [Cron prints "Script in progress"](#15-cron-prints-script-in-progress)
16. [Permission surprises](#16-permission-surprises)
17. [8.x: an event listener silently never fires](#17-8x-an-event-listener-silently-never-fires)
18. [Development-time failures](#18-development-time-failures)

---

## 0. Diagnostic toolkit (read first)

- Mautic log: `var/logs/mautic_<env>.php`, rotated daily, 7 files kept, `notice` level and above unless `debug` is on
  or the env is `dev`. [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:12-25 @7.x] The dated files
  are named `mautic_<env>-<date>.php`; other channels write `<env>.php`. [code: app/bundles/CoreBundle/Config/config.php:254-256 @7.x] [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:12-24 @7.x]
- Old paths: logs were in `app/logs` on 2.x and are in `var/logs` since 3.0. [kb: https://kb.mautic.org/article/troubleshooting-the-site-is-currently-offline-due-to-encountering-an-error-in-mautic.html]
- Then read the web-server (Apache or NGINX) error log. [kb: https://kb.mautic.org/article/troubleshooting-the-site-is-currently-offline-due-to-encountering-an-error-in-mautic.html]
- Mautic has no internal scheduler. Segments, Campaign membership, Campaign events, Segment Emails/SMS, background
  imports/exports and queued Webhooks only progress when their command runs. [kb: https://kb.mautic.org/article/getting-started-with-mautic.html] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]
- Capture cron output: add `--no-interaction --no-ansi` and `>>var/logs/cron.log 2>&1` to each line. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#tips-troubleshooting]
- On some hosts `php` drops console arguments (symptom `Invalid argument supplied for foreach()` in ArgvInput.php);
  use `php-cli` or `php -d register_argc_argv=On`. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#tips-troubleshooting]
- A locked command prints `Script in progress. Can force execution by using --bypass-locking.` and exits 0.
  Lock files are `var/run/sf.<key>.<sha256>.lock`. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:113-117 @7.x] [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:137-212 @7.x]
- Messenger transports `email` and `hit` default to `sync://` (no worker). Any other DSN queues messages until
  `messenger:consume <transport>` runs. [code: app/bundles/MessengerBundle/Config/config.php:7-8 @7.x]
- Logged-in Mautic Users are never tracked. Test public behaviour (hits, opens, form-driven Points, decisions) in a
  private window. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-60 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:410-412 @7.x]
- A real `MAUTIC_<KEY>` environment variable beats anything saved in the UI, and the UI shows the local.php value.
  Check the environment before trusting the Configuration screen. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:91-105 @7.x] [code: app/bundles/ConfigBundle/Controller/ConfigController.php:270-294 @7.x]

---

## 1. Emails not sending or stuck "pending"

Terms: a **Segment Email** (`email_type = list`) is a broadcast to Segments. A **template Email** is sent by Campaigns,
Forms, Points or the API. **DNC** (Do Not Contact) is a `lead_donotcontact` row; reason 1 unsubscribed, 2 bounced,
3 manual. [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-32 @7.x]

1. **The broadcast cron is not running.** A Segment Email is sent only by `mautic:broadcasts:send` or the UI/API
   "send". [code: app/bundles/EmailBundle/Entity/EmailRepository.php:892-914 @7.x]
   - Confirm: `php bin/console mautic:broadcasts:send --channel=email --id=<emailId>` by hand; watch the output.
   - Fix: add the cron line. No source gives a frequency. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-broadcasts-segment-emails-cron-job]
2. **The Email is not eligible.** The cron picks Emails that are published, have `publishUp <= now` (not null) and
   `publishDown` null or in the future. [code: app/bundles/EmailBundle/Entity/EmailRepository.php:892-914 @7.x]
   `sendEmailToLists` returns zeros silently for an unpublished Email or one in an unpublished Category. [code: app/bundles/EmailBundle/Model/EmailModel.php:1098-1107 @7.x]
   - Confirm: check Published, the publish-up date and the Category's published state.
3. **"Contact joined the Segment but never got it": Continue sending is off.** With it off (default), only Contacts
   whose Segment membership `date_added` is before `publishUp` are sent. [code: app/bundles/EmailBundle/Model/EmailModel.php:1021 @7.x] [code: app/bundles/EmailBundle/Entity/EmailRepository.php:285-288 @7.x]
   - Confirm: `SELECT date_added FROM lead_lists_leads WHERE lead_id=<id> AND leadlist_id=<segmentId>;` and compare
     with the Email's publish-up. [code: app/bundles/LeadBundle/Entity/ListLead.php:49-68 @7.x]
   - Fix: turn Continue sending on. The cron docs describe the opposite default; code wins. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-broadcasts-segment-emails-cron-job]
4. **The Contact is excluded by the pending rules.** A Contact is pending only if it is in an included Segment (not
   manually removed), has no email DNC of any reason, has no stat for the Email or its variants/translations, has no
   unsent `message_queue` row for it, is not in an excluded Segment, has not opted out of its Category, and has an
   email address. [code: app/bundles/EmailBundle/Entity/EmailRepository.php:183-345 @7.x]
   - Confirm: `SELECT * FROM lead_donotcontact WHERE lead_id=<id> AND channel='email';` and
     `SELECT * FROM email_stats WHERE lead_id=<id> AND email_id=<emailId>;` [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-90 @7.x]
   - Segment Emails never honour "Send to unsubscribed contacts" (`sendToDnc`). [code: app/bundles/EmailBundle/Entity/EmailRepository.php:197-206 @7.x]
   - One Email ID goes to one Contact once; duplicate the Email to resend. [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html]
5. **The pending count is stale.** It is cached as `email|<id>|pending` and is not invalidated when a Contact gets a
   DNC or stats are deleted. [code: app/bundles/EmailBundle/Model/EmailModel.php:2394-2431 @7.x]
   - Fix: `php bin/console mautic:cache:clear` clears the Mautic cache pool. [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:28-31 @7.x]
6. **The frequency rule postponed it.** Contacts over the limit go to `message_queue` and are sent later by
   `mautic:messages:send`. [code: app/bundles/EmailBundle/Model/EmailModel.php:1412-1425 @7.x] [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:68-119 @7.x]
   - Confirm: `SELECT * FROM message_queue WHERE lead_id=<id>;` [code: app/bundles/ChannelBundle/Entity/MessageQueueRepository.php:36-64 @7.x]
   - Fix: run `mautic:messages:send` on cron. [code: app/bundles/ChannelBundle/Entity/MessageQueueRepository.php:36-64 @7.x]
7. **"Sent" but never delivered: a queue DSN with no worker.** With a queue DSN, "sent" means "queued": stats exist
   and counters rise even if the worker later fails. [code: app/bundles/EmailBundle/Helper/MailHelper.php:402-414 @7.x]
   - Confirm: `messenger_dsn_email` is not `sync://` and no `messenger:consume email` runs. See §14.
8. **The transport rejects mail.** With `sync://` the SMTP/API call runs inside the request or cron command, so
   errors show there. [code: app/bundles/MessengerBundle/Config/config.php:7-13 @7.x]
   - Confirm: send the test email from Email Settings; it goes to the logged-in User with subject "Mautic test email".
     [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html]
   - Amazon SES: errors such as "Unable to Understand webhook payload" often mean the account is still in the SES
     Sandbox; only verified identities can send. [kb: https://kb.mautic.org/article/mautic-and-amazon-ses-troubleshooting.html]
   - A malformed address creates a BOUNCED DNC "Incorrectly formatted email address". [code: app/bundles/EmailBundle/Model/SendEmailToContact.php:270-285 @7.x]
9. **Dev or test instance.** DDEV sends to `smtp://localhost:1025`, a mail catcher that never delivers. [code: .ddev/mautic-setup.sh:6,32 @7.x]
   Tests use `mailer_dsn null://null`. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x]

Not a cause in 7.x: `mautic:emails:send` and the file spool. They were removed in 5.0. [code: UPGRADE-5.0.md:16,104-109 @7.x]
Detail: mautic-emails, mautic-cron-and-queues.

---

## 2. Opens or clicks not recorded

1. **Async `hit` transport with no worker.** With an async `hit` DSN, opens are recorded only when
   `messenger:consume hit` runs. [code: app/bundles/MessengerBundle/MessageHandler/EmailHitNotificationHandler.php:20-41 @7.x]
   - Confirm: check `messenger_dsn_hit` (Queue Settings or local.php); see §14.
2. **The send was a test.** "Send example" and "send to user" create no stat, no pixel and no trackable URLs.
   [code: app/bundles/EmailBundle/Model/EmailModel.php:1584-1717 @7.x]
   - Fix: test with a real Segment send to a test Segment. [kb: https://kb.mautic.org/article/how-to-test-emails-in-mautic.html]
3. **The open was filtered.** Opens are ignored when the IP is untrackable or the bot heuristic fires (at least 60%
   of: opened within 2 s of sending, blocked IP, bot user agent). [code: app/bundles/EmailBundle/Model/EmailModel.php:442-452 @7.x] [code: app/bundles/EmailBundle/Helper/BotRatioHelper.php:35-85 @7.x]
   Untrackable includes `DNT: 1`, `Sec-GPC: 1`, prefetch and IPs in `do_not_track_ips`. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:134-167,276-309 @7.x]
4. **No pixel.** The open pixel is appended only when `mailer_append_tracking_pixel` is on. [code: app/bundles/EmailBundle/Helper/MailHelper.php:806-816 @7.x]
5. **Links not rewritten.** Links are rewritten to `/r/<redirect>` unless `disable_trackable_urls` is on or the link
   has `data-mautic-disable-tracking="true"`. [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:228-317 @7.x] [code: app/bundles/PageBundle/Model/TrackableModel.php:740-747 @7.x]
   - The 7.2 user docs spell the attribute `mautic:disable:tracking`; code checks `mautic:disable-tracking`. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tracking-links-in-emails] [code: app/bundles/PageBundle/Model/TrackableModel.php:741 @7.x]
   - With SendGrid, turn off SendGrid's own click and open tracking. [kb: https://kb.mautic.org/article/how-to-use-the-sendgrid-api-in-mautic-5-with-symfony-mailer.html]
6. **The click was a bot or untrackable.** No hit is recorded when `ct` points to a stat flagged as a bot click or the
   request is untrackable. [code: app/bundles/PageBundle/Model/PageModel.php:410-416,427-433,460-463 @7.x]

Note: the first valid open sets `is_read` once; later opens only append `open_details`. [code: app/bundles/EmailBundle/Model/EmailModel.php:454-548 @7.x]
Detail: mautic-emails, mautic-pages-and-tracking.

---

## 3. Segment not updating or stuck on "Building"

"Building" shows while `needsRebuild()` is true: never built, or modified at or after `lastBuiltDate`. [code: app/bundles/LeadBundle/Entity/LeadList.php:329-342 @7.x]

1. **The rebuild cron is not running.** Only `mautic:segments:update` (alias `mautic:segments:rebuild`) rebuilds
   Segments; the UI has no "rebuild now". [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:38-168 @7.x]
   - Confirm: `php bin/console mautic:segments:update --list-id=<id>` and read the output.
     [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:110-112 @7.x]
2. **The run is locked.** A second run with the same lock key prints "Script in progress" and exits 0. See §15. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:114-116 @7.x]
3. **`--max-contacts` capped the run.** A capped run leaves `lastBuiltDate` NULL, so the Segment shows "Building"
   until a later run finishes. [code: app/bundles/LeadBundle/Model/ListModel.php:591-633 @7.x]
   - Confirm: `SELECT id, name, is_published, last_built_date FROM lead_lists WHERE id=<id>;` [code: app/bundles/LeadBundle/Entity/LeadList.php:139-196 @7.x]
4. **The rebuild is slow, not stuck.** The rebuild sleeps `batch_sleep_time` (default 1 s) before every batch of
   `--batch-limit` (default 300). [code: app/bundles/LeadBundle/Model/ListModel.php:923-939 @7.x] A 300 000-Contact
   Segment spends at least 1 000 s sleeping. [code: app/bundles/LeadBundle/Model/ListModel.php:443 @7.x]
   - Fix: raise `--batch-limit` or lower `batch_sleep_time`.
5. **A filter references a deleted field.** The rebuild silently returns 0 and changes nothing; the form also hides
   such filters. [code: app/bundles/LeadBundle/Model/ListModel.php:401-412 @7.x] [code: app/bundles/LeadBundle/Form/Type/FilterType.php:99-103 @7.x]
6. **The Segment is unpublished.** Unpublished Segments are never rebuilt. [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:242-244 @7.x]
7. **"Contact matches the filters but is not a member": it was manually removed.** The rebuild never re-adds a
   manually removed Contact; only a manual add restores it. This is intended. [code: app/bundles/LeadBundle/Segment/Query/ContactSegmentQueryBuilder.php:137-156 @7.x]
   - Confirm: `SELECT manually_added, manually_removed FROM lead_lists_leads WHERE leadlist_id=<id> AND lead_id=<cid>;` [code: app/bundles/LeadBundle/Entity/ListLead.php:49-68 @7.x]
8. **"Contact no longer matches but stays": it was manually added.** The rebuild never removes `manually_added = 1`
   rows. [code: app/bundles/LeadBundle/Segment/ContactSegmentService.php:281-282 @7.x]
9. **A Segment-membership filter sees stale rows.** It reads the referenced Segment's stored rows. Run the command
   without `--list-id`, or with the dependent id, so dependencies rebuild first. [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:110-112 @7.x]
10. **The count is wrong, not the membership.** Counts come from a cache (TTL 43200 s), and `removeLead` can drift
    it. [code: app/bundles/LeadBundle/Helper/SegmentCountCacheHelper.php:22-116 @7.x] [code: app/bundles/LeadBundle/Model/ListModel.php:868-883 @7.x]
    `lead:list:count-cache-update` recounts only published Segments. [code: app/bundles/LeadBundle/Command/SegmentCountCacheCommand.php:34-49 @7.x]

Detail: mautic-segments.

---

## 4. Campaign events not firing, stuck, or Contacts not entering or re-entering

1. **Cron is missing or out of order.** Three jobs are required: `mautic:segments:update`, `mautic:campaigns:rebuild`
   (alias `mautic:campaigns:update`) and `mautic:campaigns:trigger`. Since 5.0 the Segment rebuild no longer updates
   Campaign membership. [code: UPGRADE-5.0.md:55 @7.x] [code: app/bundles/CampaignBundle/Command/UpdateLeadCampaignsCommand.php:25 @7.x]
   A Contact added to a Segment reaches a Campaign only after the Campaign rebuild, and its first event runs on the
   next trigger. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs]
   - Confirm: run `mautic:campaigns:rebuild --campaign-id=<id>` then `mautic:campaigns:trigger --campaign-id=<id>` by hand.
2. **Something is unpublished.** Only published Segments feed membership. Unpublished, "pending" (future publish-up)
   and "expired" Campaigns are skipped. [code: app/bundles/CampaignBundle/Entity/LeadRepository.php:509-531 @7.x] [code: app/bundles/CoreBundle/Entity/FormEntity.php:233-251 @7.x]
   - Auto-unpublish: a Campaign with at least 100 members whose event `failed_count` reaches 35 % of members is
     unpublished and the owner is emailed. [code: app/bundles/CampaignBundle/EventListener/CampaignEventSubscriber.php:28-32,98-141 @7.x]
   - Form submissions while the Campaign is unpublished are not added, even after re-publishing. [kb: https://kb.mautic.org/article/how-do-i-stop-a-campaign-running.html]
3. **The Contact cannot (re-)enter.** With "Allow restart" off, a Contact who ever has an event log is never re-added
   by the rebuild. [code: app/bundles/CampaignBundle/Entity/LeadRepository.php:376-378 @7.x] A manually removed
   Contact is never re-added automatically, even with restart on. [code: app/bundles/CampaignBundle/Membership/Action/Adder.php:66-82 @7.x]
   - Confirm: `SELECT manually_removed, manually_added, date_last_exited, rotation FROM campaign_leads WHERE campaign_id=<id> AND lead_id=<cid>;` [code: app/bundles/CampaignBundle/Entity/Lead.php:52-78 @7.x]
4. **The Contact stays after leaving the source Segment.** The rebuild only removes `manually_added=0` members;
   Contacts added by hand, API, Form or campaign action stay. [code: app/bundles/CampaignBundle/Entity/LeadRepository.php:434-483 @7.x]
5. **A decision never fires.** The "yes" path runs in real time for the tracked, identified Contact, never from cron.
   [code: app/bundles/CampaignBundle/Executioner/EventExecutioner.php:258-263 @7.x] Anonymous Contacts never fire
   decisions. [code: app/bundles/CampaignBundle/Executioner/RealTimeExecutioner.php:168-176 @7.x]
   - Testing while logged in to Mautic does not trigger page-visit decisions; use a private window. [docs: https://docs.mautic.org/en/7.2/campaigns/troubleshooting_campaigns.html#page-visits-aren-t-recognized]
   - A decision fires once per rotation. [code: app/bundles/CampaignBundle/Entity/EventRepository.php:56-111 @7.x]
   - "Visits a page" URL patterns also match as substrings. [code: app/bundles/EmailBundle/Helper/UrlMatcher.php:10-64 @7.x]
   - With an async `hit` transport, decisions run only after `messenger:consume` runs. [code: app/bundles/PageBundle/Model/PageModel.php:465-507 @7.x]
6. **The "no" path never runs.** It runs in the trigger's inactive phase once the earliest "no" delay has elapsed.
   [code: app/bundles/CampaignBundle/Executioner/Helper/InactiveHelper.php:48-146 @7.x] A root decision next to a
   root action never sends Contacts down its "no" path. [code: app/bundles/CampaignBundle/Entity/LeadRepository.php:220-234 @7.x]
7. **Scheduled events look stuck.** Hour and weekday restrictions use the Contact's timezone and always schedule.
   [code: app/bundles/CampaignBundle/Executioner/Scheduler/Mode/Interval.php:138-177,322-360 @7.x] A due log whose
   recomputed date is still in the future is rescheduled. [code: app/bundles/CampaignBundle/Executioner/ScheduledExecutioner.php:279-338 @7.x]
   - Confirm: `SELECT event_id, rotation, is_scheduled, trigger_date FROM campaign_lead_event_log WHERE campaign_id=<id> AND lead_id=<cid>;` [code: app/bundles/CampaignBundle/Entity/LeadEventLog.php:125 @7.x]
8. **An action keeps failing.** A failed log is retried after the listener's interval, else
   `campaign_time_wait_on_event_false` (default `PT1H`). [code: app/bundles/CampaignBundle/Executioner/Dispatcher/ActionDispatcher.php:35-107 @7.x]
   An event type from a disabled or removed plugin cannot execute (`TypeNotFoundException`). [code: app/bundles/CampaignBundle/EventCollector/EventCollector.php:26-84 @7.x]
9. **Events added later did not run for existing Contacts.** `mautic:campaigns:resume-stuck` does not run them for
   Contacts who already passed that point. [code: app/bundles/CampaignBundle/Entity/CampaignRepository.php:742-743 @7.x]
10. **A condition was false at the moment it was reached.** Conditions are evaluated immediately; Contacts do not wait.
    [code: app/bundles/CampaignBundle/Executioner/Event/ConditionExecutioner.php:33-84 @7.x]
11. **The trigger is locked.** It prints "Script in progress" and exits 0. See §15. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:113-117 @7.x]

Detail: mautic-campaigns, mautic-cron-and-queues.

---

## 5. Contact not tracked, anonymous duplicates, unexpected merges

### Not tracked
1. **You are logged in to Mautic.** Logged-in Users, `Blocked-Tracking` cookies, bots and console contexts are never
   tracked. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-60 @7.x]
2. **The browser opted out.** `DNT: 1` or `Sec-GPC: 1` is never tracked. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:276-309 @7.x]
3. **Private-network IP.** Not tracked unless `track_private_ip_ranges` is true. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:56 @7.x]
4. **CORS blocks `/mtc/event`.** The script then falls back to the third-party-cookie pixel. Allow the embedding origin.
   [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:76-128 @7.x] CORS is restricted by default.
   [code: app/bundles/CoreBundle/Config/config.php:702 @7.x]
5. **Only the essential script loaded.** `/mautic-essential.js` alone makes no tracking request. [code: app/bundles/PageBundle/Resources/views/FormTheme/Config/_config_trackingconfig_widget.html.twig:32-85 @7.x]
6. **Async `hit` transport.** Hits stay bare rows until `messenger:consume hit` runs. [code: app/bundles/PageBundle/Model/PageModel.php:468-529 @7.x]

### Anonymous duplicates
- A new anonymous Contact is created for every untracked browser; `track_contact_by_ip` (default off) reuses the
  newest Contact with the same IP. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:191-293 @7.x]
- The JS-written `mautic_device_id` is a session cookie; only the server cookie lasts a year. [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:42-231 @7.x]
- The Contacts list hides anonymous Contacts unless the search contains `is:anonymous`. [code: app/bundles/LeadBundle/Controller/LeadController.php:192-206 @7.x]
- Clean up with `mautic:maintenance:cleanup`; it deletes with raw SQL and fires no delete events or webhooks.
  [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html] [code: app/bundles/LeadBundle/EventListener/MaintenanceSubscriber.php:26-83 @7.x]
- Unique identifiers are not DB constraints; duplicates stay until `mautic:contacts:deduplicate`. [code: app/bundles/LeadBundle/Command/DeduplicateCommand.php:30-115 @7.x]

### Unexpected merges
- A form submission whose unique identifier matches an existing Contact merges the tracked anonymous Contact into it.
  [code: app/bundles/FormBundle/Model/SubmissionModel.php:1027-1066 @7.x]
- A tracking hit with publicly-updatable unique-identifier fields in the query merges the anonymous Contact into the
  identified one. [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:45-200 @7.x]
- API PATCH with identifiers matching another Contact merges that Contact into the URL Contact. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:616-628 @7.x]
- The default duplicate operator is OR across unique identifiers (docs say AND). [code: app/bundles/LeadBundle/Config/config.php:360-361 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#managing-duplicates]
- Merged values come from the most recently modified Contact, not the winner. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:119-271 @7.x]
- The loser's id resolves to the winner forever, including through the API. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:46-78 @7.x]

Detail: mautic-pages-and-tracking, mautic-contacts.

---

## 6. Form submission does not create or update a Contact

1. **A field error stopped everything.** Any field error persists nothing: no Contact update, no submission, no
   actions. [code: app/bundles/FormBundle/Model/SubmissionModel.php:322-324 @7.x]
2. **The form is unpublished, outside its window or over its limit.** `/form/submit` checks exists, publish window,
   published state, then submission limit. [code: app/bundles/FormBundle/Controller/PublicController.php:54-245 @7.x]
   Manually copied HTML of an unpublished form still renders but submit refuses it. [code: app/bundles/FormBundle/Controller/PublicController.php:588-610 @7.x]
3. **No field is mapped to a Contact field.** Then no Contact is created or updated; from a logged-in admin browser
   `lead_id` is NULL. [code: app/bundles/FormBundle/Model/SubmissionModel.php:269-274 @7.x] [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:51-60 @7.x]
4. **You tested while logged in.** Logged-in Users are not tracked, so the submission attaches to nobody. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-60 @7.x]
5. **The email conflicts with the tracked Contact.** If it matches nobody, a new Contact is created and the tracked one
   is not overwritten. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1068-1089 @7.x]
6. **Empty values.** Empty mapped values never clear Contact fields. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1110 @7.x]
7. **Kiosk mode.** It ignores the tracked Contact and reuses an email match without merging. [code: app/bundles/FormBundle/Model/SubmissionModel.php:935-955 @7.x]
8. **An action threw `ValidationException`.** The saved submission is deleted; Emails already sent stay sent. [code: app/bundles/FormBundle/Model/SubmissionModel.php:363-374 @7.x]
9. **The Campaign did not pick it up.** A submission adds the Contact to every published Campaign that uses the form as
   a source. [code: app/bundles/FormBundle/Model/SubmissionModel.php:383-389 @7.x]

Not a cause: `saveResult=false` keeps the value out of results but still updates mapped fields. [code: app/bundles/FormBundle/Model/SubmissionModel.php:291-293 @7.x]
Detail: mautic-forms.

---

## 7. Webhooks not delivered or auto-disabled

1. **Queue mode without the cron, or the reverse.** Queued mode (`command_process`) without `mautic:webhooks:process`
   sends nothing; immediate mode makes that command a no-op. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:59-63 @7.x]
   - Confirm: `SELECT COUNT(*) FROM webhook_queue;` grows in queued mode. [code: app/bundles/WebhookBundle/Entity/WebhookQueue.php:33-117 @7.x]
2. **The Webhook was unpublished.** Only published Webhooks receive events; events raised while unpublished are never
   queued. [code: app/bundles/WebhookBundle/Entity/EventRepository.php:15-30 @7.x]
   - A `410 Gone` response unpublishes it at once. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:336-339 @7.x]
   - It is killed when none of its newest 100 logs is 2xx, unless `disable_auto_unpublish` or it was modified in the
     last 2 days. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:343-353,390-414 @7.x] [code: app/bundles/WebhookBundle/Entity/Webhook.php:507-516 @7.x]
   - Confirm: `SELECT status_code, note FROM webhook_logs WHERE webhook_id=<id> ORDER BY id DESC LIMIT 20;` A
     transport error is stored as `N/A`. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:358-361,445-463 @7.x] [code: app/bundles/WebhookBundle/Entity/Log.php:38-148 @7.x]
3. **The target is private.** Private, loopback and link-local targets are refused unless listed in
   `webhook_allowed_private_addresses`. [code: app/bundles/WebhookBundle/Http/Client.php:34-39 @7.x]
4. **Unhealthy back-off.** The cron skips an unhealthy Webhook for 300 s. [code: app/bundles/WebhookBundle/Command/ProcessWebhookQueuesCommand.php:71-110 @7.x]
5. **No event fires.** `lead_post_save_new` means "became identified"; anonymous Contacts and no-change saves send
   nothing. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:131-160 @7.x]
6. **The receiver rejects the signature.** It hashed re-serialised JSON or hex-encoded the digest; Mautic sends
   base64 of the raw HMAC bytes over the raw body. [code: app/bundles/WebhookBundle/Http/Client.php:25-26 @7.x]
7. **Duplicates.** No retry cap and no lock; make receivers idempotent. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:534-606 @7.x]
8. **"Send Test Payload" sends nothing** for event types without a sample file, including all plugin types. [code: app/bundles/WebhookBundle/Controller/AjaxController.php:116-130 @7.x]

Not the same feature: the Campaign "Send a webhook" action is unsigned, unqueued and treats only 200/201 as success.
[code: app/bundles/WebhookBundle/Helper/CampaignHelper.php:79-116 @7.x]
Detail: mautic-webhooks.

---

## 8. API errors: 401, 403, 422 (and 400, 409, 500)

Errors use `{"errors":[{"code","message","details","type"}]}`. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:611-640 @7.x]

| Status / type | Likely cause | Fix | Source |
|---|---|---|---|
| 403 `api_disabled` | `api_enabled` is false (default) | Enable the API in Configuration | [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:36-68 @7.x] |
| 403 `access_denied` with a `Basic` header | `api_enable_basic_auth` is off (default) | Enable Basic Auth or use OAuth2 | [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:70-89 @7.x] |
| 403 on a resource | The User's Role lacks the permission; without `<base>:viewother` lists show only own rows | Grant the permission; test as a non-admin | [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:177-182 @7.x] |
| 403 when authorizing a client | The browser flow needs `api:access:full` | Grant it to the authorizing User | [code: app/bundles/ApiBundle/EventListener/PreAuthorizationEventListener.php:38-66 @7.x] |
| 401 `invalid_grant` | Invalid or expired access token (lifetime 60 min) | Refresh the token | [code: app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php:58-101 @7.x] [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:13-17 @7.x] |
| 401 on Basic Auth with a correct password | The password scores below zxcvbn 3 | Reset the User's password | [code: app/bundles/UserBundle/EventListener/PasswordSubscriber.php:28-47 @7.x] |
| 400 `invalid_client` | Wrong client id/secret, or grant not allowed (`client_credentials` only when an admin created the client; `password` never) | Recreate the client as an admin | [code: app/bundles/ApiBundle/Controller/ClientController.php:207-211 @7.x] |
| 400 | Validation failure, or batch over `api_batch_max_limit` (200) | Read `details` | [code: app/bundles/ApiBundle/Controller/CommonApiController.php:605-617 @7.x] [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:728-736 @7.x] |
| 422 | Validation with a 422 cause, for example unpublishing a Segment that a Campaign or Segment uses | Remove the dependency first | [code: app/bundles/ApiBundle/Controller/CommonApiController.php:605-617 @7.x] [code: app/bundles/LeadBundle/EventListener/SegmentSubscriber.php:73-115 @7.x] |
| 409 | Entity checked out; only Emails implement this in 7.2.1. Deleting a field used in a Segment filter is also 409 | Release the lock / remove the filter | [code: app/bundles/ApiBundle/Controller/CommonApiController.php:491-520 @7.x] [code: app/bundles/LeadBundle/Field/EventListener/LeadFieldSubscriber.php:33-52 @7.x] |
| 500 | A `where` clause missing `col` or `expr` | Fix the clause | [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1610-1706 @7.x] |

Silent traps (no error at all):
- `publishedOnly` and `searchFilter` are ignored over HTTP; use `published` and `search`. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:167 @7.x]
- A batch with failed items still returns 201 or 200; check `statusCodes`. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:274-331 @7.x]
- Publish fields are dropped when the caller lacks publish permission. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:523-540 @7.x]
- v2 validation errors are 400, never 422. [code: app/config/config.php:433-477 @7.x]
- A UI AJAX call with a bad CSRF token gets HTTP 200 with a `flashes` error, not 403. [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:34-63 @7.x]

Detail: mautic-rest-api, mautic-users-and-permissions.

---

## 9. "The site is currently offline due to encountering an error"

What it is: an uncaught exception outside AJAX in prod renders this page with HTTP 500 (or `custom_offline.html.twig`);
AJAX/JSON requests get `{"errors":[...]}`. [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:156-181 @7.x] [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:424-514 @7.x]
Causes named by the KB: server config, permissions, PHP version mismatch, resources, corrupted files or a failed update,
or database issues. Check the Mautic log first, then the web-server log. [kb: https://kb.mautic.org/article/troubleshooting-the-site-is-currently-offline-due-to-encountering-an-error-in-mautic.html]

1. **Read the exception.** `var/logs/mautic_prod-<date>.php` holds it. [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:12-25 @7.x]
2. **File ownership.** Doctrine proxy `failed to open stream` errors in `var/cache/prod/doctrine/orm/Proxies` usually
   mean files owned by a user other than the web-server user. [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html]
   - Fix: reset permissions (files 644, dirs 755, group-writable `var/cache`, `var/logs`, config, `media/files`,
     `media/images`, `translations`), `rm -rf var/cache/*`, then `chown -R` to the web-server user.
     [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html]
3. **PHP version.** Web requests on PHP outside 8.2.0–8.5.99 get an HTTP 500 before the kernel boots. [code: app/middlewares/VersionCheckMiddleware.php:46-59 @7.x]
4. **Resources.** `Allowed memory size … exhausted` → raise `memory_limit`; `Class 'ZipArchive' not found` → install
   the zip extension. [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#there-is-a-php-error-when-running-a-command]
   Find php.ini via System Info > PHP Info or `php -i | grep .ini`. [docs: https://docs.mautic.org/en/7.2/troubleshooting/working_with_resource_limits.html]
5. **Document root.** On Composer installs the DocumentRoot must be `docroot`, else 404 or "autoload.php" errors.
   [kb: https://kb.mautic.org/article/troubleshooting-the-site-is-currently-offline-due-to-encountering-an-error-in-mautic.html]
6. **Stale or half-built cache after an update.** See §10 and §11.
7. **Every request hangs instead.** A crashed asset generation leaves `media/generation_in_progress.txt`; every request
   spin-waits on it. Delete the file. [code: app/bundles/CoreBundle/Helper/AssetGenerationHelper.php:121-123 @7.x]
8. **Locked out, not offline.** Wrong `trusted_hosts` lock you out; fix them in local.php. [code: app/middlewares/TrustMiddleware.php:38-40 @7.x]

Detail: mautic-configuration, mautic-architecture, mautic-dev-environment.

---

## 10. Update or migration failure

1. **Under-resourced hosting** is the usual cause. [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html]
2. **Check the schema.** The schema check tool is at `/s/update/schema`. [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#checking-for-schema-updates]
   - `php bin/console doctrine:migrations:status` shows Executed, Available, New and "Executed Unavailable"; applied
     migrations are recorded in the `migrations` table. [kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html]
3. **Recovery order (docs):** clear the cache (`cache:clear` or `rm -rf var/cache`), `mautic:update:find`/`apply`,
   `doctrine:migrations:status` then `migrate`, then manual file replacement keeping `config/local.php`, `media/files`,
   `plugins`, `themes` and `translations`. [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-is-available]
   Without SSH, a PHP troubleshooting script can do most steps. [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-isn-t-available]
4. **KB last resort:** `doctrine:schema:update --force` (preview with `--dump-sql`); `--complete` drops custom DB
   objects and the `migrations` table. Most Mautic migrations have no `down()`. [kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html]
5. **Wrong updater for the install type.** `mautic:update:apply` refuses when `composer_updates` is true and ends phase 1
   with a hard `exit()`. [code: app/bundles/CoreBundle/Command/ApplyUpdatesCommand.php:74-144 @7.x] Composer installs
   bump `mautic/*`, `composer update --with-dependencies`, then `cache:clear`, `mautic:update:apply --finish`,
   `doctrine:migration:migrate --no-interaction`, `cache:clear`. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-mautic-composer-based-installs]
6. **Ran as root.** Run update commands as the web-server user. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#running-update-commands-as-the-web-server-user]
7. **A migration re-ran or skipped unexpectedly.** `preUp()` skips only when every assertion is true. [code: app/bundles/CoreBundle/Doctrine/PreUpAssertionMigration.php:26-45 @7.x]
   Green functional tests do not prove a migration works. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:159 @7.x]
8. **Plugin schema did not update.** Plugin migrations run only when the plugin `version` was bumped. See §12. [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:67-95 @7.x]

Detail: mautic-upgrades-and-versions, mautic-contributing.

---

## 11. Cache and asset problems after a deploy

1. **Wrong cache command.** `mautic:cache:clear` empties only the Mautic data cache pool; Symfony `cache:clear`
   rebuilds `var/cache` and also clears that pool. [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:28-31 @7.x] [code: app/bundles/CacheBundle/EventListener/CacheClearSubscriber.php:26-42 @7.x]
2. **Compile-time settings.** `cookie_secure` from the `site_url` scheme, `db_host_ro`, `cache_path`/`log_path` and
   https route forcing need `bin/console cache:clear` after a manual edit. [code: app/config/config.php:35-44 @7.x] [code: app/AppKernel.php:316-334 @7.x]
3. **`cache:clear` itself fails** with class-not-found errors: delete `var/cache/<env>`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/cache.html]
4. **CSS/JS missing.** `composer generate-assets` fails when `node_modules/` or the CKEditor bundle is missing.
   [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:51-120 @7.x] Generated assets are
   gitignored, so a git-only deploy lacks them. [code: .gitignore:66-105 @7.x]
5. **Email/Page builder does not load.** A failed GrapesJS build only warns during `composer install`; fix with
   `composer gjs-build`. [code: build/gjs_build.php:5-13 @7.x] Without `dist/manifest.json` the builder is not
   injected (warning in the log). [code: plugins/GrapesJsBuilderBundle/EventSubscriber/AssetsSubscriber.php:36-91 @7.x]
6. **Requests hang.** Delete a stale `media/generation_in_progress.txt`. [code: app/bundles/CoreBundle/Helper/AssetGenerationHelper.php:121-123 @7.x]
7. **Proxy or permission errors.** Files written by a different user; see §9.2. [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html]
8. **Dashboards, Forms or Focus break with Redis.** `cache_adapter_tag_aware` must name a tag-aware adapter. [code: app/bundles/CacheBundle/Cache/CacheProviderTagAware.php:11-17 @7.x]
9. **Theme CSS change not visible on iframe forms.** Clear the cache after editing theme files. [kb: https://kb.mautic.org/article/guide-make-a-mautic-form-show-in-two-columns-works-for-landing-pages-and-embeds.html]
10. **Workers run old config.** A running Messenger worker keeps the DSNs it booted with; restart it. [code: app/config/config.php:106,112,117 @7.x]

Detail: mautic-dev-environment, mautic-cron-and-queues, mautic-theme-development.

---

## 12. Plugin not appearing after install

1. **Directory and namespace do not match.** The kernel loads `plugins/<Dir>/<File>Bundle.php` only if class
   `\MauticPlugin\<Dir>\<File>Bundle` exists. [code: app/AppKernel.php:158-187 @7.x]
2. **`MINIMUM_MAUTIC_VERSION` too high.** The bundle is silently not registered. [code: app/AppKernel.php:176-181 @7.x]
3. **Cache not cleared.** Config, translation and service changes need a cache clear. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/cache.html]
4. **Not reloaded.** Run `mautic:plugins:reload` (or Install/Upgrade Plugins). [code: app/bundles/PluginBundle/Facade/ReloadFacade.php:24-49 @7.x]
   - Confirm: `SELECT bundle, version, is_missing FROM plugins;` [code: app/bundles/PluginBundle/Entity/Plugin.php:72-103 @7.x]
5. **Services missing.** A `Config/services.php` without `DependencyInjection/<Name>Extension.php` registers nothing.
   [code: app/config/services.php:21-23 @7.x]
6. **Updated code, old behaviour.** Without a `version` bump, reload neither runs migrations nor stores new metadata.
   [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:67-95 @7.x]
7. **Integration missing from the grid.** A legacy Integration needs service id `mautic.integration.<lowercased name>`.
   [code: app/bundles/PluginBundle/Helper/IntegrationHelper.php:94-121 @7.x] A modern one needs its settings row,
   and `mautic.sync_integration`/`mautic.authentication_integration` must be tagged by hand. [code: app/bundles/IntegrationsBundle/Helper/IntegrationsHelper.php:87-98 @7.x] [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:26-33 @7.x]
8. **Marketplace install refused.** It needs `composer_updates` true (403 otherwise); pages 404 when `marketplace_enabled`
   is false. [code: app/bundles/MarketplaceBundle/Controller/AjaxController.php:52-225 @7.x]
9. **Long-running workers miss it.** Form components and channels are cached statically per process. [code: app/bundles/FormBundle/Model/FormModel.php:635-659 @7.x] [code: app/bundles/ChannelBundle/Model/MessageModel.php:30,108 @7.x]

Detail: mautic-plugin-development, mautic-integrations.

---

## 13. Scheduled Reports not sent (or sent twice)

1. **No cron.** Nothing is emailed until `mautic:reports:scheduler` runs. [code: app/bundles/ReportBundle/Scheduler/Command/ExportSchedulerCommand.php:38-78 @7.x]
   Schedules fall due at 00:00, so run it at least daily. [code: app/bundles/ReportBundle/Scheduler/Builder/SchedulerBuilder.php:46-51 @7.x]
   - Confirm: `SELECT report_id, schedule_date FROM reports_schedulers;` [code: app/bundles/ReportBundle/Entity/Scheduler.php:18-41 @7.x]
2. **The Report is unpublished.** It is skipped but re-planned. [code: app/bundles/ReportBundle/Model/ReportExporter.php:49-52,67-68,90 @7.x]
3. **Invalid schedule.** A scheduled Report needs `toAddress`; WEEKLY needs a day, MONTHLY a day and frequency. [code: app/bundles/ReportBundle/Scheduler/Validator/ScheduleIsValidValidator.php:25-87 @7.x]
4. **The email does not arrive.** Check the mail path as in §1 before suspecting the scheduler.
5. **File too large.** Over 5 MB it is zipped; if still too large, the email carries a link to `csv_reports/report_<id>.zip`,
   deleted after 7 days. [code: app/bundles/ReportBundle/Scheduler/Model/FileHandler.php:30-107 @7.x]
6. **Sent twice.** The command has no lock and appends to the CSV, so overlapping runs duplicate rows and emails.
   [code: app/bundles/ReportBundle/Model/ExportHandler.php:33 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#preventing-duplicate-report-emails]

Detail: mautic-reports-and-dashboard.

---

## 14. Messenger queue backing up

1. **No worker, or a worker that exits at once.** A cron-run `messenger:consume` needs `--limit`, `--time-limit` or
   `--memory-limit`; otherwise run it under Supervisor or systemd. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#process-email-queue-cron-job]
   KB example: every 10 min, `--limit=60 --time-limit=480 --memory-limit=128M`. [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html]
   - Confirm (Doctrine transport): `SELECT COUNT(*) FROM messenger_messages;` The table name comes from Symfony and
     could not be verified in the analysed tree [unverified].
2. **The `hit` transport is queued too.** It carries email opens and page hits. [code: app/config/config.php:111-125 @7.x]
   Run `messenger:consume hit` as well. [code: app/bundles/MessengerBundle/README.md:80-86 @7.x]
3. **Invalid DSN.** Any DSN other than `sync://` needs a host (`doctrine://default`, not `doctrine://`); hand-edited
   DSNs must be URL-encoded. [code: app/bundles/CoreBundle/Helper/Dsn/Dsn.php:44-58 @7.x]
4. **Old KB config.** A `messenger` → `transports` array in local.php does not match 7.x; set `messenger_dsn_email`
   etc. or use Queue Settings. [code: app/bundles/MessengerBundle/Config/config.php:6-14 @7.x]
5. **Worker runs stale settings.** Restart it after changing Queue Settings. [code: app/config/config.php:106,112,117 @7.x]
6. **Failures vanish.** After 3 retries a message goes to `failed`; an empty failure DSN is `null://`, so it is
   discarded and `messenger:failed:*` shows nothing. [code: app/bundles/MessengerBundle/Retry/RetryStrategy.php:31-43 @7.x] [code: app/bundles/MessengerBundle/DependencyInjection/EnvProcessor/MessengerNullableEnvVarProcessor.php:11-21 @7.x]
   Retrying opens or hits double-counts. [code: app/bundles/EmailBundle/Model/EmailModel.php:463-544 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:622-711 @7.x]
7. **Table growth.** `messenger_messages` can fill quickly; monitor disk or move to Redis/RabbitMQ. [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html]
8. **The Queue Settings "Send test message" button fails.** Expected in 7.x: no handler exists. [code: UPGRADE-7.0.md:15 @7.x]

Detail: mautic-cron-and-queues.

---

## 15. Cron prints "Script in progress"

1. **Another run holds the lock** (normal for overlapping cron). The locked run exits 0. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:113-117 @7.x]
2. **A stuck run holds it.** In `pid` mode (default) the lock is honoured while the stored pid is alive; `--timeout`
   does nothing in `pid` mode. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:137-212 @7.x] [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:64,85-88,209 @7.x]
   - Confirm: `ls -l var/run/*.lock`, read the pid, `ps -p <pid>`. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:113-117,171-179 @7.x]
   - Fix: stop the stuck process; for a one-off run use `--bypass-locking` (`--force` is the deprecated alias).
     [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:79-99 @7.x]
3. **Without `posix_getpgid`/`getmypid`** the mode silently becomes `flock`. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:137-212 @7.x]
4. **Lock key surprises.** The key is the command name plus a moderation key (Segment id, Campaign id + thread, ...);
   different keys run in parallel. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:102 @7.x]
5. **Commands that never lock** (import, webhooks:process, reports:scheduler, email:fetch, integration sync) can
   overlap with themselves. [code: app/bundles/ReportBundle/Scheduler/Command/ExportSchedulerCommand.php:38-78 @7.x]
6. **Exit code 1 that is not a failure:** `mautic:email:sendwinner` exits 1 while the A/B winner is undecided. [code: app/bundles/EmailBundle/Command/SendWinnerEmailCommand.php:21-77 @7.x]

Detail: mautic-cron-and-queues.

---

## 16. Permission surprises

- `isGranted()` caches per permission string for the request and ignores a different User argument. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:210-213,249 @7.x]
- `lead:leads:view` on an extended permission tests `viewown`; ask for `viewother` explicitly. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:144-181 @7.x]
- Admins are granted non-existent levels, so a typo passes for admins and throws for others; test as a non-admin. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:220-235 @7.x]
- `rawPermissions` in API responses omit implied levels. [code: app/bundles/UserBundle/Model/RoleModel.php:92 @7.x]
- "Own" differs by path: entity access uses owner or creator, the UI `is:mine` list owner only. [code: app/bundles/LeadBundle/Entity/Lead.php:662-665 @7.x] [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:137-164 @7.x]
- Anyone with `user:users:edit` can edit any User, including admins. [code: app/bundles/UserBundle/Security/Permissions/UserPermissions.php:26-27 @7.x]
- Configuration and System Info are admin-only. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:41 @7.x]
- Report "Visible for all logged-in users" does nothing; only `viewother` or ownership matter. [code: app/bundles/ReportBundle/Controller/ReportController.php:68-70 @7.x]
- Report data ignores entity-level permissions. [code: app/bundles/LeadBundle/EventListener/ReportSubscriber.php:171 @7.x]
- A dashboard widget type appears only when the User holds all the bundle's listed permissions. [code: app/bundles/DashboardBundle/Event/WidgetTypeListEvent.php:60-68 @7.x]
- A client-credentials token acts with the creating admin's Role. [code: app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php:43-95 @7.x]
- The docs' "Same Role" level does not exist in code. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:455-477 @7.x]
- Plugin permission strings are `<name>:<level>:<perm>`, not `plugin:...`. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x]

Detail: mautic-users-and-permissions.

---

## 17. 8.x: an event listener silently never fires

- On 8.x almost every core event dispatches by event class. A subscriber keyed on a removed constant fatals; one keyed
  on a kept constant or raw string silently receives nothing. [code: 8x-changes §3.1-3.2 @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch]
- Examples of kept constants that load fine and never fire: `FormEvents::FORM_ON_BUILD`, `PointEvents::POINT_ON_BUILD`,
  `ReportEvents::REPORT_ON_BUILD`, `LeadEvents::TIMELINE_ON_GENERATE`. [code: 8x-changes §3.2 @8.x]
- Fix: subscribe with the event class name. Names a plugin defines itself (campaign `batchEventName`, decision
  `eventName`, form action `eventName`) stay string-dispatched. [code: 8x-changes §3.1 @8.x]
- Also on 8.x: the `services` array in `config.php` is no longer read, and `--lock_mode=file_lock` is an error.
  [code: 8x-changes §4 Core "services group ... no longer read" @8.x] [code: UPGRADE-8.0.md:267 @8.x]
- On 7.x, a listener that never fires usually listens to an event core never dispatches, for example
  `EMAIL_FAILED`/`EMAIL_RESEND`, `WEBHOOK_PRE_EXECUTE`, `ApiEvents::CLIENT_PRE_SAVE`, `PluginEvents::ON_FORM_SUBMIT_ACTION_TRIGGERED`.
  [code: app/bundles/EmailBundle/EventListener/EmailSubscriber.php:126-174 @7.x] [code: app/bundles/WebhookBundle/WebhookEvents.php:73-82 @7.x] [code: app/bundles/ApiBundle/Model/ClientModel.php:101-129 @7.x] [code: app/bundles/PluginBundle/PluginEvents.php:119 @7.x]
- A custom model that does not override `dispatchEvent()` fires no events, audit log or webhooks. [code: app/bundles/CoreBundle/Model/FormModel.php:382-405 @7.x]

Detail: mautic-plugin-development, mautic-architecture, mautic-upgrades-and-versions.

---

## 18. Development-time failures

Upstream ships `.agents/skills/mautic-dev/SKILL.md` in the 7.x repo, with development pitfalls and verification steps.
Use it alongside this guide for failures during development. [code: .agents/skills/mautic-dev/SKILL.md @7.x]

- `bin/phpunit` without `-c app/phpunit.xml.dist` fails on the missing `KERNEL_CLASS`. [code: app/phpunit.xml.dist:65-76 @7.x]
- `bin/phpstan` fails until the test container is warmed; use `composer phpstan`. [code: composer.json:166-214 @7.x]
- "Base table or view not found" or "Unknown column" in tests: delete `var/cache`. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-261, 375-383 @7.x]
- Re-running the DDEV managed setup reinstalls Mautic; data survives only as `bak_*` tables. [code: .ddev/mautic-setup.sh:11-18 @7.x]
- `mautic:install` exits 0 when the requirements step fails; check the output. [code: app/bundles/InstallBundle/Command/InstallCommand.php:243 @7.x]

Detail: mautic-testing, mautic-dev-environment.
