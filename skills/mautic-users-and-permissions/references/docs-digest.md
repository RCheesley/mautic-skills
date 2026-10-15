# Users, roles, permissions — what the official docs say

Sources: user docs 7.2 (`users_roles/managing_roles`, `users_roles/managing_users`, `authentication/authentication`,
`configuration/settings`), devdocs 7.2 (`plugins/permissions`, `plugin_services/security`,
`design/displaying_elements_based_on_user_permissions`, `rest_api/users`, `rest_api/roles`). Where the code disagrees, the
code wins; discrepancies are flagged with **Code differs** and repeated in SKILL.md Pitfalls.

## 1. Roles (user docs)

- Users are accounts; Roles allow or deny access to features. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html]
- Roles list is at Settings > Roles with columns Name, Description, User Count (badge "View X Users" opens the filtered Users list; "No Users" if none) and ID; User Count is sortable. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#roles-overview] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#sorting-roles-by-the-number-of-users]
- **Full System Access = Yes** creates an Administrator Role; the Permissions tab is then not configurable. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#full-system-access]
- Granular Roles: Full System Access = No, then tick levels per area. Most areas offer View, Edit, Create, Delete, Publish ("Active"/"Activate"), and **Full** selects every checkbox. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#setting-granular-permissions]
- Ownership levels: **Own** (own resources), **Others** (own + others'). [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#explaining-the-permission-options]
- The docs also describe a **Same Role** level (own + Users sharing the Role) for Assets, Campaigns, Marketing Messages, Dynamic Content, Emails, Focus Items, Forms, Landing Pages, Reports and Segments, with check order Others → Same Role → Own. **Code differs:** no same-role level exists in the 7.2.1 or 8.x trees (grep for `samerole|same_role|sameRole` finds nothing); the extended set is own/other only. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#where-same-role-permissions-apply] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#combining-permission-levels] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:455-477 @7.x]
- **Manage** level for resources such as Custom Fields or Plugins. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#explaining-the-permission-options]
- Users section edit permissions: **Specified fields** (Name, Username, Email, Position) or **All** — this is the `user:profile` permission. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#explaining-the-permission-options] [code: app/bundles/UserBundle/Security/Permissions/UserPermissions.php:18-25 @7.x]
- **Export** exists for Contacts, Forms and Reports; without it a User cannot see or use export. (Code also defines `campaign:export`.) [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#explaining-the-permission-options] [code: app/bundles/CampaignBundle/Security/Permissions/CampaignPermissions.php:21 @7.x]
- **Send to unsubscribed contacts** controls whether the User can enable that toggle in an Email's advanced settings (transactional mail). [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#explaining-the-permission-options]
- Contact permission areas: Contacts, Notes, Segments, Custom Fields (manage), Import. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#contact-permissions]
- Notes permissions follow **Note ownership**, not Contact ownership; "Edit own" Notes allows editing own Notes on Contacts owned by others. On upgrade each non-admin Role receives the Notes access it had for Contacts. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#contact-permissions]
- Cloning: the clone icon (only shown with Roles **Create**) opens the edit screen pre-filled with "Clone of [name]", description, Full System Access and permissions; nothing is created until saved. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#cloning-a-role]
- "By default Mautic creates new Users with the Administrator Role." **Code differs (partly):** the Role field has no default value; it lists published Roles ordered by name, so on a fresh install the only option is "Administrators". [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html] [code: app/bundles/UserBundle/Form/Type/UserType.php:209-224 @7.x]

## 2. Users (user docs)

- Users are managed at Settings > Users, manually or via API. Fields: first/last name, Role, signature (used for "Mailer is owner"), position, username, email, password, time zone, language. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html]
- Passwords need at least six characters; mixing case, digits and symbols is "recommended". **Code differs:** a strength check (zxcvbn ≥ 3) is enforced, not just recommended. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html] [code: app/bundles/UserBundle/Model/PasswordStrengthEstimatorModel.php:14-44 @7.x]
- Users reset passwords with "Forgot password"; admins can set passwords manually. Mautic does not email credentials to manually created Users. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html]
- When logged in through SAML, password fields are hidden on User forms. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html]
- A User's time zone is used for Email scheduling and other features. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html]
- **Invite your team** (Users page or profile menu) needs Users **Create**; enter email and Role. The link expires after 48 hours; re-inviting invalidates earlier invitations; only addresses not belonging to an existing User can be invited. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html#inviting-a-user-by-email]
- The registration form pre-fills email and Role; the invitee supplies username, names, password + confirmation and language; **Create Account** redirects to login. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html#completing-the-invitation]
- (8.0 docs) "Never logged in" quick filter and `is:never_logged_in`. The code is on the 7.x branch head, not in the 7.2.1 tag, and not yet on 8.x. [docs: https://docs.mautic.org/en/8.0/users_roles/managing_users.html#filtering-users-who-have-never-logged-in] [code: app/bundles/UserBundle/Entity/UserRepository.php:248-249,310 @7.x]
- Installer: "Mautic requires a complex admin password from version 5.1"; DDEV default login `admin` / `Maut1cR0cks!`. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev]

## 3. SAML authentication (user docs)

- Mautic login is the default; SAML SSO is optional. Turn it on by uploading IdP metadata XML at Configuration > User/Authentication Settings and choosing a Default Role (recommended non-admin). An empty Default Role means SSO creates no Users. [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#turning-on-saml] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#saml-sso-settings]
- SP values: Entity ID = site URL shown at the top of the settings; SP metadata `https://example.com/saml/metadata.xml`; ACS `https://example.com/s/saml/login_check`; Issuer without scheme. With a custom domain set Site URL to match. [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#configuring-the-idp]
- Required IdP attributes: email, first name, last name; username optional. [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#configuring-the-idp]
- Once enabled, logins redirect to the IdP; `/s/login` still works directly; Users are auto-created on first login. **Code note:** the redirect of all unauthenticated `/s/*` requests to the IdP happens only when env `MAUTIC_SAML_ENABLED` is true; with only metadata set, unauthenticated requests still go to `/s/login`. [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#logging-in] [code: app/bundles/UserBundle/Security/EntryPoint/MainEntryPoint.php:21-34 @7.x]
- On SAML failure (expired session, "Unknown Response") Mautic clears the session and shows a retry screen. [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#recovering-from-a-login-error]
- Turn SAML off with **Remove** beside the IdP metadata file. [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html#turning-off-saml]
- Optional X.509 certificate, private key and key password sign requests. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#saml-sso-settings]

## 4. Developer docs: permissions

- Bits double (1, 2, 4, …, 1024); a Role stores the sum of granted bits and a permission is granted when the stored value includes the requested bit; `full` must be the highest bit and grants everything in the level. (The devdocs list skips 256, which the extended set uses for `publishown`.) [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#how-permissions-work] [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:455-477 @7.x]
- Notation `bundleName:permissionLevel:permission`. The devdocs say plugins prefix `plugin:`. **Code differs:** `CorePermissions::isGranted()` uses the first part as the permission class name and ignores a 4th part, so `plugin:helloWorld:items:view` resolves against the core `plugin` class and fails; plugin permissions are checked as `helloWorld:items:view`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:215-245 @7.x]
- `isGranted(array)` needs all; `'MATCH_ONE'` needs one; `'RETURN_ARRAY'` returns a map. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions]
- Security service: `mautic.security` (7.2) = `CorePermissions`; 8.0 docs fetch it by class. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/security.html#using-permissions]
- Permission classes extend `AbstractPermissions` and implement the constructor, `buildForm()` and `getName()`; `getName()` must match the bundle name in camelCase and the file name (`HelloWorldBundle` → `helloWorld`, `HelloWorldPermissions.php`). [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#creating-custom-permissions] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#getname]
- Helpers: `addStandardPermissions()`, `addExtendedPermissions()`, `addManagePermission()`; form helpers `addStandardFormFields()`, `addExtendedFormFields()`, `addManageFormFields()`; custom fields use the permission list form type named `bundleName:permissionLevel`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/security.html#creating-custom-permissions]
- 7.2 registration: `services.permissions` group in `config.php`; 8.0: `$services->set(Class)` in `Config/services.php`, autoconfigured with tag `mautic.permissions`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_services/security.html#creating-custom-permissions] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html#registering-the-permission-class-as-a-service]
- `getSynonym($name, $level)` runs before each check; `analyzePermissions(&$permissions, $allPermissions, $isSecondRound)` adjusts before save and may request a second round; `isGranted()` and `isSupported()` can be overridden. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#permission-aliases] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#manipulating-permissions-before-saving] [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#advanced-isgranted-logic]
- Hide UI with `{% if securityIsGranted('bundle:level:perm') %}` and still enforce on the backend. [devdocs: https://devdocs.mautic.org/en/7.2/design/displaying_elements_based_on_user_permissions.html]
- Devdocs not covered: admin bypass, per-request caching. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html]

## 5. REST API: Users and Roles (devdocs)

- `GET /users/ID` returns `user` with isPublished, audit fields, id, username, firstName, lastName, email, position, role (id, name, description, isAdmin, rawPermissions), timezone, locale, lastLogin, lastActive, signature. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#get-user]
- `rawPermissions` maps `bundle:group` to actions, e.g. `"asset:assets": ["viewown","editown","create","deleteown"]`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#get-current-user]
- `GET /users` accepts search, start, limit, orderBy, orderByDir, publishedOnly, minimal. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#list-users]
- `POST /users/new` — documented required: firstName, lastName, username, email, plainPassword `{password, confirm}`, role (id), timezone, locale; optional isPublished (default 1), position, signature. **Code differs:** timezone and locale are not required (the functional test creates a User without them and gets 201). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#create-user] [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:130-156 @7.x]
- `PUT /users/ID/edit` creates if missing; `PATCH` returns 404 if missing. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#edit-user]
- Delete is documented as `DELETE /users/ID` with no `/delete` suffix. **Code differs:** the standard route is `DELETE /api/users/{id}/delete`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#delete-user] [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:123-200 @7.x]
- `GET /users/self` is not wrapped in a `user` key and includes full `rawPermissions`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#get-current-user]
- `POST /users/ID/permissioncheck` with `permissions` array returns a permission → boolean map. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#verify-user-permissions]
- `GET /users/list/roles` takes `filter` and `limit`, returns a bare array of `{id, name}`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#list-user-roles]
- Errors: 400 validation (including weak password, duplicate username), 401 authentication required or "weak password detected", 403 permissions, 404 not found, 500 unexpected. Weak-password message: "Please enter a stronger password. Your password must use a combination of upper and lower case, special characters and numbers." The 401 applies when the *authenticating* User's password is weak (HTTP Basic). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#common-error-responses] [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:109-128 @7.x]
- The Roles API page is a stub pointing to the legacy docs repository. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/roles.html]

## 6. Procedures

- **Create an Administrator Role**: Settings > Roles > New; name, description; Full System Access = Yes; Save & Close. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#full-system-access]
- **Create a granular Role**: as above with Full System Access = No; tick levels in the Permissions tab. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#setting-granular-permissions]
- **Clone a Role**: clone icon on the row, edit, Save & Close. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#cloning-a-role]
- **Create a User**: Settings > Users > New; fill the fields; share the credentials yourself. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html]
- **Invite a User**: Settings > Users > Invite your team; email + Role; the invitee completes the form within 48 h. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html#inviting-a-user-by-email]
- **Turn on SAML**: save IdP metadata XML, upload under User/Authentication Settings, choose a default non-admin Role, give the IdP the Entity ID / SP metadata / ACS URLs, map attributes, optionally upload cert and key. [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html]
- **Add a plugin permission**: create `Security/Permissions/<Bundle>Permissions.php` extending `AbstractPermissions`, define levels, implement `buildForm()` and `getName()`, register, check with `isGranted('<name>:<level>:<perm>')`. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#creating-custom-permissions]

## 7. Terminology

- Docs capitalise product nouns: User, Role, Contact, Segment, Email, Landing Page, Custom Field(s), Notes, Plugin. "Full System Access" = Administrator. "Mailer is owner" is the feature that uses the owner's signature. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html]
- Permission labels in the UI: View, Edit, Create, Delete, Publish/Activate, Full, Own, Others, Manage, Export (docs use "Active", "Activate" and "Publish" interchangeably). [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#explaining-the-permission-options]
- Code identifiers keep legacy names: `lead:leads` = Contacts, `lead:lists` = Segments, `page:pages` = Landing Pages. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/permissions.html#using-permissions]

## 8. Gaps in the docs

- No full permission matrix; rely on code-map.md §8. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html]
- No docs on account lockout/throttling, 2FA, user deactivation, last-login tracking, or how Role changes affect logged-in sessions. [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html]
- SAML docs do not say how existing Users are matched (code: username or email). [docs: https://docs.mautic.org/en/7.2/authentication/authentication.html] [code: app/bundles/UserBundle/Security/SAML/User/UserCreator.php:34-67 @7.x]
