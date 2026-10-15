# Development environment, build and dependency tooling - pull-request history

## Contents
- [How to read this file](#how-to-read-this-file)
- [Decisions that shaped current behaviour](#decisions-that-shaped-current-behaviour)
  - [DDEV](#ddev)
  - [Gitpod to Codespaces](#gitpod-to-codespaces)
  - [Environment selection: .env, .env.local and index_dev.php](#environment-selection-env-envlocal-and-index_devphp)
  - [Git hooks and Composer scripts](#git-hooks-and-composer-scripts)
  - [Asset building and npm](#asset-building-and-npm)
  - [Composer layout and scaffolding](#composer-layout-and-scaffolding)
  - [Composer dependency policy](#composer-dependency-policy)
  - [Version pinning](#version-pinning)
  - [Dependabot and GitHub Actions supply chain](#dependabot-and-github-actions-supply-chain)
  - [PHP and database support policy](#php-and-database-support-policy)
  - [Release packaging](#release-packaging)
- [Regression catalogue](#regression-catalogue)
- [Feature timeline](#feature-timeline)
- [Removed, deprecated, replaced](#removed-deprecated-replaced)
- [Maintainer norms for this area](#maintainer-norms-for-this-area)
- [Open questions](#open-questions)
- [Coverage](#coverage)

## How to read this file
Source: merged pull requests on github.com/mautic/mautic for DDEV, Codespaces, build, packaging and dependency tooling, harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; `~` marks an inference. "7.x, unreleased" means merged to 7.x after 7.2.1.
Current behaviour lives in behaviour.md (code-verified); this file explains why and when it came to be.

## Decisions that shaped current behaviour

### DDEV
- DDEV is the supported local environment. On the first `ddev start`, `.ddev/mautic-setup.sh` offers to install Mautic with the API on and a mail catcher [PR #9669] (~v3.3). At launch it used PHP 7.4, Apache and Composer 1 [PR #9669] [historical versions].
- The installer's `memory_limit` check treats `-1` as enough, because the DDEV CLI runs with `-1` [PR #9669] (~v3.3).
- Shell scripts and git hooks used by DDEV must have LF line endings. Git for Windows converted them to CRLF and broke them ("bash\r: No such file or directory") [PR #9669] [PR #10551] (~v3.3-4.2). Since 5.2 the `post-start` hooks normalise CRLF to LF in `.ddev/mautic-setup.sh` and `.git/hooks/*` [PR #13813] (~v5.2). Behaviour 2.3 confirms this.
- DDEV ships Redis and Redis Commander [PR #10538] [PR #10856] (~v4.2). Redis Commander uses the maintained multi-arch image, because the old one failed health checks on Apple Silicon [PR #13550] (~v5.1).
- DDEV installs report `install_source` = DDEV, so dev installs can be told apart in stats [PR #10595] (~v4.0.2). Behaviour 3.7 confirms the value.
- `mautic-setup.sh` answers "yes" automatically on start, which also applies to local DDEV [PR #10763] (~v4.2). Behaviour 3.2 describes the piped `yes`.
- The DDEV project name is not hard-coded; it comes from the checkout folder, so several Mautic checkouts can run side by side [PR #13293] (~v5.1). This is why the setup script uses `${DDEV_HOSTNAME}` rather than `mautic.ddev.site` (SKILL.md open question).
- `upload_dirs` covers `media/files` and `media/images`, which silences the mutagen warning on macOS; see issue mautic/mautic#12244 [PR #13545] (~v5.1).
- The DDEV `local.config.php.dist` uses the Mautic 5 Symfony Mailer DSN, so mail works out of the box [PR #12514] (~v5.0).
- The repo ships `.ddev/config.yaml`; a clone needs only `ddev start` [PR #14207] (~v5.2). Auto-regenerating it with `ddev config` was merged [PR #12818] and reverted [PR #13567] because of issue mautic/mautic#13565 (~v5.1).
- The DDEV database defaults to MariaDB, at a version that meets the installer minimum. It moved to 10.11 when Mautic 7 raised the minimum [PR #14836] (~v7.0).
- The DDEV PHP version follows real compatibility. DDEV was moved back to PHP 8.0 after 8.1 was enabled too early and broke `mautic:plugins:reload` (issue mautic/mautic#12465) [PR #12467] (~v5.0). 7.x DDEV runs PHP 8.5 [code: .ddev/config.yaml:3 @7.x].
- DDEV runs in UTC so PHP and MySQL timezones agree [PR #15650] (~v7.1).
- DDEV runs Node.js 24, required by the CKEditor dev tools [PR #15828] [PR #15829] (7.0.1 / 7.1.0).
- The managed setup runs `mautic:install ... --force --no-interaction`, so it never blocks on prompts [PR #15937] (v7.1.0). `--force` skips only optional checks [PR #9680] (~v3.3).

### Gitpod to Codespaces
- Gitpod (`.gitpod.yml`, a DDEV-based image) replaced Mautibox for PR testers [PR #10500] [PR #10763] (~v4.1-4.2). Its image rebuilt only when `.gitpod.Dockerfile` changed [PR #12578] (~v5.0), and a 1440 MTU override worked around Composer hangs [PR #11084] (~v4.3) [historical].
- Gitpod was removed because it is being sunset; GitHub Codespaces is the supported PR-testing environment [PR #16310] (v7.2.0). PR and issue templates point to Codespaces [PR #16032] (v7.1.1). `.gitpod.yml` is present at 7.1.0 and absent at 7.2.0, while `.devcontainer/devcontainer.json` exists from 6.0.0 on [code: .gitpod.yml @7.1.0] [code: .devcontainer/devcontainer.json @6.0.0] [code: .devcontainer/devcontainer.json @7.x].
- Codespaces uses prebuilds (`prebuild-project.sh`, `setup-project.sh`), cutting boot from about 11 to about 4 minutes [PR #16309] (v7.2.0).
- The `post-checkout` hook is installed for Codespaces by `.devcontainer/setup-project.sh` [PR #16405] (v7.2.0). Behaviour 4.4 describes what it runs there.
- `.devcontainer` is listed in `build/exclude_files.txt`, so dev-environment files never ship [PR #15373] (~v7.0) [PR #15374] (6.0.5).

### Environment selection: .env, .env.local and index_dev.php
- `index_dev.php` was removed in 5.0. A committed `.env` holds `APP_ENV=prod` and `APP_DEBUG=0`, a git-ignored `.env.local` overrides it, and `.env.test` serves tests. One front controller serves every environment [PR #12206] (~v5.0). If a table prefix is used, set `MAUTIC_TABLE_PREFIX` in `.env.local` [PR #12206].
- Before that, DDEV opened Mautic through `index_dev.php` by default, because testers in prod mode hit stale assets [PR #10986] [PR #11134] (~v4.2-4.3) [historical].
- DDEV installs copy `.ddev/.env.local.dist` to `.env.local`, so DDEV runs in dev mode with the debug toolbar; see issue mautic/mautic#13108 [PR #13295] (~v5.1). Behaviour 3.8 confirms this.
- Earlier, DDEV copied `.ddev/.env.dist` to the root `.env` for PHPUnit [PR #9717] (~v4.0) [historical]; 7.x uses `.ddev/.env.test.local` instead (behaviour 12.1).

### Git hooks and Composer scripts
- `composer install` and `update` copy `build/hooks/pre-commit` into `.git/hooks` and make it executable (not on Windows). The hook runs php-cs-fixer on staged files [PR #6002] (~v2.14) [PR #8357] (~v3.0).
- A `post-checkout` hook deletes the cache on every branch switch, so PR testing starts clean [PR #9101] (~v3.2). Behaviour 10.7 confirms it.
- The post-install and post-update script lists are shared [PR #8720] (~v3.1). Composer githook scripts use classic script syntax, because Composer ran the key `script` and hung [PR #12337] (~v5.0).
- The `remove-git-submodules` script was removed. Why: it silently deleted nested `.git` folders, which destroyed plugin work in progress [PR #12816] (~v5.1).
- A blocking CS pre-commit hook was reverted because it broke merge commits in PhpStorm [PR #13299] (~v5.1).
- `bin/console` replaced `app/console` in 3.0 [PR #8356] (~v3.0). It finds the Composer autoloader in any layout [PR #11039] (~v4.3).

### Asset building and npm
- Compiled CSS was generated from LESS with Grunt; contributors edit sources, never the compiled file [PR #4915] (~v2.12) [historical tooling]. Grunt was cut to the configured modules only [PR #12033] [PR #12374] (~v5.0).
- Production assets in `media/css` and `media/js` are no longer committed; they are generated at install and gitignored [PR #11865] (~v5.0). Ignores are narrow and cover only generated files [PR #12776] (~v5.0).
- Front-end libraries are managed through npm so upgrades are easier and Dependabot sees them [PR #12373] (~v5.0). Reviewers ask for new libraries to go through npm [PR #13318].
- `node_modules` is development-only and excluded from builds [PR #12356] (~v5.0). Production pages never load from `node_modules`; `mautic:assets:generate` copies what is needed into `media/` and fails if the copy fails [PR #12417] [PR #12432] (~v5.0).
- `mautic:assets:generate` fails loudly when an expected minified vendor file is missing, rather than writing a broken `libraries.js`. Why: jquery-ui 1.14 removed files [PR #14226] (~v5.2). Behaviour 6.8 lists the output check.
- The minifier is `matthiasmullie/minify`, about 6x faster than `mrclay/minify` [PR #12461] [PR #12717] (~v5.0).
- No npm dependency may use a git SSH URL; HistoryJS was replaced by the native History API [PR #12346] [PR #12381] (~v5.0).
- CKEditor 5 is built from source in `app/assets/libraries/ckeditor/` by webpack [PR #13725] (~v5.1) [PR #15828] (7.0.1). Translations come from CKEditor's shipped bundles because the webpack translation plugin broke `npm run build` [PR #16357] (v7.2.0).
- npm vulnerabilities in transitive dependencies are fixed with `overrides`; success means `npm run build` passes and `npm audit` is clean [PR #16565] (v7.2.0).
- When a JS library update forces a BC break, removing the library is acceptable if it is trivially replaceable: `js-cookie` gave way to native `document.cookie` [PR #16161] (v7.2.0).

### Composer layout and scaffolding
- `mautic/mautic` is the monorepo; `app/` is `mautic/core-lib`, and plugins and themes have their own `composer.json`. `replace` with `self.version` stops Composer fetching them [PR #9920] (~v4.0). Plugins and themes are required at the root, because a downstream project cannot override core-lib's `replace`; see issue mautic/mautic#10092 [PR #10123] (~v4.0).
- Dev dependencies live in the root `composer.json`, not `app/composer.json`, so requiring core-lib does not pull them [PR #9930] (~v4.0). Behaviour 5.1 confirms this.
- A subtree-split workflow publishes read-only mirrors that auto-close PRs [PR #10582] [PR #11354] (~v4.x). Every split package needs a splitter entry, a gitsplit file, a workflow entry, a Packagist package and a composer require; missing one broke `mautic/recommended-project` [PR #14295] [PR #15430] (~v5.2-7.0).
- Scaffolded files must match their monorepo originals, and CI checks it [PR #10857] (~v4.2). Dev-only files (`Gruntfile.js`, build scripts, hooks) are not scaffolded [PR #12522] (~v5.0). `package.json` and `package-lock.json` must be mirrored too [PR #14226] [PR #16565].
- Composer-based installs have no lock file, so `app/composer.json` constraints must exclude incompatible upstream versions [PR #12452] [PR #13272] (~v5.0). See issue mautic/mautic#13243 [PR #13272].
- `symfony/maker-bundle` is available in the dev environment only [PR #11313] (~v5.0).

### Composer dependency policy
- Constraints name tagged versions, never `dev-master`; dead upstreams are forked into the mautic org [PR #1463] [PR #6702] [PR #7470].
- `config.platform.php` is set to the lowest supported PHP [PR #5718] (~v2.13). 7.x pins 8.2.0 (behaviour 1.2).
- Security releases raise the floor in `composer.json`, not only the lock [PR #8417] [PR #9025].
- Test-only packages belong in `require-dev`, so `--no-dev` builds stay small; moving a production dependency there is a BC break [PR #8404] (~v3.0).
- A runtime library must be in `require` in both `app/composer.json` and the root `composer.json`, because production installs use `--no-dev` [PR #17265] (v7.2.1) [PR #17592] (7.2.2). The 7.x snapshot has DomCrawler in core-lib `require` but still in the root `require-dev`; the root fix is in 7.2.2 on the 7.2 branch [code: app/composer.json:75 @7.x] [code: composer.json:48 @7.x].
- A PR must not update unrelated packages in `composer.lock`, and lock changes go in the same PR as the constraint change [PR #11563] [PR #12473] (~v5.0).
- Dependency updates use targeted `composer update <pkg> -W` and paste the command and lock output; `composer why-not` justifies blockers [PR #14262] [PR #15814] [PR #17342].
- Security updates are backported to every maintained line in parallel PRs [PR #15637] [PR #15656] [PR #16141] [PR #16142]. Old lines get lock-only updates validated by `composer audit --locked` [PR #16141].
- When an upstream minor breaks Mautic, Mautic adapts and moves forward rather than pinning the old version [PR #15436] (~v7.0).
- Composer patches in `patches/` are temporary and removed once upstream ships the fix [PR #16160] (v7.2.0).
- Unused dependencies are removed rather than carried: for example `doctrine/annotations`, which Mautic never used [PR #16178] (v7.2.0).
- Maintained upstream packages are preferred over in-tree forks [PR #17370] (8.x).

### Version pinning
- Symfony packages are constrained with `~7.4.0`, not `^7.x`. Why: with `^7.3`, production installs resolved 7.4 with BC breaks while CI used the locked 7.3 [PR #15705] [PR #15710] (7.0.0-rc2).
- Guzzle and other risky libraries are minor-locked the same way [PR #15737] (v7.1.0) [PR #16559] (v7.2.0).
- Mautic's own framework-bundle constraints use `~` so `mautic/recommended-project` cannot pull an untested minor [PR #17343] (8.x).
- Twig has no direct constraint, so real installs can resolve a newer Twig than the lock; code must work on both [PR #16487] (v7.2.0).

### Dependabot and GitHub Actions supply chain
- Dependabot opens one weekly grouped Composer PR and one npm PR [PR #16219], updates lock files only so constraints keep their minor lock [PR #16234], and splits Composer groups into production, development and PHPStan [PR #16567] (v7.2.0).
- `dependabot-sync-scaffolding.yml` copies the root `package-lock.json` into the scaffold on Dependabot PRs, using a GitHub App token because `GITHUB_TOKEN` cannot trigger follow-up workflows [PR #16219] (v7.2.0).
- GitHub Actions are pinned to commit SHAs and bumped by Dependabot, because of supply-chain attacks [PR #16214] [PR #16227] (v7.2.0).

### PHP and database support policy
- PHP minimums rise in majors (7.2 for 3.0) and are enforced in `VersionCheckMiddleware`, the installer and `release_metadata.json` [PR #8167] (~v3.0). Behaviour 1.3 confirms the middleware.
- PHP 7.2 was dropped in minor 3.3 after a warning in 3.2.x [PR #9451] (~v3.3), and PHP 8.0 in minor 5.2 for security reasons; both were called a grey area [PR #13972] (~v5.2).
- Mautic 7 requires MySQL 8.4+ or MariaDB 10.11+, and the installer refuses older versions [PR #14836] (~v7.0). Behaviour 1.6 confirms this.
- Mautic 8 requires PHP 8.4, a prerequisite for Symfony 8 [PR #16993] (8.x).
- Branch policy: features and fixes go to 7.x; 8.x takes only BC breaks and is not the default branch [PR #16993].

### Release packaging
- Packaging excludes by listing what to leave out, so new root files ship automatically [PR #393] (~v1.1).
- `upgrade.php` stays in the update package; removing it broke UI upgrades [PR #7757] [PR #8577] (~v2.16.1).
- The package keeps `DataFixtures` and Twig `Test` folders, because removing them broke `cache:clear` [PR #8348] [PR #8910] (~v3.0).
- The update package lists deleted files in `deleted_files.txt` [PR #10228] (~v4.0) and, since 6.0, also the vendor files removed since the minimum supported version [PR #14683] (~v6.0).
- Update packages include renamed files, use a higher rename limit and run Composer scripts explicitly [PR #12519] [PR #12521] (~v5.0).
- Update packages include generated Carbon pictograms and `media/bundles`; missing pictograms caused HTTP 500 on emails after 7.0.0 [PR #15841] (7.0.1).
- The release zip is uploaded to m.mautic.org only for stable releases, comparing `is-prerelease` as the string `'false'` [PR #10882] [PR #15938] (v7.1.0). It is registered as a remote asset pointing at the GitHub download [PR #15704] (v7.1.0).
- `build/exclude_files.txt` must not list vendor packages, because the build already uses `--no-dev`; a vendor exclusion stripped DomCrawler from the 7.2.1 package. The release workflow now checks `Crawler.php` is present, and `build/package_devhead.php` was deleted [PR #17616] [PR #17832] (7.2.2). These are fixed in 7.2.2 on the 7.2 branch; the 7.x snapshot still has the exclusion and the script [code: build/exclude_files.txt:37 @7.x] [code: build/package_devhead.php @7.x].

## Regression catalogue
| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **DDEV and Codespaces** | | | |
| `ddev start` on Windows failed in `mautic-setup.sh` | Scripts and hooks are LF-normalised on start | [PR #13813] [PR #10551] | ~5.2 / 4.2 |
| Installer warned memory `-1` was too low | `-1` counts as enough | [PR #9669] | ~3.3 |
| DDEV ran in prod mode (issue mautic/mautic#13108) | DDEV runs in dev mode via `.env.local` | [PR #13295] | ~5.1 |
| Two DDEV Mautic projects could not run at once | Project name comes from the folder | [PR #13293] | ~5.1 |
| Redis Commander health check failed on arm64 | Multi-arch image | [PR #13550] | ~5.1 |
| `mautic:plugins:reload` broke after DDEV moved to PHP 8.1 early | DDEV PHP follows real compatibility | [PR #12467] | ~5.0 |
| E2E install failed: MariaDB 10.3 too old | DDEV MariaDB 10.11 | [PR #14836] | ~7.0 |
| **Hooks and Composer scripts** | | | |
| pre-commit hook not executable after install | Composer chmods it | [PR #6002] | ~2.14 |
| `composer install` hung at the githooks step | Classic script syntax | [PR #12337] | ~5.0 |
| `composer install` deleted nested `.git` folders | No destructive Composer scripts | [PR #12816] | ~5.1 |
| **Assets** | | | |
| `npm install` failed on `grunt-remove` | Only configured Grunt modules installed | [PR #12033] | ~5.0 |
| Production pages loaded JS from `node_modules` | Libraries copied into `media/` | [PR #12417] | ~5.0 |
| Broken `libraries.js` after jquery-ui 1.14 | Asset generation fails on a missing file | [PR #14226] | ~5.2 |
| `npm run build` failed on CKEditor translations | Shipped translation bundles | [PR #16357] | 7.2.0 |
| **Dependencies** | | | |
| Production broke on Symfony 7.4 while CI was green | `~7.4.0` minor lock | [PR #15705] [PR #15710] | 7.0.0-rc2 |
| API returned empty contacts on Composer installs (issue mautic/mautic#13243) | Works with `jms/serializer-bundle` ^5.4 | [PR #13272] | ~5.0.3 |
| Binary downloads broke after an unrelated lock bump | No unrelated lock changes | [PR #11563] | ~5.0 |
| All Composer installs blocked by security advisories | Patched versions on every line | [PR #15637] [PR #15656] | ~7.1 / 5.2.9 |
| recommended-project install failed after an oauth bundle minor | Mautic adapts to the new minor | [PR #15436] | ~7.0 |
| recommended-project lacked a theme package | Every split package registered | [PR #15430] | ~7.0 |
| Saving an email on a `--no-dev` install returned HTTP 500 | Runtime libraries in `require` | [PR #17265] [PR #17592] | 7.2.1 / 7.2.2 |
| **Packaging** | | | |
| UI upgrade failed without `upgrade.php` | It stays in the update package | [PR #8577] | ~2.16.1 |
| `cache:clear` warned on a 3.0 beta package | DataFixtures and Twig Test folders kept | [PR #8910] [PR #8348] | ~3.0 |
| Upgrade to 4.0 fatal error | `deleted_files.txt` in the update package | [PR #10228] | ~4.0 |
| Leftover vendor files after upgrade | Vendor deletions listed | [PR #14683] | ~6.0 |
| Emails returned 500 after upgrading to 7.0.0 | Pictograms in the update zip | [PR #15841] | 7.0.1 |
| Pre-releases were uploaded to m.mautic.org | String comparison of `is-prerelease` | [PR #15938] | 7.1.0 |
| 7.2.1 release zip lacked DomCrawler | No vendor exclusions; package check | [PR #17616] | 7.2.2 |

## Feature timeline
| Version | Change | PR |
|---|---|---|
| ~1.1-2.14 | Exclude-list packaging; no `dev-master`; platform PHP pin; pre-commit hook | [PR #393] [PR #1463] [PR #5718] [PR #6002] |
| ~3.0-3.3 | `bin/console`; `require-dev` for test packages; post-checkout hook; DDEV | [PR #8356] [PR #8404] [PR #9101] [PR #9669] |
| ~4.0-4.4 | Monorepo split and recommended-project; DDEV Redis; Gitpod; `install_source`; scaffold check | [PR #9920] [PR #10123] [PR #10538] [PR #10500] [PR #10595] [PR #10857] |
| ~5.0 | `.env`/`.env.local` replace `index_dev.php`; npm-managed libraries; generated assets not committed; new minifier | [PR #12206] [PR #12373] [PR #11865] [PR #12717] |
| ~5.1 | DDEV dev mode; folder-based project name; `upload_dirs`; no `remove-git-submodules` | [PR #13295] [PR #13293] [PR #13545] [PR #12816] |
| ~5.2 | Shipped `.ddev/config.yaml`; CRLF hooks; PHP 8.3 in, 8.0 out | [PR #14207] [PR #13813] [PR #13958] [PR #13972] |
| ~6.0 | Vendor deletions in update packages; `.devcontainer` excluded from builds (6.0.5) | [PR #14683] [PR #15374] |
| 7.0 | MySQL 8.4 / MariaDB 10.11; `~7.4.0` Symfony; Node 24 (7.0.1) | [PR #14836] [PR #15705] [PR #15828] |
| 7.1 | DDEV UTC; Guzzle minor lock; stable-only release upload; Codespaces in templates (7.1.1) | [PR #15650] [PR #15737] [PR #15938] [PR #16032] |
| 7.2.0 | Gitpod removed; Codespaces prebuilds; grouped lock-only Dependabot; SHA-pinned actions; `js-cookie` removed | [PR #16310] [PR #16309] [PR #16219] [PR #16234] [PR #16227] [PR #16161] |
| 7.2.1-7.2.2 (7.2 branch) | DomCrawler in `require`; no vendor exclusions; `package_devhead.php` deleted | [PR #17265] [PR #17592] [PR #17616] [PR #17832] |
| 7.x, unreleased | Bug template lists 7.2 first; imports sorted | [PR #17340] [PR #17556] |
| 8.x | PHP 8.4 minimum; Symfony 8 dependency upgrades | [PR #16993] [PR #17342] [PR #17370] |

## Removed, deprecated, replaced
| What | Replaced by | PR | Version |
|---|---|---|---|
| `app/console` | `bin/console` | [PR #8356] | 3.0 |
| `index_dev.php` | `APP_ENV`/`APP_DEBUG` in `.env.local` | [PR #12206] | ~5.0 |
| Committed `media/css`, `media/js` | Generated at install | [PR #11865] | ~5.0 |
| `mrclay/minify` | `matthiasmullie/minify` | [PR #12717] | ~5.0 |
| HistoryJS, `jquery-color`, unused Grunt plugins | Native API, jQuery UI, nothing | [PR #12381] [PR #12357] [PR #12374] | ~5.0 |
| `remove-git-submodules` script | Nothing | [PR #12816] | ~5.1 |
| Auto-generated DDEV config | Hand-maintained `.ddev/config.yaml` | [PR #13567] | ~5.1 |
| Gitpod and the MTU override | GitHub Codespaces | [PR #16310] | 7.2.0 |
| `^7.3` Symfony constraints | `~7.4.0` | [PR #15705] | 7.0.0-rc2 |
| `js-cookie` | Native `document.cookie` | [PR #16161] | 7.2.0 |
| `doctrine/annotations` | Nothing (never used) | [PR #16178] | 7.2.0 |
| Vendor entries in `exclude_files.txt`, `package_devhead.php` | `--no-dev` only | [PR #17616] [PR #17832] | 7.2.2 |
| javer/sp-bundle | lightsaml2 packages | [PR #17370] | 8.x |

## Maintainer norms for this area
- Change a scaffolded file together with its copy in `app/assets/scaffold/files/` [PR #10857] [PR #13309] [PR #14226].
- Fixes to CI, scaffolding and DDEV go to every maintained branch as companion PRs [PR #10597] [PR #11089] [PR #11969].
- Composer scripts must not do destructive things, and git hooks must not block normal IDE workflows [PR #12816] [PR #13299].
- Test DDEV changes locally and in the cloud environment before merge [PR #12578] [PR #13293].
- Record library swaps and env changes in `UPGRADE-<major>.md` and the developer docs [PR #12206] [PR #12717] [PR #14883].
- Lock framework and risky libraries to a minor (`~X.Y.0`) [PR #15705] [PR #15737] [PR #17343].
- Dependency PRs paste the exact command and lock output; "a green CI is all we can test" is accepted for no-code bumps [PR #15775] [PR #15814].
- Prefer moving forward to a fixed upstream over pinning, and prefer maintained packages over forks [PR #15436] [PR #17370].
- Dev tools such as Rector must be locked to a production tag before a release [PR #16859].
- Release-process changes need a documented local test procedure [PR #12796].
- AI-generated PRs are allowed but must be flagged and reviewed carefully, especially release tooling [PR #15704].

## Open questions
- Behaviour 8.6 and the setup script call the mail catcher MailHog on port 8026, the name used when DDEV support was added [PR #9669]; Codespaces docs call it Mailpit. No PR in the inputs renames it.
- `gaufrette/extras` was mirrored as `mautic/gaufrette-extras` [PR #15923] and its removal was questioned in release prep [PR #15927]; the final state is not recorded.
- [PR #9341] blocks web access to `composer.json` and `composer.lock` only on Apache; whether Nginx installs expose them is open.
- Whether `upgrade.php` still ships in the full package, a security concern raised in [PR #8577], is not checked.
- Whether the root DomCrawler fix [PR #17592] and the packaging fixes [PR #17616] [PR #17832] have been merged up to 7.x is not visible in this snapshot.
- When DDEV moves to a new PHP version is not stated as a policy [PR #12467].
- Testing a lock-less Composer install in CI was suggested [PR #13272]; the recommended-project job [PR #15436] covers part of it.

## Coverage
The dev-tooling-testing area has 588 merged PRs in six chunks (#258 to #17832, 2015-04 to 2026-10): 122, 119, 102, 98, 105 and 42 PRs.
About 440 are substantive across testing and dev-env; the rest are dependency bumps, template edits, reverts and branch merges.
This file uses the `[dev-env]` items; `[testing]` items are in mautic-testing, and product-code PRs that landed in the bucket were skipped.
Repository-process items (PR and issue templates, branching, stalebot, bounties, Transifex) are left to mautic-contributing.
A further 869 noise PRs across all areas were excluded upstream before chunking.
