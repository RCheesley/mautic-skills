# Mautic contributing: code map (governance files, CI workflows, config files)

Paths are relative to the root of `mautic/mautic` at 7.2.1 unless marked `@8.x`.

## 1. Governance and policy files

| File | What it holds | Tag |
|---|---|---|
| `.github/PULL_REQUEST_TEMPLATE.md` | Branch rules (a.x / a.b / c.x), Q/A table, Description, Steps to test, Promptless docs note | [code: .github/PULL_REQUEST_TEMPLATE.md:1-64 @7.x] |
| `.github/ISSUE_TEMPLATE/BUG-REPORT.yml` | Bug form: supported series (only 7.2.x), version, install method, PHP, reproduction, CoC | [code: .github/ISSUE_TEMPLATE/BUG-REPORT.yml:24-111 @7.x] |
| `.github/ISSUE_TEMPLATE/config.yml` | `blank_issues_enabled: false`; support → forum c/support, ideas → forum c/ideas | [code: .github/ISSUE_TEMPLATE/config.yml @7.x] |
| `.github/CONTRIBUTING.md` | Open contribution via PRs; Community Handbook link; dev docs repo; security reporting link | [code: .github/CONTRIBUTING.md:1-15 @7.x] |
| `.github/CODE_OF_CONDUCT.md`, `.github/SUPPORT.md`, `.github/FUNDING.yml` | Community files | [code: .github/ @7.x] |
| `.github/CODEOWNERS` | `**/app/bundles/EmailBundle @mabumusa1` (stale, see behaviour.md P.6) | [code: .github/CODEOWNERS @7.x] |
| `SECURITY.md` | Security team scope, private reporting, advisories, ELTS, disclosure | [code: SECURITY.md @7.x] |
| `MAINTAINERS.md` | Project Lead, current maintainers (@escopecz, @kuzmany, @npracht, @matbcvo, @cibero42), honor roll, governance link | [code: MAINTAINERS.md @7.x] |
| `RELEASE_LEADS.md` | Release-lead schedule (stale for 7.x) | [code: RELEASE_LEADS.md @7.x] |
| `README.md` | Overview; links to supported versions page (some links still point at `6.x`) | [code: README.md:17,77,120,411 @7.x] |
| `AGENTS.md` (+ `CLAUDE.md`, `GEMINI.md` pointing to it) | Agent guidance: DDEV rule, commands, PR checklist, coding standards | [code: AGENTS.md @7.x] [code: CLAUDE.md:1-5 @7.x] |
| `.agents/skills/mautic-dev/SKILL.md` | In-repo agent skill: pitfalls, verification, migrations, BC-policy link | [code: .agents/skills/mautic-dev/SKILL.md @7.x] |
| `.github/prompts/write-test.prompt.md` | Test-writing rules (final, strict types, attributes, real objects) | [code: .github/prompts/write-test.prompt.md @7.x] |
| `UPGRADE-3.0.md` … `UPGRADE-7.0.md`, `UPGRADE-PHP-TO-TWIG-TEMPLATES.md` | BC notes per major | [code: UPGRADE-7.0.md @7.x] |
| `UPGRADE-8.0.md` | 8.0 BC notes (appended per PR) | [code: UPGRADE-8.0.md @8.x] |
| `.all-contributorsrc` | All-contributors bot data | [code: .all-contributorsrc @7.x] |
| `app/release_metadata.json` | `version`, `stability`, min/max PHP, min MySQL/MariaDB, `minimum_mautic_version`, `announcement_url` | [code: app/release_metadata.json @7.x] |

## 2. CI workflows (`.github/workflows/`)

| Workflow | Trigger | What it checks | Tag |
|---|---|---|---|
| `tests.yml` | every PR, pushes to `[0-9].*`, merge queue, daily cron | `phpunit` (PHP 8.2 × MySQL 8.4 / MariaDB 10.11; PHP 8.5 × MySQL 9.2 / MariaDB 11.4), `e2e-tests` (DDEV + Codeception), `misc` (PHPStan, CS Fixer on changed files, Rector dry-run, Twig lint, scaffold diff, composer-project install, `composer validate`) | [code: .github/workflows/tests.yml:3-316 @7.x] |
| `e2e-tests.yml` | push/PR touching `tests/**` | Codeception suite ×10, fail-fast (flakiness) | [code: .github/workflows/e2e-tests.yml:25-28 @7.x] |
| `coverage-check.yml` (+ `coverage-check-cleanup.yml`) | PR labelled `check-coverage` or `ready-to-commit` | full PHPUnit with pcov, Codecov upload | [code: .github/workflows/coverage-check.yml:7-88 @7.x] |
| `api-library-tests.yml` | every PR | installs this checkout under Apache (PHP 8.3) and runs the `mautic/api-library` suite | [code: .github/workflows/api-library-tests.yml:20-125 @7.x] |
| `build-grapesjs-assets.yml` | PR touching `plugins/GrapesJsBuilderBundle/**` | `npm ci && npm run build` | [code: .github/workflows/build-grapesjs-assets.yml @7.x] |
| `validate-json.yml` | changed JSON | `jq empty` | [code: .github/workflows/validate-json.yml @7.x] |
| `transifex.yml` | push of `**/Translations/en_US/*.ini` on default branch | `mautic:transifex:push` | [code: .github/workflows/transifex.yml @7.x] |
| `release.yml` | tag push | tag == `release_metadata.json` version; build ZIPs; draft release; fresh-install and update tests | [code: .github/workflows/release.yml:38-282 @7.x] |
| `generate-release-notes.yml` | manual | changelog per milestone | [code: .github/workflows/generate-release-notes.yml @7.x] |
| `split-monorepo-in-multi-repo.yml` | push/create/delete of `[0-9].*` branches and tags | splits core-lib, plugins, themes into `mautic/<name>` repos | [code: .github/workflows/split-monorepo-in-multi-repo.yml @7.x] |
| `dependabot-sync-scaffolding.yml` | Dependabot `package-lock.json` change | copies it into `app/assets/scaffold/files/` | [code: .github/workflows/dependabot-sync-scaffolding.yml:27-40 @7.x] |
| `stale.yml` | schedule | issues 90+14 days, PRs 365+30 days; `security`, `legacy`, `bounty`, milestoned exempt | [code: .github/workflows/stale.yml @7.x] |
| `bounties.yml`, `closed-issue-reply.yaml` | issue events | issue automation | [code: .github/workflows/ @7.x] |

Other CI configuration: `.github/release.yml` (release-note label groups), `.github/dependabot.yml` (weekly composer,
npm, actions), `.coderabbit.yaml` (AI review path instructions), `codecov.yml` (patch target 0 %),
`.sonarcloud.properties`, `.github/ci-files/` (`local.php`, `.my.cnf`, `composer.json` for the recommended-project test).
[code: .github/release.yml @7.x] [code: .github/dependabot.yml @7.x] [code: .coderabbit.yaml:2-13 @7.x]
[code: codecov.yml:7-13 @7.x]

## 3. Tooling configuration files

| File | Purpose | Tag |
|---|---|---|
| `composer.json` | root `mautic/mautic`; dev tools in `require-dev`; scripts `test`, `e2e-test`, `phpstan`, `phpstan-baseline`, `cs`, `fixcs`, `rector`, `githooks`, `generate-assets` | [code: composer.json:166-214 @7.x] |
| `app/composer.json` | `mautic/core-lib` runtime deps; autoload `Mautic\` → `app/bundles/`, `Mautic\Migrations\` → `app/migrations/`; scaffold file mapping | [code: app/composer.json:7-16,112-133 @7.x] |
| `app/phpunit.xml.dist` | suites, `KERNEL_CLASS=AppTestKernel`, `MAUTIC_ENV=test`, `failOnWarning` | [code: app/phpunit.xml.dist:42,68-75 @7.x] |
| `phpstan.neon`, `phpstan-baseline.neon`, `phpstan-bootstrap.php` | level 6, type coverage, custom rules, suppressions | [code: phpstan.neon:1-277 @7.x] |
| `utils/phpstan/src/Rule/`, `utils/phpstan/tests/Rule/` | custom PHPStan rules and their tests | [code: utils/phpstan/src/Rule/ @7.x] |
| `rector.php`, `utils/rector/src/`, `utils/rector/tests/` | Rector sets, type-guarded classes, custom rectors | [code: rector.php:10-122 @7.x] |
| `.php-cs-fixer.php`, `ecs.php` | coding standard | [code: .php-cs-fixer.php:5-57 @7.x] [code: ecs.php:7-43 @7.x] |
| `build/hooks/pre-commit`, `build/hooks/post-checkout` | git hooks installed by `composer githooks` | [code: composer.json:166-214 @7.x] |
| `codeception.yml`, `tests/` | e2e acceptance tests | [code: codeception.yml @7.x] |
| `.ddev/` | local environment (see mautic-dev-environment) | [code: .ddev/ @7.x] |
| `app/migrations/Migration.template` | generator template for core migrations | [code: app/migrations/Migration.template @7.x] |
| `app/bundles/*/Translations/en_US/*.ini` | source UI strings (only en_US in repo) | [code: app/bundles/CoreBundle/Loader/TranslationLoader.php @7.x] |
| `translations/overrides/<locale>/` | site-specific wording overrides (not for core PRs) | [code: app/config/paths.php:10 @7.x] |
| `patches/` + `composer.json` `extra.patches` | composer patch on `twig/twig`; npm patches for at.js and chosen-js | [code: composer.json:234-258 @7.x] |

## 4. 8.x differences in this map
- `.php-cs-fixer.php` is deleted; ECS only; the pre-commit hook runs `vendor/bin/ecs`. [PR #17280] [PR #17362]
- Tool binaries move from `bin/*` to `vendor/bin/*`. [PR #17164] [code: composer.json @8.x]
- PHPUnit 13, `dg/bypass-finals` enabled in `app/tests/bootstrap.php`. [PR #17004] [PR #17366]
- More PHPStan rules (for example single-argument event dispatch, `NoServiceGetterRule`, `NoServiceInEventConstructorRule`);
  baseline 8,683 lines. [PR #17625] [PR #17631] [code: phpstan.neon @8.x]
