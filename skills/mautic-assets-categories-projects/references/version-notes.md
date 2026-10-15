# Version notes — Assets, Categories, Projects

## 5.x / 6.x history
- No Projects exist in 5.x or 6.x. `ProjectBundle` and the `*_projects_xref` tables arrive in 7.x; their migrations are dated April–June 2025. [code: app/migrations/Version20250409150440.php @7.x] [code: app/migrations/Version20250618122722.php @7.x]
- Before Mautic 5, the API enablement config lived in `app/config/local.php` rather than `config/local.php`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html]
- Before 7, the API rate-limiter cache was configurable (`api_rate_limiter_cache`); 7.x no longer offers it. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-rate-limiter-cache]
- Old Asset URLs use the form `/asset/{id}:{alias}`. 7.x generates `/asset/{uuid}`, and it still resolves the old form for Assets that have an alias. [code: app/bundles/AssetBundle/Model/AssetModel.php:628-655 @7.x] [code: app/bundles/AssetBundle/Entity/Asset.php:1290-1297 @7.x]
- OpenStack and Rackspace cloud storage existed once. Only image and translation leftovers remain, and Amazon S3 is the only provider in 7.x. The version that removed them is not known. [code: plugins/MauticCloudStorageBundle/Config/services.php:20-21 @7.x]
- 5.0: public links display inline, but only for extensions in `streamed_extensions`; other types download. [PR #11043] [PR #11474]
- 5.0: UTM parameters on the download URL are stored on the download row and appear in the Asset Downloads report. [PR #12098]
- 5.0: Category changes are audit-logged, aliases with spaces save, and colour is stored without `#`. [PR #11275] [PR #12719] [PR #13123]
- 5.1: new Assets block search-engine indexing by default (`disallow=true`), and the edit page returns 403 to view-only Users. [PR #13531] [PR #13345]
- 5.1: the Category published toggle is labelled "Available for use". [PR #13374]
- 5.2.1: download tracking is skipped without an HTTP request, so CLI sends with attachments work. [PR #14360]
- 5.2.4: an unknown Asset slug returns 404 instead of 500. [PR #14663]
- 5.2.6 and 5.2.7: the Category Type field survives a failed save, and uploads honour the configured `allowed_extensions`. [PR #14445] [PR #15111]
- 6.0.0: a Category used by registered entities cannot be deleted, singly or in batch. [PR #14567]
- 6.0.0 removed the Category Apply button. [PR #14819] reverted that on the 6.0 branch, so 6.0.1 to 6.0.9 have Apply again; the 7.x line kept the removal. [PR #14680]
- 6.0.0: attaching an Asset to an email works again after the Symfony 6.4 upgrade. [PR #14715] [PR #13962]

## 7.x minors
- 7.0–7.2: Projects with UI, legacy API, API Platform `/api/v2/projects`, `project:"Name"` search on 14 entity types, and the `associate` permission. [code: app/bundles/ProjectBundle/Security/Permissions/ProjectPermissions.php:15-36 @7.x]
- API Platform resources exist for Asset, Download (read-only, ownership-scoped), Category and Project. [code: app/bundles/AssetBundle/Entity/Download.php:16-30 @7.x]
- 7.0: Projects bundle, project-aware Assets, preview modal and zoom, Asset detail labels, and API v2 for Project, Asset Download and ContactCategory. [PR #15002] [PR #15072] [PR #15110] [PR #14756] [PR #15552]
- 7.0.1: the Project add-entity lookup is no longer capped at 10 results. [PR #15861]
- 7.1: bare `/asset/{id}` returns 404 and new URLs use `/asset/{uuid}`; legacy `{id}:{alias}` still resolves for Assets with an alias. [PR #15138] [PR #15776]
- 7.1: optional remote-domain allow-list (`validate_remote_domains`, `allowed_remote_domains`), unique case-insensitive Project names, and per-type Project detail routes. [PR #15868] [PR #15564] [PR #15493]
- 7.1.1 and 7.1.3: list page size honours `default_assetlimit`; deleted Assets no longer break the Contact timeline; Category edits save without an Apply button. [PR #16035] [PR #16078] [PR #16180]
- 7.2: remote Assets are MIME-validated at save; `allowed_mimetypes` is removed (absent from the 7.2.0 tag onwards). [PR #16045]
- 7.2: single Category delete confirmation, the one-type Project add shortcut, working Asset dashboard widgets, and `final` controllers. [PR #16830] [PR #16927] [PR #16498] [PR #16603]
- 7.x after 7.2.1 (unreleased): legacy `/api/projects` CRUD and new delete-confirmation wording for Asset files. [PR #15569] [PR #17448]
- 7.x after 7.2.1 (unreleased; [PR #15609]) adds the Asset batch ZIP download: `batchDownload`, at most 100 Assets and 500 MiB. It is among the 736 7.x commits not yet forward-merged into 8.x. [code: app/bundles/AssetBundle/Service/ArchiveBuilder.php:13 @7.x]

## 8.x delta (8.x @ 11599729491 vs 7.2.1)
- **Asset events by class.** Asset CRUD events are dispatched as `AssetPreSaveEvent`, `AssetPostSaveEvent`, `AssetPreDeleteEvent` and `AssetPostDeleteEvent`, alongside `AssetLoadEvent` and `RemoteAssetBrowseEvent`. Subscribe with `::class` keys.
  - A listener keyed on a kept-but-unused string constant silently never runs.
  - `ASSET_ON_UPLOAD` is dropped.
  - `AssetEvent` is no longer `final`.

  [PR #17196] [PR #17215]
- **Service id.** `mautic.asset.upload.error.handler` is removed; reference the class instead. [PR #17196]
- **Category events.** `CATEGORY_ON_BUNDLE_LIST_BUILD` is dispatched as `CategoryTypesEvent`; the constant is kept. `CategoryModel` CRUD events still dispatch by string name. The duplicate `CATEGORY_*` constants in `DynamicContentEvents` are removed; use `CategoryEvents`. [PR #17217] [PR #17097]
- **Upload size.** Asset upload size validation, which was off by a factor of 1000, is fixed. [PR #17080]
- **Batch ZIP.** Not on 8.x code yet, although the 8.0 docs describe it; it arrives with the next forward merge. [docs: https://docs.mautic.org/en/8.0/components/assets.html#downloading-multiple-assets]
- **API controllers.** `CommonApiController` and `FetchCommonApiController` get return types and visibility changes, for example `checkEntityAccess(): bool|Response`. This affects plugins that extend `AssetApiController` or `CategoryApiController` patterns. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- **Generated aliases.** These are checked against `ReservedWords`, so a few aliases that were previously left alone now get a prefix. That can affect Category aliases generated by `cleanAlias`. [PR #17361]
- **Not yet decided.** The `default_assetlimit` parameter is marked "remove in Mautic 8" but is still read on 7.2.1. [code: app/bundles/AssetBundle/Controller/AssetController.php:59-63 @7.x]
- **Unchanged.** The 8.0 docs for Categories and Projects are unchanged, and the inputs record no 8.x code change for ProjectBundle. [docs: https://docs.mautic.org/en/8.0/projects/projects-overview.html]

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
