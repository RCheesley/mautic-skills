# Mautic architecture - behaviour specification (7.x)

Every item is a testable statement about current 7.x behaviour (commit 419a08a9b35). `CB` below always means the
path prefix `app/bundles/CoreBundle/` written out in full in each citation. Items describe outcomes; code structure is
named only where it is the contract (base classes other bundles extend).

## Contents
- A. Stack and package layout (A1-A6)
- B. Bundles, configuration and dependency injection (B1-B16)
- C. Events (C1-C12)
- D. Models, save pipeline and audit log (D1-D17)
- E. Entities, change tracking, publish state and dates (E1-E16)
- F. Repositories, list search and getEntities() (F1-F17)
- G. Standard controllers, locks and views (G1-G18)
- H. AJAX actions and CSRF (H1-H7)
- I. Request lifecycle listeners (I1-I8)
- J. Permissions framework (summary) (J1-J8)
- K. Translations (K1-K7)
- L. Logging and console errors (L1-L5)
- M. Error handling and offline page (M1-M6)
- N. Input sanitisation (N1-N6)
- O. Admin UI JavaScript and assets (O1-O10)
- P. Routing, menus, notifications, misc platform (P1-P12)
- Q. Contradictions and open questions

## A. Stack and package layout

A1. 7.2.1 requires PHP ~8.2 and Symfony components ~7.4 (framework-bundle v7.4.16 locked on 7.x at `419a08a9b35`; v7.4.14 in the 7.2.1 tag), Doctrine ORM ^2.14 (2.20.9 locked), DBAL ^3.6.2 <3.8 (3.7.3), API Platform ^4.1, FOSRestBundle ^3.8, JMS serializer bundle ^5.4, Twig 3, Guzzle ~7.15, Predis ^3. [code: app/composer.json:15-105 @7.x]

A2. The root package `mautic/mautic` requires `mautic/core-lib ^7.0`, which is the `app/` directory served as a path repository. [code: composer.json:23-27 @7.x] [code: composer.json:128-144 @7.x]

A3. `Mautic\` autoloads from `app/bundles/`, `Mautic\Middleware\` from `app/middlewares/`, `Mautic\Migrations\` from `app/migrations/`; `MauticPlugin\` autoloads from `plugins/`. [code: app/composer.json:7-16 @7.x] [code: composer.json:108-119 @7.x]

A4. Composer installer paths: `type:mautic-plugin` → `plugins/{$name}`, `type:mautic-theme` → `themes/{$name}`, `type:mautic-core` → `app`. [code: composer.json:231-243 @7.x]

A5. Root files such as `index.php`, `bin/console`, `.htaccess` and `importmap.php` are scaffolded from `app/assets/scaffold/files/`; CI diffs every mapped pair, so changing a root scaffolded file requires the same change in the scaffold copy. [code: app/composer.json:112-133 @7.x] [code: .github/workflows/tests.yml:265-277 @7.x]

A6. Middlewares in `app/middlewares` run before Symfony boots (for example IP restriction for `index_dev.php`). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#middlewares]

## B. Bundles, configuration and dependency injection

B1. Bundle metadata is built per bundle: a namespace containing `MauticPlugin\` makes a plugin, `Mautic\` a core bundle; CoreBundle is forced to the front. [code: app/bundles/CoreBundle/DependencyInjection/Builder/BundleMetadataBuilder.php:55-81 @7.x]

B2. For each bundle the builder reads `Config/config.php`, scans `Security/Permissions/*Permissions.php`, and detects static-PHP ORM mapping (`loadMetadata`) and JMS API mapping (`loadApiMetadata`) in `Entity/`. [code: app/bundles/CoreBundle/DependencyInjection/Builder/BundleMetadataBuilder.php:121-149 @7.x] [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/EntityMetadata.php:20-69 @7.x]

B3. Legacy services marked `'optional' => true` whose class does not exist are dropped, and `%` in config values is escaped to `%%` so it is not resolved as a container parameter. [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/ConfigMetadata.php:72-116 @7.x]

B4. `MauticCoreExtension::load()` loads the project `config/services.php` and CoreBundle's `Config/services.php`; the latter autowires/autoconfigures all public classes under `Mautic\CoreBundle\` except `DEFAULT_EXCLUDES` and a local list. [code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:34-43 @7.x] [code: app/bundles/CoreBundle/Config/services.php:23-53 @7.x]

B5. `Security` is in `DEFAULT_EXCLUDES`, so permission classes are not registered by the resource loader; they reach `CorePermissions` through the `mautic.permissions` tag or the deprecated directory scan. [code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-29 @7.x] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/PermissionsPass.php:12-20 @7.x]

B6. `ServicePass` (priority 1000) converts `config.php` `services` groups into definitions with default tags: `events` → `kernel.event_subscriber` (+`mautic.event_subscriber`), `forms` → `form.type`, `helpers` → `twig.helper`, `menus` → `knp_menu.menu`, `models` → `mautic.model` (raises `E_USER_DEPRECATED`), `permissions` → `mautic.permissions`, `integrations` → `mautic.integration`, `controllers` → `controller.service_arguments`. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:33-63 @7.x]

B7. Registering one legacy service name twice throws `InvalidArgumentException("<name> is already registered")`; non-array entries in `services` become container parameters. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:66-75 @7.x]

B8. Legacy argument syntax: `%param%` is a parameter, `"string"` (quoted) a literal, `@=expr` an expression, `@service` or a bare string a service reference. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:277-312 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#service-definitions]

B9. `ModelPass` collects every `mautic.model`-tagged service (and aliases) into the locator used by `ModelFactory`. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ModelPass.php:17-38 @7.x]

B10. `ModelFactory::getModel($key)` accepts a FQCN present in the locator, or `bundle.name` resolved to `mautic.{bundle}.model.{name}` (a bare `foo` means `foo.foo`); unknown keys throw `InvalidArgumentException`. [code: app/bundles/CoreBundle/Factory/ModelFactory.php:70-97 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/Factory/ModelFactoryTest.php @7.x]

B11. The parameter bag is built from bundle `parameters` defaults, then `config/local.php`, then `config/parameters_local.php`, then the `MAUTIC_CONFIG_PARAMETERS` JSON env var; `db_driver` is forced to `pdo_mysql`. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:195-221 @7.x]

B12. Each parameter is exported to the environment as `MAUTIC_<UPPER_KEY>` (arrays JSON-encoded) without overriding an existing `$_ENV` value the loader did not set. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:9-25 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:85-109 @7.x]

B13. `CoreParametersHelper::get($name)` strips a `mautic.` prefix, returns `MAUTIC_TABLE_PREFIX` for `db_table_prefix` when that constant is defined, prefers container parameter `mautic.{name}`, and falls back to the loader bag. [code: app/bundles/CoreBundle/Helper/CoreParametersHelper.php:30-46 @7.x]

B14. Env processors: `env(nullable:X)` turns `''` into null, `env(intNullable:X)` casts to int unless null, `env(mauticconst:NAME)` returns the PHP constant. [code: app/bundles/CoreBundle/DependencyInjection/EnvProcessor/ @7.x]

B15. The container refuses to build (`MessageOnlyErrorHandlerException`) when `pdo_mysql` is missing, except when `MAUTIC_INSTALLER` is defined. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/RequirementsPass.php:11-22 @7.x]

B16. A directory `themes/system/<BundleDir>/Resources/views` overrides that bundle's templates; the original stays reachable as `@!<Namespace>`. In the `test` env, Guzzle and Symfony HttpClient are replaced by mocks. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/SystemThemeTemplatePathPass.php:30-96 @7.x] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/TestPass.php:18-31 @7.x]

## C. Events

C1. 7.x dispatches most events by a string name defined as a constant in the bundle's `*Events.php`; to find who dispatches, grep the constant (and its string value); to find listeners, grep `getSubscribedEvents()` for the constant. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#available-events] [code: app/bundles/CoreBundle/CoreEvents.php @7.x]

C2. Some core events are dispatched by class name with no constant: `EntityExportEvent`, `EntityImportEvent`, `EntityImportUndoEvent`, `EntityValidateEvent`, `JobExtendTimeEvent`, `IconEvent`. [code: app/bundles/CoreBundle/Command/EntityExportCommand.php:85-87 @7.x] [code: app/bundles/CoreBundle/Validator/EntityEventValidator.php:30 @7.x] [code: app/bundles/CoreBundle/EventListener/DashboardSubscriber.php:99-100 @7.x]

C3. `CoreEvents::BUILD_MENU` (`mautic.build_menu`): `CoreSubscriber` (priority 9999) merges every bundle's `config['menu'][<type>]` with default priority 9999. [code: app/bundles/CoreBundle/Menu/MenuBuilder.php:84 @7.x] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:97-112 @7.x]

C4. `CoreEvents::BUILD_ROUTE` is dispatched once per route group (public, main/secure, api, catchall) while routes compile. [code: app/bundles/CoreBundle/Loader/RouteLoader.php:31-77 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#advanced-routing]

C5. `CoreEvents::GLOBAL_SEARCH` collects results from each bundle's `SearchSubscriber`; each model contributes at most `GlobalSearchEvent::RESULTS_LIMIT` (3) rows plus a "show more" row. [code: app/bundles/CoreBundle/Controller/AjaxController.php:144-145 @7.x] [code: app/bundles/CoreBundle/Service/GlobalSearch.php:52-58 @7.x] [code: app/bundles/CoreBundle/Event/GlobalSearchEvent.php:10 @7.x]

C6. `CoreEvents::BUILD_MAUTIC_JS` builds `/mtc.js` (all scopes), `/mautic-essential.js` (RUNTIME+ESSENTIAL) and `/mautic-tracking.js` (TRACKING); CoreBundle's `BuildJsSubscriber` runs at priority 1000 and must stay first; JS appended for a non-accepted scope is dropped; output is minified unless debug. [code: app/bundles/CoreBundle/Controller/JsController.php:20-49 @7.x] [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:14-25 @7.x] [code: app/bundles/CoreBundle/Event/BuildJsEvent.php:15-51 @7.x]

C7. `CoreEvents::VIEW_INJECT_CUSTOM_TEMPLATE` lets a listener swap template name/vars for any admin view and every Twig `include()`; `VIEW_INJECT_CUSTOM_CONTENT` injects HTML at `customContent('slot', _context)` points; `VIEW_INJECT_CUSTOM_BUTTONS` adds buttons; `VIEW_INJECT_CUSTOM_ASSETS` adds assets once per main request. Each is dispatched only when a listener exists. [code: app/bundles/CoreBundle/Controller/CommonController.php:199-207 @7.x] [code: app/bundles/CoreBundle/Twig/Extension/OverrideIncludeExtension.php:27-73 @7.x] [code: app/bundles/CoreBundle/Twig/Helper/ContentHelper.php:33-36 @7.x] [code: app/bundles/CoreBundle/Twig/Helper/ButtonHelper.php:317-321 @7.x] [code: app/bundles/CoreBundle/EventListener/AssetsSubscriber.php:30-38 @7.x]

C8. `CoreEvents::MAINTENANCE_CLEANUP_DATA` is dispatched by `mautic:maintenance:cleanup`; CoreBundle's listener (priority -50) purges `audit_log` and `notifications` older than the cut-off in batches of 10,000 and expired user tokens; dry-run only counts. [code: app/bundles/CoreBundle/Command/CleanupMaintenanceCommand.php:124-125 @7.x] [code: app/bundles/CoreBundle/EventListener/MaintenanceSubscriber.php:29-81 @7.x]

C9. `CoreEvents::LIST_STATS` serves `/api/stats/{table}`; the `audit_log` table is admin-only. [code: app/bundles/CoreBundle/Controller/Api/StatsApiController.php:39 @7.x] [code: app/bundles/CoreBundle/EventListener/CommonStatsSubscriber.php:56-93 @7.x]

C10. `CoreEvents::PRE_UPGRADE` and `POST_UPGRADE` have no dispatcher in core or bundled plugins. [code: app/bundles/CoreBundle/CoreEvents.php @7.x]

C11. `CommonEvent::setFailed()` is the generic veto used by events derived from `CommonEvent`. [code: app/bundles/CoreBundle/Event/CommonEvent.php:56 @7.x]

C12. In 8.x events are dispatched with a single argument so the class name is the event name; constant classes `CoreEvents`, `ApiEvents`, `ConfigEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents`, `UserEvents` are deleted, and constants that remain but are no longer dispatched (e.g. `ChannelEvents::ADD_CHANNEL`, `FormEvents::FORM_ON_SUBMIT`) leave old listeners silently unused. [PR #17157] [PR #17183] [PR #17625] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch]

## D. Models, save pipeline and audit log

D1. `AbstractCommonModel` receives the entity manager, `CorePermissions`, event dispatcher, URL generator, translator, `UserHelper`, logger and `CoreParametersHelper`; `getRepository()` must be overridden (the default returns the `FormEntity` repository) and `getPermissionBase()` defaults to `''`. [code: app/bundles/CoreBundle/Model/AbstractCommonModel.php:27-85 @7.x]

D2. `getEntities($args)` always sets the current user on the repository before querying, so `is:mine` works. [code: app/bundles/CoreBundle/Model/AbstractCommonModel.php:94-102 @7.x]

D3. `saveEntity($entity, $unlock = true)`: `isNewEntity()`, `setTimestamps()`, `pre_save`, repository save (persist+flush), `post_save` with the pre-save event. [code: app/bundles/CoreBundle/Model/FormModel.php:103-113 @7.x]

D4. An entity is new if `isNew()` is true, else if `getId()` is falsy, else if its UnitOfWork state is `STATE_NEW`. [code: app/bundles/CoreBundle/Model/FormModel.php:183-194 @7.x] [code: app/bundles/CoreBundle/Entity/FormEntity.php:440-459 @7.x]

D5. With `$unlock = true` the checkout fields are cleared before anything else. [code: app/bundles/CoreBundle/Model/FormModel.php:245-249 @7.x]

D6. New entities get `dateAdded = now` and `createdBy` = the current `User` only if not already set and only if the current user is a real `User` (not a guest); modified data is set too. [code: app/bundles/CoreBundle/Model/FormModel.php:251-266 @7.x]

D7. Existing entities get modified data only when `getChanges()` is non-empty (or the entity has no `getChanges()`), unless they implement `SkipModifiedInterface` and opt out. [code: app/bundles/CoreBundle/Model/FormModel.php:269-275 @7.x]

D8. Modified data sets `dateModified = now` only when `dateModified` is null (honouring the `MAUTIC_DATE_MODIFIED_OVERRIDE` unix timestamp constant) and sets `modifiedBy`/`modifiedByUser` to the current user. No core code resets `dateModified` to null. [code: app/bundles/CoreBundle/Model/FormModel.php:278-293 @7.x]

D9. `saveEntities()` order: `pre_save` ×N, `pre_batch_save` ×1, persist with a flush every 20 plus a final flush, `post_save` ×N, `post_batch_save` ×1. [code: app/bundles/CoreBundle/Model/FormModel.php:133-174 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/Model/FormModelTest.php:43-107 @7.x]

D10. `saveAndDetachEntity()` saves then detaches, for high-volume writes such as notifications. [code: app/bundles/CoreBundle/Model/FormModel.php:120-125 @7.x]

D11. `deleteEntity()` dispatches `pre_delete`; if the event reports dependency errors it throws `DeleteEntityDependencyException` and deletes nothing; otherwise it removes, flushes, sets `$entity->deletedId` and dispatches `post_delete`. [code: app/bundles/CoreBundle/Model/FormModel.php:298-330 @7.x]

D12. `deleteEntities($ids)` flushes every 20, skips entities with dependency errors, deletes the rest, and throws `DeleteEntitiesDependencyException($deleted, $unableToDelete)` at the end if any were skipped. [code: app/bundles/CoreBundle/Model/FormModel.php:332-357 @7.x]

D13. `togglePublishStatus()`: unpublished → published; published/pending/expired → `pre_unpublish` then unpublished (entities with `setIsEnabled` flip that instead); then modified data without touching the lock, `on_toggle_publish`, `pre_save`, save, `post_save`. [code: app/bundles/CoreBundle/Model/FormModel.php:203-234 @7.x]

D14. `createForm()` throws `NotFoundHttpException('Object does not support edits.')` unless overridden. [code: app/bundles/CoreBundle/Model/FormModel.php:370-373 @7.x]

D15. `flushAndCatch()` rethrows flush exceptions only when `MAUTIC_ENV === 'dev'`; in prod it logs at `error`. [code: app/bundles/CoreBundle/Model/FormModel.php:489-503 @7.x]

D16. `AuditLogModel::writeToLog()` stores `bundle, object, objectId, action, details, ipAddress`; the IP becomes `*.*.*.*` when `anonymize_ip` is on; when `MAUTIC_IGNORE_AUDITLOG_USER` or `MAUTIC_AUDITLOG_USER` is defined the row has `userId = 0` and `userName` = the constant or `mautic.core.system`; the row is persisted and detached. [code: app/bundles/CoreBundle/Model/AuditLogModel.php:34-64 @7.x]

D17. Entity detail pages show up to 10 audit rows for the object newer than the entity's `dateAdded`, newest first, never including `object = 'category'`. [code: app/bundles/CoreBundle/Entity/AuditLogRepository.php:165-197 @7.x] [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:1094 @7.x]

## E. Entities, change tracking, publish state and dates

E1. `CommonEntity` and `FormEntity` are mapped superclasses. `FormEntity` adds `is_published`, nullable `date_added`, `created_by` (int id), `created_by_user`, `date_modified`, `modified_by`, `modified_by_user`, `checked_out`, `checked_out_by`, `checked_out_by_user`; user columns store integer ids plus a display-name copy, not associations. [code: app/bundles/CoreBundle/Entity/FormEntity.php:134-184 @7.x] [code: app/bundles/CoreBundle/Entity/FormEntity.php:311-375 @7.x]

E2. `CommonEntity::__call` maps `isFoo()` to `getFoo()` and `getName()` to `getTitle()` when only a title exists. [code: app/bundles/CoreBundle/Entity/CommonEntity.php:35-45 @7.x]

E3. Setters that call `isChanged($prop, $val)` record `[old, new]`; DateTimes are compared as ISO-8601, objects and `category` by id, `''`↔`null` is ignored, collections record `added`/`removed`. [code: app/bundles/CoreBundle/Entity/CommonEntity.php:63-137 @7.x]

E4. Cloning a `FormEntity` resets `dateAdded`, `checkedOut`, `createdBy`, `changes`, sets `dateModified = now` and `isPublished = false`. [code: app/bundles/CoreBundle/Entity/FormEntity.php:215-223 @7.x]

E5. `getPublishStatus()`: `unpublished` if the flag is false; `pending` if `publishUp` is set and now < `publishUp`; `expired` if `publishDown` is set and now ≥ `publishDown`; else `published`. [code: app/bundles/CoreBundle/Entity/FormEntity.php:412-435 @7.x]

E6. `isPublished()` on entities with publish dates is true only for status `published` and (by default) a null or published category; `isPublished(false)` returns the raw flag. [code: app/bundles/CoreBundle/Entity/FormEntity.php:233-251 @7.x]

E7. Query equivalents: `isPublished = true AND (publishDown IS NULL OR publishDown >= now) AND (publishUp IS NULL OR publishUp <= now)`; the DBAL variant binds now as a UTC string. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:527-630 @7.x]

E8. `ClassMetadataBuilder`: `addId()` = unsigned auto INT; `addBigIntIdField()` = unsigned BIGINT; `addUuid()` = GUID PK; `addIdColumns()` = id + `name` + nullable TEXT `description`; `addCategory()` = nullable `category_id` with `ON DELETE SET NULL`; `addPublishDates()` = nullable `publish_up`/`publish_down`. [code: app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php:118-245 @7.x]

E9. String fields and fields with a same-named index are forced to length 191. [code: app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php:23 @7.x] [code: app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php:370-396 @7.x]

E10. Table, index, unique-constraint, join-table and sequence names of `Mautic*` entities get the `db_table_prefix`; tables of `DeprecatedInterface` entities are dropped from generated schemas. [code: app/bundles/CoreBundle/EventListener/DoctrineEventsSubscriber.php:30-135 @7.x]

E11. `datetime` and `datetime_immutable` are stored in UTC and read back converted to PHP's default timezone. [code: app/bundles/CoreBundle/Doctrine/Type/UTCDateTimeType.php:17-71 @7.x] [code: app/config/config.php:203-205 @7.x]

E12. `ArrayType` stores `null` as `N;` and scalars as `a:0:{}`; it refuses to write serialized objects with non-public members and drops them on read. [code: app/bundles/CoreBundle/Doctrine/Type/ArrayType.php:15-66 @7.x]

E13. `OptimisticLockInterface` entities carry `version` (default 1); the standard edit form posts the version and a mismatch rejects the save with `mautic.core.optimistic_lock.changed_by_someone_else_error`; the bump happens on Doctrine `postUpdate`. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:1157-1198 @7.x] [code: app/bundles/CoreBundle/EventListener/OptimisticLockSubscriber.php:24-33 @7.x]

E14. `UuidInterface` entities get a UUID v4 when empty, and a fresh one if a new entity's supplied UUID already exists. [code: app/bundles/CoreBundle/EventListener/UUIDListener.php:27-60 @7.x]

E15. `CacheInvalidateInterface` entities clear their declared result-cache namespaces on persist/update/remove, skipping updates of `FormEntity`s with no changes. [code: app/bundles/CoreBundle/EventListener/CacheInvalidateSubscriber.php:48-85 @7.x]

E16. Deleting a variant parent or translation parent cascades to children at DB level (`ON DELETE CASCADE`). [code: app/bundles/CoreBundle/Entity/VariantEntityTrait.php:54 @7.x] [code: app/bundles/CoreBundle/Entity/TranslationEntityTrait.php:48 @7.x]

## F. Repositories, list search and getEntities()

F1. The search string is `strip_tags`+`trim`med and parsed into filters `{type, command, string, not, strict, children, missingValue}`. [code: app/bundles/CoreBundle/Helper/SearchStringHelper.php:47-215 @7.x]

F2. `word:value` is a command; `!word:value` or `word:!value` negates; `+value` is exact; values after a command are lowercased. [code: app/bundles/CoreBundle/Helper/SearchStringHelper.php:127-144 @7.x] [code: app/bundles/CoreBundle/Helper/SearchStringHelper.php:235-265 @7.x]

F3. Quotes and parentheses group; `!` before a group negates it; bare `OR`/`AND` set the type of the next clause. [code: app/bundles/CoreBundle/Helper/SearchStringHelper.php:153-223 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/Helper/SearchStringHelperTest.php:11-19 @7.x]

F4. A trailing command with no value produces `1 = 0` (no rows). [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1803-1805 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/Helper/SearchStringHelperTest.php:21-29 @7.x]

F5. Commands match translations in the current locale and in `en_US`; an unknown `cmd:value` is searched as the literal string. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1751-1822 @7.x]

F6. Standard commands: `is:published`, `is:unpublished`, `is:uncategorized` (category null or `''`), `is:mine` (`createdBy` = current user), `category:alias` (exact), `ids:1,2,3`; the base repository advertises only `ids` unless the subclass returns `getStandardSearchCommands()`. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:707-789 @7.x] [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1198-1284 @7.x] [code: app/bundles/CoreBundle/Tests/Functional/Entity/CommonRepositoryTest.php:13-35 @7.x]

F7. Free text is `LIKE` on `name` (or `title`), wrapped `%…%` unless the user typed `%` or used `+`; command values get a trailing `%` only. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1073-1192 @7.x]

F8. `getEntities()` builds `SELECT e` indexed by id, auto-joins `e.category cat` when the entity has a category, or uses `$args['qb']`. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:354-369 @7.x]

F9. Recognised args: `start`, `limit` (0/absent = no limit), `orderBy`, `orderByDir`, `filter`, `ids`, `ownedBy`, `select`, `index_by`, `hydration_mode`, `iterable_mode`, `ignore_paginator`, `use_simple_paginator`, `result_cache` (must be `ResultCacheOptions`), `qb`. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:354-406 @7.x] [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1300-1604 @7.x]

F10. Return types: Doctrine `Paginator` by default (count = total); `SimplePaginator` with `use_simple_paginator` (only valid without to-many joins); array with `ignore_paginator`; iterable with `iterable_mode`. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:389-405 @7.x] [code: app/bundles/CoreBundle/Doctrine/Paginator/SimplePaginator.php:10-56 @7.x]

F11. `filter` keys: `string` (search syntax), `force`/`criteria` (column/expr/value lists ANDed with everything), `where` (structured clauses), `order`. Controllers restrict users without `viewother` with a forced `e.createdBy = <user id>`. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1528-1588 @7.x] [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:850-852 @7.x]

F12. Filter expressions support `isNull`, `isNotNull`, `in`, `notIn`, `like`/`notLike` (numeric values become `eq`/`neq`), any `Expr` method, comma-separated column lists (OR), `group`, and `not`. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:448-521 @7.x]

F13. `where` clauses support `eq neq lt lte gt gte like notLike in notIn between notBetween isNull isNotNull isEmpty isNotEmpty andX orX` and `internal` formulas; `in` values are CSV (quoted with `"`), a single value degrades to `eq`; column names are sanitised and prefixed with the alias. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1007-1032 @7.x] [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1610-1706 @7.x]

F14. Ordering: `filter['order']` wins; else empty `orderBy` uses `getDefaultOrder()`; else each comma-separated column gets the sanitised direction (default `ASC`). [code: app/bundles/CoreBundle/Entity/CommonRepository.php:983-998 @7.x] [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1381-1420 @7.x]

F15. Query parameters are named `par` + a base-36 counter per repository instance. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1716-1723 @7.x]

F16. `getSimpleList()` returns `value/label` rows ordered by label, restricted to `is_published = 1` and `deleted IS NULL` where those columns exist. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:723-774 @7.x]

F17. `upsert()` issues raw `INSERT … ON DUPLICATE KEY UPDATE`, sets the id from `LAST_INSERT_ID()`, flags insert vs update from the affected-row count (1/2), and bypasses the entity manager. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:868-951 @7.x] [code: app/bundles/CoreBundle/Tests/Functional/Entity/CommonRepositoryUpsertTest.php:23 @7.x]

## G. Standard controllers, locks and views

G1. Hierarchy: Symfony `AbstractController` → `CommonController` → `AbstractFormController` → `AbstractStandardFormController` (→ deprecated `FormController`); `AjaxController` extends `CommonController`. Only controllers implementing the `MauticController` marker are affected by Mautic's controller listeners. [code: app/bundles/CoreBundle/Controller/MauticController.php:7-12 @7.x]

G2. `executeAction($objectAction, $objectId, ...)` forwards `/s/{bundle}/{objectAction}/{objectId}` to `{objectAction}Action` when it exists, else renders the 404 page. [code: app/bundles/CoreBundle/Controller/CommonController.php:502-519 @7.x]

G3. A standard controller implements `getModelName()`; route base `mautic_{model}_index`/`_action`, session base `mautic.{model}`, translation base `mautic.{model}`, `mauticContent` = model name, template fallback `@MauticCore/Standard`, default order `name ASC` all derive from it. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:64 @7.x] [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:589-724 @7.x]

G4. Only `list.html.twig` has a core fallback; `form.html.twig` and `details.html.twig` must exist in the bundle or `getTemplateName()` throws. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:679-693 @7.x]

G5. Action-to-permission mapping: `new` → `create`; `view`/`index` → own/other via `hasEntityAccess` (else `view`); `clone` → `create` and view; `delete`/`batchDelete` → `deleteown`/`deleteother`; other actions → `{action}own`/`{action}other`; the owner is `getPermissionUser()` or `getCreatedBy()`. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:193-236 @7.x]

G6. `indexStandard()` persists `orderby`, `orderbydir`, `limit`, `filterby` and `search` in the session; clicking the same `orderby` twice toggles direction; page size defaults to `default_pagelimit` (30); an out-of-range page redirects to the last page. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:800-915 @7.x] [code: app/bundles/CoreBundle/Controller/CommonController.php:616-664 @7.x]

G7. `newStandard()`: cancel returns to the index; a valid save redirects to view (or index); "Apply" re-enters edit for the new id; a form with an `updateSelect` field (modal "create new") returns JSON with `closeModal`, `updateSelect`, `id`, `name`. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:922-1040 @7.x]

G8. `editStandard()`: not found → error flash + redirect; GET on an entity locked by another user → locked flash + redirect; otherwise GET locks it. On POST: cancel unlocks; a valid save calls `saveEntity($entity, $unlock = saveClicked)`. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:338-506 @7.x]

G9. Buttons: `apply`, `save` ("Save & Close"), `cancel`; cancelled/applied are detected by `buttons[cancel]`/`buttons[apply]` keys in the POST. [code: app/bundles/CoreBundle/Form/Type/FormButtonsType.php:32-129 @7.x] [code: app/bundles/CoreBundle/Controller/AbstractFormController.php:141-158 @7.x]

G10. `lockEntity()` only locks persisted entities and only for users with an id. [code: app/bundles/CoreBundle/Model/FormModel.php:29-40 @7.x]

G11. `isLocked()` is true only when `checkedOut` is set, the lock has not expired, and the holder is another user; `max_entity_lock_time = 0` (default) means locks never expire. [code: app/bundles/CoreBundle/Model/FormModel.php:47-74 @7.x] [code: app/bundles/CoreBundle/Config/config.php:708 @7.x]

G12. The locked flash names the holder, links to contact them, shows the lock time, and includes an "Override Lock" link only if the viewer can edit; the override route (`/s/action/unlock/{model}/{id}`) needs edit rights and only follows a `returnUrl` on the same host. [code: app/bundles/CoreBundle/Controller/AbstractFormController.php:22-136 @7.x]

G13. `unlockEntity()` refreshes the entity from the DB (dropping unflushed changes) before clearing the lock. [code: app/bundles/CoreBundle/Model/FormModel.php:82-95 @7.x]

G14. Navigating away from an edit form fires the `unlockEntity` AJAX action, which only unlocks entities checked out by the current user; links with `data-ignore-formexit="true"` skip it. [code: app/bundles/CoreBundle/Controller/AjaxController.php:304-325 @7.x] [code: app/bundles/CoreBundle/Form/EventListener/FormExitSubscriber.php:27-69 @7.x] [code: app/bundles/CoreBundle/Assets/js/10.entity.js:307-320 @7.x]

G15. Delete and batch delete run only on POST; batch ids come from the JSON `ids` query parameter; entities locked by others are skipped with a flash. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:107-171 @7.x] [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:274-329 @7.x]

G16. `delegateView()` returns HTML for normal requests and JSON `{newContent, route, mauticContent, flashes, notifications, ...passthroughVars}` for XHR; `postActionRedirect()` returns 302 (default target the dashboard) or the same JSON; `forwardController` defaults to true there and false in `delegateView`. [code: app/bundles/CoreBundle/Controller/CommonController.php:218-278 @7.x] [code: app/bundles/CoreBundle/Controller/CommonController.php:316-375 @7.x]

G17. `notFound()` serves the landing page configured in `404_page` with HTTP 404 when published, else the standard 404. [code: app/bundles/CoreBundle/Controller/CommonController.php:568-597 @7.x]

G18. `ExceptionController` returns JSON `{errors:[{message,code,type}]}` for `/oauth*`, API and `Accept: application/json` requests (real messages only in dev or for not-found/access-denied); prod uses `Error/` templates, dev uses `Exception/`; invalid codes become 500. [code: app/bundles/CoreBundle/Controller/ExceptionController.php:15-113 @7.x]

## H. AJAX actions and CSRF

H1. All admin AJAX goes through `/s/ajax`; `action` is read from the query string first, then the POST body. [code: app/bundles/CoreBundle/Controller/AjaxController.php:64-74 @7.x]

H2. Unauthenticated callers (`IS_AUTHENTICATED_REMEMBERED` missing) get `{"success":0}`. [code: app/bundles/CoreBundle/Controller/AjaxController.php:76 @7.x] [code: app/bundles/CoreBundle/Controller/AjaxController.php:115 @7.x]

H3. `bundle:name` routes to `Mautic\{Bundle}Bundle\Controller\AjaxController::{name}Action`, retrying with `Mautic{Bundle}`; `plugin:bundle:name` uses `MauticPlugin`; a missing method returns `{"success":0}`. [code: app/bundles/CoreBundle/Controller/AjaxController.php:77-136 @7.x]

H4. Core actions without prefix: `globalSearch`, `commandList`, `globalCommandList`, `togglePublishStatus`, `unlockEntity`, `clearNotification`, `getBuilderTokens`, `downloadIpLookupDataStore`, `getIpLookupForm`. [code: app/bundles/CoreBundle/Controller/AjaxController.php:138-440 @7.x]

H5. `togglePublishStatus` checks `publishown/publishother` → `publish` → `manage` → `full` → `editown/editother` → `edit`; returns `{success:1, statusHtml}`, HTTP 422 on `RecordCanNotUnpublishException`, HTTP 403 without permission. A `customToggle` property is flipped with a plain repository save and no model hooks. [code: app/bundles/CoreBundle/Controller/AjaxController.php:219-299 @7.x]

H6. XHR POSTs to paths starting `/s/` require header `X-CSRF-Token` for intention `mautic_ajax_post`; on failure the response is HTTP 200 JSON `{"flashes": ...}` with `mautic.core.error.csrf`. GET, non-XHR and public paths are not checked. [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:27-63 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/EventListener/RequestSubscriberTest.php:59-123 @7.x]

H7. The admin page exposes the token as JS global `mauticAjaxCsrf` and `mQuery.ajaxSetup` adds the header to every request; regular forms use Symfony's `_token`. [code: app/bundles/CoreBundle/Resources/views/Default/script.html.twig:10 @7.x] [code: app/bundles/CoreBundle/Assets/js/1.core.js:37-40 @7.x]

## I. Request lifecycle listeners

I1. `ErrorHandlingListener` (kernel.request 2047) wires the Monolog loggers into the static `ErrorHandler`. [code: app/bundles/CoreBundle/EventListener/ErrorHandlingListener.php:15-33 @7.x]

I2. Priority 128: PHP default timezone set from session `_timezone` (fallback `default_timezone`), only when the request has a previous session. [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:20-40 @7.x]

I3. Priority 101: request locale from session `_locale` (fallback `locale`). [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:41-61 @7.x]

I4. Priority 1 / -1: the router context is forced to the `site_url`-derived scheme/host/ports/base URL so web and CLI generate the same URLs; skipped for an empty host or during install. [code: app/bundles/CoreBundle/EventListener/RouterSubscriber.php:34-72 @7.x]

I5. Priority 0: AJAX CSRF check (H6) and `VIEW_INJECT_CUSTOM_ASSETS`. [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:27-63 @7.x] [code: app/bundles/CoreBundle/EventListener/AssetsSubscriber.php:30-38 @7.x]

I6. On interactive login: session `mautic.user`, last login, `_timezone`/`_locale` from the user or defaults, then `UserEvents::USER_LOGIN`. [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:53-95 @7.x]

I7. `ExceptionListener` (kernel.exception 253) logs uncaught exceptions except 403/404 HTTP exceptions and renders them through `ExceptionController::showAction`; authentication/access-denied/logout exceptions are left to the firewall; SAML errors redirect to login. [code: app/bundles/CoreBundle/EventListener/ExceptionListener.php:35-147 @7.x]

I8. `CookieHelper` buffers cookies and writes them on `kernel.response`; defaults: expiry 1800 s, SameSite Lax, `path=/`, `secure=true`, `httponly=false`. [code: app/bundles/CoreBundle/Helper/CookieHelper.php:44-84 @7.x] [code: app/bundles/CoreBundle/Config/config.php:297-300 @7.x]

## J. Permissions framework (summary)

Full rules, role UI and API users: mautic-users-and-permissions.

J1. `CorePermissions` (service `mautic.security`) is the registry; each bundle's `*Permissions extends AbstractPermissions` declares `name => [level => bit]`. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php @7.x] [code: app/bundles/CoreBundle/Config/services.php:167-170 @7.x]

J2. Bits: standard set view 4, edit 16, create 32, delete 128, publish 512, full 1024; extended set adds viewown 2, editown 8, deleteown 64, publishown 256. A role stores the sum. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:334-352 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:455-477 @7.x]

J3. `isGranted()` needs `bundle:name:level` (3 or 4 parts) else `PermissionBadFormatException` (code 403); admins pass any well-formed string; unknown levels throw `PermissionNotFoundException` unless `$allowUnknown`. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-235 @7.x]

J4. Results are memoised per string for the life of the service, regardless of the `$userEntity` argument; `reset()` does not clear them. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:39-42 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:210-213 @7.x]

J5. The `full` bit grants every level; `view` ≡ `viewown` on extended permissions and `viewown/viewother` ≡ `view` on standard ones. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:144-207 @7.x]

J6. Modes: `MATCH_ALL` (default), `MATCH_ONE`, `RETURN_ARRAY`. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:252-263 @7.x]

J7. `hasEntityAccess($own, $other, $ownerId)`: guests get false; owner 0 → other; owner = current user → own; else other. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:335-379 @7.x]

J8. Mautic's permission system is bitwise and does not use Symfony voters. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#firewalls-and-user-access-management]

## K. Translations

K1. Load order for a locale: each bundle's `Translations/<locale>/*.ini`, the current theme's `translations/<locale>/*.ini`, `<translations dir>/<locale>/*.ini` (downloaded packs), `<translations dir>/overrides/<locale>/*.ini`; later wins within a domain. [code: app/bundles/CoreBundle/Loader/TranslationLoader.php:21-73 @7.x]

K2. The INI file name is the domain (`messages`, `flashes`, `javascript`, `validators`); a corrupt INI throws in `dev` and is skipped otherwise. [code: app/bundles/CoreBundle/Loader/TranslationLoader.php:80-97 @7.x]

K3. `en_US` is always loaded before the requested locale as fallback; translation caching is off outside `prod`. [code: app/bundles/CoreBundle/Translation/TranslatorLoader.php:14-24 @7.x] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/TranslationLoaderPass.php:19-31 @7.x]

K4. `Translator::trans()` delegates to Symfony and retries with locale `EN` on `InvalidArgumentException` (bad plural syntax). [code: app/bundles/CoreBundle/Translation/Translator.php:42-49 @7.x]

K5. `transConditional($preferred, $alternative)` uses the preferred key if it exists; `hasId()` tests existence. [code: app/bundles/CoreBundle/Translation/Translator.php:87-110 @7.x]

K6. `getJsLang()` exposes the `javascript` domain (en_US merged with the current locale) to the page as `mauticLang`; JS reads it with `Mautic.translate(id)`, which returns the id when missing. [code: app/bundles/CoreBundle/Translation/Translator.php:111-126 @7.x] [code: app/bundles/CoreBundle/Assets/js/1.core.js:405-412 @7.x]

K7. Selecting a new `locale` in Configuration downloads its language pack; on failure it reverts to `en_US` with an error. [code: app/bundles/CoreBundle/EventListener/ConfigSubscriber.php:50-76 @7.x]

## L. Logging and console errors

L1. Channel `mautic` → `FileLogHandler` at `<log_path>/<log_file_name>` (default `var/logs/mautic_<env>.php`), daily rotation keeping `max_log_files` (7); level `notice`, or `debug` with full traces when `debug` is true or env is `dev`. [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:12-25 @7.x]

L2. In prod all other channels go through a `fingers_crossed` buffer (200 records, triggered at `error`) into `var/logs/<env>.php`. [code: app/config/config_prod.php:35-50 @7.x]

L3. Every record carries `extra.hostname` and `extra.pid`. [code: app/bundles/CoreBundle/Monolog/LogProcessor.php:11-17 @7.x]

L4. Exceptions escaping a console command are logged at `error` on `mautic` with the command name and trace; non-zero exit codes are logged as warnings and clamped to 255. [code: app/bundles/CoreBundle/EventListener/ConsoleErrorListener.php:17-35 @7.x] [code: app/bundles/CoreBundle/EventListener/ConsoleTerminateListener.php:15-34 @7.x]

L5. Inject `monolog.logger.mautic` to write to the Mautic log. [code: app/bundles/CoreBundle/Config/services.php:228-232 @7.x]

## M. Error handling and offline page

M1. `ErrorHandler::register($env)` runs from `index.php` before the kernel boots; it installs fatal/exception/error handlers and sets `display_errors=0` (dev keeps display and enables Symfony `Debug`). [code: index.php:15 @7.x] [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:304-331 @7.x]

M2. Notices and warnings are logged; deprecations are logged at `debug`; in dev non-deprecation errors become `ErrorException`. [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:121-154 @7.x]

M3. Fatal errors are logged once and rendered via the exception path (`OutOfMemoryError` for memory exhaustion). [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:188-225 @7.x]

M4. An uncaught exception sends HTTP 500 and, for non-AJAX prod requests, renders `Resources/views/Offline/offline.html.twig` (or `custom_offline.html.twig` from `Offline/` or `Exception/`) saying the site is offline and to check server logs; `MAUTIC_OFFLINE` is defined. [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:156-181 @7.x] [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:458-514 @7.x]

M5. AJAX/JSON requests get `{"errors":[{"message", "code":500, "type":null}]}` (plus trace in dev); with `MAUTIC_AJAX_DIRECT_RENDER` the HTML is wrapped as `{"newContent": ...}`. [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:172-176 @7.x] [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:424-456 @7.x]

M6. Exceptions implementing `ErrorHandlerException` may show their message on the offline page; `MessageOnlyErrorHandlerException` and `DatabaseConnectionException` show their message. [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:244-265 @7.x]

## N. Input sanitisation

N1. `InputHelper::clean()` = `FILTER_SANITIZE_SPECIAL_CHARS` (HTML-escapes `'"<>&`), recursive for arrays. [code: app/bundles/CoreBundle/Helper/InputHelper.php:162-176 @7.x]

N2. `InputHelper::_($value, $mask)` applies a per-key mask; keys missing from a mask array fall back to Joomla's `InputFilter`; unknown static calls (`int()`, `float()`) delegate to it. [code: app/bundles/CoreBundle/Helper/InputHelper.php:99-153 @7.x]

N3. `html()` blocks `applet bgsound base basefont embed frame frameset ilayer layer object` while preserving doctype, comments, Outlook tags and `<script>`; `strict_html()` allows only `b i u em strong a span`. [code: app/bundles/CoreBundle/Helper/InputHelper.php:40-90 @7.x] [code: app/bundles/CoreBundle/Helper/InputHelper.php:365-468 @7.x]

N4. Forms built on `AbstractFormStandardType` run `CleanFormSubscriber` on `PRE_SUBMIT` with `description => strict_html` plus the type's `clean_masks`; everything else is `clean`ed. [code: app/bundles/CoreBundle/Form/Type/AbstractFormStandardType.php:40-44 @7.x] [code: app/bundles/CoreBundle/Form/EventListener/CleanFormSubscriber.php:32-40 @7.x]

N5. The `?ct=` clickthrough payload accepts only base64 of a serialized array; serialized objects are refused. [code: app/bundles/CoreBundle/Helper/ClickthroughHelper.php:24-52 @7.x] [code: app/bundles/CoreBundle/Helper/Serializer.php:14-28 @7.x]

N6. CSV export prefixes cells starting with `+ - = @` with a space and writes a UTF-8 BOM. [code: app/bundles/CoreBundle/Helper/DataExporterHelper.php:60-69 @7.x] [code: app/bundles/CoreBundle/Helper/ExportHelper.php:59-78 @7.x]

## O. Admin UI JavaScript and assets

O1. jQuery runs in no-conflict mode as `mQuery`; app code lives on global `Mautic` and `MauticVars`. [code: app/bundles/CoreBundle/Assets/js/1.core.js:1-3 @7.x]

O2. Globals from `script.html.twig`: `mauticBasePath`, `mauticBaseUrl`, `mauticAjaxUrl`, `mauticAjaxCsrf`, `mauticSessionLifetime`, `mauticContent`, `mauticEnv`, `mauticLang`, `mauticLocale`, `mauticEditorFonts`, `LoginUserId`, and others. [code: app/bundles/CoreBundle/Resources/views/Default/script.html.twig:6-23 @7.x]

O3. After content loads, `Mautic[<mauticContent> + 'OnLoad'](container, response)` runs if defined, and `...OnUnload` before content is replaced; jQuery events `mautic:onPageLoad:before/after` fire on the container. [code: app/bundles/CoreBundle/Assets/js/1a.content.js:320-321 @7.x] [code: app/bundles/CoreBundle/Assets/js/1a.content.js:660-663 @7.x]

O4. `data-toggle="ajax"` links load via `Mautic.loadContent` (GET default, `data-method`, `data-target`); Ctrl/Cmd-click opens a new tab; the same route is not requested twice concurrently; `processPageContent` injects content, pushes history, sets the title and active menu, and shows flashes/notifications. [code: app/bundles/CoreBundle/Assets/js/1a.content.js:223-317 @7.x] [code: app/bundles/CoreBundle/Assets/js/1a.content.js:886-934 @7.x]

O5. Forms in loaded content are ajaxified and posted by `Mautic.postForm`. [code: app/bundles/CoreBundle/Assets/js/1a.content.js:330 @7.x] [code: app/bundles/CoreBundle/Assets/js/6.forms.js:46 @7.x]

O6. Every AJAX request appends `mauticUserLastActive` and `mauticLastNotificationId`; `/s/keep-alive` is pinged every `session.gc_maxlifetime/2` seconds. [code: app/bundles/CoreBundle/Assets/js/1.core.js:16-46 @7.x] [code: app/bundles/CoreBundle/Assets/js/1.core.js:90-121 @7.x]

O7. List sorting, paging and filtering (`Mautic.reorderTableData`, `limitTableData`, `filterTableData`) re-request the index with `tmpl=list`; bulk actions send checked ids as JSON `ids`. [code: app/bundles/CoreBundle/Assets/js/10.entity.js:36-116 @7.x] [code: app/bundles/CoreBundle/Assets/js/10.entity.js:371-432 @7.x]

O8. Bundle assets in `Assets/css` and `Assets/js` are discovered automatically and, in prod, combined into `media/css/{libraries,app}.css` and `media/js/{libraries,app}.js` (regenerated when missing or older than a source); URLs carry `?v<sha1(secret_key+version)>`; themes override with `libraries_custom`/`app_custom`. [code: app/bundles/CoreBundle/Helper/AssetGenerationHelper.php:68-237 @7.x]

O9. The admin `<head>` loads `importmap('app')` (Symfony AssetMapper entry `app/bundles/CoreBundle/Assets/app.js`, which only imports `app.scss`); webpack builds only the CKEditor 5 bundle. [code: app/bundles/CoreBundle/Resources/views/Default/head.html.twig:14-19 @7.x] [code: importmap.php:3-12 @7.x] [code: webpack.config.js:28-37 @7.x]

O10. Flash messages: PHP `addFlashMessage($key, $params, $type)` with keys in `flashes.ini`; JS `Mautic.addInfoFlashMessage`/`addErrorFlashMessage` + `Mautic.setFlashes`. [devdocs: https://devdocs.mautic.org/en/7.2/design/flash_messages.html]

## P. Routing, menus, notifications, misc platform

P1. Route groups are compiled public → api (`/api`) → main (`/s`) → catchall, all forced to https when `site_url` is https. [code: app/bundles/CoreBundle/Loader/RouteLoader.php:28-85 @7.x]

P2. `{page}` defaults to 0 with `\d+`; `{objectId}` defaults to 0 with `[a-zA-Z0-9_-]+`; in api routes `{id}` and `{…Id}` are `\d+`; api routes default to `_format=json` and GET. [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:248-307 @7.x]

P3. `standard_entity => true` on an api route expands to 10 endpoints `getall, getone, new, newbatch, editbatchput, editbatchpatch, editput, editpatch, deletebatch, delete` named `mautic_api_<name>_<standard>`. [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:123-201 @7.x]

P4. Any GET path ending in `/` is 301-redirected without it; `/s` and `/s/` go to the dashboard; `/` renders the landing page whose id is `webroot`, else the dashboard. [code: app/bundles/CoreBundle/Controller/CommonController.php:298-309 @7.x] [code: app/bundles/CoreBundle/Controller/DefaultController.php:31-49 @7.x]

P5. Menu items are sorted by `priority` (default 9999, children inherit), hidden when `access` is not granted (`MATCH_ONE`, or `admin`), or when `checks.parameters`, `checks.request` or `checks.integration` fail. [code: app/bundles/CoreBundle/Menu/MenuHelper.php:32-282 @7.x]

P6. `FlashBag::add()` translates in domain `flashes` (or verbatim with `$domain === false`) and can also create a bell notification. [code: app/bundles/CoreBundle/Service/FlashBag.php:37-69 @7.x]

P7. `NotificationModel::addNotification()` is a no-op for guests, sanitises header/message with `strict_html`, and with a dedupe value skips duplicates newer than `-1 day` by default. [code: app/bundles/CoreBundle/Model/NotificationModel.php:79-120 @7.x]

P8. For admins the bell runs an update check at most once per hour per session unless `mautic.security.disableUpdates`. [code: app/bundles/CoreBundle/Model/NotificationModel.php:147-205 @7.x]

P9. `PathsHelper::getSystemPath()` resolves named paths (cache, logs, tmp, images, themes, plugins, …) from `app/config/paths_helper.php`. [code: app/bundles/CoreBundle/Helper/PathsHelper.php:63-259 @7.x]

P10. `EncryptionHelper` encrypts the serialized value with `secret_key` (AES-256-CBC + HMAC-SHA256 via `OpenSSLCipher`). [code: app/bundles/CoreBundle/Helper/EncryptionHelper.php:39-91 @7.x] [code: app/bundles/CoreBundle/Security/Cryptography/Cipher/Symmetric/OpenSSLCipher.php:9-83 @7.x]

P11. `ModeratedCommand` adds `--bypass-locking`, `--timeout`, `--lock_mode` (pid default, flock, redis) to cron commands; details in mautic-cron-and-queues. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-135 @7.x]

P12. The client IP is taken from the first valid forwarded header or `REMOTE_ADDR`, removing `do_not_track_internal_ips`; private ranges become `127.0.0.1` unless `track_private_ip_ranges`. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:65-121 @7.x] [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:213-258 @7.x]

## Q. Contradictions and open questions

Resolved in favour of code (docs are wrong or stale):
- Autowiring docs say `config.php` service definitions stop working in Mautic 6; 7.2.1 still processes them via `ServicePass`; removal happens in 8.x. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:33-75 @7.x] [PR #17470]
- "Mautic doesn't auto-wire native services other than commands and controllers" contradicts the autowiring page; code autowires every non-excluded class in `Config/services.php`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#autowired-services] [code: app/bundles/CoreBundle/Config/services.php:23-53 @7.x]
- Config file location: docs say `app/config/local.php`; the loader reads `config/local.php`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-configuration] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:195-216 @7.x]
- `trans()` docs say a missing key returns an empty string; the decorator delegates to Symfony, which returns the key. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#using-the-translator-service] [code: app/bundles/CoreBundle/Translation/Translator.php:42-49 @7.x]
- Permission bit list in docs skips 256; code uses 256 for `publishown`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#how-permissions-work] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:455-477 @7.x]
- Docs say `standard_entity` registers 5 methods; code registers 10 named endpoints. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#route-definitions] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:123-201 @7.x]
- MVC docs describe PHP templates (`$view['slots']`, `.html.php`); live templates are Twig under `Resources/views/`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#template-helpers] [code: app/bundles/CoreBundle/Resources/views/Default/content.html.twig:1-27 @7.x]
- 7.2 docs show `dispatch($eventName, $event)`; Symfony's signature is `dispatch($event, $eventName)`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#custom-events]

Open (code alone does not settle intent):
- `FormModel::setModifiedData()` leaves an existing `dateModified` untouched (D8). Intended or a bug? [code: app/bundles/CoreBundle/Model/FormModel.php:278-293 @7.x]
- `CoreEvents::FETCH_ICONS` is never dispatched by name; `IconEvent` is dispatched by class, so `CoreSubscriber::onFetchIcons` does not run for the recent-activity widget. [code: app/bundles/CoreBundle/EventListener/DashboardSubscriber.php:99-100 @7.x] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:45 @7.x]
- `RequestTrait::prepareParametersFromRequest()` sets `$masks['description'] = 'html'` in the branch that checks `content`, which looks like a copy/paste slip. [code: app/bundles/CoreBundle/Form/RequestTrait.php:163-166 @7.x]
- `CommonStatsSubscriber` checks `viewother` and then filters to the user's own rows; tests codify it. [code: app/bundles/CoreBundle/EventListener/CommonStatsSubscriber.php:67-90 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/EventListener/CommonStatsSubscriberTest.php:64-130 @7.x]
- `getViewDateRange()` uses `setTime(24, 59, 59)`, which yields 00:59:59 of the next day. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:785 @7.x]
