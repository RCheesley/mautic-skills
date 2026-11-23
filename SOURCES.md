# Sources and provenance

Every statement in this repository carries a citation tag. This file records what each tag points at and the
exact snapshots the content was derived from, so the repository can be regenerated or audited.

## Citation tags

| Tag | Meaning |
|---|---|
| `[code: path:line @7.x]` | A file in mautic/mautic at the 7.x snapshot below. Line numbers are for that snapshot. |
| `[code: path @7.2.0]`, `@6.0.0` etc. | A file at that release tag, used for version history. |
| `[code: path:line @8.x]` | A file in the 8.x development branch snapshot below. |
| `[docs: https://docs.mautic.org/en/7.2/...]` | End-user documentation (built from mautic/user-documentation). |
| `[devdocs: https://devdocs.mautic.org/en/7.2/...]` | Developer documentation (built from mautic/developer-documentation-new). |
| `[kb: https://kb.mautic.org/article/...]` | Knowledge base article. |
| `[PR #NNNN]` | A merged pull request on github.com/mautic/mautic. Add `(vX.Y)` for the release it landed in. |

### What "7.x" means in these skills

The 7.x snapshot is the head of the `7.x` development branch, not a release tag. It contains every change in the
latest release, 7.2.2 (merged into `7.x`), plus 181 merged pull requests that are in no release yet and are bound
for 7.3, for example the Projects API, unsubscribe email validation, batch contact-to-company assignment and
"any associated company" Segment filters. Skills mark such behaviour as "unreleased on 7.x (7.3.0-rc)". Both docs
repositories have a `7.3` branch. The list of those pull requests is in the mautic-upgrades-and-versions skill.

A citation tagged with a commit instead of `@7.x` or `@8.x` (for example `@419a08a9b35`) points at the code that was
checked at that commit. It is left that way when the cited lines changed in a later snapshot and the claim has not
been re-checked yet; `scripts/remap-code-citations.py` produces these and moves every unchanged citation forward.

Where sources disagree about *current* behaviour, the order of authority used was: code at the 7.x snapshot, then
docs, then PR discussion. The disagreement is recorded where it occurs.

## Snapshots used

| Source | Snapshot | Date |
|---|---|---|
| mautic/mautic branch `7.x` (authoritative): release 7.2.2 plus 181 merged, unreleased pull requests bound for 7.3. `app/release_metadata.json` says 7.2.2. | commit `838c9c772ec` | 2026-11-19 |
| mautic/mautic branch `8.x` (in development; `release_metadata.json` says 7.2.2, minimum PHP 8.4) | commit `c79cf37a57b` | 2026-11-22 |
| mautic/user-documentation branch `7.2` (docs.mautic.org/en/7.2) | commit `a308c7f9` | 2026-11-23 |
| mautic/user-documentation branch `7.3` (unreleased; cited as GitHub paths, marked "upcoming in 7.3") | commit `79ae3d0c` | 2026-11-23 |
| mautic/user-documentation branch `8.0` (docs.mautic.org/en/8.0) | commit `50f10873` | 2026-11-23 |
| mautic/developer-documentation-new branch `7.2` (devdocs.mautic.org/en/7.2) | commit `aa63e2e` | 2026-11-23 |
| mautic/developer-documentation-new branch `7.3` (unreleased; cited as GitHub paths) | commit `4a3be59` | 2026-11-23 |
| mautic/developer-documentation-new branch `8.0` (devdocs.mautic.org/en/8.0) | commit `2b27e13` | 2026-11-23 |
| kb.mautic.org, English categories (How-to guides, Troubleshooting, Tutorials) | 48 articles crawled | 2026-11-23 |
| github.com/mautic/mautic merged pull requests (all base branches, #1 to #17840) | 7,422 PRs with descriptions, labels, files, review and issue comments | harvested 2026-10-15 |
| github.com/mautic/mautic merged pull requests, delta (merged 2026-10-15 to 2026-11-23: 94 to `7.x`, 152 to `8.x`, 38 to `7.2`, 7 to other branches) | 291 PRs | harvested 2026-11-23 |

Previous snapshots (2026-10-15 build): code 7.x `419a08a9b35` (7.2.1 plus 87 PRs) and 8.x `11599729491`; user docs 7.2 `4ad1d85`, 8.0 `5565491`; devdocs 7.2 `bb8818f`, 8.0 `4e37690`; KB 42 articles.

Release dates used to place PRs in versions: 1.0.0 2015-03-10 · 2.0.0 2016-07-05 · 3.0.0 2020-06-15 ·
4.0.0 2021-08-30 · 5.0.0 2024-01-09 · 5.1.0 2024-06-12 · 5.2.0 2024-12-02 · 6.0.0 2025-03-25 · 7.0.0 2026-01-20 ·
7.1.0 2026-04-14 · 7.2.0 2026-09-02 · 7.2.1 2026-09-23 · 7.2.2 2026-10-26 (from git tags in mautic/mautic).

## How the content was produced

1. Code analysis: one agent per product area read the 7.x tree and wrote a file:line-cited analysis.
2. Documentation digest: one agent per documentation slice read the RST sources (7.2 and 8.0 branches) and the
   knowledge base and wrote URL-cited digests.
3. PR analysis (after synthesis, area by area): `scripts/bucket-prs.py` removed 869 noise PRs (bot authors,
   mechanical tooling titles, 8.x type-hardening sweeps) and bucketed the remaining 6,553 by the files they
   touched into 26 areas. Each area was split into chunks of about 240,000 characters, ordered by PR number, so
   chunk file names do not give exact merge-date ranges; every item is dated by its merge date and release tag.
   One agent read each chunk in full (description and comments) and extracted behaviour decisions, regressions,
   features, removals, maintainer norms and open questions. For the largest areas (architecture, emails,
   contacts) a consolidation agent merged the chunk notes first. An integration agent per skill then wrote
   `references/pr-history.md` and made small, cited additions to SKILL.md, version-notes.md and
   test-patterns.md, checking disputed claims against the 7.x tree. Where a PR and the current code disagree,
   the code wins and the PR claim is recorded as history or an open question. Every `[PR #N]` tag was checked
   against the harvested list of merged PRs.
4. 8.x delta: one agent catalogued the 7.x to 8.x changes from UPGRADE-8.0.md, the branch diff and the 8.0 docs.
5. Synthesis: one agent per skill combined the inputs for its area into SKILL.md and the reference files, keeping
   every citation.
6. Review: a consistency pass checked cross-skill contradictions, terminology and citation coverage.

Regeneration scripts live in `scripts/`.
