# Version notes: landing pages, tracking, dynamic web content

## History that explains current behaviour
- JS tracking (`mtc.js`) has been the primary method since Mautic 1.4. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#tracking-script-javascript]
- Mautic 2.2.0 started placing the Contact-id cookie on domains embedding `mtc.js` (CORS required). [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/contacts.html#contact-tracking]
- Third-party `mtc_id` was deprecated in 2.13 in favour of `mautic_device_id`; `mautic_session_id` was deprecated in 2 and removed in 3; 7.2.1 only reads the legacy scheme for migration. [docs: https://docs.mautic.org/en/7.2/contacts/manage_contacts.html#cookies-used-by-mautic] [code: app/bundles/LeadBundle/Tracker/Service/ContactTrackingService/ContactTrackingService.php:29-75 @7.x]
- The GrapesJS builder arrived in Mautic 3 and became default in Mautic 4. [docs: https://docs.mautic.org/en/7.2/builders/email_landing_page.html#email-landing-page-builder]
- The v1 theme path (`content` array + theme `page.html.twig`) was marked "BC support to be removed in 3.0" but is still present in 7.2.1. [code: app/bundles/PageBundle/Controller/PublicController.php:250-274 @7.x]
- Fingerprint-based tracking (`track_by_fingerprint`) no longer exists (7.2.1 still declares the unused key; the 7.x branch removes it after 7.2.1, unreleased [PR #17671]); only `timezone_offset`/`timezone` remain from that data. [code: app/bundles/PageBundle/Config/config.php:93-107 @7.x]
- 5.x/6.x: the inputs for this skill record no page/tracking behaviour difference specific to 5.x or 6.x beyond the items listed under 7.x; PR history will be added in a later pass.

## 7.x
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
