# Mautic contributing: rules and norms (full specification)

Authoritative for Mautic 7.x (upstream `7.x` at `419a08a9b35`: release 7.2.1 plus 87 unreleased merged PRs). `@7.x` tags point at that tree;
`@8.x` tags point at upstream `8.x` at `11599729491`. Every numbered rule carries a source tag.

## Contents
- A. Branches, versions and what goes where
- B. Pull request content (the template)
- C. Pre-PR checklist and what CI runs
- D. Coding standards
- E. PHPStan: configuration and custom rules
- F. Rector
- G. Service wiring and class conventions enforced by tooling
- H. Schema changes (entity metadata AND migration)
- I. Translations
- J. Assets and scaffolded files
- K. Documentation expectations
- L. Security reporting
- M. Issues, reviews, labels and governance
- N. Terminology and writing style
- O. Tests (summary; detail in mautic-testing)
- P. Contradictions and open questions

---

## A. Branches, versions and what goes where

A.1 Branch roles. `a` is the current major, `b` the current minor, `c` the future major. `a.x` takes features and
enhancements, `a.b` takes bug fixes, `c.x` takes changes with backward-compatibility (BC) breaks.
[code: .github/PULL_REQUEST_TEMPLATE.md:1-11 @7.x]

A.2 Current mapping (2026-10): `7.x` is the default branch and takes features; `7.2` is the newest maintenance branch for
bug fixes (older `7.1`, `7.0`, `6.0`, `5.2` branches also exist); `8.x` is the next major and takes BC breaks.
[code: .github/PULL_REQUEST_TEMPLATE.md:1-11 @7.x] (branch list from `git branch -a`, recorded in
analysis migrations-upgrades-releases §9.C.3)

A.3 Submit a bug fix against the lowest maintained branch where it applies. Lower branches are merged upward regularly,
so upper branches receive the fix. [code: .github/PULL_REQUEST_TEMPLATE.md:30-36 @7.x]

A.4 Only the 7.2.x series is listed as supported in the bug-report form; 7.1.x, 7.0.x, 6.0.x, 5.x, 4.x and 3.3.x are
labelled "(not supported)". The authoritative support matrix is https://www.mautic.org/mautic-releases.
[code: .github/ISSUE_TEMPLATE/BUG-REPORT.yml:24-41 @7.x] [code: README.md:77 @7.x] [code: SECURITY.md:17-21 @7.x]
In practice a non-security bug fix today targets `7.2`.

A.5 Semantic versioning: breaking database changes only in majors; additive database changes may appear in minors.
[kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html]

A.6 Observed release content confirms A.5: 7.1.0 added 9 migrations and 7.2.0 added 13, while the 7.2.1 patch release
added none. Treat a migration in a patch-branch PR as exceptional and justify it in the PR description.
[code: app/migrations/ @7.x] (per-tag catalogue in analysis migrations-upgrades-releases §9.A.20)

A.7 Release cadence: bug-fix releases monthly, feature releases quarterly, breaking changes about once a year.
[kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]

A.8 What may go where (synthesis of A.1-A.7):

| Change | Branch | Release type |
|---|---|---|
| Bug fix, regression fix, no new behaviour, no schema change | lowest maintained `a.b` (now `7.2`) | patch `a.b.Z` |
| Feature, enhancement, new option, new event, additive schema change (new column/table/index) | `a.x` (now `7.x`) | minor `a.Y.0` |
| Deprecation (old API kept working, alternative added) | `a.x` | minor |
| Removal of deprecated code, signature change, renamed/removed service, event constant, route, column or config key, platform bump | `c.x` (now `8.x`) | major |

[code: .github/PULL_REQUEST_TEMPLATE.md:9-11,22-24 @7.x]
[kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html]
The project's definition of a BC break is linked from the in-repo agent skill as
https://contribute.mautic.org/en/latest/contributing/developer.html#backward-compatibility-breaks (not digested here).
[code: .agents/skills/mautic-dev/SKILL.md:51 @7.x]

A.9 Tags are `X.Y.Z` plus pre-releases `X.Y.0-alpha`, `-beta`, `-rc`, `-rc2`. Observed: 7.0.0 on 2026-01-20, 7.1.0 on
2026-04-14, 7.2.0 on 2026-09-02, 7.2.1 on 2026-09-23. [code: git tag @7.x] (analysis §9.C.4)

A.10 Releasing: the pushed tag must equal `app/release_metadata.json` `version`, so `version` and `announcement_url` are
bumped before tagging; the workflow builds a DRAFT GitHub release and tests a fresh install and an update from
`minimum_mautic_version`. [code: .github/workflows/release.yml:38-47,77-103,184-250 @7.x]

A.11 Release notes are grouped by PR labels: `bc-break` (Breaking Changes), `refactoring`, `security`,
`feature`/`enhancement`, `bug`/`regression`; `chore` and `github-actions` are excluded. Label PRs accordingly.
[code: .github/release.yml @7.x]

A.12 There are no `UPGRADE-7.1.md` or `UPGRADE-7.2.md` files; BC notes for a major go in `UPGRADE-<major>.0.md`
(`UPGRADE-7.0.md` on 7.x, `UPGRADE-8.0.md` on 8.x, appended per PR). [code: UPGRADE-7.0.md @7.x]
[code: UPGRADE-8.0.md @8.x]

A.13 Branch topology: `7.x` is not an ancestor of `8.x`. The last forward merge was 7.2.0 → 8.x ([PR #17253], which
resolved 138 conflicting files); 736 commits of 7.x work (the 7.2.1 release plus unreleased PRs merged after it) were not yet on 8.x on 2026-10-15. A 7.x fix is not on 8.x
until the next forward merge. (analysis 8x-changes header and §8) [PR #17253]

A.14 Keep a fork in sync by rebasing on `upstream/7.x` (or the branch you target) and force-pushing your branch;
resolve conflicts with `git add` and `git rebase --continue`.
[kb: https://kb.mautic.org/article/how-to-rebase-branch-and-sync-forked-repository-with-upstream-using-git.html]

## B. Pull request content (the template)

B.1 The PR description must contain this Q/A table, verbatim rows, answered with ✔️ or ❌:
[code: .github/PULL_REQUEST_TEMPLATE.md:19-28 @7.x]

```
| Q                                      | A
| -------------------------------------- | ---
| Bug fix? (use the a.b branch)          | ✔️❌
| New feature/enhancement? (use the a.x branch)      | ✔️❌
| Deprecations?                          | ✔️❌
| BC breaks? (use the c.x branch)        | ✔️❌
| Automated tests included?              | ✔️❌ <!-- All PRs must maintain or improve code coverage -->
| Related user documentation PR URL      | mautic/user-documentation#... <!-- required for new features -->
| Related developer documentation PR URL | mautic/developer-documentation-new#... <!-- required for developer-facing changes -->
| Issue(s) addressed                     | Fixes #... <!-- prefix each issue number with "Fixes #", no need to create an issue if none exists, explain below instead -->
```

B.2 "Automated tests included?": all PRs must maintain or improve code coverage, and contributors must always add tests
and ensure they pass. [code: .github/PULL_REQUEST_TEMPLATE.md:25,32 @7.x]

B.3 "Related user documentation PR URL" is required for new features; "Related developer documentation PR URL" is
required for developer-facing changes. [code: .github/PULL_REQUEST_TEMPLATE.md:26-27 @7.x]

B.4 "Issue(s) addressed": prefix each issue with `Fixes #`. No issue is needed; explain in the description instead.
[code: .github/PULL_REQUEST_TEMPLATE.md:28 @7.x]

B.5 `## Description`: "a short README for your feature/bugfix". For a bug with no linked issue, give the steps to
reproduce. An optional Before/After screenshot table is provided as an HTML comment.
[code: .github/PULL_REQUEST_TEMPLATE.md:38-50 @7.x]

B.6 `### 📋 Steps to test this PR:` is mandatory in practice: "write very clear, annotated and step by step test
instructions. Do not assume any previous knowledge - testers may not be developers. Do not write steps performed by
the CI. These steps are for manual testing." Step 1 is pre-filled: open the PR in GitHub Codespaces or pull it locally
(https://contribute.mautic.org/contributing-to-mautic/tester). [code: .github/PULL_REQUEST_TEMPLATE.md:53-60 @7.x]

B.7 List every deprecation and BC break at the end of the description together with its new alternative.
[code: .github/PULL_REQUEST_TEMPLATE.md:62-64 @7.x]

B.8 After the PR opens, Promptless automatically creates a documentation PR and comments the link. Once the code PR
merges, the author reviews that documentation PR, requests changes if needed and approves it promptly.
[code: .github/PULL_REQUEST_TEMPLATE.md:13-17 @7.x]
[docs: https://contribute.mautic.org/en/latest/contributing/developer.html#reviewing-documentation-prs-from-promptless]

## C. Pre-PR checklist and what CI runs

C.1 Run commands through DDEV (`ddev exec php bin/phpunit -c app/phpunit.xml.dist ...`, `ddev exec php bin/console ...`,
`ddev composer ...`), not on the host, unless the user asks. [code: AGENTS.md:11-14 @7.x]

C.2 The documented PR checklist is `ddev composer test`, `ddev composer phpstan`, `ddev composer cs`, plus
`ddev composer run e2e-test` for UI changes. [code: AGENTS.md:110-119 @7.x]

C.3 CI runs more than C.2, so also run these before pushing: [code: .github/workflows/tests.yml:181-316 @7.x]

| Check | Local command | CI job |
|---|---|---|
| PHPUnit (all suites) | `ddev composer test` (or `ddev exec composer test <path>`) | `phpunit`, 4-cell PHP × DB matrix |
| PHPStan level 6 + type coverage | `ddev composer phpstan` | `misc` / PHPSTAN |
| php-cs-fixer | `ddev composer cs` (fix with `ddev composer fixcs`) | `misc` / CS Fixer (changed files only) |
| Rector | `ddev exec bin/rector --dry-run` (apply with `ddev composer rector`) | `misc` / Rector |
| Twig lint | `ddev exec php bin/console lint:twig app plugins` | `misc` / Twig Lint |
| Scaffolded file twins | edit both copies (J.2) | `misc` / scaffolded files mismatch |
| Composer validity | `ddev composer validate` | `misc` / composer lock check |
| Composer-project install | — | `misc` / composer install |
| Codeception e2e | `ddev composer run e2e-test` | `e2e-tests` job |
| API library suite | — | `api-library-tests.yml` |

C.4 PHPUnit matrix: PHP 8.2 with MySQL 8.4 and MariaDB 10.11; PHP 8.5 with MySQL 9.2 and MariaDB 11.4. Every suite runs
on every cell; there is no sharding. [code: .github/workflows/tests.yml:22-32,111-121 @7.x]

C.5 Coverage is collected only on pushes and scheduled runs (PHP 8.2 + MariaDB 10.11), never on pull requests. Codecov
patch target is 0 %, so uncovered new lines do not fail a PR on their own, but total coverage must not drop.
[code: .github/workflows/tests.yml:36-44,117-130 @7.x] [code: codecov.yml:7-13 @7.x]

C.6 Applying the `ready-to-commit` or `check-coverage` label triggers a full coverage run (about 20 minutes).
[code: .github/workflows/coverage-check.yml:7-88 @7.x]

C.7 Changes under `tests/` (Codeception) trigger a workflow that runs the e2e suite 10 times with `fail-fast: true` to
catch flaky tests. [code: .github/workflows/e2e-tests.yml:25-28 @7.x]

C.8 CI's CS Fixer job checks only PHP files changed in the PR; ECS is not run in CI. `composer cs` locally checks the
whole tree; `composer fixcs` runs php-cs-fixer and ECS with `--fix`. [code: .github/workflows/tests.yml:256-264 @7.x]
[code: composer.json:166-214 @7.x]

C.9 Install the git hooks with `composer githooks` (run by `post-install-cmd`): the pre-commit hook fixes style on staged
files. [code: composer.json:166-214 @7.x]

C.10 `composer phpstan` first boots the test kernel so `var/cache/test/AppKernelTestDebugContainer.xml` exists; without it
PHPStan fails. After adding a plugin entity, clear `var/cache/prod` and `var/phpstan-cache`.
[code: composer.json:166-214 @7.x] [code: phpstan.neon:249-254 @7.x] [code: .agents/skills/mautic-dev/SKILL.md @7.x]

C.11 CodeRabbit reviews every PR, with path instructions for PHP, `**/Tests/**` (prefer `MauticMysqlTestCase` for DB
behaviour, flag mock-only assertions, order- or time-dependent tests) and `app/migrations/*.php`.
[code: .coderabbit.yaml:2-13 @7.x]

C.12 SonarCloud fails on duplicated new code; extract a helper rather than copying near-identical test methods.
[code: .agents/skills/mautic-dev/SKILL.md:30 @7.x]

C.13 `rector/rector` is pinned to `dev-main`, so new Rector findings can appear after a rebase without any Mautic change.
[code: composer.json:28-54 @7.x]

## D. Coding standards

D.1 PHP 8.2+, `declare(strict_types=1)`, PSR-12/Symfony style, 4-space indent, short array syntax, ordered imports,
explicit types and nullable hints, minimal DocBlocks. [code: AGENTS.md:95-101 @7.x]

D.2 php-cs-fixer rules: `@Symfony`; aligned `=>` and `=` accepted; `ordered_imports`; short `array_syntax`;
`no_unused_imports`; empty `header_comment`; `nullable_type_declaration_for_default_null_value`; `no_superfluous_phpdoc_tags`
with `allow_mixed`. Scope: `app/bundles`, `app/config`, `app/middlewares`, `app/migrations`, `plugins`, `tests`, `utils`.
[code: .php-cs-fixer.php:5-57 @7.x]

D.3 ECS adds the `comments`, `docblocks`, `namespaces`, `cleanup`, `controlStructures` and `standaloneLine` sets; Yoda style,
concat spacing and method-chaining fixers are skipped. [code: ecs.php:7-43 @7.x]

D.4 Fix types rather than suppressing: inline `@phpstan-ignore` and new `ignoreErrors` entries are a last resort
(see E.3). [code: phpstan.neon:42-239 @7.x]

D.5 Test classes are `final`, declare strict types, end in `Test`, and abstract shared bases are named
`Abstract…TestCase`. [code: .github/prompts/write-test.prompt.md:19 @7.x]

## E. PHPStan: configuration and custom rules

E.1 Level 6; paths `app/bundles`, `app/migrations`, `plugins`, `utils`; `treatPhpDocTypesAsCertain: false`.
[code: phpstan.neon:5-35 @7.x]

E.2 Type-coverage floors: return 88.3 %, param 75.7 %, property 71.6 %, constant 3, declare 73. Lowering overall type
coverage fails the run. [code: phpstan.neon:14-20 @7.x]

E.3 `phpstan-baseline.neon` (about 2040 entries) is generated; regenerate with `composer phpstan-baseline`. Hand-written
suppressions go in `phpstan.neon` `ignoreErrors` with `identifier` and `path`, or inline. An obsolete suppression fails
the run (`reportUnmatchedIgnoredErrors` default true). Never commit a broader exclusion.
[code: phpstan.neon:1-2,8,42-239 @7.x] [code: composer.json:184 @7.x]

E.4 Uses of Mautic's own deprecated classes are tolerated by `ignoreErrors` (`*.deprecated*` whose message matches
`class\s+Mautic`). Do not read a clean PHPStan run as "no deprecated API used". [code: phpstan.neon:42-239 @7.x]

E.5 Custom rules (in `utils/phpstan/src/Rule/`, tests in `utils/phpstan/tests/Rule/`), with the message each emits:
[code: phpstan.neon:257-277 @7.x] [code: utils/phpstan/src/Rule/ @7.x]

| Rule | Fails when |
|---|---|
| `AbstractClassNameMustBeAbstractRule` | a class named `Abstract*` is not declared abstract |
| `NoTablePrefixDefinitionInTestsRule` | a test defines `MAUTIC_TABLE_PREFIX` |
| `AutowireMethodNameMustMatchClassRule` | a `#[Required]` method is not named `autowire<ClassName>()` |
| `NoGetModelWithStringInControllerRule` | a controller fetches a model by string |
| `NoRequiredMethodWithConstructorInControllerRule` | a controller has both its own constructor and a `#[Required]` method |
| `CommandMustHaveAsCommandAttributeRule` | a `Command` subclass lacks `#[AsCommand]` |
| `ConstraintMustHaveAttributeRule` | a `Constraint` subclass lacks `#[\Attribute]` |
| `NoNullableServiceInConstructorRule` | a constructor service parameter is nullable |
| `NoGetRepositoryWithEntityInRepositoryRule`, `NoEntityManagerGetRepositoryRule` | a repository or the entity manager fetches a repository by entity constant |
| `NoContainerGetRule` | code calls `$container->get(...)`; in tests, a string service id is used instead of a class constant |
| `PreferInterfaceInConstructorRule` | a constructor dependency is typed as a concrete class that has an interface |
| `NoPropertyToPropertyAssignRule` | `$this->a = $this->b` |
| `ControllerMethodMustReturnResponseRule` | a controller action does not return a `Response` (alone or in a union) |
| `NoServicesInBundleConfigRule` | `Config/config.php` defines services |
| `NoParentConstructorForwardingRule` | a constructor only forwards parameters to `parent::__construct()` |
| `NoServiceJugglingRule` | a service property is passed as an argument to another method |
| Symplify `NoJustPropertyAssignRule` | (enabled) |

E.6 Present but not registered: `NoObjectPropertyAssignToVariableInTestsRule`, `NoServiceInMethodParameterRule`,
`NoUnusedServiceAliasRule` (commented out). [code: phpstan.neon:275 @7.x]

## F. Rector

F.1 Paths `app/bundles`, `plugins`; sets `deadCode`, `typeDeclarations`, `phpunitCodeQuality`, `phpunitMockToStub`,
`phpunitNarrowAsserts`, `privatization`, `codeQuality`, PHP sets from composer (8.2). Custom rectors
`UnserializeToSerializerDecodeRector` and `ModelGetRepositoryToRepositoryServiceRector`. [code: rector.php:10-55 @7.x]

F.2 `withTypeGuardedClasses` protects the signatures of the common controllers, `CommonRepository`, `AbstractPermissions`,
`AbstractIntegration` and `CrmAbstractIntegration`, because plugins extend them. [code: rector.php:26-40 @7.x]

F.3 `reportUnusedSkips()` is on: a skip entry that no longer matches fails. Add skips sparingly.
[code: rector.php:56-122 @7.x]

F.4 Run `ddev composer rector` (rewrites files) and commit the result; CI runs `bin/rector --dry-run`.
[code: .github/workflows/tests.yml:250-253 @7.x]

## G. Service wiring and class conventions enforced by tooling

G.1 Register services by autowiring in `Config/services.php`, not in the `services` key of `Config/config.php`
(`NoServicesInBundleConfigRule`). `Config`, `Entity`, `Event`, `Exception`, `Migrations`, `Security`, `Test`, `Tests`,
`Views`, `DTO`, `DataObject`, `Crate` and `DependencyInjection` are excluded from autowiring.
[code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-28 @7.x]

G.2 Inject typed constructor dependencies, preferring interfaces; never `$container->get()`, `getModel('string')` or
`$em->getRepository(Entity::class)` in controllers or repositories. [code: phpstan.neon:257-277 @7.x]

G.3 Controllers inheriting `CommonController`'s constructor add dependencies through a
`#[Required] public function autowire<ClassName>()` method, not by redeclaring the constructor.
[code: utils/phpstan/src/Rule/ @7.x] (analysis dev-tooling-testing §6.29)

G.4 Every console command has `#[AsCommand(name: ..., description: ...)]`; every validator constraint has `#[\Attribute]`.
[code: phpstan.neon:257-277 @7.x]

G.5 New 7.x code should already avoid what 8.x removes: `*Events::CONST` as subscriber keys or as the second
`dispatch()` argument, `CacheStorageHelper`, `Core\Controller\FormController`, `services`/`menus`/`models` arrays in
`config.php`, string service ids, `Request::get()`, `$this->_em` in repositories, constraint option arrays.
[code: UPGRADE-8.0.md @8.x] (list from analysis 8x-changes §7)

## H. Schema changes (entity metadata AND migration)

H.1 Fresh installs and functional tests build the schema from ORM metadata (`SchemaTool`) and mark every migration as
executed without running it; existing installs change only through migrations. Every schema change must therefore exist
twice, with identical names and types: in the entity's `loadMetadata()` and in a migration.
[code: app/bundles/InstallBundle/Install/InstallService.php:528-547 @7.x]
[code: app/bundles/InstallBundle/Helper/SchemaHelper.php:142 @7.x]
[code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:159 @7.x]

H.2 Entity side: `public const TABLE_NAME`, `loadMetadata()` with `ClassMetadataBuilder` (`setTable(self::TABLE_NAME)`,
`createField()->columnName()`, `addIndex()`, `addNullableField`, `addUuid`, `addVersionField`).
[code: app/bundles/EmailBundle/Entity/Email.php:85,366-470 @7.x]
[code: app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php:162-441 @7.x]

H.3 Migration side: generate with `doctrine:migrations:generate` from `app/migrations/Migration.template`: `final class
Version<YYYYMMDDHHMMSS>` in `app/migrations/`, namespace `Mautic\Migrations`, extending `PreUpAssertionMigration`, with
`protected const TABLE_NAME` and one `skipAssertion()` per SQL change. [code: app/migrations/Migration.template @7.x]
[code: app/config/config.php:225-236 @7.x]

H.4 `preUp()` skips only when ALL assertions are true; if one is false the whole `up()` runs, so guard each statement in
`up()` (for example `if (!$table->hasColumn(...))`). [code: app/bundles/CoreBundle/Doctrine/PreUpAssertionMigration.php:26-45 @7.x]
[code: app/migrations/Version20240228132306.php:17-40 @7.x]

H.5 Reference tables through the prefix (`$this->getPrefixedTableName()` or `$this->prefix.'table'`); prefix raw-SQL index
names too (`{$this->prefix}idx_...`), because ORM index names are prefixed at metadata load.
[code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:71-74,194-201 @7.x]
[code: app/migrations/Version20250415142826.php:24 @7.x]
[code: app/bundles/CoreBundle/EventListener/DoctrineEventsSubscriber.php:36-80 @7.x]

H.6 Compute Doctrine-generated IDX/FK names with `generatePropertyName($table, 'idx'|'fk', [$columns])`; match FK column
signedness with `getColumnTypeSignedOrUnsigned()`. [code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:153-214 @7.x]

H.7 A migration that adds an index to `leads` must check the 64-index limit (`IndexHelper::MAX_COUNT_ALLOWED`).
[code: app/migrations/Version20260629065551.php:14-19 @7.x]

H.8 The timestamp is the authoring date; Doctrine runs every unrecorded migration regardless of date, so older-dated
files still execute on upgrade (for example `Version20220104115633` first shipped in 7.1.0). This is why idempotency guards
are mandatory. [code: app/migrations/Version20220104115633.php @7.x]

H.9 Data-only migrations that emit no SQL call `suppressNoSQLStatementError()`. Only MySQL-family platforms are supported.
[code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:34,185-188 @7.x]

H.10 `down()` is not exercised by the updater; implement it anyway (most migrations do).
[code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:61-64 @7.x]

H.11 Verify a migration manually, because functional tests never run it: on a database that does NOT yet have the
change, run `doctrine:migrations:execute --up 'Mautic\Migrations\VersionX'`, then `doctrine:schema:update --dump-sql`
must print nothing for the entities you changed. On a database that already has the change the pre-up assertions skip
the migration and the check proves nothing. Unit-test it by building a `Schema` and asserting `preUp` skip and `up` SQL.
[code: .agents/skills/mautic-dev/SKILL.md:27,46 @7.x]
[code: app/bundles/CoreBundle/Tests/Unit/Doctrine/CampaignLeadEventLogIndexMigrationTest.php @7.x]

H.12 After changing an entity, `ddev exec rm -rf var/cache` so the cached test schema dumps regenerate.
[code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:202-213 @7.x]

H.13 Plugins do not use `app/migrations`; they use `PluginDatabase::installPluginSchema()` and
`PluginEvents::ON_PLUGIN_UPDATE` / `ON_PLUGIN_INSTALL`. [code: UPGRADE-6.0.md:27-33 @7.x]

H.14 Update together with a schema change: entity mapping, migration, API serializer groups, translations for new labels,
user or developer docs PR. (synthesis of B.3 and H.1)

H.15 8.x: entity mapping is moving from `loadMetadata()` to `#[ORM\*]` attributes (the hybrid driver reads attributes
first) and Doctrine is ORM 3.7 / DBAL 4.4. [PR #17382] [PR #17454] [PR #17361] [code: app/composer.json @8.x]

## I. Translations

I.1 Edit only `en_US` files. Only en_US lives in the repo; other locales are language packs from Transifex. en_US INI
changes on the default branch are pushed to Transifex by CI. [code: .github/workflows/transifex.yml @7.x]
[code: app/bundles/CoreBundle/Helper/LanguageHelper.php:61-122 @7.x]

I.2 Location and domain: `<Bundle>/Translations/en_US/<domain>.ini`; the file name is the Symfony domain: `messages`,
`flashes`, `validators`, `javascript` (and `fixtures` in InstallBundle).
[code: app/bundles/CoreBundle/Loader/TranslationLoader.php @7.x]

I.3 Format: one `key="value"` per line (parsed with `parse_ini_string`). A corrupt file throws in `dev` and is silently
skipped otherwise. [code: app/bundles/CoreBundle/Loader/TranslationLoader.php @7.x]

I.4 Keys: dot-separated, lowercase, `mautic.<bundle>.<area>.<item>` (for example `mautic.lead.customfield.notblank`).
Exceptions exist (`marketplace.*`, `project.*`, `grapesjsbuilder.*`); new core keys use the `mautic.` prefix.
[code: app/bundles/LeadBundle/Translations/en_US/messages.ini @7.x]

I.5 Placeholders `%name%`; plurals with Symfony interval syntax `"{0} …|{1} …|]1,Inf[ %count% …"`.
[code: app/bundles/LeadBundle/Translations/en_US/flashes.ini:1 @7.x]

I.6 JavaScript strings go in the `javascript` domain; missing JS keys fall back to English.
[code: app/bundles/CoreBundle/Translation/Translator.php:111-125 @7.x]

I.7 Templates translate keys with `{% trans %}key{% endtrans %}` (or the translator service in PHP); add the key to the
en_US INI rather than writing literal UI text. [code: UPGRADE-PHP-TO-TWIG-TEMPLATES.md:41,97 @7.x]

## J. Assets and scaffolded files

J.1 After touching bundle `Assets/js|css` run `ddev composer generate-assets`; after CKEditor sources `npm run build`;
after the GrapesJS plugin `ddev gjs-build`. Generated files are gitignored and must not be committed.
[code: .gitignore:66-105 @7.x] [code: AGENTS.md:54-58 @7.x]

J.2 Root scaffolded files (`.env`, `.gitignore`, `webpack.config.js`, `importmap.php`, `package.json`,
`package-lock.json`, `tsconfig.json`, `index.php`, `.htaccess`, `robots.txt`, `bin/console`, `patches/*`) change together
with their twin in `app/assets/scaffold/files/`. [code: app/composer.json:112-133 @7.x]
[code: .github/workflows/tests.yml:265-277 @7.x]

## K. Documentation expectations

K.1 User docs live in `mautic/user-documentation` (docs.mautic.org); developer docs in `mautic/developer-documentation-new`
(devdocs.mautic.org). Docs are reStructuredText. [code: .github/PULL_REQUEST_TEMPLATE.md:26-27 @7.x]
[code: .github/CONTRIBUTING.md:13-15 @7.x] [docs: https://github.com/mautic/user-documentation/blob/7.2/style-guide.md]

K.2 New features need a user-docs PR; developer-facing changes (events, services, APIs, plugin hooks) need a dev-docs
PR. Promptless drafts one automatically; the author reviews it. [code: .github/PULL_REQUEST_TEMPLATE.md:13-17,26-27 @7.x]

K.3 Both docs repos lint with Vale (`Vale`, `Google`, `Mautic` styles, minimum level suggestion, vocabulary `Mautic`).
[docs: https://github.com/mautic/user-documentation/blob/7.2/.vale.ini]

K.4 BC breaks and removals go in `UPGRADE-<major>.0.md`; for 8.x, devdocs adds a porting guide
(https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html). [code: UPGRADE-8.0.md @8.x]

K.5 Knowledge Base articles follow Diataxis (tutorial, how-to or troubleshooting) and are reviewed by the Education
Team. [kb: https://kb.mautic.org/article/how-to-contribute-to-the-knowledge-base.html]

## L. Security reporting

L.1 Report privately through the repository's security tab (https://github.com/mautic/mautic/security). Never in a public
issue, PR, forum post or Slack. A private fork may carry the fix. [code: SECURITY.md:27-36 @7.x]

L.2 Coordinated disclosure: issues stay private until a fix is released. Do not share details with others.
[code: SECURITY.md:61-66 @7.x]

L.3 Advisories cover only stable releases of supported majors (no alphas, betas or RCs). Fixes go to all affected supported
versions. Out-of-sequence security releases get at least two weeks' notice. ELTS (paid, up to two years) covers versions
past security support. [code: SECURITY.md:16-25,48-50 @7.x]

L.4 Scope: Mautic core, officially supported plugins and resources, and *.mautic.org; not third-party plugins or individual
instances. [code: SECURITY.md:11-14 @7.x]

L.5 An agent that finds a vulnerability must not open a public PR or issue for it; report it and stop.
[code: SECURITY.md:34 @7.x]

## M. Issues, reviews, labels and governance

M.1 GitHub issues are bug reports only (`blank_issues_enabled: false`); support questions go to the forum `c/support` and
feature ideas to forum `c/ideas`. Bug reports require series, exact version, install method, PHP version, what happened,
reproduction steps and Code of Conduct confirmation. [code: .github/ISSUE_TEMPLATE/config.yml @7.x]
[code: .github/ISSUE_TEMPLATE/BUG-REPORT.yml:24-111 @7.x]

M.2 Each PR needs testing by two people, who Approve or Request changes after following the test steps.
[kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]

M.3 Stale bot: PRs go stale after 365 days and close 30 days later; issues after 90 and 14 days; `security`, `legacy`,
`bounty` and milestoned items are exempt. [code: .github/workflows/stale.yml @7.x]

M.4 Governance files: `MAINTAINERS.md` (Project Lead and Core Team maintainers), `SECURITY.md`, `RELEASE_LEADS.md`,
`.github/CONTRIBUTING.md`, `.github/CODE_OF_CONDUCT.md`, `.github/SUPPORT.md`, `.github/CODEOWNERS`, `AGENTS.md`
(single source for coding agents; `CLAUDE.md` and `GEMINI.md` point to it). Maintainer duties are defined in the
governance model at https://contribute.mautic.org/governance/governance#6-2-1-expectations-and-duties-of-maintainers.
[code: MAINTAINERS.md @7.x] [code: CLAUDE.md:1-5 @7.x]

M.5 Contribution is open to anyone; all changes go through GitHub pull requests; the Community Handbook is
https://contribute.mautic.org/contributing-to-mautic. [code: .github/CONTRIBUTING.md:5-11 @7.x]

M.6 Agent skills for the core repo live in `.agents/skills/` (symlinked from `.claude/skills/`); because `.gitignore`
ignores dot-directories, new skills are added with `git add -f`. [code: AGENTS.md:128-134 @7.x]

## N. Terminology and writing style

The full tables are in terminology.md. Rules:

N.1 In prose, UI strings and docs say "Contact", never "Lead"; code identifiers keep `Lead` (`LeadBundle`, `Lead` entity,
`leads` table). [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]

N.2 Capitalise Mautic feature names as proper nouns: Contact, Company, Segment, Campaign, Email, Form, Landing Page,
Asset, Focus Item, Dynamic Content, Marketing Message, Stage, Points, Point Group, Category, Channel, Report, Role, User,
Theme, Webhook, Plugin, Integration, Custom Field. [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]

N.3 "page" → "Landing Page"; "dwc" → "Dynamic Content"; publish → "Activate"/"Turn On"; unpublish → "Deactivate"/"Turn
Off"; published → "Active"/"Available"; unpublished → "Unavailable"/"Deactivated".
[docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]

N.4 "Segment", not "list" or "contact list"; "Do Not Contact (DNC)"; "allowlist"/"blocklist", not whitelist/blacklist;
"email", not "e-mail". [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt]
[docs: https://github.com/mautic/user-documentation/tree/7.2/.github/styles/Google]

N.5 Google style in docs: American spelling; no "will"; no first person or "we"; no Latin abbreviations ("for example",
"that is"); Oxford comma; no exclamation points; sentence-case headings without a trailing period; spell out ordinals;
no "(s)" plurals; avoid passive voice; "administrator" not "admin"; "to" not "in order to"; "select" not "check";
"turn off" not "disable". [docs: https://github.com/mautic/user-documentation/tree/7.2/.github/styles/Google]

## O. Tests (summary; detail in mautic-testing)

O.1 Unit tests extend `PHPUnit\Framework\TestCase`; functional tests extend `MauticMysqlTestCase`.
[code: AGENTS.md:91-93 @7.x]

O.2 Always pass `-c app/phpunit.xml.dist` (or use `composer test`); it sets `KERNEL_CLASS=AppTestKernel`.
[code: app/phpunit.xml.dist:68-73 @7.x]

O.3 Prefer the real route or command over calling a service, and never mock objects without service dependencies
(events, entities). [code: .github/prompts/write-test.prompt.md:17-18 @7.x]

O.4 Data providers use the `#[DataProvider]` attribute with a `public static` provider; `@dataProvider` is not used and
PHPUnit 11 runs with `failOnWarning="true"`. [code: .github/prompts/write-test.prompt.md:23 @7.x]

## P. Contradictions and open questions

P.1 The PR template's hidden comment says "Features and deprecations must be submitted against the "4.x" branch" and its
c.x example reads "(e.g. 7.x)"; both are stale. Follow the a.x/a.b/c.x table: features to 7.x, BC breaks to 8.x.
[code: .github/PULL_REQUEST_TEMPLATE.md:11,35 @7.x]

P.2 `AGENTS.md` describes `Config/` as "Bundle config (services in config.php)", but PHPStan `NoServicesInBundleConfigRule`
fails when `config.php` defines services. Code wins: use `Config/services.php`. [code: AGENTS.md:70 @7.x]
[code: phpstan.neon:257-277 @7.x]

P.3 `AGENTS.md` says `composer cs` must pass or "CI will fail"; CI checks only changed files and never runs ECS.
[code: AGENTS.md:101 @7.x] [code: .github/workflows/tests.yml:256-264 @7.x]

P.4 PR testing environment: the PR template says GitHub Codespaces; the KB article says Gitpod with login admin/mautic,
while fixtures and DDEV use `Maut1cR0cks!`. [code: .github/PULL_REQUEST_TEMPLATE.md:59 @7.x]
[kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]
[kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html]

P.5 Security report URLs differ: `SECURITY.md` uses the GitHub security tab; `.github/CONTRIBUTING.md` points to
https://www.mautic.org/mautic-security-team/how-to-report-a-security-issue; `MAINTAINERS.md` to
https://mautic.org/security/reporting-a-security-issue/. All require private reporting; prefer the GitHub security tab.
[code: SECURITY.md:32 @7.x] [code: .github/CONTRIBUTING.md:3 @7.x] [code: MAINTAINERS.md:3 @7.x]

P.6 Stale governance: `README.md` links to the `6.x` branch; `RELEASE_LEADS.md` has no 7.1/7.2 schedule and wrong 7.0 dates;
`.github/CODEOWNERS` assigns EmailBundle to @mabumusa1, who is on the maintainers' honor roll, not the current list;
`MAINTAINERS.md` links `CONTRIBUTING.md` at the root, which lives in `.github/`. [code: README.md:17,120,411 @7.x]
[code: RELEASE_LEADS.md @7.x] [code: .github/CODEOWNERS @7.x] [code: MAINTAINERS.md @7.x]

P.7 Open: whether e2e tests are required for every UI PR or only "for UI changes" (AGENTS.md wording). [unverified]

P.8 Open: whether CI checks schema-versus-metadata drift (`doctrine:schema:validate`); not found in `tests.yml`. [unverified]

P.9 Vale conflicts: `CLI` is in the user `accept.txt` while `Google.WordList` flags it; American spelling is enforced while
several KB articles use British spelling. [docs: https://github.com/mautic/user-documentation/tree/7.2/.github/styles/Google]

P.10 The FeatureList says "Activate/Deactivate", but the UI still says "Published" in places; describe UI labels as they
appear on screen when writing test steps. [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]
