# Configuration and installer: version notes

## History (before 7.x)
- Mautic 2.x used `app/console`. Since 3.x the console is `bin/console`. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]
- Composer-based install has been available since 4.x, and Composer became the default install and update method in 5.x. Marketplace installs need the Composer setting (since 4.2). [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-composer] [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html] [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html#using-the-mautic-marketplace]
- The browser-based updater was deprecated in 4.2 and removed in 5.0; updates run from the CLI. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-in-the-browser]
- 5.0 moved local.php from `app/config/local.php` to `config/local.php`. The loader still falls back to the legacy file when the new one is absent. [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-is-available] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:134-137 @7.x]
- 5.x replaced Swiftmailer with Symfony Mailer. Mailer settings became the single `mailer_dsn`, which makes the old `mailer_host`/`mailer_spool_*` keys and install options obsolete. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#email-transport-settings] [code: app/bundles/EmailBundle/Config/config.php:137-224 @7.x]
- 5.x removed the legacy shortener; shorteners are now Plugins selected under System Settings > Shortener Service. [docs: https://docs.mautic.org/en/7.2/configuration/shortener.html]
- 5.1 started requiring a complex admin password at install, and the default DDEV password became `Maut1cR0cks!`. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev]
- The legacy RabbitMQ/Beanstalkd queue keys (`queue_protocol` etc.) are still documented, but Messenger DSN parameters replace them in 7.x. [docs: https://docs.mautic.org/en/7.2/queue/queue.html] [code: app/bundles/MessengerBundle/Config/config.php:7-13 @7.x]
- 3.0 moved configuration to env-var-backed parameters, so a UI save no longer rebuilds the container; the queue settings left the UI. [PR #8265]
- 3.0 renamed the `api_rate_limiter_cache` key `type` to `adapter`, which needed a manual local.php edit. [PR #8305]
- 4.0 stopped storing `db_server_version`; Doctrine detects the MySQL or MariaDB version and a migration removes the key. [PR #9739]
- 5.0 moved user config to `<project_root>/config/`; on a 4→5 upgrade the file moves after the migrations that edit it. [PR #11561] [PR #12796]
- 5.0 removed `%kernel.root_dir%`; local.php paths must use `%kernel.project_dir%`. [PR #11145]
- 5.0 removed the installer email step and the `--mailer_*` CLI options, and the installed check uses `db_driver` and `site_url` instead of `mailer_from_name`. [PR #12216]
- 5.0 introduced Messenger settings. Early 5.0 development used `messenger_dsn` and `messenger_type`; the release uses `messenger_dsn_email`, `messenger_dsn_hit`, `messenger_dsn_failed` and `messenger_retry_strategy_*`, defaulting to `sync://`. [PR #11598] [PR #12509]
- 5.0 added the read replica `db_host_ro`; it was ignored until 5.0.2. [PR #11792] [PR #13211]
- 5.0 set admin session cookies to `SameSite=Lax`. [PR #11511]
- 5.0.3 stores DSNs URL-encoded with `%` doubled and reads them through `urlencoded-dsn`. [PR #13255]
- 5.1.0 enables the GrapesJS builder again on a fresh install. [PR #13672]
- 5.2.2 made toggle-dependent config fields follow the live toggle state. [PR #14416]
- 6.x: no configuration or installer behaviour change was found in the 158 PRs reviewed; 6.0 only added a GitHub Codespaces dev container. [PR #14610]

## 7.x (authoritative: 7.x snapshot, release 7.2.1 plus unreleased merged PRs)
- 7.0 removed the web-push notification settings from the UI; the `notification_*` parameters remain. [code: UPGRADE-7.0.md:30 @7.x] [code: app/bundles/NotificationBundle/Config/config.php:113-124 @7.x]
- Platform requirements are PHP 8.2.0–8.5.99 (enforced per request by `VersionCheckMiddleware`) and MySQL ≥ 8.4.0 or MariaDB ≥ 10.11.0 (enforced at install). [code: app/release_metadata.json:4-7 @7.x] [code: app/middlewares/VersionCheckMiddleware.php:46-59 @7.x] [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:177-201 @7.x]
- `ConfigBundle/Config/services.php` still carries service aliases marked "@deprecated Remove all aliases in Mautic 6": `mautic.config.model.sysinfo`, `mautic.config.mapper`, `mautic.config.config_change_logger`, `mautic.config.form.escape_transformer` and `mautic.config.form.restriction_helper`. [code: app/bundles/ConfigBundle/Config/services.php:26-31 @7.x]
- The 7.x branch after 7.2.1 (unreleased; [PR #16870]) has the setting `validate_unsubscribe_emails` (default true), which the 8.0 docs describe as "Require email validation for unsubscribe". [code: app/bundles/EmailBundle/Config/config.php:137-224 @7.x] [docs: https://docs.mautic.org/en/8.0/configuration/settings.html#unsubscribe-settings]
- 7.0 removed the API rate limiter (`noxlogic/ratelimit-bundle`), so the `api_rate_limiter_*` parameters no longer exist. [code: UPGRADE-7.0.md:52 @7.x]
- 7.0 configures the mailer with the long `transports` form (`main` is Mautic's DSN), so plugins can add transports. [PR #15422]
- 7.0.1 made the minimum DB version check inclusive, so MySQL 8.4.0 installs and updates. [PR #15797]
- 7.1: no configuration or installer change was found in the 158 PRs reviewed. [unverified]
- 7.2.0 makes install fail if migration metadata sync or version marking fails, and the CLI installer prints plain text. [PR #17127] [PR #17100]
- 7.2.1 lets the CLI installer run on a Composer project that has never served a web request. [PR #17394]
- Unreleased 7.x (after 7.2.1): each Configuration section is its own page and `last_shown_tab` is removed. [PR #17776] [code: app/bundles/ConfigBundle/Config/config.php:8-15 @7.x]

Full history with reasons is in `pr-history.md`.

## 8.x delta (development branch; not released)
- `ConfigEvents` is deleted. Subscribe to `ConfigBuilderEvent::class` (now `final`), `ConfigPreSaveEvent::class` and `ConfigPostSaveEvent::class`. The old names were `mautic.config_on_generate`, `mautic.config_pre_save` and `mautic.config_post_save`. [PR #17625] [PR #17654]
- The `mautic.config.model.sysinfo` alias is removed, and `SysinfoModel::getLogTail(int)` is typed. [PR #17625]
- For code that must run on both 7.x and 8.x, register both keys and guard the 7.x constant:
  ```php
  $events = [ConfigBuilderEvent::class => ['onConfigGenerate', 0]];
  if (defined('Mautic\ConfigBundle\ConfigEvents::CONFIG_ON_GENERATE')) {
      $events[\Mautic\ConfigBundle\ConfigEvents::CONFIG_ON_GENERATE] = ['onConfigGenerate', 0];
  }
  ```
  On 7.x the pre/post-save handlers receive `ConfigEvent`, so type-hint loosely or guard with `class_exists()`. [PR #17625]
- `config.php` no longer reads the `services` group (including `models` and `menus`); plugins keep `parameters` and `routes` in `config.php`. Core bundle routes move to `#[Route]` attributes. [PR #17470] [PR #17169]
- `cache_adapter` must be a class name, because the `mautic.cache.adapter.*` service ids are removed. [code: UPGRADE-8.0.md:177 @8.x]
- The Redis Sentinel session handler is removed, so configs that reference it break. [PR #17050]
- SAML moves from `javer/sp-bundle` to `lightsaml2/sp-bundle`; the SAML settings are intended to be unchanged. [PR #17370]
- Platform: PHP minimum 8.4 [PR #16993], Symfony 8.1 [PR #17392], Doctrine ORM 3.7 / DBAL 4.4 [PR #17361]. The MySQL 8.4.0 and MariaDB 10.11.0 minimums are unchanged. [code: app/release_metadata.json @8.x]
- `app/release_metadata.json@8.x` still says version 7.2.0, so treat 8.x as unreleased. [code: app/release_metadata.json @8.x]
- 7.2.1 has not been merged forward. 7.x-only settings, such as the unreleased (post-7.2.1) unsubscribe email validation, are absent from 8.x code until the next merge. The last forward merge was 7.2.0 → 8.x. [PR #17253]
- The 8.0 user docs for configuration differ from 7.2 only in documenting that unreleased 7.x (post-7.2.1) unsubscribe setting. [docs: https://docs.mautic.org/en/8.0/configuration/settings.html#unsubscribe-settings]

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
