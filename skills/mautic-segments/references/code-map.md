# Segments — code map (Mautic 7.x)

LB = `app/bundles/LeadBundle/` in the tables below. Citations use full paths.

## Entities and tables
| Entity | Table | Key facts |
|---|---|---|
| `Mautic\LeadBundle\Entity\LeadList` | `lead_lists` (+ `lead_list_projects_xref`) | `filters` is a Doctrine `array` (PHP-serialised). `is_global` defaults to true. Soft delete via `deleted`. Indexes `lead_list_alias` and `segment_deleted` [code: app/bundles/LeadBundle/Entity/LeadList.php:139-196 @7.x] |
| `ListLead` | `lead_lists_leads` | PK (`leadlist_id`, `lead_id`); `date_added`, `manually_added`, `manually_removed`; indexes `manually_removed` and `lead_id_lists_id_removed` [code: app/bundles/LeadBundle/Entity/ListLead.php:49-68 @7.x] |
| Repositories | — | `LeadListRepository` (counts, visibility, search commands, dependency lookups) and `ListLeadRepository` (merge re-point, batch deletes of 5 000) [code: app/bundles/LeadBundle/Entity/ListLeadRepository.php:13-101 @7.x] |

## Services
| Class | Path | Role |
|---|---|---|
| `ListModel` | LB/Model/ListModel.php | `rebuildListLeads`, `addLead`, `removeLead`, counts, `getChoiceFields`, dependency checks [code: app/bundles/LeadBundle/Model/ListModel.php:109-1476 @7.x] |
| `SegmentActionModel` | LB/Model/SegmentActionModel.php | Batch add/remove from the contact list [code: app/bundles/LeadBundle/Model/SegmentActionModel.php:12-40 @7.x] |
| `ContactSegmentService` | LB/Segment/ContactSegmentService.php | New-member, total and orphan queries, with batch limiters |
| `ContactSegmentQueryBuilder` | LB/Segment/Query/ContactSegmentQueryBuilder.php | Base query, plugin filtering event, dependency plan, new-contact restriction |
| `ContactSegmentFilterFactory` | LB/Segment/ContactSegmentFilterFactory.php | Stored array → filter objects; OR-merge; picks the builder service |
| Decorators | LB/Segment/Decorator/ (`BaseDecorator`, `CustomMappedDecorator`, `CompanyDecorator`, `DateDecorator`, `Date/*`, `DateCompanyDecorator`) | Field/operator/value translation |
| Query builders | LB/Segment/Query/Filter/ (`Base`, `ForeignValue`, `ForeignFunc`, `DoNotContact`, `ChannelClick`, `Sessions`, `IntegrationCampaign`, `AbstractCompanyRelationValue`, `AnyCompanyRelationValue`, `ComplexRelationValue`) | SQL per filter kind; registered in LB/Config/services.php:186-200 [code: app/bundles/LeadBundle/Config/services.php:186-200 @7.x] |
| `OperatorOptions` | LB/Segment/OperatorOptions.php | Canonical operator table |
| `ContactSegmentFilterDictionary` | LB/Services/ContactSegmentFilterDictionary.php | Behaviour-filter alias → table map |
| `SegmentDependencyTreeFactory` | LB/Services/SegmentDependencyTreeFactory.php | Dependency tree on the detail page |
| `SegmentCountCacheHelper` | LB/Helper/SegmentCountCacheHelper.php | Count cache and recount marker |
| `SegmentDependencies` | LB/Segment/Stat/SegmentDependencies.php | Emails, campaigns, segments, reports, forms and triggers that use a Segment |
| Providers | LB/Provider/{TypeOperatorProvider,FilterOperatorProvider,FieldChoicesProvider,FormAdjustmentsProvider}.php | Operators and value widgets |

## Events (LB/LeadEvents.php)
| Constant | Line | Dispatched | Core listeners |
|---|---|---|---|
| `LIST_PRE_SAVE` / `LIST_POST_SAVE` | 191 / 201 | `ListModel::saveEntity` | Audit log |
| `LIST_PRE_UNPUBLISH` | 211 | publish toggle | `SegmentSubscriber` refuses if the Segment is in use |
| `LIST_PRE_DELETE` / `ON_LIST_DELETE` / `LIST_POST_DELETE` | 221 / 231 / 241 | delete | Dependency errors, hard delete, audit, cache clear |
| `LEAD_LIST_CHANGE` / `LEAD_LIST_BATCH_CHANGE` | 70 / 90 | add/remove, rebuild batches | Timeline, webhooks, email pending cache |
| `LIST_FILTERS_CHOICES_ON_GENERATE` | 663 | `getChoiceFields` | Core filter list, generated columns, point groups, CRM |
| `SEGMENT_DICTIONARY_ON_GENERATE` | 670 | dictionary build | Point groups |
| `LIST_FILTERS_OPERATORS_ON_GENERATE` | 680 | `FilterOperatorProvider` | `FilterOperatorSubscriber` |
| `COLLECT_FILTER_CHOICES_FOR_LIST_FIELD_TYPE` / `COLLECT_OPERATORS_FOR_FIELD_TYPE` / `COLLECT_OPERATORS_FOR_FIELD` / `ADJUST_FILTER_FORM_TYPE_FOR_FIELD` | 690–720 | providers | `TypeOperatorSubscriber` |
| `SEGMENT_ON_DECORATOR_DELEGATE` | 728 | `DecoratorFactory` | (plugin hook) |
| `LIST_FILTERS_ON_FILTERING` | 738 | per filter | (plugin hook) |
| `LIST_FILTERS_MERGE` | 748 | filter factory | — |
| `LIST_FILTERS_QUERYBUILDER_GENERATED` | 758 | after query build | — |
| `LIST_FILTERS_OPERATOR_QUERYBUILDER_ON_GENERATE` | 768 | `BaseFilterQueryBuilder` | `SegmentOperatorQuerySubscriber` |
| `LIST_PRE_PROCESS_LIST` | 778 | start of rebuild | CRM plugin |

[code: app/bundles/LeadBundle/LeadEvents.php:70-778 @7.x]

## Routes
| Name | Path | Controller |
|---|---|---|
| `mautic_segment_index` | `/s/segments/{page}` | `ListController::indexAction` |
| `mautic_segment_action` | `/s/segments/{objectAction}/{objectId}` | new/edit/clone/view/delete/batchDelete/removeLead/addLead |
| `mautic_segment_contacts` | `/s/segment/view/{objectId}/contact/{page}` | `contactsAction` |
| `mautic_segment_batch_contact_set` / `_view` | `/s/segments/batch/contact/set` / `view` | `BatchSegmentController` |
| `mautic_api_segmentsstandard` | `/api/segments` | `Api\ListApiController` |
| `mautic_api_segmentaddcontact` / `…addcontacts` / `…removecontact` | `/api/segments/{id}/contact/{leadId}/add`, `/contacts/add`, `/contact/{leadId}/remove` | `ListApiController` |
| `mautic_api_getcontactsegments` | `/api/contacts/list/segments` | `ListApiController::getListsAction` |
| `mautic_api_getcontactssegments` | `/api/contacts/{id}/segments` | `LeadApiController::getListsAction` |

[code: app/bundles/LeadBundle/Config/config.php:23-244 @7.x]

AJAX actions [code: app/bundles/LeadBundle/Controller/AjaxController.php:168-843 @7.x]:
- `loadSegmentFilterForm`
- `toggleLeadList` (manual)
- `getLeadCount` (cached count plus the "Building" label)
- `getSegmentDependencyTree`
- `getCampaignShareStats`

## Commands
| Command | Class | Notes |
|---|---|---|
| `mautic:segments:update` (`mautic:segments:rebuild`) | LB/Command/UpdateLeadListsCommand.php | Moderated; `-b -m -i -tm -d` [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:38-78 @7.x] |
| `lead:list:count-cache-update` | LB/Command/SegmentCountCacheCommand.php | Not moderated; published Segments only |
| `mautic:segment:delete [list-id]` | LB/Command/DeleteLeadListsCommand.php | For `delete_segment_in_background` |
| `mautic:segments:stat` | LB/Command/SegmentStatCommand.php | Usage table |

## Configuration parameters
| Parameter | Default | Effect |
|---|---|---|
| `delete_segment_in_background` | false | Defer the hard delete to `mautic:segment:delete` |
| `segment_api_count_cache_ttl` | 43200 | Count cache TTL (s) |
| `segment_rebuild_time_warning` | 30 (h) | Red icon on the list |
| `segment_build_time_warning` | 30 (s) | Clock icon |
| `update_segment_contact_count_in_background` | false | Mark for recount instead of updating |
| `batch_sleep_time` (Core) | 1 | Sleep per rebuild batch |
| `default_timezone` (Core) | — | Base for `date` filters |

[code: app/bundles/LeadBundle/Config/config.php:336-371 @7.x] [code: app/bundles/CoreBundle/Config/config.php:699 @7.x]

## Permissions
`lead:lists:viewown|viewother|editown|editother|create|deleteown|deleteother|full`. Any `lists` permission implies own-contact view [code: app/bundles/LeadBundle/Security/Permissions/LeadPermissions.php:11-96 @7.x].
- The API needs only `viewown` for create/edit/view.
- Delete needs `deleteother` or ownership.

[code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:261-273 @7.x]

## Form and validators
- `ListType` adds the `CircularDependency` constraint on `filters` [code: app/bundles/LeadBundle/Form/Type/ListType.php:146 @7.x].
- Other form types: `FilterType`, `FilterPropertiesType`, `SegmentConfigType`.
- Data transformer: `FieldFilterTransformer`.
- Validators: `SegmentInUse`, `SegmentUsedInCampaigns`, `UniqueUserAlias`, `SegmentDate`.

## Views
`LB/Resources/views/List/{list,_list,_list_row,details,form,filterpropform}.html.twig` [code: app/bundles/LeadBundle/Resources/views/List/_list_row.html.twig:5-76 @7.x].

## Consumers in other bundles
- `CampaignRepository` joins `lead_lists_leads` with `manually_removed = 0` [code: app/bundles/CampaignBundle/Entity/CampaignRepository.php:600-620 @7.x].
- `EmailBundle` `SegmentSubscriber` [code: app/bundles/EmailBundle/EventListener/SegmentSubscriber.php:19-30 @7.x].
- `PointBundle` `SegmentFilterSubscriber` [code: app/bundles/PointBundle/EventListener/SegmentFilterSubscriber.php:29-80 @7.x].
- CRM plugin `LeadListSubscriber` [code: plugins/MauticCrmBundle/EventListener/LeadListSubscriber.php:27-119 @7.x].
- Reports: `SegmentReportSubscriber`, `SegmentLogReportSubscriber` (not analysed) [code: app/bundles/LeadBundle/EventListener/SegmentReportSubscriber.php @7.x].
