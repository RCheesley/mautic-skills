# Campaigns — PR history

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
3. Regression catalogue
4. Feature timeline
5. Removed, deprecated, replaced
6. Maintainer norms for this area
7. Open questions
8. Coverage

## 1. How to read this file
Source: merged pull requests on mautic/mautic for the Campaigns area, harvested 2026-10-15.
Versions are inferred from the base branch, milestone and merge date; where a release tag was checked in the 7.x tree, the first tag that contains the change is used.
Current behaviour is in behaviour.md. This file explains why and when. Where the two disagree, behaviour.md wins.

## 2. Decisions that shaped current behaviour

### Membership: sources, rebuild and cron
- Campaign and Segment membership is built by batched CLI commands, never when a campaign or Segment is saved in the UI. Why: building it in a web request hit PHP memory limits and timeouts on large lists [PR #337] (v1.0.4).
- `mautic:segments:update` does not change campaign membership; only `mautic:campaigns:update` (alias of `mautic:campaigns:rebuild`) adds and removes members from source Segments. Originally a Segment rebuild also synced campaigns [PR #337] (v1.0.4); decoupled by [PR #10550] (v5.0: the `LeadSubscriber` Segment handlers are still at tag 4.4.13 and gone at 5.0.0). Why: performance, and both commands are mandatory crons anyway, so maintainers did not treat it as a BC break [PR #10550].
- A campaign whose only source is a Form must not make the rebuild fail; it reports there is nothing to rebuild and carries on [PR #533] (v1.1) [PR #1286] (v1.2.4).
- Segment-driven adds and removals are not filtered by the current user's campaign permissions. Every campaign that uses the Segment is affected, whoever owns it. Why: the code runs mostly outside a user session; [PR #6963] had added a "view other" check that broke it [PR #7606] (v3.3).
- Membership flags have fixed meanings: a Segment exit sets `manually_removed = 1` and `date_last_exited`; a manual removal sets `manually_removed = 1` and leaves `date_last_exited` NULL; Segment adds have `manually_added = 0`. The M3 refactor [PR #8374] had reversed the remove flag in places [PR #8573] (v3.0).
- Rebuild queries do not use ORDER BY or OFFSET; a max Contact ID fixes the pool while batching. Why: speed on large tables, and offset plus "pending only" skipped about half the Contacts [PR #1290] (v1.2.4) [PR #1609] (v1.4).
- The contacts-by-segment kickoff query does use ORDER BY so parallel workers get non-overlapping ID ranges. Why: overlapping ranges made one failing worker strand every later Contact [PR #14860] (v7.0).
- Rebuilds and removals run in batches so 100k+ campaigns do not exhaust memory or exceed `max_allowed_packet` [PR #6507] (v2.14.2) [PR #6973] (v2.15.1).
- `mautic:campaigns:rebuild`, `mautic:campaigns:trigger` and `mautic:segments:update` take `--exclude` to skip IDs [PR #13383] (v5.1), and return a non-zero exit code when `-i` names a campaign that does not exist [PR #11963] (v4.4.8) [PR #12203] (v5.0).

### Restart, rotation and re-entry
- A Contact repeats a campaign only when the campaign has "Allow contacts to restart" on and the Contact is removed and added again; each pass is a new rotation and history is kept. Why: re-running old campaigns for everyone who moves in and out of tag-based Segments was rejected in review, so restart became a per-campaign opt-in [PR #6132] (v2.14).
- The log unique key is event + Contact + rotation (`campaign_rotation`) [PR #4040] (v2.8.1). It is checked in 7.x [code: app/bundles/CampaignBundle/Entity/LeadEventLog.php:125 @7.x].
- A manually removed Contact can always be re-added manually, with or without restart. Why: maintainers said the block "wasn't intentional"; an alert-based alternative was rejected [PR #7020] (v2.15.1).
- With restart on, Contacts who left a source Segment and match it again are re-added by the rebuild. Originally [PR #7704] (v2.16) excluded only active memberships; the 2018 count-query bug that skipped them was fixed by [PR #16184] (v7.1.3), and the repeatable-batch bug that stopped after 300 Contacts by [PR #10766] (v4.2).
- With restart off, Contacts who exited (condition branch, Segment move, source filter) are never re-added automatically. Why: Contacts were restarted and re-sent the first email on every cron (issue #16133) [PR #16183] (v7.1.3).
- Restartable rebuilds must terminate when a Contact was manually removed but still matches the Segment [PR #11318] (v5.0) [PR #15461] (v7.0), and when a pre-2.14 Contact has logs but no membership row [PR #6463] (v2.14.1).
- Duplicate `campaign_rotation` errors were fixed several times. [PR #7129] (v3.2.2) bumped the rotation when a scheduled jump re-ran an event but incremented twice for immediate jumps; [PR #10206] (v5.1) moved the increment so it happens once; [PR #9639] (v4.0.2) used each campaign's rotation when one trigger matches two campaigns; [PR #14939] (v7.0) fixed the same clash when one campaign uses Jump to Event. In 7.x the logger caches rotations keyed by campaign then Contact [code: app/bundles/CampaignBundle/Executioner/Logger/EventLogger.php:31-33,88-96 @7.x], jump logs are generated before the rotation is incremented [code: app/bundles/CampaignBundle/Executioner/EventExecutioner.php:189-202 @7.x], and the jump subscriber increments the rotation once per jump [code: app/bundles/CampaignBundle/EventListener/CampaignActionJumpToEventSubscriber.php:89-93 @7.x].

### Decisions and the inactive path
- "No"-path actions run only for Contacts who did not take the decision in time, never for everyone [PR #273] (v1.0.3). Positive decision events are always logged so the negative path can exclude them [PR #1750] (v1.4.1).
- The inactive wait is the delay on the action connected to the red path, not a setting on the decision [PR #273] (v1.0.3). It is measured from when the parent actually executed [PR #1311] (v1.2.4), or from the join date for a root decision [PR #1226] (v1.2.3).
- With several red-path branches, the earliest timeframe decides inactivity and the others are scheduled from it [PR #5942] (v2.14).
- An action on a decision's red path runs as soon as the decision's wait expires; its own interval and hour window are ignored. Why: users found negative-path actions delayed beyond what they expected [PR #14289] (v5.2).
- An action on a decision's red anchor cannot be immediate, because the delay defines inactivity; a condition there, or an action on a condition's false path, can be immediate [PR #2423] (v2.2) [PR #2812] (v2.3).
- Red-path events do not run for a Contact who has left the campaign [PR #7802] (v2.15.3), and wait until the parent has really run when it is still scheduled [PR #9486] (v4.0.2).
- A decision after a condition honours the condition's branch on the negative path; the logic lives in `DecisionHelper`, shared by real-time and inactive execution [PR #11200] (v4.4).
- Real-time decisions are evaluated only when reachable: the parent action has run and the Contact is on that branch [PR #6940] (v2.15). They also respect the campaign's publish-up/publish-down dates, not only the toggle [PR #14303] (v5.2.1).
- The positive path runs in the same request as the Contact's activity, not on the next cron. Why: "that's the right behavior and was the same in the old code" [PR #5942] (v2.14).
- "Opens email" has no email selector; it applies to the Send email action it follows [PR #439] (v1.1).
- A decision limited to one channel item stores the real channel ID [PR #6322] (v2.14). Channel IDs became VARCHAR(64) for plugins with string IDs [PR #15132] (v7.0) and are compared as strings [PR #15252] (v7.0).
- URL decisions match redirect hits as well as page hits [PR #6580] (v2.14.2).

### Conditions and event chaining
- Conditions are a third event type that evaluates immediately [PR #906] (v1.2.1) and runs only after its parent succeeded [PR #1069] (v1.2.2).
- Action → action connections are an official feature. Why: they worked by accident before 2.14 and users relied on them, although a [PR #906] review had said chaining was unsupported [PR #6187] (v2.15).
- "Not equal" field conditions treat NULL as matching, and date conditions compare in local time [PR #3180] (v2.6).
- Exclude operators on select and multiselect fields send empty or non-matching values down the positive path; include operators send empty values down the negative path [PR #14071] (v5.2).
- Root decisions are never kickoff events [PR #506] (v1.1) and never send one Contact down both paths [PR #1069] (v1.2.2). For which Contacts a root decision's red path is evaluated, see behaviour.md B56.

### Scheduling: intervals, hours, weekdays, timezones
- Day-based relative delays can be restricted to an hour, an hour range and weekdays, computed in the Contact's timezone with the system timezone as fallback [PR #6520] (v2.14.2). Follow-up fixes: N days ahead at the chosen hour [PR #6755] (v2.14.2); today if the hour is still ahead [PR #6822] (v2.15); weekday-only never runs immediately [PR #6822]; root interval scheduled once [PR #6886] (v2.15); rescheduling keeps the local hour [PR #7448] (v2.15.2); next selected weekday [PR #8874] (v3.0) [PR #9018] (v3.1).
- Weekday restrictions apply to every unit, including no delay [PR #11332] (v5.0), and use 0–6 numbering with Sunday = 0 [PR #14612] (v6.0).
- "Schedule at" with a relative delay behaves like "between the hours of" [PR #13263] (v5.1).
- A Contact who arrives on an allowed weekday after the send hour runs that day, not next week [PR #14312] (v5.2.1). When the weekday rule moves execution to a later day, the time resets to the send hour in the Contact's timezone [PR #17283] (v7.2.1).
- DST fall-back must not cause an hourly reschedule loop [PR #11602] (v4.4.4). Specific-date events keep the same wall-clock time across repeated saves by non-UTC users [PR #17091] (v7.2.0).
- Optimized scheduling picks a per-Contact time from past opens, page hits and form submissions, for Send Email, Marketing Message, Push to Integration and Send Webhook. Below 5 interactions the defaults apply [PR #13569] (v5.2). Decision forms must not receive its `triggerWindow` field; loosening validation with `allow_extra_fields` was rejected [PR #14325] (v5.2.1).
- Scheduled logs whose recomputed date is still in the future are rescheduled to their own date, not to now. Why: a 7.x regression looped forever [PR #16066] (v7.1.3).
- Republish behaviour (`restart_on_publish`, `count_only_while_published`, `count_all_time` default) controls interval recalculation after republishing, lazily at evaluation time [PR #15634] (v7.1). It never affects membership or restarts [PR #16183] (v7.1.3). A negative interval executes immediately instead of crashing [PR #15963] (v7.1.0). The UI wording became "activation / reactivation"; keys were kept [PR #17678] (v7.2.2).

### Publish state and the trigger
- Events of an unpublished campaign are not executed. Originally such scheduled logs were failed with "campaign unpublished" [PR #6520] (v2.14.2); since [PR #13995] (v5.2) logs outside the publish-up/down range stay scheduled and run when the campaign is back in range. Why: failed logs were never retried after republishing.
- `mautic:campaigns:trigger` processes campaigns newest first. Why: recent campaigns get processed faster [PR #12922] (v5.1).
- `--campaign-limit` caps Contacts per campaign per run so one campaign cannot starve the others [PR #6753] (v2.15) [PR #9756] (v3.3.2). `--thread-id`/`--max-threads` split Contacts [PR #6211] (v2.14.1), and each thread has its own lock key [PR #11747] (v5.0).
- The trigger finishes the current batch on SIGTERM/SIGINT and exits with status 143 [PR #14745] (v7.0).
- Unpublishing a live campaign asks for confirmation [PR #10705] (v4.2). Saving a campaign warns once per unpublished or out-of-window email; warnings never block saving [PR #8697] (v3.1) [PR #13251] (v5.1).

### Failures, retries and auto-unpublish
- Failed events are retried after `campaign_time_wait_on_event_false` (default `PT1H`). Why: Contacts with no email blocked processing forever [PR #1795] (v2.0). A value of 0 means never retry; only the label changed [PR #8884] (v3.0.2).
- A listener can set its own retry interval with `PendingEvent::fail($log, $reason, $interval)` and close the rest with `passRemainingWithError()` [PR #9524] (v3.3).
- Failures notify the Contact owner, else the campaign creator [PR #3193] (v2.6).
- Auto-unpublish: [PR #13402] (v5.1) described notification above 5 % and unpublish above 10 % failures, and the 5.1.0 code unpublished at `failed_count / members >= 0.1` on every failure. [PR #14470] (v6.0) counts a Contact/event pair only once it reaches 100 failures, once per pair, and decrements after a later success; tag 6.0.0 has `LOOPS_TO_FAIL = 100` and a 0.35 threshold. The minimum of 100 members came with [PR #14906] (v7.0), which also sends exactly one notification and one email. Current rule: 100 failures per Contact/event bump `failed_count`; a campaign with ≥ 100 members is unpublished when `failed_count / members >= 0.35` [code: app/bundles/CampaignBundle/EventListener/CampaignEventSubscriber.php:28-32,106-125 @7.x].
- An event log runs once even under concurrent triggers: it is claimed through an optimistic `version` bump [PR #15348] (v7.0). Decisions and conditions also advance to version 2 [PR #17104] (v7.2.0). The scheduled selector fetches only logs at the initial version; reviewers narrowed the fix to the selector and rejected changing the lock itself [PR #17146] (v7.2.1). Failed, rescheduled logs get their version reset [PR #17245] (v7.3, unreleased).
- Campaign edits use optimistic locking: a stale second save is rejected. Doctrine's built-in versioning was rejected as "too dangerous" [PR #13659] (v5.1).

### Actions with special rules
- "Delete contact" (`lead.deletecontact`) permanently deletes the Contact and allows no event after it; no statistics remain on how often it ran [PR #3413] (v2.7). It still exists in LeadBundle [code: app/bundles/LeadBundle/EventListener/CampaignActionDeleteContactSubscriber.php:29-45 @7.x].
- "Change campaigns" can add to other campaigns and remove from this one in one action [PR #10151] (v4.0.2); later actions in this campaign do not run after the removal [PR #10171] (v5.1). Restarting "this" campaign needs a delay of at least 30 minutes. Why: self-restarting campaigns looped forever [PR #13963] (v5.2).
- Jump to Event avoids duplicating decision trees; pending decisions before a multi-target jump are ignored as an accepted outlier [PR #6215] (v2.14). A deleted or unpublished target fails once instead of looping [PR #7364] (v2.15.2). A jump reached through a parentless decision loops once [PR #11568] (v5.0).
- New Send email actions default to Marketing, not Transactional. Why: from 5.0 transactional sends ignored DNC, so unsubscribed Contacts were emailed [PR #14145] (v5.2). Since 7.2 DNC is bypassed only by the email's `sendToDnc` flag, whatever the type [PR #15995] [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:285 @7.x]. Marketing emails are not re-sent to a Contact who already received them [PR #2153] (v2.1).

### Builder, sources, cloning and deletion
- An event has exactly one parent connection; a new connection replaces the old one [PR #9380] (v3.2.2).
- Campaigns cannot be saved with orphan events [PR #15321] (v7.0); Form-sourced events count as connected [PR #15484] (v7.0).
- Builder state moved from the PHP session into the page. Why: session storage broke when one campaign was open in several tabs [PR #15476] (v7.0).
- Campaign source IDs are numeric end to end. Why: [PR #15598] switched choices to aliases and creating a campaign threw a 500; "A broken filter is nothing compared to broken campaigns" [PR #15987] (v7.1.0).
- Clones copy events with their own parent links and `decision_path` [PR #606] (v1.1.3) [PR #3993] (v2.8.1), keep both Segment and Form sources [PR #7934] (v2.16.1), and work with email open/click decisions [PR #12567] (v5.0). Single events can be copied and pasted across branches and campaigns under normal connection rules [PR #12752] (v5.1).
- Deleting an event soft-deletes it and can redirect scheduled Contacts to an Action or Condition [PR #15528] (v7.1). A redirected decision's target runs once per Contact, logged and paginated [PR #16384] (v7.1.3). The change log stores the redirect event ID [PR #17420] (v7.2.1).
- Event logs are deleted by explicit queries, optionally in the background (`delete_campaign_event_log_in_background`), not by FK cascade. Why: cascades on millions of rows stalled MySQL [PR #10219] (v5.1).
- Deleting a campaign removes events, scheduled actions and execution history but not the Contacts' own activity; the confirmation says so [PR #16846] (v7.2.0).
- A disabled plugin's events no longer stop the builder loading; blocking the plugin disable was proposed but not done [PR #15548] (v7.1).

### Permissions
- Campaigns have own/other permissions. [PR #6240] merged in December 2018 without a data migration, so upgraded roles lost access; it was reverted by [PR #6966] and re-landed by [PR #6963] with migration Version20181204000000, which recalculates the stored bitwise [PR #6963] (v2.15.1: `addExtendedPermissions('campaigns')` is absent at tag 2.15.0 and present at 2.15.1).
- The contacts grids on campaign and email details respect contact view own/other [PR #14315] (v5.2.2).

### Stats, summary and details page
- Stats count all logs including rotations and removed Contacts; a condition's children use the condition's outcomes so totals add up [PR #6907] (v2.15.1). Removed Contacts' pending actions stop showing as pending [PR #14809] (v5.2.5).
- `campaign_use_summary` and `campaign_by_range` are opt-in performance features built by `mautic:campaigns:summarize` [PR #9471] (v4.1). Summary rows each keep their own date window [PR #16969] (v7.2.0).
- Heavy details-page queries load by AJAX [PR #14796] (v7.0), use MySQL generated columns (MariaDB keeps the old queries) [PR #15621] (v7.1), and can be switched off (`campaign_email_stats_enabled`) [PR #14414] (v6.0).
- Write queries use `executeStatement`, never `executeQuery`, which can be routed to the read replica [PR #15199] (v6.0.4).

## 3. Regression catalogue
| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **Membership** | | | |
| Starting action fired twice when added to a list from the profile | Fires once per Contact | [PR #155] | v1.0 |
| Rebuild fails with SQL error when the only source is a Form | Skips with a message | [PR #533] [PR #1286] | v1.1, v1.2.4 |
| Manual removal in one campaign stopped adds to another | Other campaigns unaffected | [PR #1388] | v1.3 |
| Trigger processed about half the Contacts | All pending Contacts processed | [PR #1609] | v1.4 |
| Rebuild loops for a pre-2.14 Contact with logs but no membership | Contact skipped, no loop | [PR #6463] | v2.14.1 |
| Memory exhaustion rebuilding 100k Contacts | Batched fetch | [PR #6507] | v2.14.2 |
| `max_allowed_packet` removing many Contacts | Batched removal | [PR #6973] | v2.15.1 |
| Manually removed Contact cannot be re-added manually | Re-add works | [PR #7020] | v2.15.1 |
| CLI Segment → campaign sync filtered by user permissions | Not filtered | [PR #7606] | v3.3 |
| Segment exit and manual removal flags swapped | Exit sets `date_last_exited` | [PR #8573] | v3.0 |
| Repeatable campaign adds only 300 Contacts per rebuild | All eligible added | [PR #10766] | v4.2 |
| Restartable rebuild loops after manual removal | Terminates | [PR #11318] [PR #15461] | v5.0, v7.0 |
| Parallel kickoff workers overlap and strand Contacts | Ordered, non-overlapping ranges | [PR #14860] | v7.0 |
| Restart off: exited Contacts re-added every cron | Never re-added automatically | [PR #16183] | v7.1.3 |
| Restart on: Contacts re-joining the Segment not re-added | Re-added | [PR #16184] | v7.1.3 |
| **Rotation** | | | |
| Duplicate `campaign_rotation` on trigger | Existing log updated | [PR #4040] | v2.8.1 |
| Duplicate key when a scheduled jump repeats an event | Rotation bumped | [PR #7129] | v3.2.2 |
| One page hit, two campaigns, duplicate key | Rotation per campaign | [PR #9639] | v4.0.2 |
| Immediate jump increments rotation twice | Once | [PR #10206] | v5.1 |
| 500 on second page visit, two campaigns, one with Jump to Event | Rotation per campaign | [PR #14939] | v7.0 |
| **Decisions and inactive path** | | | |
| "No" actions ran for everyone when one Contact acted | Only inactive Contacts | [PR #273] | v1.0.3 |
| "Not opened" ran before the scheduled email was sent | Timer starts at execution | [PR #1311] | v1.2.4 |
| "Not opened" ran though the email was opened | Positive events logged | [PR #1750] | v1.4.1 |
| Root decision took both paths | One path | [PR #1069] | v1.2.2 |
| Landing-page-limited "visits page" never fired | Real channel ID stored | [PR #6322] | v2.14 |
| Redirected or untracked URL did not fire URL decision | Redirect hits match | [PR #6580] | v2.14.2 |
| Decision fired before its parent ran or on the wrong branch | Only when reachable | [PR #6940] | v2.15 |
| Red-path email sent to a removed Contact | Not sent | [PR #7802] | v2.15.3 |
| Red-path child ran before its scheduled parent | Waits | [PR #9486] | v4.0.2 |
| Decision after condition ran both condition paths | Honours the branch | [PR #11200] | v4.4 |
| Real-time decision fired outside publish dates | Publish dates respected | [PR #14303] | v5.2.1 |
| Red-path action delayed by its own hour window | Runs when the wait expires | [PR #14289] | v5.2 |
| Asset-download decision never evaluated after string channel IDs | Compared as strings | [PR #15252] | v7.0 |
| **Conditions** | | | |
| Not-equal never true for NULL | NULL matches | [PR #3180] | v2.6 |
| Date condition off by a day | Local timezone | [PR #3180] | v2.6 |
| Condition after action stalled the campaign | Chain continues | [PR #3180] | v2.6 |
| Condition on red path evaluated when the Contact took the action path | Not evaluated | [PR #5540] | v2.12.2 |
| State field condition cannot be saved | Grouped choices flattened | [PR #10961] | v5.0 |
| Exclude operator on select fields chose the wrong path | Empty/non-matching pass | [PR #14071] | v5.2 |
| 500 switching the operator to including/excluding | Saves | [PR #15469] | v7.0 |
| **Scheduling** | | | |
| Starting actions with different delays fired together | Each honours its delay | [PR #273] | v1.0.3 |
| Unpublished campaign's scheduled log executed | Not executed | [PR #6520] | v2.14.2 |
| 0/1/5-day actions with an hour all scheduled today | N days ahead | [PR #6755] | v2.14.2 |
| Start hour later today scheduled tomorrow; weekday-only ran now | Today; waits for the weekday | [PR #6822] | v2.15 |
| Root "in 1 day" scheduled at +2 days | +1 day | [PR #6886] | v2.15 |
| Reschedule used the UTC hour | Local hour | [PR #7448] | v2.15.2 |
| Days+hour switched to minutes kept the old hour | now + minutes | [PR #8796] | v3.0.1 |
| Email sent on an unselected weekday | Next selected weekday | [PR #8874] [PR #9018] | v3.0, v3.1 |
| Immediate event ignored weekday restriction | Next allowed weekday | [PR #11332] | v5.0 |
| Hourly reschedule loop across DST | Correct time | [PR #11602] | v4.4.4 |
| "Schedule at" with delay ignored the window | Same rules as "between hours" | [PR #13263] | v5.1 |
| Out-of-range scheduled logs failed and never retried | Stay scheduled | [PR #13995] | v5.2 |
| Wednesday 13:00 arrival with Wednesday-from-12:00 rule went to next week | Runs now | [PR #14312] | v5.2.1 |
| Weekend interval tests fail | 0–6 weekday numbering | [PR #14612] | v6.0 |
| 500 saving a "schedule at" event or importing one | Setters accept array dates | [PR #15197] | v7.0 |
| Errors with "System Default" timezone | Resolves to system default/UTC | [PR #15318] | v7.0 |
| `PT-…S` crash with `count_only_while_published` | Executes immediately | [PR #15963] | v7.1.0 |
| Scheduled logs looped forever | Rescheduled to their own date | [PR #16066] | v7.1.3 |
| `DateMalformedStringException` on "04:00" | Time-only values parsed | [PR #16241] | v7.2 |
| Specific-date time drifts by the UTC offset on each save | Wall-clock time kept | [PR #17091] | v7.2.0 |
| Tokyo Contact got the 09:00 weekday email at 18:13 | Send hour in Contact timezone | [PR #17283] | v7.2.1 |
| **Execution and failures** | | | |
| More than 20 Contacts: some never got the action | All processed | [PR #6482] | v2.14.1 |
| Scheduled event with no Contacts executed | Skipped | [PR #6207] | v2.14 |
| Contact deleted mid-run threw | Skipped | [PR #7443] | v2.15.2 |
| Deleted jump target caused endless exceptions | Fails once | [PR #7364] | v2.15.2 |
| Failures never recorded | Recorded | [PR #7783] | v3.0.1 |
| Jump via parentless decision looped the red path each run | Loops once | [PR #11568] | v5.0 |
| Actions after "remove from this campaign" still ran | Not run | [PR #10171] | v5.1 |
| Change campaigns added but did not remove | Both happen | [PR #9418] [PR #10151] | v3.2, v4.0.2 |
| "Multiple non-persisted new entities" after change-membership | Execution continues | [PR #14497] | v5.2.2 |
| One failing Contact unpublished the campaign | ≥ 100 members, per-pair counting | [PR #14470] [PR #14906] | v6.0, v7.0 |
| One unpublish notification per Contact | Exactly one | [PR #14906] | v7.0 |
| Concurrent triggers executed one log twice | Executed once | [PR #15348] | v7.0 |
| `--scheduled-only` loops on a log at version 2 | Only initial-version logs fetched | [PR #17146] | v7.2.1 |
| resume-stuck followed the Yes path for a half-run condition | Condition re-evaluated | [PR #17104] | v7.2.0 |
| Deleted decision with redirect re-sent email forever | Target runs once | [PR #16384] | v7.1.3 |
| Second trigger thread refused by the lock | Threads run concurrently | [PR #11747] | v5.0 |
| `--campaign-limit` aborted the run | Limits Contacts | [PR #9756] | v3.3.2 |
| Commands exit 0 for an unknown campaign ID | Non-zero exit | [PR #11963] [PR #12203] | v4.4.8, v5.0 |
| Writes routed to the read replica | `executeStatement` on the primary | [PR #15199] | v6.0.4 |
| **Builder, clone, delete** | | | |
| Clone linked to the original's event parents | Own event tree | [PR #606] | v1.1.3 |
| Numeric temp IDs overwrote another campaign | No collision | [PR #1852] | v2.0 |
| `decision_path` wiped on save without opening the builder | Kept | [PR #3993] | v2.8.1 |
| Clone with a Form source → duplicate `campaign_form_xref` | Saves | [PR #7642] | v2.15.3 |
| Editing one source type removed the other in a clone | Both kept | [PR #7934] | v2.16.1 |
| Builder allowed several parents | One parent | [PR #9380] | v3.2.2 |
| Fast Apply lost new event placement | Buttons wait for the request | [PR #13533] | v5.1 |
| Concurrent edits silently overwrote each other | Second save rejected | [PR #13659] | v5.1 |
| Any decision failed with "extra fields" | Decision forms lack `triggerWindow` | [PR #14325] | v5.2.1 |
| Form-sourced campaigns flagged as orphaned | Only true orphans fail | [PR #15484] | v7.0 |
| Builder did not load with a disabled plugin | Loads with a warning | [PR #15548] | v7.1 |
| API PUT deleting events returned 500 | Works | [PR #15614] | v7.1 |
| Green → red switch deleted the new connection | Kept | [PR #15777] | v7.0.0 |
| Creating a campaign threw 500 (alias as ID) | Numeric IDs | [PR #15987] | v7.1.0 |
| Builder stuck under the overlay after a failed update | Controls restored | [PR #16874] | v7.2.0 |
| Deleting an event with ~500k logs never finished | Batched deletion | [PR #7747] | v3.2 |
| **Stats, API, UI** | | | |
| Progress above 100 % after removals | Current members only | [PR #3039] | v2.4 |
| Graph total differs from event stats | Totals add up | [PR #6907] | v2.15.1 |
| Removed Contact's executed actions shown as pending | Pending dropped | [PR #14809] | v5.2.5 |
| Jump-loop campaigns over- or under-count | True counts | [PR #14837] | v7.0 |
| `campaign_summary` written for the wrong hour, repeatedly | Own window; buffer cleared | [PR #16969] | v7.2.0 |
| API `start`/`limit` ignored on campaign Contacts | Honoured | [PR #5292] | v2.12 |
| API edit-contact-event 500 without trigger date | Validation errors | [PR #10708] | v4.2 |
| API rejected the `publishUp` it returned | ISO 8601 round trip | [PR #16264] | v7.2 |
| Cancelling a scheduled event on a restarted campaign picked an old log | Latest log used | [PR #11636] [PR #11882] | v4.4.6, v5.0 |
| Contact grid on details pages ignored contact permissions | Respected | [PR #14315] | v5.2.2 |
| Upcoming events widget took 45 s | Future events only | [PR #15024] [PR #16101] | v7.0, v7.2 |

## 4. Feature timeline
| Version | Change | PR |
|---|---|---|
| 1.0–1.4 | CLI membership rebuild; Form sources; conditions; overlap guard with `--force` | [PR #337] [PR #515] [PR #906] [PR #1139] |
| 2.0–2.3 | Failed-event retry wait; builder anchors and connection restrictions; Marketing vs Transactional; PID/lock-file guard | [PR #1795] [PR #2153] [PR #2998] |
| 2.6–2.8 | Failure notifications; event API, timeline reschedule/cancel; contacts API; Delete contact action; failed-log table | [PR #3193] [PR #3219] [PR #3292] [PR #3413] [PR #4010] |
| 2.11–2.13 | Preview tab | [PR #4912] |
| 2.14 | Executioner refactor and batches; restart and rotation; Jump to Event; hour/weekday/timezone scheduling | [PR #5942] [PR #6132] [PR #6215] [PR #6520] |
| 2.15 | Own/other permissions; chained actions; clone API; read replicas; `--campaign-limit` | [PR #6963] [PR #6187] [PR #6125] [PR #5970] [PR #6753] |
| 3.0–3.3 | M3 removals; unpublished-email warning; custom failure retry interval | [PR #8374] [PR #8697] [PR #9524] |
| 4.1–4.4 | Summary statistics; unpublish confirmation | [PR #9471] [PR #10705] |
| 5.0 | Segment rebuild decoupled; Redis lock; weekday for all units; Twig views | [PR #10550] [PR #10347] [PR #11332] [PR #11778] |
| 5.1 | Query-based log deletion; event copy/paste; newest-first trigger; `--exclude`; failure auto-unpublish; optimistic edit lock; map stats | [PR #10219] [PR #12752] [PR #12922] [PR #13383] [PR #13402] [PR #13659] [PR #12570] |
| 5.2 | Optimized scheduling; Change campaigns 30-minute minimum; Marketing default; builder redesign; preview stats | [PR #13569] [PR #13963] [PR #14145] [PR #13771] [PR #14108] |
| 6.0 | Symfony 6.4; per-pair failure counting; Email Metrics tab; timeline parent info | [PR #13962] [PR #14470] [PR #14414] [PR #14601] |
| 7.0 | Import/export; orphan validation; log optimistic lock; audit tab; signal handling; anonymous-contact cleanup; string channel IDs; `date_queued` | [PR #14504] [PR #15321] [PR #15348] [PR #14676] [PR #14745] [PR #15198] [PR #15132] [PR #15510] |
| 7.1 | Redirect on event delete; republish behaviour; auto-align; `withContactCounts`; scheduling labels in preview; per-event graph stats | [PR #15528] [PR #15634] [PR #15820] [PR #15878] [PR #15880] [PR #14996] |
| 7.2 | `mautic:campaigns:resume-stuck` and `--dry-run`; event IDs in builder; infinite canvas; stats cache TTL; Marketplace campaign resources; final classes | [PR #15310] [PR #17104] [PR #16103] [PR #16127] [PR #16110] [PR #15904] [PR #16896] |
| 8.0 | Doctrine ORM 3 / DBAL 4 | [PR #17361] |

## 5. Removed, deprecated, replaced
| What | Replaced by | PR | Version |
|---|---|---|---|
| Membership built on UI save | Batched CLI rebuild | [PR #337] | v1.0.4 |
| Email selector on "Opens email" | Connect to a Send email action | [PR #439] | v1.1 |
| Campaign callback functions, `MauticFactory` | Listeners and DI; factory removed in 6.0 | [PR #1833] [PR #14682] | v2.0, v6.0 |
| Old `/contact/add/{id}` API URLs | `/contact/{id}/add` | [PR #3219] | v2.6 |
| `CampaignModel::addLead/removeLead…` | `MembershipManager` | [PR #6132] | v2.14 |
| Deprecated legacy event methods | Executioner APIs (UPGRADE-3.0.md) | [PR #8374] | v3.0 |
| Campaign sync in `mautic:segments:update` | `mautic:campaigns:update` only | [PR #10550] | v5.0 |
| FK cascade deletion of logs | Explicit deletion | [PR #10219] | v5.1 |
| PHP views | Twig | [PR #11778] | v5.0 |
| `Service\Campaign` | `CampaignAuditService` | [PR #13251] | v5.1 (removed 6.0) |
| Failing out-of-range scheduled logs | Logs stay scheduled | [PR #13995] | v5.2 |
| Transactional default email type | Marketing | [PR #14145] | v5.2 |
| Integer `channel_id` | VARCHAR(64) | [PR #15132] | v7.0 |
| Builder state in the session | Page element | [PR #15476] | v7.0 |
| Hard delete of events | Soft delete with `redirect_event_id` | [PR #15528] | v7.1 |
| `CampaignRepository::fetchEmailIdsById()` | `EventRepository::getCampaignEmailEvents()` (removal 8.x) | [PR #15753] | v7.1 |
| Extensible subscribers, events, exceptions, executioners | `final` classes | [PR #16735] [PR #16753] [PR #16755] [PR #16896] | v7.2 |
| `getModel()` lookups in campaign controllers | Constructor injection | [PR #16643] [PR #16645] | v7.2 |
| "Publish/republish" wording | "Activate/reactivate/deactivate" (keys kept) | [PR #17678] | v7.2.2 |

## 6. Maintainer norms for this area
- Long-running membership and execution work belongs in batched CLI commands, never in a web request [PR #337] [PR #273].
- Behaviour that changes existing campaigns must be opt-in per campaign [PR #6132].
- Permission changes need a data migration that updates the stored bitwise; a feature that breaks existing roles is reverted rather than holding a release [PR #6963] [PR #6966].
- Campaign fixes need functional tests: "we always be in the state where we fix one use case and break another" [PR #11568] [PR #11318]. Drive the real `mautic:campaigns:trigger` command where possible [PR #16066].
- Do not fix a symptom by loosening validation [PR #14325]. Do not change code "solely based on a theory" [PR #7802]. Keep fixes minimal [PR #17146].
- Do not force MySQL indexes through DBAL; reshape the query [PR #7901]. Bind integers and arrays as typed parameters [PR #7838] [PR #16138]. Use `executeStatement` for writes [PR #15199].
- Heavy queries on `campaign_lead_event_log`, `email_stats` or `page_hits` need large-dataset benchmarks and ideally AJAX loading or a switch [PR #14414] [PR #15024] [PR #17175].
- Bug fixes target the patch branch, features the next minor, BC breaks the next major [PR #12922] [PR #16969] [PR #17146].
- Features ship with user documentation [PR #12752] [PR #13383] [PR #15310].
- The API Library test suite is the REST regression suite [PR #10708] [PR #15614] [PR #16264].
- Translation keys are kept when wording changes [PR #1643] [PR #17678].

## 7. Open questions
- Conflict, behaviour.md wins: [PR #15476] says two tabs on one campaign now work with "last save wins", but [PR #13659] rejects stale saves and behaviour.md B78 says `campaigns.version` guards edits [PR #15476] [PR #13659].
- Conflict, behaviour.md wins: [PR #7704] excluded only active memberships from re-adding; behaviour.md B5 also excludes manually removed members with no exit date, matching [PR #11318] [PR #7704].
- Conflict, behaviour.md wins: [PR #14289] says red-path actions ignore their own interval; behaviour.md B57 says the earliest no-child runs now and later ones keep their relative dates. Check how a second red-path action is timed [PR #14289].
- Chunk notes credit the 100-member minimum to [PR #14470]; the 7.x history shows `MINIMUM_CONTACTS_FOR_DISABLE` arriving with [PR #14906] [code: app/bundles/CampaignBundle/EventListener/CampaignEventSubscriber.php:30 @7.x].
- Email type default: new events default to Marketing in the form, but an event saved without `email_type` is sent as Transactional [PR #14145] [code: app/bundles/EmailBundle/Form/Type/EmailSendType.php:68 @7.x] [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:274 @7.x].
- Every reschedule path must reset `version` to the initial value, or [PR #17146]'s selector ignores the log; [PR #17245] covers failed logs only on 7.x (7.3) [PR #17245].
- Is `campaign_use_summary` summarisation working at all? A tester saw no rows on 6.x either [PR #14776].
- Is redirect-on-delete honoured when events are deleted by API PUT [PR #15614]?
- Optimized scheduling: confirm the 5-interaction minimum and how `max_optimal_days` applies [PR #13569].
- When should `mautic:campaigns:resume-stuck` run, and does it execute a replaced middle event [PR #15310]?
- `checkLeadInCampaigns` was deliberately left without the removed-membership filter [PR #7802].
- `--campaign-limit` with relative-time Marketing Messages (issue #9769) is unresolved [PR #9756].
- A campaign with events from a disabled plugin still fails at run time; expected behaviour is undefined [PR #15548].
- [PR #4535], [PR #8572], [PR #14583] and [PR #16115] have no usable description.

## 8. Coverage
- 429 PRs read across 6 chunks (104, 77, 85, 60, 59, 44) [PR #337] [PR #17678].
- About 326 substantive; the rest are branch merges, test-only or style changes, kept only for norms [PR #11268] [PR #16466].
- 869 noise PRs were excluded upstream before chunking [unverified].
- Chunk file names carried wrong date ranges; every item here is dated by merge date and release [unverified].
