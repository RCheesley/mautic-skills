# REST API: what the official docs say

Digest of the cross-cutting REST API pages in the developer docs (devdocs.mautic.org, 7.2 and 8.0 branches) and the API
Settings section of the user docs. Per-resource pages are digested in the owning area skills. Where the docs disagree with
7.2.1 code, the code behaviour is in `behaviour.md` section 13.

## Contents
1. Pages and their status
2. Enabling the API and settings
3. Authentication procedures
4. Request and response conventions as documented
5. API v2 page
6. Plugin extension docs (custom endpoints, locking, events)
7. 8.0 docs changes
8. Terminology
9. Documentation gaps

## 1. Pages and their status

- The REST API section has 34 pages under `rest_api/`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html]
- Stub pages with no endpoint content: data, dynamic_content, files, focus, messages, pages, point_actions,
  point_triggers, roles. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/data.html]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/pages.html]
- Pages flagged "requires a major update / legacy page… potentially inaccurate" but with content: assets, campaigns,
  categories, contacts, fields, notifications, point_groups, reports, text_messages. Treat them as lower confidence.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/reports.html]
- Rewritten pages without the banner: companies, emails, forms, notes, plus the second-half pages segments, stages,
  stats, tags, themes, tweets, users, webhooks, point_insights. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html]

## 2. Enabling the API and settings

- The REST API is off by default. Turn it on under Configuration > API Settings or with `'api_enabled' => 1` in
  `config/local.php` (`app/config/local.php` before Mautic 5). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html]
- "API enabled" must be Yes to pass data in or out through the API.
  [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#api-settings]
- HTTP Basic Auth can be enabled and is recommended only over HTTPS.
  [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#api-settings]
- Access token lifetime defaults to 60 minutes; refresh token lifetime defaults to 14 days; after the refresh token
  expires the integration must reauthorize. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#api-settings]
- Once the API is on, "API Credentials" appears in the admin menu, where you create a Client ID and Secret.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#oauth2]
- All responses are JSON; the base endpoint is `https://<mautic>/api`.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-endpoints]
- The PHP client is installed with `composer require mautic/api-library`.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#mautic-api-library]
- The API rate limiter cache (`api_rate_limiter_cache`, default `file_system`, alternative memcached) "is no longer
  available in Mautic version 7 or later". No current rate limit is documented.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-rate-limiter-cache]

## 3. Authentication procedures

P1. Basic Auth: enable it in API Settings (or `'api_enable_basic_auth' => true`), base64-encode `user:password` of a
Mautic User, and send `Authorization: Basic <b64>` on every request.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#basic-authentication]

P2. Authorization Code flow:
1. Redirect the browser to `/oauth/v2/authorize` with `client_id`, URL-encoded `redirect_uri`, `response_type=code` and
   a `state` value.
2. On the callback, compare `state` with the stored value.
3. POST the `code` immediately to `/oauth/v2/token` (`application/x-www-form-urlencoded`) with
   `grant_type=authorization_code`, `client_id`, `client_secret`, `redirect_uri`, `code`.
4. Store `access_token` and `refresh_token` and compute the expiry from `expires_in` (3600 in the examples).
5. Refresh with `grant_type=refresh_token` within the refresh lifetime; a refresh returns a new access token and a new
   refresh token. On `400 Bad Request` send the User back to step 1.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#authorization-code-flow]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#refreshing-tokens]

P3. Client Credentials flow: POST `grant_type=client_credentials`, `client_id`, `client_secret` to `/oauth/v2/token`.
No refresh token is returned. Actions are recorded under the credential name, for example "Contact was identified by
Mautibot test [1]". The PHP API library does not support this flow yet.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#client-credentials-flow]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#oauth2]

P4. Sending the token: prefer `Authorization: Bearer ACCESS_TOKEN`. The server must pass headers to PHP (FastCGI setups
may lack `apache_request_headers()`); the alternative is `access_token` in a form-encoded POST body. Avoid query-string
tokens because logs, history and Referer headers expose them.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#authenticating-the-api-request]

## 4. Request and response conventions as documented

| Topic | What the docs say | URL |
|---|---|---|
| Pagination | `start` default 0; `limit` default = system pagination (30); responses carry `total` (a string on Companies and campaign contacts) | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#list-contacts] |
| Search | `search` (string or search command); some pages call it `searchFilter` | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#query-parameters] |
| Ordering | `orderBy` any response column converted to snake_case; `orderByDir` `asc`/`desc` | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#list-segments] |
| `where` | `where[n][col|expr|val]`, Doctrine expressions; documented only for Contacts (and Stats) | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#advanced-filtering] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stats.html#the-expr-parameter-in-where-arrays] |
| `minimal` | returns entities "without additional lists in it" | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html#list-assets] |
| `publishedOnly` | only currently published entities (Campaigns document `published`) | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html#list-campaigns] |
| PUT vs PATCH | PUT creates if the id is missing (201), otherwise clears and replaces (200); PATCH updates supplied fields, 404 if missing; the PHP library's `edit($id, $data, $createIfNotFound = true)` uses PUT | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#edit-company] |
| Status codes | create 201; get, list, delete and actions 200; delete returns the deleted entity | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/emails.html#delete-email] |
| Batch | `/contacts/batch/new`, `/contacts/batch/edit`, `/contacts/batch/delete?ids=`, `/companies/batch/new`; per-item `statusCodes`; duplicates return 200 | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#create-batch-contact] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#create-batch-companies] |
| Errors | OAuth: `{"error","error_description"}`; system: `{"error":{"message","code"}}`; the Users page shows `{"errors":[{"code","message","details"}]}` | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#error-handling] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#error-responses] |
| Version header | `Mautic-Version` on every response since 2.4.0, semver with optional suffix such as `-dev`; PHP library `$api->getMauticVersion()` | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#mautic-version-verification] |
| Categories | assign with `category: <ID>` on any entity that supports Categories | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/categories.html#assign-a-category] |
| Envelope keys | single entity in a singular key, lists in a plural key; Segments use `list`/`lists`, Webhooks `hook`/`hooks` | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#get-segment] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/webhooks.html#list-webhooks] |

## 5. API v2 page

API v2 is built on API Platform at `/api/v2`. It needs authentication and documents itself: opening `/api/v2` in a
browser while logged in shows interactive docs that can run calls. It paginates by default and supports JSON-LD, JSON and
`text/html`. The page gives no introduction version, no resource list and no page size.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/api_v2.html]

## 6. Plugin extension docs (custom endpoints, locking, events)

- Add custom endpoints under the `api` key of `routes` in the plugin `Config/config.php`; the route is placed behind
  `/api` and is "only accessible to authorized Users". Route keys: `path`, `controller`, `method`.
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html]
- The controller should extend `Mautic\ApiBundle\Controller\CommonApiController`, check permissions with
  `isGranted()`, return `$this->accessDenied()` on failure and `$this->handleView($this->view($data, 200))` on success.
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html]
- API-aware locking: implement `ApiLockAwareInterface` and use `ApiEntityLockTrait` (override `isApiLocked()` if
  needed); the API then returns 409 with `{"errors":[{"message":"{Entity} is currently checked out by {User} (on {Date}
  at {Time}).","code":409,"details":{"checkedOutBy","checkedOut"}}]}`.
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#enable-api-lock-for-a-model]
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#error-message]
- Permission-context event (`ApiEvents::API_PLATFORM_PERMISSION_CONTEXT`, `mautic.api_platform_permission_context`,
  payload `ApiPlatformPermissionContextEvent`): fires before API Platform authorises; subscribers may `setPermission()` and
  `setRequestObject()`; intended for placeholder permissions such as Custom Objects'
  `custom_objects:[customObject]:viewown`; it is additive and non-breaking. `getRequest()` may be null and
  `getAttributes()` empty, so guard both.
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#api-permission-context-event]
- Campaign export/import is documented as `POST /api/campaigns/export/{id}` and `POST /api/campaigns/import`
  (code uses GET for export). [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#exporting-via-api]

## 7. 8.0 docs changes

- `plugin_extensions/api`: the controller service argument becomes `CorePermissions::class` instead of `'mautic.security'`.
  [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/api.html]
- New section "API entity save events": `PreSaveApiEntityEvent` (after validation, before save) and
  `PostSaveApiEntityEvent` (after save, before serialising), both extending abstract `ApiEntityEvent`
  (`getEntity()`, `getEntityRequestParameters()`, `getRequest()`); dispatched only when a listener subscribes; a throwing
  listener aborts with its message and code. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/api.html#api-entity-save-events]
- New section "API client lifecycle events": `ClientPostSaveEvent`, `ClientPostDeleteEvent` (base `ClientEvent`,
  `getClient()`, `getApiMode()`). [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/api.html#api-client-lifecycle-events]
- New section "Upgrade API event subscribers to Mautic 8": the whole `ApiEvents` class is removed; map each constant to
  its event class; `CLIENT_PRE_SAVE` and `BUILD_ROUTE` are removed; verify wiring with
  `bin/console debug:event-dispatcher '<EventClass>'`.
  [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/api.html#upgrade-api-event-subscribers-to-mautic-8]
- `rest_api/companies`: documents `POST /companies/batch/addcontacts` (`assignments` array, batch limit
  `api_batch_max_limit` default 200, 200 with per-pair `results` and `summary`, 400 for bad payloads, 403 without
  `lead:leads:editown`/`editother`). [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/companies.html#batch-add-contacts-to-companies]
- `rest_api/forms`: `formType` deprecated in 7.1, removed from API responses in 8.0 and ignored on input.
  [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/forms.html#form-properties]
- No other REST API page changed between 7.2 and 8.0. [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/getting_started.html]

## 8. Terminology

- Prose uses Contact, Segment, Webhook, Text Message; paths and payload keys keep `lead`, `list`/`lists`, `hooks`,
  `smses`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#get-segment]
- "User" is a Mautic administrator or marketer account; "Contact" is a tracked person.
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/api.html#api-aware-entity-locking]
- "Mautic API Library" is the PHP client. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#using-the-mautic-api-library]
- "API Credentials" is the UI name for OAuth2 clients. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#oauth2]

## 9. Documentation gaps

- No API-wide statement of the batch limit, maximum `limit`, or rate limits.
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html]
- Validation error format, 403/404/409 shapes are documented only on scattered pages (Users, plugin locking).
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#common-error-responses]
- No permission requirements per endpoint except Notes, Point Insights, the Emails `sendtodnc` flag, and the 8.0
  batch add-contacts endpoint. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/notes.html#permissions]
- No list of v2 resources, filters or page size. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/api_v2.html]
- No description of the client-credentials pseudo user's permissions (the creating admin's role).
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/authentication.html#client-credentials-flow]
