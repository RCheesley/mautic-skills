# Mautic contributing: PR history and maintainer norms

## Contents
1. How to read this file
2. Branch and release policy
3. Backward compatibility and deprecation
4. Review and merge rules
5. Testing requirements
6. Tooling, code style and static analysis
7. Schema and migration rules
8. Documentation requirements
9. Translations and wording
10. Cross-cutting review criteria (security, performance, scope)
11. Community process
12. PR template and repository-file evolution
13. Conflicts: norms that changed over time
14. Open questions
15. Coverage

## 1. How to read this file
- Source: merged pull requests on mautic/mautic, harvested 2026-10-15, read through the maintainer-norms sections of
  every other skill's `pr-history.md`, the architecture PR digests and the docs/community chunk notes. [PR #17459]
- Versions are inferred from base branch and merge date; "(~x.y)" means the release that first carried the PR. Dates
  in section 13 are merge-commit dates in the 7.x history. [PR #876] [code: git log @7.x]
- For a current rule, the 7.x PR template, `.github/CONTRIBUTING.md` and behaviour.md win; this file explains why and
  when the rule arose. [code: .github/PULL_REQUEST_TEMPLATE.md @7.x] [code: .github/CONTRIBUTING.md @7.x]

## 2. Branch and release policy

### Which branch
- Current rule: bug fixes go to the patch branch `a.b` (now `7.2`), features and enhancements to `a.x` (now `7.x`), BC
  breaks to the next major `c.x` (now `8.x`). [code: .github/PULL_REQUEST_TEMPLATE.md:1-11,21-24 @7.x]
  The template rule dates from late 2021. [PR #10589] [PR #10722] [PR #10802] [PR #12242] [PR #13989]
  It is applied in every area. [PR #12835] [PR #13921] [PR #16104] [PR #17300] [PR #17680] [PR #12922] [PR #13478]
  [PR #16476] [PR #7432] [PR #14909] [PR #17129] [PR #9096] [PR #14361]
- Fix against the oldest maintained patch branch where the bug applies (5.0, 5.1, 5.2, 7.0, 7.1, 7.2 in turn).
  [PR #13182] [PR #13877] [PR #14333] [PR #14397] [PR #14372] [PR #15600] [code: .github/PULL_REQUEST_TEMPLATE.md:33-34 @7.x]
- A fix to a feature that landed in a minor targets that same minor's branch. [PR #13105]
- Rector and refactor PRs (final classes, autowiring) go to the next minor, not the patch branch. [PR #16157] [PR #16800] [PR #16897]
- After `x.y.0` ships, `x.y` takes patches and `x.x` takes the next minor; when a patch line ends (7.1 after 7.1.3),
  retarget open PRs to `7.x`. [PR #16487] [PR #16877]
- Once a major enters beta or RC it is closed to features; they move to the next line (6.0 → 7.x). [PR #14657] [PR #14668] [PR #14745]
- While a minor is being finalised, enhancements are redirected to the next one (5.x → 5.1). [PR #12824] (v5.1)
- A feature merged into a bug-fix branch is flagged for revert. [PR #10668] [PR #8922] [PR #14982] [PR #16245]
- Exceptions need release-team agreement: a fix bundled with an improvement in 5.2.1 [PR #14353]; PHP 8.5 support after
  the 7.1.0 RC [PR #15721].
- Contributors use personal forks. [PR #10722] Contributors do not set milestones; maintainers set them on merge. [PR #13825] [PR #14646]
- Mirror repositories (core-lib, themes, plugins) are read-only and auto-close PRs; contribute to mautic/mautic.
  [PR #11354] (v5.0) [PR #9925] [PR #11154]

### Merging between branches
- Release branches and tags are merged forward into `x` by maintainers, without moving dependencies backwards; the
  scaffold lock must be byte-identical to the root lock. [PR #8669] [PR #9601] [PR #15263] [PR #16486] [PR #17516]
- Merge-up PRs are titled "Merging fixes from X to 7.x". [PR #10904] [PR #16012] [PR #16071]
- 7.x is forward-merged into 8.x periodically. [PR #17281] [PR #16155]
- Branch-merge PRs may be force-merged and show up as no-op PRs in history. [PR #10460] [PR #11268] [PR #5231] [PR #8667]
- Fixes for a separate line (older major, or next major before a forward merge) are separate PRs, titled with the
  branch, for example `[6.0]` or `[5.2]`. [PR #15560] [PR #15561] [PR #9929] [PR #11885]
- CI, scaffolding and DDEV fixes go to every maintained branch as companion PRs. [PR #10597] [PR #11089] [PR #11969]
- Back-merges were not used in the 4.4/5.x era; see section 13. [PR #11775] [PR #13110]

### Releases
- Feature freezes are enforced; late features move to the next minor. [PR #3549] [PR #3819]
- No features in patch releases. [PR #7211] Default-value and behaviour changes do not go into patches either. [PR #14678] [PR #14790]
- A patch or minor on an old line stays close to previous behaviour; direction changes need Product team discussion. [PR #8337]
- A named release leader decides scope; failing CI blocks inclusion. [PR #8175] [PR #8809]
- A PR whose only effect is a PHP notice waits for the next minor rather than a hotfix. [PR #9622]
- PRs that still have conflicts near a release are dropped from the milestone. [PR #10722]
- Release-prep PRs touch only `app/release_metadata.json`, match the milestone name and need an approval. [PR #14507] [PR #15630] [PR #17227]
- Generated assets are rebuilt at release; release CI verifies them in update ZIPs. [PR #11887] [PR #12358] [PR #17300]
- Dev tools such as Rector are locked to a production tag before a release. [PR #16859]
- Updates are CLI-only from 7.0; large schema changes were already steered to the CLI. [PR #14689] [PR #7094]
- Release-process changes need a documented local test procedure. [PR #12796]

### End of life and supported versions
- After a major ships, the previous major gets no further fixes. [PR #9743] [PR #9749]
- April 2020: no more 2.x minor releases; features and fixes were rebased onto 3.x unless 2.x-only. [PR #7312] [PR #7933] [PR #8467]
- Supported versions have one source of truth, https://www.mautic.org/mautic-releases; the README table it replaced
  drifted. [PR #8368] (v2.16) [PR #12876] (v5.0) [PR #12877] (v4.4.11) [PR #15004]
- Supported platform versions are raised after asking the community, and the change is noted as BC in UPGRADE notes. [PR #8394] (v3.0)
- Patch releases keep platform promises made for that line (for example Apache 2.x). [PR #7976] (v2.16)

## 3. Backward compatibility and deprecation
- BC breaks land only in a major and are listed in `UPGRADE-<major>.md`. [PR #1713] [PR #9739] [PR #11041] [PR #12440]
  [PR #14887] [PR #12402] [PR #14689] [PR #15284] [code: UPGRADE-7.0.md @7.x]
- Removed methods and classes are listed in the UPGRADE file before approval. [PR #14144] [PR #14418]
- BC breaks carry the `bc-break` label. [PR #9886] [PR #11056] [PR #14219] [code: .github/release.yml @7.x]
- Removing deprecated API is itself a BC break, even when an earlier removal was promised. [PR #13110] [PR #13837] [PR #14896]
- Deprecate in a minor with the removal version stated; remove in the next major; removal PRs target `8.x`.
  [PR #2707] [PR #11037] [PR #11632] [PR #13066] [PR #16992] [PR #17031] [PR #16970]
- A minor may carry its own UPGRADE file for deprecations (`UPGRADE-4.3.md`); 7.1 and 7.2 have none. [code: UPGRADE-4.3.md @7.x]
- Moved classes keep deprecated aliases for type hints; moved service IDs keep aliases marked with `->deprecate()`.
  [PR #1185] [PR #1252] [PR #17251]
- Plugin compatibility counts as BC surface even for unadvertised extension points. [PR #1633] [PR #17251] [PR #740]
- Changing a shared interface or public signature is a BC break, including adding a native return type to a non-final
  public method. [PR #15481] [PR #15655] [PR #13842] [PR #13696]
- Add strict types to new APIs now, and make new classes (DTOs, events) `final`, because tightening later is a BC break. [PR #14503] [PR #13842]
- Changing only private methods is not a BC break. [PR #11232]
- Fixing code to match its documented interface contract is a bug fix, not a BC break. [PR #16772]
- A new option's default keeps the old behaviour; behaviour-changing options in a minor are opt-in.
  [PR #3549] [PR #6422] [PR #1319] [PR #1632] [PR #2259] [PR #8959] [PR #15554] [PR #15755] [PR #6132]
- Adapt code rather than rename stored user data, filter keys or identifiers; change the label, not the key.
  [PR #5548] [PR #6024] [PR #2118] [PR #3633]
- Response shapes are BC: keep `{}` versus `[]` even when fixing a 500. [PR #10724] [PR #7815]
- Embedded form markup, public Asset URLs and old embeds must keep working. [PR #8671] [PR #10726] [PR #905] [PR #15138] [PR #15776]
- A new Twig function used by themes is a BC break for those themes; they raise their `mautic/core-lib` constraint.
  [PR #14657] [PR #14302] [PR #14621] [PR #14649]
- Removing themes, tracking options or core plugins is a major-only BC break with an UPGRADE entry.
  [PR #12524] [PR #6701] [PR #8428] [PR #14974] [PR #17785]
- Plugins are deprecated for one release with front-end notices, then removed in the next major. [PR #12364] [PR #12367]
- Build tooling is not a BC break when plugins and themes consume only compiled output. [PR #16143]
- Large UI migrations ship a compatibility layer in a minor, migrate in stages and drop the layer in the next major. [PR #17767]
- UI-habit changes wait for a major. [PR #9895]
- A technically-BC change can go into a minor if it is rare, restorable through config and noted in release notes;
  a switch that undoes an unintended break can ship in a patch. [PR #3501] [PR #7482]
- A break is acceptable in a major beta if no known plugin uses the API. [PR #9886] [PR #11032]
- Symfony BC breaks already documented by Symfony are not repeated in Mautic's UPGRADE notes. [PR #12200]
- Dead code is removed in majors; untraceable code is removed rather than ported. [PR #11504] [PR #12022] [PR #11270]
- Vulnerable libraries still in use go behind an off-by-default flag before removal. [PR #12416]
- Security hardening that could break installs ships opt-in. [PR #15868]
- Exception, recorded: in 7.2.0 hundreds of classes were made `final` in a minor with no deprecation notice and no
  UPGRADE entry; "no children" was judged against core only. `final class` lines under `app/bundles` rose from 611 at
  7.1.3 to 2,856 at 7.2.0. [PR #16754] [PR #16755] [PR #16756] [PR #16883] [PR #16884] [PR #16894] [PR #16898]
  [PR #16885] [PR #16821] [PR #16888] [PR #16902] [code: git grep '^final class' 7.1.3 7.2.0 -- app/bundles @7.x]
- Working policy since then: extend through events, interfaces and decoration, not inheritance. [PR #14016] [PR #13812] [PR #14503] [PR #16886] [PR #16941]
- Classes extended or mocked by plugins were meant to stay open, and finalising changes stay open for plugin-developer
  feedback. [PR #16902] [PR #16603]

## 4. Review and merge rules
- Current labels: `code-review-passed`, `user-testing-passed`, `ready-to-commit`; `ready-to-commit` also triggers a
  coverage run. [PR #16337] [code: .github/workflows/coverage-check.yml:9-10 @7.x]
- T1 PRs need one code review and one user test, and the tester must not come from the submitter's organisation.
  [PR #13754] [PR #13873] [PR #13908] [PR #14732] [PR #14869] [PR #14953] [PR #15481]
- The author cannot approve their own PR (four-eyes rule). [PR #12128] [PR #12303]
- Merging needs an approver with write access; a comment is not an approval. [PR #13754] [PR #14869]
- Anything beyond a one- or two-line fix needs two approvals. [PR #16877]
- PRs that change only tests or CI merge with one approval on green CI; CI blockers may be self-merged.
  [PR #11045] [PR #12137] [PR #12765] [PR #13797] [PR #14499] [PR #15472]
- For CI-only changes, "if GH Actions are green then this works" is an accepted test plan. [PR #13791] [PR #14090]
- Readme and doc-only PRs need code review only, no testing. [PR #11354] [PR #12876] [PR #14806]
- Dependency bumps with no code change accept "a green CI is all we can test" when the PR pastes the command and lock output. [PR #15775] [PR #15814]
- Rector dead-code changes need two code reviews only. [PR #11232]
- Symfony-blocking refactors may merge with one approval, or untested, if the PR says so. [PR #11862] [PR #12140]
- Untestable changes merge after two weeks as ready-to-commit. [PR #12843]
- A revert that restores known-working behaviour can merge without separate testing. [PR #8653]
- Production evidence substitutes for a tester when nobody has the third-party account or a large data set.
  [PR #6383] [PR #7196] [PR #8949] [PR #10993] [PR #13208] [PR #15948] [PR #12530] [PR #15031] [PR #12131]
- Code that nobody can exercise in the UI (IntegrationsBundle, Custom Objects) has merged on code review plus PHPUnit
  tests. [PR #8590] [PR #11252] [PR #11657] [PR #13391] [PR #13484] [PR #15253]
- Small, clearly correct UI fixes may merge without tests, with follow-ups; reviewers may add the regression test themselves. [PR #14851] [PR #17609]
- Maintainers do not merge when testers cannot reproduce the problem or understand the feature. [PR #8969] [PR #15359]
- A PR with a pending change request is set to "pending feedback" and re-tested after code changes. [PR #10580]
- Changes under `app/bundles/ReportBundle/` need CODEOWNERS review. [PR #17099]
- Weakening sanitisation needs a security-team review. [PR #15165]
- Contributors sign the CLA; cla-bot enforces it from about August 2020. [PR #7211] [PR #8769] [PR #9121] [PR #9899] [PR #12242]
- New bugs found in a merged PR are reported as new issues, not on the merged PR. [PR #3311]
- A merged PR that breaks behaviour or depends on an unmerged PR is reverted rather than shipped half-working; prefer a
  forward fix when one is ready. [PR #6896] [PR #6849] [PR #13768] [PR #13902] [PR #8690] [PR #12303]
- A breaking API PR is fixed quickly or reverted, and a default change that fails the api-library tests is reverted.
  [PR #12774] [PR #10716] [PR #14678] [PR #14790]

## 5. Testing requirements
- Every change needs automated tests; functional tests through the real route or command are preferred.
  [PR #11644] [PR #11692] [PR #8345] [PR #14503] [PR #11999] [PR #14340] [PR #14714] [PR #16157] [PR #16066]
  [code: .github/PULL_REQUEST_TEMPLATE.md:25,32 @7.x]
- A bug fix includes a regression test that fails without the fix. [PR #15822] [PR #17188] [PR #17602] [PR #17627]
  [PR #7733] [PR #14967] [PR #17653] [PR #16202] [PR #17815] [PR #15160] [PR #17099] [PR #8541] [PR #15702] [PR #11125] [PR #17138]
- Tests assert behaviour, not only HTTP 200, and use negative controls. [PR #17602] [PR #16137] [PR #17627]
- New features need tests before they go into a minor; the release can wait. [PR #9103]
- New options need tests for both values. [PR #5728] Coverage must not drop. [PR #8605] [PR #11864]
- UI fixes get a Codeception Cest with Page and Step objects; builder flows are covered by acceptance tests.
  [PR #14750] [PR #14794] [PR #15914] [PR #11818] [PR #17604]
- JS changes need tests too; a feature that broke twice gets a regression test. [PR #17138] [PR #10734]
- Test public submissions as a guest; an admin session creates no Contact. [PR #5349]
- Search and filter tests go through the real search flow, not repository internals. [PR #17452]
- Tests clean up after themselves, revert schema changes even on failure, and do not depend on local instance state,
  filesystem order, external infrastructure or `MAUTIC_TABLE_PREFIX`. [PR #13590] [PR #14482] [PR #17517] [PR #9703]
  [PR #12068] [PR #11622] [PR #17214]
- Changing a test's meaning to make it pass is rejected; fix flaky tests by normalising runtime values, and prove a
  flakiness fix with repeated runs. [PR #9665] [PR #16134] [PR #14304] [PR #16724]
- Test style: `$this->assert*()`, static data providers with one `yield` per case, `static::getContainer()`, stubs rather
  than expectation-less mocks. [PR #16390] [PR #16496] [PR #16528] [PR #16552] [PR #13049] [PR #13290]
  [code: .github/prompts/write-test.prompt.md:17-23 @7.x]
- Pure event classes with no logic need no unit test. [PR #12734]
- API changes are checked against the mautic/api-library suite, which also gates big refactors and releases.
  [PR #4200] [PR #5018] [PR #11555] [PR #12213] [PR #12396] [PR #12412] [PR #14219] [PR #10708] [PR #15614]
- Plugin and integration changes are tested with a real plugin (a purpose-built test plugin or HelloWorld). [PR #14418] [PR #3310] [PR #9796]
- Re-test an earlier PR's matrix when a later fix changes its behaviour. [PR #5374]
- Testers run `mautic:assets:generate` and clear the browser cache before reporting UI bugs. [PR #14032] [PR #9568] [PR #9972]
- Installer and configuration changes are tested in prod mode. [PR #11142] [PR #11553] [PR #11557]
- Scaling claims need before/after SQL and timings on large data. [PR #11420] [PR #9944] [PR #10903] [PR #14556] [PR #16759]

## 6. Tooling, code style and static analysis
- PHPStan has run in CI since 2020; keep ignores minimal and never merge with PHPStan red. [PR #8295] [PR #8311] [PR #12225] [PR #9522]
- Fix new findings in the PR that bumps a tool, or regenerate the baseline. [PR #12302] [PR #12556] [PR #16615]
- Do not hide real bugs in the baseline; reduce it instead. [PR #16498] [PR #16516]
- Ignore a widely used new deprecation centrally in `phpstan.neon`; temporary ignores to unblock an upgrade carry a
  removal note. [PR #14495] [PR #12200]
- Satisfy PHPStan against the locked dependency version rather than widening return types. [PR #16487]
- Rector rules are enforced on future code as cumulative sets; heavy Rector sets stay out of CI. [PR #11576] [PR #12268] [PR #11537] [PR #13035]
- CI "rector" and "coding standard" failures block merging even for behaviour-neutral changes. [PR #16768]
- Mass refactors ship with their Rector or ECS rule and are split per area; do not apply big style refactors
  codebase-wide in one PR. [PR #16723] [PR #16843] [PR #16220] [PR #16396] [PR #16544] [PR #16716]
- Style rules from review: one promoted property per line, `: void`, `final` leaf commands, `declare(strict_types=1)`,
  no file-level docblocks, return early, `const`/`let` in JS. [PR #16466] [PR #16695] [PR #16885] [PR #10970]
  [PR #12940] [PR #16837] [PR #15119]
- Codecov and SonarCloud are advisory; a Codecov drop from removed code may be overridden. [PR #15532] [PR #16137] [PR #9339] [PR #11997]
- Keep `composer.lock` close to production and scope lock updates narrowly; never hand-edit composer files. [PR #16487] [PR #17392] [PR #1397]
- Lock framework and risky libraries to a minor (`~X.Y.0`); prefer moving forward to a fixed upstream over pinning. [PR #15705] [PR #15737] [PR #17343] [PR #15436] [PR #17370]
- Do not commit file-mode changes. [PR #8254]
- Commands run from composer hooks must not fail the build for non-essential work. [PR #16226] (v7.2)
- Builder `dist` files were committed until 7.2.0; since then they must not appear in PRs. [PR #10728] [PR #13610] [PR #16435] [PR #16480]
- Scaffolded root files change together with their copy in `app/assets/scaffold/files/`. [PR #10857] [PR #13309] [PR #14226]

## 7. Schema and migration rules
- Entity mapping and migration change together; reviewers block one without the other. [PR #2971] [PR #6086] [PR #13413] [PR #15351] [PR #3858] [PR #9204] [PR #1478] [PR #9837]
- A fix for new installs also repairs existing installs, through a migration or a code-side default. [PR #187] [PR #1963] [PR #2995] [PR #6410] [PR #8238]
- Fresh and upgraded schemas match, including `ON DELETE`, primary-key order and index names. [PR #3509] [PR #17454]
- New non-null columns need a database default. [PR #7326]
- Fixtures contain no DDL. [PR #10787] [PR #11058] [PR #11059]
- DDL does not run inside transactions. [PR #13249] [PR #14440]
- Test a migration on a database without the change, again after deleting its row (to see the skip), on a fresh
  install and with a table prefix. [PR #1478] [PR #5165] [PR #5898] [PR #8661] [PR #10233]
- Migrations are rarely unit-tested; [PR #16759] added one and is the model to copy. [PR #13823] [PR #13195] [PR #14170]
- Index PRs need EXPLAIN output and large-data measurements; redundant indexes are rejected without production evidence. [PR #14556] [PR #15015] [PR #16759] [PR #7082]
- Bound data migrations on big tables with index-friendly `WHERE` clauses. [PR #1036] [PR #6046] [PR #10116]
- Prefer keeping unused tables over data loss. [PR #15384]
- New entity properties need tested migrations and OpenAPI updates. [PR #15755] [PR #11917]
- New migrations go to minors; see section 13 for patch-release migrations. [PR #9542]
- Permission changes need a data migration of the stored bitwise. [PR #6963] [PR #6966]

## 8. Documentation requirements
- Features need a user-docs PR; developer-facing changes and new config options need a dev-docs or user-docs PR before
  merge. [PR #3093] [PR #6422] [PR #13373] [PR #13948] [PR #15868] [PR #12098] [PR #11474]
  [code: .github/PULL_REQUEST_TEMPLATE.md:26-27 @7.x]
- In 7.x Promptless drafts the docs PR after the code PR opens; the author must review it.
  [PR #16337] [PR #17281] [PR #15399] [PR #17041] [code: .github/PULL_REQUEST_TEMPLATE.md:13-17 @7.x]
- A complete PR description is needed for Promptless to draft a useful docs PR. [PR #17459]
- Reviewers chase missing docs after merge. [PR #9107] [PR #14724] [PR #9391]
- New tokens and behaviour changes also need help-modal entries. [PR #14114] [PR #14215] [PR #15897]
- Anything users must act on (moved config files, removed CLI options, library swaps, env changes) goes into
  `UPGRADE-<major>.md` and the developer docs before merge. [PR #11561] [PR #12216] [PR #11145] [PR #12206] [PR #12717] [PR #14883]
- Developer docs live at devdocs.mautic.org (repo `developer-documentation-new`); the REST API reference stayed on
  developer.mautic.org. [PR #14207] (v5.2) [code: .github/CONTRIBUTING.md:13-15 @7.x]
- Docs use link macros so a URL changes in one place. [PR #9899] (v4.0)
- Point to a single source of truth instead of copying content. [PR #9899] [PR #12876] [PR #8517] [PR #17459]

## 9. Translations and wording
- Edit only `en_US` INI files; CI pushes them to Transifex from the default branch, and other locales come back as
  language packs. [code: .github/workflows/transifex.yml:15-39 @7.x]
- Every user-visible string, including aria labels, must be translatable. [PR #15184] [PR #16877]
- Keep translation keys when wording changes. [PR #1643] [PR #17678]
- Strings live in the bundle that owns the feature. [PR #11450]
- No double quotes inside INI translation strings. [PR #14908]
- Wording: marketer-friendly labels, active voice, no links in tooltips, error messages that say how to fix the problem.
  [PR #611] [PR #13436] [PR #14891] [PR #12509] [PR #15327]
- Use the right entity name ("contact" not "user", "text message" not "SMS", "pre-defined dashboard" not "template").
  [PR #13658] [PR #17443] [PR #15763] [PR #13364]
- Wide terminology changes go to community consultation; user-facing names can go to a community vote. [PR #13502] [PR #11891]
- RCheesley reviews English and spelling in user-facing text. [PR #14207]
- Destructive confirmations state the irreversible consequence. [PR #16830] [PR #17448] [PR #17442] [PR #17447]
- Historical: bundled addon names dropped the word "Integration" (the only translations-bucket PR). [PR #476] (v1.1)

## 10. Cross-cutting review criteria (security, performance, scope)
- Security: never log credentials (mark `[REDACTED]`), never hardcode third-party keys, stay CSP-safe, never use `|raw`
  for user or plugin content, and show users API errors rather than exception messages. [PR #16137] [PR #14277]
  [PR #1077] [PR #5735] [PR #13535] [PR #3984] [PR #15989]
- Report vulnerabilities privately through GitHub's private vulnerability reporting, not huntr.dev. [PR #12876] (v5.0)
  [PR #12877] (v4.4.11) [code: SECURITY.md:27-36 @7.x]
- Privacy by default: no third-party calls by default even when that changes upgrade behaviour; hosted-only behaviour
  sits behind a flag that is off in community config. [PR #17781] [PR #16130] [PR #3279] [PR #3196]
- Performance: aggregate in SQL, avoid synchronous COUNTs on big tables (load over AJAX), batch large deletes, make
  choice lists scale. [PR #1169] [PR #5908] [PR #7162] [PR #7491] [PR #14770] [PR #10276] [PR #14414]
- Optional third-party services never crash the app; fail loudly on permanent errors and quietly on transient ones. [PR #16137] [PR #17188]
- Fix scope: fix shared bugs at the shared layer and every occurrence, fix the root cause, keep fixes minimal, and do not
  change code "solely based on a theory". [PR #4292] [PR #13252] [PR #16256] [PR #17146] [PR #7802]
- Before removing anything, grep for usages (including `plugins/`), add guard tests and remove every call site. [PR #12652] [PR #14463] [PR #15372] [PR #17671]
- Split large work into small single-purpose PRs and keep dependent PRs in draft; an incomplete feature may merge as a
  skeleton. [PR #12396] [PR #13624] [PR #13749] [PR #14462] [PR #15087] [PR #11598] [PR #15002]
- Prefer Symfony-documented options; core holds no bundle-specific logic; unused extension points are not merged without a real use. [PR #13536] [PR #14650]
- Third-party integrations do not belong in core; move them to the Marketplace. [PR #12081] [PR #12333] [PR #12147]
- Whether a niche feature belongs in core or a plugin is decided by the product team and community. [PR #15359]
- Accessibility (WCAG AA first) and dark-mode-safe theme variables are review criteria. [PR #13873] [PR #13887] [PR #14147] [PR #14276] [PR #15254]

## 11. Community process
- `.github/CONTRIBUTING.md` sets PR expectations and points to the Community Handbook and devdocs. [PR #876] (v1.2) [PR #14207]
  [code: .github/CONTRIBUTING.md:5-15 @7.x]
- New contributors are pointed to the Community Handbook (contribute.mautic.org) and L1 issues. [PR #8517] (v3.0)
- Contributors are credited with `@all-contributors please add @user for code|docs|review|user testing`; a manual change
  updates both `.all-contributorsrc` and `README.md`. [PR #11233] [PR #12675] [PR #13712] [PR #15536]
- AI-generated PRs are accepted with normal review and Copilot review, but must be flagged and reviewed carefully,
  especially release tooling. [PR #15660] [PR #15704]
- Agent guidance lives in `AGENTS.md` (`CLAUDE.md` and `GEMINI.md` point to it) and in `.agents/skills/`, force-added
  because `.gitignore` ignores dot-directories. [PR #15697] (v7.0) [PR #16226] [PR #17459]
- Agent guidance should be concise and link to existing docs rather than become a second manual. [PR #17459]
- Many 7.x features are "unforked" from downstream forks, upstreamed without needless indirection. [PR #15897] [PR #15995] [PR #16060] [PR #16870] [PR #17296] [PR #14666] [PR #15056]
- The repo root carries `funding.json` for FLOSS Fund applications. [PR #14206] (v5.2)
- GitHub Codespaces with DDEV is the one-click PR test environment. [PR #15515] (v5.2.9) [PR #15521] [PR #16381] (v7.2)
  [code: .github/PULL_REQUEST_TEMPLATE.md:59 @7.x]

## 12. PR template and repository-file evolution
| Version | Change | PR |
|---|---|---|
| ~1.2 | CONTRIBUTING.md added with PR expectations | [PR #876] |
| ~1.2.1 | README explains how to test a PR (clone over HTTPS) [historical] | [PR #1032] [PR #1250] |
| ~2.8 | `composer test` alias | [PR #2347] [PR #3918] |
| ~2.9 | `composer test` needs a local `app/phpunit.xml` [historical] | [PR #4334] |
| ~2.16 | Supported-versions table in README | [PR #8368] |
| ~2.16 (2020-01) | Template asks for the "why" and steps to test written for novices | [PR #7845] |
| ~4.x (2021-11) | Template branch rule a.b / a.x / c.x | [PR #10589] [PR #10722] [PR #10802] |
| ~5.0 | README table replaced by mautic.org link; huntr.dev replaced by GitHub private reporting | [PR #12876] [PR #12877] |
| ~5.0 | Template rule reaffirmed from 5.x | [PR #12242] |
| ~5.0 (2024-01) | Step-by-step test instructions reinforced | [PR #13266] |
| ~5.2 | Devdocs moved to devdocs.mautic.org | [PR #14207] |
| ~6.0 | README rewritten | [PR #13989] |
| ~7.0 | `AGENTS.md` added | [PR #15697] |
| ~7.2 | Codespaces test link; Promptless docs PRs; review labels | [PR #16381] [PR #16337] |
| 7.3 (unreleased) | `.agents/skills/mautic-dev` skill | [PR #17459] |
- The template's hidden comment still says features go to "4.x"; the table above it is current. [code: .github/PULL_REQUEST_TEMPLATE.md:30-36 @7.x]

## 13. Conflicts: norms that changed over time
- **Back-merges versus a PR per branch.** 1.x–2.x: everything went to `staging`, released through `Release x.y.z` PRs
  to `master` and back-merged [PR #6531] [PR #7744] (patch branches from 2.15.2 [PR #7572]). 4.4/5.x era (about
  2022–2023): fix 5.x first, then a duplicate backport PR; "no back-merges, each branch needs its own PR" [PR #9516]
  [PR #11644] [PR #11676] [PR #11685] [PR #11714] [PR #11775] [PR #11857]. 2024-01: classic branching with merge-up
  restored [PR #13110]. Current: one PR against the lowest maintained `a.b`, merged up; separate PRs only for other
  lines (older majors, CI companions, the next major before a forward merge) [PR #15754] [PR #15867] [PR #13921]
  [code: .github/PULL_REQUEST_TEMPLATE.md:33-34 @7.x].
- **Approval count.** Early: two positive tests [PR #1437] [PR #5374]. 2018-11: two tests, or one test plus a code review
  [PR #6828]. 2020-09: T1/T2 tiers, a core review plus a tester from another company [PR #9108] [PR #9053]. 2023-07: the
  author cannot approve [PR #12128]. 2026-08/09: labels, and two approvals beyond trivial fixes [PR #16337] [PR #16877]. The KB
  still says "two testers" [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html].
- **The 7.2.0 `final` sweep versus the minor-release BC rule.** [PR #13842] treats subclass-breaking changes as
  major-only, and [PR #16323] asked to keep typing changes off extensible classes; weeks later 7.2.0 finalised about
  2,200 more classes with no UPGRADE note. [PR #16754] [PR #16898] [PR #16888] [PR #16902] Record it as an exception, not
  a new rule. [code: UPGRADE-7.0.md @7.x]
- **Public signature changes in a minor.** [PR #16980] changed `UserModel::checkNewPassword()` and `resetPassword()`
  between 7.1.0 and 7.2.0 without deprecation. [code: app/bundles/UserBundle/Model/UserModel.php:110,236 @7.x]
- **Coding standard.** ECS was rejected for php-cs-fixer in 5.x (2023-12) [PR #13037]; ECS rules reappeared in 7.2 (2026-06) [PR #16344]
  [PR #16723]. CI on 7.x checks changed files with php-cs-fixer only.
  [code: .github/workflows/tests.yml:256-264 @7.x]
- **Coverage.** The template says every PR must maintain or improve coverage [code: .github/PULL_REQUEST_TEMPLATE.md:25 @7.x],
  and reviewers have blocked drops [PR #8605] [PR #11864]; yet Codecov and Sonar are treated as advisory and drops
  from removed code are overridden [PR #15532] [PR #16137] [PR #9339] [PR #11997].
- **Migrations in patch releases.** [PR #9542] (2021-07) was moved off the 3.2 patch branch "since this contains a
  migration"; [PR #9510] (2021-03) allowed one in a patch as a bug fix. Practice since 5.2: new migrations in minors, fixes to existing
  migrations in patches [PR #14824]. No written rule. [code: .github/PULL_REQUEST_TEMPLATE.md @7.x]
- **Defaults on upgrade.** The norm is "a new default keeps old behaviour" [PR #3549] [PR #6422]; privacy and security
  work deliberately changes behaviour on upgrade [PR #17781] [PR #16870] [PR #10845], and PII-reducing defaults must
  keep existing installs working through a migration [PR #16954].
- **PHPStan baseline.** "Regenerate the baseline" after a tool bump [PR #12302] versus "do not hide bugs in the
  baseline" [PR #16498] [PR #16516]. Current practice: regenerate for tool noise, fix real bugs.
- **Builder dist files.** Committed and rebuilt after rebase until 7.2.0; forbidden in PRs since 2026-07. [PR #10728] [PR #16435]
- **Builder fixes location.** In `grapesjs-preset-mautic` with a core bump until 7.2.0; directly in mautic/mautic since. [PR #13665] [PR #16436]
- **Security reporting URL.** huntr.dev until 5.0, then GitHub private reporting [PR #12876]; `.github/CONTRIBUTING.md`
  still links a mautic.org page. [code: .github/CONTRIBUTING.md:3 @7.x] [code: SECURITY.md:32 @7.x]
- **String service IDs.** [PR #11587] planned to drop them in Mautic 6; 7.2 deprecated only 19 aliases, with no removal
  version. [PR #17251] [code: app/bundles/CoreBundle/Config/services.php:342-354 @7.x]

## 14. Open questions
- Were the classes finalised in 7.2.0 meant to have an UPGRADE note, and how was third-party extension assessed? [PR #16754] [PR #16885] [PR #16821] [PR #16902]
- Is `UserModel` internal, which would make [PR #16980] consistent with the minor-release BC rule? [PR #16980]
- When will the 7.2-deprecated string service aliases, and the 207 undeprecated ones, be removed? [PR #11587] [PR #17251]
- No written rule on migrations in patch releases, on editing merged migrations, or on `down()`. [PR #9542] [PR #9510] [PR #5165] [PR #12305] [PR #16548]
- No agreed `SYMFONY_DEPRECATIONS_HELPER` level; Codeception silences deprecations while PHPUnit aims for zero. [PR #13150] [PR #14061] [PR #15280]
- Did [PR #4063] break a third-party SSO plugin as a core BC break? Never settled. [PR #4063]
- Should skills live in core or a separate repo? Left open by patrykgruszka. [PR #17459]
- The security, PII and data-handling section RCheesley requested for `AGENTS.md` was deferred at merge. [PR #15697]
- Should README usage content move to user docs? Raised, not resolved. [PR #3519]
- When DDEV moves to a new PHP version is not a stated policy. [PR #12467]

## 15. Coverage
- Inputs: the maintainer-norms and open-question sections of 21 skill `pr-history.md` files (mautic-contacts,
  mautic-overview and mautic-troubleshooting had none at harvest time), architecture digests A and B section 4, and the misc chunk (49 docs/community PRs, 45
  uncategorised, 1 translations). [PR #476] [PR #17459]
- Of the misc chunk, 65 PRs were substantive, 28 noise and 7 routed to the queue notes; 869 noise PRs were excluded upstream. [PR #105] [PR #13111]
