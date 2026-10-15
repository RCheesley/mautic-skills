# Mautic 7.x parameter reference

## Contents
1. How to read this table
2. CoreBundle
3. ConfigBundle
4. ApiBundle
5. AssetBundle
6. CacheBundle
7. CampaignBundle
8. DashboardBundle
9. EmailBundle
10. FormBundle
11. LeadBundle
12. MarketplaceBundle
13. MessengerBundle
14. NotificationBundle
15. PageBundle
16. ReportBundle
17. SmsBundle
18. UserBundle
19. WebhookBundle
20. Plugins
21. Undeclared keys that are read or written
22. Non-parameter container settings
23. Legacy keys still in docs

## 1. How to read this table
- **Default** is the literal value in the owning bundle's `Config/config.php` `parameters` array. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:169-183 @7.x]
- **Type** is the PHP type of the default. It selects the env processor: bool → `bool:`, int → `intNullable:`, array → `json:`, float → `float:`, else `nullable:`. [code: app/config/parameters.php:21-49 @7.x]
- **Env var** for every row is `MAUTIC_` + the upper-cased name (for example `site_url` → `MAUTIC_SITE_URL`). Arrays are passed as JSON. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:13-28 @7.x]
- **UI** is the Configuration tab `formAlias`, followed by the docs label in quotes where the docs name the field. "—" means local.php or env only. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:55 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html]
- **Meaning** marked *(inferred)* comes from the name and default only; the rest was traced in code or docs.
- **Citation** gives the declaration (bundle `config.php` line range) plus the main consumer where it was traced.
- Tab labels: coreconfig = System Settings, themeconfig = Theme Settings, privacyconfig = Privacy Centre (7.x after 7.2.1, unreleased; [PR #17781]), apiconfig = API Settings, assetconfig = Asset Settings, campaignconfig = Campaign Settings, emailconfig = Email Settings, formconfig = Form Settings, leadconfig = Contact Settings, segment_config = Segment Settings, companyconfig = Company Settings, messengerconfig = Queue Settings, notification_config = Notification Settings, pageconfig = Landing Page Settings, trackingconfig = Tracking Settings, reportconfig = Report Settings, smsconfig = Text Message Settings, userconfig = User/Authentication Settings, webhookconfig = Webhook Settings, social_config = Social Settings.

## 2. CoreBundle
Owning bundle: CoreBundle. Declared in `app/bundles/CoreBundle/Config/config.php:249-812`. Abbreviated citation: `[code: app/bundles/CoreBundle/Config/config.php:249-812 @7.x]` = **[C]**.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `site_url` | `''` | string | coreconfig "Site URL" (required, https default) | Public base URL. Drives the router context, https forcing, the secure cookie, the SAML entity id, the ElFinder URL and the installed check. | Core | [C] [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:51-68 @7.x] [code: app/AppKernel.php:272-283 @7.x] |
| `webroot` | `''` | string | coreconfig "Mautic's root URL Landing Page" | Landing Page id shown at `/` instead of the dashboard redirect. | Core | [C] [code: app/bundles/CoreBundle/Controller/DefaultController.php:33-40 @7.x] |
| `404_page` | `''` | string | coreconfig "404 page" | Landing Page id rendered for not-found responses when published. | Core | [C] [code: app/bundles/CoreBundle/Controller/CommonController.php:571-580 @7.x] |
| `cache_path` | `'%kernel.project_dir%/var/cache'` | string | coreconfig "Path to the cache directory" | Kernel cache root `<cache_path>/<env>`; read from local.php only. | Core | [C] [code: app/AppKernel.php:316-325 @7.x] |
| `log_path` | `'%kernel.project_dir%/var/logs'` | string | coreconfig "Path to logs directory" | Kernel log dir and Mautic log handler path. | Core | [C] [code: app/AppKernel.php:327-334 @7.x] [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:14-24 @7.x] |
| `max_log_files` | `7` | int | — | Rotating log retention for the `mautic` channel. | Core | [C] [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:16 @7.x] |
| `log_file_name` | `'mautic_%kernel.environment%.php'` | string | — | Mautic log file name. | Core | [C] [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:15 @7.x] |
| `image_path` | `'media/images'` | string | coreconfig "Path to images directory" | Webroot-relative image dir for ElFinder; `.`/`..` rejected. | Core | [C] [code: app/bundles/CoreBundle/Loader/EnvVars/ElFinderEnvVars.php:15-20 @7.x] [code: app/bundles/CoreBundle/Tests/Functional/EventListener/ConfigSubscriberTest.php:56-105 @7.x] |
| `media_path` | `'media'` | string | — | Media root *(inferred)*. | Core | [C] |
| `tmp_path` | `'%kernel.project_dir%/var/tmp'` | string | — | Temp dir; Twig cache `<tmp_path>/twig`. | Core | [C] [code: app/bundles/CoreBundle/Loader/EnvVars/TwigEnvVars.php:14 @7.x] |
| `theme` | `'blank'` | string | themeconfig "Default Theme" | Default theme for Forms without a theme and the auto-generated Preference Center. | Core | [C] [code: app/bundles/CoreBundle/EventListener/ConfigThemeSubscriber.php:21-38 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#theme-settings] |
| `theme_import_allowed_extensions` | `['json','twig','css','js','htm','html','txt','jpg','jpeg','png','gif']` | array | themeconfig | File extensions allowed inside an uploaded theme zip. | Core | [C] |
| `brand_name` | `'Your Brand (configurable)'` | string | themeconfig | Brand name in the UI *(inferred)*. | Core | [C] |
| `primary_brand_color` | `'000000'` | string | themeconfig | Brand colour hex *(inferred)*. | Core | [C] |
| `rounded_corners` | `'0'` | string | themeconfig | UI corner style *(inferred)*. | Core | [C] |
| `gravatar_enabled` | `false` | bool | privacyconfig | Allow Gravatar lookups *(inferred)*. 7.x after 7.2.1, unreleased [PR #17781]. | Core | [C] [code: app/bundles/CoreBundle/EventListener/ConfigPrivacySubscriber.php:21-34 @7.x] |
| `db_driver` | `'pdo_mysql'` | string | — (restricted) | Always forced to `pdo_mysql`. | Core | [C] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:219 @7.x] |
| `db_host` | `'127.0.0.1'` | string | — (restricted) | DBAL host. | Core | [C] [code: app/config/config.php:151 @7.x] |
| `db_port` | `3306` | int | — (restricted) | DBAL port. | Core | [C] [code: app/config/config.php:152 @7.x] |
| `db_name` | `''` | string | — (restricted) | Database name. | Core | [C] [code: app/config/config.php:153 @7.x] |
| `db_user` | `''` | string | — (restricted) | DB user. | Core | [C] [code: app/config/config.php:154 @7.x] |
| `db_password` | `''` | string | — (restricted) | DB password. | Core | [C] [code: app/config/config.php:155 @7.x] |
| `db_table_prefix` | `''` | string | — (restricted) | Table prefix; becomes constant `MAUTIC_TABLE_PREFIX` and the migrations table prefix. | Core | [C] [code: app/AppKernel.php:222-232 @7.x] [code: app/bundles/CoreBundle/Loader/EnvVars/MigrationsEnvVars.php:14 @7.x] |
| `db_host_ro` | `null` | null | — | Read-replica host; when set, the connection uses `PrimaryReadReplicaConnectionWrapper` (compile time). | Core | [C] [code: app/config/config.php:172-185 @7.x] |
| `locale` | `'en_US'` | string | coreconfig "Default language" | Default locale; saving downloads the language pack. | Core | [C] [code: app/config/config.php:84 @7.x] [code: app/bundles/CoreBundle/EventListener/ConfigSubscriber.php:54-74 @7.x] |
| `secret_key` | `'temp'` | string | — (restricted) | `framework.secret`, encryption key, session-name salt, remember-me key, mail hash. Generated at install and on save if missing. | Core | [C] [code: app/config/config.php:74 @7.x] [code: app/bundles/CoreBundle/Helper/EncryptionHelper.php:39 @7.x] [code: app/bundles/InstallBundle/Install/InstallService.php:518 @7.x] |
| `dev_hosts` | `[]` | array | — | Extra IPs allowed to use the dev front controller. | Core | [C] [code: app/middlewares/Dev/IpRestrictMiddleware.php:33-35 @7.x] |
| `trusted_hosts` | `[]` | array | coreconfig "Trusted hosts" | Host allow-list (`Request::setTrustedHosts`); domains or regexps. | Core | [C] [code: app/middlewares/TrustMiddleware.php:38-40 @7.x] [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:190-250 @7.x] |
| `trusted_proxies` | `[]` | array | coreconfig "Trusted proxies" | Proxy IPs/CIDRs; mandatory behind an SSL-terminating proxy. | Core | [C] [code: app/middlewares/TrustMiddleware.php:34-36 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#cors-settings] |
| `validate_remote_domains` | `false` | bool | — | Validate the domains of remote URLs (`SafeRemoteUrlValidator`). | Core | [C] |
| `allowed_remote_domains` | `[]` | array | coreconfig | Allow-list for remote URLs *(inferred)*. | Core | [C] |
| `rememberme_key` | `'%mautic.secret_key%'` | string | — | Remember-me secret. | Core | [C] [code: app/config/security.php:95 @7.x] |
| `rememberme_lifetime` | `7776000` (90 days) | int | — | Remember-me cookie lifetime in seconds (`int:` processor). | Core | [C] [code: app/config/security.php:96 @7.x] [code: app/config/parameters.php:30-33 @7.x] |
| `rememberme_path` | `'/'` | string | — | Remember-me cookie path. | Core | [C] [code: app/config/security.php:97 @7.x] |
| `rememberme_domain` | `''` | string | — | Remember-me cookie domain. | Core | [C] [code: app/config/security.php:98 @7.x] |
| `default_pagelimit` | `30` | int | coreconfig "Default item limit per page" (choices 5–100) | Default list page size. The docs say 10. | Core | [C] [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:305-329 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#system-defaults] |
| `default_timezone` | `'UTC'` | string | coreconfig "Default timezone" | PHP timezone for sessions without a User timezone. | Core | [C] [code: app/bundles/CoreBundle/Helper/CoreParametersHelper.php:72-79 @7.x] |
| `date_format_full` | `'F j, Y g:i a T'` | string | coreconfig "Default format for full dates" | PHP date format. | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#system-defaults] |
| `date_format_short` | `'D, M d'` | string | coreconfig "short dates" | PHP date format. | Core | [C] |
| `date_format_dateonly` | `'F j, Y'` | string | coreconfig "date only" | PHP date format. | Core | [C] |
| `date_format_timeonly` | `'g:i a'` | string | coreconfig "time only" | PHP date format. | Core | [C] |
| `ip_lookup_service` | `'maxmind_download'` | string | coreconfig "IP lookup service" | Key into the `ip_lookup_services` registry (12 built-in services). | Core | [C] [code: app/config/config.php:26 @7.x] |
| `ip_lookup_auth` | `''` | string | coreconfig "IP lookup service authentication" | Credentials; MaxMind format `AccountID:Licensekey`. | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/maxmind_license.html] |
| `ip_lookup_config` | `[]` | array | coreconfig | Per-service configuration. | Core | [C] |
| `ip_lookup_create_organization` | `false` | bool | coreconfig | Create a Company from the IP lookup organisation *(inferred)*. | Core | [C] |
| `transifex_api_token` | `''` | string | — | Transifex token for translation commands *(inferred)*. | Core | [C] |
| `update_stability` | `'stable'` | string | coreconfig "Minimum stability level" (alpha/beta/rc/stable) | Release channel for update notifications. | Core | [C] [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:550-557 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#update-settings] |
| `cookie_path` | `'/'` | string | — | Tracking cookie path (`CookieHelper`). | Core | [C] |
| `cookie_domain` | `''` | string | — | Tracking cookie domain. | Core | [C] |
| `cookie_secure` | `true` | bool | — | Tracking cookie Secure flag. | Core | [C] |
| `cookie_httponly` | `false` | bool | — | Tracking cookie HttpOnly flag. | Core | [C] |
| `do_not_track_ips` | `[]` | array | coreconfig "List of IPs not to track Contacts with" | IPs excluded from tracking. | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#miscellaneous-settings] |
| `do_not_track_bots` | long UA list (`config.php:302-692`) | array | coreconfig "List of known Bots" | User-agent substrings excluded from tracking. | Core | [C] |
| `do_not_track_internal_ips` | `[]` | array | — | Proxy IPs removed from `X-Forwarded-For` chains *(inferred)*. | Core | [C] |
| `track_private_ip_ranges` | `false` | bool | — | Treat RFC1918 IPs as valid *(inferred)*. | Core | [C] |
| `link_shortener_url` | `null` | null | — | Legacy shortener URL *(inferred)*. | Core | [C] |
| `shortener_email_enable` | `false` | bool | coreconfig | Shorten links in Emails *(inferred)*. | Core | [C] |
| `shortener_sms_enable` | `true` | bool | coreconfig | Shorten links in SMS *(inferred)*. | Core | [C] |
| `shortener_service` | `null` | null | coreconfig "Shortener Service" | Selected shortener service (Plugin-provided). | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/shortener.html] |
| `cached_data_timeout` | `10` | int | coreconfig "Cached data timeout (minutes)" | TTL of cached stats. | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#system-defaults] |
| `batch_sleep_time` | `1` | int | — | Sleep between command batches (0 in tests). | Core | [C] [code: app/config/config_test.php:131 @7.x] |
| `batch_campaign_sleep_time` | `false` | bool | — | Campaign batch sleep *(inferred)*. | Core | [C] |
| `transliterate_page_title` | `false` | bool | coreconfig "Translate page titles" | Transliterate non-Latin page titles in activity history. | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#miscellaneous-settings] |
| `cors_restrict_domains` | `true` | bool | coreconfig "Restrict Domains" | Only `cors_valid_domains` receive CORS headers. The docs say the default is No. | Core | [C] [code: app/middlewares/CORSMiddleware.php:50 @7.x] |
| `cors_valid_domains` | `[]` | array | coreconfig "Valid Domains" | Exact or `fnmatch`-wildcard origins. | Core | [C] [code: app/middlewares/CORSMiddleware.php:99-119 @7.x] |
| `headers_sts` | `false` | bool | coreconfig | Emit `Strict-Transport-Security`. | Core | [C] [code: app/middlewares/HSTSMiddleware.php:31 @7.x] |
| `headers_sts_expire_time` | `60` | int | coreconfig | HSTS max-age seconds. | Core | [C] [code: app/middlewares/HSTSMiddleware.php:34 @7.x] |
| `headers_sts_subdomains` | `false` | bool | coreconfig | HSTS `includeSubDomains`. | Core | [C] [code: app/middlewares/HSTSMiddleware.php:32 @7.x] |
| `headers_sts_preload` | `false` | bool | coreconfig | HSTS `preload`. | Core | [C] [code: app/middlewares/HSTSMiddleware.php:33 @7.x] |
| `max_entity_lock_time` | `0` | int | coreconfig "Item max lock time" | Edit-lock expiry (0 seconds by default). | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#miscellaneous-settings] |
| `default_daterange_filter` | `'-1 month'` | string | coreconfig "Date Range Filter Default" | Default range for Reports and snapshot charts. | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#system-defaults] |
| `debug` | `false` | bool | — | Mautic log level Debug instead of Notice. | Core | [C] [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:17-18 @7.x] |
| `anonymize_ip_address_in_background` | `false` | bool | — | When false, turning on `anonymize_ip` anonymises stored IPs synchronously. | Core | [C] [code: app/bundles/ConfigBundle/EventListener/ConfigSubscriber.php:46-49 @7.x] |
| `rss_notification_url` | `''` | string | — | RSS feed for in-app notifications. | Core | [C] |
| `motd_url` | `'https://mautic.github.io/motd/motd.json'` | string | — | Message-of-the-day source (`mautic:motd`). | Core | [C] |
| `motd_cache_path` | `'%mautic.cache_path%/motd.json'` | string | — | MOTD cache file. | Core | [C] |
| `motd_cache_ttl` | `3600` | int | — | MOTD cache TTL. | Core | [C] |
| `translations_list_url` | `'https://language-packs.mautic.com/manifest.json'` | string | — | Language pack manifest. | Core | [C] |
| `translations_fetch_url` | `'https://language-packs.mautic.com/'` | string | — | Language pack download base. | Core | [C] |
| `stats_update_url` | `'https://updates.mautic.org/stats/send'` | string | — | Anonymous stats endpoint; empty disables. | Core | [C] |
| `install_source` | `'Mautic'` | string | — | Reported in stats (DDEV sets `DDEV`). | Core | [C] [code: .ddev/local.config.php.dist:14 @7.x] |
| `system_update_url` | `'https://api.github.com/repos/mautic/mautic/releases'` | string | — | Release feed for update checks. | Core | [C] |
| `editor_fonts` | 19–20 font entries (`config.php:721-806`) | array | — | Fonts offered in builders; entries with `url` are injected as stylesheets. | Core | [C] |
| `composer_updates` | `false` | bool | coreconfig "Update Mautic through Composer [beta]" | Composer-managed install; prerequisite for Marketplace installs; `mautic:update:apply` refuses when true. | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#update-settings] |
| `redis_primary_only` | `false` | bool | — | Redis replication strategy *(inferred)*. | Core | [C] |
| `gdpr_user_purge_threshold` | `1095` | int | — | Days of inactivity before `mautic:maintenance:cleanup --gdpr` purges. | Core | [C] |
| `support_mautic_enabled` | `true` | bool | — | Show the "Support Mautic" menu item; set false in local.php to hide it. | Core | [C] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#support-mautic-menu-item] |
| `local_root` | detected webroot | string | — | Webroot detected from composer `extra`; added to the defaults at runtime. | Core | [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:147-156 @7.x] |

## 3. ConfigBundle
| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `config_allowed_parameters` | `['kernel.project_dir','kernel.logs_dir']` | array | — | Container placeholders that survive escaping on save. | Config | [code: app/bundles/ConfigBundle/Config/config.php:54-59 @7.x] [code: app/bundles/ConfigBundle/Form/Type/EscapeTransformer.php:82-92 @7.x] |

## 4. ApiBundle
Declared in `app/bundles/ApiBundle/Config/config.php:54-67`. Behaviour is covered in mautic-rest-api.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `api_enabled` | `false` | bool | apiconfig "API enabled" | Enable the REST API. | Api | [code: app/bundles/ApiBundle/Config/config.php:54-67 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#api-settings] |
| `api_enable_basic_auth` | `false` | bool | apiconfig "Enable http basic auth?" | HTTP basic auth for the API (cast to bool on save). | Api | [code: app/bundles/ApiBundle/EventListener/ConfigSubscriber.php:36-38 @7.x] |
| `api_oauth2_access_token_lifetime` | `60` (minutes) | int | apiconfig "Access token lifetime" | Exposed to the container in seconds (×60). | Api | [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:14 @7.x] [code: app/config/security_api.php:13 @7.x] |
| `api_oauth2_refresh_token_lifetime` | `14` (days) | int | apiconfig "Refresh token lifetime" | Exposed in seconds (×86400). | Api | [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:17 @7.x] [code: app/config/security_api.php:14 @7.x] |
| `api_batch_max_limit` | `200` | int | — | Max entities per batch API call *(inferred)*. | Api | [code: app/bundles/ApiBundle/Config/config.php:54-67 @7.x] |

## 5. AssetBundle
| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `upload_dir` | `'%mautic.application_dir%/media/files'` | string | assetconfig "Path to the Asset directory" | Asset storage dir; the docs advise keeping it outside the web root. | Asset | [code: app/bundles/AssetBundle/Config/config.php:60-63 @7.x] [code: app/config/config.php:260 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#asset-settings] |
| `max_size` | `'6'` | string | assetconfig "Maximum size Megabytes" | Max upload size in MB. | Asset | [code: app/bundles/AssetBundle/Config/config.php:60-63 @7.x] |
| `allowed_extensions` | 23 extensions | array | assetconfig "Allowed file extensions" | Upload extension allow-list. | Asset | [code: app/bundles/AssetBundle/Config/config.php:60-63 @7.x] |
| `streamed_extensions` | `gif,jpg,jpeg,mpg,mpeg,mp3,pdf,png,wav` | array | — | Extensions served inline *(inferred)*. | Asset | [code: app/bundles/AssetBundle/Config/config.php:60-63 @7.x] |

## 6. CacheBundle
Declared in `app/bundles/CacheBundle/Config/config.php:13-37`. There is no UI tab.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `cache_adapter` | `'mautic.cache.adapter.filesystem'` | string | — | App cache adapter service id. The alternatives are memcached, redis and redis_tag_aware. In 8.x the value is a class name. | Cache | [code: app/bundles/CacheBundle/Config/services.php:20-45 @7.x] [code: UPGRADE-8.0.md:177 @8.x] |
| `cache_adapter_tag_aware` | `'mautic.cache.adapter.filesystem'` | string | — | Tag-aware adapter service id. | Cache | [code: app/bundles/CacheBundle/Config/config.php:13-37 @7.x] |
| `cache_prefix` | `''` | string | — | Cache key prefix. | Cache | same |
| `cache_lifetime` | `86400` | int | — | Default TTL in seconds. | Cache | same |
| `cache_adapter_memcached` | `{servers:['memcached://localhost'], options:{compression:true, libketama_compatible:true, serializer:'igbinary'}}` | array | — | Memcached adapter arguments. | Cache | [code: app/bundles/CacheBundle/Config/services.php:27 @7.x] |
| `cache_adapter_redis` | `{dsn:'redis://localhost', options:{lazy:false, persistent:0, persistent_id:null, timeout:30, read_timeout:0, retry_interval:0}}` | array | — | Redis adapter arguments. | Cache | [code: app/bundles/CacheBundle/Config/config.php:13-37 @7.x] |

## 7. CampaignBundle
Declared in `app/bundles/CampaignBundle/Config/config.php:161-178` = **[CA]**. Behaviour is covered in mautic-campaigns.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `campaign_time_wait_on_event_false` | `'PT1H'` | string | campaignconfig "Wait time before retrying a failed action" | Interval used for negative-path and retry waits; htmlspecialchars on save. | Campaign | [CA] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#campaign-settings] |
| `campaign_use_summary` | `0` | int | campaignconfig "Use summary statistics" | Use summarised stats; backfill needed on first enable. | Campaign | [CA] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#campaign-settings] |
| `campaign_by_range` | `0` | int | campaignconfig "Use date range for all views" | Apply the date range to Campaign tabs. | Campaign | [CA] |
| `delete_campaign_event_log_in_background` | `false` | bool | — | Defer event-log deletion *(inferred)*. | Campaign | [CA] |
| `campaign_email_stats_enabled` | `true` | bool | campaignconfig | Show Email stats in Campaigns *(inferred)*. | Campaign | [CA] |
| `peak_interaction_timer_cache_timeout` | `43800` | int | campaignconfig "Interaction Data Cache Timeout" | Optimal-time scheduler cache. | Campaign | [CA] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#optimal-for-contact-event-scheduler] |
| `peak_interaction_timer_best_default_hour_start` | `9` | int | campaignconfig "Default Optimal Start Hour" | Fallback window start. | Campaign | [CA] |
| `peak_interaction_timer_best_default_hour_end` | `12` | int | campaignconfig "Default Optimal End Hour" | Fallback window end. | Campaign | [CA] |
| `peak_interaction_timer_best_default_days` | `[2,1,4]` | array | campaignconfig "Default Optimal Days" | Fallback days. | Campaign | [CA] |
| `peak_interaction_timer_fetch_interactions_from` | `'-60 days'` | string | campaignconfig "Fetch Interactions From" | Lookback window. | Campaign | [CA] |
| `peak_interaction_timer_fetch_limit` | `50` | int | campaignconfig "Interaction Fetch Limit" | Per-type fetch limit. | Campaign | [CA] |
| `peak_interaction_timer_max_optimal_days` | `3` | int | — | Max optimal days *(inferred)*. | Campaign | [CA] |
| `import_campaigns_dir` | `'%kernel.project_dir%/var/import'` | string | — | Campaign import dir. | Campaign | [CA] |
| `campaigns_resume_stuck_records_after` | `'2025-10-01 00:00:00'` | string | — | Cut-off for resume-stuck processing *(inferred)*. | Campaign | [CA] |
| `campaign_republish_behavior` | `'count_all_time'` | string | campaignconfig "Campaign Reactivation Behavior" | Default delay counting after reactivation. | Campaign | [CA] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#campaign-settings] |
| `campaign_event_cache_ttl` | `600` | int | — (local.php only) | Event stats cache seconds; 0 disables. | Campaign | [CA] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#advanced-campaign-performance-settings] |
| `campaign_contact_count_cache_ttl` | `43200` | int | — (local.php only) | Contact-count cache seconds. | Campaign | [CA] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#advanced-campaign-performance-settings] |
| `marketplace_website_url` | `'%env(default::MARKETPLACE_WEBSITE_URL)%'` | string | — | Duplicate of the MarketplaceBundle key with a different default. | Campaign | [code: app/bundles/CampaignBundle/Config/config.php:178 @7.x] |

## 8. DashboardBundle
| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `dashboard_import_dir` | `'%mautic.application_dir%/app/assets/dashboards'` | string | — | Global dashboard import dir. | Dashboard | [code: app/bundles/DashboardBundle/Config/config.php:45-46 @7.x] |
| `dashboard_import_user_dir` | `'%mautic.application_dir%/media/dashboards'` | string | — | Per-user dashboard dir. | Dashboard | same |

## 9. EmailBundle
Declared in `app/bundles/EmailBundle/Config/config.php:137-224` = **[E]**. Behaviour is covered in mautic-emails.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `mailer_from_name` | `'Mautic'` | string | emailconfig "Name to send mail as" | Default sender name (tokens allowed). | Email | [E] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mail-send-settings] |
| `mailer_from_email` | `'email@yoursite.com'` | string | emailconfig "Email address to send mail from" | Default sender address. | Email | [E] |
| `mailer_reply_to_email` | `null` | null | emailconfig "Reply to address" | Default Reply-To; blank uses From. | Email | [E] |
| `mailer_return_path` | `null` | null | emailconfig "Custom return path (bounce) address" | Return-Path. | Email | [E] |
| `mailer_address_length_limit` | `320` | int | emailconfig "Email address length limit" | Above the limit, the display name is dropped. | Email | [E] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mail-send-settings] |
| `mailer_append_tracking_pixel` | `true` | bool | emailconfig "Append tracking pixel into Email body?" | Open tracking. | Email | [E] |
| `mailer_convert_embed_images` | `false` | bool | emailconfig "Convert embed images to Base64" | Base64 images. | Email | [E] |
| `mailer_custom_headers` | `[]` | array | emailconfig | Default custom headers. | Email | [E] |
| `mailer_dsn` | `'smtp://localhost:1025'` | string | emailconfig DSN fields + test button | Symfony Mailer `main` transport (`urlencoded-dsn`). | Email | [E] [code: app/config/config.php:97-101 @7.x] |
| `unsubscribe_text` | `null` | null | emailconfig "Text for the {unsubscribe_text} token" | Default text. | Email | [E] |
| `webview_text` | `null` | null | emailconfig "Text for the {webview_text} token" | Default text. | Email | [E] |
| `unsubscribe_message` | `null` | null | emailconfig "Unsubscribed confirmation message" | Default text. | Email | [E] |
| `resubscribe_message` | `null` | null | emailconfig "Resubscribed confirmation message" | Default text. | Email | [E] |
| `email_default_preference_center_id` | `null` | null | emailconfig "Default Preference Center Landing Page" | Resolved at unsubscribe time. | Email | [E] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#unsubscribe-settings] |
| `email_default_utm_source` / `_medium` / `_campaign` / `_content` | `null` | null | emailconfig "Default UTM ..." | Pre-fill new Emails only. | Email | [E] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#message-settings] |
| `monitored_email` | nested `general`, `EmailBundle_bounces`, `EmailBundle_unsubscribes`, `EmailBundle_replies` | array | emailconfig "Monitored inbox" | IMAP mailboxes; passwords preserved and incomplete entries reset on save. | Email | [E] [code: app/bundles/EmailBundle/EventListener/ConfigSubscriber.php:43-62 @7.x] |
| `mailer_is_owner` | `false` | bool | emailconfig "Mailer is owner" | Send as the Contact owner; excluded from the audit log. | Email | [E] [code: app/bundles/ConfigBundle/Service/ConfigChangeLogger.php:21 @7.x] |
| `disable_unsubscribe_link_header` | `false` | bool | emailconfig "Disable unsubscribe link in header" | Suppress RFC 8058 List-Unsubscribe headers. | Email | [E] |
| `default_signature_text` | `null` | null | emailconfig "Default Email signature" | Signature. | Email | [E] |
| `email_frequency_number` | `0` | int | emailconfig "Do Not Contact more than" | Global frequency rule count. | Email | [E] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#default-frequency-rule] |
| `email_frequency_time` | `'DAY'` | string | emailconfig "each" | Frequency period. | Email | [E] |
| `show_contact_preferences` / `_frequency` / `_pause_dates` / `_preferred_channels` / `_categories` / `_segments` | `false` | bool | emailconfig "Show Contact preference settings" etc. | Preference Center toggles. | Email | [E] |
| `validate_unsubscribe_emails` | `true` | bool | emailconfig ("Require email validation for unsubscribe", 8.0 docs) | Unsubscribe confirmation page. 7.x after 7.2.1, unreleased [PR #16870]. | Email | [E] [docs: https://docs.mautic.org/en/8.0/configuration/settings.html#unsubscribe-settings] |
| `disable_trackable_urls` | `false` | bool | emailconfig "Disable trackable URLs" | Click tracking off. | Email | [E] |
| `email_draft_enabled` | `false` | bool | emailconfig | Email drafts *(inferred)*. | Email | [E] |
| `theme_email_default` | `'blank'` | string | — | Default Email theme. | Email | [E] |
| `mailer_memory_msg_limit` | `100` | int | — | Messages held in memory *(inferred)*. | Email | [E] |
| `minify_email_html` | `false` | bool | emailconfig | Minify Email HTML. | Email | [E] |
| `bot_helper_bot_ratio_threshold` | `0.6` | float | — | Bot detection ratio *(inferred)*. | Email | [E] |
| `bot_helper_time_email_threshold` | `2` | int | — | Bot detection time threshold *(inferred)*. | Email | [E] |
| `bot_helper_blocked_user_agents` | 2 sample UAs | array | — | Blocked user agents. | Email | [E] |
| `bot_helper_blocked_ip_addresses` | `[]` | array | — | Blocked IPs. | Email | [E] |
| `smime_signing_enabled` | `false` | bool | — (local.php only) | S/MIME signing (SMTP only; disables batch sending). | Email | [E] [docs: https://docs.mautic.org/en/7.2/configuration/smime_email_signing.html#configuration-parameters] |
| `smime_certificates_path` | `'%kernel.project_dir%/var/smime_certificates'` | string | — | Certificate dir. | Email | [E] |

## 10. FormBundle
Declared in `app/bundles/FormBundle/Config/config.php:143-149` = **[F]**.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `form_upload_dir` | `'%mautic.application_dir%/media/files/form'` | string | — | Form file-field uploads. | Form | [F] |
| `blacklisted_extensions` | `['php','sh']` | array | — | Blocked upload extensions. | Form | [F] |
| `do_not_submit_emails` | `[]` | array | formconfig "Do not accept submission from these domain names" | Domain blocklist (wildcards). | Form | [F] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#form-settings] |
| `blocked_free_email_providers` | large list | array | formconfig | Free-provider blocklist. | Form | [F] |
| `form_results_data_sources` | `false` | bool | formconfig | *(inferred)* | Form | [F] |
| `successful_submit_action` | `'top'` | string | formconfig | Where the success message shows *(inferred)*. | Form | [F] |
| `form_field_autofill` | `false` | bool | formconfig "Enable form field auto-fill from contact data" | Global auto-fill gate. | Form | [F] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#form-settings] |

## 11. LeadBundle
Declared in `app/bundles/LeadBundle/Config/config.php:336-374` = **[L]**. Behaviour is covered in mautic-contacts and mautic-segments.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `parallel_import_limit` | `1` | int | — | Parallel imports. | Lead | [L] |
| `background_import_if_more_rows_than` | `0` | int | leadconfig "Automatically import in background if CSV has more rows than" | 0 = always in the background. | Lead | [L] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#import-settings] |
| `contact_api_count_cache_ttl` | `5` | int | — | API count cache in seconds; null disables. | Lead | [L] |
| `delete_segment_in_background` | `false` | bool | — | Defer Segment deletion. | Lead | [L] |
| `segment_api_count_cache_ttl` | `43200` | int | — | Segment API count cache. | Lead | [L] |
| `contact_columns` | `['name','email','location','stage','points','last_active','id']` | array | leadconfig "Columns" | Contact list columns. | Lead | [L] |
| `company_columns` | `['companyname','companyemail','companywebsite','score','leadcount','id']` | array | companyconfig "Columns" | Company list columns. | Lead | [L] |
| `create_custom_field_in_background` | `false` | bool | — | Defer custom-field DDL to `mautic:custom-field:*`. | Lead | [L] [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#mautic-commands] |
| `company_unique_identifiers_operator` | `'OR'` | string | companyconfig "Merge by unique fields with operator" | AND/OR across unique identifiers. | Lead | [L] |
| `contact_unique_identifiers_operator` | `'OR'` | string | leadconfig "Merge by unique fields with operator" | AND/OR across unique identifiers. | Lead | [L] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#contact-merge-settings] |
| `segment_rebuild_time_warning` | `30` | int | segment_config "Show warning if Segment hasn't been rebuilt for X hours" | Stale-Segment warning. | Lead | [L] |
| `segment_build_time_warning` | `30` | int | segment_config | Build-time warning *(inferred)*. | Lead | [L] |
| `contact_export_in_background` | `true` | bool | leadconfig "Automatically export Contacts to CSV in the background" | Background export. | Lead | [L] |
| `contact_export_notify_admins` | `true` | bool | leadconfig "Notify admins about contact exports" | Admin notifications. | Lead | [L] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#export-settings] |
| `contact_export_dir` | `'%mautic.application_dir%/media/files/temp'` | string | — | Export dir. | Lead | [L] |
| `contact_export_batch_size` | `20000` | int | — | Export batch size. | Lead | [L] |
| `contact_export_limit` | `0` | int | leadconfig | Export row limit *(inferred)*. | Lead | [L] |
| `contact_allow_multiple_companies` | `true` | bool | leadconfig "Enable Multiple Companies" | Several Companies per Contact. | Lead | [L] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#multiple-company-management] |
| `import_leads_dir` | `'%kernel.project_dir%/var/import'` | string | — | Import dir. | Lead | [L] |
| `update_segment_contact_count_in_background` | `false` | bool | — | Defer Segment counts. | Lead | [L] |
| `clear_export_files_after_days` | `7` | int | — | Export file retention. | Lead | [L] |
| `update_company_mapping_data_in_background` | `false` | bool | — | Defer Company mapping (`mautic:company:*`). | Lead | [L] [docs: https://docs.mautic.org/en/7.2/configuration/command_line_interface.html#mautic-commands] |

## 12. MarketplaceBundle
| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `marketplace_enabled` | `true` | bool | — | Marketplace on/off. | Marketplace | [code: app/bundles/MarketplaceBundle/Config/config.php:41 @7.x] |
| `marketplace_website_url` | `'https://marketplace.mautic.org'` | string | — | Website URL (also declared in CampaignBundle). | Marketplace | [code: app/bundles/MarketplaceBundle/Config/config.php:42 @7.x] |
| `marketplace_registry_url` | `'https://marketplace.mautic.org'` | string | — | Registry URL. | Marketplace | [code: app/bundles/MarketplaceBundle/Config/config.php:43 @7.x] |

## 13. MessengerBundle
Declared in `app/bundles/MessengerBundle/Config/config.php:7-13` = **[M]**. Behaviour is covered in mautic-cron-and-queues.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `messenger_dsn_email` | `'sync://'` | string | messengerconfig "Queue DSN" (email) | `email` transport; `sync://` means no queue. History: with `messenger_dsn_hit` and `messenger_dsn_failed` it replaced `messenger_dsn`/`messenger_type` in 5.0 [PR #12509]. | Messenger | [M] [code: app/config/config.php:105-110 @7.x] |
| `messenger_dsn_hit` | `'sync://'` | string | messengerconfig (hit) | `hit` transport. | Messenger | [M] [code: app/config/config.php:111-116 @7.x] |
| `messenger_dsn_failed` | `null` | null | messengerconfig "Queue for failures" | Failure transport; empty becomes `null://` (discard). | Messenger | [M] [code: app/bundles/MessengerBundle/DependencyInjection/EnvProcessor/MessengerNullableEnvVarProcessor.php:13 @7.x] |
| `messenger_retry_strategy_max_retries` | `3` | int | messengerconfig "Max retries" | 0 disables retries. | Messenger | [M] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#retry-strategy] |
| `messenger_retry_strategy_delay` | `1000` | int | messengerconfig "Delay" | Initial delay in ms. | Messenger | [M] |
| `messenger_retry_strategy_multiplier` | `2.0` | float | messengerconfig "Multiplier" | Backoff multiplier (≥1). | Messenger | [M] |
| `messenger_retry_strategy_max_delay` | `0` | int | messengerconfig "Max delay" | 0 = no limit. | Messenger | [M] |

## 14. NotificationBundle
Declared in `app/bundles/NotificationBundle/Config/config.php:113-124` = **[NO]**.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `notification_enabled` | `false` | bool | — | Web push; no UI since 7.0. | Notification | [NO] [code: UPGRADE-7.0.md:30 @7.x] |
| `notification_landing_page_enabled` | `true` | bool | — | Web push on Landing Pages. | Notification | [NO] |
| `notification_app_id` / `notification_rest_api_key` / `notification_safari_web_id` / `notification_subdomain_name` | `null` | null | — | OneSignal credentials. | Notification | [NO] |
| `gcm_sender_id` | `'482941778795'` | string | — | GCM sender id. | Notification | [NO] |
| `welcomenotification_enabled` | `true` | bool | — | Welcome notification. | Notification | [NO] |
| `campaign_send_notification_to_author` | `true` | bool | notification_config "Send notification to author" (Campaign) | Email the author on auto-deactivation. | Notification | [NO] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#notification-settings] |
| `campaign_notification_email_addresses` | `null` | null | notification_config | Extra recipients. | Notification | [NO] |
| `webhook_send_notification_to_author` | `true` | bool | notification_config "Send notification to author" (Webhook) | Email the author on auto-unpublish. | Notification | [NO] |
| `webhook_notification_email_addresses` | `null` | null | notification_config | Extra recipients. | Notification | [NO] |

## 15. PageBundle
Declared in `app/bundles/PageBundle/Config/config.php:94-106` = **[P]**. Behaviour is covered in mautic-pages-and-tracking.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `cat_in_page_url` | `false` | bool | pageconfig "Show Category in Page URL?" | Category slug in Landing Page URLs. | Page | [P] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#landing-page-settings] |
| `google_analytics` | `null` | null | pageconfig "Analytics script" | Raw script; htmlspecialchars on save. | Page | [P] [code: app/bundles/PageBundle/EventListener/ConfigSubscriber.php:70-72 @7.x] |
| `track_contact_by_ip` | `false` | bool | trackingconfig "Identify visitors by IP" | IP-based identification. | Page | [P] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mautic-tracking-settings] |
| `google_analytics_id` | `null` | null | trackingconfig "Google Analytics ID" | GA id. | Page | [P] |
| `google_analytics_trackingpage_enabled` / `_landingpage_enabled` / `_anonymize_ip` | `false` | bool | trackingconfig "Enabled on your tracking Landing Page" / "Mautic Landing Page" / "IP Anonymization" | GA placement. | Page | [P] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#google-analytics] |
| `facebook_pixel_id` | `null` | null | trackingconfig "Facebook Pixel ID" | Pixel id. | Page | [P] |
| `facebook_pixel_trackingpage_enabled` / `_landingpage_enabled` | `false` | bool | trackingconfig | Pixel placement. | Page | [P] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#facebook-pixel] |
| `do_not_track_404_anonymous` | `false` | bool | trackingconfig "Do Not Track 404 error for anonymous Contacts" | Skip 404 hits. | Page | [P] |
| `append_segment_id_tracking_url` | `false` | bool | trackingconfig "Append Segment IDs to Tracking URLs" | Segment ids in Email links. | Page | [P] |
| `validate_page_hit_required_data` | `false` | bool | — | Validate required hit data *(inferred)*. | Page | [P] |

## 16. ReportBundle
| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `report_temp_dir` | `'%mautic.application_dir%/media/files/temp'` | string | — | Temp dir for exports. | Report | [code: app/bundles/ReportBundle/Config/config.php:80-83 @7.x] |
| `report_export_batch_size` | `1000` | int | — | Export batch. | Report | same |
| `report_export_max_filesize_in_bytes` | `5000000` | int | — | Max export size. | Report | same |
| `csv_always_enclose` | `false` | bool | reportconfig "Always quote data in CSV export" | Quote every CSV field. | Report | same [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#report-settings] |

## 17. SmsBundle
| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `sms_enabled` | `false` | bool | — | SMS channel on. | Sms | [code: app/bundles/SmsBundle/Config/config.php:70-78 @7.x] |
| `sms_username` / `sms_password` / `sms_messaging_service_sid` | `null` | null | — | Legacy Twilio credentials (integration-managed). | Sms | same |
| `sms_frequency_number` | `0` | int | — | SMS frequency count. | Sms | same |
| `sms_frequency_time` | `'DAY'` | string | — | SMS frequency period. | Sms | same |
| `sms_transport` | `'mautic.sms.twilio.transport'` | string | smsconfig "Select default transport to use" | Transport service id. | Sms | same [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#text-message-settings] |
| `sms_disable_trackable_urls` | `false` | bool | smsconfig | Disable SMS link tracking. | Sms | same |

## 18. UserBundle
Declared in `app/bundles/UserBundle/Config/config.php:133-142` = **[U]**. Behaviour is covered in mautic-users-and-permissions.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `saml_idp_metadata` | `''` | string | userconfig "Identity provider metadata file" (file, base64) | Non-empty enables SAML; must be valid XML. | User | [U] [code: app/bundles/CoreBundle/Loader/EnvVars/SAMLEnvVars.php:31-32 @7.x] [code: app/bundles/UserBundle/EventListener/ConfigSubscriber.php:60-64 @7.x] |
| `saml_idp_entity_id` | `''` | string | userconfig (choice of 3) | SP entity id; falls back to `scheme://host` of site_url. | User | [U] [code: app/bundles/CoreBundle/Loader/EnvVars/SAMLEnvVars.php:11-29 @7.x] |
| `saml_idp_own_certificate` | `''` | string | userconfig "X.509 certificate" (file) | Must start with `-----BEGIN CERTIFICATE-----`. | User | [U] [code: app/bundles/UserBundle/EventListener/ConfigSubscriber.php:65-69 @7.x] |
| `saml_idp_own_private_key` | `''` | string | userconfig "Private key file" (file) | Encrypted or RSA key. | User | [U] [code: app/bundles/UserBundle/EventListener/ConfigSubscriber.php:70-86 @7.x] |
| `saml_idp_own_password` | `''` | string | userconfig "Private key encryption password" | Preserved if empty on save. | User | [U] [code: app/bundles/UserBundle/EventListener/ConfigSubscriber.php:48 @7.x] |
| `saml_idp_email_attribute` / `_username_attribute` / `_firstname_attribute` / `_lastname_attribute` | `''` | string | userconfig "Email / Username / First name / Last name attribute" | IdP attribute mapping. | User | [U] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#saml-sso-settings] |
| `saml_idp_default_role` | `''` | string | userconfig "Default Role for created Users" | Empty means SSO creates no Users. | User | [U] [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#turning-on-saml] |

## 19. WebhookBundle
Declared in `app/bundles/WebhookBundle/Config/config.php:45-61` = **[W]**. Meanings come from the inline comments.

| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `webhook_limit` | `10` | int | — | Entities per payload. | Webhook | [W] |
| `webhook_time_limit` | `600` | int | — | Seconds the processor may run. | Webhook | [W] |
| `webhook_log_max` | `1000` | int | — | Logs kept. | Webhook | [W] |
| `webhook_health_check_time` | `300` | int | — | Retry after unhealthy, seconds. | Webhook | [W] |
| `webhook_retry_delay` | `3600` | int | — | Retry failed queue entries after, seconds. | Webhook | [W] |
| `clean_webhook_logs_in_background` | `false` | bool | — | Defer log cleanup. | Webhook | [W] |
| `webhook_disable_limit` | `100` | int | — | Failures before unpublish. | Webhook | [W] |
| `webhook_timeout` | `15` | int | — | Intended cURL timeout (seconds); read into `WebhookModel` but never passed to the HTTP client, so it has no effect. | Webhook | [W] [code: app/bundles/WebhookBundle/Model/WebhookModel.php:729 @7.x] |
| `queue_mode` | `'immediate_process'` (alt `command_process`) | string | webhookconfig "Queue Mode" | Immediate vs queued (queued needs `mautic:webhooks:process`). | Webhook | [W] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#webhook-settings] |
| `events_orderby_dir` | `'ASC'` | string | webhookconfig "Order of the queued events" | Chronological or reverse. | Webhook | [W] |
| `webhook_email_details` | `true` | bool | webhookconfig | Include Email details *(inferred)*. | Webhook | [W] |
| `disable_auto_unpublish` | `false` | bool | — | Keep failing Webhooks published. | Webhook | [W] |
| `first_webhook_failure_notification_time` | `3600` | int | — | First failure notification delay. | Webhook | [W] |
| `webhook_failure_notification_interval` | `86400` | int | — | Notification interval. | Webhook | [W] |
| `webhook_allowed_private_addresses` | `[]` | array | webhookconfig | Private addresses allowed as targets. | Webhook | [W] |

## 20. Plugins
| Parameter | Default | Type | UI | Meaning | Bundle | Citation |
|---|---|---|---|---|---|---|
| `image_path_exclude` | `['flags','mejs']` | array | — | Folders hidden in the builder asset manager *(inferred)*. | GrapesJsBuilderBundle | [code: plugins/GrapesJsBuilderBundle/Config/config.php:44-45 @7.x] |
| `static_url` | `''` | string | — | *(inferred)* | GrapesJsBuilderBundle | same |
| `website_snapshot_url` | `'https://mautic.net/api/snapshot'` | string | — | Focus Item snapshot service. | MauticFocusBundle | [code: plugins/MauticFocusBundle/Config/config.php:66-67 @7.x] |
| `website_snapshot_key` | `''` | string | — | Snapshot key. | MauticFocusBundle | same |
| `twitter_handle_field` | `'twitter'` | string | social_config "Twitter Handle Field" (only when the plugin is published) | Contact field holding the Twitter handle. | MauticSocialBundle | [code: plugins/MauticSocialBundle/Config/config.php:92 @7.x] [code: plugins/MauticSocialBundle/EventListener/ConfigSubscriber.php:29-31 @7.x] |

These bundles declare no parameters: CategoryBundle, ChannelBundle, DynamicContentBundle, IntegrationsBundle, PluginBundle, PointBundle, ProjectBundle, StageBundle, StatsBundle, and all other plugins. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:169-183 @7.x]

## 21. Undeclared keys that are read or written
These keys have no typed default, no `mautic.<key>` container parameter and no env override.

| Key | Where | Meaning | Citation |
|---|---|---|---|
| `anonymize_ip` | trackingconfig "Anonymize IP" (form default false) | Stop storing full IPs; turning it on anonymises existing IPs. | [code: app/bundles/PageBundle/EventListener/ConfigSubscriber.php:42-64 @7.x] [code: app/bundles/ConfigBundle/EventListener/ConfigSubscriber.php:43-49 @7.x] |
| `accent` | themeconfig | Theme accent colour *(inferred)*. | [code: app/bundles/CoreBundle/EventListener/ConfigThemeSubscriber.php:21-38 @7.x] |
| `sysinfo_disabled` | local.php | Hides and denies `/s/sysinfo`. | [code: app/bundles/ConfigBundle/Controller/SysinfoController.php:23 @7.x] |
| `transifex_username`, `transifex_password` | local.php | Restricted in prod; the password is excluded from the audit log. | [code: app/config/security.php:195-197 @7.x] |
| `db_backup_tables`, `db_backup_prefix`, `admin_*` | local.php before CLI install | Inputs to `mautic:install`. | [code: app/bundles/InstallBundle/Command/InstallCommand.php:183-220 @7.x] |

## 22. Non-parameter container settings
| Setting | Default | Meaning | Citation |
|---|---|---|---|
| `mautic.security.restrictedConfigFields` | db_* + `secret_key` (+ transifex in prod) | Keys hidden from the UI. | [code: app/config/security.php:182-197 @7.x] |
| `mautic.security.restrictedConfigFields.displayMode` | `remove` | `remove` or `mask`. | [code: app/config/security.php:200 @7.x] |
| `mautic.security.disableUpdates` | `false` (`true` in test) | Disables the update check. | [code: app/config/security.php:207 @7.x] [code: app/config/config_test.php:129 @7.x] |
| `mautic.famework.csrf_protection` (sic) | `true` | CSRF protection flag. | [code: app/config/config.php:146 @7.x] |

## 23. Legacy keys still in docs
The legacy queue page documents `queue_protocol`, `rabbitmq_*` and `beanstalkd_*`. They are declared in no 7.2.1 `config.php`, and Messenger DSNs replace them. [docs: https://docs.mautic.org/en/7.2/queue/queue.html] [code: app/bundles/MessengerBundle/Config/config.php:7-13 @7.x]
