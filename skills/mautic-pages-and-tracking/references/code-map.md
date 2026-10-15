# Code map: landing pages, tracking, dynamic web content (Mautic 7.x)

Paths are relative to the repository root; `PageBundle` = `app/bundles/PageBundle`, `DWC` = `app/bundles/DynamicContentBundle`.

## Contents
1. Entities and tables
2. Models, helpers and services
3. Cross-bundle tracking pipeline
4. Events (dispatched and subscribed)
5. Routes and controllers
6. Configuration parameters
7. Permissions
8. Console commands and queues
9. Front-end assets and templates
10. Tests and fixtures

## 1. Entities and tables

| Entity | Table | Key facts | Source |
|---|---|---|---|
| `PageBundle/Entity/Page.php` | `pages` | `title`, `alias` (index `page_alias_search`), `template`, `custom_html`, legacy `content` (array), publish dates, `hits`, `unique_hits`, `variant_hits`, `revision`, `meta_description`, `head_script`, `footer_script`, `redirect_type`, `redirect_url` (2048), category, `is_preference_center`, `no_index`, `public_preview` (default true), `lang`, `translation_parent_id`, `variant_parent_id`, `variant_settings`, `variant_start_date`, `uuid`, `page_projects_xref`, optimistic-lock `version` | [code: app/bundles/PageBundle/Entity/Page.php:69,228-319 @7.x] |
| `PageBundle/Entity/PageDraft.php` | `pages_draft` | one-to-one with Page; `cleanUrlsInContent` lifecycle | [code: app/bundles/PageBundle/Entity/PageDraft.php:17,40-41 @7.x] |
| `PageBundle/Entity/Hit.php` | `page_hits` | bigint id, `date_hit`, `date_left`, FKs `page_id`/`redirect_id`/`email_id`/`lead_id`/`ip_id`/`device_id` (SET NULL), geo columns, `code`, `referer`, `url` (prefix index 128), `url_title` (191), `user_agent`, `remote_host`, `page_language`, `browser_languages`, `tracking_id` (indexed), `source`+`source_id` (indexed), `query` (array); class constraint `PageHit` | [code: app/bundles/PageBundle/Entity/Hit.php:137-293 @7.x] |
| `PageBundle/Entity/Redirect.php` | `page_redirects` | `redirect_id` string(25) random sha1 prefix, `url` text (no unique constraint), `hits`, `unique_hits`, trackables | [code: app/bundles/PageBundle/Entity/Redirect.php:45-130 @7.x] |
| `PageBundle/Entity/Trackable.php` | `channel_url_trackables` | PK (`redirect_id`, `channel_id`), `channel`, `hits`, `unique_hits`; index `channel_url_trackable_search` | [code: app/bundles/PageBundle/Entity/Trackable.php:38-63 @7.x] |
| `PageBundle/Entity/VideoHit.php` | `video_hits` | `guid`, `channel`, `channel_id`, `time_watched`, `duration`, geo/UA columns | [code: app/bundles/PageBundle/Entity/VideoHit.php:135-226 @7.x] |
| `DWC/Entity/DynamicContent.php` | `dynamic_content` | `type` (`html`/`text`), `content`, `utm_tags` JSON, `filters`, `is_campaign_based` (default 1), `slot_name`, `sent_count`, translation/variant columns, `uuid`, projects | [code: app/bundles/DynamicContentBundle/Entity/DynamicContent.php:162-273 @7.x] |
| `DWC/Entity/Stat.php` | `dynamic_content_stats` | `dynamic_content_id`, `lead_id`, `date_sent`, `source`, `source_id`, `tokens` | [code: app/bundles/DynamicContentBundle/Entity/Stat.php:68-96 @7.x] |
| `DWC/Entity/DynamicContentLeadData.php` | `dynamic_content_lead_data` | Contact, DWC, `slot`, `date_added` (last DWC per Contact+slot) | [code: app/bundles/DynamicContentBundle/Entity/DynamicContentLeadData.php:46-61 @7.x] |

Owned by LeadBundle but central here: `lead_devices` (device `tracking_id`), `lead_utmtags` (`LeadBundle/Entity/UtmTag.php`), `ip_addresses`. See mautic-contacts. [code: app/bundles/LeadBundle/Entity/UtmTag.php:78 @7.x]

## 2. Models, helpers and services

| Class | Responsibility | Source |
|---|---|---|
| `PageBundle/Model/PageModel.php` | page CRUD (alias, revision, variants), URL/slug, hit pipeline `hitPage`/`processPageHit`/`getHitQuery`, `setUtmTags`, builder tokens, `convertWinnerVariant`; service `mautic.page.model.page` | [code: app/bundles/PageBundle/Model/PageModel.php:72-76,151-154 @7.x] |
| `PageBundle/Model/RedirectModel.php` | `getRedirectById`, `generateRedirectUrl`, `getRedirectByUrl(s)`, `applyUtmTags`, `shortenUrl` | [code: app/bundles/PageBundle/Model/RedirectModel.php:40-206 @7.x] |
| `PageBundle/Model/TrackableModel.php` | link rewriting for all channels: `parseContentForTrackables`, `generateTrackableUrl`, `getTrackableByUrl`, `getDoNotTrackList` | [code: app/bundles/PageBundle/Model/TrackableModel.php:90-264 @7.x] |
| `PageBundle/Model/VideoModel.php` | `hitVideo` | [code: app/bundles/PageBundle/Model/VideoModel.php:70-150 @7.x] |
| `PageBundle/Model/Tracking404Model.php` | 404 hit recording, `do_not_track_404_anonymous` | [code: app/bundles/PageBundle/Model/Tracking404Model.php:25-43 @7.x] |
| `PageBundle/Model/PageDraftModel.php` | draft create/save/delete | [code: app/bundles/PageBundle/Model/PageDraftModel.php:24-56 @7.x] |
| `PageBundle/Helper/TokenHelper.php` | `{pagelink=ID}` | [code: app/bundles/PageBundle/Helper/TokenHelper.php:9-41 @7.x] |
| `PageBundle/Helper/TrackingHelper.php` | GA/FB config, per-Contact pending pixel events cache (key `mtc-tracking-pixel-events-{leadId}`, 1 day) | [code: app/bundles/PageBundle/Helper/TrackingHelper.php:26-121 @7.x] |
| `PageBundle/Helper/PointActionHelper.php` | `validatePageHit`, `validateUrlHit` | [code: app/bundles/PageBundle/Helper/PointActionHelper.php:17-114 @7.x] |
| `PageBundle/Helper/PageConfig.php` | `isDraftEnabled()` ← `page_draft_enabled` | [code: app/bundles/PageBundle/Helper/PageConfig.php:16-19 @7.x] |
| `PageBundle/Validator/PageHitValidator.php` | required `url`/`url_title` when enabled | [code: app/bundles/PageBundle/Validator/PageHitValidator.php:20-44 @7.x] |
| `DWC/Model/DynamicContentModel.php` | CRUD, `checkEntityBySlotName`, `setSlotContentForLead`, `getSlotContentForLead`, `createStatEntry`, charts; service `mautic.dynamicContent.model.dynamicContent` | [code: app/bundles/DynamicContentBundle/Model/DynamicContentModel.php:53-307 @7.x] |
| `DWC/Helper/DynamicContentHelper.php` | slot resolution, filter evaluation, `{dynamiccontent}`/`{dwc}` handling; service `mautic.helper.dynamicContent` | [code: app/bundles/DynamicContentBundle/Helper/DynamicContentHelper.php:24-253 @7.x] |

Service aliases: `mautic.page.model.{page,redirect,trackable,video,tracking.404}`, `mautic.page.repository.{hit,page,redirect}`, `mautic.page.helper.{token,tracking}`; `mautic.form.type.dwc_entry_filters` deprecated in 7.2. [code: app/bundles/PageBundle/Config/services.php:29-41 @7.x] [code: app/bundles/DynamicContentBundle/Config/services.php:29-30 @7.x]

## 3. Cross-bundle tracking pipeline

| Class | Role | Source |
|---|---|---|
| `CoreBundle/Controller/JsController.php` | builds `/mtc.js`, `/mautic-essential.js`, `/mautic-tracking.js` | [code: app/bundles/CoreBundle/Controller/JsController.php:37-53 @7.x] |
| `CoreBundle/Event/BuildJsEvent.php`, `BuildJsScope.php` | scopes, `appendJs`, `appendJsForScope`, `acceptsScope` | [code: app/bundles/CoreBundle/Event/BuildJsEvent.php:29-81 @7.x] |
| `CoreBundle/EventListener/BuildJsSubscriber.php` | MauticJS runtime + tracking core (cookies, localStorage, `/mtc`) | [code: app/bundles/CoreBundle/EventListener/BuildJsSubscriber.php:42-376 @7.x] |
| `PageBundle/EventListener/BuildJsSubscriber.php` | pageview API `mt()`, delivery, GA/FB pixels | [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php:24-318 @7.x] |
| `DWC/EventListener/BuildJsSubscriber.php` | slot filling | [code: app/bundles/DynamicContentBundle/EventListener/BuildJsSubscriber.php:28-148 @7.x] |
| `LeadBundle/Helper/ContactRequestHelper.php` | Contact from `ct` / query / tracker; merges | [code: app/bundles/LeadBundle/Helper/ContactRequestHelper.php:45-200 @7.x] |
| `LeadBundle/Tracker/ContactTracker.php` | current tracked Contact; `LeadGetCurrentEvent`; `track_contact_by_ip` | [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-293 @7.x] |
| `LeadBundle/Tracker/DeviceTracker.php`, `Service/DeviceTrackingService/DeviceTrackingService.php` | `lead_devices`, `mautic_device_id`/`mtc_id` cookies | [code: app/bundles/LeadBundle/Tracker/Service/DeviceTrackingService/DeviceTrackingService.php:38-136 @7.x] |
| `LeadBundle/Tracker/Service/ContactTrackingService/ContactTrackingService.php` | legacy `mautic_session_id` reader | [code: app/bundles/LeadBundle/Tracker/Service/ContactTrackingService/ContactTrackingService.php:29-75 @7.x] |
| `CoreBundle/Helper/IpLookupHelper.php` | client IP, anonymisation, DNT/bot/IP filters, `isRequestTrackable()` | [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:56-309 @7.x] |
| `CoreBundle/Helper/ClickthroughHelper.php` | `ct` encode/decode | [code: app/bundles/CoreBundle/Helper/ClickthroughHelper.php:12-52 @7.x] |
| `CoreBundle/Helper/CookieHelper.php` | queued cookies, defaults (1800 s, Lax) | [code: app/bundles/CoreBundle/Helper/CookieHelper.php:44-85 @7.x] |
| `CoreBundle/Helper/TrackingPixelHelper.php` | 1×1 GIF | [code: app/bundles/CoreBundle/Helper/TrackingPixelHelper.php:16-59 @7.x] |
| `MessengerBundle/MessageHandler/PageHitNotificationHandler.php` | async hit enrichment | [code: app/bundles/MessengerBundle/MessageHandler/PageHitNotificationHandler.php:35-95 @7.x] |
| `EmailBundle/Helper/UrlMatcher.php` | URL pattern matching for campaigns and points | [code: app/bundles/EmailBundle/Helper/UrlMatcher.php:10-64 @7.x] |
| `EmailBundle/EventListener/TrackingSubscriber.php` | identifies Contact from `ct['stat']` | [code: app/bundles/EmailBundle/EventListener/TrackingSubscriber.php:25-52 @7.x] |

## 4. Events

`PageBundle/PageEvents.php`:

| Constant | Name | Event class | Dispatched | Core listeners |
|---|---|---|---|---|
| `PAGE_ON_HIT` | `mautic.page_on_hit` | `PageHitEvent` | `PageModel.php:709-712` | `CampaignSubscriber`, `PointSubscriber`, `WebhookSubscriber` |
| `VIDEO_ON_HIT` | `mautic.video_on_hit` | `VideoHitEvent` | `VideoModel.php:146-149` | none |
| `PAGE_ON_BUILD` | `mautic.page_on_build` | `PageBuilderEvent` | `PageModel.php:770-771` | `BuilderSubscriber`, `DateTimeTokenSubscriber` |
| `PAGE_ON_DISPLAY` | `mautic.page_on_display` | `PageDisplayEvent` | `PublicController.php:291-292,381-387`; EmailBundle `PublicController.php:410-411`; Notification popup | `TokenSubscriber` (254), DWC `DynamicContentSubscriber` (254), `BuilderSubscriber` (0), `DateTimeTokenSubscriber` (0), `PageSubscriber` (-255) |
| `PAGE_ON_TOGGLE_PUBLISH` | `mautic.page_on_toggle_publish` | `PageEvent` | `PageModel::dispatchEvent` :280-282 | none |
| `PAGE_PRE_SAVE`/`POST_SAVE`/`PRE_DELETE`/`POST_DELETE` | `mautic.page_*` | `PageEvent` | `PageModel.php:268-279` | `PageSubscriber` (audit log, language pack) |
| `REDIRECT_DO_NOT_TRACK` | `mautic.redirect_do_not_track` | `UntrackableUrlsEvent` | `TrackableModel.php:220-223` | none (extension point) |
| `ON_REDIRECT_GENERATE` | `mautic.page.on_redirect_generate` | `RedirectGenerationEvent` | `RedirectModel.php:70-73` | none (extension point) |
| `ON_CONTACT_TRACKED` | `mautic.page.on_contact_tracked` | `TrackingEvent` | `PublicController.php:429-430` | none |
| `ON_CAMPAIGN_TRIGGER_DECISION`/`ACTION` | `mautic.page.on_campaign_trigger_*` | `CampaignExecutionEvent` | CampaignBundle | `CampaignSubscriber` |
| `ON_DETERMINE_BOUNCE_RATE_WINNER` / `DWELL_TIME_WINNER` | `mautic.page.on_*_winner` | `DetermineWinnerEvent` | CoreBundle A/B flow | `DetermineWinnerSubscriber` |

Class-keyed: `PageEditSubmitEvent` (draft workflow, `PageSubscriber::managePageDraft`), `UrlTokenReplaceEvent` (`PublicController.php:517-518`; `SegmentTrackingSubscriber` at -100 and LeadBundle token replacers). [code: app/bundles/PageBundle/PageEvents.php @7.x] [code: app/bundles/PageBundle/EventListener/PageSubscriber.php:37,136-176 @7.x]

`DWC/DynamicContentEvents.php`: `TOKEN_REPLACEMENT` (`mautic.dwc_token_replacement`, `TokenReplacementEvent`), `PRE/POST_SAVE`, `PRE/POST_DELETE` (`mautic.dwc_*`), `ON_CAMPAIGN_TRIGGER_DECISION`/`ACTION` (`mautic.dwc.on_campaign_trigger_*`), `ON_CONTACTS_FILTER_EVALUATE` (`mautic.dwc.on_contact_filters_evaluate`, `ContactFiltersEvaluateEvent`); `CATEGORY_*` constants are never dispatched. [code: app/bundles/DynamicContentBundle/DynamicContentEvents.php @7.x] [code: app/bundles/DynamicContentBundle/Helper/DynamicContentHelper.php:173-175,241-250 @7.x]

Subscribed from other bundles: `CoreEvents::BUILD_MAUTIC_JS`, `CampaignEvents::CAMPAIGN_ON_BUILD`, `PointEvents::POINT_ON_BUILD`, `LeadEvents::TIMELINE_ON_GENERATE|CURRENT_LEAD_CHANGED|LEAD_POST_MERGE`, `EmailEvents::EMAIL_ON_BUILD|ON_SEND|ON_DISPLAY` (`{pagelink}`), `WebhookEvents::WEBHOOK_ON_BUILD`, `ReportEvents::*`, dashboard widgets, global search, `CoreEvents::MAINTENANCE_CLEANUP_DATA`, `ConfigEvents::CONFIG_ON_GENERATE|CONFIG_PRE_SAVE`, `ChannelEvents::ADD_CHANNEL` (DWC channel `dynamicContent`), `LeadEvents::ON_CLICKTHROUGH_IDENTIFICATION`. [code: app/bundles/PageBundle/EventListener @7.x] [code: app/bundles/DynamicContentBundle/EventListener/ChannelSubscriber.php:21-31 @7.x]

## 5. Routes and controllers

| Route | Path | Controller | Source |
|---|---|---|---|
| `mautic_page_index` | `/s/pages/{page}` | `PageController::indexAction` | [code: app/bundles/PageBundle/Config/config.php @7.x] |
| `mautic_page_action` | `/s/pages/{objectAction}/{objectId}` | `PageController::executeAction` (new/edit/view/clone/delete/batchDelete/builder/abtest/winner) | same |
| `mautic_page_results` / `mautic_page_export` | `/s/pages/results/{objectId}/...` | form results on a page | same |
| `mautic_page_tracker` | `/mtracking.gif` | `PublicController::trackingImageAction` | same |
| `mautic_page_tracker_cors` | `/mtc/event` | `PublicController::trackingAction` | same |
| `mautic_page_tracker_getcontact` | `/mtc` | `PublicController::getContactIdAction` | same |
| `mautic_url_redirect` / `mautic_page_redirect` | `/r/{redirectId}` / `/redirect/{redirectId}` | `PublicController::redirectAction` | same |
| `mautic_page_preview` | `/page/preview/{id}/{objectType}` | `PublicController::previewAction` | same |
| `mautic_api_pagesstandard` | `/api/pages` | `Api/PageApiController` (standard entity) | same |
| `mautic_page_public` | `/{slug}` (catch-all) | `PublicController::indexAction` | [code: app/bundles/PageBundle/Config/config.php:68 @7.x] |
| `mautic_js`, `mautic_essential_js`, `mautic_tracking_js` | `/mtc.js`, `/mautic-essential.js`, `/mautic-tracking.js` | `JsController` | [code: app/bundles/CoreBundle/Config/config.php:37-47 @7.x] |
| `mautic_dynamicContent_index` / `_action` | `/s/dwc/...` | `DynamicContentController` | [code: app/bundles/DynamicContentBundle/Config/config.php:23-52 @7.x] |
| `mautic_api_dynamicContent_index` / `_action` (public) | `/dwc`, `/dwc/{objectAlias}` | `DynamicContentApiController` (GET only) | same |
| `mautic_api_dynamicContent_standard` | `/api/dynamiccontents` | `Api/DynamicContentApiController` | same |

`Page` and `DynamicContent` also carry API Platform `#[ApiResource]` attributes (groups `page:read|write`, `dynamicContent:read|write`). [code: app/bundles/PageBundle/Entity/Page.php:36-54 @7.x] [code: app/bundles/DynamicContentBundle/Entity/DynamicContent.php:39-57 @7.x]

AJAX: `PageBundle/Controller/AjaxController.php` `getAbTestFormAction`, `pageListAction`, `getBuilderTokens`. [code: app/bundles/PageBundle/Controller/AjaxController.php:30-63 @7.x]

## 6. Configuration parameters

| Parameter | Default | Effect | Source |
|---|---|---|---|
| `cat_in_page_url` | false | category in landing-page URL | [code: app/bundles/PageBundle/Config/config.php:93-107 @7.x] |
| `google_analytics` | null | raw GA snippet in landing pages (escaped on save) | same |
| `track_contact_by_ip` | false | reuse newest Contact on same IP | same |
| `google_analytics_id`, `google_analytics_trackingpage_enabled`, `google_analytics_landingpage_enabled`, `google_analytics_anonymize_ip` | null/false | gtag in `mtc.js` | same |
| `facebook_pixel_id`, `facebook_pixel_trackingpage_enabled`, `facebook_pixel_landingpage_enabled` | null/false | fbq in `mtc.js` | same |
| `do_not_track_404_anonymous` | false | skip 404 hits for Visitors | same |
| `append_segment_id_tracking_url` | false | `segment_ids=` on redirects | same |
| `validate_page_hit_required_data` | false | `PageHitValidator` | same |
| `anonymize_ip` | (form only) | IP `*.*.*.*` | [code: app/bundles/PageBundle/EventListener/ConfigSubscriber.php:51 @7.x] |
| `anonymize_ip_address_in_background` | false | companion | [code: app/bundles/CoreBundle/Config/config.php:711 @7.x] |
| `page_draft_enabled` | false | landing-page drafts | [code: app/bundles/PageBundle/Helper/PageConfig.php:16-19 @7.x] |
| `cookie_path`, `cookie_domain`, `cookie_secure`, `cookie_httponly` | `/`, '', true, false | tracking cookies | [code: app/bundles/CoreBundle/Config/config.php:297-300 @7.x] |
| `do_not_track_ips`, `do_not_track_bots`, `do_not_track_internal_ips` | [], long UA list, [] | trackability | [code: app/bundles/CoreBundle/Config/config.php:301-693 @7.x] |
| `track_private_ip_ranges` | false | track private IPs | [code: app/bundles/CoreBundle/Config/config.php:694 @7.x] |
| `cors_restrict_domains`, `cors_valid_domains` | — | CORS for `/mtc/event`, `/dwc` | [code: app/bundles/CoreBundle/Config/config.php:702-703 @7.x] |
| `transliterate_page_title` | false | `url_title` transliteration | [code: app/bundles/CoreBundle/Config/config.php:701 @7.x] |
| `bot_helper_bot_ratio_threshold` | 0.6 | email-click bot ratio | [code: app/bundles/EmailBundle/Config/config.php:214 @7.x] |
| `messenger_dsn_hit` | `sync://` | hit transport | [code: app/bundles/MessengerBundle/Config/config.php:8 @7.x] |

Config forms: `Form/Type/ConfigType.php` and `Form/Type/ConfigTrackingPageType.php`, registered by `ConfigSubscriber` (`pageconfig`, `trackingconfig`). [code: app/bundles/PageBundle/EventListener/ConfigSubscriber.php:25-64 @7.x]

## 7. Permissions

- `page:pages:*` (viewown, viewother, editown, editother, create, deleteown, deleteother, publishown, publishother, full), `page:categories:*`, `page:preference_center:*` (needed in addition for preference-centre pages). [code: app/bundles/PageBundle/Security/Permissions/PagePermissions.php:13-31 @7.x]
- `dynamiccontent:dynamiccontents:*`, `dynamiccontent:categories:*`; DWC builder tokens need DWC view permission. [code: app/bundles/DynamicContentBundle/Security/Permissions/DynamicContentPermissions.php:13-31 @7.x]

## 8. Console commands and queues

Neither bundle has commands. Related: `mautic:maintenance:cleanup` (purges anonymous `page_hits`/`lead_utmtags`), `mautic:anonymize:ip`, `messenger:consume hit`. [code: app/bundles/PageBundle/EventListener/MaintenanceSubscriber.php:27-94 @7.x] [code: app/bundles/CoreBundle/Command/AnonymizeIpCommand.php:25 @7.x] [code: app/config/config.php:111-124 @7.x]

## 9. Front-end assets and templates

- Tracking JS is in PHP heredocs in the `BuildJsSubscriber` classes, not in static files. [code: app/bundles/PageBundle/EventListener/BuildJsSubscriber.php @7.x]
- Embed snippet: `PageBundle/Resources/views/FormTheme/Config/_config_trackingconfig_widget.html.twig`. [code: app/bundles/PageBundle/Resources/views/FormTheme/Config/_config_trackingconfig_widget.html.twig:32-85 @7.x]
- `PageBundle/Assets/js/page.js` (admin), `prefcenter.js` (public preference-centre helpers), `WebhookPayload/page_on_hit.json`. [code: app/bundles/PageBundle/Assets @7.x]
- DWC slot snippet generator: `DWC/Resources/views/DynamicContent/StandaloneSlotGenerator/dwc-generator.html.twig`, `DWC/Assets/js/dynamicContent.js:10-120`. [code: app/bundles/DynamicContentBundle/Assets/js/dynamicContent.js:10-120 @7.x]

## 10. Tests and fixtures

- Directories: `PageBundle/Tests/{Controller,Entity,EventListener,Form,Functional,Helper,Model,Unit,Validator}`, `DWC/Tests/{Controller,EventListener,Form,Functional,Unit,Validator}`, `tests/acceptance/MauticScriptSplitCest.php`, `tests/acceptance/GrapesJsBuilderPageCest.php`.
- Fixtures: `PageBundle/DataFixtures/ORM/LoadPageCategoryData.php`, `LoadPageData.php` (`fakepagedata.csv`), `LoadPageHitData.php` (`fakepagehitdata.csv`). [code: app/bundles/PageBundle/Config/services.php:23-28 @7.x]
- See test-patterns.md for the representative list.
