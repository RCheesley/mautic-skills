# Upgrading from Mautic 7.x to 8.x (authoritative guide)

Snapshot: 7.x = release 7.2.2 plus 181 unreleased merged PRs (`838c9c772ec`, 2026-11-19; see [unreleased-7.x-prs.md](unreleased-7.x-prs.md));
8.x = `c79cf37a57b` (2026-11-22), unreleased. Both are pinned in SOURCES.md. Primary sources: `UPGRADE-8.0.md@8.x` (read in
full), the 7.x and 8.x trees, the PRs merged to 8.x, and devdocs 8.0 [code: UPGRADE-8.0.md @8.x]. Since the previous snapshot
the devdocs page `plugins/update_m7_to_m8` was cut to a pointer to `UPGRADE-8.0.md`, which "the Mautic team keeps up to date"
[devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]. Claims that came from the older, longer version of
that page are now cited to the 8.x code they were checked against.

## Contents
1. Status of 8.x and how to read diffs
2. Platform and dependency changes
3. Event system: dispatch by event class, `#[AsEventListener]`, and the silent-failure trap
4. Campaign builder: legacy action path removed
5. Doctrine mapping moved to attributes
6. Native parameter and return types for plugin extension points
7. Per-bundle BC breaks
8. Behaviour changes users and integrators will see
9. Removed features (including the social bundle)
10. Before you upgrade an install or a plugin: checklist
11. Symfony 8 and Doctrine 3/4 fallout for plugin code
12. Writing code that works on both 7.x and 8.x
13. Porting a plugin from 7.x to 8.x (step by step)
14. How to test a plugin on both 7.x and 8.x
15. What to avoid in new 7.x contributions
16. Open questions and known inconsistencies

---

## 1. Status of 8.x and how to read diffs

- 8.x is development-only. `app/release_metadata.json@8.x` says `"version": "7.2.2"` with `minimum_php_version` 8.4.0; root `composer.json@8.x` requires `mautic/core-lib` `^8.0` and aliases it as `8.0.0-dev` [code: app/release_metadata.json:2-4 @8.x] [code: composer.json:26,127 @8.x]. Do not read the version from the metadata.
- 7.2.2 is an ancestor of 8.x: it was merged in by [PR #18036], which kept the 8.x service registrations. 7.x was then merged into 8.x as one squash commit on 2026-11-17 [PR #18236], carrying the 7.x branch up to [PR #15680] (`0b906d06a02`, 2026-11-16) [code: git merge-base --is-ancestor 7.2.2 c79cf37a57b].
- Because that merge was a squash, `git rev-list 8.x..7.x` still lists 1,931 7.x commits and the merge-base is still the 7.2.2 update (`f28a0120d71`). Compare trees, not ancestry: the unreleased 7.x features before that point are on 8.x (Bootstrap 5.3.8, the unsubscribe email-validation page, `POST /api/companies/batch/addcontacts`, "Any associated company" segment filters, asset ZIP download, `is:never_logged_in`, OpenID Connect login) [code: app/composer.json:114 @8.x] [code: git diff 838c9c772ec c79cf37a57b].
- 7.x PRs merged after 2026-11-16 are not on 8.x yet, for example [PR #17551], [PR #17830], [PR #18070], [PR #18216], [PR #18217] and [PR #18233] [code: git log --first-parent 0b906d06a02..838c9c772ec]. A feature from them that is missing on 8.x is pending, not removed.
- All 7.x migrations are on 8.x; 8.x adds three of its own (§8) [code: app/migrations/ @7.x vs @8.x].
- Scale: `git diff 838c9c772ec c79cf37a57b` touches 4,238 files (+70,348 / −95,780); most of it is typing, Rector, PHPStan, event-dispatch and removal work [code: git diff --shortstat 838c9c772ec c79cf37a57b].
- `UPGRADE-8.0.md` is appended per PR, and later entries supersede earlier ones. When it says a constant is "kept for backwards compatibility" but the class is gone in code, the code wins (§16) [code: UPGRADE-8.0.md @8.x] [code: app/bundles/CoreBundle/ @8.x, `CoreEvents.php` absent].

## 2. Platform and dependency changes

| Item | 7.x | 8.x | Source |
|---|---|---|---|
| PHP | 8.2.0 – 8.5.99 | **8.4** minimum (`~8.4`), max 8.5.99 | [code: app/release_metadata.json @7.x] [code: app/composer.json:19 @8.x] [code: UPGRADE-8.0.md "Platform requirements" @8.x] [PR #16993] |
| MySQL / MariaDB | ≥ 8.4.0 / ≥ 10.11.0 | unchanged | [code: app/release_metadata.json @8.x] |
| Symfony | `~7.4.0` | **`~8.1.0`** (all `symfony/*`, incl. dev packages) | [code: app/composer.json:87 @8.x] [PR #17392] [PR #17309] [PR #17411] [PR #17458] |
| Doctrine ORM / DBAL | `^2.14.0` / `^3.6.2 <3.8.0` | **`^3.7` / `^4.4`** | [code: app/composer.json:35,39 @8.x] [PR #17361] |
| doctrine-bundle / migrations-bundle | `^2.7` / `^3.2.2` | `^3.3` / `^4.0` | [PR #17361] [PR #17353] |
| data-fixtures / fixtures-bundle | `^1.6.6` / `^3.4.4` | `^2.2` / `^4.3` | [PR #17353] |
| `doctrine/cache`, `doctrine/common` | present | removed | [PR #17361] |
| API Platform core | `^4.1.0` | `^4.3.0` | [PR #17355] |
| FOSRestBundle | `^3.8` | `^3.9` | [PR #17350] |
| OAuth server bundle | `5.1.3` | `6.0.0` (oauth2-php 2.0; "no BC breaks for Mautic") | [PR #17342] |
| monolog-bundle | `~3.10.0` | `~4.0.2` | [PR #17343] |
| SAML | `javer/sp-bundle ^2.0` | `lightsaml2/sp-bundle ^5.0` + `lightsaml2/symfony-bridge ^6.0` | [code: app/composer.json:61-62 @8.x] [PR #17370] |
| `mautic/plugin-social` | required (`self.version`) | removed | [code: composer.json:65 @7.x] [PR #17473] |
| PHPUnit | `^11.5` | **`^13.0`** | [code: composer.json:44 @8.x] [PR #17004] [PR #17019] [PR #17063] [PR #17163] |
| PHPStan | `^2.2.6`, level 6 | `^2.3.5`, level 6, baseline 6,837 lines, custom rules such as `NoLoadMetadataMethodRule`, `NoServiceInEventConstructorRule`, `mautic.singleArgumentDispatch` | [code: composer.json:39 @8.x] [code: phpstan.neon:7,183,386,413 @8.x] [PR #18142] |
| Rector | — | `^2.8.4`; the one-off `loadMetadata` and `Request::get()` rules are dropped | [code: composer.json:45 @8.x] [PR #18140] |
| Coding standard | php-cs-fixer + ECS | ECS only | [PR #17280] [PR #17362] |
| Tool binaries | `bin/phpunit`, `bin/phpstan`, … | `vendor/bin/*` | [PR #17164] |
| Mocking finals in tests | — | `dg/bypass-finals ^1.11`, enabled in `app/tests/bootstrap.php` | [code: composer.json:33 @8.x] [PR #17366] |

Language-level adoption on 8.x: typed class constants everywhere [PR #16996] [PR #17543]; PHP 8.4 syntax [PR #17007] [PR #17008];
more `final` classes (3,719 → 4,083 files declaring a final class) [PR #17536] [code: grep `^final` app plugins @7.x vs @8.x];
Doctrine mapping as `#[ORM\*]` attributes (§5) [PR #17454] [PR #17532]; event listeners as `#[AsEventListener]` (§3.2)
[PR #17988]; native parameter and return types across extension points (§6) [PR #18230]; validator constraints as attributes
[PR #16963]; Twig functions via `#[AsTwigFunction]` [PR #17015]; core routes as `#[Route]` attributes [PR #17169] [PR #17222] [PR #17231].

## 3. Event system

### 3.1 Dispatch by event class

- Since Symfony 4.3, `EventDispatcherInterface::dispatch($event)` without a name uses `$event::class` as the name. 8.x converts almost every Mautic dispatch to this form [PR #17157] [PR #17160] [PR #17161] [PR #17218] [PR #17625].
- A PHPStan rule on 8.x enforces single-argument dispatch for custom events (`mautic.singleArgumentDispatch`) [code: phpstan.neon:183 @8.x] [PR #17625].
- Subscribe with the class as the key:

```diff
-public static function getSubscribedEvents(): array
-{
-    return [LeadEvents::LEAD_POST_SAVE => ['onLeadPostSave', 0]];
-}
+#[AsEventListener(event: LeadPostSaveEvent::class)]
 public function onLeadPostSave(LeadPostSaveEvent $event): void
 // dispatching your own events:
-$this->dispatcher->dispatch($event, MyEvents::THING_HAPPENED);
+$this->dispatcher->dispatch($event);   // name = $event::class
```
A `getSubscribedEvents()` array keyed on `LeadPostSaveEvent::class` works the same way [code: UPGRADE-8.0.md "Changed code" @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].

### 3.2 `#[AsEventListener]` replaces most core subscribers

- Most core subscribers no longer implement `EventSubscriberInterface`; their methods carry `#[AsEventListener]` and are registered by service autoconfiguration. On 8.x 283 non-test files use the attribute and 6 still implement `EventSubscriberInterface` (Symfony Form subscribers and JMS serializer subscribers, which have their own dispatchers; on 7.x the counts are 0 and 293) [PR #17988] [PR #18003] [PR #18004] [code: grep AsEventListener app/bundles plugins @7.x vs @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].
- A plugin service that extends an abstract core subscriber (`CommonStatsSubscriber`, `NotificationBundle\EventListener\CampaignSubscriber`, …) must be autoconfigured, or its inherited listeners are not registered. Mautic's `Config/services.php` loader sets `autoconfigure: true` by default [code: UPGRADE-8.0.md "Changed code" @8.x].
- PHP does not copy attributes onto an overriding method: a subclass that overrides `onStatsFetch()` loses the listener unless it re-declares `#[AsEventListener]` [code: UPGRADE-8.0.md "Changed code" @8.x].
- Order at equal priority changes: `kernel.event_listener` services register before `kernel.event_subscriber` ones, and attribute listeners run in method-declaration order. If your listener must run before or after a core one, set an explicit `priority` [code: UPGRADE-8.0.md "Changed code" @8.x].
- Before upgrading a plugin: list every class that extends a core class in `EventListener/`, check it is autoconfigured, re-add the attribute on each overridden listener method, and add a `priority` wherever the plugin relied on running next to a core listener. [code: UPGRADE-8.0.md "Changed code" @8.x]

### 3.3 WARNING: the silent-failure trap

- Removed constants fail loudly: referencing `CoreEvents::BUILD_MENU` on 8.x is a fatal "undefined constant" error [code: app/bundles/CoreBundle/CoreEvents.php absent @8.x].
- **Kept constants fail silently.** Some constants still exist on 8.x (as webhook type ids or for BC), but the event is dispatched under its class. A listener keyed on such a constant loads without error and **never runs** [code: UPGRADE-8.0.md "Changed code" @8.x].
- Highest-risk examples: `LeadEvents::LEAD_POST_SAVE` (now `LeadPostSaveEvent`), `FormEvents::FORM_ON_SUBMIT` (now `SubmissionEvent`), `EmailEvents::EMAIL_ON_SEND` / `EMAIL_ON_OPEN` (now `EmailSendEvent` / `EmailOpenEvent`), `PageEvents::PAGE_ON_HIT` (now `PageHitEvent`), all eight `ReportEvents` builder/generator names, all five non-CRUD `ChannelEvents` [code: app/bundles/*/*Events.php @7.x vs @8.x].
- The full kept-constant list is in [event-map-7-to-8.md §3](event-map-7-to-8.md). Check every subscriber against it; a passing PHP lint proves nothing.
- Verify a registration on a running 8.x install with `bin/console debug:event-dispatcher '<FQCN of event>'` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].

### 3.4 Removed constants and deleted classes

- 226 constants were removed; 8 whole classes were deleted (`ApiEvents`, `ConfigEvents`, `CoreEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents`, `UserEvents`, and `SocialEvents` with its bundle) [code: app/bundles/*/*Events.php @7.x vs @8.x] [PR #17473]. The mapping of every removed constant is in [event-map-7-to-8.md §6](event-map-7-to-8.md).

### 3.5 Event classes that changed shape

- Now `abstract` (instantiate a concrete subclass): `CampaignLeadChangeEvent`, `UserBundle\Event\{AuthenticationEvent,UserEvent,RoleEvent}`, `SmsEvent`, `WebhookEvent`, `ApiBundle\Event\{ClientEvent,ApiEntityEvent,ApiSerializationContextEvent}`, `IntegrationsBundle\Event\{InternalContactEvent,InternalCompanyEvent,CompletedSyncIterationEvent,ConfigSaveEvent}`, `DashboardBundle\Event\WidgetDetailEvent`, LeadBundle `CompanyEvent`, `TagEvent`, `LeadNoteEvent`, `LeadDeviceEvent`, `ImportEvent`, `LeadFieldEvent`, `LeadListEvent`, `LeadMergeEvent`, `CompanyMergeEvent`, `TagMergeEvent`, `SaveBatchLeadsEvent`, `ContactExportSchedulerEvent`, and `CoreBundle\Event\CommonEvent` [code: UPGRADE-8.0.md "Changed code" @8.x] [PR #17524].
- `LeadEvent`, `ListChangeEvent`, `AssetEvent` are no longer `final` [code: UPGRADE-8.0.md "Changed code" @8.x].
- `CommonEvent::setEntityManager()` and `$em` removed [PR #17482].
- `ParseEmailEvent` split: criteria methods (`setCriteriaRequest`, `getCriteriaRequests`, `getMarkAsSeenInstructions`) moved to new `PreFetchEmailEvent` [PR #17675].
- `CampaignExecutionEvent` removed. Decision and condition listeners must type `DecisionEvent` / `ConditionEvent`; `getEvent()` returns the `Event` entity, not an array; use `getLog()`, `pass()`/`fail()` (conditions) and `setAsApplicable()` (decisions). `AbstractEventAccessor::getConfig()` and `ScheduledEvent::getEventSettings()` are removed too; use the accessor's typed getters, `getExtraProperties()` and `getEventConfig()` [PR #18159] [PR #17151] [code: UPGRADE-8.0.md "Other removed code" @8.x].
- `CampaignScheduledEvent` folded into `ScheduledEvent`; `CampaignDecisionEvent` removed [PR #17039] [PR #17059].
- `EmailOnTogglePublishEvent` removed: publish toggling dispatches `Mautic\CoreBundle\Event\EntityTogglePublishEvent` for every entity [PR #18137].
- `SearchHelpEvent` removed; list toolbars take quick filters through the `quickFilters` option instead [code: UPGRADE-8.0.md "Other removed code" @8.x].
- `LeadListFiltersOperatorsEvent` constructor lost `$operators`; it starts empty and you call `addOperator()` [code: UPGRADE-8.0.md "Other removed code" @8.x].
- `WidgetDetailEvent`: `setCacheDir()`, `setCacheTimeout()` removed; `$cacheProvider` required; `setTemplateData()` lost `$skipCache` [PR #17034].
- `BuilderEvent::addTokensFromHelper()` / `getTokensFromHelper()` removed [code: UPGRADE-8.0.md "Other removed code" @8.x].
- `PluginIntegrationResponseEvent` is a new class for integration responses [code: app/bundles/PluginBundle/Event/PluginIntegrationResponseEvent.php @8.x].
- Event constructors may no longer receive services (PHPStan `NoServiceInEventConstructorRule`) [code: phpstan.neon:413 @8.x] [PR #17640]. Many events gained native types [PR #17426] [PR #17438] and several became `final`, for example `SubmissionEvent` [code: app/bundles/FormBundle/Event/SubmissionEvent.php:14 @8.x].

## 4. Campaign builder: legacy action path removed

- The legacy action path (`'eventName'`/`'callback'` and per-contact `CampaignExecutionEvent`) is gone: `LegacyEventDispatcher`, `EventArrayTrait`, `CampaignExecutionEvent`, `CampaignDecisionEvent`, `CampaignScheduledEvent` and all `*Events::ON_CAMPAIGN_TRIGGER_ACTION` constants were removed [PR #17097] [PR #17077] [PR #17085] [PR #17039] [PR #18159].
- A campaign action registered without `batchEventName` is **not executed at all** on 8.x [PR #17097] [code: UPGRADE-8.0.md "Other removed code" @8.x].
- Register `batchEventName` => `<Bundle>Events::ON_CAMPAIGN_BATCH_ACTION` (or your own name) and handle `PendingEvent`. This path has worked since Mautic 3, so it is safe on 7.x [code: UPGRADE-8.0.md "Other removed code" @8.x].
- Core actions moved to the batch path: `dwc.push_content`, `tracking.pixel.send`, `plugin.leadpush`, `campaign.sendwebhook`, `focus.show` [code: UPGRADE-8.0.md "Other removed code" @8.x]. The social bundle's `twitter.tweet` action no longer exists at all (§9).
- `ConnectionBuilder::addDeprecatedAnchorRestrictions()` removed: event keys `associatedActions`, `associatedDecisions`, `anchorRestrictions` are ignored, so the builder no longer restricts connections unless you use `connectionRestrictions` [PR #17032].
- `PendingEvent::fail()`, `failAll()`, `failRemaining()` and `failLogs()` take a `string $reason` [code: app/bundles/CampaignBundle/Event/PendingEvent.php:50-112 @8.x].
- `EventScheduler::reschedule()` is removed; `rescheduleLogs()` takes a `Doctrine\Common\Collections\Collection` [PR #17877] [code: UPGRADE-8.0.md "Other removed code" @8.x].
- See mautic-campaigns for the batch execution model.

## 5. Doctrine mapping moved to attributes

- Column and association mappings moved from static `loadMetadata()` to `#[ORM\*]` attributes; at this snapshot no core entity declares `loadMetadata()` any more [PR #17532] [PR #18054] [PR #18055] [PR #18056] [PR #18146] [PR #18179] [code: grep "function loadMetadata" app/bundles plugins @8.x].
- Core swaps Doctrine's static-PHP driver for `AttributeAndStaticPhpDriver`, which reads attributes first and then calls `loadMetadata()` if the class still has one. A plugin entity mapped entirely in `loadMetadata()` keeps working [code: app/bundles/CoreBundle/Doctrine/Mapping/AttributeAndStaticPhpDriver.php:29-39 @8.x] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/DoctrineMappingDriverPass.php:25-34 @8.x].
- What breaks: trait and builder helpers a plugin called from its own `loadMetadata()` are removed, because the traits now carry attributes: `DateAddedTrait::addDateAddedField()`, `VariantEntityTrait` `addVariantMetadata()` (for `#[ORM\Entity]` entities), `FiltersEntityTrait::addFiltersMetadata()`, `TranslationEntityTrait::addTranslationMetadata()`, `ProjectTrait::addProjectsField()`, `CustomFieldEntityTrait::loadFixedFieldMetadata()`, `ClassMetadataBuilder::addLead()` / `addContact()` [code: UPGRADE-8.0.md "Other removed code" @8.x] [PR #17460].
- Trait attributes are only read for an entity with a class-level `#[ORM\Entity]`. A plugin entity that uses one of these traits must declare `#[ORM\Entity]` (and `#[ORM\Table]`), drop the helper call, and, for a non-default column name, use `#[ORM\AttributeOverrides]` [code: UPGRADE-8.0.md "Other removed code" @8.x].
- Code that called `Lead::loadMetadata()`, `Company::loadMetadata()` or `FormEntity::loadMetadata()` to read mappings throws `Error` or sees only part of the mapping. Read mappings with `EntityManagerInterface::getClassMetadata()` [code: UPGRADE-8.0.md "Other removed code" @8.x].
- A new PHPStan rule forbids static `loadMetadata()` in core [PR #18142] [code: phpstan.neon:386 @8.x].
- Before upgrading a plugin: grep the plugin for `loadMetadata`, `addDateAddedField`, `addVariantMetadata`, `addFiltersMetadata`, `addTranslationMetadata`, `addProjectsField`, `loadFixedFieldMetadata`, `addLead(` and `addContact(`; move those mappings to attributes; then run `bin/console doctrine:schema:update --dump-sql` and `doctrine:schema:validate` on 8.x and confirm no column of the plugin's tables changes (for example `date_added` stays mapped) [code: UPGRADE-8.0.md "Other removed code" @8.x].

## 6. Native parameter and return types for plugin extension points

- 8.x promotes documented types to native types across entities, models, controllers, events, helpers and integrations, and keeps adding them per PR [code: UPGRADE-8.0.md "Native parameter and return types for plugin extension points" @8.x] [PR #18230] [PR #17877].
- Callers: an `array` parameter rejects `null`, scalars and collections with a `TypeError`; pass `[]` for empty. Typical cases: entity setters for JSON columns (`setProperties()`, `setFilters()`, `setUtmTags()`, …), `setPublishUp()`/`setDateAdded()` (now `?\DateTimeInterface`, no date strings), `setCategory()` (a `Category` entity or `null`, not an id), association setters (entity objects, not ids), Collection setters (`new ArrayCollection($items)`), `MailHelper::setLead()` (field array, not a `Lead`) [code: UPGRADE-8.0.md "Native parameter and return types for plugin extension points" @8.x] [code: UPGRADE-8.0.md "Changed code" @8.x].
- Overrides: keep parameter types compatible with the parent (untyped stays valid; narrowing `iterable` to `array` does not); declare every new return type; redeclared properties must keep the parent's native type (`protected array $routeParams = [];`, `protected iterable $leadFields = [];`) [code: UPGRADE-8.0.md "Native parameter and return types for plugin extension points" @8.x] [PR #18087].
- Model and API hooks: `dispatchEvent(string $action, object &$entity, …)`, `createForm(object|array $entity, $action = null, array $options = [])`, `saveEntities(iterable $entities)`; `CommonApiController::preSaveEntity(object &$entity, FormInterface $form, array $parameters, string $action = 'edit')` [PR #17841] [PR #18128] [code: UPGRADE-8.0.md "Changed code" @8.x].
- References: several overridable methods no longer take parameters by reference; remove `&` in overrides [PR #17877] [code: UPGRADE-8.0.md "Changed code" @8.x].
- In files with `declare(strict_types=1)`, scalars are no longer coerced, so an `int` passed to a `string` id or setter now throws [code: UPGRADE-8.0.md "Changed code" @8.x].
- Before upgrading a plugin: run PHPStan (level 6 or higher) against an 8.x checkout; it reports incompatible override signatures, missing return types and wrong argument types before runtime. Then run the plugin's functional tests on 8.x, since a coerced scalar or a `null` argument only fails when that path executes. [code: phpstan.neon:7 @8.x] [code: UPGRADE-8.0.md "Native parameter and return types for plugin extension points" @8.x]

## 7. Per-bundle BC breaks

### Core / cross-cutting
- `Controller\FormController` removed; extend `AbstractFormController` or `AbstractStandardFormController` and override `getModelName()` (required), `getPermissionBase()`, `getRouteBase()`, `getSessionBase()` (include the `mautic.` prefix to keep session keys), `getTranslationBase()`, `getTemplateBase()`, `getJsLoadMethodPrefix()`. Unlock route `mautic_core_form_action` moves unchanged to `LockController` [PR #17481] [code: UPGRADE-8.0.md "Other removed code" @8.x].
- `CommonController` helpers are now `protected` (`addFlashMessage`, `delegateRedirect`, `delegateView`, `postActionRedirect`, `forwardWithPost`, `notFound`, `throwAccessDenied`, `renderException`, …); `accessDenied()` removed (use `throwAccessDenied()` / `getAccessDeniedFlash()`). Only route actions may be public [PR #17535].
- `AssociationBuilder::isOwnershipParent()` → `#[Mautic\CoreBundle\Entity\Attribute\OwnershipParent('form')]`; Mautic's `ManyToManyAssociationBuilder` / `OneToManyAssociationBuilder` removed (Doctrine builders returned); mapping helpers in §5 [PR #17456] [PR #17361].
- `CommonRepository` is `abstract`; query-builder/filter params are natively typed; overrides of `addCatchAllWhereClause()` / `addSearchCommandWhereClause()` must match; public repository methods need return types [PR #17131] [PR #17524] [PR #17399]. `getPublishedByDateExpression()` removed: use `getPublishedByDateOrmExpression()` or `getPublishedByDateDbalExpression()` [PR #18157].
- `CommonEntity` abstract; `$changes` is `array`; `FormEntity::$new` is `bool` [PR #17808] [PR #17170].
- `Model\FormModel`: methods typed (`saveEntity(object $entity, …)`, `deleteEntity(object)`, `deleteEntities(array)`, `lockEntity(object)`, `isNewEntity(object)`, `togglePublishStatus(object)`) [PR #17365] [PR #17523]; `dispatchEventFromBatch()` removed from `FormModel` and `LeadModel`, `dispatchEvent()` handles single and batch saves [PR #18125]; `togglePublishStatus()` dispatches `EntityTogglePublishEvent` instead of `dispatchEvent('on_toggle_publish', …)` [PR #18137].
- `VariantModelTrait::resetVariants()` runs only when the repository implements `ResettableVariantsInterface` (it used `method_exists()`) [PR #18103]; `VariantModelTrait::$inConversion` is `bool` [PR #18170].
- `ModelFactory::getModel()` resolves only via the model's static `getName()` (no FQCN, no `mautic.<bundle>.model.<name>` aliases); `ModelPass` removed [PR #17133].
- `AbstractPermissions::definePermissions()` removed: define permissions in the constructor; `array $params` constructor arg deprecated (params come via autowired `setCoreParametersHelper()`, unavailable in the constructor); permission classes are services tagged `mautic.permissions` [PR #17079] [PR #17121].
- The `services` group in `Config/config.php` (including `models`, `menus`) is no longer read; `ServicePass`, `TwigPass` removed. Declare menus (`knp_menu.menu` + `knp_menu.renderer`) and services in `Config/services.php` [PR #17470] [PR #17116] [PR #17117].
- String service ids removed (use FQCN): `mautic.security`, `symfony.filesystem`, `mautic.config.model.sysinfo`, `mautic.helper.cache_storage`, `mautic.user.provider`, `mautic.helper.paths`, `mautic.helper.token_builder`, `mautic.cache.adapter.*`, `mautic.integrations.helper*`, `mautic.sms.callback_handler_container`, model aliases, and the `mautic.integration.gmail.config` / `mautic.integration.tagmanager.config` aliases [PR #16875] [PR #17124] [PR #17134] [code: UPGRADE-8.0.md "Other removed code" @8.x].
- Every class/interface constant is typed (`public const string X`); overriding constants must be typed (`AbstractMauticMigration::TABLE_NAME` is `?string`) [PR #16996] [PR #17543].
- Removed: `CacheStorageHelper`, `EmojiHelper` + maps, `Entity\Cache`, `PublishStatusIconAttributesInterface`, `UuidTrait::isValidUuid()` (use `UuidHelper`), `VariantModelTrait::convertVariant()` (use `VariantConverterService`), `GeneratedColumns::getForOriginalDateColumnAndUnit()`, `AbstractFormFieldHelper::setTranslator()`, `RedisSentinelSessionHandler`, `ModeratedCommand::MODE_LOCK`, `Translation\TranslatorLoader` [PR #17033] [PR #17026] [PR #17050] [PR #17393].
- DBAL `createQueryBuilder()` returns `Mautic\CoreBundle\Doctrine\Query\QueryBuilder` (keeps `getQueryPart(s)`, `resetQueryPart`); `new QueryBuilder($conn)` loses them; `Doctrine\ReservedWords` replaces the platform keyword list [PR #17361].
- Core routes moved from `Config/config.php` `routes` to `#[Route]` attributes; `RouteLoader` scans `app/bundles/*/Controller` only. **Plugins keep using `config.php` `routes`** [PR #17169] [PR #17222] [PR #17231].
- CSS: custom utility classes (`.pull-*-xs`, `.bdr-*`, `.fs-1` as flex-shrink, …), custom `.bg-*` colours, Glyphicons and unused Bootstrap 3 compatibility styles and mixins are removed; themes and plugin templates must use Bootstrap 5 utilities [PR #17873] [PR #18254] [PR #18266] [code: UPGRADE-8.0.md "Other removed code" @8.x].
- Deleted without an `UPGRADE-8.0.md` entry: `CoreBundle\Entity\UpsertTrait`, `CoreBundle\Event\UpgradeEvent`, `HashHelper(+Interface)`, `Test\DoctrineExtensions\TablePrefix`, Bounce `Definition\Rule`, IntegrationsBundle OAuth credential interfaces and `IntegrationMappingException` / `InvalidProviderException`, `LeadBundle\Helper\CampaignEventHelper`, `Segment\Exception\InvalidUseException`, `StageBundle\Helper\EventHelper`, `MauticFullContactBundle\Exception\ApiException`, Codeception functional suite [PR #17182] [PR #17183] [PR #17184] [PR #17185] [PR #17241].

### ApiBundle
- `ApiEvents` removed; `Client/ApiEntity/ApiSerializationContext` events are abstract with concrete subclasses [PR #17217].
- `CommonApiController` form hooks: `prePopulateForm()` and `preSaveEntity()` take `array $parameters`, `FormInterface $form` and `string $action`; `processBatchForm()` types `$method` as `string`; `prepareEntitiesForView()` / `prepareEntityResultsToArray()` take `iterable` and return `array` [code: UPGRADE-8.0.md "Changed code" @8.x] [code: UPGRADE-8.0.md "Native parameter and return types for plugin extension points" @8.x].

### AssetBundle
- CRUD events by class (`AssetPreSaveEvent`, `AssetPostSaveEvent`, `AssetPreDeleteEvent`, `AssetPostDeleteEvent`, `AssetLoadEvent`, `RemoteAssetBrowseEvent`); `ASSET_ON_UPLOAD` dropped; service `mautic.asset.upload.error.handler` removed [PR #17196] [PR #17215].

### CampaignBundle
- 21 constants removed (see event map); legacy action path, `CampaignExecutionEvent` and `AbstractEventAccessor::getConfig()` removed (§4) [PR #17097] [PR #18159].
- Removed: `CampaignRepository::fetchEmailIdsById()`, `getCampaignLeadCount()`, `getCampaignLeads()`, `Campaign::getOnclickMethod()` / `getDataAttributes()` / `getTranslationKeysDataAttributes()` [code: UPGRADE-8.0.md "Other removed code" @8.x].
- `CampaignModel::getLeadSources(Campaign|int|string)` [code: UPGRADE-8.0.md "Changed code" @8.x].

### ChannelBundle / CategoryBundle / ConfigBundle / DashboardBundle / DynamicContentBundle
- Channel: five events dispatched by class while their constants are kept (trap); `MessageModel::getMarketingMessagesEventLogs()` removed (use `getLeadStatsPost()`) [code: UPGRADE-8.0.md "Changed code" @8.x] [PR #18171].
- Category: `CATEGORY_ON_BUNDLE_LIST_BUILD` → `CategoryTypesEvent` (constant kept, trap); duplicate `CATEGORY_*` constants removed from `DynamicContentEvents` [code: UPGRADE-8.0.md "Changed code" @8.x].
- Config: `ConfigEvents` removed → `ConfigBuilderEvent` (final), `ConfigPreSaveEvent`, `ConfigPostSaveEvent` [PR #17625].
- Dashboard: `DashboardEvents` removed → `WidgetTypeListEvent`, `WidgetFormEvent`, `GenerateWidgetDetailEvent`, `PreLoadWidgetDetailEvent`; `WidgetDetailEventFactory` lost three args [PR #17216] [PR #17034].
- DynamicContent: `ON_CONTACTS_FILTER_EVALUATE` → `ContactFiltersEvaluateEvent`; `TOKEN_REPLACEMENT` → `Mautic\CoreBundle\Event\TokenReplacementEvent` [PR #17691].

### EmailBundle
- 20 constants removed; kept: `EMAIL_ON_SEND` and `EMAIL_ON_OPEN` (webhook type ids, trap), `EMAIL_FAILED`, `EMAIL_RESEND`, campaign constants, `ON_SENT_EMAIL_TO_USER`, `ON_DETERMINE_*` [code: app/bundles/EmailBundle/EmailEvents.php @8.x].
- `EmailOnTogglePublishEvent` removed (§3.5) [PR #18137].
- `MailHelper::validateEmail()` removed (use `EmailValidator`) [code: UPGRADE-8.0.md "Other removed code" @8.x]; `MailHelper` is `final` [code: app/bundles/EmailBundle/Helper/MailHelper.php:48 @8.x]; `setLead()` takes the contact field array [code: UPGRADE-8.0.md "Changed code" @8.x].
- Return types: `Email::getContent(): array|string`, `getUtmTags()`, `getHeaders()`, `Stat::getOpenDetails()` → `array`; `Stat::getTokens(): ?array` [code: UPGRADE-8.0.md "Changed code" @8.x].

### FormBundle
- Form "type" (`standalone`/`campaign`) removed: `Form::$formType`, `getFormType()`, `setFormType()`, `isStandalone()`, API field `formType`, `FormRepository::getFormList($formType)`; migration `Version20260814141635` drops `forms.form_type` [PR #17082] [PR #17059].
- `Field::$leadField`, `getLeadField()` and `setLeadField()` removed (use `mappedObject` / `mappedField`); migration `Version20261111164904` copies unmapped values into `mapped_field` and drops `form_fields.lead_field`; `/api/forms` responses no longer include `leadField` [PR #18158] [code: app/migrations/Version20261111164904.php:27-37 @8.x].
- `SubmissionEvent` is `final`; `setPostSubmitCallbackResponse(string $key, RedirectResponse $callbackResponse)`; `getPostSubmitPayload(): ?array` [code: app/bundles/FormBundle/Event/SubmissionEvent.php:14,238,263 @8.x].
- The social bundle's `plugin.loginSocial` field no longer exists (§9) [PR #17473].

### IntegrationsBundle
- `IntegrationEvents` removed (23 constants); new concrete events such as `InternalContactFieldChangesEvent`, `ConfigBeforeSaveEvent`, `ConfigAfterSaveEvent` [PR #17160].
- `DefaultConfigFormTrait` removed: implement `getConfigFormName()` / `getConfigFormContentTemplate()` [code: UPGRADE-8.0.md "Other removed code" @8.x].
- New `Integration\Interfaces\PushContactInterface` (`getPushContactConfigFormName()`, `pushContact()`) and `PushContactException`: an integration that offers `ConfigFormFeaturesInterface::FEATURE_PUSH_LEAD` appears in the "Push contact to integration" Form, Campaign and Point actions [PR #18139] [code: UPGRADE-8.0.md "Changed code" @8.x].
- `MappingManualDAO`: object mappings go to the constructor; `addObjectMapping()` is `private` [code: app/bundles/IntegrationsBundle/Sync/DAO/Mapping/MappingManualDAO.php:18,32 @8.x].
- `getIntegrationConfiguration()` throws `\LogicException` when unset; check `hasIntegrationConfiguration()` first [code: app/bundles/IntegrationsBundle/Integration/ConfigurationTrait.php:16 @8.x].

### LeadBundle
- 56 constants removed; many kept-but-class-dispatched (trap) [code: app/bundles/*/*Events.php @7.x vs @8.x].
- Removed: `LeadModel::isContactable()` (use `DoNotContact::isContactable()`), `FieldModel::getFieldList()` (use `Field\FieldList`), `OperatorOptions::IN` / `NOT_IN` (use `INCLUDING_ANY` / `EXCLUDING_ANY`), `LeadModel::getTagRepository()`, `CompanyModel::getCompanyLeadRepository()`, `AjaxController::addLeadUtmTagsAction()` [code: UPGRADE-8.0.md "Other removed code" @8.x] [PR #17247] [PR #17248].
- The contact companies modal is removed: `LeadController::companyAction()` (`/s/contacts/company/{objectId}`), its template, `Mautic.toggleCompanyLead` and the `lead:toggleCompanyLead` AJAX action. Use the contact edit form or `/api/companies/{companyId}/contact/{contactId}/add|remove` [PR #18091].
- `Lead::setCompany()` takes the company name string; `Lead::setUtmTags()` takes a `UtmTag` [code: UPGRADE-8.0.md "Changed code" @8.x].
- `IdentifyCompanyHelper` is an autowired service with instance methods [PR #17260].
- `Segment\Query\QueryBuilder::setParameter()` rejects `:`-prefixed keys [code: UPGRADE-8.0.md "Changed code" @8.x].
- `FieldDeleteDispatcher::dispatchPreDeleteEvent()` removed and `dispatchEvent()` is private and takes a `LeadFieldEvent`; the `UPGRADE-8.0.md` advice to call `dispatchEvent(LeadEvents::FIELD_PRE_DELETE, $entity)` cannot work (§16) [code: app/bundles/LeadBundle/Field/Dispatcher/FieldDeleteDispatcher.php:23-31 @8.x].
- `ContactTracker::setUseSystemContact(bool)` is non-nullable; `editAction(int $objectId)` on Company/Field/Lead controllers [code: UPGRADE-8.0.md "Changed code" @8.x].

### NotificationBundle / PageBundle / PluginBundle
- Notification: `NotificationHelper::unsubscribe()` removed; dead route `mautic_receive_notification` removed [code: UPGRADE-8.0.md "Other removed code" @8.x]. `OneSignalIntegration` extends `BasicIntegration` instead of `AbstractIntegration`; its config form is `NotificationBundle\Integration\Support\ConfigSupport`; saved `subdomain_name` and `platforms` move under `featureSettings['integration']` (migration `Version20261109120000`); several subscribers take `OneSignalIntegrationHelper` [PR #18113] [code: UPGRADE-8.0.md "Changed code" @8.x].
- Page: `PublicController::indexAction()` lost the v1 theme path; `RedirectModel::generateRedirectUrl($redirect, $clickthrough)`; `HitRepository::getHitCountForSource()` removed; `PAGE_ON_TOGGLE_PUBLISH` removed (§3.5) [PR #17078] [PR #18137].
- Plugin: `AbstractIntegration` 2nd constructor arg is `CacheProviderInterface`; `getCache(): Psr\SimpleCache\CacheInterface`; documented `@return array` methods declare `array`; `mergeApiKeys(): ?array`; `AbstractSsoFormIntegration` **and** `AbstractSsoServiceIntegration` are removed (a third-party SSO plugin still on `AbstractIntegration` must reproduce their overrides); `IntegrationEntityModel::logDataSync()` and `getRecordList()` removed; `oAuthHelper` requires an `AbstractIntegration` [PR #18118] [PR #18066] [code: UPGRADE-8.0.md "Other removed code" @8.x] [code: UPGRADE-8.0.md "Changed code" @8.x]. Integrations built on `BasicIntegration` are unaffected by the `AbstractIntegration` type changes [code: app/bundles/IntegrationsBundle/Integration/BasicIntegration.php @8.x].

### Point / Stage / Report / Sms / User / Webhook / Stats
- Point: `POINT_ON_ACTION` → `PointActionEvent`; `SCORE_CHANGE` → `GroupScoreChangeEvent` (constants kept, trap) [code: UPGRADE-8.0.md "Changed code" @8.x].
- Stage: `STAGE_ON_BUILD` → `StageBuilderEvent`; `Helper\EventHelper` deleted [code: UPGRADE-8.0.md "Changed code" @8.x].
- Report: 8 events by class, constants kept (trap) [code: UPGRADE-8.0.md "Changed code" @8.x].
- Sms: 10 constants removed; `SmsEvent` abstract; route `mautic_receive_sms` removed (use `/sms/twilio/callback`) [PR #17622]; `Sms` no longer implements `VariantEntityInterface`, and its 20 variant methods are gone [PR #18146].
- User: `UserEvents` removed → `LoginEvent`, `LogoutEvent`, `PreAuthenticationEvent`, `FormAuthenticationEvent`, `AuthenticationContentEvent`, `PasswordStrengthValidateEvent`, `Pre/PostSave/DeleteUserEvent`, `Pre/PostSave/DeleteRoleEvent`; `AuthenticationEvent` types integrations as `UnifiedIntegrationInterface` [PR #17510] [PR #17623] [PR #18118].
- Webhook: `ON_CAMPAIGN_TRIGGER_ACTION` → `ON_CAMPAIGN_BATCH_ACTION`; CRUD and `WEBHOOK_KILL` constants removed (class-dispatched); `WEBHOOK_ON_BUILD` etc. kept (trap) [PR #17085] [PR #17202].
- Stats: `StatEvents` removed → `AggregateStatRequestEvent` [PR #17654].

### Shipped plugins
- MauticSocialBundle: removed entirely (§9) [PR #17473].
- MauticEmailMarketingBundle (Mailchimp, Constant Contact, iContact): moved to `BasicIntegration`; `EmailAbstractIntegration`, `Api\*Api` classes and the form theme removed, replaced by `Client\{Mailchimp,ConstantContact,Icontact}Client`; each push action has its own list and field mapping; integrations are no longer `final` [PR #18139] [code: UPGRADE-8.0.md "Other removed code" @8.x].
- MauticOutlookBundle: `OutlookIntegration` extends `BasicIntegration` with `Integration\Support\ConfigSupport` and `OutlookKeysType`; `getAuthenticationType()`, `getRequiredKeyFields()`, `getFormNotes()` and other `AbstractIntegration` methods are gone [PR #18135].
- MauticCrmBundle: `ConnectwiseIntegration`, `HubspotIntegration`, `SalesforceIntegration`, `VtigerIntegration` are `final`; dead route `mautic_integration_companies` removed [code: UPGRADE-8.0.md "Changed code" @8.x].
- MauticFocusBundle: methods declare native parameter types; `FocusRepository::getFocusList()` lost `$currentId` [PR #18143] [code: UPGRADE-8.0.md "Changed code" @8.x].
- MauticTagManagerBundle: `Entity\Tag` removed (ORM 3 rejects an unmapped-inheritance subclass) [PR #17361].
- GrapesJsBuilderBundle: legacy `/grapesjsbuilder/assets` endpoint removed; `FileManager::getFullUrl(string $fileName, string $separator)` [PR #17070] [PR #18192].
- MauticClearbitBundle: removed [PR #17785].

## 8. Behaviour changes users and integrators will see

| Change | Effect | Source |
|---|---|---|
| Listeners keyed on removed / kept-but-unused names | Fatal "undefined constant" / silently never runs | §3 |
| Subclass of a core subscriber without autoconfigure, or overriding a listener method | Its events stop arriving | [PR #17988] |
| Legacy campaign actions | Not executed; only `batchEventName` actions run | [PR #17097] |
| Retained `twitter.tweet` campaign action | No longer registered; can interrupt the rest of that campaign | [code: UPGRADE-8.0.md "Social media integrations" @8.x] |
| Retained Social Login (`plugin.loginSocial`) Form field | Cannot be rendered | [code: UPGRADE-8.0.md "Social media integrations" @8.x] |
| `associatedActions` / `associatedDecisions` / `anchorRestrictions` | Ignored | [PR #17032] |
| Publish toggle | One `EntityTogglePublishEvent` for every entity type; plugin model logic for `on_toggle_publish` stops running | [PR #18137] |
| Cache via CacheBundle | A miss returns `null`, not `false`; integration/widget cache lives in `cache_adapter` and is dropped by cache clear; `cache_items` no longer written | [PR #17033] [PR #17155] |
| Emoji | No shortcode/entity conversion; stored as UTF-8 (`utf8mb4`) | [PR #17026] |
| `mautic:disable-tracking` link attribute | No longer honoured: links are tracked; use `data-mautic-disable-tracking="true"` | [docs: https://docs.mautic.org/en/8.0/channels/emails.html] |
| Landing Pages with empty custom HTML | No v1 theme fallback | [PR #17078] |
| Forms API / export | `formType` and `leadField` dropped from responses; `formType` ignored on input | [PR #17082] [PR #18158] [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/forms.html] |
| `POST /api/contacts/{id}/points/{operator}/{delta}` | A non-numeric `{delta}` returns 404 (it used to be treated as 0) | [code: UPGRADE-8.0.md "Changed code" @8.x] |
| Mailchimp, Constant Contact, iContact | New connections: Mailchimp by API key (no OAuth2), Constant Contact by V2 API key + token; saved tokens and push actions keep working; HTTP errors now fail the push | [PR #18139] |
| `--lock_mode=file_lock` | Fails `Unknown locking method specified.` (use `flock`) | [code: UPGRADE-8.0.md "Other removed code" @8.x] |
| `/sms/receive` | 404; Twilio callback must be `/sms/twilio/callback` | [code: UPGRADE-8.0.md "Other removed code" @8.x] |
| `mautic:social:monitoring`, `social:monitor:twitter:hashtags`, `social:monitor:twitter:mentions` | Commands gone; remove them from cron | [code: UPGRADE-8.0.md "Social media integrations" @8.x] |
| Generated SQL aliases | Checked against `ReservedWords`; a few aliases now get prefixed | [PR #17361] |
| Asset upload size validation | Fixed an off-by-1000 error | [PR #17080] |
| Route matching | Attribute routes sorted by specificity; same paths, different order | [PR #17169] |
| SAML | Bundle swapped to lightsaml2; behaviour intended unchanged; test IdP login | [PR #17370] |
| Redis Sentinel session handler | Gone; configs referencing it break | [PR #17050] |
| Webhook `company_soft_delete` | Event name is `Mautic\LeadBundle\Event\CompanySoftDeleteEvent` | [devdocs: https://devdocs.mautic.org/en/8.0/webhooks/events/company_soft_delete.html] |
| DB schema | Three 8.x-only migrations: `Version20260814141635` (drop `forms.form_type`), `Version20261109120000` (OneSignal settings), `Version20261111164904` (drop `form_fields.lead_field`). Social tables are kept. CI fails if an existing table changes shape and runs `doctrine:schema:validate` | [code: app/migrations/ @7.x vs @8.x] [PR #17082] [PR #18113] [PR #18158] [PR #17407] [PR #17346] |

## 9. Removed features

| Removed | Why / replacement | Source |
|---|---|---|
| `MauticSocialBundle` and `mautic/plugin-social`: Facebook, Twitter/X, Instagram, Foursquare integrations, Social Monitoring, tweets, the `twitter.tweet` campaign action, the `plugin.loginSocial` Form field, three `social:*` commands, `SocialEvents` | Removed; CRM integrations, contact social-profile fields and social links in emails are unaffected; integration settings and social tables are retained, not deleted | [PR #17473] [code: UPGRADE-8.0.md "Social media integrations" @8.x] |
| Clearbit plugin (`plugins/MauticClearbitBundle`, translations `mautic.plugin.clearbit.*`, `mautic.integration.clearbit.apikey`, 4 Twig templates) | Service sunset after the HubSpot acquisition | [PR #17785] |
| Form type standalone/campaign | Unused since 7.1; every Form is usable in Campaigns | [PR #17082] |
| Form field `leadField` | Use `mappedObject` / `mappedField` | [PR #18158] |
| Mautic v1 theme fallback for Landing Pages, `{{ public }}` template param | Deprecated | [PR #17078] |
| Legacy campaign action path, `CampaignExecutionEvent` | Batch only | [PR #17097] [PR #18159] |
| Emoji conversion | UTF-8 directly | [PR #17026] |
| `CacheStorageHelper`, `Entity\Cache`, filesystem widget cache | CacheBundle only | [PR #17033] [PR #17155] |
| `RedisSentinelSessionHandler` | Deprecated since 5.0 | [PR #17050] |
| `mautic:disable-tracking` attribute | Use `data-mautic-disable-tracking` | [code: UPGRADE-8.0.md "Other removed code" @8.x] |
| GrapesJS legacy asset endpoint | Media endpoint since 5.2 | [PR #17070] |
| Routes `mautic_receive_sms`, `mautic_receive_notification`, `mautic_campaign_import_index`, `mautic_integration_companies`, `/s/contacts/company/{objectId}` | Dead/alias | [PR #17231] [PR #18091] |
| `ModeratedCommand::MODE_LOCK` (`file_lock`) | Use `flock` | [code: UPGRADE-8.0.md "Other removed code" @8.x] |
| AJAX `lead:addLeadUtmTags`, `lead:toggleCompanyLead`; JS `Mautic.createLeadUtmTag()`, `Mautic.toggleCompanyLead` | Unused | [code: UPGRADE-8.0.md "Other removed code" @8.x] [PR #18091] |
| `AbstractSsoFormIntegration`, `AbstractSsoServiceIntegration`, TagManager `Entity\Tag`, EmailMarketing `EmailAbstractIntegration` and `Api\*Api` | Use `BasicIntegration` | [PR #18118] [PR #18139] [PR #17361] |
| SMS variants (`Sms` variant methods) | Never stored | [PR #18146] |
| Compiler passes `ModelPass`, `ServicePass`, `PermissionsPass`, `TwigPass`; `config.php` `services` group | Symfony DI/autoconfigure | [PR #17133] [PR #17116] [PR #17121] [PR #17117] [PR #17470] |

The 8.0 user docs still describe Social Monitoring, the Twitter plugin and the `mautic:social:monitoring` cron job, which 8.x
code removed; the 8.0 developer docs dropped `rest_api/tweets` [docs: https://docs.mautic.org/en/8.0/channels/social_monitoring.html]
[docs: https://docs.mautic.org/en/8.0/configuration/cron_jobs.html] [PR #17473]. Otherwise the 8.0 user docs mostly describe
7.x features; the 8-specific user-facing change they carry is the `mautic:disable-tracking` removal
[docs: https://docs.mautic.org/en/8.0/channels/emails.html].

## 10. Before you upgrade an install or a plugin: checklist

For an install (from `UPGRADE-8.0.md` and the removals above):

1. PHP 8.4 or 8.5, MySQL ≥ 8.4.0 or MariaDB ≥ 10.11.0 [code: app/release_metadata.json @8.x].
2. Social bundle: remove Twitter actions from Campaigns and reconnect the following steps; remove Social Login fields from Forms, save the Forms to regenerate their HTML and update any externally embedded static Form HTML; remove the `mautic:social:monitoring`, `social:monitor:twitter:hashtags` and `social:monitor:twitter:mentions` cron entries; for Composer installs remove an explicit `mautic/plugin-social` requirement. After upgrading, clear the cache and run `bin/console mautic:plugins:reload` so the plugin shows as missing [code: UPGRADE-8.0.md "Social media integrations" @8.x].
3. Cron: replace `--lock_mode=file_lock` with `flock`; repoint Twilio callbacks from `/sms/receive` to `/sms/twilio/callback` [code: UPGRADE-8.0.md "Other removed code" @8.x].
4. Email HTML: replace `mautic:disable-tracking` with `data-mautic-disable-tracking="true"` [code: UPGRADE-8.0.md "Other removed code" @8.x].
5. Integrations: Mailchimp OAuth2 and Constant Contact OAuth2 connections keep their saved tokens but cannot be re-made; have API keys ready [PR #18139].
6. Check every installed third-party plugin against the plugin checklist below; an incompatible plugin fails the container compile for the whole install. [code: UPGRADE-8.0.md @8.x]

For a plugin:

1. Events: replace every string key and two-argument `dispatch()` (§3.1, event map); move to `#[AsEventListener]` or keep `getSubscribedEvents()` with class keys; check autoconfiguration, overridden listener methods and priorities (§3.2). [PR #17988] [code: UPGRADE-8.0.md "Changed code" @8.x]
2. Campaign actions: `batchEventName` + `PendingEvent`; decisions and conditions on `DecisionEvent` / `ConditionEvent` (§4). [PR #17097] [PR #18159]
3. Doctrine: remove the removed trait helpers, add `#[ORM\Entity]`, verify the schema diff is empty (§5). [PR #17532] [code: UPGRADE-8.0.md "Other removed code" @8.x]
4. Types: run PHPStan against 8.x and fix override signatures, return types, redeclared property types and argument types (§6). [PR #18230]
5. Removed classes: social bundle classes, `AbstractSso*Integration`, `EmailAbstractIntegration`, `FormController`, `CacheStorageHelper`, `DefaultConfigFormTrait`, string service ids (§7, §9). [PR #17473] [PR #18118] [PR #18139] [PR #17481] [PR #17033]

## 11. Symfony 8 and Doctrine 3/4 fallout for plugin code

- `Request::get()` is removed. Use `$request->attributes->get()`, `->query->get()`, `->request->get()` (core rewrote 94 files) [PR #17309] [PR #17347].
- Constraint constructors no longer accept an options array; pass named arguments (`new Length(max: 255)`). A positional array silently does nothing on custom constraints [PR #17392].
- `Url::$requireTld` defaults to `true` (core passes `requireTld: false`); `UrlType` `default_protocol` defaults to `null` (core sets `'http'`) [PR #17392] [PR #17349].
- `UserInterface::eraseCredentials()` gone; `FrameworkBundle\Translation\Translator`, `InputBag` and `Router` are `final` (tests must not mock them); `ConstraintValidator::initialize()+validate()` deprecated for `validateInContext()` [PR #17392] [PR #17393].
- Doctrine: use `getEntityManager()` not `$this->_em`; `ClassMetadata` not `ClassMetadataInfo`; `ArrayParameterType` not `Connection::PARAM_*_ARRAY`; build composite expressions from a finished list (`CompositeExpression::and(...$parts)`), never `->add()`; take query builders from the connection; map the `lead` relation with attributes [code: UPGRADE-8.0.md "Changed code" @8.x].

## 12. Writing code that works on both 7.x and 8.x

1. **Subscribe by event class wherever the class exists on 7.x** (most do: `CampaignBuilderEvent`, `MenuEvent`, `SubmissionEvent`, `ReportBuilderEvent`, `LeadListFilteringEvent`, …). On 7.x the dispatcher still uses the string name, so register **both keys**, guarded [code: UPGRADE-8.0.md "Changed code" @8.x]:
   ```php
   public static function getSubscribedEvents(): array
   {
       $events = [CampaignBuilderEvent::class => ['onBuild', 0]];          // 8.x
       if (defined(CampaignEvents::class.'::CAMPAIGN_ON_BUILD')) {         // 7.x
           $events[CampaignEvents::CAMPAIGN_ON_BUILD] = ['onBuild', 0];
       }
       return $events;
   }
   ```
   Each version dispatches the event under one name only (string on 7.x, class on 8.x), so the handler runs once per dispatch [code: app/bundles/*/*Events.php @7.x vs @8.x]. `getSubscribedEvents()` still works on 8.x; it is the simplest form for dual-version code, because `#[AsEventListener]` takes a fixed event name and cannot be guarded [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].
2. **Events whose concrete class exists only on 8.x** (`LeadPostSaveEvent`, `PostSaveUserEvent`, `CampaignPostSaveEvent`, …): guard with `class_exists()` and type-hint the shared parent (`LeadEvent`, `UserEvent`, `CampaignEvent`) in the handler [code: UPGRADE-8.0.md "Changed code" @8.x].
3. **Classes that disappear** (`CoreEvents`, `UserEvents`, `IntegrationEvents`, `ApiEvents`, `ConfigEvents`, `DashboardEvents`, `StatEvents`, `SocialEvents`): never reference their constants unguarded; `defined('Mautic\CoreBundle\CoreEvents::BUILD_MENU')` is safe [code: app/bundles/*/*Events.php @7.x vs @8.x].
4. **Kept-but-unused constants** (§3.3): also add the class key; the constant key alone only works on 7.x [code: UPGRADE-8.0.md "Changed code" @8.x].
5. **Campaign actions**: register `batchEventName` and handle `PendingEvent`; conditions use `pass()`/`fail()`, decisions `setAsApplicable()`; never type `CampaignExecutionEvent`; use `connectionRestrictions` [PR #17097] [PR #17151] [PR #17032] [PR #18159].
6. **Entities**: plain `loadMetadata()` without the removed trait helpers works on both, because 8.x still reads it (§5). Attribute mapping also works on 8.x; on 7.x core only reads `loadMetadata()` for its entities, so test an attribute-mapped plugin entity on 7.x before relying on it [code: app/bundles/CoreBundle/Doctrine/Mapping/AttributeAndStaticPhpDriver.php @8.x] [code: app/bundles/CoreBundle/Doctrine/Mapping/ @7.x, no attribute driver].
7. **Add native types to every override now** (params, returns, typed constants, typed redeclared properties). PHP lets a child add a return type its parent lacks, so typed code runs on 7.x and 8.x [code: UPGRADE-8.0.md "Native parameter and return types for plugin extension points" @8.x].
8. **Get services by class name** (`CorePermissions::class`, `Filesystem::class`, `CacheProviderInterface`); get models via `ModelFactory::getModel('bundle.name')` with a static `getName()` on your model, or inject the model [PR #17133].
9. **Cache**: inject `CacheProviderInterface`; treat a miss as `null` (and also `false` if you still support `CacheStorageHelper` on 7.x) [devdocs: https://devdocs.mautic.org/en/8.0/plugins/cache.html#migrating-to-cachebundle-in-mautic-8].
10. Declare menus and services in `Config/services.php` with `autoconfigure()`; keep plugin routes in `Config/config.php` `routes` [PR #17470] [PR #17169] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].
11. Request access via `query`/`request`/`attributes` bags; constraints with named arguments [PR #17392].
12. Do not extend or mock `final` classes; compose and prefer interfaces. Use `data-mautic-disable-tracking="true"` [PR #17536].
13. Declare the supported range in the plugin's `composer.json` (`"mautic/core-lib": "^7.0 || ^8.0"` style constraint) and set `MINIMUM_MAUTIC_VERSION` on the bundle class if you need a floor; the kernel skips loading a plugin bundle when the running version is lower [code: app/AppKernel.php:175-181 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/marketplace/listing.html].

## 13. Porting a plugin from 7.x to 8.x (step by step)

Distilled from `UPGRADE-8.0.md`, which devdocs now name as the checklist [code: UPGRADE-8.0.md @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

1. Require PHP 8.4, Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4 in the plugin's composer constraints (`mautic/core-lib` 8.x).
2. Grep for `Events::` in `getSubscribedEvents()` and `#[AsEventListener]`, and for two-argument `dispatch(` calls. Replace with event classes using [event-map-7-to-8.md](event-map-7-to-8.md). Check every remaining constant key against the kept-constant trap list.
3. Check subclasses of core subscribers for autoconfiguration and re-declare `#[AsEventListener]` on overridden listener methods (§3.2). [PR #17988]
4. Convert campaign actions to `batchEventName` + `PendingEvent`; drop `eventName`/`callback` and `CampaignExecutionEvent`. [PR #17097] [PR #18159]
5. Remove calls to the removed mapping helpers and add `#[ORM\Entity]` where a trait's attributes must load (§5). [PR #17532]
6. Fix fatal signature mismatches: copy parent signatures exactly for overrides of `CommonRepository`, `FormModel`/`AbstractCommonModel`, `AbstractIntegration`/`CrmAbstractIntegration`, `CommonController`/`CommonApiController`/`FetchCommonApiController`, event classes, entities and dashboard `Widget`. Type overriding constants (`public const string`) and redeclared properties. The kinds of break are: new parameter type, new return type (a `null` or missing return now throws `TypeError`), new property type, removed by-reference parameter, removed property (§6).
7. Stop extending classes that are now `final` (models, repositories, `MailHelper`, CRM integrations, many events); compose instead.
8. Replace removed classes and services: `FormController`, `CacheStorageHelper`, `AbstractSsoFormIntegration` / `AbstractSsoServiceIntegration`, `DefaultConfigFormTrait`, social bundle classes, string service ids. Move a legacy `AbstractIntegration` plugin to `BasicIntegration`; `PushContactInterface` covers "Push contact to integration". [PR #18118] [PR #18139] [PR #17473]
9. Move permissions into the constructor and register the class as a service; move menus to `services.php`.
10. Apply the Doctrine 3/4 API changes (§11); move `isOwnershipParent()` to the attribute.
11. Callers of controller helpers from outside the controller break (helpers are `protected`).
12. Tests: PHPUnit 13, `dg/bypass-finals` bootstrap for mocking finals, no doubles of `Request`/`InputBag`/`Router`.
13. Verify with `rm -rf var/cache && bin/console` (container compiles) and `bin/console debug:event-dispatcher` for each event you listen to [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].

## 14. How to test a plugin on both 7.x and 8.x

The goal is to catch the two failure modes that a 7.x-only test run misses: fatal signature errors (loud) and listeners that never fire (silent).

**Environments.**
- Run the plugin inside two Mautic checkouts: the `7.x` branch (or a 7.2.x tag) on PHP 8.2+, and the `8.x` branch on PHP 8.4+. Both need MySQL ≥ 8.4.0 or MariaDB ≥ 10.11.0 [code: app/release_metadata.json @7.x] [code: app/release_metadata.json @8.x]. Core CI itself tests PHP 8.2 × MySQL 8.4 / MariaDB 10.11 and PHP 8.5 × MySQL 9.2 / MariaDB 11.4 on 7.x [code: .github/workflows/tests.yml:25-32 @7.x]. See mautic-dev-environment for DDEV setup.
- 8.x has 7.x up to 2026-11-16; a test that depends on a 7.x PR merged after that (§1) fails on 8.x for that reason, not because of your port [PR #18236].

**Static checks (both versions).**
- Clear the cache and boot the container: `rm -rf var/cache && bin/console`; this catches service wiring and compile errors [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
- `bin/console lint:twig plugins/<YourBundle>` for templates [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
- Run PHPStan against each core version. On 8.x core uses `vendor/bin/phpstan`; on 7.x `bin/phpstan` [PR #17164]. Signature mismatches against 8.x base classes show up here before runtime.
- On 8.x, `bin/console doctrine:schema:update --dump-sql` should print nothing for the plugin's tables after the mapping changes (§5). [code: UPGRADE-8.0.md "Other removed code" @8.x]

**Listener registration (both versions).**
- For each event you handle, run `bin/console debug:event-dispatcher '<event name or FQCN>'` and assert your listener appears under the name that version dispatches: the string constant on 7.x, the class on 8.x [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].
- Write one functional test per listener that performs the real action (save a Contact, submit a Form, run the campaign action) and asserts the listener's side effect. A unit test that calls the handler directly cannot detect the silent-failure trap or a lost `#[AsEventListener]` [code: UPGRADE-8.0.md "Changed code" @8.x].

**PHPUnit across versions.**
- 7.x uses PHPUnit 11.5; 8.x uses PHPUnit 13 [code: composer.json @7.x] [code: composer.json:44 @8.x]. Write tests that run on both: data providers must be `static` (core even patches Twig's `IntegrationTestCase` for this on PHPUnit 11) [code: composer.json:232-236 @7.x].
- On 8.x more classes are `final`; mocking them needs the `DG\BypassFinals` bootstrap, which core enables in `app/tests/bootstrap.php@8.x`. Prefer interfaces or real objects so the same test runs on 7.x [PR #17366].
- Do not create doubles of `Request`, `InputBag` or `Router` (final under Symfony 8) [PR #17392].
- Functional tests build the schema from entity metadata and mark migrations executed; they do not exercise migrations. Test plugin migrations separately (see mautic-plugin-development) [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:159 @7.x].
- See mautic-testing for base classes (`MauticMysqlTestCase`) and fixtures.

**Campaign actions.**
- On 8.x an action without `batchEventName` is silently not executed. Add a functional test that runs `mautic:campaigns:trigger` for a campaign using your action and asserts the outcome, on both versions [PR #17097].

## 15. What to avoid in new 7.x contributions (removed in 8.x)

`*Events::CONST` as subscriber keys or second `dispatch()` argument; `ON_CAMPAIGN_TRIGGER_ACTION` / `eventName`+`callback`
actions; `CampaignExecutionEvent`, `CampaignDecisionEvent`, `ConditionEvent::setResult()`, `AbstractEventAccessor::getConfig()`;
`CacheStorageHelper`; `EmojiHelper`; `Core\Controller\FormController`; `AbstractPermissions::definePermissions()` and the
`array $params` constructor; `services` / `menus` / `models` arrays in `config.php`; string service ids (`mautic.security`,
`mautic.helper.*`, `mautic.<bundle>.model.*`, `symfony.filesystem`); `ClassMetadataBuilder::addLead()/addContact()/isOwnershipParent()`
and the trait mapping helpers (`addDateAddedField()`, `addVariantMetadata()`, …); `Form::getFormType()/isStandalone()`,
`Field::getLeadField()`; `LeadModel::isContactable()`, `FieldModel::getFieldList()`, `MailHelper::validateEmail()`,
`OperatorOptions::IN/NOT_IN`; `getPublishedByDateExpression()`; `dispatchEventFromBatch()`; static `IdentifyCompanyHelper::`
calls; `mautic:disable-tracking`; `--lock_mode=file_lock`; `/sms/receive`; `Request::get()`; `$this->_em` in repositories;
constraint option arrays; `MappingManualDAO::addObjectMapping()`; new code on `AbstractIntegration` or `AbstractSso*Integration`;
social bundle classes; Clearbit [code: UPGRADE-8.0.md @8.x].

## 16. Open questions and known inconsistencies

- `UPGRADE-8.0.md` says these constants are "kept for backwards compatibility"; the 8.x code removed them: all of `CoreEvents` (also still recommended as `CoreEvents::VIEW_INJECT_CUSTOM_TEMPLATE` in two entries), `IntegrationEvents`, `DashboardEvents`; the eight converted `PluginEvents`; `SmsEvents` `DNC_FILTER_CONTACTS_ON_SEND`, `FILTER_CONTACTS_ON_SEND`, `QUEUE_FILTER_CONTACTS_ON_SEND`, `ON_SMS_TOKENS_BUILD`; the "several more bundles" table (`EMAIL_ON_REPLY`, `ON_TRANSPORT_WEBHOOK`, `ON_EMAIL_VALIDATION`, `MONITORED_EMAIL_CONFIG`, `USER_LOGOUT`, `USER_PASSWORD_STRENGTH_VALIDATION`, `API_PLATFORM_PERMISSION_CONTEXT`). It also says the `WebhookEvents` CRUD and `WEBHOOK_KILL` constants and `EmailEvents::EMAIL_PARSE` / `EMAIL_PRE_FETCH` "are unchanged"; all are removed [code: UPGRADE-8.0.md "Changed code" @8.x] [code: app/bundles/*/*Events.php @7.x vs @8.x].
- `UPGRADE-8.0.md` tells callers of the removed `FieldDeleteDispatcher::dispatchPreDeleteEvent()` to call `dispatchEvent(LeadEvents::FIELD_PRE_DELETE, $entity)`; `dispatchEvent()` is private, takes a `LeadFieldEvent`, and `FIELD_PRE_DELETE` is removed [code: UPGRADE-8.0.md "Other removed code" @8.x] [code: app/bundles/LeadBundle/Field/Dispatcher/FieldDeleteDispatcher.php:31 @8.x].
- The `CacheStorageHelper` entry says `Entity\Cache` and `cache_items` are kept; a later entry removes the entity, and the file is absent [code: UPGRADE-8.0.md "Other removed code" @8.x] [PR #17155].
- The `Form::setFormType()` entry says the `form_type` column is unchanged; the form-type entry and migration `Version20260814141635` drop it [code: UPGRADE-8.0.md "Other removed code" @8.x].
- The native property types table lists `CampaignExecutionEvent::$eventArray`, but [PR #18159] removed that class [code: UPGRADE-8.0.md "Native parameter and return types for plugin extension points" @8.x] [code: app/bundles/CampaignBundle/Event/ @8.x].
- `UPGRADE-8.0.md` says column mappings moved for 106 entities and 84 no longer declare `loadMetadata()`; at this snapshot none of the core entities do, after later PRs [code: UPGRADE-8.0.md "Other removed code" @8.x] [PR #18179].
- The 8.0 user docs still document Social Monitoring and its cron job (§9) [docs: https://docs.mautic.org/en/8.0/channels/social_monitoring.html].
- Older devdocs listed `CompanyEvent`, `LeadListEvent`, `ListChangeEvent`, `WebhookEvent` as `final`; code has `CompanyEvent`, `LeadListEvent` and `WebhookEvent` as `abstract` and `ListChangeEvent` as a plain class. The current devdocs no longer carry that list [code: app/bundles/LeadBundle/Event/CompanyEvent.php @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- Work still in progress on 8.x: PHPStan baseline 6,837 lines and native types added per PR, so expect more signature changes on base classes before release [code: phpstan-baseline.neon @8.x] [PR #18230].
- `lightsaml2/lightsaml` is pulled from a pinned git commit as an inline package, patched for `getIterator()`; packaging may change before release [code: composer.json:139-149,260-261 @8.x] [PR #17370].
- UI: 8.x has Bootstrap 5.3.8 plus the Bootstrap 3 compatibility layer from 7.x (`1.bootstrap-compatibility.js`, `_bootstrap-3-compatibility.scss`), and is removing unused parts of that layer [code: app/composer.json:114 @8.x] [code: app/bundles/CoreBundle/Assets/js/1.bootstrap-compatibility.js @8.x] [PR #18266].
