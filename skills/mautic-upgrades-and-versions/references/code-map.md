# Code map: update system, release metadata, migrations wiring, upgrade notes (7.x)

All paths relative to the repository root at 7.2.1 unless marked @8.x.

## Updater (CLI)

| Concern | Path | Notes |
|---|---|---|
| Apply command | `app/bundles/CoreBundle/Command/ApplyUpdatesCommand.php` | `mautic:update:apply` `--force`, `--update-package`/`-p`, `--finish`; `composer_updates` guard :84-88; hard `exit()` :92-99 [code: app/bundles/CoreBundle/Command/ApplyUpdatesCommand.php @7.x] |
| Find command | `app/bundles/CoreBundle/Command/FindUpdatesCommand.php` | `mautic:update:find`; always returns 0 [code: FindUpdatesCommand.php @7.x] |
| Step provider | `app/bundles/CoreBundle/Update/StepProvider.php` | Collects `mautic.update_step` services; splits initial/final by `shouldExecuteInFinalStage()`; sorts by `getOrder()` [code: StepProvider.php:22-60 @7.x] |
| Step interface | `app/bundles/CoreBundle/Update/Step/StepInterface.php` | `getOrder(): int`, `shouldExecuteInFinalStage(): bool`, `execute(ProgressBar, InputInterface, OutputInterface): void` [code: StepInterface.php @7.x]; 8.x adds native return types [code: UPGRADE-8.0.md @8.x] |
| Steps | `app/bundles/CoreBundle/Update/Step/{PreUpdateChecksStep(0),InstallNewFilesStep(10),RemoveDeletedFilesStep(20),DeleteCacheStep(30),UpdateTranslationsStep(40),UpdateSchemaStep(50),FinalizeUpdateStep(60)}.php` | Tags at `app/bundles/CoreBundle/Config/services.php:243-265` [code: services.php @7.x] |
| Update helper | `app/bundles/CoreBundle/Helper/UpdateHelper.php` | `fetchData($overrideCache)`, `fetchPackage($url)`, `runPreUpdateChecks()`, stats POST; cache file `lastUpdateCheck.txt` [code: UpdateHelper.php @7.x] |
| GitHub release parsing | `app/bundles/CoreBundle/Helper/Update/Github/{ReleaseParser,Release}.php` | First compatible release; `update.zip` asset [code: ReleaseParser.php:25-86 @7.x] |
| Pre-update checks | `app/bundles/CoreBundle/Helper/PreUpdateCheckHelper.php`, `Helper/Update/PreUpdateChecks/{AbstractPreUpdateCheck,CheckPhpVersion,CheckDatabaseDriverAndVersion}.php` | Tag `mautic.update_check` (`services.php:268,271`) [code: PreUpdateCheckHelper.php:20-27 @7.x] |
| Exceptions | `app/bundles/CoreBundle/Helper/Update/Exception/` | `UpdateFailedException`, `UpdatePackageNotFoundException` [code: app/bundles/CoreBundle/Helper/Update/Exception/ @7.x] |
| In-app notice | `app/bundles/CoreBundle/Model/NotificationModel.php:168-203` | Admin-only update notification [code: NotificationModel.php @7.x] |
| Browser updater | `app/bundles/CoreBundle/Controller/UpdateController.php` — **removed in 7.0.0** (present through 6.0.x, with route `/s/update/schema`) | [code: git ls-tree 6.0.0 / 7.0.0] |

## Release metadata

| Concern | Path | Notes |
|---|---|---|
| Metadata file | `app/release_metadata.json` | version, stability, PHP min/max, MySQL/MariaDB min, `minimum_mautic_version`, `announcement_url` [code: app/release_metadata.json @7.x] |
| Value object | `app/bundles/CoreBundle/Release/Metadata.php` | `final readonly`; version regex `#^(\d+)\.(\d+)\.(\d+)[\. \-]?(.*+)?$#` [code: Metadata.php @7.x] |
| Reader | `app/bundles/CoreBundle/Release/ThisRelease.php` | `ThisRelease::getMetadata()` [code: ThisRelease.php @7.x] |
| Version constant | `app/AppKernel.php:41-44` | defines `MAUTIC_VERSION` [code: app/AppKernel.php @7.x] |
| Plugin min version | `app/AppKernel.php:175-181` | `MINIMUM_MAUTIC_VERSION` on plugin bundle class [code: app/AppKernel.php @7.x] |
| Release workflow | `.github/workflows/release.yml:38-47` | tag must equal metadata `version` [code: release.yml @7.x] |
| Release notes grouping | `.github/release.yml` | label → section [code: .github/release.yml @7.x] |

## Migrations wiring (detail in mautic-architecture / mautic-contributing)

| Concern | Path | Notes |
|---|---|---|
| Doctrine migrations config | `app/config/config.php:225-236` | namespace `Mautic\Migrations`, dir `app/migrations`, template `app/migrations/Migration.template` [code: app/config/config.php @7.x] |
| Migration table name | `app/bundles/CoreBundle/Loader/EnvVars/MigrationsEnvVars.php:14` | `<db_table_prefix>migrations` [code: MigrationsEnvVars.php @7.x] |
| Base classes | `app/bundles/CoreBundle/Doctrine/{AbstractMauticMigration,PreUpAssertionMigration,MigrationFactoryDecorator}.php` | prefix + container injection; skip-when-all-assertions-true [code: PreUpAssertionMigration.php:26-45 @7.x] |
| Post-migrate generated columns | `app/bundles/CoreBundle/EventListener/MigrationCommandSubscriber.php:28-75` | runs on `doctrine:migrations:migrate` terminate [code: MigrationCommandSubscriber.php @7.x] |
| Installer marks migrations | `app/bundles/InstallBundle/Install/InstallService.php:528-547` | `sync-metadata-storage` + `version --add --all` [code: InstallService.php @7.x] |
| Plugin migrations | `Mautic\IntegrationsBundle\Migration\{Engine,AbstractMigration}` | plugin `Migrations/Version_X_Y_Z.php` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/database.html#plugin-schema-migrations] |
| 8.x only new migration | `app/migrations/Version20260814141635.php` @8.x | drops `forms.form_type` [PR #17082] |

## Configuration parameters

| Parameter | Default | Effect | Source |
|---|---|---|---|
| `update_stability` | `stable` | lowest stability offered (`alpha`/`beta`/`rc`/`stable`) | [code: app/bundles/CoreBundle/Config/config.php:296 @7.x] |
| `system_update_url` | `https://api.github.com/repos/mautic/mautic/releases` | release list; empty disables checks | [code: config.php:720 @7.x] |
| `stats_update_url` | `https://updates.mautic.org/stats/send` | anonymous stats; empty disables | [code: config.php:718 @7.x] |
| `install_source` | `Mautic` | sent in stats; part of instance id | [code: config.php:719 @7.x] |
| `composer_updates` | `false` | `true` makes `mautic:update:apply` refuse to run | [code: config.php:807 @7.x] |
| `translations_list_url` / `translations_fetch_url` | `https://language-packs.mautic.com/manifest.json` / `https://language-packs.mautic.com/` | language packs refreshed in step 40 | [code: config.php:716-717 @7.x] |
| `db_table_prefix` | install-time | injected into migrations as `$this->prefix` | [code: MigrationFactoryDecorator.php:27-35 @7.x] |

## Extension points

| Hook | How | Source |
|---|---|---|
| Custom update step | implement `Mautic\CoreBundle\Update\Step\StepInterface`, tag `mautic.update_step`, pick an order relative to 0/10/20/30 (initial) or 40/50/60 (final) | [code: StepProvider.php:22-30 @7.x] |
| Custom pre-update check | extend `AbstractPreUpdateCheck`, return `PreUpdateCheckResult`, tag `mautic.update_check` | [code: PreUpdateCheckHelper.php:20-27 @7.x] |
| Plugin install/update | 7.x: `PluginEvents::ON_PLUGIN_INSTALL` / `ON_PLUGIN_UPDATE`; 8.x: `PluginInstallEvent::class` / `PluginUpdateEvent::class` | [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/installation.html#install-and-update-events] |
| 7.x pre/post upgrade events | `CoreEvents::PRE_UPGRADE` / `POST_UPGRADE` existed but were unused; removed on 8.x with `CoreBundle\Event\UpgradeEvent` | [PR #17183] |

## Upgrade notes in the repository

| File | Covers |
|---|---|
| `UPGRADE-3.0.md`, `UPGRADE-4.0.md`, `UPGRADE-4.3.md`, `UPGRADE-5.0.md`, `UPGRADE-6.0.md`, `UPGRADE-7.0.md` | major BC breaks [code: repository root @7.x] |
| `UPGRADE-PHP-TO-TWIG-TEMPLATES.md` | template migration [code: repository root @7.x] |
| `UPGRADE-8.0.md` @8.x | 7 → 8 BC breaks (internally inconsistent; code wins) [code: UPGRADE-8.0.md @8.x] |
| `SECURITY.md`, `RELEASE_LEADS.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/BUG-REPORT.yml` | support, release leads, branch rules [code: repository root @7.x] |

## Tests

| Test | What it covers |
|---|---|
| `app/bundles/CoreBundle/Tests/Unit/Update/StepProviderTest.php` | step split and ordering |
| `app/bundles/CoreBundle/Tests/Unit/Update/Step/*Test.php` (base `AbstractStepTestCase.php`) | each step, incl. `PreUpdateChecksStepTest`, `InstallNewFilesStepTest`, `RemoveDeletedFilesStepTest`, `UpdateSchemaStepTest`, `FinalizeUpdateStepTest`, `UpdateTranslationsStepTest` |
| `app/bundles/CoreBundle/Tests/Unit/Helper/UpdateHelperTest.php` | caching (:145,181,217), stats (:253-500), disabled URL (:782), pre-update checks (:826,851) |
| `app/bundles/CoreBundle/Tests/Unit/Helper/Update/Github/ReleaseParserTest.php` | release selection (:58-122) |
| `app/bundles/CoreBundle/Tests/Unit/Helper/Update/PreUpdateChecks/{CheckPhpVersionTest,CheckDatabaseDriverAndVersionTest}.php` | platform checks |
| `app/bundles/CoreBundle/Tests/Unit/Release/MetadataTest.php` | metadata parsing |
| `app/bundles/CoreBundle/Tests/Unit/Doctrine/PreUpAssertionMigrationTest.php`, `CampaignLeadEventLogIndexMigrationTest.php` | migration skip semantics; unit-testing a concrete migration |
| `app/bundles/CoreBundle/Tests/{Unit,Functional}/EventListener/MigrationCommandSubscriberTest.php` | generated columns after migrate |

[code: app/bundles/CoreBundle/Tests/ @7.x]
