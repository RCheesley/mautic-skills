# Version notes: Mautic development and test environment

## 1. History before 7.x (why things are the way they are)
| Version | What changed for dev and test setup | Source |
|---|---|---|
| 2.x → 3.0 | The console moved from `app/console` to `bin/console`, and logs from `app/logs` to `var/logs`. | [docs: https://docs.mautic.org/en/7.2/configuration/cron_jobs.html] [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html] |
| 4.0 | The config file moved from `app/config/local.php` to `config/local.php` (KB). The troubleshooting docs say "since 5.0", so the inputs disagree. 7.x code still reads the legacy path when the new one is missing. | [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html] [docs: https://docs.mautic.org/en/7.2/troubleshooting/troubleshooting.html#ssh-access-is-available] [code: app/bundles/CoreBundle/Loader/ParameterLoader.php:134-137 @7.x] |
| 4.0 | Composer install became available, and it is the minimum version for switching a ZIP install to Composer. | [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-composer] [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html] |
| 4.2 → 5.0 | The browser updater was deprecated in 4.2. The docs say it was removed in 5.0. | [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_update_mautic.html#updating-in-the-browser] |
| 5.0 | Composer became the default install and update method. | [docs: https://docs.mautic.org/en/7.2/getting_started/switching_composer.html] |
| 5.1 | A complex admin password became required. The DDEV default password changed from `mautic` to `Maut1cR0cks!`. | [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#install-mautic-using-ddev] [docs: https://docs.mautic.org/en/7.2/getting_started/how_to_install_mautic.html#installing-with-command-line] |
| 5.x (KB Ubuntu guide) | PHP 8.1, Node 20, `recommended-project:^5`. This is outdated for 7.x versions, but the Composer approach still holds. | [kb: https://kb.mautic.org/article/how-to-install-mautic-5-on-ubuntu-22-04-with-ssl-and-node-js-20.html] |

## 2. 7.x (authoritative: 7.x snapshot, release 7.2.1 plus unreleased merged PRs)
- The platform is PHP 8.2.0–8.5.99, MySQL 8.4.0 or later, or MariaDB 10.11.0 or later. The minimum version you can upgrade from is 5.0.0. [code: app/release_metadata.json:4-9 @7.x]
- Symfony is `~7.4.0`, Doctrine ORM `^2.14` and DBAL `<3.8`. [code: app/composer.json:15-105 @7.x]
- The UI uses `twbs/bootstrap` 5.3.8, compiled by `symfonycasts/sass-bundle` and served by Symfony AssetMapper through `importmap.php`. Webpack builds only CKEditor 5. [code: app/composer.json:15-105 @7.x] [code: importmap.php:3-12 @7.x] [code: webpack.config.js:28-37 @7.x]
- DDEV runs PHP 8.5, MariaDB 10.11 and Node 24. [code: .ddev/config.yaml:1-24 @7.x]
- Dev tool binaries are in `bin/` (`bin/phpunit`, `bin/phpstan`, `bin/rector`, `bin/codecept`). Code style uses php-cs-fixer plus ECS. Tests run on PHPUnit 11.5. [code: composer.json:28-56 @7.x] [code: composer.json:173-178 @7.x]
- `composer install` builds the GrapesJS assets without failing on errors, through `build/gjs_build.php`. [code: build/gjs_build.php:1-13 @7.x]
- Open question: the inputs do not separate dev-environment changes between 7.0, 7.1 and 7.2, and they record no change specific to 6.x. [unverified]

## 3. 8.x delta (unreleased; branch snapshot 2026-10-15)
| Item | 7.x | 8.x | Source |
|---|---|---|---|
| PHP minimum | 8.2 | 8.4 (max 8.5.99) | [code: app/release_metadata.json @8.x] [PR #16993] |
| Symfony | `~7.4.0` | `~8.1.0` | [code: app/composer.json @8.x] [PR #17392] |
| Doctrine ORM / DBAL | `^2.14` / `^3.6 <3.8` | `^3.7` / `^4.4` | [code: app/composer.json @8.x] [PR #17361] |
| PHPUnit | `^11.5` | `^13.0` | [code: composer.json @8.x] [PR #17004] |
| Tool binaries | `bin/*` | `vendor/bin/*` (composer scripts updated) | [code: composer.json @8.x] [PR #17164] |
| Code style | php-cs-fixer + ECS | ECS only; `.php-cs-fixer.php` deleted; pre-commit runs `vendor/bin/ecs` | [PR #17280] [PR #17362] |
| Test finals | — | `dg/bypass-finals` enabled in `app/tests/bootstrap.php` | [PR #17366] |
| Bootstrap | `twbs/bootstrap` 5.3.8 (7.x after 7.2.1, unreleased [PR #17767]; 7.2.1 ships `bootstrap-sass` 3.4.1) | still `twbs/bootstrap-sass` 3.4.1 until 7.x is merged forward; undecided | [code: composer.json @8.x] |
| DB minimums | MySQL 8.4 / MariaDB 10.11 | unchanged | [code: app/release_metadata.json @8.x] |
| Version string | 7.2.1 | `release_metadata.json` still says 7.2.0; treat 8.x as unreleased dev | [code: app/release_metadata.json @8.x] |

Consequences for a dev environment on 8.x:
- DDEV's PHP 8.5 already meets the 8.4 minimum. The inputs do not say whether `.ddev/config.yaml` changed on 8.x. [code: .ddev/config.yaml:3 @7.x]
- Commands documented as `bin/phpunit` or `bin/phpstan` become `vendor/bin/phpunit` and `vendor/bin/phpstan`. `composer test` and `composer phpstan` keep working because the scripts were updated. [PR #17164]
- `composer cs` and `composer fixcs` change meaning because php-cs-fixer is gone. Check `composer.json@8.x` scripts before you rely on them. [PR #17280]
- The developer-environment devdocs pages are unchanged in the 8.0 branch, so they say nothing about PHP 8.4. [devdocs: https://devdocs.mautic.org/en/8.0/]

Unreleased 7.x changes (merged after 7.2.1, not in any release yet): see [post-7.2.1-prs.md](../../mautic-upgrades-and-versions/references/post-7.2.1-prs.md).
