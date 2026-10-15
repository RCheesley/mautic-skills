# Docs digest: Mautic development and test environment

What the official user docs (docs.mautic.org), developer docs (devdocs.mautic.org) and knowledge base (kb.mautic.org)
say about setting up and running development, test and staging instances. Where a page is out of date for 7.x, the
item says so and gives the current behaviour from code.

## 1. Source pages
| Topic | URL |
|---|---|
| Developer environment: getting started | https://devdocs.mautic.org/en/7.2/development-environment/getting_started.html |
| Install with DDEV | https://devdocs.mautic.org/en/7.2/development-environment/how_to_install_with_ddev.html |
| Manual dev setup | https://devdocs.mautic.org/en/7.2/development-environment/setup.html |
| Environments and `.env` files | https://devdocs.mautic.org/en/7.2/development-environment/environments.html |
| Building assets | https://devdocs.mautic.org/en/7.2/development-environment/building_assets.html |
| How to install Mautic | https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html |
| How to update Mautic | https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html |
| Command line interface | https://docs.mautic.org/en/7.2/configuration/command_line_interface.html |
| Cron jobs | https://docs.mautic.org/en/7.2/configuration/cron_jobs.html |
| Queue settings | https://docs.mautic.org/en/7.2/configuration/settings.html#queue-settings |
| Troubleshooting | https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html |
| File ownership and permissions | https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html |
| KB: test bug fixes and features | https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html |
| KB: local testing with DDEV | https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html |
| KB: staging server for releases | https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html |
| KB: rebase and sync a fork | https://kb.mautic.org/article/how-to-rebase-branch-and-sync-forked-repository-with-upstream-using-git.html |

The developer-environment pages are unchanged in the 8.0 devdocs branch. [devdocs: https://devdocs.mautic.org/en/8.0/]

## 2. Documented behaviour
1. The DDEV default login is `admin` / `Maut1cR0cks!`. Before 5.1 it was `mautic`. DDEV includes a mail catcher, phpMyAdmin and Redis Commander, at `https://mautic.ddev.site` in the docs' example. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev] [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/how_to_install_with_ddev.html]
2. Fork into a personal account, not an organisation. Otherwise maintainers cannot push to your PR branch. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#cloning-mautic-from-github]
3. `.env` files load in this order, each overriding the one before: `.env`, `.env.local`, `.env.$APP_ENV`, `.env.$APP_ENV.local`. Real environment variables override all of them. Do not commit secrets. `composer dump-env prod` compiles the env. [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/environments.html]
4. `.env` defaults to `APP_ENV=prod` and `APP_DEBUG=0`. [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/environments.html#development-environment]
5. Asset commands: `composer sass:build`, `composer sass:watch` (sources in `app/bundles/CoreBundle/Assets/css/`), `composer generate-assets` and `bin/console mautic:assets:generate`. `composer install` compiles Sass automatically. The UI uses Symfony AssetMapper with Importmap. [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/building_assets.html]
6. Install prerequisites: the requirements page, a web-server-writable directory, a database with the right permissions, and PHP `max_execution_time` of at least 240 seconds. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#preparing-for-installation]
7. In the web installer, red errors block and orange items are recommendations. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#conducting-environment-checks]
8. "Backup existing tables?" is on by default. Turn it off for new installs. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#integrating-the-database]
9. CLI install: `php bin/console mautic:install <site_url> [options]`, with defaults `--db_driver=pdo_mysql`, `--db_backup_tables=true` and `--db_backup_prefix=bak_`. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
10. The CLI installer warns when `memory_limit` is below 512M. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-a-local-php-file]
11. Run the CLI from the Mautic root. The default environment is `prod`. `mautic:cache:clear` erases the 10-minute Mautic cache (Segment counts, dashboard widgets). [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html]
12. `doctrine:fixtures:load` installs sample data and overwrites existing data. [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#doctrine-commands]
13. Queueing is off by default, because the queue DSN is `sync://`. Consumers run `php bin/console messenger:consume email`. In production, keep them alive with Supervisor or systemd. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mautic-doesn-t-use-queues-by-default] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#how-to-consume-messages-from-the-queue]
14. A `messenger:consume` started from cron needs `--memory-limit`, `--limit` or `--time-limit`. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#process-email-queue-cron-job]
15. Since Mautic 3 the cron path is `bin/console`. Without cron jobs, nothing happens in Mautic. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html] [kb: https://kb.mautic.org/article/getting-started-with-mautic.html]
16. Recovery order after a failed update: clear the cache (`cache:clear` or `rm -rf var/cache`), run `mautic:update:find`/`apply`, check `doctrine:migration:status`, then `migrate`. [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-is-available]
17. Recommended permissions: files 644, directories 755, and group-writable `var/cache`, `var/logs`, `app/config`, `media/files`, `media/images` and `translations`. [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html#reset-the-file-and-folder-permissions]
18. Logs are in `var/logs` for Mautic 3.0+ and in `app/logs` for 2.x. The config file is `config/local.php` for 4.0+ and `app/config/local.php` for 3.x and older. [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html]
19. Release cadence: bug fixes monthly, features quarterly, breaking changes about once a year. [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]
20. The default development branch has a versioned name such as `7.x`. [kb: https://kb.mautic.org/article/how-to-rebase-branch-and-sync-forked-repository-with-upstream-using-git.html]

## 3. Procedures
### 3.1 Set up locally with DDEV (devdocs, KB)
1. Install Docker (or Colima), DDEV and the GitHub CLI.
2. Fork `mautic/mautic` to your personal account and clone it (`gh repo clone <you>/mautic`).
3. Run `ddev start` and answer "yes" to the setup question.
4. Log in as `admin` / `Maut1cR0cks!` at the URL that the setup prints.

[devdocs: https://devdocs.mautic.org/en/7.2/development-environment/how_to_install_with_ddev.html] [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html]

### 3.2 Manual dev install (without DDEV)
1. Clone the repo and run `composer install`. Composer and git are required, and Node/npm for assets.
2. Either complete the browser installer, or create `config/local.php` with DB values and run `bin/console mautic:install <url>`.
3. Create `.env.local` with `APP_ENV=dev`, `APP_DEBUG=1` and any DB variables. Tests use `.env.test` and `.env.test.local`.

[devdocs: https://devdocs.mautic.org/en/7.2/development-environment/setup.html] [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/environments.html]

### 3.3 Test a pull request (KB flow, adapted to 7.x)
1. Start an environment on the base branch, using DDEV or Codespaces. The KB uses Gitpod, which 7.x no longer ships; see Pitfalls in SKILL.md.
2. Load sample data with `ddev exec bin/console d:f:l`. This purges the database.
3. Reproduce the bug.
4. Check out the PR branch. In Codespaces, use "Checkout Pull Request by ID".
5. Retest, following the PR's "Steps to test".
6. Submit "Approve" or "Request changes". Each PR needs testing by two people.

[kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]

### 3.4 Staging server for a release (KB, written for 3.x)
1. Comment out the production Mautic cron jobs.
2. Snapshot the server.
3. Boot the clone.
4. Change the vhost `ServerName` and `site_url` in local.php, then run `cache:clear`.
5. Point mail at a catcher such as MailHog. SMS and push are not captured.
6. Apply the update, then run migrations and schema commands.
7. Check System Info > Error Log.

[kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html]

### 3.5 Build front-end assets
- In dev, run `composer sass:build` or `composer sass:watch`.
- For production assets, run `composer generate-assets` or `bin/console mautic:assets:generate`.

[devdocs: https://devdocs.mautic.org/en/7.2/development-environment/building_assets.html]

## 4. Stale or contradictory doc claims (checked against 7.x code)
| Doc claim | Current behaviour | Sources |
|---|---|---|
| Use `admin` / `mautic` (KB PR-testing article) | `admin` / `Maut1cR0cks!` everywhere in code; `mautic` is pre-5.1 | [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] [code: .ddev/local.config.php.dist @7.x] [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php:24-49 @7.x] |
| Test PRs in Gitpod | No Gitpod config in 7.x; PR template points to GitHub Codespaces | [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] [code: .github/PULL_REQUEST_TEMPLATE.md:59 @7.x] |
| Use `index_dev.php` for dev mode | No `index_dev.php`; dev mode is `APP_ENV=dev` in `.env.local` | [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html] [code: .ddev/.env.local.dist @7.x] |
| DDEV includes MailHog | Setup script still says MailHog; Codespaces docs say Mailpit; the KB digest notes DDEV now ships Mailpit | [code: .ddev/mautic-setup.sh:32 @7.x] [code: .devcontainer/CODESPACES.md @7.x] |
| UI uses Bootstrap 3.4.1 | 7.x ships `twbs/bootstrap` 5.3.8 | [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/building_assets.html] [code: app/composer.json:15-105 @7.x] |
| PHP 7.4 minimum, `platform.php` 7.4 | PHP 8.2.0 minimum; Composer platform 8.2.0 | [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#how-can-you-specify-a-php-version] [code: app/release_metadata.json:4 @7.x] [code: composer.json:195-198 @7.x] |
| Do not pre-set `db_driver` or `mailer_from_name`, because they mark Mautic installed | `db_driver` + `site_url` mark it installed; `mailer_from_name` plays no part, and DDEV's template sets both | [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] [code: app/AppKernel.php:272-283 @7.x] |
| Dev setup says `app/config/local.php` | `config/local.php`; the legacy path is used only when the new one is missing and the old one exists | [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/setup.html] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:134-137 @7.x] |
| `.env.test` admin password is `Maut1cR0cks!` (D06 digest of the environments page) | Committed `.env.test` says `mautic`, and nothing reads it | [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/environments.html] [code: .env.test:10-11 @7.x] |
| Staging KB uses `mautic:update:find/apply` and `app/config/local.php` | Pre-5 instructions; use the Composer update flow (mautic-upgrades-and-versions) | [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html] |
| Recommended Project pinned to `^5` | Still shown as `^5` in the docs; use the current major for 7.x | [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#using-the-recommended-project] |

## 5. Terminology
- Use "Contact" in prose, not "Lead". Code identifiers keep `Lead`. [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html]
- Write product names as DDEV, GitHub, Composer, Docker, Redis, Doctrine and Symfony. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html]
- KB articles follow Diataxis: tutorial, how-to or troubleshooting. [kb: https://kb.mautic.org/article/how-to-contribute-to-the-knowledge-base.html]

## 6. Gaps in the docs
- No page in these slices lists the DDEV PHP, database or Node versions. Code has them in `.ddev/config.yaml`. [code: .ddev/config.yaml:1-24 @7.x]
- No page in these slices describes the GrapesJS build (`gjs-build`) or its silent failure during `composer install`. [code: build/gjs_build.php:5-13 @7.x]
- No page in the D06 or D13 slices explains running cron or a Messenger worker inside DDEV, and DDEV defines neither. [code: .ddev/config.yaml:1-24 @7.x]
- No page in these slices says that re-running the DDEV setup reinstalls Mautic over existing data. [code: .ddev/mautic-setup.sh:11-18 @7.x]
