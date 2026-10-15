# Points and stages - behaviour specification (Mautic 7.x)

Authoritative for 7.x (commit 419a08a9b35: release 7.2.1 plus unreleased merged PRs). Numbers are stable: other files refer to "item N". Citations use full repository paths.

## Contents
- A. Point Actions - when points are awarded (1-15)
- B. Point Groups and group scores (16-21)
- C. API point adjustments (22-23)
- D. Campaign and form integration (24-26, 59-60)
- E. Point Triggers - when they fire (27-40)
- F. Contact timeline, merge, deletion (41-44)
- G. Point Insights (45-46)
- H. Stages (47-58)
- I. Imports and webhooks (61-63)

Terms: **Contact** = a person record (`Lead` in code). **Point Action** = a rule that awards a signed `delta` when the Contact does something. **Point Trigger** = a threshold that runs a list of **trigger events** once per Contact. **Point Group** = a separate named score. **Point Insight** = a rule that writes the winning group into a custom field. **Stage** = a lifecycle phase with a unique integer **weight**.

## A. Point Actions - when points are awarded

1. A Point Action fires only for a type registered through the point-action builder event. Core registers `email.open`, `email.send`, `form.submit`, `asset.download`, `page.hit` and `url.hit`. No plugin under `plugins/` registers one. An action whose type is no longer registered is skipped at run time. [code: app/bundles/EmailBundle/EventListener/PointSubscriber.php:40-59 @7.x] [code: app/bundles/FormBundle/EventListener/PointSubscriber.php:31-42 @7.x] [code: app/bundles/AssetBundle/EventListener/PointSubscriber.php:31-42 @7.x] [code: app/bundles/PageBundle/EventListener/PointSubscriber.php:31-53 @7.x] [code: app/bundles/PointBundle/Model/PointModel.php:221-223 @7.x]
2. Point Actions are evaluated synchronously by the event that produced them:
   - `EMAIL_ON_OPEN` → `email.open`.
   - `EMAIL_ON_SEND` → `email.send`, with `allowUserRequest = true`.
   - `FORM_ON_SUBMIT` → `form.submit`.
   - `ASSET_ON_LOAD` → `asset.download`.
   - `PAGE_ON_HIT` → `page.hit` for a Mautic landing page; otherwise `url.hit` (tracking pixel or JS).
   There is no cron. [code: app/bundles/EmailBundle/EventListener/PointSubscriber.php:86-106 @7.x] [code: app/bundles/FormBundle/EventListener/PointSubscriber.php:44-47 @7.x] [code: app/bundles/AssetBundle/EventListener/PointSubscriber.php:44-51 @7.x] [code: app/bundles/PageBundle/EventListener/PointSubscriber.php:55-64 @7.x]
3. `triggerAction()` returns at once when the current user is a logged-in Mautic user, unless `$allowUserRequest` is true. Only the `email.send` caller passes true. So form submits, page hits, downloads and opens made while logged in award no points. [code: app/bundles/PointBundle/Model/PointModel.php:176-178 @7.x] [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:406-411 @7.x] The docs describe this as ignoring "Mautic Administrators". [docs: https://docs.mautic.org/en/7.2/points/points_troubleshooting.html#page-visits-not-recognized]
4. In `prod`, during a main request, a non-null `$typeId` is remembered in the session key `mautic.triggered.point.actions` and is not processed again in that session. All core callers pass `$typeId = null`, so core never uses this de-duplication. [code: app/bundles/PointBundle/Model/PointModel.php:180-189 @7.x]
5. Only published actions count: `isPublished = 1` and inside the publish-up/down window at query time. If no action exists for the type, the method returns before it resolves the Contact. [code: app/bundles/PointBundle/Entity/PointRepository.php:41-54 @7.x] [code: app/bundles/PointBundle/Model/PointModel.php:192-195 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html#point-actions]
6. Without a `$lead` argument, the tracked Contact from `ContactTracker::getContact()` is used. An unsaved Contact (no id) aborts the call. [code: app/bundles/PointBundle/Model/PointModel.php:199-205 @7.x]
7. A non-repeatable action fires once per Contact: action ids already in `point_lead_action_log` for that type are skipped. A repeatable action (`repeatable = 1`) is never logged there and fires on every event. The default is non-repeatable. [code: app/bundles/PointBundle/Model/PointModel.php:211-219,290-297 @7.x] [code: app/bundles/PointBundle/Entity/Point.php:82 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html#point-actions]
8. Each action's `callback` decides whether points are awarded; points are awarded only when it returns a truthy value.
   - The callback is invoked by reflection. Arguments are matched by parameter name from `action` (`id`, `type`, `name`, `properties`, `points`), `lead` and `eventDetails`. Unknown parameters get `null`.
   - Without a registered callback, `EventHelper::engagePointAction` is used. It returns the delta once per Contact per type per PHP process (static cache).
   [code: app/bundles/PointBundle/Model/PointModel.php:226-265 @7.x] [code: app/bundles/PointBundle/Helper/EventHelper.php:16-31 @7.x]
9. Matching rules per action type:
   - `email.open` and `email.send` match when the email id is in `properties.emails`, or that list is empty.
   - `form.submit` matches the form id in `properties.forms`, or an empty list.
   - `asset.download` matches the asset id in `properties.assets`, or an empty list.
   - `page.hit` compares the parent (variant) page id with `properties.pages`; an empty list matches any page.
   - `url.hit` needs `properties.page_url` to match the hit URL through `UrlMatcher`. Every configured option must then hold: `first_time`, `accumulative_time` (seconds), `page_hits`, `returns_within` and `returns_after`. The wildcards `*` and `?` become SQL `%` and `_`.
   [code: app/bundles/EmailBundle/Helper/PointEventHelper.php:15-29 @7.x] [code: app/bundles/FormBundle/Helper/PointActionHelper.php:7-15 @7.x] [code: app/bundles/AssetBundle/Helper/PointActionHelper.php:7-14 @7.x] [code: app/bundles/PageBundle/Helper/PointActionHelper.php:17-114 @7.x] The docs say a URL matches when the configured text is part of the visited URL, case-insensitively, with a trailing `*` matching any URL that starts with the prefix. [docs: https://docs.mautic.org/en/7.2/points/points_troubleshooting.html#page-visits-not-recognized]
10. An awarded delta is applied as a signed increment. It goes to the group score when the action has a group, otherwise to `leads.points` through `Lead::adjustPoints($delta)`. A group action never touches `leads.points`. [code: app/bundles/PointBundle/Model/PointModel.php:266-274 @7.x] [code: app/bundles/PointBundle/Tests/Functional/PointActionFunctionalTest.php:39-62 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html#point-actions]
11. `delta` may be negative or zero; validation allows the signed 32-bit range. A zero delta changes nothing and writes no change-log row. For a non-repeatable action, the once-per-contact `LeadPointLog` row is still written, so the action's one shot is used (inferred from code order). [code: app/bundles/PointBundle/Entity/Point.php:175-184 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:810-812,904-907 @7.x] [code: app/bundles/PointBundle/Tests/Entity/PointEntityValidationTest.php:85-94 @7.x]
12. Every award writes a `lead_points_change_log` row:
    - `type` = the part of the action type before the dot (`email`).
    - `event_name` = `"<id>: <name>"`.
    - `action_name` = the part after the dot (`open`).
    - It also stores `delta`, the IP address, and `group_id` when the action is grouped.
    [code: app/bundles/PointBundle/Model/PointModel.php:268,277-285 @7.x] [code: app/bundles/LeadBundle/Entity/Lead.php:902-923 @7.x]
13. After the change log, the model dispatches `PointEvents::POINT_ON_ACTION` with `PointActionEvent(point, lead)`. Non-repeatable actions then get a `LeadPointLog` row. Logs are saved in one batch. The Contact is saved only if something changed. [code: app/bundles/PointBundle/Model/PointModel.php:287-309 @7.x]
14. Main points are persisted by delta at the SQL level, which keeps concurrent increments safe:
    - `Lead::adjustPoints` accumulates pending changes per operator.
    - The repository drops `points` from the normal UPDATE.
    - `postSaveEntity` runs `UPDATE leads SET points = points + :n` in operator order, retries up to 3 times on deadlock, and re-reads the real value.
    `Lead::setPoints()` sets an absolute value instead and discards pending deltas. [code: app/bundles/LeadBundle/Entity/Lead.php:808-870 @7.x] [code: app/bundles/LeadBundle/Entity/LeadRepository.php:1370-1435 @7.x]
15. Main points accept the operators `plus`, `minus`, `times` and `divide`. `Lead::adjustPoints` rejects `set` with `UnexpectedValueException`. `PointGroupModel::adjustPoints` accepts `set`. [code: app/bundles/LeadBundle/Entity/Lead.php:59-67,821-838 @7.x] [code: app/bundles/PointBundle/Model/PointGroupModel.php:114-121 @7.x]

## B. Point Groups and group scores

16. The first time a Contact gets points in a group, a score row is created with score 0. The new score is computed in PHP (`+ - * / =`), persisted and flushed immediately (not at the later contact save). Then `PointGroupEvents::SCORE_CHANGE` is dispatched with the old and new values. `divide` yields a float passed to `setScore(int)` under `strict_types=1`, so expect a TypeError unless the division is exact (unverified). [code: app/bundles/PointBundle/Model/PointGroupModel.php:3,100-130 @7.x]
17. Group scores are independent of `leads.points`. The segment filter `group_points_<groupId>` queries `point_group_contact_score.score` with `null_value 0`, so a Contact without a row counts as 0. Segments offer these filters; dynamic content does not. [code: app/bundles/PointBundle/EventListener/SegmentFilterSubscriber.php:38-80 @7.x] [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#segment-filters]
18. A group score change runs trigger evaluation and Point Insights synchronously. [code: app/bundles/PointBundle/EventListener/GroupScoreSubscriber.php:26-29 @7.x] [code: app/bundles/PointBundle/EventListener/PointInsightSubscriber.php:26-30 @7.x]
19. The report source `group.score` ("Point group scores") joins `point_group_contact_score` → `point_groups` → `leads`. It exposes `group_id`, `group_name` and `group_score`. A segment filter in the report joins `lead_lists_leads` with `manually_removed = 0`. [code: app/bundles/PointBundle/EventListener/ReportSubscriber.php:17-39,61-104 @7.x] [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#group-report]
20. Deleting a Point Group cascades at database level to its Point Actions, its Point Triggers and its score rows. `lead_points_change_log.group_id` declares no ON DELETE, so what happens to those rows is not determined. [code: app/bundles/PointBundle/Entity/Point.php:167-169 @7.x] [code: app/bundles/PointBundle/Entity/Trigger.php:128-130 @7.x] [code: app/bundles/PointBundle/Entity/GroupContactScore.php:39-42 @7.x] [code: app/bundles/LeadBundle/Entity/PointsChangeLog.php:62 @7.x]
21. Point Groups support entity export and import:
    - Export writes `id`, `name`, `description`, `is_published` and `uuid`.
    - Import matches on `uuid`, then creates or updates.
    - Audit-log rows use `object = 'pointGroup'`.
    - The duplicate check is by `name`.
    [code: app/bundles/PointBundle/EventListener/GroupImportExportSubscriber.php:45-157 @7.x]

## C. API point adjustments

22. `POST /api/contacts/{leadId}/points/{operator}/{delta}` works as follows:
    - It needs edit access on the Contact.
    - It applies `Lead::adjustPoints($delta, $operator)`. The operators are plus, minus, times and divide; `set` gives HTTP 400.
    - It logs `type='API'`. `event_name` comes from the request `eventName` (default: the translated operator label). `action_name` comes from `actionName` (default "API").
    - It saves the Contact.
    [code: app/bundles/PointBundle/Controller/Api/PointApiController.php:68-93 @7.x]
23. `POST /api/contacts/{contactId}/points/groups/{groupId}/{operator}/{value}` also accepts `set`.
    - The log delta is the new score minus the old score.
    - The log has `type='API'`, default event name "Manual change", and `group_id` set.
    - The response includes `groupScore`.
    [code: app/bundles/PointBundle/Controller/Api/PointGroupsApiController.php:113-156 @7.x] [code: app/bundles/PointBundle/Tests/Controller/Api/PointGroupsApiControllerTest.php:89 @7.x]

## D. Campaign and form integration

24. The campaign action `lead.changepoints` ("Adjust contact points") only adds or subtracts.
    - The configured `points` value goes to the group when one is selected, otherwise to `Lead::adjustPoints($points)` with `plus`. A negative value subtracts.
    - The form rejects `0` (`NotEqualTo('0')`), and the run time skips empty values.
    - The log row has `type='campaign'`, `event_name = "<campaignId>: <campaignName>"`, `action_name = "<eventId>: <eventName>"` and the group, if any.
    [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:273-313 @7.x] [code: app/bundles/LeadBundle/Form/Type/PointActionType.php:17-30 @7.x] [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#campaign-action]
25. The campaign condition `lead.points` compares `leads.points`, or the group score when `group` is set. The operators are =, ≠, >, <, ≥ and ≤. For a group, `compareScore` needs an existing score row, so a Contact without a row fails every comparison, including `= 0`. [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:263-270,692-707 @7.x] [code: app/bundles/PointBundle/Entity/GroupContactScoreRepository.php:11-29 @7.x] [code: app/bundles/PointBundle/Tests/Functional/GroupScoreRepositoryFunctionalTest.php:54 @7.x]
26. The campaign condition `lead.stages` passes when the Contact's current stage is one of those selected. An empty selection always fails. The selector offers only published stages. [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:216-223,521-522 @7.x] [code: app/bundles/LeadBundle/Entity/LeadRepository.php:1142-1162 @7.x] [code: app/bundles/StageBundle/Form/Type/StageListType.php:44-54 @7.x]

## E. Point Triggers - when they fire

27. Triggers are evaluated synchronously, never by cron, in three cases:
    - (a) `LeadEvents::LEAD_POINTS_CHANGE`.
    - (b) `LEAD_POST_SAVE` for a new Contact, at priority −1, so 0-point triggers fire on creation.
    - (c) `PointGroupEvents::SCORE_CHANGE`.
    [code: app/bundles/PointBundle/EventListener/LeadSubscriber.php:31-54 @7.x] [code: app/bundles/PointBundle/EventListener/GroupScoreSubscriber.php:26-29 @7.x]
28. `LEAD_POINTS_CHANGE` is dispatched only when all of these hold:
    - `points` changed.
    - The Contact was not imported.
    - The old and new values are not both ≤ 0.
    - The Contact is not new.
    So an import never runs triggers, and a change from −5 to 0 does not either. A decrease such as 10 → 6 does run them, and nothing reverts events that already fired. [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:42-62 @7.x] [code: app/bundles/LeadBundle/EventListener/LeadSubscriber.php:165 @7.x]
29. `TriggerModel::triggerEvents(Lead)` selects two sets of events:
    - Events of published ungrouped triggers whose `points` ≤ the Contact's points.
    - Events of published grouped triggers whose `points` ≤ the Contact's score in that trigger's group.
    A grouped trigger never matches main points, and the reverse also holds. Events are ordered by event order, then by trigger points. [code: app/bundles/PointBundle/Entity/TriggerEventRepository.php:11-61 @7.x] [code: app/bundles/PointBundle/Model/TriggerModel.php:387-423 @7.x] [code: app/bundles/PointBundle/Tests/Functional/PointTriggerFunctionalTest.php:19-75 @7.x] [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#using-point-triggers]
30. Each trigger event runs at most once per Contact. Event ids already in `point_lead_event_log` are skipped. A `LeadTriggerLog` row is written only when `triggerEvent()` returns a truthy value. Nothing re-arms an event when the score drops and climbs back. [code: app/bundles/PointBundle/Model/TriggerModel.php:398-421 @7.x]
31. `triggerEvent(array $event, ?Lead $lead, bool $force)`:
    - Without `$force`, it refuses logged-in users and re-checks the log. `triggerEvents` and the existing-contacts run always pass `$force`.
    - Unknown types return false.
    - A callable `callback` is invoked by reflection with the name-matched arguments `event`, `lead` and `config` (the properties).
    - Otherwise a `TriggerExecutedEvent` is dispatched under the registered `eventName`, and `getResult()` (null, true or false) is returned.
    [code: app/bundles/PointBundle/Model/TriggerModel.php:311-382 @7.x] [code: app/bundles/PointBundle/Tests/Unit/Model/TriggerModelTest.php:74-118 @7.x]
32. The core trigger event types are `email.send`, `email.send_to_user`, `lead.changelists`, `lead.changetags`, `lead.changestage`, `campaign.changecampaign` and `plugin.leadpush`. The full registry is in references/code-map.md.
    - `email.send` sends only when the email is published and the Contact has an email address. Its stat source is `['trigger', eventId]`.
    - `email.send_to_user` reports success or failure through `EmailToUserSubscriber`.
    [code: app/bundles/EmailBundle/Helper/PointEventHelper.php:31-53 @7.x] [code: app/bundles/EmailBundle/EventListener/EmailToUserSubscriber.php:23-35 @7.x] The docs add these rules for "Send an email to user":
    - Choosing a User and also "send to Contact's owner" notifies both.
    - When the owner is missing, or is the chosen User, only one email is sent.
    - Extra to, cc and bcc addresses are comma-separated.
    [docs: https://docs.mautic.org/en/7.2/points/points.html#email-triggers]
33. `lead.changetags` adds and removes tags through `LeadModel::modifyTags`. It reports success only if the tags changed. [code: app/bundles/LeadBundle/EventListener/PointSubscriber.php:88-97 @7.x] [code: app/bundles/LeadBundle/Tests/EventListener/PointSubscriberTest.php:75 @7.x]
34. `lead.changestage` has two modes:
    - With `addstage = 0` ("Remove existing stage"), it removes the current stage and reports success.
    - Otherwise the stage must exist and be published, and `LeadModel::changeStage()` runs with origin "Point trigger". If that throws (lower weight or same stage), the event is marked failed and logged at info level.
    Because a failure writes no `LeadTriggerLog`, the change is retried on every later evaluation. [code: app/bundles/LeadBundle/EventListener/PointSubscriber.php:105-142 @7.x] [code: app/bundles/LeadBundle/Tests/EventListener/PointSubscriberTest.php:93-171 @7.x] The docs say that when the Contact is already in the stage "nothing changes", which is the visible result. [docs: https://docs.mautic.org/en/7.2/points/points.html#contact-triggers]
35. `lead.changelists` adds the Contact to, or removes it from, the configured segments. It never calls `setSucceded()`, so the result stays `null` and no `LeadTriggerLog` row is written. The event therefore runs again on every later evaluation for that Contact (inferred; no test covers the log). [code: app/bundles/LeadBundle/EventListener/PointSubscriber.php:144-159 @7.x] [code: app/bundles/PointBundle/Event/TriggerExecutedEvent.php:11,29-42 @7.x]
36. On save, trigger event `order` is renumbered 1..n from the session or API order, and events are matched to existing ones by id. Through the API, `PUT` removes events missing from the request and `PATCH` keeps them. [code: app/bundles/PointBundle/Model/TriggerModel.php:240-269 @7.x] [code: app/bundles/PointBundle/Controller/Api/TriggerApiController.php:71-111 @7.x]
37. **Trigger for existing contacts.** This runs when a trigger is saved with `trigger_existing_leads = 1` and is published. For each event:
    - It loads Contacts with `date_added <= trigger.date_added` and `points >= threshold`. For a grouped trigger it uses the group score instead.
    - On edit only, it excludes Contacts already in the event log.
    - It forces the event for each Contact and writes a log row on success.
    This runs inline in the save request and is not batched. The form label is "Trigger for existing applicable contacts upon saving (if published)?". [code: app/bundles/PointBundle/Model/TriggerModel.php:106-187 @7.x] [code: app/bundles/PointBundle/Tests/Functional/PointTriggerFunctionalTest.php:77-107 @7.x] The docs say the default is No: then only Contacts that reach the threshold after saving are affected. [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#points-trigger]
38. The trigger threshold is optional in the form and defaults to 0. An empty threshold therefore fires for every Contact, including new ones (item 27b). [code: app/bundles/PointBundle/Form/Type/TriggerType.php:66-77 @7.x]
39. The trigger colour is not applied in 7.2.1. `getColorForLeadPoints()` returns the colour of the lowest matching threshold, but `LeadRepository::setTriggerModel()` has no production caller. The contact list therefore never gets a colour. The default colour is `a0acb8`. [code: app/bundles/PointBundle/Model/TriggerModel.php:430-443 @7.x] [code: app/bundles/LeadBundle/Entity/LeadRepository.php:95 @7.x] [code: app/bundles/PointBundle/Entity/Trigger.php:70 @7.x] The docs describe a working "Contact color". [docs: https://docs.mautic.org/en/7.2/points/points.html#point-triggers]
40. The audit log covers create, update (with changes) and delete for Point Actions and Point Triggers (`bundle='point'`), and for Stages (`bundle='stage'`). Point Groups and Point Insights have no save or delete audit log. [code: app/bundles/PointBundle/EventListener/PointSubscriber.php:34-101 @7.x] [code: app/bundles/StageBundle/EventListener/StageSubscriber.php:29-57 @7.x]

## F. Contact timeline, merge, deletion

41. Two timeline types come from the change logs:
    - `point.gained` ("Point gained") lists `lead_points_change_log` rows, labelled `"<eventName> / <delta>"` plus `" (<groupName>)"` for group changes.
    - `stage.changed` ("Stage changed") lists `lead_stages_change_log` rows and links to the stage when `stage_id` is set.
    [code: app/bundles/PointBundle/EventListener/LeadSubscriber.php:59-100 @7.x] [code: app/bundles/StageBundle/EventListener/LeadSubscriber.php:32-78 @7.x] [docs: https://docs.mautic.org/en/7.2/points/points.html#contact-triggers]
42. On contact merge, the loser's `point_lead_action_log`, `point_lead_event_log` and `stage_lead_action_log` rows move to the winner. Rows that would duplicate a winner row are deleted. LeadBundle merges point totals and change logs. [code: app/bundles/PointBundle/EventListener/LeadSubscriber.php:102-113 @7.x] [code: app/bundles/PointBundle/Entity/LeadPointLogRepository.php:16-51 @7.x] [code: app/bundles/StageBundle/EventListener/LeadSubscriber.php:80-86 @7.x]
43. Deleting a Point Action deletes its `point_lead_action_log` rows. Deleting a Point Trigger deletes its events and their `point_lead_event_log` rows. Deleting a Contact deletes all of its log rows. [code: app/bundles/PointBundle/Entity/Point.php:158-163 @7.x] [code: app/bundles/PointBundle/Entity/Trigger.php:120-126 @7.x] [code: app/bundles/PointBundle/Entity/LeadTriggerLog.php:30-36 @7.x]
44. Other bundles' delete guards ask these models for dependencies:
    - Point Actions of type `email.*` that name an email are reported as dependencies of that email.
    - Trigger events that name a segment (`lead.changelists`), an email (`email.send`, `email.send_to_user`) or a tag (`lead.changetags`) are reported too.
    [code: app/bundles/PointBundle/Model/PointModel.php:341-362 @7.x] [code: app/bundles/PointBundle/Model/TriggerEventModel.php:57-131 @7.x]

## G. Point Insights

45. Every group score change runs each published insight whose `point_groups` list contains the changed group. The check uses strict `in_array`, so ids are stored as ints.
    - The winner is the highest-scoring configured group. Missing rows count as 0. A tie goes to the lower group id.
    - The insight skips when the top score is 0, and skips a tie when the field already has a value.
    - Otherwise it writes `"<groupId> (<groupName>)"` into the custom field and saves the Contact.
    [code: app/bundles/PointBundle/Model/InsightModel.php:67-139 @7.x] [code: app/bundles/PointBundle/Tests/Functional/PointInsightsFunctionalTest.php:22-98 @7.x] [docs: https://docs.mautic.org/en/7.2/points/point_insights.html#how-point-insights-work]
46. Only one insight type (`compare_point_groups`) and one action (`set_custom_field`) exist. The docs say only published text fields can be the target, and that a separate Insights permission controls access. The API does not validate `customField` or `pointGroups`. [code: app/bundles/PointBundle/Entity/PointInsight.php:16-18 @7.x] [docs: https://docs.mautic.org/en/7.2/points/point_insights.html#creating-a-point-insight] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/point_insights.html#create-point-insight]

## H. Stages

47. Stage `weight` must be unique across all stages; validation message `mautic.stage.weight.unique`. Weight is an integer, optional in the form, default 0. The API returns 400 with `weight: Another stage with this weight already exists.` [code: app/bundles/StageBundle/Entity/Stage.php:112-117 @7.x] [code: app/bundles/StageBundle/Form/Type/StageType.php:47-56 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stages.html#create-stage] [docs: https://docs.mautic.org/en/7.2/stages/stages.html#creating-stages]
48. **Weight rule.** `LeadModel::changeStage()` throws `UnexpectedValueException` in two cases:
    - "Contact is already in this stage."
    - "Contact was not able to move into this stage." when the current stage's weight is greater than the target's.
    A move from no stage is always allowed. On success it sets the stage, writes a `lead_stages_change_log` row (`event_name "<id>: <name>"`, `action_name = origin`) and saves. [code: app/bundles/LeadBundle/Model/LeadModel.php:997-1035 @7.x]
49. Only two callers of `changeStage()` enforce the weight rule:
    - The campaign action `stage.change`. It passes with an error message on refusal. A missing or unpublished stage fails the whole batch with "Stage is missing or unpublished".
    - The trigger event `lead.changestage` (item 34).
    These paths bypass the rule:
    - `POST /api/stages/{id}/contact/{cid}/add`, with origin "API: Manually Added".
    - The contact-list batch "change stage" action.
    - Contact edit and import by stage name or id.
    - The campaign "Update contact" action.
    [code: app/bundles/StageBundle/EventListener/CampaignSubscriber.php:46-72 @7.x] [code: app/bundles/StageBundle/Controller/Api/StageApiController.php:69-74 @7.x] [code: app/bundles/LeadBundle/Controller/LeadController.php:1820-1870 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:575-596,1440-1470 @7.x] The docs state the rule without these exceptions. [docs: https://docs.mautic.org/en/7.2/stages/stages.html#moving-contacts-between-stages]
50. `removeFromStage` sets `stage_id` to NULL, writes a log row that references the removed stage (`action_name` "Manually Removed" or "API: Manually Removed") and saves. [code: app/bundles/LeadBundle/Model/LeadModel.php:1061-1078 @7.x] [code: app/bundles/StageBundle/Tests/Functional/Controller/Api/StageApiControllerTest.php:22-46 @7.x]
51. The campaign action, the trigger event and the batch UI list stages from `getUserStages()`. That is published stages, or stages the user created when the user lacks `stage:stages:viewother`. The segment and campaign-condition selector offers published stages only. An unpublished stage is rejected at execution time. [code: app/bundles/StageBundle/Model/StageModel.php:181-187 @7.x] [code: app/bundles/StageBundle/Entity/StageRepository.php:104-131 @7.x] [docs: https://docs.mautic.org/en/7.2/stages/stages.html#creating-stages]
52. Deleting a stage sets `leads.stage_id` to NULL (`ON DELETE SET NULL`) and deletes its `stage_lead_action_log` rows. `lead_stages_change_log.stage_id` keeps the deleted id (inferred: no ON DELETE). [code: app/bundles/LeadBundle/Entity/Lead.php:416-421 @7.x] [code: app/bundles/LeadBundle/Entity/StagesChangeLog.php:45 @7.x]
53. **Stage merge** (`stageMerge(primary, secondary)`) runs in one transaction:
    - It moves Contacts to the primary stage.
    - It re-points `lead_stages_change_log`.
    - It re-points `stage_lead_action_log` in batches of 500, deleting would-be duplicates.
    - It deletes the secondary stage.
    It writes no change-log rows for the moved Contacts. The UI needs edit and delete permission. [code: app/bundles/StageBundle/Model/StageModel.php:151-179 @7.x] [code: app/bundles/StageBundle/Controller/StageController.php:403-460 @7.x] [docs: https://docs.mautic.org/en/7.2/stages/stages.html#merging-stages]
54. Segment filters:
    - `stage` works on `leads.stage_id` with =, ≠, empty and !empty.
    - `points` is a numeric filter on `leads.points`.
    - `group_points_<id>` works as in item 17.
    [code: app/bundles/LeadBundle/EventListener/FilterOperatorSubscriber.php:201-206,307-320 @7.x]
55. The dashboard widgets `points.in.time` and `stages.in.time` count change-log rows per period. Users without `viewother` see only their own Contacts. [code: app/bundles/PointBundle/Model/PointModel.php:320-336 @7.x] [code: app/bundles/StageBundle/Model/StageModel.php:133-149 @7.x] The docs also describe a **Lifecycle** widget (Contacts per stage within segments). [docs: https://docs.mautic.org/en/7.2/stages/stages.html#lifecycle]
56. Stage "actions" are vestigial. `STAGE_ON_BUILD` has no subscribers, `STAGE_ON_ACTION` is never dispatched, and core never writes `stage_lead_action_log`. [code: app/bundles/StageBundle/Model/StageModel.php:116-131 @7.x] [code: app/bundles/StageBundle/Helper/EventHelper.php:9-14 @7.x]
57. Validation:
    - Point Action: name, type and delta required; delta within int32.
    - Point Trigger: name required.
    - Point Group: name required.
    - Point Insight: name, type and action required.
    - Stage: name required; weight unique.
    [code: app/bundles/PointBundle/Entity/Point.php:175-184 @7.x] [code: app/bundles/PointBundle/Entity/Trigger.php:136-139 @7.x] [code: app/bundles/PointBundle/Entity/PointInsight.php:72-79 @7.x]
58. Log dates are set with `new \DateTime()` at write time. Publish windows are compared with the current time at query time. The existing-contacts filter uses the trigger's `date_added` converted to UTC. [code: app/bundles/CoreBundle/Entity/CommonRepository.php:527-560 @7.x] [code: app/bundles/PointBundle/Model/TriggerModel.php:127 @7.x]

## D (cont.). Form submit action

59. The form submit action `lead.pointschange` ("Adjust contact's points") applies `operator` and `points` to the tracked Contact, or to a group when `group` is set. It has no logged-in-user check. [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:70-78,164-205 @7.x] [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#form-action]
60. That action's change-log row has these values:
    - `type='form'`.
    - `event_name = "<formId>:<formName>"`.
    - `action_name` = the action name.
    - `delta` = new main points minus old main points.
    With a group, the delta is therefore 0 and no group is recorded (inferred). [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:174-202 @7.x]

## I. Imports and webhooks

61. CSV import sets `points` only for new Contacts and writes a change-log row with `type='lead'`. Existing Contacts keep their points. [code: app/bundles/LeadBundle/Model/LeadModel.php:1420-1430 @7.x]
62. Imports never run triggers (item 28). A Contact imported above a threshold fires only after a later non-import points change. [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:42-62 @7.x]
63. The "Contact Points Changed" webhook type follows `LEAD_POINTS_CHANGE`. Group score changes do not fire it. [code: app/bundles/LeadBundle/EventListener/WebhookSubscriber.php:33,69,165 @7.x] [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#webhooks]
