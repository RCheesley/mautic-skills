# Points and stages - docs digest

These sources are summarised here; the claims below are what the docs say. Where code disagrees, behaviour.md wins. Divergences are listed at the end.

Sources:
- User docs: https://docs.mautic.org/en/7.2/points/points.html, https://docs.mautic.org/en/7.2/points/point_groups.html, https://docs.mautic.org/en/7.2/points/point_insights.html, https://docs.mautic.org/en/7.2/points/points_troubleshooting.html, https://docs.mautic.org/en/7.2/stages/stages.html and the points-trigger part of https://docs.mautic.org/en/7.2/segments/manage_segments.html. The 8.0 versions of these pages are identical.
- Developer docs: https://devdocs.mautic.org/en/7.2/plugin_extensions/points.html (changed in 8.0) and the REST pages https://devdocs.mautic.org/en/7.2/rest_api/point_groups.html, point_insights.html and stages.html. The point_actions.html and point_triggers.html pages are stubs.
- KB: https://kb.mautic.org/article/lead-scoring-best-practices-with-mautic.html and https://kb.mautic.org/article/working-with-stages-in-mautic.html.

## 1. Points (user docs)

Point Actions:
- Points weigh Contacts. Points have actions and triggers [docs: https://docs.mautic.org/en/7.2/points/points.html].
- A Point Action changes a Contact's total, up or down, when the Contact does the chosen action. Create one at **Points > Manage Actions > New** [docs: https://docs.mautic.org/en/7.2/points/points.html#point-actions].
- Action fields [docs: https://docs.mautic.org/en/7.2/points/points.html#point-actions]:
  - **Change Points (+/-)**: no `+` needed; use `-` to subtract.
  - **Action taken by Contact**.
  - **Point Group**: empty means the overall total.
  - **Category**: organisation only.
  - **Active** and **Activate/Deactivate at**: define the period in which points are awarded.
  - **Is repeatable**: Yes awards every time; No (default) awards only the first time.

Point Triggers:
- Point Triggers fire events once a Contact reaches a total. Create one at **Points > Manage Triggers > New**. Trigger fields [docs: https://docs.mautic.org/en/7.2/points/points.html#point-triggers]:
  - **Minimum number of Points**.
  - **Contact color**.
  - **Trigger for existing applicable Contacts upon saving**.
  - One or more events on the **Events** tab.
- Trigger events:
  - Campaign: **Modify Contact's Campaigns** [docs: https://docs.mautic.org/en/7.2/points/points.html#campaign-triggers].
  - Contact: **Modify Contact's Segments**, **Modify Contact's tags** (it can create new tags) and **Change contact's stage** (or **Remove existing stage**). The stage event only moves forward by weight. It does nothing when the Contact is already in the stage, and it records a "Stage changed" timeline entry [docs: https://docs.mautic.org/en/7.2/points/points.html#contact-triggers].
  - Add-on: **Push Contact to Integration**. It needs the integration's "Triggered action push Contacts to Integration" option and is not supported with Salesforce [docs: https://docs.mautic.org/en/7.2/points/points.html#add-on-triggers].
  - Email: **Send an Email** (a template email) and **Send an Email to User** (User and/or owner; to, cc and bcc are comma-separated; one email when the owner is missing or is the selected User) [docs: https://docs.mautic.org/en/7.2/points/points.html#email-triggers].
- "Trigger for existing": No (default) affects only Contacts who reach the threshold later; Yes affects all existing Contacts at or above it. A trigger with **Modify Contact's Segments** works like a dynamic segment on Points ≥ the minimum, except that it can be limited to Contacts who reach the value after the trigger is created [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#points-trigger].

## 2. Point Groups and Insights

Point Groups:
- Point Groups split a Contact's score into separate groups. Manage them at Points > **Manage Groups**; the fields are Name and Description [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#managing-point-groups].
- Groups can be used by Point Actions, Point Triggers, a campaign condition, a campaign action, the form action "Adjust Contact's Points", a segment filter per group, contact details and a Group Report [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#using-point-actions].
- Changing group points does not fire the "Contact Points Changed" webhook [docs: https://docs.mautic.org/en/7.2/points/point_groups.html#webhooks].

Point Insights:
- Manage them at **Points > Point Insights**. Access is controlled by a separate **Insights** permission [docs: https://docs.mautic.org/en/7.2/points/point_insights.html#managing-point-insights].
- Fields: Name, Description, Point Groups to Compare, Custom Field (published text fields only), Category and Active. Only active insights run [docs: https://docs.mautic.org/en/7.2/points/point_insights.html#creating-a-point-insight].
- Insights re-evaluate automatically when a compared group changes. The winner is written as `ID (Name)`, for example `12 (Umbrellas)`. When every score is zero, nothing is written. On a tie the lower id wins, but an existing value is kept [docs: https://docs.mautic.org/en/7.2/points/point_insights.html#how-point-insights-work].

## 3. Troubleshooting

- Activity from Mautic Administrators is ignored, so test logged out, in incognito or in another browser [docs: https://docs.mautic.org/en/7.2/points/points_troubleshooting.html#page-visits-not-recognized].
- Page-visit actions count once per Contact.
- A URL matches when the configured text is part of the visited URL. Matching is case-insensitive, and `*` wildcards work. For example, `https://example.com` matches `https://example.com/index.php?foo=bar` [docs: https://docs.mautic.org/en/7.2/points/points_troubleshooting.html#page-visits-not-recognized].

## 4. Stages

- Create a stage at **Stages > +New**. Fields: Name, Description, **Weight**, Category and activation dates [docs: https://docs.mautic.org/en/7.2/stages/stages.html#creating-stages].
- A higher weight is further along, and Contacts cannot move back. Weights must be unique; the form shows a table of existing weights. An inactive stage does not appear in segment filters, campaign conditions or the widget [docs: https://docs.mautic.org/en/7.2/stages/stages.html#creating-stages].
- Contacts move by the campaign action **Change Contact's Stage** or the trigger event. A Contact is in one stage at a time. Weights are unique across all funnels [docs: https://docs.mautic.org/en/7.2/stages/stages.html#moving-contacts-between-stages].
- **Merge Stage** (Options menu, needs edit and delete) moves Contacts and stage history into the target, then deletes the merged stage. This cannot be undone. The success message is "Stage 'name' was successfully merged into 'target'" [docs: https://docs.mautic.org/en/7.2/stages/stages.html#merging-stages].
- Dashboard widgets: **Stages in time** and **Lifecycle** (Contacts per stage within segments) [docs: https://docs.mautic.org/en/7.2/stages/stages.html#lifecycle].

## 5. REST API (devdocs)

Point Groups (library key `pointGroups`):
- `GET /points/groups/ID` and `GET /points/groups`.
- `POST /points/groups/new` (name required).
- `PATCH /points/groups/ID/edit`.
- `DELETE /points/groups/ID/delete`.
- The page carries an "outdated" note [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/point_groups.html].

Point Insights (Mautic 7+):
- The API library does not support them. They need the `point:insights` permission.
- `GET /points/insights/ID` returns `insight`. The list returns only id, name, category and description.
- `POST /points/insights/new`: `insightType` defaults to `compare_point_groups` and `insightAction` to `set_custom_field`.
- `customField` and `pointGroups` are not validated.
- PUT creates the insight when it is missing; PATCH returns 404 when it is missing.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/point_insights.html]

Stages (library key `stages`):
- `GET /stages/ID` and `GET /stages`.
- `POST /stages/new` (name required).
- A duplicate weight gives 400 `weight: Another stage with this weight already exists.`
- PUT and PATCH edit; `DELETE /stages/ID/delete`.
- `POST /stages/ID/contact/CID/add` and `.../remove` return `{"success":1}`.
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stages.html]

Point Actions and Point Triggers: the pages are stubs, so use code-map.md section 6 [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/point_actions.html] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/point_triggers.html].

`/api/stats` tables include `lead_points_change_log`, `lead_stages_change_log`, `point_lead_action_log`, `point_lead_event_log` and `stage_lead_action_log` [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/stats.html#get-stat-tables].

## 6. Plugin extension (devdocs)

7.2:
- Subscribe to `PointEvents::POINT_ON_BUILD` and call `PointBuilderEvent::addAction($key, $def)`. The definition keys are `label` (required), `formType`, `formTypeOptions`, `formTypeCleanMasks`, `formTypeTheme`, `template` and `callback`.
- Fire the action with `triggerAction($key, $details)`, or pass a Contact as the fourth argument.
- Trigger events use `TRIGGER_ON_BUILD` and `addEvent()`.
[devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/points.html#point-actions]

8.0: subscribe on `PointBuilderEvent::class` and `TriggerBuilderEvent::class`. The old constants receive nothing. `TRIGGER_POST_SAVE` and the other CRUD events are still dispatched by string [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/points.html].

## 7. KB guidance

Lead scoring (strategy guide, version-agnostic) [kb: https://kb.mautic.org/article/lead-scoring-best-practices-with-mautic.html]:
- Give low-value actions less than 10% of the threshold and high-value actions 20-100%.
- Use negative points for careers or investor pages and for unsubscribes.
- Use a suppression segment plus a reset campaign.
- Use decay of −10 every 7 days.
- Cap the score at 70.
- Start with an MQL threshold of 50-100.
- Score video views by matching "phantom" GTM page URLs.

Stages [kb: https://kb.mautic.org/article/working-with-stages-in-mautic.html]: stages have a name, description and weight. Movement is one direction only, and the campaign action moves Contacts.

## 8. Terminology

- Write Points, Point Actions, Point Triggers, Point Groups, Point Insights, Stages and Contacts as capitalised product nouns [docs: https://docs.mautic.org/en/7.2/points/points.html].
- The trigger event label is **Change contact's stage** (lower case) and the campaign action label is **Change Contact's Stage** [docs: https://docs.mautic.org/en/7.2/stages/stages.html#moving-contacts-between-stages].

## 9. Where docs and code diverge

| Docs say | Code (7.2.1) | Source |
|---|---|---|
| Administrators are ignored | Every logged-in user is ignored, except for `email.send` | behaviour item 3 |
| Page visits count once per Contact | Only for non-repeatable actions | item 7 |
| "Contact color" highlights Contacts | Never applied; `setTriggerModel()` has no caller | item 39 |
| Contacts cannot move to a lower stage | Enforced only by the campaign action and the trigger event | item 49 |
| Same stage: "nothing changes" | The event is marked failed and retried at every evaluation | item 34 |
| Modify Contact's Campaigns and Push Contact to Integration work | Both look broken (missing or non-injectable callbacks) | code-map section 4 |
| Trigger callback `($config, $lead, MauticFactory $factory)` | Only `event`, `lead` and `config` are injected | item 31 |
| KB: campaigns reset scores to 0 or cap them | The campaign "Adjust contact points" action is delta-only and rejects 0 | item 24 |
| Point Groups edit: PATCH only | `standard_entity` route; PUT is presumably also available (unverified) | code-map section 6 |
