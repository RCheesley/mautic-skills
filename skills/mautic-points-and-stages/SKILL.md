---
name: mautic-points-and-stages
description: "Mautic lead scoring and lifecycle stages: Point Actions (repeatable vs once), Point Groups and group scores, Point Triggers and trigger events, 'Trigger for existing applicable contacts', Point Insights, the campaign 'Adjust contact points' action and points/stages conditions, the form points action, Stages, stage weights and the forward-only stage rule, timeline entries and segment filters, and the points and stages REST API. Use whenever a task mentions points, lead scoring, scoring decay, point actions, point triggers, point groups, group score, point insights, MQL threshold, stages, lifecycle stage, stage weight, 'change contact's stage', contact colour, lead_points_change_log, lead_stages_change_log, /api/points, /api/stages, PointModel, TriggerModel, PointGroupModel, StageModel, LeadModel::changeStage, PointBuilderEvent, adding a custom point action from a plugin, or touches app/bundles/PointBundle/ or app/bundles/StageBundle/."
---
# Mautic points and stages

## Scope
Points are Mautic's lead-scoring system: a Contact (a person record, `Lead` in code) carries one integer score (`leads.points`) plus optional per-Point-Group scores, changed by Point Actions, campaigns, forms and the API; Point Triggers run one-off events when a score reaches a threshold [code: app/bundles/PointBundle/Model/PointModel.php:173-310 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html]. Stages are ordered lifecycle phases with a unique integer weight; a Contact holds at most one Stage [code: app/bundles/StageBundle/Entity/Stage.php:112-117 @7.x] [docs: https://docs.mautic.org/en/7.2/stages/stages.html]. Out of scope: segment filter mechanics (mautic-segments), campaign execution (mautic-campaigns), the contact entity and merge as a whole (mautic-contacts), page/URL hit tracking (mautic-pages-and-tracking).

## Expected behaviour (essentials)
**Point Actions**
- Core registers exactly six Point Action types: `email.open`, `email.send`, `form.submit`, `asset.download`, `page.hit`, `url.hit`; an action whose type is no longer registered is skipped [code: app/bundles/PointBundle/Model/PointModel.php:221-223 @7.x] [code: app/bundles/EmailBundle/EventListener/PointSubscriber.php:40-59 @7.x].
- Point Actions are evaluated synchronously inside the request or process that produced the email open, form submit, hit or download; there is no cron and no `mautic:points:*` command [code: app/bundles/PageBundle/EventListener/PointSubscriber.php:55-64 @7.x].
- Activity by a logged-in Mautic user never awards Point Action points, except `email.send` [code: app/bundles/PointBundle/Model/PointModel.php:176-178 @7.x]. Test logged out.
- Only published actions inside their publish-up/down window count [code: app/bundles/PointBundle/Entity/PointRepository.php:41-54 @7.x].
- A non-repeatable action (the default) fires once per Contact, ever; this is recorded in `point_lead_action_log`. A repeatable action fires on every qualifying event and is never logged there [code: app/bundles/PointBundle/Model/PointModel.php:211-219,290-297 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html#point-actions].
- An empty email/form/asset/page selection on an action means "any" [code: app/bundles/EmailBundle/Helper/PointEventHelper.php:15-29 @7.x]. `page.hit` matches the parent (translation/variant parent) page id [code: app/bundles/PageBundle/Helper/PointActionHelper.php:17-36 @7.x].
- `delta` is a signed integer in the int32 range; negative subtracts; zero awards nothing but still uses up a non-repeatable action [code: app/bundles/PointBundle/Entity/Point.php:175-184 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:810-812 @7.x].
- An action assigned to a Point Group changes only that group score and never `leads.points` [code: app/bundles/PointBundle/Model/PointModel.php:266-274 @7.x].
- Main points are written as SQL increments (`points = points + n`) on contact save, so concurrent awards do not overwrite each other; `Lead::setPoints()` sets an absolute value instead [code: app/bundles/LeadBundle/Entity/LeadRepository.php:1370-1435 @7.x].

**Point Triggers**
- Triggers are evaluated synchronously when main points change, when a new Contact is saved (so 0-point triggers fire on creation), and when any group score changes [code: app/bundles/PointBundle/EventListener/LeadSubscriber.php:41-54 @7.x] [code: app/bundles/PointBundle/EventListener/GroupScoreSubscriber.php:26-29 @7.x].
- The points-change evaluation is skipped for imported Contacts, for new Contacts, and when both the old and new totals are less than or equal to 0 [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:42-62 @7.x].
- A trigger fires when score ≥ threshold. An ungrouped trigger looks only at `leads.points`; a grouped trigger looks only at that group's score [code: app/bundles/PointBundle/Entity/TriggerEventRepository.php:11-61 @7.x].
- Each trigger event runs at most once per Contact (recorded in `point_lead_event_log`). It is never re-armed when the score drops and rises again, and dropping below the threshold undoes nothing [code: app/bundles/PointBundle/Model/TriggerModel.php:398-421 @7.x].
- An event result of false or null writes no log, so the event retries on the next evaluation. "Modify contact's segments" never reports success, so it re-runs every time [code: app/bundles/LeadBundle/EventListener/PointSubscriber.php:144-159 @7.x].
- "Trigger for existing applicable contacts upon saving" runs inline in the save request, unbatched, for published triggers only. It targets Contacts added on or before the trigger's creation date whose score is ≥ the threshold [code: app/bundles/PointBundle/Model/TriggerModel.php:106-187 @7.x].
- An empty threshold is 0, which means every Contact qualifies, including each new Contact [code: app/bundles/PointBundle/Form/Type/TriggerType.php:66-77 @7.x].
- One points change that crosses several thresholds runs every trigger now met, in threshold order, so the highest threshold's tag change is the one that stands [PR #12867] (v5.0).
- The trigger "Contact color" is stored but never shown in 7.2.1: `LeadRepository::setTriggerModel()` has no caller [code: app/bundles/LeadBundle/Entity/LeadRepository.php:95 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html#point-triggers].

**Groups, insights, campaigns, API**
- A group score row is created lazily at 0, changed with plus/minus/times/divide/set, flushed immediately, and then fires `SCORE_CHANGE` [code: app/bundles/PointBundle/Model/PointGroupModel.php:100-130 @7.x]. A group change does not fire the "Contact Points Changed" webhook [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#webhooks].
- Point Insights run on every group score change. They write `"<id> (<name>)"` of the highest-scoring compared group into a text field. They skip when every score is 0, break a tie by lower id, and keep an existing value on a tie [code: app/bundles/PointBundle/Model/InsightModel.php:67-139 @7.x].
- The campaign action "Adjust contact points" adds or subtracts only (never sets) and rejects 0 [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:273-313 @7.x]. The REST endpoint `/api/contacts/{id}/points/{op}/{delta}` accepts plus/minus/times/divide; `set` is accepted only for group scores [code: app/bundles/PointBundle/Controller/Api/PointApiController.php:68-93 @7.x].
- The campaign condition on a group score fails for a Contact with no row in that group, even for `= 0` or `< n` [code: app/bundles/PointBundle/Entity/GroupContactScoreRepository.php:11-29 @7.x]. The segment filter `group_points_<id>` treats a missing row as 0 [code: app/bundles/PointBundle/EventListener/SegmentFilterSubscriber.php:63-80 @7.x].

**Stages**
- Stage weights are unique. A duplicate is a validation error: HTTP 400 in the API [code: app/bundles/StageBundle/Entity/Stage.php:116 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stages.html#create-stage].
- `LeadModel::changeStage()` refuses a move to a lower weight and refuses the current stage; a move from no stage is always allowed [code: app/bundles/LeadBundle/Model/LeadModel.php:1009-1020 @7.x].
- Only the campaign action "Change contact's stage" and the trigger event "Change contact's stage" enforce the weight rule. The API add endpoint, the contact batch action, contact edit, import and "Update contact" bypass it [code: app/bundles/StageBundle/Controller/Api/StageApiController.php:69-74 @7.x] [code: app/bundles/LeadBundle/Controller/LeadController.php:1820-1870 @7.x].
- Every stage change or removal through LeadModel writes a `lead_stages_change_log` row, which feeds the "Stage changed" timeline entry. A stage merge moves Contacts without writing log rows [code: app/bundles/StageBundle/Model/StageModel.php:151-179 @7.x].
- Deleting a stage sets `leads.stage_id` to NULL for its Contacts. Deleting a Point Group deletes its actions, triggers and score rows [code: app/bundles/LeadBundle/Entity/Lead.php:416-421 @7.x] [code: app/bundles/PointBundle/Entity/Point.php:167-169 @7.x].

## Where it lives
| Concern | Path(s) |
|---|---|
| Point entities/tables | `app/bundles/PointBundle/Entity/` - `points`, `point_lead_action_log`, `point_triggers`, `point_trigger_events`, `point_lead_event_log`, `point_groups`, `point_group_contact_score`, `point_insights` |
| Stage entities/tables | `app/bundles/StageBundle/Entity/` - `stages`, `stage_lead_action_log` (vestigial) |
| Change logs (timeline) | `app/bundles/LeadBundle/Entity/PointsChangeLog.php` (`lead_points_change_log`), `StagesChangeLog.php` (`lead_stages_change_log`) |
| Models | `PointBundle/Model/{PointModel,TriggerModel,TriggerEventModel,PointGroupModel,InsightModel}.php`, `StageBundle/Model/StageModel.php`, `LeadModel::changeStage/addToStage/removeFromStage` |
| Events | `PointBundle/PointEvents.php`, `PointGroupEvents.php`, `StageBundle/StageEvents.php` |
| Action/trigger registries | `{Email,Form,Asset,Page}Bundle/EventListener/PointSubscriber.php` (actions); `{Email,Lead,Campaign,Plugin}Bundle/EventListener/PointSubscriber.php` (trigger events) - see references/code-map.md |
| Campaign/form integration | `LeadBundle/EventListener/CampaignSubscriber.php` (adjust points, points/stages conditions), `StageBundle/EventListener/CampaignSubscriber.php` (`stage.change`), `LeadBundle/EventListener/FormSubscriber.php` (`lead.pointschange`) |
| Routes/API | `PointBundle/Config/config.php` (`/s/points/*`, `/api/points*`, `/api/contacts/{id}/points/*`), `StageBundle/Config/config.php` (`/s/stages/*`, `/api/stages*`) |
| Commands / config params | none / none |
| Permissions | `point:{points,triggers,groups,categories,insights}:*`, `stage:{stages,categories}:*` |
| Tests | `app/bundles/PointBundle/Tests/`, `app/bundles/StageBundle/Tests/` |

## How to change or extend it
- Add a Point Action type: in 7.x subscribe to `PointEvents::POINT_ON_BUILD`, call `PointBuilderEvent::addAction($key, [...])` with a `callback` that returns truthy to award points, and call `PointModel::triggerAction($key, $details, null, $lead)` from your own event [code: app/bundles/PointBundle/Event/PointBuilderEvent.php:18-36 @7.x]. In 8.x subscribe to `PointBuilderEvent::class` instead [code: app/bundles/PointBundle/Model/PointModel.php:158 @8.x].
- Add a trigger event: in 7.x subscribe to `PointEvents::TRIGGER_ON_BUILD`, call `TriggerBuilderEvent::addEvent()` with either `callback` or `eventName` [code: app/bundles/PointBundle/Event/TriggerBuilderEvent.php:18-42 @7.x]. With `eventName`, your listener must call `setSucceded()` or `setFailed()`; otherwise the event re-runs on every evaluation (item 35 in references/behaviour.md). In 8.x subscribe to `TriggerBuilderEvent::class` [code: app/bundles/PointBundle/Model/TriggerModel.php:275 @8.x].
- Callbacks are invoked by reflection with arguments matched by parameter name. Point Action callbacks receive only `action`, `lead` and `eventDetails`; trigger callbacks receive only `event`, `lead` and `config`; any other parameter gets `null` [code: app/bundles/PointBundle/Model/PointModel.php:226-263 @7.x] [code: app/bundles/PointBundle/Model/TriggerModel.php:355-382 @7.x]. Use a service callback to get dependencies.
- Change main points with `Lead::adjustPoints()` + `addPointsChangeLogEntry()` + `LeadModel::saveEntity()`. Change group scores with `PointGroupModel::adjustPoints()`. Set `$lead->imported = true` to suppress triggers [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:42-62 @7.x].
- Move Contacts between stages with `LeadModel::changeStage()` when the weight rule must apply, and with `addToStage()`/`removeFromStage()` when it must not [code: app/bundles/LeadBundle/Model/LeadModel.php:997-1078 @7.x].
- A new column on `Point`, `Trigger`, `Stage` or a group/insight entity needs all of these together: a migration in `app/migrations/`, the `loadApiMetadata` serializer group, the form type, `en_US` translations and the user docs [code: app/bundles/PointBundle/Entity/Point.php:189-213 @7.x] [code: app/migrations/Version20260616075543.php:22 @7.x].
- Keep the observable contract: once-per-contact logs, the forward-only stage rule, delta-based API semantics and the timeline `type`/`event_name`/`action_name` formats. Reports, the timeline and the webhook payloads consume these.

## How to test it
- Functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase` and call `logoutUser()` before driving Point Actions; otherwise no points are awarded [code: app/bundles/PointBundle/Tests/Functional/PointActionFunctionalTest.php:18-37 @7.x].
- Build triggers with `PointBundle/Tests/Functional/TriggerTrait.php` (`createTrigger`, `createAddTagEvent`).
- Copy from: `PointBundle/Tests/Functional/PointActionFunctionalTest.php`, `PointTriggerFunctionalTest.php`, `PointInsightsFunctionalTest.php`, `StageBundle/Tests/Unit/EventListener/CampaignSubscriberTest.php`, `LeadBundle/Tests/EventListener/CampaignSubscriberFunctionalTest.php:217-345`, `StageBundle/Tests/Functional/Controller/StageControllerFunctionalTest.php`.
- A good regression test asserts the observable result: `leads.points` or `point_group_contact_score.score`, the `lead_points_change_log` row (type, delta, group), the once-per-contact log row, and that a second event does or does not award again. Re-read the Contact from the database because points are applied with SQL. See references/test-patterns.md.

## Version notes
- 7.x adds Point Insights (table `point_insights`, `/api/points/insights`, the `point:insights` permission) [code: app/migrations/Version20260616075543.php:22 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/point_insights.html].
- 8.x dispatches `PointBuilderEvent`, `TriggerBuilderEvent`, `PointActionEvent`, `GroupScoreChangeEvent`, `StageBuilderEvent` and `PointsChangeEvent` by class name. Subscribers keyed on the old string constants load without error but never fire [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/points.html]. Trigger-event `eventName` dispatch and the CRUD pre/post events still use strings [code: app/bundles/PointBundle/Model/TriggerModel.php:224,342 @8.x].
- 8.x removes `StageEvents::ON_CAMPAIGN_TRIGGER_ACTION` and `StageBundle\Helper\EventHelper` [code: app/bundles/StageBundle/StageEvents.php:17-59 @8.x].
- 5.0 introduced Point Groups and moved Point and Stage templates to Twig [PR #11891] [PR #11565] (v5.0.0). 5.1 added the Point Groups REST API [PR #13517] (v5.1.0).
- 5.0.0 to 5.2.1 delete trigger events after their first execution; 5.2.2 fixes it [PR #12353] [PR #14448].
- Before 5.2 a cloned Point Trigger lost its events [PR #14177] (v5.2).
- 6.0 removes `GenericPointSettingsType` and `MauticFactory::getEntityManager()`; custom point code that used either breaks [PR #13904] [PR #14611] (v6.0).
- 7.2 adds stage merge, server-side unique stage weights and the trigger event "Change contact's stage"; none exist in 6.x or 7.0-7.1 [PR #15399] [PR #15404] [PR #17041] (v7.2.0).
- The user docs for points and stages are identical in 7.2 and 8.0 [docs: https://docs.mautic.org/en/8.0/points/points.html]. Details are in references/version-notes.md.

## Pitfalls
- Testing while logged in: form submits, page hits, asset downloads and email opens award nothing. The docs say "Administrators", but the code skips every logged-in user [code: app/bundles/PointBundle/Model/PointModel.php:176-178 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points_troubleshooting.html#page-visits-not-recognized].
- "Page visits count once" in the troubleshooting docs applies only to non-repeatable actions; repeatable actions fire on every hit [code: app/bundles/PointBundle/Model/PointModel.php:290-297 @7.x].
- Imports never fire triggers, and import sets points only for new Contacts [code: app/bundles/LeadBundle/Model/LeadModel.php:1420-1422 @7.x].
- A score decrease does not untag, un-stage or remove a Contact from a segment, and a trigger never fires twice for the same Contact [code: app/bundles/PointBundle/Model/TriggerModel.php:398-421 @7.x].
- The stage forward-only rule is not universal. The KB and docs say Contacts "cannot move backwards", but the API, batch, import and edit paths can move them back [code: app/bundles/StageBundle/Controller/Api/StageApiController.php:69-74 @7.x] [kb: https://kb.mautic.org/article/working-with-stages-in-mautic.html].
- The trigger event "Change contact's stage" to the current stage or a lower weight is marked failed and is retried on every later evaluation, not "nothing changes" once [code: app/bundles/LeadBundle/EventListener/PointSubscriber.php:112-128 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html#contact-triggers].
- The trigger events "Modify contact's campaigns" (`campaign.changecampaign`, missing callback `CampaignEventHelper::addRemoveLead`) and "Push contact to integration" (`plugin.leadpush`, callback signature not injectable) look broken in 7.2.1 and 8.x; not verified at runtime [code: app/bundles/CampaignBundle/EventListener/PointSubscriber.php:27 @7.x] [code: app/bundles/PluginBundle/Helper/EventHelper.php:17-25 @7.x].
- Group `divide` produces a float passed to `setScore(int)` under `strict_types`; expect a TypeError unless the result is exact (unverified) [code: app/bundles/PointBundle/Model/PointGroupModel.php:114-122 @7.x].
- The form submit action "Adjust contact's points" with a group logs `delta = new main points − old main points`, which is 0, and sets no group on the log row (inferred) [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:164-205 @7.x].
- "Trigger for existing contacts" on a large database can time out the save request [code: app/bundles/PointBundle/Model/TriggerModel.php:106-187 @7.x].
- The API Platform resource for `Point` checks `point:triggers:*` permissions, not `point:points:*` [code: app/bundles/PointBundle/Entity/Point.php:28-36 @7.x].
- Trigger events must survive execution. From 5.0.0 to 5.2.1 executing a trigger deleted its rows in `point_trigger_events`, so triggers emptied after first use; assert the event count after a trigger fires [PR #12353] [PR #14448] (v5.2.2).
- A repeatable `email.send` action must award once per send. `EMAIL_ON_SEND` was once dispatched twice per send and double-awarded [PR #8619] (v3.0.2).
- A plugin Point Action without its own properties form awards the action's top-level delta; since 5.2 Mautic adds no second "Change points" field to it [PR #14218] (v5.2).
- Import with a stage column creates a missing stage by name, with weight 0, rather than failing; this is deliberate [PR #2076] (v2.1.1) [code: app/bundles/LeadBundle/Model/LeadModel.php:1440-1450 @7.x].
- Open question: the KB lead-scoring guide recommends campaigns that "reset scores to 0" and "cap at 70", but the campaign "Adjust contact points" action is delta-only and rejects 0. How the guide's reset is meant to be built is unverified [kb: https://kb.mautic.org/article/lead-scoring-best-practices-with-mautic.html] [code: app/bundles/LeadBundle/Form/Type/PointActionType.php:17-30 @7.x].
- Open question: the devdocs show a trigger callback `($config, $lead, MauticFactory $factory)`. Only `event`, `lead` and `config` are injected, so `$factory` is null [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/points.html#point-triggers] [code: app/bundles/PointBundle/Model/TriggerModel.php:357-381 @7.x].

## Related skills
- mautic-contacts - the Lead entity, contact merge, import, the webhook on points change, contact timeline framework.
- mautic-segments - the `points`, `stage` and `group_points_<id>` filters in the segment query builder.
- mautic-campaigns - how "Adjust contact points", "Change contact's stage" and the points/stage conditions execute.
- mautic-emails - `email.open`/`email.send` actions and the "Send an email"/"Send email to user" trigger events.
- mautic-forms - the `form.submit` action and the "Adjust contact's points" submit action.
- mautic-pages-and-tracking - `page.hit`/`url.hit` matching, dwell time, the tracking pixel and contact identification.
- mautic-assets-categories-projects - `asset.download`, categories and projects on points/triggers/stages.
- mautic-rest-api - authentication, envelopes and the generic `standard_entity` API behaviour.
- mautic-plugin-development - registering subscribers and services for custom actions and trigger events.
- mautic-testing - MauticMysqlTestCase, fixtures and running the suite.
- mautic-upgrades-and-versions - the general 8.x event-by-class migration.

## Reference files
- references/behaviour.md - full numbered behaviour specification with citations; open it before asserting edge cases.
- references/code-map.md - entities and tables, models, events, routes, permissions, and the full registries of Point Action types and trigger events with their listener files.
- references/docs-digest.md - what docs.mautic.org, devdocs and the KB say, with URLs, UI procedures and terminology.
- references/test-patterns.md - base classes, the trigger trait, representative tests and test skeletons.
- references/version-notes.md - 5.x/6.x history, 7.x additions and the 8.x delta for points and stages.
- references/pr-history.md - why and when points and stages behaviour changed: decisions, a regression catalogue, a feature timeline and removals from 78 merged PRs.
