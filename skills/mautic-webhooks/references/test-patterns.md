# Webhooks — test patterns

## Base classes and helpers

- Functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase` (real MySQL test DB). [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:12,24 @7.x]
- Fake the receiving server with `Mautic\CoreBundle\Test\Guzzle\ClientMockTrait`; `getClientMockHandler()` returns the container's Guzzle `MockHandler`, so append callables or `Response` objects to it. [code: app/bundles/CoreBundle/Test/Guzzle/ClientMockTrait.php:9-17 @7.x]
- Override config per test with `$this->setUpSymfony($this->configParams + ['queue_mode' => WebhookModel::COMMAND_PROCESS, 'webhook_limit' => 2])`. [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:41-50 @7.x]
- Run the processor with `$this->testSymfonyCommand(ProcessWebhookQueuesCommand::COMMAND_NAME, ['--webhook-id' => $id])`. [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:79 @7.x]
- `$this->authenticateApi = true` logs the test client in with HTTP Basic for API calls. [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:41 @7.x]
- Tests that truncate tables set `protected $useCleanupRollback = false;` and truncate `leads, webhooks, webhook_queue, webhook_events` in `setUp`/`beforeTearDown`. [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:29,52-64 @7.x]
- Unit tests extend `PHPUnit\Framework\TestCase` with mocks (e.g. `Tests/Unit/Http/ClientTest.php` asserts the exact header set and signature). [code: app/bundles/WebhookBundle/Tests/Unit/Http/ClientTest.php:39-75 @7.x]

## Representative tests to copy from

| Test | What it shows |
|---|---|
| `WB/Tests/Functional/WebhookFunctionalTest.php` | Command mode end to end: queue counts after creating Contacts, range mode (L88-102), failure notifications (L126-162), unhealthy skip and recovery (L166-199). |
| `WB/Tests/Functional/Model/WebhookModelProcessFailureTest.php` | Kill rules (data provider, L37-62), 404 single log (L63), recent-modification grace and `disable_auto_unpublish` (L78-115). |
| `WB/Tests/Functional/Model/WebhookModelTest.php` | ASC/DESC queue ordering (L27-66). |
| `WB/Tests/Functional/Command/ProcessWebhookQueuesCommandTest.php`, `DeleteWebhookLogsCommandTest.php` | Command no-op rules (L67); log trimming (L27-64). |
| `WB/Tests/Functional/Controller/AjaxControllerTest.php` | Test-payload validation and private-address refusal (L14-128). |
| `WB/Tests/Unit/Http/ClientTest.php` | Header set and HMAC (L39-75). |
| `WB/Tests/Unit/Model/WebhookModelTest.php` | Payload envelope assembly (L189-231), secret generation (L71). |
| `WB/Tests/Functional/CampaignSendWebhookFunctionalTest.php`, `WB/Tests/Unit/Helper/CampaignHelperTest.php` | Campaign "Send a webhook" action (L61-113). |

[code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:88-199 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/Model/WebhookModelProcessFailureTest.php:37-115 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/Model/WebhookModelTest.php:27-66 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/Controller/AjaxControllerTest.php:14-128 @7.x] [code: app/bundles/WebhookBundle/Tests/Unit/Model/WebhookModelTest.php:71,189-231 @7.x]

No Codeception acceptance tests cover webhooks. [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:24 @7.x]

## Fixture: a Webhook in code

```php
$webhook = new Webhook();
$event   = new Event();
$event->setEventType('mautic.lead_post_save_new');
$event->setWebhook($webhook);
$webhook->addEvent($event);
$webhook->setName('Webhook from a functional test');
$webhook->setWebhookUrl('https://httpbin.org/post');
$webhook->setSecret('any_secret_will_do');
$webhook->isPublished(true);
$webhook->setCreatedBy(1);   // needed for notification recipients
$this->em->persist($event);
$this->em->persist($webhook);
$this->em->flush();
```
[code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:202-220 @7.x]

## Skeleton: signature and envelope regression test

```php
final class MyWebhookDeliveryTest extends MauticMysqlTestCase
{
    use ClientMockTrait;

    protected $useCleanupRollback = false;

    protected function setUp(): void
    {
        parent::setUp();
        $this->setUpSymfony($this->configParams + ['queue_mode' => WebhookModel::COMMAND_PROCESS]);
    }

    public function testDeliveryIsSignedAndEnveloped(): void
    {
        $webhook = $this->createWebhook();          // as in the fixture above
        $this->getClientMockHandler()->append(function (RequestInterface $request): Response {
            $body = (string) $request->getBody();
            $expected = base64_encode(hash_hmac('sha256', $body, 'any_secret_will_do', true));
            Assert::assertSame($expected, $request->getHeaderLine('Webhook-Signature'));
            Assert::assertSame('application/json', $request->getHeaderLine('Content-Type'));
            $json = json_decode($body, true);
            Assert::assertArrayHasKey('mautic.lead_post_save_new', $json);
            Assert::assertArrayHasKey('timestamp', $json['mautic.lead_post_save_new'][0]);
            return new Response(200);
        });

        // create an identified Contact here so mautic.lead_post_save_new is queued

        $this->testSymfonyCommand(ProcessWebhookQueuesCommand::COMMAND_NAME, ['--webhook-id' => $webhook->getId()]);
        // assert webhook_queue is empty and one webhook_logs row with status_code 200 exists
    }
}
```
Algorithm source: [code: app/bundles/WebhookBundle/Http/Client.php:25-30 @7.x]

## What a good regression test asserts

- Queue row count after the triggering action (queued mode) and zero rows after a 2xx. [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:66-82 @7.x]
- Exactly one `webhook_logs` row per attempt, including transport errors (`N/A`). [code: app/bundles/WebhookBundle/Tests/Functional/Model/WebhookModelProcessFailureTest.php:63 @7.x]
- Publish state after failures: killed only when no 2xx in the window; not killed when recently modified or `disable_auto_unpublish`. [code: app/bundles/WebhookBundle/Tests/Functional/Model/WebhookModelProcessFailureTest.php:37-115 @7.x]
- `retries` incremented and the row kept on non-2xx. [code: app/bundles/WebhookBundle/Model/WebhookModel.php:309-331 @7.x]
- For a new event type: the key appears in `GET /api/hooks/triggers` and the payload keys/serializer groups match the documented table. [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php:90-99 @7.x]
- Append one mock response per request you expect (the core helper appends one callable per expected call) and count calls inside the callable. [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:274-290 @7.x]
