# Themes and builder — code map (Mautic 7.x)

All paths relative to the repository root; all tags `@7.x` unless marked.

## Database
| Table / column | Meaning | Source |
|---|---|---|
| `bundle_grapesjsbuilder` (`id`, `email_id` FK → emails ON DELETE CASCADE, `custom_mjml` TEXT, `draft_custom_mjml` TEXT) | MJML sidecar, at most one row per email (not enforced by a unique key); no row for Landing Pages | [code: plugins/GrapesJsBuilderBundle/Entity/GrapesJsBuilder.php:31-44 @7.x] |
| `emails.template` | theme dir name or `mautic_code_mode` | [code: app/bundles/EmailBundle/Entity/Email.php:389 @7.x] |
| `emails.content` (PHP-serialised array) | legacy slot content + `grapesjsbuilder.editorState`, `updatedAt` | [code: app/bundles/EmailBundle/Entity/Email.php:390 @7.x] |
| `emails.custom_html` | final HTML that is sent | [code: app/bundles/EmailBundle/Entity/Email.php:393 @7.x] |
| `emails.public_preview` (default false) | anonymous preview allowed | [code: app/bundles/EmailBundle/Entity/Email.php:201,454 @7.x] |
| `pages.template`, `pages.custom_html`, `pages.content`, `pages.public_preview` (default true) | same for Landing Pages | [code: app/bundles/PageBundle/Entity/Page.php:203,242-249,312 @7.x] |
| `forms.template` | theme for form styling/standalone page | [code: app/bundles/FormBundle/Model/FormModel.php:415 @7.x] |
| `themes/hidden-themes.txt` (file, not DB) | hidden default themes, `|`-separated | [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:24,800-820 @7.x] |

## Core theme classes
| Class | Role | Source |
|---|---|---|
| `Mautic\CoreBundle\Helper\ThemeHelper` (+ `ThemeHelperInterface`) | discovery, install, zip, copy, rename, delete, visibility, sandboxed render, template fallback | [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:110-899 @7.x] |
| `ThemeHelper::$defaultThemes` / `addDefaultThemes()` | undeletable themes (incl. reserved `system`); plugins can add | [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:61-134 @7.x] |
| `Mautic\CoreBundle\Twig\Helper\ThemeHelper` | per-theme value object (`getName`, `getTheme`, `getConfig`, `getThemePath`, `getErrorPageTemplate`) | [code: app/bundles/CoreBundle/Twig/Helper/ThemeHelper.php:58-106 @7.x] |
| `Twig\Sandbox\ThemeSandboxPolicy` | deny-list | [code: app/bundles/CoreBundle/Twig/Sandbox/ThemeSandboxPolicy.php:27-83 @7.x] |
| `Twig\Extension\ThemesExtension` | `getBrandPrimaryColor`, `getTextOnBrandColor`, `getTextOnBrandHelperColor`, `getRoundedCorners` | [code: app/bundles/CoreBundle/Twig/Extension/ThemesExtension.php:18-70 @7.x] |
| `Twig\Extension\ThemeExtension` | `getThemeName` | [code: app/bundles/CoreBundle/Twig/Extension/ThemeExtension.php:30-40 @7.x] |
| `Twig\Helper\AssetsHelper` | `getOverridableUrl`; injects `Mautic.getActiveBuilderName()` | [code: app/bundles/CoreBundle/Twig/Helper/AssetsHelper.php:88-100,440-447 @7.x] |
| `Helper\ThemeSearchFilter`, `ThemeSearchScopeProvider` | Theme Manager search (feature/builder commands; dir, name, author text) | [code: app/bundles/CoreBundle/Helper/ThemeSearchFilter.php:64-70 @7.x] |
| `DependencyInjection\Compiler\SystemThemeTemplatePathPass` | registers `themes/system/<Bundle>/Resources/views` overrides | [code: app/bundles/CoreBundle/DependencyInjection/Compiler/SystemThemeTemplatePathPass.php:30-33,90-96 @7.x] |
| `Form\Type\ThemeListType`, `ThemeUploadType`, `ConfigThemeType` | dropdown (adds Code Mode), upload, Theme Settings | [code: app/bundles/CoreBundle/Form/Type/ThemeListType.php:25-32 @7.x] [code: app/bundles/CoreBundle/Form/Type/ConfigThemeType.php:54-107 @7.x] |
| `IntegrationsBundle\Integration\Interfaces\BuilderInterface`, `Helper\BuilderIntegrationsHelper` | builder plug-point (`mautic.builder_integration` tag, autoconfigured) | [code: app/bundles/IntegrationsBundle/Helper/BuilderIntegrationsHelper.php:37-59 @7.x] [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:32-33 @7.x] |
| `CoreBundle\Event\BuilderEvent` (Email/PageBuilderEvent) | token registration | [code: app/bundles/CoreBundle/Event/BuilderEvent.php:73-260 @7.x] |
| `CoreBundle\Model\BuilderModelTrait` | common builder components (tokens) | [code: app/bundles/CoreBundle/Model/BuilderModelTrait.php:18-42 @7.x] |

## Core templates
- `app/bundles/CoreBundle/Resources/views/Theme/base.html.twig`, `message.html.twig`, `email-validation.html.twig` — parents themes extend.
- `app/bundles/CoreBundle/Resources/views/Theme/{index,list,list_results,_list_results,form}.html.twig` — Theme Manager.
- `app/bundles/CoreBundle/Resources/views/Helper/theme_select.html.twig` — picker cards; `Helper/builder.html.twig` — builder container, `#builder_url`, `#customHtmlContainer`.
- `app/bundles/CoreBundle/Resources/views/Slots/*.html.twig` — preference-centre slot renderers.
- `app/bundles/FormBundle/Resources/views/Builder/{form,_style,_script}.html.twig`, `Field/<type>.html.twig` — form defaults themes override.

## Routes
| Route | Path | Controller | Permission |
|---|---|---|---|
| `mautic_themes_index` | `/s/themes` | `ThemeController::indexAction` | `core:themes:view` |
| `mautic_themes_action` | `/s/themes/{objectAction}/{objectId}` (download, delete, batchDelete, visibility) | `ThemeController` | view / delete |
| `mautic_core_api_theme_list` | `GET /api/themes` | `ThemeApiController::listAction` | view |
| `mautic_core_api_theme_get` | `GET /api/themes/{theme}` (zip) | `getAction` | view |
| `mautic_core_api_theme_create` | `POST /api/themes/new` | `newAction` | `core:themes:create` |
| `mautic_core_api_theme_delete` | `DELETE /api/themes/{theme}/delete` | `deleteAction` | `core:themes:delete` |
| `mautic_email_action` builder | `/s/emails/builder/{id}` | `EmailController::builderAction` (raw template) | entity view |
| `mautic_page_action` builder | `/s/pages/builder/{id}` | `PageController::builderAction` | entity view |
| `grapesjsbuilder_builder` | `/s/grapesjsbuilder/{objectType}/{objectId}?template=&resetEditorState=` | `GrapesJsController::builderAction` → JSON `{templateHtml, templateMjml}` | entity create/view |
| `grapesjsbuilder_editor_state` | `GET /s/grapesjsbuilder/{objectType}/{objectId}/editor-state` | `editorStateAction` | entity view |
| `grapesjsbuilder_upload` / `_delete` / `_media` | `/s/grapesjsbuilder/upload`, `/delete?filename=`, `/media?page=&limit=` | `FileManagerController` | `/s/` firewall only |
| `grapesjsbuilder_assets` | `/s/grapesjsbuilder/assets` | deprecated since 5.2 | — |
| `mautic_email_preview` | `/email/preview/{objectId}/{objectType}` | `EmailBundle\Controller\PublicController::previewAction` | published+publicPreview or view |
| `mautic_page_preview` | `/page/preview/{id}/{objectType}` | `PageBundle\Controller\PublicController::previewAction` | same |
| AJAX tokens | `/s/ajax?action=email:getBuilderTokens` / `page:getBuilderTokens` | `CoreBundle\Controller\AjaxController::getBuilderTokensAction` | — |

Sources: [code: app/bundles/CoreBundle/Config/config.php:23-30,85-102,144-148 @7.x] [code: plugins/GrapesJsBuilderBundle/Config/config.php:21-24 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/SystemPermissions.php:15,25 @7.x] [code: plugins/GrapesJsBuilderBundle/Controller/GrapesJsController.php:104-227 @7.x] [code: app/bundles/EmailBundle/Config/config.php:103-111 @7.x] [code: app/bundles/PageBundle/Config/config.php:49-51 @7.x].

## Configuration parameters
| Parameter | Default | Effect | Source |
|---|---|---|---|
| `theme` | `blank` | system default theme (forms, message pages, Code Mode fallback) | [code: app/bundles/CoreBundle/Config/config.php:260 @7.x] |
| `theme_import_allowed_extensions` | json, twig, css, js, htm, html, txt, jpg, jpeg, png, gif | zip entries kept on install | [code: app/bundles/CoreBundle/Config/config.php:261 @7.x] |
| `theme_email_default` | `blank` | fallback when an entity's theme is gone | [code: app/bundles/EmailBundle/Config/config.php:211 @7.x] |
| `brand_name`, `primary_brand_color` (`000000`), `rounded_corners` (`0`) | | `ThemesExtension` functions | [code: app/bundles/CoreBundle/Config/config.php:262-264 @7.x] |
| `image_path` | `media/images` | builder upload dir | [code: app/bundles/CoreBundle/Config/config.php:257 @7.x] |
| `image_path_exclude` | `['flags','mejs']` | hidden from media listing | [code: plugins/GrapesJsBuilderBundle/Config/config.php:44 @7.x] |
| `static_url` | `''` | CDN base for image URLs | [code: plugins/GrapesJsBuilderBundle/Config/config.php:45 @7.x] |
| `editor_fonts` | list of name/font/url | builder fonts, JS `mauticEditorFonts` | [code: app/bundles/CoreBundle/Config/config.php:721 @7.x] |
| `mailer_append_tracking_pixel`, `mailer_convert_embed_images`, `minify_email_html` | | post-builder HTML changes | [code: app/bundles/EmailBundle/Helper/MailHelper.php:383-385,808-814,1231-1233 @7.x] |

## Events
| Event | Listener | Effect | Source |
|---|---|---|---|
| `CoreEvents::VIEW_INJECT_CUSTOM_ASSETS` | `GrapesJs AssetsSubscriber::injectAssets` | adds hashed builder JS/CSS on `/s/` | [code: plugins/GrapesJsBuilderBundle/EventSubscriber/AssetsSubscriber.php:29-99 @7.x] |
| `CoreEvents::VIEW_INJECT_CUSTOM_CONTENT` | `InjectCustomContentSubscriber` | `email.settings.advanced` → hidden `grapesjsbuilder[customMjml]`; `page.header.left` → `#grapesjsbuilder_assets` | [code: plugins/GrapesJsBuilderBundle/EventSubscriber/InjectCustomContentSubscriber.php:32-97 @7.x] |
| `EmailEvents::EMAIL_PRE_SAVE` / `EMAIL_POST_SAVE` / `EMAIL_POST_DELETE` / `ON_EMAIL_EDIT_SUBMIT` | `EmailSubscriber` | draft capture, sidecar persist, delete, draft apply | [code: plugins/GrapesJsBuilderBundle/EventSubscriber/EmailSubscriber.php:44-117 @7.x] |
| `PageEvents::PAGE_POST_SAVE` | `PageSubscriber` | editor state | [code: plugins/GrapesJsBuilderBundle/EventSubscriber/PageSubscriber.php:21-35 @7.x] |
| JMS `POST_SERIALIZE` | `SerializerSubscriber::addCustomMJML` | API `grapesjsbuilder.customMjml` | [code: plugins/GrapesJsBuilderBundle/EventSubscriber/SerializerSubscriber.php:27-62 @7.x] |
| `EmailEvents::EMAIL_ON_BUILD`, `PageEvents::PAGE_ON_BUILD` | token providers | builder token lists | [code: app/bundles/EmailBundle/Model/EmailModel.php:566-567 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:770-771 @7.x] |
| `EmailEvents::EMAIL_ON_SEND` / `EMAIL_ON_DISPLAY` | accessibility 10000, DC tokens 254, tokens 0, URL→tokens -9999 | render order | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:49-60 @7.x] |
| `PageEvents::PAGE_ON_DISPLAY` | Page `BuilderSubscriber::onPageDisplay` (0), DWC (254) | page tokens/slots | [code: app/bundles/PageBundle/EventListener/BuilderSubscriber.php:28-54 @7.x] |

No events are dispatched by the theme code or the GrapesJS plugin.

## GrapesJS plugin (`plugins/GrapesJsBuilderBundle/`)
- PHP: `Integration/GrapesJsBuilderIntegration.php` (`NAME = 'grapesjsbuilder'`), `Integration/Support/BuilderSupport.php`, `Integration/Config.php`, `Model/GrapesJsBuilderModel.php`, `Helper/FileManager.php`, `Controller/GrapesJsController.php`, `Controller/FileManagerController.php`, `InstallFixtures/ORM/GrapesJsData.php`, `Config/services.php`, `Config/config.php`, `Resources/views/{Builder/template,Setting/fields}.html.twig` [code: plugins/GrapesJsBuilderBundle/Config/services.php:24-39 @7.x].
- JS (`Assets/library/js/`): `builder.js` (entry), `builder.service.js` (init per mode, plugin registry, CKEditor, asset manager), `editorState.service.js`, `storage.service.js`, `asset.service.js`, `mjmlStyles.service.js`, `codeMode/`, `commands/`, `preset-mautic/{blocks,buttons,dynamicContent,editorFonts,mjml,panels}/`, `preset-mautic/content.service.js`, `plugins/{grapesjs-ckeditor,grapesjs-mjmlThemeTokens,grapesjs-image-link}/`.
- Build: `package.json` (grapesjs ^0.22.16, grapesjs-mjml ^1.0.6, Parcel ^2.16.4), `scripts/manifest-reporter.js` writes `dist/manifest.json`; root `composer gjs-build` / `gjs-build-safe`, `build/gjs_build.php` hook (non-fatal) [code: plugins/GrapesJsBuilderBundle/scripts/manifest-reporter.js:13-32 @7.x] [code: build/gjs_build.php:5-13 @7.x].
- Root front-end build is separate: `npm run build` builds only CKEditor 5 into `media/libraries/ckeditor/`; `bin/console mautic:assets:generate` produces `media/css/app.css`, `libraries.css`, `media/js/app.js`, `libraries.js`; AssetMapper entry `app/bundles/CoreBundle/Assets/app.js` [code: webpack.config.js:30-40 @7.x] [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:24-27,106-110 @7.x].

## Shared admin JS used by builders
`app/bundles/CoreBundle/Assets/js/4.builder.js`: `Mautic.launchBuilder` stub, theme selection, `inBuilder` hidden input, `Mautic.sanitizeHtmlBeforeSave`, `openMediaManager` (elFinder), `getBuilderTokensMethod` [code: app/bundles/CoreBundle/Assets/js/4.builder.js:1-131 @7.x].

## Bundled themes (44 dirs)
| Group | Dirs | features / builder |
|---|---|---|
| Dropsolid MJML | `_1-2-1-2-column`, `_1-2-1-column`, `_1-2-column`, `_1-3-1-3-column`, `_1-3-column`, `_connect-through-content`, `_educate`, `_gallery`, `_make-announcement`, `_showcase`, `_simple-text`, `_survey`, `_welcome` | email / grapesjsbuilder, tags adaptative+newsletter |
| GrapesJS email | `attract`, `brienz`, `confirmme`, `creative`, `paprika`*, `trulypersonal`* | email / grapesjsbuilder (*only deprecated `email.mjml.twig`) |
| GrapesJS page | `blend`, `capture`, `formscape`, `mono`, `reachout` | page / grapesjsbuilder |
| All features | `blank` | page, email, form / legacy + grapesjsbuilder; ships `email-validation.html.twig` |
| Legacy | `aurora`, `cards`, `goldstar`, `sparse`, `vibrant` (email); `fresh-center/-fixed/-left/-wide` (page); `neopolitan`, `oxygen`, `skyline` (page, email); `sunday` (all) | no `builder` → legacy |
| Form style | `chord`, `eclipse`, `multi-step` | form / legacy |

Source: each `themes/<dir>/config.json` [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:61-103 @7.x]. User-installed themes are git-ignored [code: .gitignore:127-136 @7.x].

## Tests
- `app/bundles/CoreBundle/Tests/Unit/Helper/ThemeHelperTest.php` (21 tests)
- `app/bundles/CoreBundle/Tests/Functional/Controller/ThemeControllerTest.php`
- `app/bundles/CoreBundle/Tests/Functional/DependencyInjection/Compiler/SystemThemeTemplatePathPassTest.php`
- `app/bundles/PageBundle/Tests/Functional/Controller/ThemeHelperSandboxTest.php`
- `app/bundles/CoreBundle/Tests/Twig/ThemesExtensionTest.php`, `Tests/Unit/Helper/ThemeSearchFilterTest.php`, `ThemeSearchScopeProviderTest.php`
- `app/bundles/IntegrationsBundle/Tests/Unit/Helper/BuilderIntegrationsHelperTest.php`
- `app/bundles/EmailBundle/Tests/EventListener/BuilderSubscriberTest.php`, `BuilderSubscriberFunctionalTest.php`; `app/bundles/PageBundle/Tests/Functional/EventListener/BuilderSubscriberTest.php`
- `plugins/GrapesJsBuilderBundle/Tests/{Functional/Controller/AssertCustomMjmlTest,FileManagerControllerFunctionalTest}.php`, `Tests/Unit/Controller/GrapesJsControllerTest.php`, `Tests/Unit/Model/{GrapesJsBuilderModelTest,GrapesJsBuilderModelEditorStateTest}.php`, `Tests/Unit/EventSubscriber/{Assets,Email,InjectCustomContent,Page}SubscriberTest.php`, `Tests/InstallFixtures/ORM/GrapeJsDataTest.php`
