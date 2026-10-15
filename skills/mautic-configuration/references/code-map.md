# Configuration and installer: code map (Mautic 7.x)

All paths are relative to the repository root. Neither ConfigBundle nor InstallBundle declares Doctrine entities. Configuration is stored in the PHP file `config/local.php`. [code: app/bundles/CoreBundle/Configurator/Configurator.php:193-215 @7.x]

## Services and classes
| Class / service | Path | Responsibility |
|---|---|---|
| `ParameterLoader` (final) | `app/bundles/CoreBundle/Loader/ParameterLoader.php` | Loads defaults (`:169-183`) and local layers (`:186-222`). Also `getParameterBag()`, `getLocalParameterBag()`, `loadIntoEnvironment()` (`:67-110`), static `getLocalConfigFile()` (`:112-159`) and webroot detection (`:272-305`). [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:26-305 @7.x] |
| `EnvVars\*` (8 classes) | `app/bundles/CoreBundle/Loader/EnvVars/` | `ConfigEnvVars`, `ApiEnvVars`, `ElFinderEnvVars`, `MigrationsEnvVars`, `SAMLEnvVars`, `SessionEnvVars`, `SiteUrlEnvVars`, `TwigEnvVars`. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:73-82 @7.x] |
| `CoreParametersHelper` | `app/bundles/CoreBundle/Helper/CoreParametersHelper.php` | `get($name, $default)`, `all()`, `getDefaultTimezone()`. [code: app/bundles/CoreBundle/Helper/CoreParametersHelper.php:30-79 @7.x] |
| `Configurator` (`mautic.configurator`) | `app/bundles/CoreBundle/Configurator/Configurator.php` | `isFileWritable()`, `addStep()/getSteps()`, `mergeParameters()`, `render()`, `write()`, `read()`. [code: app/bundles/CoreBundle/Configurator/Configurator.php:50-283 @7.x] [code: app/bundles/CoreBundle/Config/services.php:163-164 @7.x] |
| `CacheHelper` | `app/bundles/CoreBundle/Helper/CacheHelper.php` | `refreshConfig()`, `nukeCache()`, `clearSymfonyCache()`. [code: app/bundles/CoreBundle/Helper/CacheHelper.php:26-85 @7.x] |
| Env processors | `app/bundles/CoreBundle/DependencyInjection/EnvProcessor/`; `EmailBundle/.../MailerDsnEnvVarProcessor.php`; `MessengerBundle/.../MessengerNullableEnvVarProcessor.php` | `nullable`, `intNullable`, `mauticconst`, `urlencoded-dsn`/`mailer`, `messenger-nullable`. [code: app/config/parameters.php:13-49 @7.x] |
| `ConfigMapper` | `app/bundles/ConfigBundle/Mapper/ConfigMapper.php` | Overlays resolved values onto the contributed form defaults. [code: app/bundles/ConfigBundle/Mapper/ConfigMapper.php:30-72 @7.x] |
| `Mapper\Helper\RestrictionHelper` | `app/bundles/ConfigBundle/Mapper/Helper/RestrictionHelper.php` | Normalises and applies restrictions to data. [code: app/bundles/ConfigBundle/Mapper/Helper/RestrictionHelper.php:10-54 @7.x] |
| `Form\Helper\RestrictionHelper` | `app/bundles/ConfigBundle/Form/Helper/RestrictionHelper.php` | Applies `MODE_REMOVE`/`MODE_MASK` to forms. [code: app/bundles/ConfigBundle/Form/Helper/RestrictionHelper.php:60-82 @7.x] |
| `EscapeTransformer` | `app/bundles/ConfigBundle/Form/Type/EscapeTransformer.php` | `%` ↔ `%%`. [code: app/bundles/ConfigBundle/Form/Type/EscapeTransformer.php:63-92 @7.x] |
| `DsnType`, `DsnTransformer` | `app/bundles/ConfigBundle/Form/Type/DsnType.php`, `Form/DataTransformer/` | DSN compound field and password mask. [code: app/bundles/ConfigBundle/Form/Type/DsnType.php:120-175 @7.x] |
| `ConfigType` (root form) | `app/bundles/ConfigBundle/Form/Type/ConfigType.php` | One child per tab; escape transformer; restriction pass; OAuth2 lifetime hack. [code: app/bundles/ConfigBundle/Form/Type/ConfigType.php:26-107 @7.x] |
| `ConfigChangeLogger` | `app/bundles/ConfigBundle/Service/ConfigChangeLogger.php` | Writes the audit-log diff. [code: app/bundles/ConfigBundle/Service/ConfigChangeLogger.php:48-82 @7.x] |
| `SysinfoModel` | `app/bundles/ConfigBundle/Model/SysinfoModel.php` | phpinfo, requirements, folders, log tail, DB info. [code: app/bundles/ConfigBundle/Model/SysinfoModel.php:40-141 @7.x] |
| `InstallService` (`mautic.install.service`) | `app/bundles/InstallBundle/Install/InstallService.php` | Step constants 0–3 and the per-step methods. [code: app/bundles/InstallBundle/Install/InstallService.php:41-547 @7.x] |
| `SchemaHelper` | `app/bundles/InstallBundle/Helper/SchemaHelper.php` | Connection test, DB creation, schema install, version check, table backup. [code: app/bundles/InstallBundle/Helper/SchemaHelper.php:70-312 @7.x] |
| `CheckStep`, `DoctrineStep`, `UserStep` | `app/bundles/InstallBundle/Configurator/Step/` | `StepInterface` implementations (priorities 0/1/2). [code: app/bundles/InstallBundle/Config/services.php:31-36 @7.x] |
| `InstallCommandPass` | `app/bundles/InstallBundle/DependencyInjection/Compiler/InstallCommandPass.php` | Injects `--db_table_prefix`. [code: app/bundles/InstallBundle/DependencyInjection/Compiler/InstallCommandPass.php:16-34 @7.x] |
| `DoctrineEventSubscriber` | `app/bundles/InstallBundle/EventListener/DoctrineEventSubscriber.php` | Adds core field columns and indexes. [code: app/bundles/InstallBundle/EventListener/DoctrineEventSubscriber.php:11-52 @7.x] |
| Install fixtures | `app/bundles/InstallBundle/InstallFixtures/ORM/{RoleData,LeadFieldData,LoadReportData}.php` | Group `group_install`. [code: app/bundles/InstallBundle/Install/InstallService.php:393-411 @7.x] |
| Middlewares | `app/middlewares/*.php` | CORS 1000, HSTS 900, CatchException 100, IpRestrict (dev) 20, VersionCheck 10, Trust 0; config via `ConfigAwareTrait`. [code: app/middlewares/ConfigAwareTrait.php:17-45 @7.x] |

## Events (7.x)
| Constant | Name | Event class | Dispatched |
|---|---|---|---|
| `ConfigEvents::CONFIG_ON_GENERATE` | `mautic.config_on_generate` | `ConfigBuilderEvent` | edit, download and remove actions [code: app/bundles/ConfigBundle/Controller/ConfigController.php:45-46 @7.x] |
| `ConfigEvents::CONFIG_PRE_SAVE` | `mautic.config_pre_save` | `ConfigEvent` | after validation, before write [code: app/bundles/ConfigBundle/Controller/ConfigController.php:104 @7.x] |
| `ConfigEvents::CONFIG_POST_SAVE` | `mautic.config_post_save` | `ConfigEvent` | after `Configurator::write()` [code: app/bundles/ConfigBundle/Controller/ConfigController.php:150 @7.x] |

The `ConfigEvents.php:16` docblock names a non-existent `ConfigGenerateEvent`. [code: app/bundles/ConfigBundle/ConfigEvents.php:16 @7.x]

`ConfigBuilderEvent` API: `addForm()`, `removeForm()`, `getForms()`, `getFormThemes()`, `getParametersFromConfig($bundle)`, `addFileFields()`, `getFileFields()`. [code: app/bundles/ConfigBundle/Event/ConfigBuilderEvent.php:20-111 @7.x]

`ConfigEvent` API: `getConfig($key)`, `setConfig($array, $key)`, `getPost()`, `unsetIfEmpty($fields)`, `setError($msg, $vars, $key, $field)`, `getFileContent(UploadedFile)`, `encodeFileContents()`, `get/setOriginalNormData`, `get/setNormData`. [code: app/bundles/ConfigBundle/Event/ConfigEvent.php:88-159 @7.x]

## Tab contributors (CONFIG_ON_GENERATE listeners, priority 0)
| formAlias | Listener | Parameters |
|---|---|---|
| `coreconfig` | `app/bundles/CoreBundle/EventListener/ConfigSubscriber.php:27-40` | Core params minus theme keys and `gravatar_enabled` |
| `themeconfig` | `app/bundles/CoreBundle/EventListener/ConfigThemeSubscriber.php:21-38` | `theme`, `theme_import_allowed_extensions`, `brand_name`, `primary_brand_color`, `rounded_corners` |
| `privacyconfig` | `app/bundles/CoreBundle/EventListener/ConfigPrivacySubscriber.php:21-34` | `gravatar_enabled` |
| `apiconfig` | `app/bundles/ApiBundle/EventListener/ConfigSubscriber.php:21-30` | ApiBundle |
| `assetconfig` | `app/bundles/AssetBundle/EventListener/ConfigSubscriber.php:21-30` | AssetBundle |
| `campaignconfig` | `app/bundles/CampaignBundle/EventListener/ConfigSubscriber.php:21-32` | CampaignBundle |
| `emailconfig` | `app/bundles/EmailBundle/EventListener/ConfigSubscriber.php:27-36` | EmailBundle |
| `formconfig` | `app/bundles/FormBundle/EventListener/ConfigSubscriber.php:21-30` | FormBundle |
| `leadconfig`, `segment_config`, `companyconfig` | `app/bundles/LeadBundle/EventListener/ConfigSubscriber.php:27-72` | LeadBundle, split |
| `messengerconfig` | `app/bundles/MessengerBundle/EventListener/ConfigSubscriber.php:21-30` | MessengerBundle |
| `notification_config` | `app/bundles/NotificationBundle/EventListener/ConfigSubscriber.php:21-30` | NotificationBundle |
| `pageconfig`, `trackingconfig` | `app/bundles/PageBundle/EventListener/ConfigSubscriber.php:25-64` | Literal lists, incl. undeclared `anonymize_ip` |
| `reportconfig` | `app/bundles/ReportBundle/EventListener/ConfigSubscriber.php:21-30` | ReportBundle |
| `smsconfig` | `app/bundles/SmsBundle/EventListener/ConfigSubscriber.php:21-30` | SmsBundle |
| `userconfig` | `app/bundles/UserBundle/EventListener/ConfigSubscriber.php:31-43` | UserBundle; file fields `saml_idp_metadata`, `saml_idp_own_certificate`, `saml_idp_own_private_key` |
| `webhookconfig` | `app/bundles/WebhookBundle/EventListener/ConfigSubscriber.php:21-30` | WebhookBundle |
| `social_config` | `plugins/MauticSocialBundle/EventListener/ConfigSubscriber.php:27-40` | Only when the plugin is published |

[code: app/bundles/ConfigBundle/Controller/ConfigController.php:45-55 @7.x]

CacheBundle, ConfigBundle, DashboardBundle, MarketplaceBundle, GrapesJsBuilderBundle and MauticFocusBundle declare parameters but have no tab. IntegrationsBundle's config screen is a separate system. [code: app/bundles/IntegrationsBundle/IntegrationEvents.php:52 @7.x]

## Routes
| Name | Path | Controller |
|---|---|---|
| `mautic_config_edit` | `/s/config/edit/{activeTabId}` | `ConfigController::editAction` |
| `mautic_config_action` | `/s/config/{objectAction}/{objectId}` | `downloadAction`, `removeAction` |
| `mautic_sysinfo_index` | `/s/sysinfo` | `SysinfoController::indexAction` |
| `mautic_installer_home` | `/installer` | `InstallController::stepAction` |
| `mautic_installer_step` | `/installer/step/{index}` | `InstallController::stepAction` (float index) |
| `mautic_installer_final` | `/installer/final` | `InstallController::finalAction` |
| `mautic_installer_catchcall` | `/installer/{noerror}` | `InstallController::stepAction` |

[code: app/bundles/ConfigBundle/Config/config.php:6-25 @7.x] [code: app/bundles/InstallBundle/Config/config.php:6-33 @7.x]

Admin menu entries: `mautic.config.menu.index` and `mautic.sysinfo.menu.index`, both admin-only. Sysinfo is hidden when `sysinfo_disabled` is set. [code: app/bundles/ConfigBundle/Config/config.php:27-52 @7.x]

## Commands
| Command | Notes |
|---|---|
| `mautic:install <site_url> [step]` | Options: `--force/-f`, `--db_driver`, `--db_host`, `--db_port`, `--db_name`, `--db_user`, `--db_password`, `--db_table_prefix`, `--db_backup_tables`, `--db_backup_prefix`, `--admin_firstname`, `--admin_lastname`, `--admin_username`, `--admin_email`, `--admin_password`. Step: 0 check, 1 database (1.1 schema, 1.2 fixtures), 2 admin, 3 final. [code: app/bundles/InstallBundle/Command/InstallCommand.php:52-147 @7.x] |
| `mautic:install:data [--force]` | Drops the schema, recreates it and loads sample data. [code: app/bundles/CoreBundle/Command/InstallDataCommand.php:6-90 @7.x] |
| `mautic:cache:clear` | Clears the Mautic cache adapter only. [code: app/bundles/CacheBundle/Command/ClearCacheCommand.php:7-22 @7.x] |
| `cache:clear` (Symfony) | Rebuilds the container; needed for compile-time settings. [code: app/bundles/CoreBundle/Helper/CacheHelper.php:47-62 @7.x] |

There is no `mautic:config:*` command and no API for the Configuration UI. [code: app/bundles/ConfigBundle/Config/config.php:6-25 @7.x]

## Files and env vars
| File / var | Role |
|---|---|
| `config/local.php` | Main writable config (`$parameters`). [code: app/config/paths.php:11 @7.x] |
| `app/config/local.php` | Legacy location, used when the new one is absent. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:134-137 @7.x] |
| `config/parameters_local.php` | Forced overrides above local.php. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:201-209 @7.x] |
| `config/security_local.php`, `config_override.php`, `config_local.php`, `bundles_local.php`, `paths_local.php` | Optional overrides. [code: app/config/config_prod.php:10-14 @7.x] [code: app/config/config_prod.php:77-85 @7.x] [code: app/AppKernel.php:199-202 @7.x] [code: app/config/paths.php:28-32 @7.x] |
| `.env`, `.env.local`, `.env.local.php`, `.env.test` | `APP_ENV`, `APP_DEBUG`, test DB vars. [code: app/config/bootstrap.php:14-21 @7.x] [code: .env:15-16 @7.x] |
| `MAUTIC_CONFIG_PARAMETERS` | JSON overrides (tests, `DeduplicateCommand` children). [code: app/bundles/LeadBundle/Command/DeduplicateCommand.php:113 @7.x] |
| `MAUTIC_<KEY>` | Per-key override. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:26 @7.x] |
| `MAUTIC_TABLE_PREFIX` | Constant/env table prefix. [code: app/AppKernel.php:222-232 @7.x] |
| `MAUTIC_CUSTOM_DEV_HOSTS`, `DDEV_TLD` | Dev front-controller access. [code: app/middlewares/Dev/IpRestrictMiddleware.php:37-51 @7.x] |
| `app/release_metadata.json` | Version and PHP/DB minimums. [code: app/release_metadata.json:2-7 @7.x] |

## Permissions
There is no Permissions class. Access is admin-only via `isAdmin()` checks, and `/installer` sits outside the firewall. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:41 @7.x] [code: app/config/security.php:6-11 @7.x]

## Tests directories
`app/bundles/ConfigBundle/Tests/`, `app/bundles/InstallBundle/Tests/`, `app/bundles/CoreBundle/Tests/Unit/Loader/`, `app/middlewares/Tests/`. See test-patterns.md.
