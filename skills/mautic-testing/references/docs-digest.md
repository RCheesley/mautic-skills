# Mautic testing: what the official docs say

The developer docs cover only the Codeception end-to-end suite; nothing on PHPUnit, `MauticMysqlTestCase`, PHPStan,
Rector, coding standards or CI [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html]. For those, the
code and the in-repo agent files are the only source (see code-map.md section 11). The KB adds DDEV, PR-testing and
email-testing how-tos.

## 1. Devdocs: end-to-end test suite

Page: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html (unchanged in 8.0:
https://devdocs.mautic.org/en/8.0/testing/e2e_test_suite.html).

- Purpose: Codeception with Selenium (W3C WebDriver) ensures new pull requests do not break features [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html].
- Prerequisite: Mautic running on DDEV (`ddev start`), then `bin/codecept build`; `codeception.yml` and `tests/acceptance.suite.yml` already exist [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#setup].
- Test environment: acceptance tests go through the web server using the app's database, so a separate test database is needed. In `.env.local` set `APP_ENV=test`, `APP_DEBUG=1`; in `.env.test.local` set `DB_HOST=db`, `DB_USER=db`, `DB_PASSWD=db`, `DB_NAME=test`. Database `db` is for normal use, `test` for tests [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#configuring-the-test-environment].
- Structure: `_data/` (SQL dumps, sample CSVs), `_output/` (failure snapshots, HTML reports), `_support/` (`AcceptanceTester.php` with login logic; `Helper/` including `DbHelper.php`, which builds the DB if no dump exists and exports one; `Page/` PageObject locators; `Step/` step objects), `acceptance/` [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#acceptance-tests-structure].
- Do not hard-code complex CSS/XPath locators in tests; use PageObject classes [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#acceptance-tests-structure].
- Watch tests in a browser via noVNC at `https://mautic.ddev.site:7900/`, password `secret` [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#view-tests-in-the-browser].
- Failures produce snapshots and HTML reports in `_output` [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#view-test-results].
- Commands: `bin/codecept build`; `bin/codecept run [acceptance [Cest[:method]]]`; `--steps`; `-vvv`; `bin/codecept generate:cest|generate:pageobject|generate:stepobject acceptance <Name>` [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#running-tests] [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html#writing-tests].

Discrepancies with code (code wins):
- The page also shows `tests/Acceptance` and `/tests/Support/Page/Acceptance` with capitals; the tree uses `tests/acceptance/` and `tests/_support/` [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html] [code: codeception.yml @7.x].
- The page's login example uses undefined `$name`/`$password`; the real `AcceptanceTester::login()` defaults them to `admin` / `Maut1cR0cks!` [docs: https://devdocs.mautic.org/en/7.2/testing/e2e_test_suite.html] [code: tests/_support/AcceptanceTester.php:27-68 @7.x].
- The composer script `e2e-test` sets `APP_ENV=test` and `EnvHelper` rewrites `.env.local` automatically, so the manual `.env.local` step is only needed when running `bin/codecept` directly [code: composer.json:166-214 @7.x] [code: tests/_support/Helper/EnvHelper.php:16-83 @7.x].

## 2. KB: test environments and PR testing

- Local DDEV: `gh repo clone mautic/mautic`, `ddev start` (answer yes to install), log in as `admin` / `Maut1cR0cks!` at https://mautic.ddev.site; use `index_dev.php` for dev mode with the debug bar [kb: https://kb.mautic.org/article/how-to-set-up-a-mautic-instance-for-testing-locally-with-ddev.html].
- PR testing: the article uses Gitpod; load fixtures with `ddev exec bin/console d:f:l` (purges the database); its login is admin/mautic; each PR needs testing by two people, who Approve or Request changes [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html].
- Release cadence: bug fixes monthly, features quarterly, breaking changes about yearly [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html].
- The default development branch has versioned names (6.0, 7.x) [kb: https://kb.mautic.org/article/how-to-rebase-branch-and-sync-forked-repository-with-upstream-using-git.html].
- Staging: comment out crons before snapshotting, change `site_url`, `cache:clear`, capture mail with a mail catcher; SMS and push are not captured [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html].

Freshness: the DDEV article dates from 2024 and mentions MailHog; the D13 digest notes DDEV now ships Mailpit [unverified]. The Gitpod article's admin/mautic login conflicts with the DDEV and fixture password `Maut1cR0cks!` [kb: https://kb.mautic.org/article/how-do-i-test-bug-fixes-and-new-features-in-mautic.html] [code: app/bundles/UserBundle/DataFixtures/ORM/LoadUserData.php:24-49 @7.x].

## 3. KB: testing emails (black-box)

- "Send example" sends to arbitrary addresses; links are not rewritten to tracking links, tokens render as placeholders, opens and clicks are not tracked, and the webview link works only in a browser logged into Mautic [kb: https://kb.mautic.org/article/how-to-test-emails-in-mautic.html].
- A proper test: tag test Contacts, build a Segment from the tag, do a real Segment send, then duplicate the email; re-subscribe Contacts used to test unsubscribe [kb: https://kb.mautic.org/article/how-to-test-emails-in-mautic.html].
- One Email (same ID) is sent only once to the same Contact in a real Segment send; duplicate the email to resend [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html].
- The test email from Email settings goes to the logged-in User's address with subject "Mautic test email" [kb: https://kb.mautic.org/article/email-sending-doesn-039%3bt-work-here-are-10-things-to-check.html].
These KB articles date from the 4.x era; check against mautic-emails behaviour before relying on them [kb: https://kb.mautic.org/article/how-to-test-emails-in-mautic.html].

## 4. KB: cron for a test instance

- Typical cron jobs: `mautic:segments:update`, `mautic:campaigns:update`, `mautic:campaigns:trigger`, `messenger:consume email --time-limit=240` every 5 minutes, and `mautic:maintenance:cleanup --days-old=365` daily [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html].
- Without cron jobs nothing happens in Mautic [kb: https://kb.mautic.org/article/getting-started-with-mautic.html].

## 5. Terminology

- Use "Contact", "Segment", "Campaign", "Email", "Form", "Landing Page" in prose; code identifiers keep `lead`, `lists`, `list` [docs: https://devdocs.mautic.org/en/7.2/webhooks/events/email_on_send.html].
