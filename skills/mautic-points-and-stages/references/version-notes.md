# Points and stages - version notes

## 5.x / 6.x
- 5.0.0 introduced Point Groups: group scores, group-targeted actions and triggers, a campaign condition and action, a segment filter and the "Group points" report [PR #11891].
- 5.0.0 moved Point and Stage templates from PHP to Twig. The migration lost trigger events on clone until 5.2 [PR #11565] [PR #11968] [PR #14177].
- 5.0.0 fixed several crossed thresholds: every trigger now met runs [PR #12867].
- 5.0.0 to 5.2.1 delete a trigger's events from `point_trigger_events` after its first execution; 5.2.2 restores them persisting [PR #12353] [PR #14448].
- 5.0.2 fixed the `GroupContactScore` mapping [PR #13231].
- 5.1.0 added the Point Groups REST API under `/api/points/groups` and `/api/contacts/{id}/points/groups` [PR #13517]. The action type label became "Action taken by contact" [PR #13495] [PR #13658].
- 5.2 stopped adding `GenericPointSettingsType` to custom Point Actions; their top-level delta is awarded [PR #14218].
- 6.0.0 removes the `GenericPointSettingsType` class and `MauticFactory::getEntityManager()` (UPGRADE-6.0.md), and adds `customContent()` hooks to the point, trigger and stage lists [PR #13904] [PR #14611] [PR #14488].
- 6.0.3 no longer errors when a Contact is saved without a points log [PR #14714].
- Older KB articles (4.x/5.x era) describe stages with a "colour" field and a forward-only rule [kb: https://kb.mautic.org/article/working-with-stages-in-mautic.html]. 7.2.1 has no stage colour column; colour belongs to triggers [code: app/bundles/StageBundle/Entity/Stage.php:60-117 @7.x] [code: app/bundles/PointBundle/Entity/Trigger.php:70 @7.x].
- The docs "now triggers" wording for URL matching implies a recent change to `url.hit` matching. The version is not identified in the inputs [docs: https://docs.mautic.org/en/7.2/points/points_troubleshooting.html#page-visits-not-recognized].

## 7.x
- Point Insights are new in Mautic 7: entity `PointInsight`, table `point_insights` created by migration `Version20260616075543`, `/api/points/insights`, the `point:insights` permission and the menu item "Insights". No feature flag was found [code: app/migrations/Version20260616075543.php:22 @7.x] [code: app/bundles/PointBundle/Security/Permissions/PointPermissions.php:19-33 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/point_insights.html].
- Point, Trigger and Stage carry `ProjectTrait`; Projects are a 7.x feature. The xref tables are `point_projects_xref`, `point_trigger_projects_xref` and `stage_projects_xref` [code: app/bundles/PointBundle/Entity/Point.php:172 @7.x] [code: app/bundles/StageBundle/Entity/Stage.php:109 @7.x].
- 7.0.0 adds Projects to Point Actions, triggers and stages, and fixes trigger events that stayed visible after delete and Apply [PR #15409] [PR #15186].
- 7.2.0 adds Point Insights, stage merge, server-side unique stage weights and the trigger event `lead.changestage`; none of these exist in 7.1 [PR #15359] [PR #15399] [PR #15404] [PR #17041].
- Unreleased on 7.x (7.3.0-rc): deleting a trigger or a Point Group warns that it is permanent [PR #17442] [PR #17447]; the 7.3 user docs carry the same warnings [docs: github.com/mautic/user-documentation/blob/7.3/docs/points/points.rst] [docs: github.com/mautic/user-documentation/blob/7.3/docs/points/point_groups.rst].
- Unreleased on 7.x (7.3.0-rc): Stages list Contacts column and **View Contacts** action, the Contacts search command `stage_id:<id>`, and correct Stages list pagination [PR #15403]; Point Actions list search commands `type:gain`, `type:loss`, `is:repeatable` with a "Point change" quick-filter group [PR #18078]; the Point, Trigger and Stage lists group their quick filters and drop the search-command help text [PR #18069].
- Unreleased on 7.x (7.3.0-rc): no IP is stored on points change-log and trigger-log rows caused by an untracked form submitter (kiosk mode, DNT, Global Privacy Control, bot, prefetch), and the `form.submit` point action and the "Adjust contact's points" form action are skipped when the submission has no Contact [PR #17847] [PR #17868].
- Point Groups have entity export and import keyed by UUID [code: app/bundles/PointBundle/EventListener/GroupImportExportSubscriber.php:45-157 @7.x].
- API Platform `#[ApiResource]` attributes exist on `Point`, `Trigger`, `TriggerEvent` and `Stage`, next to the legacy `/api/*` controllers [code: app/bundles/PointBundle/Entity/Point.php:28-36 @7.x] [code: app/bundles/StageBundle/Entity/Stage.php:26-44 @7.x].

## 8.x delta: 8.x (snapshot pinned in SOURCES.md)
Event dispatch by class. Subscribers must use the class as the key; the string constants still exist but are never dispatched:
- `PointBuilderEvent` is dispatched by class [code: app/bundles/PointBundle/Model/PointModel.php:163 @8.x].
- `TriggerBuilderEvent` is dispatched by class [code: app/bundles/PointBundle/Model/TriggerModel.php:276 @8.x].
- `PointActionEvent` (formerly `POINT_ON_ACTION`) and `GroupScoreChangeEvent` (formerly `SCORE_CHANGE`) are dispatched by class [code: app/bundles/PointBundle/Model/PointGroupModel.php:162 @8.x].
- `StageBuilderEvent` (formerly `STAGE_ON_BUILD`) is dispatched by class.
- The LeadBundle events the PointBundle listens to are now keyed by class through `#[AsEventListener]` attributes (`LeadSubscriber` no longer implements `EventSubscriberInterface`): `PointsChangeEvent`, `LeadPostSaveEvent`, `LeadPostMergeEvent` and `LeadTimelineEvent` [PR #17988] [code: app/bundles/PointBundle/EventListener/LeadSubscriber.php:32-35,43-44,57-58,103-104 @8.x].
- The constants `POINT_ON_BUILD`, `TRIGGER_ON_BUILD` and `STAGE_ON_BUILD` remain, which makes this a trap: a listener on the string loads but never fires [code: app/bundles/PointBundle/PointEvents.php:45,87 @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/points.html].

Still dispatched by string:
- The CRUD pre/post save and delete events of `PointModel`, `TriggerModel`, `PointGroupModel` and `StageModel` [code: app/bundles/PointBundle/Model/TriggerModel.php:228 @8.x].
- Trigger events registered with `eventName`, such as `TRIGGER_ON_EVENT_EXECUTE` and `TRIGGER_ON_LEAD_SEGMENTS_CHANGE` [code: app/bundles/PointBundle/Model/TriggerModel.php:343 @8.x].
- `LEAD_POINTS_CHANGE` stays as a webhook type id, but listeners must key on `PointsChangeEvent` [code: UPGRADE-8.0.md:200 @8.x]. UPGRADE-8.0.md:951 contradicts this (lists `LEAD_POINTS_CHANGE` as "unchanged"); the 8.x subscriber code follows line 200 [code: app/bundles/PointBundle/EventListener/LeadSubscriber.php:32-35 @8.x].

Removed:
- `StageEvents::ON_CAMPAIGN_TRIGGER_ACTION`; use `ON_CAMPAIGN_BATCH_ACTION` with a `PendingEvent` listener [code: app/bundles/StageBundle/StageEvents.php:17-59 @8.x] [PR #17059].
- `StageBundle\Helper\EventHelper` (only `StageSearchScopeProvider` remains in `Helper/`) [code: app/bundles/StageBundle/Helper/StageSearchScopeProvider.php @8.x].
- PluginBundle's `ON_CAMPAIGN_TRIGGER_ACTION`, replaced by `ON_CAMPAIGN_BATCH_ACTION`. This concerns the campaign `plugin.leadpush` action, not the trigger event [code: app/bundles/PluginBundle/PluginEvents.php:36 @8.x].

Typing:
- `Point::getProperties(): array` and `TriggerEvent::getProperties(): array` [code: app/bundles/PointBundle/Entity/Point.php:207 @8.x] [code: app/bundles/PointBundle/Entity/TriggerEvent.php:188 @8.x].
- `TriggerModel::getColorForLeadPoints(int $points)` [code: app/bundles/PointBundle/Model/TriggerModel.php:428 @8.x].
- `PointBuilderEvent` and `TriggerExecutedEvent` are `final` [code: app/bundles/PointBundle/Event/PointBuilderEvent.php:9 @8.x] [code: app/bundles/PointBundle/Event/TriggerExecutedEvent.php:9 @8.x]. Custom code that extended them breaks.
- The point-group score primary-key order is preserved under the attribute mapping driver [PR #17454].

Unchanged:
- `campaign.changecampaign` still registers the missing `CampaignEventHelper::addRemoveLead` [code: app/bundles/CampaignBundle/EventListener/PointSubscriber.php:22 @8.x].
- The user docs for points and stages and the REST pages are identical in 8.0 [docs: https://docs.mautic.org/en/8.0/stages/stages.html] [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/].

CSS: `point.css` is cut from 46 to 22 lines (dead trigger-event and colour-column rules); no intended visual change [PR #18291].

Branch topology: 7.2.2 and the 7.x work up to 2026-11-16 are in 8.x through the squash merge [PR #18236]; compare trees, not ancestry. The stage list Contacts column is on 8.x [PR #15403] [code: app/bundles/StageBundle/Model/StageModel.php:227 @8.x]. The Point Actions `type:gain`/`type:loss`/`is:repeatable` search [PR #18078] is not on 8.x yet.

### Porting a 7.x points plugin to 8.x
```diff
 public static function getSubscribedEvents(): array
 {
     return [
-        PointEvents::POINT_ON_BUILD   => ['onPointBuild', 0],
-        PointEvents::TRIGGER_ON_BUILD => ['onTriggerBuild', 0],
+        PointBuilderEvent::class      => ['onPointBuild', 0],
+        TriggerBuilderEvent::class    => ['onTriggerBuild', 0],
         // unchanged: your own trigger 'eventName' string still dispatches by name
     ];
 }
```
