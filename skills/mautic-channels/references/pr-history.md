# Channels: PR history

## Contents
1. [How to read this file](#1-how-to-read-this-file)
2. [Decisions that shaped current behaviour](#2-decisions-that-shaped-current-behaviour)
3. [Regression catalogue](#3-regression-catalogue)
4. [Feature timeline](#4-feature-timeline)
5. [Removed, deprecated, replaced](#5-removed-deprecated-replaced)
6. [Maintainer norms for this area](#6-maintainer-norms-for-this-area)
7. [Open questions](#7-open-questions)
8. [Coverage](#8-coverage)

## 1. How to read this file
Source: merged pull requests on github.com/mautic/mautic, harvested 2026-10-15. The version is inferred from the base
branch, milestone and merge date; "unreleased 7.x" means merged to `7.x` after 7.2.1 (milestone 7.3.0-rc), and "8.0 only"
means merged to `8.x`. Current behaviour is in references/behaviour.md; this file explains why and when it came about.

## 2. Decisions that shaped current behaviour

### 2.1 Channel framework and Marketing Messages
- Marketing Messages have a detail page with a graph and the Contacts sent to [PR #3367] (v2.6). The API returns `channelName` per channel [PR #3511] (v2.7.0). At first the Twitter channel returned null `channelId`/`channelName` because tweets were stored as parameters; the Tweet entity replaced that [PR #3748] (v2.8.0).
- Editing a Marketing Message's channels persists the change [PR #3634] (v2.7.1). The API casts each channel's `isEnabled` to int so JSON payloads work [PR #8727] (v3.0.0).
- Marketing Message categories are stored with bundle `messages`, not `0`; a migration converted old rows [PR #8462] (v3.0.1).
- Message and Category setters record changes, so edits produce audit-log entries [PR #11275] (v5.0).
- Channel detail pages (asset, campaign, Marketing Message, DWC, email, form, segment, page, SMS, focus, social monitoring, notification) have a custom-content hook below the graphs for plugin stats [PR #6016] (v2.14.0) [PR #6344] (v2.14.1).
- Contact list batch actions include Channel subscription (DNC plus frequency rules); the public preference centre pre-selects the Contact's current channel preferences [PR #5962] (v2.15.0). It was held back from 2.14.2 because it was a 2k-line feature.
- The contact list and detail view show DNC per channel, not only for email [PR #7879] (v3.2.0).
- Event constant names must be unique across bundles. `NotificationEvents::ON_CAMPAIGN_TRIGGER_ACTION` once shared the Email event's name, so email sends were handled by the notification listener and logged as "not subscribed"; a migration repaired the logs [PR #2152] (v2.1.0).
- Deprecated ChannelBundle APIs were removed in 3.0 (`MessageQueueModel::dispatchDeprecatedEvent`, `ChannelEvents::ON_CAMPAIGN_TRIGGER_ACTION`, `LeadBundle\Event\ChannelEvent`) [PR #8059] (v3.0.0).
- When a missing or uninitialised OneSignal integration is listed as a channel, it is skipped instead of causing a fatal error [PR #8793] (v3.0.0).
- A Marketing Message with several channels sent from a campaign logs its per-channel events correctly [PR #14583] (v6.0.0). The PR has no description; behaviour is inferred from its test steps.
- Marketing Message delete and view work after the controller and Symfony 6 refactors [PR #12773] (v5.0.0) [PR #14489] (v6.0.0).
- When a Marketing Message or a campaign "Send Marketing Message" action selects an email, a read-only indicator shows whether that email sends to unsubscribed (DNC) Contacts [PR #17388] (unreleased 7.x). Why: users could not see that a message would bypass unsubscribes.

### 2.2 Frequency rules and the message queue
- A send blocked by a frequency rule is queued for the next period, not N periods ahead [PR #4761] (v2.10.0). The frequency number had been used as the multiplier, so a 4th email under "3 per week" waited 3 weeks. behaviour.md Q3–Q4 describes the current "now + one whole period".
- Queued SMS use the SMS channel's own frequency defaults, not the email ones [PR #4761] (v2.10.0).
- A queued message whose email or SMS is now unpublished is not sent; it is rescheduled as failed until max attempts, "just in case the unpublished state is temporary" [PR #4761] (v2.10.0).
- Rescheduling uses a real `\DateInterval`. The old custom format read "15M" as 15 months, so a failed queued message waited months instead of 15 minutes; `addToQueue` and `rescheduleMessage` were deprecated [PR #7816] (v3.1.1). The same PR stopped campaign queue jobs re-injecting themselves in a loop.
- The Contact timeline shows queued messages with attempts and next date, and offers a cancel button [PR #5051] (v2.11.0). behaviour.md Q11 records that cancel does not stop the send in 7.x.
- Reports have a "Channel Messages → Queued messages" data source [PR #5084] [PR #5118] (v2.11.0).
- `mautic:messages:send` sends one queued message per Contact per window, and `scheduled_date` is fixed when the row is queued, so later limit changes do not re-time queued rows [PR #14247] (v5.2.3). Why: the Lead was detached after the first queued send, so the second send to the same Contact raised an ORM cascade-persist error and risked a resend.
- Queue processing detaches the event entity only if it exists, and company fields are not normalised like custom fields when tokens are prepared [PR #13071] (v5.0.0). Why: queued messages were sent several times.
- Channel batch loops detach single entities instead of calling the deprecated `EntityManager::clear()` [PR #12328] [PR #12361] (v5.0.0). Later fixes removed Lead detaches from these loops because they caused duplicate sends [PR #14247] [PR #14874].
- `mautic:messages:send` drains the whole queue by default; `--limit` caps the total and `--batch` (default 50) sets the batch size [PR #15333] (v7.0.0). Before 7.0 a run sent at most a hard-coded 50 messages. The options are absent at tag 6.0.0 and present at 7.0.0 [code: app/bundles/ChannelBundle/Command/ProcessMarketingMessagesQueueCommand.php:38-70 @7.x].

### 2.3 Broadcasts
- `mautic:broadcast:send` takes `--limit` (default 100), `--batch`, `--min-contact-id` and `--max-contact-id`, so non-overlapping runs can go in parallel [PR #5715] (v2.13.0). The options exist for every channel; only email used them at first.
- Segment ("list") Text Messages are sent by `mautic:broadcasts:send --channel=sms` within their publish window [PR #7879] (v3.2.0). The documentation PR was mautic/documentation#346.
- `--max-threads=N --thread-id=i` split Contacts between parallel processes without duplicate sends, for email and SMS [PR #11549] (v5.0).
- The broadcast command must not fail with "cannot assign null to property" under 5.x types [PR #13172] (v5.0.0).
- A segment SMS broadcast sends only when publish-up is in the past and publish-down in the future; a tester's zero sends were explained by the publish window [PR #15999] (v7.2.0).
- `BroadcastQuery` and `BroadcastResult` gained extra methods so custom SMS plugins can extend broadcasts [PR #16481] (v7.2.0). The PR does not say which methods.

### 2.4 SMS: transports and Twilio
- SMS started as a Twilio-only campaign action with STOP handling, built on the per-channel DNC work [PR #1525] (v1.4.0).
- Twilio and OneSignal settings moved from global Configuration into plugin integrations; the SMS and Notifications menus follow the integration's enabled state [PR #3821] (v2.8.0).
- Sending goes through a transport chain. Every service tagged `mautic.sms_transport` registers, a transport is used only if its integration is published, and the default is chosen in Configuration → Text Message Settings (`sms_transport`) [PR #5854] (v2.13.0). The same PR added the API endpoint that sends an SMS to a Contact.
- A transport tag names its integration through a tag attribute, falling back to the service ID [PR #6001] (v2.13.1). Rejected: forcing one integration name, because several SMS integrations must register. [PR #5983] had made the tag a single value and hid Twilio from the dropdown.
- The SMS campaign action and SMS frequency support appear for any SMS transport, not only Twilio [PR #6294] (v2.14.0).
- A transport's `sendSms()` receives the Lead, not just a number, as a declared BC break [PR #6295] (v2.14.0). 2.14.0 shipped it incomplete and every Twilio send failed with a TypeError until [PR #6366] (v2.14.1).
- The chosen default transport is saved; with no SMS plugin enabled the config shows a notice instead of an empty dropdown [PR #6544] (v2.15.1).
- Transports implement `TransportInterface` (`Integration\Twilio\TwilioTransport`); `AbstractSmsApi` and `Api\TwilioApi` were deprecated so callbacks work with pluggable transports [PR #7449] (v2.16.0).
- Twilio sends through a Messaging Service SID instead of a "From" number [PR #12539] (v5.0.0). Why: Twilio stopped supporting sending from a number for this use (issue mautic/mautic#12479). It was flagged as a possible BC break for number-configured installs. At tag 4.4.0 the feature setting is `sending_phone_number`; at 5.0.0 it is `messaging_service_sid`. In 7.x the live value is the integration feature setting `messaging_service_sid`; the `sms_messaging_service_sid` parameter is declared but not read [code: app/bundles/SmsBundle/Integration/Twilio/Configuration.php:83 @7.x] [code: app/bundles/SmsBundle/Integration/TwilioIntegration.php:56-64 @7.x] [code: app/bundles/SmsBundle/Config/config.php:74 @7.x].
- Channels → Text Messages appears only when an SMS transport plugin is enabled; bogus credentials are enough to show it [PR #11866] (v5.0) [PR #8542] (v3.0.0).
- SMS transports may implement `BulkTransportInterface::sendBatchSms()` and `MMSTransportInterface::sendMms()` [PR #15999] (v7.2.0). The interfaces are absent at tag 7.1.0 and present at 7.2.0.
- A test-only SMS transport lets functional tests exercise real sending [PR #13743] (v5.1).

### 2.5 SMS: content, tracking, tokens, translations and MMS
- URLs in SMS are shortened through the configured shortener during token replacement [PR #2623] (v2.2.1).
- Links in SMS become trackable redirects; a click is logged on the timeline and identifies the Contact, through a `ContactIdentificationEvent` shared with email [PR #6829] (v2.15.0).
- An option sends SMS URLs as written, without tracking [PR #5728] (v2.14.0). It started as a Twilio integration option and became the global Text Message setting `sms_disable_trackable_urls` with a migration [PR #11683] (merged 2023-07-25, v5.0.0). Why: it should not depend on one transport. The Twilio form has the option at tag 4.4.0 and the SMS ConfigType has it at 5.0.0 [code: app/bundles/SmsBundle/Form/Type/ConfigType.php:19,50-57 @7.x] [code: app/bundles/SmsBundle/Config/config.php:78 @7.x] [code: app/bundles/SmsBundle/Helper/SmsHelper.php:68 @7.x].
- The SMS editor has a live character counter and a note that one SMS is 160 characters [PR #10514] (v4.1); the counter is correct when reopening a saved SMS [PR #10838] (v4.2.2).
- The SMS body has token autosuggest (`{` then Ctrl+Space), including owner fields; `TokensBuildEvent` lets plugins add tokens [PR #11864] (v5.1.0). Owner tokens use the shared owner-token code [PR #13743] (v5.1).
- SMS translations: an SMS has a language and translation parent, and a Contact receives the translation matching their preferred locale, else the parent [PR #15481] (v7.0.0). It went into 7.0 deliberately because it changed method signatures. `TranslationEntityTrait` is absent on `Sms` at tag 6.0.0 and present at 7.0.0.
- Sent and failed stats are recorded against the translation actually sent [PR #15545] (v7.2.0). In 7.x the parent's own count excludes translations and `getSentCount(true)` adds them [code: app/bundles/SmsBundle/Tests/Functional/SmsModelFunctionalTest.php:185-188 @7.x].
- MMS: a Text Message can carry an uploaded or external image [PR #15999] (v7.2.0). Why: issue mautic/mautic#9890. Twilio delivers MMS only to US, Canada and Australia numbers and sends a link elsewhere.
- "Template" SMS, emails and notifications are called "Trigger(ed)" in the UI because "Template Email" confused users [PR #14084] (v5.2).

### 2.6 SMS: sending, replies and STOP
- One malformed phone number must not abort the campaign run; only that Contact is affected [PR #2162] (v2.1.0). In 7.x the SMS action passes every Contact in the result (behaviour.md S19), so "fails that Contact's event" is historical.
- An SMS is sent once per campaign event [PR #3297] (v2.6.0). The PR also recorded provider errors in the timeline; see open questions for the 7.x state.
- SMS and Notifications created from the list's New button are stored as templates so campaign actions can select them [PR #2344] (v2.1.1).
- Unpublished SMS and notifications are never sent by campaign actions. This was fixed for the queue [PR #4761] (v2.10.0), for notifications [PR #6328] (v2.14.1) and again for SMS [PR #10577] (v4.1.2), where it was called a critical issue.
- Sending an SMS from a campaign must not detach the Lead [PR #14874] (v6.0.1). Detaching broke the campaign log ("LeadEventLog must be passed to either pass() or fail()") and caused duplicate SMS.
- When a send fails, the timeline shows the message content with the error [PR #13350] (v5.1). Events read "Text Message Sent" / "Text Message Failed" [PR #15763] (v7.1.0).
- Inbound replies arrive at `/sms/{transport}/callback` and fire the campaign decision "Sends a text message" (`sms.reply`) with wildcard patterns [PR #7449] (v2.16.0). A reply cannot be tied to a specific outbound SMS, so marketers must use unique phrases per step ("There's no way to include metadata to know which SMS is being replied to").
- A "Stop" reply adds an SMS DNC; the subscriber had been missing its DNC model and threw a fatal error [PR #9154] (v3.1.2).
- Segment SMS log each send in `sms_message_stats` with `is_failed` and `details` [PR #7879] (v3.2.0). The segment pending-count query must prefix every table [PR #11159] (v4.3).
- The SMS list text search filters results [PR #3639] (v2.7.1). Admins can override another user's edit lock on SMS and notifications [PR #3131] (v2.5).

### 2.7 Web and mobile push notifications
- Web push is a OneSignal campaign action; Mautic must be on HTTPS because it is the pusher [PR #1656] (v1.4.0).
- Sending to an unsubscribed Contact fails with `not_subscribed`, and by design it is not put in the timeline, like an email to a Contact with no address [PR #2152] (v2.1.0). The campaign condition "Has active notification" was added so campaigns can branch first [PR #6329] (v2.14.1).
- The OneSignal sender ID (`gcm_sender_id`, default `482941778795`) is configurable for old accounts, and the welcome notification can be turned off [PR #2909] (v2.3).
- Web notifications can have an action button (Chrome only) [PR #2980] (v2.5).
- Web push works on any page with `mtc.js`, including non-HTTPS sites through the OneSignal subdomain [PR #3274] (v2.8.0). Rejected: serving the worker scripts from Mautic's URL, because service workers must come from the site's own origin.
- Native mobile push goes through OneSignal; apps post to `/notification/appcallback` [PR #3821] (v2.8.0). An empty `push_id` there must not create a push-id row, because it broke campaign execution [PR #14480] (v5.2.7). That fix was merged without the requested test.
- OneSignal JS is added to `mtc.js` only when the integration is enabled [PR #4002] (v2.8.1), and the helper never touches Twilio [PR #3965] (v2.8.1). The "tracking page enabled" feature was restored after 2.8.0 dropped it [PR #4077] (v2.8.2); it is still read in 7.x [code: app/bundles/NotificationBundle/Integration/OneSignalIntegration.php:31 @7.x].
- UTM tags can be set on notifications [PR #3891] (v2.9.0). The UTM fields of focus items, emails, DWC and notifications share one collapsed accordion [PR #13984] (v5.2).
- The notification title is sent with each push, and the URL becomes a trackable once per notification, not once per Contact [PR #5061] (v2.12.0).
- OneSignal "Additional data" is sent in the format the API expects [PR #8605] (v3.2.5).
- Web and mobile notifications require a heading because the column is not nullable [PR #12861] (v5.0.0), fixing issue mautic/mautic#11922. The message reads "A heading is required." [PR #14775] (v7.0.0).
- The OneSignal campaign action uses batched campaign execution; batching covers several player IDs of one Contact [PR #13451] (v5.1).
- Web and mobile notification menus and permissions appear only when OneSignal is enabled [PR #11450] (v5.0). `/notification` is a public opt-in popup page [PR #11907] (v5.0).
- Mobile notifications support translations chosen by the Contact's preferred language [PR #15520] (v7.0.0). `TranslationEntityTrait` is absent on `Notification` at tag 6.0.0 and present at 7.0.0.
- Mobile and web notification previews were redesigned [PR #15427] (v7.0.0) [PR #15428] (v7.1.0); the web preview updates live while typing [PR #16928] (v7.2.0).
- The unused `notification_tracking_page_enabled` parameter was removed [PR #17671] (unreleased 7.x). The OneSignal feature `tracking_page_enabled` is a different setting and remains.

### 2.8 Focus items: visitor-side behaviour
- Focus items came from the mautic.com "mPower Focus" feature [PR #2563] (v2.2). Whether a link click counts as exit intent is a per-item option, because users wanted both behaviours.
- "Timeout before engage" applies to every trigger; "Immediately" was renamed "Upon arrival" [PR #2955] (v2.3). Rejected: a separate "after N seconds" trigger, because exit intent and scroll also need the delay.
- `/focus/{id}.js` is served as JavaScript [PR #3370] (v2.6.1). A missing item returns 404, and the script does not throw when `Focus.iframe` is undefined [PR #14521] (v5.2.4).
- The "already shown" cookie uses path `/` so limits apply site-wide [PR #5280] (v2.12.0); the conversion cookie does too [PR #7507] (v3.1.0).
- No focus stat is recorded for logged-in Mautic users or anonymous visitors without a tracked Contact [PR #4663] (v2.10.0) [PR #7197] (v2.15.2).
- "Show focus item" can follow "Visits a page" and uses only the standard tracking code [PR #4666] (v2.10.0). A 2021 comment says it needs synchronous page-hit processing. It loads its JS from an absolute URL [PR #9349] (v3.3.2); `{focus=ID}` in DWC renders an absolute URL too [PR #9519] (v3.2.5).
- "Stop engaging after conversion" works for "Emphasize a link" only with the Basic-mode link [PR #6049] (v2.14.1).
- A modal or notification closes only with its × button; a click elsewhere, such as on a cookie banner, no longer closes it [PR #12705] (v5.1). Reviewers called the click-anywhere handler "far too broad a solution". In 7.x clicks inside the item stop propagation and the close link dispatches `focus_{id}_close` [code: plugins/MauticFocusBundle/Resources/views/Builder/generate.js.twig:83-96 @7.x].
- "Stop engaging after closing the focus?" suppresses an item after the visitor closes it with ×, using a separate cookie `mautic_focus_{id}_closed` that counts closes [PR #12742] (v5.1). Rejected: reusing `mautic_focus_{id} = -1`, because a dedicated cookie records why the item stopped. The cookie is absent at tag 5.0.0 and present at 5.1.0 [code: plugins/MauticFocusBundle/Resources/views/Builder/generate.js.twig:55,673-682 @7.x] [code: plugins/MauticFocusBundle/Form/Type/PropertiesType.php:167-173 @7.x].
- After a form submission inside a focus item, the success message stays until the visitor closes it [PR #12706] (v5.1).
- Modals and notifications resize with the window and scroll vertically [PR #13132] (v5.1).
- A focus link containing contact tokens resolves to the Contact's value, and each link produces exactly one tracked redirect [PR #15502] (v7.0.0). The same PR removed the focus rendering cache because it "was always missed" and only added DB load.
- Form auto-fill works in focus items [PR #15860] (v7.0.1). Rejected: unifying form names everywhere, because that is a BC break.
- Form JavaScript inside a focus item works although the template is returned as one line; statements must end with semicolons and must not rely on HTML comments [PR #15126] (v6.0.3).
- A notice-type item never renders a form that was attached before the type changed [PR #10527] (v4.0.2). Multi-page forms paginate in modal and notification styles [PR #9737] (v4.0.0).

### 2.9 Focus items: builder and content
- Content has three modes, Basic, Editor and HTML, and each keeps its own content [PR #3460] (v2.9.0). Rejected: one shared content, because content from one mode can break another. The same PR added the REST API, UTM tags and clone without stats.
- In Editor or HTML mode the selected form is inserted with `{focus_form}`; a pasted `{form=ID}` is not counted as a focus conversion [PR #4900] (v2.10.1). Contact tokens are replaced when content is fetched, not cached.
- Custom CSS is a field of the focus content [PR #8841] (v4.1).
- The builder previews the target site in a non-scrollable iframe and reports when framing is blocked [PR #8894] (v3.0.1); it still builds a preview with an empty URL [PR #9289] (v3.1.2). The check parses the CSP `frame-ancestors` directive per RFC [PR #15837] (v7.0.1).
- Focus styles compile with Composer's `wikimedia/less.php`, so invalid LESS is now an error [PR #12422] [PR #12442] (v5.0.0).
- The bar colour works with or without a stored leading `#`, and the builder never outputs `##` [PR #14256] (v5.2).
- Cloning sets the ID to null so a new item is created [PR #6446] (v2.14.1). All focus types can be saved [PR #12769] (v5.0.0).
- The description field accepts HTML, like Assets and Campaigns [PR #16007] (v7.0.2).
- The `website` URL field defaults to `http://` when no scheme is given, because Symfony 8 changes the `UrlType` default [PR #17349] (8.0 only).

### 2.10 Focus items: statistics and reports
- Click and submission stats count only that item [PR #5257] (v2.12.1). Plugins get `FocusViewEvent` when the view pixel is hit [PR #6459] (v2.14.2).
- The detail page shows total views and conversion rates [PR #11945] (v5.0.0). The total rate is unique Contacts who clicked at least one link divided by unique views, so it cannot exceed 100%. Rejected: raw hits as the numerator. The stats are cached and loaded asynchronously, all or nothing, because counts on million-row tables time out.
- A click is not also a view [PR #13584] (v5.1). Views load for every type, not only link items [PR #13561] (v5.2).
- Focus views and clicks appear on the Contact timeline [PR #11999] (v5.0.0). With no Contact filter the subscriber returns events for all Contacts, like other activity subscribers [PR #12774] (v5.0.0).
- Unique-click links open the Contact list filtered to Contacts who clicked [PR #11418] (v4.4.3) [PR #11465] (v5.0).
- A "Focus Stats" report data source exists from 6.0 [PR #14340] (v6.0.0); the 5.2 version was not merged. 7.0 added Focus ID, category, ratios, "Hit"/"Unique Hit" and a "Focus Leads" source [PR #14923] (v7.0.0).
- The detail page has an activity feed [PR #14411] (v7.0.0) and type, style and engagement tags [PR #14831] (v7.0.0).

### 2.11 Social monitoring, tweets and social login
- Social monitoring and the "Tweet contact" action came from the mautic.com "mPower Social" feature [PR #1766] (v2.0.0). Following Twitter's automation rules is the user's responsibility.
- Tweets are a stand-alone entity, migrated from Marketing Message and campaign parameters [PR #3748] (v2.8.0); text is up to 280 characters [PR #5594] (v2.12.2).
- Handles are matched case-insensitively [PR #4035] (v2.8.2). "Match contact names" is opt-in because name matching is not exact [PR #5342] (v2.12.0).
- The monitoring commands were lost with autowiring and restored for 5.x [PR #11981] (v5.0.0). With no published monitors the command says so; with Twitter unpublished the sub-commands error.
- Google+ was removed everywhere [PR #8430] (v3.0.0).
- LinkedIn was removed from core because its API no longer worked; anyone may publish it on the Marketplace [PR #12147] (v5.0.0). The integration class is present at tag 4.4.0 and absent at 5.0.0; 7.x still ships LinkedIn Twig templates and an image [code: plugins/MauticSocialBundle/Resources/views/Integration/LinkedIn/share.html.twig @7.x].
- Twitter remains in 7.x, calling API v1.1 endpoints [code: plugins/MauticSocialBundle/Integration/TwitterIntegration.php:85 @7.x]. RCheesley noted that most SocialBundle networks no longer work with current APIs and that Twitter is the most used [PR #11944] (v5.0).
- With Twitter disabled, Social Monitoring, the contact Social tab, the Social config and the "Social login" form field are hidden [PR #12778] (v5.1).
- Tweet list templates check the plural `mauticSocial:tweets:*` permissions [PR #15460] (v7.0.0). Social Monitoring is available in API v2 [PR #15696] (v7.1.0).
- A form with a "Social login" field saves without a 500 [PR #14919] (v5.2.5).

## 3. Regression catalogue
Rows describe contracts still true in 7.x unless marked historical.

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| [MM] Email campaign sends logged "not subscribed" | Each channel's campaign event name is unique | [PR #2152] | 2.1.0 |
| [MM] Channel edits lost | Channel edits persist | [PR #3634] | 2.7.1 |
| [MM] Category type stored as 0 | Stored as `messages` | [PR #8462] | 3.0.1 |
| [MM] Contact page 500 when OneSignal object missing | Missing integration skipped | [PR #8793] | 3.0.0 |
| [MM] Sort by category broke the list | Sorting works | [PR #11725] [PR #11733] | 5.0 / 4.4.6 |
| [MM] 500 on delete or view | Delete and view work | [PR #12773] [PR #14489] | 5.0.0 / 6.0.0 |
| [Queue] 3/week limit delayed the 4th email 3 weeks | Delayed one period | [PR #4761] | 2.10.0 |
| [Queue] SMS used email frequency settings | SMS uses SMS settings | [PR #4761] | 2.10.0 |
| [Queue] Unpublished email/SMS sent from queue | Not sent; retried as failed | [PR #4761] | 2.10.0 |
| [Queue] Failed message rescheduled 15 months ahead | Rescheduled in minutes | [PR #7816] | 3.1.1 |
| [Queue] Queued messages sent several times | Each queued row sends once | [PR #13071] | 5.0.0 |
| [Queue] Second queued message to a Contact raised an ORM error | One send per Contact per window | [PR #14247] | 5.2.3 |
| [Queue] Only 50 queued messages sent per run | Whole queue unless `--limit` | [PR #15333] | 7.0.0 |
| [Broadcast] "cannot assign null to property" | Broadcast sends | [PR #13172] | 5.0.0 |
| [SMS] Bad phone number aborted the whole run | Other Contacts still processed | [PR #2162] | 2.1.0 |
| [SMS] List-created SMS not offered in campaigns | Stored as template | [PR #2344] | 2.1.1 |
| [SMS] URLs not shortened | Shortener applied | [PR #2623] | 2.2.1 |
| [SMS] Sent twice per event | Sent once | [PR #3297] | 2.6.0 |
| [SMS] Twilio missing from gateway dropdown | Alias from tag attribute or service ID | [PR #6001] | 2.13.1 |
| [SMS] Campaign action hidden for non-Twilio gateways | Shown for any transport | [PR #6294] | 2.14.0 |
| [SMS] Twilio TypeError on every send | Transport receives the Lead | [PR #6366] | 2.14.1 |
| [SMS] Default transport not saved | Saved and used | [PR #6544] | 2.15.1 |
| [SMS] SMS link click did not identify the Contact | Click logged; Contact identified | [PR #6829] | 2.15.0 |
| [SMS] SMS dropdowns empty | Existing SMS listed | [PR #8542] | 3.0.0 |
| [SMS] "Stop" reply fatal error | SMS DNC added | [PR #9154] | 3.1.2 |
| [SMS] Timeline SMS event blank | Content shown | [PR #9578] | 3.3.0 |
| [SMS] Unpublished SMS sent by campaign | Not sent | [PR #10577] | 4.1.2 |
| [SMS] 500 on Text Messages list with table prefix | All tables prefixed | [PR #11159] | 4.3 |
| [SMS] Duplicate SMS; campaign log unresolved | Lead not detached; one send | [PR #14874] | 6.0.1 |
| [SMS] Translation stats attributed to parent | Stats on the sent translation | [PR #15545] | 7.2.0 |
| [Push] Unpublished notification sent | Not sent | [PR #6328] | 2.14.1 |
| [Push] OneSignal JS loaded when disabled | Added only when enabled | [PR #4002] | 2.8.1 |
| [Push] Click stats showed per-Contact URLs | Trackable built once | [PR #5061] | 2.12.0 |
| [Push] "Additional data" broke sending | Formatted for OneSignal | [PR #8605] | 3.2.5 |
| [Push] 500 on empty heading | Validation message | [PR #12861] [PR #14775] | 5.0.0 / 7.0.0 |
| [Push] Empty `push_id` stored and broke campaigns | Empty `push_id` ignored | [PR #14480] | 5.2.7 |
| [Push] Mobile form errored with platforms unchecked | Works with any platform set | [PR #15427] | 7.0.0 |
| [Focus] JS served as text/html | Served as JavaScript | [PR #3370] | 2.6.1 |
| [Focus] Stat error for logged-in users | No stat without a Contact | [PR #4663] [PR #7197] | 2.10.0 / 2.15.2 |
| [Focus] Contact tokens frozen at cache time | Replaced per request | [PR #4900] | 2.10.1 |
| [Focus] Stats identical across items | Stats per item | [PR #5257] | 2.12.1 |
| [Focus] Shown again on another path | Cookies use path `/` | [PR #5280] [PR #7507] | 2.12.0 / 3.1.0 |
| [Focus] Clone opened the original | Clone creates a new item | [PR #6446] | 2.14.1 |
| [Focus] Blank bar with "Allow to hide" off | Bar renders | [PR #8038] | 2.16.0 |
| [Focus] Builder blank screen | Iframe preview with availability check | [PR #8894] | 3.0.1 |
| [Focus] Campaign or DWC focus used a relative URL | Absolute URL | [PR #9349] [PR #9519] | 3.3.2 / 3.2.5 |
| [Focus] Form shown in notice item | Form only for collect-data | [PR #10527] | 4.0.2 |
| [Focus] Builder 500 with null URL | URL read from GET | [PR #11687] [PR #11712] | 4.4.5 / 5.0 |
| [Focus] Conversion rate 200% | At most 100% | [PR #11945] | 5.0.0 |
| [Focus] Only link type could be saved | All types save | [PR #12769] | 5.0.0 |
| [Focus] Activity API 500 without a Contact | Events for all Contacts | [PR #12774] | 5.0.0 |
| [Focus] Cookie banner click closed the popup | Only × closes | [PR #12705] | 5.1 |
| [Focus] Success message replaced by empty form | Message stays until closed | [PR #12706] | 5.1 |
| [Focus] Link click counted as a view | Click is not a view | [PR #13584] | 5.1 |
| [Focus] Views never loaded for non-link items | Views load | [PR #13561] | 5.2 |
| [Focus] Bar colour `##hex` | Single `#` | [PR #14256] | 5.2 |
| [Focus] Missing script not 404; JS error | 404; no error | [PR #14521] | 5.2.4 |
| [Focus] Form JS broken in one-line template | Form JS works | [PR #15126] | 6.0.3 |
| [Focus] Token link redirected to a broken URL; double redirect | Token resolved; one redirect | [PR #15502] | 7.0.0 |
| [Focus] CSP `frame-ancestors` not detected | Framing blocked is reported | [PR #15837] | 7.0.1 |
| [Focus] Auto-fill missing in focus forms | Known values pre-filled | [PR #15860] | 7.0.1 |
| [Social] Duplicate Contacts from handle case | Case-insensitive match | [PR #4035] | 2.8.2 |
| [Social] Tweet over 255 characters gave SQL error | 280 characters with validation | [PR #5594] | 2.12.2 |
| [Social] Monitoring command missing in 5.x | Command registered | [PR #11981] | 5.0.0 |
| [Social] Tweets list 500 | Tweets CRUD works | [PR #14058] | 5.2 |
| [Social] 500 saving a form with Social login | Form saves | [PR #14919] | 5.2.5 |
| [Social] Tweet permissions hid New/Edit/Delete | Plural permission keys | [PR #15460] | 7.0.0 |

## 4. Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.4 | SMS channel (Twilio, STOP); web push (OneSignal); social login field | [PR #1525] [PR #1656] [PR #1552] |
| 2.0–2.2 | Social monitoring and Tweet action; SMS/push detail views; Focus items | [PR #1766] [PR #2160] [PR #2563] |
| 2.3–2.7 | Push sender ID, action button; focus engage timeout; MM detail page and `channelName` | [PR #2909] [PR #2980] [PR #2955] [PR #3367] [PR #3511] |
| 2.8 | Mobile push; Twilio/OneSignal as integrations; Tweet entity; push on tracked pages | [PR #3821] [PR #3748] [PR #3274] |
| 2.9–2.12 | Focus content modes, API and UTM; queued-messages timeline and report; "Show focus item" action; `{focus_form}` | [PR #3460] [PR #5051] [PR #5084] [PR #4666] [PR #4900] |
| 2.13–2.15 | SMS transport chain; broadcast limit/batch/ID range; disable SMS tracking; "Has active notification"; SMS click tracking; channel batch actions | [PR #5854] [PR #5715] [PR #5728] [PR #6329] [PR #6829] [PR #5962] |
| 2.16 | Inbound SMS replies and `sms.reply` decision | [PR #7449] |
| 3.0 | Focus iframe preview | [PR #8894] |
| 3.1 | DateInterval message-queue API | [PR #7816] |
| 3.2 | Segment SMS; per-channel DNC badges | [PR #7879] |
| 3.3 | Email-send and SMS-send webhooks | [PR #7716] |
| 4.1 | Focus custom CSS; SMS character counter | [PR #8841] [PR #10514] |
| 5.0 | Twilio Messaging Service SID; global SMS tracking toggle; broadcast threads; focus conversion rates and timeline events; LinkedIn removed | [PR #12539] [PR #11683] [PR #11549] [PR #11945] [PR #11999] [PR #12147] |
| 5.1 | SMS token autosuggest; focus stop-after-close and close-only-via-×; responsive focus modal; failed SMS content on timeline; batched OneSignal action; Twitter UI hidden when disabled | [PR #11864] [PR #12742] [PR #12705] [PR #13132] [PR #13350] [PR #13451] [PR #12778] |
| 5.2 | UTM accordion; "Trigger" wording | [PR #13984] [PR #14084] |
| 6.0 | Focus Stats report | [PR #14340] |
| 7.0 | SMS and mobile notification translations; `mautic:messages:send --limit/--batch`; focus cache removed; Focus Leads report; SMS phone preview | [PR #15481] [PR #15520] [PR #15333] [PR #15502] [PR #14923] [PR #15410] |
| 7.1 | Social Monitoring in API v2; web notification preview; "Text Message Sent/Failed" labels | [PR #15696] [PR #15428] [PR #15763] |
| 7.2 | MMS and bulk SMS transports; translation-aware SMS stats; live web push preview; typed model injection in controllers | [PR #15999] [PR #15545] [PR #16928] [PR #16582] |
| unreleased 7.x | Send-to-unsubscribed indicator; "text message" delete wording; `notification_tracking_page_enabled` removed | [PR #17388] [PR #17443] [PR #17671] |
| 8.0 only | `getLookupResults(): array` on lookup models; URL fields default to `http://` | [PR #15655] [PR #17349] |

## 5. Removed, deprecated, replaced

| What | Replaced by | PR | Version | Note |
|---|---|---|---|---|
| Twilio/OneSignal settings in global config | Plugin integrations | [PR #3821] | 2.8.0 | `sms_*`/`notification_*` parameters remain but are unused |
| Tweets stored as parameters | Tweet entity | [PR #3748] | 2.8.0 | Migration merged duplicates |
| Direct Twilio calls | SMS transport chain | [PR #5854] | 2.13.0 | Twilio is the default |
| `sendSms($phoneNumber, …)` | `sendSms(Lead $lead, …)` | [PR #6295] [PR #6366] | 2.14.0 | BC break for transports |
| `AbstractSmsApi`, `Api\TwilioApi` | `TransportInterface`, `TwilioTransport` | [PR #7449] | 2.16.0 | Deprecated |
| `MessageQueueModel::addToQueue`, `rescheduleMessage` | DateInterval methods | [PR #7816] | 3.1.1 | Deprecated |
| Deprecated ChannelBundle events and `ChannelEvent` | — | [PR #8059] | 3.0.0 | BC break |
| Google+ | — | [PR #8430] | 3.0.0 | UPGRADE-3.0.md |
| Twilio "disable trackable URLs" option | Global `sms_disable_trackable_urls` | [PR #11683] | 5.0.0 | Migration moves the value |
| Twilio "sending phone number" | Messaging Service SID | [PR #12539] | 5.0.0 | Possible BC break |
| LinkedIn integration | Marketplace plugin | [PR #12147] | 5.0.0 | bc-break label |
| Bundled `lessc.inc.php` | `wikimedia/less.php` | [PR #12422] | 5.0.0 | Invalid LESS now fails |
| PHP templates | Twig | [PR #11668] [PR #11866] [PR #11931] [PR #11944] | 5.0 | Overrides must be Twig |
| `EntityManager::clear()` in batch loops | `detach()` | [PR #12328] [PR #12361] | 5.0.0 | Lead detach later removed |
| Click-anywhere closes focus modal | × button only | [PR #12705] | 5.1 | — |
| `iterator_mode` | `iterable_mode` | [PR #13112] [PR #14896] | 5.1 / 7.0.0 | Issue mautic/mautic#14523 planned removal for 6.0; present at tag 6.0.0, gone at 7.0.0 [code: app/bundles/CoreBundle/Entity/CommonRepository.php:389 @7.x] |
| Focus rendering cache | None | [PR #15502] | 7.0.0 | Cache never hit |
| Hard-coded 50 per `mautic:messages:send` run | `--limit`, `--batch` | [PR #15333] | 7.0.0 | Full drain by default |
| `getModel('…')` in channel controllers | Typed model injection | [PR #16582] [PR #16595] [PR #16636] | 7.2.0 | Controller subclasses must adapt |
| `config.php` services (SMS, Social, Notification) | Autowired `services.php` | [PR #16785] [PR #16790] [PR #16800] | 7.2.0 | Service IDs may become FQCNs |
| `notification_tracking_page_enabled` | — | [PR #17671] | unreleased 7.x | Never read |
| Untyped `getLookupResults()` | `array` return type | [PR #15655] | 8.0 only | BC break for implementers |

## 6. Maintainer norms for this area
- Event constant names must be unique across bundles, or listener order decides which runs [PR #2152].
- New features need tests for both branches of an option; [PR #5728] was blocked until trackable-on and trackable-off were tested. Coverage must not drop [PR #8605] [PR #11864].
- Functional tests that load the real page are preferred to unit tests that dispatch events [PR #11999] [PR #14340].
- API changes are checked against mautic/api-library tests; a breaking PR is fixed quickly or reverted [PR #12774] [PR #10716].
- Detail-page counts must not run unbounded COUNT queries without caching or async loading, and one view's stats are cached together [PR #11945].
- Activity subscribers return all events when no Contact filter is given [PR #12774].
- Do not detach the Lead in send loops; it caused duplicate sends in email, the queue and SMS [PR #14247] [PR #14874].
- Possible BC breaks such as transport configuration changes go to a major and into UPGRADE-x.md [PR #12539]; method-signature changes wait for a major [PR #15481] [PR #15655]; bug fixes avoid BC breaks [PR #15860].
- Unsupported third-party integrations are removed from core and left to the Marketplace [PR #12147].
- User-facing wording says "text message", not "SMS" or "smses" [PR #17443] [PR #15763]; translation strings live in the bundle that owns the feature [PR #11450].
- User-facing changes need a user-docs PR [PR #7449] [PR #12742] [PR #14084].
- Twig migrations must keep behaviour identical; reviewers test list, new, edit, view, sort, filter and campaign actions [PR #11866] [PR #11931].
- Dead configuration keys are removed after a repository-wide search including `plugins/` [PR #17671].

## 7. Open questions
- Conflict with behaviour.md S13: [PR #3297] recorded failed SMS in the timeline and [PR #7879] added `is_failed` to `sms_message_stats`; [PR #13350] shows content for failed sends. 7.x writes no stat row for a failed send although the column still exists [code: app/bundles/SmsBundle/Entity/Stat.php:77,109-110 @7.x]. behaviour.md wins; check where [PR #13350]'s failed-send content is read from.
- Conflict with behaviour.md F7: [PR #13491] added help text saying "Once per session" ends when the visitor leaves the site, and 7.x still ships it [code: plugins/MauticFocusBundle/Translations/en_US/messages.ini:40-46 @7.x]. behaviour.md F7 says the cookie never expires; the code wins.
- Resolved: [PR #11159] built the pending query as `mobile IS NOT NULL OR mobile <> ''`, and 7.x still does, so an empty-string `mobile` counts as present. behaviour.md S21 now says so [code: app/bundles/SmsBundle/Broadcast/BroadcastQuery.php:47-58 @7.x].
- [PR #2162] said a bad number fails that Contact's event; behaviour.md S19 says the SMS action passes every Contact. Historical; check whether Marketing Message fallback should rely on it (behaviour.md M9).
- [PR #7449]: a reply still cannot be tied to the SMS it answers.
- [PR #4666]: does "Show focus item" still need synchronous page-hit processing in 7.x?
- [PR #6049]: links written in Editor or HTML mode may not count as conversions.
- [PR #12539]: whether the UPGRADE-5.0 note for the phone-number-to-SID switch was written.
- [PR #13132]: drag-resize glitches in focus modals were not fully resolved.
- [PR #15999]: SMS token syntax, media limits beyond behaviour.md S17, and how bulk transports interact with frequency rules are not described; the Twilio SDK upgrade was deferred.
- [PR #14923]: "Hit" and "Unique Hit" and the ratio formulas are not defined.
- [PR #14583]: no description; the Marketing Message log fix is inferred.
- [PR #14480]: merged without a test; empty `push_id` handling in 7.x is untested (see test-patterns.md).
- [PR #16481]: the added BroadcastQuery/BroadcastResult methods are not listed.

## 8. Coverage
The channels area had 320 merged PRs in 4 chunks (111, 69, 90 and 50). About 260 were substantive, 19 were
behaviour-neutral refactors and 41 were noise or near-noise. Misbucketed PRs (security roll-ups #16173 and #16174,
contact booleans #10716, instance notification emails #10299, campaign progress #3039, the webhook UI revert #4341, and
UI, UUID, logger and Twig refactors) were used only as norms or ignored. 869 noise PRs were excluded upstream before
chunking.
