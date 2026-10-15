# Users, roles, permissions and authentication — behaviour specification (Mautic 7.x)

Every item is an observable rule with a source tag. "User" means a back-office account (table `users`), never a
Contact. A "Role" is a named set of permissions assigned to a User; every User has exactly one Role. "Admin" means a
User whose Role has Full System Access (`is_admin = 1`).

## Table of contents
1. Login and sessions (B1–B18)
2. Password rules, reset and change notifications (B19–B29)
3. User records and CRUD (B30–B44)
4. Invitations (B45–B48)
5. Profile, preferences, timezone and locale (B49–B57)
6. Roles (B58–B68)
7. Permission evaluation framework (B69–B90)
8. API authentication and the Users/Roles API (B91–B104)
9. Plugin, SSO and SAML authentication (B105–B115)
10. Audit log of user actions (B116–B123)
11. Defaults, fixtures and CLI acting-as-user (B124–B127)

---

## 1. Login and sessions

B1. A User logs in with either the username or the email address; the provider query matches `username = :x OR email = :x` and only published Users. [code: app/bundles/UserBundle/Security/Provider/UserProvider.php:39-56 @7.x] [code: app/bundles/UserBundle/Tests/Security/UserLoginTest.php:27-50 @7.x]

B2. The provider lookup is result-cached for 5 minutes; saving a User or Role invalidates the cache, direct DBAL writes (for example `last_login`) do not. [code: app/bundles/UserBundle/Security/Provider/UserProvider.php:50 @7.x] [code: app/bundles/UserBundle/Entity/Role.php:302-308 @7.x]

B3. An unpublished ("inactive") User cannot authenticate; the login page shows "Invalid login". [code: app/bundles/UserBundle/Security/Provider/UserProvider.php:46-55 @7.x] [code: app/bundles/UserBundle/Controller/SecurityController.php:67-69 @7.x]

B4. An existing session of a User who is then unpublished ends on the next token refresh, because `refreshUser()` reloads through the same published-only query. [code: app/bundles/UserBundle/Security/Provider/UserProvider.php:66-74 @7.x]

B5. Changing a User's password invalidates that User's other sessions on refresh: session serialisation keeps id, username, password hash and `isPublished`, and `isEqualTo` compares id, identifier and hash. [code: app/bundles/UserBundle/Entity/User.php:400-425 @7.x] [code: app/bundles/UserBundle/Entity/User.php:709-719 @7.x]

B6. The login form is CSRF-protected (`enable_csrf: true`, token id `authenticate`, field `_csrf_token`). [code: app/config/security.php:83-89 @7.x] [code: app/bundles/UserBundle/Resources/views/Security/login.html.twig:43 @7.x]

B7. Login attempts are throttled to 3 attempts per 30 minutes (Symfony `login_throttling`). Whether Symfony's default limiter also limits per IP is inferred from Symfony defaults, not Mautic code. [code: app/config/security.php:105-108 @7.x] [unverified: per-IP limit]

B8. Login timing does not reveal whether a username exists: for an unknown identifier the authenticator verifies the submitted password against a fixed bcrypt hash before rethrowing `UserNotFoundException`. [code: app/bundles/UserBundle/Security/TimingSafeFormLoginAuthenticator.php:69-84 @7.x] [code: app/bundles/UserBundle/Config/services.php:138-147 @7.x]

B9. A correct login whose presented password scores below zxcvbn 3 is rejected with `WeakPasswordException`; the login page flashes "Your password is too weak. Please reset it." and forwards to the password-reset form. [code: app/bundles/UserBundle/EventListener/PasswordSubscriber.php:28-47 @7.x] [code: app/bundles/UserBundle/Controller/SecurityController.php:62-66 @7.x] [code: app/bundles/UserBundle/Tests/EventListener/PasswordSubscriberTest.php @7.x]

B10. An empty presented password is rejected with `BadCredentialsException`. [code: app/bundles/UserBundle/EventListener/PasswordSubscriber.php:21-47 @7.x]

B11. On every interactive login Mautic writes `last_login` and `last_active` (UTC) with DBAL, stores the User id in session key `mautic.user`, and sets session `_timezone` and `_locale` from the User, falling back to `default_timezone` and `locale`. Then it dispatches `mautic.user_login`. [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:53-95 @7.x] [code: app/bundles/UserBundle/Entity/UserRepository.php:29-38 @7.x]

B12. For Users, `last_active` is written only at login, so it always equals `last_login`; `UserRepository::setLastActive()` has no caller. [code: app/bundles/UserBundle/Entity/UserRepository.php:29-38 @7.x]

B13. After login the User is redirected to the saved `_security.main.target_path` or the dashboard; a request with `format=json` gets `{"success":true}` instead. Failure stores the exception in session and redirects to `login`. [code: app/bundles/UserBundle/Security/Authentication/AuthenticationHandler.php:22-58 @7.x]

B14. Opening the login page while already authenticated (fully or via remember-me) redirects to the dashboard. [code: app/bundles/UserBundle/Controller/SecurityController.php:36-53 @7.x]

B15. Remember-me uses the `_remember_me` checkbox, secret `rememberme_key` (default `%mautic.secret_key%`), lifetime `rememberme_lifetime` (default 7776000 s = 90 days), path `rememberme_path`, domain `rememberme_domain`, SameSite=Lax. [code: app/config/security.php:94-100 @7.x] [code: app/bundles/CoreBundle/Config/config.php:281-284 @7.x] [code: app/bundles/UserBundle/Resources/views/Security/login.html.twig:37 @7.x]

B16. `/s/*` requires `IS_AUTHENTICATED` (remember-me suffices); `/api/*` requires `IS_AUTHENTICATED_FULLY`. [code: app/config/security.php:153-154 @7.x]

B17. An unauthenticated request to `/s/*` is redirected to `/s/login`, or to `/saml/discovery` when env `MAUTIC_SAML_ENABLED` is true and the route is not login/login_check. [code: app/bundles/UserBundle/Security/EntryPoint/MainEntryPoint.php:21-34 @7.x]

B18. Logout dispatches `mautic.user_logout`, clears the whole session, re-adds any items listeners kept with `setPostSessionItem()`, and sets `post_logout = true`, which the login page exposes as `AuthenticationContentEvent::isLogout()`. The session idle timeout follows php.ini; Mautic sets no `cookie_lifetime`/`gc_maxlifetime`. [code: app/bundles/UserBundle/EventListener/LogoutListener.php:21-38 @7.x] [code: app/bundles/UserBundle/Event/AuthenticationContentEvent.php:19-36 @7.x] [code: app/config/config.php:89-94 @7.x]

## 2. Password rules, reset and change notifications

B19. A password must be at least 6 characters and not "weak": zxcvbn score ≥ 3, with the extra dictionary `mautic,user,lead,bundle,campaign,company`. This applies to the User form, the reset-confirm form and the legacy API. [code: app/bundles/UserBundle/Entity/User.php:260-266 @7.x] [code: app/bundles/UserBundle/Form/Type/PasswordResetConfirmType.php:59-63 @7.x] [code: app/bundles/UserBundle/Model/PasswordStrengthEstimatorModel.php:14-44 @7.x] [code: app/bundles/UserBundle/Form/Validator/Constraints/NotWeakValidator.php:19-32 @7.x]

B20. On the legacy API `aaa`, `qwerty` and `qwerty123` are rejected with 400 and `Qwertee@123` is accepted with 201. [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:130-156 @7.x]

B21. Plugins can override the strength verdict by listening to `mautic.user_password_strength_validation` and setting `$event->isValid`. There is no configuration parameter for the minimum score. [code: app/bundles/UserBundle/Model/PasswordStrengthEstimatorModel.php:40-41 @7.x] [code: app/bundles/UserBundle/Event/PasswordStrengthValidateEvent.php @7.x]

B22. Passwords are hashed with bcrypt cost 12 (prod) and md5 in the `test` environment. [code: app/config/security.php:129-137 @7.x] [code: app/config/security_test.php:14-25 @7.x]

B23. Leaving the password field empty on edit keeps the existing hash: `checkNewPassword()` returns the existing hash when nothing is submitted and throws for fewer than 6 characters when validating. [code: app/bundles/UserBundle/Model/UserModel.php:110-124 @7.x] [code: app/bundles/UserBundle/Controller/UserController.php:376-385 @7.x]

B24. Password reset request (`/passwordreset`): the identifier is matched by username or email; a token is created and emailed only if the User exists, but the same success flash appears either way and the response is padded to at least 1 s. [code: app/bundles/UserBundle/Controller/PublicController.php:44-75 @7.x] [code: app/bundles/UserBundle/Tests/Functional/Controller/PublicControllerTest.php:49-79 @7.x]

B25. The reset token is a 64-character random secret with authorizator `reset-password`; it expires after 24 hours and is one-time-only. The email links to `/passwordresetconfirm?token=…`. A DB error while saving the token becomes `PasswordResetTokenCreationFailedException` and an error flash. [code: app/bundles/UserBundle/Model/UserModel.php:247-256 @7.x] [code: app/bundles/UserBundle/Model/UserModel.php:276-304 @7.x] [code: app/bundles/UserBundle/Enum/UserTokenAuthorizator.php:9 @7.x]

B26. The reset-confirm page stores the `token` query parameter in session `resetToken`; the POST needs the identifier and the session token; a valid unexpired token is deleted on first use; unknown identifiers still get the success flash. [code: app/bundles/UserBundle/Controller/PublicController.php:93-139 @7.x] [code: app/bundles/UserBundle/Entity/UserTokenRepository.php:26-47 @7.x]

B27. Expired reset tokens are deleted by `mautic:maintenance:cleanup` (dry-run aware). [code: app/bundles/CoreBundle/EventListener/MaintenanceSubscriber.php:29-36 @7.x] [code: app/bundles/UserBundle/Entity/UserTokenRepository.php:49-64 @7.x]

B28. When someone changes another User's password in the edit form, that User gets a "password changed" email; when the email address changes, a notice goes to the old address. [code: app/bundles/UserBundle/Controller/UserController.php:386-392 @7.x] [code: app/bundles/UserBundle/Model/UserModel.php:309-342 @7.x]

B29. Mautic never emails a generated password; the translation `mautic.user.user.passwordreset.body` with `%password%` is unused. [code: app/bundles/UserBundle/Translations/en_US/messages.ini:108 @7.x] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html]

## 3. User records and CRUD

B30. Username and email must each be unique across both the `username` and the `email` columns, so a username cannot equal another User's email. [code: app/bundles/UserBundle/Entity/UserRepository.php:52-67 @7.x] [code: app/bundles/UserBundle/Entity/User.php:236,252 @7.x]

B31. Required fields: username, first name, last name, email (valid format) and role. Position is optional (max 191). Timezone and locale are not validated as required. [code: app/bundles/UserBundle/Entity/User.php:230-267 @7.x]

B32. A new User needs a password; an existing User needs one only when changing it (validation groups `CheckPasswordNotBlank` / `CheckPassword`). [code: app/bundles/UserBundle/Entity/User.php:269-285 @7.x] [code: app/bundles/UserBundle/Tests/Functional/Controller/UserControllerFunctionalTest.php:141-240 @7.x]

B33. Only published Roles are offered in the Role dropdown of the User form and invite form. The dropdown has no placeholder and is ordered by name. [code: app/bundles/UserBundle/Form/Type/UserType.php:209-224 @7.x] [code: app/bundles/UserBundle/Form/Type/UserInviteType.php:52-54 @7.x]

B34. The User edit form locks the record (checkout) while open; a locked User cannot be edited or deleted by someone else until cancel/save. [code: app/bundles/UserBundle/Controller/UserController.php:358-361,429-439,497-499 @7.x]

B35. A User cannot delete their own account (single or batch); flash `mautic.user.user.error.cannotdeleteself`. [code: app/bundles/UserBundle/Controller/UserController.php:488-516,670-675 @7.x]

B36. Deleting a User cascades its `user_tokens`. Content the User created keeps the plain `created_by` id (no FK) and `created_by_user` name. Contacts owned by the User become unowned (`owner_id` FK `SET NULL`). Audit-log rows are untouched. [code: app/bundles/UserBundle/Entity/UserToken.php:52 @7.x] [code: app/bundles/CoreBundle/Entity/FormEntity.php:146-153 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:312-314 @7.x]

B37. When the current session is a SAML session, the password fields are removed from the User edit form and from the profile. [code: app/bundles/UserBundle/Controller/UserController.php:366-369 @7.x] [code: app/bundles/UserBundle/Controller/ProfileController.php:235-238 @7.x] [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#managing-passwords-for-saml-authenticated-users]

B38. The "contact user" action emails the target User from the current User's address and writes an audit-log entry with action `communication`. [code: app/bundles/UserBundle/Controller/UserController.php:556-601 @7.x]

B39. User list search commands: `is:admin`, `is:never_logged_in`, `is:published`/`is:unpublished`, `email:`, `name:`, `position:`, `role:`, `username:`, `ids:`. Default order is last name, first name, username. [code: app/bundles/UserBundle/Entity/UserRepository.php:223-327 @7.x] [code: app/bundles/UserBundle/Tests/Functional/Controller/UserControllerFunctionalTest.php:80-120 @7.x]

B40. User pickers (owner lists, `UserListType`) return only published Users; `getUserList` can be limited to Users whose Role has a given `bundle:level` row or is admin. [code: app/bundles/UserBundle/Entity/UserRepository.php:124-144,157-175 @7.x] [code: app/bundles/UserBundle/Form/Type/UserListType.php:52-64 @7.x]

B41. `UserModel::getSystemAdministrator()` returns the first published User of the first admin Role; other bundles use it as a default sender or owner. [code: app/bundles/UserBundle/Model/UserModel.php:159-169 @7.x]

B42. `UserModel::getEntity($id)` always attaches the Role's permission array as `activePermissions`. [code: app/bundles/UserBundle/Model/UserModel.php:138-154 @7.x]

B43. Admin status is a Role flag: `User::isAdmin()` delegates to the Role, and `getRoles()` returns `ROLE_ADMIN` or `ROLE_USER` (plus `ROLE_API` on API requests). [code: app/bundles/UserBundle/Entity/User.php:375-390,624-631 @7.x]

B44. The Users menu entries need `user:users:view`; Roles needs `user:roles:view`; the parent menu shows with either. [code: app/bundles/UserBundle/Config/config.php:6-26 @7.x]

## 4. Invitations (added in 7.2.0)

B45. Inviting needs `user:users:create`. It stores a `UserInvite` with a 16-byte hex selector, a `password_hash` of a 32-byte hex verifier and a 48-hour expiry, revokes every unused invite for the same email, and emails `/invite/{selector}.{verifier}` without queueing. [code: app/bundles/UserBundle/Model/UserModel.php:416-441,487-497 @7.x] [code: app/bundles/UserBundle/Controller/UserController.php:148 @7.x] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html#inviting-a-user-by-email]

B46. An invite link is rejected (warning logged, flash `mautic.user.invite.invalid`, redirect to login) when the token format is wrong, the selector is unknown, the invite is used or expired, or the verifier does not match. [code: app/bundles/UserBundle/Model/UserModel.php:443-475 @7.x] [code: app/bundles/UserBundle/Tests/Model/UserModelTest.php:308-398 @7.x]

B47. Registration through an invite pre-fills email and Role (not editable), asks for username, first and last name, password and optional locale, refuses if a User with that email exists, and marks the invite used before saving the User. [code: app/bundles/UserBundle/Controller/PublicController.php:154-216 @7.x] [code: app/bundles/UserBundle/Tests/Functional/Controller/PublicControllerTest.php:81-116 @7.x]

B48. Deleting a Role deletes its pending invites (`user_invites.role_id` ON DELETE CASCADE). [code: app/bundles/UserBundle/Entity/UserInvite.php:38,63-65 @7.x]

## 5. Profile, preferences, timezone and locale

B49. On the profile page (`/s/account`) name, username, position and email are editable only with `user:profile:editname|editusername|editposition|editemail` (or `full`); other fields are rendered disabled and the stored values override what is submitted. Role and active status are never editable there. [code: app/bundles/UserBundle/Controller/ProfileController.php:40-152,165-168 @7.x] [code: app/bundles/UserBundle/Form/Type/UserType.php:209-241 @7.x]

B50. The profile's API-credentials tab needs `api_enabled` and `api:access:full`. [code: app/bundles/UserBundle/Controller/ProfileController.php:42-43 @7.x]

B51. The profile POST is guarded by a session flag `formProcessed` against double submission. [code: app/bundles/UserBundle/Controller/ProfileController.php:155-157,233 @7.x]

B52. Timezone precedence per request is User → system: the request listener calls `date_default_timezone_set()` with session `_timezone` or `default_timezone` (default `UTC`). [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:30-40 @7.x] [code: app/bundles/CoreBundle/Config/config.php:286 @7.x]

B53. Locale precedence is User → system `locale` (default `en_US`); the Twig language helper also prefers the User locale. [code: app/bundles/CoreBundle/EventListener/EnvironmentSubscriber.php:45-61 @7.x] [code: app/bundles/CoreBundle/Twig/Extension/LanguageExtension.php:52-53 @7.x]

B54. Saving the profile resets session `_timezone` and `_locale` at once; an admin editing another User's timezone/locale takes effect for that User at their next login. [code: app/bundles/UserBundle/Controller/ProfileController.php:198-209 @7.x] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:66-84 @7.x]

B55. Choosing a locale whose language pack is missing triggers a download on save; on failure the User's locale is reset to `null` (system default) with a flash. [code: app/bundles/UserBundle/Controller/ProfileController.php:173-196 @7.x] [code: app/bundles/UserBundle/Controller/UserController.php:280-296,395-417 @7.x]

B56. UI preferences (`theme`, `reduce_transparency`, `reduce_motion`, `contrast_borders`, `enable_underlines`) are stored per User in the serialized `preferences` column; dismissed onboarding elements are not — they live in browser `localStorage['dismissedElements']`. [code: app/bundles/UserBundle/Form/Type/UserPreferencesType.php @7.x] [code: app/bundles/UserBundle/Model/UserModel.php:376-401 @7.x] [code: app/bundles/CoreBundle/Assets/js/1.core.js:148-165 @7.x]

B57. The User `signature` defaults to the translated default signature with `|FROM_NAME|`; when an email is sent as the Contact owner ("Mailer is owner"), `{signature}` is the owner's signature with `|FROM_NAME|` → "First Last" and `|USER_<COLUMN>|` → that User column. Signature HTML is purified on input. [code: app/bundles/UserBundle/Form/Type/UserType.php:42,187-207 @7.x] [code: app/bundles/EmailBundle/Helper/FromEmailHelper.php:115-137 @7.x] [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:213-222 @7.x]

## 6. Roles

B58. A Role with Full System Access (`is_admin = 1`) stores no `permissions` rows; the raw array is still saved in `readable_permissions`. Admin Users pass every permission check. [code: app/bundles/UserBundle/Model/RoleModel.php:77-93 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:220-222 @7.x] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#full-system-access]

B59. Saving an existing Role deletes all its permission rows and recreates them from the submitted raw array, then invalidates the `Role` and `User` result caches. [code: app/bundles/UserBundle/Model/RoleModel.php:56-70 @7.x] [code: app/bundles/UserBundle/Entity/PermissionRepository.php:18-27 @7.x] [code: app/bundles/UserBundle/Entity/Role.php:302-308 @7.x]

B60. The raw permission array is keyed `bundle:name => [level, …]`, for example `['lead:leads' => ['full'], 'user:profile' => ['editname']]`. This is also the `rawPermissions` format of the Roles API. [code: app/bundles/UserBundle/DataFixtures/ORM/LoadRoleData.php:42-46 @7.x] [code: app/bundles/UserBundle/Controller/Api/RoleApiController.php:60-65 @7.x]

B61. An unknown level in the raw array throws `InvalidArgumentException("<perm> does not exist for <bundle>:<name>")` at save. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:149-171 @7.x]

B62. Implied levels are added to the stored bits at save but are not added to `readable_permissions`, so API consumers reading `rawPermissions` do not see them (see B79). [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:214-255 @7.x] [code: app/bundles/UserBundle/Model/RoleModel.php:92 @7.x]

B63. A Role that still has Users cannot be deleted (single or batch); flash "%name% cannot be deleted because it still has users assigned to it". The `users.role_id` FK has no ON DELETE. Deleting an empty Role cascades its permission rows and invites. [code: app/bundles/UserBundle/Model/RoleModel.php:98-110 @7.x] [code: app/bundles/UserBundle/Controller/RoleController.php:547-552,590-603 @7.x] [code: app/bundles/UserBundle/Entity/User.php:197-201 @7.x]

B64. Cloning a Role opens the form pre-filled with "Clone of %name%", the description, the admin flag and the raw permissions; nothing is stored until saved. Cloning needs `user:roles:create` and `user:roles:view`. [code: app/bundles/UserBundle/Model/RoleModel.php:134-145 @7.x] [code: app/bundles/UserBundle/Controller/RoleController.php:20-26,213-341 @7.x] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#cloning-a-role]

B65. In the Role form, ticking `full` unticks the other levels of that permission and ticking any other level unticks `full`; each tab shows `granted / total`, where `full` counts as all other levels. With Full System Access = Yes the matrix is hidden. [code: app/bundles/UserBundle/Assets/js/user.js:79-147 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:262-294 @7.x] [code: app/bundles/UserBundle/Resources/views/Role/form.html.twig:47-99 @7.x]

B66. The Role list shows a per-Role User count, sortable as `user_count`. [code: app/bundles/UserBundle/Entity/RoleRepository.php:20-35 @7.x] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#sorting-roles-by-the-number-of-users]

B67. Role search commands: `is:admin`, `name:`. [code: app/bundles/UserBundle/Entity/RoleRepository.php:97-129,175-183 @7.x]

B68. On upgrade to 7.2.0, migration `Version20260501090000` gives every non-admin Role that has `lead:leads` levels but no `lead:notes` entry a mapped `lead:notes` set, so Notes access matches Contact access. [code: app/migrations/Version20260501090000.php @7.x] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#contact-permissions]

## 7. Permission evaluation framework

B69. A permission string is `bundle:name:level` (for example `lead:leads:viewother`). `isGranted()` accepts 3 or 4 colon parts but only uses the first three; any other count throws `PermissionBadFormatException` (code 403). `bundle` is the permission class's `getName()`, not the Symfony bundle name. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-218,227-245 @7.x] [code: app/bundles/CoreBundle/Security/Exception/PermissionException.php:9 @7.x]

B70. Admin bypass: for an admin User every well-formed string is granted without consulting permission classes, even for levels that do not exist. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:220-222 @7.x]

B71. For non-admins, an unsupported `name:level` throws `PermissionNotFoundException` unless `$allowUnknown = true`, which returns false. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:227-235 @7.x]

B72. A non-admin with no stored row for the bundle is denied every permission of that bundle. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:241-243 @7.x]

B73. Grant test: if the permission name has a `full` level and the stored bits include the `full` bit, every level is granted; otherwise the result is `(levelBit & storedBits) != 0`. `full` is a superset flag, not the OR of the other bits. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:190-207 @7.x]

B74. Bit values. Standard set: view 4, edit 16, create 32, delete 128, publish 512 (optional), full 1024. Extended set: viewown 2, viewother 4, editown 8, editother 16, create 32, deleteown 64, deleteother 128, publishown 256, publishother 512 (publish optional), full 1024. Manage set: manage 1024. A Role's stored `bitwise` is the sum of the ticked bits. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:334-352,408-419,455-477 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:149-169 @7.x]

B75. Synonyms: on an extended permission, asking for `view`/`edit`/`delete`/`publish` tests `viewown`/`editown`/`deleteown`/`publishown`; on a standard permission, asking for `viewown` or `viewother` tests `view` (same for edit/delete/publish). [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:144-181 @7.x]

B76. Consequence of B75: `user:users` and `user:roles` are standard, so there is no "own users only" level — `user:users:edit` lets a User edit any User, including admins. [code: app/bundles/UserBundle/Security/Permissions/UserPermissions.php:26-27 @7.x] [code: app/bundles/UserBundle/Controller/UserController.php:131-132,320 @7.x]

B77. Own/other resolution for a record (`hasEntityAccess(own, other, ownerId)`): guest → false; owner id 0 or null → the "other" permission decides; owner is the current User → the "own" permission decides; any other owner → the "other" permission decides. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:335-379 @7.x]

B78. Publish access (`hasPublishAccessForEntity`): a new record needs the own-publish permission; an existing record compares the current User with `getPermissionUser()` if defined, else `getCreatedBy()`. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:300-326 @7.x]

B79. Implied levels added at Role save (`analyzePermissions`): edit*/publish* ⇒ viewother + viewown; delete* ⇒ editother + viewother + viewown; viewother, editown, deleteown, publishown, create ⇒ viewown; any view level ⇒ `categories:view` when the class defines `categories`. Only levels the permission supports are added. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:214-255 @7.x]

B80. `LeadPermissions` adds `lead:leads:viewown` when Segments, Notes or Custom Fields access is granted and Contacts view access is not already complete. [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php:88-101 @7.x]

B81. A permission class may return `true` from `analyzePermissions()` to request a second pass after every class has been analysed. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:137-146 @7.x]

B82. `isGranted()` with an array: `MATCH_ALL` (default) needs every string granted; `MATCH_ONE` needs one; `RETURN_ARRAY` returns a map; any other mode throws `PermissionNotFoundException`. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:252-263 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions]

B83. Results are memoised per permission string for the life of the `CorePermissions` service, regardless of the `$userEntity` argument; `reset()` does not clear them. Checking a second User's permission in the same request returns the first User's result. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:39-42,210-213,249 @7.x]

B84. A permission class implementing `VirtualPermissions` is answered by `isVirtuallyGranted()` before any stored bits are examined. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:239-240 @7.x] [code: app/bundles/CoreBundle/Tests/Functional/Security/Permissions/CorePermissionsTest.php:27-40 @7.x]

B85. `checkPermissionExists()` accepts exactly 3 parts and never throws for unknown bundles. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:287-293 @7.x]

B86. `definePermissions()` runs every time the class is fetched and only when `isEnabled()` is true; disabled classes (for example Marketplace when disabled) disappear from the Role form, and stored bits for missing permissions are dropped when the form is rebuilt. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:100-102 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:63-66,101-134 @7.x]

B87. Permission classes are found by the `mautic.permissions` service tag or, deprecated, by scanning `Security/Permissions/*Permissions.php` in every core bundle and plugin. [code: app/bundles/CoreBundle/DependencyInjection/Compiler/PermissionsPass.php:12-20 @7.x] [code: app/bundles/CoreBundle/DependencyInjection/Builder/Metadata/PermissionClassMetadata.php:20-51 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:446-462,482-495 @7.x]

B88. The guest User returned by `UserHelper::getUser()` when no one is logged in has no permissions and `isAdmin()` false; anonymous access is denied by the "no bundle row" branch. [code: app/bundles/CoreBundle/Helper/UserHelper.php:20-38 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:236-243 @7.x]

B89. Configuration and System Info are admin-only (not permission-based). [code: app/bundles/ConfigBundle/Controller/ConfigController.php:41,207,242 @7.x] [code: app/bundles/ConfigBundle/Controller/SysinfoController.php:23 @7.x]

B90. The audit-log stats table (`/api/stats/audit_log`) and the audit-log report are admin-only; the report excludes the `config` object because it may contain passwords. [code: app/bundles/CoreBundle/EventListener/CommonStatsSubscriber.php:56-93 @7.x] [code: app/bundles/CoreBundle/EventListener/ReportSubscriber.php:84,179-183 @7.x]

## 8. API authentication and the Users/Roles API

B91. On the `api` firewall OAuth2 bearer, HTTP Basic and plugin authenticators all resolve to the same `User` entity, and the token's User gets `activePermissions` attached. API permissions are therefore the User's Role permissions. [code: app/config/security.php:51-67 @7.x] [code: app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php:30-63 @7.x]

B92. OAuth2 client-credentials tokens (no User) get a pseudo-User whose Role is the API client's Role, named `"<client name> [<client id>]"`; `MAUTIC_AUDITLOG_USER` is defined with that name so audit rows and `created_by_user` show the client. [code: app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php:68-95 @7.x] [code: app/bundles/UserBundle/EventListener/ApiUserSubscriber.php:50-71 @7.x]

B93. Weak-password rejection also applies to HTTP Basic API logins and returns 401. [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:109-128 @7.x]

B94. Legacy Users API: `GET /api/users`, `GET /api/users/{id}`, `POST /api/users/new`, `POST /api/users/batch/new`, `PUT|PATCH /api/users/{id}/edit`, `PUT|PATCH /api/users/batch/edit`, `DELETE /api/users/{id}/delete`, `DELETE /api/users/batch/delete`. Roles have the same set on `/api/roles`. [code: app/bundles/UserBundle/Config/config.php:78-104 @7.x] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:123-200 @7.x]

B95. `GET /api/users/self` returns the authenticated User (unwrapped, with Role and `rawPermissions`). [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:64-70 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#get-current-user]

B96. `POST /api/users/{id}/permissioncheck` with `permissions` (string or array) returns a map evaluated for that User (admin bypass applies). [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:173-193 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#verify-user-permissions]

B97. `GET /api/users/list/roles` needs `user:users:create` or `user:users:edit`. [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:198-217 @7.x]

B98. `POST /api/users/new` needs `user:users:create`; edits need `user:users:edit`; `PUT` on a missing id also needs `create`. [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:79,106-112 @7.x]

B99. On an existing User the legacy API silently ignores password changes (`plainPassword` dropped) and username changes (dropped on PATCH, replaced with the stored value on PUT); PUT also preserves the Role. [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:122-139 @7.x]

B100. Validation failures (missing fields, weak password, duplicate username) return 400; permission failures 403; unknown id 404. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#common-error-responses] [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:130-156 @7.x]

B101. `POST /api/roles/new` accepts `rawPermissions` in the B60 format and converts it with `setRolePermissions`. [code: app/bundles/UserBundle/Controller/Api/RoleApiController.php:60-65 @7.x]

B102. API Platform v2: `/api/v2/users`, `/api/v2/roles`, `/api/v2/permissions`. Collection GET needs `…:viewown`, POST needs `…:create`, item GET/PUT/PATCH/DELETE use `viewown`/`editown`/`editother`/`deleteown` evaluated against the object. [code: app/bundles/UserBundle/Entity/User.php:28-46 @7.x] [code: app/bundles/UserBundle/Entity/Role.php:26-44 @7.x]

B103. API Platform `POST /api/v2/users` hashes `plainPassword` in `UserProcessor`; `password` is never in the read group. [code: app/bundles/UserBundle/ApiPlatform/UserProcessor.php:23-32 @7.x] [code: app/bundles/UserBundle/Entity/User.php:54-149 @7.x]

B104. The API Platform voter maps any `…own`/`…other` attribute with an object subject onto `hasEntityAccess`, resolving the owner via `getPermissionUser()` → `getCreatedBy()` → `getOwner()`; `mautic.api_platform_permission_context` can rewrite the permission or subject first. [code: app/bundles/ApiBundle/Security/Voter/ApiPermissionVoter.php:30-60,93-115 @7.x]

## 9. Plugin, SSO and SAML authentication

B105. A login POST that includes an `integration` field is handled by `SsoAuthenticator` (runs before form login) which dispatches `mautic.user_form_authentication`; listeners may call `setIsAuthenticated()` (optionally creating the User) or `setIsFailedAuthentication()` with a message to block local password login. [code: app/bundles/UserBundle/Security/Authenticator/SsoAuthenticator.php:71-164 @7.x] [code: app/bundles/UserBundle/Event/AuthenticationEvent.php:96-181 @7.x]

B106. Requests on the `sso_login`, `api` and `v2api` firewalls run `PluginAuthenticator`, which dispatches `mautic.user_pre_authentication` unless a bearer token is present. With no listener result on the API firewalls it returns `null` so the next authenticator runs. [code: app/bundles/UserBundle/Security/Authenticator/PluginAuthenticator.php:48-52,66-79,112-120,189-200 @7.x] [code: app/config/security.php:22-27,51-67 @7.x]

B107. `/s/sso_login/{integration}` is public; the login check sets `isLoginCheck()` on the event, and an empty JSON response is returned if nothing authenticated. The login page lists `sso_service` integrations as links. [code: app/bundles/UserBundle/Security/Authenticator/PluginAuthenticator.php:69-78,106-109 @7.x] [code: app/bundles/UserBundle/Controller/SecurityController.php:83-84,103-115 @7.x]

B108. Users created by SSO plugins (`UserProvider::saveUser`) must have role, username, email, first and last name; a missing password gets a random one; `USER_PRE_SAVE`/`USER_POST_SAVE` fire. [code: app/bundles/UserBundle/Security/Provider/UserProvider.php:90-145 @7.x]

B109. SAML is "enabled" when `saml_idp_metadata` (base64 IdP XML) is non-empty. [code: app/bundles/UserBundle/Security/SAML/Helper.php:18-27 @7.x] [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#turning-on-saml]

B110. A SAML assertion is mapped to a User (email as username unless a username attribute is configured). A matching User (by username or email) is logged in; otherwise a User is created with `saml_idp_default_role`, or login fails "User does not exist." when no default Role is set. [code: app/bundles/UserBundle/Security/SAML/User/UserMapper.php:38-59 @7.x] [code: app/bundles/UserBundle/Security/SAML/User/UserCreator.php:34-67 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#saml-sso-settings]

B111. The SP endpoints are `/saml/metadata.xml`, `/saml/discovery`, `/s/saml/login` and ACS `/s/saml/login_check`. [code: app/bundles/UserBundle/Config/config.php:28-131 @7.x] [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#configuring-the-idp]

B112. SAML request state lives in the cache for 2 minutes; `/saml/login_retry` invalidates the session and offers a retry link when SAML is enabled, else redirects to login. [code: app/bundles/UserBundle/Security/SAML/Store/RequestStateStore.php:23-34 @7.x] [code: app/bundles/UserBundle/Controller/SecurityController.php:118-138 @7.x] [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#recovering-from-a-login-error]

B113. With an own certificate configured, AuthnRequests and assertions are signed and encrypted; without one a self-signed dummy cert is generated in `cache_path` and nothing is signed. [code: app/bundles/UserBundle/Security/SAML/Store/TrustOptionsStore.php:39-54 @7.x] [code: app/bundles/UserBundle/Security/SAML/Store/CredentialsStore.php:36-87 @7.x]

B114. Uploaded IdP metadata is validated as XML and the cert/key pair validated on config save; a blank key password keeps the stored one. [code: app/bundles/UserBundle/EventListener/ConfigSubscriber.php:48,60-86 @7.x]

B115. When env `MAUTIC_SAML_ENABLED` is not true, `SAMLSubscriber` is removed from the container; when present it redirects any `/saml/*` or `lightsaml*` route to `login`. `/s/login` stays reachable directly. [code: app/bundles/UserBundle/EventListener/SAMLSubscriber.php:31-48 @7.x] [code: app/bundles/UserBundle/DependencyInjection/MauticUserExtension.php:23-26 @7.x] [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#logging-in]

## 10. Audit log of user actions

B116. Every interactive login writes an audit row: bundle `user`, object `security`, action `login`, with username and IP. [code: app/bundles/UserBundle/EventListener/SecuritySubscriber.php:28-43 @7.x]

B117. User create/update/delete write rows with bundle `user`, object `user`, and the changed fields; Role changes on a User are logged as `"Name (id)"`. [code: app/bundles/UserBundle/EventListener/UserSubscriber.php:34-66 @7.x] [code: app/bundles/UserBundle/Entity/User.php:316-334 @7.x]

B118. Role create/update/delete write rows with object `role`; the change log includes `rawPermissions` diffs. [code: app/bundles/UserBundle/EventListener/UserSubscriber.php:71-102 @7.x] [code: app/bundles/UserBundle/Entity/Role.php:262-266 @7.x]

B119. Logout, failed logins and password resets are not audit-logged (no listener writes them). [code: app/bundles/UserBundle/EventListener/SecuritySubscriber.php:28-43 @7.x] [code: app/bundles/UserBundle/EventListener/LogoutListener.php:25-32 @7.x]

B120. Audit rows written under an OAuth2 client-credentials token carry the client name (B92). [code: app/bundles/UserBundle/Security/Authentication/Token/Permissions/TokenPermissions.php:68-95 @7.x]

B121. `mautic:maintenance:cleanup` purges `audit_log` rows older than `--days-old` in batches of 10,000 and writes its own row `core/maintenance/cleanup` by user `system` (id 0). [code: app/bundles/CoreBundle/EventListener/MaintenanceSubscriber.php:29-81 @7.x] [code: app/bundles/CoreBundle/Command/CleanupMaintenanceCommand.php:160-179 @7.x]

B122. `mautic:anonymize:ip` (requires `anonymize_ip`) anonymises IPs in `audit_log` as well as `ip_addresses`. [code: app/bundles/CoreBundle/Command/AnonymizeIpCommand.php:37-43 @7.x]

B123. The `recent.activity` dashboard widget reads the audit log. [code: app/bundles/CoreBundle/EventListener/DashboardSubscriber.php:52-106 @7.x]

## 11. Defaults, fixtures and CLI acting-as-user

B124. The installer creates the Role "Administrators" (`is_admin = 1`) and the admin User as id 1 from the install form. [code: app/bundles/InstallBundle/InstallFixtures/ORM/RoleData.php:24-38 @7.x] [code: app/bundles/InstallBundle/Install/InstallService.php:415-460 @7.x]

B125. Dev/test fixtures add Users `admin` and `sales` (password `Maut1cR0cks!`) and a "Sales Team" Role with `user:profile:editname` and `lead:leads:full`. [code: app/bundles/UserBundle/DataFixtures/ORM/LoadRoleData.php @7.x] [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php @7.x]

B126. CLI or background code that must act as a User calls `UserTokenSetter::setUser($id)`; otherwise `UserHelper::getUser()` returns a guest with no permissions. [code: app/bundles/UserBundle/Security/UserTokenSetter.php:18-25 @7.x] [code: app/bundles/CoreBundle/Helper/UserHelper.php:20-38 @7.x]

B127. There is no two-factor authentication in core; `AuthenticationEvent::setIsFailedAuthentication()` is the hook a 2FA plugin would use. There are no `mautic:user:*` console commands. [code: app/bundles/UserBundle/Event/AuthenticationEvent.php:171-181 @7.x]
