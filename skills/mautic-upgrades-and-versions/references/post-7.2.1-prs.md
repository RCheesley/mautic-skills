# Pull requests merged to 7.x after the 7.2.1 release

These 87 pull requests are in the 7.x snapshot this repository describes (`419a08a9b35`) but not in the 7.2.1 release. Behaviour they introduce is unreleased until the next 7.x minor. Source: `git log --first-parent 7.2.1..419a08a9b35` in mautic/mautic.

| PR | Merged | Base | Title |
|---|---|---|---|
| [PR #15569] | 2026-10-06 | 7.x | Projects API |
| [PR #15609] | 2026-10-07 | 7.x | feat: Download selected assets |
| [PR #15800] | 2026-10-05 | 7.x | Enable contact segment filters based on any associated company fields |
| [PR #15822] | 2026-10-08 | 7.x | [UXUI-186] Add category filters to all resources |
| [PR #15988] | 2026-09-03 | 7.x | Re-adding tags filter for DWC and fixed unable to create DWC with tag filter |
| [PR #16426] | 2026-09-14 | 7.x | fix(form): existing contact wins merge on form submission |
| [PR #16474] | 2026-09-23 | 7.x | Fix manually adding lead to segment via campaign |
| [PR #16512] | 2026-09-11 | 7.x | Add batch contact-to-company assignment  & add logging |
| [PR #16849] | 2026-09-11 | 7.x | [UXUI-295] Clear contact owners in bulk |
| [PR #16852] | 2026-10-09 | 7.x | [UXUI-296] Remove selected contacts from a company |
| [PR #16870] | 2026-09-09 | 7.x | Making unsubscribes/resubscribes more secure |
| [PR #16872] | 2026-10-07 | 7.x | [UXUI-299] Add quick filters for indexed and unique custom fields |
| [PR #17139] | 2026-09-04 | 7.x | Fix duplicate error class being added to the same element- #3097 |
| [PR #17188] | 2026-09-11 | 7.x | Throw instead of a TypeError when the lock file cannot be opened |
| [PR #17245] | 2026-09-16 | 7.x | Fix Campaign Event getting skip which are reschedule due to race-condition |
| [PR #17256] | 2026-09-15 | 7.x | Support relative dates in report filters |
| [PR #17281] | 2026-09-22 | 7.x | Add custom search command |
| [PR #17282] | 2026-09-24 | 7.x | Custom field related code refactoring |
| [PR #17284] | 2026-09-09 | 7.x | docs: add kah-ja as a contributor for code |
| [PR #17285] | 2026-09-08 | 7.x | Bump the composer-dev-dependencies group with 2 updates |
| [PR #17286] | 2026-09-08 | 7.x | Bump phpstan/phpstan from 2.2.9 to 2.2.13 in the composer-phpstan-dependencies group |
| [PR #17287] | 2026-09-08 | 7.x | Bump the npm-dependencies group with 32 updates |
| [PR #17296] | 2026-09-14 | 7.x | A/B test improvements |
| [PR #17301] | 2026-09-09 | 7.x | Bump predis/predis from 3.0.1 to 3.6.0 |
| [PR #17305] | 2026-09-09 | 7.x | Bump composer/composer from 2.10.2 to 2.10.3 |
| [PR #17306] | 2026-09-09 | 7.x | Bump baseline-browser-mapping from 2.10.35 to 2.11.21 |
| [PR #17307] | 2026-09-09 | 7.x | Bump js-yaml from 4.3.1 to 4.3.2 in /plugins/GrapesJsBuilderBundle |
| [PR #17340] | 2026-09-10 | 7.x | Add 7.2.x series to bug report template |
| [PR #17341] | 2026-09-16 | 7.x | Fixing duplicate tag saving issue |
| [PR #17348] | 2026-09-11 | 7.x | docs: add brynnclaw as a contributor for code |
| [PR #17351] | 2026-09-11 | 7.x | docs: add fabiooliveir as a contributor for code |
| [PR #17352] | 2026-09-11 | 7.x | docs: add peculiaruc as a contributor for code |
| [PR #17356] | 2026-09-22 | 7.x | Fixing Reply-to address configuration precedence |
| [PR #17377] | 2026-09-14 | 7.x | [7.x] Fix flaky ResumeStuckCampaignCommandTest matching ids inside timestamps |
| [PR #17385] | 2026-09-15 | 7.x | Bump the composer-dev-dependencies group with 2 updates |
| [PR #17386] | 2026-09-15 | 7.x | Bump @carbon/pictograms from 12.83.0 to 12.84.0 in the npm-dependencies group |
| [PR #17388] | 2026-10-13 | 7.x | Showing Send to unsubscribed info for Marketing Messages |
| [PR #17391] | 2026-09-16 | 7.x | Assert the upload rollback in testUploadFilesWithError |
| [PR #17400] | 2026-09-16 | 7.x | docs: add dylanpulver as a contributor for code |
| [PR #17404] | 2026-09-22 | 7.x | Dynamic Email Content multi filter fix |
| [PR #17405] | 2026-09-16 | 7.x | docs: add redbullpeter as a contributor for code |
| [PR #17442] | 2026-09-18 | 7.x | [UXUI-305] Clarify point trigger deletion consequences |
| [PR #17443] | 2026-09-18 | 7.x | [UXUI-306] Clarify text message deletion wording |
| [PR #17444] | 2026-09-18 | 7.x | [UXUI-307] Clarify user deletion consequences |
| [PR #17445] | 2026-09-18 | 7.x | [UXUI-308] Clarify segment deletion consequences |
| [PR #17446] | 2026-09-18 | 7.x | [UXUI-309] Clarify report deletion consequences |
| [PR #17447] | 2026-09-18 | 7.x | [UXUI-310] Clarify point group deletion consequences |
| [PR #17448] | 2026-09-18 | 7.x | [UXUI-311] Clarify asset deletion consequences |
| [PR #17449] | 2026-10-07 | 7.x | [UXUI-312] Add Reports filter for reports that have scheduled reports |
| [PR #17450] | 2026-09-18 | 7.x | [UXUI-313] Add Clone action to Report details |
| [PR #17451] | 2026-10-12 | 7.x | [UXUI-314] Add Unowned companies quick filter |
| [PR #17452] | 2026-10-05 | 7.x | [UXUI-315] Add Never logged in users quick filter |
| [PR #17459] | 2026-10-13 | 7.x | Add mautic-dev Agent Skill for core and plugin development |
| [PR #17461] | 2026-09-23 | 7.x | Handle form.repost non-200 responses as integration errors |
| [PR #17472] | 2026-09-22 | 7.x | Allow plugins to add content above the company sidebar score |
| [PR #17475] | 2026-09-22 | 7.x | Bump symfony/maker-bundle from 1.67.0 to 1.68.0 in the composer-dev-dependencies group |
| [PR #17477] | 2026-09-22 | 7.x | Bump the npm-dependencies group with 33 updates |
| [PR #17478] | 2026-09-22 | 7.x | Bump codecov/codecov-action from 7.0.0 to 7.1.1 in the github-actions group |
| [PR #17516] | 2026-09-24 | 7.x | Merge 7.2.1 into 7.x |
| [PR #17548] | 2026-09-25 | 7.x | docs: add DeepanshuPal as a contributor for code |
| [PR #17549] | 2026-10-09 | 7.x | Email and landing page preview improvements |
| [PR #17556] | 2026-09-29 | 7.x | [psr-12] Import fully qualified names and sort use imports |
| [PR #17576] | 2026-09-28 | 7.x | Bump the composer-dev-dependencies group with 2 updates |
| [PR #17577] | 2026-09-29 | 7.x | Bump the npm-dependencies group with 33 updates |
| [PR #17578] | 2026-09-29 | 7.x | Bump undici from 6.28.0 to 6.29.0 |
| [PR #17579] | 2026-09-29 | 7.x | Bump ip-address from 10.4.0 to 10.7.2 |
| [PR #17590] | 2026-10-14 | 7.x | feat: Multi-section copy&paste in GrapesJS |
| [PR #17594] | 2026-10-07 | 7.x | Fix config tabs on Ajax load |
| [PR #17596] | 2026-09-29 | 7.x | Bump league/flysystem from 3.30.0 to 3.36.0 |
| [PR #17602] | 2026-10-12 | 7.x | fix(core): fall back to the default SAML entity id when site_url has no host |
| [PR #17618] | 2026-10-05 | 7.x | docs: add gcomneno as a contributor for code |
| [PR #17628] | 2026-10-07 | 7.x | Bump brace-expansion from 5.0.9 to 5.0.12 |
| [PR #17630] | 2026-10-09 | 7.x | Bump the composer-phpstan-dependencies group across 1 directory with 2 updates |
| [PR #17655] | 2026-10-07 | 7.x | Bump postcss-selector-parser from 7.1.4 to 7.1.6 |
| [PR #17656] | 2026-10-07 | 7.x | Bump source-map-js from 1.2.1 to 1.2.2 |
| [PR #17657] | 2026-10-07 | 7.x | Bump source-map-js from 1.2.0 to 1.2.2 in /plugins/GrapesJsBuilderBundle |
| [PR #17658] | 2026-10-07 | 7.x | Bump fast-uri from 3.1.7 to 3.1.8 |
| [PR #17659] | 2026-10-07 | 7.x | Bump brace-expansion from 1.1.18 to 1.1.21 in /plugins/GrapesJsBuilderBundle |
| [PR #17671] | 2026-10-08 | 7.x | Remove dead track_by_fingerprint and notification_tracking_page_enabled config keys |
| [PR #17689] | 2026-10-12 | 7.x | Add CodeRabbit configuration |
| [PR #17767] | 2026-10-14 | 7.x | [UXUI-264] Update Bootstrap from 3.4.1 to 5.3.8 |
| [PR #17776] | 2026-10-14 | 7.x | Split configuration tabs into separate pages |
| [PR #17781] | 2026-10-13 | 7.x | Add Privacy Centre configuration page with Gravatar toggle |
| [PR #17818] | 2026-10-14 | 7.x | Bump the composer-phpstan-dependencies group across 1 directory with 3 updates |
| [PR #17819] | 2026-10-14 | 7.x | Bump @carbon/pictograms from 12.85.0 to 12.86.0 in the npm-dependencies group |
| [PR #17820] | 2026-10-14 | 7.x | Bump the github-actions group with 4 updates |
| [PR #17834] | 2026-10-14 | 7.x | docs: add techsurrusr as a contributor for code |
