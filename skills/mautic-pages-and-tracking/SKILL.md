---
name: mautic-pages-and-tracking
description: "Mautic Landing Pages, the website tracking script and Dynamic Web Content: landing pages (slug, publishing and redirects, A/B variants, translations, preference-centre pages, page tokens), the tracking script mtc.js and the mt() API, the tracking pixel mtracking.gif, cookies (mautic_device_id, mtc_id), consent, Do Not Track, bot and IP filtering, the page-hit pipeline (page_hits, dwell time, unique hits), clickthrough identification (ct), redirects and trackable links (/r/{id}), UTM capture, 'Visits a page' URL matching, and Dynamic Web Content (DWC slots, {dwc=slot}). Use whenever a task mentions landing pages, page hits, visits a page, tracking code, tracking script, tracking pixel, mtc.js, cookies, anonymous visitors, clickthrough, tracked links, redirects, UTM on page visits, A/B test pages, dynamic content, PageModel::hitPage or TrackableModel, or touches app/bundles/PageBundle/ or app/bundles/DynamicContentBundle/."
---
# Mautic landing pages, tracking and dynamic web content

## Scope
This skill covers Landing Pages (`app/bundles/PageBundle/`), visitor tracking (the generated tracking script, pixel, hit pipeline, cookies, clickthrough identification, redirects/trackables used by every channel for click tracking) and Dynamic Web Content (`app/bundles/DynamicContentBundle/`). Contact identity rules, merging and the UTM tag entity live in mautic-contacts; email click statistics in mautic-emails; Focus Items in mautic-channels; theme templates in mautic-theme-development.

Terms used here: a **Contact** is a person record (code: `Lead`); a **Visitor** is an anonymous Contact created by tracking; a **hit** is one row in `page_hits` (a page view, a tracked-link click, or a 404); a **clickthrough** (`ct`) is an encoded array appended to tracked URLs that identifies the channel, message and Contact; **DWC** is Dynamic Web Content, a block of content chosen per Contact and injected into a "slot" on a web page. [code: app/bundles/PageBundle/Entity/Hit.php:17 @7.x] [code: app/bundles/CoreBundle/Helper/ClickthroughHelper.php:12-15 @7.x]

## Expected behaviour (essentials)

Tracking script
- `/mtc.js`, `/mautic-essential.js` and `/mautic-tracking.js` are generated per request from `BUILD_MAUTIC_JS` subscribers; the script request itself never creates a Contact. [code: app/bundles/CoreBundle/Controller/JsController.php:37-53 @7.x]
- `/mtc.js` = all scopes; `/mautic-essential.js` = RUNTIME + ESSENTIAL (no tracking, no identity); `/mautic-tracking.js` = TRACKING only. `appendJs()` without a scope means TRACKING. [code: app/bundles/CoreBundle/Event/BuildJsEvent.php:38-41 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#generated-scripts-and-endpoints]
- The recommended embed is the two-script consent snippet: essential first, tracking (and `mt('send','pageview')`) only after consent. Essential alone makes no tracking request and does not read `mtc_id`. [code: app/bundles/PageBundle/Resources/views/FormTheme/Config/_config_trackingconfig_widget.html.twig:32-85 @7.x] [code: tests/acceptance/MauticScriptSplitCest.php:48-121 @7.x]
- `mt('send','pageview', {extra}, {onload,onerror})` sends `page_title`, `page_language`, `page_referrer`, `page_url`, `counter`, `timezone_offset`, `timezone`, `resolution`, `platform`, `do_not_track` plus any extra keys (contact fields, `tags`, `utm_*`, `company`). [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:131-189 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-of-custom-parameters]
- Delivery is a CORS POST to `/mtc/event`; on failure it falls back to an `<img>` request to `/mtracking.gif`. DWC slots are filled before the first pageview is posted. [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:76-128 @7.x] [code: app/bundles/DynamicContentBundle/EventListener/BuildJsSubscriber.php:35-135 @7.x]
- `/mtc/event` returns `{"success":1,"id","sid","device_id","events"}`; it returns `{"success":0}` for logged-in Mautic users and for an undecodable `ct`. [code: app/bundles/PageBundle/Controller/PublicController.php:400-441 @7.x]

When a hit is (not) recorded
- No hit is recorded for logged-in Mautic users, when the `Blocked-Tracking` cookie is present, when the request is untrackable, when `ct` points to an email stat flagged as a bot click, or when no Contact with an id resolves. [code: app/bundles/PageBundle/Model/PageModel.php:410-416,427-433,460-463 @7.x]
- Untrackable = `HEAD`, `Purpose`/`Sec-Purpose: prefetch|prerender`, `Sec-GPC: 1`, `DNT: 1`, IP in `do_not_track_ips`/`do_not_track_internal_ips`, UA in `do_not_track_bots`, or DeviceDetector `isBot()`. The JS `do_not_track` parameter is only stored, never acted on. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:134-167,276-309 @7.x]
- Private-network IPs are not tracked unless `track_private_ip_ranges` is true. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:56 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#website-monitoring]
- With `anonymize_ip` on, every hit stores the IP `*.*.*.*` and no geo lookup happens. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:109-123 @7.x]

Identification and cookies
- Contact resolution for a hit: `ct` clickthrough (email/SMS stat) first, then publicly-updatable unique-identifier fields in the query, then the tracked device cookie; an identified Contact absorbs (merges) the anonymous tracked one. [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:45-200 @7.x]
- Without any identifier, a new anonymous Contact is created for every untracked browser; `track_contact_by_ip` (default off) reuses the newest Contact with the same IP. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:191-293 @7.x] [code: app/bundles/PageBundle/Config/config.php:93-107 @7.x]
- Server cookies: `mautic_device_id` (device tracking id, 1 year, SameSite=None), `mtc_id` (Contact id, session), `mautic_referer_id` (last hit id, 1800 s), `mautic_page_{parentId}` (A/B variant, 14 days), `Blocked-Tracking` (15 s, from `/r/{id}`). `cookie_secure` defaults to true. [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:119-136 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:482-488 @7.x] [code: app/bundles/PageBundle/Controller/PublicController.php:212-216,539 @7.x]
- Query values update only publicly-updatable fields; `tags=A,-B` adds A and removes B (sanitised). [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:45-200 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tags]
- A `company`/`companyname` value in the hit query can attach the Contact to a Company and make it primary. [code: app/bundles/PageBundle/Model/PageModel.php:439-457 @7.x]

Hit pipeline
- A bare hit row is flushed immediately, then `PageHitNotification` goes to Messenger transport `hit` (default DSN `sync://`, so processing is synchronous unless an async DSN is configured); enrichment, UTM, points, campaigns and webhooks run in `processPageHit`. [code: app/bundles/PageBundle/Model/PageModel.php:465-507 @7.x] [code: app/config/config.php:124 @7.x] [code: app/bundles/MessengerBundle/Config/config.php:8 @7.x]
- `page_url` comes from the explicit param, else the Redirect URL, else (pixel/CORS) `HTTP_REFERER`; query parameters inside `page_url` are merged into the hit query. [code: app/bundles/PageBundle/Model/PageModel.php:1124-1211 @7.x]
- UTM capture is automatic on every recorded hit: if any query key contains `utm_` (request or `page_url` query string), a `lead_utmtags` row is written for the hit's Contact, anonymous or known. No form action is needed. [code: app/bundles/PageBundle/Model/PageModel.php:680,1055-1097 @7.x]
- Dwell time: the next hit sets the previous hit's `date_left` from the `mautic_referer_id` cookie. A hit is unique per Contact (or tracking id) per page/redirect. [code: app/bundles/PageBundle/Model/PageModel.php:613-637 @7.x] [code: app/bundles/PageBundle/Entity/HitRepository.php:25-57 @7.x]
- `PAGE_ON_HIT` fires after the enriched hit is saved and may run inside the Messenger worker; it drives "Visits a page" and "Device visit" campaign decisions, `page.hit`/`url.hit` point actions and the `mautic.page_on_hit` webhook. [code: app/bundles/PageBundle/Model/PageModel.php:709-712 @7.x] [code: app/bundles/PageBundle/EventListener/PointSubscriber.php:58-67 @7.x]

Clickthrough, redirects, trackables
- `ct` = `urlencode(base64(serialize(array)))`; decoding rejects anything that is not a serialized array. [code: app/bundles/CoreBundle/Helper/ClickthroughHelper.php:12-52 @7.x]
- `/r/{redirectId}`: 404 if missing or unpublished; forwards every query param except `ct`; records a hit against the Redirect; dispatches `UrlTokenReplaceEvent` for `{contactfield=...}` in the destination; 302 with `Blocked-Tracking` for 15 s when the hit was not trackable. An invalid `ct` is logged and dropped, not fatal. [code: app/bundles/PageBundle/Controller/PublicController.php:446-542 @7.x]
- Channels rewrite links with `TrackableModel::parseContentForTrackables`; only `<a href>` and `<area href>` in HTML are rewritten; `data-mautic-disable-tracking="true"`, unsubscribe/webview tokens and non-http(s)/ftp/mailto URLs are skipped. [code: app/bundles/PageBundle/Model/TrackableModel.php:239-264,533-547,741-750 @7.x]

Landing pages
- Public URL is `/{[lang/][category/]alias}`; variants always use the parent's URL; visiting a variant's own alias 301-redirects to the parent. [code: app/bundles/PageBundle/Model/PageModel.php:332-378 @7.x] [code: app/bundles/PageBundle/Controller/PublicController.php:120-125 @7.x]
- Unpublished pages: users with view permission see them; others get the configured redirect (301/302/303/307/308) or a 401/404. Preference-centre pages are never served on `/{slug}`. [code: app/bundles/PageBundle/Controller/PublicController.php:67-86 @7.x]
- A/B selection picks the variant with the largest weight deficit and pins it in `mautic_page_{parentId}` for 14 days. Editing a published variant resets `variant_hits` and `variant_start_date` for the whole set. [code: app/bundles/PageBundle/Controller/PublicController.php:128-223 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:203-208 @7.x]
- Translations: a visitor without a language slug is 302-redirected to the translation matching `preferred_locale` then `Accept-Language`, unless `?ntrd=1`. [code: app/bundles/PageBundle/Controller/PublicController.php:226-242 @7.x]
- Preview `/page/preview/{id}[/draft]` records no hit; anonymous preview requires the page published and `publicPreview` true. [code: app/bundles/PageBundle/Controller/PublicController.php:315-391 @7.x]
- Drafts (`page_draft_enabled`): one draft per page; only content (HTML/template) is drafted. [code: app/bundles/PageBundle/EventListener/PageSubscriber.php:136-176 @7.x] [code: app/bundles/PageBundle/Model/PageDraftModel.php:24-56 @7.x]

Visits-a-page matching
- "Visits a page" (`page.pagehit`) with nothing configured matches any hit; otherwise parent page id, or any comma-separated URL/referer pattern. Patterns are scheme- and trailing-slash-insensitive, `*`/`?`/`[` use `fnmatch`, and every pattern also matches as a case-insensitive substring. [code: app/bundles/PageBundle/EventListener/CampaignSubscriber.php:156-222 @7.x] [code: app/bundles/EmailBundle/Helper/UrlMatcher.php:10-64 @7.x]

Dynamic Web Content
- Two kinds: campaign-based (default; chosen by the "Request dynamic content" decision and "Push dynamic content" action) and filter-based (`is_campaign_based=0`, needs a slot name and at least one filter). [code: app/bundles/DynamicContentBundle/Entity/DynamicContent.php:242-272 @7.x]
- Slot resolution: (1) real-time campaign decision for that slot, (2) last DWC stored for Contact+slot, (3) filter-based DWC for the slot whose filters match the Contact (evaluated in PHP), else empty (page default stays). [code: app/bundles/DynamicContentBundle/Helper/DynamicContentHelper.php:42-91 @7.x]
- `GET /dwc/{slot}` returns 204 with no content or `{content,id,sid,device_id}`; POST/PUT give 403. Pushed campaign content has `<script>` blocks stripped. [code: app/bundles/DynamicContentBundle/Controller/DynamicContentApiController.php:27-68 @7.x] [code: app/bundles/DynamicContentBundle/EventListener/CampaignSubscriber.php:115-148 @7.x]
- DWC content may not contain `{dwc=...}` tokens; a slot name cannot be reused with a different type (`html`/`text`). [code: app/bundles/DynamicContentBundle/Validator/Constraints/NoNestingValidator.php:28-31 @7.x]

## Where it lives

| Concern | Path |
|---|---|
| Entities / tables | `PageBundle/Entity/{Page,PageDraft,Hit,Redirect,Trackable,VideoHit}.php` → `pages`, `pages_draft`, `page_hits`, `page_redirects`, `channel_url_trackables`, `video_hits`; `DynamicContentBundle/Entity/{DynamicContent,Stat,DynamicContentLeadData}.php` → `dynamic_content`, `dynamic_content_stats`, `dynamic_content_lead_data` |
| Hit pipeline | `PageBundle/Model/PageModel.php` (`hitPage`, `processPageHit`, `getHitQuery`), `MessengerBundle/MessageHandler/PageHitNotificationHandler.php` |
| Identity | `LeadBundle/Helper/ContactRequestHelper.php`, `LeadBundle/Tracker/{ContactTracker,DeviceTracker}.php`, `.../Service/DeviceTrackingService/` |
| Request filters | `CoreBundle/Helper/{IpLookupHelper,ClickthroughHelper,CookieHelper,TrackingPixelHelper}.php` |
| Tracking JS | `CoreBundle/Controller/JsController.php`, `CoreBundle/Event/{BuildJsEvent,BuildJsScope}.php`, `{Core,Page,DynamicContent,Notification}Bundle/EventListener/BuildJsSubscriber.php` |
| Click tracking | `PageBundle/Model/{TrackableModel,RedirectModel}.php`, `PublicController::redirectAction` |
| Public routes | `/{slug}`, `/mtracking.gif`, `/mtc/event`, `/mtc`, `/r/{id}`, `/page/preview/{id}`, `/mtc.js`, `/dwc/{slot}` |
| Events | `PageBundle/PageEvents.php`, `DynamicContentBundle/DynamicContentEvents.php` |
| Config | `PageBundle/Config/config.php:93-107`; cookie/IP params in `CoreBundle/Config/config.php:297-703` |
| Permissions | `page:pages:*`, `page:preference_center:*`, `page:categories:*`, `dynamiccontent:dynamiccontents:*` |
| Tests | `PageBundle/Tests/`, `DynamicContentBundle/Tests/`, `tests/acceptance/MauticScriptSplitCest.php` |

All paths under `app/bundles/` unless absolute. Full detail: references/code-map.md. [code: app/bundles/PageBundle/Config/config.php @7.x] [code: app/bundles/DynamicContentBundle/Config/config.php:23-52 @7.x]

## How to change or extend it
- Add tracking JS through a `BUILD_MAUTIC_JS` subscriber with `appendJsForScope($js, BuildJsScope::ESSENTIAL|TRACKING, $section)`; scope is the 2nd argument. Use priority above -255 (page-event delivery must stay last); write native JS, no jQuery. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#script-scopes-and-split-scripts] [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:24-29 @7.x]
- Anything that must work before consent goes in ESSENTIAL and must not read identity cookies or call `/mtc/event`. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#script-scopes-and-split-scripts]
- Return per-pageview data to the browser via `PageEvents::ON_CONTACT_TRACKED` → `$event->getResponse()->set()`; it arrives in `detail.response.events`. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#hooking-into-the-tracking-process-and-returning-custom-responses]
- React to hits with `PAGE_ON_HIT`, assuming it may run in a Messenger worker with no live request (`activeRequest=false`, system contact set). [code: app/bundles/MessengerBundle/MessageHandler/PageHitNotificationHandler.php:35-95 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:608-611 @7.x]
- Add page tokens / A/B criteria on `PAGE_ON_BUILD`; replace tokens on `PAGE_ON_DISPLAY` (priority >254 runs before token decoding, < -255 after asset injection). [code: app/bundles/PageBundle/Model/PageModel.php:770-771 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html]
- Click tracking hooks: `REDIRECT_DO_NOT_TRACK` (skip URLs), `ON_REDIRECT_GENERATE` (add to `ct`), `UrlTokenReplaceEvent::class` (rewrite destination per Contact), `LeadEvents::ON_CLICKTHROUGH_IDENTIFICATION` (identify from custom `ct` keys). A new channel calls `parseContentForTrackables($content, $tokens, 'mychannel', $id)`. [code: app/bundles/PageBundle/Model/TrackableModel.php:220-223 @7.x] [code: app/bundles/PageBundle/Model/RedirectModel.php:70-73 @7.x]
- DWC custom filter matching: `DynamicContentEvents::ON_CONTACTS_FILTER_EVALUATE`. [code: app/bundles/DynamicContentBundle/Helper/DynamicContentHelper.php:241-250 @7.x]
- Changing `pages`/`page_hits` columns needs entity metadata + a migration in `app/migrations/` + API serializer groups (`page:read|write`) together; `page_hits` is large, so index changes need care. [code: app/bundles/PageBundle/Entity/Page.php:36-54 @7.x]
- Write code that also works in 8.x: key subscribers on event classes where 8.x requires it (see Version notes) and use `data-mautic-disable-tracking`. [code: app/bundles/PageBundle/Model/TrackableModel.php:740 @7.x]

## How to test it
- Functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`; unit tests use `PHPUnit\Framework\TestCase`; `Mautic\PageBundle\Tests\PageTestAbstract` builds a mocked `PageModel`. Fixtures: `LoadPageData`, `LoadPageHitData`, `LoadPageCategoryData`. [code: app/bundles/PageBundle/Tests @7.x]
- Copy from:
  - `app/bundles/PageBundle/Tests/Functional/Model/PageModelTest.php` (hits with field values, bot filtering, redirects)
  - `app/bundles/PageBundle/Tests/Controller/PublicControllerFunctionalTest.php` (pixel, tags XSS, company)
  - `app/bundles/PageBundle/Tests/Controller/PublicControllerRedirectTest.php` (`/r/{id}`)
  - `app/bundles/PageBundle/Tests/Model/TrackableModelTest.php` (link rewriting)
  - `app/bundles/PageBundle/Tests/EventListener/CampaignSubscriberTest.php` (URL matching)
  - `app/bundles/DynamicContentBundle/Tests/Controller/DynamicContentApiControllerFunctionalTest.php` (`/dwc/{slot}`)
- `/mtracking.gif` returns an empty 200 in the `test` env; assert on `page_hits` rows, not the GIF body. [code: app/bundles/PageBundle/Controller/PublicController.php:393-398 @7.x]
- A good regression test drives the public endpoint, then asserts the `page_hits` row (url, source, lead), Contact field/tag changes, `lead_utmtags`, and the cookies set on the response. Detail: references/test-patterns.md.

## Version notes
- 7.2 split the script into `/mautic-essential.js` and `/mautic-tracking.js` with `BuildJsScope`; `/mtc.js` is unchanged. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#generated-scripts-and-endpoints]
- 7.2 added programmatic preference-centre slot labels via `PAGE_ON_DISPLAY` params. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#customizing-preference-center]
- 7.x deprecated `mautic:disable-tracking`, positional `$shortenUrl/$utmTags` in `generateRedirectUrl`, and service `mautic.form.type.dwc_entry_filters` (7.2). [code: app/bundles/PageBundle/Model/RedirectModel.php:60-68 @7.x] [code: app/bundles/DynamicContentBundle/Config/services.php:29-30 @7.x]
- 8.x: `BuildJsEvent`, `TrackingEvent`, `PageBuilderEvent`, `PageDisplayEvent`, `PageHitEvent`, `UntrackableUrlsEvent`, `RedirectGenerationEvent`, `VideoHitEvent`, `TokenReplacementEvent`, `ContactFiltersEvaluateEvent` are dispatched by class; `CoreEvents` is deleted; `PAGE_ON_HIT` and friends still exist but never fire under their string. `PAGE_ON_TOGGLE_PUBLISH` stays string-keyed. [devdocs: https://devdocs.mautic.org/en/8.0/mauticjs_api/tracking_script.html] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/landing_pages.html]
- 8.x removes `mautic:disable-tracking` (links get tracked), the v1 theme `content` fallback for landing pages, and moves `tracking.pixel.send`/`dwc.push_content` to batch campaign actions. [PR #17078] [PR #17691]
- Full detail: references/version-notes.md.

## Pitfalls
- The UTM docs conflict: manage_contacts says UTM is recorded only by the "Record UTM Tags" form action; code records UTM on every tracked hit (landing page, script, pixel, redirect) for anonymous and known Contacts. Code wins. [code: app/bundles/PageBundle/Model/PageModel.php:680,1055-1097 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#utm-code] [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_landing_pages.html]
- Testing while logged in to Mautic records nothing: use a private window. [code: app/bundles/PageBundle/Model/PageModel.php:410-412 @7.x]
- A browser sending `DNT: 1` or `Sec-GPC: 1` is never tracked, even if the script loads fine. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:276-309 @7.x]
- `/mtc/event` needs CORS to allow the embedding origin, or the script falls back to the third-party-cookie pixel. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#local-contact-cookie-first-party-cookie] [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:76-128 @7.x]
- With an async `hit` transport, campaign decisions, points and UTM rows appear only after `messenger:consume` runs. [code: app/bundles/PageBundle/Model/PageModel.php:465-507 @7.x]
- URL patterns in "Visits a page" also match as substrings: `example.com/a` matches `example.com/about`. [code: app/bundles/EmailBundle/Helper/UrlMatcher.php:10-64 @7.x]
- Unrelated query parameters on the page URL reach the Contact if their key equals a publicly-updatable field alias. [code: app/bundles/PageBundle/Model/PageModel.php:1124-1211 @7.x]
- Server-written `mautic_device_id` lasts a year but the JS-written copy is a session cookie; the docs' "cookies last 1 year" applies only to the server cookie. [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:42-231 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-script-javascript]
- The landing-page URL-mismatch 301 never fires when a query string is present (`$requestUri` built from `$url`). [code: app/bundles/PageBundle/Controller/PublicController.php:102-113 @7.x]
- A/B total-hits uses the last child's hits instead of the parent's (`$variants[$id]` after the loop). [code: app/bundles/PageBundle/Controller/PublicController.php:183 @7.x]
- Browser-language weights (`;q=`) are never stripped (`strpos` argument order). [code: app/bundles/PageBundle/Model/PageModel.php:687 @7.x]
- DynamicContentBundle depends on the Focus plugin's `TokenHelper`; removing the plugin breaks DWC token replacement. [code: app/bundles/DynamicContentBundle/EventListener/DynamicContentSubscriber.php:26,38 @7.x]
- `PublicController::hitVideoAction` is not referenced by any route or JS in `app/` or `plugins/`, so `video_hits` is never written by core in 7.2.1. [code: app/bundles/PageBundle/Controller/PublicController.php:547-561 @7.x]
- Landing-page draft docs mention "Subject" and "selected Segment", which do not exist on pages; only HTML/template are drafted. [docs: https://docs.mautic.org/en/7.2/components/landing_pages.html#creating-a-draft-landing-page] [code: app/bundles/PageBundle/EventListener/PageSubscriber.php:136-176 @7.x]
- Devdocs still describe a `mautic_session_id` cookie with a 30-minute session; 7.2.1 only reads it for migration and never writes it. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/contacts.html#contact-tracking] [code: app/bundles/LeadBundle/Tracker/Service/ContactTrackingService/ContactTrackingService.php:29-75 @7.x]

## Related skills
- mautic-contacts: identity rules, merging, publicly-updatable fields, `lead_utmtags` entity and UTM REST endpoints.
- mautic-campaigns: how "Visits a page", "Request dynamic content" and real-time decisions are executed.
- mautic-emails: email click tracking, `{pagelink}` in emails, bot-ratio, preference centre from the unsubscribe flow.
- mautic-forms: "Record UTM Tags" action, forms embedded in pages, `mautic-form.js`.
- mautic-points-and-stages: `page.hit` / `url.hit` point actions beyond the matching rules here.
- mautic-theme-development: `page.html.twig`, builder slots, Twig sandbox.
- mautic-channels: Focus Items (`focus_item` events, `{focus=}`), notifications in `mtc.js`.
- mautic-cron-and-queues: the `hit` Messenger transport and `messenger:consume`.
- mautic-rest-api: `/api/pages`, `/api/dynamiccontents`.
- mautic-testing: test base classes and running the suite.
- mautic-upgrades-and-versions: the 8.x event-class migration across bundles.

## Reference files
- references/behaviour.md — full numbered behaviour specification (script, pipeline, identity, cookies, redirects, pages, DWC), every item cited.
- references/code-map.md — entities/columns, services, events with listeners, routes, config parameters, permissions, test locations.
- references/docs-digest.md — what docs.mautic.org and devdocs say, with URLs, procedures and doc/code discrepancies.
- references/test-patterns.md — base classes, fixtures, representative tests and skeletons for hits, redirects and DWC.
- references/version-notes.md — 5.x/6.x history, 7.x minors and the 8.x delta for this area.
- references/pr-history.md — not yet generated; PR-derived history is added in a later pass.
