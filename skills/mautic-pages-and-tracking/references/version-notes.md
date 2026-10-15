# Version notes: landing pages, tracking, dynamic web content

## History that explains current behaviour
- JS tracking (`mtc.js`) has been the primary method since Mautic 1.4. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-script-javascript]
- Mautic 2.2.0 started placing the Contact-id cookie on domains embedding `mtc.js` (CORS required). [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/contacts.html#contact-tracking]
- Third-party `mtc_id` was deprecated in 2.13 in favour of `mautic_device_id`; `mautic_session_id` was deprecated in 2 and removed in 3; 7.2.1 only reads the legacy scheme for migration. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#cookies-used-by-mautic] [code: app/bundles/LeadBundle/Tracker/Service/ContactTrackingService/ContactTrackingService.php:29-75 @7.x]
- The GrapesJS builder arrived in Mautic 3 and became default in Mautic 4. [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#email-landing-page-builder]
- The v1 theme path (`content` array + theme `page.html.twig`) was marked "BC support to be removed in 3.0" but is still present in 7.2.1. [code: app/bundles/PageBundle/Controller/PublicController.php:250-274 @7.x]
- Fingerprint-based tracking (`track_by_fingerprint`) no longer exists (7.2.1 still declares the unused key; the 7.x branch removes it after 7.2.1, unreleased [PR #17671]); only `timezone_offset`/`timezone` remain from that data. [code: app/bundles/PageBundle/Config/config.php:93-107 @7.x]
- Earlier majors: 3.0 removed fingerprint identification and fingerprintjs2 [PR #8428]; 3.2 stopped transliterating page titles by default (`transliterate_page_title`) [PR #9026]; 4.0 added the custom 404 page and UTM capture from every page hit [PR #9813] [PR #9265]; 4.1 added `do_not_track_404_anonymous` [PR #7614]. Full history: pr-history.md.

## 5.x
- 5.0 removed `index_dev.php`; debug mode comes from `APP_ENV`/`APP_DEBUG` in `.env.local`. [PR #12206]
- 5.0 converted the DWC and page UIs to Twig; custom PHP template overrides stop working. [PR #11979]
- 5.0: gated video accepted YouTube/Vimeo iframe embeds (the feature was removed in 6.0). [PR #12051]
- 5.0: `mailto:` and `<area>` links became trackables, and replacement runs longest URL first, case-insensitively. [PR #11481] [PR #11391] [PR #11948]
- 5.1: `TrackingHelper` and campaign DWC keep state in the cache, not the PHP session, so `/mtc/event` and `/dwc/{slot}` set no session cookie. [PR #13459] [PR #13464]
- 5.1: turning on Anonymize IP anonymises existing IP rows and audit-log IPs, irreversibly. [PR #10116]
- 5.1: the variations preview requires a logged-in user with view permission. [PR #11719]
- 5.1: unpublished pages honour their 301/302 redirect; the preference-centre form wraps every field (CSRF fix); DWC gained the segment-membership filter and primary-company fields. [PR #10152] [PR #11442] [PR #13526] [PR #13393]
- 5.1: "Published" reads "Available for use" on content items. [PR #13502]
- 5.2: the custom 404 page is rendered at the missing URL with status 404 instead of a redirect plus 200. [PR #14286]
- 5.2: `&amp;` in query strings is matched for click tracking. [PR #13858]

## 6.x
- 6.0 added bot-ratio filtering for opens and email-click hits (`bot_helper_blocked_ip_addresses`, `bot_helper_blocked_user_agents`, `bot_helper_time_email_threshold` = 2, `bot_helper_bot_ratio_threshold` = 0.6). [PR #14593] [code: app/bundles/EmailBundle/Config/config.php:214-221 @7.x]
- 6.0 refuses a redirect type without a redirect URL and no longer prepends `http://`; legacy invalid pages return 404. [PR #14551]
- 6.0: the preference page language is contact locale, then page language, then user and system locale. [PR #14370]
- 6.0 removed deprecated PageBundle parts (`PagePublishDatesType`, `TrackingHelper`/`PageModel` methods, `MauticFactory::getTheme`). [PR #14244] [PR #14443]
- 6.0: gated video was removed (present in 5.2.9, absent from 6.0.0-alpha); the removing PR is not in this area's inputs. [code: app/bundles/CoreBundle/Command/GenerateProductionAssetsCommand.php:113,189 @7.x]
- 6.0: the filter-based DWC default was added and reverted before release; new DWC stays campaign-based. [PR #14678] [PR #14790]
- 6.0.3: a `Blocked-Tracking` cookie no longer causes a 500. [PR #15102]

## 7.x
- 7.0 removed "Identify visitor by tracking URL" (`track_by_tracking_url`, BC break); `ct` identification runs through `LeadEvents::ON_CLICKTHROUGH_IDENTIFICATION`. [PR #14974]
- 7.0 added page drafts (`page_draft_enabled`, default false), the public-preview toggle (`publicPreview` defaults to true), DWC Text/HTML type, the DWC no-nesting rule and the page-hit Time Spent report column. [PR #13937] [PR #14766] [PR #14759] [PR #14744] [PR #15141]
- 7.0: redirect URLs are trimmed, query strings keep `%20`, and a malformed `ct` is stripped instead of causing a 500. [PR #14958] [PR #15336] [PR #15567]
- 7.1 added `data-mautic-disable-tracking`, `append_segment_id_tracking_url` and optimistic locking for pages; dots in query keys survive redirects. [PR #15713] [PR #15746] [PR #15774] [PR #15725]
- 7.2 applied `UrlMatcher` substring matching to every URL filter, added `validate_page_hit_required_data` (default false), `UrlTokenReplaceEvent` and `PAGE_ON_TOGGLE_PUBLISH`, and logs an undecodable `ct` at WARNING. [PR #15979] [PR #16130] [PR #16199] [PR #16244] [PR #16893]
- 7.2.0 shipped the split scripts: the `/mautic-essential.js` and `/mautic-tracking.js` routes exist in 7.2.0 but not in 7.1.0. [PR #16660] [code: app/bundles/CoreBundle/Config/config.php:36-48 @7.x]
- In 7.2.1 page hits are processed through the Messenger `hit` transport (`PageHitNotification`, default `sync://`). [code: app/config/config.php:111-124 @7.x] [code: app/bundles/MessengerBundle/Config/config.php:8 @7.x]
- 7.x deprecated the `mautic:disable-tracking` attribute (removal in 8.0) in favour of `data-mautic-disable-tracking="true"`. [code: app/bundles/PageBundle/Model/TrackableModel.php:740 @7.x]
- 7.x deprecated positional `$shortenUrl`/`$utmTags` in `RedirectModel::generateRedirectUrl`. [code: app/bundles/PageBundle/Model/RedirectModel.php:60-68 @7.x]
- 7.2: split scripts `/mautic-essential.js` + `/mautic-tracking.js`, `BuildJsScope`, `appendJsForScope`, `acceptsScope`, consent snippet; `/mtc.js` unchanged. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#generated-scripts-and-endpoints] Which 7.x minor first shipped the split is not stated beyond the 7.2 docs branch. [devdocs: https://devdocs.mautic.org/en/7.2/mauticjs_api/tracking_script.html#script-scopes-and-split-scripts]
- 7.2: preference-centre slot labels customisable via `PAGE_ON_DISPLAY` params. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/landing_pages.html#customizing-preference-center]
- 7.2: service alias `mautic.form.type.dwc_entry_filters` deprecated. [code: app/bundles/DynamicContentBundle/Config/services.php:29-30 @7.x]

## 8.x delta (8.x @ 11599729491; 7.2.1 work not yet merged forward)
- Event dispatch by class. Re-key subscribers:
  - `CoreEvents::BUILD_MAUTIC_JS` → `BuildJsEvent::class` (`CoreEvents` class deleted). [devdocs: https://devdocs.mautic.org/en/8.0/mauticjs_api/tracking_script.html]
  - `PageEvents::PAGE_ON_BUILD` → `PageBuilderEvent::class`, `PAGE_ON_DISPLAY` → `PageDisplayEvent::class` (constants removed; `PageDisplayEvent` final). [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/landing_pages.html] [PR #17203] [PR #17638]
  - `PAGE_ON_HIT`, `VIDEO_ON_HIT`, `REDIRECT_DO_NOT_TRACK`, `ON_REDIRECT_GENERATE`, `ON_CONTACT_TRACKED` constants still exist but are dispatched only as `PageHitEvent`, `VideoHitEvent`, `UntrackableUrlsEvent`, `RedirectGenerationEvent`, `TrackingEvent` — a string-keyed listener loads and silently never fires. [PR #17097]
  - DWC: `TOKEN_REPLACEMENT` → `TokenReplacementEvent`, `ON_CONTACTS_FILTER_EVALUATE` → `ContactFiltersEvaluateEvent`; CRUD names unchanged; duplicate `CATEGORY_*` constants removed. [PR #17691] [PR #17198]
  - `PAGE_ON_TOGGLE_PUBLISH` stays string-keyed (shared `PageEvent`); `UrlTokenReplaceEvent::class` unchanged. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/landing_pages.html#toggle-available-for-use-event]
- Campaign actions: `ON_CAMPAIGN_TRIGGER_ACTION` removed; `tracking.pixel.send` and `dwc.push_content` run as batch actions on `PendingEvent` (`ON_CAMPAIGN_BATCH_ACTION`). [PR #17097] [PR #17691]
- `mautic:disable-tracking` is no longer honoured (links get tracked). [PR #17066]
- Landing pages with empty `customHtml` no longer fall back to v1 theme `content` rendering; `PublicController::indexAction()` lost the `ThemeHelper` argument. [PR #17078]
- API changes: `RedirectModel::generateRedirectUrl($redirect, $clickthrough)` only (call `applyUtmTags()`, `shortenUrl()` yourself); `HitRepository::getHitCountForSource()` removed; `Page::getContent(): ?array`, `getCloneObjectId(): ?int`, `getPublicPreview(): ?bool`. [PR #17203]
- `IdentifyCompanyHelper` becomes an autowired service with instance methods (affects hit-time Company identification code). [PR #17260]

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
