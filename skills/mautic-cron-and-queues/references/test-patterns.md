# Test patterns — commands, locking, Messenger, cache

Run everything through DDEV: `ddev exec php bin/phpunit -c app/phpunit.xml.dist <path> [--filter testName]`
[code: AGENTS.md ("Command Execution Rule", "Testing") @7.x].

## 1. Base classes

| Need | Base class | Notes |
|---|---|---|
| Pure logic (lock modes, retry strategy, handlers with mocks) | `PHPUnit\Framework\TestCase` | Mock `EmailModel`, `PageModel`, repositories, `CoreParametersHelper`. [code: app/bundles/MessengerBundle/Tests/MessageHandler/EmailHitNotificationHandlerTest.php:43-91 @7.x] |
| Run a real command against the DB | `Mautic\CoreBundle\Test\MauticMysqlTestCase` | Transaction rolled back after each test; Mautic cache pool cleared in setup. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:57-91,385-390 @7.x] |
| Kernel without DB | `Mautic\CoreBundle\Test\AbstractMauticTestCase` | Sets `MAUTIC_CONFIG_PARAMETERS` from `$this->configParams`. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61,111-114 @7.x] |

Test-environment defaults: `mailer_dsn=null://null`, `messenger_dsn_email=in-memory://default`,
`messenger_dsn_hit=sync://`, `messenger_dsn_failed=in-memory://default`, `create_custom_field_in_background=false`
[code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x].

## 2. Running a command in a functional test

- Use `$this->testSymfonyCommand('<name>', [options])`, then assert on `getDisplay()` and `getStatusCode()`. Do not
  build `Application`/`ArrayInput` by hand [code: .github/prompts/write-test.prompt.md:33-37 @7.x].
- `--bypass-locking` is added automatically when the command defines it, so functional tests never exercise the lock
  [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:212-216 @7.x]. Test locking with the unit test below.
- Call `$this->em->clear()` before running the command so it loads fresh entities
  [code: .github/prompts/write-test.prompt.md:33-37 @7.x].
- Override settings before `parent::setUp()`: `$this->configParams['clean_webhook_logs_in_background'] = true;`
  [code: app/bundles/WebhookBundle/Tests/Command/DeleteWebhookLogsCommandTest.php:18-22 @7.x].
- Commands that `define()` constants (e.g. `MAUTIC_INTEGRATION_SYNC_IN_PROGRESS`) need `#[RunInSeparateProcess]`
  [code: app/bundles/CoreBundle/Test/Extensions/SeparateProcess/SeparateProcess.php:29-31,76-87 @7.x].

Skeleton:

```php
<?php
declare(strict_types=1);

namespace Mautic\WebhookBundle\Tests\Command;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\WebhookBundle\Command\DeleteWebhookLogsCommand;
use Symfony\Component\Console\Command\Command;

final class DeleteWebhookLogsCommandSketchTest extends MauticMysqlTestCase
{
    protected function setUp(): void
    {
        $this->configParams['clean_webhook_logs_in_background'] = true;
        $this->configParams['webhook_log_max']                  = 2;
        parent::setUp();
    }

    public function testKeepsOnlyNewestLogs(): void
    {
        // arrange: persist a Webhook and 5 Log rows, then $this->em->flush(); $this->em->clear();
        $tester = $this->testSymfonyCommand(DeleteWebhookLogsCommand::COMMAND_NAME);

        $this->assertSame(Command::SUCCESS, $tester->getStatusCode());
        // assert: 2 Log rows remain for the Webhook
    }
}
```
Pattern taken from [code: app/bundles/WebhookBundle/Tests/Command/DeleteWebhookLogsCommandTest.php:18-85 @7.x].

## 3. Testing ModeratedCommand locking

Copy `app/bundles/CoreBundle/Tests/Unit/Command/ModeratedCommandTest.php` with its
`Tests/Unit/Command/src/FakeModeratedCommand.php`. Existing cases: unwritable lock file throws (65), bypass touches no
lock (85), deprecated `--force` recognised (102), pid lock blocks a second run (120-168), unopenable pid file (170),
flock (226), redis (280), `completeRun()` variants (308-359)
[code: app/bundles/CoreBundle/Tests/Unit/Command/ModeratedCommandTest.php:65-359 @7.x].

A good regression test for a new moderated command asserts: (1) the second run with the same moderation key exits 0
and prints "Script in progress"; (2) a run with a different key is not blocked; (3) the lock file is removed after
`completeRun()`.

## 4. Testing Messenger behaviour

- Email sends routed through Messenger: with the default `in-memory://default` use `assertQueuedEmailCount(n)`; for
  synchronous sends use `assertEmailCount(n)`; read messages with `getMailerMessages()` /
  `getMailerMessagesByToAddress()` [code: app/bundles/CampaignBundle/Tests/Controller/Api/CampaignApiControllerFunctionalTest.php:254 @7.x]
  [code: app/bundles/EmailBundle/Tests/Controller/Api/SMimeFunctionalTest.php:27-28,111-112 @7.x].
- To make a queued send happen immediately set `$this->configParams['messenger_dsn_email'] = 'sync://';`
  [code: app/bundles/LeadBundle/Tests/Controller/LeadControllerTest.php:57 @7.x].
- Page-hit side effects appear immediately because the test `hit` DSN is `sync://`
  [code: app/bundles/PageBundle/Tests/Functional/Model/PageHitCookieTest.php:17-70 @7.x].
- Async path end to end: `ReportControllerFunctionalTest` switches `messenger_dsn_email` to `doctrine://default` through
  the Queue Settings form, runs `mautic:reports:scheduler` and asserts the attachment survives until consumption
  [code: app/bundles/ReportBundle/Tests/Controller/ReportControllerFunctionalTest.php:553-596 @7.x].
- Handler units: assert that `RetryableException` becomes `RecoverableMessageHandlingException` and that other
  exceptions propagate; assert `processPageHit($hit, $page, $request, $lead, false, false)`
  [code: app/bundles/MessengerBundle/Tests/MessageHandler/EmailHitNotificationHandlerTest.php:43-91 @7.x]
  [code: app/bundles/MessengerBundle/Tests/MessageHandler/PageHitNotificationHandlerTest.php:68-73 @7.x].
- Queue Settings form: submit `/s/config/edit/messengerconfig` and assert multiplier `0`/`0.5` rejected, `3` accepted
  [code: app/bundles/MessengerBundle/Tests/Form/Type/ConfigTypeTest.php:21-49 @7.x].
- No test consumes an in-memory transport explicitly; there is no Mautic helper for `messenger:consume` in tests
  [code: app/bundles/MessengerBundle/Tests (grep InMemoryTransport → none) @7.x].

## 5. Testing cache usage

- Unit: mock `CacheProviderInterface` / `CacheProviderTagAwareInterface`
  [code: app/bundles/LeadBundle/Tests/Helper/SegmentCountCacheHelperTest.php @7.x].
- Provider wiring: `app/bundles/CacheBundle/Tests/Cache/CacheProviderTest.php:36-64`; clear hook:
  `Tests/EventListener/CacheClearSubscriberTest.php:32-37` [code: app/bundles/CacheBundle/Tests/Cache/CacheProviderTest.php:36-64 @7.x].
- Functional tests start with an empty pool, so cached counts never leak between tests
  [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:385-390 @7.x].

## 6. Representative tests to copy

1. `app/bundles/CoreBundle/Tests/Unit/Command/ModeratedCommandTest.php` — locking.
2. `app/bundles/WebhookBundle/Tests/Command/DeleteWebhookLogsCommandTest.php` — functional command with config override.
3. `app/bundles/ReportBundle/Tests/Scheduler/Command/ExportSchedulerCommandTest.php` — options and exit codes.
4. `app/bundles/LeadBundle/Tests/Command/ImportCommandTest.php` — command with signal handling.
5. `app/bundles/MessengerBundle/Tests/MessageHandler/EmailHitNotificationHandlerTest.php` — handler retry semantics.
6. `app/bundles/ReportBundle/Tests/Controller/ReportControllerFunctionalTest.php:553-596` — queue DSN end to end.

[code: app/bundles/ReportBundle/Tests/Scheduler/Command/ExportSchedulerCommandTest.php @7.x]

## 7. Regression tests worth adding

Rows from references/pr-history.md (Regression catalogue) for which a grep of the 7.x `Tests/` directories found no test.

| Behaviour to assert | Suggested test | PR |
|---|---|---|
| The console skips `set_time_limit()` when the function is unavailable | Unit test of `app/console-application.php` bootstrap, or a process test with `disable_functions` | [PR #3165] |
| The console uses php.ini `date.timezone` and falls back to UTC only when it is empty | Process test running a command with `-d date.timezone=Europe/Prague` | [PR #7617] |
| `mautic:segments:update -q` writes nothing when there is no error | Functional `testSymfonyCommand('mautic:segments:update', ['-q' => true])`, assert empty display | [PR #10533] |
| `mautic:campaigns:trigger`, `mautic:campaigns:rebuild` and `mautic:webhooks:process` exit non-zero for an unknown id | Functional command test with `-i 999`, assert `Command::FAILURE` | [PR #11963] [PR #12203] |
| Two trigger threads of the same Campaign do not block each other | Unit test in the style of `ModeratedCommandTest` with keys `<id>-1` and `<id>-2` | [PR #11747] |
| Deleting `var/cache/<env>/middlewares.cache.php` and booting rebuilds it | Unit test of `MiddlewareBuilder::resolve()` with a missing cache file | [PR #8568] |
| `RetryStrategy` reads the four `messenger_retry_strategy_*` parameters | Unit test with a mocked `CoreParametersHelper`, assert waiting times 1000/2000/4000 ms | [PR #12509] |

