---
name: mautic-theme-development
description: "Mautic themes and the email and Landing Page builder: theme anatomy (config.json keys, html/email.html.twig, page.html.twig, form and message templates, thumbnails), the Twig sandbox for @themes templates, form theming, themes/system core-view overrides, theme upload/zip rules, hiding default themes, the GrapesJS builder (MJML vs HTML mode, asset manager, dynamic content blocks, code mode, editor fonts, gjs-build), the removed legacy builder, render order (Twig, tokens, trackable URL rewrite) and admin UI design conventions. Use whenever a task mentions a Mautic theme, theme zip, Theme Manager, config.json builder/features, email or page templates, @themes/, ThemeHelper, Twig sandbox errors, GrapesJS, grapesjsbuilder, MJML, the email builder or page builder, custom builder blocks, legacy builder, or touches themes/, plugins/GrapesJsBuilderBundle/ or app/bundles/CoreBundle/Helper/ThemeHelper.php."
---
# Mautic theme development and the GrapesJS builder

## Scope
A Theme is a filesystem package under `themes/<dir>/` of Twig templates that supplies the starting HTML or MJML for Emails, Landing Pages and Forms plus the public message screens; the Builder is the browser-side GrapesJS editor (shipped as `plugins/GrapesJsBuilderBundle`) that edits that content and writes the final HTML back into the entity's `customHtml` [code: plugins/GrapesJsBuilderBundle/Assets/library/js/builder.js:13-47 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html]. Token semantics, sending and tracking belong to `mautic-emails` and `mautic-pages-and-tracking`; form fields, actions and submissions belong to `mautic-forms`; writing a PHP plugin bundle belongs to `mautic-plugin-development`.

Terms: a Contact is a person record; a Landing Page is a Mautic-hosted page; Code Mode is the "no theme, raw HTML" option stored as the literal template value `mautic_code_mode` [code: app/bundles/CoreBundle/Form/Type/ThemeListType.php:25-32 @7.x]; a default theme is one bundled with core (listed in `ThemeHelper::$defaultThemes`) [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:61-103 @7.x].

## Expected behaviour (essentials)

Theme anatomy and discovery
- A directory under `themes/` is a theme only if it contains `config.json` [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:716-751 @7.x].
- `config.json` must have `name`; a theme object without it throws `BadConfigurationException` [code: app/bundles/CoreBundle/Twig/Helper/ThemeHelper.php:36-50 @7.x].
- `features` is a list of `email`, `page`, `form`; a theme without `features` is never offered for any feature [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:756-786 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html#configuration-file].
- `builder` must be an array; absent means `["legacy"]`; a non-array value throws `BadConfigurationException` [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:734-736,778-783 @7.x].
- For a feature, a theme is offered only if `features` contains it AND `builder` contains the active builder's name (`grapesjsbuilder` when GrapesJS is published, else `legacy`) [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:756-786 @7.x]. With GrapesJS published (install default), legacy-only themes (aurora, cards, fresh-*, neopolitan, sunday, …) disappear from the Email and Landing Page pickers [code: plugins/GrapesJsBuilderBundle/InstallFixtures/ORM/GrapesJsData.php:50-52 @7.x].
- GrapesJS supports only `email` and `page`; for `form` the builder lookup fails and `legacy` is assumed, so form themes need `builder` absent or containing `legacy` [code: plugins/GrapesJsBuilderBundle/Integration/Support/BuilderSupport.php:15-19 @7.x].
- `tags` (7.2+) render as labels in the picker; `adaptative` gets a brand-coloured icon [code: app/bundles/CoreBundle/Resources/views/Helper/theme_select.html.twig:59-78 @7.x] [docs: https://docs.mautic.org/en/7.2/themes/manage_themes.html#theme-tags].
- The picker shows `thumbnail_<feature>.png`, else `thumbnail.png`, else a placeholder [code: app/bundles/CoreBundle/Resources/views/Helper/theme_select.html.twig:14-22 @7.x].

Install, hide, delete
- Upload accepts `.zip` only; the theme directory name is the zip basename [code: app/bundles/CoreBundle/Controller/ThemeController.php:59-82 @7.x].
- Install requires `config.json`, `html/message.html.twig`, and `html/<feature>.html.twig` for every declared feature, at the zip root or inside exactly one top-level folder [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:345-406,522-555 @7.x].
- Entries whose extension is not in `theme_import_allowed_extensions` (default json, twig, css, js, htm, html, txt, jpg, jpeg, png, gif) are silently skipped, so `.php`, `.svg`, `.webp` and font files never land [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:349,369-372 @7.x] [code: app/bundles/CoreBundle/Config/config.php:261 @7.x].
- Absolute paths or `..` segments abort the install (zip-slip guard) [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:356-359,481-516 @7.x].
- A zip named like a default theme (including the reserved `system`) is refused [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:333-335 @7.x].
- Re-uploading a non-default theme extracts over the existing directory; files absent from the new zip stay on disk [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:408-470 @7.x].
- Default themes cannot be deleted, only hidden; hiding writes the name to `themes/hidden-themes.txt` and hidden themes are listed last with class `hide` [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:205-222,839-869 @7.x] [code: app/bundles/CoreBundle/Controller/ThemeController.php:261-266,344-352 @7.x].

Rendering
- Templates whose name contains `@themes/` render in a separate sandboxed Twig environment; the policy denies filters `map`, `reduce`, `filter` and functions `configGetParameter`, `getEntity`, `getEntities`, `source`, `ini_get`, `is_file`, `get_class`, `method_exists`, `is_class`, `is_extension_loaded`, `is_function` [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:570-621 @7.x] [code: app/bundles/CoreBundle/Twig/Sandbox/ThemeSandboxPolicy.php:27-83 @7.x].
- `email.html.twig` is a complete document (HTML with doctype, or a raw `<mjml>` document) and does not extend a parent; page, form and message templates extend `@themes/<t>/html/base.html.twig` → `@MauticCore/Theme/base.html.twig` [code: themes/blank/html/email.html.twig:1 @7.x] [code: app/bundles/CoreBundle/Resources/views/Theme/base.html.twig:1-17 @7.x].
- No template ever receives a Contact object; personalisation happens later through tokens such as `{contactfield=firstname}` [code: app/bundles/EmailBundle/Helper/MailHelper.php:1262-1266 @7.x] [code: app/bundles/EmailBundle/Controller/PublicController.php:1056-1065 @7.x].
- Sending uses `customHtml` as-is; the theme's `email.html.twig` is rendered only when `customHtml` is empty (legacy v1 path) [code: app/bundles/EmailBundle/Helper/MailHelper.php:1256-1269 @7.x]. Landing Pages behave the same way [code: app/bundles/PageBundle/Controller/PublicController.php:248-282 @7.x].
- Email render order: Twig (only if `customHtml` empty) → tracking pixel appended → accessibility fix (priority 10000) → dynamic content tokens (254) → core/contact tokens (0) → trackable URL rewriting (-9999) → one search/replace pass [code: app/bundles/EmailBundle/Helper/MailHelper.php:360-385,806-821,1414-1432 @7.x] [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:49-60,228-269 @7.x].
- A missing template falls back to the default theme's copy via `checkForTwigTemplate`; the "any other theme" fallback loop is dead code [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:259-267,667-701 @7.x].

GrapesJS builder
- Opening the builder loads canvas content from the form's textareas (`builder-html`, `builder-mjml`), not from the server; MJML mode is chosen when the MJML textarea is non-empty [code: plugins/GrapesJsBuilderBundle/Assets/library/js/builder.service.js:776-786 @7.x].
- Selecting a theme fetches `/s/grapesjsbuilder/<type>/<id>?template=<t>&resetEditorState=1`; output containing `<mjml>` is returned as `templateMjml` [code: plugins/GrapesJsBuilderBundle/Controller/GrapesJsController.php:146-184 @7.x].
- MJML compiles to HTML in the browser only (`mjml-browser`); MJML sent via the API is never compiled, so API clients must send `customHtml` [code: plugins/GrapesJsBuilderBundle/Assets/library/js/preset-mautic/mjml/mjml.service.js:1,49-83 @7.x].
- For emails, the MJML is stored in the sidecar table `bundle_grapesjsbuilder.custom_mjml`; GrapesJS project JSON is stored in `content['grapesjsbuilder']['editorState']` on both Emails and Landing Pages [code: plugins/GrapesJsBuilderBundle/Entity/GrapesJsBuilder.php:31-44 @7.x] [code: plugins/GrapesJsBuilderBundle/Model/GrapesJsBuilderModel.php:77-118 @7.x].
- On email save the plugin re-sets `customHtml` from the raw request after form sanitisation and saves again through the repository [code: plugins/GrapesJsBuilderBundle/Model/GrapesJsBuilderModel.php:97-104 @7.x].
- Uploaded images go to `media/images/` (no sub-folder) and are returned as absolute URLs [code: plugins/GrapesJsBuilderBundle/Helper/FileManager.php:18,32-49,74-83 @7.x].
- Dynamic content blocks (`data-slot="dynamicContent"`) are serialised to `{dynamiccontent="<name>"}` tokens on save and exist only in email modes [code: plugins/GrapesJsBuilderBundle/Assets/library/js/preset-mautic/dynamicContent/dynamicContent.commands.js:82-110 @7.x] [code: plugins/GrapesJsBuilderBundle/Assets/library/js/preset-mautic/blocks.js:20-28 @7.x].
- The builder keeps up to 10 local-storage backups (`gjs-storage`) and offers Restore/Dismiss when a backup differs [code: plugins/GrapesJsBuilderBundle/Assets/library/js/storage.service.js:4-22,138-241 @7.x] [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#restoring-unsaved-changes].
- Builder JS/CSS are content-hashed Parcel output resolved through `dist/manifest.json`; if the manifest is missing the builder is silently not injected (warning in the log) [code: plugins/GrapesJsBuilderBundle/EventSubscriber/AssetsSubscriber.php:36-91 @7.x].
- The legacy (Froala/slot) builder was removed in 6.0; core `Mautic.launchBuilder` only alerts the user to enable a builder plugin [code: app/bundles/CoreBundle/Assets/js/4.builder.js:1-3 @7.x] [code: UPGRADE-6.0.md:4-15 @7.x].

## Where it lives

| Concern | Path |
|---|---|
| Theme discovery, install, zip, hide, render | `app/bundles/CoreBundle/Helper/ThemeHelper.php` |
| Per-theme value object | `app/bundles/CoreBundle/Twig/Helper/ThemeHelper.php` |
| Twig sandbox policy | `app/bundles/CoreBundle/Twig/Sandbox/ThemeSandboxPolicy.php` |
| Theme Twig functions | `app/bundles/CoreBundle/Twig/Extension/ThemesExtension.php`, `ThemeExtension.php` |
| `themes/system` overrides | `app/bundles/CoreBundle/DependencyInjection/Compiler/SystemThemeTemplatePathPass.php` |
| Core parent templates | `app/bundles/CoreBundle/Resources/views/Theme/{base,message,email-validation}.html.twig` |
| Theme Manager UI / API | `CoreBundle/Controller/ThemeController.php`, `Controller/Api/ThemeApiController.php` (`/s/themes`, `/api/themes`) |
| Theme picker / builder markup | `CoreBundle/Resources/views/Helper/{theme_select,builder}.html.twig` |
| Builder selection | `app/bundles/IntegrationsBundle/Helper/BuilderIntegrationsHelper.php`, `Integration/Interfaces/BuilderInterface.php` |
| GrapesJS PHP | `plugins/GrapesJsBuilderBundle/{Controller,Model,EventSubscriber,Helper,Entity}/` |
| GrapesJS JS | `plugins/GrapesJsBuilderBundle/Assets/library/js/` (entry `builder.js`, build to `dist/`) |
| Bundled themes | `themes/<dir>/` (44 dirs) |
| Config parameters | `theme`, `theme_import_allowed_extensions`, `brand_name`, `primary_brand_color`, `rounded_corners`, `editor_fonts` (CoreBundle); `theme_email_default` (EmailBundle); `image_path_exclude`, `static_url` (plugin) |
| Permissions | `core:themes:view|create|edit|delete` |
| Tests | `CoreBundle/Tests/Unit/Helper/ThemeHelperTest.php`, `PageBundle/Tests/Functional/Controller/ThemeHelperSandboxTest.php`, `plugins/GrapesJsBuilderBundle/Tests/` |

Full detail with line numbers: references/code-map.md.

## How to change or extend it
### Minimal valid theme skeleton
The smallest theme that installs through the Theme Manager and is offered for GrapesJS emails and Landing Pages. Each rule is enforced by `ThemeHelper::install()` [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:345,379-388 @7.x] and `getInstalledThemes()` [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:756-786 @7.x].

```
my-theme.zip                      (zip basename = theme dir name; must not match a default theme)
├── config.json                   required
├── thumbnail.png                 optional (picker placeholder otherwise)
└── html/
    ├── base.html.twig            {% extends '@MauticCore/Theme/base.html.twig' %}
    ├── message.html.twig         required for every theme: {% extends '@MauticCore/Theme/message.html.twig' %}
    ├── email.html.twig           required because "email" is in features (HTML or <mjml> document)
    └── page.html.twig            required because "page" is in features
```

```json
{
  "name": "My Theme",
  "author": "Example Ltd",
  "authorUrl": "https://example.com",
  "features": ["email", "page"],
  "builder": ["grapesjsbuilder"],
  "tags": ["newsletter"]
}
```

`page.html.twig` minimum: `{% extends "@themes/"~template~"/html/base.html.twig" %}{% block content %}…{% endblock %}` [code: themes/blank/html/page.html.twig:1-3 @7.x]. Add `"form"` to `features` only with `html/form.html.twig` and with `"legacy"` in `builder` [code: plugins/GrapesJsBuilderBundle/Integration/Support/BuilderSupport.php:15-19 @7.x]. `themes/blank/` is the reference implementation of every file [code: themes/blank/config.json @7.x].

### Guidance
- Build themes from `themes/blank/` and keep `message.html.twig` even for email-only themes, or the zip will not install [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:345 @7.x].
- Put email starting markup in `email.html.twig` as MJML; do not create `email.mjml.twig`, which is deprecated since 5.0 [code: plugins/GrapesJsBuilderBundle/Controller/GrapesJsController.php:157-161,229-239 @7.x].
- Declare MJML theme tokens as `<mj-class name="t-…">` inside `<mj-attributes>` with explicit closing tags; the builder auto-applies them to dropped text, button and section components [code: plugins/GrapesJsBuilderBundle/Assets/library/js/plugins/grapesjs-mjmlThemeTokens/index.js:7-44 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#mjml-theme-tokens].
- Reference theme files with `getAssetUrl('themes/'~template~'/img/x.png', null, null, true)` so URLs are absolute in sent mail [code: themes/neopolitan/html/page.html.twig:28 @7.x].
- Use only sandbox-safe Twig in `@themes/` templates; test by rendering a preview, because a denied call throws a Twig security error at render [code: app/bundles/CoreBundle/Twig/Sandbox/ThemeSandboxPolicy.php:27-51 @7.x].
- Override form markup per theme with `themes/<t>/Field/<type>.html.twig`, `html/MauticFormBundle/Builder/{form,_style}.html.twig` and `MauticForm/Builder/_script.html.twig` (note the different roots) [code: app/bundles/FormBundle/Model/FormModel.php:412-470,702-719 @7.x].
- Override any core view globally by copying it to `themes/system/<BundleName>/Resources/views/…` and clearing cache; recheck after every upgrade [code: app/bundles/CoreBundle/DependencyInjection/Compiler/SystemThemeTemplatePathPass.php:30-33,90-96 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/themes/system.html].
- Add GrapesJS behaviour without forking: push `{name, plugin, context, pluginOptions}` onto `window.MauticGrapesJsPlugins` from a script injected on `CoreEvents::VIEW_INJECT_CUSTOM_ASSETS` before `builder.js` loads [code: plugins/GrapesJsBuilderBundle/Assets/library/js/builder.service.js:753-771 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#grapesjs-builder-plugins].
- Add builder tokens by subscribing to `EmailEvents::EMAIL_ON_BUILD` / `PageEvents::PAGE_ON_BUILD` and replace them on send/display (see `mautic-emails`) [code: app/bundles/CoreBundle/Event/BuilderEvent.php:73-260 @7.x].
- Ship an alternative builder by implementing `BuilderInterface` on a `BasicIntegration`; the first published builder whose `isSupported($feature)` is true wins, and themes must list its name in `builder` [code: app/bundles/IntegrationsBundle/Helper/BuilderIntegrationsHelper.php:37-49 @7.x].
- After changing GrapesJS JS, run `composer gjs-build` (or `ddev gjs-build`); `dist/` is git-ignored [code: plugins/GrapesJsBuilderBundle/.gitignore @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#building-the-builder-assets].
- Distribute a theme through Composer as type `mautic-theme` with `extra.install-directory-name` [code: themes/blank/composer.json @7.x].
- For admin UI templates follow the design conventions (inactive states over hiding, `no-information.html.twig`, utility classes): see references/docs-digest.md §4.

## How to test it
- Unit-test theme rules with `ThemeHelperTest` (plain `TestCase`, mocked `PathsHelper`/Twig loader/`BuilderIntegrationsHelper`, real zips in the temp dir) [code: app/bundles/CoreBundle/Tests/Unit/Helper/ThemeHelperTest.php:170-190,248-275 @7.x].
- Test controllers and rendering with `MauticMysqlTestCase`: `ThemeControllerTest::testThemeVisibility`, `ThemeHelperSandboxTest::testHarmfulTwigPayloadsAreBlockedOnPagePreview` [code: app/bundles/PageBundle/Tests/Functional/Controller/ThemeHelperSandboxTest.php:41-119 @7.x].
- GrapesJS tests live in `plugins/GrapesJsBuilderBundle/Tests/` with their own `phpunit.xml`; functional tests must create the `Plugin` row and a published `Integration` row themselves [code: plugins/GrapesJsBuilderBundle/Tests/Functional/Controller/AssertCustomMjmlTest.php:129-142 @7.x].
- Copy from: `ThemeHelperTest::testThemeIsInstalled`, `::testCustomThemesAreReturnedForFeatureIfCustomBuilderIsEnabled`, `GrapesJsBuilderModelEditorStateTest::testAddOrEditEntityStoresDecodedEditorStateAndCustomHtmlFallback`, `FileManagerControllerFunctionalTest::testUploadedSvgIsReturnedInMediaList`, `AssetsSubscriberTest::testInjectAssetsSkipsWhenManifestContainsPathTraversal`.
- No JS unit tests exist for the builder; verify builder changes manually in a browser [code: plugins/GrapesJsBuilderBundle/package.json @7.x].
- A good regression test asserts the observable outcome: which themes a feature offers, which zip entries land on disk, that a denied Twig call fails the preview, or the exact `customHtml`/`custom_mjml` stored after save.

Full detail and skeletons: references/test-patterns.md.

## Version notes
- 5.0: `email.mjml.twig` deprecated in favour of MJML inside `email.html.twig`; themes coffee, Mauve, nature removed [code: plugins/GrapesJsBuilderBundle/Controller/GrapesJsController.php:157-161 @7.x] [code: UPGRADE-5.0.md:101 @7.x].
- 5.1: `window.MauticGrapesJsPlugins` registration [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#grapesjs-builder-plugins]. 5.2: media endpoint replaces `/s/grapesjsbuilder/assets` [code: plugins/GrapesJsBuilderBundle/Config/config.php:21-24 @7.x].
- 6.0: legacy builder and `MauticFactory::getTheme/getInstalledThemes` removed [code: UPGRADE-6.0.md:4-15,60-61 @7.x].
- 7.2: MJML theme tokens (`mj-class`); devdocs say 7.0 but the code first ships in tag 7.2.0 [PR #16042] [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#mjml-theme-tokens]. Also 7.2: `tags` key, Typography block category, builder assets built at install instead of committed [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#typography] [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#building-the-builder-assets]. 7.2.1: optional `html/email-validation.html.twig` [code: app/bundles/EmailBundle/Controller/PublicController.php:168 @7.x].
- 5.0: CKEditor 5 replaces CKEditor 4 in GrapesJS; Code Mode content opens in the builder after a warning instead of being blocked [PR #12641] [PR #11339].
- 5.1: local autosave with restore prompt; Apply saves a new email or page without leaving the builder [PR #13610] [PR #13665].
- 5.2: Blank becomes MJML, 13 `_`-prefixed starter themes, `grapesjsbuilder.customMjml` in the email API; 5.2.2 moves `themes/@defaults` into `@MauticCore/Theme/*` [PR #14255] [PR #14155] [PR #13775] [PR #14425].
- 6.0: primary brand colour and company name in Theme settings; new Landing Page and form themes; Goldstar, Neopolitan, Oxygen, Skyline stop being form themes [PR #14649] [PR #14519] [PR #14547] [PR #14588].
- 7.1.3: CKEditor keeps valid inline CSS and strips only MS Word styles; table editing restored in the same patch [PR #16058] [PR #16476].
- 8.x: Landing Pages with empty `customHtml` no longer fall back to theme `page.html.twig` and the `public` template variable is gone [PR #17078]; `/grapesjsbuilder/assets` removed [PR #17070]; `EmojiHelper` removed [PR #17026]; `TwigPass` removed [PR #17117]; Bootstrap stack undecided on the 8.x snapshot. See references/version-notes.md.

## Pitfalls
- Disabling GrapesJS does not bring back a legacy builder in 6.0+; the docs page that says it does is stale [code: app/bundles/CoreBundle/Assets/js/4.builder.js:1-3 @7.x] [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#switching-back-to-the-legacy-builder].
- `"builder": "grapesjsbuilder"` as a string (old 3.x syntax, still shown in a docs example) throws; use an array [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:781-783 @7.x] [docs: https://docs.mautic.org/en/7.2/builders/creating_themes.html#modifying-legacy-themes].
- Changing an email's theme in the UI replaces existing content after a confirmation; it is not a re-skin [code: app/bundles/CoreBundle/Assets/js/4.builder.js:64-131 @7.x].
- Editing `email.html.twig` after emails were created changes nothing in those emails, because they send their saved `customHtml` [code: app/bundles/EmailBundle/Helper/MailHelper.php:1256-1269 @7.x].
- A theme overriding the form wrapper and copying `configGetParameter('form_field_autofill')` from core will fail in the sandbox [code: app/bundles/FormBundle/Resources/views/Builder/form.html.twig:29 @7.x] [code: app/bundles/CoreBundle/Twig/Sandbox/ThemeSandboxPolicy.php:27-51 @7.x].
- `theme_email_default` (an Email parameter) is also the fallback for Landing Pages whose theme was removed [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:788-795 @7.x].
- The GrapesJS file-manager endpoints have no permission check beyond the `/s/` firewall, and delete refuses non-image files [code: plugins/GrapesJsBuilderBundle/Controller/FileManagerController.php:31-43 @7.x].
- If Node is missing, `composer install` warns and continues; the builder then silently does not load [code: build/gjs_build.php:5-13 @7.x].
- `static_url` defaults to `''` and `FileManager::getFullUrl` uses `??`, so an empty `static_url` is not replaced by `site_url`; check upload URLs on instances without a CDN [code: plugins/GrapesJsBuilderBundle/Helper/FileManager.php:77 @7.x] [code: plugins/GrapesJsBuilderBundle/Config/config.php:45 @7.x] [unverified: runtime normalisation elsewhere].
- `ThemeHelper::rename()` updates `config.json` using the pre-rename path and likely throws [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:200-202 @7.x].
- Open question (docs vs code): thumbnails are 575x600 in devdocs and 400x600 in user docs; code does not check size [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html#thumbnails] [docs: https://docs.mautic.org/en/7.2/builders/creating_themes.html#steps-to-save-the-theme-package].
- Open question: devdocs place `email-validation.html.twig` in 8.0 docs only, but it is on the 7.x branch after 7.2.1 (unreleased; [PR #16870]) and not yet on the 8.x branch [code: app/bundles/EmailBundle/Controller/PublicController.php:168 @7.x] [devdocs: https://devdocs.mautic.org/en/8.0/themes/getting_started.html#html-email-validation-html-twig].
- A theme that extends `@MauticCore/Theme/base.html.twig` or calls `getRoundedCorners` breaks on older cores unless its `composer.json` raises `mautic/core-lib` (≥5.2.2, ^7.0) [PR #14621] [PR #14657].
- Use `#` for placeholder hrefs in theme markup; a bare `https://` href is rejected on save [PR #16778] [PR #16892].
- Head tags marked `data-source="mautic"` are stripped when GrapesJS content is saved; do not use that attribute on theme head assets you want to keep [PR #10360].
- A theme's form `_style.html.twig` override must follow core form-style changes, or layout fixes such as 50%-width columns do not reach it [PR #16281].
- Builder localStorage backups are not scoped by user; on a shared browser another user can be offered a draft [PR #13610].

More: references/behaviour.md §9.

## Related skills
- `mautic-emails` — token semantics, sending pipeline, email drafts, A/B tests, dynamic content in emails.
- `mautic-pages-and-tracking` — Landing Page display, preference centre slots, trackable URLs, tracking pixel.
- `mautic-forms` — form fields, actions, submissions, embedding; use this skill only for form theming.
- `mautic-plugin-development` — building the bundle that injects assets, subscribes to builder events or implements `BuilderInterface`.
- `mautic-dev-environment` — DDEV, `ddev gjs-build`, Node, asset generation.
- `mautic-testing` — base test classes, running PHPUnit, fixtures.
- `mautic-upgrades-and-versions` — release lines and upgrade procedures.

## Reference files
- references/behaviour.md — full numbered behaviour spec (themes, sandbox, variables, install, GrapesJS load/save, render order, forms, legacy).
- references/code-map.md — files, classes, routes, parameters, permissions, events, tables, JS modules, tests.
- references/docs-digest.md — what the user docs and devdocs say, procedures, design/UI conventions, terminology.
- references/test-patterns.md — base classes, representative tests, fixtures, test skeletons.
- references/version-notes.md — 5.x/6.x history, 7.x minors, the 8.x delta.
- references/pr-history.md — why and when: decisions, regression catalogue, feature timeline and removals from merged PRs.
