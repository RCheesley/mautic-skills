# Campaigns — docs digest

Sources: user docs 7.2 (8.0 copies identical) and dev docs 7.2 / 8.0.
- OV https://docs.mautic.org/en/7.2/campaigns/campaigns_overview.html
- CR https://docs.mautic.org/en/7.2/campaigns/creating_campaigns.html
- CB https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html
- MG https://docs.mautic.org/en/7.2/campaigns/managing_campaigns.html
- EX https://docs.mautic.org/en/7.2/campaigns/exporting_campaigns.html
- IM https://docs.mautic.org/en/7.2/campaigns/importing_campaigns.html
- TS https://docs.mautic.org/en/7.2/campaigns/troubleshooting_campaigns.html
- DEV https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html ; DEV8 https://devdocs.mautic.org/en/8.0/plugin_extensions/campaigns.html
- API https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html (carries a "legacy page, potentially inaccurate" banner)

## Concepts
- Campaign types: time driven, Contact driven, mixed [docs: https://docs.mautic.org/en/7.2/campaigns/campaigns_overview.html#campaign-types].
- Sources: Segments (public only) and Forms, or both [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#getting-started-with-campaign-builder].
- Event types: Decision ("Branch flow based on contact behavior"), Action ("Automatically execute tasks when triggered"), Condition ("Filter by known profile field values or submitted form data") [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#getting-started-with-campaign-builder].
- Green path = Contact acted (runs at action time); red path = non-action, timed by the following action's delay [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#green-paths] [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#red-paths].

## Campaign properties
- Name, description, Category, "Allow Contacts to restart the Campaign", Campaign Reactivation (Republish) Behavior, Active toggle with optional scheduled (de)activation [docs: https://docs.mautic.org/en/7.2/campaigns/creating_campaigns.html#create-your-first-campaign].
- Restart disabled: exited Contacts cannot restart even if they re-qualify [docs: https://docs.mautic.org/en/7.2/campaigns/creating_campaigns.html#create-your-first-campaign].

## Actions (user docs list)
Add/Remove Do Not Contact, Add to Company's score, Add Company, Adjust Contact Points, Change Campaigns, Change Contact's Stage, Delete Contact (terminal), Jump to Event, Modify Contact's Segments, Modify Contact's tags, Push Contact to Integration, Send a Webhook, Send Email (Repeatable email toggle), Send Email to User, Send Marketing Message, Update Contact, Update Contact's primary Company, Update Contact owner [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#actions].

## Decisions
Device visit, Downloads Asset, Request Dynamic Content, Submits Form, Visits a page; Opens/Clicks/Replies to Email only after a Send Email action [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#decisions].

## Conditions
Contact Campaigns, Contact device, Contact field value, Contact owner, Contact Segments, Contact Tags, Contact Points, Form Field value, Has active notification, Has valid Email address (syntax only), Prevent action after date [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#conditions]. Prevent action after date: Time Stamp = Campaign Start Date, operator less/greater than, interval in minutes–years [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#prevent-action-after-date-condition]. Code uses publish-up, or date added when no publish-up [code: app/bundles/LeadBundle/EventListener/CampaignSubscriber.php:718-760 @7.x].

## Scheduling
- Event timing options: immediately / relative time period / specific date-time / optimal for Contact; "Send from or between the hours of"; "Schedule only on selected days" (incl. Weekdays) — screenshot only [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#notes-on-campaign-actions].
- Condition delay is respected before a connected action's delay [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#notes-on-delayed-conditions-and-dates].
- Smart schedule: within 24 hours or within 7 days; for Send Email, Marketing Message, Push to Integration, Webhook [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#smart-event-schedule].

## Cron
- `mautic:campaigns:update` adds/removes Contacts in batch [docs: https://docs.mautic.org/en/7.2/campaigns/creating_campaigns.html#add-or-remove-contacts-in-batch].
- `mautic:campaigns:trigger` runs events; `--campaign-id=ID`, `--exclude=ID` (repeatable) [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#triggering-campaign-events]. Frequency is not stated on these pages (see mautic-cron-and-queues).

## Reactivation (republish) behaviour
- Applies only to relative delays; global in Configuration > Campaign Settings, per campaign override [docs: https://docs.mautic.org/en/7.2/campaigns/managing_campaigns.html#configuring-reactivation-behaviour].
- Examples: count regardless (1 Jan + 10 d → 11 Jan); restart (reactivated 7 Jan → 17 Jan); only while active (4 days used, reactivated 10 Jan → 16 Jan) [docs: https://docs.mautic.org/en/7.2/campaigns/managing_campaigns.html#campaign-reactivation-behavior].
- Recalculation happens when cron evaluates the log [docs: https://docs.mautic.org/en/7.2/campaigns/managing_campaigns.html#activate-and-deactivate-campaigns].
- "Last Publish Date" on the detail page is the reference for restart [docs: https://docs.mautic.org/en/7.2/campaigns/managing_campaigns.html#viewing-last-activation-date].

## Procedures
- Create: Campaigns > New; properties; Launch Campaign Builder; add sources and ≥1 event; Save & Close [docs: https://docs.mautic.org/en/7.2/campaigns/creating_campaigns.html#create-your-first-campaign].
- Copy an event (5.1+): hover copy icon, click target anchor, click the cloned tile [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#cloning-campaign-events].
- Delete an event: dialog redirects scheduled Contacts to another event [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html#identifying-campaign-events].
- Delete campaigns: permanent; events, scheduled actions, history gone; Contact activity kept [docs: https://docs.mautic.org/en/7.2/campaigns/managing_campaigns.html#deleting-a-campaign].
- Export UI: Export → Share screen → Download ZIP or Publish to Marketplace; CLI `mautic:entity:export`; API GET `/api/campaigns/export/{id}` [docs: https://docs.mautic.org/en/7.2/campaigns/exporting_campaigns.html#using-mautic-instance].
- Import UI: Campaigns > Options > Import > ZIP > Update or Create new per entity > Proceed; imported campaign is inactive; CLI `mautic:entity:import --entity=campaign --file= --user=`; API POST `/api/campaigns/import` [docs: https://docs.mautic.org/en/7.2/campaigns/importing_campaigns.html#using-mautic-instance].
- Troubleshoot Visits a page: test logged out, confirm membership in timeline, decisions fire once, check substring/wildcard URL [docs: https://docs.mautic.org/en/7.2/campaigns/troubleshooting_campaigns.html#page-visits-aren-t-recognized].

## Developer contract
- Subscribe to `CampaignEvents::CAMPAIGN_ON_BUILD` (7.2) / `CampaignBuilderEvent::class` (8.0) [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#registering-campaign-events] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/campaigns.html#registering-campaign-events].
- Action: required `label`, `batchEventName`; Condition/Decision: `label`, `eventName`; optional `description`, `formType`, `formTypeOptions`, `formTypeCleanMasks`, `formTypeTheme`, `connectionRestrictions`, `timelineTemplate` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#campaign-action-definition].
- `connectionRestrictions.anchor` lists disallowed anchors like `decision.no`; `source`/`target` list allowed keys per type [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#campaign-action-definition].
- `PendingEvent` methods: `checkContext`, `fail`, `failAll`, `failLogs`, `failRemaining`, `findLogByContactId`, `getConfig`, `getContactIds`, `getContacts`, `getContactsKeyedById`, `getEvent`, `pass`, `passAll`, `passAllWithError`, `passLogs`, `passRemaining`, `passRemainingWithError`, `passWithError`, `setChannel` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#executing-a-campaign-action].
- Conditions: `ConditionEvent::pass()/fail()`; Decisions: `RealTimeExecutioner::execute()` then `DecisionEvent::setAsApplicable()`, `getPassthrough()` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#evaluating-a-campaign-decision].

## REST API (dev docs)
Endpoints C1–C11 (get, list with `published`/`withContactCounts`, contacts, new, clone, edit, delete, export, import, add/remove contact); counts cached 12 h [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html#list-campaigns]. Event payload schema for create/edit is not documented ("see the unit tests") [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html#create-campaign].

## Terminology
"Contact" not "Lead"; "Segment" not "list"; Actions, Decisions, Conditions; green/red paths in user docs vs `yes`/`no` anchors in dev docs; UI says "Republish" while user docs say "Reactivation"/"activation" [code: app/bundles/CampaignBundle/Translations/en_US/messages.ini:194-199 @7.x] [docs: https://docs.mautic.org/en/7.2/campaigns/managing_campaigns.html#configuring-reactivation-behaviour].

## Known doc errors
- Dev docs: export via POST (route is GET) [code: app/bundles/CampaignBundle/Config/config.php:131-135 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#exporting-via-api].
- Dev docs: "Exporting via command line" shows the import command [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#exporting-via-command-line].
- Dev docs 7.2: decision example calls `addCondition()`; namespace written `Mautic\CampaignBundle\Events` (actual `Event`) [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#registering-a-campaign-decision].
- User docs Python import example has a stray `}` [docs: https://docs.mautic.org/en/7.2/campaigns/importing_campaigns.html#using-mautic-api].
- Import content type: user docs `multipart/form-data`, dev docs `application/zip` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/campaigns.html#importing-via-api].

## Gaps in the docs
Trigger options beyond `--campaign-id`/`--exclude`, restart mechanics (rotations), Jump to Event loops, inactive-path timing, timezone basis of delays, failure/retry counts, permissions [docs: https://docs.mautic.org/en/7.2/campaigns/campaign_builder.html]. The code behaviour for each is in `behaviour.md`.
