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
- No 5.x/6.x-specific behaviour difference for this area is recorded in the inputs. The PR-history pass will add it. Treat the 7.2.1 behaviour as the baseline. [unverified]

## 7.x minors
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
