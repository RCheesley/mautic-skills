# Mautic Emails - docs digest

What docs.mautic.org (7.2 and 8.0), devdocs.mautic.org and kb.mautic.org say about Emails. Statements are the docs'
claims; where the 7.2.1 code differs, see "Discrepancies" at the end and references/behaviour.md section 16.

Main pages:
- User docs, Emails: https://docs.mautic.org/en/7.2/channels/emails.html (8.0: https://docs.mautic.org/en/8.0/channels/emails.html)
- Settings: https://docs.mautic.org/en/7.2/configuration/settings.html
- Cron jobs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html
- Variables: https://docs.mautic.org/en/7.2/configuration/variables.html
- S/MIME: https://docs.mautic.org/en/7.2/configuration/smime_email_signing.html
- Message queue: https://docs.mautic.org/en/7.2/queue/message_queue.html
- Devdocs, email extensions: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html (8.0: https://devdocs.mautic.org/en/8.0/plugin_extensions/emails.html)
- REST API, Emails: https://devdocs.mautic.org/en/7.2/rest_api/emails.html

## Contents
1. Terminology
2. Email types and sending
3. A/B testing
4. Details page, preview, drafts, translations, cloning, examples
5. Tokens and sender resolution
6. Tracking
7. Unsubscribe, Preference Centre, web view
8. Bounces, replies, monitored inbox
9. Transport, queue and cron settings
10. REST API
11. Developer contracts
12. Knowledge base
13. Procedures
14. 8.0 docs changes
15. Discrepancies with code

## 1. Terminology
- Use "Email", "Contact", "Segment", "Campaign", "Do Not Contact (DNC)", "Preference Center"; "Segment Email" = broadcast; "template Email" = triggered/transactional by default. UI status labels are Active/Unavailable. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#email-types]
- "Preference Center" (8.0) vs "preferences center"/"preference centre" (7.2) are used inconsistently. [docs: https://docs.mautic.org/en/8.0/channels/emails.html#unsubscribing]

## 2. Email types and sending
- Two types: template and Segment (broadcast). [docs: https://docs.mautic.org/en/7.2/channels/emails.html#email-types]
- Template Emails are transactional by default, used by Campaigns, Form actions and Point Triggers, and can be sent many times to a Contact. A direct send from a Contact clones the content, so stats are not tracked against the template. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#template-emails]
- Segment Emails are marketing by default; each Contact receives one once; an "excluding Segments" field removes members of other Segments. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#segment-broadcast-emails] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#excluding-segments]
- Segment Email sending is started by the "Send Scheduled Broadcasts" cron (`mautic:broadcasts:send`). [docs: https://docs.mautic.org/en/7.2/channels/emails.html#excluding-segments]
- "Send to unsubscribed contacts" (Advanced tab) sends to unsubscribed Contacts, is for transactional messages only, needs the matching Role permission, and exempts the email from frequency rules. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#send-to-unsubscribed-contacts] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#frequency-rules-behavior]

## 3. A/B testing
- Only a Segment Email with zero sends can be converted; settings: How to pick the winner (Read rate, Clickthrough rate...), Wait before picking winner (24 h default), Test audience size (10% default, split evenly). [docs: https://docs.mautic.org/en/7.2/channels/emails.html#converting-an-email-to-an-a-b-test]
- The original counts as a variant; at least two variants are needed; the header Send button is hidden and sending is scheduled from the A/B panel; after the wait, the winner gets a Winner badge and goes to the rest. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#scheduling-the-a-b-test] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#sending-and-determining-the-winner]
- `mautic:email:sendwinner [--id]` picks the winner after the wait time and sends the rest through the broadcast command. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#determine-a-b-test-winner-cron-job]

## 4. Details page, preview, drafts, translations, cloning, examples
- Stat cards: Sent, Read, Queued (frequency rules), Pending (Segment Emails only). [docs: https://docs.mautic.org/en/7.2/channels/emails.html#segments-used]
- Drafts need `'email_draft_enabled' => 1` in `local.php`; one draft per email; drafts cover content only; preview with `/draft`. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#creating-a-draft-email]
- Translations: a Contact with a preferred language gets the matching translation, else the parent. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#translations]
- "Clone with translations and variants" creates Unavailable copies with `(copy)` appended. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#clone-with-translations-and-variants]
- "Send example" goes to Users; trackable links and unsubscribe behave differently. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#sending-an-example-email]

## 5. Tokens and sender resolution
- `{contactfield=alias}`, defaults after `|`, `|true` URL-encodes, `|datetime`/`|date`/`|time`, `|label`. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tokens] [docs: https://docs.mautic.org/en/7.2/configuration/variables.html]
- Owner tokens `{ownerfield=firstname|lastname|email|position|signature}`; tokens in link URLs resolve at click time on tracked links only. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tokens-in-link-urls]
- From priority: tokenized Advanced From (if valid), owner (Mailer is owner), plain Advanced From, system default. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#sender-resolution-hierarchy]
- Reply-To priority: email Reply-To, owner (Use owner as mailer), email From, global Reply-To, system From. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#reply-to-resolution-hierarchy]
- Signatures: default `Best regards,<br/>|FROM_NAME|.`; owner signature only when the email has Use owner as mailer and the Contact has an owner. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#signatures]
- Every owner domain needs SPF and DKIM when Mailer is owner is on. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mail-send-settings]

## 6. Tracking
- A 1-pixel GIF is added before `</body>`; `{tracking_pixel}` relocates it; "Append tracking pixel" = No disables opens and open decisions. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tracking-opened-emails] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#message-settings]
- All links become redirect links; `data-mautic-disable-tracking="true"` disables one link; "Disable trackable URLs" disables all. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tracking-links-in-emails]
- Link validation accepts `http`, `https`, `ftp`, `ftps`, `mailto`, `tel`, `sms`, anchors and Mautic tokens. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#link-validation]

## 7. Unsubscribe, Preference Centre, web view
- `{unsubscribe_text}`, `{unsubscribe_url}` (Preference Centre if active), `{resubscribe_url}`, `{dnc_url}`, `{webview_url}`. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#unsubscribing]
- "Disable unsubscribe link in header" = No adds RFC 8058 `List-Unsubscribe` and `List-Unsubscribe-Post` when "Send to unsubscribed contacts" is off. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#unsubscribe-settings]
- With "Show Contact preference settings" and no Preference Centre page, a default page is generated; the default Preference Centre page is resolved at unsubscribe time. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#unsubscribe-settings]
- Unsubscribe links do not work in test emails. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#unsubscribe-link-doesn-t-work]

## 8. Bounces, replies, monitored inbox
- IMAP monitoring uses `+bounce_<hash>` and `+unsubscribe_<hash>` addresses; providers that rewrite Return-Path (Gmail, Amazon SES) break it. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#bounce-management]
- Since Mautic 5 all transports use `https://mautic.example.com/mailer/callback`. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#webhook-bounce-management]
- Replies need PHP IMAP, an inbox other than Google/Yahoo, and `mautic:email:fetch`. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#contact-replies]
- Segment bounced Contacts with the filter "Bounced Email equals Yes". [docs: https://docs.mautic.org/en/7.2/channels/emails.html#create-a-segment-with-bounced-emails]

## 9. Transport, queue and cron settings
- Symfony Mailer since 5; SMTP default; DSN must be URL-encoded in `local.php`; ports 465/587. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#smtp-transport]
- Generic Symfony API transports do not batch and do not process bounce callbacks; Mautic transport plugins do. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#example-api-transport-installation]
- Queueing is off by default (`sync://`); transports Doctrine, Redis, AMQP, Beanstalkd, SQS; consume with `messenger:consume email` under Supervisor/systemd, or from cron with `--limit`/`--time-limit`/`--memory-limit`. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#how-to-enable-the-queuing] [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#process-email-queue-cron-job]
- Retry defaults 3 / 1000 ms / x2 / no max; failed messages are discarded unless a failure queue is set. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#retry-strategy]
- `mautic:broadcasts:send`: email needs a publish-up date and be published; `--limit` default 100; `--min/max-contact-id` for parallel runs. [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-broadcasts-segment-emails-cron-job]
- `mautic:messages:send` processes messages held by frequency rules; queue priority High/Normal (broadcasts Normal). [docs: https://docs.mautic.org/en/7.2/queue/message_queue.html]
- Default frequency rule "Do Not Contact more than N each day/week/month"; "Send to unsubscribed contacts" emails do not count. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#default-frequency-rule]
- S/MIME: SMTP only, signs only, `local.php` only; cert files named by From address. [docs: https://docs.mautic.org/en/7.2/configuration/smime_email_signing.html]

## 10. REST API
| Method | Path | Notes |
|---|---|---|
| GET | `/api/emails/ID` | Full entity incl. `emailType`, `sendToDnc`, `lists`, `dynamicContent`, `headers`, `settings` |
| GET | `/api/emails` | `search`, `start`, `limit` (30), `orderBy`, `orderByDir`, `publishedOnly`, `minimal` |
| POST | `/api/emails/new` | `name`, `subject`, `language`, `lists` documented as required |
| PUT/PATCH | `/api/emails/ID/edit` | PUT omitting `sendToDnc` resets it to false |
| DELETE | `/api/emails/ID/delete` | Returns deleted data |
| POST | `/api/emails/ID/contact/CONTACT_ID/send` | `tokens`; DNC Contacts skipped silently unless `sendToDnc` |
| POST | `/api/emails/ID/send` | Documented body `listIds` |
| POST | `/api/emails/reply/TRACKING_HASH` | 201 |

Source: [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/emails.html]. Setting `sendToDnc` needs `email:emails:sendtodnc`; otherwise ignored. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/emails.html#create-email]

## 11. Developer contracts
- Tokens: `EMAIL_ON_BUILD` (`addToken`) and `EMAIL_ON_SEND`/`EMAIL_ON_DISPLAY` (`addToken`, `getContent`/`setContent`). [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-tokens]
- `settings` JSON column with `settings_<key>` magic properties. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-settings]
- `BuilderTokenHelperFactory`; `BuilderEvent::addTokensFromHelper()`/`getTokensFromHelper()` deprecated in 7.2. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#deprecated-methods]
- A/B criteria: `addAbTestWinnerCriteria` + `DetermineWinnerEvent::setAbTestResults`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-a-b-testing]
- Monitored inbox events `MONITORED_EMAIL_CONFIG`, `EMAIL_PRE_FETCH`, `EMAIL_PARSE`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#monitored-inbox-integration]
- Transport testing checklist: Test Connection, unicode, template and Segment emails with BCC, Reply-To, attachments, custom headers, report emails, forgot-password. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#testing-email-transports]

## 12. Knowledge base
Version status of KB articles: k-10things and k-sesrate describe the pre-5 spool (`mautic:emails:send`) and are outdated; k-doctrine (Messenger) and k-transact (5.0+) are current. [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html] [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html]
- Doctrine queue: messages in `messenger_messages`; worker `messenger:consume email --limit=60 --time-limit=480 --memory-limit=128M` every 10 minutes behind a lock file; watch table size. [kb: https://kb.mautic.org/article/configuring-doctrine-for-email-queue-management-in-mautic-with-cron-jobs.html]
- One email id is sent once per Contact on a real Segment send; duplicate the email to resend. [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html]
- A queued (postponed) email exceeded the frequency rule. Contacts stay in Segments after unsubscribing unless filters remove them. [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html]
- Test emails: links are not rewritten, unsubscribe does not work, opens/clicks are not tracked; test properly with a tagged test Segment and a real send. [kb: https://kb.mautic.org/article/how-to-test-emails-in-mautic.html]
- SendGrid: `composer require symfony/sendgrid-mailer`, DSN `sendgrid+api://KEY@default`; turn off SendGrid click/open tracking. [kb: https://kb.mautic.org/article/how-to-use-the-sendgrid-api-in-mautic-5-with-symfony-mailer.html]
- Amazon SES: Sandbox causes webhook payload errors; region must match. [kb: https://kb.mautic.org/article/mautic-and-amazon-ses-troubleshooting.html]
- A/B (4.x-era): variants created unpublished; trophy ends the test early. [kb: https://kb.mautic.org/article/how-to-create-an-a-b-test-for-emails-in-mautic.html]
- An API "success" means queued, not delivered. [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html]

## 13. Procedures
- Convert to A/B: unsent Segment Email -> Convert to A/B test -> criteria/wait/size -> Add variant -> Schedule sending. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#a-b-testing-for-segment-emails]
- Mailer as owner: Configuration -> Email Settings -> Mailer is owner = Yes; override per email. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#mailer-as-owner]
- Reply monitoring: copy sender addresses to one inbox -> IMAP config -> cron `mautic:email:fetch` -> "Contact replies" decision. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#contact-replies]
- Troubleshoot sending: credentials/port, test email recipient, queue mode and consumer, `broadcasts:send`/`campaigns:trigger` crons, frequency rule, Segment counts, the once-per-email rule. [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html]

## 14. 8.0 docs changes
- Company preview selector, open/download preview HTML. [docs: https://docs.mautic.org/en/8.0/channels/emails.html#opening-and-downloading-the-email-preview]
- Unsubscribe/resubscribe confirm-address page and "Require email validation for unsubscribe" (on by default). [docs: https://docs.mautic.org/en/8.0/channels/emails.html#unsubscribing] [docs: https://docs.mautic.org/en/8.0/configuration/settings.html#unsubscribe-settings]
- `mautic:disable-tracking` removed in 8.0. [docs: https://docs.mautic.org/en/8.0/channels/emails.html#tracking-links-in-emails]
- Event classes `EmailOnBuildEvent`, `EmailSendEvent`, `EmailDisplayEvent`; `EMAIL_ON_BUILD`/`EMAIL_ON_DISPLAY` removed; `EMAIL_ON_SEND` kept but not dispatched; `PreFetchEmailEvent`; `EmailOnTogglePublishEvent`; custom search commands. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/emails.html]

## 15. Discrepancies with code
See references/behaviour.md section 16. Summary: `sendToDnc` vs bounced, transactional vs DNC (KB), `listIds` vs `lists`,
later Segment members and unpublish date, `mautic:disable:tracking` spelling, `/mailer/{transport}/callback`,
Swiftmailer-era transport docs, the legacy Queue page (`mautic:queue:process`, `mautic:email:send`), and the unreleased 7.x (post-7.2.1)
unsubscribe validation feature documented only on the 8.0 branch.
