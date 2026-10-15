# Themes and builder — pull-request history

## Contents
1. [How to read this file](#1-how-to-read-this-file)
2. [Decisions that shaped current behaviour](#2-decisions-that-shaped-current-behaviour)
3. [Regression catalogue](#3-regression-catalogue)
4. [Feature timeline](#4-feature-timeline)
5. [Removed, deprecated, replaced](#5-removed-deprecated-replaced)
6. [Maintainer norms for this area](#6-maintainer-norms-for-this-area)
7. [Open questions](#7-open-questions)
8. [Coverage](#8-coverage)

## 1. How to read this file
Source: merged pull requests on github.com/mautic/mautic, harvested 2026-10-15. Versions are inferred from the base branch and merge date; where a release tag was checked against the 7.x tree the version is given without `~`. Current behaviour is in references/behaviour.md (code-verified); this file explains why and when it came about, and behaviour.md wins on any conflict.

## 2. Decisions that shaped current behaviour

### Theme package and config.json
- A theme declares the features it supports (`features`: email, page, form); a theme that does not declare a feature is not offered for it. Why: the Goldstar invoice theme is email-only and must not appear for Landing Pages. [PR #1906] (v2.0)
- Themes are Twig templates with a JSON `config.json`; `mautic:theme:json-config` once converted PHP configs. Why: start of the PHP-to-Twig migration; the command is historical. [PR #1412] (v1.3)
- `builder` in `config.json` must be an array (`["grapesjsbuilder"]` or `["legacy", "grapesjsbuilder"]`); a theme without `builder` is treated as `legacy`. Why: one theme (Blank) must serve several builders. Rejected: a separate `blank-grapejs` theme. Originally a string in [PR #9654] (v3.3); changed to an array by [PR #9893] (v4.0). On 7.x a non-array value throws "Theme %s not configured properly: builder property in the config.json" when the theme is checked for a feature [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:778-785 @7.x], while the theme list silently coerces it to `['legacy']` [code: app/bundles/CoreBundle/Helper/ThemeHelper.php:733-736 @7.x].
- Email and Landing Page theme pickers are filtered by the active builder; the theme manager (`/s/themes`) lists every installed theme with a builder badge. Why: the admin needs to see everything installed. [PR #9654] (v3.3) [PR #9893] (v4.0)
- When several builder plugins support a feature, only the first one found is used. [PR #9654] (v3.3)
- Theme template paths do not depend on the folder name, so a theme zip can be renamed and uploaded as a separate theme. Why: download, rename, customise, re-upload. [PR #2066] (v2.1)
- Page title, meta description and email subject reach the theme head through `{pagetitle}`, `{pagemetadescription}` and `{subject}` tokens. Why: the Mautic 1 head mechanism did not work with 2.0 themes, and the title must follow edits. [PR #2134] (v2.1); replaced the direct meta tag of [PR #704] (v1.2).
- Every theme ships `base.html.twig` and a form template, because unsubscribe pages and form preview fall back to them. [PR #2019] (v2.0.1) [PR #5415] (v2.12)
- Shared base and message templates live in core as `@MauticCore/Theme/base.html.twig` and `message.html.twig`, and placeholder images in `app/assets/images`. Originally a `themes/@defaults` folder [PR #14155] (v5.2); moved into core by [PR #14425] (v5.2.2). Why: Composer installs did not include `themes/@defaults`, which caused 500 errors on unsubscribe links, new emails, form previews and Landing Pages. Rejected: a copy in `app/assets/scaffold` and a separate `mautic/theme-defaults` package.
- Each core theme's `composer.json` requires the lowest `mautic/core-lib` that provides the core templates and Twig functions it uses: ≥5.2 for Blank and the 5.2 themes [PR #14302], ≥5.2.2 for themes that extend `@MauticCore/Theme/base.html.twig` [PR #14621], ^6.0 for `_color_helper.html.twig` users [PR #14649], ^7.0 for `getRoundedCorners` users [PR #14657]. Why: Composer then resolves the right theme tag for each core version.
- Each new major branch bumps the `mautic/core-lib` constraint of every core theme and plugin to that major. Why: `^5.0` excludes 6.x and breaks Composer installs. [PR #11593] (v5.0) [PR #14546] (v6.0) [PR #14748] (v7.0)
- Every shipped theme has a `composer.json` and is split to its own read-only repository `mautic/theme-<name>` with a Packagist package; PRs on the mirrors are auto-closed. Why: Composer decoupling, and later Marketplace management. [PR #9742] [PR #10083] (v4.0) [PR #11154] (v4.3) [PR #14292] [PR #14295] (v5.2)
- Core themes credit "Mautic Team" as author, even when a company donated them. Why: Product Team and Community Council decision. Rejected: crediting the donor in `config.json`. [PR #10271] (v4.0)
- `tags` in `config.json` label themes in the picker with one of 9 translated purpose values. Why: help users choose by purpose. [PR #15691] (v7.2.0)

### Theme manager and install
- Theme zip install extracts only whitelisted file types and drops everything else, notably PHP. Why: security. [PR #2066] (v2.1). The list is now the `theme_import_allowed_extensions` parameter without `tiff` [code: app/bundles/CoreBundle/Config/config.php:261 @7.x].
- A zip without `config.json` is rejected. [PR #2066] (v2.1)
- Core themes cannot be deleted or overwritten through the theme manager. Why: a customised core theme would be broken by later upgrades; copy and upload under a new name instead. [PR #2066] (v2.1)

### Core theme catalogue
- Core ships a curated range of best-practice MJML themes, including 13 neutral `_`-prefixed starter layouts that sort first. Why: users wanted usable starting templates. Rejected: fewer core themes and the Marketplace only (core themes cannot be deleted and return on update). [PR #14155] (v5.2)
- Blank, the default theme, is MJML. [PR #14255] (v5.2)
- The legacy "onlyForBC" slot themes (Mauve, coffee, nature) were removed as a 5.0 BC break. Why: deprecated for seven years. [PR #12524] (v5.0)
- Goldstar, Neopolitan, Oxygen and Skyline are no longer form themes; their form style templates were deleted and `form` removed from their config. Why: they added nothing over Blank. Removing the themes entirely was proposed and not done. [PR #14588] (v6.0)
- Shipped themes must not contain URL shorteners. Why: t-online rejected Skyline mail as spam. [PR #8582] (v2.16.2)
- Default email themes use `%` line-height, not `em`. Why: `em` crops text in Outlook for Windows. [PR #15780] (v7.1.0)
- Placeholder hrefs in themes and new buttons are `#`, not `https://`, because a bare `https://` is rejected on save. [PR #16778] [PR #16892] (v7.2.0)

### Global brand settings
- Configuration > Theme settings holds a primary brand colour, a company name and a rounded-corners value that new-style email, page and form themes apply when content is created; only full-access administrators can change them. Why: consistent branding, moving from "themes" towards "templates". [PR #14649] (v6.0) [PR #14657] (v7.0). The PR stated a "Mautic" company-name default; 7.x defaults are `brand_name: 'Your Brand (configurable)'`, `primary_brand_color: '000000'`, `rounded_corners: '0'` [code: app/bundles/CoreBundle/Config/config.php:262-264 @7.x].
- Text on the brand colour gets a contrasting colour chosen by luminance (`@MauticCore/Theme/_color_helper.html.twig`). [PR #14649] (v6.0)

### Form theming
- A form's theme also styles the embedded form through `themes/<t>/html/MauticFormBundle/Builder/style.html.twig`. Why: embeds cannot include the theme head without breaking the host page; iframes rejected. [PR #2427] (v2.2)
- Theme form-style overrides must stay in sync with core: the 50%-width column fix had to touch the core style template and every shipped theme's override. [PR #16281] (v7.2.0)
- Custom field widths become 100% on mobile, using `twig/string-extra` rather than a custom Twig extension. [PR #15425] (v7.2.0)

### GrapesJS packaging and build
- GrapesJS ships in core as `plugins/GrapesJsBuilderBundle` and is released with mautic/mautic. [PR #9966] [PR #10242] (v4.0)
- Shared builder logic lived in the `grapesjs-preset-mautic` npm package, with only wiring in the bundle; core picked up preset fixes by moving the branch reference and rebuilding. Originally [PR #10114] (v4.0); the preset source moved into `plugins/GrapesJsBuilderBundle/Assets/library/js/preset-mautic/` by [PR #16436] (v7.2.0). Why: Mautic was the only consumer and cross-repo PRs and branch pins drifted. Imported with `git subtree add`; not to be squashed.
- Compiled builder assets are no longer committed; Parcel builds content-hashed files plus `manifest.json`, `composer install`/`update` run a non-fatal build, and release packages include dist without `node_modules` or `.parcel-cache`. Originally committed dist [PR #10095] [PR #10360] (v4.0); changed by [PR #16435] (v7.2.0). Why: hashed filenames in git caused churn and conflicts, and users should not need to build assets [code: composer.json:157-182 @7.x].
- Asset lookups use `PathsHelper::getPluginsPath()` so separate-webroot installs find the manifest. [PR #17375] (v7.2.1) [code: plugins/GrapesJsBuilderBundle/EventSubscriber/AssetsSubscriber.php:46-48 @7.x]
- Third-party code extends the editor by pushing named plugin objects onto `window.MauticGrapesJsPlugins` before init. Why: loose coupling without forking. [PR #12429] (v5.1)
- GrapesJS core is bumped in patch and minor releases to pick up upstream fixes. [PR #13928] (v5.2) [PR #14454] (v5.2.2)

### GrapesJS editing: MJML
- Self-closing MJML tags (including `mj-spacer`) are converted to open/close pairs before parsing. Why: the grapesjs-mjml parser broke them; a stop-gap until upstream is fixed. [PR #13431] (v5.1) [PR #14142] (v5.2)
- The Raw block is not offered for MJML emails, because in the MJML preset it renders an image gallery. [PR #13363] (v5.2)
- MJML themes can declare tokens as `mj-class` definitions in `<mj-attributes>`, inherited by components on load and on drop; tokens are opt-in per theme. Why: a theme defines its visual defaults once. A tester objected that deep `mj-attributes` restructuring may not suit every theme developer. [PR #16042] (v7.2.0). Rolled out to all core email themes except Truly Personal by [PR #16778] (v7.2.0).
- Resolved `mj-class` attributes, `<mj-font>` stylesheets and non-inline `<mj-style>` CSS are applied in the canvas only and never leak into saved MJML; explicit component attributes win and merging is shorthand-aware. [PR #16403] (v7.2.0)
- `<mj-preview>` is stripped from head content injected into component templates while editing but kept in the saved document. Why: its hidden div crashed the builder. [PR #16106] (v7.2.0)
- Top-level comments in `mj-body` become invisible canvas markers so drops land at the right position; saved MJML is unchanged. Why: a narrowly scoped workaround for a GrapesJS 0.22.16 regression. [PR #16765] (v7.2.0)
- `<mj-style>` text is serialised verbatim while all other text nodes stay HTML-escaped. Why: escaped `>` broke saved CSS. [PR #17474] (7.2 branch after 7.2.1, unreleased; not on the 7.x snapshot)
- The source editor reparses MJML only in MJML mode; in HTML mode saving from "Edit code" keeps styling. [PR #15971] (v7.1.2)
- The email builder has a Typography block category (H1–H4, Subtitle, Text), and its blocks belong in the theme-token block patcher. [PR #15694] (v7.2.0)

### Rich-text editing (CKEditor in GrapesJS)
- CKEditor 5 replaced CKEditor 4 across Mautic, including GrapesJS; the "Powered by CKEditor" logo is accepted. Why: CKEditor 4 end of life. [PR #12641] (v5.0)
- All CKEditor init paths pass `licenseKey: 'GPL'`. Why: HTML email templates threw `license-key-missing`. [PR #16191] (v7.2.0)
- Buttons are edited with the GrapesJS RTE, not CKEditor. Why: CKEditor wraps content in `<p>`, which changed button padding. [PR #14258] (v5.2.1)
- The CKEditor modal background matches the element being edited, not the admin theme. Why: WYSIWYG should match the real rendering; matching the admin appearance setting was rejected. [PR #14258] (v5.2.1)
- A backdrop click does not close the text editor modal, and its close button reads "Cancel". Why: users lost unsaved text. [PR #14533] (v6.0)
- CKEditor edits text inline in the canvas. [PR #15839] (v7.1.0). Its hiding of the Typography style section and list/indent tools was reverted by [PR #16098] (v7.1.3), because legacy themes rely on them.
- On paste and save only MS Word properties are stripped and valid inline CSS is kept; style and class are reconciled so repeated edits do not drift. [PR #16058] (v7.1.3). Table editing broken by this change was restored by [PR #16476] (v7.1.3).
- Headings in the page builder are wrapped in `div.gjs-heading-wrapper` so CKEditor does not inject `<p>` into headings, and the code editor emits `mautic:code-editor-update` so the wrapper is re-detected. [PR #16362] (v7.2.0)
- Inline phrasing elements (`span`, `strong`) stay inside the MJML paragraph when CKEditor starts. [PR #16480] (v7.2.0)
- The CKEditor toolbars inside GrapesJS include the `TokenPlugin` "Insert Token" dropdown. Originally a CKEditor 4 plugin [PR #11525] (v5.0); a CKEditor 5 `TokenPlugin` now provides it [code: plugins/GrapesJsBuilderBundle/Assets/library/js/builder.service.js:892,1068 @7.x] [code: app/assets/libraries/ckeditor/src/TokenPlugin.js:10-43 @7.x].

### Builder UX and save flow
- The builder keeps up to 10 localStorage backups keyed by type, theme and ID, and offers a restore; the copy is cleared when a new entity is saved. Why: crash recovery within the ~10 MiB storage limit. Keying by user was proposed and not done. [PR #13610] (v5.1)
- No restore prompt appears when the backup equals what was just saved. [PR #16383] (v7.2.0)
- "Apply" saves a new email or page without leaving the builder and switches the URL to the edit route. [PR #13665] (v5.1)
- A failed Apply shows the validation modal plus a message that builder content is preserved in the form but not yet saved. Rejected: a JavaScript pre-check duplicating `EmailListsValidator`, because validation belongs in Symfony entity validation. [PR #17604] (7.2 branch after 7.2.1, unreleased; not on the 7.x snapshot)
- Code Mode content can be opened in the builder after a warning. Originally the builder button was blocked [PR #11102] (v4.2.2); changed by [PR #11339] (v5.0). Why: users want to tweak code and continue in the builder.
- Tags in the head with `data-source="mautic"` (builder JS/CSS) are stripped before save. Why: live pages loaded builder assets. [PR #10360] (v4.0)
- Saving a parent email must not overwrite translation children's content. [PR #10620] (v4.2.1)
- Email components with styles can be copied and pasted between emails through a localStorage clipboard. [PR #15124] (v7.0.0). Multi-section selection and paste in document order: [PR #17590] (unreleased 7.3, on 7.x after 7.2.1).
- Landing Page images have `href`, `target` and `rel` traits and are wrapped in `<a>` when `href` is set; the email builder keeps its own image linking. [PR #16267] (v7.2.0). The extended type must keep an `isComponent` detector [PR #16330]; bare domains get `https://` [PR #16369] (v7.2.0).

### Asset manager and API
- The asset list loads asynchronously from a dedicated endpoint, lazily and newest first. Why: >2 MB of asset JSON on unrelated admin pages, then slow large libraries. [PR #11818] (v5.0) [PR #14191] (v5.2)
- SVG uploads are listed with dimensions from width/height or viewBox. SVG sanitisation and a Landing-Page-only restriction were raised and not done. [PR #15954] (v7.2.0)
- The email API returns and accepts `grapesjsbuilder.customMjml`, through a JMS serializer subscriber in GrapesJsBuilderBundle. Rejected: reusing the legacy `Email` builder property, a separate REST endpoint, an API save subscriber. [PR #13775] (v5.2)
- Custom fonts from `editor_fonts` appear in the Style Manager, and only used fonts are written to the saved head. [PR #12067] (v5.0)

### Legacy builder (historical)
- The Froala/slot builder decisions (drag-and-drop slots, clone button, Mailchimp column stacking, editor-safe inline styles) no longer apply: the legacy builder was removed in 6.0. [PR #1921] [PR #1941] [PR #3587] [PR #5635] [PR #2474]

## 3. Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **Themes and config** | | | |
| Theme with `"builder": "grapesjsbuilder"` string | Array required; string throws `BadConfigurationException` | [PR #9893] | v4.0 |
| Form preview with an email theme errors | Every theme provides the templates fallbacks need | [PR #2019] | v2.0.1 |
| Unsubscribe page errors for themes without `base.html.twig` | Page renders | [PR #5415] | v2.12 |
| 500s on unsubscribe, new email, form preview, Landing Pages on Composer installs | Base/message templates load from `@MauticCore/Theme/*` | [PR #14425] | v5.2.2 |
| Capture theme on 5.2.0/5.2.1: "Unable to find template" | Theme requires core-lib ≥5.2.2 | [PR #14621] | v6.0 |
| Page title stale in preview | Head tokens render current values | [PR #2134] | v2.1 |
| Text cropped in Outlook for Windows | `%` line-height in default themes | [PR #15780] | v7.1.0 |
| Shipped theme mail rejected as spam | No URL shorteners | [PR #8582] | v2.16.2 |
| Blank font sizes ignored in Gmail | No `font-size:0` on tables | [PR #9269] | v3.1.2 |
| Paprika text hidden in builder vs preview | Builder and preview identical | [PR #13619] | v5.1 |
| New Paprika text black; new button `https://` href fails to save | Text inherits theme colour; href `#` | [PR #16892] | v7.2.0 |
| **Forms** | | | |
| Embedded form ignores the form theme | Theme style template applied to embed | [PR #2427] | v2.2 |
| 50%-width fields collapse after validation error or page break | Column layout persists | [PR #16281] | v7.2.0 |
| Set-width fields form 4 columns on phones | Fields 100% wide on mobile | [PR #15425] | v7.2.0 |
| **Builder loading and build** | | | |
| "Please enable the GrapesJS builder plugin" on docroot installs | Manifest found through `getPluginsPath()` | [PR #17375] | v7.2.1 |
| `license-key-missing` with HTML email templates | All paths pass `licenseKey: 'GPL'` | [PR #16191] | v7.2.0 |
| Empty canvas / TypeError when theme has `<mj-preview>` | Builder loads; preview text kept | [PR #16106] | v7.2.0 |
| ReferenceError for Paprika (no `<mj-head>`) | Builder loads | [PR #16334] | v7.2.0 |
| `h.getAssetsConfig is not a function` on save | Save works; AssetService injected | [PR #14308] | v5.2 |
| **MJML editing** | | | |
| `<mj-image />` broke output | Self-closing tags converted | [PR #13431] | v5.1 |
| `<mj-spacer/>` broke rendering | Spacer renders | [PR #14142] | v5.2 |
| `<mj-style>` CSS saved as `&gt;` | Verbatim serialisation | [PR #17474] | 7.2 branch, unreleased |
| Drops misplaced in themes with comments in `mj-body` | Sections insert at drop point | [PR #16765] | v7.2.0 |
| DC block missing in MJML emails | DC block available | [PR #11319] | v4.4.1 |
| **Rich text** | | | |
| Button padding changed after editing text | GrapesJS RTE for buttons | [PR #14258] | v5.2.1 |
| Inline styles stripped; styles duplicated across edits | Only MS Word styles stripped | [PR #16058] | v7.1.3 |
| CKEditor table editing broken | Tables work as in 7.1.2 | [PR #16476] | v7.1.3 |
| Heading wrapped in `<p>` after code-editor Update | Wrapper re-detected; no `<p>` | [PR #16362] | v7.2.0 |
| Inline `span` split out of MJML `<p>` | Phrasing stays in paragraph | [PR #16480] | v7.2.0 |
| Typography and list/indent tools missing | Tools available | [PR #16098] | v7.1.3 |
| Backdrop click discarded text edits | Modal stays open | [PR #14533] | v6.0 |
| Several CKEditor fields per DC variant | One editor per variant | [PR #14925] | v5.2.7 |
| **Save flow and UX** | | | |
| Apply errored and did not save a new email | Apply saves and switches to edit URL | [PR #13665] | v5.1 |
| Restore prompt right after a clean save | No prompt | [PR #16383] | v7.2.0 |
| Users unsure if content survived failed Apply | Modal says preserved but unsaved | [PR #17604] | 7.2 branch, unreleased |
| Landing Page "Edit code" save removed styling | HTML mode not reparsed as MJML | [PR #15971] | v7.1.2 |
| Live pages loaded builder JS/CSS | `data-source="mautic"` head tags stripped | [PR #10360] | v4.0 |
| Parent save overwrote translations | Translations keep content | [PR #10620] | v4.2.1 |
| Publish toggle / API email edit fails with GrapesJS | Model tolerates missing builder data | [PR #10023] [PR #10259] | v4.0 |
| Custom HTML field hidden in Code Mode on create | Field visible on Advanced tab | [PR #14638] | v5.2.4 |
| "Edit code" modal won't reopen or save | Modal reopens and saves | [PR #10842] [PR #11376] | v4.2 / v4.4.2 |
| Source syntax popup blocks saving | Save allowed | [PR #10482] | v4.0.1 |
| Long email jumps on Enter | No scroll jump | [PR #11491] | v5.0 |
| **Assets and API** | | | |
| Admin pages slow (>2 MB asset JSON) | Assets fetched on builder init | [PR #11818] | v5.0 |
| Uploaded SVGs not listed, undeletable | SVGs listed with dimensions | [PR #15954] | v7.2.0 |
| Images in loaded themes lack link traits | All `<img>` get href/target/rel | [PR #16330] | v7.2.0 |
| Bare-domain image link became relative | `https://` prepended | [PR #16369] | v7.2.0 |
| API email copy lost MJML | `customMjml` returned and accepted | [PR #13775] | v5.2 |
| Plugin settings 500 in 5.x | Settings open | [PR #11896] | v5.0 |

## 4. Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.x–2.x | Twig themes and `config.json`; Goldstar; theme manager; head tokens; form embed styles; 8 themes (aurora, cards, sparse, vibrant, fresh-*); form noindex | [PR #1412] [PR #1906] [PR #2066] [PR #2134] [PR #2427] [PR #5311] [PR #6161] |
| 3.x | Responsive Blank; builder-specific themes; first MJML themes | [PR #6481] [PR #9654] [PR #9681] [PR #9682] [PR #9683] |
| 4.0 | Multi-builder `builder` array; GrapesJS in core; preset library; DC in HTML emails | [PR #9893] [PR #9966] [PR #10114] |
| 4.2 | DC in MJML emails; Code Mode textarea | [PR #10782] [PR #11102] |
| 5.0 | Builder from Code Mode with warning; token dropdown; async asset manager; `editor_fonts`; CKEditor 5 | [PR #11339] [PR #11525] [PR #11818] [PR #12067] [PR #12641] |
| 5.1 | `window.MauticGrapesJsPlugins`; GrapesJS + Parcel 2; local autosave; Apply saves new entities | [PR #12429] [PR #13283] [PR #13610] [PR #13665] |
| 5.2 | `customMjml` in API; 13 starter themes; lazy asset manager; Attract, Creative; Blank as MJML; theme repo split | [PR #13775] [PR #14155] [PR #14191] [PR #14200] [PR #14201] [PR #14255] [PR #14292] |
| 5.2.1 | Custom CKEditor initializer; GrapesJS RTE for buttons | [PR #14258] |
| 5.2.2 | Shared templates moved to `@MauticCore/Theme` | [PR #14425] |
| 6.0 | Landing Page themes ReachOut, Formscape, Blend, Mono, Capture; form themes Chord, Eclipse; brand colour and company name | [PR #14519] [PR #14527] [PR #14534] [PR #14536] [PR #14545] [PR #14547] [PR #14591] [PR #14649] |
| 7.0.0 | Rounded corners; Eclipse submit animation; Multi-step form theme; email component copy/paste | [PR #14657] [PR #14654] [PR #14795] [PR #15124] |
| 7.1.0 | Inline CKEditor in canvas; `%` line-height | [PR #15839] [PR #15780] |
| 7.1.3 | Typography/list tools back; MS-Word-only style stripping; table fix | [PR #16098] [PR #16058] [PR #16476] |
| 7.2.0 | MJML theme tokens and core-theme rollout; canvas `mj-class`/`mj-font`/`mj-style`; Typography blocks; theme `tags`; SVG listing; Landing Page image links; in-repo preset; build-time assets | [PR #16042] [PR #16778] [PR #16403] [PR #15694] [PR #15691] [PR #15954] [PR #16267] [PR #16436] [PR #16435] |
| 7.2.1 | Plugins-path asset lookup | [PR #17375] |
| 7.2 branch (unreleased) | `<mj-style>` verbatim; failed-Apply message | [PR #17474] [PR #17604] |
| 7.x after 7.2.1 (unreleased 7.3) | Multi-section copy/paste | [PR #17590] |

## 5. Removed, deprecated, replaced

| What | Replaced by | PR | Version | Note |
|---|---|---|---|---|
| PHP theme templates/config | Twig + `config.json` | [PR #1412] | v1.3 | historical |
| `"builder": "<string>"` | Array | [PR #9893] | v4.0 | string throws |
| `blank-grapejs` theme | Multi-builder `blank` | [PR #9893] | v4.0 | — |
| Mauve, coffee, nature | Current themes | [PR #12524] | v5.0 | UPGRADE-5.0.md |
| CKEditor 4 | CKEditor 5 | [PR #12641] | v5.0 | rebuild assets |
| GrapesJS assets inline in admin pages | Async endpoint | [PR #11818] | v5.0 | — |
| `FileManager::getImages()`, `FileManagerController::assetsAction`, `GET /grapesjsbuilder/assets` | Paginated `/grapesjsbuilder/media` | [PR #14191] | deprecated 5.2 | annotated "to be removed in 6.0" but still in 7.x [code: plugins/GrapesJsBuilderBundle/Helper/FileManager.php:96-98 @7.x] [code: plugins/GrapesJsBuilderBundle/Controller/FileManagerController.php:46-48 @7.x] [code: plugins/GrapesJsBuilderBundle/Config/config.php:20-24 @7.x] |
| Raw block in MJML sidebar | Nothing | [PR #13363] | v5.2 | — |
| `grapesjs-plugin-ckeditor5` | Custom initializer, later `plugins/grapesjs-ckeditor/*` | [PR #14258] [PR #15839] | v5.2.1 / v7.1.0 | — |
| `themes/@defaults` | `@MauticCore/Theme/*` | [PR #14425] | v5.2.2 | custom themes must switch |
| Form role of Goldstar, Neopolitan, Oxygen, Skyline | Blank, Chord, Eclipse | [PR #14588] | v6.0 | themes kept for email/page |
| `line-height: 1.4em` | `140%` | [PR #15780] | v7.1.0 | do the same in custom themes |
| `grapesjs-preset-mautic` npm repo | In-repo `preset-mautic/` | [PR #16436] | v7.2.0 | contribute to mautic/mautic |
| Committed `dist/builder.js`/`.css` | Hashed build + `manifest.json` | [PR #16435] | v7.2.0 | do not hard-code dist filenames |

## 6. Maintainer norms for this area
- Builder UI fixes once belonged in `grapesjs-preset-mautic` with a branch bump in core; since 7.2.0 they go straight into mautic/mautic. [PR #13665] [PR #14925] [PR #16436]
- Until 7.2.0, PRs committed rebuilt dist and rebuilt after rebasing; since then dist must not appear in PRs. [PR #10728] [PR #13610] [PR #16435] [PR #16480]
- A theme that starts using a core template or Twig function must raise its `mautic/core-lib` constraint; this counts as a BC break for the theme. [PR #14302] [PR #14621] [PR #14649] [PR #14657]
- A new core theme needs a `mautic/theme-<name>` repo, Packagist package, git-split config, `close_pull_requests.yml`, README and the right minimum core version before merge. [PR #14295] [PR #14519] [PR #14547]
- Removing themes is a BC break for a major release and must be listed in UPGRADE-x.md. [PR #12524]
- Canvas-only GrapesJS workarounds stay isolated in their own file and must not change saved MJML; narrowly scoped workarounds for upstream regressions are acceptable. [PR #16403] [PR #16765]
- Validation belongs in Symfony entity validation, not duplicated in builder JavaScript. [PR #17604]
- Large builder JS plugins are split into `Assets/library/js/plugins/<name>/`. [PR #15839]
- UX policy for builder modals: "Save" saves and closes, static pages use "Apply", and a backdrop click must not discard work. [PR #14533]
- Email rendering fixes are checked against caniemail and real clients (EmailOnAcid, Litmus). [PR #15780] [PR #14155]
- New PHP endpoints and behaviour need functional tests; builder flows are covered by Codeception acceptance tests because there is no JS test runner. [PR #11818] [PR #13775] [PR #15954] [PR #17474] [PR #17604]
- Patch fixes target the patch branch (`7.1`, `7.2`), features `7.x`. [PR #16476] [PR #17375] [PR #17474] [PR #14657]

## 7. Open questions
- Resolved: MJML theme tokens first ship in tag 7.2.0 (the plugin is absent at 7.0.0 and 7.1.0); the devdocs placement under 7.0 is a documentation discrepancy [PR #16042] [code: plugins/GrapesJsBuilderBundle/Assets/library/js/plugins/grapesjs-mjmlThemeTokens/index.js:7-44 @7.x].
- `FileManager::getImages()` says to use `getMediaFiles`, while the PR notes name `getImagePages`; the 7.x method is `getMediaFiles` [code: plugins/GrapesJsBuilderBundle/Helper/FileManager.php:96,143 @7.x]. Removal is due on 8.x only for the route and `assetsAction` [PR #17070] [PR #14191].
- Token insertion: [PR #11525] said typing `{` did not open suggestions (CKEditor 4 era); behaviour.md B56 says `{` triggers the CKEditor mention feed today. Behaviour.md wins; the PR statement is historical. [PR #11525]
- [PR #12641] reviewers reported GrapesJS issues (bold plus colour, link editing); which were fixed is unclear. [PR #12641]
- Tables: [PR #16476] (v7.1.3) restored table editing broken by [PR #16058]; issue #16081 (table/img) was reported open at the time of [PR #16058] and its status is unknown.
- Autosave backups are not scoped by user, so a shared browser may offer another user's draft. [PR #13610]
- SVG uploads have no sanitisation discussed in the PRs. [PR #15954]
- `<head>` duplication in the HTML-mode code editor was reported still open. [PR #15971]
- Map block is full width in the editor and fixed width when saved. [PR #13283]
- Typography blocks use token styling; how they render in themes without tokens is not discussed. [PR #15694]
- Image-link normalisation is in the page-builder plugin; whether email image links are normalised is unverified. [PR #16369]
- Multi-step form: Enter on page 1 submits the whole form. [PR #14795]
- `{dynamiccontent=...}` duplication after save was reported in 4.2 with no fix found. [PR #10782]
- Docker images built without compiled assets show "enable the plugin" after 7.2.1; tracked in mautic/docker-mautic. [PR #17375]
- Editing an entity whose theme is not available for the active builder may show the wrong theme in the picker. [PR #9654]
- test-patterns.md says no Codeception coverage exists for the builder, but `tests/acceptance/GrapesJsBuilderPageCest.php` is on the 7.x snapshot and [PR #17604] adds `GrapesJsBuilderEmailCest.php` on the 7.2 branch. [PR #17604]

## 8. Coverage
- 169 PRs in 3 chunks (84, 60, 25); 147 substantive after excluding 20 noise PRs, the 7.1→7.x branch merge [PR #16327] (used for norms only) and the misfiled search fix [PR #9679]. [PR #16327] [PR #9679]
- 869 noise PRs were excluded upstream before chunking. [unverified: upstream filter count from the harvest brief]
