# Mautic architecture: pull-request history

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
3. Removed, deprecated, replaced
4. Regression catalogue
5. Feature timeline
6. Platform requirements timeline
7. Maintainer norms for this area
8. Conflicts resolved against the code
9. Open questions
10. Coverage

## 1. How to read this file
Source: merged pull requests on mautic/mautic for the framework layer (core-platform and core-foundation buckets), harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; "unreleased 7.x" means merged on `7.x` after 7.2.1 (milestone 7.3.0-rc), and "8.0 only" means merged on `8.x`.
Current behaviour is specified in `behaviour.md`, which is code-verified and wins on any conflict; this file explains why and when.

## 2. Decisions that shaped current behaviour

### DI, services and autowiring
- Bundle `config.php` service definitions gained the full Symfony `Definition` feature set (factory, lazy, decorated). [PR #1224] (v1.2.3)
- Tagged services are collected by compiler passes, not instantiated in `boot()`: configurator steps [PR #1185] (v1.2.3), permissions through `PermissionsPass` [PR #7312] (v3.3), pre-update checks tagged `mautic.update_check` [PR #10459] (v4.2), SMS transports [PR #5983], URL shorteners [PR #12299] (v5.0).
- From 7.2.0 consuming constructors use `#[AutowireIterator]` instead of a dedicated compiler pass. [PR #16776] (v7.2) The shortener service is an example on 7.x. [code: app/bundles/CoreBundle/Shortener/Shortener.php:20-28 @7.x]
- `EventPass` passes a reference to the shared `mautic.parameters` array instead of copying it into every listener, which made the container about 1.5 MB smaller. [PR #6923] (v2.15.1, historical 2.x container)
- Merging bundle config must not silently overwrite service tags. [PR #4887] (v2.10.1)
- Mautic 4 made services public and auto-registered commands as explicit stopgaps for Symfony 4. [PR #9409] (v4.0)
- Commands take dependencies through the constructor; about 30 commands were refactored. [PR #11041] (v5.0)
- Autowiring arrived in 5.0: `app/config/services.php` applies `autowire()`/`autoconfigure()` to every bundle and plugin directory, excludes DTOs, events and exceptions, and lets a bundle ship its own `Config/services.php`. [PR #11587] (v5.0)
- Services that hold state must be instantiated once; a second `AssetsHelper` instance broke GrapesJS during the autowiring move. [PR #11587] (v5.0)
- Controllers receive dependencies through the constructor; `initialize()` and `CoreSubscriber` injection were removed. [PR #12412] (v5.0)
- Models are autowired and can be fetched by class; long constructor lists are accepted because they expose models that do too much. [PR #12493] (v5.0)
- DataTransformers are autowired services with typed data, and FormTypes carry PHPStan `@template TData` generics. [PR #13130] [PR #13085] (v5.1)
- In 7.2 services moved from `config.php` arrays to `Config/services.php` for Core, Campaign, Form, Lead, Sms and Page with a custom Rector rule. [PR #16812] [PR #16813] [PR #16818] [PR #16843] (v7.2)
- Dropping the old string IDs in that move broke plugins, so they were restored as aliases marked `->deprecate('mautic/mautic', '7.2', …)`. [PR #17251] (v7.2.1) [code: app/bundles/CoreBundle/Config/services.php:189-190 @7.x]
- Legacy string service IDs are public plugin API and can be removed only in a major. [PR #17251] [PR #11587]
- A subscriber must not also be tagged `kernel.event_listener`, because autoconfiguration already tags it; `ExceptionListener` ran twice per exception until fixed. [PR #16879] (v7.2)
- A container smoke test instantiates every registered service (about 3,965) with a `TestKernel` that needs no database or Redis, because hand-wired services broke silently after constructor changes; new subscribers should be covered by it. [PR #16747] [PR #16843] [PR #16879] [PR #17781] (v7.2)
- Test-only commands and services are registered only in the `test` environment through `TestPass`; `mautic:phpunit:config` broke production updates to 7.1 until this was done. [PR #16104] (v7.1.2)
- Test HTTP clients follow the same pattern: `MockHttpClient` replaces `http_client` in test config [PR #12579] [PR #12615] (v5.0), and Guzzle is mocked through `ClientMockTrait` [PR #15472] (v7.0).
- `CommonRepository` receives the translator through a `#[Required]` method, `autowireCommonRepository()`, so hand-built repositories in unit tests must call it. [PR #16979] (v7.2)
- The Mautic logger is injected through the constructor or an autowire method, not as a controller action argument. [PR #16985] (v7.2)
- DI extensions extend `Symfony\Component\DependencyInjection\Extension\Extension`, because the HttpKernel variant is internal since Symfony 7.1. [PR #16540] (v7.2)
- Stateless services are declared `readonly` where possible. [PR #16417] (v7.2)
- Generic infrastructure that only plugins need is accepted into core: `UuidInterface`/`UuidTrait` [PR #10883] (v4.3), upsert [PR #11654] [PR #11746], `SimplePaginator` [PR #11444] (v5.0), full-text indexes [PR #9335] (v4.3).
- `CommandHelper`/`CommandResponse` let core run console commands programmatically. [PR #10405] (v4.2)

### MauticFactory, ModelFactory and the container-by-name ban
- MauticFactory was injected through setter `methodCalls` [PR #532] and exposed bundle config [PR #175]; it was deprecated around 2.1.1, when the common model got its logger through `setLogger`. [PR #2228] (v2.1.1)
- In 3.0 the factory was removed from `AbstractCommonModel` and `FormModel`, and deprecated CoreBundle code was swept. [PR #8207] [PR #8104] (v3.0)
- In 6.0 its methods were removed one at a time: [PR #14399] [PR #14400] [PR #14435] [PR #14462] [PR #14463] [PR #14464] [PR #14494] [PR #14564] (v6.0). The class itself was deleted in 7.0; see section 8. [code: UPGRADE-7.0.md:16 @7.x]
- `ModelFactory::getModel($name)` is only for models chosen at runtime (a stored channel or source name); it must not become "MauticFactory all over again". [PR #2542] (v2.2) From 5.0 it also accepts a class name. [PR #12493] (v5.0)
- `getModel()` has a PHPStan conditional return type mapping keys to classes as an interim step; the stated goal is to remove `getModel('x')` in favour of typed injection. [PR #16543] [PR #16624] (v7.2)
- Fetching services by string (`$this->get('…')`, `$this->container->get('…')`) is being removed from app and plugin code; a custom PHPStan rule enforces it, and tests are exempt. [PR #16737] [PR #16771] (v7.2)
- `CoreParametersHelper::getParameter()` was removed in favour of `get($name, $default)`; it was deprecated since 3.0 but the removal waited for a major. [PR #13837] (v6.0)
- Narrow purpose-specific services are preferred over generic factories: `SchemaHelperFactory` [PR #5834] became `TableSchemaHelper`/`IndexSchemaHelper`/`ColumnSchemaHelper` [PR #8456] (v3.0), and `BuilderTokenHelper` is built by `BuilderTokenHelperFactory` [PR #8204] (v3.0).

### Kernel, bundles, config and paths
- `BundleMetadataBuilder` and the `*Metadata` classes replaced inline `app/config/config.php` bundle logic. [PR #8466] [PR #8578] (v3.0)
- Config values may reference environment variables: first `getenv(KEY)` [PR #1025] (v1.2.1), then the 3.0 `ParameterLoader`, where most `local.php` changes need no cache clear [PR #8449] (v3.0). The `int-nullable` env processor lets null integers through. [PR #8580] (v3.0)
- Values derived from `local.php` never override values already set by `.env`, `.env.local` or the system environment; the loader refreshes only keys it populated itself. [PR #17072] (v7.2)
- For recommended-project installs, the webroot is auto-detected from `composer.json` and `local_root` is set automatically; `PathsHelper` resolves themes, media, plugins, assets, images and translations from it. [PR #17023] (v7.2)
- AssetMapper compiles into the resolved webroot, not `<project>/public`, through `AssetMapperWebRootPass`. [PR #17300] (v7.2.1)
- `Configurator::renderArray()` writes `local.php` with single quotes so `$` is not interpolated [PR #6737] (v2.14.2); quotes are escaped [PR #2270] and numeric-string keys preserved [PR #1761].
- Null config defaults used as arrays default to `[]`. [PR #1135]
- Middlewares in `app/middlewares` are compiled to `middlewares.cache.php` at `cache:warmup`. [PR #8475] (v3.0) Examples are `IpRestrictMiddleware` for `index_dev.php` with `dev_hosts` set only in local.php [PR #1937] (v2.1) and `HSTSMiddleware` [PR #11608] (v5.0).
- `%kernel.root_dir%` was replaced by `%kernel.project_dir%`. [PR #11145] (v5.0) `tmp_path` defaults under `%kernel.project_dir%/var/tmp`. [PR #2757]
- Paths are never CWD-relative; error templates are anchored to the install root for cPanel PHP-FPM. [PR #16155] (v7.1.3)
- `PathsHelper` creates missing temp and dashboard-import directories [PR #13415] (v5.1), and theme ZIPs are built in the temp path, not the cache [PR #13483] (v5.1).
- Application-shipped files live in `app/assets` and `media/` holds instance content; a same-path file in `media/` overrides through `AssetsHelper::getOverridableUrl()`. [PR #10682] (v5.0)
- AppKernel version constants were replaced by `ThisRelease::getMetadata()` and `app/release_metadata.json`, which carries PHP and database limits per release. [PR #8449] (v3.0) [PR #10459] (v4.2) `show_php_version_warning_if_under` is optional [PR #9594] [PR #9622]; suffixed versions `X.Y.Z-label` are allowed [PR #10919] (v4.3).
- `themes/system/` overrides any core Twig template through `SystemThemeTemplatePathPass`, restoring Mautic 4 behaviour; a Twig `system` namespace was rejected because it would change every template reference. [PR #13590] (v5.1)
- Config fields removed by `security.php` restrictions must be rendered conditionally; never call `form_row()` on a field that may be absent. [PR #15912] (v7.2.0)
- Trusted hosts are validated on save, so a bad pattern is a form error, not a 500. [PR #16006] (v7.1.1)
- `mautic:motd` runs on Composer hooks and DDEV start [PR #15970] (v7.1) and always exits 0, because non-essential Composer hooks must not block installs [PR #16226] (v7.2.0).
- The "Support Mautic" menu item is hidden only through `support_mautic_enabled`; making it user-dismissible was rejected. [PR #16337] (v7.2)
- New shared features go into CoreBundle "following the usual practice" rather than a new bundle; the Privacy Centre (`gravatar_enabled`, default false) lives in CoreBundle and no PrivacyBundle exists. [PR #17781] (unreleased 7.x) [code: app/bundles/CoreBundle/Config/config.php:265 @7.x]
- Only code shared by more than one bundle belongs in CoreBundle. [PR #4123]

### Request lifecycle, routing, errors and logging
- The admin UI is secured under `/s/`; pages, tracking and form submits live outside it. [PR #70] (v1.0)
- `objectId` accepts only `[a-zA-Z0-9_]+` [PR #720] (v1.2); `-` was added for theme names because renaming themes would have been a BC break [PR #5548] (v2.12.2).
- The URL generator always uses `site_url`, so cached forms carry the right action URL. [PR #7193] (v2.15.2) That broke `index_dev.php` and subdirectory installs, fixed in [PR #7457] and [PR #7572] (v2.15.2). Originally CLI only: [PR #151] (v1.0).
- Links generated in subrequests use `site_url` because `RouterSubscriber` reapplies it after Symfony restores the parent context. [PR #17168] (v7.2.0)
- A kernel-request subscriber applies the user's locale and timezone [PR #2352]; its priority was fixed after timestamps showed in UTC [PR #2397] (v2.2). The user preference overrides the system locale. [PR #11119] (v4.4.1)
- `EnvironmentSubscriber` sets PHP's default timezone from the session user and pushes it into `DateTimeHelper::setLocalTimezone()` on each authenticated request. [PR #17627] (v7.2.2) [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:20-40 @7.x]
- API and OAuth routes are always registered and a disabled API returns 403 at runtime [PR #1025] (v1.2.1); enabling the API needs no cache clear [PR #11420] (v4.4.2).
- Core helpers that run on every page must not touch the database before install. [PR #10372] (v4.0)
- Errors go to Mautic's Monolog log with daily rotation [PR #721] (v1.2); 40x responses are not logged [PR #2881] [PR #3421] (v2.3, v2.6.1).
- Error pages return HTTP 500 [PR #4629] and API errors carry the real status code [PR #6545].
- Exception logs carry context and trace [PR #7465]; console errors are logged at `error` with a trace [PR #11656] (v5.0); every record has `hostname` and `pid` [PR #11121] (v4.3) merged into `extra` [PR #12835] (v5.1).
- The offline page started as static PHP with a `custom_offline.php` override [PR #203] and became the Twig `Offline/offline.html.twig` rendered by `ErrorHandler` [PR #12101] (v5.0).
- `symfony/debug` was replaced by `symfony/error-handler`. [PR #11143] [PR #12235] (v4.3, v5.0)
- Menus are built from the `config.php` `menu` key [PR #1115] (v2.0) with per-item priority [PR #1659], each menu in isolation [PR #2340] [PR #2906]; URI-only items render [PR #16337] (v7.2).
- Updating is CLI-only from 7.0; `/s/update` and `UpdateController` were removed. [PR #14689] (v7.0) The chain: web/CLI updater [PR #682] [PR #855] → GitHub releases with `mautic:update:apply --finish` [PR #8449] (v3.0) → pre-update checks [PR #10459] (v4.2) → UI updater notice for Composer installs [PR #10907] (v4.2).
- A newer release stays visible on an old PHP version and fails at the pre-update check with a reason. [PR #10459] (v4.2)

### Doctrine, entities, repositories and migrations
- Entities declare static `loadMetadata` through `ClassMetadataBuilder` instead of annotations, because annotations generated about 800 cache files. [PR #229] (v1.1)
- All entities use DEFERRED_EXPLICIT change tracking: `persist()` before `flush()`, and `saveEntity()` flushes only that entity. [PR #1221] (v1.2.3) `CommonRepository::clear()` was removed in favour of entity-manager detach and clear. [PR #12354] (v5.0)
- Repository where-clauses are additive [PR #281], values are always bound as parameters [PR #2281], `IN` binds array parameters [PR #3209], and parameter names do not accumulate across batches [PR #9299] (v4.0).
- The published expression is "publish up null or ≤ now, and publish down null or ≥ now" [PR #280]; publish up uses `<` now so an item is published from that minute [PR #2041] (v2.1).
- Published-date helpers are split: `getPublishedByDateOrmExpression()` returns an ORM `Andx` and `getPublishedByDateDbalExpression()` a DBAL `CompositeExpression`. Originally [PR #16505] switched ORM to `and()`/`or()`, which broke API-library CI on ORM 2.20.9; changed by [PR #16970] (v7.2).
- The custom `ArrayType` cleans UTF-8 [PR #517], guards null bytes [PR #1437], returns `[]` on unserialize failure [PR #2177] (v2.1.1) and strips null bytes before unserialize [PR #8704] (v3.0). `Serializer` rejects only real serialized-object patterns. [PR #8266] (v2.16.0)
- New installs use utf8mb4 with 191-character indexed VARCHARs, with no migration for existing installs. [PR #8349] (v3.0) Native characters are stored, so `EmojiToShortTransformer` was removed. [PR #12483] (v5.0)
- Queries must pass `ONLY_FULL_GROUP_BY` [PR #2074] [PR #5761] and work on MySQL 8.0.16+ [PR #8455].
- Schema changes ship a Doctrine migration that tolerates drift [PR #1884]; use `doctrine:migrations:generate` with `app/migrations/Migration.template` [PR #8429] (v3.0).
- Generated columns (`email_stats.generated_sent_date` first) made charts about 3.5× faster [PR #7094] (v3.1). Generated-column migrations run after regular migrations through `MigrationCommandSubscriber`, because running them first caused outages. [PR #13455] (v5.1) Stored generated date columns for stats are MySQL-only; MariaDB keeps `DATE_FORMAT(CONVERT_TZ())`. [PR #15621] (v7.1)
- Install fixtures are services in `group_install` [PR #8366] (v3.0). Indexes are declared in metadata, never as DDL in fixtures [PR #10787] (v4.2), and schema DDL runs before fixture inserts [PR #11701] (v5.0).
- `db_host_ro` enables a primary/read-replica connection wrapper. [PR #11792] (v5.0)
- DBAL 2.13 → 3.6 and ORM were upgraded together because of circular dependencies [PR #12396] (v5.0); use `executeStatement`/`executeQuery` [PR #12294] and no deprecated calls [PR #13113] (v5.1).
- `pdo_mysql` is the only driver: a compiler pass fails the cache build with a readable message if it is missing. Originally `mysqli` was the default so the installer booted without PDO [PR #710] (v1.2); changed by [PR #13210] (v5.0.2).
- All datetimes are stored in UTC and converted for display: [PR #4456] [PR #9747] [PR #2011] [PR #12248]; `UTCDateTimeImmutableType` [PR #13127] (v5.1). A display-timezone change [PR #6850] was reverted by [PR #7433] and redone in [PR #7752] (v2.15.2).
- `DateTimeHelper` "local" means `default_timezone` [PR #12116] (v5.0); helpers are side-effect free [PR #10375] (v4.2.1) and clone before converting [PR #17091] (v7.2.0).
- Optimistic locking is Mautic-controlled and opt-in: `OptimisticLockInterface` entities carry a version and `AbstractStandardFormController` checks the submitted version. Doctrine's native `@Version` was rejected as "too dangerous" because its exception could surface in unrelated paths. [PR #13659] (v5.1) The campaign event log used it for at-most-once execution [PR #15348] (v7.0), and the builder refreshes the version after each Apply [PR #15894] (v7.1).
- `SkipModifiedInterface` lets an entity skip modified-by tracking in `FormModel::saveEntity()`; `Lead` uses it so DNC-only saves do not update `leads`, which avoided deadlocks. [PR #13994] (v5.2) [code: app/bundles/CoreBundle/Model/FormModel.php:269-271 @7.x]
- `CommonRepository::upsert()` sets the entity ID from `LAST_INSERT_ID(id)` on duplicate-key updates. [PR #14482] (v5.2.2)
- `FormModel::saveEntities()` dispatches `pre_batch_save`/`post_batch_save`. [PR #14503] (v6.0)
- `FormEntity` change tracking compares by value [PR #7311], a `dateLastActive`-only change writes no audit row [PR #1202], and a `last_active`-only change does not bump `date_modified` [PR #12026].
- A clone gets `createdBy` = the cloner [PR #11528] (v4.4.4).
- `TranslationEntityInterface`/`Trait` and `TranslationModelTrait` are a shared CoreBundle mechanism; the interface change counted as a BC break and went into 7.0. [PR #15481] (v7.0)
- `iterator_mode` was removed from `CommonRepository::getEntities()` as a BC break. [PR #14896] (v7.0)
- `ImportEntityDenormalizer` maps snake_case export keys to properties, because Symfony's denormaliser drops unknown keys silently. [PR #17226] (v7.2.0)
- 8.0 only: use `ClassMetadata`, not `ClassMetadataInfo`, and `getEntityManager()`, not `$_em`. [PR #17359] [PR #17392]

### Templating: PHP to Twig, extension hooks
- The historical override order was `themes/system/<Bundle>` → theme → bundle views → plugin views. [PR #201] [PR #282]
- Twig became first-class alongside PHP templates in 4.3 [PR #10129] (v4.3); every `.html.php` file was deleted in 5.0 [PR #12046], and `TemplatingHelper`, `PhpEngine`, `TemplateNameParser`, `TemplateReference` and `TemplatingPass` were removed [PR #12122] [PR #12124] [PR #12130] [PR #12134] [PR #12136] [PR #12140] (v5.0).
- Unused templates were deleted rather than ported. [PR #12011] [PR #12013] [PR #12014]
- Twig rules: `@Bundle/...` names [PR #12134]; base → layout → concrete inheritance [PR #11953]; tests expect escaped output [PR #11953]; embedded controllers use FQCN `::method` [PR #12161]; third-party bundle overrides go in `templates/bundles/<Bundle>/` [PR #12209].
- `Standard/list.html.twig` stays as the fallback for `AbstractStandardFormController`; its removal [PR #12006] was reverted by [PR #12021] (v5.0).
- `VIEW_INJECT_CUSTOM_TEMPLATE` was restored for Twig [PR #12924] (v5.0), dispatched for AJAX responses [PR #13580] (v5.1), and fixed again through `CommonController::eventAwareRenderView` after being reported broken since 5.0 [PR #14434] (v5.2.2). [code: app/bundles/CoreBundle/Controller/CommonController.php:197-205 @7.x]
- `VIEW_INJECT_CUSTOM_CONTENT` accepts several templates per type [PR #7307]; `mauticTemplateVars` were restored [PR #13257] (v5.0.3), then replaced by Twig `_context` [PR #13670] (v5.1), and AJAX updates send the correct `viewName` [PR #14437] (v5.2.2).
- `OverrideIncludeExtension::includeWithEvent()` returns `string|Twig\Markup` unchanged: a cast to string [PR #16487] would double-escape and made every page 500 on Twig ≥3.28, fixed by [PR #16741] (v7.2). Pinning Twig back was rejected because of security advisories.
- Uploaded `@themes` templates render in a Twig sandbox that delegates runtimes to the main environment so `purify` works [PR #16238] (v7.2.0); Mautic's own `map`/`filter`/`reduce`/`sort`/`find` denylist was dropped for Twig's built-in checks [PR #17620] (v7.2.2).
- Plugin- or user-fillable HTML in labels and help goes through `purify`, never `raw`. [PR #13535] [PR #13536] (v5.1) `purify_allow_target_blank` keeps `target="_blank"` only for labels and help. [PR #15298] (v7.0)
- A theme's `error_<code>.html.twig` overrides error pages. [PR #13266] (v5.1)
- A new Twig function used by themes is a BC break for those themes (`getRoundedCorners` needs `mautic/core-lib >=7.0`). [PR #14657] (v7.0)
- Twig extensions use first-class callables and native `array` returns. [PR #16409] [PR #16416] [PR #16541] [PR #16560] [PR #16561] (v7.2)
- Shared templates stay generic and take context-specific labels at include time. [PR #15243] [PR #16517] (v7.0, v7.2)
- Production Twig keeps `auto_reload` on, so theme edits apply without a cache clear. [PR #3571]

### Shared form layer and controller conventions
- `CommonController::executeAction` forwards through the ArgumentResolver, so action parameter names must match route attribute names. [PR #12837] [PR #12847] (v5.0) Internal `editAction`/`newAction` calls pass `Request` first. [PR #12719] [PR #12772] (v5.0)
- A clone save checks create permission [PR #6238], a locked entity redirects to its own view [PR #6506], any user with edit permission can unlock [PR #2291] [PR #3604], and `max_entity_lock_time` defaults to 0, never expiring [PR #3549] (v2.9). [code: app/bundles/CoreBundle/Config/config.php:708 @7.x]
- Symfony upgrade rules: FQCN form types [PR #8237]; choice arrays map label → value after `choices_as_values` went [PR #8248] (v3.0); check `isSubmitted()` before `isValid()` [PR #9847]; `getBlockPrefix()` [PR #9303].
- `RequestTrait` normalises booleans (unknown values become NULL [PR #10866] (v4.2)), leaves values unchanged on null [PR #4609], unwraps single-element arrays [PR #5366], and clears a multiselect on an empty string [PR #9506].
- `EntityLookupChoiceLoader` keeps the selected choices [PR #4245], loads the selection beyond the first 100 [PR #12644] (v5.0), supports `model_key` [PR #12875] and tolerates null-ID clones [PR #15562] (v7.1). `AjaxLookupControllerTrait` is guarded by a test. [PR #12652]
- `CustomFormEvent` exposed the FormBuilder [PR #6120] (v2.14), was deprecated [PR #11037] (v4.3) and removed [PR #11632] (v5.0).
- The `EntityEvent` constraint dispatches `EntityValidateEvent` so plugins can add violations; core registers no listeners. [PR #13812] (v5.1)
- Core form types hold no cross-bundle knowledge; variation goes behind an `OptionsResolver` option. [PR #14650] (v6.0)
- Inapplicable fields are disabled and cleared, not just hidden (`data-enable-on`/`data-disable-on`). [PR #14221] (v5.2) [PR #14934] (v6.0.1)
- `YesNoButtonGroupType` renders as a toggle but submits radio inputs [PR #14147] (v5.2); conditional JS reads the live `checked` property [PR #14416] (v5.2.2).
- Field-value comparisons use bound parameters on raw values, not `InputHelper::clean()`, after a security-team review. [PR #15165] (v7.1)
- `CommonController::accessDenied()` throws for anonymous or non-batch requests and returns an error array for batch requests. [PR #16299] (v7.2.0)
- 8.0 only: `Request::get()` is replaced by explicit bag reads [PR #17309]; constraints take named arguments [PR #17392].

### Security, CSRF, sanitisation and permissions framework
- Permission prefixes `addon:`/`plugin:` [PR #588] were deprecated in 2.2.1 [PR #2707]. Typed permission exceptions map to API 403 [PR #4299] (v2.9); unknown permissions return false [PR #601].
- Permission classes are DI services under `services.permissions` and filesystem discovery is deprecated. [PR #7312] (v3.3)
- `VirtualPermissions::isVirtuallyGranted()` grants in code with no role UI. [PR #14016] (v5.2)
- Parent menus with no permitted children are hidden [PR #14863], as is the admin cog for non-admins [PR #14880] (v7.0).
- CSRF tokens are validated with `CsrfTokenManager::isTokenValid()` because Symfony 5 randomises them. [PR #12198] (v5.0) The keep-alive ping keeps the session and token valid. [PR #7883] [PR #13753]
- `InputHelper` strips HTML unless the mask is `html` [PR #1546] (v1.3.1); the `html` filter keeps doctype, comments, Outlook conditionals [PR #443] [PR #6938] [PR #7071] and must be idempotent [PR #9108] [PR #9516] (v4.4.6). Unicode is detected with `mb_check_encoding`, not `iconv()`. [PR #13572] [PR #15006] (v5.2.6)
- Weakening sanitisation needs security-team review. [PR #4123] [PR #15165]
- Cookies use an explicit `sameSite` argument defaulting to Lax, with tracking cookies set to None; forced Lax broke tracking. [PR #11448] [PR #12325] (v5.0)
- The remember-me secret is `%mautic.secret_key%`, static per install, because a random secret logged everyone out [PR #12425] (v5.0). The lifetime fell from 365 to 90 days. [PR #15739] (v7.1) [code: app/bundles/CoreBundle/Config/config.php:282 @7.x]
- `EncryptionHelper` took ciphers in priority order with lazy re-encryption [PR #5300] (v2.12); only `OpenSSLCipher` remains.
- Security hardening that could break installs ships opt-in (`validate_remote_domains`) [PR #15868] (v7.1); a vulnerable library still in use goes behind an off-by-default flag first [PR #12416] (v5.0).
- No third-party calls by default: fonts are self-hosted [PR #13317] (v5.1) and Gravatar is off [PR #17781] (unreleased 7.x).
- SAML moved to a mautic/SpBundle fork [PR #13742] (v5.1), then `javer/sp-bundle` [PR #14390] (v6.0).

### Events and extension points
- `CoreEvents::BUILD_MAUTIC_JS` builds `/mtc.js` from subscribers in priority order. [PR #1582] (v1.4)
- `CustomButtonEvent` lets plugins add buttons by priority and fires even where core defines no buttons. [PR #2905] [PR #6844]
- `CoreEvents::MAINTENANCE_CLEANUP_DATA` lets bundles purge old data. [PR #2024] (v2.1)
- Form actions and fields dispatch an `eventName`, with `callback` kept for BC. [PR #2451]
- `SearchCommandEvent`, `SearchQueryEvent` and `SearchHelpEvent` let plugins add list search commands. [PR #17281] (unreleased 7.x)
- Global search is built from each bundle's `SearchSubscriber`, gated by view permission. [PR #14432] (v6.0)
- Symfony 5: `dispatch()` returns the event, and tests may not mock Symfony event classes. [PR #12213] (v5.0)
- Event-class properties are `private` and typed, so plugin subclasses must use getters. [PR #16821] (v7.2)
- `CoreEvents::PRE_UPGRADE`/`POST_UPGRADE` were added in [PR #1484]; behaviour.md C10 records that 7.x has no dispatcher for them. [code: app/bundles/CoreBundle/CoreEvents.php:70-79 @7.x]

### Commands and locking
- `ModeratedCommand` prevents overlapping runs [PR #1139] (v1.2.3), gained PID locking with a file-lock fallback [PR #2998] (v2.3), `--lock_mode` [PR #4337] and `flock` for NFS [PR #7137]. In 7.x `file_lock` is mapped to `flock`. [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:91-93 @7.x]
- `checkRunStatus()` returns false only for contention and callers exit SUCCESS; an unopenable lock file throws a `RuntimeException` naming the path, because returning false would make all ten callers report SUCCESS. [PR #17188] (unreleased 7.x) The lock file is removed only if it exists. [PR #15257] (v7.1)
- Subclasses pass every parent dependency to the two-argument constructor. [PR #12303] (v5.0)
- Commands return an int exit code [PR #11576] using `Command::SUCCESS/FAILURE` [PR #12268] (v5.0); help goes in `#[AsCommand(help:)]` [PR #16723] and leaf commands are `final` [PR #16885] (v7.2).
- Long-running commands finish the current batch on SIGTERM/SIGINT and exit 143. [PR #14745] (v7.0) `ProcessSignalService` arrived with a resumable `mautic:import`. [PR #12845] (v5.1)
- `--gdpr` cleanup uses `gdpr_user_purge_threshold` (1095); a `--days-old` override was rejected to avoid typo wipes. [PR #13240] (v5.1) Cleanup writes an audit-log summary. [PR #12682]
- Unused-IP deletion selects IDs and deletes by primary key in batches. [PR #7491] [PR #10710] (v2.15.2, v4.1.2)
- `--bypass-locking` exists on maintenance and unused-IP commands. [PR #11478] (v5.0)

### Assets, JS and CSS pipeline
- Generated `media/js/app.js` and CSS are not committed; run `mautic:assets:generate`. [PR #180] [PR #9307] [PR #12358] (v5.0)
- From 5.0 libraries come from `package.json`; `composer install` runs `npm ci` and `patch-package`. [PR #12234] [PR #12240] [PR #12270] [PR #12271] (v5.0)
- Never load from `node_modules` at runtime: asset generation copies files into `media/`. [PR #12417] [PR #12395] (v5.0) It fails loudly when a source is missing [PR #14226] (v5.2.0) and regenerates `media/css/libraries.css` [PR #17597] (v7.2.2).
- JS dependency policy is same versions first, then max-minor updates, then majors. [PR #12373] Script order matters: touch-punch loads after jQuery UI. [PR #13216] (v5.0.2)
- Minification stays on `mrclay/minify`. [PR #12461] (v5.0)
- Styling moved from LESS and Grunt [PR #12942] [PR #14687] to SCSS through the SymfonyCasts Sass Bundle plus AssetMapper, with Bootstrap 3.4.1 from `twbs/bootstrap-sass`; this was judged not a BC break because plugins ship compiled CSS. [PR #16143] (v7.2.0)
- Bootstrap 5.3.8 replaces 3.4.1 with a generated BS3 compatibility layer and a JS shim for the BS3 jQuery API, to be removed in Mautic 8; targeting 8.x directly was rejected. [PR #17767] (unreleased 7.x) [code: app/composer.json:109 @7.x]
- Update ZIPs must contain `assets/build/` and `var/sass/`, and release CI checks it. [PR #17300] (v7.2.1)
- Remix Icon was installed from npm [PR #13318] (v5.1), vendored into CoreBundle because release packages lack `node_modules` [PR #13758] (v5.1), and hand-patched at 4.6.0 [PR #14520] (v6.0). See section 8 for the 7.x state.
- Third-party licences go in `LICENSE.txt`. [PR #14868]
- The file manager is elFinder through FMElfinderBundle [PR #8306] (v3.0).

### IP lookup, tracking gate and shared helpers
- IP lookup services are pluggable through `AbstractRemoteDataLookup`/`AbstractLocalDataLookup` and `mautic:iplookup:download`. [PR #964] [PR #1252] (v1.2.3) MaxMind downloads never crash the app. [PR #16137] (v7.1.3)
- `IpLookupHelper::isRequestTrackable()` is the single tracking gate: false for bots, HEAD, prefetch, `DNT: 1` and `Sec-GPC: 1`. [PR #15844] (v7.1) Bot detection uses Matomo DeviceDetector and `do_not_track_bots` holds only custom extras. [PR #12750] (v7.1)
- Private ranges map to 127.0.0.1 unless `track_private_ip_ranges` is set. [PR #6422]
- The HTTP client is Guzzle `mautic.http.client`, replacing `joomla/http`. [PR #9833] (v4.0)
- Charts aggregate in SQL with a minimum one-hour bucket. [PR #1169] [PR #6222]
- `UrlHelper` uses Guzzle's query parser, not `parse_str`, so dots in keys survive and parameters are not duplicated. [PR #15725] [PR #15744] (v7.1) URLs keep `%20`. [PR #15336] (v7.0)
- The translator falls back to English on a missing catalogue instead of a 500. [PR #15475] (v7.0) The `MauticResourceTranslator` decorator replaced `TranslatorLoader` on 8.x only. [PR #17393] [PR #14887]
- Shortening is pluggable through `ShortenerServiceInterface` [PR #12299] with per-channel switches [PR #12128] (v5.0).

### UI framework and design system
- UI colours, spacing and type are CSS custom properties with light and dark themes; names describe function, not colour. [PR #13735] [PR #13689] (v5.2)
- Icons are Remix (`ri-*`) [PR #13957] (v5.2) and Font Awesome was removed [PR #14265] (v6.0).
- A cog dropdown replaced the right sidebar [PR #13953] [PR #14029] (v5.2); the accent colour became a global setting [PR #14637] (v6.0); admin chrome uses square Carbon corners [PR #14668] (v7.0).
- Twig components live in `@MauticCore/Components/` so a Bootstrap upgrade changes markup in one place. [PR #14869] [PR #15089] [PR #15090] [PR #16143] (v7.0)
- JS hooks `Mautic.<bundle>OnLoad` with delegated `mQuery` events [PR #13767]; `onPageUnload` destroys only CKEditors in the unloaded container [PR #15195] (v7.0).
- Only uppercase `AND`/`OR` are search operators. [PR #14415] (v5.2.2)
- The builder entity button order is Builder, Apply, Save & Close, Cancel and changes only in a major. [PR #9895] (v4.0)
- Accessibility is a review criterion. [PR #13376] [PR #13629] [PR #13887] [PR #14276]

### The `final` sweep (7.2.0)
- Classes with no core children were made `final`: form types and validators [PR #16754], exceptions [PR #16755], bundles and passes [PR #16756], helpers [PR #16883], DI extensions [PR #16884], models, Doctrine types and migrations [PR #16894], CoreBundle infrastructure and permissions [PR #16898]. `protected` became `private`. [PR #16700] [PR #16702] [PR #16824] (v7.2.0)
- Plugins that subclassed these classes must switch to composition or decoration. See section 7 for the BC tension. [PR #16754]

## 3. Removed, deprecated, replaced

| Thing | Deprecated | Removed | Replacement | PR |
|---|---|---|---|---|
| Annotations on entities | — | 1.1 | Static `loadMetadata` | [PR #229] |
| `GraphHelper` | 1.4 | 2.0 | `Helper/Chart/*` | [PR #1169] [PR #1713] |
| PostgreSQL | — | 2.0 | MySQL only | [PR #1884] |
| `mautic:duplicateip:delete` | — | 2.15.2 | `mautic:unusedip:delete` | [PR #7491] |
| MauticFactory in models | 2.1.1 | 3.0 | Constructor/setter DI | [PR #2228] [PR #8207] |
| MauticFactory methods | 2.1.1 | 6.0 | DI | [PR #14399] [PR #14400] [PR #14564] |
| MauticFactory class | 2.0 (docblock) | 7.0 | DI | [PR #14462] (see section 8) |
| `plugin:` permission prefix | 2.2.1 | 3.0 target | Plain names | [PR #2707] |
| Filesystem discovery of permission classes | 3.3 | not removed in 7.x | `services.permissions` | [PR #7312] |
| `mautic:migrations:generate` | — | 3.0 | `doctrine:migrations:generate` | [PR #2167] [PR #8429] |
| `SchemaHelperFactory` | — | 3.0 | Specific schema helpers | [PR #8456] |
| AppKernel version constants | — | 3.0 | `ThisRelease::getMetadata()` | [PR #8449] |
| `choices_as_values` | — | 3.0 | label → value choices | [PR #8248] |
| `CoreParametersHelper::getParameter()` | 3.0 | 6.0 | `get()` | [PR #13837] |
| `joomla/http` | — | 4.0 | Guzzle | [PR #9833] |
| `db_server_version` | — | 4.0 | Auto-detection | [PR #9739] |
| `CustomFormEvent` | 4.3 | 5.0 | none | [PR #11037] [PR #11632] |
| PHP templates, `PhpEngine`, `TemplatingHelper` | 4.3 | 5.0 | Twig | [PR #12046] [PR #12122] |
| Controller `initialize()` | — | 5.0 | Constructor autowiring | [PR #12412] |
| `CommonRepository::clear()` | — | 5.0 | EM detach/clear | [PR #12354] |
| `%kernel.root_dir%` | — | 5.0 | `%kernel.project_dir%` | [PR #11145] |
| `EmojiToShortTransformer` | — | 5.0 | utf8mb4 | [PR #12483] |
| `mtc_sid` cookie | — | 5.0 | none | [PR #12440] |
| `offline.php` | — | 5.0 | Twig offline template | [PR #12101] |
| CalendarBundle | — | 5.0 | none | [PR #11270] |
| Committed generated assets | — | 5.0 | `mautic:assets:generate` | [PR #12358] |
| `link_shortener_url` | — | 5.0 (UPGRADE note) | `Shortener` service; key still a 7.x default | [PR #12299] |
| mysqli / `db_driver` choice | — | 5.0.2 | `pdo_mysql` | [PR #13210] |
| `mauticTemplateVars` in `customContent()` | — | 5.1 | Twig `_context` | [PR #13670] |
| Font Awesome | 5.1 | 6.0 | Remix Icon | [PR #13957] [PR #14265] |
| Froala | 5.0 (flag) | 6.0 | CKEditor 5 | [PR #12416] [PR #14501] |
| Legacy builder | — | 6.0 | GrapesJS | [PR #14450] |
| `lightsaml2/sp-bundle` | — | 6.0 | `javer/sp-bundle` | [PR #14390] |
| UI updater, `/s/update` | 4.2 notice | 7.0 | `mautic:update:*` | [PR #10907] [PR #14689] |
| PHP 8.1 | — | 7.0 | PHP ≥8.2 | [PR #14689] |
| `iterator_mode` | — | 7.0 | — | [PR #14896] |
| Remember-me 365 days | — | 7.1 | 90 days | [PR #15739] |
| Static bot list | — | 7.1 | DeviceDetector | [PR #12750] |
| `parse_str` in `UrlHelper` | — | 7.1 | Guzzle query parser | [PR #15725] |
| LESS, Grunt, npm `bootstrap` | — | 7.2.0 | SCSS, AssetMapper | [PR #16143] |
| Tagged-service compiler passes | — | 7.2.0 | `#[AutowireIterator]` | [PR #16776] |
| String service IDs moved to `services.php` | 7.2 | not before 8.0 | FQCN services | [PR #16843] [PR #17251] |
| `getPublishedByDateExpression()` | 7.2 | 8.0 planned | ORM/DBAL variants | [PR #16970] |
| `BuilderEvent::addTokensFromHelper()` | 7.2 | 8.0 planned | `getFormattedTokens()` | [PR #15855] |
| EmojiMap classes, `EmojiHelper` | 7.2 | 8.0 | none | [PR #16992] [PR #17031] |
| Bootstrap 3.4.1 as native UI | unreleased 7.x | 8 planned | Bootstrap 5.3.8 | [PR #17767] |
| Gravatar by default | — | unreleased 7.x | `gravatar_enabled` opt-in | [PR #17781] |
| `TranslatorLoader extends Translator` | — | 8.0 only | `MauticResourceTranslator` | [PR #17393] |
| `Request::get()`, `ClassMetadataInfo` | — | 8.0 only | Explicit bags, `ClassMetadata` | [PR #17309] [PR #17359] |

## 4. Regression catalogue

| Area | Symptom | Expected behaviour | PR | Version |
|---|---|---|---|---|
| DI | Plugins broke on 7.2.0 because string IDs such as `mautic.helper.encryption` vanished | Moving a service keeps its old ID as a deprecated alias | [PR #16843] [PR #17251] | 7.2.1 |
| DI | `onKernelException` ran twice | A subscriber is not also tagged as a listener | [PR #16879] | 7.2 |
| DI | GrapesJS builder broke under autowiring | Stateful helpers are instantiated once | [PR #11587] | 5.0 |
| DI | Update to 7.1 failed | Test-only commands are registered only in the test env | [PR #16104] | 7.1.2 |
| DI | Hand-wired services broke silently after constructor changes | The container smoke test builds every service | [PR #16747] | 7.2 |
| Config | `.env` values overwritten by `local.php` | Existing env wins over `local.php`-derived values | [PR #17072] | 7.2 |
| Config | Recommended-project paths wrong | Webroot auto-detected, paths resolved from `local_root` | [PR #17023] | 7.2 |
| Config | Restricted config field gave a 500 | Optional config fields render conditionally | [PR #15912] | 7.2.0 |
| Config | Invalid trusted host gave a 500 | Config is validated on save | [PR #16006] | 7.1.1 |
| Composer | MOTD failure broke `composer install` | Non-essential hooks exit 0 | [PR #16226] | 7.2.0 |
| Errors | Error page failed under cPanel FPM | Absolute paths from the install root | [PR #16155] | 7.1.3 |
| Installer | GUI installer returned 500 | No database access in per-page helpers before install | [PR #10372] | 4.0 |
| Routing | Subdirectory installs broke after the `site_url` change | Preserve base path and front controller | [PR #7193] [PR #7457] [PR #7572] | 2.15.2 |
| Routing | Tracking links used the admin host | `site_url` applied in subrequests | [PR #17168] | 7.2.0 |
| Listener priority | Timestamps shown in UTC after the locale fix | Check listener priorities when adding request subscribers | [PR #2352] [PR #2397] | 2.2 |
| Timezone | Day in user timezone, clock in global timezone | Session timezone pushed into `DateTimeHelper` per request | [PR #17627] | 7.2.2 |
| Timezone | Campaign trigger date drifted on each save | Helpers clone before conversion | [PR #17091] | 7.2.0 |
| Timezone | `toUtcString` reset the helper's timezone | Helpers are side-effect free | [PR #10375] | 4.2.1 |
| Timezone | `DateTimeImmutable` stored in user timezone | All datetimes stored in UTC | [PR #13127] | 5.1 |
| Doctrine | "New entity found through relationship" | Persist before flush (DEFERRED_EXPLICIT) | [PR #1221] | 1.2.3 |
| Doctrine | Corrupt serialized data gave a 500 | `ArrayType` returns `[]` and strips null bytes | [PR #2177] [PR #8704] | 2.1.1–3.0 |
| Doctrine | Contacts with `o:` in data could not open | Reject only real object patterns | [PR #8266] | 2.16.0 |
| Doctrine | A/B stats equal to one variant | `IN` binds array parameters | [PR #3209] | 2.8 |
| Doctrine | `upsert()` returned an earlier insert's ID | `LAST_INSERT_ID(id)` on duplicate key | [PR #14482] | 5.2.2 |
| Doctrine | Deadlocks on `leads` during DNC writes | DNC-only saves skip modified tracking | [PR #13994] | 5.2 |
| Doctrine | `Expr::and()` undefined in API-library CI | ORM keeps `andX`/`orX`; ORM and DBAL helpers split | [PR #16505] [PR #16970] | 7.2 |
| Migrations | Generated-column migration caused outages | Generated columns run after regular migrations | [PR #13455] | 5.1 |
| Fixtures | "No active transaction" on install under PHP 8 | No DDL inside fixtures | [PR #10787] [PR #11701] | 4.2/5.0 |
| DB | Install failed obscurely without `pdo_mysql` | Cache build fails with a clear message | [PR #13210] | 5.0.2 |
| Locking | Second Apply reported "changed by someone else" | Version refreshed after each partial save | [PR #15894] | 7.1 |
| Commands | Cron died with a `flock()` TypeError or silently succeeded | Permanent errors throw; false means contention | [PR #17188] | unreleased 7.x |
| Commands | Overlapping cron runs caused duplicate keys | A second run is refused | [PR #1139] [PR #1867] | 1.2.3 |
| Commands | Unused-IP delete locked tables | Select IDs, delete by PK in batches | [PR #7491] [PR #10710] | 2.15.2/4.1.2 |
| CSRF | False "invalid CSRF" on Symfony 5 | `isTokenValid()`, not string compare | [PR #12198] | 5.0 |
| Cookies | Cross-site tracking broke after forced Lax | Tracking cookies use SameSite None | [PR #11448] [PR #12325] | 5.0 |
| Auth | Users logged out on every bootstrap | Remember-me secret static per install | [PR #12425] | 5.0 |
| Forms | Labels and values swapped after Symfony 3 | Choice arrays are label → value | [PR #8248] [PR #8771] | 3.0 |
| Forms | Company merge returned 500 | `isSubmitted()` before `isValid()` | [PR #9847] | 4.0 |
| Forms JS | Toggle-dependent fields never updated | Read the live `checked` property | [PR #14416] | 5.2.2 |
| Controllers | 500 on unlock and theme download | Action parameter names match route attributes | [PR #12837] [PR #12847] | 5.0 |
| Controllers | 500 saving or cloning entities | Internal action calls pass `Request` first | [PR #12719] [PR #12772] | 5.0 |
| Lookups | Company search broke after an "unused" trait was deleted | Guard implicit dependencies with a test | [PR #12652] | 5.0 |
| Twig | Plugin template injection missing on AJAX | `VIEW_INJECT_*` dispatched on every render path | [PR #13580] [PR #14434] [PR #14437] | 5.1–5.2.2 |
| Twig | Marketing Messages broke when Standard templates were removed | Keep CoreBundle Standard fallbacks | [PR #12006] [PR #12021] | 5.0 |
| Twig | Every page 500 on Twig ≥3.28 | Pass `Markup` through unchanged | [PR #16487] [PR #16741] | 7.2 |
| Twig | Theme templates using `purify` returned 500 | The sandbox delegates runtimes | [PR #16238] | 7.2.0 |
| Twig | `sort` blocked in uploaded themes | Use Twig's own sandbox checks | [PR #17620] | 7.2.2 |
| Assets | Production JS referenced `node_modules` | Copy npm libraries into `media/` | [PR #12417] [PR #12395] | 5.0 |
| Assets | Mobile dashboards broke | Respect library order in aggregation | [PR #13216] | 5.0.2 |
| Assets | Icons missing without `node_modules` | Ship runtime assets inside the bundle | [PR #13758] | 5.1 |
| Assets | A jquery-ui bump silently broke `libraries.js` | Asset generation fails loudly on a missing source | [PR #14226] | 5.2.0 |
| Assets | Update 7.1.3 → 7.2.0 broke the UI | Update ZIP ships `assets/build` and `var/sass` | [PR #17300] | 7.2.1 |
| Assets | Stale `libraries.css` overrode new SCSS | Asset generation clears legacy files | [PR #17597] | 7.2.2 |
| URLs | Dots in query keys became underscores | Guzzle query parsing | [PR #15725] [PR #15744] | 7.1 |
| Input | `iconv` notices on emoji input | `mb_check_encoding` detection | [PR #13572] [PR #15006] | 5.2.6 |
| Sanitiser | Doctype duplicated on every save | Cleaning is idempotent | [PR #9108] [PR #9516] | 4.4.6 |
| Sanitisation | Campaign conditions failed on `'` and `&` | Compare raw values with bound parameters | [PR #15165] | 7.1 |
| Import | Imported campaigns lost content | Map snake_case export keys before denormalising | [PR #17226] | 7.2.0 |
| Updates | Newer release hidden on old PHP | Show it and fail at the pre-update check | [PR #10459] | 4.2 |

## 5. Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.0–1.4 | `/s/` firewall; static entity metadata; Monolog logging; DEFERRED_EXPLICIT; moderated commands; IP lookup family; `BUILD_MAUTIC_JS`; chart library | [PR #70] [PR #229] [PR #721] [PR #1221] [PR #1139] [PR #1252] [PR #1582] [PR #1169] |
| 2.0–2.2 | Config menus; MySQL only; maintenance cleanup event; ModelFactory; message queue | [PR #1115] [PR #1884] [PR #2024] [PR #2542] [PR #2549] |
| 2.3–2.15 | PID locking; DB cache table; lock expiry option; typed permission exceptions; cipher priority; `site_url` URL generation | [PR #2998] [PR #2954] [PR #3549] [PR #4299] [PR #5300] [PR #7193] |
| 3.0 | Symfony 3; ParameterLoader and env vars; middlewares; `release_metadata.json`; utf8mb4 for new installs; elFinder; fixture groups | [PR #8254] [PR #8449] [PR #8475] [PR #8349] [PR #8306] [PR #8366] |
| 3.1–3.3 | Generated columns; permission classes as DI services | [PR #7094] [PR #7312] |
| 4.0–4.4 | Symfony 4; Guzzle; DB platform auto-detection; pre-update checks; Twig hybrid; full-text indexes; PHP 8.0 | [PR #9409] [PR #9833] [PR #9739] [PR #10459] [PR #10129] [PR #9335] [PR #11217] |
| 5.0 | Autowiring; Twig only; Symfony 5; DBAL 3.6; npm asset pipeline; constructor-injected controllers; `app/assets`; read replica; HSTS | [PR #11587] [PR #12046] [PR #12213] [PR #12396] [PR #12234] [PR #12412] [PR #10682] [PR #11792] [PR #11608] |
| 5.0.2 | `pdo_mysql` only | [PR #13210] |
| 5.1 | Generated columns after migrations; optimistic locking; system theme overrides; `EntityValidateEvent`; self-hosted fonts; Remix Icon | [PR #13455] [PR #13659] [PR #13590] [PR #13812] [PR #13317] [PR #13318] |
| 5.2 | VirtualPermissions; design tokens; `SkipModifiedInterface`; Remix replaces Font Awesome in core UI | [PR #14016] [PR #13735] [PR #13994] [PR #13957] |
| 5.2.2 | Accurate `upsert()` IDs; custom template event on AJAX | [PR #14482] [PR #14434] |
| 6.0 | MauticFactory methods removed; batch-save events; per-bundle global search; `javer/sp-bundle` | [PR #14400] [PR #14503] [PR #14432] [PR #14390] |
| 7.0 | Symfony 7; CLI-only updates; graceful SIGTERM; component library | [PR #14887] [PR #14689] [PR #14745] [PR #14869] |
| 7.1 | MOTD; remember-me 90 days; `isRequestTrackable`; DeviceDetector; MySQL generated stats columns; PHP 8.5 | [PR #15970] [PR #15739] [PR #15844] [PR #12750] [PR #15621] [PR #15721] |
| 7.2.0 | `services.php` wave; `final` sweep; SCSS and AssetMapper; container smoke test; `#[AutowireIterator]`; container-by-name ban; env precedence; theme sandbox; PHPUnit 11 | [PR #16843] [PR #16754] [PR #16143] [PR #16747] [PR #16776] [PR #16737] [PR #17072] [PR #16238] [PR #16891] |
| 7.2.1 | Deprecated aliases restored; AssetMapper webroot; update ZIP contents | [PR #17251] [PR #17300] |
| 7.2.2 | Per-request `DateTimeHelper` timezone; sandbox denylist dropped; `libraries.css` regenerated | [PR #17627] [PR #17620] [PR #17597] |
| unreleased 7.x | Privacy Centre; search events; Bootstrap 5.3.8 with BS3 layer; lock errors throw | [PR #17781] [PR #17281] [PR #17767] [PR #17188] |
| 8.0 only | ORM 3 preparation; `Request::get()` removed; Symfony 8.1; translator decorator | [PR #17359] [PR #17309] [PR #17392] [PR #17393] |

## 6. Platform requirements timeline

| Version | PHP | Symfony | Doctrine / database | Templates and front end | PR |
|---|---|---|---|---|---|
| 1.x | 5.3 minimum (no short arrays) | — | `mysqli` default driver | PHP templates | [PR #1477] [PR #710] |
| 2.0 | — | — | MySQL only | — | [PR #1884] |
| 3.0 | 7.2+ | 3 | utf8mb4 for new installs | jQuery 3.3, Bootstrap 3.3.7 | [PR #8254] [PR #8349] |
| 3.2 | 7.4 supported | — | MySQL 5.7 minimum | — | [PR #8447] [PR #9437] |
| 4.0 | ≥7.4 | 4 | Platform auto-detected | — | [PR #9409] [PR #9739] |
| 4.3 | — | — | — | Twig alongside PHP templates | [PR #10129] |
| 4.4 | 8.0 | 4.4 | ORM 2.8 | — | [PR #11217] |
| 5.0 | ~8.0 (8.0.2–8.1.99 in release metadata) | 5.4 | DBAL 3.6, ORM 2.14 | Twig only; jQuery 3.7, Bootstrap 3.4.1 from npm | [PR #12213] [PR #12382] [PR #12396] [PR #12046] [PR #12373] |
| 5.0.2 | — | — | `pdo_mysql` only | — | [PR #13210] |
| 5.1 | 8.2 supported; `ext-iconv` | — | — | Remix Icon, Source Sans 3 | [PR #12469] [PR #13318] [PR #13317] |
| 6.0 | ~8.1 (to 8.3.99) | 6.4 | DBAL 3.6–3.7 | Stricter types | [PR #13110] |
| 7.0 | ~8.2 (to 8.4.99) | 7.4 | MySQL 8.4.0 / MariaDB 10.11 minimum | oauth-server-bundle 5.x | [PR #14689] [PR #14887] |
| 7.1 | 8.5 supported | — | — | — | [PR #15721] |
| 7.2.0 | 8.2 floor (PHPUnit 11) | 7.4 | ORM 2.20, DBAL 3.7 | SCSS, AssetMapper, `twbs/bootstrap-sass` 3.4.1 | [PR #16891] [PR #16143] |
| unreleased 7.x | — | — | — | Bootstrap 5.3.8 plus BS3 layer | [PR #17767] |
| 8.0 only | — | 8.1 | ORM 3, DBAL 4 | — | [PR #17392] [PR #17359] |

The 4.4, 5.0, 6.0 and 7.0 PHP and Symfony constraints were read from `app/composer.json` and `app/release_metadata.json` at those git tags; the 5.0 row corrects the inputs, which said PHP 8.1. The current values are in the 7.x snapshot. [code: app/composer.json:19-82 @7.x] [code: app/release_metadata.json:4-7 @7.x]

## 7. Maintainer norms for this area

BC policy
- BC breaks land only in a major and are documented in `UPGRADE-x.0.md`; removing deprecated APIs counts as a BC break even when an earlier removal was promised. [PR #1713] [PR #11041] [PR #13110] [PR #13837] [PR #14896] [PR #15284]
- Deprecate in a minor with the removal version stated, then remove in the next major; removal PRs target `8.x`. [PR #2707] [PR #11037] [PR #11632] [PR #13066] [PR #16970]
- When classes or services move, leave deprecated aliases. [PR #1185] [PR #1252] [PR #17251]
- Unadvertised extension points and plugin compatibility count as BC surface. [PR #1633] [PR #17251]
- Changing a shared interface or signature, including adding a return type, is a BC break; add strict types to new APIs now. [PR #15481] [PR #15655] [PR #14503]
- A new option's default keeps the old behaviour [PR #3549] [PR #6422]; adapt code rather than rename user data or identifiers [PR #5548].
- Build tooling is not a BC break when plugins consume only compiled output. [PR #16143]
- Large UI migrations ship a compatibility layer in a minor, migrate in stages, and remove the layer in the next major. [PR #17767]
- Exception: the 7.2.0 `final` sweep landed in a minor without deprecation notices, weeks after [PR #16323] asked to keep typing changes off classes "meant to be extended". "No children" was judged against core only. [PR #16754] [PR #16883] [PR #16894] [PR #16898] [PR #16885] [PR #16821] The working policy is to extend through events, interfaces and decoration (VirtualPermissions [PR #14016], `EntityValidateEvent` [PR #13812], batch-save events [PR #14503]), not inheritance.

Branches
- Bug fixes target the oldest maintained patch branch `a.b` (for example `7.2`); features and enhancements target `a.x` (for example `7.x`); BC breaks target the next major (`8.x`). [PR #10589] [PR #12835] [PR #13921] [PR #16104] [PR #17300] [PR #17680] [code: .github/PULL_REQUEST_TEMPLATE.md:9-11 @7.x]
- After 7.2.0, `7.2` takes patches and `7.x` takes 7.3 work; when a patch line ends, retarget to `7.x`. [PR #16487] [PR #16877]
- Once a major enters beta or RC it is closed to features. [PR #14657] [PR #14745]
- Release tags are merged forward into `x` without moving dependencies backwards. [PR #15263] [PR #16486] [PR #17516] 7.x is forward-merged into 8.x. [PR #17281] [PR #16155]

Review and testing
- T1 PRs need one code review and one user test from another organisation, and the author cannot approve; 7.x uses `code-review-passed`, `user-testing-passed` and `ready-to-commit` labels. [PR #12128] [PR #13754] [PR #16337]
- Bug fixes include a regression test that fails without the fix; functional tests are preferred. [PR #11644] [PR #14503] [PR #17188] [PR #17627]
- Before removing anything, grep for usages, add guard tests and remove every call site. [PR #12652] [PR #14463] [PR #15372]
- Large refactors are split per area, ship with their Rector rule, and are validated against the mautic/api-library suite. [PR #12396] [PR #12412] [PR #16723] [PR #16843]
- Code style is php-cs-fixer on 7.x [PR #13037]; heavy Rector sets stay out of CI [PR #13035].
- Fail loudly on permanent errors and quietly on transient ones; optional third-party services never crash the app. [PR #17188] [PR #16137]
- Aggregate in SQL, batch large deletes and avoid synchronous counts on big tables. [PR #1169] [PR #7162] [PR #14770]
- Privacy work ships with no third-party calls by default, even when that changes behaviour on upgrade. [PR #17781]

## 8. Conflicts resolved against the code

- MauticFactory: the inputs said "removed in 3.0" and "removed in 6.0", while UPGRADE-7.0 lists the class. The code settles it: 3.0 removed it from models and the API bundle, 6.0 removed its methods, and the file still existed at tag 6.0.0 with only a constructor and `getModel()` under a `@deprecated 2.0` docblock. It is absent at tag 7.0.0, and UPGRADE-7.0 records the class removal. [PR #8207] [PR #14462] [PR #14564] [code: UPGRADE-6.0.md:26-39 @7.x] [code: UPGRADE-7.0.md:16 @7.x]
- Old string service IDs: [PR #11587] planned to drop them in Mautic 6, which did not happen. On 7.x the bundles' `Config/services.php` files hold 226 `mautic.*` aliases, 19 of them marked deprecated in 7.2 with no removal version. The 8.x snapshot has 18 `mautic.*` aliases and none of the 7.2-deprecated ones. [PR #17251] [code: app/bundles/CoreBundle/Config/services.php:189-190 @7.x] [code: app/bundles/CoreBundle/Config/services.php:342-354 @7.x]
- Custom-template event on AJAX is a regression chain: [PR #13580] (v5.1) dispatched it for AJAX, it was reported broken since 5.0, and [PR #14434] (v5.2.2) fixed it through `eventAwareRenderView()`, which 7.x calls on the AJAX render path. [code: app/bundles/CoreBundle/Controller/CommonController.php:197-205 @7.x] [code: app/bundles/CoreBundle/Controller/CommonController.php:426-430 @7.x]
- The `final` sweep is a recorded exception to the BC norm: a `git grep` count of lines starting `final class` under `app/bundles` rose from 611 at tag 7.1.3 to 2,856 at tag 7.2.0, and no UPGRADE file mentions it. [PR #16754] [PR #16898]
- Remix Icon and release packages: 7.x vendors Remix Icon in CoreBundle (`Assets/css/libraries/remixicon/` with its licence) and imports it from SCSS; it is not an npm dependency. Release packaging excludes `node_modules/*` and also removes the GrapesJS plugin's nested `node_modules`. [PR #13758] [PR #14520] [code: app/bundles/CoreBundle/Assets/css/libraries/_libraries.scss:7 @7.x] [code: build/exclude_files.txt:30 @7.x] [code: build/package_release.php:78-81 @7.x]
- `link_shortener_url`: UPGRADE-5.0 says the key was removed, but 7.x (and 8.x) still declare it as a `null` default in CoreBundle config, and nothing reads it. Shortening goes through the `Shortener` service. [PR #12299] [code: UPGRADE-5.0.md:30 @7.x] [code: app/bundles/CoreBundle/Config/config.php:695 @7.x]
- Bug-fix target branch: the history is `staging` for everything in 1.x–2.x [PR #6531], then fix 5.x first with duplicate backports in the 4.4/5.x era [PR #11644] [PR #11676], then classic branching restored in 2024-01 [PR #13110]. The current rule is in the PR template: fixes to the lowest maintained `a.b` branch (for example `7.2`), features to `a.x` (`7.x`). [PR #13921] [code: .github/PULL_REQUEST_TEMPLATE.md:9-11 @7.x] [code: .github/PULL_REQUEST_TEMPLATE.md:33 @7.x]
- `ModeratedCommand` `file_lock`: still accepted on 7.x and silently mapped to `flock`. [PR #4337] [PR #7137] [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:91-93 @7.x]
- `TranslatorLoader`: on 7.x it is still a `final` class extending FrameworkBundle's `Translator`; the decorator is 8.x only. [PR #17393] [code: app/bundles/CoreBundle/Translation/TranslatorLoader.php:12 @7.x]

## 9. Open questions

- Conflict with behaviour.md D7/D8: [PR #13994] describes `SkipModifiedInterface` as skipping the automatic `dateModified` update, but on 7.x `setModifiedData()` sets `dateModified` only when it is null, so the interface mainly skips `modifiedBy`. behaviour.md wins. [PR #13994] [code: app/bundles/CoreBundle/Model/FormModel.php:269-290 @7.x]
- Conflict with behaviour.md C10: [PR #1484] added `PRE_UPGRADE`/`POST_UPGRADE`, but 7.x defines them with no dispatcher. behaviour.md wins. [PR #1484] [code: app/bundles/CoreBundle/CoreEvents.php:70-79 @7.x]
- The CLI-detection constant [PR #357] and forced UTC in the console [PR #7752] are historical: 7.x `bin/console` sets neither. Relative segment filters under CLI (issue #7967) may still be affected. [PR #7752]
- When will the 7.2-deprecated string aliases be removed, and are the 207 undeprecated `mautic.*` aliases on 7.x also slated for 8.0? [PR #11587] [PR #17251]
- Were the classes finalised in 7.2.0 meant to be recorded in an UPGRADE note? [PR #16754] [PR #16885] [PR #16821]
- Which status codes does 7.x log? [PR #721] [PR #2881] [PR #3421]
- Are DB-exception traces still shown on the production offline page? [PR #12101]
- X-Forwarded-For used the last IP [PR #318]; check 7.x `IpLookupHelper` against Symfony trusted-proxy handling.
- utf8mb4 was applied only to new installs; was there ever a charset migration? [PR #8349]
- Which classes deprecated by [PR #13066] were removed in 6.0?
- What replaces `iterator_mode` in `getEntities()`? [PR #14896]
- Was the BS3 compatibility layer merged up to 8.x? The 8.x snapshot has no `1.bootstrap-compatibility.js`. [PR #17767]
- The minimum database version is checked in two places. [PR #15797]
- Does DeviceDetector stop email-link scanners from causing clicks or DNC? [PR #12750] [PR #15844]
- Per-browser state (autosave, dismissed tips, tab state) lives in browser storage and can leak on shared machines. [PR #13610] [PR #13927] [PR #15362]
- Is the HSTS header duplicated or present when disabled? [PR #11608]

## 10. Coverage
- 19 chunk analyses: core-platform 1–3 (214 PRs) and core-foundation 1–16 (1,310 PRs), 1,524 PRs in all; core-foundation chunk 9 appeared in both digests and is counted once. [PR #12395] [PR #13380]
- About 1,200 were substantive; the rest were release merges, typo fixes, mechanical Rector or CS series, and UI-only tweaks. A further 869 noise PRs were excluded upstream before chunking. [PR #16486] [PR #17516]
- Items that belong to feature skills (tracking, emails, contacts, segments, forms, campaigns, themes, API, users, i18n, cron, dashboard) were routed there and are not repeated here. [PR #17781]
