# Points and stages - version notes

## 5.x / 6.x
- The analysis inputs record no behaviour differences for points or stages in 5.x or 6.x. Older KB articles (4.x/5.x era) describe stages with a "colour" field and a forward-only rule [kb: https://kb.mautic.org/article/working-with-stages-in-mautic.html]. 7.2.1 has no stage colour column; colour belongs to triggers [code: app/bundles/StageBundle/Entity/Stage.php:60-117 @7.x] [code: app/bundles/PointBundle/Entity/Trigger.php:70 @7.x].
- The docs "now triggers" wording for URL matching implies a recent change to `url.hit` matching. The version is not identified in the inputs [docs: https://docs.mautic.org/en/7.2/points/points_troubleshooting.html#page-visits-not-recognized].

## 7.x
- Point Insights are new in Mautic 7: entity `PointInsight`, table `point_insights` created by migration `Version20260616075543`, `/api/points/insights`, the `point:insights` permission and the menu item "Insights". No feature flag was found [code: app/migrations/Version20260616075543.php:22 @7.x] [code: app/bundles/PointBundle/Security/Permissions/PointPermissions.php:19-33 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/point_insights.html].
- Point, Trigger and Stage carry `ProjectTrait`; Projects are a 7.x feature. The xref tables are `point_projects_xref`, `point_trigger_projects_xref` and `stage_projects_xref` [code: app/bundles/PointBundle/Entity/Point.php:172 @7.x] [code: app/bundles/StageBundle/Entity/Stage.php:109 @7.x].
- Point Groups have entity export and import keyed by UUID [code: app/bundles/PointBundle/EventListener/GroupImportExportSubscriber.php:45-157 @7.x].
- API Platform `#[ApiResource]` attributes exist on `Point`, `Trigger`, `TriggerEvent` and `Stage`, next to the legacy `/api/*` controllers [code: app/bundles/PointBundle/Entity/Point.php:28-36 @7.x] [code: app/bundles/StageBundle/Entity/Stage.php:26-44 @7.x].

## 8.x delta (from 7.x to 8.x @11599729491)
Event dispatch by class. Subscribers must use the class as the key; the string constants still exist but are never dispatched:
- `PointBuilderEvent` is dispatched by class [code: app/bundles/PointBundle/Model/PointModel.php:158 @8.x].
- `TriggerBuilderEvent` is dispatched by class [code: app/bundles/PointBundle/Model/TriggerModel.php:275 @8.x].
- `PointActionEvent` (formerly `POINT_ON_ACTION`) and `GroupScoreChangeEvent` (formerly `SCORE_CHANGE`) are dispatched by class [code: app/bundles/PointBundle/Model/PointGroupModel.php:159 @8.x].
- `StageBuilderEvent` (formerly `STAGE_ON_BUILD`) is dispatched by class.
- The LeadBundle events the PointBundle listens to are now keyed by class: `PointsChangeEvent`, `LeadPostSaveEvent`, `LeadPostMergeEvent` and `LeadTimelineEvent` [code: app/bundles/PointBundle/EventListener/LeadSubscriber.php:29-37 @8.x].
- The constants `POINT_ON_BUILD`, `TRIGGER_ON_BUILD` and `STAGE_ON_BUILD` remain, which makes this a trap: a listener on the string loads but never fires [code: app/bundles/PointBundle/PointEvents.php:45,87 @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/points.html].

Still dispatched by string:
- The CRUD pre/post save and delete events of `PointModel`, `TriggerModel`, `PointGroupModel` and `StageModel` [code: app/bundles/PointBundle/Model/TriggerModel.php:224 @8.x].
- Trigger events registered with `eventName`, such as `TRIGGER_ON_EVENT_EXECUTE` and `TRIGGER_ON_LEAD_SEGMENTS_CHANGE` [code: app/bundles/PointBundle/Model/TriggerModel.php:342 @8.x].
- `LEAD_POINTS_CHANGE` stays as a webhook type id, but listeners must key on `PointsChangeEvent` [code: UPGRADE-8.0.md:130 @8.x]. UPGRADE-8.0.md:728 contradicts this ("unchanged"); the 8.x subscriber code follows line 130 [code: app/bundles/PointBundle/EventListener/LeadSubscriber.php:32 @8.x].

Removed:
- `StageEvents::ON_CAMPAIGN_TRIGGER_ACTION`; use `ON_CAMPAIGN_BATCH_ACTION` with a `PendingEvent` listener [code: app/bundles/StageBundle/StageEvents.php:17-59 @8.x] [PR #17059].
- `StageBundle\Helper\EventHelper` (only `StageSearchScopeProvider` remains in `Helper/`) [code: app/bundles/StageBundle/Helper/StageSearchScopeProvider.php @8.x].
- PluginBundle's `ON_CAMPAIGN_TRIGGER_ACTION`, replaced by `ON_CAMPAIGN_BATCH_ACTION`. This concerns the campaign `plugin.leadpush` action, not the trigger event [code: app/bundles/PluginBundle/PluginEvents.php:36 @8.x].

Typing:
- `Point::getProperties(): array` and `TriggerEvent::getProperties(): array` [code: app/bundles/PointBundle/Entity/Point.php:219 @8.x] [code: app/bundles/PointBundle/Entity/TriggerEvent.php:200 @8.x].
- `TriggerModel::getColorForLeadPoints(int $points)` [code: app/bundles/PointBundle/Model/TriggerModel.php:426 @8.x].
- `PointBuilderEvent` and `TriggerExecutedEvent` are `final` [code: app/bundles/PointBundle/Event/PointBuilderEvent.php:9 @8.x] [code: app/bundles/PointBundle/Event/TriggerExecutedEvent.php:9 @8.x]. Custom code that extended them breaks.
- The point-group score primary-key order is preserved under the attribute mapping driver [PR #17454].

Unchanged:
- `campaign.changecampaign` still registers the missing `CampaignEventHelper::addRemoveLead` [code: app/bundles/CampaignBundle/EventListener/PointSubscriber.php:26 @8.x].
- The user docs for points and stages and the REST pages are identical in 8.0 [docs: https://docs.mautic.org/en/8.0/stages/stages.html] [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/].

Branch topology: the last forward merge into 8.x was 7.2.0 [PR #17253]. 7.2.1-only fixes may be missing from 8.x until the next forward merge.

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
