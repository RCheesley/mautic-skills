# Upgrading from Mautic 7.x to 8.x (authoritative guide)

Snapshot: 7.x = 7.2.1 plus 87 unreleased merged PRs (`419a08a9b35`, 2026-10-14; see [post-7.2.1-prs.md](post-7.2.1-prs.md)); 8.x = `11599729491` (2026-10-15), unreleased. Primary sources: `UPGRADE-8.0.md@8.x`
(read in full), three-dot diffs `upstream/7.x...upstream/8.x`, 294 first-parent merge PRs, devdocs 8.0 `plugins/update_m7_to_m8`
[code: UPGRADE-8.0.md @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]. The 8.0 devdocs URLs are
inferred from RST paths; the 8.0 site may not be published yet.

## Contents
1. Status of 8.x and how to read diffs
2. Platform and dependency changes
3. Event system: dispatch by event class (and the silent-failure trap)
4. Campaign builder: legacy action path removed
5. Per-bundle BC breaks
6. Behaviour changes users and integrators will see
7. Removed features
8. Symfony 8 and Doctrine 3/4 fallout for plugin code
9. Writing code that works on both 7.x and 8.x
10. Porting a plugin from 7.x to 8.x (step by step)
11. How to test a plugin on both 7.x and 8.x
12. What to avoid in new 7.x contributions
13. Open questions and known inconsistencies

---

## 1. Status of 8.x and how to read diffs

- 8.x is development-only. `app/release_metadata.json@8.x` still says `"version": "7.2.0"` while requiring PHP 8.4, and root `composer.json@8.x` pins `mautic/core-lib` `"7.0.0-dev"` [code: app/release_metadata.json @8.x] [code: composer.json @8.x].
- `upstream/7.x` (7.2.1 and later) is not an ancestor of 8.x. The last forward merge was 7.2.0 → 8.x on 2026-09-04; 736 7.x commits (the 7.2.1 release plus the unreleased 7.x work after it) are not on 8.x yet [PR #17253].
- Use a three-dot (merge-base) diff. A two-dot diff shows 7.x-only features as if 8.x removed them. All of the following are 7.x after 7.2.1 (unreleased; [post-7.2.1-prs.md](post-7.2.1-prs.md)): `twbs/bootstrap 5.3.8` vs `twbs/bootstrap-sass 3.4.1`, the unsubscribe email-validation page, `POST /api/companies/batch/addcontacts`, "Any associated company" segment filters, asset ZIP download, `is:never_logged_in`, Contacts "Save & New" [code: 8.x vs 7.x tree grep]. Do not document these as removed in 8.
- Scale: 1,626 commits / 350 merges since the merge-base; 3,298 files changed (+49,088 / −60,791); 266 of 294 first-parent merges are typing, Rector, PHPStan, event-dispatch and removal work [code: git log upstream/7.x...upstream/8.x].
- `UPGRADE-8.0.md` is appended per PR, and later entries supersede earlier ones. When it says a constant is "kept for backwards compatibility" but the class is gone in code, the code wins [code: UPGRADE-8.0.md @8.x] [code: app/bundles/CoreBundle/ @8.x — `CoreEvents.php` absent].

## 2. Platform and dependency changes

| Item | 7.x (7.2.1) | 8.x | Source |
|---|---|---|---|
| PHP | 8.2.0 – 8.5.99 | **8.4** minimum (`~8.4`), max 8.5.99 | [code: app/release_metadata.json @7.x] [code: app/composer.json @8.x] [PR #16993] |
| MySQL / MariaDB | ≥ 8.4.0 / ≥ 10.11.0 | unchanged | [code: app/release_metadata.json @8.x] |
| Symfony | `~7.4.0` | **`~8.1.0`** (all `symfony/*`, incl. dev packages) | [PR #17392] [PR #17309] [PR #17411] [PR #17458] |
| Doctrine ORM / DBAL | `^2.14.0` / `^3.6.2 <3.8.0` | **`^3.7` / `^4.4`** | [PR #17361] |
| doctrine-bundle / migrations-bundle | `^2.7` / `^3.2.2` | `^3.3` / `^4.0` | [PR #17361] [PR #17353] |
| data-fixtures / fixtures-bundle | `^1.6.6` / `^3.4.4` | `^2.2` / `^4.3` | [PR #17353] |
| `doctrine/cache`, `doctrine/common` | present | removed | [PR #17361] |
| API Platform core | `^4.1.0` | `^4.3.0` | [PR #17355] |
| FOSRestBundle | `^3.8` | `^3.9` | [PR #17350] |
| OAuth server bundle | `5.1.3` | `6.0.0` (oauth2-php 2.0; "no BC breaks for Mautic") | [PR #17342] |
| monolog-bundle | `~3.10.0` | `~4.0.2` | [PR #17343] |
| SAML | `javer/sp-bundle ^2.0` | `lightsaml2/sp-bundle ^5.0` + `lightsaml2/symfony-bridge ^6.0` | [PR #17370] |
| PHPUnit | `^11.5` | **`^13.0`** | [PR #17004] [PR #17019] [PR #17063] [PR #17163] |
| PHPStan | `^2.2.6`, level 6 | `^2.3`, level 6, baseline 12,268 → 8,683 lines, new custom rules | [code: phpstan.neon @8.x] [PR #17631] [PR #17640] |
| Coding standard | php-cs-fixer + ECS | ECS only | [PR #17280] [PR #17362] |
| Tool binaries | `bin/phpunit`, `bin/phpstan`, … | `vendor/bin/*` | [PR #17164] |
| Mocking finals in tests | — | `dg/bypass-finals ^1.11`, enabled in `app/tests/bootstrap.php` | [PR #17366] |

Language-level adoption on 8.x: typed class constants everywhere [PR #16996] [PR #17543]; PHP 8.4 syntax [PR #17007] [PR #17008];
more `final` classes (2,163 → 2,521 files) [PR #17536]; Doctrine mapping moving from `loadMetadata()` to `#[ORM\*]` attributes
(hybrid driver reads attributes first) [PR #17454]; validator constraints as attributes [PR #16963]; Twig functions via
`#[AsTwigFunction]` [PR #17015]; core routes as `#[Route]` attributes [PR #17169] [PR #17222] [PR #17231].

## 3. Event system: dispatch by event class

### 3.1 The rule

- Since Symfony 4.3, `EventDispatcherInterface::dispatch($event)` without a name uses `$event::class` as the name. 8.x converts almost every Mautic dispatch to this form [PR #17157] [PR #17160] [PR #17161] [PR #17218] [PR #17625].
- A PHPStan rule on 8.x enforces single-argument dispatch for custom events (`mautic.singleArgumentDispatch`) [PR #17625] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].
- Subscribe with the class as the key:

```diff
 public static function getSubscribedEvents(): array
 {
     return [
-        CampaignEvents::CAMPAIGN_ON_BUILD => ['onCampaignBuild', 0],
-        LeadEvents::LEAD_POST_SAVE        => ['onLeadPostSave', 0],
+        CampaignBuilderEvent::class       => ['onCampaignBuild', 0],
+        LeadPostSaveEvent::class          => ['onLeadPostSave', 0],
     ];
 }
 // dispatching your own events:
-$this->dispatcher->dispatch($event, MyEvents::THING_HAPPENED);
+$this->dispatcher->dispatch($event);   // name = $event::class
```
[code: UPGRADE-8.0.md @8.x]

### 3.2 WARNING: the silent-failure trap

- Removed constants fail loudly: referencing `CoreEvents::BUILD_MENU` on 8.x is a fatal "undefined constant" error [code: app/bundles/CoreBundle/CoreEvents.php absent @8.x].
- **Kept constants fail silently.** Some constants still exist on 8.x (as webhook type ids or for BC), but the event is dispatched under its class. A listener keyed on such a constant loads without error and **never runs** [code: UPGRADE-8.0.md @8.x "Changed code"].
- Highest-risk examples: `LeadEvents::LEAD_POST_SAVE` (now `LeadPostSaveEvent`), `FormEvents::FORM_ON_SUBMIT` (now `SubmissionEvent`), `EmailEvents::EMAIL_ON_OPEN` (now `EmailOpenEvent`), `PageEvents::PAGE_ON_HIT` (now `PageHitEvent`), all `ReportEvents::*`, all five `ChannelEvents::*` [code: app/bundles/*/*Events.php @7.x vs @8.x].
- The full kept-constant list is in [event-map-7-to-8.md §3](event-map-7-to-8.md). Check every subscriber against it; a passing PHP lint proves nothing.
- Verify a registration on a running 8.x install with `bin/console debug:event-dispatcher '<FQCN of event>'` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].

### 3.3 Removed constants and deleted classes

- 225 constants were removed; 7 whole classes were deleted (`ApiEvents`, `ConfigEvents`, `CoreEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents`, `UserEvents`) [code: app/bundles/*/*Events.php @7.x vs @8.x]. The mapping of every removed constant is in [event-map-7-to-8.md §6](event-map-7-to-8.md).

### 3.4 Event classes that changed shape

- Now `abstract` (instantiate a concrete subclass): `CampaignLeadChangeEvent`, `UserBundle\Event\{AuthenticationEvent,UserEvent,RoleEvent}`, `SmsEvent`, `WebhookEvent`, `ApiBundle\Event\{ClientEvent,ApiEntityEvent,ApiSerializationContextEvent}`, `IntegrationsBundle\Event\{InternalContactEvent,InternalCompanyEvent,CompletedSyncIterationEvent,ConfigSaveEvent}`, `DashboardBundle\Event\WidgetDetailEvent`, LeadBundle `CompanyEvent`, `TagEvent`, `LeadNoteEvent`, `LeadDeviceEvent`, `ImportEvent`, `LeadFieldEvent`, `LeadListEvent`, `LeadMergeEvent`, `CompanyMergeEvent`, `TagMergeEvent`, `SaveBatchLeadsEvent`, `ContactExportSchedulerEvent`, and `CoreBundle\Event\CommonEvent` [code: UPGRADE-8.0.md @8.x lines 17-135] [PR #17524].
- `LeadEvent`, `ListChangeEvent`, `AssetEvent` are no longer `final` [code: UPGRADE-8.0.md @8.x].
- `CommonEvent::setEntityManager()` and `$em` removed [PR #17482].
- `ParseEmailEvent` split: criteria methods (`setCriteriaRequest`, `getCriteriaRequests`, `getMarkAsSeenInstructions`) moved to new `PreFetchEmailEvent` [PR #17675].
- `ConditionEvent` / `DecisionEvent`: `getResult()`/`setResult()` and `setChannel()` overrides removed; use `pass()`/`fail()` and `setAsApplicable()` [PR #17151].
- `CampaignScheduledEvent` folded into `ScheduledEvent`; `CampaignDecisionEvent` removed [PR #17039] [PR #17059].
- `LeadListFiltersOperatorsEvent` constructor lost `$operators`; it starts empty and you call `addOperator()` [code: UPGRADE-8.0.md @8.x].
- `WidgetDetailEvent`: `setCacheDir()`, `setCacheTimeout()` removed; `$cacheProvider` required; `setTemplateData()` lost `$skipCache` [PR #17034].
- `BuilderEvent::addTokensFromHelper()` / `getTokensFromHelper()` removed [code: UPGRADE-8.0.md @8.x].
- New `PluginIntegrationResponseEvent`; the response is no longer readable from `PluginIntegrationRequestEvent`, so a listener that type-hints the request event for responses gets a `TypeError` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- Event constructors may no longer receive services (PHPStan `NoServiceInEventConstructorRule`) [PR #17640]. Many events gained native types [PR #17426] [PR #17438] and several became `final` (`ConfigBuilderEvent`, `MaintenanceEvent`, `StatsEvent`, `EmailValidationEvent`, `SubmissionEvent`, `MauticSyncFieldsLoadEvent`, `ImportValidateEvent`, `PageDisplayEvent`, `PageHitEvent`, `PluginIntegrationRequestEvent`, `PluginIsPublishedEvent`, `PointBuilderEvent`, `TriggerExecutedEvent`, `ReportDataEvent`, `ReportGeneratorEvent`, `ReportGraphEvent`, `SmsSendEvent`, `LoginEvent`, `WebhookBuilderEvent`, `WebhookNotificationEvent`) [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

## 4. Campaign builder: legacy action path removed

- The legacy action path (`'eventName'`/`'callback'` and per-contact `CampaignExecutionEvent`) is gone: `LegacyEventDispatcher`, `EventArrayTrait`, `CampaignDecisionEvent`, `CampaignScheduledEvent` and all `*Events::ON_CAMPAIGN_TRIGGER_ACTION` constants were removed [PR #17097] [PR #17077] [PR #17085] [PR #17039].
- A campaign action registered without `batchEventName` is **not executed at all** on 8.x [PR #17097] [code: UPGRADE-8.0.md @8.x line 141].
- Register `batchEventName` => `<Bundle>Events::ON_CAMPAIGN_BATCH_ACTION` (or your own name) and handle `PendingEvent`. This path has worked since Mautic 3, so it is safe on 7.x [code: UPGRADE-8.0.md @8.x].
- Core actions moved to the batch path: `dwc.push_content`, `tracking.pixel.send`, `plugin.leadpush`, `campaign.sendwebhook`, `focus.show` [code: UPGRADE-8.0.md @8.x].
- `ConnectionBuilder::addDeprecatedAnchorRestrictions()` removed: event keys `associatedActions`, `associatedDecisions`, `anchorRestrictions` are ignored, so the builder no longer restricts connections unless you use `connectionRestrictions` [PR #17032].
- `PendingEvent::fail(string $reason)` now requires a string [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- See mautic-campaigns for the batch execution model.

## 5. Per-bundle BC breaks

### Core / cross-cutting
- `Controller\FormController` removed; extend `AbstractFormController` or `AbstractStandardFormController`. `setStandardParameters()` is replaced by overriding `getModelName()` (required), `getPermissionBase()`, `getRouteBase()`, `getSessionBase()` (include the `mautic.` prefix to keep session keys), `getTranslationBase()`, `getTemplateBase()`, `getJsLoadMethodPrefix()`. Unlock route `mautic_core_form_action` moves unchanged to `LockController` [PR #17481] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#removed-formcontroller].
- `CommonController` helpers are now `protected` (`addFlashMessage`, `delegateRedirect`, `delegateView`, `postActionRedirect`, `forwardWithPost`, `notFound`, `throwAccessDenied`, `renderException`, …); `accessDenied()` removed (use `throwAccessDenied()` / `getAccessDeniedFlash()`). Only route actions may be public [PR #17535].
- `ClassMetadataBuilder::addLead()` / `addContact()` removed (use `#[ORM\ManyToOne]` / `#[ORM\JoinColumn]`); `AssociationBuilder::isOwnershipParent()` → `#[Mautic\CoreBundle\Entity\Attribute\OwnershipParent('form')]`; Mautic's `ManyToManyAssociationBuilder` / `OneToManyAssociationBuilder` removed (Doctrine builders returned) [PR #17460] [PR #17456] [PR #17361].
- `CommonRepository` is `abstract`; query-builder/filter params are natively typed; overrides of `addCatchAllWhereClause()` / `addSearchCommandWhereClause()` must match; public repository methods need return types [PR #17131] [PR #17524] [PR #17399]. Typed returns include `checkUniqueAlias: int`, `findOneBySlugs: ?object`, `getBaseColumns: array`, `getEntities: iterable`, `getTableName: string` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- `CommonEntity` abstract; `$changes` is `array`; `FormEntity::$new` is `bool` [PR #17808] [PR #17170].
- `Model\FormModel` methods typed (`saveEntity(object $entity, …)`, `deleteEntity(object)`, `deleteEntities(array)`, `lockEntity(object)`, `isNewEntity(object)`, `togglePublishStatus(object)`); `AbstractCommonModel::encodeArrayForUrl(array)` [PR #17365] [PR #17523].
- `ModelFactory::getModel()` resolves only via the model's static `getName()` (no FQCN, no `mautic.<bundle>.model.<name>` aliases); `ModelPass` removed [PR #17133].
- `AbstractPermissions::definePermissions()` removed: define permissions in the constructor; `array $params` constructor arg deprecated (params come via autowired `setCoreParametersHelper()`, unavailable in the constructor); permission classes are services tagged `mautic.permissions` [PR #17079] [PR #17121].
- The `services` group in `Config/config.php` (including `models`, `menus`) is no longer read; `ServicePass`, `TwigPass` removed. Declare menus (`knp_menu.menu` + `knp_menu.renderer`) and services in `Config/services.php` [PR #17470] [PR #17116] [PR #17117].
- String service ids removed (use FQCN): `mautic.security`, `symfony.filesystem`, `mautic.config.model.sysinfo`, `mautic.helper.cache_storage`, `mautic.user.provider`, `mautic.helper.paths`, `mautic.helper.token_builder`, `mautic.cache.adapter.*`, `mautic.integrations.helper*`, `mautic.sms.callback_handler_container`, model aliases (full list at `UPGRADE-8.0.md@8.x` line 177) [PR #16875] [PR #17124] [PR #17134].
- Every class/interface constant is typed (`public const string X`); overriding constants must be typed (`AbstractMauticMigration::TABLE_NAME` is `?string`) [PR #16996] [PR #17543].
- Native `array` return types on many base classes/interfaces (`StepInterface`, `ThemeHelperInterface`, `AbstractPermissions::getPermissions()`, `BuilderEvent::getTokens()`, `AbstractMauticMigration::generateKeys()`, …) [code: UPGRADE-8.0.md @8.x lines 974-1015].
- Removed: `CacheStorageHelper`, `EmojiHelper` + maps, `Entity\Cache`, `PublishStatusIconAttributesInterface`, `UuidTrait::isValidUuid()` (use `UuidHelper`), `VariantModelTrait::convertVariant()` (use `VariantConverterService`), `GeneratedColumns::getForOriginalDateColumnAndUnit()`, `AbstractFormFieldHelper::setTranslator()`, `RedisSentinelSessionHandler`, `ModeratedCommand::MODE_LOCK`, `Translation\TranslatorLoader` [PR #17033] [PR #17026] [PR #17050] [PR #17393].
- DBAL `createQueryBuilder()` returns `Mautic\CoreBundle\Doctrine\Query\QueryBuilder` (keeps `getQueryPart(s)`, `resetQueryPart`); `new QueryBuilder($conn)` loses them; `Doctrine\ReservedWords` replaces the platform keyword list [PR #17361].
- Core routes moved from `Config/config.php` `routes` to `#[Route]` attributes; `RouteLoader` scans `app/bundles/*/Controller` only. **Plugins keep using `config.php` `routes`** [PR #17169] [PR #17222] [PR #17231].
- Deleted without an `UPGRADE-8.0.md` entry: `CoreBundle\Entity\UpsertTrait`, `CoreBundle\Event\UpgradeEvent`, `HashHelper(+Interface)`, `Test\DoctrineExtensions\TablePrefix`, Bounce `Definition\Rule`, IntegrationsBundle OAuth credential interfaces and `IntegrationMappingException` / `InvalidProviderException`, `LeadBundle\Helper\CampaignEventHelper`, `Segment\Exception\InvalidUseException`, `StageBundle\Helper\EventHelper`, `MauticFullContactBundle\Exception\ApiException`, Codeception functional suite [PR #17182] [PR #17183] [PR #17184] [PR #17185] [PR #17241].

### ApiBundle
- `ApiEvents` removed; `Client/ApiEntity/ApiSerializationContext` events are abstract with concrete subclasses [PR #17217].
- `CommonApiController::prePopulateForm()`, `preSaveEntity()` take `array $parameters`; `processForm(?array)`; `getNewEntity()`, `getCurrentRequest()`, `postActionRedirect()` now `protected`; `accessDenied()`, `badRequest()`, `notFound()` return `Response`; `prepareParametersForBinding(...)` must return `array|Response` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

### AssetBundle
- CRUD events by class (`AssetPreSaveEvent`, `AssetPostSaveEvent`, `AssetPreDeleteEvent`, `AssetPostDeleteEvent`, `AssetLoadEvent`, `RemoteAssetBrowseEvent`); `ASSET_ON_UPLOAD` dropped; service `mautic.asset.upload.error.handler` removed [PR #17196] [PR #17215].

### CampaignBundle
- 21 constants removed (see event map); legacy action path removed (§4); `ActionDispatcher` and `DecisionDispatcher` constructors changed [PR #17097].
- Removed: `EventScheduler::reschedule()` (use `rescheduleLogs()`), `CampaignRepository::fetchEmailIdsById()`, `getCampaignLeadCount()`, `Campaign::getOnclickMethod()` / `getDataAttributes()` / `getTranslationKeysDataAttributes()` [code: UPGRADE-8.0.md @8.x].
- `CampaignModel::getLeadSources(Campaign|int|string)`, `getCampaignsByForm(Form|int)`; `CampaignBuilderEvent::add*(string $key)` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

### ChannelBundle / CategoryBundle / ConfigBundle / DashboardBundle / DynamicContentBundle
- Channel: five events dispatched by class while their constants are kept (trap) [code: UPGRADE-8.0.md @8.x].
- Category: `CATEGORY_ON_BUNDLE_LIST_BUILD` → `CategoryTypesEvent` (constant kept, trap); duplicate `CATEGORY_*` constants removed from `DynamicContentEvents` [code: UPGRADE-8.0.md @8.x].
- Config: `ConfigEvents` removed → `ConfigBuilderEvent` (final), `ConfigPreSaveEvent`, `ConfigPostSaveEvent` [PR #17625].
- Dashboard: `DashboardEvents` removed → `WidgetTypeListEvent`, `WidgetFormEvent`, `GenerateWidgetDetailEvent`, `PreLoadWidgetDetailEvent`; `WidgetDetailEventFactory` lost three args [PR #17216] [PR #17034].
- DynamicContent: `ON_CONTACTS_FILTER_EVALUATE` → `ContactFiltersEvaluateEvent`; `TOKEN_REPLACEMENT` → `Mautic\CoreBundle\Event\TokenReplacementEvent` [PR #17691].

### EmailBundle
- 20 constants removed; kept: `EMAIL_ON_OPEN` (trap), `EMAIL_ON_SEND`, `EMAIL_FAILED`, `EMAIL_RESEND`, campaign constants, `ON_SENT_EMAIL_TO_USER`, `ON_DETERMINE_*` [code: app/bundles/*/*Events.php @7.x vs @8.x].
- `MailHelper::validateEmail()` removed (use `EmailValidator`); `MailHelper` is `final` [code: UPGRADE-8.0.md @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- Return types: `Email::getContent(): array|string`, `getUtmTags()`, `getHeaders()`, `Stat::getOpenDetails()` → `array`; `Stat::getTokens(): ?array` [code: UPGRADE-8.0.md @8.x].

### FormBundle
- Form "type" (`standalone`/`campaign`) removed: `Form::$formType`, `getFormType()`, `setFormType()`, `isStandalone()`, API field `formType`, `FormRepository::getFormList($formType)`; migration `Version20260814141635` drops `forms.form_type` [PR #17082] [PR #17059].
- `SubmissionEvent` is `final`; `setPostSubmitCallbackResponse()` requires a `RedirectResponse` (devdocs call this the "biggest impact" change); `getPostSubmitPayload(): ?array` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

### IntegrationsBundle
- `IntegrationEvents` removed (23 constants); new concrete events such as `InternalContactFieldChangesEvent`, `ConfigBeforeSaveEvent`, `ConfigAfterSaveEvent` [PR #17160].
- `DefaultConfigFormTrait` removed: implement `getConfigFormName()` / `getConfigFormContentTemplate()` [code: UPGRADE-8.0.md @8.x].
- `MappingManualDAO`: object mappings go to the constructor (`new MappingManualDAO($name, [$objectMapping])`); `addObjectMapping()` is `private`. Not in `UPGRADE-8.0.md` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html] [code: IntegrationsBundle/Sync/DAO/Mapping/MappingManualDAO.php @8.x].
- `getIntegrationConfiguration()` throws `\LogicException` when unset; check `hasIntegrationConfiguration()` first [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

### LeadBundle
- 56 constants removed; many kept-but-class-dispatched (trap) [code: app/bundles/*/*Events.php @7.x vs @8.x].
- Removed: `LeadModel::isContactable()` (use `DoNotContact::isContactable()`), `FieldModel::getFieldList()` (use `Field\FieldList`), `OperatorOptions::IN` / `NOT_IN` (use `INCLUDING_ANY` / `EXCLUDING_ANY`), `LeadModel::getTagRepository()`, `CompanyModel::getCompanyLeadRepository()`, `AjaxController::addLeadUtmTagsAction()` [code: UPGRADE-8.0.md @8.x] [PR #17247] [PR #17248].
- `IdentifyCompanyHelper` is an autowired service with instance methods [PR #17260].
- `Segment\Query\QueryBuilder::setParameter()` rejects `:`-prefixed keys [code: UPGRADE-8.0.md @8.x].
- `FieldDeleteDispatcher::dispatchPreDeleteEvent()` removed and `dispatchEvent()` is private; the `UPGRADE-8.0.md` advice at line 262 is stale [code: LeadBundle/Field/Dispatcher/FieldDeleteDispatcher.php @8.x].
- `ContactTracker::setUseSystemContact(bool)` is non-nullable; `editAction(int $objectId)` on Company/Field/Lead controllers [code: UPGRADE-8.0.md @8.x lines 1037-1088].

### NotificationBundle / PageBundle / PluginBundle
- Notification: `NotificationHelper::unsubscribe()` removed; dead route `mautic_receive_notification` removed [code: UPGRADE-8.0.md @8.x].
- Page: `PublicController::indexAction()` lost the v1 theme path; `RedirectModel::generateRedirectUrl($redirect, $clickthrough)`; `HitRepository::getHitCountForSource()` removed [PR #17078].
- Plugin: `AbstractIntegration` 2nd constructor arg is `CacheProviderInterface`; `getCache(): Psr\SimpleCache\CacheInterface`; ~18 methods gain `array` returns; `mergeApiKeys(): ?array`; `AbstractSsoFormIntegration` removed (extend `AbstractSsoServiceIntegration`, return `['sso_form']` from `getSupportedFeatures()`); `IntegrationEntityModel::logDataSync()` removed [code: UPGRADE-8.0.md @8.x]. Integrations built on `BasicIntegration` are unaffected by the `AbstractIntegration` type changes [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

### Point / Stage / Report / Sms / User / Webhook / Stats
- Point: `POINT_ON_ACTION` → `PointActionEvent`; `SCORE_CHANGE` → `GroupScoreChangeEvent` (constants kept, trap) [code: UPGRADE-8.0.md @8.x].
- Stage: `STAGE_ON_BUILD` → `StageBuilderEvent`; `Helper\EventHelper` deleted [code: UPGRADE-8.0.md @8.x].
- Report: 8 events by class, constants kept (trap) [code: UPGRADE-8.0.md @8.x].
- Sms: 10 constants removed; `SmsEvent` abstract; route `mautic_receive_sms` removed (use `/sms/twilio/callback`) [PR #17622].
- User: `UserEvents` removed → `LoginEvent`, `LogoutEvent`, `PreAuthenticationEvent`, `FormAuthenticationEvent`, `AuthenticationContentEvent`, `PasswordStrengthValidateEvent`, `Pre/PostSave/DeleteUserEvent`, `Pre/PostSave/DeleteRoleEvent` [PR #17510] [PR #17623].
- Webhook: `ON_CAMPAIGN_TRIGGER_ACTION` → `ON_CAMPAIGN_BATCH_ACTION`; `WEBHOOK_ON_BUILD` etc. kept (trap) [PR #17085] [PR #17202].
- Stats: `StatEvents` removed → `AggregateStatRequestEvent` [PR #17654].

### Shipped plugins
- MauticCrmBundle: `ConnectwiseIntegration`, `HubspotIntegration`, `SalesforceIntegration`, `VtigerIntegration` are `final`; dead route `mautic_integration_companies` removed [code: UPGRADE-8.0.md @8.x].
- MauticSocialBundle: `SocialEvent` removed → `AbstractMonitorEvent` / `AbstractTweetEvent` + 8 lifecycle classes [PR #17544].
- MauticTagManagerBundle: `Entity\Tag` removed (ORM 3 rejects an unmapped-inheritance subclass) [PR #17361].
- GrapesJsBuilderBundle: legacy `/grapesjsbuilder/assets` endpoint removed [PR #17070].
- MauticClearbitBundle: removed [PR #17785].

## 6. Behaviour changes users and integrators will see

| Change | Effect | Source |
|---|---|---|
| Listeners keyed on removed / kept-but-unused names | Fatal "undefined constant" / silently never runs | §3 |
| Legacy campaign actions | Not executed; only `batchEventName` actions run | [PR #17097] |
| `associatedActions` / `associatedDecisions` / `anchorRestrictions` | Ignored | [PR #17032] |
| Cache via CacheBundle | A miss returns `null`, not `false`; integration/widget cache lives in `cache_adapter` and is dropped by cache clear; `cache_items` no longer written | [PR #17033] [PR #17155] |
| Emoji | No shortcode/entity conversion; stored as UTF-8 (`utf8mb4`) | [PR #17026] |
| `mautic:disable-tracking` link attribute | No longer honoured: links are tracked; use `data-mautic-disable-tracking="true"` | [docs: https://docs.mautic.org/en/8.0/channels/emails.html] |
| Landing Pages with empty custom HTML | No v1 theme fallback | [PR #17078] |
| Forms API / export | `formType` dropped from responses, ignored on input | [PR #17082] [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/forms.html] |
| `--lock_mode=file_lock` | Fails `Unknown locking method specified.` (use `flock`) | [code: UPGRADE-8.0.md @8.x line 267] |
| `/sms/receive` | 404; Twilio callback must be `/sms/twilio/callback` | [code: UPGRADE-8.0.md @8.x line 277] |
| Generated SQL aliases | Checked against `ReservedWords`; a few aliases now get prefixed | [PR #17361] |
| Asset upload size validation | Fixed an off-by-1000 error | [PR #17080] |
| Route matching | Attribute routes sorted by specificity; same paths, different order | [PR #17169] |
| SAML | Bundle swapped to lightsaml2; behaviour intended unchanged — test IdP login | [PR #17370] |
| Redis Sentinel session handler | Gone; configs referencing it break | [PR #17050] |
| Webhook `company_soft_delete` | Event name is `Mautic\LeadBundle\Event\CompanySoftDeleteEvent` | [devdocs: https://devdocs.mautic.org/en/8.0/webhooks/events/company_soft_delete.html] |
| DB schema | One new migration (`Version20260814141635`, drop `forms.form_type`); CI fails if an existing table changes shape and runs `doctrine:schema:validate` | [PR #17407] [PR #17346] |

## 7. Removed features

| Removed | Why | Source |
|---|---|---|
| Clearbit plugin (`plugins/MauticClearbitBundle`, translations `mautic.plugin.clearbit.*`, `mautic.integration.clearbit.apikey`, 4 Twig templates) | Service sunset after the HubSpot acquisition | [PR #17785] |
| Form type standalone/campaign | Unused since 7.1; every Form is usable in Campaigns | [PR #17082] |
| Mautic v1 theme fallback for Landing Pages, `{{ public }}` template param | Deprecated | [PR #17078] |
| Legacy campaign action path | Batch only | [PR #17097] |
| Emoji conversion | UTF-8 directly | [PR #17026] |
| `CacheStorageHelper`, `Entity\Cache`, filesystem widget cache | CacheBundle only | [PR #17033] [PR #17155] |
| `RedisSentinelSessionHandler` | Deprecated since 5.0 | [PR #17050] |
| `mautic:disable-tracking` attribute | Use `data-mautic-disable-tracking` | [code: UPGRADE-8.0.md @8.x] |
| GrapesJS legacy asset endpoint | Media endpoint since 5.2 | [PR #17070] |
| Routes `mautic_receive_sms`, `mautic_receive_notification`, `mautic_campaign_import_index`, `mautic_integration_companies` | Dead/alias | [PR #17231] |
| `ModeratedCommand::MODE_LOCK` (`file_lock`) | — | [code: UPGRADE-8.0.md @8.x] |
| AJAX `lead:addLeadUtmTags`, JS `Mautic.createLeadUtmTag()` | Unused | [code: UPGRADE-8.0.md @8.x] |
| `AbstractSsoFormIntegration`, TagManager `Entity\Tag` | — | [code: UPGRADE-8.0.md @8.x] [PR #17361] |
| Compiler passes `ModelPass`, `ServicePass`, `PermissionsPass`, `TwigPass`; `config.php` `services` group | Symfony DI/autoconfigure | [PR #17133] [PR #17116] [PR #17121] [PR #17117] [PR #17470] |

The 8.0 user docs mostly describe 7.2.x features; the only 8-specific user-facing doc change is the `mautic:disable-tracking`
removal. They do not yet mention PHP 8.4, Clearbit removal, form types or `file_lock` [docs: https://docs.mautic.org/en/8.0/channels/emails.html].

## 8. Symfony 8 and Doctrine 3/4 fallout for plugin code

- `Request::get()` is removed. Use `$request->attributes->get()`, `->query->get()`, `->request->get()` (core rewrote 94 files) [PR #17309] [PR #17347].
- Constraint constructors no longer accept an options array; pass named arguments (`new Length(max: 255)`). A positional array silently does nothing on custom constraints [PR #17392].
- `Url::$requireTld` defaults to `true` (core passes `requireTld: false`); `UrlType` `default_protocol` defaults to `null` (core sets `'http'`) [PR #17392] [PR #17349].
- `UserInterface::eraseCredentials()` gone; `FrameworkBundle\Translation\Translator`, `InputBag` and `Router` are `final` (tests must not mock them); `ConstraintValidator::initialize()+validate()` deprecated for `validateInContext()` [PR #17392] [PR #17393].
- Doctrine: use `getEntityManager()` not `$this->_em`; `ClassMetadata` not `ClassMetadataInfo`; `ArrayParameterType` not `Connection::PARAM_*_ARRAY`; build composite expressions from a finished list (`CompositeExpression::and(...$parts)`), never `->add()`; take query builders from the connection; map the `lead` relation with attributes or `createManyToOne('lead', Lead::class)->addJoinColumn('lead_id', 'id', …)` [code: UPGRADE-8.0.md @8.x lines 931-946].

## 9. Writing code that works on both 7.x and 8.x

1. **Subscribe by event class wherever the class exists on 7.x** (most do: `CampaignBuilderEvent`, `MenuEvent`, `SubmissionEvent`, `ReportBuilderEvent`, `LeadListFilteringEvent`, …). On 7.x the dispatcher still uses the string name, so register **both keys**, guarded [code: UPGRADE-8.0.md @8.x]:
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
   Each version dispatches the event under one name only (string on 7.x, class on 8.x), so the handler runs once per dispatch [code: app/bundles/*/*Events.php @7.x vs @8.x].
2. **Events whose concrete class exists only on 8.x** (`LeadPostSaveEvent`, `PostSaveUserEvent`, `CampaignPostSaveEvent`, …): guard with `class_exists()` and type-hint the shared parent (`LeadEvent`, `UserEvent`, `CampaignEvent`) in the handler [code: UPGRADE-8.0.md @8.x].
3. **Classes that disappear** (`CoreEvents`, `UserEvents`, `IntegrationEvents`, `ApiEvents`, `ConfigEvents`, `DashboardEvents`, `StatEvents`): never reference their constants unguarded; `defined('Mautic\CoreBundle\CoreEvents::BUILD_MENU')` is safe [code: app/bundles/*/*Events.php @7.x vs @8.x].
4. **Kept-but-unused constants** (§3.2): also add the class key; the constant key alone only works on 7.x [code: UPGRADE-8.0.md @8.x].
5. **Campaign actions**: register `batchEventName` and handle `PendingEvent`; conditions use `pass()`/`fail()`, decisions `setAsApplicable()`; use `connectionRestrictions` [PR #17097] [PR #17151] [PR #17032].
6. **Add native types to every override now** (params, returns, typed constants, typed redeclared properties). PHP lets a child add a return type its parent lacks, so typed code runs on 7.x and 8.x [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
7. **Get services by class name** (`CorePermissions::class`, `Filesystem::class`, `CacheProviderInterface`); get models via `ModelFactory::getModel('bundle.name')` with a static `getName()` on your model, or inject the model [PR #17133].
8. **Cache**: inject `CacheProviderInterface`; treat a miss as `null` (and also `false` if you still support `CacheStorageHelper` on 7.x) [devdocs: https://devdocs.mautic.org/en/8.0/plugins/cache.html#migrating-to-cachebundle-in-mautic-8].
9. Declare menus and services in `Config/services.php`; keep plugin routes in `Config/config.php` `routes` [PR #17470] [PR #17169].
10. Request access via `query`/`request`/`attributes` bags; constraints with named arguments [PR #17392].
11. Do not extend or mock `final` classes; compose and prefer interfaces. Use `data-mautic-disable-tracking="true"` [PR #17536].
12. Declare the supported range in the plugin's `composer.json` (`"mautic/core-lib": "^7.0 || ^8.0"` style constraint) and set `MINIMUM_MAUTIC_VERSION` on the bundle class if you need a floor; the kernel skips loading a plugin bundle when the running version is lower [code: app/AppKernel.php:175-181 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/marketplace/listing.html].

## 10. Porting a plugin from 7.x to 8.x (step by step)

Distilled from devdocs `update_m7_to_m8` and `UPGRADE-8.0.md` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html] [code: UPGRADE-8.0.md @8.x].

1. Require PHP 8.4, Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4 in the plugin's composer constraints (`mautic/core-lib` 8.x).
2. Grep for `Events::` in `getSubscribedEvents()` and for two-argument `dispatch(` calls. Replace with event classes using [event-map-7-to-8.md](event-map-7-to-8.md). Check every remaining constant key against the kept-constant trap list.
3. Convert campaign actions to `batchEventName` + `PendingEvent`; drop `eventName`/`callback`.
4. Fix fatal signature mismatches: copy parent signatures exactly for overrides of `CommonRepository`, `FormModel`/`AbstractCommonModel`, `AbstractIntegration`/`CrmAbstractIntegration`/`SocialIntegration`, `CommonController`/`CommonApiController`/`FetchCommonApiController`, event classes and dashboard `Widget`. Type overriding constants (`public const string`) and redeclared `$changes`/`$new` properties. The four kinds of break are: new parameter type, new return type (a `null` or missing return now throws `TypeError`), new property type, removed property.
5. Stop extending classes that are now `final` (models, repositories, `MailHelper`, CRM integrations, many events); compose instead.
6. Replace removed classes and services: `FormController` (mapping table in devdocs), `CacheStorageHelper`, `AbstractSsoFormIntegration`, `DefaultConfigFormTrait`, string service ids.
7. Move permissions into the constructor and register the class as a service; move menus to `services.php`.
8. Apply the Doctrine 3/4 API changes (§8); move `addLead()` / `isOwnershipParent()` to attributes.
9. Callers of controller helpers from outside the controller break (helpers are `protected`).
10. Tests: PHPUnit 13, `dg/bypass-finals` bootstrap for mocking finals, no doubles of `Request`/`InputBag`/`Router`.
11. Verify with `rm -rf var/cache && bin/console` (container compiles) and `bin/console debug:event-dispatcher` for each event you listen to [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].

## 11. How to test a plugin on both 7.x and 8.x

The goal is to catch the two failure modes that a 7.x-only test run misses: fatal signature errors (loud) and listeners that never fire (silent).

**Environments.**
- Run the plugin inside two Mautic checkouts: the `7.x` branch (or a 7.2.x tag) on PHP 8.2+, and the `8.x` branch on PHP 8.4+. Both need MySQL ≥ 8.4.0 or MariaDB ≥ 10.11.0 [code: app/release_metadata.json @7.x] [code: app/release_metadata.json @8.x]. Core CI itself tests PHP 8.2 × MySQL 8.4 / MariaDB 10.11 and PHP 8.5 × MySQL 9.2 / MariaDB 11.4 on 7.x [code: .github/workflows/tests.yml:25-32 @7.x]. See mautic-dev-environment for DDEV setup.
- Remember 8.x lacks the 7.2.1 and later 7.x work until the next forward merge; a test that depends on a 7.x-only feature fails on 8.x for that reason, not because of your port [PR #17253].

**Static checks (both versions).**
- Clear the cache and boot the container: `rm -rf var/cache && bin/console` — this catches service wiring and compile errors [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
- `bin/console lint:twig plugins/<YourBundle>` for templates [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
- Run PHPStan against each core version. On 8.x core uses `vendor/bin/phpstan`; on 7.x `bin/phpstan` [PR #17164]. Signature mismatches against 8.x base classes show up here before runtime.

**Listener registration (both versions).**
- For each event you handle, run `bin/console debug:event-dispatcher '<event name or FQCN>'` and assert your listener appears under the name that version dispatches: the string constant on 7.x, the class on 8.x [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html].
- Write one functional test per listener that performs the real action (save a Contact, submit a Form, run the campaign action) and asserts the listener's side effect. A unit test that calls the handler directly cannot detect the silent-failure trap [code: UPGRADE-8.0.md @8.x "Changed code"].

**PHPUnit across versions.**
- 7.x uses PHPUnit 11.5; 8.x uses PHPUnit 13 [code: composer.json @7.x] [code: composer.json @8.x]. Write tests that run on both: data providers must be `static` (core even patches Twig's `IntegrationTestCase` for this on PHPUnit 11) [code: composer.json:234-238 @7.x].
- On 8.x more classes are `final`; mocking them needs the `DG\BypassFinals` bootstrap, which core enables in `app/tests/bootstrap.php@8.x`. Prefer interfaces or real objects so the same test runs on 7.x [PR #17366] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#final-classes].
- Do not create doubles of `Request`, `InputBag` or `Router` (final under Symfony 8) [PR #17392].
- Functional tests build the schema from entity metadata and mark migrations executed; they do not exercise migrations. Test plugin migrations separately (see mautic-plugin-development) [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:159 @7.x].
- See mautic-testing for base classes (`MauticMysqlTestCase`) and fixtures.

**Campaign actions.**
- On 8.x an action without `batchEventName` is silently not executed. Add a functional test that runs `mautic:campaigns:trigger` for a campaign using your action and asserts the outcome, on both versions [PR #17097].

## 12. What to avoid in new 7.x contributions (removed in 8.x)

`*Events::CONST` as subscriber keys or second `dispatch()` argument; `ON_CAMPAIGN_TRIGGER_ACTION` / `eventName`+`callback`
actions; `CampaignExecutionEvent`, `CampaignDecisionEvent`, `ConditionEvent::setResult()`; `CacheStorageHelper`; `EmojiHelper`;
`Core\Controller\FormController`; `AbstractPermissions::definePermissions()` and the `array $params` constructor; `services` /
`menus` / `models` arrays in `config.php`; string service ids (`mautic.security`, `mautic.helper.*`, `mautic.<bundle>.model.*`,
`symfony.filesystem`); `ClassMetadataBuilder::addLead()/addContact()/isOwnershipParent()`; `Form::getFormType()/isStandalone()`;
`LeadModel::isContactable()`, `FieldModel::getFieldList()`, `MailHelper::validateEmail()`, `OperatorOptions::IN/NOT_IN`;
static `IdentifyCompanyHelper::` calls; `mautic:disable-tracking`; `--lock_mode=file_lock`; `/sms/receive`; `Request::get()`;
`$this->_em` in repositories; constraint option arrays; `MappingManualDAO::addObjectMapping()`; Clearbit
[code: UPGRADE-8.0.md @8.x].

## 13. Open questions and known inconsistencies

- `UPGRADE-8.0.md` contradictions: "Changed code" says `CoreEvents`, `IntegrationEvents`, `PluginEvents`, `DashboardEvents`, `UserEvents`, `WebhookEvents` CRUD, `LeadEvents` CRUD/merge and `EmailEvents::EMAIL_PARSE/EMAIL_PRE_FETCH` constants are "kept"; the code removed them. The `CacheStorageHelper` entry says `Entity\Cache`/`cache_items` are kept; a later entry removes the entity. The `Form::setFormType()` entry says the column is unchanged; a migration drops it [code: UPGRADE-8.0.md @8.x] [PR #17155].
- Devdocs list `CompanyEvent`, `LeadListEvent`, `ListChangeEvent`, `WebhookEvent` as `final`; code has `CompanyEvent`, `LeadListEvent` and `WebhookEvent` as `abstract` and `ListChangeEvent` as a plain class. Trust code [code: LeadBundle/Event/CompanyEvent.php @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#affected-classes].
- Devdocs 8.0 call `LIST_FILTERS_ON_FILTERING` both "remains defined" and "removed"; the constant diff shows it removed [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html] [code: app/bundles/*/*Events.php @7.x vs @8.x].
- Devdocs claim the 7→8 changes cause "no runtime behaviour change", yet narrowed types (`SubmissionEvent`, `TokenReplacementEvent::setContent`, `setDateSent`) throw at runtime [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#event-and-entity-classes].
- Work still in progress on 8.x: commented-out `LoadMetadata*ToDoctrineAttributeRector` rules (mapping style will keep changing), PHPStan baseline 8,683 lines, type-coverage thresholds rising per PR — expect more native types on base classes [code: rector.php @8.x] [PR #17766] [PR #17775].
- `lightsaml2/lightsaml` is pulled from a pinned git commit as an inline package; packaging may change before release [PR #17370].
- UI asset stack for 8.0 undecided on this snapshot: the 7.x branch moved to Bootstrap 5.3.8 after 7.2.1 (unreleased; [PR #17767]; 7.2.1 itself ships `bootstrap-sass 3.4.1`), 8.x still has `bootstrap-sass 3.4.1` until the forward merge [code: composer.json @7.x vs @8.x].
