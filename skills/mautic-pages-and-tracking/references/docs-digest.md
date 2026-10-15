# Docs digest: landing pages, tracking, dynamic web content

What docs.mautic.org (user docs, 7.2) and devdocs.mautic.org (developer docs, 7.2) say. Where code disagrees, the discrepancy section states the 7.2.1 behaviour.

## Terminology (from the docs)
- Capitalised product nouns: Landing Page, Dynamic Web Content (also "Dynamic Content"), Focus Item, Campaign Decision, Contact, Segment, Tag, Preference Center. [docs: https://docs.mautic.org/en/7.2/components/landing_pages.html]
- The Landing Page status toggle is **Available for use**. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#toggle-available-for-use-event]
- "Visitor" (formerly "anonymous lead") is an unidentified tracked Contact; `is:anonymous` lists them. [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]
- "UTM tags" in prose; groups "inbound capture", "outbound tagging", "targeting", "display". [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_overview.html#feature-groups]
- "MauticJS" / `mtc.js` for the tracking script. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html]

## Tracking script and pixel (user docs)
- JS tracking (`mtc.js`, `mt('send','pageview')`) is the primary method since Mautic 1.4; place it before `</body>`; it tracks title, language, referrer and URL and loads asynchronously. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-script-javascript]
- Install: Settings > Configuration > Tracking Settings, copy the code, configure CORS. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-script-javascript]
- `mt()` accepts `onload`/`onerror` callbacks as the fourth argument. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#mt-events]
- Custom parameters: Contact fields, `tags`, UTM fields; Company via `company` or `companyname` plus `companyemail`, `companyaddress1`, …, `companydescription`. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-of-custom-parameters]
- Fields update only if publicly editable; values must be URL-encoded. `tags=ProductA,-ProductB` adds/removes. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#updating-contact-fields] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tags]
- Pixel `https://example.com/mtracking.gif` relies on third-party cookies; the script with CORS is recommended. Pixel params: `page_url`, `referrer`, `language`, `page_title` (`url`, `title` deprecated because they clash with Contact fields). [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-pixel] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#page-information]
- PHP can send a `d=` urlencoded base64 serialized array. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#php-snippet]
- With CORS allowing the embedding domain, Mautic sets a first-party `mtc_id`; CORS domains need the protocol, list http and https and each subdomain; `http://*.example.com` is allowed. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#local-contact-cookie-first-party-cookie]
- Script tracking: Mautic looks for `mautic_device_id` on its domain, returns Contact id, device id and legacy session id (= device id), stored in local storage and first-party cookie. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#how-are-contacts-tracked-with-the-tracking-script]
- Cookie table: `mautic_device_id` (1 year), `mtc_id` (session), `mautic_referer_id` (session, last page), `mtc_sid` (deprecated), `mautic_session_id` (removed in 3). [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#cookies-used-by-mautic]
- "Identify visitors by tracking URL" identifies returning visitors from channel tracking URLs; not recommended (spoofing); needs Email as a publicly editable unique identifier. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#identify-visitors-by-tracking-url]
- Logged-in Mautic users are not tracked; private-network traffic needs `track_private_ip_ranges`. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#website-monitoring]
- Bot, monitoring and privacy opt-out traffic is filtered automatically. "Do Not Track 404 error for anonymous Contacts" stops 404 tracking. [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]
- Mobile apps: named screens as `page_url`, Email as publicly editable unique identifier, reuse the cookie. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#mobile-monitoring]
- GA ID and Facebook Pixel ID live in Tracking Settings (GA USERID, FB Advanced Matching); campaign action **Send tracking event** requires a **Visits a page** decision right before it. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#google-analytics-and-facebook-pixel-tracking-support] [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#campaign-action-send-tracking-event]

## Tracking script (developer docs)
- Inject JS with a `CoreEvents::BUILD_MAUTIC_JS` listener (priority > -255) using `appendJs()` (TRACKING) or `appendJsForScope($js, BuildJsScope $scope, $section)`; native JS only. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#mtc-js]
- Scopes: RUNTIME (bootstrap), ESSENTIAL (pre-consent: DWC fallback, forms in fallback), TRACKING (identity, pixel, `/mtc/event`). [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#script-scopes-and-split-scripts]
- Globals `MauticJS.runtimeReady`, `trackingEnabled`, `requestWithCredentials`; `mauticEssentialReady` is dispatched by the shipped loader snippet, not by the script. Check `runtimeReady` first, else listen for the event. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#client-side-runtime-globals]
- `ON_CONTACT_TRACKED` + `$event->getResponse()->set(key, value)` → `detail.response.events.<key>` in `mauticPageEventDelivered`. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#hooking-into-the-tracking-process-and-returning-custom-responses]
- MauticJS API: `serialize`, `documentReady`, `iterateCollection`, `log`, `createCORSRequest`, `makeCORSRequest(method, url, data, success, error)`, `parseTextToJSON`, `insertScript`; example fetches `/dwc/slot1`. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#mauticjs-api-functions]
- Form JS callbacks (`MauticFormCallback[formName]`) are covered in mautic-forms. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#javascript-form-processing-hooks]

## Landing pages
- Drafts need `'page_draft_enabled' => 1` in local.php, then **Save as Draft** appears; one draft per page; with a draft the buttons are **Apply Draft** and **Discard Draft**; draft preview = preview URL + `/draft`. [docs: https://docs.mautic.org/en/7.2/components/landing_pages.html#creating-a-draft-landing-page] [docs: https://docs.mautic.org/en/7.2/components/landing_pages.html#previewing-a-draft-landing-page]
- Forms embed with `{form=ID}`; page links with `{pagelink=ID}`; default theme in Theme Settings; changing theme after building may hide content. [docs: https://docs.mautic.org/en/7.2/components/forms.html#shortcodes] [docs: https://docs.mautic.org/en/7.2/themes/manage_themes.html#assigning-a-default-theme]
- The user docs page is nearly empty: nothing on A/B variants, translations, preference-centre slots, SEO fields, redirect type, preview URLs or hits. Use behaviour.md for those.

## Landing pages (developer docs)
- Extend with tokens and A/B winner criteria on `PAGE_ON_BUILD` (`addToken`, `addAbTestWinnerCriteria($key, ['group','label','callback'])`, callback gets `Page $page`, `Page $parent`, `$children`); replace tokens on `PAGE_ON_DISPLAY`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#page-a-b-test-winner-criteria]
- `UrlTokenReplaceEvent` (`getContent`, `setContent`, `getLead`, `getEmailId`) lets plugins replace tokens in redirect targets; core handles `{contactfield=…}`; test with `LeadBundle\Helper\TokenHelper::REGEX` and `urlencode()` values. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#url-token-replacement]
- Since 7.2, preference-centre slot labels can be set in a `PAGE_ON_DISPLAY` listener (priority 100 in the example, guard `getIsPreferenceCenter()`). [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#customizing-preference-center]
- `PAGE_ON_TOGGLE_PUBLISH` fires before persisting the **Available for use** toggle; `isPublished()` is the pre-toggle state. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#toggle-available-for-use-event]

## Dynamic Web Content
- Website slot: `<div data-slot="dwc" data-param-slot-name="myslot">default</div>`; Joomla `{mautic type="content" slot="x"}...{/mautic}`; WordPress `[mautic type="content" slot="x"]...[/mautic]`. [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#website-configuration]
- CORS must be configured or content won't display. [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#mautic-configuration]
- Fields: Internal name, Content (tokens `{contactfield=}`, `{pagelink=}`, `{assetlink=}`, `{form=}`, `{focus=}`), Category, Language, translation parent, Published, Is Campaign based, Requested slot name, publish dates, UTM tags. [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#creating-dynamic-web-content-slots]
- Campaign-based: decision **Request Dynamic Content** (slot name, default content) → conditions → action **Push Dynamic Content**; default may show before the push. [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#campaign-based-dynamic-web-content]
- Filter-based (Is Campaign based = No) shows a Filters tab and does not depend on campaign cron. [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#filter-based-dynamic-web-content]
- DWC UTM fields are appended to every trackable link in the block; they do not filter who sees it. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_dynamic_web_content.html]

## UTM
- Inbound capture reads UTM already in the URL; Mautic never adds them. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_overview.html#inbound-capture-recording-utm-data]
- Landing-page and tracking-script visits store UTM automatically; Landing Pages have no UTM settings. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_landing_pages.html]
- Pixel UTM params create a timeline entry titled by `utm_campaign`, icon by `utm_medium`. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#utm-code]
- Hard-coded UTM in Email/DWC links may get a second set appended. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_emails.html#configure-email-utm-tags]

## Procedures
- Test tracking: open the site in a private window (logged-in users are not tracked), check `/mtc/event` returns `success:1`, then look for the Visitor with `is:anonymous`. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#website-monitoring] [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads]
- Test GA/FB events: Tag Assistant / Pixel Helper; campaign with Visits a page + Send tracking event; expect one pageview and one event. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#how-to-test-google-analytics-tracking-code-and-campaign-action]
- Campaign DWC: slot on website → DWC with Is Campaign based = Yes → campaign Request Dynamic Content → Push Dynamic Content. Filter DWC: Is Campaign based = No, slot name and filters, default content on the page. [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#campaign-based-dynamic-web-content]

## Doc/code discrepancies (7.x code wins)
- UTM "only on Record UTM Tags form action" (manage_contacts) is wrong: every recorded hit with `utm_*` in its query writes `lead_utmtags`. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#utm-code] [code: app/bundles/PageBundle/Model/PageModel.php:680,1055-1097 @7.x]
- UTM pages say "Known Contacts"; code records UTM for anonymous Visitors too. [docs: https://docs.mautic.org/en/7.2/utm_tags/utm_tags_landing_pages.html] [code: app/bundles/PageBundle/Model/PageModel.php:460-463 @7.x]
- "Cookies last 1 year": only the server-written `mautic_device_id`; `mtc_id` and JS-written copies are session cookies. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-script-javascript] [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:119-136 @7.x]
- `mautic_referer_id` is documented as session; code sets 1800 s. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#cookies-used-by-mautic] [code: app/bundles/PageBundle/Model/PageModel.php:482-488 @7.x]
- Devdocs contact tracking (`mautic_session_id`, 30-minute session cookie) describes the pre-2.13 scheme; 7.2.1 only reads it. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/contacts.html#contact-tracking] [code: app/bundles/LeadBundle/Tracker/Service/ContactTrackingService/ContactTrackingService.php:29-75 @7.x]
- Landing-page draft docs mention "Subject" and "selected Segment"; pages have neither; only HTML/template are drafted. [docs: https://docs.mautic.org/en/7.2/components/landing_pages.html#creating-a-draft-landing-page] [code: app/bundles/PageBundle/EventListener/PageSubscriber.php:136-176 @7.x]
- DWC docs say the translation is chosen by browser language; code picks the Contact's translation via `TranslationModelTrait` (preferred locale first, then browser language). [docs: https://docs.mautic.org/en/7.2/components/dynamic_web_content.html#creating-dynamic-web-content-slots] [code: app/bundles/CoreBundle/Model/TranslationModelTrait.php:21-131 @7.x]
- Docs say privacy opt-out traffic is filtered; in code that means the `DNT: 1` / `Sec-GPC: 1` request headers, not the `do_not_track` param the script sends. [docs: https://docs.mautic.org/en/7.2/contacts/contacts_overview.html#visitors-formerly-anonymous-leads] [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:276-309 @7.x]
