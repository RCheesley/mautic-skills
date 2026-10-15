# Mautic architecture - test patterns

How to test framework-level behaviour (base model, repository search, controllers, AJAX, CSRF, listeners, DI).
The general harness (test DB, fixtures, Codeception, CI) is in mautic-testing.

## Running tests
- `composer test` runs `bin/phpunit -d memory_limit=2G --bootstrap vendor/autoload.php --configuration app/phpunit.xml.dist`; append a path to run one file, for example `ddev exec composer test app/bundles/CoreBundle/Tests/Unit/Model/FormModelTest.php`. [code: composer.json:166-214 @7.x]
- Under DDEV the PHPUnit database is `test` (from `.ddev/.env.test.local`). [code: .ddev/.env.test.local @7.x]
- PHPUnit ^11.5 (11.5.56 locked) on 7.x; PHPUnit 13 and `dg/bypass-finals` on 8.x. [code: composer.json:28-54 @7.x] [PR #17004] [PR #17366]

## Base classes
| Class | Use for | Notes |
|---|---|---|
| `PHPUnit\Framework\TestCase` | Pure unit tests (`Tests/Unit/`) | Mock the model's eight constructor dependencies [code: app/bundles/CoreBundle/Tests/Unit/Model/FormModelTest.php:22-75 @7.x] |
| `Mautic\CoreBundle\Test\AbstractMauticTestCase` | Kernel-booted tests without DB isolation | `$this->client`, `loginUser(User)`, `logoutUser()`, `loadFixtures()`, `applyMigrations()`, `setCsrfHeader($intention = 'mautic_ajax_post')`, `getCsrfToken()`, `createAjaxHeaders()`, `testSymfonyCommand()` [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:111-200 @7.x] |
| `Mautic\CoreBundle\Test\MauticMysqlTestCase` | Functional tests against MySQL | Installs schema once, logs in `admin`, rolls back each test when `$useCleanupRollback = true` (set false for schema-changing or fulltext tests), `$this->em`, `$this->connection`, `truncateTables()`, `resetAutoincrement()` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:24-152 @7.x] |
| `AbstractContainerSmokeTestCase` | Container wiring | Asserts every command/subscriber/controller can be built [code: app/bundles/CoreBundle/Tests/Functional/DependencyInjection/ @7.x] |

`TestPass` replaces Guzzle and Symfony HttpClient with mocks in the test env, so no real outbound HTTP happens. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/TestPass.php:18-31 @7.x]

## Representative tests to copy
| Test | Shows |
|---|---|
| `app/bundles/CoreBundle/Tests/Unit/Model/FormModelTest.php` | Anonymous `FormModel` subclass recording hook order for `saveEntities()`; asserts 2 flushes for 30 entities [code: app/bundles/CoreBundle/Tests/Unit/Model/FormModelTest.php:43-107 @7.x] |
| `app/bundles/CoreBundle/Tests/Functional/Entity/CommonRepositoryTest.php` | `is:mine`, `is:published` against real repositories [code: app/bundles/CoreBundle/Tests/Functional/Entity/CommonRepositoryTest.php:13-35 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/Entity/CommonRepositoryTest.php` | Order-by sanitisation, `in` CSV parsing, parameter names with a mocked QueryBuilder [code: app/bundles/CoreBundle/Tests/Unit/Entity/CommonRepositoryTest.php:61-360 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/Helper/SearchStringHelperTest.php` | Negated groups, missing values [code: app/bundles/CoreBundle/Tests/Unit/Helper/SearchStringHelperTest.php:11-29 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/EventListener/RequestSubscriberTest.php` | CSRF matrix: regular POST, AJAX GET, public route, missing/invalid/valid token [code: app/bundles/CoreBundle/Tests/Unit/EventListener/RequestSubscriberTest.php:59-123 @7.x] |
| `app/bundles/CoreBundle/Tests/Functional/Controller/AjaxControllerTest.php` | `xmlHttpRequest()` to `/s/ajax?action=globalSearch`, admin vs non-admin results [code: app/bundles/CoreBundle/Tests/Functional/Controller/AjaxControllerTest.php:50-467 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/EventListener/EnvironmentSubscriberTest.php` | Locale/timezone from session [code: app/bundles/CoreBundle/Tests/Unit/EventListener/EnvironmentSubscriberTest.php:41-86 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/Helper/DateTimeHelperTest.php` | Mutating vs cloning helpers [code: app/bundles/CoreBundle/Tests/Unit/Helper/DateTimeHelperTest.php:131-355 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/ErrorHandler/ErrorHandlerTest.php` | Offline template rendering [code: app/bundles/CoreBundle/Tests/Unit/ErrorHandler/ErrorHandlerTest.php:47 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/Monolog/Handler/FileLogHandlerTest.php` | Log level selection [code: app/bundles/CoreBundle/Tests/Unit/Monolog/Handler/FileLogHandlerTest.php:26-56 @7.x] |
| `app/bundles/CoreBundle/Tests/Translation/TranslatorTest.php` | EN fallback on bad syntax [code: app/bundles/CoreBundle/Tests/Translation/TranslatorTest.php:14 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/DependencyInjection/Builder/` | config.php parsing with GoodConfig/BadConfig fixtures [code: app/bundles/CoreBundle/Tests/Unit/DependencyInjection/Builder/Metadata/ConfigMetadataTest.php @7.x] |
| `app/bundles/CoreBundle/Tests/Functional/Security/Permissions/CorePermissionsTest.php` | Virtual permissions with a non-admin user [code: app/bundles/CoreBundle/Tests/Functional/Security/Permissions/CorePermissionsTest.php:27-40 @7.x] |

## What a good regression test asserts here
- Model changes: the exact hook sequence and flush count, or the event your bundle maps a hook to, plus the audit-log row written by your subscriber. [code: app/bundles/CoreBundle/Tests/Unit/Model/FormModelTest.php:43-107 @7.x]
- Repository/search changes: the ids returned for a concrete search string, including negation and a missing value. [code: app/bundles/CoreBundle/Tests/Functional/Entity/CommonRepositoryTest.php:13-35 @7.x]
- Controller changes: status code, redirect target or JSON keys (`newContent`, `flashes`, `closeModal`), and lock fields after GET/Apply/Save. [code: app/bundles/CoreBundle/Controller/CommonController.php:218-278 @7.x]
- AJAX/CSRF: an XHR POST without token yields HTTP 200 with `flashes` and no side effect; with `setCsrfHeader()` the action runs. [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:34-63 @7.x]
- New subscribers/commands: the smoke tests pass (they build every subscriber). [code: app/bundles/CoreBundle/Tests/Functional/DependencyInjection/ @7.x]

## Skeletons (adapt names; based on the tests above)

### Unit: hook order of a custom FormModel
```php
final class MyModelHookTest extends \PHPUnit\Framework\TestCase
{
    public function testSaveEntityFiresPreAndPostSave(): void
    {
        $em = $this->createMock(\Doctrine\ORM\EntityManager::class);
        $em->method('getRepository')->willReturn($this->createStub(\Mautic\FormBundle\Entity\FormRepository::class));
        $userHelper = $this->createMock(\Mautic\CoreBundle\Helper\UserHelper::class);
        $userHelper->method('getUser')->willReturn(new \Mautic\UserBundle\Entity\User());

        $model = new class($em, $this->createStub(\Mautic\CoreBundle\Security\Permissions\CorePermissions::class),
            $this->createStub(\Symfony\Component\EventDispatcher\EventDispatcherInterface::class),
            $this->createStub(\Symfony\Component\Routing\Generator\UrlGeneratorInterface::class),
            $this->createStub(\Mautic\CoreBundle\Translation\Translator::class), $userHelper,
            $this->createStub(\Psr\Log\LoggerInterface::class),
            $this->createStub(\Mautic\CoreBundle\Helper\CoreParametersHelper::class)) extends \Mautic\CoreBundle\Model\FormModel {
            public array $actions = [];
            protected function dispatchEvent($action, &$entity, $isNew = false, ?\Symfony\Contracts\EventDispatcher\Event $event = null): ?\Symfony\Contracts\EventDispatcher\Event
            {
                $this->actions[] = $action;
                return $event;
            }
        };

        $model->saveEntity(new \Mautic\LeadBundle\Entity\Lead());
        $this->assertSame(['pre_save', 'post_save'], $model->actions);
    }
}
```
Constructor argument order and the `dispatchEvent()` signature are taken from the existing test. [code: app/bundles/CoreBundle/Tests/Unit/Model/FormModelTest.php:60-75 @7.x]

### Functional: AJAX POST needs the CSRF header
```php
final class MyAjaxActionTest extends \Mautic\CoreBundle\Test\MauticMysqlTestCase
{
    public function testWithoutTokenIsRejected(): void
    {
        $this->client->xmlHttpRequest('POST', '/s/ajax', ['action' => 'togglePublishStatus', 'model' => 'email', 'id' => 1]);
        $this->assertSame(200, $this->client->getResponse()->getStatusCode());
        $this->assertArrayHasKey('flashes', json_decode($this->client->getResponse()->getContent(), true));
    }

    public function testWithTokenRuns(): void
    {
        $this->setCsrfHeader();
        $this->client->xmlHttpRequest('POST', '/s/ajax', ['action' => 'togglePublishStatus', 'model' => 'email', 'id' => 1]);
        // assert on the entity state or the JSON keys your action returns
    }
}
```
[code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:172-198 @7.x] [code: app/bundles/CoreBundle/Controller/AjaxController.php:219-299 @7.x]

### Functional: search command on a repository
```php
final class MySearchTest extends \Mautic\CoreBundle\Test\MauticMysqlTestCase
{
    public function testIsPublished(): void
    {
        // persist one published and one unpublished entity with $this->em, then:
        $items = $this->em->getRepository(MyEntity::class)->getEntities(['filter' => ['string' => 'is:published']]);
        $this->assertCount(1, $items); // Paginator: count() is the total
    }
}
```
[code: app/bundles/CoreBundle/Entity/CommonRepository.php:389-405 @7.x] [code: app/bundles/CoreBundle/Tests/Functional/Entity/CommonRepositoryTest.php:13-35 @7.x]

## Traps when testing this area
- `CorePermissions` memoises per string; build a fresh client/container when switching users within a test. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:210-213 @7.x]
- `mautic:update:apply` calls `exit()`, so it cannot be run in-process. [code: app/bundles/CoreBundle/Command/ApplyUpdatesCommand.php:99 @7.x]
- In 8.x many core classes are `final`; mocking them needs `DG\BypassFinals`, and `Request`/`InputBag`/`Router` must not be mocked. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#final-classes] [PR #17392]
