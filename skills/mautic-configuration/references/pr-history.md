# Configuration and installer: pull-request history

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
3. Regression catalogue
4. Feature timeline
5. Removed, deprecated, replaced
6. Maintainer norms for this area
7. Open questions
8. Coverage

## 1. How to read this file
Source: merged pull requests on mautic/mautic for configuration and the installer, harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; "unreleased 7.x" means merged on 7.x after 7.2.1 (milestone 7.3.0-rc).
Current behaviour is specified in `behaviour.md`, which is code-verified and wins on any conflict; this file explains why and when.

## 2. Decisions that shaped current behaviour

### Installed detection and bootstrap
- Mautic decides it is installed from parameters in the local config, not from a database query, so a database outage shows a connection error instead of sending a live site to the installer. Originally [PR #161] (v1.0). The marker keys were `db_driver` and `mailer_from_name` [PR #7395] (v3.1); they became `db_driver` and `site_url` [PR #12216] (v5.0), because the installer stopped writing `mailer_from_name`. `secret_key` was offered as an alternative marker and not adopted [PR #12216]. On 7.x both `AppKernel` and `InstallService` check non-empty `db_driver` and `site_url`. [code: app/AppKernel.php:272-283 @7.x] [code: app/bundles/InstallBundle/Install/InstallService.php:125-139 @7.x]
- Because `db_driver` is now always forced to `pdo_mysql`, `site_url` is the real switch; older advice to leave `db_driver` out of a pre-seeded local.php is historical. [PR #7395] [PR #12216] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:217-219 @7.x]
- The PHP version gate runs before the application boots, so an unsupported PHP version is rejected without building the container. It started in `index.php` [PR #788] (v1.2) and moved to `app/middlewares/VersionCheckMiddleware.php` [PR #8167] (v3.0).
- User configuration lives outside the application code, in `<project_root>/config/` (`local.php`, `parameters_local.php`, `paths_local.php` and the other `*_local` files), so Composer updates do not wipe it. [PR #11561] (v5.0). A migration moves the old `app/config/*local.php` files instead of silently ignoring them; a `local_config/` folder name was proposed and rejected in review. [PR #11561]
- On a 4→5 upgrade the config file moves last, after the migrations that still edit it. Release packages must contain `config/.gitkeep` and `composer.json`, which is used to find the project root. [PR #12796] (v5.0)
- `AppKernel::getProjectDir()` returns the real project root, which on Composer installs differs from the application directory. [PR #11561] (v5.0). `%kernel.root_dir%` is gone; local.php values must use `%kernel.project_dir%`. Re-implementing the removed Symfony method was rejected. [PR #11145] (v5.0)
- `paths.php` resolves `$projectRoot` itself when the including script has not set it. [PR #13193] (v5.0.2) [code: app/config/paths.php:25 @7.x]

### Installer requirements and recommendations
- Requirements block install; recommendations only warn. The app must be able to run without anything that is only a recommendation. [PR #872] (v1.2.1) [PR #366] (v1.1)
- HTTPS is a recommendation, not a requirement, because a hard requirement would break local and VPN-only installs. [PR #6862] (v2.15)
- cURL is a hard requirement, because without it Mautic installed and then failed with HTTP 500 errors. [PR #7657] (v2.15.3)
- The recommended `memory_limit` is 512M and `-1` counts as fine. Originally 128M [PR #1124] (v1.2.3); the message was aligned with the 512M check [PR #8956] (v3.0.1). [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:47 @7.x]
- `zend.assertions` should be `-1` in production, because core uses `\assert()` for type narrowing. The installer flags other values, and the same recommendations are shown on System Info after install. [PR #11019] (v4.3) [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:219-220 @7.x]
- The minimum database version is inclusive: a server at exactly the minimum passes both the installer schema check and the pre-update check. The strict comparison had rejected MySQL 8.4.0. [PR #15797] (v7.0.1) [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:198 @7.x] [code: app/bundles/CoreBundle/Helper/Update/PreUpdateChecks/CheckDatabaseDriverAndVersion.php:47 @7.x]

### Web and CLI installer
- The web and CLI installers share `InstallService`; `mautic:install <site_url>` takes options named after local.php keys and values can be pre-seeded in local.php. [PR #7395] (v3.1)
- CLI option defaults are empty so they never overwrite values from local.php or env vars. [PR #10104] (v4.0)
- `--db_backup_tables` is parsed as a real boolean (`false`, `0`, `true`). [PR #10757] (v4.2)
- Neither installer configures email: the email step and all `--mailer_*` options were removed, and transports are set up after install. [PR #12216] (v5.0)
- Installing with a table prefix must work through both UI and CLI. Dropping prefix support from the web installer was proposed [PR #9934] (v4.0) and rejected; the installer clears only Doctrine's metadata cache instead of the whole cache folder. [PR #10481] (v4.0.x)
- Wrong database credentials give a handled error, not HTTP 500. [PR #9934] (v4.0)
- If the DB password field is left empty and local.php already has one, the stored password is used, because passwords are never prefilled into HTML forms. [PR #3726] (v2.8)
- The final install step syncs the migrations metadata storage, then marks every migration as applied; a failure of either command aborts the install. [PR #17127] (v7.2.0) [code: app/bundles/InstallBundle/Install/InstallService.php:535 @7.x]
- The CLI installer works on a Composer project that has never served a web request; a missing `var/logs` is scaffolded or tolerated. [PR #17394] (v7.2.1)
- CLI messages are plain text: HTML is stripped and the memory-limit placeholder is filled. [PR #17100] (v7.2.0)

### Install fixtures and schema
- Install fixtures are services in the `group_install` group; `mautic:install:data` loads all fixtures and is idempotent for custom fields. [PR #8366] [PR #8532] (v3.0)
- Fixtures must not run DDL, because DDL commits implicitly and Doctrine's fixture transaction then fails on PHP 8. Indexes belong in entity metadata [PR #10787] (v4.2) and optional field columns are created in a `postGenerateSchema` listener [PR #11059] (v4.3).
- That listener must use the prefixed table name [PR #11128] (v4.3) and must not assume core tables exist when a plugin installs its own schema [PR #11206] (v4.4).
- Redundant single-column indexes are dropped at schema generation for all tables. This replaced a fixture that handled only two xref tables. [PR #11058] (v4.3) [PR #9510] (v3.3.2)
- A fresh install enables the GrapesJS builder; the fixture had to be tagged for the installer to run it again in 5.x. [PR #10112] (v4.0) [PR #13672] (v5.1.0)
- MySQL tables use `row_format => DYNAMIC` to avoid "column size too large" on fresh installs. [PR #6066] (v2.15.1)

### Database platform and connections
- `db_server_version` is no longer stored; Doctrine detects the MySQL or MariaDB version. A hard-coded `5.7` had made Doctrine treat MariaDB as MySQL. [PR #9739] (v4.0). `MAUTIC_DB_SERVER_VERSION` is set only while local.php does not exist; on 7.x its install-time value is `'8.4'`. [code: app/AppKernel.php:52-55 @7.x] [code: app/config/config.php:167 @7.x]
- A read replica is used when `db_host_ro` is set: reads go to that host and writes to `db_host`. [PR #11792] (v5.0). A refactor silently disabled it until [PR #13211] (v5.0.2). [code: app/config/config.php:172-177 @7.x]
- Mautic relies on the feature intersection of MySQL and MariaDB. [PR #8930] (v3.0)

### Configuration storage and loading
- Since 3.0 config values come from env-var-backed parameters, so a UI save does not rebuild the container. [PR #8265] (v3.0). This continued an older decision to avoid a full cache warmup on save. [PR #1192] (v1.2.3)
- A save writes only the parameters in the form; unresolved placeholders such as `%kernel.project_dir%` stay as they are, so an install can be moved. [PR #5663] (v2.13)
- `%` in a value is escaped to `%%` on save and decoded on load, for every string field including multiline ones. [PR #2884] (v2.3) [PR #4034] (v2.9) [PR #4078] (v2.9)
- Config fields may hold `getenv(KEY)` so secrets need not sit in a web-accessible file. [PR #1025] (v1.2.x). This still works on 7.x. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:14-16 @7.x]
- `parameters_local.php` overrides local.php, and the session cookie name stays stable across cache clears when it exists. [PR #4513] (v2.10)
- `site_url` provides the router context for CLI-generated URLs; a trailing slash is stripped and a port is kept only when present. [PR #151] (v1.0) [PR #297] (v1.0.3) [PR #1442] (v1.3)
- `install_source` (default `Mautic`) identifies the installer in anonymous stats; third-party installers set their own. [PR #237] (v1.0) [code: app/bundles/CoreBundle/Config/config.php:719 @7.x]
- `'debug' => true` in local.php enables debug logging in prod, for temporary troubleshooting only. [PR #1220] (v1.2.3)

### Configuration UI and saving
- Each Configuration section is its own page at `/s/config/edit/{tab}`, and only that page's form is built, because rendering every tab was slow. `/s/config/edit` redirects to `coreconfig`, legacy `?tab=` links redirect, and unknown tabs return 404. [PR #17776] (unreleased 7.x) [code: app/bundles/ConfigBundle/Config/config.php:8-15 @7.x]
- A save merges only the current page's values into local.php. Apply stays on the page; Save and Cancel go to the dashboard; leaving with unsaved changes asks for confirmation. Moving the buttons to the bottom of the form was rejected because the top toolbar is the convention for every form. [PR #17776] (unreleased 7.x). This replaced the earlier rule that Apply returns to the last shown tab. [PR #7156] (v2.15.1)
- The `last_shown_tab` hidden field and `Mautic.observeConfigTabs()` are removed; `Mautic.parseQuery()` and `Mautic.parseUrlHashParameter()` stay because plugins may use them. [PR #17776] (unreleased 7.x)
- Settings tabs have no formal ordering rule. [PR #11598] (v5.0)
- Fields can be removed or locked through `security.php` restrictions. [PR #5194] (v2.12)
- Every configuration change is written to the audit log. [PR #6720] (v2.15)
- A user's own language beats the system default locale; changing the system locale affects only users on "System Default Locale". [PR #11119] (v4.4.1)
- Toggle-dependent fields follow the live checked state of the toggle, so "Identify visitors by IP" is disabled while "Anonymize IP" is on. [PR #14416] (v5.2.2)
- In the API tab, token lifetimes are shown in minutes (60) and days (14). [PR #8912] (v3.0)
- Config pages, tab widgets and System Info render with Twig; plugin config widgets must be Twig. [PR #11938] (v5.0)

### DSNs, Messenger and mailer
- Queueing is off by default: every Messenger transport defaults to `sync://`. Any Symfony transport is configured by DSN in the UI, the failure transport is optional, and retry changes apply without a cache clear. [PR #12509] (v5.0). This replaced the first Messenger settings `messenger_dsn` and `messenger_type`. [PR #11598] (v5.0) [code: app/bundles/MessengerBundle/Config/config.php:7-13 @7.x]
- DSNs are stored with URL-encoded parts and `%` doubled to `%%`, and are read through the `urlencoded-dsn` env processor, so secrets with special characters parse. [PR #13255] (v5.0.3) [code: app/config/config.php:99-112 @7.x]
- The DSN help text shows as an inline warning because users missed it. [PR #13876] (v5.2)
- The mailer uses the long `transports` form with Mautic's DSN as `main`, so plugins can add transports and choose one per message with `X-Transport`. [PR #15422] (v7.0)
- `DsnTransformer` is `final`; extend by composition. [PR #16940] (v7.2.0)

### Security-related settings
- `rememberme_lifetime` reaches the firewall as a strict int, so remember-me cookies last the configured lifetime. [PR #11363] (v4.4.1)
- elFinder routes sit in the `main` firewall so remembered users can use the file manager. A dedicated firewall and patching the bundle's routes were rejected. [PR #12430] (v5.0) [PR #12433] (v4.4.10)
- Admin session cookies are `SameSite=Lax`. [PR #11511] (v5.0)
- During install, the Secure cookie flag comes from the request scheme because `site_url` is not yet set. [PR #8422] (v3.0)
- The SAML IdP entity ID can use the site URL or an alternate `subdomain_url` from local config. [PR #12655] (v5.0)

### System Info, logging, dev and test environment
- System Info (admin only) shows PHP info, folder permissions and the error log; `sysinfo_disabled` hides it. [PR #898] (v1.2.1)
- Twig `auto_reload` is on in prod so theme changes show without a cache clear. [PR #3571] (v2.7)
- Functional tests never call third parties: `http_client` is a `MockHttpClient` in `config_test.php`, also when autowired. [PR #12579] [PR #12615] (v5.0)
- Tests hash passwords with md5 and use a static table prefix to keep runs fast. [PR #11498] (v5.0) [PR #11476] (v4.4.3)
- The Symfony debug toolbar is controlled only by `config_dev.php`, not by a check in templates. [PR #16380] (v7.2.0)

## 3. Regression catalogue
| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **Installed detection and bootstrap** | | | |
| DB down redirected a live site to the installer | Installed state comes from config; a DB error is shown | [PR #161] | 1.0 |
| Installer redirect dropped a non-standard port | Redirect keeps the port | [PR #5463] | 2.12.2 |
| "Undefined variable $projectRoot in paths.php" after the 5.x upgrade | `paths.php` resolves the project root itself | [PR #13193] | 5.0.2 |
| Composer installs lost local config on update | Local config lives in `<project_root>/config/` | [PR #11561] | 5.0 |
| **Installer** | | | |
| Install succeeded without cURL, then HTTP 500 | cURL is a requirement | [PR #7657] | 2.15.3 |
| IMAP warning shown when IMAP was installed | Warn only when missing | [PR #981] | 1.2.1 |
| Blank web installer when `memory_limit` < 512M | Requirements page renders with a memory warning | [PR #12121] | 5.0 |
| Installer failed with preconfigured DB and blank password field | Stored DB password is used | [PR #3726] | 2.8 |
| Installer HTTP 500 on bad DB credentials | Handled error | [PR #9934] | 4.0 |
| Web install with prefix: "Table mau_leads does not exist" | Only Doctrine metadata cache is cleared; prefix works | [PR #10481] | 4.0.x |
| Backing up `page_hits` failed on index options | Index options copied to `bak_` tables | [PR #10747] | 4.2 |
| `--db_backup_tables=false` still backed up | Real boolean parsing and storage | [PR #10757] | 4.2 |
| CLI install ignored admin values from local.php | Empty option defaults; local.php and env values used | [PR #10104] | 4.0 |
| CLI install printed `<strong>` and `%min_memory_limit%` | Plain text with 512M filled in | [PR #17100] | 7.2.0 |
| Fresh install left the migrations table missing yet reported success | Metadata storage synced; failure aborts install | [PR #17127] | 7.2.0 |
| CLI install failed `mautic.install.logs.unwritable` on a never-visited Composer project | `var/logs` scaffolded or created | [PR #17394] | 7.2.1 |
| Install on MySQL 8.4.0 (the stated minimum) failed | Minimum version check is inclusive | [PR #15797] | 7.0.1 |
| UI installer broken by a controller refactor | Installer completes; covered by `InstallWorkflowTest` | [PR #11553] [PR #11557] | 5.0 |
| **Fixtures and schema** | | | |
| PHP 8: "There is no active transaction" during fixtures | No DDL in fixtures | [PR #10787] [PR #11059] | 4.2 / 4.3 |
| `doctrine:schema:update` failed on a prefixed DB | Schema listener uses the prefixed table name | [PR #11128] | 4.3 |
| `mautic:plugins:install` failed: no table `leads` in schema | Listener skips core-table logic for plugin schemas | [PR #11206] | 4.4 |
| "Column size too large" on a fresh MySQL install | `row_format=DYNAMIC` | [PR #6066] | 2.15.1 |
| Foreign tables with enum/point/bit broke schema tools | Unknown types mapped to string | [PR #1084] | 1.2.3 |
| `mautic:install:data` duplicated custom fields | Idempotent install data | [PR #8532] | 3.0 |
| GrapesJS off after a fresh 5.x install | GrapesJS enabled on install | [PR #13672] | 5.1.0 |
| **Database connections** | | | |
| `db_host_ro` silently ignored | Reads go to the replica | [PR #13211] | 5.0.2 |
| **Configuration UI and saving** | | | |
| `%text%` in a value threw parameter-not-found | `%` escaped on save, decoded on load | [PR #2884] [PR #4034] [PR #4078] | 2.3–2.9 |
| `cache_path` saved as an absolute path | Only form parameters written; placeholders kept | [PR #5663] | 2.13 |
| Config save with an uploaded SAML file failed | Save with file upload succeeds | [PR #7305] [PR #7512] | 2.16.1 / 3.3.2 |
| API token lifetimes shown as 3600/1209600 | Shown as 60 minutes / 14 days | [PR #8912] | 3.0 |
| System language change overrode a user's language | User preference wins | [PR #11119] | 4.4.1 |
| Toggle-dependent fields did not respond | Fields follow the live toggle state | [PR #14416] | 5.2.2 |
| Save stored only the visible part of the form | Each page saves its own values; unsaved-changes prompt | [PR #17776] | unreleased 7.x |
| **DSNs and Messenger** | | | |
| SQS DSN with special characters failed to parse | DSN parts URL-encoded, `%` doubled, decoded by `urlencoded-dsn` | [PR #13255] | 5.0.3 |
| Retry changes needed a cache clear; failure transport fixed to Doctrine | Retry applies at once; failure transport configurable | [PR #12509] | 5.0 |
| **Security and environment** | | | |
| Remember-me cookie ignored ("Expected int") | Lifetime applied as int | [PR #11363] | 4.4.1 |
| elFinder 401 for remembered users | elFinder routes in `main` firewall | [PR #12430] [PR #12433] | 5.0 / 4.4.10 |
| Logged out on every cache clear with `parameters_local.php` | Session cookie name stable | [PR #4513] | 2.10 |
| Theme change invisible until cache clear | Twig `auto_reload` in prod | [PR #3571] | 2.7 |

## 4. Feature timeline
| Version | Change | PR |
|---|---|---|
| 1.x | Config-based installed check; `site_url` for CLI URLs; `install_source`; System Info and `sysinfo_disabled`; `getenv()` in config; PHP version gate; memory and zip recommendations; prod debug logging | [PR #161] [PR #151] [PR #237] [PR #898] [PR #1025] [PR #788] [PR #1124] [PR #872] [PR #1220] |
| 2.x | `%` escaping; Twig auto-reload in prod; SAML SSO; restricted-field helpers; config audit log; SSL recommendation; `row_format=DYNAMIC`; cURL required | [PR #2884] [PR #3571] [PR #3113] [PR #5194] [PR #6720] [PR #6862] [PR #6066] [PR #7657] |
| 3.0 | Env-var-backed parameters (no rebuild on save); fixture groups; PHP ≥ 7.2 | [PR #8265] [PR #8366] [PR #8167] |
| 3.1 | CLI installer `mautic:install` | [PR #7395] |
| 4.0 | Doctrine detects DB version (`db_server_version` dropped); Database info tab; prefix through UI and CLI | [PR #9739] [PR #9934] [PR #10481] |
| 4.2–4.3 | Index options in backups; boolean `--db_backup_tables`; no DDL in fixtures; redundant-index cleanup; `zend.assertions` recommendation and recommendations on System Info | [PR #10747] [PR #10757] [PR #10787] [PR #11059] [PR #11058] [PR #11019] |
| 4.4 | Remember-me lifetime fixed; system locale no longer overrides user locale | [PR #11363] [PR #11119] |
| 5.0 | User config in `<project_root>/config/`; installer without email step and `--mailer_*`; installed check uses `site_url`; Messenger with DSN transports, failure transport and retry settings; read replica `db_host_ro`; Twig config pages and installer; SameSite=Lax session cookie | [PR #11561] [PR #12216] [PR #12509] [PR #11792] [PR #11938] [PR #11817] [PR #11511] |
| 5.0.2–5.0.3 | `db_host_ro` restored; `urlencoded-dsn` processor | [PR #13211] [PR #13255] |
| 5.1.0 | GrapesJS enabled again on fresh install | [PR #13672] |
| 5.2 | DSN help as inline warning; live toggle state for dependent fields (5.2.2) | [PR #13876] [PR #14416] |
| 6.0 | GitHub Codespaces dev container | [PR #14610] |
| 7.0 | Mailer `transports` with `main`; centred installer window | [PR #15422] [PR #15302] |
| 7.0.1 | Inclusive minimum DB version | [PR #15797] |
| 7.2.0 | Strict migration bootstrap on install; plain-text CLI installer messages; InstallBundle autowired; `DsnTransformer` final | [PR #17127] [PR #17100] [PR #16787] [PR #16940] |
| 7.2.1 | CLI install on a never-visited Composer project | [PR #17394] |
| unreleased 7.x | One page per Configuration section; `last_shown_tab` removed | [PR #17776] |

## 5. Removed, deprecated, replaced
| What | Replaced by | PR | Version |
|---|---|---|---|
| Database-based installed check | Config-parameter check | [PR #161] | 1.0 |
| `mailer_from_name` as installed marker | `site_url` (with `db_driver`) | [PR #12216] | 5.0 |
| Installer email step and `--mailer_*` CLI options | Email configured after install | [PR #12216] | 5.0 |
| `ConfigBuilderEvent::getParameters()` | none (it was broken) | [PR #5980] | 2.14 |
| `ConfigEvent::getPost()` | deprecated | [PR #6720] | 2.15 |
| Queue settings in the UI (`queue_mode`, `queue_protocol`) | local.php edit; later Messenger DSNs | [PR #8265] [PR #12509] | 3.0 / 5.0 |
| `api_rate_limiter_cache.type` | `api_rate_limiter_cache.adapter` | [PR #8305] | 3.0 |
| `db_server_version` in local.php | Doctrine auto-detection; migration removes it | [PR #9739] | 4.0 |
| Full cache wipe during install | Doctrine metadata cache clear | [PR #10481] | 4.0.x |
| `PageHitIndex` and `RemoveDuplicateIndexData` fixtures, column creation in `LeadFieldData` | Entity metadata and schema listeners | [PR #10787] [PR #11058] [PR #11059] | 4.2–4.3 |
| `kernel.root_dir` / `getRootDir()` | `%kernel.project_dir%` / `getProjectDir()` | [PR #11145] | 5.0 |
| `app/config/local.php` and `app/config/*_local.php` | `<project_root>/config/` | [PR #11561] | 5.0 |
| ConfigBundle string service aliases | FQCN autowired services | [PR #11774] | 5.0 |
| Installer and ConfigBundle PHP templates | Twig | [PR #11817] [PR #11938] | 5.0 |
| `messenger_dsn`, `messenger_type` | `messenger_dsn_email`, `messenger_dsn_hit`, `messenger_dsn_failed`, `messenger_retry_strategy_*` | [PR #12509] | 5.0 |
| Mailer short `dsn` config | `transports: {main: ...}` | [PR #15422] | 7.0 |
| InstallBundle `config.php` services | Autowired `services.php` | [PR #16787] | 7.2.0 |
| `last_shown_tab`, `Mautic.observeConfigTabs()` | Per-page config routes | [PR #17776] | unreleased 7.x |

The API rate-limiter parameters (`api_rate_limiter_limit`, `api_rate_limiter_cache`) renamed in [PR #8305] existed in 6.0.0 and are absent from 7.0.0 onwards, because 7.0 removed `noxlogic/ratelimit-bundle`. [code: UPGRADE-7.0.md:52 @7.x]

## 6. Maintainer norms for this area
Project-wide norms (branching, CLA, test requirement) belong to mautic-contributing.
- Installer checks are either blocking requirements or warning recommendations; do not block on anything the app can run without, and make hard dependencies requirements. [PR #872] [PR #6862] [PR #7657]
- A fix for new installs must also repair existing installs, through a migration or a code-side default. [PR #187] [PR #1963]
- Fixtures contain no DDL; schema belongs in entity metadata or Doctrine schema events. [PR #10787] [PR #11058] [PR #11059]
- The installer must work with and without a table prefix through both the UI and the CLI. [PR #9934] [PR #10481] [PR #11128]
- Avoid needless container rebuilds and cache warmups on config save. [PR #1192] [PR #8265]
- Secrets should not have to live in web-accessible files, and passwords are never prefilled into forms. [PR #1025] [PR #3726]
- Anything users must act on (moved config files, removed CLI options, changed installed check) goes into the UPGRADE notes before merge. [PR #11561] [PR #12216] [PR #11145]
- Testers open the config page and the installer in prod mode, because code review alone let installer regressions through; critical-flow regressions get a test. [PR #11142] [PR #11553] [PR #11557]
- Use standard Symfony APIs rather than re-implementing removed framework features. [PR #11145]
- Do not patch third-party bundle routes; adjust Mautic's firewall config. [PR #12430]
- Keep form action buttons in the top toolbar, and keep JS helpers that plugins may still call. [PR #17776]
- Only rely on features that MySQL and MariaDB share. [PR #8930]
- User-facing configuration strings get wording review, and error messages should say how to fix the problem. [PR #12509]

## 7. Open questions
- `sysinfo_disabled`: [PR #898] calls it a parameter, but on 7.x it appears only as a menu check in `ConfigBundle/Config/config.php`, not in a `parameters` array; behaviour.md and SKILL.md treat it as undeclared. [code: app/bundles/ConfigBundle/Config/config.php:45-48 @7.x]
- `rememberme_lifetime`: [PR #11363] describes about one year; the 7.x default is 7,776,000 seconds (90 days). [code: app/bundles/CoreBundle/Config/config.php:282 @7.x]
- Which of the two duplicated DB-version checks is authoritative is undecided. [PR #15797]
- How to override `MAUTIC_DB_SERVER_VERSION` after install is unclear; a reviewer argued `null` is worse than a fixed value. [PR #9739]
- Whether timestamped cron output [PR #2075] is always on or tied to `--no-interaction` was not checked.
- Hand-editing DSNs in local.php needs URL-encoding and `%%`; no docs PR was found. [PR #13255]
- `subdomain_url` has no UI field and no declared default on 7.x. [PR #12655]
- Whether the token-lifetime display fix was ever replaced by a proper default fix is unknown. [PR #8912]
- No automated test covers installing or running with a DB table prefix. [PR #11128]

## 8. Coverage
The inputs covered 158 merged PRs in two chunks: 97 merged 2015-02 to 2022-07 (#67–#11128) and 61 merged 2022-06 to 2026-10 (#11142–#17789).
140 were substantive and 18 were noise or refactors with no behaviour content.
Five PRs only loosely about configuration (#11856, #12131, #15440, #17689, #17789) are left out of this file.
A further 869 noise PRs (translations, dependency bumps, CI) were excluded upstream before chunking.
