---
name: mautic-configuration
description: "How Mautic configuration works, with the complete parameter reference: bundle default parameters, config/local.php, parameters_local.php, MAUTIC_* environment variables and .env files, precedence and caching, CoreParametersHelper, the admin Configuration UI (Settings > Configuration) and how bundles add tabs, restricted parameters, System Info, and the web and CLI installer (/installer, mautic:install). Use whenever a task mentions settings, configuration, config parameters, local.php, env vars, site_url, secret_key, db_* settings, trusted_hosts or trusted_proxies, CORS, a setting not taking effect or config not saved, ConfigEvents (CONFIG_ON_GENERATE, CONFIG_PRE_SAVE), ConfigBuilderEvent, ParameterLoader, installing Mautic, or touches app/bundles/ConfigBundle/, app/bundles/InstallBundle/, app/config/ or any bundle's Config/config.php 'parameters' array."
---
# Mautic configuration, parameters and installer

## Scope
This skill covers how Mautic turns bundle defaults, `config/local.php` and the environment into runtime settings; the admin
Configuration UI that rewrites `config/local.php`; the System Info page; and the web and CLI installer. It also holds the
complete parameter reference (`references/parameters.md`). The meaning of individual feature settings is owned by the feature
skills: mailer and monitored inbox (mautic-emails), SAML (mautic-users-and-permissions), API settings (mautic-rest-api),
tracking settings (mautic-pages-and-tracking), queues and cron (mautic-cron-and-queues), local environments (mautic-dev-environment).

Terms: a **parameter** is one key in a bundle's `Config/config.php` `parameters` array. A **tab** is one section of the
Configuration UI, identified by its `formAlias`. **local.php** is the PHP file holding `$parameters = array(...)` that the UI writes.

## Expected behaviour (essentials)
Loading and precedence
- Defaults are the merge of the `parameters` array of every `app/bundles/*/Config/config.php` and `plugins/*/Config/config.php`; a duplicate key is last-wins in Finder order. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:169-183 @7.x]
- Local layers override defaults in this order: `config/local.php` < `config/parameters_local.php` < `MAUTIC_CONFIG_PARAMETERS` (a JSON object in the environment). [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:186-215 @7.x]
- `db_driver` is always forced to `pdo_mysql`, whatever any layer says. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:217-219 @7.x]
- Every merged key is exported as environment variable `MAUTIC_` + upper-cased key; arrays are JSON-encoded; `null` becomes `''`. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:13-28 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:67-110 @7.x]
- A `MAUTIC_<KEY>` variable already in the real environment (OS or `.env*` files) is never overwritten, so it beats every file-based layer. Effective order, highest first: real `MAUTIC_<KEY>` env var > `MAUTIC_CONFIG_PARAMETERS` > `parameters_local.php` > `local.php` > bundle default. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:91-105 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/Loader/ParameterLoaderTest.php:156-170 @7.x]
- A string value written as `getenv(NAME)` is replaced by that environment variable's value. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:14-16 @7.x]
- Container parameter `mautic.<key>` is `%env(<processor>resolve:MAUTIC_<KEY>)%`, with the processor chosen from the default's PHP type (bool, intNullable, json, float, nullable). [code: app/config/parameters.php:13-49 @7.x]
- `CoreParametersHelper::get('key')` (or `'mautic.key'`) prefers the container parameter and falls back to the merged bag; keys that exist only in local.php are readable but have no env override and no type cast. [code: app/bundles/CoreBundle/Helper/CoreParametersHelper.php:30-46 @7.x]
- Some env vars are derived and overwrite the generic ones: OAuth2 lifetimes are exposed in seconds (minutes×60, days×86400), plus site_url router context, session name, SAML, ElFinder, migrations table and Twig cache vars. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:73-82 @7.x] [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:13-17 @7.x]
- The middlewares (CORS, HSTS, trusted proxies/hosts, dev IP restriction) read local.php and parameters_local.php directly, so they ignore env vars and `MAUTIC_CONFIG_PARAMETERS`. [code: app/middlewares/ConfigAwareTrait.php:17-45 @7.x]

Installed state and site_url
- Mautic counts as installed when the local parameters contain non-empty `db_driver` and `site_url`; because `db_driver` is forced, `site_url` is the real switch. [code: app/AppKernel.php:272-283 @7.x] [code: app/bundles/InstallBundle/Install/InstallService.php:125-139 @7.x]
- While not installed, every request is redirected to `/installer`, and any URI containing `installer` runs in installer mode. [code: app/AppKernel.php:60-84 @7.x]
- `site_url` drives the router context for web and CLI, the https forcing of routes, the secure session cookie, the SAML entity id fallback and the ElFinder URL. [code: app/bundles/CoreBundle/Loader/EnvVars/SiteUrlEnvVars.php:11-56 @7.x] [code: app/bundles/CoreBundle/Loader/RouteLoader.php:34-43 @7.x] [code: app/config/config.php:35-44 @7.x]
- The session cookie name is `md5(md5(<local config path>) . secret_key)`, so moving the install or changing `secret_key` logs everyone out. [code: app/bundles/CoreBundle/Loader/EnvVars/SessionEnvVars.php:12-17 @7.x]

Configuration UI
- Only admin Users can open, save, download or remove configuration; there is no granular permission. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:41-43 @7.x]
- Each tab is its own page at `/s/config/edit/<formAlias>`; `/s/config/edit` redirects to `coreconfig`; an unknown tab returns 404. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:55-71 @7.x]
- Saving a tab merges only that tab's values into local.php; other tabs' values are kept. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:131-140 @7.x] [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:138 @7.x]
- Saving needs a writable local.php; otherwise the form shows `mautic.config.notwritable` and nothing is written. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:86-92 @7.x]
- Restricted keys (`db_*`, `secret_key`, and `transifex_*` in prod) are removed from the form and from form data; display mode `mask` shows them disabled instead. [code: app/config/security.php:182-200 @7.x] [code: app/bundles/ConfigBundle/Form/Helper/RestrictionHelper.php:60-82 @7.x]
- Every value is escaped on save (`%` → `%%`) except allowed container placeholders (`%kernel.project_dir%`, `%kernel.logs_dir%`). [code: app/bundles/ConfigBundle/Form/Type/EscapeTransformer.php:77-92 @7.x]
- Empty password and file fields keep the stored value (`unsetIfEmpty`, file fields, the `🔒` DSN password mask). [code: app/bundles/ConfigBundle/Controller/ConfigController.php:127-137 @7.x] [code: app/bundles/ConfigBundle/Form/DataTransformer/DsnTransformer.php:74-77 @7.x]
- After a write, Mautic dispatches `CONFIG_POST_SAVE`, then `CacheHelper::refreshConfig()` clears the session menu cache, invalidates opcache for local.php and clears APCu; the Symfony container is not rebuilt. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:149-154 @7.x] [code: app/bundles/CoreBundle/Helper/CacheHelper.php:37-42 @7.x]
- Settings consumed at container compile time need `bin/console cache:clear` after a manual edit: `cookie_secure` from the site_url scheme, `db_host_ro`, `cache_path`/`log_path`, and https route forcing. [code: app/config/config.php:35-44 @7.x] [code: app/config/config.php:172-185 @7.x] [code: app/AppKernel.php:316-334 @7.x]
- Each save that changes values writes one audit-log row (`config/config/0/update`) listing changed keys, never `transifex_password` or `mailer_is_owner`. [code: app/bundles/ConfigBundle/Service/ConfigChangeLogger.php:19-22 @7.x] [code: app/bundles/ConfigBundle/Service/ConfigChangeLogger.php:48-82 @7.x]
- Turning on `anonymize_ip` anonymises all stored IP addresses synchronously unless `anonymize_ip_address_in_background` is true. [code: app/bundles/ConfigBundle/EventListener/ConfigSubscriber.php:39-49 @7.x]
- Saving a `locale` without an installed language pack downloads it; if the download fails, the value falls back to `en_US` with a form error. [code: app/bundles/CoreBundle/EventListener/ConfigSubscriber.php:49-76 @7.x]
- local.php omits keys whose value is `''`. [code: app/bundles/CoreBundle/Configurator/Configurator.php:193-245 @7.x]

Installer
- Hard requirements block install: writable config, cache and log paths; required PHP functions and extensions; PDO MySQL; an OpenSSL cipher. Recommendations only warn: `memory_limit` ≥ 512M, intl, zip, imap, https site_url, and others. [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:73-224 @7.x]
- The database must be MySQL ≥ 8.4.0 or MariaDB ≥ 10.11.0; PHP must be 8.2.0 to 8.5.99. [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:177-201 @7.x] [code: app/release_metadata.json:4-7 @7.x]
- Install backs up existing tables to `bak_*` by default (`db_backup_tables=true`), or drops them, before creating the schema. [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:119-175 @7.x]
- Install loads the `group_install` fixtures (admin Role, core Contact/Company fields, sample Reports), creates the admin User, writes `secret_key` and `site_url`, and marks every migration as executed. [code: app/bundles/InstallBundle/Install/InstallService.php:393-411 @7.x] [code: app/bundles/InstallBundle/Install/InstallService.php:514-547 @7.x]
- `mautic:install` exits 0 at once when already installed. An existing local.php `site_url` beats the `site_url` argument. A failed requirements step also exits 0; later steps return -1, -2 or -3. [code: app/bundles/InstallBundle/Command/InstallCommand.php:155-159 @7.x] [code: app/bundles/InstallBundle/Command/InstallCommand.php:222-227 @7.x] [code: app/bundles/InstallBundle/Command/InstallCommand.php:243 @7.x]

## Where it lives
| Concern | Path(s) |
|---|---|
| Parameter loading, env export | `app/bundles/CoreBundle/Loader/ParameterLoader.php`, `app/bundles/CoreBundle/Loader/EnvVars/*.php` |
| Container wiring of params | `app/config/parameters.php`, env processors in `app/bundles/CoreBundle/DependencyInjection/EnvProcessor/` |
| Runtime accessor | `app/bundles/CoreBundle/Helper/CoreParametersHelper.php` |
| local.php read/write | `app/bundles/CoreBundle/Configurator/Configurator.php` (service `mautic.configurator`) |
| Cache refresh | `app/bundles/CoreBundle/Helper/CacheHelper.php` |
| Bootstrap, installed check, `.env` | `app/AppKernel.php`, `app/config/bootstrap.php`, `index.php`, `.env`, `.env.test` |
| Middlewares (CORS, HSTS, trust) | `app/middlewares/*.php` |
| Config UI | `app/bundles/ConfigBundle/Controller/ConfigController.php`, `Form/Type/ConfigType.php`, `Mapper/ConfigMapper.php`, `Form/Helper/RestrictionHelper.php` |
| Events | `app/bundles/ConfigBundle/ConfigEvents.php`, `Event/ConfigBuilderEvent.php`, `Event/ConfigEvent.php` |
| Tab contributors | `app/bundles/*/EventListener/ConfigSubscriber.php` (list in `references/code-map.md`) |
| Restricted fields | `app/config/security.php:182-200` |
| System Info | `app/bundles/ConfigBundle/Controller/SysinfoController.php`, `Model/SysinfoModel.php` |
| Installer | `app/bundles/InstallBundle/` (`Install/InstallService.php`, `Command/InstallCommand.php`, `Configurator/Step/*`, `Helper/SchemaHelper.php`, `InstallFixtures/ORM/*`) |
| Routes | `/s/config/edit/{tab}`, `/s/config/{download|remove}/{key}`, `/s/sysinfo`, `/installer`, `/installer/step/{index}`, `/installer/final` |
| Commands | `mautic:install`, `mautic:install:data`, `mautic:cache:clear`; Symfony `cache:clear` |
| Parameters | `references/parameters.md` |
| Tests | `app/bundles/ConfigBundle/Tests/`, `app/bundles/InstallBundle/Tests/`, `app/bundles/CoreBundle/Tests/Unit/Loader/` |

## How to change or extend it
- Add a parameter: declare its default in your bundle's `Config/config.php` `parameters`. The default's PHP type fixes the env processor, so use `false` (not `0`) for booleans and `[]` for lists. Only declared keys get a `MAUTIC_<KEY>` override and a `mautic.<key>` container parameter. [code: app/config/parameters.php:21-49 @7.x]
- Add a Configuration tab: subscribe to `ConfigEvents::CONFIG_ON_GENERATE` and call `$event->addForm([...'formAlias','formType','formTheme','parameters' => $event->getParametersFromConfig('MyBundle')])`. Add the translation `mautic.config.tab.<alias>`. A tab with empty `parameters` is not shown. [code: app/bundles/ConfigBundle/Event/ConfigBuilderEvent.php:38-111 @7.x] [code: app/bundles/ConfigBundle/Controller/ConfigController.php:55 @7.x]
- Validate or transform before save in `CONFIG_PRE_SAVE` (`getConfig`, `setConfig`, `setError`, `unsetIfEmpty`). React after save in `CONFIG_POST_SAVE`. [code: app/bundles/ConfigBundle/Event/ConfigEvent.php:88-159 @7.x]
- Register uploaded-file settings with `addFileFields()`. They are stored base64-encoded and are downloadable and removable through `/s/config/{download|remove}/<key>`. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:204-265 @7.x]
- Use `DsnType` for DSN settings. It masks the password and supports a test button wired to an AJAX action. [code: app/bundles/ConfigBundle/Form/Type/DsnType.php:120-175 @7.x]
- To restrict more fields system-wide, override `mautic.security.restrictedConfigFields` and `.displayMode` in `config/security_local.php`. [code: app/config/security.php:182-200 @7.x]
- Add an installer step as a `mautic.configurator.step` tagged service. Add install fixtures with the `group_install` group. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ConfiguratorPass.php:21-24 @7.x] [code: app/bundles/InstallBundle/InstallFixtures/ORM/RoleData.php:19-22 @7.x]
- For code that must run on 7.x and 8.x, subscribe by event class and guard the `ConfigEvents` constants with `defined()`, because 8.x deletes `ConfigEvents`. [PR #17625] [PR #17654]
- Keep backward compatibility. Never rename a parameter key: existing local.php files and `MAUTIC_<KEY>` deployments depend on it. Changing a default's PHP type changes the env processor. [code: app/config/parameters.php:21-49 @7.x]
- A new setting usually needs four things together: the default in `config.php`, the form field in the bundle's ConfigType, the label and tooltip translations, and the user docs settings page. [code: app/bundles/ConfigBundle/Event/ConfigBuilderEvent.php:86-99 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html]

## How to test it
- Use `MauticMysqlTestCase` for functional tests. Set `$this->configParams['key'] = value` before `parent::setUp()`; the values reach the kernel as `MAUTIC_CONFIG_PARAMETERS`. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:111-114 @7.x]
- Tests that write local.php must back it up and restore it. [code: app/bundles/CoreBundle/Tests/Functional/EventListener/ConfigSubscriberTest.php:26-50 @7.x]
- Representative tests:
  - `app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php`: escaping, tab redirect, per-tab saving, restricted fields, locale.
  - `app/bundles/CoreBundle/Tests/Unit/Loader/ParameterLoaderTest.php` and `Tests/Unit/Loader/EnvVars/*Test.php`: precedence and derived env vars.
  - `app/bundles/ConfigBundle/Tests/Mapper/ConfigMapperTest.php` and `Tests/Form/Helper/RestrictionHelperTest.php`.
  - `app/bundles/InstallBundle/Tests/Functional/InstallWorkflowTest.php`: drives `/installer` end to end.
  - `app/bundles/InstallBundle/Tests/Command/InstallCommandTest.php`.
- A good regression test submits one tab, using fields named `config[<alias>][<field>]` and `config[buttons][apply]`. It then re-reads local.php or `CoreParametersHelper` and asserts that the changed key, the untouched keys and the restricted keys are all as expected. Details are in `references/test-patterns.md`.

## Version notes
- 5.x moved local.php from `app/config/local.php` to `config/local.php`; 7.x still falls back to the legacy path when only it exists. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:134-137 @7.x] [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-is-available]
- 5.x replaced Swiftmailer with Symfony Mailer, so the mailer is configured by one `mailer_dsn` setting. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#email-transport-settings]
- The installer has required a complex admin password since 5.1. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
- 7.0 removed the web-push notification settings from the UI. [code: UPGRADE-7.0.md:30 @7.x]
- 7.x requires PHP 8.2 to 8.5 and MySQL 8.4 or MariaDB 10.11. [code: app/release_metadata.json:4-7 @7.x]
- 8.x deletes `ConfigEvents` and dispatches by event class: `ConfigBuilderEvent` (final), `ConfigPreSaveEvent` and `ConfigPostSaveEvent`. [PR #17625] [PR #17654]
- 8.x removes the `mautic.config.model.sysinfo` service alias and gives `SysinfoModel::getLogTail(int)` a typed parameter. [PR #17625]
- 8.x requires PHP 8.4 [PR #16993] and Symfony 8.1 [PR #17392].
- 8.x expects `cache_adapter` to hold a class name, not a `mautic.cache.adapter.*` service id. [code: UPGRADE-8.0.md:177 @8.x]
- Full detail is in `references/version-notes.md`.

## Pitfalls
- A real `MAUTIC_<KEY>` environment variable silently beats anything saved in the UI. The UI then shows the local.php value, not the effective one. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:91-105 @7.x] [code: app/bundles/ConfigBundle/Controller/ConfigController.php:270-294 @7.x]
- CORS, HSTS and trusted hosts and proxies ignore env vars, because the middlewares read the PHP files directly. [code: app/middlewares/ConfigAwareTrait.php:17-45 @7.x]
- `mautic:cache:clear` clears only the Mautic application cache adapter. It is not the Symfony `cache:clear` that compile-time settings need. [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:18-21 @7.x]
- `mautic:install` returns exit code 0 when the requirements step fails, so scripts cannot tell that failure from success. [code: app/bundles/InstallBundle/Command/InstallCommand.php:243 @7.x]
- Wrong `trusted_hosts` lock you out of the UI. Fix them by editing local.php. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#cors-settings] [code: app/middlewares/TrustMiddleware.php:38-40 @7.x]
- `anonymize_ip`, `sysinfo_disabled` and the theme tab's `accent` are not declared in any `config.php`, so they have no env override and no typed default. [code: app/bundles/PageBundle/EventListener/ConfigSubscriber.php:42-64 @7.x]
- `marketplace_website_url` is declared twice with different defaults, in CampaignBundle and MarketplaceBundle; the winner depends on Finder order. [code: app/bundles/CampaignBundle/Config/config.php:178 @7.x] [code: app/bundles/MarketplaceBundle/Config/config.php:42 @7.x]
- A literal string containing `getenv(...)` cannot be stored as a value, because it is always treated as an env reference. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:14-16 @7.x]
- Docs and code disagree on the "Default item limit per page". The docs say `10`; the code default is `30`. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#system-defaults] [code: app/bundles/CoreBundle/Config/config.php:285 @7.x]
- Docs and code disagree on CORS "Restrict Domains". The docs say the default is No; the code default is `true`, so CORS is restricted out of the box. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#cors-settings] [code: app/bundles/CoreBundle/Config/config.php:702 @7.x]
- The docs warn not to pre-set `db_driver` and `mailer_from_name` because they mark Mautic as installed. In code only `db_driver` and `site_url` count, and `db_driver` is always forced. A pre-set `site_url` is what makes Mautic look installed. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] [code: app/AppKernel.php:272-283 @7.x]
- The docs list `--mailer_*` options for `mautic:install`, but the 7.2.1 command defines only `--db_*`, `--admin_*` and `--force`. [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#mautic-commands] [code: app/bundles/InstallBundle/Command/InstallCommand.php:58-147 @7.x]
- Open question: the docs say Mautic wraps trusted-host regexes in `/` delimiters. The code analysis confirms only domain-or-regexp validation. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#cors-settings] [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:190-250 @7.x] [unverified]

## Related skills
- mautic-dev-environment: DDEV, `.env.local`, running a local instance.
- mautic-cron-and-queues: Messenger DSNs, cron jobs and the `*_in_background` flags in operation.
- mautic-emails: mailer DSN, mail-send, monitored inbox and unsubscribe settings.
- mautic-users-and-permissions: SAML settings, admin role, User locale and timezone.
- mautic-rest-api: API enable, basic auth and OAuth2 lifetimes.
- mautic-pages-and-tracking: tracking, CORS for tracking, IP anonymisation, cookies.
- mautic-architecture: kernel, bundles, DI and the event system in general.
- mautic-testing: `MauticMysqlTestCase`, `configParams` and test env details.
- mautic-upgrades-and-versions: updates, migrations and the 8.x upgrade.
- mautic-troubleshooting: "setting not applied", permission and cache problems.

## Reference files
- `references/behaviour.md`: the full numbered behaviour specification (bootstrap, loading, UI, installer, caching). Open it before changing or testing any config path.
- `references/parameters.md`: every parameter with default, type, UI tab and doc label, meaning, owning bundle and citation.
- `references/code-map.md`: classes, events, tab contributors, routes, commands, env vars and override files.
- `references/docs-digest.md`: what docs.mautic.org and devdocs say about settings, install and environments, with URLs.
- `references/test-patterns.md`: base classes, fixtures, local.php backup pattern and test skeletons.
- `references/version-notes.md`: 5.x/6.x history, 7.x specifics and the 8.x delta.
- `references/pr-history.md`: not yet generated; PR-derived history is added in a later pass.
