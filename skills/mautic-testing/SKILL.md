---
name: mautic-testing
description: "How to test Mautic (7.x, with the 8.x delta): PHPUnit suites and app/phpunit.xml.dist, the functional base classes MauticMysqlTestCase and AbstractMauticTestCase, transaction rollback vs database reset, fixtures, $configParams overrides, mailer and Messenger assertions, HTTP mocks, helpers for commands, AJAX, API requests and login, the Codeception end-to-end suite on DDEV, PHPStan (level 6, baseline), php-cs-fixer, Rector, test conventions, the GitHub Actions matrix, and black-box QA of a running instance through the UI and REST API. Use whenever a task says write a test, add a regression test, run a single test, fix a failing or flaky test, tests pass locally but fail in CI, PHPStan error, baseline, rector, cs fixer, composer test, e2e, Codeception, QA a PR, verify behaviour on a DDEV instance, or touches app/phpunit.xml.dist, app/bundles/*/Tests/, plugins/*/Tests/, tests/, phpstan.neon or .github/workflows/."
---
# Testing Mautic

## Scope
This skill covers how Mautic itself is tested and statically checked: PHPUnit (unit and functional), the Codeception
end-to-end suite, PHPStan, Rector, coding standards and the CI that runs them, plus how a QA agent tests a running
instance as a black box. Installing the DDEV environment is in mautic-dev-environment; PR process and branch policy are
in mautic-contributing; how each feature is supposed to behave (the test oracle) is in each area skill's
`references/behaviour.md`.

Terms: a Contact is a person record (code and tables say `lead`); a Segment is a contact list (code says `LeadList`,
`lists`); "functional test" means a PHPUnit test that boots the Symfony kernel against a real MySQL/MariaDB database
[code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:35-64 @7.x].

## Expected behaviour (essentials)
Running tests
- Always run PHPUnit with `-c app/phpunit.xml.dist` (or `composer test`); `KERNEL_CLASS=AppTestKernel`, `APP_ENV=test` and `MAUTIC_ENV=test` are set only there, so a bare `bin/phpunit` fails [code: app/phpunit.xml.dist:65-76 @7.x] [code: .agents/skills/mautic-dev/SKILL.md @7.x].
- Run every PHP, composer, console and PHPUnit command inside DDEV (`ddev exec ...`, `ddev composer ...`) unless told otherwise [code: AGENTS.md @7.x].
- One file: `ddev exec php bin/phpunit -c app/phpunit.xml.dist <path/to/XTest.php>`; one method: add `--filter testName`; or `ddev exec composer test <path>` because composer appends the arguments [code: AGENTS.md @7.x] [code: .github/prompts/write-test.prompt.md:41 @7.x].
- PHPUnit fails on risky tests and on warnings (`failOnRisky`, `failOnWarning`), so a deprecated annotation or a test with no assertion fails the run [code: app/phpunit.xml.dist:3-19 @7.x].
- Every database table in tests is prefixed `test_` by the `DbPrefix` PHPUnit extension; a test must never `define('MAUTIC_TABLE_PREFIX', ...)` itself (PHPStan rule) [code: app/bundles/CoreBundle/Test/Extensions/DbPrefix/DbPrefix.php:21-27 @7.x] [code: utils/phpstan/src/Rule/NoTablePrefixDefinitionInTestsRule.php @7.x].
- Under DDEV the PHPUnit database is `test`; in GitHub Actions it is `mautictest` [code: .ddev/.env.test.local @7.x] [code: .env.test @7.x].

The functional base class
- Functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`; unit tests extend `PHPUnit\Framework\TestCase`; extend `AbstractMauticTestCase` directly only when you need the kernel without a prepared database [code: AGENTS.md @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:32-65 @7.x].
- Every functional test starts logged in as `admin` inside an open database transaction; `tearDown()` rolls the transaction back [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:35-64, 69-97 @7.x].
- `tearDown()` is `final`; if you override `setUp()` and forget `parent::setUp()`, `tearDown()` throws a `LogicException` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:69-97 @7.x].
- The test schema is built from Doctrine entity metadata (`doctrine:schema:create`), not by running migrations; migrations are only marked as executed [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:157-165 @7.x] [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-237 @7.x].
- The prepared database is cached as `fresh_db-<db>.sql`, `reset_db-<db>.sql` and `prepared-<db>.sql` in `var/cache/test`; after adding an entity or column, delete `var/cache` or tests fail with "Base table or view not found" or "Unknown column" [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-261, 375-383 @7.x].
- Set `$useCleanupRollback = false` when the test runs DDL (custom fields), needs full-text search to see rows, or re-creates the client; the whole database is then reset from `reset_db-*.sql` after the test, which is slower [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:20-30, 89-91 @7.x].
- Re-creating the client (`setUpSymfony()`) while rollback is on throws a `LogicException` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:118-128 @7.x].
- Creating a custom field always forces a full reset: `resetCustomFields()` drops added columns and then the database is reset [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:73, 89-91, 310-324 @7.x].
- Override configuration by assigning `$this->configParams['key']` before `parent::setUp()`; the array is passed to the kernel as JSON in `MAUTIC_CONFIG_PARAMETERS` [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:111-114 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:212-215 @7.x].
- Default test config: API and basic auth on, `create_custom_field_in_background` off, `site_url https://localhost`, `mailer_dsn null://null`, email Messenger transport `in-memory://default`, hit transport `sync://` [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x].
- Two users exist in every functional test: `admin` (Administrators) and `sales` (Sales Team), both with password `Maut1cR0cks!` [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php:24-49 @7.x] [code: app/bundles/UserBundle/DataFixtures/ORM/LoadRoleData.php:24-52 @7.x].
- Never assume fixed IDs; avoid `truncateTables()` and `resetAutoincrement()` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:131-161 @7.x].

Test container and side effects
- No email is delivered: synchronous sends are counted by `assertEmailCount()`, Messenger-routed sends (Segment and Campaign emails) by `assertQueuedEmailCount()`; set `messenger_dsn_email` to `sync://` to make queued sends immediate [code: app/bundles/EmailBundle/Tests/Controller/AjaxControllerFunctionalTest.php:79-89 @7.x] [code: app/bundles/EmailBundle/Tests/Controller/Api/SMimeFunctionalTest.php:27, 111-112 @7.x].
- No HTTP request leaves the test: `http_client` is a `MockHttpClient` and Guzzle clients use a container `MockHandler` you fill with `ClientMockTrait::getClientMockHandler()->append(...)` [code: app/config/config_test.php:150-154 @7.x] [code: app/bundles/WebhookBundle/Tests/Functional/WebhookFunctionalTest.php:274-290 @7.x].
- CSRF is checked only on XHR `POST` requests under `/s/`; a failed check returns HTTP 200 with a JSON `flashes` error, not 403. Use `createAjaxHeaders()` or `setCsrfHeader()` [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:34-63 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:172-195 @7.x].
- One CSRF token is valid across all requests in a test because PHPUnit swaps in `InMemoryTokenStorage` [code: app/config/config_test.php:139-141 @7.x].
- API tests authenticate with HTTP basic (`$authenticateApi = true`) because the test firewall enables `http_basic` with plain md5 hashing [code: app/config/security_test.php:5-26 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:47-50, 117 @7.x].
- `testSymfonyCommand()` runs a console command through `CommandTester` and adds `--bypass-locking` automatically when the command has it [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:200-223 @7.x].
- Raw DBAL fetches return numbers as strings in tests (`PDO::ATTR_STRINGIFY_FETCHES`) [code: app/config/config_test.php:62-77 @7.x].
- A test that defines `MAUTIC_INTEGRATION_SYNC_IN_PROGRESS` without `#[RunInSeparateProcess]` makes the whole suite fail at the end [code: app/bundles/CoreBundle/Test/Extensions/SeparateProcess/SeparateProcess.php:29-31, 48-87 @7.x].

Static analysis and CI
- PHPStan runs at level 6 over `app/bundles`, `app/migrations`, `plugins` and `utils`, tests included, with type-coverage floors that new code must not lower [code: phpstan.neon:5-35 @7.x].
- `composer phpstan` first warms the test container because PHPStan reads `var/cache/test/AppKernelTestDebugContainer.xml` [code: composer.json:166-214 @7.x] [code: phpstan.neon:249-254 @7.x].
- An obsolete baseline or `ignoreErrors` entry fails PHPStan, and an unused Rector skip fails Rector (`reportUnusedSkips()`) [code: phpstan.neon:8 @7.x] [code: rector.php:56-122 @7.x].
- On every PR CI runs PHPUnit on four PHP/database cells, Codeception e2e, PHPStan, php-cs-fixer on changed files, Rector dry-run, Twig lint, scaffold diff, `composer validate` and the api-library suite; ECS is not run in CI [code: .github/workflows/tests.yml:22-32, 181-316 @7.x] [code: .github/workflows/api-library-tests.yml:20-125 @7.x].

## Where it lives
| Concern | Path |
|---|---|
| PHPUnit config and suites | `app/phpunit.xml.dist` |
| Test kernel, test config, test security | `app/AppTestKernel.php`, `app/config/config_test.php`, `app/config/security_test.php`, `.env.test` |
| Base classes | `app/bundles/CoreBundle/Test/AbstractMauticTestCase.php`, `MauticMysqlTestCase.php` |
| PHPUnit extensions | `app/bundles/CoreBundle/Test/Extensions/{DbPrefix,SeparateProcess,SlowTest}/` |
| Test helpers | `app/bundles/CoreBundle/Test/{Guzzle,Doctrine,Session,Container}/`, `CoreBundle/Tests/Functional/{CreateTestEntitiesTrait,UserEntityTrait}.php` |
| Installed fixtures | `app/bundles/InstallBundle/InstallFixtures/ORM/`, `app/bundles/UserBundle/DataFixtures/ORM/` |
| Unit/functional tests | `app/bundles/<Bundle>/Tests/`, `plugins/<Bundle>/Tests/` |
| Container smoke tests | `app/bundles/CoreBundle/Tests/Functional/DependencyInjection/` |
| Codeception e2e | `codeception.yml`, `tests/acceptance.suite.yml`, `tests/acceptance/`, `tests/_support/` |
| PHPStan | `phpstan.neon`, `phpstan-baseline.neon`, `phpstan-bootstrap.php`, `utils/phpstan/src/Rule/` |
| Rector | `rector.php`, `utils/rector/src/` |
| Coding standard | `.php-cs-fixer.php`, `ecs.php`, `build/hooks/pre-commit` |
| CI | `.github/workflows/tests.yml`, `e2e-tests.yml`, `coverage-check.yml`, `api-library-tests.yml` |
| Agent guidance shipped in core | `AGENTS.md`, `.agents/skills/mautic-dev/SKILL.md`, `.github/prompts/write-test.prompt.md`, `.coderabbit.yaml` |

Full detail, with line numbers, is in references/code-map.md [code: app/phpunit.xml.dist:40-64 @7.x].

## How to change or extend it
- Put a test in `<Bundle>/Tests/` mirroring the class under test; the file and class name end in `Test`, the class is `final` and the file declares `strict_types=1` [code: app/phpunit.xml.dist:42 @7.x] [code: .github/prompts/write-test.prompt.md:19 @7.x].
- Exercise the real entry point first: a route through `$this->client`, then a command through `testSymfonyCommand()`, then an event through the dispatcher, and only then a service [code: .github/prompts/write-test.prompt.md:17-18 @7.x].
- Do not mock objects that have no service dependencies (entities, events); build the real object [code: .github/prompts/write-test.prompt.md:17-18 @7.x].
- Use `#[DataProvider('name')]` with a `public static` provider; `@dataProvider` annotations are not used anywhere [code: app/bundles/LeadBundle/Tests/Model/LeadModelFunctionalTest.php:189, 263-268 @7.x].
- Get services with `static::getContainer()->get(Foo::class)`; string service ids fail PHPStan's `NoContainerGetRule` in tests [code: utils/phpstan/src/Rule/NoContainerGetRule.php:42-47 @7.x].
- Do not change production code when the task is only to add a test [code: .github/prompts/write-test.prompt.md:29-31 @7.x].
- Suppress a PHPStan error only with an `ignoreErrors` entry that has `identifier` and `path`, or by regenerating the baseline with `composer phpstan-baseline` [code: phpstan.neon:42-239 @7.x] [code: composer.json:184 @7.x].
- Before a PR run `ddev composer test`, `ddev composer phpstan`, `ddev composer cs`, `ddev exec bin/rector --dry-run`, and `ddev composer run e2e-test` for UI changes [code: AGENTS.md @7.x] [code: .github/workflows/tests.yml:245-264 @7.x].
- A new Doctrine migration is not exercised by functional tests; run it by hand with `doctrine:migrations:execute --up` and check `doctrine:schema:update --dump-sql` prints nothing [code: .agents/skills/mautic-dev/SKILL.md @7.x].
- A change to a scaffolded root file (`.env`, `package.json`, `importmap.php`, `bin/console` and others) must be mirrored in `app/assets/scaffold/files/`, or the CI scaffold check fails [code: app/composer.json:112-133 @7.x] [code: .github/workflows/tests.yml:265-277 @7.x].

## How to test it
Copy one of these, then adapt (skeletons in references/recipes.md):
- `app/bundles/EmailBundle/Tests/Functional/EmailClickTrackingTest.php` - minimal public-route functional test.
- `app/bundles/WebhookBundle/Tests/Functional/Command/DeleteWebhookLogsCommandTest.php` - command test with per-method `configParams`.
- `app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php` - REST API v1 test.
- `app/bundles/LeadBundle/Tests/Functional/EventListener/CompanySubscriberFunctionalTest.php` - listener side effect through the model.
- `app/bundles/EmailBundle/Tests/Controller/EmailSendFunctionalTest.php` - AJAX send plus mailer assertions.
- `app/bundles/LeadBundle/Tests/Model/LeadModelFunctionalTest.php` - custom fields with `$useCleanupRollback = false`.

A good regression test reproduces the reported input through the same entry point the user hit, fails on the old code,
and asserts the observable outcome (HTTP status and body, database row, audit log, queued email, command output) rather
than that a mock was called [code: .coderabbit.yaml @7.x] [code: .github/prompts/write-test.prompt.md:17-31 @7.x].
The per-change-type guide is in references/behaviour.md section 6.

## Testing Mautic as a black box
For QA agents that test a running instance, not the code.
- Start the DDEV instance with `ddev start`; the default login is `admin` / `Maut1cR0cks!` at `https://mautic.ddev.site` [code: .ddev/mautic-setup.sh:3-35 @7.x] [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html].
- The DDEV config enables the API and HTTP basic auth, so `curl -u admin:'Maut1cR0cks!' https://mautic.ddev.site/api/contacts` works without OAuth [code: .ddev/local.config.php.dist @7.x].
- DDEV sends mail to `smtp://localhost:1025`, the local mail catcher; read outgoing mail there, not in a real inbox [code: .ddev/local.config.php.dist @7.x].
- Nothing scheduled happens on its own: run the cron commands yourself (`mautic:segments:update`, `mautic:campaigns:update`, `mautic:campaigns:trigger`, `messenger:consume email`) with `ddev exec bin/console ...` [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html] [kb: https://kb.mautic.org/article/getting-started-with-mautic.html].
- To test email content properly, do a real Segment send to tagged test Contacts; "Send example" does not rewrite links, does not render tokens and does not track [kb: https://kb.mautic.org/article/how-to-test-emails-in-mautic.html].
- Use the area skill's `references/behaviour.md` as the oracle: each numbered item is an expected observable outcome with a citation; report a bug as "behaviour N not met" with the steps.
- Keep test data distinguishable (a tag or name prefix) and never rely on IDs from another run.
More in references/behaviour.md section 7.

## Version notes
- 7.x uses PHPUnit 11.5, PHPStan 2 at level 6, Rector `dev-main`, php-cs-fixer plus ECS, Codeception 5 and Symfony 7.4 [code: composer.json:28-54 @7.x].
- 8.x moves to PHPUnit 13, keeps PHPStan level 6 with many more custom rules and a smaller baseline, pins Rector `^2.6.5`, drops php-cs-fixer for ECS only, runs tools from `vendor/bin/`, and adds `dg/bypass-finals` so tests can mock final classes [code: composer.json @8.x] [PR #17004] [PR #17280] [PR #17164] [PR #17366].
- 8.x forbids test doubles of `Request`, `InputBag` and `Router` (final in Symfony 8) [code: composer.json @8.x] [PR #17392].
- 8.x dispatches most events by class name, so a listener test asserting a string event key from `getSubscribedEvents()` must change [PR #17625].
- 5.x and 6.x run PHPUnit 9.6, 7.0 and 7.1 run PHPUnit 10.5, and 7.2 moved to PHPUnit 11.5 [PR #15814] [PR #15816] [PR #15817] [PR #16891].
- 5.x and 6.x stop tests defining `MAUTIC_TABLE_PREFIX` with a custom php-cs-fixer rule; 7.2 replaced it with a PHPStan rule [code: .php-cs-fixer.php:39-42 @5.0.0] [PR #11622] [PR #16578].
- `composer test` uses 1G of memory at 5.0.0 and 2G from 6.0.0 [code: composer.json:134 @5.0.0] [code: composer.json:152 @6.0.0].
- 6.0 CI crossed PHP 8.1-8.3 with MySQL and MariaDB; 7.0 raised the minimums to MySQL 8.4 and MariaDB 10.11 and 7.x pairs PHP with DB versions [code: .github/workflows/tests.yml:24-25 @6.0.0] [PR #14836].
- The Codeception E2E suite exists from 5.2; 5.0 and 5.1 have none [PR #13884] [PR #14079].
- Up to 7.1, CI collected coverage on every PR and failed when the PHPStan baseline changed; 7.2.0 removed both [PR #16646] [PR #16581].

## Pitfalls
- `bin/phpstan` without a warmed test container fails with "Container ... AppKernelTestDebugContainer.xml does not exist"; use `composer phpstan` [code: composer.json:166-214 @7.x].
- A stale `var/cache/test` dump hides your new entity; `rm -rf var/cache` [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-213 @7.x].
- A public page test must call `$this->logoutUser()` first, because `setUp()` logged in `admin` [code: app/bundles/EmailBundle/Tests/Functional/EmailClickTrackingTest.php:1-56 @7.x].
- An outbound call that "succeeds" in a test proves nothing; the mock answers 200 with an empty body [code: app/config/config_test.php:150-154 @7.x].
- `.env.test` says `MAUTIC_ADMIN_PASSWORD=mautic`, but the fixtures and the client use `Maut1cR0cks!` [code: .env.test @7.x] [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php:24-49 @7.x].
- php-cs-fixer in CI checks only changed files, so `composer cs` locally can report errors CI never would [code: .github/workflows/tests.yml:256-264 @7.x].
- Rector is pinned to `dev-main` on 7.x, so a rebase can surface new Rector findings unrelated to your change [code: composer.json:28-54 @7.x].
- Coverage is never collected on pull requests; adding the `ready-to-commit` label starts a long coverage run [code: .github/workflows/tests.yml:36-44 @7.x] [code: .github/workflows/coverage-check.yml:7-88 @7.x].
- Changes under `tests/` trigger a workflow that runs the e2e suite 10 times to catch flakiness [code: .github/workflows/e2e-tests.yml:25-28 @7.x].
- Fixed `wait()` calls in a Cest are rejected in review because they slow the suite; wait for the element, the closed modal or the notification instead [PR #14304] [PR #14157].
- E2E selectors that use styling, labels or list positions break; use Page objects with canonical IDs, scope modals to `#MauticSharedModal` and assert exact notification text [PR #14210] [PR #15937] [PR #17118].
- To see what a functional test wrote inside its rolled-back transaction, set your DB client to READ UNCOMMITTED [PR #9387].
- Do not add Codeception modules or other unrelated `composer.json` changes in a feature PR; reviewers ask for them to be reverted [PR #14998].
- A crashed run can leave `config/local.php.backup` behind [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:326-337 @7.x].
- Near-duplicate test methods trip SonarCloud's duplication gate; extract a helper [code: .agents/skills/mautic-dev/SKILL.md @7.x].
- The KB says Gitpod fixtures log in as admin/mautic; DDEV and tests use `Maut1cR0cks!` [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html].
- The e2e devdocs show `tests/Acceptance` and `Support/` with capitals; the tree uses `tests/acceptance/` and `tests/_support/` [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html] [code: codeception.yml @7.x].
- Open question: the KB DDEV article mentions MailHog while D13 notes DDEV now ships Mailpit [unverified]; either way the SMTP port is 1025 [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html].

## Related skills
- mautic-dev-environment - install and run DDEV, assets, Codespaces; switch here when the environment itself is broken.
- mautic-contributing - branch targeting, PR template, review norms, BC policy.
- mautic-architecture - kernel, DI, events, bundles; needed to know what to dispatch or inject in a test.
- mautic-upgrades-and-versions - migrations, release packaging and the 7.x to 8.x port.
- Every area skill (mautic-contacts, mautic-segments, mautic-campaigns, mautic-emails, mautic-forms, mautic-rest-api, mautic-webhooks, ...) - its `references/behaviour.md` is the oracle and its `references/test-patterns.md` lists area-specific tests and fixtures.

## Reference files
- references/behaviour.md - numbered conventions and rules for tests, static analysis and CI; per-change-type regression guide; black-box QA procedure.
- references/recipes.md - copy-ready skeletons (controller, API, command, listener, unit with mocks, mailer, config override, custom field), each adapted from a cited real test.
- references/code-map.md - every test-infrastructure file, helper trait, fixture, PHPStan rule, CI job and composer script.
- references/docs-digest.md - what devdocs and the KB say about e2e tests, DDEV and testing PRs and emails.
- references/version-notes.md - toolchain versions in 7.x and the 8.x delta.
- references/pr-history.md - why the base classes, table prefix, E2E norms, PHPStan baseline and rules, Rector, CI matrix and coverage policy are the way they are, with a regression catalogue from merged PRs.
