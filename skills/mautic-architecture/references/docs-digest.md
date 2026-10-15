# Mautic architecture - docs digest

What devdocs.mautic.org says about Mautic's architecture (7.2 branch unless marked 8.0). Many legacy pages carry a
"content requires a major update" banner, and 13 plugin-services/miscellaneous pages contain only that banner;
prefer code where they disagree (see "Discrepancies"). [devdocs: https://devdocs.mautic.org/en/7.2/index.html]

## Mautic vs Symfony
- Code submitted to Mautic follows Symfony coding standards; deviations are listed on the "Mautic vs Symfony" page. [devdocs: https://devdocs.mautic.org/en/7.2/index.html#submitting-code-to-mautic]
- Directory layout: `app/bundles/`, `app/config/`, `app/middlewares/`, `app/migrations/`, `bin/console`, `media/`, `plugins/`, `themes/`, `themes/system` (core template overrides), `translations/`, `var/`, `vendor/`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-directory-structure]
- Core bundles and plugins mostly use the Symfony 2.x/3.x bundle structure. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-directory-structure]
- Routes, services, menus and parameters live in one PHP file per bundle (`Config/config.php`), implemented through `MauticCoreExtension` and listeners. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#php-everything]
- Configuration values are read via Symfony parameters or `CoreParametersHelper`; Symfony environment variables have been supported since Mautic 3, not by every bundle. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-configuration]
- Services are public by default for backward compatibility. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#service-scope]
- Entities use Doctrine's static PHP driver (`loadMetadata(ORM\ClassMetadata $metadata)`); a plugin may use annotations but must not mix both. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#support-for-entity-annotations]
- Firewalls are in `app/config/security.php`; plugins hook authentication via `UserEvents::USER_PRE_AUTHENTICATION` / `USER_FORM_AUTHENTICATION` (8.0: `PreAuthenticationEvent` / `FormAuthenticationEvent`). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#firewalls-and-user-access-management] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/mautic_vs_symfony.html#firewalls-and-user-access-management]
- Permissions are bitwise and do not use Symfony voters. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#firewalls-and-user-access-management]
- Middlewares in `app/middlewares` run before Symfony boots (e.g. `IpRestrictMiddleware` for `index_dev.php`). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#middlewares] Discrepancy: `index_dev.php` was removed in 5.0; the middleware now lives in `app/middlewares/Dev/` and guards the dev environment [PR #12206] [code: app/middlewares/Dev/IpRestrictMiddleware.php:51 @7.x].
- Mautic's translator extends Symfony's and supports language packs built from Transifex. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-translator]
- Do not override core classes from a plugin; contribute the needed hook to core. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/getting_started.html]

## Services and autowiring
- Mautic 5 added Symfony autowiring and autoconfigure; `app/config/services.php` configures all bundles including plugins. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html]
- Recommended bundle `Config/services.php`: defaults `autowire()->autoconfigure()->public()`, `load()` the bundle namespace excluding `MauticCoreExtension::DEFAULT_EXCLUDES` plus your own list, and load `Entity/*Repository.php` separately. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#introducing-services-php]
- `services.php` needs a `DependencyInjection/<Name>Extension.php` matching the bundle class name and loading `../Config/services.php` with `PhpFileLoader`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#introducing-services-php]
- Entities, events and DTOs are excluded from autowiring because they must not be services. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#why-exclude-directories-from-autowiring]
- Scalar constructor arguments must be wired explicitly (`->arg('$name', '%mautic.param%')`). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#special-cases]
- Core bundles keep string service aliases for BC; plugins may move to FQCN ids in a major release. Depend on interfaces, not implementations. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#consider-backward-compatibility-for-services]
- Legacy `config.php` services: groups `command(s)`, `controllers`, `events`, `forms`, `helpers`, `models` (deprecated), `permissions`, `menus`, `other`; keys `class`, `arguments`, `alias`, `serviceAlias(es)`, `tag(s)`, `tagArguments`, `factory`, `methodCalls`, `decoratedService`, `public`, `synthetic`, `file`, `configurator`; `abstract` and `lazy` are accepted but ignored. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#service-types] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#service-definitions]
- Controllers can use constructor or action injection; invokable controllers are suggested for new code. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#dependency-injection-in-controllers]

## config.php
- Routes are grouped by firewall: `api` (`/api/*`), `main` (`/s/*`), `public` (`/*`), `catchall` (compiled last, Landing Page URLs); route names are unique across Mautic, paths unique per firewall, first match wins. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#routing-firewalls]
- Controller formats: legacy `Bundle:World:hello`, `[WorldController::class, 'hello']` (recommended since 4), or an invokable class. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#route-definitions]
- Advanced routing listens to `CoreEvents::BUILD_ROUTE` (8.0: `RouteEvent::class`). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#advanced-routing] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/config.html#advanced-routing]
- Menus `main`, `admin`, `profile`, `extra`; default priority 9999; item keys `route`, `routeParameters`, `uri`, `parent`, `priority`, `access`, `checks`, `id`, `iconClass`, `linkAttributes`; `uri`-only items render from 7.2. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-definitions]
- `parameters` defaults must match the value type; values are stored in `config/local.php`; parameters are not shown in the UI unless a config subscriber, form type and view are added. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#parameters-config-items] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#custom-config-parameters]

## Events
- Mautic uses Symfony's EventDispatcher; find events in each bundle's `*Events.php` and always use the constants (7.2). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#available-events]
- Custom events (7.2): a `final` constants class, an event class extending `Symfony\Contracts\EventDispatcher\Event`, dispatch via `event_dispatcher`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#custom-events]
- 8.0: dispatch by event object; a subscriber keyed on an old constant or string "silently receives nothing"; dispatch with one argument (PHPStan rule `mautic.singleArgumentDispatch`); use `bin/console debug:event-dispatcher`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#custom-events]
- 8.0 keeps a string constant only where several names share one event object or the name crosses bundles (e.g. Form CRUD) or is a stored Webhook type id (`mautic.form_on_submit`). [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#form-integration-and-focus-events-dispatched-by-class-name-in-mautic-8]

## MVC
- Flow: route → controller → model → view; route placeholders map to controller arguments by name, and a route default must be mirrored as the parameter default. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#route-placeholders]
- `delegateView($args)`: `contentTemplate`, `viewParameters`, `passthroughVars` (`activeLink`, `route`, `mauticContent`, `callback`, `redirect`, `target`, `replaceContent`); set at least `activeLink` and `route`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#delegateview-args]
- `delegateRedirect($url)` returns JSON `{redirect}` for AJAX, a redirect otherwise; `postActionRedirect($args)` adds `returnUrl` (default dashboard), `flashes`, `forwardController` (default true). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#postactionredirect-args]
- `AbstractCommonModel` exposes entity manager, security, dispatcher, translator; `FormModel` adds entity/repository helpers; get models through the container in controllers and inject them elsewhere. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#base-model-classes]
- Views: `@BundleName/Dir/template.html.twig`; AJAX links `data-toggle="ajax"`; modals `data-toggle="ajaxmodal"` with `data-target="#MauticSharedModal"`; forms are AJAX-enabled automatically; `Mautic.<mauticContent>OnLoad(container, response)` / `OnUnload` run around content swaps. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#ajax-links] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#ajax-content-callbacks]
- 8.0: `CommonController` helpers are `protected`; `FormController` is replaced by `AbstractFormController` / `AbstractStandardFormController`; models register via a static `getName()`; `FormModel` methods gain `object`/`array` types. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/mvc.html#extending-mautic-s-controllers] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/mvc.html#registering-a-model] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/mvc.html#mautic-8-type-changes]

## Entities and database
- `ClassMetadataBuilder::addField()` forces length 191 for string or indexed fields; helpers include `addBigIntIdField`, `addCategory`, `addContact`, `addDateAdded`, `addId`, `addIdColumns`, `addIpAddress`, `addNamedField`, `addNullableField`, `addPublishDates`, `addUuid`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#entity-php-static-function-mapping]
- Plugins cannot use core Doctrine migrations; they use `Mautic\IntegrationsBundle\Migration\Engine` with `AbstractMigration` classes guarded by `isApplicable()`, and only when the bundle extends `AbstractPluginBundle`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations]

## Translations
- INI files at `Translations/{locale}/{domain}.ini`; every bundle and plugin must include `en_US`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#translation-file-and-directory-structure]
- Load order (last wins): bundle, theme `translations/`, `translations/{locale}/`, `translations/overrides/{locale}/`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#translation-file-and-directory-structure]
- Domains: `messages` (default), `flashes`, `validators`, plus custom; keys use periods between segments and underscores between words; placeholders `%name%`; plurals `{0}...|{1}...|]1,Inf[...` with `%count%`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#translation-strings]
- Only core strings go through Transifex; plugins ship their own. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/translations.html]

## Cache
- Symfony cache is `var/cache/<env>`; in `dev` translations/views/assets are not cached, in `prod` they need a cache clear; config changes always need one; delete the folder if `cache:clear` itself fails. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/cache.html]

## Design and UI conventions
- Prefer inactive states to hiding elements; disabled tabs use `.nav-tabs.nav-tabs-contained > li.disabled`. [devdocs: https://devdocs.mautic.org/en/7.2/design/availability.html]
- Twig `securityIsGranted('bundle:level:permission')` controls visibility, and the backend must still enforce the permission. [devdocs: https://devdocs.mautic.org/en/7.2/design/displaying_elements_based_on_user_permissions.html]
- Empty states: `@MauticCore/Helper/no-information.html.twig` with a context-specific `tip` and optional `link`. [devdocs: https://devdocs.mautic.org/en/7.2/design/feedback.html#no-results-template]
- Flash messages: PHP `addFlashMessage($key, $params, $type='notice')` with keys in `flashes.ini`; JS `Mautic.addInfoFlashMessage`/`addErrorFlashMessage` + `Mautic.setFlashes`. [devdocs: https://devdocs.mautic.org/en/7.2/design/flash_messages.html]
- Bell notifications: `NotificationModel::addNotification($message, $type, $isRead, $header, $iconClass, $datetime, $user, $deduplicateValue, $deduplicateDateTimeFrom)`; header must be a translation key. [devdocs: https://devdocs.mautic.org/en/7.2/design/notifications.html#creating-a-notification]
- Quick filters: pass `quickFilters` to `@MauticCore/Helper/list_toolbar.html.twig`; `Mautic.listQuickFilter()` fills `#list-search`. [devdocs: https://devdocs.mautic.org/en/7.2/design/quick_filters.html]
- Twig `configGetParameter('name'[, default])` reads configuration values. [devdocs: https://devdocs.mautic.org/en/7.2/design/retrieving_system_information.html]
- CSS utilities: flex, gap and spacing classes with `-sm/-md/-lg` suffixes. [devdocs: https://devdocs.mautic.org/en/7.2/design/utilities.html]
- Labels: sentence case; "Apply" not "Save changes"; "Log in/Log out"; "Move to trash" for recoverable deletes; capitalised feature nouns (Contact, Segment, Campaign, Email, Form, Landing Page, Asset, Plugin, Theme, User, Role, Webhook). [devdocs: https://devdocs.mautic.org/en/7.2/design/labelling.html#action-labels]

## Procedures
- Migrate a bundle to autowiring: add `Config/services.php` and the Extension class, delete command/subscriber/form definitions from `config.php`, keep or alias string ids, wire scalars with `->arg()`, verify with `rm -rf var/cache && bin/console`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#how-to-migrate] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html]
- Return an AJAX view with JS lifecycle: `delegateView()` with `activeLink`, `route`, `mauticContent`; define `Mautic.<x>OnLoad/OnUnload`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#ajax-content-callbacks]
- Custom events: 7.2 constants class + event class + dispatch; 8.0 event class only, single-argument dispatch, subscribe on `EventClass::class`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#custom-events]

## Terminology
- Prose uses Contact, Segment, Plugin, Theme, Landing Page; code keeps `lead`, `LeadBundle`, `lead:leads:viewother`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions]
- Permission notation `bundle:level:permission`; firewall names `main`, `public`, `api`, `catchall`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#how-permissions-work]

## Discrepancies with 7.x code
| Docs claim | Code (7.2.1) |
|---|---|
| `config.php` service definitions "won't work in Mautic 6" [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] | Still processed by `ServicePass` [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:33-75 @7.x]; removed in 8.x [PR #17470] |
| "Mautic doesn't auto-wire native services other than commands and controllers" [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#autowired-services] | `Config/services.php` autowires all non-excluded classes [code: app/bundles/CoreBundle/Config/services.php:23-53 @7.x] |
| Config written to `app/config/local.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-configuration] | `config/local.php` [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:195-216 @7.x] |
| `trans()` returns `''` for a missing key [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#using-the-translator-service] | Delegates to Symfony (returns the key); retries locale `EN` on bad syntax [code: app/bundles/CoreBundle/Translation/Translator.php:42-49 @7.x] |
| Bit list 1…128, 512, 1024 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#how-permissions-work] | 256 = `publishown` [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:455-477 @7.x] |
| `standard_entity` registers 5 methods [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#route-definitions] | 10 named endpoints [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:123-201 @7.x] |
| PHP template helpers (`$view['slots']`, `.html.php`) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#template-helpers] | Twig templates under `Resources/views` [code: app/bundles/CoreBundle/Resources/views/Default/content.html.twig:1-27 @7.x] |
| Route debugging via `php app/console router:debug` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#debugging-routes] | Console lives at `bin/console` [code: composer.json:215-230 @7.x] |
| Custom-event example `dispatch($eventName, $event)` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#custom-events] | Symfony signature is `dispatch($event, $eventName)` (single argument in 8.x) [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#custom-events] |
| Translator type-hint `Symfony\Component\Translation\TranslatorInterface` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#using-the-translator-service] | Mautic's `Translator` decorates the Symfony contracts translator [code: app/bundles/CoreBundle/DependencyInjection/Compiler/TranslationsPass.php:27-29 @7.x] |

Gaps: devdocs do not document admin bypass of permissions, permission caching, event priorities, `CoreParametersHelper`,
the `MAUTIC_*` env mapping, the asset pipeline, or most of the `Mautic.*` JS API; rely on code and references/behaviour.md.
[devdocs: https://devdocs.mautic.org/en/7.2/index.html]
