# Themes and builder — version notes

## History before 5.x (context only)
- GrapesJS arrived in Mautic 3 (opt-in from 3.3-RC1) and became the default in Mautic 4; the `builder` key changed from a string to an array between 3.3 and 4 [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#enabling-the-builder] [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#templates].
- `PageBundle\Controller\PublicController` still carries comments that the `content`-based (v1) rendering was "BC support to be removed in 3.0" and `'public' => true` "Remove in 2.0" [code: app/bundles/PageBundle/Controller/PublicController.php:252-254,374 @7.x].

## 5.x
- 5.0: `html/email.mjml.twig` deprecated; put MJML directly in `email.html.twig` [code: plugins/GrapesJsBuilderBundle/Controller/GrapesJsController.php:157-161,229-239 @7.x].
- 5.0: bundled themes `coffee`, `Mauve`, `nature` removed [code: UPGRADE-5.0.md:101 @7.x].
- 5.1: third-party GrapesJS plugins via `window.MauticGrapesJsPlugins` [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#grapesjs-builder-plugins].
- 5.2: paginated `/s/grapesjsbuilder/media` replaces `/s/grapesjsbuilder/assets` (deprecated, still routed in 7.2) [code: plugins/GrapesJsBuilderBundle/Config/config.php:21-24 @7.x].
- 5.0: CKEditor 5 replaces CKEditor 4 app-wide, including GrapesJS text editing [PR #12641].
- 5.0: the builder opens Code Mode content after a warning instead of blocking it (4.2.2 blocked it) [PR #11339] [PR #11102].
- 5.0: GrapesJS asset list loaded asynchronously on builder init; `editor_fonts` added to the Style Manager [PR #11818] [PR #12067].
- 5.1: GrapesJS upgrade with Parcel 2; local autosave with restore prompt; Apply saves new emails and pages [PR #13283] [PR #13610] [PR #13665].
- 5.1: self-closing MJML tags converted to open/close pairs before parsing (`mj-spacer` added in 5.2) [PR #13431] [PR #14142].
- 5.2: Blank becomes MJML; 13 `_`-prefixed starter themes plus Attract and Creative; core themes split into `mautic/theme-<name>` packages [PR #14255] [PR #14155] [PR #14200] [PR #14201] [PR #14292].
- 5.2: `grapesjsbuilder.customMjml` returned and accepted by the email API; Raw block removed from the MJML sidebar [PR #13775] [PR #13363].
- 5.2.1: buttons edited with the GrapesJS RTE, not CKEditor; CKEditor modal background matches the edited element [PR #14258].
- 5.2.2: `themes/@defaults` replaced by core `@MauticCore/Theme/base.html.twig` and `message.html.twig`; custom themes extending @defaults must switch and require core-lib ≥5.2.2 [PR #14425] [PR #14621].

## 6.x
- 6.0: legacy (Froala/slot) builder removed; `Mautic.launchBuilder` in core became an alert stub [code: UPGRADE-6.0.md:4-15 @7.x] [code: app/bundles/CoreBundle/Assets/js/4.builder.js:1-3 @7.x].
- 6.0: `MauticFactory::getTheme()` / `getInstalledThemes()` removed — use `ThemeHelper` [code: UPGRADE-6.0.md:60-61 @7.x].
- 6.0: `GrapesJsData` install fixture moved into the plugin namespace [code: UPGRADE-6.0.md:82 @7.x].
- 6.0: primary brand colour and company name in Theme settings, applied by new-style themes with automatic contrast [PR #14649]. The 7.x defaults are `brand_name: 'Your Brand (configurable)'` and `primary_brand_color: '000000'` [code: app/bundles/CoreBundle/Config/config.php:262-263 @7.x].
- 6.0: Landing Page themes ReachOut, Formscape, Blend, Mono, Capture and form themes Chord, Eclipse added [PR #14519] [PR #14527] [PR #14534] [PR #14536] [PR #14545] [PR #14547] [PR #14591].
- 6.0: Goldstar, Neopolitan, Oxygen, Skyline no longer offered as form themes [PR #14588].
- 6.0: clicking outside the text editor modal no longer closes it; the close button reads "Cancel" [PR #14533].
- 6.0: core themes and plugins require `mautic/core-lib ^6.0` [PR #14546].
- Docs still describe disabling GrapesJS as reverting to the legacy builder; that is not true from 6.0 [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#switching-back-to-the-legacy-builder].

## 7.x
- 7.2.0: MJML theme tokens (`mj-class` in `mj-attributes`, auto-applied to dropped components) [PR #16042] [code: plugins/GrapesJsBuilderBundle/Assets/library/js/plugins/grapesjs-mjmlThemeTokens/index.js:7-44 @7.x]. The plugin is absent at tags 7.0.0 and 7.1.0 and present at 7.2.0. Discrepancy: devdocs list this under 7.0 [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#mjml-theme-tokens].
- 7.0.0: rounded-corners setting (`getRoundedCorners`), Multi-step form theme, Eclipse submit animation, email component copy/paste [PR #14657] [PR #14795] [PR #14654] [PR #15124].
- 7.1.0: inline CKEditor in the canvas; `%` line-height in default email themes [PR #15839] [PR #15780]. 7.1.2: HTML-mode "Edit code" no longer reparses as MJML [PR #15971].
- 7.1.3: Typography section and list/indent tools restored; CKEditor strips only MS Word styles; table editing restored [PR #16098] [PR #16058] [PR #16476].
- 7.2.0: theme tokens rolled out to core email themes, canvas resolves `mj-class`/`mj-font`/`mj-style`, preset moved in-repo, Landing Page image links, SVG media listing [PR #16778] [PR #16403] [PR #16436] [PR #16267] [PR #15954].
- 7.2.1: builder asset lookup uses the plugins path, fixing separate-webroot installs [PR #17375].
- 7.2.2 (2026-10-26): `<mj-style>` serialised verbatim; failed-Apply message says content is preserved but unsaved [PR #17474] [PR #17604].
- 7.2.2: theme sandbox hardened for security advisory GHSA-h7pm-79gc-8867. Methods and properties are reachable only on `Mautic\`/`MauticPlugin\` objects, methods only as `get*`/`is*`/`has*` accessors minus a sensitive deny-list (plus six form-template methods); the `less_compile` filter is denied; Mautic's own `map`/`filter`/`reduce` deny-list was dropped because Twig's sandbox accepts only arrow-function callbacks. Custom themes calling setters, `__toString` or methods on `DateTime` and other non-Mautic objects stop rendering. The advisory fix arrived with the 7.2.2 release PR, the filter change separately [PR #17934] [PR #17620] [code: app/bundles/CoreBundle/Twig/Sandbox/ThemeSandboxPolicy.php:24-217 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html#template-sandbox-restrictions].
- Fixed on the 7.2 branch after 7.2.2 (milestone 7.2.3, not on the 7.x snapshot): inline MJML content, editor fonts, `<html>` attributes and dynamic content kept on Apply/save [PR #17794]; GrapesJS editor-only attributes (`draggable`, `data-gjs-*`, generated ids, `gjs-*` classes) stripped from CKEditor-edited text [PR #18016]; readable tooltip on the disabled Apply button of a segment email without a segment [PR #18014].
- Unreleased on 7.x (7.3.0-rc): multi-section copy/paste in MJML emails [PR #17590].
- Unreleased on 7.x (7.3.0-rc): favourite themes in the Email and Landing Page picker, per user and type [PR #18138]; Apply refreshes the form's CSRF token [PR #15403]; `message.html.twig` picks its layout from `message_type`, styles moved to `_message_styles.html.twig` [PR #15680].
- 7.x: GrapesJS editor state (project JSON) is stored in `content['grapesjsbuilder']` for Emails and Landing Pages [code: plugins/GrapesJsBuilderBundle/Model/GrapesJsBuilderModel.php:174-184 @7.x].
- 7.2: `tags` key in `config.json` and theme-picker labels [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html#configuration-file].
- 7.2: Typography block category for MJML emails [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#typography].
- 7.2: builder assets no longer committed; Parcel build with hashed names and `manifest.json`, run by composer install/update (non-fatal), DDEV, or `composer gjs-build` [devdocs: https://devdocs.mautic.org/en/7.2/themes/grapesjs.html#building-the-builder-assets] [code: build/gjs_build.php:5-13 @7.x].
- Unreleased on 7.x (7.3.0-rc; [PR #17767]): the admin UI moves from `twbs/bootstrap-sass 3.4.1` (still the dependency in 7.2.2) to `twbs/bootstrap 5.3.8` [code: app/composer.json:113 @7.x]. `_bootstrap.scss` builds Bootstrap 5 and then imports `_bootstrap-3-compatibility.scss`, which keeps Bootstrap 3 class names working (for example `col-xs-*` and `col-*-offset-*` grid classes, `panel`, `input-group-btn`, `input-group-addon`, `help-block`, `pull-right`, `visible-*`) [code: app/bundles/CoreBundle/Assets/css/libraries/bootstrap/_bootstrap.scss:1-81 @7.x]. Core templates and JS are being migrated to Bootstrap 5 markup and `data-bs-*` attributes [PR #17826] [PR #17827] [PR #17829] [PR #17830]; spacing classes now use one pixel scale (`$spacers` 0-5, 8, 12, 16, 24, 32, … 160), so `me-1` is 1px, and `ml`/`mr`/`pl`/`pr` become `ms`/`me`/`ps`/`pe`, while the old `xs`/`sm`/`md`/`lg` aliases stay defined [PR #18060]. A JavaScript layer keeps Bootstrap 3 usage working too: it mirrors `data-toggle`/`data-target`-style attributes to `data-bs-*`, and gives jQuery `.modal()`, `.collapse()`, `.tab()`, `.tooltip()`, `.popover()` calls (including `fixTitle` and `destroy`), `.button()` and the removed `affix` and transition helpers a Bootstrap 3 facade [code: app/bundles/CoreBundle/Assets/js/1.bootstrap-compatibility.js:1-64,232-330,623-660,810-835 @7.x]. Custom admin CSS/JS that relies on exact Bootstrap 3 spacing or markup the layers do not cover may still look or behave differently [unverified: coverage of the compatibility layers]; public theme templates are not affected, because `@MauticCore/Theme/base.html.twig` loads no admin CSS [code: app/bundles/CoreBundle/Resources/views/Theme/base.html.twig:1-17 @7.x]. The 8.x snapshot picked this up in the 7.x-to-8.x merge of 2026-11-16 [PR #18236] [code: app/composer.json:114 @8.x].
- 7.2.1: Twig sandbox for `@themes/` templates covering advisory GHSA-9fx4-7cmj-47vg (hardened in 7.2.2, see above) [code: app/bundles/PageBundle/Tests/Functional/Controller/ThemeHelperSandboxTest.php:14-21 @7.x] [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:570-621 @7.x]. The version in which the sandbox first shipped is not established by the inputs [unverified].
- Unreleased on 7.x (7.3.0-rc; [PR #16870]): optional `html/email-validation.html.twig` and core `@MauticCore/Theme/email-validation.html.twig` for the "require email validation for unsubscribe" step. After the 7.2.2 sandbox change the controller passes `emailAddressField`, `emailAddressValid`, `emailAddressHasErrors` and `submitField` instead of letting the template read `FormView` properties [PR #17953] [code: app/bundles/EmailBundle/Controller/PublicController.php:159-223 @7.x]. Documented in the 7.3 and 8.0 devdocs, not 7.2 [devdocs: https://devdocs.mautic.org/en/8.0/themes/getting_started.html#html-email-validation-html-twig] [docs: github.com/mautic/developer-documentation-new/blob/7.3/docs/themes/getting_started.rst].
- 7.2.1: theme zip install hardened (zip-slip guard, single-folder prefix stripping) [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:356-359,481-555 @7.x]; exact minor of introduction [unverified].

## 8.x delta (8.x @ 11599729491; 7.2.1 work not yet forward-merged)
- Landing Pages with empty `customHtml` no longer fall back to rendering `@themes/<t>/html/page.html.twig` from `Page::getContent()`; the `public` template variable is gone; `PageBundle\Controller\PublicController::indexAction()` no longer takes `ThemeHelper` [PR #17078].
- `/s/grapesjsbuilder/assets` route and `FileManagerController::assetsAction` removed [PR #17070].
- `EmojiHelper` removed; emoji stored as UTF-8 — `GrapesJsController::builderAction`'s `EmojiHelper::toEmoji` call goes away with it [PR #17026].
- `TwigPass` and the `services` group in `Config/config.php` removed; helpers previously wired by `TwigPass` (such as `Mautic.getActiveBuilderName()` injection) move to service config [PR #17117] [PR #17470].
- Twig functions/filters registered via `#[AsTwigFunction]` / `#[AsTwigFilter]` [PR #17015] [PR #17042].
- `ThemeHelperInterface` and `BuilderEvent::getTokens()` get native `array` return types; `BuilderEvent::addTokensFromHelper()` / `getTokensFromHelper()` removed — custom token providers must use `addTokens()` [code: UPGRADE-8.0.md @8.x].
- Builder events dispatched by class name: subscribe to `EmailBuilderEvent::class` / `PageBuilderEvent::class` (`PAGE_ON_BUILD` → `PageBuilderEvent`, `PAGE_ON_DISPLAY` → final `PageDisplayEvent`) [PR #17097] [PR #17203].
- Not yet on 8.x but expected after the forward merge: `email-validation.html.twig` (present @7.x, absent @8.x), Bootstrap 5.3.8; both are unreleased 7.x work after 7.2.1 [PR #16870] [PR #17767] [code: app/bundles/EmailBundle/Controller/PublicController.php:179 @7.x] [code: composer.json @8.x].

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [unreleased-7.x-prs.md](../../mautic-upgrades-and-versions/references/unreleased-7.x-prs.md).
