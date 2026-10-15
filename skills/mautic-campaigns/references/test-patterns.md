# Campaigns — test patterns

## Base classes and helpers
- Unit tests extend PHPUnit `TestCase` (e.g. `Tests/Membership/Action/AdderTest.php`, `Tests/Executioner/Scheduler/Mode/IntervalTest.php`, `Tests/Helper/InactiveHelperTest.php`) [code: app/bundles/CampaignBundle/Tests @7.x].
- Functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase` (`Tests/Functional/**`, `Tests/Command/**`, `Tests/Controller/**`) [code: app/bundles/CampaignBundle/Tests @7.x].
- `Tests/Command/AbstractCampaignCommand.php` extends `MauticMysqlTestCase`, loads `LeadFieldData` and `LoadLeadData` fixtures and `campaign_schema.sql`, and offers `createLead`, `createCampaign`, `createCampaignLead(campaign, lead, manuallyRemoved, rotation)`, `createSegmentMember`, `createEvent(name, campaign, type, eventType, properties)`, `createEventLog(lead, event, campaign, rotation)`, `markEventLogAsCompleted` (bumps version via `OptimisticLockServiceInterface`), `getCampaignEventLogs(ids)` [code: app/bundles/CampaignBundle/Tests/Command/AbstractCampaignCommand.php:20-203 @7.x].
- `Tests/Campaign/AbstractCampaignTestCase.php` (`saveSomeCampaignLeadEventLogs`); traits `Tests/Functional/Campaign/CampaignEntitiesTrait.php` (segments, leads, campaign + events) and `Tests/Functional/Controller/CampaignControllerTrait.php` (submit builder form, `createCanvasSettings`); `Tests/Functional/Fixtures/FixtureHelper.php` + `entity_data.json`; ORM fixture `DataFixtures/ORM/CampaignData.php` [code: app/bundles/CampaignBundle/Tests @7.x].
- Time control: `TestScheduledExecutioner::setNowTime()` and `TestInactiveExecutioner::setNowTime()` replace the executioners in the test env [code: app/bundles/CampaignBundle/Config/services.php:75-83 @7.x]. Set `CAMPAIGN_EXECUTIONER_SCHEDULER_ACKNOWLEDGE_SECONDS=1` to avoid minute truncation [code: app/bundles/CampaignBundle/Tests/Command/TriggerCampaignCommandTest.php:36 @7.x].
- Codeception UI smoke: `tests/_support/Page/Acceptance/CampaignPage.php`, `tests/_support/Step/Acceptance/CampaignStep.php` [code: tests/_support/Page/Acceptance/CampaignPage.php @7.x].

## Representative tests
| Test | Covers |
|---|---|
| `Tests/Command/TriggerCampaignCommandTest.php` | full pipeline, Change Campaigns (+restart rotation), exclusion, infinite loop, republish behaviour |
| `Tests/Functional/Campaign/CampaignRestartFromSegmentTest.php` | restart when Contact returns to Segment |
| `Tests/Functional/Campaign/CampaignMembershipFunctionalTest.php` | no re-send after exit/rejoin with restart off |
| `Tests/Functional/Campaign/CampaignRotationTest.php` | rotations |
| `Tests/Functional/Campaign/JumpToActionTest.php` | jump loops (`testInfiniteLoop`) |
| `Tests/Functional/Executioner/InactiveExecutionerFunctionalTest.php` | no path, deleted-decision redirects |
| `Tests/Functional/Executioner/Scheduler/Mode/IntervalWeekdayHourTimezoneTest.php` | hour/day/timezone scheduling |
| `Tests/Executioner/EventExecutionerLockTest.php` | optimistic locks, retry after failure |
| `Tests/Command/ResumeStuckCampaignCommandTest.php` | resume stuck |
| `Tests/Membership/Action/AdderTest.php`, `RemoverTest.php` | membership rules |
| `Tests/Executioner/RealTimeExecutionerTest.php` | decisions |
| `Tests/Functional/Controller/CampaignControllerTest.php` | builder save, source/event requirement |
| `Tests/Command/Api/EventLogApiControllerTest.php` | log edit API |
| `Tests/Functional/Controller/CampaignImportControllerTest.php` | import |

All under `app/bundles/CampaignBundle/` [code: app/bundles/CampaignBundle/Tests @7.x].

## How the existing jump test drives the engine
Build entities with Doctrine, flush, run `$this->testSymfonyCommand('mautic:campaigns:trigger', ['-i' => $campaignId])`, read logs, back-date `trigger_date`/`date_triggered` by two minutes, run again, assert the log count did not grow [code: app/bundles/CampaignBundle/Tests/Functional/Campaign/JumpToActionTest.php:20-180 @7.x].

## Skeleton: functional regression test for an execution bug
```php
namespace Mautic\CampaignBundle\Tests\Functional\Campaign;

use Mautic\CampaignBundle\Entity\Campaign;
use Mautic\CampaignBundle\Entity\Event;
use Mautic\CampaignBundle\Entity\Lead as CampaignMember;
use Mautic\CampaignBundle\Entity\LeadEventLog;
use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\LeadBundle\Entity\Lead;

final class MyCampaignRegressionTest extends MauticMysqlTestCase
{
    public function testEventRunsOncePerRotation(): void
    {
        $contact = new Lead();
        $contact->setEmail('a@example.com');
        $this->em->persist($contact);

        $campaign = new Campaign();
        $campaign->setName('Regression');
        $campaign->setIsPublished(true);
        $this->em->persist($campaign);

        $action = new Event();
        $action->setName('Tag');
        $action->setType('lead.changetags');
        $action->setEventType('action');
        $action->setTriggerMode('immediate');
        $action->setProperties(['add_tags' => ['x'], 'remove_tags' => []]);
        $action->setCampaign($campaign);
        $this->em->persist($action);

        $member = new CampaignMember();
        $member->setCampaign($campaign);
        $member->setLead($contact);
        $member->setDateAdded(new \DateTime());
        $this->em->persist($member);
        $this->em->flush();

        $this->testSymfonyCommand('mautic:campaigns:trigger', ['-i' => $campaign->getId()]);
        $this->testSymfonyCommand('mautic:campaigns:trigger', ['-i' => $campaign->getId()]);

        $logs = $this->em->getRepository(LeadEventLog::class)->findBy(['lead' => $contact, 'event' => $action]);
        $this->assertCount(1, $logs);
        $this->assertSame(1, $logs[0]->getRotation());
        $this->assertFalse($logs[0]->getIsScheduled());
    }
}
```
Entity setters follow the entities listed in code-map.md; check each against the entity before use (the skeleton is illustrative) [code: app/bundles/CampaignBundle/Entity/Event.php:265-410 @7.x].

## Skeleton: unit test of a custom action listener
```php
// Given a PendingEvent built from an EventAccessor, an Event and an ArrayCollection of LeadEventLog,
// call your subscriber's handler and assert every log ended passed or failed:
$this->assertCount(0, $pendingEvent->getPending()); // or assert on getSuccessful()/getFailures()
```
`PendingEvent` behaviour is covered in `Tests/Event/PendingEventTest.php` and dispatcher rules in `Tests/Executioner/Dispatcher/ActionDispatcherTest.php` — copy their construction [code: app/bundles/CampaignBundle/Tests/Executioner/Dispatcher/ActionDispatcherTest.php @7.x].

## What a good regression test asserts
- Exact log rows per Contact: event, rotation, `is_scheduled`, `date_triggered`, `trigger_date`, `non_action_path_taken`, failed-log presence [code: app/bundles/CampaignBundle/Entity/LeadEventLog.php:110-186 @7.x].
- Idempotency: a second trigger run adds no rows (unique `campaign_rotation`) [code: app/bundles/CampaignBundle/Entity/LeadEventLog.php:125 @7.x].
- Membership row state (`manually_removed`, `manually_added`, `date_last_exited`, `rotation`) after add/remove [code: app/bundles/CampaignBundle/Entity/Lead.php:66-78 @7.x].
- For scheduling: the computed `trigger_date` in the Contact's timezone, with fixed "now" [code: app/bundles/CampaignBundle/Executioner/Scheduler/Mode/Interval.php:322-360 @7.x].
- For failures: retry date = now + interval and `version` back to 1 [code: app/bundles/CampaignBundle/Executioner/Scheduler/EventScheduler.php:117-137 @7.x].

Running the suite and fixtures in general: see mautic-testing.

## Regression tests worth adding
Rows from the regression catalogue in `references/pr-history.md` with no matching test found by a grep of the 7.x Tests directories.

| Behaviour to assert | PR |
|---|---|
| A due scheduled log already at `version` 2 is not fetched again, and the trigger finishes | [PR #17146] |
| A real-time decision does not fire when the campaign is published but outside its publish-up/down dates | [PR #14303] |
| Parallel kickoff ranges from the contacts-by-segment query do not overlap | [PR #14860] |
