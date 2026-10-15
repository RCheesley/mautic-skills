---
name: mautic-plugin-development
description: "Building a Mautic plugin end to end on 7.x and porting it to 8.x: the plugins/<Name>Bundle layout and MauticPlugin namespace rules, the bundle class (AbstractPluginBundle), Config/config.php keys (routes, menu, services, parameters), Config/services.php autowiring, permission classes, entities and plugin Migrations (Version_x_y_z), the install/update lifecycle (mautic:plugins:reload, PluginInstallEvent), translations, Twig views, the catalogue of extension points (campaign events, form fields/actions, point triggers, segment filters, reports, widgets, webhooks, tokens, channels, transports, API routes, UI hooks) with 7.x event constants and 8.x event classes, plugin tests, and Marketplace packaging (composer type mautic-plugin). Use whenever a task says write, build or scaffold a Mautic plugin, add a campaign action from a plugin, plugin migration, plugin not showing up or won't install, port my plugin to Mautic 8, getSubscribedEvents, services.php, or touches plugins/*Bundle/."
---
# Mautic plugin development

## Scope
A Mautic Plugin is a Symfony bundle under `plugins/` that extends Mautic through `Config/config.php`, autowired services, Doctrine entities, its own migrations and event subscribers on core events [devdocs: https://devdocs.mautic.org/en/7.2/plugins/getting_started.html] [code: app/AppKernel.php:158-187 @7.x].
This skill covers the plugin skeleton, wiring, lifecycle, the extension-point catalogue and packaging, for 7.x with the 8.x delta.
Out of scope: the integration frameworks (`AbstractIntegration`, `BasicIntegration`, sync engine, auth providers, Marketplace internals) live in **mautic-integrations**; Themes live in **mautic-theme-development**; the deep behaviour of each extended feature lives in the feature skill named in [references/extension-points.md](references/extension-points.md).

## Expected behaviour (essentials)
Discovery and naming
- The kernel loads a plugin only if `plugins/<Dir>/<File>Bundle.php` exists at depth 1 and class `\MauticPlugin\<Dir>\<File>Bundle` exists and is a Symfony `Bundle`; the directory name is the namespace segment, so `MauticPlugin\HelloWorldBundle\HelloWorldBundle` must live in `plugins/HelloWorldBundle/HelloWorldBundle.php` [code: app/AppKernel.php:158-187 @7.x].
- A bundle class that defines `MINIMUM_MAUTIC_VERSION` higher than the running version is silently not registered (no error, no log) [code: app/AppKernel.php:176-181 @7.x].
- Namespaces containing `MauticPlugin\` are classified as plugins and exposed in the container parameter `mautic.plugin.bundles`; anything else that is not `Mautic\` is ignored by Mautic's metadata builder [code: app/bundles/CoreBundle/DependencyInjection/Builder/BundleMetadataBuilder.php:53-119 @7.x] [code: app/config/config.php:22-23 @7.x].
- `Mautic\IntegrationsBundle\Bundle\AbstractPluginBundle` is an empty subclass of `Mautic\PluginBundle\Bundle\PluginBundleBase`; extend it as the docs recommend [code: app/bundles/IntegrationsBundle/Bundle/AbstractPluginBundle.php:12 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/structure.html].

Configuration and services
- `Config/config.php` must `return` an array; core reads `name`, `description`, `version`, `author`, `routes`, `menu`, `services`, `parameters`, `categories` and `ip_lookup_services` [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/ConfigMetadata.php:17-116 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html].
- Every `parameters` default becomes the container parameter `%mautic.<key>%`, overridable by the env var `MAUTIC_<KEY>`; the default's type drives typecasting [code: app/config/parameters.php:16-47 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#parameters-config-items].
- A plugin **without** `Config/services.php` is autoloaded by `app/config/services.php` (autowire, autoconfigure, public, `DEFAULT_EXCLUDES`, plus `Entity/*Repository.php`) [code: app/config/services.php:10-32 @7.x].
- A plugin **with** `Config/services.php` is skipped by that default loader, so it must ship `DependencyInjection/<Name>Extension.php` that loads the file; a `services.php` without the extension registers nothing [code: app/config/services.php:21-23 @7.x] [code: plugins/MauticCrmBundle/DependencyInjection/MauticCrmExtension.php:12-22 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#introducing-services-php].
- `Config`, `Entity`, `Event`, `Migrations`, `Security`, `Tests`, `Views`, `DTO`, `Exception` and similar directories are excluded from autowiring, so classes there are not services [code: app/bundles/CoreBundle/DependencyInjection/MauticCoreExtension.php:14-29 @7.x].
- On 7.x the `services` array in `config.php` is still processed by `ServicePass`, which auto-tags groups: `events` → `kernel.event_subscriber`, `forms` → `form.type`, `permissions` → `mautic.permissions`, `controllers` → `controller.service_arguments`, `integrations` → `mautic.integration`, `menus` → `knp_menu.menu`, `models` → `mautic.model` (deprecated) [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:31-64 @7.x]. 8.x stops reading this array [code: 8x-changes §4 Core "services group ... no longer read" @8.x].
- Scalar or array constructor arguments cannot be autowired; bind them explicitly with `->arg('$name', '%mautic.key%')` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#special-cases].

Routes, menus, permissions
- Routes are grouped by firewall: `main` is prefixed `/s` and needs a logged-in User, `api` is prefixed `/api`, `public` has no prefix and no authentication, `catchall` is compiled last [code: app/bundles/CoreBundle/Loader/RouteLoader.php:28-84 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#routing-firewalls].
- Route names must be unique across all bundles; the first matching route wins [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#routing-firewalls].
- Menu items default to priority 9999 and are sorted by priority [code: app/bundles/CoreBundle/Menu/MenuHelper.php:32,142,177 @7.x]; items defining only a `uri` render from 7.2 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-definitions].
- `*Permissions.php` classes in `Security/Permissions/` extending `AbstractPermissions` are discovered from the plugin directory [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/PermissionClassMetadata.php:20-49 @7.x]; tagged `mautic.permissions` services are registered by `getName()` [code: app/bundles/CoreBundle/DependencyInjection/Compiler/PermissionsPass.php:12-20 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:44-48 @7.x].
- Permission strings are `<getName()>:<level>:<permission>`; the first segment selects the permission object, Administrators are granted everything, and bits must be powers of two with `full` the highest [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#how-permissions-work].

Install, update, schema
- `mautic:plugins:reload` (aliases `mautic:plugins:install`, `mautic:plugins:update`) and the **Install/Upgrade Plugins** button flag removed plugins `is_missing`, un-flag returning ones, update changed ones, install new ones, then report counts [code: app/bundles/PluginBundle/Facade/ReloadFacade.php:24-49 @7.x] [code: app/bundles/PluginBundle/Command/ReloadCommand.php:13-35 @7.x].
- A plugin counts as updated only when the stored version is empty and the config now has one, or `version_compare(old, new) === -1`; a lower or equal version does nothing [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:67-95 @7.x].
- On install, Mautic creates tables from the plugin's Doctrine metadata only if none of its tables exist yet, and runs **no** migrations [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:102-126 @7.x] [code: app/bundles/PluginBundle/Bundle/PluginDatabase.php:35-65 @7.x].
- On update, Mautic runs **every** file in `Migrations/` in `scandir` (alphabetical) order, each guarded by its own `isApplicable(Schema)`, all inside one transaction rolled back on a DBAL exception [code: app/bundles/IntegrationsBundle/Migration/Engine.php:26-95 @7.x] [code: app/bundles/IntegrationsBundle/Migration/AbstractMigration.php:23-45,122-127 @7.x].
- Migration classes must be named `MauticPlugin\<Bundle>\Migrations\<FileBasename>` and extend `Mautic\IntegrationsBundle\Migration\AbstractMigration` [code: app/bundles/IntegrationsBundle/Migration/Engine.php:68-80 @7.x].
- Nothing deletes a `plugins` row or drops plugin tables; removed plugins are only flagged missing and there is no uninstall hook [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:26-39 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html].
- `PluginInstallEvent` / `PluginUpdateEvent::checkContext()` compare against the plugin's display `name`, not the bundle name [code: app/bundles/PluginBundle/Event/PluginInstallEvent.php:41-44 @7.x] [code: app/bundles/PluginBundle/Event/PluginUpdateEvent.php:48-51 @7.x].

Events and 8.x
- On 7.x most core events dispatch under string constants on `*Events` classes; subscribe with those constants [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#available-events].
- On 8.x almost every core event dispatches by event class; a subscriber keyed on a removed constant fatals, and one keyed on a kept constant or raw string silently receives nothing [code: 8x-changes §3.1-3.2 @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch].
- Names a plugin defines itself (campaign `batchEventName`, condition/decision `eventName`, form action/validator `eventName`) stay string-dispatched on 8.x [code: 8x-changes §3.1 @8.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:1192 @8.x].

## Where it lives
| Concern | Path(s) @7.x |
|---|---|
| Plugin discovery | `app/AppKernel.php:158-202`; `app/bundles/CoreBundle/DependencyInjection/Builder/BundleMetadataBuilder.php`; `.../Builder/Metadata/{ConfigMetadata,PermissionClassMetadata}.php` |
| Default autowiring for plugins | `app/config/services.php`; `MauticCoreExtension::DEFAULT_EXCLUDES` |
| `config.php` services processing | `app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php` |
| Routes / menus | `app/bundles/CoreBundle/Loader/RouteLoader.php`; `app/bundles/CoreBundle/Menu/MenuHelper.php` |
| Permissions | `app/bundles/CoreBundle/Security/Permissions/{AbstractPermissions,CorePermissions}.php`; `Compiler/PermissionsPass.php` |
| Reload / install / update | `app/bundles/PluginBundle/{Command/ReloadCommand,Facade/ReloadFacade,Helper/ReloadHelper,Bundle/PluginDatabase,EventListener/PluginSubscriber}.php` |
| Plugin migrations | `app/bundles/IntegrationsBundle/Migration/{Engine,AbstractMigration}.php` |
| Entity / table | `Mautic\PluginBundle\Entity\Plugin` → `plugins` (unique `bundle`, `is_missing`, `version`) |
| Plugin events | `app/bundles/PluginBundle/PluginEvents.php` |
| Marketplace | `app/bundles/MarketplaceBundle/`; `app/bundles/CoreBundle/Helper/ComposerHelper.php` (see mautic-integrations) |
| Reference plugins | `plugins/MauticTagManagerBundle/` (entity + permissions + routes), `plugins/MauticFocusBundle/` (campaign/form/categories), `plugins/MauticZapierBundle/` (config only) |
Full map: [references/code-map.md](references/code-map.md).

## How to change or extend it
- Pick the hook from [references/extension-points.md](references/extension-points.md); subscribe to the 7.x constant and the 8.x class when you need both versions [code: 8x-changes §7 @8.x].
- Do not override core classes from a plugin; propose the missing hook to core as a PR [devdocs: https://devdocs.mautic.org/en/7.2/plugins/getting_started.html].
- For a schema change: change the entity, bump `version` in `config.php`, and add `Migrations/Version_<x>_<y>_<z>.php` whose `isApplicable()` returns false once applied [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations] [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:67-95 @7.x].
- Prefix every table and index name through `concatPrefix()` or `MAUTIC_TABLE_PREFIX` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations].
- Keep string service ids you already published as aliases; switching a plugin's service ids to FQCN is a major-version change [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#consider-backward-compatibility-for-services].
- Ship `en_US` translations for every key (menu labels, permission labels, campaign labels, `mautic.config.tab.<formAlias>`) [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/translator.html#translation-file-and-directory-structure] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#custom-config-parameters].
- Enforce permissions in controllers, not only with Twig `securityIsGranted()` [devdocs: https://devdocs.mautic.org/en/7.2/design/displaying_elements_based_on_user_permissions.html].
- Publish through the Marketplace with Composer `type` `mautic-plugin` and `extra.install-directory-name` equal to the bundle directory; do not bundle `vendor/` [code: integrations-plugins-marketplace §11 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/dependencies.html].
- Integration classes (auth, sync, config modal) follow **mautic-integrations**.

### Minimal plugin skeleton (works on 7.x)
```
plugins/HelloWorldBundle/
├── HelloWorldBundle.php                      # bundle class
├── composer.json                             # type mautic-plugin
├── Config/config.php                         # name/version/routes/menu/parameters
├── Config/services.php                       # autowiring
├── DependencyInjection/HelloWorldExtension.php
├── Controller/WorldController.php
├── EventListener/CampaignSubscriber.php
├── Security/Permissions/HelloWorldPermissions.php
├── Entity/World.php, Entity/WorldRepository.php
├── Migrations/Version_1_0_1.php
├── Translations/en_US/messages.ini
├── Resources/views/World/index.html.twig     # @HelloWorld/World/index.html.twig
└── Assets/img/icon.png
```
Layout follows the docs and the bundled plugins [devdocs: https://devdocs.mautic.org/en/7.2/plugins/structure.html] [code: bundled-plugins §0.1 @7.x].

```php
<?php // HelloWorldBundle.php
declare(strict_types=1);
namespace MauticPlugin\HelloWorldBundle;
use Mautic\IntegrationsBundle\Bundle\AbstractPluginBundle;
class HelloWorldBundle extends AbstractPluginBundle {}
```

```php
<?php // Config/config.php
declare(strict_types=1);
return [
    'name'        => 'Hello World',          // shown in Plugin Manager; checkContext() compares this
    'description' => 'Example plugin.',
    'version'     => '1.0.0',                // version_compare() drives updates + migrations
    'author'      => 'Acme',
    'routes'      => [
        'main' => [                          // served under /s, requires login
            'mautic_helloworld_index' => [
                'path'       => '/hello/{page}',
                'controller' => 'MauticPlugin\HelloWorldBundle\Controller\WorldController::indexAction',
                'defaults'   => ['page' => 1],
            ],
        ],
    ],
    'menu' => [
        'main' => [
            'helloworld.menu.index' => [     // key = translation key
                'route'     => 'mautic_helloworld_index',
                'access'    => 'helloWorld:worlds:view',
                'iconClass' => 'ri-earth-line',
                'priority'  => 10,
            ],
        ],
    ],
    'parameters' => [
        'helloworld_api_timeout' => 30,      // %mautic.helloworld_api_timeout%, env MAUTIC_HELLOWORLD_API_TIMEOUT
    ],
];
```
Keys and shapes mirror `plugins/MauticTagManagerBundle/Config/config.php:5-41` [code: plugins/MauticTagManagerBundle/Config/config.php:5-41 @7.x].

```php
<?php // Config/services.php
declare(strict_types=1);
use Doctrine\Bundle\DoctrineBundle\DependencyInjection\Compiler\ServiceRepositoryCompilerPass;
use Mautic\CoreBundle\DependencyInjection\MauticCoreExtension;
use Symfony\Component\DependencyInjection\Loader\Configurator\ContainerConfigurator;

return function (ContainerConfigurator $configurator): void {
    $services = $configurator->services()->defaults()->autowire()->autoconfigure()->public();
    $excludes = [];
    $services->load('MauticPlugin\\HelloWorldBundle\\', '../')
        ->exclude('../{'.implode(',', array_merge(MauticCoreExtension::DEFAULT_EXCLUDES, $excludes)).'}');
    $services->load('MauticPlugin\\HelloWorldBundle\\Entity\\', '../Entity/*Repository.php')
        ->tag(ServiceRepositoryCompilerPass::REPOSITORY_SERVICE_TAG);
};
```
Pattern copied from `plugins/MauticTagManagerBundle/Config/services.php` [code: plugins/MauticTagManagerBundle/Config/services.php:9-28 @7.x].

```php
<?php // DependencyInjection/HelloWorldExtension.php  (name = bundle class with Bundle → Extension)
declare(strict_types=1);
namespace MauticPlugin\HelloWorldBundle\DependencyInjection;
use Symfony\Component\Config\FileLocator;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Extension\Extension;
use Symfony\Component\DependencyInjection\Loader\PhpFileLoader;
final class HelloWorldExtension extends Extension
{
    public function load(array $configs, ContainerBuilder $container): void
    {
        (new PhpFileLoader($container, new FileLocator(__DIR__.'/../Config')))->load('services.php');
    }
}
```
[code: plugins/MauticCrmBundle/DependencyInjection/MauticCrmExtension.php:12-22 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#introducing-services-php]

```php
<?php // EventListener/CampaignSubscriber.php - registers a campaign action; runs on 7.x and 8.x
namespace MauticPlugin\HelloWorldBundle\EventListener;
use Mautic\CampaignBundle\CampaignEvents;
use Mautic\CampaignBundle\Event\CampaignBuilderEvent;
use Mautic\CampaignBundle\Event\PendingEvent;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
final class CampaignSubscriber implements EventSubscriberInterface
{
    public const ON_SAY_HELLO = 'helloworld.on_campaign_say_hello'; // plugin-owned name, string-dispatched on 7.x and 8.x
    public static function getSubscribedEvents(): array
    {
        $events = [CampaignBuilderEvent::class => ['onBuild', 0], self::ON_SAY_HELLO => ['onSayHello', 0]];
        if (defined(CampaignEvents::class.'::CAMPAIGN_ON_BUILD')) { // 7.x dispatches by name
            $events[CampaignEvents::CAMPAIGN_ON_BUILD] = ['onBuild', 0];
        }
        return $events;
    }
    public function onBuild(CampaignBuilderEvent $event): void
    {
        $event->addAction('helloworld.say_hello', ['label' => 'helloworld.campaign.say_hello', 'batchEventName' => self::ON_SAY_HELLO]);
    }
    public function onSayHello(PendingEvent $event): void
    {
        foreach ($event->getPending() as $log) { /* do work */ $event->pass($log); } // every log must be passed or failed
    }
}
```
Dual-key pattern and `batchEventName` rule from the 8.x guidance; `PendingEvent` API from code [code: 8x-changes §7 @8.x] [code: app/bundles/CampaignBundle/Event/PendingEvent.php:46-205 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#executing-a-campaign-action].

```php
<?php // Security/Permissions/HelloWorldPermissions.php (7.x constructor form)
namespace MauticPlugin\HelloWorldBundle\Security\Permissions;
use Mautic\CoreBundle\Security\Permissions\AbstractPermissions;
use Symfony\Component\Form\FormBuilderInterface;
class HelloWorldPermissions extends AbstractPermissions
{
    public function __construct(array $params) { parent::__construct($params); $this->addStandardPermissions(['worlds']); }
    public function getName(): string { return 'helloWorld'; }            // first segment of 'helloWorld:worlds:view'
    public function buildForm(FormBuilderInterface &$builder, array $options, array $data): void
    { $this->addStandardFormFields('helloWorld', 'worlds', $builder, $data); }
}
```
[code: plugins/MauticTagManagerBundle/Security/Permissions/TagManagerPermissions.php:10-31 @7.x]

```php
<?php // Migrations/Version_1_0_1.php - runs on upgrade only; must be idempotent
namespace MauticPlugin\HelloWorldBundle\Migrations;
use Doctrine\DBAL\Schema\Schema;
use Mautic\IntegrationsBundle\Migration\AbstractMigration;
class Version_1_0_1 extends AbstractMigration
{
    protected function isApplicable(Schema $schema): bool
    { return !$schema->getTable($this->concatPrefix('hello_worlds'))->hasColumn('is_enabled'); }
    protected function up(): void
    { $this->addSql('ALTER TABLE '.$this->concatPrefix('hello_worlds').' ADD is_enabled TINYINT(1) DEFAULT 0 NOT NULL'); }
}
```
[code: app/bundles/IntegrationsBundle/Migration/AbstractMigration.php:105-127 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations]

`composer.json`: `{"name": "acme/mautic-hello-world", "type": "mautic-plugin", "extra": {"install-directory-name": "HelloWorldBundle"}, "require": {"mautic/core-lib": "^7.0"}}` [code: plugins/MauticCrmBundle/composer.json:1-17 @7.x].
Activate with `bin/console mautic:plugins:reload` and clear the cache [code: app/bundles/PluginBundle/Command/ReloadCommand.php:13-35 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/cache.html].

#### What changes for 8.x
- Key subscribers on event classes only (`CampaignBuilderEvent::class`); the `defined()` branch becomes dead [code: 8x-changes §3.1, §7 @8.x].
- Permissions: no-argument constructor, `$this->params` injected by setter after construction, and register `$services->set(HelloWorldPermissions::class)` in `services.php` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html#registering-the-permission-class-as-a-service] [code: 8x-changes §4 Core @8.x].
- Move anything left in the `config.php` `services` array (including `menus`) to `services.php`; plugin `routes` stay in `config.php` [code: 8x-changes §4 Core @8.x].
- Add native types matching the parents, stop extending classes that became `final`, and require PHP 8.4 / `mautic/core-lib` 8.x [code: 8x-changes §7 "Porting a plugin" @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- Install/update subscribers use `PluginInstallEvent::class` / `PluginUpdateEvent::class` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/installation.html#install-and-update-events].

## How to test it
- Unit tests extend `PHPUnit\Framework\TestCase`; DB/HTTP tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase` [code: plugins/MauticTagManagerBundle/Tests/Unit/Security/Permissions/TagManagerPermissionsTest.php:11 @7.x] [code: plugins/MauticFocusBundle/Tests/Controller/FocusControllerTest.php:14 @7.x].
- Core's PHPUnit config already includes `plugins/*Bundle/Tests` [code: app/phpunit.xml.dist:23,53 @7.x].
- Copy from: `app/bundles/PluginBundle/Tests/Helper/ReloadHelperTest.php` (install/update rules), `app/bundles/PluginBundle/Tests/Controller/PluginControllerTest.php` (runs `mautic:plugins:install`), `plugins/MauticTagManagerBundle/Tests/Unit/Security/Permissions/TagManagerPermissionsTest.php`, `plugins/MauticFocusBundle/Tests/Controller/FocusControllerTest.php` [code: integrations-plugins-marketplace §10 @7.x].
- A good plugin regression test asserts the observable outcome: the route returns 200 for a permitted User and 403 otherwise, the campaign action appears in `CampaignBuilderEvent::getActions()`, or a migration's `isApplicable()` is false after `up()` ran.
- No core test covers `Migration\Engine`; test your migrations yourself [code: grep of app/bundles/*/Tests for Migration\Engine, none @7.x].
Full detail: [references/test-patterns.md](references/test-patterns.md).

## Version notes
- 5.x introduced autowiring/autoconfigure, Twig-only views, FQCN controllers and moved `local.php` to `config/local.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
- Install/update events exist since 4.2.0 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html].
- 7.x still processes `config.php` `services`, although the docs said they "won't work in Mautic 6" [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:31-64 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html].
- 7.2: `uri`-only menu items render; `BuilderEvent::addTokensFromHelper()` deprecated; Preference Center slot labels editable from `PageDisplayEvent` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-definitions] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#deprecated-methods] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#customizing-preference-center].
- 8.x: class-keyed events, 225 constants removed, `CoreEvents`/`ConfigEvents`/`DashboardEvents`/`ApiEvents`/`UserEvents`/`IntegrationEvents`/`StatEvents` deleted, `FormController` removed, 300+ `final` classes, typed constants [code: 8x-changes §3.3, §4 @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
Full detail: [references/version-notes.md](references/version-notes.md).

## Pitfalls
- A `Config/services.php` without `DependencyInjection/<Name>Extension.php` silently registers no services [code: app/config/services.php:21-23 @7.x].
- Migration files run alphabetically: `Version_1_10_0.php` runs before `Version_1_2_0.php`; guard each with `isApplicable()` instead of relying on order [code: app/bundles/IntegrationsBundle/Migration/Engine.php:86-95 @7.x].
- Fresh installs create tables from the current entity mapping and skip migrations; an entity added in a later version is never created on an existing install unless a migration creates it [code: app/bundles/PluginBundle/Bundle/PluginDatabase.php:35-40 @7.x] [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:102-126 @7.x].
- Forgetting to bump `version` means `mautic:plugins:reload` neither runs migrations nor persists new name/description/author [code: app/bundles/PluginBundle/Helper/ReloadHelper.php:67-95 @7.x] [code: integrations-plugins-marketplace 9.7 @7.x].
- A wrong directory/namespace pair or a too-low Mautic version for `MINIMUM_MAUTIC_VERSION` makes the plugin vanish without an error [code: app/AppKernel.php:170-181 @7.x].
- Config, translation and service changes need a cache clear; if `cache:clear` itself fails with class-not-found errors, delete `var/cache/<env>` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/cache.html].
- On 8.x, a subscriber keyed on a kept constant such as `FormEvents::FORM_ON_BUILD`, `PointEvents::POINT_ON_BUILD`, `ReportEvents::REPORT_ON_BUILD` or `LeadEvents::TIMELINE_ON_GENERATE` loads fine and never fires [code: 8x-changes §3.2 @8.x].
- The docs' permission notation `plugin:helloWorld:worlds:view` does not match 7.x code: the first segment is resolved as a permission object name, so `plugin:` selects PluginBundle's own `plugin:plugins:manage` object; in-repo plugins use `focus:items:view` and `tagManager:tagManager:view` [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x] [code: plugins/MauticFocusBundle/Config/config.php:51 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions]. The `plugin:` prefix is used for Category bundle keys (`plugin:focus`) [code: plugins/MauticFocusBundle/Config/config.php:58-63 @7.x].
- The docs say migrations run only for bundles extending `AbstractPluginBundle`; in 7.x code the core `PluginSubscriber` runs the engine on every plugin update regardless of base class [code: app/bundles/PluginBundle/EventListener/PluginSubscriber.php:34-37 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations].
- The email-transport docs (tag `mautic.email_transport`, Swiftmailer example, `/mailer/{transport}/callback`) are outdated: 7.x builds transports through Symfony Mailer's transport factory and handles callbacks on `/mailer/callback` via `EmailEvents::ON_TRANSPORT_WEBHOOK` [code: app/bundles/EmailBundle/Mailer/Transport/TransportFactory.php:13-58 @7.x] [code: app/bundles/EmailBundle/Config/config.php:99-102 @7.x] [code: app/bundles/EmailBundle/Controller/PublicController.php:539-540 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-transports].
- `mautic.sync_integration` and `mautic.authentication_integration` tags are not autoconfigured; tag them explicitly (see mautic-integrations) [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:26-33 @7.x].
- Several devdocs examples contain bugs (`extends EventSubscriberInterface`, reversed `dispatch()` arguments, `addCondition()` for decisions, `.html.php` templates); trust code [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#config-event-subscriber] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/event_listeners.html#custom-events].

## Related skills
- mautic-architecture — bundle layout, kernel, container and event conventions shared with core.
- mautic-integrations — integration classes, auth, sync engine, config modal, Marketplace internals.
- mautic-theme-development — Themes (not plugins).
- mautic-users-and-permissions — Roles, permission bits, `CorePermissions` in depth.
- mautic-campaigns / mautic-forms / mautic-points-and-stages / mautic-segments — semantics behind those extension points.
- mautic-reports-and-dashboard / mautic-webhooks / mautic-channels / mautic-emails — reports, widgets, webhook types, channels, transports and tokens.
- mautic-rest-api — API routes, serializer groups and API Platform for plugin entities.
- mautic-testing — test base classes, fixtures and CI in depth.
- mautic-upgrades-and-versions — version policy and the full 8.x upgrade path.

## Reference files
- references/behaviour.md — numbered behaviour specification for discovery, wiring, lifecycle, migrations, permissions, events.
- references/extension-points.md — full catalogue: every extension point, 7.x hook, 8.x equivalent, required keys, deep-dive skill.
- references/code-map.md — files, classes, tables, commands, parameters, tags and tests by concern.
- references/docs-digest.md — what devdocs.mautic.org says (7.2 and 8.0), procedures, terminology, doc errors.
- references/test-patterns.md — base classes, representative tests, skeletons for plugin tests and CI.
- references/version-notes.md — 4.x/5.x/6.x history, 7.x minors and the 8.x porting checklist.
- references/pr-history.md — not yet generated; PR-derived history is added in a later pass.
