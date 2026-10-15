# Mautic Emails - version notes

Authoritative behaviour is 7.x (release 7.2.1 plus unreleased merged PRs). 8.x is unreleased development (its release metadata still says 7.2.0)
[code: app/release_metadata.json @8.x]. The last forward merge was 7.2.0 -> 8.x [PR #17253], so 7.2.1 and later 7.x features are not
yet on 8.x and arrive with the next forward merge; do not document them as removed in 8.

## History that explains current behaviour
- 2.x used `app/console`; since Mautic 3 cron commands run from `bin/console`. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html]
- `mautic:broadcasts:send` exists since 2.2.0. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-broadcasts-segment-emails-cron-job]
- Up to 4.x, Swiftmailer had a filesystem spool ("How the emails should be handled": queue vs immediate) flushed by `mautic:emails:send`; queued mail counted as sent once written to `var/spool`. [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html] [kb: https://kb.mautic.org/article/how-to-optimize-amazon-ses-send-rate-with-mautic.html]
- The legacy Queue page (RabbitMQ/Beanstalkd `queue_protocol`, `mautic:queue:process -i email_hit`) describes pre-5 behaviour and is still in the 7.2 docs. [docs: https://docs.mautic.org/en/7.2/queue/queue.html]

## 5.x
- Symfony Mailer replaced Swiftmailer; the transport is a DSN (`mailer_dsn`); the spool and `mautic:emails:send` were removed (commit `736b07fbba1`). Email transport configuration had to be redone on upgrade from 4.x. [code: UPGRADE-5.0.md:16 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#email-transport-settings] [kb: https://kb.mautic.org/article/update-from-mautic-4-to-5-1-when-installed-by-softaculous-quick-guide.html]
- Queueing moved to Symfony Messenger (`messenger_dsn_email`, `messenger:consume email`). [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#queued-delivery]
- All transports share the webhook URL `/mailer/callback`. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#webhook-bounce-management]
- Since 5.0 transactional emails are described as sent to opted-out Contacts without an unsubscribe header (KB); in 7.2.1 code that requires the email's `sendToDnc` flag. [kb: https://kb.mautic.org/article/understand-the-difference-transactional-and-marketing-emails-in-mautic.html] [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:315-382 @7.x]
- 5.1: preview of A/B and translation variants; Campaigns triggered newest to oldest. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#translations] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#campaign-cron-jobs]

## 6.x
- No email-specific 6.x behaviour changes are recorded in the inputs. [unverified]

## 7.x
- 7.0 removed `symfony/amqp-messenger` from core dependencies (AMQP DSNs fail validation until installed) and deleted the Messenger `TestHandler` (Queue Settings test button cannot succeed). [code: UPGRADE-7.0.md:15 @7.x] [code: UPGRADE-7.0.md:53 @7.x] [code: app/bundles/MessengerBundle/Validator/DsnValidator.php:31-45 @7.x]
- 7.x deprecates `mautic:disable-tracking` ("Will be removed in 8.0"); use `data-mautic-disable-tracking="true"`. [code: app/bundles/PageBundle/Model/TrackableModel.php:740-747 @7.x]
- 7.2 deprecates `BuilderEvent::addTokensFromHelper()`/`getTokensFromHelper()`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#deprecated-methods]
- Messenger retry multiplier must be >= 1 (fix for mautic/mautic#16017). [code: app/bundles/MessengerBundle/Form/Type/ConfigType.php:57-124 @7.x]
- 7.x after 7.2.1 (unreleased) has the unsubscribe/resubscribe confirm-address page (`validate_unsubscribe_emails`, default true; [PR #16870]), the email preview "Download HTML", and the Company preview selector ([PR #17549]); these are documented on the 8.0 docs branch only. [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:176-182 @7.x] [docs: https://docs.mautic.org/en/8.0/channels/emails.html#unsubscribing]
- Deprecated and still present in 7.x: `MailHelper::validateEmail()` (since 2.11), `EmailEvents::ON_CAMPAIGN_TRIGGER_ACTION` (2.13), `hitEmail()` without a Stat, `ModeratedCommand --force`. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1935-1944 @7.x] [code: app/bundles/EmailBundle/EmailEvents.php:238-248 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:437-441 @7.x]

## 8.x delta (from 7.x)
- Events dispatch by class. Removed `EmailEvents` constants (20) and their subscription keys:

| Removed constant | Subscribe to |
|---|---|
| `EMAIL_ON_BUILD` | `EmailOnBuildEvent` |
| `EMAIL_ON_DISPLAY` | `EmailDisplayEvent` |
| `EMAIL_ON_REPLY` | `EmailReplyEvent` |
| `EMAIL_ON_TOGGLE_PUBLISH` | `EmailOnTogglePublishEvent` |
| `EMAIL_PARSE` | `ParseEmailEvent` |
| `EMAIL_PRE_FETCH` | `PreFetchEmailEvent` |
| `EMAIL_PRE_SAVE` / `EMAIL_POST_SAVE` | `EmailPreSaveEvent` / `EmailPostSaveEvent` |
| `EMAIL_PRE_DELETE` / `EMAIL_POST_DELETE` | `EmailPreDeleteEvent` / `EmailPostDeleteEvent` |
| `EMAIL_PRE_SEND` | `EmailPreSendEvent` |
| `MONITORED_EMAIL_CONFIG` | `MonitoredEmailEvent` |
| `ON_EMAIL_ADDRESS_TOKEN_REPLACEMENT` | `OnEmailAddressTokenReplacementEvent` |
| `ON_EMAIL_EDIT_SUBMIT` | `EmailEditSubmitEvent` |
| `ON_EMAIL_STAT_PRE_SAVE` / `ON_EMAIL_STAT_POST_SAVE` | `EmailStatEvent` / `EmailStatPostSaveEvent` |
| `ON_EMAIL_VALIDATION` | `EmailValidationEvent` |
| `ON_TRANSPORT_WEBHOOK` | `TransportWebhookEvent` |
| `TOKEN_REPLACEMENT` | `Mautic\CoreBundle\Event\TokenReplacementEvent` |
| `ON_CAMPAIGN_TRIGGER_ACTION` | none - register `batchEventName` => `ON_CAMPAIGN_BATCH_ACTION` and handle `PendingEvent` |

  [code: UPGRADE-8.0.md @8.x] [PR #17217] [PR #17675] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/emails.html#rendering-custom-tokens]
- Kept constants: `EMAIL_ON_OPEN`, `EMAIL_ON_SEND`, `EMAIL_FAILED`, `EMAIL_RESEND`, campaign constants, `ON_SENT_EMAIL_TO_USER`, `ON_DETERMINE_*`. `EMAIL_ON_OPEN` and `EMAIL_ON_SEND` are kept as webhook type ids but are not dispatched under those names, so a listener keyed on them loads and never fires. [code: UPGRADE-8.0.md @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/emails.html#rendering-custom-tokens]
- `ParseEmailEvent` criteria methods moved to new `PreFetchEmailEvent`. [PR #17675]
- `MailHelper` is `final`; `MailHelper::validateEmail()` removed (use `EmailValidator`). [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- Return types: `Email::getContent(): array|string`, `getUtmTags()`, `getHeaders()`, `Stat::getOpenDetails()`, `EmailSendEvent::getSource()` return `array`; `Stat::getTokens(): ?array`; `EmailDraft::getHtml()/getTemplate(): ?string`; `EmailModel::getEmailStatus(string)`, `removeDoNotContact(string)`. [code: UPGRADE-8.0.md @8.x]
- `MonitoredEmail\Processor\Bounce\Definition\Rule` deleted (not in UPGRADE-8.0.md). [PR #17183]
- `mautic:disable-tracking` links are tracked in 8.x. [docs: https://docs.mautic.org/en/8.0/channels/emails.html#tracking-links-in-emails]
- `BuilderEvent::addTokensFromHelper()`/`getTokensFromHelper()` removed. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/emails.html#deprecated-methods]
- Custom Email list search commands via `SearchCommandEvent`/`SearchQueryEvent`/`SearchHelpEvent` with `checkContext('email')`. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/emails.html#custom-search-commands]
- `CacheStorageHelper` is replaced by CacheBundle; a cache miss returns `null`, not `false` (affects email pending/delivered caches in plugins). [PR #17033] [PR #17155]
- Emoji are stored/rendered as UTF-8 with no shortcode conversion. [PR #17026]
- `--lock_mode=file_lock` fails on moderated commands such as `mautic:broadcasts:send` and `mautic:email:sendwinner`; use `flock`. [code: UPGRADE-8.0.md @8.x]
- 8.x requires PHP 8.4, Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4. [code: UPGRADE-8.0.md @8.x]

## Writing code that works on 7.x and 8.x
- Subscribe by class and, for 7.x, also by the string constant guarded with `defined()`; type-hint shared parent classes. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- Register campaign email-like actions with `batchEventName` and handle `PendingEvent`.
- Use `data-mautic-disable-tracking="true"`, never `mautic:disable-tracking`.
- Compose instead of extending `MailHelper`.

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
