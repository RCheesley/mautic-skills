# REST API framework: version notes

Authoritative behaviour is 7.x (commit 419a08a9b35: release 7.2.1 plus unreleased merged PRs). 8.x is unreleased development (its `release_metadata.json` still says
7.2.0). [code: app/release_metadata.json @8.x]

## History that explains current behaviour

- `Mautic-Version` response header exists since 2.4.0.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#mautic-version-verification]
- Before Mautic 5, `local.php` lived in `app/config/local.php`; from 5 it is `config/local.php`.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html]
- Older releases stored token lifetimes in seconds (3600 and 1209600); the 7.x configuration form rewrites those legacy
  values to 60 minutes and 14 days for display. [code: app/bundles/ConfigBundle/Form/Type/ConfigType.php:27-37 @7.x]
- Before Mautic 7 an API rate limiter existed, configured with `api_rate_limiter_cache` (`file_system` default, memcached
  alternative). It is not available in 7 or later and 7.2.1 has no rate limiting code.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-rate-limiter-cache]
  [code: app/config/security.php:105-108 @7.x]

## Mautic 5.x and 6.x

- 5.0: the OAuth server fork moved to a Twig branch reset on upstream master (bc-break, an event listener was renamed),
  and the API Credentials UI moved to Twig. [PR #12091] [PR #11853]
- 5.0.3: API output works with `jms/serializer-bundle` ^5.4 on Composer installs without a lock file. [PR #13272]
- 5.1: `ApiSerializationContextEvent` lets plugins change serializer groups and exclusion strategies; `ClientController`
  extends `AbstractStandardFormController`. [PR #12734] [PR #13296]
- 5.2: the API Credentials list paginates and sorts by name. 5.2.7: a batch edit can change one entity more than once.
  [PR #14167] [PR #14928]
- 6.0: `where[...][val]` values are no longer HTML-entity encoded. [PR #14550]
- No other 5.x or 6.x API-framework differences were found in the 158 harvested API and webhooks PRs. [PR #14550]

## Mautic 7.x

- 7.0: API Platform v2 at `/api/v2` (new in Mautic 7 per the code analysis), with the Mautic permission voter, ownership
  collection extension, PUT processor and write subscriber. The devdocs v2 page gives no introduction version.
  [code: app/config/routing.php:10-12 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/api_v2.html]
- 7.0: Point Insights and their `/api/points/insights` endpoints were introduced.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/point_insights.html]
- 7.0: the rate limiter and `noxlogic/ratelimit-bundle` were removed (bc-break, UPGRADE-7.0.md); no replacement exists
  on the 7.x head. The OAuth server bundle is `klapaudius/oauth-server-bundle` 5.1.3. [PR #14876] [PR #15436]
- 7.1.0: opt-in 409 API locking (`ApiLockAwareInterface`, Emails only). [PR #15299]
- 7.1.2: security release adding v2 ownership scoping (`OwnershipScopedCollectionExtension`, owner-aware voter, metadata
  meta-test). 7.1.3: User-bound OAuth bearer tokens work on `/api/v2`. [PR #16175] [PR #16245]
- 7.2.0: `PreAuthorizationEventListener` subscribes itself; the voter takes the nullable `$vote` argument; the v2
  permission-context event was added. [PR #16879] [PR #16566] [PR #16837]
- 7.1: the Form `formType` field was deprecated. [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/forms.html#form-properties]
- 7.2: the `mautic.api.oauth.event_listener` service alias is deprecated; use `PreAuthorizationEventListener::class`.
  [code: app/bundles/ApiBundle/Config/services.php:29-31 @7.x]
- 7.2: the 7.2 plugin docs document `ApiEvents::API_PLATFORM_PERMISSION_CONTEXT` for placeholder permissions.
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#api-permission-context-event]
- 7.x after 7.2.1 (unreleased): `POST /api/companies/batch/addcontacts` exists (documented only in the 8.0 docs) [PR #16512]; legacy `/api/projects` CRUD is added [PR #15569] (`/api/v2/projects` already ships in 7.2.1).
  [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:122-124 @7.x]
- Component versions on 7.2.1: API Platform core `^4.1.0`, FOSRestBundle `^3.8`, OAuth server bundle 5.1.3, Symfony
  `~7.4.0`, PHP 8.2. [PR #17355] [PR #17350] [PR #17342]

## Mautic 8.x delta

Branch topology: 8.x was forked before the 7.2.1 work, so 7.x-only features (7.2.1 and the unreleased work after it) such as
`POST /api/companies/batch/addcontacts` are absent from 8.x today and are expected with the next forward merge. Do not
document them as removed. [PR #17253]

| Change | Impact on API code | Source |
|---|---|---|
| `Mautic\ApiBundle\ApiEvents` class deleted. Subscribe by event class: `PreSaveApiEntityEvent`, `PostSaveApiEntityEvent`, `PreSerializationContextEvent`, `PostSerializationContextEvent`, `ApiPlatformPermissionContextEvent`, `ClientPostSaveEvent`, `ClientPostDeleteEvent`. `CLIENT_PRE_SAVE` and `BUILD_ROUTE` removed without replacement. A subscriber keyed on the old string receives nothing. | Referencing the class fatals (`Class "Mautic\ApiBundle\ApiEvents" not found`). | [PR #17217] [PR #17654] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/api.html#upgrade-api-event-subscribers-to-mautic-8] |
| `ApiEntityEvent`, `ClientEvent`, `ApiSerializationContextEvent` become abstract bases. | Code that does `new ApiEntityEvent(...)` must use the concrete subclass; type-hints on the base still work. | [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/api.html#upgrade-api-event-subscribers-to-mautic-8] |
| API entity save events are dispatched only when a listener subscribes. | No behaviour change for callers. | [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/api.html#api-entity-save-events] |
| `CommonApiController::prePopulateForm()`, `preSaveEntity()` take `array $parameters`; `processForm(?array)`, `processBatchForm(?array)`; `FetchCommonApiController::getBatchEntities(array)`; `getNewEntity()`, `getCurrentRequest()`, `postActionRedirect()` become `protected`; `accessDenied()`, `badRequest()`, `notFound()` return `Response`; `checkEntityAccess(): bool|Response`; `returnError(): Response|array`; `validateBatchPayload(): Response|array|true`. | Plugin controllers overriding these must copy the new signatures exactly; callers from outside the controller break. | [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html] |
| `oAuth2\Client::getRole(): ?Role`. | Typed return. | [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html] |
| Core bundle routes, including `/api/...`, move from `Config/config.php` to `#[Route]` attributes with full paths; attribute routes are sorted by specificity. Plugins keep `config.php` `routes` (including `routes.api`). | Paths unchanged, match order may differ. | [PR #17169] [PR #17222] [PR #17231] [code: app/bundles/CoreBundle/Loader/RouteLoader.php @8.x] |
| Controller service argument in the plugin API example becomes `CorePermissions::class`; the `mautic.security` service id is removed. | Update plugin service definitions. | [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/api.html] [PR #16875] |
| API Platform core `^4.3.0`, FOSRestBundle `^3.9`, OAuth server bundle 6.0.0 (oauth2-php 2.0, "no BC breaks for Mautic"), Symfony `~8.1.0`, PHP 8.4. | Re-run v2 and OAuth tests after upgrading. | [PR #17355] [PR #17350] [PR #17342] [PR #17392] [PR #16993] |
| Form `formType` removed from API responses and ignored on input; column dropped. | Clients must not rely on `formType`. | [PR #17082] [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/forms.html#form-properties] |
| PHPUnit 13 and `dg/bypass-finals`; many classes become `final`. | API tests mocking finals need the bootstrap. | [PR #17004] |

No 8.x change to the v1 URL scheme, response envelopes, `api_*` parameters, the token endpoints or the 409 lock contract
is recorded in the inputs. [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/getting_started.html]

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
