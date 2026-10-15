# Bundled integration plugins (Mautic 7.x)

One section per bundled integration plugin: purpose, framework, data direction, commands, status/maintenance and
limitations. "Status" is what code and docs show; nothing here tests the remote APIs live.

## Contents
- Overview table
- 1 Salesforce
- 2 HubSpot
- 3 Zoho CRM
- 4 Microsoft Dynamics CRM
- 5 SugarCRM
- 6 vTiger
- 7 ConnectWise
- 8 Shared CRM behaviour (CrmAbstractIntegration)
- 9 Clearbit
- 10 FullContact
- 11 MailChimp, Constant Contact, iContact (EmailMarketing)
- 12 Zapier
- 13 Gmail and Outlook
- 14 Other plugins (pointers)

## Overview
| Plugin dir | Integrations | Framework | Direction | Tests |
|---|---|---|---|---|
| `plugins/MauticCrmBundle` | Salesforce, Hubspot, Zoho, Dynamics, Sugarcrm, Vtiger, Connectwise | legacy `CrmAbstractIntegration` | push (+ pull for most) | unit tests only |
| `plugins/MauticClearbitBundle` | Clearbit | IntegrationsBundle `BasicIntegration` | pull (enrichment) | unit + functional |
| `plugins/MauticFullContactBundle` | FullContact | legacy | pull (enrichment) | none |
| `plugins/MauticEmailMarketingBundle` | Mailchimp, ConstantContact, Icontact | legacy | push only | none |
| `plugins/MauticZapierBundle` | none (info card only) | none | n/a | none |
| `plugins/MauticGmailBundle` | Gmail | IntegrationsBundle | inbound tracking | unit |
| `plugins/MauticOutlookBundle` | Outlook | legacy | inbound tracking | unit |
Sources: [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:17 @7.x] [code: plugins/MauticClearbitBundle/Integration/ClearbitIntegration.php:10-32 @7.x] [code: plugins/MauticGmailBundle/Integration/GmailIntegration.php:10-26 @7.x] [code: plugins/MauticOutlookBundle/Integration/OutlookIntegration.php:10-53 @7.x]

No CRM uses the IntegrationsBundle sync engine, so `mautic:integrations:sync` does nothing for them. Their pull and push run through `mautic:integration:fetchleads`. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:17 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/hubspot.html#configure-the-hubspot-crm-plugin]

There is no Pipedrive integration class. Only `pipedrive.png` and `cobalt.png` images remain, but the docs still have a title-only Pipedrive page. [code: plugins/MauticCrmBundle/Assets/img/pipedrive.png @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/pipedrive.html]

History: Pipedrive and Citrix/GoTo were deprecated in 4.4.9 and removed in 5.0; Rackspace/OpenStack storage was removed in 3.0; Clearbit is removed in 8.x only. Details: references/pr-history.md section 3. [PR #12081] [PR #12333] [PR #8310] [PR #17785]

## 1 Salesforce
- Purpose: two-way Contact/Lead/Account sync, CRM campaign membership, activity export. Framework: legacy. [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:119-122 @7.x]
- Features: `push_lead`, `get_leads`, `push_leads`. Settings: `sandbox`, `updateOwner`, `updateBlanks`, `updateDncByDate`, `objects` (Lead/Contact/company/Activity), `activityEvents`, `namespace`. [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:514-632 @7.x]
- Auth: OAuth2 against `login.salesforce.com` (or `test.salesforce.com` with sandbox), scope `api refresh_token`. REST API v34.0, composite v38.0. [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:79-164 @7.x]
- Commands: `mautic:integration:fetchleads -i Salesforce` and `mautic:integration:pushleadactivity -i Salesforce` (creates `mautic_timeline__c` records). [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:987-1095 @7.x]
- Behaviour:
  - Pull uses `SystemModStamp` windows, excludes converted Leads, and pages with a retrying paginator. [code: plugins/MauticCrmBundle/Api/SalesforceApi.php:314-377 @7.x]
  - Bulk push uses composite chunks of 25 with `allOrNone=false`. It processes Contacts before Leads and marks duplicates `lead-duplicate`. [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:1113-1297,1601-1726 @7.x]
  - `State` is removed unless `Country` is one of nine supported countries. [code: plugins/MauticCrmBundle/Integration/Salesforce/Helper/StateValidationHelper.php:12-46 @7.x]
  - DNC sync by date compares the SF `HasOptedOutOfEmail` history with the Mautic audit log; the later change wins. [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:2512-2627 @7.x]
  - `INVALID_SESSION_ID` refreshes the token once, and `UNABLE_TO_LOCK_ROW` retries 3 times. [code: plugins/MauticCrmBundle/Api/SalesforceApi.php:519-607 @7.x]
  - A missing column removes that mapping and retries; `HasOptedOutOfEmail` instead notifies admins. [code: plugins/MauticCrmBundle/Api/SalesforceApi.php:654-708 @7.x]
  - The segment filter "Integration campaign members" (`integration_campaigns`) uses `getCampaignMembers()`. [code: plugins/MauticCrmBundle/EventListener/LeadListSubscriber.php:32-119 @7.x]
- Status: the most complete and most tested CRM, with documentation deferred to the KB. [docs: https://docs.mautic.org/en/7.2/plugins/salesforce.html]
- Limitations and bugs:
  - `pushCompany` records `internalEntity='lead'` for Accounts. [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:827-830 @7.x]
  - `pushLeadActivity` formats dates as `'Y-m-d H:m:s'`, with the month in the minutes slot. [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:1023-1024 @7.x]
  - The class is `final` in 8.x. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- History: DNC sync by date added in 2.12 and changed in 5.1 (new opted-out records, ticked-then-unticked); stale-field self-healing in 5.2. [PR #4920] [PR #13411] [PR #13444] [PR #13406]

## 2 HubSpot
- Purpose: push Contacts, and pull Contacts/Companies. Framework: legacy. Features: `push_lead`, `get_leads`. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:46-49 @7.x]
- Auth: with `accessKey` (private-app token), auth is bearer `oauth2`. Otherwise it uses the deprecated `hapikey` query key. There is no OAuth authorization step. [code: plugins/MauticCrmBundle/Integration/HubspotIntegration.php:38-97,240-245 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/hubspot.html#hubspot-api-key]
- Push: `POST /contacts/v1/contact/createOrUpdate/email/<email>`. An unknown property is auto-created as a string, and `lifecyclestage`/`associatedcompanyid` are never sent. [code: plugins/MauticCrmBundle/Integration/HubspotIntegration.php:546-594 @7.x]
- Pull: recently-updated v1/v2 endpoints, 100 per page. `lifecyclestage` maps to a Mautic Stage by name. [code: plugins/MauticCrmBundle/Integration/HubspotIntegration.php:339-517 @7.x]
- Commands: `mautic:integration:fetchleads --integration=Hubspot --fetch-all` per docs. [docs: https://docs.mautic.org/en/7.2/plugins/hubspot.html#configure-the-hubspot-crm-plugin]
- Webhook: public `POST /plugin/{integration}/contact_data` always resolves Hubspot. It passes a scalar id where `getLeads()` expects an array, so inferred: the webhook does not fetch the Contact. [code: plugins/MauticCrmBundle/Controller/PublicController.php:14-48 @7.x]
- Limitations:
  - "Recently modified" endpoints see only about 30 days, even with `--fetch-all`. [docs: https://docs.mautic.org/en/7.2/plugins/hubspot.html#troubleshooting-hubspot-integration]
  - The route `mautic_integration_companies` points to a missing method; it is removed in 8.x. [code: plugins/MauticCrmBundle/Config/config.php:19-25 @7.x]
  - HubSpot creates Contacts only for valid emails. [docs: https://docs.mautic.org/en/7.2/plugins/hubspot.html#troubleshooting-hubspot-integration]
- History: API-key auth replaced by a Private App token in 4.4.5/5.0. [PR #11470] [PR #11857]

## 3 Zoho CRM
- Purpose: push, pull (Leads/Contacts/Accounts) and bulk push. Framework: legacy. Features add `push_leads`. [code: plugins/MauticCrmBundle/Integration/ZohoIntegration.php:93-96 @7.x]
- Auth: OAuth2 against `accounts.<datacenter>`; the data centre (`zoho.com`/`.eu`/`.co.jp`/`.com.cn`) is required. The API base is `api_domain/crm/v2`. [code: plugins/MauticCrmBundle/Integration/ZohoIntegration.php:32-117,612-669 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/zoho_crm.html#configure-the-zoho-crm-plugin]
- Behaviour:
  - `pushLead` always targets the `Leads` module and searches by Email. [code: plugins/MauticCrmBundle/Integration/ZohoIntegration.php:775-794 @7.x]
  - Bulk push caps batches at 100. [code: plugins/MauticCrmBundle/Integration/ZohoIntegration.php:1005-1081 @7.x]
  - `updateBlanks` treats the string `'null'` as blank. [code: plugins/MauticCrmBundle/Integration/ZohoIntegration.php:1005-1081 @7.x]
- Limitations:
  - Both accounts must use English, because field aliases change by language. [docs: https://docs.mautic.org/en/7.2/plugins/zoho_crm.html#language-configuration-warning]
  - Empty Mautic values are sent as "Unknown". [docs: https://docs.mautic.org/en/7.2/plugins/zoho_crm.html#configure-the-zoho-crm-plugin]
- History: moved to Zoho REST API v2 with OAuth in 2.16; installs had to re-authorise. [PR #8272]

## 4 Microsoft Dynamics CRM
- Purpose: push and pull contacts/companies. Framework: legacy. Auth: OAuth2 via `login.microsoftonline.com/common`. API: Web API v8.2 with a 300 s timeout. [code: plugins/MauticCrmBundle/Integration/DynamicsIntegration.php:41-159 @7.x] [code: plugins/MauticCrmBundle/Api/DynamicsApi.php:11-60 @7.x]
- Behaviour: an existing mapping triggers a PATCH, otherwise a POST that parses `OData-EntityId`. Pull follows `@odata.nextLink`, 200 per page. [code: plugins/MauticCrmBundle/Integration/DynamicsIntegration.php:298-423 @7.x]
- Limitations: `updateBlanks` is added to every form area. The docs page is title only. [code: plugins/MauticCrmBundle/Integration/DynamicsIntegration.php:52-100 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/microsoft_dynamics_crm.html]
- History: the plural `Contacts` object fix landed in 5.0.4. [PR #13208]

## 5 SugarCRM
- Purpose: push and pull (Leads/Contacts/company), DNC sync, activity push. Framework: legacy. [code: plugins/MauticCrmBundle/Integration/SugarcrmIntegration.php:67-71,417-510 @7.x]
- Auth: version 6 uses REST login with an md5 password. Version 7 uses an OAuth2 password grant and re-logs in on every `isAuthorized()` call. [code: plugins/MauticCrmBundle/Integration/SugarcrmIntegration.php:100-156,567-643 @7.x]
- DNC: `updateDnc` pushes `email_opt_out`/`invalid_email`. On pull, `opt_out` adds UNSUBSCRIBED DNC. [code: plugins/MauticCrmBundle/Integration/SugarcrmIntegration.php:1241-1309 @7.x]
- Limitations: deleted-contact fetch is a `@todo`, and there are `TODO 7.x` markers in the API. The docs page is title only. [code: plugins/MauticCrmBundle/Integration/SugarcrmIntegration.php:1395 @7.x] [code: plugins/MauticCrmBundle/Api/SugarcrmApi.php:298,481 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/sugar_crm.html]
- History: the `/filter` endpoint switched to GET in 4.2. [PR #10667]

## 6 vTiger
- Purpose: push only (`push_lead`). Framework: legacy. Auth: `getchallenge` + `login` on `<url>/webservice.php`. `assigned_user_id` is forced to the authenticated user. [code: plugins/MauticCrmBundle/Integration/VtigerIntegration.php:25-28,62-222 @7.x]
- Limitations: Vtiger Cloud has the Contacts module disabled by default, which causes "Permission to perform the operation is denied". [docs: https://docs.mautic.org/en/7.2/plugins/vtiger.html#mautic-vtiger-crm-plugin]

## 7 ConnectWise
- Purpose: push and pull Contacts/Companies, plus creating CW Activities from the campaign action. Framework: legacy. Auth: `basic` plus a `clientId` header. [code: plugins/MauticCrmBundle/Integration/ConnectwiseIntegration.php:36-155 @7.x]
- Behaviour: `pushLead` updates every CW contact with that email. With `push_activities` it creates an Activity recorded as `Activities`. [code: plugins/MauticCrmBundle/Integration/ConnectwiseIntegration.php:566-626,971-988 @7.x] [code: plugins/MauticCrmBundle/Form/Type/IntegrationCampaignsTaskType.php:27-79 @7.x]
- Limitations: inverted `update_mautic` convention on update, and `customFields` is a todo. [code: plugins/MauticCrmBundle/Integration/ConnectwiseIntegration.php:344,633 @7.x]
- History: the appcookie credential was replaced by a Client ID in 5.1. [PR #13408]

## 8 Shared CRM behaviour (CrmAbstractIntegration)
- `pushLead` returns `[]` with no mapped fields, `false` on an empty payload or an error, and `true` on success. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:57-84 @7.x]
- Activity export defaults to `point.gained, form.submitted, email.read` when the setting is absent. A present-but-empty setting sends nothing. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:178-266 @7.x]
- A pull without any unique-identifier value returns `null`, so no Contact is created. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:357-389 @7.x]
- For existing Contacts only `update_mautic=1` fields are written. `updateBlanks` additionally fills empty fields. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:391-410,476-505 @7.x]
- `updateOwner` sets the owner from `owner_email` when a matching user exists. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:437-443 @7.x]
- Companies without `companyname` are not created. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:271-326 @7.x]
- A trailing `/` in the `url` key is stripped. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:23-33 @7.x]
- History: `getLeadData()` detaches the wrong entities from 5.0.0 to 7.2.1, so activity push silently does nothing; fixed in 7.2.2. The 7.x snapshot still has the bug. [PR #12361] [PR #17815] [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:245-254 @7.x]
- Add a CRM: subclass `CrmAbstractIntegration`, add `Api/<Name>Api extends CrmApi`, and alias `mautic.integration.<name>`. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:155-163 @7.x]

## 9 Clearbit
- Purpose: enrich Contacts (by email) and Companies (by website domain), asynchronously via webhook. Framework: IntegrationsBundle (`BasicIntegration` + `ConfigSupport`). Direction: pull. [code: plugins/MauticClearbitBundle/Integration/Support/ConfigSupport.php:15-38 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/clearbit.html]
- Keys: `apikey`, `auto_update`. Lookups run from Contact/Company buttons, and on save when `auto_update` is on. At most one lookup per entity per hour (cache id by `YmdH`). Batches are capped at 20. [code: plugins/MauticClearbitBundle/Helper/LookupHelper.php:55-59,169-184 @7.x] [code: plugins/MauticClearbitBundle/Controller/ClearbitController.php:180-207 @7.x]
- Callback `/clearbit/callback` fills only empty fields. Mautic must be publicly reachable. [code: plugins/MauticClearbitBundle/Controller/PublicController.php:60-259 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/clearbit.html#clearbit-plugin-requirements]
- Limitations:
  - Company lookups have no permission check. [code: plugins/MauticClearbitBundle/Controller/ClearbitController.php:282-515 @7.x]
  - Notification type is the literal `'FullContact'`. [code: plugins/MauticClearbitBundle/Controller/PublicController.php:50-53 @7.x]
  - Uses raw cURL rather than Mautic's HTTP client. [code: plugins/MauticClearbitBundle/Services/Clearbit_Base.php:79-126 @7.x]
- Status: **removed in 8.x** (service sunset after the HubSpot acquisition). [PR #17785]
- History: moved from `AbstractIntegration` to `BasicIntegration` in 7.2. [PR #16586]

## 10 FullContact
- Purpose: same enrichment flow as Clearbit against FullContact v2. Framework: legacy, auth `none`, key `apikey`. [code: plugins/MauticFullContactBundle/Integration/FullContactIntegration.php:13-111 @7.x]
- Limitations:
  - The plugin targets the v2 API. Inferred: the integer status is compared to strings, so `NoCreditException` and rate limiting never trigger. [code: plugins/MauticFullContactBundle/Services/FullContact_Base.php:171-178 @7.x]
  - The stats call runs from the admin's browser and exposes the key there. [code: plugins/MauticFullContactBundle/Assets/js/fullcontact.js:31 @7.x]
  - Person saves bypass `LEAD_POST_SAVE`. [code: plugins/MauticFullContactBundle/Controller/PublicController.php:88-220 @7.x]
  - No tests, and the docs page is title only. [docs: https://docs.mautic.org/en/7.2/plugins/fullcontact.html]
- 8.x: `FullContact_Base` becomes abstract, and `Exception\ApiException` is deleted. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]

## 11 MailChimp, Constant Contact, iContact (EmailMarketing)
- Purpose: push a Contact to a list through `plugin.leadpush` only (feature `push_lead`). Framework: legacy. Nothing is written to `integration_entity`. There are no commands. [code: plugins/MauticEmailMarketingBundle/Integration/EmailAbstractIntegration.php:16-96 @7.x]
- MailChimp:
  - Auth is basic (username + API key), or OAuth2 when `client_id` is set. API v3.0 on `<dc>.api.mailchimp.com`. [code: plugins/MauticEmailMarketingBundle/Integration/MailchimpIntegration.php:19-70 @7.x]
  - Push status is `pending` with double opt-in, else `subscribed`. Double opt-in and welcome Email default to on. [code: plugins/MauticEmailMarketingBundle/Integration/MailchimpIntegration.php:123-157 @7.x] [code: plugins/MauticEmailMarketingBundle/Form/Type/MailchimpType.php:72,77 @7.x] [docs: https://docs.mautic.org/en/7.2/plugins/mailchimp.html#other-configuration-options]
  - Field mapping appears only after a list is chosen and saved. [docs: https://docs.mautic.org/en/7.2/plugins/mailchimp.html#configure-the-plugin]
- Constant Contact: OAuth2 and the v2 API. Inferred bug: the address/custom-field split tests the value instead of the key. [code: plugins/MauticEmailMarketingBundle/Integration/ConstantContactIntegration.php:19-164 @7.x]
- iContact: `rest` auth with API version 2.2. Push creates the contact, then the subscription. [code: plugins/MauticEmailMarketingBundle/Integration/IcontactIntegration.php:19-219 @7.x]
- Status: no tests. Constant Contact v2 and iContact 2.2 are old APIs, and remote availability is unknown. [docs: https://docs.mautic.org/en/7.2/plugins/icontact.html]

## 12 Zapier
- Purpose: an info card only. It has `config.php` with an embedded zapier.com widget script, and no Integration class, routes, events or API endpoints. Zapier uses Mautic's REST API and webhooks. [code: plugins/MauticZapierBundle/Config/config.php:5-17 @7.x]
- Limitation: the info modal loads third-party JavaScript into the admin UI. [code: plugins/MauticZapierBundle/Config/config.php:14 @7.x]

## 13 Gmail and Outlook
- Purpose: store the shared `secret` used to verify tracking pixels from the Gmail extension / Outlook add-in. Tracking itself lives in EmailBundle at `/plugin/{integration}/tracking.gif`. [code: app/bundles/EmailBundle/Controller/PublicController.php:710-810 @7.x]
- Gmail uses IntegrationsBundle (`GmailKeysType` with a required `secret`). Outlook uses the legacy framework (auth `none`, key `secret`). [code: plugins/MauticGmailBundle/Form/Type/GmailKeysType.php:18-36 @7.x] [code: plugins/MauticOutlookBundle/Integration/OutlookIntegration.php:10-53 @7.x]
- Behaviour:
  - The signature is `crc32b(crypt(urlencode(d), '$1$'.secret))`, compared with `hash_equals`. [code: app/bundles/EmailBundle/Controller/PublicController.php:710-752 @7.x]
  - The payload needs `email`, `subject` and `body`. [code: app/bundles/EmailBundle/Controller/PublicController.php:764-801 @7.x]
  - Outlook's first request is not counted as an open. [code: app/bundles/EmailBundle/Controller/PublicController.php:764-801 @7.x]
- Limitation (inferred): `GmailIntegration` has no `getDecryptedApiKeys()`, which the tracking code calls, so Gmail tracking would fail with an undefined-method error. [code: app/bundles/EmailBundle/Controller/PublicController.php:741 @7.x] [code: app/bundles/IntegrationsBundle/Integration/BasicIntegration.php:10-40 @7.x]
- History: Gmail moved from `AbstractIntegration` to `BasicIntegration` in 7.2.0, which is when this limitation appeared. [PR #16847]

## 14 Other plugins (pointers)
- Amazon S3 (`plugins/MauticCloudStorageBundle`, feature `cloud_storage`) is covered by the assets skill. Tags UI (`plugins/MauticTagManagerBundle`) is covered by mautic-contacts. [code: plugins/MauticCloudStorageBundle/Integration/AmazonS3Integration.php @7.x] [code: plugins/MauticTagManagerBundle/Integration/TagManagerIntegration.php @7.x]
- History: S3 gained a custom endpoint in 5.0. Tag Manager moved to `BasicIntegration` in 7.2; its tag-screen history is in pr-history.md section 2.14. [PR #11693] [PR #16795]
- Social (Facebook, Twitter, Instagram, Foursquare), Focus and GrapesJS builder are separate plugins outside this skill. Twilio (SmsBundle) and OneSignal (NotificationBundle) are core legacy Integrations. [code: app/bundles/SmsBundle/Integration/TwilioIntegration.php @7.x] [code: app/bundles/NotificationBundle/Integration/OneSignalIntegration.php @7.x]
