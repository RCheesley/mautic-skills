# Integrations: version notes

## History (why there are two frameworks)
- IntegrationsBundle (interface-driven, with the sync engine) was introduced in the 2.15/3.x era next to the legacy PluginBundle framework, and both still ship in 7.2.1. [code: app/bundles/IntegrationsBundle/README.md:5-19 @7.x]
- `AbstractIntegration` was marked for removal in 6.0 but survives in 7.2.1. All bundled CRMs still extend it. [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:54 @7.x]
- Activity export defaults to `point.gained, form.submitted, email.read` for pre-2.11 BC. Salesforce segment-filter values stay unprefixed for the same reason. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:178-266 @7.x] [code: plugins/MauticCrmBundle/EventListener/LeadListSubscriber.php:32-81 @7.x]

## Marketplace and Composer (4.x → 7.x)
- 4.0 introduced a read-only Marketplace. Since 4.2, install/update/remove requires the Composer setting. [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html#using-the-mautic-marketplace]
- Composer install is available since Mautic 4 and is the default install/update method since 5. [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html]
- `marketplace_registry_url` replaced the older `marketplace_api_base`. [code: app/bundles/MarketplaceBundle/Service/Config.php:32-38 @7.x]
- `mautic-resource` packages (campaign ZIPs) install without Composer. [code: app/bundles/MarketplaceBundle/Service/ResourceInstaller.php:57-121 @7.x]

## 5.x / 6.x differences
### 4.4.x (last 4.x line)
- 4.4.5/4.4.6: HubSpot authenticates with a Private App access token, and the token fields can be edited. [PR #11470] [PR #11775]
- 4.4.9: Pipedrive and Citrix show deprecation notices in the config form, notification centre and CLI. [PR #12364] [PR #12367]

### 5.0
- Pipedrive (with `mautic:integration:pipedrive:fetch|push`) and MauticCitrixBundle (with `mautic:citrix:sync`) are removed. [PR #12081] [PR #12333]
- IntegrationsBundle, PluginBundle, MarketplaceBundle and plugin templates are Twig, referenced as `@Mautic<Bundle>/...`. [PR #11862] [PR #11960] [PR #11560] [PR #12139]
- Pulled values are validated against Mautic field type and length; invalid fields are skipped with a notification, and batch-completed events fire. [PR #11303]
- New extension points: `INTEGRATION_BEFORE_CONTACT_FIELD_CHANGES`/`..._COMPANY_...`, `ConfigFormNotesInterface`, `ObjectMappingRepository` locking helpers, and `--disable-activity-push`. [PR #10512] [PR #11451] [PR #11657] [PR #11255]
- The sync and `AbstractIntegration` detach entities instead of calling `EntityManager::clear()`. The CRM version of this change inverted the `getLeadData()` check, so `pushleadactivity` pushes nothing from 5.0.0 until 7.2.2. [PR #12341] [PR #12342] [PR #12361] [PR #17815]
- Each plugin `composer.json` requires `mautic/core-lib` of the same major. [PR #11593]
- S3 accepts a custom endpoint for S3-compatible storage. [PR #11693]
- Dynamics fetches the plural `Contacts` object from 5.0.4. [PR #13208]

### 5.1 and 5.2
- One-way "to integration" fields are never cleared by a pull. [PR #11251]
- `mautic:integrations:cleanup` deletes orphan change rows. [PR #13340]
- Sync changes are attributed to the integration; same-batch duplicates reuse one Contact; `--mautic-object-id` limits the push to the named objects. [PR #13426] [PR #13435] [PR #13454]
- OAuth2 tokens can carry a default expiry, and `ConfigAuthUrlEvent` can rewrite the auth URL. [PR #13429] [PR #13434]
- Salesforce pulls DNC for new opted-out records and ignores an opt-out that was ticked then unticked (with "Use latest updated Do Not Contact record"). [PR #13411] [PR #13444]
- ConnectWise uses a Client ID instead of the appcookie credential. [PR #13408]
- 5.2: Salesforce drops a deleted SF field from the mapping and keeps syncing; logged Authorization headers are `[REDACTED]`; plugin migrations skip the commit after DDL. [PR #13406] [PR #14277] [PR #14440]

### 6.0
- An empty value for a required Mautic field skips a new object, or that field of an existing object, instead of aborting the sync. [PR #14666]
- `MauticFactory::getDatabase()` and `FieldModel::getUniqueIdentiferFields()` are removed; plugin install/update receives the connection by DI. [PR #14418] [PR #14144]
- Froala styles and Gated Video are removed. [PR #14271] [PR #14284]
- No other 6.x-only integration difference was found in the 492 PRs read. [PR #14532] [PR #14571]

## 7.x minors
- 7.0: a `PLUGIN_IS_PUBLISHED_STATE_CHANGING` listener can veto publishing, and credential changes clear tokens. IntegrationsBundle ships a test `TestPass` for HTTP mocking. [PR #13696] [PR #15084]
- 7.1: the plugin config modal shows the plugin version. [PR #15789]
- 7.2: Clearbit, Gmail and Tag Manager move to `BasicIntegration`; IntegrationsBundle DAOs without children are `final`; IntegrationsBundle services are autowired in `services.php`; legacy mapping pagination reads POST. [PR #16586] [PR #16847] [PR #16795] [PR #16888] [PR #16781] [PR #16202]
- 7.2.2: `pushleadactivity` pushes activity again. The 7.x snapshot (and 7.2.1) still contains the inverted check. [PR #17815] [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:245-254 @7.x]
- Unreleased 7.x (7.3.0-rc): duplicate tag names are refused on create and rename. [PR #17341]
- 7.2 deprecates the aliases `mautic.integrations.sync.service` and `mautic.integrations.subscriber.controller` in favour of FQCN services. [code: app/bundles/IntegrationsBundle/Config/services.php:91-94 @7.x]
- 7.2 deprecates the Clearbit alias `mautic.plugin.clearbit.lookup_helper`. [code: plugins/MauticClearbitBundle/Config/services.php:24-25 @7.x]
- In 7.2 the devdocs still name string service ids (`mautic.integrations.helper`, `mautic.integrations.auth_provider.api_key`...). [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_authentication.html]

## 8.x delta (from the 8.x branch; unreleased)
- `IntegrationEvents` is removed (23 constants), and listeners subscribe by event class. New concrete classes: `InternalContactFieldChangesEvent`, `InternalCompanyFieldChangesEvent`, `InternalContactFullReportBuildEvent`, `InternalCompanyFullReportBuildEvent`, `IntegrationToMauticSyncCompletedEvent`, `MauticToIntegrationSyncCompletedEvent`, `ConfigBeforeSaveEvent` and `ConfigAfterSaveEvent`. `InternalContactEvent`, `InternalCompanyEvent`, `CompletedSyncIterationEvent` and `ConfigSaveEvent` become abstract. [PR #17160] [PR #17654] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_integrations/integrations_sync.html#sync-events]
- `PluginEvents`: 12 constants are converted to class dispatch. `PLUGIN_ON_INTEGRATION_REQUEST`/`RESPONSE` are removed. Responses now arrive in the new `PluginIntegrationResponseEvent`, so a listener type-hinting the request event for responses gets a `TypeError`. [PR #17162] [PR #17625] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- `plugin.leadpush`: `ON_CAMPAIGN_TRIGGER_ACTION` is replaced by `ON_CAMPAIGN_BATCH_ACTION` with `PendingEvent`. [PR #17162]
- `AbstractIntegration`:
  - The 2nd constructor argument is `CacheProviderInterface`.
  - `getCache()` returns a PSR-16 cache.
  - `makeRequest()`/`prepareRequest()` take `array $parameters`.
  - About 18 methods gain `array` return types.
  - `IntegrationEntityModel::logDataSync()` is removed.
  - `AbstractSsoFormIntegration` is removed; extend `AbstractSsoServiceIntegration` and return `['sso_form']`.
  [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- IntegrationsBundle API:
  - `DefaultConfigFormTrait` is removed.
  - `MappingManualDAO` takes object mappings in its constructor, and `addObjectMapping()` is private.
  - `ConfigurationTrait::getIntegrationConfiguration()` throws `LogicException` when unset.
  - `FieldHelper` takes `FieldList`.
  - The OAuth credential interfaces `Oauth1aThreeLegged\CredentialsInterface` and `Oauth2ThreeLegged\Credentials\{AccessToken,RefreshToken,State}Interface` are removed.
  - The exceptions `IntegrationMappingException` and `InvalidProviderException` are removed.
  [PR #17184] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_integrations/integrations_sync.html]
- The service ids `mautic.integrations.helper*` are removed; use FQCNs. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_integrations/integrations_authentication.html]
- Bundled plugins:
  - Clearbit is removed (service sunset). [PR #17785]
  - `ConnectwiseIntegration`, `HubspotIntegration`, `SalesforceIntegration` and `VtigerIntegration` are `final`, and `CrmAbstractIntegration` gains array return types.
  - `HubspotApi::createLead()` validates email itself.
  - The dead route `mautic_integration_companies` is removed. [PR #17231]
  - `FullContact_Base` becomes abstract.
  [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- Plugin routes stay in `Config/config.php` `routes`; only core moves to `#[Route]` attributes. [PR #17169] [PR #17222]
- Caution: 7.2.1 fixes are not yet merged forward to 8.x, and UPGRADE-8.0.md contradicts itself about which `*Events` constants survive. The code shows `IntegrationEvents.php` deleted. [PR #17253]
- Porting rule for plugins that target both 7.x and 8.x: never reference `IntegrationEvents::` unguarded; check with `defined()`/`class_exists()`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
