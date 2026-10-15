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
- 5.0 (PR history): campaign "transactional" sends and the API direct send ignored DNC [PR #11786]; transactional, direct and API sends got no `List-Unsubscribe` [PR #11787]; both rules held until 7.1 [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php @7.1.0] [code: app/bundles/EmailBundle/Helper/MailHelper.php:1327 @7.1.0].
- 5.0: RFC 8058 `List-Unsubscribe-Post` one-click [PR #13103]; `--limit`/`--batch` semantics aligned with SMS and thread options added to `mautic:broadcasts:send` [PR #11127] [PR #11549]; manual send batch size from `mailer_memory_msg_limit` [PR #11167] [PR #11595]; clones clear publish dates [PR #12784]; `{today}` token [PR #11722].
- 5.1: excluded Segments [PR #13458]; HTTPS before `mailto:` in List-Unsubscribe [PR #13407]; `EMAIL_PRE_SEND` skip event [PR #13360]; retry 3 times before DNC [PR #13341]; tokenised From [PR #7811]; Category opt-out respected [PR #10879]; HMAC address fallback in unsubscribe URLs [PR #10846].
- 5.2: campaign default type Marketing [PR #14145]; drafts (`email_draft_enabled`) [PR #14028]; Preheader [PR #13792]; `{dnc_url}` and `{resubscribe_url}` [PR #14114] [PR #14215]; public preview allowed for unpublished/expired emails [PR #14525]; "Template email" renamed "Trigger email" [PR #14084].

## 6.x
- 6.0: bot-ratio filtering of opens and clicks (`bot_helper_blocked_ip_addresses`, `bot_helper_blocked_user_agents`, 2 s threshold, ratio 0.6) [PR #14593].
- 6.0: a last-moment duplicate check before each Segment send [PR #14531]; campaign Email Metrics tab with `campaign_email_stats_enabled` [PR #14414]; tokenised transports use the direct-send From [PR #14661].
- 6.0: Preference Centre language order Contact, page, user, system [PR #14370]; `MauticFactory` getters replaced by DI (target version disputed) [PR #14382] [PR #14611].
- 6.0.x: multi-folder IMAP fetch fixed [PR #15364]; ANSI-quote-safe stats SQL [PR #15324]; Internal Name limited to 190 characters [PR #15147].

## 7.x
- 7.0 (PR history): schedule send and "Continue sending to new contacts" [PR #14254]; publish fields back on trigger emails [PR #15506]; publish permission enforced on save and API [PR #15543]; `sent_time` in pixel and `ct` [PR #14816]; Outlook bounce codes [PR #15371].
- 7.1: S/MIME signing (`smime_signing_enabled`, certificates in `%kernel.project_dir%/var/smime_certificates`) [PR #15563] [code: app/bundles/EmailBundle/Config/config.php:222-223 @7.x]; optimistic locking [PR #15774] [PR #15894]; default `mailer_dsn` `smtp://localhost:1025` [PR #15627]; campaign selector shows top-level emails only [PR #15745].
- 7.1.0 to 7.1.x: an unconditional `Sender` header broke VERP bounce detection; fixed in 7.2 [PR #15674] [PR #16152].
- 7.2: "Send to unsubscribed contacts" (`sendToDnc`) replaces the campaign transactional DNC bypass and List-Unsubscribe rule; the campaign switch is "Repeatable email" [PR #15995] [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:274-286 @7.x]; `disable_unsubscribe_link_header` first appears in the 7.2.0 tag [code: app/bundles/EmailBundle/Config/config.php:198 @7.x].
- 7.2: Segment Email A/B tests [PR #15897]; tokenised From chain [PR #16060]; `{signature}` follows the per-email owner switch [PR #15931]; link validation on save [PR #16256] [PR #16508]; Preference Centre resolved at unsubscribe [PR #16352].
- 7.x after 7.2.1 (unreleased): A/B winner through the broadcast pipeline [PR #17296]; Reply-To final rule, email From before global reply-to [PR #17356]; public preview needs the published flag for anonymous viewers [PR #17549] [code: app/bundles/EmailBundle/Controller/PublicController.php:561-575 @7.x].
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
