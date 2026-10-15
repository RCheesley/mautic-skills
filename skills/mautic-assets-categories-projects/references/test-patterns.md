# Test patterns — Assets, Categories, Projects

## Base classes and helpers
- `Mautic\CoreBundle\Test\MauticMysqlTestCase` is the base for every functional test. It provides `$this->client`, `$this->em` and `logoutUser()`. [code: app/bundles/AssetBundle/Tests/Asset/AbstractAssetTestCase.php:14 @7.x]
- `Mautic\AssetBundle\Tests\Asset\AbstractAssetTestCase` writes a CSV file into `upload_dir` and persists an `Asset` pointing at it. `createAsset(array)` takes the keys `title`, `alias`, `storage`, `path`, `extension` and `isPublished`. The file is removed in `beforeTearDown()`. [code: app/bundles/AssetBundle/Tests/Asset/AbstractAssetTestCase.php:26-93 @7.x]
- `Mautic\AssetBundle\Tests\RemoteFileServerTrait` starts a local file server for remote-Asset tests. [code: app/bundles/AssetBundle/Tests/RemoteFileServerTrait.php @7.x]
- `Mautic\ProjectBundle\Tests\Functional\AbstractProjectSearchTestCase` provides `createProject($name)` and `searchAndAssert($term, $expected, $unexpected, $routes)`. The routes cover both the UI and `/api/`. [code: app/bundles/ProjectBundle/Tests/Functional/AbstractProjectSearchTestCase.php:16-68 @7.x]
- `SearchScopeProviderTestCase` is the base for the `*SearchScopeProviderTest` unit tests. `RepositoryConfiguratorTrait` covers `AssetRepositoryTest`. `OwnershipScopedApiAuthorizationTestBase` covers the API v2 download ownership test. [code: app/bundles/AssetBundle/Tests/Functional/ApiPlatform/DownloadOwnershipApiV2AuthorizationRegressionTest.php @7.x]
- The fixture `AssetBundle/DataFixtures/ORM/LoadAssetData.php` loads one Asset, `asset1`. [code: app/bundles/AssetBundle/DataFixtures/ORM/LoadAssetData.php:14-34 @7.x]

## Representative tests

| Test | What it covers |
|---|---|
| `app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php` | stream vs attachment, `{id}:{alias}` slug, invalid slug, unpublished (403), remote 302, missing file 404, robots header, UTM |
| `app/bundles/AssetBundle/Tests/Controller/AssetControllerFunctionalTest.php` | upload validation, path traversal, batch ZIP matrix (`testBatchDownload*`), preview, `testEditWithPermissions`, `testAssetWithProject`, remote-domain validation |
| `app/bundles/AssetBundle/Tests/Controller/UploadControllerFunctionalTest.php` | Dropzone endpoint MIME and extension checks |
| `app/bundles/AssetBundle/Tests/Controller/Api/AssetApiControllerFunctionalTest.php` | API create (local and remote), invalid remote files, delete |
| `app/bundles/AssetBundle/Tests/Controller/AssetDownloadFunctionalTest.php` | click-through attribution from a Page or an Email |
| `app/bundles/AssetBundle/Tests/Model/AssetModelTest.php` | `testTrackDownload`, `testGetEntityBySlugs` (unit, mocked) |
| `app/bundles/AssetBundle/Tests/EventListener/DetermineWinnerSubscriberTest.php` | A/B winner maths |
| `app/bundles/AssetBundle/Tests/EventListener/LeadSubscriberFunctionalTest.php` | timeline, including downloads of deleted Assets |
| `app/bundles/CategoryBundle/Tests/Controller/CategoryControllerFunctionalTest.php` | inline modal (`testNewActionWithInForm`), locking, permissions, `testDeleteUsedInStage`, `testBatchDeleteUsedInStage` |
| `app/bundles/CategoryBundle/Tests/Model/ContactActionModelTest.php` | bulk contact Category changes |
| `app/bundles/ProjectBundle/Tests/Functional/Controller/ProjectControllerTest.php` | CRUD, the one-editable-type shortcut, permissions, deletion |
| `app/bundles/ProjectBundle/Tests/Functional/Controller/ProjectAddEntityTest.php`, `ProjectEntityLookupLimitTest.php` | add-entity flow, 1000-row lookup |
| `app/bundles/ProjectBundle/Tests/Functional/Controller/AjaxControllerTest.php`, `ProjectPopoverSecurityTest.php` | inline creation, duplicate names, XSS escaping |
| `app/bundles/ProjectBundle/Tests/Functional/Controller/Api/ProjectApiControllerTest.php`, `ProjectApiV2ControllerTest.php` | legacy and API Platform CRUD and validation |

[code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:17-155 @7.x] [code: app/bundles/CategoryBundle/Tests/Controller/CategoryControllerFunctionalTest.php:59-270 @7.x]

## Conventions observed
- Log out before testing public downloads. Tracking ignores logged-in Users, so a download made while logged in writes no `asset_downloads` row. [code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:73 @7.x] [code: app/bundles/AssetBundle/Model/AssetModel.php:104-116 @7.x]
- To read a streamed or binary body, call `$response->sendContent()` inside `ob_start()` / `ob_get_contents()`. [code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:77-81 @7.x]
- For remote redirects, call `$this->client->followRedirects(false)` and then `assertResponseRedirects($remotePath)`. [code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:127-131 @7.x]
- AJAX category actions post with `HTTP_X-Requested-With: XMLHttpRequest` and `HTTP_X-CSRF-Token` from `getCsrfToken('mautic_ajax_post')`, then assert on the JSON `flashes`. [code: app/bundles/CategoryBundle/Tests/Controller/CategoryControllerFunctionalTest.php:198-209 @7.x]
- Each project-aware bundle has a `*ProjectSearchFunctionalTest` that extends `AbstractProjectSearchTestCase` with a data provider. Add one when making a new entity project-aware. [code: app/bundles/AssetBundle/Tests/Controller/AssetProjectSearchFunctionalTest.php:11-33 @7.x]

## Skeleton: public download regression test
```php
final class MyAssetDownloadTest extends \Mautic\AssetBundle\Tests\Asset\AbstractAssetTestCase
{
    public function testAnonymousDownloadIsTrackedWithUtm(): void
    {
        $this->logoutUser();
        $this->client->request('GET', '/asset/'.$this->asset->getSlug().'?utm_source=s&stream=0');
        $this->assertResponseIsSuccessful();
        $this->assertStringStartsWith('attachment', (string) $this->client->getResponse()->headers->get('Content-Disposition'));

        $download = $this->em->getRepository(\Mautic\AssetBundle\Entity\Download::class)->findOneBy(['asset' => $this->asset]);
        $this->assertSame('s', $download->getUtmSource());
        $this->assertSame(200, $download->getCode());
    }
}
```
This skeleton follows the pattern of `PublicControllerFunctionalTest::testDownloadActionWithUTM`. [code: app/bundles/AssetBundle/Tests/Controller/PublicControllerFunctionalTest.php:71-97 @7.x]

## Skeleton: project search for a new project-aware entity
```php
final class MyEntityProjectSearchFunctionalTest extends \Mautic\ProjectBundle\Tests\Functional\AbstractProjectSearchTestCase
{
    #[\PHPUnit\Framework\Attributes\DataProvider('searchDataProvider')]
    public function testProjectSearch(string $searchTerm, array $expectedEntities, array $unexpectedEntities): void
    {
        $p1 = $this->createProject('Project One');
        // create entities, $entity->addProject($p1); $this->em->flush(); $this->em->clear();
        $this->searchAndAssert($searchTerm, $expectedEntities, $unexpectedEntities, ['/api/myentities', '/s/myentities']);
    }
}
```
This skeleton follows `AssetProjectSearchFunctionalTest`. [code: app/bundles/AssetBundle/Tests/Controller/AssetProjectSearchFunctionalTest.php:11-33 @7.x]

## What a good regression test asserts here
- Downloads:
  - the HTTP status and the `Content-Disposition` and `X-Robots-Tag` headers;
  - the `asset_downloads` row's `code`, `lead_id`, `source` and utm fields;
  - `download_count` and `unique_download_count` after repeated requests with the same tracking cookie.

  [code: app/bundles/AssetBundle/Model/AssetModel.php:234-257 @7.x]
- Uploads: post to the Dropzone endpoint and assert the JSON `error`, then post the Asset form and check the validator messages. [code: app/bundles/AssetBundle/EventListener/UploadSubscriber.php:60-92 @7.x]
- Categories: test both an in-use delete (flash, row still present) and a delete of an unused Category. For bundle-specific permission checks, use a non-admin User. [code: app/bundles/CategoryBundle/Tests/Controller/CategoryControllerFunctionalTest.php:178-270 @7.x]
- Projects: test as a non-admin with and without `project:project:associate`, and with entity-level `viewown` only. An admin hides permission bugs; for example, `ProjectApiV2ControllerTest` runs as admin. [code: app/bundles/ProjectBundle/Service/ProjectEntityLoaderService.php:153-176 @7.x]
- Cloud storage: the plugin has no tests. Mock the `RemoteAssetBrowseEvent` adapter (Gaufrette `InMemory`) when you touch it. [code: plugins/MauticCloudStorageBundle/EventListener/RemoteAssetBrowseSubscriber.php:13-33 @7.x]
