# Integrations: pull-request history

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
   - [2.1 IntegrationsBundle framework and config](#21-integrationsbundle-framework-and-config)
   - [2.2 Sync engine](#22-sync-engine)
   - [2.3 Legacy PluginBundle framework (`AbstractIntegration`)](#23-legacy-pluginbundle-framework-abstractintegration)
   - [2.4 Legacy CRM base: field mapping, push to integration, fetchleads](#24-legacy-crm-base-field-mapping-push-to-integration-fetchleads)
   - [2.5 Salesforce](#25-salesforce)
   - [2.6 HubSpot](#26-hubspot)
   - [2.7 Zoho CRM](#27-zoho-crm)
   - [2.8 SugarCRM](#28-sugarcrm)
   - [2.9 Microsoft Dynamics, ConnectWise, vTiger](#29-microsoft-dynamics-connectwise-vtiger)
   - [2.10 Email marketing (Mailchimp, iContact, Constant Contact)](#210-email-marketing-mailchimp-icontact-constant-contact)
   - [2.11 Enrichment (Clearbit, FullContact)](#211-enrichment-clearbit-fullcontact)
   - [2.12 Gmail, Outlook, Zapier](#212-gmail-outlook-zapier)
   - [2.13 Amazon S3 (CloudStorage)](#213-amazon-s3-cloudstorage)
   - [2.14 Tag Manager plugin](#214-tag-manager-plugin)
   - [2.15 Packaging and the monorepo](#215-packaging-and-the-monorepo)
   - [2.16 Marketplace](#216-marketplace)
3. Removed plugins
4. Regression catalogue
5. Feature timeline
6. Removed, deprecated, replaced
7. Maintainer norms for this area
8. Open questions
9. Coverage

## 1. How to read this file
Source: merged pull requests on mautic/mautic, harvested 2026-10-15. Versions are inferred from the base branch and the
merge date, so `(v2.8)` means "first released in about 2.8". Current behaviour is in references/behaviour.md; this file
explains why and when it became so. Where a PR conflicts with behaviour.md, behaviour.md (code-verified) wins and the PR
is listed as historical or under section 8.

## 2. Decisions that shaped current behaviour

### 2.1 IntegrationsBundle framework and config
- The standalone `mautic-inc/plugin-integrations` repository was merged into core as `app/bundles/IntegrationsBundle`, with its git history, auth providers, config form and the sync engine (`mautic:integrations:sync`). [PR #8210] [PR #8223] (v3.0)
- Legacy and IntegrationsBundle integrations share the Plugins UI, events and helper through `UnifiedIntegrationInterface`. [PR #8433] (v3.0)
- An IntegrationsBundle plugin can be published with no auth config at all; this was needed for key-less plugins such as the GrapesJS builder. [PR #9050] (v3.1)
- Config form templates resolve for bundles whose name lacks the `Mautic` prefix. [PR #8564] (v3.0)
- Saving the config calls `isAuthorized()` only when the integration implements `ConfigFormAuthorizeButtonInterface`. [PR #9642] (v3.3)
- `INTEGRATION_CONFIG_BEFORE_SAVE` is dispatched after the form is handled, so listeners see the new values. It was accepted as a labelled BC break in the 4.0 beta because no known plugin used it. [PR #9886] (v4.0)
- Validation errors show when the integration is published or the Authorize button was clicked. A "required" asterisk alone validates nothing; the field needs a constraint. [PR #10539] (v4.4)
- `ConfigFormNotesInterface` lets an integration show notes on its config form. [PR #11451] (v5.0)
- IntegrationsBundle, PluginBundle and MarketplaceBundle templates are Twig since 5.0; plugins that override them must move to Twig. [PR #11862] [PR #11960] [PR #11560] (v5.0)
- The OAuth2 three-legged `HttpFactory` applies a `base_uri` from the credentials, so requests can use relative paths. [PR #12760] (v5.1)
- `INTEGRATION_CONFIG_ON_GENERATE_AUTH_URL` (`ConfigAuthUrlEvent`) lets a host rewrite the OAuth2 authorisation URL. [PR #13434] (v5.1)
- PR #13521 describes integration interface classes as autoconfigured with "the right integration tags". The 7.x code auto-tags only `mautic.integration`, `mautic.basic_integration`, `mautic.config_integration` and `mautic.builder_integration`, so the sync and auth tags are still manual (behaviour.md wins; see section 8). [PR #13521] (v5.1) [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:26-33 @7.x]
- A `PLUGIN_IS_PUBLISHED_STATE_CHANGING` listener can veto publishing, and changing credentials clears the stored access and refresh tokens. [PR #13696] (v7.0)
- IntegrationsBundle registers a test-only `TestPass` and a mock `Oauth2ThreeLegged` `HttpFactory`, so plugins can mock HTTP in functional tests. [PR #15084] (v7.0)
- Config tabs (Features, Auth, Sync) render the plugin's form type once instead of double-wrapping it. [PR #15957] (v7.2)
- Translation strings in IntegrationsBundle templates are passed through `purify` after `trans`, so HTML in translations renders safely. [PR #14270] (v5.2)
- The field-mapping Twig template must not use hyphenated variable names; one crashed the settings modal of every plugin with field mapping. [PR #14361] (v5.2.1)
- 46 IntegrationsBundle services moved to autowired `Config/services.php`; plugins should reference services by FQCN. [PR #16781] (v7.2)
- IntegrationsBundle DAOs and DTOs with no children are `final` in 7.2 (for example `ObjectMappingDAO`, `FieldMappingDAO`, `ObjectChangeDAO`, `NotificationDAO`, `OrderResultsDAO`). Plugins must compose, not extend. [PR #16888] (v7.2)
- Re-thrown exceptions in MarketplaceBundle and in the sync `ObjectChangeGenerator` chain the original exception. [PR #16488] (v7.2)

### 2.2 Sync engine
- Field-change lookup is scoped to the exact Mautic object being synced. A wrong comparison had matched objects with greater ids and could overwrite one Contact with another's data. [PR #8590] (v3.0)
- Deleting a Contact or Company removes its `sync_object_field_change_report` and `sync_object_mapping` rows. [PR #8598] [PR #8738] (v3.0) [PR #11623] (v5.0)
- Deleting an anonymous Contact runs no delete on the sync tables, because anonymous Contacts never reach them. This removed lock-wait timeouts. [PR #11262] (v4.4)
- A primary-company change is recorded as a field change, so the new company relation is pushed. [PR #8644] (v3.0)
- A full-object report marks every mapped field as changed, not only required ones. Before, form "push to integration" created remote records without first name. [PR #9063] (v3.3)
- Required Mautic fields are cached for one sync run instead of being queried per object. [PR #9313] (v3.2)
- `--option="key:value"` (repeatable) passes custom values to the integration through `OrderDAO::getOptions()`. [PR #9796] (v4.0)
- Select and multiselect values carry their real type in `NormalizedValueDAO`. [PR #9919] (v4.0)
- `sync_object_field_change_report.column_value` is LONGTEXT, so long values are not truncated. [PR #10778] (v4.1)
- Only the object flagged "retry later" is retried; the rest of the batch is not. [PR #11252] (v4.4)
- `--disable-activity-push` switches off activity push for integrations that support it. [PR #11255] (v5.0)
- Pulled values are validated against Mautic field type and length; invalid fields are skipped and the user is notified, instead of the sync crashing. Batch-completed events fire in both directions. [PR #11303] (v5.0)
- `INTEGRATION_BEFORE_CONTACT_FIELD_CHANGES` and `INTEGRATION_BEFORE_COMPANY_FIELD_CHANGES` let an integration filter which changes are recorded. [PR #10512] (v5.0)
- Contact changes made by the sync carry a manipulator, so the timeline and plugins can tell integration changes from campaign changes. [PR #11669] [PR #11686] (v5.0)
- The sync detaches specific entities instead of calling `EntityManager::clear()`. [PR #12341] (v5.0)
- A field mapped one-way "to integration" is never cleared or overwritten in Mautic by a pull, and one-way fields are not added to the opposite direction's required list. Rejected: per-integration filtering; maintainers preferred a global rule. [PR #11251] (v5.1)
- `mautic:integrations:cleanup`, meant to run daily, deletes change rows whose object no longer exists. [PR #13340] (v5.1)
- Sync changes are attributed to the integration in the audit log, not to "System". [PR #13426] (v5.1)
- OAuth2 integrations can set a default token expiry, so tokens refresh on 401 instead of on every run; Salesforce login limits were being exhausted. [PR #13429] (v5.1)
- Integration objects in one batch that resolve to the same unique-identifier values reuse one Contact or Company. [PR #13435] (v5.1)
- `--mautic-object-id=contact:N` syncs only those objects; other object types are not pushed. [PR #13454] (v5.1)
- An empty value for a required Mautic field no longer aborts the sync: a new object is skipped, an existing object keeps its old value for that field, and the user is notified. Before, every rerun failed the same way. Rejected: an `OrderDAOFactory` from the Acquia fork. [PR #14666] (v6.0)
- Engine pull-then-push order, the change report and SyncJudge are unchanged by any PR in the inputs; see behaviour.md sections E and F. [PR #8210]

### 2.3 Legacy PluginBundle framework (`AbstractIntegration`)
- Addons were renamed Plugins, every plugin bundle is always enabled, and an integration is switched on by publishing it. [PR #740] (v1.2)
- Required keys are validated, and a password key is required only when nothing is stored yet. [PR #1230] (v1.2.3) Keys are required only when the integration is published. [PR #2035] (v2.1)
- Saving an integration's config dispatches a PluginBundle event. [PR #2035] (v2.1)
- The authorisation popup stays open and shows the integration's error on failure; it closes only on success. [PR #3784] (v2.8)
- API errors (`ApiErrorException`) create a user notification, linked to the Contact when there is one. Code exceptions are only logged. [PR #3984] (v2.8.1)
- Values pushed to an integration are HTML-entity-decoded and tag-stripped first. [PR #3996] (v2.8.1)
- `curl_options` are merged with `+`, which keeps the `CURLOPT_*` keys. [PR #5022] (v2.12.1)
- Integrations became DI services through `IntegrationPass` [PR #4063] (v2.8.2), then constructor-injected in 3.0, where `IntegrationPass` was removed. [PR #8128] (v3.0)
- `requires_authorization` controls only the "Authorize App" button; key fields show whenever `getRequiredKeyFields()` is non-empty. Originally [PR #8610] (v3.0) hid keys; changed by [PR #8799] (v3.0).
- `makeRequest()` sends array parameters as Guzzle `form_params`. It was ruled a bug fix, not a BC break, because Guzzle had deprecated array `body`. [PR #10301] (v4.0) JSON-encoded parameters (`encode_parameters => json`) are sent as the body. [PR #10674] (v4.1.2)
- `decryptApiKeys()` skips keys that decrypt to empty instead of dropping every key. A "No" answer had wiped all credentials. [PR #10574] (v4.2)
- `AbstractIntegration` was deprecated in 4.3 "to be removed in Mautic 6.0". It is still in 7.x, and every bundled CRM extends it. [PR #11050] (v4.3) [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:54 @7.x]
- JSON responses have control characters stripped before decoding. [PR #11343] (v5.0)
- Logged Authorization headers are replaced by the literal `[REDACTED]`. Rejected: hashing, because a hash does not show that the value was changed. [PR #14277] (v5.2.1)
- Saving a Contact does not touch `integration_entity` when no lead-sync plugin is enabled. [PR #13086] (v5.1)
- CRM errors from `AbstractIntegration` go to `monolog.logger.mautic`. [PR #9821] (v4.0) Plugin services use the same channel. [PR #13951] (v5.2)
- The legacy field-mapping AJAX reads `integration`, `page` and `settings` from POST with GET fallback, so mapping pages 2+ work and save. [PR #16202] (v7.2) Earlier pagination fixes: [PR #8980] (v3.0.2), [PR #11753] [PR #11761] (v4.4.5, v5.0), [PR #15056] (v7.0).
- The config modal shows the plugin version as a badge. [PR #15789] (v7.1)

### 2.4 Legacy CRM base: field mapping, push to integration, fetchleads
- Each mapped field has one direction (`update_mautic`). Direction applies only on update; on create all mapped fields are used. Reviewers asked for "both directions"; the PR kept one direction per field. [PR #3508] (v2.7) [PR #4247] (v2.9)
- Mapping lists show only mapped fields, paginated by AJAX, because Salesforce field lists made the modal huge. [PR #3508] [PR #3674] (v2.8)
- Pseudo fields: "Contact timeline link" [PR #3774] (v2.8), "Do not contact (email)" as 1 = contactable, 0 = not, with no reason [PR #4459] (v2.10), and "Mautic contact ID" [PR #5655] (v2.14.1).
- Pseudo fields have locked direction arrows and always push Mautic → integration. [PR #4896] [PR #4919] (v2.10.1) The Mautic contact ID must never be overwritten from the integration. [PR #5655]
- An integration can force a fixed direction for one field; Salesforce `CreatedDate` is pull-only. [PR #7404] (v2.15.3)
- "Update blank values" (`updateBlanks`) fills a blank field from the other side regardless of direction. It applies to Salesforce, SugarCRM, Zoho, ConnectWise and Dynamics, and it is still read in 7.x. [PR #4445] (v2.10) [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:407,552-553 @7.x]
- `updateBlanks` shows only in the plugin config, not in the campaign action. [PR #5138] (v2.11)
- Placeholder values written to satisfy CRM-required fields (company "Unknown") are never synced back. [PR #4718] (v2.10)
- "Push contact to integration" behaves the same as a form action, campaign action and point trigger (shared `PushToIntegrationTrait`). [PR #1950] (v2.0) [PR #4433] (v2.9.1) The trait gets `integrationHelper` injected. [PR #13470] (v5.0.4)
- Push config carries the campaign `Event` [PR #6638] (v2.14.2) and the triggering `LeadEventLog`. [PR #7131] (v2.15.1)
- `mautic:integration:fetchleads` (alias `synccontacts`) is the single CLI entry: pull, then push, with `-i`, `-d`/`-t`, `--time-interval` and `--fetch-all`. [PR #1825] [PR #1908] [PR #1955] (v2.0–2.1) [PR #4247] (v2.9)
- fetchleads checks that `pushLeads()` exists before calling it. [PR #4880] (v2.10.1) It prints clear errors and lists usable integrations. [PR #5336] (v2.12.1) It pushes companies only when `push_companies` is a supported feature. [PR #10497] (v4.0.2)
- All pending records sync in one run, not 25. [PR #4024] (v2.8.1)
- Contacts created by a pull get a `last_sync_date`, so they are not pushed straight back. [PR #4490] (v2.9.1)
- Companies created from a CRM get every mapped company field. [PR #5842] (v2.13) CRM date strings are converted to SQL format. [PR #6483] (v2.14.2) [PR #7042] (v2.15.1)
- An empty or false value from the CRM updates the Mautic field instead of being skipped. [PR #7753] (v3.3.3)
- Fetched text longer than 255 characters for a Mautic text field is truncated. [PR #5197] (v2.12)
- Missing unique identifiers or "Priority Fields For Mautic" log `getMauticLead: No unique identifiers` / `No fields to update in Mautic` at debug level. [PR #12619] (v5.0) [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:372,400 @7.x]
- `mautic:integration:pushleadactivity` (alias `pushactivity`) pushes timeline activity for synced Contacts. [PR #1955] (v2.1) Its message is integration-neutral. [PR #4440] (v2.9.1)
- `getLeadData()` must detach every loaded entity except `Integration` and `Plugin` after each timeline page. In 5.0 the `EntityManager::clear()` replacement [PR #12361] (v5.0) inverted the check, so only those two were detached and the command reported success while pushing nothing. Fixed by [PR #17815] (v7.2.2). The 7.x snapshot still has the inverted check, so it affects the 7.x snapshot and 7.2.1 (and every release since 5.0.0); fixed in 7.2.2. [code: plugins/MauticCrmBundle/Integration/CrmAbstractIntegration.php:245-254 @7.x]
- `pushLeadActivity()` only logs exceptions, so a successful exit of `pushleadactivity` does not prove anything was pushed; check the logs. [PR #17815] (v7.2.2)
- The contact page has an "Integrations" tab listing `integration_entity` links [PR #4426] (v2.10), which can link to the remote record [PR #9096] (v3.2). The object-mapping block came back in 5.0 RC2. [PR #12924] (v5.0)
- Segment filter "Integration Campaigns" builds a segment from CRM campaign members (Salesforce campaigns, ConnectWise groups). An `integration_entity` composite index was a merge condition, because without it one rebuild took about 20 minutes. [PR #3733] (v2.8) [PR #5037] (v2.11)

### 2.5 Salesforce
- Pull objects (Lead, Contact, Account) are chosen in Feature settings; both Lead and Contact pull into Mautic Contacts. [PR #1955] (v2.1) A "Sandbox" setting targets the SF sandbox. [PR #1978] (v2.1)
- Records with no value in the unique identifier (email) are not imported. [PR #2929] (v2.3)
- Formula fields are pull-only. [PR #2930] (v2.3) The SF `Id` is excluded from push query fields. [PR #5607] (v2.12.2)
- "Update Contact Owner" sets the owner to the Mautic user with the same email as the SF owner. [PR #2945] (v2.3)
- SF metadata is cached in the DB cache table. [PR #2954] (v2.6)
- Push avoids duplicates: it uses the `integration_entity` id, else searches Leads (including converted) and Contacts by email and updates every match, and creates a Lead only when nothing matches. [PR #3373] (v2.6) [PR #3392] (v2.7) An SF Contact takes priority over a Lead. [PR #3800] (v2.8)
- Email is a required mapping. [PR #3991] (v2.8.1) [PR #4481] (v2.9.1)
- Assignment rules fire only when a Lead is created (`Sforce-Auto-Assign: FALSE` on update and composite PATCH). [PR #3978] (v2.8.1) [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:1819 @7.x]
- An empty Mautic company never overwrites SF with "Unknown"; the SF value is written back to Mautic. [PR #3925] (v2.8.1)
- SOQL values are escaped: apostrophes in emails [PR #4041] (v2.8.1), backslashes [PR #5835] (v2.13), and HTML entities decoded before quotes are escaped [PR #10535] (v4.0.2).
- Campaign push adds or updates the SF campaign member, re-creates deleted members, and adds every SF person sharing the email. [PR #3753] (v2.8) [PR #4555] (v2.9.2) It still adds the member when no field needed updating. [PR #4437] (v2.9.1) [PR #6293] (v2.14)
- Activity push uses composite requests with per-record results. [PR #4664] (v2.10) Any timeline event type can be chosen, with the old three types as BC default. [PR #4935] (v2.11) Activity names are truncated to 80 characters. [PR #8989] (v3.0.2)
- Contact `AccountId` can link a Contact to a Mautic Company. [PR #4720] (v2.11) [PR #5168] (v2.11) `IsDeleted` can be mapped to a boolean. [PR #4737] (v2.11) Companies push to Accounts only when push is enabled. [PR #4871] (v2.11) [PR #5840] (v2.13)
- Locked records are retried with back-off, and campaign-member segment sync is incremental. [PR #5518] (v2.12.2) A failed run does not cache a new "last synced" date. [PR #7514] (v4.0.2)
- Pulls follow `nextRecordsUrl` and filter on `SystemModStamp`. [PR #5841] (v2.13)
- A State that SF does not support for the Country is dropped from the push. [PR #6823] (v2.15)
- A form-triggered push sends the just-submitted values. [PR #6824] (v2.15)
- Booleans sync true → false [PR #7643] (v2.15.3) and keep their type on push [PR #9618] (v3.3.3). Multiselect fields sync both ways. [PR #8402] (v3.0.1)
- TLS 1.2 is forced. [PR #7814] (v2.16)
- `INVALID_SESSION_ID` in the response `message` triggers a token refresh. [PR #10993] (v4.3)
- A mapped SF field deleted in SF is dropped from the mapping with a notification, and the sync continues. [PR #13406] (v5.2)
- The "Integration Campaign Members" select lists campaigns by name. [PR #12058] (v4.4.10) [PR #12141] (v5.0) [PR #14712] (v5.2.4) Segment rebuild no longer crashes on a null entity at the end of a batch. [PR #15948] (v7.0.2)
- DNC, current behaviour: DNC flows Mautic → SF unless "Use latest updated Do Not Contact record" (`updateDncByDate`) is on. Originally forced Mautic → SF [PR #4919] (v2.10.1); optional latest-wins added by [PR #4920] (v2.12); boolean value pushed [PR #5365] (v2.12). [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:2547-2549 @7.x]
- DNC with `updateDncByDate` on: a newly pulled SF record with `HasOptedOutOfEmail` gets DNC MANUAL "Set by Salesforce" [PR #13411] (v5.1); SF opt-out history is replayed oldest first, so a box ticked then unticked ends with no DNC [PR #13444] (v5.1); a later Mautic audit-log change wins over older SF history [PR #4920]; DNC is added with the current-status check [PR #9956] (v4.0.2). [code: plugins/MauticCrmBundle/Integration/SalesforceIntegration.php:457-467,2566-2627 @7.x]
- A Contact deleted in Mautic is not re-created by a later fetch after the SF record is edited and deleted. [PR #13411] (v5.1)

### 2.6 HubSpot
- HubSpot was added as a push via createOrUpdate by email. [PR #1074] (v1.2.3) Pull and a webhook followed, with API-key auth and an auto-created `mautic_timeline` property. [PR #3026] (v2.4)
- Field direction is honoured, and contacts and companies are fetched with relations. [PR #4184] (v2.9)
- Multiselects sync both ways. [PR #7887] (v2.16) Read-only HubSpot properties are pull-only, because HubSpot rejects the whole push with READ_ONLY_VALUE. [PR #8785] (v3.1.1)
- A 401 shows an error in the config modal. [PR #11416] (v4.4.4)
- Auth moved from the sunset `hapikey` to a Private App access token. [PR #11470] (v4.4.5) [PR #11857] (v5.0) Token fields became editable and savable. [PR #11775] (v4.4.6)
- What 7.x does: with `accessKey` stored, `getAuthenticationType()` returns `oauth2` and the token is sent as a bearer; otherwise requests still append `?hapikey=<key>`, which HubSpot no longer accepts. [code: plugins/MauticCrmBundle/Integration/HubspotIntegration.php:79-97 @7.x] [code: plugins/MauticCrmBundle/Api/HubspotApi.php:18-24 @7.x]
- fetchleads syncs only Contacts modified inside the time window; a small count is expected, not a bug. [PR #11470]
- PHP 8 `implode` argument order fixed. [PR #14571] (v6.0)

### 2.7 Zoho CRM
- Bi-directional Leads, Contacts and Accounts through `fetchleads -i Zoho`, with a data-centre selector. [PR #4068] (v2.9)
- Non-Latin field labels are transliterated so keys are not empty. [PR #2333] (v2.1.1)
- Each pushed record is built independently; a blank never inherits the previous record's value. [PR #5153] (v2.11)
- A single push respects field priority for create, link and update. [PR #6427] (v2.14.2) Updates to tracked Contacts are applied on sync. [PR #6908] (v2.15)
- Zoho moved to REST API v2 with OAuth client id and secret; installs had to re-authorise. [PR #8272] (v2.16)

### 2.8 SugarCRM
- Sugar 6 CE and 7 are supported, with full two-way sync; SuiteCRM is not officially supported. [PR #4247] (v2.9) [PR #4445]
- Sugar 7 re-authenticates on every call. [PR #869] (v1.2.1) The `/filter` endpoint uses GET. [PR #10667] (v4.2)
- Owner is pushed from forms, campaigns and point triggers, matched by user email, and sent empty if no Sugar user matches. [PR #5303] (v2.12.2) Owner changes in Sugar update Mautic on pull. [PR #7898] (v2.16.1)
- Multiselect values convert between `a|b` and `^a^,^b^`. [PR #5616] (v2.13)
- "Update emails Do not contact info" maps `email_opt_out` to unsubscribed/manual and `invalid_email` to bounced. [PR #5896] (v2.14.1)
- Priority is applied per object [PR #6185] (v2.14.1), in bulk push [PR #7377] (v2.15.2) and in the form push [PR #7555] (v2.15.3).
- Email matching is case-insensitive. [PR #7401] (v2.15.2)

### 2.9 Microsoft Dynamics, ConnectWise, vTiger
- Dynamics lives in `MauticCrmBundle` because maintainers keep all core CRMs together. [PR #4212] (v2.9) It requests the plural `Contacts` object. [PR #13208] (v5.0.4)
- ConnectWise: pull via fetchleads, push via campaign action [PR #4214] (v2.9); optional activity creation [PR #4955] [PR #5142] (v2.11); GET calls page to the last page [PR #5427] (v2.12.1); Client ID replaces the appcookie credential [PR #13408] (v5.1).
- vTiger: company mapping [PR #4122] (v2.9), no auth loop [PR #4875] (v2.10.1), field loading without settings [PR #5545] (v2.13).

### 2.10 Email marketing (Mailchimp, iContact, Constant Contact)
- Mailchimp uses an API key by default; OAuth stays only for existing configs. [PR #1184] (v1.2.3) [PR #1351] (v1.2.4)
- Push-to-integration works again and Mailchimp uses API 3.0. [PR #4219] (v2.9) Double opt-in requests the confirmation email. [PR #4934] (v2.11)
- Field mappings survive a list change in the campaign action. [PR #4455] (v2.9.1)
- iContact auth failures show an error. [PR #1218] (v1.2.3)

### 2.11 Enrichment (Clearbit, FullContact)
- Contacts and Companies are enriched on demand; results arrive by a public callback URL sent with each request. [PR #2933] [PR #2934] (v2.3) Clearbit lookups are cached. [PR #3011] (v2.3) FullContact callbacks apply data. [PR #3851] (v2.8.1)
- Clearbit moved from `AbstractIntegration` to `BasicIntegration` with `ConfigSupport` in 7.2. [PR #16586] (v7.2)
- Plugin controllers must keep `autowire()` signatures compatible with `FormController`. [PR #16596] (v7.2)
- Clearbit is removed in 8.x only, because HubSpot shut the service down. It is still in 7.x. [PR #17785] (8.x)

### 2.12 Gmail, Outlook, Zapier
- Outlook and Gmail tracking use a signed tracking GIF verified with a shared secret; the public endpoint must be sanitised because it writes into the timeline. [PR #2175] [PR #2604] (v2.2)
- Tracked emails create email Stat rows and "email read" timeline events. [PR #4022] (v2.8.1) The Outlook config shows the site URL. [PR #4004] (v2.8.1)
- Gmail moved from `AbstractIntegration` to `BasicIntegration` with `GmailKeysType` in 7.2.0. [PR #16847] (v7.2) This is the change behind the `getDecryptedApiKeys()` pitfall in SKILL.md: 7.1.3 still extends `AbstractIntegration`. [code: plugins/MauticGmailBundle/Integration/GmailIntegration.php:10 @7.x]
- Zapier is info-only, and plugin descriptions split on `\n---\n` into a secondary description. [PR #5794] (v2.13)

### 2.13 Amazon S3 (CloudStorage)
- S3 got a configurable region [PR #6945] (v2.15) and an optional endpoint for S3-compatible providers [PR #11693] (v5.0).
- Missing credentials show a user-facing error when browsing remote assets. [PR #14865] (v7.0)
- Rackspace and OpenStack were removed (section 3). [PR #8310] (v3.0)

### 2.14 Tag Manager plugin
Tag behaviour for Contacts (tagging, segment filters, the API) lives in mautic-contacts. These PRs change the Tag
Manager plugin's own screens.
- The plugin adds a Tags menu with CRUD and a contact count per tag. [PR #9364] (v4.0) "View contacts" quotes the tag name, so tags with spaces work. [PR #10252] (v4.0)
- Tags have an optional description; the name is set at creation and cannot be renamed. Rejected: a separate "summary" field. [PR #10799] (v4.2)
- Tags have no Clone action, and saving shows the standard update flash. [PR #10984] (v4.2.1) An empty name is rejected. [PR #11120] (v4.3)
- Contact-list batch actions add and remove tags. [PR #13711] (v5.1)
- The tag page lists "Tag usages" in segments, campaigns, forms, point triggers and reports. [PR #13917] (v5.2) It tolerates non-array report filter values. [PR #15134] (v6.0.3)
- The list renders a `customContent` hook. [PR #15540] (v7.0)
- Tag merge moves Contacts to the primary tag, deletes the secondary tag, rewrites references and dispatches `TAG_PRE_MERGE`/`TAG_POST_MERGE`. [PR #15331] (v7.2)
- Search matches name or description in the UI and in `GET /api/tags?search=`. [PR #16003] (v7.2)
- A tag in use can be deleted; its `lead_tags_xref` rows are removed first and the Contacts are kept. [PR #16132] (v7.2)
- Tag Manager moved to `BasicIntegration`. [PR #16795] (v7.2)
- Creating a duplicate tag name saves nothing and links to the existing tag; renaming to an existing name is refused. [PR #17341] (unreleased 7.x, 7.3.0-rc)

### 2.15 Packaging and the monorepo
- Bundled plugins live in mautic/mautic; per-plugin repos are read-only mirrors. [PR #9925] (v4.0) Mirrors close PRs automatically. [PR #11154] (v4.3)
- Each plugin has a `composer.json`, and the root uses `replace` with `self.version`, so plugins version in lockstep with core. [PR #9920] (v4.0)
- On 5.x each plugin requires `mautic/core-lib` of the same major. [PR #11593] (v5.0)
- Plugin migrations load from the plugin's own directory [PR #8688] (v3.0), a plugin that newly declares a version runs its update [PR #13423] (v5.1), and `mautic:plugins:reload` runs DDL outside a transaction [PR #13249] (v5.1).
- The IntegrationsBundle migration engine skips the commit when DDL already committed. [PR #14440] (v5.2.2)
- `MauticFactory::getDatabase()` is removed; install and update classes receive the connection by DI. [PR #14418] (v6.0) Plugins without an `Entity` directory update correctly. [PR #15951] (v7.0.2)

### 2.16 Marketplace
- MarketplaceBundle is a core bundle, read-only at first, listing allowlisted packages, with view/create permissions and a config switch. [PR #9650] (v4.0)
- Install and remove run Composer in-process, from the UI or `mautic:marketplace:install|remove`, and only for allowlisted packages. Rejected: shipping `composer.phar`, because a second PHP process may be the wrong PHP. [PR #10518] (v4.2)
- Install and remove sit behind `composer_updates` (default false); when true, the old self-updater is disabled. [PR #10518] (v4.2)
- The latest stable version is shown, with display names, docs/issue links and a cache-clear button for the one-hour cache. [PR #11197] (v4.4)
- Detail pages show the CLI install command, and a failed UI install returns a JSON error. [PR #12529] (v5.0)
- Pager and cache-clear fixes [PR #12728] [PR #12729] (v5.0), marketer-friendly copy [PR #13326] [PR #13329] [PR #13375] [PR #13377] (v5.1), and `|purify` for HTML descriptions [PR #12528] (v5.0).
- A name-derived, theme-aware header colour [PR #14199] (v6.0) and a working check-all box [PR #14413] (v5.2.2).
- The registry moved from Packagist to `marketplace.mautic.org` outside the inputs; log messages still say "Packagist". [PR #9650] [code: app/bundles/MarketplaceBundle/Service/Config.php:32-38 @7.x]

## 3. Removed plugins
| Plugin | Added | Deprecated | Removed | In 7.x `plugins/`? | Replacement |
|---|---|---|---|---|---|
| Pipedrive (in MauticCrmBundle) | [PR #4163] (v2.9) | [PR #12364] (v4.4.9) | [PR #12081] (v5.0) | No; only `Assets/img/pipedrive.png` remains [code: plugins/MauticCrmBundle/Assets/img/pipedrive.png @7.x] | Standalone Pipedrive plugin |
| Citrix / GoTo (MauticCitrixBundle) | [PR #2850] (v2.3) | [PR #12367] (v4.4.9) | [PR #12333] (v5.0) | No; present at tag 4.4.13, absent at 5.0.0 | Leuchtfeuer GoTo plugin |
| Rackspace, OpenStack (MauticCloudStorageBundle) | before the inputs | none | [PR #8310] (v3.0) | No; only `AmazonS3Integration` and `CloudStorageIntegration` remain [code: plugins/MauticCloudStorageBundle/Integration/AmazonS3Integration.php @7.x] | Amazon S3 |
| Clearbit (MauticClearbitBundle) | [PR #2934] (v2.3) | none | [PR #17785] (8.x only) | Yes, still shipped in 7.x [code: plugins/MauticClearbitBundle/Integration/ClearbitIntegration.php:10 @7.x] | None (service shut down) |
| Froala editor (core, not a plugin) | before the inputs | none | styles [PR #14271], Gated Video [PR #14284] (v6.0) | No Froala code in `app/bundles` from 6.0.0; one commented-out call remains [code: plugins/GrapesJsBuilderBundle/Assets/library/js/preset-mautic/dynamicContent/dynamicContent.service.js:182 @7.x] | GrapesJS builder |

- Pipedrive was removed because API deprecations had already broken it and community policy keeps third-party integrations out of core. Its migrations drop its data, including `integration_entity` records (scope unclear, see section 8). [PR #12081] (v5.0)
- In 4.4.9 Pipedrive and Citrix show deprecation notices in the config form, the notification centre (added by migration only when enabled), CLI `[WARNING]` lines and `@deprecated`. Rejected: a new dismissible dashboard banner. [PR #12364] [PR #12367] (v4.4.9)
- Citrix was a "maintenance nightmare" nobody could test without paid accounts; core Citrix hooks went with it, so the old bundle cannot be dropped back in. [PR #12333] (v5.0)
- Rackspace/OpenStack were removed because the library had been unmaintained for three years, with no test instances and no known users. [PR #8310] (v3.0)

## 4. Regression catalogue
Rows describe contracts still true in 7.x. Seeds for tests.

| Area | Symptom | Expected behaviour | PR | Version |
|---|---|---|---|---|
| Framework | Enabling a key-less IntegrationsBundle plugin: "Undefined index apiKeys" | Publishes without auth config | [PR #9050] | 3.1 |
| Framework | `isAuthorized()` undefined on config save | Called only with `ConfigFormAuthorizeButtonInterface` | [PR #9642] | 3.3 |
| Framework | BEFORE_SAVE listeners saw old values | Event fires after the form is handled | [PR #9886] | 4.0 |
| Framework | Validation ignored for unauthorised integrations | Errors shown when published or Authorize clicked | [PR #10539] | 4.4 |
| Framework | Mapping modal crashed: Twig "filter" on FormView | Template renders | [PR #14361] | 5.2.1 |
| Framework | Config tabs double-wrapped | Single wrap | [PR #15957] | 7.2 |
| Framework | Filtered mapping save reset all mappings | Hidden mappings kept | [PR #8596] | 3.0 |
| Sync | One Contact overwritten with another's data | Change lookup scoped to the exact object | [PR #8590] | 3.0 |
| Sync | Sync tables not cleaned on delete | Change and mapping rows deleted | [PR #8598] [PR #8738] [PR #11623] | 3.0 / 5.0 |
| Sync | Lock-wait timeouts deleting anonymous Contacts | No sync-table delete for anonymous Contacts | [PR #11262] | 4.4 |
| Sync | Company change not synced | Change recorded as `company` | [PR #8644] | 3.0 |
| Sync | Form push lost first name | All mapped fields reported as changed | [PR #9063] | 3.3 |
| Sync | "new entity found through Company#owner" | Company owner syncs across a batch | [PR #9328] | 4.0.2 |
| Sync | Select/multiselect normalised as string | Typed values | [PR #9919] | 4.0.2 |
| Sync | "Data too long for column_value" | LONGTEXT | [PR #10778] | 4.1.2 |
| Sync | Whole batch retried for one retry flag | Only that object retried | [PR #11252] | 4.4 |
| Sync | Sync crashed on wrong type/length | Field skipped, user notified | [PR #11303] | 5.0 |
| Sync | One-way "to integration" field cleared by pull | Untouched | [PR #11251] | 5.1 |
| Sync | Orphan change rows broke sync | `mautic:integrations:cleanup` removes them | [PR #13340] | 5.1 |
| Sync | Changes attributed to "System" | Attributed to the integration | [PR #13426] | 5.1 |
| Sync | OAuth2 token refreshed every run | Default expiry; refresh on 401 | [PR #13429] | 5.1 |
| Sync | Same person twice in a batch → duplicates | One Contact reused | [PR #13435] | 5.1 |
| Sync | `--mautic-object-id=contact:N` also pushed companies | Only named objects | [PR #13454] | 5.1 |
| Sync | "Required field can't be empty" blocked sync forever | New object skipped, existing keeps value, user notified | [PR #14666] | 6.0 |
| Legacy | Auth popup closed and hid the error | Stays open on error | [PR #3784] | 2.8 |
| Legacy | `&#39;` sent literally | Decoded and tag-stripped | [PR #3996] | 2.8.1 |
| Legacy | Only 25 records per run | All pending records | [PR #4024] | 2.8.1 |
| Legacy | Pulled Contacts pushed straight back | `last_sync_date` set on create | [PR #4490] | 2.9.1 |
| Legacy | Fatal `pushLeads` undefined | Method-exists check | [PR #4880] | 2.10.1 |
| Legacy | Timeline link / DNC pseudo fields not pushed | Always pushed to the integration | [PR #4919] | 2.10.1 |
| Legacy | "Unknown" placeholder written back to Mautic | Not synced back | [PR #4718] | 2.10 |
| Legacy | `curl_options` re-indexed | Keys preserved | [PR #5022] | 2.12.1 |
| Legacy | Key fields hidden for HubSpot/OneSignal/Twilio | Shown when required keys exist | [PR #8799] | 3.0 |
| Legacy | Guzzle "body as array" error | `form_params` | [PR #10301] | 4.0 |
| Legacy | Yes/No "No" wiped all keys | Only empty keys skipped | [PR #10574] | 4.2 |
| Legacy | Unchecked CRM checkbox did not clear Mautic field | Empty/false written | [PR #7753] | 3.3.3 |
| Legacy | Company date strings rejected by MySQL | Converted to SQL format | [PR #6483] [PR #7042] | 2.14.2 / 2.15.1 |
| Legacy | Tokens written to logs | `[REDACTED]` | [PR #14277] | 5.2.1 |
| Legacy | Mapping pages 2+ unreachable | POST page/settings honoured; later-page mappings saved | [PR #16202] | 7.2 |
| Legacy | `pushleadactivity` "succeeded", pushed nothing, "EntityManager is closed" | Only non-Integration/Plugin entities detached | [PR #17815] | 7.2.2 |
| Legacy | "No active transaction" on plugin reload or migration | DDL outside transaction; no commit after DDL | [PR #13249] [PR #14440] | 5.1 / 5.2.2 |
| Salesforce | Duplicate SF records on push | Lookup by id, then email; create Lead only if no match | [PR #3373] [PR #3392] | 2.6 / 2.7 |
| Salesforce | Assignment rules re-fired on update | Only on create | [PR #3978] | 2.8.1 |
| Salesforce | Empty Mautic company → "Unknown" in SF | SF value kept and pulled | [PR #3925] | 2.8.1 |
| Salesforce | Apostrophe/backslash/`&#39;` broke SOQL | Escaped after decoding | [PR #4041] [PR #5835] [PR #10535] | 2.8.1–4.0.2 |
| Salesforce | One record error failed the activity batch | Composite per-record results | [PR #4664] | 2.10 |
| Salesforce | DNC entity pushed (circular export) | Boolean DNC pushed | [PR #5365] | 2.12 |
| Salesforce | >2,000 records looped forever | Follows `nextRecordsUrl` | [PR #5841] | 2.13 |
| Salesforce | Campaign member skipped when person unchanged | Member still added | [PR #6293] | 2.14 |
| Salesforce | Contact rejected for unsupported State | State dropped | [PR #6823] | 2.15 |
| Salesforce | Form push sent previous values | Submitted values sent | [PR #6824] | 2.15 |
| Salesforce | Boolean stuck on true; boolean sent as string | true → false syncs; type kept | [PR #7643] [PR #9618] | 2.15.3 / 3.3.3 |
| Salesforce | Activity name >80 chars rejected | Truncated to 80 | [PR #8989] | 3.0.2 |
| Salesforce | Tokens never refreshed | `INVALID_SESSION_ID` in `message` refreshes | [PR #10993] | 4.3 |
| Salesforce | New opted-out SF record arrived without DNC | DNC set (with `updateDncByDate`) | [PR #13411] | 5.1 |
| Salesforce | Opt-out ticked then unticked → DNC | Current state only; no DNC | [PR #13444] | 5.1 |
| Salesforce | Deleted SF field → "No such column" | Mapping dropped, notification, sync continues | [PR #13406] | 5.2 |
| Salesforce | CampaignMember rebuild: detach(NULL) | All gathered entities detached | [PR #15948] | 7.0.2 |
| HubSpot | Push rejected for read-only properties | Read-only properties pull-only | [PR #8785] | 3.1.1 |
| HubSpot | 401 left the modal spinning | Error shown | [PR #11416] | 4.4.4 |
| HubSpot | Cannot connect after API-key sunset; form 500 | Private App token; editable fields | [PR #11470] [PR #11775] [PR #11857] | 4.4.5–5.0 |
| Zoho | Blank inherited previous record's value | Records built independently | [PR #5153] | 2.11 |
| Zoho | Single push ignored priority | Priority respected | [PR #6427] | 2.14.2 |
| SugarCRM | Mixed-case email marked `lead-deleted` | Case-insensitive match | [PR #7401] | 2.15.2 |
| SugarCRM | Form push ignored priority | Only Mautic-priority fields pushed | [PR #7555] | 2.15.3 |
| Dynamics | No fields, no Contacts | Plural `Contacts` object | [PR #13208] | 5.0.4 |
| ConnectWise | Only 25 records synced | Pages to the last page | [PR #5427] | 2.12.1 |
| S3 | PHP error browsing without credentials | User-facing error | [PR #14865] | 7.0 |
| Tag Manager | Tag with spaces showed no Contacts | Quoted filter | [PR #10252] | 4.0 |
| Tag Manager | Tag in use could not be deleted | xref rows removed, Contacts kept | [PR #16132] | 7.2 |
| Tag Manager | Duplicate name "updated" a null-id tag | Nothing saved; link to existing tag | [PR #17341] | unreleased 7.x |
| Marketplace | UI install failure returned nothing | JSON error | [PR #12529] | 5.0 |
| Marketplace | Check-all selected nothing | All visible rows selected | [PR #14413] | 5.2.2 |

## 5. Feature timeline
| Version | Change | PR |
|---|---|---|
| 1.2 | Plugins replace Addons; Mailchimp API key; HubSpot push; required-key validation | [PR #740] [PR #1184] [PR #1074] [PR #1230] |
| 2.0–2.4 | Salesforce fetchleads, object choice, activity push, sandbox; Outlook/Gmail tracking; Clearbit/FullContact; Citrix; HubSpot pull | [PR #1825] [PR #1955] [PR #1978] [PR #2175] [PR #2604] [PR #2933] [PR #2934] [PR #2850] [PR #3026] |
| 2.6–2.8 | SF dedupe and DB cache; data-direction mapping; Integration Campaigns filter; SF campaign push; timeline-link field; API-error notifications | [PR #3373] [PR #2954] [PR #3508] [PR #3733] [PR #3753] [PR #3774] [PR #3984] |
| 2.9–2.12 | Zoho two-way; Dynamics; ConnectWise; Pipedrive; Sugar full sync; `updateBlanks`; DNC field; DNC latest-wins | [PR #4068] [PR #4212] [PR #4214] [PR #4163] [PR #4247] [PR #4445] [PR #4459] [PR #4920] |
| 2.13–2.16 | Zapier; contact-ID field; plugin install CLI; S3 region; Zoho API v2; SF TLS 1.2 | [PR #5794] [PR #5655] [PR #6201] [PR #6945] [PR #8272] [PR #7814] |
| 3.0 | IntegrationsBundle and sync engine in core; `UnifiedIntegrationInterface`; constructor DI; Rackspace/OpenStack removed | [PR #8210] [PR #8433] [PR #8128] [PR #8310] |
| 3.1–3.3 | Key-less publish; read-only HubSpot properties; all mapped fields on full report | [PR #9050] [PR #8785] [PR #9063] |
| 4.0 | Marketplace (read-only); sync `--option`; monorepo `replace`; Tag Manager plugin | [PR #9650] [PR #9796] [PR #9920] [PR #9364] |
| 4.1–4.4 | Marketplace install via Composer; `AbstractIntegration` deprecated; retry-only-flagged; HubSpot Private App token | [PR #10518] [PR #11050] [PR #11252] [PR #11470] |
| 4.4.9 | Pipedrive and Citrix deprecation notices | [PR #12364] [PR #12367] |
| 5.0 | Pipedrive and Citrix removed; Twig templates; type/length validation on pull; before-field-changes events; config notes; S3 endpoint | [PR #12081] [PR #12333] [PR #11862] [PR #11303] [PR #10512] [PR #11451] [PR #11693] |
| 5.0 | `getLeadData()` detach check inverted (regression) | [PR #12361] |
| 5.1 | One-way fields protected; cleanup command; audit attribution; default token expiry; auth-URL event; SF DNC pull for new records; ConnectWise Client ID; batch tag actions | [PR #11251] [PR #13340] [PR #13426] [PR #13429] [PR #13434] [PR #13411] [PR #13408] [PR #13711] |
| 5.2 | Token redaction; SF self-healing mapping; tag usages | [PR #14277] [PR #13406] [PR #13917] |
| 6.0 | Required-empty values skip instead of abort; DB connection by DI; Froala removed | [PR #14666] [PR #14418] [PR #14271] [PR #14284] |
| 7.0 | Publish veto event; IntegrationsBundle test HTTP mocking; S3 credential error | [PR #13696] [PR #15084] [PR #14865] |
| 7.1 | Plugin version badge; page-load JS events | [PR #15789] |
| 7.2 | Clearbit, Gmail, Tag Manager on `BasicIntegration`; final DAOs; autowired services; tag merge, search, delete-in-use; legacy mapping pagination | [PR #16586] [PR #16847] [PR #16795] [PR #16888] [PR #16781] [PR #15331] [PR #16003] [PR #16132] [PR #16202] |
| 7.2.2 | `pushleadactivity` pushes again | [PR #17815] |
| unreleased 7.x | Duplicate tag names refused | [PR #17341] |
| 8.x | Clearbit removed | [PR #17785] |

## 6. Removed, deprecated, replaced
| What | Replaced by | PR | Version |
|---|---|---|---|
| Addons, `/addons` | Plugins, `/plugins` | [PR #740] | 1.2 |
| `IntegrationPass` setter injection | Constructor injection | [PR #8128] | 3.0 |
| Standalone plugin-integrations repo | Core IntegrationsBundle | [PR #8210] | 3.0 |
| Rackspace, OpenStack storage | Amazon S3 | [PR #8310] | 3.0 |
| `amendToSfFields` in Salesforce/Sugar | removed | [PR #8143] | 3.0 |
| Zoho API v1, GoTo OAuth1, SF TLS 1.1, Mcrypt | Zoho v2, OAuth2, TLS 1.2, OpenSSL | [PR #8272] [PR #7380] [PR #7814] [PR #6893] | 2.15–2.16 |
| Guzzle array `body` | `form_params` | [PR #10301] | 4.0 |
| `AbstractIntegration` | IntegrationsBundle (deprecated, still shipped) | [PR #11050] | 4.3 |
| HubSpot `hapikey` | Private App token | [PR #11470] [PR #11857] | 4.4.5 / 5.0 |
| `IntegrationsBundle/Configuration/PluginConfiguration.php` | removed | [PR #11032] | 5.0 |
| PHP templates | Twig | [PR #11862] [PR #11960] [PR #11560] [PR #12139] | 5.0 |
| `EntityManager::clear()` | `detach()` | [PR #12341] [PR #12342] [PR #12361] | 5.0 |
| Pipedrive, Citrix | Marketplace / third-party plugins | [PR #12081] [PR #12333] | 5.0 |
| ConnectWise appcookie | Client ID | [PR #13408] | 5.1 |
| `MauticFactory::getDatabase()`, `FieldModel::getUniqueIdentiferFields()` | DI, unique-identifier lookup | [PR #14418] [PR #14144] | 6.0 |
| Froala styles, Gated Video | removed | [PR #14271] [PR #14284] | 6.0 |
| `config.php` service arrays, tagged compiler passes, `getModel('plugin')` | `services.php`, `#[AutowireIterator]`, typed injection | [PR #16781] [PR #16776] [PR #16625] | 7.2 |
| Clearbit | nothing | [PR #17785] | 8.x |

## 7. Maintainer norms for this area
- Keep all core-supported CRMs in `MauticCrmBundle`; do not add a plugin per CRM. [PR #4212]
- Third-party integrations do not belong in core; move them to the Marketplace and name the alternative. [PR #12081] [PR #12333]
- Deprecate a plugin in one release with front-end notices, and remove it only in the next major. [PR #12364] [PR #12367]
- Removing a core plugin is a `bc-break` for the major branch only, with an UPGRADE entry and removal of split, composer and baseline config. [PR #17785]
- Mirror repos are read-only; all PRs go to mautic/mautic. [PR #9925] [PR #11154]
- Show users only API errors, never code exceptions. [PR #3984]
- Never log secrets; mark redaction visibly as `[REDACTED]`. [PR #14277]
- Public plugin endpoints must sanitise input and verify a shared-secret signature. [PR #2175]
- SOQL values must be escaped and SQL parameterised. [PR #4041] [PR #4997]
- Performance blocks merges; add indexes and avoid repeated queries in sync paths. [PR #3733] [PR #9313] [PR #13086]
- Two tests are required to merge, but code review plus production evidence is accepted when nobody has the third-party account. [PR #10993] [PR #13208] [PR #15948]
- Bug fixes need a regression test that fails without the fix. [PR #16202] [PR #17815]
- When a shared CRM base class changes, check every caller. [PR #17815]
- No back-merges; each branch needs its own PR. [PR #11775] [PR #11857]
- BC breaks need labelling and an UPGRADE entry; childless classes are made `final`. [PR #9886] [PR #13842] [PR #16902]
- "Unforking" upstreams Acquia fork code but drops needless indirection. [PR #14666] [PR #15056]

## 8. Open questions
- PR #13521 says integration classes are autoconfigured with the right tags, but 7.x does not auto-tag `mautic.sync_integration` or `mautic.authentication_integration`. behaviour.md (manual tagging) is followed. [PR #13521] [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:26-33 @7.x]
- PR #13340 describes the cleanup command as covering Contacts and Companies; behaviour.md item 54 says Contacts only. behaviour.md is followed. [PR #13340]
- HubSpot's `hapikey` branch still runs when no `accessKey` is stored; whether any key-mode path still works against HubSpot is unknown. [PR #11470] [code: plugins/MauticCrmBundle/Api/HubspotApi.php:23 @7.x]
- PR #12081 says its migration removes `integration_entity` records; whether only Pipedrive rows or all rows were removed is unclear. [PR #12081]
- PR #10497 gates company push on `push_companies`, which Salesforce may never set. [PR #10497]
- PR #16888 and PR #16902 made classes `final` in a 7.x minor, while PR #13842 treats subclass-breaking changes as major-only. [PR #16888] [PR #13842]
- The Gmail move to `BasicIntegration` may have broken Gmail tracking (`getDecryptedApiKeys()`); not verified at runtime. [PR #16847]
- PR #13406: whether auto-unmapping covers Lead and Contact equally. [PR #13406]
- PR #1825: whether the Salesforce 30-day lookback limit still applies. [PR #1825]
- PR #5424 removed the ConnectWise company from the push while PR #5333 added company lookup; current precedence unchecked. [PR #5424] [PR #5333]
- PR #16132 deletes an in-use tag without rewriting segment or campaign references, unlike PR #15331 merge. [PR #16132] [PR #15331]
- PR #17341: whether duplicate tag matching is case-sensitive. [PR #17341]
- PR #4063 broke a third-party SSO plugin; never resolved whether that was a core BC break. [PR #4063]

## 9. Coverage
- integrations-plugins-marketplace: 221 PRs in 3 chunks (104 + 83 + 34); 193 substantive. [PR #740] [PR #16905]
- bundled-plugins: 271 PRs in 4 chunks (99 + 83 + 86 + 3); 227 substantive. Mis-bucketed core editor PRs were skipped. [PR #846] [PR #17815]
- Some PRs appear in both buckets (for example [PR #3784], [PR #4024], [PR #11470]) and are merged here.
- 869 noise PRs were excluded upstream before chunking. [PR #740]
- Items tagged [plugin-dev] are covered by mautic-plugin-development and are summarised here only where they change integration behaviour. [PR #13696]
