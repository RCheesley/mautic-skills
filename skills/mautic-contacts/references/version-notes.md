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
- No 6.x-specific contacts differences appear in the inputs. [unverified]

## 7.0 to 7.2.1

- 7.0: the API rate limiter cache (`api_rate_limiter_cache`) is no longer available. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/getting_started.html#api-rate-limiter-cache]
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
