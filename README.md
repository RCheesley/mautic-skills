# mautic-skills

Agent skills that teach any AI coding or testing agent how Mautic works: what its behaviour is supposed to be, where
that behaviour lives in the code, and how to change and test it safely.

The skills use the cross-tool Agent Skills format (`skills/<name>/SKILL.md` plus `references/`). Claude Code, Codex,
Cursor, Gemini CLI and GitHub Copilot can all load them. Tools that do not load skills can read `AGENTS.md`, which
indexes every skill.

## What the skills cover

- **Authoritative version:** Mautic 7.x, the head of the upstream `7.x` branch at commit `838c9c772ec` (2026-11-19).
  That is release 7.2.2 plus 181 merged pull requests bound for 7.3. Skills mark behaviour from those pull requests.
- **Next major:** Mautic 8.x is in development. Every skill has version notes for what changes there, and
  `mautic-upgrades-and-versions` holds the full 7.x to 8.x guide.
- **Older versions:** differences in 5.x and 6.x are called out where the sources show them. Earlier versions appear
  only as history.

Every statement carries a source tag: code path and line at a pinned commit, a docs.mautic.org, devdocs.mautic.org or
kb.mautic.org URL, or a pull request number. Where the docs and the code disagree, the skill states the code's
behaviour and records the discrepancy. See [SOURCES.md](SOURCES.md) for the exact snapshots and the method.

## Skills

| Skill | Use it for |
|---|---|
| `mautic-overview` | Start here: what Mautic is, glossary, which skill to open |
| `mautic-architecture` | Bundles, DI, events, models, controllers, request lifecycle, bundle map |
| `mautic-dev-environment` | DDEV, install, assets, local cron and Messenger, credentials |
| `mautic-testing` | PHPUnit and Codeception, base classes, recipes, static analysis, black-box QA |
| `mautic-contributing` | Branches, PR template, checklist, schema-change rules, terminology |
| `mautic-plugin-development` | Plugin structure, lifecycle and the extension-point catalogue |
| `mautic-theme-development` | Themes, GrapesJS builder, MJML, Twig sandbox |
| `mautic-upgrades-and-versions` | Release history, updater, migrations, the 7.x to 8.x guide |
| `mautic-configuration` | Parameter precedence, env vars, installer, full parameter reference |
| `mautic-cron-and-queues` | Every console command, cron schedule, locking, Messenger, cache |
| `mautic-troubleshooting` | Symptom-first diagnosis across all areas |
| `mautic-contacts` | Contacts, companies, custom fields, import, DNC, identification and merge |
| `mautic-segments` | Segment filters and operators, membership, rebuilds |
| `mautic-campaigns` | Campaign builder, scheduling, membership, execution, extension contract |
| `mautic-emails` | Sending eligibility, tokens, tracking, unsubscribe, bounces, transports |
| `mautic-forms` | Fields, actions, submission pipeline, kiosk mode, progressive profiling, embedding |
| `mautic-pages-and-tracking` | Landing pages, tracking script, page hits, redirects, dynamic web content |
| `mautic-assets-categories-projects` | Assets and downloads, categories, projects |
| `mautic-points-and-stages` | Point actions, groups, triggers, stages |
| `mautic-reports-and-dashboard` | Reports, scheduled reports, dashboard widgets |
| `mautic-channels` | SMS, push, marketing messages, focus items, social, frequency rules |
| `mautic-users-and-permissions` | Users, roles, the permission framework, authentication, SAML |
| `mautic-rest-api` | API conventions, OAuth2 and Basic auth, endpoint inventory |
| `mautic-webhooks` | Webhook events, payloads, delivery, signatures |
| `mautic-integrations` | Integrations framework, sync engine, CRM plugins, Marketplace |

Each skill has the same shape:

```
skills/<name>/
├── SKILL.md                    # scope, expected behaviour, where it lives, how to change and test, pitfalls
└── references/
    ├── behaviour.md            # full numbered behaviour specification, every item cited
    ├── code-map.md             # entities, tables, services, events, routes, commands, parameters, permissions
    ├── docs-digest.md          # what the official docs say, with URLs and docs-vs-code discrepancies
    ├── test-patterns.md        # base classes, representative tests, skeletons
    ├── version-notes.md        # 5.x/6.x differences, 7.x minors, 8.x changes
    └── pr-history.md           # why behaviour is the way it is: decisions, regressions, timeline, norms
```

Some skills add extra reference files, such as the full parameter table, the endpoint inventory, the command
inventory or the 7.x to 8.x event map.

## Relationship to Mautic's own agent files

Mautic core ships `AGENTS.md` and a `mautic-dev` skill (`.agents/skills/mautic-dev/`) in its repository. Those cover
the development commands and the pitfalls that waste the most time when changing core. This repository is
complementary: it documents behaviour, the code map and the official documentation for every product area. When
working inside a Mautic checkout, agents should load both.

## Install

```bash
# Claude Code (default target ~/.claude/skills)
./scripts/link-skills.sh

# Codex
CODEX_SKILLS_DIR=~/.codex/skills ./scripts/link-skills.sh

# Any other tool
AGENT_SKILLS_DIR=/path/to/skills ./scripts/link-skills.sh
```

The installer symlinks each skill, so pulling this repository updates installed skills. To vendor the skills into a
project instead, copy `skills/*` into that project's skills directory, for example `.claude/skills/` or
`.agents/skills/`.

## Maintenance

| Script | Purpose |
|---|---|
| `scripts/harvest-prs.py` | Download merged pull requests on mautic/mautic, with comments, as JSONL (`--since DATE` for a delta) |
| `scripts/bucket-prs.py` | Filter noise and split the pull request corpus by product area into chunks |
| `scripts/crawl-kb.py` | Crawl the English kb.mautic.org articles |
| `scripts/check-citations.py` | Report statements in skills that carry no source tag |
| `scripts/check-pr-tags.py` | Fail if any `[PR #N]` tag is not a merged pull request |
| `scripts/remap-code-citations.py` | Move `[code: path:line]` citations to a new snapshot; pin the ones whose code changed |
| `scripts/relabel-released.py` | List statements marked unreleased whose pull requests are now in a release tag |

### Pull request history

Every product-area and working skill has `references/pr-history.md` (the overview and troubleshooting skills point to them): the behaviour decisions, regression catalogue, feature timeline,
removals and maintainer norms mined from the area's merged pull requests, with descriptions and review comments.
The corpus is every merged pull request on mautic/mautic up to 2026-10-15 (7,422), less 869 bot, tooling and
mechanical pull requests. `mautic-contributing` collects the project-wide norms: branch and release policy,
backward compatibility and deprecation, review and testing rules, and how those norms changed over time.

## Updating to a new snapshot

1. Fetch upstream and create worktrees for the new `7.x` and `8.x` heads and the latest release tag.
2. Run `scripts/remap-code-citations.py --apply --pin-changed` for `7.x` and for `8.x`. Unchanged citations move to
   the new line numbers; citations whose code changed are pinned to the old commit and listed in the report.
3. Update the commits and the release description in `SOURCES.md`, `README.md` and `AGENTS.md`. File headers point
   at `SOURCES.md`, so they do not need editing.
4. Run `scripts/relabel-released.py` against the new release tags and relabel what has shipped.
5. Harvest the pull requests merged since the last harvest (`harvest-prs.py --since`), bucket them by area, and give
   each area's new pull requests, pinned citations and docs diffs to one agent. It re-checks the pinned claims, moves
   them back to `@7.x` or `@8.x`, and updates `behaviour.md`, `pr-history.md` and `version-notes.md`.
6. Diff the docs branches and the KB crawl and update each `docs-digest.md`.
7. Run `scripts/check-citations.py` and `scripts/check-pr-tags.py` before committing.
