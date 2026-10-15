# Themes and builder — test patterns (Mautic 7.x)

For running PHPUnit, base classes and DB fixtures in general see the `mautic-testing` skill.

## 1. Where tests live and which base class to use

| What you test | Base class | Example | Source |
|---|---|---|---|
| `ThemeHelper` rules (discovery, install, fallback, copy, delete, sandbox render) | `PHPUnit\Framework\TestCase` with mocked `PathsHelper`, Twig `Environment`, `TranslatorInterface`, `CoreParametersHelper`, `BuilderIntegrationsHelper`; real `Filesystem` and `Finder` | `ThemeHelperTest` (21 tests) | [code: app/bundles/CoreBundle/Tests/Unit/Helper/ThemeHelperTest.php:31-90 @7.x] |
| Theme fixtures on disk | `app/bundles/CoreBundle/Tests/Unit/Helper/resource/themes/` (incl. `good.zip`, `theme-custom-builder-*`) | `testThemeIsInstalled` | [code: app/bundles/CoreBundle/Tests/Unit/Helper/ThemeHelperTest.php:152-166 @7.x] |
| Theme Manager controller | `Mautic\CoreBundle\Test\MauticMysqlTestCase` | `ThemeControllerTest::testThemeVisibility`, `testDeleteTheme`, `testBatchDeleteActionWithNonCoreTheme` | [code: app/bundles/CoreBundle/Tests/Functional/Controller/ThemeControllerTest.php @7.x] |
| Twig sandbox end-to-end | `MauticMysqlTestCase`, writes a theme into `themes/` and requests `/page/preview/{id}` | `ThemeHelperSandboxTest` (covers advisory GHSA-9fx4-7cmj-47vg) | [code: app/bundles/PageBundle/Tests/Functional/Controller/ThemeHelperSandboxTest.php:12-140 @7.x] |
| `themes/system` overrides | functional, creates `themes/system` and rebuilds the container | `SystemThemeTemplatePathPassTest` | [code: app/bundles/CoreBundle/Tests/Functional/DependencyInjection/Compiler/SystemThemeTemplatePathPassTest.php @7.x] |
| Builder selection | unit | `BuilderIntegrationsHelperTest::testBuilderNotFoundIfFeatureSupportedButNotEnabled` | [code: app/bundles/IntegrationsBundle/Tests/Unit/Helper/BuilderIntegrationsHelperTest.php @7.x] |
| Email accessibility / render listeners | unit + functional | `EmailBundle/Tests/EventListener/BuilderSubscriberTest.php`, `BuilderSubscriberFunctionalTest.php` | [code: app/bundles/EmailBundle/Tests/EventListener/BuilderSubscriberTest.php @7.x] |
| GrapesJS model/controller/subscribers | unit (plugin's own `phpunit.xml`) | `GrapesJsBuilderModelEditorStateTest`, `GrapesJsControllerTest`, `EmailSubscriberTest`, `AssetsSubscriberTest` | [code: plugins/GrapesJsBuilderBundle/phpunit.xml @7.x] |
| GrapesJS HTTP endpoints, API serialisation | `MauticMysqlTestCase`; test must create the `Plugin` row and a published `Integration` row | `AssertCustomMjmlTest`, `FileManagerControllerFunctionalTest` | [code: plugins/GrapesJsBuilderBundle/Tests/Functional/Controller/AssertCustomMjmlTest.php:129-142 @7.x] |
| Builder JavaScript | none — no JS unit tests; only eslint/prettier scripts | — | [code: plugins/GrapesJsBuilderBundle/package.json @7.x] |

No Codeception coverage for themes or the builder was found [code: tests/ @7.x] [unverified: exhaustive search].

## 2. Tests to read first
- `ThemeHelperTest::testThemeIsInstalled`, `::testThemeInstallRejectsZipSlipEntries` (data provider builds zips with `../` and absolute entries), `::testCustomThemesAreReturnedForFeatureIfCustomBuilderIsEnabled`, `::testThemeFallbackToDefaultIfTemplateIsMissing` [code: app/bundles/CoreBundle/Tests/Unit/Helper/ThemeHelperTest.php:152,202,281,537 @7.x].
- `ThemeHelperSandboxTest::testHarmfulTwigPayloadsAreBlockedOnPagePreview` [code: app/bundles/PageBundle/Tests/Functional/Controller/ThemeHelperSandboxTest.php:64-77 @7.x].
- `GrapesJsBuilderModelEditorStateTest::testAddOrEditEntityStoresDecodedEditorStateAndCustomHtmlFallback`, `testAddOrEditPageEntityPersistsOnlyWhenEditorStateProvided`.
- `GrapesJsControllerTest::testEditorStateActionReturnsEditorStateFromSerializedContent`.
- `EmailSubscriberTest::testManageEmailDraftHandlesSaveAsDraft`.
- `AssetsSubscriberTest::testInjectAssetsSkipsWhenManifestContainsPathTraversal`.
- `FileManagerControllerFunctionalTest::testUploadedSvgIsReturnedInMediaList`.
- `AssertCustomMjmlTest::testAssertCustomHtmlAndCustomMjml`.

## 3. What a good regression test asserts
- Theme selection: the exact keys returned by `getInstalledThemes($feature)` under a given builder (published custom builder vs none) [code: app/bundles/CoreBundle/Tests/Unit/Helper/ThemeHelperTest.php:519-562 @7.x].
- Install: files that exist (and do not exist) on disk after `install()`, including dropped extensions and paths outside the theme root.
- Sandbox: a preview response that is successful for safe templates and does not contain the output of a denied call.
- Builder persistence: `custom_mjml`, `content['grapesjsbuilder']['editorState']` and `custom_html` after a POST with the `grapesjsbuilder` payload.
- Render order: the final email body after send/display listeners (e.g. a token inside a trackable link becomes a tracked URL).

## 4. Skeletons

### 4.1 Unit: a theme is (not) offered for a feature
```php
final class MyThemeSelectionTest extends TestCase
{
    public function testLegacyOnlyThemeHiddenWhenGrapesJsActive(): void
    {
        $paths   = $this->createMock(PathsHelper::class);
        $paths->method('getSystemPath')->willReturn(__DIR__.'/resource/themes');
        $params  = $this->createMock(CoreParametersHelper::class);
        $builder = $this->createMock(BuilderInterface::class);
        $builder->method('getName')->willReturn('grapesjsbuilder');
        $integration = new Integration();
        $integration->setIsPublished(true);
        $builder->method('getIntegrationConfiguration')->willReturn($integration);
        $builders = $this->createMock(BuilderIntegrationsHelper::class);
        $builders->method('getBuilder')->willReturn($builder);

        $helper = new ThemeHelper($paths, $this->createMock(Environment::class),
            $this->createMock(TranslatorInterface::class), $params, new Filesystem(), new Finder(), $builders);

        $themes = $helper->getInstalledThemes('email');
        $this->assertArrayNotHasKey('my-legacy-theme', $themes);
    }
}
```
Constructor order and mocking style follow [code: app/bundles/CoreBundle/Tests/Unit/Helper/ThemeHelperTest.php:64-90,537-562 @7.x].

### 4.2 Unit: zip install drops disallowed files
Build the zip in `sys_get_temp_dir()` with `ZipArchive`, entries `config.json`, `html/message.html.twig`, `evil.php`; stub `theme_import_allowed_extensions`; call `install()`; assert `config.json` exists and `evil.php` does not [code: app/bundles/CoreBundle/Tests/Unit/Helper/ThemeHelperTest.php:72-75,240-275 @7.x] [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:369-372 @7.x]. The zip basename must not be a default theme name [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:333-335 @7.x].

### 4.3 Functional: sandbox blocks a call on Landing Page preview
```php
final class MySandboxTest extends MauticMysqlTestCase
{
    public function testDeniedFunctionIsBlocked(): void
    {
        $dir = self::getContainer()->getParameter('kernel.project_dir').'/themes/sandbox_test_'.uniqid();
        mkdir($dir.'/html', 0777, true);
        file_put_contents($dir.'/config.json', json_encode(['name' => 'x', 'builder' => ['legacy'], 'features' => ['page']]));
        file_put_contents($dir.'/html/base.html.twig', '<html><body>{% block content %}{% endblock %}</body></html>');
        file_put_contents($dir.'/html/page.html.twig',
            "{% extends '@themes/".basename($dir)."/html/base.html.twig' %}{% block content %}{{ configGetParameter('db_password') }}{% endblock %}");

        $page = new Page();
        $page->setTitle('t'); $page->setAlias('t-'.uniqid()); $page->setTemplate(basename($dir));
        $page->setIsPublished(true); $page->setPublicPreview(true);
        $page->setContent(['main' => 'x']);          // customHtml empty → theme path is rendered
        $this->em->persist($page); $this->em->flush();

        $this->client->request('GET', '/page/preview/'.$page->getId());
        $this->assertStringNotContainsString('db_password', (string) $this->client->getResponse()->getContent());
        // remove $dir in tearDown
    }
}
```
Pattern from [code: app/bundles/PageBundle/Tests/Functional/Controller/ThemeHelperSandboxTest.php:22-140 @7.x]. The page needs empty `customHtml` and non-empty `content`, otherwise the theme is not rendered [code: app/bundles/PageBundle/Controller/PublicController.php:330-379 @7.x]. On 8.x this Landing Page fallback is removed, so port such tests to an Email preview or message page [PR #17078].

### 4.4 Functional: GrapesJS email save persists MJML
1. In `setUp`, create a `Plugin` (bundle `GrapesJsBuilderBundle`) and a published `Integration` named `GrapesJsBuilder` [code: plugins/GrapesJsBuilderBundle/Tests/Functional/Controller/AssertCustomMjmlTest.php:129-142 @7.x].
2. POST the email edit form with `emailform[customHtml]` and `grapesjsbuilder[customMjml]`, `grapesjsbuilder[editorState]`.
3. Assert the `bundle_grapesjsbuilder` row for the email has the MJML, `Email::getContent()['grapesjsbuilder']['editorState']` is the decoded array, and `custom_html` equals the posted HTML [code: plugins/GrapesJsBuilderBundle/Model/GrapesJsBuilderModel.php:77-105 @7.x].

## 5. Manual checks (no automated coverage)
- After `composer gjs-build`, `plugins/GrapesJsBuilderBundle/Assets/library/js/dist/manifest.json` exists and an Email edit page loads the hashed bundle [code: plugins/GrapesJsBuilderBundle/EventSubscriber/AssetsSubscriber.php:36-91 @7.x].
- In the browser: select a theme, edit, Apply, reload; confirm MJML mode reopens with editor state and no local-backup prompt [code: plugins/GrapesJsBuilderBundle/Assets/library/js/storage.service.js:138-241 @7.x].
