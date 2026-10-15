---
name: mautic-architecture
description: "How Mautic is built internally: the Symfony 7.4 / Doctrine stack, the mautic/mautic + mautic/core-lib layout and bundle map, dependency injection (Config/config.php, Config/services.php, autowiring, compiler passes), the event system (*Events.php constants in 7.x vs event classes in 8.x), the model save pipeline (AbstractCommonModel, FormModel, audit log), entities and repositories (CommonEntity, FormEntity, CommonRepository search syntax), CRUD controllers (AbstractStandardFormController, locks/checkout, AJAX actions, CSRF), permissions basics, translations, logging, error and offline handling, and admin UI JavaScript (Mautic.*, mQuery). Use whenever a task asks how Mautic works internally, where something lives or which bundle owns it, needs a new entity, model, controller, subscriber or AJAX action, or debugs a save that fires no events, an edit screen stuck 'locked', a CSRF failure, a missing translation or the 'site is offline' page, or touches app/bundles/CoreBundle/."
---
# Mautic architecture

## Scope
This skill explains the framework layer every Mautic feature sits on: the stack and package layout, how bundles are
assembled into the container, the event, model, entity, repository and controller conventions in CoreBundle, the
request lifecycle, translations, logging, error handling and admin UI JavaScript. Feature behaviour lives in the
feature skills (see Related skills); the full role/permission model is in mautic-users-and-permissions, building a
plugin end to end is in mautic-plugin-development, and the test harness is in mautic-testing.

## Expected behaviour (essentials)
Stack and layout
- Mautic 7.2.1 runs on PHP ~8.2, Symfony ~7.4, Doctrine ORM ^2.14 (2.20.9) and DBAL 3.7.x. [code: app/composer.json:15-105 @7.x]
- The repository root is the `mautic/mautic` project that requires `mautic/core-lib`; core-lib is the `app/` directory and autoloads `Mautic\` from `app/bundles/`, while the root autoloads `MauticPlugin\` from `plugins/`. [code: composer.json:23-27 @7.x] [code: composer.json:108-119 @7.x] [code: app/composer.json:7-16 @7.x]
- A bundle whose namespace contains `MauticPlugin\` is treated as a plugin and `Mautic\` as core; CoreBundle is always loaded first. [code: app/bundles/CoreBundle/DependencyInjection/Builder/BundleMetadataBuilder.php:55-81 @7.x]

Dependency injection
- Each bundle's `Config/config.php` declares routes, menus, parameters, legacy services and IP lookup services; `ServicePass` converts its `services` arrays into container definitions and auto-tags them (events→`kernel.event_subscriber`, forms→`form.type`, permissions→`mautic.permissions`, models→`mautic.model` with a deprecation). [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:33-63 @7.x]
- Registering the same legacy service name twice throws `InvalidArgumentException("<name> is already registered")`. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:66-68 @7.x]
- `Config/services.php` autowires and autoconfigures every class in the bundle except `MauticCoreExtension::DEFAULT_EXCLUDES` (which include `Security`, so permission classes are not autowired by the resource loader). [code: app/bundles/CoreBundle/Config/services.php:23-53 @7.x] [code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-29 @7.x]
- `ModelFactory::getModel('lead')` resolves `mautic.lead.model.lead`, `'lead.list'` resolves `mautic.lead.model.list`, a FQCN in the locator also works, and unknown keys throw `InvalidArgumentException`. [code: app/bundles/CoreBundle/Factory/ModelFactory.php:70-97 @7.x]
- Parameters resolve from bundle defaults, then `config/local.php`, then `config/parameters_local.php`, then the `MAUTIC_CONFIG_PARAMETERS` JSON env var; `db_driver` is always forced to `pdo_mysql`. [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:195-221 @7.x]

Events
- In 7.x events are dispatched by string names held in `*Events.php` constant classes (e.g. `CoreEvents::BUILD_MENU` = `mautic.build_menu`); subscribers key on those constants. [code: app/bundles/CoreBundle/CoreEvents.php @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#available-events]
- In 8.x almost every dispatch uses the event class as the name; `CoreEvents` no longer exists, and a subscriber keyed on a constant that still exists but is no longer dispatched silently never fires. [PR #17157] [PR #17183] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch]

Models and entities
- `FormModel::saveEntity($entity, $unlock = true)` runs `isNewEntity()`, `setTimestamps()`, hook `pre_save`, repository persist+flush, hook `post_save`, in that order. [code: app/bundles/CoreBundle/Model/FormModel.php:103-113 @7.x]
- `FormModel::dispatchEvent()` is a no-op in the base class; each bundle's model maps the string hooks (`pre_save`, `post_save`, `pre_delete`, `post_delete`, `pre_unpublish`, `on_toggle_publish`, batch variants) to its own events, so a model that does not override it fires no events at all. [code: app/bundles/CoreBundle/Model/FormModel.php:382-405 @7.x]
- The base model never writes the audit log; bundles' own post-save/post-delete subscribers call `AuditLogModel::writeToLog()`, which stores `*.*.*.*` when `anonymize_ip` is on. [code: app/bundles/CoreBundle/Model/AuditLogModel.php:34-64 @7.x]
- `saveEntities()` fires `pre_save` per entity, one `pre_batch_save`, flushes every 20 entities plus a final flush, then `post_save` per entity and one `post_batch_save`. [code: app/bundles/CoreBundle/Model/FormModel.php:133-174 @7.x] [code: app/bundles/CoreBundle/Tests/Unit/Model/FormModelTest.php:43-107 @7.x]
- `deleteEntities()` deletes every entity it can, skips those whose `pre_delete` event reports dependency errors, and then throws `DeleteEntitiesDependencyException` listing both groups. [code: app/bundles/CoreBundle/Model/FormModel.php:298-357 @7.x]
- On save, `dateModified` is set only when it is currently null, and `modifiedBy` only when the entity reports changes through `isChanged()`-tracking setters. [code: app/bundles/CoreBundle/Model/FormModel.php:243-293 @7.x]
- Cloning a `FormEntity` resets `dateAdded`, `checkedOut`, `createdBy` and changes, and sets `isPublished = false`. [code: app/bundles/CoreBundle/Entity/FormEntity.php:215-223 @7.x]
- Publish status is `unpublished` when the flag is off, `pending` before `publishUp`, `expired` at or after `publishDown`, else `published`; `isPublished()` on dated entities also requires a published (or no) category. [code: app/bundles/CoreBundle/Entity/FormEntity.php:233-251 @7.x] [code: app/bundles/CoreBundle/Entity/FormEntity.php:412-435 @7.x]
- All `datetime` columns are stored in UTC through `UTCDateTimeType` and read back into PHP's default timezone, which Mautic sets per request from the session `_timezone` or `default_timezone`. [code: app/bundles/CoreBundle/Doctrine/Type/UTCDateTimeType.php:17-71 @7.x] [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:20-40 @7.x]
- String fields and indexed fields mapped through `ClassMetadataBuilder` are forced to length 191 for utf8mb4. [code: app/bundles/CoreBundle/Doctrine/Mapping/ClassMetadataBuilder.php:370-396 @7.x]

Repositories and list search
- List search uses `command:value` syntax: `is:published`, `is:unpublished`, `is:uncategorized`, `is:mine`, `category:alias`, `ids:1,2,3`; `!` negates, `+` makes a value exact, quotes and parentheses group, `OR`/`AND` join clauses. [code: app/bundles/CoreBundle/Helper/SearchStringHelper.php:127-207 @7.x] [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1198-1284 @7.x]
- Search commands match in both the current locale and `en_US`, and an unknown `cmd:value` is searched as the literal text, not rejected. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1751-1822 @7.x]
- A command with no value (`is:` at the end) matches nothing (`1 = 0`). [code: app/bundles/CoreBundle/Helper/SearchStringHelper.php:136-140 @7.x] [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1803-1805 @7.x]
- `getEntities()` returns a Doctrine `Paginator` by default, so `count($result)` is the total across pages, not the page size. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:389-405 @7.x]

Controllers, locks and AJAX
- Opening an edit form (GET) checks the entity out to the current user; a GET by anyone else while it is checked out returns a "locked" flash and a redirect instead of the form. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:338-506 @7.x]
- "Save & Close" releases the lock and "Apply" keeps it. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:407 @7.x] [code: app/bundles/CoreBundle/Model/FormModel.php:245-249 @7.x]
- Locks never expire unless `max_entity_lock_time` (seconds) is non-zero; the "Override Lock" link appears only for users who can edit the entity. [code: app/bundles/CoreBundle/Model/FormModel.php:47-74 @7.x] [code: app/bundles/CoreBundle/Controller/AbstractFormController.php:71-136 @7.x]
- Delete and batch delete act only on POST. [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:107-171 @7.x]
- `/s/ajax?action=bundle:name` forwards to `{name}Action()` on `Mautic\{Bundle}Bundle\Controller\AjaxController` (`plugin:bundle:name` → `MauticPlugin`); unauthenticated calls or missing methods return `{"success":0}`. [code: app/bundles/CoreBundle/Controller/AjaxController.php:64-136 @7.x]
- Every XHR POST to a `/s/` path must carry header `X-CSRF-Token` for intention `mautic_ajax_post`; an invalid token gets HTTP 200 with a JSON `flashes` error and the controller never runs. [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:27-63 @7.x]
- `delegateView()` returns a full page for normal requests and JSON (`newContent`, `route`, `mauticContent`, `flashes`) for XHR requests. [code: app/bundles/CoreBundle/Controller/CommonController.php:218-278 @7.x]

Permissions, translation, logging, errors
- Permission strings are `bundle:name:level`; administrators are granted any well-formed string; results are memoised per string for the service lifetime. Detail: mautic-users-and-permissions. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:195-264 @7.x]
- Translations load from bundle `Translations/<locale>/*.ini`, then the theme's `translations/`, then downloaded packs, then `translations/overrides/<locale>/`; later files win, the file name is the domain, and `en_US` is always loaded first as the fallback. [code: app/bundles/CoreBundle/Loader/TranslationLoader.php:21-97 @7.x] [code: app/bundles/CoreBundle/Translation/TranslatorLoader.php:14-24 @7.x]
- The `mautic` log channel writes `var/logs/mautic_<env>.php`, rotating daily and keeping 7 files, at `notice` level unless `debug` is true or the env is `dev`. [code: app/bundles/CoreBundle/Monolog/Handler/FileLogHandler.php:12-25 @7.x]
- An uncaught exception outside AJAX in prod renders the "site is currently offline" page with HTTP 500 (or `custom_offline.html.twig` if present); AJAX/JSON requests get `{"errors":[...]}`. [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:156-181 @7.x] [code: app/bundles/CoreBundle/ErrorHandler/ErrorHandler.php:424-514 @7.x]

## Where it lives
| Concern | Path(s) |
|---|---|
| Stack, package layout | `composer.json`, `app/composer.json`, `app/AppKernel.php`, `index.php` |
| Bundle discovery, DI | `app/bundles/CoreBundle/DependencyInjection/` (`MauticCoreExtension`, `Compiler/*Pass.php`, `Builder/BundleMetadataBuilder.php`), each bundle's `Config/config.php` and `Config/services.php` |
| Core events | `app/bundles/CoreBundle/CoreEvents.php`, `app/bundles/CoreBundle/Event/` |
| Base model | `app/bundles/CoreBundle/Model/AbstractCommonModel.php`, `FormModel.php`, `AuditLogModel.php`, `Factory/ModelFactory.php` |
| Base entity, mapping | `app/bundles/CoreBundle/Entity/CommonEntity.php`, `FormEntity.php`, `Doctrine/Mapping/ClassMetadataBuilder.php`, `Doctrine/Type/` |
| Base repository, search | `app/bundles/CoreBundle/Entity/CommonRepository.php`, `Helper/SearchStringHelper.php` |
| Controllers | `app/bundles/CoreBundle/Controller/CommonController.php`, `AbstractFormController.php`, `AbstractStandardFormController.php`, `AjaxController.php`, `ExceptionController.php` |
| Request listeners | `app/bundles/CoreBundle/EventListener/` (`EnvironmentSubscriber`, `RouterSubscriber`, `RequestSubscriber`, `ExceptionListener`, `CoreSubscriber`) |
| Permissions | `app/bundles/CoreBundle/Security/Permissions/` (`CorePermissions`, `AbstractPermissions`) |
| Translations | `app/bundles/CoreBundle/Loader/TranslationLoader.php`, `Translation/`, `app/bundles/*/Translations/en_US/*.ini` |
| Logging, errors | `app/bundles/CoreBundle/Monolog/`, `ErrorHandler/ErrorHandler.php`, `Resources/views/Offline/` |
| Admin UI | `app/bundles/CoreBundle/Resources/views/`, `Assets/js/*.js`, `Helper/AssetGenerationHelper.php` |
| Parameters | `app/bundles/CoreBundle/Config/config.php:249-812`, `Loader/ParameterLoader.php`, `Helper/CoreParametersHelper.php` |
| Tests | `app/bundles/CoreBundle/Tests/{Unit,Functional}/`, base classes in `app/bundles/CoreBundle/Test/` |

Bundle-by-bundle ownership: references/bundle-map.md. Full map: references/code-map.md.

## How to change or extend it
- New entity: extend `FormEntity`, map it in a static `loadMetadata()` with `ClassMetadataBuilder`, and make setters call `isChanged()` so `modifiedBy` and audit details work. [code: app/bundles/CoreBundle/Entity/CommonEntity.php:63-137 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#entity-php-static-function-mapping]
- New repository: extend `CommonRepository`, override `getTableAlias()`, return `getStandardSearchCommands()` from `getSearchCommands()` to get `is:published` and friends, and override `addCatchAllWhereClause()`/`addSearchCommandWhereClause()` for custom columns. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:707-789 @7.x]
- New model: extend `FormModel`, override `getRepository()`, `getPermissionBase()`, `createForm()` and `dispatchEvent()`; without `dispatchEvent()` nothing downstream (audit log, webhooks) sees saves. [code: app/bundles/CoreBundle/Model/FormModel.php:370-405 @7.x]
- New CRUD screen: extend `AbstractStandardFormController`, implement `getModelName()`, call the `*Standard()` methods, and ship `form.html.twig` and `details.html.twig` (only `list.html.twig` has a core fallback). [code: app/bundles/CoreBundle/Controller/AbstractStandardFormController.php:679-693 @7.x]
- New AJAX action: add `fooAction(Request $request): JsonResponse` to your bundle's `AjaxController extends Mautic\CoreBundle\Controller\AjaxController` and call `action=bundle:foo`. [code: app/bundles/CoreBundle/Controller/AjaxController.php:77-136 @7.x]
- Prefer `Config/services.php` with autowiring over `config.php` `services` arrays; 8.x no longer reads the `services` group. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#introducing-services-php] [PR #17470]
- Subscribe to event classes where they exist, and register the 7.x constant as a second key guarded by `defined()` when the code must run on both 7.x and 8.x. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch] [PR #17157]
- Core bundles must keep string service aliases for backward compatibility; plugins may switch to FQCN service ids in a major release. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#consider-backward-compatibility-for-services]
- Any schema change needs a migration under `app/migrations/` (core) or a plugin migration; update the entity, migration, API serializer groups and `en_US` translations together. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations] [code: app/bundles/CoreBundle/Entity/FormEntity.php:17-92 @7.x]
- New user-facing strings go into `Translations/en_US/<domain>.ini`; every bundle and plugin must ship `en_US`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#translation-file-and-directory-structure]
- Do not override core classes from a plugin; contribute the missing hook to core instead. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/getting_started.html]

## How to test it
- Unit tests extend `PHPUnit\Framework\TestCase`; functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`, which installs the schema once, logs in `admin` and rolls each test back. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:24-152 @7.x]
- Use `$this->client->xmlHttpRequest()` plus `setCsrfHeader()` or `createAjaxHeaders()` for AJAX POSTs. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:172-198 @7.x]
- Copy from: `app/bundles/CoreBundle/Tests/Unit/Model/FormModelTest.php` (hook order), `Tests/Functional/Entity/CommonRepositoryTest.php` (search commands), `Tests/Unit/Helper/SearchStringHelperTest.php` (parser), `Tests/Unit/EventListener/RequestSubscriberTest.php` (CSRF matrix), `Tests/Functional/Controller/AjaxControllerTest.php` (AJAX and permissions), `Tests/Functional/DependencyInjection/` smoke tests (every subscriber/command can be built). [code: app/bundles/CoreBundle/Tests/ @7.x]
- A good regression test asserts the observable result: the event that fired (or the audit-log row), the HTTP status and JSON keys of an AJAX call, the rows a search string returns, or the lock state after a GET/Apply/Save. Detail: references/test-patterns.md.

## Version notes
- Mautic 5 added autowiring/autoconfigure, moved `local.php` to `config/local.php`, and required Twig views. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html]
- 7.0 deprecated `UuidTrait::isValidUuid()`; 7.2 deprecated several string service aliases (`mautic.helper.encryption`, `mautic.core.service.flashbag`, `mautic.route_loader`, ...) and made `uri`-only menu items render. [code: app/bundles/CoreBundle/Entity/UuidTrait.php:33-43 @7.x] [code: app/bundles/CoreBundle/Config/services.php:189-190 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-definitions]
- 8.x: PHP 8.4, Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4, PHPUnit 13; dispatch by event class; `CoreEvents` removed; `ServicePass`, `ModelPass`, `PermissionsPass`, `TwigPass` and the `config.php` `services` group removed; `FormController` removed; core routes become `#[Route]` attributes while plugins keep `config.php` routes. [PR #16993] [PR #17392] [PR #17361] [PR #17004] [PR #17157] [PR #17116] [PR #17133] [PR #17121] [PR #17117] [PR #17470] [PR #17481] [PR #17169]
- Full detail: references/version-notes.md.

## Pitfalls
- A custom model that does not override `dispatchEvent()` saves fine but fires no events, writes no audit log and triggers no webhooks. [code: app/bundles/CoreBundle/Model/FormModel.php:382-405 @7.x]
- `dateModified` is not refreshed on later saves through the base model once it has a value; bundles that need it call `setDateModified()` themselves. Whether this is intended is an open question. [code: app/bundles/CoreBundle/Model/FormModel.php:278-293 @7.x]
- A CSRF failure on an AJAX POST is HTTP 200, not 403; check the `flashes` key in the JSON. [code: app/bundles/CoreBundle/EventListener/RequestSubscriber.php:34-63 @7.x]
- `CorePermissions::isGranted()` caches by permission string and ignores a different `$userEntity` argument later in the same request. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:210-213 @7.x]
- Passing `ignore_paginator` to `getEntities()` makes `count()` return the page size, so list totals break. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:389-405 @7.x]
- `DateTimeHelper::getLocalDateTime()`/`getUtcDateTime()` mutate the wrapped object, while `toLocalString()`/`toUtcString()` do not. [code: app/bundles/CoreBundle/Helper/DateTimeHelper.php:101-150 @7.x]
- Every form built on `AbstractFormStandardType` HTML-escapes all fields except `description` (strict HTML); allow raw HTML explicitly with a `clean_masks` entry. [code: app/bundles/CoreBundle/Form/Type/AbstractFormStandardType.php:40-44 @7.x]
- `CoreEvents::FETCH_ICONS` is never dispatched by name; `DashboardSubscriber` dispatches `IconEvent` by class, so `CoreSubscriber::onFetchIcons` does not run for it (open question: regression or intended). [code: app/bundles/CoreBundle/EventListener/DashboardSubscriber.php:99-100 @7.x] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:45 @7.x]
- Docs say `config.php` service definitions "won't work in Mautic 6"; in 7.2.1 `ServicePass` still processes them (removed only in 8.x). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:33-75 @7.x]
- Docs say configuration is written to `app/config/local.php`; since 5.x the loader reads `config/local.php`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-configuration] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:195-216 @7.x]
- Docs say `trans()` returns an empty string for a missing key; Mautic's decorator delegates to Symfony, which returns the key itself, and only retries with locale `EN` on an `InvalidArgumentException`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#using-the-translator-service] [code: app/bundles/CoreBundle/Translation/Translator.php:42-49 @7.x]
- The 7.2 custom-event docs pass `($eventName, $event)` to `dispatch()`; Symfony's order is `dispatch($event, $eventName)`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#custom-events]
- `track_private_ip_ranges = false` (default) records 10.x/192.168.x visitors as `127.0.0.1`. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:213-222 @7.x]
- A crashed prod asset generation leaves `media/generation_in_progress.txt` behind and every request spin-waits on it. [code: app/bundles/CoreBundle/Helper/AssetGenerationHelper.php:121-123 @7.x]

## Related skills
- mautic-overview: product concepts and glossary before diving into code.
- mautic-users-and-permissions: role bits, synonyms, implied levels, own/other checks, API users.
- mautic-plugin-development: building a plugin bundle end to end (structure, migrations, integrations hooks).
- mautic-configuration: parameters, `local.php`, env vars, the Configuration UI, cache adapters.
- mautic-cron-and-queues: `ModeratedCommand` locking, cron commands, Messenger transports.
- mautic-testing: test kernel, `MauticMysqlTestCase`, fixtures, Codeception.
- mautic-dev-environment: DDEV, asset build, `bin/console` usage.
- mautic-contributing: coding standards, PHPStan/Rector, PR norms.
- mautic-upgrades-and-versions: platform upgrades and the 7.x to 8.x porting guide.
- mautic-troubleshooting: logs, offline page, cache and permission diagnosis.
- mautic-rest-api: API controllers, serializer groups, `standard_entity` routes.
- mautic-theme-development: Twig templates, `themes/system` overrides, builder.
- Feature skills (mautic-contacts, mautic-segments, mautic-campaigns, mautic-emails, mautic-forms, mautic-pages-and-tracking, mautic-assets-categories-projects, mautic-points-and-stages, mautic-reports-and-dashboard, mautic-channels, mautic-webhooks, mautic-integrations): bundle-specific behaviour; see references/bundle-map.md.

## Reference files
- references/behaviour.md — numbered behaviour specification for the framework layer, every item cited; open before changing or testing base classes.
- references/bundle-map.md — one row per core bundle and plugin: purpose, key entities/tables, owning skill.
- references/code-map.md — classes, events, listeners, compiler passes, routes, parameters, commands and tests by path.
- references/docs-digest.md — what devdocs say about MVC, Mautic vs Symfony, services, events, translations and UI design, with URLs and discrepancies.
- references/test-patterns.md — base classes, helpers, representative tests and skeletons for framework-level tests.
- references/version-notes.md — 5.x/6.x history, 7.x minors and the 8.x delta for the framework layer.
- references/pr-history.md — not yet generated; PR-derived history is added in a later pass.
