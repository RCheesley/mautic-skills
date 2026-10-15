# Testing forms

## Base classes and tooling

| Need | Base class / tool | Example |
|---|---|---|
| End-to-end submission, API, controllers | `Mautic\CoreBundle\Test\MauticMysqlTestCase` | `app/bundles/FormBundle/Tests/Controller/SubmissionFunctionalTest.php` |
| Pure logic (entities, DisplayManager, helpers) | `PHPUnit\Framework\TestCase` | `app/bundles/FormBundle/Tests/Entity/FieldTest.php` |
| Builder Symfony form types | `Symfony\Component\Form\Test\TypeTestCase` | `app/bundles/FormBundle/Tests/Form/Type/FormFieldCheckboxGroupTypeTest.php` |
| Constraint validators | `ConstraintValidatorTestCase` | `app/bundles/FormBundle/Tests/Validator/Constraint/IsPostActionRedirectUrlValidatorTest.php` |
| Report subscriber | `AbstractReportSubscriberTestCase` | `app/bundles/FormBundle/Tests/EventListener/` |
| Browser flows | Codeception | `tests/acceptance/FormActionSendToUserCest.php`, `tests/_support/Page/Acceptance/FormPage.php` |

FormBundle has about 75 test files: 24 functional tests on `MauticMysqlTestCase`, plus unit tests and form-type tests. [code: app/bundles/FormBundle/Tests @7.x]

## Helpers and fixtures

- `Mautic\FormBundle\Tests\FormTestHelperTrait` provides these helpers:
  - `getPayLoad()` builds a published form with a `name` text field and a `button`.
  - `createFormViaApi()` POSTs to `/api/forms/new` and asserts 201.
  - `submitForm()` GETs `/form/{id}`, fills `mauticform[name]` and submits.
  - `deleteAllFormResultsTable()` drops every `form_results*` table.

  [code: app/bundles/FormBundle/Tests/FormTestHelperTrait.php:10-95 @7.x]
- `Tests/Model/FormSubmissionTrait.php` (`createFormWithCompanies`, `submitForm…`). [code: app/bundles/FormBundle/Tests/Model/FormSubmissionTrait.php @7.x]
- ORM fixtures `DataFixtures/ORM/LoadFormData.php` (creates forms and their results tables) and `LoadFormResultData.php` with CSVs. [code: app/bundles/FormBundle/DataFixtures/ORM/LoadFormData.php:66 @7.x]

## Rules specific to forms tests

- Functional tests that create forms set `protected $useCleanupRollback = false;` because creating the results table is DDL, which commits the open transaction in MySQL. That is why rollback cleanup cannot be used (inferred from the pattern). [code: app/bundles/FormBundle/Tests/Controller/SubmissionFunctionalTest.php:33 @7.x]
- Drop the results tables you create in `beforeTearDown()` (or call `deleteAllFormResultsTable()`); otherwise later tests that reuse form id 1 hit an existing `form_results_1_<alias>`. [code: app/bundles/FormBundle/Tests/Controller/SubmissionFunctionalTest.php:1557-1564 @7.x]
- Use `protected bool $authenticateApi = true;` when creating forms through `/api/forms/new`. [code: app/bundles/FormBundle/Tests/Controller/SubmissionFunctionalTest.php:35 @7.x]
- Toggle parameters before `parent::setUp()` with `$this->configParams['form_field_autofill'] = true;`. [code: app/bundles/FormBundle/Tests/Controller/AutoFillReadOnlyFormSubmissionTest.php:17-21 @7.x]
- The functional client is logged in as an admin. `ContactTracker` returns null for a logged-in user, so submissions without mapped fields get `lead_id` NULL. Map an email field when the test needs a contact. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:51-60 @7.x]
- The crawler selector is `form[id=mauticform_<formName>]`, where `<formName>` is the lowercase alphanumeric form name. [code: app/bundles/FormBundle/Tests/Controller/SubmissionFunctionalTest.php:79-80 @7.x] [code: app/bundles/FormBundle/Entity/Form.php:867-884 @7.x]
- Submitting the crawler form exercises the standard (non-JS) path, which ends in a redirect. To test the messenger or AJAX JSON, POST to `/form/submit?formId=ID&ajax=1` or to `/form/submit/ajax` yourself. [code: app/bundles/FormBundle/Controller/PublicController.php:334-426 @7.x]
- The fixtures and helpers still send `formType => 'standalone'`. It is deprecated, and 8.x ignores it. [code: app/bundles/FormBundle/Tests/FormTestHelperTrait.php:22 @7.x]

## Representative tests to copy

1. `app/bundles/FormBundle/Tests/Controller/SubmissionFunctionalTest.php` covers end-to-end submission: redirect tokens, conditional required fields, the progressive-profiling limit, campaign-source membership, company lookup, reserved-word aliases, the submission limit and cascade deletes.
2. `app/bundles/FormBundle/Tests/Model/SubmissionModelFunctionalTest.php` covers contact/company updates and the anonymous-to-existing merge (`testExistingContactWinsMergeWhenTrackedAnonymousContactSubmitsMatchingForm`).
3. `app/bundles/FormBundle/Tests/Entity/FieldTest.php` holds the `showForContact` and `showForConditionalField` matrices.
4. `app/bundles/FormBundle/Tests/Controller/Api/FormApiControllerFunctionalTest.php` and `FormApiControllerTest.php` cover API PUT/PATCH semantics.
5. `app/bundles/FormBundle/Tests/Model/FormCaptchaHoneypotFunctionalTest.php` covers honeypot rendering.
6. `app/bundles/FormBundle/Tests/EventListener/FormSubscriberTest.php` covers repost response parsing.

Also useful:
- `Tests/Functional/Model/SubmissionOwnerAndStageFunctionalTest.php` (pseudo-fields)
- `Tests/Functional/UpdateLeadFormActionFunctionalTest.php`
- `Tests/ProgressiveProfiling/DisplayManagerTest.php`
- `Tests/Model/FormModelTest.php` (ordering, syncList, auto-fill, `getAutomaticJavascript`)
- `Tests/Controller/PublicControllerFunctionalTest.php` (`generate.js` independent of tracking)
- `Tests/Command/*CommandTest.php`
- `Tests/Twig/FieldTemplateTest.php`

[code: app/bundles/FormBundle/Tests @7.x]

## Skeleton: functional submission regression test

```php
<?php

declare(strict_types=1);

namespace Mautic\FormBundle\Tests\Controller;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\FormBundle\Tests\FormTestHelperTrait;
use Mautic\LeadBundle\Entity\Lead;
use Symfony\Component\HttpFoundation\Request;

final class MyFormSubmissionFunctionalTest extends MauticMysqlTestCase
{
    use FormTestHelperTrait;

    protected $useCleanupRollback   = false; // results table DDL
    protected bool $authenticateApi = true;

    public function testMappedEmailCreatesContact(): void
    {
        $form = $this->createFormViaApi([
            'name'               => 'Regression form',
            'isPublished'        => true,
            'postAction'         => 'message',
            'postActionProperty' => 'Thanks',
            'fields'             => [
                ['label' => 'Email', 'type' => 'email', 'alias' => 'email', 'mappedObject' => 'contact', 'mappedField' => 'email'],
                ['label' => 'Submit', 'type' => 'button'],
            ],
        ]);

        $crawler = $this->client->request(Request::METHOD_GET, "/form/{$form['id']}");
        $htmlForm = $crawler->filter('form[id=mauticform_regressionform]')->form();
        $htmlForm->setValues(['mauticform[email]' => 'jane@example.com']);
        $this->client->submit($htmlForm);

        $contact = $this->em->getRepository(Lead::class)->findOneBy(['email' => 'jane@example.com']);
        self::assertNotNull($contact);
        // also assert: form_submissions row, results row, submission_count, side effects of actions
    }

    protected function beforeTearDown(): void
    {
        parent::beforeTearDown();
        $this->deleteAllFormResultsTable();
    }
}
```

The skeleton follows the pattern in [code: app/bundles/FormBundle/Tests/Controller/SubmissionFunctionalTest.php:37-97 @7.x].

## What a good regression test asserts

- The visitor-facing outcome: redirect target, message or JSON keys (`success`, `validationErrors`, `redirect`). [code: app/bundles/FormBundle/Controller/PublicController.php:334-514 @7.x]
- The `form_submissions` row and the `form_results_<id>_<alias>` row, including which columns are empty for `saveResult=false` or view-only fields. [code: app/bundles/FormBundle/Entity/SubmissionRepository.php:24-47 @7.x]
- The contact outcome: created, merged or new because of a conflict, and which field values changed or stayed. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1027-1110 @7.x]
- On validation failure, that nothing was persisted and `submission_count` did not change. [code: app/bundles/FormBundle/Model/SubmissionModel.php:322-324 @7.x]
- For builder changes, that the results table schema changed as expected (column added or dropped). [code: app/bundles/FormBundle/Tests/Model/FieldModelFunctionalTest.php @7.x]
