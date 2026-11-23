# Plugin development — code map (7.x, the 7.x snapshot pinned in SOURCES.md)

All paths relative to the Mautic repository root. 8.x notes marked `@8.x`.

## 1. Discovery and metadata
| What | Where | Notes |
|---|---|---|
| Plugin bundle scan | `app/AppKernel.php:158-187` | depth-1 `*Bundle.php`, `MauticPlugin\<dir>\<file>`, `MINIMUM_MAUTIC_VERSION` [code: app/AppKernel.php:158-187 @7.x] |
| Local extra bundles | `config/bundles_local.php` via `app/AppKernel.php:199-202` | [code: app/AppKernel.php:199-202 @7.x] |
| Bundle metadata | `app/bundles/CoreBundle/DependencyInjection/Builder/BundleMetadataBuilder.php:53-133`, `BundleMetadata.php` | `isPlugin`, `base`, `directory`, `namespace`, `config`, `permissionClasses` [code: app/bundles/CoreBundle/DependencyInjection/Builder/BundleMetadataBuilder.php:53-119 @7.x] |
| `config.php` parser | `app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/ConfigMetadata.php:17-116` | routes, menu, services, parameters, ip_lookup_services [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/ConfigMetadata.php:17-116 @7.x] |
| Permission class scan | `app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/PermissionClassMetadata.php:20-49` | [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/PermissionClassMetadata.php:20-49 @7.x] |
| Container params | `mautic.bundles`, `mautic.plugin.bundles` in `app/config/config.php:22-23` | [code: app/config/config.php:22-23 @7.x] |
| Bundle base classes | `app/bundles/PluginBundle/Bundle/PluginBundleBase.php:9-14`; `app/bundles/IntegrationsBundle/Bundle/AbstractPluginBundle.php:12` | [code: app/bundles/IntegrationsBundle/Bundle/AbstractPluginBundle.php:12 @7.x] |

## 2. Services and DI
| What | Where | Notes |
|---|---|---|
| Default autowiring for bundles without `services.php` | `app/config/services.php:10-32` | [code: app/config/services.php:10-32 @7.x] |
| Excluded directories | `MauticCoreExtension::DEFAULT_EXCLUDES` in `app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-29` | [code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-29 @7.x] |
| `config.php` `services` processing | `app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:24-254` | removed @8.x [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:31-64 @7.x] [code: UPGRADE-8.0.md:205,1108 @8.x] [PR #17116] |
| Other compiler passes | `app/bundles/CoreBundle/DependencyInjection/Compiler/{ModelPass,PermissionsPass,TwigPass,TranslationsPass,...}.php` | `ModelPass`, `PermissionsPass`, `TwigPass` removed @8.x [PR #17133] [PR #17121] [PR #17117] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ @8.x] |
| Plugin extension example | `plugins/MauticCrmBundle/DependencyInjection/MauticCrmExtension.php:12-22` | [code: plugins/MauticCrmBundle/DependencyInjection/MauticCrmExtension.php:12-22 @7.x] |
| Plugin `services.php` examples | `plugins/MauticTagManagerBundle/Config/services.php`, `plugins/MauticCrmBundle/Config/services.php:10-35`, `plugins/MauticClearbitBundle/Config/services.php:8-26` (Clearbit is removed on 8.x [code: UPGRADE-8.0.md:33 @8.x]) | [code: plugins/MauticTagManagerBundle/Config/services.php:9-28 @7.x] [code: plugins/MauticCrmBundle/Config/services.php:10-35 @7.x] [code: plugins/MauticClearbitBundle/Config/services.php:8-26 @7.x] |
| Integration autotagging | `app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:26-33` | [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:26-33 @7.x] |
| SMS transport collection | `app/bundles/SmsBundle/DependencyInjection/Compiler/SmsTransportPass.php` | tag `mautic.sms_transport` [code: app/bundles/SmsBundle/DependencyInjection/Compiler/SmsTransportPass.php @7.x] |
| Email stat helpers / transport factory | `app/bundles/EmailBundle/Config/services.php:47-63`; `app/bundles/EmailBundle/Mailer/Transport/TransportFactory.php` | tag `mautic.email_stat_helper`; decorates `mailer.transport_factory` [code: app/bundles/EmailBundle/Config/services.php:47-63 @7.x] |

## 3. Routing, menus, controllers
| What | Where | Notes |
|---|---|---|
| Route loader | `app/bundles/CoreBundle/Loader/RouteLoader.php:28-84` | firewalls public, main (`/s`), api (`/api`), catchall [code: app/bundles/CoreBundle/Loader/RouteLoader.php:28-84 @7.x] |
| Route event | `CoreEvents::BUILD_ROUTE` (`app/bundles/CoreBundle/CoreEvents.php:25`), `RouteEvent` | [code: app/bundles/CoreBundle/CoreEvents.php:25 @7.x] |
| Menu structure | `app/bundles/CoreBundle/Menu/MenuHelper.php:32-177` | default priority 9999 [code: app/bundles/CoreBundle/Menu/MenuHelper.php:32,142,177 @7.x] |
| Base controllers | `Mautic\CoreBundle\Controller\CommonController`, `FormController` (removed @8.x), `AbstractFormController`, `AbstractStandardFormController`, `AjaxController`; API `Mautic\ApiBundle\Controller\CommonApiController` | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html] [code: UPGRADE-8.0.md:243 @8.x] [PR #17481] |
| Asset discovery | `app/bundles/CoreBundle/Helper/AssetGenerationHelper.php:155-157` | [code: app/bundles/CoreBundle/Helper/AssetGenerationHelper.php:155-157 @7.x] |

## 4. Permissions
| What | Where | Notes |
|---|---|---|
| Base class | `app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php` | `definePermissions()` (removed @8.x), `getName()`, `buildForm()`, `getSynonym()`, `isGranted()`, `analyzePermissions()` [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:15-214 @7.x] |
| Resolver | `app/bundles/CoreBundle/Security/Permissions/CorePermissions.php` | `isGranted()` 210-262, object lookup 79-104, fallback 446-462 [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:79-104,210-262,446-462 @7.x] |
| Tag registration | `app/bundles/CoreBundle/DependencyInjection/Compiler/PermissionsPass.php:12-20` | tag `mautic.permissions` [code: app/bundles/CoreBundle/DependencyInjection/Compiler/PermissionsPass.php:12-20 @7.x] |
| Plugin example | `plugins/MauticTagManagerBundle/Security/Permissions/TagManagerPermissions.php`; `plugins/MauticFocusBundle/Security/Permissions/FocusPermissions.php` (`getName()` = `focus`) | [code: plugins/MauticFocusBundle/Security/Permissions/FocusPermissions.php:20-22 @7.x] |
| Plugin Manager permission | `plugin:plugins:manage` (`app/bundles/PluginBundle/Security/Permissions/PluginPermissions.php:13-27`) | [code: app/bundles/PluginBundle/Security/Permissions/PluginPermissions.php:13-27 @7.x] |

## 5. Lifecycle (reload, install, update) and schema
| What | Where | Notes |
|---|---|---|
| Command | `app/bundles/PluginBundle/Command/ReloadCommand.php:13-35` — `mautic:plugins:reload` (aliases `mautic:plugins:install`, `mautic:plugins:update`) | [code: app/bundles/PluginBundle/Command/ReloadCommand.php:13-35 @7.x] |
| Facade | `app/bundles/PluginBundle/Facade/ReloadFacade.php:24-49` | order of operations [code: app/bundles/PluginBundle/Facade/ReloadFacade.php:24-49 @7.x] |
| Helper | `app/bundles/PluginBundle/Helper/ReloadHelper.php` — disable 26-39, update 67-95, install 102-126, config mapping 128-153 | [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:26-153 @7.x] |
| Core install/update subscriber | `app/bundles/PluginBundle/EventListener/PluginSubscriber.php:20-37` | [code: app/bundles/PluginBundle/EventListener/PluginSubscriber.php:20-37 @7.x] |
| Schema helper | `app/bundles/PluginBundle/Bundle/PluginDatabase.php` — `installPluginSchema()` 35-75 (skips tables that already exist, unreleased 7.3 [PR #17977]), `onPluginUpdate()` 80-90, `dropPluginSchema()` 95-113 (no caller) | [code: app/bundles/PluginBundle/Bundle/PluginDatabase.php:35-113 @7.x] |
| Migration engine | `app/bundles/IntegrationsBundle/Migration/Engine.php:26-95` | [code: app/bundles/IntegrationsBundle/Migration/Engine.php:26-95 @7.x] |
| Migration base | `app/bundles/IntegrationsBundle/Migration/AbstractMigration.php:17-127` | [code: app/bundles/IntegrationsBundle/Migration/AbstractMigration.php:17-127 @7.x] |
| Events | `app/bundles/PluginBundle/PluginEvents.php` — `ON_PLUGIN_UPDATE` :128, `ON_PLUGIN_INSTALL` :137, `PLUGIN_IS_PUBLISHED_STATE_CHANGING` :146 (all three removed @8.x, use the event classes) | [code: app/bundles/PluginBundle/PluginEvents.php:128,137,146 @7.x] [code: app/bundles/PluginBundle/PluginEvents.php:14-36 @8.x] |
| Event classes | `app/bundles/PluginBundle/Event/{PluginInstallEvent,PluginUpdateEvent,PluginIsPublishedEvent}.php` | [code: app/bundles/PluginBundle/Event/PluginUpdateEvent.php:12-50 @7.x] |
| Plugin Manager UI | `app/bundles/PluginBundle/Controller/PluginController.php` (`/s/plugins`, info modal, reload action) | [code: app/bundles/PluginBundle/Config/config.php:17-29 @7.x] [code: app/bundles/PluginBundle/Controller/PluginController.php:409 @7.x] |

## 6. Tables
| Table | Entity | Key columns |
|---|---|---|
| `plugins` | `Mautic\PluginBundle\Entity\Plugin` | `id`, `name`, `description`, `is_missing`, `bundle` (unique `unique_bundle`, string 50), `version`, `author` [code: app/bundles/PluginBundle/Entity/Plugin.php:72-103 @7.x] |
| `plugin_integration_settings` | `Mautic\PluginBundle\Entity\Integration` | `plugin_id` (nullable, cascade), `name`, `is_published`, `supported_features`, `api_keys` (encrypted), `feature_settings` [code: app/bundles/PluginBundle/Entity/Integration.php:49-85 @7.x] |
| Plugin-owned tables | your `Entity/` classes | created on install from metadata; prefixed with `MAUTIC_TABLE_PREFIX`; on 7.x an `Entity/` directory is mapped only if a class has `loadMetadata()`, on 8.x attribute-only entities are mapped too [code: app/bundles/PluginBundle/Bundle/PluginDatabase.php:35-75 @7.x] [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/EntityMetadata.php:58-66 @7.x] [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/EntityMetadata.php:61-71 @8.x] |

## 7. Commands relevant to plugin work
| Command | Purpose | Source |
|---|---|---|
| `bin/console mautic:plugins:reload` | install/update/flag plugins | [code: app/bundles/PluginBundle/Command/ReloadCommand.php:13-35 @7.x] |
| `bin/console cache:clear --env=<env>` / `mautic:cache:clear` | rebuild container / clear Mautic cache | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/cache.html] |
| `bin/console debug:router`, `debug:event-dispatcher` | verify routes and subscribers | [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#available-events] |
| `bin/console lint:twig plugins/<Bundle>` | Twig syntax | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html#rendering-views] |
| `bin/console mautic:marketplace:install|remove|list` | Marketplace via CLI | [code: app/bundles/MarketplaceBundle/Command/InstallCommand.php @7.x] [code: app/bundles/MarketplaceBundle/Command/RemoveCommand.php @7.x] [code: app/bundles/MarketplaceBundle/Command/ListCommand.php @7.x] |

## 8. Configuration parameters touching plugins
| Parameter | Default | Effect | Source |
|---|---|---|---|
| `composer_updates` | `false` | gates Marketplace plugin install/remove in UI | [code: app/bundles/CoreBundle/Config/config.php:807 @7.x] |
| `marketplace_enabled` | `true` | Marketplace pages and menu | [code: app/bundles/MarketplaceBundle/Config/config.php:41 @7.x] [code: app/bundles/MarketplaceBundle/Service/Config.php:24 @7.x] |
| `marketplace_registry_url` | `https://marketplace.mautic.org` | registry API base | [code: app/bundles/MarketplaceBundle/Config/config.php:43 @7.x] |
| your plugin `parameters` | as declared | `%mautic.<key>%`, env `MAUTIC_<KEY>` | [code: app/config/parameters.php:16-47 @7.x] |

## 9. Event constant files (7.x) used by plugins
`app/bundles/CoreBundle/CoreEvents.php`, `CampaignBundle/CampaignEvents.php`, `FormBundle/FormEvents.php`, `LeadBundle/LeadEvents.php`, `EmailBundle/EmailEvents.php`, `PageBundle/PageEvents.php`, `PointBundle/PointEvents.php`, `StageBundle/StageEvents.php`, `ReportBundle/ReportEvents.php`, `DashboardBundle/DashboardEvents.php`, `WebhookBundle/WebhookEvents.php`, `ChannelBundle/ChannelEvents.php`, `ApiBundle/ApiEvents.php`, `ConfigBundle/ConfigEvents.php`, `CategoryBundle/CategoryEvents.php`, `PluginBundle/PluginEvents.php`, `SmsBundle/SmsEvents.php`; on 8.x `CoreEvents`, `ApiEvents`, `ConfigEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents`, `UserEvents` do not exist [code: UPGRADE-8.0.md:102,121,447-474 @8.x] [PR #17654] [PR #17625] [PR #17241]. Full mapping: [extension-points.md](extension-points.md).

## 10. Reference plugins in the tree
| Plugin | Shows | Source |
|---|---|---|
| `plugins/MauticTagManagerBundle/` | entity + repository, routes, menu, permissions, modern integration, unit tests | [code: plugins/MauticTagManagerBundle/Config/config.php:5-41 @7.x] |
| `plugins/MauticFocusBundle/` | campaign action, categories, permissions, functional tests | [code: plugins/MauticFocusBundle/Config/config.php:51-63 @7.x] |
| `plugins/MauticZapierBundle/` | minimal plugin: bundle class, `Config/config.php`, `Config/services.php`, `DependencyInjection` extension, icon, `composer.json` | [code: plugins/MauticZapierBundle/MauticZapierBundle.php @7.x] [code: plugins/MauticZapierBundle/DependencyInjection/MauticZapierExtension.php @7.x] |
| `plugins/MauticCrmBundle/` | legacy integrations, `PluginSubscriber` calling `installPluginSchema()` | [code: plugins/MauticCrmBundle/EventListener/PluginSubscriber.php:22-55 @7.x] |
| `plugins/GrapesJsBuilderBundle/` | builder integration (`BuilderInterface`) | [code: plugins/GrapesJsBuilderBundle/Integration/Support/BuilderSupport.php:10 @7.x] |

## 11. Tests
| Test | Covers | Source |
|---|---|---|
| `app/bundles/PluginBundle/Tests/Helper/ReloadHelperTest.php` | disable/enable/update/install rules | [code: app/bundles/PluginBundle/Tests/Helper/ReloadHelperTest.php:83-160 @7.x] |
| `app/bundles/PluginBundle/Tests/Helper/PluginBundleBaseStub.php` | stub bundle for helper tests | [code: app/bundles/PluginBundle/Tests/Helper/PluginBundleBaseStub.php @7.x] |
| `app/bundles/PluginBundle/Tests/Controller/PluginControllerTest.php` | `/s/plugins/info/MauticFocusBundle` after `mautic:plugins:install` | [code: app/bundles/PluginBundle/Tests/Controller/PluginControllerTest.php:50-52 @7.x] |
| `app/bundles/PluginBundle/Tests/Functional/Command/ReloadCommandFunctionalTest.php` | first reload of an entity plugin when `messenger_messages` already exists (unreleased 7.3) | [code: app/bundles/PluginBundle/Tests/Functional/Command/ReloadCommandFunctionalTest.php:37 @7.x] [PR #17977] |
| `app/bundles/CoreBundle/Tests/Unit/DependencyInjection/Builder/BundleMetadataBuilderTest.php` | plugin metadata shape | [code: app/bundles/CoreBundle/Tests/Unit/DependencyInjection/Builder/BundleMetadataBuilderTest.php:59-82 @7.x] |
| `app/bundles/SmsBundle/Tests/DependencyInjection/Compiler/SmsTransportPassTest.php` | tagged transport collection | [code: app/bundles/SmsBundle/Tests/DependencyInjection/Compiler/SmsTransportPassTest.php @7.x] |
| `plugins/*/Tests/` | plugin-level unit and functional tests (TagManager, Focus, CRM, Gmail, Outlook) | [code: app/phpunit.xml.dist:23,53 @7.x] |
| (none) | `Migration\Engine`, `AbstractMigration` | no test references them [code: grep app/bundles/*/Tests @7.x] |
