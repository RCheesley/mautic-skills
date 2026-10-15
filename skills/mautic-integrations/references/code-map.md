# Integrations: code map (Mautic 7.x)

## Contents
1. Tables and entities
2. Services and helpers
3. Interfaces (modern framework)
4. Events
5. Routes and controllers
6. Commands
7. Parameters
8. Permissions
9. Tests directories

## 1. Tables and entities
| Table | Entity | Key columns / notes | Source |
|---|---|---|---|
| `plugins` | `Mautic\PluginBundle\Entity\Plugin` | `name`, `description`, `is_missing`, `bundle` (unique `unique_bundle`), `version`, `author`. The description is split on a `---` line. | [code: app/bundles/PluginBundle/Entity/Plugin.php:13,72-103,249-264 @7.x] |
| `plugin_integration_settings` | `Mautic\PluginBundle\Entity\Integration` | `plugin_id` (nullable, ON DELETE CASCADE; null = core Integration), `name`, `is_published`, `supported_features`, `api_keys` (encrypted), `feature_settings` | [code: app/bundles/PluginBundle/Entity/Integration.php:49-85 @7.x] |
| `integration_entity` | `Mautic\PluginBundle\Entity\IntegrationEntity` | legacy remote-id map; indexes `integration_external_entity`, `integration_internal_entity`, `integration_entity_match`, `integration_last_sync_date`, `internal_integration_entity` | [code: app/bundles/PluginBundle/Entity/IntegrationEntity.php:64-105 @7.x] |
| `sync_object_mapping` | `Mautic\IntegrationsBundle\Entity\ObjectMapping` | `integration`, `internal_object_name` (`lead`/`company`), `internal_object_id`, `integration_object_name`, `integration_object_id` (string), `last_sync_date`, `internal_storage` (JSON), `is_deleted`, `integration_reference_id`. No unique constraint. | [code: app/bundles/IntegrationsBundle/Entity/ObjectMapping.php:62-134 @7.x] |
| `sync_object_field_change_report` | `Mautic\IntegrationsBundle\Entity\FieldChange` | `integration`, `object_id`, `object_type` (entity FQCN), `modified_at`, `column_name`, `column_type`, `column_value` | [code: app/bundles/IntegrationsBundle/Entity/FieldChange.php:53-96 @7.x] |
| (file) `var/marketplace_installed_resources.json` | none | installed `mautic-resource` packages | [code: app/bundles/MarketplaceBundle/Service/ResourceInstaller.php:26,460-463 @7.x] |

Repositories: `IntegrationRepository::getIntegrations()` (inner join plugin), `getCoreIntegrations()`, `findOneByName()` [code: app/bundles/PluginBundle/Entity/IntegrationRepository.php:18-71 @7.x]; `IntegrationEntityRepository::findLeadsToUpdate/findLeadsToCreate/markAsDeleted` [code: app/bundles/PluginBundle/Entity/IntegrationEntityRepository.php:166-535 @7.x]; `ObjectMappingRepository` [code: app/bundles/IntegrationsBundle/Entity/ObjectMappingRepository.php:161-170 @7.x]; `FieldChangeRepository` [code: app/bundles/IntegrationsBundle/Entity/FieldChangeRepository.php:73-201 @7.x].

## 2. Services and helpers
| Class (service id) | Path | Role |
|---|---|---|
| `IntegrationHelper` (`mautic.helper.integration`) | `app/bundles/PluginBundle/Helper/IntegrationHelper.php` | legacy discovery, `getIntegrationObject($name)`, `getIntegrationObjects(...)` [code: app/bundles/PluginBundle/Helper/IntegrationHelper.php:71-309 @7.x] |
| `AbstractIntegration` | `app/bundles/PluginBundle/Integration/AbstractIntegration.php` | legacy base; auth types `none|key|oauth1a|oauth2|basic|rest|callback` [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:250 @7.x] |
| `AbstractSsoServiceIntegration` / `AbstractSsoFormIntegration` | `app/bundles/PluginBundle/Integration/` | SSO bases [code: app/bundles/PluginBundle/Integration/AbstractSsoServiceIntegration.php:34-104 @7.x] |
| `PluginModel`, `IntegrationEntityModel` | `app/bundles/PluginBundle/Model/` | plugin metadata, entity wrapper; `logDataSync()` is a no-op [code: app/bundles/PluginBundle/Model/IntegrationEntityModel.php:30-32 @7.x] |
| `ReloadHelper`, `ReloadFacade`, `PluginDatabase` | `app/bundles/PluginBundle/{Helper,Facade,Bundle}/` | install/update/missing flags, schema, migrations [code: app/bundles/PluginBundle/Facade/ReloadFacade.php:24-49 @7.x] |
| `PushToIntegrationTrait` | `app/bundles/PluginBundle/EventListener/PushToIntegrationTrait.php` | `plugin.leadpush` execution [code: app/bundles/PluginBundle/EventListener/PushToIntegrationTrait.php:44-81 @7.x] |
| `IntegrationsHelper` (`mautic.integrations.helper`) | `app/bundles/IntegrationsBundle/Helper/IntegrationsHelper.php` | registry of `mautic.basic_integration`; load/save config with encryption [code: app/bundles/IntegrationsBundle/Helper/IntegrationsHelper.php:30-116 @7.x] |
| `ConfigIntegrationsHelper`, `AuthIntegrationsHelper`, `SyncIntegrationsHelper`, `BuilderIntegrationsHelper` | `app/bundles/IntegrationsBundle/Helper/` | tagged registries [code: app/bundles/IntegrationsBundle/Helper/SyncIntegrationsHelper.php:31-131 @7.x] |
| `FieldValidationHelper`, `FieldMergerHelper`, `FieldFilterHelper`, `TokenParser`, `EncryptionService` | `app/bundles/IntegrationsBundle/{Helper,Facade}/` | config form support, tokens, encryption [code: app/bundles/IntegrationsBundle/Facade/EncryptionService.php:21-50 @7.x] |
| `SyncService` (alias `mautic.integrations.sync.service`, deprecated 7.2) | `app/bundles/IntegrationsBundle/Sync/SyncService/SyncService.php` | builds and runs `SyncProcess` [code: app/bundles/IntegrationsBundle/Config/services.php:91-94 @7.x] |
| `SyncProcess`, `IntegrationSyncProcess`, `MauticSyncProcess`, `ObjectChangeGenerator`s | `app/bundles/IntegrationsBundle/Sync/SyncProcess/` | orchestration and per-direction orders |
| `MauticSyncDataExchange` (`NAME='mautic'`, `OBJECT_CONTACT='lead'`, `OBJECT_COMPANY='company'`) | `app/bundles/IntegrationsBundle/Sync/SyncDataExchange/MauticSyncDataExchange.php` | Mautic side [code: app/bundles/IntegrationsBundle/Sync/SyncDataExchange/MauticSyncDataExchange.php:28-32 @7.x] |
| `FullObjectReportBuilder`, `PartialObjectReportBuilder`, `FieldBuilder`, `OrderExecutioner`, `FieldValidator`, `ReferenceResolver`, `ContactObjectHelper`, `CompanyObjectHelper` | `app/bundles/IntegrationsBundle/Sync/SyncDataExchange/Internal/` | Mautic reports and order execution |
| `MappingHelper`, `SyncDateHelper`, `RelationsHelper` | `app/bundles/IntegrationsBundle/Sync/Helper/` | mapping table, windows, relations |
| `SyncJudge` (`mautic.integrations.helper.sync_judge`) + `Modes/{HardEvidence,BestEvidence,FuzzyEvidence}` | `app/bundles/IntegrationsBundle/Sync/SyncJudge/` | conflict resolution |
| Notification `Notifier`, handlers (tag `mautic.sync.notification_handler`) | `app/bundles/IntegrationsBundle/Sync/Notification/` | sync issues |
| Auth `HttpFactory` per provider, `TokenPersistence(Factory)`, `IntegrationToken(Factory)` | `app/bundles/IntegrationsBundle/Auth/` | Guzzle clients and OAuth2 tokens |
| `Migration\Engine`, `AbstractMigration` | `app/bundles/IntegrationsBundle/Migration/` | plugin migrations |
| `ComposerHelper` | `app/bundles/CoreBundle/Helper/ComposerHelper.php` | in-process Composer [code: app/bundles/CoreBundle/Helper/ComposerHelper.php:32-169 @7.x] |
| `Config` (`marketplace.service.config`), `Connection`, `PluginCollector`, `PackageModel`, `ResourceInstaller`, `RouteProvider` | `app/bundles/MarketplaceBundle/{Service,Api,Model}/` | Marketplace |

## 3. Interfaces (modern framework)
Path: `app/bundles/IntegrationsBundle/Integration/Interfaces/`. [code: app/bundles/IntegrationsBundle/Form/Type/IntegrationConfigType.php:32-88 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_configuration.html]
| Interface | Methods / purpose | Tag |
|---|---|---|
| `IntegrationInterface`, `BasicInterface` | `getName()`, `getDisplayName()`, `getIcon()` | `mautic.integration`, `mautic.basic_integration` (auto) |
| `ConfigFormInterface` | `getConfigFormName()`, `getConfigFormContentTemplate()` (null = default) | `mautic.config_integration` (auto) |
| `ConfigFormAuthInterface` | `getAuthConfigFormName()`: Enabled/Auth tab, values encrypted | - |
| `ConfigFormFeaturesInterface` | `getSupportedFeatures()`; `FEATURE_SYNC='sync'`, `FEATURE_PUSH_ACTIVITY='push_activity'` | - |
| `ConfigFormFeatureSettingsInterface` | `getFeatureSettingsConfigFormName()`: Features tab, not encrypted | - |
| `ConfigFormSyncInterface` | `getSyncConfigObjects()`, mappable/required fields, optional `getSyncConfigFormName()` | - |
| `ConfigFormAuthorizeButtonInterface`, `ConfigFormCallbackInterface`, `ConfigFormNotesInterface` | Authorize button / callback help key / `Note` objects | - |
| `SyncInterface` | `getMappingManual()`, `getSyncDataExchange()` | `mautic.sync_integration` (manual) |
| `AuthenticationInterface` | `isAuthenticated(): bool`, `authenticateIntegration(Request): string` | `mautic.authentication_integration` (manual) [code: app/bundles/IntegrationsBundle/Integration/Interfaces/AuthenticationInterface.php:9-21 @7.x] |
| `BuilderInterface` | `isSupported($feature)` (`email`, `page`) | `mautic.builder_integration` (auto) |
| `SyncDataExchangeInterface` | `getSyncReport(RequestDAO): ReportDAO`, `executeSyncOrder(OrderDAO)` | - |
Traits: `ConfigurationTrait`, `DefaultConfigFormTrait`, `ConfigFormNotesTrait`. [code: app/bundles/IntegrationsBundle/Integration/ConfigurationTrait.php:13-26 @7.x]

## 4. Events
### PluginEvents (`app/bundles/PluginBundle/PluginEvents.php`)
| Constant | Event | Dispatched |
|---|---|---|
| `PLUGIN_ON_INTEGRATION_CONFIG_SAVE` | `PluginIntegrationEvent` | legacy config POST, only if listeners [code: app/bundles/PluginBundle/Controller/PluginController.php:255-264 @7.x] |
| `PLUGIN_ON_INTEGRATION_KEYS_ENCRYPT/DECRYPT/MERGE` | `PluginIntegrationKeyEvent` | [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:374-440 @7.x] |
| `PLUGIN_ON_INTEGRATION_REQUEST` / `_RESPONSE` | `PluginIntegrationRequestEvent` | around `makeRequest()` [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:670-673,822-826 @7.x] |
| `PLUGIN_ON_INTEGRATION_AUTH_REDIRECT`, `PLUGIN_ON_INTEGRATION_GET_AUTH_CALLBACK_URL` | auth URL rewrites (stop propagation on set) | [code: app/bundles/PluginBundle/Controller/AuthController.php:104-110 @7.x] |
| `PLUGIN_ON_INTEGRATION_FORM_DISPLAY` / `_FORM_BUILD` | form hooks | [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:2058-2102 @7.x] |
| `ON_CAMPAIGN_TRIGGER_ACTION` | `CampaignExecutionEvent` for `plugin.leadpush` | [code: app/bundles/PluginBundle/EventListener/CampaignSubscriber.php:24-57 @7.x] |
| `ON_FORM_SUBMIT_ACTION_TRIGGERED` | never dispatched | [code: app/bundles/PluginBundle/PluginEvents.php:119 @7.x] |
| `ON_PLUGIN_INSTALL` / `ON_PLUGIN_UPDATE` | schema create / migrations | [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:83-119 @7.x] |
| `PLUGIN_IS_PUBLISHED_STATE_CHANGING` | `PluginIsPublishedEvent` (veto) | [code: app/bundles/PluginBundle/Form/Constraint/CanPublishValidator.php:29-30 @7.x] |

### IntegrationEvents (`app/bundles/IntegrationsBundle/IntegrationEvents.php`; removed in 8.x)
| Constant | Event | Use |
|---|---|---|
| `INTEGRATION_CONFIG_FORM_LOAD`, `_CONFIG_BEFORE_SAVE`, `_CONFIG_AFTER_SAVE`, `_CONFIG_ON_GENERATE_AUTH_URL`, `INTEGRATION_API_KEYS_BEFORE_SAVE` | `FormLoadEvent`, `ConfigSaveEvent`, `ConfigAuthUrlEvent`, `KeysSaveEvent` | config modal [code: app/bundles/IntegrationsBundle/Controller/ConfigController.php:69-256 @7.x] |
| `INTEGRATION_KEYS_BEFORE_ENCRYPTION` / `_AFTER_DECRYPTION` | `KeysEncryptionEvent` / `KeysDecryptionEvent` | [code: app/bundles/IntegrationsBundle/Helper/IntegrationsHelper.php:70-108 @7.x] |
| `INTEGRATION_MAUTIC_SYNC_FIELDS_LOAD` | `MauticSyncFieldsLoadEvent` | add Mautic sync fields [code: app/bundles/IntegrationsBundle/Sync/SyncDataExchange/Helper/FieldHelper.php:107-108 @7.x] |
| `INTEGRATION_COLLECT_INTERNAL_OBJECTS`, `_CREATE_`, `_UPDATE_INTERNAL_OBJECTS`, `_FIND_INTERNAL_RECORDS`, `_FIND_INTERNAL_RECORD`, `_FIND_OWNER_IDS`, `_BUILD_INTERNAL_OBJECT_ROUTE` | `Internal*Event` | internal object plumbing; Contact/Company subscribers implement them [code: app/bundles/IntegrationsBundle/EventListener/ContactObjectSubscriber.php:46-166 @7.x] |
| `INTEGRATION_BEFORE_CONTACT/COMPANY_FIELD_CHANGES` | `InternalContactEvent`/`InternalCompanyEvent` | veto tracking |
| `INTEGRATION_BEFORE_FULL_CONTACT/COMPANY_REPORT_BUILD` | same | veto full report |
| `INTEGRATION_BATCH_SYNC_COMPLETED_INTEGRATION_TO_MAUTIC` / `_MAUTIC_TO_INTEGRATION` | `CompletedSyncIterationEvent` | after each batch [code: app/bundles/IntegrationsBundle/Sync/SyncProcess/SyncProcess.php:132-135,202-205 @7.x] |
| `INTEGRATION_POST_EXECUTE` | `SyncEvent` | after the run |
| `INTEGRATION_OBJECT_TOKEN_EVENT` | `MappedIntegrationObjectTokenEvent` | email builder tokens |

Listened-to core events: LeadBundle post-save/delete/company-change (tracking, cleanup), `KernelEvents::CONTROLLER` (config reroute), Email build/send/display (tokens), timeline, `VIEW_INJECT_CUSTOM_TEMPLATE` (Contact Integrations tab), `BUILD_MENU` (Marketplace). [code: app/bundles/IntegrationsBundle/EventListener/LeadSubscriber.php:38-47 @7.x] [code: app/bundles/IntegrationsBundle/EventListener/UIContactIntegrationsTabSubscriber.php:21-56 @7.x]

## 5. Routes and controllers
| Route | Path | Controller | Source |
|---|---|---|---|
| `mautic_plugin_index` | `/s/plugins` | `PluginController::indexAction` | [code: app/bundles/PluginBundle/Config/config.php:6-47 @7.x] |
| `mautic_plugin_config` | `/s/plugins/config/{name}/{page}` | legacy config (rerouted for modern) | same |
| `mautic_plugin_info`, `mautic_plugin_reload` | `/s/plugins/info/{name}`, `/s/plugins/reload` | info modal, reload | same |
| `mautic_integration_auth_user` / `_callback` / `_postauth` (public + `_secure`) | `/plugins/integrations/{authuser,authcallback,authstatus}/{integration}` | `AuthController` | same |
| AJAX `plugin:setIntegrationFilter|getIntegrationFields|getIntegrationConfig|getIntegrationCampaignStatus|matchFields` | `/s/ajax` | `PluginBundle\Controller\AjaxController` | [code: app/bundles/PluginBundle/Controller/AjaxController.php:27-279 @7.x] |
| `mautic_integration_config` | `/s/integration/{integration}/config` | `ConfigController::editAction` | [code: app/bundles/IntegrationsBundle/Config/config.php:9-33 @7.x] |
| `mautic_integration_config_field_pagination` / `_field_update` | `/s/integration/{integration}/config/{object}/{page}` / `.../field/{field}` | `FieldPaginationController`, `UpdateFieldController` | same |
| `mautic_integration_public_callback` | `/integration/{integration}/callback` (public) | `IntegrationsBundle\Controller\AuthController::callbackAction` | same |
| `mautic_marketplace_list|detail|install|remove|clear_cache` | `/s/marketplace/{page}`, `/detail/{vendor}/{package}`, `/install/...`, `/remove/...`, `/clear/cache` | `MarketplaceBundle\Controller\Package\*` | [code: app/bundles/MarketplaceBundle/Config/config.php:9-38 @7.x] |
| `mautic_integration_contacts` | `/plugin/{integration}/contact_data` (public, HubSpot webhook) | `MauticCrmBundle\Controller\PublicController` | [code: plugins/MauticCrmBundle/Config/config.php:12-18 @7.x] |
| `mautic_plugin_tracker` | `/plugin/{integration}/tracking.gif` (Gmail/Outlook) | `EmailBundle\Controller\PublicController::pluginTrackingGifAction` | [code: app/bundles/EmailBundle/Config/config.php:65-71 @7.x] |

## 6. Commands
| Command | Source |
|---|---|
| `mautic:integrations:sync <integration> [options]` | [code: app/bundles/IntegrationsBundle/Command/SyncCommand.php:31-126 @7.x] |
| `mautic:integrations:cleanup` | [code: app/bundles/IntegrationsBundle/Command/CleanupCommand.php:14-37 @7.x] |
| `mautic:integration:fetchleads` (alias `mautic:integration:synccontacts`) | [code: app/bundles/PluginBundle/Command/FetchLeadsCommand.php:33-285 @7.x] |
| `mautic:integration:pushleadactivity` (alias `mautic:integration:pushactivity`) | [code: app/bundles/PluginBundle/Command/PushLeadActivityCommand.php:13-91 @7.x] |
| `mautic:plugins:reload` (aliases `:install`, `:update`) | [code: app/bundles/PluginBundle/Command/ReloadCommand.php:13-35 @7.x] |
| `mautic:marketplace:list [-p 1] [-l 15] [-f]`, `mautic:marketplace:install <vendor/name> [--dry-run] [--user-id]`, `mautic:marketplace:remove <vendor/name>` | [code: app/bundles/MarketplaceBundle/Command/ListCommand.php:16-69 @7.x] [code: app/bundles/MarketplaceBundle/Command/InstallCommand.php:48-160 @7.x] [code: app/bundles/MarketplaceBundle/Command/RemoveCommand.php:18-106 @7.x] |

## 7. Parameters
| Parameter | Default | Source |
|---|---|---|
| `marketplace_enabled` | `true` | [code: app/bundles/MarketplaceBundle/Config/config.php:40-44 @7.x] |
| `marketplace_website_url` | `https://marketplace.mautic.org` | same |
| `marketplace_registry_url` | `https://marketplace.mautic.org` (replaces old `marketplace_api_base`) | same; [code: app/bundles/MarketplaceBundle/Service/Config.php:32-38 @7.x] |
| `composer_updates` (UI: "Update Mautic through Composer") | `false` | [code: app/bundles/CoreBundle/Config/config.php:807 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#update-settings] |
Env override: `MAUTIC_<NAME>`, e.g. `MAUTIC_COMPOSER_UPDATES`. [code: app/config/parameters.php:16-47 @7.x] PluginBundle and IntegrationsBundle declare no parameters.

## 8. Permissions
- `plugin:plugins:manage`: plugin grid, legacy and modern config, field pagination. [code: app/bundles/PluginBundle/Controller/PluginController.php:41,141,371,409 @7.x] [code: app/bundles/IntegrationsBundle/Controller/ConfigController.php:58-60 @7.x]
- `marketplace:packages:view|create|remove` (+ standard `edit|delete|full`), hidden when the Marketplace is disabled. [code: app/bundles/MarketplaceBundle/Security/Permissions/MarketplacePermissions.php:12-50 @7.x]

## 9. Tests directories
`app/bundles/PluginBundle/Tests/`, `app/bundles/IntegrationsBundle/Tests/{Unit,Functional}/`, `app/bundles/MarketplaceBundle/Tests/{Functional,ApiResponse}/`, `plugins/MauticCrmBundle/Tests/`, `plugins/MauticClearbitBundle/Tests/`, `plugins/MauticGmailBundle/Tests/`, `plugins/MauticOutlookBundle/Tests/`. No Codeception coverage. [code: tests/acceptance/ContactManagementCest.php @7.x]
