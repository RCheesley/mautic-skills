# Testing contacts (Mautic 7.x)

## Base classes

- Functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`. It logs in the `admin` user (from `$clientServer['PHP_AUTH_USER']`) and wraps each test in a transaction that is rolled back. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:35-64 @7.x]
- Set `protected $useCleanupRollback = false;` when a test changes the schema (creating a custom field runs `ALTER TABLE`, which commits the open transaction) or relies on full-text search. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:22-30 @7.x]
- Override configuration by writing to `$this->configParams` before `parent::setUp()` (for example `api_enabled`, `create_custom_field_in_background`, `contact_unique_identifiers_operator`). [code: app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php:38-55 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52 @7.x]
- `$this->client` is a Symfony test client authenticated with Basic auth for API calls. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:47-50 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:117 @7.x]
- Unit tests extend PHPUnit `TestCase` and mock repositories and models. [code: app/bundles/LeadBundle/Tests/Model/LeadModelTest.php @7.x]
- In 8.x, PHPUnit 13 is used, many classes are `final` (use the `dg/bypass-finals` bootstrap), and `Request`/`InputBag`/`Router` must not be mocked. See version-notes.md.

## Helpers and fixtures

| Helper | Use | Source |
|---|---|---|
| `TestEntityCreationTrait` | `createContact()`, `createCompany()`, `attachContactToCompany()`, `updateCompanyName()`, `softDeleteCompany()` | [code: app/bundles/LeadBundle/Tests/TestEntityCreationTrait.php:9-56 @7.x] |
| `StandardImportTestHelper` | import mocks (extends `CommonMocks`) | [code: app/bundles/LeadBundle/Tests/StandardImportTestHelper.php @7.x] |
| `LeadFieldTestTrait` | create custom fields in tests | [code: app/bundles/LeadBundle/Tests/Traits/LeadFieldTestTrait.php @7.x] |
| `ApiTestUserTrait`, `CreateTestEntitiesTrait` | API users and entities | [code: app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php:34-35 @7.x] |
| `Tests/Fixtures`, `Tests/DataFixtures` | CSV and data fixtures | [code: app/bundles/LeadBundle/Tests/Fixtures @7.x] |

Get services from the container by class: `self::getContainer()->get(LeadModel::class)`. [code: app/bundles/LeadBundle/Tests/Deduplicate/ContactMergerFunctionalTest.php:21-27 @7.x]

## Representative tests to copy from

| Test | Covers |
|---|---|
| `app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php` | create-or-update by unique identifier, merged ids, batch limits and status codes, DNC add/remove, own-list permissions |
| `app/bundles/LeadBundle/Tests/Deduplicate/ContactMergerTest.php` | every merge rule (fields, timestamps, owners, points, tags, companies) |
| `app/bundles/LeadBundle/Tests/Deduplicate/ContactMergerFunctionalTest.php` | merge-record resolution, points accuracy, company links |
| `app/bundles/LeadBundle/Tests/Command/DeduplicateCommandFunctionalTest.php` | AND/OR unique operator |
| `app/bundles/LeadBundle/Tests/Model/LeadModelTest.php`, `LeadModelFunctionalTest.php` | duplicates, import rules, IP lookup, manipulator, primary company, select validation, single company |
| `app/bundles/LeadBundle/Tests/Tracker/ContactTrackerTest.php`, `ContactTrackerFunctionalTest.php`, `Tests/Helper/ContactRequestHelperTest.php` | tracking identity |
| `app/bundles/LeadBundle/Tests/Model/ImportModelTest.php`, `Tests/Functional/Command/ImportCommandTest.php` | import |
| `app/bundles/LeadBundle/Tests/Field/CustomFieldColumnTest.php`, `Tests/Controller/Api/FieldApiControllerFunctionalTest.php` | custom field schema |
| `app/bundles/LeadBundle/Tests/EventListener/DoNotContactSubscriberTest.php`, `Tests/Functional/Entity/DoNotContactFunctionalTest.php` | DNC |
| `app/bundles/LeadBundle/Tests/Controller/Api/CompanyApiControllerFunctionalTest.php`, `Tests/Model/BatchCompanyContactAssignmentModelTest.php`, `Tests/Helper/IdentifyCompanyHelperTest.php` | companies |
| `app/bundles/LeadBundle/Tests/Model/SetFrequencyRulesFunctionalTest.php` | frequency rules |
| `app/bundles/LeadBundle/Tests/Functional/ContactExportLimitFunctionalTest.php` | export limit |

[code: app/bundles/LeadBundle/Tests @7.x] Codeception coverage under the repository-root `tests/` was not inspected. [unverified]

## What a good regression test asserts

- The observable outcome in the database or API response, not only the absence of an exception: for example `doNotContact[0].reason === 3` after a DNC add, and the `lead.donotcontact` activity event. [code: app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php:1232-1272 @7.x]
- For merges: the surviving id, the merged id resolving to the winner, and each field/points/tag/company rule. [code: app/bundles/LeadBundle/Tests/Deduplicate/ContactMergerFunctionalTest.php:19-75 @7.x]
- For API create: 201 versus 200 depending on a unique-identifier match, and that no duplicate row was created.
- For identification: `date_identified` set once, `LEAD_IDENTIFIED` dispatched, and the webhook `_new` versus `_update` choice.
- For custom fields: column presence (`SHOW COLUMNS`) and the background-mode 202 path; disable rollback.

## Skeleton: API functional test

```php
<?php

declare(strict_types=1);

namespace Mautic\LeadBundle\Tests\Controller\Api;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

final class ContactUpsertFunctionalTest extends MauticMysqlTestCase
{
    protected function setUp(): void
    {
        $this->configParams['api_enabled'] = true;
        parent::setUp();
    }

    public function testNewEndpointUpdatesExistingContactByEmail(): void
    {
        $this->client->request(Request::METHOD_POST, '/api/contacts/new', ['email' => 'a@example.com', 'firstname' => 'A']);
        $this->assertResponseStatusCodeSame(Response::HTTP_CREATED);
        $id = json_decode($this->client->getResponse()->getContent(), true)['contact']['id'];

        $this->client->request(Request::METHOD_POST, '/api/contacts/new', ['email' => 'a@example.com', 'lastname' => 'B']);
        $this->assertResponseStatusCodeSame(Response::HTTP_OK);
        $contact = json_decode($this->client->getResponse()->getContent(), true)['contact'];

        $this->assertSame($id, $contact['id']);
        $this->assertSame('A', $contact['fields']['all']['firstname']); // blank not overwritten on POST
    }
}
```

The 201-then-200 behaviour follows B11.1 and the blank rule follows B11.4 in behaviour.md. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:338-347 @7.x] [code: app/bundles/LeadBundle/Controller/Api/CustomFieldsApiControllerTrait.php:175-210 @7.x]

## Skeleton: model functional test

```php
final class MergeKeepsOwnerFunctionalTest extends MauticMysqlTestCase
{
    public function testWinnerKeepsItsOwner(): void
    {
        $model  = self::getContainer()->get(\Mautic\LeadBundle\Model\LeadModel::class);
        $merger = self::getContainer()->get(\Mautic\LeadBundle\Deduplicate\ContactMerger::class);
        // create $winner and $loser with Lead setters, save both with $model->saveEntity()
        // $merger->merge($winner, $loser);
        // assert $model->getEntity($loserId)->getId() === $winnerId
    }
}
```
