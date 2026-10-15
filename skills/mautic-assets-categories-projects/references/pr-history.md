# Assets, Categories and Projects - pull-request history

## Contents
- [How to read this file](#how-to-read-this-file)
- [Decisions that shaped current behaviour](#decisions-that-shaped-current-behaviour)
- [Regression catalogue](#regression-catalogue)
- [Feature timeline](#feature-timeline)
- [Removed, deprecated, replaced](#removed-deprecated-replaced)
- [Maintainer norms for this area](#maintainer-norms-for-this-area)
- [Open questions](#open-questions)
- [Coverage](#coverage)

## How to read this file
Source: merged pull requests on github.com/mautic/mautic for AssetBundle, CategoryBundle, ProjectBundle and MauticCloudStorageBundle, harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; `~` marks an inference. 7.x versions were checked against the release tags; "unreleased 7.x" means merged to `7.x` after 7.2.1 (milestone 7.3.0-rc).
Current behaviour lives in behaviour.md (code-verified); this file explains why and when it came to be.

## Decisions that shaped current behaviour

### Assets: upload, size limits and validation
- Local uploads go through Dropzone (AJAX) and OneupUploaderBundle, with an admin-editable extension allow-list in Configuration > Asset Settings [PR #130] (~v1.0). The browser checks size and extension before sending [PR #133] (~v1.0).
- Editing an Asset without replacing its file must work; size checks run only when a file is present [PR #116] (~v1.0).
- The effective upload limit is the lowest of `max_size` and the PHP limits, so Dropzone refuses an oversized file before transfer [PR #586] (~v1.1.3). PHP limits of `-1` or `0` count as unlimited, because they had blocked every upload [PR #1024] (~v1.2.1). Behaviour A2.11 shows 7.x also includes `memory_limit` in the minimum.
- One helper converts php.ini size strings: `FileHelper::convertPHPSizeToBytes()`. Three diverging copies existed; `Asset::convertSizeToBytes()` was removed [PR #8392] (v3.0.0).
- Upload validation reads the configured `allowed_extensions`, not a hardcoded list; adding `mp4` in the UI had no effect before the fix [PR #15111] (v5.2.7).
- Remote URL and original file name are stored as TEXT so URLs over 191 characters no longer cause a 500. The reviewer required the entity mapping to change with the migration, and the PR moved to the feature branch because it had a migration [PR #9542] (v4.0.0).
- A remote Asset created through the API gets its MIME type and extension filled in [PR #9120] (~v3.2.0).
- Asset language is required; an empty language had caused a 500 [PR #10406] (v4.0.1).
- Remote Assets are validated like local ones since 7.2. Mautic fetches the URL (with a User-Agent, because CDNs returned 403), resolves the MIME type from `Content-Type` or magic bytes, and rejects non-2xx, unresolvable or disallowed types [PR #16045] (v7.2.0).
- For local uploads the detected MIME type must match the extension, so a PHP file renamed to `.png` is rejected [PR #16045] (v7.2.0).
- Validation is one entity-level `Upload` constraint using Symfony `MimeTypes`. The duplicate form-level extension check and the `allowed_mimetypes` parameter were removed [PR #16045] (v7.2.0).
- Remote URLs can be restricted by domain: with `validate_remote_domains => true` in `config/local.php` (default false), only the instance domain and `allowed_remote_domains` pass. It applies to UI and API through `SafeRemoteUrl` [PR #15868] (v7.1.0).
- Browsing remote files with an unconfigured S3 integration shows a readable credentials error instead of a PHP error [PR #14865] (~v7.0).
- The upload size check was off by a factor of 1000. The fix changes signatures (for example `getDisallow(): ?bool`), so it targets 8.x [PR #17080] (8.0 dev).

### Assets: public download URL
- Remote Assets are tracked and then redirected (302) to the remote URL, never proxied through PHP, because streaming large files hit `memory_limit` [PR #944] (~v1.2.1).
- Bare `/asset/{id}` returns 404, which stops guessing Assets by numeric id [PR #15138] (v7.1.0). New URLs use an unguessable UUID: `Asset::getSlug()` returns the `uuid`, so the canonical URL is `/asset/{uuid}` [PR #15776] (v7.1.0).
- Legacy `/asset/{id}:{alias}` links keep working because old links sit in sent emails. The alias text is not compared, and the lookup succeeds only when the Asset's alias is not NULL [PR #15138] [PR #15776] (v7.1.0). Behaviour A3.20 records the 7.x rule.
- UUID links were first rejected in #15138 because recipients might find them "malicious". They were adopted in #15776 because `id:alias` links break when the alias is renamed [PR #15138] [PR #15776].
- Rejected for #15776: a "Secret Asset Download" config switch (maintainers preferred a safe default that needs no action), and a NULL alias (the schema allows only an empty string) [PR #15776].
- The planned removal of the lenient `{id}:` and wrong-alias forms will make them 404; until then they still allow enumeration of Assets that have an alias [PR #15776].
- `getSlug()` throws `LogicException` for an unsaved Asset, so callers must guard deleted or unsaved Assets [PR #15776]. Two regressions followed: API DELETE returned 500 [PR #15934] (v7.1.0), and the Contact timeline returned 500 for a deleted Asset [PR #16078] (v7.1.3).
- Public links display inline by default since 5.0 [PR #11043] (v5.0), but only for extensions in the `streamed_extensions` parameter, because ICS files rendered as text [PR #11474] (v5.0). The form "Download asset" action must still force a download [PR #11462] (v4.4.3).
- The "Block search engines from indexing this file" option (`disallow`) sends `X-Robots-Tag: noindex, nofollow, noarchive`. Reviewers asked for positive "allow indexing" wording; the author kept "disallow" [PR #5667] (~v2.13.0). New Assets have it on by default since 5.1, because Assets are usually gated behind forms [PR #13531] (v5.1.0).
- The API returns a public `downloadUrl` for each Asset [PR #717] (~v1.2.0).

### Assets: download tracking
- A download is unique when the tracking cookie was just created, or else when no row exists for the tracking id; a COUNT query was too slow on large tables [PR #1244] (~v1.2.3).
- Click-through downloads record `source` and `source_id` even when the Email no longer exists [PR #2321] (~v2.1.1).
- Admin preview must not increment the download count [PR #4239] (~v2.9.0).
- UTM parameters on the download URL are stored on the download row and shown in the Asset Downloads report [PR #12098] (v5.0). Behaviour A4.31 shows 7.x stores five of them, not `utm_id` (see Open questions).
- Tracking is skipped when there is no HTTP request, so CLI broadcast sends with attachments no longer crash [PR #14360] (v5.2.1).
- A non-existent Asset gives 404, not 500 [PR #14663] (v5.2.4).

### Assets: emails, forms, campaigns
- Remote Assets can be email attachments; the mailer fetches them [PR #599] (~v1.1.3). Attaching an Asset to an email after the Symfony 6 refactor is covered by a functional test [PR #14715] (v6.0.0).
- `{assetlink=ID}` is replaced and tracked even inside an `href` attribute [PR #1083] (~v1.2.3).
- The form "Download asset" action can serve "the latest asset from the category", so marketers publish a new file version without editing the form. With no Asset in the Category nothing is served, but the submission is saved [PR #6319] (~v2.15.0). The Category select shows only for that option [PR #11461] (v4.4.3).
- The campaign "asset downloaded" decision fires through `onCampaignTriggerDecision` [PR #2309] (~v2.1.1).

### Assets: permissions, list and UI
- Assets have own/other permissions; "view own" sees only the User's own Assets [PR #941] (~v1.2.1).
- The edit page enforces edit permission on the server; a view-only User gets 403 at `/s/assets/edit/{id}`. A hidden button had been the only guard [PR #13345] (v5.1.0).
- The list has Created, Modified and Created by columns and sorts by modified date descending. A reviewer objected that items shift around; the default was kept as user-friendly [PR #9688] (v4.2.0).
- The list page size uses `default_assetlimit`, else `default_pagelimit`; a find-and-replace bug had ignored it [PR #16035] (v7.1.1).
- Batch delete removes files from disk as single delete does [PR #949] (~v1.2.1). The delete confirmation says a locally stored file is deleted permanently, while for remote Assets only the record goes [PR #17448] (unreleased 7.x).
- List "Preview" opens the preview modal for images and PDFs [PR #15054] (~v7.0). Images zoom on hover, PDFs open in a dialog, and a message replaces the tile when no preview exists [PR #15110] (~v7.0).
- The detail page shows labels for type, indexing block, storage location and language [PR #14756] (v7.0.0).
- Bulk "Download selected assets" builds one ZIP, checking each Asset's permission. Review raised DoS (no limit) and CSRF (GET without token); 7.x has a 100-Asset cap and a CSRF check [PR #15609] (unreleased 7.x).
- The dashboard and data-API Asset widgets work again; "unique vs repetitive downloads" builds the unique-Contact subquery first. The bug had been hidden in the PHPStan baseline [PR #16498] (v7.2.0).

### Asset reports
- Download counts respect the report date range and can be sorted [PR #9641] (~v3.3.3).
- The Asset Downloads report is per download: without a group-by each download is a row. A default group-by from [PR #10693] (v4.1.2) was replaced by this rule in [PR #10833] (v4.2.0).

### Categories
- One Categories screen with a Type filter replaced per-bundle menu items. Bundles and plugins register types in config; plugin types use a `plugin:` prefix [PR #864] (~v1.2.1).
- A Category's Type cannot change after creation: "That would cause chaos when the category has some items in it" [PR #864].
- Inline creation fixes and hides the Type, closes the modal and selects the new Category [PR #249] (~v1.0) [PR #8800] (v3.0.0) [PR #10164] (v4.0.0). After a failed validation the Type field stays (hidden inline) [PR #14445] (v5.2.6). A Category created inline from Dynamic Web Content gets the Dynamic Web Content type [PR #15726] (v7.1.0).
- Global Categories are available to every bundle [PR #2821] (~v2.3).
- The menu entry is hidden without category view permission [PR #1216] (~v1.2.3). Filtering by Type returns only that type [PR #8479] (v3.0.0).
- Category changes are written to the audit log [PR #11275] (v5.0).
- A Category checked out by another User shows the lock notice with an override link, not a 500 [PR #11854] (v5.0.0) [PR #15726] (v7.1.0).
- An alias with spaces saves, with spaces turned into `-` [PR #12719] (v5.0).
- Colour is stored without `#`, and templates add one [PR #13123] (v5.0.0).
- The published toggle reads "Available for use"; Published/Unpublished, On/Off and Draft/Enabled were rejected [PR #13374] (v5.1.0).
- A Category used by other entities cannot be deleted, singly or in batch. Bundles register their category-using entities through `CategoryTypeEntityEvent` [PR #14567] (v6.0.0).
- Category form buttons: [PR #14680] (v6.0.0) removed the Apply button (`apply_text => false`). [PR #14819] reverted it on the 6.0 branch (v6.0.1), so 6.0.1 to 6.0.9 have Apply again. The 7.x line kept #14680: `apply_text => false` is in 7.0.0 and later. Controllers must use `isButtonClicked()`, because `->get('apply')` caused a 500 on save [PR #16180] (v7.1.3).
- Single Category delete shows a confirmation like the batch one [PR #16830] (v7.2.0). Its text says items become uncategorised, which conflicts with the in-use guard (see Open questions).
- API v2 categories declare no API Platform filters, so `?bundle=` is ignored there; a test pins this [PR #17421] (8.0 dev).

### Projects
- Projects started as a skeleton in 7.0: name, description, list, detail, form and menu item. It merged incomplete on purpose; smaller PRs were preferred [PR #15002] (v7.0.0).
- Projects group things users create, not Contacts, because Categories are "a little messy" in serving both. An entity can be in many Projects but only one Category [PR #15072] (~v7.0).
- Deleting a Project removes only its links; entities stay untouched [PR #15002] (v7.0.0).
- Coverage grew from Campaign, Email, Form, Segment and SMS [PR #15002] to Marketing Messages, Focus Items, Companies, Assets and Landing Pages [PR #15072] (~v7.0). Behaviour C.94 lists 14 types in 7.x.
- `project:"Name"` filters each participating list [PR #15002] [PR #15072] (~v7.0).
- Legacy APIs return `projects` with only `id` and `name`; endpoints had been inconsistent [PR #15507] (~v7.0).
- The detail page lists members by type and adds or removes them in a modal, checking each type's permission. Types are discovered automatically rather than listed [PR #15327] (~v7.0).
- The UI term "entities" was challenged as jargon; "items" was preferred and "resources" rejected because it clashes with Assets. The term stayed pending a rename [PR #15327].
- Plugins can link their own entities through `EntityTypeModelMappingEvent` and `EntityTypeNormalizationEvent` [PR #15485] (~v7.0). Detail links use per-type routes from `EntityTypeDetailRouteSubscriber` [PR #15493] (v7.1.0).
- The add-entity lookup leaves out existing members [PR #15493] (v7.1.0) and is no longer capped at 10 results [PR #15719] (v7.1.0) [PR #15861] (v7.0.1). Behaviour C.105 gives the cap as 1000.
- Project names are unique, case-insensitive and ignoring surrounding whitespace, backed by a migration; this also blocks inline creation [PR #15564] (v7.1.0).
- With one editable type, the Add button opens that type's picker directly [PR #16927] (v7.2.0).
- The empty Projects list shows a content block; a search with no results shows the normal message [PR #15292] (~v7.0).
- Project screens avoid `bg-white`, `bg-auto` and `table-striped`, which break dark mode [PR #15438] (~v7.0).
- Project, Asset Download, Company, ContactCategory and User are exposed in API v2. v2 PUT replaces rather than creates. It was cherry-picked to 7.0 to ship in the major [PR #15552] (v7.0.0).
- Legacy `/api/projects` CRUD and batch delete, plus `/api/v2/projects`, arrived after 7.2.1. To link Projects through an entity's v1 API, PATCH `"projects": [ids]`; the array replaces the existing links [PR #15569] (unreleased 7.x).

### Cross-cutting code changes
- Concrete controllers, including Asset, Category and Project controllers, are `final` [PR #16603] (v7.2.0). Event subscribers are `final` (and `readonly` where possible) [PR #16735] (~v7.2).
- Entity validation rules (Asset, Category and others) are PHP attributes instead of `loadValidatorMetadata()`, with the same rules [PR #16959] (~v7.2).
- `FormModel::deleteEntity()` sets `deletedId` so post-delete listeners can read the id [PR #17421] (8.0 dev).
- Asset and Category views are Twig templates since 5.0 [PR #11554] [PR #11610] [PR #11846] [PR #12100] [PR #12102] (v5.0). Controllers are autowired services since 5.0 [PR #11892] (v5.0).

## Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| Upload larger than PHP limit fails after transfer | Dropzone limit is the lowest of `max_size` and PHP limits | [PR #586] | 1.1.3 |
| Unlimited PHP limits (-1/0) block uploads | Treated as unlimited | [PR #1024] | ~1.2.1 |
| Batch delete leaves files on disk | Files deleted with the records | [PR #949] | ~1.2.1 |
| Long remote URL (>191 chars) gives 500 | Stored as TEXT | [PR #9542] | 4.0.0 |
| Remote Asset via API has null MIME and extension | Populated | [PR #9120] | ~3.2.0 |
| Empty Asset language gives 500 | Language required | [PR #10406] | 4.0.1 |
| Configured extension (mp4) has no effect | Upload validation uses `allowed_extensions` | [PR #15111] | 5.2.7 |
| PHP file renamed to .png accepted | MIME must match extension | [PR #16045] | 7.2.0 |
| Remote URL of disallowed type accepted | Remote MIME validated; non-2xx rejected | [PR #16045] | 7.2.0 |
| Unconfigured S3 browse gives PHP error | Readable credentials error | [PR #14865] | ~7.0 |
| Large remote download exhausts memory | 302 redirect to remote URL | [PR #944] | ~1.2.1 |
| Asset downloadable by guessing its id | `/asset/{id}` gives 404; UUID URL | [PR #15138] [PR #15776] | 7.1.0 |
| Unknown Asset slug gives 500 | 404 | [PR #14663] | 5.2.4 |
| ICS files shown as plain text | Only `streamed_extensions` inline | [PR #11474] | 5.0 |
| Form download action no longer downloads | Submission starts a download | [PR #11462] | 4.4.3 |
| Admin preview increments download count | Preview not counted | [PR #4239] | ~2.9.0 |
| Click-through download errors when Email deleted | Source recorded regardless | [PR #2321] | ~2.1.1 |
| Broadcast send with attachment crashes in CLI | Tracking skipped without request | [PR #14360] | 5.2.1 |
| Asset API DELETE gives 500 | Delete succeeds; no URL for id-less entity | [PR #15934] | 7.1.0 |
| Contact page 500 after a downloaded Asset is deleted | Row shows "Deleted asset", no link | [PR #16078] | 7.1.3 |
| `{assetlink}` inside `href` not replaced | Replaced and tracked | [PR #1083] | ~1.2.3 |
| Attaching an Asset to an email gives 500 | Works | [PR #14715] | 6.0.0 |
| View-only User edits Asset via URL | 403 | [PR #13345] | 5.1.0 |
| Asset list ignores per-page limit | `default_assetlimit`, else `default_pagelimit` | [PR #16035] | 7.1.1 |
| Timeline Asset preview uses missing template | Uses `Modules/preview.html.twig` | [PR #16034] | 7.1.1 |
| List Preview streams the file | Preview modal opens | [PR #15054] | ~7.0 |
| `unique.vs.repetitive.downloads` TypeError | Returns chart data | [PR #16498] | 7.2.0 |
| Asset Downloads report ignores date range | Counts limited to the range | [PR #9641] | ~3.3.3 |
| Count columns collapse report to one row | Per-download rows unless grouped | [PR #10693] [PR #10833] | 4.1.2, 4.2.0 |
| Clone then Apply creates a copy each click | Apply updates the new entity | [PR #2305] | ~2.1.1 |
| Category menu shown without permission | Menu hidden | [PR #1216] | ~1.2.3 |
| Category Type filter shows all | Filter applied | [PR #8479] | 3.0.0 |
| Inline Category create leaves the modal | Modal closes, new Category selected | [PR #8800] [PR #10164] | 3.0.0, 4.0.0 |
| Category Type field disappears after failed save | Type stays (hidden inline) | [PR #14445] | 5.2.6 |
| DWC inline Category gets wrong type | Dynamic Web Content type | [PR #15726] | 7.1.0 |
| Locked Category gives error or 500 | Lock notice with override link | [PR #11854] [PR #15726] | 5.0.0, 7.1.0 |
| Category alias with spaces gives 500 | Saves; space becomes `-` | [PR #12719] | 5.0 |
| Category colour saved as `##xxxxxx` | Single `#` | [PR #13123] | 5.0.0 |
| Category save gives "Child apply does not exist" | Saves; controller checks the button | [PR #16180] | 7.1.3 |
| In-use Category deleted | Refused, singly and in batch | [PR #14567] | 6.0.0 |
| Duplicate or case-variant Project names | Rejected | [PR #15564] | 7.1.0 |
| Project add-entity shows only 10 results | Many more (cap 1000) | [PR #15719] [PR #15861] | 7.1.0, 7.0.1 |
| Project detail links and labels wrong for Points, Stages, Point Triggers | Per-type routes and labels | [PR #15493] | 7.1.0 |
| Inconsistent `projects` API payload | `id` and `name` only | [PR #15507] | ~7.0 |
| API v2 PUT creates a new resource | PUT replaces | [PR #15552] | 7.0.0 |
| White backgrounds on Project screens in dark mode | No hardcoded Bootstrap bg/stripe classes | [PR #15438] | ~7.0 |
| Upload size check off by 1000x | Correct limit | [PR #17080] | 8.0 dev |

## Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.0-1.2 | AJAX upload with extension allow-list; client-side checks; remote URL field editable; API `downloadUrl`; one Categories screen; own/other permissions; audio/video preview; remote redirect | [PR #130] [PR #133] [PR #279] [PR #717] [PR #864] [PR #941] [PR #944] |
| 2.x | Asset and Category API write endpoints; global Categories; preview `?stream=1`/`?download=1`; block indexing (`disallow`); latest Asset from Category | [PR #2738] [PR #2821] [PR #3228] [PR #5667] [PR #6319] |
| 3.0-4.2 | Single size helper; remote path as TEXT; list columns and modified-date sort | [PR #8392] [PR #9542] [PR #9688] |
| 5.0 | Stream by default with `streamed_extensions`; UTM on downloads; Category audit log; Twig views | [PR #11043] [PR #11474] [PR #12098] [PR #11275] [PR #11554] |
| 5.1 | "Available for use" label; block indexing on by default; server-side edit check | [PR #13374] [PR #13531] [PR #13345] |
| 6.0 | In-use Category delete guard; Symfony 6.4 | [PR #14567] [PR #13962] |
| 7.0 | Projects bundle and coverage; Asset detail labels; preview modal; API v2 entities | [PR #15002] [PR #15072] [PR #15327] [PR #14756] [PR #15110] [PR #15552] |
| 7.1 | UUID download URLs; remote domain allow-list; unique Project names; per-type detail routes | [PR #15138] [PR #15776] [PR #15868] [PR #15564] [PR #15493] |
| 7.2 | Remote MIME validation; single-type add shortcut; single Category delete confirmation; final controllers | [PR #16045] [PR #16927] [PR #16830] [PR #16603] |
| unreleased 7.x | Bulk ZIP download; Projects legacy API; delete confirmation wording | [PR #15609] [PR #15569] [PR #17448] |
| 8.0 dev | Upload size fix (BC break); v2 Category filter test | [PR #17080] [PR #17421] |

## Removed, deprecated, replaced

| What | Replaced by | PR | Version |
|---|---|---|---|
| Per-bundle Category menu items | One Categories screen with Type filter | [PR #864] | ~1.2.1 |
| Proxy-streaming remote Assets | 302 redirect | [PR #944] | ~1.2.1 |
| `Asset::convertSizeToBytes()` | `FileHelper::convertPHPSizeToBytes()` | [PR #8392] | 3.0.0 |
| `Mautic\CategoryBundle\Helper\MenuHelper` | Removed | [PR #8053] | 3.0.0 |
| PHP templates for Assets and Categories | Twig | [PR #11554] [PR #12102] | 5.0 |
| Category Apply button | Removed in 6.0.0 and 7.x; restored in 6.0.1-6.0.9 by the revert | [PR #14680] [PR #14819] | 6.0.0 / 6.0.1 |
| Bare `/asset/{id}` | `/asset/{uuid}`; legacy `{id}:{alias}` kept, lenient forms deprecated | [PR #15138] [PR #15776] | 7.1.0 |
| `allowed_mimetypes` parameter | Symfony `MimeTypes` from `allowed_extensions` | [PR #16045] | 7.2.0 |
| `Asset::validateFile()`, `AssetType::validateExtension()` | `Upload` constraint | [PR #16045] | 7.2.0 |
| `loadValidatorMetadata()` on Asset, Category | Validator attributes | [PR #16959] | ~7.2 |
| Extensible controllers and subscribers | `final` classes | [PR #16603] [PR #16735] | 7.2.0 |
| Untyped Asset signatures | Typed (BC break) | [PR #17080] | 8.0 dev |

## Maintainer norms for this area
- Public URLs already in sent emails must keep working; add new URL formats, do not break old ones [PR #15138] [PR #15776].
- Prefer a safe default over a config switch nobody enables [PR #15776].
- New config parameters need a linked user-docs PR before merge [PR #15868] [PR #12098] [PR #11474].
- Bulk endpoints need a size cap and a CSRF token; state-changing GETs are not accepted [PR #15609].
- Permission checks belong on the server; hiding a button is not access control [PR #13345].
- Escape Asset titles in builder token lists, search and the timeline [PR #1195].
- Destructive confirmations must state the consequence [PR #16830] [PR #17448].
- Entity mapping and migration change together, and a migration moves a PR to the feature branch [PR #9542].
- Tests must not make real HTTP requests; remote-Asset tests use `RemoteFileServerTrait` [PR #17214].
- Bug fixes need automated tests; reviewers ask for them [PR #9641] [PR #14445] [PR #17080].
- Do not hide bugs in the PHPStan baseline; reduce it instead [PR #16498].
- Avoid Bootstrap classes that break dark mode, and check backported utilities before writing CSS [PR #15438] [PR #15587].
- Prefer marketer-friendly terms over developer jargon such as "entities" [PR #15327].
- Changes that affect plugin developers, such as finalising classes, stay open for feedback [PR #16603].
- Prefer several small PRs; an incomplete feature can merge as a skeleton [PR #15002].

## Open questions
- URL format: [PR #15776]'s table lists `/asset/53:{uuid}` as working. In 7.x that form works only as a legacy `{id}:<anything>` slug when the alias is not NULL; the generated URL is bare `/asset/{uuid}` (behaviour A3.19-20). behaviour.md wins.
- Conflict with behaviour.md: [PR #16830] and [PR #15292] word the Category delete message as "items become uncategorised". Since [PR #14567] the delete is refused while a registered entity uses the Category (behaviour B.83-84). behaviour.md wins.
- Conflict with behaviour.md: [PR #12098] lists `utm_id` among stored UTM fields. Behaviour A4.31 shows 7.x stores only five, without `utm_id`.
- Minor: [PR #11854] and [PR #15726] describe a lock notice with an override link; behaviour B.87 records a JSON `closeModal` with an error flash. Both may hold.
- When the lenient `{id}:` and wrong-alias forms will 404 is not decided [PR #15776].
- Whether the bulk ZIP fetches remote Assets is not shown in review [PR #15609]; behaviour A6.60 shows 7.x rejects remote Assets.
- Remote MIME validation is always on, so saving a remote Asset needs the instance to reach the URL, even with `validate_remote_domains` off [PR #15868] [PR #16045].
- Whether underscores are allowed in aliases was left open [PR #13372].
- Whether the `plugin:` prefix for plugin Category types is still required [PR #864].
- How failed downloads of missing Assets appear in Contact history was truncated in the input [PR #14663].

## Coverage
The area has 149 merged PRs in two chunks: chunk 1 has 106 (#63 to #14858, 2015-02 to 2025-05; about 84 substantive) and chunk 2 has 43 (#14865 to #17448, 2025-04 to 2026-10; 37 substantive).
About 26 PRs were low-signal (branch merges, CS fixes, production asset builds, funding.json) and used only for norms.
A further 869 noise PRs across all areas were excluded upstream before chunking.
