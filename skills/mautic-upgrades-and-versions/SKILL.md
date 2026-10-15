---
name: mautic-upgrades-and-versions
description: "Mautic versions and moving between them: release timeline 1.x to 7.2 with PHP and database requirements per major, support policy, branch and tag model, the CLI updater (mautic:update:find, mautic:update:apply), Composer-based updates, pre-update checks, migrations during an update, recovering from a failed update, UPGRADE-*.md breaking changes, and the authoritative Mautic 7.x to 8.x guide (PHP 8.4, Symfony 8, Doctrine ORM 3 / DBAL 4, event constants replaced by event classes, removed features, porting and dual-version plugins). Use whenever a task mentions upgrading or updating Mautic, which version or whether it is supported, minimum PHP, Mautic 8 or the 8.x branch, BC breaks, a listener that stopped firing after upgrading, porting a plugin to 8, making a plugin work on 7 and 8, a failed update, doctrine:migrations:migrate after update, or touches app/bundles/CoreBundle/Update/ or UPGRADE-*.md."
---
# Mautic upgrades and versions

## Scope
This skill covers which Mautic versions exist and what they require, how an installed instance is updated (CLI updater or
Composer), what happens to the database during an update and how to recover, the breaking changes of each major, and the
complete 7.x → 8.x migration guide for plugin and core code. Writing new migrations is in mautic-contributing and
mautic-architecture; installing Mautic and setting `local.php` is in mautic-configuration; local stacks are in
mautic-dev-environment.

Terms: **Contact** = a marketing record (code: `Lead`); **Plugin** = a bundle in `plugins/`; **major** = X in X.Y.Z;
**minor** = Y; **BC break** = backwards-compatibility break.

## Expected behaviour (essentials)

Versions and platform
- Current stable is 7.2.1 (tagged 2026-09-23): PHP 8.2.0–8.5.99, MySQL ≥ 8.4.0, MariaDB ≥ 10.11.0 [code: app/release_metadata.json @7.x] [code: git tag @7.x].
- 8.x is unreleased development: PHP 8.4 minimum, Symfony 8.1, Doctrine ORM 3.7 / DBAL 4.4, PHPUnit 13; DB minimums unchanged [code: app/composer.json @8.x] [PR #16993] [PR #17392] [PR #17361].
- 7.0 raised the floor from PHP 8.1 / MySQL 5.7.14 / MariaDB 10.2.7 to PHP 8.2 / MySQL 8.4.0 / MariaDB 10.11.0, so a 6.x host usually needs a DB server upgrade before Mautic 7 [code: UPGRADE-7.0.md:3-6 @7.x].
- Any version ≥ 5.0.0 can update directly to a 7.x release (`minimum_mautic_version`); 5.x needed ≥ 4.4.10; 4.0 needed ≥ 3.2.0; 2.x had to reach the latest 2.x before 3.0 [code: app/release_metadata.json @7.2.1, @5.0.0, @4.0.0] [code: UPGRADE-3.0.md:19 @7.x].
- Only the 7.2.x series is listed as supported in the bug template; the authoritative matrix is https://www.mautic.org/mautic-releases [code: .github/ISSUE_TEMPLATE/BUG-REPORT.yml:24-41 @7.x] [code: SECURITY.md:17-21 @7.x].
- Branches: `7.x` = features, `7.0`/`7.1`/`7.2` = bug fixes (merged upward), `8.x` = BC breaks [code: .github/PULL_REQUEST_TEMPLATE.md:1-36 @7.x].

The updater
- Updating is CLI-only from 7.0; the browser updater (`UpdateController`, `/s/update/schema`) existed through 6.0.x [code: UPGRADE-7.0.md:9 @7.x] [code: git ls-tree 6.0.0 / 7.0.0].
- `mautic:update:apply` is two-phase: phase 1 (checks, new files, deleted files, cache nuke) then a hard `exit()`; phase 2 `--finish` (language packs, migrations, finalise) [code: app/bundles/CoreBundle/Command/ApplyUpdatesCommand.php:90-108 @7.x] [code: app/bundles/CoreBundle/Update/StepProvider.php:33-60 @7.x].
- With `composer_updates` = true the command refuses to run at all, including `--finish` [code: ApplyUpdatesCommand.php:84-88 @7.x].
- Without `--force` phase 1 asks for confirmation, default No [code: ApplyUpdatesCommand.php:117-125 @7.x].
- `--update-package <zip>` skips all pre-update checks [code: app/bundles/CoreBundle/Update/Step/PreUpdateChecksStep.php:38-44 @7.x].
- Pre-update checks abort before any file changes when PHP is outside min/max, the DB is below the MySQL/MariaDB minimum, metadata is missing, or no newer compatible release exists; all failures print together [code: app/bundles/CoreBundle/Helper/UpdateHelper.php:166-196 @7.x].
- The release offered is the first GitHub release whose `release_metadata.json` exists, passes `update_stability`, accepts the running version via `minimum_mautic_version`, and is newer [code: app/bundles/CoreBundle/Helper/Update/Github/ReleaseParser.php:25-86 @7.x].
- Update data is cached 3 hours in `lastUpdateCheck.txt`; `mautic:update:find` bypasses the cache and always exits 0, even on error [code: UpdateHelper.php:83-95 @7.x] [code: app/bundles/CoreBundle/Command/FindUpdatesCommand.php @7.x].
- An empty `system_update_url` disables update checks and reports "running the latest version" [code: UpdateHelper.php:288-291 @7.x].

Migrations and recovery
- Phase 2 runs `doctrine:migrations:migrate`; Doctrine executes every unrecorded migration regardless of its date, so migrations must be idempotent [code: app/bundles/CoreBundle/Update/Step/UpdateSchemaStep.php:41-54 @7.x] [code: app/migrations/ @7.x].
- A `PreUpAssertionMigration` is skipped only if all its assertions are true [code: app/bundles/CoreBundle/Doctrine/PreUpAssertionMigration.php:26-45 @7.x].
- Fresh installs and functional tests never run migrations; they build schema from entity metadata and mark migrations executed [code: app/bundles/InstallBundle/Install/InstallService.php:528-547 @7.x].
- There is no rollback: files are replaced and cache nuked before the schema step [code: StepProvider.php @7.x].
- A failed migration step hides Doctrine's output (NullOutput); re-run `php bin/console doctrine:migrations:migrate` to see the error [code: UpdateSchemaStep.php:41-54 @7.x].
- Some 7.2 migrations write data or files: `Version20260709103000` writes to `config/local.php` and throws if it is not writable [code: app/migrations/Version20260709103000.php @7.x].
- Deleted-file and language-pack failures are only logged; the update continues [code: app/bundles/CoreBundle/Update/Step/RemoveDeletedFilesStep.php:34-77 @7.x] [code: app/bundles/CoreBundle/Update/Step/UpdateTranslationsStep.php:36-80 @7.x].
- A Plugin bundle with `MINIMUM_MAUTIC_VERSION` above the running version is not loaded [code: app/AppKernel.php:175-181 @7.x].

7.x → 8.x
- 8.x dispatches events by class (`dispatch($event)`); subscribe to `LeadPostSaveEvent::class`, not `LeadEvents::LEAD_POST_SAVE` [code: UPGRADE-8.0.md @8.x] [PR #17157] [PR #17625].
- **Silent failure:** some constants still exist on 8.x (webhook type ids, BC) but are no longer dispatched; a listener keyed on them loads and never runs [code: UPGRADE-8.0.md @8.x "Changed code"].
- 225 event constants are removed and `ApiEvents`, `ConfigEvents`, `CoreEvents`, `DashboardEvents`, `IntegrationEvents`, `StatEvents`, `UserEvents` are deleted (fatal on reference) [code: app/bundles/*/*Events.php @7.x vs @8.x].
- Campaign actions registered without `batchEventName` are not executed on 8.x [PR #17097].
- Removed on 8.x: Clearbit plugin, Form "type" (standalone/campaign, column dropped), emoji conversion, `CacheStorageHelper`, `mautic:disable-tracking` attribute, `file_lock` mode, `/sms/receive` [PR #17785] [PR #17082] [PR #17026] [PR #17033] [code: UPGRADE-8.0.md @8.x].
- 7.2.1 and the later unreleased 7.x work are not merged into 8.x yet; features only on 7.x are pending, not removed [PR #17253].
- `UPGRADE-8.0.md` contradicts itself about kept constants; code wins [code: UPGRADE-8.0.md @8.x].

## Where it lives

| Concern | Path(s) |
|---|---|
| Update commands | `app/bundles/CoreBundle/Command/{ApplyUpdatesCommand,FindUpdatesCommand}.php` |
| Update steps | `app/bundles/CoreBundle/Update/StepProvider.php`, `Update/Step/*Step.php` (orders 0–60; tag `mautic.update_step`) |
| Update data, stats, checks | `app/bundles/CoreBundle/Helper/UpdateHelper.php`, `Helper/Update/{Github,PreUpdateChecks,Exception}/`, `Helper/PreUpdateCheckHelper.php` (tag `mautic.update_check`) |
| Release metadata | `app/release_metadata.json`, `app/bundles/CoreBundle/Release/{Metadata,ThisRelease}.php`, `app/AppKernel.php:41-44` |
| Migrations | `app/migrations/`, `app/config/config.php:225-236`, `CoreBundle/Doctrine/{AbstractMauticMigration,PreUpAssertionMigration}.php` |
| Config params | `update_stability`, `system_update_url`, `stats_update_url`, `composer_updates` in `CoreBundle/Config/config.php:296,718-720,807` |
| Upgrade notes | `UPGRADE-{3.0,4.0,4.3,5.0,6.0,7.0}.md`, `UPGRADE-PHP-TO-TWIG-TEMPLATES.md`, `UPGRADE-8.0.md` @8.x |
| Policy | `SECURITY.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/BUG-REPORT.yml`, `.github/release.yml`, `RELEASE_LEADS.md` (stale) |
| Tests | `app/bundles/CoreBundle/Tests/Unit/{Update,Helper/Update,Release,Doctrine}/`, `Tests/Unit/Helper/UpdateHelperTest.php` |

Sources: [code: app/bundles/CoreBundle/ @7.x] [code: app/release_metadata.json @7.x]. Full detail in references/code-map.md.

## How to change or extend it

- Add an update step by implementing `StepInterface` and tagging `mautic.update_step`; pick an order between the existing 0/10/20/30 (before files are final) or 40/50/60 (after) [code: StepProvider.php:22-30 @7.x].
- Add a pre-update check by extending `AbstractPreUpdateCheck` and tagging `mautic.update_check` [code: app/bundles/CoreBundle/Helper/PreUpdateCheckHelper.php:20-27 @7.x].
- Bump `version` and `announcement_url` in `app/release_metadata.json` before tagging; the release workflow rejects a tag that differs [code: .github/workflows/release.yml:38-47 @7.x].
- Raise `minimum_php_version` / `minimum_mysql_version` / `minimum_mariadb_version` only in a major, and write the change into that major's `UPGRADE-X.0.md` under "Platform requirements" [code: UPGRADE-7.0.md:3-6 @7.x] [kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html].
- Every schema change needs both the entity mapping (fresh installs) and an idempotent migration (upgrades) [code: InstallService.php:528-547 @7.x]. Migration rules are in mautic-contributing.
- BC breaks go to the next-major branch (`8.x`) with an `UPGRADE-8.0.md` entry and the `bc-break` label [code: .github/PULL_REQUEST_TEMPLATE.md @7.x] [code: .github/release.yml @7.x].
- In new 7.x code, avoid everything 8.x removes: string event keys, `ON_CAMPAIGN_TRIGGER_ACTION`, `CacheStorageHelper`, `FormController`, `definePermissions()`, `config.php` `services`, string service ids, `Request::get()` (full list in references/upgrade-to-8.md §12) [code: UPGRADE-8.0.md @8.x].
- For code that must run on 7.x and 8.x: subscribe with both the class key and the guarded constant key; use `batchEventName` + `PendingEvent`; add native types to every override now (references/upgrade-to-8.md §9) [code: UPGRADE-8.0.md @8.x] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].

## How to test it

- Updater: unit tests in `app/bundles/CoreBundle/Tests/Unit/Update/` (base `Update/Step/AbstractStepTestCase.php`), `Tests/Unit/Helper/UpdateHelperTest.php`, `Tests/Unit/Helper/Update/Github/ReleaseParserTest.php`, `Tests/Unit/Helper/Update/PreUpdateChecks/*` [code: app/bundles/CoreBundle/Tests/Unit/ @7.x].
- Copy from: `StepProviderTest.php` (ordering), `PreUpdateChecksStepTest.php` (skip with `--update-package`), `ReleaseParserTest.php:58-122` (release selection), `UpdateHelperTest.php:826,851` (platform failures), `Release/MetadataTest.php` [code: app/bundles/CoreBundle/Tests/Unit/ @7.x].
- Migrations: functional tests do not execute migrations, so unit-test a migration against a built `Schema` as in `Tests/Unit/Doctrine/CampaignLeadEventLogIndexMigrationTest.php` [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:159 @7.x].
- A good updater regression test asserts the observable outcome: which release is chosen for a given stability and running version, which messages print, and that no file step runs after a failed check.
- Manual end-to-end: clone production to staging (crons off, change `site_url`, capture mail), run the update there, then check System Info > Error Log [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html].
- Testing a plugin on 7.x and 8.x: references/upgrade-to-8.md §11. Test base classes are in mautic-testing.

## Version notes

- 3.0: `bin/console`, `release_metadata.json`, GitHub-releases updater, `{contactfield=}` tokens [code: UPGRADE-3.0.md @7.x].
- 4.0: PHP 7.4, Symfony 4, OAuth1 removed; browser updater deprecated in 4.2 [code: UPGRADE-4.0.md @7.x] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-in-the-browser].
- 5.0: PHP 8.0/8.1, Symfony 5, Symfony Mailer (DSN), Messenger, `config/local.php`, Twig-only templates, Composer default [code: UPGRADE-5.0.md @7.x].
- 6.0: Symfony 6, legacy builder and Froala removed, `MauticFactory` getters removed, `PluginDatabase` [code: UPGRADE-6.0.md @7.x].
- 7.0: PHP 8.2, MySQL 8.4 / MariaDB 10.11, browser updater removed; 7.1/7.2 additive only (9 and 13 migrations), no `UPGRADE-7.x` files; 7.2.1 has no migrations [code: UPGRADE-7.0.md @7.x] [code: app/migrations/ @7.x].
- 8.x: see references/upgrade-to-8.md and references/event-map-7-to-8.md.

## Pitfalls

- Docs tell Composer users to run `mautic:update:apply --finish`; with `composer_updates` on, it fails. Run `doctrine:migrations:migrate --no-interaction` and `cache:clear` instead [code: ApplyUpdatesCommand.php:84-88 @7.x] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-mautic-composer-based-installs].
- Docs still describe a browser updater "removed in 5.0" and a `/s/update/schema` tool; both existed until 6.0.x and are gone in 7.x [code: git ls-tree 6.0.0 / 7.0.0] [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#checking-for-schema-updates].
- Install docs still say PHP 7.4 and `recommended-project:^5` [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#how-can-you-specify-a-php-version].
- Skipping phase 2 leaves new code on an old schema; errors look like random SQL failures [code: StepProvider.php @7.x].
- `mautic:update:find` exit code 0 does not mean the check succeeded [code: FindUpdatesCommand.php @7.x].
- `doctrine:schema:update --force --complete` (KB last resort) drops custom DB objects and the `migrations` table [kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html].
- Running updates as root breaks cache ownership (Doctrine proxy "failed to open stream") [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html].
- On 8.x a listener on a kept constant (`FormEvents::FORM_ON_SUBMIT`, `LeadEvents::LEAD_POST_SAVE`, `PageEvents::PAGE_ON_HIT`, `ReportEvents::*`, `ChannelEvents::*`) never fires and nothing logs it [code: UPGRADE-8.0.md @8.x].
- A two-dot `7.x..8.x` diff shows 7.x-only features as "removed in 8"; use a three-dot diff [PR #17253].
- `app/release_metadata.json@8.x` says 7.2.0; do not read the version from it [code: app/release_metadata.json @8.x].
- `RELEASE_LEADS.md` dates are stale; use tags [code: RELEASE_LEADS.md @7.x].
- `FinalizeUpdateStep` prints a session `post_upgrade_message` that nothing sets [code: app/bundles/CoreBundle/Update/Step/FinalizeUpdateStep.php:34-56 @7.x].
- Open question: UPGRADE-3.0 lists PHP 7.2–7.4 while `release_metadata.json@3.0.0` caps PHP at 7.3.99 (later 3.x may have raised it) [code: UPGRADE-3.0.md:4 @7.x] [code: app/release_metadata.json @3.0.0].
- Open question: devdocs 8.0 call `CompanyEvent`, `LeadListEvent`, `WebhookEvent` `final`; 8.x code has them `abstract` [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#affected-classes] [code: UPGRADE-8.0.md @8.x].

## Related skills

- mautic-contributing — branch to target, PR template, writing migrations and UPGRADE entries.
- mautic-plugin-development — plugin structure, plugin migrations, Marketplace packaging.
- mautic-architecture — kernel, bundles, Doctrine wiring, event dispatcher.
- mautic-configuration — install, `local.php`, Configuration settings (`update_stability`, `composer_updates`).
- mautic-dev-environment — DDEV and local stacks for running 7.x and 8.x side by side.
- mautic-troubleshooting — broader error diagnosis after an update.
- mautic-testing — test base classes and fixtures.
- Every area skill's `references/version-notes.md` — area-specific 5.x/6.x/7.x/8.x differences.

## Reference files

- references/behaviour.md — numbered rules for the updater, release selection, migrations during update, recovery, metadata, support and branches; open for exact conditions and messages.
- references/code-map.md — files, commands, config parameters, extension points and tests of the update system.
- references/docs-digest.md — what the user docs, devdocs and KB say about updating, with procedures and docs-vs-code discrepancies.
- references/version-notes.md — release timeline with platform per major, upgrade paths, UPGRADE-3.0 → 7.0 and PHP → Twig summaries, 7.x minors.
- references/upgrade-to-8.md — the full 7.x → 8.x guide: platform, events, campaign actions, per-bundle BC breaks, behaviour changes, removals, dual-version code, porting steps, testing on both versions.
- references/event-map-7-to-8.md — every removed 7.x event constant and its 8.x event class, plus the kept-constant trap list.
- references/pr-history.md — not yet generated; PR-derived history is added in a later pass.
