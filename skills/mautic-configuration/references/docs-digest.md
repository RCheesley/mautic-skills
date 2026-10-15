# Configuration, settings and installation: what the official docs say

Sources are docs.mautic.org 7.2 and devdocs.mautic.org 7.2 (8.0 where noted). The per-setting doc labels are merged into
`parameters.md`. This file holds the general statements, the procedures and the terminology. Where code disagrees, see the last section.

## Settings page (Settings > Configuration)
- Site URL is "where Mautic is physically installed". Cron needs it to build absolute links in Emails. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#general-settings]
- The root URL shows the login page unless a root Landing Page is set. Once one is set, Users sign in at `/s/login`. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#general-settings]
- System defaults: page limit `10` (the code says 30), timezone `UTC`, language English (US), cached data timeout 10 min, date range `1 Month`, American date formats. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#system-defaults]
- CORS: setting Restrict Domains to Yes is "strongly recommended". Valid Domains holds one exact URL per line; the scheme matters and there is no trailing slash. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#cors-settings]
- Trusted hosts are comma-separated and may be regexes, which Mautic wraps in `/` delimiters; empty means all hosts. Wrong values can lock you out and then need a manual config-file edit. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#cors-settings]
- Trusted proxies are mandatory behind an SSL-terminating proxy, for example `127.0.0.1, 10.0.0.0/8, fc00::/7`. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#cors-settings]
- Minimum stability defaults to stable. Never enable early access in production. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#update-settings]
- "Update Mautic through Composer" is required for Marketplace installs. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#update-settings] [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html#using-the-mautic-marketplace]
- DSN values pasted into `config/local.php` must be URL-encoded; the form encodes them automatically. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#smtp-transport]
- Queueing is off by default (`sync://`). Workers run `messenger:consume email`. Retry defaults are 3 / 1000 ms / ×2 / no max. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#retry-strategy]
- Some settings exist only in local.php: `campaign_event_cache_ttl` (600), `campaign_contact_count_cache_ttl` (43200), `support_mautic_enabled`, `smime_signing_enabled` and `smime_certificates_path`. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#advanced-campaign-performance-settings] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#support-mautic-menu-item] [docs: https://docs.mautic.org/en/7.2/configuration/smime_email_signing.html#configuration-parameters]
- Saving Configuration with a new language downloads the language pack. To force a refresh, delete `translations/<locale>` and re-save. [docs: https://docs.mautic.org/en/7.2/translations/translations.html#how-to-update-a-language]
- The MaxMind license key goes in "IP lookup service authentication" as `AccountID:Licensekey`. [docs: https://docs.mautic.org/en/7.2/configuration/maxmind_license.html]
- SAML is turned on by uploading the IdP metadata and turned off with Remove beside the file. If the Default Role is empty, SSO creates no Users. [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#turning-on-saml] [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#turning-off-saml]
- 8.0 docs add "Require email validation for unsubscribe" (default Yes). [docs: https://docs.mautic.org/en/8.0/configuration/settings.html#unsubscribe-settings]

## Installation
- Prerequisites: the requirements at mautic.org/download/requirements, a directory writable by the web server, enough disk, and PHP `max_execution_time` ≥ 240 s. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#preparing-for-installation]
- Web installer: red errors must be fixed; orange warnings are recommendations; SSL is recommended. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#conducting-environment-checks]
- "Backup existing tables?" is on by default and should be turned off for new installs. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#integrating-the-database]
- A complex admin password has been required since 5.1. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
- CLI install: `php bin/console mautic:install https://m.example.com [options]`. The defaults are `--db_driver=pdo_mysql`, `--db_backup_tables=true` and `--db_backup_prefix=bak_`. You may pre-create local.php with DB and admin values. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
- The CLI installer warns when `memory_limit` < 512M. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-a-local-php-file]
- Composer install uses `composer create-project mautic/recommended-project:^5 some-dir --no-interaction`. The web root must point to `docroot`, and `.env` drives the env vars. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#using-the-recommended-project]
- DDEV: default login `admin` / `Maut1cR0cks!`. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev]
- Recommended permissions: files 644, dirs 755, and group-writable `var/cache`, `var/logs`, `app/config`, `media/files`, `media/images` and `translations`. [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html#reset-the-file-and-folder-permissions]
- After a manual fix, recovery keeps `config/local.php` (pre-5.0: `app/config/local.php`). [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-is-available]

## Environment files (devdocs)
- Precedence: `.env` < `.env.local` < `.env.$APP_ENV` < `.env.$APP_ENV.local`, and real env vars win. Do not put secrets in committed files. `composer dump-env prod` compiles them. [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/environments.html]
- `.env` defaults to `APP_ENV=prod`, `APP_DEBUG=0`. For local dev, create `.env.local` with `APP_ENV=dev`, `APP_DEBUG=1` and the DB vars. [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/environments.html#development-environment]

## CLI
- Run the CLI from the Mautic root; the default env is `prod`. `mautic:cache:clear` erases the 10-minute Mautic cache (Segment counts, dashboard widgets). [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html]
- `doctrine:fixtures:load` installs sample data and overwrites existing data. [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#doctrine-commands]

## Procedures
1. **Web install:**
   1. Unzip the package.
   2. Open the site URL.
   3. Fix the red checks.
   4. Enter the DB settings, with backup off for a fresh install.
   5. Create the admin.
   6. Configure Email.

   [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#using-the-web-based-installer]
2. **CLI install:**
   1. Optionally write local.php with `db_*`/`admin_*` values, but not `db_driver`, `mailer_from_name` or `site_url`. See the discrepancies section.
   2. Run `mautic:install <url>`.

   [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
3. **Manual dev install:**
   1. Clone the repository.
   2. Run `composer install`.
   3. Use either the browser installer or local.php plus `mautic:install`.

   [devdocs: https://devdocs.mautic.org/en/7.2/development-environment/setup.html]
4. **Hide Support Mautic:** add `'support_mautic_enabled' => false,` to `config/local.php`. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#support-mautic-menu-item]
5. **Raise PHP limits:**
   1. Find php.ini via System Info > PHP Info or `php -i | grep .ini`.
   2. Edit the value.
   3. Restart the web server.

   [docs: https://docs.mautic.org/en/7.2/troubleshooting/working_with_resource_limits.html]
6. **Override a translation:**
   1. Create `translations/overrides/<locale>/messages.ini` containing the overridden line.
   2. Run `bin/console cache:clear`.

   [docs: https://docs.mautic.org/en/7.2/translations/translations.html#translation-overrides]

## Terminology
- "Configuration" (Settings > Configuration) is the admin settings screen. "System Info" is the diagnostics page. "Site URL" is the base URL. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html]
- The docs use capitalised entity nouns (Contact, Segment, Email, Landing Page, User, Role, Plugin, Theme) and "turn on/turn off". [docs: https://docs.mautic.org/en/7.2/configuration/settings.html]

## Where the docs disagree with 7.x code
| Doc claim | Code (7.2.1) |
|---|---|
| Default item limit per page `10` [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#system-defaults] | `30` [code: app/bundles/CoreBundle/Config/config.php:285 @7.x] |
| CORS Restrict Domains default No [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#cors-settings] | `true` [code: app/bundles/CoreBundle/Config/config.php:702 @7.x] |
| `db_driver` + `mailer_from_name` mark Mautic as installed [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] | `db_driver` + `site_url` [code: app/AppKernel.php:272-283 @7.x] |
| `mautic:install --mailer_*` options [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#mautic-commands] | none exist [code: app/bundles/InstallBundle/Command/InstallCommand.php:58-147 @7.x] |
| PHP 7.4 minimum [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#how-can-you-specify-a-php-version] | 8.2.0 – 8.5.99 [code: app/release_metadata.json:4-5 @7.x] |
| `app/config/local.php` (S/MIME, switching, dev setup pages) [docs: https://docs.mautic.org/en/7.2/configuration/smime_email_signing.html#configuration] | `config/local.php`, with legacy fallback [code: app/config/paths.php:11 @7.x] |
| Legacy `queue_protocol`/RabbitMQ/Beanstalkd keys [docs: https://docs.mautic.org/en/7.2/queue/queue.html] | not declared; Messenger DSNs instead [code: app/bundles/MessengerBundle/Config/config.php:7-13 @7.x] |
| "Complex password" requirement [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] | CLI: ≥ 6 chars; web form: `NotWeak` [code: app/bundles/InstallBundle/Install/InstallService.php:416-509 @7.x] |
