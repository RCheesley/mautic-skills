# Event map: Mautic 7.x event-name constants → Mautic 8.x event classes

Generated from the constant diff of `app/bundles/*/*Events.php`, `plugins/*/*Events.php` and `DoNotContact{Add,Remove}Event`
between 7.x (`419a08a9b35`; its `*Events.php` constants are identical to the 7.2.1 tag) and 8.x (`11599729491`, 2026-10-15) [code: app/bundles/*/*Events.php @7.x vs @8.x]. Open this file when
you port a listener, review a plugin for 8.x, or need to know what to subscribe to on 8.x.

## Contents
1. How to read this file
2. Summary numbers
3. Trap: constants that still exist on 8.x but are no longer dispatched
4. Names that are still dispatched as strings on 8.x
5. Constants added on 8.x
6. Full table of removed constants (225 rows)

## 1. How to read this file

- On 8.x, almost every `dispatch()` call passes only the event object, so the event name is `$event::class` [code: UPGRADE-8.0.md @8.x] [PR #17157] [PR #17625].
- A listener must subscribe to the **event class** (`LeadPostSaveEvent::class`), not to the old string constant [code: UPGRADE-8.0.md @8.x].
- Where one event object used to be dispatched under several names (pre/post save/delete), the shared parent became `abstract` and gained one concrete subclass per name. Type-hinting the abstract parent in the handler method still works; the subscription key must be the concrete class [code: UPGRADE-8.0.md @8.x lines 17-135].
- "Subscribe to / replacement" is a class in the same bundle's `Event` namespace unless a fully qualified class name is given [code: app/bundles/*/Event/ @8.x].
- "(none)" means the constant had no dispatcher or listener and has no replacement, or the mechanism changed (for example `ON_CAMPAIGN_TRIGGER_ACTION` → register `batchEventName` and listen on `PendingEvent`) [PR #17097].
- The PR column lists the PRs that touched that bundle's `*Events.php` file plus the bundle's dispatch-by-class PR; #16996 (typed constants) touched every file and is omitted.

## 2. Summary numbers

- 393 constants on 7.2.1 → 174 on 8.x: 225 removed, 6 added [code: app/bundles/*/*Events.php @7.x vs @8.x].
- Of the 225 removed: 201 map to an event class, 9 are `ON_CAMPAIGN_TRIGGER_ACTION` (→ batch action + `PendingEvent`), 15 had no dispatcher/listener and have no replacement (the table has 10 `ON_CAMPAIGN_TRIGGER_ACTION` rows: the tenth, `SmsEvents::ON_CAMPAIGN_TRIGGER_ACTION`, was unused and is counted in the 15) [code: app/bundles/*/*Events.php @7.x vs @8.x].
- Whole classes deleted on 8.x: `ApiEvents`, `ConfigEvents`, `CoreEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents`, `UserEvents` [code: app/bundles/*/ @8.x].
- Removed per bundle: ApiBundle 9, AssetBundle 7, CampaignBundle 21, ConfigBundle 3, CoreBundle 15, DashboardBundle 4, DynamicContentBundle 7, EmailBundle 20, IntegrationsBundle 23, LeadBundle 56, MauticFocusBundle 2, MauticSocialBundle 10, PageBundle 3, PluginBundle 12, SmsBundle 10, StageBundle 1, StatsBundle 1, UserBundle 15, WebhookBundle 6 [code: app/bundles/*/*Events.php @7.x vs @8.x].

## 3. Trap: constants that still exist on 8.x but are no longer dispatched

A listener keyed on one of these constants compiles and loads on 8.x but **never fires**. No error, no log line. Key on the
class instead [code: UPGRADE-8.0.md @8.x "Changed code"; verified that no 8.x dispatch passes these names].

| Kept constant (8.x) | Old name | Dispatched as |
|---|---|---|
| `ChannelEvents::ADD_CHANNEL` / `CHANNEL_BROADCAST` / `MESSAGE_QUEUED` / `PROCESS_MESSAGE_QUEUE` / `PROCESS_MESSAGE_QUEUE_BATCH` | `mautic.add_channel` … | `ChannelEvent` / `ChannelBroadcastEvent` / `MessageQueueEvent` / `MessageQueueProcessEvent` / `MessageQueueBatchProcessEvent` |
| `WebhookEvents::WEBHOOK_ON_BUILD` / `WEBHOOK_QUEUE_ON_ADD` / `WEBHOOK_ON_REQUEST` | `mautic.webhook_on_build` … | `WebhookBuilderEvent` / `WebhookQueueEvent` / `WebhookRequestEvent` |
| `PageEvents::VIDEO_ON_HIT` / `PAGE_ON_HIT` / `REDIRECT_DO_NOT_TRACK` / `ON_REDIRECT_GENERATE` / `ON_CONTACT_TRACKED` | `mautic.page_on_hit` … | `VideoHitEvent` / `PageHitEvent` / `UntrackableUrlsEvent` / `RedirectGenerationEvent` / `TrackingEvent` |
| `SmsEvents::SMS_ON_SEND` | `mautic.sms_on_send` | `SmsSendEvent` |
| `ReportEvents::REPORT_ON_BUILD` / `REPORT_ON_GENERATE` / `REPORT_QUERY_PRE_EXECUTE` / `REPORT_ON_DISPLAY` / `REPORT_ON_GRAPH_GENERATE` / `REPORT_SCHEDULE_SEND` / `REPORT_ON_COLUMN_COLLECT` / `REPORT_PERMANENT_FILE_CREATED` | `mautic.report_on_build` … | `ReportBuilderEvent` / `ReportGeneratorEvent` / `ReportQueryEvent` / `ReportDataEvent` / `ReportGraphEvent` / `ReportScheduleSendEvent` / `ColumnCollectEvent` / `PermanentReportFileCreatedEvent` |
| `EmailEvents::EMAIL_ON_OPEN` (also a webhook type id) | `mautic.email_on_open` | `EmailOpenEvent` |
| `PointEvents::POINT_ON_ACTION`; `PointGroupEvents::SCORE_CHANGE` | | `PointActionEvent`; `GroupScoreChangeEvent` |
| `PointEvents::POINT_ON_BUILD` / `TRIGGER_ON_BUILD` | `mautic.point_on_build` / `mautic.trigger_on_build` | `PointBuilderEvent` / `TriggerBuilderEvent` [code: app/bundles/PointBundle/PointEvents.php:45,87 @8.x] [code: app/bundles/EmailBundle/EventListener/PointSubscriber.php:32-33 @8.x] |
| `CategoryEvents::CATEGORY_ON_BUNDLE_LIST_BUILD` | | `CategoryTypesEvent` |
| `NotificationEvents::NOTIFICATION_ON_SEND` | `mautic.notification_on_send` | `NotificationSendEvent` |
| `StageEvents::STAGE_ON_BUILD` | `mautic.stage_on_build` | `StageBuilderEvent` |
| `FocusEvents::FOCUS_ON_VIEW` | | `FocusViewEvent` |
| `FormEvents::FORM_ON_SUBMIT` (also a webhook type id) / `FORM_ON_BUILD` / `ON_OBJECT_COLLECT` / `ON_FIELD_COLLECT` | `mautic.form_on_submit` … | `SubmissionEvent` / `FormBuilderEvent` / `ObjectCollectEvent` / `FieldCollectEvent` |
| `LeadEvents::LEAD_UTMTAGS_ADD`, `LEAD_CATEGORY_CHANGE`, `CHANNEL_SUBSCRIPTION_CHANGED`, `LEAD_BUILD_SEARCH_COMMANDS`, `COMPANY_BUILD_SEARCH_COMMANDS`, `ADJUST_FILTER_FORM_TYPE_FOR_FIELD`, `COLLECT_OPERATORS_FOR_FIELD_TYPE`, `COLLECT_OPERATORS_FOR_FIELD`, `COLLECT_FILTER_CHOICES_FOR_LIST_FIELD_TYPE`, `SEGMENT_ON_DECORATOR_DELEGATE`, `LIST_FILTERS_MERGE`, `LIST_FILTERS_OPERATORS_ON_GENERATE`, `LIST_FILTERS_OPERATOR_QUERYBUILDER_ON_GENERATE`, `LIST_FILTERS_QUERYBUILDER_GENERATED`, `IMPORT_ON_INITIALIZE`, `IMPORT_ON_FIELD_MAPPING`, `IMPORT_ON_PROCESS`, `IMPORT_ON_VALIDATE`, `LEAD_FIELD_PRE_{ADD,UPDATE,DELETE}_COLUMN[_BACKGROUND_JOB]`, `TIMELINE_ON_GENERATE` | | `LeadUtmTagsEvent`, `CategoryChangeEvent`, `ChannelSubscriptionChange`, `LeadBuildSearchEvent`, `CompanyBuildSearchEvent`, `FormAdjustmentEvent`, `TypeOperatorsEvent`, `FieldOperatorsEvent`, `ListFieldChoicesEvent`, `LeadListFiltersDecoratorDelegateEvent`, `LeadListMergeFiltersEvent`, `LeadListFiltersOperatorsEvent`, `SegmentOperatorQueryBuilderEvent`, `LeadListQueryBuilderGeneratedEvent`, `ImportInitEvent`, `ImportMappingEvent`, `ImportProcessEvent`, `ImportValidateEvent`, `Field\Event\{Add,Update,Delete}Column[Background]Event`, `LeadTimelineEvent` [PR #17250] |
| `LeadEvents::LEAD_POST_SAVE`, `LEAD_POST_DELETE`, `LEAD_POINTS_CHANGE`, `LEAD_COMPANY_CHANGE`, `LEAD_LIST_CHANGE`, `COMPANY_POST_SAVE`, `COMPANY_POST_DELETE` (kept as webhook type ids) | | `LeadPostSaveEvent`, `LeadPostDeleteEvent`, `PointsChangeEvent`, `LeadChangeCompanyEvent`, `ListChangeEvent`, `CompanyPostSaveEvent`, `CompanyPostDeleteEvent` |

## 4. Names that are still dispatched as strings on 8.x

Outside tests, only these dispatches still pass a string name on 8.x [code: app/bundles/*/*Events.php @7.x vs @8.x]:

- `CampaignEvents::ON_EVENT_DECISION_EVALUATION` and `ON_EVENT_CONDITION_EVALUATION` (`DecisionDispatcher`, `ConditionDispatcher`).
- `NotificationEvents::TOKEN_REPLACEMENT` and `SmsEvents::TOKEN_REPLACEMENT` (shared `TokenReplacementEvent`).
- Variable names (`$name`, `$eventName`, `$batchEventName`): the CRUD groups in `ReportModel`, `MessageModel`, `DynamicContentModel`, `PointGroupModel`, `TriggerModel`, `PointModel`, `StageModel`, `Form\FormModel`, `Form\FieldModel`, `NotificationModel`, `CategoryModel`, `PageModel`, `FocusModel`, and the campaign action/decision/condition names a plugin registers in `CampaignBuilderEvent` (`batchEventName`, `eventName` for decisions/conditions).

So string constants remain meaningful on 8.x only for: those CRUD groups, campaign registration names
(`*::ON_CAMPAIGN_BATCH_ACTION`, `ON_CAMPAIGN_TRIGGER_DECISION`, `ON_CAMPAIGN_TRIGGER_CONDITION`, …), A/B-winner `ON_DETERMINE_*`
names, and webhook type identifiers (`LeadEvents::LEAD_POST_SAVE`, `EmailEvents::EMAIL_ON_SEND`, `FormEvents::FORM_ON_SUBMIT`, …)
[code: UPGRADE-8.0.md @8.x lines 130, 176, 726, 753].

`CampaignEvents` keeps only `ON_EVENT_DECISION_EVALUATION`, `ON_EVENT_CONDITION_EVALUATION`, `ON_EVENT_JUMP_TO_EVENT`,
`ON_CAMPAIGN_ACTION_CHANGE_MEMBERSHIP` [code: app/bundles/CampaignBundle/CampaignEvents.php @8.x].

## 5. Constants added on 8.x

All six are `ON_CAMPAIGN_BATCH_ACTION` registration names for bundles that used to register only the legacy trigger action
[code: app/bundles/*/*Events.php @7.x vs @8.x] [PR #17097]:

| Class | Constant | Value |
|---|---|---|
| `DynamicContentEvents` | `ON_CAMPAIGN_BATCH_ACTION` | `mautic.dwc.on_campaign_batch_action` |
| `PageEvents` | `ON_CAMPAIGN_BATCH_ACTION` | `mautic.page.on_campaign_batch_action` |
| `PluginEvents` | `ON_CAMPAIGN_BATCH_ACTION` | `mautic.plugin.on_campaign_batch_action` |
| `WebhookEvents` | `ON_CAMPAIGN_BATCH_ACTION` | `mautic.webhook.on_campaign_batch_action` |
| `FocusEvents` | `ON_CAMPAIGN_BATCH_ACTION` | `mautic.focus.on_campaign_batch_action` |
| `SocialEvents` | `ON_CAMPAIGN_BATCH_ACTION` | `mautic.social.on_campaign_batch_action` |

## 6. Full table of removed constants

Source: [code: app/bundles/*/*Events.php @7.x vs @8.x, and the event classes dispatched @8.x]. Every row is a constant that exists on 7.2.1 and does not exist on 8.x.

| Bundle | Removed constant | Old event name | Subscribe to / replacement (in bundle `Event` namespace unless FQCN given) | PRs |
|---|---|---|---|---|
| ApiBundle | `ApiEvents::API_ON_ENTITY_POST_SAVE` | `mautic.api_on_entity_post_save` | `PostSaveApiEntityEvent` | #17217, #17654 |
| ApiBundle | `ApiEvents::API_ON_ENTITY_PRE_SAVE` | `mautic.api_on_entity_pre_save` | `PreSaveApiEntityEvent` | #17217, #17654 |
| ApiBundle | `ApiEvents::API_PLATFORM_PERMISSION_CONTEXT` | `mautic.api_platform_permission_context` | `ApiPlatformPermissionContextEvent` | #17217, #17654 |
| ApiBundle | `ApiEvents::API_POST_SERIALIZATION_CONTEXT` | `mautic.api_post_serialization_context` | `PostSerializationContextEvent` | #17217, #17654 |
| ApiBundle | `ApiEvents::API_PRE_SERIALIZATION_CONTEXT` | `mautic.api_pre_serialization_context` | `PreSerializationContextEvent` | #17217, #17654 |
| ApiBundle | `ApiEvents::BUILD_ROUTE` | `mautic.build_api_route` | `RouteEvent` | #17217, #17654 |
| ApiBundle | `ApiEvents::CLIENT_POST_DELETE` | `mautic.client_post_delete` | `ClientPostDeleteEvent` | #17217, #17654 |
| ApiBundle | `ApiEvents::CLIENT_POST_SAVE` | `mautic.client_post_save` | `ClientPostSaveEvent` | #17217, #17654 |
| ApiBundle | `ApiEvents::CLIENT_PRE_SAVE` | `mautic.client_pre_save` | (none - unused, removed) | #17217, #17654 |
| AssetBundle | `AssetEvents::ASSET_ON_LOAD` | `mautic.asset_on_load` | `AssetLoadEvent` | #17196, #17215 |
| AssetBundle | `AssetEvents::ASSET_ON_REMOTE_BROWSE` | `mautic.asset_on_remote_browse` | `RemoteAssetBrowseEvent` | #17196, #17215 |
| AssetBundle | `AssetEvents::ASSET_ON_UPLOAD` | `mautic.asset_on_upload` | (none - never dispatched) | #17196, #17215 |
| AssetBundle | `AssetEvents::ASSET_POST_DELETE` | `mautic.asset_post_delete` | `AssetPostDeleteEvent` | #17196, #17215 |
| AssetBundle | `AssetEvents::ASSET_POST_SAVE` | `mautic.asset_post_save` | `AssetPostSaveEvent` | #17196, #17215 |
| AssetBundle | `AssetEvents::ASSET_PRE_DELETE` | `mautic.asset_pre_delete` | `AssetPreDeleteEvent` | #17196, #17215 |
| AssetBundle | `AssetEvents::ASSET_PRE_SAVE` | `mautic.asset_pre_save` | `AssetPreSaveEvent` | #17196, #17215 |
| CampaignBundle | `CampaignEvents::CAMPAIGN_ON_BUILD` | `mautic.campaign_on_build` | `CampaignBuilderEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::CAMPAIGN_ON_LEADCHANGE` | `mautic.campaign_on_leadchange` | `CampaignSingleLeadChangeEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::CAMPAIGN_ON_TRIGGER` | `mautic.campaign_on_trigger` | `CampaignTriggerEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::CAMPAIGN_POST_DELETE` | `mautic.campaign_post_delete` | `CampaignPostDeleteEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::CAMPAIGN_POST_SAVE` | `mautic.campaign_post_save` | `CampaignPostSaveEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::CAMPAIGN_PRE_DELETE` | `mautic.campaign_pre_delete` | `CampaignPreDeleteEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::CAMPAIGN_PRE_SAVE` | `mautic.campaign_pre_save` | `CampaignPreSaveEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::LEAD_CAMPAIGN_BATCH_CHANGE` | `mautic.lead_campaign_batch_change` | `CampaignBatchLeadChangeEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_AFTER_EVENTS_DELETE` | `mautic.on_after_events_delete` | `AfterEventsDeleteEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_CAMPAIGN_DELETE` | `mautic.on_campaign_delete` | `DeleteCampaign` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_CAMPAIGN_FAILURE_NOTIFY` | `mautic.campaign_failure_notify` | `NotifyOfFailureEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_CAMPAIGN_UNPUBLISH_NOTIFY` | `mautic.campaign_unpublish_notify` | `NotifyOfUnpublishEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_EVENT_DECISION_EVALUATION_RESULTS` | `mautic.campaign_on_event_decision_evaluation_results` | `DecisionResultsEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_EVENT_DECISION_TRIGGER` | `mautic.campaign_on_event_decision_trigger` | (none) - use CampaignEvents::ON_EVENT_DECISION_EVALUATION + DecisionEvent | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_EVENT_DELETE` | `mautic.on_event_delete` | `DeleteEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_EVENT_EXECUTED` | `mautic.campaign_on_event_executed` | `ExecutedEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_EVENT_EXECUTED_BATCH` | `mautic.campaign_on_event_executed_batch` | `ExecutedBatchEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_EVENT_EXECUTION` | `mautic.campaign_on_event_execution` | (none) - use ExecutedEvent / FailedEvent | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_EVENT_FAILED` | `mautic.campaign_on_event_failed` | `FailedEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_EVENT_SCHEDULED` | `mautic.campaign_on_event_scheduled` | `ScheduledEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| CampaignBundle | `CampaignEvents::ON_EVENT_SCHEDULED_BATCH` | `mautic.campaign_on_event_scheduled_batch` | `ScheduledBatchEvent` | #17039, #17161, #17225, #17654, #17675, #17676 |
| ConfigBundle | `ConfigEvents::CONFIG_ON_GENERATE` | `mautic.config_on_generate` | `ConfigBuilderEvent` | #17625, #17654 |
| ConfigBundle | `ConfigEvents::CONFIG_POST_SAVE` | `mautic.config_post_save` | `ConfigPostSaveEvent` | #17625, #17654 |
| ConfigBundle | `ConfigEvents::CONFIG_PRE_SAVE` | `mautic.config_pre_save` | `ConfigPreSaveEvent` | #17625, #17654 |
| CoreBundle | `CoreEvents::BUILD_COMMAND_LIST` | `mautic.build_command_list` | `CommandListEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::BUILD_MAUTIC_JS` | `mautic.build_embeddable_js` | `BuildJsEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::BUILD_MENU` | `mautic.build_menu` | `MenuEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::BUILD_ROUTE` | `mautic.build_route` | `RouteEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::FETCH_ICONS` | `mautic.on_fetch_icons` | `IconEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::GLOBAL_SEARCH` | `mautic.global_search` | `GlobalSearchEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::LIST_STATS` | `mautic.list_stats` | `StatsEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::MAINTENANCE_CLEANUP_DATA` | `mautic.maintenance_cleanup_data` | `MaintenanceEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::ON_GENERATED_COLUMNS_BUILD` | `mautic.on_generated_columns_build` | `GeneratedColumnsEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::POST_UPGRADE` | `mautic.post_upgrade` | (none - unused, removed in #17183) | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::PRE_UPGRADE` | `mautic.pre_upgrade` | (none - unused, removed in #17183) | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::VIEW_INJECT_CUSTOM_ASSETS` | `mautic.view_inject_custom_assets` | `CustomAssetsEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::VIEW_INJECT_CUSTOM_BUTTONS` | `mautic.view_inject_custom_buttons` | `CustomButtonEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::VIEW_INJECT_CUSTOM_CONTENT` | `mautic.view_inject_custom_content` | `CustomContentEvent` | #17157, #17183, #17241 |
| CoreBundle | `CoreEvents::VIEW_INJECT_CUSTOM_TEMPLATE` | `mautic.view_inject_custom_template` | `CustomTemplateEvent` | #17157, #17183, #17241 |
| DashboardBundle | `DashboardEvents::DASHBOARD_ON_MODULE_DETAIL_GENERATE` | `mautic.dashboard_on_widget_detail_generate` | `GenerateWidgetDetailEvent` | #17216, #17654 |
| DashboardBundle | `DashboardEvents::DASHBOARD_ON_MODULE_DETAIL_PRE_LOAD` | `mautic.dashboard_on_widget_detail_pre_load` | `PreLoadWidgetDetailEvent` | #17216, #17654 |
| DashboardBundle | `DashboardEvents::DASHBOARD_ON_MODULE_FORM_GENERATE` | `mautic.dashboard_on_widget_form_generate` | `WidgetFormEvent` | #17216, #17654 |
| DashboardBundle | `DashboardEvents::DASHBOARD_ON_MODULE_LIST_GENERATE` | `mautic.dashboard_on_widget_list_generate` | `WidgetTypeListEvent` | #17216, #17654 |
| DynamicContentBundle | `DynamicContentEvents::CATEGORY_POST_DELETE` | `mautic.category_post_delete` | (none) - use CategoryEvents::CATEGORY_POST_DELETE | #17097, #17198, #17625, #17691 |
| DynamicContentBundle | `DynamicContentEvents::CATEGORY_POST_SAVE` | `mautic.category_post_save` | (none) - use CategoryEvents::CATEGORY_POST_SAVE | #17097, #17198, #17625, #17691 |
| DynamicContentBundle | `DynamicContentEvents::CATEGORY_PRE_DELETE` | `mautic.category_pre_delete` | (none) - use CategoryEvents::CATEGORY_PRE_DELETE | #17097, #17198, #17625, #17691 |
| DynamicContentBundle | `DynamicContentEvents::CATEGORY_PRE_SAVE` | `mautic.category_pre_save` | (none) - use CategoryEvents::CATEGORY_PRE_SAVE | #17097, #17198, #17625, #17691 |
| DynamicContentBundle | `DynamicContentEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.dwc.on_campaign_trigger_action` | (none) - register `batchEventName` => `DynamicContentEvents::ON_CAMPAIGN_BATCH_ACTION`, listen on `PendingEvent` | #17097, #17198, #17625, #17691 |
| DynamicContentBundle | `DynamicContentEvents::ON_CONTACTS_FILTER_EVALUATE` | `mautic.dwc.on_contact_filters_evaluate` | `ContactFiltersEvaluateEvent` | #17097, #17198, #17625, #17691 |
| DynamicContentBundle | `DynamicContentEvents::TOKEN_REPLACEMENT` | `mautic.dwc_token_replacement` | `Mautic\CoreBundle\Event\TokenReplacementEvent` | #17097, #17198, #17625, #17691 |
| EmailBundle | `EmailEvents::EMAIL_ON_BUILD` | `mautic.email_on_build` | `EmailOnBuildEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_ON_DISPLAY` | `mautic.email_on_display` | `EmailDisplayEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_ON_REPLY` | `mautic.email_on_reply` | `EmailReplyEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_ON_TOGGLE_PUBLISH` | `mautic.email_on_toggle_publish` | `EmailOnTogglePublishEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_PARSE` | `mautic.on_email_parse` | `ParseEmailEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_POST_DELETE` | `mautic.email_post_delete` | `EmailPostDeleteEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_POST_SAVE` | `mautic.email_post_save` | `EmailPostSaveEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_PRE_DELETE` | `mautic.email_pre_delete` | `EmailPreDeleteEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_PRE_FETCH` | `mautic.on_email_pre_fetch` | `PreFetchEmailEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_PRE_SAVE` | `mautic.email_pre_save` | `EmailPreSaveEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::EMAIL_PRE_SEND` | `mautic.email_pre_send` | `EmailPreSendEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::MONITORED_EMAIL_CONFIG` | `mautic.monitored_email_config` | `MonitoredEmailEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.email.on_campaign_trigger_action` | (none) - register `batchEventName` => `EmailEvents::ON_CAMPAIGN_BATCH_ACTION`, listen on `PendingEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::ON_EMAIL_ADDRESS_TOKEN_REPLACEMENT` | `mautic.email_address_token_replacement` | `OnEmailAddressTokenReplacementEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::ON_EMAIL_EDIT_SUBMIT` | `mautic.email.on_edit_submit` | `EmailEditSubmitEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::ON_EMAIL_STAT_POST_SAVE` | `mautic.email.on_email_stat_post_save` | `EmailStatPostSaveEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::ON_EMAIL_STAT_PRE_SAVE` | `mautic.email.on_email_stat_pre_save` | `EmailStatEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::ON_EMAIL_VALIDATION` | `mautic.email.on_email_validation` | `EmailValidationEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::ON_TRANSPORT_WEBHOOK` | `mautic.email.on_transport_webhook` | `TransportWebhookEvent` | #17059, #17217, #17225, #17675 |
| EmailBundle | `EmailEvents::TOKEN_REPLACEMENT` | `mautic.email_token_replacement` | `Mautic\CoreBundle\Event\TokenReplacementEvent` | #17059, #17217, #17225, #17675 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_API_KEYS_BEFORE_SAVE` | `mautic.integration.INTEGRATION_API_KEYS_BEFORE_SAVE` | `KeysSaveEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_BATCH_SYNC_COMPLETED_INTEGRATION_TO_MAUTIC` | `mautic.integration.INTEGRATION_BATCH_SYNC_COMPLETED_INTEGRATION_TO_MAUTIC` | `IntegrationToMauticSyncCompletedEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_BATCH_SYNC_COMPLETED_MAUTIC_TO_INTEGRATION` | `mautic.integration.INTEGRATION_BATCH_SYNC_COMPLETED_MAUTIC_TO_INTEGRATION` | `MauticToIntegrationSyncCompletedEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_BEFORE_COMPANY_FIELD_CHANGES` | `mautic.integration.INTEGRATION_BEFORE_COMPANY_FIELD_CHANGES` | `InternalCompanyFieldChangesEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_BEFORE_CONTACT_FIELD_CHANGES` | `mautic.integration.INTEGRATION_BEFORE_CONTACT_FIELD_CHANGES` | `InternalContactFieldChangesEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_BEFORE_FULL_COMPANY_REPORT_BUILD` | `mautic.integration.INTEGRATION_BEFORE_FULL_COMPANY_REPORT_BUILD` | `InternalCompanyFullReportBuildEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_BEFORE_FULL_CONTACT_REPORT_BUILD` | `mautic.integration.INTEGRATION_BEFORE_FULL_CONTACT_REPORT_BUILD` | `InternalContactFullReportBuildEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_BUILD_INTERNAL_OBJECT_ROUTE` | `mautic.integration.INTEGRATION_BUILD_INTERNAL_OBJECT_ROUTE` | `InternalObjectRouteEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_COLLECT_INTERNAL_OBJECTS` | `mautic.integration.INTEGRATION_COLLECT_INTERNAL_OBJECTS` | `InternalObjectEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_CONFIG_AFTER_SAVE` | `mautic.integration.config_after_save` | `ConfigAfterSaveEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_CONFIG_BEFORE_SAVE` | `mautic.integration.config_before_save` | `ConfigBeforeSaveEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_CONFIG_FORM_LOAD` | `mautic.integration.config_form_loaded` | `FormLoadEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_CONFIG_ON_GENERATE_AUTH_URL` | `mautic.integration.INTEGRATION_CONFIG_ON_GENERATE_AUTH_URL` | `ConfigAuthUrlEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_CREATE_INTERNAL_OBJECTS` | `mautic.integration.INTEGRATION_CREATE_INTERNAL_OBJECTS` | `InternalObjectCreateEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_FIND_INTERNAL_RECORD` | `mautic.integration.INTEGRATION_FIND_INTERNAL_RECORD` | `InternalObjectFindByIdEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_FIND_INTERNAL_RECORDS` | `mautic.integration.INTEGRATION_FIND_INTERNAL_RECORDS` | `InternalObjectFindEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_FIND_OWNER_IDS` | `mautic.integration.INTEGRATION_FIND_OWNER_IDS` | `InternalObjectOwnerEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_KEYS_AFTER_DECRYPTION` | `mautic.integration.keys_after_decryption` | `KeysDecryptionEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_KEYS_BEFORE_ENCRYPTION` | `mautic.integration.keys_before_encryption` | `KeysEncryptionEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_MAUTIC_SYNC_FIELDS_LOAD` | `mautic.integration.mautic_sync_field_load` | `MauticSyncFieldsLoadEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_OBJECT_TOKEN_EVENT` | `mautic.integration.INTEGRATION_OBJECT_TOKEN_EVENT` | `MappedIntegrationObjectTokenEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_POST_EXECUTE` | `mautic.integration.sync_post_execute_integration` | `SyncEvent` | #17160, #17654 |
| IntegrationsBundle | `IntegrationEvents::INTEGRATION_UPDATE_INTERNAL_OBJECTS` | `mautic.integration.INTEGRATION_UPDATE_INTERNAL_OBJECTS` | `InternalObjectUpdateEvent` | #17160, #17654 |
| LeadBundle | `DoNotContactAddEvent::ADD_DONOT_CONTACT` | `mautic.lead.add_donot_contact` | (none - unused; DoNotContactAddEvent itself still exists) | #17077, #17218, #17545, #17625 |
| LeadBundle | `DoNotContactRemoveEvent::REMOVE_DONOT_CONTACT` | `mautic.lead.remove_donot_contact` | (none - unused; DoNotContactRemoveEvent itself still exists) | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::COMPANY_POST_MERGE` | `mautic.company_post_merge` | `CompanyPostMergeEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::COMPANY_PRE_DELETE` | `mautic.company_pre_delete` | `CompanyPreDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::COMPANY_PRE_MERGE` | `mautic.company_pre_merge` | `CompanyPreMergeEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::COMPANY_PRE_SAVE` | `mautic.company_pre_save` | `CompanyPreSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::COMPANY_SOFT_DELETE` | `mautic.company_soft_delete` | `CompanySoftDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::CONTACT_EXPORT_PREPARE_FILE` | `mautic.contact_export_prepare_file` | `ContactExportPrepareFileEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::CONTACT_EXPORT_SEND_EMAIL` | `mautic.contact_export_send_email` | `ContactExportSendEmailEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::CURRENT_LEAD_CHANGED` | `mautic.current_lead_changed` | `LeadChangeEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::DEVICE_POST_DELETE` | `mautic.lead_device_post_delete` | `DevicePostDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::DEVICE_POST_SAVE` | `mautic.lead_device_post_save` | `DevicePostSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::DEVICE_PRE_DELETE` | `mautic.lead_device_pre_delete` | `DevicePreDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::DEVICE_PRE_SAVE` | `mautic.lead_device_pre_save` | `DevicePreSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::FIELD_POST_DELETE` | `mautic.lead_field_post_delete` | `FieldPostDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::FIELD_POST_SAVE` | `mautic.lead_field_post_save` | `FieldPostSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::FIELD_PRE_DELETE` | `mautic.lead_field_pre_delete` | `FieldPreDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::FIELD_PRE_SAVE` | `mautic.lead_field_pre_save` | `FieldPreSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::IMPORT_BATCH_PROCESSED` | `mautic.lead_import_batch_processed` | `ImportBatchProcessedEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::IMPORT_POST_DELETE` | `mautic.lead_import_post_delete` | `ImportPostDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::IMPORT_POST_SAVE` | `mautic.lead_import_post_save` | `ImportPostSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::IMPORT_PRE_DELETE` | `mautic.lead_import_pre_delete` | `ImportPreDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::IMPORT_PRE_SAVE` | `mautic.lead_import_pre_save` | `ImportPreSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LEAD_IDENTIFIED` | `mautic.lead_identified` | `LeadIdentifiedEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LEAD_LIST_BATCH_CHANGE` | `mautic.lead_list_batch_change` | `ListBatchChangeEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LEAD_POST_BATCH_SAVE` | `mautic.lead_post_batch_save` | `LeadPostBatchSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LEAD_POST_MERGE` | `mautic.lead_post_merge` | `LeadPostMergeEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LEAD_PRE_BATCH_SAVE` | `mautic.lead_pre_batch_save` | `LeadPreBatchSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LEAD_PRE_DELETE` | `mautic.lead_pre_delete` | `LeadPreDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LEAD_PRE_MERGE` | `mautic.lead_pre_merge` | `LeadPreMergeEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LEAD_PRE_SAVE` | `mautic.lead_pre_save` | `LeadPreSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LIST_FILTERS_CHOICES_ON_GENERATE` | `mautic.list_filters_choices_on_generate` | `LeadListFiltersChoicesEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LIST_FILTERS_ON_FILTERING` | `mautic.list_filters_on_filtering` | `LeadListFilteringEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LIST_POST_DELETE` | `mautic.lead_list_post_delete` | `ListPostDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LIST_POST_SAVE` | `mautic.lead_list_post_save` | `ListPostSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LIST_PRE_DELETE` | `mautic.lead_list_pre_delete` | `ListPreDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LIST_PRE_PROCESS_LIST` | `mautic.list_pre_process_list` | `ListPreProcessListEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LIST_PRE_SAVE` | `mautic.lead_list_pre_save` | `ListPreSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::LIST_PRE_UNPUBLISH` | `mautic.lead_list_pre_unpublish` | `ListPreUnpublishEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::NOTE_POST_DELETE` | `mautic.lead_note_post_delete` | `NotePostDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::NOTE_POST_SAVE` | `mautic.lead_note_post_save` | `NotePostSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::NOTE_PRE_DELETE` | `mautic.lead_note_pre_delete` | `NotePreDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::NOTE_PRE_SAVE` | `mautic.lead_note_pre_save` | `NotePreSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.lead.on_campaign_trigger_action` | (none) - register `batchEventName` => `LeadEvents::ON_CAMPAIGN_BATCH_ACTION`, listen on `PendingEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::ON_CLICKTHROUGH_IDENTIFICATION` | `mautic.clickthrough_contact_identification` | `ContactIdentificationEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::ON_LIST_DELETE` | `mautic.lead_list_delete` | `ListDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::POST_CONTACT_EXPORT` | `mautic.post_contact_export` | `ContactExportEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::POST_CONTACT_EXPORT_SCHEDULED` | `mautic.post_contact_export_scheduled` | `ContactExportScheduledEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::POST_CONTACT_EXPORT_SEND_EMAIL` | `mautic.post_contact_export_send_email` | `ContactExportEmailSentEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::SEGMENT_DICTIONARY_ON_GENERATE` | `mautic.list_dictionary_on_generate` | `SegmentDictionaryGenerationEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::TAG_POST_DELETE` | `mautic.lead_tag_post_delete` | `TagPostDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::TAG_POST_MERGE` | `mautic.lead_tag_post_merge` | `TagPostMergeEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::TAG_POST_SAVE` | `mautic.lead_tag_post_save` | `TagPostSaveEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::TAG_PRE_DELETE` | `mautic.lead_tag_pre_delete` | `TagPreDeleteEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::TAG_PRE_MERGE` | `mautic.lead_tag_pre_merge` | `TagPreMergeEvent` | #17077, #17218, #17545, #17625 |
| LeadBundle | `LeadEvents::TAG_PRE_SAVE` | `mautic.lead_tag_pre_save` | `TagPreSaveEvent` | #17077, #17218, #17545, #17625 |
| PageBundle | `PageEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.page.on_campaign_trigger_action` | (none) - register `batchEventName` => `PageEvents::ON_CAMPAIGN_BATCH_ACTION`, listen on `PendingEvent` | #17097, #17203, #17638 |
| PageBundle | `PageEvents::PAGE_ON_BUILD` | `mautic.page_on_build` | `PageBuilderEvent` | #17097, #17203, #17638 |
| PageBundle | `PageEvents::PAGE_ON_DISPLAY` | `mautic.page_on_display` | `PageDisplayEvent` | #17097, #17203, #17638 |
| PluginBundle | `PluginEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.plugin.on_campaign_trigger_action` | (none) - register `batchEventName` => `PluginEvents::ON_CAMPAIGN_BATCH_ACTION`, listen on `PendingEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::ON_FORM_SUBMIT_ACTION_TRIGGERED` | `mautic.plugin.on_form_submit_action_triggered` | (none - unused) | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::ON_PLUGIN_INSTALL` | `mautic.plugin.on_plugin_install` | `PluginInstallEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::ON_PLUGIN_UPDATE` | `mautic.plugin.on_plugin_update` | `PluginUpdateEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::PLUGIN_IS_PUBLISHED_STATE_CHANGING` | `mautic.plugin.is_published_state_changing` | `PluginIsPublishedEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::PLUGIN_ON_INTEGRATION_AUTH_REDIRECT` | `mautic.plugin_on_integration_auth_redirect` | `PluginIntegrationAuthRedirectEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::PLUGIN_ON_INTEGRATION_CONFIG_SAVE` | `mautic.plugin_on_integration_config_save` | `PluginIntegrationEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::PLUGIN_ON_INTEGRATION_FORM_BUILD` | `mautic.plugin_on_integration_form_build` | `PluginIntegrationFormBuildEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::PLUGIN_ON_INTEGRATION_FORM_DISPLAY` | `mautic.plugin_on_integration_form_display` | `PluginIntegrationFormDisplayEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::PLUGIN_ON_INTEGRATION_GET_AUTH_CALLBACK_URL` | `mautic.plugin_on_integration_get_auth_callback_url` | `PluginIntegrationAuthCallbackUrlEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::PLUGIN_ON_INTEGRATION_REQUEST` | `mautic.plugin_on_integration_request` | `PluginIntegrationRequestEvent` | #17097, #17162, #17625 |
| PluginBundle | `PluginEvents::PLUGIN_ON_INTEGRATION_RESPONSE` | `mautic.plugin_on_integration_response` | `PluginIntegrationResponseEvent` (new class) | #17097, #17162, #17625 |
| SmsBundle | `SmsEvents::DNC_FILTER_CONTACTS_ON_SEND` | `mautic.sms.dnc_filter_contacts_on_send` | `DncEvent` | #17216, #17622 |
| SmsBundle | `SmsEvents::FILTER_CONTACTS_ON_SEND` | `mautic.sms.filter_contacts_on_send` | `FilterEvent` | #17216, #17622 |
| SmsBundle | `SmsEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.sms.on_campaign_trigger_action` | (none - unused) | #17216, #17622 |
| SmsBundle | `SmsEvents::ON_REPLY` | `mautic.sms.on_reply` | `ReplyEvent` | #17216, #17622 |
| SmsBundle | `SmsEvents::ON_SMS_TOKENS_BUILD` | `mautic.sms.on_tokens_build` | `TokensBuildEvent` | #17216, #17622 |
| SmsBundle | `SmsEvents::QUEUE_FILTER_CONTACTS_ON_SEND` | `mautic.sms.queue_filter_contacts_on_send` | `QueueEvent` | #17216, #17622 |
| SmsBundle | `SmsEvents::SMS_POST_DELETE` | `mautic.sms_post_delete` | `SmsPostDeleteEvent` | #17216, #17622 |
| SmsBundle | `SmsEvents::SMS_POST_SAVE` | `mautic.sms_post_save` | `SmsPostSaveEvent` | #17216, #17622 |
| SmsBundle | `SmsEvents::SMS_PRE_DELETE` | `mautic.sms_pre_delete` | `SmsPreDeleteEvent` | #17216, #17622 |
| SmsBundle | `SmsEvents::SMS_PRE_SAVE` | `mautic.sms_pre_save` | `SmsPreSaveEvent` | #17216, #17622 |
| StageBundle | `StageEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.stage.on_campaign_trigger_action` | (none) - register `batchEventName` => `StageEvents::ON_CAMPAIGN_BATCH_ACTION`, listen on `PendingEvent` | #17059 |
| StatsBundle | `StatEvents::AGGREGATE_STAT_REQUEST` | `mautic.aggregate_stat_request` | `AggregateStatRequestEvent` | #17654 |
| UserBundle | `UserEvents::ROLE_POST_DELETE` | `mautic.role_post_delete` | `PostDeleteRoleEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::ROLE_POST_SAVE` | `mautic.role_post_save` | `PostSaveRoleEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::ROLE_PRE_DELETE` | `mautic.role_pre_delete` | `PreDeleteRoleEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::ROLE_PRE_SAVE` | `mautic.role_pre_save` | `PreSaveRoleEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_AUTHENTICATION_CONTENT` | `mautic.user_authentication_content` | `AuthenticationContentEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_FORM_AUTHENTICATION` | `mautic.user_form_authentication` | `FormAuthenticationEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_FORM_POST_LOCAL_PASSWORD_AUTHENTICATION` | `mautic.user_form_post_local_password_authentication` | (none - never dispatched) | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_LOGIN` | `mautic.user_login` | `LoginEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_LOGOUT` | `mautic.user_logout` | `LogoutEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_PASSWORD_STRENGTH_VALIDATION` | `mautic.user_password_strength_validation` | `PasswordStrengthValidateEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_POST_DELETE` | `mautic.user_post_delete` | `PostDeleteUserEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_POST_SAVE` | `mautic.user_post_save` | `PostSaveUserEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_PRE_AUTHENTICATION` | `mautic.user_pre_authentication` | `PreAuthenticationEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_PRE_DELETE` | `mautic.user_pre_delete` | `PreDeleteUserEvent` | #17217, #17510, #17623, #17654 |
| UserBundle | `UserEvents::USER_PRE_SAVE` | `mautic.user_pre_save` | `PreSaveUserEvent` | #17217, #17510, #17623, #17654 |
| WebhookBundle | `WebhookEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.webhook.campaign_on_trigger_action` | (none) - register `batchEventName` => `WebhookEvents::ON_CAMPAIGN_BATCH_ACTION`, listen on `PendingEvent` | #17085, #17202, #17654 |
| WebhookBundle | `WebhookEvents::WEBHOOK_KILL` | `mautic.webhook_kill` | `WebhookKillEvent` | #17085, #17202, #17654 |
| WebhookBundle | `WebhookEvents::WEBHOOK_POST_DELETE` | `mautic.webhook_post_delete` | `WebhookPostDeleteEvent` | #17085, #17202, #17654 |
| WebhookBundle | `WebhookEvents::WEBHOOK_POST_SAVE` | `mautic.webhook_post_save` | `WebhookPostSaveEvent` | #17085, #17202, #17654 |
| WebhookBundle | `WebhookEvents::WEBHOOK_PRE_DELETE` | `mautic.webhook_pre_delete` | `WebhookPreDeleteEvent` | #17085, #17202, #17654 |
| WebhookBundle | `WebhookEvents::WEBHOOK_PRE_SAVE` | `mautic.webhook_pre_save` | `WebhookPreSaveEvent` | #17085, #17202, #17654 |
| MauticFocusBundle | `FocusEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.focus.on_campaign_trigger_action` | (none) - register `batchEventName` => `FocusEvents::ON_CAMPAIGN_BATCH_ACTION`, listen on `PendingEvent` | #17097, #17223, #17782 |
| MauticFocusBundle | `FocusEvents::TOKEN_REPLACEMENT` | `mautic.focus_token_replacement` | `FocusTokenReplacementEvent` (extends `AbstractTokenReplacementEvent`) | #17097, #17223, #17782 |
| MauticSocialBundle | `SocialEvents::MONITOR_POST_DELETE` | `mautic.monitor_post_delete` | `MonitorPostDeleteEvent` | #17097, #17544 |
| MauticSocialBundle | `SocialEvents::MONITOR_POST_PROCESS` | `mautic.monitor_post_process` | `SocialMonitorEvent` | #17097, #17544 |
| MauticSocialBundle | `SocialEvents::MONITOR_POST_SAVE` | `mautic.monitor_post_save` | `MonitorPostSaveEvent` | #17097, #17544 |
| MauticSocialBundle | `SocialEvents::MONITOR_PRE_DELETE` | `mautic.monitor_pre_delete` | `MonitorPreDeleteEvent` | #17097, #17544 |
| MauticSocialBundle | `SocialEvents::MONITOR_PRE_SAVE` | `mautic.monitor_pre_save` | `MonitorPreSaveEvent` | #17097, #17544 |
| MauticSocialBundle | `SocialEvents::ON_CAMPAIGN_TRIGGER_ACTION` | `mautic.social.on_campaign_trigger_action` | (none) - register `batchEventName` => `SocialEvents::ON_CAMPAIGN_BATCH_ACTION`, listen on `PendingEvent` | #17097, #17544 |
| MauticSocialBundle | `SocialEvents::TWEET_POST_DELETE` | `mautic.tweet_post_delete` | `TweetPostDeleteEvent` | #17097, #17544 |
| MauticSocialBundle | `SocialEvents::TWEET_POST_SAVE` | `mautic.tweet_post_save` | `TweetPostSaveEvent` | #17097, #17544 |
| MauticSocialBundle | `SocialEvents::TWEET_PRE_DELETE` | `mautic.tweet_pre_delete` | `TweetPreDeleteEvent` | #17097, #17544 |
| MauticSocialBundle | `SocialEvents::TWEET_PRE_SAVE` | `mautic.tweet_pre_save` | `TweetPreSaveEvent` | #17097, #17544 |

Per-bundle counts: ApiBundle 9, AssetBundle 7, CampaignBundle 21, ConfigBundle 3, CoreBundle 15, DashboardBundle 4, DynamicContentBundle 7, EmailBundle 20, IntegrationsBundle 23, LeadBundle 56, MauticFocusBundle 2, MauticSocialBundle 10, PageBundle 3, PluginBundle 12, SmsBundle 10, StageBundle 1, StatsBundle 1, UserBundle 15, WebhookBundle 6 ; total 225
