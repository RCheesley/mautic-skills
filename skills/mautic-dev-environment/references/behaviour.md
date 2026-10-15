# Behaviour specification: Mautic development and test environment (7.x)

Every item states one observable behaviour and its source. "Managed setup" means the DDEV auto-install in
`.ddev/mautic-setup.sh`.

## Contents
1. Platform requirements
2. DDEV: configuration and lifecycle
3. DDEV: managed setup
4. Codespaces
5. Composer and the two-package layout
6. Front-end assets
7. Installing with mautic:install
8. Running console commands, cron and Messenger locally
9. Logs
10. Caches
11. Credentials
12. Test databases and test runs
13. Testing a pull request
14. Staging server for release testing
15. Common setup failures

## 1. Platform requirements
1.1 7.2.1 supports PHP 8.2.0 to 8.5.99, MySQL 8.4.0 or later and MariaDB 10.11.0 or later. [code: app/release_metadata.json:4-7 @7.x]
1.2 Composer resolves dependencies as if on PHP 8.2.0 (`config.platform.php`), whatever PHP runs Composer. [code: composer.json:195-198 @7.x]
1.3 A web request on a PHP version outside the supported range gets an HTTP 500 text response before the kernel runs. [code: app/middlewares/VersionCheckMiddleware.php:46-59 @7.x]
1.4 The installer stops on hard requirement failures. These are: `vendor/composer` missing, an unwritable config file, unwritable `cache_path` or `log_path`, an unrecognised default timezone, missing core functions (`json_encode`, `session_start`, `ctype_alpha`, `token_get_all`, `simplexml_import_dom`, `curl_init`, `finfo_open`, `mb_strtolower`), an unsupported OpenSSL cipher, the xdebug `show_exception_trace` or `scream` setting on, or no PDO MySQL driver. [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:73-152 @7.x] [code: app/bundles/InstallBundle/Configurator/Step/DoctrineStep.php:95-108 @7.x]
1.5 Recommendations only warn: `zip`, `date.timezone`, DOM, `iconv`, `xml`, `imap_open`, an https `site_url`, `memory_limit` of at least 512M, `intl`, a working `Collator`, and `zend.assertions = -1`. The CLI installer asks whether to continue unless you pass `--force`. [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:154-224 @7.x] [code: app/bundles/InstallBundle/Command/InstallCommand.php:245-260 @7.x]
1.6 The installer refuses MySQL below 8.4.0, MariaDB below 10.11.0 and any other database platform, with "Mautic only supports MySQL and MariaDB!". [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:177-201 @7.x]
1.7 The docs also ask for PHP `max_execution_time` of at least 240 seconds and a web-server-writable install directory. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#preparing-for-installation]

## 2. DDEV: configuration and lifecycle
2.1 The DDEV project is `type: php` with an empty docroot (the repo root), PHP 8.5, `apache-fpm`, timezone UTC, MariaDB 10.11, Node 24 and Composer 2. It installs the extra `php<ver>-imap` package. [code: .ddev/config.yaml:1-24 @7.x]
2.2 `media/files` and `media/images` are declared as upload dirs. [code: .ddev/config.yaml:16-18 @7.x]
2.3 The post-start hooks strip CRLF from `.ddev/mautic-setup.sh` and `.git/hooks/*`, make the script executable, run `yes | ./.ddev/mautic-setup.sh` and then `composer motd`. [code: .ddev/config.yaml:9-15 @7.x]
2.4 The add-ons are phpMyAdmin (ports 8036/8037, `ddev phpmyadmin`), Redis with redis-commander (`ddev redis-cli`), and Selenium standalone Chromium for Codeception. [code: .ddev/docker-compose.phpmyadmin.yaml @7.x] [code: .ddev/docker-compose.redis.yaml @7.x] [code: .ddev/docker-compose.selenium-chrome.yaml @7.x]
2.5 `.ddev/php/codeception.ini` turns on `register_argc_argv` and hides `E_DEPRECATED`, which Codeception on PHP 8.5 needs. [code: .ddev/php/codeception.ini @7.x]
2.6 DDEV defines no cron job and no Messenger worker. [code: .ddev/config.yaml:1-24 @7.x]
2.7 `ddev gjs-build` runs `npm ci` in `plugins/GrapesJsBuilderBundle` when `node_modules` is missing, then `npm run build-dev`. That build is unminified and uses `NODE_ENV=development`. [code: .ddev/commands/web/gjs-build @7.x] [code: plugins/GrapesJsBuilderBundle/package.json:18-19 @7.x]

## 3. DDEV: managed setup
3.1 On the first `ddev start` the script asks "Do you want us to set up the Mautic instance for you…". It writes `ddev-managed` or `unmanaged` to `.ddev/mautic-preference`. [code: .ddev/mautic-setup.sh:40-61 @7.x]
3.2 Because the hook pipes `yes` into the script, a non-interactive first start chooses the managed setup. [code: .ddev/config.yaml:14 @7.x]
3.3 While `.ddev/mautic-preference` exists, later starts do not run setup again. [code: .ddev/mautic-setup.sh:42 @7.x]
3.4 `MAUTIC_URL` defaults to `https://${DDEV_HOSTNAME}`, phpMyAdmin to port 8037 and the mail catcher to port 8026 on the same host. [code: .ddev/mautic-setup.sh:4-6 @7.x]
3.5 The managed setup runs these steps in order:
   1. `composer install`.
   2. Copy `.ddev/local.config.php.dist` to `config/local.php` and `.ddev/.env.test.local` to `.env.test.local`. Outside Codespaces, also copy `.ddev/.env.local.dist` to `.env.local`.
   3. `php bin/console mautic:install "${MAUTIC_URL}" --force --no-interaction`.
   4. `cache:warmup --env=dev`.
   5. `mautic:plugins:reload`.
   6. `npm ci && npm run build-dev` in `plugins/GrapesJsBuilderBundle`.

   [code: .ddev/mautic-setup.sh:8-25 @7.x]
3.6 At the end it prints the login `admin / Maut1cR0cks!`, the phpMyAdmin and mail URLs, and the commands `ddev exec composer test`, `ddev exec composer e2e-test` and `ddev exec bin/console COMMAND`. [code: .ddev/mautic-setup.sh:27-37 @7.x]
3.7 `config/local.php` from the template contains `api_enabled true`, `api_enable_basic_auth true`, `db_driver pdo_mysql`, `db_host db`, `db_port 3306`, `db_name db`, `db_user db`, `db_password db`, `db_table_prefix null`, `admin_email mautic@ddev.local`, `admin_password Maut1cR0cks!`, `install_source DDEV`, `mailer_from_name DDEV`, `mailer_from_email mautic@ddev.local` and `mailer_dsn smtp://localhost:1025`. [code: .ddev/local.config.php.dist @7.x]
3.8 `.env.local` from the template sets `APP_ENV=dev` and `APP_DEBUG=1`, so the DDEV site runs in the dev environment. [code: .ddev/.env.local.dist @7.x]
3.9 `ddev ddev-setup-mautic` sources the setup script, writes `ddev-managed` to the preference file and runs `setup_mautic` without asking. [code: .ddev/commands/web/ddev-setup-mautic @7.x]
3.10 Re-running the setup overwrites `config/local.php` with a template that has no `site_url`. Mautic therefore counts as not installed, and `mautic:install --force` runs again over the existing database. By default it renames existing tables to `bak_*` before it creates a new schema. [code: app/AppKernel.php:272-283 @7.x] [code: app/bundles/InstallBundle/Command/InstallCommand.php:183-194 @7.x] [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:119-175 @7.x]
3.11 The KB article describes the same flow: `gh repo clone mautic/mautic`, `ddev start`, answer yes, and log in at the DDEV URL. [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html]
3.12 The user docs give the same flow for contributors: install the GitHub CLI, fork Mautic to a personal account (not an organisation), clone, install DDEV and Docker (or Colima), then `ddev start`. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#cloning-mautic-from-github] [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/how_to_install_with_ddev.html]

## 4. Codespaces
4.1 The devcontainer is a Debian 12 image with docker-in-docker. `postCreateCommand` runs `.devcontainer/setup-project.sh`, which writes `.ddev/config.local.yaml` with Codespaces URLs and runs `ddev start`. Prebuilds run `ddev composer install`. [code: .devcontainer/setup-project.sh:14-30 @7.x] [code: .devcontainer/prebuild-project.sh @7.x]
4.2 In Codespaces, the managed setup does not copy `.env.local`. [code: .ddev/mautic-setup.sh:13-15 @7.x]
4.3 The readiness page gives username `admin`, password `Maut1cR0cks!`, and the Mailpit and phpMyAdmin URLs. [code: .devcontainer/CODESPACES-READY.tpl.md @7.x]
4.4 To test a PR in Codespaces, use the GitHub panel's "Checkout Pull Request by ID". Afterwards the `post-checkout` hook clears `var/cache` and runs `ddev composer install --no-interaction` and `doctrine:migrations:migrate -n`. [code: .devcontainer/CODESPACES.md @7.x] [code: build/hooks/post-checkout:3-12 @7.x]
4.5 Start a Codespace from the default branch, which takes about 4 minutes with prebuilds, rather than from a PR, which takes about 12 minutes without them. Then check out each PR inside it. [code: .devcontainer/CODESPACES.md:44-46 @7.x]
4.6 For CLI work, including emulating a cron job, run `ddev ssh` in the Codespace and run the commands there. [code: .devcontainer/CODESPACES.md @7.x]

## 5. Composer and the two-package layout
5.1 The root `composer.json` is the `mautic/mautic` distribution package. It requires `composer/installers`, `cweagans/composer-patches` and `mautic/core-lib ^7.0`, and holds all dev tooling in `require-dev`. [code: composer.json:23-56 @7.x]
5.2 `mautic/core-lib` is the `app/` directory, loaded as a path repository (as version `7.0.0-dev`). All runtime dependencies and the `Mautic\` autoload are declared in `app/composer.json`. [code: composer.json:124-148 @7.x] [code: app/composer.json:7-16 @7.x]
5.3 The root package declares that it replaces every `mautic/plugin-*`, `mautic/theme-*` and `mautic/grapes-js-builder-bundle` package. A monorepo split workflow publishes them. [code: composer.json:57-110 @7.x]
5.4 Installer paths: `mautic-core` packages go to `app`, `mautic-plugin` to `plugins/{$name}` and `mautic-theme` to `themes/{$name}`. [code: composer.json:212-233 @7.x]
5.5 With `bin-dir = bin`, `bin/phpunit`, `bin/phpstan`, `bin/rector`, `bin/ecs`, `bin/php-cs-fixer` and `bin/codecept` are generated and gitignored. Only `bin/console` and `bin/.htaccess` are tracked. [code: composer.json:195-211 @7.x] [code: .gitignore:62-64 @7.x]
5.6 `post-install-cmd` and `post-update-cmd` each run `@githooks`, `@npm-ci`, `@npx-patch-package`, `@gjs-build-safe`, `@generate-assets` and `@motd`. A `composer install` therefore needs Node and npm to finish its asset steps. [code: composer.json:153-168 @7.x]
5.7 `composer githooks` copies `build/hooks/pre-commit` (or `pre-commit.win`) and `post-checkout` into `.git/hooks/`. [code: composer.json:149-152 @7.x]
5.8 The `pre-commit` hook runs php-cs-fixer on staged PHP files and stages them again. [code: build/hooks/pre-commit:17-20 @7.x]
5.9 `app/composer.json` maps root files to templates in `app/assets/scaffold/files/`. CI fails when a root file and its template differ. [code: app/composer.json:112-133 @7.x] [code: .github/workflows/tests.yml:265-277 @7.x]
5.10 For a production-style install, the docs recommend the Recommended Project (`composer create-project mautic/recommended-project`), which serves from `docroot/`. CI checks that this layout installs and resolves `docroot` as the webroot. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#using-the-recommended-project] [code: .github/workflows/tests.yml:278-303 @7.x]
5.11 The project dir is the first ancestor of `app/` that contains `composer.json`. The webroot comes from `extra.mautic-scaffold.locations.web-root` or `extra.public-dir`. [code: app/AppKernel.php:290-311 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:272-305 @7.x]

## 6. Front-end assets
6.1 `npm ci` runs the `postinstall` script, which runs `npm run build` (`webpack --mode production`). [code: package.json:62-65 @7.x]
6.2 Webpack builds only the CKEditor 5 bundle: entry `app/assets/libraries/ckeditor/src/ckeditor.ts`, output `media/libraries/ckeditor/ckeditor.js` (UMD `ClassicEditor`), with its cache in `var/cache/js/webpack`. It does not build Mautic's `app.js` or `app.css`. [code: webpack.config.js:22-37 @7.x]
6.3 `npx patch-package` applies `patches/at.js+1.5.4.patch` and `patches/chosen-js+1.8.7.patch`. [code: composer.json:180 @7.x]
6.4 `importmap.php` registers one entrypoint, `app` → `app/bundles/CoreBundle/Assets/app.js`. That file only imports `./css/app.scss`. [code: importmap.php:3-12 @7.x]
6.5 AssetMapper maps `app/bundles/CoreBundle/Assets` and Bootstrap's dist JS, publishes under `/assets/build/` and runs with `missing_import_mode: strict`. Sass compiles `app/bundles/CoreBundle/Assets/css/app.scss` into `var/sass/`. [code: app/config/config.php:50-73 @7.x] [code: app/config/config.php:134-144 @7.x]
6.6 `composer sass:build` and `composer sass:watch` first delete `assets/build`, then run `bin/console sass:build` (with `--watch` for the second). [code: composer.json:183-191 @7.x]
6.7 `mautic:assets:generate` fails with "…does not exist. Execute `npm install`…" when `node_modules/` or `media/libraries/ckeditor/ckeditor.js` is missing. [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:51-63 @7.x]
6.8 Otherwise `mautic:assets:generate` takes these steps:
   1. Run `sass:build`, `importmap:install --no-interaction` and `asset-map:compile`.
   2. Install elFinder assets.
   3. Combine and minify every bundle's `Assets/css/*` and `Assets/js/*` into `media/css/{app,libraries}.css` and `media/js/{app,libraries}.js`.
   4. Copy libraries from `node_modules`, and minify `mautic-form-src.js` into `media/js/mautic-form.js`.
   5. Check that a fixed list of output files exists.

   [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:65-120 @7.x]
6.9 `composer generate-assets` runs `mautic:assets:generate`, then `assets:install --symlink --relative ./`. [code: composer.json:192 @7.x]
6.10 `composer gjs-build` runs `npm ci` and then `npm run build` (a Parcel production build) in `plugins/GrapesJsBuilderBundle`. [code: composer.json:181 @7.x] [code: plugins/GrapesJsBuilderBundle/package.json:18 @7.x]
6.11 During `composer install`, `gjs-build-safe` runs `build/gjs_build.php`. On failure it only prints "WARN: GrapesJS builder assets failed to build…" and exits 0. [code: build/gjs_build.php:5-13 @7.x]
6.12 These generated files are gitignored: `media/libraries/ckeditor/*`, `media/css/app.css`, `media/js/app.js` and related files, `assets/build/` and `var/sass/`. GrapesJS dist files are not tracked either. [code: .gitignore:66-105 @7.x] [code: .github/workflows/build-grapesjs-assets.yml:28 @7.x]
6.13 Release packages ship pre-built assets. The release workflow requires `assets/build/manifest.json` and `var/sass/app.output.css`. [code: .github/workflows/release.yml:71-72 @7.x]
6.14 The devdocs list `composer sass:build`, `composer sass:watch`, `composer generate-assets` and `bin/console mautic:assets:generate`. They also say `composer install` compiles Sass automatically. [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/building_assets.html]

## 7. Installing with mautic:install
7.1 Usage: `bin/console mautic:install <site_url> [step]`. The options are `--force`, `--db_driver`, `--db_host`, `--db_port`, `--db_name`, `--db_user`, `--db_password`, `--db_table_prefix`, `--db_backup_tables`, `--db_backup_prefix`, `--admin_firstname`, `--admin_lastname`, `--admin_username`, `--admin_email` and `--admin_password`. [code: app/bundles/InstallBundle/Command/InstallCommand.php:52-147 @7.x]
7.2 Values come from three layers, each overriding the one before: the built-in defaults (`pdo_mysql`, backup tables `true`, backup prefix `bak_`, admin `Admin Mautic`, username `admin`), then local.php `db_*`/`admin_*` keys, then CLI options. [code: app/bundles/InstallBundle/Command/InstallCommand.php:183-220 @7.x]
7.3 An existing `site_url` in local.php wins over the `site_url` argument. [code: app/bundles/InstallBundle/Command/InstallCommand.php:222-227 @7.x]
7.4 If Mautic is already installed, the command prints "Mautic already installed", exits 0 and changes nothing. [code: app/bundles/InstallBundle/Command/InstallCommand.php:155-159 @7.x]
7.5 Mautic counts as installed when local parameters contain non-empty `db_driver` and `site_url`. Because `db_driver` is always forced to `pdo_mysql` after loading, `site_url` in local.php is the effective switch. [code: app/AppKernel.php:272-283 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:217-219 @7.x]
7.6 Steps run in order: requirements, database (connect, then create the database if missing), schema, fixtures, admin user, final config. The final step writes a new `secret_key` and `site_url`, then marks every migration as executed. [code: app/bundles/InstallBundle/Command/InstallCommand.php:231-340 @7.x] [code: app/bundles/InstallBundle/Install/InstallService.php:514-547 @7.x]
7.7 Before the check, the installer creates the cache and log directories, so a fresh checkout is not reported as unwritable. [code: app/bundles/InstallBundle/Install/InstallService.php:205-215 @7.x]
7.8 The admin password needs at least 6 characters, and the web form also applies the `NotWeak` rule. The docs say a complex password is required from 5.1. [code: app/bundles/InstallBundle/Install/InstallService.php:416-509 @7.x] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
7.9 Exit codes are `(int) -$step`. A requirements failure therefore returns `0`, a database, schema or fixtures failure `-1`, an admin failure `-2`, and a final-step failure `-3`. [code: app/bundles/InstallBundle/Command/InstallCommand.php:243-338 @7.x]
7.10 Install loads only the `group_install` fixtures: the admin role, core Contact and Company fields, and default Reports. It loads no sample data. Sample data comes from `mautic:install:data`, which drops and recreates the schema, or from `doctrine:fixtures:load`. [code: app/bundles/InstallBundle/Install/InstallService.php:393-411 @7.x] [code: app/bundles/CoreBundle/Command/InstallDataCommand.php:6-90 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#doctrine-commands]
7.11 The `group_mautic_install_data` fixtures create the Users `admin` and `sales`, both with password `Maut1cR0cks!`, and the Roles `Administrators` and `Sales Team`. [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php:24-49 @7.x]
7.12 Before a fresh CLI install, the docs suggest putting DB, admin and mailer values in local.php. They say not to pre-set `db_driver` or `mailer_from_name`, but in code only `db_driver` plus `site_url` matter (see 7.5). [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
7.13 Use the web installer at `/installer` instead of the CLI if you prefer. Any request to an uninstalled instance is redirected there. [code: app/AppKernel.php:60-84 @7.x]

## 8. Running console commands, cron and Messenger locally
8.1 Run every PHP, Composer, console and PHPUnit command through DDEV: `ddev exec bin/console …`, `ddev composer …`, `ddev exec php bin/phpunit -c app/phpunit.xml.dist …`. [code: AGENTS.md "Command Execution Rule" @7.x]
8.2 The console reads `--env/-e` and `--no-debug` before bootstrap. With `--no-interaction` it prints timestamped output. The default environment is `prod` unless `APP_ENV` is set, and DDEV sets `APP_ENV=dev` through `.env.local`. [code: app/console-application.php:26-44 @7.x] [code: app/config/bootstrap.php:14-27 @7.x] [code: .ddev/.env.local.dist @7.x]
8.3 Nothing in DDEV runs Mautic's scheduled commands. To emulate cron, run the commands by hand, for example `mautic:segments:update`, `mautic:campaigns:update`, `mautic:campaigns:trigger` and `mautic:broadcasts:send`. The full list is in mautic-cron-and-queues. [code: .ddev/config.yaml:1-24 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]
8.4 With the default `messenger_dsn_email` and `messenger_dsn_hit` of `sync://`, email sends and page or email hits are handled inside the request. No consumer is needed. [code: app/bundles/MessengerBundle/Config/config.php:7-9 @7.x]
8.5 To test queued sending, set a queue transport under Settings > Configuration > Queue Settings (Doctrine needs no extension) and run `bin/console messenger:consume email`. When you run it from cron, give it at least one of `--memory-limit`, `--limit` or `--time-limit`. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#how-to-enable-the-queuing] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#process-email-queue-cron-job]
8.6 The mail catcher captures mail sent to the DDEV mailer DSN `smtp://localhost:1025`, so nothing leaves the machine. The setup script labels it MailHog on port 8026, and Codespaces docs call it Mailpit. [code: .ddev/local.config.php.dist @7.x] [code: .ddev/mautic-setup.sh:6,32 @7.x] [code: .devcontainer/CODESPACES.md @7.x]
8.7 Cron logging tip from the docs: append `>> file.log 2>&1` and use `--no-interaction --no-ansi`. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#tips-troubleshooting]

## 9. Logs
9.1 The log dir is `log_path`, default `%kernel.project_dir%/var/logs`. The kernel reads it from local.php only. [code: app/bundles/CoreBundle/Config/config.php:254 @7.x] [code: app/AppKernel.php:327-334 @7.x]
9.2 The Mautic channel writes to a rotating file named from `log_file_name`, default `mautic_%kernel.environment%.php`. Files are named by day, for example `mautic_dev-2026-10-15.php`. [code: app/bundles/CoreBundle/Config/config.php:256 @7.x] [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:12-24 @7.x] [code: app/bundles/ConfigBundle/Model/SysinfoModel.php:123-132 @7.x]
9.3 The Mautic log records debug level when `debug` is true or `MAUTIC_ENV` is `dev`. Otherwise it records notice level and above. [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:17-18 @7.x]
9.4 In prod, channels other than `mautic` go to `var/logs/prod.php` at error level, keeping 7 files. In dev they go to `var/logs/dev.php` at debug level, keeping 7 files. [code: app/config/config_prod.php:45-49 @7.x] [code: app/config/config_dev.php:58-64 @7.x]
9.5 The test environment logs to `var/logs/test.php` and `var/logs/mautic_test.php` at the `MAUTIC_DEBUG_LEVEL` level, default `error`. [code: app/config/config_test.php:81-111 @7.x]
9.6 Settings > System Info shows the last 200 lines of today's Mautic log. [code: app/bundles/ConfigBundle/Model/SysinfoModel.php:123-132 @7.x]
9.7 Before 3.0 logs were in `app/logs`. [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html]

## 10. Caches
10.1 The Symfony cache dir is `<cache_path>/<env>`, default `var/cache/<env>`. [code: app/AppKernel.php:316-325 @7.x]
10.2 `bin/console cache:clear` rebuilds the container cache for the current environment. [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-is-available]
10.3 `mautic:cache:clear` calls `clear()` on Mautic's cache adapter only, for example Segment counts and dashboard widgets. It does not touch the container cache. [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:7-22 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html]
10.4 `rm -rf var/cache` clears every environment's cache, including the test schema dumps. Run it after entity changes and before re-running functional tests. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-213 @7.x]
10.5 Saving the Configuration UI only invalidates opcache for local.php and clears APCu. It does not rebuild the container. [code: app/bundles/CoreBundle/Helper/CacheHelper.php:37-42 @7.x]
10.6 Some values are read when the container is compiled. These are the cookie `secure` flag from the `site_url` scheme, `db_host_ro`, the cache and log dirs, and https route forcing. They need `cache:clear` after a hand edit of local.php. [code: app/config/config.php:35-44 @7.x] [code: app/AppKernel.php:316-334 @7.x]
10.7 The `post-checkout` git hook deletes `var/cache` on every checkout. [code: build/hooks/post-checkout:3-4 @7.x]
10.8 In the dev environment, `bootstrap.php` clears APCu for allowed IPs. [code: app/config/bootstrap.php:23-32 @7.x]

## 11. Credentials
11.1 DDEV install: username `admin` (the installer default), password `Maut1cR0cks!` (from local.php), email `mautic@ddev.local`. [code: app/bundles/InstallBundle/Command/InstallCommand.php:195-198 @7.x] [code: .ddev/local.config.php.dist @7.x]
11.2 Codespaces: `admin` / `Maut1cR0cks!`. [code: .devcontainer/CODESPACES-READY.tpl.md @7.x]
11.3 Sample-data fixtures: `admin` / `Maut1cR0cks!` (`admin@yoursite.com`) and `sales` / `Maut1cR0cks!` (`sales@yoursite.com`). [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php:24-49 @7.x]
11.4 PHPUnit functional tests authenticate as `admin` / `Maut1cR0cks!` through HTTP basic auth server variables. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:48-49 @7.x]
11.5 Codeception `login()` defaults to `admin` / `Maut1cR0cks!`. [code: tests/_support/AcceptanceTester.php:27 @7.x]
11.6 `.env.test` sets `MAUTIC_ADMIN_USERNAME=admin` and `MAUTIC_ADMIN_PASSWORD=mautic`. No PHP, YAML or workflow file in the tree reads either variable (checked with grep over `app`, `tests` and `.github`). [code: .env.test:10-11 @7.x]
11.7 The docs give `Maut1cR0cks!` as the DDEV password and `mautic` for versions before 5.1. The KB PR-testing article still gives `admin` / `mautic`. The KB DDEV article gives `Maut1cR0cks!` for both DDEV and Gitpod. Resolution: in 7.x, use `admin` / `Maut1cR0cks!` for DDEV, Codespaces, fixtures and tests. `admin` / `mautic` applies only to pre-5.1 environments and to old Gitpod images. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev] [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html]
11.8 The DDEV database credentials are `db` / `db`, database `db`, host `db`. [code: .ddev/local.config.php.dist @7.x]

## 12. Test databases and test runs
12.1 Under DDEV, `.env.test.local` points PHPUnit at host `db`, user `db`, password `db`, database `test`. [code: .ddev/.env.test.local @7.x]
12.2 Without it, `.env.test` uses `127.0.0.1:3306`, user `root` with an empty password, and database `mautictest`, as CI does. [code: .env.test:2-6 @7.x]
12.3 Test tables are prefixed `test_` (`MAUTIC_DB_PREFIX`). [code: .env.test:7-8 @7.x] [code: app/bundles/CoreBundle/Test/Extensions/DbPrefix/DbPrefix.php:21-27 @7.x]
12.4 `composer test` runs `bin/phpunit -d memory_limit=2G --bootstrap vendor/autoload.php --configuration app/phpunit.xml.dist` and accepts a path argument. [code: composer.json:169 @7.x] [code: .github/prompts/write-test.prompt.md:41 @7.x]
12.5 `composer e2e-test` runs `APP_ENV=test bin/codecept run acceptance` and needs the DDEV Selenium service. [code: composer.json:170 @7.x]
12.6 `composer phpstan` first boots the test kernel so that `var/cache/test/AppKernelTestDebugContainer.xml` exists. [code: composer.json:171 @7.x]

## 13. Testing a pull request
13.1 The PR template asks testers to open the PR in GitHub Codespaces or pull it down to test locally. It links to the community handbook's tester page. [code: .github/PULL_REQUEST_TEMPLATE.md:54-59 @7.x]
13.2 The KB flow, adapted to 7.x:
   1. Reproduce the bug on the base branch first, loading sample data with `ddev exec bin/console d:f:l` (this purges the database).
   2. Check out the PR.
   3. Retest.
   4. Submit an "Approve" or "Request changes" review.

   Each PR needs testing by two people. [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]
13.3 The KB article runs this flow in Gitpod. The 7.x tree has no Gitpod configuration, so use DDEV or Codespaces. [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] [code: .devcontainer/CODESPACES.md @7.x]
13.4 Local PR checkout in DDEV takes these steps:
   1. Fetch and check out the PR branch. The `post-checkout` hook clears `var/cache`.
   2. Run `ddev composer install`, which also rebuilds assets.
   3. Run `ddev exec bin/console doctrine:migrations:migrate -n` if the PR adds migrations.
   4. Run `ddev gjs-build` if it touches the builder.

   [code: build/hooks/post-checkout:3-12 @7.x] [code: composer.json:153-160 @7.x]
13.5 Release cadence that shapes what you test: bug fixes monthly, features quarterly, breaking changes about once a year. [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]

## 14. Staging server for release testing
14.1 KB flow:
   1. Comment out Mautic cron jobs on production.
   2. Snapshot the server.
   3. Boot a clone.
   4. Change the vhost `ServerName` and `site_url` in local.php.
   5. Run `cache:clear`.
   6. Run the update, migrations and schema commands.
   7. Check System Info > Error Log.

   [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html]
14.2 On staging, route outgoing mail to a catcher such as MailHog. SMS and push notifications are not captured. [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html]
14.3 `update_stability` (for example `beta`) appears in local.php only after the configuration has been saved once in the UI. [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html]
14.4 The staging KB article dates from 3.x. Its paths (`app/config/local.php`) and update commands (`mautic:update:find/apply`) are pre-5. On Composer installs, use the Composer update procedure in mautic-upgrades-and-versions. [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-mautic-composer-based-installs]
14.5 Always have a tested backup, with files and database restored into a test environment, before you update. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-at-the-command-line-non-composer-based-installations]

## 15. Common setup failures
15.1 "`node_modules` … does not exist" or "`…/ckeditor.js` does not exist. Execute `npm install`": run `npm ci` (or `ddev exec npm ci`), then `composer generate-assets`. [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:51-63 @7.x]
15.2 The builder does not load after `composer install`, and the output showed "WARN: GrapesJS builder assets failed to build": run `composer gjs-build` or `ddev gjs-build`. [code: build/gjs_build.php:7-10 @7.x]
15.3 PHPUnit reports a missing `KERNEL_CLASS`: pass `-c app/phpunit.xml.dist` or use `composer test`. [code: app/phpunit.xml.dist:65-76 @7.x]
15.4 PHPStan reports "Container var/cache/test/AppKernelTestDebugContainer.xml does not exist": use `composer phpstan`, which warms the test container. [code: composer.json:171 @7.x]
15.5 Functional tests fail with "Base table or view not found" or "Unknown column" after entity changes: `rm -rf var/cache`. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:194-213 @7.x]
15.6 `mautic:install` prints "Mautic already installed" and does nothing: `site_url` and `db_driver` are already in local.php. Remove `site_url`, or the file, to reinstall. [code: app/bundles/InstallBundle/Install/InstallService.php:125-139 @7.x]
15.7 A database connection error on every page after install: when not in installer mode, the kernel connects to the database before it handles the request and throws `DatabaseConnectionException`. Check the `db_*` values in local.php. [code: app/AppKernel.php:90-99 @7.x]
15.8 `Allowed memory size … exhausted`: raise `memory_limit`. `Class 'ZipArchive' not found`: install the PHP `zip` extension. [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#there-is-a-php-error-when-running-a-command]
15.9 Doctrine proxy "failed to open stream" under `var/cache/prod/doctrine/orm/Proxies`: fix file ownership so it matches the web server user. [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html]
15.10 `Invalid argument supplied for foreach()` in `ArgvInput.php` from cron: the host's `php` drops arguments. Use `php-cli` or `php -d register_argc_argv=On`. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#tips-troubleshooting]
15.11 A 404 or "autoload.php" error on a Recommended Project install: the web root must point at `docroot/`, and Apache needs `AllowOverride All`. [kb: https://kb.mautic.org/article/how-to-install-mautic-5-on-ubuntu-22-04-with-ssl-and-node-js-20.html]
15.12 CI fails "scaffolded files mismatch": copy your root-file change into `app/assets/scaffold/files/`. [code: .github/workflows/tests.yml:265-277 @7.x]
15.13 A crashed config-writing test can leave `config/local.php.backup` behind. Restore it by hand. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:334-343 @7.x]
