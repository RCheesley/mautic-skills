# Themes and builder — version notes

## History before 5.x (context only)
- GrapesJS arrived in Mautic 3 (opt-in from 3.3-RC1) and became the default in Mautic 4; the `builder` key changed from a string to an array between 3.3 and 4 [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#enabling-the-builder] [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#templates].
- `PageBundle\Controller\PublicController` still carries comments that the `content`-based (v1) rendering was "BC support to be removed in 3.0" and `'public' => true` "Remove in 2.0" [code: app/bundles/PageBundle/Controller/PublicController.php:252-254,374 @7.x].

## 5.x
- 5.0: `html/email.mjml.twig` deprecated; put MJML directly in `email.html.twig` [code: plugins/GrapesJsBuilderBundle/Controller/GrapesJsController.php:157-161,229-239 @7.x].
- 5.0: bundled themes `coffee`, `Mauve`, `nature` removed [code: UPGRADE-5.0.md:101 @7.x].
- 5.1: third-party GrapesJS plugins via `window.MauticGrapesJsPlugins` [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#grapesjs-builder-plugins].
- 5.2: paginated `/s/grapesjsbuilder/media` replaces `/s/grapesjsbuilder/assets` (deprecated, still routed in 7.2) [code: plugins/GrapesJsBuilderBundle/Config/config.php:21-24 @7.x].

## 6.x
- 6.0: legacy (Froala/slot) builder removed; `Mautic.launchBuilder` in core became an alert stub [code: UPGRADE-6.0.md:4-15 @7.x] [code: app/bundles/CoreBundle/Assets/js/4.builder.js:1-3 @7.x].
- 6.0: `MauticFactory::getTheme()` / `getInstalledThemes()` removed — use `ThemeHelper` [code: UPGRADE-6.0.md:60-61 @7.x].
- 6.0: `GrapesJsData` install fixture moved into the plugin namespace [code: UPGRADE-6.0.md:82 @7.x].
- Docs still describe disabling GrapesJS as reverting to the legacy builder; that is not true from 6.0 [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#switching-back-to-the-legacy-builder].

## 7.x
- 7.0: MJML theme tokens (`mj-class` in `mj-attributes`, auto-applied to dropped components) [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#mjml-theme-tokens] [code: plugins/GrapesJsBuilderBundle/Assets/library/js/plugins/grapesjs-mjmlThemeTokens/index.js:7-44 @7.x].
- 7.x: GrapesJS editor state (project JSON) is stored in `content['grapesjsbuilder']` for Emails and Landing Pages [code: plugins/GrapesJsBuilderBundle/Model/GrapesJsBuilderModel.php:174-184 @7.x].
- 7.2: `tags` key in `config.json` and theme-picker labels [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html#configuration-file].
- 7.2: Typography block category for MJML emails [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#typography].
- 7.2: builder assets no longer committed; Parcel build with hashed names and `manifest.json`, run by composer install/update (non-fatal), DDEV, or `composer gjs-build` [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#building-the-builder-assets] [code: build/gjs_build.php:5-13 @7.x].
- 7.x after 7.2.1 (unreleased; [PR #17767]): Bootstrap upgraded to `twbs/bootstrap 5.3.8` (8.x branch still on `bootstrap-sass 3.4.1` until the forward merge) — custom admin CSS/JS targeting Bootstrap 3 markup may break [code: composer.json @7.x] [code: composer.json @8.x].
- 7.2.1: Twig sandbox for `@themes/` templates covering advisory GHSA-9fx4-7cmj-47vg [code: app/bundles/PageBundle/Tests/Functional/Controller/ThemeHelperSandboxTest.php:12-19 @7.x] [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:570-621 @7.x]. The version in which the sandbox first shipped is not established by the inputs [unverified].
- 7.x after 7.2.1 (unreleased; [PR #16870]): optional `html/email-validation.html.twig` and core `@MauticCore/Theme/email-validation.html.twig` for the "require email validation for unsubscribe" step; documented only in the 8.0 devdocs [code: app/bundles/EmailBundle/Controller/PublicController.php:154-200 @7.x] [devdocs: https://devdocs.mautic.org/en/8.0/themes/getting_started.html#html-email-validation-html-twig].
- 7.2.1: theme zip install hardened (zip-slip guard, single-folder prefix stripping) [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:356-359,481-555 @7.x]; exact minor of introduction [unverified].

## 8.x delta (8.x @ 11599729491; 7.2.1 work not yet forward-merged)
- Landing Pages with empty `customHtml` no longer fall back to rendering `@themes/<t>/html/page.html.twig` from `Page::getContent()`; the `public` template variable is gone; `PageBundle\Controller\PublicController::indexAction()` no longer takes `ThemeHelper` [PR #17078].
- `/s/grapesjsbuilder/assets` route and `FileManagerController::assetsAction` removed [PR #17070].
- `EmojiHelper` removed; emoji stored as UTF-8 — `GrapesJsController::builderAction`'s `EmojiHelper::toEmoji` call goes away with it [PR #17026].
- `TwigPass` and the `services` group in `Config/config.php` removed; helpers previously wired by `TwigPass` (such as `Mautic.getActiveBuilderName()` injection) move to service config [PR #17117] [PR #17470].
- Twig functions/filters registered via `#[AsTwigFunction]` / `#[AsTwigFilter]` [PR #17015] [PR #17042].
- `ThemeHelperInterface` and `BuilderEvent::getTokens()` get native `array` return types; `BuilderEvent::addTokensFromHelper()` / `getTokensFromHelper()` removed — custom token providers must use `addTokens()` [code: UPGRADE-8.0.md @8.x].
- Builder events dispatched by class name: subscribe to `EmailBuilderEvent::class` / `PageBuilderEvent::class` (`PAGE_ON_BUILD` → `PageBuilderEvent`, `PAGE_ON_DISPLAY` → final `PageDisplayEvent`) [PR #17097] [PR #17203].
- Not yet on 8.x but expected after the forward merge: `email-validation.html.twig` (present @7.x, absent @8.x), Bootstrap 5.3.8; both are unreleased 7.x work after 7.2.1 [PR #16870] [PR #17767] [code: app/bundles/EmailBundle/Controller/PublicController.php:168 @7.x] [code: composer.json @8.x].

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
