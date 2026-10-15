# Points and stages - code map (Mautic 7.x)

All paths are relative to the Mautic root. The citation tag `@7.x` applies throughout unless `@8.x` is given.

## Contents
1. Entities and tables
2. Services and models
3. Registry: Point Action types
4. Registry: Point Trigger event types
5. Events
6. Routes (UI, API, AJAX)
7. Permissions
8. Forms, views, translations
9. Tests
10. Extension points

## 1. Entities and tables

| Entity | File | Table | Key facts |
|---|---|---|---|
| `Point` (Point Action) | `app/bundles/PointBundle/Entity/Point.php` | `points` | `type` string(50) indexed; `repeatable` bool default false; `delta` int; `properties` array; `group_id` FK CASCADE; category; UUID; projects xref `point_projects_xref` [code: app/bundles/PointBundle/Entity/Point.php:139-172 @7.x] |
| `LeadPointLog` | `.../Entity/LeadPointLog.php` | `point_lead_action_log` | PK (point_id, lead_id); `ip_id`; `date_fired` [code: app/bundles/PointBundle/Entity/LeadPointLog.php:42-54 @7.x] |
| `Trigger` | `.../Entity/Trigger.php` | `point_triggers` | `points` threshold; `color` default `a0acb8`; `trigger_existing_leads`; `group_id` FK CASCADE; events ordered by `order` [code: app/bundles/PointBundle/Entity/Trigger.php:67-130 @7.x] |
| `TriggerEvent` | `.../Entity/TriggerEvent.php` | `point_trigger_events` | `type`, `action_order`, `properties`; ownership parent = trigger [code: app/bundles/PointBundle/Entity/TriggerEvent.php:83-110 @7.x] |
| `LeadTriggerLog` | `.../Entity/LeadTriggerLog.php` | `point_lead_event_log` | PK (event_id, lead_id) [code: app/bundles/PointBundle/Entity/LeadTriggerLog.php:30-42 @7.x] |
| `Group` | `.../Entity/Group.php` | `point_groups` | name, description; API prefix `pointGroup` [code: app/bundles/PointBundle/Entity/Group.php:18-63 @7.x] |
| `GroupContactScore` | `.../Entity/GroupContactScore.php` | `point_group_contact_score` | PK (contact_id, group_id); `score` int; inverse `Lead::$groupScores` [code: app/bundles/PointBundle/Entity/GroupContactScore.php:22-45 @7.x] |
| `PointInsight` | `.../Entity/PointInsight.php` | `point_insights` | `insight_type`, `insight_action`, `custom_field`, `point_groups` JSON; migration `Version20260616075543` [code: app/bundles/PointBundle/Entity/PointInsight.php:16-79 @7.x] [code: app/migrations/Version20260616075543.php:22 @7.x] |
| `PointsChangeLog` | `app/bundles/LeadBundle/Entity/PointsChangeLog.php` | `lead_points_change_log` | `type`, `event_name`, `action_name`, `delta`, `group_id`, `ip_id`, `date_added` (indexed) [code: app/bundles/LeadBundle/Entity/PointsChangeLog.php:38-62 @7.x] |
| `Stage` | `app/bundles/StageBundle/Entity/Stage.php` | `stages` | `weight` int, unique validation; publish dates; category; UUID; projects xref `stage_projects_xref` [code: app/bundles/StageBundle/Entity/Stage.php:60-117 @7.x] |
| `LeadStageLog` | `app/bundles/StageBundle/Entity/LeadStageLog.php` | `stage_lead_action_log` | PK (stage_id, lead_id); never written by core [code: app/bundles/StageBundle/Entity/LeadStageLog.php:30-42 @7.x] |
| `StagesChangeLog` | `app/bundles/LeadBundle/Entity/StagesChangeLog.php` | `lead_stages_change_log` | `event_name`, `action_name`, `stage_id`, `date_added` [code: app/bundles/LeadBundle/Entity/StagesChangeLog.php:29-45 @7.x] |
| Contact columns | `app/bundles/LeadBundle/Entity/Lead.php` | `leads.points`, `leads.stage_id` | `stage_id` ON DELETE SET NULL; `stageChangeLog` ordered DESC; `groupScores` cascadeAll [code: app/bundles/LeadBundle/Entity/Lead.php:317-318,416-450 @7.x] |

## 2. Services and models

| Service (alias) | Path | Key methods |
|---|---|---|
| `PointModel` (`mautic.point.model.point`) | `app/bundles/PointBundle/Model/PointModel.php` | `getPointActions()` registry (:149-162); `triggerAction($type, $eventDetails, $typeId, ?Lead, $allowUserRequest)` (:173-310); `getPointLineChartData` (:320-336); `getPointActionIdsWithDependenciesOnEmail` (:341-362) [code: app/bundles/PointBundle/Model/PointModel.php:149-362 @7.x] |
| `TriggerModel` (`mautic.point.model.trigger`) | `.../Model/TriggerModel.php` | `saveEntity` + existing contacts (:106-187); `setEvents` (:240-269); `getEvents` registry (:276-285); `triggerEvent` (:311-353); `invokeCallback` (:355-382); `triggerEvents(Lead)` (:387-423); `getColorForLeadPoints` (:430-443) [code: app/bundles/PointBundle/Model/TriggerModel.php:106-443 @7.x] |
| `TriggerEventModel` (`mautic.point.model.triggerevent`) | `.../Model/TriggerEventModel.php` | dependency finders for segment, email and tag (:57-131) [code: app/bundles/PointBundle/Model/TriggerEventModel.php:57-131 @7.x] |
| `PointGroupModel` (`mautic.point.model.group`) | `.../Model/PointGroupModel.php` | `adjustPoints(Lead, Group, int, operator)` (:100-130); `isAllowedPointOperation` (:132-135) [code: app/bundles/PointBundle/Model/PointGroupModel.php:100-135 @7.x] |
| `InsightModel` (`mautic.point.model.insight`) | `.../Model/InsightModel.php` | `executePointInsights(Lead, Group)` (:67-139) [code: app/bundles/PointBundle/Model/InsightModel.php:67-139 @7.x] |
| `StageModel` (`mautic.stage.model.stage`) | `app/bundles/StageBundle/Model/StageModel.php` | `getStageActions` (vestigial, :116-131); `getStageLineChartData` (:133-149); `stageMerge` (:151-179); `getUserStages` (:181-187) [code: app/bundles/StageBundle/Model/StageModel.php:116-187 @7.x] |
| `LeadModel` (LeadBundle) | `app/bundles/LeadBundle/Model/LeadModel.php` | `addToStage` (:997-1007), `changeStage` (:1009-1035), `removeFromStage` (:1061-1078) [code: app/bundles/LeadBundle/Model/LeadModel.php:997-1078 @7.x] |
| `LeadChangeEventDispatcher` | `app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php` | gates `LEAD_POINTS_CHANGE` (:42-62) [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:42-62 @7.x] |

Repositories of note:
- `PointRepository::getPublishedByType`, `getCompletedLeadActions` [code: app/bundles/PointBundle/Entity/PointRepository.php:41-85 @7.x].
- `TriggerEventRepository::getPublishedByPointTotal`, `getPublishedByGroupScore`, `getLeadTriggeredEvents`, `getLeadsForEvent` [code: app/bundles/PointBundle/Entity/TriggerEventRepository.php:11-119 @7.x].
- `GroupContactScoreRepository::compareScore` [code: app/bundles/PointBundle/Entity/GroupContactScoreRepository.php:11-29 @7.x].
- `StageRepository::getStageWeights`, `getStages`, `getStageByName`, `findByIdOrName` [code: app/bundles/StageBundle/Entity/StageRepository.php:28-177 @7.x].

There are no console commands and no `parameters` in either bundle's config [code: app/bundles/PointBundle/Config/config.php:6-137 @7.x].

## 3. Registry: Point Action types (`POINT_ON_BUILD`)

| Key | Label key | Callback | Form type | Fired from | Listener file |
|---|---|---|---|---|---|
| `email.open` | `mautic.email.point.action.open` | `EmailBundle\Helper\PointEventHelper::validateEmail` | `EmailOpenType` | `EmailEvents::EMAIL_ON_OPEN` | `app/bundles/EmailBundle/EventListener/PointSubscriber.php:42-49,86-89` |
| `email.send` | `mautic.email.point.action.send` | `PointEventHelper::validateEmail` | `EmailOpenType` | `EmailEvents::EMAIL_ON_SEND` (`allowUserRequest = true`) | `app/bundles/EmailBundle/EventListener/PointSubscriber.php:51-58,91-107` |
| `form.submit` | `mautic.form.point.action.submit` | `FormBundle\Helper\PointActionHelper::validateFormSubmit` | `PointActionFormSubmitType` | `FormEvents::FORM_ON_SUBMIT` | `app/bundles/FormBundle/EventListener/PointSubscriber.php:31-49` |
| `asset.download` | `mautic.asset.point.action.download` | `AssetBundle\Helper\PointActionHelper::validateAssetDownload` | `PointActionAssetDownloadType` | `AssetEvents::ASSET_ON_LOAD` | `app/bundles/AssetBundle/EventListener/PointSubscriber.php:31-52` |
| `page.hit` | `mautic.page.point.action.pagehit` | `PageBundle\Helper\PointActionHelper::validatePageHit` | `PointActionPageHitType` | `PageEvents::PAGE_ON_HIT` (landing page) | `app/bundles/PageBundle/EventListener/PointSubscriber.php:31-41,55-62` |
| `url.hit` | `mautic.page.point.action.urlhit` | `[$this->pointActionHelper, 'validateUrlHit']` (service) | `PointActionUrlHitType` | `PageEvents::PAGE_ON_HIT` (tracking pixel/JS) | `app/bundles/PageBundle/EventListener/PointSubscriber.php:43-52,63-65` |

[code: app/bundles/EmailBundle/EventListener/PointSubscriber.php:33-107 @7.x] [code: app/bundles/FormBundle/EventListener/PointSubscriber.php:26-49 @7.x] [code: app/bundles/AssetBundle/EventListener/PointSubscriber.php:26-52 @7.x] [code: app/bundles/PageBundle/EventListener/PointSubscriber.php:26-65 @7.x]

`GET /api/points/actions/types` returns this registry [code: app/bundles/PointBundle/Controller/Api/PointApiController.php:56-66 @7.x].

## 4. Registry: Point Trigger event types (`TRIGGER_ON_BUILD`)

| Key | Label key | Mechanism | Form type | Listener / handler | Notes |
|---|---|---|---|---|---|
| `email.send` | `mautic.email.point.trigger.sendemail` | callback `[$this->pointEventHelper, 'sendEmail']` | `EmailSendType` | `app/bundles/EmailBundle/EventListener/PointSubscriber.php:62-72`; `app/bundles/EmailBundle/Helper/PointEventHelper.php:31-53` | sends only if the email is published and the Contact has an email address |
| `email.send_to_user` | `mautic.email.point.trigger.send_email_to_user` | eventName `EmailEvents::ON_SENT_EMAIL_TO_USER` | `EmailToUserType` | `app/bundles/EmailBundle/EventListener/PointSubscriber.php:74-83`; `app/bundles/EmailBundle/EventListener/EmailToUserSubscriber.php:20-35` | sets succeeded or failed |
| `lead.changelists` | `mautic.lead.point.trigger.changelists` | eventName `PointEvents::TRIGGER_ON_LEAD_SEGMENTS_CHANGE` | `ListActionType` | `app/bundles/LeadBundle/EventListener/PointSubscriber.php:39-47,144-159` | never sets success, so it re-runs (behaviour item 35) |
| `lead.changetags` | `mautic.lead.lead.events.changetags` | eventName `PointEvents::TRIGGER_ON_EVENT_EXECUTE` | `ModifyLeadTagsType` | `app/bundles/LeadBundle/EventListener/PointSubscriber.php:49-57,88-97` | success only if tags changed |
| `lead.changestage` | `mautic.lead.lead.events.changestage` | eventName `PointEvents::TRIGGER_ON_EVENT_EXECUTE` | `StageType` (items = user stages) | `app/bundles/LeadBundle/EventListener/PointSubscriber.php:59-77,105-142` | weight rule; fails and retries on refusal |
| `campaign.changecampaign` | `mautic.campaign.point.trigger.changecampaigns` | callback `[CampaignEventHelper::class, 'addRemoveLead']` (method missing) | `CampaignEventAddRemoveLeadType` | `app/bundles/CampaignBundle/EventListener/PointSubscriber.php:22-32` | broken; see Pitfalls |
| `plugin.leadpush` | `mautic.plugin.actions.push_lead` | callback `[PluginBundle\Helper\EventHelper::class, 'pushLead']` | `IntegrationsListType` | `app/bundles/PluginBundle/EventListener/PointSubscriber.php:22-33`; `app/bundles/PluginBundle/Helper/EventHelper.php:17-25` | callback needs services that are not injected; likely TypeError |

[code: app/bundles/EmailBundle/EventListener/PointSubscriber.php:62-83 @7.x] [code: app/bundles/LeadBundle/EventListener/PointSubscriber.php:31-159 @7.x] [code: app/bundles/CampaignBundle/EventListener/PointSubscriber.php:18-31 @7.x] [code: app/bundles/PluginBundle/EventListener/PointSubscriber.php:18-32 @7.x] [code: app/bundles/CampaignBundle/Helper/CampaignEventHelper.php:12 @7.x]

`GET /api/points/triggers/events/types` returns this registry [code: app/bundles/PointBundle/Controller/Api/TriggerApiController.php:127-143 @7.x].

## 5. Events

PointEvents (`app/bundles/PointBundle/PointEvents.php`):

| Constant | Event class | Dispatched | Core listeners |
|---|---|---|---|
| `POINT_PRE/POST_SAVE`, `POINT_PRE/POST_DELETE` | `PointEvent` | `PointModel.php:107-142` | `PointBundle/EventListener/PointSubscriber.php` (audit) |
| `POINT_ON_BUILD` | `PointBuilderEvent` | `PointModel.php:154-155` | Email, Form, Asset, Page `PointSubscriber` |
| `POINT_ON_ACTION` | `PointActionEvent` | `PointModel.php:287-288` | none |
| `TRIGGER_PRE/POST_SAVE`, `TRIGGER_PRE/POST_DELETE` | `TriggerEvent` | `TriggerModel.php:201-235` | `PointSubscriber` (audit) |
| `TRIGGER_ON_BUILD` | `TriggerBuilderEvent` | `TriggerModel.php:279-280` | Campaign, Email, Lead, Plugin `PointSubscriber` |
| `TRIGGER_ON_EVENT_EXECUTE` | `TriggerExecutedEvent` | `TriggerModel.php:350` | `LeadBundle/EventListener/PointSubscriber.php:32` |
| `TRIGGER_ON_LEAD_SEGMENTS_CHANGE` | `TriggerExecutedEvent` | `TriggerModel.php:350` | `LeadBundle/EventListener/PointSubscriber.php:33` |

[code: app/bundles/PointBundle/PointEvents.php:19-127 @7.x]

PointGroupEvents: `GROUP_PRE/POST_SAVE/DELETE` (`GroupEvent`, plain class, no listeners) and `SCORE_CHANGE` (`GroupScoreChangeEvent`). `SCORE_CHANGE` has two listeners: `GroupScoreSubscriber` (triggers) and `PointInsightSubscriber` [code: app/bundles/PointBundle/PointGroupEvents.php:16-52 @7.x] [code: app/bundles/PointBundle/EventListener/GroupScoreSubscriber.php:22 @7.x] [code: app/bundles/PointBundle/EventListener/PointInsightSubscriber.php:22 @7.x].

StageEvents:
- `STAGE_PRE/POST_SAVE/DELETE` (`StageEvent`; audit listener `StageSubscriber`).
- `STAGE_ON_BUILD` (no subscribers).
- `STAGE_ON_ACTION` and `ON_CAMPAIGN_TRIGGER_ACTION` (unused).
- `ON_CAMPAIGN_BATCH_ACTION` (campaign `stage.change`).
[code: app/bundles/StageBundle/StageEvents.php:9-23 @7.x]

Events consumed from other bundles:
- `LEAD_POINTS_CHANGE` and `LEAD_POST_SAVE` (−1) run triggers.
- `TIMELINE_ON_GENERATE` builds the timeline.
- `LEAD_POST_MERGE` merges the logs.
- `LIST_FILTERS_CHOICES_ON_GENERATE` (−10) and `SEGMENT_DICTIONARY_ON_GENERATE` add the group filters.
- `REPORT_ON_BUILD/GENERATE` add the `group.score` report.
- Global search, dashboard widgets and `/api/stats` tables (`StatsSubscriber`).
- Entity import/export for groups.
- `CAMPAIGN_ON_BUILD` and `StageEvents::ON_CAMPAIGN_BATCH_ACTION` handle the stage campaign action.
[code: app/bundles/PointBundle/EventListener/LeadSubscriber.php:31-34 @7.x] [code: app/bundles/PointBundle/EventListener/SegmentFilterSubscriber.php:29-35 @7.x] [code: app/bundles/PointBundle/EventListener/ReportSubscriber.php:56-57 @7.x] [code: app/bundles/StageBundle/EventListener/CampaignSubscriber.php:29-62 @7.x] [code: app/bundles/PointBundle/EventListener/StatsSubscriber.php:18-23 @7.x]

Campaign and form handlers that live in LeadBundle:
- `lead.changepoints` action and the `lead.points` and `lead.stages` conditions [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:107-112,216-313,521-522,692-707 @7.x].
- Form submit action `lead.pointschange` [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:53-54,70-78,164-205 @7.x].

## 6. Routes

UI routes (`/s` prefix):
- `mautic_pointtriggerevent_action` `/points/triggers/events/{objectAction}/{objectId}`.
- `mautic_pointtrigger_index` and `mautic_pointtrigger_action` (`/points/triggers/...`).
- `mautic_point.group_index` and `mautic_point.group_action` (`/points/groups/...`).
- `mautic_point.insight_index` and `mautic_point.insight_action` (`/points/insights/...`).
- `mautic_point_index` and `mautic_point_action` (`/points/...`). These are declared last, so the more specific routes win.
- `mautic_stage_index` and `mautic_stage_action` (`/stages/...`, including `merge`).
[code: app/bundles/PointBundle/Config/config.php:6-44 @7.x] [code: app/bundles/StageBundle/Config/config.php:6-16 @7.x]

API routes:

| Route | Path | Verb | Handler |
|---|---|---|---|
| `mautic_api_pointactionsstandard` | `/api/points` (`points`) | standard | `PointApiController` |
| `mautic_api_getpointactiontypes` | `/api/points/actions/types` | GET | `PointApiController::getPointActionTypesAction` |
| `mautic_api_pointtriggersstandard` | `/api/points/triggers` (`triggers`) | standard | `TriggerApiController` |
| `mautic_api_getpointtriggereventtypes` | `/api/points/triggers/events/types` | GET | `TriggerApiController` |
| `mautic_api_pointtriggerdeleteevents` | `/api/points/triggers/{triggerId}/events/delete` | DELETE | `TriggerApiController::deletePointTriggerEventsAction` |
| `mautic_api_adjustcontactpoints` | `/api/contacts/{leadId}/points/{operator}/{delta}` | POST | `PointApiController::adjustPointsAction` |
| `mautic_api_pointgroupsstandard` | `/api/points/groups` (`pointGroups`) | standard | `PointGroupsApiController` |
| `mautic_api_getcontactpointgroups` | `/api/contacts/{contactId}/points/groups` | GET | `PointGroupsApiController` |
| `mautic_api_getcontactpointgroup` | `/api/contacts/{contactId}/points/groups/{groupId}` | GET | `PointGroupsApiController` |
| `mautic_api_adjustcontactgrouppoints` | `/api/contacts/{contactId}/points/groups/{groupId}/{operator}/{value}` | POST | `PointGroupsApiController::adjustGroupPointsAction` |
| `mautic_api_pointinsightsstandard` | `/api/points/insights` (`insights`) | standard | `PointInsightApiController` |
| `mautic_api_stagesstandard` | `/api/stages` (`stages`) | standard | `StageApiController` |
| `mautic_api_stageddcontact` | `/api/stages/{id}/contact/{contactId}/add` | POST | `StageApiController` (no weight rule) |
| `mautic_api_stageremovecontact` | `/api/stages/{id}/contact/{contactId}/remove` | POST | `StageApiController` |

[code: app/bundles/PointBundle/Config/config.php:45-101 @7.x] [code: app/bundles/StageBundle/Config/config.php:17-34 @7.x] API Platform `#[ApiResource]` attributes also exist on `Point`, `Trigger`, `TriggerEvent` and `Stage` [code: app/bundles/PointBundle/Entity/Point.php:28-36 @7.x].

AJAX routes:
- `reorderTriggerEventsAction` reorders the trigger events held in the session.
- `getActionFormAction` returns the property sub-form for an action type.
[code: app/bundles/PointBundle/Controller/AjaxController.php:25-43 @7.x]

Trigger events are edited in the session under `mautic.point.<id>.triggerevents.modified` and `.deleted` until the trigger is saved [code: app/bundles/PointBundle/Controller/TriggerController.php:197-226 @7.x].

## 7. Permissions

`point` permission bundle:
- Levels `points`, `triggers`, `groups`, `categories` and `insights`, each with the standard view/edit/create/delete/publish/full set.
- Each model's permission base matches its level (`point:points`, `point:triggers`, `point:groups`, `point:insights`).
- The API Platform resources for `Point`, `Trigger` and `TriggerEvent` all check `point:triggers:*`.
[code: app/bundles/PointBundle/Security/Permissions/PointPermissions.php:19-33 @7.x]

`stage` permission bundle:
- Levels `stages` and `categories`.
- Merge needs both edit and delete.
- The API add and remove-contact endpoints need edit on the Contact plus `stage:stages:view`.
[code: app/bundles/StageBundle/Security/Permissions/StagePermissions.php:10-25 @7.x] [code: app/bundles/StageBundle/Controller/StageController.php:428-431 @7.x] [code: app/bundles/StageBundle/Controller/Api/StageApiController.php:59-95 @7.x]

## 8. Forms, views, translations

Form types:
- `PointType`: `repeatable` defaults to No [code: app/bundles/PointBundle/Form/Type/PointType.php:111-150 @7.x].
- `TriggerType`: points, color and trigger_existing_leads [code: app/bundles/PointBundle/Form/Type/TriggerType.php:66-127 @7.x].
- `GroupListType`: `return_entity` defaults to true [code: app/bundles/PointBundle/Form/Type/GroupListType.php:23-49 @7.x].
- `PointInsightType`.
- `StageType` [code: app/bundles/StageBundle/Form/Type/StageType.php:47-56 @7.x].
- `StageListType`: published stages only [code: app/bundles/StageBundle/Form/Type/StageListType.php:44-54 @7.x].
- `StageActionListType`.
- LeadBundle `PointActionType` (campaign) and `CampaignEventPointType` (condition).

Views live in `app/bundles/PointBundle/Resources/views/{Point,Trigger,Group,Insight,Event,FormTheme,SubscribedEvents}` and `app/bundles/StageBundle/Resources/views/Stage/`.

Translations: `app/bundles/PointBundle/Translations/en_US/messages.ini` (help texts at :3, :19, :39) and `app/bundles/StageBundle/Translations/en_US/{messages,validators}.ini` [code: app/bundles/StageBundle/Translations/en_US/validators.ini:3 @7.x].

## 9. Tests

- `app/bundles/PointBundle/Tests/{Unit,Functional,Controller,Entity}`.
- `app/bundles/StageBundle/Tests/{Unit,Functional}`.
- Shared trait: `app/bundles/PointBundle/Tests/Functional/TriggerTrait.php`.
- Representative tests are listed in test-patterns.md.

## 10. Extension points

- Point Action type: `POINT_ON_BUILD` → `addAction()`. Keys must be unique; `callback` is checked with `is_callable($x, true)`, which checks syntax only [code: app/bundles/PointBundle/Event/PointBuilderEvent.php:18-36 @7.x].
- Trigger event type: `TRIGGER_ON_BUILD` → `addEvent()`. One of `callback` or `eventName` is required [code: app/bundles/PointBundle/Event/TriggerBuilderEvent.php:18-42 @7.x].
- Reacting to scoring: `POINT_ON_ACTION`, `SCORE_CHANGE`, `LEAD_POINTS_CHANGE` (also a webhook type) [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:33,69,165 @7.x].
- Moving stages: `LeadModel::changeStage()` enforces the weight rule; `addToStage()` and `removeFromStage()` do not.
- 8.x: subscribe by event class; see version-notes.md.
