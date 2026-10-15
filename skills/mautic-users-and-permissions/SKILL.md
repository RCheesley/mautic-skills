---
name: mautic-users-and-permissions
description: "Mautic back-office Users, Roles and the permission framework, plus authentication (form login, remember-me, login throttling, password policy and reset, user invitations, SAML SSO, plugin SSO authenticators, API auth), the audit log of user actions, and the Users/Roles REST API. Use whenever a task mentions users, roles, permissions, access denied or 403 for a back-office user, admin or Full System Access, own vs other permissions (viewown, editother), isGranted, CorePermissions, AbstractPermissions, permission bits, adding permissions to a plugin, login, logout, remember me, password strength, forgot password, inviting team members, SAML, SSO, UserEvents, a user's timezone, locale or signature, the audit log, /api/users, /api/roles, or touches app/bundles/UserBundle/, app/bundles/CoreBundle/Security/Permissions/, any */Security/Permissions/*Permissions.php or app/config/security*.php."
---
# Mautic users, roles, permissions and authentication

## Scope
This skill covers back-office accounts (`User`, table `users`), Roles and their bitwise permission rows, the
CoreBundle permission framework every bundle uses, how Users authenticate (form, remember-me, SAML, plugin SSO, API),
password and invitation flows, per-User timezone/locale/signature, and the audit trail of user and role changes.
Out of scope: Contacts and contact ownership semantics (mautic-contacts), OAuth2 client setup and general API conventions
(mautic-rest-api), the Configuration UI and parameters at large (mautic-configuration).

## Expected behaviour (essentials)

Terms: **User** = back-office account (never a Contact). **Role** = named permission set; each User has exactly one.
**Admin** = User whose Role has Full System Access (`roles.is_admin = 1`). **Permission string** = `bundle:name:level`,
e.g. `lead:leads:viewother`.

Authentication
- Users log in with username **or** email; only published Users can authenticate, and unpublishing a User ends their session on the next refresh. [code: app/bundles/UserBundle/Security/Provider/UserProvider.php:39-74 @7.x]
- Login is CSRF-protected and throttled to 3 attempts per 30 minutes; unknown usernames take the same time as wrong passwords. [code: app/config/security.php:83-89,105-108 @7.x] [code: app/bundles/UserBundle/Security/TimingSafeFormLoginAuthenticator.php:69-84 @7.x]
- A correct login with a password that scores below zxcvbn 3 is rejected and the User is sent to reset it; on HTTP Basic API calls this is a 401. [code: app/bundles/UserBundle/EventListener/PasswordSubscriber.php:28-47 @7.x] [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:109-128 @7.x]
- Every interactive login writes `last_login`/`last_active`, sets session timezone and locale from the User (fallback: `default_timezone`, `locale`), and writes an audit row `user/security/login` with IP. [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:53-95 @7.x] [code: app/bundles/UserBundle/EventListener/SecuritySubscriber.php:28-43 @7.x]
- Remember-me lasts `rememberme_lifetime` (default 90 days) and satisfies `/s/*`; `/api/*` requires full authentication. [code: app/config/security.php:94-100,153-154 @7.x]
- A password change invalidates the User's other sessions (session compares the password hash). [code: app/bundles/UserBundle/Entity/User.php:709-719 @7.x]
- On the API firewall OAuth2, HTTP Basic and plugin authenticators all resolve to the same `User`, so API permissions are Role permissions; client-credentials tokens act as a pseudo-User with the API client's Role. [code: app/config/security.php:51-67 @7.x] [code: app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php:30-95 @7.x]
- SAML is "on" when `saml_idp_metadata` is non-empty; a SAML User is matched by username or email, else created with `saml_idp_default_role`, else refused. Password fields are hidden in SAML sessions. [code: app/bundles/UserBundle/Security/SAML/Helper.php:18-27 @7.x] [code: app/bundles/UserBundle/Security/SAML/User/UserCreator.php:34-67 @7.x] [code: app/bundles/UserBundle/Controller/UserController.php:366-369 @7.x]
- Redirecting every unauthenticated request to the IdP needs env `MAUTIC_SAML_ENABLED=true`; metadata alone does not do it. [code: app/bundles/UserBundle/Security/EntryPoint/MainEntryPoint.php:21-34 @7.x]

Passwords, reset, invites
- Passwords need ≥ 6 characters **and** zxcvbn score ≥ 3 (plugins can override via `mautic.user_password_strength_validation`). [code: app/bundles/UserBundle/Entity/User.php:260-266 @7.x] [code: app/bundles/UserBundle/Model/PasswordStrengthEstimatorModel.php:14-44 @7.x]
- Password reset never reveals whether the account exists (same flash, ≥ 1 s response); tokens are 64 chars, one-time, 24 h. [code: app/bundles/UserBundle/Controller/PublicController.php:44-139 @7.x] [code: app/bundles/UserBundle/Model/UserModel.php:247-304 @7.x]
- Invites (7.2.0+, `user:users:create`) expire after 48 h, revoke earlier unused invites to the same email, and fix email and Role for the invitee. [code: app/bundles/UserBundle/Model/UserModel.php:416-497 @7.x] [code: app/bundles/UserBundle/Controller/PublicController.php:154-216 @7.x]
- On an existing User the legacy API silently ignores `plainPassword` and username changes. [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:122-139 @7.x]

Users and Roles
- Username and email are unique across **both** columns. [code: app/bundles/UserBundle/Entity/UserRepository.php:52-67 @7.x]
- Users cannot delete themselves; a Role with Users cannot be deleted. [code: app/bundles/UserBundle/Controller/UserController.php:488-516 @7.x] [code: app/bundles/UserBundle/Model/RoleModel.php:98-110 @7.x]
- Deleting a User leaves `created_by` ids dangling on content and makes their Contacts unowned. [code: app/bundles/CoreBundle/Entity/FormEntity.php:146-153 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:312-314 @7.x]
- Profile fields are editable only with the matching `user:profile:*` level; Role and active status are never editable from the profile. [code: app/bundles/UserBundle/Controller/ProfileController.php:40-168 @7.x]
- Timezone and locale precedence is User → system, applied per request from the session. [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:30-61 @7.x]
- User and Role create/update/delete are audit-logged with changed fields (Role changes include `rawPermissions` diffs). [code: app/bundles/UserBundle/EventListener/UserSubscriber.php:34-102 @7.x]

Permission framework
- Admins pass every well-formed permission check without any stored rows; admin Roles store no `permissions` rows. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:220-222 @7.x] [code: app/bundles/UserBundle/Model/RoleModel.php:84-86 @7.x]
- A Role stores one row per `bundle:name` whose `bitwise` is the sum of ticked level bits; `full` (1024) grants every level of that name. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:149-169 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:190-207 @7.x]
- Standard set: view 4, edit 16, create 32, delete 128, publish 512, full 1024. Extended set adds own/other: viewown 2, viewother 4, editown 8, editother 16, create 32, deleteown 64, deleteother 128, publishown 256, publishother 512, full 1024. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:334-352,455-477 @7.x]
- Synonyms: on an extended permission `view` means `viewown`; on a standard permission `viewother` means `view`. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:144-181 @7.x]
- Own/other: no owner (0/null) → "other" decides; owner = current User → "own" decides; else "other". [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:335-379 @7.x]
- Saving a Role adds implied levels (edit ⇒ view own+other; delete ⇒ editother + views; create/editown/… ⇒ viewown; any view ⇒ that bundle's `categories:view`) to the stored bits but **not** to `readable_permissions`/`rawPermissions`. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:214-255 @7.x] [code: app/bundles/UserBundle/Model/RoleModel.php:92 @7.x]
- A non-admin with no row for a bundle is denied everything in it; an unknown level throws `PermissionNotFoundException`; a malformed string throws `PermissionBadFormatException` (403). [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x]
- `user:users` and `user:roles` are standard sets: anyone with `user:users:edit` can edit any User, including admins. [code: app/bundles/UserBundle/Security/Permissions/UserPermissions.php:26-27 @7.x]
- Configuration, System Info, audit-log stats and the audit-log report are admin-only, not permission-based. [code: app/bundles/ConfigBundle/Controller/ConfigController.php:41 @7.x] [code: app/bundles/CoreBundle/EventListener/CommonStatsSubscriber.php:56-93 @7.x]

Full list: references/behaviour.md (B1–B127).

## Where it lives

| Concern | Path(s) |
|---|---|
| Entities / tables | `app/bundles/UserBundle/Entity/{User,Role,Permission,UserToken,UserInvite,IdEntry}.php` → `users`, `roles`, `permissions`, `user_tokens`, `user_invites`, `saml_id_entry` |
| Models | `app/bundles/UserBundle/Model/{UserModel,RoleModel,PasswordStrengthEstimatorModel}.php` |
| Permission framework | `app/bundles/CoreBundle/Security/Permissions/{CorePermissions,AbstractPermissions,SystemPermissions,VirtualPermissions}.php` (service `mautic.security`) |
| Per-bundle permission classes | `app/bundles/*/Security/Permissions/*Permissions.php`, `plugins/*/Security/Permissions/*Permissions.php` |
| Security config | `app/config/security.php`, `security_api.php`, `security_test.php` |
| Authenticators, provider, SAML | `app/bundles/UserBundle/Security/` |
| Login side effects, timezone/locale | `app/bundles/CoreBundle/EventListener/{CoreSubscriber,EnvironmentSubscriber}.php` |
| Events | `app/bundles/UserBundle/UserEvents.php` (7.x only), `app/bundles/UserBundle/Event/` |
| Controllers / routes | `app/bundles/UserBundle/Controller/{Security,User,Role,Profile,Public}Controller.php`, `Controller/Api/{User,Role}ApiController.php`, routes in `app/bundles/UserBundle/Config/config.php` |
| Audit listeners | `app/bundles/UserBundle/EventListener/{UserSubscriber,SecuritySubscriber}.php` |
| Config parameters | `saml_idp_*` in `app/bundles/UserBundle/Config/config.php`; `rememberme_*`, `locale`, `default_timezone` in `app/bundles/CoreBundle/Config/config.php` |
| Tests | `app/bundles/UserBundle/Tests/`, `app/bundles/CoreBundle/Tests/*/Security/Permissions/` |

Every registered permission and the bit table: references/code-map.md §7–§8. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:334-477 @7.x]

## How to change or extend it

- **Add permissions for a plugin**: create `Security/Permissions/<Name>Permissions.php` extending `AbstractPermissions`; return the permission prefix from `getName()` (camelCase bundle name, matching the file); define levels with `addStandardPermissions` / `addExtendedPermissions` / `addManagePermission` / `addCustomPermission`; add the matching `add*FormFields` in `buildForm()`; register it as a service tagged `mautic.permissions`. Check with `isGranted('<name>:<level>:<perm>')` — no `plugin:` prefix. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:24-27,306-519 @7.x] [code: app/bundles/CoreBundle/DependencyInjection/Compiler/PermissionsPass.php:12-20 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#creating-custom-permissions]
- Define levels in the constructor, not `definePermissions()`, so the class also works on 8.x. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html#construct]
- Override `isEnabled()` to hide the tab when the plugin is off; override `analyzePermissions()` for cross-permission implications (return `true` for a second round); implement `VirtualPermissions` for computed grants. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:63-66 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:137-146,239-240 @7.x]
- Never renumber existing bits or rename levels: stored `permissions.bitwise` values and `readable_permissions` arrays would silently change meaning, and unknown names throw on Role save. A data migration is needed for any such change (the `lead:notes` backfill is the model). [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:149-171 @7.x] [code: app/migrations/Version20260501090000.php @7.x]
- Enforce on the backend; Twig `securityIsGranted()` only hides UI. For record-level checks use `hasEntityAccess($ownPerm, $otherPerm, $ownerId)`. [devdocs: https://devdocs.mautic.org/en/7.2/design/displaying_elements_based_on_user_permissions.html] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:335-379 @7.x]
- **Custom login**: listen to `mautic.user_form_authentication` (login form with `integration` field) or `mautic.user_pre_authentication` (`/s/sso_login/*`, `/api/*`) and call `setIsAuthenticated()`, `setResponse()` or `setIsFailedAuthentication()`. Add login-page HTML with `mautic.user_authentication_content`. [code: app/bundles/UserBundle/Event/AuthenticationEvent.php:96-181 @7.x]
- **Act as a User from CLI** with `UserTokenSetter::setUser($id)`; otherwise code sees a guest with no permissions. [code: app/bundles/UserBundle/Security/UserTokenSetter.php:18-25 @7.x]
- Adding a User column: update `User.php` metadata, a migration, the `user:read`/`user:write` API Platform groups and legacy serializer, `UserType`, translations, and check `UserSubscriber` audit output. [code: app/bundles/UserBundle/Entity/User.php:54-149 @7.x]
- On 7.x, subscribe to both the constant and (on 8.x) the event class; never reference `UserEvents::*` unguarded in code meant for 8.x. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]

## How to test it

- Functional: extend `MauticMysqlTestCase`; use `Tests/Traits/CreateEntityTrait` (`createRole`, `createUser`) and add `Permission` rows with explicit bits — rows built this way skip implied levels. [code: app/bundles/UserBundle/Tests/Traits/CreateEntityTrait.php @7.x] [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:161-171 @7.x]
- The test env uses md5 hashing and HTTP Basic on `main`; fixtures give `admin`/`sales` with `Maut1cR0cks!`. [code: app/config/security_test.php:8-25 @7.x]
- Copy from: `Tests/Controller/Api/UserApiControllerFunctionalTest.php`, `Tests/Functional/Controller/RoleControllerFunctionalTest.php`, `Tests/Functional/Controller/PublicControllerTest.php`, `Tests/Security/UserLoginTest.php`, `Tests/Model/UserModelTest.php`, `app/bundles/CoreBundle/Tests/Functional/Security/Permissions/CorePermissionsTest.php`. [code: app/bundles/UserBundle/Tests/Functional/Controller/RoleControllerFunctionalTest.php:62-192 @7.x]
- A good regression test asserts both sides of a gate (granted vs 403, admin always passes), own vs other records, and for Role saves the stored bits vs the raw array. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:220-245 @7.x]
- Details and skeletons: references/test-patterns.md.

## Version notes

- 5.1.0: zxcvbn password strength introduced; complex admin password required at install. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
- 7.0.0: timing-safe login; `project:project` permission. [code: app/bundles/UserBundle/Security/TimingSafeFormLoginAuthenticator.php @7.x]
- 7.2.0: User invitations; `lead:notes` permission with a migration copying Contact levels to Notes. [code: app/bundles/UserBundle/Entity/UserInvite.php @7.x] [code: app/migrations/Version20260501090000.php @7.x]
- 7.x head after 7.2.1: `is:never_logged_in`; not yet on 8.x. [code: app/bundles/UserBundle/Entity/UserRepository.php:248-249 @7.x]
- 5.0: logout runs on Symfony's `LogoutEvent`; templates are Twig; each instance generates its own SAML key and certificate when none is configured. [PR #11867] [PR #11580] [PR #12212]
- 5.1–5.2: the User toggle reads "Active"; the User list gains last login and recent activity; admins changing a User's email or password triggers an email to that User; full-access Roles disable the Permissions tab. [PR #13503] [PR #13074] [PR #13925] [PR #14004]
- 6.0: form login, SAML, OAuth2 and plugin SSO move to Symfony's authenticator system (bc-break); User preferences are stored in the database; Roles and permission rows get UUIDs. [PR #14219] [PR #14398] [PR #14751]
- 6.0.3: plugin SSO authenticators (for example Auth0) log the User in again after the 6.0 change. [PR #15020]
- 8.x: `UserEvents` deleted (event classes such as `PostSaveUserEvent`, `PreAuthenticationEvent`); `AuthenticationEvent`/`UserEvent`/`RoleEvent` abstract; `definePermissions()` removed and permission classes are autoconfigured services; `mautic.security` and `mautic.user.provider` ids removed; SAML moves to lightsaml2. [PR #17510] [PR #17079] [PR #17121] [PR #17370]
- Full detail: references/version-notes.md.

## Pitfalls

- `isGranted()` caches per permission string for the request, ignoring the User argument: checking a second User's permission returns the first result. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:210-213,249 @7.x]
- `lead:leads:view` on an extended permission tests `viewown`, not "any view". Ask for `viewother` explicitly. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:144-181 @7.x]
- Admins are granted even non-existent levels, so a typo in a permission string passes for admins and throws for everyone else — always test as a non-admin. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:220-235 @7.x]
- `marketplace:packages:remove` (`MarketplacePermissions::CAN_REMOVE_PACKAGES`) is checked by the Marketplace remove controllers, but `remove` is not a defined level of the standard set, so for non-admins `isGranted()` should throw `PermissionNotFoundException`. Treat package removal as admin-only in practice. [code: app/bundles/MarketplaceBundle/Security/Permissions/MarketplacePermissions.php:22,33 @7.x] [code: app/bundles/MarketplaceBundle/Controller/Package/RemoveController.php:40 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:47-58 @7.x]
- `rawPermissions` in API responses omit implied levels; compare stored bits, not the raw array. [code: app/bundles/UserBundle/Model/RoleModel.php:92 @7.x]
- `users.last_active` is only written at login, so for Users it equals `last_login`. [code: app/bundles/UserBundle/Entity/UserRepository.php:29-38 @7.x]
- Admin is a Role flag; there may be several admin Roles and `getSystemAdministrator()` picks the first published User of the first one. [code: app/bundles/UserBundle/Model/UserModel.php:159-169 @7.x]
- `UserEvents::USER_FORM_POST_LOCAL_PASSWORD_AUTHENTICATION` is never dispatched, and `AuthenticationEvent::isFormLogin()` is always false. [code: app/bundles/UserBundle/Event/AuthenticationEvent.php:63 @7.x]
- `MAUTIC_SAML_ENABLED=true` without metadata sends every unauthenticated request to `/saml/discovery` while SAML reports "not configured". [code: app/bundles/UserBundle/Security/EntryPoint/MainEntryPoint.php:23-25 @7.x]
- Docs describe a **Same Role** permission level; no such level exists in 7.2.1 or 8.x code — only own/other. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#where-same-role-permissions-apply] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:455-477 @7.x]
- Devdocs say plugin permissions use a `plugin:` prefix; the code treats the first segment as the permission class name, so use `<name>:<level>:<perm>`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x]
- Devdocs say `DELETE /api/users/ID` and that timezone/locale are required on create; the code route is `DELETE /api/users/{id}/delete` and creation succeeds without timezone/locale. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#delete-user] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:123-200 @7.x] [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:130-156 @7.x]
- User docs call complex passwords "recommended"; the strength check is enforced. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html] [code: app/bundles/UserBundle/Model/PasswordStrengthEstimatorModel.php:36-44 @7.x]
- `PATCH /api/users/{id}/edit` strips `username` and `plainPassword` but accepts `role`, so `user:users:edit` is enough to change any User's Role through the API. It shipped in 4.1.2 and was never reverted. [PR #10668] [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:122-138 @7.x]
- `UserModel::checkNewPassword()` and `resetPassword()` lost their hasher argument in 7.2.0 with no deprecation step; plugin code calling them must branch on the version. [PR #16980] [code: app/bundles/UserBundle/Model/UserModel.php:110,236 @7.x]
- The delete-User confirmation says API tokens and scheduled exports are removed, but that PR changed only translation strings; verify the cascade before testing for it. [PR #17444]
- Login, reset, invite, SAML-retry and OAuth2 consent pages do not load CKEditor (`includeEditor` false); scripts added there must not assume the editor exists. [PR #16987]
- Open questions: whether login throttling also limits per IP (Symfony default) [unverified]; whether API Platform `POST /api/v2/users` enforces the strength rule (no test) [unverified]; which code sets the `samlsso` session key (presumably the SAML vendor bundle) [unverified].

## Related skills

- mautic-architecture — bundle layout, DI, events, how `mautic.security` fits the container.
- mautic-rest-api — OAuth2/Basic setup, API clients, response conventions, API Platform v2.
- mautic-configuration — Configuration UI, SAML settings form, `local.php` parameters.
- mautic-plugin-development — building a plugin end to end (permission classes, SSO integrations).
- mautic-contacts — Contact owner, `lead:leads` own/other semantics on Contacts, Notes ownership.
- mautic-testing — test environment, `MauticMysqlTestCase`, fixtures, running PHPUnit.
- mautic-upgrades-and-versions — 7.x → 8.x porting and migrations.

## Reference files

- references/behaviour.md — numbered behaviour spec B1–B127 (login, passwords, invites, profile, Roles, permission evaluation, API, SSO/SAML, audit); open when you need the exact rule and citation.
- references/code-map.md — entities, services, security wiring, events, routes, parameters, the bit table and every registered permission; open to locate code.
- references/docs-digest.md — what docs.mautic.org and devdocs say, with URLs, procedures and doc/code discrepancies.
- references/test-patterns.md — base classes, helpers, tests to copy, regression-test checklist, skeletons.
- references/version-notes.md — 5.1/7.x history and the 8.x delta for users, permissions and SAML.
- references/pr-history.md — why and when User, Role, login, reset, invite and SAML behaviour changed: decisions, regression catalogue, feature timeline and removals from merged PRs.
