# Campaigns — code map (Mautic 7.x)

Paths relative to `app/bundles/CampaignBundle/` unless they start with `app/` or `plugins/`.

## Table of contents
1. Entities and tables
2. Repositories
3. Services and models
4. Events (CampaignEvents)
5. Registered campaign event keys (full table)
6. Routes and UI
7. REST API
8. Console commands
9. Configuration parameters
10. Permissions
11. Tests
12. Extension hooks

## 1. Entities and tables
| Entity | Table | Key facts | Source |
|---|---|---|---|
| `Entity/Campaign.php` | `campaigns` | `name`, `description`, `publish_up/down`, `republish_behavior` (string 32, nullable), `category_id`, `canvas_settings` (serialized nodes/connections), `allow_restart` (bool, default false), `deleted` (soft delete), `version` (optimistic lock), `uuid`; relations `events`, `leads`, `lists` (`campaign_leadlist_xref`), `forms` (`campaign_form_xref`), projects (`campaign_projects_xref`); validator `NoOrphanEvents` | [code: app/bundles/CampaignBundle/Entity/Campaign.php:55-223 @7.x] |
| `Entity/Event.php` | `campaign_events` | `type` (registered key), `event_type` (action/decision/condition), `event_order`, `properties`, `deleted`, `redirect_event_id`, `trigger_mode` (immediate/interval/date/optimized), `trigger_date`, `trigger_interval`, `trigger_interval_unit` (i,h,d,m,y), `trigger_hour`, `trigger_restricted_start_hour/stop_hour`, `trigger_restricted_dow`, `trigger_window`, `parent_id`, `decision_path` (yes/no/null), `temp_id`, `channel`, `channel_id`, `failed_count`, `uuid`, `date_linked` | [code: app/bundles/CampaignBundle/Entity/Event.php:54-72,265-410 @7.x] |
| `Entity/Lead.php` | `campaign_leads` | PK (`campaign_id`,`lead_id`); `date_added`, `manually_removed`, `manually_added`, `date_last_exited`, `rotation` (default 1) | [code: app/bundles/CampaignBundle/Entity/Lead.php:52-78 @7.x] |
| `Entity/LeadEventLog.php` | `campaign_lead_event_log` | bigint id; `event_id`, `lead_id`, `campaign_id`, `ip_id`, `rotation`, `date_triggered`, `is_scheduled`, `trigger_date`, `system_triggered`, `metadata`, `channel`, `channel_id`, `non_action_path_taken`, `date_queued`, `version`; unique `campaign_rotation(event_id, lead_id, rotation)` | [code: app/bundles/CampaignBundle/Entity/LeadEventLog.php:110-186 @7.x] |
| `Entity/FailedLeadEventLog.php` | `campaign_lead_event_failed_log` | PK `log_id`, `date_added`, `reason` | [code: app/bundles/CampaignBundle/Entity/FailedLeadEventLog.php:34-44 @7.x] |
| `Entity/Summary.php` | `campaign_summary` | hour bucket counts; unique (campaign, event, date_triggered) | [code: app/bundles/CampaignBundle/Entity/Summary.php:57-83 @7.x] |

MySQL generated columns `generated_date_added_{hour,day,week,month,year}` are added to `campaign_leads` [code: app/bundles/CampaignBundle/EventListener/GeneratedColumnSubscriber.php:27-55 @7.x].

## 2. Repositories
| Repository | Notable methods | Source |
|---|---|---|
| `CampaignRepository` | `getEntities()` excludes deleted; `setCampaignAsDeleted()`; `getPendingContactIds()` (kickoff); `findStuckEventsToExecute()`; `getCampaignPublishAndVersionData()` (FOR UPDATE); `getPublishedCampaigns()` | [code: app/bundles/CampaignBundle/Entity/CampaignRepository.php:25-827 @7.x] |
| `LeadRepository` | `getCampaignContactsBySegments`, `getOrphanedContacts`, `getInactiveContacts`, `getContactRotations`, `incrementCampaignRotationForContacts`, `updateLead` (merge) | [code: app/bundles/CampaignBundle/Entity/LeadRepository.php:92-660 @7.x] |
| `LeadEventLogRepository` | `getScheduled`, `getScheduledByIds`, `getScheduledCounts`, `unscheduleEvents`, `getCampaignLogCounts`, `getLeadLogs`, `getUpcomingEvents`, `markEventLogsQueued` | [code: app/bundles/CampaignBundle/Entity/LeadEventLogRepository.php:67-742 @7.x] |
| `EventRepository` | `getContactPendingEvents` (real time), `setEventsAsDeletedWithRedirect`, failed-count helpers | [code: app/bundles/CampaignBundle/Entity/EventRepository.php:56-533 @7.x] |

## 3. Services and models
| Class | Responsibility | Source |
|---|---|---|
| `Model/CampaignModel` | CRUD + lifecycle events, `setEvents()`, `setCanvasSettings()`, `setLeadSources()`, `transactionalCampaignUnPublish()` | [code: app/bundles/CampaignBundle/Model/CampaignModel.php:101-936 @7.x] |
| `Model/EventModel` | soft delete with redirect, delete events | [code: app/bundles/CampaignBundle/Model/EventModel.php:74-142 @7.x] |
| `Model/EventLogModel` | API log edits via `EventScheduler::rescheduleLogs()` | [code: app/bundles/CampaignBundle/Model/EventLogModel.php:82-213 @7.x] |
| `Model/SummaryModel` | summary buffering/backfill | [code: app/bundles/CampaignBundle/Model/SummaryModel.php:41-169 @7.x] |
| `Membership/MembershipBuilder`, `MembershipManager`, `Action/Adder`, `Action/Remover` | membership sync and rules | [code: app/bundles/CampaignBundle/Membership/MembershipManager.php:37-219 @7.x] |
| `Executioner/*Executioner` | kickoff, scheduled, inactive, real-time, event | [code: app/bundles/CampaignBundle/Executioner/EventExecutioner.php:109-425 @7.x] |
| `Executioner/Scheduler/EventScheduler` + `Mode/{Interval,DateTime,Optimized}` | dates, rescheduling, republish | [code: app/bundles/CampaignBundle/Executioner/Scheduler/EventScheduler.php:89-433 @7.x] |
| `Executioner/Dispatcher/{Action,Condition,Decision,LegacyEvent}Dispatcher` | per-type dispatch | [code: app/bundles/CampaignBundle/Executioner/Dispatcher/ActionDispatcher.php:35-124 @7.x] |
| `Executioner/Logger/EventLogger` | log creation/persistence | [code: app/bundles/CampaignBundle/Executioner/Logger/EventLogger.php:47-219 @7.x] |
| `Executioner/ContactFinder/Limiter/ContactLimiter` | command option limits | [code: app/bundles/CampaignBundle/Executioner/ContactFinder/Limiter/ContactLimiter.php:41-121 @7.x] |
| `Executioner/Helper/{Decision,Inactive,EventRedirection,Notification}Helper` | decision rules, inactivity, redirects, notifications | [code: app/bundles/CampaignBundle/Executioner/Helper/DecisionHelper.php:22-64 @7.x] |
| `EventCollector/EventCollector` | registry of event types | [code: app/bundles/CampaignBundle/EventCollector/EventCollector.php:26-84 @7.x] |
| `Service/PublishStateService` | publish history for republish behaviour | [code: app/bundles/CampaignBundle/Service/PublishStateService.php:28-303 @7.x] |
| `Service/CampaignShareService` | marketplace ZIP + token | [code: app/bundles/CampaignBundle/Service/CampaignShareService.php:20-61 @7.x] |
| `Helper/ChannelExtractor`, `Helper/RemovedContactTracker`, `Helper/CampaignContactCountHelper` | channel fields, deleted-contact tracking, cached counts | [code: app/bundles/CampaignBundle/Helper/ChannelExtractor.php:11-59 @7.x] |

## 4. Events (CampaignEvents)
| Constant (value) | Event class | Dispatched at | Core listener | 8.x |
|---|---|---|---|---|
| `CAMPAIGN_PRE_SAVE` | `CampaignEvent` | `Model/CampaignModel.php:188-209` | `CampaignEventSubscriber::onCampaignPreSave` | `CampaignPreSaveEvent` |
| `CAMPAIGN_POST_SAVE` | `CampaignEvent` | `Model/CampaignModel.php:191` | audit, jump-target resolution | `CampaignPostSaveEvent` |
| `CAMPAIGN_PRE_DELETE` / `CAMPAIGN_POST_DELETE` | `CampaignEvent` | `Model/CampaignModel.php:161,171` | audit | `CampaignPreDeleteEvent` / `CampaignPostDeleteEvent` |
| `ON_CAMPAIGN_DELETE` | `DeleteCampaign` | `Model/CampaignModel.php:164` | log purge | class |
| `CAMPAIGN_ON_BUILD` (`mautic.campaign_on_build`) | `CampaignBuilderEvent` | `EventCollector/EventCollector.php:77` | every bundle's CampaignSubscriber | `CampaignBuilderEvent` |
| `CAMPAIGN_ON_TRIGGER` | `CampaignTriggerEvent` (`doNotTrigger()`) | `Command/TriggerCampaignCommand.php:288-296` | none | class |
| `CAMPAIGN_ON_LEADCHANGE` / `LEAD_CAMPAIGN_BATCH_CHANGE` | `CampaignLeadChangeEvent` | `Membership/EventDispatcher.php:21-35` | LeadBundle timeline | `CampaignSingleLeadChangeEvent` / `CampaignBatchLeadChangeEvent` |
| `ON_EVENT_EXECUTED` / `ON_EVENT_EXECUTED_BATCH` | `ExecutedEvent` / `ExecutedBatchEvent` | `Executioner/Dispatcher/ActionDispatcher.php:75-85` | failed-count decrease; failed-log cleanup | class |
| `ON_EVENT_FAILED` | `FailedEvent` | `ActionDispatcher.php:95-104` | failure escalation | class |
| `ON_EVENT_SCHEDULED` / `_BATCH` | `ScheduledEvent` / `ScheduledBatchEvent` | `Executioner/Scheduler/EventScheduler.php:348-366` | none in bundle | class |
| `ON_EVENT_DELETE` / `ON_AFTER_EVENTS_DELETE` | `DeleteEvent` | `Model/EventModel.php:98,115` | delete subscriber | `DeleteEvent` / `AfterEventsDeleteEvent` |
| `ON_EVENT_DECISION_EVALUATION` / `_RESULTS` | `DecisionEvent` / `DecisionResultsEvent` | `Dispatcher/DecisionDispatcher.php:33-53` | none | constant kept / class |
| `ON_EVENT_CONDITION_EVALUATION` (same string as decision evaluation) | `ConditionEvent` | `Dispatcher/ConditionDispatcher.php:22` | — | constant kept |
| `ON_EVENT_JUMP_TO_EVENT` | `PendingEvent` | batch name of `campaign.jump_to_event` | jump subscriber | constant kept |
| `ON_CAMPAIGN_ACTION_CHANGE_MEMBERSHIP` | `PendingEvent` | batch name of `campaign.addremovelead` | membership subscriber | constant kept |
| `ON_EVENT_EXECUTION`, `ON_EVENT_DECISION_TRIGGER` (legacy) | `CampaignExecutionEvent`, `CampaignDecisionEvent` | `LegacyEventDispatcher.php` | legacy plugins | removed |
| `ON_CAMPAIGN_FAILURE_NOTIFY` / `ON_CAMPAIGN_UNPUBLISH_NOTIFY` | `NotifyOfFailureEvent` / `NotifyOfUnpublishEvent` | `EventListener/CampaignEventSubscriber.php:117-139` | `NotificationHelper` | class |

Sources: [code: app/bundles/CampaignBundle/CampaignEvents.php:20-248 @7.x]; 8.x column from the 8.x constant table [PR #17161] [PR #17225].

## 5. Registered campaign event keys (full table)
Registered via `CampaignBuilderEvent::addAction/addDecision/addCondition` [code: app/bundles/CampaignBundle/Event/CampaignBuilderEvent.php:50-196 @7.x].

| Bundle / file | Key | Kind | Executes via |
|---|---|---|---|
| `app/bundles/CampaignBundle/EventListener/CampaignActionChangeMembershipSubscriber.php:40-51` | `campaign.addremovelead` | action | `CampaignEvents::ON_CAMPAIGN_ACTION_CHANGE_MEMBERSHIP` |
| `app/bundles/CampaignBundle/EventListener/CampaignActionJumpToEventSubscriber.php:46-59` | `campaign.jump_to_event` | action (no outgoing connections) | `CampaignEvents::ON_EVENT_JUMP_TO_EVENT` |
| `app/bundles/AssetBundle/EventListener/CampaignSubscriber.php:42` | `asset.download` | decision | `AssetEvents::ON_CAMPAIGN_TRIGGER_DECISION`; fired at :53 |
| `app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:81` | `message.send` | action | `ChannelEvents::ON_CAMPAIGN_BATCH_ACTION` |
| `app/bundles/DynamicContentBundle/EventListener/CampaignSubscriber.php:41-72` | `dwc.push_content` | action | `DynamicContentEvents::ON_CAMPAIGN_TRIGGER_ACTION` |
| same | `dwc.decision` | decision | `DynamicContentEvents::ON_CAMPAIGN_TRIGGER_DECISION` |
| `app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:66-134` | `email.send`, `email.send.to.user` | action | `EmailEvents::ON_CAMPAIGN_BATCH_ACTION` |
| same | `email.open`, `email.click`, `email.reply` | decision | `EmailEvents::ON_CAMPAIGN_TRIGGER_DECISION` |
| `app/bundles/EmailBundle/EventListener/CampaignConditionSubscriber.php:31-36` | `email.validate.address` | condition | `EmailEvents::ON_CAMPAIGN_TRIGGER_CONDITION` |
| `app/bundles/FormBundle/EventListener/CampaignSubscriber.php:51-62` | `form.submit` | decision | `FormEvents::ON_CAMPAIGN_TRIGGER_DECISION` |
| same | `form.field_value` | condition | `FormEvents::ON_CAMPAIGN_TRIGGER_CONDITION` |
| `app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:110-170` | `lead.changepoints`, `lead.changelist`, `lead.updatelead` (batch), `lead.updatecompany`, `lead.changetags`, `lead.addtocompany`, `lead.changeowner`, `lead.scorecontactscompanies` | action | `LeadEvents::ON_CAMPAIGN_TRIGGER_ACTION` / `ON_CAMPAIGN_BATCH_ACTION` |
| `app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:179-270` | `lead.field_value`, `lead.device`, `lead.pageHit`, `lead.tags`, `lead.segments`, `lead.stages`, `lead.owner`, `lead.attached` ("Prevent action after date"), `lead.campaigns`, `lead.dnc`, `lead.points` | condition | `LeadEvents::ON_CAMPAIGN_TRIGGER_CONDITION` |
| `app/bundles/LeadBundle/EventListener/CampaignActionDNCSubscriber.php:35-50` | `lead.adddnc`, `lead.removednc` | action | `LeadEvents::ON_CAMPAIGN_ACTION_ADD/REMOVE_DONOTCONTACT` |
| `app/bundles/LeadBundle/EventListener/CampaignActionDeleteContactSubscriber.php:31-47` | `lead.deletecontact` | action (no outgoing connections) | `LeadEvents::ON_CAMPAIGN_ACTION_DELETE_CONTACT` |
| `app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:76-97` | `notification.send_mobile_notification` (if enabled), `notification.send_notification` | action | `NotificationEvents::ON_CAMPAIGN_BATCH_ACTION` |
| `app/bundles/NotificationBundle/EventListener/CampaignConditionSubscriber.php:24-29` | `notification.has.active` | condition | `NotificationEvents::ON_CAMPAIGN_TRIGGER_CONDITION` |
| `app/bundles/PageBundle/EventListener/CampaignSubscriber.php:57-88` | `page.pagehit`, `page.devicehit` | decision | `PageEvents::ON_CAMPAIGN_TRIGGER_DECISION`; fired at :106-107 |
| same | `tracking.pixel.send` | action | `PageEvents::ON_CAMPAIGN_TRIGGER_ACTION` |
| `app/bundles/PluginBundle/EventListener/CampaignSubscriber.php:34` | `plugin.leadpush` | action | `PluginEvents::ON_CAMPAIGN_TRIGGER_ACTION` |
| `app/bundles/SmsBundle/EventListener/CampaignSendSubscriber.php:36-41` | `sms.send_text_sms` | action | `SmsEvents::ON_CAMPAIGN_TRIGGER_BATCH_ACTION` |
| `app/bundles/SmsBundle/EventListener/CampaignReplySubscriber.php:18,41-46` | `sms.reply` | decision | `SmsEvents::ON_CAMPAIGN_REPLY`; fired at :83 |
| `app/bundles/StageBundle/EventListener/CampaignSubscriber.php:43` | `stage.change` | action | `StageEvents::ON_CAMPAIGN_BATCH_ACTION` |
| `app/bundles/WebhookBundle/EventListener/CampaignSubscriber.php:50-52` | `campaign.sendwebhook` | action | `WebhookEvents::ON_CAMPAIGN_TRIGGER_ACTION` |
| `plugins/MauticFocusBundle/EventListener/CampaignSubscriber.php:53` | `focus.show` | action | `FocusEvents::ON_CAMPAIGN_TRIGGER_ACTION` |
| `plugins/MauticSocialBundle/EventListener/CampaignSubscriber.php:46` | `twitter.tweet` | action | `SocialEvents::ON_CAMPAIGN_TRIGGER_ACTION` |

In 8.x every `*::ON_CAMPAIGN_TRIGGER_ACTION` above is replaced by an `ON_CAMPAIGN_BATCH_ACTION` handled with `PendingEvent` [PR #17097] [PR #17085] [PR #17691].

## 6. Routes and UI
| Route | Path | Controller |
|---|---|---|
| `mautic_campaignevent_action` | `/campaigns/events/{objectAction}/{objectId}` | `EventController::executeAction` (new, edit, delete, undelete, clone, insert; AJAX) |
| `mautic_campaignsource_action` | `/campaigns/sources/{objectAction}/{objectId}` | `SourceController::executeAction` |
| `mautic_campaign_index` | `/campaigns/{page}` | `CampaignController::indexAction` |
| `mautic_campaign_action` | `/campaigns/{objectAction}/{objectId}` | `CampaignController::executeAction` (new, edit, view, clone, delete, batchDelete, export, batchExport, share) |
| `mautic_campaign_contacts` | `/campaigns/view/{objectId}/contact/{page}` | `CampaignController::contactsAction` |
| `mautic_campaign_event_stats` / `mautic_campaign_graph` | `/campaigns/event/stats/...`, `/campaigns/graph/...` | `CampaignController` |
| `mautic_campaign_import_index` / `_action` | `/campaign/import[/{objectAction}]` | `ImportController` |
| `mautic_campaign_share_download` (public) | `/campaign-share/{token}` | `CampaignShareDownloadController::downloadAction` |
| metrics / map stats | `/campaign/metrics/...`, `/campaign-map-stats/...` | `CampaignMetricsController`, `CampaignMapStatsController` |

Source: [code: app/bundles/CampaignBundle/Config/config.php:8-74 @7.x]. AJAX: `updateConnectionsAction`, `updateScheduledCampaignEventAction`, `cancelScheduledCampaignEventAction` [code: app/bundles/CampaignBundle/Controller/AjaxController.php:39-108 @7.x]. Builder JS: `Assets/js/campaign.js` (`Mautic.launchCampaignEditor`, `campaignBuilderValidateConnection`, `saveCampaignFromBuilder`, `updateJumpToEventOptions`) [code: app/bundles/CampaignBundle/Assets/js/campaign.js @7.x].

## 7. REST API
| Method | Path | Notes | Source |
|---|---|---|---|
| GET | `/api/campaigns` | params `search`, `start`, `limit`, `orderBy`, `orderByDir`, `published` (not `publishedOnly`), `minimal`, `withContactCounts` | [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:167 @7.x] [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:89-90 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html#list-campaigns] |
| GET | `/api/campaigns/{id}` | campaign with events keyed by id | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html#get-campaign] |
| POST | `/api/campaigns/new` | needs `events` and `lists` or `forms` | [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:179-193 @7.x] |
| PUT/PATCH | `/api/campaigns/{id}/edit` | PUT deletes missing events/sources; events need `id` | [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:194-218 @7.x] |
| DELETE | `/api/campaigns/{id}/delete` | | [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html] |
| GET | `/api/campaigns/{id}/contacts` | memberships | [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:324 @7.x] |
| POST | `/api/campaigns/{id}/contact/{leadId}/add` / `remove` | `{"success":1}`; needs Contact edit permission | [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:123-171 @7.x] |
| POST | `/api/campaigns/clone/{campaignId}` | | [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:366-399 @7.x] |
| GET | `/api/campaigns/export/{campaignId}` | JSON or ZIP | [code: app/bundles/CampaignBundle/Config/config.php:131-135 @7.x] |
| POST | `/api/campaigns/import` | JSON or ZIP; 201 on success | [code: app/bundles/CampaignBundle/Config/config.php:136-140 @7.x] [code: app/bundles/CampaignBundle/Controller/Api/CampaignApiController.php:487 @7.x] |
| GET | `/api/campaigns/events`, `/api/campaigns/events/{id}` | read only | [code: app/bundles/CampaignBundle/Config/config.php:75-141 @7.x] |
| GET | `/api/campaigns/events/contact/{contactId}`, `/api/campaigns/{campaignId}/events/contact/{contactId}` | Contact logs | same |
| PUT | `/api/campaigns/events/{eventId}/contact/{contactId}/edit`, `/api/campaigns/events/batch/edit` | edit logs | [code: app/bundles/CampaignBundle/Controller/Api/EventLogApiController.php:139-260 @7.x] |

Campaign and Event are also API Platform resources [code: app/bundles/CampaignBundle/Entity/Campaign.php:36-54 @7.x].

## 8. Console commands
| Command | Options | Lock | Source |
|---|---|---|---|
| `mautic:campaigns:rebuild` (alias `mautic:campaigns:update`) | `--batch-limit/-l` (300), `--max-contacts/-m`, `--campaign-id/-i`, `--contact-id`, `--contact-ids`, `--min-contact-id`, `--max-contact-id`, `--thread-id`, `--max-threads`, `--exclude/-d` | campaign id | [code: app/bundles/CampaignBundle/Command/UpdateLeadCampaignsCommand.php:47-234 @7.x] |
| `mautic:campaigns:trigger` | `--campaign-id/-i`, `--campaign-limit`, contact options, `--thread-id`, `--max-threads`, `--kickoff-only`, `--scheduled-only`, `--inactive-only`, `--batch-limit/-l` (100), `--exclude/-d` | `{campaign-id}-{thread-id}` | [code: app/bundles/CampaignBundle/Command/TriggerCampaignCommand.php:74-359 @7.x] |
| `mautic:campaigns:execute` | `--scheduled-log-ids` (required), `--execution-time` | none | [code: app/bundles/CampaignBundle/Command/ExecuteEventCommand.php:30-54 @7.x] |
| `mautic:campaigns:validate` | `--decision-id` (required), `--contact-id`, `--contact-ids` | none | [code: app/bundles/CampaignBundle/Command/ValidateEventCommand.php:76-89 @7.x] |
| `mautic:campaigns:summarize` | `--batch-limit/-l` (hours, 1), `--max-hours`, `--rebuild` | moderated | [code: app/bundles/CampaignBundle/Command/SummarizeCommand.php:37-61 @7.x] |
| `mautic:campaign:delete-event-logs` | arg `campaign_event_ids`, `--campaign-id/-i` | none | [code: app/bundles/CampaignBundle/Command/CampaignDeleteEventLogsCommand.php:49-66 @7.x] |
| `mautic:campaigns:resume-stuck` | arg `campaign-id`, `--dry-run`, `--min-contact-id`, `--max-contact-id`, `--batch-limit/-l` (100) | none | [code: app/bundles/CampaignBundle/Command/ResumeStuckCampaignCommand.php:57-277 @7.x] |
| `mautic:entity:export --entity=campaign --id= [--zip-file --path=] [--json-only]`, `mautic:entity:import --entity=campaign --file= --user=` | CoreBundle commands | — | [docs: https://docs.mautic.org/en/7.2/campaigns/exporting_campaigns.html#using-the-command-line] [docs: https://docs.mautic.org/en/7.2/campaigns/importing_campaigns.html#using-the-command-line] |

Moderated commands add `--bypass-locking`, `--timeout`, `--lock_mode` (`pid`|`flock`|`redis`) [code: app/bundles/CoreBundle/Command/ModeratedCommand.php:56-73 @7.x].

## 9. Configuration parameters
| Parameter | Default | Effect |
|---|---|---|
| `campaign_time_wait_on_event_false` | `PT1H` | retry delay for failed actions (null = never) |
| `campaign_use_summary` | 0 | use/write `campaign_summary` |
| `campaign_by_range` | 0 | in config form; consumer not found (open) |
| `delete_campaign_event_log_in_background` | false | defer log deletion to `mautic:campaign:delete-event-logs` |
| `campaign_email_stats_enabled` | true | email stats tab |
| `peak_interaction_timer_*` | cache 43800 min, hours 9–12, days [2,1,4], fetch `-60 days`, limit 50, max days 3 | optimized scheduling |
| `import_campaigns_dir` | `%kernel.project_dir%/var/import` | import upload dir |
| `campaigns_resume_stuck_records_after` | `2025-10-01 00:00:00` | resume-stuck lower bound |
| `campaign_republish_behavior` | `count_all_time` | global republish default |
| `campaign_event_cache_ttl` | 600 | event log count cache |
| `campaign_contact_count_cache_ttl` | 43200 | contact count cache |
| `marketplace_website_url` | env `MARKETPLACE_WEBSITE_URL` | share target |

Source: [code: app/bundles/CampaignBundle/Config/config.php:160-179 @7.x]. Env `CAMPAIGN_EXECUTIONER_SCHEDULER_ACKNOWLEDGE_SECONDS` disables minute truncation [code: app/bundles/CampaignBundle/Executioner/Scheduler/EventScheduler.php:289-300 @7.x]. Failure notification parameters `campaign_send_notification_to_author`, `campaign_notification_email_addresses` [code: app/bundles/CampaignBundle/Executioner/Helper/NotificationHelper.php:26-138 @7.x].

## 10. Permissions
`campaign:campaigns:{viewown,viewother,editown,editother,create,deleteown,deleteother,publishown,publishother,cloneown,cloneother,full}`, `campaign:categories:*`, `campaign:imports:{view,edit,create,delete,full}`, `campaign:export:enable` [code: app/bundles/CampaignBundle/Security/Permissions/CampaignPermissions.php:15-22 @7.x]. Publish toggle read-only without `publish` [code: app/bundles/CampaignBundle/Form/Type/CampaignType.php:72-96 @7.x]; export/share need `campaign:export:enable` [code: app/bundles/CampaignBundle/Controller/CampaignController.php:192,224 @7.x].

## 11. Tests
See `test-patterns.md`. Directory `app/bundles/CampaignBundle/Tests/` [code: app/bundles/CampaignBundle/Tests @7.x].

## 12. Extension hooks
- `CAMPAIGN_ON_BUILD` / `CampaignBuilderEvent` to register types; registration keys `label`, `batchEventName` | `eventName`, `description`, `formType`, `formTypeOptions`, `formTypeCleanMasks`, `formTheme`, `template`, `timelineTemplate`, `connectionRestrictions`, `channel`, `channelIdField`; duplicate key → `KeyAlreadyRegisteredException` [code: app/bundles/CampaignBundle/Event/CampaignBuilderEvent.php:50-196 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#campaign-action-definition].
- `CAMPAIGN_ON_TRIGGER` veto, membership events, scheduled/executed/failed events, `EventPreview`, `MaxAllowedRecordsReachedInSingleProcessEvent`, `JobExtendTimeEvent` [code: app/bundles/CampaignBundle/CampaignEvents.php:20-248 @7.x].
- Services are autowired; legacy `mautic.campaign.*` ids are aliases [code: app/bundles/CampaignBundle/Config/services.php:9-72 @7.x].
