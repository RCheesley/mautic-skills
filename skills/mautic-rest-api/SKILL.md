---
name: mautic-rest-api
description: "The Mautic REST API framework: enabling the API, HTTP Basic auth vs OAuth2 (authorization_code, refresh_token, client_credentials, API Credentials, /oauth/v2/token), the v1 /api/... conventions shared by every resource (search/start/limit/orderBy, where[] filters, response envelopes, PUT vs PATCH, batch endpoints and limits, error codes, 409 checked-out locking), API Platform v2 under /api/v2 (JSON-LD, ownership-scoped permissions), rate limiting, the full endpoint inventory, and how to add API support for a new entity or plugin. Use whenever a task mentions the Mautic API, REST, /api/, /api/v2, OAuth, access or bearer tokens, Basic Auth, API credentials, API permissions, pagination, batch endpoints, 401/403/404/409/422 API errors, mautic/api-library, CommonApiController, ApiEvents, ApiResource, routes.api in config.php, or touches app/bundles/ApiBundle/ or any */Controller/Api/*."
---
# Mautic REST API framework

## Scope
The REST API framework in `app/bundles/ApiBundle/`: switching the API on, authentication (Basic and OAuth2), the
conventions every v1 `/api/...` endpoint inherits from `CommonApiController`, the API Platform v2 layer at `/api/v2`, and
the inventory of all endpoints. What each resource does (fields, dedupe, side effects) belongs to its area skill; the
inventory links to it. Outgoing webhooks are in mautic-webhooks; Role and permission semantics are in
mautic-users-and-permissions.

## Expected behaviour (essentials)
Terms: a **Contact** is a tracked person (code `Lead`); a **User** is a Mautic login; **API Credentials** are OAuth2
clients; **v1** is the classic `/api/...` API, **v2** the API Platform one under `/api/v2`.

Enabling and authentication
- The API is off by default. While `api_enabled` is false every request whose URI contains `/api` or `/oauth` gets 403
  `type: api_disabled` before authentication. [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:36-68 @7.x]
- Basic Auth is separately off by default (`api_enable_basic_auth`). A `Basic` header while it is off gets 403
  `type: access_denied`. It uses a User's own username and password. [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:70-89 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#basic-authentication]
- OAuth2 clients created in the UI allow `authorization_code` and `refresh_token`. `client_credentials` is added only when
  the creating User is an admin. The `password` grant is never enabled. [code: app/bundles/ApiBundle/Controller/ClientController.php:207-211 @7.x]
  [code: app/bundles/ApiBundle/Entity/oAuth2/Client.php:58-61 @7.x]
- A client-credentials token acts as a pseudo User named `"<client name> [<id>]"` with the creating admin's role. It
  returns no refresh token. [code: app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php:43-95 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#client-credentials-flow]
- Authorizing a client in the browser flow requires `api:access:full`. [code: app/bundles/ApiBundle/EventListener/PreAuthorizationEventListener.php:38-66 @7.x]
- Access tokens last `api_oauth2_access_token_lifetime` minutes (60) and refresh tokens `api_oauth2_refresh_token_lifetime`
  days (14). [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:13-17 @7.x]
- The v1 firewall is stateless. The v2 firewall shares the UI session, so a logged-in browser can call `/api/v2`.
  [code: app/config/security.php:51-67 @7.x]
- No rate limiting exists in 7.x; `api_rate_limiter_cache` is gone. [code: app/config/security.php:105-108 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-rate-limiter-cache]

v1 conventions
- Lists return `{"total": N, "<plural>": {...}}`. The collection is an object keyed by entity id, not an array.
  [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:232-245 @7.x] [code: app/bundles/CoreBundle/Entity/CommonRepository.php:360-364 @7.x]
- `limit` defaults to 30 (`default_pagelimit`); `limit=0` means unlimited; there is no maximum. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1364-1373 @7.x]
- The published filter parameter is `published`, not `publishedOnly`. The search parameter is `search`, not `searchFilter`.
  [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:167,184 @7.x]
- `orderBy` takes database column names (snake_case). `minimal` switches to the `*List` serializer group.
  [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1381-1406 @7.x]
- `where[n][col|expr|val]` works on every list endpoint. Unknown `expr` values are ignored silently. A clause missing `col`
  or `expr` gives a 500. Clauses with an `internal` key are stripped. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1610-1706 @7.x]
  [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:253-260 @7.x]
- Without `<base>:viewother` a list shows only rows you created (Contacts: rows you own). [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:177-182 @7.x]
- Create is `POST /new` and returns 201 with a `Location` header; an `id` in the body is ignored. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:338-348,460-489 @7.x]
- PATCH `/{id}/edit` keeps omitted fields and returns 404 for a missing id. PUT `/{id}/edit` resets omitted fields. On a
  missing id PUT creates a new entity (201) with a new id. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:243-267,557 @7.x]
- Publish fields are silently dropped when the caller lacks publish permission. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:523-540 @7.x]
- Batch payloads are capped at `api_batch_max_limit` (200). The cap gives 400 for the whole request. Item failures are
  reported in `statusCodes` and `errors` while the response stays 201 or 200. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:728-736 @7.x]
  [code: app/bundles/ApiBundle/Controller/CommonApiController.php:169-331 @7.x]
- Batch delete takes ids in the query string (`?ids=1,2`). Delete responses return the deleted entity.
  [code: app/bundles/ApiBundle/Controller/CommonApiController.php:78-162 @7.x]
- Errors use `{"errors":[{"code","message","details","type"}]}`. OAuth errors are rewritten into the same envelope.
  [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:611-640 @7.x] [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:92-176 @7.x]
- Validation failures return 400, or 422 when a constraint cause carries 422. `details` maps field to messages.
  [code: app/bundles/ApiBundle/Controller/CommonApiController.php:605-617 @7.x]
- 409 "checked out" applies only to models implementing `ApiLockAwareInterface`. In 7.2.1 only Emails do. Contacts stay
  editable while open in the UI. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:491-520 @7.x]
  [code: app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php:20-116 @7.x]
- Every v1 response carries `Mautic-Version`. Dates are ISO-8601 UTC. Nulls are serialised unless `select` was used.
  [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:742-752 @7.x] [code: app/config/config.php:281-290 @7.x]

v2 (API Platform)
- v2 PUT replaces the whole resource. Omitted fields become null and a missing id gives 404. v2 PUT never creates.
  [code: app/bundles/ApiBundle/State/PutProcessor.php:27-97 @7.x]
- v2 validation errors are 400, never 422. PATCH needs `application/merge-patch+json`.
  [code: app/config/config.php:433-477 @7.x]
- v2 collections with `...own` security are filtered to the caller's rows. Item operations must pass `object` to the
  security expression; a meta-test enforces this. [code: app/bundles/ApiBundle/Extension/OwnershipScopedCollectionExtension.php:32-204 @7.x]
  [code: app/bundles/ApiBundle/Tests/Functional/OwnershipScopedSecurityMetadataTest.php @7.x]

## Where it lives
| Concern | Path |
|---|---|
| Base controllers | `app/bundles/ApiBundle/Controller/FetchCommonApiController.php`, `CommonApiController.php` |
| Resource controllers | `app/bundles/*/Controller/Api/*ApiController.php`, `plugins/*/Controller/Api/` |
| Route declaration / expansion | `routes.api` in each `Config/config.php`; `app/bundles/CoreBundle/EventListener/CoreSubscriber.php:114-302`; prefix in `CoreBundle/Loader/RouteLoader.php:58-67` |
| List filter engine | `app/bundles/CoreBundle/Entity/CommonRepository.php` (`where`, order, limit) |
| Request coercion | `app/bundles/CoreBundle/Form/RequestTrait.php:35-169` |
| OAuth2 entities / tables | `app/bundles/ApiBundle/Entity/oAuth2/` → `oauth2_clients`, `oauth2_accesstokens`, `oauth2_refreshtokens`, `oauth2_authcodes`, `oauth2_user_client_xref` |
| Guards and error rewriting | `app/bundles/ApiBundle/EventListener/ApiSubscriber.php` |
| Firewalls | `app/config/security.php` (`oauth2_token`, `oauth2_area`, `v2api`, `api`); OAuth server `app/config/security_api.php` |
| Serializer | `app/bundles/ApiBundle/Serializer/Driver/ApiMetadataDriver.php`, `Serializer/Exclusion/`; entity `loadApiMetadata()` |
| v2 glue | `app/bundles/ApiBundle/Security/Voter/ApiPermissionVoter.php`, `Extension/OwnershipScopedCollectionExtension.php`, `State/PutProcessor.php`, `ApiPlatform/EventListener/MauticWriteSubscriber.php`; config `app/config/config.php:410-478` |
| Events | `app/bundles/ApiBundle/ApiEvents.php`, `Event/ApiInitializeEvent.php` |
| Config parameters | `api_enabled`, `api_enable_basic_auth`, `api_oauth2_access_token_lifetime`, `api_oauth2_refresh_token_lifetime`, `api_batch_max_limit` (`app/bundles/ApiBundle/Config/config.php:62-68`); `default_pagelimit`, `max_entity_lock_time` |
| Permissions | `api:access:full`, `api:clients:*` (`app/bundles/ApiBundle/Security/Permissions/ApiPermissions.php`) |
| Credentials UI | `/s/credentials` → `app/bundles/ApiBundle/Controller/ClientController.php` |
| Tests | `app/bundles/ApiBundle/Tests/` |

Details and line numbers: `references/code-map.md`. [code: app/bundles/ApiBundle/Config/config.php:9-68 @7.x]

## How to change or extend it
Add a v1 resource (core bundle or plugin):
1. Give the entity a static `loadApiMetadata(ApiMetadataDriver $metadata)`. Call `setGroupPrefix('thing')`, then
   `addListProperties([...])` for list fields and `addProperties([...])` for detail fields.
   [code: app/bundles/ApiBundle/Serializer/Driver/ApiMetadataDriver.php:101-158 @7.x]
2. Extend `CommonApiController` (or `FetchCommonApiController` for read-only). In the constructor set `$this->model` (a
   `FormModel`), `$entityClass`, `$entityNameOne`, `$entityNameMulti` and `$serializerGroups` (`thingDetails`,
   `categoryList`, `publishDetails`...). Copy `WebhookApiController` as the minimal example.
   [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:143-155 @7.x] [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php @7.x]
3. Declare the route in `Config/config.php`:
   `'routes' => ['api' => ['mautic_api_thingsstandard' => ['standard_entity' => true, 'name' => 'things', 'path' => '/things', 'controller' => ThingApiController::class]]]`.
   Restrict verbs with `supported_endpoints`. Custom routes take `path`, `controller`, `method`.
   [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:123-194 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html]
4. Make the model's `getPermissionBase()` return your permission base. Without own/other levels, list filtering and
   `hasEntityAccess` behave as plain view/edit/delete. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:409-429 @7.x]
5. Override `prepareParametersForBinding`, `preSaveEntity`, `preSerializeEntity` or `getEntityFormOptions` for special
   fields. Do not reimplement `processForm`. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:376-460 @7.x]
6. Opt in to 409 locking by implementing `ApiLockAwareInterface` with `ApiEntityLockTrait` on the model.
   [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#enable-api-lock-for-a-model]

Add a v2 resource:
- Add `#[ApiResource]` with `GetCollection`, `Post`, `Get`, `Put`, `Patch`, `Delete`. Use groups `<name>:read` and
  `<name>:write`, and `#[Groups]` on properties.
- Use `security: "is_granted('bundle:name:viewown', object)"` on item operations so the voter and the ownership
  extension apply.
- Mark child-to-parent associations `->isOwnershipParent()`.
[code: app/bundles/WebhookBundle/Entity/Webhook.php:28-50 @7.x] [code: app/bundles/ApiBundle/Extension/OwnershipScopedCollectionExtension.php:32-204 @7.x]

Hook in without subclassing:
- `ApiEvents::API_ON_ENTITY_PRE_SAVE`/`POST_SAVE`: validate or enrich v1 writes. Throw to abort with a code.
- `ApiInitializeEvent`, `API_PRE/POST_SERIALIZATION_CONTEXT`: change serializer groups.
- `API_PLATFORM_PERMISSION_CONTEXT`: rewrite v2 permission strings.
[code: app/bundles/ApiBundle/ApiEvents.php:52-88 @7.x]

Update together: entity, migration, `loadApiMetadata` (use `setSinceVersion` for new fields), form type (v1 writes go
through it), `#[Groups]` for v2, translations for error messages, the area skill's docs. Keep v1 envelopes, keys and
status codes stable: external clients and `mautic/api-library` depend on them. [code: app/bundles/ApiBundle/Serializer/Driver/ApiMetadataDriver.php:101-158 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#mautic-api-library]
For 8.x compatibility, subscribe by event class where 8.x provides one (see Version notes).

## How to test it
- Base class `Mautic\CoreBundle\Test\MauticMysqlTestCase`. It enables `api_enabled` and Basic Auth and logs `admin` in.
  Set `$authenticateApi = true` to send Basic credentials `admin`/`Maut1cR0cks!`.
  [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:47-63,117 @7.x] [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:57-58 @7.x]
- Copy from: `ApiBundle/Tests/Functional/Oauth2Test.php` (OAuth), `ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php`
  (locking and per-user permissions), `ApiBundle/Tests/Functional/Serializer/PutOperationTest.php` (v2),
  `AssetBundle/Tests/Functional/ApiPlatform/DownloadOwnershipApiV2AuthorizationRegressionTest.php` (v2 own/other via
  `OwnershipScopedApiAuthorizationTestBase`), `ApiBundle/Tests/Controller/CommonApiControllerTest.php` (`where`).
  [code: app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php:33-183 @7.x]
- A good regression test asserts the exact status code (200 vs 201), the envelope key, `errors[0].code`/`details`, the
  database state after reload, and own/other boundaries on both v1 and v2. Skeletons: `references/test-patterns.md`.

## Version notes
- Before 7: an API rate limiter existed (`api_rate_limiter_cache`). Before 5: `app/config/local.php`.
  Legacy lifetimes were stored in seconds. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-rate-limiter-cache]
  [code: app/bundles/ConfigBundle/Form/Type/ConfigType.php:27-37 @7.x]
- 5.x: the OAuth server fork moved to Twig and the credentials UI to Twig (5.0) [PR #12091] [PR #11853]; 5.0.3 fixed empty
  API objects on Composer installs [PR #13272]; 5.1 added `ApiSerializationContextEvent` [PR #12734]; 5.2.7 applies
  every item when a batch edits one entity twice [PR #14928].
- 6.0: `where[...][val]` is no longer HTML-entity encoded, so values with `'` match [PR #14550].
- 7.0 removed the rate limiter and moved OAuth to `klapaudius/oauth-server-bundle` [PR #14876] [PR #15436]. 7.1 added 409
  locking [PR #15299]. 7.1.2 added v2 ownership scoping and 7.1.3 user-bound bearer tokens on v2 [PR #16175] [PR #16245].
- 7.x: API Platform v2 at `/api/v2`. 7.2 deprecates the `mautic.api.oauth.event_listener` alias. The 7.x branch after 7.2.1 adds
  `POST /api/companies/batch/addcontacts` and legacy `/api/projects` (unreleased; [PR #16512] [PR #15569]). [code: app/bundles/ApiBundle/Config/services.php:29-31 @7.x]
  [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:122-124 @7.x]
- 8.x:
  - The `ApiEvents` class is removed. Subscribe to `PreSaveApiEntityEvent`, `PostSaveApiEntityEvent`,
    `Pre/PostSerializationContextEvent`, `ApiPlatformPermissionContextEvent`, `ClientPostSaveEvent` or
    `ClientPostDeleteEvent`. [PR #17217] [PR #17654]
  - `CommonApiController` and `FetchCommonApiController` get typed signatures and `protected` helpers.
    [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
  - Core `/api` routes move to `#[Route]` attributes. Plugins keep `routes.api`. [PR #17169]
  - API Platform goes to 4.3 and the OAuth server bundle to 6.0. [PR #17355] [PR #17342]
  - `formType` leaves the Forms API. [PR #17082]
  - 7.x-only endpoints (unreleased, after 7.2.1) arrive with the next forward merge. [PR #17253]
- Full detail: `references/version-notes.md`.

## Pitfalls
- v2 ownership scoping (the collection extension and the owner-aware voter) shipped in the 7.1.2 security release. Upgrade
  to 7.1.2 or later before exposing v2, and test own/other boundaries on both APIs [PR #16175] [PR #16181].
- Changing a response's JSON type (`{}` to `[]`, string to int) is a BC break, even when it fixes a 500. Keep shapes
  stable for `mautic/api-library` and external clients [PR #10724] [PR #7815] [PR #10065].
- The API has broken twice on Composer installs without a lock file (JMS serializer, OAuth bundle). Test API changes on a
  recommended-project install as well as a git checkout [PR #13272] [PR #15436].
- `publishedOnly` and `searchFilter` in the docs are PHP-library argument names. Over HTTP use `published` and `search`;
  `publishedOnly` is silently ignored. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:167 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html#list-assets]
- Clients that expect a JSON array break on lists: collections are id-keyed objects, and an empty list may be `[]` or `{}`.
  [code: app/bundles/ApiBundle/Helper/EntityResultHelper.php:29-32 @7.x]
- v1 PUT on a missing id creates a new entity with a new id, not the one in the URL. v2 PUT returns 404.
  [code: app/bundles/ApiBundle/Controller/CommonApiController.php:243-267 @7.x] [code: app/bundles/ApiBundle/State/PutProcessor.php:27-97 @7.x]
- A batch with failed items still returns 201 or 200. Check `statusCodes` per item.
  [code: app/bundles/ApiBundle/Controller/CommonApiController.php:274-331 @7.x]
- Error shapes differ from the devdocs. The docs show `{"error":{...}}`; the code returns `{"errors":[...]}`. One
  exception: SMS send without a transport returns `{"error":...}` with HTTP 200. Stats errors also come back with HTTP 200.
  [code: app/bundles/SmsBundle/Controller/Api/SmsApiController.php:66-70 @7.x] [code: app/bundles/CoreBundle/Controller/Api/StatsApiController.php:49-56 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#error-handling]
- A malformed `where` clause gives a 500, not a 400. A misspelt `expr` silently returns unfiltered rows.
  [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1610-1706 @7.x]
- `client_credentials` is added only when an admin creates the client; the client then carries that admin's role.
  [code: app/bundles/ApiBundle/Controller/ClientController.php:207-211 @7.x]
- v2 accepts the UI session cookie because its firewall is not stateless. Consider CSRF when exposing it (open question).
  [code: app/config/security.php:51-59 @7.x]
- `GET /api/v2/categories` has no security expression. [code: app/bundles/CategoryBundle/Entity/Category.php:23-26 @7.x]
- `MauticDenyAccessListener` is not registered, so only the voter path dispatches the permission-context event.
  The devdocs say both paths do. [code: app/bundles/ApiBundle/ApiPlatform/EventListener/MauticDenyAccessListener.php:35-80 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#api-permission-context-event]
- `ApiEvents::CLIENT_PRE_SAVE` and `BUILD_ROUTE` are never dispatched. Subscribing to them does nothing.
  [code: app/bundles/ApiBundle/Model/ClientModel.php:101-129 @7.x]
- Docs errors confirmed against code (details in `references/endpoint-inventory.md` section 6):
  - User delete is `DELETE /api/users/{id}/delete`.
  - Campaign export is GET.
  - Stats `limit` defaults to 100.
  [code: app/bundles/UserBundle/Config/config.php:79-84 @7.x]
- Open questions:
  - The v2 page size is not configured, so API Platform's default applies (not verified against the vendor version).
  - `api_included` in the v2 normalization contexts is read by no PHP code. [unverified]
  - `/api/files/*` and `/api/data/*` have no controller-level permission check. Confirm whether this is intended.
  [code: app/config/config.php:410-478 @7.x] [code: app/bundles/CoreBundle/Controller/Api/FileApiController.php:59-125 @7.x]

## Related skills
- mautic-contacts: `/api/contacts`, `/companies`, `/fields`, `/notes`, `/devices`, `/tags`, DNC, UTM, dedupe and `overwriteWithBlank`.
- mautic-segments: `/api/segments` (`list`/`lists` keys), membership add/remove, filter JSON.
- mautic-campaigns: `/api/campaigns`, events, event logs, clone, export/import, contact membership.
- mautic-emails: `/api/emails`, send endpoints, `sendToDnc`, the only API-locked entity.
- mautic-forms: `/api/forms`, fields/actions delete, submissions.
- mautic-pages-and-tracking: `/api/pages`, `/api/dynamiccontents`, public `/dwc` endpoints.
- mautic-assets-categories-projects: `/api/assets` (with `/api/files/assets` upload), `/api/categories`, `/api/projects`.
- mautic-points-and-stages: `/api/points*`, point groups and insights, contact point adjustments, `/api/stages`.
- mautic-reports-and-dashboard: `/api/reports/{id}` data and `/api/data` widgets.
- mautic-channels: `/api/smses`, `/api/notifications`, `/api/messages`, `/api/focus`, `/api/tweets`.
- mautic-users-and-permissions: `/api/users`, `/api/roles`, permission strings, `users/self`, `permissioncheck`.
- mautic-webhooks: `/api/hooks`, `/api/v2/webhooks` and outgoing webhook delivery.
- mautic-configuration: where `api_*` parameters are set and how `config/local.php` and env vars interact.
- mautic-plugin-development: plugin bundle structure, `Config/config.php`, services, when adding API routes to a plugin.
- mautic-testing: test harness, database reset, fixtures, running PHPUnit.
- mautic-upgrades-and-versions: porting API code to 8.x and release history.

## Reference files
- `references/behaviour.md`: the numbered behaviour specification (R1–R104) plus docs-versus-code discrepancies. Open it
  before asserting any API behaviour in a test.
- `references/endpoint-inventory.md`: every v1, v2 and OAuth endpoint with method, path, permission, owning skill and
  citation. Open it to find an endpoint or its owner.
- `references/code-map.md`: classes, tables, events, firewalls, parameters, permissions and tests with line numbers.
- `references/docs-digest.md`: what devdocs and user docs say (authentication procedures, conventions, 8.0 changes, gaps).
- `references/test-patterns.md`: base classes, auth in tests, representative tests and v1/v2 skeletons.
- `references/version-notes.md`: history, 7.x minors and the 8.x delta for the API framework.
- `references/pr-history.md`: why and when API behaviour changed: decisions, a regression catalogue, a feature timeline and
  removals from the merged API PRs.
