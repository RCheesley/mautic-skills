# Plugin development — test patterns

## 1. Where plugin tests run
- Core's PHPUnit config includes `plugins/*Bundle/Tests` in the test suite and excludes test/config/translation/view directories from coverage [code: app/phpunit.xml.dist:23-35,53 @7.x].
- A plugin living in core's `plugins/` directory is therefore run by the normal core test command; a standalone plugin repository installs Mautic in CI and runs PHPUnit with `KERNEL_CLASS=AppTestKernel`, `KERNEL_DIR=app` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/continuous_integration.html#adding-the-phpunit-xml-file].
- CI should install Mautic (`mautic:install --force http://localhost`) and the plugin (`mautic:plugins:install`) before tests; `PLUGIN_DIR` matches `extra.install-directory-name` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/continuous_integration.html].
- Quick wiring check after container-affecting changes: `rm -rf var/cache && bin/console` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html#autowiring].

## 2. Base classes
| Base | Use for | Source |
|---|---|---|
| `PHPUnit\Framework\TestCase` | permission classes, subscribers with mocked events, helpers | [code: plugins/MauticTagManagerBundle/Tests/Unit/Security/Permissions/TagManagerPermissionsTest.php:11 @7.x] |
| `Mautic\CoreBundle\Test\MauticMysqlTestCase` | routes, controllers, repositories, commands (`$this->client`, `$this->em`, `testSymfonyCommand()`) | [code: plugins/MauticFocusBundle/Tests/Controller/FocusControllerTest.php:14 @7.x] [code: integrations-plugins-marketplace §10 @7.x] |
| `Mautic\CoreBundle\Test\AbstractMauticTestCase` | kernel without DB reset | [code: integrations-plugins-marketplace §10 @7.x] |
| `Symfony\Bundle\FrameworkBundle\Test\KernelTestCase` | container wiring checks | [code: integrations-plugins-marketplace §10 @7.x] |

## 3. Representative tests to copy
1. `app/bundles/PluginBundle/Tests/Helper/ReloadHelperTest.php` — `testDisableMissingPlugins`, `testEnableFoundPlugins`, `testUpdatePlugins`, `testInstallPlugins`; uses `PluginBundleBaseStub` [code: app/bundles/PluginBundle/Tests/Helper/ReloadHelperTest.php:17-160 @7.x].
2. `app/bundles/PluginBundle/Tests/Controller/PluginControllerTest.php` — runs `mautic:plugins:install` then reads `/s/plugins/info/MauticFocusBundle` [code: integrations-plugins-marketplace §10 @7.x].
3. `plugins/MauticTagManagerBundle/Tests/Unit/Security/Permissions/TagManagerPermissionsTest.php` — `testBuildFormMethodAddsStandardFormFields` [code: plugins/MauticTagManagerBundle/Tests/Unit/Security/Permissions/TagManagerPermissionsTest.php:30 @7.x].
4. `plugins/MauticFocusBundle/Tests/Controller/FocusControllerTest.php` — index/new pages return 200 [code: plugins/MauticFocusBundle/Tests/Controller/FocusControllerTest.php:16-32 @7.x].
5. `app/bundles/CoreBundle/Tests/Unit/DependencyInjection/Builder/BundleMetadataBuilderTest.php` — expected plugin metadata shape [code: app/bundles/CoreBundle/Tests/Unit/DependencyInjection/Builder/BundleMetadataBuilderTest.php:59-82 @7.x].
6. `app/bundles/SmsBundle/Tests/DependencyInjection/Compiler/SmsTransportPassTest.php` — tagged service collection [code: app/bundles/SmsBundle/Tests/DependencyInjection/Compiler/SmsTransportPassTest.php @7.x].

## 4. What a good plugin regression test asserts
- Route + permission: a User with the permission gets 200; a User without gets 403; anonymous `main` access redirects to login [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:219-247 @7.x].
- Extension registration: after dispatching the builder event the plugin's key is present (`CampaignBuilderEvent::getActions()`, `FormBuilderEvent`, `ReportBuilderEvent`) [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#registering-campaign-events].
- Action execution: every `LeadEventLog` passed to a `PendingEvent` ends up in `getSuccessful()` or `getFailures()` [code: app/bundles/CampaignBundle/Event/PendingEvent.php:217-225 @7.x].
- Subscriber keys: `getSubscribedEvents()` contains the 8.x class key (and the 7.x constant when defined) [code: 8x-changes §7 @8.x].
- Migration idempotence: `isApplicable()` true before, `up()` SQL valid, `isApplicable()` false after; no core test covers the engine [code: app/bundles/IntegrationsBundle/Migration/AbstractMigration.php:23-45 @7.x].
- Install/update: after bumping `version`, `mautic:plugins:reload` reports the plugin as updated and the `plugins.version` column changes [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:67-95 @7.x].

## 5. Skeletons
Unit test for a permission class (pattern from TagManager) [code: plugins/MauticTagManagerBundle/Tests/Unit/Security/Permissions/TagManagerPermissionsTest.php:11-30 @7.x]:
```php
final class HelloWorldPermissionsTest extends \PHPUnit\Framework\TestCase
{
    public function testNameAndLevels(): void
    {
        $permissions = new HelloWorldPermissions([]);        // 7.x signature; 8.x: new HelloWorldPermissions()
        $this->assertSame('helloWorld', $permissions->getName());
        $this->assertTrue($permissions->isSupported('worlds', 'view'));
    }
}
```

Subscriber registration test (works on 7.x and 8.x):
```php
public function testRegistersCampaignAction(): void
{
    $event = new CampaignBuilderEvent($this->createMock(TranslatorInterface::class));
    (new CampaignSubscriber())->onBuild($event);
    $this->assertArrayHasKey('helloworld.say_hello', $event->getActions());
    $this->assertArrayHasKey(CampaignBuilderEvent::class, CampaignSubscriber::getSubscribedEvents());
}
```
[devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#registering-campaign-events] [code: 8x-changes §7 @8.x]

Functional route test:
```php
final class WorldControllerFunctionalTest extends MauticMysqlTestCase
{
    public function testIndexLoadsForAdmin(): void
    {
        $this->client->request('GET', '/s/hello');
        $this->assertResponseIsSuccessful();
    }
}
```
[code: plugins/MauticFocusBundle/Tests/Controller/FocusControllerTest.php:14-24 @7.x]

Migration test (no core precedent — build schema with the DBAL schema manager):
```php
public function testMigrationIsIdempotent(): void
{
    $migration = new Version_1_0_1($this->em, MAUTIC_TABLE_PREFIX);
    $this->assertTrue($migration->shouldExecute());
    $migration->execute();
    $this->assertFalse($migration->shouldExecute());
}
```
[code: app/bundles/IntegrationsBundle/Migration/AbstractMigration.php:17-45 @7.x]

## 6. Fixtures and data
- Create entities in the test with `$this->em->persist()`/`flush()`; `MauticMysqlTestCase` resets the DB between tests [code: integrations-plugins-marketplace §10 @7.x].
- Data fixtures used by core plugin tests include `LeadFieldData`, `LoadLeadData` [code: integrations-plugins-marketplace §10 @7.x].

## 7. 8.x testing changes
- PHPUnit 13; 300+ core classes are `final`, so mocking them needs `DG\BypassFinals` enabled in a plugin bootstrap; no test doubles of `Request`/`InputBag`/`Router` [code: 8x-changes §7 "Porting a plugin" @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#final-classes].
- Tests asserting on `getSubscribedEvents()` must expect class keys [code: 8x-changes §3.1 @8.x].
- For deeper testing conventions see mautic-testing.
