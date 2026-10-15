# Plugin development — what the official docs say

Source: developer docs at devdocs.mautic.org, 7.2 branch (8.0 branch where marked). Many plugin pages carry the banner "The content for this page requires a major update. The legacy page contains outdated and potentially inaccurate information"; 13 service/miscellaneous pages contain only that banner [devdocs: https://devdocs.mautic.org/en/7.2/plugins/getting_started.html]. Where docs and 7.x code disagree, the code statement is in behaviour.md and the discrepancy is listed in section 7 below.

Contents: 1 Pages · 2 Plugin basics · 3 config.php · 4 Autowiring · 5 Lifecycle and database · 6 Permissions, MVC, translations, cache · 7 Doc errors and discrepancies · 8 Procedures · 9 Terminology · 10 8.0 docs changes · 11 Gaps

## 1. Pages
| Topic | URL |
|---|---|
| Getting started | https://devdocs.mautic.org/en/7.2/plugins/getting_started.html |
| Structure | https://devdocs.mautic.org/en/7.2/plugins/structure.html |
| Config file | https://devdocs.mautic.org/en/7.2/plugins/config.html |
| Autowiring | https://devdocs.mautic.org/en/7.2/plugins/autowiring.html |
| Mautic vs Symfony | https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html |
| Event listeners | https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html |
| Installation / update | https://devdocs.mautic.org/en/7.2/plugins/installation.html |
| Database / migrations | https://devdocs.mautic.org/en/7.2/plugins/database.html |
| Permissions | https://devdocs.mautic.org/en/7.2/plugins/permissions.html |
| MVC | https://devdocs.mautic.org/en/7.2/plugins/mvc.html |
| Cache | https://devdocs.mautic.org/en/7.2/plugins/cache.html |
| Translations | https://devdocs.mautic.org/en/7.2/plugins/translations.html , https://devdocs.mautic.org/en/7.2/plugin_services/translator.html |
| Dependencies | https://devdocs.mautic.org/en/7.2/plugins/dependencies.html |
| CI | https://devdocs.mautic.org/en/7.2/plugins/continuous_integration.html |
| Upgrade 4→5 | https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html |
| Upgrade 7→8 (8.0 only) | https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html |
| Extension pages | https://devdocs.mautic.org/en/7.2/plugin_extensions/ (api, campaigns, categories, channels, contacts, emails, forms, forms_advanced, landing_pages, maintenance, points, reports, sms, ui; integrations/webhooks/manipulating_contacts are stubs) |

## 2. Plugin basics
- Plugins are Symfony bundles in `plugins/`, namespaced `MauticPlugin\<Plugin Folder Name>\` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/getting_started.html].
- Do not override core classes from a plugin; contribute the hook to core as a PR [devdocs: https://devdocs.mautic.org/en/7.2/plugins/getting_started.html].
- Minimum structure: `Config/config.php` + `<Name>Bundle.php` extending `Mautic\IntegrationsBundle\Bundle\AbstractPluginBundle` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/structure.html].
- Full example layout: `Assets/{images,css,js}`, `Config/`, `Controller/`, `Entity/`, `EventListener/`, `Form/Type/`, `Migrations/Version_0_0_1.php`, `Model/`, `Helper/`, `Security/Permissions/`, `Translations/en_US/{flashes,messages}.ini`, `Tests/{Unit,Functional}/`, `Views/` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/structure.html]. In practice the bundled plugins put Twig under `Resources/views/` [code: bundled-plugins §0.1 @7.x].
- Do not bundle dependencies in the distributable; use Composer plus the Marketplace [devdocs: https://devdocs.mautic.org/en/7.2/plugins/dependencies.html].
- Mautic's own config framework lets one PHP file per bundle declare routes, services, menus and parameters (`MauticCoreExtension` and listeners) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#php-everything].
- Mautic's permission system is bitwise and does not use Symfony voters [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#firewalls-and-user-access-management].
- Entities default to Doctrine's static PHP mapping; annotations are allowed but cannot be mixed [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#support-for-entity-annotations].

## 3. `config.php`
- General keys: `name` (Plugin Manager), `description` (not displayed), `author`, `version` (PHP-standardised; `version_compare()` decides upgrade eligibility) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#general-config-items].
- Firewalls: `api` → `/api/*` (API auth), `main` → `/s/*` (User auth), `public` → `/*` (none), `catchall` → `/*` compiled last (Landing Page custom URLs) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#routing-firewalls].
- Route keys: `path`, `controller` (`[Controller::class, 'action']` recommended since 4; invokable allowed), `method`, `defaults`, `requirements`, `format`, `standard_entity` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#route-definitions].
- Menu keys: `route`, `routeParameters`, `uri`, `parent`, `priority` (default 9999), `access` (permission or `admin`), `checks` (`parameters`, `request`, `integration`), `id`, `iconClass`, `linkAttributes`, `children` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-definitions].
- Service groups and auto tags: `command(s)` → `console.command`, `controllers`, `events`, `forms`, `models` (deprecated; gone in 8.0), `permissions`, `other` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#service-types].
- Service keys: `class`, `arguments`, `alias`, `serviceAlias(es)`, `tag(s)`, `tagArguments`, `factory`, `methodCalls`, `decoratedService`, `public`, `synthetic`, `file`, `configurator`; `abstract` and `lazy` are accepted but ignored [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#service-definitions].
- Mautic service tags: `mautic.sms_transport`, `mautic.sms_callback_handler`, `mautic.email_transport`, `mautic.email_stat_helper`, `mautic.permissions`, `mautic.basic_integration`, `mautic.builder_integration`, `mautic.authentication_integration`, `mautic.config_integration`, `mautic.sync_integration`, `mautic.sync.notification_handler` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#mautic-service-tags].
- `categories`: `'plugin:helloWorld' => 'mautic.helloworld.world.categories'` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#category-config-items].
- `parameters`: defaults read via `CoreParametersHelper`, `%mautic.key%` or env `MAUTIC_KEY`; values saved to `config/local.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#parameters-config-items].
- Configuration UI tab: subscriber on `ConfigEvents::CONFIG_ON_GENERATE` and `CONFIG_PRE_SAVE`, form type, template `_config_{formAlias}_widget.html.twig` (panel structure), label `mautic.config.tab.<formAlias>` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#custom-config-parameters].

## 4. Autowiring
- Mautic 5 added Symfony autowiring and autoconfigure [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html].
- Recommended `services.php`: defaults autowire/autoconfigure/public; `load()` with `DEFAULT_EXCLUDES` + plugin excludes; repositories loaded separately [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#introducing-services-php].
- The bundle needs `DependencyInjection/<Bundle minus Bundle>Extension.php` loading `services.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#introducing-services-php].
- Commands autowired since Mautic 3; subscribers and form types since 5 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#remove-commands-subscribers-and-forms].
- Core keeps string aliases for BC; plugins switching to FQCN ids should release a major version [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#consider-backward-compatibility-for-services].
- Depend on interfaces; bind scalars with `->arg()` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#special-cases].
- Controllers: constructor or action DI; invokable controllers suggested for new code [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#dependency-injection-in-controllers].

## 5. Lifecycle and database
- Install/update events `ON_PLUGIN_INSTALL` / `ON_PLUGIN_UPDATE` since 4.2.0; no uninstall hook; prefer migrations if the plugin manages schema [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html].
- Migrations: extend `\Mautic\IntegrationsBundle\Migration\AbstractMigration`; name `Version_X_Y_Z.php` after the plugin version; `isApplicable(Schema)` must return false once applied because every file runs on each upgrade; prefix table and index names [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations].
- `AbstractMigration` API: `tablePrefix`, `isApplicable()`, `up()`, `addSql()`, `columnsToString()`, `concatPrefix()`, `generateAlterTableForeignKeyStatement()`, `generateIndexStatement()` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations].
- `ClassMetadataBuilder` helpers and the 191-character limit for indexed strings [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#entity-php-static-function-mapping].

## 6. Permissions, MVC, translations, cache
- Permission bits double; `full` is the highest; Roles store the sum [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#how-permissions-work].
- `getName()` must equal the bundle name in camelCase and match the file (`HelloWorldBundle` → `helloWorld`, `HelloWorldPermissions.php`) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#getname].
- `isGranted(array)`, `isGranted(array, 'MATCH_ONE')`, `isGranted(array, 'RETURN_ARRAY')` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions].
- Twig `securityIsGranted('bundle:level:perm')` for UI; always enforce on the backend too [devdocs: https://devdocs.mautic.org/en/7.2/design/displaying_elements_based_on_user_permissions.html].
- `delegateView()`, `delegateRedirect()`, `postActionRedirect()` (`returnUrl` default `/s/dashboard`), `passthroughVars` (`activeLink`, `route`, `mauticContent`, `callback`, `target`, `replaceContent`) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#delegateview-args].
- JS lifecycle `Mautic.<mauticContent>OnLoad/OnUnload`; set the `mauticContent` slot for full page loads [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#ajax-content-callbacks].
- Translations: `Translations/<locale>/<domain>.ini`; `en_US` mandatory; domains `messages`, `flashes`, `validators`; keys use dots and underscores; `%placeholder%`; plurals with `%count%` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html].
- Cache: `var/cache/<env>`; `cache:clear --env=<env>`; delete the folder if the command fails; CacheBundle offers PSR-6/16 tag-aware adapters; `mautic:cache:clear` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/cache.html].
- Flash messages: keys in `flashes.ini`, `addFlashMessage($key, $params, $type)` [devdocs: https://devdocs.mautic.org/en/7.2/design/flash_messages.html].
- Labels: sentence case, "Apply" not "Save changes", "Log in", "Move to trash" for recoverable deletes [devdocs: https://devdocs.mautic.org/en/7.2/design/labelling.html].

## 7. Doc errors and discrepancies (checked against code)
| Docs claim | Code reality (7.2.1) | Sources |
|---|---|---|
| `config.php` services "won't work in Mautic 6" | Still processed by `ServicePass` on 7.x; removed on 8.x | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:31-64 @7.x] |
| "Mautic doesn't auto-wire native services other than commands and controllers" | Every bundle is autowired by default | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#autowired-services] [code: app/config/services.php:10-32 @7.x] |
| Migrations only with `AbstractPluginBundle` | Core subscriber runs them for any plugin | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations] [code: app/bundles/PluginBundle/EventListener/PluginSubscriber.php:34-37 @7.x] |
| installation.rst prose says `MauticPlugin\IntegrationsBundle\...` and folder `Migration` | Class is `Mautic\IntegrationsBundle\Bundle\AbstractPluginBundle`; folder is `Migrations` | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html#plugin-migrations] [code: app/bundles/IntegrationsBundle/Migration/Engine.php:68-80 @7.x] |
| Permission strings `plugin:helloWorld:...` | First segment = permission object `getName()`; bundled plugins use `focus:items:view` | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions] [code: plugins/MauticFocusBundle/Config/config.php:51 @7.x] |
| Email transport tag `mautic.email_transport` (prose: `mautic.email.transport_type`), Swiftmailer example, `/mailer/{transport}/callback` | Symfony Mailer transport factory; route `/mailer/callback` | [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-transports] [code: app/bundles/EmailBundle/Config/config.php:99-102 @7.x] |
| Channel broadcast "`CoreEvents::CHANNEL_BROADCAST`" | `ChannelEvents::CHANNEL_BROADCAST` | [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/channels.html#extending-broadcasts] [code: app/bundles/ChannelBundle/ChannelEvents.php:25 @7.x] |
| `php app/console router:debug` | Symfony 2-era path; use `bin/console debug:router` | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#debugging-routes] |
| Config subscriber `extends EventSubscriberInterface` | must `implements` (fixed in 8.0 docs) | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#config-event-subscriber] |
| 7.2 custom event `dispatch($eventName, $event)` | Symfony order is `dispatch($event, $eventName)` | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#custom-events] |
| MVC page uses `.html.php` and `$view[...]` helpers | Twig is mandatory since 5 | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mvc.html#template-helpers] |
| CI example pins PHP 7.4/8.0, Mautic 4.x, `whitelist` | Outdated for 7.x | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/continuous_integration.html] |
| Campaign decision example calls `addCondition()` | Use `addDecision()` | [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#registering-a-campaign-decision] |
| 8.0 forms page unchanged (`FORM_ON_BUILD`) | 8.x dispatches `FormBuilderEvent` by class; constant kept but not dispatched | [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/forms.html] [code: 8x-changes §3.2 @8.x] |

## 8. Procedures (docs)
- **Create a minimal plugin** — folder, `config.php` with name/description/author/version, bundle class extending `AbstractPluginBundle` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/structure.html].
- **Migrate to autowiring** — add `services.php` + Extension, delete command/subscriber/form definitions from `config.php`, alias string ids, bind scalars [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#how-to-migrate].
- **Add plugin settings to Configuration** — defaults in `parameters`; config subscriber; form type; widget template; tab translation [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#custom-config-parameters].
- **Schema migration** — add `Migrations/Version_X_Y_Z.php`, guard with `isApplicable()`, bump `version` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html#database-migrations].
- **Custom permissions** — `Security/Permissions/<Bundle>Permissions.php`, bits with `full` highest, `buildForm()`, `getName()`; register via `services.permissions` (7.2) or `services.php` (8.0) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#creating-custom-permissions].
- **Plugin CI** — GitHub workflow installs Mautic (`mautic:install --force`) and plugins (`mautic:plugins:install`), runs cs-fixer, PHPStan, Rector, Twig lint and PHPUnit; `phpunit.xml` sets `KERNEL_CLASS=AppTestKernel` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/continuous_integration.html].
- **Upgrade 4→5** — `local.php` moved to `config/local.php`; FQCN controllers; Twig; `static::getContainer()`; Rector/CS/PHPStan [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
- **Upgrade 7→8** — see version-notes.md [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

## 9. Terminology
- Capitalised feature nouns in prose: Plugin, Theme, Contact, Segment, Campaign, Email, Form, Landing Page, Category, User, Role, Integration, Webhook, Widget [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html].
- Code keeps "lead" (`LeadBundle`, `lead:leads:viewother`); prose says Contact [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions].
- Permission notation "bundle:level:permission"; "level" = permission area [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#how-permissions-work].

## 10. 8.0 docs changes relevant to plugins
- Advanced routing keys on `RouteEvent` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/config.html#advanced-routing].
- Custom menus via `knp_menu.menu` / `knp_menu.renderer` in `services.php`; `mautic.menu.builder` alias removed [devdocs: https://devdocs.mautic.org/en/8.0/plugins/config.html#registering-a-custom-menu].
- `ConfigEvents` removed → `ConfigBuilderEvent`, `ConfigPreSaveEvent`, `ConfigPostSaveEvent` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/config.html#config-event-subscriber].
- Class-name dispatch: old constant either fatals or silently receives nothing [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch].
- Custom events: single-argument dispatch enforced by PHPStan rule `mautic.singleArgumentDispatch` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#custom-events].
- Install/update: `PluginInstallEvent::class` / `PluginUpdateEvent::class` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/installation.html#install-and-update-events].
- Permissions: no-arg constructor; registered in `services.php`; `getSynonym(): array`; `isGranted(array $userPermissions, $name, $level): bool` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html].
- Models: implement `MauticModelInterface` with static `getName()` for `getModel('key')` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/mvc.html#registering-a-model].
- Cache: `CacheStorageHelper` removed; miss returns `null` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/cache.html#replacing-cachestoragehelper].
- New `update_m7_to_m8` page: signature changes, `FormController` removal, 300+ final classes, typed constants, `DG\BypassFinals` for tests [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

## 11. Gaps in the docs
- No documentation of `mautic:plugins:reload` semantics, `is_missing`, or Plugin Manager flow; no uninstall [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html].
- No docs on the assets pipeline for plugins, Twig equivalents of template helpers, webhook type registration, or segment filter extension [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/webhooks.html] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/contacts.html].
- Integrations page is a stub; see mautic-integrations [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/integrations.html].
