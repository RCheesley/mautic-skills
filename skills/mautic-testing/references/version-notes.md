# Mautic testing: version notes

## 5.x and 6.x
Differences found in the merged PRs (588 dev-tooling-testing PRs; detail in pr-history.md):
- PHPUnit 9.6 on the 5.2 and 6.0 lines, bumped to 9.6.34 for CVE-2026-24765 [PR #15816] [PR #15817].
- `composer test` uses `-d memory_limit=1G` at 5.0.0 and 2G at 6.0.0 [code: composer.json:134 @5.0.0] [code: composer.json:152 @6.0.0].
- PHPStan is already at level 6 at 5.0.0 and 6.0.0 [code: phpstan.neon:6 @5.0.0] [code: phpstan.neon:6 @6.0.0].
- `MAUTIC_TABLE_PREFIX` defines in tests are removed by the php-cs-fixer rule `Mautic/no_table_prefix_definition_in_tests` [PR #11622] [code: .php-cs-fixer.php:39-42 @5.0.0] [code: .php-cs-fixer.php:47 @6.0.0].
- 5.0: separate-process detector, rollback verification, UTC in `phpunit.xml.dist`, PHPStan Symfony/PHPUnit extensions, single Rector dry-run, lock-sync check, merge-queue trigger [PR #12137] [PR #12138] [PR #12788] [PR #11970] [PR #13024] [PR #12473] [PR #12129].
- 5.1: private-service replacement through `TestContainer`, `symfony/phpunit-bridge`, `zend.assertions=1` in CI, PHPStan cache in `var/phpstan-cache`, fixture password `Maut1cR0cks!` [PR #13797] [PR #13150] [PR #13338] [PR #13302] [PR #13105].
- 5.2: Codeception E2E suite, `composer e2e-test` and the E2E CI job; PHP 8.0 dropped and 8.3 added; `afterRollback()` (5.2.2) [PR #13884] [PR #14079] [PR #14086] [PR #13972] [PR #13958] [PR #14482].
- 6.0: CI crosses PHP 8.1, 8.2, 8.3 with MySQL and MariaDB [code: .github/workflows/tests.yml:24-25 @6.0.0]; the 10x E2E flakiness workflow and JSON validation arrive [PR #14318] [PR #14622].

The KB's Gitpod-based PR-testing flow and
its admin/mautic login come from older setups; current DDEV and test fixtures use `Maut1cR0cks!`
[kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]
[code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php:24-49 @7.x]. The minimum version that 7.2.1 upgrades
from is 5.0.0 [code: app/release_metadata.json @7.x].

## 7.x (snapshot: release 7.2.1 plus unreleased merged PRs)
- PHP `~8.2` (composer platform 8.2.0); release metadata allows PHP 8.2.0-8.5.99, MySQL >= 8.4.0, MariaDB >= 10.11.0 [code: app/composer.json:16 @7.x] [code: composer.json:216-218 @7.x] [code: app/release_metadata.json @7.x].
- PHPUnit 11.5 (locked 11.5.56), schema 10.5 config; Codeception 5.3.6; PHPStan 2.3.1 at level 6; Rector `dev-main`; php-cs-fixer 3.95 plus ECS 13; Symfony 7.4 [code: composer.json:28-54 @7.x].
- DDEV runs PHP 8.5 with MariaDB 10.11 while CI's minimum cell is PHP 8.2; check behaviour that differs between PHP versions [code: .ddev/config.yaml:1-24 @7.x] [code: .github/workflows/tests.yml:22-32 @7.x].
- CI matrix: PHP 8.2 x (MySQL 8.4, MariaDB 10.11), PHP 8.5 x (MySQL 9.2, MariaDB 11.4) [code: .github/workflows/tests.yml:22-32 @7.x].
- Twig is patched so `IntegrationTestCase` data providers are static for PHPUnit 11 [code: composer.json:254-258 @7.x].
- 7.0: MySQL 8.4+/MariaDB 10.11+ in CI and DDEV; PHPUnit 10.5 runs without deprecations on PHP 8.4 [PR #14836] [PR #15280] [PR #15814].
- 7.1: `mautic:phpunit:config <N>` and deterministic E2E selectors [PR #15628] [PR #15937].
- 7.2.0: PHPUnit 11.5; custom PHPStan and Rector rules move to `utils/`; `NoTablePrefixDefinitionInTestsRule` replaces the CS fixer; baseline cut to about 14.1k lines; the baseline-change job and PR coverage removed, label-triggered coverage added; api-library CI; Actions pinned to SHAs; `EnvHelper` for E2E [PR #16891] [PR #16583] [PR #16578] [PR #16500] [PR #16581] [PR #16646] [PR #16697] [PR #16532] [PR #16227] [PR #16729].
- 7.2.2 (7.2 branch, not in this snapshot): the release workflow checks DomCrawler is in the package [PR #17616].

## 8.x delta (8.x at 11599729491, unreleased)
| Item | 7.x | 8.x | Source |
|---|---|---|---|
| PHPUnit | ^11.5 | ^13.0 (via 12) | [code: composer.json @8.x] [PR #17004] [PR #17019] [PR #17063] [PR #17163] |
| PHP minimum | 8.2 | 8.4 | [code: app/composer.json @8.x] [PR #16993] |
| Symfony | ~7.4.0 | ~8.1.0 | [code: app/composer.json @8.x] [PR #17392] |
| Doctrine ORM / DBAL | 2.x / 3.x | ^3.7 / ^4.4 | [code: app/composer.json @8.x] [PR #17361] |
| data-fixtures / fixtures-bundle | ^1.6.6 / ^3.4.4 | ^2.2 / ^4.3 | [code: app/composer.json @8.x] [PR #17353] |
| Codeception | ^5.1 | ^5.3.5 | [code: composer.json @8.x] |
| PHPStan | level 6 | still level 6; baseline 12,268 to 8,683 lines; new rules incl. `NoServiceGetterRule`, `NoServiceInEventConstructorRule`, model single-param typing | [code: phpstan.neon @8.x] [PR #17631] [PR #17766] [PR #17799] [PR #17365] [PR #17238] [PR #17640] |
| Rector | dev-main + type-perfect | ^2.6.5, type-perfect dropped, `withPhpSets(php84: true)`, adds `symfonyCodeQuality`, custom `LoadMetadata*ToDoctrineAttributeRector`, `RequestGetToParameterBagsRector` | [code: rector.php @8.x] [PR #17190] [PR #17498] [PR #17309] [PR #17324] |
| Coding standard | php-cs-fixer + ECS | ECS only; `.php-cs-fixer.php` deleted; pre-commit runs `vendor/bin/ecs` | [PR #17280] [PR #17362] |
| Tool paths | `bin/phpunit`, `bin/phpstan`, ... | `vendor/bin/*` | [code: composer.json @8.x] [PR #17164] |
| Mocking finals | not possible | `dg/bypass-finals ^1.11` enabled in `app/tests/bootstrap.php` | [code: composer.json @8.x] [PR #17366] |
| Removed test helpers | present | `CoreBundle\Test\DoctrineExtensions\TablePrefix`, `Tests\Twig\TwigIntegrationTestTrait`, Codeception `FunctionalTester`/functional suite | [PR #17182] [PR #17183] [PR #17184] [PR #17185] [PR #17241] [PR #17696] [PR #17033] |

Consequences for tests on 8.x:
- Do not create test doubles of `Request`, `InputBag` or `Router`; they are final in Symfony 8 [PR #17392].
- Most events are dispatched by class name; assertions on `getSubscribedEvents()` keys and listener registrations must use event classes. Some constants still exist but are never dispatched, so a listener keyed on them loads but never fires [PR #17625].
- A PHPStan rule enforces single-argument `dispatch()` [PR #17625].
- Event constructors may not receive services [PR #17640].
- Several models, repositories and events are `final`; prefer interfaces over mocks of concrete classes [PR #17536].
- `Request::get()` is removed; use `query`, `request` or `attributes` bags in code and tests [PR #17309] [PR #17347].
- The PHPStan level is unchanged; type-coverage thresholds are being raised PR by PR [PR #17766] [PR #17775].
- The 8.x snapshot does not yet contain the 7.2.1 fixes (no forward merge since 7.2.0) [PR #17253].

To keep a test working on 7.x and 8.x, subscribe by event class and, where needed, both keys guarded with `defined()`;
see mautic-upgrades-and-versions for the full porting list [code: UPGRADE-8.0.md @8.x].
