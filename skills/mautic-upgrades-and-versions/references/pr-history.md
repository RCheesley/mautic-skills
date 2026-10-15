# PR history: migrations, the updater, releases and version policy

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
3. Regression catalogue
4. Feature timeline
5. Removed, deprecated, replaced
6. Maintainer norms for this area
7. Open questions
8. Coverage

## 1. How to read this file

- Source: merged pull requests on mautic/mautic in the migrations, upgrades and releases area, harvested 2026-10-15 [PR #261] [PR #17821].
- The version after each PR is inferred from its base branch and merge date; a 7.3.0-rc milestone would mean unreleased on 7.x after 7.2.1 ([post-7.2.1-prs.md](post-7.2.1-prs.md)) [PR #17504].
- Current behaviour is specified in [behaviour.md](behaviour.md). This file explains why and when it came about, and behaviour.md wins on any conflict [PR #13823].

## 2. Decisions that shaped current behaviour

### 2.1 Every schema change ships as an entity change plus a migration

- A schema change needs both the entity's Doctrine metadata (fresh installs build the schema from entities) and a migration (upgraded instances). A reviewer blocked an index added only as a migration: "if someone installs a fresh Mautic then this index won't exist for them" [PR #13413] (v5.1). Later index PRs follow the pair rule [PR #11588] [PR #13007] [PR #14556] [PR #14625] [PR #15015] [PR #16548] [PR #16759].
- The reverse is a bug too: an entity column without a migration is missing on upgraded instances. `point_groups.uuid` was added to the entity only, so a migration that adds and fills the column was added before 7.0 [PR #15351] (v7.0).
- The rule dates from 2.x: "This will need a migration so that schema matches Doctrine entity metadata" [PR #2971] (v2.3); an index added only to the entity "would add the index only to newly installed instances" [PR #6086] (v2.14). Same rule in [PR #4418] (v2.9) and [PR #6083] (v2.14).
- A metadata-only mapping change (for example `isShortVisible` on LeadField) also ships with a migration, "to avoid too much diff in schema update" [PR #14566] (v6.0).
- Mapping types must match the PHP property: `campaigns.allow_restart` became `BOOLEAN NOT NULL` by migration. The PR was retargeted from a bug fix to the feature branch because "there is no bug to blame" [PR #11279] (v5.1).
- The updater runs only migrations and never `doctrine:schema:update`, which is why every schema change must be a migration. Maintainers rejected the argument that schema update would fix dynamic custom-field columns [PR #7596] (v2.16). This still holds: the 7.x schema step runs `doctrine:migrations:migrate` [code: app/bundles/CoreBundle/Update/Step/UpdateSchemaStep.php:41-54 @7.x].
- Acceptance test: after `doctrine:migrations:migrate`, `doctrine:schema:update --dump-sql` shows nothing for the changed entities [PR #3979] (v2.8) [PR #5898] (v2.13) [PR #6092] (v2.14). Core's own agent guidance repeats this check [code: .agents/skills/mautic-dev/SKILL.md:27 @7.x].

### 2.2 Idempotency and skip assertions

- A migration must detect that its change is already present and skip, because fresh installs already have it and a migration can be re-run. Originally [PR #261] (v1.0); restated for fresh installs in [PR #5592] (v2.12): "New installations gets the fresh SQL schema from entities. But all the migrations will run on next update. So the migrations must handle both cases."
- The 2.x pattern was `CREATE TABLE IF NOT EXISTS` everywhere. galvani objected to rewriting old migrations; the blanket change was merged because nobody could name any harm [PR #5592] (v2.12). Per-statement guards inside `up()` were also accepted so one migration can apply some changes and skip others [PR #4193] (v2.9).
- Current rule: every core migration extends `PreUpAssertionMigration` and declares one `skipAssertion()` per SQL statement in `preUpAssertions()` [PR #13823] (v5.2) [code: app/migrations/Migration.template:14 @7.x].
- The migration is skipped only when every assertion returns true. One false assertion runs the whole `up()`, so `up()` must tolerate a partially applied schema [PR #16925] (v7.2) [code: app/bundles/CoreBundle/Doctrine/PreUpAssertionMigration.php:26-45 @7.x].
- Because assertions are ANDed, "skip when X or Y" must be one combined assertion. `Version20230615101328` had two separate ones ("local.php not writable", "mailer_dsn exists") and overwrote an existing `mailer_dsn` whenever `local.php` was writable. The fix combines them [PR #16925] (v7.2) [code: app/migrations/Version20230615101328.php:18-21 @7.x].
- An existence check must use the object's real (prefixed) name, otherwise the re-run fails with "Duplicate key name" [PR #14824] (v6.0.1). A trailing space in a table name broke a 2.x preUp check the same way [PR #5555] (v2.12).
- A migration that drops an index must check it exists first and skip otherwise ("Can't DROP INDEX") [PR #14852] (v6.0.1).
- A migration must not re-add a column that already exists, and preUp checks that read column comments must tolerate legacy `(DC2Type:json_array)` comments [PR #12491] (v5.0).

### 2.3 Table prefix handling

- Table names, index names, foreign-key names and existence checks all carry the prefix. Prefix bugs broke upgrades repeatedly [PR #4193] (v2.9) [PR #5165] (v2.11) [PR #8661] (v2.16) [PR #10233] (v4.0).
- The prefix is applied exactly once. Double prefixes such as `m_m_campaign_summary` broke 4.2 upgrades with "table already exists" and rename-index errors [PR #10931] (v4.2.1).
- preUp conditions must be right with and without a prefix. That fix went to the next major only, because rebasing onto the 4.4 bug-fix branch conflicted in 86 files [PR #11371] (v5.0).
- `AbstractMauticMigration::getPrefixedTableName()` is the shared helper, and the template uses it with a `TABLE_NAME` constant [PR #13823] (v5.2) [code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:194 @7.x].

### 2.4 Names, types and drivers

- Index and foreign-key names created by a migration must equal the names Doctrine generates from metadata, or `--dump-sql` keeps proposing renames. Use the prefix-aware `generatePropertyName()` / `generateKeys()` helpers [PR #5165] (v2.11).
- Do not assume a column type. M2-upgraded schemas had signed IDs where M3 had unsigned [PR #9720] (v3.3.1), and `leads.id` can be `INT` or `BIGINT`, which broke a foreign key ("Foreign key constraint is incorrectly formed") [PR #13284] (v5.0.3). Use `getColumnTypeSignedOrUnsigned()` / `getColumnType()` [code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:203-216 @7.x].
- Migrations must work on every supported DBAL driver, including `mysqli` [PR #8961] (v3.0.1).
- Use the Doctrine Migrations classes of the bundled version; the old `Doctrine\DBAL\Migrations\SkipMigrationException` namespace broke 3.2.0→3.2.1 upgrades. PHPStan analyses `app/migrations` since [PR #9480] (v3.2.2).
- `up()` must match the parent signature, including `: void` [PR #8462] (v3.0.1).
- Migration class names stay stable once released; a typo was corrected only because the version was unreleased [PR #12886] (v5.0).
- `mautic:migrations:generate` was removed in 3.0; use `bin/console doctrine:migrations:generate`, which applies `app/migrations/Migration.template` [PR #8429] (v3.0). The template was fixed in [PR #9170] (v3.1.1) and [PR #12491] (v5.0) and rewritten around skip assertions in [PR #13823] (v5.2).
- Use `utf8mb4` for columns that hold user text; emoji broke notifications and email-stat tokens [PR #9526] (v3.2.3) [PR #10844] (v4.2). Old instances that predate MySQL 8 had their remaining tables converted to `utf8mb4` [PR #14618] (v6.0).

### 2.5 Ordering, defaults and MySQL limits

- Doctrine runs every unrecorded migration, so independently merged migrations can interact. A row insert failed with "doesn't have a default value" after another migration added a NOT NULL column. The fix was a new migration timestamped to run earlier and add defaults [PR #10213] (v4.2).
- Columns that receive inserts during upgrade migrations must be nullable or defaulted [PR #4418] (v2.9.1) [PR #4538] (v2.9.2). A `lead_fields` insert must set every required column, such as `object` [PR #3311] (v2.6).
- A migration that creates a core contact field must update an existing field with the same alias, not insert a duplicate [PR #3311] (v2.6).
- Before adding an index to `leads`, check MySQL's 64-index limit and skip if it would be exceeded; guard each index separately [PR #4193] (v2.9) [PR #5898] (v2.13).
- Drop any index before converting a column to TEXT (MySQL error 1170) [PR #7596] (v2.16.1) [PR #9057] (v3.1). Drop and re-add foreign keys around a column change (MySQL error 1832) [PR #779] (v1.1) [PR #1007] (v1.2).
- Some indexes cannot be expressed in metadata (the `page_hits.url` prefix index) and were created by an install fixture plus a migration [PR #6864] (v2.15.1). Whether the dual path still exists is an open question (section 7).

### 2.6 `down()` and downgrades

- Mautic does not support downgrades: "We don't support downgrades in Mautic so we don't use Doctrine's `down()`" [PR #5165] (v2.11). The updater never calls `down()`, and the base implementation is still a no-op [code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:61-64 @7.x].
- Since 5.2 the template includes `down()` with "If it makes sense for your migration, undo what was done in the up() method here" [PR #13823] (v5.2) [code: app/migrations/Migration.template:46-49 @7.x].
- `down()` is encouraged, not required. Reviewers accepted index-only migrations without it ("the indexes won't hurt if they stay"), while others asked for it [PR #12305] (v5.2) [PR #16548] (v7.2). A working `down()` let users recover a failed point-groups migration with `--down` then `--up` [PR #13195] (v5.0.2).
- [PR #13823] said `up()` / `down()` would become `protected` for 6.x. It never happened: both are `public` in the 7.x base class and template, and the base `up()` still carries "@todo remove this method to make it absctract for Mautic 6" [code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:45-64 @7.x] [code: app/migrations/Migration.template:32-46 @7.x].
- An edited migration does not re-run where it already ran. Maxell92 argued for a new corrective migration instead of editing a merged one; in-place edits happened anyway [PR #5165] (v2.11) [PR #14824] (v6.0.1). See section 7.

### 2.7 Data and config migrations; no destructive changes

- Data fixes ship as migrations so existing rows are corrected, not only new ones. Examples: boolean filter values [PR #2995] (v2.3), category type `0` → `messages` [PR #8462] (v3.0.1), quotes in campaign event labels [PR #12651] (v5.0), recalculated `emails.read_count` [PR #13915] (v5.1.1).
- Renaming a stored value list (countries, regions) needs a data migration for every table that stores it, and is a BC break recorded in `UPGRADE-X.0.md`: Portuguese regions [PR #8134] (v3.1), Uttarakhand [PR #9204] (v5.0), French regions [PR #10802] (v5.0), Eswatini [PR #12061] (v5.0), AT/DE/CH regions [PR #12391] (v5.0), Türkiye in `leads` and `companies` [PR #13997] [PR #14170] (v5.2).
- Migrations may rewrite `config/local.php`: `db_server_version` [PR #9458] (v3.2.5), `%kernel.root_dir%` → `%kernel.project_dir%` [PR #12526] (v5.0), legacy mailer settings → `mailer_dsn` with URL-encoded parts and `%` doubled [PR #13256] (v5.0.3). The DSN migration never overwrites an existing `mailer_dsn` [PR #16925] (v7.2).
- Migrations may move config between scopes (SMS "disable trackable URLs" from Twilio to global SMS settings) [PR #11683] (v5.0) and may create notification-centre messages (Pipedrive and Citrix deprecation) [PR #12364] [PR #12367] (v4.4.9).
- Permission data migrations create the permission row before setting bitwise values [PR #15456] (v7.0).
- No destructive data changes that third parties may rely on. The migration dropping `plugin_citrix_events` was removed rather than fixed, because forks of the GoTo bundle still use the table: "Losing data sucks"; wasted space is cheap [PR #15384] (v7.0) [PR #15385] (v6.0.5). `UPGRADE-7.0.md` tells admins to drop the table by hand if unused [code: UPGRADE-7.0.md:69 @7.x].
- No slow row-by-row cleanup over large tables. The null-byte cleanup of `ip_addresses` was reverted in favour of read-time handling [PR #8664] (v3.0), superseding [PR #8636].

### 2.8 Migration lifecycle per major (squashing)

- At 5.0, migrations that shipped in the 4.x line were deleted from `app/migrations`: old instances had run them and new instances build from entities [PR #12441] (v5.0). The tree confirms 45 deletions between 4.4.0 and 5.0.0 [code: git diff --diff-filter=D 4.4.0 5.0.0 -- app/migrations @7.x].
- Delete only migrations that shipped in the previous major's release branch. A migration added during 5.0 alpha was deleted by mistake and restored in 5.0.1, because 4.4→5 upgrades broke forms [PR #13183] (v5.0.1) [PR #13194].
- Squashing is not done at every major. The tree shows deletions at 3.0 (136 files at 2.16.5, 9 at 3.0.0) and 5.0 only. 4.0, 6.0 and 7.0 kept all earlier migrations; 6.0→7.0 removed just the Citrix one [code: git ls-tree 2.16.5 3.0.0 4.0.0 5.0.0 6.0.0 7.0.0 -- app/migrations @7.x].
- The 7.x branch has 117 migrations. By name the oldest is `Version20190326190241`, but it was added in 2024; names are not release dates. `Version020230615115326` sorts first on purpose [code: app/migrations/ @7.x] [code: git log --diff-filter=A -- app/migrations/Version20190326190241.php @7.x].
- The squash requires a minimum source version. `minimum_mautic_version` was 3.2.0 for 4.0 [PR #10228] (v4.0) and is 5.0.0 for 7.x, matching the 5.0 squash [code: app/release_metadata.json @7.x].

### 2.9 The updater and `release_metadata.json`

- 3.x replaced `app/version.txt` with `app/release_metadata.json`, read by `mautic:update:find` and `mautic:update:apply`; the root `upgrade.php` and `upgrade_v3.php` scripts are gone [PR #9029] [PR #9455] [PR #10228] [code: app/bundles/CoreBundle/Command/ApplyUpdatesCommand.php @7.x].
- `stability` must match the release type. A wrong value offered 4.3.0-beta to production instances, and it had to be re-released as beta-2 [PR #11172] (v4.3). An `-rc` is offered only to the RC channel [PR #9029] (v3.0.2).
- The updater reads older releases' metadata from GitHub, so every new key must be optional when read. `show_php_version_warning_if_under` (added in 3.2.5) caused undefined-index notices until it was made optional [PR #9622] (v3.3). behaviour.md lists the required and optional keys in 7.x [code: app/bundles/CoreBundle/Release/Metadata.php @7.x].
- `version` must equal the GitHub milestone name including stability (`6.0.0-alpha`, `7.0.0-rc`), or the release workflow fails. A mismatch meant deleting and re-creating the tag [PR #14507] (v6.0.0-alpha) [PR #15630] (v7.0.0-rc) [PR #15717].
- Version strings may be `X.Y.Z-stability-suffix` (for example `4.2.0-beta-xxx`); the documented format stays `x.y.z[-alpha|beta|rc]` [PR #10919] (v4.3).
- Each release-prep PR updates `version` and `announcement_url` (the GitHub release tag URL) [PR #15450] (v6.0.5) [PR #17504] (v7.2.1).
- The update package ships `deleted_files.txt` so legacy files are removed; a 3.1→4.0-rc upgrade failed without it [PR #10228] (v4.0).
- `FinalizeUpdateStep` checks for a session before using it, so `mautic:update:apply` works from the CLI [PR #14681] (v6.0).
- Validated CLI path (5.2 → 7.0.0-beta, prod env): download the zip, `mautic:update:apply --update-package=./X.zip`, then `mautic:update:apply --finish` [PR #15630] (v7.0.0-rc).
- Upgrade fixes are tested by installing an old release and running `mautic:update:find` and `mautic:update:apply` [PR #8661] [PR #10228] [PR #10233].

### 2.10 Branch, release and deprecation policy

- Bug fixes target the patch branch (`a.b`), features `a.x`, BC breaks the next major `c.x` [PR #10407] (v4.0.1) [PR #10931] [PR #13915] [PR #14824]. When `a.x` is locked for a release, fixes go to `a.b` [PR #14824] (v6.0.1).
- A PR merged to the wrong branch is reverted and re-opened on the right one [PR #10843] [PR #10844] (v4.2).
- Once a major's last minor is out, its `.x` branch gets no more feature releases; fixes there ship only in the next major [PR #11371] (v5.0).
- After a patch release the patch branch is merged up into the feature branch ("Merging X to Y.x") [PR #13194] [PR #9334].
- Major cadence: alpha → beta(s) → rc(s) → GA. 5.0: alpha [PR #12517], beta1 [PR #12793], beta2 [PR #12806], rc1 [PR #12897], rc2 [PR #13089], GA [PR #13177] (2024-01-09). 7.0: beta [PR #15581], rc [PR #15630], rc2 [PR #15717], GA [PR #15793] (2026-01-20). Minors also get an rc: 7.2.0-rc [PR #16195], 7.2.0 [PR #17227].
- Several majors are patched in parallel: 5.2.10, 6.0.8 and 7.0.1 were prepared on 2026-02-24 [PR #15898] [PR #15899] [PR #15895].
- Until 7.2.0, each release-prep PR linked a green API Library test run; from 7.2.0 those tests run in mautic/mautic CI [PR #13177] [PR #16195] [PR #17227].
- A PR merged after a pre-release was tagged forces a re-tag or a new pre-release [PR #14625] [PR #14507]. The release lead may hold a release-prep PR until a named PR merges [PR #17227] [PR #16475].
- Release preparation changes only `release_metadata.json` from 5.0; in 2.x–4.x it also rebuilt production assets [PR #6582] [PR #11109] [PR #13633] [PR #12517].
- A hotfix release is reserved for upgrade-breaking or essential bugs; notices wait for the next release [PR #9480] [PR #9720] [PR #9622].
- Security releases have planned due dates across all affected supported versions (7.1.2 and 5.2.11, both due 2026-05-25). A non-security patch should go out first so fewer non-security changes mix with security fixes [PR #16059] (v7.1.1).
- Deprecate first, remove in the next major; removing a plugin or API in a patch is a BC break. Pipedrive and Citrix were deprecated in 4.4.9 with notices in code, config forms, CLI and user notifications, then removed in 5.0 [PR #12364] [PR #12367] (v4.4.9). `CoreParametersHelper::getParameter` had to be moved from 5.x to 6.x for the same reason [PR #13837] (v6.0).
- Changing stored values that the API exposes (region names) is a BC break and goes to the next major [PR #10802] (v5.0).
- Every BC break is recorded in `UPGRADE-X.0.md`; omissions are fixed by follow-up PRs [PR #8429] [PR #8805] [PR #12061] [PR #14400] [PR #14406] [PR #17821].
- Platform floors rise only in majors. 3.0 recommended MySQL 5.7.14 (from 5.5.3); escopecz refused to keep end-of-life MySQL 5.5 [PR #8394] (v3.0). Current floors are in behaviour.md [code: app/release_metadata.json @7.x].
- After 3.0 was imminent (April 2020) no new 2.x minors were made, and pending 2.x features were rebased on 3.x [PR #6126] [PR #8478].

### 2.11 Security policy and governance files

- `SECURITY.md` was added in 3.0 [PR #8379] [PR #8453]. Reporting moved to huntr.dev in 2021 [PR #10569], then to GitHub private vulnerability reporting when huntr.dev dropped non-AI projects [PR #12876] (v5.0) [PR #12877] (v4.4.11).
- Supported versions live in one place, the mautic.org releases page; per-file tables were removed because they drifted [PR #12876] [PR #15115] (v7.0), superseding [PR #11545].
- `SECURITY.md` says fixes go to all affected versions, mentions ELTS and covers other Mautic repositories [PR #15115] (v7.0).
- `MAINTAINERS.md` and `RELEASE_LEADS.md` live in the main repository after a General Assembly vote; the cost is back-merging across branches [PR #15004] (v7.0).

### 2.12 Product changes delivered by migration (examples only)

These PRs are in this area only because they carry a migration. The product behaviour belongs to the area skills; use them as migration examples.

- Column widening for free-length values (URLs, user agents, referrers): [PR #1190] [PR #2631] [PR #7084] [PR #9542] [PR #10407] [PR #10778]. Other widenings: `redirect_url` 2048 [PR #5484], tweet text 280 without index [PR #5594] [PR #9057], notification header 512 [PR #9569], multiselect fields as unindexed TEXT [PR #7596] [PR #8661].
- Performance indexes with entity plus migration: [PR #2632] [PR #3580] [PR #5898] [PR #6086] [PR #6092] [PR #6864] [PR #7082] (2.x); [PR #11588] [PR #13007] [PR #13413] [PR #12305] (5.x); [PR #14556] [PR #14625] (6.0); [PR #15015] (7.0); [PR #16548] [PR #16759] (7.2).
- `campaign_leads` index reordered campaign-first in place rather than adding a second composite; the migration handles legacy order and has a unit test [PR #16759] (v7.2) [code: app/bundles/CoreBundle/Tests/Unit/Doctrine/CampaignLeadEventLogIndexMigrationTest.php @7.x].
- Data-model changes with migrations: core fields `timezone` [PR #3311], `points` [PR #3858], `last_active` [PR #6279]; `campaign_events.channel_id` VARCHAR(64) [PR #15132] (v7.0); `emails.settings` JSON [PR #16363] (v7.2); `date_modified` backfill [PR #14433] (v6.0); `email_copies.body_text` [PR #11254] (v5.0).

## 3. Regression catalogue

Rows still describing a 7.x contract. Historical-only rows (removed scripts, 1.x mechanics) are omitted.

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **Idempotency and skip** | | | |
| Re-running a migration errors because columns exist | Migration detects the existing schema and skips | [PR #261] | 1.0 |
| Fresh install, then next update: "table exists" | Migrations skip on a schema built from entities | [PR #5592] | 2.12 |
| Writable `local.php` with an existing `mailer_dsn` is overwritten | DSN migration skips when `mailer_dsn` exists or the file is not writable | [PR #16925] | 7.2.0 |
| "Duplicate key name internal_object_id_idx" on re-run | preUp detects the existing index under its real name | [PR #14824] | 6.0.1 |
| "Can't DROP INDEX … company_match" in the utf8mb4 migration | Migration skips when the index is missing | [PR #14852] | 6.0.1 |
| "Table 'point_groups' already exists" | Point-groups migration skips; `--down`/`--up` recovers | [PR #13195] | 5.0.2 |
| "Unknown column type json_array"; duplicate `utm_campaign` | Legacy DC2Type comments and existing columns tolerated | [PR #12491] | 5.0 |
| **Prefix** | | | |
| 4.2 upgrade on prefixed DB: "campaign_summary already exists" | Prefix applied once in table, FK and index names | [PR #10931] | 4.2.1 |
| preUp checks wrong with or without prefix | Checks correct in both cases | [PR #11371] | 5.0 |
| Prefixed DB re-run: duplicate index name | Check uses the prefixed name | [PR #4059] | 2.8.2 |
| Prefixed DB: "no table oauth1_access_tokens" | Removal migration respects the prefix | [PR #10233] | 4.0 |
| **Types, drivers, order** | | | |
| Point-groups FK "incorrectly formed" where `leads.id` is INT | FK column follows the actual `leads.id` type | [PR #13284] | 5.0.3 |
| Migrations fail on M2-upgraded schemas (signed vs unsigned) | Migrations detect signedness | [PR #9720] | 3.3.1 |
| Migrations fail with the `mysqli` driver | Driver-agnostic migrations | [PR #8961] | 3.0.1 |
| `SkipMigrationException` class not found | Current Doctrine Migrations namespace; PHPStan covers migrations | [PR #9480] | 3.2.2 |
| "Field … doesn't have a default value" during migrate | Earlier migration adds defaults; order-safe | [PR #10213] | 4.2 |
| Upgrade fatal when `leads` has about 60 indexes | Index migrations skip at the 64-index limit | [PR #4193] | 2.9 |
| "BLOB/TEXT column used in key specification" | Index dropped before TEXT conversion | [PR #7596] | 2.16.1 |
| `--dump-sql` keeps proposing index renames after migrate | Migration names match Doctrine-generated names | [PR #5165] | 2.11 |
| **Entity and migration pairs** | | | |
| 6→7 upgrade missing `point_groups.uuid` | Migration adds and fills the column | [PR #15351] | 7.0 |
| Company custom field cannot be created | Mapping fix plus migration | [PR #14566] | 6.0 |
| **Data and config migrations** | | | |
| Mailer password with special characters breaks Mautic after 5.0 | DSN parts URL-encoded and `%` doubled | [PR #13256] | 5.0.3 |
| `%kernel.root_dir%` left in `local.php` breaks 5.0 | Migration rewrites to `%kernel.project_dir%` | [PR #12526] | 5.0 |
| Türkiye migration errors on 4.x-origin DBs | Updates `leads` and `companies` | [PR #14170] | 5.2 |
| List permission migration errors when the row is missing | Row created, then bits set | [PR #15456] | 7.0 |
| Campaigns cannot save: quotes in event labels | Migration strips bad quotes | [PR #12651] | 5.0 |
| Email read counts never update | Counter updates on read; history recalculated | [PR #13915] | 5.1.1 |
| Japanese characters not stored on old instances | All tables `utf8mb4` | [PR #14618] | 6.0 |
| `plugin_citrix_events` not dropped | Table kept on purpose; migration removed | [PR #15384] [PR #15385] | 7.0 / 6.0.5 |
| **Migration lifecycle** | | | |
| 4.4→5 upgrade broke forms after old-migration cleanup | Only previous-major migrations are deleted | [PR #13183] | 5.0.1 |
| **Updater and release metadata** | | | |
| "No session available" in `FinalizeUpdateStep` from the CLI | Updater works without a session | [PR #14681] | 6.0 |
| 4.3.0-beta offered to production instances | Pre-releases offered only when `update_stability` allows | [PR #11172] | 4.3 |
| `mautic:update:find` undefined-index notices | Missing metadata keys tolerated | [PR #9622] | 3.3 |
| 3.1→4.0-rc fatal: old files left behind | `deleted_files.txt` shipped and applied | [PR #10228] | 4.0 |
| Release workflow fails: tag 6.0.0 vs milestone 6.0.0-alpha | `version` includes the stability suffix | [PR #14507] | 6.0.0-alpha |

## 4. Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.0–1.4 | Idempotent migrations; `addons` → `plugins`; FK drop and re-add around column changes | [PR #261] [PR #809] [PR #1007] |
| 2.x | `IF NOT EXISTS` everywhere; 64-index guard; Doctrine-matching index names; performance indexes | [PR #5592] [PR #4193] [PR #5165] [PR #6092] |
| 3.0 | `release_metadata.json`; `doctrine:migrations:generate` with Mautic template; `SECURITY.md`; MySQL 5.7.14 | [PR #8429] [PR #8379] [PR #8394] |
| 3.2–3.3 | PHPStan on migrations; `show_php_version_warning_if_under` (optional key); signedness detection | [PR #9480] [PR #9622] [PR #9720] |
| 4.0 | `deleted_files.txt`; `minimum_mautic_version` 3.2.0 | [PR #10228] |
| 4.2.1 | Prefix applied once in generated names | [PR #10931] |
| 4.3 | Stability-suffixed versions; stability must match release type | [PR #10919] [PR #11172] |
| 4.4.9 | Pipedrive/Citrix deprecation notices created by migration | [PR #12364] [PR #12367] |
| 5.0 | 4.x migrations deleted; `mailer_dsn` and `project_dir` config migrations; private vulnerability reporting | [PR #12441] [PR #12526] [PR #12876] |
| 5.0.1–5.0.3 | Wrongly deleted migration restored; point-groups fixes; DSN `%` escaping | [PR #13183] [PR #13195] [PR #13284] [PR #13256] |
| 5.1 | Entity-plus-migration pair enforced in review | [PR #13413] |
| 5.2 | Template rewritten around `skipAssertion()`, `getPrefixedTableName()`, `down()` | [PR #13823] |
| 6.0 | CLI updater works without a session; all tables to `utf8mb4` | [PR #14681] [PR #14618] |
| 6.0.1 | Index existence checks fixed | [PR #14824] [PR #14852] |
| 7.0 | Citrix drop migration removed; `point_groups.uuid` migration; `MAINTAINERS.md`, `RELEASE_LEADS.md` | [PR #15384] [PR #15351] [PR #15004] |
| 7.2.0 | Skip-assertion AND semantics clarified; `mailer_dsn` never overwritten; API Library tests in core CI | [PR #16925] [PR #17227] |
| 7.2.1 | Release-prep only (`version`, `announcement_url`) | [PR #17504] |

## 5. Removed, deprecated, replaced

| What | Replaced by | PR | Version |
|---|---|---|---|
| Root `upgrade.php`, `upgrade_v3.php` | `mautic:update:find` / `mautic:update:apply` | [PR #9455] [PR #10228] | 3.x+ |
| `app/version.txt` | `app/release_metadata.json` | [PR #9029] | 3.0 |
| `mautic:migrations:generate` | `doctrine:migrations:generate` + `Migration.template` | [PR #8429] | 3.0 |
| `Doctrine\DBAL\Migrations\SkipMigrationException` | Doctrine Migrations 3 `SkipMigration` | [PR #9480] | 3.2.2 |
| 4.x migrations in `app/migrations` | Schema from entities; upgrade from ≥ 4.4.10 | [PR #12441] | 5.0 |
| `Version20230522141144` (drop `plugin_citrix_events`) | Nothing; table kept, drop by hand | [PR #15384] [PR #15385] | 7.0 / 6.0.5 |
| `ip_addresses` null-byte cleanup migration | Read-time handling | [PR #8664] | 3.0 |
| Production assets rebuilt in release PRs | `release_metadata.json`-only release PRs | [PR #13633] [PR #12517] | 5.0 |
| Scaffolded build files in Composer packages | Monorepo-only development | [PR #12522] | 5.0 |
| huntr.dev reporting | GitHub private vulnerability reporting | [PR #12876] [PR #12877] | 5.0 / 4.4.11 |
| Supported-version tables in README/SECURITY.md | mautic.org releases page | [PR #12876] [PR #15115] | 5.0 / 7.0 |
| Manual API Library runs before release | API Library tests in core CI | [PR #17227] | 7.2.0 |

## 6. Maintainer norms for this area

- Reviewers block entity changes without a migration and migrations without the entity change; maintainers sometimes add the missing migration themselves [PR #2971] [PR #6086] [PR #13413] [PR #15351] [PR #3858] [PR #9204].
- Test a migration on a database without the change, again after deleting its row from the migrations table (to see the skip), on a fresh install, and with a table prefix [PR #1478] [PR #5165] [PR #5898] [PR #8661] [PR #10233].
- Migrations are rarely unit-tested ("None, as migrations aren't tested"); testing is `doctrine:migrations:migrate`, `doctrine:migrations:execute --up/--down` and `--dry-run` against an older or real database [PR #13823] [PR #13195] [PR #14170]. [PR #16759] added a unit test and is the model to copy.
- Index PRs need EXPLAIN output and measurements on large datasets; redundant composite indexes are rejected without production evidence [PR #14556] [PR #15015] [PR #16759] [PR #7082].
- Prefer keeping unused tables over data loss [PR #15384].
- Release-prep PRs touch only `release_metadata.json`, match the milestone name and need an approval [PR #14507] [PR #15630] [PR #17227].
- One source of truth for supported versions (mautic.org) [PR #12876] [PR #15004].

## 7. Open questions

- **Migrations in patch releases.** [PR #9542] was moved from the 3.2 patch branch to the feature branch "since this contains a migration"; [PR #9510] allowed one in a patch "as a bug fix". No written rule exists in the 7.x PR template, `AGENTS.md`/`.agents/skills/mautic-dev`, the `UPGRADE-*.md` files or devdocs [code: .github/PULL_REQUEST_TEMPLATE.md @7.x]. Tag evidence: 5.0.1–5.0.4 added 2 migrations (the restore of [PR #13183]) and 5.1.1 added 1 ([PR #13915]); 5.2.x, 6.0.x, 7.0.x, 7.1.x and 7.2.1 added none, although 6.0.1 edited existing ones [PR #14824] [code: git diff --diff-filter=A <x.y.0> <x.y.z> -- app/migrations @7.x]. Practice since 5.2: new migrations land in minors; fixes to existing migrations land in patches.
- **Squash at every major?** [PR #12441] says migrations were deleted at 4.0 and 5.0. The tree shows no deletions at 4.0, 6.0 or 7.0 (only the Citrix file at 7.0) [code: git diff --diff-filter=D 3.3.5 4.0.0; 5.2.0 6.0.0; 6.0.0 7.0.0 -- app/migrations @7.x]. Whether 8.0 will squash 5.x–7.x migrations is not decided in the inputs.
- **Minimum source version.** Chunk notes infer "upgrade to a new major only from the last minor of the previous major" [PR #12441]. behaviour.md (code-verified) wins: 7.x accepts any source ≥ 5.0.0, and 5.0 accepted ≥ 4.4.10 [code: app/release_metadata.json @7.x].
- **Editing merged migrations.** In-place edits were common [PR #5165] [PR #8661] [PR #14824]; the argument for corrective new migrations [PR #5165] was never made policy.
- **`down()` policy** is unwritten: requested by some reviewers, waived for indexes by others [PR #12305] [PR #16548].
- **Install fixtures for non-Doctrine indexes** [PR #6864] [PR #9510]: unclear whether this dual path survives in 7.x.
- **`up()`/`down()` visibility** stayed `public` despite the 6.x plan [PR #13823] [code: app/bundles/CoreBundle/Doctrine/AbstractMauticMigration.php:45-64 @7.x].
- **[PR #11371]** merged to 4.x with a 5.0 milestone; the 4.x migrations it fixed were then deleted [PR #12441], so its fixes may never have reached a 4.4 user.
- **[PR #14433]** backfills `leads.date_added` from `date_modified` as a best guess; whether other tables got the same backfill is not stated.

## 8. Coverage

- 214 PRs across 2 chunks: 109 in chunk 1 (2015-03 to 2022-10, 101 substantive) and 105 in chunk 2 (2022-03 to 2026-10, 62 substantive, 34 routine release bumps used only as release-process evidence, 9 noise) [PR #113] [PR #17821].
- About 20 PRs are product features or bug fixes that sit in this area only because they carry a migration; section 2.12 lists them as migration examples [PR #3858] [PR #16363].
- 869 noise PRs (dependency bumps, CI, translations and similar) were excluded upstream before chunking [unverified] (harvest count, not a code fact).
