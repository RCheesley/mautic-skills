# Channels: test patterns

## Base classes and helpers
- Functional tests (real DB, container, HTTP client): `Mautic\CoreBundle\Test\MauticMysqlTestCase`. Unit tests: `PHPUnit\Framework\TestCase`. Form types: `Symfony\Component\Form\Test\TypeTestCase`. Project search: `Mautic\ProjectBundle\Tests\Functional\AbstractProjectSearchTestCase`. Social integrations: `Mautic\PluginBundle\Tests\Integration\AbstractIntegrationTestCase` [code: app/bundles/SmsBundle/Tests/Functional/SmsModelFunctionalTest.php:20 @7.x].
- No Codeception acceptance tests cover SMS, focus, push, marketing messages or monitoring (code analysis grep of `tests/acceptance`).
- `Mautic\SmsBundle\Tests\SmsTestHelperTrait::configureTwilioWithArrayTransport()` runs `mautic:plugins:install`, publishes Twilio through `s/plugins/config/Twilio` (username, password, messaging_service_sid) and swaps `ArrayTransport` into the `TransportChain`. Sent messages land in `$transport->smses` / `$transport->mmses` [code: app/bundles/SmsBundle/Tests/SmsTestHelperTrait.php:15-49 @7.x] [code: app/bundles/SmsBundle/Tests/ArrayTransport.php:15-22 @7.x].
- `Mautic\SmsBundle\Tests\Functional\CreateEntitiesTrait::createAnSms($name, $message, $isPublished, $locale)` [code: app/bundles/SmsBundle/Tests/Functional/CreateEntitiesTrait.php:11 @7.x].
- `Mautic\NotificationBundle\Tests\NotificationTrait` publishes OneSignal with encrypted keys, creates a notification and campaign, and exposes the container's Guzzle `MockHandler` so tests can queue OneSignal responses and inspect requests [code: app/bundles/NotificationBundle/Tests/NotificationTrait.php:23-70 @7.x].
- The queue command test uses `CreateTestEntitiesTrait` [code: app/bundles/ChannelBundle/Tests/Command/ProcessMarketingMessagesQueueCommandFunctionalTest.php:25 @7.x].

## Representative tests to copy
| Area | Test | What it shows |
|---|---|---|
| Marketing Message fallback | `app/bundles/ChannelBundle/Tests/EventListener/CampaignSubscriberTest.php:157-200` | email fails → SMS used; SMS DNC written to metadata |
| Priority | `app/bundles/ChannelBundle/Tests/PreferenceBuilder/PreferenceBuilderTest.php:18-101` | priorities, DNC exclusion |
| Queue | `app/bundles/ChannelBundle/Tests/Model/MessageQueueModelTest.php:82-160` | reschedule intervals, null campaign event |
| Queue command | `app/bundles/ChannelBundle/Tests/Command/ProcessMarketingMessagesQueueCommandFunctionalTest.php:25-86` | `Messages sent: N`, `--limit` |
| Bulk DNC | `app/bundles/ChannelBundle/Tests/Model/ChannelActionModelTest.php:83-200` | unsubscribed not resubscribed |
| SMS per locale | `app/bundles/SmsBundle/Tests/Functional/SmsModelFunctionalTest.php:20-130` | one batch per language |
| SMS filters | `app/bundles/SmsBundle/Tests/EventListener/SendSmsSubscriberTest.php:34-130` | DNC, frequency, missing number |
| Twilio inbound / STOP | `app/bundles/SmsBundle/Tests/Integration/Twilio/TwilioCallbackTest.php:28-90`, `app/bundles/SmsBundle/Tests/EventListener/StopSubscriberTest.php:25` | 404/400 rules; DNC on `stop` |
| Transports | `app/bundles/SmsBundle/Tests/Sms/TransportChainTest.php:61-115` | registration and dispatch |
| MMS | `app/bundles/SmsBundle/Tests/Controller/SMSControllerFunctionalTest.php:72` | 5 MB limit |
| Push campaign | `app/bundles/NotificationBundle/Tests/Functional/EventListener/CampaignSubscriberTest.php:48-470` | DNC, unpublished, no push ids, web vs mobile, tokens, buttons, batching |
| Push payload | `app/bundles/NotificationBundle/Tests/Unit/Api/OneSignalApiTest.php:12` | OneSignal JSON |
| Focus JS | `plugins/MauticFocusBundle/Tests/Controller/FocusPublicControllerFunctionalTest.php:18-60` | JS body, 404 when unpublished |
| Focus stats | `plugins/MauticFocusBundle/Tests/Model/FocusModelFunctionalTest.php:28`, `plugins/MauticFocusBundle/Tests/Model/FocusModelTest.php:43` | chart, form only for `form` |
| Social | `plugins/MauticSocialBundle/Tests/Functional/SocialCommandsTest.php:11-35`, `plugins/MauticSocialBundle/Tests/Functional/V2API/MonitoringV2ApiTest.php:60-240` | exit codes, API Platform CRUD |
[code: app/bundles/ChannelBundle/Tests/EventListener/CampaignSubscriberTest.php:157 @7.x] [code: app/bundles/NotificationBundle/Tests/Functional/EventListener/CampaignSubscriberTest.php:422-470 @7.x]

## What a good regression test asserts
- SMS send: the `ArrayTransport` captured text (tokens replaced, link tracked or not), `sms_message_stats` rows (only for successes), `sms_messages.sent_count`, and the returned status string per Contact [code: app/bundles/SmsBundle/Model/SmsModel.php:348-378 @7.x].
- Frequency: a `message_queue` row with channel, channel_id, `scheduled_date` and `max_attempts = 3`, and no stat [code: app/bundles/SmsBundle/EventListener/SendSmsSubscriber.php:48-68 @7.x].
- Inbound: the HTTP status for `/sms/twilio/callback`, a `lead_donotcontact` row (`channel = sms`, `reason = 1`), and a `lead_event_log` reply row [code: app/bundles/SmsBundle/EventListener/ReplySubscriber.php:36-56 @7.x].
- Marketing Message: which pseudo event ran per Contact, the MM log's passed/failed state and the per-channel metadata [code: app/bundles/ChannelBundle/EventListener/CampaignSubscriber.php:187-238 @7.x].
- Push: the request body in the Guzzle `MockHandler` history, the log metadata `status: delivered`, and the `push_notification_stats` row [code: app/bundles/NotificationBundle/EventListener/CampaignSubscriber.php:260-282 @7.x].
- Focus: the JS response code and content type, and `focus_stats` rows after hitting the view pixel with a tracked Contact [code: plugins/MauticFocusBundle/Controller/PublicController.php:46-65 @7.x].

## Skeletons

Unit test of a reply listener (mirrors `StopSubscriberTest`):
```php
final class MyKeywordSubscriberTest extends \PHPUnit\Framework\TestCase
{
    public function testStartRemovesDnc(): void
    {
        $lead = new Lead();
        $lead->setId(1);
        $dnc = $this->createMock(DoNotContactModel::class);
        $dnc->expects($this->once())->method('removeDncForContact')->with(1, 'sms');

        (new MyKeywordSubscriber($dnc))->onReply(new ReplyEvent($lead, 'START'));
    }
}
```
`ReplyEvent($lead, $message)` and `addDncForContact(id, 'sms', DoNotContact::UNSUBSCRIBED)` are taken from `StopSubscriberTest` [code: app/bundles/SmsBundle/Tests/EventListener/StopSubscriberTest.php:25-41 @7.x]. `removeDncForContact` is an assumption: check `Mautic\LeadBundle\Model\DoNotContact` for the exact name.

Functional SMS send:
```php
final class SmsSendRegressionTest extends MauticMysqlTestCase
{
    use SmsTestHelperTrait;
    use CreateEntitiesTrait;

    public function testDncContactIsNotSent(): void
    {
        $transport = $this->configureTwilioWithArrayTransport();
        $sms       = $this->createAnSms('t', 'Hi {contactfield=firstname}', true, 'en');
        $contact   = new Lead();
        $contact->setMobile('+15555550100');
        $this->em->persist($contact);
        $this->em->flush();
        // add DNC for channel 'sms' via DoNotContact model, then:
        $result = static::getContainer()->get(SmsModel::class)->sendSms($sms, $contact);
        Assert::assertSame([], $transport->smses);
        Assert::assertFalse($result[$contact->getId()]['sent']);
    }
}
```
The result array keys follow `SmsModel::sendSms()` [code: app/bundles/SmsBundle/Model/SmsModel.php:231-246 @7.x]. Confirm the service id and the `createAnSms` signature in the trait before running.

Run: `bin/phpunit app/bundles/SmsBundle/Tests/...` or `--filter`. For DB setup, see mautic-testing.

## Regression tests worth adding
Rows from the regression catalogue in references/pr-history.md with no matching test found in the 7.x `Tests` directories.

| Contract | PR | Where to add |
|---|---|---|
| `/notification/appcallback` with an empty `push_id` stores no push id | [PR #14480] | `app/bundles/NotificationBundle/Tests/Functional/` |
| The focus builder reports a site whose CSP `frame-ancestors` blocks framing | [PR #15837] | `plugins/MauticFocusBundle/Tests/` |
| The segment SMS pending count works with a DB table prefix | [PR #11159] | `app/bundles/SmsBundle/Tests/Functional/` |
| One campaign "Send text message" run sends once per Contact and resolves every log | [PR #14874] | `app/bundles/SmsBundle/Tests/Functional/` |
| A malformed phone number does not stop the other Contacts in the batch | [PR #2162] | `app/bundles/SmsBundle/Tests/Functional/` |
