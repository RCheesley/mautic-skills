# Code map: Mautic development and test environment (7.x)

All paths are relative to the repository root of `mautic/mautic` 7.x (commit 419a08a9b35).

## 1. DDEV (`.ddev/`)
| File | Role | Source |
|---|---|---|
| `.ddev/config.yaml` | Project type php, docroot `""`, PHP 8.5, apache-fpm, UTC, MariaDB 10.11, Node 24, Composer 2, extra package `php${DDEV_PHP_VERSION}-imap`, upload dirs, post-start hooks | [code: .ddev/config.yaml:1-24 @7.x] |
| `.ddev/mautic-setup.sh` | `setup_mautic()` (install, copy config/env, `mautic:install`, warmup, plugin reload, GrapesJS build) and the first-run question | [code: .ddev/mautic-setup.sh:3-61 @7.x] |
| `.ddev/mautic-preference` | Generated; `ddev-managed` or `unmanaged`; its presence skips setup | [code: .ddev/mautic-setup.sh:42-60 @7.x] |
| `.ddev/local.config.php.dist` | Template for `config/local.php` (DB `db`, admin password, mailer DSN, API on) | [code: .ddev/local.config.php.dist @7.x] |
| `.ddev/.env.local.dist` | Template for `.env.local`: `APP_ENV=dev`, `APP_DEBUG=1` | [code: .ddev/.env.local.dist @7.x] |
| `.ddev/.env.test.local` | Copied to `.env.test.local`: test DB `test` on host `db` | [code: .ddev/.env.test.local @7.x] |
| `.ddev/commands/web/ddev-setup-mautic` | `ddev ddev-setup-mautic`: force managed setup | [code: .ddev/commands/web/ddev-setup-mautic @7.x] |
| `.ddev/commands/web/gjs-build` | `ddev gjs-build`: `npm ci` if needed, `npm run build-dev` in the GrapesJS plugin | [code: .ddev/commands/web/gjs-build @7.x] |
| `.ddev/commands/host/phpmyadmin`, `.ddev/commands/redis/redis-cli` | Helper commands | [code: .ddev/commands @7.x] |
| `.ddev/docker-compose.phpmyadmin.yaml` | phpMyAdmin on 8036/8037 | [code: .ddev/docker-compose.phpmyadmin.yaml @7.x] |
| `.ddev/docker-compose.redis.yaml`, `docker-compose.redis-commander.yaml`, `.ddev/redis/` | Redis and its web UI | [code: .ddev/docker-compose.redis.yaml @7.x] |
| `.ddev/docker-compose.selenium-chrome.yaml`, `config.selenium-standalone-chrome.yaml` | Selenium Chromium for Codeception | [code: .ddev/docker-compose.selenium-chrome.yaml @7.x] |
| `.ddev/php/codeception.ini` | `register_argc_argv = On`, `error_reporting = E_ALL & ~E_DEPRECATED` | [code: .ddev/php/codeception.ini:3-7 @7.x] |

## 2. Codespaces (`.devcontainer/`)
| File | Role | Source |
|---|---|---|
| `devcontainer.json` | Debian 12, docker-in-docker, opens `CODESPACES.md` | [code: .devcontainer/devcontainer.json:33-35 @7.x] |
| `setup-project.sh` | Writes `.ddev/config.local.yaml` with Codespaces URLs; `ddev start` | [code: .devcontainer/setup-project.sh:14-30 @7.x] |
| `prebuild-project.sh` | `ddev composer install` for prebuilds | [code: .devcontainer/prebuild-project.sh @7.x] |
| `post-attach.sh`, `CODESPACES-READY.tpl.md` | Ready page with URLs and `admin` / `Maut1cR0cks!` | [code: .devcontainer/CODESPACES-READY.tpl.md @7.x] |
| `CODESPACES.md` | PR checkout instructions, Mailpit, phpMyAdmin, CLI, boot tips | [code: .devcontainer/CODESPACES.md @7.x] |

## 3. Composer
| Item | Location | Source |
|---|---|---|
| Root package `mautic/mautic` `require` | `composer.json:23-27` | [code: composer.json:23-27 @7.x] |
| `require-dev` (PHPUnit 11.5, PHPStan 2, Rector dev-main, php-cs-fixer, ECS, Codeception 5, liip test bundles) | `composer.json:28-56` | [code: composer.json:28-56 @7.x] |
| `replace` (plugins, themes, GrapesJS bundle) | `composer.json:57-110` | [code: composer.json:57-110 @7.x] |
| Path repo `app` = `mautic/core-lib` | `composer.json:124-148` | [code: composer.json:124-148 @7.x] |
| Scripts | `composer.json:149-193` | [code: composer.json:149-193 @7.x] |
| `config` (platform php 8.2.0, `bin-dir bin`, `component-dir media/assets`, `process-timeout 5000`) | `composer.json:195-211` | [code: composer.json:195-211 @7.x] |
| `extra.installer-paths`, `extra.patches` | `composer.json:212-240` | [code: composer.json:212-240 @7.x] |
| Core-lib manifest (runtime deps, `Mautic\` autoload, scaffold file map, `pre-autoload-dump`) | `app/composer.json` | [code: app/composer.json:7-136 @7.x] |
| Scaffold templates | `app/assets/scaffold/files/` | [code: app/composer.json:112-133 @7.x] |

### Composer scripts
| Script | Runs | Source |
|---|---|---|
| `githooks` | Copy `build/hooks/pre-commit[.win]` and `post-checkout` into `.git/hooks`, chmod 0755 | [code: composer.json:149-152 @7.x] |
| `post-install-cmd`, `post-update-cmd` | `@githooks @npm-ci @npx-patch-package @gjs-build-safe @generate-assets @motd` | [code: composer.json:153-168 @7.x] |
| `test` | `bin/phpunit -d memory_limit=2G --bootstrap vendor/autoload.php --configuration app/phpunit.xml.dist` | [code: composer.json:169 @7.x] |
| `e2e-test` | `APP_ENV=test bin/codecept run acceptance` | [code: composer.json:170 @7.x] |
| `phpstan`, `phpstan-baseline` | Warm the test container, then `bin/phpstan analyse` | [code: composer.json:171-172 @7.x] |
| `cs`, `fixcs`, `rector` | php-cs-fixer dry run; php-cs-fixer fix + `ecs --fix`; `rector process` | [code: composer.json:173-178 @7.x] |
| `npm-ci`, `npx-patch-package` | `npm ci --prefer-offline --no-audit`; `npx patch-package` | [code: composer.json:179-180 @7.x] |
| `gjs-build`, `gjs-build-safe` | Full GrapesJS build; non-fatal wrapper `build/gjs_build.php` | [code: composer.json:181-182 @7.x] |
| `asset-map:clean`, `sass:build`, `sass:watch` | Delete `assets/build`; `bin/console sass:build [--watch]` | [code: composer.json:183-191 @7.x] |
| `generate-assets` | `bin/console mautic:assets:generate && bin/console assets:install --symlink --relative ./` | [code: composer.json:192 @7.x] |
| `motd` | `bin/console mautic:motd` | [code: composer.json:193 @7.x] |

## 4. Front-end build
| Item | Location | Source |
|---|---|---|
| npm manifest (`build`, `postinstall`, CKEditor 5, jQuery, Chart.js and others) | `package.json` | [code: package.json:5-65 @7.x] |
| CKEditor webpack build | `webpack.config.js` → `media/libraries/ckeditor/ckeditor.js` | [code: webpack.config.js:14-37 @7.x] |
| npm patches | `patches/at.js+1.5.4.patch`, `patches/chosen-js+1.8.7.patch` | [code: composer.json:180 @7.x] |
| Importmap entry | `importmap.php` → `app/bundles/CoreBundle/Assets/app.js` | [code: importmap.php:3-12 @7.x] |
| AssetMapper and Sass config | `app/config/config.php:50-73`, `:134-144` | [code: app/config/config.php:50-73 @7.x] |
| Sass source | `app/bundles/CoreBundle/Assets/css/app.scss` | [code: app/config/config.php:134-144 @7.x] |
| TypeScript config | `tsconfig.json` (strict, es2019, `include: []`) | [code: tsconfig.json:7-21 @7.x] |
| Asset generation command `mautic:assets:generate` | `app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php` | [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:32-120 @7.x] |
| Bundle asset combiner | `app/bundles/CoreBundle/Helper/AssetGenerationHelper.php` | [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:81 @7.x] |
| GrapesJS plugin build (`build`, `build-dev`, `rebuild-dev`, Parcel) | `plugins/GrapesJsBuilderBundle/package.json` | [code: plugins/GrapesJsBuilderBundle/package.json:18-22 @7.x] |
| Non-fatal GrapesJS wrapper | `build/gjs_build.php` | [code: build/gjs_build.php:1-13 @7.x] |

### Generated paths (all gitignored)
| Path | Produced by | Source |
|---|---|---|
| `node_modules/` | `npm ci` | [code: .gitignore:66-105 @7.x] |
| `media/libraries/ckeditor/*` | webpack (`npm run build`) | [code: webpack.config.js:28-37 @7.x] |
| `media/css/app.css`, `media/css/libraries.css`, `media/js/app.js`, `media/js/libraries.js`, `media/js/mautic-form.js` | `mautic:assets:generate` | [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:80-96 @7.x] |
| `var/sass/` | `sass:build` | [code: .gitignore:68-69 @7.x] |
| `assets/build/` (incl. `manifest.json`) | `asset-map:compile` | [code: .gitignore:67 @7.x] |
| `plugins/GrapesJsBuilderBundle/Assets/library/js/dist/` | Parcel build | [code: plugins/GrapesJsBuilderBundle/package.json:18-19 @7.x] |
| `var/cache/js/webpack` | webpack filesystem cache | [code: webpack.config.js:22-25 @7.x] |

## 5. Git hooks and build tooling (`build/`)
| File | Role | Source |
|---|---|---|
| `build/hooks/pre-commit` | php-cs-fixer on staged files, re-add | [code: build/hooks/pre-commit:17-20 @7.x] |
| `build/hooks/post-checkout` | `rm -rf var/cache`; in Codespaces also `ddev composer install` and migrations | [code: build/hooks/post-checkout:1-12 @7.x] |
| `build/package_release.php` | Build release and update ZIPs (`-b=<branch-or-tag>`) | [code: build/package_release.php:8-274 @7.x] |
| `build/exclude_files.txt` | Excludes `.ddev/*`, `.devcontainer/*`, test tooling from packages | [code: build/exclude_files.txt @7.x] |
| `build/processfiles.php` | Deletes tests, dev config and caches from packages | [code: build/processfiles.php:9-32 @7.x] |

## 6. Install, bootstrap and platform
| Concern | Location | Source |
|---|---|---|
| CLI installer `mautic:install` | `app/bundles/InstallBundle/Command/InstallCommand.php` | [code: app/bundles/InstallBundle/Command/InstallCommand.php:52-445 @7.x] |
| Install steps service | `app/bundles/InstallBundle/Install/InstallService.php` | [code: app/bundles/InstallBundle/Install/InstallService.php:41-547 @7.x] |
| Requirement checks | `app/bundles/InstallBundle/Configurator/Step/CheckStep.php`, `DoctrineStep.php` | [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:73-224 @7.x] |
| DB version check, backup of existing tables | `app/bundles/InstallBundle/Helper/SchemaHelper.php` | [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:119-201 @7.x] |
| Web installer | `app/bundles/InstallBundle/Controller/InstallController.php` (`/installer`) | [code: app/bundles/InstallBundle/Controller/InstallController.php:39-263 @7.x] |
| Sample data | `mautic:install:data` (`app/bundles/CoreBundle/Command/InstallDataCommand.php`); fixtures `app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php`, `LoadRoleData.php` | [code: app/bundles/CoreBundle/Command/InstallDataCommand.php:6-90 @7.x] |
| "Installed" check | `app/AppKernel.php:272-283` | [code: app/AppKernel.php:272-283 @7.x] |
| `.env` loading, `APP_ENV`/`APP_DEBUG` defaults | `app/config/bootstrap.php:14-32` | [code: app/config/bootstrap.php:14-32 @7.x] |
| Console bootstrap | `bin/console`, `app/console-application.php` | [code: app/console-application.php:26-51 @7.x] |
| Platform versions | `app/release_metadata.json` | [code: app/release_metadata.json:4-10 @7.x] |
| PHP version gate | `app/middlewares/VersionCheckMiddleware.php` | [code: app/middlewares/VersionCheckMiddleware.php:46-59 @7.x] |
| Dev IP restriction (DDEV allowed) | `app/middlewares/Dev/IpRestrictMiddleware.php` | [code: app/middlewares/Dev/IpRestrictMiddleware.php:27-56 @7.x] |

## 7. Logs and caches
| Concern | Location | Source |
|---|---|---|
| `log_path`, `log_file_name` defaults | `app/bundles/CoreBundle/Config/config.php:254-256` | [code: app/bundles/CoreBundle/Config/config.php:254-256 @7.x] |
| Mautic log handler | `app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php` | [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:10-24 @7.x] |
| Dev and prod monolog | `app/config/config_dev.php:58-82`, `app/config/config_prod.php:40-58` | [code: app/config/config_dev.php:58-82 @7.x] |
| Test monolog | `app/config/config_test.php:81-111` | [code: app/config/config_test.php:81-111 @7.x] |
| Kernel cache and log dirs | `app/AppKernel.php:316-334` | [code: app/AppKernel.php:316-334 @7.x] |
| `mautic:cache:clear` | `app/bundles/CacheBundle/Command/ClearCacheCommand.php` | [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:7-22 @7.x] |
| Cache helper (`refreshConfig`, `nukeCache`, `clearSymfonyCache`) | `app/bundles/CoreBundle/Helper/CacheHelper.php` | [code: app/bundles/CoreBundle/Helper/CacheHelper.php:26-85 @7.x] |
| System Info log tail | `app/bundles/ConfigBundle/Model/SysinfoModel.php:123-132` | [code: app/bundles/ConfigBundle/Model/SysinfoModel.php:123-132 @7.x] |

## 8. Messenger defaults (for local queue testing)
| Parameter | Default | Source |
|---|---|---|
| `messenger_dsn_email` | `sync://` | [code: app/bundles/MessengerBundle/Config/config.php:7 @7.x] |
| `messenger_dsn_hit` | `sync://` | [code: app/bundles/MessengerBundle/Config/config.php:8 @7.x] |
| `messenger_dsn_failed` | `null` (becomes `null://`) | [code: app/bundles/MessengerBundle/Config/config.php:9 @7.x] |
| Transport definitions and routing | `app/config/config.php:102-127` | [code: app/config/config.php:102-127 @7.x] |

## 9. Test environment files
| File | Content | Source |
|---|---|---|
| `.env.test` | `DB_HOST=127.0.0.1`, `DB_PORT=3306`, `DB_NAME=mautictest`, `DB_USER=root`, empty password, prefix `test_`, `MAUTIC_ENV=test`, unused admin vars, SAML host/port | [code: .env.test:1-13 @7.x] |
| `.env.test.local` (DDEV copy) | `DB_HOST=db`, `DB_USER=db`, `DB_PASSWD=db`, `DB_NAME=test` | [code: .ddev/.env.test.local @7.x] |
| `app/phpunit.xml.dist` | `KERNEL_CLASS=AppTestKernel`, `APP_ENV=test`, extensions | [code: app/phpunit.xml.dist:65-82 @7.x] |
| `codeception.yml`, `tests/` | E2E suite; `AcceptanceTester::login('admin','Maut1cR0cks!')` | [code: tests/_support/AcceptanceTester.php:27 @7.x] |
| `AGENTS.md`, `.agents/skills/mautic-dev/SKILL.md` | In-repo agent guidance (run via DDEV, PR checklist) | [code: AGENTS.md @7.x] |

## 10. CI jobs that exercise the environment
| Workflow | What it proves | Source |
|---|---|---|
| `tests.yml` `phpunit` | PHP 8.2/8.5 × MySQL 8.4/9.2 × MariaDB 10.11/11.4 matrix | [code: .github/workflows/tests.yml:22-32 @7.x] |
| `tests.yml` `e2e-tests` | DDEV in CI (`ddev/github-action-setup-ddev`), `ddev exec composer e2e-test` | [code: .github/workflows/tests.yml:155-179 @7.x] |
| `tests.yml` `misc` scaffold diff | Root files equal their scaffold templates | [code: .github/workflows/tests.yml:265-277 @7.x] |
| `tests.yml` `misc` composer install | Recommended-project layout installs, `docroot` webroot | [code: .github/workflows/tests.yml:278-303 @7.x] |
| `build-grapesjs-assets.yml` | GrapesJS builds on Node 24 | [code: .github/workflows/build-grapesjs-assets.yml:28 @7.x] |
| `release.yml` | Fresh-install and update-install tests of the release ZIPs | [code: .github/workflows/release.yml:184-250 @7.x] |
| `api-library-tests.yml` | Apache + PHP 8.3 install with `mautic:install http://localhost/ --force --env=test` | [code: .github/workflows/api-library-tests.yml:61-66 @7.x] |
