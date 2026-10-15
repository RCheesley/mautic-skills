# Contacts, companies and fields - pull-request history

## Table of contents
- [How to read this file](#how-to-read-this-file)
- [Decisions that shaped current behaviour](#decisions-that-shaped-current-behaviour)
  - [Custom fields: columns, creation and deletion](#custom-fields-columns-creation-and-deletion)
  - [Custom fields: length, index and unique flag](#custom-fields-length-index-and-unique-flag)
  - [Custom fields: types, options and values](#custom-fields-types-options-and-values)
  - [Defaults and core fields](#defaults-and-core-fields)
  - [Unique identifiers and duplicate matching](#unique-identifiers-and-duplicate-matching)
  - [Contact-field tokens](#contact-field-tokens)
  - [Identification, tracking and devices](#identification-tracking-and-devices)
  - [Merging and deduplication](#merging-and-deduplication)
  - [Companies](#companies)
  - [Do Not Contact](#do-not-contact)
  - [Import](#import)
  - [Export](#export)
  - [Contact API](#contact-api)
  - [Points on contacts](#points-on-contacts)
  - [Tags](#tags)
  - [Timeline, audit log and profile](#timeline-audit-log-and-profile)
  - [Search, list, notes and permissions](#search-list-notes-and-permissions)
  - [Preference centre and frequency rules](#preference-centre-and-frequency-rules)
  - [Raw input versus cleaning](#raw-input-versus-cleaning)
  - [8.x only](#8x-only)
- [Questions resolved against 7.x code](#questions-resolved-against-7x-code)
- [Regression catalogue](#regression-catalogue)
- [Feature timeline](#feature-timeline)
- [Removed, deprecated, replaced](#removed-deprecated-replaced)
- [Maintainer norms for this area](#maintainer-norms-for-this-area)
- [Open questions](#open-questions)
- [Coverage](#coverage)

## How to read this file
Source: merged pull requests on github.com/mautic/mautic for LeadBundle outside segments, harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; `~` marks an inference; "7.3.0-rc" means merged to `7.x` after 7.2.1 and not yet released.
Current behaviour lives in behaviour.md (code-verified); this file explains why and when it came to be.

## Decisions that shaped current behaviour

### Custom fields: columns, creation and deletion
- A field definition is saved only if its column is created. A specific flash error appears only for the two MySQL row-size and column-limit error codes. Edits to existing fields are always saved [PR #4019] (~v2.9.0), with a regression fix in [PR #4342].
- Aliases that are SQL reserved words or numbers get an `f_` column prefix; existing fields were not migrated [PR #664] (~v1.1.3).
- Reserved segment-filter keywords cannot be field aliases (`hit_url_count`, `sessions`, later `contact_id`, `company_id`), enforced by `FieldAliasKeywordValidator` [PR #5838] (~v2.13.0) [PR #10224] (~v4.2.1). System aliases such as `owner` are rejected too, because an `owner` field broke the contact page [PR #15059] (v7.0.0).
- Aliases are unique across contact and company fields. A colliding auto-generated company alias gets a numeric suffix, because import maps columns by alias [PR #7210] (~v2.16.1).
- Batch-deleting fields drops their columns, including on companies [PR #5834] (~v2.13.0). Batch deletion uses the same column-deletion service as single deletion, also in background mode [PR #15962] (~v7.1).
- A field used in a segment filter cannot be deleted, singly or in bulk; the flash names the blocking segments [PR #6725] (~v2.14.2) [PR #7157] (~v2.15.1). The API refuses the same delete with HTTP 409 [PR #15882] (~v7.1). Campaign-condition usage is not checked [PR #6725].
- Cloning a field creates the clone immediately with a unique alias, and its object and type cannot change [PR #6542] (~v2.14.2). Cloning uses `/s/contacts/fields/clone/{id}`, and cloning a core field yields a normal writable field that keeps properties such as character length [PR #14780] (v5.2.7).
- Background column creation: with `create_custom_field_in_background`, saving a field skips `ALTER TABLE` and the field stays unpublished until `mautic:custom-field:create-column` runs [PR #8828] (~v3.3). The API returns 202 for background and 201 for inline creation [PR #9761] (~v4.0). The command handles several pending fields [PR #10458] (~v4.3); without `--id` it creates every pending column, and a separate `--all` flag was rejected [PR #12508] (~v5.0). It takes a lock [PR #12000] (~v5.0) and works without a creating user [PR #12446] (~v5.0).
- With background mode on, deleting a field soft-deletes it, and `mautic:custom-field:delete-column [--id] [--user]` drops the column (no `--id` = all; no `--user` = last modifier) [PR #14679] (v7.0.0).
- `mautic:fields:analyse [-t]` reports VARCHAR-backed fields with length, longest value and a suggested size [PR #10775] (~v5.1.0). It quotes identifiers, CSV-quotes labels with commas and never suggests a size smaller than the current one [PR #15463] [PR #15477] (v7.0.0).
- Column types: UI-created text fields are VARCHAR(191), not 255, because of the utf8mb4 index limit [PR #9460] (~v4.3). `phone`, `mobile`, `fax`, `companyphone` and `companyfax` are varchar with a `<col>_search` index [PR #8407] (~v3.0). Multiselect columns are TEXT with no index [PR #7596] (~v2.16.1).
- `generated_email_domain` ("Email Domain") is an indexed, database-generated column kept in sync with email; filter on it rather than `LIKE` on email [PR #10583] (~v4.1). Every extra indexed column reduces the custom-field index budget [PR #10583].
- Company custom-field creation was fixed on 6.x with a migration for `is_short_visible` [PR #14566] (v6.0.0).
- `GET /api/fields/contact` needs only Custom Fields view or manage permission, not admin [PR #9078] (~v3.1). The view and manage permissions were lost when segment permissions were split and restored in [PR #13741] (v5.1.0).

### Custom fields: length, index and unique flag
- Text fields have a maximum length (at most 255 when indexed) and an "indexable" flag counted against MySQL's 64-index limit. Non-indexed or longer fields may be TEXT, and background mode applies index changes with `mautic:custom-field:update-column -i <id>` [PR #13319] (~v5.1). Indexes on existing core fields (phone, city) were not created at merge [PR #13319].
- Length was fixed at creation in [PR #13319] (~v5.1); changed by [PR #14762] (v7.0.0): `charLengthLimit` is editable in the UI and through `PATCH /api/fields/contact/{id}/edit`, the column is resized, and shortening below the longest stored value is rejected with "This value cannot be set this short…".
- The fields API returns `isIndexed` and `charLengthLimit` [PR #14442] (v5.2.2). A label longer than 191 characters gives a validation error, not an exception [PR #13761] (v5.1.0).
- "Is Unique Identifier" is validated server-side on the full form, Quick Add and the API, honouring the AND/OR operator; the client-side "contact already exists" check stays [PR #11716] (~v5.0). The flag was disabled for company fields [PR #14236] (v5.2.0) and re-enabled as a company dedupe key, explicitly reverting that change [PR #15784] (v7.1).
- Indexed fields show a search icon and unique identifiers a key icon [PR #14999] (v7.0.0). Custom Fields has "Indexed" and "Unique" quick filters (`is:indexed`, `is:unique`) [PR #16872] (7.3.0-rc).
- Lookup values are validated at a maximum of 191 characters on create, edit and import [PR #10225] (~v4.2).

### Custom fields: types, options and values
- Select and lookup options are a list, not a bar-separated string [PR #815] (~v1.2); lookup options are single values [PR #2814] (~v2.3) [PR #13946] (v5.1.1). A 3.0 migration normalised lookup, select and multiselect properties to arrays [PR #8740] (~v3.0).
- Symfony 3 flipped choice keys and values; many follow-ups fixed the fallout, including state names over the API [PR #8137] [PR #8771] (~v3.0) and date and locale lists [PR #11233] (~v4.4.0) [PR #11364] (~v4.4.2).
- Only defined option values are stored for `select` fields, on import and on every `LeadModel::saveEntity` path; others become NULL [PR #14183] (v5.2.0). Import also updates select values on existing contacts [PR #15136] (v7.0.0). Option keys and values are trimmed on save because trailing spaces broke campaign updates [PR #15703] (~v7.1). Options with quotes save and reload [PR #14186] (v5.2.0).
- Multiselect values were limited to 255 joined characters [PR #7103], which broke form submits [PR #7375] (~v2.15.2); the TEXT column replaced the limit [PR #7596] (~v2.16.1). Multiselect options keep special characters raw: [PR #6418] forbade them and [PR #6596] allowed them again as "way too restrictive" (~v2.14.1).
- Values are stored as entered, without HTML-encoding `&`, from UI, API, integrations and import [PR #4361] (~v2.9.0) [PR #5516] (~v2.12.2).
- Boolean false persists as `0` [PR #4471] (~v2.9.1). A boolean default "No" stores `0`, not `''` [PR #14805] (v5.2.5); the old third NULL option was lost between 4.x and 5.x and not restored [PR #14805]. A boolean field created through the API without yes/no labels gets a validation error [PR #14112] (v5.2.0).
- Number fields keep non-zero fractions such as `0.5` on API `POST`/`PATCH`; only true zeros are filtered, preserving merge behaviour [PR #16591] (v7.2.0). Rounding modes use `\NumberFormatter::ROUND_*` [PR #11677] (~v5.0).
- Datetimes are stored in UTC and shown in the user's timezone [PR #9747] (~v3.3.3). Time fields are stored and shown as entered, with no timezone conversion, so the server must run in UTC [PR #11040] (~v4.3). Relative words (NOW, TODAY…) are accepted in the edit form and Update contact action but not in field defaults [PR #4615] (~v2.10.0).
- Change detection normalises types (`0` equals `false`), so an unchanged save records no field change [PR #4700] (~v2.10.1). Editing a contact leaves unset core text fields NULL, not `''` [PR #5259] (~v2.12.1).
- Email validation is syntax-only, with no DNS or MX check [PR #10273] (~v4.2). Consecutive dots are rejected, not corrected [PR #11258] (~v4.4.0).
- The `html` field type stores HTML, shows it as text in details and the audit log, and renders unescaped through `{contactfield=alias}` [PR #13428] (~v5.1). HTML is kept through import and add/edit [PR #15139] (v7.0.0). The textarea "Allow HTML" option [PR #8706] (~v4.0) was kept beside the type, then removed with a data migration; `setCleaningRules` was deprecated, not removed [PR #13926] (v5.2.0).
- Website and URL fields reject `data:` URLs [PR #15749] (~v7.1). Company score is validated to 0..2147483647 [PR #15455] (v7.0.0).
- Hosting can override countries and regions with `countries.json` and `regions.json` in the upload directory [PR #13430] (~v5.1).
- Field order choices list only fields of the selected object and group; fixed fields cannot be reordered [PR #14242] (v5.2.0). "Visible on short forms" became "Visible on quick add" [PR #13504] (v5.1.0). Field-type labels were renamed for marketers ("Text: Short answer") [PR #13368] (~v5.1).
- `CustomFieldHelper::fieldValueTransformer()` replaces the misspelled `fieldValueTransfomer()` and appends `23:59:59`/`00:00:00` for `in_next`/`in_last` [PR #17282] (7.3.0-rc).

### Defaults and core fields
- Defaults apply to contacts and companies created outside the UI only when the field has no value [PR #3022] (~v2.3), including tracker-created visitors [PR #6402] (~v2.14.1) and import [PR #2616] (~v2.2). Import applies defaults to empty fields and loads field metadata once per object per request (6,000 rows: 150 MB to 26 MB) [PR #15959] (v7.2.0).
- A default must match the field type; for select, multiselect and lookup it is picked from the options [PR #3295] (~v2.6). Multiselect defaults use the multiselect control [PR #10415] (~v4.1) [PR #11069] (~v4.2.2).
- Import does not overwrite an existing value with the default when the column is absent from the CSV [PR #6616] (~v2.14.2).
- Identifying fields cannot have defaults (email, firstname, lastname, company, unique identifiers, social fields; for companies companyname, companyemail, companywebsite, city, state, country). Why: a default first name made every visitor "identified" [PR #11250] (~v4.4.0).
- Email cannot be unpublished; other core fields can be unpublished without breaking forms or lists [PR #1827] (~v2.0). Templates must tolerate unpublished fields [PR #13254] (v5.0.3).
- `last_active` is a built-in, non-removable field [PR #6279] (~v2.15.1). The contact field labelled "Company" became "Primary company"; the alias stays `company` [PR #6615] (~v2.14.2).
- `isUniqueIdentifier` is settable through the API; before that only the misspelling `isUniqueIdentifer` worked [PR #3626] (~v2.7).

### Unique identifiers and duplicate matching
- Any field can be a unique identifier; a match updates the existing contact. Email is unique by default [PR #345] (~v1.0.4). The UI warns about mass-merge risk [PR #1201] (~v1.2.3).
- Lookup used OR ("we need only 1 match to identify a contact") [PR #7501] (~v2.15.2); changed by [PR #9452] (~v4.0) to the configurable `contact_unique_identifiers_operator`, OR by default, used by import, API and integrations.
- Company matching was hard-coded to name, city, country and state with AND; [PR #9461] (~v4.0, BC break) made company unique flags and `company_unique_identifiers_operator` drive it, flagging those four fields by migration. Non-unique company fields then threw an exception until [PR #10173] (~v4.0).
- Email lookup uses no database-side `LOWER()`; it relies on case-insensitive collation [PR #6603] (~v2.14.2).

### Contact-field tokens
- `{leadfield=}` became `{contactfield=}` [PR #1893] (~v2.0); `leadfield` was no longer suggested but still rendered [PR #5574] (~v2.12.2). 7.x does not render it (see resolved questions).
- `{contactfield=x|true}` URL-encodes the value and an empty value outputs empty (BC break: `true` is no longer a literal default) [PR #6078] (~v2.14.1). Date modifiers `|date`, `|time`, `|datetime` exist [PR #6237] (~v2.14.1). `{contactfield=alias|label}` outputs labels for select and boolean fields [PR #12620] (~v7.0).
- Company tokens resolve from the primary company [PR #5800] (~v2.13.0) [PR #10733] (~v4.2.1) [PR #11711] (~v5.0), in non-campaign dynamic content [PR #13393] (~v5.1), and in email preview, Send example and send-from-contact [PR #14944] (v7.0.0; backport [PR #15128] v5.2.7).
- `{ownerfield=…}` comes from the contact owner [PR #8373] (~v3.1); in tracked URLs it resolves at redirect [PR #15924] (v7.2.0).

### Identification, tracking and devices
- Anonymity is decided by `date_identified`, set by identifying data including on import [PR #585] (~v1.1.3) [PR #1763] (~v2.0). A contact with only a social identity [PR #617] (~v1.1.3) or only a company [PR #7482] (~v2.15.2) is identified.
- An anonymous visitor who submits a form is converted in place, keeping tags and history [PR #1037] (~v1.2.1). Kiosk-mode forms do not set cookies or merge the visitor [PR #253] (~v1.0).
- IP-based merging of anonymous visitors ended with cookie-only tracking [PR #2950] (~v2.3); 7.x has it only as opt-in `track_contact_by_ip`. A "do not track" IP always skips tracking, even for a cookie-identified contact [PR #7805] (~v2.15.3).
- Fingerprinting arrived as an opt-in [PR #2999] (~v2.5) [PR #3279] (~v2.8) and was removed in 3.0 because identical fingerprints (iPhones) merged strangers [PR #8428] (v3.0).
- Device tracking: the `mautic_device_id` cookie holds a random tracking id on a `LeadDevice` row and replaced the lead-id cookies (BC break) [PR #5437] (~v2.13.0). `mtc_sid` is no longer set; only `mtc_id` remains (BC break) [PR #12440] (~v5.0). Device dedupe also matches OS [PR #15343] (v7.0.0).
- Clickthrough identification: an anonymous visitor merges into the stat's contact; an already-identified tracked contact is not merged and the cookie switches instead [PR #5945] (~v2.13.0). `ct` uses the found contact directly [PR #7595] (~v2.16.1). The "Identify visitor by tracking URL" setting and `$clickthrough['lead']` were removed; identification goes through `ON_CLICKTHROUGH_IDENTIFICATION` subscribers, and pre-2018 links no longer identify [PR #14974] (v7.0.0).
- Logged-in Mautic users are never tracked as contacts or devices [PR #4395] (~v2.9.0) [PR #6131] (~v2.14.0).
- Merge records: merged-away ids are stored in `contact_merge_records`, and an old `mtc_id` resolves to the survivor [PR #4850] (~v2.10.1).
- `LeadGetCurrentEvent` lets a plugin supply the current contact before default identification [PR #15556] (v7.0.0). A listener can call `skipContactLastActiveLogged()` to record a hit without bumping `last_active`, and cookies are cleared when the hit is not trackable [PR #16080] (v7.2.0). Tracking services reset for long-running workers [PR #15625] (~v7.1). `leads.last_active` is indexed [PR #16548] (v7.2.0).
- Geo lookup uses the real IP before anonymisation [PR #8175] (~v2.16.1). The IP-lookup organisation sets the company only when `ip_lookup_create_organization` is on (default off, because a company alone identifies a contact) [PR #7083] (~v2.15.1) [PR #7482] (~v2.15.2).
- `date_modified`: DNC-only changes no longer bump `date_modified`/`modified_by`, to avoid `leads` deadlocks [PR #13994] (v5.2.0); batch "Set DNC" broke and was fixed [PR #14085] (v5.2.0). `date_modified` is set on create and back-filled from `date_added` by migration, enabling one "changed since" API sync [PR #14433] (v6.0.0). See resolved questions for the 7.x reading.
- The contact "updated" webhook fires only on real data changes [PR #12535] (~v5.0). "Contact created" fires on identification, not anonymous creation [PR #4590] (~v2.10.0).
- Contact changes record a manipulator from campaigns and integrations [PR #11669] (~v5.0); the audit log stores `manipulated_by`/`manipulator_key` [PR #13432] (~v5.1).

### Merging and deduplication
- Manual merge: the picked contact merges into the viewed one and is deleted [PR #803] (~v1.2). Merging must not re-add segments or campaigns and must not fail without an owner [PR #144] (~v1.0) [PR #1068] (~v1.2.2). The field-value rule is now "newest non-empty wins" (behaviour.md B6.3); [PR #803]'s "keep existing values, fill blanks" is historical.
- API create and edit merge on unique identifiers [PR #3317] (~v2.8). POST matching an existing contact is treated as PATCH [PR #5050] (~v2.11.0). Omitted fields, tags and points are not wiped [PR #5892] (~v2.13.0), and stage and owner are kept when not sent [PR #12078] (~v5.0).
- Merge arithmetic: points are summed [PR #5964] (~v2.13.1). A NULL `date_identified` never overwrites the winner's [PR #6358] (~v2.14.1). A value that is only the newest contact's default does not overwrite a real value [PR #7717] (~v2.16.1). The loser's devices are reassigned, not deleted [PR #8836] (~v3.0.1).
- Company links move on merge: the loser's links missing on the winner are recreated with their original `date_added`; the winner keeps its primary, else inherits the loser's. This applies to manual merge and form-submission dedupe [PR #16247] (v7.2.0).
- `mautic:contacts:deduplicate` merges older into newer by default, takes values from the most recently modified record, keeps the latest `last_active` and oldest `date_identified`, and skips contacts conflicting on another unique field [PR #5344] (~v2.14.0). It queries only contacts with duplicates and parallelises with `--batch` and `--processes` [PR #11697] (~v5.0).
- Batch API endpoints resolve merged-away ids to the winner without creating duplicates [PR #15447] (v7.0.0). The merger no longer clears repositories mid-merge [PR #12195] (~v5.0).
- Code chain: `LeadModel::mergeLeads` deprecated for `ContactMerger` [PR #5344]; all callers moved [PR #8335] (~v3.0); `LegacyLeadModel` removed [PR #11543] (~v5.0).
- Duplicates can still be created manually in the UI [PR #202] (~v1.0).

### Companies
- Companies are a separate entity; a contact can have several [PR #2558] (~v2.2). Single-company mode `contact_allow_multiple_companies` (default true) overwrites rather than adds, and `mautic:contact:delete:secondary-companies` cleans up [PR #12219] (v5.1.0).
- Primary company: a star marked it [PR #2869] (~v2.3); re-assigning made a company primary [PR #4377] (~v2.9.0); changed by [PR #11000] (~v4.2.1): the primary link and `company` field always follow the links, removing the primary promotes another, removing all empties `company`. An empty `company` from an integration removes the primary link [PR #11658] (~v5.0).
- Renaming a company updates `company` on contacts whose primary it is [PR #5675] (~v2.13.0) [PR #16176].
- Deletion chain: deleting a company NULLs `leads.company` [PR #15462] (v7.0.0); then companies are soft-deleted, a new primary is chosen, and with `update_company_mapping_data_in_background` cron runs `mautic:company:update_lead_company` and `mautic:company:delete_company_leads` [PR #16176] (v7.2.0). The "most recently attached" new-primary rule is from the PR; behaviour.md C3 treats the choice as unspecified.
- No company is created or guessed from the email domain ("confusing and inaccurate") [PR #6170] (~v2.14.0). Lookup is by name first [PR #5610] [PR #5637] (~v2.14.1), now by unique flags [PR #9461].
- `POST /api/companies/new` and `/batch/new` update a matching company instead of duplicating [PR #12273] (v5.2.1).
- Company merge: the company picked in the modal is the master [PR #2879] (~v2.3). A company cannot merge with itself [PR #13578] (v5.2.0), and Merge appears only after save [PR #13679] (v5.2.0).
- The company lookup on contact edit loads the first 100 and searches the rest [PR #14461] (v5.2.4); a selected company beyond the first 100 is kept on save [PR #15232] (v6.0.4); names show without location [PR #15801] (v7.0.1).
- Company changes on contact edit are logged as contact changes, old and new [PR #9317] (~v3.2) [PR #11110] (~v4.3). Owner changes are logged with the user id [PR #12766] (~v5.0) [PR #13346] (~v5.1).
- The company API uses `lead:leads` permission [PR #7442] (~v2.15.2). Company webhooks [PR #8133] and the Contact Company Subscription Change webhook [PR #8218] exist from ~v3.1.
- Bulk Change Owner on companies [PR #16853] (v7.2.0); `is:unowned` company search [PR #17451] (7.3.0-rc); bulk remove contacts from a company, max 1,000 ids [PR #16852] (7.3.0-rc); `POST /api/companies/batch/addcontacts` [PR #16512] (7.3.0-rc).
- Company names with `&` are decoded once in all views [PR #17266] (v7.2.1). The company detail page loads chart and contacts by AJAX [PR #16015] (~v7.1) and lists only linked contacts [PR #12464] (~v5.0).

### Do Not Contact
- The universal `lead_donotcontact` table (channel, channel id, reason 0-3) replaced `email_donotemail` [PR #1513] (~v1.4). One row per contact and channel, written through the model so events fire [PR #1823] (~v2.0).
- Reversibility: [PR #1513] called an unsubscribe "not reversible by an admin", and [PR #1663] (~v1.4) kept reason 1 when a manual DNC was added. Later PRs allowed removal from the profile [PR #1840] (~v2.0) [PR #11665] [PR #12074] (~v5.0), by preference-centre re-tick [PR #3905] (~v2.8.1), by import [PR #7464] (~v2.15.2) and by the campaign Remove DNC action [PR #7567] (~v2.16.0). The 7.x rule is in resolved questions.
- DNC is checked by contact id, not email, so a duplicate does not inherit it [PR #6297] (~v2.14.1). DNC on an already-deleted contact is skipped [PR #6883] (~v2.15.1).
- API: `POST /contacts/{id}/dnc/{channel}/add` stores `channelId` [PR #6807] (~v2.15.1); with no reason it uses 3, and reason 0 is rejected with 400 [PR #9229] (~v3.1.1). Batch edit mapped reason 0 to 3 [PR #7437] (~v2.15.2); 7.x removes the DNC instead (behaviour.md B10.8).
- `addDncForContact()` argument order was fixed at call sites, the bounce processor passes BOUNCED, and `DoNotContactSubscriber` listens again; this made import, batch, monitored-inbox and SMS STOP DNC work [PR #9186] (~v3.1.2).
- Bulk DNC from the list creates one timeline entry per contact [PR #12839] (~v5.0). An empty contact search no longer loads all DNC rows (OOM at 1.7M rows) [PR #13347] (~v5.1).
- Channels: SMS DNC is honoured [PR #5397] (~v2.12.2). Form action "Remove contact from DNC" [PR #2936] (~v2.3) works with any email field alias [PR #12393] (~v5.0). Campaign actions `lead.adddnc`/`lead.removednc` [PR #7567] and condition "Has Do Not Contact flag" [PR #12099] (~v5.0).
- Search `dnc:any`, `dnc:<channel>` and `!dnc:any` [PR #14952] (v7.0.0); DNC columns in six report sources [PR #14915] (v7.0.0).

### Import
- Matching uses every unique-identifier field [PR #4765] (~v2.10.1); re-import updates rather than duplicates [PR #5282] (~v2.12.0); an `ID` column takes priority [PR #9780] (~v4.0); the AND/OR operator applies [PR #9452].
- Background import with an Import entity, `mautic:import`, `parallel_import_limit` and `background_import_if_more_rows_than` [PR #4067] (~v2.9.0). Only one import runs at a time [PR #9782] (~v3.3.3). It survives SIGTERM/SIGINT with PCNTL [PR #12845] (~v5.1); unpublishing stops it [PR #13952] (v7.0.0). A closed EntityManager makes the import DELAYED, not FAILED [PR #10744] (~v4.2) [PR #17615] (7.2 branch, unreleased).
- "Skip if value exists" [PR #7460] (~v4.0.0) was relabelled "Keep value if already exists" [PR #12551] (~v5.0), made to work [PR #13008] (~v5.0), and extended to booleans [PR #15468] (v7.0.0). It is offered only for core contact and company imports [PR #16008] (v7.2.0).
- Tags: existing tags are kept and import-form tags added [PR #2538] (~v2.2) [PR #11220] (~v4.4.0); a CSV tags column is `|`-separated [PR #12547] (~v5.0).
- DNC: the property is mappable [PR #4930] (~v2.10.1); 0/No/False removes manual DNC or bounce [PR #7464]; it applies to new contacts [PR #9732] (~v4.0); TRUE/yes/1 marks DNC [PR #15133] (v7.0.0).
- Permissions: each row is checked against the user who last modified the import, so create-only users cannot update [PR #14554] (v6.0.0). Imports by users without publish permission are saved unpublished [PR #15137] (v7.0.0).
- "Create new Contacts?" (`create_new`, default Yes): No means update only [PR #17176] (v7.2.0).
- Robustness: failed rows are logged while the rest imports [PR #14642] (v6.0.0) [PR #15008] (v7.0.0); invalid dates skip the row [PR #15549] (v7.0.0); email `0` is rejected [PR #15779] (~v7.1); an unknown `ownerusername` fails that row only [PR #15877] (~v7.1); raw SQL is hidden [PR #6569] (~v2.15.1) [PR #13367] (~v5.1).
- Import is generic, with contact and company logic in listeners [PR #7308] (~v4.0.0). Mapping is validated before creation via `ImportValidateEvent` [PR #10884] (~v4.3).

### Export
- List export covers all contacts matching the search or the selection [PR #3123] (~v2.5). Batched exports sort with a unique tiebreaker [PR #10849] (~v4.2.1).
- Background CSV export with `contact_export_in_background` and `mautic:contacts:scheduled_export`; Excel stays immediate [PR #11272] (~v5.0). `contact_export_limit` (0 = unlimited) blocks over-cap exports [PR #14691] (v7.0.0); `mautic:contacts:cleanup_exported_files` removes files after `clear_export_files_after_days` [PR #15471] (v7.0.0); `contact_export_notify_admins` [PR #16095] (v7.2.0).
- Each export is written to `audit_log`; a per-feature log file was rejected [PR #13981] (v5.2.0). Exports need their own "Export" permission, granted to existing roles by migration [PR #12884] (~v5.1), including timeline and audit-log export [PR #13980] (v5.2.0).

### Contact API
- Fields are grouped by field group plus `fields.all` [PR #246] (~v1.0). `total` is an integer [PR #10065] (~v4.0). An empty `contacts` result is `{}`: [PR #10065] made it `[]`, and [PR #10724] (~v4.3) restored `{}` as the contract.
- Blanks do not overwrite by default; `overwriteWithBlank: true` clears, kept opt-in for BC [PR #8459] (~v3.0). Batch endpoints honour it [PR #12255] (~v5.0). Only `''` counts as blank and `0` is a value [PR #1247] (~v1.2.3).
- Batch create upserts [PR #5396] (~v2.12.1) [PR #5979] (~v2.13.1) and is faster (381 to 9 custom-field queries per 100) [PR #11277] (~v5.1.0). `batch/edit` with a missing id creates a contact (201) [PR #10724]. The same id twice in one bulk edit applies both [PR #14928] (v5.2.7).
- Number fields return an integer at 0 precision, else a float [PR #8845] (~v3.0). Values are cleaned before the duplicate lookup [PR #5520] (~v2.13.0).
- `owner` and `stage` can be set on create [PR #5750] (~v2.13.0). `color` is not settable [PR #5892].
- `contact_api_count_cache_ttl` (default 5 s) caches the `GET /api/contacts` total; the UI is never cached [PR #13288] (~v5.1). The list page does not join IPs but the API does [PR #11620] (~v5.0) [PR #12274] (~v5.0).
- `where[]` values are not entity-encoded [PR #14550] (v6.0.0). `mautic.pre_batch_save` and `mautic.post_batch_save` events exist [PR #14503] (v6.0.0). API requests start no PHP session [PR #11144] (~v5.1.0).
- The `lead` key was removed from webhook payloads in favour of `contact` (BC break) [PR #8170] (~v3.0).

### Points on contacts
- Points change by atomic database increment (200 concurrent submits: 33 to 197 points) [PR #4752] (~v2.10.0). Points are never written through the custom-field SQL path, and new installs default `points` to 0 [PR #6118] (~v2.14.0).
- The Update contact action leaves unset points and NULL booleans alone [PR #4609] [PR #4633] (~v2.10.0); its boolean option has "No change" [PR #14888] (v5.2.5) and values are truncated to the field length [PR #14889] (v7.0.0).
- Stage changes go through `LeadModel::addToStage/changeStage/removeFromStage` [PR #17041] (v7.2.0).

### Tags
- `tags=a,b,-c` with a leading `-` removes a tag [PR #798] (~v1.2). The API upsert does not clear tags when none are sent [PR #5892].
- Tag names are normalised for HTML encoding before lookup and creation across import and campaign, point and form actions [PR #14046] (v5.2.0); names are returned raw [PR #11116] (~v4.3).
- Tag merge moves contacts and deletes the secondary, with `mautic.lead_tag_pre_merge`/`post_merge` events [PR #15331] (v7.2.0). Tags in use can be deleted; links are removed first [PR #16132] (v7.2.0).

### Timeline, audit log and profile
- One audit entry per save, and last-active-only changes are not logged [PR #1202] (~v1.2.3). The timeline gives every event an `eventId` [PR #5446] (~v2.12.1).
- Segment and campaign add and remove events are logged [PR #6605] (~v2.15.0). Activity API campaign events carry `campaign_id`/`campaign_name` [PR #9507] (~v3.3).
- Detail views show only fields with a value, and 0 counts as a value [PR #11016] (~v4.3). A missing contact or company redirects with a flash, not a 500 [PR #13173] (~v5.0.0). Tabs always show, with empty states [PR #13929] (v5.2.0).
- The audit log CSV column is `userSourceName` [PR #15994] (~v7.1).

### Search, list, notes and permissions
- Permissions are owner-based: "edit/delete other" is checked against the owner, not the creator [PR #2392] (~v2.2). `GET /api/contacts` for `viewown`-only users returns owned contacts plus unowned contacts they created [PR #16022] (v7.2.0).
- `lead:notes` is its own permission group, checked in the UI, the Notes API and `/api/contacts/{id}/notes`; a migration back-fills it from `lead:leads` [PR #16067] (v7.2.0). The Notes API returns `publishDetails` [PR #17177] (v7.2.0). API notes keep HTML [PR #11793] (~v5.0).
- Fields marked searchable match plain search without `alias:`; the toggle is labelled "Add to Search Index" [PR #14393] (v6.0.0). Search commands added over time include `ids:` [PR #3101], `stage:` [PR #4405], `company_id:` [PR #10702], `campaign:<id>` [PR #15727] (~v7.1) and `form:<alias>` [PR #16355] (v7.2.0).
- Anonymous contacts are hidden from the list by default [PR #796] (~v1.2). Configurable list columns `contact_columns` [PR #7511] (~v3.2.0).
- Bulk Change Owner on contacts offers "No owner" [PR #16849] (7.3.0-rc). Bulk find-and-replace on contacts and companies [PR #16207] (v7.2.0).

### Preference centre and frequency rules
- Frequency rules per channel skip, not queue, an over-limit message [PR #2114] (~v2.1). A default rule applies only when both number and period are set; 0 or blank means no limit [PR #10753] (~v4.1.2).
- Admin channel toggles add and remove DNC [PR #7303] (~v2.15.2) [PR #8565] (~v3.0). Bounced contacts cannot re-subscribe themselves through preferences [PR #8565].
- `isPreferenceCenter` "Available in Preference Center" is separate from global visibility [PR #6410] (~v2.15.0). Category unsubscribes block segment and campaign emails in that category [PR #10879] (~v5.1.0); contacts with no category choice count as subscribed to all [PR #15533] (v7.0.0).

### Raw input versus cleaning
- Values never rendered may stay raw when SQL binds parameters: API `where[]` [PR #14550] (v6.0.0), global search [PR #14818] (v6.0.1), campaign select conditions [PR #15165] (~v7.1). Remove `InputHelper::clean` at the source rather than decoding downstream [PR #14818].

### 8.x only
- Import templates read request parameters through explicit bags [PR #17347]; `UrlType` sets `default_protocol` explicitly [PR #17349]; repository `$_em` and `$_class` are replaced by accessors [PR #17372]. All are on the `8.x` branch only.

## Questions resolved against 7.x code
- Own unsubscribe reversal: in 7.x a reason-1 (unsubscribed) entry can be removed. `removeDncForContact()` deletes the channel's entry whatever its reason unless a reason filter is passed [code: app/bundles/LeadBundle/Model/DoNotContact.php:32-62 @7.x]. Callers that remove it: the profile channel toggle and bounce badge [code: app/bundles/LeadBundle/Controller/AjaxController.php:325-345 @7.x] [code: app/bundles/LeadBundle/Controller/AjaxController.php:420-447 @7.x], `POST /api/contacts/{id}/dnc/{channel}/remove` [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:490-512 @7.x], API create/edit `doNotContact` with reason 0 [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:680-697 @7.x], import `doNotEmail` false [code: app/bundles/LeadBundle/Model/LeadModel.php:1471-1491 @7.x], the campaign Remove DNC action [code: app/bundles/LeadBundle/EventListener/CampaignActionDNCSubscriber.php:81-101 @7.x], the form Remove DNC action [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:305-314 @7.x] and the resubscribe URL [code: app/bundles/EmailBundle/Controller/PublicController.php:439-492 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:1787-1801 @7.x]. The preference form removes only UNSUBSCRIBED or MANUAL, never BOUNCED [code: app/bundles/LeadBundle/Controller/FrequencyRuleTrait.php:165-175 @7.x]. What is protected is overwriting: an add with another reason does not replace an unsubscribe unless override is on [code: app/bundles/LeadBundle/Model/DoNotContact.php:105-118 @7.x]. [PR #1513]'s "not reversible" is historical.
- Manual merge winner: the viewed contact survives and the selected one is deleted [code: app/bundles/LeadBundle/Controller/LeadController.php:1064 @7.x]. Field values come from whichever contact was modified (or added) most recently, independent of the winner [code: app/bundles/LeadBundle/Deduplicate/ContactMerger.php:119-172 @7.x]. This matches behaviour.md B6.3 and B6.12.
- `{leadfield}` token: 7.x does not render it. The token regex matches only `contactfield` and `companyfield` [code: app/bundles/LeadBundle/Helper/TokenHelper.php:11 @7.x]. The BC alias was present at 2.16.0 and gone by 3.0.0 (git grep of `TokenHelper.php` at those tags); no PR in the inputs records the removal [PR #5574].
- DNC reason 0 through the API: the single `dnc/{channel}/add` endpoint rejects 0 with 400 [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:467-477 @7.x]; create, edit and batch payloads treat reason 0 as "remove DNC" for existing contacts [code: app/bundles/LeadBundle/Controller/Api/LeadApiController.php:680-697 @7.x]. [PR #7437]'s mapping of 0 to 3 is historical.
- `date_modified` on DNC changes: a save whose only changes are `dnc_channel_status` or `manipulator` skips `date_modified` and `modified_by` [code: app/bundles/LeadBundle/Entity/Lead.php:1924-1936 @7.x] [code: app/bundles/CoreBundle/Model/FormModel.php:269-271 @7.x] [PR #13994]. On create, `setModifiedData()` sets `date_modified` [code: app/bundles/CoreBundle/Model/FormModel.php:251-266 @7.x] [PR #14433]. behaviour.md has no `date_modified` rule to reconcile. See Open questions for the update path.
- Company unique identifier: enabled in 7.x. The `isUniqueIdentifer` toggle is added for every field object with no company exception [code: app/bundles/LeadBundle/Form/Type/FieldType.php:606-618 @7.x]; [PR #15784] (v7.1.0 tag) reverted [PR #14236].
- Field length after creation: editable in 7.x. `charLengthLimit` is a normal form field with a 1..max range [code: app/bundles/LeadBundle/Form/Type/FieldType.php:715-737 @7.x], and `LeadFieldMinimumLength` rejects a value shorter than stored data [code: app/bundles/LeadBundle/Translations/en_US/validators.ini:14 @7.x] [PR #14762].
- Segment operator labels in 7.x: `in` = "includes any of", `!in` = "excludes any of", `in_all` = "includes all of", `!in_all` = "excludes all of" [code: app/bundles/LeadBundle/Translations/en_US/messages.ini:767-768 @7.x] [code: app/bundles/LeadBundle/Translations/en_US/messages.ini:776-777 @7.x] [code: app/bundles/LeadBundle/Segment/OperatorOptions.php:143-162 @7.x]. `like` is "contains" [code: app/bundles/LeadBundle/Translations/en_US/messages.ini:765 @7.x] and `contains` is "in list" [code: app/bundles/CoreBundle/Translations/en_US/messages.ini:491 @7.x]. The code follows [PR #15344]; the [PR #15027] wording where `notin` meant "excludes all of" is superseded.
- Empty contacts list: `GET /api/contacts` with no results returns `"contacts": {}`, because the contact repository returns an array, not a Paginator, and `EntityResultHelper` turns an empty id-keyed result into an `ArrayObject` [code: app/bundles/ApiBundle/Helper/EntityResultHelper.php:29-32 @7.x] [code: app/bundles/LeadBundle/Entity/LeadRepository.php:478-489 @7.x]. This agrees with mautic-rest-api behaviour R31 [PR #10724].
- Segment warnings: `segment_rebuild_time_warning` (default 30) shows a red exclamation when a segment has not been rebuilt for X hours; `segment_build_time_warning` (default 30) shows a red clock when a build took longer than X seconds [code: app/bundles/LeadBundle/Config/config.php:362-363 @7.x] [code: app/bundles/LeadBundle/Translations/en_US/messages.ini:739-743 @7.x] [PR #11917].

## Regression catalogue
| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| Field row saved without a column caused 500s | Save the field only if the column is created | [PR #4019] [PR #4342] | ~2.9.0 |
| Field used in a segment was deleted, breaking segments | Deletion blocked in UI (flash) and API (409) | [PR #6725] [PR #7157] [PR #15882] | ~2.14.2, ~7.1 |
| Contact and company field shared an alias; import overwrote | Aliases unique across objects | [PR #7210] | ~2.16.1 |
| `hit_url_count`/`company_id` aliases hijacked queries | Reserved aliases rejected | [PR #5838] [PR #10224] | ~2.13, ~4.2.1 |
| Alias `owner` broke the contact page | System aliases rejected | [PR #15059] | 7.0.0 |
| Multiselect over 255 chars gave a DB error | Multiselect is TEXT | [PR #7596] | ~2.16.1 |
| Datetime shown in UTC | Shown in the user's timezone | [PR #9747] | ~3.3.3 |
| Field CRUD broke in 4.4.0 | Functional tests guard field CRUD | [PR #11321] | ~4.4.1 |
| Lookup/select creation broke after Twig | Option editor works | [PR #13946] | 5.1.1 |
| Junk values stored in select fields by import | Non-option values become NULL on every save | [PR #14183] | 5.2.0 |
| Boolean default "No" stored `''` | Stored as `0` | [PR #14805] | 5.2.5 |
| Trailing-space options broke campaign updates | Options trimmed on save | [PR #15703] | ~7.1 |
| Background column creation failed without a user | User optional | [PR #12446] | ~5.0 |
| Duplicate email saved through UI or API | Unique identifiers validated server-side | [PR #11716] | ~5.0 |
| Unpublished field broke templates | Templates check the field first | [PR #13254] | 5.0.3 |
| Default first name made every visitor identified | Identifying fields cannot have defaults | [PR #11250] | ~4.4.0 |
| Cookie pointing to a deleted contact spawned anonymous contacts | No repeated creation | [PR #119] | ~1.0 |
| Anonymous visitor's form submit created a second contact | Converted in place | [PR #1037] | ~1.2.1 |
| Colleagues behind one IP were merged | No IP merging unless `track_contact_by_ip` | [PR #2950] | ~2.3 |
| Identical fingerprints merged strangers | No fingerprinting | [PR #8428] | 3.0 |
| Logged-in user's form previews landed on one contact | Users are never device-tracked | [PR #6131] | ~2.14.0 |
| Do-not-track IP ignored for a cookie-identified contact | Do-not-track IP always wins | [PR #7805] | ~2.15.3 |
| Third-party form merge orphaned the browser | Merge records resolve an old `mtc_id` | [PR #4850] | ~2.10.1 |
| Merged points 50+100 showed 100 or 200 | Points summed (150) | [PR #5964] | ~2.13.1 |
| Anonymous merge reset `date_identified` to now | NULL never overwrites the winner | [PR #6358] | ~2.14.1 |
| Cookieless link click reset fields to defaults | Defaults never overwrite real values | [PR #7595] [PR #7717] | ~2.16.1 |
| Merge deleted devices; next hit made a new visitor | Devices reassigned | [PR #8836] | ~3.0.1 |
| Merge dropped company links | Links move to the winner | [PR #16247] | 7.2.0 |
| CSV rows sharing one unique value merged different people | AND/OR operator setting | [PR #9452] | ~4.0 |
| Batch create duplicated on repost | Batch create upserts | [PR #5396] [PR #5979] | ~2.13.1 |
| `x@y.com,` created duplicates | Values cleaned before lookup | [PR #5520] | ~2.13.0 |
| POST with an existing email wiped fields, tags and points | Omitted data untouched | [PR #5050] [PR #5892] | ~2.11-2.13 |
| PATCH with a unique field blanked the known contact | POST/PATCH keep non-empty values | [PR #7036] | ~2.15.2 |
| Clearing a field through the API was impossible | `overwriteWithBlank: true` | [PR #8459] | ~3.0 |
| Number fields returned `123.0` | Integer at 0 precision, else float | [PR #8845] | ~3.0 |
| `0.5` dropped on API write | Only true zeros filtered | [PR #16591] | 7.2.0 |
| Empty contacts list became `[]` | `{}` is the contract | [PR #10724] | ~4.3 |
| Merge through `/contacts/new` cleared stage and owner | Unsent fields kept | [PR #12078] | ~5.0 |
| Batch edit on merged ids created duplicates | Merged ids resolve to the winner | [PR #15447] | 7.0.0 |
| `where` with `'` matched nothing | Raw values with bound parameters | [PR #14550] | 6.0.0 |
| Unsubscribe URL created many DNC rows | One row per contact and channel | [PR #1823] | ~2.0 |
| Duplicate contact inherited another's DNC by email | DNC checked by contact id | [PR #6297] | ~2.14.1 |
| API DNC add without reason wrote reason 0 | Default 3; 0 rejected with 400 | [PR #9229] | ~3.1.1 |
| Import, batch, bounce and SMS STOP DNC silently not applied | Correct argument order; subscriber listens | [PR #9186] | ~3.1.2 |
| Preference toggle kept DNC | Toggle adds and removes DNC | [PR #7303] [PR #8565] | ~2.15.2, ~3.0 |
| Remove-DNC form action needed alias `email` | Any email-type field works | [PR #12393] | ~5.0 |
| Bulk DNC wrote two timeline entries | One per contact | [PR #12839] | ~5.0 |
| Empty search loaded all DNC rows (OOM) | No DNC load for empty ids | [PR #13347] | ~5.1 |
| `leads` deadlocks on bulk DNC | DNC-only change does not bump modified data | [PR #13994] | 5.2.0 |
| Batch "Set DNC" broke after the deadlock fix | Applies to all selected | [PR #14085] | 5.2.0 |
| Category unsubscribe ignored by segment/campaign emails | Category preferences enforced | [PR #10879] | ~5.1.0 |
| Only one email or SMS sent, then all held | Default rule needs number and period | [PR #10753] | ~4.1.2 |
| Gmail form submit created company "gmail.com" | No company from email domain | [PR #6170] | ~2.14.0 |
| CRM edit created a duplicate company | Match by name / unique flags first | [PR #5610] | ~2.14.1 |
| Primary company stale after removal | Primary follows the links | [PR #11000] [PR #11658] | ~4.2.1, ~5.0 |
| Non-unique company fields threw an exception | Graceful fallback | [PR #10173] | ~4.0 |
| Company batch API created duplicates or 422 | Match on unique identifiers | [PR #12273] | 5.2.1 |
| Empty company listed unrelated contacts | Strict id filter | [PR #12464] | ~5.0 |
| Contact edit hung with many companies | Capped lookup plus search | [PR #14461] | 5.2.4 |
| Company beyond the 100th lost on save | Selected company kept | [PR #15232] | 6.0.4 |
| `&amp;` shown in company names | Decoded once | [PR #17266] | 7.2.1 |
| Company owner change missing from audit log | Logged as user id | [PR #12766] [PR #13346] | ~5.0, ~5.1 |
| Re-import duplicated every row | Existing contacts updated | [PR #5282] | ~2.12.0 |
| Non-email unique identifier ignored by import | All unique fields used | [PR #4765] | ~2.10.1 |
| Absent CSV column reset fields to default | Absent columns untouched | [PR #6616] | ~2.14.2 |
| Second `--limit` run re-imported rows | Resume after the last row | [PR #5261] [PR #11060] | ~2.12, ~4.3 |
| Existing tags wiped / import tags not applied | Keep existing, add form tags | [PR #2538] [PR #11220] | ~2.2, ~4.4.0 |
| "Keep value" did nothing | Keep non-empty, fill empty, booleans too | [PR #13008] [PR #15468] | ~5.0, 7.0.0 |
| Create-only user could update through import | Per-row permission by last modifier | [PR #14554] | 6.0.0 |
| Import auto-published without publish permission | Saved unpublished | [PR #15137] | 7.0.0 |
| Invalid dates broke the edit page | Row skipped with a reason | [PR #15549] | 7.0.0 |
| Raw SQL error shown on import | Generic message | [PR #6569] [PR #13367] | ~2.15.1, ~5.1 |
| Closed EntityManager marked import FAILED | Import becomes DELAYED | [PR #17615] | 7.2 branch |
| Batched export had duplicates or gaps | Unique tiebreaker sort | [PR #10849] | ~4.2.1 |
| Contact list over 30 s with many IPs | List does not join IPs | [PR #11620] | ~5.0 |
| Concurrent submits lost points | Atomic increment | [PR #4752] | ~2.10.0 |
| Company mapping plus points action reset points | Points never via custom-field SQL | [PR #6118] | ~2.14.0 |
| Update contact reset booleans and points | Untouched fields stay as they are | [PR #4609] [PR #4633] | ~2.10.0 |
| Update contact could not set boolean No | Yes / No / No change | [PR #14888] | 5.2.5 |
| Token value exceeded field length | Truncated to the limit | [PR #14889] | 7.0.0 |
| Save & Close with a tag change gave 500 | Saves; audit shows old and new | [PR #12105] [PR #12106] | ~5.0 |
| Tags with `&` duplicated | Names normalised everywhere | [PR #14046] | 5.2.0 |
| Point-trigger tag actions ignored | Applied | [PR #12867] | ~5.0 |
| Update webhook fired on a no-op save | Only on real changes | [PR #12535] | ~5.0 |
| Missing contact URL gave 500 | Redirect with flash | [PR #13173] | ~5.0.0 |
| Timeline export without export permission | Export permission required | [PR #13980] | 5.2.0 |
| Field "view" permission lost | View and manage both work | [PR #13741] | 5.1.0 |
| `viewown` API list missed owned contacts | Owner, else creator when unowned | [PR #16022] | 7.2.0 |
| Users without permission saw notes through the API | `lead:notes` enforced | [PR #16067] | 7.2.0 |
| "R&D" not found by global search | No cleaning in global search | [PR #14818] | 6.0.1 |
| API note HTML stripped | HTML kept | [PR #11793] | ~5.0 |

## Feature timeline
| Version | Change | PR |
|---|---|---|
| 1.x | Unique identifiers, merge button, tags with `-` removal, universal DNC table, CSV-only import | [PR #345] [PR #803] [PR #798] [PR #1513] [PR #799] |
| 2.0-2.5 | `{contactfield}`, `date_identified` anonymity, companies entity, cookie-only tracking, list export | [PR #1893] [PR #1763] [PR #2558] [PR #2950] [PR #3123] |
| 2.9-2.10 | Background import, atomic points, audit log tab, CSV-header-first mapping | [PR #4067] [PR #4752] [PR #4457] [PR #4604] |
| 2.13-2.16 | Device tracking cookie, `mautic:contacts:dedup`, merge records, reserved aliases, Primary company label | [PR #5437] [PR #5344] [PR #4850] [PR #5838] [PR #6615] |
| 3.0-3.3 | Fingerprinting removed, `overwriteWithBlank`, background column creation, company webhooks | [PR #8428] [PR #8459] [PR #8828] [PR #8133] |
| 4.0-4.4 | AND/OR unique operator, company unique flags, `ID` import column, VARCHAR(191), no defaults on identifying fields | [PR #9452] [PR #9461] [PR #9780] [PR #9460] [PR #11250] |
| 5.0 | Twig templates, `mtc_sid` removed, parallel dedupe, background CSV export, server-side unique validation | [PR #11793] [PR #12440] [PR #11697] [PR #11272] [PR #11716] |
| 5.1 | Field length and index flags, HTML field type, single-company mode, Export permission, API count cache, `mautic:fields:analyse` | [PR #13319] [PR #13428] [PR #12219] [PR #12884] [PR #13288] [PR #10775] |
| 5.2 | DNC without modified-date bump, select option enforcement, Allow HTML removed, company unique flag disabled | [PR #13994] [PR #14183] [PR #13926] [PR #14236] |
| 6.0 | `date_modified` on create, searchable fields, import per-row permissions, batch-save events | [PR #14433] [PR #14393] [PR #14554] [PR #14503] |
| 7.0 | Editable field length, background column delete, `dnc:` search, tracking-URL identification removed, export limit, `LeadGetCurrentEvent` | [PR #14762] [PR #14679] [PR #14952] [PR #14974] [PR #14691] [PR #15556] |
| 7.1 | Company unique flag re-enabled, field delete 409, `campaign:` search, `data:` URLs rejected | [PR #15784] [PR #15882] [PR #15727] [PR #15749] |
| 7.2.0 | Company soft delete, merge moves company links, `lead:notes`, viewown fallback, `create_new`, tag merge, fractions kept | [PR #16176] [PR #16247] [PR #16067] [PR #16022] [PR #17176] [PR #15331] [PR #16591] |
| 7.2.1 | Company `&` decoding, "Import Another" object type | [PR #17266] [PR #17221] |
| 7.3.0-rc | Company batch addcontacts, bulk remove from company, "No owner", Indexed/Unique quick filters, company `is:unowned` | [PR #16512] [PR #16852] [PR #16849] [PR #16872] [PR #17451] |

## Removed, deprecated, replaced
| What | Replaced by | PR | Version |
|---|---|---|---|
| `email_donotemail` table | `lead_donotcontact` (channel + reason) | [PR #1513] | ~1.4 |
| `{leadfield=}` token | `{contactfield=}`; BC alias gone by 3.0.0 | [PR #1893] [PR #5574] | ~2.0 |
| Anonymity from name/email/company | `date_identified IS NULL` | [PR #1763] | ~2.0 |
| IP merging of anonymous visitors | Cookie only; opt-in `track_contact_by_ip` | [PR #2950] | ~2.3 |
| Fingerprint identification | Removed | [PR #3279] [PR #8428] | 3.0 |
| Lead-id cookies `mautic_session_id`, `mtc_sid` | `mautic_device_id`; `mtc_id` only | [PR #5437] [PR #12440] | ~2.13, ~5.0 |
| "Identify visitor by tracking URL" setting | `ON_CLICKTHROUGH_IDENTIFICATION` subscribers | [PR #14974] | 7.0.0 (BC) |
| `LeadModel::mergeLeads`, `LegacyLeadModel` | `ContactMerger` | [PR #5344] [PR #8335] [PR #11543] | ~2.14 to ~5.0 |
| LeadModel DNC methods | `DoNotContact` model | [PR #5327] [PR #9302] | ~2.12, ~3.1.2 |
| Company from email domain | Removed | [PR #6170] | ~2.14.0 |
| Hard-coded company match | Unique flags and operator | [PR #9461] | ~4.0 (BC) |
| `\|true` as literal token default | URL-encode flag | [PR #6078] | ~2.14.1 (BC) |
| Multiselect VARCHAR(255) | TEXT, no index | [PR #7596] | ~2.16.1 |
| UI text fields VARCHAR(255) | VARCHAR(191) | [PR #9460] | ~4.3 |
| `lead` key in webhooks | `contact` key | [PR #8170] | ~3.0 (BC) |
| API batch DNC reason 0 mapped to 3 | Reason 0 removes DNC | [PR #7437] | ~2.15.2 (historical) |
| Empty contacts `[]` | `{}` restored | [PR #10065] [PR #10724] | ~4.0 to ~4.3 |
| Defaults on identifying fields | Disabled and cleared | [PR #11250] | ~4.4.0 |
| LeadBundle PHP templates | Twig | [PR #11793] [PR #11814] | ~5.0 |
| `CommonController::addFlash()` | `addFlashMessage()` | [PR #12197] | ~5.0 (BC) |
| `manipulator` audit entry | `manipulated_by`, `manipulator_key` | [PR #13432] | ~5.1 |
| "Visible on short forms" | "Visible on quick add" | [PR #13504] | 5.1.0 |
| Export implied by view | Export permission | [PR #12884] | ~5.1 |
| Textarea "Allow HTML" | HTML field type; `setCleaningRules` deprecated | [PR #13926] | 5.2.0 |
| Company unique identifier disabled | Re-enabled | [PR #14236] [PR #15784] | 5.2.0 to 7.1 |
| `FieldModel::getUniqueIdentiferFields` | Other FieldModel methods | [PR #14144] | 6.0.0 |
| Non-final `LeadEvent`, untyped `getLead()` | final, `getLead(): Lead` | [PR #13842] | 6.0.0 (BC) |
| Boolean NULL third option | Yes/No only | [PR #14805] | 5.x (unacknowledged) |
| Note ACL through `lead:leads` | `lead:notes` | [PR #16067] | 7.2.0 |
| Tag delete guard | Links removed, then delete | [PR #16132] | 7.2.0 |
| `js-cookie` | Native `document.cookie` | [PR #16161] | 7.2.0 (BC in a minor) |
| `addToStages()/removeFromStages()` | `addToStage/changeStage/removeFromStage` | [PR #17041] | 7.2.0 |
| `CompanyModel::addLeadToCompany()` bool return | List of new ids | [PR #16512] | 7.3.0-rc |
| `fieldValueTransfomer()` | `fieldValueTransformer()` | [PR #17282] | 7.3.0-rc |

## Maintainer norms for this area
- Regression fixes need a functional test that fails without the fix; maintainers add one if missing [PR #5282] [PR #11321] [PR #14085].
- API behaviour changes prefer opt-in parameters over changed defaults, with tests for both options [PR #8459]. Response-shape changes such as `{}` to `[]` are BC breaks [PR #10724].
- Schema changes ship Doctrine migrations, including for dynamic custom-field columns, and leave `--dump-sql` clean [PR #7596] [PR #5898]. Permission changes back-fill existing roles by migration [PR #12884] [PR #16067].
- Use the field's `object` property, not alias prefixes, to tell contact from company fields [PR #5628] [PR #7086].
- Never load all contacts or companies into UI controls; search and page, and cap unbounded lists [PR #803] [PR #14461].
- Prove performance claims with query logs on millions of rows [PR #11620] [PR #13288] [PR #13569].
- Deleting or merging entities must update references in campaigns, segments, forms, points and reports [PR #15331]. Bulk actions dedupe and validate ids [PR #16852].
- Weakening sanitisation needs security review; remove cleaning at the source when values are not rendered [PR #14550] [PR #14818] [PR #15165].
- Log to `audit_log`, not per-feature files [PR #13981]. Never expose raw SQL errors [PR #6569] [PR #13367].
- Constructor changes on services go to the next minor, not a patch [PR #16247]. Once a minor ships, fixes target the patch branch [PR #17266] [PR #17615].
- Privacy-impacting tracking features need a config switch [PR #3279].
- UI renames cost docs and developers; use marketer-friendly labels without developer jargon [PR #13368] [PR #14393] [PR #12551].

## Open questions
- `date_modified` on update: in 7.x `setModifiedData()` writes `date_modified` only when it is empty [code: app/bundles/CoreBundle/Model/FormModel.php:278-284 @7.x]. Because [PR #14433] fills it on create and back-fills old rows, an edit of an existing contact may no longer move `date_modified` forward through `setTimestamps()`. No 7.x test asserts that an edit bumps it. This would break the "changed since" sync that [PR #14433] aimed at. Unverified at runtime.
- [PR #13994] says an email-link unsubscribe still bumps `date_modified`; in 7.x that path saves a DNC-only change, which the skip rule should exclude [code: app/bundles/LeadBundle/Entity/Lead.php:1924-1936 @7.x]. Which DNC paths bump it is unresolved.
- Company soft delete: [PR #16176] says the most recently attached remaining company becomes primary; behaviour.md C3 found an unordered query. behaviour.md wins; the PR claim is unverified. What happens to the primary on bulk remove-from-company [PR #16852] is not stated.
- [PR #16512]: whether the single `POST /api/companies/{id}/contact/{cid}/add` writes `lead_companies_change_log` is contradictory in the PR.
- [PR #7494] then [PR #8579]: is the custom-field ordering hack still in `CustomFieldRepositoryTrait`?
- AND/OR operator: does it apply to form submissions and the `ct` path as well as import, API and sync [PR #9452]?
- [PR #12551] renamed the import label to "Keep value if already exists", yet [PR #15468] quotes the older wording; check the 7.x string.
- Searchable and indexed: one column or two in 7.x, and are core-field indexes (phone, city) created [PR #14393] [PR #13319]?
- Frequency rules: [PR #2114] drops over-limit messages while [PR #10753] mentions queueing; issue mautic/mautic#10416 asks whether default 0 should queue everything.
- `create_new = No`: available from CLI and API or only the UI mapping [PR #17176]? Does a DELAYED import retry forever [PR #17615]?
- Tag merge: exactly which references are rewritten [PR #15331]?
- Bulk "No owner" on contacts: are audit and owner-change events written [PR #16849]? Is company bulk owner checked per company [PR #16853]?
- Does the UI contact list use the same `viewown` owner-or-creator fallback as the API [PR #16022]? Does the Notes API check `lead:notes` against the note owner [PR #16067]?
- [PR #8565] was merged though a reviewer asked to close it for #8434, and [PR #8828] after a final "did not behave as expected" comment; both flows exist in 7.x and need a behavioural check.
- The boolean NULL option lost in 5.x was never restored [PR #14805]. [PR #10884] lets rows with empty required values import; intended?
- Lookup suggestions come only from stored values, ignoring the defined list (issue mautic/mautic#8748) [PR #8740].
- [PR #11040] requires the server in UTC, but no official server-configuration doc says so.
- `common:` search [PR #2599] is not in 7.x; multi-`segment:` searches return wrong results [PR #7784].
- Field-type labels: LeadBundle shows the new names but FormBundle still says "Checkbox group" [PR #13368].

## Coverage
The contacts area has about 1,260 merged PRs in 15 chunks (2015-03 to 2026-10), summarised in two digests. About 1,030 are substantive; the rest are refactors, test-only changes, merge-ups or cosmetic fixes that contribute only norms. Segment, campaign, email, form, report and integration items found in these chunks are routed to their skills and left out here. A further 869 noise PRs across all areas were excluded upstream before chunking.
