---
name: mautic-forms
description: "Mautic Forms: the form builder, field types, submit actions, validation (captcha, honeypot, blocked domains, file uploads), the public submission pipeline and how a submission identifies, merges or creates a Contact (lead) and company, kiosk mode, progressive profiling, auto-fill, conditional fields, results and export, embedding (generate.js, iframe, {form=ID} token, self-hosted HTML), the mautic-form.js SDK and MauticFormCallback hooks, post-submit messages and redirects, the /api/forms API, and form-to-campaign/points/webhook integration. Use whenever a task mentions forms, form submissions, form fields, form actions, embedding a form, captcha, honeypot, progressive profiling, kiosk mode, /form/submit, MauticFormCallback, form_results tables, FormEvents (FORM_ON_BUILD, FORM_ON_SUBMIT), FormBuilderEvent, SubmissionModel, adding a custom form field or action, or touches app/bundles/FormBundle/ or themes/*/html/MauticFormBundle/."
---
# Mautic forms

## Scope
A **Form** is a Mautic-hosted web form that you embed anywhere. It validates a submission, stores it in `form_submissions`
plus a per-form results table, and identifies or creates the **Contact** (code name `Lead`) and Company from mapped
fields. It then runs its **Form actions** in order, feeds Campaigns, Points and Webhooks, and shows the **Successful
Submit Action** (message, redirect, return or hide form). Contact merge rules and tracking cookies belong to
mautic-contacts. Campaign execution belongs to mautic-campaigns. Theme packaging belongs to mautic-theme-development.

Terms: **Kiosk mode** turns off visitor tracking for shared devices. **Progressive profiling** hides fields whose values
are already known. A **honeypot** is a captcha field with no question, hidden by CSS, that must stay empty. **DNC** is
Do Not Contact.

## Expected behaviour (essentials)
Builder and storage
- Fields and actions are edited in the PHP session. Nothing reaches the DB until the form is saved. On save `FORM_PRE_SAVE`/`FORM_POST_SAVE` fire once. [code: app/bundles/FormBundle/Controller/FormController.php:309-362 @7.x]
- The form alias (max 10 characters) is set once at creation and never regenerated. The results table `form_results_<id>_<alias>` depends on it. [code: app/bundles/FormBundle/Model/FormModel.php:323-326 @7.x] [code: app/bundles/FormBundle/Entity/SubmissionRepository.php:532-535 @7.x]
- Saving adds missing results columns and never renames them. Deleting a field drops its column and loses its data. Deleting a form drops the table. [code: app/bundles/FormBundle/Model/FormModel.php:530-590 @7.x] [code: app/bundles/FormBundle/EventListener/FormFieldSubscriber.php:29-36 @7.x]
- `button`, `captcha`, `freetext`, `freehtml` and `pagebreak` are view-only: no column, never saved, never exported. [code: app/bundles/FormBundle/Model/FormModel.php:649-655 @7.x]
- Field aliases come from the label (`f_` prefix, 25 characters), are unique per form only in code, and cannot be edited after creation. [code: app/bundles/FormBundle/Model/FieldModel.php:101-126 @7.x] [code: app/bundles/FormBundle/Form/Type/FieldType.php:216-231 @7.x]
- A contact or company field can be mapped to only one top-level form field per form. [code: app/bundles/FormBundle/Form/Type/FieldType.php:495-500 @7.x]

Rendering and embedding
- Cached HTML is served unless the form uses progressive profiling. Those forms are rendered per request from up to 200 earlier submissions. [code: app/bundles/FormBundle/Model/FormModel.php:373-405 @7.x]
- `generate.js` returns an empty body for unpublished forms. Manually copied HTML still renders, but `/form/submit` refuses the submission. [code: app/bundles/FormBundle/Controller/PublicController.php:588-610 @7.x] [code: app/bundles/FormBundle/Controller/PublicController.php:138-190 @7.x]
- Auto-fill needs `form_field_autofill=true` and kiosk mode off. It works on every server-rendered path (generate.js, `/form/ID`, `{form=ID}`) but not on self-hosted static HTML. [code: app/bundles/FormBundle/Model/FormModel.php:372-388 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:754-758 @7.x]
- The JS SDK posts into a hidden iframe with `mauticform[messenger]=1`. It reads the reply via `postMessage` and accepts only origins in `window.MauticDomains` or the form's action origin. [code: app/assets/js/mautic-form-src.js:215-312 @7.x] [code: app/assets/js/mautic-form-src.js:759-827 @7.x]
- `MauticFormCallback[<formName>]` hooks (`onValidate`, `onResponse`, `onErrorMark`, …) work for JS and manual embeds, not iframes. [code: app/assets/js/mautic-form-src.js:200-213 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/form_hooks/getting_started.html]

Submission and validation
- `/form/submit` is POST-only. It checks, in order: form exists, publish window, published state, submission limit. [code: app/bundles/FormBundle/Controller/PublicController.php:54-245 @7.x]
- Any field error returns errors and persists nothing: no contact update, no submission, no actions. [code: app/bundles/FormBundle/Model/SubmissionModel.php:322-324 @7.x]
- Order after validation: contact/company resolution, file upload, submission save, actions in `action_order`, campaign-source membership, then `FORM_ON_SUBMIT` (campaign decision, points, webhooks). [code: app/bundles/FormBundle/Model/SubmissionModel.php:327-397 @7.x]
- A honeypot must be blank. A question captcha must equal the answer. Captcha values are never stored. [code: app/bundles/FormBundle/Model/SubmissionModel.php:181-189 @7.x]
- Core validation is limited to required checks, Symfony `Email`/`Url`, phone `international`, email `donotsubmit`/`blockfreeemail`, checkbox min/max, and file size/extension. Core has no regex validator and no reCAPTCHA. [code: app/bundles/FormBundle/EventListener/FormValidationSubscriber.php:35-179 @7.x]
- A hidden conditional field (parent value not matching) is skipped entirely, including its required check. [code: app/bundles/FormBundle/Entity/Field.php:863-895 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:201-203 @7.x]
- An action that throws `ValidationException` (for example `form.repost` receiving `violations`) deletes the saved submission and its files. Emails already sent by earlier actions stay sent. [code: app/bundles/FormBundle/Model/SubmissionModel.php:363-374 @7.x]

Contact identification
- With no contact/company-mapped fields, the submission attaches to the tracked contact (may be null) and no contact is created or updated. [code: app/bundles/FormBundle/Model/SubmissionModel.php:269-274 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:327-331 @7.x]
- If a unique identifier (usually email) matches an existing contact, the tracked anonymous contact is merged into it and the existing contact wins. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1027-1066 @7.x]
- If the submitted email conflicts with the tracked contact's email and matches nobody, a new contact is created. The tracked contact is not overwritten. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1068-1089 @7.x]
- Non-empty mapped values always overwrite contact fields. Empty values never clear them. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1110 @7.x] [code: app/bundles/LeadBundle/Model/LeadModel.php:597-668 @7.x]
- Pseudo-fields `stagebyname`, `ownerbyemail` and `ownerbyid` set stage and owner. No form action does that. [code: app/bundles/FormBundle/Model/SubmissionModel.php:1116-1151 @7.x]
- Kiosk mode ignores the tracked contact, reuses an email match without merging, stores no IP and sets no cookie. It also turns progressive profiling off. [code: app/bundles/FormBundle/Model/SubmissionModel.php:935-955 @7.x] [code: app/bundles/FormBundle/Entity/Field.php:818-821 @7.x]

Actions, response, integration
- Contact actions act on the contact resolved for this submission. `email.send.lead` ignores DNC. [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:164-373 @7.x] [code: app/bundles/EmailBundle/EventListener/FormSubscriber.php:83-87 @7.x]
- `hideform` hides the form only on the JS path. A standard POST shows the message page, as for `message`. [code: app/bundles/FormBundle/Controller/PublicController.php:378-390 @7.x] [code: app/bundles/FormBundle/Controller/PublicController.php:432-514 @7.x]
- `{formfield=}`, `{contactfield=}` and `{pagelink=}` tokens are replaced in redirect URLs and messages. [code: app/bundles/FormBundle/Controller/PublicController.php:639-661 @7.x]
- Any form can be a campaign source (form types were deprecated in 7.1). Submitting adds the contact to every published campaign that uses the form as a source. [code: app/bundles/FormBundle/Model/SubmissionModel.php:383-389 @7.x] [code: app/bundles/FormBundle/Entity/Form.php:778-800 @7.x]
- The submission limit compares the atomic counter `submission_count` without a lock. Deleting results reopens the form. [code: app/bundles/FormBundle/EventListener/SubmissionSubscriber.php:30-46 @7.x] [code: app/bundles/FormBundle/Controller/PublicController.php:204-212 @7.x]
- API: `PUT /api/forms/ID/edit` removes fields and actions missing from the payload, while `PATCH` keeps them. The default `postAction` is `return` via the API but `message` in the entity. [code: app/bundles/FormBundle/Controller/Api/FormApiController.php:132-354 @7.x]

## Where it lives
| Concern | Path |
|---|---|
| Entities / tables | `app/bundles/FormBundle/Entity/{Form,Field,Action,Submission}.php` → `forms`, `form_fields`, `form_actions`, `form_submissions`, dynamic `form_results_<id>_<alias>` |
| Models | `app/bundles/FormBundle/Model/{FormModel,SubmissionModel,FieldModel,ActionModel}.php` |
| Field registry / validation | `app/bundles/FormBundle/Helper/FormFieldHelper.php`, `EventListener/FormValidationSubscriber.php` |
| Events | `app/bundles/FormBundle/FormEvents.php`, `Event/{FormBuilderEvent,SubmissionEvent,ValidationEvent}.php` |
| Actions registered | `app/bundles/{FormBundle,LeadBundle,EmailBundle,AssetBundle,PluginBundle}/EventListener/FormSubscriber.php` |
| Public controller | `app/bundles/FormBundle/Controller/PublicController.php` (`/form/submit`, `/form/generate.js`, `/form/{id}`) |
| Admin / API | `Controller/{FormController,FieldController,ActionController,ResultController}.php`, `Controller/Api/{FormApiController,SubmissionApiController}.php` |
| JS SDK | `app/assets/js/mautic-form-src.js` → `media/js/mautic-form.js`; `Resources/views/Builder/_script.html.twig` |
| Templates | `Resources/views/Builder/form.html.twig`, `Field/*.html.twig`, `messenger.html.twig`; theme overrides `themes/<t>/html/MauticFormBundle/` |
| Commands | `mautic:forms:delete-results-table`, `mautic:forms:delete-orphan-form-submission-records-from-form-results-table` |
| Config | `form_upload_dir`, `blacklisted_extensions`, `do_not_submit_emails`, `blocked_free_email_providers`, `form_results_data_sources`, `successful_submit_action`, `form_field_autofill` (`Config/config.php:142-150`) |
| Permissions | `form:forms:*`, `form:categories:*`, `form:export:enable` (`Security/Permissions/FormPermissions.php`) |
| Tests | `app/bundles/FormBundle/Tests/` |

Sources: [code: app/bundles/FormBundle/Config/config.php:8-150 @7.x] [code: app/bundles/FormBundle/Security/Permissions/FormPermissions.php:8-39 @7.x]. Field-type and action registries are in references/code-map.md.

## How to change or extend it
- Add a field type, submit action or validator from a plugin. Subscribe to `FormEvents::FORM_ON_BUILD` and call `addFormField()`, `addSubmitAction()` or `addValidator()` on `FormBuilderEvent`; do not edit FormBundle. [code: app/bundles/FormBundle/Event/FormBuilderEvent.php:28-215 @7.x] [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms.html]
- In an action listener:
  - Guard with `$event->checkContext('<key>')`.
  - Read `getActionConfig()`, `getResults()`, `getTokens()` and `getContactFieldMatches()`.
  - Throw `ValidationException` with `setViolations([alias => msg])` to reject.
  - Use `setPostSubmitCallback()` or `setPostSubmitResponse()` to control the response.

  [code: app/bundles/FormBundle/Event/SubmissionEvent.php:181-210 @7.x]
- Set `builderOptions.addSaveResult=false` for custom view-only fields so that no results column is created. [code: app/bundles/FormBundle/Model/FormModel.php:649-655 @7.x]
- A plugin mapping object (`ON_OBJECT_COLLECT`) is not applied by core. Consume `getContactFieldMatches()`/results yourself. [code: app/bundles/FormBundle/Model/SubmissionModel.php:270 @7.x]
- React to any submission with a `FORM_ON_SUBMIT` listener. In 8.x, key it on `SubmissionEvent::class`. [code: app/bundles/FormBundle/Model/SubmissionModel.php:391-397 @7.x] [PR #17223]
- New form or field columns need entity mapping, a migration, the API serializer (`loadApiMetadata`), the builder form type (`Form/Type/FormType.php` or `FieldType.php`), translations, and import/export subscribers together. [code: app/bundles/FormBundle/Entity/Form.php:217-384 @7.x] [code: app/bundles/FormBundle/Entity/Field.php:240-331 @7.x]
- Never change how results-table names or columns are derived. Existing tables are only extended, and renames orphan data. [code: app/bundles/FormBundle/Model/FormModel.php:530-555 @7.x]
- Keep the public HTML contract stable: element ids, `mauticform[...]` names, `data-mautic-form*` attributes and messenger JSON keys. Self-hosted copies and `MauticFormCallback` code depend on it. [code: app/bundles/FormBundle/Resources/views/Builder/form.html.twig:17-139 @7.x] [code: app/bundles/FormBundle/Controller/PublicController.php:334-426 @7.x]
- After changing `mautic-form-src.js`, rebuild `media/js/mautic-form.js`. [code: app/bundles/FormBundle/Resources/views/Builder/_script.html.twig:1-35 @7.x]

## How to test it
- Use `MauticMysqlTestCase` with `FormTestHelperTrait`. Set `$useCleanupRollback = false` (results-table DDL) and drop `form_results*` tables in `beforeTearDown()`. [code: app/bundles/FormBundle/Tests/Controller/SubmissionFunctionalTest.php:28-35 @7.x] [code: app/bundles/FormBundle/Tests/FormTestHelperTrait.php:82-95 @7.x]
- Copy from:
  - `Tests/Controller/SubmissionFunctionalTest.php` (end-to-end)
  - `Tests/Model/SubmissionModelFunctionalTest.php` (contact merge)
  - `Tests/Entity/FieldTest.php` (visibility matrices)
  - `Tests/Controller/Api/FormApiControllerFunctionalTest.php`
  - `Tests/Model/FormCaptchaHoneypotFunctionalTest.php`
  - `Tests/EventListener/FormSubscriberTest.php` (repost)

  [code: app/bundles/FormBundle/Tests @7.x]
- The test client is a logged-in user, so `ContactTracker` returns null. Map an email field when you need a contact. [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:51-60 @7.x]
- A good regression test asserts the visitor outcome (redirect, message or JSON), the `form_submissions` row and the results row, the contact result (created, merged or untouched values), and, on failure, that nothing was persisted. Details: references/test-patterns.md.

## Version notes
- 5.x/6.x: forms were `standalone` or `campaign`; only campaign forms could be sources. `leadField` was the original mapping column and is still synced. [code: app/bundles/FormBundle/Entity/Form.php:166-172 @7.x] [code: app/bundles/FormBundle/Entity/Field.php:728-746 @7.x]
- 7.1: form types deprecated; every form is usable in campaigns; the builder hides the type. [code: app/bundles/FormBundle/Entity/Form.php:778-800 @7.x]
- 8.x: `form_type` column dropped (`Version20260814141635`) and `formType` ignored by the API. [PR #17082]
- 8.x: `FORM_ON_SUBMIT`, `FORM_ON_BUILD`, `ON_OBJECT_COLLECT` and `ON_FIELD_COLLECT` are dispatched by class name; their constants still exist but receive nothing. [PR #17223]
- 8.x: `SubmissionEvent` is final, and `setPostSubmitCallbackResponse()` requires a `RedirectResponse`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- 8.x: a Symfony 8 regression returned 500 on email, url and captcha submissions; it is fixed. [PR #17392]
- 5.0: form templates are Twig, so theme field overrides must be `.html.twig`. Mapping moved to `mapped_object`/`mapped_field`. URL pre-fill works on external JS embeds. [PR #11898] [PR #11905] [PR #11077]
- 5.1: new forms default to "Display message"; the API default stays `return`. Forms gained a language setting. [PR #12813] [PR #13410] [PR #12814]
- 5.2.3–5.2.7: a mapped choice field uses its own options unless `syncList` is on. [PR #14560] [PR #14048]
- 6.0: submission values are stored without HTML entity encoding (BC break). Read-only fields were added. [PR #14604] [PR #14422]
- Full detail: references/version-notes.md.

## Pitfalls
- A submission with no mapped fields does not create or update a contact, and from a logged-in admin browser it has `lead_id` NULL. [code: app/bundles/FormBundle/Model/SubmissionModel.php:269-274 @7.x] [code: app/bundles/LeadBundle/Tracker/ContactTracker.php:51-60 @7.x]
- `saveResult=false` keeps the value out of results, but mapped contact fields still update. [code: app/bundles/FormBundle/Model/SubmissionModel.php:291-293 @7.x] [docs: https://docs.mautic.org/en/7.2/components/forms.html#general]
- UTM tags are not stored on submissions. Add the "Record UTM tags" action. [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:248-286 @7.x]
- The submission limit can be overshot by concurrent posts (no lock). [code: app/bundles/FormBundle/Controller/PublicController.php:204-212 @7.x]
- `getCustomComponents()` caches components statically per process, so long-running workers miss newly enabled plugin fields and actions. [code: app/bundles/FormBundle/Model/FormModel.php:635-659 @7.x]
- Duplicate `addValidator` keys silently overwrite, and only one validator per field type survives. [code: app/bundles/FormBundle/Event/FormBuilderEvent.php:160 @7.x] [code: app/bundles/FormBundle/Event/FormBuilderEvent.php:195-215 @7.x]
- Validators run twice for non-empty core values, and `form`-level validators run once per field. Write idempotent validators. [code: app/bundles/FormBundle/Model/SubmissionModel.php:257-264 @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php:1213 @7.x]
- Docs vs code (kiosk): the docs say kiosk mode "always creates a new Contact". The code reuses an existing contact matched by unique identifier, without merging. [docs: https://docs.mautic.org/en/7.2/components/forms.html#limits-of-progressive-profiling] [code: app/bundles/FormBundle/Model/SubmissionModel.php:1027-1050 @7.x]
- Docs vs code (auto-fill): one docs page says auto-fill works "with Mautic Landing Pages only". The code applies it on every server-rendered embed. [docs: https://docs.mautic.org/en/7.2/components/forms.html#behavior] [code: app/bundles/FormBundle/Model/FormModel.php:372-388 @7.x]
- Docs vs code (conditional parents): the docs list Select, Select-Multiple and Boolean as conditional parents. The code allows `select`, `country`, `checkboxgrp` and `radiogrp`, with `expr` `in`/`notIn` only. The API docs' `eq`/`neq`/`!in` and `isConditionallyHidden` do not exist in code. [docs: https://docs.mautic.org/en/7.2/components/forms.html#adding-conditional-fields-to-a-mautic-form] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html#conditional-fields] [code: app/bundles/FormBundle/Enum/ConditionalFieldEnum.php:12 @7.x] [code: app/bundles/FormBundle/Form/Type/FormFieldConditionType.php:73-78 @7.x]
- Docs vs code (phone): the docs say Phone validates international format. The code validates only when the field's `international` option is on, which is off by default. [docs: https://docs.mautic.org/en/7.2/components/forms.html#fields] [code: app/bundles/FormBundle/Form/Type/FormFieldTelType.php:25-30 @7.x]
- Open question (API serializer): the API docs list `submissionLimit`, `submissionLimitMessage` and `submissionCount` in GET responses. The v1 serializer does not expose them, nor `progressiveProfilingLimit` or the field behaviour properties (`showWhenValueExists`, `showAfterXSubmissions`, `alwaysDisplay`). Verify against a live response or API v2. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html] [code: app/bundles/FormBundle/Entity/Form.php:351-384 @7.x] [code: app/bundles/FormBundle/Entity/Field.php:300-331 @7.x]
- Open question (isAutoFill): the API docs say `isAutoFill=false` means "the value is not saved". The code shows no such link. [unverified] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html#form-field-properties]
- "Existing contact wins" (B73) is unreleased: in 7.2.1 and earlier, a known contact submitting without a cookie lost the merge, and its ID was deleted. [PR #16426]
- Auto-fill is off on new installs from 7.2.0 (`form_field_autofill=false`). Upgrades that already use it get it switched on by a migration. [PR #16954]
- "Send form results" needs a To address from 7.2.0. Actions saved with only CC/BCC (allowed since 4.4.2) must get a To when next edited. [PR #17137] [PR #11405]
- Repost failures: in 7.2.1 and earlier, a 4xx from the target shows on the form. On the 7.x head, only a `violations` response blocks the visitor; other errors send the failure email. [PR #13482] [PR #17461]
- Mapped select/radio/checkbox fields have regressed several times to showing the contact field's options. They should use their own list unless `syncList` is on. Turning `syncList` off does not restore custom labels. [PR #8646] [PR #14117] [PR #14560] [PR #14048]
- The devdocs plugin example has bugs (`onFormValidateCustomFIeld` typo, inverted validation branch, `.html.php` templates). Use core subscribers such as `FormValidationSubscriber` as the reference instead. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms.html#example-code] [code: app/bundles/FormBundle/EventListener/FormValidationSubscriber.php:35-82 @7.x]

## Related skills
- mautic-contacts: unique identifiers, `ContactTracker`, `ContactMerger`, `setFieldValues`, company identification, DNC.
- mautic-campaigns: form sources, the `form.submit` decision, the `form.field_value` condition, real-time execution.
- mautic-points-and-stages: the `form.submit` point action, point groups, and stages set by `stagebyname`.
- mautic-emails: "Send email to contact/user" and "Send form results" delivery, email A/B winner by submissions.
- mautic-pages-and-tracking: the `{form=ID}` landing-page token, tracking cookies, `generate.js` and tracking.
- mautic-assets-categories-projects: the "Download an asset" action, form categories and projects.
- mautic-theme-development: theme `form.html.twig`, `message.html.twig`, `MauticFormBundle` overrides.
- mautic-plugin-development: plugin structure, service registration, the 8.x event-class dispatch.
- mautic-rest-api: API auth, pagination, API v2/API Platform.
- mautic-testing: `MauticMysqlTestCase`, fixtures, running suites.
- mautic-upgrades-and-versions: the broader 7→8 porting guide.

## Reference files
- references/behaviour.md: the full numbered behaviour specification (B1–B118). Open it before asserting any edge case.
- references/code-map.md: entities, the results table, models, the **field-type and submit-action registry tables**, validators, events, routes, commands, config, permissions and integrations.
- references/docs-digest.md: what docs.mautic.org and devdocs say (user procedures, JS hooks, plugin extension, REST endpoints), with URLs.
- references/test-patterns.md: base classes, helpers, cleanup rules, representative tests and a functional-test skeleton.
- references/version-notes.md: pre-7 history, 7.0–7.2 changes and the 8.x delta.
- references/pr-history.md: why and when forms behaviour changed, from merged PRs: decisions, a regression catalogue, a feature timeline, removals, maintainer norms and open questions.
