# Pull requests on 7.x that are in no release

These 181 pull requests are on the `7.x` branch at the snapshot this repository describes (`838c9c772ec`, 2026-11-19) but in no release tag: not in 7.2.2 (released 2026-10-26) or any earlier release. They are bound for 7.3 (GitHub milestone `7.3.0-rc` where one is set); skills label their behaviour "unreleased on 7.x (7.3.0-rc)". Source: `git log --first-parent 7.2.2..838c9c772ec` in mautic/mautic, one first-parent commit per pull request [code: git log --first-parent 7.2.2..838c9c772ec @7.x].

This file replaces `post-7.2.1-prs.md` (87 PRs at `419a08a9b35`, the 7.x commits after 7.2.1). All 87 are still unreleased and are included here; the other 94 were merged between 2026-10-15 and 2026-11-19. Two entries are branch merges, not features: [PR #17516] (7.2.1 into 7.x) and [PR #17953] (7.2.2 into 7.x). Pull requests that target the `7.2` branch after 7.2.2 (milestone 7.2.3) are not on 7.x yet and are not listed.

Merged is the commit date of the pull request's commit on `7.x`. Every entry's base branch is `7.x`.

| PR | Merged | Title |
|---|---|---|
| [PR #13766] | 2026-11-16 | Login page layout |
| [PR #15300] | 2026-11-13 | Removing useless data from email audit log |
| [PR #15403] | 2026-11-05 | [UXUI] Add contact count for stages |
| [PR #15569] | 2026-10-06 | Projects API |
| [PR #15609] | 2026-10-07 | feat: Download selected assets |
| [PR #15680] | 2026-11-16 | Split unsubscription statuses into different template files |
| [PR #15800] | 2026-10-05 | Enable contact segment filters based on any associated company fields |
| [PR #15822] | 2026-10-08 | [UXUI-186] Add category filters to all resources |
| [PR #15988] | 2026-09-03 | Re-adding tags filter for DWC and fixed unable to create DWC with tag filter |
| [PR #16350] | 2026-11-05 | [UXUI-278] Show cards for manually added and filter added contacts in segment details |
| [PR #16354] | 2026-11-06 | fix(page): skip href replacement when full URL is in do-not-track list |
| [PR #16426] | 2026-09-14 | fix(form): existing contact wins merge on form submission |
| [PR #16474] | 2026-09-23 | Fix manually adding lead to segment via campaign |
| [PR #16492] | 2026-11-05 | Do not send email translation children as independent broadcasts |
| [PR #16512] | 2026-09-11 | Add batch contact-to-company assignment  & add logging |
| [PR #16513] | 2026-11-05 | [UXUI-285] Campaigns get stuck when action executes immediately after conditions |
| [PR #16848] | 2026-11-06 | Migrate MauticOutlookBundle off deprecated AbstractIntegration |
| [PR #16849] | 2026-09-11 | [UXUI-295] Clear contact owners in bulk |
| [PR #16852] | 2026-10-09 | [UXUI-296] Remove selected contacts from a company |
| [PR #16870] | 2026-09-09 | Making unsubscribes/resubscribes more secure |
| [PR #16872] | 2026-10-07 | [UXUI-299] Add quick filters for indexed and unique custom fields |
| [PR #17139] | 2026-09-04 | Fix duplicate error class being added to the same element- #3097 |
| [PR #17188] | 2026-09-11 | Throw instead of a TypeError when the lock file cannot be opened |
| [PR #17245] | 2026-09-16 | Fix Campaign Event getting skip which are reschedule due to race-condition |
| [PR #17256] | 2026-09-15 | Support relative dates in report filters |
| [PR #17281] | 2026-09-22 | Add custom search command |
| [PR #17282] | 2026-09-24 | Custom field related code refactoring |
| [PR #17284] | 2026-09-09 | docs: add kah-ja as a contributor for code |
| [PR #17285] | 2026-09-08 | Bump the composer-dev-dependencies group with 2 updates |
| [PR #17286] | 2026-09-08 | Bump phpstan/phpstan from 2.2.9 to 2.2.13 in the composer-phpstan-dependencies group |
| [PR #17287] | 2026-09-08 | Bump the npm-dependencies group with 32 updates |
| [PR #17296] | 2026-09-14 | A/B test improvements |
| [PR #17301] | 2026-09-09 | Bump predis/predis from 3.0.1 to 3.6.0 |
| [PR #17305] | 2026-09-09 | Bump composer/composer from 2.10.2 to 2.10.3 |
| [PR #17306] | 2026-09-09 | Bump baseline-browser-mapping from 2.10.35 to 2.11.21 |
| [PR #17307] | 2026-09-09 | Bump js-yaml from 4.3.1 to 4.3.2 in /plugins/GrapesJsBuilderBundle |
| [PR #17340] | 2026-09-10 | Add 7.2.x series to bug report template |
| [PR #17341] | 2026-09-16 | Fixing duplicate tag saving issue |
| [PR #17348] | 2026-09-11 | docs: add brynnclaw as a contributor for code |
| [PR #17351] | 2026-09-11 | docs: add fabiooliveir as a contributor for code |
| [PR #17352] | 2026-09-11 | docs: add peculiaruc as a contributor for code |
| [PR #17356] | 2026-09-22 | Fixing Reply-to address configuration precedence |
| [PR #17377] | 2026-09-14 | [7.x] Fix flaky ResumeStuckCampaignCommandTest matching ids inside timestamps |
| [PR #17385] | 2026-09-15 | Bump the composer-dev-dependencies group with 2 updates |
| [PR #17386] | 2026-09-15 | Bump @carbon/pictograms from 12.83.0 to 12.84.0 in the npm-dependencies group |
| [PR #17388] | 2026-10-13 | Showing Send to unsubscribed info for Marketing Messages |
| [PR #17391] | 2026-09-16 | Assert the upload rollback in testUploadFilesWithError |
| [PR #17400] | 2026-09-16 | docs: add dylanpulver as a contributor for code |
| [PR #17404] | 2026-09-22 | Dynamic Email Content multi filter fix |
| [PR #17405] | 2026-09-16 | docs: add redbullpeter as a contributor for code |
| [PR #17442] | 2026-09-18 | [UXUI-305] Clarify point trigger deletion consequences |
| [PR #17443] | 2026-09-18 | [UXUI-306] Clarify text message deletion wording |
| [PR #17444] | 2026-09-18 | [UXUI-307] Clarify user deletion consequences |
| [PR #17445] | 2026-09-18 | [UXUI-308] Clarify segment deletion consequences |
| [PR #17446] | 2026-09-18 | [UXUI-309] Clarify report deletion consequences |
| [PR #17447] | 2026-09-18 | [UXUI-310] Clarify point group deletion consequences |
| [PR #17448] | 2026-09-18 | [UXUI-311] Clarify asset deletion consequences |
| [PR #17449] | 2026-10-07 | [UXUI-312] Add Reports filter for reports that have scheduled reports |
| [PR #17450] | 2026-09-18 | [UXUI-313] Add Clone action to Report details |
| [PR #17451] | 2026-10-12 | [UXUI-314] Add Unowned companies quick filter |
| [PR #17452] | 2026-10-05 | [UXUI-315] Add Never logged in users quick filter |
| [PR #17459] | 2026-10-13 | Add mautic-dev Agent Skill for core and plugin development |
| [PR #17461] | 2026-09-23 | Handle form.repost non-200 responses as integration errors |
| [PR #17472] | 2026-09-22 | Allow plugins to add content above the company sidebar score |
| [PR #17475] | 2026-09-22 | Bump symfony/maker-bundle from 1.67.0 to 1.68.0 in the composer-dev-dependencies group |
| [PR #17477] | 2026-09-22 | Bump the npm-dependencies group with 33 updates |
| [PR #17478] | 2026-09-22 | Bump codecov/codecov-action from 7.0.0 to 7.1.1 in the github-actions group |
| [PR #17516] | 2026-09-24 | Merge 7.2.1 into 7.x |
| [PR #17527] | 2026-10-20 | Support for Open ID authentication |
| [PR #17548] | 2026-09-25 | docs: add DeepanshuPal as a contributor for code |
| [PR #17549] | 2026-10-09 | Email and landing page preview improvements |
| [PR #17551] | 2026-11-18 | MAUT-13692: align DWC numeric filter evaluation with segment SQL |
| [PR #17556] | 2026-09-29 | [psr-12] Import fully qualified names and sort use imports |
| [PR #17576] | 2026-09-29 | Bump the composer-dev-dependencies group with 2 updates |
| [PR #17577] | 2026-09-29 | Bump the npm-dependencies group with 33 updates |
| [PR #17578] | 2026-09-29 | Bump undici from 6.28.0 to 6.29.0 |
| [PR #17579] | 2026-09-29 | Bump ip-address from 10.4.0 to 10.7.2 |
| [PR #17590] | 2026-10-14 | feat: Multi-section copy&paste in GrapesJS |
| [PR #17594] | 2026-10-07 | Fix config tabs on Ajax load |
| [PR #17596] | 2026-09-29 | Bump league/flysystem from 3.30.0 to 3.36.0 |
| [PR #17602] | 2026-10-12 | fix(core): fall back to the default SAML entity id when site_url has no host |
| [PR #17618] | 2026-10-05 | docs: add gcomneno as a contributor for code |
| [PR #17628] | 2026-10-07 | Bump brace-expansion from 5.0.9 to 5.0.12 |
| [PR #17630] | 2026-10-09 | Bump the composer-phpstan-dependencies group across 1 directory with 2 updates |
| [PR #17655] | 2026-10-07 | Bump postcss-selector-parser from 7.1.4 to 7.1.6 |
| [PR #17656] | 2026-10-07 | Bump source-map-js from 1.2.1 to 1.2.2 |
| [PR #17657] | 2026-10-07 | Bump source-map-js from 1.2.0 to 1.2.2 in /plugins/GrapesJsBuilderBundle |
| [PR #17658] | 2026-10-07 | Bump fast-uri from 3.1.7 to 3.1.8 |
| [PR #17659] | 2026-10-07 | Bump brace-expansion from 1.1.18 to 1.1.21 in /plugins/GrapesJsBuilderBundle |
| [PR #17671] | 2026-10-08 | Remove dead track_by_fingerprint and notification_tracking_page_enabled config keys |
| [PR #17687] | 2026-11-09 | Enable customizing lead list view primary identifier via plugins |
| [PR #17689] | 2026-10-12 | Add CodeRabbit configuration |
| [PR #17764] | 2026-10-21 | Add Marketplace type filtering and richer package details |
| [PR #17765] | 2026-10-15 | Optimize query for sending emails |
| [PR #17767] | 2026-10-14 | [UXUI-264] Update Bootstrap from 3.4.1 to 5.3.8 |
| [PR #17776] | 2026-10-14 | Split configuration tabs into separate pages |
| [PR #17781] | 2026-10-13 | Add Privacy Centre configuration page with Gravatar toggle |
| [PR #17784] | 2026-10-19 | Mark an email entity no longer cloned when clicking the "Save" button |
| [PR #17818] | 2026-10-14 | Bump the composer-phpstan-dependencies group across 1 directory with 3 updates |
| [PR #17819] | 2026-10-14 | Bump @carbon/pictograms from 12.85.0 to 12.86.0 in the npm-dependencies group |
| [PR #17820] | 2026-10-14 | Bump the github-actions group with 4 updates |
| [PR #17826] | 2026-10-20 | [2] Migrate PHP markup to Bootstrap 5 class names |
| [PR #17827] | 2026-11-05 | [3] Migrate Twig markup to Bootstrap 5 class names |
| [PR #17829] | 2026-11-06 | [4] Migrate JavaScript attributes to Bootstrap 5 |
| [PR #17830] | 2026-11-19 | [5] Use native Bootstrap 5 JavaScript APIs |
| [PR #17834] | 2026-10-14 | docs: add techsurrusr as a contributor for code |
| [PR #17843] | 2026-10-21 | Use the Mautic checkbox style across forms and lists |
| [PR #17846] | 2026-10-15 | Bump the composer dev dependencies |
| [PR #17847] | 2026-10-27 | Stop storing the IP address and device ID for kiosk mode submissions |
| [PR #17848] | 2026-10-19 | docs: add AlexanderZlobinM1 as a contributor for code |
| [PR #17859] | 2026-10-19 | Improve email report performance for unsubscribe and bounce columns |
| [PR #17862] | 2026-11-02 | Replace Gravatar user avatars with generated Line Face avatars |
| [PR #17868] | 2026-11-11 | Skip tracking form submitters whose request is not trackable |
| [PR #17870] | 2026-10-21 | elFinder permissions |
| [PR #17871] | 2026-10-20 | Remove duplicate utility classes that Bootstrap 5 provides |
| [PR #17872] | 2026-11-03 | Migrate custom utilities to Bootstrap 5 ones |
| [PR #17874] | 2026-10-20 | Bump symplify/phpstan-rules from 14.19.0 to 14.19.1 in the composer-dev-dependencies group |
| [PR #17875] | 2026-10-20 | Bump actions/create-github-app-token from 3.2.0 to 3.3.0 in the github-actions group |
| [PR #17879] | 2026-10-27 | Add Mautic design system document (DESIGN.md) |
| [PR #17900] | 2026-10-23 | Replace vertical align utilities with Bootstrap classes |
| [PR #17901] | 2026-10-23 | Replace overflow hidden utility with Bootstrap class |
| [PR #17909] | 2026-11-05 | Login page uses new text and password fields |
| [PR #17917] | 2026-11-02 | Update Chart.js to 4.x |
| [PR #17918] | 2026-10-23 | [7.x] Fix DWC token replacement in href/src/action attributes on newer libxml |
| [PR #17923] | 2026-11-05 | Remove SonarQube references |
| [PR #17928] | 2026-11-12 | Fix campaign library import references |
| [PR #17953] | 2026-10-27 | Merge 7.2.2 into 7.x |
| [PR #17955] | 2026-11-06 | Polish chart visuals |
| [PR #17957] | 2026-10-27 | Bump the composer-dev-dependencies group with 2 updates |
| [PR #17958] | 2026-10-27 | Bump @carbon/pictograms from 12.86.0 to 12.87.0 in the npm-dependencies group |
| [PR #17959] | 2026-10-27 | Bump fast-uri from 3.1.8 to 3.1.9 |
| [PR #17960] | 2026-10-27 | Bump ip-address from 10.7.2 to 10.7.5 |
| [PR #17962] | 2026-10-27 | Bump undici from 6.29.0 to 6.29.1 |
| [PR #17965] | 2026-10-30 | Add a setting to record aggregate analytics |
| [PR #17977] | 2026-11-13 | Fix plugin install when messenger_messages already exists - MTC-12349 |
| [PR #18006] | 2026-11-13 | Don't record email opens for contacts who turned tracking off |
| [PR #18011] | 2026-11-05 | Show unscheduled segment emails as ready to send |
| [PR #18013] | 2026-10-30 | Don't recognise untracked visitors on the tracking pixel and /mtc |
| [PR #18027] | 2026-11-02 | Bump phpoffice/phpspreadsheet from 5.9.0 to 5.10.0 |
| [PR #18028] | 2026-11-05 | Fix tracking event 500er when contact is unavailable |
| [PR #18039] | 2026-11-03 | Bump symplify/easy-coding-standard from 13.3.9 to 13.3.12 in the composer-dev-dependencies group |
| [PR #18041] | 2026-11-03 | Bump the npm-dependencies group with 32 updates |
| [PR #18042] | 2026-11-03 | Bump the github-actions group with 5 updates |
| [PR #18044] | 2026-11-05 | fix: prevent duplicate Chosen icons on high-DPI displays |
| [PR #18045] | 2026-11-05 | Handle missing bundle configuration parameters safely |
| [PR #18046] | 2026-11-05 | Remove two assertions that cannot run after the expected exception |
| [PR #18059] | 2026-11-05 | Improve "Active Contacts" display in segments |
| [PR #18060] | 2026-11-13 | Use Bootstrap 5 spacing classes |
| [PR #18062] | 2026-11-11 | fix: typeError when company custom field value is null |
| [PR #18064] | 2026-11-05 | [7.x] Add CodeRabbit path instructions for Codeception E2E tests |
| [PR #18065] | 2026-11-06 | [7.x] Fix plugin tracking pixel for IntegrationsBundle integrations |
| [PR #18069] | 2026-11-13 | Quick filters (shared helper + grouped filters) |
| [PR #18070] | 2026-11-18 | Quick filters for report data sources |
| [PR #18071] | 2026-11-18 | Quick filter for preference segments |
| [PR #18072] | 2026-11-18 | Quick filters for custom fields |
| [PR #18073] | 2026-11-18 | Quick filters for segment and email types |
| [PR #18076] | 2026-11-18 | Quick filters for unsegmented contacts |
| [PR #18077] | 2026-11-18 | Quick filters for form status and actions |
| [PR #18078] | 2026-11-18 | Quick filters for point gain and loss |
| [PR #18080] | 2026-11-05 | Fix empty error-box being displayed upon hiding/unhiding a theme |
| [PR #18082] | 2026-11-06 | Remove the contact photo from the page title |
| [PR #18106] | 2026-11-12 | Make company views extensible -  MTC-12375 |
| [PR #18117] | 2026-11-10 | Security: Fix OIDC account takeover vulnerability |
| [PR #18122] | 2026-11-10 | Bump the composer-dev-dependencies group with 2 updates |
| [PR #18123] | 2026-11-10 | Bump @carbon/pictograms from 12.87.0 to 12.88.0 in the npm-dependencies group |
| [PR #18129] | 2026-11-13 | Check company permission in email preview |
| [PR #18138] | 2026-11-13 | [feat] Add "favorite themes" to emails and landing pages |
| [PR #18148] | 2026-11-11 | Compare OIDC subject IDs case-sensitively |
| [PR #18155] | 2026-11-11 | docs: add mahmoud-alawad as a contributor for code |
| [PR #18162] | 2026-11-13 | fix(oidc): reset OIDC links when the provider changes |
| [PR #18164] | 2026-11-12 | Skip campaign log backfill during migration dry run |
| [PR #18166] | 2026-11-13 | Fix preview link for subdirectory installs and variant selection |
| [PR #18182] | 2026-11-13 | Add leadid filter to contact timeline |
| [PR #18186] | 2026-11-13 | docs: add VictorMoni as a contributor for code |
| [PR #18198] | 2026-11-13 | Tune CodeRabbit walkthrough and labels |
| [PR #18216] | 2026-11-18 | Remove contacts tab from segment view |
| [PR #18217] | 2026-11-17 | Add progress bar component |
| [PR #18233] | 2026-11-19 | Enable report listeners to provide custom report filter conditions |
| [PR #18238] | 2026-11-18 | Bump jquery-form from 4.3.0 to 4.5.0 in the npm-dependencies group |
| [PR #18239] | 2026-11-16 | Bump the composer-dev-dependencies group with 2 updates |
| [PR #18240] | 2026-11-18 | Enable CodeRabbit issue enrichment |
