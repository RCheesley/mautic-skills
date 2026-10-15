# Test recipes (copy-ready skeletons)

Each skeleton is adapted from a real 7.2.1 test, cited under its heading. Replace the namespace, entities and
assertions. All tests run with `ddev exec php bin/phpunit -c app/phpunit.xml.dist <file> [--filter testName]`
[code: AGENTS.md @7.x].

Contents
1. Functional controller test (UI route, form, flash)
2. REST API test (v1 form-encoded and v2 JSON)
3. Console command test
4. Event listener test (functional side effect)
5. Unit test with mocks
6. Mailer assertion
7. Config override per test or per method
8. Custom-field test needing a full reset
9. Choosing a recipe for a change

Rules every recipe follows: `declare(strict_types=1);`, `final class ...Test`, typed properties, `testDescriptiveName(): void`,
services fetched with `self::getContainer()->get(Foo::class)` [code: .github/prompts/write-test.prompt.md:17-26 @7.x]
[code: utils/phpstan/src/Rule/NoContainerGetRule.php:42-47 @7.x].

## 1. Functional controller test

Adapted from `app/bundles/EmailBundle/Tests/Functional/EmailClickTrackingTest.php:1-56` (public route) and
`app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:170-186` (form submit and flash)
[code: app/bundles/EmailBundle/Tests/Functional/EmailClickTrackingTest.php:1-56 @7.x]
[code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:170-186 @7.x].

```php
<?php

declare(strict_types=1);

namespace Mautic\ExampleBundle\Tests\Controller;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\LeadBundle\Entity\Lead;
use Symfony\Component\HttpFoundation\Request;

final class ExampleControllerFunctionalTest extends MauticMysqlTestCase
{
    // No setUp() needed: the base class logs in "admin" and opens a transaction that is rolled back.

    public function testAdminCanSaveAndSeesSuccessFlash(): void
    {
        $contact = new Lead();
        $contact->setEmail('john@example.com');
        $this->em->persist($contact);
        $this->em->flush();

        $crawler = $this->client->request(Request::METHOD_GET, '/s/contacts/edit/'.$contact->getId());
        self::assertResponseIsSuccessful();

        $form = $crawler->selectButton('lead[buttons][apply]')->form();   // adjust to the real button name
        $form->setValues(['lead[firstname]' => 'John']);
        $crawler = $this->client->submit($form);                       // redirects are followed
        self::assertResponseIsSuccessful();

        $flash = $crawler->filterXPath("//div[@id='flashes']//span");
        $this->assertGreaterThan(0, $flash->count());

        $this->em->clear();
        $this->assertSame('John', $this->em->getRepository(Lead::class)->find($contact->getId())?->getFirstname());
    }

    public function testPublicPageWorksForAnonymousVisitor(): void
    {
        $this->logoutUser();                                           // drop the admin session from setUp()
        $this->client->request(Request::METHOD_GET, '/some-public-page');
        self::assertResponseIsSuccessful();
    }
}
```
Notes: `followRedirects(true)` is set by the base class [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:111-128 @7.x].
For a user without admin rights use `UserEntityTrait::createUserWithPermission()` and `$this->loginUser($user)`
[code: app/bundles/CoreBundle/Tests/Functional/UserEntityTrait.php @7.x].

## 2. REST API test

v1, adapted from `app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php:32-66, 685-710`
[code: app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php:32-66, 685-710 @7.x].
That test relies on the admin session created by `setUp()`; set `$authenticateApi = true` to send HTTP basic credentials
instead [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:47-50, 117 @7.x].

```php
<?php

declare(strict_types=1);

namespace Mautic\ExampleBundle\Tests\Controller\Api;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

final class ExampleApiControllerFunctionalTest extends MauticMysqlTestCase
{
    protected function setUp(): void
    {
        $this->configParams['api_enabled'] = 'testDisabledApiReturns403' !== $this->name();
        parent::setUp();
    }

    public function testDisabledApiReturns403(): void
    {
        $this->client->request(Request::METHOD_POST, '/api/contacts/new', ['email' => 'a@example.com']);
        self::assertResponseStatusCodeSame(Response::HTTP_FORBIDDEN);
    }

    public function testCreateContact(): void
    {
        $payload = ['email' => 'api@example.com', 'firstname' => 'API', 'tags' => ['t1', 't2']];

        $this->client->request(Request::METHOD_POST, '/api/contacts/new', $payload);
        $response = $this->client->getResponse();
        self::assertResponseStatusCodeSame(Response::HTTP_CREATED, (string) $response->getContent());

        $data = json_decode((string) $response->getContent(), true);
        $this->assertSame('api@example.com', $data['contact']['fields']['all']['email']);
        $this->assertCount(2, $data['contact']['tags']);
    }
}
```

v2 (API Platform, JSON-LD body), adapted from
`app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:198-240`
[code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:198-240 @7.x]:

```php
$this->client->request(
    Request::METHOD_POST,
    '/api/v2/users',
    [],
    [],
    ['CONTENT_TYPE' => 'application/ld+json', 'HTTP_ACCEPT' => 'application/ld+json'],
    json_encode($userData)
);
self::assertResponseIsSuccessful();
```
Permission check pattern: create a user without the permission, `loginUser()` it, expect 403
[code: app/bundles/CampaignBundle/Tests/Controller/Api/CampaignApiControllerFunctionalTest.php:490-505 @7.x].
Payload shapes and endpoints are in mautic-rest-api.

## 3. Console command test

Adapted from `app/bundles/WebhookBundle/Tests/Functional/Command/DeleteWebhookLogsCommandTest.php:14-85`
[code: app/bundles/WebhookBundle/Tests/Functional/Command/DeleteWebhookLogsCommandTest.php:14-85 @7.x].

```php
<?php

declare(strict_types=1);

namespace Mautic\ExampleBundle\Tests\Functional\Command;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\WebhookBundle\Command\DeleteWebhookLogsCommand;

final class DeleteWebhookLogsCommandTest extends MauticMysqlTestCase
{
    protected function setUp(): void
    {
        $this->configParams['webhook_log_max'] = 5;     // config before parent::setUp()
        parent::setUp();
    }

    public function testCommandReportsNothingToDo(): void
    {
        $tester = $this->testSymfonyCommand(DeleteWebhookLogsCommand::COMMAND_NAME);

        $this->assertSame(0, $tester->getStatusCode());
        $this->assertStringContainsString('There is 0 webhooks with logs more than defined limit.', $tester->getDisplay());
    }

    public function testCommandDeletesOldestLogs(): void
    {
        // arrange: persist entities, then $this->em->clear() so the command loads fresh rows
        $this->em->clear();

        $tester = $this->testSymfonyCommand(DeleteWebhookLogsCommand::COMMAND_NAME, ['--some-option' => 'x']);

        $this->assertStringContainsString('logs deleted successfully', $tester->getDisplay());
        // assert: query the repository for what remains
    }
}
```
Do not build `Application`, `ArrayInput` or `BufferedOutput` by hand; `--bypass-locking` is added for you
[code: .github/prompts/write-test.prompt.md:33-37 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:200-223 @7.x].

## 4. Event listener test (functional side effect)

Adapted from `app/bundles/LeadBundle/Tests/Functional/EventListener/CompanySubscriberFunctionalTest.php:18-45`
[code: app/bundles/LeadBundle/Tests/Functional/EventListener/CompanySubscriberFunctionalTest.php:18-45 @7.x].
Trigger the listener through the model that dispatches the event and assert the side effect (here, the audit log).

```php
<?php

declare(strict_types=1);

namespace Mautic\ExampleBundle\Tests\Functional\EventListener;

use Mautic\CoreBundle\Entity\AuditLog;
use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\LeadBundle\Entity\Company;
use Mautic\LeadBundle\Model\CompanyModel;
use Mautic\UserBundle\Entity\User;

final class CompanySubscriberFunctionalTest extends MauticMysqlTestCase
{
    public function testSavingCompanyWritesAuditLog(): void
    {
        $user = $this->em->getRepository(User::class)->findOneBy(['username' => 'admin']);
        $this->assertInstanceOf(User::class, $user);

        $company = new Company();
        $company->setName('Test company');
        $company->setOwner($user);
        self::getContainer()->get(CompanyModel::class)->saveEntity($company);

        $log = $this->em->getRepository(AuditLog::class)->findOneBy([
            'bundle'   => 'lead',
            'object'   => 'company',
            'action'   => 'create',
            'objectId' => $company->getId(),
        ]);
        $this->assertInstanceOf(AuditLog::class, $log);
        $this->assertSame([null, "Admin User ({$user->getId()})"], $log->getDetails()['owner']);
    }
}
```
For a subscriber with no persistence, dispatch the event with the container's `event_dispatcher` service instead
[code: .github/prompts/write-test.prompt.md:18 @7.x]. Registration of every subscriber is already proved by
`EventSubscriberSmokeTest` [code: app/phpunit.xml.dist:50 @7.x].

## 5. Unit test with mocks

Adapted from `app/bundles/EmailBundle/Tests/EventListener/SegmentSubscriberTest.php:15-42` and
`app/bundles/CampaignBundle/Tests/EventListener/NotifyOfFailureSubscriberTest.php:15-50`
[code: app/bundles/EmailBundle/Tests/EventListener/SegmentSubscriberTest.php:15-42 @7.x]
[code: app/bundles/CampaignBundle/Tests/EventListener/NotifyOfFailureSubscriberTest.php:15-50 @7.x].
Mock services; build entities and events for real.

```php
<?php

declare(strict_types=1);

namespace Mautic\ExampleBundle\Tests\EventListener;

use Mautic\EmailBundle\EventListener\SegmentSubscriber;
use Mautic\EmailBundle\Model\EmailModel;
use Mautic\LeadBundle\Entity\Lead;
use Mautic\LeadBundle\Entity\LeadList;
use Mautic\LeadBundle\Event\ListChangeEvent;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;

final class SegmentSubscriberTest extends TestCase
{
    private MockObject&EmailModel $emailModel;

    private SegmentSubscriber $subscriber;

    protected function setUp(): void
    {
        parent::setUp();
        $this->emailModel = $this->createMock(EmailModel::class);
        $this->subscriber = new SegmentSubscriber($this->emailModel);
    }

    #[DataProvider('segmentIdProvider')]
    public function testListChangeInvalidatesCacheForThatSegment(int $segmentId): void
    {
        $segment = new LeadList();          // real entity, not a mock
        $segment->setId($segmentId);

        $this->emailModel->expects($this->once())
            ->method('invalidatePendingCountCacheForList')
            ->with($segmentId);

        $this->subscriber->onListChange(new ListChangeEvent(new Lead(), $segment));
    }

    /**
     * @return \Iterator<string, array{int}>
     */
    public static function segmentIdProvider(): \Iterator
    {
        yield 'first' => [42];
        yield 'second' => [7];
    }
}
```
Use `createStub()` when you do not assert calls (Rector `phpunitMockToStub`) [code: rector.php:10-25 @7.x].
On 8.x, `final` classes can be mocked through `dg/bypass-finals`, but `Request`, `InputBag` and `Router` must not be
doubled [code: composer.json @8.x] [PR #17366] [PR #17392].
For repository unit tests, `RepositoryConfiguratorTrait::configureRepository()` exists but its docblock recommends a
functional test instead [code: app/bundles/CoreBundle/Test/Doctrine/RepositoryConfiguratorTrait.php:15-18, 51-64 @7.x].

## 6. Mailer assertion

Adapted from `app/bundles/EmailBundle/Tests/Controller/EmailSendFunctionalTest.php:16-60` (Segment send through
Messenger) and `app/bundles/EmailBundle/Tests/Controller/AjaxControllerFunctionalTest.php:79-89` (synchronous test email)
[code: app/bundles/EmailBundle/Tests/Controller/EmailSendFunctionalTest.php:16-60 @7.x]
[code: app/bundles/EmailBundle/Tests/Controller/AjaxControllerFunctionalTest.php:79-89 @7.x].

```php
public function testSegmentSendReachesEachContact(): void
{
    // arrange: a Segment with 2 contacts and a Segment Email (helpers in the source test)
    $this->em->flush();
    $this->em->clear();

    $this->setCsrfHeader();                                     // XHR POST under /s/ needs the CSRF header
    $this->client->xmlHttpRequest(Request::METHOD_POST, '/s/ajax?action=email:sendBatch', ['id' => $emailId, 'pending' => 2]);
    self::assertResponseIsSuccessful();

    $message = self::getMailerMessagesByToAddress('contact-0@example.com')[0];   // MauticMessage
    $body    = quoted_printable_decode($message->getBody()->bodyToString());
    $this->assertStringContainsString('expected text', $body);
}

public function testTestEmailIsSentSynchronously(): void
{
    $this->client->request(Request::METHOD_POST, '/s/ajax?action=email:sendTestEmail');
    self::assertResponseIsSuccessful();

    $this->assertQueuedEmailCount(0);
    $this->assertEmailCount(1);
    $this->assertInstanceOf(\Symfony\Component\Mime\Email::class, self::getMailerMessage());
}
```
Which count to use: `assertQueuedEmailCount()` for sends routed through the `email` Messenger transport (Segment and
Campaign emails); `assertEmailCount()` for synchronous sends, or after setting
`$this->configParams['messenger_dsn_email'] = 'sync://'` [code: app/bundles/EmailBundle/Tests/Controller/Api/SMimeFunctionalTest.php:22-29, 105-113 @7.x]
[code: app/bundles/LeadBundle/Tests/Controller/LeadControllerTest.php:660 @7.x].

## 7. Config override per test or per method

Adapted from `DeleteWebhookLogsCommandTest.php:18-25`, `LeadApiControllerFunctionalTest.php:37-55` and
`WebhookFunctionalTest.php:28-49`
[code: app/bundles/WebhookBundle/Tests/Functional/Command/DeleteWebhookLogsCommandTest.php:18-25 @7.x]
[code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:28-49 @7.x].

```php
protected function setUp(): void
{
    // Per class:
    $this->configParams['mailer_from_email'] = 'admin@example.com';
    // Per method:
    $this->configParams['clean_webhook_logs_in_background'] = 'testRemoveLogUsingCleanUpJob' === $this->name();
    // Replace a service before boot (as LeadApiControllerFunctionalTest does with the session):
    // self::getContainer()->set('session', $customSession);

    parent::setUp();   // values are serialised into MAUTIC_CONFIG_PARAMETERS here
}
```
To change config inside a test you must re-boot the kernel, which is only allowed with rollback off:

```php
protected $useCleanupRollback = false;

protected function setUp(): void
{
    parent::setUp();
    $this->setUpSymfony($this->configParams + ['queue_mode' => WebhookModel::COMMAND_PROCESS]);
}
```
[code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:118-128 @7.x].

## 8. Custom-field test needing a full reset

Adapted from `app/bundles/LeadBundle/Tests/Model/LeadModelFunctionalTest.php:29, 186-268`
[code: app/bundles/LeadBundle/Tests/Model/LeadModelFunctionalTest.php:29, 186-268 @7.x].
Creating a field runs `ALTER TABLE`, which commits the open transaction, so rollback cannot clean up.

```php
<?php

declare(strict_types=1);

namespace Mautic\ExampleBundle\Tests\Model;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\LeadBundle\Entity\Lead;
use Mautic\LeadBundle\Entity\LeadField;
use Mautic\LeadBundle\Model\FieldModel;
use Mautic\LeadBundle\Model\LeadModel;
use PHPUnit\Framework\Attributes\DataProvider;

final class SelectFieldFunctionalTest extends MauticMysqlTestCase
{
    protected $useCleanupRollback = false;   // DDL inside the test; DB is reset from reset_db-*.sql afterwards

    #[DataProvider('valueProvider')]
    public function testSelectFieldStoresOnlyAllowedValues(string $input, ?string $expected): void
    {
        $field = new LeadField();
        $field->setName('Select Field')->setAlias('select_field')->setType('select')->setObject('lead')
            ->setProperties(['list' => [['label' => 'Male', 'value' => 'male'], ['label' => 'Female', 'value' => 'female']]]);
        self::getContainer()->get(FieldModel::class)->saveEntity($field);   // column created synchronously in tests
        $this->em->clear();

        $leadModel = self::getContainer()->get(LeadModel::class);
        $lead      = new Lead();
        $lead->setEmail('x@example.com')->addUpdatedField('select_field', $input);
        $leadModel->saveEntity($lead);
        $this->em->clear();

        $this->assertSame($expected, $leadModel->getEntity($lead->getId())->getFieldValue('select_field'));
    }

    /**
     * @return \Iterator<string, array{string, ?string}>
     */
    public static function valueProvider(): \Iterator
    {
        yield 'allowed' => ['female', 'female'];
        yield 'disallowed' => ['gibberish', null];
    }
}
```
The column is created during `saveEntity()` because tests set `create_custom_field_in_background` to false
[code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x]. `tearDown()` drops added columns and
resets the database [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:73, 89-91, 310-324 @7.x].
`LeadFieldTestTrait` has helpers for field tests [code: app/bundles/LeadBundle/Tests/Traits/LeadFieldTestTrait.php @7.x].

## 9. Choosing a recipe for a change

| Change | Recipe | Assert |
|---|---|---|
| Controller action or UI form | 1 | status, DOM/flash, DB row after `em->clear()` |
| REST endpoint or serializer | 2 | status code, JSON keys and values, DB row, 403 without permission |
| Console command | 3 | exit code, `getDisplay()` text, DB state |
| Event listener with persistence | 4 | side effect row (audit log, stat, queue) |
| Pure service, validator, helper | 5 | return value; mocks only for services |
| Anything that sends email | 6 | queued vs sent count, recipient, body content |
| Behaviour behind a config flag | 7 | both values of the flag, one method each |
| Custom fields, schema, full-text | 8 | value persisted and read back |
