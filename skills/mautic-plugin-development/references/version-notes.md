# Plugin development — version notes

## 1. History that explains current behaviour
- Install/update events `ON_PLUGIN_INSTALL` / `ON_PLUGIN_UPDATE` exist since Mautic 4.2.0 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html].
- Mautic 3 introduced Symfony environment variables and autowired commands [devdocs: https://devdocs.mautic.org/en/7.2/plugins/mautic_vs_symfony.html#custom-configuration] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#remove-commands-subscribers-and-forms].
- The `[Controller::class, 'action']` route format is recommended since Mautic 4 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/config.html#route-definitions].
- The integrations framework (IntegrationsBundle) came into core in 3.0 from the `mautic-inc/plugin-integrations` repository [PR #8210] (~v3.0.0); `AbstractIntegration` is marked "To be removed in Mautic 6.0" yet remains in 7.x [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:54 @7.x].

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
- The docs announced removal of `config.php` service definitions in Mautic 6; 7.x code still processes them, so this did not happen in 6.x or 7.x [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/ServicePass.php:31-64 @7.x].
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
- Unreleased on 7.x (7.3.0-rc): `twbs/bootstrap 5.3.8` replaces bootstrap-sass 3 [PR #17767] [code: app/composer.json:113 @7.x], and core PHP, Twig and JS markup moved to Bootstrap 5 names (`data-bs-toggle`, `data-bs-dismiss`, `form-label`, `ms-*`/`mb-*` spacing) and native Bootstrap 5 JS APIs [PR #17826] [PR #17827] [PR #17829] [PR #17830] [code: app/bundles/PluginBundle/Assets/js/plugin.js:85 @7.x]. Review plugin admin views and JS that use Bootstrap 3 attributes. 8.x has the same Bootstrap version [code: app/composer.json:114 @8.x].
- Unreleased on 7.x (7.3.0-rc): plugin install creates only the plugin's own tables when a schema listener's table (such as `messenger_messages`) already exists [PR #17977]; `SearchHelpEvent` is deprecated and no longer dispatched, so plugin search-help listeners are not called [PR #18069] [code: UPGRADE-7.0.md:69 @7.x]; the Marketplace list filters by package type and shows richer package details [PR #17764].
- Fixed on the 7.2 branch after 7.2.2 (milestone 7.2.3, not yet in the 7.x snapshot): an unreadable directory under `plugins/` no longer makes kernel boot fail with HTTP 500 [PR #18025].

## 5. 8.x delta (in development; 8.x snapshot pinned in SOURCES.md)
Platform: PHP 8.4 [code: UPGRADE-8.0.md:5 @8.x], Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4 [code: app/composer.json:19,35,39,87 @8.x] [code: UPGRADE-8.0.md:1154 @8.x] [PR #17361], PHPUnit 13 with `dg/bypass-finals` [code: composer.json:33,44 @8.x] [code: app/tests/bootstrap.php:5-9 @8.x]. 7.2.2 and the 7.x work up to 2026-11-16 are merged into 8.x, so the 7.3 changes above are on 8.x too [PR #18036] [PR #18236].

Removed bundles and base classes
- `MauticSocialBundle` and `mautic/plugin-social` are gone: Facebook, Twitter/X, Instagram, Foursquare, Social Monitoring, tweets, the `twitter.tweet` campaign action and the `plugin.loginSocial` form field. Remove those actions and fields before upgrading, then run `mautic:plugins:reload` to flag the plugin missing; its tables and settings are kept [code: UPGRADE-8.0.md:9-20 @8.x] [PR #17473]. The Clearbit plugin is removed [code: UPGRADE-8.0.md:33 @8.x].
- `AbstractSsoServiceIntegration` and `AbstractSsoFormIntegration` are removed. SSO plugins keep the `sso_service`/`sso_form` features and listen to `PreAuthenticationEvent`/`FormAuthenticationEvent`, running their own authentication [code: UPGRADE-8.0.md:501 @8.x] [PR #18118].
- OneSignal, Outlook and the Mailchimp/Constant Contact/iContact integrations no longer extend `AbstractIntegration`; code that relied on inherited legacy methods on those classes breaks [code: UPGRADE-8.0.md:26,598,610 @8.x] [PR #18113] [PR #18139].
- `FormController` removed → `AbstractFormController` / `AbstractStandardFormController` [code: UPGRADE-8.0.md:243 @8.x] [PR #17481]; `CommonController::accessDenied()` removed → `throwAccessDenied()` [code: UPGRADE-8.0.md:359 @8.x] [PR #17059].
- `CampaignExecutionEvent`, `LegacyEventDispatcher`, `EventArrayTrait`, `AbstractEventAccessor::getConfig()` and `ConditionEvent`/`DecisionEvent::getResult()`/`setResult()` removed [code: UPGRADE-8.0.md:35-79,230-232 @8.x] [PR #18159] [PR #17097].
- `SearchHelpEvent` removed; supply `quickFilters` instead [code: UPGRADE-8.0.md:233 @8.x].
- `FormModel::dispatchEventFromBatch()` and `LeadModel::dispatchEventFromBatch()` removed; `dispatchEvent()` covers single and batch saves [code: UPGRADE-8.0.md:515 @8.x] [PR #18125].
- `CommonRepository::getPublishedByDateExpression()` removed → `getPublishedByDateOrmExpression()` or `getPublishedByDateDbalExpression()` [code: UPGRADE-8.0.md:516 @8.x] [PR #18157].
- `CacheStorageHelper` removed; use `CacheProviderInterface::getSimpleCache()`; a miss returns `null` [code: UPGRADE-8.0.md:295-316 @8.x] [PR #17033] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/cache.html#replacing-cachestoragehelper].
- `BuilderEvent::addTokensFromHelper()`/`getTokensFromHelper()` removed [code: UPGRADE-8.0.md:355 @8.x] [PR #17059].

Events
- Dispatch by event class everywhere except plugin-owned names, campaign registration names, CRUD groups and webhook type ids [code: UPGRADE-8.0.md:266,891 @8.x] [code: app/bundles/CampaignBundle/Executioner/Dispatcher/ActionDispatcher.php:40-41 @8.x].
- `ApiEvents`, `ConfigEvents`, `CoreEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents` and `UserEvents` are deleted; the removed constants are listed per bundle in UPGRADE-8.0.md [code: UPGRADE-8.0.md:80-201,441-500 @8.x] [PR #17654] [PR #17625] [PR #17241].
- Kept-but-not-dispatched constants (Channel, Webhook builder, Page hit, Report, Point build, Stage build, Form build/submit, Category bundle list, many Lead) silently break old subscribers [code: UPGRADE-8.0.md:760,784,785,826,846,891,906,953 @8.x].
- Shared events became abstract with concrete subclasses; `CommonEvent` and `CommonRepository` are abstract [code: UPGRADE-8.0.md:87,112,1186 @8.x] [PR #17524].
- Core listeners use `#[AsEventListener]`; plugin subscribers still work, but plugins that extend a core listener class must be autoconfigured and re-add the attribute on overrides; equal-priority order changes [code: UPGRADE-8.0.md:635-638 @8.x] [PR #17988].
- Campaign actions must use `batchEventName` + `PendingEvent`; the `eventName`/`callback` action path and all `ON_CAMPAIGN_TRIGGER_ACTION` constants are removed; `associatedActions`/`associatedDecisions`/`anchorRestrictions` are ignored, use `connectionRestrictions` [code: UPGRADE-8.0.md:231,234-237,268-281 @8.x] [PR #17097] [PR #17032].
- `PluginInstallEvent::class` / `PluginUpdateEvent::class` replace the removed constants [code: UPGRADE-8.0.md:756-757 @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/installation.html#install-and-update-events].
- `FormModel::togglePublishStatus()` dispatches the generic `EntityTogglePublishEvent` for every entity [code: UPGRADE-8.0.md:31 @8.x] [PR #18137].

Wiring
- `config.php` `services` (including `models` and `menus`) is no longer read; `ServicePass`, `TwigPass`, `ModelPass`, `PermissionsPass` removed [code: UPGRADE-8.0.md:205,386,1108 @8.x] [PR #17470] [PR #17116] [PR #17117] [PR #17133] [PR #17121].
- Plugin `routes` in `config.php` keep working; core moved to `#[Route]`, scanned only in `app/bundles/*/Controller` [code: app/bundles/CoreBundle/Loader/RouteLoader.php:74-92 @8.x] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:110-121 @8.x].
- String service ids removed include `mautic.security`, `symfony.filesystem`, `mautic.helper.cache_storage` and the model aliases [code: UPGRADE-8.0.md:267,295,324,325,414 @8.x] [PR #17121] [PR #17134] [PR #17133].
- `ModelFactory::getModel()` resolves only via static `getName()` on the model [code: UPGRADE-8.0.md:414,980 @8.x] [PR #17133].

Doctrine
- Core and bundled entities are attribute-mapped; `loadMetadata()` still works for plugins through `AttributeAndStaticPhpDriver`, and attribute-only plugin entities are now registered [code: UPGRADE-8.0.md:207 @8.x] [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/EntityMetadata.php:61-71 @8.x] [PR #17532] [PR #18179].
- Removed mapping helpers: `ClassMetadataBuilder::addLead()`/`addContact()`, `DateAddedTrait::addDateAddedField()`, `addTranslationMetadata()`, `addFiltersMetadata()`, `addProjectsField()`, `addVariantMetadata()` (for attribute-mapped entities), `loadFixedFieldMetadata()` [code: UPGRADE-8.0.md:24,30,206-210,228,241 @8.x] [PR #17460] [PR #17456] [PR #18054] [PR #18055] [PR #18056] [PR #18146] [PR #18142].
- ORM 3 / DBAL 4 changes that reach plugin code: `getEntityManager()` access, `ArrayParameterType`, composite expressions built from finished lists, `isOwnershipParent()` replaced by an attribute, Doctrine's own association builders [code: UPGRADE-8.0.md:424-437,1154-1185 @8.x] [PR #17361].

Classes and signatures
- `AbstractPermissions::definePermissions()` removed; no-arg constructor; permission classes are services [code: UPGRADE-8.0.md:991-1015 @8.x] [PR #17079].
- Native parameter and return types for plugin extension points: nullable dates and categories on entity setters, `array` parameters on entity setters, controllers, events, helpers and models, typed integration data, object parameters, nullable booleans, and native `array`/`iterable` property types; overrides must stay compatible with the parent [code: UPGRADE-8.0.md:1818-1975 @8.x] [PR #18230]. See section 6 step 4.
- Repository and model methods carry native parameter and `array` return types [code: UPGRADE-8.0.md:1021-1056,1198 @8.x] [PR #17131] [PR #17365] [PR #17564].
- Every class constant is typed; overriding constants must be typed [code: UPGRADE-8.0.md:1188 @8.x] [PR #17543]. Base entity properties declare native types [code: UPGRADE-8.0.md:1189 @8.x] [PR #17877].
- About 330 more classes are `final` than on 7.x (2527 of 2808 non-test classes), including `MailHelper`, `IpLookupHelper`, `CookieHelper` and `LeadRepository` [code: grep of app/bundles and plugins for final class, 2527 of 2808 non-test classes @8.x] [code: grep of app/bundles and plugins for final class, 2195 of 2781 non-test classes @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php @8.x]. `LeadEvent` is no longer `final` because the lifecycle event classes extend it [code: app/bundles/LeadBundle/Event/LeadEvent.php:10 @8.x].
- Symfony constraints must use named arguments [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/forms_advanced.html#data-validation].
- Core replaced almost every `$request->get()` call with explicit `query`/`request`/`attributes` access (251 non-test call sites on 7.x, 10 on 8.x); plugins should do the same [code: grep of app/bundles for $request->get(, 10 non-test matches @8.x] [code: grep of app/bundles for $request->get(, 251 non-test matches @7.x].
- Admin CSS: custom utility classes, custom background colour classes and unused Bootstrap 3 compatibility styles are removed; use Bootstrap 5 utilities [code: UPGRADE-8.0.md:519-594 @8.x] [PR #17873] [PR #18266].

## 6. Porting checklist 7.x → 8.x
1. Raise constraints to PHP 8.4 and `mautic/core-lib` 8.x [code: UPGRADE-8.0.md:5 @8.x] [code: app/composer.json:19 @8.x].
2. Replace every `*Events::CONST` subscriber key and second `dispatch()` argument with the event class (extension-points.md) [code: UPGRADE-8.0.md:641,701 @8.x].
3. Campaign actions → `batchEventName` + `PendingEvent`; conditions/decisions type `ConditionEvent`/`DecisionEvent` and call `pass()`/`fail()`/`setAsApplicable()` [code: UPGRADE-8.0.md:35-69,231 @8.x].
4. Work through "Native parameter and return types for plugin extension points" in UPGRADE-8.0.md: copy parent signatures on overrides, pass `[]` not `null` to `array` parameters, pass `\DateTime` objects not strings to date setters, pass entities not IDs to association setters, and keep redeclared properties' native types [code: UPGRADE-8.0.md:1818-1975 @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
5. Type overriding constants; stop extending `final` classes; compose instead [code: UPGRADE-8.0.md:1188 @8.x].
6. Replace removed classes, methods and string service ids (the "Removed code" section of UPGRADE-8.0.md) [code: UPGRADE-8.0.md:22-594 @8.x].
7. Move permissions to constructor-only definitions registered in `services.php`; move menus and remaining `config.php` services to `services.php` [code: UPGRADE-8.0.md:991-1015,1108 @8.x].
8. Update Doctrine usage for ORM 3 / DBAL 4, and replace removed `ClassMetadataBuilder` and trait helpers with attributes (or keep the rest of `loadMetadata()`) [code: UPGRADE-8.0.md:206-241,1154-1185 @8.x].
9. If the plugin extends a core listener class, make it autoconfigured and re-add `#[AsEventListener]` on overrides [code: UPGRADE-8.0.md:636-637 @8.x].
10. Tests: PHPUnit 13, `dg/bypass-finals`; use `AttributeEventListenerRegistrar` to register attribute listeners in unit tests [code: composer.json:33,44 @8.x] [code: app/bundles/CoreBundle/Test/AttributeEventListenerRegistrar.php:10-16 @8.x] [PR #18004].
To support 7.x and 8.x from one codebase, key subscribers on classes and add `defined()`-guarded constants, and add native types now (allowed on 7.x) [code: UPGRADE-8.0.md:641 @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#mautic-8-class-name-event-dispatch].

## 7. Uncertainty
- 8.x is unreleased; `release_metadata.json` still says 7.2.2 [code: app/release_metadata.json @8.x].
- UPGRADE-8.0.md says the `CoreEvents` and `PluginEvents` constants are kept and tells operator listeners to key on `LIST_FILTERS_OPERATORS_ON_GENERATE`; the 8.x code deleted those constants and dispatches the operator event by class. The code wins (behaviour.md Q9) [code: UPGRADE-8.0.md:373,701,745 @8.x] [PR #17241] [PR #17625].
- Attribute mapping is complete for core entities; plugin entities may still mix attributes with `loadMetadata()`, but core's own PHPStan rule flags the static method [code: utils/phpstan/src/Rule/NoLoadMetadataMethodRule.php @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/database.html].

Unreleased 7.x changes (merged after 7.2.2, not in any release yet): see [unreleased-7.x-prs.md](../../mautic-upgrades-and-versions/references/unreleased-7.x-prs.md).
