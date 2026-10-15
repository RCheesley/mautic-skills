# Contacts docs digest (docs.mautic.org 7.2, devdocs 7.2)

What the official documentation says about contacts, companies, custom fields, import, tags, UTM tags, preferences
and the contact-related REST API. Where code disagrees, behaviour.md section 16 records it.

## Table of contents
1. Terminology
2. Contact types and tracking
3. Custom fields
4. Import
5. Managing contacts, duplicates and merge
6. Tags, UTM tags
7. Preferences, DNC and frequency rules
8. Companies
9. Search filters for contacts
10. REST API (contacts, companies, fields, notes)
11. Procedures
12. 8.0 docs changes

## 1. Terminology

- Use "Contact", "Company", "Segment", "Campaign", "Custom Field", "Tag", "Channel", "Preference Center" capitalised as product nouns. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html]
- "Visitor" or "anonymous Contact" replaces "anonymous lead"; "lead" survives only in code, table and command names. [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html]
- "Do Not Contact (DNC)" for channel opt-out; "Manual Unsubscription" for DNC from import or manual action. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#faq]
- "Unique identifier" for de-duplication fields; "primary Company" for the main company link. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html]
- UTM groups: "inbound capture", "outbound tagging", "targeting", "display". [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_overview.html#feature-groups]

## 2. Contact types and tracking

- Two types: Visitors (unidentified) and Standard Contacts (identified via a form or another source). [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#contact-types]
- `is:anonymous` in the Contacts search shows only visitors. [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]
- Bot, monitoring and privacy opt-out traffic creates no anonymous contacts. [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]
- The docs say anonymous data is not available for segmentation or reporting until identified. [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]
- "Do Not Track 404 error for anonymous Contacts" (Tracking Settings) skips 404 hits. [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]
- Logged-in Mautic users are not tracked; private network traffic is not tracked unless `track_private_ip_ranges` is true. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#website-monitoring]
- JS tracking (`mtc.js`, `mt('send','pageview')`) is the primary method. Cookies last 1 year; returning visitors are identified by cookie only. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-script-javascript]
- With CORS configured, a first-party `mtc_id` cookie (contact id) is set; it is not used for tracking. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#local-contact-cookie-first-party-cookie]
- Pageview custom parameters: contact fields, `tags`, UTM fields; company by `company` or `companyname` plus company fields. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-of-custom-parameters]
- Pixel `mtracking.gif` params: `page_url`, `referrer`, `language`, `page_title` (`url`/`title` deprecated); `d=` base64 serialised array from PHP. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#page-information]
- Fields update from pixel/script only when publicly editable; values must be URL-encoded. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#updating-contact-fields]
- Script tracking stores device id in local storage and a first-party cookie, falling back to Mautic-domain cookies. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#how-are-contacts-tracked-with-the-tracking-script]
- Mobile apps: email as publicly editable unique identifier, POST to `/form/submit?formId=<id>`, reuse the cookie or contacts from the same IP may merge. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#mobile-monitoring]
- Cookie table: `mautic_device_id` (1 year, used), `mtc_id` (session, deprecated 2.13 as third-party), `mautic_referer_id`, `mtc_sid` (deprecated), `mautic_session_id` (removed in 3). [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#cookies-used-by-mautic]

## 3. Custom fields

- Managed under Settings (cogwheel) > Custom Fields; object dropdown switches between Contact and Company. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#custom-fields] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#company-custom-fields]
- Icons: lock = core, cannot be removed; list = segment filter; asterisk = required; globe = publicly updatable. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#custom-fields]
- Since Mautic 5, default values of identifying fields cannot be edited. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#custom-fields]
- Field versus Tag decision helper: fields for personalisation and unique data; tags for behaviours and bulk labels. Custom fields have server capacity limits; tags do not. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#deciding-between-a-custom-field-and-a-tag]
- Creating a field adds a column; on large instances this locks the table and may time out, leaving the UI saying the column exists while updates fail. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#creating-custom-fields-via-a-command]
- `create_custom_field_in_background` (since Mautic 3) defers creation to `mautic:custom-field:create-column` and deletion to `mautic:custom-field:delete-column`; run daily off-peak. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#creating-custom-fields-via-a-command]
- `mautic:fields:analyse` (since 5.1, `-t` tabular) helps optimise VARCHAR sizes. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#analyzing-custom-fields-to-optimize-tables]
- `countries.json` and `regions.json` in `upload_dir` override country/region lists (since 5.1). [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#locally-defined-countries-and-regions]
- Gap: the docs do not list field types or explain required, short-form, index or unique options in detail. Use code-map.md.

## 4. Import

- CSV must be UTF-8; booleans `true`, `1`, `on`, `yes` are true; tags separated by `|`; ISO 8601 dates recommended. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#import-file-requirements]
- Headers matching field aliases auto-map; an option skips fields that already have a value. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#tips]
- Browser import needs the window open; background import (100 rows per batch) resumes from the last row and needs `mautic:import` in cron. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#background-import]
- Threshold in Configuration > Contact settings chooses browser versus background; 0 shows both buttons. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#automatic-import-type-configuration]
- `parallel_import_limit` default 1. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#parallel-imports]
- Statuses: Queued, In Progress, Imported, Failed (missing file or more than 2 hours unresponsive), Stopped, Manual, Delayed. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#import-job-status]
- "Create new Contacts?" No = update only; unmatched rows are ignored and listed. Same for companies. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#create-new-contacts-or-update-only]
- Stopping a background import takes effect after the current batch; cancelling a browser import removes the CSV and notifies the creator. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#how-to-stop-a-background-import] [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#how-to-cancel-an-import]
- Imported DNC is stored as a Manual Unsubscription. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#faq]
- The timeline shows an "Imported" event (since 2.9). [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html]

## 5. Managing contacts, duplicates and merge

- Quick Add shows fields marked available on short forms. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#quick-add]
- Export to CSV emails a link to the user (max one million contacts); Excel downloads directly. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#exporting-contact-lists]
- During tracking, contacts are auto-merged by unique identifiers and cookie; a form email merges into the contact with that email. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#managing-duplicates]
- The UI can create duplicates; since 2.1.0 it warns. The docs claim AND is the default duplicate operator (code: OR). [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#managing-duplicates]
- Batch actions: delete, export, change campaigns, categories, channels, owner, segments, stages, tags, find and replace, set DNC (email channel). Docs recommend a campaign for more than a few hundred contacts. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#batch-changes]
- Find and Replace is case sensitive and matches the stored value exactly. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#batch-changes]
- Manually adding or removing a contact to a segment stops filters applying to that contact in that segment. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#batch-changes]
- Merge: open the contact to keep > Merge > pick the duplicate, which is deleted. Docs rules: values fill only empty fields (code differs), owner inherited if empty, points combine, tags combine, primary company kept or inherited. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#merge-two-contacts]
- Timeline event types include Contact Created/Identified (By Source), Do Not Contact, Imported, Message Queue, UTM Tags Recorded and others; plugins add more. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#history]
- Notes: types General, Email, Call, Meeting; permissions based on note creator. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#note-permissions]

## 6. Tags, UTM tags

- Tags are created on first use; added manually, by batch, by tracking params, by campaign or form action "Modify Contact's Tags". [docs: https://docs.mautic.org/en/7.2/contacts/tags.html#adding-tags-to-contacts]
- Search `tag:name`, `!tag:name`, `tag:"tag name"`. [docs: https://docs.mautic.org/en/7.2/contacts/tags.html#searching-contacts-by-tags]
- Tracking `tags` param: comma-separated, `-` prefix removes. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tags]
- Five UTM params; inbound capture reads only what is in the URL. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_overview.html#understanding-utm-parameters]
- Record UTM Tags form action falls back to the referrer; forms also store URL, referrer, user agent and raw query. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_forms.html]
- Asset-download UTM data is separate and not segmentable; form-triggered downloads never carry UTM. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_asset_downloads.html#how-asset-download-utm-works]
- Segment UTM filters match any recorded value; campaign field-value conditions have a UTM group. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_segment_filters.html#create-segment-filters] [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_campaign_conditions.html#configure-conditions]
- REST: `POST /contacts/{id}/utm/add`, `POST /contacts/{id}/utm/{utmid}/remove`. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_overview.html#rest-api]

## 7. Preferences, DNC and frequency rules

- Contact > Preferences has tabs Channels and Frequency, Categories, Segments; unchecking a channel sets DNC for it. [docs: https://docs.mautic.org/en/7.2/contacts/preference_center.html#manage-contact-preferences]
- Per channel: frequency, pause period, one preferred channel; marketing messages send only the preferred channel's version. [docs: https://docs.mautic.org/en/7.2/contacts/preference_center.html#preferred-channels-and-frequency]
- Frequency rules exist for Email and SMS; contact rules override global ones; "Send to unsubscribed contacts" = Yes emails do not count. [docs: https://docs.mautic.org/en/7.2/contacts/frequency_rules.html]
- Preference Center landing pages, slot labels and unsubscribe behaviour are covered by mautic-emails and mautic-pages-and-tracking. [docs: https://docs.mautic.org/en/7.2/contacts/preference_center.html]

## 8. Companies

- Company name is the default unique identifier; any company field can become one; Company Settings choose AND/OR. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#company-duplicates]
- Docs say companies are identified strictly by name, city and country or state; forms need name, city and country fields. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#identifying-companies] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#through-a-form]
- Deleting a company: docs say the most recently attached company becomes primary. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#deleting-companies]
- Renaming updates only contacts where it is primary; `update_company_mapping_data_in_background` defers rename/delete to commands. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#processing-company-updates-in-the-background]
- The latest assigned company becomes primary in the contact profile. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#contact-profile]
- Company merge moves contacts and removes the merged company. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#merging-companies]

## 9. Search filters for contacts

`is:anonymous`, `is:unowned`, `is:mine`, `email:`, `segment:{alias}`, `name:`, `company:`, `owner:`, `ip:`, `ids:1,2`, `common:{alias} + {alias}`, `tag:`, `stage:`, `form:{alias}`, `email_sent:ID`, `email_read:ID`, `email_queued:ID`, `email_pending:ID`; operators `+`, `!`, quotes, parentheses, `OR`, `%`. [docs: https://docs.mautic.org/en/7.2/search/search_operators.html#contacts-search-filters] [docs: https://docs.mautic.org/en/7.2/search/search_operators.html#search-operators]

## 10. REST API (contacts, companies, fields, notes)

Cross-cutting: API off by default (`api_enabled`); `limit` default 30; `orderBy` in snake_case; PUT creates if missing and replaces data, PATCH updates and 404s if missing; create 201; `Mautic-Version` header. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html#edit-company]

Contacts: get, list (`where`, `order`, `select`), new, batch new, edit, batch edit, delete, batch delete, DNC add/remove (reason 1/2/3, default 3, channel default `email`), UTM add/remove, points plus/minus, point groups, list owners/fields, notes, segments, campaigns, activity, companies, devices. `overwriteWithBlank` defaults false. `events` is deprecated in favour of `activity`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html]

Companies: get, list (`total` is a string), new (`companyname` required), batch new (200 for duplicates), edit, delete, add/remove contact. The 8.0 docs add `POST /companies/batch/addcontacts` (present on the 7.x branch after 7.2.1, unreleased; [PR #16512]). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/companies.html] [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/companies.html#batch-add-contacts-to-companies]

Fields: `/fields/contact` and `/fields/company`; `isPubliclyUpdatable`, `isUniqueIdentifier`; delete returns 409 if a segment uses the field. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/fields.html]

Notes: `/notes`; `lead` and `text` required; type default `general`; own/other by note creator; create also needs contact view permission. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/notes.html]

Docs gaps: no statement of duplicate/merge behaviour on create, `company` field behaviour, or general batch limits. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/contacts.html]

## 11. Procedures

- Create a custom field: Settings > Custom Fields > New; choose object, type, group; save. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#adding-a-new-custom-field]
- Start an import: Contacts > actions > Import (`/s/contacts/import/new`); upload; set owner, segment, tags, create-new; map; import. [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html#how-to-start-an-import]
- Merge two contacts: open the contact to keep > Merge > select duplicate. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#merge-two-contacts]
- Export the change log: contact dropdown > export. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#exporting-the-change-log]
- Background company updates: set the parameter and schedule both company commands. [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#processing-company-updates-in-the-background]

## 12. 8.0 docs changes

The 8.0 docs branch mostly documents unreleased 7.x features merged after 7.2.1 (see `mautic-upgrades-and-versions/references/post-7.2.1-prs.md`): custom-field quick filters `is:indexed`/`is:unique`, Quick Add "Save & New", "No owner" in Change Owner, email confirmation before the Preference Center, "Contact's primary company" versus "Any associated company" segment filter groups, `POST /companies/batch/addcontacts`, and default email UTM values. [docs: https://docs.mautic.org/en/8.0/contacts/custom_fields.html#filtering-custom-fields-with-quick-filters] [docs: https://docs.mautic.org/en/8.0/contacts/manage_contacts.html#quick-add] [docs: https://docs.mautic.org/en/8.0/companies/companies_overview.html#company-segments]
