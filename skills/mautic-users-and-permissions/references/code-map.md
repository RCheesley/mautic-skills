# Users, roles, permissions — code map (Mautic 7.x)

## Table of contents
1. Entities and tables
2. Models and services
3. Security wiring (firewalls, authenticators, listeners)
4. Events
5. Routes and controllers
6. Configuration parameters and env switches
7. Permission bit table
8. Every registered permission (bundle:name → level set)
9. Operation → permission map for UserBundle
10. Tests directory


## 1. Entities and tables

| Entity | Table | Key facts | Source |
|---|---|---|---|
| `Mautic\UserBundle\Entity\User` | `users` | `username` (191, unique), `password` (64, bcrypt), `first_name`, `last_name`, `email` (191, unique), `position`, `role_id` (NOT NULL FK, no ON DELETE), `timezone`, `locale`, `last_login`, `last_active`, `preferences` (serialized array), `signature` (text); inherits `is_published` and audit columns from `FormEntity` | [code: app/bundles/UserBundle/Entity/User.php:166-227 @7.x] |
| `Role` | `roles` | `name`, `description`, `is_admin`, `readable_permissions` (array, raw form/API input), `uuid`; OneToMany `permissions` (orphanRemoval, cascade) and `users` | [code: app/bundles/UserBundle/Entity/Role.php:105-128 @7.x] |
| `Permission` | `permissions` | `bundle` (50), `name` (50), `role_id` (ON DELETE CASCADE), `bitwise` int, `uuid`; unique `unique_perm (bundle, name, role_id)` | [code: app/bundles/UserBundle/Entity/Permission.php:81-101 @7.x] |
| `UserToken` | `user_tokens` | `user_id` (CASCADE), `authorizator` (32), `secret` (120, unique), `expiration` (NULL = never), `one_time_only` (default true) | [code: app/bundles/UserBundle/Entity/UserToken.php:40-70 @7.x] |
| `UserInvite` (7.2.0+) | `user_invites` | `email` (indexed), `token_selector` (32, unique), `token_verifier_hash`, `expiration` (indexed), `used`, `role_id` (CASCADE) | [code: app/bundles/UserBundle/Entity/UserInvite.php:36-65 @7.x] |
| `IdEntry` | `saml_id_entry` | LightSAML replay store, PK `(id, entity_id)`, `expiry_timestamp` | [code: app/bundles/UserBundle/Entity/IdEntry.php:30-44 @7.x] |
| `AuditLog` (CoreBundle) | `audit_log` | consumer of user/role/login events via `AuditLogModel::writeToLog` | [code: app/bundles/UserBundle/EventListener/UserSubscriber.php:34-102 @7.x] |

Repositories: `UserRepository` (search commands, `checkUniqueUsernameEmail`, `setLastLogin`, `getUserList`), `RoleRepository` (user count subquery), `PermissionRepository` (cached `[bundle][name] => bitwise`), `UserTokenRepository` (`deleteExpired`). [code: app/bundles/UserBundle/Entity/UserRepository.php:29-327 @7.x] [code: app/bundles/UserBundle/Entity/PermissionRepository.php:18-59 @7.x]

## 2. Models and services

| Class / service id | Path | Role | Source |
|---|---|---|---|
| `UserModel` / `mautic.user.model.user` | `app/bundles/UserBundle/Model/UserModel.php` | CRUD, `checkNewPassword`, reset token + email, change notifications, preferences, invites; permission base `user:users` | [code: app/bundles/UserBundle/Model/UserModel.php:72-75 @7.x] |
| `RoleModel` (final) / `mautic.user.model.role` | `app/bundles/UserBundle/Model/RoleModel.php` | CRUD, `setRolePermissions` → `CorePermissions::generatePermissions`, delete guard, clone | [code: app/bundles/UserBundle/Model/RoleModel.php:48-145 @7.x] |
| `PasswordStrengthEstimatorModel` | `app/bundles/UserBundle/Model/PasswordStrengthEstimatorModel.php` | zxcvbn, min score 3 | [code: app/bundles/UserBundle/Model/PasswordStrengthEstimatorModel.php:14-44 @7.x] |
| `UserTokenService` | `app/bundles/UserBundle/Model/UserToken/` | unique secret generation/verification | [code: app/bundles/UserBundle/Model/UserToken/UserTokenService.php:20-36 @7.x] |
| `CorePermissions` / `mautic.security` | `app/bundles/CoreBundle/Security/Permissions/CorePermissions.php` | `isGranted`, `hasEntityAccess`, `hasPublishAccessForEntity`, `generatePermissions`, `checkPermissionExists` | [code: app/bundles/CoreBundle/Config/services.php:167-170 @7.x] |
| `AbstractPermissions` | `app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php` | base class for every permission class | [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:24-519 @7.x] |
| `UserProvider` / `mautic.user.provider` | `app/bundles/UserBundle/Security/Provider/UserProvider.php` | load by username or email, published only, 5-min cache; `saveUser()` for SSO | [code: app/bundles/UserBundle/Security/Provider/UserProvider.php:39-145 @7.x] |
| `TokenPermissions` / `security.token.permissions` | `app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php` | attaches Role permissions; client-credentials pseudo-User | [code: app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php:30-104 @7.x] |
| `UserTokenSetter` | `app/bundles/UserBundle/Security/UserTokenSetter.php` | act as a User from CLI | [code: app/bundles/UserBundle/Security/UserTokenSetter.php:18-25 @7.x] |
| `AuthenticationHandler` / `mautic.security.authentication_handler` | `app/bundles/UserBundle/Security/Authentication/AuthenticationHandler.php` | success/failure redirects or JSON | [code: app/bundles/UserBundle/Security/Authentication/AuthenticationHandler.php:22-58 @7.x] |
| `UserHelper` | `app/bundles/CoreBundle/Helper/UserHelper.php` | current User or guest | [code: app/bundles/CoreBundle/Helper/UserHelper.php:20-38 @7.x] |
| SAML helpers/stores | `app/bundles/UserBundle/Security/SAML/` | `Helper`, `User/UserMapper`, `User/UserCreator`, `Store/*` | [code: app/bundles/UserBundle/Security/SAML/Helper.php:18-27 @7.x] |
| `UserProcessor` | `app/bundles/UserBundle/ApiPlatform/UserProcessor.php` | hashes `plainPassword` for API Platform | [code: app/bundles/UserBundle/ApiPlatform/UserProcessor.php:23-32 @7.x] |
| `ApiPermissionVoter` | `app/bundles/ApiBundle/Security/Voter/ApiPermissionVoter.php` | own/other for API Platform | [code: app/bundles/ApiBundle/Security/Voter/ApiPermissionVoter.php:46-115 @7.x] |

Deprecated since 7.2: service aliases `mautic.security.logout_handler` and `mautic.security.user_token_setter` (use class ids). [code: app/bundles/UserBundle/Config/services.php:131-134 @7.x]

## 3. Security wiring

| Piece | Where | Source |
|---|---|---|
| Firewalls `sso_login`, `api`, `v2api`, `main`; form login, logout, remember-me, login throttling, access control | `app/config/security.php` | [code: app/config/security.php:22-154 @7.x] |
| OAuth2 token lifetimes (env `MAUTIC_API_OAUTH2_ACCESS_TOKEN_LIFETIME`, `_REFRESH_TOKEN_LIFETIME`) | `app/config/security_api.php` | [code: app/config/security_api.php:13-14 @7.x] |
| Test env: md5 hasher, HTTP Basic on `main` | `app/config/security_test.php` | [code: app/config/security_test.php:8-25 @7.x] |
| `TimingSafeFormLoginAuthenticator` (decorates `security.authenticator.form_login.main`) | `app/bundles/UserBundle/Security/TimingSafeFormLoginAuthenticator.php` | [code: app/bundles/UserBundle/Security/TimingSafeFormLoginAuthenticator.php:69-84 @7.x] |
| `SsoAuthenticator` (`mautic_sso` factory) / `PluginAuthenticator` (`mautic_plugin_auth` factory) | `app/bundles/UserBundle/Security/Authenticator/` | [code: app/bundles/UserBundle/DependencyInjection/Firewall/Factory/MauticSsoFactory.php:21-57 @7.x] |
| Factory + compiler-pass registration | `app/bundles/UserBundle/MauticUserBundle.php`, `DependencyInjection/Compiler/*` | [code: app/bundles/UserBundle/MauticUserBundle.php:17-30 @7.x] |
| `MainEntryPoint` | `app/bundles/UserBundle/Security/EntryPoint/MainEntryPoint.php` | [code: app/bundles/UserBundle/Security/EntryPoint/MainEntryPoint.php:21-34 @7.x] |
| `PasswordStrengthSubscriber` (CheckPassport prio 100), `PasswordSubscriber` (prio −100), `ApiUserSubscriber` (prio 2048) | `app/bundles/UserBundle/EventListener/` | [code: app/bundles/UserBundle/EventListener/PasswordSubscriber.php:21-47 @7.x] [code: app/bundles/UserBundle/EventListener/ApiUserSubscriber.php:30-97 @7.x] |
| Login side effects (last_login, session timezone/locale, `USER_LOGIN`) | `app/bundles/CoreBundle/EventListener/CoreSubscriber.php` | [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:53-95 @7.x] |
| Per-request timezone/locale | `app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php` | [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:30-61 @7.x] |
| Restricted config fields list | `app/config/security.php` (`mautic.security.restrictedConfigFields`) | [code: app/config/security.php:181-200 @7.x] |

## 4. Events (`app/bundles/UserBundle/UserEvents.php`; whole class removed on 8.x)

| Constant | Name | Event class | Dispatched | Core listener | Source |
|---|---|---|---|---|---|
| `USER_PRE_SAVE` / `USER_POST_SAVE` | `mautic.user_pre_save` / `mautic.user_post_save` | `UserEvent` | `UserModel` save, `UserProvider::saveUser` | post: audit log | [code: app/bundles/UserBundle/Model/UserModel.php:174-208 @7.x] |
| `USER_PRE_DELETE` / `USER_POST_DELETE` | `mautic.user_pre_delete` / `…post_delete` | `UserEvent` | `UserModel` delete | post: audit log | [code: app/bundles/UserBundle/EventListener/UserSubscriber.php:54-66 @7.x] |
| `ROLE_PRE_SAVE` / `ROLE_POST_SAVE` / `ROLE_PRE_DELETE` / `ROLE_POST_DELETE` | `mautic.role_*` | `RoleEvent` | `RoleModel` | post: audit log | [code: app/bundles/UserBundle/Model/RoleModel.php:150-184 @7.x] |
| `USER_LOGIN` | `mautic.user_login` | `LoginEvent` | `CoreSubscriber` on interactive login | audit log `security/login` | [code: app/bundles/UserBundle/EventListener/SecuritySubscriber.php:28-43 @7.x] |
| `USER_LOGOUT` | `mautic.user_logout` | `LogoutEvent` | `LogoutListener` | none | [code: app/bundles/UserBundle/EventListener/LogoutListener.php:25-32 @7.x] |
| `USER_FORM_AUTHENTICATION` | `mautic.user_form_authentication` | `AuthenticationEvent` | `SsoAuthenticator` (login POST with `integration`) | none | [code: app/bundles/UserBundle/Security/Authenticator/SsoAuthenticator.php:130-132 @7.x] |
| `USER_PRE_AUTHENTICATION` | `mautic.user_pre_authentication` | `AuthenticationEvent` | `PluginAuthenticator` | none | [code: app/bundles/UserBundle/Security/Authenticator/PluginAuthenticator.php:66-79 @7.x] |
| `USER_AUTHENTICATION_CONTENT` | `mautic.user_authentication_content` | `AuthenticationContentEvent` | login page Twig helper | none | [code: app/bundles/CoreBundle/Twig/Helper/SecurityHelper.php:63-65 @7.x] |
| `USER_FORM_POST_LOCAL_PASSWORD_AUTHENTICATION` | — | — | never dispatched | — | [code: app/bundles/UserBundle/UserEvents.php @7.x] |
| `USER_PASSWORD_STRENGTH_VALIDATION` | `mautic.user_password_strength_validation` | `PasswordStrengthValidateEvent` | `PasswordStrengthEstimatorModel` | none | [code: app/bundles/UserBundle/Model/PasswordStrengthEstimatorModel.php:40-41 @7.x] |
| (ApiBundle) `API_PLATFORM_PERMISSION_CONTEXT` | `mautic.api_platform_permission_context` | `ApiPlatformPermissionContextEvent` | `ApiPermissionVoter` | none | [code: app/bundles/ApiBundle/Security/Voter/ApiPermissionVoter.php:30-38 @7.x] |

8.x event classes replacing these are listed in version-notes.md.

## 5. Routes and controllers

| Route | Path | Controller | Source |
|---|---|---|---|
| `login` | `/s/login` | `SecurityController::loginAction` | [code: app/bundles/UserBundle/Config/config.php:28-131 @7.x] |
| `mautic_user_logincheck` | `/s/login_check` | intercepted by firewall | [code: app/config/security.php:83-89 @7.x] |
| `mautic_user_logout` | `/s/logout` | firewall logout → `/s/login` | [code: app/config/security.php:90-93 @7.x] |
| `mautic_sso_login`, `mautic_sso_login_check` | `/s/sso_login/{integration}`, `/s/sso_login_check/{integration}` | redirect to login unless a plugin intercepts | [code: app/bundles/UserBundle/Controller/SecurityController.php:103-115 @7.x] |
| `lightsaml_sp.login`, `lightsaml_sp.login_check` | `/s/saml/login`, `/s/saml/login_check` | LightSAML | [code: app/bundles/UserBundle/Config/config.php:28-131 @7.x] |
| `lightsaml_sp.metadata`, `lightsaml_sp.discovery`, `mautic_saml_login_retry` | `/saml/metadata.xml`, `/saml/discovery`, `/saml/login_retry` | LightSAML / `SecurityController::samlLoginRetryAction` | same |
| `mautic_user_index`, `mautic_user_action` | `/s/users/{page}`, `/s/users/{objectAction}/{objectId}` (`new`, `edit`, `delete`, `batchDelete`, `contact`, `invite`) | `UserController` | same |
| `mautic_role_index`, `mautic_role_action` | `/s/roles/{page}`, `/s/roles/{objectAction}/{objectId}` (`new`, `edit`, `clone`, `delete`, `batchDelete`) | `RoleController` | same |
| `mautic_user_account` | `/s/account` | `ProfileController::indexAction` | same |
| `mautic_user_passwordreset`, `mautic_user_passwordresetconfirm` | `/passwordreset`, `/passwordresetconfirm` | `PublicController` | same |
| `mautic_user_invite_register` | `/invite/{token}` | `PublicController::inviteAction` | same |
| API (legacy) | `/api/users[...]`, `/api/users/self`, `/api/users/{id}/permissioncheck`, `/api/users/list/roles`, `/api/roles[...]` | `Controller/Api/UserApiController`, `RoleApiController` | [code: app/bundles/UserBundle/Config/config.php:78-104 @7.x] |
| API Platform | `/api/v2/users`, `/api/v2/roles`, `/api/v2/permissions` | entity attributes | [code: app/bundles/UserBundle/Entity/User.php:28-46 @7.x] |

Views: `app/bundles/UserBundle/Resources/views/` (`Security/*`, `User/*`, `Role/*`, `Profile/index.html.twig`, `Email/invite.html.twig`). Role matrix JS: `app/bundles/UserBundle/Assets/js/user.js:79-147`. [code: app/bundles/UserBundle/Resources/views/Role/form.html.twig:47-99 @7.x]

There are no `mautic:user:*` console commands; expired tokens are purged by `mautic:maintenance:cleanup`. [code: app/bundles/CoreBundle/EventListener/MaintenanceSubscriber.php:34-35 @7.x]

## 6. Configuration parameters and env switches

| Parameter | Default | Effect | Source |
|---|---|---|---|
| `saml_idp_metadata` | `''` | non-empty = SAML enabled | [code: app/bundles/UserBundle/Config/config.php:132-143 @7.x] |
| `saml_idp_entity_id` | `''` | SP entity id (site URL or subdomain URL); env `MAUTIC_SAML_ENTITY_ID` | [code: app/bundles/UserBundle/Form/Type/ConfigType.php:30-45 @7.x] [code: app/config/security.php:161 @7.x] |
| `saml_idp_own_certificate`, `saml_idp_own_private_key`, `saml_idp_own_password` | `''` | signing/encryption cert, key, key password | [code: app/bundles/UserBundle/EventListener/ConfigSubscriber.php:48,65-86 @7.x] |
| `saml_idp_email_attribute`, `saml_idp_username_attribute`, `saml_idp_firstname_attribute`, `saml_idp_lastname_attribute` | form defaults `EmailAddress`, —, `FirstName`, `LastName` | IdP attribute mapping | [code: app/bundles/UserBundle/Form/Type/ConfigType.php:112-162 @7.x] |
| `saml_idp_default_role` | `''` | Role id for auto-created SAML Users; empty = no creation | [code: app/bundles/UserBundle/Security/SAML/User/UserCreator.php:34-38 @7.x] |
| `rememberme_key`, `rememberme_lifetime`, `rememberme_path`, `rememberme_domain` | `%mautic.secret_key%`, `7776000`, `/`, `''` | remember-me cookie | [code: app/bundles/CoreBundle/Config/config.php:281-284 @7.x] |
| `locale`, `default_timezone` | `en_US`, `UTC` | system fallbacks for Users | [code: app/bundles/CoreBundle/Config/config.php:274,286 @7.x] |
| env `MAUTIC_SAML_ENABLED` | — | entry point to `/saml/discovery`; registers `SAMLSubscriber` | [code: app/config/security.php:162 @7.x] |
| env `MAUTIC_SAML_LOGIN_PATH`, `MAUTIC_SAML_LOGIN_CHECK_PATH` | — | SAML firewall paths | [code: app/config/security.php:77-81 @7.x] |
| env `MAUTIC_SESSION_NAME` | — | session cookie name | [code: app/config/config.php:91 @7.x] |

There is no parameter for password strength, token lifetimes (24 h reset, 48 h invite) or throttling; these are constants. [code: app/bundles/UserBundle/Model/UserModel.php:247-256,416-441 @7.x] [code: app/config/security.php:105-108 @7.x]

## 7. Permission bit table

| Level | Standard set (`addStandardPermissions($names, $includePublish = true)`) | Extended set (`addExtendedPermissions($names, $includePublish = true)`) | Manage (`addManagePermission`) |
|---|---|---|---|
| viewown | — (synonym → view) | 2 | — |
| view / viewother | 4 | 4 (`viewother`; `view` → viewown) | — |
| editown | — (synonym → edit) | 8 | — |
| edit / editother | 16 | 16 (`editother`) | — |
| create | 32 | 32 | — |
| deleteown | — (synonym → delete) | 64 | — |
| delete / deleteother | 128 | 128 (`deleteother`) | — |
| publishown | — | 256 (if publish included) | — |
| publish / publishother | 512 (if publish included) | 512 (`publishother`) | — |
| full | 1024 | 1024 | `manage` = 1024 |

Sources: [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:334-352,408-419,455-477 @7.x]. `addCustomPermission($level, [name => bit])` defines arbitrary levels. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:306-309 @7.x]

Worked examples: bitwise `52` = view 4 + edit 16 + create 32 (standard) [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:113 @7.x]; extended `editother` saved alone becomes `16 + 4 + 2 = 22` after implied levels. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:214-247 @7.x]

## 8. Every registered permission (7.x)

"Std" = standard set, "Std−pub" = standard without publish, "Ext" = extended set, "Ext−pub" = extended without publish.
`bundle` is the class's `getName()`.

| Permission (`bundle:name`) | Level set | Class (line) |
|---|---|---|
| `api:access` | custom `{full: 1024}` | [code: app/bundles/ApiBundle/Security/Permissions/ApiPermissions.php:18-22 @7.x] |
| `api:clients` | Std−pub | [code: app/bundles/ApiBundle/Security/Permissions/ApiPermissions.php:23 @7.x] |
| `asset:assets` | Ext | [code: app/bundles/AssetBundle/Security/Permissions/AssetPermissions.php:18 @7.x] |
| `asset:categories` | Std | [code: app/bundles/AssetBundle/Security/Permissions/AssetPermissions.php:19 @7.x] |
| `campaign:campaigns` | Ext | [code: app/bundles/CampaignBundle/Security/Permissions/CampaignPermissions.php:18 @7.x] |
| `campaign:categories` | Std | [code: app/bundles/CampaignBundle/Security/Permissions/CampaignPermissions.php:19 @7.x] |
| `campaign:imports` | Std | [code: app/bundles/CampaignBundle/Security/Permissions/CampaignPermissions.php:20 @7.x] |
| `campaign:export` | custom `{enable: 1024}` | [code: app/bundles/CampaignBundle/Security/Permissions/CampaignPermissions.php:21 @7.x] |
| `category:categories` | Std | [code: app/bundles/CategoryBundle/Security/Permissions/CategoryPermissions.php:17 @7.x] |
| `channel:categories` | Std | [code: app/bundles/ChannelBundle/Security/Permissions/ChannelPermissions.php:17 @7.x] |
| `channel:messages` (Marketing Messages) | Ext | [code: app/bundles/ChannelBundle/Security/Permissions/ChannelPermissions.php:18 @7.x] |
| `core:themes` | Std | [code: app/bundles/CoreBundle/Security/Permissions/SystemPermissions.php:15 @7.x] |
| `dynamiccontent:categories` | Std | [code: app/bundles/DynamicContentBundle/Security/Permissions/DynamicContentPermissions.php:17 @7.x] |
| `dynamiccontent:dynamiccontents` | Ext | [code: app/bundles/DynamicContentBundle/Security/Permissions/DynamicContentPermissions.php:18 @7.x] |
| `email:categories` | Std | [code: app/bundles/EmailBundle/Security/Permissions/EmailPermissions.php:18 @7.x] |
| `email:emails` | Ext + `sendtodnc` = 1 ("Send to unsubscribed contacts") | [code: app/bundles/EmailBundle/Security/Permissions/EmailPermissions.php:19-20 @7.x] |
| `form:export` | custom `{enable: 1024}` | [code: app/bundles/FormBundle/Security/Permissions/FormPermissions.php:16 @7.x] |
| `form:forms` | Ext | [code: app/bundles/FormBundle/Security/Permissions/FormPermissions.php:17 @7.x] |
| `form:categories` | Std | [code: app/bundles/FormBundle/Security/Permissions/FormPermissions.php:18 @7.x] |
| `lead:fields` (Custom Fields) | custom `{view: 1, full: 1024}`; form label "manage" = full; `publishown`/`publishother` → full | [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php:36-41,106-120 @7.x] |
| `lead:leads` (Contacts) | Ext−pub | [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php:43 @7.x] |
| `lead:notes` (7.2.0+) | Ext−pub | [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php:44 @7.x] |
| `lead:lists` (Segments) | Ext | [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php:45 @7.x] |
| `lead:imports` | Std | [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php:46 @7.x] |
| `lead:export` | custom `{enable: 1024}` | [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php:47 @7.x] |
| `marketplace:packages` | Std−pub; class enabled only when the Marketplace is enabled | [code: app/bundles/MarketplaceBundle/Security/Permissions/MarketplacePermissions.php:31-39 @7.x] |
| `notification:categories` | Std | [code: app/bundles/NotificationBundle/Security/Permissions/NotificationPermissions.php:16 @7.x] |
| `notification:notifications` | Ext | [code: app/bundles/NotificationBundle/Security/Permissions/NotificationPermissions.php:17 @7.x] |
| `notification:mobile_notifications` | Ext | [code: app/bundles/NotificationBundle/Security/Permissions/NotificationPermissions.php:18 @7.x] |
| `page:pages` (Landing Pages) | Ext | [code: app/bundles/PageBundle/Security/Permissions/PagePermissions.php:16 @7.x] |
| `page:categories` | Std | [code: app/bundles/PageBundle/Security/Permissions/PagePermissions.php:17 @7.x] |
| `page:preference_center` | Ext | [code: app/bundles/PageBundle/Security/Permissions/PagePermissions.php:18 @7.x] |
| `plugin:plugins` | Manage | [code: app/bundles/PluginBundle/Security/Permissions/PluginPermissions.php:16 @7.x] |
| `point:points`, `point:triggers`, `point:groups`, `point:categories`, `point:insights` | Std (each) | [code: app/bundles/PointBundle/Security/Permissions/PointPermissions.php:19 @7.x] |
| `project:project` | Std−pub + `associate` = 8 | [code: app/bundles/ProjectBundle/Security/Permissions/ProjectPermissions.php:32-35 @7.x] |
| `report:reports` | Ext | [code: app/bundles/ReportBundle/Security/Permissions/ReportPermissions.php:18 @7.x] |
| `report:export` | custom `{enable: 1024}` | [code: app/bundles/ReportBundle/Security/Permissions/ReportPermissions.php:19 @7.x] |
| `sms:categories` | Std | [code: app/bundles/SmsBundle/Security/Permissions/SmsPermissions.php:16 @7.x] |
| `sms:smses` | Ext | [code: app/bundles/SmsBundle/Security/Permissions/SmsPermissions.php:17 @7.x] |
| `stage:stages` | Std | [code: app/bundles/StageBundle/Security/Permissions/StagePermissions.php:27 @7.x] |
| `stage:categories` | Std | [code: app/bundles/StageBundle/Security/Permissions/StagePermissions.php:28 @7.x] |
| `user:profile` | custom `{editusername: 1, editemail: 2, editposition: 4, editname: 8, full: 1024}` | [code: app/bundles/UserBundle/Security/Permissions/UserPermissions.php:18-25 @7.x] |
| `user:users` | Std−pub | [code: app/bundles/UserBundle/Security/Permissions/UserPermissions.php:26 @7.x] |
| `user:roles` | Std−pub | [code: app/bundles/UserBundle/Security/Permissions/UserPermissions.php:27 @7.x] |
| `webhook:webhooks` | Ext | [code: app/bundles/WebhookBundle/Security/Permissions/WebhookPermissions.php:16 @7.x] |
| `webhook:categories` | Std | [code: app/bundles/WebhookBundle/Security/Permissions/WebhookPermissions.php:17 @7.x] |
| `focus:categories` (plugin) | Std | [code: plugins/MauticFocusBundle/Security/Permissions/FocusPermissions.php:16 @7.x] |
| `focus:items` (plugin, Focus Items) | Ext | [code: plugins/MauticFocusBundle/Security/Permissions/FocusPermissions.php:17 @7.x] |
| `mauticSocial:categories`, `mauticSocial:monitoring` (plugin) | Std | [code: plugins/MauticSocialBundle/Security/Permissions/MauticSocialPermissions.php:16-17 @7.x] |
| `mauticSocial:tweets` (plugin) | Ext | [code: plugins/MauticSocialBundle/Security/Permissions/MauticSocialPermissions.php:18 @7.x] |
| `tagManager:tagManager` (plugin) | Std−pub | [code: plugins/MauticTagManagerBundle/Security/Permissions/TagManagerPermissions.php:19 @7.x] |

Not permission-based: Configuration and System Info (admin only) [code: app/bundles/ConfigBundle/Controller/ConfigController.php:41 @7.x]; audit-log stats/report (admin only) [code: app/bundles/CoreBundle/EventListener/CommonStatsSubscriber.php:56-93 @7.x].

Constant strings used by callers but not defined as levels: `marketplace:packages:remove` (`MarketplacePermissions::CAN_REMOVE_PACKAGES`) — see SKILL.md Pitfalls. [code: app/bundles/MarketplaceBundle/Security/Permissions/MarketplacePermissions.php:22 @7.x] [code: app/bundles/MarketplaceBundle/Controller/Package/RemoveController.php:40 @7.x]

## 9. Operation → permission map (UserBundle)

| Operation | Permission | Source |
|---|---|---|
| Users list / new / edit / delete / batch delete | `user:users:view` / `create` / `edit` / `delete` | [code: app/bundles/UserBundle/Controller/UserController.php:61,148,208,319,466,681 @7.x] |
| Invite a User | `user:users:create` | [code: app/bundles/UserBundle/Controller/UserController.php:148 @7.x] |
| Roles list / new / edit / delete | `user:roles:view` / `create` / `edit` / `delete` | [code: app/bundles/UserBundle/Controller/RoleController.php:20-26 @7.x] |
| Clone Role | `user:roles:create` and `user:roles:view` | [code: app/bundles/UserBundle/Controller/RoleController.php:215 @7.x] |
| Profile fields | `user:profile:editname|editusername|editposition|editemail` | [code: app/bundles/UserBundle/Controller/ProfileController.php:40-152 @7.x] |
| Profile API-credentials tab | `api:access:full` + `api_enabled` | [code: app/bundles/UserBundle/Controller/ProfileController.php:42-43 @7.x] |
| Global search Users / Roles | `user:users:view` / `user:roles:view` | [code: app/bundles/UserBundle/EventListener/SearchSubscriber.php:65-71 @7.x] |
| `GET /api/users/list/roles` | `user:users:create` or `edit` | [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:198-217 @7.x] |

## 10. Tests directory

`app/bundles/UserBundle/Tests/` (functional tests on `MauticMysqlTestCase`; unit tests on PHPUnit `TestCase`); permission framework tests in `app/bundles/CoreBundle/Tests/Functional/Security/Permissions/` and `app/bundles/CoreBundle/Tests/Unit/Security/Permissions/`. See test-patterns.md. [code: app/bundles/UserBundle/Tests/Traits/CreateEntityTrait.php @7.x]
