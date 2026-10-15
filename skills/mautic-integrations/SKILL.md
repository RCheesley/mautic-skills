---
name: mautic-integrations
description: "Mautic integrations and plugins that connect to external systems: the modern IntegrationsBundle (BasicIntegration) and legacy PluginBundle AbstractIntegration, encrypted api_keys, Guzzle auth providers (API key, basic, OAuth1a, OAuth2), the two-way sync engine (field mapping, sync directions, SyncJudge conflict rules, mautic:integrations:sync), the legacy integration_entity table and fetchleads/pushleadactivity commands, 'Push contact to integration', the bundled CRM and email-marketing plugins (Salesforce, HubSpot, Zoho, Dynamics, SugarCRM, MailChimp, Zapier) and the Marketplace. Use whenever a task mentions integrations, plugin configuration, CRM sync, Salesforce, HubSpot, Zoho, Dynamics, field mapping, sync direction, sync_object_mapping, AbstractIntegration, BasicIntegration, IntegrationsHelper, mautic:integrations:sync, the Marketplace, or touches app/bundles/IntegrationsBundle/, app/bundles/PluginBundle/, app/bundles/MarketplaceBundle/ or plugins/Mautic*Bundle/ CRM plugins."
---
# Mautic integrations

## Scope
An **Integration** is a configured connection between Mautic and a third-party system. A **Plugin** is the package
(a Symfony bundle under `plugins/`) that ships one or more Integrations. This skill covers both integration frameworks,
the sync engine, the legacy CRM push/pull, the bundled integration plugins and the Marketplace. Plugin anatomy,
discovery, `config.php` and `mautic:plugins:reload` basics belong to mautic-plugin-development. Campaign execution
belongs to mautic-campaigns, and Contact field/merge rules belong to mautic-contacts.

Terms: **Contact** = code `Lead`; **DNC** = Do Not Contact record; **feature** = a capability an Integration declares
and the admin ticks (`push_lead`, `get_leads`, `sync`...); **mapping manual** = the sync engine's description of which
objects and fields sync, and in which direction.

## Expected behaviour (essentials)
- Two frameworks coexist and share one settings row per Integration in `plugin_integration_settings` (`Mautic\PluginBundle\Entity\Integration`). [code: app/bundles/PluginBundle/Entity/Integration.php:49-85 @7.x]
- Legacy `AbstractIntegration` is marked "@deprecated To be removed in Mautic 6.0" but is still present in 7.2.1 and every bundled CRM extends it. [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:54 @7.x] [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:17 @7.x]
- A legacy Integration is discovered only from `plugins/<Bundle>/Integration/*Integration.php` of a plugin that is installed in the `plugins` table, and only if service id `mautic.integration.<lowercased name>` exists; otherwise it is silently unavailable. [code: app/bundles/PluginBundle/Helper/IntegrationHelper.php:94-121 @7.x]
- The first discovery of an Integration writes its settings row (unpublished, all features ticked, empty keys), even on a GET page load. [code: app/bundles/PluginBundle/Helper/IntegrationHelper.php:112-132,175-213 @7.x]
- Modern Integrations are auto-tagged by interface: `BasicInterface` → `mautic.basic_integration`, `ConfigFormInterface` → `mautic.config_integration`, `BuilderInterface` → `mautic.builder_integration`. `mautic.sync_integration` and `mautic.authentication_integration` are NOT auto-tagged; you must tag them. [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:26-33 @7.x] [code: app/bundles/IntegrationsBundle/Helper/AuthIntegrationsHelper.php:24 @7.x]
- A modern Integration works only once its settings row exists. Without it, `IntegrationsHelper::getIntegrationConfiguration()` throws `IntegrationNotFoundException`, and the sync helper treats the Integration as "not installed yet". [code: app/bundles/IntegrationsBundle/Helper/IntegrationsHelper.php:87-98 @7.x] [code: app/bundles/IntegrationsBundle/Helper/SyncIntegrationsHelper.php:74-84 @7.x]
- The legacy config URL `/s/plugins/config/{name}` is re-dispatched to the modern `ConfigController::editAction` when `{name}` is a `mautic.basic_integration`. Both kinds therefore share the `/s/plugins` grid. [code: app/bundles/IntegrationsBundle/EventListener/ControllerSubscriber.php:29-57 @7.x]
- Managing integrations needs only `plugin:plugins:manage`. The legacy auth/AJAX actions and the modern field-update AJAX action perform no ACL check of their own. [code: app/bundles/PluginBundle/Security/Permissions/PluginPermissions.php:13-27 @7.x] [code: app/bundles/IntegrationsBundle/Controller/UpdateFieldController.php:13-38 @7.x]
- API keys are stored encrypted. In the modern framework the in-memory entity always holds decrypted keys: they are encrypted at save and decrypted once per request. [code: app/bundles/IntegrationsBundle/Helper/IntegrationsHelper.php:64-116 @7.x]
- Legacy config save: a blank secret keeps the stored secret, and changing the client id or a secret discards stored tokens. [code: app/bundles/PluginBundle/Controller/PluginController.php:196-210,443-462 @7.x]
- Required keys and required field mappings are enforced only when the Integration is being published. An unpublished Integration saves even when invalid. [code: app/bundles/PluginBundle/Form/Type/KeysType.php:18-64 @7.x] [code: app/bundles/IntegrationsBundle/Controller/ConfigController.php:48-262 @7.x] [code: app/bundles/IntegrationsBundle/Helper/FieldValidationHelper.php:29-157 @7.x]
- Enabling can be vetoed by a `PLUGIN_IS_PUBLISHED_STATE_CHANGING` listener. The validator fires only when the submitted value is exactly int `1`. [code: app/bundles/PluginBundle/Form/Constraint/CanPublishValidator.php:21-36 @7.x]
- "Push contact to integration" (`plugin.leadpush`) exists as a campaign action, a form submit action and a point trigger. It calls `pushLead()` on each selected published Integration, then `pushLeadToCampaign()` when a CRM campaign is chosen. A false result marks the campaign log `failed: 1` with a reason. [code: app/bundles/PluginBundle/EventListener/PushToIntegrationTrait.php:44-81 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/plugin_resources.html#testing-integrations]
- Only published Integrations that support `push_lead` are offered in that action, grouped by plugin. [code: app/bundles/PluginBundle/Form/Type/IntegrationsListType.php:24-133 @7.x]
- Legacy `integration_entity` rows link a Contact or Company to a remote id. Deleting a Contact or Company deletes its rows. A remote deletion is recorded as `internal_entity = '<type>-deleted'`, and the row is kept. [code: app/bundles/PluginBundle/EventListener/LeadSubscriber.php:33-77 @7.x] [code: app/bundles/PluginBundle/Entity/IntegrationEntityRepository.php:482-497 @7.x]
- Legacy bulk push creates only identified Contacts with an email and no `integration_entity` row. A `lead-error`, `lead-deleted` or `lead-duplicate` marker therefore suppresses re-creation. Saving the Contact resets `lead-error` to `lead`. [code: app/bundles/PluginBundle/Entity/IntegrationEntityRepository.php:310-406 @7.x] [code: app/bundles/PluginBundle/EventListener/LeadSubscriber.php:33-77 @7.x]
- `mautic:integration:fetchleads -i <Name>` pulls (`get_leads`) and then pushes (`push_leads`). It uses a default window of the last 15 minutes, exits 255 when the Integration is not authorized, and has no lock. `--force` is never read. [code: app/bundles/PluginBundle/Command/FetchLeadsCommand.php:70-285 @7.x]
- In legacy CRM field mapping, `update_mautic = 1` means the CRM value updates Mautic, and `update_mautic = 0` fields are pushed. ConnectWise inverts this on update. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:391-410,489-505 @7.x] [code: plugins/MauticCrmBundle/Integration/ConnectwiseIntegration.php:633 @7.x]
- The modern sync tracks field changes only for non-anonymous Contacts. It needs at least one published Integration with feature `sync` and an object mapped to that Mautic object, and it does not track while a sync is running. [code: app/bundles/IntegrationsBundle/EventListener/LeadSubscriber.php:53-69,114-124 @7.x]
- Tracked changes go to `sync_object_field_change_report`, one row per Integration, object and field. Owner, points, DNC and company changes are recorded as the pseudo fields `owner_id`, `points`, `mautic_internal_dnc_<channel>` and `company`. [code: app/bundles/IntegrationsBundle/EventListener/LeadSubscriber.php:71-97,147-197 @7.x]
- A sync run first pulls (Integration → Mautic), then pushes (Mautic → Integration). Each direction loops in batches until the report or the order is empty. [code: app/bundles/IntegrationsBundle/Sync/SyncProcess/SyncProcess.php:54-76 @7.x]
- The pull window starts at `--start-datetime`. Without it, the start is the latest `last_sync_date` for the object in `sync_object_mapping`, else now minus 24 hours. The Mautic side never uses the stored date because it uses the change report. [code: app/bundles/IntegrationsBundle/Sync/Helper/SyncDateHelper.php:30-114 @7.x]
- The push is a full report (all identified Contacts in the window, 200 per batch) on `--first-time-sync` or with `--mautic-object-id`. Otherwise it is a partial report built from tracked field changes. [code: app/bundles/IntegrationsBundle/Sync/SyncDataExchange/MauticSyncDataExchange.php:45-52 @7.x] [code: app/bundles/IntegrationsBundle/Sync/SyncDataExchange/Internal/ReportBuilder/FullObjectReportBuilder.php:36-148 @7.x]
- Field directions: an `integration`-only field is never written to Mautic, and a `mautic`-only field is never sent. For `bidirectional` fields that changed on both sides, `SyncJudge` decides. [code: app/bundles/IntegrationsBundle/Sync/SyncProcess/Direction/Internal/ObjectChangeGenerator.php:105-190 @7.x] [code: app/bundles/IntegrationsBundle/Sync/SyncProcess/Direction/Integration/ObjectChangeGenerator.php:86-150 @7.x]
- Conflict rule: equal values make Mautic win. Otherwise the newer change wins using hard, then best, then fuzzy evidence. Equal or missing dates leave the field unsynced. [code: app/bundles/IntegrationsBundle/Sync/SyncJudge/SyncJudge.php:22-36 @7.x]
- On pull, an unmapped remote object is matched to an existing Contact by Mautic's unique-identifier fields (email by default). A mapping row is created immediately. A new object missing a required value is skipped as a whole, with a notification. [code: app/bundles/IntegrationsBundle/Sync/Helper/MappingHelper.php:40-115 @7.x] [code: app/bundles/IntegrationsBundle/Sync/SyncProcess/Direction/Internal/ObjectChangeGenerator.php:326-334 @7.x]
- Values longer than the field's char limit, or with the wrong type for date/datetime/time/boolean/float fields, are dropped on pull with a de-duplicated user notification. [code: app/bundles/IntegrationsBundle/Sync/SyncDataExchange/Internal/Executioner/FieldValidator.php:30-136 @7.x]
- After a push, tracked changes of successfully synced objects are deleted. Objects flagged `retrySyncLater()` keep theirs. [code: app/bundles/IntegrationsBundle/Sync/SyncProcess/SyncProcess.php:278-297 @7.x]
- The modern engine has no "update blank values" switch. `updateBlanks` exists only inside individual legacy CRM plugins. [code: app/bundles/IntegrationsBundle/Form/Type/IntegrationSyncSettingsType.php:47-60 @7.x] [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:391-410 @7.x]
- Neither `mautic:integrations:sync` nor the legacy commands take a lock, so concurrent runs are possible. [code: app/bundles/IntegrationsBundle/Command/SyncCommand.php:31-126 @7.x]
- Salesforce DNC flows Mautic → SF only, unless "Use latest updated Do Not Contact record" is on. With it on, a newly pulled opted-out SF record gets DNC, and SF opt-out history is replayed oldest first, so a box ticked then unticked leaves no DNC. [PR #4920] [PR #13411] [PR #13444] [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:457-467,2541-2627 @7.x]
- Marketplace pages return 404 when `marketplace_enabled` is false. Installing or removing a `mautic-plugin` or `mautic-theme` runs Composer in-process and is refused with 403 unless `composer_updates` is true. A `mautic-resource` (campaign ZIP) installs without Composer. [code: app/bundles/MarketplaceBundle/Controller/AjaxController.php:52-225 @7.x] [code: app/bundles/CoreBundle/Helper/ComposerHelper.php:142-169 @7.x]
- Only packages installed with Composer type `mautic-plugin` can be removed through the Marketplace. [code: app/bundles/MarketplaceBundle/Command/RemoveCommand.php:64-69 @7.x]
- To be listed, a plugin must be allowlisted by the core team. The Marketplace does not check Mautic version compatibility. [docs: https://devdocs.mautic.org/en/7.2/marketplace/allowlist_what_and_why.html] [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html]

## Where it lives
| Concern | Path(s) |
|---|---|
| Legacy framework | `app/bundles/PluginBundle/` (`Integration/AbstractIntegration.php`, `Helper/IntegrationHelper.php`, `Controller/{PluginController,AuthController,AjaxController}.php`) |
| Modern framework | `app/bundles/IntegrationsBundle/` (`Integration/BasicIntegration.php`, `Integration/Interfaces/*`, `Helper/*IntegrationsHelper.php`, `Controller/ConfigController.php`) |
| Sync engine | `app/bundles/IntegrationsBundle/Sync/` (`SyncProcess/`, `SyncJudge/`, `SyncDataExchange/`, `DAO/`, `Helper/`, `Notification/`) |
| Auth providers | `app/bundles/IntegrationsBundle/Auth/Provider/{ApiKey,BasicAuth,Oauth1aTwoLegged,Oauth2TwoLegged,Oauth2ThreeLegged}/HttpFactory.php` |
| Tables | `plugins`, `plugin_integration_settings`, `integration_entity` (PluginBundle); `sync_object_mapping`, `sync_object_field_change_report` (IntegrationsBundle) |
| Events | `app/bundles/PluginBundle/PluginEvents.php`, `app/bundles/IntegrationsBundle/IntegrationEvents.php` |
| Commands | `mautic:integrations:sync`, `mautic:integrations:cleanup`, `mautic:integration:fetchleads`, `mautic:integration:pushleadactivity`, `mautic:marketplace:{list,install,remove}` |
| Routes | `/s/plugins`, `/s/plugins/config/{name}`, `/s/integration/{integration}/config`, public `/integration/{integration}/callback`, `/plugins/integrations/authcallback/{integration}`, `/s/marketplace/*` |
| Parameters | `marketplace_enabled`, `marketplace_website_url`, `marketplace_registry_url`, core `composer_updates` |
| Permissions | `plugin:plugins:manage`; `marketplace:packages:{view,create,remove}` |
| Bundled plugins | `plugins/Mautic{Crm,Clearbit,FullContact,EmailMarketing,Zapier,Gmail,Outlook}Bundle/` |
| Tests | `app/bundles/{PluginBundle,IntegrationsBundle,MarketplaceBundle}/Tests/`, `plugins/MauticCrmBundle/Tests/` |

Full detail: references/code-map.md.

## How to change or extend it
- Write new integrations against IntegrationsBundle. Extend `BasicIntegration` and add support classes for `ConfigFormInterface` (+ `ConfigFormAuthInterface`, `ConfigFormFeaturesInterface`, `ConfigFormSyncInterface`...), `SyncInterface` and `AuthenticationInterface`. Copy `plugins/MauticClearbitBundle/Integration/` for config and auth. [code: app/bundles/IntegrationsBundle/Integration/BasicIntegration.php:10-40 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations.html]
- Tag the sync class `mautic.sync_integration` and the auth class `mautic.authentication_integration` explicitly in `Config/services.php`. [code: app/bundles/IntegrationsBundle/Helper/SyncIntegrationsHelper.php:34,57-59 @7.x]
- Still ship `Integration/<Name>Integration.php`, so that legacy discovery creates the settings row, and alias `mautic.integration.<lowercase name>`. [code: app/bundles/PluginBundle/Helper/IntegrationHelper.php:94-121 @7.x] [code: plugins/MauticGmailBundle/Config/services.php:21-22 @7.x]
- Sync: implement `SyncDataExchangeInterface::getSyncReport()` / `executeSyncOrder()`, build the mapping with `ObjectMappingDAO::addFieldMapping($mauticField, $integrationField, $direction, $required)`, and report new ids, remaps, deletions and retries on the `OrderDAO`. [code: app/bundles/IntegrationsBundle/Sync/DAO/Sync/Order/OrderDAO.php:129-267 @7.x]
- Add Mautic-side sync fields with `INTEGRATION_MAUTIC_SYNC_FIELDS_LOAD`. Add new internal objects through `INTEGRATION_COLLECT_INTERNAL_OBJECTS` and the `INTEGRATION_*_INTERNAL_*` events; the Contact and Company subscribers are the reference. [code: app/bundles/IntegrationsBundle/EventListener/ContactObjectSubscriber.php:46-166 @7.x]
- Build HTTP clients with the auth-provider `HttpFactory` services. Persist OAuth2 tokens with `TokenPersistenceFactory`, never by hand. [code: app/bundles/IntegrationsBundle/Auth/Support/Oauth2/Token/TokenPersistence.php:27-104 @7.x]
- For a campaign/form action, reuse `plugin.leadpush`. Add per-action options with `appendToForm($builder, $data, 'integration')` (legacy) or register your own campaign action (see mautic-campaigns). [code: app/bundles/PluginBundle/Form/Type/IntegrationConfigType.php:17-19 @7.x]
- Plugin schema: `Entity/` classes create tables on install, and `Migrations/Version_*.php` (extending `IntegrationsBundle\Migration\AbstractMigration`) run on version bump. [code: app/bundles/IntegrationsBundle/Migration/Engine.php:26-95 @7.x]
- 8.x readiness: subscribe by event class, not by `IntegrationEvents::*` constants. Pass mappings to the `MappingManualDAO` constructor. Do not use `DefaultConfigFormTrait`. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_integrations/integrations_sync.html#sync-events]
- Bundled plugin directories are mirrored to read-only GitHub repos. Send PRs to mautic/mautic, not to the mirrors. [code: plugins/MauticCrmBundle/README.md:1-5 @7.x]

## How to test it
- Base classes: `MauticMysqlTestCase` for DB-backed functional tests, `AbstractIntegrationTestCase` for legacy integrations (16 mocked collaborators), and plain `TestCase` for sync DAOs and the judge. [code: app/bundles/PluginBundle/Tests/Integration/AbstractIntegrationTestCase.php:31-56 @7.x]
- In `test` env, legacy integrations get a mockable `ClientFactory`, and the OAuth2 three-legged factory is replaced by a mock-handler factory. [code: app/bundles/PluginBundle/Tests/DependencyInjection/Compiler/TestPass.php:15-28 @7.x] [code: app/bundles/IntegrationsBundle/DependencyInjection/Compiler/TestPass.php:14-20 @7.x]
- Copy from: `app/bundles/IntegrationsBundle/Tests/Unit/Sync/SyncJudge/Modes/*Test.php`, `.../Tests/Unit/Sync/SyncProcess/Direction/Internal/ObjectChangeGeneratorTest.php`, `.../Tests/Functional/EventListener/LeadSubscriberTest.php`, `app/bundles/PluginBundle/Tests/Helper/ReloadHelperTest.php`, `plugins/MauticClearbitBundle/Tests/Functional/Controller/ConfigControllerTest.php`, `app/bundles/MarketplaceBundle/Tests/Functional/Command/InstallCommandTest.php`.
- The end-to-end `SyncServiceTest` is skipped. Use its `TestExamples/` as the reference implementation, not as coverage. [code: app/bundles/IntegrationsBundle/Tests/Functional/Services/SyncService/SyncServiceTest.php @7.x]
- A good regression test asserts rows in `sync_object_field_change_report` / `sync_object_mapping` / `integration_entity`, the encrypted state of `api_keys`, and the direction/required outcome per field.
Full detail: references/test-patterns.md.

## Version notes
- 7.2 deprecates the service aliases `mautic.integrations.sync.service` and `mautic.integrations.subscriber.controller`, and the Clearbit `mautic.plugin.clearbit.lookup_helper` alias. [code: app/bundles/IntegrationsBundle/Config/services.php:91-94 @7.x] [code: plugins/MauticClearbitBundle/Config/services.php:24-25 @7.x]
- 8.x removes `IntegrationEvents` (23 constants → event classes such as `InternalContactFieldChangesEvent` and `MauticToIntegrationSyncCompletedEvent`) and the `mautic.integrations.helper*` service ids. [PR #17160] [PR #17654] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_integrations/integrations_sync.html#sync-events]
- 8.x removes Clearbit entirely, `AbstractSsoFormIntegration`, `DefaultConfigFormTrait` and the dead HubSpot `mautic_integration_companies` route. It also makes four CRM integrations `final`. [PR #17785] [PR #17231]
- 8.x: `plugin.leadpush` moves to `ON_CAMPAIGN_BATCH_ACTION`. Responses arrive in the new `PluginIntegrationResponseEvent`, and `AbstractIntegration` takes `CacheProviderInterface` and gains array return types. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- 5.0 removes the Pipedrive and Citrix/GoTo integrations; 4.4.9 shows deprecation notices for both. Rackspace/OpenStack storage went in 3.0. [PR #12081] [PR #12333] [PR #12364] [PR #12367] [PR #8310]
- 5.0 to 7.2.1: `getLeadData()` detaches the wrong entities, so `mautic:integration:pushleadactivity` pushes nothing; fixed in 7.2.2. [PR #12361] [PR #17815]
- HubSpot uses a Private App token since 4.4.5/5.0; the `hapikey` path remains only as a fallback. [PR #11470] [PR #11857]
- 5.1 sync engine: one-way "to integration" fields are never cleared by a pull, same-batch duplicates reuse one Contact, sync changes are attributed to the integration, and `mautic:integrations:cleanup` exists. [PR #11251] [PR #13435] [PR #13426] [PR #13340]
- 6.0: an empty value for a required Mautic field skips the object or field instead of aborting the sync. [PR #14666]
- 7.2 moves Clearbit, Gmail and Tag Manager from `AbstractIntegration` to `BasicIntegration`, and makes childless IntegrationsBundle DAOs `final`. [PR #16586] [PR #16847] [PR #16795] [PR #16888]
- Marketplace: read-only since 4.0, and install/remove has required the Composer setting since 4.2. [docs: https://docs.mautic.org/en/7.2/marketplace/marketplace.html#using-the-mautic-marketplace]
Full detail: references/version-notes.md.

## Pitfalls
- Forgetting the `mautic.sync_integration` tag yields `IntegrationNotFoundException("... has not been tagged with mautic.sync_integration")`. [code: app/bundles/IntegrationsBundle/Helper/SyncIntegrationsHelper.php:57-59 @7.x]
- The docs name the auth tag `mautic.auth_integration`, but the code iterates `mautic.authentication_integration`. Use the code's name. [code: app/bundles/IntegrationsBundle/Helper/AuthIntegrationsHelper.php:24 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_authentication.html#register-the-integration-for-authentication]
- The docs say the sync runs Mautic → Integration first, but the code pulls first and then pushes. [code: app/bundles/IntegrationsBundle/Sync/SyncProcess/SyncProcess.php:63-70 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_sync.html]
- The builder docs say tag `mautic.config_integration`, but builders use `mautic.builder_integration` (auto-tagged). [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:33 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_integrations/integrations_builder.html#register-the-integration-as-a-builder]
- `authenticateIntegration()` must return `string`, although the docs example returns a `Response`. [code: app/bundles/IntegrationsBundle/Integration/Interfaces/AuthenticationInterface.php:21 @7.x]
- Legacy `key` auth: `getRequiredKeyFields()` declares `key`, but `isAuthorized()` checks `api_key`. Override one of them. [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:561-563,1238-1240 @7.x]
- Gmail email-client tracking: EmailBundle calls `getDecryptedApiKeys()` on the Integration object, but `GmailIntegration` (a `BasicIntegration`) defines no such method. Inferred: Gmail tracking requests fail. [code: app/bundles/EmailBundle/Controller/PublicController.php:741 @7.x] [code: app/bundles/IntegrationsBundle/Integration/BasicIntegration.php:10-40 @7.x] [unverified at runtime]
- `PluginEvents::ON_FORM_SUBMIT_ACTION_TRIGGERED` is declared but never dispatched. [code: app/bundles/PluginBundle/PluginEvents.php:119 @7.x]
- HubSpot `--fetch-all` still uses "recently modified" endpoints, which return only about 30 days on long-lived portals. [docs: https://docs.mautic.org/en/7.2/plugins/hubspot.html#troubleshooting-hubspot-integration] [code: plugins/MauticCrmBundle/Integration/HubspotIntegration.php:339-431 @7.x]
- `ReferenceValueDAO` serializes key `types` but unserializes `type`, so the relation type is lost on round-trip. [code: app/bundles/IntegrationsBundle/Sync/DAO/Value/ReferenceValueDAO.php:41-56 @7.x]
- Open question: the partial report keeps the earliest `modified_at` as the object change date, although a comment says "latest". [code: app/bundles/IntegrationsBundle/Sync/SyncDataExchange/Internal/ReportBuilder/PartialObjectReportBuilder.php:122-125 @7.x]
- `IntegrationsBundle/README.md` says pulling specific ids and company ids are "not implemented yet". That is stale: the code supports both. [code: app/bundles/IntegrationsBundle/README.md:19-21 @7.x]
- Marketplace log and CLI messages still say "Packagist", although the registry is `marketplace.mautic.org`. [code: app/bundles/MarketplaceBundle/Api/Connection.php:77 @7.x] [code: app/bundles/MarketplaceBundle/Service/Config.php:32-38 @7.x]
- `mautic:integration:pushleadactivity` exits successfully even when nothing was pushed, because `pushLeadActivity()` only logs exceptions. The 7.x snapshot and 7.2.1 still have the inverted detach check (fixed in 7.2.2), so check the logs for "EntityManager is closed". [PR #17815] [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:245-254 @7.x]
- The Gmail tracking pitfall above dates from 7.2.0, when Gmail moved from `AbstractIntegration` to `BasicIntegration`; 7.1.3 still extends `AbstractIntegration`, which has the method. [PR #16847] [code: plugins/MauticGmailBundle/Integration/GmailIntegration.php:10 @7.x]
- HubSpot without a stored `accessKey` still sends `?hapikey=`, which HubSpot sunset in 2022. Inferred: a legacy key no longer authenticates. [PR #11470] [code: plugins/MauticCrmBundle/Api/HubspotApi.php:18-24 @7.x]
- A legacy CRM fetch with no "Is Unique Identifier" field or no Mautic-priority fields imports nothing, and says so only at debug log level. [PR #12619] [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:372,400 @7.x]

## Related skills
- mautic-plugin-development: plugin anatomy, discovery, `config.php`, `mautic:plugins:reload`, plugin migrations in general.
- mautic-contacts: Contact/Company fields, unique identifiers, DNC, `LeadManipulator`, merge.
- mautic-campaigns: campaign actions, `PendingEvent`/batch actions, the campaign event log.
- mautic-forms: form submit actions, including `plugin.leadpush`.
- mautic-cron-and-queues: scheduling `mautic:integrations:sync` and `mautic:integration:fetchleads`.
- mautic-configuration: `composer_updates`, `marketplace_*` parameters and env overrides.
- mautic-rest-api: what Zapier and other external tools call instead of a plugin.
- mautic-testing: test base classes, fixtures, running PHPUnit.
- mautic-upgrades-and-versions: Composer-based installs, 7 → 8 porting.

## Reference files
- references/behaviour.md: full numbered behaviour specification (frameworks, config, legacy push/pull, sync engine, auth, Marketplace).
- references/code-map.md: tables, entities, services, events, routes, commands, parameters, permissions, tests.
- references/bundled-plugins.md: one section per bundled integration plugin (purpose, framework, direction, commands, status, limitations).
- references/docs-digest.md: what docs.mautic.org and devdocs say, with URLs, procedures and terminology.
- references/test-patterns.md: base classes, representative tests, skeletons for sync, legacy and Marketplace tests.
- references/version-notes.md: 5.x/6.x history, 7.x minors and the 8.x delta for this area.
- references/pr-history.md: why and when behaviour changed, from merged PRs: decisions by sub-topic and bundled plugin, removed plugins, regression catalogue, feature timeline, norms and open questions.
