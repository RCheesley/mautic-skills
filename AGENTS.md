# AGENTS.md

Guidance for AI agents using this repository. Tools that load Agent Skills (Claude Code, Codex, Cursor, Gemini CLI,
GitHub Copilot) can install `skills/` directly; see README.md. Tools that do not load skills should use this file as
an index and open the files it points to.

## What this repository is

A behaviour specification and code map of Mautic, the open-source marketing automation platform, written for agents
that test Mautic, build on it, or change its core. Mautic 7.x is authoritative: the `7.x` branch head, which is
release 7.2.1 plus 87 unreleased pull requests. Mautic 8.x is in development,
and every skill notes what changes there. Differences in 5.x and 6.x are called out where known.

## How to use it

1. Open `skills/mautic-overview/SKILL.md` first. It explains Mautic, defines the terms, and routes a task to the
   right skills.
2. Open the `SKILL.md` of each skill the task touches. Each one lists the essential expected behaviours, where the
   code lives, how to change it, how to test it, version differences and pitfalls.
3. Open a skill's `references/` file only when you need the detail: the full numbered behaviour list, the code map,
   the documentation digest, test patterns or version notes.
4. Treat every behaviour statement as the expected behaviour (the test oracle) unless it is marked `[unverified]` or
   listed as an open question.

## Citation rules

Every statement carries a source tag. SOURCES.md defines the tags and the pinned snapshots.

- `[code: path:line @7.x]` points into mautic/mautic at commit `419a08a9b35`. `@8.x` points at the 8.x snapshot.
- `[docs: …]`, `[devdocs: …]` and `[kb: …]` are docs.mautic.org, devdocs.mautic.org and kb.mautic.org URLs.
- `[PR #N]` is a merged pull request on github.com/mautic/mautic.

When the code and the documentation disagree about current behaviour, the skills follow the code and record the
documentation URL as a discrepancy. Do the same when you extend a skill.

## Skill index

| Skill | Open it when the task involves |
|---|---|
| `skills/mautic-overview` | Anything about Mautic where you are unsure which skill applies |
| `skills/mautic-architecture` | Bundles, DI, events, models, controllers, entities, the request lifecycle |
| `skills/mautic-dev-environment` | Setting up DDEV, installing, building assets, running cron or Messenger locally |
| `skills/mautic-testing` | Writing or running PHPUnit or Codeception tests, static analysis, black-box QA |
| `skills/mautic-contributing` | Opening a pull request, choosing a branch, schema changes, terminology |
| `skills/mautic-plugin-development` | Building a plugin or using an extension point |
| `skills/mautic-theme-development` | Themes, the GrapesJS builder, MJML, Twig templates |
| `skills/mautic-upgrades-and-versions` | Updating Mautic, migrations, release history, porting to 8.x |
| `skills/mautic-configuration` | Configuration parameters, environment variables, the installer |
| `skills/mautic-cron-and-queues` | Console commands, cron schedules, locking, Messenger transports, cache |
| `skills/mautic-troubleshooting` | Diagnosing something that does not work |
| `skills/mautic-contacts` | Contacts, companies, custom fields, import, DNC, identification, merging |
| `skills/mautic-segments` | Segment filters, operators, membership, rebuilds |
| `skills/mautic-campaigns` | Campaigns, scheduling, execution, campaign events |
| `skills/mautic-emails` | Emails, sending, tokens, tracking, unsubscribe, bounces, transports |
| `skills/mautic-forms` | Forms, fields, actions, submissions, embedding |
| `skills/mautic-pages-and-tracking` | Landing pages, the tracking script, page hits, redirects, dynamic web content |
| `skills/mautic-assets-categories-projects` | Assets and downloads, categories, projects |
| `skills/mautic-points-and-stages` | Points, point groups, triggers, stages |
| `skills/mautic-reports-and-dashboard` | Reports, scheduled reports, dashboard widgets |
| `skills/mautic-channels` | SMS, push notifications, marketing messages, focus items, frequency rules |
| `skills/mautic-users-and-permissions` | Users, roles, permissions, authentication, SAML |
| `skills/mautic-rest-api` | The REST API, OAuth2, endpoint conventions and inventory |
| `skills/mautic-webhooks` | Outgoing webhooks, payloads, delivery, signatures |
| `skills/mautic-integrations` | The integrations framework, sync engine, CRM plugins, Marketplace |

## Working inside a Mautic checkout

Mautic core ships its own `AGENTS.md` and a `mautic-dev` skill at `.agents/skills/mautic-dev/`. Follow those for
commands and development pitfalls. Use this repository for what the code is supposed to do.

## Editing this repository

- Keep each `SKILL.md` under 450 lines and its `description` under 1,024 characters.
- Give every new statement a source tag. Run `scripts/check-citations.py` before committing.
- Start any reference file longer than 300 lines with a table of contents.
- Record the snapshot you verified against in SOURCES.md when you move to a new Mautic release.
