# Forms behaviour specification (Mautic 7.x)

Authoritative for 7.x at commit 419a08a9b35. Code wins over docs where they disagree; each disagreement is listed in
SKILL.md "Pitfalls". Terms: a **Form** is a Mautic-hosted web form; a **Field** is one input; a **Submit action** (UI:
"Form action") runs after a valid submission; the **post action** (UI: "Successful Submit Action") decides what the
visitor sees; a **Contact** is a person record (code `Lead`); **Kiosk mode** turns off visitor tracking;
**progressive profiling** hides fields whose values are already known.

## Contents
- A. Form lifecycle and builder (B1–B19)
- B. Fields and field options (B20–B27)
- C. Rendering and embedding (B28–B40)
- D. Client-side SDK and JS hooks (B41–B46)
- E. Progressive profiling, auto-fill and kiosk mode (B47–B54)
- F. Submission pipeline and validation (B55–B70)
- G. Contact and company identification (B71–B80)
- H. Submit actions (B81–B86)
- I. Post-submit response (B87–B92)
- J. Campaigns, points, webhooks, timeline, counts (B93–B99)
- K. Results, export and API (B100–B108)
- L. Landing pages, tokens and A/B (B109–B111)
- M. Known performance and race behaviour (B112–B118)

## A. Form lifecycle and builder

B1. A new form gets an alias from `cleanAlias(name, '', 10)` (max 10 characters) when none is set; the alias is never regenerated, so the results-table name stays stable. [code: app/bundles/FormBundle/Model/FormModel.php:323-326 @7.x] [code: app/bundles/FormBundle/Controller/Api/FormApiController.php:138-143 @7.x]

B2. Every form save back-fills deprecated `leadField` from `mappedField` and the reverse (object inferred as `company` when the alias starts with `company` and is not exactly `company`, else `contact`), persists, creates the results table or adds missing columns, and regenerates cached HTML. [code: app/bundles/FormBundle/Model/FormModel.php:319-339 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:1085-1098 @7.x]

B3. The builder keeps fields and actions in the PHP session (`mautic.form.<sessionId>.fields.modified|deleted`, `.actions.modified|deleted`); nothing reaches the database until the form is saved. New items get ids `new<sha1>`. [code: app/bundles/FormBundle/Controller/FormController.php:309-317 @7.x] [code: app/bundles/FormBundle/Controller/FieldController.php:103-151 @7.x]

B4. On save the controller persists the form through the repository (no events), then actions, then calls `FormModel::saveEntity` so `FORM_PRE_SAVE`/`FORM_POST_SAVE` fire once. Session ids used by action `mappedFields` and by conditional `parent` are translated to real ids. [code: app/bundles/FormBundle/Controller/FormController.php:350-362 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:251-276 @7.x] [code: app/bundles/FormBundle/EventListener/FormConditionalSubscriber.php:35-47 @7.x]

B5. A form needs at least one field (error `mautic.form.form.fields.notempty`). A new form starts with a `button` field aliased `submit`, which cannot be deleted in the builder. [code: app/bundles/FormBundle/Controller/FormController.php:330-338 @7.x] [code: app/bundles/FormBundle/Controller/FormController.php:439-451 @7.x] [code: app/bundles/FormBundle/Resources/views/Builder/_field_wrapper.html.twig:28 @7.x]

B6. Field order is reassigned 1..n from the session order on save; rendering sorts by order, then id. Reordering is an AJAX call that rewrites the session array. [code: app/bundles/FormBundle/Model/FormModel.php:169-205 @7.x] [code: app/bundles/FormBundle/Controller/AjaxController.php:34-54 @7.x]

B7. A field alias equal to the generated form name is prefixed `f_` to avoid HTML id collisions. [code: app/bundles/FormBundle/Model/FormModel.php:185-188 @7.x]

B8. Field aliases come from `cleanAlias(label, 'f_', 25)`, get a numeric suffix when already used in the form, and get `f_` when they collide with `message`, `error`, `id`, `return`, `name`, `messenger`. Existing aliases cannot be edited in the UI. [code: app/bundles/FormBundle/Model/FieldModel.php:101-126 @7.x] [code: app/bundles/FormBundle/Form/Type/FieldType.php:216-231 @7.x]

B9. Alias uniqueness is enforced in code only; there is no database unique index on `form_fields.alias`. [code: app/bundles/FormBundle/Model/FieldModel.php:101-126 @7.x] [code: app/bundles/FormBundle/Controller/Api/FormApiController.php:239-245 @7.x]

B10. A captcha field is forced required only when a question/answer is configured; with empty `properties.captcha` it is a honeypot. [code: app/bundles/FormBundle/Controller/FieldController.php:121-124 @7.x]

B11. Deleting a field deletes its uploaded files and the entity on form save; `FIELD_POST_DELETE` then drops the results column, so that field's stored results are lost. [code: app/bundles/FormBundle/Model/FormModel.php:213-243 @7.x] [code: app/bundles/FormBundle/EventListener/FormFieldSubscriber.php:29-36 @7.x]

B12. After `FORM_POST_SAVE`, conditional child fields whose parent no longer exists are deleted. [code: app/bundles/FormBundle/EventListener/FormConditionalSubscriber.php:49-59 @7.x]

B13. Deleting a form removes its upload directory and drops `form_results_<id>_<alias>`; fields, actions and submissions go by `ON DELETE CASCADE`. Batch delete does the same per id. [code: app/bundles/FormBundle/Model/FormModel.php:560-595 @7.x] [code: app/bundles/FormBundle/Entity/Submission.php:76 @7.x]

B14. Cloning copies fields and actions, sets `isPublished=false`, and only persists when the clone is saved. [code: app/bundles/FormBundle/Controller/FormController.php:856-896 @7.x]

B15. Opening the edit page locks the form; cancel unlocks; a locked form cannot be edited or deleted by another user. [code: app/bundles/FormBundle/Controller/FormController.php:561-563 @7.x] [code: app/bundles/FormBundle/Controller/FormController.php:1007-1008 @7.x]

B16. Saving a form clears the stored results-list order and filter session keys. [code: app/bundles/FormBundle/Controller/FormController.php:674-677 @7.x]

B17. "Rebuild HTML" batch action regenerates cached HTML (needs `editown|editother`); cached HTML is also rebuilt when a contact select/multiselect field used by a `syncList` form field is saved. [code: app/bundles/FormBundle/Controller/FormController.php:1120-1181 @7.x] [code: app/bundles/FormBundle/EventListener/CustomFieldSubscriber.php:35-61 @7.x]

B18. The audit log records `create`/`update` with the form change set (field and action changes folded in) and `delete` with the name; fields and actions have no audit entries of their own. [code: app/bundles/FormBundle/EventListener/FormSubscriber.php:56-90 @7.x] [code: app/bundles/FormBundle/Entity/Form.php:559-581 @7.x]

B19. Post action `message` and `hideform` require message text; `redirect` requires a URL that is valid after `{pagelink=}`, `{formfield=}`, `{contactfield=}` are replaced by dummy data; `progressiveProfilingLimit` must be > 0 when set. [code: app/bundles/FormBundle/Entity/Form.php:311-346 @7.x] [code: app/bundles/FormBundle/Validator/Constraint/IsPostActionRedirectUrlValidator.php:22-57 @7.x]

## B. Fields and field options

B20. Builder field types are the `FormFieldHelper::$types` keys plus plugin fields from `FormBuilderEvent::addFormField` (core ships only `plugin.loginSocial`, when MauticSocialBundle is published). Full table: code-map.md section 4. [code: app/bundles/FormBundle/Helper/FormFieldHelper.php:23-74 @7.x] [code: plugins/MauticSocialBundle/EventListener/FormSubscriber.php:27-45 @7.x]

B21. View-only types `button`, `captcha`, `freetext`, `freehtml`, `pagebreak`, and any custom field with `builderOptions.addSaveResult === false`, get no results column, are not saved and are not exported. [code: app/bundles/FormBundle/Model/FormModel.php:649-655 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:228-231 @7.x]

B22. Builder defaults: `showLabel=true`, `isRequired=false`, `saveResult=true`, `showWhenValueExists=true`, `alwaysDisplay=false`, `isAutoFill=false`, `isReadOnly=false`, `fieldWidth='100%'`; an empty label becomes the translated type name; mapped object defaults to `contact`; a new email field is pre-mapped. [code: app/bundles/FormBundle/Form/Type/FieldType.php:179-198 @7.x] [code: app/bundles/FormBundle/Form/Type/FieldType.php:393-542 @7.x]

B23. Per-type options differ: `freetext`/`freehtml` have no help, default, required, mapping, save-result or behaviour options; `hidden` has no label/help/required/width; `captcha` has no show-label/required/default/mapping/behaviour; `file` has no default or behaviour; `rating` has no default; `slider` has no required toggle; conditional children have no behaviour tab. [code: app/bundles/FormBundle/Form/Type/FieldType.php:104-169 @7.x]

B24. A contact or company field can be mapped to only one top-level form field: the mapped-field dropdown excludes fields already mapped in the builder session. [code: app/bundles/FormBundle/Form/Type/FieldType.php:495-500 @7.x] [code: app/bundles/FormBundle/Collector/AlreadyMappedFieldCollector.php:21-77 @7.x]

B25. With `properties.syncList`, a select/radio/checkbox field mapped to a list-type contact field (select, multiselect, lookup, boolean, country, region, timezone, locale) takes its options from that contact field at load time. [code: app/bundles/FormBundle/Model/FormModel.php:110-125 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:1005-1067 @7.x]

B26. Conditional parents may be `select`, `country`, `checkboxgrp` or `radiogrp`; conditions are `expr` `in` or `notIn` plus an "any value" switch. [code: app/bundles/FormBundle/Enum/ConditionalFieldEnum.php:12 @7.x] [code: app/bundles/FormBundle/Form/Type/FormFieldConditionType.php:73-78 @7.x]

B27. Blacklisted extensions (`php`, `sh` by default) cannot be allowed on a file field. [code: app/bundles/FormBundle/Validator/Constraint/FileExtensionConstraintValidator.php:22-37 @7.x]

## C. Rendering and embedding

B28. Once the submission limit is reached, `getContent()` returns the limit message (through `InputHelper::strict_html`) instead of the form. [code: app/bundles/FormBundle/Model/FormModel.php:347-353 @7.x]

B29. Cached HTML is used unless the form uses progressive profiling; then HTML is regenerated per request using up to 200 of the tracked contact's submissions. [code: app/bundles/FormBundle/Model/FormModel.php:373-405 @7.x]

B30. `usesProgressiveProfiling()` is true when not in kiosk mode and either a profiling limit is set or any field has `showWhenValueExists === false` or `showAfterXSubmissions > 0`. [code: app/bundles/FormBundle/Entity/Form.php:888-915 @7.x]

B31. HTML structure: wrapper `#mauticform_wrapper_<name>`; `<form method="post" action=".../form/submit?formId=ID" id="mauticform_<name>" data-mautic-form="<name>" enctype="multipart/form-data">`; page wrappers `div.mauticform-page-wrapper[data-mautic-form-page=N]`; field containers `div#mauticform_<name>_<alias>.mauticform-row`; inputs `#mauticform_input_<name>_<alias>` named `mauticform[<alias>]` (`[]` for multiple); hidden `mauticform[formId]`, `mauticform[return]`, `mauticform[formName]`. `formAttributes` is injected raw into the `<form>` tag. [code: app/bundles/FormBundle/Resources/views/Builder/form.html.twig:17-139 @7.x] [code: app/bundles/FormBundle/Resources/views/Field/text.html.twig:29-158 @7.x]

B32. `<name>` is the lowercase transliterated alphanumeric form name, or `form-<id>` if that is empty. [code: app/bundles/FormBundle/Entity/Form.php:867-884 @7.x]

B33. `pagebreak` fields split the form into pages; the last page wrapper has `data-mautic-form-pagebreak-lastpage`. [code: app/bundles/FormBundle/Model/FormModel.php:483-522 @7.x]

B34. `showLabel=false` omits the label; label and help text pass through `purify_allow_target_blank`; required fields render `span.mauticform-errormsg` with the custom or translated generic message in the form language. [code: app/bundles/FormBundle/Resources/views/Field/text.html.twig:112-157 @7.x]

B35. A honeypot captcha renders in a `.mauticform-honeypot` container hidden by inline CSS and is not required; a question captcha is a required text input. [code: app/bundles/FormBundle/Resources/views/Field/captcha.html.twig:4-21 @7.x] [code: app/bundles/FormBundle/Resources/views/Builder/form.html.twig:32-35 @7.x]

B36. Conditional children render with `mauticform-field-hidden`, `data-mautic-form-show-on="<parentAlias>:v1|v2"` (or `*` for any value unless `notIn`) and `data-mautic-form-expr`; the SDK shows them on matching parent values and sets `data-validate-disable` on hidden ones. Children of a `hidden` parent are not rendered. [code: app/bundles/FormBundle/Resources/views/Field/text.html.twig:96-110 @7.x] [code: app/assets/js/mautic-form-src.js:314-375 @7.x]

B37. The details page offers automatic JS (`<script src="/form/generate.js?id=ID">`), iframe (`<iframe src="/form/ID">`), manual copy (HTML + `getFormScript()`) and a self-hosted script variant. [code: app/bundles/FormBundle/Resources/views/Form/details.html.twig:382-440 @7.x]

B38. `generate.js` returns an empty body for unpublished forms, is a non-trackable request, and inserts the HTML with `document.currentScript.insertAdjacentHTML` (scripts appended to `<head>`), falling back to `document.write`. [code: app/bundles/FormBundle/Controller/PublicController.php:588-610 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:664-700 @7.x]

B39. `renderStyle` defaults to true for a new form; when true the theme's `_style`/`style` template is injected before the HTML; theme templates can override `Builder/form.html.twig` and `Field/<type>.html.twig`. [code: app/bundles/FormBundle/Form/Type/FormType.php:158-169 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:422-440 @7.x]

B40. Query parameters named like a field alias are URL-encoded and injected as field values on server-rendered paths (page token, preview, `TokenHelper`); the SDK also fills empty non-hidden inputs from `window.location.search` with tags stripped. [code: app/bundles/FormBundle/Model/FormModel.php:734-749 @7.x] [code: app/assets/js/mautic-form-src.js:1026-1041 @7.x]

## D. Client-side SDK and JS hooks

B41. The loader registers the Mautic origin in `window.MauticDomains`, loads `media/js/mautic-form.js` once (`MauticSDKLoaded` guard), and sets `MauticLang.submittingMessage`. [code: app/bundles/FormBundle/Resources/views/Builder/_script.html.twig:1-35 @7.x]

B42. For each `form[data-mautic-form]` the SDK targets a hidden iframe `mauticiframe_<name>`, appends `mauticform[messenger]=1`, collects required fields from `[data-validate]`, and wires show-on rules and pagination. On submit it validates required fields (checked options, basic `@`/`.` email check, non-empty), sets `mauticform[return]` to `document.URL`, disables submit buttons and posts into the iframe. [code: app/assets/js/mautic-form-src.js:215-312 @7.x] [code: app/assets/js/mautic-form-src.js:551-702 @7.x]

B43. The server answers messenger posts with `messenger.html.twig`, which calls `parent.postMessage(json, '*')`. The SDK accepts messages only from http(s) origins equal to a `MauticDomains` entry or a loaded form's `action` origin. It then handles `download`, `redirect` (`window.top.location`), `validationErrors` (marks fields, jumps to the first page with an error), `errorMessage`, `success` with `hideform`/`successMessage`, adds `mauticform-post-success`, and resets the form. Download plus redirect waits 2 s. [code: app/bundles/FormBundle/Resources/views/messenger.html.twig @7.x] [code: app/assets/js/mautic-form-src.js:759-827 @7.x] [code: app/assets/js/mautic-form-src.js:946-1000 @7.x]

B44. `MauticFormCallback[<formName>]` hooks: `onValidate`, `onValidateStart`, `onValidateEnd`, `onValidateField`, `onErrorMark`, `onErrorClear`, `onResponse`, `onResponseStart`, `onResponseEnd`, `onSubmitButtonDisable`, `onSubmitButtonEnable`, `onShowNextPage`, `onShowPreviousPage`, `onMessageSet`. A non-null return from `onValidate`/`onResponse` replaces default handling. [code: app/assets/js/mautic-form-src.js:200-213 @7.x] [code: app/assets/js/mautic-form-src.js:443-463 @7.x] [code: app/assets/js/mautic-form-src.js:842 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/form_hooks/validation_hooks.html]

B45. `onValidate` returning true skips default validation and submits; false prevents submission; null continues default validation. `onValidateStart` is skipped when `onValidate` returned true; `onResponseStart`/`onResponseEnd` are skipped when `onResponse` returns true. [devdocs: https://devdocs.mautic.org/en/7.2/form_hooks/validation_hooks.html] [devdocs: https://devdocs.mautic.org/en/7.2/form_hooks/response_hooks.html]

B46. Hooks work for automatic-JS and manual embeds, not for iframes; declare `MauticFormCallback` before the form loads. [devdocs: https://devdocs.mautic.org/en/7.2/form_hooks/getting_started.html]

## E. Progressive profiling, auto-fill and kiosk mode

B47. In kiosk mode `showForContact()` returns true for every field: progressive profiling is off. [code: app/bundles/FormBundle/Entity/Field.php:818-821 @7.x]

B48. `showAfterXSubmissions > 0` (and not `alwaysDisplay`) hides the field until the contact has at least X earlier submissions of this form. [code: app/bundles/FormBundle/Entity/Field.php:823-826 @7.x]

B49. `showWhenValueExists === false` (and not `alwaysDisplay`) hides the field when any earlier submission by the contact has a non-empty value for the alias or the mapped contact field has a value, unless the field is `isAutoFill`. [code: app/bundles/FormBundle/Entity/Field.php:828-847 @7.x]

B50. `progressiveProfilingLimit` caps the number of non-view-only fields displayed: `alwaysDisplay` fields count first; others show while `displayed + (alwaysDisplayTotal - alwaysDisplayShown) < limit`. Rendering and submission both drive `DisplayManager`, so required errors for fields not displayed are dropped. [code: app/bundles/FormBundle/ProgressiveProfiling/DisplayManager.php:21-74 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:308-319 @7.x]

B51. Auto-fill runs only when `form_field_autofill` is true and the form is not in kiosk mode. It runs inside `getFormHtml()`, so it applies to every server-rendered path: `generate.js`, `/form/ID`, `/form/embed/ID`, the `{form=ID}` token. It does not apply to self-hosted static HTML. Fields with `isAutoFill` mapped to contact/company are prefilled from the tracked contact and primary company. With `isReadOnly` the input gets `readonly`. [code: app/bundles/FormBundle/Model/FormModel.php:372-388 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:754-806 @7.x] [code: app/bundles/FormBundle/Helper/FormFieldHelper.php:162-183 @7.x]

B52. Top-level auto-fill fields with a known value render as `hidden` inputs when `showWhenValueExists` is false. [code: app/bundles/FormBundle/Resources/views/Builder/form.html.twig:56-69 @7.x]

B53. Kiosk mode on submit ignores the tracked contact. It starts from a fresh contact. If a unique-identifier match exists, that contact is used without merging. No IP is associated, and `setSystemContact()` replaces `setTrackedContact()`, so no tracking cookie is set. [code: app/bundles/FormBundle/Model/SubmissionModel.php:935-955 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:1042-1050 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:1162-1168 @7.x]

B54. Docs: progressive profiling needs a server-rendered embed (JS, iframe, preview, landing page) and inspects at most 200 earlier submissions. [docs: https://docs.mautic.org/en/7.2/components/forms.html#limits-of-progressive-profiling]

## F. Submission pipeline and validation

B55. `/form/submit` accepts POST only (403 otherwise). `post` = `request['mauticform']`. `return` = posted `mauticform[return]`, else `HTTP_REFERER`, with `mauticError`/`mauticMessage` removed. Messenger mode = `post.messenger` set; AJAX = query `ajax`. [code: app/bundles/FormBundle/Controller/PublicController.php:54-112 @7.x]

B56. Pre-checks run in this order:
1. A missing or unknown form gives "unavailable".
2. A form whose publish-up date has not arrived (`pending`) gives an error with the publish-up date.
3. An expired form gives an error with the publish-down date.
4. Any other non-published state gives "unavailable".
5. The form is reloaded. If the submission limit is reached, the owner is notified and the limit message (or the default) is returned. [code: app/bundles/FormBundle/Controller/PublicController.php:138-245 @7.x]

B57. `saveSubmission()` order: (1) build `Submission` (now, form, page from `mauticpage`, IP, referer); (2) validate each field; (3) get tracked contact and prune progressive-profiling errors; (4) on any error return errors and persist nothing; (5) `createLeadFromSubmit()` if contact/company fields are mapped; (6) ensure contact is managed, read tracking id; (7) upload files; (8) persist submission and results row; (9) transform file values to URLs; (10) run submit actions in order; (11) update contact with file URLs; (12) add contact to published campaigns sourcing this form; (13) dispatch `FORM_ON_SUBMIT`; (14) return callback or submission event. [code: app/bundles/FormBundle/Model/SubmissionModel.php:121-407 @7.x]

B58. Captcha with an answer must be non-blank and equal to it; a honeypot must be blank. The error is the field's `errorMessage` or the translated default. Captcha values are never saved. [code: app/bundles/FormBundle/Model/SubmissionModel.php:181-189 @7.x] [code: app/bundles/FormBundle/Helper/FormFieldHelper.php:106-149 @7.x]

B59. An empty required value yields the field's `validationMessage` or `mautic.form.field.generic.validationfailed`. A required field with `showWhenValueExists=false` that was not posted at all is skipped. [code: app/bundles/FormBundle/Model/SubmissionModel.php:205-226 @7.x]

B60. A conditional field is processed only when `showForConditionalField($post)` is true: parent value present and (any + non-empty, or `notIn` → not in list, else in list). Otherwise it is skipped entirely (no required error, no result). [code: app/bundles/FormBundle/Entity/Field.php:863-895 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:201-203 @7.x]

B61. Non-empty values are filtered by type: `email`→email, `url`→url, `number`/`slider`→float, `checkboxgrp`/`radiogrp`/`select`→raw, others→string; custom fields use their `valueFilter`. [code: app/bundles/FormBundle/Helper/FormFieldHelper.php:23-101 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:234-261 @7.x]

B62. `email` gets Symfony `Email`, `url` gets Symfony `Url`; then every validator registered for the field type and for `form` is dispatched as a `ValidationEvent`; the first failure wins. [code: app/bundles/FormBundle/Model/SubmissionModel.php:253-267 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:1205-1231 @7.x]

B63. Core validators: `tel` `international`; `email` `donotsubmit` (fnmatch on `do_not_submit_emails`) and `blockfreeemail`; `checkboxgrp` min/max. Core has no regex or length validator and no reCAPTCHA. [code: app/bundles/FormBundle/EventListener/FormValidationSubscriber.php:35-179 @7.x]

B64. File fields read `request->files['mauticform'][alias]`, check size (`allowed_file_size`, MB) and extension (`allowed_file_extensions`); a missing file errors only when required; the stored value is the final file name under `<form_upload_dir>/<formId>/<fieldId>/`; JPEGs are EXIF-rotated. [code: app/bundles/FormBundle/Model/SubmissionModel.php:190-199 @7.x] [code: app/bundles/FormBundle/Validator/UploadFieldValidator.php:27-49 @7.x] [code: app/bundles/FormBundle/Helper/FormUploader.php:102-151 @7.x]

B65. `companyLookup` posts a company id, stores the company name and links the company. Arrays are stored joined by `, `. `{formfield=alias}` tokens resolve option labels from `properties.list`. [code: app/bundles/FormBundle/Model/SubmissionModel.php:276-293 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:1233-1245 @7.x]

B66. `saveResult=false` fields are validated and mapped but their value is not written to the results row; the column still exists. [code: app/bundles/FormBundle/Model/SubmissionModel.php:291-293 @7.x] [code: app/bundles/FormBundle/Entity/SubmissionRepository.php:60-71 @7.x]

B67. The results insert quotes aliases that are SQL reserved words. [code: app/bundles/FormBundle/Entity/SubmissionRepository.php:24-47 @7.x]

B68. Each submission stores form, IP, contact, tracking id, `date_submitted` (UTC), referer and page. UTM values are stored only by the "Record UTM tags" action. [code: app/bundles/FormBundle/Entity/Submission.php:63-98 @7.x] [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:248-286 @7.x]

B69. Files are uploaded before actions run. An action throwing `ValidationException` deletes the submission and its files and returns the violations as field errors. [code: app/bundles/FormBundle/Model/SubmissionModel.php:340-374 @7.x]

B70. `validateFieldValue` runs twice for non-empty core values, and `form`-level validators run once per field. [code: app/bundles/FormBundle/Model/SubmissionModel.php:257 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:264 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:1213 @7.x]

## G. Contact and company identification

B71. Only fields mapped to `contact` or `company` feed contact matching; with none mapped, the submission attaches to the tracked contact (possibly null) and no contact is created or updated. [code: app/bundles/FormBundle/Model/SubmissionModel.php:269-274 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:327-331 @7.x]

B72. Non-kiosk submissions start from `ContactTracker::getContact()`, which creates an anonymous contact and cookies for an unknown visitor. Unique-identifier fields (typically email) with non-empty values are looked up excluding the current contact. [code: app/bundles/FormBundle/Model/SubmissionModel.php:941-975 @7.x] [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:49-78 @7.x]

B73. If a match is found, it is used as-is in these cases: kiosk mode; the found contact's unique fields conflict case-insensitively with the tracked contact's (both non-empty); or the tracked contact has no id. Otherwise the tracked contact is merged into the found one. The found contact keeps its id and the anonymous contact is deleted. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1027-1066 @7.x]

B74. When submitted unique values conflict with the current contact's, a new contact is created instead of overwriting. Example: the tracked contact has email A and the form submits email B, which matches nobody. The result is a new contact B. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1068-1089 @7.x]

B75. Values apply through `LeadModel::setFieldValues($lead, $data, false, true, true)`. Empty submitted values never clear existing values. Invalid values are dropped. Non-empty values always overwrite; there is no "only if empty" option. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1110 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:597-668 @7.x]

B76. Pseudo-fields: `stagebyname` sets the stage and logs it (warning if missing); `ownerbyemail`/`ownerbyid` set the owner when a user is found. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1116-1151 @7.x]

B77. The contact gets `lastActive`, a `LeadManipulator('form','submission',id,name)`, is saved, then (non-kiosk) becomes the tracked contact with cookies and gets the request IP. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1092-1168 @7.x]

B78. A `companyLookup` field links its company directly; otherwise company-mapped values go through `IdentifyCompanyHelper::identifyLeadsCompany`, which finds or creates the company, updates it, sets it primary and logs the change. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1170-1197 @7.x]

B79. Contact merges move all submissions to the winner (`LEAD_POST_MERGE`). [code: app/bundles/FormBundle/EventListener/LeadSubscriber.php:85-88 @7.x]

B80. `ContactTracker::getContact()` returns null for logged-in Mautic users and `Blocked-Tracking` cookies, so such test submissions get `lead_id` NULL unless fields are mapped. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:51-60 @7.x]

## H. Submit actions

B81. Actions run in `action_order`, only if their type is still registered; each is dispatched separately on its `eventName` with the action set on the `SubmissionEvent`. [code: app/bundles/FormBundle/Model/SubmissionModel.php:915-925 @7.x]

B82. Contact actions act on `ContactTracker::getContact()` (the contact resolved in B77), except `lead.remove_do_not_contact`, which uses `$event->getLead()`. [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:164-373 @7.x]

B83. `email.send.lead` ignores DNC (`ignoreDNC => true`). [code: app/bundles/EmailBundle/EventListener/FormSubscriber.php:83-87 @7.x]

B84. `form.repost` POSTs non-button values (keys remappable), `mautic_contact` and `mautic_form` with `X-Forwarded-For` and optional `authorization_header`, 15 s timeout. A `redirect` in the response becomes a redirect. `error`/`errors`/non-2xx raises `ResponseParsingException`. `violations` raise `ValidationException` (submission deleted). On failure `failure_email` receives the data with passwords masked. [code: app/bundles/FormBundle/EventListener/FormSubscriber.php:191-351 @7.x]

B85. `asset.download` registers callback `asset.download_file`, which returns `download` in messenger mode or a themed page with the link; the URL carries `lead` and `channel=form`. [code: app/bundles/AssetBundle/EventListener/FormSubscriber.php:63-150 @7.x]

B86. Emails sent by earlier actions are not rolled back when a later action rejects the submission. [code: app/bundles/FormBundle/Model/SubmissionModel.php:363-374 @7.x]

## I. Post-submit response

B87. Post-submit callbacks are dispatched after `saveSubmission`; a listener that stops propagation and sets a response short-circuits (direct `Response` in standard mode, JSON data in messenger mode). [code: app/bundles/FormBundle/Controller/PublicController.php:299-328 @7.x] [code: app/bundles/FormBundle/Controller/PublicController.php:408-426 @7.x]

B88. Messenger/AJAX JSON keys: `success`, `validationErrors` or `errorMessage`, `results`, `redirect`, `hideform`, `successMessage` (joined `<br /><br />`), `download`, `formName`. `?ajax=1` returns `JsonResponse`; `/form/submit/ajax` adds `message`/`type`. [code: app/bundles/FormBundle/Controller/PublicController.php:334-426 @7.x] [code: app/bundles/FormBundle/Controller/AjaxController.php:138-160 @7.x]

B89. Standard POST: errors → redirect to `return` with `?mauticError=<html>#<alias>`; `redirect` → 302 to the URL; `return` → 302 back (+`mauticMessage` if set); `message`/`hideform` or no return URL → session message and `/form/message` (theme `message.html.twig`). [code: app/bundles/FormBundle/Controller/PublicController.php:432-514 @7.x]

B90. `hideform` behaves as `message` on the standard path; only the JS path hides the form. [code: app/bundles/FormBundle/Controller/PublicController.php:378-390 @7.x]

B91. `{formfield=alias}`, `{contactfield=alias}` (resolved contact) and `{pagelink=ID}` are replaced in the redirect URL and message after success. [code: app/bundles/FormBundle/Controller/PublicController.php:639-661 @7.x]

B92. The API default `postAction` is `return`; the entity default is `message`. [code: app/bundles/FormBundle/Controller/Api/FormApiController.php:336-354 @7.x] [code: app/bundles/FormBundle/Entity/Form.php:107 @7.x]

## J. Campaigns, points, webhooks, timeline, counts

B93. Since 7.1 every form can be a campaign source and trigger campaigns; form type is deprecated. [code: app/bundles/FormBundle/Entity/Form.php:778-800 @7.x] [docs: https://docs.mautic.org/en/7.2/components/forms.html#creating-a-new-form]

B94. A contact submitting a form that is a source of a published campaign is added via `MembershipManager::addContact` before `FORM_ON_SUBMIT`. [code: app/bundles/FormBundle/Model/SubmissionModel.php:383-389 @7.x]

B95. Campaign decision `form.submit` fires in real time through `RealTimeExecutioner`; condition `form.field_value` compares stored results with `=,!=,gt,gte,lt,lte,like,!like,startsWith,endsWith,contains`. [code: app/bundles/FormBundle/EventListener/CampaignSubscriber.php:45-139 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:808-869 @7.x]

B96. Point action `form.submit` fires on `FORM_ON_SUBMIT`; webhook `mautic.form_on_submit` uses serializer groups `submissionDetails, ipAddress, leadList, pageList, formList`. [code: app/bundles/FormBundle/EventListener/PointSubscriber.php:47-50 @7.x] [code: app/bundles/FormBundle/EventListener/WebhookSubscriber.php:44-59 @7.x]

B97. The timeline shows `form.submitted` with referer and every non-empty saved value (files as links). [code: app/bundles/FormBundle/EventListener/LeadSubscriber.php:37-83 @7.x]

B98. `forms.submission_count` changes atomically on submission persist/remove, never below 0; deleting submissions below the limit reopens the form. [code: app/bundles/FormBundle/EventListener/SubmissionSubscriber.php:30-46 @7.x] [code: app/bundles/FormBundle/Entity/FormRepository.php:290-313 @7.x] [docs: https://docs.mautic.org/en/7.2/components/forms.html#submission-limits]

B99. Form details show a submissions chart, total and unique (`COUNT(DISTINCT lead_id)`) counts and the audit log. [code: app/bundles/FormBundle/Controller/FormController.php:226-275 @7.x]

## K. Results, export and API

B100. The results list joins the results table with `form_submissions` and `ip_addresses`. It shows only `save_result=1`, non-view-only columns. Default order is `date_submitted DESC`, and filters persist in the session. [code: app/bundles/FormBundle/Controller/ResultController.php:64-208 @7.x] [code: app/bundles/FormBundle/Entity/SubmissionRepository.php:49-179 @7.x]

B101. Deleting results needs `editown|editother` and removes files, the results row and the submission (count decremented). [code: app/bundles/FormBundle/Controller/ResultController.php:345-400 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:436-467 @7.x]

B102. Export (`csv`, `html`, `xlsx`) needs admin or `form:export:enable`; columns: submission id, contact id, date (UTC), IP, referer, saved field labels. [code: app/bundles/FormBundle/Controller/ResultController.php:286-343 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:494-594 @7.x]

B103. "Add to segment" from results uses the distinct contact ids of the filtered results. [code: app/bundles/FormBundle/Controller/ResultController.php:463-553 @7.x]

B104. File downloads are public only when the field's `public` property is set; otherwise `viewown|viewother` is required. [code: app/bundles/FormBundle/Controller/ResultController.php:210-284 @7.x]

B105. API create/edit: fields without `id` are new; aliases are cleaned and must be unique in the request (400); each field and action is validated through its form type (400); `PUT` removes fields/actions absent from the payload, `PATCH` keeps them; unknown field id → 404. [code: app/bundles/FormBundle/Controller/Api/FormApiController.php:132-293 @7.x]

B106. The submissions API is read-only (list, by id, by contact). Results are flattened to `alias => value`. Permission is checked on the parent form. There is no API endpoint for posting a submission; clients POST to `/form/submit`. [code: app/bundles/FormBundle/Controller/Api/SubmissionApiController.php:60-143 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html]

B107. `DELETE /forms/{id}/fields/delete` and `/actions/delete` require `editown|editother`. [code: app/bundles/FormBundle/Controller/Api/FormApiController.php:73-128 @7.x]

B108. `form_results_data_sources=true` turns each results table into a report source. [code: app/bundles/FormBundle/EventListener/ReportSubscriber.php:132-171 @7.x]

## L. Landing pages, tokens and A/B

B109. `{form=ID}` in a landing page becomes the form HTML with hidden `mauticform[mauticpage]` (published), an "unpublished" notice for users who may view it, or nothing. [code: app/bundles/FormBundle/EventListener/PageSubscriber.php:65-102 @7.x] [code: app/bundles/FormBundle/Helper/TokenHelper.php:18-54 @7.x]

B110. Submission rate is an A/B winner criterion (`form.submissions`) for pages and emails. [code: app/bundles/FormBundle/EventListener/DetermineWinnerSubscriber.php:30-120 @7.x]

B111. Unpublished forms are hidden from JS embeds; manually copied HTML still renders but submissions are refused. [docs: https://docs.mautic.org/en/7.2/components/forms.html#creating-a-new-form] [code: app/bundles/FormBundle/Controller/PublicController.php:138-190 @7.x]

## M. Known performance and race behaviour

B112. The submission-limit check reads `submission_count` without a lock, so concurrent submissions can exceed the limit by one or more. [code: app/bundles/FormBundle/Controller/PublicController.php:204-212 @7.x]

B113. `setFieldValues(..., fetchSocialProfiles=true)` can call integration profile lookups during the public request. [code: app/bundles/LeadBundle/Model/LeadModel.php:553-569 @7.x]

B114. Progressive-profiling forms bypass the cache and query up to 200 submissions per render; the timeline listener loads entities per row (N+1). [code: app/bundles/FormBundle/Model/FormModel.php:375-405 @7.x] [code: app/bundles/FormBundle/EventListener/LeadSubscriber.php:56-60 @7.x]

B115. `getCustomComponents()` caches in a `static` for the process lifetime; long-running workers miss later-enabled plugins until restart. [code: app/bundles/FormBundle/Model/FormModel.php:635-659 @7.x]

B116. `createTableSchema` only adds columns; a direct DB rename of a form or field alias orphans tables/columns (hence the cleanup commands). [code: app/bundles/FormBundle/Model/FormModel.php:530-555 @7.x]

B117. `FormBuilderEvent::addValidator` checks key collisions against `$this->fields`, so duplicate validator keys silently overwrite; `getValidators()` keeps one validator per field type. [code: app/bundles/FormBundle/Event/FormBuilderEvent.php:160 @7.x] [code: app/bundles/FormBundle/Event/FormBuilderEvent.php:195-215 @7.x]

B118. Plugin objects collected through `ON_OBJECT_COLLECT` are not applied by `SubmissionModel`; only `contact`/`company` values are, so a plugin must consume results itself. [code: app/bundles/FormBundle/Model/SubmissionModel.php:270 @7.x]
