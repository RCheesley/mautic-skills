# Plugin development — version notes

## 1. History that explains current behaviour
- Install/update events `ON_PLUGIN_INSTALL` / `ON_PLUGIN_UPDATE` exist since Mautic 4.2.0 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html].
- Mautic 3 introduced Symfony environment variables and autowired commands [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-configuration] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#remove-commands-subscribers-and-forms].
- The `[Controller::class, 'action']` route format is recommended since Mautic 4 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#route-definitions].
- The integrations framework (IntegrationsBundle) was introduced in 2.15/3.x; `AbstractIntegration` is marked "To be removed in Mautic 6.0" yet remains in 7.2.1 [code: integrations-plugins-marketplace §1, §12 @7.x].

## 2. 5.x
- Autowiring and autoconfigure added; subscribers and form types can be dropped from `config.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html].
- PHP templates removed; views must be Twig at `@Bundle/...html.twig`; validate with `lint:twig` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
- `local.php` moved from `app/config/local.php` to `config/local.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html#continuous-integration].
- IntegrationsBundle expects service id `mautic.integration.<name>`; alias it in `services.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html#the-integration-class].
- Tests use `static::getContainer()` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
- IntegrationsBundle, PluginBundle and MarketplaceBundle templates moved to Twig; plugins that override those views must move too [PR #11862] [PR #11960] [PR #11560] (~v5.0).
- `IntegrationsBundle/Configuration/PluginConfiguration.php` was removed (listed in UPGRADE-5.0.md) [PR #11032] (~v5.0).
- `ConfigFormNotesInterface` adds notes to integration config forms [PR #11451] (~v5.0); `INTEGRATION_BEFORE_CONTACT_FIELD_CHANGES`/`INTEGRATION_BEFORE_COMPANY_FIELD_CHANGES` let plugins filter recorded sync changes [PR #10512] (~v5.0).
- 5.1: `mautic:plugins:reload` runs DDL outside a transaction [PR #13249]; a plugin that gains its first version is updated and its migrations run [PR #13423]; integration classes are autoconfigured [PR #13521]; `INTEGRATION_CONFIG_ON_GENERATE_AUTH_URL` rewrites OAuth2 URLs [PR #13434] (all ~v5.1.0).
- 5.2: the migration engine skips commit after MySQL's implicit DDL commit [PR #14440] (v5.2.2); legacy request logs show `[REDACTED]` for Authorization tokens [PR #14277] (v5.2.1).

## 3. 6.x
- The docs announced removal of `config.php` service definitions in Mautic 6; 7.2.1 code still processes them, so this did not happen in 6.x or 7.x [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:31-64 @7.x].
- `PluginBundleBase::onPluginInstall`/`onPluginUpdate`/`updatePluginSchema`/`onPluginUninstall` and `AbstractPluginBundle::onPluginUpdate` were removed; schema work runs from `PluginEvents::ON_PLUGIN_INSTALL`/`ON_PLUGIN_UPDATE` [code: UPGRADE-6.0.md:27-33 @7.x]. The removing PR is not identified in the PR inputs.
- `MauticFactory::getDatabase()` was removed; plugin install/update classes receive the connection by DI [PR #14418] (~v6.0.0) [code: UPGRADE-6.0.md:34 @7.x].
- `FieldModel::getUniqueIdentiferFields()` was removed [PR #14144] (~v6.0.0).
- `LeadEvent::getLead()` has a native `Lead` return type and `LeadEvent` is `final` [PR #13842] (v6.0.0) [code: app/bundles/LeadBundle/Event/LeadEvent.php:10,22 @7.x].

## 4. 7.x minors
- 7.x enables Symfony attribute validation constraints on entities [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms_advanced.html#using-entity-attribute-constraints].
- 7.2: `uri`-only menu items render [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#menu-item-definitions].
- 7.2: `BuilderEvent::addTokensFromHelper()` / `getTokensFromHelper()` deprecated [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#deprecated-methods].
- 7.2: Preference Center slot labels customisable from the page display event [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#customizing-preference-center].
- 7.2: `ApiPlatformPermissionContextEvent` documented for API Platform permission rewriting [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#api-permission-context-event].
- 7.2: IntegrationsBundle service aliases `mautic.integrations.sync.service` and `mautic.integrations.subscriber.controller` deprecated in favour of FQCN [code: app/bundles/IntegrationsBundle/Config/services.php:91-94 @7.x].
- 7.0.0: `PluginEvents::PLUGIN_IS_PUBLISHED_STATE_CHANGING` lets a listener veto publishing, and credential changes clear stored tokens [PR #13696] (v7.0.0); the IntegrationsBundle `TestPass` lets plugin tests mock OAuth2 HTTP [PR #15084] (v7.0.0).
- 7.0.2: `PluginUpdateEvent::getMetadata()` returns `?array`, `null` for plugins without entities [PR #15951] (v7.0.2).
- 7.1.0: jQuery events `mautic:onPageLoad:before`/`after` and a plugin version badge in the config modal [PR #15789] (v7.1.0).
- 7.2.0: childless classes became `final` (IntegrationsBundle DAOs, bundled integrations such as `OneSignalIntegration`), `protected` members `private` [PR #16888] [PR #16902] (v7.2.0); legacy field-mapping pagination reads POST [PR #16202] (v7.2.0).
- 7.2: child controllers and models take dependencies via `#[Required] autowire*()` setters [PR #16880]; IntegrationsBundle services are autowired in `services.php` [PR #16781]; Guzzle is 7.14 [PR #16559] (all ~v7.2).
- Bundled plugins require `mautic/core-lib ^7.0` [code: plugins/MauticCrmBundle/composer.json:1-17 @7.x].
- 7.x moved to `twbs/bootstrap 5.3.8` after 7.2.1 (unreleased; [PR #17767]); plugin admin UI built against Bootstrap 3 classes may need review (8.x snapshot is still on bootstrap-sass 3.4.1 until the forward merge) [code: 8x-changes §8 @8.x].

## 5. 8.x delta (unreleased; branch snapshot 2026-10-15)
Platform: PHP 8.4, Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4, PHPUnit 13 [code: 8x-changes §7 "Porting a plugin" @8.x].

Events
- Dispatch by event class everywhere except plugin-owned names, campaign registration names, CRUD groups and webhook type ids [code: 8x-changes §3.1 @8.x].
- 225 constants removed; `ApiEvents`, `ConfigEvents`, `CoreEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents`, `UserEvents` deleted [code: 8x-changes §3.3 @8.x].
- Kept-but-not-dispatched constants (Channel, Webhook builder, Page hit, Report, Point build, Stage build, Form build/submit, many Lead) silently break old subscribers [code: 8x-changes §3.2 @8.x].
- Shared events became abstract with concrete subclasses; constructors may not receive services [code: 8x-changes §3.4 @8.x].
- Campaign actions must use `batchEventName` + `PendingEvent`; `ON_CAMPAIGN_TRIGGER_ACTION` paths removed; `associatedActions`/`anchorRestrictions` ignored [code: 8x-changes §4 CampaignBundle @8.x].
- `PluginInstallEvent::class` / `PluginUpdateEvent::class` replace the constants [devdocs: https://devdocs.mautic.org/en/8.0/plugins/installation.html#install-and-update-events].

Wiring
- `config.php` `services` (incl. `models`, `menus`) no longer read; `ServicePass`, `TwigPass`, `ModelPass`, `PermissionsPass` removed [code: 8x-changes §4 Core @8.x].
- Plugin `routes` in `config.php` keep working; core moved to `#[Route]` [code: 8x-changes §4 Core @8.x].
- Many string service ids removed (`mautic.security`, `mautic.helper.*`, `mautic.cache.adapter.*`, model aliases) [code: 8x-changes §4 Core @8.x].
- `ModelFactory::getModel()` resolves only via static `getName()` on the model [code: 8x-changes §4 Core @8.x].

Classes and signatures
- `FormController` removed → `AbstractFormController` / `AbstractStandardFormController`; `CommonController` helpers `protected` [code: 8x-changes §4 Core @8.x].
- `AbstractPermissions::definePermissions()` removed; no-arg constructor; permission classes are services [code: 8x-changes §4 Core @8.x].
- `CommonRepository`/`CommonEntity` abstract; repository public methods need return types; `FormModel` methods typed [code: 8x-changes §4 Core @8.x].
- Every class constant typed; overriding constants must be typed [code: 8x-changes §4 Core @8.x].
- 300+ classes `final` (models, repositories, `MailHelper`, `IpLookupHelper`, `CookieHelper`, CRM integrations, many events) [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#final-classes].
- `ClassMetadataBuilder::addLead()`/`addContact()` removed; Doctrine attributes preferred [code: 8x-changes §4 Core @8.x].
- `CacheStorageHelper` removed; use `CacheProviderInterface::getSimpleCache()`; miss returns `null` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/cache.html#replacing-cachestoragehelper].
- Symfony constraints must use named arguments [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/forms_advanced.html#data-validation].
- `$request->get()` must be replaced by `query`/`request`/`attributes` access [code: 8x-changes §7 @8.x].

## 6. Porting checklist 7.x → 8.x
1. Raise constraints to PHP 8.4 and `mautic/core-lib` 8.x [code: 8x-changes §7 @8.x].
2. Replace every `*Events::CONST` subscriber key and second `dispatch()` argument with the event class (extension-points.md) [code: 8x-changes §7 @8.x].
3. Campaign actions → `batchEventName` + `PendingEvent` [code: 8x-changes §7 @8.x].
4. Copy parent signatures exactly on overrides; type constants and redeclared properties [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
5. Stop extending `final` classes; compose instead [code: 8x-changes §7 @8.x].
6. Replace removed classes and string service ids [code: 8x-changes §7 @8.x].
7. Move permissions to constructor-only definitions registered in `services.php`; move menus and remaining `config.php` services to `services.php` [code: 8x-changes §7 @8.x].
8. Update Doctrine usage (`getEntityManager()`, `ArrayParameterType`, composite expressions from finished lists) [code: 8x-changes §7 @8.x].
9. Tests: PHPUnit 13, `dg/bypass-finals` [code: 8x-changes §7 @8.x].
To support 7.x and 8.x from one codebase, key subscribers on classes and add `defined()`-guarded constants, and add native types now (allowed on 7.x) [code: 8x-changes §7 @8.x].

## 7. Uncertainty
- 8.x is unreleased; version strings are not bumped and 7.2.1 work is not yet merged forward [code: 8x-changes §8 @8.x].
- UPGRADE-8.0.md contradicts itself about kept constants; the code diff wins [code: 8x-changes §3.2, §8 @8.x].
- Doctrine attribute migration is partial; mapping style will keep changing [code: 8x-changes §8 @8.x].

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
