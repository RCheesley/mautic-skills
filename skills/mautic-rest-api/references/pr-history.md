# REST API framework - pull-request history

## How to read this file
Source: merged pull requests on github.com/mautic/mautic for ApiBundle, OAuth and API Platform v2, harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; `~` marks an inference. 7.x versions were checked against the release tags.
Current behaviour lives in behaviour.md (code-verified); this file explains why and when it came to be.

## Decisions that shaped current behaviour

### Enabling the API and authentication
- When the API is disabled, every API endpoint, including the OAuth endpoints, is blocked, and Basic Auth is rejected while it is disabled [PR #8265] (~v3.0.0). Behaviour R1-R3 give the current 403 `api_disabled` rule.
- `ROLE_API` is granted only when the User is authenticated and the request path is under `/api`. API requests skip CSRF tokens, and every UI form keeps CSRF protection. Granting `ROLE_API` to every logged-in User had silently switched off CSRF on all Mautic forms [PR #1545] (~v1.3.1).
- HTTP Basic Auth is supported but off by default (`api_enable_basic_auth`). It was added because the Zapier integration broke with OAuth [PR #2957] (~v2.3).
- OAuth2 access-token and refresh-token lifetimes are configurable, with defaults of 60 minutes and 14 days; they had been hard-coded [PR #683] (~v1.1.3). The lifetime settings show only while the API is enabled [PR #955] (~v1.2.1).
- OAuth token `expiresAt` columns are BIGINT so far-future expiry timestamps do not overflow. Doctrine returns BIGINT values as strings, so arithmetic on them must cast. Unsigned INT was rejected because PostgreSQL has no unsigned integers [PR #725] (~v1.2.0).
- OAuth redirect URIs may use any URL scheme, so native-app schemes such as `myapp://oauth/callback` are accepted [PR #358] (~v1.0.4).
- The 2-legged `client_credentials` grant exists for machine-to-machine integrations: POST `grant_type`, `client_id` and `client_secret` to `/oauth/v2/token` and use the token as a Bearer token. The client is linked to a role (`oauth2_clients.role_id`) [PR #9837] (~v4.0.0). Behaviour R11-R12 say which role and pseudo User the token acts as.
- OAuth1a is not supported from Mautic 4. OAuth2 (authorization code, refresh token, client credentials) and Basic Auth are the only methods. It was dropped because of the "increasing workload to keep supporting it" [PR #10111] (~v4.0.0). The `.htaccess` Authorization-header workaround for fcgi went with it [PR #246] (~v1.0.2) [PR #10111].
- OAuth2 bearer tokens bound to a User work on both `/api` (v1) and `/api/v2`. The authenticator uses the token's user identifier when a User is attached and the client identifier only for client-only tokens. User-bound tokens had returned 401 "Invalid credentials" on v2 [PR #16245] (v7.1.3).
- `PreAuthorizationEventListener` subscribes to the OAuth pre- and post-authorization events through `getSubscribedEvents()`, not through manual service tags. The same PR stopped the CoreBundle exception listener running twice per exception [PR #16879] (v7.2.0).

### OAuth server library
- Mautic first kept a fork of FOSOAuthServerBundle. In 5.0 the fork moved to a branch reset on upstream master with Twig templates, because PHP templating was being removed and upstream did not merge Mautic's changes. `thephpleague/oauth2-server-bundle` was proposed and not adopted [PR #12091] (v5.0, bc-break). Removing the fork in 4.0 had been rejected because upstream had no compatible release [PR #10111].
- By 7.0 the server bundle is `klapaudius/oauth-server-bundle` 5.1.3, and Mautic's `AuthorizeController` matches its `authorizeAction(Request, AuthorizeFormHandler, Twig\Environment)` signature. A patch release had broken Composer installs without a lock file; moving forward was preferred over pinning the old version [PR #15436] (v7.0.0).
- A call to the OAuth1 `ClientModel::deleteAccessTokens()`, removed with OAuth1, survived until 7.2 because the PHPStan baseline hid it [PR #16516] (v7.2.0).

### Error responses
- A failed API authentication returns a generic "API authorization denied." with type `access_denied` and code 401, not "OAuth2 authentication required", because OAuth2 is only the last firewall checked [PR #3203] (~v2.6.0).
- Auth errors name the cause: API disabled, Basic Auth disabled, or "Authorization denied, invalid credentials." [PR #4755] (~v2.10.1).
- Authentication failures keep their real HTTP status (for example 401). `ApiSubscriber` used to rewrite them to 200, which broke clients such as Zapier [PR #6731] (~v2.14.2).
- All errors use an `errors` array of `{message, code, type}`. The legacy top-level `error` and `error_description` keys were deprecated in 2.6.0 "for removal in 3.0" [PR #3203] (~v2.6.0). In 7.x `ApiSubscriber` reads `error_description` only from the OAuth server's own error body and returns `{"errors":[{"message","code","type"}]}` with the original status; the legacy keys are not in the rewritten response (behaviour R67).
- Form validation errors return 400 with a `details` map keyed by field, so clients can show messages next to fields. The BC break was accepted because form errors were broken anyway [PR #2142] (~v2.1.0). The singular `error` envelope of that PR was replaced by the `errors` array [PR #3203].
- OAuth exceptions are returned as JSON in the API format, not HTML [PR #246] (~v1.0.2).

### Response shape and serialization
- List responses carry `total` as an integer and the entities under the plural key [PR #246] (~v1.0.2). `/api/contacts` returned `total` as a string until it was made an integer like the other endpoints [PR #10065] (~v4.0.0).
- Contact responses include fields grouped by field group plus a flat `fields.all` map [PR #246] (~v1.0.2). The artificial `all` group is ignored when a write updates field groups [PR #7719] (~v2.16.0).
- DELETE responses serialise the deleted entity the same way as GET [PR #246] (~v1.0.2).
- Empty object-like properties, such as custom field `properties`, are returned as `{}` rather than `[]`, so the JSON type does not depend on emptiness [PR #7723] (~v4.0.0). The PR also aimed at empty entity lists; behaviour R31 shows a Paginator-backed empty list is still `[]` (see Open questions).
- Batch delete returns a JSON array when the request ids are a sequential list and an object when they are keyed. The author called the design "undesirable" but rejected a rewrite as a BC break [PR #7815] (~v3.2.5).
- An empty batch-edit result stays a JSON object. An earlier fix that returned `[]` was treated as a BC break because the endpoint otherwise returns `{}` [PR #10724] (~v4.3).
- Entity serializer and Doctrine metadata are defined in static PHP methods (`loadApiMetadata`, `loadMetadata`), not annotations, because annotation caching produced hundreds of cache files that broke shared hosts [PR #229] (~v1.2.0).
- Serialised names fall back to the property name unless `serializedName` is set, so output stayed identical across the JMS serializer 3 upgrade [PR #8201] (~v3.0.0).
- API JSON output works on Composer installs without a lock file with `jms/serializer-bundle` ^5.4. Mautic adapts to the renamed `annotation_or_attribute_driver` service; contact calls had returned empty objects [PR #13272] (v5.0.3). A later PR repaired the JMS API metadata driver config that another change had broken [PR #13447] (~v5.1).

### Listing and querying
- `orderBy` takes a bare column name and the repository alias is added; a name already prefixed is not prefixed twice [PR #4589] (~v2.10.0). A custom alias for a joined table, such as `s.date_submitted` on form submissions, is kept as given [PR #8886] (~v3.1.0).
- `/api/fields/contact` returns only Contact fields and `/api/fields/company` only Company fields, even with `where` conditions [PR #5018] (~v2.11.0).
- List endpoints honour "view own" versus "view other": a User without `viewother` gets their own rows without an error [PR #5990] (~v2.14.0). Behaviour R42 gives the current rule.
- `where[...][val]` values are no longer HTML-entity encoded, so a search for a value containing `'` matches. The values never reach HTML, and parameter binding covers SQL injection [PR #14550] (v6.0).

### Writing and batch endpoints
- A category can be set on create or edit with `category: <id>`; an unknown id is a validation error. Contact category subscriptions are not covered [PR #6318] (~v2.14.2).
- `POST /api/contacts/batch/new` deduplicates on unique identifier fields like `/contacts/new`: matches are updated, not duplicated [PR #5396] (~v2.12.1).
- Batch edit maps each payload item to its own entity by id, so unique-field validation does not fail spuriously [PR #9745] (~v4.0.0).
- `/api/contacts/batch/*` accepts a single id such as `ids=1` as well as a comma list [PR #10700] (v4.1.2).
- Batch edit with ids that no longer exist does not return 500; with PUT, a missing id creates a new Contact (201). The same PR fixed parameter binding for `in` and `notIn` in `CommonRepository`, which also affects reports and segments [PR #10724] (~v4.3).
- One batch edit request can edit the same entity more than once; items are applied in order. Detaching the entity after the first edit had broken later edits [PR #14928] (v5.2.7).
- PUT on a device (and similar entities) with a missing id no longer throws a PHP 8 TypeError [PR #11873] (v5.0) [PR #11957] (v4.4.7).
- Clicking Apply when creating API Credentials does not regenerate the secret [PR #708] (~v1.2.0).

### Locking
- Models opt in to API edit locking with `ApiLockAwareInterface` and `ApiEntityLockTrait`, which reuse `FormModel::isLocked()`. An edit to an entity checked out by another User returns 409 with a translated message. Only `EmailModel` opts in; Contacts stay editable. The goal was that API writes do not silently overwrite an open editor session [PR #15299] (v7.1.0). The PR description says `LockableModelInterface`; the merged names are `ApiLockAware*`.

### Rate limiting
- An hourly API rate limit returning 429 was added [PR #6793] (~v2.15.0). Its cache moved to Symfony cache in 3.0, with `api_rate_limiter_cache` taking `adapter` instead of `type` [PR #8305] (~v3.0.0). Changing it still needed a `local.php` edit and a cache rebuild [PR #8265] (~v3.0.0). The cache key was sanitised of reserved characters [PR #9293] (~v3.1.2).
- Rate limiting was removed in 7.0 with `noxlogic/ratelimit-bundle`, which does not support Symfony 7 and is unmaintained [PR #14876] (v7.0.0, bc-break). The PR expected a replacement before 7.0 stable. None exists on the 7.x head: `UPGRADE-7.0.md` lists the removed package and no rate-limit code remains (behaviour R87-R88). The only throttling in `security.php` is `login_throttling` on the UI form login.

### API v2 (API Platform)
- API v2 on API Platform 4 lives at `/api/v2`, with OpenAPI docs at the same path. Entities with `#[ApiResource]` are exposed; Basic Auth and OAuth both work; unauthenticated calls get 401 "API authorization denied."; permissions go through `ApiPermissionVoter`; writes go through `MauticWriteSubscriber`. Early builds allowed unauthenticated access and were fixed before merge [PR #14812] (v7.0.0).
- `ApiEvents::API_PLATFORM_PERMISSION_CONTEXT` lets plugins with dynamic permissions, such as Custom Objects, rewrite the permission and object before the vote. It was ported from Acquia's fork [PR #16837] (v7.2.0). Behaviour notes that only the voter path dispatches it in 7.x.
- v2 is ownership-scoped since the 7.1.2 security release [PR #16175] (v7.1.2) [PR #16181] (forward merge, v7.2.0). The 7.x code enforces three things. Collections whose security is a `...own` permission are filtered for callers who hold only one of own or other: own-only callers see rows they own, other-only callers see rows they do not own. Item operations pass `object`, and the voter resolves the owner (`getPermissionUser()`, then `getCreatedBy()`) and applies `hasEntityAccess` own/other semantics. A meta-test fails if an ownership-scoped item operation omits `object` (behaviour R97-R99).
- `ApiPermissionVoter::voteOnAttribute` takes the nullable `$vote` argument for Symfony 7.2 and later [PR #16566] (v7.2.0).

### Extension points and credentials UI
- Plugins can act after an API entity save through an `ApiEvents` post-save event with `ApiEntityEvent`, which exposes the entity and the whole request [PR #7719] (~v2.16.0). Post-save events for API clients use the correct event name [PR #552] (~v1.1.3).
- Plugins can change the serialization context (groups, exclusion strategies) before and after Mautic sets it, through `ApiSerializationContextEvent` [PR #12734] (v5.1).
- The API Credentials UI is Twig [PR #11853] (v5.0), `ClientController` extends `AbstractStandardFormController` [PR #13296] (v5.1), and the form column layout was fixed [PR #13769] (v5.1).
- The API Credentials list paginates and sorts by name. The "check all" box was removed because there are no batch actions; the row checkboxes still do nothing [PR #14167] (v5.2).
- Configuration > API settings tolerates options hidden in `security_local.php`; a missing key such as `api_enable_basic_auth` gives no notice [PR #8937] (~v3.0.2).
- Configuration values are read through environment-variable placeholders, so saving Configuration no longer rebuilds the container [PR #8265] (~v3.0.0).

## Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| All UI forms lacked a CSRF token | `ROLE_API` only on `/api` requests; UI forms keep CSRF | [PR #1545] | ~1.3.1 |
| Unauthenticated call always said "OAuth2 authentication required" | Generic "API authorization denied.", type `access_denied`, 401 | [PR #3203] | ~2.6.0 |
| Auth failure returned 200 OK | Real status (401) | [PR #6731] | ~2.14.2 |
| OAuth errors returned as HTML | JSON error envelope | [PR #246] | ~1.0.2 |
| Notice "Undefined index: api_enable_basic_auth" when the option is hidden | Settings form and subscriber tolerate missing keys | [PR #8937] | ~3.0.2 |
| SQL error when requesting a refresh token | `expiresAt` stored as BIGINT | [PR #725] | ~1.2.0 |
| User-bound OAuth bearer token got 401 on `/api/v2` | Works on v1 and v2 | [PR #16245] | 7.1.3 |
| Composer install fatal with oauth-server-bundle 5.1.3 | Controller signature matches; dependency locked | [PR #15436] | 7.0.0 |
| `PreAuthorizationEventListener` had no `getSubscribedEvents` | Subscribes to pre/post authorization events | [PR #16879] | 7.2.0 |
| Form errors in API calls broken | 400 with per-field `details` | [PR #2142] | ~2.1.0 |
| List `total` and entity key swapped | `total` integer, entities under plural key | [PR #246] | ~1.0.2 |
| `/api/contacts` returned `"total":"0"` | Integer `total` | [PR #10065] | ~4.0.0 |
| Contact updates raised notices for the `all` group | `all` ignored on update | [PR #7719] | ~2.16.0 |
| Empty custom field `properties` returned `[]`, filled returned `{}` | Always an object | [PR #7723] | ~4.0.0 |
| Batch delete response sometimes array, sometimes object | Shape follows request id keying | [PR #7815] | ~3.2.5 |
| Composer installs returned empty Contact objects | Serializer works with jms/serializer-bundle ^5.4 | [PR #13272] | 5.0.3 |
| `orderBy=dateAdded` caused an SQL error | Alias added automatically | [PR #4589] | ~2.10.0 |
| Could not sort form submissions by date | Custom alias kept in `orderBy` | [PR #8886] | ~3.1.0 |
| `/api/fields/company` with `where` returned Contact fields | Object filter always applied | [PR #5018] | ~2.11.0 |
| List errored for a User without `viewother` | Returns own rows | [PR #5990] | ~2.14.0 |
| `where` search with `'` in the value found nothing | Value not HTML-encoded before the query | [PR #14550] | 6.0 |
| `batch/new` created duplicate Contacts | Deduplicates like single create | [PR #5396] | ~2.12.1 |
| Batch edit of Users failed "Username already in use" at random | Each payload mapped to its entity id | [PR #9745] | ~4.0.0 |
| `batch/delete?ids=1` did nothing | Single id accepted | [PR #10700] | 4.1.2 |
| Batch edit with deleted Contact ids gave 500 | PUT creates (201); empty result stays `{}` | [PR #10724] | ~4.3 |
| Batch edit of the same Contact twice applied once | Every item applied in order | [PR #14928] | 5.2.7 |
| PUT on a missing device id gave a TypeError on PHP 8 | Handled; entity created | [PR #11873] [PR #11957] | 5.0 / 4.4.7 |
| Apply on new API Credentials wiped the secret | Secret kept | [PR #708] | ~1.2.0 |
| API Credentials pagination and batch broken | Pagination and sorting work; check-all removed | [PR #14167] | 5.2 |
| Call to removed OAuth1 `deleteAccessTokens()` | Call removed | [PR #16516] | 7.2.0 |

## Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.0-1.3 | List/total fix, `fields.all`, contact sub-resources, JSON OAuth errors; any-scheme redirect URIs; token lifetimes; BIGINT expiry; OAuth mode choice; static metadata; `ROLE_API` only on `/api` | #246, #358, #683, #955, #725, #777, #229, #1545 |
| 2.1-2.6 | Form error `details`; Basic Auth; `errors` array and generic auth message | #2142, #2957, #3203 |
| 2.10-2.16 | `orderBy` alias; descriptive auth errors; field object filter; batch dedupe; own/other lists; category on write; real auth status codes; rate limiter; post-save API event | #4589, #4755, #5018, #5396, #5990, #6318, #6731, #6793, #7719 |
| 3.0-3.2 | Env-var config; Symfony-cache rate limiter; JMS 3 names; custom `orderBy` alias; batch delete shape | #8265, #8305, #8201, #8886, #7815 |
| 4.0 | `client_credentials`; OAuth1a removed; `{}` for empty properties; integer `total`; batch edit id mapping | #9837, #10111, #7723, #10065, #9745 |
| 4.1-4.4 | Single-id batch; batch edit missing ids; PUT missing device id | #10700, #10724, #11957 |
| 5.0 | Twig OAuth fork; Twig credentials UI; jms ^5.4 fix (5.0.3) | #12091, #11853, #13272 |
| 5.1-5.2 | Serialization context event; credentials controller and pagination; batch edit same entity twice (5.2.7) | #12734, #13296, #14167, #14928 |
| 6.0 | `where` values no longer HTML-encoded | #14550 |
| 7.0.0 | API v2 (API Platform); rate limiter removed; klapaudius OAuth bundle | #14812, #14876, #15436 |
| 7.1.0 | API locking (409) | #15299 |
| 7.1.2-7.1.3 | v2 ownership scoping (security release); user-bound bearer tokens on v2 | #16175, #16245 |
| 7.2.0 | v2 permission-context event; OAuth listener subscribes itself; voter `$vote` argument | #16837, #16879, #16566 |
| 8.0 (unreleased) | Ownership parent marked by `#[OwnershipParent]` entity attribute under Doctrine ORM 3 | #17361 |

## Removed, deprecated, replaced

| What | Replaced by | PR | Version | Note |
|---|---|---|---|---|
| Doctrine/JMS annotations on entities | Static PHP metadata methods | #229 | ~1.2.0 | |
| Top-level `error`, `error_description` in responses | `errors` array | #3203 | ~2.6.0 | Not emitted by the 7.x rewrite |
| Doctrine cache for the rate limiter | Symfony cache (`adapter` key) | #8305 | ~3.0.0 | Manual `local.php` edit |
| Container-compiled config | Env-var placeholders | #8265 | ~3.0.0 | |
| `MauticFactory` and deprecated form calls in ApiBundle | DI, FQCN form types | #8057 | ~3.0.0 | |
| OAuth1a (Bazinga bundle, `.htaccess` header hack) | OAuth2 or Basic Auth | #10111 | ~4.0.0 | In UPGRADE-4.0.md |
| PHP-template FOSOAuthServerBundle fork | Twig fork branch | #12091 | 5.0 | An event listener was renamed (name not in the PR) |
| ApiBundle PHP templates | Twig | #11853 | 5.0 | |
| `ClientController` on `FormController` | `AbstractStandardFormController` | #13296 | 5.1 | |
| FOSOAuthServerBundle fork | `klapaudius/oauth-server-bundle` 5.1.3 | #15436 | 7.0.0 | `AuthorizeController` signature changed |
| API rate limiter (`noxlogic/ratelimit-bundle`) | Nothing | #14876 | 7.0.0 | bc-break, UPGRADE-7.0.md |
| Manual tags for `PreAuthorizationEventListener` | `getSubscribedEvents()` | #16879 | 7.2.0 | |
| Ownership parent on the association mapping | `#[OwnershipParent]` attribute | #17361 | 8.0 (unreleased) | Doctrine ORM 3 / DBAL 4 |

## Maintainer norms for this area
- Changing the shape of an API response (for example `{}` to `[]`) is a BC break even when it fixes a 500; keep the shape [PR #10724] [PR #7815].
- API changes are checked against the `mautic/api-library` test suite, and API library PRs accompany API changes [PR #4200] [PR #5018] [PR #6318] [PR #8201] [PR #9745] [PR #11873] [PR #13272].
- Test Composer installs without the lock file (recommended-project, Docker); dependency drift there broke the API twice [PR #13272] [PR #15436].
- Prefer moving forward to a new dependency over pinning an old one, and watch BC because plugins rely on semver [PR #15436].
- New API features need developer documentation and clear test steps before merge [PR #2957] [PR #9837] [PR #14812] [PR #15299].
- Pure event classes with no logic need no unit test; a sample plugin for manual testing is acceptable [PR #12734].
- Sanitising for XSS is not needed for values that never reach HTML; SQL injection is handled by parameter binding [PR #14550].
- The PHPStan baseline hides real bugs; fix them instead of baselining [PR #16516].
- Event wiring belongs in `getSubscribedEvents()`, and services move to autowired `Config/services.php` [PR #16879] [PR #16791].
- Prefer "return early" over deep nesting [PR #16837].
- Refactor PRs that only touched ApiBundle files set general code style: no file-level docblocks, constructor promotion, readonly properties, `declare(strict_types=1)`, native return types, Rector and PHPStan clean [PR #10970] [PR #12940] [PR #13001] [PR #13062] [PR #16408] [PR #16982]. Project-wide norms are owned by mautic-contributing.

## Open questions
- Conflict with behaviour.md: [PR #7723] intended empty entity lists to be `{}`. Behaviour R31 shows an empty Paginator-backed list is `[]` and other empty lists `{}`. behaviour.md wins; the PR is historical for lists.
- The lock check in [PR #15299] covers single-entity edits. Behaviour R85 says batch edits report a locked item as 409, although a reviewer said batch `editEntitiesAction` did not check locks at merge time. v2 handling of locked Emails is not described [PR #15299].
- Whether the entity detach in batch edit is needed at all was not resolved [PR #14928].
- [PR #10724] says PUT batch edit creates a missing Contact; whether PATCH reports a per-item 404 is not stated in the PR [PR #10724].
- The name of the event listener renamed in the 5.0 OAuth fork change is not given [PR #12091].
- The PR that switched from the FOS fork to `klapaudius/oauth-server-bundle` is not among the harvested PRs; [PR #15436] only updates it.
- Category assignment does not cover Contact category subscriptions [PR #6318]. With `select[]`, non-selected columns can still appear with defaults [PR #5018].
- Security advisory details for the 7.1.2 fixes are not in the PRs; the description above comes from 7.x code [PR #16175] [PR #16181].

## Coverage
The API and webhooks area has 158 merged PRs in two chunks (#125 to #17361, 2015-03 to 2026-09). This file uses the [API] items; webhook items are in mautic-webhooks.
Chunk 1 has 92 PRs (74 substantive); chunk 2 has 66 (40 substantive, 22 refactor-only that contribute norms, 4 noise).
[PR #7606] is a Campaigns change filed in this area and is left out. A further 869 noise PRs across all areas were excluded upstream before chunking.
