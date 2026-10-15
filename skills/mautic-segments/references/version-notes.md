# Segments — version notes

## History (5.x / 6.x)
- 5.0: `mautic:segments:update` no longer updates Campaign members. Schedule `mautic:campaigns:update` as well [code: UPGRADE-5.0.md:55 @7.x].
- Since Mautic 4, deleting or deactivating a Segment checks whether another Segment uses it as a filter [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#deleting-or-deactivating-a-segment].
- 5.0:
  - `mautic:segments:update -i` exits non-zero when that Segment fails or does not exist. A failure in one Segment does not stop a full run [PR #11439].
  - `last_built_time` is stored and a slow-build warning uses `segment_build_time_warning` (default 30 s) [PR #11917].
  - Leading Segment-membership filters keep their stored glue, and two membership filters joined by OR give the union [PR #12214] [PR #12530].
  - Orphan removal uses `NOT IN` on `lead_lists_leads`, and batch limiters reach inner subqueries [PR #11583] [PR #11283].
  - The rebuild writes "added to segment" timeline entries again [PR #12249].
  - The Campaign condition "Is a member of segment" treats manually removed Contacts as non-members [PR #11782].
- 5.1:
  - OR-ed `=` filters on one field merge into one `IN` [PR #11007].
  - `--exclude` skips Segment IDs on `mautic:segments:update` [PR #13383].
  - `first day of` and `last day of` are relative values [PR #10822].
  - Multiselect "exclude" also matches NULL and empty values [PR #12906].
  - `anniversary` works on datetime fields (5.1.1) [PR #13871].
  - Contact search `segment:{alias}` uses an `EXISTS` subquery [PR #9944].
- 5.2.3: an empty `default_timezone` falls back to UTC for date filters [PR #14549].
- 6.0:
  - The list shows "Building", "No Contacts", "X Contacts" and "Building (X Contacts)" from `needsRebuild()`. Unpublished and filterless Segments never show "Building" [PR #14431] [PR #14706].
  - With `today`/`yesterday`/`tomorrow` on datetime fields, `>` and `<=` use 23:59:59 and `>=` and `<` use 00:00:00 [PR #14552].
  - Numeric and boolean filter values are no longer cast to float [PR #14555].
  - `mautic:segments:stat` reports where Segments are used [PR #14575].
- Before 5.0 the main changes were `last_built_date` with the stale warning (4.2.0), `EXISTS` subqueries and async list counts (4.3), and the 2.14 builder rewrite. See pr-history.md [PR #10772] [PR #10903] [PR #11071] [PR #5755].

## 7.x
- 7.0: `SegmentReferenceFilterQueryBuilder` was removed. The `leadlist` filter now uses `ForeignValueFilterQueryBuilder` against `lead_lists_leads` with `manually_removed = 0` [code: UPGRADE-7.0.md:62 @7.x] [code: app/bundles/LeadBundle/Services/ContactSegmentFilterDictionary.php:142-147 @7.x].
- Added in 7.x:
  - "Any associated company" filters (`company_all`), alongside primary-company `company` filters; 7.x after 7.2.1, unreleased [PR #15800] [code: app/bundles/LeadBundle/EventListener/FilterOperatorSubscriber.php:122-126 @7.x];
  - (already in 7.2.0) `--max-contacts` partial-rebuild completion tracking, where an incomplete run keeps the Segment "Building" [code: app/bundles/LeadBundle/Model/ListModel.php:591-633 @7.x].
- From PR history:
  - 7.0.0: "including any of", "including all of", "excluding any of" and "excluding all of" replace "including"/"excluding". Stored `in`/`!in` now mean "any of" [PR #15344] [PR #15473].
  - 7.0.0: membership filters read stored rows, and the command rebuilds referenced Segments first [PR #15031].
  - 7.0.0: counts are cached in the cache provider, and `update_segment_contact_count_in_background` moves recounts to `lead:list:count-cache-update` [PR #15554] [PR #14911].
  - 7.0.1: date filters are never merged into `IN` [PR #15702].
  - 7.0.2: the webhook subscriber releases entities it loaded during a rebuild [PR #15881].
  - 7.1.0: `delete_segment_in_background` and `mautic:segment:delete` [PR #15755].
  - 7.1.1: "all of" operators only on multiselect fields [PR #16012].
  - 7.1.3: "Read any email (date)" uses the latest read date [PR #16224].
  - 7.2.0: `inLast`/`inNext`, hour-level relative dates on datetime fields, and preference-centre order by public name [PR #16574] [PR #16135] [PR #15850].
  - 7.x after 7.2.1: a Campaign add sets `manually_added = 1` even after an automatic add [PR #16474].
- The 7.2 user docs still describe primary company only. The 8.0 docs describe both groups [docs: https://docs.mautic.org/en/8.0/segments/manage_segments.html#configuring-segment-filters].
- Deprecated in 7.x [code: app/bundles/LeadBundle/Segment/OperatorOptions.php:33-41 @7.x] [code: app/bundles/LeadBundle/Entity/OperatorListTrait.php:128-140 @7.x] [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:24-27 @7.x]:
  - `OperatorOptions::IN`/`NOT_IN`;
  - `OperatorListTrait::getFilterExpressionFunctions()`;
  - `LeadList::addLegacyParams`;
  - `ModeratedCommand::MODE_LOCK` (`file_lock` → `flock`).

## 8.x delta (snapshot 11599729491, 2026-10-15)
- **Branch topology**: 7.x work since 7.2.0, including the unreleased `company_all`, is not yet merged into 8.x. A two-dot diff wrongly shows it as removed. Expect it in 8.0.
- **Event dispatch by class.** Segment events are dispatched by class name. The string constants below were removed, so subscribe to the class [PR #17077] [PR #17218] [PR #17545] [PR #17625]:

  | Removed constant | Event class |
  |---|---|
  | `LIST_PRE_SAVE` | `ListPreSaveEvent` |
  | `LIST_POST_SAVE` | `ListPostSaveEvent` |
  | `LIST_PRE_DELETE` | `ListPreDeleteEvent` |
  | `ON_LIST_DELETE` | `ListDeleteEvent` |
  | `LIST_POST_DELETE` | `ListPostDeleteEvent` |
  | `LIST_PRE_UNPUBLISH` | `ListPreUnpublishEvent` |
  | `LEAD_LIST_BATCH_CHANGE` | `ListBatchChangeEvent` |
  | `LIST_FILTERS_CHOICES_ON_GENERATE` | `LeadListFiltersChoicesEvent` |
  | `LIST_FILTERS_ON_FILTERING` | `LeadListFilteringEvent` |
  | `LIST_PRE_PROCESS_LIST` | `ListPreProcessListEvent` |
  | `SEGMENT_DICTIONARY_ON_GENERATE` | `SegmentDictionaryGenerationEvent` |

- **Constants kept but not dispatched under their string.** A listener keyed on these strings loads but never fires on 8.x: `SEGMENT_ON_DECORATOR_DELEGATE`, `LIST_FILTERS_MERGE`, `LIST_FILTERS_OPERATORS_ON_GENERATE`, `LIST_FILTERS_OPERATOR_QUERYBUILDER_ON_GENERATE`, `LIST_FILTERS_QUERYBUILDER_GENERATED`, `COLLECT_OPERATORS_FOR_FIELD_TYPE`, `COLLECT_OPERATORS_FOR_FIELD`, `COLLECT_FILTER_CHOICES_FOR_LIST_FIELD_TYPE` and `ADJUST_FILTER_FORM_TYPE_FOR_FIELD`. Key them on their classes [PR #17218] [PR #17545]:
  - `LeadListFiltersDecoratorDelegateEvent`
  - `LeadListMergeFiltersEvent`
  - `LeadListFiltersOperatorsEvent`
  - `SegmentOperatorQueryBuilderEvent`
  - `LeadListQueryBuilderGeneratedEvent`
  - `TypeOperatorsEvent`
  - `FieldOperatorsEvent`
  - `ListFieldChoicesEvent`
  - `FormAdjustmentEvent`
- **Webhook type id.** `LEAD_LIST_CHANGE` is kept as a webhook type id. The event is dispatched as `ListChangeEvent`.
- **Event classes.** `LeadListEvent` is `abstract`, with one concrete subclass per name. Type-hinting the parent in a listener method still works. `ListChangeEvent` is no longer `final`. Devdocs list these classes as `final`; the code is authoritative.
- **`LeadListFiltersOperatorsEvent`.** Its constructor lost `$operators`. The event starts empty; call `addOperator()`.
- **Removed API:**
  - `OperatorOptions::IN`/`NOT_IN` (use `INCLUDING_ANY`/`EXCLUDING_ANY`);
  - `OperatorListTrait::getFilterExpressionFunctions()` (use `Provider\TypeOperatorProvider`);
  - `LeadListRepository`/`LeadRepository` no longer use `OperatorListTrait`;
  - `LeadListRepository::autowireLeadListRepository()`;
  - `Segment\Exception\InvalidUseException`.
- **`Segment\Query\QueryBuilder`.** It now extends `CoreBundle\Doctrine\Query\QueryBuilder`, and `setParameter()` rejects `:`-prefixed keys.
- **`ModeratedCommand`.** `MODE_LOCK` was removed, and `--lock_mode=file_lock` errors with "Unknown locking method specified."
- **Docs.** No Segment REST docs change for 8.0.

## Writing code for both 7.x and 8.x
Register both keys in `getSubscribedEvents()`. Guard the string constant with `defined()`, and subscribe to the event class where it exists on 7.x. Most Segment event classes already exist on 7.x [PR #17625].

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
