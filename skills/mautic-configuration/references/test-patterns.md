# Testing configuration and the installer

## Base classes and environment
- Use `MauticMysqlTestCase` (via `AbstractMauticTestCase`) for functional tests. `configParams` is passed to the kernel as the `MAUTIC_CONFIG_PARAMETERS` JSON before boot. The defaults enable the API and basic auth, and set `site_url=https://localhost`, `mailer_dsn=null://null`, in-memory messenger transports and `create_custom_field_in_background=false`. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:111-114 @7.x]
- `AppTestKernel` always reports installed and honours `TEST_CACHE_DIR`/`TEST_LOG_DIR`. [code: app/AppTestKernel.php:11-32 @7.x]
- The test DB comes from `.env.test` / `.env.test.local` (`DB_*`, prefix `test_`). [code: .env.test:2-13 @7.x]
- Use Symfony `TypeTestCase` for form helpers. `CommonMocks` is used by `ConfigBuilderEventTest`. [code: app/bundles/ConfigBundle/Tests/Form/Helper/RestrictionHelperTest.php:153-230 @7.x]

## Representative tests
| Test | What it shows |
|---|---|
| `app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php` | Escaping, tab redirect and 404, per-tab saving, restricted fields (swaps the `RestrictionHelper` service), user and system locale, SAML entity id. [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:20-420 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/Loader/ParameterLoaderTest.php` | Precedence and env not overwritten; fixture root `Tests/Unit/Loader/TestRoot`. [code: app/bundles/CoreBundle/Tests/Unit/Loader/ParameterLoaderTest.php:40-170 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/Loader/EnvVars/*Test.php` | Each derived env var (API, SiteUrl, SAML, ElFinder, ...). [code: app/bundles/CoreBundle/Tests/Unit/Loader/EnvVars/ConfigEnvVarsTest.php:26-60 @7.x] |
| `app/bundles/ConfigBundle/Tests/Mapper/ConfigMapperTest.php` | Value overlay and restriction. [code: app/bundles/ConfigBundle/Tests/Mapper/ConfigMapperTest.php:168-260 @7.x] |
| `app/bundles/ConfigBundle/Tests/Service/ConfigChangeLoggerTest.php`, `Tests/EventListener/ConfigSubscriberTest.php` | Audit log and IP anonymisation on save. [code: app/bundles/ConfigBundle/Tests/Service/ConfigChangeLoggerTest.php:34-60 @7.x] [code: app/bundles/ConfigBundle/Tests/EventListener/ConfigSubscriberTest.php:42-70 @7.x] |
| `app/bundles/InstallBundle/Tests/Functional/InstallWorkflowTest.php` | Moves local.php aside, drives `/installer` through all forms and asserts the `email` LeadField fixture. [code: app/bundles/InstallBundle/Tests/Functional/InstallWorkflowTest.php:36-164 @7.x] |
| `app/bundles/InstallBundle/Tests/Command/InstallCommandTest.php` | Already installed → 0; HTML stripped. [code: app/bundles/InstallBundle/Tests/Command/InstallCommandTest.php:55-156 @7.x] |
| `app/bundles/InstallBundle/Tests/Install/InstallServiceTest.php` | DB param validation, admin user, directory prep (23 tests). [code: app/bundles/InstallBundle/Tests/Install/InstallServiceTest.php:255-470 @7.x] |
| `app/middlewares/Tests/HSTSMiddlewareTest.php` | HSTS header rules. [code: app/middlewares/Tests/HSTSMiddlewareTest.php:50-120 @7.x] |
| `app/bundles/ConfigBundle/Tests/Controller/SysinfoControllerTest.php` | System Info access. [code: app/bundles/ConfigBundle/Tests/Controller/SysinfoControllerTest.php:13 @7.x] |

No Codeception acceptance tests cover the installer or config. [code: tests/_support/Helper/DbHelper.php @7.x]

## Patterns
- **Back up local.php.** Any test that saves configuration writes the real local.php, so copy it in `setUp()` and restore it in `beforeTearDown()`. [code: app/bundles/CoreBundle/Tests/Functional/EventListener/ConfigSubscriberTest.php:26-50 @7.x]
- **Disable rollback** when the controller writes files and the DB in separate steps (`$useCleanupRollback = false`). [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:20-49 @7.x]
- **Submit one tab** using field names `config[<alias>][<field>]` and the button `config[buttons][apply]` or `[save]`. [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:138 @7.x]
- **Override parameters per test** with `$this->configParams[...]` before `parent::setUp()`. Do not write local.php to set test parameters. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:111-114 @7.x]

## Skeleton: functional save test
```php
final class MySettingFunctionalTest extends MauticMysqlTestCase
{
    protected $useCleanupRollback = false;
    private string $localConfig;
    private string $backup = '';

    protected function setUp(): void
    {
        $this->configParams['my_setting'] = false;   // reaches the kernel via MAUTIC_CONFIG_PARAMETERS
        parent::setUp();
        $this->localConfig = self::getContainer()->get(KernelInterface::class)->getLocalConfigFile(); // \AppKernel
        $this->backup      = file_exists($this->localConfig) ? file_get_contents($this->localConfig) : '';
    }

    protected function beforeTearDown(): void
    {
        file_put_contents($this->localConfig, $this->backup);
    }

    public function testSavingTabKeepsOtherValues(): void
    {
        $crawler = $this->client->request('GET', '/s/config/edit/myconfig');
        $form    = $crawler->selectButton('config[buttons][apply]')->form();
        $form['config[myconfig][my_setting]']->setValue('1');
        $this->client->submit($form);
        $this->assertResponseIsSuccessful();

        $parameters = [];
        include $this->localConfig;
        $this->assertTrue($parameters['my_setting']);
        $this->assertArrayNotHasKey('db_password', $parameters['myconfig'] ?? []); // restricted keys never come from the form
    }
}
```
The local.php path is obtained the same way as in `ConfigSubscriberTest::getConfigPath()`, which backs up via `copy()` to `.backup` and restores via `rename()`. [code: app/bundles/CoreBundle/Tests/Functional/EventListener/ConfigSubscriberTest.php:26-53 @7.x] [code: app/bundles/ConfigBundle/Tests/Controller/ConfigControllerFunctionalTest.php:138 @7.x]

## What a good regression test asserts
- The changed key is written, and keys from other tabs are unchanged. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:131-140 @7.x]
- Restricted keys can neither be rendered nor be submitted. [code: app/bundles/ConfigBundle/Form/Helper/RestrictionHelper.php:60-82 @7.x]
- `%` round-trips as `%%` in local.php and as `%` in the form. [code: app/bundles/ConfigBundle/Form/Type/EscapeTransformer.php:63-92 @7.x]
- Empty secret fields keep the stored value. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:127-137 @7.x]
- For loader changes, assert precedence with a unit test on `ParameterLoader`, including a pre-set `$_ENV` key. [code: app/bundles/CoreBundle/Tests/Unit/Loader/ParameterLoaderTest.php:156-170 @7.x]
