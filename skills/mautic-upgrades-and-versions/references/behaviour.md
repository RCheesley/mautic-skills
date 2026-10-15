# Update system and version policy — behaviour specification (Mautic 7.x)

Numbered rules for how an installed Mautic finds, applies and recovers from updates, how schema changes reach existing
installs, and how versions, branches and support are defined. Authoritative tree: 7.x at `419a08a9b35` (7.2.1 plus unreleased merged PRs). 8.x deltas are
flagged inline; the full 8.x guide is [upgrade-to-8.md](upgrade-to-8.md).

## Contents
- A. Update entry points and modes (UB-A1 – A6)
- B. Two-phase CLI update sequence (UB-B1 – B12)
- C. Pre-update checks and release selection (UB-C1 – C10)
- D. Migrations during an update (UB-D1 – D12)
- E. Failure modes and recovery (UB-E1 – E9)
- F. Release metadata, versions and plugin gating (UB-F1 – F7)
- G. Support policy, branches and tags (UB-G1 – G9)

## A. Update entry points and modes

UB-A1. Updating is CLI-only on 7.x. `UPGRADE-7.0.md` removed the browser updater; `CoreBundle/Controller/UpdateController.php` exists at tags 4.4.0, 5.0.0 and 6.0.0 and is absent from 7.0.0 [code: UPGRADE-7.0.md:9 @7.x] [code: git ls-tree 6.0.0 / 7.0.0].

UB-A2. There are two supported update methods: the non-Composer CLI updater (`mautic:update:find`, `mautic:update:apply`, `mautic:update:apply --finish`) and Composer (`composer update` of `mautic/*` packages) [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html].

UB-A3. The Configuration setting "Update Mautic through Composer [BETA]" stores `composer_updates` (default `false`) [code: app/bundles/CoreBundle/Config/config.php:807 @7.x] [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:160-171 @7.x].

UB-A4. When `composer_updates` is `true`, `mautic:update:apply` prints "You have Composer updates enabled. This means that you can only update Mautic through the 'composer update' command…" and returns FAILURE. The check runs before the `--finish` branch, so `--finish` is refused too [code: app/bundles/CoreBundle/Command/ApplyUpdatesCommand.php:84-88 @7.x] [code: app/bundles/CoreBundle/Translations/en_US/messages.ini:132 @7.x].

UB-A5. `composer_updates = true` is a prerequisite for installing and updating Plugins through the Marketplace; the Marketplace is not compatible with ZIP installs [code: messages.ini:231 @7.x] [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html].

UB-A6. Admin users get an in-app "update available" notification. It is checked at most once per session per hour and shown at most once per session per version [code: app/bundles/CoreBundle/Model/NotificationModel.php:168-203 @7.x].

## B. Two-phase CLI update sequence

UB-B1. `mautic:update:apply` runs in two invocations. Without `--finish` it runs the initial steps (orders 0–30); with `--finish` it runs the final steps (orders 40–60) [code: app/bundles/CoreBundle/Command/ApplyUpdatesCommand.php:90-108 @7.x] [code: app/bundles/CoreBundle/Update/StepProvider.php:33-60 @7.x].

UB-B2. Phase 1 ends with `exit($returnCode)`, a hard process exit, so the old kernel never runs against the new files. It prints "IMPORTANT: Run the same command again with --finish. For example 'php bin/console mautic:update:apply --finish'" [code: ApplyUpdatesCommand.php:92-99 @7.x] [code: messages.ini:133 @7.x].

UB-B3. Without `--force`, phase 1 asks for confirmation with default No; declining throws `mautic.core.update.aborted` [code: ApplyUpdatesCommand.php:117-125 @7.x].

UB-B4. Step 0 `PreUpdateChecksStep` (initial) runs the pre-update checks and throws `UpdateFailedException` listing every failure. It is skipped when `--update-package` / `-p` is given [code: app/bundles/CoreBundle/Update/Step/PreUpdateChecksStep.php:38-66 @7.x].

UB-B5. Step 10 `InstallNewFilesStep` (initial) uses the local ZIP from `--update-package` or downloads the `package` URL from the update data, validates it, extracts it over the root path and deletes the ZIP [code: app/bundles/CoreBundle/Update/Step/InstallNewFilesStep.php:44-140 @7.x].

UB-B6. Step 20 `RemoveDeletedFilesStep` (initial) reads the JSON list in `<appRoot>/deleted_files.txt`, deletes each file, and deletes the list. A file that cannot be deleted is logged as "UPDATE ERROR" and the update continues [code: app/bundles/CoreBundle/Update/Step/RemoveDeletedFilesStep.php:34-77 @7.x].

UB-B7. Step 30 `DeleteCacheStep` (initial) nukes the cache via `CacheHelper::nukeCache()` [code: app/bundles/CoreBundle/Config/services.php:243-265 @7.x].

UB-B8. Step 40 `UpdateTranslationsStep` (final) re-downloads each installed non-en_US language pack when more than one language is installed. Errors are only logged; en_US is never re-downloaded [code: app/bundles/CoreBundle/Update/Step/UpdateTranslationsStep.php:36-80 @7.x].

UB-B9. Step 50 `UpdateSchemaStep` (final) runs `doctrine:migrations:migrate --quiet --no-interaction` in a fresh console Application. A non-zero exit throws `UpdateFailedException` with "An error occurred while updating the database. Check log for more details." [code: app/bundles/CoreBundle/Update/Step/UpdateSchemaStep.php:41-54 @7.x] [code: messages.ini:659 @7.x].

UB-B10. Step 60 `FinalizeUpdateStep` (final) deletes `upgrade.php` and `lastUpdateCheck.txt` and prints "Success! You are now running version %version% of Mautic." [code: app/bundles/CoreBundle/Update/Step/FinalizeUpdateStep.php:34-56 @7.x] [code: messages.ini:666 @7.x].

UB-B11. Any `UpdateFailedException` prints its message and the command returns FAILURE [code: ApplyUpdatesCommand.php:100-108 @7.x].

UB-B12. `mautic:update:apply` takes no lock and is not a cron command; do not schedule it [code: ApplyUpdatesCommand.php @7.x].

## C. Pre-update checks and release selection

UB-C1. `mautic:update:find` fetches update data bypassing the cache and prints an error, "running the latest version", or the available version with its announcement. It always exits 0, even when the check fails [code: app/bundles/CoreBundle/Command/FindUpdatesCommand.php @7.x].

UB-C2. The release list comes from `system_update_url` (default `https://api.github.com/repos/mautic/mautic/releases`) [code: app/bundles/CoreBundle/Config/config.php:720 @7.x].

UB-C3. The chosen release is the first entry in API order whose `app/release_metadata.json` (fetched from `raw.githubusercontent.com/mautic/mautic/<tag>/app/release_metadata.json`) exists, has a `version`, matches the allowed stability, has `minimum_mautic_version` ≤ the running version, and has a version greater than the running one. Releases without metadata are skipped [code: app/bundles/CoreBundle/Helper/Update/Github/ReleaseParser.php:25-86 @7.x].

UB-C4. Stability gating uses `update_stability` (default `stable`; choices `alpha`, `beta`, `rc`, `stable`). `stable` accepts only stable releases; otherwise a release is skipped when `version_compare($allowed, $release, 'gt')`, so `beta` accepts beta, rc and stable but not alpha [code: ReleaseParser.php:31-38 @7.x] [code: app/bundles/CoreBundle/Config/config.php:296 @7.x] [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:553-558 @7.x].

UB-C5. The download is the release asset whose name contains `update.zip`. A missing asset is reported as the generic "error fetching updates" message [code: app/bundles/CoreBundle/Helper/Update/Github/Release.php @7.x] [code: app/bundles/CoreBundle/Helper/UpdateHelper.php:130-136 @7.x].

UB-C6. Update data is cached in `<cache>/lastUpdateCheck.txt` for 3 hours and invalidated when `update_stability` changes [code: UpdateHelper.php:83-95,263-278 @7.x].

UB-C7. An empty `system_update_url` disables checks and reports "running the latest version", not an error [code: UpdateHelper.php:288-291 @7.x].

UB-C8. Each uncached check first POSTs anonymous stats (application, version, PHP version, DB driver, server OS, instanceId = sha1(secret_key + install_source + db_driver), installSource) to `stats_update_url` with a 10-second connect timeout. Failures are logged and ignored; an empty URL disables it [code: UpdateHelper.php:199-260 @7.x].

UB-C9. Pre-update checks fail, before any file is touched, when: the update data has an error; the instance already runs the latest compatible version; release metadata is missing; PHP is below `minimum_php_version` or above `maximum_php_version`; the DB is MariaDB below `minimum_mariadb_version` or MySQL below `minimum_mysql_version`; or the platform is neither. All messages are collected and printed together [code: UpdateHelper.php:166-196 @7.x] [code: app/bundles/CoreBundle/Helper/Update/PreUpdateChecks/CheckPhpVersion.php @7.x] [code: …/CheckDatabaseDriverAndVersion.php @7.x].

UB-C10. MariaDB is detected from the DBAL platform class or from `SELECT VERSION()` containing "mariadb"; the comparison is `version_compare` on the raw version string [code: CheckDatabaseDriverAndVersion.php @7.x].

## D. Migrations during an update

UB-D1. Core migrations live in `app/migrations/` (namespace `Mautic\Migrations`); executed versions are recorded in `<db_table_prefix>migrations` [code: app/config/config.php:225-236 @7.x] [code: app/bundles/CoreBundle/Loader/EnvVars/MigrationsEnvVars.php:14 @7.x].

UB-D2. Doctrine runs every migration not yet recorded, in class-name order. The timestamp in a name is the authoring date, not the release: `Version20201007003589` first shipped in 7.0.0. Older-dated files therefore still run on upgrade [code: app/migrations/ @7.2.1; git ls-tree per tag].

UB-D3. Two names force ordering: `Version020230615115326` sorts first ("must run first otherwise the pre-up assertions for other migrations will fail on M5") and `Versionzz20230929183000` sorts last (moves `app/config/*local.php` to `config/`) [code: app/migrations/Version020230615115326.php:9-12 @7.x] [code: app/migrations/Versionzz20230929183000.php:11-40 @7.x].

UB-D4. A `PreUpAssertionMigration` is skipped ("Schema includes this migration") only when **all** its assertions are true. One false assertion runs the whole `up()`, so `up()` must tolerate partially applied state [code: app/bundles/CoreBundle/Doctrine/PreUpAssertionMigration.php:26-45 @7.x].

UB-D5. Fresh installs and functional tests never execute migrations: they build the schema from entity metadata and mark every migration executed (`doctrine:migrations:version --add --all`). An entity change without a migration breaks upgrades; a migration without the entity change breaks fresh installs [code: app/bundles/InstallBundle/Install/InstallService.php:528-547 @7.x] [code: app/bundles/CoreBundle/Test/AbstractMauticTestCase.php:159 @7.x].

UB-D6. After `doctrine:migrations:migrate` finishes, missing generated columns and their indexes are added automatically, or a warning is printed if the DB cannot support them [code: app/bundles/CoreBundle/EventListener/MigrationCommandSubscriber.php:28-75 @7.x].

UB-D7. `down()` is a no-op by default and the updater never calls it; there is no schema rollback. `Version20250402103942::down()` is broken (single-quoted interpolation) [code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:61-64 @7.x] [code: app/migrations/Version20250402103942.php:29 @7.x].

UB-D8. Some migrations change data or files, not only schema. `Version20260709103000` writes `form_field_autofill => true` into the local config file when any form field has auto-fill, and throws if the file is not writable. `Version20260501090000` copies `lead:leads` permissions into a new `lead:notes` key for non-admin roles. `Version20250804003400` rewrites multiselect segment filter operators [code: app/migrations/Version20260709103000.php @7.x] [code: app/migrations/Version20260501090000.php:14-45 @7.x] [code: app/migrations/Version20250804003400.php @7.x].

UB-D9. Migration counts per release: 7.0.0 added 33 migrations vs 6.0.0; 7.1.0 added 9; 7.2.0 added 13; 7.2.1 added none [code: git ls-tree per tag @7.x].

UB-D10. 8.x adds one migration (`Version20260814141635`, drops `forms.form_type`) and edits many existing migrations for DBAL 4 and typed constants; 8.x CI fails if an existing table changes shape and runs `doctrine:schema:validate` [PR #17082] [PR #17407] [PR #17346].

UB-D11. Plugins do not use `app/migrations`. A plugin bundle extending `Mautic\IntegrationsBundle\Bundle\AbstractPluginBundle` gets its `Migrations/` run by `IntegrationsBundle\Migration\Engine` on install/upgrade; each migration's `isApplicable(Schema)` must return false once applied [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations].

UB-D12. Removing a core migration is a BC note: 7.0 removed `Version20230522141144` (Citrix); admins may drop `plugin_citrix_events` by hand [code: UPGRADE-7.0.md @7.x].

## E. Failure modes and recovery

UB-E1. There is no automatic rollback. Phase 1 overwrites files and nukes the cache before phase 2 touches the schema [code: StepProvider.php @7.2.1; steps 10–30].

UB-E2. If phase 2 fails in `UpdateSchemaStep`, the files are new and the schema is old. Migration output is sent to a NullOutput, so re-run `php bin/console doctrine:migrations:migrate` by hand to see the error [code: UpdateSchemaStep.php:41-54 @7.x].

UB-E3. If phase 1 succeeded but `--finish` was never run, translations, migrations and finalisation are pending; run `mautic:update:apply --finish` (non-Composer installs) or `doctrine:migrations:migrate` [code: StepProvider.php:33-60 @7.x].

UB-E4. The documented recovery order is: clear cache (`cache:clear` or `rm -rf var/cache`); `mautic:update:find` / `mautic:update:apply`; `doctrine:migration:status` then `doctrine:migration:migrate`; finally replace files by hand keeping `config/local.php`, `media/files`, `plugins`, `themes`, `translations` [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-is-available].

UB-E5. The KB adds `doctrine:schema:update --force` after migrations, with `--dump-sql` to preview, and `--force --complete` as a last resort that drops custom DB objects and the `migrations` table, after which `doctrine:migrations:migrate` must run [kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html]. Treat `--complete` as destructive.

UB-E6. Run update commands as the web-server user, never root; Doctrine proxy "failed to open stream" errors in `var/cache/prod/doctrine/orm/Proxies` usually mean files were written by a different user [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#running-update-commands-as-the-web-server-user] [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html].

UB-E7. Failed updates usually stem from under-resourced hosting; `Allowed memory size … exhausted` needs a higher `memory_limit`; `Class 'ZipArchive' not found` means the zip extension is missing [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html].

UB-E8. ZIP errors map to specific messages: `archive_zip_corrupt`, `archive_no_such_file`, `archive_not_valid_zip`, `archive_could_not_open`, `archive_file_exists` [code: InstallNewFilesStep.php:109-140 @7.x].

UB-E9. Always take a tested backup (files and DB, restored in a test environment) before updating [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html].

## F. Release metadata, versions and plugin gating

UB-F1. `app/release_metadata.json` at 7.2.1: version 7.2.1, stability stable, PHP 8.2.0–8.5.99, MySQL ≥ 8.4.0, MariaDB ≥ 10.11.0, `minimum_mautic_version` 5.0.0 [code: app/release_metadata.json @7.x].

UB-F2. `Metadata` is a `final readonly` value object. Required keys: `version`, `stability`, `minimum_php_version`, `maximum_php_version`, `minimum_mautic_version`, `announcement_url`; optional (default `''`): `show_php_version_warning_if_under`, `minimum_mysql_version`, `minimum_mariadb_version`. Versions parse as `major.minor.patch[extra]` [code: app/bundles/CoreBundle/Release/Metadata.php @7.x].

UB-F3. `MAUTIC_VERSION` is defined from the metadata file at kernel boot [code: app/AppKernel.php:41-44 @7.x].

UB-F4. `minimum_mautic_version` defines the oldest version that can update directly to the release via the updater: 7.x releases need ≥ 5.0.0; 6.0.0 needs ≥ 5.0.0; 5.0.0 and 5.2.0 need ≥ 4.4.10; 4.0.0 needs ≥ 3.2.0 [code: app/release_metadata.json @7.2.1, @6.0.0, @5.0.0, @5.2.0, @4.0.0].

UB-F5. The release workflow requires the pushed tag to equal `version` in `release_metadata.json`, so bump `version` and `announcement_url` before tagging [code: .github/workflows/release.yml:38-47 @7.x].

UB-F6. A plugin bundle class may declare `const MINIMUM_MAUTIC_VERSION`; the kernel skips loading the plugin when the running version is lower [code: app/AppKernel.php:175-181 @7.x].

UB-F7. On the 8.x snapshot the metadata still says `"version": "7.2.0"` while `minimum_php_version` is 8.4.0 [code: app/release_metadata.json @8.x].

## G. Support policy, branches and tags

UB-G1. Branch model: `a.x` = current-major feature branch (`7.x`, upstream default); `a.b` = maintenance branch for bug fixes (`7.0`, `7.1`, `7.2`, `6.0`, `5.2`, …); `c.x` = next major for BC breaks (`8.x`). Bug fixes target the lowest maintained branch where they apply and are merged upward [code: .github/PULL_REQUEST_TEMPLATE.md:1-36 @7.x]. Contribution rules are in mautic-contributing.

UB-G2. Tags are `X.Y.Z` plus pre-releases `X.Y.0-alpha`, `-beta`, `-rc`, `-rc2`. 7.0 went 7.0.0-alpha (2025-08-04) → beta (2025-10-20) → rc (2025-11-11) → rc2 (2025-12-10) → 7.0.0 (2026-01-20) [code: git tag @7.x].

UB-G3. The bug-report template lists only the 7.2.x series as supported; 7.1.x, 7.0.x, 6.0.x, 5.x, 4.x and 3.3.x are labelled "(not supported)" [code: .github/ISSUE_TEMPLATE/BUG-REPORT.yml:24-41 @7.x].

UB-G4. README and SECURITY.md defer the authoritative support matrix to https://www.mautic.org/mautic-releases [code: README.md:77-81 @7.x] [code: SECURITY.md:17-21 @7.x].

UB-G5. Security advisories cover stable releases in supported majors; fixes go to every affected supported major; out-of-sequence security releases get at least 2 weeks' notice; ELTS (paid, up to two years) covers versions past security support. Report privately via https://github.com/mautic/mautic/security [code: SECURITY.md:17-51 @7.x].

UB-G6. Semantic versioning in practice: breaking DB changes only in majors; additive DB changes can appear in minors [kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html]. No `UPGRADE-7.1.md` / `UPGRADE-7.2.md` exist; minor-release BC notes, if any, are only in GitHub release notes [code: repository root @7.x].

UB-G7. Cadence stated by the community: bug-fix releases monthly, feature releases quarterly, breaking changes about annually [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html].

UB-G8. GitHub release notes group PRs by label: `bc-break`, `refactoring`, `security`, `feature`/`enhancement`, `bug`/`regression`; `chore` and `github-actions` are excluded [code: .github/release.yml @7.x].

UB-G9. `RELEASE_LEADS.md` is stale (7.0 GA planned 2025-09-29; actual tag 2026-01-20; no 7.1/7.2 tables). Use tags for dates [code: RELEASE_LEADS.md @7.x] [code: git tag @7.x].
