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

## 5. Process changes by version (from merged PRs)
Full history and conflicts: pr-history.md sections 12 and 13.

### Before 5.x
- 1.x–2.x: all work went to `staging`; releases were `Release x.y.z` PRs to `master`, back-merged afterwards. [PR #6531] [PR #7744]
- April 2020: no further 2.x minors; features and fixes rebased onto 3.x. [PR #7312] [PR #7933] [PR #8467]
- From about August 2020 cla-bot enforces the CLA. [PR #7211] [PR #8769]
- Late 2021: the PR template's a.b / a.x / c.x branch rule. [PR #10589] [PR #10722] [PR #10802]

### 5.x
- 4.4/5.x era: fix 5.x first, then a duplicate backport PR; no back-merges. [PR #11644] [PR #11676] [PR #11775] [PR #11857]
- January 2024: classic branching with merge-up restored. [PR #13110]
- 5.0 / 4.4.11: supported versions moved to mautic.org; security reports to GitHub private reporting. [PR #12876] [PR #12877]
- 5.x: php-cs-fixer chosen over ECS; heavy Rector sets kept out of CI. [PR #13037] [PR #13035]
- 5.2: developer docs moved to devdocs.mautic.org. [PR #14207]
- 5.2.9: GitHub Codespaces with DDEV for testing PRs. [PR #15515] [PR #15561]
- New migrations land in minors from 5.2; fixes to existing migrations may land in patches. [PR #9542] [PR #14824]

### 6.x
- 6.0 entered beta closed to features, which went to 7.x. [PR #14657] [PR #14668] [PR #14745]
- 6.0.7: Codespaces image backport as a separate `[6.0]` PR. [PR #15560]

### 7.0, 7.1, 7.2
- 7.0: updates are CLI-only; `AGENTS.md` added for coding agents. [PR #14689] [PR #15697]
- 7.1: PHP 8.5 support accepted after the 7.1.0 RC by release-team agreement; the 7.1 patch line ended after 7.1.3. [PR #15721] [PR #16877]
- 7.2: review labels and Promptless docs PRs; composer-hook commands must not fail the build. [PR #16337] [PR #16226]
- 7.2.0: builder `dist` files no longer committed; builder fixes go straight into mautic/mautic. [PR #16435] [PR #16436]
- 7.2.0: hundreds of classes made `final` in a minor without an UPGRADE note (recorded exception). [PR #16754] [PR #16898]
- 7.2.0: `UserModel` public signatures changed without deprecation. [PR #16980]
- 7.3 (unreleased): `.agents/skills/mautic-dev` added to core. [PR #17459]
