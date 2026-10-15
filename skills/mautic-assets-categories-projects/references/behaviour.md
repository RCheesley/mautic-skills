# Behaviour specification — Assets, Categories, Projects (Mautic 7.x)

Authoritative tree: upstream 7.x at 419a08a9b35 (release 7.2.1 plus unreleased merged PRs). Paths are relative to the repo root. Where docs disagree with code, code wins and the discrepancy is listed in section D.

## Contents
- A. Assets
  - A1 Lifecycle and defaults (1–8)
  - A2 Upload and validation (9–18)
  - A3 Public download URL and response (19–28)
  - A4 Download tracking (29–40)
  - A5 Integrations: campaign, points, forms, tokens, A/B, reports, dashboard (41–52)
  - A6 Admin UI, list, permissions, batch ZIP (53–64)
  - A7 API, import/export, cloud storage (65–72)
- B. Categories (73–92)
- C. Projects (93–112)
- D. Docs-vs-code discrepancies and open questions

---

## A. Assets

An Asset is a file offered for download, either stored locally ("local") or referenced by URL ("remote"). The public URL tracks each download against the Contact.

### A1 Lifecycle and defaults
1. A new Asset defaults to `storageLocation='local'`, `language='en'`, `revision=1`, `downloadCount=0`, `uniqueDownloadCount=0`, `disallow=true`. [code: app/bundles/AssetBundle/Entity/Asset.php:81,151,169,175,181,217 @7.x]
2. A null `storage_location` in the database reads as `local`. [code: app/bundles/AssetBundle/Entity/Asset.php:468-475 @7.x]
3. Each save of an existing Asset increments `revision`; the model then runs the standard pre/post save flow. [code: app/bundles/AssetBundle/Model/AssetModel.php:83-93 @7.x]
4. Every create or update with changes writes an audit log row (`bundle=asset, object=asset, action=create|update`); delete writes `action=delete` with the title. [code: app/bundles/AssetBundle/EventListener/AssetSubscriber.php:32-62 @7.x]
5. Deleting an Asset (single or batch) unlinks the local file. The controller calls `removeUpload()`, and `ASSET_POST_DELETE` calls it again so batch deletes also remove files. `asset_downloads` rows are deleted by FK cascade. [code: app/bundles/AssetBundle/Controller/AssetController.php:649-650 @7.x] [code: app/bundles/AssetBundle/EventListener/AssetSubscriber.php:64-65 @7.x] [code: app/bundles/AssetBundle/Entity/Download.php:121-124 @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#deleting-an-asset]
6. Cloning copies the Asset with `downloadCount=0`, `uniqueDownloadCount=0`, `revision=0` and `isPublished=false`, keeping its category and projects. It requires `create` plus view access to the source. [code: app/bundles/AssetBundle/Controller/AssetController.php:584-606 @7.x] [code: app/bundles/AssetBundle/Entity/Asset.php:340-345 @7.x]
7. An Asset counts as published only when `isPublished` is true, `publishUp` (if set) is not in the future, `publishDown` (if set) is not in the past, and its Category (if any) is published. [code: app/bundles/CoreBundle/Entity/FormEntity.php:233-251,412-435 @7.x]
8. Opening the edit form locks the Asset, and cancelling unlocks it. Another User cannot edit or delete a locked Asset. [code: app/bundles/AssetBundle/Controller/AssetController.php:481-484,530,548,645-646,753-755 @7.x]

### A2 Upload and validation
9. A local upload is two-step. Dropzone posts to the OneupUploader `asset` endpoint, which validates the file, moves it to `<upload_dir>/tmp/<tempId>/<file>` and returns `tmpFileName`. The form carries `tempId`, `tempName` and `originalFileName`, and saving moves the file to `<upload_dir>/<sha1>.<ext>`. [code: app/bundles/AssetBundle/EventListener/UploadSubscriber.php:37-53 @7.x] [code: app/bundles/AssetBundle/Form/Type/AssetType.php:54-70,147-153 @7.x] [code: app/bundles/AssetBundle/Entity/Asset.php:667-721 @7.x]
10. The upload endpoint checks each file in this order: size above `getMaxUploadSize('B')`, extension not in `allowed_extensions`, then client or detected MIME type not matching the extension. Each failure is returned to Dropzone as `error`. [code: app/bundles/AssetBundle/EventListener/UploadSubscriber.php:60-92 @7.x] [code: app/bundles/AssetBundle/ErrorHandler/DropzoneErrorHandler.php:12-18 @7.x]
11. The effective maximum is `min(max_size MB, post_max_size, upload_max_filesize, memory_limit)`. A value of `-1` or `0` (in config or php.ini) counts as unlimited. [code: app/bundles/AssetBundle/Model/AssetModel.php:448-464 @7.x] [code: app/bundles/AssetBundle/Entity/Asset.php:1186-1199 @7.x]
12. Default `allowed_extensions`: csv, doc, docx, epub, gif, jpg, jpeg, mpg, mpeg, mp3, odt, odp, ods, pdf, png, ppt, pptx, tif, tiff, txt, xls, xlsx, wav. Change the list in Configuration → Asset Settings. [code: app/bundles/AssetBundle/Config/config.php:59-64 @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#uploading-an-asset]
13. On form submit, the `Upload` constraint applies. For a local Asset:
    - a new Asset needs `tempName` or `path` (`mautic.asset.asset.error.missing.file`);
    - the stored, temp and original extensions must each be allowed and must match the MIME type;
    - `remotePath` is set to null.

    [code: app/bundles/AssetBundle/Validator/Constraints/UploadValidator.php:24-76 @7.x]
14. For a remote Asset, `remotePath` is required. Its MIME type comes from the `Content-Type` header, or else from `finfo` on the first 1024 bytes, and must map to an allowed extension. `path` is set to null. [code: app/bundles/AssetBundle/Validator/Constraints/UploadValidator.php:87-141 @7.x] [code: app/bundles/AssetBundle/Entity/Asset.php:1299-1340 @7.x]
15. `remotePath` must be a valid URL and pass `SafeRemoteUrl`. With `validate_remote_domains` enabled, only allowed remote domains and the instance domain are accepted. [code: app/bundles/AssetBundle/Entity/Asset.php:93-97 @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#using-remote-assets]
16. `tempId` passes through `basename()`, which prevents path traversal. [code: app/bundles/AssetBundle/EventListener/UploadSubscriber.php:41 @7.x]
17. The stored file name is `sha1(uniqid(mt_rand(), true)).<ext>`. The client name is kept in `original_file_name` and becomes the title when the title is empty. For a remote Asset, the title defaults to `basename(remotePath)`, and extension, MIME type and size come from a cURL HEAD request (5 s connect timeout). [code: app/bundles/AssetBundle/Entity/Asset.php:655-697,865-881,1347-1356 @7.x]
18. Replacing the file on edit unlinks the old file and removes the temp folder once the new file has moved. [code: app/bundles/AssetBundle/Entity/Asset.php:355-365,702-717 @7.x]

### A3 Public download URL and response
19. `generateUrl()` builds `/asset/{slug}`, where the slug is the UUID or, failing that, `{id}:{alias}`. It adds `?stream=` when asked, and `ct=<encoded>` when a click-through is given. [code: app/bundles/AssetBundle/Model/AssetModel.php:420-438 @7.x] [code: app/bundles/AssetBundle/Entity/Asset.php:1290-1297 @7.x]
20. Slug resolution tries the UUID first. If that fails, `{id}:{alias}` is accepted when `id` is numeric and the Asset has a non-null alias; the alias text itself is not compared. Anything else returns 404. [code: app/bundles/AssetBundle/Controller/PublicController.php:45-58 @7.x] [code: app/bundles/AssetBundle/Model/AssetModel.php:637-655 @7.x]
21. Nothing in 7.x sets `alias` on new Assets: the form has no alias field and only tests call `setAlias`. New Assets are therefore reachable only by UUID. [code: app/bundles/AssetBundle/Form/Type/AssetType.php @7.x]
22. For an unpublished Asset, a visitor without view access gets a tracked download with `code=401` and then Access Denied (HTTP 403 in the functional test). A User with `viewown`/`viewother` access still downloads it. [code: app/bundles/AssetBundle/Controller/PublicController.php:78-101 @7.x] [code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:105-113 @7.x]
23. A remote Asset is tracked with `code=200` and redirected (302) to `remotePath`. [code: app/bundles/AssetBundle/Controller/PublicController.php:108-113 @7.x]
24. A local Asset is read fully into memory and served with the detected MIME type. A missing file is tracked with `code=404` and returns 404. [code: app/bundles/AssetBundle/Controller/PublicController.php:131-142 @7.x]
25. Extensions in `streamed_extensions` (default gif, jpg, jpeg, mpg, mpeg, mp3, pdf, png, wav) are served inline unless `?stream=0`. Other files are sent with `Content-Disposition: attachment; filename="<originalFileName>"`. `streamed_extensions` is not in the config UI; set it in `local.php`. [code: app/bundles/AssetBundle/Controller/PublicController.php:148-158 @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#display-assets-directly-in-the-browser]
26. When `disallow` is true ("Block search engines from indexing this file"), the response carries `X-Robots-Tag: noindex, nofollow, noarchive`. [code: app/bundles/AssetBundle/Controller/PublicController.php:144-146 @7.x]
27. Preview (`/s/assets/preview/{id}`) streams streamed extensions inline. `?stream=0` renders the preview modal and `?download=1` forces an attachment. [code: app/bundles/AssetBundle/Controller/AssetController.php:246-289 @7.x]
28. The "Download an Asset" form action always appends `&stream=0`, which forces an attachment. [code: app/bundles/AssetBundle/EventListener/FormSubscriber.php:119-122 @7.x]

### A4 Download tracking
29. `trackDownload` does nothing for logged-in Mautic Users (unless a system entry is passed) and does nothing without a current Request. [code: app/bundles/AssetBundle/Model/AssetModel.php:104-116 @7.x]
30. `trackDownload` also skips requests where `IpLookupHelper::isRequestTrackable()` is false: HEAD requests, prefetch or prerender, `Sec-GPC: 1`, DNT, and untrackable IPs. [code: app/bundles/AssetBundle/Model/AssetModel.php:118-129 @7.x] [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:276-301 @7.x]
31. The download row stores `utm_campaign`, `utm_content`, `utm_medium`, `utm_source` and `utm_term` from the query string. [code: app/bundles/AssetBundle/Model/AssetModel.php:120-124 @7.x]
32. A click-through `ct` with `lead` loads that Contact, tracks its device (creating a cookie if needed) and makes it the tracked Contact. `channel` or `source` fill `source` and `source_id`, and `email` links the row to the Email. Without a click-through, the currently tracked Contact and device are used. [code: app/bundles/AssetBundle/Model/AssetModel.php:133-189 @7.x]
33. With no tracking id and no system entry, no `asset_downloads` row is written; only `download_count` is incremented. [code: app/bundles/AssetBundle/Model/AssetModel.php:177-189,234-251 @7.x]
34. A download is unique when the tracking cookie was just generated, or when no row exists for the same `asset_id` and `tracking_id`. Only unique downloads increment `unique_download_count`. [code: app/bundles/AssetBundle/Model/AssetModel.php:234-257 @7.x] [code: app/bundles/AssetBundle/Entity/DownloadRepository.php:22-43 @7.x]
35. `mautic.asset_on_load` (`AssetLoadEvent(download, isUnique)`) fires before the row is persisted. [code: app/bundles/AssetBundle/Model/AssetModel.php:267-270 @7.x]
36. If persisting the row fails, the exception is re-thrown in `dev` and otherwise logged with `error_log`; the download still succeeds. [code: app/bundles/AssetBundle/Model/AssetModel.php:272-283 @7.x]
37. Email-attachment entries come from `MailHelper::createAssetDownloadEntries()`, which calls `trackDownload($asset, null, 200, $stat)` per recipient and then `upDownloadCount($asset, n, true)`. These rows have no `asset_id`. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1581-1613 @7.x] [code: app/bundles/AssetBundle/Model/AssetModel.php:190-232,253-257 @7.x]
38. Download rows follow the Contact. A tracking-id change rewrites `lead_id` and `tracking_id`, and a merge moves the losing Contact's rows to the winner. [code: app/bundles/AssetBundle/EventListener/LeadSubscriber.php:88-100 @7.x] [code: app/bundles/AssetBundle/Entity/DownloadRepository.php:224-250 @7.x]
39. The Contact timeline shows `asset.download` events linked to the Asset. A row whose Asset was deleted shows plain text or "deleted". [code: app/bundles/AssetBundle/EventListener/LeadSubscriber.php:37-86 @7.x]
40. API v2 `/api/v2/downloads` is read-only and scoped by ownership through the Asset's creator: a `viewown`-only User cannot read other Users' download rows. [code: app/bundles/AssetBundle/Entity/Download.php:16-30,398-401 @7.x]

### A5 Integrations
41. The campaign decision `asset.download` passes when the downloaded Asset is in the configured list or the list is empty. A non-Asset detail fails and a null detail passes. It runs in real time from `ASSET_ON_LOAD`. [code: app/bundles/AssetBundle/EventListener/CampaignSubscriber.php:31-84 @7.x]
42. The point action `asset.download` takes an optional asset limit and fires from `ASSET_ON_LOAD`. [code: app/bundles/AssetBundle/EventListener/PointSubscriber.php:31-54 @7.x] [code: app/bundles/AssetBundle/Helper/PointActionHelper.php:7-14 @7.x]
43. The form action `asset.download` ("Download an Asset") uses the configured Asset, or else the newest published Asset of the configured Category. It acts only when that Asset is published. [code: app/bundles/AssetBundle/EventListener/FormSubscriber.php:50-82 @7.x] [code: app/bundles/AssetBundle/Entity/AssetRepository.php:228-238 @7.x]
44. Its post-submit callback stops propagation, so later actions do not run. It builds the URL with click-through `lead` and `channel=['form'=>id]`. In messenger mode it returns `{download: url}`; otherwise it renders the theme `message.html.twig` with the configured message and the link. [code: app/bundles/AssetBundle/EventListener/FormSubscriber.php:84-150 @7.x]
45. `{assetlink=ID}` is offered in the Email and Landing Page builders and replaced on send and display. Emails get the click-through (`source`, `lead`, `email`) only when `shouldAppendClickthrough()` is true. Landing Pages get `source=['page', id]` plus the tracked Contact. An unknown id becomes an empty string. [code: app/bundles/AssetBundle/EventListener/BuilderSubscriber.php:40-100 @7.x] [code: app/bundles/AssetBundle/Helper/TokenHelper.php:16-33 @7.x]
46. The A/B criterion `asset.downloads` (Emails and Pages) picks the variant with the highest rate: downloads per send for Emails, downloads per hit for Pages. It counts distinct tracking ids with `code=200` since `variantStartDate`. Ties give several winners, and no data gives no winner. [code: app/bundles/AssetBundle/EventListener/DetermineWinnerSubscriber.php:30-119 @7.x] [code: app/bundles/AssetBundle/Entity/DownloadRepository.php:142-222 @7.x]
47. Report data sources are `assets` and `asset.downloads`. In `asset.downloads`, `download_count` is `COUNT(ad.id)` and `unique_download_count` is `COUNT(DISTINCT ad.lead_id)`. Graphs: downloads line, most downloaded, top referrers, HTTP status pie. [code: app/bundles/AssetBundle/EventListener/ReportSubscriber.php:18-284 @7.x]
48. Dashboard widgets (`asset.downloads.in.time`, `unique.vs.repetitive.downloads`, `popular.assets`, `created.assets`) need `asset:assets:viewown|viewother`. Without `viewother`, they show only Assets the User created. [code: app/bundles/AssetBundle/EventListener/DashboardSubscriber.php:24-175 @7.x]
49. Global search includes Assets for Users with view permission. [code: app/bundles/AssetBundle/EventListener/SearchSubscriber.php:32-54 @7.x]
50. Campaign export collects the file paths of local Assets through `AssetExportListEvent`, for the ZIP. [code: app/bundles/AssetBundle/EventListener/AssetExportListEventSubscriber.php:19-54 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html#export-campaign]
51. Entity export and import carry Asset metadata (not the file), keyed by `uuid`. Import updates a matching uuid or creates a new Asset, and duplicate analysis compares `title`. [code: app/bundles/AssetBundle/EventListener/AssetImportExportSubscriber.php:45-164 @7.x]
52. Other channels reuse the `asset.download` decision through their ChannelSubscriber. [code: app/bundles/EmailBundle/EventListener/ChannelSubscriber.php:41 @7.x]

### A6 Admin UI, list, permissions, batch ZIP
53. The asset list needs `viewown` or `viewother`; without `viewother` it shows only the User's own Assets. [code: app/bundles/AssetBundle/Controller/AssetController.php:53-55,75-81 @7.x]
54. View and preview use `hasEntityAccess(viewown, viewother)`. New needs `create`. Edit needs `editown`/`editother`. Delete needs `deleteown`/`deleteother`. [code: app/bundles/AssetBundle/Controller/AssetController.php:194-196,305-307,426-428,638-644 @7.x]
55. Asset permission bits: `asset:assets:viewown(2) viewother(4) editown(8) editother(16) create(32) deleteown(64) deleteother(128) publishown(256) publishother(512) full(1024)`. Asset category permissions: `asset:categories:view|edit|create|delete|publish|full`. [code: app/bundles/AssetBundle/Security/Permissions/AssetPermissions.php:18-25 @7.x]
56. List search commands:
    - `is:published`, `is:unpublished`, `is:uncategorized`, `is:mine`;
    - `is:expired` (published, `publishDown` < now) and `is:pending` (published, `publishUp` > now);
    - `category:<alias>`, `lang:<code>`, `project:"Name"`, `ids:`.

    Free text matches title or alias. [code: app/bundles/AssetBundle/Entity/AssetRepository.php:74-168 @7.x]
57. The UI list is ordered by `a.dateModified DESC` by default; the repository default is `a.title ASC`. [code: app/bundles/AssetBundle/Controller/AssetController.php:91-92,810-813 @7.x]
58. The list offers a category filter, stored in session as `mautic.asset.list_filters`. [code: app/bundles/AssetBundle/Controller/AssetController.php:83-89 @7.x]
59. Batch ZIP download (`POST /s/assets/batchDownload`, JSON `ids`, `_token`) needs view permission and a valid CSRF token (otherwise 403) and returns 405 for non-POST. [code: app/bundles/AssetBundle/Service/BatchDownloadRequestValidator.php:25-44 @7.x]
60. It rejects:
    - empty, non-list or non-integer `ids`, or more than 100 ids;
    - remote Assets and unreadable local files;
    - a total size over 500 MiB.

    The whole request fails with a 400 JSON response and a flash. [code: app/bundles/AssetBundle/Service/BatchDownloadRequestValidator.php:45-87 @7.x] [code: app/bundles/AssetBundle/Service/BatchFileCollector.php:27-63 @7.x] [code: app/bundles/AssetBundle/Service/ArchiveBuilder.php:13 @7.x]
61. The ZIP is named `assets-batch-<Ymd-His>.zip`. File names inside are transliterated and de-duplicated as `name (1).ext`, and the temp file is deleted after sending. Each Asset is checked with `hasEntityAccess`. [code: app/bundles/AssetBundle/Service/ArchiveBuilder.php:18-166 @7.x] [code: app/bundles/AssetBundle/Service/BatchFileCollector.php:38-44 @7.x] [code: app/bundles/AssetBundle/Service/BatchDownloadResponder.php:19-34 @7.x]
62. The Asset menu entry sits under Components (priority 300) and needs view permission. [code: app/bundles/AssetBundle/Config/config.php:40-51 @7.x]
63. List page size comes from `default_assetlimit`, falling back to `default_pagelimit`. [code: app/bundles/AssetBundle/Controller/AssetController.php:59-63 @7.x]
64. Every persisted `UuidInterface` entity (Asset, Category, Project) gets a v4 UUID on `prePersist` if none is set. A supplied UUID that already exists is replaced on a new entity. [code: app/bundles/CoreBundle/EventListener/UUIDListener.php:27-60 @7.x]

### A7 API, import/export, cloud storage
65. Legacy API `POST /api/assets/new` requires `file`. For `storageLocation=local` it must name a file already present in `upload_dir` (otherwise 400). For `remote` it becomes `remotePath` and the remote metadata is fetched. [code: app/bundles/AssetBundle/Controller/Api/AssetApiController.php:59-105 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html#create-asset]
66. API responses include `downloadUrl`, except where the entity has no id (delete responses). [code: app/bundles/AssetBundle/Controller/Api/AssetApiController.php:59-105 @7.x]
67. Legacy routes: `GET /api/assets`, `GET /api/assets/{id}`, `POST /api/assets/new`, `PUT|PATCH /api/assets/{id}/edit`, `DELETE /api/assets/{id}/delete`, plus batch variants. [code: app/bundles/AssetBundle/Config/config.php:22-27 @7.x]
68. API Platform `/api/v2/assets` supports GetCollection, Post, Get, Put, Patch and Delete, gated on `asset:assets:*`. [code: app/bundles/AssetBundle/Entity/Asset.php:32-50 @7.x]
69. The Remote tab lists integrations with feature `cloud_storage`. Browsing dispatches `ASSET_ON_REMOTE_BROWSE` and lists `Gaufrette\Filesystem::listKeys(path)`. [code: app/bundles/AssetBundle/Controller/AjaxController.php:45-79 @7.x] [code: app/bundles/AssetBundle/Controller/AssetController.php:391,552,784-803 @7.x]
70. MauticCloudStorageBundle implements only Amazon S3. Its keys are `client_id`, `client_secret`, `bucket`, `region` (default `us-east-1`) and an optional `endpoint` for S3-compatible storage. [code: plugins/MauticCloudStorageBundle/Integration/AmazonS3Integration.php:20-137 @7.x]
71. A missing S3 id or secret makes browsing fail with "AmazonS3Integration misconfigured: client_id or client_secret missing." [code: plugins/MauticCloudStorageBundle/Integration/AmazonS3Integration.php:97-100 @7.x] [code: plugins/MauticCloudStorageBundle/EventListener/RemoteAssetBrowseSubscriber.php:28-32 @7.x]
72. An Asset picked from cloud storage is stored as `storageLocation='remote'` with a URL in `remotePath`, so downloads redirect to the provider URL. [code: app/bundles/AssetBundle/Form/Type/AssetType.php:42-46,84-93 @7.x]

---

## B. Categories

A Category is a label from the single `categories` table. Its `bundle` column scopes it to one component type, or to `global` for every type.

73. A Category requires `title` and `bundle`. It also has `alias`, `description`, `color` (7 characters) and a published flag. [code: app/bundles/CategoryBundle/Entity/Category.php:55,80,91-104 @7.x] [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html#creating-and-managing-categories]
74. The type (`bundle`) is chosen from the registered types plus `global`, but only on the Categories admin screen. Inline creation sets it as a hidden preset, and it cannot be changed after creation. [code: app/bundles/CategoryBundle/Form/Type/CategoryType.php:33-59 @7.x] [code: app/bundles/CategoryBundle/Controller/CategoryController.php:216 @7.x]
75. Registered types (from each bundle's `config['categories']`): `asset`, `campaign`, `messages`, `dynamicContent`, `email`, `form`, `segment`, `page`, `point`, `sms`, `stage`, `plugin:focus`, `plugin:mauticSocial`, and `global`. [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:41-52 @7.x] [code: app/bundles/CategoryBundle/Event/CategoryTypesEvent.php:20-33 @7.x]
76. On every save, the alias (as supplied, or else the title) is cleaned and made unique within the same bundle by appending 1, 2, … . The entity's own row is excluded from the check, and different bundles may share an alias. No DB unique constraint exists. [code: app/bundles/CategoryBundle/Model/CategoryModel.php:67-92 @7.x] [code: app/bundles/CategoryBundle/Entity/CategoryRepository.php:152-169 @7.x]
77. Category pickers (`CategoryListType`, `bundle` option required) list only published Categories of that bundle or `global`, ordered by title. The placeholder is "Uncategorized", and a "Create new category…" choice is added. [code: app/bundles/CategoryBundle/Form/Type/CategoryListType.php:30-84 @7.x] [code: app/bundles/CategoryBundle/Entity/CategoryRepository.php:37-77 @7.x]
78. Inline creation: `/s/categories/{bundle}/new?inForm=1` opens a modal. On save it returns JSON `{closeModal:1, inForm:1, categoryName, categoryId}` and JS selects the new option. [code: app/bundles/CategoryBundle/Controller/CategoryController.php:198-287,575-584 @7.x]
79. On the Category list, the bundle filter is remembered in session (`mautic.category.type`). `all` and `category` show every bundle. The default order is `c.title DESC`. Search supports `is:published`, `is:unpublished` and `ids:`, and free text matches title or description. [code: app/bundles/CategoryBundle/Controller/CategoryController.php:62-120 @7.x] [code: app/bundles/CategoryBundle/Entity/CategoryRepository.php:82-133 @7.x]
80. Permissions are `<bundle>:categories:<view|create|edit|delete|publish|full>`; `global` and empty map to `category:categories:*`. Bundles that want their own category permissions declare `addStandardPermissions('categories')`. [code: app/bundles/CategoryBundle/Model/CategoryModel.php:54-65 @7.x] [code: app/bundles/CategoryBundle/Security/Permissions/CategoryPermissions.php:13-18 @7.x]
81. `CategoryApiController` falls back to the generic base when `<bundle>:categories:<action>` does not exist; `CategoryController` does not. [code: app/bundles/CategoryBundle/Controller/Api/CategoryApiController.php:54-75 @7.x]
82. The admin menu entry is under Settings and needs `category:categories:view`. [code: app/bundles/CategoryBundle/Config/config.php:41-52 @7.x]
83. Delete guard: `CATEGORY_PRE_DELETE` collects usage, and `FormModel::deleteEntity` throws `DeleteEntityDependencyException`. The flash `mautic.category.is_in_use.delete` names the users (e.g. "Stage Id: N"). A batch delete skips Categories in use and deletes the rest. [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:90-102 @7.x] [code: app/bundles/CategoryBundle/Model/CategoryModel.php:197-223 @7.x] [code: app/bundles/CoreBundle/Model/FormModel.php:298-345 @7.x]
84. The guard checks only the class registered for the Category's bundle, or every registered class for `global`. References from unregistered classes do not block deletion: Trigger, Webhook, Notification, PointInsight, Tweet, and Contacts through `lead_categories`. Deleting then sets their `category_id` to NULL (FK `SET NULL`) and removes `lead_categories` rows (FK `CASCADE`). [code: app/bundles/CategoryBundle/Event/CategoryTypeEntityEvent.php:21-28 @7.x] [code: app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php:198-208 @7.x] [code: app/bundles/LeadBundle/Entity/LeadCategory.php:84-86 @7.x]
85. An unpublished Category makes all its entities count as unpublished. [code: app/bundles/CoreBundle/Entity/FormEntity.php:239-244 @7.x]
86. Category create, update and delete are audit-logged (`bundle=category, object=category`). [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:57-88 @7.x]
87. Edit locking applies to Categories. Opening a locked Category returns JSON `closeModal` with an error flash. [code: app/bundles/CategoryBundle/Controller/CategoryController.php:306-314,370 @7.x]
88. Contact Categories: the contact bulk "Change categories" button (on `mautic_contact_*` routes) opens a modal that adds or removes `global` Categories. It skips Contacts the User cannot edit and lists at most 300 Categories. [code: app/bundles/CategoryBundle/EventListener/ButtonSubscriber.php:20-45 @7.x] [code: app/bundles/CategoryBundle/Controller/BatchContactController.php:32-91 @7.x] [code: app/bundles/CategoryBundle/Model/ContactActionModel.php:14-40 @7.x]
89. Contacts can also subscribe to Categories in the Preference Center. Contact Categories can be used in Segment and Dynamic Content filters. [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html#using-categories-for-contacts]
90. `lead_categories` rows carry `manually_added` and `manually_removed` flags. [code: app/bundles/LeadBundle/Entity/LeadCategory.php:79-99 @7.x]
91. The legacy API is `/api/categories` (GET, list, new, edit, delete), and `?bundle=` filtering works on the list. The API Platform `/api/v2/categories` `GetCollection` has no security expression. [code: app/bundles/CategoryBundle/Controller/Api/CategoryApiController.php:80-83 @7.x] [code: app/bundles/CategoryBundle/Entity/Category.php:23-31 @7.x]
92. To assign a Category through any entity's API, send `category: <ID>`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/categories.html#assign-a-category]

---

## C. Projects

A Project is a named grouping of entities of many types for one initiative. `ProjectBundle` is new in 7.x.

93. A Project needs a non-blank, unique `name`. The `UniqueName` validator gives `project.name.already.exists` ("A project with this name already exists."), and the DB unique index `unique_project_name` backs it. Description is optional. `properties` (JSON) is API-only. [code: app/bundles/ProjectBundle/Entity/Project.php:84-118 @7.x] [code: app/bundles/ProjectBundle/Validator/Constraints/UniqueNameValidator.php:20-43 @7.x] [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#creating-projects]
94. Fourteen entity types are project-aware, each with an xref table: Asset, Campaign, Message, DynamicContent, Email, Form, Company, LeadList (Segment), Page, Point, Trigger, Sms, Stage and Focus. [code: app/bundles/ProjectBundle/Entity/ProjectTrait.php:24-37 @7.x]
95. Membership is owned by the member entity. Saving an entity with `projects` selected writes xref rows, and changes are recorded as `changes['projects']['added'|'removed']`. [code: app/bundles/ProjectBundle/Entity/ProjectTrait.php:48-72 @7.x]
96. Both xref foreign keys cascade. Deleting a Project removes its xref rows, and deleting a member entity removes that entity's rows. [code: app/bundles/ProjectBundle/Entity/ProjectTrait.php:24-37 @7.x]
97. Permissions are `project:project:view(4) associate(8) edit(16) create(32) delete(128) full(1024)`; there is no publish permission. [code: app/bundles/ProjectBundle/Security/Permissions/ProjectPermissions.php:15-36 @7.x] [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#permissions]
98. The `projects` field on entity forms (`ProjectType`, sorted by name) is disabled without `project:project:associate`. [code: app/bundles/ProjectBundle/Form/Type/ProjectType.php:24-53 @7.x]
99. With `project:project:create`, typing a name and pressing Enter calls `project:addProjects`. That creates the missing Projects, reusing an existing one with the same trimmed name, and returns HTML-escaped `<option>`s. [code: app/bundles/ProjectBundle/Controller/AjaxController.php:52-95 @7.x] [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#assigning-entities-to-a-project]
100. The menu entry is top-level (priority 1) and needs `project:project:view`. [code: app/bundles/ProjectBundle/Config/config.php:27-37 @7.x]
101. The Project list shows `entitiesCount`, the members counted across the types the User can view, and sorts by name or date. [code: app/bundles/ProjectBundle/Controller/ProjectController.php:81-88 @7.x]
102. Entity types are discovered at runtime from Doctrine metadata (any ManyToMany to `Project`) and sorted by label. Each type is shown only if the User has `viewown|viewother` (list and view) or `editown|editother` (add and remove) on that entity's own permission base. [code: app/bundles/ProjectBundle/Service/ProjectEntityLoaderService.php:72-85,153-243 @7.x]
103. The Project view lists members by type, ordered by `dateModified DESC`. Detail links go to `mautic_<type>_action` with `view`; Points and Stages link to `edit`. [code: app/bundles/ProjectBundle/Service/ProjectEntityLoaderService.php:41-65 @7.x] [code: app/bundles/ProjectBundle/Event/EntityTypeDetailRouteEvent.php:17-30 @7.x]
104. The Add button opens `addEntity` directly when exactly one type is editable, and `selectEntityType` otherwise. [code: app/bundles/ProjectBundle/Resources/views/Project/details.html.twig:23-33 @7.x] [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#assigning-entities-to-a-project]
105. `addEntity` needs `edit`. Its lookup leaves out existing members and returns up to 1000 rows. The POST adds only entities that are not yet members and flashes the count (or "no entities added"). An unknown or non-editable type gives a bad-request flash. [code: app/bundles/ProjectBundle/Controller/ProjectController.php:511-645 @7.x] [code: app/bundles/ProjectBundle/Service/ProjectEntityLoaderService.php:92-148 @7.x]
106. `remove` needs `edit`. It calls `removeProject()` on the member and flushes directly, so the member's model save events and audit log are bypassed. [code: app/bundles/ProjectBundle/Controller/ProjectController.php:657-737 @7.x]
107. Deleting a Project has no dependency check, and member entities are untouched. The batch-delete catch for `ForeignKeyConstraintViolationException` flashes `mautic.project.error.cannotbedeleted`. [code: app/bundles/ProjectBundle/Controller/ProjectController.php:375-418,457-470 @7.x] [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#deleting-projects]
108. `project:"Name"` and `!project:"Name"` filter member lists and legacy API lists through the xref table by exact name. No match gives `IN (0)`, an empty result. [code: app/bundles/ProjectBundle/Entity/ProjectRepositoryTrait.php:14-36 @7.x] [code: app/bundles/AssetBundle/Entity/AssetRepository.php:122-132 @7.x]
109. Legacy API responses for the 14 entities include `projects: [{id, name}]` (serializer group `projectList`). [code: app/bundles/ProjectBundle/EventListener/ApiSubscriber.php:34-57 @7.x]
110. Legacy `/api/projects` (7.x after 7.2.1, unreleased; [PR #15569]) supports get, list, new, edit, delete and batch, despite `'methods' => 'GET'` in the config. `/api/v2/projects` supports GET, POST, PUT, PATCH and DELETE. [code: app/bundles/ProjectBundle/Config/config.php:18-24 @7.x] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:186-200 @7.x]
111. Project names and descriptions are HTML-escaped in the chip popover and in AJAX options (XSS regression tests). [code: app/bundles/ProjectBundle/Controller/AjaxController.php:75-78 @7.x]
112. Project edit uses the standard lock and unlock flow; a missing id gives a not-found flash. No project-specific save or delete events exist. [code: app/bundles/ProjectBundle/Controller/ProjectController.php:199-298 @7.x] [code: app/bundles/ProjectBundle/Model/ProjectModel.php:18-85 @7.x]

---

## D. Docs-vs-code discrepancies and open questions
- **Category delete.** The docs and the confirm text say items become uncategorized. In code, deletion is refused while a registered entity uses the Category, and only unregistered references are nulled. [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:90-102 @7.x] [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html#deleting-categories]
- **Asset Alias field.** The docs list one; the 7.2.1 form has none. [code: app/bundles/AssetBundle/Form/Type/AssetType.php @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#uploading-an-asset]
- **Download URL format.** The docs show `/asset/{id}:{name}?utm_...` including `utm_id`. Code generates `/asset/{uuid}` and does not store `utm_id`. [code: app/bundles/AssetBundle/Model/AssetModel.php:120-124,420-438 @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#add-utm-codes-to-asset]
- **`?stream=1`.** The docs say it opens the file in a new tab. In code, `stream=1` overrides only for non-streamed extensions, by forcing inline. [code: app/bundles/AssetBundle/Controller/PublicController.php:148-158 @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#viewing-an-asset]
- **Batch ZIP.** The docs describe it only in 8.0, but it is on the 7.x branch after 7.2.1 (unreleased; [PR #15609]) and is not yet on 8.x. [code: app/bundles/AssetBundle/Service/ArchiveBuilder.php:13 @7.x] [docs: https://docs.mautic.org/en/8.0/components/assets.html#downloading-multiple-assets]
- **Category types.** The docs list Assets, Campaigns, Emails, Focus Items, Forms, Pages, Points, Social Monitoring and Stages. Code also registers Segments, Marketing Messages, Dynamic Content and SMS. [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html]
- **Category API list.** The devdocs call it "List Contact Categories" and say "This list isn't filterable", but `?bundle=` works and every bundle is returned. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/categories.html#list-contact-categories]
- **Project types.** The docs list 13 types; code has 14, adding Point Triggers. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html]
- **Unpublished download status.** The code-analysis input said 401. The response is Access Denied (403 asserted in the test), while the tracked row keeps `code=401`. [code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:105-113 @7.x]
- **Open questions:**
  - `sms` category type registered with a `null` class may break `getUsage()`. [unverified]
  - `messages:categories:*` permission existence. [unverified]
  - `project:projects:*` (API Platform) vs `project:project:*` (permission class). [unverified]
  - Email-attachment downloads without `asset_id`. [code: app/bundles/AssetBundle/Model/AssetModel.php:253-257 @7.x]
