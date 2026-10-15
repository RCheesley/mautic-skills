---
name: mautic-contacts
description: Mautic contacts, companies, custom fields, CSV import, Do Not Contact (DNC), contact identification and merging, deduplication, web tracking identity (mautic_device_id, mtc_id), UTM tags, tags, notes, frequency rules and the contact/company/field/note REST API. Use whenever a task mentions contacts, leads, visitors, anonymous contacts, companies, primary company, custom fields, unique identifiers, merge or duplicate contacts, import, doNotEmail, DNC, unsubscribe reasons, tags, UTM, owner, notes, frequency rules, contact export, /api/contacts, /api/companies, /api/fields, /api/notes, mautic:import, mautic:contacts:deduplicate, mautic:custom-field:*, LeadModel, FieldModel, CompanyModel, ContactMerger, ContactTracker, DoNotContact, LeadField, CustomFieldRepositoryTrait, LeadEvents, or touches app/bundles/LeadBundle/ outside Segment/ and LeadList*.
---
# Mautic contacts, companies and fields

## Scope
This skill covers the Contact record (code name `Lead`, table `leads`), Companies, custom fields, identification and
merging, web tracking identity, tags, UTM tags, DNC, frequency rules, notes, import, export and their REST API, all in
`app/bundles/LeadBundle/`. Segments (`Segment/`, `LeadList*`) are in mautic-segments; points actions, triggers and stages
are in mautic-points-and-stages; email unsubscribe and bounce processing is in mautic-emails.

Terms: a **Contact** is a person; a **Visitor** is an anonymous tracked contact; a **unique identifier** is a field used
to find an existing record; **DNC** (Do Not Contact) is a per-channel opt-out with a reason; a **Channel** is a medium
such as `email` or `sms`; a **Frequency rule** caps messages per channel per period.

## Expected behaviour (essentials)
Identification and tracking
- A contact is anonymous unless firstname, lastname, company, email or a social field has a value; phone and other fields do not identify. [code: app/bundles/LeadBundle/Entity/Lead.php:1165-1174 @7.x]
- `date_identified` is set once, the first time a contact stops being anonymous, and then `LEAD_IDENTIFIED` fires and the `lead_post_save_new` webhook fires; anonymous saves never fire contact webhooks. [code: app/bundles/LeadBundle/Entity/Lead.php:1420-1426 @7.x] [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:131-158 @7.x]
- The Contacts list hides anonymous contacts unless the search contains `is:anonymous` (= `date_identified IS NULL`). [code: app/bundles/LeadBundle/Controller/LeadController.php:192-206 @7.x]
- Logged-in Mautic users, `Blocked-Tracking` cookies, bots and console contexts are never tracked; bots get an unsaved Lead. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-60 @7.x] [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:246-253 @7.x]
- Current-contact order: `LeadGetCurrentEvent` listener, `mautic_device_id` device, legacy `mtc_id` cookie, same IP (only if `track_contact_by_ip`), new contact. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:191-267 @7.x]
- Tracking query parameters update only published fields marked publicly updatable, and find existing contacts only through unique identifiers. [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:97-150 @7.x]

Duplicates and merge
- Duplicate lookup uses published unique-identifier fields (email by default) combined with OR by default (`contact_unique_identifiers_operator`); the newest match wins. [code: app/bundles/LeadBundle/Config/config.php:360-361 @7.x] [code: app/bundles/LeadBundle/Entity/LeadRepository.php:245-256 @7.x]
- Unique identifiers are not DB unique constraints; duplicates exist until `mautic:contacts:deduplicate` merges them. [code: app/bundles/LeadBundle/Command/DeduplicateCommand.php:30-115 @7.x]
- In a merge the loser is deleted and its id resolves to the winner forever (merge records), including through the API. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:46-78 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:303-355 @7.x]
- Merged field values come from the most recently modified contact, not from the winner; points sum, tags union, owner and primary company kept unless empty. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:119-271 @7.x]
- The loser's DNC rows, frequency rules, UTM tags, stage and categories are not merged; SMS and push stats are not moved. [code: app/bundles/LeadBundle/Entity/Lead.php:336-343 @7.x] [code: app/bundles/SmsBundle/Entity/StatRepository.php:169 @7.x]
- The winner depends on the caller: UI = viewed contact, API edit = URL contact, clickthrough = tracked contact, form = identified contact, dedupe command = newest. [code: app/bundles/LeadBundle/Controller/LeadController.php:1064 @7.x] [code: app/bundles/LeadBundle/Deduplicate/ContactDeduper.php:93-131 @7.x]

Field values
- Every write passes `addUpdatedField()`: trims strings, turns '' into null, joins arrays with `|`, records only real changes. [code: app/bundles/LeadBundle/Entity/CustomFieldEntityTrait.php:106-157 @7.x]
- A `select` value outside its option list is reset to null on every save. [code: app/bundles/LeadBundle/Model/LeadModel.php:2518-2544 @7.x]
- New contacts receive field default values for empty fields. [code: app/bundles/LeadBundle/Model/LeadModel.php:501 @7.x]
- Points are changed by atomic SQL after save; never write `points` as a plain field. [code: app/bundles/LeadBundle/Entity/LeadRepository.php:1370-1435 @7.x]

Companies
- One primary company per contact; `leads.company` mirrors its name; adding companies makes the first new one primary. [code: app/bundles/LeadBundle/Entity/CompanyLeadRepository.php:22-52 @7.x]
- Setting the contact `company` field finds or creates the company by company unique identifiers and makes it primary. [code: app/bundles/LeadBundle/Helper/IdentifyCompanyHelper.php:11-117 @7.x]
- API `companies` on a contact replaces the whole list. [code: app/bundles/LeadBundle/Model/LeadModel.php:1882-1907 @7.x]
- Deleting a company is a soft delete followed by cleanup and hard delete (immediate unless `update_company_mapping_data_in_background`); the hard delete nulls `leads.company` for every contact with that company name. [code: app/bundles/LeadBundle/EventListener/CompanySubscriber.php:60-114 @7.x]

DNC
- Reasons: 0 contactable, 1 unsubscribed, 2 bounced, 3 manual; DNC is per channel. [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-32 @7.x]
- An existing unsubscribe is overwritten only with override enabled; `DoNotContactAddEvent` enables it by default, the campaign action does not. [code: app/bundles/LeadBundle/Model/DoNotContact.php:79-140 @7.x] [code: app/bundles/LeadBundle/Event/DoNotContactAddEvent.php:15-24 @7.x]
- DNC changes save the contact, so `CHANNEL_SUBSCRIPTION_CHANGED` fires per channel. [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:74-87 @7.x]
- API DNC add defaults to reason 3 and rejects reason 0 with 400. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:450-513 @7.x]

API
- `POST /api/contacts/new` updates an existing contact matched by unique identifiers (200) instead of creating one (201). [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:579-582 @7.x]
- PATCH edit with identifiers matching another contact merges that contact into the URL contact. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:616-628 @7.x]
- POST and PATCH ignore blanks and numeric 0 unless `overwriteWithBlank`; PUT writes blanks. [code: app/bundles/LeadBundle/Controller/Api/CustomFieldsApiControllerTrait.php:175-210 @7.x]
- API `tags` are additive (`-tag` removes); the UI form replaces the tag set. [code: app/bundles/LeadBundle/Model/LeadModel.php:1788-1874 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:1641-1682 @7.x]
- Batches over `api_batch_max_limit` (200) get 400; per-item status codes sit inside the overall response. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:730-733 @7.x]

Custom fields and import
- Creating a field runs `ALTER TABLE` synchronously unless `create_custom_field_in_background`, which saves it unpublished, returns 202 from the API, and waits for `mautic:custom-field:create-column`. [code: app/bundles/LeadBundle/Model/FieldModel.php:627-633 @7.x] [code: app/bundles/LeadBundle/Controller/Api/FieldApiController.php:82-93 @7.x]
- A field used in a segment filter cannot be deleted (API 409). [code: app/bundles/LeadBundle/Field/EventListener/LeadFieldSubscriber.php:33-52 @7.x]
- Import matches by `id` column or unique identifiers; empty cells never overwrite; literal `NULL` clears; `doNotEmail` applies only when the row has an email. [code: app/bundles/LeadBundle/Model/LeadModel.php:1342-1350 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:2553-2583 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:1471-1489 @7.x]
- Background imports wait for `mautic:import` cron; one runs at a time by default; imports stuck over 2 hours become FAILED. [code: app/bundles/LeadBundle/Model/ImportModel.php:121-186 @7.x]

## Where it lives
| Concern | Path |
|---|---|
| Contact entity / table `leads` | `app/bundles/LeadBundle/Entity/Lead.php`, `CustomFieldEntityTrait.php`, `LeadRepository.php`, `CustomFieldRepositoryTrait.php` |
| Field definitions / `lead_fields` | `app/bundles/LeadBundle/Entity/LeadField.php`, `Model/FieldModel.php`, `Field/` (schema, background commands) |
| Companies / `companies`, `companies_leads` | `app/bundles/LeadBundle/Entity/Company.php`, `CompanyLead.php`, `Model/CompanyModel.php`, `Helper/IdentifyCompanyHelper.php` |
| Contact model | `app/bundles/LeadBundle/Model/LeadModel.php` |
| Merge / dedupe | `app/bundles/LeadBundle/Deduplicate/` |
| Tracking identity | `app/bundles/LeadBundle/Tracker/`, `Helper/ContactRequestHelper.php` |
| DNC / `lead_donotcontact` | `app/bundles/LeadBundle/Model/DoNotContact.php`, `Entity/DoNotContact.php`, `EventListener/DoNotContactSubscriber.php` |
| Import / `imports` | `app/bundles/LeadBundle/Model/ImportModel.php`, `Controller/ImportController.php`, `Command/ImportCommand.php` |
| Events | `app/bundles/LeadBundle/LeadEvents.php`, `Helper/LeadChangeEventDispatcher.php` |
| API | `app/bundles/LeadBundle/Controller/Api/` (`LeadApiController`, `CompanyApiController`, `FieldApiController`, `CustomFieldsApiControllerTrait`) |
| Routes and parameters | `app/bundles/LeadBundle/Config/config.php` (routes 7-293, parameters 336-374) |
| Permissions | `app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php` (`lead:leads`, `lead:notes`, `lead:fields`, `lead:imports`, `lead:export`) |
| Tests | `app/bundles/LeadBundle/Tests/` |

[code: app/bundles/LeadBundle/Config/config.php:7-374 @7.x] Full detail: references/code-map.md.

## How to change or extend it
- React to contact changes with a `LEAD_POST_SAVE` listener and `$event->getChanges()`; do not add logic to `LeadModel::saveEntity`. [code: app/bundles/LeadBundle/EventListener/LeadSubscriber.php:77 @7.x]
- Any plugin table keyed by contact id needs a `LEAD_POST_MERGE` listener that moves rows from `getLoser()` to `getVictor()`, or the data is orphaned. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:72 @7.x]
- Change DNC through the `DoNotContact` model or `DoNotContactAddEvent`/`DoNotContactRemoveEvent`, never by writing `lead_donotcontact` directly, so the channel-subscription event and audit log fire. [code: app/bundles/LeadBundle/Model/DoNotContact.php:31-227 @7.x]
- Change points with `adjustPoints()`/`setPoints()`; change tags with `modifyTags()` when additive semantics are wanted. [code: app/bundles/LeadBundle/Entity/Lead.php:808-871 @7.x]
- Write custom-field values via `addUpdatedField()`/`setFieldValues()`; dynamic columns are written by DBAL after flush. [code: app/bundles/LeadBundle/Entity/CustomFieldRepositoryTrait.php:267-293 @7.x]
- A new fixed column on `leads` needs: entity mapping in `Lead.php`, a migration in `app/migrations/`, a `FieldModel::$coreFields` entry, API serializer groups, translations and docs. Custom fields need no migration because `FieldModel` alters the table at runtime. [code: app/bundles/LeadBundle/Model/FieldModel.php:49-478 @7.x]
- Use timeline (`TIMELINE_ON_GENERATE`), import (`IMPORT_ON_*`) and search (`LEAD_BUILD_SEARCH_COMMANDS`) events to extend the UI. [code: app/bundles/LeadBundle/LeadEvents.php:160-409 @7.x]
- Keep backward compatible: the misspelled `is_unique_identifer` column, the API field names, the `LeadEvents` string names on 7.x, and webhook type ids. [code: app/bundles/LeadBundle/Controller/Api/FieldApiController.php:117-121 @7.x]
- For code that must also run on 8.x, subscribe by event class as well as by string and avoid APIs removed in 8 (see Version notes). [PR #17218]

## How to test it
- Functional tests extend `MauticMysqlTestCase` (admin logged in, transaction rolled back); set `$this->configParams` before `parent::setUp()`. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:35-64 @7.x]
- Set `$useCleanupRollback = false` for tests that create custom fields, because `ALTER TABLE` commits the transaction. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:22-30 @7.x]
- Copy from: `Tests/Controller/Api/LeadApiControllerFunctionalTest.php` (API, DNC, batch), `Tests/Deduplicate/ContactMergerTest.php` and `ContactMergerFunctionalTest.php` (merge), `Tests/Model/LeadModelTest.php` (import, duplicates), `Tests/Tracker/ContactTrackerFunctionalTest.php` (tracking), `Tests/Controller/Api/FieldApiControllerFunctionalTest.php` (fields). [code: app/bundles/LeadBundle/Tests @7.x]
- A good regression test asserts the stored outcome: surviving ids, field values, DNC reason and channel, 200 versus 201, and the timeline or audit entry. Full detail: references/test-patterns.md.

## Version notes
- 5.0 locked default values of identifying fields; 5.1 added `mautic:fields:analyse` and custom country/region lists. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#custom-fields]
- 7.2 deprecated `AjaxController::addLeadUtmTagsAction`. [code: app/bundles/LeadBundle/Controller/AjaxController.php:631 @7.x]
- The 7.x branch added, after 7.2.1 and not yet released, `POST /api/companies/batch/addcontacts` [PR #16512], "Any associated company" filters [PR #15800] and Quick Add "Save & New" [PR #16849]; they are documented in the 8.0 docs and not yet on the 8.x branch. [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:121-153 @7.x]
- 8.x dispatches events by class (56 LeadBundle constants removed; subscribe to `LeadPostSaveEvent`, `LeadPostMergeEvent`, `CompanySoftDeleteEvent` ...). [PR #17218] [PR #17545]
- 8.x removes `LeadModel::isContactable()`, `FieldModel::getFieldList()`, `CompanyModel::getCompanyLeadRepository()`, `LeadModel::getTagRepository()`, and makes `IdentifyCompanyHelper` an instance service. [PR #17247] [PR #17248] [PR #17260]
- 8.x unique-identifier columns get length 255 (7.x: 191) and require PHP 8.4, Symfony 8.1, Doctrine ORM 3 / DBAL 4. [PR #17361]
Full detail: references/version-notes.md.

## Pitfalls
- The docs say the default duplicate operator is AND; the code default is OR for contacts and companies. [code: app/bundles/LeadBundle/Config/config.php:360-361 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#managing-duplicates]
- The docs say merging only fills empty fields; the code takes the most recently modified contact's non-empty values. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:119-172 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#merge-two-contacts]
- The docs say the most recently attached company becomes primary after a company delete; the code takes the first row of an unordered query. [code: app/bundles/LeadBundle/Entity/CompanyLeadRepository.php:54-76 @7.x] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#deleting-companies]
- "Own" differs: entity access uses owner or creator, the UI `is:mine` list uses owner only, the API list uses owner or (no owner and creator). [code: app/bundles/LeadBundle/Entity/Lead.php:662-665 @7.x] [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:137-164 @7.x]
- Setting `owner` through the API does not check permissions on the target user. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:645-649 @7.x]
- Maintenance cleanup deletes anonymous contacts with raw SQL; no delete events, webhooks or audit entries. [code: app/bundles/LeadBundle/EventListener/MaintenanceSubscriber.php:26-83 @7.x]
- Import and new contacts never fire `LEAD_POINTS_CHANGE`, and imported contacts skip IP geolocation. [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:42-62 @7.x]
- Campaign "change owner" bypasses `LeadModel::saveEntity` extras. [code: app/bundles/LeadBundle/Model/LeadModel.php:2375-2381 @7.x]
- `LEAD_IDENTIFIED`, `LEAD_UTMTAGS_ADD`, batch-save and column events have no core listener; a missing side effect there is expected. [code: app/bundles/LeadBundle/LeadEvents.php:50-140 @7.x]
- Marking a field unique silently changes its column to varchar and adds an index. [code: app/bundles/LeadBundle/Field/SchemaDefinition.php:17-23 @7.x]
- Suspected bugs to verify before relying on them: `analyzePermissions()` uses `==` where `!=` looks intended; `addDncForContact()` return value with an unsubscribe and no override; `removeBounceStatusAction` lacks a permission check; `setFrequencyRules(persist: false)` deletes all rules. [code: app/bundles/LeadBundle/Model/DoNotContact.php:105-130 @7.x] [code: app/bundles/LeadBundle/Controller/AjaxController.php:420-447 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:1180-1183 @7.x]
- Open question: one docs page says UTM tags are recorded only by the "Record UTM Tags" form action, while the UTM pages say page visits record them too. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#utm-code] [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_landing_pages.html]
- Open question: the docs say companies are matched strictly by name, city and country/state; the code matches on the configured company unique identifiers. [code: app/bundles/LeadBundle/Helper/IdentifyCompanyHelper.php:11-60 @7.x] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#identifying-companies]

## Related skills
- mautic-segments: segment filters, membership, `mautic:segments:update`, manual add/remove flags.
- mautic-points-and-stages: point actions, triggers, groups and stages that write to contacts.
- mautic-campaigns: campaign actions and conditions on contacts (update contact, change tags, add DNC, delete contact).
- mautic-emails: DNC created by unsubscribes and bounces, frequency enforcement at send, Preference Center email flow.
- mautic-forms: contact creation and merging from form submissions, Record UTM Tags action.
- mautic-pages-and-tracking: tracking script and pixel, page hits, landing-page identity.
- mautic-rest-api: authentication, pagination and batch conventions shared by all endpoints.
- mautic-users-and-permissions: the role and permission framework behind `lead:*` permissions.
- mautic-integrations: CRM sync of contacts and companies through the integrations framework.
- mautic-testing: test environment, base classes and running the suite.
- mautic-upgrades-and-versions: platform upgrades and the 7.x to 8.x porting guide.

## Reference files
- references/behaviour.md — the full numbered behaviour specification with citations and the contradiction list; open it before changing or testing any rule.
- references/code-map.md — entities, tables, models, events, routes, API endpoints, commands, parameters, permissions, extension points.
- references/docs-digest.md — what docs.mautic.org and devdocs say, with URLs, procedures and terminology.
- references/test-patterns.md — base classes, helpers, representative tests and test skeletons.
- references/version-notes.md — history, 5.x/6.x, 7.x minors and the 8.x delta with dual-version code.
- references/pr-history.md — not yet generated; PR-derived history is added in a later pass.
