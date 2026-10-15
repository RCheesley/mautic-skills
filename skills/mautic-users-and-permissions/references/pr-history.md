# Users, roles, permissions and authentication — PR history

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
3. Regression catalogue
4. Feature timeline
5. Removed, deprecated, replaced
6. Maintainer norms for this area
7. Open questions
8. Coverage

## 1. How to read this file
Source: merged pull requests on mautic/mautic for the users, roles and authentication area, harvested 2026-10-15.
Versions are inferred from the base branch, milestone and merge date; where a release tag was checked in the 7.x tree, the first tag that contains the merge is used. "7.x after 7.2.1" means merged to `7.x` but in no release yet (milestone 7.3.0-rc).
Current behaviour is in behaviour.md. This file explains why and when. Where the two disagree, behaviour.md wins.

## 2. Decisions that shaped current behaviour

### User records and validation
- First name and last name are required, and the form shows their validation errors. Why: Users without a last name failed to save with no visible reason [PR #252] (v1.0). The fields are labelled as required [PR #2109] (v2.1).
- Creating a User without a password shows a validation error on Save and on Save & Close, not a server error [PR #14107] (v5.2).
- The Position field is limited to 191 characters by form validation ("Position cannot exceed 191 characters."). Why: longer values hit the column limit and returned a 500 [PR #15682] (v7.1.0).
- The `signature` column is TEXT with no 255-character limit. Why: the original string column truncated signatures [PR #1478] (v1.3).
- Signatures may contain HTML. Line breaks are converted with nl2br on render; HTML is not stripped [PR #1319] (v1.3). Signatures sent through the Users API keep their HTML, so the API behaves like the UI [PR #7543] (v2.15.2).
- The signature field shows helper text listing the variables a signature may use, on the Account page [PR #13324] (v5.1) and on the User edit page [PR #13498] (v5.1).
- "Mailer is owner" (Email configuration, off by default for backward compatibility) sends email to a Contact from the owner User's name and address, and `{signature}` becomes the owner's signature. Why: sales teams wanted email to come from the Contact's owner. Per-sender transports to fix DKIM were deferred to a separate request [PR #1319] (v1.3).
- A new User's timezone and locale default to empty, which means "use the system default" [PR #110] (v1.0). Choosing the empty locale does not raise a warning [PR #147] (v1.0).
- A User's locale and timezone are applied on every request after login, not only on the Account page [PR #2352] (v2.1.1).
- When an admin changes a User's email or password, Mautic emails the affected User. Why: make Users aware of account changes. Editing a non-existent User id redirects instead of erroring [PR #13925] (v5.2).
- The status toggle on Users reads "Active", with a tooltip saying a disabled User cannot log in. Why: "Published" was ambiguous for accounts [PR #13503] (v5.1). Other bundles got context-specific labels instead of one changed global label [PR #13500] (v5.1).
- `UserRepository::getUserList()` returns no duplicate rows and includes each User's email. The admin JS gets the globals `LoginUserName` and `LoginUserId` [PR #15504] (v7.0.0).
- `User::isGuest` is a constructor argument with an `isGuest()` method; the public property was deprecated [PR #4240] (v2.9).

### User list, profile and preferences
- The User list shows "Last Login" and active/inactive columns, and the User view shows "Recent activity" built from the audit log. The publish switch is hidden for the logged-in User so admins cannot lock themselves out. Role changes were left out of the sidebar in favour of the user-activity report [PR #13074] (v5.1).
- The "last login" column sorts by `u.lastLogin`. Why: the template sorted by role name by mistake [PR #14982] (v5.2.6). The 7.x template uses `u.lastLogin` [code: app/bundles/UserBundle/Resources/views/User/list.html.twig:152 @7.x].
- The User edit page renders even when a recent-activity entry points to a User whose details changed [PR #14884] (v5.2.5). The fix was widened so that entries that no longer resolve to a current User or Role are skipped [PR #17609] (7.2 branch, merged 2026-10-12; not found in the 7.x snapshot).
- The User list has a "Never logged in" quick filter, search command `is:never_logged_in`. Why: find unused or invited accounts [PR #17452] (7.x after 7.2.1).
- `name:` in User search matches first or last name [PR #11599] (v5.0).
- The Account page (`/s/account`) loads for Users whose Role cannot edit Users [PR #8571] (v3.0).
- Editing one's own profile does not ask for the current password. Why: long passwords sometimes failed the check [PR #776] (v1.2). A grep of the 7.x profile controller and form types finds no current-password field. [unverified]
- The Account page has titled sections [PR #13473] (v5.1) and an Accessibility tab (transitions, strong borders, reduced transparency, link underlines) [PR #13887] (v5.2). Reviewers recorded that opt-in options do not replace baseline WCAG AA compliance [PR #13887].
- Theme choices apply after Save, with no live preview. Why: the preview caused bugs on cancel [PR #14291] (v5.2).
- UI preferences are stored per User in the database, not in browser localStorage. Why: the same experience across devices [PR #14398] (v6.0).
- Accent colour is a global theme setting, not a per-User preference [PR #14637] (v6.0). Solarized themes are stored as `solarized-dark`/`solarized-light` [PR #14733] (v6.0).
- The account menu has an "Invite your team" link, shown only to Users who may create Users [PR #13914] (v5.2). Since 7.2.0 it opens the invite modal [PR #15401] (v7.2.0).

### Invitations
- An admin invites a new User by email with a Role. The invite link expires after 48 hours, and the invitee sets their own details and password on a public page. Why: admins should not set passwords for others [PR #15401] (v7.2.0). The 7.x expiry is `PT48H` [code: app/bundles/UserBundle/Model/UserModel.php:423 @7.x].
- Invites are a separate entity (`UserInvite`, table `user_invites`), not password-reset tokens. Why: the invite lifecycle (Role, expiry, acceptance) differs from reset [PR #15401] (v7.2.0).
- The invite flow starts from the "Invite user" button on the User list or the "Invite your team" link; both open a modal on `mautic_user_index` with `open=invite` [PR #15401] (v7.2.0).

### Deleting Users and Roles
- Users and Roles can be batch-deleted. A User cannot delete themselves, and a Role with Users cannot be deleted; the other selected items are still deleted, with a notice per refused item [PR #233] (v1.0).
- The delete confirmation (single and batch) states that the User's Contacts and Companies become unassigned and that their API access tokens and scheduled Contact exports are removed. Why: deleting a User had non-obvious side effects. Only translation strings changed [PR #17444] (7.x after 7.2.1). See section 7.

### Roles and permissions
- The Roles list shows a User count. The Role name opens the Role, and the count opens the User list filtered by `role:"Name"` [PR #1534] (v1.4) [PR #2085] (v2.1) [PR #6565] (v2.14.2). The count column is sortable [PR #15414] (v7.1.0).
- A Role may mix bundles at full permission and bundles at none [PR #8865] (v3.0). Existing Roles can be edited and saved again [PR #12520] (v5.0).
- When "Has full system access?" is Yes, the Permissions tab is disabled, also when editing. Why: granular permissions are redundant for admins [PR #14004] (v5.2).
- A Role can be cloned. The clone opens as a new, unsaved form named "Clone of {name}" with the same permissions. Why: re-ticking every permission by hand [PR #15402] (v7.2.0).
- Roles and permission rows carry a UUID, filled for existing rows by migration and on creation. Why: the campaign library import needs global ids. It was retargeted to 6.x as a bug fix so 6.x data has no rows without UUIDs [PR #14751] (v6.0).
- The "User management" header in the admin menu shows only with `user:users:view` or `user:roles:view` [PR #14851] (v7.0.0).
- Calendar events show only when the viewer may view the underlying item [PR #2719] (v2.5).
- Background imports run as the importing User, so permission checks apply to that User [PR #13469] (v5.1).
- In a Contact import, an `ownerusername` that matches no active User fails only that row, with "Unable to find an active user by the username or email "X"". Owner lookup accepts a username or an email [PR #15877] (v7.1.0).

### Login, sessions and authenticators
- Unpublished Users cannot log in and get the generic invalid-login message. A dedicated message was suggested and not implemented [PR #3802] (v2.8).
- Login and OAuth authorize pages send noindex/nofollow [PR #1457] (v1.4).
- CSRF protection is on for all UI forms; `ROLE_API` is granted only to authenticated `/api` requests, where CSRF is skipped [PR #1545] (v1.3.1).
- Every successful login writes an audit-log entry [PR #6721] (v2.15).
- Anonymous tracked visitors get no Symfony session, and the User online-status tracking was removed. Why: the session cookie had no SameSite and was a remnant of a chat feature [PR #8639] (v3.0).
- Password hashing uses Symfony's hasher factory across UI, API, installer and SAML [PR #9842] (v4.0).
- Logout runs on Symfony's `LogoutEvent` and deletes the session. Why: logout was broken after the handler interface was deprecated [PR #11867] (v5.0).
- `User` and `PluginToken` serialise for the session through `__serialize()`/`__unserialize()` [PR #12434] (v5.0) [PR #11150] (v5.0). `eraseCredentials()` clears plain and current password fields [PR #12507] (v5.0).
- Form login moved to a Guard authenticator [PR #11520] (v5.0), which only ran after [PR #12855] (v5.0). Mautic 6 uses Symfony's authenticator system for form login, SAML, OAuth2 and plugin SSO; it was merged with a known SAML issue to unblock the alpha [PR #14219] (v6.0).
- Plugins can authenticate Users from the login form or a third-party SSO through dedicated events and a firewall [PR #1114] (v2.0). Failures use `mautic.user.auth.error.invalidlogin` [PR #8535] (v3.0). When a plugin marks the request authenticated, the User is logged in; this restored plugin SSO such as Auth0 on 6.x [PR #15020] (v6.0.3).
- The login and security pages do not load CKEditor (login, reset request and confirm, SAML retry, invite registration, API login, OAuth2 consent). Why: these pages never render rich text, and the editor slowed unauthenticated pages. Other pages load it by default through the Twig variable `includeEditor` [PR #16987] (v7.2.0).

### Passwords and reset
- Reset emails a tokenised link; the password changes only after the token is verified [PR #1544] (v1.3.1).
- Reset tokens are random, stored in `user_tokens`, expire, and one-time tokens are deleted on use [PR #5958] (v2.13.1). The 7.x reset expiry is `PT24H` [code: app/bundles/UserBundle/Model/UserModel.php:252 @7.x].
- The reset response is the same whether or not the User exists, and always redirects to login [PR #6568] (v2.15) [PR #11417] (v5.0). The message reads "If this user exists…" [PR #13107] (v5.0).
- The reset email has HTML and plain-text parts [PR #2285] (v2.1.1), has no tracking pixel [PR #2008] (v2.0.1), and uses an absolute link [PR #8714] (v3.0).
- `mautic:maintenance:cleanup` deletes expired User tokens [PR #6851] (v2.15). Its dry run reports the real count of expired tokens; the documented `@return int` was treated as the contract [PR #16772] (v7.2.0).
- Passwords are checked for strength (zxcvbn score plus a dictionary check, not fixed character rules) in the UI, API and installer. Users with a weak stored password are sent to a forced reset at login. `PasswordStrengthValidateEvent` allows custom rules. Strict character rules (an alternative PR) were rejected [PR #12826] (v5.1).
- Dev and test fixture Users use `Maut1cR0cks!` because the old password fails the strength check [PR #13105] (v5.1).
- `UserModel` receives the password hasher in its constructor; `checkNewPassword()` and `resetPassword()` no longer take it as an argument [PR #16980] (v7.2.0). See section 6 and section 7.

### SAML
- SAML SSO: SP metadata at `/saml/metadata.xml`, login at `/s/saml/login`, IdP metadata upload, attribute mapping and a default Role for created Users [PR #3113] (v2.5). Attribute fields are optional [PR #3182] (v2.6).
- PR #3113 described a redirect to the IdP whenever SAML is enabled. In 7.x the redirect needs env `MAUTIC_SAML_ENABLED=true` (behaviour.md B17, B115) [PR #3113].
- SAML matches an existing User by email instead of creating a duplicate. An empty default Role disables automatic creation [PR #4074] (v2.9).
- A mapped, non-empty Username attribute becomes the username; otherwise the email is used [PR #8922] (v3.1). Unmapped attributes are ignored so the fallback works [PR #12557] (v5.0).
- Without a custom SP certificate, SAML requests are not signed. Why: 3.0 signed with the vendor certificate, a change from 2.x [PR #8770] (v3.0).
- Without configured keys each instance generates its own key and certificate in the cache folder. Why: shared predefined keys are unsafe, and the library dropped its bundled keys [PR #12212] (v5.0).
- `saml_idp_entity_id` can use the site URL or a configured `subdomain_url` [PR #12655] (v5.0). SP metadata and routes match what the IdP expects regardless of `site_url` [PR #15508] (v7.0.0).
- Request state storage was fixed so IdPs such as Entra complete login; the mapping fields hold attribute names [PR #14367] (v5.2.1).
- SAML Users do not see password fields on their profile or on the User edit form [PR #15508] (v7.0.0).
- A SAML "Unknown Response" (stale session state) shows a retry page that clears the session [PR #15508] (v7.0.0).

### API
- OAuth2 `client_credentials` (two-legged) is supported [PR #9837] (v4.0).
- A User-bound OAuth2 bearer token authenticates on `/api` and `/api/v2`. The authenticator uses the token's user identifier and falls back to the client identifier only for client-only tokens [PR #16245] (v7.1.3).
- `PATCH /api/users/{id}/edit` with `{"role": <id>}` changes a User's Role [PR #10668] (v4.1.2). It merged to the 4.1 bug-fix branch and was flagged for a possible revert; no revert followed, and 7.x still accepts it. PATCH strips `username` and `plainPassword`, but not `role`; PUT keeps the stored username and Role [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:122-138 @7.x]. Functional tests cover the role PATCH [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:20-45 @7.x].
- Batch User edit through the API works [PR #4336] (v2.9).

## 3. Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| User without last name not saved, no message | First/last name errors shown | [PR #252] | v1.0 |
| Error creating a User without password | Validation message on Save and Save & Close | [PR #14107] | v5.2 |
| Position over 191 characters gave a 500 | "Position cannot exceed 191 characters." | [PR #15682] | v7.1.0 |
| HTML stripped from signature sent through the API | HTML kept | [PR #7543] | v2.15.2 |
| User locale/timezone reverted to system default | User preference applied on every request | [PR #2352] | v2.1.1 |
| `/s/account` failed for limited-permission Users | Profile loads | [PR #8571] | v3.0 |
| Account page tabs unusable | Tabs work | [PR #13704] | v5.1 |
| Solarized themes not applied | Correct theme ids | [PR #14733] | v6.0 |
| User list "last login" sorted by role name | Sorts by `u.lastLogin` | [PR #14982] | v5.2.6 |
| User edit gave a 500 from an activity entry for a changed User | Page renders | [PR #14884] | v5.2.5 |
| User edit gave a Twig error from activity entries that no longer resolve | Entries skipped, page renders | [PR #17609] | 7.2 branch |
| Batch delete did nothing | Batch delete works except self and Roles with Users | [PR #233] | v1.0 |
| Role name link opened a random User | Opens the Role | [PR #2085] | v2.1 |
| Role count link showed no Users | `role:` filter works | [PR #6565] | v2.14.2 |
| 500 saving a Role with mixed permissions | Role saves | [PR #8865] | v3.0 |
| Roles not editable after creation | Edit and save work | [PR #12520] | v5.0 |
| Full-access Role showed the Permissions tab when editing | Tab disabled | [PR #14004] | v5.2 |
| UUIDs missing on Roles/permissions | UUID set on migrate and create | [PR #14751] | v6.0 |
| "User management" header shown without User/Role view permission | Header hidden | [PR #14851] | v7.0.0 |
| Users without permissions saw all calendar events | Per-event permission check | [PR #2719] | v2.5 |
| Custom-object import failed with permission errors | Import runs as the importing User | [PR #13469] | v5.1 |
| Unknown `ownerusername` in import gave an unclear error | Row fails with the "Unable to find an active user…" message; other rows import | [PR #15877] | v7.1.0 |
| Unpublished User could log in | Login denied | [PR #3802] | v2.8 |
| All UI forms had CSRF disabled | CSRF on all UI forms, skipped only on `/api` | [PR #1545] | v1.3.1 |
| Translated login placeholder broke at an apostrophe | Strings escaped | [PR #2169] | v2.1 |
| Session cookie set for tracked visitors | No session for anonymous visitors | [PR #8639] | v3.0 |
| Unable to edit a User account on 4.0 | Hashing through the new hasher works | [PR #9842] | v4.0 |
| Logout broken | Logout listener deletes the session | [PR #11867] | v5.0 |
| Guard authenticator never invoked | Authenticator events fire on login | [PR #12855] | v5.0 |
| Plugin SSO (Auth0) not completed on 6.x | User logged in when the plugin marks success | [PR #15020] | v6.0.3 |
| Login page loaded CKEditor and a missing source map | Security pages skip the editor | [PR #16987] | v7.2.0 |
| Reset email blank in some clients | HTML and text parts | [PR #2285] | v2.1.1 |
| Tracking pixel in the reset email | No pixel | [PR #2008] | v2.0.1 |
| Reset link was relative | Absolute URL | [PR #8714] | v3.0 |
| Reset token not random | Random, expiring, one-time token | [PR #5958] | v2.13.1 |
| Reset response differed for unknown Users | Same response regardless | [PR #11417] | v5.0 |
| Fixture Users failed the strength check | Strong fixture password | [PR #13105] | v5.1 |
| Cleanup dry run always reported 1 expired token | Reports the real count | [PR #16772] | v7.2.0 |
| Config would not save with empty SAML attributes | Attributes optional | [PR #3182] | v2.6 |
| SAML 500 when a User with that email existed | Existing User matched by email | [PR #4074] | v2.9 |
| SAML username mapping ignored | Mapped username used | [PR #8922] | v3.1 |
| SAML without username mapping failed | Falls back to email | [PR #12557] | v5.0 |
| SAML requests signed with the vendor certificate | Unsigned unless a custom certificate is set | [PR #8770] | v3.0 |
| SAML InResponseTo error (Entra) | Login completes | [PR #14367] | v5.2.1 |
| Intermittent SAML "Unknown Response" after session expiry | Retry page clears the session | [PR #15508] | v7.0.0 |
| API batch User edit: "Entities must be managed" | Batch edit works | [PR #4336] | v2.9 |
| User-bound OAuth2 token returned 401 on `/api/v2` | Same token valid on v1 and v2 | [PR #16245] | v7.1.3 |

## 4. Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.x | Batch delete [PR #233]; token-based reset [PR #1544]; CSRF fix [PR #1545]; signature and "Mailer is owner" [PR #1319]; Role User count [PR #1534]; login noindex [PR #1457] | [PR #233] |
| 2.0–2.15 | Plugin authentication and SSO [PR #1114]; SAML SSO [PR #3113]; unpublished Users blocked [PR #3802]; "Update contact owner" Campaign action [PR #4910]; random `user_tokens` [PR #5958]; login audit entry [PR #6721]; expired-token cleanup [PR #6851] | [PR #3113] |
| 3.0 | No session for anonymous visitors [PR #8639]; SAML unsigned without custom certificate [PR #8770] | [PR #8639] |
| 4.0 | OAuth2 `client_credentials` [PR #9837]; Symfony password hasher [PR #9842] | [PR #9837] |
| 4.1.2 | Role change through `PATCH /api/users/{id}/edit` | [PR #10668] |
| 5.0 | Twig templates [PR #11580]; logout listener [PR #11867]; per-instance SAML keys [PR #12212]; SAML entity id choice [PR #12655] | [PR #12212] |
| 5.1 | zxcvbn password strength with forced reset | [PR #12826] |
| 5.1 | Last login, status columns and recent activity | [PR #13074] |
| 5.1 | "Active" label for Users | [PR #13503] |
| 5.2 | "Invite your team" link to the new-User form | [PR #13914] |
| 5.2 | Accessibility preferences | [PR #13887] |
| 5.2 | Email to a User when an admin changes their email or password | [PR #13925] |
| 5.2 | Permissions tab disabled for full-access Roles | [PR #14004] |
| 6.0 | Symfony authenticator system | [PR #14219] |
| 6.0 | User preferences stored in the database | [PR #14398] |
| 6.0 | Global accent colour | [PR #14637] |
| 6.0 | UUIDs on Roles and permissions | [PR #14751] |
| 7.0.0 | "User management" header permission-gated | [PR #14851] |
| 7.0.0 | `getUserList()` email and dedupe; JS login globals | [PR #15504] |
| 7.0.0 | SAML password fields hidden, retry page, IdP-matching metadata | [PR #15508] |
| 7.1.0 | Sortable Role User count | [PR #15414] |
| 7.1.0 | Position limited to 191 characters | [PR #15682] |
| 7.1.0 | Clear import error for an unknown owner | [PR #15877] |
| 7.1.3 | User-bound OAuth2 tokens accepted on `/api/v2` | [PR #16245] |
| 7.2.0 | User invitations by email | [PR #15401] |
| 7.2.0 | Role cloning | [PR #15402] |
| 7.2.0 | Cleanup dry run reports the real token count | [PR #16772] |
| 7.2.0 | Hasher injected into `UserModel` | [PR #16980] |
| 7.2.0 | `includeEditor` switch; security pages skip CKEditor | [PR #16987] |
| 7.x after 7.2.1 | Delete confirmation lists consequences | [PR #17444] |
| 7.x after 7.2.1 | "Never logged in" filter, `is:never_logged_in` | [PR #17452] |

## 5. Removed, deprecated, replaced

| What | Replaced by | PR | Version |
|---|---|---|---|
| Current-password check on profile edit | Removed | [PR #776] | v1.2 |
| Instant password reset | Tokenised link | [PR #1544] | v1.3.1 |
| Reset token derived from account data | `UserToken` entity; `UserModel::getResetToken` returns a `UserToken` | [PR #5958] | v2.13.1 |
| Public `$user->isGuest` property | `new User(true)`, `isGuest()` | [PR #4240] | v2.9 |
| `LoginEvent` extending the Campaign event | Extends the Symfony event | [PR #6721] | v2.15 |
| Anonymous session and User online status | Removed | [PR #8639] | v3.0 |
| User import fix | Merged, then reverted by [PR #8690] because it depended on an unmerged PR; to be redone inside another PR | [PR #8631] | v3.0 |
| `AdvancedUserInterface` on `User` | Removed (bc-break, UPGRADE-5.0.md) | [PR #11056] | v5.0 |
| `ListenerInterface` authentication listener | Callable listener; `anonymous: lazy` | [PR #11057] | v5.0 |
| Legacy form authenticator | Guard authenticator, later superseded by [PR #14219] | [PR #11520] | v5.0 |
| `LogoutHandlerInterface` | `LogoutEvent` listener | [PR #11867] | v5.0 |
| `Serializable` on `User`/`PluginToken` | `__serialize()`/`__unserialize()` | [PR #12434] | v5.0 |
| UserBundle PHP templates | Twig | [PR #11580] | v5.0 |
| Bundled SAML dummy keys | Per-instance generated keys | [PR #12212] | v5.0 |
| Guard and legacy authentication | Symfony authenticator system (bc-break, UPGRADE-6.0.md) | [PR #14219] | v6.0 |
| Theme live preview | Apply on Save | [PR #14291] | v5.2 |
| localStorage preferences | Database | [PR #14398] | v6.0 |
| Per-User accent colour | Global setting | [PR #14637] | v6.0 |
| "Published" label on Users | "Active" | [PR #13503] | v5.1 |
| Hasher argument on `UserModel::checkNewPassword()`/`resetPassword()` | Constructor injection; no deprecation step | [PR #16980] | v7.2.0 |
| `getModel('user.*')` in UserBundle controllers | Typed injection | [PR #16589] | v7.2.0 |
| Five UserBundle services in `config.php` (including SAML `IdStore`) | Autowired in `services.php` | [PR #16784] | v7.2.0 |
| Unused `MauticSsoFactory` members | Deleted | [PR #16702] | v7.2.0 |
| Unconditional CKEditor load | `includeEditor` (default true) | [PR #16987] | v7.2.0 |

## 6. Maintainer norms for this area
- Bug fixes target the patch branch and features the next minor. A feature merged to a bug-fix branch was flagged for revert [PR #10668] [PR #8922] [PR #14982] [PR #16245].
- A fix to a feature that landed in a minor targets the same branch [PR #13105]. The UUID fix was retargeted to 6.x so stable data stays consistent [PR #14751].
- A merged PR that depends on an unmerged PR is reverted rather than shipped half-working [PR #8690].
- Security fixes avoid User enumeration and prove identical responses with a functional test before merge [PR #6568] [PR #11417].
- Erase credentials after authentication and never ship predefined keys [PR #12507] [PR #12212].
- Schema changes ship a migration in the same release [PR #1478] [PR #9837].
- BC breaks are labelled and listed in UPGRADE-x.md [PR #11056] [PR #14219]. [PR #16980] changed public `UserModel` signatures in 7.2.0 without a deprecation step; see section 7.
- Fixing code to match its documented interface contract counts as a bug fix, not a BC break [PR #16772].
- Search and filter tests go through the real search flow, not repository internals via reflection [PR #17452].
- Reviewers may add the regression test themselves for small bug fixes [PR #17609]. Small, clearly correct UI fixes may merge without tests, with follow-ups [PR #14851].
- API changes are checked against the mautic/api-library test suite [PR #14219] [PR #4336].
- Inject stateless services in the constructor, use typed injection instead of `getModel()`, and autowire in `services.php` [PR #16980] [PR #16589] [PR #16784].
- Do not load heavy assets on unauthenticated pages [PR #16987].
- Features ship with user or developer documentation PRs [PR #15401] [PR #15402] [PR #17452].

## 7. Open questions
- [PR #16980] changed the public signatures of `UserModel::checkNewPassword()` and `resetPassword()` between 7.1.0 and 7.2.0 with no deprecation step. This conflicts with the minor-release BC policy unless `UserModel` is treated as internal. The 7.1.0 signatures take a hasher argument and the 7.2.0 ones do not [code: app/bundles/UserBundle/Model/UserModel.php:110,236 @7.x].
- [PR #10668] was flagged for revert as a feature on a bug-fix branch, but it shipped in 4.1.2 and 7.x keeps it. Whether Role change by PATCH is an intended API contract was never stated.
- [PR #17444] says deleting a User removes their API access tokens and scheduled Contact exports. Only translation strings changed. behaviour.md B36 records the `user_tokens` cascade and unowned Contacts, not OAuth tokens or exports. Check the delete cascade before relying on the message.
- [PR #17609] (merged 2026-10-12 to the 7.2 branch) is not in the 7.x snapshot by commit-message grep. Until it is merged up, unresolved activity entries may still break the User edit page on 7.x.
- [PR #15401] does not say whether invites can be resent, or whether a pending invite creates a User row.
- [PR #3802] Unpublished Users get the generic invalid-login message; behaviour.md B3 confirms "Invalid login" in 7.x. A dedicated message was never added.
- [PR #11057] `anonymous: lazy` did not stop session cookies on public routes; the state under the 6.x authenticator system is not recorded.
- [PR #5958] Tokens without an expiry are never deleted by cleanup [PR #6851].
- [PR #15020] The exact plugin-authenticator contract (which event flag counts as authenticated) is not described in the PR.
- [PR #15508] came from a downstream fork; a test step mentions vendor-specific SAML user creation. Check that no vendor-specific branching was upstreamed.

## 8. Coverage
- 127 PRs read in 2 chunks: 102 in chunk 1 (2015-02 to 2025-03, [PR #42] to [PR #14751]) and 25 in chunk 2 (2025-04 to 2026-10, [PR #14851] to [PR #17609]).
- About 111 are substantive. About 16 are refactors or noise with no behaviour change, for example [PR #13129] and [PR #16702].
- One merge was reverted: [PR #8631] by [PR #8690].

869 noise PRs across all areas were excluded upstream before these chunks were written.
