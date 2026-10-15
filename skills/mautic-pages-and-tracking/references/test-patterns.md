# Test patterns: landing pages, tracking, dynamic web content

## Base classes and fixtures
- Functional (real DB, `$this->client`, `$this->em`): `Mautic\CoreBundle\Test\MauticMysqlTestCase`. [code: app/bundles/PageBundle/Tests/Functional/Model/PageModelTest.php @7.x]
- Unit: `PHPUnit\Framework\TestCase`; `Mautic\PageBundle\Tests\PageTestAbstract` builds a `PageModel` with mocks (used by `Tests/Model/PageModelTest.php`, `RedirectModelTest.php`). [code: app/bundles/PageBundle/Tests/PageTestAbstract.php @7.x]
- Others: `AbstractReportSubscriberTestCase`, `AbstractProjectSearchTestCase`, `SearchScopeProviderTestCase`, `ConstraintValidatorTestCase`. [code: app/bundles/PageBundle/Tests @7.x]
- Fixtures: `PageBundle/DataFixtures/ORM/LoadPageCategoryData.php`, `LoadPageData.php` (references `page-{n}`), `LoadPageHitData.php`. [code: app/bundles/PageBundle/Config/services.php:23-28 @7.x]
- Browser (Codeception): `tests/acceptance/MauticScriptSplitCest.php` with `tests/_data/mautic-script-split.html`; `GrapesJsBuilderPageCest.php`. No Codeception coverage for DWC. [code: tests/acceptance/MauticScriptSplitCest.php @7.x]

## Representative tests to copy (all under app/bundles/)

| Area | Test | What it shows |
|---|---|---|
| Hit recording | `PageBundle/Tests/Functional/Model/PageModelTest.php` | hits with field values, bot filtering via email stat `ct`, redirect hits; `ct` payload shape (:111-120) |
| Hit query | `PageBundle/Tests/Model/PageModelTest.php` | `testGetHitQueryRequest`, `testGetHitQueryRedirect`, `testNoClickThroughInQuery`, timezone, transliteration, clean query |
| `/mtc/event` | `PageBundle/Tests/Controller/PublicControllerTest.php` | `testMtcTrackingEvent`, `testTrackingActionWithInvalidCt`, `testAssetRedirectUrlWithClickThrough`, `testVariantPageWeightsAreAppropriate` |
| Pixel, XSS | `PageBundle/Tests/Controller/PublicControllerFunctionalTest.php` | `testTrackingImageAction`, `testContactTrackingTagsXss`, `testMtcEventCompanyXss` |
| Redirects | `PageBundle/Tests/Controller/PublicControllerRedirectTest.php`, `PageControllerSqlRollbackFunctionalTest::testRedirectNotPersistClickthrough` | `/r/{id}` |
| Cookies | `PageBundle/Tests/Functional/Model/PageHitCookieTest.php`, `Tests/Controller/DeviceTrackingServiceClearCookiesTest.php` | `mautic_referer_id`/`date_left`; cookie clearing |
| IP anonymisation | `PageBundle/Tests/Controller/VisitPageWitIpAnonymizationOnFunctionalTest.php` / `...OffFunctionalTest.php` | `*.*.*.*` |
| UTM | `PageBundle/Tests/Controller/PageControllerTest::testLandingPageWithUtmTracking` | `lead_utmtags` from a landing-page visit |
| Link rewriting | `PageBundle/Tests/Model/TrackableModelTest.php`, `TrackableModelFunctionalTest::testDisableTrackingAttributeWorks` | 20 rewriting cases |
| URL matching | `PageBundle/Tests/EventListener/CampaignSubscriberTest.php`, `Tests/Helper/PointActionHelperFunctionalTest.php` | Visits a page; url.hit |
| Pages | `PageBundle/Tests/Controller/PageDraftFunctionalTest.php`, `PreviewFunctionalTest.php`, `PageControllerFunctionalTest::testOptimisticLock`, `Tests/Entity/PageRepositoryFunctionalTest::testResetVariants`, `Tests/EventListener/DetermineWinnerSubscriberTest.php` | drafts, preview, locking, variants |
| Preference centre | `PageBundle/Tests/EventListener/PreferencePageTest.php`, `Tests/Functional/EventListener/BuilderSubscriberTest::testUnsubscribeFormRendersPreferenceCenterPageCorrectly` | slot rendering |
| Script scopes | `PageBundle/Tests/Unit/EventListener/BuildJsSubscriberTest.php`, `DynamicContentBundle/Tests/Unit/EventListener/BuildJsSubscriberTest.php`, `PageBundle/Tests/Functional/Controller/TrackingConfigTest.php` | JS composition |
| 404 | `PageBundle/Tests/Model/Tracking404ModelTest.php`, `Tests/Controller/NotFoundFunctionalTest::testCustom404Page` | |
| DWC | `DynamicContentBundle/Tests/Controller/DynamicContentApiControllerFunctionalTest.php`, `DynamicContentControllerFunctionalTest.php`, `Tests/Unit/Helper/DynamicContentHelperTest.php`, `Tests/Validator/Constraints/SlotNameTypeValidatorTest.php`, `Tests/Functional/DynamicContentCloneTest.php` | `/dwc/{slot}`, validation, filters |

[code: app/bundles/PageBundle/Tests @7.x] [code: app/bundles/DynamicContentBundle/Tests @7.x]

## Environment facts that affect tests
- `/mtracking.gif` returns an empty 200 in `test`; assert on DB rows. [code: app/bundles/PageBundle/Controller/PublicController.php:393-398 @7.x]
- The default `hit` transport is `sync://`, so `processPageHit` runs inside the request; a test that configures an async transport must consume the message before asserting enrichment. [code: app/bundles/MessengerBundle/Config/config.php:8 @7.x]
- Requests from a logged-in admin client are not tracked; use an anonymous client (or log out) for hit tests. [code: app/bundles/PageBundle/Model/PageModel.php:410-412 @7.x]
- Loopback/private IPs are untrackable unless `track_private_ip_ranges` is true or a public `REMOTE_ADDR`/`HTTP_X_FORWARDED_FOR` is supplied in server params [unverified how the test env sets this]. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:56,65-98 @7.x]
- `DNT: 1` or `Sec-GPC: 1` server headers make the request untrackable, which is the cheapest negative test. [code: app/bundles/CoreBundle/Helper/IpLookupHelper.php:276-309 @7.x]

## Skeleton: functional hit test

```php
<?php
namespace Mautic\PageBundle\Tests\Functional;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\PageBundle\Entity\Hit;

final class TrackingPixelUtmFunctionalTest extends MauticMysqlTestCase
{
    public function testPixelHitStoresUtmAndUrl(): void
    {
        $this->logoutUser(); // tracking ignores logged-in users

        $this->client->request('GET', '/mtracking.gif', [
            'page_url'   => 'https://example.com/pricing?utm_source=news&utm_campaign=spring',
            'page_title' => 'Pricing',
        ]);
        $this->assertResponseIsSuccessful();

        $hit = $this->em->getRepository(Hit::class)->findOneBy([], ['id' => 'DESC']);
        $this->assertNotNull($hit);
        $this->assertSame('https://example.com/pricing?utm_source=news&utm_campaign=spring', $hit->getUrl());
        $this->assertSame('news', $hit->getQuery()['utm_source']);
        // also assert a lead_utmtags row exists for $hit->getLead()
    }
}
```
The pattern (anonymous request → assert `page_hits` → assert side tables) follows `PageControllerTest::testLandingPageWithUtmTracking` and `PublicControllerFunctionalTest::testTrackingImageAction`; `logoutUser()` is defined on `AbstractMauticTestCase`. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:135 @7.x] [code: app/bundles/PageBundle/Tests/Controller/PublicControllerFunctionalTest.php:27 @7.x]

## Skeleton: link rewriting unit test
Copy a case from `TrackableModelTest.php`: build the model with mocked `RedirectModel`, call `parseContentForTrackables($html, [], 'email', 1)`, and assert `{trackable=...}` replaced `href` values and that `data-mautic-disable-tracking="true"` links are unchanged. [code: app/bundles/PageBundle/Tests/Model/TrackableModelTest.php @7.x]

## What a good regression test asserts
- The hit row: `url`, `url_title`, `code`, `source`/`source_id`, `lead_id`, `tracking_id`.
- The Contact: field values only for publicly-updatable fields; tags added/removed; Company link if sent.
- Side tables: `lead_utmtags`, `channel_url_trackables` counters, `dynamic_content_stats`.
- Response: status, JSON keys (`success`, `id`, `sid`, `device_id`, `events`), and cookies (`mautic_device_id`, `mtc_id`, `mautic_referer_id`, `Blocked-Tracking`).
- Negative paths: logged-in user, `DNT: 1`, bot UA, invalid `ct` (must not 500).
