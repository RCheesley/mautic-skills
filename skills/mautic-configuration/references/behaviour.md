# Configuration, installer and bootstrap: behaviour specification (Mautic 7.x)

Every item is an observable behaviour with its source. Paths are relative to the Mautic 7.x repository root.
Where docs disagree with code, the code statement is given and the discrepancy is noted under "Doc discrepancies".

## Contents
1. Bootstrap and kernel (B1–B17)
2. Parameter loading and precedence (P1–P17)
3. site_url and URL generation (U1–U8)
4. Timezone and locale (L1–L4)
5. Security headers and trust (S1–S4)
6. Configuration UI (C1–C22)
7. System Info (I1)
8. Installer (N1–N21)
9. Caching of parameters (K1–K3)
10. Test environment (T1–T4)
11. Mailer and Messenger DSNs (D1–D2)
12. DDEV (V1)
13. Doc discrepancies and open questions

## 1. Bootstrap and kernel
B1. The web front controller forces `date_default_timezone_set('UTC')` before bootstrapping and wraps the kernel in the middleware stack. [code: index.php:7-17 @7.x]
B2. `APP_ENV` defaults to `prod` and `APP_DEBUG` defaults to "environment is not prod". A compiled `.env.local.php` takes precedence over the `.env` files when its `APP_ENV` matches. [code: app/config/bootstrap.php:14-27 @7.x]
B3. `IPS_ALLOWED` defaults to `127.0.0.1,::1,172.17.0.1`, and APCu is cleared in dev for allowed IPs. [code: app/config/bootstrap.php:23-32 @7.x]
B4. On the console, `--env/-e` and `--no-debug` are read before bootstrap and exported to `APP_ENV`/`APP_DEBUG`. Debug mode applies `umask(0000)` and `Debug::enable()`. `--no-interaction/-n` adds timestamps to output. [code: app/console-application.php:26-44 @7.x]
B5. The kernel constructor defines `MAUTIC_ENV` and `MAUTIC_VERSION` (from `app/release_metadata.json`, 7.2.1). [code: app/AppKernel.php:41-44 @7.x] [code: app/release_metadata.json:2 @7.x]
B6. `MAUTIC_DB_SERVER_VERSION` is `null` when `config/local.php` exists and `'8.4'` otherwise, so Doctrine can boot without a database during install. [code: app/AppKernel.php:52-55 @7.x] [code: app/config/config.php:167 @7.x]
B7. Mautic is installed if and only if the local parameters contain non-empty `db_driver` and `site_url`. Because `db_driver` is always forced, `site_url` is the effective flag. [code: app/AppKernel.php:272-283 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:219 @7.x] [code: app/bundles/InstallBundle/Install/InstallService.php:125-139 @7.x]
B8. A request defines `MAUTIC_INSTALLER` when Mautic is not installed or when the URI contains `installer` anywhere. Non-installer URIs are then redirected to `/installer`, prefixed with `/index.php` unless the server is Apache with `.htaccess`. [code: app/AppKernel.php:60-84 @7.x]
B9. Outside installer mode, the kernel opens a DB connection before handling the request. If the connection fails, it throws `DatabaseConnectionException` (`mautic.core.db.connection.error`). [code: app/AppKernel.php:90-99 @7.x]
B10. `MAUTIC_TABLE_PREFIX` is defined at boot from `$_SERVER['MAUTIC_TABLE_PREFIX']` first, then from local `db_table_prefix`. [code: app/AppKernel.php:222-232 @7.x] [code: app/config/bootstrap.php:24 @7.x]
B11. Plugins are auto-registered from `plugins/<Dir>/<Name>Bundle.php`. A plugin is skipped when its `MINIMUM_MAUTIC_VERSION` exceeds the running version. [code: app/AppKernel.php:158-187 @7.x]
B12. WebProfiler and Maker load only in dev and test. Liip test bundles load only in test. `config/bundles_local.php` may append bundles. [code: app/AppKernel.php:189-202 @7.x]
B13. The project dir is the first ancestor of `app/` that contains `composer.json`, which supports `mautic/recommended-project` layouts. The webroot comes from `extra.mautic-scaffold.locations.web-root` or `extra.public-dir` and is exposed as the default parameter `local_root`. [code: app/AppKernel.php:290-311 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:272-305 @7.x]
B14. The cache dir is `<cache_path>/<env>` and the log dir is `<log_path>`, with `%kernel.project_dir%` substituted. Both are read from local.php only, with defaults `var/cache/<env>` and `var/logs`. [code: app/AppKernel.php:316-334 @7.x]
B15. Middlewares are discovered from `app/middlewares/*Middleware.php` and cached in `<cache_dir>/middlewares.cache.php`, ordered by `PRIORITY`: CORS 1000, HSTS 900, CatchException 100, IpRestrict (dev) 20, VersionCheck 10, Trust 0. [code: app/bundles/CoreBundle/Cache/MiddlewareCacheWarmer.php:19-51 @7.x] [code: app/middlewares/MiddlewareBuilder.php:22-45 @7.x]
B16. A request on PHP below 8.2.0 or above 8.5.99 gets an HTTP 500 text response before the kernel runs. [code: app/middlewares/VersionCheckMiddleware.php:46-59 @7.x] [code: app/release_metadata.json:4-5 @7.x]
B17. The dev front controller is restricted to `127.0.0.1`, `fe80::1`, `::1`, `dev_hosts`, the `MAUTIC_CUSTOM_DEV_HOSTS` JSON, or any environment with `DDEV_TLD` set. [code: app/middlewares/Dev/IpRestrictMiddleware.php:27-56 @7.x]

## 2. Parameter loading and precedence
P1. Defaults are the merge of every bundle and plugin `Config/config.php` `parameters` array. A duplicate key is last-wins in Finder order. Defaults are cached in a static for the life of the process. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:26 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:163-183 @7.x]
P2. The local file is `%kernel.project_dir%/config/local.php`. When that file is absent but the legacy `app/config/local.php` exists, the legacy file is used. `config/paths_local.php` can override paths. [code: app/config/paths.php:11 @7.x] [code: app/config/paths.php:27-32 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:112-159 @7.x]
P3. The local layers merge in this order: local.php, then `config/parameters_local.php` (same `$parameters` variable), then the `MAUTIC_CONFIG_PARAMETERS` JSON. `db_driver` is then forced to `pdo_mysql`. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:186-222 @7.x]
P4. `loadIntoEnvironment()` runs from `AppKernel::boot`. It exports each merged key as `MAUTIC_` + `mb_strtoupper(key)`. [code: app/AppKernel.php:220-221 @7.x] [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:26 @7.x]
P5. Arrays, and keys whose default is an array, are JSON-encoded; the default is used when the value is empty. `null` becomes `''`. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:19-23 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:87-89 @7.x]
P6. A string value of the form `getenv(NAME)` is replaced by that environment variable's value. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:14-16 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/Loader/EnvVars/ConfigEnvVarsTest.php:26-60 @7.x]
P7. A `MAUTIC_*` key already in `$_ENV` that the loader did not set itself is not overwritten. Real OS or `.env` variables therefore win. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:91-105 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/Loader/ParameterLoaderTest.php:156-170 @7.x]
P8. Effective precedence for a declared key, highest first:
1. Environment variable `MAUTIC_<KEY>`.
2. `MAUTIC_CONFIG_PARAMETERS`.
3. `parameters_local.php`.
4. `local.php`.
5. The bundle default.

[code: app/bundles/CoreBundle/Loader/ParameterLoader.php:186-222 @7.x] [code: app/config/bootstrap.php:14-21 @7.x]
P9. Derived env vars are loaded after the generic export and overwrite same-named keys [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:73-82 @7.x]:
- `MAUTIC_API_OAUTH2_ACCESS_TOKEN_LIFETIME` is minutes×60 (default 3600). `..._REFRESH_TOKEN_LIFETIME` is days×86400 (default 1 209 600). [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:13-17 @7.x]
- `MAUTIC_EL_FINDER_PATH` and `MAUTIC_EL_FINDER_URL`. [code: app/bundles/CoreBundle/Loader/EnvVars/ElFinderEnvVars.php:13-20 @7.x]
- `MAUTIC_MIGRATIONS_TABLE_NAME` is `<db_table_prefix>migrations`. [code: app/bundles/CoreBundle/Loader/EnvVars/MigrationsEnvVars.php:13-14 @7.x]
- `MAUTIC_SAML_ENTITY_ID`, `MAUTIC_SAML_ENABLED` (true when `saml_idp_metadata` is non-empty), `MAUTIC_SAML_LOGIN_PATH=/s/saml/login` and `MAUTIC_SAML_LOGIN_CHECK_PATH=/s/saml/login_check`. [code: app/bundles/CoreBundle/Loader/EnvVars/SAMLEnvVars.php:11-35 @7.x]
- `MAUTIC_SESSION_NAME`. [code: app/bundles/CoreBundle/Loader/EnvVars/SessionEnvVars.php:12-17 @7.x]
- `MAUTIC_REQUEST_CONTEXT_HOST/SCHEME/BASE_URL/HTTP_PORT/HTTPS_PORT`. [code: app/bundles/CoreBundle/Loader/EnvVars/SiteUrlEnvVars.php:11-56 @7.x]
- `MAUTIC_TWIG_CACHE_DIR` is `<tmp_path>/twig`. [code: app/bundles/CoreBundle/Loader/EnvVars/TwigEnvVars.php:13-14 @7.x]

P10. For every declared key, the container parameter `mautic.<key>` is `%env(<processor>resolve:MAUTIC_<KEY>)%`. The processor follows the default's type:

| Default type | Processor |
|---|---|
| bool | `bool:` |
| int | `intNullable:` (but `rememberme_lifetime` uses `int:`) |
| array | `json:` |
| float | `float:` |
| anything else | `nullable:` |

[code: app/config/parameters.php:13-49 @7.x]
P11. The custom env processors:
- `nullable`: `''` becomes null.
- `intNullable`.
- `mauticconst`: reads a PHP constant.
- `urlencoded-dsn` / `mailer`: unescapes `%%`; an invalid DSN becomes `invalid://null`.
- `messenger-nullable`: an empty value becomes `null://`.

[code: app/bundles/CoreBundle/DependencyInjection/EnvProcessor/NullableProcessor.php:9-14 @7.x] [code: app/bundles/EmailBundle/DependencyInjection/EnvProcessor/MailerDsnEnvVarProcessor.php:12-22 @7.x] [code: app/bundles/MessengerBundle/DependencyInjection/EnvProcessor/MessengerNullableEnvVarProcessor.php:11-14 @7.x]
P12. `CoreParametersHelper::get()` works as follows [code: app/bundles/CoreBundle/Helper/CoreParametersHelper.php:30-46 @7.x]:
- It accepts both `foo` and `mautic.foo`.
- For `db_table_prefix` it returns the `MAUTIC_TABLE_PREFIX` constant when that is defined.
- Otherwise it prefers the container parameter and falls back to the merged bag.
- As a result, undeclared local.php keys are readable but are neither env-overridable nor type-cast.
P13. `getDefaultTimezone()` returns `UTC` when `default_timezone` is empty. [code: app/bundles/CoreBundle/Helper/CoreParametersHelper.php:72-79 @7.x]
P14. The session cookie name is `md5(md5(<local config path>) . (secret_key ?: 'mautic'))`. Moving the install or changing `secret_key` invalidates all sessions. [code: app/bundles/CoreBundle/Loader/EnvVars/SessionEnvVars.php:12-17 @7.x] [code: app/config/config.php:91 @7.x]
P15. Migrations are tracked in table `<db_table_prefix>migrations`. [code: app/bundles/CoreBundle/Loader/EnvVars/MigrationsEnvVars.php:13-14 @7.x] [code: app/config/config.php:229-234 @7.x]
P16. Optional override files are read from the config base dir:
- `config/security_local.php` replaces `security.php`.
- `config/config_override.php` and `config/config_local.php` are imported after the main config.
- `config/bundles_local.php` adds bundles.
- `config/paths_local.php` overrides paths.

[code: app/config/config_prod.php:10-14 @7.x] [code: app/config/config_prod.php:77-85 @7.x] [code: app/AppKernel.php:199-202 @7.x]
P17. Git ignores `/.env.local`, `/.env.local.php`, `/.env.*.local`, `/config/*` (except `.gitkeep`) and the legacy `app/config/local*.php`. [code: .gitignore:15-17 @7.x] [code: .gitignore:51-57 @7.x]

## 3. site_url and URL generation
U1. `site_url` is parsed into router-context env vars [code: app/bundles/CoreBundle/Loader/EnvVars/SiteUrlEnvVars.php:11-56 @7.x]:
- host: required for any of the vars to be set;
- scheme: defaults to `http`;
- base URL: `index.php` and the trailing slash are stripped;
- port: goes to the HTTP or HTTPS port var by scheme (defaults 80/443).
U2. On every request and finish-request, `RouterSubscriber` forces the router context to those values, so web and CLI generate identical URLs. It does nothing when the host is empty or during install. [code: app/bundles/CoreBundle/EventListener/RouterSubscriber.php:36-77 @7.x]
U3. If `site_url` starts with `https`, all public routes are forced to the https scheme. [code: app/bundles/CoreBundle/Loader/RouteLoader.php:34-43 @7.x]
U4. The session `cookie_secure` is decided at compile time: true when `site_url` starts with `https`, or in the installer when the request is secure. [code: app/config/config.php:35-44 @7.x] [code: app/config/config.php:92 @7.x]
U5. Trailing-slash redirects are built as `rtrim(site_url,'/') . '/' . ltrim(path,'/')`. [code: app/bundles/CoreBundle/Helper/TrailingSlashHelper.php:14-20 @7.x]
U6. The ElFinder URL is `rtrim(site_url,'/') . '/' . trim(image_path,'/')`. The path is `<local_root or project dir>/<image_path>`. [code: app/bundles/CoreBundle/Loader/EnvVars/ElFinderEnvVars.php:13-20 @7.x]
U7. The SAML entity id falls back to `scheme://host` of `site_url`. When `site_url` has no host or is malformed, it is the literal `mautic`. [code: app/bundles/CoreBundle/Loader/EnvVars/SAMLEnvVars.php:11-29 @7.x]
U8. In the form, `site_url` is a required `UrlType` with default protocol https. No trailing-slash normalisation is applied on save. [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:51-68 @7.x]

## 4. Timezone and locale
L1. On login, the session gets `_timezone` (the User's timezone, else `default_timezone`, else UTC) and `_locale` (the User's locale, else the system `locale`). [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:60-84 @7.x]
L2. On each request with a session, PHP's timezone is set from `_timezone` (priority 128). The request locale is set from `_locale` or `locale` (priority 101). [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:21-61 @7.x]
L3. Saving the configuration sets session `_locale` to the User's locale, else the saved `locale`. A User-level locale always beats the system locale. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:299-310 @7.x] [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:344-400 @7.x]
L4. Saving a `locale` whose language pack is not installed downloads the pack. If the download fails, the value resets to `en_US` and a form error is added. [code: app/bundles/CoreBundle/EventListener/ConfigSubscriber.php:49-76 @7.x] [docs: https://docs.mautic.org/en/7.2/translations/translations.html#how-to-update-a-language]

## 5. Security headers and trust
S1. `trusted_proxies` and `trusted_hosts` from local.php are applied before the kernel handles the request, via `Request::setTrustedProxies(..., Request::getTrustedHeaderSet())` and `setTrustedHosts`. [code: app/middlewares/TrustMiddleware.php:30-43 @7.x]
S2. Each `trusted_hosts` entry must be a valid domain name or a valid PCRE regexp; otherwise the form raises `...trusted_hosts.invalid.regexp` or `.invalid.domain`. [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:203-248 @7.x]
S3. CORS behaviour [code: app/middlewares/CORSMiddleware.php:54-124 @7.x]:
- With `cors_restrict_domains=true` (the default), `Access-Control-Allow-Origin` echoes the Origin only when it is listed in `cors_valid_domains` or matches a case-insensitive `fnmatch` wildcard. A wildcard match also adds `Vary: Origin`.
- `OPTIONS` preflight gets 204 only when the origin is valid and the request has `Origin` and `Access-Control-Request-Headers`.
- XHR responses always get the header.
S4. The HSTS header `max-age=<headers_sts_expire_time>[; includeSubDomains][; preload]` is added to main-request responses only when `headers_sts` is true and the expire time is non-zero. [code: app/middlewares/HSTSMiddleware.php:37-52 @7.x] [code: app/middlewares/Tests/HSTSMiddlewareTest.php:50-120 @7.x]

## 6. Configuration UI
C1. Only admins may open, save, download or remove configuration. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:41-43 @7.x] [code: app/bundles/ConfigBundle/Controller/ConfigController.php:206-208 @7.x] [code: app/bundles/ConfigBundle/Controller/ConfigController.php:241-243 @7.x]
C2. The form is built from every `CONFIG_ON_GENERATE` listener's `addForm()`. `addForm` is keyed by `formAlias`, so a later call with the same alias replaces the earlier one. [code: app/bundles/ConfigBundle/Event/ConfigBuilderEvent.php:38-47 @7.x]
C3. Tabs are the aliases with non-empty `parameters`. `/s/config/edit` redirects to the legacy `?tab=` value or to `coreconfig`. An unknown tab is a 404. Only the active tab's sub-form is built, and a POST without a tab saves nothing. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:55-71 @7.x] [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:79-136 @7.x]
C4. Values shown in the form are the container-resolved values overlaid by raw local.php values. Restricted keys are removed from the form data entirely. [code: app/bundles/ConfigBundle/Mapper/ConfigMapper.php:43-72 @7.x] [code: app/bundles/ConfigBundle/Controller/ConfigController.php:270-294 @7.x]
C5. A contributed form with no `parameters` key throws `BadFormConfigException`. [code: app/bundles/ConfigBundle/Mapper/ConfigMapper.php:30-32 @7.x]
C6. The restricted list is `db_driver, db_host, db_table_prefix, db_name, db_user, db_password, db_path, db_port, secret_key`, plus `transifex_username` and `transifex_password` in prod. The default display mode is `remove`. [code: app/config/security.php:182-200 @7.x]
C7. `MODE_REMOVE` removes restricted fields. `MODE_MASK` re-adds them disabled and unmapped with placeholder `mautic.config.restricted`. Nested restrictions such as `monitored_email => [EmailBundle_bounces]` apply to sub-forms. [code: app/bundles/ConfigBundle/Form/Helper/RestrictionHelper.php:32-82 @7.x] [code: app/bundles/ConfigBundle/Mapper/Helper/RestrictionHelper.php:10-54 @7.x]
C8. Every leaf value is escaped on save (`%` → `%%`). The exceptions are the allowed container parameters in `config_allowed_parameters`, which are written unescaped. Values are unescaped for display. [code: app/bundles/ConfigBundle/Form/Type/EscapeTransformer.php:29-92 @7.x] [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:51-77 @7.x]
C9. Saving requires a writable local.php, or a writable directory for it. Otherwise the form shows `mautic.config.notwritable` and nothing is written. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:86-92 @7.x] [code: app/bundles/CoreBundle/Configurator/Configurator.php:50-59 @7.x]
C10. `CONFIG_PRE_SAVE` runs after form validation. Listener errors abort the save and are shown as form or field errors, translated in the `validators` domain. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:104-125 @7.x]
C11. The core `CONFIG_PRE_SAVE` listeners:
- Api casts `api_enable_basic_auth` to bool.
- Campaign and Page escape `campaign_time_wait_on_event_false` and `google_analytics` with htmlspecialchars.
- Core preserves `transifex_password` and downloads the locale pack.
- Email preserves monitored-mailbox passwords and resets incomplete mailboxes.
- User preserves `saml_idp_own_password` and validates and base64-encodes the uploaded SAML files.
- Social escapes `twitter_handle_field`.

[code: app/bundles/ApiBundle/EventListener/ConfigSubscriber.php:36-38 @7.x] [code: app/bundles/CampaignBundle/EventListener/ConfigSubscriber.php:17 @7.x] [code: app/bundles/CoreBundle/EventListener/ConfigSubscriber.php:42-77 @7.x] [code: app/bundles/PageBundle/EventListener/ConfigSubscriber.php:70-72 @7.x] [code: app/bundles/EmailBundle/EventListener/ConfigSubscriber.php:38-66 @7.x] [code: app/bundles/UserBundle/EventListener/ConfigSubscriber.php:45-93 @7.x] [code: plugins/MauticSocialBundle/EventListener/ConfigSubscriber.php:23 @7.x]
C12. Fields registered through `unsetIfEmpty()`, and all file fields, are dropped from the submitted data when empty, so stored secrets survive an empty submission. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:127-137 @7.x] [code: app/bundles/ConfigBundle/Event/ConfigEvent.php:88-104 @7.x]
C13. Saving one tab merges only that tab's array into local.php. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:131-140 @7.x] [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:138 @7.x]
C14. If local.php has no `secret_key` after merging, a new key is generated before writing: `sha256(uniqid(mt_rand(), true))`. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:144-147 @7.x] [code: app/bundles/CoreBundle/Helper/EncryptionHelper.php:45-48 @7.x]
C15. After a successful write, these happen in order [code: app/bundles/ConfigBundle/Controller/ConfigController.php:149-157 @7.x]:
1. `CONFIG_POST_SAVE` is dispatched.
2. The flash `mautic.config.config.notice.updated` is shown.
3. `CacheHelper::refreshConfig()` runs.

A `RuntimeException` produces the flash `mautic.config.config.error.not.updated` instead.
C16. Save redirects to the dashboard. Apply stays on the tab. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:171-177 @7.x]
C17. A save with at least one changed value writes one audit-log entry (`bundle=config, object=config, objectId=0, action=update`) listing the changed keys. `transifex_password` and `mailer_is_owner` are excluded, and uploaded files are logged by filename. [code: app/bundles/ConfigBundle/Service/ConfigChangeLogger.php:19-22 @7.x] [code: app/bundles/ConfigBundle/Service/ConfigChangeLogger.php:48-82 @7.x]
C18. When `trackingconfig.anonymize_ip` flips to true, `CONFIG_POST_SAVE` anonymises all stored IP addresses and audit-log IPs, unless `anonymize_ip_address_in_background` is true. [code: app/bundles/ConfigBundle/EventListener/ConfigSubscriber.php:26-51 @7.x]
C19. File-type values are stored base64-encoded and are never shown in the form. Download one via `/s/config/download/<key>`, which returns 404 for an unregistered key. Remove one via `/s/config/remove/<key>`, which writes `null` and returns JSON `{success}`. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:204-265 @7.x]
C20. DSN fields mask the stored password as `🔒`, and submitting the mask keeps the stored password. An empty DSN is allowed only when the field is optional. The rendered view exposes `currentDsn` with the password replaced by `SECRET`. [code: app/bundles/ConfigBundle/Form/DataTransformer/DsnTransformer.php:45-77 @7.x] [code: app/bundles/ConfigBundle/Form/Type/DsnType.php:155-175 @7.x]
C21. local.php is rendered as `$parameters = array(...)`, with these rules [code: app/bundles/CoreBundle/Configurator/Configurator.php:193-245 @7.x]:
- strings are single-quoted, with `\` and `'` escaped;
- booleans and null are written as literals;
- nested arrays are rendered recursively;
- keys whose value is `''` are omitted.
C22. When an OAuth2 lifetime is absent from local.php and its value equals the default in seconds (3600 or 1 209 600), the form converts it back to minutes or days (60, 14). [code: app/bundles/ConfigBundle/Form/Type/ConfigType.php:26-37 @7.x]

## 7. System Info
I1. `/s/sysinfo` is denied to non-admins and when `sysinfo_disabled` is truthy. It shows [code: app/bundles/ConfigBundle/Controller/SysinfoController.php:21-43 @7.x] [code: app/bundles/ConfigBundle/Model/SysinfoModel.php:40-141 @7.x]:
- sanitised phpinfo;
- requirement and recommendation messages from `CheckStep`;
- whether local.php, the cache, log, upload, images and translations paths are writable;
- the last 200 lines of `log_path/mautic_<ENV>-<Y-m-d>.php`;
- the DB version, driver and platform.

## 8. Installer
N1. Installer steps are `mautic.configurator.step` services: check (0), doctrine (1), user (2). [code: app/bundles/InstallBundle/Config/services.php:31-36 @7.x] [code: app/bundles/CoreBundle/Configurator/Configurator.php:114-124 @7.x]
N2. `/installer` is outside the firewall. Its only protection is the installed check, which redirects to the dashboard. [code: app/config/security.php:6-11 @7.x] [code: app/bundles/InstallBundle/Controller/InstallController.php:43-45 @7.x]
N3. Hard requirements: `vendor/composer` present; config file writable; `cache_path` and `log_path` writable; PHP default timezone valid; the functions `json_encode`, `session_start`, `ctype_alpha`, `token_get_all`, `simplexml_import_dom`, `curl_init`, `finfo_open` and `mb_strtolower`; an OpenSSL cipher; xdebug `show_exception_trace` and `scream` off; PDO with the mysql driver. [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:73-152 @7.x] [code: app/bundles/InstallBundle/Configurator/Step/DoctrineStep.php:95-108 @7.x]
N4. Recommendations (warnings only): xdebug nesting > 100, zip, `date.timezone` set, DOM, iconv, xml, `imap_open`, an https `site_url`, `posix_isatty`, `memory_limit` ≥ 512M, intl/`Locale`, a working `Collator`, and `zend.assertions = -1`. The CLI asks "Continue with install anyway?" unless `--force` is given. [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:154-224 @7.x] [code: app/bundles/InstallBundle/Command/InstallCommand.php:245-260 @7.x]
N5. The installer creates the cache and log directories before the check. [code: app/bundles/InstallBundle/Install/InstallService.php:205-215 @7.x]
N6. Database parameters require a driver, host, name, user, a port > 0, and a driver in `['pdo_mysql']`. [code: app/bundles/InstallBundle/Install/InstallService.php:248-285 @7.x]
N7. The database step [code: app/bundles/InstallBundle/Install/InstallService.php:290-338 @7.x] [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:70-111 @7.x]:
1. tests the credentials without the db name;
2. validates the server version;
3. creates the database if connecting with the name fails;
4. writes the `db_*` values to local.php and refreshes the config.
N8. The installer refuses MySQL < 8.4.0, MariaDB < 10.11.0 and any non-MySQL platform. [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:177-201 @7.x] [code: app/release_metadata.json:6-7 @7.x]
N9. Schema install sets `foreign_key_checks = 0`. When `backup_tables` is true it renames existing tables to `<backup_prefix>` (default `bak_`); otherwise it drops them. It then runs the ORM schema SQL. [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:119-175 @7.x]
N10. During schema generation, `postGenerateSchema` adds the core Contact/Company columns and the `contact_attribution`, `date_added_country_index`, `company_filter` and `company_match` indexes. [code: app/bundles/InstallBundle/EventListener/DoctrineEventSubscriber.php:14-51 @7.x]
N11. The installer loads the `group_install` fixtures, appending in DELETE purge mode [code: app/bundles/InstallBundle/Install/InstallService.php:393-411 @7.x] [code: app/bundles/InstallBundle/InstallFixtures/ORM/RoleData.php:19-43 @7.x]:
- `RoleData`: the admin Role;
- `LeadFieldData`: the core Contact and Company fields;
- `LoadReportData`: the sample Reports.
N12. Admin User creation [code: app/bundles/InstallBundle/Install/InstallService.php:416-509 @7.x] [code: app/bundles/InstallBundle/Form/Type/UserStepType.php:117-124 @7.x]:
- User id 1 is reused if it exists.
- First name, last name, username, email and password are required.
- The email is validated, and the password must be at least 6 characters; the web form adds `NotWeak`.
- The User gets Role id 1.
N13. The final step writes a new `secret_key` and `site_url`, then runs `doctrine:migrations:sync-metadata-storage` and `doctrine:migrations:version --add --all`. A non-zero exit throws. [code: app/bundles/InstallBundle/Install/InstallService.php:514-547 @7.x]
N14. The check step also persists the `cache_path`, `log_path` and `site_url` defaults into local.php. [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:25-33 @7.x] [code: app/bundles/InstallBundle/Configurator/Step/CheckStep.php:234-246 @7.x]
N15. The web installer tracks completed steps in session `mautic.installer.completedsteps` and redirects back when a later step is requested directly. The step index is a float: 1.1 is schema, 1.2 is fixtures. On step 1, an empty DB password falls back to the local `db_password`. [code: app/bundles/InstallBundle/Controller/InstallController.php:51-188 @7.x]
N16. `finalAction` is reachable only after install. It clears the installer session keys and runs `finalMigrationStep()`. [code: app/bundles/InstallBundle/Controller/InstallController.php:219-263 @7.x]
N17. `mautic:install` exits 0 immediately when Mautic is already installed. [code: app/bundles/InstallBundle/Command/InstallCommand.php:155-159 @7.x]
N18. `mautic:install` builds its values in three layers [code: app/bundles/InstallBundle/Command/InstallCommand.php:183-227 @7.x]:
- Built-in defaults: `pdo_mysql`, backup tables true, prefix `bak_`, admin `Admin Mautic / admin`.
- local.php `db_*` and `admin_*` values override the built-in defaults.
- CLI options override local.php.

The exception is `site_url`: an existing local.php `site_url` wins over the argument.
N19. `mautic:install` failures return `(int) -$step`: `0` for a requirements failure, `-1` for database, schema or fixtures, `-2` for the admin User and `-3` for the final config. [code: app/bundles/InstallBundle/Command/InstallCommand.php:243 @7.x] [code: app/bundles/InstallBundle/Command/InstallCommand.php:283-338 @7.x]
N20. The CLI installer defines `MAUTIC_INSTALLER` (except under PHPUnit) and strips HTML from its messages. `InstallCommandPass` propagates `--db_table_prefix` into the prefix subscriber and the schema helpers. DB params may use `getenv(NAME)` placeholders. [code: app/bundles/InstallBundle/Command/InstallCommand.php:167-170 @7.x] [code: app/bundles/InstallBundle/DependencyInjection/Compiler/InstallCommandPass.php:14-35 @7.x] [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:44-49 @7.x]
N21. `mautic:install:data` destroys the schema and loads sample data: it drops and recreates the schema, then loads the fixtures in `group_mautic_install_data`. [code: app/bundles/CoreBundle/Command/InstallDataCommand.php:6-90 @7.x]

## 9. Caching of parameters
K1. `refreshConfig()` does three things: clears the session menu cache, runs `opcache_invalidate(local.php)` and runs `apcu_clear_cache()`. `nukeCache()` removes the cache dir and calls `opcache_reset`. `clearSymfonyCache()` runs `cache:clear` in-process. [code: app/bundles/CoreBundle/Helper/CacheHelper.php:26-62 @7.x] [code: app/bundles/CoreBundle/Helper/CacheHelper.php:78-103 @7.x]
K2. A manual edit of a value read through `%env()%` needs no container rebuild. These settings are read at compile time and do need `bin/console cache:clear`:
- `cookie_secure` (from the `site_url` scheme);
- `db_host_ro`;
- the kernel cache and log dirs;
- https route forcing.

The runtime nature of `%env()%` is Symfony framework behaviour and was not verified in vendor code. [code: app/config/config.php:35-44 @7.x] [code: app/config/config.php:172-185 @7.x] [code: app/AppKernel.php:316-334 @7.x]
K3. `mautic:cache:clear` clears only the Mautic cache adapter (`CacheProviderInterface::clear()`). [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:7-22 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html]

## 10. Test environment
T1. In `test` [code: app/config/config_test.php:16-159 @7.x] [code: .env.test:2-13 @7.x]:
- the DB comes from `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWD`;
- the table prefix comes from `MAUTIC_DB_PREFIX` (`test_`);
- `secret_key` is fixed;
- update checks are disabled and `rss_notification_url` is null;
- `batch_sleep_time` is 0;
- sessions are mock files;
- HTTP clients are mocked.
T2. The test password hasher is md5, and HTTP basic auth is on for the main firewall. [code: app/config/security_test.php:3-27 @7.x]
T3. `AppTestKernel` always reports installed and honours `TEST_CACHE_DIR`/`TEST_LOG_DIR`. [code: app/AppTestKernel.php:11-32 @7.x]
T4. Functional tests inject `configParams` through `MAUTIC_CONFIG_PARAMETERS`. The defaults enable the API and basic auth, and set `site_url=https://localhost`, `mailer_dsn=null://null`, in-memory messenger transports and `create_custom_field_in_background=false`. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:111-114 @7.x]

## 11. Mailer and Messenger DSNs
D1. `mailer_dsn` must parse as `scheme://[user[:pass]@]host[:port][/path][?options]`, with a mandatory host; literal DSNs listed in `Dsn::ALLOWED_DSN_ARRAY` are also accepted. The env processor turns an unparsable value into `invalid://null`. Values pasted into local.php must be URL-encoded. [code: app/bundles/CoreBundle/Helper/Dsn/Dsn.php:42-68 @7.x] [code: app/bundles/EmailBundle/DependencyInjection/EnvProcessor/MailerDsnEnvVarProcessor.php:12-22 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#smtp-transport]
D2. The Messenger transports `email` and `hit` use `urlencoded-dsn` and Mautic's `RetryStrategy`. `failed` uses `messenger-nullable`, so an empty value becomes `null://`. The defaults are `sync://`, which means no queue. [code: app/config/config.php:102-127 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mautic-doesn-t-use-queues-by-default]

## 12. DDEV
V1. DDEV setup copies files into place and then runs commands [code: .ddev/mautic-setup.sh:8-25 @7.x] [code: .ddev/local.config.php.dist @7.x]:
- `.ddev/local.config.php.dist` becomes `config/local.php` (DB `db`, `install_source=DDEV`, mailer `smtp://localhost:1025`).
- `.ddev/.env.local.dist` becomes `.env.local` (`APP_ENV=dev`).
- It runs `mautic:install https://<host> --force --no-interaction`.
- It runs `cache:warmup --env=dev` and `mautic:plugins:reload`.

## 13. Doc discrepancies and open questions
- "Default item limit per page": the docs say `10`; the code default is `30`. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#system-defaults] [code: app/bundles/CoreBundle/Config/config.php:285 @7.x]
- CORS "Restrict Domains": the docs table says the default is No; the code default is `true`. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#cors-settings] [code: app/bundles/CoreBundle/Config/config.php:702 @7.x]
- The install docs say `db_driver` and `mailer_from_name` mark Mautic as installed. In code it is `db_driver` and `site_url`. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] [code: app/AppKernel.php:272-283 @7.x]
- The docs list `--mailer_*` options (Swiftmailer-era) for `mautic:install`. The 7.2.1 command has none. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] [code: app/bundles/InstallBundle/Command/InstallCommand.php:58-147 @7.x]
- Several docs pages still use `app/config/local.php`. The 7.x path is `config/local.php`, with a legacy fallback. [docs: https://docs.mautic.org/en/7.2/configuration/smime_email_signing.html#configuration] [code: app/config/paths.php:11 @7.x]
- The docs say PHP 7.4 is the minimum. The code requires 8.2.0. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#how-can-you-specify-a-php-version] [code: app/release_metadata.json:4 @7.x]
- The docs say "complex password since 5.1". The CLI installer only checks for at least 6 characters; the web form adds `NotWeak`. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] [code: app/bundles/InstallBundle/Install/InstallService.php:416-509 @7.x]
- Open: which of the two `marketplace_website_url` defaults wins depends on Finder order. [code: app/bundles/CampaignBundle/Config/config.php:178 @7.x] [code: app/bundles/MarketplaceBundle/Config/config.php:42 @7.x]
- Open: the intended meaning of `media_path`, `redis_primary_only` and `campaigns_resume_stuck_records_after` is undocumented. [unverified]
