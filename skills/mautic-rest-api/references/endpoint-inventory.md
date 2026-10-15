# REST API endpoint inventory (Mautic 7.x)

Every HTTP endpoint the 7.x tree (`419a08a9b35`; endpoints added after 7.2.1 are marked) exposes under `/api` (v1), `/api/v2` (API Platform) and `/oauth/v2`, one line each.
Behaviour of each resource (payload fields, side effects, special codes) lives in the owning skill; this file only says
that the endpoint exists, which permission gates it, and where it is declared.

## Contents
1. Conventions used in this file
2. OAuth2 and credentials endpoints
3. v1 custom (non-standard) endpoints
4. v1 standard endpoints, per resource (10 routes each)
5. v2 (API Platform) resources
6. Documentation discrepancies found while building this table

## 1. Conventions

- v1 routes come from each bundle's `Config/config.php` `routes.api` block and get the `/api` prefix; there is no
  version segment. [code: app/bundles/CoreBundle/Loader/RouteLoader.php:58-67 @7.x]
- A `standard_entity => true` block expands to the ten routes listed in section 4 (`getall`, `getone`, `new`, `newbatch`,
  `editbatchput`, `editbatchpatch`, `editput`, `editpatch`, `deletebatch`, `delete`), named `mautic_api_<name>_<std>`.
  [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:123-194 @7.x]
- `supported_endpoints` narrows that set. Only campaign events use it in core (`getone`, `getall`).
  [code: app/bundles/CampaignBundle/Config/config.php:84-86 @7.x]
- `{id}` and every `{...Id}` placeholder only match digits. [code: app/bundles/CoreBundle/EventListener/CoreSubscriber.php:288-302 @7.x]
- Permission column for standard routes: list needs `<base>:view` and is filtered to own rows when `<base>:viewother` is
  not granted; item read/edit/delete use `hasEntityAccess(<base>:<action>own, <base>:<action>other, owner)`; create uses
  `<base>:create`. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:177-182,409-429 @7.x]
- `<base>` is the controller's `$permissionBase`, which defaults to the model's `getPermissionBase()`.
  [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:143-145 @7.x]
- Every request also needs `api_enabled = true` and a fully authenticated caller.
  [code: app/bundles/ApiBundle/EventListener/ApiSubscriber.php:49-68 @7.x] [code: app/config/security.php:153 @7.x]
- "Owning skill" is where the resource's behaviour is specified. `mautic-rest-api` means this skill owns it.

## 2. OAuth2 and credentials endpoints

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET, POST | `/oauth/v2/token` | none (`security: false`; client id/secret in the body) | mautic-rest-api | [code: app/bundles/ApiBundle/Config/config.php:9-13 @7.x] [code: app/config/security.php:38-41 @7.x] |
| GET, POST | `/oauth/v2/authorize` | logged-in Mautic User holding `api:access:full` | mautic-rest-api | [code: app/bundles/ApiBundle/Config/config.php:14-18 @7.x] [code: app/bundles/ApiBundle/EventListener/PreAuthorizationEventListener.php:42-44 @7.x] |
| GET, POST | `/oauth/v2/authorize_login` | public (login form) | mautic-rest-api | [code: app/bundles/ApiBundle/Config/config.php:19-23 @7.x] |
| POST | `/oauth/v2/authorize_login_check` | handled by the `oauth2_area` firewall | mautic-rest-api | [code: app/bundles/ApiBundle/Config/config.php:24-28 @7.x] |
| GET | `/s/credentials/{page}` (UI) | `api:clients:view` | mautic-rest-api | [code: app/bundles/ApiBundle/Config/config.php:32-35 @7.x] |
| GET, POST | `/s/credentials/{objectAction}/{objectId}` (UI: new, edit, delete, authorized, revoke) | `api:clients:*` | mautic-rest-api | [code: app/bundles/ApiBundle/Config/config.php:36-39 @7.x] |

## 3. v1 custom (non-standard) endpoints

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/campaigns/{id}/contacts` | campaign view access (`checkEntityAccess`) | mautic-campaigns | [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:324-332 @7.x] |
| POST | `/api/campaigns/{id}/contact/{leadId}/add` | `lead:leads:editown`/`editother` on the Contact | mautic-campaigns | [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:123-132 @7.x] |
| POST | `/api/campaigns/{id}/contact/{leadId}/remove` | edit access to the Contact (`checkLeadAccess(..., 'edit')`) | mautic-campaigns | [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:154-160 @7.x] |
| POST | `/api/campaigns/clone/{campaignId}` | `campaign:campaigns:create` (`checkEntityAccess(..., 'create')`) | mautic-campaigns | [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:366-378 @7.x] |
| GET | `/api/campaigns/export/{campaignId}` | `campaign:export:enable` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:132-134 @7.x] [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:404-413 @7.x] |
| POST | `/api/campaigns/import` | `campaign:imports:create` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:137-139 @7.x] [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:429-432 @7.x] |
| GET | `/api/campaigns/events` | `campaign:campaigns:view` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:84-86 @7.x] |
| GET | `/api/campaigns/events/{id}` | view access to the parent Campaign | mautic-campaigns | [code: app/bundles/CampaignBundle/Controller/Api/EventApiController.php:60-63 @7.x] |
| GET | `/api/campaigns/events/contact/{contactId}` | view access per Campaign | mautic-campaigns | [code: app/bundles/CampaignBundle/Controller/Api/EventLogApiController.php:92-106 @7.x] |
| GET | `/api/campaigns/{campaignId}/events/contact/{contactId}` | view access to the Campaign | mautic-campaigns | [code: app/bundles/CampaignBundle/Controller/Api/EventLogApiController.php:92-106 @7.x] |
| PUT | `/api/campaigns/events/{eventId}/contact/{contactId}/edit` | edit access to the Campaign | mautic-campaigns | [code: app/bundles/CampaignBundle/Controller/Api/EventLogApiController.php:139-156 @7.x] |
| PUT | `/api/campaigns/events/batch/edit` | edit access to each Campaign | mautic-campaigns | [code: app/bundles/CampaignBundle/Controller/Api/EventLogApiController.php:181-218 @7.x] |
| GET | `/api/files/{dir}` | authenticated API caller; no controller-level permission check | mautic-rest-api | [code: app/bundles/CoreBundle/Controller/Api/FileApiController.php:96 @7.x] |
| POST | `/api/files/{dir}/new` | authenticated API caller; no controller-level permission check | mautic-rest-api | [code: app/bundles/CoreBundle/Controller/Api/FileApiController.php:59-65 @7.x] |
| DELETE | `/api/files/{dir}/{file}/delete` | authenticated API caller; no controller-level permission check | mautic-rest-api | [code: app/bundles/CoreBundle/Controller/Api/FileApiController.php:125 @7.x] |
| GET | `/api/themes` | `core:themes:view` | mautic-rest-api | [code: app/bundles/CoreBundle/Controller/Api/ThemeApiController.php:106-108 @7.x] |
| GET | `/api/themes/{theme}` | `core:themes:view` | mautic-rest-api | [code: app/bundles/CoreBundle/Controller/Api/ThemeApiController.php:76-78 @7.x] |
| POST | `/api/themes/new` | `core:themes:create` | mautic-rest-api | [code: app/bundles/CoreBundle/Controller/Api/ThemeApiController.php:32-34 @7.x] |
| DELETE | `/api/themes/{theme}/delete` | `core:themes:delete` | mautic-rest-api | [code: app/bundles/CoreBundle/Controller/Api/ThemeApiController.php:128-130 @7.x] |
| GET | `/api/stats` (lists `availableTables`, `tableColumns`) | authenticated API caller | mautic-rest-api | [code: app/bundles/CoreBundle/Controller/Api/StatsApiController.php:25-46 @7.x] |
| GET | `/api/stats/{table}` | `<base>:view` of the table's owning area, own-only without `viewother` (checked in the stats subscriber) | mautic-rest-api | [code: app/bundles/CoreBundle/EventListener/CommonStatsSubscriber.php:63-68 @7.x] |
| GET | `/api/data` | authenticated API caller | mautic-reports-and-dashboard | [code: app/bundles/DashboardBundle/Controller/Api/WidgetApiController.php:62 @7.x] |
| GET | `/api/data/{type}` | authenticated API caller; widget-level checks in the widget's subscriber | mautic-reports-and-dashboard | [code: app/bundles/DashboardBundle/Controller/Api/WidgetApiController.php:77-86 @7.x] |
| POST | `/api/emails/{id}/send` | email view access (`checkEntityAccess`) | mautic-emails | [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:107-121 @7.x] |
| POST | `/api/emails/{id}/contact/{leadId}/send` | email view access | mautic-emails | [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:145-153 @7.x] |
| POST | `/api/emails/reply/{trackingHash}` | authenticated API caller | mautic-emails | [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:211 @7.x] |
| DELETE | `/api/forms/{formId}/fields/delete` | `form:forms:editown` or `editother` | mautic-forms | [code: app/bundles/FormBundle/Controller/Api/FormApiController.php:73-75 @7.x] |
| DELETE | `/api/forms/{formId}/actions/delete` | `form:forms:editown` or `editother` | mautic-forms | [code: app/bundles/FormBundle/Controller/Api/FormApiController.php:101-103 @7.x] |
| GET | `/api/forms/{formId}/submissions` | `form:forms` view access | mautic-forms | [code: app/bundles/FormBundle/Controller/Api/SubmissionApiController.php:49 @7.x] |
| GET | `/api/forms/{formId}/submissions/{submissionId}` | `form:forms` view access | mautic-forms | [code: app/bundles/FormBundle/Controller/Api/SubmissionApiController.php:49 @7.x] |
| GET | `/api/forms/{formId}/submissions/contact/{contactId}` | `form:forms` view access | mautic-forms | [code: app/bundles/FormBundle/Controller/Api/SubmissionApiController.php:49 @7.x] |
| POST | `/api/contacts/{id}/dnc/{channel}/add` (`channel` default `email`) | Contact edit access | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:450-458 @7.x] |
| POST | `/api/contacts/{id}/dnc/{channel}/remove` | Contact edit access | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:490-498 @7.x] |
| GET | `/api/contacts/{id}/activity` | Contact view access | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:406-414 @7.x] |
| GET | `/api/contacts/activity` | `lead:leads:viewown` / `viewother` (scopes the result) | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:424-427 @7.x] |
| GET | `/api/contacts/{id}/notes` | `lead:notes:viewown`/`viewother` against the Contact's owner | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:197-205 @7.x] |
| GET | `/api/contacts/{id}/devices` | `lead:leads:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:249-257 @7.x] |
| GET | `/api/contacts/{id}/campaigns` | `lead:leads:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:365-369 @7.x] |
| GET | `/api/contacts/{id}/segments` | `lead:leads:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:301-305 @7.x] |
| GET | `/api/contacts/{id}/companies` | `lead:leads:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:337-345 @7.x] |
| POST | `/api/contacts/{id}/utm/add` | Contact edit access | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:520-558 @7.x] |
| POST | `/api/contacts/{id}/utm/{utmid}/remove` | Contact edit access | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:520-569 @7.x] |
| GET | `/api/contacts/list/owners` | one of `lead:leads:create`, `editown`, `editother` | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:96-104 @7.x] |
| GET | `/api/contacts/list/fields` | `lead:leads:editown` or `editother` | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:166-168 @7.x] |
| GET | `/api/contacts/list/segments` | Segments visible to the caller | mautic-segments | [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:133 @7.x] |
| POST | `/api/segments/{id}/contact/{leadId}/add` | Segment access plus Contact edit access | mautic-segments | [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:151 @7.x] |
| POST | `/api/segments/{id}/contacts/add` (body `ids`) | Segment access plus Contact edit access per Contact | mautic-segments | [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:184 @7.x] |
| POST | `/api/segments/{id}/contact/{leadId}/remove` | Segment access plus Contact edit access | mautic-segments | [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:227 @7.x] |
| POST | `/api/companies/batch/addcontacts` (7.x after 7.2.1, unreleased; [PR #16512]) | `lead:leads:editown` or `editother` | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:122-124 @7.x] |
| POST | `/api/companies/{companyId}/contact/{contactId}/add` | Contact edit access | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:95 @7.x] |
| POST | `/api/companies/{companyId}/contact/{contactId}/remove` | `lead:leads:editown`/`editother` on the Contact | mautic-contacts | [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:215-230 @7.x] |
| GET | `/api/points/actions/types` | `point:points:view` or `viewown` | mautic-points-and-stages | [code: app/bundles/PointBundle/Controller/Api/PointApiController.php:65-67 @7.x] |
| POST | `/api/contacts/{leadId}/points/{operator}/{delta}` (`plus`, `minus`) | Contact edit access | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:72 @7.x] [code: app/bundles/PointBundle/Controller/Api/PointApiController.php:84-86 @7.x] |
| GET | `/api/points/triggers/events/types` | `point:triggers` view | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| DELETE | `/api/points/triggers/{triggerId}/events/delete` | `point:triggers` edit | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| GET | `/api/contacts/{contactId}/points/groups` | Contact view access | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| GET | `/api/contacts/{contactId}/points/groups/{groupId}` | Contact view access | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| POST | `/api/contacts/{contactId}/points/groups/{groupId}/{operator}/{value}` (`plus`, `minus`, `times`, `divide`, `set`) | Contact edit access | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:91 @7.x] [code: app/bundles/PointBundle/Model/PointGroupModel.php:150-153 @7.x] |
| GET | `/api/smses/{id}/contact/{contactId}/send` (note: GET) | Contact edit access | mautic-channels | [code: app/bundles/SmsBundle/Controller/Api/SmsApiController.php:66-80 @7.x] |
| POST | `/api/stages/{id}/contact/{contactId}/add` | `stage:stages:view` plus Contact edit access | mautic-points-and-stages | [code: app/bundles/StageBundle/Controller/Api/StageApiController.php:62-76 @7.x] |
| POST | `/api/stages/{id}/contact/{contactId}/remove` | `stage:stages:view` plus Contact edit access | mautic-points-and-stages | [code: app/bundles/StageBundle/Controller/Api/StageApiController.php:98-112 @7.x] |
| GET | `/api/users/self` | any authenticated caller | mautic-users-and-permissions | [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:64-70 @7.x] |
| POST | `/api/users/{id}/permissioncheck` (body `permissions`) | user view access | mautic-users-and-permissions | [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:173-189 @7.x] |
| GET | `/api/users/list/roles` | `user:users:create` or `user:users:edit` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:198-206 @7.x] |
| GET | `/api/hooks/triggers` | authenticated API caller | mautic-webhooks | [code: app/bundles/WebhookBundle/Controller/Api/WebhookApiController.php:90-96 @7.x] |
| POST | `/api/focus/{id}/js` | authenticated API caller; no controller-level check | mautic-channels | [code: plugins/MauticFocusBundle/Controller/Api/FocusApiController.php:63-69 @7.x] |

Public, non-`/api` "API-like" endpoints (`/dwc/{objectAlias}` for Dynamic Content) use a different controller and are
covered by mautic-pages-and-tracking. [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x]
`CacheBundle` and `GrapesJsBuilderBundle` declare empty `api` route blocks.
[code: app/bundles/CacheBundle/Config/config.php:9 @7.x] [code: plugins/GrapesJsBuilderBundle/Config/config.php:40 @7.x]

## 4. v1 standard endpoints, per resource

Each block lists the ten standard routes. Campaign events (`/api/campaigns/events`) expose only `getall` and `getone`
and are listed in section 3. The Users controller overrides create/edit to check plain `user:users:create` and
`user:users:edit`. [code: app/bundles/UserBundle/Controller/Api/UserApiController.php:75-112 @7.x] Category item
permissions use the bundle of the Category (`<bundle>:categories`).
[code: app/bundles/CategoryBundle/Controller/Api/CategoryApiController.php:60-64 @7.x] `GET /api/reports/{id}`
returns report data rows, not the report definition (see mautic-reports-and-dashboard).
[code: app/bundles/ReportBundle/Config/config.php:55 @7.x]

#### Assets — `/api/assets` (keys `asset/assets`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/assets` | `asset:assets:view` (own-only filter without `viewother`) | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |
| GET | `/api/assets/{id}` | `asset:assets:viewown`/`viewother` | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |
| POST | `/api/assets/new` | `asset:assets:create` | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |
| POST | `/api/assets/batch/new` | `asset:assets:create` | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |
| PUT | `/api/assets/batch/edit` | `asset:assets:editown`/`editother` (+`create` for missing ids) | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |
| PATCH | `/api/assets/batch/edit` | `asset:assets:editown`/`editother` | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |
| PUT | `/api/assets/{id}/edit` | `asset:assets:editown`/`editother` (+`create` if id missing) | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |
| PATCH | `/api/assets/{id}/edit` | `asset:assets:editown`/`editother` | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |
| DELETE | `/api/assets/batch/delete?ids=` | `asset:assets:deleteown`/`deleteother` | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |
| DELETE | `/api/assets/{id}/delete` | `asset:assets:deleteown`/`deleteother` | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Config/config.php:21 @7.x] |

#### Campaigns — `/api/campaigns` (keys `campaign/campaigns`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/campaigns` | `campaign:campaigns:view` (own-only filter without `viewother`) | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |
| GET | `/api/campaigns/{id}` | `campaign:campaigns:viewown`/`viewother` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |
| POST | `/api/campaigns/new` | `campaign:campaigns:create` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |
| POST | `/api/campaigns/batch/new` | `campaign:campaigns:create` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |
| PUT | `/api/campaigns/batch/edit` | `campaign:campaigns:editown`/`editother` (+`create` for missing ids) | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |
| PATCH | `/api/campaigns/batch/edit` | `campaign:campaigns:editown`/`editother` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |
| PUT | `/api/campaigns/{id}/edit` | `campaign:campaigns:editown`/`editother` (+`create` if id missing) | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |
| PATCH | `/api/campaigns/{id}/edit` | `campaign:campaigns:editown`/`editother` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |
| DELETE | `/api/campaigns/batch/delete?ids=` | `campaign:campaigns:deleteown`/`deleteother` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |
| DELETE | `/api/campaigns/{id}/delete` | `campaign:campaigns:deleteown`/`deleteother` | mautic-campaigns | [code: app/bundles/CampaignBundle/Config/config.php:75 @7.x] |

#### Categories — `/api/categories` (keys `category/categories`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/categories` | `<bundle>:categories (bundle of the category):view` (own-only filter without `viewother`) | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |
| GET | `/api/categories/{id}` | `<bundle>:categories (bundle of the category):viewown`/`viewother` | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |
| POST | `/api/categories/new` | `<bundle>:categories (bundle of the category):create` | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |
| POST | `/api/categories/batch/new` | `<bundle>:categories (bundle of the category):create` | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |
| PUT | `/api/categories/batch/edit` | `<bundle>:categories (bundle of the category):editown`/`editother` (+`create` for missing ids) | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |
| PATCH | `/api/categories/batch/edit` | `<bundle>:categories (bundle of the category):editown`/`editother` | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |
| PUT | `/api/categories/{id}/edit` | `<bundle>:categories (bundle of the category):editown`/`editother` (+`create` if id missing) | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |
| PATCH | `/api/categories/{id}/edit` | `<bundle>:categories (bundle of the category):editown`/`editother` | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |
| DELETE | `/api/categories/batch/delete?ids=` | `<bundle>:categories (bundle of the category):deleteown`/`deleteother` | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |
| DELETE | `/api/categories/{id}/delete` | `<bundle>:categories (bundle of the category):deleteown`/`deleteother` | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Config/config.php:31 @7.x] |

#### Marketing Messages — `/api/messages` (keys `message/messages`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/messages` | `channel:messages:view` (own-only filter without `viewother`) | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |
| GET | `/api/messages/{id}` | `channel:messages:viewown`/`viewother` | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |
| POST | `/api/messages/new` | `channel:messages:create` | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |
| POST | `/api/messages/batch/new` | `channel:messages:create` | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |
| PUT | `/api/messages/batch/edit` | `channel:messages:editown`/`editother` (+`create` for missing ids) | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |
| PATCH | `/api/messages/batch/edit` | `channel:messages:editown`/`editother` | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |
| PUT | `/api/messages/{id}/edit` | `channel:messages:editown`/`editother` (+`create` if id missing) | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |
| PATCH | `/api/messages/{id}/edit` | `channel:messages:editown`/`editother` | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |
| DELETE | `/api/messages/batch/delete?ids=` | `channel:messages:deleteown`/`deleteother` | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |
| DELETE | `/api/messages/{id}/delete` | `channel:messages:deleteown`/`deleteother` | mautic-channels | [code: app/bundles/ChannelBundle/Config/config.php:29 @7.x] |

#### Dynamic Content — `/api/dynamiccontents` (keys `dynamicContent/dynamicContents`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/dynamiccontents` | `dynamiccontent:dynamiccontents:view` (own-only filter without `viewother`) | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |
| GET | `/api/dynamiccontents/{id}` | `dynamiccontent:dynamiccontents:viewown`/`viewother` | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |
| POST | `/api/dynamiccontents/new` | `dynamiccontent:dynamiccontents:create` | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |
| POST | `/api/dynamiccontents/batch/new` | `dynamiccontent:dynamiccontents:create` | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |
| PUT | `/api/dynamiccontents/batch/edit` | `dynamiccontent:dynamiccontents:editown`/`editother` (+`create` for missing ids) | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |
| PATCH | `/api/dynamiccontents/batch/edit` | `dynamiccontent:dynamiccontents:editown`/`editother` | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |
| PUT | `/api/dynamiccontents/{id}/edit` | `dynamiccontent:dynamiccontents:editown`/`editother` (+`create` if id missing) | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |
| PATCH | `/api/dynamiccontents/{id}/edit` | `dynamiccontent:dynamiccontents:editown`/`editother` | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |
| DELETE | `/api/dynamiccontents/batch/delete?ids=` | `dynamiccontent:dynamiccontents:deleteown`/`deleteother` | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |
| DELETE | `/api/dynamiccontents/{id}/delete` | `dynamiccontent:dynamiccontents:deleteown`/`deleteother` | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Config/config.php:44 @7.x] |

#### Emails — `/api/emails` (keys `email/emails`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/emails` | `email:emails:view` (own-only filter without `viewother`) | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |
| GET | `/api/emails/{id}` | `email:emails:viewown`/`viewother` | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |
| POST | `/api/emails/new` | `email:emails:create` | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |
| POST | `/api/emails/batch/new` | `email:emails:create` | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |
| PUT | `/api/emails/batch/edit` | `email:emails:editown`/`editother` (+`create` for missing ids) | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |
| PATCH | `/api/emails/batch/edit` | `email:emails:editown`/`editother` | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |
| PUT | `/api/emails/{id}/edit` | `email:emails:editown`/`editother` (+`create` if id missing) | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |
| PATCH | `/api/emails/{id}/edit` | `email:emails:editown`/`editother` | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |
| DELETE | `/api/emails/batch/delete?ids=` | `email:emails:deleteown`/`deleteother` | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |
| DELETE | `/api/emails/{id}/delete` | `email:emails:deleteown`/`deleteother` | mautic-emails | [code: app/bundles/EmailBundle/Config/config.php:41 @7.x] |

#### Forms — `/api/forms` (keys `form/forms`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/forms` | `form:forms:view` (own-only filter without `viewother`) | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |
| GET | `/api/forms/{id}` | `form:forms:viewown`/`viewother` | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |
| POST | `/api/forms/new` | `form:forms:create` | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |
| POST | `/api/forms/batch/new` | `form:forms:create` | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |
| PUT | `/api/forms/batch/edit` | `form:forms:editown`/`editother` (+`create` for missing ids) | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |
| PATCH | `/api/forms/batch/edit` | `form:forms:editown`/`editother` | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |
| PUT | `/api/forms/{id}/edit` | `form:forms:editown`/`editother` (+`create` if id missing) | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |
| PATCH | `/api/forms/{id}/edit` | `form:forms:editown`/`editother` | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |
| DELETE | `/api/forms/batch/delete?ids=` | `form:forms:deleteown`/`deleteother` | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |
| DELETE | `/api/forms/{id}/delete` | `form:forms:deleteown`/`deleteother` | mautic-forms | [code: app/bundles/FormBundle/Config/config.php:49 @7.x] |

#### Contacts — `/api/contacts` (keys `contact/contacts`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/contacts` | `lead:leads:view` (own-only filter without `viewother`) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| GET | `/api/contacts/{id}` | `lead:leads:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/contacts/new` | `lead:leads:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/contacts/batch/new` | `lead:leads:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/contacts/batch/edit` | `lead:leads:editown`/`editother` (+`create` for missing ids) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/contacts/batch/edit` | `lead:leads:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/contacts/{id}/edit` | `lead:leads:editown`/`editother` (+`create` if id missing) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/contacts/{id}/edit` | `lead:leads:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/contacts/batch/delete?ids=` | `lead:leads:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/contacts/{id}/delete` | `lead:leads:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |

#### Segments — `/api/segments` (keys `list/lists`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/segments` | `lead:lists:view` (own-only filter without `viewother`) | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| GET | `/api/segments/{id}` | `lead:lists:viewown`/`viewother` | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/segments/new` | `lead:lists:create` | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/segments/batch/new` | `lead:lists:create` | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/segments/batch/edit` | `lead:lists:editown`/`editother` (+`create` for missing ids) | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/segments/batch/edit` | `lead:lists:editown`/`editother` | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/segments/{id}/edit` | `lead:lists:editown`/`editother` (+`create` if id missing) | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/segments/{id}/edit` | `lead:lists:editown`/`editother` | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/segments/batch/delete?ids=` | `lead:lists:deleteown`/`deleteother` | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/segments/{id}/delete` | `lead:lists:deleteown`/`deleteother` | mautic-segments | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |

#### Companies — `/api/companies` (keys `company/companies`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/companies` | `lead:leads:view` (own-only filter without `viewother`) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| GET | `/api/companies/{id}` | `lead:leads:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/companies/new` | `lead:leads:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/companies/batch/new` | `lead:leads:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/companies/batch/edit` | `lead:leads:editown`/`editother` (+`create` for missing ids) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/companies/batch/edit` | `lead:leads:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/companies/{id}/edit` | `lead:leads:editown`/`editother` (+`create` if id missing) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/companies/{id}/edit` | `lead:leads:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/companies/batch/delete?ids=` | `lead:leads:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/companies/{id}/delete` | `lead:leads:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |

#### Custom fields — `/api/fields/{object}` (keys `field/fields`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/fields/{object}` | `lead:fields:view` (own-only filter without `viewother`) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| GET | `/api/fields/{object}/{id}` | `lead:fields:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/fields/{object}/new` | `lead:fields:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/fields/{object}/batch/new` | `lead:fields:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/fields/{object}/batch/edit` | `lead:fields:editown`/`editother` (+`create` for missing ids) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/fields/{object}/batch/edit` | `lead:fields:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/fields/{object}/{id}/edit` | `lead:fields:editown`/`editother` (+`create` if id missing) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/fields/{object}/{id}/edit` | `lead:fields:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/fields/{object}/batch/delete?ids=` | `lead:fields:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/fields/{object}/{id}/delete` | `lead:fields:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |

#### Notes — `/api/notes` (keys `note/notes`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/notes` | `lead:notes:view` (own-only filter without `viewother`) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| GET | `/api/notes/{id}` | `lead:notes:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/notes/new` | `lead:notes:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/notes/batch/new` | `lead:notes:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/notes/batch/edit` | `lead:notes:editown`/`editother` (+`create` for missing ids) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/notes/batch/edit` | `lead:notes:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/notes/{id}/edit` | `lead:notes:editown`/`editother` (+`create` if id missing) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/notes/{id}/edit` | `lead:notes:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/notes/batch/delete?ids=` | `lead:notes:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/notes/{id}/delete` | `lead:notes:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |

#### Devices — `/api/devices` (keys `device/devices`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/devices` | `lead:leads:view` (own-only filter without `viewother`) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| GET | `/api/devices/{id}` | `lead:leads:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/devices/new` | `lead:leads:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/devices/batch/new` | `lead:leads:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/devices/batch/edit` | `lead:leads:editown`/`editother` (+`create` for missing ids) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/devices/batch/edit` | `lead:leads:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/devices/{id}/edit` | `lead:leads:editown`/`editother` (+`create` if id missing) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/devices/{id}/edit` | `lead:leads:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/devices/batch/delete?ids=` | `lead:leads:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/devices/{id}/delete` | `lead:leads:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |

#### Tags — `/api/tags` (keys `tag/tags`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/tags` | `lead:leads:view` (own-only filter without `viewother`) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| GET | `/api/tags/{id}` | `lead:leads:viewown`/`viewother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/tags/new` | `lead:leads:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| POST | `/api/tags/batch/new` | `lead:leads:create` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/tags/batch/edit` | `lead:leads:editown`/`editother` (+`create` for missing ids) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/tags/batch/edit` | `lead:leads:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PUT | `/api/tags/{id}/edit` | `lead:leads:editown`/`editother` (+`create` if id missing) | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| PATCH | `/api/tags/{id}/edit` | `lead:leads:editown`/`editother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/tags/batch/delete?ids=` | `lead:leads:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |
| DELETE | `/api/tags/{id}/delete` | `lead:leads:deleteown`/`deleteother` | mautic-contacts | [code: app/bundles/LeadBundle/Config/config.php:154 @7.x] |

#### Web push notifications — `/api/notifications` (keys `notification/notifications`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/notifications` | `notification:notifications:view` (own-only filter without `viewother`) | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |
| GET | `/api/notifications/{id}` | `notification:notifications:viewown`/`viewother` | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |
| POST | `/api/notifications/new` | `notification:notifications:create` | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |
| POST | `/api/notifications/batch/new` | `notification:notifications:create` | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |
| PUT | `/api/notifications/batch/edit` | `notification:notifications:editown`/`editother` (+`create` for missing ids) | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |
| PATCH | `/api/notifications/batch/edit` | `notification:notifications:editown`/`editother` | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |
| PUT | `/api/notifications/{id}/edit` | `notification:notifications:editown`/`editother` (+`create` if id missing) | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |
| PATCH | `/api/notifications/{id}/edit` | `notification:notifications:editown`/`editother` | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |
| DELETE | `/api/notifications/batch/delete?ids=` | `notification:notifications:deleteown`/`deleteother` | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |
| DELETE | `/api/notifications/{id}/delete` | `notification:notifications:deleteown`/`deleteother` | mautic-channels | [code: app/bundles/NotificationBundle/Config/config.php:65 @7.x] |

#### Landing Pages — `/api/pages` (keys `page/pages`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/pages` | `page:pages:view` (own-only filter without `viewother`) | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |
| GET | `/api/pages/{id}` | `page:pages:viewown`/`viewother` | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |
| POST | `/api/pages/new` | `page:pages:create` | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |
| POST | `/api/pages/batch/new` | `page:pages:create` | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |
| PUT | `/api/pages/batch/edit` | `page:pages:editown`/`editother` (+`create` for missing ids) | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |
| PATCH | `/api/pages/batch/edit` | `page:pages:editown`/`editother` | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |
| PUT | `/api/pages/{id}/edit` | `page:pages:editown`/`editother` (+`create` if id missing) | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |
| PATCH | `/api/pages/{id}/edit` | `page:pages:editown`/`editother` | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |
| DELETE | `/api/pages/batch/delete?ids=` | `page:pages:deleteown`/`deleteother` | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |
| DELETE | `/api/pages/{id}/delete` | `page:pages:deleteown`/`deleteother` | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Config/config.php:55 @7.x] |

#### Point actions — `/api/points` (keys `point/points`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/points` | `point:points:view` (own-only filter without `viewother`) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| GET | `/api/points/{id}` | `point:points:viewown`/`viewother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| POST | `/api/points/new` | `point:points:create` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| POST | `/api/points/batch/new` | `point:points:create` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PUT | `/api/points/batch/edit` | `point:points:editown`/`editother` (+`create` for missing ids) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PATCH | `/api/points/batch/edit` | `point:points:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PUT | `/api/points/{id}/edit` | `point:points:editown`/`editother` (+`create` if id missing) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PATCH | `/api/points/{id}/edit` | `point:points:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| DELETE | `/api/points/batch/delete?ids=` | `point:points:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| DELETE | `/api/points/{id}/delete` | `point:points:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |

#### Point triggers — `/api/points/triggers` (keys `trigger/triggers`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/points/triggers` | `point:triggers:view` (own-only filter without `viewother`) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| GET | `/api/points/triggers/{id}` | `point:triggers:viewown`/`viewother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| POST | `/api/points/triggers/new` | `point:triggers:create` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| POST | `/api/points/triggers/batch/new` | `point:triggers:create` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PUT | `/api/points/triggers/batch/edit` | `point:triggers:editown`/`editother` (+`create` for missing ids) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PATCH | `/api/points/triggers/batch/edit` | `point:triggers:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PUT | `/api/points/triggers/{id}/edit` | `point:triggers:editown`/`editother` (+`create` if id missing) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PATCH | `/api/points/triggers/{id}/edit` | `point:triggers:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| DELETE | `/api/points/triggers/batch/delete?ids=` | `point:triggers:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| DELETE | `/api/points/triggers/{id}/delete` | `point:triggers:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |

#### Point groups — `/api/points/groups` (keys `pointGroup/pointGroups`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/points/groups` | `point:groups:view` (own-only filter without `viewother`) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| GET | `/api/points/groups/{id}` | `point:groups:viewown`/`viewother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| POST | `/api/points/groups/new` | `point:groups:create` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| POST | `/api/points/groups/batch/new` | `point:groups:create` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PUT | `/api/points/groups/batch/edit` | `point:groups:editown`/`editother` (+`create` for missing ids) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PATCH | `/api/points/groups/batch/edit` | `point:groups:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PUT | `/api/points/groups/{id}/edit` | `point:groups:editown`/`editother` (+`create` if id missing) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PATCH | `/api/points/groups/{id}/edit` | `point:groups:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| DELETE | `/api/points/groups/batch/delete?ids=` | `point:groups:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| DELETE | `/api/points/groups/{id}/delete` | `point:groups:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |

#### Point insights — `/api/points/insights` (keys `insight/insights`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/points/insights` | `point:insights:view` (own-only filter without `viewother`) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| GET | `/api/points/insights/{id}` | `point:insights:viewown`/`viewother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| POST | `/api/points/insights/new` | `point:insights:create` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| POST | `/api/points/insights/batch/new` | `point:insights:create` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PUT | `/api/points/insights/batch/edit` | `point:insights:editown`/`editother` (+`create` for missing ids) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PATCH | `/api/points/insights/batch/edit` | `point:insights:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PUT | `/api/points/insights/{id}/edit` | `point:insights:editown`/`editother` (+`create` if id missing) | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| PATCH | `/api/points/insights/{id}/edit` | `point:insights:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| DELETE | `/api/points/insights/batch/delete?ids=` | `point:insights:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |
| DELETE | `/api/points/insights/{id}/delete` | `point:insights:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/PointBundle/Config/config.php:45 @7.x] |

#### Projects — `/api/projects` (keys `project/projects`; 7.x after 7.2.1, unreleased; [PR #15569])

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/projects` | `project:project:view` (own-only filter without `viewother`) | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |
| GET | `/api/projects/{id}` | `project:project:viewown`/`viewother` | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |
| POST | `/api/projects/new` | `project:project:create` | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |
| POST | `/api/projects/batch/new` | `project:project:create` | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |
| PUT | `/api/projects/batch/edit` | `project:project:editown`/`editother` (+`create` for missing ids) | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |
| PATCH | `/api/projects/batch/edit` | `project:project:editown`/`editother` | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |
| PUT | `/api/projects/{id}/edit` | `project:project:editown`/`editother` (+`create` if id missing) | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |
| PATCH | `/api/projects/{id}/edit` | `project:project:editown`/`editother` | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |
| DELETE | `/api/projects/batch/delete?ids=` | `project:project:deleteown`/`deleteother` | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |
| DELETE | `/api/projects/{id}/delete` | `project:project:deleteown`/`deleteother` | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Config/config.php:17 @7.x] |

#### Reports — `/api/reports` (keys `report/reports`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/reports` | `report:reports:view` (own-only filter without `viewother`) | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |
| GET | `/api/reports/{id}` | `report:reports:viewown`/`viewother` | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |
| POST | `/api/reports/new` | `report:reports:create` | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |
| POST | `/api/reports/batch/new` | `report:reports:create` | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |
| PUT | `/api/reports/batch/edit` | `report:reports:editown`/`editother` (+`create` for missing ids) | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |
| PATCH | `/api/reports/batch/edit` | `report:reports:editown`/`editother` | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |
| PUT | `/api/reports/{id}/edit` | `report:reports:editown`/`editother` (+`create` if id missing) | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |
| PATCH | `/api/reports/{id}/edit` | `report:reports:editown`/`editother` | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |
| DELETE | `/api/reports/batch/delete?ids=` | `report:reports:deleteown`/`deleteother` | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |
| DELETE | `/api/reports/{id}/delete` | `report:reports:deleteown`/`deleteother` | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Config/config.php:55 @7.x] |

#### Text messages (SMS) — `/api/smses` (keys `sms/smses`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/smses` | `sms:smses:view` (own-only filter without `viewother`) | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |
| GET | `/api/smses/{id}` | `sms:smses:viewown`/`viewother` | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |
| POST | `/api/smses/new` | `sms:smses:create` | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |
| POST | `/api/smses/batch/new` | `sms:smses:create` | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |
| PUT | `/api/smses/batch/edit` | `sms:smses:editown`/`editother` (+`create` for missing ids) | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |
| PATCH | `/api/smses/batch/edit` | `sms:smses:editown`/`editother` | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |
| PUT | `/api/smses/{id}/edit` | `sms:smses:editown`/`editother` (+`create` if id missing) | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |
| PATCH | `/api/smses/{id}/edit` | `sms:smses:editown`/`editother` | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |
| DELETE | `/api/smses/batch/delete?ids=` | `sms:smses:deleteown`/`deleteother` | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |
| DELETE | `/api/smses/{id}/delete` | `sms:smses:deleteown`/`deleteother` | mautic-channels | [code: app/bundles/SmsBundle/Config/config.php:35 @7.x] |

#### Stages — `/api/stages` (keys `stage/stages`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/stages` | `stage:stages:view` (own-only filter without `viewother`) | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |
| GET | `/api/stages/{id}` | `stage:stages:viewown`/`viewother` | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |
| POST | `/api/stages/new` | `stage:stages:create` | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |
| POST | `/api/stages/batch/new` | `stage:stages:create` | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |
| PUT | `/api/stages/batch/edit` | `stage:stages:editown`/`editother` (+`create` for missing ids) | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |
| PATCH | `/api/stages/batch/edit` | `stage:stages:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |
| PUT | `/api/stages/{id}/edit` | `stage:stages:editown`/`editother` (+`create` if id missing) | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |
| PATCH | `/api/stages/{id}/edit` | `stage:stages:editown`/`editother` | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |
| DELETE | `/api/stages/batch/delete?ids=` | `stage:stages:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |
| DELETE | `/api/stages/{id}/delete` | `stage:stages:deleteown`/`deleteother` | mautic-points-and-stages | [code: app/bundles/StageBundle/Config/config.php:17 @7.x] |

#### Users — `/api/users` (keys `user/users`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/users` | `user:users (new/edit use plain create/edit):view` (own-only filter without `viewother`) | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| GET | `/api/users/{id}` | `user:users (new/edit use plain create/edit):viewown`/`viewother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| POST | `/api/users/new` | `user:users (new/edit use plain create/edit):create` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| POST | `/api/users/batch/new` | `user:users (new/edit use plain create/edit):create` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| PUT | `/api/users/batch/edit` | `user:users (new/edit use plain create/edit):editown`/`editother` (+`create` for missing ids) | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| PATCH | `/api/users/batch/edit` | `user:users (new/edit use plain create/edit):editown`/`editother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| PUT | `/api/users/{id}/edit` | `user:users (new/edit use plain create/edit):editown`/`editother` (+`create` if id missing) | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| PATCH | `/api/users/{id}/edit` | `user:users (new/edit use plain create/edit):editown`/`editother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| DELETE | `/api/users/batch/delete?ids=` | `user:users (new/edit use plain create/edit):deleteown`/`deleteother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| DELETE | `/api/users/{id}/delete` | `user:users (new/edit use plain create/edit):deleteown`/`deleteother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |

#### Roles — `/api/roles` (keys `role/roles`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/roles` | `user:roles:view` (own-only filter without `viewother`) | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| GET | `/api/roles/{id}` | `user:roles:viewown`/`viewother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| POST | `/api/roles/new` | `user:roles:create` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| POST | `/api/roles/batch/new` | `user:roles:create` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| PUT | `/api/roles/batch/edit` | `user:roles:editown`/`editother` (+`create` for missing ids) | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| PATCH | `/api/roles/batch/edit` | `user:roles:editown`/`editother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| PUT | `/api/roles/{id}/edit` | `user:roles:editown`/`editother` (+`create` if id missing) | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| PATCH | `/api/roles/{id}/edit` | `user:roles:editown`/`editother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| DELETE | `/api/roles/batch/delete?ids=` | `user:roles:deleteown`/`deleteother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |
| DELETE | `/api/roles/{id}/delete` | `user:roles:deleteown`/`deleteother` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Config/config.php:78 @7.x] |

#### Webhooks — `/api/hooks` (keys `hook/hooks`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/hooks` | `webhook:webhooks:view` (own-only filter without `viewother`) | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |
| GET | `/api/hooks/{id}` | `webhook:webhooks:viewown`/`viewother` | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |
| POST | `/api/hooks/new` | `webhook:webhooks:create` | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |
| POST | `/api/hooks/batch/new` | `webhook:webhooks:create` | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |
| PUT | `/api/hooks/batch/edit` | `webhook:webhooks:editown`/`editother` (+`create` for missing ids) | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |
| PATCH | `/api/hooks/batch/edit` | `webhook:webhooks:editown`/`editother` | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |
| PUT | `/api/hooks/{id}/edit` | `webhook:webhooks:editown`/`editother` (+`create` if id missing) | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |
| PATCH | `/api/hooks/{id}/edit` | `webhook:webhooks:editown`/`editother` | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |
| DELETE | `/api/hooks/batch/delete?ids=` | `webhook:webhooks:deleteown`/`deleteother` | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |
| DELETE | `/api/hooks/{id}/delete` | `webhook:webhooks:deleteown`/`deleteother` | mautic-webhooks | [code: app/bundles/WebhookBundle/Config/config.php:17 @7.x] |

#### Focus Items (plugin) — `/api/focus` (keys `focus/focus`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/focus` | `focus:items:view` (own-only filter without `viewother`) | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |
| GET | `/api/focus/{id}` | `focus:items:viewown`/`viewother` | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |
| POST | `/api/focus/new` | `focus:items:create` | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |
| POST | `/api/focus/batch/new` | `focus:items:create` | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |
| PUT | `/api/focus/batch/edit` | `focus:items:editown`/`editother` (+`create` for missing ids) | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |
| PATCH | `/api/focus/batch/edit` | `focus:items:editown`/`editother` | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |
| PUT | `/api/focus/{id}/edit` | `focus:items:editown`/`editother` (+`create` if id missing) | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |
| PATCH | `/api/focus/{id}/edit` | `focus:items:editown`/`editother` | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |
| DELETE | `/api/focus/batch/delete?ids=` | `focus:items:deleteown`/`deleteother` | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |
| DELETE | `/api/focus/{id}/delete` | `focus:items:deleteown`/`deleteother` | mautic-channels | [code: plugins/MauticFocusBundle/Config/config.php:32 @7.x] |

#### Tweets (plugin) — `/api/tweets` (keys `tweet/tweets`)

| Method | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET | `/api/tweets` | `mauticSocial:tweets:view` (own-only filter without `viewother`) | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |
| GET | `/api/tweets/{id}` | `mauticSocial:tweets:viewown`/`viewother` | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |
| POST | `/api/tweets/new` | `mauticSocial:tweets:create` | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |
| POST | `/api/tweets/batch/new` | `mauticSocial:tweets:create` | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |
| PUT | `/api/tweets/batch/edit` | `mauticSocial:tweets:editown`/`editother` (+`create` for missing ids) | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |
| PATCH | `/api/tweets/batch/edit` | `mauticSocial:tweets:editown`/`editother` | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |
| PUT | `/api/tweets/{id}/edit` | `mauticSocial:tweets:editown`/`editother` (+`create` if id missing) | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |
| PATCH | `/api/tweets/{id}/edit` | `mauticSocial:tweets:editown`/`editother` | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |
| DELETE | `/api/tweets/batch/delete?ids=` | `mauticSocial:tweets:deleteown`/`deleteother` | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |
| DELETE | `/api/tweets/{id}/delete` | `mauticSocial:tweets:deleteown`/`deleteother` | mautic-channels | [code: plugins/MauticSocialBundle/Config/config.php:34 @7.x] |

## 5. v2 (API Platform) resources

All under `/api/v2`. Unless noted each declares `GetCollection`, `Post`, `Get`, `Put`, `Patch`, `Delete` with
`is_granted(...)` security; ownership-scoped item operations pass `object`.
[code: app/bundles/ApiBundle/Tests/Functional/OwnershipScopedSecurityMetadataTest.php @7.x] Interactive docs are at
`/api/v2/docs` (and `/api/v2` in a logged-in browser). [code: app/config/config.php:410-421 @7.x]
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/api_v2.html]

| Methods | Path | Permission | Owning skill | Citation |
|---|---|---|---|---|
| GET, POST, GET/PUT/PATCH/DELETE `{id}` | `/api/v2/contacts` | `lead:leads:*` (own/other) | mautic-contacts | [code: app/bundles/LeadBundle/Entity/Lead.php:33-53 @7.x] |
| same | `/api/v2/companies` | `lead:leads:*` | mautic-contacts | [code: app/bundles/LeadBundle/Entity/Company.php:25-28 @7.x] |
| same | `/api/v2/segments` | `lead:lists:*` | mautic-segments | [code: app/bundles/LeadBundle/Entity/LeadList.php:29-32 @7.x] |
| same | `/api/v2/contactcategories` | `lead:leads:*` | mautic-contacts | [code: app/bundles/LeadBundle/Entity/LeadCategory.php:17-20 @7.x] |
| same | derived from class name (`LeadField`) | `lead:leads:*` | mautic-contacts | [code: app/bundles/LeadBundle/Entity/LeadField.php:29-31 @7.x] |
| same | derived from class name (`Tag`) | `tagManager:tagManager:view/create/edit/delete` | mautic-contacts | [code: app/bundles/LeadBundle/Entity/Tag.php:23-25 @7.x] |
| same | `/api/v2/webhooks` | `webhook:webhooks:*` | mautic-webhooks | [code: app/bundles/WebhookBundle/Entity/Webhook.php:28-50 @7.x] |
| same (custom `UserProcessor` on writes) | `/api/v2/users` | `user:users:*` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Entity/User.php:32-35 @7.x] |
| same | derived (`Role`, `Permission`) | `user:roles:*` | mautic-users-and-permissions | [code: app/bundles/UserBundle/Entity/Role.php:26-28 @7.x] |
| same | `/api/v2/focus_items` | `focus:items:*` | mautic-channels | [code: plugins/MauticFocusBundle/Entity/Focus.php:26-29 @7.x] |
| same | derived (`Report`) | `report:reports:*` | mautic-reports-and-dashboard | [code: app/bundles/ReportBundle/Entity/Report.php:28-30 @7.x] |
| same | derived (`Message`, `Channel`) | `channel:messages:*` | mautic-channels | [code: app/bundles/ChannelBundle/Entity/Message.php:27-29 @7.x] |
| same | derived (`Campaign`, `Event`) | `campaign:campaigns:*` | mautic-campaigns | [code: app/bundles/CampaignBundle/Entity/Campaign.php:36-38 @7.x] |
| same | derived (`DynamicContent`) | `dynamiccontent:dynamiccontents:*` | mautic-pages-and-tracking | [code: app/bundles/DynamicContentBundle/Entity/DynamicContent.php:39-41 @7.x] |
| same | `/api/v2/projects` | `project:projects:view/create/edit/delete` (non-ownership) | mautic-assets-categories-projects | [code: app/bundles/ProjectBundle/Entity/Project.php:26-28 @7.x] |
| same | derived (`Point`, `Trigger`, `TriggerEvent`) | `point:triggers:*` for all three | mautic-points-and-stages | [code: app/bundles/PointBundle/Entity/Point.php:28-30 @7.x] |
| same | derived (`Email`) | `email:emails:*` | mautic-emails | [code: app/bundles/EmailBundle/Entity/Email.php:49-51 @7.x] |
| same | derived (`Stage`) | `stage:stages:*` | mautic-points-and-stages | [code: app/bundles/StageBundle/Entity/Stage.php:26-28 @7.x] |
| same | derived (`Form`, `Field`, `Action`) | `form:forms:*` | mautic-forms | [code: app/bundles/FormBundle/Entity/Form.php:29-31 @7.x] |
| same | derived (`Notification`) | `notification:notifications:*` | mautic-channels | [code: app/bundles/NotificationBundle/Entity/Notification.php:29-31 @7.x] |
| same; **GetCollection has no security expression** | derived (`Category`) | `category:categories:*` (non-ownership) on the other operations | mautic-assets-categories-projects | [code: app/bundles/CategoryBundle/Entity/Category.php:23-26 @7.x] |
| GetCollection, Get only | derived (`IpAddress`) | `lead:leads:viewown`/`viewother` | mautic-contacts | [code: app/bundles/CoreBundle/Entity/IpAddress.php:13-15 @7.x] |
| same | derived (`Asset`) | `asset:assets:*` | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Entity/Asset.php:32-34 @7.x] |
| GetCollection, Get only | `/api/v2/downloads` | `asset:assets:view*` (ownership via `getPermissionUser()`) | mautic-assets-categories-projects | [code: app/bundles/AssetBundle/Entity/Download.php:16-18 @7.x] [code: app/bundles/AssetBundle/Tests/Functional/ApiPlatform/DownloadOwnershipApiV2AuthorizationRegressionTest.php:67 @7.x] |
| same | `/api/v2/pages` | `page:pages:*` | mautic-pages-and-tracking | [code: app/bundles/PageBundle/Entity/Page.php:36-38 @7.x] [code: app/bundles/ApiBundle/Tests/Functional/Serializer/PutOperationTest.php:50-93 @7.x] |
| same | derived (`Sms`) | `sms:smses:*` | mautic-channels | [code: app/bundles/SmsBundle/Entity/Sms.php:37-39 @7.x] |
| same | derived (`Monitoring`) | `mauticSocial:monitoring:view/...` (non-ownership) | mautic-channels | [code: plugins/MauticSocialBundle/Entity/Monitoring.php:21-23 @7.x] |

Rows marked "derived" have no `uriTemplate`; API Platform derives the path from the short class name, so check
`/api/v2/docs` for the exact segment. The permission column shows the first security expression of each resource
(`viewown` for ownership-scoped ones); the `Channel` entity also uses `channel:messages:*`, `Event` uses
`campaign:campaigns:*`, `Field`/`Action` use `form:forms:*`, and `Permission` uses `user:roles:*`.
[code: app/bundles/ChannelBundle/Entity/Channel.php:23-25 @7.x] [code: app/bundles/CampaignBundle/Entity/Event.php:27-29 @7.x]
[code: app/bundles/FormBundle/Entity/Field.php:23-25 @7.x] [code: app/bundles/UserBundle/Entity/Permission.php:21-23 @7.x]

## 6. Documentation discrepancies found while building this table

- Users delete is the standard `DELETE /api/users/{id}/delete`; the docs show `DELETE /users/ID` with no suffix, which
  matches no route. [code: app/bundles/UserBundle/Config/config.php:79-84 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/users.html#delete-user]
- Campaign export is `GET`; the plugin-extension docs say `POST /api/campaigns/export/{id}`.
  [code: app/bundles/CampaignBundle/Config/config.php:132-134 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#exporting-via-api]
- `POST /api/companies/batch/addcontacts` is on the 7.x branch, not yet released (after 7.2.1; [PR #16512]), but is documented only in the 8.0 docs; the 8.x branch
  does not have it yet (it arrives with the next forward merge).
  [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:122 @7.x]
  [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/companies.html#batch-add-contacts-to-companies]
- The Point Group docs write the paths with a leading `/api/`; the routes are the normal `/api/contacts/{contactId}/points/groups...`.
  [code: app/bundles/PointBundle/Config/config.php:91 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#get-all-contact-point-groups-scores]
- `POST /api/emails/{id}/send` reads `lists`, `limit` and `batch` from the body; the docs call the Segment override
  `listIds` (the PHP library's argument name). [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:119-121 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/emails.html]
- Stats `limit` defaults to 100 in code; the docs say 30.
  [code: app/bundles/CoreBundle/Controller/Api/StatsApiController.php:25-32 @7.x]
  [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stats.html#get-stats-from-a-table]
