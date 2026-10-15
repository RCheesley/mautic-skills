# Mautic testing: version notes

## 5.x and 6.x
The analysis inputs record no test-tooling differences specific to 5.x or 6.x. The KB's Gitpod-based PR-testing flow and
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
- The inputs do not record test-tooling changes between 7.0, 7.1 and 7.2.

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
