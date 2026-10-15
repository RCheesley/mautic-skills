# Mautic contributing: what the official docs say

The documentation sources for contributing are spread over the Community Handbook (contribute.mautic.org), the
Knowledge Base (kb.mautic.org), the two documentation repositories and the in-repo files. The Community Handbook pages
are linked from the repo but were not digested; treat their content as unverified until read.

## 1. Where contribution guidance lives

| Topic | URL | Linked from |
|---|---|---|
| Community Handbook (how to contribute) | https://contribute.mautic.org/contributing-to-mautic | [code: .github/CONTRIBUTING.md:11 @7.x] |
| Contributing code | https://contribute.mautic.org/contributing-to-mautic/developer | [code: README.md:412 @7.x] |
| Working on a pull request | https://contribute.mautic.org/contributing-to-mautic/developer/code/pull-requests#work-on-your-pull-request | [code: .github/PULL_REQUEST_TEMPLATE.md:31 @7.x] |
| Testing PRs | https://contribute.mautic.org/contributing-to-mautic/tester | [code: .github/PULL_REQUEST_TEMPLATE.md:59 @7.x] |
| Reviewing Promptless documentation PRs | https://contribute.mautic.org/en/latest/contributing/developer.html#reviewing-documentation-prs-from-promptless | [code: .github/PULL_REQUEST_TEMPLATE.md:17 @7.x] |
| Backward-compatibility breaks | https://contribute.mautic.org/en/latest/contributing/developer.html#backward-compatibility-breaks | [code: .agents/skills/mautic-dev/SKILL.md:51 @7.x] |
| Maintainer duties (governance model) | https://contribute.mautic.org/governance/governance#6-2-1-expectations-and-duties-of-maintainers | [code: MAINTAINERS.md @7.x] |
| Supported releases | https://www.mautic.org/mautic-releases | [code: SECURITY.md:19 @7.x] |
| Security advisory policy | https://www.mautic.org/mautic-security-team/mautic-security-advisory-policy | [code: SECURITY.md:30 @7.x] |
| Reporting a security issue | https://github.com/mautic/mautic/security | [code: SECURITY.md:32 @7.x] |
| ELTS | https://mau.tc/elts | [code: SECURITY.md:25 @7.x] |
| Developer documentation | https://devdocs.mautic.org (source: https://github.com/mautic/developer-documentation-new) | [code: .github/CONTRIBUTING.md:15 @7.x] |
| User documentation | https://docs.mautic.org (source: mautic/user-documentation) | [code: .github/PULL_REQUEST_TEMPLATE.md:26 @7.x] |
| Technical writing style guide | contribute.mautic.org/education-team/technical-writing-styleguide | [kb: https://kb.mautic.org/article/how-to-contribute-to-the-knowledge-base.html] |
| 8.x plugin porting guide | https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html | [code: UPGRADE-8.0.md @8.x] |

## 2. Knowledge Base articles on contributing

| Article | Statement | Tag |
|---|---|---|
| How do I test bug fixes and new features in Mautic? (Oct 2025) | Release cadence: bug fixes monthly, features quarterly, BC breaks about annually. PR testing uses Gitpod; load fixtures with `ddev exec bin/console d:f:l` (purges the DB); login admin/mautic; each PR needs testing by two people, who Approve or Request changes. | [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] |
| How to set up a Mautic instance for testing locally with DDEV (Mar 2024) | `gh repo clone mautic/mautic`, `ddev start`, log in as admin / `Maut1cR0cks!` at https://mautic.ddev.site; `index_dev.php` for dev mode. DDEV now ships Mailpit, not MailHog. | [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html] |
| How to rebase branch and sync forked repository with upstream (Dec 2025) | Add the upstream remote, fetch, rebase on `upstream/7.x`, force-push; resolve conflicts with `git add` and `rebase --continue`. Default development branch uses versioned names (6.0, 7.x). | [kb: https://kb.mautic.org/article/how-to-rebase-branch-and-sync-forked-repository-with-upstream-using-git.html] |
| Understanding Migrations and Schema Update with Doctrine (Oct 2022) | Semantic versioning: breaking DB changes only in majors; additive DB changes may appear in minors. Repair after failed update: retry, `migrations:migrate`, `schema:update --force`. | [kb: https://kb.mautic.org/article/understanding-migrations-and-schema-update-with-doctrine-in-mautic.html] |
| How to contribute to the Knowledge Base (Aug 2022) | KB articles follow Diataxis (tutorial, how-to, troubleshooting); log in, Admin Area > Add New, one top-level category, tags and summary; Education Team reviews. | [kb: https://kb.mautic.org/article/how-to-contribute-to-the-knowledge-base.html] |

## 3. Procedures

**Open a core PR.**
1. Pick the branch (features `7.x`, bug fixes `7.2`, BC breaks `8.x`). [code: .github/PULL_REQUEST_TEMPLATE.md:1-11 @7.x]
2. Rebase on the upstream branch. [kb: https://kb.mautic.org/article/how-to-rebase-branch-and-sync-forked-repository-with-upstream-using-git.html]
3. Run the checklist in SKILL.md. [code: AGENTS.md:110-119 @7.x]
4. Fill the template (Q/A table, Description, Steps to test, deprecations/BC list). [code: .github/PULL_REQUEST_TEMPLATE.md:19-64 @7.x]
5. Review the Promptless docs PR when it appears and after merge. [code: .github/PULL_REQUEST_TEMPLATE.md:13-17 @7.x]

**Test someone else's PR.** Reproduce on the base branch with fixtures, switch to the PR, retest, and submit Approve or
Request changes. [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html]

**Write documentation.** Edit RST in `mautic/user-documentation` or `mautic/developer-documentation-new`; Vale lints with
the Vale, Google and Mautic styles at level suggestion. [docs: https://github.com/mautic/user-documentation/blob/7.2/.vale.ini]
[docs: https://github.com/mautic/user-documentation/blob/7.2/style-guide.md]

## 4. Terminology
See terminology.md for the full FeatureList, WordList and accepted vocabulary tables.

## 5. 8.0 documentation changes relevant to contributors
- Dev docs 8.0 add the plugin porting guide `plugins/update_m7_to_m8` and switch all event examples to event classes.
  [docs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html] [docs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html]
- The dev-docs accept list adds `LeadBundle`; style rules are otherwise unchanged in 8.0.
  [docs: https://github.com/mautic/developer-documentation-new/blob/8.0/.github/styles/config/vocabularies/Mautic/accept.txt]
- The 8.0 user docs mostly describe unreleased 7.x features (merged after 7.2.1) not yet merged into 8.x code; the only 8-specific user-facing change
  is the removal of `mautic:disable-tracking`. [docs: https://docs.mautic.org/en/8.0/channels/emails.html]
