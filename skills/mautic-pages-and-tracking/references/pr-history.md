# Landing pages, tracking and dynamic web content — PR history

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
3. Regression catalogue
4. Feature timeline
5. Removed, deprecated, replaced
6. Maintainer norms for this area
7. Open questions and conflicts
8. Coverage

## 1. How to read this file
- Source: merged pull requests on mautic/mautic for Pages, Tracking, Redirects and DWC, harvested 2026-10-15. Versions come from the base branch, milestone, merge date and, where checked, the release tags in the 7.x tree; pre-3.0 versions are inferred from merge dates. [PR #1582] [PR #16660]
- "Unreleased on 7.x (after 7.2.1)" means the merge is on the 7.x head but in no release tag; a PR on the 8.x base branch applies to 8.x only. [PR #17671]
- Current behaviour is in behaviour.md; this file explains why and when. Where the two disagree, behaviour.md (code-verified) wins and the conflict is listed in section 7. [PR #9265]

## 2. Decisions that shaped current behaviour

### Pages: publishing, redirects, URLs, 404
- An unpublished page can redirect to a URL or another page alias. "No Redirect" was chosen over "none" as marketer-friendly wording, and the URL is validated as a URL. Why: avoid dead links when pages are retired [PR #611] [PR #676] (v1.1.3).
- The redirect applies while the page is unpublished; the redirect-type choices are hard-coded in the form type rather than read from config, because wrong config values broke redirects [PR #10152] (v5.1.0). 7.x offers 301/302/303/307/308 [code: app/bundles/PageBundle/Form/Type/RedirectListType.php:19-25 @7.x].
- A redirect type without a redirect URL cannot be saved, and `http://` is no longer prepended to an invalid URL. Legacy pages with a type but no URL return 404, not 500 [PR #14551] (v6.0.0).
- Aliases keep underscores. Why: "There is no reason to replace underscores with hyphens" (escopecz) [PR #13122] (v5.0.0).
- `favicon.ico` never resolves to a page or records a 404 hit [PR #136] (v1.0.0).
- A custom 404 page (`404_page`) can be any published landing page [PR #9813] (v4.0.0). Since [PR #14286] (v5.2) its content is rendered at the requested URL with status 404 instead of a redirect plus 200, so analytics tools see the bad URI. 7.x also requires the page to have custom HTML [code: app/bundles/CoreBundle/Controller/CommonController.php:569-586 @7.x].
- "Disable search indexing" sends `noindex`; "Index / No index" was rejected because "index" is not a search-engine term for editors [PR #5730] (v2.13.0).
- Language is required on pages and emails, with no empty option, because an empty language caused a 500 [PR #9403] (v3.2.0).
- Page hit URL, referer and redirect URL columns are TEXT; the user agent is TEXT too [PR #235] (v1.0.x) [PR #1190] (v1.2.3).
- The "Published" toggle reads "Available for use" for content items, and detail badges are "Available/Unavailable" for content but "Active/Inactive" for campaigns and segments. RCheesley objected to different words per bundle; it merged after community debate and docs PRs [PR #13502] (v5.1.0) [PR #14009] (v5.2).
- Emails and pages use optimistic locking: a save is refused when the record changed since the form opened [PR #15774] (v7.1.0).
- Publish toggles from the list dispatch `PAGE_ON_TOGGLE_PUBLISH` so plugins can tell a toggle from a normal save [PR #16244] (v7.2.0).
- Plugins can reject invalid landing page HTML by throwing `InvalidRenderedHtmlException`, which the page controller handles [PR #15470] (v7.0.0).

### Pages: A/B tests, translations, preview, drafts
- Variant weights must total no more than 100%, and variant start dates persist when a test starts [PR #1688] (v1.4.0). Weight and winner criteria are validated with a Callback constraint because `validation_groups` skipped validation [PR #948] (v1.2.1).
- An A/B test can be created only from the parent page [PR #1685] (v1.4.0). Cancelling "Add A/B test" or "Clone" creates nothing [PR #705] (v1.2.0) [PR #1688] (v1.4.0).
- Variants are served in proportion to their weights. The test start date resets when a published variant is deleted, not when an unpublished one is edited [PR #2335] (v2.1.1).
- Winner determination moved from static `AbTestHelper` to `DetermineWinnerEvent` so plugins can add criteria [PR #8145] (v3.0.0). The "lowest bounce rate" criterion had picked the highest rate until [PR #9936] (v4.0.2).
- A page hit is a bounce when its `date_left` is NULL. Why: the earlier temp-table and IN-list queries failed on 1.5M-row tables [PR #1103] (v1.2.3) [PR #2374] (v2.1.1).
- Landing page A/B variant creation was broken in 5.0 by a field rendered twice and fixed in [PR #13223] (v5.0.2).
- Translations: originally the language-less URL served the system-default language page [PR #1389] (v1.4.0). Since [PR #2154] (v2.1.0) Mautic redirects to the translation matching the contact's preferred locale, and the same locale logic picks email and DWC translations.
- Preview: originally any published page or variant had a public, untracked preview URL [PR #391] (v1.1). The variations preview requires a logged-in user with view permission, to avoid leaking content and contact data [PR #11719] (v5.1.0). A per-page "public preview" toggle then reopened anonymous preview for reviewers without accounts [PR #14766] (v7.0.0); 7.x defaults `publicPreview` to true [code: app/bundles/PageBundle/Entity/Page.php:203 @7.x].
- Landing page drafts sit behind `page_draft_enabled`, default false. One draft per page; the public URL serves the published content until "Apply draft". Ported from Acquia Campaign Studio and rebased to 7.x because 6.x no longer took features [PR #13937] (v7.0.0) [code: app/bundles/PageBundle/Helper/PageConfig.php:18 @7.x].

### Pages: preference centre, scripts, builder, UI
- Any page can be a preference centre; an email chooses its preference page, else the default is used. A page without a "save preferences" button cannot save [PR #4779] (v2.11.0).
- The preference form must wrap every preference field, or CSRF fails and DNC changes are lost. The form wraps only the preference slots so other forms can sit on the page [PR #6404] (v2.15.2); all fields moved inside the `<form>` to fix "CSRF token is invalid" [PR #11442] (v5.1.0); a `{channelfrequency}` slot placed first is marked `data-prefs-center-first="1"` [PR #15045] [PR #15518] (v7.2.0).
- Builder text and styles of the "save preferences" button are kept [PR #6455] (v2.14.2) [PR #7219] (v2.15.1). Every preference slot accepts a `label-text` attribute that falls back to the translation [PR #16041] (v7.2.0).
- The preference page language order is contact preferred locale, page language, user locale, system locale; saving a page downloads its language pack [PR #14370] (v6.0.0).
- Per-page "Script inside head" and "Script inside footer" are injected automatically before `</head>` and `</body>`. Hand-placed `{headScript}`/`{footerScript}` tokens were rejected because they would not work on existing pages. Tokens are not replaced inside these scripts [PR #9695] (v4.2.0). Tooltips name literal `<script>` tags because bare code is printed as text [PR #13436] (v5.1.0).
- Body-open scripts are inserted whatever attributes the `<body>` tag carries [PR #12385] (v5.1.0).
- The global "Analytics script" is raw HTML. It must not be cast to boolean [PR #9389] (v3.2.2) or escaped on save, which re-escaped it on every save [PR #13859] (v5.1.1).
- Landing page settings and tracking settings are separate config forms; when merged, tracking values overwrote page values [PR #5577] (v2.12.2).
- The landing page list has created/modified columns sorted by modified date [PR #9691] (v4.2.0) and a "Results" column of form submissions per page [PR #9693] (v4.2.0). The results join is added only where needed, because adding it in `getEntities()` broke global search [PR #11842] (v5.0).
- Tooltips never contain links: they cannot be clicked and docs URLs move [PR #14891] (v5.2.5).
- Theme Twig templates may use `map`, `filter`, `reduce`, `sort` and `find`; Twig's sandbox, not a Mautic denylist, blocks callable-string callbacks [PR #17620] (7.2 patch branch, not in 7.2.1).

### Tracking script and transport
- `mtc.js` is built server-side through `BUILD_MAUTIC_JS`, so plugins append JS by priority. It was the first step to JS-only tracking; the pixel was to be "removed in 2.0" [PR #1582] (v1.4.0). The pixel is still the fallback in 7.x [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:76-128 @7.x].
- The embed is a GA-style async loader with a configurable global (default `mt`) and explicit `mt('send','pageview',{fields})`. Why: users should not need new embed code as tracking evolves, and single-page apps can send views on demand. Rejected: firing a pageview on every script load [PR #1689] (v1.4.0).
- Callbacks go in a fourth `options` argument (`onload`, `onerror`, `onabort`), not in the fields object, so contact fields named like options still work [PR #2073] (v2.1.0) [PR #2196] (v2.2).
- Only `mt('send','pageview')` records a hit; it may be called repeatedly for SPAs, while other events such as `('send','click')` do not record a hit [PR #2639] (v2.2.1) [PR #3196] (v2.6.0) [PR #6782] (v2.16.1).
- Since 2.6, page views are a CORS POST to `/mtc/event`, with the pixel as fallback; the response returns the contact ID so no second request is needed [PR #3196] (v2.6.0).
- The CORS allow-list takes full origins, one per line, with no trailing slash [PR #1905] (v2.0.0). Preflights are cached with `Access-Control-Max-Age` [PR #5360] (v2.12.1).
- The tracking pixel code loads last in `mtc.js`, so DWC and other modules register first. Fingerprint removal took away a delay DWC relied on by accident [PR #8511] (v3.0.0).
- Plugins return data in the `/mtc/event` response through `ON_CONTACT_TRACKED`; it arrives in the `mauticPageEventDelivered` DOM event. Why: chat bots personalise without another request [PR #8442] (v3.3.0).
- GA and Facebook Pixel can be injected on landing pages and tracked pages, with a campaign "Send tracking event" action after "Visits a page". One action covers both services so other services can be added later [PR #4573] (v2.10.0). GA IP anonymisation (`google_analytics_anonymize_ip`) must be set before the pageview [PR #5525] (v2.14.1).
- The embed is split into `mautic-essential.js` (no tracking or identifiers) and `mautic-tracking.js` (consent-based tracking and personalised DWC), so essential features work without consent. Tracking Settings shows the two snippets; `/mtc.js` remains and is unchanged [PR #16660] (v7.2.0). Confirmed: the routes exist in 7.2.0 and 7.2.1 but not in 7.1.0 [code: app/bundles/CoreBundle/Config/config.php:36-48 @7.x].
- The tracking snippet in the config shows the real `mtc.js` URL, not literal Twig [PR #15718] (v7.0.0).
- `TrackingHelper` (send tracking event, show focus item) and campaign DWC keep per-visitor state in the cache, not the PHP session, so public endpoints set no session cookie and stay SameSite-safe [PR #13459] [PR #13464] (v5.1.0).

### Identification, privacy and bot filtering
- Contact fields sent by pixel or `mt()` are written only when the field is publicly updatable. Why: anonymous third parties must not write arbitrary data [PR #670] (v1.1.3) [PR #3196] (v2.6.0). Since [PR #6375] (v2.14.1) this applies to known contacts too, not only anonymous ones.
- Page data uses `page_title` and `page_url`; `title` and `url` stay as fallbacks, but `title` is the contact field [PR #670] (v1.1.3).
- Company fields can be sent in a pageview; a company is created only when a name can be found [PR #5611] (v2.13.0). Dropping the email-domain lookup was called "a business decision" and deferred.
- Tracking by IP is opt-in (`track_contact_by_ip`, default false) because shared IPs merged different people [PR #3196] (v2.6.0) [code: app/bundles/PageBundle/Config/config.php:96 @7.x].
- Fingerprint identification was opt-in from the start, "since tracking by fingerprint is illegal in some countries" [PR #3279] (v2.8.0). It was removed in 3.0 with fingerprintjs2 and adblock detection, because identical fingerprints (for example iPhones) merged strangers: "this feature is a trap" [PR #8428] (v3.0.0). The dead `track_by_fingerprint` key stayed until [PR #17671] (unreleased on 7.x, after 7.2.1).
- "Identify visitor by tracking URL" arrived on by default for cross-device identification [PR #3685] (v2.9.0). It was removed as a BC break in 7.0: the `ct` clickthrough now identifies through `LeadEvents::ON_CLICKTHROUGH_IDENTIFICATION`, which email and SMS implement. Why: legacy, manual setup, unused, and it put email in the query string [PR #14974] (v7.0.0). Confirmed: `track_by_tracking_url` is in 6.0.0 and gone from 7.0.0 [code: app/bundles/LeadBundle/LeadEvents.php:788 @7.x].
- A logged-in Mautic user is never tracked as a contact [PR #4395] (v2.9.0).
- Mautic-wide "Anonymize IP" first masked the last octet of new IPs only [PR #6121] (v2.15.0). Since [PR #10116] (v5.1.0) turning it on anonymises existing IP rows and audit-log IPs too, irreversibly, with a red warning. Not storing IP rows was rejected because changing foreign keys on huge tables locked them for hours. In 7.x the key is `anonymize_ip`, declared with default false in the tracking config form, not in a bundle `parameters` list, and every hit stores `*.*.*.*` [code: app/bundles/PageBundle/EventListener/ConfigSubscriber.php:51 @7.x] [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:109-123 @7.x]. Background anonymisation is controlled by `anonymize_ip_address_in_background` [code: app/bundles/CoreBundle/Config/config.php:711 @7.x].
- Requests from "do not track" IPs and bots create no hit and log no click; Bitly's preview bot was the trigger. Adding vendor bots to the default list was rejected [PR #3196] (v2.6.0) [PR #6591] (v2.15.0).
- Anonymous 404s can be excluded with `do_not_track_404_anonymous` (default false); known contacts' 404s are still tracked, at aspiers' insistence [PR #7614] (v4.1) [code: app/bundles/PageBundle/Config/config.php:104 @7.x].
- Bot filtering for opens and email-click page hits uses `bot_helper_blocked_ip_addresses`, `bot_helper_blocked_user_agents`, `bot_helper_time_email_threshold` (2 s) and `bot_helper_bot_ratio_threshold` (0.6). These are cheap metrics with no DB queries, separate from the do-not-track lists [PR #14593] (v6.0.0) [code: app/bundles/EmailBundle/Config/config.php:214-221 @7.x]. In 7.x a page hit is checked only when `ct` carries an email stat [code: app/bundles/PageBundle/Model/PageModel.php:427-433 @7.x].
- The `Blocked-Tracking` cookie must not cause a 500; tracking cookies are cleared [PR #15102] (v6.0.3).

### Hit pipeline, UTM, points and campaign matching
- Hit counters use atomic SQL increments because concurrent hits lost updates [PR #1036] (v1.2.1). Unique checks avoid COUNT on hot paths [PR #1244] (v1.2.3).
- A hit's `date_left` is set by the next hit from the same tracking ID [PR #2374] (v2.1.1). The page hit report has a "Time Spent" column computed from it [PR #15141] (v7.0.0).
- Page hit URLs store a real `&`, not `&#38;`, so "Visits a page" matches multi-parameter URLs [PR #6046] (v2.14.2) [PR #6303] (v2.14.1).
- Page titles keep UTF-8 by default since utf8mb4; `transliterate_page_title` (default off) restores the 2.x transliteration [PR #7080] (v2.15.1) [PR #9026] (v3.2.0).
- Long values are truncated to their column length so the hit is still recorded [PR #10709] (v4.2.0) [PR #14902] (v7.0.0).
- `validate_page_hit_required_data` (default false; hosted sets true) rejects hits missing page, URL or title. Hosted-only behaviour goes behind a flag that is off in community config [PR #16130] (v7.2.0).
- Queued hit messages carry `isRedirect`, and a bad message is rejected rather than blocking the queue [PR #6655] [PR #6983] (v2.15.2).
- UTM tags were first stored from pixel parameters [PR #1043] (v1.2.1). Since [PR #9265] (v4.0.0) they are recorded from the page URL on every landing page and `/mtc/event` hit. That PR regressed the pixel and click counting, fixed in [PR #9983] [PR #10025] (v4.0.0).
- The browser's IANA `timezone` is used before guessing from `timezone_offset` [PR #8205] (v4.0.0) [PR #12751] (v7.2.0).
- A URL-hit or page-hit point action credits the contact attached to the hit, not a separately resolved "current" contact, because shared IPs credited the wrong contact [PR #12550] (v5.0).
- "Visits specific URL" was made once per contact, and "every time" was removed because it never worked [PR #1241] (v1.2.3). The hit-count condition is "greater than or equal" [PR #5299] (v2.12.1); wildcard dwell time adds up across matching URLs [PR #5296] (v2.12.1); "seconds" was added as a unit [PR #12334] (v5.1.0).
- Plain text in URL filters matches as a substring in email-click decisions, "Visits a page" (URL and referrer), URL point actions and page-hit conditions through `UrlMatcher`. Dropping wildcard support was rejected because it would break saved configs [PR #15979] (v7.2.0).
- The "Visits a page" referrer filter supports `fnmatch` and uses the dictionary spelling "referrer" [PR #2919] (v2.3) [PR #3681] (v2.8.0).
- "Show focus item" works after "Visits a page" with the standard tracking code only, replacing a design that needed a new table [PR #4666] (v2.10.0).

### Redirects and trackables
- Since 1.4, clicks are tracked per channel through Trackables (`channel_url_trackables`), because a column per channel was impossible. URL shortening is a per-channel opt-in, and email should not shorten because providers reject short URLs [PR #1676] (v1.4.0).
- A click marks the email read, because image-blocking clients skip the open pixel [PR #921] (v1.2.1).
- Per-contact tokens such as `{webview_url}` and `{unsubscribe_url}` are never tracked, and plugins can add untrackable URLs [PR #1310] (v1.2.4). Contact-token links were at first left untracked [PR #4028] (v2.8.1). Since [PR #6043] (v2.14.0, BC break) they become redirects that store the tokens and replace them on redirect.
- Contact tokens in redirect URLs are replaced through `UrlTokenReplaceEvent` [PR #16199] (v7.2.0). `append_segment_id_tracking_url` (default false) appends `segment_ids` for third-party personalisation [PR #15746] (v7.1.0).
- Previews, "send example" and emails to users keep raw links, so stats are not polluted [PR #595] (v1.1.3) [PR #1696] (v1.4.0).
- Link replacement covers every `href`, including VML buttons [PR #4328] (v2.10.0), `<area>` image maps [PR #11391] (v4.4.2) and `mailto:` [PR #11481] (v5.0). It ignores `data-mce-href` [PR #1429] (v1.4.0) and runs longest URL first, case-insensitively [PR #530] (v1.1.3) [PR #11948] (v5.0).
- Ampersands are normalised: `&amp;` on save [PR #917] [PR #1711] (v1.4.0), encoded `&#38;`/`&#x26;` before building the redirect [PR #11644] (v5.0), and `&amp;` in a query is matched for tracking [PR #13858] (v5.2). Changing `InputHelper::clean` was rejected as too risky [PR #11644].
- Whitespace around `href` and redirect URLs is tolerated [PR #14958] (v7.0.0) [PR #15698] (v7.0.1). Query strings keep RFC 3986 `%20` [PR #15336] (v7.0.0) and dots in parameter names [PR #15725] (v7.1.0) [PR #15869] (v7.0.1).
- UTM parameters go before any `#fragment` [PR #8467] (v3.0.1). "Disable trackable URLs" still appends UTM tags: shortening, tagging and redirecting are independent [PR #15748] (v7.0.1).
- A missing `ct` still redirects without notices [PR #10418] (v4.2.0). A corrupt `ct` is treated as a bot: served, not tracked, no exception; maintainers left issue mautic/mautic#9400 open because this only treats the symptom [PR #10444] (v4.0.2). A malformed `ct` is stripped instead of causing a TypeError [PR #15567] (v7.0.0), and is logged at WARNING [PR #16893] (v7.2.0).
- Links opt out with `data-mautic-disable-tracking="true"`; `mautic:disable-tracking` is deprecated because it is not valid HTML and gets stripped [PR #15713] (v7.1.0). Confirmed: the new attribute is absent from 7.0.0 and present from 7.1.0 [code: app/bundles/PageBundle/Model/TrackableModel.php:740-747 @7.x].
- A click is unique per contact first, then per tracking cookie [PR #4293] (v2.9.0).
- Redirect SQL uses bound parameters [PR #15040] (v5.2.6) and single-quoted literals for `ANSI_QUOTES` [PR #15324] (v6.0.4) [PR #15325] (v7.0.0).

### Dynamic Web Content
- DWC began as a campaign channel: "Request dynamic content" and "Push dynamic content" fill `/dwc/{slot}` [PR #1882] (v2.0.0), with `.mautic-slot` divs on any site with `mtc.js` [PR #1905] (v2.0.0). An empty slot returns 204 [PR #2161] (v2.1.0).
- Filter-based DWC (segment-style filters plus a slot name) arrived with the "Is campaign based?" toggle [PR #5038] (v2.11.0). Only published items are served [PR #5338] (v2.12.1).
- Default type: [PR #14678] made new items filter-based, then [PR #14790] reverted it before 6.0.0 because the API-library tests failed (a BC break) and "Changing behaviour shouldn't go to a bug fix release". 7.x still defaults to campaign-based [code: app/bundles/DynamicContentBundle/Entity/DynamicContent.php:130 @7.x].
- DWC is requested before the page hit, with the same identifying parameters, which took about 600 ms instead of 2500 ms; a non-matching slot logs no campaign decision [PR #5360] (v2.12.1).
- Slot content is wrapped in CDATA before DOM insertion so entities and `&` do not break it [PR #6726] (v2.15.0). Untracked requests to `/dwc/{slot}` do not throw [PR #7197] (v2.15.2).
- DWC content can hold `{form=ID}` and `{focus=ID}` [PR #3044] (v2.5) but not nested `{dwc=}` tokens [PR #14744] (v7.0.0). Items have a Text or HTML type, only Text DWC can go in an email subject, and all items in one slot share a type [PR #14759] [PR #14901] (v7.0.0).
- Filter evaluation dispatches `ContactFiltersEvaluateEvent` for plugin filters [PR #10886] (v4.3), including for inline `{dwc=slot}` tokens [PR #14599] (v5.2.7). Filters added: segment membership [PR #13526] (v5.1.0), primary-company fields [PR #13393] (v5.1.0), tags again [PR #15988] (unreleased on 7.x, after 7.2.1). Filters that do not work for DWC are not re-introduced [PR #15988].
- DWC links become trackables with the item's UTM tags [PR #6347] (v2.14.1). `{dwc=slot}` inside an `href` resolves with HTML stripped [PR #17495] (v7.2.1).
- Fallback content works with `mautic-essential.js` alone; personalised DWC needs `mautic-tracking.js` [PR #16660] (v7.2.0).
- Deleting a DWC item cascades to `dynamic_content_lead_data`; `SET NULL` was rejected because stats mean nothing without the item [PR #3509] (v2.7.0). Create and delete need the matching permission [PR #11278] (v4.4.3) [PR #15458] (v7.0.0).

### Gated and tracked video (removed)
- Gated video paused a builder video at `data-gate-time` and showed `data-form-id` [PR #2081] (v2.1.0). Plain-video tracking became opt-in through `data-mautic-video="true"` [PR #4480] (v2.9.1). The feature was extended with a preview placeholder [PR #10074] (v4.0.0), local froogaloop [PR #11467] (v4.4.3) and iframe embeds [PR #12051] (v5.0).
- Status in 7.x: removed. Gated-video code is in 5.2.9 and absent from 6.0.0-alpha onward. The removing PR is not among this area's inputs; the 7.x git log shows commit 5c12251e03b, "Removing the Gated Video feature". Only the froogaloop copy step remains [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:113,189 @7.x], and `video_hits` is unreachable (behaviour.md B108).

## 3. Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **Pages** | | | |
| Page with redirect type but no URL gave 500 | Saving is refused; legacy rows return 404 | [PR #14551] | 6.0.0 |
| 301/302 redirect of an unpublished page did nothing | Visitors are redirected | [PR #10152] | 5.1.0 |
| Custom 404 redirected and returned 200 | 404 content at the bad URI with status 404 | [PR #14286] | 5.2 |
| Underscores stripped from aliases | Underscores kept | [PR #13122] | 5.0.0 |
| Empty language gave 500 | Language required | [PR #9403] | 3.2.0 |
| Analytics script saved as `1` or re-escaped on every save | Raw HTML stored and printed | [PR #9389], [PR #13859] | 3.2.2 / 5.1.1 |
| Landing page settings would not save | Page and tracking config both save | [PR #5577] | 2.12.2 |
| Body-open scripts missed on complex `<body>` tags | Inserted for any attributes | [PR #12385] | 5.1.0 |
| Global search on pages broken by Results join | Join only when the column needs it | [PR #11842] | 5.0 |
| Lowest-bounce criterion picked highest bounce | Lowest bounce wins | [PR #9936] | 4.0.2 |
| A/B variant creation errored in 5.0 | Variants can be created | [PR #13223] | 5.0.2 |
| Weights over 100% accepted; start dates lost | Validated; dates persist | [PR #1688] | 1.4.0 |
| Variants ignored weights | Served by weight | [PR #2335] | 2.1.1 |
| Preference centre: embedded form did not submit | Preference form wraps only its slots | [PR #6404] | 2.15.2 |
| Preference centre: "CSRF token is invalid" | All fields inside the form | [PR #11442] | 5.1.0 |
| `{channelfrequency}` first: DNC not saved | Form wraps all fields | [PR #15045], [PR #15518] | 7.2.0 |
| Restricted users could not create pages | Correct permission key | [PR #612], [PR #5361] | 1.1.x / 2.12.1 |
| **Tracking script & identification** | | | |
| Back-to-back `mt()` calls dropped hits | Every pageview call records a hit | [PR #2639], [PR #3196] | 2.2.1 / 2.6.0 |
| `mt()` with other events recorded a hit | Only `('send','pageview')` records | [PR #6782] | 2.16.1 |
| DWC stopped rendering in 3.0 | Pixel code loads last in `mtc.js` | [PR #8511] | 3.0.0 |
| Known contact not updated by publicly updatable fields | Any tracked contact updated | [PR #6375] | 2.14.1 |
| Logged-in admin bumped last-active date | Users never tracked | [PR #4395] | 2.9.0 |
| `mtracking.gif` returned 500 | 200 and a hit | [PR #9983] | 4.0.0 |
| `Blocked-Tracking` cookie gave 500 | Page loads, cookies cleared | [PR #15102] | 6.0.3 |
| Shared-IP contacts got each other's points | Points go to the hit's contact | [PR #12550] | 5.0 |
| URL point action with returns within/after gave 500 or warnings | 200; no warnings, even on first hit | [PR #12609], [PR #15529] | 5.0.3 / 7.1.0 |
| Hit count passed threshold before time spent | Hit condition is `>=` | [PR #5299] | 2.12.1 |
| Very long `<title>` broke the hit | Truncated; hit recorded | [PR #10709], [PR #14902] | 4.2.0 / 7.0.0 |
| Array query params raised warnings | Tolerated | [PR #10404] | 4.0.1 |
| CJK or emoji titles failed the insert | Stored (UTF-8 unless transliteration on) | [PR #7080], [PR #9026] | 2.15.1 / 3.2.0 |
| Stored `&#38;` broke "Visits a page" | Real `&` stored and compared | [PR #6046], [PR #6303] | 2.14.x |
| Plain `test` URL filter missed page visits | Substring everywhere; wildcards still work | [PR #15979] | 7.2.0 |
| Bad hit queue message blocked the queue | Rejected; queue continues | [PR #6983] | 2.15.2 |
| Timezone guessed despite exact zone | `timezone` used first | [PR #12751] | 7.2.0 |
| Tracking snippet showed literal Twig | Real URL shown | [PR #15718] | 7.0.0 |
| **Redirects & trackables** | | | |
| Per-contact tokens became shared trackables | Never tracked | [PR #1310] | 1.2.4 |
| `{pagelink}`/`{assetlink}` links 404 after tokenised redirects | Tokens resolve | [PR #6260] | 2.14.0 |
| Clicks not counted after UTM change | `/r/` clicks counted | [PR #10025] | 4.0.0 |
| `#anchor` broke with UTM tags | Query inserted before fragment | [PR #8467] | 3.0.1 |
| Missing `ct` logged notices | Redirects, click not attributed | [PR #10418] | 4.2.0 |
| Corrupt or malformed `ct` gave errors or 500 | Served/redirected, not tracked; WARNING log | [PR #10444], [PR #15567], [PR #16893] | 4.0.2 / 7.0.0 / 7.2.0 |
| Short URL overwrote part of a longer, differently cased URL | Longest first, case-insensitive | [PR #11948] | 5.0 |
| `&#38;` left in redirect target | Decoded before redirect | [PR #11644], [PR #11676] | 5.0 / 4.4.5 |
| `&amp;` query links untracked | Matched and tracked | [PR #13858] | 5.2 |
| Trailing space in link gave 404 | Trimmed | [PR #14958] | 7.0.0 |
| `href` with newline not tracked | Tracked | [PR #15698] | 7.0.1 |
| Spaces became `+` | `%20` kept | [PR #15336] | 7.0.0 |
| Dots in query keys became underscores | Dots kept | [PR #15725], [PR #15869] | 7.1.0 / 7.0.1 |
| "Disable trackable URLs" dropped UTM tags | UTM still appended | [PR #15748] | 7.0.1 |
| `<area>` and `mailto:` links untracked | Tracked | [PR #11391], [PR #11481] | 4.4.2 / 5.0 |
| SMS click counts did not increase | Channel counts increase | [PR #6233] | 2.14.1 |
| ANSI SQL mode broke redirect stats | Single-quoted literals | [PR #15324], [PR #15325] | 6.0.4 / 7.0.0 |
| **DWC** | | | |
| Empty slot returned 404 | 204 | [PR #2161] | 2.1.0 |
| Unpublished filter-based DWC served | Only published served | [PR #5338] | 2.12.1 |
| `&nbsp;` or `&` broke slot replacement | CDATA wrap | [PR #6726] | 2.15.0 |
| `/dwc/{slot}` threw for untracked requests | No exception; no stats | [PR #7197] | 2.15.2 |
| DWC set a session cookie without SameSite=None | Cache, no session | [PR #13464] | 5.1.0 |
| Company tokens empty in DWC | Rendered from primary company | [PR #13198], [PR #13393] | 5.1.0 |
| Select, locale or state filters showed keys | Labels shown | [PR #13526] | 5.1.0 |
| Inline `{dwc=}` ignored plugin filters | Filters evaluated | [PR #14599] | 5.2.7 |
| Lone DWC could not change type | Validator ignores itself | [PR #14901] | 7.0.0 |
| User with create permission blocked | Allowed by role | [PR #15458] | 7.0.0 |
| View-only user could create or delete | 403 | [PR #11278], [PR #11480] | 4.4.3 / 5.0 |
| Cloning DWC gave 500 | Clone works | [PR #12811], [PR #15562] | 5.0 / 7.1.0 |
| DWC timeline entries broke the contact page | Shown as "triggered" | [PR #11726], [PR #12902] | 5.0 |
| `{dwc=}` in `href` not replaced | Resolved, HTML stripped | [PR #17495] | 7.2.1 |

## 4. Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.x | Unpublished-page redirects; public preview; UTM from pixel; Trackables and per-channel shortening; `mtc.js` and the `mt()` loader | [PR #611], [PR #391], [PR #1043], [PR #1676], [PR #1582], [PR #1689] |
| 2.0–2.2 | DWC channel and CORS allow-list; pageview callbacks; gated video; locale-aware content; `mtc_id` cookie | [PR #1882], [PR #1905], [PR #2073], [PR #2081], [PR #2154], [PR #2550] |
| 2.6–2.10 | CORS `/mtc/event`; opt-in IP tracking; fingerprint option; identify by tracking URL; device decision; GA/FB Pixel; show focus item | [PR #3196], [PR #3279], [PR #3685], [PR #3894], [PR #4573], [PR #4666] |
| 2.11–2.16 | Preference centre; filter-based DWC; noindex; company fields in pageview; tokenised redirects; Anonymize IP; DWC UTM tags; redirect generation event | [PR #4779], [PR #5038], [PR #5730], [PR #5611], [PR #6043], [PR #6121], [PR #6347], [PR #6377] |
| 3.0 | Fingerprinting removed; A/B winner events | [PR #8428], [PR #8145] |
| 3.2–3.3 | `transliterate_page_title`; tracking response event | [PR #9026], [PR #8442] |
| 4.0 | Custom 404 page; timezone and locale from JS; UTM from every page hit | [PR #9813], [PR #8205], [PR #9265] |
| 4.1–4.4 | Skip anonymous 404s; head/footer scripts; Results column; DWC filter event; image-map links | [PR #7614], [PR #9695], [PR #9693], [PR #10886], [PR #11391] |
| 5.0 | `mailto:` trackables; gated video via iframe | [PR #11481], [PR #12051] |
| 5.1 | Variations preview; IP anonymisation of existing data; tracking state in cache; DWC segment filter; "Available for use" | [PR #11719], [PR #10116], [PR #13459], [PR #13526], [PR #13502] |
| 5.2 | Custom 404 rendered in place with status 404; context badges | [PR #14286], [PR #14009] |
| 6.0 | Bot-ratio filter; redirect URL validation; preference-centre language order; gated video removed (PR not identified) | [PR #14593], [PR #14551], [PR #14370] |
| 7.0 | Landing page drafts; public preview toggle; identify by tracking URL removed; DWC Text/HTML type and no nesting; Time Spent column | [PR #13937], [PR #14766], [PR #14974], [PR #14759], [PR #14744], [PR #15141] |
| 7.1 | `data-mautic-disable-tracking`; segment IDs on tracking URLs; optimistic locking | [PR #15713], [PR #15746], [PR #15774] |
| 7.2 | Split embed scripts; `UrlMatcher` everywhere; page-hit validation; `UrlTokenReplaceEvent`; preference-slot labels; toggle-publish events | [PR #16660], [PR #15979], [PR #16130], [PR #16199], [PR #16041], [PR #16244] |
| Unreleased on 7.x (after 7.2.1) | DWC tags filter; dead `track_by_fingerprint` key removed | [PR #15988], [PR #17671] |

## 5. Removed, deprecated, replaced

| What | Replaced by | PR | Version |
|---|---|---|---|
| Pixel `url`/`title` keys for page data | `page_url`/`page_title` (fallbacks kept) | [PR #670] | 1.1.3 |
| `page_redirects.email_id` | `channel_url_trackables` | [PR #1676] | 1.4.0 |
| Implicit tracking by IP | Opt-in `track_contact_by_ip` | [PR #3196] | 2.6.0 |
| `{leadfield=}` | `{contactfield=}` (old token still works) | [PR #1893] | 2.0.0 |
| Tracking of every video | Opt-in `data-mautic-video` (later removed with video tracking) | [PR #4480] | 2.9.1 |
| Fingerprint identification and fingerprintjs2 | Cookie, device ID and clickthrough identification | [PR #8428] | 3.0.0 |
| `track_by_fingerprint` dead key | — | [PR #17671] | unreleased on 7.x |
| `AbTestHelper`, slideshow form types | `DetermineWinnerEvent` | [PR #8145], [PR #8099] | 3.0.0 |
| Forced title transliteration | `transliterate_page_title` (default off) | [PR #9026] | 3.2.0 |
| `index_dev.php` | `APP_ENV`/`APP_DEBUG` in `.env.local` | [PR #12206] | 5.0 |
| Session in `TrackingHelper` and campaign DWC | Cache | [PR #13459], [PR #13464] | 5.1.0 |
| Redirect to the custom 404 URL | 404 content rendered in place | [PR #14286] | 5.2 |
| Deprecated `PagePublishDatesType`, `TrackingHelper`/`PageModel` methods, `MauticFactory::getTheme` | — | [PR #14244], [PR #14443] | 6.0.0 |
| Gated video | — (removing PR not identified) | [PR #12051] | 6.0.0 |
| Auto-prepended `http://` on redirect URL | Validation error | [PR #14551] | 6.0.0 |
| "Identify visitor by tracking URL" | `ON_CLICKTHROUGH_IDENTIFICATION` from `ct` | [PR #14974] | 7.0.0 |
| `mautic:disable-tracking` (deprecated) | `data-mautic-disable-tracking="true"` | [PR #15713] | 7.1.0 |
| `parse_str` in URL sanitising | Guzzle query parser | [PR #15725] | 7.1.0 |
| `mtc.js` as the advertised snippet (endpoint kept) | `mautic-essential.js` + `mautic-tracking.js` | [PR #16660] | 7.2.0 |
| DWC filter-based default | Reverted to campaign-based | [PR #14678], [PR #14790] | 6.0.0 |

## 6. Maintainer norms for this area
- Privacy-sensitive tracking is configurable and defaults to safe: fingerprinting opt-in, IP tracking opt-in, and later removal of features that "are a trap" [PR #3279] [PR #3196] [PR #8428].
- Removing tracking options is a BC break: it waits for a major and goes in UPGRADE-x.md [PR #6701] [PR #8428] [PR #14974].
- Default-value and behaviour changes do not go into patch releases. A default change that fails the API-library tests is reverted, because those tests gate releases [PR #14678] [PR #14790].
- Stats tables are huge: avoid COUNT, temp tables, large IN lists and foreign-key rewrites; bound data migrations with index-friendly `WHERE` clauses [PR #1036] [PR #2374] [PR #6046] [PR #10116].
- Fresh and upgraded schemas must match, including `ON DELETE` [PR #3509].
- Anonymous public endpoints (`/mtc/event`, `/dwc`) use the cache, not the session [PR #13459] [PR #13464].
- Expected bot and scanner noise is logged at WARNING. When only a symptom is patched, the issue stays open [PR #16893] [PR #10444].
- Hosted-only behaviour sits behind a flag that is off in community config [PR #16130].
- Test tracking in a private window on a publicly reachable page; 127.0.0.1 is on the do-not-track list [PR #4395] [PR #8205] [PR #15529].
- Wording: marketer-friendly labels, active voice, no links in tooltips, and wide terminology changes only after community consultation [PR #611] [PR #13436] [PR #14891] [PR #13502].
- Parsing logic (trackables, URLs) needs unit tests with every change [PR #4028] [PR #11644].

## 7. Open questions and conflicts
- Conflict, UTM uniqueness: [PR #9265] (and [PR #2642] earlier) say UTM tags are recorded only on a contact's first visit to a URL. 7.x writes a `lead_utmtags` row on every recorded hit whose query has a `utm_` key; behaviour.md wins [code: app/bundles/PageBundle/Model/PageModel.php:680,1055-1097 @7.x].
- Conflict, bot ratio scope: [PR #14593] describes bot filtering for page hits in general. In 7.x `hitPage` applies it only when `ct` carries an email stat; other hits rely on the do-not-track lists [code: app/bundles/PageBundle/Model/PageModel.php:427-433 @7.x].
- Conflict, redirect codes: [PR #10152] hard-coded 301 and 302. 7.x offers 301/302/303/307/308; the PR that added the rest is not in the inputs [code: app/bundles/PageBundle/Form/Type/RedirectListType.php:19-25 @7.x].
- Gated video was removed in 6.0.0, but no PR in this area's inputs removes it. `vimeo-froogaloop2` is still built and `hitVideoAction` and the `video_hits` report remain [PR #12051] [code: app/bundles/PageBundle/Controller/PublicController.php:547-561 @7.x].
- After [PR #14974], a custom `ct` that carries only `lead` may no longer identify anyone; the reviewer could not find where it is handled.
- Public preview defaults to true in 7.x; it is not stated what pre-7.0 pages got on migration [PR #14766].
- Corrupt `ct` values from scanners: root cause unknown (issue mautic/mautic#9400) [PR #10444].
- Unique clicks from mobile mail apps may still double-count [PR #4293].
- "Show focus item" and "Send tracking event" need synchronous hit processing; with an async `hit` transport they may not show [PR #4666] [PR #13459].
- Whether 6.x had partial IP masking or `*.*.*.*` was debated; 7.x stores `*.*.*.*` [PR #10116].
- The null `page_hits` root cause is unknown, and validation is off in community installs [PR #16130].
- `mtc.js` has no stated deprecation plan after the split [PR #16660].

## 8. Coverage
- Area total: 338 PRs across 4 chunks (120, 79, 79, 60); 302 substantive (113, 75, 64, 50), the rest noise, refactor-only, test-only or unclear. 869 noise PRs were excluded upstream before chunking. [PR #1582] [PR #17671]
- Chunk header dates were wrong in places, so items are dated by merge date and release tag. [PR #3894] [PR #12751]
