# Users, roles, permissions — test patterns (Mautic 7.x)

## 1. Base classes and helpers

| Need | Use | Source |
|---|---|---|
| Functional test with DB, HTTP client, logged-in admin | `Mautic\CoreBundle\Test\MauticMysqlTestCase` (15 UserBundle tests use it) | [code: app/bundles/UserBundle/Tests/Functional/Controller/UserControllerFunctionalTest.php @7.x] |
| Container access without DB fixtures | `AbstractMauticTestCase` | [code: app/bundles/UserBundle/Tests/Security/UserTokenSetterTest.php @7.x] |
| Pure unit tests | PHPUnit `TestCase` | [code: app/bundles/UserBundle/Tests/Model/RoleModelTest.php @7.x] |
| Search-scope providers | `Mautic\CoreBundle\Tests\Unit\Helper\SearchScopeProviderTestCase` | [code: app/bundles/UserBundle/Helper/UserSearchScopeProvider.php @7.x] |
| Create a Role / User quickly | `Tests/Traits/CreateEntityTrait` — `createRole(bool $isAdmin = false)`, `createUser(Role, email, password)` (hashes the password via `UserPasswordHasherInterface`) | [code: app/bundles/UserBundle/Tests/Traits/CreateEntityTrait.php @7.x] |
| Fake a SAML session | `Tests/Controller/LoginUserWithSamlTrait` (sets `samlsso` and a `TestBrowserToken` in a mocked session) | [code: app/bundles/UserBundle/Tests/Controller/LoginUserWithSamlTrait.php @7.x] |

Environment facts that shape tests:
- The `test` environment hashes passwords with md5 and enables HTTP Basic on the `main` firewall, so tests can authenticate with `PHP_AUTH_USER` / `PHP_AUTH_PW` without the form. [code: app/config/security_test.php:8-25 @7.x]
- Fixtures provide `admin` and `sales` Users with password `Maut1cR0cks!` and a "Sales Team" Role (`user:profile:editname`, `lead:leads:full`). [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php @7.x] [code: app/bundles/UserBundle/DataFixtures/ORM/LoadRoleData.php:42-46 @7.x]
- Tests create `Permission` rows directly with a bitwise value; this bypasses `analyzePermissions()`, so implied levels are **not** added — set every bit you rely on. Example `52` = view + edit + create. [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:113,161-171 @7.x]
- `CorePermissions::isGranted()` memoises per permission string for the service lifetime; when one test checks the same string for two Users, reboot the client/container or use separate requests. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:210-213,249 @7.x]
- Saving a Role invalidates the `Role`/`User` result caches, but rows inserted with raw SQL do not; persist through Doctrine or clear the cache. [code: app/bundles/UserBundle/Entity/Role.php:302-308 @7.x]

## 2. Representative tests to copy from

1. `app/bundles/UserBundle/Tests/Security/UserLoginTest.php` — real form login through `/s/login`, including login by email. [code: app/bundles/UserBundle/Tests/Security/UserLoginTest.php:27-50 @7.x]
2. `app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php` — non-admin Role with a hand-built permission row, weak password → 401, password policy data provider (400/201), API Platform creation. [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:100-260 @7.x]
3. `app/bundles/UserBundle/Tests/Functional/Controller/RoleControllerFunctionalTest.php` — new/edit/clone/delete/batch delete with and without permission; sort by user count. [code: app/bundles/UserBundle/Tests/Functional/Controller/RoleControllerFunctionalTest.php:62-192 @7.x]
4. `app/bundles/UserBundle/Tests/Functional/Controller/PublicControllerTest.php` — reset page (XSS), reset flow, invite registration. [code: app/bundles/UserBundle/Tests/Functional/Controller/PublicControllerTest.php:49-116 @7.x]
5. `app/bundles/UserBundle/Tests/Model/UserModelTest.php` — reset token persistence and errors, invite token lifecycle (unit). [code: app/bundles/UserBundle/Tests/Model/UserModelTest.php:123-398 @7.x]
6. `app/bundles/CoreBundle/Tests/Functional/Security/Permissions/CorePermissionsTest.php` — virtual permissions with the `sales` User. [code: app/bundles/CoreBundle/Tests/Functional/Security/Permissions/CorePermissionsTest.php:27-40 @7.x]

Also useful: `Tests/Security/Authenticator/TimingSafeFormLoginAuthenticatorTest.php`, `Tests/EventListener/PasswordSubscriberTest.php`, `Tests/Security/Authenticator/PluginAuthenticatorTest.php`, `SsoAuthenticatorTest.php`, `Tests/Security/SAML/**`, `Tests/Functional/Entity/UserTokenRepositoryTest.php`, `Tests/Functional/UserLogoutFunctionalTest.php`, `Tests/Controller/ProfileControllerTest.php`, `Tests/Controller/UserControllerTest.php` (SAML password hiding), `Tests/Functional/Controller/UserControllerFunctionalTest.php` (password field rules, `is:never_logged_in`). [code: app/bundles/UserBundle/Tests/Functional/Controller/UserControllerFunctionalTest.php:80-240 @7.x]

There is no Codeception coverage specific to users or roles; acceptance tests only use login as a step. [code: app/bundles/UserBundle/Tests/Security/UserLoginTest.php @7.x]

## 3. What a good regression test asserts here

- **Permission gates**: one test per side of the gate — a non-admin User with the exact bits (and without) gets 200 vs 403 on the route or API call; an admin always passes. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:220-245 @7.x]
- **Own vs other**: create the record with `created_by` = the logged-in User and with another User; assert own-only Roles see/edit only the first. [code: app/bundles/CoreBundle/Security/Permissions/CorePermissions.php:335-379 @7.x]
- **Role save**: post the Role form (or `POST /api/roles/new` with `rawPermissions`) and assert the stored `permissions.bitwise` includes implied levels, while `readable_permissions` equals the submitted array. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:214-255 @7.x] [code: app/bundles/UserBundle/Model/RoleModel.php:56-93 @7.x]
- **Auth flows**: assert flash text and redirect target, and that unknown identifiers produce the same response as known ones (reset request, reset confirm). [code: app/bundles/UserBundle/Controller/PublicController.php:44-139 @7.x]
- **Audit**: after a User/Role save or a login, assert an `audit_log` row with the expected bundle/object/action. [code: app/bundles/UserBundle/EventListener/UserSubscriber.php:34-102 @7.x] [code: app/bundles/UserBundle/EventListener/SecuritySubscriber.php:28-43 @7.x]
- **Password policy**: use a data provider of weak and strong passwords (`aaa`, `qwerty`, `qwerty123` → 400; `Qwertee@123` → 201). [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:130-156 @7.x]

## 4. Skeleton: permission gate on a non-admin User

```php
<?php
declare(strict_types=1);

namespace Mautic\UserBundle\Tests\Functional;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\UserBundle\Entity\Permission;
use Mautic\UserBundle\Entity\Role;
use Mautic\UserBundle\Tests\Traits\CreateEntityTrait;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

final class RoleIndexPermissionTest extends MauticMysqlTestCase
{
    use CreateEntityTrait;

    public function testUserWithoutRolesViewIsDenied(): void
    {
        $role = $this->createRole();                  // non-admin
        $this->addPermission($role, 'user', 'users', 4); // user:users:view only
        $user = $this->createUser($role, 'gate@example.com', 'Maut1cR0cks!');
        $this->em->flush();
        $this->em->clear();

        $this->loginUser($user);
        $this->client->request(Request::METHOD_GET, '/s/roles');
        self::assertResponseStatusCodeSame(Response::HTTP_FORBIDDEN);
    }

    private function addPermission(Role $role, string $bundle, string $name, int $bitwise): void
    {
        $permission = new Permission();
        $permission->setBundle($bundle);
        $permission->setName($name);
        $permission->setRole($role);
        $permission->setBitwise($bitwise);
        $this->em->persist($permission);
    }
}
```

Pattern sources: `createPermission()` and `loginUser()` usage. [code: app/bundles/UserBundle/Tests/Controller/Api/UserApiControllerFunctionalTest.php:100-171 @7.x] RoleControllerFunctionalTest asserts 403 for denied Role actions. [code: app/bundles/UserBundle/Tests/Functional/Controller/RoleControllerFunctionalTest.php:62-163 @7.x]

## 5. Skeleton: unit test of a plugin permission class

```php
public function testEditImpliesView(): void
{
    $perms = new HelloWorldPermissions([]);          // 7.x: array $params constructor
    $data  = ['items' => ['editother']];
    $perms->analyzePermissions($data, []);
    self::assertContains('viewother', $data['items']);
    self::assertContains('viewown', $data['items']);
}
```

Based on the implied-level rules. [code: app/bundles/CoreBundle/Security/Permissions/AbstractPermissions.php:214-255 @7.x] On 8.x the constructor takes no `$params`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html#construct]

## 6. Running

`bin/phpunit --filter RoleControllerFunctionalTest` (or a path under `app/bundles/UserBundle/Tests`). Functional tests need the test database configured by `.env.test` (`mautictest`, prefix `test_`). See mautic-testing for the full setup. [docs: https://devdocs.mautic.org/en/7.2/development-environment/environments.html]

## 7. Regression tests worth adding
Rows from the regression catalogue in pr-history.md with no matching test found by one grep of `app/bundles/*/Tests` @7.x:

| Behaviour to assert | PR |
|---|---|
| An unpublished User cannot log in and sees the generic invalid-login message | [PR #3802] |
| `/s/account` loads for a User whose Role has no `user:users` permissions | [PR #8571] |
| An admin changing a User's email or password sends that User a notification email | [PR #13925] |
| Editing a full-access Role renders the Permissions tab disabled | [PR #14004] |
| The User list "last login" column orders by `u.lastLogin` | [PR #14982] |
| The "User management" admin-menu header is hidden without `user:users:view` and `user:roles:view` | [PR #14851] |
| A Position over 191 characters gives "Position cannot exceed 191 characters." instead of a 500 | [PR #15682] |
| Contact import with an unknown `ownerusername` fails only that row, with "Unable to find an active user by the username or email" | [PR #15877] |
