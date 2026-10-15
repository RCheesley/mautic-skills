---
name: mautic-segments
description: "Mautic Segments (code name 'lead lists', LeadList): how dynamic and static Segments work, the filter DSL (glue, object, type, operator, properties), operators per field type, relative dates, company 'primary' vs 'any company' filters, behaviour filters (emails, page hits, tags, DNC, UTM, devices), manual add/remove membership, the rebuild command mautic:segments:update and its batching options, segment-membership filters and circular references, member count caching, performance, and the /api/segments API. Use whenever a task mentions segments, lead lists, contact lists, segment filters or operators, the 'Building' label, segment rebuild, mautic:segments:update, lead_lists_leads, ListModel, ContactSegmentService, ContactSegmentQueryBuilder, adding a custom segment filter, or asks why a contact is or is not in a segment, or touches app/bundles/LeadBundle/Segment/ or app/bundles/LeadBundle/Model/ListModel.php."
---
# Mautic Segments

## Scope
A Segment is a named set of Contacts (people records; code name "lead"). A dynamic Segment has filters and is
materialised by a cron command. A static Segment has no filters and changes only through explicit add/remove
actions. Segment membership feeds Campaigns, Segment Emails, SMS, Reports and Dynamic Content
[code: app/bundles/LeadBundle/Model/ListModel.php:383-633 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html].
Out of scope: contact fields and the contact search box (mautic-contacts); how Campaigns pull Segment members
(mautic-campaigns); Segment Email sending (mautic-emails); cron scheduling and locking in general
(mautic-cron-and-queues); the general REST conventions (mautic-rest-api).

## Expected behaviour (essentials)
- Membership is stored as rows in `lead_lists_leads` with two flags, `manually_added` and `manually_removed`. The rebuild command writes these rows. A dynamic Segment's filters are never evaluated live when a Segment is used [code: app/bundles/LeadBundle/Entity/ListLead.php:49-68 @7.x] [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:249 @7.x].
- Only `mautic:segments:update` (alias `mautic:segments:rebuild`) rebuilds Segments. The UI has no "rebuild now" action [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:38-168 @7.x].
- Since 5.0 the Segment rebuild no longer updates Campaign membership. `mautic:campaigns:update` must also run [code: UPGRADE-5.0.md:55 @7.x].
- A rebuild adds Contacts that match the filters and are not yet members. It then removes "orphans": rows with `manually_added = 0` whose Contact no longer matches [code: app/bundles/LeadBundle/Segment/ContactSegmentService.php:265-291 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#date-options].
- Manual adds come from the UI, API, Campaign/Form/Point actions, import and batch actions. They set `manually_added = 1`. The rebuild never removes those Contacts [code: app/bundles/LeadBundle/Model/LeadModel.php:960-973 @7.x] [code: app/bundles/LeadBundle/Segment/ContactSegmentService.php:281-282 @7.x].
- Manually removing a Contact that a filter added keeps the row with `manually_removed = 1`. The rebuild never re-adds that Contact, because the add query skips every Contact that already has a row [code: app/bundles/LeadBundle/Model/ListModel.php:868-876 @7.x] [code: app/bundles/LeadBundle/Segment/Query/ContactSegmentQueryBuilder.php:137-156 @7.x].
- Manually removing a manually added row deletes the row. Manually adding a filter-added or manually removed row flips it to `manually_added = 1, manually_removed = 0` [code: app/bundles/LeadBundle/Model/ListModel.php:727-741 @7.x].
- Glue: the first filter's glue is always `and`. An `or` starts a new AND-group, so `A and B or C and D` means `(A AND B) OR (C AND D)` [code: app/bundles/LeadBundle/Entity/LeadList.php:511-519 @7.x] [code: app/bundles/LeadBundle/Segment/Query/QueryBuilder.php:386-426 @7.x].
- Consecutive `or` filters with `=` on the same field are merged into one `in` filter. Date filters are never merged [code: app/bundles/LeadBundle/Segment/ContactSegmentFilterFactory.php:106-176 @7.x].
- UI labels differ from operator keys. Label "contains" is operator `like`: the value is wrapped in `%…%` unless it already contains `%`. Label "in list" is operator `contains`: the value is always wrapped in `%…%` [code: app/bundles/LeadBundle/Translations/en_US/messages.ini:765 @7.x] [code: app/bundles/CoreBundle/Translations/en_US/messages.ini:491 @7.x] [code: app/bundles/LeadBundle/Segment/Decorator/BaseDecorator.php:92-102 @7.x].
- On contact fields, `!=`, `!like`, `!in` and `!between` also match NULL. `!regexp` deliberately does not match NULL [code: app/bundles/LeadBundle/EventListener/SegmentOperatorQuerySubscriber.php:29-112 @7.x] [code: app/bundles/LeadBundle/EventListener/SegmentOperatorQuerySubscriber.php:185 @7.x].
- `empty` means `IS NULL OR = ''`. On date columns it means `IS NULL` only [code: app/bundles/LeadBundle/Segment/ContactSegmentFilter.php:218-221 @7.x].
- On behaviour (foreign-table) filters, `!in` is `NOT EXISTS`. A Contact that has the excluded tag plus other tags is excluded [code: app/bundles/LeadBundle/Segment/Query/Filter/ForeignValueFilterQueryBuilder.php:19-181 @7.x].
- Multiselect `in`/`!in`/`in_all`/`!in_all` are rewritten to REGEXP matches against the pipe-separated stored value. On single-value fields, `in_all` with more than one value never matches [code: app/bundles/LeadBundle/EventListener/SegmentOperatorQuerySubscriber.php:82-169 @7.x].
- Relative date strings (`today`, `last month`, `-1 week`, `anniversary`) are re-evaluated at each rebuild. Membership drifts only as often as the cron runs [code: app/bundles/LeadBundle/Segment/Decorator/Date/DateOptionFactory.php:34-99 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters].
- Named ranges with `=` become `LIKE 'YYYY-MM-DD%'`-style prefixes. Weeks become `BETWEEN monday 00:00:00 AND sunday 23:59:59`. With `gt`/`lte` the comparison uses the last second of the range [code: app/bundles/LeadBundle/Segment/Decorator/Date/DateOptionAbstract.php:88-107 @7.x].
- `inLast`/`inNext` take `{interval, unit}` and cover whole days: `BETWEEN '<now-N> 00:00:00' AND '<today> 23:59:59'`. "Today" is taken in UTC. Only positive whole numbers are accepted [code: app/bundles/LeadBundle/Segment/Query/Expression/ExpressionBuilder.php:126-147 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#in-the-last-and-in-the-next].
- Timezones: for `datetime` fields "now" is UTC. For `date` fields "now" uses the `default_timezone` setting [code: app/bundles/LeadBundle/Segment/Decorator/Date/TimezoneResolver.php:20-38 @7.x].
- A Segment-membership filter (`leadlist`) reads the referenced Segment's materialised rows (`manually_removed = 0`), not its filters. The command therefore rebuilds the referenced Segments first, recursively [code: app/bundles/LeadBundle/Services/ContactSegmentFilterDictionary.php:142-147 @7.x] [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:106-157 @7.x].
- Circular Segment references are rejected in three places: on form save, at query build, and in the command, which skips the edge [code: app/bundles/LeadBundle/Form/Type/ListType.php:146 @7.x] [code: app/bundles/LeadBundle/Segment/Query/ContactSegmentQueryBuilder.php:255-277 @7.x] [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:202-210 @7.x].
- A Segment that another Segment filters on, or that a Campaign uses as a source, cannot be unpublished or deleted. The API returns 422 on such an unpublish [code: app/bundles/LeadBundle/EventListener/SegmentSubscriber.php:73-115 @7.x].
- Unpublished Segments are never rebuilt, and their existing memberships stay untouched [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:242-244 @7.x].
- `--max-contacts` caps adds plus removes per Segment per run. A capped run leaves `lastBuiltDate` NULL, so the Segment keeps showing "Building" until a later run finishes [code: app/bundles/LeadBundle/Model/ListModel.php:591-633 @7.x].
- "Building" is shown while `needsRebuild()` is true: the Segment has never been built, or it was modified at or after `lastBuiltDate` [code: app/bundles/LeadBundle/Entity/LeadList.php:329-342 @7.x].
- The rebuild sleeps `batch_sleep_time` (default 1 s) before every batch of `--batch-limit` (default 300) Contacts, in both the add and remove phases [code: app/bundles/LeadBundle/Model/ListModel.php:923-939 @7.x].
- The rebuild fires `LEAD_LIST_BATCH_CHANGE` per batch, not `LEAD_LIST_CHANGE` per Contact. Timeline entries and webhooks handle both events [code: app/bundles/LeadBundle/Model/ListModel.php:474-479 @7.x] [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:39-40 @7.x].
- If a filter references a deleted field or table, the rebuild silently returns 0 and does not change membership [code: app/bundles/LeadBundle/Model/ListModel.php:401-412 @7.x].
- Member counts come from a cache (`segment.<id>.lead`, TTL `segment_api_count_cache_ttl` = 43200 s). Single adds and removes update the cache incrementally [code: app/bundles/LeadBundle/Helper/SegmentCountCacheHelper.php:22-116 @7.x].
- Deleting a Segment is a soft delete followed by an immediate hard delete. With `delete_segment_in_background = true` the hard delete waits for `mautic:segment:delete` [code: app/bundles/LeadBundle/Model/ListModel.php:194-215 @7.x].
- The 7.x branch (after 7.2.1, unreleased; [PR #15800]) offers two company filter groups; 7.2.1 has only `company`. `company` matches the primary company only, and its negative operators also match Contacts with no primary company. `company_all` matches any associated company and never matches Contacts without a company [code: app/bundles/LeadBundle/Segment/Query/Filter/AbstractCompanyRelationValueFilterQueryBuilder.php:15-86 @7.x].

## Where it lives
| Concern | Path(s) |
|---|---|
| Entities / tables | `app/bundles/LeadBundle/Entity/LeadList.php` (`lead_lists`), `Entity/ListLead.php` (`lead_lists_leads`), repositories `LeadListRepository.php`, `ListLeadRepository.php` |
| Model | `app/bundles/LeadBundle/Model/ListModel.php` (rebuild, add/remove, counts, dependencies); `Model/SegmentActionModel.php` (batch) |
| Query engine | `app/bundles/LeadBundle/Segment/` (`ContactSegmentService`, `ContactSegmentFilterFactory`, `Decorator/`, `Query/`, `Query/Filter/*QueryBuilder`, `OperatorOptions`) |
| Filter dictionary | `app/bundles/LeadBundle/Services/ContactSegmentFilterDictionary.php` |
| Filter choices / operators | `EventListener/FilterOperatorSubscriber.php`, `TypeOperatorSubscriber.php`, `SegmentOperatorQuerySubscriber.php`, `Entity/OperatorListTrait.php` |
| Events | `app/bundles/LeadBundle/LeadEvents.php` (`LIST_*`, `LEAD_LIST_*`, `SEGMENT_*`) |
| Commands | `Command/UpdateLeadListsCommand.php`, `SegmentCountCacheCommand.php`, `DeleteLeadListsCommand.php`, `SegmentStatCommand.php` |
| UI / routes | `Controller/ListController.php`, `BatchSegmentController.php`, `AjaxController.php`; routes in `Config/config.php:23-38`, `:141-144` |
| API | `Controller/Api/ListApiController.php` (`/api/segments`); API Platform resource on `LeadList.php:29-48` |
| Config params | `Config/config.php:336-371` (`delete_segment_in_background`, `segment_api_count_cache_ttl`, `segment_rebuild_time_warning`, `segment_build_time_warning`, `update_segment_contact_count_in_background`) |
| Permissions | `Security/Permissions/LeadPermissions.php` (`lead:lists:*`) |
| Tests | `app/bundles/LeadBundle/Tests/{Segment,Command,Model,Entity,Controller}` |

Full detail: references/code-map.md [code: app/bundles/LeadBundle/Config/config.php:23-371 @7.x].

## How to change or extend it
- Add a filter in two steps. First register the choice on `LIST_FILTERS_CHOICES_ON_GENERATE` (`addChoice($object, $alias, [...])`). Then map it to SQL on `SEGMENT_DICTIONARY_ON_GENERATE` (`addTranslation($alias, ['type' => <builder service id>, 'foreign_table', 'field', ...])`). Copy the Point Group pattern [code: app/bundles/PointBundle/EventListener/SegmentFilterSubscriber.php:38-80 @7.x].
- A custom query builder implements `FilterQueryBuilderInterface` and is fetched from the container by `getServiceId()`. Use `$queryBuilder->addLogic($expr, $filter->getGlue())`, never `andWhere()`, or OR-groups break [code: app/bundles/LeadBundle/Segment/ContactSegmentFilterFactory.php:92-96 @7.x] [code: app/bundles/LeadBundle/Segment/Query/QueryBuilder.php:382-386 @7.x].
- For a new operator, register it on `LIST_FILTERS_OPERATORS_ON_GENERATE` and attach it per type on `COLLECT_OPERATORS_FOR_FIELD_TYPE`. Emit its SQL on `LIST_FILTERS_OPERATOR_QUERYBUILDER_ON_GENERATE` with `addExpression()` + `stopPropagation()` [code: app/bundles/LeadBundle/Event/SegmentOperatorQueryBuilderEvent.php:47-72 @7.x].
- To take over a filter completely, use `LIST_FILTERS_ON_FILTERING` (`setSubQuery()` + `setFilteringStatus(true)`). To sync external data before a rebuild, use `LIST_PRE_PROCESS_LIST` [code: app/bundles/LeadBundle/Segment/Query/ContactSegmentQueryBuilder.php:227-242 @7.x].
- Keep stored filters backward compatible. Saved Segments use the legacy top-level `filter`/`display` keys and the legacy `in_all`/`!in_all` operators, and both must still load [code: app/bundles/LeadBundle/Entity/LeadList.php:448-468 @7.x] [code: app/bundles/LeadBundle/Form/Type/FilterType.php:66-76 @7.x].
- `filters` is a PHP-serialised Doctrine `array`. Dependency lookups use `LIKE '%s:8:"leadlist"%'`. Changing the storage format breaks these lookups [code: app/bundles/LeadBundle/Model/ListModel.php:1244 @7.x].
- A new entity column needs a migration, the `loadApiMetadata` groups, the API Platform `segment:read/write` groups and translations [code: app/bundles/LeadBundle/Entity/LeadList.php:29-48 @7.x] [code: app/bundles/LeadBundle/Entity/LeadList.php:201-224 @7.x].
- For code that must run on 7.x and 8.x, subscribe by event class as well as by the string constant. See Version notes and mautic-upgrades-and-versions.

## How to test it
- Use `Mautic\CoreBundle\Test\MauticMysqlTestCase` for anything touching SQL. Create Contacts, save a `LeadList` with filters, run `$this->testSymfonyCommand('mautic:segments:update', ['-i' => $id])`, then assert on `lead_lists_leads` [code: app/bundles/LeadBundle/Tests/Command/UpdateLeadListCommandFunctionalTest.php @7.x].
- Copy from:
  - `app/bundles/LeadBundle/Tests/Command/UpdateLeadListCommandFunctionalTest.php` (include/exclude matrices, `--max-contacts`).
  - `app/bundles/LeadBundle/Tests/Segment/ContactSegmentServiceFunctionalTest.php` (company primary vs any, limiters).
  - `app/bundles/LeadBundle/Tests/Command/SegmentFilterWithRelativeTimeFunctionalTest.php` (timezones).
  - `app/bundles/LeadBundle/Tests/Segment/Query/Filter/ForeignValueFilterQueryBuilderTest.php` (SQL unit tests).
  - `app/bundles/LeadBundle/Tests/Controller/Api/ListApiControllerFunctionalTest.php` (API, 422 guards).
  - `app/bundles/LeadBundle/Tests/Command/UpdateLeadListsCommandCircularDependencyTest.php`.
- A good regression test asserts both who is in and who is out. Include a Contact with NULL in the field, one manually added and one manually removed. For date filters, freeze or compute "now" in the same timezone as the code.

Full detail: references/test-patterns.md.

## Version notes
- 7.0 removed `SegmentReferenceFilterQueryBuilder`. The `leadlist` filter uses `ForeignValueFilterQueryBuilder` [code: UPGRADE-7.0.md:62 @7.x].
- The 7.x branch has "Any associated company" (`company_all`) filters, after 7.2.1 and not yet released [PR #15800]. The 7.2 user docs still describe primary-company only, and the 8.0 docs describe both [code: app/bundles/LeadBundle/EventListener/FilterOperatorSubscriber.php:122-126 @7.x] [docs: https://docs.mautic.org/en/8.0/segments/manage_segments.html#configuring-segment-filters].
- 8.x (snapshot) dispatches Segment events by class: `ListPreSaveEvent`, `ListPostSaveEvent`, `ListPreDeleteEvent`, `ListDeleteEvent`, `ListPostDeleteEvent`, `ListPreUnpublishEvent`, `ListBatchChangeEvent`, `LeadListFiltersChoicesEvent`, `LeadListFilteringEvent`, `SegmentDictionaryGenerationEvent` and others. Listeners keyed only on the old string names never fire [PR #17218] [PR #17545] [PR #17625].
- 8.x removes `OperatorOptions::IN`/`NOT_IN` and `OperatorListTrait::getFilterExpressionFunctions()`. `LeadListEvent` is `abstract`. `Segment\Query\QueryBuilder::setParameter()` rejects `:`-prefixed keys [code: UPGRADE-8.0.md @8.x].
- 8.x removes the `file_lock` lock mode. `--lock_mode=file_lock` now errors [code: UPGRADE-8.0.md @8.x].
- `company_all` is not yet on the 8.x branch. It arrives with the next 7.x → 8.x forward merge. Do not treat it as removed.

Full detail: references/version-notes.md.

## Pitfalls
- A Contact that was manually removed never comes back through filters. Only a manual add restores it. This is intended [code: app/bundles/LeadBundle/Segment/Query/ContactSegmentQueryBuilder.php:137-156 @7.x].
- A Segment-membership filter on a Segment that has not been rebuilt sees stale rows. Run the command without `--list-id`, or with the dependent id, so that dependencies rebuild first [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:110-112 @7.x].
- A second `mautic:segments:update` with the same lock key prints "Script in progress" and exits 0, not failure [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:114-116 @7.x].
- Filters on a deleted custom field make the rebuild return 0 without an error in the output. The form also hides such filters [code: app/bundles/LeadBundle/Form/Type/FilterType.php:99-103 @7.x].
- With default settings a 300 000-Contact Segment spends at least 1 000 s sleeping. Raise `--batch-limit` or lower `batch_sleep_time` for large installs [code: app/bundles/LeadBundle/Model/ListModel.php:443 @7.x].
- `removeLead` decrements the count cache even when the row was kept, which can cause count drift until the next recount [code: app/bundles/LeadBundle/Model/ListModel.php:868-883 @7.x].
- `lead:list:count-cache-update` recounts only published Segments [code: app/bundles/LeadBundle/Command/SegmentCountCacheCommand.php:34-49 @7.x].
- Docs say "contains/doesn't contain are not supported for date fields", yet code offers `like` and `contains` for date types [code: app/bundles/LeadBundle/Entity/OperatorListTrait.php:12-126 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#operators].
- The REST docs name the bulk-add body key `contactIds`, but code reads `ids`. Use `ids[]` [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:186 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#add-contacts-to-segment].
- Open question: the REST docs say `isGlobal` defaults to "restricted" when not set, but the entity default is `true`. The value after a POST without `isGlobal` was not verified [code: app/bundles/LeadBundle/Entity/LeadList.php:105 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#get-segment].
- Open question: the docs' "Public Segment = Yes" requirement for the Campaign "Modify Contact's Segments" action names no existing field. The likely gate is `isGlobal` ("Visible to other Users") via `getUserLists()` [unverified] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#using-a-campaign-action].
- Open question: named date ranges (`today`, `this week`) on `datetime` fields in a non-UTC install use local-time formatting, while relative intervals use UTC. Correctness is not covered by tests [code: app/bundles/LeadBundle/Segment/Decorator/Date/DateOptionAbstract.php:106 @7.x].

## Related skills
- mautic-contacts: contact fields, the contact search box (`segment:alias`), merge, import, batch actions.
- mautic-campaigns: Segment-sourced Campaigns, `mautic:campaigns:update`, the "Modify Contact's Segments" action.
- mautic-emails: Segment (broadcast) Emails, pending counts, include/exclude Segments.
- mautic-points-and-stages: Point Group filters, Point Trigger Segment actions, Stage filter.
- mautic-cron-and-queues: cron cadence, `ModeratedCommand` locking, background workers.
- mautic-rest-api: authentication, envelopes, pagination for `/api/segments`.
- mautic-plugin-development: writing custom Segment filters, operators and decorators.
- mautic-testing: test base classes, fixtures, running the suite.
- mautic-upgrades-and-versions: 7.x → 8.x event-by-class migration.

## Reference files
- references/behaviour.md — full numbered behaviour spec, including the operator-by-field-type table; open it for any "is this a bug?" question.
- references/code-map.md — entities, columns, services, events, routes, commands, parameters, permissions.
- references/docs-digest.md — what docs.mautic.org and devdocs say, UI label ↔ operator mapping, procedures.
- references/test-patterns.md — base classes, fixtures, test skeletons for filters, rebuild and API.
- references/version-notes.md — 5.x/6.x history, 7.x minors, the 8.x delta for Segments.
- references/pr-history.md — not yet generated; PR-derived history is added in a later pass.
