# Segments — test patterns

## Base classes and setup
- **Functional (real MySQL)**: extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`. Use it for any filter, rebuild, controller or API test. Add `use CreateTestEntitiesTrait;` for entity helpers [code: app/bundles/LeadBundle/Tests/Command/UpdateLeadListCommandFunctionalTest.php:7-29 @7.x].
- **Schema changes**: set `protected $useCleanupRollback = false;` when the test creates custom fields, because it changes DDL on `leads` [code: app/bundles/LeadBundle/Tests/Command/UpdateLeadListCommandFunctionalTest.php:29 @7.x].
- **Unit tests**: use plain `PHPUnit\Framework\TestCase` for decorators, query builders and the dictionary. These tests assert generated SQL strings [code: app/bundles/LeadBundle/Tests/Segment/Query/Filter/ForeignValueFilterQueryBuilderTest.php @7.x].
- **Fixtures**: `app/bundles/LeadBundle/Tests/DataFixtures/ORM/LoadSegmentsData.php` (service `mautic.lead.fixture.test.segment`) [code: app/bundles/LeadBundle/Config/services.php:63 @7.x].
- **Acceptance**: page object `tests/_support/Page/Acceptance/SegmentsPage.php`.

## Representative tests to copy
1. `app/bundles/LeadBundle/Tests/Command/UpdateLeadListCommandFunctionalTest.php`: command options, `--max-contacts` partial runs, include/exclude matrices for tags, custom fields, company fields and Segment references.
2. `app/bundles/LeadBundle/Tests/Command/UpdateLeadListsCommandCircularDependencyTest.php`: dependency order and cycles.
3. `app/bundles/LeadBundle/Tests/Segment/ContactSegmentServiceFunctionalTest.php`: company primary vs any, missing table, `ids` limiter.
4. `app/bundles/LeadBundle/Tests/Command/SegmentFiltersFunctionalTest.php`: table-driven filter correctness.
5. `app/bundles/LeadBundle/Tests/Segment/Decorator/Date/RelativeDateFunctionalTest.php` and `Tests/Command/SegmentFilterWithRelativeTimeFunctionalTest.php`: relative dates and a non-UTC timezone.
6. `app/bundles/LeadBundle/Tests/Segment/Decorator/Date/Other/DateRelativeIntervalTest.php`, `DateAnniversaryTest.php`: decorator unit tests.
7. `app/bundles/LeadBundle/Tests/Segment/Query/ContactSegmentQueryBuilderTest.php`: the new-contact restriction.
8. `app/bundles/LeadBundle/Tests/Model/ListModelFunctionalTest.php`: manual add after an automatic add.
9. `app/bundles/LeadBundle/Tests/Controller/ListControllerFunctionalTest.php`: alias, clone, unpublish/delete guards, warning icons, invalid dates, positive-only inLast.
10. `app/bundles/LeadBundle/Tests/Controller/Api/ListApiControllerFunctionalTest.php`: API, 422 on unpublish, `withCounts`, inLast/inNext, regex validation.
11. `app/bundles/LeadBundle/Tests/Entity/LeadListTest.php`: legacy filter normalisation and first-glue `and`.
12. `app/bundles/LeadBundle/Tests/Command/SegmentStressTest.php`: many filters.

[code: app/bundles/LeadBundle/Tests @7.x]

## Skeleton: filter + rebuild
Adapted from `testMaxContactsPartialRebuildKeepsBuildingAndUpdatesCountCache` [code: app/bundles/LeadBundle/Tests/Command/UpdateLeadListCommandFunctionalTest.php:135-211 @7.x].
```php
final class MyFilterFunctionalTest extends MauticMysqlTestCase
{
    public function testNotEqualMatchesNull(): void
    {
        $match = (new Lead())->setEmail('a@example.com'); $match->setCity('Paris');
        $null  = (new Lead())->setEmail('b@example.com');                 // city NULL
        $miss  = (new Lead())->setEmail('c@example.com'); $miss->setCity('Berlin');
        foreach ([$match, $null, $miss] as $c) { $this->em->persist($c); }

        $segment = new LeadList();
        $segment->setName('Not Berlin'); $segment->setPublicName('Not Berlin'); $segment->setAlias('not-berlin');
        $segment->setFilters([[
            'glue' => 'and', 'object' => 'lead', 'field' => 'city', 'type' => 'text',
            'operator' => '!=', 'properties' => ['filter' => 'Berlin'],
        ]]);
        $this->em->persist($segment);
        $this->em->flush();

        $output = $this->testSymfonyCommand(UpdateLeadListsCommand::NAME, ['--list-id' => $segment->getId()]);
        $this->assertSame(Command::SUCCESS, $output->getStatusCode());

        $ids = array_column($this->connection->fetchAllAssociative(
            'SELECT lead_id FROM '.MAUTIC_TABLE_PREFIX.'lead_lists_leads WHERE leadlist_id = ? AND manually_removed = 0',
            [$segment->getId()]
        ), 'lead_id');
        $this->assertEqualsCanonicalizing([$match->getId(), $null->getId()], array_map('intval', $ids));
    }
}
```
The `$this->connection` / `MAUTIC_TABLE_PREFIX` usage is a sketch [unverified]. Copy the exact DB-access idiom from the test you base yours on.

## What a good regression test asserts
- Members **and** non-members. Include a NULL-valued Contact for negative operators [code: app/bundles/LeadBundle/EventListener/SegmentOperatorQuerySubscriber.php:29-112 @7.x].
- Manual flags. Add a Contact via `LeadModel::addToLists` and remove another via `removeFromLists`, rebuild, then assert both survive the rebuild unchanged [code: app/bundles/LeadBundle/Model/ListModel.php:727-741 @7.x] [code: app/bundles/LeadBundle/Model/ListModel.php:868-876 @7.x].
- Building state. Check `lastBuiltDate`/`needsRebuild()` after partial and complete runs [code: app/bundles/LeadBundle/Model/ListModel.php:591-633 @7.x].
- Count cache via `SegmentCountCacheHelper::getSegmentContactCount()` alongside `LeadListRepository::getLeadCount()` [code: app/bundles/LeadBundle/Helper/SegmentCountCacheHelper.php:22-53 @7.x].
- For dates, compute expected boundaries in UTC for datetime fields and in `default_timezone` for date fields [code: app/bundles/LeadBundle/Segment/Decorator/Date/TimezoneResolver.php:20-38 @7.x].
- For OR logic, use mixed `and`/`or` chains, because OR-merge into `in` changes the SQL shape [code: app/bundles/LeadBundle/Segment/ContactSegmentFilterFactory.php:106-176 @7.x].
- For Segment references, rebuild with the dependent id only and assert that the base Segment was rebuilt first [code: app/bundles/LeadBundle/Command/UpdateLeadListsCommand.php:110-117 @7.x].

## API test pattern
- Use `$this->client->request('POST', '/api/segments/new', [...])` and assert 201 plus the `list` envelope.
- Unpublishing a Segment that a Campaign uses must return 422 (see `testWeGet422ResponseCodeIfSegmentIsBeingUsedInSomeCampaignAndWeUnpublishIt`).
- For bulk add, post `ids[]` and assert `details[id].success`.

[code: app/bundles/LeadBundle/Tests/Controller/Api/ListApiControllerFunctionalTest.php @7.x] [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:186-215 @7.x]
