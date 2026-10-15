# Segments — version notes

## History (5.x / 6.x)
- 5.0: `mautic:segments:update` no longer updates Campaign members. Schedule `mautic:campaigns:update` as well [code: UPGRADE-5.0.md:55 @7.x].
- Since Mautic 4, deleting or deactivating a Segment checks whether another Segment uses it as a filter [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#deleting-or-deactivating-a-segment].
- No other 5.x/6.x Segment behaviour differences appear in the inputs. PR-derived history is added in a later pass.

## 7.x
- 7.0: `SegmentReferenceFilterQueryBuilder` was removed. The `leadlist` filter now uses `ForeignValueFilterQueryBuilder` against `lead_lists_leads` with `manually_removed = 0` [code: UPGRADE-7.0.md:62 @7.x] [code: app/bundles/LeadBundle/Services/ContactSegmentFilterDictionary.php:142-147 @7.x].
- Added in 7.x:
  - "Any associated company" filters (`company_all`), alongside primary-company `company` filters; 7.x after 7.2.1, unreleased [PR #15800] [code: app/bundles/LeadBundle/EventListener/FilterOperatorSubscriber.php:122-126 @7.x];
  - (already in 7.2.0) `--max-contacts` partial-rebuild completion tracking, where an incomplete run keeps the Segment "Building" [code: app/bundles/LeadBundle/Model/ListModel.php:591-633 @7.x].
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
