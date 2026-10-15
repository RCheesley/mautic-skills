---
name: mautic-dev-environment
description: "Setting up and running a Mautic development or test instance: DDEV (.ddev/config.yaml, the auto-install hook, the separate test database, Mailpit, Redis, phpMyAdmin), GitHub Codespaces (.devcontainer), composer install and the mautic/mautic + mautic/core-lib layout, building assets (mautic:assets:generate, npm run build, importmap, GrapesJS gjs-build), running bin/console, cron and Messenger consumers locally, logs in var/logs, clearing caches, default dev credentials, testing a pull request locally, staging servers, and common setup failures. Use whenever a task says set up Mautic locally, ddev start, install Mautic for development, test this PR, reproduce a bug locally, assets not loading, builder doesn't load, GrapesJS not built, node_modules or ckeditor.js missing, what is the admin password, where are the logs, clear the cache, 'Mautic already installed', or touches .ddev/, .devcontainer/, build/, composer.json scripts, package.json or importmap.php."
---
# Mautic development and test environment

## Scope
This skill covers getting a Mautic 7.x checkout running for development, testing or pull request (PR) review: DDEV and Codespaces, Composer and npm, asset builds, CLI install, running scheduled commands and queue consumers by hand, logs, caches, credentials, PR testing and staging clones.
It does not cover writing tests (mautic-testing), the meaning of configuration parameters (mautic-configuration), the cron and queue command catalogue (mautic-cron-and-queues), contribution policy (mautic-contributing) or production upgrades (mautic-upgrades-and-versions).

Terms: **DDEV** is the Docker-based local environment the repo ships in `.ddev/`. **local.php** is `config/local.php`, the file that holds instance settings. A **Contact** is a marketing record. A **User** is a back-office login.

## Expected behaviour (essentials)
DDEV and install
- DDEV runs PHP 8.5, Apache-FPM, MariaDB 10.11, Node 24 and Composer 2, and adds the PHP `imap` extension. [code: .ddev/config.yaml:1-24 @7.x]
- Every `ddev start` runs `.ddev/mautic-setup.sh` as a post-start hook. On the first run it asks whether DDEV should manage the install and saves the answer to `.ddev/mautic-preference`. Later starts skip setup while that file exists. [code: .ddev/config.yaml:9-15 @7.x] [code: .ddev/mautic-setup.sh:40-61 @7.x]
- A managed setup runs `composer install` and copies `.ddev/local.config.php.dist` to `config/local.php`. It copies `.ddev/.env.test.local` to `.env.test.local`. Outside Codespaces it also copies `.ddev/.env.local.dist` to `.env.local`, which sets `APP_ENV=dev` and `APP_DEBUG=1`. [code: .ddev/mautic-setup.sh:8-15 @7.x]
- The setup then runs `mautic:install https://<ddev host> --force --no-interaction`, `cache:warmup --env=dev` and `mautic:plugins:reload`. It finishes with `npm ci && npm run build-dev` in `plugins/GrapesJsBuilderBundle`. [code: .ddev/mautic-setup.sh:17-25 @7.x]
- `ddev ddev-setup-mautic` forces the managed setup again. It overwrites `config/local.php` with the dist file, which has no `site_url`, so Mautic is treated as not installed and is installed again over the existing database. [code: .ddev/commands/web/ddev-setup-mautic @7.x] [code: app/AppKernel.php:272-283 @7.x]
- In the DDEV `config/local.php`, the database is `db`/`db`/`db` on host `db`, the mailer is `smtp://localhost:1025`, the API and HTTP basic auth are on, and `install_source` is `DDEV`. [code: .ddev/local.config.php.dist @7.x]
- Mautic counts as installed only when the local parameters contain both `db_driver` and `site_url`. Deleting `site_url` from local.php reopens the installer. [code: app/AppKernel.php:272-283 @7.x] [code: app/bundles/InstallBundle/Install/InstallService.php:125-139 @7.x]
- `mautic:install` exits 0 with "Mautic already installed" when Mautic is already installed. An existing `site_url` in local.php wins over the `site_url` argument. [code: app/bundles/InstallBundle/Command/InstallCommand.php:155-159 @7.x] [code: app/bundles/InstallBundle/Command/InstallCommand.php:222-227 @7.x]
- A failed requirements check makes `mautic:install` return exit code `0`, the same as success. Later steps return `-1`, `-2` or `-3`. Scripts must check the output, not only the exit code. [code: app/bundles/InstallBundle/Command/InstallCommand.php:243 @7.x]
- By default the installer backs up existing tables by renaming them with the prefix `bak_` (`--db_backup_tables=true`). It does not drop them. [code: app/bundles/InstallBundle/Command/InstallCommand.php:183-194 @7.x] [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:119-175 @7.x]
- The installer refuses MySQL below 8.4.0, MariaDB below 10.11.0 and any other database platform. Web requests on PHP outside 8.2.0–8.5.99 get an HTTP 500 before the kernel boots. [code: app/release_metadata.json:4-7 @7.x] [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:177-201 @7.x] [code: app/middlewares/VersionCheckMiddleware.php:46-59 @7.x]

Credentials
- The dev and test admin login is `admin` / `Maut1cR0cks!` in every path that is in code. That covers the DDEV install, the Codespaces readiness page, the user fixtures (`admin` and `sales`), the PHPUnit base class and the Codeception tester. [code: .ddev/local.config.php.dist @7.x] [code: .devcontainer/CODESPACES-READY.tpl.md @7.x] [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php:24-49 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:48-49 @7.x] [code: tests/_support/AcceptanceTester.php:27 @7.x]
- `admin` / `mautic` is stale. The KB PR-testing article still gives it, and the docs say it applied before 5.1. `.env.test` still sets `MAUTIC_ADMIN_PASSWORD=mautic`, but no code reads that variable. [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev] [code: .env.test:10-11 @7.x]

Composer and assets
- The repo has two packages. The root `mautic/mautic` holds the dev tooling. It requires `mautic/core-lib` from the `app/` path repository, and `app/composer.json` declares every runtime dependency. [code: composer.json:23-27 @7.x] [code: app/composer.json:15-105 @7.x]
- `composer install` and `composer update` run six scripts in order: install git hooks, `npm ci`, `npx patch-package`, the GrapesJS build, `generate-assets`, then `motd`. [code: composer.json:153-168 @7.x]
- `npm ci` also builds, because the `postinstall` script runs `npm run build`. Webpack builds only the CKEditor 5 bundle, to `media/libraries/ckeditor/ckeditor.js`. [code: package.json:62-65 @7.x] [code: webpack.config.js:28-37 @7.x]
- `composer generate-assets` runs `mautic:assets:generate` and then `assets:install --symlink --relative ./`. The command fails when `node_modules/` or the CKEditor bundle is missing. Otherwise it runs `sass:build`, `importmap:install` and `asset-map:compile`, then writes `media/css/*.css` and `media/js/*.js`. [code: composer.json:192 @7.x] [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:51-120 @7.x]
- During `composer install`, a failed GrapesJS build (for example, Node missing) only prints a warning, so the email and page builder stays unbuilt with no error. Fix it with `composer gjs-build`, or `ddev gjs-build` for a dev build. [code: build/gjs_build.php:5-13 @7.x] [code: .ddev/commands/web/gjs-build @7.x]
- Generated assets are gitignored: `media/css/app.css`, `media/js/app.js`, the CKEditor bundle, `assets/build/` and `var/sass/`. Never commit them. [code: .gitignore:66-105 @7.x]

Running, logs and caches
- Run PHP, Composer, console and PHPUnit commands inside DDEV, for example `ddev exec bin/console …` and `ddev composer …`. Run them on the host only when asked. [code: AGENTS.md "Command Execution Rule" @7.x]
- DDEV has no cron service. Run scheduled commands by hand, for example `ddev exec bin/console mautic:segments:update`. [code: .ddev/config.yaml:1-24 @7.x] [code: .ddev/mautic-setup.sh:35 @7.x]
- The Messenger transports `email` and `hit` default to `sync://`, so a fresh dev instance sends email and records hits inside the request and needs no worker. [code: app/bundles/MessengerBundle/Config/config.php:7-9 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mautic-doesn-t-use-queues-by-default]
- Logs live in `var/logs`. The Mautic channel writes daily-rotated `mautic_<env>-<date>.php` files. Other channels write `<env>.php`. In the dev environment, or when `debug` is set, the Mautic log records debug level. Otherwise it records notice level and above. [code: app/bundles/CoreBundle/Config/config.php:254-256 @7.x] [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:12-24 @7.x] [code: app/config/config_dev.php:58-78 @7.x]
- `cache:clear` rebuilds the Symfony container cache in `var/cache/<env>`. `mautic:cache:clear` clears only Mautic's application cache adapter, for example Segment counts and dashboard widgets. They are not interchangeable. [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:7-22 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html]
- The `post-checkout` git hook deletes `var/cache` on every branch switch. In Codespaces it also runs `composer install` and `doctrine:migrations:migrate`. [code: build/hooks/post-checkout:3-12 @7.x]
- The dev front controller only accepts local IPs, `dev_hosts`, or any request when `DDEV_TLD` is set, so dev mode works inside DDEV without extra settings. [code: app/middlewares/Dev/IpRestrictMiddleware.php:33-51 @7.x]

Tests in the environment
- Under DDEV, PHPUnit uses the `test` database through `.env.test.local`. GitHub Actions uses `mautictest` from `.env.test`. Every test table gets the prefix `test_`. [code: .ddev/.env.test.local @7.x] [code: .env.test:2-8 @7.x]
- Always run PHPUnit with `-c app/phpunit.xml.dist` or through `composer test`, because only that file sets `KERNEL_CLASS`. [code: app/phpunit.xml.dist:65-76 @7.x] [code: composer.json:169 @7.x]
- The Codeception end-to-end suite runs only inside DDEV, because it uses the Selenium add-on's service names. [code: .ddev/docker-compose.selenium-chrome.yaml @7.x] [code: composer.json:170 @7.x]

## Where it lives
| Concern | Path(s) |
|---|---|
| DDEV config, hooks, add-ons | `.ddev/config.yaml`, `.ddev/docker-compose.{phpmyadmin,redis,redis-commander,selenium-chrome}.yaml`, `.ddev/php/codeception.ini` |
| Auto-install | `.ddev/mautic-setup.sh`, `.ddev/commands/web/ddev-setup-mautic`, `.ddev/mautic-preference` (generated) |
| Instance and env templates | `.ddev/local.config.php.dist` → `config/local.php`; `.ddev/.env.local.dist` → `.env.local`; `.ddev/.env.test.local` → `.env.test.local` |
| Codespaces | `.devcontainer/devcontainer.json`, `setup-project.sh`, `prebuild-project.sh`, `CODESPACES.md`, `CODESPACES-READY.tpl.md` |
| Composer layout and scripts | `composer.json` (root, scripts at `:149-193`), `app/composer.json` (core-lib, scaffold map `:112-133`) |
| Front-end build | `package.json`, `webpack.config.js` (CKEditor only), `importmap.php`, `app/config/config.php:50-73,134-144` (AssetMapper, Sass) |
| Asset generation | `app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php`, `AssetGenerationHelper` |
| GrapesJS build | `plugins/GrapesJsBuilderBundle/package.json` (`build`, `build-dev`), `build/gjs_build.php`, `.ddev/commands/web/gjs-build` |
| Git hooks | `build/hooks/pre-commit`, `pre-commit.win`, `post-checkout` |
| Install | `app/bundles/InstallBundle/Command/InstallCommand.php`, `Install/InstallService.php`, `Helper/SchemaHelper.php`, `Configurator/Step/CheckStep.php` |
| Logs | `var/logs/` (`log_path`), `app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php` |
| Caches | `var/cache/<env>/`, `app/bundles/CacheBundle/Command/ClearCacheCommand.php`, `app/bundles/CoreBundle/Helper/CacheHelper.php` |
| Platform limits | `app/release_metadata.json`, `app/middlewares/VersionCheckMiddleware.php` |

Full detail is in `references/code-map.md`.

## How to change or extend it
- If you change a scaffolded root file (`.env`, `.gitignore`, `webpack.config.js`, `importmap.php`, `package.json`, `package-lock.json`, `tsconfig.json`, `index.php`, `.htaccess`, `bin/console`, `patches/*`), change its copy in `app/assets/scaffold/files/` in the same PR. CI compares each pair. [code: app/composer.json:112-133 @7.x] [code: .github/workflows/tests.yml:265-277 @7.x]
- After you edit bundle `Assets/js` or `Assets/css`, run `ddev composer generate-assets`. After you edit the CKEditor sources, run `npm run build`. After you edit the GrapesJS plugin, run `ddev gjs-build`. Do not commit the output. [code: AGENTS.md @7.x] [code: .gitignore:66-105 @7.x]
- For Sass work, run `composer sass:build` once or `composer sass:watch` to rebuild on change. Both first delete `assets/build`. [code: composer.json:183-191 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/building_assets.html]
- After you add an entity or column, run `ddev exec rm -rf var/cache` so the cached test schema dumps are rebuilt. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-213 @7.x]
- To change DDEV defaults for yourself only, use DDEV's own override files. Do not edit `.ddev/config.yaml`, which every contributor shares. Codespaces already writes `.ddev/config.local.yaml`. [code: .devcontainer/setup-project.sh:14-30 @7.x]
- Keep `.ddev/` and `.devcontainer/` out of release packages. They are excluded by `build/exclude_files.txt`. [code: build/exclude_files.txt @7.x]
- Before you open a PR, run `ddev composer test`, `ddev composer phpstan` and `ddev composer cs`, plus `ddev composer run e2e-test` for UI changes. [code: AGENTS.md "PR Checklist" @7.x]

## How to test it
This area has no PHPUnit suite of its own. Check the environment with the commands below. Use mautic-testing for writing tests.
- Smoke check: log in at `https://<project>.ddev.site` as `admin` / `Maut1cR0cks!`, then run `ddev exec bin/console mautic:segments:update` and check `var/logs/mautic_dev-<date>.php`. [code: .ddev/mautic-setup.sh:29-35 @7.x]
- Installer behaviour is covered by `app/bundles/InstallBundle/Tests/Functional/InstallWorkflowTest.php` (drives `/installer`), `Tests/Command/InstallCommandTest.php` and `Tests/Install/InstallServiceTest.php`. [code: app/bundles/InstallBundle/Tests/Functional/InstallWorkflowTest.php:74-124 @7.x]
- CI checks fresh install and update packages in `release.yml`, and checks the recommended-project Composer layout in the `composer install` job of `tests.yml`. Copy these when you change install or asset tooling. [code: .github/workflows/tests.yml:278-303 @7.x]
- Run one PHPUnit file with `ddev exec composer test app/bundles/<Bundle>/Tests/<File>Test.php`. [code: .github/prompts/write-test.prompt.md:41 @7.x]

## Version notes
- 7.x: PHP 8.2–8.5, MySQL 8.4+ or MariaDB 10.11+. Twitter Bootstrap 5.3.8 (7.x after 7.2.1, unreleased [PR #17767]; 7.2.1 ships `bootstrap-sass` 3.4.1) is built through Symfony AssetMapper and the Sass bundle. Binaries are in `bin/`. [code: app/release_metadata.json:4-7 @7.x] [code: app/composer.json:15-105 @7.x]
- Before 5.1 the DDEV admin password was `mautic`. Since 5.1 a complex admin password is required. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
- Since 3.0, logs are in `var/logs` (2.x: `app/logs`) and cron uses `bin/console` (2.x: `app/console`). The config file is `config/local.php` (older: `app/config/local.php`). [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]
- 8.x (unreleased): PHP minimum 8.4, Symfony 8.1, PHPUnit 13. Tool binaries move to `vendor/bin/*`. Only ECS checks code style, because php-cs-fixer is removed and the pre-commit hook runs ECS. [code: app/composer.json @8.x] [code: composer.json @8.x]
- 8.x has not settled the UI asset stack: the 8.x snapshot still uses `twbs/bootstrap-sass 3.4.1` until 7.x is merged forward (the 7.x move to Bootstrap 5.3.8 is after 7.2.1 and unreleased; [PR #17767]). [code: composer.json @8.x]
Full detail is in `references/version-notes.md`.

## Pitfalls
- Re-running the managed setup (`ddev ddev-setup-mautic`, or deleting `.ddev/mautic-preference`) reinstalls Mautic. Your data survives only as `bak_*` tables. [code: .ddev/mautic-setup.sh:11-18 @7.x] [code: app/bundles/InstallBundle/Command/InstallCommand.php:183-194 @7.x]
- `doctrine:fixtures:load` (`d:f:l`) purges the database before it loads sample data. The KB PR-testing flow uses it for this reason. [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#doctrine-commands]
- `index_dev.php` does not exist in 7.x. The KB DDEV article says to use it for dev mode, but dev mode now comes from `APP_ENV=dev` in `.env.local`. [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html] [code: .ddev/.env.local.dist @7.x]
- The KB PR-testing article tells you to use Gitpod. The 7.x repo has no `.gitpod.yml`, and the PR template points to GitHub Codespaces instead. [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] [code: .github/PULL_REQUEST_TEMPLATE.md:59 @7.x]
- The setup script calls the mail catcher "MailHog" on port 8026. Codespaces docs call it Mailpit. Either way, mail sent to `smtp://localhost:1025` is captured and never delivered. [code: .ddev/mautic-setup.sh:6,32 @7.x] [code: .devcontainer/CODESPACES.md @7.x]
- The install docs say not to put `db_driver` or `mailer_from_name` in local.php before a CLI install, because they mark Mautic as installed. In code, only `db_driver` plus `site_url` mark it installed, and the DDEV template sets both keys and installs fine. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] [code: app/AppKernel.php:272-283 @7.x] [code: .ddev/local.config.php.dist @7.x]
- The building-assets devdocs say the UI uses Bootstrap 3.4.1. 7.x code ships `twbs/bootstrap` 5.3.8. [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/building_assets.html] [code: app/composer.json:15-105 @7.x]
- The install docs still give PHP 7.4 as minimum. 7.x needs PHP 8.2 or later. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#how-can-you-specify-a-php-version] [code: app/release_metadata.json:4 @7.x]
- DDEV runs PHP 8.5, but CI's minimum is 8.2. Code that only works on 8.3 or later passes locally and fails in CI. [code: .ddev/config.yaml:3 @7.x] [code: .github/workflows/tests.yml:22-32 @7.x]
- `bin/phpunit` without `-c app/phpunit.xml.dist` fails on the missing `KERNEL_CLASS`. `bin/phpstan` fails until the test container is warmed, which `composer phpstan` does for you. [code: app/phpunit.xml.dist:65-76 @7.x] [code: composer.json:171 @7.x]
- Settings that are read when the container is compiled need `cache:clear` after you edit local.php by hand. These include cookie security from the `site_url` scheme, the cache and log dirs, and the read replica. [code: app/config/config.php:35-44 @7.x] [code: app/AppKernel.php:316-334 @7.x]
- Doctrine proxy "failed to open stream" errors under `var/cache/prod` usually come from files owned by a user other than the web server user. [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html]
- Open question: the KB DDEV article gives `https://mautic.ddev.site`, but the setup script uses `https://${DDEV_HOSTNAME}`, which depends on the checkout directory name or DDEV project name. [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html] [code: .ddev/mautic-setup.sh:4 @7.x]

## Related skills
- mautic-testing: writing and running PHPUnit and Codeception tests, base classes and fixtures.
- mautic-configuration: what each local.php parameter means, precedence, and the installer internals.
- mautic-cron-and-queues: the full cron command list, Messenger transports and consumer options.
- mautic-contributing: branch targeting, PR template, code style and review norms.
- mautic-theme-development: theme assets and how they relate to the asset build.
- mautic-troubleshooting: production failures, permissions and resource limits.
- mautic-upgrades-and-versions: production updates, migrations and version support.

## Reference files
- `references/behaviour.md`: the numbered behaviour specification for DDEV, install, assets, logs, caches, credentials, PR testing and staging. Open it to check an exact rule.
- `references/code-map.md`: every file, script, command and generated path, with line references.
- `references/docs-digest.md`: what the devdocs, user docs and KB say, with URLs, procedures and stale claims.
- `references/version-notes.md`: 2.x–6.x history, 7.x state and the 8.x delta for tooling and platform.
- `references/test-patterns.md`: not needed for this skill. Testing is covered by mautic-testing.
- `references/pr-history.md`: not yet generated; PR-derived history is added in a later pass.
