# Campaigns — version notes

## History that explains current behaviour (pre-7.x)
- Rotations were introduced around 2.14: a new membership starts at rotation 2 when rotation-1 logs already exist, for backward compatibility with older data [code: app/bundles/CampaignBundle/Membership/Action/Adder.php:22-41 @7.x]. A 2.14 self-heal rewrites decisions whose `channel_id` is literally `'1'` [code: app/bundles/CampaignBundle/Executioner/RealTimeExecutioner.php:187-197 @7.x].
- Batch actions (`batchEventName` + `PendingEvent`) have worked since Mautic 3; the per-contact `eventName`/`callback` path is legacy [code: app/bundles/CampaignBundle/Executioner/Dispatcher/LegacyEventDispatcher.php:152,181 @7.x].
- 5.1 added copy/paste (clone) of events within and between campaigns [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#cloning-campaign-events].
- No 5.x/6.x-specific behaviour differences for campaign execution were found in the inputs beyond the items above; treat other differences as unverified.

## 7.x
- Campaign import/export (UI, CLI `mautic:entity:export/import`, API) exists only from 7.0 [docs: https://docs.mautic.org/en/7.2/campaigns/exporting_campaigns.html].
- 7.1: Form "type" (`standalone`/`campaign`) became unused; every Form can be a campaign source [PR #17082].
- 7.2: the `mautic.campaign.event_collector` service alias is deprecated [code: app/bundles/CampaignBundle/Config/services.php:69-70 @7.x].
- 7.2.x: `mautic:campaigns:resume-stuck` considers only members added after `campaigns_resume_stuck_records_after` (default `2025-10-01 00:00:00`) [code: app/bundles/CampaignBundle/Config/config.php:174 @7.x].
- 7.x deprecations still present: `Campaign::getOnclickMethod/getDataAttributes/getTranslationKeysDataAttributes`, `CampaignRepository::fetchEmailIdsById()`, legacy `eventName`/`callback` actions, `ON_EVENT_EXECUTION`, `ON_EVENT_DECISION_TRIGGER`, the `lists` API property (to become `segments`), `--force` on moderated commands [code: app/bundles/CampaignBundle/Entity/Campaign.php:247,698-732 @7.x].

## 8.x delta (branch 8.x, not yet released)
Branch note: 7.2.1 work is not yet merged forward into 8.x, so a two-dot diff misreports 7.x-only features (7.2.1 and unreleased later work) as removed.
- Event dispatch by class: 21 `CampaignEvents` constants removed; only `ON_EVENT_DECISION_EVALUATION`, `ON_EVENT_CONDITION_EVALUATION`, `ON_EVENT_JUMP_TO_EVENT`, `ON_CAMPAIGN_ACTION_CHANGE_MEMBERSHIP` remain [PR #17161] [PR #17225].
  - `CAMPAIGN_ON_BUILD` → `CampaignBuilderEvent::class` (referencing the constant fails with "Undefined constant") [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/campaigns.html#registering-campaign-events].
  - `CAMPAIGN_ON_LEADCHANGE` → `CampaignSingleLeadChangeEvent`; `LEAD_CAMPAIGN_BATCH_CHANGE` → `CampaignBatchLeadChangeEvent`; `CampaignLeadChangeEvent` is abstract [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/campaigns.html#campaign-membership-change-events].
  - `CAMPAIGN_PRE_SAVE/POST_SAVE/PRE_DELETE/POST_DELETE` → `CampaignPreSaveEvent`, `CampaignPostSaveEvent`, `CampaignPreDeleteEvent`, `CampaignPostDeleteEvent` (final, extend `CampaignEvent`); raw string keys like `mautic.campaign_post_save` silently receive nothing; post-delete reads `$campaign->deletedId` [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/campaigns.html#campaign-save-and-delete-events].
  - `ON_AFTER_EVENTS_DELETE` → `AfterEventsDeleteEvent`; `ON_CAMPAIGN_DELETE` → `DeleteCampaign`; executed/failed/scheduled/notify events → their classes; `ON_EVENT_EXECUTION` and `ON_EVENT_DECISION_TRIGGER` have no replacement [PR #17161].
- Legacy action path removed: `LegacyEventDispatcher`, `EventArrayTrait`, `CampaignDecisionEvent`, `CampaignScheduledEvent` (folded into `ScheduledEvent`) and all `*Events::ON_CAMPAIGN_TRIGGER_ACTION` constants deleted; `eventName`/`callback` actions no longer execute at all [PR #17097] [PR #17039] [PR #17059].
- Core actions moved to new `ON_CAMPAIGN_BATCH_ACTION` constants in DynamicContent (`dwc.push_content`), Page (`tracking.pixel.send`), Plugin (`plugin.leadpush`), Webhook (`campaign.sendwebhook`), Focus (`focus.show`), Social [PR #17691] [PR #17085].
- `associatedActions`/`associatedDecisions`/`anchorRestrictions` are ignored; use `connectionRestrictions` [PR #17032].
- `ConditionEvent`/`DecisionEvent::getResult()/setResult()` removed; use `pass()/fail()` and `setAsApplicable()`; dev docs add `wasConditionSatisfied()` / `wasDecisionApplicable()` [PR #17151] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/campaigns.html#evaluating-a-campaign-condition].
- Removed: `EventScheduler::reschedule()` (use `rescheduleLogs()`), `CampaignRepository::fetchEmailIdsById()`, `getCampaignLeadCount()`, the deprecated `Campaign` UI helpers; `LeadBundle\Helper\CampaignEventHelper` deleted [PR #17182].
- Typed signatures: `CampaignExecutionEvent`, `AbstractEventAccessor`, `Event::getProperties()`, `LeadEventLog::getMetadata()` return `array`; `CampaignModel::getLeadSources(Campaign|int|string)`, `getCampaignsByForm(Form|int)`, `getCampaignIdsWithDependenciesOnSegment(int)`; `DTO\PublishState::getPublished(): ?bool` [code: UPGRADE-8.0.md @8.x].
- Route `mautic_campaign_import_index` removed as dead [PR #17231].
- Dev docs 8.0 drop the `mautic.campaign.executioner.realtime` service id; inject `RealTimeExecutioner` by class [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/campaigns.html#evaluating-a-campaign-decision].
- `--lock_mode=file_lock` fails on 8.x ("Unknown locking method specified."); use `flock` [code: UPGRADE-8.0.md:267 @8.x].
- User docs for campaigns are identical between 7.2 and 8.0 [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html].

## Writing plugin code for both 7.x and 8.x
```php
public static function getSubscribedEvents(): array
{
    $events = [CampaignBuilderEvent::class => ['onBuild', 0]];
    if (defined(CampaignEvents::class.'::CAMPAIGN_ON_BUILD')) { // 7.x dispatches by string
        $events[CampaignEvents::CAMPAIGN_ON_BUILD] = ['onBuild', 0];
    }
    return $events;
}
```
For 8.x-only classes (`CampaignPostSaveEvent`), guard with `class_exists()` and type-hint `CampaignEvent`. Register actions with `batchEventName` only [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/campaigns.html#registering-campaign-events].
