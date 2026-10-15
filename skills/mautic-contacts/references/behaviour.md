# Contacts behaviour specification (Mautic 7.x)

Authoritative for Mautic 7.x at commit 419a08a9b35 (release 7.2.1 plus unreleased merged PRs). Every item carries a source tag. Code wins over docs for
current behaviour; where they disagree the item says so and the discrepancy is listed in section 16.
Paths are from the repository root. "Contact" is the docs term for the `Lead` entity (table `leads`).

## Table of contents
1. Glossary
2. Identification: anonymous versus identified
3. Web tracking identity (cookies, devices, current contact)
4. Field values: writing, coercion and defaults
5. Unique identifiers and duplicate detection
6. Merging contacts
7. Companies and the primary company
8. Owner assignment
9. Tags and UTM tags
10. Do Not Contact (DNC)
11. REST API create/edit semantics
12. Custom fields (schema)
13. Import
14. Frequency rules, preferences, notes, timeline, audit log, export, deletion
15. Points (contact-side storage only)
16. Contradictions and open questions

---

## 1. Glossary

- **Contact**: a person record, table `leads`, entity `Mautic\LeadBundle\Entity\Lead`. [code: app/bundles/LeadBundle/Entity/Lead.php:294-310 @7.x]
- **Visitor / anonymous Contact**: a tracked web visitor not yet identified; hidden from the Contacts list by default. [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#contact-types]
- **Company**: an organisation record, table `companies`; contacts link to companies through `companies_leads` with one primary. [code: app/bundles/LeadBundle/Entity/Company.php:51 @7.x] [code: app/bundles/LeadBundle/Entity/CompanyLead.php:12-53 @7.x]
- **Custom field**: a contact or company field whose definition is a `lead_fields` row and whose value is a physical column on `leads` or `companies`. [code: app/bundles/LeadBundle/Entity/LeadField.php:217-305 @7.x]
- **Unique identifier**: a field flagged `is_unique_identifer` (sic) used to find existing records; contact `email` and company `companyname` by default. [code: app/bundles/LeadBundle/Model/FieldModel.php:88 @7.x] [code: app/bundles/LeadBundle/Model/FieldModel.php:268 @7.x]
- **DNC (Do Not Contact)**: a per-channel opt-out row in `lead_donotcontact` with a reason. [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-32 @7.x]
- **Channel**: a communication medium named by a string such as `email` or `sms`. [code: app/bundles/LeadBundle/Model/DoNotContact.php:179-198 @7.x]
- **Frequency rule**: a per-channel cap on how many messages a contact receives per period, with optional pause dates and a preferred channel. [code: app/bundles/LeadBundle/Entity/FrequencyRule.php:66-98 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/frequency_rules.html]
- **Manipulator**: the `LeadManipulator` recording which bundle/object created or identified a contact. [code: app/bundles/LeadBundle/Model/LeadModel.php:2383-2406 @7.x]

## 2. Identification: anonymous versus identified

B2.1 A contact is anonymous unless firstname, lastname, company, email or any social field has a value. Phone, mobile and other custom fields do not identify a contact. [code: app/bundles/LeadBundle/Entity/Lead.php:1165-1174 @7.x]

B2.2 `date_identified` is set to now in a pre-persist/pre-update callback the first time a contact with a null `date_identified` becomes non-anonymous. The callback never clears it. [code: app/bundles/LeadBundle/Entity/Lead.php:300-301 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:1176-1179 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:1420-1426 @7.x]

B2.3 When `dateIdentified` changes on save, `LEAD_IDENTIFIED` (`mautic.lead_identified`) is dispatched and an audit-log entry with action `identified` is written. [code: app/bundles/LeadBundle/EventListener/LeadSubscriber.php:138-161 @7.x] [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:33-40 @7.x]

B2.4 The `mautic.lead_post_save_new` webhook fires when a contact has just been identified; otherwise `mautic.lead_post_save_update` fires. Saves of anonymous contacts trigger neither webhook. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:131-158 @7.x]

B2.5 A `lead_event_log` row `created_contact` or `identified_contact` is written once, only when the contact is new or is becoming identified. [code: app/bundles/LeadBundle/Model/LeadModel.php:2383-2406 @7.x]

B2.6 The Contacts list hides anonymous contacts (`!is:anonymous`) unless the search contains `is:anonymous`. `is:anonymous` means `date_identified IS NULL`. [code: app/bundles/LeadBundle/Controller/LeadController.php:192-206 @7.x] [code: app/bundles/LeadBundle/Entity/LeadRepository.php:757-760 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]

B2.7 Maintenance cleanup deletes contacts with `last_active` on or before the cutoff and a null `date_identified`. In GDPR mode it also deletes those with `date_added` on or before the cutoff and a null `last_active`. It uses raw DBAL deletes in loops of 10000 ids, so no `LEAD_*_DELETE` events or audit entries are produced. [code: app/bundles/LeadBundle/EventListener/MaintenanceSubscriber.php:26-83 @7.x]

## 3. Web tracking identity

B3.1 No contact is tracked when the request has a `Blocked-Tracking` cookie, when a Mautic user is logged in, or in a console or no-request context. In those cases the "system contact" is used. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-60 @7.x] [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:173-189 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#website-monitoring]

B3.2 The current contact is resolved in this order: a `LeadGetCurrentEvent` listener; the tracked device (`mautic_device_id` cookie or request parameter); the legacy cookie (`{trackingId}` or `mtc_id`); the newest contact with the same IP if `track_contact_by_ip` is on; otherwise a new contact. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:191-267 @7.x] [code: app/bundles/LeadBundle/Tracker/Service/ContactTrackingService/ContactTrackingService.php:29-70 @7.x]

B3.3 The legacy-cookie lookup follows merge records. It returns null if the contact already has a tracked device. [code: app/bundles/LeadBundle/Tracker/Service/ContactTrackingService/ContactTrackingService.php:53-69 @7.x]

B3.4 Non-trackable requests (bots, privacy signals, prefetch, non-trackable IP) get a new Lead that is never persisted. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:246-253 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]

B3.5 A new tracked contact is saved directly through the repository. `LEAD_PRE_SAVE` and `LEAD_POST_SAVE` are dispatched manually and default field values are applied. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:269-293 @7.x]

B3.6 Cookies: `mautic_device_id` lasts 1 year with SameSite=None; `mtc_id` is a session cookie holding the contact id. Device tracking ids are random 23-character strings, unique in `lead_devices`. [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:119-136 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#cookies-used-by-mautic]

B3.7 `setTrackedContact()` with an unsaved contact clears the tracking cookies. Switching to a different saved contact dispatches `CURRENT_LEAD_CHANGED`, but only if a previous tracking id existed. Page and Asset listeners then move hits and downloads to the new contact. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:83-124 @7.x] [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:320-333 @7.x]

B3.8 `last_active` is updated once per request for the tracked contact with a direct query. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:71-75 @7.x]

B3.9 Tracking requests can identify a contact from a `ct` clickthrough (Email and SMS listeners on `ON_CLICKTHROUGH_IDENTIFICATION`) or from query fields. Only published fields with `is_publicly_updatable = 1` are applied, and an existing contact is found only through unique-identifier fields. [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:97-157 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:875-930 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#updating-contact-fields]

B3.10 On a clickthrough identification, an anonymous tracked contact is merged with the identified contact and the tracked contact is the winner (its id survives). Field data still follows the newest-value rule of B6.3. [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:154-166 @7.x] [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:205-216 @7.x]

B3.11 A `tags` query parameter on a tracking request is applied with `modifyTags`, so a `-` prefix removes a tag. [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:193-195 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tags]

B3.12 "Identify visitors by tracking URL" requires email to be a unique identifier and publicly editable; the docs do not recommend it because it can be spoofed. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#identify-visitors-by-tracking-url]

B3.13 Traffic from private IP ranges is not tracked unless `track_private_ip_ranges` is true. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#website-monitoring]

## 4. Field values: writing, coercion and defaults

B4.1 Every field write goes through `addUpdatedField()`. `id` cannot be set. Strings are trimmed and an empty string becomes null. Arrays are joined with `|`. A change is recorded only if the value really changed; null and '' are treated as equal. [code: app/bundles/LeadBundle/Entity/CustomFieldEntityTrait.php:106-157 @7.x]

B4.2 Type coercion on write and compare: number becomes float (numeric or '' only), boolean becomes bool, select becomes string, null is never transformed. [code: app/bundles/LeadBundle/Helper/CustomFieldHelper.php:29-42 @7.x]

B4.3 Booleans are stored as integers 0/1. [code: app/bundles/LeadBundle/Entity/CustomFieldRepositoryTrait.php:398-406 @7.x]

B4.4 Request and import cleaning: booleans via `InputHelper::boolean`; date, datetime and time parsed with `strtotime` and normalised, with zero placeholders such as `0000-00-00` dropped; multiselect strings split on `|`; numbers cast to float; email via `InputHelper::email`; nulls left alone. [code: app/bundles/CoreBundle/Form/RequestTrait.php:175-238 @7.x]

B4.5 Date values set from campaigns or segment values are converted from local time to UTC strings (`Y-m-d H:i:s`, `Y-m-d`, `H:i:s`). [code: app/bundles/LeadBundle/Helper/CustomFieldHelper.php:62-95 @7.x]

B4.6 On every contact save, a `select` field value that is not in the field's option list is reset to null. [code: app/bundles/LeadBundle/Model/LeadModel.php:2518-2544 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:497 @7.x]

B4.7 `setFieldValues()` only touches aliases present in the data. Blank incoming values are ignored unless `$overwriteWithBlank` is true. [code: app/bundles/LeadBundle/Model/LeadModel.php:651-673 @7.x]

B4.8 `setFieldValues()` with `stage` changes the stage only when it differs. An unknown stage id or name throws `ImportFailedException`. [code: app/bundles/LeadBundle/Model/LeadModel.php:571-594 @7.x]

B4.9 With `bindWithForm`, values are validated through the Lead form and invalid fields are silently dropped (logged at debug level). [code: app/bundles/LeadBundle/Model/LeadModel.php:617-646 @7.x]

B4.10 For a new contact, every field with a non-empty default value and an empty current value receives the default on save. [code: app/bundles/LeadBundle/Model/DefaultValueTrait.php @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:501 @7.x]

B4.11 Custom-field columns not mapped in Doctrine are written with a DBAL `UPDATE leads SET ...` after the ORM flush. Fields already persisted through a property setter are excluded, and `points` is never written this way. [code: app/bundles/LeadBundle/Entity/CustomFieldRepositoryTrait.php:267-293 @7.x] [code: app/bundles/LeadBundle/Entity/LeadRepository.php:1429-1435 @7.x]

B4.12 The Doctrine-mapped (fixed) contact columns are title, firstname, lastname, company, position, email, phone, mobile, address1, address2, city, state, zipcode, timezone and country. Every other field is a dynamic column. [code: app/bundles/LeadBundle/Entity/Lead.php:451-470 @7.x]

B4.13 IP geolocation fills city, state, country and zipcode on save only if all four are empty and the contact is not being imported. With `ip_lookup_create_organization`, the IP organisation may fill an empty `company`. [code: app/bundles/LeadBundle/Model/LeadModel.php:460-489 @7.x]

B4.14 `attribution_date` is set to today when `attribution` has a value and no date, and cleared when `attribution` is empty. [code: app/bundles/LeadBundle/Entity/Lead.php:1405-1416 @7.x]

B4.15 Since Mautic 5 the UI does not allow editing the default value of identifying fields (email, company, first name, last name, social profiles, unique identifiers, company name, company email, company website, state, country, city). [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#custom-fields]

## 5. Unique identifiers and duplicate detection

B5.1 Duplicate lookup uses only published contact fields flagged as unique identifiers (email by default) that have a non-empty value after cleaning. [code: app/bundles/LeadBundle/Model/LeadModel.php:875-930 @7.x] [code: app/bundles/LeadBundle/Field/FieldsWithUniqueIdentifier.php @7.x]

B5.2 Several unique-identifier fields are combined with OR by default; AND when `contact_unique_identifiers_operator` is `and`. Companies use `company_unique_identifiers_operator`, also OR by default. [code: app/bundles/LeadBundle/Config/config.php:360-361 @7.x] [code: app/bundles/LeadBundle/Entity/CustomFieldRepositoryTrait.php:454-461 @7.x] The user docs state AND is the default; see section 16. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#managing-duplicates]

B5.3 When several contacts match, the newest (`date_added DESC, id DESC`) is used. [code: app/bundles/LeadBundle/Entity/LeadRepository.php:245-256 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:921-926 @7.x]

B5.4 Marking a field unique forces an index, and its column is stored as varchar(191) whatever the field type. [code: app/bundles/LeadBundle/Entity/LeadField.php:677-686 @7.x] [code: app/bundles/LeadBundle/Field/SchemaDefinition.php:17-23 @7.x]

B5.5 Unique identifiers are not enforced by database unique constraints. Duplicates can exist; `mautic:contacts:deduplicate` merges them. [code: app/bundles/LeadBundle/Field/CustomFieldColumn.php:112-114 @7.x] [code: app/bundles/LeadBundle/Command/DeduplicateCommand.php:30-115 @7.x] The UI only warns when a contact with the same unique identifier exists. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#managing-duplicates]

B5.6 A form submission carrying an email merges into the contact with that email even if the cookie or IP matches another contact. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#managing-duplicates]

## 6. Merging contacts

B6.1 `ContactMerger::merge(winner, loser)` throws `SameContactException` for the same id; dispatches `LEAD_PRE_MERGE`; records merge history; merges timestamps, IPs, fields, owner, points, tags and companies; saves the winner; dispatches `LEAD_POST_MERGE`; and deletes the loser through `LeadModel::deleteEntity`, so the delete events fire. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:46-78 @7.x]

B6.2 Merge records: rows pointing at the loser move to the winner, and a new `contact_merge_records` row (winner id, loser id, loser primary identifier) is written. `LeadModel::getEntity()`/`getEntities()`, the API and the legacy cookie lookup resolve a merged (deleted) id to the winner, through chains of merges. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:276-291 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:303-355 @7.x]

B6.3 Field values: the contact modified (or, if never modified, added) most recently is "newest". For each field the newest non-empty value wins, otherwise the older non-empty value. If the newest contact is anonymous and its value equals the field default, the older value wins. `id` and `points` are skipped. This is independent of which contact is the winner. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:119-172 @7.x] [code: app/bundles/LeadBundle/Deduplicate/Helper/MergeValueHelper.php @7.x] The user docs say the merged contact's values only fill empty fields on the kept contact; see section 16. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#merge-two-contacts]

B6.4 `last_active` keeps the most recent value; `date_identified` keeps the oldest non-null value. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:80-98 @7.x]

B6.5 The winner keeps its owner and inherits the loser's owner only if it has none. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:177-189 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#merge-two-contacts]

B6.6 Points are summed. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:194-206 @7.x]

B6.7 Tags are unioned. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:211-219 @7.x]

B6.8 Companies: the loser's links are copied unless the winner already has that company. The winner keeps its primary company; it inherits the loser's primary only if it has none. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:224-271 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#merge-two-contacts]

B6.9 Segment membership (`lead_lists_leads`) and campaign membership (`campaign_leads`) of the loser move to the winner, except where the winner is already a member; those loser rows are deleted so the winner's own manual flags win. [code: app/bundles/LeadBundle/Entity/ListLeadRepository.php:18-53 @7.x] [code: app/bundles/CampaignBundle/Entity/LeadRepository.php:92-125 @7.x]

B6.10 History moved to the winner: lead event log, points change log, notes, devices, campaign event log, point and trigger logs, email and dynamic-content stats, stage log, form submissions, page and video hits, asset downloads. An audit-log `merge` entry is written for the loser id. [code: app/bundles/LeadBundle/EventListener/LeadSubscriber.php:273-312 @7.x]

B6.11 Not merged: the loser's DNC entries, frequency rules, UTM tags, stage and categories. They are removed with the loser by FK cascade (inferred: no code moves them). SMS and push-notification stats are not moved either: their repositories have `updateLead()` but no `LEAD_POST_MERGE` subscriber. [code: app/bundles/LeadBundle/Entity/Lead.php:336-343 @7.x] [code: app/bundles/SmsBundle/Entity/StatRepository.php:169 @7.x] [code: app/bundles/NotificationBundle/Entity/StatRepository.php:191 @7.x]

B6.12 Who wins depends on the caller:
- UI merge: the contact being viewed wins; the selected duplicate is deleted. [code: app/bundles/LeadBundle/Controller/LeadController.php:1064 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#merge-two-contacts]
- API edit with a unique-identifier match: the contact in the URL wins. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:614-628 @7.x]
- Form submission: the existing identified contact wins over the tracked anonymous one unless there is a unique-identifier conflict or kiosk mode. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1041-1060 @7.x]
- Clickthrough identification: the tracked contact wins (B3.10). [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:205-216 @7.x]
- `mautic:contacts:deduplicate`: older contacts are merged successively into the newest; `--newer-into-older` reverses this. [code: app/bundles/LeadBundle/Deduplicate/ContactDeduper.php:93-131 @7.x]

## 7. Companies and the primary company

B7.1 A contact can link to many companies through `companies_leads`, with exactly one flagged `is_primary`. The contact's `company` text field mirrors the primary company's name. [code: app/bundles/LeadBundle/Model/CompanyModel.php:378-389 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:2306-2348 @7.x]

B7.2 Adding companies resets all the contact's links to non-primary, makes the first newly added company primary, and writes its name to `leads.company`. [code: app/bundles/LeadBundle/Entity/CompanyLeadRepository.php:22-52 @7.x] [code: app/bundles/LeadBundle/Model/CompanyModel.php:343-389 @7.x] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#contact-profile]

B7.3 Adding a contact to a company it already belongs to is a no-op and dispatches no event. [code: app/bundles/LeadBundle/Model/CompanyModel.php:347-358 @7.x]

B7.4 Removing the primary company makes the first remaining company (as returned by an unordered query) primary, or empties `leads.company` if none remain. [code: app/bundles/LeadBundle/Model/CompanyModel.php:494-499 @7.x] [code: app/bundles/LeadBundle/Model/CompanyModel.php:952-985 @7.x] [code: app/bundles/LeadBundle/Entity/CompanyLeadRepository.php:54-76 @7.x]

B7.5 Setting the contact `company` field (UI, API, form or import) looks up a company by the company unique identifiers (companyname by default; contact city, state and country are mapped to company fields for the lookup), creates it if absent, links the contact and makes it primary. Emptying the field removes the primary flag. [code: app/bundles/LeadBundle/Model/LeadModel.php:491-517 @7.x] [code: app/bundles/LeadBundle/Helper/IdentifyCompanyHelper.php:11-117 @7.x]

B7.6 With `contact_allow_multiple_companies = false`, every `LEAD_COMPANY_CHANGE` removes the contact's secondary companies, and the UI offers a single company. [code: app/bundles/LeadBundle/EventListener/LeadSubscriber.php:451-458 @7.x] [code: app/bundles/LeadBundle/Form/Type/LeadType.php:117 @7.x]

B7.7 API `companies` on a contact is a full replacement list: listed companies are added and unlisted ones removed. [code: app/bundles/LeadBundle/Model/LeadModel.php:1882-1907 @7.x] [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:640-643 @7.x]

B7.8 Deleting a company is a soft delete (`deleted` set, `COMPANY_SOFT_DELETE` dispatched). Unless `update_company_mapping_data_in_background` is true, contacts get a new primary, links are deleted and the company is hard-deleted immediately. In background mode, `mautic:company:delete_company_leads` does that later. [code: app/bundles/LeadBundle/Model/CompanyModel.php:989-997 @7.x] [code: app/bundles/LeadBundle/EventListener/CompanySubscriber.php:73-91 @7.x] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#processing-company-updates-in-the-background]

B7.9 After a company hard delete, `leads.company` is set to NULL for every contact whose company text equals the deleted company's name, including contacts not linked to it. [code: app/bundles/LeadBundle/EventListener/CompanySubscriber.php:60-71 @7.x] [code: app/bundles/LeadBundle/EventListener/CompanySubscriber.php:104-114 @7.x]

B7.10 Renaming a company updates `leads.company` only for contacts where it is primary, synchronously unless background mode is on (then `mautic:company:update_lead_company`). [code: app/bundles/LeadBundle/EventListener/CompanySubscriber.php:92-102 @7.x] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#renaming-a-company]

B7.11 Company merge: empty fields of the remaining company are filled from the other, the owner is inherited if empty, all contacts are linked to the remaining company, `COMPANY_PRE/POST_MERGE` fire, and the other company is soft-deleted. [code: app/bundles/LeadBundle/Model/CompanyModel.php:675-726 @7.x] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#merging-companies]

B7.12 `POST /api/companies/new` returns the existing company when unique fields match; batch create returns 200 for such duplicates. [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:66-74 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#create-batch-companies]

B7.13 `POST /api/companies/batch/addcontacts` (7.x after 7.2.1, unreleased; [PR #16512]) takes `assignments: [{contactId, companyId}]` of positive integers, rejects batches larger than `api_batch_max_limit`, checks edit access per contact, and returns a per-pair status of 200, 403, 404 or 500 inside an overall 200. [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:121-153 @7.x] [code: app/bundles/LeadBundle/Model/BatchCompanyContactAssignmentModel.php:52-160 @7.x] [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/companies.html#batch-add-contacts-to-companies]

B7.14 Companies reuse the `lead:leads` permissions; the Companies menu needs `lead:leads:viewother`. [code: app/bundles/LeadBundle/Model/CompanyModel.php:135-139 @7.x]

B7.15 The "Change Company score" action needs an identified contact and changes the score of every company linked to that contact. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#company-scoring] [code: app/bundles/LeadBundle/Model/LeadModel.php:2353-2370 @7.x]

## 8. Owner assignment

B8.1 The owner FK is `ON DELETE SET NULL`. `disassociateOwner()` nulls the owner on all of a user's contacts. [code: app/bundles/LeadBundle/Entity/Lead.php:312-315 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:711-718 @7.x]

B8.2 For permissions, the "own" user of a contact is its owner, or its creator when it has no owner. [code: app/bundles/LeadBundle/Entity/Lead.php:662-665 @7.x]

B8.3 The UI list without `viewother` adds `is:mine`, which matches `owner_id = current user` only. The API list "own" filter matches owner = user OR (owner null AND creator = user). [code: app/bundles/LeadBundle/Controller/LeadController.php:208-210 @7.x] [code: app/bundles/LeadBundle/Entity/LeadRepository.php:762-764 @7.x] [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:137-164 @7.x]

B8.4 API: omitting `owner` keeps the current owner; supplying it sets it, with no permission check on the target user. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:597-600 @7.x] [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:645-649 @7.x]

B8.5 Import: a per-row `ownerusername` column overrides the import's default owner. [code: app/bundles/LeadBundle/Model/LeadModel.php:1491-1508 @7.x]

B8.6 The campaign "change owner" action uses `updateLeadOwner()`, which calls `FormModel::saveEntity` directly and skips the `LeadModel::saveEntity` extras (IP lookup, company identification, select validation, defaults). [code: app/bundles/LeadBundle/Model/LeadModel.php:2375-2381 @7.x] [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:395-409 @7.x]

## 9. Tags and UTM tags

B9.1 `modifyTags()` adds tags (creating missing ones), removes tags prefixed with `-`, accepts CSV strings, trims and HTML-decodes names, and ignores empty names. [code: app/bundles/LeadBundle/Model/LeadModel.php:1788-1874 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#edit-contact]

B9.2 API `tags` is additive (uses `modifyTags`); existing tags are kept even on PUT. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:584-595 @7.x] [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:657-659 @7.x]

B9.3 The UI contact form uses `setTags()`, which replaces the tag set and can delete orphan tags. [code: app/bundles/LeadBundle/Model/LeadModel.php:1641-1682 @7.x]

B9.4 The import tags column is split on `|`. [code: app/bundles/LeadBundle/Model/LeadModel.php:1510-1514 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#import-file-requirements]

B9.5 Tags need no pre-creation; the `lead_tags.tag` column is indexed but not unique in the schema. [docs: https://docs.mautic.org/en/7.2/contacts/tags.html#creating-tags] [code: app/bundles/LeadBundle/Entity/Tag.php:73-80 @7.x]

B9.6 Tag merge (`TagModel::tagMerge`) runs in a transaction. [code: app/bundles/LeadBundle/Model/TagModel.php:153-180 @7.x]

B9.7 UTM add through the API parses a `query` string into an array, maps `useragent`/`remotehost` synonyms, uses `lastActive` (ISO date) as the UTM date and the contact's last active time, and creates a device from the user agent. [code: app/bundles/LeadBundle/Model/LeadModel.php:1698-1760 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#add-utm-tags]

B9.8 UTM tags are only captured from values already in the URL; Mautic never adds them on inbound capture. Known contacts visiting a Mautic landing page or a page with the tracking script store URL UTM values automatically. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_overview.html#inbound-capture-recording-utm-data] [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_landing_pages.html]

B9.9 The "Record UTM Tags" form action reads UTM parameters from the landing-page URL at submission and falls back to the referrer URL. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_forms.html#add-utm-recording]

B9.10 Asset-download UTM values live on the download record, not on the contact; they do not feed the timeline, segment filters or campaign conditions. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_asset_downloads.html#how-asset-download-utm-works]

B9.11 Segment UTM filters match any value ever recorded on the contact, not only the latest. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_segment_filters.html#create-segment-filters]

B9.12 `LEAD_UTMTAGS_ADD` is dispatched after save when UTM tags are added; core has no listener. [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:71 @7.x]

## 10. Do Not Contact (DNC)

B10.1 Reasons: 0 contactable, 1 UNSUBSCRIBED, 2 BOUNCED, 3 MANUAL. DNC is per channel (a string, optionally with a channel id). [code: app/bundles/LeadBundle/Entity/DoNotContact.php:17-32 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#add-do-not-contact]

B10.2 `DoNotContact::isContactable()` returns the first non-zero reason found for the channel, else 0. [code: app/bundles/LeadBundle/Model/DoNotContact.php:153-172 @7.x]

B10.3 `addDncForContact()` creates an entry if the contact is contactable. If an entry with a different reason exists it is updated, but an UNSUBSCRIBED entry is overwritten only when `allowUnsubscribeOverride` is true. The same reason causes no change and returns false. [code: app/bundles/LeadBundle/Model/DoNotContact.php:79-140 @7.x]

B10.4 `DoNotContactAddEvent` defaults `override = true`, so event-based adds (for example an import `doNotEmail`) can turn an unsubscribe into the event's reason. [code: app/bundles/LeadBundle/Event/DoNotContactAddEvent.php:15-24 @7.x] [code: app/bundles/LeadBundle/EventListener/DoNotContactSubscriber.php:36-57 @7.x]

B10.5 `removeDncForContact()` removes the first entry for the channel, optionally only one with a matching reason. [code: app/bundles/LeadBundle/Model/DoNotContact.php:31-62 @7.x]

B10.6 DNC changes are persisted by saving the contact, so `CHANNEL_SUBSCRIPTION_CHANGED` fires per changed channel (old reason to new reason) and the change appears in the audit log. [code: app/bundles/LeadBundle/Entity/Lead.php:1087-1108 @7.x] [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:74-87 @7.x]

B10.7 `POST /api/contacts/{id}/dnc/{channel}/add` needs edit access. `reason` defaults to 3 (manual); 0 is rejected with 400; `channelId` and `comments` are optional. The response holds the full contact. Remove returns `recordFound`. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:450-513 @7.x] [code: app/bundles/LeadBundle/Tests/Controller/Api/LeadApiControllerFunctionalTest.php:1232-1272 @7.x]

B10.8 Contact create/edit through the API accepts `doNotContact: [{channel (default email), reason (default manual), comments}]`; reason 0 removes DNC. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:669-689 @7.x]

B10.9 The UI batch "Set Do Not Contact" adds a MANUAL email DNC to each selected contact the user can edit. [code: app/bundles/LeadBundle/Controller/LeadController.php:1768-1776 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#batch-changes]

B10.10 The campaign "add DNC" action uses reason MANUAL with the configured text as comments and does not override an unsubscribe. [code: app/bundles/LeadBundle/EventListener/CampaignActionDNCSubscriber.php:57-78 @7.x]

B10.11 Import `doNotEmail` is honoured only when the row has an email value; true adds MANUAL, false removes. The docs call this a "Manual Unsubscription". [code: app/bundles/LeadBundle/Model/LeadModel.php:1471-1489 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#faq]

B10.12 Unchecking a channel in the contact preferences sets DNC for that channel only. [docs: https://docs.mautic.org/en/7.2/contacts/preference_center.html#preferred-channels-and-frequency]

## 11. REST API create/edit semantics

B11.1 `POST /api/contacts/new` looks up an existing contact by unique identifiers. If one is found it is updated (200) instead of a new one being created (201). Only `lead:leads:create` is checked. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:579-582 @7.x] [code: app/bundles/ApiBundle/Controller/CommonApiController.php:338-347 @7.x] [code: app/bundles/ApiBundle/Controller/CommonApiController.php:465-483 @7.x]

B11.2 `PATCH /api/contacts/{id}/edit` returns 404 if the contact does not exist; `PUT` creates it (needs create permission). [code: app/bundles/ApiBundle/Controller/CommonApiController.php:243-265 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#edit-contact]

B11.3 On edit, if the payload's unique identifiers match another contact, that contact is merged into the URL contact. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:616-628 @7.x]

B11.4 `overwriteWithBlank`: PUT writes blanks; POST and PATCH do not unless the payload has a truthy `overwriteWithBlank`. On POST/PATCH, numeric 0 values are dropped from the payload. [code: app/bundles/LeadBundle/Controller/Api/CustomFieldsApiControllerTrait.php:175-210 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#create-contact]

B11.5 On POST/PUT, fields missing from the payload and empty on the entity receive the field default. [code: app/bundles/LeadBundle/Controller/Api/CustomFieldsApiControllerTrait.php:35-60 @7.x]

B11.6 An empty or 0 `points` value is ignored on POST/PATCH so accumulated points are not overwritten. [code: app/bundles/LeadBundle/Controller/Api/CustomFieldsApiControllerTrait.php:183-187 @7.x]

B11.7 Number fields in responses are cast to int (no scale) or float (scale set). `fields.all` is a flat alias-to-value map; the other keys group fields by core, social, personal and professional. [code: app/bundles/LeadBundle/Controller/Api/CustomFieldsApiControllerTrait.php:62-120 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#get-contact]

B11.8 Batch endpoints reject more than `api_batch_max_limit` (default 200) items with 400. Batch new returns an overall 201 with per-item `statusCodes` (201 created, 200 existing, 403); batch edit returns an overall 200 with per-item 200/201/403/404. [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:730-733 @7.x] [code: app/bundles/ApiBundle/Controller/CommonApiController.php:169-333 @7.x] [code: app/bundles/ApiBundle/Config/config.php:67 @7.x]

B11.9 API saves set a `LeadManipulator('lead', 'api-single'|'api-batch', null, <user name>)`. [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:630-637 @7.x]

B11.10 The payload may carry `ipAddress` (added to the contact) and `lastActive` (UTC). [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:661-675 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#create-contact]

B11.11 The total count of `GET /api/contacts` is cached for `contact_api_count_cache_ttl` seconds (default 5). [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:117-120 @7.x]

B11.12 `GET /api/contacts` supports `where[n][col|expr|val]`, `order` and `select` (field aliases; `id` mandatory) in addition to `search`, `start`, `limit` (default 30), `orderBy` (snake_case), `orderByDir`, `publishedOnly` and `minimal`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#advanced-filtering]

B11.13 Merged (deleted) contact ids requested on single endpoints resolve to the winner. [code: app/bundles/LeadBundle/Model/LeadModel.php:303-321 @7.x]

B11.14 Notes: `/api/notes` evaluates own/other against the note creator; `GET /api/contacts/{id}/notes` evaluates against the contact owner; creating a note needs `lead:notes:create` plus view access to the contact. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/notes.html#permissions] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html#list-contact-notes]

## 12. Custom fields (schema)

B12.1 Creating a contact or company field runs `ALTER TABLE` immediately, unless `create_custom_field_in_background` is true. In that case the field is saved with `column_is_not_created`, stays unpublished, the API returns 202, and `mautic:custom-field:create-column` creates the column later. [code: app/bundles/LeadBundle/Model/FieldModel.php:627-633 @7.x] [code: app/bundles/LeadBundle/Field/CustomFieldColumn.php:41-77 @7.x] [code: app/bundles/LeadBundle/Controller/Api/FieldApiController.php:82-93 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#creating-custom-fields-via-a-command]

B12.2 In background mode, deleting a field hides it until `mautic:custom-field:delete-column` drops the column. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#creating-custom-fields-via-a-command] [code: app/bundles/LeadBundle/Field/Command/DeleteCustomFieldCommand.php:22 @7.x]

B12.3 A MySQL row-size overflow (error 1118) becomes a `CustomFieldLimitException` ("max columns"). [code: app/bundles/LeadBundle/Field/CustomFieldColumn.php:98-107 @7.x] `mautic:fields:analyse` (since 5.1) reports actual usage to help shrink VARCHAR columns. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#analyzing-custom-fields-to-optimize-tables]

B12.4 Column SQL type: unique identifier is always varchar(191); datetime, date, time and boolean map to the same type; number is `float`; timezone, locale, country, email, lookup, select, region, tel and url are varchar(length or 191); text is `text` if the alias contains "description", else varchar(length); multiselect is text(65535); html and other types are text. [code: app/bundles/LeadBundle/Field/SchemaDefinition.php:13-68 @7.x]

B12.5 The alias is generated from the label when empty, cleaned (prefixed `f_` if needed, max 25 characters) and suffixed with a number if taken. It cannot change for existing fields. Reserved aliases (contact_id, company_id, notes, owner, id, ip, tags, dateAdded, dateModified, lastActive, createdByUser, modifiedByUser) and segment filter keys are rejected. [code: app/bundles/LeadBundle/Helper/FieldAliasHelper.php:20-50 @7.x] [code: app/bundles/LeadBundle/Form/Validator/Constraints/FieldAliasKeywordValidator.php:20-71 @7.x]

B12.6 `time` fields are forced non-listable. [code: app/bundles/LeadBundle/Model/FieldModel.php:622-625 @7.x]

B12.7 Deleting a field used in any segment filter fails with a dependency error (API 409). Fixed fields cannot be deleted in the UI. [code: app/bundles/LeadBundle/Field/EventListener/LeadFieldSubscriber.php:33-52 @7.x] [code: app/bundles/LeadBundle/Model/FieldModel.php:671-689 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/fields.html#delete-field]

B12.8 Field changes are audit-logged (`object=field`), invalidate the `LeadField` result cache, and make FormBundle regenerate form caches. [code: app/bundles/LeadBundle/EventListener/LeadSubscriber.php:211-245 @7.x] [code: app/bundles/LeadBundle/Entity/LeadField.php:842 @7.x]

B12.9 The API accepts `isUniqueIdentifier` and maps it to the misspelled `is_unique_identifer` property. [code: app/bundles/LeadBundle/Controller/Api/FieldApiController.php:117-121 @7.x]

B12.10 `isPubliclyUpdatable` lets public requests such as the tracking pixel change the value. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/fields.html#get-field]

B12.11 Fields: listing needs `lead:fields:view` or `full`; any change needs `lead:fields:full`. [code: app/bundles/LeadBundle/Controller/FieldController.php:40-133 @7.x]

## 13. Import

B13.1 Imports with fewer rows than `background_import_if_more_rows_than` run in the browser (status MANUAL); others are queued (QUEUED) for `mautic:import`. With the default 0 the user picks each time. [code: app/bundles/LeadBundle/Controller/ImportController.php:400-433 @7.x] [code: app/bundles/LeadBundle/Controller/ImportController.php:525-537 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#automatic-import-type-configuration]

B13.2 A background import stays DELAYED while `parallel_import_limit` (default 1) imports are IN_PROGRESS. IN_PROGRESS imports older than 2 hours are marked FAILED at the start of each run. [code: app/bundles/LeadBundle/Model/ImportModel.php:121-186 @7.x] [code: app/bundles/LeadBundle/Entity/ImportRepository.php:26 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#import-job-status]

B13.3 Rows are processed in batches of `batchlimit` (form default 100) and progress is saved each batch. Unpublishing the import stops it (STOPPED). Unfinished imports are set DELAYED. The header row is skipped; rows with more values than headers, and empty rows, are ignored and logged. [code: app/bundles/LeadBundle/Model/ImportModel.php:258-421 @7.x] [code: app/bundles/LeadBundle/Form/Type/LeadImportType.php:98-103 @7.x]

B13.4 `mautic:import` runs as the import's `modifiedBy` user and fails if there is none. [code: app/bundles/LeadBundle/Command/ImportCommand.php:85-87 @7.x]

B13.5 Each row writes a `lead_event_log` row (`inserted`, `updated` or `failed`) linked to the import. [code: app/bundles/LeadBundle/Model/ImportModel.php:474-509 @7.x]

B13.6 Row matching: an `id` column matches by id; otherwise unique identifiers are used. With `create_new = false` ("Create new Contacts?" = No), unmatched rows fail and are listed as ignored. [code: app/bundles/LeadBundle/Model/LeadModel.php:1342-1350 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#create-new-contacts-or-update-only]

B13.7 Empty CSV cells never overwrite existing values. The literal `NULL` clears a value. With `skip_if_exists`, existing non-empty values are kept. [code: app/bundles/LeadBundle/Model/LeadModel.php:2553-2583 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:1544-1559 @7.x]

B13.8 Email-type fields are validated per row; invalid rows fail with the field messages. [code: app/bundles/LeadBundle/Model/LeadModel.php:1561-1585 @7.x]

B13.9 Special columns: dateAdded, dateModified, lastActive, dateIdentified (parsed and stored UTC), createdByUser, modifiedByUser, ip (CSV list), points, stage (created if missing), doNotEmail, ownerusername, tags. [code: app/bundles/LeadBundle/Model/LeadModel.php:1368-1514 @7.x]

B13.10 Company columns in a contact import create or update the company and link it as primary. [code: app/bundles/LeadBundle/Model/LeadModel.php:1336-1340 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:1621-1624 @7.x]

B13.11 Imported contacts are flagged `imported`, so IP geolocation and points-change events are skipped. Points are set only for new contacts and get a `PointsChangeLog` entry. [code: app/bundles/LeadBundle/Model/LeadModel.php:1418-1434 @7.x] [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:48-50 @7.x]

B13.12 Per-row permission: creating needs `lead:leads:create`; updating needs edit own/other. Creating an import without `lead:imports:publish` creates it unpublished. [code: app/bundles/LeadBundle/Model/LeadModel.php:1352-1366 @7.x] [code: app/bundles/LeadBundle/Controller/ImportController.php:419-422 @7.x]

B13.13 Boolean values `true`, `1`, `on` and `yes` are TRUE; CSV must be UTF-8; ISO 8601 dates are recommended. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#import-file-requirements]

## 14. Frequency rules, preferences, notes, timeline, audit log, export, deletion

B14.1 `setFrequencyRules()` writes one rule per preference channel (frequency number and period, pause dates, preferred channel), adds or removes segment membership from the preference form, and manages category subscriptions. [code: app/bundles/LeadBundle/Model/LeadModel.php:1106-1186 @7.x]

B14.2 Frequency rules exist for Email and SMS. Per-contact rules override the global configuration. A message over the limit is rescheduled and shown as a "Message Queue" timeline event. [docs: https://docs.mautic.org/en/7.2/contacts/frequency_rules.html#how-to-set-frequency-rules] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#history]

B14.3 An email with "Send to unsubscribed contacts" = Yes does not count toward frequency limits. [docs: https://docs.mautic.org/en/7.2/contacts/frequency_rules.html#emails-and-frequency-rules]

B14.4 Notes have types general, email, call and meeting, and an optional date. Their permission set `lead:notes` is separate from contact permissions; list and count with `viewown` show only own notes. [code: app/bundles/LeadBundle/Form/Type/NoteType.php:50-53 @7.x] [code: app/bundles/LeadBundle/Model/NoteModel.php:116-131 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#note-permissions]

B14.5 The contact audit log stores every non-trivial change set with action `create` or `update` (ignoring dateLastActive, dateModified, ipAddressList and manipulator), plus `identified` and `ipadded` entries. [code: app/bundles/LeadBundle/EventListener/LeadSubscriber.php:94-162 @7.x]

B14.6 The timeline is built by dispatching `TIMELINE_ON_GENERATE` to all bundles; the payload has events, types, total, page and maxPages. [code: app/bundles/LeadBundle/Model/LeadModel.php:2185-2204 @7.x]

B14.7 Contact export is refused (400) when the count exceeds `contact_export_limit` (0 = no limit). CSV exports are scheduled in the background by default (`contact_export_in_background` true) and processed by `mautic:contacts:scheduled_export`, which emails a download link. [code: app/bundles/LeadBundle/Controller/LeadController.php:2273-2289 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#exporting-contact-lists]

B14.8 Export needs admin or `lead:export:enable`. [code: app/bundles/LeadBundle/Controller/LeadController.php:2224 @7.x]

B14.9 Deleting a contact removes its avatar file, decrements cached segment counts (unless `update_segment_contact_count_in_background`), and writes a `delete` audit entry. [code: app/bundles/LeadBundle/Model/LeadModel.php:529-541 @7.x] [code: app/bundles/LeadBundle/EventListener/LeadSubscriber.php:167-205 @7.x]

B14.10 Contact edit, delete, merge, DNC and company assignment require `lead:leads:editown` or `editother` against `getPermissionUser()`. [code: app/bundles/LeadBundle/Model/LeadModel.php:792-795 @7.x] [code: app/bundles/LeadBundle/Controller/LeadController.php:1050-1053 @7.x]

## 15. Points (contact-side storage only)

See the mautic-points-and-stages skill for point actions, triggers and groups.

B15.1 Point adjustments are applied with an atomic SQL `UPDATE leads SET points = points <op> :n` after save, retried up to 3 times on deadlock; the actual value is re-read into the entity. [code: app/bundles/LeadBundle/Entity/LeadRepository.php:1370-1427 @7.x]

B15.2 `LEAD_POINTS_CHANGE` is not dispatched for new contacts, imported contacts, or when old and new points are both 0 or below. [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:42-62 @7.x]

B15.3 Anything that sets points must use `setPoints()` or `adjustPoints()`; points are excluded from the DBAL custom-field write. [code: app/bundles/LeadBundle/Entity/Lead.php:808-871 @7.x] [code: app/bundles/LeadBundle/Entity/LeadRepository.php:1429-1435 @7.x]

## 16. Contradictions and open questions

C1. Default unique-identifier operator. Code: `contact_unique_identifiers_operator` and `company_unique_identifiers_operator` default to OR. [code: app/bundles/LeadBundle/Config/config.php:360-361 @7.x] Docs: "AND is the default operator". [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#managing-duplicates] Code wins.

C2. Merge field rule. Code: the newest non-empty value wins regardless of winner. [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:119-172 @7.x] Docs: the merged contact's values only fill empty fields on the main contact. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#merge-two-contacts] Code wins.

C3. New primary after deleting or removing a company. Code takes the first row of an unordered query. [code: app/bundles/LeadBundle/Entity/CompanyLeadRepository.php:54-76 @7.x] Docs: "the most recently attached Company". [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#deleting-companies] Treat the choice as unspecified.

C4. Company identification. Code matches on the configured company unique identifiers. [code: app/bundles/LeadBundle/Helper/IdentifyCompanyHelper.php:11-60 @7.x] Docs say companies are matched "strictly" by name, city and country or state. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#identifying-companies]

C5. `POST /api/companies/batch/addcontacts` is documented only in the 8.0 devdocs but exists on the 7.x branch (after 7.2.1, not yet released; [PR #16512]) and not yet in 8.x code. [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:121-153 @7.x] [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/companies.html#batch-add-contacts-to-companies]

C6. UTM recording. One docs page says UTM tags are recorded only by the "Record UTM Tags" form action; the UTM pages say landing-page and tracking-script visits record them too. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#utm-code] [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_landing_pages.html] Not resolved from the contacts code analysis.

C7. Suspected bugs (inferred from code, unverified by tests):
- `LeadPermissions::analyzePermissions()` adds `viewown` when `array_intersect(...) == $viewPerms`; `!=` looks intended. [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php @7.x]
- `addDncForContact()` with an existing UNSUBSCRIBED entry and override off returns the last iterated DNC object, not false, and still saves. [code: app/bundles/LeadBundle/Model/DoNotContact.php:105-130 @7.x]
- `removeBounceStatusAction` has no contact permission check and dereferences `$dnc->getLead()` without a null check. [code: app/bundles/LeadBundle/Controller/AjaxController.php:420-447 @7.x]
- `ContactRequestHelper::getContactFromUrl()` merge branches depend on `$this->trackedContact`, assigned only after it returns; on the first call these merges likely never run. [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:154-216 @7.x]
- `setFrequencyRules(..., persist: false)` leaves `$entities` empty, so all existing rules are deleted. [code: app/bundles/LeadBundle/Model/LeadModel.php:1180-1183 @7.x]
- Campaign "update contact" calls `fail()` then `pass()` on the same log on `ImportFailedException`, and calls `setFieldValues` twice. [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:358-391 @7.x]
- `LeadRepository::updateContactPoints` swallows non-deadlock DB errors. [code: app/bundles/LeadBundle/Entity/LeadRepository.php:1385-1394 @7.x]

C8. Open: how frequency rules are enforced at send time (EmailBundle/ChannelBundle); whether SMS and notification stats are intentionally not moved on merge; whether DB-level unique enforcement was ever intended. [unverified]
