# Integrations: test patterns (Mautic 7.x)

## Base classes and helpers
| Use | Class | Source |
|---|---|---|
| DB-backed functional (HTTP client, `$this->em`, `testSymfonyCommand()`) | `Mautic\CoreBundle\Test\MauticMysqlTestCase` | [code: plugins/MauticClearbitBundle/Tests/Functional/Controller/ConfigControllerTest.php:21-80 @7.x] |
| Kernel without DB reset (Marketplace commands/services) | `Mautic\CoreBundle\Test\AbstractMauticTestCase` | [code: app/bundles/MarketplaceBundle/Tests/Functional/Command/InstallCommandTest.php @7.x] |
| Legacy integration unit tests (16 mocked collaborators: dispatcher, cache, em, session, request, router, translator, logger, encryptionHelper, leadModel, companyModel, pathsHelper, notificationModel, fieldModel, integrationEntityModel, doNotContact...) | `Mautic\PluginBundle\Tests\Integration\AbstractIntegrationTestCase` | [code: app/bundles/PluginBundle/Tests/Integration/AbstractIntegrationTestCase.php:31-56 @7.x] |
| Iterate every legacy integration (form settings, OAuth headers) | `KernelTestCase` | [code: app/bundles/PluginBundle/Tests/ConfigFormTest.php:55-111 @7.x] |
| Guzzle mocking in Marketplace controllers | `Mautic\CoreBundle\Test\Guzzle\ClientMockTrait` | [code: app/bundles/MarketplaceBundle/Tests/Functional/Controller/ListControllerTest.php @7.x] |
| Test-env HTTP seams | `TestPass` injects `ClientFactory` into legacy integrations; a mock-handler OAuth2 three-legged factory | [code: app/bundles/PluginBundle/Tests/DependencyInjection/Compiler/TestPass.php:15-28 @7.x] [code: app/bundles/IntegrationsBundle/DependencyInjection/Compiler/TestPass.php:14-20 @7.x] |

Fixtures: `LeadFieldData` and `LoadLeadData` for the sync service test. Marketplace API responses live in `app/bundles/MarketplaceBundle/Tests/ApiResponse/*.json`. [code: app/bundles/IntegrationsBundle/Tests/Functional/Services/SyncService/SyncServiceTest.php:24 @7.x]

## Representative tests to copy
1. `app/bundles/PluginBundle/Tests/Helper/ReloadHelperTest.php`: install, update, disable and enable rules and the events they dispatch.
2. `app/bundles/PluginBundle/Tests/Controller/PluginControllerTest.php`: legacy config validation (`/s/plugins/config/Twilio`).
3. `app/bundles/PluginBundle/Tests/Entity/IntegrationEntityRepositoryTest.php`: `findLeadsToUpdate`, `markAsDeleted`.
4. `app/bundles/IntegrationsBundle/Tests/Functional/EventListener/LeadSubscriberTest.php`: change rows written on save, with a stubbed `SyncIntegrationsHelper`.
5. `app/bundles/IntegrationsBundle/Tests/Unit/Sync/SyncProcess/Direction/{Internal,Integration}/ObjectChangeGeneratorTest.php`: direction, required and judge outcomes.
6. `app/bundles/IntegrationsBundle/Tests/Unit/Sync/SyncJudge/Modes/{HardEvidence,BestEvidence,FuzzyEvidence}Test.php`: the conflict matrix.
7. `app/bundles/IntegrationsBundle/Tests/Unit/Sync/SyncDataExchange/Internal/Executioner/FieldValidatorTest.php`, `.../ReportBuilder/PartialObjectReportBuilderTest.php`.
8. `app/bundles/IntegrationsBundle/Tests/Unit/Auth/Provider/Oauth2ThreeLegged/HttpFactoryTest.php`, `Tests/Unit/Auth/Support/Oauth2/Token/TokenPersistenceTest.php`.
9. `app/bundles/IntegrationsBundle/Tests/Unit/Command/SyncCommandTest.php`, `Tests/Functional/Command/CleanupCommandTest.php`.
10. `plugins/MauticClearbitBundle/Tests/Functional/Controller/ConfigControllerTest.php`: creates `Plugin` + `Integration` rows, posts the modern config form and asserts the key is encrypted at rest.
11. `plugins/MauticCrmBundle/Tests/Integration/SalesforceIntegrationTest.php`, `Tests/Api/SalesforceApiTest.php`: legacy push counts, retries and DNC by date.
12. `app/bundles/MarketplaceBundle/Tests/Functional/Command/InstallCommandTest.php`, `Tests/Functional/Service/ResourceInstallerTest.php`: dry-run, 404, wrong type, unsafe URLs, size cap, rollback.
Source list: [code: app/bundles/IntegrationsBundle/Tests/Unit/Sync/SyncJudge/Modes/HardEvidenceTest.php @7.x] and the code analysis test list.

`SyncServiceTest` is skipped ("disabled for now"), so there is no end-to-end DB test of the engine. Its `TestExamples/Integration/ExampleIntegration.php` and `TestExamples/Sync/SyncDataExchange/ExampleSyncDataExchange.php` are the canonical minimal sync implementation. [code: app/bundles/IntegrationsBundle/Tests/Functional/Services/SyncService/TestExamples/Sync/SyncDataExchange/ExampleSyncDataExchange.php:124-169 @7.x]

FullContact, EmailMarketing, Zapier and CloudStorage have no tests. [code: plugins/MauticFullContactBundle @7.x]

## Skeleton: modern Integration row + config save (functional)
```php
final class MyIntegrationConfigTest extends MauticMysqlTestCase
{
    public function testApiKeyIsEncryptedAtRest(): void
    {
        $plugin = new Plugin();
        $plugin->setName('My');
        $plugin->setBundle('MyBundle');
        $integration = new Integration();
        $integration->setName('My');
        $integration->setIsPublished(false);
        $integration->setPlugin($plugin);
        $this->em->persist($plugin);
        $this->em->persist($integration);
        $this->em->flush();

        // legacy route; ControllerSubscriber re-dispatches it to the modern ConfigController
        $route = self::getContainer()->get(RouterInterface::class)
            ->generate('mautic_plugin_config', ['name' => 'My']);
        $crawler = $this->client->request('GET', $route);
        // fill integration_config[isPublished], integration_config[apiKeys][apikey] and submit (see Clearbit test)

        $this->em->clear();
        $stored = $this->em->getRepository(Integration::class)->findOneBy(['name' => 'My']);
        $this->assertNotSame('secret', $stored->getApiKeys()['apikey'] ?? null); // encrypted at rest
        // decrypt through IntegrationsHelper::getIntegrationConfiguration() to assert the round trip
    }
}
```
This pattern follows the Clearbit config test, which also shows that the reloaded form re-displays the decrypted key (`#integration_config_apiKeys_apikey`). [code: plugins/MauticClearbitBundle/Tests/Functional/Controller/ConfigControllerTest.php:20-80 @7.x]

## Skeleton: sync field direction (unit)
Build an `ObjectMappingDAO` with `addFieldMapping('email', 'Email', ObjectMappingDAO::SYNC_BIDIRECTIONALLY, true)`, feed a `ReportObjectDAO` to the internal `ObjectChangeGenerator`, and assert the resulting `ObjectChangeDAO` fields. Copy the setup from `ObjectChangeGeneratorTest`. [code: app/bundles/IntegrationsBundle/Tests/Unit/Sync/SyncProcess/Direction/Internal/ObjectChangeGeneratorTest.php @7.x] [code: app/bundles/IntegrationsBundle/Sync/DAO/Mapping/MappingManualDAO.php:159-183 @7.x]

## What a good regression test asserts
- **Tracking**: the exact `sync_object_field_change_report` rows (column name, type, encoded value) after a Contact save, and no rows for anonymous Contacts or during a sync. [code: app/bundles/IntegrationsBundle/EventListener/LeadSubscriber.php:53-197 @7.x]
- **Mapping**: a `sync_object_mapping` row is created on match, `is_deleted` is honoured, and `last_sync_date` advances. [code: app/bundles/IntegrationsBundle/Sync/Helper/MappingHelper.php:40-234 @7.x]
- **Legacy**: `integration_entity` markers (`lead-error`, `lead-deleted`) and the `failed`/`reason` campaign log metadata from `plugin.leadpush`. [code: app/bundles/PluginBundle/EventListener/PushToIntegrationTrait.php:44-81 @7.x]
- **Config**: encrypted `api_keys`, validity only enforced when published, and that unpublished saves still succeed. [code: app/bundles/IntegrationsBundle/Controller/ConfigController.php:48-262 @7.x]
- **Marketplace**: HTTP status codes (400/403/500), no Composer call when `composer_updates` is false, and resource rollback. [code: app/bundles/MarketplaceBundle/Controller/AjaxController.php:52-225 @7.x]
- **8.x note**: CRM integration classes become `final`; mock through interfaces or use `dg/bypass-finals`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
