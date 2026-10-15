# Docs digest: updating, upgrading and versions

What docs.mautic.org (7.2), devdocs.mautic.org (7.2 and 8.0) and kb.mautic.org say about updates, upgrades, staging and
version porting. Where docs disagree with 7.x code, the code behaviour is in [behaviour.md](behaviour.md) and the
discrepancy is listed in §6.

## 1. Updating Mautic (user docs)

Page: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html

- Two ways are documented: command line (recommended) and the browser. The CLI is strongly recommended for production, large or shared-hosting instances [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html].
- Always keep a tested backup: files and DB, restored in a test environment [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-at-the-command-line-non-composer-based-installations].
- Do not run update commands as root; on Apache/Linux run them as the web-server user (`sudo -u www-data`) [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#running-update-commands-as-the-web-server-user].
- Stability levels: "Minimum stability level" controls notifications for Alpha/Beta/RC; default stable; never enable early access on production [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#stability-levels] [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#update-settings].
- "Update Mautic through Composer [beta]" = Yes is a prerequisite for Marketplace installs/updates [docs: https://docs.mautic.org/en/7.2/configuration/settings.html#update-settings].
- Recommended permissions: files 644, directories 755, group-writable `var/cache`, `var/logs`, `app/config`, `media/files`, `media/images`, `translations` [docs: https://docs.mautic.org/en/7.2/troubleshooting/file_ownership_permissions.html#reset-the-file-and-folder-permissions].
- Ask for help on the Community Forums first, include steps, PHP version, from/to versions, errors from `var/logs` and server logs; GitHub only for confirmed bugs [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#what-to-do-if-you-need-help-updating-mautic].

## 2. Procedures

**Non-Composer CLI update** [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#installing-updates-at-the-command-line]
1. Take a tested backup.
2. `cd` to the Mautic directory as the web-server user.
3. `php bin/console mautic:update:find`; read the announcement.
4. `php bin/console mautic:update:apply`.
5. `php bin/console mautic:update:apply --finish`.
6. `php bin/console cache:clear`; fix permissions if needed.

**Composer-based update** [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-mautic-composer-based-installs]
1. Back up `composer.json` and `composer.lock`.
2. Bump every `mautic/*` version constraint.
3. `composer update --with-dependencies`.
4. `git diff` the scaffold files (`mautic/core-composer-scaffold` rewrites them when `mautic/core-lib` updates; a customised `.htaccess` may conflict) and restore customisations.
5. Commit in one commit.
6. `cache:clear`, `mautic:update:apply --finish`, `doctrine:migration:migrate --no-interaction`, `cache:clear`.
   Code check: with `composer_updates` = true, step 6's `mautic:update:apply --finish` is refused (see §6 item 1).

**Switch a ZIP install to Composer** (Mautic ≥ 4.0.0; codebase only, DB untouched) [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html]
- `composer create-project` into `html-new`; copy `local.php`, plugins, media files/images, dashboards, themes, translations into `docroot/...`; swap directories; point the web root at `docroot`; turn on the Composer setting.

**Recover a failed update** [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html]
- Clear cache (`cache:clear` or `rm -rf var/cache`); rerun `mautic:update:find` / `apply`; `doctrine:migration:status` then `doctrine:migration:migrate`; otherwise replace files by hand keeping `config/local.php` (pre-5.0: `app/config/local.php`), `media/files`, `plugins`, `themes`, `translations`.
- Without SSH, a PHP troubleshooting script (gist escopecz/9a1a0b10861941a457f4) can do most steps [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-isn-t-available].
- The docs also point to a schema check tool at `/s/update/schema` — this no longer exists in 7.x (§6) [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#checking-for-schema-updates].
- PHP errors: `Allowed memory size … exhausted` → raise `memory_limit`; `Class 'ZipArchive' not found` → install the zip extension [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#there-is-a-php-error-when-running-a-command].
- Resource-limit errors are server configuration, not Mautic bugs [docs: https://docs.mautic.org/en/7.2/troubleshooting/working_with_resource_limits.html].

## 3. Knowledge base articles

| Article | What it says | Status for 7.x |
|---|---|---|
| Understanding Migrations and Schema Update with Doctrine [kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html] | Migrations in `app/migrations`, recorded in the `migrations` table (prefixed in code); `doctrine:migrations:status` shows Executed / Available / New / "Executed Unavailable" (row with no file, rarely a problem); most migrations have no `down()`; recovery: rerun update → `doctrine:migrations:migrate` → `doctrine:schema:update --force` (`--dump-sql` to preview); last resort `--force --complete` (drops custom DB objects and the `migrations` table) then migrate; breaking DB changes only in majors | Concepts valid (2022, 3.x era) |
| How to set up a staging server to test new Mautic releases [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html] | Comment out crons before snapshotting; change vhost `ServerName` and `site_url`, then `cache:clear`; capture mail with MailHog (SMS and push are not captured); `update_stability` appears in `local.php` only after the config is first saved; run update, migrations and schema commands, then check System Info > Error Log | Outdated paths (`app/config/local.php`) and pre-5 commands; the clone-and-test approach still applies |
| Update from Mautic 4 to 5.1 (Softaculous) [kb: https://kb.mautic.org/article/update-from-mautic-4-to-5-1-when-installed-by-softaculous-quick-guide.html] | Keep `local.php`, replace files, `mautic:update:apply --finish`, clear cache, fix `.htaccess` and permissions, redo SMTP | Historical |
| Troubleshooting "The site is currently offline…" [kb: https://kb.mautic.org/article/troubleshooting-the-site-is-currently-offline-due-to-encountering-an-error-in-mautic.html] | Causes include PHP version mismatch, permissions, corrupted files or a failed update; check Mautic logs (`var/logs`) then web-server logs; stay within one minor release | Valid |
| How do I test bug fixes and new features [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] | Release cadence: bug fixes monthly, features quarterly, breaking changes about annually | 2025 |

## 4. Developer docs: porting guides

- **M4 → M5** [devdocs: https://devdocs.mautic.org/en/7.2/plugins/update_m4_to_m5.html]: add PHP 8.1/8.2 and Mautic 5.1 in CI; `local.php` moved to `config/`; verify wiring with `rm -rf var/cache && bin/console`; controllers become `Class::method`; PHP views to Twig (`@MauticCore/...html.twig`), check with `bin/console lint:twig plugins/MyBundle`; IntegrationsBundle expects service key `mautic.integration.[NAME]`; tests use `static::getContainer()`; run Rector, php-cs-fixer, PHPStan.
- **M7 → M8** (new in the 8.0 branch) [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]: type declarations added; the risk is signature mismatch (fatal `TypeError` or compile error); four break kinds (new parameter type, new return type, new property type, removed property); `CommonRepository`, `AbstractPermissions`, `AbstractIntegration`/`CrmAbstractIntegration`/`SocialIntegration`, controller and API controller signatures; per-bundle event/entity changes in 16 bundles; `FormController` removal with a `setStandardParameters()` mapping; protected controller helpers; nullable getters; `PluginIntegrationResponseEvent`; `MappingManualDAO` constructor; 300+ `final` classes and the `DG\BypassFinals` bootstrap; typed class constants. It does not cover PHP/Symfony/Doctrine versions or Twig/JS asset changes. Condensed in [upgrade-to-8.md](upgrade-to-8.md) §5 and §10.
- Plugin lifecycle: `ON_PLUGIN_INSTALL` / `ON_PLUGIN_UPDATE` since 4.2.0, no uninstall hook; on 8.0 subscribe to `PluginInstallEvent::class` / `PluginUpdateEvent::class` [devdocs: https://devdocs.mautic.org/en/7.2/plugins/installation.html] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/installation.html#install-and-update-events].

## 5. Changes in the 8.0 docs branches

Developer docs (33 changed files, 2 new) [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html]:
- New `plugins/update_m7_to_m8` and an xref `UPGRADE_GUIDE_8` → https://github.com/mautic/mautic/blob/8.x/UPGRADE-8.0.md.
- `plugins/event_listeners`: "Mautic 8 class-name event dispatch", `debug:event-dispatcher`, per-bundle mapping tables, all examples keyed on `::class`.
- `plugin_extensions/*`: examples switched to event classes with "Former constant → Mautic 8.0 subscription key" tables.
- `plugins/cache`: "Migrating to CacheBundle in Mautic 8" [devdocs: https://devdocs.mautic.org/en/8.0/plugins/cache.html#migrating-to-cachebundle-in-mautic-8].
- `plugins/config`: menus via `services.php`; `ConfigEvents` replaced [devdocs: https://devdocs.mautic.org/en/8.0/plugins/config.html].
- `plugins/mvc`, `plugins/permissions`, `plugins/database`, `plugin_services/{security,ip_lookups}`: FQCN services, constructor permissions, `getName()` model registration, Doctrine builders [devdocs: https://devdocs.mautic.org/en/8.0/plugins/mvc.html] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/permissions.html].
- `rest_api/forms`: `formType` removed [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/forms.html].
- `rest_api/companies` and `themes/getting_started` document unreleased 7.x features (after 7.2.1) not yet on 8.x code [PR #16512] [PR #16870].

User docs (12 files): mostly unreleased 7.x features merged after 7.2.1; the only 8-specific change is the `mautic:disable-tracking` removal
[docs: https://docs.mautic.org/en/8.0/channels/emails.html]. The update/getting-started pages are unchanged in 8.0
[docs: https://docs.mautic.org/en/8.0/].

## 6. Discrepancies between docs and 7.x code

1. Composer update procedure runs `mautic:update:apply --finish`, but the command returns FAILURE whenever `composer_updates` is true, before checking `--finish` [code: app/bundles/CoreBundle/Command/ApplyUpdatesCommand.php:84-88 @7.x] vs [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-mautic-composer-based-installs]. On such installs, run `doctrine:migrations:migrate` and `cache:clear` directly.
2. Docs say the browser updater was "completely removed" from 5.0 and still document "Updating in the browser". Code: `UpdateController` exists through 6.0.x and was removed in 7.0.0 [code: git ls-tree 6.0.0 / 7.0.0] [code: UPGRADE-7.0.md:9 @7.x] vs [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-in-the-browser].
3. The `/s/update/schema` schema check tool belonged to `UpdateController` and does not exist in 7.x [code: git show 6.0.0:app/bundles/CoreBundle/Config/config.php] vs [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#checking-for-schema-updates].
4. Docs disagree on when Composer became the default (5 vs 6) [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#checking-for-updates-at-the-command-line]. The setting tooltip still says "will be the default … in Mautic 5" and the label still says [BETA] [code: app/bundles/CoreBundle/Translations/en_US/messages.ini:230-231 @7.x].
5. Install page states PHP 7.4 minimum and `platform.php` "7.4"; 7.x requires 8.2.0–8.5.99 [code: app/release_metadata.json @7.x] vs [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#how-can-you-specify-a-php-version].
6. Recommended Project commands pin `mautic/recommended-project:^5` [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#using-the-recommended-project]; use the current major.
7. Marketplace listing example pins `"php": ">=8.0 <8.1"`, `"mautic/core-lib": "^5.0"` — stale for 7.x [devdocs: https://devdocs.mautic.org/en/7.2/marketplace/listing.html].
8. Devdocs 8.0 call `CompanyEvent`, `LeadListEvent`, `ListChangeEvent`, `WebhookEvent` `final`; 8.x code has three `abstract` and `ListChangeEvent` non-final [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html#affected-classes] [code: UPGRADE-8.0.md @8.x].
9. The KB staging article uses `app/config/local.php`; since 5.0 the file is `config/local.php` [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html] [code: app/migrations/Versionzz20230929183000.php @7.x].

## 7. Terminology

- Docs say "update" for moving within a major via the updater or Composer and "upgrade" in porting guides (`update_m7_to_m8`) and `UPGRADE-*.md` files; both are used loosely [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html].
- "Stability level": alpha, beta, rc (release candidate), stable [code: app/bundles/CoreBundle/Form/Type/ConfigType.php:553-558 @7.x].
