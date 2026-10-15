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
  `2025-10-01 00:00:00`) exists in 7.2.1 [code: app/bundles/CampaignBundle/Config/config.php:174 @7.x].

## 8.x delta (from 7.x)

- Symfony `~7.4` → `~8.1`, PHP minimum 8.2 → 8.4; Messenger and Lock follow Symfony 8.1 [code: app/composer.json @8.x].
- `ModeratedCommand::MODE_LOCK` removed: `--lock_mode=file_lock` now fails with `Unknown locking method specified.`;
  use `flock` [code: UPGRADE-8.0.md:267 @8.x].
- `CacheStorageHelper`, `mautic.helper.cache_storage` and `Entity\Cache` removed; the `cache_items` table is no longer
  mapped or written; use CacheBundle (#17033, #17155) [code: UPGRADE-8.0.md @8.x] [PR #17033] [PR #17155].
- Legacy filesystem dashboard-widget cache removed; widgets use the tag-aware CacheBundle pool only [PR #17033] [PR #17034].
- A cache miss returns `null`, not `false`; integration and widget data live in `cache_adapter` and are dropped by a
  cache clear [PR #17033] [PR #17155].
- Service ids `mautic.cache.adapter.*` removed: a custom `cache_adapter` parameter must be a class name
  [code: UPGRADE-8.0.md:177 @8.x].
- `ResultCacheHelper::getCache()` returns a PSR-6 pool; `doctrine/cache` and `doctrine/common` removed [PR #17361].
- `AbstractIntegration` takes `CacheProviderInterface` as its second constructor argument and `getCache()` returns a
  PSR-16 cache [code: UPGRADE-8.0.md @8.x].
- No console command is added or removed on 8.x according to the inputs; the 8.0 user docs do not yet mention
  `file_lock` [code: UPGRADE-8.0.md @8.x] [docs: https://docs.mautic.org/en/8.0/configuration/cron_jobs.html].
- Code that must run on both: avoid `--lock_mode=file_lock` and `CacheStorageHelper`; inject `CacheProviderInterface`
  and treat both `null` and `false` as a miss [code: UPGRADE-8.0.md @8.x].
