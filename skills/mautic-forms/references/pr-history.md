# Forms — PR history

## Contents
1. How to read this file
2. Decisions that shaped current behaviour
3. Regression catalogue
4. Feature timeline
5. Removed, deprecated, replaced
6. Maintainer norms for this area
7. Open questions
8. Coverage

## 1. How to read this file
Source: merged pull requests on mautic/mautic for the Forms area, harvested 2026-10-15.
Versions come from the first release tag in the 7.x tree that contains the merge, or else from the base branch, milestone and merge date. "Unreleased on 7.x (after 7.2.1)" means the merge is on the 7.x head but in no tag.
Current behaviour is in behaviour.md. This file explains why and when. Where the two disagree, behaviour.md wins.

## 2. Decisions that shaped current behaviour

### Submission pipeline and contact identification
- Only form fields that are on the form and mapped to a contact field are sent to the contact update. Unmapped contact fields are not touched. Why: every submit sent empty strings for fields missing from the form, which reset boolean custom fields to false [PR #3582] (v2.7.1).
- A submission must not merge two different contacts. If the tracked contact and the submitted unique identifier conflict, Mautic creates or updates the right contact instead. Why: submitting email A, then B, then A in one browser merged A and B [PR #778] (v1.2.0). A conflicting email creates a new contact rather than overwriting the tracked one [PR #1219] (v1.2.3).
- An anonymous tracked contact that submits a new email becomes the identified contact and keeps its tags and history. Why: tags set on the visitor vanished on identification [PR #1037] (v1.2.1).
- When a known contact submits without a tracking cookie and the email matches, the existing contact wins the merge and keeps its ID. The anonymous contact is deleted and cookies are regenerated for the winner. Why: the anonymous contact used to win, which deleted long-standing contact IDs that external systems stored (issue #16425) [PR #16426] (unreleased on 7.x, after 7.2.1). In 7.2.1 and earlier the anonymous contact won [PR #16426].
- Kiosk mode assigns no IP, sets no tracking cookie and does not merge the tracked visitor, but still updates a contact with a matching email. Why: forms on a vendor's device at events attached the vendor's IP and cookie to every contact [PR #253] (v1.0.2).
- A form with no mapped fields still submits, including when "Send form results" runs with no contact. Why: subscribers called methods on a null contact and returned 500 [PR #5349] (v2.12.2).
- Server-side required checks reject a submission that skips the JS (bots, JS disabled), and no contact is created or updated [PR #7818] (v2.16.0).
- A value of `0` (number or boolean "No") counts as a value for the required check [PR #5189] (v2.12.0).
- An unchecked single checkbox mapped to a boolean field sends nothing, so the contact's value is not overwritten. If the checkbox has a default value, a hidden input sends that default. escopecz questioned how a contact could ever set false; kuzmany cited preference-centre parity [PR #6282] (v2.14.1).
- Submission values are stored without HTML entity encoding (`R&R`, not `R&#x26;R`). Output is escaped when rendered. Why: encoded storage duplicated companies and made webhook payloads inconsistent. Listed as a BC break in UPGRADE-6.0.md [PR #14604] (v6.0.0).
- Company-mapped fields create a company only when a company name is submitted [PR #4660] (v2.10.0). An existing company with the same name is updated with the submitted values; first fixed in [PR #5915] (v2.14.0), then again in [PR #14688] (v7.0).
- Pseudo-fields "Stage (Name)", "Contact Owner (Email)" and "Contact Owner (User Id)" set stage and owner. Non-matching or empty values leave them unchanged [PR #15267] (v7.1.0).
- A submission from a campaign-source form adds the contact only to published campaigns. escopecz objected that contacts submitted while a campaign is briefly unpublished are lost; the PR merged anyway [PR #11130] (v4.3).
- A failed file-upload batch deletes every file already uploaded in that batch. The test that claimed otherwise never ran its assertions [PR #17391] (unreleased on 7.x, after 7.2.1).

### Kiosk mode, auto-fill, pre-fill and progressive profiling
- Kiosk mode turns off progressive profiling and auto-fill. This was decided in the discussion of [PR #2022] (v2.1.0). The 7.x code does both: `Field::showForContact()` returns true in kiosk mode and `getFormHtml()` skips auto-fill [code: app/bundles/FormBundle/Entity/Field.php:818-821 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:383 @7.x].
- Auto-fill pre-fills a mapped field from the identified contact. A query-string value wins, and an empty contact value does not replace a field default. Why: query-string pre-fill was "techie" and put contact data in URLs [PR #1363] (v2.1.0).
- Auto-fill is gated by the global `form_field_autofill`, which is off on new installs. When off, the field option is hidden and neither auto-fill nor auto-fill-driven hiding runs. A migration turns it on when any field already uses auto-fill. Why: auto-fill can expose contact PII on public forms [PR #16954] (v7.2.0). escopecz had raised the same PII risk earlier [PR #14422].
- Read-only fields keep an auto-filled value fixed, for example the email on an invitation link. Why: changing it would break identification [PR #14422] (v6.0.0). A null `readOnly` means false [PR #14502] (v6.0.0).
- Auto-fill covers select and country [PR #4146] (v2.8.2), url, website, date and datetime [PR #8976] (v3.2.2), number fields [PR #12668] (v5.1), company fields from the primary company [PR #12635] (v5.0.0), checkbox groups from multiselect values [PR #15305] (v7.0.0), boolean checkboxes [PR #15740] (v7.1.0) and forms inside Focus items [PR #15860] (v7.0.1).
- Auto-fill keeps a `+` in values (plus-addressed emails, international phone numbers) [PR #12621] (v5.1.0) [PR #12670] (v5.0.0).
- Auto-fill selects the right option whatever the attribute order or whitespace in the `<select>` markup, and keeps `$` and `\` in values [PR #16179] (v7.1.3).
- Pre-fill from URL query parameters was limited to Mautic-hosted pages in 2.10.1, because a reviewer judged it an XSS risk on external pages [PR #4692] (v2.10.1). It was extended to external JS embeds, with `+` preserved [PR #11077] (v5.0.0).
- Loading `generate.js` does not create an anonymous contact unless the form has an auto-fill field. Why: an embed should not act as a tracking script [PR #6122] (v2.14.1).
- Progressive profiling started with "show when value exists" and "show after X submissions" [PR #2022] (v2.1.0). The email field was first excluded, then allowed with a docs warning [PR #3732] (v2.9.0).
- "Display only N fields", "Always display" and cross-form known values arrived in [PR #8611] (v3.3.1). npracht wanted "show after X submissions" removed; it stays in 7.x [PR #8611]. The field limit broke and was restored with a regression test [PR #11125] (v4.3).
- Fields hidden by progressive profiling are not validated [PR #2622] (v2.2.1) [PR #3586] (v2.7.1). A required field that is not displayed cannot be validated, so make it "always display" [PR #8611].
- Submissions with a NULL contact are not counted for "show after X submissions" [PR #6826] (v2.15.0).

### Field mapping and option lists
- Since 5.0, mapping is stored in `mapped_object` and `mapped_field`. Migration `20200415135706` converts `leadField`. Why: to map to any object through collectors [PR #11905] (v5.0.0). The API still accepts the deprecated `leadField` [PR #13938] (v5.2.0).
- Only published contact and company fields can be mapped [PR #10734] (v4.2.1).
- An unmapped email field stays unmapped on edit. Why: 5.x silently remapped it to contact email [PR #13744] (v5.1.0).
- A mapped select, radio or checkbox field uses its own option list unless "Use assigned contact/company field's list choices" (`syncList`) is on. This regressed repeatedly: [PR #8646] (v3.0.0), [PR #14117] (v5.2), [PR #14560] (v5.2.3) [PR #14048] (v5.2.7). Turning `syncList` on overwrites custom labels, and turning it off does not restore them [PR #14117].
- Synced options are available wherever the field loads: campaign condition, preview, JS embed and dynamic content filters [PR #6842] (v2.15.0). Saving a contact select field rebuilds the cached HTML of forms that use it [PR #15557] (v7.1.0).
- Radio groups mapped to Lookup fields store the selected value [PR #14716] (v5.2.4).

### Field aliases, results tables and storage
- Each form has its own results table. The alias part of the name is only a hint [PR #1456] (v1.4.0). The form alias never changes on rename because it ties the form to that table [PR #6894] (v2.15.0).
- Numeric and reserved-word aliases get an `f_` prefix rather than quoting [PR #664] (v1.1.3). Since 5.0, reserved-word columns are also backticked at query time. That replaced [PR #12043], which backticked every column and broke uploads and plugins [PR #12272] (v5.0.0).
- Aliases that collide with `message`, `error`, `id`, `return`, `name` or `messenger` are prefixed. Why: a field labelled "Message" hid validation messages [PR #2302] (v2.1.1).
- API-supplied aliases are sanitised like UI aliases [PR #4317] (v2.9.1) [PR #6895] (v2.15.1). A duplicate once got a random alias [PR #4317]. Since 5.1, aliases that collide after truncation return 400 and the save rolls back [PR #13599] (v5.1.0).
- Deleting a field drops its results column, and a migration removed old orphan columns [PR #15129] (v7.0.0). Deleting a form drops its table [PR #15489] (v7.0.0).
- Deleting results also deletes the results row. Two commands clean up older orphans: `mautic:forms:delete-orphan-form-submission-records-from-form-results-table` and `mautic:forms:delete-results-table`. The PR text uses older names without `forms:` [PR #16123] (v7.2.0) [code: app/bundles/FormBundle/Command/DeleteOrphanFormResultsTableCommand.php:24 @7.x] [code: app/bundles/FormBundle/Command/DeleteOrphanSubmissionRecordsFromFormResultsTableCommand.php:25 @7.x].
- Uploads live under `media/files/form/{formId}/{fieldId}/`. Deleting a submission, field or form deletes the matching files [PR #5082] (v2.11.0). Deleting one form removes only its own folder [PR #5957] (v2.13.1).
- Field order is unique and sequential on save, including conditional children, with field ID as tie-breaker [PR #15459] (v7.0.0) [PR #16223] (v7.2.0). Action order is kept after save [PR #14213] (v5.2).
- Long redirect URLs and messages (over 191 characters) save [PR #10266] (v4.1.0).

### Validation and spam protection
- An empty captcha is a honeypot [PR #2451] (v2.2.0). It must not be visible on the rendered form [PR #16514] (v7.2.0).
- E.164 phone validation runs only when enabled on the field and skips empty values [PR #5400] (v2.14.1) [PR #6645] (v2.14.2) [PR #7130] (v2.15.1). It checks format only [PR #9415] (v3.2.0).
- "Do not submit these emails" accepts addresses and `*@domain` wildcards [PR #7709] (v2.16.0). "Block free email providers" uses an editable global domain list [PR #15420] (v7.1.0).
- Checkbox groups can require a minimum and maximum number of selections, checked on the server [PR #15423] (v7.1.0).
- File fields can never allow extensions in `blacklisted_extensions` [PR #5082] (v2.11.0).

### Submit actions
- "Send form results" goes to the configured recipients, and to the contact only when "Send to contact" is on [PR #5853] (v2.13.0). That toggle defaults to No [PR #6074] (v2.14.0).
- The **To** field of "Send form results" is required. Why: with To empty, "send to owner" on and an ownerless contact, no email went out. escopecz rejected a hidden fallback to the form creator as "a little hidden or assumed behavior" [PR #17137] (v7.2.0). This reverses [PR #11405] (v4.4.2), which allowed CC or BCC only. In 7.x the trait's `toRequired` flag is set only by `SubmitActionEmailType`, so no other form is affected [code: app/bundles/FormBundle/Form/Type/SubmitActionEmailType.php:128 @7.x] [code: app/bundles/CoreBundle/Form/ToBcBccFieldsTrait.php:14-24 @7.x].
- File tokens in results emails become download URLs [PR #6104] (v2.14.1), and absolute URLs when results are not saved but the public link is on [PR #9233] (v4.1.0). Select values show as labels [PR #10087] (v4.0.0).
- "Send email" actions have "Send immediately" to bypass the queue [PR #5414] (v2.12.1).
- Repost sends values unencoded [PR #10872] (v4.2.1). From 5.1, a 4xx from the target was shown on the form [PR #13482] (v5.1.0). On the 7.x head, only a `violations` response blocks the visitor. Other non-2xx responses count as delivery failures and trigger the failure email [PR #17461] (unreleased on 7.x, after 7.2.1).
- "Update contact" sets contact fields after submission [PR #15690] (v7.1.0).
- Submit actions run only through `ON_EXECUTE_SUBMIT_ACTION` listeners; callbacks were removed [PR #8186] (v3.0.0).

### Successful-submit behaviour
- The UI default for new forms is "Display message" [PR #12813] (v5.1.0). The API default stays `return` so API clients do not break [PR #13410] (v5.0.4).
- `hideform` hides the form and shows a required message. Why: hiding needed custom JS [PR #15118] (v7.0.0).
- `successful_submit_action` (default `top`) puts the message above or below the form. Moving it unconditionally was rejected as a BC break for sites that style embeds [PR #10726] (v5.0.0).
- Redirect URLs must be valid URLs or recognised tokens (`{pagelink=}`, `{contactfield=}`, `{formfield=}`). A plain Symfony `Url` constraint was rejected because it broke tokens [PR #15596] (v7.0.2) [PR #14099] (v5.2).
- A submission limit closes the form with its own message, and deleting results reopens it [PR #15396] (v7.2.0).

### Rendering, embedding and the JS SDK
- Forms post through a hidden iframe and answer via `postMessage` [PR #500] (v1.1.0). The origin check stays; a PR that removed it was rejected, and the subfolder fix compares hosts [PR #5558] (v2.12.2).
- `generate.js` inserts HTML through the DOM so `async`/`defer` work, with `document.write` as fallback [PR #6432] (v2.14.1).
- The SDK refuses a second submit while one is in flight (`data-mautic-form-submitting`, `aria-busy`). The guard runs before `onValidate` and is client-side only [PR #17138] (v7.2.0).
- Forms from two Mautic instances on one page each submit to their own instance [PR #17354] (v7.2.1).
- Embed snippets on the details page use the configured Site URL [PR #17193] (v7.2.0).
- Enter does not submit a multi-page form before the last page [PR #15156] (v7.1.0).
- Public form markup is a BC contract: the tel field kept `mauticform-tel` [PR #8671] (v3.0.0).
- Form attributes are output raw, so admins can add JS attributes that run only on embeds. escopecz invited a security discussion; it merged as-is [PR #13726] (v5.1.0).
- Labels and help text allow HTML through `purify`, not `raw` [PR #14026] (v5.2) [PR #12562] (v5.0.0). `target="_blank"` is kept [PR #15298] (v7.0.0).
- New forms default to "Disable search indexing" (`noIndex`). The request to remove the toggle was rejected [PR #15255] (v7.0.0). In 7.0.0 the constructor sets it; on the 7.x head it is the property default [code: app/bundles/FormBundle/Entity/Form.php:178 @7.x].

### Themes and templates
- Since 5.0 form templates are Twig. Theme overrides must be `.html.twig` [PR #11898] (v5.0.0) [PR #12115] (v5.0.0).
- A form with no theme uses the system default theme, then core [PR #13043] (v5.1.0). Themes need only override the `text`, `select` and `group` base templates [PR #13052] (v5.1.0).
- "Use theme style?" set to No clears and disables the theme select [PR #13369] (v5.1) [PR #14003] (v5.2.0).

### Form types and campaigns
- Standalone and campaign forms were introduced in [PR #515] (v1.1.0). Campaign forms regained actions in [PR #2451] (v2.2.0). Since 7.1 there is one form type and every action works on every form. Why: the split confused users [PR #15803] (v7.1.0).
- The "Form field value" condition compares numbers numerically [PR #7705] (v3.0.1), matches values with `&` [PR #10470] (v4.1.0), and wraps `like` values in `%` as segments do [PR #13079] (v5.1.0).

### Results, export and reports
- Results show "Submission ID" and "Contact ID" [PR #6085] (v2.14.0) [PR #11894] (v5.0.0). Values are escaped [PR #3212] (v2.6.0).
- Results exports stream large data sets [PR #5792] (v2.13.1).
- Sorting results stays on the current form [PR #17403] (v7.2.1).
- `form_results_data_sources` (default false) makes each results table a report source. All form code must stay in FormBundle and talk to ReportBundle through events [PR #11567] (v5.0.0).

### API
- `GET api/forms/{id}/submissions` without permission returns 403 [PR #10679] (v4.2.1).
- `PUT` removes actions missing from the payload [PR #6892] (v2.15.1). `PATCH` must not unpublish the form [PR #15806] (v7.0.1).
- Create and update run in one transaction and return proper errors [PR #15319] (v7.0.0).

## 3. Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **Submission and contact** | | | |
| A, B, A submissions merged contacts A and B | No merge on unique-identifier conflict | [PR #778] | 1.2.0 |
| Conflicting email overwrote the tracked contact | New contact created | [PR #1219] | 1.2.3 |
| Anonymous visitor's submit made a second contact | Anonymous contact becomes identified | [PR #1037] | 1.2.1 |
| Boolean fields reset to false on every submit | Only mapped form fields reach the contact | [PR #3582] | 2.7.1 |
| Required 0 value rejected | 0 is a value | [PR #5189] | 2.12.0 |
| 500 on a form with no mapped fields and a results action | Submit succeeds | [PR #5349] | 2.12.2 |
| Unchecked checkbox set a boolean field to false | No overwrite unless a default is set | [PR #6282] | 2.14.1 |
| Missing required fields accepted with JS off | Rejected server-side, no contact | [PR #7818] | 2.16.0 |
| Existing company not updated on resubmit | Company fields updated | [PR #5915] [PR #14688] | 2.14.0, 7.0 |
| Results showed `R&#x26;R` | Stored raw, escaped on output | [PR #14604] | 6.0.0 |
| Campaign-source form joined unpublished campaigns | Only published campaigns | [PR #11130] | 4.3 |
| Known contact without cookie lost its ID | Existing contact wins the merge | [PR #16426] | unreleased on 7.x (after 7.2.1) |
| **Auto-fill and progressive profiling** | | | |
| Second boolean auto-fill field not filled | All boolean fields filled | [PR #7347] | 2.15.2 |
| Auto-fill turned `a+b@x` into `a b@x` | `+` kept | [PR #12621] [PR #12670] | 5.1.0, 5.0.0 |
| Company-mapped fields not auto-filled | Filled from primary company | [PR #12635] | 5.0.0 |
| Select auto-fill missed when `id` was not first | Option selected; `$` and `\` kept | [PR #16179] | 7.1.3 |
| Checkbox auto-fill from multiselect failed | Prepopulated | [PR #15305] | 7.0.0 |
| Auto-fill missing in Focus item forms | Works | [PR #15860] | 7.0.1 |
| Progressive limit ignored | Only N non-"always display" fields render | [PR #11125] | 4.3 |
| Hidden required field blocked submit | Hidden fields not validated | [PR #2622] [PR #3586] | 2.2.1, 2.7.1 |
| **Mapping and options** | | | |
| Mapped choice field ignored its own list | Own list unless `syncList` | [PR #14560] [PR #14048] | 5.2.3, 5.2.7 |
| Unmapped email field remapped on edit | Stays unmapped | [PR #13744] | 5.1.0 |
| Unpublished contact fields offered for mapping | Only published fields | [PR #10734] | 4.2.1 |
| Removed custom-field options still on cached forms | Cache rebuilt on field save | [PR #15557] | 7.1.0 |
| Radio to Lookup field stored wrong value | Value stored | [PR #14716] | 5.2.4 |
| **Aliases and storage** | | | |
| Reserved-word alias broke results | `f_` prefix plus backticks at query time | [PR #12272] | 5.0.0 |
| Renaming via API emptied results | Alias unchanged on rename | [PR #6894] | 2.15.0 |
| Truncated API aliases collided: 500, partial save | 400 and rollback | [PR #13599] | 5.1.0 |
| Deleted field left its column | Column dropped | [PR #15129] | 7.0.0 |
| Deleting results left results rows | Rows deleted | [PR #16123] | 7.2.0 |
| Deleting one form wiped other uploads | Only its folder removed | [PR #5957] | 2.13.1 |
| Conditional children shuffled after save | Unique order, ID tie-break | [PR #16223] | 7.2.0 |
| Action order lost after save | Order kept | [PR #14213] | 5.2 |
| Cloned form lost conditional fields | Children cloned | [PR #14752] | 7.0.0 |
| **Validation** | | | |
| Phone validated with the option off | Only when enabled; empty skipped | [PR #6645] [PR #7130] | 2.14.2, 2.15.1 |
| Honeypot captcha visible | Hidden | [PR #16514] | 7.2.0 |
| Radio with no default preselected option `0` | Nothing selected; explicit `"0"` still selects | [PR #16637] | 7.2.0 |
| Default checked every later option | Only matching options checked | [PR #13781] | 5.1.0 |
| **Actions** | | | |
| Results sent to contact with the switch off | Only configured recipients | [PR #5853] | 2.13.0 |
| To empty plus ownerless contact sent nothing | To required | [PR #17137] | 7.2.0 |
| Repost target 500 blocked the visitor | Failure email; only `violations` block | [PR #17461] | unreleased on 7.x (after 7.2.1) |
| Repost sent `A &#38; B` | Original characters | [PR #10872] | 4.2.1 |
| **Response and redirect** | | | |
| API create without `postAction` failed | Defaults to `return` | [PR #13410] | 5.0.4 |
| Redirect with tokens went to 404 | URL or tokens validated | [PR #15596] | 7.0.2 |
| Iframe embed redirected inside the iframe | Parent page redirected | [PR #7515] | 2.16.1 |
| **Rendering and SDK** | | | |
| `$100m` garbled on landing pages | Literal substitution | [PR #5754] | 2.13.0 |
| Async `generate.js` showed nothing | DOM insertion | [PR #6432] | 2.14.1 |
| Embedding created an anonymous contact | No tracking without an auto-fill field | [PR #6122] | 2.14.1 |
| Random incomplete forms | Field collection not mutated during render | [PR #6882] | 2.15.1 |
| Multiple async forms: one not initialised | All initialised | [PR #8935] | 3.0.2 |
| Duplicate submits | In-flight guard | [PR #17138] | 7.2.0 |
| Enter submitted a multi-page form early | Enter ignored except in textarea | [PR #15156] | 7.1.0 |
| Forms from two instances on one page | Both submit to their own instance | [PR #17354] | 7.2.1 |
| Label class attribute gave 500 | Class always an array | [PR #12220] | 5.0.0 |
| **Campaign condition** | | | |
| `3 > 15` was true | Numeric comparison | [PR #7705] | 3.0.1 |
| `&` in value never matched | Matches | [PR #10470] | 4.1.0 |
| **Results and API** | | | |
| Sorting results jumped to form 1 | Stays on current form | [PR #17403] | 7.2.1 |
| Export ran out of memory | Streams | [PR #5792] | 2.13.1 |
| API submissions without permission gave 500 | 403 | [PR #10679] | 4.2.1 |
| API PUT kept omitted actions | Omitted actions deleted | [PR #6892] | 2.15.1 |
| API "no active transaction" | One transaction, proper errors | [PR #15319] | 7.0.0 |

## 4. Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.0–1.4 | "Send form results"; kiosk mode; iframe posting; standalone/campaign types; SDK callbacks; render style; iframe embed | [PR #132], [PR #253], [PR #500], [PR #515], [PR #549], [PR #777], [PR #1055] |
| 2.1–2.9 | Auto-fill; progressive profiling; repost action, page breaks, honeypot; HTML area; date/time | [PR #1363], [PR #2022], [PR #2451], [PR #2986], [PR #3072] |
| 2.10–2.16 | Submissions API; company fields; file upload; E.164 phone; send immediately; form attributes; do-not-submit list; profile image | [PR #4613], [PR #4660], [PR #5082], [PR #5400], [PR #5414], [PR #7687], [PR #7709], [PR #7886] |
| 3.0–4.1 | Submit actions via events; progressive limit and always display; conditional fields | [PR #8186], [PR #8611], [PR #8794] |
| 5.0.0 | Twig templates; `mapped_object`/`mapped_field`; external URL pre-fill; message position; results as report sources | [PR #11898], [PR #11905], [PR #11077], [PR #10726], [PR #11567] |
| 5.1.0 | "Display message" default; per-form language; theme fallback; number precision | [PR #12813], [PR #12814], [PR #13043], [PR #12506] |
| 5.2 | Company lookup field; `{pagelink=}` redirect; HTML labels | [PR #13990], [PR #14099], [PR #14026] |
| 6.0.0 | Read-only fields; builder labels; raw value storage | [PR #14422], [PR #14513], [PR #14604] |
| 7.0.0 | Field width; `hideform`; noindex default; slider; add submitters to segment | [PR #14800], [PR #15118], [PR #15255], [PR #15332], [PR #15328] |
| 7.1.0 | Single form type; stage/owner mapping; free-email block; checkbox min/max; "Update contact"; ARIA errors | [PR #15803], [PR #15267], [PR #15420], [PR #15423], [PR #15690], [PR #15712] |
| 7.2.0 | Global auto-fill switch; mandatory To; submission limit; rating field; cleanup commands; duplicate-submit guard | [PR #16954], [PR #17137], [PR #15396], [PR #15342], [PR #16123], [PR #17138] |
| 7.2.1 | Multi-instance embeds; results sort fix | [PR #17354], [PR #17403] |
| 7.x after 7.2.1 (unreleased) | Existing contact wins merge; repost failure handling | [PR #16426], [PR #17461] |

## 5. Removed, deprecated, replaced

| What | Replaced by | PR | Version |
|---|---|---|---|
| "Create/Update Lead" action | Per-field contact mapping | [PR #444] | 1.1 |
| Static submit-action `callback` | `eventName`, then `ON_EXECUTE_SUBMIT_ACTION` | [PR #2451] [PR #8186] | 2.2, 3.0.0 |
| `LeadEvents::FORM_SUBMIT_REMOVE_DO_NOT_CONTACT` | `ON_EXECUTE_SUBMIT_ACTION` with context `lead.remove_do_not_contact` | [PR #8186] | 3.0.0 |
| PHP form templates | Twig | [PR #11898] [PR #12115] | 5.0.0 |
| `leadField` mapping | `mappedObject` + `mappedField` (`leadField` still accepted) | [PR #11905] [PR #13938] | 5.0.0 |
| Backticking every results column | Backticks on reserved words only | [PR #12272] | 5.0.0 |
| HTML-encoded submission storage | Raw storage, escaped output | [PR #14604] | 6.0.0 |
| Form types and `allowCampaignForm` | One form type; removal in 8.0 | [PR #15803] | deprecated 7.1.0 |
| Optional To on "Send form results" | Required To | [PR #17137] | 7.2.0 |
| Per-field auto-fill as the only control | Global `form_field_autofill` plus field option | [PR #16954] | 7.2.0 |
| Repost non-2xx as validation error | `ResponseParsingException` and failure email | [PR #17461] | unreleased on 7.x (after 7.2.1) |

## 6. Maintainer norms for this area
- Embedded form markup and behaviour are BC: class names, message position and old embeds must keep working. Changes come as options with the old default [PR #8671] [PR #10726] [PR #905].
- Security defaults: escape results, purify user HTML rather than `raw`, never drop the postMessage origin check [PR #3212] [PR #14026] [PR #5558].
- A default that reduces PII exposure must keep existing installs working through a migration [PR #16954].
- Prefer explicit validation over hidden fallback behaviour [PR #17137].
- Form code stays in FormBundle; other bundles are reached through events [PR #11567].
- Bug fixes need tests that fail without the fix, including JS changes; a feature that broke twice gets a regression test [PR #11125] [PR #17138] [PR #10734].
- Test public submissions as a guest; an admin session creates no contact [PR #5349].
- After JS changes run `mautic:assets:generate`, and re-save forms after template changes [PR #9972] [PR #12075].
- Bug fixes target the patch branch and features the next minor [PR #13478] [PR #16179].

## 7. Open questions
- Resolved: kiosk mode turns off progressive profiling and auto-fill in 7.x (behaviour.md B47, B51) [PR #2022] [code: app/bundles/FormBundle/Entity/Field.php:818-821 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:383 @7.x].
- Resolved: [PR #15098] (preview URL panel) was said to be merged by accident. A revert commit (`cd1bbbd7a35`, 2025-07-04) exists only on a contributor branch, and its change did not survive the merge. The panel is in 7.0.0, 7.2.1 and the 7.x head [code: app/bundles/FormBundle/Resources/views/Form/details.html.twig:334-370 @7.x].
- Resolved: the [PR #16123] commands are `mautic:forms:delete-results-table` and `mautic:forms:delete-orphan-form-submission-records-from-form-results-table`. They first ship in 7.2.0, so the "before 7.x" note in version-notes.md is wrong [code: app/bundles/FormBundle/Command/DeleteOrphanFormResultsTableCommand.php:24 @7.x].
- Resolved: the [PR #17137] required To applies only where `addToBcBccFields($builder, true)` is called. In 7.x that is only `SubmitActionEmailType` [code: app/bundles/FormBundle/Form/Type/SubmitActionEmailType.php:128 @7.x].
- Resolved: `noIndex` defaults to true for new forms since 7.0.0 [PR #15255] [code: app/bundles/FormBundle/Entity/Form.php:178 @7.x].
- Conflict with behaviour.md: [PR #6727] says results and exports show dates in the user's timezone. behaviour.md B102 says export dates are UTC. behaviour.md wins [PR #6727].
- Conflict with behaviour.md: [PR #17354] scopes the SDK load guard per instance. behaviour.md B41 and `_script.html.twig` show one global `MauticSDKLoaded` guard. behaviour.md wins; check `mautic-form-src.js` [PR #17354].
- Conflict with behaviour.md: [PR #13599] speaks of aliases truncated to 24 characters. behaviour.md B8 says 25 (`cleanAlias` can trim a trailing character). behaviour.md wins [PR #13599].
- [PR #12272]: whether API-created forms get the `f_` prefix on reserved words [PR #12272].
- [PR #11513]: condition values with `'` or `&` fail for option lists typed in the Properties tab [PR #11513].
- [PR #802]: whether `0` is shown in the timeline [PR #802].
- [PR #17137]: whether "send to owner" also sends to the To address [PR #17137].
- [PR #16954]: what happens when the migration cannot write `config/local.php` [PR #16954].
- [PR #14099]: deleting a page used by `{pagelink=}` is not prevented [PR #14099].
- [PR #15340]: the results Close button returns to the list, not the form [PR #15340].

## 8. Coverage
The inputs cover 383 PRs in 5 chunks: 136 (2015–2018), 86 (2017–2021, plus #10238 merged 2024), 78 (2021–2025), 59 (2025–2026) and 24 (2026-06 to 2026-09).
Of these, about 332 are substantive; the rest are merges forward, test-only or refactor PRs.
A further 869 noise PRs (dependency bumps, translations, CI) were excluded upstream before chunking.
