# Segments — behaviour specification (Mautic 7.x)

All statements describe 7.2.1 (commit 419a08a9b35) unless marked. Code paths are repository-relative.

## Contents
1. Data model and terms
2. Filter DSL and glue
3. Operators: key ↔ UI label ↔ SQL
4. Operators offered per field type (full table)
5. Value preparation and NULL semantics
6. Date filters and relative dates
7. Behaviour (foreign-table) filters
8. Company filters
9. Membership: manual add / remove
10. Rebuild algorithm and the command
11. Segment-membership filters, dependencies, circularity
12. Counts and caches
13. Lifecycle: save, publish, delete, clone, visibility
14. Events, timeline, webhooks
15. REST API
16. Performance
17. Open questions and doc discrepancies

## 1. Data model and terms

1.1 A Segment is a `LeadList` entity in table `lead_lists`. It has `name`, `alias`, `public_name`, `description`, `category_id`, a serialised `filters` array, `is_global`, `is_preference_center`, `last_built_date`, `last_built_time`, a soft-delete `deleted`, `uuid` and the published/created/modified columns [code: app/bundles/LeadBundle/Entity/LeadList.php:139-196 @7.x].

1.2 Membership is the table `lead_lists_leads`. Its primary key is (`leadlist_id`, `lead_id`). It has `date_added`, `manually_added` and `manually_removed`. Both foreign keys use `ON DELETE CASCADE` [code: app/bundles/LeadBundle/Entity/ListLead.php:49-68 @7.x].

1.3 "Dynamic" Segment means one with filters. "Static" Segment means one with no filters, where membership comes only from explicit add/remove. Both types accept manual changes [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#static-segments] [code: app/bundles/LeadBundle/Segment/ContactSegmentService.php:32-41 @7.x].

1.4 `needsRebuild()` returns false when the Segment has no filters or is unpublished. Otherwise it returns true when the Segment was never built or when `dateModified >= lastBuiltDate` [code: app/bundles/LeadBundle/Entity/LeadList.php:329-342 @7.x].

1.5 `getFilters()` back-fills the legacy `filter`/`display` keys from `properties`. It also forces the first filter's glue to `and` [code: app/bundles/LeadBundle/Entity/LeadList.php:320-327 @7.x] [code: app/bundles/LeadBundle/Entity/LeadList.php:448-468 @7.x] [code: app/bundles/LeadBundle/Entity/LeadList.php:511-519 @7.x].

## 2. Filter DSL and glue

2.1 Each filter is an array with these keys [code: app/bundles/LeadBundle/Segment/ContactSegmentFilterCrate.php:54-67 @7.x]:
- `glue`: `and` or `or`.
- `field`: the field alias.
- `object`: `lead` (the default), `company`, `company_all` or `behaviors`.
- `type`: the field type, or a special type such as `leadlist`, `tags`, `datetime`.
- `operator`.
- `properties`: `{filter, display?}`.

2.2 The API converts the legacy top-level `filter`/`display` keys into `properties` [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:75-94 @7.x].

2.3 The first filter's glue is always treated as `and` [code: app/bundles/LeadBundle/Entity/LeadList.php:511-519 @7.x].

2.4 Consecutive filters are ANDed. An `or` filter closes the current AND-group and opens a new one, so `A and B or C and D` = `(A AND B) OR (C AND D)`. There is no explicit parenthesis support [code: app/bundles/LeadBundle/Segment/Query/QueryBuilder.php:386-426 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters].

2.5 Before SQL is built, consecutive `or`-glued `=` filters on the same object and field merge into one `in` filter. An `and` filter that follows such a group pops the last OR-ed filter back out. Date and datetime filters are never merged [code: app/bundles/LeadBundle/Segment/ContactSegmentFilterFactory.php:106-176 @7.x].

2.6 Every query selects from `leads l`. It prefers a read replica when one is configured. Parameter and alias names are sequential: `par0`, `par1`, … [code: app/bundles/LeadBundle/Segment/Query/ContactSegmentQueryBuilder.php:46-59 @7.x] [code: app/bundles/LeadBundle/Segment/RandomParameterName.php:20-27 @7.x].

2.7 An unknown operator throws `Exception('Dunno how to handle operator …')`. Unsupported operators in the company/complex builder throw `UnsupportedFilterOperatorException` [code: app/bundles/LeadBundle/Segment/Query/Filter/BaseFilterQueryBuilder.php:44-46 @7.x] [code: app/bundles/LeadBundle/Segment/Query/Filter/ComplexRelationValueFilterQueryBuilder.php:180 @7.x].

2.8 A filter on a column that no longer exists throws `FieldNotFoundException`. A missing table throws `TableNotFoundException`. The rebuild catches both and returns 0 without changes, and logs only the table case [code: app/bundles/LeadBundle/Segment/ContactSegmentFilter.php:43-60 @7.x] [code: app/bundles/LeadBundle/Model/ListModel.php:401-412 @7.x].

## 3. Operators: key ↔ UI label ↔ SQL

Keys and expressions come from `OperatorOptions` [code: app/bundles/LeadBundle/Segment/OperatorOptions.php:9-194 @7.x]. Labels come from en_US translations [code: app/bundles/LeadBundle/Translations/en_US/messages.ini:758-784 @7.x] [code: app/bundles/CoreBundle/Translations/en_US/messages.ini:477-493 @7.x].

| Key | Segment UI label | Expression | Notes |
|---|---|---|---|
| `=` | is equal to | eq | |
| `!=` | is not equal to | neq | NULL matches on contact fields |
| `gt` | greater than (dates: "more recent than") | gt | |
| `gte` | greater than or equal ("equal or more recent than") | gte | |
| `lt` | less than ("older than") | lt | |
| `lte` | less than or equal ("equal or older than") | lte | |
| `empty` | is empty | isNull / `= ''` | |
| `!empty` | is not empty | isNotNull and `!= ''` | |
| `like` | **contains** | like | `%v%` unless the value already has `%` |
| `!like` | doesn't contain | notLike | |
| `contains` | **in list** | like | always `%v%` |
| `startsWith` | starts with | like | `v%` |
| `endsWith` | ends with | like | `%v` |
| `in` | includes any of | in | string split on `|` |
| `!in` | excludes any of | notIn | |
| `in_all` | includes all of | — | legacy except multiselect/behaviours |
| `!in_all` | excludes all of | — | as above |
| `regexp` | matches pattern | regexp | MySQL POSIX regex, validated by `DbRegex` |
| `!regexp` | does not match pattern | notRegexp | no NULL branch |
| `between` / `!between` | (hidden) | between / notBetween | not offered in UI |
| `inLast` / `inNext` | in the last / in the next | inLast / inNext | segment context only |
| `date` | (hidden) | — | internal |

3.1 `ContactSegmentFilterOperator::fixOperator` maps the stored key to its expression [code: app/bundles/LeadBundle/Segment/ContactSegmentFilterOperator.php:21-32 @7.x].

3.2 `OperatorOptions::IN`/`NOT_IN` are deprecated aliases of `INCLUDING_ANY`/`EXCLUDING_ANY`, with the same values [code: app/bundles/LeadBundle/Segment/OperatorOptions.php:33-41 @7.x].

3.3 `in_all`/`!in_all` are not offered for new filters on standard fields. They stay selectable on saved filters that already use them [code: app/bundles/LeadBundle/Form/Type/FilterType.php:66-76 @7.x].

## 4. Operators offered per field type

Source: `OperatorListTrait` type map, `TypeOperatorSubscriber`, `FilterOperatorSubscriber` [code: app/bundles/LeadBundle/Entity/OperatorListTrait.php:12-126 @7.x] [code: app/bundles/LeadBundle/Entity/OperatorListTrait.php:213-240 @7.x] [code: app/bundles/LeadBundle/EventListener/TypeOperatorSubscriber.php:69-95 @7.x] [code: app/bundles/LeadBundle/EventListener/FilterOperatorSubscriber.php:26-59 @7.x] [code: app/bundles/LeadBundle/EventListener/FilterOperatorSubscriber.php:538-579 @7.x].

| Field type | Operators (keys) | Notes |
|---|---|---|
| text, lookup, email, url, tel | `= != empty !empty like !like regexp !regexp startsWith endsWith contains`, plus `in !in` on the segment form | `in`/`!in` are added for text-type filters on the segment form [code: app/bundles/LeadBundle/EventListener/FilterOperatorSubscriber.php:538-566 @7.x] |
| select, country, timezone, region, locale | `= != empty !empty regexp !regexp in !in` | `in_all` with more than one value = never; `!in_all` with more than one value = always [code: app/bundles/LeadBundle/EventListener/SegmentOperatorQuerySubscriber.php:82-99 @7.x] |
| multiselect | `in !in in_all !in_all empty !empty` | REGEXP on pipe-separated values (§5.4) |
| boolean / bool | `= !=` | value cast to bool |
| number | `= != gt gte lt lte empty !empty like !like regexp !regexp startsWith endsWith contains` | value cast to float |
| date, datetime | `= != gt gte lt lte empty !empty like !like regexp !regexp startsWith endsWith contains`, plus `inLast inNext` in segment context | `inLast`/`inNext` enabled by `TypeOperatorProvider::setContext('segment')` [code: app/bundles/LeadBundle/Form/Type/ListType.php:39 @7.x] |
| lookup_id (owner) | `= != empty !empty` | |
| unknown/default | number set plus `like !like` | |
| behaviour datetime (e.g. `lead_email_read_date`, `hit_url_date`) | `= != gt lt gte lte`, plus `inLast inNext` | |
| behaviour number (e.g. `lead_email_read_count`, `hit_url_count`, `sessions`) | `= gt lt gte lte` | |
| behaviour text (e.g. `hit_url`, `referer`, `url_title`) | `= != like !like regexp !regexp startsWith endsWith contains` | |
| `lead_email_received`, `lead_email_sent` | `in !in in_all !in_all` | |
| `leadlist`, `tags`, `campaign`, `globalcategory` (choice behaviour) | `in !in` (plus `empty !empty` where offered) | `!in` = NOT EXISTS |
| DNC (`dnc_*`), `email_id`, `sms_clicked_link`, `page_id`, `redirect_id`, `notification` (boolean behaviour) | `= !=` with yes/no | rewritten to IN / NOT IN (§7.5–7.6) |
| `generated_email_domain` | text set | virtual column [code: app/bundles/LeadBundle/EventListener/GeneratedColumnSubscriber.php:35-72 @7.x] |

4.1 The static contact filters and the behaviours group are offered only when `isForSegmentation()` is true. The static filters are `date_added`, `date_identified`, `last_active`, `date_modified`, `owner_id`, `points`, `campaign`, `device_*`, `dnc_*`, `stage`, `globalcategory` and `utm_*`. `isForSegmentation()` is true on the segment form, on the `mautic_api_lists*` routes and in the filter AJAX action. Dynamic Content gets only custom fields, `leadlist` and `tags` [code: app/bundles/LeadBundle/EventListener/FilterOperatorSubscriber.php:130-536 @7.x] [code: app/bundles/LeadBundle/Event/LeadListFiltersChoicesEvent.php:91-109 @7.x].

4.2 Contact and company fields appear as filters only when they are set "Available for Segments" [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters].

4.3 Filter choices are grouped by object (`lead`, `company`, `company_all`, `behaviors`, `groups`), sorted by label and cached per model instance [code: app/bundles/LeadBundle/Model/ListModel.php:303-338 @7.x].

## 5. Value preparation and NULL semantics

5.1 Value preparation [code: app/bundles/LeadBundle/Segment/Decorator/BaseDecorator.php:80-119 @7.x] [code: app/bundles/LeadBundle/Segment/ContactSegmentFilterCrate.php:103-124 @7.x]:
- number → float.
- boolean → bool, except for set and regexp operators.
- `in`/`!in` strings → split on `|`.
- `like`/`!like` → `%v%` unless `%` is already present.
- `contains` → `%v%`.
- `startsWith` → `v%`.
- `endsWith` → `%v`.
- `regexp` → `prepareRegex()`.

5.2 Contact-field SQL [code: app/bundles/LeadBundle/EventListener/SegmentOperatorQuerySubscriber.php:29-112 @7.x] [code: app/bundles/LeadBundle/EventListener/SegmentOperatorQuerySubscriber.php:171-221 @7.x]:
- `empty` → `IS NULL OR = ''`. Date columns get no `= ''` branch.
- `!empty` → `IS NOT NULL AND != ''`.
- `!=`, `!like`, `!between`, `!in` → `IS NULL OR <negated>`.
- `!regexp` → plain `NOT REGEXP`. NULL is excluded for backward compatibility.

5.3 Regexp values are validated with the `DbRegex` constraint [code: app/bundles/LeadBundle/EventListener/TypeOperatorSubscriber.php:347-349 @7.x].

5.4 For multiselect, `in`/`!in`/`in_all`/`!in_all` become `multiselect`/`!multiselect`. Each value becomes the pattern `(([|]|^)value([|]|$))` [code: app/bundles/LeadBundle/Segment/ContactSegmentFilterCrate.php:179-184 @7.x] [code: app/bundles/LeadBundle/EventListener/SegmentOperatorQuerySubscriber.php:114-169 @7.x]:
- includes-all → AND of the regexps.
- includes-any → OR of the regexps.
- excludes-all → `NOT(AND…) OR IS NULL`.
- excludes-any → `AND NOT REGEXP… OR IS NULL`.

## 6. Date filters and relative dates

6.1 `DecoratorFactory` picks the date decorator for `date`/`datetime` types [code: app/bundles/LeadBundle/Segment/Decorator/DecoratorFactory.php:34-42 @7.x] [code: app/bundles/LeadBundle/Segment/Decorator/Date/DateOptionFactory.php:34-99 @7.x]. The value is classified as one of:
- a named range: `today`, `tomorrow`, `yesterday`, `this|last|next week|month|year`;
- a relative interval: starts with `+`/`-`, or contains `first day of`, `last day of` or ` ago`;
- an anniversary: `birthday`/`anniversary`, optionally with a modifier;
- otherwise, an absolute date.

6.2 Named strings are stored in English and translated for display. Absolute datetimes are converted from the user's timezone to UTC on save [code: app/bundles/LeadBundle/Form/DataTransformer/FieldFilterTransformer.php:44-134 @7.x]. Evaluation does not depend on UI language [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#date-options].

6.3 "Now" is UTC for `datetime` fields and `default_timezone` for `date` fields [code: app/bundles/LeadBundle/Segment/Decorator/Date/TimezoneResolver.php:20-38 @7.x]. Relative intervals are formatted with `toUtcString()` [code: app/bundles/LeadBundle/Segment/Decorator/Date/Other/DateRelativeInterval.php:91 @7.x]. Named ranges and anniversaries use `toLocalString()` [code: app/bundles/LeadBundle/Segment/Decorator/Date/DateOptionAbstract.php:106 @7.x] [code: app/bundles/LeadBundle/Segment/Decorator/Date/Other/DateAnniversary.php:61 @7.x].

6.4 Named ranges with `=`/`!=` [code: app/bundles/LeadBundle/Segment/Decorator/Date/Day/DateDayAbstract.php:16-29 @7.x] [code: app/bundles/LeadBundle/Segment/Decorator/Date/Week/DateWeekAbstract.php:16-36 @7.x]:
- Day, month and year ranges become `LIKE`/`NOT LIKE` on a prefix: `'YYYY-MM-DD%'`, `'YYYY-MM-%'`, `'YYYY-%'`.
- Week ranges become `BETWEEN monday 00:00:00 AND sunday 23:59:59`, or `NOT BETWEEN` for `!=`.

6.5 Named ranges with `gt`/`lte` compare against the last second of the range. `gte`/`lt` compare against the first second. Base dates are `midnight today`, `midnight monday this week`, `midnight first day of this month` and `midnight first day of January this year` [code: app/bundles/LeadBundle/Segment/Decorator/Date/DateOptionAbstract.php:88-107 @7.x].

6.6 Relative intervals are applied with `DateTime::modify()` to "now" [code: app/bundles/LeadBundle/Segment/Decorator/Date/Other/DateRelativeInterval.php:43-92 @7.x]:
- `=` becomes `LIKE 'YYYY-MM-DD%'`, and `!=` becomes `NOT LIKE`.
- Datetime fields include `H:i:s` in the value.
- Date fields with `gt` get ` 23:59:59` appended.

6.7 `anniversary`/`birthday`, with an optional modifier, forces `LIKE '%-MM-DD%'` and matches any year [code: app/bundles/LeadBundle/Segment/Decorator/Date/Other/DateAnniversary.php:35-62 @7.x].

6.8 `inLast`/`inNext` store `{interval, unit}`, which is parsed to `-N unit`/`+N unit` [code: app/bundles/LeadBundle/Segment/Decorator/ParseDateFilterValueTrait.php:16-41 @7.x]. The SQL uses "today" in UTC [code: app/bundles/LeadBundle/Segment/Query/Expression/ExpressionBuilder.php:126-147 @7.x]:
- inLast: `BETWEEN '<now-N> 00:00:00' AND '<today> 23:59:59'`.
- inNext: `BETWEEN '<today> 00:00:00' AND '<now+N> 23:59:59'`.

6.9 For `inLast`/`inNext`, the form accepts only positive whole numbers. The documented units are days, months and years [code: app/bundles/LeadBundle/Tests/Controller/ListControllerFunctionalTest.php @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#in-the-last-and-in-the-next].

6.10 Absolute date values must parse as `Y-m-d`, `Y-m-d H:i` or `Y-m-d H:i:s`. Otherwise the form error `mautic.lead.segment.date_invalid` is raised. Values with `%` and pattern operators are exempt [code: app/bundles/LeadBundle/Validator/Constraints/SegmentDateValidator.php:24-63 @7.x].

## 7. Behaviour (foreign-table) filters

7.1 `ContactSegmentFilterDictionary` maps each alias to a builder service, `foreign_table`, `field`, an optional `foreign_table_field` (default `lead_id`), `func`, `where` and `null_value` [code: app/bundles/LeadBundle/Services/ContactSegmentFilterDictionary.php:77-274 @7.x].

7.2 `ForeignValueFilterQueryBuilder` SQL [code: app/bundles/LeadBundle/Segment/Query/Filter/ForeignValueFilterQueryBuilder.php:19-181 @7.x]:
- Positive operators → `l.id IN (SELECT lead_id FROM t WHERE field <op> :p [AND where])`.
- `empty` → `NOT IN`, and `!empty` → `IN`.
- `!in` → `NOT EXISTS (… field IN (:p))`.
- `!=` → `NOT EXISTS (… = :p OR IS NULL)`.
- `in_all` → `GROUP BY lead_id HAVING COUNT(DISTINCT field) = n`.
- `!in_all` → `NOT EXISTS` of that.

7.3 Mapping [code: app/bundles/LeadBundle/Services/ContactSegmentFilterDictionary.php:79-273 @7.x]:
- `tags` → `lead_tags_xref.tag_id`.
- `leadlist` → `lead_lists_leads.leadlist_id` with `manually_removed = 0`.
- `campaign` → `campaign_leads.campaign_id` with `manually_removed = 0`.
- `globalcategory` → `lead_categories`.
- `lead_email_received` → `email_stats.email_id` with `is_read = 1`.
- `lead_email_sent` → `email_stats.email_id`.
- `lead_email_read_date` → `MAX(email_stats.date_read)`.
- `lead_email_read_count` → `SUM(open_count)`, with NULL treated as 0.
- `hit_url*`, `referer`, `url_title`, `source*`, `page_id`, `redirect_id` → `page_hits`.
- `hit_url_count` → `COUNT(page_hits.id)`.
- `device_*` → `lead_devices`.
- `utm_*` → `lead_utmtags`.
- `lead_asset_download` → `asset_downloads`.
- `notification` → `push_ids`.
- `stage` → `leads.stage_id`.
- Point groups → `point_group_contact_score.score` [code: app/bundles/PointBundle/EventListener/SegmentFilterSubscriber.php:63-80 @7.x].

7.4 Aggregate filters use `EXISTS (SELECT func(...) … HAVING func <op> :p)`. `SUM` is wrapped in `COALESCE(…, 0)` [code: app/bundles/LeadBundle/Segment/Query/Filter/ForeignFuncFilterQueryBuilder.php:21-128 @7.x]. Behaviour date filters therefore evaluate the most recent occurrence [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters].

7.5 DNC filters (Do Not Contact) [code: app/bundles/LeadBundle/Segment/DoNotContact/DoNotContactParts.php:15-28 @7.x] [code: app/bundles/LeadBundle/Segment/Query/Filter/DoNotContactFilterQueryBuilder.php:22-52 @7.x]:
- The suffix selects the reason: `_manual` → MANUAL, `_bounced` → BOUNCED, anything else → UNSUBSCRIBED.
- The suffix selects the channel: `_sms` → sms, anything else → email.
- `= yes` / `!= no` → `IN lead_donotcontact`.
- `= no` / `!= yes` → `NOT IN`.

7.6 Click filters (`email_id`, `sms_clicked_link`, and their `_date` variants) query `page_hits` with `redirect_id IS NOT NULL` and `source = 'email'|'sms'`. In the boolean variants, yes means IN and no means NOT IN [code: app/bundles/LeadBundle/Segment/Query/Filter/ChannelClickQueryBuilder.php:20-82 @7.x].

7.7 `sessions` counts page hits that have no email/redirect id and no other hit by the same Contact in the preceding 30 minutes [code: app/bundles/LeadBundle/Segment/Query/Filter/SessionsFilterQueryBuilder.php:15-63 @7.x].

7.8 UTM filters match any value ever recorded on the Contact, not only the latest one [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_segment_filters.html#create-segment-filters] [code: app/bundles/LeadBundle/Services/ContactSegmentFilterDictionary.php:243-262 @7.x].

7.9 `integration_campaigns` LEFT JOINs `integration_entity`. The CRM plugin pulls campaign members before each rebuild via `LIST_PRE_PROCESS_LIST` [code: app/bundles/LeadBundle/Segment/Query/Filter/IntegrationCampaignFilterQueryBuilder.php:19-57 @7.x] [code: plugins/MauticCrmBundle/EventListener/LeadListSubscriber.php:86-119 @7.x].

## 8. Company filters

8.1 Two objects exist: `company` ("primary company") and `company_all` ("any company"). `company_all` is offered only on the segment form and API [code: app/bundles/LeadBundle/EventListener/FilterOperatorSubscriber.php:122-126 @7.x].

8.2 Both objects generate `EXISTS (SELECT 1 FROM companies_leads r LEFT JOIN companies c … WHERE r.lead_id = l.id …)` [code: app/bundles/LeadBundle/Segment/Query/Filter/AbstractCompanyRelationValueFilterQueryBuilder.php:15-86 @7.x] [code: app/bundles/LeadBundle/Segment/Query/Filter/AnyCompanyRelationValueFilterQueryBuilder.php:14-22 @7.x]:
- `company` adds `is_primary = 1`. For the negative operators (`empty`, `!=`, `!like`, `!between`, `!in`, `!multiselect`, `!in_all`) it also matches Contacts with no primary company.
- `company_all` never matches Contacts without a company. Its negative operators need only one non-matching company.

8.3 Company date filters use `DateCompanyDecorator`, which routes to the same builders [code: app/bundles/LeadBundle/Segment/Decorator/DateCompanyDecorator.php:59-66 @7.x].

## 9. Membership: manual add / remove

9.1 `ListModel::addLead($lead, $lists, $manuallyAdded = false, $batchProcess = false, $searchListLead = 1, $dateManipulated = null)` [code: app/bundles/LeadBundle/Model/ListModel.php:647-725 @7.x].

9.2 Re-adding an existing member manually updates the row to `manually_removed = 0, manually_added = 1`. A non-manual re-add does nothing [code: app/bundles/LeadBundle/Model/ListModel.php:727-741 @7.x].

9.3 `removeLead` behaves as follows [code: app/bundles/LeadBundle/Model/ListModel.php:795-913 @7.x]:
- A manual removal of a manually added row deletes the row.
- An automatic removal of a filter-added row deletes the row.
- A manual removal of a filter-added row keeps it with `manually_removed = 1`.
- An automatic removal of a manually added row does nothing.

9.4 All of these go through `LeadModel::addToLists/removeFromLists` with the manual flags set to true [code: app/bundles/LeadBundle/Model/LeadModel.php:960-973 @7.x] [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:329-334 @7.x] [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:223-227 @7.x] [code: app/bundles/LeadBundle/EventListener/PointSubscriber.php:153-157 @7.x]:
- UI single toggle.
- Contact-list batch action.
- API add/remove.
- Campaign action `lead.changelist`.
- Form action.
- Point trigger.

9.5 Docs: once a Contact is manually added or removed, the Segment's filters no longer apply to that Contact [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#batch-changes].

9.6 Lists that do not exist are skipped silently [code: app/bundles/LeadBundle/Model/ListModel.php:703-706 @7.x].

9.7 On contact merge, memberships move to the winner unless the winner is already a member [code: app/bundles/LeadBundle/Entity/ListLeadRepository.php:18-53 @7.x].

9.8 Non-batch changes fire `LEAD_LIST_CHANGE`. Batch changes (the rebuild) fire one `LEAD_LIST_BATCH_CHANGE` per batch [code: app/bundles/LeadBundle/Model/ListModel.php:771-781 @7.x].

## 10. Rebuild algorithm and the command

10.1 Command `mautic:segments:update` (alias `mautic:segments:rebuild`) has these options [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:38-78 @7.x] [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-74 @7.x]:
- `--batch-limit|-b` (default 300).
- `--max-contacts|-m`.
- `--list-id|-i`.
- `--timing|-tm`.
- `--exclude|-d` (repeatable).
- Inherited: `--bypass-locking`, `--timeout|-t`, `--lock_mode|-x pid|flock|redis` and `--force` (deprecated).

10.2 The lock key is the command name plus `--list-id`. Different ids may run in parallel. A held lock prints "Script in progress" and exits 0 [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:102-116 @7.x].

10.3 An unknown `--list-id` prints `mautic.lead.list.rebuild.not_found` and exits FAILURE [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:100-104 @7.x].

10.4 Without an id, the command iterates all Segments except `--exclude`. It rebuilds dependencies first and never rebuilds the same id twice [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:119-157 @7.x].

10.5 Unpublished Segments are skipped [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:242-244 @7.x].

10.6 At the start, the rebuild captures UTC now as a `dateTime` limiter. Only Contacts with `date_added <= now` are considered [code: app/bundles/LeadBundle/Model/ListModel.php:391 @7.x].

10.7 Add phase [code: app/bundles/LeadBundle/Model/ListModel.php:400-500 @7.x] [code: app/bundles/LeadBundle/Segment/Query/LeadBatchLimiterTrait.php:13-30 @7.x]:
1. Count new matches and record `maxId`.
2. Loop: `batchSleep()`, then fetch up to `--batch-limit` ids. The `NOT IN existing rows` clause replaces OFFSET.
3. Call `addLead(..., false, true, -1, localNow)` for each id.
4. Dispatch `LEAD_LIST_BATCH_CHANGE`.
5. Stop when the fetch is empty or `--max-contacts` is reached.

10.8 Remove phase [code: app/bundles/LeadBundle/Model/ListModel.php:503-581 @7.x] [code: app/bundles/LeadBundle/Segment/ContactSegmentService.php:265-291 @7.x]:
- Orphans are rows with `manually_added = 0` whose `lead_id NOT IN (<filter query>)`.
- They are removed in batches, with `LEAD_LIST_BATCH_CHANGE` dispatched with `added = false`.

10.9 `finishRebuild` refreshes the count cache. It sets `lastBuiltDate = now (UTC)` only when the run completed or a probe finds no remaining work. Otherwise it sets `lastBuiltDate` to NULL, so the Segment keeps showing "Building" [code: app/bundles/LeadBundle/Model/ListModel.php:591-633 @7.x].

10.10 A run capped by `--max-contacts` returns after the add phase without removing orphans. The next run continues [code: app/bundles/LeadBundle/Model/ListModel.php:464-466 @7.x] [code: app/bundles/LeadBundle/Model/ListModel.php:547-549 @7.x].

10.11 The command stores `lastBuiltTime` (seconds) only when `lastBuiltDate` changed and every `leadlist` dependency is complete. Otherwise it clears the dependent Segment's `lastBuiltDate` [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:240-302 @7.x].

10.12 Segments without filters add and remove nothing [code: app/bundles/LeadBundle/Segment/ContactSegmentService.php:32-41 @7.x].

10.13 The rebuild saves the entity only when `lastBuiltDate` changed [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:254-262 @7.x].

10.14 Since 5.0, the Segment rebuild does not update Campaign membership [code: UPGRADE-5.0.md:55 @7.x].

10.15 The repo states no recommended cron interval. The docs say Segments rebuild "as often as the Segment cron job fires" [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters].

10.16 Other commands [code: app/bundles/LeadBundle/Command/SegmentCountCacheCommand.php:34-49 @7.x] [code: app/bundles/LeadBundle/Command/DeleteLeadListsCommand.php:47-87 @7.x] [code: app/bundles/LeadBundle/Command/SegmentStatCommand.php:32-52 @7.x]:
- `lead:list:count-cache-update` recounts published Segments that carry a recount marker.
- `mautic:segment:delete [id]` hard-deletes soft-deleted Segments.
- `mautic:segments:stat` prints usage.

## 11. Segment-membership filters, dependencies, circularity

11.1 `leadlist` filters read the materialised rows of the referenced Segment (`manually_removed = 0`) [code: app/bundles/LeadBundle/Services/ContactSegmentFilterDictionary.php:142-147 @7.x].

11.2 The command rebuilds referenced Segments first, recursively [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:106-157 @7.x] [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:177-238 @7.x]:
- A cycle prints "Circular dependency detected in segment chain: a → b → a" and the edge is skipped.
- Missing dependencies are skipped.

11.3 The form constraint `CircularDependency` on `filters` rejects cycles on save [code: app/bundles/LeadBundle/Form/Type/ListType.php:146 @7.x] [code: app/bundles/CoreBundle/Form/Validator/Constraints/CircularDependencyValidator.php:26-67 @7.x]. At query build, `getResolutionPlan` throws `SegmentQueryException('Circular reference detected.')` [code: app/bundles/LeadBundle/Segment/Query/ContactSegmentQueryBuilder.php:255-277 @7.x].

11.4 Unpublishing a Segment used by another Segment's filter or by a Campaign source is refused in three places [code: app/bundles/LeadBundle/Form/Validator/Constraints/SegmentInUseValidator.php:24-44 @7.x] [code: app/bundles/LeadBundle/Validator/Constraints/SegmentUsedInCampaignsValidator.php:20-33 @7.x] [code: app/bundles/LeadBundle/EventListener/SegmentSubscriber.php:73-91 @7.x]:
- Form validation.
- The publish toggle, via `RecordCanNotUnpublishException`.
- The API, which returns 422.

11.5 Deleting such a Segment is refused with dependency errors. Batch delete deletes the rest. A set whose only dependents are inside the set can be deleted [code: app/bundles/LeadBundle/Model/ListModel.php:166-208 @7.x] [code: app/bundles/LeadBundle/Model/ListModel.php:1349-1398 @7.x]. The docs date this check to Mautic 4 [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#deleting-or-deactivating-a-segment].

11.6 The detail page lists dependants: emails, campaigns, segments, reports, forms and point triggers [code: app/bundles/LeadBundle/Segment/Stat/SegmentDependencies.php:24-50 @7.x].

## 12. Counts and caches

12.1 Member count = rows with `manually_removed = 0` [code: app/bundles/LeadBundle/Entity/LeadListRepository.php:286-338 @7.x].

12.2 The cached count lives in `segment.<id>.lead` with TTL `segment_api_count_cache_ttl` (43200). The list page returns 0 on a cache miss [code: app/bundles/LeadBundle/Model/ListModel.php:1430-1468 @7.x].

12.3 With `update_segment_contact_count_in_background = true`, changes set a recount marker instead of updating the count. `lead:list:count-cache-update` must then run [code: app/bundles/LeadBundle/Model/ListModel.php:626-630 @7.x].

12.4 The decrement floors at 0. Every removal decrements, even when the row is kept [code: app/bundles/LeadBundle/Helper/SegmentCountCacheHelper.php:95-106 @7.x] [code: app/bundles/LeadBundle/Model/ListModel.php:879-883 @7.x].

12.5 "Active contacts" = members minus DNC, floored at 0 [code: app/bundles/LeadBundle/Model/ListModel.php:1470-1476 @7.x].

## 13. Lifecycle

13.1 On save, a blank alias is generated from the name and de-duplicated with a counter. A blank public name defaults to the name [code: app/bundles/LeadBundle/Model/ListModel.php:120-159 @7.x].

13.2 Saving writes an audit-log entry [code: app/bundles/LeadBundle/EventListener/SegmentSubscriber.php:54-68 @7.x].

13.3 Delete runs in two steps [code: app/bundles/LeadBundle/Entity/LeadListRepository.php:690-699 @7.x] [code: app/bundles/LeadBundle/Model/ListModel.php:194-215 @7.x]:
1. A soft delete sets `deleted = now` and `is_published = 0`.
2. Unless `delete_segment_in_background` is set, memberships are removed in batches of 5 000 and the row is hard-deleted.

13.4 A clone is unpublished, with no members, a blank alias and no `lastBuiltDate` [code: app/bundles/LeadBundle/Entity/LeadList.php:414-423 @7.x].

13.5 Non-global Segments are visible only to their creator or to users with `viewother`. Preference-centre listing requires both published and `is_preference_center` [code: app/bundles/LeadBundle/Entity/LeadListRepository.php:92-126 @7.x] [code: app/bundles/LeadBundle/Entity/LeadListRepository.php:263-277 @7.x].

13.6 Search commands on the Segment list: `is:global`, `is:published`, `is:unpublished`, `is:mine`, `name:`, `category:`, `filters_field:<alias>` and project [code: app/bundles/LeadBundle/Entity/LeadListRepository.php:429-499 @7.x]. The docs list only `ids:`, `is:global`, `name:` and `category:` [docs: https://docs.mautic.org/en/7.2/search/search_operators.html#companies-search-filters].

13.7 Permissions are `lead:lists:{viewown,viewother,editown,editother,create,deleteown,deleteother,full}` [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php:11-45 @7.x].

13.8 List-row warnings [code: app/bundles/LeadBundle/Resources/views/List/_list_row.html.twig:5-35 @7.x]:
- A red icon when hours since the last build ≥ `segment_rebuild_time_warning` (30).
- A clock icon when `lastBuiltTime` ≥ `segment_build_time_warning` (30 s).

## 14. Events, timeline, webhooks

14.1 Membership changes write `lead_event_log` entries (bundle `lead`, object `segment`, action added/removed). Runs from CLI use the system user [code: app/bundles/LeadBundle/EventListener/TimelineEventLogSegmentSubscriber.php:40-123 @7.x].

14.2 The webhook `mautic.lead_list_change` fires for single and batch changes [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:266-287 @7.x].

14.3 The Email pending-count cache is invalidated on both change events [code: app/bundles/EmailBundle/EventListener/SegmentSubscriber.php:19-30 @7.x].

## 15. REST API

15.1 Endpoints under `/api/segments` [code: app/bundles/LeadBundle/Config/config.php:220-244 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html]:
- `GET /segments` returns `total` plus `lists`, keyed by id.
- `GET /segments/{id}` returns a `list` object.
- `POST /segments/new`.
- `PUT|PATCH /segments/{id}/edit`.
- `DELETE /segments/{id}/delete`.
- Batch endpoints.

15.2 `?withCounts` adds `contactCount` from the cache [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:99-128 @7.x].

15.3 Membership endpoints [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:151-251 @7.x]:
- `POST /segments/{id}/contact/{cid}/add|remove` returns `{"success":1}`.
- `POST /segments/{id}/contacts/add` takes body `ids[]`. It returns `success: 1` and a per-id `details[id].success`. Missing `ids` returns 400.
- These endpoints add manually. They need edit access to the Contact, and the Segment must be in the user's lists.

15.4 `GET /contacts/list/segments` returns the Segments available to the user. `GET /contacts/{id}/segments` returns one Contact's Segments [code: app/bundles/LeadBundle/Config/config.php:194-223 @7.x].

15.5 For `inLast`/`inNext`, `properties.filter` is `{interval, unit}` [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#in-the-last-and-in-the-next-filter].

15.6 An API Platform resource also exists at `/api/segments` with `segment:read/write` groups [code: app/bundles/LeadBundle/Entity/LeadList.php:29-48 @7.x].

## 16. Performance

16.1 One sleep of `batch_sleep_time` (default 1 s) happens per batch in each phase. `batch_lead_sleep_time` is read but not declared anywhere [code: app/bundles/LeadBundle/Model/ListModel.php:923-939 @7.x] [code: app/bundles/CoreBundle/Config/config.php:699 @7.x].

16.2 `DISTINCT` is added only when the query has a JOIN [code: app/bundles/LeadBundle/Segment/ContactSegmentService.php:159-163 @7.x].

16.3 The filter factory runs several times per rebuild, and each run dispatches `LIST_FILTERS_MERGE` [code: app/bundles/LeadBundle/Segment/ContactSegmentService.php:30 @7.x].

16.4 The count query for a single id uses `USE INDEX (manually_removed)` [code: app/bundles/LeadBundle/Entity/LeadListRepository.php:286-338 @7.x].

16.5 SQL is logged at debug level, and query exceptions at error level [code: app/bundles/LeadBundle/Segment/ContactSegmentService.php:320-375 @7.x].

## 17. Open questions and doc discrepancies

17.1 Docs operator labels vs keys: the docs' "contains honours %" describes operator `like` (UI "contains"). The docs' "in list" is operator `contains`. Both agree with the code once the labels are mapped [code: app/bundles/LeadBundle/Segment/Decorator/BaseDecorator.php:92-102 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#matching-part-of-a-string].

17.2 The docs say contains/doesn't contain are not supported on date fields. The code offers them, as string matching on the stored value [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#operators].

17.3 The REST docs' operator table is incomplete: it lacks `regexp`, `startsWith`, `endsWith`, `contains`, `in_all` and the empty operators. Use §4 [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#common-operators-by-field-type].

17.4 The REST docs name the bulk-add key `contactIds`, but the code reads `ids` [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:186 @7.x].

17.5 The REST docs say `isGlobal` defaults to restricted. The entity default is `true` [code: app/bundles/LeadBundle/Entity/LeadList.php:105 @7.x]. Unresolved.

17.6 The 7.2 docs describe primary-company filters only, but the 7.x branch has `company_all` (after 7.2.1, unreleased; [PR #15800]) [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters].

17.7 Named ranges on `datetime` fields in non-UTC installs, and the week ranges' use of local midnight, are untested [code: app/bundles/LeadBundle/Segment/Decorator/Date/Week/DateWeekThis.php:13 @7.x].

17.8 `getLists($user)` composes `(published AND global) OR createdBy = user`. It may return unpublished own lists. This is inferred from the query composition [code: app/bundles/LeadBundle/Entity/LeadListRepository.php:99-108 @7.x].

17.9 Docs date examples: "equal to last week" in the docs reads like "this week". With today = 2022-03-05, "anniversary -1 month" → 02-04 looks off by one [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#date-options]. Code: weeks run Monday to Sunday (§6.4).
