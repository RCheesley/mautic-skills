# Mautic testing: behaviour and conventions (7.x)

Numbered rules an agent must follow, and the behaviours of the test infrastructure it must rely on. Every item is
cited. Code paths are relative to the Mautic repo root at 7.2.1 (commit 419a08a9b35).

Contents
1. Running tests
2. Functional test lifecycle (MauticMysqlTestCase)
3. Test container: mail, HTTP, CSRF, API, commands, logs
4. Test-writing conventions
5. Codeception end-to-end suite
6. Static analysis, coding standard, Rector
7. CI: what runs on a pull request
8. Writing a good regression test, per kind of change
9. Testing Mautic as a black box (QA agents)

## 1. Running tests

1.1 Run PHP, composer, console and PHPUnit inside DDEV: `ddev exec php bin/phpunit ...`, `ddev exec php bin/console ...`, `ddev composer ...` [code: AGENTS.md @7.x].
1.2 Pass `-c app/phpunit.xml.dist` or use `composer test`; only that file sets `KERNEL_CLASS=AppTestKernel`, `IS_PHPUNIT`, `MAUTIC_ENV=test`, `APP_ENV=test`, `APP_DEBUG=0`, `date.timezone=UTC` [code: app/phpunit.xml.dist:65-76 @7.x].
1.3 `composer test` is `bin/phpunit -d memory_limit=2G --bootstrap vendor/autoload.php --configuration app/phpunit.xml.dist`; extra arguments are appended, so `ddev exec composer test app/bundles/X/Tests/YTest.php` runs one file [code: composer.json:166-214 @7.x] [code: .github/prompts/write-test.prompt.md:41 @7.x].
1.4 Single method: add `--filter testMethodName`; a whole bundle: pass its `Tests` directory [code: AGENTS.md @7.x].
1.5 Suites: "Project Test Suite" (`bundles/*Bundle/Tests` minus smoke tests), "Container smoke tests" (`ControllerSmokeTest`, `CommandSmokeTest`, `EventSubscriberSmokeTest`), "Plugin tests" (`plugins/*Bundle/Tests`), "Middleware tests", "Static analysis rule tests" (`utils/rector/tests`, `utils/phpstan/tests`) [code: app/phpunit.xml.dist:40-64 @7.x].
1.6 Only files ending in `Test.php` are discovered [code: app/phpunit.xml.dist:42 @7.x].
1.7 `failOnRisky` and `failOnWarning` are true, and deprecations, errors, notices and warnings are displayed per test [code: app/phpunit.xml.dist:3-19 @7.x].
1.8 Every run prints `using db prefix "test_"`; the `DbPrefix` extension loads `.env*` and defines `MAUTIC_TABLE_PREFIX` from `MAUTIC_DB_PREFIX` (default `test_`) [code: app/bundles/CoreBundle/Test/Extensions/DbPrefix/DbPrefix.php:21-27 @7.x].
1.9 `.env.test` points at `127.0.0.1:3306`, database `mautictest`, user `root`, empty password; `.env.test.local` overrides it, and under DDEV sets `DB_HOST=db`, `DB_USER=db`, `DB_PASSWD=db`, `DB_NAME=test` [code: .env.test @7.x] [code: .ddev/.env.test.local @7.x] [code: app/bundles/CoreBundle/Test/EnvLoader.php:14-20 @7.x].
1.10 Slow-test reporting is off unless `MAUTIC_TEST_LOG_SLOW_TESTS` is truthy; the threshold is `MAUTIC_TEST_SLOW_TESTS_THRESHOLD` (default 2 s) [code: app/bundles/CoreBundle/Test/Extensions/SlowTest/SlowTest.php:39-43, 95-106 @7.x].
1.11 There is no SQLite test case; functional tests need MySQL or MariaDB [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:35-64 @7.x].
1.12 `mautic:phpunit:config <n>` can split the suite into N shards, but CI does not use it [code: app/bundles/CoreBundle/Test/PhpUnitConfigCommand.php:36-78 @7.x] [code: .github/workflows/tests.yml:111-121 @7.x].

## 2. Functional test lifecycle (MauticMysqlTestCase)

2.1 `setUp()` adds `db_driver => pdo_mysql` to `$configParams`, boots the kernel through `AbstractMauticTestCase::setUp()`, backs up `config/local.php`, prepares the database if needed, logs in the `admin` user, and, when `$useCleanupRollback` is true, calls `beforeBeginTransaction()` and opens a transaction [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:35-64 @7.x].
2.2 Kernel boot: `MAUTIC_CONFIG_PARAMETERS` is set to the JSON of `$configParams`, the client is created (with basic-auth server params only if `$authenticateApi`), reboot is disabled, redirects are followed, and `$em`, `$connection`, `$router` are set [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:111-128 @7.x].
2.3 `ParameterLoader` merges `MAUTIC_CONFIG_PARAMETERS` over local parameters [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:212-215 @7.x].
2.4 Default `$configParams`: `api_enabled true`, `api_enable_basic_auth true`, `create_custom_field_in_background false`, `site_url https://localhost`, `mailer_dsn null://null`, `messenger_dsn_email in-memory://default`, `messenger_dsn_hit sync://`, `messenger_dsn_failed in-memory://default` [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x].
2.5 First-run database preparation: drop and create the database, `doctrine:schema:create`, sync migration metadata, mark all migrations as executed, load `LeadFieldData`, `RoleData`, `LoadRoleData`, `LoadUserData`, then `mysqldump` to `fresh_db-<db>.sql` and build `reset_db-<db>.sql`; a `prepared-<db>.sql` marker records readiness. All three live in the kernel cache dir (`var/cache/test`) [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-261, 375-383 @7.x].
2.6 Without `proc_open` the database is installed directly instead of from dumps [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-237 @7.x].
2.7 `applyMigrations()` only runs `doctrine:migrations:version --add --all`; no migration code runs in functional tests [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:157-165 @7.x].
2.8 `tearDown()` is `final`. It resets the timezone to UTC, restores `config/local.php`, drops custom lead/company field columns added by the test, calls `beforeTearDown()`, throws `LogicException('You omitted invoking parent::setUp()...')` if `setUp()` was skipped, then rolls back [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:69-97 @7.x].
2.9 Rollback check: before rolling back, a sentinel row is inserted into `<prefix>ip_addresses`; if rollback was disabled, no transaction was active, custom fields were reset, or the sentinel row survived, the database is reset from `reset_db-*.sql` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:69-97, 365-368 @7.x].
2.10 Override hooks: `beforeBeginTransaction()`, `beforeTearDown()`, `afterRollback()` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:99-118 @7.x].
2.11 `$useCleanupRollback` defaults to true. Set it to false when a query alters the schema (DDL commits the open transaction) or full-text search must see the rows [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:20-30 @7.x].
2.12 Calling `setUpSymfony()` again while rollback is on throws `LogicException('You cannot re-create the client when a transaction rollback for cleanup is enabled...')` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:118-128 @7.x].
2.13 `AbstractMauticTestCase::tearDown()` calls `restore_exception_handler()` because kernel boot leaks a handler that PHPUnit 11.5 would flag [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:101-109 @7.x].
2.14 `truncateTables()` disables foreign-key checks around `TRUNCATE`; `resetAutoincrement()` is discouraged by its own docblock; do not assume fixed IDs [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:131-161 @7.x].
2.15 `generateTypeSafePayload()` turns booleans into `'1'`/`'0'` for BrowserKit form payloads [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:392-406 @7.x].
2.16 For raw SQL build table names from `$this->em->getClassMetadata(X::class)->getTableName()` or the `mautic.db_table_prefix` parameter [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:370-373 @7.x] [code: .agents/skills/mautic-dev/SKILL.md @7.x].
2.17 Users: `admin` (role Administrators, admin) and `sales` (role Sales Team: `user:profile editname`, `lead:leads full`), password `Maut1cR0cks!` for both; emails `admin@yoursite.com`, `sales@yoursite.com` [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php:24-49 @7.x] [code: app/bundles/UserBundle/DataFixtures/ORM/LoadRoleData.php:24-52 @7.x].
2.18 Optional fixtures load with `$this->loadFixtures([X::class])` or `loadFixtureFiles([...])`; `$append` defaults to true to avoid purges [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:141-155 @7.x].
2.19 Most tests build entities inline or through traits (`CreateTestEntitiesTrait`, `UserEntityTrait`, `ApiTestUserTrait`, `FixtureHelper`) rather than fixture classes [code: app/bundles/CoreBundle/Tests/Functional/CreateTestEntitiesTrait.php @7.x] [code: app/bundles/CampaignBundle/Tests/Functional/Fixtures/FixtureHelper.php @7.x].
2.20 Test config sets Twig `strict_variables: true`, a mock file session `MOCKSESSION`, CSRF on, profiler collection off, `mautic.batch_sleep_time = 0`, `mautic.security.disableUpdates = true`, a fixed secret key, and imports `config/config_override.php` if present [code: app/config/config_test.php:23-131 @7.x].

## 3. Test container: mail, HTTP, CSRF, API, commands, logs

3.1 `AppTestKernel` wires `test.service_container` to `TestContainer`, so `static::getContainer()->set($id, $service)` can replace private services [code: app/AppTestKernel.php:11-53 @7.x] [code: app/bundles/CoreBundle/Test/Container/TestContainer.php:17-29 @7.x].
3.2 Mail: the mailer DSN is `null://null` and the `email` transport is `in-memory://default`, so nothing is delivered [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:57-58 @7.x].
3.3 Use `assertQueuedEmailCount(n)` for sends routed through Messenger (Segment and Campaign emails) and `assertEmailCount(n)` for synchronous sends (test emails) [code: app/bundles/LeadBundle/Tests/Controller/LeadControllerTest.php:660 @7.x] [code: app/bundles/EmailBundle/Tests/Controller/AjaxControllerFunctionalTest.php:79-89 @7.x].
3.4 Read messages with `self::getMailerMessage($i)`, `self::getMailerMessages()` or `self::getMailerMessagesByToAddress('x@y')`; they return `MauticMessage` objects [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:70-93 @7.x] [code: app/bundles/EmailBundle/Tests/Controller/EmailSendFunctionalTest.php:47-60 @7.x].
3.5 Set `$this->configParams['messenger_dsn_email'] = 'sync://'` to make queued sends immediate, then assert with `assertEmailCount()` [code: app/bundles/EmailBundle/Tests/Controller/Api/SMimeFunctionalTest.php:22-29, 105-113 @7.x].
3.6 Symfony HttpClient is replaced by `MockHttpClient`, which answers every request with 200 and an empty body [code: app/config/config_test.php:150-154 @7.x] [code: .agents/skills/mautic-dev/SKILL.md @7.x].
3.7 Guzzle clients use a public `GuzzleHttp\Handler\MockHandler`; `use ClientMockTrait;` and queue responses or callables with `$this->getClientMockHandler()->append(...)`. The method is `private` inside the trait [code: app/bundles/CoreBundle/Test/Guzzle/ClientMockTrait.php @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:274-290 @7.x].
3.8 CSRF on AJAX: `RequestSubscriber` validates `X-CSRF-Token` against intention `mautic_ajax_post` only for XHR `POST` requests whose path starts with `/s/`; on failure it returns HTTP 200 with JSON `{"flashes": ...}` [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:34-63 @7.x].
3.9 `createAjaxHeaders()` returns `HTTP_Content-Type`, `HTTP_X-Requested-With: XMLHttpRequest` and a valid `HTTP_X-CSRF-Token`; `setCsrfHeader($intention)` sets the header on the client; `getCsrfToken($intention)` returns a token for direct form POSTs [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:172-195 @7.x] [code: app/bundles/DashboardBundle/Tests/Controller/DashboardControllerFunctionalTest.php:245 @7.x].
3.10 `InMemoryTokenStorage` replaces the CSRF token storage under PHPUnit, so one token stays valid across requests [code: app/config/config_test.php:139-141 @7.x] [code: app/bundles/CoreBundle/Test/Session/InMemoryTokenStorage.php:11-16 @7.x].
3.11 API auth: `protected bool $authenticateApi = true;` sends `PHP_AUTH_USER=admin` and `PHP_AUTH_PW=Maut1cR0cks!`; the test firewall enables `http_basic` with plain md5 hashing [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:47-50, 117 @7.x] [code: app/config/security_test.php:5-26 @7.x].
3.12 Alternatively rely on the admin session from `setUp()`, or create a user with `ApiTestUserTrait::createApiUserWithPermissions()` / `UserEntityTrait::createUserWithPermission()` and log it in [code: app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php:32-66 @7.x] [code: app/bundles/LeadBundle/Tests/Controller/Api/ApiTestUserTrait.php @7.x].
3.13 JSON bodies: pass `CONTENT_TYPE` and `HTTP_ACCEPT` server params and `json_encode($data)` as raw content; there is no `jsonRequest()` helper in use [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:198-240 @7.x].
3.14 `testSymfonyCommand($name, $params, $command = null)` builds an `Application` on the kernel, adds `--bypass-locking => true` when the command defines it, executes through `CommandTester` and returns it [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:200-223 @7.x].
3.15 `loginUser(User $user)` logs into firewall `mautic`; `logoutUser()` GETs `/s/logout` and clears cookies [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:130-139 @7.x].
3.16 Audit log assertions: query `AuditLog` by `bundle`, `object`, `objectId`, `action` and read `getDetails()` (`[old, new]` pairs) [code: app/bundles/LeadBundle/Tests/Functional/EventListener/CompanySubscriberFunctionalTest.php:38-44 @7.x] [code: app/bundles/LeadBundle/Tests/Controller/LeadControllerTest.php:406-418 @7.x].
3.17 Flash assertions: after `$this->client->submit($form)` read `//div[@id='flashes']//span`; AJAX responses carry flashes in the JSON `flashes` key [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:170-186 @7.x].
3.18 Logs: `LoggerTrait` swaps `monolog.logger.mautic` handlers for a `TestHandler`; it overrides `setUp()`/`beforeTearDown()`, so call the trait's methods if you redeclare them [code: app/bundles/CoreBundle/Tests/Traits/LoggerTrait.php @7.x].
3.19 Raw DBAL fetches return strings for numbers because test config sets `PDO::ATTR_STRINGIFY_FETCHES => true` [code: app/config/config_test.php:62-77 @7.x].
3.20 Tests that define `MAUTIC_INTEGRATION_SYNC_IN_PROGRESS` or boot a second kernel must carry `#[RunInSeparateProcess]` (usually with `#[PreserveGlobalState(false)]`), or the `SeparateProcess` extension throws at suite end [code: app/bundles/CoreBundle/Test/Extensions/SeparateProcess/SeparateProcess.php:29-31, 48-87 @7.x] [code: app/bundles/PointBundle/Tests/Functional/EmailTriggerTest.php:19-20 @7.x].
3.21 `ReflectionHelper::setValue()`/`setStaticValue()` set private properties up the class hierarchy [code: app/bundles/CoreBundle/Test/ReflectionHelper.php:15-36 @7.x].

## 4. Test-writing conventions

4.1 Place tests in `<Bundle>/Tests/` (plugins: `plugins/<Bundle>/Tests/`), mirroring the class under test (`Controller`, `Model`, `EventListener`, `Command`, `Functional`, `Unit`); functional tests are often suffixed `FunctionalTest` [code: app/phpunit.xml.dist:40-64 @7.x].
4.2 Every test class is `final` and declares `strict_types=1`; shared bases are `abstract` and named `Abstract...TestCase` (PHPStan `AbstractClassNameMustBeAbstractRule`) [code: .github/prompts/write-test.prompt.md:19 @7.x] [code: utils/phpstan/src/Rule/AbstractClassNameMustBeAbstractRule.php @7.x].
4.3 Methods are `public function testDescriptiveName(): void` [code: .github/prompts/write-test.prompt.md:17-26 @7.x].
4.4 Data providers use `#[DataProvider('name')]` with a `public static` provider returning `\Iterator` or `array`, typed in a docblock; `@dataProvider` annotations do not appear in the tree [code: app/bundles/CoreBundle/Tests/Unit/Form/Validator/Constraints/CircularDependencyValidatorTest.php:154-166 @7.x] [code: app/bundles/LeadBundle/Tests/Model/LeadModelFunctionalTest.php:189, 263-268 @7.x].
4.5 Only one `#[Group(...)]` exists (`time-sensitive`); CI never selects tests by group [code: .github/workflows/tests.yml:118-120 @7.x].
4.6 Prefer the real entry point: route, then command, then event dispatch, then service [code: .github/prompts/write-test.prompt.md:17-18 @7.x].
4.7 Do not mock entities or events; mock only services. CodeRabbit flags tests that only assert mocks were called, and order- or time-dependent tests [code: .github/prompts/write-test.prompt.md:17-18 @7.x] [code: .coderabbit.yaml @7.x].
4.8 Use `assertResponseIsSuccessful()` for 2xx, `assertResponseStatusCodeSame()` for specific codes, `assertSame` over `assertEquals` [code: .github/prompts/write-test.prompt.md:24 @7.x] [code: utils/rector/src/ @7.x] [code: rector.php:10-25 @7.x].
4.9 Fetch services as `static::getContainer()->get(Foo::class)`; a string id fails `NoContainerGetRule` in tests [code: utils/phpstan/src/Rule/NoContainerGetRule.php:42-47 @7.x] [code: phpstan.neon:47-57 @7.x].
4.10 Type properties, parameters and returns in tests too; PHPStan, Rector and php-cs-fixer all cover test code [code: .github/prompts/write-test.prompt.md:20 @7.x] [code: phpstan.neon:21-35 @7.x].
4.11 Keep the test minimal and do not change production code when asked only for a test [code: .github/prompts/write-test.prompt.md:29-31 @7.x].
4.12 Do not depend on wall-clock time; tests run in UTC [code: app/phpunit.xml.dist:75 @7.x] [code: .coderabbit.yaml @7.x].
4.13 Call `$this->em->clear()` before asserting on data written by a command or another request, so you read fresh rows [code: .github/prompts/write-test.prompt.md:33-37 @7.x].
4.14 Extend the container smoke tests' `SKIPPED_SERVICE_IDS` only with a justification [code: app/bundles/CoreBundle/Tests/Functional/DependencyInjection/AbstractContainerSmokeTestCase.php @7.x].
4.15 Extract helpers for repeated setup; near-duplicate methods fail SonarCloud's duplication gate [code: .agents/skills/mautic-dev/SKILL.md @7.x].

## 5. Codeception end-to-end suite

5.1 The suite uses Codeception with Selenium WebDriver to check that pull requests do not break features [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html].
5.2 Run it with `ddev composer run e2e-test` (`APP_ENV=test bin/codecept run acceptance`); it only runs inside DDEV because WebDriver points at `https://web:443` and host `selenium-chrome:4444` [code: composer.json:166-214 @7.x] [code: tests/acceptance.suite.yml @7.x].
5.3 `DbHelper::_beforeSuite()` re-imports `tests/_data/dump.sql` if it exists, otherwise drops and creates the database, runs `doctrine:schema:create` and `doctrine:fixtures:load`, and dumps it [code: tests/_support/Helper/DbHelper.php:15-100 @7.x].
5.4 `EnvHelper` writes `APP_ENV=test` / `APP_DEBUG=1` to `.env.local` for the run and restores the original afterwards [code: tests/_support/Helper/EnvHelper.php:16-83 @7.x].
5.5 Write `final class XCest` in `tests/acceptance/`; log in with `$I->login()` in `_before`; keep selectors in `tests/_support/Page/Acceptance/*Page.php` and flows in `tests/_support/Step/Acceptance/*Step.php` [code: tests/acceptance/ContactManagementCest.php:13-80 @7.x] [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#acceptance-tests-structure].
5.6 `AcceptanceTester::TIMEOUT` is 30 s; `login()` defaults to `admin` / `Maut1cR0cks!` and reuses a session snapshot; `ensureNotificationAppears($text)` waits for `#flashes .alert` [code: tests/_support/AcceptanceTester.php:27-68 @7.x].
5.7 Database assertions use the `test_` prefix, for example `$I->seeInDatabase('test_leads', [...])` [code: tests/acceptance/ContactManagementCest.php:13-80 @7.x].
5.8 Watch the browser via noVNC at `https://mautic.ddev.site:7900/` (password `secret`); failures write screenshots and HTML reports to `tests/_output` [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#view-tests-in-the-browser].
5.9 Scaffold with `bin/codecept generate:cest|generate:pageobject|generate:stepobject acceptance <Name>`; add `--steps` or `-vvv` when running [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#writing-tests].
5.10 Codeception `functional` and `unit` suites define only empty helpers; there are no such tests [code: tests/functional.suite.yml @7.x].

## 6. Static analysis, coding standard, Rector

6.1 PHPStan: level 6, `tmpDir var/phpstan-cache`, `treatPhpDocTypesAsCertain: false`, paths `app/bundles`, `app/migrations`, `plugins`, `utils` [code: phpstan.neon:5-35 @7.x].
6.2 Type-coverage floors: return 88.3 %, param 75.7 %, property 71.6 %, constant 3, declare 73; lowering them fails the run [code: phpstan.neon:14-20 @7.x].
6.3 The Doctrine and Symfony extensions need `tests/object-manager.php` and `var/cache/test/AppKernelTestDebugContainer.xml`; `composer phpstan` builds the latter first [code: phpstan.neon:249-254 @7.x] [code: composer.json:166-214 @7.x].
6.4 Custom rules (messages in references/code-map.md): no `MAUTIC_TABLE_PREFIX` in tests; `#[AsCommand]` on commands; `#[\Attribute]` on constraints; `#[Required]` methods named `autowire<ClassName>()`; no string `getModel()` in controllers; no `getRepository(Entity::class)` in repositories or on the entity manager; no `$container->get()`; typed non-nullable constructor services; interfaces over concrete classes; controller actions return `Response`; no services in `Config/config.php` [code: phpstan.neon:257-277 @7.x] [code: utils/phpstan/src/Rule/ @7.x].
6.5 Suppress with an `ignoreErrors` entry carrying `identifier` and `path`, or regenerate the baseline (`composer phpstan-baseline`); unmatched ignores fail the run [code: phpstan.neon:8, 42-239 @7.x] [code: composer.json:184 @7.x].
6.6 After adding a plugin entity, clear `var/cache/prod` and `var/phpstan-cache` if PHPStan reports it "not found in the chain configured namespaces" [code: .agents/skills/mautic-dev/SKILL.md @7.x].
6.7 Coding standard: php-cs-fixer `@Symfony` plus ordered imports, short arrays, no unused imports, explicit nullable types for `= null`, aligned `=>`/`=` allowed [code: .php-cs-fixer.php:26-57 @7.x].
6.8 `composer cs` is a php-cs-fixer dry run; `composer fixcs` runs php-cs-fixer and ECS with fixes; the git pre-commit hook (installed by `composer githooks`) fixes staged files [code: composer.json:166-214 @7.x] [code: build/hooks/pre-commit:17-20 @7.x].
6.9 Rector: sets `deadCode`, `typeDeclarations`, `phpunitCodeQuality`, `phpunitMockToStub`, `phpunitNarrowAsserts`, `privatization`, `codeQuality`, PHP sets from composer (8.2); `reportUnusedSkips()` is on [code: rector.php:10-25, 55-122 @7.x].
6.10 `ddev composer rector` rewrites files; commit the result. CI runs `bin/rector --dry-run` [code: composer.json:166-214 @7.x] [code: .github/workflows/tests.yml:250-253 @7.x].

## 7. CI: what runs on a pull request

7.1 `tests.yml` runs on every pull request, on pushes to `[0-9].*` branches, on merge groups and daily [code: .github/workflows/tests.yml:3-19 @7.x].
7.2 PHPUnit matrix: PHP 8.2 + MySQL 8.4, PHP 8.2 + MariaDB 10.11, PHP 8.5 + MySQL 9.2, PHP 8.5 + MariaDB 11.4, plus a SimpleSAMLphp service for SAML tests; the whole suite runs in one process per cell after `rm -rf var/cache` [code: .github/workflows/tests.yml:22-68, 111-121 @7.x].
7.3 CI runs with `zend.assertions=1` [code: .github/workflows/tests.yml:86-92, 111-121 @7.x].
7.4 Coverage is collected only on push or schedule (PHP 8.2 + MariaDB 10.11), never on pull requests; Codecov's patch target is 0 % [code: .github/workflows/tests.yml:36-44, 117-130 @7.x] [code: codecov.yml:7-13 @7.x].
7.5 The `misc` job runs PHPStan, php-cs-fixer on changed `*.php` files only, Rector dry-run, `lint:twig app plugins`, the scaffold-file diff, a `mautic/recommended-project` composer install check, and `composer validate` [code: .github/workflows/tests.yml:181-316 @7.x].
7.6 The `e2e-tests` job runs Codeception inside DDEV and uploads `tests/_output` on failure [code: .github/workflows/tests.yml:155-179 @7.x].
7.7 `api-library-tests.yml` installs the PR under Apache (PHP 8.3) and runs the `mautic/api-library` PHPUnit suite against it [code: .github/workflows/api-library-tests.yml:20-125 @7.x].
7.8 `e2e-tests.yml` runs the e2e suite 10 times when `tests/**` changes [code: .github/workflows/e2e-tests.yml:25-28 @7.x].
7.9 Applying `check-coverage` or `ready-to-commit` triggers a full coverage run [code: .github/workflows/coverage-check.yml:7-88 @7.x].
7.10 PHPUnit logs under `var/logs/*` are uploaded as artifacts on every run; read them when CI fails and local passes [code: .github/workflows/tests.yml:148-153 @7.x].

## 8. Writing a good regression test, per kind of change

A regression test must fail before the fix and pass after it, use the entry point the user hit, and assert an observable
outcome [code: .github/prompts/write-test.prompt.md:17-31 @7.x] [code: .coderabbit.yaml @7.x]. Skeletons are in
recipes.md.

8.1 Controller or form bug: request the route as the affected user (create one with only the needed permission), submit the form, assert status, flash text and the persisted row after `em->clear()`; add a 403 case for permission bugs [code: app/bundles/CampaignBundle/Tests/Controller/Api/CampaignApiControllerFunctionalTest.php:490-505 @7.x].
8.2 API bug: call the endpoint with the exact payload from the report; assert status code, the JSON keys and values, and the database row [code: app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php:685-710 @7.x].
8.3 AJAX endpoint: send `createAjaxHeaders()`; remember a missing token yields 200 with `flashes`, so assert on content, not only status [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:34-46 @7.x].
8.4 Command or cron behaviour: persist the state, `em->clear()`, run `testSymfonyCommand()`, assert exit code, output text and the resulting rows [code: app/bundles/WebhookBundle/Tests/Functional/Command/DeleteWebhookLogsCommandTest.php:64-85 @7.x].
8.5 Event listener: trigger the model or route that dispatches the event and assert the listener's side effect; use a unit test only for pure logic [code: app/bundles/LeadBundle/Tests/Functional/EventListener/CompanySubscriberFunctionalTest.php:18-45 @7.x].
8.6 Email content or sending: assert queued versus sent counts, recipients and decoded body; use `sync://` when you need delivered messages [code: app/bundles/EmailBundle/Tests/Controller/EmailSendFunctionalTest.php:40-60 @7.x].
8.7 Config-dependent behaviour: one method per value of the flag, switched with `$this->name()` in `setUp()` [code: app/bundles/WebhookBundle/Tests/Functional/Command/DeleteWebhookLogsCommandTest.php:18-25 @7.x].
8.8 Custom fields, schema changes or full-text search: `$useCleanupRollback = false` [code: app/bundles/LeadBundle/Tests/Model/LeadModelFunctionalTest.php:29 @7.x].
8.9 Outbound HTTP (webhooks, integrations): queue responses in the Guzzle `MockHandler` and assert on the captured request (path, headers, body) [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:274-290 @7.x].
8.10 Migration: functional tests do not run it; execute it manually and check that `doctrine:schema:update --dump-sql` prints nothing [code: .agents/skills/mautic-dev/SKILL.md @7.x].
8.11 New entity or column: delete `var/cache` before running tests [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-213 @7.x].
8.12 UI-only change (JavaScript, layout): add or extend a Codeception Cest and run it locally; expect the 10x flakiness run [code: AGENTS.md @7.x] [code: .github/workflows/e2e-tests.yml:25-28 @7.x].
8.13 Area-specific base helpers and representative tests are in each area skill's `references/test-patterns.md`.

## 9. Testing Mautic as a black box (QA agents)

9.1 Instance: DDEV, `ddev start`, `https://mautic.ddev.site`, `admin` / `Maut1cR0cks!`; DDEV's setup script installs Mautic, warms the cache and reloads plugins [code: .ddev/mautic-setup.sh:3-35 @7.x] [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html].
9.2 Credentials and switches: DDEV's `local.php` sets `api_enabled true`, `api_enable_basic_auth true`, `mailer_dsn smtp://localhost:1025` [code: .ddev/local.config.php.dist @7.x].
9.3 API: call `/api/...` with HTTP basic auth; endpoints and payloads are in mautic-rest-api.
9.4 Cron: run `mautic:segments:update`, `mautic:campaigns:update`, `mautic:campaigns:trigger` and `messenger:consume email --time-limit=...` yourself through `ddev exec bin/console`; without them nothing scheduled happens [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html] [kb: https://kb.mautic.org/article/getting-started-with-mautic.html]. Queue and cron detail is in mautic-cron-and-queues.
9.5 Email: a real Segment send to tagged test Contacts is the reliable test; "Send example" does not rewrite links, shows tokens as placeholders and does not track; the same Email is sent once per Contact, so duplicate it to resend [kb: https://kb.mautic.org/article/how-to-test-emails-in-mautic.html] [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html].
9.6 Sample data: `ddev exec bin/console doctrine:fixtures:load` loads fixtures and purges the database [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html].
9.7 Dev mode with the debug toolbar comes from `APP_ENV=dev` (and `APP_DEBUG=1`) in `.env.local`; DDEV ships `.ddev/.env.local.dist` for this. `index_dev.php` was removed in 5.0 [PR #12206] [code: .env:15-16 @7.x] [code: .ddev/.env.local.dist @7.x]. Discrepancy: the KB DDEV article still says to use `index_dev.php` [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html].
9.8 Testing a PR: check out the branch, reproduce on the base branch first, retest on the PR, and record the PR template's "Steps to test" outcome; each PR needs two testers [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] [code: .github/PULL_REQUEST_TEMPLATE.md:1-36 @7.x].
9.9 Oracle: for each step, find the matching numbered item in the area skill's `references/behaviour.md` (mautic-contacts, mautic-segments, mautic-campaigns, mautic-emails, mautic-forms, mautic-pages-and-tracking, mautic-points-and-stages, mautic-webhooks, mautic-rest-api, ...) and report pass or fail against it, citing the item number.
9.10 Logs: check Mautic's logs in `var/logs/` first, then the web server error log, when an action fails [kb: https://kb.mautic.org/article/troubleshooting-the-site-is-currently-offline-due-to-encountering-an-error-in-mautic.html].
