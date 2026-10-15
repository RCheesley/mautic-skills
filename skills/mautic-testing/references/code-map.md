# Mautic testing: code map (7.x)

Contents
1. Composer packages and scripts
2. PHPUnit configuration and extensions
3. Test kernel, config and environment files
4. Base classes and helpers (`app/bundles/CoreBundle/Test/`)
5. Helper traits and fixtures
6. Representative tests to copy
7. Codeception
8. PHPStan rules
9. Rector and coding standard
10. CI workflows
11. Agent guidance files shipped in core

## 1. Composer packages and scripts

Dev tooling is in the root `composer.json` `require-dev`; runtime dependencies in `app/composer.json` [code: composer.json:28-54 @7.x] [code: app/composer.json:15-105 @7.x].

| Package | Constraint | Locked |
|---|---|---|
| phpunit/phpunit | ^11.5 | 11.5.56 |
| codeception/codeception | ^5.1 | 5.3.6 |
| codeception/module-webdriver | ^4.0 | 4.0.5 |
| liip/functional-test-bundle / test-fixtures-bundle | ^4.3 / ^3.5 | 4.16.0 / 3.9.0 |
| phpstan/phpstan | ^2.2.6 | 2.3.1 |
| phpstan/phpstan-doctrine, -symfony, -phpunit, -deprecation-rules | ^2.0 | |
| symplify/phpstan-rules | ^14.10 | 14.10.0 |
| tomasvotruba/type-coverage | ^2.2.1 | 2.2.1 |
| rector/rector | dev-main | dev-main |
| friendsofphp/php-cs-fixer | ^v3.95.11 | v3.95.27 |
| symplify/easy-coding-standard | ^13.2.17 | 13.3.2 |
| symfony/browser-kit, dom-crawler, phpunit-bridge | ~7.4.0 | |
[code: composer.json:28-54 @7.x]

Composer `bin-dir` is `bin`, so tools are `bin/phpunit`, `bin/phpstan`, `bin/rector`, `bin/ecs`, `bin/php-cs-fixer`, `bin/codecept`; only `bin/console` is in git [code: composer.json:215-230 @7.x] [code: .gitignore:62-64 @7.x].

Scripts [code: composer.json:166-214 @7.x]:

| Script | Runs |
|---|---|
| `test` | `bin/phpunit -d memory_limit=2G --bootstrap vendor/autoload.php --configuration app/phpunit.xml.dist` |
| `e2e-test` | `APP_ENV=test bin/codecept run acceptance` |
| `phpstan` | warms `var/cache/test/AppKernelTestDebugContainer.xml` if missing, then `php -d memory_limit=5G bin/phpstan analyse` |
| `phpstan-baseline` | `composer phpstan -- --generate-baseline phpstan-baseline.neon` |
| `cs` | `bin/php-cs-fixer fix --config=.php-cs-fixer.php -v --dry-run --diff` |
| `fixcs` | `bin/php-cs-fixer fix -v` then `bin/ecs --fix` |
| `rector` | `bin/rector process --ansi` |
| `githooks` | copies `build/hooks/pre-commit` and `post-checkout` into `.git/hooks/` |

`extra.patches` patches `twig/twig` to make `IntegrationTestCase` data providers static for PHPUnit 11 [code: composer.json:254-258 @7.x].

## 2. PHPUnit configuration and extensions

`app/phpunit.xml.dist` [code: app/phpunit.xml.dist:3-82 @7.x]:
- Attributes: schema 10.5, bootstrap `../vendor/autoload.php`, `failOnRisky`, `failOnWarning`, display details for deprecations/errors/notices/warnings, cache `../var/cache/phpunit`, no process isolation, no static backup.
- Coverage source: `bundles`, `../plugins`, `middlewares`, excluding `Config`, `DataFixtures`, `Tests`, `Translations`, `Views`, `middlewares/Tests`, `bundles/CoreBundle/Test`.
- Suites: Project Test Suite, Container smoke tests, Plugin tests, Middleware tests, Static analysis rule tests.
- `<php>`: `SYMFONY_DEPRECATIONS_HELPER=weak`, `MAXMIND_LICENSE_KEY=""`, `KERNEL_CLASS=AppTestKernel`, `IS_PHPUNIT=true`, `MAUTIC_ENV=test`, `KERNEL_DIR=app`, `APP_DEBUG=0`, `APP_ENV=test`, `error_reporting=E_ALL`, `date.timezone=UTC`.
- Extensions: `SeparateProcess`, `DbPrefix`, `SlowTest`; a `Cleanup` extension line is commented out.

| Extension | File | Effect |
|---|---|---|
| DbPrefix | `app/bundles/CoreBundle/Test/Extensions/DbPrefix/DbPrefix.php:21-27` | loads `.env*`, defines `MAUTIC_TABLE_PREFIX` (default `test_`) |
| SeparateProcess | `.../SeparateProcess/SeparateProcess.php:29-31, 48-87` | fails suite if `MAUTIC_INTEGRATION_SYNC_IN_PROGRESS` was defined outside a separate process |
| SlowTest | `.../SlowTest/SlowTest.php:39-43, 95-106` | prints slow test classes when `MAUTIC_TEST_LOG_SLOW_TESTS` is set |
[code: app/bundles/CoreBundle/Test/Extensions/ @7.x]

## 3. Test kernel, config and environment files

| File | Content |
|---|---|
| `app/AppTestKernel.php:11-53` | extends `AppKernel`, `isInstalled()` true, `TEST_CACHE_DIR`/`TEST_LOG_DIR`, `TestContainer` as `test.service_container` |
| `app/config/config_test.php:18-154` | prefix/env constants, Twig strict, mock session, test DB from env with `ATTR_STRINGIFY_FETCHES`, monolog to `var/logs/test.php`, Liip `keep_database_and_schema`, `config/config_override.php`, fixed secret, `batch_sleep_time 0`, `InMemoryTokenStorage`, Guzzle `MockHandler`, `MockHttpClient` |
| `app/config/security_test.php:5-26` | `http_basic` on `main` firewall, md5 hashing |
| `.env.test` | `DB_HOST=127.0.0.1`, `DB_NAME=mautictest`, `DB_USER=root`, `MAUTIC_DB_PREFIX=test_`, `MAUTIC_ADMIN_PASSWORD=mautic` (unused by tests), `SAML_HOST`/`SAML_PORT` |
| `.ddev/.env.test.local` | `DB_HOST=db`, `DB_USER=db`, `DB_PASSWD=db`, `DB_NAME=test` |
| `app/bundles/CoreBundle/Loader/ParameterLoader.php:212-219` | merges `MAUTIC_CONFIG_PARAMETERS`; `db_driver` fixed to `pdo_mysql` |
[code: app/AppTestKernel.php:11-53 @7.x] [code: app/config/config_test.php:18-154 @7.x] [code: app/config/security_test.php:5-26 @7.x] [code: .env.test @7.x]

## 4. Base classes and helpers (`app/bundles/CoreBundle/Test/`)

`AbstractMauticTestCase` (extends Symfony `WebTestCase`) [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:32-223 @7.x]:

| Member | Lines | Purpose |
|---|---|---|
| `$em`, `$connection`, `$client`, `$router`, `$databaseTool` | 32-65 | ready after `setUp()` |
| `$configParams` | 52-61 | config overrides (defaults listed in behaviour.md 2.4) |
| `$clientOptions`, `$clientServer`, `$authenticateApi` | 32-65 | client construction; basic auth when `$authenticateApi` |
| `getMailerMessage()`, `getMailerMessagesByToAddress()` | 70-93 | static mailer readers |
| `setUp()`, `setUpSymfony()`, `tearDown()` | 95-128 | kernel boot, exception-handler restore |
| `loginUser()`, `logoutUser()` | 130-139 | firewall `mautic`; `/s/logout` |
| `loadFixtures()`, `loadFixtureFiles()` | 141-155 | Liip database tool, append by default |
| `applyMigrations()` | 157-165 | marks all migrations executed |
| `setCsrfHeader()`, `getCsrfToken()`, `createAjaxHeaders()` | 172-195 | CSRF and AJAX headers |
| `testSymfonyCommand()` | 200-223 | `CommandTester` with auto `--bypass-locking` |

`MauticMysqlTestCase` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:20-406 @7.x]:

| Member | Lines | Purpose |
|---|---|---|
| `$useCleanupRollback` | 20-30 | transaction rollback (true) vs full reset (false) |
| `setUp()` | 35-64 | prepare DB, log in admin, begin transaction |
| `tearDown()` (final) | 69-97 | restore config, reset custom fields, rollback or reset |
| `beforeBeginTransaction()`, `beforeTearDown()`, `afterRollback()` | 99-118 | hooks |
| `setUpSymfony()` | 118-128 | refuses re-boot while rollback is on |
| `resetAutoincrement()`, `truncateTables()` | 131-161 | discouraged helpers |
| database preparation and dumps | 194-261 | `fresh_db-*`, `reset_db-*` |
| `resetCustomFields()` | 310-324 | drops added field columns |
| `config/local.php` backup | 326-337 | |
| `wasRollbackSuccessful()` | 365-368 | sentinel row check |
| table prefix getter | 370-373 | `mautic.db_table_prefix` |
| `prepared-*.sql` marker | 375-383 | |
| `generateTypeSafePayload()` | 392-406 | booleans to `'1'`/`'0'` |

Other support classes [code: app/bundles/CoreBundle/Test/ @7.x]:
- `Guzzle/ClientMockTrait` (`getClientMockHandler()`), `Guzzle/ClientFactory::stub(MockHandler)`.
- `Doctrine/RepositoryConfiguratorTrait::configureRepository()`, `MockedConnectionTrait`, `DBALMocker` (older).
- `ReflectionHelper::setValue()` / `setStaticValue()` (`ReflectionHelper.php:15-36`).
- `Session/FixedMockFileSessionStorage`, `Session/InMemoryTokenStorage`.
- `DoctrineExtensions/TablePrefix` (prefixes tables and renames indexes; removed on 8.x, see version-notes.md).
- `Container/TestContainer`, `EnvLoader`, `PhpUnitConfigCommand` (`mautic:phpunit:config`, unused by CI), `FunctionalWarmupTest`.
- Real tests living under `Test/` rather than `Tests/`: `Event/TokenReplacementEventTest.php`, `EventListener/MaintenanceSubscriberTest.php`, `Service/AbTestSettingsServiceTest.php`.

## 5. Helper traits and fixtures

Fixtures loaded into every fresh test database: `InstallBundle/InstallFixtures/ORM/LeadFieldData`, `RoleData`, `UserBundle/DataFixtures/ORM/LoadRoleData`, `LoadUserData` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:223-229 @7.x].

Optional ORM fixtures: `LeadBundle/DataFixtures/ORM/` (`LoadLeadData`, `LoadCompanyData`, `LoadCategoryData`, `LoadLeadListData`, `LoadCategorizedLeadListData`), `EmailBundle/DataFixtures/ORM/LoadEmailData`, Asset/Campaign/Form/Page `DataFixtures`, test-only `LeadBundle/Tests/DataFixtures/ORM/` (`LoadClickData`, `LoadDncData`, `LoadPageHitData`, `LoadSegmentsData`, `LoadTagData`) [code: app/bundles/LeadBundle/DataFixtures/ORM/ @7.x] [code: app/bundles/LeadBundle/Tests/DataFixtures/ORM/ @7.x].

Helper traits and classes:

| Helper | Path | Provides |
|---|---|---|
| CreateTestEntitiesTrait | `app/bundles/CoreBundle/Tests/Functional/CreateTestEntitiesTrait.php` | `createLead`, `createCampaign`, `createEvent`, ... |
| UserEntityTrait | `app/bundles/CoreBundle/Tests/Functional/UserEntityTrait.php` | `createUserWithPermission`, `createRole`, `createUser`, `createPermission`, `loginOtherUser` |
| ApiTestUserTrait | `app/bundles/LeadBundle/Tests/Controller/Api/ApiTestUserTrait.php` | `createApiUserWithPermissions`, `authenticateApiUser` |
| FixtureHelper | `app/bundles/CampaignBundle/Tests/Functional/Fixtures/FixtureHelper.php` | campaign fixtures (final readonly, takes the EM) |
| CampaignAuditLogTrait | `app/bundles/CampaignBundle/Tests/CampaignAuditLogTrait.php` | `saveAuditLogs` |
| LoggerTrait | `app/bundles/CoreBundle/Tests/Traits/LoggerTrait.php` | `TestHandler` on `monolog.logger.mautic` |
| ControllerTrait | `app/bundles/CoreBundle/Tests/Traits/ControllerTrait.php` | `getControllerColumnTests` (list ordering) |
| LeadFieldTestTrait | `app/bundles/LeadBundle/Tests/Traits/LeadFieldTestTrait.php` | custom-field helpers |
| Others | `FormBundle/Tests/FormTestHelperTrait`, `SmsBundle/Tests/SmsTestHelperTrait`, `PointBundle/Tests/Functional/TriggerTrait`, `NotificationBundle/Tests/NotificationTrait`, `AssetBundle/Tests/RemoteFileServerTrait`, `CoreBundle/Tests/Twig/TwigIntegrationTestTrait`, `UserBundle/Tests/Traits/CreateEntityTrait`, `UserBundle/Tests/Controller/LoginUserWithSamlTrait` | area helpers |
[code: app/bundles/CoreBundle/Tests/Functional/ @7.x]

Counts at 7.x (`419a08a9b35`): 1296 `*Test.php` files, 445 extend `MauticMysqlTestCase`, 16 extend `AbstractMauticTestCase` directly, 224 use `#[DataProvider]`, 87 set `$useCleanupRollback` false, 0 non-final concrete test classes [code: app/bundles/ @7.x].

## 6. Representative tests to copy

| Test | Shows |
|---|---|
| `app/bundles/EmailBundle/Tests/Functional/EmailClickTrackingTest.php` | minimal public-route functional test with `logoutUser()` |
| `app/bundles/WebhookBundle/Tests/Functional/Command/DeleteWebhookLogsCommandTest.php` | command test, per-method `configParams` |
| `app/bundles/CampaignBundle/Tests/Controller/Api/CampaignApiControllerFunctionalTest.php` | API, uploads, `assertQueuedEmailCount`, `UserEntityTrait`, rollback off |
| `app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php` | JSON-LD POST to `/api/v2` |
| `app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php` | API v1, disabled-API case, stateless session guard |
| `app/bundles/LeadBundle/Tests/Controller/LeadControllerTest.php` | fixtures, crawler forms, audit log, queued email |
| `app/bundles/LeadBundle/Tests/Functional/EventListener/CompanySubscriberFunctionalTest.php` | listener side effects via the model |
| `app/bundles/EmailBundle/Tests/Controller/AjaxControllerFunctionalTest.php` | AJAX action, `assertEmailCount`, `getMailerMessage()` |
| `app/bundles/EmailBundle/Tests/Controller/EmailSendFunctionalTest.php` | `setCsrfHeader`, `xmlHttpRequest`, `getMailerMessagesByToAddress` |
| `app/bundles/EmailBundle/Tests/Controller/Api/SMimeFunctionalTest.php` | `messenger_dsn_email = sync://` |
| `app/bundles/DashboardBundle/Tests/Controller/DashboardControllerFunctionalTest.php` | `createAjaxHeaders()` |
| `app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php` | Guzzle `ClientMockTrait`, `authenticateApi`, kernel re-boot |
| `app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php` | flash DOM assertion |
| `app/bundles/LeadBundle/Tests/Model/LeadModelFunctionalTest.php` | custom fields with full reset |
| `app/bundles/PointBundle/Tests/Functional/EmailTriggerTest.php`, `app/bundles/InstallBundle/Tests/Functional/InstallWorkflowTest.php` | separate-process attributes |
| `app/bundles/CoreBundle/Tests/Unit/Form/Validator/Constraints/CircularDependencyValidatorTest.php` | unit test with `#[DataProvider]` |
| `app/bundles/EmailBundle/Tests/EventListener/SegmentSubscriberTest.php` | unit subscriber test with mocks |
| `app/bundles/ReportBundle/Tests/Entity/SchedulerRepositoryTest.php` | repository unit test with `RepositoryConfiguratorTrait` |
| `app/bundles/CoreBundle/Tests/Functional/DependencyInjection/AbstractContainerSmokeTestCase.php` (+ `ControllerSmokeTest`, `CommandSmokeTest`, `EventSubscriberSmokeTest`) | every controller, command and subscriber can be built |
| `tests/acceptance/ContactManagementCest.php` + `tests/_support/Step/Acceptance/ContactStep.php` | Codeception pattern |
[code: app/bundles/ @7.x]

## 7. Codeception

| File | Content |
|---|---|
| `codeception.yml` | paths `tests`, `_output`, `_data`, `_support`, `_envs`; `RunFailed`; params from `.env.test.local` |
| `tests/acceptance.suite.yml` | `AcceptanceTester`; modules Asserts, `\Helper\EnvHelper`, `\Helper\DbHelper`, WebDriver (`https://web:443`, `selenium-chrome:4444`, Chrome), Db (dump `tests/_data/dump.sql`, populate) |
| `tests/_support/AcceptanceTester.php:27-68` | `TIMEOUT`, `login()`, `createACategory()`, `ensureNotificationAppears()` |
| `tests/_support/Helper/DbHelper.php:15-100` | build/import the e2e DB |
| `tests/_support/Helper/EnvHelper.php:16-83` | switch `.env.local` to test mode and back |
| `tests/_support/Page/Acceptance/` | `CampaignPage`, `CategoriesPage`, `ContactPage`, `EmailsPage`, `FormPage`, `MenuPage`, `SegmentsPage`, `ThemesPage` |
| `tests/_support/Step/Acceptance/` | `CampaignStep`, `ContactStep`, `EmailStep`, `FormStep`, `MenuStep`, `SegmentStep` |
| `tests/acceptance/` | `AssetBatchDownloadCest`, `ContactManagementCest`, `DisplayTestCest`, `EmailManagementCest`, `EmailScheduleCest`, `FormActionSendToUserCest`, `GrapesJsBuilderPageCest`, `MauticScriptSplitCest`, `MenuNavigationCest`, `ThemeManagementCest` |
| `.ddev/docker-compose.selenium-chrome.yaml`, `.ddev/php/codeception.ini` | Selenium Chromium; `register_argc_argv` on, `E_DEPRECATED` hidden |
[code: codeception.yml @7.x] [code: tests/acceptance.suite.yml @7.x]

## 8. PHPStan rules

Config: `phpstan.neon` (includes `phpstan-baseline.neon` first, about 2040 entries), bootstrap `phpstan-bootstrap.php` defines `MAUTIC_ENV`, `MAUTIC_VERSION`, `MAUTIC_TABLE_PREFIX` as `''` and `MAUTIC_DB_SERVER_VERSION='8.0.0'`; `dynamicConstantNames` covers the first three [code: phpstan.neon:1-39 @7.x] [code: phpstan-bootstrap.php @7.x].

Registered custom rules in `utils/phpstan/src/Rule/`, tests in `utils/phpstan/tests/Rule/` [code: phpstan.neon:257-277 @7.x]:

| Rule | Message (abridged) |
|---|---|
| AbstractClassNameMustBeAbstractRule | Class has "Abstract" in its name but is not declared abstract |
| NoTablePrefixDefinitionInTestsRule | Test must not define the "MAUTIC_TABLE_PREFIX" const |
| AutowireMethodNameMustMatchClassRule | `#[Required]` method must be named `autowire<ClassName>()` |
| NoGetModelWithStringInControllerRule | Controller must not fetch a model by string |
| NoRequiredMethodWithConstructorInControllerRule | `#[Required]` method in a controller with its own constructor |
| CommandMustHaveAsCommandAttributeRule | Command missing `#[AsCommand]` |
| ConstraintMustHaveAttributeRule | Constraint missing `#[\Attribute]` |
| NoNullableServiceInConstructorRule | Constructor service is nullable |
| NoGetRepositoryWithEntityInRepositoryRule / NoEntityManagerGetRepositoryRule | Do not fetch a repository by entity constant |
| NoContainerGetRule | Do not fetch a service from the container; in tests: use a class constant id |
| PreferInterfaceInConstructorRule | Use the interface instead of the concrete class |
| NoPropertyToPropertyAssignRule | Property assigned from another property |
| ControllerMethodMustReturnResponseRule | Controller action must return a Response |
| NoServicesInBundleConfigRule | Config file must not define services |
| NoParentConstructorForwardingRule | Constructor forwards parameters to `parent::__construct()` |
| NoServiceJugglingRule | Service passed as an argument instead of injected |
Symplify `NoJustPropertyAssignRule` is also on. Present but not registered: `NoObjectPropertyAssignToVariableInTestsRule`, `NoServiceInMethodParameterRule`, `NoUnusedServiceAliasRule` [code: phpstan.neon:257-277 @7.x].

Project-wide `ignoreErrors` (`phpstan.neon:42-239`) tolerate, among others, `missingType.generics`, `missingType.iterableValue`, deprecated `Request::get()`, and use of Mautic's own deprecated classes [code: phpstan.neon:42-239 @7.x].

## 9. Rector and coding standard

- `rector.php`: paths `app/bundles`, `plugins`; sets listed in behaviour.md 6.9; extra rules `AssertClassToThisAssertRector`, `MergePhpstanDocTagIntoNativeRector`, `FlipNegatedTernaryInstanceofRector`, `NarrowArrayCollectionUnionReturnDocblockRector`, `Utils\Rector\UnserializeToSerializerDecodeRector`, `Utils\Rector\ModelGetRepositoryToRepositoryServiceRector`; `withTypeGuardedClasses` protects common controllers, `CommonRepository`, `AbstractPermissions`, `AbstractIntegration`, `CrmAbstractIntegration`; cache `var/cache/rector` [code: rector.php:10-122 @7.x].
- Custom rectors: `utils/rector/src/`, fixture tests in `utils/rector/tests/` (`*.php.inc`) [code: rector.php:41-53 @7.x].
- `.php-cs-fixer.php`: finder over `app/bundles`, `app/config`, `app/middlewares`, `app/migrations`, `plugins`, `tests`, `utils` and root PHP files [code: .php-cs-fixer.php:5-57 @7.x].
- `ecs.php`: sets `comments`, `docblocks`, `namespaces`, `cleanup`, `controlStructures`, `standaloneLine`, with skips; run only by `composer fixcs` [code: ecs.php:7-43 @7.x].
- Hooks: `build/hooks/pre-commit` (php-cs-fixer on staged files), `build/hooks/post-checkout` (deletes `var/cache`) [code: build/hooks/pre-commit:17-20 @7.x] [code: build/hooks/post-checkout:4-12 @7.x].

## 10. CI workflows

| Workflow | Trigger | Does |
|---|---|---|
| `tests.yml` job `phpunit` | every PR, pushes, merge group, daily | 4-cell PHP/DB matrix, full suite, coverage only on push/schedule |
| `tests.yml` job `e2e-tests` | same | Codeception in DDEV |
| `tests.yml` job `misc` | same | PHPStan, CS Fixer (changed files), Rector dry-run, Twig lint, scaffold diff, composer install check, composer validate |
| `e2e-tests.yml` | `tests/**` changes | e2e suite x10 |
| `coverage-check.yml` | labels `check-coverage` / `ready-to-commit` | coverage run and Codecov upload |
| `api-library-tests.yml` | every PR | `mautic/api-library` suite against an installed instance |
| `build-grapesjs-assets.yml` | `plugins/GrapesJsBuilderBundle/**` | npm build |
| `validate-json.yml` | changed JSON | `jq empty` |
| `release.yml` | tags | package, install and update tests |
[code: .github/workflows/tests.yml:3-316 @7.x] [code: .github/workflows/e2e-tests.yml:25-28 @7.x] [code: .github/workflows/coverage-check.yml:7-88 @7.x] [code: .github/workflows/api-library-tests.yml:20-125 @7.x]

CI support files: `.github/ci-files/.my.cnf` (`column-statistics=0` for mysqldump), `.github/ci-files/local.php`, `.github/ci-files/composer.json` [code: .github/workflows/tests.yml:94-101 @7.x].

## 11. Agent guidance files shipped in core

`AGENTS.md` (command execution rule, PR checklist, base classes), `.agents/skills/mautic-dev/SKILL.md` (functional test notes, cache hygiene, migrations), `.github/prompts/write-test.prompt.md` (test-writing rules), `.coderabbit.yaml` (review instructions for `**/Tests/**` and migrations) [code: AGENTS.md @7.x] [code: .github/prompts/write-test.prompt.md @7.x] [code: .coderabbit.yaml @7.x].
