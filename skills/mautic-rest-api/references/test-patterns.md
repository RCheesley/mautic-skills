# REST API framework: test patterns

How to test the API framework and any endpoint built on it. Area skills hold resource-specific tests; mautic-testing holds
the general harness (database reset, fixtures, Codeception).

## 1. Base classes and harness facts

- Functional API tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`.
  [code: app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php:16 @7.x]
- The harness sets `api_enabled` and `api_enable_basic_auth` to true in `$configParams` for every test, so the API is
  reachable without extra configuration. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x]
- `MauticMysqlTestCase::setUp()` logs the `admin` user in on the `mautic` context, which creates a session.
  [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:57-58 @7.x]
- Set `protected bool $authenticateApi = true;` to make the test client send HTTP Basic credentials `admin` /
  `Maut1cR0cks!` on every request. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:47-63,117 @7.x]
- To act as a less-privileged User, create a `User` with a `Role`, persist it, and call `$this->loginUser($user)`.
  [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:130-133 @7.x]
  [code: app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php:144-159 @7.x]
- For v2 own/other permission tests extend `Mautic\LeadBundle\Tests\Functional\ApiPlatform\OwnershipScopedApiAuthorizationTestBase`,
  which provides `createUserWithPermissions($username, $email, $password, $permissions)`.
  [code: app/bundles/LeadBundle/Tests/Functional/ApiPlatform/OwnershipScopedApiAuthorizationTestBase.php:19-24 @7.x]
- `CreateTestEntitiesTrait` creates common entities (for example `createEmail()`).
  [code: app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php:9,18,22 @7.x]
- Unit tests extend `PHPUnit\Framework\TestCase` or `Mautic\CoreBundle\Test\CommonMocks`.
  [code: app/bundles/ApiBundle/Tests/Controller/CommonApiControllerTest.php @7.x]

## 2. Representative tests to copy

| Test | Copy it for |
|---|---|
| `app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php` | OAuth2 flows: authorize redirect, invalid client/token envelopes, client-credentials end to end, bearer token on v1 and v2. [code: app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php:33-183 @7.x] |
| `app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php` | Locking (409), per-user permissions, batch edit item errors. [code: app/bundles/ApiBundle/Tests/Functional/Controller/CommonApiControllerTest.php:20-116 @7.x] |
| `app/bundles/ApiBundle/Tests/Functional/Serializer/PutOperationTest.php` | v2 requests: create with the EntityManager, call `/api/v2/...`, assert JSON. [code: app/bundles/ApiBundle/Tests/Functional/Serializer/PutOperationTest.php:22-93 @7.x] |
| `app/bundles/AssetBundle/Tests/Functional/ApiPlatform/DownloadOwnershipApiV2AuthorizationRegressionTest.php` | v2 own/other item and collection regressions, including `?page=1&itemsPerPage=10` totals. [code: app/bundles/AssetBundle/Tests/Functional/ApiPlatform/DownloadOwnershipApiV2AuthorizationRegressionTest.php:19-218 @7.x] |
| `app/bundles/ApiBundle/Tests/Controller/CommonApiControllerTest.php` | Unit tests of `where` sanitising and alias prefixing. [code: app/bundles/ApiBundle/Tests/Controller/CommonApiControllerTest.php:28-246 @7.x] |
| `app/bundles/ApiBundle/Tests/Functional/OwnershipScopedSecurityMetadataTest.php` | The meta-test that fails when a new v2 ownership-scoped operation omits `object`. [code: app/bundles/ApiBundle/Tests/Functional/OwnershipScopedSecurityMetadataTest.php @7.x] |

Per-resource functional API tests exist for most bundles, for example
`app/bundles/LeadBundle/Tests/Controller/Api/CompanyApiControllerFunctionalTest.php`,
`app/bundles/CategoryBundle/Tests/Controller/Api/CategoryApiControllerFunctionalTest.php` and
`app/bundles/UserBundle/Tests/Functional/ApiPlatform/UserApiTest.php`.
[code: app/bundles/LeadBundle/Tests/Controller/Api/CompanyApiControllerFunctionalTest.php @7.x]
[code: app/bundles/UserBundle/Tests/Functional/ApiPlatform/UserApiTest.php @7.x]

## 3. What a good API regression test asserts

1. The HTTP status code, not only "successful": 200 vs 201 matters for create, PUT-create and batch (R45, R50, R58 in
   `behaviour.md`). [code: app/bundles/ApiBundle/Controller/CommonApiController.php:243-348 @7.x]
2. The envelope key (`contact`, `list`, `hook`...) and that list collections are keyed by id (R31).
   [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:232-245 @7.x]
3. For errors, `errors[0].code`, `errors[0].message` and, for validation, `errors[0].details[<field>]` (R66, R69).
   [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:611-640 @7.x]
4. The database state after the call (reload with the EntityManager after `$this->em->clear()`), because PUT clears
   omitted fields and PATCH keeps them (R49–R50). [code: app/bundles/ApiBundle/Tests/Functional/Serializer/PutOperationTest.php:50-93 @7.x]
5. Permission boundaries: a User with only `viewown` must not see or change another User's row, on v1 and on v2
   (R42, R97). [code: app/bundles/AssetBundle/Tests/Functional/ApiPlatform/DownloadOwnershipApiV2AuthorizationRegressionTest.php:19-152 @7.x]
6. For batch endpoints, `statusCodes[i]` and `errors[i]` per item, and the 200-item cap (R56–R62).
   [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:728-736 @7.x]

## 4. Skeletons

v1 endpoint (functional, admin via Basic Auth):

```php
<?php

declare(strict_types=1);

namespace MauticPlugin\HelloWorldBundle\Tests\Functional\Api;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Symfony\Component\HttpFoundation\Response;

final class WorldApiControllerFunctionalTest extends MauticMysqlTestCase
{
    protected bool $authenticateApi = true; // HTTP Basic admin / Maut1cR0cks!

    public function testCreateThenPatchKeepsOmittedFields(): void
    {
        $this->client->request('POST', '/api/worlds/new', ['name' => 'Earth', 'description' => 'Blue']);
        $this->assertResponseStatusCodeSame(Response::HTTP_CREATED);
        $id = json_decode($this->client->getResponse()->getContent(), true)['world']['id'];

        $this->client->request('PATCH', "/api/worlds/{$id}/edit", ['name' => 'Terra']);
        $this->assertResponseIsSuccessful();
        $world = json_decode($this->client->getResponse()->getContent(), true)['world'];
        $this->assertSame('Terra', $world['name']);
        $this->assertSame('Blue', $world['description']); // PATCH keeps omitted fields

        $this->client->request('PATCH', '/api/worlds/999999/edit', ['name' => 'X']);
        $this->assertResponseStatusCodeSame(Response::HTTP_NOT_FOUND);
    }

    public function testListIsKeyedById(): void
    {
        $this->client->request('GET', '/api/worlds?limit=5&orderBy=id&orderByDir=DESC');
        $body = json_decode($this->client->getResponse()->getContent(), true);
        $this->assertArrayHasKey('total', $body);
        foreach ($body['worlds'] as $key => $row) {
            $this->assertSame((int) $key, $row['id']);
        }
    }
}
```

The `world`/`worlds` keys and paths are hypothetical; use your controller's `entityNameOne`/`entityNameMulti`.

v2 resource (functional, session admin from `setUp()`):

```php
public function testPutReplacesWholeResource(): void
{
    $project = new \Mautic\ProjectBundle\Entity\Project();
    $project->setName('A');        // setters return void
    $project->setDescription('D');
    $this->em->persist($project);
    $this->em->flush();

    $this->client->request('PUT', '/api/v2/projects/'.$project->getId(), [], [], [
        'CONTENT_TYPE' => 'application/ld+json',
        'HTTP_ACCEPT'  => 'application/ld+json',
    ], json_encode(['name' => 'B']));
    $this->assertResponseIsSuccessful();

    $this->em->clear();
    $reloaded = $this->em->find(\Mautic\ProjectBundle\Entity\Project::class, $project->getId());
    $this->assertSame('B', $reloaded->getName());
    $this->assertNull($reloaded->getDescription()); // v2 PUT nulls omitted fields
}
```

This mirrors the structure of `PutOperationTest`. [code: app/bundles/ApiBundle/Tests/Functional/Serializer/PutOperationTest.php:22-93 @7.x]
[code: app/bundles/ProjectBundle/Entity/Project.php:130-142 @7.x]

## 5. Running

`composer test` runs `bin/phpunit -d memory_limit=2G --bootstrap vendor/autoload.php --configuration app/phpunit.xml.dist`;
append a file path to run one test, for example `composer test -- app/bundles/ApiBundle/Tests/Functional/Oauth2Test.php`.
`bin/phpunit` exists only after `composer install`. Database setup and the test environment are described in
mautic-testing. [code: composer.json:169 @7.x]
