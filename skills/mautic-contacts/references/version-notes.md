# Contacts version notes

## History that still explains behaviour

- 2.1.0: the UI warns about contacts with the same unique identifier; it does not block them. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#managing-duplicates]
- 2.9: imports appear on the contact timeline as "Imported". [docs: https://docs.mautic.org/en/7.2/contacts/import_contacts.html]
- 2.12: `LeadModel::isContactable()` deprecated in favour of the `DoNotContact` model. [code: app/bundles/LeadBundle/Model/LeadModel.php:2437 @7.x]
- 2.13: the third-party `mtc_id` cookie deprecated; `mautic_device_id` is the tracking cookie. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#cookies-used-by-mautic]
- 3: `create_custom_field_in_background` added; `mautic_session_id` cookie removed. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#creating-custom-fields-via-a-command] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#cookies-used-by-mautic]

## 5.x and 6.x

- 5.0: default values of identifying fields can no longer be edited. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#custom-fields]
- 5.1: `mautic:fields:analyse` and locally defined `countries.json`/`regions.json`. [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#analyzing-custom-fields-to-optimize-tables] [docs: https://docs.mautic.org/en/7.2/contacts/custom_fields.html#locally-defined-countries-and-regions]
- The local config path moved from `app/config/local.php` to `config/local.php` in 5; the contacts docs still mix both. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html] [docs: https://docs.mautic.org/en/7.2/companies/companies_overview.html#processing-company-updates-in-the-background]
- 5.0: `mtc_sid` is no longer set; only `mtc_id` remains (BC break). LeadBundle views moved to Twig, so plugin view overrides must move too. [PR #12440] [PR #11793]
- 5.0: unique identifiers are validated server-side on the full form, Quick Add and the API. `POST /api/contacts/new` merges keep stage and owner when not sent. `mautic:contacts:deduplicate` gained `--batch` and `--processes`. [PR #11716] [PR #12078] [PR #11697]
- 5.0: background CSV export (`contact_export_in_background`, `mautic:contacts:scheduled_export`); Excel export stays immediate. [PR #11272]
- 5.1: text fields get a maximum length and an indexable flag; the `html` field type arrives; single-company mode (`contact_allow_multiple_companies`); a separate Export permission; `contact_api_count_cache_ttl`. [PR #13319] [PR #13428] [PR #12219] [PR #12884] [PR #13288]
- 5.2: DNC-only changes no longer bump `date_modified`/`modified_by`; select values outside the options become NULL on every save; textarea "Allow HTML" removed by migration; the unique-identifier flag disabled for company fields. [PR #13994] [PR #14183] [PR #13926] [PR #14236]
- 5.x: the boolean field's third NULL option disappeared between 4.x and 5.x and was not restored; a boolean default "No" stores `0` from 5.2.5. [PR #14805]
- 6.0: `date_modified` is set on create and back-filled from `date_added` by migration. [PR #14433]
- 6.0: fields marked searchable match plain search without `alias:` ("Add to Search Index"). [PR #14393]
- 6.0: import rows are checked against the permissions of the user who last modified the import; `mautic.pre_batch_save`/`post_batch_save` events; `where[]` values are no longer entity-encoded. [PR #14554] [PR #14503] [PR #14550]
- 6.0: `LeadEvent` is final with `getLead(): Lead`; `FieldModel::getUniqueIdentiferFields` removed (UPGRADE-6.0). [PR #13842] [PR #14144]

## 7.0 to 7.2.1

- 7.0: the API rate limiter cache (`api_rate_limiter_cache`) is no longer available. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-rate-limiter-cache]
- 7.0: field `charLengthLimit` is editable after creation and shortening below stored data is rejected; background field delete with `mautic:custom-field:delete-column`; `dnc:` search; `contact_export_limit`; "Identify visitor by tracking URL" removed (BC break); `LeadGetCurrentEvent`. [PR #14762] [PR #14679] [PR #14952] [PR #14691] [PR #14974] [PR #15556]
- 7.0: batch API endpoints resolve merged-away ids to the winner. [PR #15447]
- 7.1: the unique-identifier flag is re-enabled for company fields; deleting a field used by a segment returns 409 through the API; `campaign:` search. [PR #15784] [PR #15882] [PR #15727]
- 7.2.0: companies are soft-deleted with cron cleanup; merge moves company links; `lead:notes` permission; `viewown` API fallback to unowned contacts the user created; import "Create new Contacts?"; tag merge events; API keeps number fractions. [PR #16176] [PR #16247] [PR #16067] [PR #16022] [PR #17176] [PR #15331] [PR #16591]
- 7.2.1: company names with `&` decoded once; "Import Another" follows the object type. [PR #17266] [PR #17221]
- 7.2: `AjaxController::addLeadUtmTagsAction` deprecated. [code: app/bundles/LeadBundle/Controller/AjaxController.php:631 @7.x]
- 7.x after 7.2.1, not yet released (documented in the 8.0 docs branch, not yet on the 8.x code branch): `POST /api/companies/batch/addcontacts` [PR #16512], "Any associated company" segment filters [PR #15800], Quick Add "Save & New" and "No owner" in batch Change Owner [PR #16849], custom-field quick filters [PR #16872], email confirmation before the Preference Center [PR #16870]. [code: app/bundles/LeadBundle/Controller/Api/CompanyApiController.php:121-153 @7.x] [docs: https://docs.mautic.org/en/8.0/contacts/manage_contacts.html#quick-add] [docs: https://docs.mautic.org/en/8.0/companies/companies_overview.html#company-segments]

## 8.x delta (unreleased, branch at 11599729491)

Topology warning: 7.2.1 and the later unreleased 7.x work are not merged into 8.x yet, so 7.x-only features are missing from 8.x code but are expected after the next forward merge. Do not document them as removed.

- Platform: PHP 8.4, Symfony 8.1, Doctrine ORM 3.7 and DBAL 4.4; PHPUnit 13 with `dg/bypass-finals`. Custom-field DBAL writes and repository code must follow the Doctrine 3/4 API (`ArrayParameterType`, `getEntityManager()` instead of `$_em`).
- Events are dispatched by class. 56 `LeadEvents` constants were removed. Subscribe to concrete classes: `LeadPreSaveEvent`, `LeadPostSaveEvent`, `LeadPreDeleteEvent`, `LeadPostDeleteEvent`, `LeadIdentifiedEvent`, `LeadPreMergeEvent`, `LeadPostMergeEvent`, `FieldPreSaveEvent`/`FieldPostSaveEvent`/`FieldPreDeleteEvent`/`FieldPostDeleteEvent`, `NotePreSaveEvent` etc., `ImportPreSaveEvent` etc., `TagPreMergeEvent` etc., `CompanyPreSaveEvent`, `CompanySoftDeleteEvent`, `CompanyPreMergeEvent`/`CompanyPostMergeEvent`, `DevicePreSaveEvent` etc., `ContactIdentificationEvent` for clickthrough identification, `LeadChangeEvent` for `CURRENT_LEAD_CHANGED`.
- Kept constants (`LEAD_POST_SAVE`, `LEAD_POST_DELETE`, `LEAD_POINTS_CHANGE`, `LEAD_COMPANY_CHANGE`, `COMPANY_POST_SAVE`, `COMPANY_POST_DELETE`, `CHANNEL_SUBSCRIPTION_CHANGED`) remain as webhook type ids; a listener keyed on the string still compiles but may never fire. Key on the class.
- `LEAD_UTMTAGS_ADD`, `IMPORT_ON_*`, `LEAD_FIELD_PRE_*_COLUMN*`, `TIMELINE_ON_GENERATE`, `LEAD_BUILD_SEARCH_COMMANDS` constants removed; use `LeadUtmTagsEvent`, `ImportInitEvent`/`ImportMappingEvent`/`ImportProcessEvent`/`ImportValidateEvent`, `Field\Event\{Add,Update,Delete}Column[Background]Event`, `LeadTimelineEvent`, `LeadBuildSearchEvent`.
- `DoNotContactAddEvent::ADD_DONOT_CONTACT` and `DoNotContactRemoveEvent::REMOVE_DONOT_CONTACT` constants removed; the event classes remain.
- `LeadEvent`, `CompanyEvent`, `TagEvent`, `LeadNoteEvent`, `LeadDeviceEvent`, `ImportEvent`, `LeadFieldEvent`, `LeadMergeEvent`, `CompanyMergeEvent`, `TagMergeEvent`, `SaveBatchLeadsEvent`, `ContactExportSchedulerEvent` are abstract or non-final parents; type-hint the parent, subscribe to the concrete class.
- Removed APIs: `LeadModel::isContactable()` (use `DoNotContact::isContactable()`), `FieldModel::getFieldList()` (use `Field\FieldList`), `AjaxController::addLeadUtmTagsAction()`, `LeadModel::getTagRepository()`, `CompanyModel::getCompanyLeadRepository()`, `OperatorOptions::IN/NOT_IN`, `FieldDeleteDispatcher::dispatchPreDeleteEvent()`, `Helper\CampaignEventHelper`, `MauticTagManagerBundle\Entity\Tag` (use `LeadBundle\Entity\Tag`).
- `IdentifyCompanyHelper` becomes an autowired service with instance methods `identifyLeadsCompany($data, $lead)` and `findCompany()`.
- `SchemaDefinition` gives unique-identifier columns an explicit length of 255 (7.x: 191).
- ~45 public LeadBundle methods gain native parameter types (for example `ContactTracker::setUseSystemContact(bool)`, `CompanyModel::companyMerge(Company, Company): Company`, `LeadModel::getLead(int)`).
- Campaign actions in LeadBundle run only through `ON_CAMPAIGN_BATCH_ACTION` and `PendingEvent`.
- The Clearbit plugin (a `LEAD_POST_SAVE` enrichment listener in 7.x) is removed.

Source for the whole 8.x section: the 7.x to 8.x delta analysis (UPGRADE-8.0.md@8.x and three-dot diff), PRs #17218, #17545, #17077, #17625 (LeadBundle events), #17260 (IdentifyCompanyHelper), #17247, #17248 (repository getters), #17361 (Doctrine 3, TagManager Tag), #17785 (Clearbit). [PR #17218] [PR #17545] [PR #17260] [PR #17247] [PR #17248] [PR #17361] [PR #17785]

### Writing code that works on 7.x and 8.x

Register both keys in `getSubscribedEvents()`, guarded:

```php
$events = [];
if (class_exists(\Mautic\LeadBundle\Event\LeadPostSaveEvent::class)) {   // 8.x
    $events[\Mautic\LeadBundle\Event\LeadPostSaveEvent::class] = ['onPostSave', 0];
}
if (defined(\Mautic\LeadBundle\LeadEvents::class.'::LEAD_POST_SAVE')) {   // 7.x string dispatch
    $events[\Mautic\LeadBundle\LeadEvents::LEAD_POST_SAVE] = ['onPostSave', 0];
}
return $events;
```

Type-hint `LeadEvent` in the handler. On 8.x the `LEAD_POST_SAVE` constant still exists but nothing dispatches it as a name, so the second key is inert there. [PR #17218]

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
