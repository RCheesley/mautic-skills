# Mautic contributing: version notes

## 1. History that explains current rules
- 3.0: `app/console` → `bin/console`; `app/version.txt` → `app/release_metadata.json`; updater switched to GitHub releases;
  `CommonSubscriber` removed (use DI). [code: UPGRADE-3.0.md @7.x]
- 4.0: Symfony 4, services private by default. [code: UPGRADE-4.0.md @7.x]
- 5.0: Symfony 5; autowiring/autoconfigure in `Config/services.php` (legacy `config.php` services slated for removal);
  local config moved from `app/config` to `config/`; JS dependencies via npm. [code: UPGRADE-5.0.md @7.x]
- 6.0: Symfony 6; `MauticFactory` removed; plugin schema via `PluginDatabase` and `PluginEvents`; functional-test API
  changes (`loginUser`, `assertResponseIsSuccessful`). [code: UPGRADE-6.0.md @7.x]
- 7.0: PHP 8.2, MySQL 8.4.0, MariaDB 10.11.0; browser-based updater removed (CLI only); many deprecated classes removed.
  [code: UPGRADE-7.0.md @7.x]

## 2. 7.x minors
- 7.0.0 (2026-01-20), 7.1.0 (2026-04-14), 7.2.0 (2026-09-02), 7.2.1 (2026-09-23). [code: git tag @7.x]
- Minors carry additive schema changes: 7.1.0 added 9 migrations, 7.2.0 added 13; 7.2.1 added none. [code: app/migrations/ @7.x]
- No `UPGRADE-7.1.md` or `UPGRADE-7.2.md` exists; minor-release notes are on GitHub releases, grouped by PR label.
  [code: .github/release.yml @7.x]
- Only 7.2.x is listed as supported in the bug form. [code: .github/ISSUE_TEMPLATE/BUG-REPORT.yml:24-41 @7.x]

## 3. The 8.x delta for contributors
| Area | 7.x | 8.x | Tag |
|---|---|---|---|
| PHP | 8.2–8.5 | 8.4 minimum | [PR #16993] [code: app/release_metadata.json @8.x] |
| Symfony | 7.4 | 8.1 | [PR #17392] |
| Doctrine | ORM 2.14 / DBAL 3.6 | ORM 3.7 / DBAL 4.4 | [PR #17361] |
| Entity mapping | `loadMetadata()` | moving to `#[ORM\*]` attributes (partial) | [PR #17382] [PR #17454] |
| Routes (core) | `Config/config.php` | native `#[Route]` attributes (plugins may keep `config.php` routes) | [PR #17169] [PR #17222] |
| Event dispatch | constant names | by event class; PHPStan enforces single-argument dispatch | [PR #17625] |
| PHPUnit | 11.5 | 13 (+ `dg/bypass-finals`) | [PR #17004] [PR #17366] |
| PHPStan | level 6, ~2040-entry baseline | level 6, more custom rules, rising type-coverage floors | [PR #17631] [PR #17766] |
| Rector | `dev-main` + type-perfect | `^2.6.5`, PHP 8.4 sets | [PR #17190] [PR #17498] |
| Coding standard | php-cs-fixer + ECS | ECS only | [PR #17280] [PR #17362] |
| Tool binaries | `bin/*` | `vendor/bin/*` | [PR #17164] |
| Classes | — | many more `final` classes; do not extend or mock them | [PR #17536] |

Notes:
- `app/release_metadata.json@8.x` still says 7.2.0; treat 8.x as unreleased development. [code: app/release_metadata.json @8.x]
- 7.x work since 7.2.0 (736 commits: the 7.2.1 release plus unreleased PRs merged after it) is not yet merged forward into 8.x; a 7.x fix is not on 8.x until the next forward merge.
  [PR #17253]
- `UPGRADE-8.0.md` is appended per PR and contradicts itself in places (for example constants described as "kept" that
  the code removed); prefer the code. [code: UPGRADE-8.0.md @8.x]

## 4. Writing code that lands on 7.x and survives 8.x
Avoid in new 7.x contributions: `*Events::CONST` subscriber keys or second `dispatch()` argument; `CacheStorageHelper`;
`Core\Controller\FormController`; `services`/`menus`/`models` arrays in `config.php`; string service ids; `Request::get()`;
`$this->_em` in repositories; Symfony constraint option arrays; Clearbit. Add native types to every override now.
[code: UPGRADE-8.0.md @8.x] (full list and dual-version subscriber pattern: mautic-upgrades-and-versions)
