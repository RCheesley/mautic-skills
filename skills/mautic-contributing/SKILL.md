---
name: mautic-contributing
description: "How to contribute to Mautic core (mautic/mautic): which branch to target (features to 7.x, bug fixes to 7.2, BC breaks to 8.x), what belongs in a patch, minor or major release, the pull request template and its Q/A rows, the pre-PR checklist (PHPUnit, PHPStan, php-cs-fixer, Rector, Twig lint), coding standards, schema-change rules (entity metadata plus migration), en_US translation keys, documentation PRs, security reporting, and official terminology and writing style (Contact not Lead, Segment not list, Landing Page). Use whenever a task says contribute, open, prepare or review a PR, write a pull request description, choose a branch, backport, bug fix vs feature, BC break, deprecation, UPGRADE-*.md, changelog, composer test/phpstan/fixcs, CI failure, phpstan-baseline, new migration, Transifex, docs PR, style guide, terminology, or touches .github/, phpstan.neon, rector.php, app/migrations/ or */Translations/en_US/."
---
# Contributing to Mautic core

## Scope
This skill covers the rules for getting a change merged into `mautic/mautic`: branch and release targeting, PR content,
the checks CI enforces, coding and schema conventions, translations, documentation, security reporting, governance
and the project's terminology. How to write tests is in mautic-testing; setting up DDEV is in mautic-dev-environment;
updater and upgrade mechanics are in mautic-upgrades-and-versions; plugin development outside core is in
mautic-plugin-development.

Terms used here: a *Contact* is a person record (code name `Lead`); a *Segment* is a contact list (code name
`LeadList`); a *BC break* is a change that breaks code or data built on a previous release of the same major.

## Expected behaviour (essentials)
Branches and releases
- Target `a.x` (now `7.x`) for features and enhancements, `a.b` (now `7.2`) for bug fixes, `c.x` (now `8.x`) for BC
  breaks. [code: .github/PULL_REQUEST_TEMPLATE.md:1-11,19-24 @7.x]
- Submit a bug fix against the lowest maintained branch where it applies; lower branches are merged upward.
  [code: .github/PULL_REQUEST_TEMPLATE.md:33-34 @7.x]
- Only 7.2.x is listed as supported; the authoritative matrix is https://www.mautic.org/mautic-releases.
  [code: .github/ISSUE_TEMPLATE/BUG-REPORT.yml:24-41 @7.x] [code: SECURITY.md:19 @7.x]
- Breaking DB changes only in majors; additive DB changes may appear in minors.
  [kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html]
  7.1.0 added 9 migrations, 7.2.0 added 13, the 7.2.1 patch none. [code: app/migrations/ @7.x]
- Cadence: bug-fix releases monthly, features quarterly, BC breaks about yearly.
  [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]
- `7.x` is not an ancestor of `8.x`; fixes reach 8.x only through periodic forward merges (last: 7.2.0 → 8.x).
  [PR #17253]
- Release notes are grouped by PR label: `bc-break`, `refactoring`, `security`, `feature`/`enhancement`,
  `bug`/`regression`; `chore` is excluded. [code: .github/release.yml @7.x]

Pull request content
- The description must keep the template's Q/A table: "Bug fix? (use the a.b branch)", "New feature/enhancement? (use the
  a.x branch)", "Deprecations?", "BC breaks? (use the c.x branch)", "Automated tests included?", "Related user
  documentation PR URL", "Related developer documentation PR URL", "Issue(s) addressed" (`Fixes #...`).
  [code: .github/PULL_REQUEST_TEMPLATE.md:19-28 @7.x]
- All PRs must maintain or improve code coverage; always add tests. [code: .github/PULL_REQUEST_TEMPLATE.md:25,32 @7.x]
- A user-docs PR is required for new features; a dev-docs PR for developer-facing changes. Promptless drafts one after
  the PR opens; the author reviews it. [code: .github/PULL_REQUEST_TEMPLATE.md:13-17,26-27 @7.x]
- `### 📋 Steps to test this PR:` must be annotated, step-by-step manual instructions for testers who may not be
  developers, with no steps the CI already performs. [code: .github/PULL_REQUEST_TEMPLATE.md:53-60 @7.x]
- List each deprecation and BC break with its alternative. [code: .github/PULL_REQUEST_TEMPLATE.md:62-64 @7.x]
- Each PR needs two human testers who Approve or Request changes (KB wording; see Pitfalls for how review works in practice).
  [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]

Checks
- Run tools through DDEV, not on the host. [code: AGENTS.md:11-14 @7.x]
- CI runs PHPUnit on PHP 8.2 and 8.5 against MySQL and MariaDB, plus PHPStan, CS Fixer (changed files), Rector dry-run,
  Twig lint, scaffold diff, `composer validate`, Codeception e2e and the api-library suite.
  [code: .github/workflows/tests.yml:22-316 @7.x] [code: .github/workflows/api-library-tests.yml:20-125 @7.x]
- PHPStan is level 6 with type-coverage floors (return 88.3 %, param 75.7 %, property 71.6 %); lowering coverage fails.
  [code: phpstan.neon:5-20 @7.x]
- Custom PHPStan rules forbid `$container->get()`, models fetched by string, repositories fetched by entity class,
  services in `Config/config.php`, nullable constructor services, commands without `#[AsCommand]`, and `Abstract*`
  classes that are not abstract. [code: phpstan.neon:257-277 @7.x]
- Rector and PHPStan fail on stale skips or unmatched suppressions. [code: rector.php:56-122 @7.x] [code: phpstan.neon:8 @7.x]

Schema, translations, security, style
- Every schema change exists twice: entity `loadMetadata()` (fresh installs and tests build schema from it) AND an
  idempotent migration (upgrades run only migrations). [code: app/bundles/InstallBundle/Install/InstallService.php:528-547 @7.x]
  [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:159 @7.x]
- Migrations extend `PreUpAssertionMigration`, use `getPrefixedTableName()` and prefixed index names, and guard each
  statement. [code: app/migrations/Migration.template @7.x] [code: app/bundles/CoreBundle/Doctrine/PreUpAssertionMigration.php:26-45 @7.x]
- Edit only `en_US` INI files; other locales come from Transifex, which CI updates from the default branch.
  [code: .github/workflows/transifex.yml @7.x]
- Translation keys are lowercase, dot-separated `mautic.<bundle>.<area>.<item>`, placeholders `%name%`.
  [code: app/bundles/LeadBundle/Translations/en_US/flashes.ini:1 @7.x]
- Report vulnerabilities privately at https://github.com/mautic/mautic/security; never in a public issue, PR, forum or
  Slack. [code: SECURITY.md:27-36 @7.x]
- GitHub issues are bug reports only; feature ideas go to the forum. [code: .github/ISSUE_TEMPLATE/config.yml @7.x]
- In prose say Contact (not Lead), Segment (not list), Landing Page (not page), Activate/Deactivate (not
  publish/unpublish); code identifiers keep `Lead`.
  [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]

Full detail with every rule numbered: references/behaviour.md.

## Where it lives
| Concern | Path(s) |
|---|---|
| PR template | `.github/PULL_REQUEST_TEMPLATE.md` |
| Issue forms | `.github/ISSUE_TEMPLATE/BUG-REPORT.yml`, `config.yml` |
| Governance | `SECURITY.md`, `MAINTAINERS.md`, `RELEASE_LEADS.md`, `.github/CONTRIBUTING.md`, `.github/CODE_OF_CONDUCT.md`, `.github/CODEOWNERS` |
| Agent guidance | `AGENTS.md` (`CLAUDE.md`, `GEMINI.md` point to it), `.agents/skills/mautic-dev/SKILL.md`, `.github/prompts/write-test.prompt.md` |
| CI | `.github/workflows/tests.yml` (main), `e2e-tests.yml`, `coverage-check.yml`, `api-library-tests.yml`, `transifex.yml`, `release.yml`, `stale.yml`; `.coderabbit.yaml`, `codecov.yml` |
| Release labels | `.github/release.yml` |
| Static analysis | `phpstan.neon`, `phpstan-baseline.neon`, `utils/phpstan/src/Rule/` |
| Refactoring | `rector.php`, `utils/rector/src/` |
| Coding standard | `.php-cs-fixer.php`, `ecs.php`, `build/hooks/pre-commit` |
| Composer scripts | `composer.json` `scripts` (test, phpstan, cs, fixcs, rector, e2e-test) |
| Migrations | `app/migrations/Version*.php`, `app/migrations/Migration.template` |
| Source strings | `app/bundles/*/Translations/en_US/*.ini`, `plugins/*/Translations/en_US/*.ini` |
| BC notes | `UPGRADE-7.0.md` (7.x), `UPGRADE-8.0.md` (8.x) |
| Release version | `app/release_metadata.json` |

All tags and the CI job table: references/code-map.md.

## How to change or extend it
Pre-PR checklist (run all; CI runs every one):
```bash
ddev composer test                                   # PHPUnit; or: ddev exec composer test <path>
ddev composer phpstan                                # warms the test container first
ddev composer cs                                     # php-cs-fixer dry run; fix with: ddev composer fixcs
ddev exec bin/rector --dry-run                       # apply with: ddev composer rector, then commit
ddev exec php bin/console lint:twig app plugins
ddev composer run e2e-test                           # for UI changes
```
[code: AGENTS.md:45-52,110-119 @7.x] [code: .github/workflows/tests.yml:245-264 @7.x]

1. Classify the change with the table in behaviour.md A.8, then branch from `7.2`, `7.x` or `8.x`.
   [code: .github/PULL_REQUEST_TEMPLATE.md:1-11 @7.x]
2. Keep BC on `7.x` and `7.2`: do not change public signatures of classes plugins extend (common controllers,
   `CommonRepository`, `AbstractPermissions`, `AbstractIntegration`, `CrmAbstractIntegration`); Rector guards them.
   Deprecate with an alternative instead of removing. [code: rector.php:26-40 @7.x]
3. Wire services by autowiring in `Config/services.php` with typed constructor dependencies (interfaces preferred).
   [code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-28 @7.x]
4. Schema change: update the entity mapping, add a migration from the template, then verify on a database without the
   change: `doctrine:migrations:execute --up 'Mautic\Migrations\VersionX'` and `doctrine:schema:update --dump-sql`
   must print nothing. Clear `var/cache` before running tests. [code: .agents/skills/mautic-dev/SKILL.md:27,46 @7.x]
5. Update together: entity + migration + API serializer + en_US translations + docs PR + `UPGRADE-*.md` for BC notes.
   [code: .github/PULL_REQUEST_TEMPLATE.md:26-27 @7.x]
6. Scaffolded root files change with their twin in `app/assets/scaffold/files/`. [code: app/composer.json:112-133 @7.x]
7. On 7.x, already avoid what 8.x removes (`*Events::CONST` subscriber keys, string service ids, `Request::get()`,
   `CacheStorageHelper`). [code: UPGRADE-8.0.md @8.x]
8. Fill every template section and label the PR for release notes. [code: .github/release.yml @7.x]

### Maintainer norms
Full PR-derived norms, with history and exceptions: references/pr-history.md.
- Two testers must approve after following your test steps. [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]
- Applying `ready-to-commit` triggers a full coverage run. [code: .github/workflows/coverage-check.yml:7-88 @7.x]
- CodeRabbit flags mock-only assertions, order- or time-dependent tests, and reviews migrations specifically.
  [code: .coderabbit.yaml:2-13 @7.x]
- SonarCloud fails duplicated new code; extract helpers. [code: .agents/skills/mautic-dev/SKILL.md:30 @7.x]
- Stale PRs close after 365 + 30 days of inactivity. [code: .github/workflows/stale.yml @7.x]
- Lower branches are merged upward regularly, so one PR against the lowest applicable branch carries the fix upward.
  [code: .github/PULL_REQUEST_TEMPLATE.md:33-34 @7.x]

## How to test it
Test-writing rules, base classes and skeletons are in mautic-testing; there is no test-patterns.md here. Essentials:
unit tests extend `PHPUnit\Framework\TestCase`, functional tests extend `MauticMysqlTestCase`; always run with
`-c app/phpunit.xml.dist`. [code: AGENTS.md:91-93 @7.x] [code: app/phpunit.xml.dist:68-73 @7.x]
Test classes are `final`, `declare(strict_types=1)`, use `#[DataProvider]` attributes, and avoid mocking objects without
service dependencies. [code: .github/prompts/write-test.prompt.md:17-23 @7.x]
Migrations are not exercised by functional tests; unit-test them like
`app/bundles/CoreBundle/Tests/Unit/Doctrine/CampaignLeadEventLogIndexMigrationTest.php`. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:159 @7.x]
Custom PHPStan rules have their own tests in `utils/phpstan/tests/Rule/`. [code: phpstan.neon:257-277 @7.x]
A good contribution test fails before the change and passes after it, through the real route or command.
[code: .github/prompts/write-test.prompt.md:17-18 @7.x]

## Version notes
- 5.x introduced `Config/services.php` autowiring; 6.0 removed `MauticFactory`; 7.0 requires PHP 8.2, MySQL 8.4,
  MariaDB 10.11 and removed the browser updater. [code: UPGRADE-5.0.md @7.x] [code: UPGRADE-6.0.md @7.x] [code: UPGRADE-7.0.md @7.x]
- 7.0.0 2026-01-20, 7.1.0 2026-04-14, 7.2.0 2026-09-02, 7.2.1 2026-09-23; no UPGRADE file for minors.
  [code: git tag @7.x]
- 8.x: PHP 8.4, Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4, PHPUnit 13, ECS only (php-cs-fixer removed), tools in
  `vendor/bin/`, event dispatch by class enforced by PHPStan, entity mapping moving to attributes.
  [PR #16993] [PR #17392] [PR #17361] [PR #17004] [PR #17280] [PR #17164] [PR #17625] [PR #17382]
- 8.x is unreleased: `app/release_metadata.json@8.x` still says 7.2.0. [code: app/release_metadata.json @8.x]
- 4.4/5.x era: fix 5.x first, then a duplicate backport PR; classic merge-up branching restored in January 2024.
  [PR #11644] [PR #11676] [PR #11775] [PR #13110]
- 5.0: security reports moved from huntr.dev to GitHub private reporting; supported versions moved to mautic.org.
  [PR #12876] [PR #12877]
- 5.x chose php-cs-fixer over ECS; ECS rules reappeared in 7.2. [PR #13037] [PR #16344] [PR #16723]
- 7.2: Promptless docs PRs and `code-review-passed`/`user-testing-passed`/`ready-to-commit` labels; builder `dist`
  no longer committed in PRs. [PR #16337] [PR #16435] [PR #16480]
Details: references/version-notes.md.

## Pitfalls
- The PR template's hidden comment says features go to "4.x" and gives "(e.g. 7.x)" as the c.x example; both are stale.
  Features go to 7.x, BC breaks to 8.x. [code: .github/PULL_REQUEST_TEMPLATE.md:11,35 @7.x]
- `AGENTS.md` says bundle services live in `config.php`; PHPStan `NoServicesInBundleConfigRule` rejects that. Use
  `Config/services.php`. [code: AGENTS.md:70 @7.x] [code: phpstan.neon:257-277 @7.x]
- CI's CS check covers only changed files and never runs ECS, so `composer cs` locally can report old violations; fix
  only what you touched. [code: .github/workflows/tests.yml:256-264 @7.x]
- A green functional test suite does not prove a migration works: tests build schema from metadata and mark migrations
  as run. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:159 @7.x]
- `preUp()` skips only when every assertion is true; one false assertion runs all of `up()`. [code: app/bundles/CoreBundle/Doctrine/PreUpAssertionMigration.php:26-45 @7.x]
- Raw-SQL index names without the table prefix diverge from fresh installs. [code: app/migrations/Version20250415142826.php:24 @7.x]
- PHPStan tolerates uses of Mautic's own deprecated classes; a clean run does not mean no deprecated API.
  [code: phpstan.neon:42-239 @7.x]
- `rector/rector` is `dev-main`: new findings can appear after a rebase. [code: composer.json:28-54 @7.x]
- Coverage is not measured on PRs; Codecov's patch target is 0 %. [code: .github/workflows/tests.yml:36-44 @7.x] [code: codecov.yml:7-13 @7.x]
- Testing environment and credentials disagree: the template says GitHub Codespaces; the KB says Gitpod with admin/mautic;
  fixtures use `Maut1cR0cks!`. [code: .github/PULL_REQUEST_TEMPLATE.md:59 @7.x]
  [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]
- Security report links differ between `SECURITY.md`, `.github/CONTRIBUTING.md` and `MAINTAINERS.md`; all say report
  privately. Use the GitHub security tab. [code: SECURITY.md:32 @7.x] [code: .github/CONTRIBUTING.md:3 @7.x]
- Stale governance: README links the `6.x` branch, `RELEASE_LEADS.md` lacks 7.1/7.2, `CODEOWNERS` names a former
  maintainer. [code: README.md:17 @7.x] [code: RELEASE_LEADS.md @7.x] [code: .github/CODEOWNERS @7.x]
- The UI still says "Published" where the style guide says "Active"; quote on-screen labels exactly in test steps.
  [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]
- Open question: whether e2e tests are required for every UI PR. [unverified]
- "Two testers" is the KB wording; in practice a PR needs one code review plus one user test from another
  organisation, the author cannot approve, and more than a one- or two-line fix needs two approvals. Test- or CI-only
  PRs merge with one approval on green CI. [PR #13754] [PR #12128] [PR #16877] [PR #11045] [PR #14499]
- A bug fix without a regression test that fails before the fix stalls in review; reviewers ask for functional tests
  through the real route or command. [PR #15822] [PR #17627] [PR #11644] [PR #14503]
- A new option's default keeps the old behaviour; behaviour changes in a minor are opt-in, and default changes never
  go into a patch. [PR #3549] [PR #6422] [PR #8959] [PR #14678] [PR #14790]
- Do not treat the 7.2.0 `final` sweep as precedent for BC changes in a minor: it is a recorded exception. Extend core
  through events, interfaces and decoration, not inheritance. [PR #16754] [PR #16898] [PR #13842] [PR #14016]
- Merge-up covers only `a.b` → `a.x`. A fix for an older major, or a CI or DDEV fix for every maintained line, needs
  its own PR titled with the branch (`[6.0]`). [PR #15560] [PR #15561] [PR #10597] [PR #11969]

## Related skills
- mautic-testing — writing PHPUnit and Codeception tests, base classes, fixtures, assertions.
- mautic-dev-environment — DDEV setup, credentials, running commands, caches.
- mautic-architecture — bundles, services, events, entities; where a change belongs.
- mautic-upgrades-and-versions — migrations catalogue, updater, release metadata, 7→8 porting and dual-version code.
- mautic-plugin-development — building plugins outside core (plugin schema, `MINIMUM_MAUTIC_VERSION`).

## Reference files
- references/behaviour.md — every rule numbered (branches, PR template, CI, PHPStan rules, Rector, schema, translations, docs, security, governance, style) and the contradiction list; open before preparing or reviewing a PR.
- references/code-map.md — governance files, CI workflows and tooling config files with what each enforces.
- references/docs-digest.md — Community Handbook, KB and docs-repo guidance with URLs and procedures.
- references/terminology.md — full FeatureList, Google WordList and accepted-vocabulary tables; open when writing docs, UI strings or PR text.
- references/version-notes.md — history behind the rules, 7.x minors and the 8.x tooling delta.
- references/pr-history.md — maintainer norms from merged PRs: branch and release policy, BC and deprecation, review and merge rules, testing, schema, docs, translations, and the norms that changed over time; open when a rule's reason or exception matters.
