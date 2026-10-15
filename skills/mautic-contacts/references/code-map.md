# Contacts code map (Mautic 7.x)

All paths from the repository root; `LB` is never used as an abbreviation in citations. Segments (`Segment/`,
`LeadList*`, `ListModel`) are mapped in the mautic-segments skill.

## Table of contents
1. Entities and tables
2. Models and services
3. Events
4. Controllers, routes and API endpoints
5. Console commands
6. Configuration parameters
7. Permissions
8. Extension points
9. Tests
10. Deprecations

## 1. Entities and tables

| Entity | Table | Notes | Source |
|---|---|---|---|
| `Lead` | `leads` | BigInt id; `owner_id` SET NULL; `stage_id` SET NULL; `points` int; fixed field columns mapped, others dynamic; indexes `lead_date_added`, `lead_date_modified`, `date_identified`, `last_active` | [code: app/bundles/LeadBundle/Entity/Lead.php:294-471 @7.x] |
| `LeadField` | `lead_fields` | label, alias (unique), type, field_group, default_value, is_required, is_fixed, is_visible, is_short_visible, is_listable, is_publicly_updatable, `is_unique_identifer` (sic), is_index, char_length_limit, field_order, object (`lead`/`company`), properties, column_is_not_created, column_is_not_removed | [code: app/bundles/LeadBundle/Entity/LeadField.php:217-305 @7.x] |
| `Company` | `companies` | `deleted` datetime = soft delete; `score`; `owner_id` SET NULL; custom company fields are columns | [code: app/bundles/LeadBundle/Entity/Company.php:51 @7.x] [code: app/bundles/LeadBundle/Entity/Company.php:176-218 @7.x] |
| `CompanyLead` | `companies_leads` | PK (company_id, lead_id), both CASCADE; `date_added`, `is_primary` | [code: app/bundles/LeadBundle/Entity/CompanyLead.php:12-53 @7.x] |
| `DoNotContact` | `lead_donotcontact` | reason 0/1/2/3, channel, channel_id, comments, date_added | [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-90 @7.x] |
| `FrequencyRule` | `lead_frequencyrules` | frequency_number, frequency_time, channel, preferred_channel, pause_from_date, pause_to_date | [code: app/bundles/LeadBundle/Entity/FrequencyRule.php:66-98 @7.x] |
| `Import` | `imports` | status 1 QUEUED, 2 IN_PROGRESS, 3 IMPORTED, 4 FAILED, 5 STOPPED, 6 MANUAL, 7 DELAYED; priority LOW 512 / NORMAL 64 / HIGH 1 | [code: app/bundles/LeadBundle/Entity/Import.php:21-60 @7.x] |
| `LeadNote` | `lead_notes` | text, type, date_time; lead FK cascade | [code: app/bundles/LeadBundle/Entity/LeadNote.php:45-60 @7.x] |
| `Tag` | `lead_tags` (+ `lead_tags_xref`) | tag indexed, not unique; description; uuid | [code: app/bundles/LeadBundle/Entity/Tag.php:73-80 @7.x] |
| `UtmTag` | `lead_utmtags` | | [code: app/bundles/LeadBundle/Entity/UtmTag.php:78-93 @7.x] |
| `LeadDevice` | `lead_devices` | tracking_id plus device fields | [code: app/bundles/LeadBundle/Entity/LeadDevice.php:77-86 @7.x] |
| `MergeRecord` | `contact_merge_records` | contact_id (winner), merged_id (loser id), name | [code: app/bundles/LeadBundle/Entity/MergeRecord.php:41-44 @7.x] |
| `LeadEventLog` | `lead_event_log` | bundle/object/action/object_id/properties | [code: app/bundles/LeadBundle/Entity/LeadEventLog.php:80-87 @7.x] |
| `PointsChangeLog`, `CompanyChangeLog`, `StagesChangeLog` | `lead_points_change_log`, `lead_companies_change_log`, `lead_stages_change_log` | | [code: app/bundles/LeadBundle/Entity/PointsChangeLog.php:14 @7.x] |
| `LeadCategory` | `lead_categories` | category subscription | [code: app/bundles/LeadBundle/Entity/LeadCategory.php:79 @7.x] |
| `ContactExportScheduler` | `contact_export_scheduler` | queued CSV exports | [code: app/bundles/LeadBundle/Entity/ContactExportScheduler.php:40 @7.x] |
| IP addresses | `lead_ips_xref` | ManyToMany, keyed by IP | [code: app/bundles/LeadBundle/Entity/Lead.php:345-353 @7.x] |

Core field definitions: `FieldModel::$coreFields` and `$coreCompanyFields`. [code: app/bundles/LeadBundle/Model/FieldModel.php:49-478 @7.x]
Column types per field type: [code: app/bundles/LeadBundle/Field/SchemaDefinition.php:13-68 @7.x]

## 2. Models and services

| Class | Path | Responsibility |
|---|---|---|
| `LeadModel` | `app/bundles/LeadBundle/Model/LeadModel.php` | `getEntity()` follows merges (`:303-321`); `saveEntity()` (`:453-523`); `setFieldValues()` (`:551-704`); `checkForDuplicateContact()` (`:875-930`); `setFrequencyRules()` (`:1106-1186`); `import()` (`:1332-1634`); `setTags()` (`:1641-1682`); `addUTMTags()` (`:1698-1780`); `modifyTags()` (`:1788-1874`); `modifyCompanies()` (`:1882-1907`); `getEngagements()` (`:2185-2204`); `setPrimaryCompany()` (`:2306-2348`) [code: app/bundles/LeadBundle/Model/LeadModel.php @7.x] |
| `FieldModel` | `app/bundles/LeadBundle/Model/FieldModel.php` | `saveEntity()` creates/updates column (`:614-641`); `deleteEntity()` (`:671-689`) [code: app/bundles/LeadBundle/Model/FieldModel.php:614-689 @7.x] |
| `CompanyModel` | `app/bundles/LeadBundle/Model/CompanyModel.php` | add/remove contacts (`:278-518`), `companyMerge()` (`:675-726`), `importCompany()` (`:810-925`), soft `deleteEntity()` (`:989-997`) [code: app/bundles/LeadBundle/Model/CompanyModel.php @7.x] |
| `DoNotContact` (model) | `app/bundles/LeadBundle/Model/DoNotContact.php` | add/remove/isContactable/create/update DNC [code: app/bundles/LeadBundle/Model/DoNotContact.php:31-227 @7.x] |
| `ImportModel` | `app/bundles/LeadBundle/Model/ImportModel.php` | queue selection, parallel limit, ghost imports, `process()` [code: app/bundles/LeadBundle/Model/ImportModel.php:70-421 @7.x] |
| `NoteModel`, `TagModel`, `DeviceModel`, `BatchCompanyContactAssignmentModel`, `ContactExportSchedulerModel` | `app/bundles/LeadBundle/Model/` | notes, tags (`tagMerge()`), devices, API batch company assignment, scheduled exports [code: app/bundles/LeadBundle/Model/TagModel.php:153-180 @7.x] |
| `ContactMerger` | `app/bundles/LeadBundle/Deduplicate/ContactMerger.php` | `merge(winner, loser)` [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:46-78 @7.x] |
| `ContactDeduper`, `CompanyDeduper`, `MergeValueHelper` | `app/bundles/LeadBundle/Deduplicate/` | duplicate detection and merge value rule [code: app/bundles/LeadBundle/Deduplicate/ContactDeduper.php:93-131 @7.x] |
| `ContactTracker` | `app/bundles/LeadBundle/Tracker/ContactTracker.php` | current web contact, system contact [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-333 @7.x] |
| `DeviceTracker`, `DeviceTrackingService`, `ContactTrackingService` | `app/bundles/LeadBundle/Tracker/` | cookies and devices [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:119-136 @7.x] |
| `ContactRequestHelper` | `app/bundles/LeadBundle/Helper/ContactRequestHelper.php` | identify contact on tracking requests [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:97-216 @7.x] |
| `IdentifyCompanyHelper` | `app/bundles/LeadBundle/Helper/IdentifyCompanyHelper.php` | find or create company from contact data (static in 7.x) [code: app/bundles/LeadBundle/Helper/IdentifyCompanyHelper.php:11-117 @7.x] |
| `CustomFieldHelper` | `app/bundles/LeadBundle/Helper/CustomFieldHelper.php` | type coercion [code: app/bundles/LeadBundle/Helper/CustomFieldHelper.php:29-95 @7.x] |
| `LeadChangeEventDispatcher` | `app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php` | identified/points/UTM/DNC change events [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:33-87 @7.x] |
| `CustomFieldColumn`, `BackgroundService`, `LeadFieldSaver`, `LeadFieldDeleter`, `SchemaDefinition`, `FieldsWithUniqueIdentifier`, `FieldList` | `app/bundles/LeadBundle/Field/` | custom-field schema changes [code: app/bundles/LeadBundle/Field/CustomFieldColumn.php:41-114 @7.x] |
| `CustomFieldRepositoryTrait` | `app/bundles/LeadBundle/Entity/CustomFieldRepositoryTrait.php` | DBAL field writes, unique-identifier queries [code: app/bundles/LeadBundle/Entity/CustomFieldRepositoryTrait.php:267-461 @7.x] |

`LeadModel` dispatches the `LEAD_*` CRUD events only when listeners exist; audit logging happens in listeners. [code: app/bundles/LeadBundle/Model/LeadModel.php:360-391 @7.x]

## 3. Events (`app/bundles/LeadBundle/LeadEvents.php`)

| Constant | Event class | Dispatched at | Core listeners |
|---|---|---|---|
| `LEAD_PRE_SAVE` / `LEAD_POST_SAVE` | `LeadEvent` | `LeadModel.php:368,371`; `ContactTracker.php:282,287` | `LeadSubscriber::onLeadPostSave` (audit + change events), `WebhookSubscriber`, PointBundle (prio -1), IntegrationsBundle, PluginBundle, enrichment plugins [code: app/bundles/LeadBundle/LeadEvents.php:20-30 @7.x] |
| `LEAD_PRE_DELETE` / `LEAD_POST_DELETE` | `LeadEvent` | `LeadModel.php:374,377` | segment count decrement (pre); audit, webhook, integrations (post) [code: app/bundles/LeadBundle/LeadEvents.php:100-110 @7.x] |
| `LEAD_IDENTIFIED` | `LeadEvent` | `LeadChangeEventDispatcher.php:39` | none [code: app/bundles/LeadBundle/LeadEvents.php:140 @7.x] |
| `LEAD_POINTS_CHANGE` | `PointsChangeEvent` | `LeadChangeEventDispatcher.php:61` | PointBundle, Webhook [code: app/bundles/LeadBundle/LeadEvents.php:40 @7.x] |
| `LEAD_UTMTAGS_ADD` | `LeadUtmTagsEvent` | `LeadChangeEventDispatcher.php:71` | none [code: app/bundles/LeadBundle/LeadEvents.php:50 @7.x] |
| `CHANNEL_SUBSCRIPTION_CHANGED` | `ChannelSubscriptionChange` | `LeadChangeEventDispatcher.php:85` | Webhook [code: app/bundles/LeadBundle/LeadEvents.php:150 @7.x] |
| `LEAD_COMPANY_CHANGE` | `LeadChangeCompanyEvent` | `CompanyModel.php:395,507` | secondary-company removal, Webhook, Integrations [code: app/bundles/LeadBundle/LeadEvents.php:60 @7.x] |
| `LEAD_PRE_MERGE` / `LEAD_POST_MERGE` | `LeadMergeEvent` | `ContactMerger.php:56,72` | Lead, Campaign, Point, Email, DynamicContent, Stage, Form, Page, Asset move history [code: app/bundles/LeadBundle/LeadEvents.php:120-130 @7.x] |
| `CURRENT_LEAD_CHANGED` | `LeadChangeEvent` | `ContactTracker.php:330` | Page, Asset [code: app/bundles/LeadBundle/LeadEvents.php:181 @7.x] |
| `ON_CLICKTHROUGH_IDENTIFICATION` | `ContactIdentificationEvent` | `ContactRequestHelper.php:157` | Email, Sms `TrackingSubscriber` [code: app/bundles/LeadBundle/LeadEvents.php:788 @7.x] |
| `TIMELINE_ON_GENERATE` | `LeadTimelineEvent` | `LeadModel.php:2189` | most bundles [code: app/bundles/LeadBundle/LeadEvents.php:291 @7.x] |
| `FIELD_PRE/POST_SAVE`, `FIELD_PRE/POST_DELETE` | `LeadFieldEvent` | `FieldModel.php:860-869`; `Field/Dispatcher/*` | segment dependency check, audit, form cache [code: app/bundles/LeadBundle/LeadEvents.php:251-281 @7.x] |
| `LEAD_FIELD_PRE_{ADD,UPDATE,DELETE}_COLUMN[_BACKGROUND_JOB]` | `AddColumnEvent` etc. | `Field/Dispatcher/FieldColumnDispatcher.php:34-69` | none [code: app/bundles/LeadBundle/LeadEvents.php:798-881 @7.x] |
| `NOTE_*`, `IMPORT_*`, `TAG_*`, `DEVICE_*` | `LeadNoteEvent`, `ImportEvent`, ... | `NoteModel.php:87-96`; `ImportModel.php:325,596-630`; `TagModel.php:123-169` | import subscribers; audit for notes [code: app/bundles/LeadBundle/LeadEvents.php:301-519 @7.x] |
| `COMPANY_PRE/POST_SAVE`, `PRE/POST_DELETE`, `COMPANY_SOFT_DELETE`, `COMPANY_PRE/POST_MERGE` | `CompanyEvent`, `CompanyMergeEvent` | `CompanyModel.php:640-720` | `CompanySubscriber` (rename propagation, soft-delete cleanup, audit) [code: app/bundles/LeadBundle/LeadEvents.php:597-653 @7.x] |
| `ADD_DONOT_CONTACT` / `REMOVE_DONOT_CONTACT` | `DoNotContactAddEvent` / `DoNotContactRemoveEvent` | other bundles | `DoNotContactSubscriber` [code: app/bundles/LeadBundle/EventListener/DoNotContactSubscriber.php:19-58 @7.x] |
| `LeadGetCurrentEvent` (by class) | | `ContactTracker::getCurrentContact()` | supply current contact [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:191-212 @7.x] |

In 8.x all of these are dispatched by event class; see version-notes.md.

## 4. Controllers, routes and API endpoints

UI routes in `app/bundles/LeadBundle/Config/config.php:7-153`: `mautic_contact_index` `/contacts/{page}`,
`mautic_contact_action` `/contacts/{objectAction}/{objectId}`, `mautic_contactfield_*` `/contacts/fields/...`,
`mautic_contactnote_*`, `mautic_import_*` `/{object}/import/...`, `mautic_company_*`, timeline/audit-log/export routes. [code: app/bundles/LeadBundle/Config/config.php:7-153 @7.x]

Controllers: `LeadController` (index `:146`, view `:372`, edit `:739`, merge `:940`, batchDnc `:1744`, batchExport `:2206`),
`CompanyController` (merge `:1133`), `FieldController`, `ImportController`, `NoteController`, `AjaxController`
(`removeBounceStatus` `:420`, `addLeadUtmTags` `:633` deprecated, `setAsPrimaryCompany` `:778`). [code: app/bundles/LeadBundle/Controller/LeadController.php @7.x] [code: app/bundles/LeadBundle/Controller/AjaxController.php:420-778 @7.x]

API routes (`app/bundles/LeadBundle/Config/config.php:154-293`): [code: app/bundles/LeadBundle/Config/config.php:154-293 @7.x]

| Path | Verbs | Controller action |
|---|---|---|
| `/api/contacts`, `/{id}`, `/new`, `/batch/new`, `/{id}/edit`, `/batch/edit`, `/{id}/delete`, `/batch/delete` | standard | `LeadApiController` |
| `/api/contacts/{id}/dnc/{channel}/add`, `/remove` | POST | `addDncAction`, `removeDncAction` |
| `/api/contacts/{id}/activity`, `/api/contacts/activity` | GET | activity |
| `/api/contacts/{id}/notes`, `devices`, `campaigns`, `segments`, `companies` | GET | sub-resources |
| `/api/contacts/{id}/utm/add`, `/{id}/utm/{utmid}/remove` | POST | UTM |
| `/api/contacts/list/owners`, `list/fields`, `list/segments` | GET | lookups |
| `/api/companies` (standard), `/companies/{companyId}/contact/{contactId}/add`, `/remove` | standard, POST | `CompanyApiController` |
| `/api/companies/batch/addcontacts` (7.x after 7.2.1, unreleased; [PR #16512]) | POST | `batchAddContactsAction` |
| `/api/fields/{object}` (`contact` or `company`) | standard | `FieldApiController` |
| `/api/notes`, `/api/devices`, `/api/tags` | standard | |

API controller helpers: `app/bundles/LeadBundle/Controller/Api/CustomFieldsApiControllerTrait.php` (defaults, overwriteWithBlank, number casting). [code: app/bundles/LeadBundle/Controller/Api/CustomFieldsApiControllerTrait.php:35-210 @7.x]

Twig views: `app/bundles/LeadBundle/Resources/views/`. [code: app/bundles/LeadBundle/Resources/views @7.x]

## 5. Console commands

| Command | Options | Purpose | Source |
|---|---|---|---|
| `mautic:import` | `--id`, `--limit` | process queued/delayed imports; run from cron | [code: app/bundles/LeadBundle/Command/ImportCommand.php:35-135 @7.x] |
| `mautic:contacts:deduplicate` | `--newer-into-older`, `--batch` (100), `--processes` (1) | merge duplicates on unique identifiers; FAILURE when none | [code: app/bundles/LeadBundle/Command/DeduplicateCommand.php:30-115 @7.x] |
| `mautic:contacts:deduplicate:ids` | `--contact-ids`, `--newer-into-older` | worker for the above | [code: app/bundles/LeadBundle/Command/DeduplicateIdsCommand.php:27 @7.x] |
| `mautic:custom-field:create-column` | `--id`, `--user` | create pending columns (background mode) | [code: app/bundles/LeadBundle/Field/Command/CreateCustomFieldCommand.php:36-87 @7.x] |
| `mautic:custom-field:update-column`, `mautic:custom-field:delete-column` | `--id` (required), `--user` | background update/delete | [code: app/bundles/LeadBundle/Field/Command/UpdateCustomFieldCommand.php:21 @7.x] [code: app/bundles/LeadBundle/Field/Command/DeleteCustomFieldCommand.php:22 @7.x] |
| `mautic:fields:analyse` | `-t` | column usage report | [code: app/bundles/LeadBundle/Field/Command/AnalyseCustomFieldCommand.php:19 @7.x] |
| `mautic:fields:modify` | argument | change column sizes | [code: app/bundles/LeadBundle/Field/Command/ModifyCustomFieldCommand.php:17 @7.x] |
| `mautic:contacts:scheduled_export` | `--ids` | process queued exports | [code: app/bundles/LeadBundle/Command/ContactScheduledExportCommand.php:29-75 @7.x] |
| `mautic:contacts:cleanup_exported_files` | days | delete old export files | [code: app/bundles/LeadBundle/Command/CleanupExportedFilesCommand.php:22 @7.x] |
| `mautic:company:delete_company_leads` | `--id` | background soft-delete cleanup | [code: app/bundles/LeadBundle/Command/DeleteCompanyLeads.php:21 @7.x] |
| `mautic:company:update_lead_company` | `--id` | background rename propagation | [code: app/bundles/LeadBundle/Command/UpdateCompanyNameOnLeadsCommand.php:21 @7.x] |
| `mautic:contact:delete:secondary-companies` | — | remove secondary companies when multiple disallowed | [code: app/bundles/LeadBundle/Command/DeleteContactSecondaryCompaniesCommand.php:28 @7.x] |

The company docs name the option `--company-id`; the code analysis records `--id|-i`. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#processing-company-updates-in-the-background] [code: app/bundles/LeadBundle/Command/DeleteCompanyLeads.php:21 @7.x]

## 6. Configuration parameters (`app/bundles/LeadBundle/Config/config.php:336-374`)

| Parameter | Default | Effect |
|---|---|---|
| `parallel_import_limit` | 1 | max IN_PROGRESS imports |
| `background_import_if_more_rows_than` | 0 | browser vs background threshold |
| `contact_api_count_cache_ttl` | 5 | API list count cache (s) |
| `create_custom_field_in_background` | false | defer column changes to commands |
| `contact_unique_identifiers_operator` / `company_unique_identifiers_operator` | OR | combine unique identifiers |
| `contact_export_in_background` | true | schedule CSV exports |
| `contact_export_limit` | 0 | max exportable contacts (0 = none) |
| `contact_export_batch_size` | 20000 | |
| `contact_export_dir` | `%mautic.application_dir%/media/files/temp` | |
| `clear_export_files_after_days` | 7 | |
| `contact_allow_multiple_companies` | true | false removes secondary companies |
| `update_company_mapping_data_in_background` | false | defer company rename/delete propagation |
| `import_leads_dir` | `%kernel.project_dir%/var/import` | |
| `contact_columns`, `company_columns` | list columns | |

[code: app/bundles/LeadBundle/Config/config.php:336-374 @7.x]
Consumed from other bundles: `track_contact_by_ip` (false) [code: app/bundles/PageBundle/Config/config.php:96 @7.x], `ip_lookup_create_organization` (false) [code: app/bundles/CoreBundle/Config/config.php:294 @7.x], `api_batch_max_limit` (200) [code: app/bundles/ApiBundle/Config/config.php:67 @7.x].

## 7. Permissions (`app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php`)

| Key | Levels | Use |
|---|---|---|
| `lead:leads` | viewown, viewother, editown, editother, create, deleteown, deleteother, full | contacts and companies |
| `lead:notes` | same extended set | notes (own = note creator) |
| `lead:lists` | extended + publish | segments |
| `lead:fields` | view, full (publish = full) | custom fields |
| `lead:imports` | standard | imports |
| `lead:export` | enable | exports |

[code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php @7.x] The mautic-users-and-permissions skill covers the permission framework.

## 8. Extension points

- Listen to `LEAD_POST_SAVE` and use `$event->getChanges()` for diffs. [code: app/bundles/LeadBundle/EventListener/LeadSubscriber.php:77 @7.x]
- Implement `LEAD_POST_MERGE` (`LeadMergeEvent::getLoser()/getVictor()`) to move plugin rows keyed by contact id. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:72 @7.x]
- `TIMELINE_ON_GENERATE` to add timeline event types. [code: app/bundles/LeadBundle/Model/LeadModel.php:2189 @7.x]
- `ON_CLICKTHROUGH_IDENTIFICATION` to identify contacts from a channel's `ct` payload. [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:157 @7.x]
- `LeadGetCurrentEvent` to supply the current contact. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:191-197 @7.x]
- `IMPORT_ON_INITIALIZE`, `ON_FIELD_MAPPING`, `ON_VALIDATE`, `ON_PROCESS` to add import objects (see `ImportContactSubscriber`, `ImportCompanySubscriber`). [code: app/bundles/LeadBundle/LeadEvents.php:381-409 @7.x]
- `LEAD_FIELD_PRE_*_COLUMN` to intercept schema changes. [code: app/bundles/LeadBundle/Field/Dispatcher/FieldColumnDispatcher.php:29-69 @7.x]
- `LEAD_BUILD_SEARCH_COMMANDS` to add search commands. [code: app/bundles/LeadBundle/Entity/LeadRepository.php:998 @7.x]
- Dispatch `DoNotContactAddEvent`/`DoNotContactRemoveEvent` or call the `DoNotContact` model to change DNC from another bundle. [code: app/bundles/LeadBundle/EventListener/DoNotContactSubscriber.php:19-58 @7.x]
- Campaign actions and conditions of this bundle are registered in `app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:105-271`. [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:105-271 @7.x]

## 9. Tests

`app/bundles/LeadBundle/Tests/` (about 195 non-segment test files). Functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`; unit tests extend PHPUnit `TestCase`. Helpers: `Tests/StandardImportTestHelper.php`, `Tests/TestEntityCreationTrait.php`, `Tests/Traits/LeadFieldTestTrait.php`, `Tests/Fixtures`, `Tests/DataFixtures`. [code: app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php:32 @7.x] See test-patterns.md.

## 10. Deprecations (7.x)

| Item | Since | Source |
|---|---|---|
| `LeadModel::isContactable()` | 2.12 | [code: app/bundles/LeadBundle/Model/LeadModel.php:2437 @7.x] |
| `FieldModel::getFieldList()` | — | [code: app/bundles/LeadBundle/Model/FieldModel.php:889 @7.x] |
| `CustomFieldHelper::fieldValueTransfomer` | — | [code: app/bundles/LeadBundle/Helper/CustomFieldHelper.php:45 @7.x] |
| `FieldDeleteDispatcher` pre-delete helper | — | [code: app/bundles/LeadBundle/Field/Dispatcher/FieldDeleteDispatcher.php:26 @7.x] |
| `AjaxController::addLeadUtmTagsAction` | 7.2 | [code: app/bundles/LeadBundle/Controller/AjaxController.php:631 @7.x] |
| `LeadEvents::FILTER_CHOICE_FIELDS` | — | [code: app/bundles/LeadBundle/LeadEvents.php:532 @7.x] |
| `GET /api/contacts/{id}/events` | — (use `/activity`) | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#get-contact-s-events] |
