# Version notes — cron, queues, cache

## History (why things are the way they are)

- Mautic 2.x used `app/console`; since 3.0 the path is `bin/console`
  [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html].
- Up to 4.x, Email "queue" meant a Swiftmailer filesystem spool (`var/spool`) drained by `mautic:emails:send`; spooled
  Email counted as sent [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html].
- Up to 4.x, QueueBundle could queue page hits and email opens via RabbitMQ or Beanstalkd, processed by
  `mautic:queue:process -i page_hit|email_hit` [docs: https://docs.mautic.org/en/7.2/queue/queue.html].
- The legacy queue arrived in ~2.11. It stored the Request as a flat array, deliberately avoiding PHP object
  serialisation for security [PR #3873]. From ~3.0 its settings lived in `local.php` [PR #8320]. `--timeout` (~3.3) and
  `rabbitmq_idle_timeout` (~4.0) were its last additions [PR #9394] [PR #9391]. All of it is historical.
- CacheBundle (tag-aware cache, filesystem/Memcached/Redis, `mautic:cache:clear`) arrived in ~3.3 [PR #9107]. Its
  filesystem adapter moved to `mautic.tmp_path` in ~4.4.7 [PR #9929].
- Console commands honour php.ini `date.timezone` since ~2.16.1 [PR #7617]. Unknown Campaign ids give a non-zero exit since
  ~4.4.8 [PR #11963].

## 5.x

- 5.0 replaced Swiftmailer with Symfony Mailer + Messenger. `mautic:emails:send` was removed; start a consumer with
  `bin/console messenger:consume email` [code: UPGRADE-5.0.md:16 @7.x].
- 5.0 removed QueueBundle "in favor symfony's messenger"; its events, `QueueService`, `QueueRequestHelper` have no
  replacement; `mautic:queue:process` → `messenger:consume` [code: UPGRADE-5.0.md:104-109 @7.x].
- 5.0: `mautic:segments:update` no longer updates Campaign membership; also run `mautic:campaigns:update`
  [code: UPGRADE-5.0.md:55 @7.x].
- The Swiftmailer `ProcessEmailQueueCommand` file was deleted in commit `736b07fbba1` (2023-06-02); QueueBundle files in
  `b77e0553b03` (2023-06-27) [code: app/bundles/EmailBundle/Command/ (ProcessFetchEmailCommand.php, SendWinnerEmailCommand.php only) @7.x].
- Messenger stopped using JSON serialisation (commit `0628b6280b4`, 2023-08-22); messages use PHP native serialisation
  [code: app/bundles/MessengerBundle/Message/Traits/MessageRequestTrait.php:32-65 @7.x].
- 5.1: Campaigns are triggered newest to oldest; `mautic:webhooks:process` gained `--webhook-id` range mode with
  `--min-id`/`--max-id` [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs]
  [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#webhooks-cron-job].
- PR view of 5.0 Messenger: MessengerBundle and its config section [PR #11598]; `sync://` defaults, any-transport DSNs,
  an optional failure transport, test buttons and parameter-driven retry settings [PR #12509]; hits through Messenger and
  QueueBundle removal [PR #12648]. JSON serialisation was dropped for failed-transport compatibility, reversing the 2.11
  flat-array rule [PR #12648] [PR #3873].
- 5.0: `ModeratedCommand` gained the Redis lock store (`-x redis`) [PR #10347]. Trigger threads got their own lock keys
  [PR #11747]. The tmp_path cache fix was forward-ported [PR #11885].
- 5.1.0: `--exclude` on `mautic:segments:update`, `mautic:campaigns:rebuild` and `mautic:campaigns:trigger` [PR #13383];
  `mautic:campaign:delete-event-logs` for background event-log deletion [PR #10219].

## 6.x

- No Messenger, queue or cache changes were found in the 26 PRs of this area for 6.x. The only command change is the new
  `mautic:segments:stat` (6.0.0) [PR #14575]. Treat 6.x behaviour as the 7.0 baseline minus the 7.0 items below.

## 7.0

- The deprecated Messenger `TestHandler` was deleted, so `TestEmail`/`TestHit`/`TestFailed` have no handler and the
  Queue Settings "Send test message" button cannot report a processed message [code: UPGRADE-7.0.md:15 @7.x].
- `symfony/amqp-messenger` was removed from core dependencies; `amqp://` DSNs are rejected as "Unsupported scheme" until
  it is installed with Composer [code: UPGRADE-7.0.md:53 @7.x].
- 7.0.0: Redis caching splits into a non-tag-aware provider (`cache_adapter`) and a tag-aware one
  (`cache_adapter_tag_aware`), which removed about 50% of Redis queries [PR #14724].
- 7.0: Segment counts moved from the database to the cache provider [PR #15554]; `lead:list:count-cache-update` recounts
  them when `update_segment_contact_count_in_background` is on [PR #14911].

## 7.1 / 7.2

- `RemoveReportAttachmentHandler` (commit `d7722bf09ad`, 2025-06-11) deletes scheduled-Report attachments after the
  Email is sent; the release containing it is not stated in the inputs
  [code: app/bundles/MessengerBundle/MessageHandler/RemoveReportAttachmentHandler.php:13-48 @7.x].
- 7.1.3: the Queue Settings form validates the retry multiplier (≥ 1) and rejects negative values, fixing the worker
  crash reported in issue mautic/mautic#16017 [PR #16157] [code: app/bundles/MessengerBundle/Form/Type/ConfigType.php:96-99 @7.x].
- 7.1.0: `mautic:segment:delete` hard-deletes Segments when `delete_segment_in_background` is on [PR #15755].
- 7.2.0: CacheBundle services are autowired [PR #16800]; Messenger message and handler classes are `final` [PR #16897].
  `mautic:motd` always exits 0 (~7.2) [PR #16226].
- `mautic:campaigns:resume-stuck` with the `campaigns_resume_stuck_records_after` cut-off (default
  `2025-10-01 00:00:00`) exists since 7.2.1 [code: app/bundles/CampaignBundle/Config/config.php:174 @7.x].
- 7.2.2: `mautic:assets:generate` deletes a stale `media/css/libraries.css` before regenerating it [PR #17597]
  [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:80-84 @7.x].

## Unreleased on 7.x (7.3.0-rc)

- The email tracking pixel dispatches no `EmailHitNotification` when the Contact has turned activity tracking off
  [PR #18006] [code: app/bundles/EmailBundle/Controller/PublicController.php:138-157 @7.x].
- `/mtc/event` returns null ids and no events for untrackable visitors [PR #18013], and `success:0` instead of a 500
  when no Contact is available [PR #18028] [code: app/bundles/PageBundle/Controller/PublicController.php:400-458 @7.x].
- Installing a Plugin with entities no longer fails when `messenger_messages` already exists [PR #17977]
  [code: app/bundles/PluginBundle/Bundle/PluginDatabase.php:42-53 @7.x].
- The full list of unreleased 7.x PRs is in [unreleased-7.x-prs.md](../../mautic-upgrades-and-versions/references/unreleased-7.x-prs.md) [code: git log --first-parent 7.2.2..838c9c772ec @7.x].

## 8.x delta: 8.x (snapshot pinned in SOURCES.md)

- Symfony `~7.4` → `~8.1`, PHP minimum 8.2 → 8.4; Messenger and Lock follow Symfony 8.1 [code: app/composer.json @8.x].
- `ModeratedCommand::MODE_LOCK` removed: `--lock_mode=file_lock` now fails with `Unknown locking method specified.`;
  use `flock` [code: UPGRADE-8.0.md:358 @8.x].
- `CacheStorageHelper`, `mautic.helper.cache_storage` and `Entity\Cache` removed; the `cache_items` table is no longer
  mapped or written; use CacheBundle (#17033, #17155) [code: UPGRADE-8.0.md:229,295 @8.x] [PR #17033] [PR #17155].
- Legacy filesystem dashboard-widget cache removed; widgets use the tag-aware CacheBundle pool only [PR #17033] [PR #17034].
- A cache miss returns `null`, not `false`; integration and widget data live in `cache_adapter` and are dropped by a
  cache clear [PR #17033] [PR #17155].
- Service ids `mautic.cache.adapter.*` removed: a custom `cache_adapter` parameter must be a class name
  [code: UPGRADE-8.0.md:267 @8.x].
- `ResultCacheHelper::getCache()` returns a PSR-6 pool; `doctrine/cache` and `doctrine/common` removed [PR #17361].
- `AbstractIntegration` takes `CacheProviderInterface` as its second constructor argument and `getCache()` returns a
  PSR-16 cache [code: UPGRADE-8.0.md:316 @8.x].
- `MauticSocialBundle` is removed, and with it `mautic:social:monitoring`, `social:monitor:twitter:hashtags` and
  `social:monitor:twitter:mentions`. Before upgrading, remove those cron entries; afterwards clear the cache and run
  `mautic:plugins:reload`. No other console command is added or removed between the 7.x and 8.x snapshots. The 8.0
  user docs do not yet mention `file_lock` and still describe the social monitoring cron job
  [code: UPGRADE-8.0.md:9-21 @8.x] [PR #17473] [docs: https://docs.mautic.org/en/8.0/configuration/cron_jobs.html].
- Most core subscribers, including the ones that feed cron-run listeners, are `#[AsEventListener]` methods on 8.x;
  a plugin that extends an abstract core subscriber must be an autoconfigured service or its listeners stop firing
  [code: UPGRADE-8.0.md:635-638 @8.x] [PR #17988].
- The 7.2.2 `mautic:assets:generate` deletion of a stale `libraries.css` is on 8.x, because 7.2.2 is merged into 8.x
  [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:82-84 @8.x] [PR #17597] [PR #18036]. The
  unreleased 7.x fix that skips existing tables such as `messenger_messages` on plugin install is on 8.x too, from the
  2026-11-17 merge [code: app/bundles/PluginBundle/Bundle/PluginDatabase.php:55 @8.x] [PR #17977] [PR #18236].
- Code that must run on both: avoid `--lock_mode=file_lock` and `CacheStorageHelper`; inject `CacheProviderInterface`
  and treat both `null` and `false` as a miss [code: UPGRADE-8.0.md:295-316 @8.x].
