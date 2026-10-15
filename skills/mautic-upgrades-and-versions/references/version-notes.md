# Version notes: release timeline and per-major breaking changes (1.x → 8.x)

Open this file to answer "what changed in version N", "what PHP/DB does version N need", or "why does the code look like this".
Dates are commit dates of the tagged commits [code: git tag @7.x]. Platform values come from `app/release_metadata.json`
at the named tag unless stated. The 7.x → 8.x guide is separate: [upgrade-to-8.md](upgrade-to-8.md).

## Contents
1. Release timeline and platform requirements
2. Upgrade paths between majors
3. Per-major summaries: 3.0, 4.0, 4.3, 5.0, 6.0, 7.0, PHP → Twig
4. 7.x minors (7.0 → 7.1 → 7.2 → 7.2.1)
5. 8.x (in development)

## 1. Release timeline and platform requirements

| Series | First stable tag | Last tag in the 7.x clone | PHP | MySQL / MariaDB | Can update from (`minimum_mautic_version`) | Source |
|---|---|---|---|---|---|---|
| 1.x | 1.0.0 (2015-03-10) | 1.4.1 (2016-05-31) | not covered by inputs | not covered | — | [code: git tag] |
| 2.x | 2.0.0 (2016-07-05) | 2.16.5 (2021-01-14) | not covered | MySQL 5.5.3 (implied by UPGRADE-3.0 "from v5.5.3") | — | [code: git tag] [code: UPGRADE-3.0.md:17] |
| 3.x | 3.0.0 (2020-06-15) | 3.3.5 (2022-02-28) | 7.2.21 – 7.3.99 at 3.0.0 | MySQL ≥ 5.7.14 | 3.0.0-alpha | [code: app/release_metadata.json @3.0.0] [code: UPGRADE-3.0.md:17] |
| 4.x | 4.0.0 (2021-08-30) | 4.4.13 (2024-09-18) | 7.4.0 – 8.0.99 | MySQL ≥ 5.7.14 / MariaDB ≥ 10.2.7 (at 4.4.0) | 3.2.0 | [code: app/release_metadata.json @4.0.0, @4.4.0] |
| 5.x | 5.0.0 (2024-01-09) | 5.2.11 (2026-05-28) | 8.0.2 – 8.1.99 at 5.0.0; 8.1.0 – 8.3.99 at 5.2.0 | MySQL ≥ 5.7.14 / MariaDB ≥ 10.2.7 | 4.4.10 | [code: app/release_metadata.json @5.0.0, @5.2.0] |
| 6.x | 6.0.0 (2025-03-25) | 6.0.9 (2026-05-28) | 8.1.0 – 8.3.99 | MySQL ≥ 5.7.14 / MariaDB ≥ 10.2.7 | 5.0.0 | [code: app/release_metadata.json @6.0.0] |
| 7.x | 7.0.0 (2026-01-20) | 7.2.1 (2026-09-23) | 8.2.0 – 8.4.99 at 7.0.0; 8.2.0 – 8.5.99 from 7.1.0 | MySQL ≥ 8.4.0 / MariaDB ≥ 10.11.0 | 5.0.0 | [code: app/release_metadata.json @7.0.0, @7.1.0, @7.x] |
| 8.x | unreleased | branch `8.x` @ `11599729491` | 8.4 – 8.5.99 | MySQL ≥ 8.4.0 / MariaDB ≥ 10.11.0 | metadata not bumped | [code: app/release_metadata.json @8.x] |

7.x minor dates: 7.0.0-alpha 2025-08-04, -beta 2025-10-20, -rc 2025-11-11, -rc2 2025-12-10, 7.0.0 2026-01-20, 7.1.0-rc 2026-03-06,
7.1.0 2026-04-14 … 7.1.3 2026-07-07, 7.2.0-rc 2026-06-02, 7.2.0 2026-09-02, 7.2.1 2026-09-23. 5.1.0 2024-06-12; 5.2.0 2024-12-02
[code: git tag @7.x].

Note: majors overlap. 5.2.x and 6.0.x patch releases continued in 2026 while 7.x was current [code: git tag @7.x].
Only the 7.2.x series is "supported" in the bug template [code: .github/ISSUE_TEMPLATE/BUG-REPORT.yml:24-41 @7.x].

## 2. Upgrade paths between majors

- 2.x → 3.0: upgrade to the latest 2.x first, because all 2.x migrations were removed from 3.x [code: UPGRADE-3.0.md:19 @7.x].
- 3.x → 4.x: the 4.0.0 updater accepts sources ≥ 3.2.0 [code: app/release_metadata.json @4.0.0].
- 4.x → 5.x: the 5.x updater accepts sources ≥ 4.4.10 [code: app/release_metadata.json @5.0.0]. The email transport must be re-configured as a DSN; a migration converts most Mautic 4 transport settings [code: UPGRADE-5.0.md @7.x]. The KB Softaculous guide (4.4 → 5.1) keeps `local.php`, replaces files, runs `mautic:update:apply --finish`, clears cache and redoes SMTP [kb: https://kb.mautic.org/article/update-from-mautic-4-to-5-1-when-installed-by-softaculous-quick-guide.html].
- 5.x/6.x → 7.x: any version ≥ 5.0.0 can take a 7.x release through the updater, provided PHP ≥ 8.2 and MySQL ≥ 8.4.0 / MariaDB ≥ 10.11.0 are already in place (pre-update checks enforce both) [code: app/release_metadata.json @7.x] [code: app/bundles/CoreBundle/Helper/UpdateHelper.php:166-196 @7.x]. Upgrade the database server before updating Mautic: 6.x allowed MySQL 5.7.14.
- Switching a ZIP install to Composer requires Mautic ≥ 4.0.0 and touches only the codebase [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html].
- Stay current within a series (for example, do not lag more than one minor behind) [kb: https://kb.mautic.org/article/troubleshooting-the-site-is-currently-offline-due-to-encountering-an-error-in-mautic.html].

## 3. Per-major summaries

### 3.0 (`UPGRADE-3.0.md`)
- PHP 7.2/7.3/7.4 per the upgrade note (release metadata at 3.0.0 caps at 7.3.99); MySQL minimum raised from 5.5.3 to 5.7.14 [code: UPGRADE-3.0.md:3-17 @7.x] [code: app/release_metadata.json @3.0.0].
- Console moved: `app/console` → `bin/console`; update cron jobs [code: UPGRADE-3.0.md @7.x].
- `app/version.txt` → `app/release_metadata.json`; `AppKernel::*_VERSION` constants removed (use `ThisRelease::getMetadata()`); the updater switched to GitHub releases (`system_update_url`) [code: app/bundles/*/*Events.php @7.x vs @8.x].
- `{leadfield=…}` tokens removed; use `{contactfield=…}` [code: UPGRADE-3.0.md:3 @7.x].
- IntegrationsBundle moved into core; configuration no longer depends on the container (parameters used in compiler passes must be set in `local.php`) [code: UPGRADE-3.0.md @7.x].
- `CommonSubscriber` removed (use DI; subscriber members private); jQuery 2 → jQuery 3.3.1; Rackspace/OpenStack remote-asset plugins removed [code: UPGRADE-3.0.md @7.x].

### 4.0 (`UPGRADE-4.0.md`)
- PHP minimum 7.3 → 7.4 [code: UPGRADE-4.0.md:3-4 @7.x].
- OAuth1 removed (OAuth2 incl. Client Credentials grant) [code: UPGRADE-4.0.md @7.x].
- Symfony 4: services private by default; `YesNoButtonGroupType` uses true/false [code: UPGRADE-4.0.md @7.x].
- Guzzle 7 `mautic.http.client` (PSR-18); `mautic.http.connector` removed; `makeRequest` raw responses are PSR-7; Webhook queue methods removed; company unique fields [code: app/bundles/*/*Events.php @7.x vs @8.x].
- PHP templating deprecated in Symfony 4.3; Mautic 4.3 introduced `content.html.twig` so new bundles and plugins use Twig [code: UPGRADE-4.0.md @7.x].
- The browser updater was deprecated in 4.2 [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-in-the-browser].
- `ON_PLUGIN_INSTALL` / `ON_PLUGIN_UPDATE` events available since 4.2.0 [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html].

### 4.3 (`UPGRADE-4.3.md`)
- Deprecated `CoreEvents::ON_FORM_TYPE_BUILD`, `CustomFormEvent`, `mautic.form.extension.custom` [code: UPGRADE-4.3.md @7.x].

### 5.0 (`UPGRADE-5.0.md`)
- PHP 7.4 → 8.0/8.1; Symfony 5; `%kernel.root_dir%` → `%kernel.project_dir%/app` [code: UPGRADE-5.0.md:20-22 @7.x].
- Local config moved from `app/config/local.php` to `config/local.php` (migration `Versionzz20230929183000`) [code: app/migrations/Versionzz20230929183000.php @7.x].
- Swift Mailer → Symfony Mailer: transports became plugins, a single `mailer_dsn`, SMTP only after a fresh install, installer email step removed [code: UPGRADE-5.0.md @7.x].
- Queue → Symfony Messenger (`mautic:emails:send`, `mautic:queue:process` removed); `mautic:segments:update` no longer updates campaign membership [code: app/bundles/*/*Events.php @7.x vs @8.x].
- Autowiring/autoconfigure in `Config/services.php` (legacy `config.php` services marked for removal); JS dependencies via npm (CKEditor 5); `addFlash()` → `addFlashMessage()` [code: app/bundles/*/*Events.php @7.x vs @8.x].
- Removed: Pipedrive, Citrix, LinkedIn plugins and the calendar; Froala assets disabled by default; new URL shortener configuration [code: UPGRADE-5.0.md @7.x].
- Composer became the default install/update method [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html]. A complex admin password is required from 5.1 [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line].
- Plugin porting guide M4 → M5: controllers as `Class::method`, PHP views to Twig (`@MauticCore/...html.twig`), `bin/console lint:twig`, `static::getContainer()` in tests [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html].
- PR-derived (migrations and releases): all 4.x migrations were deleted from `app/migrations` [PR #12441]; one added during 5.0 alpha was deleted by mistake and restored in 5.0.1 [PR #13183]. Migrations rewrite `local.php`: `%kernel.root_dir%` → `%kernel.project_dir%` [PR #12526], legacy mailer settings → `mailer_dsn`, with `%` doubled from 5.0.3 [PR #13256]. 5.0.2/5.0.3 fixed the point-groups migration for existing tables and `INT` `leads.id` [PR #13195] [PR #13284].
- 5.0 cadence: alpha, beta1, beta2, rc1, rc2, GA on 2024-01-09 [PR #12517] [PR #12793] [PR #12806] [PR #12897] [PR #13089] [PR #13177]. Release-prep PRs touch only `release_metadata.json` from 5.0 [PR #13177]. Security reports moved to GitHub private vulnerability reporting [PR #12876].
- 5.1/5.2: entity metadata and a migration are both required for every index [PR #13413]; `emails.read_count` recalculated in 5.1.1 [PR #13915]; `Migration.template` rewritten around `skipAssertion()`, `getPrefixedTableName()` and an optional `down()` in 5.2 [PR #13823]; Türkiye rename migration [PR #13997] [PR #14170].

### 6.0 (`UPGRADE-6.0.md`)
- Symfony 6; legacy builder, Froala and Gated Video removed; Froala, CodeMirror (outside GrapesJS), jQuery UI Safe Blur and Modernizr JS removed [code: UPGRADE-6.0.md @7.x].
- `MauticFactory` getters removed (use DI); `PluginBundleBase` hooks replaced by `PluginEvents` and `PluginDatabase::installPluginSchema/dropPluginSchema` (`updatePluginSchema` removed) [code: UPGRADE-6.0.md:27-33 @7.x].
- `AbstractIntegration::__construct()` lost `SessionInterface` (session via `RequestStack`); session service gone [code: UPGRADE-6.0.md:25 @7.x].
- `$request->request->get()` must return a scalar (use `->all()[...]`); Doctrine `Order` enum; functional-test API changes (`xmlHttpRequest` + `setCsrfHeader`, `loginUser($user)`, `assertResponseIsSuccessful`); form submissions stored without HTML-entity encoding; `CoreParametersHelper::getParameter()` → `get()` [code: app/bundles/*/*Events.php @7.x vs @8.x].
- PR-derived: `mautic:update:apply` works from the CLI without a session [PR #14681]; remaining legacy tables converted to `utf8mb4` [PR #14618]; release `version` must carry the stability suffix of the milestone (`6.0.0-alpha`) [PR #14507]. 6.0.1 fixed index existence checks in two migrations [PR #14824] [PR #14852]. 6.0.5 removed the Citrix table-drop migration [PR #15385]. No migrations were squashed at 6.0 [code: git diff --diff-filter=D 5.2.0 6.0.0 -- app/migrations @7.x].

### 7.0 (`UPGRADE-7.0.md`)
- PHP 8.1 → 8.2; MySQL 5.7.14 → 8.4.0; MariaDB 10.2.7 → 10.11.0 [code: UPGRADE-7.0.md:3-6 @7.x].
- Browser updater removed: update from the command line [code: UPGRADE-7.0.md:9 @7.x].
- API rate limiter removed "temporarily" (the note says it should return before 7 stable); it did not: 7.2.1 has no rate-limiting code [code: UPGRADE-7.0.md:10 @7.x] [code: app/config/security.php:105-108 @7.x].
- `track_by_tracking_url` removed; `ct` identification was already the default [code: UPGRADE-7.0.md:11 @7.x].
- Many deprecated classes removed: `MauticFactory`, `MauticSqliteTestCase`, `CustomFormEvent`, `UTF8Helper`, `EmojiExtension`, `TwilioApi`, Oauth2ThreeLegged interfaces (→ `AuthenticationInterface`/`AuthCredentialsInterface`), and more [code: UPGRADE-7.0.md:13-30 @7.x].
- Composer deps removed (`symfony/yaml`, `symfony/templating`, `php-amqplib/rabbitmq-bundle`, `symfony/amqp-messenger`, `noxlogic/ratelimit-bundle`, …); JS `Mautic.insertTextInEditor` → `Mautic.insertHtmlInEditor` [code: app/bundles/*/*Events.php @7.x vs @8.x].
- Citrix migration `Version20230522141144` removed; `plugin_citrix_events` may be dropped by hand [code: UPGRADE-7.0.md @7.x].
- PR-derived: the Citrix drop migration was removed to avoid data loss for forks [PR #15384]; a missing `point_groups.uuid` migration was added before GA [PR #15351]; the list-permission migration creates the row first [PR #15456]. Cadence: beta 2025-10-20, rc 2025-11-11, rc2, GA 2026-01-20 [PR #15581] [PR #15630] [PR #15717] [PR #15793]. No migrations were squashed at 7.0 [code: git diff --diff-filter=D 6.0.0 7.0.0 -- app/migrations @7.x].

### PHP → Twig (`UPGRADE-PHP-TO-TWIG-TEMPLATES.md`)
- Templates extend `@MauticCore/Default/content.html.twig` and fill blocks (`headerTitle`, `mauticContent`, `actions`); use `{% trans %}`, `path()`, `form_start/row/end`, `securityHasEntityAccess()` [code: UPGRADE-PHP-TO-TWIG-TEMPLATES.md @7.x].
- `strict_variables` is on in dev and prod: everything in a child of `content.html.twig` must be inside a block; prefer `is defined and … is not empty` over `!empty` [code: UPGRADE-PHP-TO-TWIG-TEMPLATES.md @7.x]. See mautic-theme-development.

## 4. 7.x minors

There are no `UPGRADE-7.1.md` / `UPGRADE-7.2.md` files; minor BC notes live only in GitHub release notes [code: repository root @7.x].
Schema changes shipped per minor (all additive) [code: app/bundles/*/*Events.php @7.x vs @8.x]:

- **7.0.0** (33 migrations): `lead_fields.column_is_not_removed`; page drafts; `pages.public_preview`; orphan form-result column cleanup; `campaign_events.channel_id` VARCHAR(64); `emails.continue_sending`; `webhook_queue` reshaped (drop `payload`, add `retries`) and `id` BIGINT; webhook health columns; `dynamic_content.type`; `form_fields.field_width`; Projects (`projects` + 15 xref tables); `<prefix>idx_scheduled_events`; multiselect segment operators rewritten (`including_any`→`including_all`, `excluding_any`→`excluding_all`); point-group `uuid`; optimistic-lock `campaign_lead_event_log.version`; SMS and push translation parents; `date_queued`.
- **7.1.0** (9): Segment soft delete (`lead_lists.deleted` + index); campaign `redirect_event_id`; `campaigns.republish_behavior`; project name index; `monitoring.uuid`; `pages.version` / `emails.version`; `assets.alias` nullable.
- **7.2.0** (13): `sms_messages.media` JSON and `is_mms`; `emails.send_to_dnc`; `user_invites`; `campaign_events.date_linked/date_added`; `lead:notes` permission backfill; Company soft delete; Form submission limits; `point_insights`; `emails.settings`; `leads.last_active` index; form auto-fill config flag written to `local.php`; `campaign_lead_event_log` index reorder.
- **7.2.1**: no migrations.
- 7.x features after 7.2.1, not yet released and not yet on 8.x ([post-7.2.1-prs.md](post-7.2.1-prs.md)): unsubscribe/resubscribe email-validation page and "Require email validation for unsubscribe" setting, email preview "Download HTML", asset multi-download ZIP, "Any associated company" segment filters, `POST /api/companies/batch/addcontacts`, Users `is:never_logged_in`, Contacts "Save & New" [code: 7.x vs 8.x tree grep].
- PR-derived 7.2.0: skip assertions are ANDed, so the mailer DSN migration now uses one combined assertion and never overwrites `mailer_dsn` [PR #16925]; API Library tests run in core CI, so release-prep PRs no longer link a manual run [PR #17227]. 7.2.1 was a metadata-only release PR [PR #17504]. Background for all of this: [pr-history.md](pr-history.md) [PR #13823].

Each area skill's `references/version-notes.md` holds the area-specific 5.x/6.x/7.x differences.

## 5. 8.x (in development)

- PHP 8.4, Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4, PHPUnit 13 [PR #16993] [PR #17392] [PR #17361] [PR #17004].
- Events dispatched by class; 225 constants removed; legacy campaign actions removed; Clearbit removed; form types removed [PR #17157] [PR #17097] [PR #17785] [PR #17082].
- Full guide: [upgrade-to-8.md](upgrade-to-8.md); event mapping: [event-map-7-to-8.md](event-map-7-to-8.md).
