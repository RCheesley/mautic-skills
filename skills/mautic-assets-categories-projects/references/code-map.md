# Code map — Assets, Categories, Projects (7.x)

Paths are relative to the repo root. None of the three bundles defines console commands. [code: app/bundles/AssetBundle/ @7.x]

## 1. Entities and tables

### Asset — `assets` (`app/bundles/AssetBundle/Entity/Asset.php`)
- Base classes: extends `FormEntity` and uses `UuidTrait` and `ProjectTrait`. [code: app/bundles/AssetBundle/Entity/Asset.php:51-55 @7.x]
- Index: `asset_alias_search(alias)`. [code: app/bundles/AssetBundle/Entity/Asset.php:228-230 @7.x]
- Columns: `id`, `title`, `description`, `alias`, `storage_location`, `path`, `remote_path` (TEXT), `original_file_name`, `lang`, `publish_up`, `publish_down`, `download_count`, `unique_download_count`, `revision`, `category_id` (FK SET NULL), `extension`, `mime`, `size`, `disallow`, `uuid`, plus the FormEntity columns. [code: app/bundles/AssetBundle/Entity/Asset.php:232-293 @7.x]
- Project xref: `asset_projects_xref(asset_id, project_id)`. [code: app/bundles/AssetBundle/Entity/Asset.php:293 @7.x]
- Transient fields: `file`, `uploadDir`, `maxSize`, `temp`, `tempId`, `tempName`, `downloadUrl`. [code: app/bundles/AssetBundle/Entity/Asset.php:105-139,211 @7.x]
- API: API Platform operations are gated on `asset:assets:*`. Serializer groups are `assetDetails` and `assetList`. [code: app/bundles/AssetBundle/Entity/Asset.php:32-50,304-335 @7.x]

### Download — `asset_downloads` (`app/bundles/AssetBundle/Entity/Download.php`)
- Id: bigint. [code: app/bundles/AssetBundle/Entity/Download.php:115 @7.x]
- Indexes: `download_tracking_search(tracking_id)`, `download_source_search(source, source_id)` and `asset_date_download(date_download)`. [code: app/bundles/AssetBundle/Entity/Download.php:111-113 @7.x]
- Columns:
  - `date_download`;
  - `asset_id` (FK CASCADE, ownership parent);
  - `ip_id`;
  - `lead_id` (FK SET NULL);
  - `code` (HTTP status 200, 401 or 404);
  - `referer`, `tracking_id`, `source`, `source_id`;
  - `email_id` (FK SET NULL);
  - `utm_campaign`, `utm_content`, `utm_medium`, `utm_source`, `utm_term`.

  [code: app/bundles/AssetBundle/Entity/Download.php:121-176 @7.x]
- API: API Platform access is read-only. [code: app/bundles/AssetBundle/Entity/Download.php:16-30 @7.x]

### Category — `categories` (`app/bundles/CategoryBundle/Entity/Category.php`)
- Columns: `id`, `title`, `description`, `alias` (NOT NULL), `color` (7 characters), `bundle` (50 characters, NOT NULL), `uuid`, plus the FormEntity columns. [code: app/bundles/CategoryBundle/Entity/Category.php:87-104 @7.x]
- Index: `category_alias_search(alias)`. [code: app/bundles/CategoryBundle/Entity/Category.php:87-89 @7.x]
- There is no unique constraint on `(bundle, alias)`. [code: app/bundles/CategoryBundle/Model/CategoryModel.php:67-92 @7.x]
- Contact membership is stored in `lead_categories` (LeadBundle). Its FKs cascade on `category_id` and `lead_id`, and each row has `manually_added` and `manually_removed` flags. [code: app/bundles/LeadBundle/Entity/LeadCategory.php:79-99 @7.x]

### Project — `projects` (`app/bundles/ProjectBundle/Entity/Project.php`)
- Columns: `id`, `name` (unique index `unique_project_name`), `description`, `properties` (JSON), `uuid`, plus the FormEntity columns. [code: app/bundles/ProjectBundle/Entity/Project.php:82-90 @7.x]

### Category types and project-aware entities
`addCategory()` creates a ManyToOne `category_id` with FK SET NULL. [code: app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php:198-208 @7.x]

Category types are registered under `config['categories']`; the `global` type covers all of them. [code: app/bundles/CategoryBundle/Event/CategoryTypesEvent.php:20-33 @7.x]

| Entity | Category type (config key) | Project xref table / column |
|---|---|---|
| Asset | `asset` | `asset_projects_xref` / `asset_id` |
| Campaign | `campaign` | `campaign_projects_xref` / `campaign_id` |
| ChannelBundle Message | `messages` | `message_projects_xref` / `message_id` |
| DynamicContent | `dynamicContent` | `dynamic_content_projects_xref` / `dynamic_content_id` |
| Email | `email` | `email_projects_xref` / `email_id` |
| Form | `form` | `form_projects_xref` / `form_id` |
| Company | — | `company_projects_xref` / `company_id` |
| LeadList (Segment) | `segment` | `lead_list_projects_xref` / `leadlist_id` |
| Page | `page` | `page_projects_xref` / `page_id` |
| Point | `point` | `point_projects_xref` / `point_id` |
| Point Trigger | (column only) | `point_trigger_projects_xref` / `point_trigger_id` |
| Sms | `sms` (class `null`) | `sms_projects_xref` / `sms_id` |
| Stage | `stage` | `stage_projects_xref` / `stage_id` |
| Focus (plugin) | `plugin:focus` | `focus_projects_xref` / `focus_id` |
| Social Monitoring (plugin) | `plugin:mauticSocial` | — |
| Notification, Webhook, PointInsight, Tweet | `category_id` column only | — |

[code: app/bundles/ProjectBundle/Entity/ProjectTrait.php:24-37 @7.x] [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:41-52 @7.x] [code: app/bundles/SmsBundle/Config/config.php:67 @7.x]

## 2. Models and services

### Assets
- `app/bundles/AssetBundle/Model/AssetModel.php` (alias `mautic.asset.model.asset`):
  - `saveEntity` (`:83-93`);
  - `trackDownload` (`:101-284`);
  - `upDownloadCount` (`:292-297`);
  - `generateUrl` (`:420-438`);
  - `getMaxUploadSize` (`:448-464`);
  - `getEntityBySlugs` (`:637-655`).

  [code: app/bundles/AssetBundle/Config/services.php:35 @7.x]
- `AssetBundle/Entity/AssetRepository.php`:
  - search commands (`:85-168`);
  - `getLatestAssetForCategory` (`:228-238`);
  - `findOneByUuid` (`:246-259`).

  [code: app/bundles/AssetBundle/Entity/AssetRepository.php:85-259 @7.x]
- `AssetBundle/Entity/DownloadRepository.php`:
  - `isUniqueDownload` (`:22-43`);
  - `getLeadDownloads` (`:52-70`);
  - A/B helpers (`:142-222`);
  - `updateLeadByTrackingId` and `updateLead` (`:224-250`).

  [code: app/bundles/AssetBundle/Entity/DownloadRepository.php:22-250 @7.x]
- `AssetBundle/Helper/TokenHelper.php`: `REGEX = '/{assetlink=(.*?)}/'`. [code: app/bundles/AssetBundle/Helper/TokenHelper.php:9 @7.x]
- `AssetBundle/Helper/PointActionHelper.php`. [code: app/bundles/AssetBundle/Helper/PointActionHelper.php:7-14 @7.x]
- Batch ZIP:
  - `Service/BatchDownloadRequestValidator.php`: `MAX_ASSETS_PER_REQUEST = 100`, CSRF id `mautic_asset_batch_download`;
  - `Service/BatchFileCollector.php`;
  - `Service/ArchiveBuilder.php`: `MAX_TOTAL_ASSET_SIZE_BYTES` = 500 MiB;
  - `Service/BatchDownloadResponder.php`.

  [code: app/bundles/AssetBundle/Service/BatchDownloadRequestValidator.php:15-17 @7.x] [code: app/bundles/AssetBundle/Service/ArchiveBuilder.php:13 @7.x]
- Upload:
  - `Controller/UploadController.php`, which replaces OneupUploader's Dropzone controller through `oneup_uploader.controller.dropzone.class`;
  - `EventListener/UploadSubscriber.php`;
  - `Validator/Constraints/UploadValidator.php`;
  - `ErrorHandler/DropzoneErrorHandler.php`.

  [code: app/bundles/AssetBundle/Config/services.php:10-32 @7.x]

### Categories
- `app/bundles/CategoryBundle/Model/CategoryModel.php` (alias `mautic.category.model.category`):
  - `getPermissionBase` (`:54-65`);
  - `saveEntity` alias logic (`:67-92`);
  - `getLookupResults` (`:168-192`);
  - `getUsage` (`:197-223`).

  [code: app/bundles/CategoryBundle/Model/CategoryModel.php:23-223 @7.x]
- `CategoryBundle/Model/ContactActionModel.php`. [code: app/bundles/CategoryBundle/Model/ContactActionModel.php:14-40 @7.x]
- `CategoryBundle/Entity/CategoryRepository.php`: `getCategoryList` (`:37-77`) and `checkUniqueCategoryAlias` (`:152-169`). [code: app/bundles/CategoryBundle/Entity/CategoryRepository.php:37-169 @7.x]
- Form types: `Form/Type/CategoryListType.php` (the picker), `CategoryType.php`, `CategoryBundlesType.php`. [code: app/bundles/CategoryBundle/Form/Type/CategoryListType.php:30-84 @7.x]

### Projects
- `app/bundles/ProjectBundle/Model/ProjectModel.php` is final, with permission base `project:project`. [code: app/bundles/ProjectBundle/Model/ProjectModel.php:18,82-85 @7.x]
- `ProjectBundle/Service/ProjectEntityLoaderService.php` handles discovery, permission filtering, member lists and lookups. [code: app/bundles/ProjectBundle/Service/ProjectEntityLoaderService.php:41-316 @7.x]
- `ProjectBundle/Entity/ProjectRepositoryTrait.php::handleProjectFilter`. [code: app/bundles/ProjectBundle/Entity/ProjectRepositoryTrait.php:14-36 @7.x]
- `ProjectBundle/Form/Type/ProjectType.php` and `Assets/js/project-select-box.js`. [code: app/bundles/ProjectBundle/Form/Type/ProjectType.php:24-53 @7.x]

## 3. Events

| Constant / class | Name | Dispatched | Core listeners |
|---|---|---|---|
| `AssetEvents::ASSET_ON_LOAD` | `mautic.asset_on_load` | `AssetModel.php:267-270` | Campaign and Point subscribers |
| `AssetEvents::ASSET_ON_REMOTE_BROWSE` | `mautic.asset_on_remote_browse` | `AjaxController.php:57-58` | CloudStorage `RemoteAssetBrowseSubscriber` |
| `AssetEvents::ASSET_ON_UPLOAD` | `mautic.asset_on_upload` | never | — |
| `ASSET_PRE/POST_SAVE`, `ASSET_PRE/POST_DELETE` | `mautic.asset_*` | `FormModel` save/delete | `AssetSubscriber` (audit log, `removeUpload`) |
| `AssetEvents::ON_CAMPAIGN_TRIGGER_DECISION` | `mautic.asset.on_campaign_trigger_decision` | campaign executioner | `CampaignSubscriber` |
| `AssetEvents::ON_DETERMINE_DOWNLOAD_RATE_WINNER` | `mautic.asset.on_download_rate_winner` | A/B winner | `DetermineWinnerSubscriber` |
| `AssetExportListEvent` (class) | — | `CampaignController.php:215,339,442` | `AssetExportListEventSubscriber` |
| `CategoryEvents::CATEGORY_PRE/POST_SAVE` | `mautic.category_*` | `CategoryModel.php:125-160` | audit log |
| `CategoryEvents::CATEGORY_PRE_DELETE` | `mautic.category_pre_delete` | `FormModel.php:302` | usage guard |
| `CategoryEvents::CATEGORY_ON_BUNDLE_LIST_BUILD` | `mautic.category_on_bundle_list_build` | `CategoryController.php:159-163`, `CategoryBundlesType.php:27-29` | config `categories` reader |
| `CategoryTypeEntityEvent` (class) | — | `CategoryModel::getUsage` | `CategorySubscriber::onCategoryTypeEntity` |
| `EntityTypeDetailRouteEvent`, `EntityTypeNormalizationEvent`, `EntityTypeModelMappingEvent` (classes) | — | `ProjectEntityLoaderService` | Point and Stage detail routes |

[code: app/bundles/AssetBundle/AssetEvents.php:20-100 @7.x] [code: app/bundles/CategoryBundle/CategoryEvents.php:20-60 @7.x] [code: app/bundles/ProjectBundle/Event/EntityTypeDetailRouteEvent.php:17-30 @7.x]

AssetBundle also subscribes to events from other bundles:
- Campaign, Form and Point build events;
- Email and Page build/send/display;
- Lead timeline, contact change and merge;
- Report, Global search, Config and Dashboard;
- OneupUploader `POST_UPLOAD` and `VALIDATION`.

[code: app/bundles/AssetBundle/EventListener/UploadSubscriber.php:25-31 @7.x] [code: app/bundles/AssetBundle/EventListener/BuilderSubscriber.php:29-37 @7.x]

## 4. Routes

| Name | Path | Controller |
|---|---|---|
| `mautic_asset_index` | `/s/assets/{page}` | `AssetController::indexAction` |
| `mautic_asset_remote` | `/s/assets/remote` | `AssetController::remoteAction` |
| `mautic_asset_action` | `/s/assets/{objectAction}/{objectId}` | `AssetController::executeAction` (actions: new, edit, view, clone, delete, batchDelete, preview, batchDownload) |
| `mautic_asset_download` | `/asset/{slug}` (public) | `PublicController::downloadAction` |
| `mautic_api_assetsstandard` | `/api/assets...` | `Api/AssetApiController` |
| `mautic_category_index` | `/s/categories/{bundle}/{page}` | `CategoryController::indexAction` |
| `mautic_category_action` | `/s/categories/{bundle}/{objectAction}/{objectId}` | `CategoryController::executeCategoryAction` |
| `mautic_category_batch_contact_set` / `_view` | `/s/categories/batch/contact/set` / `view` | `BatchContactController` |
| `mautic_api_categoriesstandard` | `/api/categories...` | `Api/CategoryApiController` |
| `mautic_project_index` | `/s/projects/{page}` | `ProjectController::indexAction` |
| `mautic_project_action` | `/s/projects/{objectAction}/{objectId}` | `ProjectController::executeAction` (actions: new, edit, view, delete, batchDelete, selectEntityType, addEntity, remove) |
| `mautic_api_projectsstandard` | `/api/projects...` | `Api/ProjectApiController` |

[code: app/bundles/AssetBundle/Config/config.php:8-36 @7.x] [code: app/bundles/CategoryBundle/Config/config.php:8-38 @7.x] [code: app/bundles/ProjectBundle/Config/config.php:8-24 @7.x]

AJAX endpoints:
- `asset:categoryList` and `asset:fetchRemoteFiles`;
- `category:categoryList`;
- `project:getLookupChoiceList` and `project:addProjects`.

[code: app/bundles/AssetBundle/Controller/AjaxController.php:27-79 @7.x] [code: app/bundles/ProjectBundle/Controller/AjaxController.php:21-82 @7.x]

## 5. Configuration parameters

| Parameter | Default | Notes |
|---|---|---|
| `upload_dir` | `%mautic.application_dir%/media/files` | UI: Asset Settings; temp uploads go to `<upload_dir>/tmp/<tempId>/` |
| `max_size` | `'6'` (MB) | UI; `-1` or `0` means unlimited |
| `allowed_extensions` | csv, doc, docx, epub, gif, jpg, jpeg, mpg, mpeg, mp3, odt, odp, ods, pdf, png, ppt, pptx, tif, tiff, txt, xls, xlsx, wav | UI (comma-separated) |
| `streamed_extensions` | gif, jpg, jpeg, mpg, mpeg, mp3, pdf, png, wav | `local.php` only |
| `default_assetlimit` | falls back to `default_pagelimit` | marked for removal in 8 |
| `validate_remote_domains` | false (per docs) | `local.php`; see docs digest |

[code: app/bundles/AssetBundle/Config/config.php:59-64 @7.x] [code: app/bundles/AssetBundle/Form/Type/ConfigType.php:18-65 @7.x] [code: app/bundles/AssetBundle/Controller/AssetController.php:59-63 @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#using-remote-assets]

## 6. Permissions

| Class | Permissions |
|---|---|
| `AssetBundle/Security/Permissions/AssetPermissions.php` | `asset:assets:{viewown,viewother,editown,editother,create,deleteown,deleteother,publishown,publishother,full}`, `asset:categories:{view,edit,create,delete,publish,full}` |
| `CategoryBundle/Security/Permissions/CategoryPermissions.php` | `category:categories:{view,edit,create,delete,publish,full}` (for `global` and the generic screens) |
| `ProjectBundle/Security/Permissions/ProjectPermissions.php` | `project:project:{view(4),associate(8),edit(16),create(32),delete(128),full(1024)}` |

[code: app/bundles/AssetBundle/Security/Permissions/AssetPermissions.php:18-25 @7.x] [code: app/bundles/CategoryBundle/Security/Permissions/CategoryPermissions.php:13-18 @7.x] [code: app/bundles/ProjectBundle/Security/Permissions/ProjectPermissions.php:15-36 @7.x]

## 7. Cloud storage plugin
- `plugins/MauticCloudStorageBundle/Integration/CloudStorageIntegration.php`: abstract, auth type `api`, feature `cloud_storage`. [code: plugins/MauticCloudStorageBundle/Integration/CloudStorageIntegration.php:9-68 @7.x]
- `Integration/AmazonS3Integration.php`: name `AmazonS3`, Gaufrette `AwsS3` adapter. [code: plugins/MauticCloudStorageBundle/Integration/AmazonS3Integration.php:20-137 @7.x]
- `EventListener/RemoteAssetBrowseSubscriber.php`. [code: plugins/MauticCloudStorageBundle/EventListener/RemoteAssetBrowseSubscriber.php:13-33 @7.x]
- The OpenStack and Rackspace images and keys are leftovers; no integration class exists for them. [code: plugins/MauticCloudStorageBundle/Config/services.php:20-21 @7.x]

## 8. Templates and JS
- AssetBundle templates: `app/bundles/AssetBundle/Resources/views/Asset/{list,form,details}.html.twig`, `Remote/{browse,list}.html.twig`, `Action/asset.html.twig`.
- AssetBundle JS: `Assets/js/asset.js`, with `Mautic.batchAssetDownload` and `Mautic.initializeDropzone`.

  [code: app/bundles/AssetBundle/Assets/js/asset.js:14-20,88,100 @7.x]
- CategoryBundle templates: `app/bundles/CategoryBundle/Resources/views/Category/{list,form}.html.twig`.
- ProjectBundle templates: `app/bundles/ProjectBundle/Resources/views/Project/{list,form,details,_entity_list,add_entity_modal,select_entity_type_modal}.html.twig`, `Modules/projects.html.twig`.

  [code: app/bundles/ProjectBundle/Resources/views/Project/_entity_list.html.twig:15-64 @7.x]

## 9. Tests (directories)
- `app/bundles/AssetBundle/Tests/{Asset,Controller,Entity,EventListener,Functional,Model,Unit}` and `RemoteFileServerTrait.php`.
- `app/bundles/CategoryBundle/Tests/{Controller,Entity,Model}`.
- `app/bundles/ProjectBundle/Tests/Functional/{Controller,Validator}` and `AbstractProjectSearchTestCase.php`.
- MauticCloudStorageBundle has no tests.

See test-patterns.md. [code: app/bundles/AssetBundle/Tests/Asset/AbstractAssetTestCase.php:14 @7.x]
