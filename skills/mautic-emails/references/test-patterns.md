# Mautic Emails - test patterns (7.x)

## Base classes and defaults
- Unit tests extend `PHPUnit\Framework\TestCase`; functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`, often with `Mautic\CoreBundle\Tests\Functional\CreateTestEntitiesTrait` and `Mautic\CoreBundle\Tests\Traits\ControllerTrait`. [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:17-51 @7.x]
- Default functional config: `mailer_dsn = null://null`, `messenger_dsn_email = in-memory://default`, `messenger_dsn_hit = sync://`, `messenger_dsn_failed = in-memory://default`, API basic auth on (`admin` / `Maut1cR0cks!`), `site_url = https://localhost`. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:41-61 @7.x]
- Override per test class by setting `$this->configParams[...]` before `parent::setUp()` (e.g. `disable_trackable_urls`, `mailer_from_email`, `mailer_custom_headers`). [code: app/bundles/EmailBundle/Tests/Controller/EmailControllerFunctionalTest.php:54-63 @7.x]
- Read sent messages with `self::getMailerMessages()`, `self::getMailerMessage($i)` or `self::getMailerMessagesByToAddress('x@y.z')`. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:70-93 @7.x]
- Run commands with `$this->testSymfonyCommand($name, $params)` (returns a `CommandTester`). [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:200 @7.x]
- To exercise the real transport path set `messenger_dsn_email = 'sync://'`; to assert queueing keep `in-memory://default`. [code: app/bundles/EmailBundle/Tests/Controller/Api/SMimeFunctionalTest.php:27-28 @7.x]

## Fixtures
- `app/bundles/EmailBundle/Tests/Functional/Fixtures/EmailFixturesHelper.php`: `createEmail(...)`, `emulateEmailSend(Lead, Email, date, source, sourceId): Stat`, `emulateEmailRead(Stat, Email, date)`, `createEmailLink(url, channelId, hits, uniqueHits): Trackable`, `emulateLinkClick(Email, Trackable, Lead, date, count)`. [code: app/bundles/EmailBundle/Tests/Functional/Fixtures/EmailFixturesHelper.php:18-102 @7.x]
- Doctrine fixture `app/bundles/EmailBundle/DataFixtures/ORM/LoadEmailData.php` (Segment emails on the `lead-list` reference).
- Test transports: `app/bundles/EmailBundle/Tests/Helper/Transport/{BatchTransport,BcInterfaceTokenTransport,SmtpTransport}.php` (batch/tokenized sending), `Tests/MonitoredEmail/Transport/TestTransport.php`; sample bounce/FBL messages in `Tests/_data/`.

## Representative tests (all under `app/bundles/EmailBundle/Tests/`)
| Test | What to copy |
|---|---|
| `Entity/PendingQueryFunctionalTest.php`, `Functional/PendingCountTest.php` | Pending semantics incl. stats with `lead_id = NULL`; asserting the AJAX count JSON |
| `Model/EmailModelFunctionalTest.php` | `sendEmailToLists` limit/batch, Continue sending, pending cache invalidation (`:544-606`), frequency rules vs `sendToDnc` (`:648-690`), winner helpers |
| `Model/EmailModelTest.php` | DNC honoured (`:531`), Segment duplicate guard (`:555`), A/B weighting (`:306`, `:422`), frequency queueing (`:663`), `hitEmail` (`:766`, `:818`) |
| `Model/SendEmailToContactTest.php` | Bad-address DNC (`:173`, `:225`), transport exception (`:566`), stat persistence (`:446`) |
| `Helper/MailHelperTest.php` | From/Reply-To precedence, owner as mailer, headers, List-Unsubscribe (`:955`, `:1005`), batch limits |
| `Controller/PublicControllerFunctionalTest.php` | Unsubscribe, One-Click (`:205`, `:219`), validation form (`:727-829`), resubscribe (`:795-850`), Preference Centre, webview (`:865`), `/mailer/callback` (`:78-103`) |
| `Controller/EmailControllerFunctionalTest.php` | Schedule + broadcast command end to end (`:1217-1312`), optimistic lock (`:902`), link validation (`:1433-1510`) |
| `Controller/EmailSendFunctionalTest.php`, `Functional/EmailClickTrackingTest.php` | UI batch send via `/s/ajax?action=email:sendBatch`, tracked URLs |
| `Controller/Api/EmailApiControllerFunctionalTest.php` | API send (`:528`), reply (`:483`), `sendToDnc` permission masking (`:316`, `:374`, `:462`) |
| `EventListener/CampaignSubscriberActionEmailToContactFunctionalTest.php`, `Functional/EmailVariantInCampaignFunctionalTest.php` | Campaign send, marketing-once across variants |
| `EventListener/BroadcastSubscriberFunctionalTest.php` | A/B broadcast sample handling |
| `MonitoredEmail/Processor/{BounceTest,UnsubscribeTest,ReplyTest,FeedbackLoopTest}.php` | Inbox processing |
| `Functional/BotRatioHelperFunctionalTest.php` | Bot-filtered opens |
| `Functional/EmailTokenTest.php` | Tokens rendered in a real send |

Line references from [code: app/bundles/EmailBundle/Tests/ @7.x] as recorded in the code analysis.

## What a good regression test asserts
- Rows, not UI text: `email_stats` (count per Contact/email, `is_failed`, `is_read`, `list_id`, `source`), `lead_donotcontact` (reason, `channel`, `channel_id`, comment), `emails.sent_count`/`read_count`, `message_queue`, `email_stat_replies`.
- The number and recipients of messages in the mailer (`getMailerMessagesByToAddress`), and headers (`List-Unsubscribe`, `X-EMAIL-ID`, `Reply-To`).
- Both sides of a guard: e.g. one Contact added before `publishUp` (sent) and one after (not sent) when Continue sending is off. [code: app/bundles/EmailBundle/Tests/Controller/EmailControllerFunctionalTest.php:1217-1264 @7.x]
- For pending-count bugs, call the AJAX endpoint after the change that should invalidate the cache.

## Skeleton: Segment Email eligibility
```php
<?php

declare(strict_types=1);

namespace Mautic\EmailBundle\Tests\Functional;

use Mautic\CoreBundle\Test\MauticMysqlTestCase;
use Mautic\EmailBundle\Entity\Email;
use Mautic\EmailBundle\Entity\Stat;
use Mautic\LeadBundle\Entity\DoNotContact;
use Mautic\LeadBundle\Entity\Lead;
use Mautic\LeadBundle\Entity\LeadList;
use Mautic\LeadBundle\Entity\ListLead;

final class SegmentEmailEligibilityFunctionalTest extends MauticMysqlTestCase
{
    protected function setUp(): void
    {
        $this->configParams['messenger_dsn_email'] = 'sync://'; // send through the (null) mailer now
        parent::setUp();
    }

    public function testDncContactIsNotSent(): void
    {
        $segment = new LeadList();
        $segment->setName('Seg');
        $segment->setPublicName('Seg');
        $segment->setAlias('seg');
        $this->em->persist($segment);

        $ok  = $this->addMember($segment, 'ok@example.com', '-1 hour');
        $dnc = $this->addMember($segment, 'dnc@example.com', '-1 hour');

        $email = new Email();
        $email->setName('E');
        $email->setSubject('S');
        $email->setEmailType('list');
        $email->setCustomHtml('<html><body>Hi</body></html>');
        $email->addList($segment);
        $email->setIsPublished(true);
        $email->setPublishUp(new \DateTime('-1 minute'));
        $this->em->persist($email);

        $row = new DoNotContact();
        $row->setLead($dnc);
        $row->setChannel('email');
        $row->setReason(DoNotContact::UNSUBSCRIBED);
        $row->setDateAdded(new \DateTime());
        $this->em->persist($row);
        $this->em->flush();

        $this->testSymfonyCommand('mautic:broadcasts:send', ['--channel' => 'email', '--id' => $email->getId()]);

        $stats = $this->em->getRepository(Stat::class)->findBy(['email' => $email->getId()]);
        self::assertCount(1, $stats);
        self::assertSame('ok@example.com', $stats[0]->getEmailAddress());
    }

    private function addMember(LeadList $segment, string $address, string $added): Lead
    {
        $lead = new Lead();
        $lead->setEmail($address);
        $this->em->persist($lead);
        $ref = new ListLead();
        $ref->setLead($lead);
        $ref->setList($segment);
        $ref->setDateAdded(new \DateTime($added));
        $this->em->persist($ref);

        return $lead;
    }
}
```
The entity setup mirrors
`app/bundles/EmailBundle/Tests/Functional/PendingCountTest.php` and the broadcast test in
`EmailControllerFunctionalTest.php`, which runs `mautic:broadcast:send` (singular alias) with `--channel` and `--id`.
[code: app/bundles/EmailBundle/Tests/Controller/EmailControllerFunctionalTest.php:1256 @7.x]

## Skeleton: unsubscribe endpoint
Create a Contact, an email and a `Stat` with a `tracking_hash`, compute `secretHash` with `MailHashHelper` (HMAC-SHA256 of
the address with `secret_key`), then `POST /email/unsubscribe/{hash}/{email}/{secretHash}` with body
`List-Unsubscribe=One-Click` and assert one `lead_donotcontact` row with reason 1 and channel `email`. Copy the request
setup from `PublicControllerFunctionalTest.php:205`. [code: app/bundles/EmailBundle/Helper/MailHashHelper.php:16-26 @7.x] [code: app/bundles/EmailBundle/Controller/PublicController.php:970-995 @7.x]

## Testing async paths
- Keep `messenger_dsn_email = in-memory://default` and assert the message is in the in-memory transport rather than the mailer. [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:52-61 @7.x]
- `EmailHitNotificationHandler` has a unit test that mocks `EmailModel` and `CoreParametersHelper`: `app/bundles/MessengerBundle/Tests/MessageHandler/EmailHitNotificationHandlerTest.php`.
