# Campaigns — version notes

## History that explains current behaviour (pre-7.x)
- Rotations were introduced around 2.14: a new membership starts at rotation 2 when rotation-1 logs already exist, for backward compatibility with older data [code: app/bundles/CampaignBundle/Membership/Action/Adder.php:22-41 @7.x]. A 2.14 self-heal rewrites decisions whose `channel_id` is literally `'1'` [code: app/bundles/CampaignBundle/Executioner/RealTimeExecutioner.php:187-197 @7.x].
- Batch actions (`batchEventName` + `PendingEvent`) have worked since Mautic 3; the per-contact `eventName`/`callback` path is legacy [code: app/bundles/CampaignBundle/Executioner/Dispatcher/LegacyEventDispatcher.php:152,181 @7.x].
- 5.1 added copy/paste (clone) of events within and between campaigns [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#cloning-campaign-events].
- Pre-5.0 history (2.x–4.x decisions such as restart, own/other permissions, the 2.14 executioner refactor) is in `references/pr-history.md` [PR #6132] [PR #6963] [PR #5942].

## 5.x
- 5.0: `mautic:segments:update` no longer adds or removes campaign members; only `mautic:campaigns:update` does. The `LeadSubscriber` Segment handlers exist at tag 4.4.13 and are gone at 5.0.0 [PR #10550].
- 5.0: weekday restrictions apply to every delay unit, including no delay [PR #11332]; `--thread-id` threads get separate lock keys [PR #11747]; restartable rebuilds no longer loop after a manual removal [PR #11318].
- 5.0: Redis lock store for moderated commands (`-x redis`) [PR #10347]; campaign views are Twig [PR #11778].
- 5.1: event logs are deleted by explicit queries, optionally in the background (`delete_campaign_event_log_in_background`) [PR #10219].
- 5.1: failure auto-unpublish arrived: every failure bumped `failed_count` and a campaign unpublished at `failed_count / members >= 0.1` [PR #13402].
- 5.1: campaign edits use optimistic locking [PR #13659]; the trigger runs newest campaigns first [PR #12922]; `--exclude` on trigger, rebuild and segments update [PR #13383]; "Schedule at" with a delay behaves like "between the hours of" [PR #13263].
- 5.2: optimized scheduling [PR #13569]; "Change campaigns" restarting "this" campaign needs a delay of at least 30 minutes [PR #13963]; new Send email events default to Marketing [PR #14145].
- 5.2: scheduled logs outside the publish-up/down range stay scheduled instead of failing [PR #13995]; real-time decisions respect publish dates [PR #14303]; red-path actions run as soon as the decision's wait expires [PR #14289].

## 6.x
- 6.0: a Contact/event pair counts toward auto-unpublish only after 100 failures, once per pair, and is decremented after a later success; the threshold became 35 % (tag 6.0.0 has no member minimum) [PR #14470].
- 6.0: weekday numbering is 0–6 with Sunday = 0 [PR #14612]; Email Metrics tab with `campaign_email_stats_enabled` [PR #14414]; timeline shows the parent decision or condition and its path [PR #14601].
- 6.0: `MauticFactory` removed [PR #14682]; Symfony 6.4 [PR #13962]. 6.0.4: writes use `executeStatement` so they never reach the read replica [PR #15199].

## 7.x
- Campaign import/export (UI, CLI `mautic:entity:export/import`, API) exists only from 7.0 [docs: https://docs.mautic.org/en/7.2/campaigns/exporting_campaigns.html].
- 7.0: auto-unpublish requires at least 100 members and sends one notification and one email [PR #14906]; event logs carry an optimistic-lock `version` so concurrent triggers run each once [PR #15348].
- 7.0: orphan events block saving [PR #15321]; builder state lives in the page, not the session [PR #15476]; `campaign_events.channel_id` is VARCHAR(64) [PR #15132]; the trigger exits cleanly on SIGTERM [PR #14745].
- 7.1: deleting an event soft-deletes it with an optional redirect [PR #15528]; per-campaign republish behaviour [PR #15634]; `GET /api/campaigns?withContactCounts` [PR #15878].
- 7.1.3: restart-off campaigns never auto re-add exited Contacts, and restart-on campaigns re-add Contacts who re-join the Segment [PR #16183] [PR #16184]; future-dated scheduled logs no longer loop [PR #16066].
- 7.2.0: `mautic:campaigns:resume-stuck` (with `--dry-run`) re-evaluates half-run conditions; decisions and conditions advance the log version [PR #15310] [PR #17104]. Many campaign classes became `final` [PR #16735] [PR #16753] [PR #16755] [PR #16896].
- 7.2.1: the scheduled phase fetches only logs at the initial version [PR #17146]; send hour resets in the Contact's timezone when a weekday rule moves the day [PR #17283].
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
