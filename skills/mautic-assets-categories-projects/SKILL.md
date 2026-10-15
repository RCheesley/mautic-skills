---
name: mautic-assets-categories-projects
description: "Mautic Assets, Categories and Projects. Assets: downloadable files (local uploads, remote URLs, Amazon S3 via MauticCloudStorageBundle), the tracked download URL /asset/{slug}, download and unique-download tracking, upload limits and allowed extensions, batch ZIP download, the {assetlink=ID} token, the 'Download an Asset' form action and asset campaign/point triggers. Categories: bundle-scoped and global categories, inline creation, category permissions, the in-use delete guard, Contact category subscriptions. Projects (new in 7.x): cross-type groupings, *_projects_xref tables, the Associate permission and project search. Use whenever a task mentions assets, asset downloads, file uploads, download counts, S3 or cloud storage, categories, global categories, lead categories, projects, /api/assets, /api/categories or /api/projects, or touches app/bundles/AssetBundle/, app/bundles/CategoryBundle/, app/bundles/ProjectBundle/ or plugins/MauticCloudStorageBundle/."
---
# Mautic Assets, Categories and Projects

## Scope
An Asset is a downloadable file that Mautic hosts locally or references by URL; every public download through `/asset/{slug}` is tracked against the Contact (the person record, code name `Lead`) and can fire campaign decisions, point actions and form actions. A Category is a label from one shared `categories` table, scoped to one component ("bundle") or `global`; a Project (new in 7.x) is a named grouping that spans fourteen entity types. Out of scope: segment filters on contact categories (mautic-segments), the Preference Center UI (mautic-contacts), the email `assetAttachments` sending logic (mautic-emails), the Role editor (mautic-users-and-permissions) and the generic API framework (mautic-rest-api).

## Expected behaviour (essentials)

### Assets
- A new Asset defaults to `storageLocation=local`, language `en`, `revision=1`, zero download counters and `disallow=true` (send `X-Robots-Tag`). [code: app/bundles/AssetBundle/Entity/Asset.php:81,151,169,175,181,217 @7.x]
- A local upload is two-step: Dropzone posts the file to the OneupUploader `asset` endpoint, which validates it and parks it in `<upload_dir>/tmp/<tempId>/`; saving the Asset form moves it to `<upload_dir>/<sha1>.<ext>`. [code: app/bundles/AssetBundle/EventListener/UploadSubscriber.php:37-53 @7.x] [code: app/bundles/AssetBundle/Entity/Asset.php:667-721 @7.x]
- The upload endpoint rejects, in order: files over the effective size limit, extensions not in `allowed_extensions`, and files whose client or detected MIME type does not match the extension. [code: app/bundles/AssetBundle/EventListener/UploadSubscriber.php:60-92 @7.x]
- The effective upload limit is the minimum of `max_size` (MB, default `6`), PHP `post_max_size`, `upload_max_filesize` and `memory_limit`; `-1` or `0` means unlimited. [code: app/bundles/AssetBundle/Model/AssetModel.php:448-464 @7.x] [code: app/bundles/AssetBundle/Config/config.php:59-64 @7.x]
- The size limit is enforced only at the Dropzone endpoint; the legacy API path that references a file already in `upload_dir` gets no size check. [code: app/bundles/AssetBundle/Controller/Api/AssetApiController.php:82-89 @7.x]
- A remote Asset must have a valid URL that passes the `SafeRemoteUrl` (SSRF) constraint, and its MIME type must map to an allowed extension. [code: app/bundles/AssetBundle/Entity/Asset.php:93-97 @7.x] [code: app/bundles/AssetBundle/Validator/Constraints/UploadValidator.php:87-141 @7.x]
- The public URL is `/asset/{uuid}`; the legacy form `/asset/{id}:{alias}` still resolves when the Asset has a non-null alias, and the alias text is not checked. [code: app/bundles/AssetBundle/Entity/Asset.php:1290-1297 @7.x] [code: app/bundles/AssetBundle/Model/AssetModel.php:637-655 @7.x]
- An unpublished Asset is tracked with `code=401` and the visitor gets 403 Access Denied; a logged-in User with view access can still download it. [code: app/bundles/AssetBundle/Controller/PublicController.php:78-101 @7.x]
- A remote Asset download is tracked and answered with a 302 redirect to `remotePath`; Mautic does not proxy it. [code: app/bundles/AssetBundle/Controller/PublicController.php:108-113 @7.x]
- Extensions in `streamed_extensions` (gif, jpg, jpeg, mpg, mpeg, mp3, pdf, png, wav) display inline unless `?stream=0`; other files are sent as attachments named after `originalFileName`. [code: app/bundles/AssetBundle/Controller/PublicController.php:148-158 @7.x]
- Downloads by logged-in Mautic Users are not tracked, and neither are untrackable requests (HEAD, prefetch, DNT, `Sec-GPC: 1`). [code: app/bundles/AssetBundle/Model/AssetModel.php:104-129 @7.x]
- A visitor with no tracking id adds to `download_count` but writes no `asset_downloads` row. [code: app/bundles/AssetBundle/Model/AssetModel.php:177-189,234-251 @7.x]
- A download is unique (and increments `unique_download_count`) when no earlier row exists for the same asset and tracking id, or the tracking cookie was just created. [code: app/bundles/AssetBundle/Model/AssetModel.php:234-257 @7.x]
- `mautic.asset_on_load` fires before the download row is persisted, and the `asset.download` campaign decision and point action run synchronously from it. [code: app/bundles/AssetBundle/Model/AssetModel.php:267-270 @7.x]
- The "Download an Asset" form action serves the chosen Asset, or else the newest published Asset in the chosen Category. It stops later form actions and always adds `&stream=0`. [code: app/bundles/AssetBundle/EventListener/FormSubscriber.php:50-150 @7.x]
- `{assetlink=ID}` in Emails and Landing Pages becomes the tracked public URL; an unknown id becomes an empty string. [code: app/bundles/AssetBundle/Helper/TokenHelper.php:9-33 @7.x]
- Deleting an Asset unlinks the local file and cascade-deletes its `asset_downloads` rows. [code: app/bundles/AssetBundle/EventListener/AssetSubscriber.php:51-66 @7.x] [code: app/bundles/AssetBundle/Entity/Download.php:121-124 @7.x]
- Batch ZIP download (7.x after 7.2.1, unreleased; [PR #15609]): up to 100 local Assets and 500 MiB in total, view permission and a CSRF token are required, and any failure aborts the whole ZIP. [code: app/bundles/AssetBundle/Service/BatchDownloadRequestValidator.php:15-87 @7.x] [code: app/bundles/AssetBundle/Service/ArchiveBuilder.php:13 @7.x]

### Categories
- A Category has a `title` and a `bundle` (type). You choose the type only on the Categories admin screen, and it cannot be changed after creation. [code: app/bundles/CategoryBundle/Form/Type/CategoryType.php:33-59 @7.x]
- Category pickers list only published Categories of the requested bundle plus `global` ones, plus a "Create new category" choice that opens an inline modal. [code: app/bundles/CategoryBundle/Entity/CategoryRepository.php:37-77 @7.x] [code: app/bundles/CategoryBundle/Form/Type/CategoryListType.php:30-84 @7.x]
- Aliases are unique within a bundle only (`alias`, `alias1`, …); the same alias may exist in another bundle. [code: app/bundles/CategoryBundle/Model/CategoryModel.php:67-92 @7.x]
- Deleting a Category that a registered entity class still uses is refused with a flash naming the users (e.g. "Stage Id: 3"); a batch delete skips those Categories and deletes the rest. [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:90-102 @7.x]
- The guard ignores Triggers, Webhooks, Notifications, PointInsights, Tweets and contact memberships. When a Category is deleted, their `category_id` becomes NULL and the `lead_categories` rows are removed. [code: app/bundles/CategoryBundle/Event/CategoryTypeEntityEvent.php:21-28 @7.x] [code: app/bundles/LeadBundle/Entity/LeadCategory.php:84-86 @7.x]
- Permissions are per bundle: `<bundle>:categories:<action>`, with `global` mapping to `category:categories:*`. [code: app/bundles/CategoryBundle/Model/CategoryModel.php:54-65 @7.x]
- An unpublished Category makes every entity in it count as unpublished. [code: app/bundles/CoreBundle/Entity/FormEntity.php:239-244 @7.x]
- The contact bulk action "Change categories" adds or removes `global` Categories only and skips Contacts the User cannot edit. [code: app/bundles/CategoryBundle/Controller/BatchContactController.php:32-91 @7.x] [code: app/bundles/CategoryBundle/Model/ContactActionModel.php:14-40 @7.x]

### Projects
- A Project needs a unique, non-blank `name`; the validator message is "A project with this name already exists." and a DB unique index backs it. [code: app/bundles/ProjectBundle/Entity/Project.php:84,111-118 @7.x] [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#creating-projects]
- Membership is stored on the member entity, in one `<entity>_projects_xref` table per type (14 types). [code: app/bundles/ProjectBundle/Entity/ProjectTrait.php:24-37 @7.x]
- The Projects field on an entity form is disabled without `project:project:associate`. With `create` permission, typing a name and pressing Enter creates the Project inline. [code: app/bundles/ProjectBundle/Form/Type/ProjectType.php:24-53 @7.x]
- The Project screens show a type only when the User may view it (list/view) or edit it (add/remove) through that entity's own `viewown|viewother` or `editown|editother` permissions. [code: app/bundles/ProjectBundle/Service/ProjectEntityLoaderService.php:153-176 @7.x]
- Deleting a Project has no dependency check: the xref rows cascade and the member entities stay. [code: app/bundles/ProjectBundle/Controller/ProjectController.php:375-418 @7.x] [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#deleting-projects]
- `project:"Name"` (and `!project:"Name"`) filters every participating list and legacy API list by exact name; an unknown name returns nothing. [code: app/bundles/ProjectBundle/Entity/ProjectRepositoryTrait.php:14-36 @7.x]
- Projects dispatch no save or delete events, and adding or removing members from the Project screen bypasses the member entity's model save events. [code: app/bundles/ProjectBundle/Controller/ProjectController.php:622-628,720-722 @7.x]

## Where it lives
| Concern | Path(s) |
|---|---|
| Entities / tables | `app/bundles/AssetBundle/Entity/Asset.php` (`assets`), `Download.php` (`asset_downloads`); `app/bundles/CategoryBundle/Entity/Category.php` (`categories`); `app/bundles/LeadBundle/Entity/LeadCategory.php` (`lead_categories`); `app/bundles/ProjectBundle/Entity/Project.php` (`projects`), `ProjectTrait.php` (`*_projects_xref`) |
| Models | `AssetBundle/Model/AssetModel.php` (`trackDownload`, `generateUrl`, `getMaxUploadSize`); `CategoryBundle/Model/CategoryModel.php`, `ContactActionModel.php`; `ProjectBundle/Model/ProjectModel.php`, `Service/ProjectEntityLoaderService.php` |
| Events | `AssetBundle/AssetEvents.php`, `CategoryBundle/CategoryEvents.php`, `ProjectBundle/Event/EntityType*Event.php` |
| Public download | `AssetBundle/Controller/PublicController.php` (`/asset/{slug}`) |
| Upload | `AssetBundle/EventListener/UploadSubscriber.php`, `Controller/UploadController.php`, `Validator/Constraints/UploadValidator.php` |
| Batch ZIP | `AssetBundle/Service/{BatchDownloadRequestValidator,BatchFileCollector,ArchiveBuilder,BatchDownloadResponder}.php` |
| Integrations | `AssetBundle/EventListener/{Campaign,Point,Form,Builder,Email,Page,DetermineWinner,Report,Dashboard,Lead}Subscriber.php` |
| UI routes | `/s/assets/...`, `/s/categories/{bundle}/...`, `/s/projects/...` (each bundle's `Config/config.php`) |
| API | `/api/assets`, `/api/categories`, `/api/projects`; API v2 `/api/v2/{assets,downloads,categories,projects}` |
| Config params | `upload_dir`, `max_size`, `allowed_extensions`, `streamed_extensions` (`AssetBundle/Config/config.php:59-64`) |
| Permissions | `AssetBundle/Security/Permissions/AssetPermissions.php`, `CategoryBundle/.../CategoryPermissions.php`, `ProjectBundle/.../ProjectPermissions.php` |
| Cloud storage | `plugins/MauticCloudStorageBundle/` (Amazon S3 only) |
| Tests | `app/bundles/{AssetBundle,CategoryBundle,ProjectBundle}/Tests/` |

Full detail: references/code-map.md. [code: app/bundles/AssetBundle/Config/config.php:8-64 @7.x] [code: app/bundles/ProjectBundle/Config/config.php:8-37 @7.x]

## How to change or extend it
- React to downloads by subscribing to `AssetEvents::ASSET_ON_LOAD`. The `Download` is not flushed yet, so use `AssetLoadEvent::getRecord()` and `isUnique()` rather than querying. [code: app/bundles/AssetBundle/Model/AssetModel.php:267-270 @7.x]
- Do not listen to `AssetEvents::ASSET_ON_UPLOAD`: it is never dispatched. For extra upload validation (for example virus scanning), subscribe to OneupUploader `UploadEvents::VALIDATION` for mapping `asset`. [code: app/bundles/AssetBundle/AssetEvents.php:40 @7.x] [code: app/bundles/AssetBundle/EventListener/UploadSubscriber.php:25-31 @7.x]
- To add a remote storage provider, subclass `CloudStorageIntegration` (feature `cloud_storage`), return a Gaufrette `Adapter` from `getAdapter()`, and set it on `RemoteAssetBrowseEvent` (or call `setFailed()`). [code: plugins/MauticCloudStorageBundle/Integration/CloudStorageIntegration.php:9-68 @7.x] [code: plugins/MauticCloudStorageBundle/EventListener/RemoteAssetBrowseSubscriber.php:13-33 @7.x]
- To make an entity categorisable: register `'categories' => ['<type>' => ['class' => X::class]]` in its `Config/config.php`, call `$builder->addCategory()`, add `CategoryListType` with `bundle => '<type>'`, and add `addStandardPermissions('categories')` to the bundle's permission class. Without the registration the delete guard cannot see your references. [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:41-52,104-115 @7.x]
- Block a category delete from a plugin with `CategoryEvent::addDependencyError()` on `CATEGORY_PRE_DELETE`. [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:90-102 @7.x]
- To make an entity project-aware:
  - in the entity, `use ProjectTrait`, call `initializeProjects()` and `addProjectsField($builder, '<x>_projects_xref', '<x>_id')`;
  - add the `projects` field (`ProjectType`) to the form;
  - in the repository, `use ProjectRepositoryTrait` and handle `mautic.project.searchcommand.name`;
  - register the class for API output in `ProjectBundle/EventListener/ApiSubscriber`;
  - add a migration that creates the xref table.

  `ProjectEntityLoaderService` discovers the new type automatically. [code: app/bundles/ProjectBundle/Service/ProjectEntityLoaderService.php:181-316 @7.x] [code: app/bundles/ProjectBundle/EventListener/ApiSubscriber.php:34-57 @7.x]
- Change entity, migration, API serializer groups (`assetDetails`/`assetList`, `projectList`), translations and docs together. [code: app/bundles/AssetBundle/Entity/Asset.php:304-335 @7.x]
- On 8.x, subscribe to event classes (`AssetPreSaveEvent::class`, …), not string constants. [PR #17196] [PR #17215]

## How to test it
- Use `Mautic\CoreBundle\Test\MauticMysqlTestCase` for functional tests. Use `AssetBundle/Tests/Asset/AbstractAssetTestCase` (it creates a real file in `upload_dir` plus an `Asset`) for download tests, and `ProjectBundle/Tests/Functional/AbstractProjectSearchTestCase` for project search in each bundle. [code: app/bundles/AssetBundle/Tests/Asset/AbstractAssetTestCase.php:14-93 @7.x] [code: app/bundles/ProjectBundle/Tests/Functional/AbstractProjectSearchTestCase.php:16-68 @7.x]
- Copy from these:
  - `AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php` (stream, slug, unpublished, remote, UTM);
  - `AssetControllerFunctionalTest.php` (upload validation, path traversal, batch ZIP);
  - `UploadControllerFunctionalTest.php`;
  - `CategoryBundle/Tests/Controller/CategoryControllerFunctionalTest.php` (inline modal, in-use guard);
  - `ProjectBundle/Tests/Functional/Controller/ProjectControllerTest.php`.

  [code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:12-155 @7.x]
- A good regression test asserts the HTTP status and headers (`Content-Disposition`, `X-Robots-Tag`) and the persisted `asset_downloads` row with its `code`, `lead_id` and utm fields. For permissions, log in as a non-admin User whose Role is limited to `viewown`. [code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:71-97 @7.x]
- Call `$this->logoutUser()` before testing public downloads: downloads by logged-in Users are not tracked. [code: app/bundles/AssetBundle/Model/AssetModel.php:104-116 @7.x]

Full detail: references/test-patterns.md.

## Version notes
- Projects (`ProjectBundle`) are new in 7.x; their migrations are dated April–June 2025. [code: app/migrations/Version20250409150440.php @7.x]
- Batch ZIP download is on the 7.x branch after 7.2.1 (not yet released; [PR #15609]) and not yet on 8.x (it arrives with the next forward merge); the 8.0 docs describe it as new. [code: app/bundles/AssetBundle/Service/ArchiveBuilder.php:13 @7.x] [docs: https://docs.mautic.org/en/8.0/components/assets.html#downloading-multiple-assets]
- 8.x dispatches Asset CRUD events by class (`AssetPreSaveEvent`, `AssetPostSaveEvent`, `AssetPreDeleteEvent`, `AssetPostDeleteEvent`) and drops `ASSET_ON_UPLOAD` and service `mautic.asset.upload.error.handler`. [PR #17196] [PR #17215]
- 8.x: `CATEGORY_ON_BUNDLE_LIST_BUILD` is dispatched as `CategoryTypesEvent` (constant kept); `CategoryModel` CRUD events still use string names; duplicate `CATEGORY_*` constants are removed from `DynamicContentEvents`. [PR #17217] [PR #17097]
- 8.x fixes an asset upload size validation that was off by 1000×. [PR #17080]
- The `default_assetlimit` parameter is marked for removal in Mautic 8. [code: app/bundles/AssetBundle/Controller/AssetController.php:59-63 @7.x]
- 5.0 serves public links inline only for `streamed_extensions` and stores UTM fields on downloads; 5.1 turns "Block search engines" on for new Assets. [PR #11474] [PR #12098] [PR #13531]
- 5.2.7 makes upload validation honour the configured `allowed_extensions`. [PR #15111]
- 6.0 refuses to delete a Category that registered entities use. [PR #14567]
- 6.0.0 removed the Category Apply button; 6.0.1 to 6.0.9 restore it (revert [PR #14819]), while 7.x keeps it removed. [PR #14680]
- Before 7.1 the download URL is `/asset/{id}:{alias}` and bare `/asset/{id}` was not blocked; 7.1 adds UUID URLs. [PR #15138] [PR #15776]
- Before 7.2 remote Assets are not MIME-checked and `allowed_mimetypes` exists; 7.2 removes it. [PR #16045]

Full detail: references/version-notes.md.

## Pitfalls
- The unpublished-download test asserts 403, but the stored download row has `code=401`. Do not "fix" either one to match the other. [code: app/bundles/AssetBundle/Controller/PublicController.php:78-82 @7.x] [code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:105-113 @7.x]
- Email-attachment download entries (`MailHelper::createAssetDownloadEntries`) are written without `asset_id`, so reports that join on the asset miss them. This may be a long-standing bug. [code: app/bundles/AssetBundle/Model/AssetModel.php:253-257 @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php:1581-1613 @7.x]
- The whole local file is read into memory on download (`file_get_contents`), so `memory_limit` caps the practical Asset size. [code: app/bundles/AssetBundle/Controller/PublicController.php:131-142 @7.x]
- Docs list an "Alias" field on the Asset form, but `AssetType` has none and nothing sets `alias` on new Assets. [code: app/bundles/AssetBundle/Form/Type/AssetType.php @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#uploading-an-asset]
- Docs (and the confirm dialog text) say a deleted Category's items "will be assigned as uncategorized", but core refuses to delete a Category that a registered entity uses. [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:90-102 @7.x] [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html#deleting-categories]
- Docs show `utm_id` on asset URLs, but only `utm_campaign`, `utm_content`, `utm_medium`, `utm_source` and `utm_term` are stored on the download. [code: app/bundles/AssetBundle/Model/AssetModel.php:120-124 @7.x] [docs: https://docs.mautic.org/en/7.2/components/assets.html#add-utm-codes-to-asset]
- The `sms` category type is registered with a `null` class. Deleting an in-use SMS Category may then error inside `getUsage()`. [unverified] [code: app/bundles/SmsBundle/Config/config.php:67 @7.x]
- `ProjectPermissions` defines `project:project:*`, but API Platform attributes check `project:projects:*`; whether the plural resolves for non-admins is untested. [unverified] [code: app/bundles/ProjectBundle/Entity/Project.php:28-33 @7.x]
- Legacy `/api/projects` is on the 7.x branch after 7.2.1, unreleased ([PR #15569]; 7.2.1 has only `/api/v2/projects`). Its config says `'methods' => 'GET'`, but the route generator ignores that key, so full CRUD exists. [code: app/bundles/ProjectBundle/Config/config.php:18-24 @7.x] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:186-200 @7.x]
- The project batch-delete error flash says "Only projects without any contacts can be deleted.", although Projects have no contact relation. [code: app/bundles/ProjectBundle/Controller/ProjectController.php:457-470 @7.x]
- The "Download an Asset" form action does nothing when the chosen Category has no published Asset (`NoResultException` is swallowed). [code: app/bundles/AssetBundle/EventListener/FormSubscriber.php:76-82 @7.x]
- Docs list fewer category types and project types than the code registers. Code adds Segments, Marketing Messages, Dynamic Content and SMS category types, and Point Triggers as a project type. [code: app/bundles/CategoryBundle/EventListener/CategorySubscriber.php:41-52 @7.x] [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html]
- Bare `/asset/{id}` returning 404 is deliberate (it blocks id enumeration); the generated URL is `/asset/{uuid}` and old `{id}:{alias}` links stay for sent emails. [PR #15138] [PR #15776]
- `Asset::getSlug()` and `generateUrl()` throw `LogicException` for an Asset with no id. Guard deleted or unsaved Assets; this caused a 500 on API DELETE and on the Contact timeline. [PR #15776] [PR #15934] [PR #16078]
- The Category form has no Apply button in 7.x (`apply_text => false`). Check buttons with `isButtonClicked()`, not `->get('apply')`, which caused "Child apply does not exist". [PR #14680] [PR #16180]
- Saving a remote Asset fetches the URL to validate its MIME type, so an unreachable or non-2xx URL fails validation even with `validate_remote_domains` off. [PR #16045]
- Linking Projects through an entity's v1 API with `"projects": [ids]` replaces the existing links; send the full list. [PR #15569]

## Related skills
- mautic-contacts — contact identity, tracking cookies, the Preference Center and `lead_categories` semantics.
- mautic-campaigns — how the `asset.download` decision is evaluated inside campaign execution.
- mautic-forms — form actions in general, and the submit flow around "Download an Asset".
- mautic-emails — `{assetlink}` in emails, `assetAttachments`, click-through and A/B winner criteria.
- mautic-points-and-stages — point actions and triggers, including `asset.download`.
- mautic-users-and-permissions — Roles, `viewown`/`viewother`, and the permission bit model.
- mautic-rest-api — the legacy `/api` and API Platform `/api/v2` frameworks and auth.
- mautic-integrations — the legacy integration framework behind MauticCloudStorageBundle.
- mautic-testing — the test base classes, fixtures and the CI test matrix.
- mautic-upgrades-and-versions — the 7→8 event-class migration in general.

## Reference files
- references/behaviour.md — the full numbered behaviour specification (Assets, Categories, Projects); open it before asserting any behaviour.
- references/code-map.md — entities, tables, routes, events, services, parameters, permissions and test locations.
- references/docs-digest.md — what docs.mautic.org and devdocs say, with URLs, procedures and terminology.
- references/test-patterns.md — base classes, fixtures, representative tests and test skeletons.
- references/version-notes.md — 5.x/6.x history, 7.x minors and the 8.x delta for this area.
- references/pr-history.md — why and when behaviour changed: decisions, regression catalogue, feature timeline and open questions from merged PRs.
