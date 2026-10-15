# Testing, static analysis and CI - pull-request history

## Contents
- [How to read this file](#how-to-read-this-file)
- [Decisions that shaped current behaviour](#decisions-that-shaped-current-behaviour)
  - [Running PHPUnit](#running-phpunit)
  - [Functional base classes and isolation](#functional-base-classes-and-isolation)
  - [Table prefix in tests](#table-prefix-in-tests)
  - [Test environment, timezone and assertions](#test-environment-timezone-and-assertions)
  - [HTTP stubs and test doubles](#http-stubs-and-test-doubles)
  - [Parallel and slow-test tooling](#parallel-and-slow-test-tooling)
  - [Codeception end-to-end suite](#codeception-end-to-end-suite)
  - [PHPStan and the baseline](#phpstan-and-the-baseline)
  - [Custom PHPStan rules](#custom-phpstan-rules)
  - [Rector](#rector)
  - [Coding standard and git hooks](#coding-standard-and-git-hooks)
  - [CI matrix and workflows](#ci-matrix-and-workflows)
  - [Coverage policy](#coverage-policy)
- [Regression catalogue](#regression-catalogue)
- [Feature timeline](#feature-timeline)
- [Removed, deprecated, replaced](#removed-deprecated-replaced)
- [Maintainer norms for this area](#maintainer-norms-for-this-area)
- [Open questions](#open-questions)
- [Coverage](#coverage)

## How to read this file
Source: merged pull requests on github.com/mautic/mautic for the test suite, static analysis and CI, harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; `~` marks an inference. "7.x, unreleased" means merged to 7.x after 7.2.1.
Current behaviour lives in behaviour.md (code-verified); this file explains why and when it came to be.

## Decisions that shaped current behaviour

### Running PHPUnit
- `composer test` is the standard way to run PHPUnit. It was added because the raw command was hard to remember [PR #3918] (~v2.8). It always passes `--configuration app/phpunit.xml.dist`, which is the only file that sets `KERNEL_CLASS` (behaviour 1.2) [PR #3918].
- CI calls `bin/phpunit` directly rather than `composer test` or a global `phpunit`. Why: Composer's 300-second script timeout killed long runs, and the global binary ran "No tests executed!" [PR #4343] (~v2.9).
- `composer test` sets its own PHP memory limit. Why: maintainers develop in 512 MB containers so app code stays inside that limit, but PHPUnit needs more. Originally `-d memory_limit=4G` [PR #9523] (~v3.2.3). The value was 1G at 4.4.0 and 5.0.0 and 2G from 6.0.0 to 7.x [code: composer.json:134 @5.0.0] [code: composer.json:152 @6.0.0] [code: composer.json:169 @7.x]. The PR that changed it is not in the inputs.
- PHPUnit 9 replaced 5.7 in 3.3, after PHP 7.2 was dropped and PHPStan was updated. PHPUnit 10 deprecations such as the `at()` matcher were left for separate PRs [PR #9602] (~v3.3).
- Mautic's own ErrorHandler is not registered under PHPUnit, so notices and warnings fail tests. Why: PRs had been adding notices (undefined index, `MAUTIC_TABLE_PREFIX already defined`) that nobody saw [PR #9602] (~v3.3).
- 7.0 and 7.1 run PHPUnit 10.5; the 5.2 and 6.0 lines run PHPUnit 9.6. All lines were bumped together for CVE-2026-24765 [PR #15814] [PR #15815] [PR #15816] [PR #15817] (7.1.0 / 7.0.1 / 5.2.10 / 6.0.8).
- 7.2.0 moved to PHPUnit 11 (`^11.5`). Why: PHPUnit 11 needs PHP 8.2, which is Mautic 7's minimum, so test and runtime PHP requirements stay in step [PR #16891] (v7.2.0).
- The PHPUnit 11 preparation made data providers static, removed `parent::__construct()` from test classes, made assertion-free tests declare it, and required tests that swap the error handler to restore it. Twig's `IntegrationTestCase` is patched by Composer so its providers are static [PR #16396] [PR #16397] [PR #16398] [PR #16399] (v7.2.0).
- PHPUnit on the newest supported PHP is expected to run without deprecations. Vendor deprecations were cleared by upgrading packages one at a time [PR #15280] [PR #15287] (~v7.0).

### Functional base classes and isolation
- Functional tests that touch the database extend `MauticMysqlTestCase`, which wraps each test in a transaction and rolls it back. Why: the suite went from 15.6 min and 1.14 GB to 7.0 min and 709 MB. The idea came from hautelook/AliceBundle [PR #9387] (~v3.2).
- Rollback cannot clean up schema-altering queries, MySQL full-text queries (they do not see uncommitted rows) or tests that boot the kernel twice. Those tests clean up themselves [PR #9387] (~v3.2). In 7.x they set `$useCleanupRollback = false` (behaviour 2.11, 2.12).
- Fixtures are avoided in functional tests; tests build the data they need. If fixtures are loaded they are appended, because purging is expensive. `MauticWebTestCase` stopped loading all fixtures in `setUp()` [PR #9387] (~v3.2).
- Data providers are avoided in functional tests (each data set boots the kernel again), and functional tests do not run in debug mode [PR #9387] (~v3.2).
- Tests never rely on fixed entity IDs. Debugging tip: set your DB client to READ UNCOMMITTED to see what a test wrote inside its transaction [PR #9387] (~v3.2).
- The suite cleans up test-case properties after each test to save memory (832 MB to 294 MB), including non-nullable typed properties [PR #9824] [PR #9834] (~v4.0) [historical mechanism].
- `MauticMysqlTestCase` restores global shell verbosity after each test, because one test's verbosity change broke later tests [PR #9853] (~v4.0).
- `runCommand()` is strict: a failing command fails the test instead of being swallowed [PR #10212] (~v4.2).
- Functional tests do not need an installed Mautic. The parameters `AppKernel::isInstalled()` needs are injected through `MAUTIC_CONFIG_PARAMETERS` [PR #10759] (~v4.2). This is the mechanism behind `$configParams` (behaviour 2.2).
- The DB snapshot is made with `mysqldump` run through `symfony/process`, so `~/.my.cnf` is honoured. Hard-coding `--column-statistics=0` was rejected because older clients reject the flag [PR #10759] (~v4.2).
- `mysqldump` and `mysql` receive DB credentials explicitly, not through `MYSQL_PWD`, because newer DDEV MariaDB ignores `MYSQL_PWD` [PR #15067] (v5.2.7).
- Functional tests use Symfony `KernelBrowser`, and the kernel is shut down before `createClient()` because Symfony 5 throws otherwise [PR #11049] (~v4.3) [PR #12172] (~v5.0).
- The base classes back up and restore `config/local.php`, verify that the rollback really happened, reset custom fields and clear the cache. Why: isolation, and a suite about 33% faster; it had run in Acquia's fork for months [PR #12138] (~v5.0). Behaviour 2.8 and 2.9 describe the current sentinel-row check.
- `MauticMysqlTestCase` has an `afterRollback()` hook so schema changes are undone even when the test fails. The author chose a new hook over `setUp()`/`beforeTearDown()` [PR #14482] (v5.2.2).
- The suite fails when a test needs a separate process and is not marked for it. Why: tests that only pass in isolation hide state leaks [PR #12137] (~v5.0). Today this is the `SeparateProcess` extension (behaviour 3.20).
- Flaky functional tests are fixed in shared base classes where possible [PR #15058] (~v7.0).
- Fixture users `admin` and `sales` use the password `Maut1cR0cks!`, matching DDEV. Why: password complexity rules made `mautic` trigger an insecure-password warning; see issue mautic/mautic#13104 [PR #13105] (~v5.1).
- Fixture classes that DI needs at runtime live outside `Tests/` (for example `DataFixtures/`), because `Tests/` folders are stripped from packages. Optional services whose class is missing are dropped [PR #8356] [PR #8377] (~v3.0).

### Table prefix in tests
- Tests must pass whatever `MAUTIC_TABLE_PREFIX` is, so SQL assertions include the prefix [PR #5087] (~v2.11).
- A random per-run prefix [historical] was replaced by a fixed prefix from env (`MAUTIC_DB_PREFIX`). Why: the dynamic prefix forced a cache rebuild before every run. A prefix that differs between dev, prod and test still catches hard-coded table names [PR #11476] (~v4.4.3).
- The default test prefix is `test_` [PR #11494] (~v5.0) [PR #11496] (~v4.4.3). Today `.env.test` holds it (behaviour 1.8).
- Tests in a separate process also get `MAUTIC_TABLE_PREFIX`. Why: an isolated test that ran first built the schema without the prefix and every later test failed [PR #11507] (~v4.4.4).
- Tests must not define `MAUTIC_TABLE_PREFIX`. Originally a custom php-cs-fixer rule, `Mautic/no_table_prefix_definition_in_tests`, removed such defines [PR #11622] (~v5.0); it is in `.php-cs-fixer.php` at 5.0.0 and 6.0.0 [code: .php-cs-fixer.php:39-42 @5.0.0] [code: .php-cs-fixer.php:47 @6.0.0]. Changed by [PR #16578] (v7.2.0): the PHPStan rule `NoTablePrefixDefinitionInTestsRule` replaced it because PHPStan sees through traits. The fixer is gone from 7.x and the rule is enabled [code: phpstan.neon:260 @7.x].
- Tests must not depend on another environment's cached config. When asset generation warms the cache with `.env` values, clear `var/cache` before PHPUnit [PR #11865] (~v5.0).

### Test environment, timezone and assertions
- Test env vars came from `.env`/`.env.dist` loaded by Symfony Dotenv [PR #4868] (~v2.11) [historical]. Since 5.0 they live in `.env.test`, and `index_dev.php` is gone [PR #12206] (~v5.0).
- CI sets `MAUTIC_ENV=test` so `config_test.php` is actually used [PR #11476] (~v4.4.3).
- PHPUnit runs with `date.timezone=UTC` in `app/phpunit.xml.dist`. Why: date tests failed outside UTC [PR #12788] (~v5.0) [PR #12791] (4.4 backport). DDEV also runs in UTC, so PHP and MySQL agree [PR #15650] (~v7.1).
- CI runs PHPUnit with `zend.assertions=1`, so `assert()` is evaluated. Enabling it exposed a wrong `\assert()` that was fixed in the same PR [PR #13338] (~v5.1).
- `symfony/phpunit-bridge` and `SYMFONY_DEPRECATIONS_HELPER` report runtime deprecations PHPStan cannot see. Showing them in CI without failing was proposed and rejected as an ignored "wall of text"; no default level was agreed [PR #13150] (~v5.1). 7.x uses `weak` [PR #13150].

### HTTP stubs and test doubles
- In the test environment the HTTP client service is replaced by a stub, so functional tests cannot call third parties [PR #9440] (~v3.3). Behaviour 3.6 and 3.7 describe the 7.x `MockHttpClient` and Guzzle `MockHandler`.
- Test HTTP clients use Guzzle's client and mock handler, not the abandoned `php-http/mock-client` and `php-http/message-factory` [PR #12439] (~v5.0).
- Query-building logic is pulled into its own method so it can be unit-tested against SQL; `DBALMocker` exists for this [PR #7358] (~v2.15.2).
- Private services can be replaced with `static::getContainer()->set()` because Mautic wires its own `TestContainer`. Why: Symfony's container throws "service is private, you cannot replace it" [PR #13797] (~v5.1).

### Parallel and slow-test tooling
- The test database is built once per suite run, and slow tests can be listed [PR #11585] (~v5.0). Slow-test reporting is enabled with `MAUTIC_TEST_LOG_SLOW_TESTS=1` and tuned with `MAUTIC_TEST_SLOW_TESTS_THRESHOLD` [PR #12844] (~v5.1). In 7.x it is the `SlowTest` extension (behaviour 1.10).
- `bin/console mautic:phpunit:config <N>` writes a PHPUnit config split into N suites, each starting with `FunctionalWarmupTest` [PR #15628] (~v7.1). CI does not use it (behaviour 1.12).
- An `ExecuteTestAfterExtension` once helped find the earlier test that broke a later one [PR #10212] (~v4.2). It is not in 7.x; the extensions are `DbPrefix`, `SeparateProcess` and `SlowTest` [code: app/phpunit.xml.dist @7.x].

### Codeception end-to-end suite
- Codeception was first added for acceptance tests in 2017 [PR #4868] (~v2.11) and upgraded to 4 to drop abandoned `facebook/webdriver` [PR #8342] (~v3.0); no such tests existed then [PR #8342].
- The working E2E suite under `tests/` runs against a Selenium Chrome DDEV add-on, starting with contact management [PR #13884] (~v5.2). Reviewers required tests that can run more than once without leftover data [PR #13884].
- `composer e2e-test` runs it, and the DDEV setup prints the command [PR #14079] (~v5.2). It runs in `tests.yml` on every PR [PR #14086] (~v5.2).
- Codeception moved to its latest major once PHP 8.0 was dropped [PR #14090] (~v5.2).
- On failure CI uploads screenshots and HTML as `e2e-test-screenshots` [PR #14194] (~v5.2); E2E output is streamed to the log [PR #16730] (v7.2.0).
- Every Cest uses Step objects and Page objects, with one selector style. Why: mixed styles made new tests hard to write [PR #14210] (~v5.2).
- Selectors must not depend on styling or label markup. Wait for modals to close [PR #14157] (~v5.2).
- Flaky tests are fixed with element and notification waits, not fixed `wait()` calls, which make the suite slower. The fix in [PR #14304] (~v5.2) was proven with 10 consecutive CI runs; see issue mautic/mautic#14174 [PR #14304].
- `e2e-tests.yml` runs the suite 10 times when `tests/` changes [PR #14318] (~v6.0). It first landed on 5.x and was reverted because 5.x was closed [PR #14311] [PR #14317]. Reducing it to 4 runs was discussed [PR #16724]; the 7.x workflow still runs 10 iterations [code: .github/workflows/e2e-tests.yml:27 @7.x].
- The Codeception Db populator reads every credential, including the password, from env [PR #14492] (~v6.0) [PR #14493] (v5.2.2).
- Selectors must be deterministic: bulk actions by label, contacts by ID, modals scoped to `#MauticSharedModal`, unique emails, exact notification text [PR #15937] (v7.1.0).
- E2E runs on the official multi-arch `selenium/standalone-chromium` image. Flaky tests exposed by Chromium upgrades are fixed rather than pinning an old browser [PR #16724] [PR #16727] (v7.2.0).
- E2E must run with `APP_ENV=test`. `EnvHelper` rewrites `.env.local` for the run and restores it. Why: DDEV's `.env.local` defaults to dev, so most tests failed locally [PR #16729] (v7.2.0). Earlier PRs told developers to edit `.env.local` by hand [PR #14061] [historical].
- GrapesJS builder tests wait for `Mautic.launchBuilder`, click `#page_buttons_builder` (not `.btn-builder`), wait for the theme request and the enabled button, then for `.builder.builder-active` [PR #17118] (v7.2.0).
- UI bug fixes are expected to ship with a Cest where practical [PR #14750] [PR #14794] [PR #14833] [PR #15914]. An E2E assertion checks the real contract (every action link has an `href`) rather than a proxy attribute [PR #14833] (~v6.0.1).
- PHP-CS-Fixer also covers `tests/` [PR #16729]; `tests/_support` classes are `final` [PR #16733] (v7.2.0).

### PHPStan and the baseline
- PHPStan analyses migrations too. Why: a migration referencing a non-existent class shipped in 3.2.0 and broke upgrades; see issue mautic/mautic#9479 [PR #9480] (~v3.2.2).
- PHPStan runs in parallel; constants are declared in `phpstan.neon` so every process evaluates them the same way [PR #10696] (~v4.1.1).
- PHPStan runs with the Symfony, PHPUnit, deprecation-rules and php-parser extensions, so framework code is understood and new use of deprecated code is blocked [PR #11970] (~v5.0).
- `phpstan.neon` excludes as little as possible. A temporary `ignoreErrors` entry with a removal note is acceptable during a framework upgrade [PR #12200] [PR #12225] (~v5.0).
- When PHPStan or Rector is upgraded, the baseline is regenerated rather than every new error fixed [PR #12302] [PR #12531] (~v5.0).
- `composer phpstan` builds the test container when it is missing [PR #12515] (~v5.0).
- The PHPStan cache lives in `var/phpstan-cache`, because the `post-checkout` hook clears `var/cache` on every branch switch [PR #13302] [PR #13309] (~v5.1).
- Baseline guard: originally a CI job failed whenever `phpstan-baseline.neon` changed, so the baseline could only shrink [PR #10857] (~v4.2). Changed by [PR #16581] (v7.2.0): the job was removed as mostly false positives; the main PHPStan job is enough [PR #16581].
- The baseline was cut from about 37.6k to about 14.1k lines by excluding less serious identifiers [PR #16500] (v7.2.0); later PRs regenerate it to drop fixed errors [PR #16553] [PR #16719].
- Mautic's own deprecations are skipped by the deprecation rules, so vendor deprecations stay visible [PR #16502] (v7.2.0).
- A git-ignored `phpstan.neon.dist` can include `phpstan.neon` and override parallel settings for faster local runs [PR #16550] (v7.2.0).
- PHPStan is at level 6 at 5.0.0, 6.0.0 and 7.x [code: phpstan.neon:6 @5.0.0] [code: phpstan.neon:6 @6.0.0] [code: phpstan.neon:6 @7.x]. The "level 3 fixes" PRs worked from a no-baseline level-3 run [PR #16494] [PR #16545] (v7.2.0).
- `symplify/phpstan-rules` [PR #16716] [PR #16742] and the `rector/type-perfect` ruleset [PR #16850] are enabled (v7.2.0). Under type-perfect, objects are checked with `instanceof`, not `empty()` or `isset()` [PR #16850].

### Custom PHPStan rules
- Custom rules live in `utils/phpstan/src/Rule/` with tests in `utils/phpstan/tests/`, run by PHPUnit [PR #16583] (v7.2.0).
- A new rule is merged in its own PR, with existing violations baselined or the rule disabled, and enabled once the codebase is fixed [PR #16641] [PR #16748] [PR #16984].
- Rules added in 7.2.0: `AbstractClassNameMustBeAbstractRule` [PR #16529]; `NoTablePrefixDefinitionInTestsRule` [PR #16578]; `AutowireMethodNameMustMatchClassRule` (`#[Required]` setters named `autowire<Class>`) [PR #16600]; `NoGetModelWithStringInControllerRule` [PR #16641], skipping traits [PR #16662]; `NoRequiredMethodWithConstructorInControllerRule` [PR #16663]; `NoNullableServiceInConstructorRule` [PR #16703]; `NoGetRepositoryWithEntityInRepositoryRule` [PR #16725]; `NoContainerGetRule` [PR #16737]; `NoEntityManagerGetRepositoryRule` (131 violations baselined) [PR #16748]; `NoPropertyToPropertyAssignRule` [PR #16766]; `NoServiceJugglingRule` [PR #16908]; `ConstraintMustHaveAttributeRule` [PR #16975].
- `NoContainerGetRule` was merged "not enabled yet" [PR #16737] and is enabled in 7.x [code: phpstan.neon:268 @7.x].
- `NoServiceInMethodParameterRule` forbids passing shared services as method parameters [PR #16984] (v7.2.0). It was merged to be enabled later. The class exists in 7.x but is not registered in `phpstan.neon` [code: utils/phpstan/src/Rule/NoServiceInMethodParameterRule.php @7.x] [code: phpstan.neon:257-277 @7.x].
- `NoServicesInBundleConfigRule` is enabled in 7.x [code: phpstan.neon:274 @7.x]; it enforces the move of every bundle service to `Config/services.php` [PR #16758] [PR #16861] (v7.2.0). `NoUnusedServiceAliasRule` exists but is commented out [code: phpstan.neon:275 @7.x].
- Container smoke tests (`AbstractContainerSmokeTestCase`, `EventSubscriberSmokeTest`) were added to check the container after the service move [PR #16843] [PR #16861] (v7.2.0).

### Rector
- Rector runs in CI as a standalone dev dependency [PR #10168] (~v4.0). Its config uses `RectorConfig` [PR #11227] (~v4.4) and rule sets rather than single rules [PR #12376] (~v5.0).
- Symfony rule sets run in CI, with `cache:warmup` first because they need the container XML. Why: to stop about 260 open PRs adding deprecated Symfony code [PR #11479] (~v5.0).
- CI runs Rector once with `--dry-run` and fails if it would change anything [PR #13024] (~v5.0).
- The heavy `UP_TO_*` sets were kept for the "Unforking" initiative and plugin authors [PR #12676]; old-Symfony rules later moved to `rector-older-symfony.php` [PR #13048] (~v5.0), which is not in 7.x [PR #13048].
- Dead-code rules are welcome. Adding return types to public methods is a BC break, so it waits for a major [PR #12938] (~v5.0). Extension-point classes such as `FormController` are skipped by return-type rules [PR #16333] (v7.2.0).
- The custom `UnserializeToSerializerDecodeRector` blocks new `unserialize()` calls. Why: five had crept back since the 2019 clean-up [PR #16193] (v7.2.0).
- Separate `rector-tests.php` and `rector-mock-to-stub.php` runs were folded into `rector.php` [PR #16549]; unused skips are removed [PR #16311] [PR #16554] (v7.2.0).
- `rector.php` applies the full privatization set [PR #16842] and the Symfony sets [PR #16859] (v7.2.0). Rector must be locked to a production tag before a release [PR #16859]; 7.x still pins `dev-main` (SKILL.md pitfall).
- Custom Rector rules live in `utils/rector/src/`, for example `ModelGetRepositoryToRepositoryServiceRector` [PR #16739] and `ConfigServiceToAutowiredServiceRector` [PR #16758] (v7.2.0).

### Coding standard and git hooks
- PHP-CS-Fixer enforces code style; `.php_cs` became `.php-cs-fixer.php` [PR #6991] (~v2.16) [historical file name].
- The pre-commit hook runs php-cs-fixer once on all staged files [PR #6002] (~v2.14) [PR #8357] (~v3.0).
- A blocking CS pre-commit hook was reverted because it broke merge commits in PhpStorm; the hook fixes and re-stages, it does not block [PR #13299] (~v5.1).
- CS fixes are run with `bin/php-cs-fixer fix --config=.php-cs-fixer.php` on the changed files [PR #14833].

### CI matrix and workflows
- CI moved from Travis to GitHub Actions [PR #9451] [PR #9453] (~v3.3). PHPUnit runs on both MySQL and MariaDB. Running only two PHP versions was rejected [PR #9234] (~v3.2).
- CI triggers on every `[MAJOR].*` branch; the old `N.N` pattern left 4.x untested for two months [PR #10591] (~v4.x).
- Scheduled and side-effect workflows run only in mautic/mautic; unit tests still run on any fork [PR #10594] [PR #10894] [PR #11062] (~v4.2-4.3).
- Required status checks reference CI job names, so jobs are not renamed casually [PR #10857] [PR #9451].
- CI also checks scaffolded files [PR #10857], the `mautic/recommended-project` install [PR #11039] [PR #11164] [PR #15436], `lint:twig` [PR #11844] and `composer.lock` sync via `composer validate` [PR #12473] [PR #13029]. `plugin-api-version` drift is ignored [PR #12690].
- CI caches PHPStan, Rector, Composer, npm and webpack results and puts MySQL on tmpfs, cutting runs from about 15 to about 5 minutes [PR #11952] [PR #12475] [PR #12695] [PR #12771] (~v5.0).
- `tests.yml` runs on `merge_group` for the merge queue [PR #12129] (~v5.0).
- Workflow tokens are read-only by default with per-job write grants [PR #11295] [PR #11509]. Actions are pinned to commit SHAs (not tag-object hashes) and bumped by Dependabot [PR #16214] [PR #16227] (v7.2.0).
- PHP 8.0 was dropped in 5.2. Why: no security support, and four PHP versions wasted CI minutes [PR #13972] (~v5.2). PHP 8.3 was added [PR #13958].
- The 6.0.0 matrix was a cross product of PHP 8.1, 8.2, 8.3 and MySQL, MariaDB [code: .github/workflows/tests.yml:24-25 @6.0.0].
- Mautic 7 supports MySQL 8.4+ and MariaDB 10.11+. Every PHP x DB combination was debated against Actions minutes, and only the latest version per DB major is tested [PR #14836] (~v7.0). MariaDB health uses `healthcheck.sh`, MySQL uses `mysqladmin ping` [PR #14836].
- The 7.x matrix pairs PHP with databases instead of crossing them: PHP 8.2 with MySQL 8.4 and MariaDB 10.11, PHP 8.5 with MySQL 9.2 and MariaDB 11.4 [code: .github/workflows/tests.yml:22-32 @7.x] [PR #16646].
- `api-library-tests.yml` runs mautic/api-library against the checkout [PR #16532] (v7.2.0). Fixes on a patch branch are merged up so the scheduled api-library tests stay green [PR #13457] (~v5.1).
- `validate-json.yml` checks changed JSON files with `jq` [PR #14622] (~v6.0).
- From 7.2.2 the release workflow checks that DomCrawler is in the full package [PR #17616]; this is fixed in 7.2.2 on the 7.2 branch and not in the 7.x snapshot.
- In 8.x, CI runs PHP 8.4 only [PR #16993] and fails when an existing table changes shape [PR #17407] (8.x only).

### Coverage policy
- Coverage was generated for one PHP version only, and `composer test` does not collect it by default [PR #8954] (~v3.0.1).
- PRs are expected to keep or improve coverage; a drop is ignored when no PHP code changed [PR #9120] [PR #9523] [PR #10105].
- Codecov and SonarCloud are advisory [PR #12199] [PR #13622]. JUnit and clover reports feed SonarCloud [PR #12454] (~v5.0).
- Coverage is no longer collected on pull requests, only on push and schedule. Why: the coverage leg took about 19 minutes against about 11 [PR #16646] (v7.2.0).
- A PR gets a one-off coverage run when labelled `check-coverage` (removed afterwards) or `ready-to-commit` (kept). Label removal runs through `workflow_run` because fork PRs have read-only tokens [PR #16697] (v7.2.0).

## Regression catalogue
| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **Running PHPUnit** | | | |
| `composer test` killed after 300 s in CI | CI calls `bin/phpunit` directly | [PR #4343] | ~2.9 |
| `composer test` ran out of memory in a 512 MB container | The script sets its own memory limit | [PR #9523] | ~3.2.3 |
| Date tests failed outside UTC | PHPUnit runs in UTC | [PR #12788] [PR #12791] | ~5.0 / 4.4 |
| A wrong `\assert()` went unnoticed | CI runs with `zend.assertions=1` | [PR #13338] | ~5.1 |
| **Base classes and isolation** | | | |
| A test changed shell verbosity and broke later tests | Verbosity is restored after each test | [PR #9853] | ~4.0 |
| Functional tests needed a local install | Config comes from `MAUTIC_CONFIG_PARAMETERS` | [PR #10759] | ~4.2 |
| mysqldump "Unknown table COLUMN_STATISTICS" | The snapshot honours `.my.cnf` | [PR #10759] | ~4.2 |
| mysqldump "Access denied" under DDEV MariaDB | Credentials passed explicitly | [PR #15067] | 5.2.7 |
| Schema change left behind when a test failed | `afterRollback()` undoes it | [PR #14482] | 5.2.2 |
| Fixture login warned the password was insecure | Fixture password `Maut1cR0cks!` | [PR #13105] | ~5.1 |
| Package console failed on a stripped test fixture class | Optional services are dropped when their class is missing | [PR #8377] | ~3.0 |
| **Table prefix** | | | |
| Repository tests failed with a table prefix set | Tests honour `MAUTIC_TABLE_PREFIX` | [PR #5087] | ~2.11 |
| Tests ran without a prefix | Default prefix `test_` | [PR #11494] [PR #11496] | ~5.0 / 4.4.3 |
| An isolated test created unprefixed tables first | Isolated processes define the prefix | [PR #11507] | ~4.4.4 |
| Tests failed after asset generation warmed the cache | Clear `var/cache` before PHPUnit | [PR #11865] | ~5.0 |
| **E2E** | | | |
| Codeception failed on deprecation warnings | Exit code reflects test results | [PR #14061] | ~5.2 |
| Click intercepted by a lingering modal | Tests wait for overlays to close | [PR #14157] | ~5.2 |
| Flaky batch-DNC and batch-category Cests | Element and notification waits; 10 green runs | [PR #14304] | ~5.2 |
| Db populator "access denied" | All credentials from env | [PR #14492] [PR #14493] | ~6.0 / 5.2.2 |
| E2E install failed: MariaDB 10.3 too old | DDEV MariaDB matches the installer minimum | [PR #14836] | ~7.0 |
| Most E2E tests failed locally in dev mode | `EnvHelper` forces `APP_ENV=test` | [PR #16729] | 7.2.0 |
| CI E2E failure showed only an exit code | Output streamed to the log | [PR #16730] | 7.2.0 |
| GrapesJS Cest missed the builder button | Canonical selector plus AJAX and state waits | [PR #17118] | 7.2.0 |
| **Static analysis** | | | |
| Upgrade broke on a migration using a missing class | Migrations are analysed by PHPStan | [PR #9480] | ~3.2.2 |
| `composer phpstan` failed on a clean checkout | It builds the test container first | [PR #12515] | ~5.0 |
| PHPStan cache lost on every branch switch | Cache in `var/phpstan-cache` | [PR #13302] | ~5.1 |
| Rector took 13 minutes in dry-run | Rector cache populated in CI | [PR #12475] | ~5.0 |
| A tool upgrade merged red and broke all PRs | Tool-upgrade PRs must be green | [PR #12556] | ~5.0 |
| **CI** | | | |
| No CI on 4.x for two months | Triggers on every `[MAJOR].*` branch | [PR #10591] | ~4.x |
| Forks got scheduled-workflow failure emails | Side-effect workflows run only in mautic/mautic | [PR #10594] [PR #10894] | ~4.2 |
| Composer 2.6 changed `plugin-api-version` and broke CI | The lock check ignores it | [PR #12690] | ~5.0 |
| `composer.lock` drifted from `composer.json` | CI fails on an out-of-sync lock | [PR #12473] | ~5.0 |
| Binary downloads broke after an unrelated lock bump | Unrelated lock changes reverted | [PR #11563] | ~5.0 |
| 5.1.0 release pipeline failed | Paired artifact actions on the same major | [PR #13830] | 5.1.0 |
| CI MariaDB job ran out of memory | Explicit memory limit | [PR #13622] | ~5.0.4 |

## Feature timeline
| Version | Change | PR |
|---|---|---|
| ~2.8-2.11 | `composer test`; `.env` test vars; first Codeception scaffolding | [PR #3918] [PR #4868] |
| ~3.0-3.3 | Single-version coverage; transaction rollback; HTTP stub; PHPUnit 9; GitHub Actions; daily CI | [PR #8954] [PR #9387] [PR #9440] [PR #9602] [PR #9451] [PR #9668] |
| ~4.0-4.4 | Property cleanup; strict `runCommand()`; no install needed; baseline and scaffold checks; Composer-install job; Rector config; static `test_` prefix | [PR #9824] [PR #10212] [PR #10759] [PR #10857] [PR #11039] [PR #11227] [PR #11476] |
| ~5.0 | Separate-process detector; faster isolated base classes; PHPStan extensions; Twig lint; Rector sets and dry-run; lock-sync check; UTC; merge queue | [PR #12137] [PR #12138] [PR #11970] [PR #11844] [PR #11479] [PR #13024] [PR #12473] [PR #12788] [PR #12129] |
| ~5.1 | Private-service replacement; phpunit-bridge; `zend.assertions=1`; `var/phpstan-cache`; slow-test vars | [PR #13797] [PR #13150] [PR #13338] [PR #13302] [PR #12844] |
| ~5.2 | Codeception E2E suite, `composer e2e-test`, E2E in CI, Page/Step standard; PHP 8.3 in, 8.0 out; `afterRollback()` | [PR #13884] [PR #14079] [PR #14086] [PR #14210] [PR #13958] [PR #13972] [PR #14482] |
| ~6.0 | E2E 10x flakiness workflow; JSON validation; AI test prompt | [PR #14318] [PR #14622] [PR #15102] |
| ~7.0 | MySQL 8.4+ / MariaDB 10.11+ matrix; deprecation-free PHPUnit on PHP 8.4 | [PR #14836] [PR #15280] |
| 7.1.0 | `mautic:phpunit:config`; deterministic E2E selectors | [PR #15628] [PR #15937] |
| 7.2.0 | PHPUnit 11; custom PHPStan and Rector rules in `utils/`; baseline cut; baseline job removed; no coverage on PRs; label-triggered coverage; api-library CI; SHA-pinned actions; Chromium image; `EnvHelper` | [PR #16891] [PR #16583] [PR #16500] [PR #16581] [PR #16646] [PR #16697] [PR #16532] [PR #16227] [PR #16724] [PR #16729] |
| 7.2.2 (7.2 branch) | Release workflow asserts DomCrawler in the package | [PR #17616] |
| 8.x | PHP 8.4-only CI; table-shape check | [PR #16993] [PR #17407] |

## Removed, deprecated, replaced
| What | Replaced by | PR | Version |
|---|---|---|---|
| Travis CI | GitHub Actions | [PR #9451] [PR #9453] | ~3.3 |
| PHPUnit 5.7 | PHPUnit 9, then 10.5 (7.0), then 11.5 (7.2) | [PR #9602] [PR #15814] [PR #16891] | 3.3 / 7.0 / 7.2.0 |
| DB rebuild per test, all fixtures in `setUp()` | Transaction rollback, in-test data | [PR #9387] | ~3.2 |
| `FrameworkBundle\Client` | `KernelBrowser` | [PR #11049] | ~4.3 |
| Random test prefix | `MAUTIC_DB_PREFIX`, default `test_` | [PR #11476] [PR #11494] | ~4.4.3 / 5.0 |
| `.env`/`.env.dist` test vars, `index_dev.php` | `.env.test`, `.env.local` | [PR #12206] | ~5.0 |
| `php-http/mock-client` | Guzzle mock handler | [PR #12439] | ~5.0 |
| Blocking CS pre-commit hook | Reverted | [PR #13299] | ~5.1 |
| `rector-older-symfony.php` | Not in 7.x | [PR #13048] | ~5.0 |
| PR auto-labeller workflow | Reverted (failed on fork PRs) | [PR #13874] [PR #13993] | 2024-07 |
| `NoTablePrefixDefinitionInTestsFixer` | `NoTablePrefixDefinitionInTestsRule` | [PR #16578] | 7.2.0 |
| Root `/phpstan`, `/rector` | `utils/phpstan`, `utils/rector` | [PR #16583] | 7.2.0 |
| "PHPStan baseline changes" job | Main PHPStan job only | [PR #16581] | 7.2.0 |
| Coverage on every PR | Push/schedule plus label opt-in | [PR #16646] [PR #16697] | 7.2.0 |
| seleniarm image | `selenium/standalone-chromium` | [PR #16724] | 7.2.0 |
| phpspec/prophecy (5.2, 6.0) | PHPUnit mocks | [PR #15816] [PR #15817] | 5.2.10 / 6.0.8 |

## Maintainer norms for this area
- PRs that change only tests or CI can merge with one approval once CI is green; CI blockers may be self-merged [PR #11045] [PR #12137] [PR #12765] [PR #13797].
- For CI-only changes, "if GH Actions are green then this works" is an accepted test plan [PR #13791] [PR #14090].
- New features need tests before they go into a minor, and the release can wait [PR #9103].
- Bug fixes include automated tests; UI fixes get a Cest with Page and Step objects [PR #14750] [PR #14794] [PR #15914].
- Prove a flakiness fix with repeated runs; prefer fixing flaky E2E tests over pinning old browsers [PR #14304] [PR #16724].
- Fix new findings in the same PR that bumps a tool, or regenerate the baseline; never merge with PHPStan red [PR #9522] [PR #12302] [PR #12556] [PR #16615].
- Ignore a widely used new deprecation centrally in `phpstan.neon`, not inline [PR #14495].
- Satisfy PHPStan against the locked dependency version rather than widening return types [PR #16487].
- Split big refactors into small single-concern PRs and rebuild the baseline after rebase [PR #16396] [PR #16544] [PR #16716].
- CI "rector" and "coding standard" failures block merging even for behaviour-neutral changes [PR #16768].
- Test schema changes must be reverted even when the test fails [PR #14482].
- Keep CI affordable: test the latest version per DB major, and keep tooling fast [PR #14836] [PR #13048] [PR #16646].
- Update paired GitHub Actions together, for example upload and download artifact [PR #13830].

## Open questions
- Resolved: behaviour.md 9.7 previously repeated the KB's `index_dev.php` advice; it now says dev mode is `APP_ENV=dev` in `.env.local` [PR #12206] [PR #13295].
- `.env.test` still sets `MAUTIC_ADMIN_PASSWORD=mautic` although [PR #13105] moved fixtures to `Maut1cR0cks!`; no code reads the variable (SKILL.md pitfall) [PR #13105].
- The PR that lowered `composer test` from 4G [PR #9523] to 1G (4.4.0) and later raised it to 2G (6.0.0) is not in the inputs [code: composer.json:152 @6.0.0].
- `NoServiceInMethodParameterRule` [PR #16984] is not registered in `phpstan.neon`; whether it will be enabled is open.
- Reducing the E2E flakiness workflow from 10 to 4 runs was discussed [PR #16724]; 7.x still runs 10.
- No default `SYMFONY_DEPRECATIONS_HELPER` level was agreed [PR #13150]; whether contributors must act on runtime deprecations is unstated.
- Codeception silences deprecations [PR #14061] while PHPUnit aims for zero [PR #15280]; the suites follow different policies.
- [PR #17407] (8.x table-shape check) has no description; how an intended schema change is allowed is unknown.
- `NoPropertyToPropertyAssignRule` [PR #16766] has no description; read the rule source before relying on its intent.
- [PR #11563] showed no tests covered `BinaryFileResponse` downloads; whether that gap has closed is not checked.

## Coverage
The dev-tooling-testing area has 588 merged PRs in six chunks (#258 to #17832, 2015-04 to 2026-10): 122, 119, 102, 98, 105 and 42 PRs.
About 440 are substantive across testing and dev-env; the rest are dependency bumps, template edits, reverts and branch merges.
This file uses the `[testing]` items; `[dev-env]` items are in mautic-dev-environment, and product-code PRs that landed in the bucket were skipped.
A further 869 noise PRs across all areas were excluded upstream before chunking.
