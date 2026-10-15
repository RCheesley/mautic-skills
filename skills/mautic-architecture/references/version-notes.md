# Mautic architecture - version notes

## History that explains the current shape (before 7.x)
- Mautic historically used PHP templates and PHP config; Symfony removed the PHP template engine, and Twig became mandatory from Mautic 5 (plugins had to migrate views to `@Bundle/...html.twig` and lint them with `bin/console lint:twig`). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#php-everything] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html]
- Mautic 3 introduced Symfony environment variables and autowired console commands. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-configuration] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#remove-commands-subscribers-and-forms]
- Mautic 4 recommended the `[Controller::class, 'method']` route controller format; 4.2 added plugin install/update events. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#route-definitions] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html]
- Mautic 5 added autowiring/autoconfigure for subscribers and form types, moved `local.php` from `app/config/` to `config/`, switched controllers to FQCN `Class::method`, and moved tests to `static::getContainer()`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html]
- Deprecated in 5.0 and still shipped in 7.2.1: `RedisSentinelSessionHandler` ("to be removed in 6.0") and `Entity\Cache` (`cache_items`). [code: app/bundles/CoreBundle/Session/Storage/Handler/RedisSentinelSessionHandler.php:14 @7.x] [code: app/bundles/CoreBundle/Entity/Cache.php:10-12 @7.x]
- The deprecated permission-class directory scan is marked "To be removed in 4.0" and still works in 7.2.1. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:445-462 @7.x]
- `Controller\FormController` has been deprecated since 2.3 and is still the class behind `mautic_core_form_action` in 7.2.1. [code: app/bundles/CoreBundle/Controller/FormController.php @7.x]

## 5.x
- 5.0 applied autowiring and autoconfiguration to every bundle and plugin directory; legacy string IDs stayed as aliases. [PR #11587]
- 5.0 removed PHP templates, `PhpEngine`, `TemplatingHelper` and `TemplatingPass`; controllers take dependencies through the constructor and `initialize()` is gone. [PR #12046] [PR #12122] [PR #12412]
- 5.0 moved front-end libraries to npm, copied into `media/` at asset generation; `node_modules` is never loaded at runtime. [PR #12234] [PR #12417]
- 5.0 upgraded to Symfony 5.4 and DBAL 3.6; CSRF tokens are compared with `isTokenValid()`. [PR #12213] [PR #12396] [PR #12198]
- 5.0.2 made `pdo_mysql` the only database driver, enforced at cache build. [PR #13210]
- 5.1 runs generated-column migrations after regular migrations, adds opt-in optimistic locking, `EntityValidateEvent` and `themes/system/` template overrides. [PR #13455] [PR #13659] [PR #13812] [PR #13590]
- 5.2 added `VirtualPermissions` and `SkipModifiedInterface`; 5.2.2 restored `VIEW_INJECT_CUSTOM_TEMPLATE` on AJAX renders. [PR #14016] [PR #13994] [PR #14434]

## 6.x
- The autowiring docs said `config.php` service definitions would stop working in Mautic 6; in 7.2.1 `ServicePass` still processes them, so they kept working through 6.x and 7.x. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:33-75 @7.x]
- 6.0 removed every `MauticFactory` method one at a time; the class file survived 6.0 with only `getModel()` and was deleted in 7.0. [PR #14399] [PR #14400] [PR #14564] [code: UPGRADE-7.0.md:16 @7.x]
- 6.0 removed `CoreParametersHelper::getParameter()`, added `pre_batch_save`/`post_batch_save` to `saveEntities()`, and built global search from per-bundle subscribers. [PR #13837] [PR #14503] [PR #14432]
- 6.0 removed Font Awesome, Froala and the legacy builder, and moved SAML to `javer/sp-bundle`. [PR #14265] [PR #14501] [PR #14450] [PR #14390]

## 7.x minors
- 7.0: updates are CLI-only; `iterator_mode` was removed from `getEntities()`; PHP 8.1 was dropped. [PR #14689] [PR #14896]
- 7.1: remember-me lifetime 90 days; `isRequestTrackable()` became the single tracking gate. [PR #15739] [PR #15844]
- 7.2.0: services moved to `Config/services.php`, tagged-service passes replaced by `#[AutowireIterator]`, a container smoke test added, and many classes made `final` in a minor. [PR #16843] [PR #16776] [PR #16747] [PR #16754]
- 7.2.1: the string IDs dropped in 7.2.0 came back as deprecated aliases. [PR #17251]
- 7.0: `UuidTrait::isValidUuid()` deprecated in favour of `UuidHelper::isValidUuid()`. [code: app/bundles/CoreBundle/Entity/UuidTrait.php:33-43 @7.x]
- 7.2: string service aliases `mautic.helper.encryption`, `mautic.core.service.flashbag`, `mautic.database.version.provider`, `mautic.doctrine.loader.mautic_fixtures_loader`, `mautic.generated.columns.provider`, `mautic.helper.twig.menu`, `mautic.route_loader` deprecated. [code: app/bundles/CoreBundle/Config/services.php:189-190 @7.x] [code: app/bundles/CoreBundle/Config/services.php:342-354 @7.x]
- 7.2: menu items that define only a `uri` render. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-definitions]
- 7.x stack: PHP ~8.2, Symfony ~7.4, Doctrine ORM 2.20 / DBAL 3.7, PHPUnit 11.5, `twbs/bootstrap 5.3.8` (after 7.2.1, unreleased [PR #17767]; 7.2.1 ships `bootstrap-sass` 3.4.1), Symfony AssetMapper + Sass bundle for admin CSS. [code: app/composer.json:15-105 @7.x] [code: composer.json:28-54 @7.x] [code: app/config/config.php:50-73 @7.x]

## 8.x delta (development branch, unreleased)
Treat 8.x as unreleased: `app/release_metadata.json@8.x` still says 7.2.0, and 7.2.1 work has not been merged forward. [code: app/release_metadata.json @8.x]

Platform
- PHP 8.4 minimum, Symfony ~8.1, Doctrine ORM ^3.7 / DBAL ^4.4, PHPUnit ^13, monolog-bundle ~4.0, OAuth server bundle 6.0, SAML via `lightsaml2/sp-bundle`. [PR #16993] [PR #17392] [PR #17361] [PR #17004] [PR #17343] [PR #17342] [PR #17370]
- Coding standard is ECS only (`.php-cs-fixer.php` deleted); tool binaries move to `vendor/bin/`. [PR #17280] [PR #17164]
- Typed class constants everywhere, more `final` classes, Doctrine mapping moving to `#[ORM\*]` attributes (hybrid driver), Twig functions via attributes, core routes as `#[Route]` attributes. [PR #16996] [PR #17536] [PR #17454] [PR #17169]
- Symfony 8: `Request::get()` removed (use `query`/`request`/`attributes` bags); constraint constructors take named arguments, not option arrays. [PR #17309] [PR #17392]

Events
- Dispatch by event class everywhere except a few CRUD groups, campaign registration names, A/B winner names and webhook type ids; `CoreEvents`, `ApiEvents`, `ConfigEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents`, `UserEvents` are deleted; PHPStan enforces single-argument dispatch. [PR #17157] [PR #17183] [PR #17625]
- CoreEvents mapping: `BUILD_MENU` → `MenuEvent`, `BUILD_ROUTE` → `RouteEvent`, `GLOBAL_SEARCH` → `GlobalSearchEvent`, `LIST_STATS` → `StatsEvent`, `BUILD_COMMAND_LIST` → `CommandListEvent`, `FETCH_ICONS` → `IconEvent`, `BUILD_MAUTIC_JS` → `BuildJsEvent`, `MAINTENANCE_CLEANUP_DATA` → `MaintenanceEvent`, `ON_GENERATED_COLUMNS_BUILD` → `GeneratedColumnsEvent`, `VIEW_INJECT_CUSTOM_{ASSETS,BUTTONS,CONTENT,TEMPLATE}` → `Custom{Assets,Button,Content,Template}Event`; `PRE_UPGRADE`/`POST_UPGRADE` removed without replacement. [PR #17157] [PR #17183] [PR #17241]
- Shared CRUD event classes became `abstract` with one concrete subclass per name (type-hinting the parent still works; subscribe to the concrete class); `CommonEvent` is abstract and loses `setEntityManager()`; event constructors may not receive services. [PR #17524] [PR #17482] [PR #17640]
- Trap: constants that still exist but are no longer dispatched (e.g. `ChannelEvents::ADD_CHANNEL`, `FormEvents::FORM_ON_SUBMIT`, `ReportEvents::REPORT_ON_BUILD`) leave old subscribers silently unused. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch]

DI, models, controllers, entities
- `ServicePass` (and the `config.php` `services`, `models`, `menus` groups), `ModelPass`, `PermissionsPass`, `TwigPass` removed; menus are declared in `Config/services.php` with `knp_menu.menu` + `knp_menu.renderer`. [PR #17470] [PR #17116] [PR #17133] [PR #17121] [PR #17117]
- `ModelFactory::getModel()` resolves only via a static `getName()` on the model (no FQCN, no `mautic.<bundle>.model.<name>` alias). [PR #17133] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/mvc.html#registering-a-model]
- String service ids removed (use FQCN): `mautic.security`, `symfony.filesystem`, `mautic.helper.paths`, `mautic.helper.cache_storage`, model aliases and others. [PR #16875] [PR #17124] [PR #17134]
- `FormModel` single-parameter methods typed (`saveEntity(object $entity, …)`, `deleteEntities(array)`, …); `AbstractCommonModel::encodeArrayForUrl(array)`. [PR #17365] [PR #17523]
- `FormController` removed; `LockController` hosts `mautic_core_form_action`; `CommonController` helpers become `protected` and `accessDenied()` is removed. [PR #17481] [PR #17535]
- `CommonRepository` and `CommonEntity` become abstract; repository methods gain native types that overrides must match. [PR #17131] [PR #17524] [PR #17808]
- `ClassMetadataBuilder::addLead()`/`addContact()` removed; `isOwnershipParent()` becomes the `#[OwnershipParent]` attribute. [PR #17460] [PR #17456]
- `AbstractPermissions::definePermissions()` removed (define in the constructor; params via setter after construction). [PR #17079] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html#construct]
- `Translation\TranslatorLoader` replaced by a decorator; `CacheStorageHelper`, `EmojiHelper`, `Entity\Cache`, `RedisSentinelSessionHandler`, `ModeratedCommand::MODE_LOCK` removed. [PR #17393] [PR #17033] [PR #17026] [PR #17155] [PR #17050]
- DBAL `createQueryBuilder()` returns `Mautic\CoreBundle\Doctrine\Query\QueryBuilder`; generated aliases are checked against a MySQL+MariaDB reserved-word list. [PR #17361]
- Core routes move to `#[Route]` attributes sorted by specificity; plugins keep `config.php` `routes`. [PR #17169] [PR #17222] [PR #17231]

## Writing code for both 7.x and 8.x
- Subscribe by event class and add the 7.x constant as a second key guarded by `defined('Mautic\CoreBundle\CoreEvents::BUILD_MENU')`; never reference a deleted constants class unguarded. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch]
- Add native parameter and return types to every override now; PHP allows a child to add a return type its parent lacks. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- Get services by class name, declare menus and services in `Config/services.php`, keep plugin routes in `config.php`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/config.html#registering-a-custom-menu]
- Use `$request->query->get()` / `request->get()` / `attributes->get()`, never `$request->get()`. [PR #17392]
- Full porting checklist: mautic-upgrades-and-versions. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
