# Integrations: what the official docs say (7.2, with 8.0 changes)

All six developer pages under `plugin_integrations/` carry the banner "requires a major update... potentially inaccurate", and five of them are orphan pages. Prefer the code where they disagree. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations.html]

## Terminology
- "Plugin" = the Mautic package; "Integration" = the configured connection/class. Both are capitalised. [docs: https://docs.mautic.org/en/7.2/plugins/plugin_resources.html]
- Config tabs are named "Enabled/Auth", "Features" and "Contact Field Mapping". The buttons are "Install/Upgrade Plugins", "Save & Close", "Authorize"/"Reauthorize" and "Push Contact to Integration". [docs: https://docs.mautic.org/en/7.2/plugins/hubspot.html#configure-the-hubspot-crm-plugin]
- Dev-doc sync terms are "Sync Engine", "sync report", "sync order", "sync judge", "mapping manual" and "sync data exchange". [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_sync.html]
- The MailChimp docs call a MailChimp list a "Segment"; do not confuse it with a Mautic Segment. [docs: https://docs.mautic.org/en/7.2/plugins/mailchimp.html#configure-the-plugin]

## User procedures
- **Install plugins**: Settings > Plugins > Install/Upgrade Plugins. If a new third-party plugin is missing, clear the cache and click again. [docs: https://docs.mautic.org/en/7.2/plugins/plugin_resources.html#install-plugins]
- **A coloured icon means active.** [docs: https://docs.mautic.org/en/7.2/plugins/amazon.html#setting-up-s3-in-mautic]
- **Test an Integration**:
  1. Build a Form with `email` and `firstname`.
  2. Add the action Push Contact to Integration.
  3. Submit the public Form.
  4. Check the remote system.
  If `firstname` is missing, check the Form's "Save result" option and the field mapping. [docs: https://docs.mautic.org/en/7.2/plugins/plugin_resources.html#how-to-test-an-integration]
- **Field mapping**: you only need to map the fields you want pushed. [docs: https://docs.mautic.org/en/7.2/plugins/plugin_resources.html#field-mapping]
- **HubSpot**:
  1. Create a private app token and paste it into "HubSpot API key".
  2. Set Features.
  3. Save & Close, then reopen to map fields.
  4. Activate.
  5. Add the cron `mautic:integration:fetchleads --integration=Hubspot --fetch-all`.
  [docs: https://docs.mautic.org/en/7.2/plugins/hubspot.html#configure-the-hubspot-crm-plugin]
- **MailChimp**: enter the username and API key, choose the list, save, reopen and map fields. The options are push, double opt-in and welcome Email. [docs: https://docs.mautic.org/en/7.2/plugins/mailchimp.html]
- **Zoho**:
  1. Set both accounts to English.
  2. Create a Server Based Application with callback `https://<mautic>/plugins/integrations/authcallback/Zoho`.
  3. Pick the data centre.
  4. Authorize.
  5. Set Features ("Update blank values", objects).
  6. Add a cron job.
  [docs: https://docs.mautic.org/en/7.2/plugins/zoho_crm.html]
- **Vtiger**: enable the Contacts module in Vtiger Cloud. The URL is the base URL for Cloud, or the base URL plus `/webservice.php` for Open Source. [docs: https://docs.mautic.org/en/7.2/plugins/vtiger.html#authenticate-the-vtiger-plugin]
- **Clearbit**: needs a public URL (it does not work on localhost) and an API key. The lookup runs from Contact/Company toolbar buttons. [docs: https://docs.mautic.org/en/7.2/plugins/clearbit.html]
- **Salesforce**: the page only links to the KB. ConnectWise, FullContact, iContact, Dynamics, Outlook, Pipedrive, SugarCRM, Twitter and Zapier pages are title only. [docs: https://docs.mautic.org/en/7.2/plugins/salesforce.html] [docs: https://docs.mautic.org/en/7.2/plugins/connectwise.html]

## Developer docs (IntegrationsBundle)
- Register a class tagged `mautic.basic_integration` that implements `BasicInterface` (usually by extending `BasicIntegration`). The `NAME` must contain only letters. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations.html#registering-the-integration]
- Config: `ConfigFormInterface` (+ `DefaultConfigFormTrait`). Auth-tab values are encrypted, while Features-tab values are not. `FEATURE_SYNC='sync'` and `FEATURE_PUSH_ACTIVITY='push_activity'`. `ConfigFormNotesInterface` returns `Note` objects of `TYPE_INFO`/`TYPE_WARNING`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_configuration.html] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_configuration_form_notes.html]
- Auth providers:
  - API key, as a parameter or a header.
  - Basic.
  - OAuth1a two-legged; three-legged is not implemented.
  - OAuth2 three-legged (`code`, `refresh_token`) and two-legged (`client_credentials`, `password`), using the kamermans middleware.
  - `TokenPersistenceFactory` stores `access_token`, `refresh_token` and `expires_at` encrypted.
  - `IntegrationTokenFactory(['extra_key'])` keeps extra token values.
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_authentication.html]
- Three-legged callback: route `mautic_integration_public_callback` (parameter `integration`). [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_authentication.html#oauth2-three-legged]
- Builder: `BuilderInterface::isSupported()` for `email`/`page`. It decides which Themes are listed. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_builder.html]
- Sync:
  - Tag `mautic.sync_integration` and implement `SyncInterface` (mapping manual + sync data exchange).
  - Run `mautic:integrations:sync HelloWorld --start-datetime=... --end-datetime=...`.
  - The engine calls `getSyncReport()` repeatedly until a report is empty.
  - The Integration must report back created ids and any conversions or deletions.
  - First-time sync handling is up to the Integration.
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_sync.html]

## Marketplace docs
- The Marketplace is reached from the Settings cog. It is read-only since 4.0. Since 4.2, install/update/remove needs "Update Mautic through Composer" = Yes. [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html#using-the-mautic-marketplace] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#update-settings]
- It is not compatible with ZIP installs. [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html]
- It does not verify Mautic version compatibility. Column sorting is not available. Ratings and reviews are managed on the public Marketplace website. [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html]
- CLI: `mautic:marketplace:list -p 1 -l 15 -f <filter>`. [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html#list-plugins]
- Listing requirements:
  - `composer.json` with `type: mautic-plugin`.
  - `extra.install-directory-name` equal to the bundle namespace (typos can crash Mautic).
  - `require.php`, `require.ext-*` and `require.mautic/core-lib`.
  - No `mautic/composer-plugin` dependency.
  - Publish on Packagist.
  [devdocs: https://devdocs.mautic.org/en/7.2/marketplace/listing.html]
- Allowlist: the core team must allowlist each plugin. Apply via mau.tc/marketplace-allowlist; the list is github.com/mautic/marketplace-allowlist. [devdocs: https://devdocs.mautic.org/en/7.2/marketplace/allowlist_what_and_why.html]
- Best practices: a README, GitHub issues, tagged releases with changelogs, CI, and semver starting at 1.0. [devdocs: https://devdocs.mautic.org/en/7.2/marketplace/best_practices.html]

## 8.0 doc changes
- The sync page gains "Sync events" (six event classes) and the removal of `IntegrationEvents`, with a constant → class map. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_integrations/integrations_sync.html#sync-events]
- The authentication page drops string service ids in favour of FQCNs. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_integrations/integrations_authentication.html]
- The feature constants become `public const string`. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_integrations/integrations_configuration.html#configformfeaturesinterface]
- User plugin pages are unchanged in 8.0. [docs: https://docs.mautic.org/en/8.0/plugins/plugin_resources.html]

## Known doc errors (code wins)
- The auth tag is documented as `mautic.auth_integration`; the code uses `mautic.authentication_integration`. [code: app/bundles/IntegrationsBundle/Helper/AuthIntegrationsHelper.php:24 @7.x]
- The builder page text says `mautic.config_integration`; it should be `mautic.builder_integration`. [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:33 @7.x]
- The sync order is documented as Mautic → Integration first; the code pulls first. [code: app/bundles/IntegrationsBundle/Sync/SyncProcess/SyncProcess.php:63-70 @7.x]
- The three-legged example returns a `Response` and imports two-legged classes; the interface returns `string`. [code: app/bundles/IntegrationsBundle/Integration/Interfaces/AuthenticationInterface.php:21 @7.x]
- Several dev pages say `app/config.php`; plugins use `Config/config.php` / `Config/services.php`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_configuration.html]
- The Marketplace docs say "Packagist API". The code uses the `marketplace.mautic.org` registry API. [code: app/bundles/MarketplaceBundle/Api/Connection.php:26-50 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/marketplace/getting_started.html#marketplace-under-the-hood]
- The listing example pins `mautic/core-lib ^5.0` and PHP `>=8.0 <8.1`, which is stale for 7.x. [devdocs: https://devdocs.mautic.org/en/7.2/marketplace/listing.html]

## Gaps in the docs
- No docs for the legacy cron commands, the sync command options, the judge modes or the sync tables. No docs for which plugins use which framework. No troubleshooting for the sync engine. These are covered in references/behaviour.md. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_sync.html]
