# Cron, queues and cache - pull-request history

## Contents
- [How to read this file](#how-to-read-this-file)
- [Decisions that shaped current behaviour](#decisions-that-shaped-current-behaviour)
- [Regression catalogue](#regression-catalogue)
- [Feature timeline](#feature-timeline)
- [Removed, deprecated, replaced](#removed-deprecated-replaced)
- [Maintainer norms for this area](#maintainer-norms-for-this-area)
- [Open questions](#open-questions)
- [Coverage](#coverage)

## How to read this file
Source: merged pull requests on github.com/mautic/mautic for QueueBundle, MessengerBundle, CacheBundle and the console runtime, harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; `~` marks an inference. Versions without `~` were checked against the release tags in the 7.x tree.
Current behaviour lives in behaviour.md (code-verified); this file explains why and when it came to be.

## Decisions that shaped current behaviour

### Legacy QueueBundle (2.11 to 4.x) - historical
Everything in this group is historical. QueueBundle and `mautic:queue:process` do not exist in 5.x to 7.x; Symfony Messenger replaced them in 5.0 [PR #12648] (v5.0). Only an empty `app/bundles/QueueBundle/Config/config.php` remains (behaviour H3).
- Email-open and landing-page hits could be pushed to a queue and processed asynchronously instead of in the request [PR #3873] (~v2.11). Why: open and page-hit tracking were the main scaling bottleneck. The design was event-based so that other protocols could be added through listeners [PR #3873].
- The legacy queue supported RabbitMQ and Beanstalkd, set on a "Queue Settings" page, and was consumed with `app/console mautic:queue:process -i page_hit|email_hit` (`-m` = max messages) [PR #3873] (~v2.11).
- With no queue configured, hit tracking behaved exactly as before, so the feature was backward compatible by default [PR #3873] (~v2.11).
- The RabbitMQ consumer declared queues with `auto_delete=false`, the same as the producer, because RabbitMQ rejects inequivalent declarations [PR #6573] (~v2.14.2).
- Queue form fields were registered by FQCN so the Queue tab worked on Symfony 3 [PR #8214] [PR #8239] (~v3.0).
- From 3.0, queue settings were meant to be edited in `local.php`, followed by a manual cache delete, because the "containerless config" no longer rebuilds the cache when config changes [PR #8320] (~v3.0). A `bin/console queue:enable` command was suggested and not built [PR #8320]. The GUI docs page went out of date as a result [PR #9391].
- The Beanstalkd consumer recovered from `Socket timed out!` in `command_process` mode [PR #8395] (~v3.0).
- `mautic:queue:process` gained `--timeout|-t SECONDS` so a consumer on an empty queue would stop [PR #9394] (~v3.3). `rabbitmq_idle_timeout` and `rabbitmq_idle_timeout_exit_code` (both default 0) followed [PR #9391] (~v4.0). A `graceful_max_execution` key was rejected because the RabbitMQ bundle applies it whenever it is set [PR #9391].

### Message serialisation: a policy reversal
- 2.11: queued hit payloads stored the Request as a flat array and rebuilt it on consume. Native object serialisation was rejected because `unserialize` can trigger `__wakeup` (a security risk) and queue admin UIs could not display jobs holding Symfony classes [PR #3873] (~v2.11).
- 5.0: Messenger messages use native PHP serialisation. JSON was proposed and dropped, because mixing JSON and PHP serialisation breaks the failed transport (symfony/symfony#33394) and the size difference (7 kB vs 8.7 kB) was negligible [PR #12648] (v5.0).
- The 5.0 rule is the current one. The `Request` is still flattened to its bags and rebuilt, to avoid "Cannot serialize closure" [PR #12648] (v5.0). Behaviour C14 confirms this in 7.x.
- Consequence: anyone who can write to a Messenger transport can inject PHP-serialised objects. Keep transports (Doctrine table, Redis) trusted (inferred from [PR #3873] and [PR #12648]).

### Symfony Messenger (5.0+)
- Messenger arrived as a new MessengerBundle with its own Configuration section. The large original PR #11180 was split: bundle and config UI first, queue wiring after [PR #11598] (v5.0).
- Queuing is off by default. The `email` and `hit` DSNs default to `sync://`, which means no queue [PR #12509] (v5.0). Behaviour C3 confirms this.
- Any Symfony Messenger transport can be set as a DSN, without a Mautic plugin per transport [PR #12509] (v5.0). 7.0 later stopped bundling `symfony/amqp-messenger` (behaviour C7).
- The failure transport became configurable in the UI and optional (`messenger_dsn_failed`). Before this, one Doctrine option was hard-coded [PR #12509] (v5.0). In 7.x an empty failure DSN discards messages (behaviour C5).
- Retry settings (max retries, delay, multiplier, max delay) are read from parameters, so a change applies without rebuilding the Symfony cache [PR #12509] (v5.0). A running worker still keeps the values it loaded; restart it (behaviour C12).
- Queue Settings gained test buttons that dispatch `TestEmail`, `TestHit` and `TestFailed` [PR #12509] (v5.0). Their handler was removed in 7.0, so the button cannot report success in 7.x (behaviour C13).
- Page and email hits are queued through Messenger and configured in the existing Configuration UI. Buses need no configuration [PR #12648] (v5.0). The PR is labelled bc-break; deprecations are in UPGRADE-5.0.md [PR #12648].
- Hit messages are `EmailHitNotification` and `PageHitNotification`. The hit time is captured when the message is created, so late processing does not change the recorded time (inferred from the `eventTime` payload field) [PR #12648] (v5.0).
- The retry fields are validated: multiplier ≥ 1, and max retries, delay and max delay ≥ 0 [PR #16157] (v7.1.3). Why: Symfony's `MultiplierRetryStrategy` rejects a multiplier below 1. A saved 0 crashed the worker on every redelivery, left the failed message stuck and, with email batching, caused duplicate sends [PR #16157].
- "DSN" is spelt `dsn` everywhere: form type, JS, translations and the AJAX controller [PR #13259] (~v5.0.3).
- Messenger message and handler classes without children are `final` since 7.2. Plugins must not extend them [PR #16897] (v7.2.0).

### Locking and the command runtime
- `ModeratedCommand` can lock through the Symfony Lock component, including a Redis store: `--lock_mode|-x redis` with `cache_adapter_redis.dsn` [PR #10347] (v5.0).
- The lock key is the command plus its id. Runs that differ only by `--min-contact-id`/`--max-contact-id` still collide [PR #10347] (~v5.0). The maintainers' answer: scale email sending with more Messenger workers, not contact-id ranges [PR #10347].
- `mautic:campaigns:trigger --max-threads=N --thread-id=X` gives each thread its own lock key, because thread 2 was refused with "Script in progress" [PR #11747] (~v5.0). Behaviour B confirms the `<id>-<thread>` key.
- `mautic:campaigns:trigger`, `mautic:campaigns:rebuild` and `mautic:webhooks:process` return a non-zero exit code when the given id does not exist, so cron wrappers can detect failure [PR #11963] (~v4.4.8) [PR #12203] (~v5.0).
- `mautic:segments:update -q` prints nothing unless there is an error, because cron mails any output [PR #10533] (~v4.0.2).
- `mautic:segments:update`, `mautic:campaigns:rebuild` and `mautic:campaigns:trigger` accept `--exclude` (repeatable ids) [PR #13383] (v5.1.0).
- `mautic:segments:update` no longer updates Campaign membership; `mautic:campaigns:rebuild` does [PR #10550] (v5.0). It was not treated as a BC break because both are required crons [PR #10550].
- The console defaults to the `prod` environment and reports Mautic's name and version [PR #613] (~v1.1). It was made executable [PR #826] (~v1.2). The path is now `bin/console`.
- The console calls `set_time_limit()` only when the function exists, because hosts that disable it filled their disks with cron warnings [PR #3165] (~v2.6).
- Console commands use the php.ini `date.timezone` instead of forcing UTC, because relative options such as `--time-interval=20minutes` were computed in the wrong zone [PR #7617] (~v2.16.1). In 7.x UTC is used only when `date.timezone` is empty [code: app/console-application.php:4-6 @7.x].
- `mautic:motd`, run from composer `post-install-cmd`, always exits 0, because a failed fetch blocked CI and installs [PR #16226] (~v7.2).

### Cache
- The Symfony cache can be cleared from the CLI with plugins fully registered, because the table-prefix constant is defined in kernel `boot()` [PR #590] (~v1.1.3).
- Middlewares are compiled into `var/cache/<env>/middlewares.cache.php` and not globbed on every request [PR #8250] (~v3.0). Deleting `var/cache/*` must still work: the middleware cache is warmed when missing [PR #8568] (~v3.0) [code: app/middlewares/MiddlewareBuilder.php:18,38-45 @7.x].
- CacheBundle adds a tag-aware cache with filesystem, Memcached and Redis adapters, plus `mautic:cache:clear` and a cache-clear subscriber [PR #9107] (~v3.3). Why: Acquia's fork relied on it and changed no existing behaviour [PR #9107].
- The filesystem adapter writes under `mautic.tmp_path`, not `sys_get_temp_dir()`, because `cache:clear` threw when `/tmp` was not accessible [PR #9929] (~v4.4.7) [PR #11885] (v5.0). The objection "set sys_temp_dir in php.ini" was overruled [PR #9929].
- `CacheProvider::clear()` accepts `$prefix` to match the Symfony ≥ 4.4 signature [PR #12200] (~v5.0). Behaviour G8 records that 7.x ignores the prefix and clears the whole pool.
- Redis caching has a non-tag-aware provider (`cache_adapter`) and a tag-aware one (`cache_adapter_tag_aware`), because the tag-aware provider caused about 50% more Redis queries where tags were not needed [PR #14724] (v7.0.0). After changing the adapter, delete the cache directory [PR #14724].
- Segment contact counts moved from the database (`CacheStorageHelper`) to the configured cache provider, because many small cache queries pushed MySQL to 100% CPU [PR #15554] (~v7.0). With `update_segment_contact_count_in_background` on, `lead:list:count-cache-update` recounts them from cron [PR #14911] (v7.0.0).
- CacheBundle service definitions moved from `config.php` to autowired `services.php` [PR #16800] (v7.2.0).

## Regression catalogue

| Sub-topic | Symptom | Expected behaviour | PR | Version |
|---|---|---|---|---|
| Console | Cron logged `set_time_limit` warnings on hardened hosts | The call is skipped when the function is unavailable | [PR #3165] | ~2.6 |
| Console | Console used UTC regardless of php.ini | Console honours `date.timezone`; UTC only when it is empty | [PR #7617] | ~2.16.1 |
| Console | `mautic:segments:update -q` printed output, so cron sent mail | Silent under `-q` unless there is an error | [PR #10533] | ~4.0.2 |
| Console | Trigger/rebuild/webhooks:process exited 0 for an unknown id | Non-zero exit code | [PR #11963] [PR #12203] | ~4.4.8 / ~5.0 |
| Console | `mautic:motd` fetch failure failed `composer install` and CI | Command always exits 0 | [PR #16226] | ~7.2 |
| Locking | Trigger thread 2..N refused with "Script in progress" | Each `--thread-id` has its own lock key | [PR #11747] | ~5.0 |
| Messenger | Install failed with an undefined `messenger_transport` key (found in review) | CLI and web installs work with Messenger defaults | [PR #11598] | 5.0 |
| Messenger | Retry-strategy changes ignored until the cache was cleared | Retry settings are read from parameters | [PR #12509] | 5.0 |
| Messenger | Failure transport could not be configured | `messenger_dsn_failed` is configurable and optional | [PR #12509] | 5.0 |
| Messenger | Multiplier 0 or 0.5 saved; worker crashed hourly, message stuck, duplicate sends | Form rejects multiplier < 1 and negative retries, delay or max delay | [PR #16157] | 7.1.3 |
| Cache | CLI `cache:clear` with a table prefix dropped plugin routes, menus and services | CLI and web cache builds see the same plugins | [PR #590] | ~1.1.3 |
| Cache | `rm -rf var/cache/*` then load gave "No middleware cache file found" | Middleware cache is rebuilt on demand | [PR #8568] | ~3.0 |
| Cache | `cache:clear` failed when `/tmp` was not accessible | Filesystem cache uses `mautic.tmp_path` | [PR #9929] [PR #11885] | ~4.4.7 / 5.0 |
| Cache | Redis cache issued about 50% extra queries | Non-tag operations use the non-tag-aware provider | [PR #14724] | 7.0.0 |

Historical regressions that no longer apply (QueueBundle, PHP 7 class cache): RabbitMQ `PRECONDITION_FAILED` [PR #6573], Beanstalkd socket timeout [PR #8395], queue protocol switch crash [PR #8320], cache files rewritten on every PHP 7 request [PR #7318].

## Feature timeline

| Version | Change | PR |
|---|---|---|
| ~1.0-1.2 | Upgrade cache-clear step reports state; console defaults to `prod`; CLI cache clear sees plugins; console made executable | [PR #170] [PR #613] [PR #590] [PR #826] |
| ~2.6-2.7 | `set_time_limit` guard; PHP 7.1 support added and reverted next day | [PR #3165] [PR #3416] [PR #3573] |
| ~2.11 | Legacy hit queue (RabbitMQ/Beanstalkd), `mautic:queue:process` | [PR #3873] |
| ~2.14.2-2.16.1 | RabbitMQ `auto_delete` fix; PHP 7 class-cache warm-up; console honours php.ini timezone | [PR #6573] [PR #7318] [PR #7617] |
| ~3.0 | Middleware cache file; queue settings move to `local.php`; Beanstalkd timeout recovery; middleware cache rebuilt on demand | [PR #8250] [PR #8320] [PR #8395] [PR #8568] |
| ~3.3 | CacheBundle and `mautic:cache:clear`; `mautic:queue:process --timeout` | [PR #9107] [PR #9394] |
| ~4.0 | `rabbitmq_idle_timeout`; `segments:update -q` silent | [PR #9391] [PR #10533] |
| ~4.4.7-4.4.8 | Filesystem cache under tmp_path; non-zero exit for unknown Campaign id | [PR #9929] [PR #11963] |
| 5.0 | MessengerBundle and Messenger configuration | [PR #11598] |
| 5.0 | Any-transport DSNs, optional failure transport, test buttons, live retry settings | [PR #12509] |
| 5.0 | Email and page hits through Messenger; QueueBundle removed; PHP serialisation | [PR #12648] |
| 5.0 | Redis lock mode for `ModeratedCommand` | [PR #10347] |
| 5.0 | `segments:update` stops updating Campaigns; trigger threads get own lock keys | [PR #10550] [PR #11747] |
| 5.0 | tmp_path cache fix forward-ported; `CacheProvider::clear($prefix)` signature | [PR #11885] [PR #12200] |
| ~5.0.3 | DSN spelling unified | [PR #13259] |
| 5.1.0 | `--exclude` on segments:update, campaigns:rebuild, campaigns:trigger | [PR #13383] |
| 5.1.0 | `mautic:campaign:delete-event-logs` (background event-log deletion) | [PR #10219] |
| 6.0.0 | `mautic:segments:stat` | [PR #14575] |
| 7.0.0 | Separate non-tag-aware and tag-aware Redis cache providers | [PR #14724] |
| 7.0.0 | Segment counts in the cache provider; `lead:list:count-cache-update` | [PR #15554] [PR #14911] |
| 7.1.0 | `mautic:segment:delete` (background Segment delete) | [PR #15755] |
| 7.1.3 | Retry-setting validation in Queue Settings | [PR #16157] |
| 7.2.0 | CacheBundle autowired services; final Messenger classes; `mautic:motd` always exits 0 | [PR #16800] [PR #16897] [PR #16226] |

## Removed, deprecated, replaced

| What | Replaced by | PR | Version | Note |
|---|---|---|---|---|
| QueueBundle (RabbitMQ/Beanstalkd, `mautic:queue:process`, `queue_protocol`, `rabbitmq_*`) | Symfony Messenger, `messenger:consume email|hit` | [PR #12648] [PR #11598] [PR #12509] | 5.0 | bc-break; set `messenger_dsn_*` |
| Queue settings in the GUI (3.x) | `local.php` plus a manual cache delete | [PR #8320] | ~3.0 | Historical; replaced again by the Messenger UI in 5.0 |
| Flat-array queue payloads (no object serialisation) | Native PHP serialisation | [PR #3873] [PR #12648] | 5.0 | JSON was proposed and dropped |
| One cache provider for everything | `CacheProviderInterface` plus `CacheProviderTagAwareInterface` | [PR #14724] | 7.0.0 | Depend on the tag-aware interface only where tags are needed |
| Segment count cache in the database | Configured cache provider | [PR #15554] | ~7.0 | Old DB-cached counts are not read |
| Segment rebuild updating Campaign membership | `mautic:campaigns:rebuild` | [PR #10550] | 5.0 | Both crons are required |
| CacheBundle services in `config.php` | Autowired `services.php` | [PR #16800] | 7.2.0 | none |
| PHP 7.1 support (2.7) | Reverted | [PR #3573] | ~2.7 | Historical |

## Maintainer norms for this area
- Do not serialise PHP objects into queues; prefer flat data [PR #3873]. Messenger is the pragmatic exception, for failed-transport compatibility [PR #12648].
- Split very large features into reviewable PRs: bundle and config UI first, wiring second [PR #11598].
- Symfony BC breaks that Symfony already documents need not be repeated in Mautic's UPGRADE notes [PR #12200].
- Temporary PHPStan ignores are acceptable to unblock an upgrade, with a note to remove them [PR #12200].
- New capabilities need user or developer docs; reviewers chase missing docs after merge [PR #9107] [PR #14724] [PR #9391] [PR #13383].
- Error and help strings should guide the user to a fix [PR #12509].
- Prefer functional tests that drive the real endpoint (for example `/s/config/edit`) over `TypeTestCase` unit tests [PR #16157].
- Bug fixes target the current patch branch; Rector and refactor PRs (final classes, autowiring) go to the next minor [PR #16157] [PR #16800] [PR #16897].
- Fixes are forward-ported to the next major as separate PRs [PR #9929] [PR #11885].
- Commands run from composer hooks must not fail the build for non-essential work [PR #16226].
- Scale email throughput with more Messenger workers rather than contact-id ranges [PR #10347].

## Open questions
- [PR #12509] says retry changes apply without a cache rebuild. `RetryStrategy` memoises the values per process, so a running worker needs a restart (behaviour C12). Not a conflict, but the PR wording overstates it.
- [PR #12200] made `clear()` accept `$prefix`, but 7.x ignores it (behaviour G8). Whether prefix-scoped clearing was ever intended is unclear.
- [PR #9929]: maintainers disagreed on whether the tmp_path override is right; `sys_get_temp_dir()` is still used elsewhere.
- [PR #7617]: installs that relied on UTC may have seen times shift; no follow-up was found.
- [PR #14724]: Redis cache configuration was flagged as missing from the user docs (2025-07).
- [PR #3873]: hits appeared in the UI even when the queue was not consumed; whether this was fixed before merge is unknown (historical only).
- [PR #170]: no description; its exact change is unknown.

## Coverage
- messenger-queue-cache chunk: 26 PRs, 22 substantive, 4 noise or pure refactor (#12972, #16305, #16800, #16897; the last two are still recorded above) [PR #12972] [PR #16305].
- Routed in from the uncategorised bucket: 7 PRs (#613, #826, #3165, #7617, #8250, #3416, #3573). From the misc chunk only [PR #16226] (motd exit code) belongs to this area.
- Cross-checked, not re-analysed: campaigns chunk 3 ([PR #10347], [PR #10550], [PR #11747], [PR #11963], [PR #12203], [PR #13383], [PR #10219]) and segments chunks 2-3 ([PR #10533], [PR #14575], [PR #14911], [PR #15554], [PR #15755]). Their full analysis is in mautic-campaigns and mautic-segments.

869 noise PRs were excluded upstream, before chunking.
