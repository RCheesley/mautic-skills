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

The 7.x snapshot is the head of the `7.x` development branch, not the 7.2.1 release tag. It contains every change in
7.2.1 plus 87 pull requests merged after it, for example the Projects API, unsubscribe email validation, batch
contact-to-company assignment and "any associated company" Segment filters. Skills mark such behaviour as
"7.x after 7.2.1 (unreleased)". The 8.0 docs branch already documents several of these features, and the 7.3 user-docs
branch exists upstream. The list of those pull requests is in `references/post-7.2.1-prs.md` of the
mautic-upgrades-and-versions skill.

Where sources disagree about *current* behaviour, the order of authority used was: code at the 7.x snapshot, then
docs, then PR discussion. The disagreement is recorded where it occurs.

## Snapshots used

| Source | Snapshot | Date |
|---|---|---|
| mautic/mautic branch `7.x` (authoritative): release 7.2.1 plus 87 merged, unreleased pull requests (671 commits) bound for the next 7.x minor. `app/release_metadata.json` still says 7.2.1. | commit `419a08a9b35` | 2026-10-14 |
| mautic/mautic branch `8.x` (in development) | commit `11599729491` | 2026-10-15 |
| mautic/user-documentation branch `7.2` (docs.mautic.org/en/7.2) | commit `4ad1d85` | 2026-10-15 |
| mautic/user-documentation branch `8.0` (docs.mautic.org/en/8.0) | commit `5565491` | 2026-10-15 |
| mautic/developer-documentation-new branch `7.2` (devdocs.mautic.org/en/7.2) | commit `bb8818f` | 2026-10-12 |
| mautic/developer-documentation-new branch `8.0` (devdocs.mautic.org/en/8.0) | commit `4e37690` | 2026-10-12 |
| kb.mautic.org, English categories (How-to guides, Troubleshooting, Tutorials) | 42 articles crawled | 2026-10-15 |
| github.com/mautic/mautic merged pull requests (all base branches, #1 to #17840) | 7,422 PRs with descriptions, labels, files, review and issue comments | harvested 2026-10-15 |

Release dates used to place PRs in versions: 1.0.0 2015-03-10 · 2.0.0 2016-07-05 · 3.0.0 2020-06-15 ·
4.0.0 2021-08-30 · 5.0.0 2024-01-09 · 5.1.0 2024-06-12 · 5.2.0 2024-12-02 · 6.0.0 2025-03-25 · 7.0.0 2026-01-20 ·
7.1.0 2026-04-14 · 7.2.0 2026-09-02 · 7.2.1 2026-09-23 (from git tags in mautic/mautic).

## How the content was produced

1. Code analysis: one agent per product area read the 7.x tree and wrote a file:line-cited analysis.
2. Documentation digest: one agent per documentation slice read the RST sources (7.2 and 8.0 branches) and the
   knowledge base and wrote URL-cited digests.
3. PR analysis: every merged PR was bucketed by the files it touched, split into chronological chunks of about
   110k tokens, and read in full by an agent that extracted behaviour decisions, regressions, features, removals
   and maintainer norms; a second pass consolidated each area.
4. 8.x delta: one agent catalogued the 7.x to 8.x changes from UPGRADE-8.0.md, the branch diff and the 8.0 docs.
5. Synthesis: one agent per skill combined the inputs for its area into SKILL.md and the reference files, keeping
   every citation.
6. Review: a consistency pass checked cross-skill contradictions, terminology and citation coverage.

Regeneration scripts live in `scripts/`.
