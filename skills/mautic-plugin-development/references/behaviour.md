# Plugin development — behaviour specification (7.x, with 8.x deltas)

Contents
1. Discovery and bundle registration (B1–B8)
2. Configuration file and parameters (B9–B16)
3. Services, autowiring and DI (B17–B26)
4. Routes, controllers and views (B27–B36)
5. Menus (B37–B41)
6. Permissions (B42–B52)
7. Install, update, reload lifecycle (B53–B66)
8. Entities, schema and migrations (B67–B78)
9. Events and subscribers (B79–B88)
10. Translations, assets, cache (B89–B97)
11. Marketplace and packaging (B98–B104)
12. Open questions and contradictions (Q1–Q8)

## 1. Discovery and bundle registration
B1. The kernel scans `<app>/plugins` at depth 1 for files named `*Bundle.php`, follows symlinks, and builds the class name `\MauticPlugin\<directory name>\<file name without .php>` [code: app/AppKernel.php:158-170 @7.x].
B2. The bundle is registered only if that class exists and is an instance of Symfony's `Bundle`; otherwise it is skipped silently [code: app/AppKernel.php:170-185 @7.x].
B3. If the class defines `MINIMUM_MAUTIC_VERSION` and `version_compare(<running version>, MINIMUM_MAUTIC_VERSION, 'lt')`, the plugin is skipped silently; no in-repo plugin uses this constant [code: app/AppKernel.php:176-181 @7.x] [code: integrations-plugins-marketplace 9.2 @7.x].
B4. Extra bundles can be added through `config/bundles_local.php`, included after plugin discovery [code: app/AppKernel.php:199-202 @7.x].
B5. Mautic's metadata builder treats bundles whose namespace contains `MauticPlugin\` as plugins and builds `isPlugin`, `base` (bundle name minus `Bundle`), `bundle`, `relative`, `directory`, `namespace`, `symfonyBundleName`, `bundleClass`, `config`, `permissionClasses` [code: app/bundles/CoreBundle/DependencyInjection/Builder/BundleMetadataBuilder.php:53-119 @7.x].
B6. Plugin metadata is published as the container parameter `mautic.plugin.bundles` (core bundles in `mautic.bundles`); `CoreParametersHelper::get('plugin.bundles')` resolves to it [code: app/config/config.php:22-23 @7.x] [code: app/bundles/CoreBundle/Helper/CoreParametersHelper.php:30-42 @7.x].
B7. `AbstractPluginBundle` (IntegrationsBundle) is an empty abstract subclass of `PluginBundleBase` (PluginBundle), itself an empty abstract Symfony `Bundle`; the bundled plugins extend `PluginBundleBase` directly [code: app/bundles/IntegrationsBundle/Bundle/AbstractPluginBundle.php:12 @7.x] [code: app/bundles/PluginBundle/Bundle/PluginBundleBase.php:9-14 @7.x] [code: plugins/MauticCrmBundle/MauticCrmBundle.php:5-11 @7.x].
B8. All plugin classes must live in namespace `MauticPlugin\<Plugin Folder Name>\` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/getting_started.html].

## 2. Configuration file and parameters
B9. `Config/config.php` returns an array; core reads `name`, `description`, `version`, `author` (reload helper), `routes`, `menu`, `services`, `parameters`, `ip_lookup_services` (metadata) and `categories` [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/ConfigMetadata.php:17-116 @7.x] [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:128-153 @7.x] [code: plugins/MauticFocusBundle/Config/config.php:58-63 @7.x].
B10. If `name` is missing, the plugin's display name falls back to the bundle base name [code: bundled-plugins §0.3 @7.x].
B11. `description` is split on a line containing only `---` into primary and secondary descriptions for the info modal [code: app/bundles/PluginBundle/Entity/Plugin.php:13,249-256 @7.x].
B12. A `services` entry with `'optional' => true` whose class does not exist is dropped; `%` in service arguments and parameters is escaped [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/ConfigMetadata.php:17-116 @7.x].
B13. Every bundle's `parameters` are merged and registered as `mautic.<name>` resolving `%env(…:MAUTIC_<NAME>)%`, so env vars override defaults [code: app/config/parameters.php:16-47 @7.x].
B14. Parameter defaults must have the value's type (`[]`, `0`, `true/false`) so Mautic typecasts; services should accept `null` for string and integer parameters [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#parameters-config-items].
B15. Parameters are not shown in the Configuration UI unless the plugin adds a config form through the config builder event; saved values go to `config/local.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#custom-config-parameters].
B16. The config form subscriber adds a tab with `ConfigBuilderEvent::addForm(['formAlias','formTheme','parameters'])`, can rewrite values before save via `getConfig()`/`setConfig()`, and the tab label key is `mautic.config.tab.<formAlias>` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#generate-plugin-configuration]. On 8.x the subscriber keys on `ConfigBuilderEvent::class` / `ConfigPreSaveEvent::class` / `ConfigPostSaveEvent::class` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/config.html#config-event-subscriber].

## 3. Services, autowiring and DI
B17. For every core and plugin bundle **without** `Config/services.php`, `app/config/services.php` loads the bundle namespace with autowire, autoconfigure and public defaults, excluding `MauticCoreExtension::DEFAULT_EXCLUDES`, and loads `Entity/*Repository.php` as services [code: app/config/services.php:10-32 @7.x].
B18. A bundle **with** `Config/services.php` is skipped by that loader; its own `DependencyInjection/<Name>Extension.php` must load the file (name = bundle class name with `Bundle` replaced by `Extension`) [code: app/config/services.php:21-23 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#introducing-services-php].
B19. `DEFAULT_EXCLUDES` = `Config`, `Crate`, `DataObject`, `DependencyInjection`, `DTO`, `Entity`, `Event`, `Exception`, `Migration`, `Migrations`, `Security`, `Test`, `Tests`, `Views` [code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-29 @7.x].
B20. Because `Security` is excluded, permission classes are not autowired on 7.x; they are discovered by file scan (B43) [code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-29 @7.x].
B21. On 7.x `ServicePass` still processes the `services` array of every bundle's `config.php` and assigns default tags per group (`events`, `forms`, `helpers` → `twig.helper`, `menus`, `models` (deprecated, triggers `E_USER_DEPRECATED`), `permissions`, `integrations`, `controllers`; other groups untagged) [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:31-64 @7.x].
B22. Service keys in `config.php` must be unique across Mautic; `arguments` strings are service ids unless wrapped as `%param%` or `'"literal"'`; `public` defaults to true [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#service-definitions].
B23. Unused private services that are not dependencies are removed from the container; services are public by default only for controllers and legacy container access [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#advantages].
B24. Scalars and arrays must be bound explicitly (`->arg('$x', '%mautic.key%')`), otherwise the container fails with "Cannot autowire service" [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#special-cases].
B25. Bundled plugins add explicit string aliases (`mautic.integration.<name>`, `mautic.<plugin>.model.<name>`) next to FQCN services for BC [code: plugins/MauticTagManagerBundle/Config/services.php:25-28 @7.x].
B26. 8.x no longer reads the `config.php` `services` array (including `models` and `menus`); `ServicePass`, `TwigPass`, `ModelPass`, `PermissionsPass` are removed; many string service ids (`mautic.security`, `mautic.helper.*`, `mautic.cache.adapter.*`, model aliases) are gone [code: 8x-changes §4 Core @8.x].

## 4. Routes, controllers and views
B27. `RouteLoader` dispatches `CoreEvents::BUILD_ROUTE` four times: `public` (no prefix), default/`main` (prefixed `/s`), `api` (prefixed `/api`), `catchall` (added last) [code: app/bundles/CoreBundle/Loader/RouteLoader.php:28-84 @7.x].
B28. When `site_url` is https, all four collections are forced to the https scheme [code: app/bundles/CoreBundle/Loader/RouteLoader.php:34-44 @7.x].
B29. `main` routes require standard User authentication; `api` routes require API authentication (OAuth2/basic); `public` routes require none [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#routing-firewalls].
B30. Route names are unique across all bundles and firewalls; paths are unique within a firewall; Symfony uses the first match [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#routing-firewalls].
B31. Mautic route defaults: `{page}` requires `\d+`, `{objectId}` defaults to 0, `{id}` requires digits on `api` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#special-routing-parameters].
B32. `controller` accepts `Class::method`, `[Class::class, 'method']` or an invokable class; the legacy `Bundle:Controller:action` notation is pre-Mautic 5 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#route-definitions] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
B33. `standard_entity => true` on an `api` route registers GET, POST, PUT, PATCH and DELETE single and batch endpoints [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#route-definitions].
B34. Views are Twig only since Mautic 5, addressed as `@<BundleNameWithoutBundle>/<Dir>/<file>.html.twig` from `Resources/views/` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html] [code: plugins/MauticTagManagerBundle/Controller/TagController.php:153 @7.x].
B35. `delegateView()` returns a full page for HTTP and partial content for AJAX; `passthroughVars.activeLink` and `route` should be set for main-content responses; `mauticContent` triggers `Mautic.<value>OnLoad()` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#delegateview-args].
B36. 8.x: core routes move to `#[Route]` attributes but plugins keep `config.php` `routes`; `CommonController` helpers become `protected`; `FormController` is removed in favour of `AbstractFormController` / `AbstractStandardFormController` [code: 8x-changes §4 Core @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#removed-formcontroller].

## 5. Menus
B37. Menus are `main`, `admin`, `profile` and `extra` (unused by core) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#available-menus].
B38. Items default to priority 9999; higher priority sorts earlier [code: app/bundles/CoreBundle/Menu/MenuHelper.php:32,142,177 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-priority].
B39. Items keep only if they define `route`, `uri` or `children`; `uri`-only items render from 7.2 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-definitions].
B40. `access` hides an item unless the permission (or `admin`) is granted; `checks` (`parameters`, `request`, `integration`) must all pass [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-checks].
B41. 8.x removes `services > menus`; a custom top-level menu needs a `MenuItem` tagged `knp_menu.menu` and a `MenuRenderer` tagged `knp_menu.renderer` sharing an alias in `services.php` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/config.html#registering-a-custom-menu].

## 6. Permissions
B42. Permission classes extend `AbstractPermissions` and implement a constructor defining `$this->permissions`, `getName()` and `buildForm()` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#creating-custom-permissions] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:15-93 @7.x].
B43. Mautic scans `<bundle>/Security/Permissions/*Permissions.php`, skips abstract classes and non-`AbstractPermissions` classes, and records the rest in `permissionClasses` [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/PermissionClassMetadata.php:20-49 @7.x].
B44. Services tagged `mautic.permissions` are injected into `CorePermissions` and indexed by class and by `getName()` [code: app/bundles/CoreBundle/DependencyInjection/Compiler/PermissionsPass.php:12-20 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:44-48 @7.x].
B45. Untagged classes are instantiated on the fly with all core parameters through a deprecated fallback [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:445-461 @7.x].
B46. `isGranted()` requires 3 or 4 colon-separated parts, else `PermissionBadFormatException`; the first part selects the permission object by name [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-227 @7.x].
B47. Administrators are granted every permission; anonymous Users are denied; an unsupported permission throws `PermissionNotFoundException` unless `$allowUnknown` [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:219-247 @7.x].
B48. `MATCH_ALL` (default) denies if any is denied, `MATCH_ONE` grants if any is granted, `RETURN_ARRAY` returns the map [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:252-262 @7.x].
B49. Bits double (1, 2, 4, …); a Role stores the sum of granted bits; `full` must be the highest bit and implies all others in its level [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#how-permissions-work].
B50. `addStandardPermissions()` adds view, edit, create, delete, publish (optional), full; `addExtendedPermissions()` adds own/other variants; `addManagePermission()` adds a single `manage` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/security.html#creating-custom-permissions].
B51. `getSynonym()` maps e.g. `editown` → `edit` when the level lacks `editown`; `analyzePermissions()` can adjust bits before save and request a second round [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#permission-aliases].
B52. 8.x: `definePermissions()` removed, constructor takes no `$params`, `$this->params` set by an autowired setter after construction, classes registered as services in `services.php` (autoconfigured tag) [code: 8x-changes §4 Core @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html#construct].

## 7. Install, update, reload lifecycle
B53. `mautic:plugins:reload` (aliases `mautic:plugins:install`, `mautic:plugins:update`) runs `ReloadFacade::reloadPlugins()`, prints the flash message, always exits 0, and takes no lock [code: app/bundles/PluginBundle/Command/ReloadCommand.php:13-35 @7.x].
B54. The reload order is: flag DB plugins whose bundle is gone as `is_missing=1`; un-flag plugins that reappeared; update changed plugins; install new plugins; save all; report added/disabled/updated counts [code: app/bundles/PluginBundle/Facade/ReloadFacade.php:24-49 @7.x].
B55. The UI **Install/Upgrade Plugins** action on `/s/plugins` runs the same reload and requires `plugin:plugins:manage` [code: integrations-plugins-marketplace §8 @7.x] [code: app/bundles/PluginBundle/Controller/PluginController.php:409 @7.x].
B56. A plugin is "updated" only when the DB version is empty and the config version is not, or `version_compare(old, new) === -1` [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:76-77 @7.x].
B57. On update, Mautic dispatches `PluginEvents::ON_PLUGIN_UPDATE` with `PluginUpdateEvent(plugin, oldVersion, metadata, installedSchema)` [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:78-85 @7.x].
B58. Core's `PluginSubscriber::onUpdate()` runs the plugin's migrations for every updated plugin, independent of its base class [code: app/bundles/PluginBundle/EventListener/PluginSubscriber.php:34-37 @7.x] [code: app/bundles/PluginBundle/Bundle/PluginDatabase.php:70-80 @7.x].
B59. Name, description and author are re-mapped from config on every reload but are persisted only when the version changed [code: integrations-plugins-marketplace 9.7 @7.x].
B60. On install, Mautic maps config `version`, `name`, `description`, `author` to a new `Plugin` row and dispatches `ON_PLUGIN_INSTALL` with `PluginInstallEvent(plugin, metadata, installedSchema)` [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:102-153 @7.x].
B61. `metadata` is null when the plugin has no Doctrine entities; `installedSchema` is non-null when at least one plugin table already exists [code: integrations-plugins-marketplace 9.8 @7.x].
B62. Core's `PluginSubscriber::onInstall()` creates the schema with `SchemaTool::getCreateSchemaSql()` only when metadata is present and `installedSchema` is null; DDL runs outside a transaction [code: app/bundles/PluginBundle/EventListener/PluginSubscriber.php:20-32 @7.x] [code: app/bundles/PluginBundle/Bundle/PluginDatabase.php:35-65 @7.x].
B63. Migrations do not run on install [code: app/bundles/PluginBundle/EventListener/PluginSubscriber.php:20-37 @7.x].
B64. `checkContext($name)` on both events compares against the plugin's display name [code: app/bundles/PluginBundle/Event/PluginInstallEvent.php:41-44 @7.x] [code: app/bundles/PluginBundle/Event/PluginUpdateEvent.php:48-51 @7.x].
B65. Nothing deletes `plugins` rows; `PluginDatabase::dropPluginSchema()` has no caller; deleting a `plugins` row would cascade to `plugin_integration_settings` [code: integrations-plugins-marketplace §12, 9.85 @7.x].
B66. `plugins.bundle` has a unique constraint `unique_bundle` [code: app/bundles/PluginBundle/Entity/Plugin.php:76-78 @7.x].

## 8. Entities, schema and migrations
B67. Entities use Doctrine's static PHP mapping (`loadMetadata(ClassMetadata $metadata)`) by default; annotations are allowed but cannot be mixed with it in one plugin [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#support-for-entity-annotations].
B68. `ClassMetadataBuilder::addField()` caps string/indexed fields at 191 characters for utf8mb4; helpers include `addIdColumns()`, `addDateAdded()`, `addCategory()`, `addContact()`, `addPublishDates()`, `addUuid()` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#entity-php-static-function-mapping].
B69. Plugins cannot use core Doctrine migrations (configured only for `Mautic\Migrations` in `app/migrations`) [code: app/config/config.php:225-228 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations].
B70. The plugin migration engine reads `plugins/<Bundle>/Migrations/`; a missing directory is not an error [code: app/bundles/IntegrationsBundle/Migration/Engine.php:26-35,86-95 @7.x] [code: app/bundles/PluginBundle/Bundle/PluginDatabase.php:70-80 @7.x].
B71. Every file in that directory is `require_once`d and instantiated as `MauticPlugin\<Bundle>\Migrations\<file basename>` with `(EntityManager, tablePrefix)`; non-PHP files would break the run [code: app/bundles/IntegrationsBundle/Migration/Engine.php:68-80 @7.x].
B72. Files run in `scandir` order (ascending byte order), not semantic-version order [code: app/bundles/IntegrationsBundle/Migration/Engine.php:86-95 @7.x].
B73. Each migration runs only if `isApplicable(Schema)` returns true on the introspected schema; `up()` queues SQL with `addSql()`, executed with prepared statements [code: app/bundles/IntegrationsBundle/Migration/AbstractMigration.php:23-45 @7.x].
B74. All applicable migrations of one plugin share one transaction; commit is skipped when PDO auto-committed DDL; a DBAL exception rolls back and is rethrown [code: app/bundles/IntegrationsBundle/Migration/Engine.php:38-60 @7.x].
B75. MySQL DDL auto-commits, so a failed migration after a successful `ALTER` leaves the earlier change applied; `isApplicable()` guards make re-runs safe [code: app/bundles/IntegrationsBundle/Migration/Engine.php:52-56 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations].
B76. `AbstractMigration` helpers: `concatPrefix()`, `columnsToString()`, `generateIndexStatement()`, `generateAlterTableForeignKeyStatement()`, `generatePropertyName()` [code: app/bundles/IntegrationsBundle/Migration/AbstractMigration.php:54-127 @7.x].
B77. No bundled plugin ships a `Migrations/` directory; they rely on install-time schema creation [code: bundled-plugins §0.1 @7.x].
B78. 8.x: `ClassMetadataBuilder::addLead()`/`addContact()` removed; mapping moves towards `#[ORM\*]` attributes (hybrid driver reads attributes first); `createManyToMany()`/`createOneToMany()` return Doctrine builders [code: 8x-changes §4 Core @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/database.html#entity-php-static-function-mapping].

## 9. Events and subscribers
B79. Subscribers implement `EventSubscriberInterface`; in an autowired directory they are autoconfigured, so no registration is needed [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#remove-commands-subscribers-and-forms] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#example-implementation].
B80. On 7.x core events are found as constants in each bundle's `*Events.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#available-events].
B81. Custom plugin events on 7.x: a final constants class, an event class extending `Symfony\Contracts\EventDispatcher\Event`, and `$dispatcher->dispatch($event, $name)` (event first) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#custom-events].
B82. Several 7.x dispatches are guarded by `hasListeners()` (e.g. segment filter events) [code: app/bundles/LeadBundle/Model/ListModel.php:322-324 @7.x] [code: app/bundles/LeadBundle/Segment/Query/ContactSegmentQueryBuilder.php:229-235 @7.x].
B83. 8.x dispatches by class (`dispatch($event)`); 225 constants are removed and `ApiEvents`, `ConfigEvents`, `CoreEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents`, `UserEvents` are deleted [code: 8x-changes §3.3 @8.x].
B84. 8.x keeps some constants that are no longer dispatched (Channel, Webhook builder/queue/request, Page hit, Report, Point, Stage build, Form build/submit, many LeadBundle ones); subscribers keyed on them never fire [code: 8x-changes §3.2 @8.x].
B85. Shared event classes became abstract with one concrete subclass per name; type-hinting the abstract parent still works [code: 8x-changes §3.1, §3.4 @8.x].
B86. 8.x PHPStan rules enforce single-argument dispatch and forbid services in event constructors [code: 8x-changes §3.1, §3.4 @8.x].
B87. Plugin-owned names (`batchEventName`, condition/decision `eventName`, form action/validator `eventName`) remain string-dispatched on 8.x [code: 8x-changes §3.1 @8.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:1192 @8.x].
B88. `bin/console debug:event-dispatcher <name-or-class>` shows whether a subscriber is wired [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#available-events].

## 10. Translations, assets, cache
B89. Translations are INI files `Translations/<locale>/<domain>.ini`; every plugin must include `en_US` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#translation-file-and-directory-structure].
B90. Domains: `messages` (default), `flashes`, `validators`; later sources override earlier (bundle, theme, `translations/<locale>`, `translations/overrides/<locale>`) [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#translation-file-and-directory-structure].
B91. Plugin translations are not managed in Transifex; plugins ship their own [devdocs: https://devdocs.mautic.org/en/7.2/plugins/translations.html].
B92. `Assets/js` and `Assets/css` of every bundle are discovered by `AssetGenerationHelper` [code: app/bundles/CoreBundle/Helper/AssetGenerationHelper.php:155-157 @7.x].
B93. The Plugin Manager icon is `plugins/<Bundle>/Assets/img/icon.png` (bundle) or `Assets/img/<lowercase integration name>.png` (legacy integration), falling back to `generic.png` [code: app/bundles/PluginBundle/Helper/IntegrationHelper.php:595-617 @7.x].
B94. Cache lives in `var/cache/<env>`; config changes always need a clear; translations, views and assets need one in `prod` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/cache.html].
B95. `Plugin` and `Integration` entity saves invalidate the `Plugin` and `IntegrationSettings` result-cache namespaces [code: app/bundles/PluginBundle/Entity/Plugin.php:258-264 @7.x].
B96. 8.x removes `CacheStorageHelper`; inject `CacheProviderInterface`, call `getSimpleCache()`, and treat a miss as `null` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/cache.html#replacing-cachestoragehelper].
B97. 8.x removes `Translation\TranslatorLoader` (decorator instead) [code: 8x-changes §4 Core @8.x].

## 11. Marketplace and packaging
B98. Bundled plugins declare `"type": "mautic-plugin"`, `"extra": {"install-directory-name": "<Bundle>"}` and require `mautic/core-lib ^7.0` [code: plugins/MauticCrmBundle/composer.json:1-17 @7.x].
B99. The Marketplace installs `mautic-plugin` and `mautic-theme` packages with an in-process `composer require`, and refuses other types except `mautic-resource` [code: integrations-plugins-marketplace 9.77 @7.x].
B100. UI install/remove needs `composer_updates` = true (default false), else 403; list and detail still work [code: integrations-plugins-marketplace §7 @7.x].
B101. Only installed packages of type `mautic-plugin` can be removed through the Marketplace [code: integrations-plugins-marketplace 9.79 @7.x].
B102. After a Composer install or remove the Symfony cache is cleared; running `mautic:plugins:reload` is still needed to register the plugin row [code: integrations-plugins-marketplace 9.77 @7.x] [code: bundled-plugins §0.3 @7.x].
B103. Bundling dependencies inside the plugin package is discouraged; use Composer [devdocs: https://devdocs.mautic.org/en/7.2/plugins/dependencies.html].
B104. CI `PLUGIN_DIR` must match `extra.install-directory-name` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/continuous_integration.html].

## 12. Open questions and contradictions
Q1. Docs: `config.php` service definitions "won't work in Mautic 6". Code 7.2.1: `ServicePass` still processes them; 8.x stops [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:31-64 @7.x] [code: 8x-changes §4 Core @8.x]. Resolved in favour of code.
Q2. Docs: migrations run only when the bundle extends `AbstractPluginBundle`. Code: core subscriber runs them for any plugin [code: app/bundles/PluginBundle/EventListener/PluginSubscriber.php:34-37 @7.x]. Resolved in favour of code.
Q3. Docs: permission notation `plugin:<bundle>:<level>:<perm>`. Code resolves the first segment as the permission object name; in-repo plugins use 3-part strings. A 4-part string's semantics beyond that were not traced [unverified] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x].
Q4. Docs: "executes every migration file on upgrade" vs "loops up to the latest version". Code: every file, every update, guarded only by `isApplicable()` [code: app/bundles/IntegrationsBundle/Migration/Engine.php:26-95 @7.x].
Q5. Docs: email transport tag `mautic.email_transport`/`mautic.email.transport_type` and `/mailer/{transport}/callback`. 7.x code: no such tag; Symfony Mailer transport factory; callback `/mailer/callback` [code: app/bundles/EmailBundle/Config/config.php:99-102 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-transports].
Q6. Docs: Channel broadcast under `CoreEvents::CHANNEL_BROADCAST`. Code: `ChannelEvents::CHANNEL_BROADCAST` [code: app/bundles/ChannelBundle/ChannelEvents.php:25 @7.x].
Q7. 8.0 docs list `FormEvents::FORM_ON_BUILD` as unchanged; 8.x code dispatches `FormBuilderEvent` by class with the constant kept [code: 8x-changes §3.2 @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/forms.html].
Q8. 8.0 docs say `WebhookEvent` CRUD still dispatch by constant; the 8.x constant diff removes them [code: 8x-changes §3.3 WebhookBundle @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch].
