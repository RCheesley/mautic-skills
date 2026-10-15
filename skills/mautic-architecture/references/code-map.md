# Mautic architecture - code map (7.x)

Paths are repo-relative. `@7.x` = upstream 7.x at 419a08a9b35 (7.2.1 plus unreleased merged PRs).

## Contents
1. Repository layout
2. Dependency injection machinery
3. Base classes (entity, repository, model, controller, form)
4. Core events and who dispatches/listens
5. Request lifecycle and Doctrine listeners
6. Routes in CoreBundle
7. Key parameters
8. Permissions classes
9. Translations, logging, errors
10. Admin UI files
11. Console commands in CoreBundle
12. Tests
13. Extension points

## 1. Repository layout

| Path | Holds | Source |
|---|---|---|
| `app/bundles/` | Core bundles, namespace `Mautic\` | [code: app/composer.json:7-16 @7.x] |
| `app/config/` | Kernel config (`config.php`, `config_prod.php`, `config_dev.php`, `config_test.php`, `security.php`, `paths_helper.php`) | [code: app/config/config.php:203-205 @7.x] |
| `app/middlewares/` | Pre-Symfony middlewares (`Mautic\Middleware\`) | [code: app/composer.json:7-16 @7.x] |
| `app/migrations/` | Core Doctrine migrations (`Mautic\Migrations\`) | [code: app/composer.json:7-16 @7.x] |
| `plugins/` | Plugins, namespace `MauticPlugin\` | [code: composer.json:108-119 @7.x] |
| `themes/`, `themes/system/` | Themes; `system` overrides core bundle templates | [code: app/bundles/CoreBundle/DependencyInjection/Compiler/SystemThemeTemplatePathPass.php:20-68 @7.x] |
| `translations/`, `translations/overrides/` | Downloaded language packs; site overrides | [code: app/bundles/CoreBundle/Loader/TranslationLoader.php:21-73 @7.x] |
| `config/local.php` | Saved configuration values | [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:195-216 @7.x] |
| `media/` | Combined admin assets, images, uploaded files | [code: app/bundles/CoreBundle/Helper/AssetGenerationHelper.php:84-237 @7.x] |
| `var/cache`, `var/logs`, `var/tmp`, `var/run` | Symfony cache, logs, temp, command lock files | [code: app/bundles/CoreBundle/Config/config.php:253-259 @7.x] [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:104-110 @7.x] |
| `index.php`, `bin/console` | Web and CLI entry points | [code: index.php:15 @7.x] |

Bundle internals follow a fixed layout: `Config/{config.php,services.php}`, `Controller/` (+`Api/`), `Entity/`,
`EventListener/`, `Event/`, `<Bundle>Events.php`, `Form/Type/`, `Model/`, `Security/Permissions/`,
`Translations/en_US/*.ini`, `Resources/views/`, `Assets/{css,js,images}`, `Tests/{Unit,Functional}/`, `Migrations/`
(plugins). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/structure.html]

## 2. Dependency injection machinery

| Item | Path | Notes |
|---|---|---|
| Extension | `app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php` | `DEFAULT_EXCLUDES` (14-29); loads project + Core `services.php` (34-43) [code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-43 @7.x] |
| Bundle build | `app/bundles/CoreBundle/MauticCoreBundle.php` | registers compiler passes (12-30) [code: app/bundles/CoreBundle/MauticCoreBundle.php:12-30 @7.x] |
| Bundle metadata | `DependencyInjection/Builder/BundleMetadataBuilder.php`, `Builder/Metadata/{ConfigMetadata,EntityMetadata,PermissionClassMetadata}.php` | core vs plugin, config.php reading, permission scan [code: app/bundles/CoreBundle/DependencyInjection/Builder/BundleMetadataBuilder.php:55-149 @7.x] |
| `ServicePass` (1000) | `DependencyInjection/Compiler/ServicePass.php` | legacy `config.php` services → definitions [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:33-312 @7.x] |
| `TranslationLoaderPass` (100) | `Compiler/TranslationLoaderPass.php` | swaps translator class, no cache outside prod [code: app/bundles/CoreBundle/DependencyInjection/Compiler/TranslationLoaderPass.php:13-31 @7.x] |
| `RequirementsPass` | `Compiler/RequirementsPass.php` | requires `pdo_mysql` [code: app/bundles/CoreBundle/DependencyInjection/Compiler/RequirementsPass.php:11-22 @7.x] |
| `ConfiguratorPass` | `Compiler/ConfiguratorPass.php` | `mautic.configurator.step` tags [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ConfiguratorPass.php:13-25 @7.x] |
| `DbalPass` | `Compiler/DbalPass.php` | DBAL result cache [code: app/bundles/CoreBundle/DependencyInjection/Compiler/DbalPass.php:18-27 @7.x] |
| `TwigPass` | `Compiler/TwigPass.php` | helpers + `site_url` + asset version into `AssetsHelper` [code: app/bundles/CoreBundle/DependencyInjection/Compiler/TwigPass.php:14-25 @7.x] |
| `ModelPass` | `Compiler/ModelPass.php` | `mautic.model` locator for `ModelFactory` [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ModelPass.php:17-38 @7.x] |
| `PermissionsPass` | `Compiler/PermissionsPass.php` | `mautic.permissions` → `setPermissionObject()` [code: app/bundles/CoreBundle/DependencyInjection/Compiler/PermissionsPass.php:12-20 @7.x] |
| `AssetMapperWebRootPass`, `ORMPurgerPass` (-10), `TranslationsPass` (-100), `SystemThemeTemplatePathPass`, `TestPass` (test only) | `Compiler/` | [code: app/bundles/CoreBundle/MauticCoreBundle.php:12-30 @7.x] |
| Env processors | `DependencyInjection/EnvProcessor/` | `nullable`, `intNullable`, `mauticconst` [code: app/bundles/CoreBundle/Config/services.php:282-294 @7.x] |
| Parameter loading | `Loader/ParameterLoader.php`, `Loader/EnvVars/ConfigEnvVars.php`, `Helper/CoreParametersHelper.php` | [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:195-221 @7.x] |
| Model lookup | `Factory/ModelFactory.php` | [code: app/bundles/CoreBundle/Factory/ModelFactory.php:70-108 @7.x] |

Service tags worth knowing: `mautic.permissions`, `mautic.model`, `mautic.shortener.service`, `mautic.configurator.step`,
`mautic.update_step`, `mautic.update_check`, `twig.helper`, `monolog.processor`, `container.env_var_processor`,
`translation.loader`, `knp_menu.menu`, `knp_menu.renderer`. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:33-63 @7.x] [code: app/bundles/CoreBundle/Config/services.php:69 @7.x]

Deprecated string aliases (since 7.2): `mautic.helper.encryption`, `mautic.core.service.flashbag`, `mautic.database.version.provider`,
`mautic.doctrine.loader.mautic_fixtures_loader`, `mautic.generated.columns.provider`, `mautic.helper.twig.menu`, `mautic.route_loader`.
[code: app/bundles/CoreBundle/Config/services.php:189-190 @7.x] [code: app/bundles/CoreBundle/Config/services.php:342-354 @7.x]

## 3. Base classes

| Class | Path | Key API |
|---|---|---|
| `CommonEntity` | `app/bundles/CoreBundle/Entity/CommonEntity.php` | change tracking `isChanged()`, `getChanges()`, magic `isFoo()`/`getName()` [code: app/bundles/CoreBundle/Entity/CommonEntity.php:14-137 @7.x] |
| `FormEntity` | `app/bundles/CoreBundle/Entity/FormEntity.php` | published flag, created/modified/checked-out columns, `getPublishStatus()`, `isPublished()`, `__clone()` [code: app/bundles/CoreBundle/Entity/FormEntity.php:127-459 @7.x] |
| Traits/interfaces | `Entity/{VariantEntityTrait,TranslationEntityTrait,DateAddedTrait,UuidTrait,OptimisticLockTrait,UpsertInterface,SkipModifiedInterface,CacheInvalidateInterface,FiltersEntityTrait,DynamicContentEntityTrait,DeprecatedInterface}.php` | [code: app/bundles/CoreBundle/Entity/VariantEntityTrait.php:50-73 @7.x] |
| `ClassMetadataBuilder` | `app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php` | `addId`, `addBigIntIdField`, `addUuid`, `addIdColumns`, `addCategory`, `addPublishDates`, `addDateAdded`, `addIndex`, length 191 rule [code: app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php:23-451 @7.x] |
| DBAL types | `Doctrine/Type/{UTCDateTimeType,UTCDateTimeImmutableType,ArrayType}.php` | registered globally [code: app/config/config.php:203-205 @7.x] |
| `CommonRepository` | `app/bundles/CoreBundle/Entity/CommonRepository.php` | `getEntities()` (354-406), `getSearchCommands()`/`getStandardSearchCommands()` (707-789), `getSimpleList()` (723-774), `upsert()` (868-951), `getPublishedByDate*Expression()` (527-630), `findOneBySlugs()` (239-297) [code: app/bundles/CoreBundle/Entity/CommonRepository.php:239-1883 @7.x] |
| `SearchStringHelper` | `app/bundles/CoreBundle/Helper/SearchStringHelper.php` | search syntax parser [code: app/bundles/CoreBundle/Helper/SearchStringHelper.php:47-284 @7.x] |
| `AbstractCommonModel` | `app/bundles/CoreBundle/Model/AbstractCommonModel.php` | `getRepository()`, `getPermissionBase()`, `getEntities()`, `getEntity()`, `getEntityBySlugs()`, `canViewOwnEntity()` [code: app/bundles/CoreBundle/Model/AbstractCommonModel.php:27-297 @7.x] |
| `FormModel` | `app/bundles/CoreBundle/Model/FormModel.php` | lock/unlock, `saveEntity(ies)`, `deleteEntity(ies)`, `togglePublishStatus()`, `setTimestamps()`, `createForm()`, `dispatchEvent()` (no-op), `cleanAlias()`, `flushAndCatch()` [code: app/bundles/CoreBundle/Model/FormModel.php:29-503 @7.x] |
| `AuditLogModel` | `app/bundles/CoreBundle/Model/AuditLogModel.php` | `writeToLog()`, `getLogForObject()` [code: app/bundles/CoreBundle/Model/AuditLogModel.php:34-80 @7.x] |
| `CommonController` | `app/bundles/CoreBundle/Controller/CommonController.php` | `delegateView()`, `postActionRedirect()`, `delegateRedirect()`, `executeAction()`, `notFound()`, `getModel()` [code: app/bundles/CoreBundle/Controller/CommonController.php:120-729 @7.x] |
| `AbstractFormController` | `app/bundles/CoreBundle/Controller/AbstractFormController.php` | `unlockAction()`, `isLocked()`, `isFormCancelled()`, `isFormApplied()`, `canEdit()` [code: app/bundles/CoreBundle/Controller/AbstractFormController.php:22-204 @7.x] |
| `AbstractStandardFormController` | `app/bundles/CoreBundle/Controller/AbstractStandardFormController.php` | `indexStandard`, `newStandard`, `editStandard`, `viewStandard`, `cloneStandard`, `deleteStandard`, `batchDeleteStandard`; hooks `beforeEntitySave`, `afterEntitySave`, `afterEntityClone`, `getViewArguments`, `getEntityFormOptions` [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:64-1215 @7.x] |
| `AjaxController` | `app/bundles/CoreBundle/Controller/AjaxController.php` | `delegateAjaxAction()`, `executeAjaxAction()`, `sendJsonResponse()` [code: app/bundles/CoreBundle/Controller/AjaxController.php:44-136 @7.x] |
| `AbstractFormStandardType` | `app/bundles/CoreBundle/Form/Type/AbstractFormStandardType.php` | name/description/category/isPublished/publish dates/buttons, `clean_masks` [code: app/bundles/CoreBundle/Form/Type/AbstractFormStandardType.php:40-133 @7.x] |
| Controller traits | `Controller/{AjaxLookupControllerTrait,FormErrorMessagesTrait,FormThemeTrait,QuickFilterSearchTrait,CategoryListFiltersTrait,VariantAjaxControllerTrait}.php` | [code: app/bundles/CoreBundle/Controller/FormErrorMessagesTrait.php:79-94 @7.x] |

## 4. Core events (`app/bundles/CoreBundle/CoreEvents.php`)

| Constant (value) | Event class | Dispatched at | Main listeners |
|---|---|---|---|
| `BUILD_MENU` (`mautic.build_menu`) | `MenuEvent` | `Menu/MenuBuilder.php:84` | `CoreSubscriber::onBuildMenu` prio 9999 [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:43 @7.x] |
| `BUILD_ROUTE` (`mautic.build_route`) | `RouteEvent` | `Loader/RouteLoader.php:31,48,59,77` | `CoreSubscriber::onBuildRoute` [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:114-208 @7.x] |
| `GLOBAL_SEARCH` (`mautic.global_search`) | `GlobalSearchEvent` | `Controller/DefaultController.php:58`, `Controller/AjaxController.php:145` | `SearchSubscriber` in 12 bundles [code: app/bundles/CoreBundle/Controller/AjaxController.php:144-145 @7.x] |
| `LIST_STATS` (`mautic.list_stats`) | `StatsEvent` | `Controller/Api/StatsApiController.php:39` | `CommonStatsSubscriber` subclasses [code: app/bundles/CoreBundle/EventListener/CommonStatsSubscriber.php:36-41 @7.x] |
| `BUILD_COMMAND_LIST` (`mautic.build_command_list`) | `CommandListEvent` | `Service/SearchCommandList.php:30` | `SearchSubscriber`s [code: app/bundles/CoreBundle/Service/SearchCommandList.php:23-33 @7.x] |
| `FETCH_ICONS` (`mautic.on_fetch_icons`) | `IconEvent` | never by this name (see behaviour Q) | `CoreSubscriber::onFetchIcons` [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:210-246 @7.x] |
| `PRE_UPGRADE` / `POST_UPGRADE` | `UpgradeEvent` | no dispatcher | none [code: app/bundles/CoreBundle/CoreEvents.php @7.x] |
| `BUILD_MAUTIC_JS` (`mautic.build_embeddable_js`) | `BuildJsEvent` | `Controller/JsController.php:48-49` | Core (prio 1000), DynamicContent, Notification, Page `BuildJsSubscriber` [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:17-25 @7.x] |
| `MAINTENANCE_CLEANUP_DATA` | `MaintenanceEvent` | `Command/CleanupMaintenanceCommand.php:125` | Core (prio -50), Lead, Page `MaintenanceSubscriber` [code: app/bundles/CoreBundle/EventListener/MaintenanceSubscriber.php:29-81 @7.x] |
| `VIEW_INJECT_CUSTOM_BUTTONS` | `CustomButtonEvent` | `Twig/Helper/ButtonHelper.php:317-321` | Channel, Campaign, Lead, Category, FullContact, Clearbit `ButtonSubscriber` |
| `VIEW_INJECT_CUSTOM_CONTENT` | `CustomContentEvent` | `Twig/Helper/ContentHelper.php:33-35` | Campaign, Email subscribers |
| `VIEW_INJECT_CUSTOM_TEMPLATE` | `CustomTemplateEvent` | `Controller/CommonController.php:199,263`, `Twig/Extension/OverrideIncludeExtension.php` | Campaign `PublishToggleSubscriber`, Integrations `UIContactIntegrationsTabSubscriber` |
| `VIEW_INJECT_CUSTOM_ASSETS` | `CustomAssetsEvent` | `EventListener/AssetsSubscriber.php:32-36` | `EditorFontsSubscriber` [code: app/bundles/CoreBundle/EventListener/EditorFontsSubscriber.php:33-43 @7.x] |
| `ON_GENERATED_COLUMNS_BUILD` | `GeneratedColumnsEvent` | `Doctrine/Provider/GeneratedColumnsProvider.php:41-43` | Campaign, Email, Lead `GeneratedColumnSubscriber` |

Class-dispatched (no constant): `EntityExportEvent`, `EntityImportEvent`, `EntityImportAnalyzeEvent`, `EntityImportUndoEvent`,
`EntityValidateEvent`, `JobExtendTimeEvent`, `IconEvent`. [code: app/bundles/CoreBundle/Command/EntityExportCommand.php:85-87 @7.x] [code: app/bundles/CoreBundle/Command/EntityImportCommand.php:80-81 @7.x]

Model string hooks (converted to bundle events by each model's `dispatchEvent()`): `pre_save`, `post_save`, `pre_batch_save`,
`post_batch_save`, `pre_delete`, `post_delete`, `pre_unpublish`, `on_toggle_publish`. [code: app/bundles/CoreBundle/Model/FormModel.php:110-343 @7.x]

How to find dispatchers and listeners: grep the constant name and its string value across `app/bundles` and `plugins`;
in 8.x run `bin/console debug:event-dispatcher <class>`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#available-events]

## 5. Request lifecycle and Doctrine listeners

| Listener | Event / priority | Path |
|---|---|---|
| `ErrorHandlingListener` | kernel.request 2047 | `app/bundles/CoreBundle/EventListener/ErrorHandlingListener.php` |
| `EnvironmentSubscriber` | kernel.request 128 (timezone), 101 (locale) | `app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php` |
| `RouterSubscriber` | kernel.request 1, finish_request -1 | `app/bundles/CoreBundle/EventListener/RouterSubscriber.php` |
| `RequestSubscriber` | kernel.request 0 (AJAX CSRF) | `app/bundles/CoreBundle/EventListener/RequestSubscriber.php` |
| `AssetsSubscriber` | kernel.request 0 | `app/bundles/CoreBundle/EventListener/AssetsSubscriber.php` |
| `ExceptionListener` | kernel.exception 253 / 0; kernel.response -128 | `app/bundles/CoreBundle/EventListener/ExceptionListener.php` |
| `CoreSubscriber` | security.interactive_login, BUILD_MENU, BUILD_ROUTE, FETCH_ICONS | `app/bundles/CoreBundle/EventListener/CoreSubscriber.php` |
| `ConsoleErrorListener`, `ConsoleTerminateListener`, `MigrationCommandSubscriber` | console.error / console.terminate | `app/bundles/CoreBundle/EventListener/` |
| `DoctrineEventsSubscriber` | loadClassMetadata, postGenerateSchema (table prefix) | `app/bundles/CoreBundle/EventListener/DoctrineEventsSubscriber.php` |
| `UUIDListener`, `OptimisticLockSubscriber`, `CacheInvalidateSubscriber`, `DoctrineGeneratedColumnsListener` | Doctrine prePersist / postUpdate / post* / postGenerateSchema | `app/bundles/CoreBundle/EventListener/` |

[code: app/bundles/CoreBundle/EventListener/ @7.x]

## 6. Routes in CoreBundle (`app/bundles/CoreBundle/Config/config.php:6-110`)

| Name | Path | Controller |
|---|---|---|
| `mautic_core_ajax` | `/s/ajax` | `AjaxController::delegateAjaxAction` |
| `mautic_core_form_action` | `/s/action/{objectAction}/{objectModel}/{objectId}` | `FormController::executeAction` (unlock) |
| `mautic_core_file_action` | `/s/file/{objectAction}/{objectId}` | `FileController::executeAction` |
| `mautic_themes_index` / `_action` | `/s/themes`, `/s/themes/{objectAction}/{objectId}` | `ThemeController` |
| `mautic_core_keep_alive` | `/s/keep-alive` | `KeepAliveController` |
| `mautic_js`, `mautic_essential_js`, `mautic_tracking_js` | `/mtc.js`, `/mautic-essential.js`, `/mautic-tracking.js` | `JsController` |
| `mautic_base_index`, `mautic_secure_root(_slash)`, `mautic_remove_trailing_slash` | `/`, `/s`, `/s/`, `/{url}` ending `/` | `DefaultController`, `CommonController` |
| `mautic_core_api_file_*`, `mautic_core_api_theme_*`, `mautic_core_api_stats` | `/api/files/{dir}...`, `/api/themes...`, `/api/stats/{table}` | `Api\FileApiController`, `Api\ThemeApiController`, `Api\StatsApiController` |

[code: app/bundles/CoreBundle/Config/config.php:6-110 @7.x]

Route groups in `config.php`: `main` (`/s`, user login), `public` (no auth), `api` (`/api`, OAuth/basic), `catchall`
(compiled last; Landing Page custom URLs). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#routing-firewalls] [code: app/bundles/CoreBundle/Loader/RouteLoader.php:28-85 @7.x]

## 7. Key parameters (`app/bundles/CoreBundle/Config/config.php` `parameters`, 249-812)

| Parameter | Default | Effect |
|---|---|---|
| `site_url` | `''` | Router context, https forcing, trailing-slash redirects [code: app/bundles/CoreBundle/Loader/RouteLoader.php:34-41 @7.x] |
| `secret_key` | `temp` | Encryption key, asset version salt, remember-me key [code: app/bundles/CoreBundle/Helper/EncryptionHelper.php:39 @7.x] |
| `locale` / `default_timezone` | `en_US` / `UTC` | UI locale and local timezone fallbacks [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:38-56 @7.x] |
| `default_pagelimit` | `30` | List page size [code: app/bundles/CoreBundle/Helper/PageHelper.php:19-25 @7.x] |
| `max_entity_lock_time` | `0` (never expires) | Entity checkout expiry seconds [code: app/bundles/CoreBundle/Config/config.php:708 @7.x] |
| `date_format_full/_short/_dateonly/_timeonly` | `F j, Y g:i a T` / `D, M d` / `F j, Y` / `g:i a` | Twig date helpers [code: app/bundles/CoreBundle/Config/config.php:287-290 @7.x] |
| `log_path`, `log_file_name`, `max_log_files`, `debug` | `var/logs`, `mautic_%kernel.environment%.php`, `7`, `false` | Mautic log [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:12-25 @7.x] |
| `cookie_path/_domain/_secure/_httponly` | `/`, `''`, `true`, `false` | `CookieHelper` defaults [code: app/bundles/CoreBundle/Config/config.php:297-300 @7.x] |
| `404_page`, `webroot` | `''` | Landing page for 404 / for `/` [code: app/bundles/CoreBundle/Controller/CommonController.php:568-597 @7.x] |
| `db_table_prefix` | `''` | Prefix for every Mautic table [code: app/bundles/CoreBundle/EventListener/DoctrineEventsSubscriber.php:30-109 @7.x] |
| `track_private_ip_ranges`, `do_not_track_ips`, `do_not_track_internal_ips` | `false`, `[]`, `[]` | Client IP handling [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:53-56 @7.x] |

Configuration UI and `local.php` writing: mautic-configuration.

## 8. Permissions classes

| Class | Path |
|---|---|
| `CorePermissions` (`mautic.security`) | `app/bundles/CoreBundle/Security/Permissions/CorePermissions.php` |
| `AbstractPermissions` | `app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php` |
| `SystemPermissions` (`core:themes`) | `app/bundles/CoreBundle/Security/Permissions/SystemPermissions.php` |
| `VirtualPermissions` interface | `app/bundles/CoreBundle/Security/Permissions/VirtualPermissions.php` |
| Exceptions (code 403) | `app/bundles/CoreBundle/Security/Exception/` |
| Stored rows | `UserBundle\Entity\Permission` → `permissions` (`bundle`, `name`, `role_id`, `bitwise`) [code: app/bundles/UserBundle/Entity/Permission.php:79-99 @7.x] |

Twig: `securityIsGranted('bundle:name:level')`, `securityHasEntityAccess(...)`. [code: app/bundles/CoreBundle/Twig/Extension/ @7.x]

## 9. Translations, logging, errors

| Concern | Path |
|---|---|
| Loader (`translation.loader` alias `mautic`) | `app/bundles/CoreBundle/Loader/TranslationLoader.php` [code: app/bundles/CoreBundle/Config/services.php:69 @7.x] |
| Translator decorator | `app/bundles/CoreBundle/Translation/Translator.php`, `TranslatorLoader.php` |
| Core strings | `app/bundles/CoreBundle/Translations/en_US/{flashes,javascript,messages,validators}.ini` |
| Log handler / processor | `app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php`, `Monolog/LogProcessor.php`; prod channels `app/config/config_prod.php:31-59` |
| Error handler | `app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php` (registered in `index.php:15`) |
| Offline page | `app/bundles/CoreBundle/Resources/views/Offline/offline.html.twig` (override `custom_offline.html.twig`) |
| Exception rendering | `app/bundles/CoreBundle/Controller/ExceptionController.php`, `Resources/views/{Error,Exception}/` |

## 10. Admin UI files

| File | Role |
|---|---|
| `app/bundles/CoreBundle/Resources/views/Default/base.html.twig` | Full admin shell |
| `Resources/views/Default/content.html.twig` | Template bundles extend; picks base/slim/output/modal |
| `Resources/views/Default/script.html.twig` | JS globals incl. `mauticAjaxCsrf` |
| `Resources/views/Standard/list.html.twig` | Generic list |
| `Resources/views/Helper/*.html.twig` | Partials (publish status, pagination, toolbar, search, modal, `no-information`) |
| `Assets/js/1.core.js`, `1a.content.js`, `6.forms.js`, `10.entity.js`, ... | `Mautic.*` runtime, numbered load order |
| `Assets/app.js`, `Assets/css/app.scss` | AssetMapper/Sass entry |
| `Helper/AssetGenerationHelper.php` | Combines bundle assets into `media/` |

[code: app/bundles/CoreBundle/Resources/views/ @7.x] [code: app/bundles/CoreBundle/Assets/ @7.x]

## 11. Console commands in CoreBundle

`mautic:maintenance:cleanup`, `mautic:unusedip:delete`, `mautic:anonymize:ip`, `mautic:remove:anonymous_contacts`,
`mautic:max-mind:purge`, `mautic:donotsell:download`, `mautic:iplookup:download`, `mautic:motd`, `mautic:assets:cleanup`,
`mautic:update:find`, `mautic:update:apply`, `mautic:theme:json-config`, `mautic:entity:export`, `mautic:entity:import`,
`mautic:install:data`, `mautic:transifex:pull`, `mautic:transifex:push`, `mautic:assets:generate`. Commands are autowired
and registered with `#[AsCommand]`. Scheduling and locking: mautic-cron-and-queues. [code: app/bundles/CoreBundle/Command/ @7.x]

## 12. Tests

| Kind | Location |
|---|---|
| Base classes | `app/bundles/CoreBundle/Test/AbstractMauticTestCase.php`, `MauticMysqlTestCase.php` |
| Unit | `app/bundles/CoreBundle/Tests/Unit/` |
| Functional | `app/bundles/CoreBundle/Tests/Functional/` |
| Container smoke tests | `app/bundles/CoreBundle/Tests/Functional/DependencyInjection/` (`CommandSmokeTest`, `EventSubscriberSmokeTest`) |
| Legacy mixed dirs | `Tests/Command`, `Tests/EventListener`, `Tests/Service`, `Tests/Translation`, `Tests/Helper`, `Tests/Form`, `Tests/Twig` |

[code: app/bundles/CoreBundle/Tests/ @7.x] Details: test-patterns.md.

## 13. Extension points

| Want to | Use |
|---|---|
| Add an entity type with CRUD | `FormEntity` + `CommonRepository` + `FormModel` + `AbstractStandardFormController` + `AbstractFormStandardType` [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:64 @7.x] |
| Add an AJAX endpoint | `fooAction()` on your `AjaxController`, `action=bundle:foo` [code: app/bundles/CoreBundle/Controller/AjaxController.php:77-136 @7.x] |
| Inject UI into core screens | `VIEW_INJECT_CUSTOM_TEMPLATE/CONTENT/BUTTONS/ASSETS` [code: app/bundles/CoreBundle/CoreEvents.php @7.x] |
| Add menu items | `config.php` `menu` (`main`, `admin`, `profile`, `extra`) or `BUILD_MENU` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-config-items] |
| Add routes | `config.php` `routes` or `BUILD_ROUTE` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#advanced-routing] |
| Add tracking JS | `BUILD_MAUTIC_JS` with `appendJsForScope()` [code: app/bundles/CoreBundle/Event/BuildJsEvent.php:38-51 @7.x] |
| Global search / search commands | `GlobalSearchInterface` + `GLOBAL_SEARCH` / `BUILD_COMMAND_LIST` |
| Maintenance cleanup | `MAINTENANCE_CLEANUP_DATA`, respect `isDryRun()`/`isGdpr()` |
| Optimistic locking / cache purge / uuid | `OptimisticLockInterface`, `CacheInvalidateInterface`, `UuidInterface` |
| Custom permissions | `AbstractPermissions` subclass tagged `mautic.permissions` (see mautic-users-and-permissions) |
| Override a template | `themes/system/<BundleDir>/Resources/views/...` [code: app/bundles/CoreBundle/DependencyInjection/Compiler/SystemThemeTemplatePathPass.php:30-66 @7.x] |
| URL shortener | service tagged `mautic.shortener.service` implementing `ShortenerServiceInterface` [code: app/bundles/CoreBundle/Shortener/Shortener.php:22-71 @7.x] |
