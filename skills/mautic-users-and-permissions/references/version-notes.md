# Users, roles, permissions — version notes

Authoritative behaviour is 7.x (commit 419a08a9b35: release 7.2.1 plus unreleased merged PRs). 8.x is unreleased development.

## 1. History that explains current behaviour (5.x / 6.x)

- 5.1.0: the zxcvbn password-strength model (`PasswordStrengthEstimatorModel`) was introduced; the install docs say a complex admin password is required "from version 5.1". Before 5.1 the only rule was the 6-character minimum. [code: app/bundles/UserBundle/Model/PasswordStrengthEstimatorModel.php @7.2.1 — file first added in the commit tagged 5.1.0] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line]
- DDEV default login was `mautic` before 5.1 and `Maut1cR0cks!` since. [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev]
- No other 5.x/6.x differences for this area are recorded in the analysis inputs. [unverified]

## 2. 7.x minors

| Version | Change | Source |
|---|---|---|
| 7.0.0 | `TimingSafeFormLoginAuthenticator` (constant-time login for unknown users) added. | [code: app/bundles/UserBundle/Security/TimingSafeFormLoginAuthenticator.php @7.2.1 — first tagged 7.0.0] |
| 7.0.0 | `project:project` permission (Projects, with `associate` = 8) added. | [code: app/bundles/ProjectBundle/Security/Permissions/ProjectPermissions.php:32-35 @7.2.1 — first tagged 7.0.0] |
| 7.2.0 | User invitations (`user_invites`, `/invite/{token}`, 48 h links). | [code: app/bundles/UserBundle/Entity/UserInvite.php @7.2.1 — first tagged 7.2.0] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_users.html#inviting-a-user-by-email] |
| 7.2.0 | `lead:notes` permission; migration `Version20260501090000` copies each non-admin Role's Contact levels to Notes. | [code: app/migrations/Version20260501090000.php @7.2.1 — first tagged 7.2.0] [docs: https://docs.mautic.org/en/7.2/users_roles/managing_roles.html#contact-permissions] |
| 7.2 | Service aliases `mautic.security.logout_handler` and `mautic.security.user_token_setter` deprecated. | [code: app/bundles/UserBundle/Config/services.php:131-134 @7.x] |
| 7.x head (after 7.2.1 tag) | `is:never_logged_in` search command and "Never logged in" quick filter. | [code: app/bundles/UserBundle/Entity/UserRepository.php:248-249,310 @7.x] [docs: https://docs.mautic.org/en/8.0/users_roles/managing_users.html#filtering-users-who-have-never-logged-in] |

## 3. 8.x delta

Branch topology: 7.2.1 is not merged into 8.x yet; `is:never_logged_in` is present on 7.x and absent on 8.x until the next forward merge. [code: app/bundles/UserBundle/Entity/UserRepository.php @8.x]

| Change | What to do | Source |
|---|---|---|
| `UserEvents` class deleted. Event classes: `LoginEvent` (final), `LogoutEvent`, `PreAuthenticationEvent`, `FormAuthenticationEvent`, `AuthenticationContentEvent`, `PasswordStrengthValidateEvent`, `PreSaveUserEvent`/`PostSaveUserEvent`/`PreDeleteUserEvent`/`PostDeleteUserEvent`, `PreSaveRoleEvent`/`PostSaveRoleEvent`/`PreDeleteRoleEvent`/`PostDeleteRoleEvent`. `USER_FORM_POST_LOCAL_PASSWORD_AUTHENTICATION` has no replacement (never dispatched). | Subscribe by event class. For code that must run on 7.x and 8.x, guard with `class_exists()` and type-hint the shared parent (`UserEvent`, `RoleEvent`, `AuthenticationEvent`). | [PR #17217] [PR #17510] [PR #17623] [PR #17654] [code: app/bundles/UserBundle @8.x] |
| `AuthenticationEvent`, `UserEvent`, `RoleEvent` become `abstract`. | Instantiate the concrete subclass. | [code: app/bundles/UserBundle/Event @8.x] |
| `AuthenticationEvent` setters take `bool` params. | Pass real booleans. | [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html] |
| `AbstractPermissions::definePermissions()` removed — define levels in the constructor; the `array $params` constructor argument is deprecated (params arrive via autowired `setCoreParametersHelper()` after construction, so not inside the constructor). Permission classes are services autoconfigured with `mautic.permissions`; `PermissionsPass` removed; `CorePermissions` receives them by `AutowireIterator`. Unregistered classes still work through a deprecated fallback. | Register the class in `Config/services.php`; move level definitions to the constructor. | [PR #17079] [PR #17121] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html#registering-the-permission-class-as-a-service] |
| Native types on `AbstractPermissions`: `getPermissions(): array`, `getSynonym(): array`, `getPermissionRatio(): array`, `isGranted(array $userPermissions, $name, $level): bool`, form helpers take `array $data`. | Copy parent signatures exactly in overrides. | [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html] |
| Service ids removed: `mautic.security`, `mautic.user.provider` (and others). | Inject `CorePermissions::class` / the provider class. | [PR #16875] [PR #17124] [PR #17134] |
| `config.php` `services` groups (including `permissions`) no longer read. | Use `Config/services.php`. | [PR #17470] [PR #17116] [PR #17117] |
| SAML bundle swapped from `javer/sp-bundle ^2.0` to `lightsaml2/sp-bundle ^5.0` + `lightsaml2/symfony-bridge ^6.0` (+ pinned `lightsaml2/lightsaml`). Behaviour intended unchanged. | Re-test IdP login, metadata and ACS on 8.x. | [PR #17370] |
| `Role::getRawPermissions(): ?array`; `oAuth2\Client::getRole(): ?Role`. | Handle `null`. | [code: app/bundles/UserBundle/Entity/Role.php @8.x] [code: app/bundles/ApiBundle/Entity/oAuth2/Client.php @8.x] |
| Symfony 8 removes `UserInterface::eraseCredentials()` (7.x already marks `User::eraseCredentials()` deprecated and empty). | Do not call or override it. | [PR #17392] [code: app/bundles/UserBundle/Entity/User.php:392-395 @7.x] |
| User docs 8.0 for users/roles are identical to 7.2 except the "Never logged in" section; devdocs 8.0 permissions page updated as above. | — | [docs: https://docs.mautic.org/en/8.0/users_roles/managing_roles.html] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html] |

## 4. Writing code that works on 7.x and 8.x

- Define permission levels in the constructor (works on both; 7.x calls `definePermissions()` only if you override it). Register the class as a service tagged `mautic.permissions`. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:24-27 @7.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html#construct]
- Add native return types to every `AbstractPermissions` override now; PHP allows a child to add a return type the parent lacks. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- Never reference `UserEvents::*` unguarded; use `defined()` checks. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
