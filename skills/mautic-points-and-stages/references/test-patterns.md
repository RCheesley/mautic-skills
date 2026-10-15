# Points and stages - test patterns

## Base classes and helpers
- Functional and controller tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`. It provides a real MySQL database and `$this->em`, `$this->client` and `logoutUser()` [code: app/bundles/PointBundle/Tests/Functional/PointActionFunctionalTest.php:7,15-20 @7.x].
- Unit tests extend `PHPUnit\Framework\TestCase` [code: app/bundles/StageBundle/Tests/Unit/EventListener/CampaignSubscriberTest.php:19-22 @7.x].
- Project-search tests extend `Mautic\ProjectBundle\Tests\Functional\AbstractProjectSearchTestCase`.
- `app/bundles/PointBundle/Tests/Functional/TriggerTrait.php` provides two helpers [code: app/bundles/PointBundle/Tests/Functional/TriggerTrait.php:11-47 @7.x]:
  - `createTrigger(string $name, int $points = 0, ?Group $group = null, bool $triggerExistingLeads = false)` persists a trigger. It does not flush.
  - `createAddTagEvent(string $tag, Trigger $trigger)` adds a `lead.changetags` event with `add_tags = [$tag]`.
- No Codeception coverage for these bundles was found (the search was not exhaustive).

## Rules that make or break a test
1. Call `$this->logoutUser()` before driving a Point Action through HTTP. A logged-in test user gets no points, except for `email.send` [code: app/bundles/PointBundle/Model/PointModel.php:176-178 @7.x].
2. Re-read the Contact after the action, with `$this->em->clear()` and then `LeadModel::getEntity()`. Main points are applied with SQL `UPDATE ... points = points + n`, so the in-memory entity can be stale [code: app/bundles/LeadBundle/Entity/LeadRepository.php:1370-1428 @7.x].
3. To fire triggers on a new Contact, save it with points through `LeadModel::setFieldValues()` and `saveEntity()`; the new-contact `LEAD_POST_SAVE` path runs them. To fire them on an existing Contact, change points without the imported flag [code: app/bundles/PointBundle/Tests/Functional/PointTriggerFunctionalTest.php:19-41 @7.x] [code: app/bundles/LeadBundle/Helper/LeadChangeEventDispatcher.php:42-62 @7.x].
4. Point Actions are synchronous. Assert straight after the request; there is no command to run [code: app/bundles/PageBundle/EventListener/PointSubscriber.php:55-64 @7.x].
5. Group score changes flush immediately and run triggers and insights inside `adjustPoints()` [code: app/bundles/PointBundle/Model/PointGroupModel.php:100-130 @7.x].
6. Unique stage weights: give each fixture stage a distinct weight, or the save fails validation [code: app/bundles/StageBundle/Entity/Stage.php:116 @7.x].

## Representative tests to copy from
| Test | What it shows |
|---|---|
| `app/bundles/PointBundle/Tests/Functional/PointActionFunctionalTest.php` | Email-open action awards the delta through the tracking pixel; a group action leaves main points at 0; early return when no action exists |
| `app/bundles/PointBundle/Tests/Functional/PointTriggerFunctionalTest.php` | Thresholds; grouped vs ungrouped triggers; trigger-existing-contacts on save (:77-107) |
| `app/bundles/PointBundle/Tests/Unit/Model/PointModelTest.php` | Reflection-based callback invocation for `url.hit` (:76-140) |
| `app/bundles/PointBundle/Tests/Unit/Model/TriggerModelTest.php` | Trigger event dispatch by `eventName` (:74-118) |
| `app/bundles/PointBundle/Tests/Entity/PointEntityValidationTest.php` | Delta int32 range via the form and the API |
| `app/bundles/PointBundle/Tests/Functional/PointInsightsFunctionalTest.php` | Insight winner, zero and tie rules (:22-98) |
| `app/bundles/PointBundle/Tests/Functional/SegmentFilterFunctionalTest.php` | `group_points_<id>` segment filter |
| `app/bundles/PointBundle/Tests/Functional/ReportSubscriberFunctionalTest.php` | Point-log report with group; group-score report |
| `app/bundles/PointBundle/Tests/Controller/Api/PointGroupsApiControllerTest.php` | Group CRUD and contact group adjustments via the API (:89) |
| `app/bundles/PointBundle/Tests/Functional/EventListener/LeadSubscriberTest.php` | Merge of action and trigger logs (:30, :60) |
| `app/bundles/LeadBundle/Tests/EventListener/PointSubscriberTest.php` | Trigger events change tags (:75) and stage, remove stage, missing stage (:93-171) |
| `app/bundles/LeadBundle/Tests/EventListener/CampaignSubscriberFunctionalTest.php:217-345` | Stage condition, points condition (main and group), adjust-points action |
| `app/bundles/StageBundle/Tests/Unit/EventListener/CampaignSubscriberTest.php` | Every branch of the weight rule (:24-415) |
| `app/bundles/StageBundle/Tests/Functional/Controller/StageControllerFunctionalTest.php` | Stage merge moves Contacts and logs (:57-136) |
| `app/bundles/StageBundle/Tests/Functional/Controller/Api/StageApiControllerTest.php` | Add and remove a Contact via the API (:22-46) |

[code: app/bundles/PointBundle/Tests/Functional/PointActionFunctionalTest.php:18-83 @7.x] [code: app/bundles/PointBundle/Tests/Functional/PointTriggerFunctionalTest.php:19-107 @7.x]

## What a good regression test asserts
- The score: `leads.points`, or `point_group_contact_score.score` for the group.
- The `lead_points_change_log` row: `type`, `event_name`, `action_name`, `delta` and `group_id` (behaviour item 12).
- The once-per-contact log: `point_lead_action_log` for non-repeatable actions, or `point_lead_event_log` for trigger events. Then fire a second time and assert whether points were awarded again.
- For triggers: the side effect (tag, stage or segment), and that it does not happen below the threshold or for the other score type (main vs group).
- For stages: `leads.stage_id`, the `lead_stages_change_log` row (`action_name` = origin), and the refusal message for a lower weight.

## Skeleton - Point Action (functional)
```php
final class MyPointActionTest extends MauticMysqlTestCase
{
    public function testRepeatableActionAwardsTwice(): void
    {
        $this->logoutUser();                       // required: logged-in users earn nothing
        $lead = new Lead();
        $lead->setEmail('a@example.com');
        $this->em->persist($lead);
        $point = new Point();
        $point->setName('Form submit');
        $point->setType('form.submit');            // registered type
        $point->setDelta(10);
        $point->setRepeatable(true);
        $point->setProperties(['forms' => []]);    // empty = any form
        $this->em->persist($point);
        $this->em->flush();

        // ... submit the form twice as the tracked contact (see mautic-forms) ...

        $this->em->clear();
        $lead = self::getContainer()->get(LeadModel::class)->getEntity($lead->getId());
        self::assertSame(20, $lead->getPoints());
        self::assertSame(0, (int) $this->em->getConnection()->fetchOne(
            'SELECT COUNT(*) FROM '.MAUTIC_TABLE_PREFIX.'point_lead_action_log'
        ));                                         // repeatable actions are not logged
    }
}
```

## Skeleton - Point Trigger (functional)
```php
final class MyTriggerTest extends MauticMysqlTestCase
{
    use TriggerTrait;

    public function testTriggerFiresOnceForNewContactAtThreshold(): void
    {
        $model   = self::getContainer()->get(LeadModel::class);
        $trigger = $this->createTrigger('MQL', 50);
        $this->createAddTagEvent('mql', $trigger);
        $this->em->flush();

        $lead = new Lead();
        $model->setFieldValues($lead, ['email' => 'b@example.com', 'points' => 50], false, true, true);
        $model->saveEntity($lead);                 // new-contact post-save runs triggers

        $this->em->getUnitOfWork()->clear(Lead::class);
        $lead = $model->getEntity($lead->getId());
        self::assertTrue($lead->getTags()->exists(fn ($k, $t) => 'mql' === $t->getTag()));
    }
}
```

## Skeleton - stage weight rule (unit)
Copy `app/bundles/StageBundle/Tests/Unit/EventListener/CampaignSubscriberTest.php`. It builds a `PendingEvent` with an anonymous `Lead` subclass whose `getStage()` returns the current stage and mocks `LeadModel::changeStage()` to throw. It then asserts that the `LeadEventLog` passed with an error. Assert both the lower-weight branch and the same-stage branch [code: app/bundles/StageBundle/Tests/Unit/EventListener/CampaignSubscriberTest.php:24-415 @7.x].

## Running
For example: `bin/phpunit app/bundles/PointBundle/Tests/Functional/PointTriggerFunctionalTest.php`. Environment setup is covered by the mautic-testing skill.

## Regression tests worth adding
These rows come from the regression catalogue in pr-history.md. A grep of the 7.x `Tests/` directories of PointBundle, StageBundle, LeadBundle, EmailBundle and PageBundle found no test that asserts them.

| Contract | Where to add it | PR |
|---|---|---|
| A +35 change with triggers at 1, 20 and 30 runs all three; the 30-point tag result stands | `PointTriggerFunctionalTest` | #12867 |
| After a trigger fires, its rows in `point_trigger_events` still exist | `PointTriggerFunctionalTest` | #14448 |
| A repeatable action awards again on a second qualifying event (functional, not mocked) | `PointActionFunctionalTest` | #6388 |
| A repeatable `email.send` action awards once per send, including segment emails | `EmailBundle/Tests/EventListener/PointSubscriberFunctionalTest.php` | #8619 |
| A `url.hit` action fires from `/mtracking.gif` with HTTP 200 and adds points | `PointActionFunctionalTest` | #14611 |
| A Contact moves to stage "1 - Lead" when "10 - Customer" also exists, without `NonUniqueResultException` | `StageBundle/Tests/Functional` | #9066 |
| Saving a stage whose weight another stage already uses fails server-side with `mautic.stage.weight.unique` | `StageBundle/Tests/Functional/Controller` | #15404 |
