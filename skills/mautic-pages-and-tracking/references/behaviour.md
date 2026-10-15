# Behaviour specification: landing pages, tracking, dynamic web content (Mautic 7.x)

All paths are relative to the Mautic repository root. Code tags refer to commit 419a08a9b35 (7.2.1).

## Contents
- A. Tracking script (B1–B12)
- B. Public tracking endpoints (B13–B16)
- C. Trackability filters (B17–B21)
- D. Contact and device identification, cookies (B22–B29)
- E. Hit pipeline (B30–B44)
- F. UTM capture (B45–B48)
- G. Clickthrough, redirects, trackables (B49–B57)
- H. Landing pages: URLs, publish, variants, translations, rendering (B58–B76)
- I. Campaign, points, reports, timeline, webhooks (B77–B84)
- J. Dynamic Web Content (B85–B96)
- K. Known defects and open questions (B97–B110)

## A. Tracking script

B1. `/mtc.js`, `/mautic-essential.js` and `/mautic-tracking.js` are built per request by `JsController::buildJs`, which defines `MAUTIC_NON_TRACKABLE_REQUEST` (the script request creates no Contact) and dispatches `CoreEvents::BUILD_MAUTIC_JS` with the accepted scopes; output is minified unless `kernel.debug`. [code: app/bundles/CoreBundle/Controller/JsController.php:37-53 @7.x] [code: app/bundles/CoreBundle/Event/BuildJsEvent.php:29-33,47-81 @7.x]

B2. Scopes are the enum `BuildJsScope::{RUNTIME, ESSENTIAL, TRACKING}`. Routes: `mautic_js` `/mtc.js` (all scopes), `mautic_essential_js` `/mautic-essential.js` (RUNTIME + ESSENTIAL), `mautic_tracking_js` `/mautic-tracking.js` (TRACKING only). [code: app/bundles/CoreBundle/Event/BuildJsScope.php:7-12 @7.x] [code: app/bundles/CoreBundle/Config/config.php:37-47 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#generated-scripts-and-endpoints]

B3. `appendJs($js, $section)` appends to TRACKING; `appendJsForScope($js, BuildJsScope $scope, $section)` is a no-op when the build does not accept the scope; `acceptsScope()` reports it. [code: app/bundles/CoreBundle/Event/BuildJsEvent.php:38-41 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#appendjsforscope-js-buildjsscope-scope-section]

B4. Subscriber priorities on `BUILD_MAUTIC_JS`: CoreBundle runtime 1000, PageBundle third-party pixels 256, NotificationBundle 254, DynamicContentBundle 200, PageBundle page-event delivery -255 ("must always be last"). [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:17 @7.x] [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:24-29 @7.x] [code: app/bundles/DynamicContentBundle/EventListener/BuildJsSubscriber.php:28 @7.x] [code: app/bundles/NotificationBundle/EventListener/BuildJsSubscriber.php:28 @7.x]

B5. Embed snippets: the consent snippet loads `/mautic-essential.js` (script id `mautic-essential-script`, then fires `mauticEssentialReady`); once consent is given it sets `window.MauticTrackingObject='mt'`, defines the `mt()` queue, queues `mt('send','pageview')` and loads `/mautic-tracking.js` (id `mautic-tracking-script`). The legacy single snippet loads essential then tracking and sends a pageview. [code: app/bundles/PageBundle/Resources/views/FormTheme/Config/_config_trackingconfig_widget.html.twig:32-43,50-68,76-85 @7.x]

B6. Essential alone makes no tracking request and does not read an existing `mtc_id`; tracking without essential stops safely (`console.warn`). [code: tests/acceptance/MauticScriptSplitCest.php:48-121 @7.x] [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:233-282 @7.x]

B7. Runtime defines `MauticJS.serialize`, `documentReady`, `iterateCollection`, `log`, `setCookie` (path `/`, `secure`, no expiry = session cookie), `createCORSRequest`, `makeCORSRequest` (POST form-encoded, header `X-Requested-With: XMLHttpRequest`, `withCredentials = MauticJS.requestWithCredentials`; an `UNSENT` status sets `CORSRequestsAllowed=false` so later calls go straight to the error callback), `parseTextToJSON`, `insertScript`, `insertStyle`, `guid`, `dispatchEvent`, `beforeFirstEventDelivery`, flags `trackingEnabled=false`, `runtimeReady=true`, `requestWithCredentials=false`. [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:42-231 @7.x]

B8. The tracking scope sets `trackingEnabled=true` and `requestWithCredentials=true`, adds `mautic_device_id` from `localStorage` to requests when `localStorage.mtc_id` exists, and defines `getTrackedContact()` (GET `/mtc`) and `setTrackedContact(response)`, which writes `mtc_id` and `mautic_device_id` as cookies and in `localStorage`. [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:233-282 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#how-are-contacts-tracked-with-the-tracking-script]

B9. `mt('send','pageview', params, callbacks)`: params sent are `page_title`, `page_language`, `preferred_locale`, `page_referrer` (hostname of `document.referrer`), `page_url`, `counter`, `timezone_offset`, `resolution`, `platform`, `do_not_track`, `timezone`, merged with the user object in argument 3 (contact fields, `tags`, `utm_*`, `company`…). The pageview runs at load and again for every later `mt('send','pageview')`. [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:131-189 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#mt-events]

B10. Delivery: pageviews after the first wait for `firstDeliveryMade`; before the first delivery the `preEventDeliveryQueue` runs (DWC fill); the POST goes to `/mtc/event`; on failure an `Image()` loads `/mtracking.gif?<params>`. URLs use `https:` if the page is https, else the Mautic site scheme. [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:61-128 @7.x]

B11. JS events: `mauticPageEventDelivered` (`detail = {event, params, response}` or `{event, params, image:true}`) → tracking core then calls `setTrackedContact(detail.response)` or `getTrackedContact()`, runs `event[3].onload`, then the `onFirstEventDelivery` queue once; `eventAddedToMauticQueue` fires on every `mt()` push. A static `<img src=".../mtracking.gif?...">` on the page is detected (polls up to 3000 ms) and treated as a delivered pageview. [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:284-376 @7.x]

B12. Third-party pixels: with `google_analytics_id` / `facebook_pixel_id` and the matching `*_trackingpage_enabled` (page outside `site_url`) or `*_landingpage_enabled` (referer contains `site_url`), the tracking build injects gtag (`user_id` = Contact id, optional `anonymize_ip`) and/or fbq with advanced-matching fields; `MauticJS.setTrackedEvents(events)` replays `facebook_pixel`, `google_analytics` and `focus_item` events from the first `/mtc/event` response. [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:196-318 @7.x] [code: app/bundles/PageBundle/Helper/TrackingHelper.php:92-121 @7.x]

## B. Public tracking endpoints

B13. `/mtracking.gif` calls `PageModel::hitPage(null, $request)` and returns a 43-byte transparent GIF with no-cache headers; in the `test` environment an empty 200 is returned. [code: app/bundles/PageBundle/Controller/PublicController.php:393-398 @7.x] [code: app/bundles/CoreBundle/Helper/TrackingPixelHelper.php:16-59 @7.x]

B14. `/mtc/event` returns `{"success":0}` for logged-in users or an undecodable `ct`; otherwise `{"success":1,"id":<contact id|null>,"sid":<device tracking id>,"device_id":<same>,"events":{...}}`, where `events` is the per-contact cache from `TrackingHelper::getCacheItem(true)` (read once and deleted) plus whatever `ON_CONTACT_TRACKED` listeners set. [code: app/bundles/PageBundle/Controller/PublicController.php:400-441 @7.x] [code: app/bundles/PageBundle/Event/TrackingEvent.php:14-34 @7.x]

B15. `/mtc` returns `{id, sid, device_id}` for the tracked Contact, or `{}` for logged-in Mautic users. [code: app/bundles/PageBundle/Controller/PublicController.php:566-581 @7.x]

B16. Public endpoints need no permission and refuse to track logged-in Mautic users. [code: app/bundles/PageBundle/Model/PageModel.php:410-412 @7.x] [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:38-41 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#website-monitoring]

## C. Trackability filters

B17. `hitPage` returns without recording when: a Mautic user is logged in; the `Blocked-Tracking` cookie is present; `IpLookupHelper::isRequestTrackable()` is false; `ct` names an email stat flagged by `BotRatioHelper::isHitByBot`; or no Contact with an id resolves. [code: app/bundles/PageBundle/Model/PageModel.php:410-416,427-433,460-463 @7.x]

B18. `isRequestTrackable()` is false for `HEAD`, `Purpose`/`Sec-Purpose` `prefetch|prerender`, `Sec-GPC: 1`, `DNT: 1`, and untrackable IPs/user agents. The JS `do_not_track` param is only stored in the hit query. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:276-309 @7.x]

B19. Untrackable IP/UA: exact, CIDR or partial match against `do_not_track_ips` + `do_not_track_internal_ips`; UA containing any `do_not_track_bots` substring; DeviceDetector `isBot()`. Client IP is read from `HTTP_CLIENT_IP`, `HTTP_X_FORWARDED_FOR`, `HTTP_X_FORWARDED`, `HTTP_X_CLUSTER_CLIENT_IP`, `HTTP_FORWARDED_FOR`, `HTTP_FORWARDED`, `REMOTE_ADDR` in that order, default `127.0.0.1`. Private ranges are skipped unless `track_private_ip_ranges`. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:56,65-98,134-167 @7.x] [code: app/bundles/CoreBundle/Entity/IpAddress.php:161-186 @7.x]

B20. `anonymize_ip` stores the literal IP `*.*.*.*` (one shared `ip_addresses` row) and skips geo lookup. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:109-123,172 @7.x]

B21. Bot-ratio filtering applies only when `ct['stat']` points to an email stat (email link scanners), not to generic pixel or script hits. [code: app/bundles/PageBundle/Model/PageModel.php:427-433 @7.x]

## D. Contact and device identification, cookies

B22. `ContactRequestHelper::getContactFromQuery`: returns null on `Blocked-Tracking`, untrackable IP or bot ratio; then (a) `ct` → `ON_CLICKTHROUGH_IDENTIFICATION` listeners (email: `ct['stat']` tracking hash → `email_stats.lead`, refused if `ct['channel']['email']` differs from the stat's email; SMS analogous) and the anonymous tracked Contact is merged into the identified one; (b) else `checkForDuplicateContact` on publicly-updatable unique-identifier fields, an existing match wins and absorbs the tracked Contact; (c) else `ContactTracker::getContact()`. Then the IP is attached, publicly-updatable values applied, and `tags` applied via `modifyTags`. [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:45-200 @7.x] [code: app/bundles/EmailBundle/EventListener/TrackingSubscriber.php:25-52 @7.x]

B23. `ContactTracker::getContact()` order: `Blocked-Tracking` → null; system Contact; `LeadGetCurrentEvent` listener; device (`mautic_device_id` cookie or request param → `lead_devices.tracking_id`); legacy `mautic_session_id` scheme (read only); `track_contact_by_ip` (newest Contact on that IP); else a new anonymous Contact (persisted unless `MAUTIC_NON_TRACKABLE_REQUEST`). Cookies are generated and `last_active` updated once per request. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-78,191-293 @7.x] [code: app/bundles/LeadBundle/Tracker/Service/ContactTrackingService/ContactTrackingService.php:29-75 @7.x]

B24. `mautic_device_id` = device `tracking_id` (23 random chars), 1 year, SameSite=None; `mtc_id` = Contact id, session cookie, SameSite=None; both use `cookie_path` (`/`), `cookie_domain` (''), `cookie_secure` (true), `cookie_httponly` (false). [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:119-136 @7.x] [code: app/bundles/CoreBundle/Helper/CookieHelper.php:44-63 @7.x] [code: app/bundles/CoreBundle/Config/config.php:297-300 @7.x]

B25. Other cookies: `mautic_referer_id` = last `page_hits.id`, 1800 s, SameSite=None; `mautic_page_{parentId}` = chosen A/B variant, 14 days, SameSite Lax; `Blocked-Tracking` = "1"/"" for 15 s from `/r/{id}`. `mautic_session_id` is never written. [code: app/bundles/PageBundle/Model/PageModel.php:482-488 @7.x] [code: app/bundles/PageBundle/Controller/PublicController.php:212-216,539 @7.x]

B26. Tracking cookies are expired when a landing-page hit was not trackable or `Blocked-Tracking` is present, and when `setTrackedContact` receives an unsaved Contact. [code: app/bundles/PageBundle/Controller/PublicController.php:298-300 @7.x] [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:87-91 @7.x] [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:111-116 @7.x]

B27. A device row is reused when signature and Contact match; otherwise a new or existing `lead_devices` row for that Contact is tracked and `wasDeviceChanged()` is true. Results are memoised per (contact id, user agent) per request. [code: app/bundles/LeadBundle/Tracker/DeviceTracker.php:32-61 @7.x] [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:60-85 @7.x]

B28. Company identification runs on hits where the model resolved the Contact itself: `IdentifyCompanyHelper::identifyLeadsCompany` can add the Contact to a Company (writing a change log) and set it as primary. Docs: pass `company` or `companyname` plus optional Company fields. [code: app/bundles/PageBundle/Model/PageModel.php:439-457 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-of-custom-parameters]

B29. On `CURRENT_LEAD_CHANGED` all hits with the old tracking id move to the new Contact; on `LEAD_POST_MERGE` page and video hits (and DWC stats) move to the winner. [code: app/bundles/PageBundle/EventListener/LeadSubscriber.php:182-202 @7.x] [code: app/bundles/PageBundle/Entity/HitRepository.php:523-549 @7.x] [code: app/bundles/DynamicContentBundle/EventListener/LeadSubscriber.php:83-89 @7.x]

## E. Hit pipeline

B30. Hit query (`getHitQuery`): GET + POST merged; `page_url` = explicit `page_url` param → Redirect URL → for pixel/CORS requests `HTTP_REFERER` unless the query (or the `d` blob) has `page_url` → else the current request URL. Query params found in `page_url` (lower-cased keys, URL-decoded) are merged under the request params; `ct` is decoded. [code: app/bundles/PageBundle/Model/PageModel.php:737-759,1029-1050,1124-1211 @7.x]

B31. `d` = urlencoded base64 of a PHP-serialized array of pixel params, decoded with `ClickthroughHelper::decodeArrayFromUrl($d, false)`. [code: app/bundles/PageBundle/Model/PageModel.php:1156-1159 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#php-snippet]

B32. Persistence is two-phase: a bare `Hit` (date, IP, raw query, code, tracking id, device) is flushed first so `mautic_referer_id` has an id; then `PageHitNotification(hitId, request, deviceChanged, isRedirect, pageId, leadId)` is dispatched; if dispatch throws, `processPageHit` runs inline. [code: app/bundles/PageBundle/Model/PageModel.php:465-507 @7.x]

B33. `PageHitNotification` routes to Messenger transport `hit`, DSN `MAUTIC_MESSENGER_DSN_HIT`, default `messenger_dsn_hit = sync://` (processed in the same request). The handler reloads hit/page or redirect/Contact and calls `processPageHit(..., activeRequest=false, hitDate=message time)`; missing rows raise `InvalidPayloadException`. [code: app/config/config.php:111-124 @7.x] [code: app/bundles/MessengerBundle/Config/config.php:8 @7.x] [code: app/bundles/MessengerBundle/MessageHandler/PageHitNotificationHandler.php:35-95 @7.x]

B34. Enrichment: page/redirect link; `source`/`source_id` from `ct['channel']` (`{channel: id}` or `[channel, id]`) else `ct['source']`; `email_id` from `ct['email']`; Contact timezone from `timezone` or `timezone_offset` (only if the Contact has none); query sanitised (`InputHelper::url` for URLs, `clean` otherwise); `referer` ← `page_referrer`; `url_title` ← `page_title` (optionally transliterated; landing pages fall back to the page title); `url` ← `page_url` or request URI. [code: app/bundles/PageBundle/Model/PageModel.php:522-589 @7.x]

B35. With `validate_page_hit_required_data` (default false), a non-404 hit without page or redirect must have `url` and `url_title`, otherwise the pre-persisted row is deleted. [code: app/bundles/PageBundle/Model/PageModel.php:591-600 @7.x] [code: app/bundles/PageBundle/Validator/PageHitValidator.php:20-44 @7.x]

B36. The Contact is saved with a `LeadManipulator('page', 'page'|'redirect'|'hit', id, url)`; off-request, the Contact is set as system Contact so listeners see it. [code: app/bundles/PageBundle/Model/PageModel.php:603-611,1099-1119 @7.x]

B37. Dwell time: a numeric `mautic_referer_id` cookie sets that earlier hit's `date_left` to now (UTC). [code: app/bundles/PageBundle/Model/PageModel.php:613-619 @7.x] [code: app/bundles/PageBundle/Entity/HitRepository.php:463-472 @7.x]

B38. Uniqueness: no earlier hit for the same `lead_id` (or `tracking_id`) and the same page/redirect. Landing pages increment `hits`, `unique_hits` if unique, and `variant_hits` if unique and `variant_start_date` is set; `page_language` is overwritten with the page's language. [code: app/bundles/PageBundle/Entity/HitRepository.php:25-57 @7.x] [code: app/bundles/PageBundle/Model/PageModel.php:625-637 @7.x]

B39. Redirect hits increment `page_redirects.hits/unique_hits`, and with `source`+`source_id` the matching `channel_url_trackables.hits/unique_hits`. [code: app/bundles/PageBundle/Model/PageModel.php:638-661 @7.x]

B40. Geo/ISP columns come from the IP lookup (unless anonymised); `referer` falls back to `HTTP_REFERER`; `user_agent`, `remote_host`, `browser_languages` stored; strings capped at 191 chars. [code: app/bundles/PageBundle/Model/PageModel.php:663-693,1252-1263 @7.x]

B41. `PAGE_ON_HIT` (`PageHitEvent`: hit, request, code, clickthrough, isUnique) is dispatched after the enriched hit is flushed. [code: app/bundles/PageBundle/Model/PageModel.php:709-712 @7.x]

B42. Off-request processing bumps `leads.last_active` to the hit time when later. [code: app/bundles/PageBundle/Model/PageModel.php:714-734 @7.x]

B43. 404s: an unknown slug records a 404 hit (no page) unless `do_not_track_404_anonymous` is on and the Contact is anonymous. [code: app/bundles/PageBundle/Controller/PublicController.php:305-309 @7.x] [code: app/bundles/PageBundle/Model/Tracking404Model.php:25-43 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]

B44. `mautic:maintenance:cleanup` deletes `page_hits` and `lead_utmtags` of Contacts with `last_active` ≤ cutoff and (unless GDPR mode) `date_identified IS NULL`, in batches of 10 000; dry-run only counts. [code: app/bundles/PageBundle/EventListener/MaintenanceSubscriber.php:27-94 @7.x]

## F. UTM capture

B45. Resolution of the documentation conflict: in 7.2.1 every recorded hit calls `setUtmTags($hit, $lead)`; if any hit-query key contains `utm_`, a `lead_utmtags` row is saved with `date_added` = hit date, `url`, `referer`, full `query`, `user_agent`, `remote_host`, the Contact and the five `utm_campaign|term|content|medium|source` values, then `LeadModel::setUtmTags` saves the Contact. This applies to landing-page views, script/pixel hits on external sites and `/r/{id}` clicks. [code: app/bundles/PageBundle/Model/PageModel.php:680,1055-1097 @7.x]

B46. The Contact may be anonymous: the only requirement is that the hit resolves to a Contact with an id (B17). The docs say "Known Contacts", which is narrower than the code. [code: app/bundles/PageBundle/Model/PageModel.php:460-463 @7.x] [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_landing_pages.html]

B47. UTM keys reach the query from the request params or from the `page_url` query string, so `mt('send','pageview')` on `https://site/?utm_source=x` records UTM without passing it explicitly. [code: app/bundles/PageBundle/Model/PageModel.php:1124-1211 @7.x]

B48. Outbound: redirect URLs get `utm_*` from the entity's UTM tags via `RedirectModel::applyUtmTags` (`utmSource`→`utm_source`, …); DWC applies its own UTM tags to links in its content. Mautic does not de-duplicate UTM already hard-coded in links. [code: app/bundles/PageBundle/Model/RedirectModel.php:191-201 @7.x] [code: app/bundles/DynamicContentBundle/EventListener/DynamicContentSubscriber.php:92-140 @7.x] [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_emails.html#configure-email-utm-tags]

## G. Clickthrough, redirects, trackables

B49. `ct` = `urlencode(base64_encode(serialize($array)))`; decoding optionally url-decodes, base64-decodes, requires the payload to start with `a` and unserialise to an array, else `InvalidDecodedStringException`. Typical email keys: `source => ['email', id]`, `email => id`, `stat => trackingHash`, `lead => id`, `channel => ['email' => id]`. [code: app/bundles/CoreBundle/Helper/ClickthroughHelper.php:12-52 @7.x] [code: app/bundles/PageBundle/Tests/Functional/Model/PageModelTest.php:111-120 @7.x]

B50. `/r/{redirectId}` (alias `/redirect/{redirectId}`): 404 if missing or unpublished; `&amp;` decoded; every query param except `ct` appended to the destination; with `ct` and a trackable IP the Contact is identified from `ct` (invalid `ct` → warning, `ct` removed, cookie Contact used), a 200 hit is recorded on the Redirect, `UrlTokenReplaceEvent(url, lead, emailId)` replaces Contact tokens; Mautic asset-download destinations get `ct` re-appended; the final URL must pass `UrlHelper::isValidUrl` else 404; response 302 with `Blocked-Tracking` = `!isHitTrackable` for 15 s. [code: app/bundles/PageBundle/Controller/PublicController.php:446-542 @7.x]

B51. With `append_segment_id_tracking_url`, `segment_ids=<comma list>` of the Contact's Segments is appended to the redirect destination. [code: app/bundles/PageBundle/EventListener/SegmentTrackingSubscriber.php:35-71 @7.x]

B52. `RedirectModel::generateRedirectUrl` builds the absolute `mautic_url_redirect` URL with the clickthrough, after `ON_REDIRECT_GENERATE` listeners may add keys. Passing `$shortenUrl`/`$utmTags` positionally is deprecated. [code: app/bundles/PageBundle/Model/RedirectModel.php:54-106 @7.x]

B53. `getRedirectByUrl` creates a Redirect when the URL is unknown; there is no DB unique constraint on `page_redirects.url`. [code: app/bundles/PageBundle/Model/RedirectModel.php:115-127 @7.x] [code: app/bundles/PageBundle/Entity/Redirect.php:45-71 @7.x]

B54. `TrackableModel::generateTrackableUrl` sets `clickthrough['channel'] = [channel => channelId]` and delegates; lookups are by exact URL + channel + channelId, creating Redirect+Trackable when missing. With channel+id, `Trackable` rows (per-channel stats) are created; without, plain Redirects. [code: app/bundles/PageBundle/Model/TrackableModel.php:90-200,613-622 @7.x]

B55. `parseContentForTrackables($content, $tokens, $channel, $channelId, $usingClickthrough)` returns content with URLs replaced by `{trackable=REDIRECTID}` plus a token map. HTML (detected by `/<[^<]+>/`) is parsed for `<a href>` and `<area href>` only; plain text uses `UrlHelper::getUrlsFromPlaintext` plus Contact URL-type fields; longer URLs are replaced first; `&` and `&amp;` both match. [code: app/bundles/PageBundle/Model/TrackableModel.php:239-330,337-394,732-759 @7.x]

B56. A link is left untracked when it carries `data-mautic-disable-tracking="true"` (or deprecated `mautic:disable-tracking`); matches the do-not-track list (`{webview_url}`, `{resubscribe_url}`, `{unsubscribe_url}`, `{dnc_url}`, `{trackable=...}` plus `REDIRECT_DO_NOT_TRACK` additions); has a scheme other than http/https/ftp/ftps/mailto or no host/path; or has a tokenised host whose token has no value. Contact-field tokens as host are kept and tracked dynamically. [code: app/bundles/PageBundle/Model/TrackableModel.php:456-463,502-547,655-658,741-750 @7.x] [code: app/bundles/PageBundle/Event/UntrackableUrlsEvent.php:14-20 @7.x]

B57. `{pagelink=ID}` resolves to the absolute landing-page URL; in emails it carries the email clickthrough, on pages `source => ['page', id]`. [code: app/bundles/PageBundle/Helper/TokenHelper.php:16-41 @7.x] [code: app/bundles/PageBundle/EventListener/BuilderSubscriber.php:84-110 @7.x]

## H. Landing pages

B58. Alias on save: empty → title; cleaned allowing underscores; made unique among pages outside the page's own variant/translation set by appending 1, 2, …; `revision` increments on every non-new save. [code: app/bundles/PageBundle/Model/PageModel.php:169-200 @7.x] [code: app/bundles/PageBundle/Entity/PageRepository.php:45-62 @7.x]

B59. URL = `/{[lang/][category|uncategorized/]alias}` (category only with `cat_in_page_url`); variants use the parent's URL. Slugs of 1–3 segments resolve; in a 2-segment slug the first segment is treated as language when it is a known locale; the translated "uncategorized" word maps to no category; `id:alias` loads by id. [code: app/bundles/PageBundle/Model/PageModel.php:332-378 @7.x] [code: app/bundles/CoreBundle/Model/AbstractCommonModel.php:170-230 @7.x]

B60. The catch-all route `/{slug}` excludes `_profiler`, `_wdt`, `css`, `images`, `js`, `favicon.ico`, `apps/bundles/`, `plugins/`. [code: app/bundles/PageBundle/Config/config.php:68 @7.x]

B61. Published = `is_published`, within `publish_up`/`publish_down`, category published. [code: app/bundles/CoreBundle/Entity/FormEntity.php:233-251 @7.x]

B62. Unpublished page: users with view access see it; others get a hit with the configured redirect code and a redirect (301/302/303/307/308) when `redirectType` is set (404 if no URL), else a 401 hit and access denied. `redirectUrl` must be a valid URL when `redirectType` is set. [code: app/bundles/PageBundle/Controller/PublicController.php:72-86 @7.x] [code: app/bundles/PageBundle/Form/Type/RedirectListType.php:19-25 @7.x] [code: app/bundles/PageBundle/Entity/Page.php:327-343 @7.x]

B63. For anonymous visitors the Contact is resolved before rendering (for language choice); a non-canonical URI is 301-redirected after a 301 hit (but see B97); a variant's own alias 301-redirects to the parent. [code: app/bundles/PageBundle/Controller/PublicController.php:90-125 @7.x]

B64. A/B selection (anonymous visitors only): children weighted `weight/100` with hits = `variant_hits` (+ published translations); a valid `mautic_page_{parentId}` cookie wins; otherwise parent weight = `(100 − Σchild)/100`, deficit = `weight − hits/totalHits`, highest deficit wins (ties: fewer hits), stored in the cookie for 14 days. [code: app/bundles/PageBundle/Controller/PublicController.php:128-223 @7.x]

B65. Variant weights of all children must total ≤ 100; a variant of a variant cannot be created. [code: app/bundles/PageBundle/Entity/Page.php:345-361 @7.x] [code: app/bundles/PageBundle/Controller/PageController.php:904-906 @7.x]

B66. Saving a published variant or translation of a variant with changes resets `variant_start_date` to now and `variant_hits` to 0 for the related set; deleting a published variant resets siblings; `convertWinnerVariant` swaps parent and child without regenerating aliases/dates. [code: app/bundles/PageBundle/Model/PageModel.php:203-222,1216-1227 @7.x] [code: app/bundles/CoreBundle/Model/VariantModelTrait.php:81-161 @7.x]

B67. Winner criteria: `page.bouncerate` — bounces = code 200 hits with `date_left IS NULL` since `variant_start_date` over `variant_hits`, lowest wins (ties → several winners); `page.dwelltime` — highest average `date_left − date_hit` wins. [code: app/bundles/PageBundle/EventListener/DetermineWinnerSubscriber.php:30-162 @7.x] [code: app/bundles/PageBundle/Entity/HitRepository.php:271-406 @7.x]

B68. Translations: without a language slug, `getTranslatedEntity` picks by `preferred_locale`, then `Accept-Language` (dialect, then core language), stores `preferred_locale` on the Contact if empty, and 302-redirects (302 hit) unless `?ntrd=1`. `{langbar}` links carry `?ntrd=1`. [code: app/bundles/PageBundle/Controller/PublicController.php:226-242 @7.x] [code: app/bundles/CoreBundle/Model/TranslationModelTrait.php:21-131 @7.x] [code: app/bundles/PageBundle/EventListener/BuilderSubscriber.php:362-425 @7.x]

B69. Rendering: `customHtml` if present, else the legacy v1 path (theme `html/page.html.twig` with `content`); GA snippet and `<meta name="robots" content="noindex">` (if `noIndex`) before `</head>`; `/mtc.js` added to `onPageDisplay_headClose`; `PAGE_ON_DISPLAY`; then `hitPage(... 200 ...)`. [code: app/bundles/PageBundle/Controller/PublicController.php:245-300 @7.x]

B70. `PAGE_ON_DISPLAY` chain: `TokenSubscriber` (254) decodes `%7B…%7D`; `DynamicContentSubscriber::decodeTokens` (254) fills DWC slots and `{dwc=slot}`; `BuilderSubscriber` (0) replaces `{langbar}`, `{sharebuttons}`, `{pagetitle}`, `{brand=name}`, `{pagemetadescription}`, preference-centre tokens, `{pagelink=ID}`, and inserts `headScript`/`footerScript`; `DateTimeTokenSubscriber` (0) replaces `{today}`; `PageSubscriber` (-255) outputs asset slots `onPageDisplay_headClose|bodyOpen|bodyClose` and `customTag`. [code: app/bundles/PageBundle/EventListener/TokenSubscriber.php:18-24 @7.x] [code: app/bundles/PageBundle/EventListener/BuilderSubscriber.php:186-232 @7.x] [code: app/bundles/PageBundle/EventListener/PageSubscriber.php:86-134 @7.x]

B71. Page builder tokens (`PAGE_ON_BUILD`): `{pagelink=ID}`, filter-based `{dwc=slot}`, `{langbar}`, `{sharebuttons}`, `{pagetitle}`, `{brand=name}`, `{pagemetadescription}`, `{segmentlist}`, `{categorylist}`, `{preferredchannel}`, `{channelfrequency}`, `{saveprefsbutton}`, `{successmessage}`, `{leadidentifier}`, `{today}`; A/B criteria `page.bouncerate`, `page.dwelltime`. [code: app/bundles/PageBundle/EventListener/BuilderSubscriber.php:115-184 @7.x]

B72. Preference centre: only on `isPreferenceCenter` pages, the slot tokens render from `@MauticCore/Slots/*.html.twig`; the form wraps the smallest ancestor containing both the first slot and `.prefs-saveprefs`; a missing save button throws `RuntimeException`. Pages are rendered and hit-tracked through the email unsubscribe flow, never via `/{slug}`. Viewing/editing them needs `page:preference_center:*` as well as `page:pages:*`. [code: app/bundles/PageBundle/EventListener/BuilderSubscriber.php:237-266,438-484 @7.x] [code: app/bundles/EmailBundle/Controller/PublicController.php:395-415 @7.x] [code: app/bundles/PageBundle/Controller/PageController.php:48-60,534-545 @7.x]

B73. Since 7.2, preference-centre slot labels can be changed in a `PAGE_ON_DISPLAY` listener via `getParams()`/`setParams()` (keys `segmentlist.label-text`, `categorylist.label-text`, `preferredchannel.label-text`, `channelfrequency.label-text…label-text4`, `saveprefsbutton.btnText`). [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#available-slot-parameters]

B74. Preview `/page/preview/{id}[/draft]`: anonymous needs published + `publicPreview` (draft uses the draft's flag); users need `page:pages:viewown|viewother`; `?contactId=` needs admin and contact view; no hit is recorded. [code: app/bundles/PageBundle/Controller/PublicController.php:315-391 @7.x]

B75. Drafts (`page_draft_enabled`, default false): "save as draft" stores HTML/template in `pages_draft` and keeps the live HTML; apply/save while a draft exists updates the draft; "discard" reverts and deletes the draft; "apply draft" deletes the draft row and the submitted form becomes live; only one draft per page. [code: app/bundles/PageBundle/EventListener/PageSubscriber.php:136-176 @7.x] [code: app/bundles/PageBundle/Model/PageDraftModel.php:24-56 @7.x] [code: app/bundles/PageBundle/Helper/PageConfig.php:16-19 @7.x]

B76. Edit safety and sanitising: optimistic lock `version` rejects concurrent edits; `PageType` cleans `content`, `customHtml`, `headScript`, `footerScript` as HTML and `redirectUrl` as URL; API maps `customHtml` ↔ `html` and hides variant/translation children in lists. [code: app/bundles/PageBundle/Entity/Page.php:318 @7.x] [code: app/bundles/PageBundle/Form/Type/PageType.php:58,331 @7.x] [code: app/bundles/PageBundle/Controller/Api/PageApiController.php:52-74 @7.x]

## I. Campaign, points, reports, timeline, webhooks

B77. Campaign decision `page.pagehit` ("Visits a page"; options `pages`, `url`, `referer`): matches any hit when nothing is configured; else the hit's landing-page parent id in `pages`, or the hit URL matches any comma-separated `url` pattern, or the referer matches any `referer` pattern. [code: app/bundles/PageBundle/EventListener/CampaignSubscriber.php:156-222 @7.x]

B78. `UrlMatcher::hasMatch`: both sides normalised (strip scheme, trailing slash, leading `//`, `%5B/%5D`→`[]`, `[n]`→`[]`); patterns containing `*`, `?` or `[` use case-insensitive `fnmatch`; every pattern is also tried as a case-insensitive substring. [code: app/bundles/EmailBundle/Helper/UrlMatcher.php:10-64 @7.x]

B79. Decision `page.devicehit` matches the Contact's device type/brand/OS for the hit's device. Action `tracking.pixel.send` (offered only with GA/FB ids; must follow `page.pagehit`) caches `{category, action, label}` per service for the next `/mtc/event` response. [code: app/bundles/PageBundle/EventListener/CampaignSubscriber.php:70-89,110-154,224-240 @7.x] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#campaign-action-send-tracking-event]

B80. Point actions: `page.hit` (optional page list; variants count as parent) for landing pages; `url.hit` for script/pixel hits — `page_url` must match; optional `first_time`, `page_hits ≥ N`, `accumulative_time`, `returns_within`, `returns_after`, all conditions must hold; repository lookups use LIKE with `*`→`%`, `?`→`_`, else `%url%`. [code: app/bundles/PageBundle/Helper/PointActionHelper.php:17-114 @7.x] [code: app/bundles/PageBundle/EventListener/PointSubscriber.php:31-67 @7.x]

B81. Webhook `mautic.page_on_hit` with serializer groups `hitDetails, emailDetails, pageList, leadList`. [code: app/bundles/PageBundle/EventListener/WebhookSubscriber.php:44-58 @7.x]

B82. Reports: contexts `pages`, `page.hits` (with `time_spent`, hits/time-on-site/new-vs-returning/devices/languages/referrers graphs), `video.hits`. [code: app/bundles/PageBundle/EventListener/ReportSubscriber.php:21-25,120-274,361-411 @7.x]

B83. Timeline: `page.hit` entries (page title or `url_title`/URL; channel models may customise via `ChannelTimelineInterface`) and `page.videohit`. [code: app/bundles/PageBundle/EventListener/LeadSubscriber.php:50-180 @7.x]

B84. Video hits (`VideoModel::hitVideo`) update one row per Contact+`guid`, store duration/time watched, and dispatch `VIDEO_ON_HIT`; the "don't track users" check is commented out. [code: app/bundles/PageBundle/Model/VideoModel.php:70-150 @7.x]

## J. Dynamic Web Content

B85. Campaign-based DWC (`is_campaign_based=1`, default) is selectable in the DWC campaign decision/action; filter-based DWC (`is_campaign_based=0`) requires `slot_name` and ≥1 filter and appears as `{dwc=slot}` page tokens. [code: app/bundles/DynamicContentBundle/Entity/DynamicContent.php:242-272 @7.x] [code: app/bundles/PageBundle/EventListener/BuilderSubscriber.php:150-159 @7.x] [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#filter-based-dynamic-web-content]

B86. Filters reuse the Segment filter form, limited to Contact custom fields plus `date_added`, `date_modified`, `device_brand|model|os|type`, `tags`, `leadlist` (no Company fields), and are evaluated in PHP by `MatchFilterForLeadTrait::matchFilterForLead` after `ON_CONTACTS_FILTER_EVALUATE` (a listener can force a match). [code: app/bundles/DynamicContentBundle/Form/Type/DwcEntryFiltersType.php:22-101 @7.x] [code: app/bundles/DynamicContentBundle/Helper/DynamicContentHelper.php:234-253 @7.x]

B87. Slot resolution `getDynamicContentForLead(slot, lead)`: (1) real-time `dwc.decision` for the slot, first `dwc.push_content` response wins; (2) latest published DWC in `dynamic_content_lead_data` for Contact+slot; (3) published filter-based DWC with that slot whose filters match; else `''`. [code: app/bundles/DynamicContentBundle/Helper/DynamicContentHelper.php:42-91 @7.x] [code: app/bundles/DynamicContentBundle/Model/DynamicContentModel.php:157-179 @7.x]

B88. Decision `dwc.decision` (slot `dwc_slot_name`, default `dynamicContent`) is false unless the requested slot matches; it stores the default DWC for Contact+slot, caches the slot name for 1 day, stops propagation and returns true. Action `dwc.push_content` (only after `dwc.decision`) resolves the translation, stores it for the slot, creates a Stat, replaces tokens, strips `<script>` blocks and returns the content. [code: app/bundles/DynamicContentBundle/EventListener/CampaignSubscriber.php:85-148 @7.x]

B89. Serving content creates a `dynamic_content_stats` row (`source` = slot) and dispatches `TOKEN_REPLACEMENT`: `{contactfield=…}` (incl. primary Company), `{pagelink=…}`, `{assetlink=…}`, `{form=…}`, `{focus=…}` replaced, links made trackable for channel `dynamicContent` and the DWC's UTM tags applied. [code: app/bundles/DynamicContentBundle/Helper/DynamicContentHelper.php:160-178 @7.x] [code: app/bundles/DynamicContentBundle/EventListener/DynamicContentSubscriber.php:92-140 @7.x]

B90. `GET /dwc/{slot}` defines `MAUTIC_NON_TRACKABLE_REQUEST` (no hit), resolves the Contact from the full hit query (`ct`, `mautic_device_id`, `mtc_id`, field values), returns 204 with no content, else `{content, id, sid, device_id}`; non-GET → 403. [code: app/bundles/DynamicContentBundle/Controller/DynamicContentApiController.php:27-68 @7.x]

B91. `mtc.js` fills `.mautic-slot[data-slot-name]` and `[data-slot="dwc"][data-param-slot-name]` elements (empties nodes with neither attribute), injects `response.content`, initialises embedded Mautic forms and Focus scripts; a response with `id` and `sid` updates the tracked Contact in TRACKING scope. [code: app/bundles/DynamicContentBundle/EventListener/BuildJsSubscriber.php:35-148 @7.x]

B92. Token forms: `{dynamiccontent="slot"}default{/dynamiccontent}` in emails/other content (default used when empty); `{dwc=slot}` and `<div data-slot="dwc" data-param-slot-name="slot">default</div>` in landing pages; CMS syntax `{mautic type="content" slot="x"}…{/mautic}` / `[mautic type="content" slot="x"]…[/mautic]`. [code: app/bundles/DynamicContentBundle/Helper/DynamicContentHelper.php:24-29,98-152 @7.x] [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#website-configuration]

B93. Default content: the markup inside the slot shows when no DWC matches or the visitor is not tracked; campaign default is set in the decision. [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#default-content]

B94. Validation: DWC content may not contain `{dwc=…}` (`NoNesting`); a standalone slot name cannot exist with a different `type` (`html`/`text`). [code: app/bundles/DynamicContentBundle/Validator/Constraints/NoNestingValidator.php:28-31 @7.x] [code: app/bundles/DynamicContentBundle/Validator/Constraints/SlotNameTypeValidator.php:30-41 @7.x]

B95. `sent_count` is a counter column; charts read `dynamic_content_stats.date_sent`; cloning resets `sentCount` and stats. [code: app/bundles/DynamicContentBundle/Model/DynamicContentModel.php:271-307 @7.x] [code: app/bundles/DynamicContentBundle/Entity/DynamicContent.php:146-155 @7.x]

B96. Pushed DWC needs CORS configured for the website origin, or content will not display. [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#mautic-configuration]

## K. Known defects and open questions

B97. URL-mismatch 301: `$requestUri = str_replace("?{$query}", '', $url)` strips from `$url`, so the redirect never fires when a query string is present. [code: app/bundles/PageBundle/Controller/PublicController.php:102-113 @7.x]

B98. A/B `$totalHits += $variants[$id]['hits']` uses the last child's `$id`, double-counting it instead of the parent. [code: app/bundles/PageBundle/Controller/PublicController.php:183 @7.x]

B99. `strpos(';q=', $l)` has reversed arguments, so browser-language weights are stored. [code: app/bundles/PageBundle/Model/PageModel.php:687 @7.x] [code: app/bundles/PageBundle/Model/VideoModel.php:124 @7.x]

B100. `getContactByIpAddress` builds a Contact object for untrackable requests (not persisted); `hitPage` then bails because it has no id. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:251-253 @7.x]

B101. JS-written `mtc_id`/`mautic_device_id` are session cookies without SameSite, unlike the 1-year server `mautic_device_id`. [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:42-231 @7.x]

B102. `PageHitValidator` is off by default, so pixel hits without `page_url`/`page_title` are stored. [code: app/bundles/PageBundle/Config/config.php:93-107 @7.x]

B103. `TrackingHelper::isLandingPage` uses whether `HTTP_REFERER` contains `site_url`, so GA/FB "landing page" mode applies to any page under the Mautic site URL. [code: app/bundles/PageBundle/Helper/TrackingHelper.php:120 @7.x]

B104. `DynamicContentRepository::getDynamicContentForSlotFromCampaign` has no callers. [code: app/bundles/DynamicContentBundle/Entity/DynamicContentRepository.php:199-230 @7.x]

B105. DynamicContentBundle depends on `MauticPlugin\MauticFocusBundle\Helper\TokenHelper`. [code: app/bundles/DynamicContentBundle/EventListener/DynamicContentSubscriber.php:26,38 @7.x]

B106. `/mtc/event` returns `sid` and `device_id` with the same value (BC) [unverified intent]. [code: app/bundles/PageBundle/Controller/PublicController.php:400-441 @7.x]

B107. A/B cookie is SameSite Lax while tracking cookies are SameSite None; landing pages in third-party iframes may lose the variant assignment [unverified]. [code: app/bundles/PageBundle/Controller/PublicController.php:212-216 @7.x]

B108. `PublicController::hitVideoAction` exists but nothing in `app/` or `plugins/` routes to it or calls it, and `mtc.js` contains no video tracker; video hits are unreachable in core. [code: app/bundles/PageBundle/Controller/PublicController.php:547-561 @7.x]

B109. Open: `anonymize_ip` has no `parameters` default in any bundle `config.php`; it is declared in the tracking config form only. [code: app/bundles/PageBundle/EventListener/ConfigSubscriber.php:51 @7.x]

B110. There is no `track_by_fingerprint` parameter on the 7.x branch after 7.2.1 (dead key removed, unreleased; [PR #17671]); 7.2.1 still declares it (default `false`) but nothing reads it; `page_hits.tracking_id` is the device tracking id. [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:98-117 @7.x]
