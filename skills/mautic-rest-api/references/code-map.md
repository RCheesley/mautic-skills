# REST API framework: code map (Mautic 7.x)

Paths are relative to the repository root. The full endpoint list is in `endpoint-inventory.md`.

## Contents
1. Bundles and base controllers
2. OAuth2 entities and tables
3. Helpers, serializer and security services
4. API Platform (v2) glue
5. Events
6. Routes and firewalls
7. Configuration parameters
8. Permissions
9. Tests

## 1. Bundles and base controllers

| Concern | Path | Notes |
|---|---|---|
| REST framework bundle | `app/bundles/ApiBundle/` | Base controllers, OAuth2, JMS metadata, API Platform glue, `/s/credentials` UI. [code: app/bundles/ApiBundle/Config/config.php @7.x] |
| Read-only base controller | `app/bundles/ApiBundle/Controller/FetchCommonApiController.php` | Extends FOS REST `AbstractFOSRestController`. Config properties set in the child constructor: `$entityClass`, `$entityNameOne`, `$entityNameMulti`, `$serializerGroups`, `$exclusionStrategies`, `$permissionBase`, `$listFilters`, `$extraGetEntitiesArguments`, `$parentChildrenLevelDepth = 3`. Actions `getEntitiesAction` L163-246, `getEntityAction` L307-335. Helpers `checkEntityAccess` L409-429, `getBatchEntities` L441-497, `returnError` L611-640, `setBatchError` L661-673, `setSerializationContext` L678-721, `validateBatchPayload` L728-736, `view()` L742-752, `getOwnEntityListFilters` L775-782. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php @7.x] |
| Write base controller | `app/bundles/ApiBundle/Controller/CommonApiController.php` | `deleteEntitiesAction` L78-128, `deleteEntityAction` L137-162, `editEntitiesAction` L169-234, `editEntityAction` L243-267, `newEntitiesAction` L274-331, `newEntityAction` L338-348, hooks `prePopulateForm` L376, `preSaveEntity` L390, `prepareParametersForBinding` L403, `processForm` L460-620, `saveEntity` L622-627, `setCategory` L635-646, `detachEntity` L651-654. `$model` must be a `FormModel`. [code: app/bundles/ApiBundle/Controller/CommonApiController.php @7.x] |
| Request coercion | `app/bundles/CoreBundle/Form/RequestTrait.php:35-169` | Boolean, pipe multiselect, date normalisation, HTML masks. [code: app/bundles/CoreBundle/Form/RequestTrait.php:35-169 @7.x] |
| Form error extraction | `app/bundles/CoreBundle/Controller/FormErrorMessagesTrait.php:64-74` | Builds `details`. [code: app/bundles/CoreBundle/Controller/FormErrorMessagesTrait.php:64-74 @7.x] |
| List filter engine | `app/bundles/CoreBundle/Entity/CommonRepository.php` | Index-by-id L360-405, `where` L1007-1030 and L1610-1706, limits L1364-1373, ordering L1381-1420. [code: app/bundles/CoreBundle/Entity/CommonRepository.php @7.x] |
| Route expansion | `app/bundles/CoreBundle/EventListener/CoreSubscriber.php:114-302` | `standard_entity`, `supported_endpoints`, `_format`, id constraints. [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:114-302 @7.x] |
| Route prefix | `app/bundles/CoreBundle/Loader/RouteLoader.php:58-67` | Adds `/api`. [code: app/bundles/CoreBundle/Loader/RouteLoader.php:58-67 @7.x] |
| Minimal example controller | `app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php` | Smallest real `CommonApiController` child; copy it for a new resource. [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php @7.x] |
| Per-resource controllers | `app/bundles/*/Controller/Api/*ApiController.php`, `plugins/*/Controller/Api/*ApiController.php` | Listed in `endpoint-inventory.md`. |

## 2. OAuth2 entities and tables

All extend FOS OAuthServerBundle model classes. [code: app/bundles/ApiBundle/Entity/oAuth2/Client.php:67-102 @7.x]

| Entity | Table | Key facts |
|---|---|---|
| `Entity/oAuth2/Client.php` | `oauth2_clients` | `name`, `random_id` (index `client_id_search`), `secret`, `redirect_uris` (array), `allowed_grant_types` (array), `role_id` (nullable FK to Role). M2M `users` via `oauth2_user_client_xref` (cascade delete). Default grants L58-61. Repository `ClientRepository`. [code: app/bundles/ApiBundle/Entity/oAuth2/Client.php:58-102 @7.x] |
| `Entity/oAuth2/AccessToken.php` | `oauth2_accesstokens` | `client_id` NOT NULL cascade, `user_id` nullable (client credentials), `token` unique, `expires_at`, `scope`. [code: app/bundles/ApiBundle/Entity/oAuth2/AccessToken.php:14-47 @7.x] |
| `Entity/oAuth2/RefreshToken.php` | `oauth2_refreshtokens` | `user_id` NOT NULL. [code: app/bundles/ApiBundle/Entity/oAuth2/RefreshToken.php:14-46 @7.x] |
| `Entity/oAuth2/AuthCode.php` | `oauth2_authcodes` | `redirect_uri` TEXT. [code: app/bundles/ApiBundle/Entity/oAuth2/AuthCode.php:14-49 @7.x] |

| Class | Path | Role |
|---|---|---|
| `ClientModel` | `app/bundles/ApiBundle/Model/ClientModel.php` | Permission base `api:clients`; only mode `oauth2`; dispatches only post-save/post-delete; `revokeAccess()`. [code: app/bundles/ApiBundle/Model/ClientModel.php:28-148 @7.x] |
| `ClientController` | `app/bundles/ApiBundle/Controller/ClientController.php` | `/s/credentials` UI; adds `client_credentials` for admins L207-210; sets role L211. [code: app/bundles/ApiBundle/Controller/ClientController.php:115-225 @7.x] |
| `AuthorizeController` | `app/bundles/ApiBundle/Controller/oAuth2/AuthorizeController.php` | Consent screen. [code: app/bundles/ApiBundle/Controller/oAuth2/AuthorizeController.php:36-54 @7.x] |
| `SecurityController` | `app/bundles/ApiBundle/Controller/oAuth2/SecurityController.php` | Login for the authorize flow. [code: app/bundles/ApiBundle/Controller/oAuth2/SecurityController.php:13-51 @7.x] |
| `PreAuthorizationEventListener` | `app/bundles/ApiBundle/EventListener/PreAuthorizationEventListener.php` | `api:access:full` check and auto-approval. Service alias `mautic.api.oauth.event_listener` deprecated since 7.2. [code: app/bundles/ApiBundle/EventListener/PreAuthorizationEventListener.php:27-66 @7.x] [code: app/bundles/ApiBundle/Config/services.php:29-31 @7.x] |
| `TokenPermissions` | `app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php` | Client-credentials pseudo user. [code: app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php:43-95 @7.x] |
| `ApiEnvVars` | `app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php` | Token lifetimes to env vars. [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:13-17 @7.x] |
| OAuth server config | `app/config/security_api.php` | `fos_oauth_server` lifetimes; `supported_scopes` commented out. [code: app/config/security_api.php:9-16 @7.x] |

## 3. Helpers, serializer and security services

| Class | Path | Role |
|---|---|---|
| `ApiSubscriber` | `app/bundles/ApiBundle/EventListener/ApiSubscriber.php` | `KernelEvents::REQUEST` (priority 255): API disabled and Basic disabled guards; `RESPONSE`: OAuth error rewriting. [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:23-176 @7.x] |
| `ConfigSubscriber` | `app/bundles/ApiBundle/EventListener/ConfigSubscriber.php` | Casts `api_enable_basic_auth` on save. [code: app/bundles/ApiBundle/EventListener/ConfigSubscriber.php:32-40 @7.x] |
| `RequestHelper` | `app/bundles/ApiBundle/Helper/RequestHelper.php` | `isApiRequest()`, `hasBasicAuth()`. [code: app/bundles/ApiBundle/Helper/RequestHelper.php:11-26 @7.x] |
| `EntityResultHelper` | `app/bundles/ApiBundle/Helper/EntityResultHelper.php` | Paginator rows to entities; `{}` for empty non-Paginator results. [code: app/bundles/ApiBundle/Helper/EntityResultHelper.php:29-85 @7.x] |
| `BatchIdToEntityHelper` | `app/bundles/ApiBundle/Helper/BatchIdToEntityHelper.php` | Batch id payload parsing. [code: app/bundles/ApiBundle/Helper/BatchIdToEntityHelper.php:54-154 @7.x] |
| `ApiMetadataDriver` | `app/bundles/ApiBundle/Serializer/Driver/ApiMetadataDriver.php` | Calls each entity's static `loadApiMetadata()`; wired by `SerializerPass`. [code: app/bundles/ApiBundle/Serializer/Driver/ApiMetadataDriver.php:27-242 @7.x] [code: app/bundles/ApiBundle/DependencyInjection/Compiler/SerializerPass.php:20-26 @7.x] |
| Exclusion strategies | `app/bundles/ApiBundle/Serializer/Exclusion/` | `FieldExclusionStrategy`, `FieldInclusionStrategy`, `ParentChildrenExclusionStrategy`, `PublishDetailsExclusionStrategy`. [code: app/bundles/ApiBundle/Serializer/Exclusion/FieldExclusionStrategy.php:36-52 @7.x] |
| `ApiLockAwareInterface`, `ApiEntityLockTrait` | `app/bundles/ApiBundle/Model/` | 409 opt-in; only `EmailModel` implements it. [code: app/bundles/ApiBundle/Controller/CommonApiController.php:491-520 @7.x] |
| `ApiPermissions` | `app/bundles/ApiBundle/Security/Permissions/ApiPermissions.php` | `api:access:full`, `api:clients:*`. [code: app/bundles/ApiBundle/Security/Permissions/ApiPermissions.php:18-72 @7.x] |

## 4. API Platform (v2) glue

| Class | Path | Role |
|---|---|---|
| `ApiPermissionVoter` | `app/bundles/ApiBundle/Security/Voter/ApiPermissionVoter.php` | Voter for Mautic permission strings (tag `security.voter`). [code: app/bundles/ApiBundle/Security/Voter/ApiPermissionVoter.php:22-115 @7.x] [code: app/bundles/ApiBundle/Config/services.php:34 @7.x] |
| `OwnershipScopedCollectionExtension` | `app/bundles/ApiBundle/Extension/OwnershipScopedCollectionExtension.php` | Own/other filtering of collections. [code: app/bundles/ApiBundle/Extension/OwnershipScopedCollectionExtension.php:32-204 @7.x] |
| `PutProcessor` | `app/bundles/ApiBundle/State/PutProcessor.php` | Decorates `api_platform.doctrine.orm.state.persist_processor`; PUT replaces the existing entity. [code: app/bundles/ApiBundle/State/PutProcessor.php:27-97 @7.x] [code: app/bundles/ApiBundle/Config/services.php:49-54 @7.x] |
| `MauticWriteSubscriber` | `app/bundles/ApiBundle/ApiPlatform/EventListener/MauticWriteSubscriber.php` | `KernelEvents::VIEW` at `PRE_WRITE`; audit stamps. [code: app/bundles/ApiBundle/ApiPlatform/EventListener/MauticWriteSubscriber.php:26-61 @7.x] |
| `MauticDenyAccessListener` | `app/bundles/ApiBundle/ApiPlatform/EventListener/MauticDenyAccessListener.php` | Not registered anywhere; only its unit test uses it. [code: app/bundles/ApiBundle/ApiPlatform/EventListener/MauticDenyAccessListener.php:35-80 @7.x] |
| API Platform config | `app/config/config.php:410-478` | Formats, PATCH formats, error formats, `exception_to_status`, docs. [code: app/config/config.php:410-478 @7.x] |
| v2 route import | `app/config/routing.php:10-12` | Prefix `/api/v2/`. [code: app/config/routing.php:10-12 @7.x] |
| Resource declarations | `#[ApiResource]` on entities | List in `endpoint-inventory.md` section 5. |

## 5. Events

| Constant (string) | Event class | Dispatched at | Core listeners |
|---|---|---|---|
| `ApiEvents::API_ON_ENTITY_PRE_SAVE` (`mautic.api_on_entity_pre_save`) | `ApiEntityEvent(entity, requestParameters, request)` | `CommonApiController.php:568-570` | none [code: app/bundles/ApiBundle/ApiEvents.php:52 @7.x] |
| `ApiEvents::API_ON_ENTITY_POST_SAVE` (`mautic.api_on_entity_post_save`) | `ApiEntityEvent` | `CommonApiController.php:590-592` | none [code: app/bundles/ApiBundle/ApiEvents.php:61 @7.x] |
| `ApiEvents::API_PRE_SERIALIZATION_CONTEXT` | `ApiSerializationContextEvent(context, request)` | `FetchCommonApiController.php:682-686` | none [code: app/bundles/ApiBundle/ApiEvents.php:70 @7.x] |
| `ApiEvents::API_POST_SERIALIZATION_CONTEXT` | `ApiSerializationContextEvent` | `FetchCommonApiController.php:714-718` | none [code: app/bundles/ApiBundle/ApiEvents.php:79 @7.x] |
| `ApiEvents::API_PLATFORM_PERMISSION_CONTEXT` | `ApiPlatformPermissionContextEvent` (mutable permission and subject) | `ApiPermissionVoter.php:30-35` | none [code: app/bundles/ApiBundle/ApiEvents.php:88 @7.x] |
| `ApiEvents::CLIENT_POST_SAVE` / `CLIENT_POST_DELETE` | `ClientEvent` | `ClientModel.php:101-129` | `ClientSubscriber` audit log [code: app/bundles/ApiBundle/EventListener/ClientSubscriber.php:24-65 @7.x] |
| `ApiEvents::CLIENT_PRE_SAVE`, `ApiEvents::BUILD_ROUTE` | — | never dispatched | — [code: app/bundles/ApiBundle/ApiEvents.php:16,43 @7.x] |
| (class name) `ApiInitializeEvent(entityClass, serializerGroups, exclusionStrategies)` | `app/bundles/ApiBundle/Event/ApiInitializeEvent.php` | `FetchCommonApiController.php:147-152` | none [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:147-155 @7.x] |

External events consumed: FOS `OAuthEvent::PRE_AUTHORIZATION_PROCESS`/`POST_AUTHORIZATION_PROCESS`, `KernelEvents::REQUEST`
and `RESPONSE`, `ConfigEvents::CONFIG_ON_GENERATE`/`CONFIG_PRE_SAVE`, `CoreEvents::GLOBAL_SEARCH`/`BUILD_COMMAND_LIST`.
[code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:23-29 @7.x]
[code: app/bundles/ApiBundle/EventListener/PreAuthorizationEventListener.php:27-66 @7.x]

## 6. Routes and firewalls

| Item | Where |
|---|---|
| OAuth routes and `/s/credentials` | `app/bundles/ApiBundle/Config/config.php:9-39` [code: app/bundles/ApiBundle/Config/config.php:9-39 @7.x] |
| "API Credentials" menu (Integrations; needs `api_enabled` and `api:clients:view`) | `app/bundles/ApiBundle/Config/config.php:43-60` [code: app/bundles/ApiBundle/Config/config.php:43-60 @7.x] |
| `oauth2_token` firewall (`security: false`) | `app/config/security.php:38-41` [code: app/config/security.php:38-41 @7.x] |
| `oauth2_area` form login | `app/config/security.php:42-50` [code: app/config/security.php:42-50 @7.x] |
| `v2api` firewall (stateful, shared `mautic` context) | `app/config/security.php:51-59` [code: app/config/security.php:51-59 @7.x] |
| `api` firewall (stateless) | `app/config/security.php:60-67` [code: app/config/security.php:60-67 @7.x] |
| `main` UI firewall also enables `fos_oauth` | `app/config/security.php:103` [code: app/config/security.php:103 @7.x] |
| access control `^/api` → `IS_AUTHENTICATED_FULLY` | `app/config/security.php:153` [code: app/config/security.php:153 @7.x] |
| Views | `app/bundles/ApiBundle/Resources/views/Client/{list,form,authorized}.html.twig`, `Authorize/oAuth2/authorize.html.twig`, `Security/login.html.twig` [code: app/bundles/ApiBundle/Controller/oAuth2/AuthorizeController.php:36-44 @7.x] |

## 7. Configuration parameters

| Parameter | Default | UI | Effect |
|---|---|---|---|
| `api_enabled` | `false` | Configuration > API Settings | Master switch. [code: app/bundles/ApiBundle/Config/config.php:62-68 @7.x] [code: app/bundles/ApiBundle/Form/Type/ConfigType.php:20-28 @7.x] |
| `api_enable_basic_auth` | `false` | yes | Allows `Authorization: Basic`. [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:70-89 @7.x] |
| `api_oauth2_access_token_lifetime` | `60` minutes | yes | Env `MAUTIC_API_OAUTH2_ACCESS_TOKEN_LIFETIME`. [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:13-14 @7.x] |
| `api_oauth2_refresh_token_lifetime` | `14` days | yes | Env `MAUTIC_API_OAUTH2_REFRESH_TOKEN_LIFETIME`. [code: app/bundles/CoreBundle/Loader/EnvVars/ApiEnvVars.php:16-17 @7.x] |
| `api_batch_max_limit` | `200` | no (`config/local.php`) | Max batch items. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:728-736 @7.x] |
| `default_pagelimit` | `30` | system settings | Default list `limit`. [code: app/bundles/CoreBundle/Config/config.php:285 @7.x] |
| `max_entity_lock_time` | core | system settings | Lock expiry for 409. [code: app/bundles/CoreBundle/Model/FormModel.php:47-73 @7.x] |

## 8. Permissions

| Permission | Meaning |
|---|---|
| `api:access:full` (bit 1024, synonym `granted`) | Required to authorize an OAuth2 client in the authorize flow. [code: app/bundles/ApiBundle/Security/Permissions/ApiPermissions.php:18-22,65-72 @7.x] |
| `api:clients:view/create/edit/delete` | Manage API credentials (no own/other). [code: app/bundles/ApiBundle/Security/Permissions/ApiPermissions.php:23 @7.x] |
| `<resource base>:*` | Each endpoint's resource permissions; see `endpoint-inventory.md` and mautic-users-and-permissions. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:409-429 @7.x] |

## 9. Tests

| Test | What it covers |
|---|---|
| `app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php` | Authorize redirect, error envelopes, full client-credentials flow, bearer on v1 and v2. [code: app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php:33-183 @7.x] |
| `app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php` | 409 lock for Emails, no lock for Contacts, batch lock errors. [code: app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php:20-116 @7.x] |
| `app/bundles/ApiBundle/Tests/Functional/Serializer/PutOperationTest.php` | v2 PUT replace semantics and 404. [code: app/bundles/ApiBundle/Tests/Functional/Serializer/PutOperationTest.php:50-250 @7.x] |
| `app/bundles/ApiBundle/Tests/Functional/OwnershipScopedSecurityMetadataTest.php` | Meta-test: ownership-scoped item operations pass `object`. [code: app/bundles/ApiBundle/Tests/Functional/OwnershipScopedSecurityMetadataTest.php @7.x] |
| `app/bundles/ApiBundle/Tests/Controller/CommonApiControllerTest.php` | `where` sanitising, alias prefixing, batch entity resolution. [code: app/bundles/ApiBundle/Tests/Controller/CommonApiControllerTest.php:28-246 @7.x] |
| `app/bundles/ApiBundle/Tests/Helper/BatchIdToEntityHelperTest.php` | Batch id payload shapes. [code: app/bundles/ApiBundle/Tests/Helper/BatchIdToEntityHelperTest.php @7.x] |
| `app/bundles/ApiBundle/Tests/Extension/OwnershipScopedCollectionExtensionTest.php`, `Tests/Security/Voter/ApiPermissionVoterTest.php` | v2 permission semantics. [code: app/bundles/ApiBundle/Tests/Security/Voter/ApiPermissionVoterTest.php @7.x] |
| `app/bundles/ApiBundle/Tests/EventListener/ApiSubscriberTest.php` | Disabled-API and Basic guards. [code: app/bundles/ApiBundle/Tests/EventListener/ApiSubscriberTest.php:62-93 @7.x] |
| `app/bundles/LeadBundle/Tests/Functional/ApiPlatform/OwnershipScopedApiAuthorizationTestBase.php` | Base class for v2 own/other regression tests (users with permissions, `loginUser`). [code: app/bundles/AssetBundle/Tests/Functional/ApiPlatform/DownloadOwnershipApiV2AuthorizationRegressionTest.php:9-17 @7.x] |
| `app/bundles/CoreBundle/Tests/Unit/Loader/EnvVars/ApiEnvVarsTest.php` | Token lifetime conversion. [code: app/bundles/CoreBundle/Tests/Unit/Loader/EnvVars/ApiEnvVarsTest.php @7.x] |
