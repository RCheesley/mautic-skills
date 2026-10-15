# Mautic Emails - behaviour specification (7.x)

Authoritative for Mautic 7.x (commit 419a08a9b35: release 7.2.1 plus unreleased merged PRs). Every item is cited; all paths are repo-relative. Where docs and code disagree, the code statement is given and the discrepancy is listed in
section 16.

## Contents
1. Email types, saving and lifecycle (B1-B13)
2. Publishing and scheduling of Segment Emails (B14-B19)
3. Eligibility: who receives a Segment Email (B20-B23)
4. The common send path `sendEmail()` (B24-B33)
5. Stat and copy contents, counters (B34-B37)
6. From, Reply-To, Return-Path, headers, attachments (B38-B47)
7. Tokens and content generation (B48-B56) + token reference table
8. Open, click and webview tracking (B57-B62)
9. Replies (B63)
10. Unsubscribe, resubscribe, Preference Centre, DNC (B64-B70)
11. Bounces, monitored inbox and transport callbacks (B71-B76)
12. Campaigns, Points, Forms, Webhooks, message queue (B77-B84)
13. A/B testing (B85-B90)
14. UI, API, examples, previews, search, reports (B91-B101)
15. Transports and Messenger queueing (B102-B112)
16. Doc/code discrepancies and open questions

---

## 1. Email types, saving and lifecycle

B1. An email whose type is empty on save becomes `template`; a `list` (Segment) email that is a translation inherits its parent's Segments; a non-Segment email has its Segments cleared on every save. [code: app/bundles/EmailBundle/Model/EmailModel.php:221-239 @7.x]

B2. Every save of an existing email increments `revision`, except the automatic re-save of translation children; translation children of a Segment Email are re-saved so they share the parent's Segments. [code: app/bundles/EmailBundle/Model/EmailModel.php:241-247 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:264-271 @7.x]

B3. Saving a variant with any change resets `variant_sent_count`, `variant_read_count` and sets `variant_start_date = now` on all related variants, unless the entity is unpublished (and was not just unpublished) or the save is part of a winner conversion. [code: app/bundles/EmailBundle/Model/EmailModel.php:249-260 @7.x] [code: app/bundles/CoreBundle/Model/VariantModelTrait.php:81-137 @7.x]

B4. On `EMAIL_PRE_SAVE` a variant child copies `publishUp`, `publishDown`, `isPublished` and Segments from its parent (or the parent pushes them to all children). [code: app/bundles/EmailBundle/EventListener/EmailSubscriber.php:59-65 @7.x] [code: app/bundles/EmailBundle/Entity/EmailRepository.php:788-810 @7.x]

B5. Deleting a published variant resets the remaining variants' counters and start date first; deleting an email also deletes its draft and writes an audit-log `delete` entry. Stats are kept with `email_id = NULL`. [code: app/bundles/EmailBundle/Model/EmailModel.php:311-318 @7.x] [code: app/bundles/EmailBundle/EventListener/EmailSubscriber.php:109-121 @7.x] [code: app/bundles/EmailBundle/Entity/Stat.php:144-147 @7.x]

B6. Audit log `create`/`update` entries record the entity `changes` array; Segment changes are recorded under `lists` and `excludedLists`. [code: app/bundles/EmailBundle/EventListener/EmailSubscriber.php:70-84 @7.x] [code: app/bundles/EmailBundle/Entity/Email.php:1339-1400 @7.x]

B7. New (non-clone) emails get the global default UTM tags when none are set; the default is not recorded as a user change. Existing and cloned emails keep their own values. [code: app/bundles/EmailBundle/EventListener/EmailDefaultsSubscriber.php:26-35 @7.x] [code: app/bundles/EmailBundle/Helper/EmailDefaultsHelper.php:56-74 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#message-settings]

B8. New emails default `useOwnerAsMailer` to the global `mailer_is_owner`; existing emails keep their value. [code: app/bundles/EmailBundle/Form/Type/EmailType.php:709-717 @7.x]

B9. Validation: name and subject are required and at most 190 characters; preheader at most 130; From must be one address or a `{contactfield=alias}` token (optionally `|default`); the subject must not contain non-text dynamic content; a Segment Email that is not a translation needs at least one Segment the user can access and must not include and exclude the same Segment. [code: app/bundles/EmailBundle/Entity/Email.php:472-549 @7.x] [code: app/bundles/EmailBundle/Validator/EmailListsValidator.php:18-68 @7.x] [code: app/bundles/EmailBundle/Validator/EmailOrEmailTokenListValidator.php:30-80 @7.x]

B9a. Every `href` must use `http`, `https`, `ftp`, `ftps`, `mailto`, `tel` or `sms`, be an anchor, or be a Mautic token; otherwise the save fails with "The email contains an invalid URL". [code: app/bundles/EmailBundle/Validator/ValidEmailLinksValidator.php:17-106 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#link-validation]

B9b. Variant weights summing to more than 100 are rejected. [code: app/bundles/EmailBundle/Entity/Email.php:530-548 @7.x]

B10. The date-range validator rejects `publishDown <= publishUp` only when Continue sending is on. [code: app/bundles/EmailBundle/Validator/ScheduleDateRangeValidator.php:14-48 @7.x]

B11. "Clone with translations and variants" produces copies named `<name> (copy)` (truncated to 190) with parent/child links re-created. [code: app/bundles/EmailBundle/Model/EmailModel.php:178-217 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#clone-with-translations-and-variants]

B11a. `__clone` resets id, counters, revision, variant counters, `emailType` (to null), plain text, publish dates and `continueSending`, and clears translations, variants, stats and draft. [code: app/bundles/EmailBundle/Entity/Email.php:323-346 @7.x]

B12. Editing uses optimistic locking through the `version` field; a stale version is rejected. [code: app/bundles/EmailBundle/Controller/EmailController.php:770-778 @7.x] [code: app/bundles/EmailBundle/Entity/Email.php:469 @7.x]

B13. Drafts (only when `email_draft_enabled`): "Save as draft" stores HTML/template in `emails_draft` and reverts the live email; "Apply draft" deletes the draft keeping the edits; "Discard draft" reverts everything except id/type and deletes the draft. Only content is drafted; subject, name and Segments apply to the live email. [code: app/bundles/EmailBundle/EventListener/EmailSubscriber.php:176-244 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#creating-a-draft-email]

## 2. Publishing and scheduling of Segment Emails

B14. An email is "published" only when `is_published = 1`, `publish_up` is null or past, `publish_down` is null or future, and its Category (if any) is published. For a Segment Email with Continue sending off, `getPublishDown()` returns null, so `publish_down` never expires it. [code: app/bundles/CoreBundle/Entity/FormEntity.php:233-251 @7.x] [code: app/bundles/EmailBundle/Entity/Email.php:933-940 @7.x]

B15. "Schedule send" sets `publishUp`, `publishDown`, `continueSending` and forces `isPublished = true`; "cancel" clears all three. [code: app/bundles/EmailBundle/Controller/EmailController.php:1687-1702 @7.x]

B16. `mautic:broadcasts:send` considers only emails with type `list`, `isPublished = 1`, `publishUp` not null and `<= now`, and `publishDown` null or `>= now`; a null `publishUp` is allowed only when sending an A/B winner by id. Variant children are skipped. [code: app/bundles/EmailBundle/Entity/EmailRepository.php:892-914 @7.x] [code: app/bundles/EmailBundle/EventListener/BroadcastSubscriber.php:38-45 @7.x]

B16a. Broadcast defaults when options are omitted: limit 100, batch 50; `--thread-id` greater than `--max-threads` fails; lock key `<channel>-<id>-<threadId>-<maxThreads>`. [code: app/bundles/ChannelBundle/Command/SendChannelBroadcastCommand.php:22-184 @7.x] [code: app/bundles/ChannelBundle/Event/ChannelBroadcastEvent.php:34-39 @7.x]

B17. After a broadcast pass, a Segment Email that is not Continue sending, is not an undecided A/B test, and has sent before is unpublished when nothing is pending and nothing was sent in this pass (thread 1 / non-parallel only). [code: app/bundles/EmailBundle/EventListener/BroadcastSubscriber.php:99-108 @7.x] [code: app/bundles/EmailBundle/Entity/Email.php:1453-1464 @7.x]

B18. The UI sending status is `sent` (published, not Continue sending, nothing pending, something sent), `sending` (pending > 0), or the publish status. [code: app/bundles/EmailBundle/Entity/Email.php:1431-1451 @7.x]

B19. The pending count is cached under `email|<id>|pending`. It is invalidated for every Segment Email that includes or excludes a Segment when that Segment changes (`LEAD_LIST_CHANGE`, `LEAD_LIST_BATCH_CHANGE`); `getEntity()`/`getEntities()` recompute it when cold. It is not invalidated by new DNC rows or deleted stats. [code: app/bundles/EmailBundle/Model/EmailModel.php:1024-1034 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:2394-2431 @7.x] [code: app/bundles/EmailBundle/EventListener/SegmentSubscriber.php:19-30 @7.x]

B19a. Stat cards: Sent (successful and failed), Read (with %), Queued (held by frequency rules), Pending (Segment Emails only); Campaign-triggered emails show no Pending card. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#segments-used]

## 3. Eligibility: who receives a Segment Email

B20. A Contact is pending for Segment Email E only if ALL of these hold [code: app/bundles/EmailBundle/Entity/EmailRepository.php:183-345 @7.x]:
- a. member of at least one included Segment with `manually_removed = 0` [code: app/bundles/EmailBundle/Entity/EmailRepository.php:267-300 @7.x];
- b. no `lead_donotcontact` row with channel `email`, whatever the reason [code: app/bundles/EmailBundle/Entity/EmailRepository.php:197-206 @7.x];
- c. no `email_stats` row for E or any of E's variants/translations; stats of deleted Contacts (`lead_id` null) do not block others [code: app/bundles/EmailBundle/Entity/EmailRepository.php:221-241 @7.x];
- d. no unsent `message_queue` row for channel `email` and E or its variants [code: app/bundles/EmailBundle/Entity/EmailRepository.php:209-218 @7.x];
- e. not a member of any excluded Segment [code: app/bundles/EmailBundle/Entity/EmailRepository.php:310-315 @7.x];
- f. not opted out (`lead_categories.manually_removed = 1`) of E's Category [code: app/bundles/EmailBundle/Entity/EmailRepository.php:318-319 @7.x];
- g. a non-empty `email` [code: app/bundles/EmailBundle/Entity/EmailRepository.php:324-329 @7.x];
- h. inside the optional min/max contact-id window and thread shard `MOD(id + threadId - 1, maxThreads) = 0` [code: app/bundles/EmailBundle/Entity/EmailRepository.php:321-337 @7.x];
- i. when Continue sending is off, Segment membership `date_added` strictly before `publishUp` [code: app/bundles/EmailBundle/Model/EmailModel.php:1021 @7.x] [code: app/bundles/EmailBundle/Entity/EmailRepository.php:285-288 @7.x].

B21. `sendEmailToLists` returns `[0, 0, []]` without sending when the email is not type `list` or not published (dates and Category included). [code: app/bundles/EmailBundle/Model/EmailModel.php:1098-1107 @7.x]

B22. Segment sends use source `['email', id]`, `allowResends = false`, and headers `Precedence: Bulk` and `X-EMAIL-ID: <id>`. [code: app/bundles/EmailBundle/Model/EmailModel.php:1109-1116 @7.x]

B23. `limit` caps Contacts loaded per call across all Segments; `batch` loops in batches until nothing is pending. `Stat.list_id` records only the Segment being iterated when the stat was created. [code: app/bundles/EmailBundle/Model/EmailModel.php:1120-1194 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:1135-1150 @7.x]

## 4. The common send path `sendEmail()`

B24. Unless `ignoreDNC` is true, every Contact with any email DNC row (any reason) is removed; with `dnc_as_error` the error "Contact has requested to not be emailed." is returned. [code: app/bundles/EmailBundle/Model/EmailModel.php:1399-1409 @7.x] [code: app/bundles/EmailBundle/Entity/EmailRepository.php:53-77 @7.x]

B25. Unless the email has `sendToDnc`, frequency rules apply: Contacts over their own rule (`lead_frequencyrules`, counting `email_stats.date_sent` of emails with `send_to_dnc = 0` in the last DAY/WEEK/MONTH) or the global `email_frequency_number/time` are removed and queued in `message_queue` (or rescheduled) with attempts (default 3) and priority. [code: app/bundles/EmailBundle/Model/EmailModel.php:1412-1425 @7.x] [code: app/bundles/ChannelBundle/Model/MessageQueueModel.php:68-119 @7.x] [code: app/bundles/LeadBundle/Entity/FrequencyRuleRepository.php:122-230 @7.x]

B26. For a Segment Email each Contact is skipped if a non-failed stat already exists for that Contact and email (second guard after the pending query). [code: app/bundles/EmailBundle/Model/EmailModel.php:1507-1514 @7.x] [code: app/bundles/EmailBundle/Entity/StatRepository.php:663-676 @7.x]

B27. Contacts are shuffled and split between the parent and published variants proportionally to `send_weight`; within a variant, Contacts go to a published translation matching `preferred_locale` (exact `xx_YY`, else first `xx`), the rest get the default language. [code: app/bundles/EmailBundle/Model/EmailModel.php:1442-1494 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:1204-1343 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#translations]

B28. Contacts are hydrated with Company fields before token replacement. [code: app/bundles/EmailBundle/Model/EmailModel.php:2184-2214 @7.x]

B29. After a batch, `emails.sent_count` (and `variant_sent_count`) is incremented by the number of created stats, retrying 3 times on DB errors. [code: app/bundles/EmailBundle/Model/EmailModel.php:1548-1562 @7.x] [code: app/bundles/EmailBundle/Entity/EmailRepository.php:812-846 @7.x]

B30. Return value: for one Contact (`$leads['id']` set) a bool or, with `return_errors`, the error string; for many, the `[leadId => email]` failed map or `[leadId => message]`. [code: app/bundles/EmailBundle/Model/EmailModel.php:1376-1399 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:1566-1571 @7.x]

B31. An address the mailer rejects (RFC) fails, its stat is deleted, and DNC `BOUNCED` "Incorrectly formatted email address" with channel `['email' => emailId]` is written on `finalFlush`. [code: app/bundles/EmailBundle/Model/SendEmailToContact.php:143-154 @7.x] [code: app/bundles/EmailBundle/Model/SendEmailToContact.php:270-285 @7.x]

B32. A transport exception fails every recipient of that message (To/Cc/Bcc and, in batch mode, all metadata recipients); stats are deleted and counts decremented. [code: app/bundles/EmailBundle/Helper/MailHelper.php:409-426 @7.x] [code: app/bundles/EmailBundle/Model/SendEmailToContact.php:241-265 @7.x]

B33. The stat is persisted before the message reaches the transport (so the pixel can resolve it) and deleted on failure; stats are detached from the EntityManager. [code: app/bundles/EmailBundle/Model/SendEmailToContact.php:287-346 @7.x] [code: app/bundles/EmailBundle/Stat/StatHelper.php:27-48 @7.x]

## 5. Stat and copy contents, counters

B34. Each stat stores `date_sent`, email, Contact, `email_address`, `list_id` (Segment send), `tracking_hash`, `source`/`source_id`, the full token map and a `Copy` reference. The copy id is the email id for an Email entity (else MD5 of subject+body) and holds subject, HTML and plain text, created once per content hash. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1679-1762 @7.x]

B35. Delivered = `sent_count - failed stats - BOUNCED DNC rows for the email`, never negative. [code: app/bundles/EmailBundle/Model/EmailModel.php:1056-1069 @7.x]

B36. Merging Contacts moves all `email_stats.lead_id` from loser to winner. [code: app/bundles/EmailBundle/EventListener/LeadSubscriber.php:43-49 @7.x]

B37. EmailBundle has no stat retention or purge; stats are deleted only on send failure, and a deleted Contact leaves its stats with `lead_id` null. [code: app/bundles/EmailBundle/Entity/StatRepository.php:628-643 @7.x] [code: app/bundles/EmailBundle/Entity/Stat.php:149 @7.x]

## 6. From, Reply-To, Return-Path, headers, attachments

B38. From (direct send): if `useOwnerAsMailer` and the Contact has an existing owner, the owner's name/email; else the email's From name/address (each falls back to system); `{contactfield=...}` tokens in From are resolved per Contact, falling back to owner (batch) or system default. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1963-1995 @7.x] [code: app/bundles/EmailBundle/Helper/FromEmailHelper.php:42-77 @7.x] [code: app/bundles/EmailBundle/Helper/FromEmailHelper.php:140-240 @7.x]

B38a. Docs priority: (1) tokenized Advanced From that resolves to a valid value, (2) owner when Mailer is owner applies, (3) plain Advanced From, (4) system default. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#sender-resolution-hierarchy] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#mail-send-settings]

B39. Reply-To (direct send): email `replyToAddress`, then the owner's email when the Contact has an owner and owner-as-mailer applies, then email From, then global `mailer_reply_to_email`, then system From. Batch sends use the batch owner in step 2. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1997-2054 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#reply-to-resolution-hierarchy]

B40. In tokenized batch mode recipients are grouped by resolved From and one message per group carries per-recipient metadata (tokens, leadId, emailId, hashId, source, utmTags, includeDnc); the transport's `getMaxBatchLimit()` bounds a batch. [code: app/bundles/EmailBundle/Helper/MailHelper.php:453-490 @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php:1912-1926 @7.x]

B41. Return-Path: with a configured bounces mailbox, `<local>+bounce_<idHash>@<domain>` (and the `Sender` header removed); otherwise `mailer_return_path` if set. [code: app/bundles/EmailBundle/Helper/MailHelper.php:327-333 @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php:1781-1800 @7.x]

B42. Email-level `headers` override global `mailer_custom_headers`; tokens are replaced in header values; an empty value removes the header; invalid address headers are dropped. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1848-1910 @7.x]

B43. `List-Unsubscribe: <https://.../email/unsubscribe/{idHash}/{email}/{hash}>` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` are added when the body contains `{unsubscribe_url}` (or `{unsubscribe_text}` with `|URL|`), the email is not `sendToDnc`, and `disable_unsubscribe_link_header` is off; a custom `List-Unsubscribe` header gets Mautic's URL prepended; with an unsubscribe mailbox a `mailto:...+unsubscribe_<idHash>@...` entry is appended. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1317-1396 @7.x] [code: app/bundles/EmailBundle/EventListener/ProcessUnsubscribeSubscriber.php:57-80 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#unsubscribe-settings]

B44. The email's `bccAddress` (comma-separated) is added only when BCC is allowed (Segment/Campaign sends yes; send-to-user and example no). [code: app/bundles/EmailBundle/Helper/MailHelper.php:1242-1250 @7.x]

B45. Asset attachments are attached only if the Asset is published; an `asset_downloads` row with source `email` is recorded per successful recipient. [code: app/bundles/EmailBundle/Helper/MailHelper.php:718-732 @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php:1581-1645 @7.x]

B46. With S/MIME signing on, messages are signed with the certificate matching the From address and tokenized batch mode is disabled; S/MIME works only with SMTP and is configured only in `local.php`. [code: app/bundles/EmailBundle/Helper/MailHelper.php:277-284 @7.x] [code: app/bundles/EmailBundle/Helper/SMimeHelper.php:54-117 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/smime_email_signing.html]

B47. `mailer_convert_embed_images` replaces `<img src>` (except the pixel) by CID attachments. If the encoded `To` exceeds `mailer_address_length_limit` (320), only the bare address is used. [code: app/bundles/EmailBundle/Helper/MailHelper.php:828-863 @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php:930-938 @7.x]

## 7. Tokens and content generation

B48. Content is rendered by dispatching `EMAIL_ON_SEND` once per Contact (standard transports) or into per-recipient metadata (tokenized transports); each pass starts from the same initial body/subject/plain text. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1477-1499 @7.x]

B49. `EMAIL_ON_SEND` listener order: accessibility fixes (10000), `TokenSubscriber::decodeTokens` (254), preheader injection (200), content generation (0), URL-to-trackable conversion (-9999). [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:55-60 @7.x] [code: app/bundles/EmailBundle/EventListener/TokenSubscriber.php:30 @7.x] [code: app/bundles/EmailBundle/EventListener/EmailSubscriber.php:50 @7.x]

B50. With `validate_unsubscribe_emails` on, `{unsubscribe_url}`/`{resubscribe_url}` point to `/email/validate/{action}/{secretHash}/{idHash}`; otherwise to `/email/unsubscribe/{idHash}/{email}/{hash}`. `secretHash = HMAC-SHA256(email, secret_key)`. `{webview_url}` falls back to the public preview URL with no Contact. [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:160-205 @7.x] [code: app/bundles/EmailBundle/Helper/MailHashHelper.php:16-26 @7.x]

B51. `{tracking_pixel}` resolves to `/email/{idHash}.gif?ct=<sent_time>` or, without an idHash, an inline blank GIF; it is appended before `</body>` only when `mailer_append_tracking_pixel` is on and the send is not internal. Do not place it right after `<body>` (breaks the preheader). [code: app/bundles/EmailBundle/Helper/MailHelper.php:806-816 @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php:1414-1432 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#email-open-tracking]

B52. All `http(s)`/`ftp` links in HTML and plain text are converted to trackables and replaced by `/r/<redirect_id>?ct=<clickthrough>` (source, email id, stat hash, sent time, Contact id) with the email's UTM tags appended; URL-encoded tokens are decoded first. With `disable_trackable_urls` the original URL plus UTM is used. Links are not trackable in Send example, direct Contact-profile sends, or form-preview emails. [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:228-317 @7.x] [code: app/bundles/EmailBundle/EventListener/TokenSubscriber.php:42-49 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#email-link-tracking]

B52a. A link with `data-mautic-disable-tracking="true"` is not tracked; the legacy `mautic:disable-tracking` attribute also works in 7.x but is deprecated. [code: app/bundles/PageBundle/Model/TrackableModel.php:740-747 @7.x]

B52b. Contact and owner tokens inside link URLs resolve at click time, so only on tracked links. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tokens-in-link-urls] [code: app/bundles/PageBundle/Model/TrackableModel.php:657 @7.x]

B53. The preheader is injected as a hidden `<div class="preheader">` right after `<body>` (replacing an existing one); `<head>`, `<title>` (subject) and `<html lang>` are added when missing. [code: app/bundles/EmailBundle/EventListener/EmailSubscriber.php:89-104 @7.x] [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:112-148 @7.x]

B54. Dynamic content: for each `{dynamiccontent="name"}` the first filter group whose filters all match the Contact (with primary Company fields) wins, else the default; the chosen content is token-replaced again via a nested `EMAIL_ON_DISPLAY` with `isDynamicContentParsing`. Operators: `=`, `!=`, `gt/gte/lt/lte`, `empty/!empty`, `like/!like`, `regexp/!regexp`, `startsWith/endsWith/contains`, plus type handling for boolean, date/time, tags, select/multiselect, number, region and Segment membership. [code: app/bundles/EmailBundle/EventListener/TokenSubscriber.php:73-121 @7.x] [code: app/bundles/EmailBundle/EventListener/MatchFilterForLeadTrait.php:16-271 @7.x]

B55. Plain text: the email's `plainText` is used if set; the send path does not auto-generate it. The editor's "generate" (`email:generatePlaintText`) uses `PlainTextHelper` (links inline as `text [url]`, width 70). HTML tags are stripped from the text part after token replacement. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1252-1254 @7.x] [code: app/bundles/EmailBundle/Helper/PlainTextHelper.php:166-181 @7.x] [code: app/bundles/EmailBundle/Controller/AjaxController.php:104-119 @7.x]

B56. An email with no `customHtml` but a `template` is rendered from `@themes/<template>/html/email.html.twig` with legacy `content` slots. [code: app/bundles/EmailBundle/Helper/MailHelper.php:1256-1267 @7.x]

### Token reference table

| Token | Value | Source |
|---|---|---|
| `{contactfield=alias}` | Contact (or core Company) field value | [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tokens] |
| `{contactfield=alias\|default}` | Value, else the default after `\|` | [docs: https://docs.mautic.org/en/7.2/channels/emails.html#default-value] |
| `{contactfield=alias\|true}` | URL-encoded value | [docs: https://docs.mautic.org/en/7.2/channels/emails.html#encoded-value] |
| `{contactfield=alias\|datetime}` / `\|date` / `\|time` | Human-readable date using System Settings formats | [docs: https://docs.mautic.org/en/7.2/channels/emails.html#date-formats] |
| `{contactfield=alias\|label}` | Label of a select/boolean value (Contact and Company fields) | [docs: https://docs.mautic.org/en/7.2/configuration/variables.html#label-modifier-for-select-and-boolean-fields] |
| `{contactfield=<custom company alias>}` | Custom Company fields use `contactfield` without a "company" prefix | [docs: https://docs.mautic.org/en/7.2/configuration/variables.html#company-contact-fields] |
| `{ownerfield=firstname\|lastname\|email\|position\|signature}` | Contact owner's User fields; empty when no owner | [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tokens-in-link-urls] [code: app/bundles/LeadBundle/EventListener/OwnerSubscriber.php:20 @7.x] |
| `{unsubscribe_text}` | Configured `unsubscribe_text` sentence with `\|URL\|` replaced; hidden if `{unsubscribe_url}` is also used | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:171-174 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#unsubscribe-settings] |
| `{unsubscribe_url}` | Unsubscribe (or validation) URL; leads to the Preference Centre when enabled | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:160-205 @7.x] |
| `{dnc_url}` | Unsubscribe-all URL `/email/dnc/...` | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:150-226 @7.x] |
| `{resubscribe_url}` | Resubscribe (or validation) URL | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:160-205 @7.x] |
| `{webview_text}` | Configured `webview_text` with `\|URL\|` (default "Having trouble reading this Email? Click here") | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:192-197 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#message-settings] |
| `{webview_url}` | `/email/view/{idHash}`, or the public preview URL without a Contact | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:160-205 @7.x] |
| `{signature}` | Owner signature (email has Use owner as mailer and Contact has an owner), else `default_signature_text` with `\|FROM_NAME\|` | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:207-220 @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php:364 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#signatures] |
| `{subject}` | The email subject | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:64-110 @7.x] |
| `{brand=name}` | Brand name | [code: app/bundles/EmailBundle/Helper/MailHelper.php:368 @7.x] |
| `{tracking_pixel}` | Open-tracking pixel URL (blank GIF when internal) | [code: app/bundles/EmailBundle/Helper/MailHelper.php:1414-1432 @7.x] |
| `{today}` | Current date, Contact-timezone aware | [code: app/bundles/EmailBundle/EventListener/DateTimeTokenSubscriber.php:29-53 @7.x] |
| `{listUnsubscribeHeader}` | Internal value used for the List-Unsubscribe header | [code: app/bundles/EmailBundle/Helper/MailHelper.php:1335 @7.x] |
| `{dynamiccontent="name"}` | Dynamic content slot (B54) | [code: app/bundles/EmailBundle/EventListener/TokenSubscriber.php:73-121 @7.x] |
| `{assetlink=ID}`, `{pagelink=ID}`, `{formlink=ID}`, `{focus=ID}` | Provided by Asset/Page/Form/Focus bundles on the same events | [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:64-110 @7.x] |
| API `tokens` (`{name}` => value) | Custom tokens for `POST /api/emails/{id}/contact/{cid}/send`; braces added automatically, HTML-sanitised | [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:145-206 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/emails.html#tokens] |

Builder token groups are ordered Contact, Company, Owner, Page link, Dynamic Content, Focus Item, Asset, This page, Email, Other. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#token-sorting]

## 8. Open, click and webview tracking

B57. The pixel dispatches `EmailHitNotification(idHash, request)` on Messenger and returns the GIF immediately; if dispatch throws, the hit is processed inline. With `messenger_dsn_hit = sync://` the handler runs in the request and tracks the opener's device; with a queue it uses the system Contact and the dispatch time. DB `RetryableException`s become `RecoverableMessageHandlingException` for retry. [code: app/bundles/EmailBundle/Controller/PublicController.php:131-146 @7.x] [code: app/bundles/MessengerBundle/MessageHandler/EmailHitNotificationHandler.php:20-41 @7.x]

B58. A hit is ignored when the IP is untrackable or the bot heuristic fires: at least `bot_helper_bot_ratio_threshold` (0.6) of three signals - opened within `bot_helper_time_email_threshold` (2 s) of sending, IP in `bot_helper_blocked_ip_addresses`, user agent in the block list or detected as a bot. [code: app/bundles/EmailBundle/Model/EmailModel.php:442-452 @7.x] [code: app/bundles/EmailBundle/Helper/BotRatioHelper.php:35-85 @7.x]

B59. On a valid hit: `last_opened` updated, `open_count` incremented, `{datetime, useragent, inBrowser}` appended to `open_details` (max 1000); on the first open `is_read = 1`, `date_read` set and `read_count`/`variant_read_count` incremented once; `viewed_in_browser` set for webview; an `email_stats_devices` row written in a separate transaction; `last_active` moved forward only if newer; `EMAIL_ON_OPEN` dispatched with `firstTime`. Re-processing is not idempotent. [code: app/bundles/EmailBundle/Model/EmailModel.php:454-548 @7.x] [code: app/bundles/EmailBundle/Entity/EmailRepository.php:848-887 @7.x]

B60. `/email/view/{idHash}` records an open (anonymous visitors only, always synchronously), then renders the stored Copy with the stat's tokens, a blank pixel and analytics code; 404 when the stat does not exist. [code: app/bundles/EmailBundle/Controller/PublicController.php:85-129 @7.x]

B61. A click carrying `ct.email` + `ct.stat` is bot-filtered, stored as a page hit with `email_id`/`redirect_id`/`source`, then fires the real-time `email.click` decision and marks the stat read if needed. The visitor is identified as the stat's Contact only if `ct.channel.email` matches the stat's email. [code: app/bundles/PageBundle/Model/PageModel.php:427-432 @7.x] [code: app/bundles/EmailBundle/EventListener/PageSubscriber.php:31-65 @7.x] [code: app/bundles/EmailBundle/EventListener/TrackingSubscriber.php:25-52 @7.x]

B62. Email-client plugin tracking (`/plugin/{integration}/tracking.gif`, Outlook/Gmail) verifies the integration signature, creates the Contact if unknown, creates a stat with source `email.client` and records the open. [code: app/bundles/EmailBundle/Controller/PublicController.php:710-803 @7.x]

B62a. Open tracking depends on the client loading images; clients that block or prefetch images make opens inaccurate. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#email-open-tracking]

## 9. Replies

B63. An IMAP message is a reply when its HTML contains `email/<hash>.gif`; the From address must be one of the Contact's address variations; one `email_stat_replies` row per (stat, message id); `EMAIL_ON_REPLY` fires the real-time `email.reply` decision. `POST /api/emails/reply/{trackingHash}` creates a reply (message id `api-<random>`, returns 201) without the From check. Reply monitoring needs PHP IMAP and a non-Google/Yahoo inbox; the last processed UID is cached. [code: app/bundles/EmailBundle/MonitoredEmail/Processor/Reply.php:34-130 @7.x] [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:211-222 @7.x] [code: app/bundles/EmailBundle/EventListener/ProcessReplySubscriber.php:41-66 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#contact-replies]

## 10. Unsubscribe, resubscribe, Preference Centre, DNC

B64. A POST `List-Unsubscribe=One-Click` to `/email/unsubscribe/{idHash}/{urlEmail}/{secretHash}` needs an existing stat and a matching hash, then writes DNC `UNSUBSCRIBED` "User unsubscribed." with channel `['email' => emailId]`; otherwise 404/400/403. Legacy links without `urlEmail`/`secretHash` return 400. [code: app/bundles/EmailBundle/Controller/PublicController.php:970-995 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:1763-1775 @7.x]

B65. A GET without `urlEmail`/`secretHash` but with a known stat redirects to the validation form; the typed address must match the HMAC and (when a stat exists) the stat address, case-insensitively, then the visitor is redirected to the real URL. [code: app/bundles/EmailBundle/Controller/PublicController.php:148-234 @7.x] [code: app/bundles/EmailBundle/Helper/EmailAddressLinkMatcher.php:13-29 @7.x]

B66. With a valid hash: if preferences are disabled, or the route is `/email/dnc/...` (unsubscribe all), or no Contact is found, an email DNC `UNSUBSCRIBED` is written for the stat's Contact (or the last Contact with that address) and the unsubscribe message with a resubscribe link is shown. HEAD requests change nothing. [code: app/bundles/EmailBundle/Controller/PublicController.php:267-304 @7.x] [code: app/bundles/EmailBundle/Controller/PublicController.php:856-901 @7.x]

B67. With preferences enabled (`show_contact_preferences`) and a Contact, the preference form is shown inside the email's Preference Centre page (must contain the `saveprefsbutton` slot), else the default `email_default_preference_center_id` page (resolved at unsubscribe time), else `Lead/preference_options.html.twig`. Saving: unticked channels get DNC `UNSUBSCRIBED`; re-ticked channels with `UNSUBSCRIBED`/`MANUAL` DNC have it removed; Segment and Category checkboxes add/remove membership; frequency, pause dates and preferred channel go to `lead_frequencyrules`. [code: app/bundles/EmailBundle/Controller/PublicController.php:305-421 @7.x] [code: app/bundles/LeadBundle/Controller/FrequencyRuleTrait.php:159-185 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#unsubscribe-settings]

B67a. Only active, public Segments appear in the Preference Centre; a "pause" is not an unsubscribe and sending resumes after the range. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#unsubscribe-settings]

B68. An email with a published unsubscribe Form embeds it on the unsubscribe page (or appends its HTML if the theme lacks a `form` slot). [code: app/bundles/EmailBundle/Controller/PublicController.php:242-254 @7.x]

B69. Resubscribe requires `urlEmail` + matching `secretHash` (legacy idHash-only links go to the validation form) and removes all email DNC rows, any reason, for every Contact with that address. [code: app/bundles/EmailBundle/Controller/PublicController.php:439-498 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:1787-1801 @7.x]

B70. DNC write rules: a new row is created if the Contact is contactable on the channel; an existing row changes reason only if the reason differs and the existing one is not `UNSUBSCRIBED`. `EmailModel::setEmailDoNotContact`/`removeDoNotContact` act on every Contact sharing the address. [code: app/bundles/LeadBundle/Model/DoNotContact.php:76-136 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:1807 @7.x]

## 11. Bounces, monitored inbox and transport callbacks

B71. Bounce processing tries a transport `BounceProcessorInterface`, then the DSN report, then body rules; the Contact is found by the `+bounce_<hash>` address or by address. Result: `open_details.bounces[]` entry, `retry_count + 1`, `is_failed = 1` when final or `retry_count >= 5`, and DNC `BOUNCED` with a category comment. Hard: `unknown`, `inactive`, `user_reject`, `dns_*`, `command_reject`; soft: `full`, `defer`, `oversize`, `outofoffice`. [code: app/bundles/EmailBundle/MonitoredEmail/Processor/Bounce.php:46-123 @7.x] [code: app/bundles/EmailBundle/MonitoredEmail/Processor/Bounce/Mapper/CategoryMapper.php:13-32 @7.x] [code: app/bundles/EmailBundle/MonitoredEmail/Search/ContactFinder.php:25-70 @7.x]

B72. Unsubscribe mailbox: messages to `...+unsubscribe...` give DNC `UNSUBSCRIBED` "Contact unsubscribed via email"; ARF `feedback-type: abuse` gives DNC `UNSUBSCRIBED` "Marked as spam". [code: app/bundles/EmailBundle/MonitoredEmail/Processor/Unsubscribe.php:29-76 @7.x] [code: app/bundles/EmailBundle/MonitoredEmail/Processor/FeedbackLoop.php:26-63 @7.x]

B73. `mautic:email:fetch` (`--message-limit`) reads each configured folder; it takes no lock and always exits 0. [code: app/bundles/EmailBundle/Command/ProcessFetchEmailCommand.php:16-59 @7.x]

B74. Each folder uses the `general` connection unless `override_settings`; a folder is configured only with host, port, user and password; saving config keeps stored passwords when the field is empty. [code: app/bundles/EmailBundle/MonitoredEmail/Mailbox.php:199-320 @7.x] [code: app/bundles/EmailBundle/EventListener/ConfigSubscriber.php:38-66 @7.x]

B75. `POST /mailer/callback` dispatches `ON_TRANSPORT_WEBHOOK`; a transport plugin's listener calls `TransportCallback::addFailureByHashId|Address|ContactId` (sets `is_failed` for BOUNCED, appends `open_details.bounces[]`, adds DNC). With no listener responding the route returns 404 "No email transport that could process this callback was found". [code: app/bundles/EmailBundle/Controller/PublicController.php:537-543 @7.x] [code: app/bundles/EmailBundle/Model/TransportCallback.php:24-84 @7.x]

B75a. Services that overwrite Return-Path (Gmail, Amazon SES) break IMAP bounce monitoring; webhook bounces are supported by provider plugins. [docs: https://docs.mautic.org/en/7.2/channels/emails.html#bounce-management]

B76. Legacy spool hooks `EMAIL_FAILED` (DNC BOUNCED after failures) and `EMAIL_RESEND` (retry up to 3, then DNC) have listeners but are never dispatched in 7.x. [code: app/bundles/EmailBundle/EventListener/EmailSubscriber.php:126-174 @7.x]

## 12. Campaigns, Points, Forms, Webhooks, message queue

B77. Campaign action `email.send`: an unpublished/missing email passes everyone with "Email not found or published"; Contacts without an address pass with a note; unless `sendToDnc`, Contacts opted out of the email's Category pass with a note. Options: source `['campaign.event', eventId]`, `email_attempts` 3, `email_priority` 2, `dnc_as_error`, header `X-EMAIL-ID`, `ignoreDNC = sendToDnc`. [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:250-333 @7.x]

B78. `email_type` marketing (default) passes with "has already received this marketing email" for a Contact who has a non-failed stat for the email or any variant child; transactional always sends. DNC-filtered Contacts pass (not fail) so they are not retried; other errors fail the log. [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:335-382 @7.x]

B79. Decisions `email.open`, `email.click` (optional URL list, substring/regex/wildcard) and `email.reply` apply only when the parent event is `email.send` and the email (or a related variant/translation) is the parent's email; they run in real time from `EMAIL_ON_OPEN`, `PAGE_ON_HIT` and `EMAIL_ON_REPLY`. [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:64-242 @7.x] [code: app/bundles/EmailBundle/Helper/UrlMatcher.php:10-33 @7.x]

B80. "Send email to user" (campaign `email.send.to.user`, point trigger `email.send_to_user`, form action `email.send.user`): recipients are selected Users, optionally the owner, and literal or `{contactfield=...}` to/cc/bcc; the email must be published; sent as internal (no tracking, no stat, no webhooks); cc/bcc only on the first message. [code: app/bundles/EmailBundle/Model/SendEmailToUser.php:36-107 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:1584-1717 @7.x]

B81. Form action `email.send.lead` sends to the submitter with `ignoreDNC = true` and source `['form', formId]`. [code: app/bundles/EmailBundle/EventListener/FormSubscriber.php:82-88 @7.x]

B82. Points actions `email.open`/`email.send` score on open/send; trigger `email.send` sends an email. [code: app/bundles/EmailBundle/EventListener/PointSubscriber.php:40-112 @7.x]

B83. Webhook `mautic.email_on_send` (non-internal sends with a Contact) and `mautic.email_on_open`; with `webhook_email_details` off, `customHtml`/`plainText` are stripped. [code: app/bundles/EmailBundle/EventListener/WebhookSubscriber.php:52-120 @7.x]

B84. `mautic:messages:send` re-sends queued emails through `sendEmail` as marketing; frequency hits are rescheduled, successes marked, failures retried; unpublished email or missing Contact fail. Broadcast queue items always have Normal priority. [code: app/bundles/EmailBundle/EventListener/MessageQueueSubscriber.php:29-87 @7.x] [docs: https://docs.mautic.org/en/7.2/queue/message_queue.html]

## 13. A/B testing

B85. Settings live in the parent's `variant_settings`: `enableAbTest`, `winnerCriteria` (default `email.openrate`), `sendWinnerDelay` hours (default 24), `totalWeight` (default 10, % of pending used for the test); children have a `weight`; weights must total at most 100. [code: app/bundles/CoreBundle/Helper/AbTestSettingsService.php:16-73 @7.x] [code: app/bundles/EmailBundle/Form/Type/VariantType.php:25-88 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#converting-an-email-to-an-a-b-test]

B86. During an undecided test the sample is `ceil(pending / variants * totalWeight / 100) * variants`; only thread 1 sends, without batch/threads, limited to the remaining sample; the first test send sets `variant_start_date`; when the sample is sent nothing more goes out until a winner exists. [code: app/bundles/EmailBundle/EventListener/BroadcastSubscriber.php:57-85 @7.x] [code: app/bundles/EmailBundle/EventListener/BroadcastSubscriber.php:120-142 @7.x] [code: app/bundles/CoreBundle/Entity/VariantEntityTrait.php:296-315 @7.x]

B87. Open rate = reads/sends per variant since `variant_start_date` (until start + delay); click-through = tracked hits/sent; the highest rate wins, ties take the first. [code: app/bundles/EmailBundle/EventListener/DetermineWinnerSubscriber.php:33-214 @7.x]

B88. `mautic:email:sendwinner [--id]` is ready when the parent and variants are published, `totalWeight < 100`, `sendWinnerDelay > 0`, and now is past the last `date_sent` + delay; the winner becomes the parent (inheriting dates and Continue sending) and a broadcast with `abTestWinner = true` sends to the rest; not ready returns exit 1. [code: app/bundles/EmailBundle/Model/AbTest/SendWinnerService.php:40-174 @7.x] [code: app/bundles/EmailBundle/Command/SendWinnerEmailCommand.php:21-77 @7.x]

B89. Manual winner (`winner` action, POST, edit access, not locked) converts the variant and dispatches `ManualWinnerEvent`. [code: app/bundles/EmailBundle/Controller/EmailController.php:1365-1435 @7.x]

B90. A/B status: `prepare`, `pending` (publishUp future), `running`, `done`. The UI converts only Segment Emails with zero sends; the header Send button is hidden for A/B tests. [code: app/bundles/EmailBundle/Model/AbTest/EmailStatus.php:20-42 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#scheduling-the-a-b-test]

## 14. UI, API, examples, previews, search, reports

B91. UI "Send" for a Segment Email requires published + type `list`; variant/translation children redirect to the parent; the AJAX loop sends batches of `mailer_memory_msg_limit` (100). [code: app/bundles/EmailBundle/Controller/EmailController.php:1440-1575 @7.x] [code: app/bundles/EmailBundle/Controller/AjaxController.php:55-97 @7.x]

B92. "Send example": subject prefixed `[TEST]`, recipients default to the current User, rendered with a chosen Contact (needs Contact view permission) or a fake Contact, internal send, no stat, pixel blanked. [code: app/bundles/EmailBundle/Controller/EmailController.php:69 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:2216-2309 @7.x]

B93. `/email/preview/{id}` is public only for a published email with `publicPreview` on; logged-in Users need view access; `?contactId=`/`?companyId=` personalise when permitted; drafts use `/draft`. [code: app/bundles/EmailBundle/Controller/PublicController.php:545-705 @7.x] [docs: https://docs.mautic.org/en/7.2/channels/emails.html#previewing-a-draft-email]

B94. `POST /api/emails/{id}/send` (body `lists`, `limit`, `batch`) needs a published email and view access, runs `sendEmailToLists` synchronously and returns `success`, `sentCount`, `failedRecipients`. `POST /api/emails/{id}/contact/{leadId}/send` needs edit access to the Contact, accepts `tokens` and `assetAttachments`, uses source `['api', 0]` and honours DNC unless `sendToDnc`. [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:107-206 @7.x]

B95. API writes ignore `isPublished`/`publishUp`/`publishDown` without publish permission, drop `sendToDnc` without `email:emails:sendtodnc`, and reset `sendToDnc` to false on a PUT that omits it. `GET /api/emails` returns only top-level emails (no variant children). [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:89-98 @7.x] [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:224-256 @7.x]

B96. The configuration "Send test email" sends a plain message from the system From to the current User and reports transport errors. [code: app/bundles/EmailBundle/Controller/AjaxController.php:168-188 @7.x]

B97. Search commands: `is:published`, `is:unpublished`, `is:uncategorized`, `is:mine`, `name:`, `subject:`, `is:expired`, `is:pending`, `category:`, `lang:`, `project:`. [code: app/bundles/EmailBundle/Entity/EmailRepository.php:636-745 @7.x]

B98. Contact timeline shows `email.sent`, `email.read`, `email.failed`, `email.replied`. [code: app/bundles/EmailBundle/EventListener/LeadSubscriber.php:35-158 @7.x]

B99. Reports expose `emails` and `email.stats` contexts. [code: app/bundles/EmailBundle/EventListener/ReportSubscriber.php:29-192 @7.x]

B100. Channel registration: `email` with campaign action `email.send` and decisions `email.open`, `page.pagehit`, `asset.download`, `form.submit`. [code: app/bundles/EmailBundle/EventListener/ChannelSubscriber.php:31-52 @7.x]

B101. Publish dates compare against local now; open details store UTC strings; A/B delay maths is UTC. [code: app/bundles/CoreBundle/Entity/FormEntity.php:412-435 @7.x] [code: app/bundles/EmailBundle/Model/EmailModel.php:2461-2496 @7.x]

## 15. Transports and Messenger queueing

B102. `mailer_dsn` (default `smtp://localhost:1025`) is the single Symfony Mailer transport `main`, read through the `urlencoded-dsn` env processor; an unparsable DSN becomes `invalid://null`, and an unknown scheme becomes `InvalidTransport`, which throws on send. [code: app/config/config.php:97-101 @7.x] [code: app/bundles/EmailBundle/DependencyInjection/EnvProcessor/MailerDsnEnvVarProcessor.php:12-31 @7.x] [code: app/bundles/EmailBundle/Mailer/Transport/TransportFactory.php:34-41 @7.x]

B103. DSN values must be URL-encoded; the form does this, but values pasted into `local.php` must be encoded by hand. Extra Symfony transports (e.g. `symfony/sendgrid-mailer`, `sendgrid+api://KEY@default`) need a Composer-based install. [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#smtp-transport] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#example-api-transport-installation]

B104. Every local parameter is also an env var `MAUTIC_<UPPERCASE_NAME>`; a real environment variable wins over `local.php`. [code: app/bundles/CoreBundle/Loader/EnvVars/ConfigEnvVars.php:26 @7.x] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:88-110 @7.x]

B105. `SendEmailMessage` is routed to Messenger transport `email` (`messenger_dsn_email`, default `sync://`); `EmailHitNotification` to `hit` (`messenger_dsn_hit`, default `sync://`); `failure_transport` is always `failed`. [code: app/config/config.php:102-125 @7.x] [code: app/bundles/MessengerBundle/Config/config.php:7-13 @7.x]

B106. `sync://` sends inside the request/command; any other DSN (`doctrine://default`, `redis://...`) stores the message for `messenger:consume email`. `sync://` is the only DSN accepted without a host. [code: app/bundles/CoreBundle/Helper/Dsn/Dsn.php:9-58 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#queued-delivery]

B107. Retry: `max_retries` 3, delay 1000 ms, multiplier 2.0, no max delay (about 1 s, 2 s, 4 s), then `failed`; an empty failed DSN is `null://` and the message is discarded. [code: app/bundles/MessengerBundle/Retry/RetryStrategy.php:31-43 @7.x] [code: app/bundles/MessengerBundle/DependencyInjection/EnvProcessor/MessengerNullableEnvVarProcessor.php:11-14 @7.x] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#retry-strategy]

B108. With a queue DSN the stat and `sent_count` are written when the message is queued; a later worker failure does not mark the stat failed. [code: app/bundles/EmailBundle/Helper/MailHelper.php:402-414 @7.x]

B109. `amqp://` is rejected as "Unsupported scheme" until `symfony/amqp-messenger` is installed. [code: app/bundles/MessengerBundle/Validator/DsnValidator.php:31-45 @7.x] [code: UPGRADE-7.0.md:53 @7.x]

B110. The Queue Settings "Send test message" button dispatches a `TestEmail` that has no handler, so it cannot succeed with `sync://`. [code: app/bundles/MessengerBundle/Service/TestMessageFactory.php:19-27 @7.x] [code: UPGRADE-7.0.md:15 @7.x]

B111. A running `messenger:consume` keeps the DSN and retry settings it booted with until restarted (inferred from boot-time env resolution). [code: app/bundles/ConfigBundle/Controller/ConfigController.php:149-154 @7.x]

B112. `RemoveReportAttachmentHandler` runs after every `SendEmailMessage` and deletes report export files whose name matches an attachment. [code: app/bundles/MessengerBundle/MessageHandler/RemoveReportAttachmentHandler.php:13-48 @7.x]

## 16. Doc/code discrepancies and open questions

| Topic | Docs say | Code (7.2.1) says |
|---|---|---|
| `sendToDnc` and bounces | Bounced still respected [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/emails.html#email-properties] | DNC check skipped entirely, any reason [code: app/bundles/EmailBundle/Model/EmailModel.php:1399-1409 @7.x] |
| Transactional emails and opt-outs | Sent even to opted-out Contacts since 5.0, no unsubscribe header [kb: https://kb.mautic.org/article/understand-the-difference-transactional-and-marketing-emails-in-mautic.html] | Campaign "transactional" only allows re-send; DNC bypass needs `sendToDnc`; header suppression depends on `sendToDnc` [code: app/bundles/EmailBundle/EventListener/CampaignSubscriber.php:315-382 @7.x] [code: app/bundles/EmailBundle/Helper/MailHelper.php:1329 @7.x] |
| Segment-send API field | `listIds` [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/emails.html] | `lists`, `limit`, `batch` [code: app/bundles/EmailBundle/Controller/Api/EmailApiController.php:119-123 @7.x] |
| Contacts added to a Segment later | Sent unless an unpublish date is set [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html#send-scheduled-broadcasts-segment-emails-cron-job] | Sent only with Continue sending on; `publishDown` ignored otherwise [code: app/bundles/EmailBundle/Entity/EmailRepository.php:285-288 @7.x] |
| Legacy no-track attribute | `mautic:disable:tracking` [docs: https://docs.mautic.org/en/7.2/channels/emails.html#tracking-links-in-emails] | `mautic:disable-tracking` [code: app/bundles/PageBundle/Model/TrackableModel.php:741 @7.x] |
| Transport callback URL | `/mailer/{transport}/callback` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#testing-transport-callback] | `/mailer/callback` [code: app/bundles/EmailBundle/Config/config.php:99-100 @7.x] |
| Transport registration | Swiftmailer-era `mautic.email_transport` tag, `CallbackTransportInterface` [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/emails.html#email-transports] | Symfony `TransportFactoryInterface` + `ON_TRANSPORT_WEBHOOK` [code: app/bundles/EmailBundle/Mailer/Transport/TransportFactory.php:34-41 @7.x] |
| Unsubscribe validation | Documented only in the 8.0 docs branch [docs: https://docs.mautic.org/en/8.0/configuration/settings.html#unsubscribe-settings] | Present and on by default on the 7.x branch after 7.2.1, not yet released (`validate_unsubscribe_emails`; [PR #16870]) [code: app/bundles/EmailBundle/EventListener/BuilderSubscriber.php:176-182 @7.x] |
| Legacy queue page | `mautic:queue:process`, cron `mautic:email:send` [docs: https://docs.mautic.org/en/7.2/queue/queue.html] | Neither command exists; Messenger is used [code: app/bundles/EmailBundle/Command/ProcessFetchEmailCommand.php:16-59 @7.x] |
| Frequency-rule delay | Postponed 24 h [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html] | Rescheduling interval not verified [unverified] |

Open questions [unverified]: whether any Messenger failure listener marks stats failed (none found); which official
transport plugins exist for 7.x; whether `mautic:maintenance:cleanup` purges email stats.
