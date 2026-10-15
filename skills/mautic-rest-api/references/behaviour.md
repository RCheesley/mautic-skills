# REST API framework: behaviour specification (Mautic 7.x)

Numbered rules for the framework shared by every endpoint. Resource-specific rules (contact dedupe, `overwriteWithBlank`,
`sendToDnc`, Segment filters and so on) are in the owning area skill; the few summarised here are marked "summary".
Code wins over docs where they disagree; each disagreement is listed in section 13.

## Contents
1. Enabling the API and request classification (R1–R6)
2. Authentication: Basic and OAuth2 (R7–R22)
3. Routing conventions (R23–R29)
4. List endpoints (R30–R42)
5. Single read, create and edit (R43–R55)
6. Batch endpoints (R56–R62)
7. Delete (R63–R65)
8. Errors and status codes (R66–R74)
9. Serialization and response shape (R75–R82)
10. Locking (R83–R86)
11. Rate limiting, versions and headers (R87–R90)
12. API Platform v2 (R91–R104)
13. Docs-versus-code discrepancies (D1–D12)

## 1. Enabling the API and request classification

R1. A request is an "API request" when its URI contains `/api` or `/oauth`.
[code: app/bundles/ApiBundle/Helper/RequestHelper.php:16-26 @7.x]

R2. `api_enabled` defaults to `false`. While it is false every API request gets HTTP 403 with body
`{"errors":[{"message":"API disabled. ...","code":403,"type":"api_disabled"}]}` before authentication runs.
[code: app/bundles/ApiBundle/Config/config.php:62-68 @7.x] [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:36-68 @7.x]
[code: app/bundles/ApiBundle/Tests/EventListener/ApiSubscriberTest.php:62-93 @7.x]

R3. While `api_enabled` is false every `api:*` permission evaluates to 0, the API permission block is hidden from the Role
editor, and the "API Credentials" menu item is hidden.
[code: app/bundles/ApiBundle/Security/Permissions/ApiPermissions.php:50-63 @7.x] [code: app/bundles/ApiBundle/Config/config.php:43-60 @7.x]

R4. Turn the API on in Configuration > API Settings or with `'api_enabled' => 1` in `config/local.php`
(`app/config/local.php` before Mautic 5). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html]
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#api-settings]

R5. `api_enable_basic_auth` defaults to `false`. A request whose `Authorization` header starts with `Basic` while it is
false gets 403 `{"errors":[{"message":"Basic Auth disabled. ...","code":403,"type":"access_denied"}]}`. The value is cast
to bool when the configuration is saved. [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:70-89 @7.x]
[code: app/bundles/ApiBundle/EventListener/ConfigSubscriber.php:32-40 @7.x]

R6. `/api/*` requires `IS_AUTHENTICATED_FULLY`. [code: app/config/security.php:153 @7.x]

## 2. Authentication: Basic and OAuth2

R7. The v1 `api` firewall (`^/api/`) is stateless and accepts, in order, an OAuth2 bearer token (`fos_oauth`), plugin
authentication (`mautic_plugin_auth`), and HTTP Basic. [code: app/config/security.php:60-67 @7.x]

R8. The v2 `v2api` firewall (`^/api/v2`) has the same authenticators but is not stateless and shares the `mautic` session
context, so a logged-in UI session cookie authenticates v2 calls. [code: app/config/security.php:51-59 @7.x]

R9. Basic Auth uses a Mautic User's own username and password, base64-encoded as `user:password`. Mautic recommends
OAuth2 and Basic Auth only over HTTPS. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#basic-authentication]
[docs: https://docs.mautic.org/en/7.2/configuration/settings.html#api-settings]

R10. The token endpoint is `/oauth/v2/token`, accepts GET or POST, and sits behind a firewall with `security: false`.
[code: app/bundles/ApiBundle/Config/config.php:9-13 @7.x] [code: app/config/security.php:38-41 @7.x]

R11. A client created in the UI allows the `authorization_code` and `refresh_token` grants. If the creating User's role
is admin, `client_credentials` is added. The client stores the creator's role. The `password` grant is never enabled.
[code: app/bundles/ApiBundle/Entity/oAuth2/Client.php:58-61 @7.x] [code: app/bundles/ApiBundle/Controller/ClientController.php:207-211 @7.x]

R12. A `client_credentials` access token has no user (`oauth2_accesstokens.user_id` is null). On each request Mautic
builds a transient User carrying the client's stored role, named `"<client name> [<client id>]"`; permissions are that
role's, and audit-log and `createdByUser` entries show that name.
[code: app/bundles/ApiBundle/Entity/oAuth2/AccessToken.php:14-47 @7.x]
[code: app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php:43-46,68-95 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#oauth2]

R13. A client-credentials token response contains no refresh token.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#client-credentials-flow]

R14. Authorization-code flow: `/oauth/v2/authorize` needs an authenticated session; unauthenticated GET or POST redirects
(302) to `/oauth/v2/authorize_login`. [code: app/bundles/ApiBundle/Controller/oAuth2/AuthorizeController.php:46-54 @7.x]
[code: app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php:33-56 @7.x]

R15. The authorizing User must hold `api:access:full`, otherwise access is denied. A client already in the User's
authorized list skips the consent screen; after consent the User is added to `oauth2_user_client_xref`.
[code: app/bundles/ApiBundle/EventListener/PreAuthorizationEventListener.php:38-66 @7.x]

R16. With the authorization-code flow, actions are recorded as the authorizing User.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#oauth2]

R17. Access tokens live `api_oauth2_access_token_lifetime` minutes (default 60) and refresh tokens
`api_oauth2_refresh_token_lifetime` days (default 14). The values are converted to seconds in the env vars
`MAUTIC_API_OAUTH2_ACCESS_TOKEN_LIFETIME` and `MAUTIC_API_OAUTH2_REFRESH_TOKEN_LIFETIME`; a non-integer falls back to
3600 s and 1 209 600 s. [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:13-17 @7.x]
[code: app/config/security_api.php:9-16 @7.x]

R18. The configuration form shows a legacy stored value of 3600 (access) as 60, and 1209600 (refresh) as 14.
[code: app/bundles/ConfigBundle/Form/Type/ConfigType.php:27-37 @7.x]

R19. A refresh inside the refresh-token lifetime returns a new access token and a new refresh token. When the refresh
token has expired the token endpoint returns 400 and the app must restart authorization.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#refreshing-tokens]

R20. Redirect URIs are mandatory for a client and each must match `~^[0-9a-z].*://(.*?)(:[0-9]+)?(/?|/\S+)$~ixu`; the
form field takes a comma-separated string. [code: app/bundles/ApiBundle/Entity/oAuth2/Client.php:44-45 @7.x]
[code: app/bundles/ApiBundle/Form/Validator/Constraints/OAuthCallbackValidator.php:13-38 @7.x]

R21. Deleting a client cascades at database level to its access tokens, refresh tokens, auth codes and User
authorizations. [code: app/bundles/ApiBundle/Entity/oAuth2/AccessToken.php:27-29 @7.x]
[code: app/bundles/ApiBundle/Entity/oAuth2/Client.php:77-82 @7.x]

R22. Saving a client writes an audit-log entry (bundle `api`, object `client`) only when `name` or `redirectUris`
changed; deleting always logs. The generated client id and secret are shown once in a flash message after creation.
[code: app/bundles/ApiBundle/EventListener/ClientSubscriber.php:32-65 @7.x]
[code: app/bundles/ApiBundle/Controller/ClientController.php:212-225 @7.x]

Send tokens as `Authorization: Bearer <token>`. The alternative is `access_token` in a form-encoded POST body. Do not put
tokens in query strings. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#authenticating-the-api-request]

## 3. Routing conventions

R23. v1 routes come from each bundle's `Config/config.php` `routes.api` block and get the `/api` prefix. No version
segment exists in v1 URLs. [code: app/bundles/CoreBundle/Loader/RouteLoader.php:58-67 @7.x]

R24. `standard_entity => true` expands to ten routes: GET list, GET `/{id}`, POST `/new`, POST `/batch/new`, PUT and
PATCH `/batch/edit`, PUT and PATCH `/{id}/edit`, DELETE `/batch/delete`, DELETE `/{id}/delete`, named
`mautic_api_<name>_<std>`. `supported_endpoints` restricts the set.
[code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:123-194 @7.x]

R25. `_format` defaults to `json` and FOS REST has only the `json` view format, so responses are always JSON.
[code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:255-259 @7.x] [code: app/config/config.php:267-278 @7.x]

R26. The FOS REST body listener is on, so a JSON request body is decoded into request parameters; form-encoded bodies
also work. [code: app/config/config.php:269 @7.x]

R27. A route's HTTP method defaults to GET. [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:263-265 @7.x]

R28. `{id}` and every `{...Id}` placeholder are constrained to `\d+`, so a non-numeric id gets a routing 404.
[code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:288-302 @7.x]

R29. The legacy constant `ApiEvents::BUILD_ROUTE` is never dispatched; API routes are built through
`CoreEvents::BUILD_ROUTE` with type `api`. [code: app/bundles/CoreBundle/Loader/RouteLoader.php:58-60 @7.x]

## 4. List endpoints

R30. `GET /api/<resource>` returns `{"total": <int>, "<entityNameMulti>": {...}}`. `total` counts all matching rows and
ignores `start`/`limit`. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:232-245 @7.x]

R31. The collection is a JSON object keyed by entity id, because the repository indexes results by id. An empty result
is `[]` when it came from a Paginator and `{}` otherwise.
[code: app/bundles/CoreBundle/Entity/CommonRepository.php:360-364,398-405 @7.x]
[code: app/bundles/ApiBundle/Helper/EntityResultHelper.php:29-32,82-85 @7.x]

R32. `start` is the offset (default 0). `limit` defaults to `default_pagelimit` (30). `limit=0` or an empty value means
no limit. No maximum is enforced. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:163-232 @7.x]
[code: app/bundles/CoreBundle/Config/config.php:285 @7.x] [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1364-1373 @7.x]

R33. `search` takes a Mautic search string, for example `is:published`, or a search command.
[code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:163-232 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#query-parameters]

R34. `orderBy` takes a comma list of columns; a column without a dot is prefixed with the repository alias. `orderByDir`
defaults to `ASC` and is sanitised. Use database column names (snake_case), not property names.
[code: app/bundles/CoreBundle/Entity/CommonRepository.php:1381-1406 @7.x]
[code: app/bundles/ApiBundle/Tests/Controller/CommonApiControllerTest.php:28-62 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#list-segments]

R35. `order[n][col]` / `order[n][dir]` override `orderBy`/`orderByDir` when present; otherwise `orderBy` applies;
otherwise the repository's default order. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1381-1420 @7.x]

R36. The published filter is read from the query parameter `published`. A truthy value adds `isPublished = true`.
`publishedOnly` (the name in most docs pages and in the PHP library) is not read by the base controller.
[code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:167,184 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html#list-campaigns]

R37. A truthy `minimal` swaps the first serializer group from `*Details` to `*List`, which drops nested lists.
[code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:163-232 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html#list-assets]

R38. `select[]` selects specific columns and turns off null serialisation, so null values are omitted. On Contacts,
`id` is mandatory in `select`. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:163-232 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#list-contacts]

R39. `where[n][col]`, `where[n][expr]`, `where[n][val]` filter the list (`column`/`value` are accepted aliases). Allowed
`expr`: `eq, neq, lt, lte, gt, gte, like, notLike, in, notIn, between, notBetween` (take a value), `isNull, isNotNull,
isEmpty, isNotEmpty` (column only), and `andX, orX` (whose `val` is a nested array of clauses). Columns without a dot get
the repository alias. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1007-1030,1610-1706 @7.x]
[code: app/bundles/ApiBundle/Tests/Controller/CommonApiControllerTest.php:63-246 @7.x]

R40. `in`/`notIn` take a CSV string (`"a,b"`); a single value degrades to `eq`/`neq`. `between` needs a two-element
array. An unknown `expr` is silently ignored. A clause missing `expr` or `col` throws `InvalidArgumentException`, which
surfaces as a 500. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:1610-1706 @7.x]

R41. Any `where` clause carrying an `internal` key is stripped from the request, recursively inside `andX`/`orX`; the key
is reserved for server-side formula clauses. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:253-260,645-654 @7.x]

R42. A caller without `<base>:viewother` sees only rows they created. Contacts override this to
`owner_id = me OR (owner_id IS NULL AND created_by = me)`.
[code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:177-182,775-782 @7.x]
[code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:137-160 @7.x]

## 5. Single read, create and edit

R43. `GET /api/<resource>/{id}` returns `{"<entityNameOne>": {...}}`. A missing entity returns 404
`{"errors":[{"message":"Item was not found.","code":404,"details":[],"type":null}]}`; a failed access check returns 403.
[code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:307-335,379-382,555-558,611-640 @7.x]

R44. Item access uses `hasEntityAccess(<base>:<action>own, <base>:<action>other, owner)`, where owner is
`getPermissionUser()` when the entity has it and `getCreatedBy()` otherwise. Create uses `isGranted(<base>:create)`.
Publish changes use `hasPublishAccessForEntity`. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:409-429 @7.x]

R45. `POST /api/<resource>/new` takes form fields in the body (JSON or form-encoded) and returns 201
`{"<entityNameOne>": {...}}` with a `Location` header pointing at the GET route.
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:338-348,577-587 @7.x]

R46. On create, an `id` in the payload is ignored. Doctrine-mapped defaults are merged under the posted values so
validation sees every property. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:460-489 @7.x]

R47. `category` may be passed as a Category id and is resolved to the entity. An unknown id raises
`UnexpectedValueException`, which surfaces as a 500. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:635-646 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/categories.html#assign-a-category]

R48. PUT and PATCH both target `/{id}/edit` and both need `<base>:editown`/`editother` on an existing entity.
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:243-267 @7.x]

R49. PATCH requires the entity to exist (404 otherwise) and submits the form with `clearMissing = false`: omitted fields
keep their values. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:243-267,557 @7.x]

R50. PUT submits with `clearMissing = true`: omitted fields are reset to the form's empty value. If `{id}` does not
exist, PUT creates a new entity (needs `<base>:create`) and returns 201; the new entity gets a new auto-increment id, not
`{id}`. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:243-267,557 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#edit-company]

R51. `isPublished`, `publishUp` and `publishDown` are silently dropped when the caller lacks publish permission for the
entity; on create the entity is forced to unpublished. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:523-540 @7.x]

R52. Before binding, request values are coerced: boolean form types accept `on/off/true/false/1/0`; multi-select values
may be `a|b` pipe strings; date and time fields are parsed with `strtotime` and normalised to `Y-m-d H:i:s`, `Y-m-d` or
`H:i:s`; zero dates such as `0000-00-00` are dropped; `HtmlType` fields are cleaned with the `html` mask and
`description` with `strict_html`; everything passes through `InputHelper::_`.
[code: app/bundles/CoreBundle/Form/RequestTrait.php:35-169 @7.x]

R53. `API_ON_ENTITY_PRE_SAVE` is dispatched after the form validates and before `saveEntity`; `API_ON_ENTITY_POST_SAVE`
after saving. A listener that throws aborts the request with the exception's message and code. No core listener exists.
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:567-595 @7.x] [code: app/bundles/ApiBundle/ApiEvents.php:52,61 @7.x]

R54. A successful edit returns 200 `{"<entityNameOne>": {...}}`; a PUT that created returns 201.
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:243-267 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#edit-company]

R55. Summary (owned by mautic-contacts): for Contacts and Companies, PUT overwrites custom fields including blanks; POST
and PATCH ignore blank values unless the body has a truthy `overwriteWithBlank`; `POST /contacts/new` deduplicates on
unique identifier fields and returns 200 when it updated an existing Contact.
[code: app/bundles/LeadBundle/Controller/Api/CustomFieldsApiControllerTrait.php:175-210 @7.x]
[code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:579-740 @7.x]

## 6. Batch endpoints

R56. Every `/batch/*` payload is capped at `api_batch_max_limit` items (default 200). Exceeding it returns 400 with
"A max of %limit% entities are supported at a time." The parameter is not in the configuration UI.
[code: app/bundles/ApiBundle/Config/config.php:62-68 @7.x] [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:728-736 @7.x]

R57. `POST /batch/new` takes a list or map of entity payloads. `<base>:create` is checked once up front. Each item is
processed like a POST, except when `getNewEntity()` resolves an existing entity (Contacts and Companies deduplicate on
unique fields): then the item is treated as PATCH, needs edit access, and its status is 200.
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:274-331,412-450 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#create-batch-companies]

R58. Batch create returns 201 with `{"<multi>": [...], "statusCodes": [...], "errors": {<index>: {...}}}`; items keep the
keys of the request; `errors` appears only when an item failed. A batch with failed items still returns 201.
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:274-331 @7.x]

R59. Entities are detached from the EntityManager after each batch item, so memory does not grow with the batch.
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:651-654 @7.x]

R60. `PUT|PATCH /batch/edit`: each item must carry `id`, else that item gets 400 "ID is missing from the payload.". PATCH
on a missing id gives a 404 item error; PUT on a missing id creates the entity (needs create permission, status 201).
The response is 200 with `statusCodes` and, when needed, `errors`.
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:169-234 @7.x]

R61. Batch id payloads are accepted as `{"ids":[1,2]}`, `{"ids":"1,2"}`, `[1,2]` or `[{"id":1,...},...]`; the response
mirrors the request keys. [code: app/bundles/ApiBundle/Helper/BatchIdToEntityHelper.php:54-154 @7.x]
[code: app/bundles/ApiBundle/Tests/Helper/BatchIdToEntityHelperTest.php @7.x]

R62. Batch item errors have the shape `{"message","code","type":"api"}`.
[code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:661-673 @7.x]

## 7. Delete

R63. `DELETE /{id}/delete` returns 200 with the deleted entity's data. A dependency conflict
(`DeleteEntityDependencyException`) returns the exception's code with message "Entity with ID %id% is currently in use by
other entities…". [code: app/bundles/ApiBundle/Controller/CommonApiController.php:137-162 @7.x]
[code: app/bundles/ApiBundle/Translations/en_US/validators.ini:4 @7.x]

R64. `DELETE /batch/delete?ids=1,2,3` takes ids in the query string, not the body. It serialises the entities before
deleting so the response still carries their ids, then deletes; 404, 403 and dependency errors are reported per item
(dependency errors carry the dependency list in `details`).
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:78-128 @7.x]

R65. Summary (owned by mautic-contacts): deleting a custom field used by a Segment filter returns 409.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/fields.html#delete-field]

## 8. Errors and status codes

R66. Controller errors use `{"errors":[{"code":<int>,"message":<string>,"details":<array|object>,"type":null}]}`.
Messages are translated from the `flashes`, then `messages` domains.
[code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:611-640 @7.x]

R67. FOS OAuth error bodies `{"error":"...","error_description":"..."}` are rewritten on the way out into the same
`errors` envelope, keeping the HTTP status and putting the OAuth error code in `type`. `access_denied` becomes "API
authorization denied." or, with Basic Auth, "Authorization denied, invalid credentials.".
[code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:92-176 @7.x]

R68. Examples asserted by tests: invalid client → 400
`{"errors":[{"message":"The client credentials are invalid","code":400,"type":"invalid_client"}]}`; invalid token → 401
`{"errors":[{"message":"The access token provided is invalid.","code":401,"type":"invalid_grant"}]}`.
[code: app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php:58-101 @7.x]

R69. A validation failure returns 422 if any form error's cause has code 422, otherwise 400. `details` is
`{field: [messages]}` and `message` is the first error (or "mautic.core.error.badrequest").
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:605-617 @7.x]
[code: app/bundles/CoreBundle/Controller/FormErrorMessagesTrait.php:64-74 @7.x]

R70. Status codes used by the v1 framework: 200 read/edit/delete/actions, 201 create and PUT-create, 400 validation or
bad batch, 401 bad token, 403 API disabled / Basic disabled / permission denied, 404 not found, 409 locked or entity in
use, 422 validation with a 422 cause, 500 uncaught exceptions. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:137-348,491-617 @7.x]
[code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:36-176 @7.x]

R71. `GET /api/smses/{id}/contact/{contactId}/send` returns a singular `{"error":{"message":"SMS transport is
disabled.","code":417}}` body with HTTP 200 when no SMS transport is enabled.
[code: app/bundles/SmsBundle/Controller/Api/SmsApiController.php:66-70 @7.x]

R72. `GET /api/stats/{table}` returns exceptions as `{"errors":[{"message","code"}]}` with HTTP 200.
[code: app/bundles/CoreBundle/Controller/Api/StatsApiController.php:49-56 @7.x]

R73. API Platform (v2) maps validation errors to 400 (not 422), optimistic-lock errors to 409, access denied to 403, and
serializer errors to 400, returned as `application/problem+json`, JSON-LD or JSON:API.
[code: app/config/config.php:461-477 @7.x]

R74. The devdocs "Error handling" section shows `{"error":{"message","code"}}` for system errors; the framework actually
returns the `errors` array (R66), except for the SMS case in R71.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#error-handling]

## 9. Serialization and response shape

R75. v1 responses are serialised with JMS. The serializer groups come from the controller's `$serializerGroups`; for
example Contacts use `leadDetails, frequencyRulesList, doNotContactList, userList, stageList, publishDetails, ipAddress,
tagList, utmtagsList`. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:678-721 @7.x]
[code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:88 @7.x]

R76. An entity declares its API fields in a static `loadApiMetadata(ApiMetadataDriver)`. `setGroupPrefix('x')` plus
`addProperties()` puts fields in `xDetails`; `addListProperties()` also puts them in `xList`. `setSinceVersion`,
`setUntilVersion`, `setSerializedName` and `setMaxDepth` are supported.
[code: app/bundles/ApiBundle/Serializer/Driver/ApiMetadataDriver.php:27-42,101-158,236-242 @7.x]

R77. `PublishDetailsExclusionStrategy` hides `isPublished, dateAdded, createdBy, dateModified, modifiedBy, checkedOut,
checkedOutBy` on nested entities (depth > 1). `ParentChildrenExclusionStrategy` hides `parent` and `children` beyond
depth 3. [code: app/bundles/ApiBundle/Serializer/Exclusion/PublishDetailsExclusionStrategy.php:13-26 @7.x]
[code: app/bundles/ApiBundle/Serializer/Exclusion/ParentChildrenExclusionStrategy.php:13-22 @7.x]

R78. Null values are serialised as `"key": null` unless `select` was used. Property names are the PHP property names in
camelCase. [code: app/config/config.php:286-290,314-317 @7.x]

R79. Dates are ISO-8601 in UTC, for example `"2017-06-19T09:31:18+00:00"`. [code: app/config/config.php:281-286 @7.x]

R80. `ApiInitializeEvent` (dispatched by class name in the controller constructor) and `API_PRE_SERIALIZATION_CONTEXT` /
`API_POST_SERIALIZATION_CONTEXT` let a plugin change groups, exclusion strategies or the JMS context of any v1
controller. No core listener exists. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:147-155,682-718 @7.x]

R81. Response keys are the controller's `entityNameOne`/`entityNameMulti`; several differ from the URL: Segments use
`list`/`lists`, Webhooks `hook`/`hooks`, Text Messages `sms`/`smses`, Focus Items `focus`/`focus`.
[code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:55-56 @7.x]
[code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php:48-49 @7.x]
[code: plugins/MauticFocusBundle/Controller/Api/FocusApiController.php:47-48 @7.x]

R82. `GET /api/users/self` returns the current User (for client-credentials tokens, the pseudo user) unwrapped, not
under a `user` key. [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:64-70 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#get-current-user]

## 10. Locking

R83. A model opts in to API locking by implementing `ApiLockAwareInterface` (with `ApiEntityLockTrait`, which delegates
to `FormModel::isLocked()`). Only `EmailModel` implements it in 7.2.1.
[code: app/bundles/ApiBundle/Model/ApiLockAwareInterface.php @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php @7.x]

R84. When such an entity is checked out by another User and the lock is younger than `max_entity_lock_time`, PUT and PATCH
return 409 with message "%name% is currently checked out by %user% (on %date% at %time%)" and `details`
`{checkedOutBy, checkedOut: "Y-m-d H:i:s T"}`. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:491-520 @7.x]
[code: app/bundles/CoreBundle/Model/FormModel.php:47-73 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#error-message]

R85. In batch edits a locked item gets code 409 in `statusCodes`/`errors`; the rest of the batch proceeds.
[code: app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php:81-116 @7.x]

R86. Contacts (and every other non-opted-in entity) stay editable through the API while a User has them open in the UI.
[code: app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php:62-80 @7.x]

## 11. Rate limiting, versions and headers

R87. No rate limiter exists in 7.2.1: no `RateLimiter` or `rate_limit` code in `app/` or `plugins/`. The only throttling
is `login_throttling` on the UI firewall, which does not apply to `/api`.
[code: app/config/security.php:105-108 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-rate-limiter-cache]

R88. The `api_rate_limiter_cache` setting used before Mautic 7 is gone.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-rate-limiter-cache]

R89. Every v1 response carries `Mautic-Version: <app version>` (since 2.4.0); dev builds add a suffix such as `-dev`.
[code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:742-752 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#mautic-version-verification]

R90. OAuth2 scopes are not used: `supported_scopes` is commented out in the server configuration.
[code: app/config/security_api.php:12 @7.x]

## 12. API Platform v2

R91. v2 routes are imported with the prefix `/api/v2/`. Resources are declared with `#[ApiResource]` on entities.
OpenAPI, Swagger UI and ReDoc are enabled; `/api/v2/docs` exists and opening `/api/v2` while logged in shows interactive
docs. [code: app/config/routing.php:10-12 @7.x] [code: app/config/config.php:410-421 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/api_v2.html]

R92. Formats: `jsonld` (`application/ld+json`), `json`, `jsonapi`, `html`. PATCH needs `application/merge-patch+json` or
`application/vnd.api+json`. Collections in JSON-LD contain `member`.
[code: app/config/config.php:433-452 @7.x] [code: app/bundles/ApiBundle/Tests/Functional/Serializer/PutOperationTest.php:64-72 @7.x]

R93. Pagination is on by default; Mautic does not configure the page size, so API Platform's default applies. Tests page
with `?page=1&itemsPerPage=10`. [code: app/config/config.php:410-478 @7.x]
[code: app/bundles/AssetBundle/Tests/Functional/ApiPlatform/DownloadOwnershipApiV2AuthorizationRegressionTest.php:140 @7.x]

R94. Normalization and denormalization groups are `<name>:read` and `<name>:write`.
[code: app/bundles/WebhookBundle/Entity/Webhook.php:28-50 @7.x]

R95. Security expressions are evaluated by `ApiPermissionVoter`, which supports any attribute containing `:`. For an
`...own`/`...other` attribute with an object it calls `hasEntityAccess(own, other, owner)`; otherwise `isGranted()`.
Owner resolution prefers `getPermissionUser()`, then `getCreatedBy()`, then `getOwner()`.
[code: app/bundles/ApiBundle/Security/Voter/ApiPermissionVoter.php:22-115 @7.x]

R96. `API_PLATFORM_PERMISSION_CONTEXT` is dispatched before the voter decides; listeners may rewrite the permission and
the subject. On the voter path `getRequest()` is null and `getAttributes()` is empty.
[code: app/bundles/ApiBundle/Security/Voter/ApiPermissionVoter.php:30-38 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#api-permission-context-event]

R97. Collections whose operation security is `is_granted('<x>:<y>:<z>own')` are ownership-scoped: own-only callers see
rows with `owner = me` or (`owner IS NULL AND createdBy = me`) for entities with an `owner` field (Lead, Company), else
`createdBy = me`; other-only callers see the complement plus unowned rows; callers with both or neither get no filter.
[code: app/bundles/ApiBundle/Extension/OwnershipScopedCollectionExtension.php:32-204 @7.x]

R98. A child entity filters through its parent when the parent association is marked `->isOwnershipParent()` in its
Doctrine metadata. [code: app/bundles/ApiBundle/Extension/OwnershipScopedCollectionExtension.php:32-204 @7.x]

R99. Every ownership-scoped item operation must pass `object` in its expression; a meta-test enforces this.
[code: app/bundles/ApiBundle/Tests/Functional/OwnershipScopedSecurityMetadataTest.php @7.x]

R100. `PUT /api/v2/<resource>/{id}` loads the existing entity and replaces every mapped field and association from the
request, setting omitted fields to null; the id is preserved. A nonexistent id returns 404 (PUT never creates in v2).
[code: app/bundles/ApiBundle/State/PutProcessor.php:27-97 @7.x]
[code: app/bundles/ApiBundle/Tests/Functional/Serializer/PutOperationTest.php:50-93,145-164,206-250 @7.x]

R101. v2 writes on a `FormEntity` stamp `dateAdded`, `createdBy`, `createdByUser` when new and always `dateModified`,
`modifiedBy`, `modifiedByUser`, in UTC. [code: app/bundles/ApiBundle/ApiPlatform/EventListener/MauticWriteSubscriber.php:26-61 @7.x]

R102. v2 writes persist through API Platform's Doctrine persist processor (decorated by `PutProcessor`), not through
Mautic models or forms. Inferred consequence (no model call exists on that path): model events
(`*_PRE_SAVE`/`*_POST_SAVE`), the `API_ON_ENTITY_*` events and v1 coercion (R52) do not run for v2 writes. Verify with a
test before relying on a side effect. [code: app/bundles/ApiBundle/Config/services.php:49-54 @7.x]
[code: app/bundles/ApiBundle/State/PutProcessor.php:27-97 @7.x]
[code: app/bundles/ApiBundle/Controller/CommonApiController.php:567-595 @7.x]

R103. `GET /api/v2/categories` (Category `GetCollection`) has no security expression.
[code: app/bundles/CategoryBundle/Entity/Category.php:23-26 @7.x]

R104. The same User-bound bearer token works on v1 and v2 (`/api/users` and `/api/v2/users`).
[code: app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php:154-183 @7.x]

## 13. Docs-versus-code discrepancies

D1. `publishedOnly` vs `published`: most devdocs pages and the PHP library name the list filter `publishedOnly`; the
controller reads `published` (R36). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html#list-assets]

D2. `searchFilter` appears in the Companies, Forms, Segments, Stages, Users and Webhooks docs; it is the PHP library
argument name and the HTTP parameter is `search`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#query-parameters]
[code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:163-232 @7.x]

D3. Error envelope: devdocs show `{"error":{...}}` (R74).

D4. `where`/`order`/`select` are documented only for Contacts; the base controller accepts them on every list endpoint
(R39). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#advanced-filtering]

D5. `api_batch_max_limit` is documented only for the 8.0 batch add-contacts endpoint; it caps every batch endpoint in
7.2.1 (R56). [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/companies.html#batch-add-contacts-to-companies]

D6. `POST /api/companies/batch/addcontacts` is on the 7.x branch after 7.2.1 (unreleased; [PR #16512]) but only in the 8.0 docs.
[code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:122-124 @7.x]

D7. The authentication docs say only the refresh-token lifetime is configurable; the access-token lifetime is also
configurable (R17). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#refreshing-tokens]

D8. `DELETE /users/ID` (docs) does not exist; use `DELETE /api/users/{id}/delete`.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#delete-user] [code: app/bundles/UserBundle/Config/config.php:79-84 @7.x]

D9. Campaign export is GET, not POST. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#exporting-via-api]
[code: app/bundles/CampaignBundle/Config/config.php:132-134 @7.x]

D10. Stats `limit` default is 100 in code, 30 in the docs.
[code: app/bundles/CoreBundle/Controller/Api/StatsApiController.php:25-32 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stats.html#get-stats-from-a-table]

D11. The plugin-extension docs say the permission-context event fires from `MauticDenyAccessListener` and the voter;
`MauticDenyAccessListener` is not registered as a listener anywhere, so only the voter path runs.
[devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#api-permission-context-event]
[code: app/bundles/ApiBundle/ApiPlatform/EventListener/MauticDenyAccessListener.php:35-80 @7.x]

D12. Several devdocs REST pages (data, dynamic_content, files, focus, messages, pages, point_actions, point_triggers,
roles) are stubs, and others carry a "legacy, potentially inaccurate" banner; use code and this inventory for those.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/data.html] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/pages.html]
