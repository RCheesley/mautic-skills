# Points and stages - pull-request history

## How to read this file
Source: merged pull requests on github.com/mautic/mautic for PointBundle and StageBundle, harvested 2026-10-15.
Versions are inferred from each PR's base branch and merge date; `~` marks an inference, and "7.x head" means merged after 7.2.1.
Current behaviour lives in behaviour.md (code-verified); this file explains why and when it came to be.

## Decisions that shaped current behaviour

### Point Actions
- A non-repeatable Point Action awards points once per Contact; "Is repeatable" awards points every time the Contact performs the action. All actions were one-time only until repeatable actions were added after a long-standing community request; new actions default to off [PR #6388] (v2.15.0).
- The `repeatable` column has a database default, so creating a Point Action through the API without `repeatable` works on MySQL strict mode. 2.15.0 had broken this for strict-mode databases and it was fixed in a patch release [PR #7326] (v2.15.1).
- The "Is repeatable" field carries a tooltip: enabled means points every time the action is completed, disabled means a one-time score [PR #13479] (v5.1.0).
- The Point Action delta must lie in the signed 32-bit range; an out-of-range value gives a validation error instead of HTTP 500 [PR #11191] (v4.4.0).
- The action type selector is labelled "Action taken by contact". Originally "When a contact..."; changed to "Action taken by user" for screen readers by [PR #13495] (v5.1.0); corrected to "contact" by [PR #13658] (v5.1.0) because "user" names the wrong entity.
- "Is sent an email" and "opens an email" actions cover segment (broadcast) emails as well as template emails, and segment emails appear in the "limit to these emails" selector [PR #8619] (v3.0.2).
- A repeatable "is sent an email" action awards once per send. `EMAIL_ON_SEND` used to be dispatched twice per send, which double-awarded repeatable points [PR #8619] (v3.0.2).
- Email-send points are awarded when the send runs from the CLI, using the Contact passed in the event rather than the cookie-tracked Contact; no cookies are set in a console command [PR #1191] (v1.2.3). The mechanism is historical; behaviour item 2 records `allowUserRequest = true` for `email.send` today.
- The "Visits specific URL" action honours every configured criterion (URL, returns within, returns after and the others) [PR #2296] (v2.1.1). Rejected at the time: awarding points when any single criterion matches; the related request for repeated awards was delivered later as "repeatable" [PR #6388] (v2.15.0). Behaviour item 9 confirms that every configured option must hold.
- The "Visits specific URL" action works when the hit is the tracking pixel `/mtracking.gif`: the pixel returns 200 and points are added. The removal of `MauticFactory::getEntityManager()` broke this path during review and it was fixed before merge [PR #14611] (v6.0).
- A custom Point Action registered by a plugin without its own properties form gets no extra "Change points (+/-)" field, and the action's top-level delta is the awarded value. Mautic used to inject `GenericPointSettingsType`, and `EventHelper::engagePointAction` read the delta from properties, so such actions awarded nothing; built-in actions hid the bug because they use their own callbacks [PR #14218] (v5.2).
- Saving a Contact when no Point Action produced a log does not error; the Contact is saved only when a points log exists [PR #14714] (v6.0.3). The failure was reproduced only with a private plugin.
- `PointActionEvent` is dispatched when a Point Action is processed, so listeners can react [PR #1684] (v2.0.0). Behaviour item 13 records the current dispatch point.
- Core maintainers want point handling moved from static callbacks to events; this was deferred out of the `MauticFactory` removal [PR #14611] (v6.0).

### Point Triggers: firing and execution
- 0-point triggers fire for newly created Contacts. Triggers originally ran only on a points change, so a 0-point trigger meant "every new Contact" never ran [PR #238] (v1.0.x). Behaviour items 27-28 give the current rule.
- Triggers fire only once the Contact reaches the threshold; an early query fired them prematurely, and a stale tracking cookie looped anonymous-contact creation [PR #119] (v1.0.0).
- When one points change crosses several thresholds, every trigger whose threshold is now met runs, in order. With triggers at 1, 20 and 30 and a +35 action, all three run and the 30-point trigger's tag result wins. Reviewers confirmed it also works with Point Groups [PR #12867] (v5.0.0).
- Executing a trigger never deletes its events from `point_trigger_events`. Originally [PR #12353] (v5.0.0) replaced `em->clear()` with a call that deleted rather than detached trigger events, so triggers "vanished after first invocation"; fixed by [PR #14448] (v5.2.2), which removed the call. A manual detach was rejected because no memory leak needed solving.
- Point Triggers can change or remove a Contact's stage with the trigger event `lead.changestage`; the target stage must be published [PR #17041] (v7.2.0). Stage progression by points used to need a campaign workaround.
- The trigger event "Push contact to integration": cancelling the popup without choosing an integration does not throw [PR #11968] (v5.0.0).

### Point Triggers: admin UI and lifecycle
- Batch delete on the trigger list deletes the selected triggers. The controller used the contact model, which could delete a Contact with the same id [PR #438] (v1.1).
- Cloning a Point Action or a Point Trigger does not persist anything until the clone is saved [PR #700] [PR #701] (v1.2.0).
- Cloning a trigger copies its events, and the clone keeps them after the first Apply or Save. Events were lost on clone since the Twig migration [PR #11968] (v5.0.0); fixed by [PR #14177] (v5.2) and reinforced by [PR #15186] (v7.0.0).
- Deleting an event from a trigger and clicking Apply removes it from the form at once [PR #15186] (v7.0.0).
- The trigger colour is required in the database and defaults when left empty [PR #754] (v1.2.0). It was shown in the trigger list and re-populated the form [PR #1228] [PR #1235] (v1.2.3). See the open questions: behaviour item 39 says the colour is not applied in 7.2.1.
- In the "Send an email to user" trigger event, the Preview and Edit buttons open the selected email, are enabled when editing an event that has an email, and are disabled when none is selected [PR #11449] (v5.0.0).
- The "Select an event from the 'Add an event' list" prompt appears once [PR #13480] (v5.1.0).
- Trigger event rows show their edit and delete buttons on hover [PR #14617] (v5.2.3). Hover styling uses the theme variable `--layer-hover` so text stays readable in dark themes [PR #15254] (v7.0.0).
- The "Add an event" button has a visible background and outline for accessibility [PR #15546] (v7.0.0).
- The trigger list can be sorted by category [PR #11968] (v5.0.0), and the Point Action list sorts by category without an SQL error [PR #2006] (v2.0.1).
- Deleting a trigger, single or batch, warns that its event configuration and trigger history are permanently deleted [PR #17442] (7.x head, ~7.3).
- Users with view-only permission see point, trigger and stage names as plain text, not as links to edit pages that would fail [PR #6928] (v2.15.1).

### Point Groups
- Point Groups (proposed as "Point Leagues") give a Contact separate named scores. A Point Action or a trigger can target a group; Contact details show group points; campaigns get a group-points condition and action; segments get a group-points filter; there is a "Group points" report [PR #11891] (v5.0.0). Rejected: the name "League", because it implied a ranking; a forum vote chose "Groups" over Types, Families, Sections and Tiers.
- Point Groups have a REST API: CRUD under `/api/points/groups`, reads under `/api/contacts/{id}/points/groups`, and `POST /api/contacts/{contactId}/points/groups/{groupId}/{operator}/{value}` to adjust a score [PR #13517] (v5.1.0).
- A group score is keyed by `(contact_id, group_id)` in that order. Moving only `$group` to Doctrine attributes reversed the key and caused schema drift; mapping `$contact` first fixed it [PR #17454] (v8.0). An earlier mapping error on `GroupContactScore` was fixed in [PR #13231] (v5.0.2).
- Deleting a Point Group, single or batch, warns that its Contact scores are permanently deleted [PR #17447] (7.x head, ~7.3). Behaviour item 20 adds that the group's Point Actions and triggers are deleted too, which the dialog does not mention.

### Point Insights
- Point Insights compare chosen Point Groups and write the winner to a custom field as `ID (GroupName)`. Every published insight runs whenever a group score changes, through `GroupScoreChangeEvent` [PR #15359] (v7.2.0). Contested: two core maintainers asked for a plugin to keep core lean; others argued interest-based scoring belongs in core, and it was merged after product-team discussion.
- The Point Insights list has empty-state text that explains the feature [PR #16465] (v7.2.0).

### Stages
- A campaign "change stage" action cannot move a Contact to a lower-weight stage [PR #8063] (v3.0.0). Behaviour items 48-49 confirm the rule and list the paths that bypass it.
- The campaign "change contact stage" action runs in batches. A Contact that cannot move is recorded as a failure on its timeline and does not unpublish the campaign [PR #8969] (v3.3.3). Testers could not reproduce the unpublish symptom after [PR #8907] (v3.0.0) fixed a crash in the Symfony 3 dispatcher; the PR was merged for batch performance.
- All stage transitions (campaign action, point trigger, contact batch update, Stage API) go through one LeadModel path for a consistent stage update and audit log. `addToStages()` and `removeFromStages()` stay as BC wrappers [PR #17041] (v7.2.0). Only `changeStage()` applies the weight rule (behaviour item 49).
- Import with a stage column assigns the stage to new and existing Contacts; the stage is matched by name and created without a weight when missing [PR #2076] (v2.1.1).
- Stage lookup by name does not confuse "1 - Lead" with "10 - Customer" and does not throw `NonUniqueResultException` [PR #9066] (v3.1.0).
- A stage change writes a timeline entry linked to the stage, and the change log references the stage by a nullable id so deleting the stage keeps the log [PR #2635] (v2.2.1).
- The Stage API add and remove endpoints persist the change; they once returned success without saving [PR #3437] (v2.6.1).
- Stages appear in global search [PR #2082] (v2.1.0).
- Stages can be merged from the list (edit and delete permission). Contacts and stage history move to the target stage and the source stage is permanently deleted [PR #15399] (v7.2.0).
- Stage weights are unique. The form checks as the user types, lists existing weights, and the server rejects a conflict with `mautic.stage.weight.unique`. The first version validated only in the browser; a tester submitted a duplicate, so server-side validation was added [PR #15404] (v7.2.0).
- The campaign detail page shows a translated label for the stage change action [PR #2172] (v2.1.0).

### Projects, plugins, API and refactors
- Point Actions, Point Triggers and Stages can be assigned to Projects and searched by project in the UI and API [PR #15409] (v7.0.0).
- The Point Action, trigger and stage list templates expose `customContent()` hooks for plugins [PR #14488] (v6.0.0).
- The Points and Stages list pages show ProTips [PR #14035] (v5.2).
- `/api/points` and `/api/points/triggers` return entities without a serializer error [PR #1581] (v1.4.0). The trigger API works on Symfony 4 with the lowercase model alias `point.triggerevent` and the FOS REST body listener [PR #9865] (v4.0.0).
- Publish-date filtering for points, triggers, trigger events and stages uses `getPublishedByDateOrmExpression()` or `getPublishedByDateDbalExpression()`. A mediator abstraction was the rejected alternative [PR #16970] (v7.2.0).
- Point and Stage templates are Twig from 5.0 [PR #11565] [PR #11968] (v5.0.0). Forms moved to Symfony 3 form types for 3.0 [PR #8063] [PR #8230] (v3.0.0).
- Point and Stage controllers receive models by typed injection, not `getModel('...')` [PR #16597] [PR #16622] [PR #16635] [PR #16648] (v7.2.0).

## Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **Point Actions** | | | |
| URL-hit action ignored "returns within/after" | Every configured criterion must hold | #2296 | 2.1.1 |
| API create of a Point Action failed on strict SQL mode | `repeatable` has a default; create succeeds | #7326 | 2.15.1 |
| Segment emails not selectable and not awarding points | Segment emails selectable and awarding | #8619 | 3.0.2 |
| Repeatable "is sent an email" awarded twice per send | One award per send | #8619 | 3.0.2 |
| Huge delta gave HTTP 500 | Validation error with the int32 range | #11191 | 4.4.0 |
| Custom plugin action awarded nothing; duplicate delta field | Top-level delta awarded; no extra field | #14218 | 5.2 |
| Tracking-pixel URL hit gave HTTP 500 | Pixel returns 200 and points are added | #14611 | 6.0 |
| Error saving a Contact when no points log was produced | No error; Contact saved only with a log | #14714 | 6.0.3 |
| Sorting Point Actions by category gave an SQL error | Sort works | #2006 | 2.0.1 |
| **Point Triggers** | | | |
| 0-point triggers never fired | 0-point triggers fire for new Contacts | #238 | 1.0.x |
| Batch delete of triggers deleted Contacts | Selected triggers deleted | #438 | 1.1 |
| Trigger API "triggerEvent is not a registered container key" | Endpoints work | #9865 | 4.0.0 |
| "Send email to user" preview 404, buttons disabled on edit | Buttons open the selected email | #11449 | 5.0.0 |
| Push-to-integration popup cancel threw TypeError | Cancel works | #11968 | 5.0.0 |
| Tags from several crossed thresholds not applied | Every met trigger runs; highest threshold's result stands | #12867 | 5.0.0 |
| Cloned trigger lost its events | Events cloned and kept after save | #14177, #15186 | 5.2, 7.0.0 |
| Trigger events deleted after first execution | Events persist | #14448 | 5.2.2 |
| Deleted trigger event still shown after Apply | Removed at once | #15186 | 7.0.0 |
| Trigger event buttons hidden on hover; white-on-white in dark theme | Buttons visible; theme hover colour | #14617, #15254 | 5.2.3, 7.0.0 |
| **Point Groups** | | | |
| `GroupContactScore` mapping error | Valid mapping | #13231 | 5.0.2 |
| Group score primary key reversed to `(group_id, contact_id)` | Key stays `(contact_id, group_id)` | #17454 | 8.0 |
| **Stages** | | | |
| Import with a stage column errored | Stage matched by name or created; assigned to new and existing Contacts | #2076 | 2.1.1 |
| Stage API add/remove returned success without saving | Change persisted | #3437 | 2.6.1 |
| Stage change via campaign threw an undefined-method error | Change works | #8907 | 3.0.0 |
| Change-stage failure unpublished the campaign | Failure on the Contact timeline; campaign stays published | #8969 | 3.3.3 |
| `NonUniqueResultException` for stage names with numbers | Exact name match | #9066 | 3.1.0 |
| Duplicate stage weight saved after client-side check | Server rejects with `mautic.stage.weight.unique` | #15404 | 7.2.0 |
| **Cross-cutting** | | | |
| View-only users got links to edit pages | Names shown as plain text | #6928 | 2.15.1 |
| Global search JS error; stages not found | Global search includes stages | #2082 | 2.1.0 |

Rows from 1.x that describe removed mechanisms ([PR #119], [PR #700], [PR #754], [PR #1191], [PR #1228], [PR #1324], [PR #1581]) are kept in the timeline only.

## Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.0-1.4 | Trigger threshold fix; 0-point triggers; trigger batch delete; clone fixes; trigger colour default and display; CLI email-send points; Points/Triggers API fixes | #119, #238, #438, #700, #701, #754, #1228, #1235, #1191, #1324, #1581 |
| 2.0-2.6 | `PointActionEvent`; category sort; stages in global search; stage import; URL-hit criteria; stage timeline entry; Stage API persists | #1684, #2006, #2082, #2076, #2296, #2635, #3437 |
| 2.15 | Repeatable Point Actions; strict-mode default; view-only plain names | #6388, #7326, #6928 |
| 3.0 | Symfony 3 forms; forward-only campaign stage change; dispatcher fix; segment-email points | #8063, #8230, #8907, #8619 |
| 3.1-3.3 | Stage names with numbers; batched campaign change-stage action | #9066, #8969 |
| 4.0-4.4 | Symfony 4 trigger API; int32 delta validation | #9865, #11191 |
| 5.0.0 | Twig templates; Point Groups; multi-threshold trigger fix; "Send email to user" buttons | #11565, #11968, #11891, #12867, #11449 |
| 5.0.2 | `GroupContactScore` mapping fix | #13231 |
| 5.1.0 | Point Groups API; "Action taken by contact" label; repeatable tooltip; single event prompt | #13517, #13495, #13658, #13479, #13480 |
| 5.2 | ProTips; clone keeps trigger events; custom actions use top-level delta | #14035, #14177, #14218 |
| 5.2.2-5.2.3 | Trigger events persist after execution; hover buttons | #14448, #14617 |
| 6.0.0 | `customContent()` hooks; `GenericPointSettingsType` removed; tracking-pixel URL hit after factory removal | #14488, #13904, #14611 |
| 6.0.3 | No error saving a Contact without a points log | #14714 |
| 7.0.0 | Projects; trigger event Apply fixes; dark-theme hover; visible "Add an event" button | #15409, #15186, #15254, #15546 |
| 7.2.0 | Point Insights and onboarding; stage merge; unique stage weights; trigger "change stage"; central stage path; split publish-date expressions; typed model injection | #15359, #16465, #15399, #15404, #17041, #16970, #16597, #16622, #16635, #16648 |
| 7.x head (~7.3) | Permanent-deletion warnings for triggers and groups | #17442, #17447 |
| 8.0 | Group score key order preserved under attribute mapping | #17454 |

## Removed, deprecated, replaced

| What | Replaced by | PR | Version | Note |
|---|---|---|---|---|
| PHP templates in PointBundle and StageBundle | Twig | #11565, #11968 | 5.0.0 | Overrides must be Twig |
| `em->clear()` in point models | Removed call | #12353, #14448 | 5.0.0, 5.2.2 | The 5.0 replacement deleted trigger events |
| `GenericPointSettingsType` added to custom actions | Top-level delta | #14218 | 5.2 | No default properties form |
| `GenericPointSettingsType` class | Nothing | #13904 | 6.0.0 | BC break in UPGRADE-6.0.md |
| `MauticFactory::getEntityManager()` | Injected EntityManager | #14611 | 6.0 | In UPGRADE-6.0.md |
| Label "When a contact..." | "Action taken by contact" (`mautic.point.form.type`) | #13495, #13658 | 5.1.0 | Briefly "Action taken by user" |
| `CommonRepository::getPublishedByDateExpression()` | ORM and DBAL variants | #16970 | 7.2.0 | Deprecated wrapper kept |
| `getModel('point'…)` string lookups in controllers | Typed injection | #16597, #16622, #16635, #16648 | 7.2.0 | Internal |
| `LeadModel::addToStages()`/`removeFromStages()` as primary API | Explicit add, change and remove methods | #17041 | 7.2.0 | Kept as BC wrappers |

## Maintainer norms for this area
- New non-null columns need a database default so the API does not break on strict SQL mode [PR #7326]; schema changes ship with a migration [PR #2635] [PR #6388].
- Doctrine mapping changes must not change primary-key order or cause schema drift [PR #17454].
- A refactor that breaks a user flow is not merged, even when the refactor is the goal [PR #14611].
- Prefer functional tests that reproduce the bug over heavily mocked unit tests [PR #14714]; API endpoints should also test 404 and XSS cases [PR #13517].
- Maintainers do not merge when testers cannot reproduce the problem or understand the feature [PR #8969] [PR #15359].
- New features come with a documentation PR [PR #13517] [PR #15359]; docs drafted by Promptless must be reviewed by the author [PR #15399] [PR #17041].
- Whether a niche feature belongs in core or in a plugin is decided by the product team and community [PR #15359].
- User-facing names can go to a community vote [PR #11891]; labels must name the right entity, "contact" not "user" [PR #13658].
- Confirmation dialogs for destructive actions state the irreversible consequence [PR #17442] [PR #17447].
- UI colours use theme CSS variables so dark themes work [PR #15254].

## Open questions
- Conflict with behaviour.md: the trigger colour was shown in the trigger list and used on contact profiles [PR #754] [PR #1228]. Behaviour item 39 says the colour is not applied in 7.2.1, and the 7.x trigger list template has no colour column. behaviour.md wins; the PRs are historical.
- Conflict with behaviour.md: the stage merge PR says Contacts and stage history move to the target [PR #15399]. Behaviour item 53 confirms the move but records that no new change-log rows are written for moved Contacts. behaviour.md wins.
- Partly resolved: "all stage transitions go through one path" [PR #17041] does not mean one rule; behaviour item 49 shows only `changeStage()` callers enforce the forward-only rule [PR #8063].
- Resolved by code: the Point Insights tie rule was truncated in the PR [PR #15359]; behaviour item 45 says a tie goes to the lower group id and keeps an existing value.
- Import creates a missing stage with weight 0 [PR #2076]. Whether that bypasses the unique-weight rule added later is unverified [PR #15404].
- Pre-existing duplicate stage weights on upgrade: no migration is mentioned [PR #15404].
- The campaign-unpublish symptom was never reproduced, and the stage failure message on the timeline stays generic [PR #8969].
- [PR #12353] has no description; other changes it made in PointModel may have side effects beyond the deletion fixed by [PR #14448].
- The trigger condition for the contact-save error is unknown outside a private plugin [PR #14714].
- [PR #14611] carried a 6.0.0-beta2 milestone while discussion mentioned 7.0-alpha; it merged to 6.x on 2025-03-05.

## Coverage
78 merged PRs fall in this area, in one chunk covering 2015-03-03 to 2026-09-18 (#119 to #17454).
64 are substantive, 10 are refactor-only (#485, #9959, #12956, #12964, #12999, #13005, #16597, #16622, #16635, #16648) and 4 are noise (#10381, #10382, #13274, #16464).
A further 869 noise PRs across all areas were excluded upstream before chunking.
