# Forms code map (Mautic 7.x)

All paths are relative to the repository root. `FB` below is shorthand only in prose; every citation spells out the full
path. Line numbers are from upstream 7.x at commit 419a08a9b35 (7.2.1).

## Contents
1. Entities and tables
2. Dynamic results tables
3. Models, helpers and services
4. Field-type registry (core and plugin)
5. Submit-action registry
6. Validators
7. Events
8. Routes and controllers
9. Public JavaScript and templates
10. Console commands
11. Configuration parameters
12. Permissions
13. Campaign, point, webhook, report and dashboard integration
14. Tests and fixtures

## 1. Entities and tables

| Entity | Table | Key facts | Source |
|---|---|---|---|
| `Mautic\FormBundle\Entity\Form` | `forms` | `alias`, `cached_html`, `post_action` (entity default `message`), `post_action_property`, `template`, `in_kiosk_mode`, `render_style`, `submission_limit`, `submission_limit_message`, `submission_count` (not null, default 0), `form_type` (deprecated 7.1), `no_index` (default true), `progressive_profiling_limit`, `uuid`, projects xref `form_projects_xref` | [code: app/bundles/FormBundle/Entity/Form.php:217-309 @7.x] |
| `Mautic\FormBundle\Entity\Field` | `form_fields` | `label`, `show_label`, `alias`, `type` (indexed), `is_custom`, `custom_parameters`, `default_value`, `is_required`, `validation_message`, `help_message`, `field_order`, `properties` (PHP array), `validation` (json), `parent_id`, `conditions` (json), `label_attr`/`input_attr`/`container_attr`, `lead_field` (deprecated), `save_result`, `is_auto_fill`, `is_read_only`, `show_when_value_exists`, `show_after_x_submissions`, `always_display`, `mapped_object`, `mapped_field`, `field_width` (default `100%`), `uuid`; FK `form_id` ON DELETE CASCADE | [code: app/bundles/FormBundle/Entity/Field.php:240-298 @7.x] |
| `Mautic\FormBundle\Entity\Action` | `form_actions` | `type` string(50) indexed, `action_order`, `properties` (PHP array), FK `form_id` ON DELETE CASCADE, uuid | [code: app/bundles/FormBundle/Entity/Action.php:98-124 @7.x] |
| `Mautic\FormBundle\Entity\Submission` | `form_submissions` | bigint id, `form_id` CASCADE, `ip_id`, `lead_id` (ON DELETE SET NULL), `tracking_id` (indexed), `date_submitted` (indexed), `referer` (not null), `page_id` (SET NULL); `results` is not a column but is hydrated from the results table | [code: app/bundles/FormBundle/Entity/Submission.php:63-98 @7.x] [code: app/bundles/FormBundle/Entity/SubmissionRepository.php:184-213 @7.x] |

Relations: `Form::$fields` ordered by `order ASC, id ASC`, cascade all, extra-lazy; `Form::$actions` ordered by `order ASC`;
`Form::$submissions` ordered `dateSubmitted DESC`, no cascade. [code: app/bundles/FormBundle/Entity/Form.php:253-287 @7.x]

Entity helpers worth knowing:
- `Form::usesProgressiveProfiling()` (memoised) [code: app/bundles/FormBundle/Entity/Form.php:888-915 @7.x]
- `Form::isSubmissionLimitReached()` [code: app/bundles/FormBundle/Entity/Form.php:974-977 @7.x]
- `Form::generateFormName()` — the HTML name used in every element id [code: app/bundles/FormBundle/Entity/Form.php:867-884 @7.x]
- `Form::determineValidationGroups()` [code: app/bundles/FormBundle/Entity/Form.php:326-346 @7.x]
- `Field::showForContact()` (progressive profiling) and `Field::showForConditionalField()` [code: app/bundles/FormBundle/Entity/Field.php:816-895 @7.x]
- `Field::isCaptchaType()`, `isFileType()`, `hasChoices()`, `isAutoFillReadOnly()` [code: app/bundles/FormBundle/Entity/Field.php:897-913 @7.x] [code: app/bundles/FormBundle/Entity/Field.php:1022-1025 @7.x]
- Enums: `Enum/ConditionalFieldEnum` (parent types `select`, `country`, `checkboxgrp`, `radiogrp`), `Enum/Token/RedirectUrlToken` (`pagelink`, `formfield`, `contactfield`) [code: app/bundles/FormBundle/Enum/ConditionalFieldEnum.php:12 @7.x] [code: app/bundles/FormBundle/Enum/Token/RedirectUrlToken.php:7-30 @7.x]

API serializer (legacy v1): Form groups `formDetails`/`formList` expose id, name, alias, category, description,
cachedHtml, publishUp/Down, fields, actions, template, inKioskMode, renderStyle, formType, postAction,
postActionProperty, noIndex, formAttributes, language (+ projects). [code: app/bundles/FormBundle/Entity/Form.php:351-384 @7.x]
Field properties exposed: id, label, showLabel, alias, type, defaultValue, isRequired, validationMessage, helpMessage,
order, properties, validation, parent, conditions, label/input/containerAttributes, leadField, saveResult, isAutoFill,
isReadOnly, mappedObject, mappedField, fieldWidth. [code: app/bundles/FormBundle/Entity/Field.php:300-331 @7.x]
The Form entity is also an API Platform resource gated by `form:forms:*`. [code: app/bundles/FormBundle/Entity/Form.php:29-46 @7.x]

## 2. Dynamic results tables

- Name: `<prefix>form_results_<formId>_<formAlias>`. [code: app/bundles/FormBundle/Entity/SubmissionRepository.php:532-535 @7.x]
- Created or extended by `FormModel::createTableSchema()`: `submission_id` (PK), `form_id`, unique `(submission_id, form_id)`, one nullable `text` column per non-view-only field; existing tables only get missing columns. [code: app/bundles/FormBundle/Model/FormModel.php:530-628 @7.x]
- Column dropped on field delete through `FIELD_POST_DELETE`. [code: app/bundles/FormBundle/EventListener/FormFieldSubscriber.php:29-36 @7.x] [code: app/bundles/FormBundle/Model/FieldModel.php:170-179 @7.x]
- Table dropped on form delete. [code: app/bundles/FormBundle/Model/FormModel.php:560-590 @7.x]
- No FK to `form_submissions`; row deletes happen in code. [code: app/bundles/FormBundle/Model/SubmissionModel.php:436-467 @7.x]
- Low-level DDL helpers: `TableSchemaHelper`, `ColumnSchemaHelper` in `app/bundles/CoreBundle/Doctrine/Helper/`. [code: app/bundles/FormBundle/Model/FormModel.php:530-555 @7.x]

## 3. Models, helpers and services

| Class | Path | Role |
|---|---|---|
| `FormModel` | `app/bundles/FormBundle/Model/FormModel.php` | Form CRUD and events (`:130-165`), builder session → entities (`:167-317`), `saveEntity` alias + results table + cached HTML (`:319-339`), rendering `getContent/getFormHtml/generateHtml` (`:347-481`), page grouping (`:483-522`), `getCustomComponents` (`:635-659`), `getAutomaticJavascript/getFormScript` (`:664-729`), GET/auto-fill population (`:734-806`), campaign condition operators (`:808-869`), syncList (`:1005-1067`) |
| `SubmissionModel` (final) | `app/bundles/FormBundle/Model/SubmissionModel.php` | `saveSubmission()` (`:121-407`), `createLeadFromSubmit()` (`:932-1200`), `executeFormActions()` (`:915-925`), `validateFieldValue()` (`:1205-1231`), deletes (`:436-467`), exports (`:494-691`), dashboard data (`:823-908`) |
| `FieldModel` | `app/bundles/FormBundle/Model/FieldModel.php` | alias generation (`:101-126`), `FIELD_*` events (`:131-165`), `removeFieldColumn()` (`:170-179`) |
| `ActionModel` | `app/bundles/FormBundle/Model/ActionModel.php` | "used by" lookups for segment/email/tag (`:72-153`) |
| `FormFieldHelper` (`mautic.helper.form.field_helper`) | `app/bundles/FormBundle/Helper/FormFieldHelper.php` | type registry `$types` (`:23-74`), filters (`:98-101`), constraint validation (`:106-149`), `populateField()` (`:154-252`) |
| `FormUploader` | `app/bundles/FormBundle/Helper/FormUploader.php` | file storage `<form_upload_dir>/<formId>/<fieldId>/` (`:102-118`), EXIF rotation (`:124-151`) |
| `TokenHelper` | `app/bundles/FormBundle/Helper/TokenHelper.php` | `{form=ID}` replacement (`:18-54`) |
| `UploadFieldValidator` | `app/bundles/FormBundle/Validator/UploadFieldValidator.php` | size/extension checks (`:27-49`) |
| `ProgressiveProfiling\DisplayManager` / `DisplayCounter` | `app/bundles/FormBundle/ProgressiveProfiling/` | max-fields-displayed limit (`DisplayManager.php:21-74`); not services |
| `Event\Service\FieldValueTransformer` | `app/bundles/FormBundle/Event/Service/FieldValueTransformer.php` | file values → download URLs (`:25-60`) |
| Collectors | `app/bundles/FormBundle/Collector/` | `ObjectCollector`, `FieldCollector`, `MappedObjectCollector`, `AlreadyMappedFieldCollector` (`:21-77`) |
| `IsPostActionRedirectUrlValidator` | `app/bundles/FormBundle/Validator/Constraint/IsPostActionRedirectUrlValidator.php` | redirect URL validity after token substitution (`:22-57`) |
| `FileExtensionConstraintValidator` | `app/bundles/FormBundle/Validator/Constraint/FileExtensionConstraintValidator.php` | blocks blacklisted extensions (`:22-37`) |

Source for the table: [code: app/bundles/FormBundle/Model/FormModel.php @7.x] [code: app/bundles/FormBundle/Model/SubmissionModel.php @7.x] and the paths listed.

## 4. Field-type registry

Core types are the keys of `FormFieldHelper::$types` plus `button`. Templates live in
`app/bundles/FormBundle/Resources/views/Field/<type>.html.twig`. Plugin types come from `FormBuilderEvent::addFormField()`.
[code: app/bundles/FormBundle/Helper/FormFieldHelper.php:23-74 @7.x] [code: app/bundles/FormBundle/Event/FormBuilderEvent.php:91-139 @7.x]

| Key | UI name (docs) | Input filter | Built-in constraint / validator | Results column? | Notable properties (API) | Notes |
|---|---|---|---|---|---|---|
| `button` | Submit button | – | – | No (view only) | – | Auto-created as `submit` on a new form; not in pick list |
| `captcha` | CAPTCHA | – | `NotBlank`+`EqualTo` answer, or `Blank` (honeypot) | No (view only) | `placeholder`, `captcha`, `errorMessage` | Empty `captcha` property = honeypot |
| `checkboxgrp` | Checkbox Group | `raw` | `minimum`/`maximum` validator | Yes | `syncList`, `optionlist`, `labelAttributes` | Values stored joined by `, `; conditional parent |
| `country` | Select: Country | `string` | – | Yes | `placeholder`, `multiple` | Conditional parent |
| `date` | Date | `string` | – | Yes | `format`, `placeholder` | |
| `datetime` | Date/time | `string` | – | Yes | `format` | |
| `email` | Email | `email` | Symfony `Email`; `donotsubmit` / `blockfreeemail` validators | Yes | `placeholder` | New email field is pre-mapped |
| `freetext` | Description | – | – | No (view only) | `text` | HTML allowed in properties |
| `freehtml` | HTML area | – | – | No (view only) | `text` | HTML allowed in properties |
| `hidden` | Hidden | `string` | – | Yes | – | No label/help/required/width; children not rendered |
| `companyLookup` | Company lookup | `string` | – | Yes (company name) | – | Posts company id; stores name; links company |
| `number` | Number | `float` | – | Yes | `placeholder`, `precision` | |
| `slider` | Slider | `float` | – | Yes | – | No required toggle |
| `pagebreak` | Page break | – | – | No (view only) | `next_page_label`, `prev_page_label` | Splits pages |
| `password` | Password | `string` | – | Yes | – | Docs: do not map to a Contact field |
| `radiogrp` | Radio group | `raw` | – | Yes | `syncList`, `optionlist`, `labelAttributes` | Conditional parent |
| `select` | Select | `raw` | – | Yes | `placeholder`, `syncList`, `list`, `multiple` | Conditional parent |
| `tel` | Phone | `string` | `international` validator (libphonenumber), off by default | Yes | `placeholder` | |
| `text` | Text: Short answer | `string` | – | Yes | `placeholder`, `maxlength` | No regex/length validator in core |
| `rating` | Rating | `string` | – | Yes | `star_count` 1–10, `symbol`, `star_color`, `base_color` | No default value |
| `textarea` | Text: Paragraph | `string` | – | Yes | `placeholder`, `rows`, `maxlength` | |
| `url` | URL | `url` | Symfony `Url` | Yes | `placeholder` | |
| `file` | File | `string` | size + extension checks | Yes (file name) | `allowed_file_size`, `allowed_file_extensions`, `public`, `profile_image` | |
| `plugin.loginSocial` | Social login | plugin | – | plugin | – | Only when MauticSocialBundle is published |

Sources: filters and constraints [code: app/bundles/FormBundle/Helper/FormFieldHelper.php:23-149 @7.x]; view-only list
[code: app/bundles/FormBundle/Model/FormModel.php:649-655 @7.x]; per-type builder options [code: app/bundles/FormBundle/Form/Type/FieldType.php:104-169 @7.x];
validators [code: app/bundles/FormBundle/EventListener/FormValidationSubscriber.php:35-179 @7.x]; companyLookup
[code: app/bundles/FormBundle/Model/SubmissionModel.php:276-293 @7.x]; social login
[code: plugins/MauticSocialBundle/EventListener/FormSubscriber.php:27-45 @7.x]; API property names
[devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html#form-field-types]; UI names
[docs: https://docs.mautic.org/en/7.2/components/forms.html#fields].

## 5. Submit-action registry

All core actions use `eventName = FormEvents::ON_EXECUTE_SUBMIT_ACTION` and guard with `$event->checkContext('<key>')`.
[code: app/bundles/FormBundle/Model/SubmissionModel.php:915-925 @7.x] [code: app/bundles/FormBundle/Event/SubmissionEvent.php:181-210 @7.x]

| Key | UI label | Registered in | Properties (API) | Behaviour | Source |
|---|---|---|---|---|---|
| `form.email` | Send form results | FormBundle `EventListener/FormSubscriber` | `subject`, `immediately`, `set_replyto`, `message`, `email_to_owner`, `copy_lead`, `templates`, `to`, `cc`, `bcc` | Emails results; Reply-To = contact email unless off; optional copy to contact/owner | [code: app/bundles/FormBundle/EventListener/FormSubscriber.php:95-189 @7.x] |
| `form.repost` | Post results to another form | FormBundle `EventListener/FormSubscriber` | `post_url`, `authorization_header`, `failure_email`, per-field key remap | POST with 15 s timeout; `redirect` in response → callback; `violations` → `ValidationException` deletes the submission | [code: app/bundles/FormBundle/EventListener/FormSubscriber.php:191-351 @7.x] |
| `lead.pointschange` | Adjust contact's points | LeadBundle `EventListener/FormSubscriber` | `operator`, `points`, `group` | Logs `PointsChangeLog` type `form` | [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:164-206 @7.x] |
| `lead.changelist` | Modify contact's segments | LeadBundle | `addToLists`, `removeFromLists` | | [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:208-229 @7.x] |
| `lead.changetags` | Modify contact's tags | LeadBundle | `add_tags`, `remove_tags` | | [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:231-246 @7.x] |
| `lead.addutmtags` | Record UTM tags | LeadBundle | – | Reads submit-request query, else referer query | [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:248-286 @7.x] |
| `lead.scorecontactscompanies` | Add to company's score | LeadBundle | `score` | | [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:288-303 @7.x] |
| `lead.remove_do_not_contact` | Remove contact from DNC | LeadBundle | – | Email channel only; uses `$event->getLead()` | [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:305-314 @7.x] |
| `lead.updatelead` | Update contact | LeadBundle | contact field values | Tokens replaced, char limits enforced, `overwriteWithBlank=false` | [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:333-373 @7.x] |
| `email.send.lead` | Send email to contact | EmailBundle | `email` | Sends with `ignoreDNC => true`, source `['form', id]` | [code: app/bundles/EmailBundle/EventListener/FormSubscriber.php:64-89 @7.x] |
| `email.send.user` | Send email to user | EmailBundle | `useremail`, `user_id` | Tokens resolve with contact data | [code: app/bundles/EmailBundle/EventListener/FormSubscriber.php:64-89 @7.x] |
| `asset.download` | Download an asset | AssetBundle | `asset`, `category` | Registers post-submit callback `asset.download_file` | [code: app/bundles/AssetBundle/EventListener/FormSubscriber.php:50-150 @7.x] |
| `plugin.leadpush` | Push contact to integration | PluginBundle | `integration` | Legacy `AbstractIntegration` plugins only | [code: app/bundles/PluginBundle/EventListener/FormSubscriber.php:23-43 @7.x] |

API property names: [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html#form-action-types].
No core action sets stage, adds to a campaign, redirects or shows a message. [code: app/bundles/FormBundle/Model/SubmissionModel.php:383-389 @7.x]

## 6. Validators (registered through `FORM_ON_BUILD`)

| Key / field type | Option | Rule | Source |
|---|---|---|---|
| `tel` | `international` (+ `international_validationmsg`) | libphonenumber must parse | [code: app/bundles/FormBundle/EventListener/FormValidationSubscriber.php:35-67 @7.x] [code: app/bundles/FormBundle/Form/Type/FormFieldTelType.php:25-45 @7.x] |
| `email` | `donotsubmit` | rejects `do_not_submit_emails` fnmatch patterns | [code: app/bundles/FormBundle/EventListener/FormValidationSubscriber.php:93-101 @7.x] |
| `email` | `blockfreeemail` | rejects domains in `blocked_free_email_providers` | [code: app/bundles/FormBundle/EventListener/FormValidationSubscriber.php:103-110 @7.x] |
| `checkboxgrp` | `minimum`, `maximum`, `min_message`, `max_message` | selected-count bounds | [code: app/bundles/FormBundle/Form/Type/FormFieldCheckboxGroupType.php:29-95 @7.x] |

The email validator is only registered when one of the two email parameters is non-empty. [code: app/bundles/FormBundle/EventListener/FormValidationSubscriber.php:35-67 @7.x]

## 7. Events (`app/bundles/FormBundle/FormEvents.php`)

| Constant | Name | Event class | Dispatched | Core listeners |
|---|---|---|---|---|
| `FORM_PRE_SAVE` / `FORM_POST_SAVE` | `mautic.form_pre_save` / `mautic.form_post_save` | `FormEvent` | `Model/FormModel.php:130-165` | `FormSubscriber::onFormPostSave` (audit log, language pack), `FormConditionalSubscriber::onFormPostSave` |
| `FORM_PRE_DELETE` / `FORM_POST_DELETE` | `mautic.form_pre_delete` / `mautic.form_post_delete` | `FormEvent` | `Model/FormModel.php:143-148` | `FormSubscriber::onFormDelete` |
| `FIELD_PRE/POST_SAVE`, `FIELD_PRE/POST_DELETE` | `mautic.field_*` | `FormFieldEvent` | `Model/FieldModel.php:131-165` | `FormFieldSubscriber::onFieldPostDelete` (drop column) |
| `FORM_ON_BUILD` | `mautic.form_on_build` | `FormBuilderEvent` | `Model/FormModel.php:641-642`, `Controller/FieldController.php:432-434` | Form, Lead, Email, Asset, Plugin bundles, MauticSocialBundle |
| `ON_FORM_VALIDATE` | `mautic.on_form_validate` | `ValidationEvent` | `Model/SubmissionModel.php:1222` | `FormValidationSubscriber::onFormValidate` |
| `FORM_ON_SUBMIT` | `mautic.form_on_submit` | `SubmissionEvent` | `Model/SubmissionModel.php:391-397` | Campaign, Point, Webhook subscribers |
| `ON_EXECUTE_SUBMIT_ACTION` | `mautic.form.on_execute_submit_action` | `SubmissionEvent` | `Model/SubmissionModel.php:921-924`; post-submit callbacks `Controller/PublicController.php:312` | All core action listeners |
| `ON_CAMPAIGN_TRIGGER_DECISION` / `_CONDITION` | `mautic.form.on_campaign_trigger_*` | `CampaignExecutionEvent` | CampaignBundle | `CampaignSubscriber` |
| `ON_DETERMINE_SUBMISSION_RATE_WINNER` | `mautic.form.on_submission_rate_winner` | `DetermineWinnerEvent` | A/B winner logic | `DetermineWinnerSubscriber` |
| `ON_OBJECT_COLLECT` / `ON_FIELD_COLLECT` | `mautic.form.on_object_collect` / `on_field_collect` | `ObjectCollectEvent` / `FieldCollectEvent` | `Collector/ObjectCollector.php:33`, `Collector/FieldCollector.php:42` | LeadBundle adds `contact`, `company` and their fields + `ownerbyemail`, `ownerbyid`, `stagebyname` |

All rows: [code: app/bundles/FormBundle/FormEvents.php @7.x] plus the dispatch sites listed, all under `app/bundles/FormBundle/`.
Doctrine listener `EventListener/SubmissionSubscriber` maintains `forms.submission_count`. [code: app/bundles/FormBundle/EventListener/SubmissionSubscriber.php:30-46 @7.x]
LeadBundle listener `app/bundles/LeadBundle/EventListener/FormSubscriber.php:68-162` registers lead actions and collectors. [code: app/bundles/LeadBundle/EventListener/FormSubscriber.php:68-162 @7.x]
Other events FormBundle consumes: `LeadEvents::TIMELINE_ON_GENERATE`, `LEAD_POST_MERGE`, `FIELD_POST_SAVE`; `PageEvents::PAGE_ON_DISPLAY`/`PAGE_ON_BUILD`; `EmailEvents::EMAIL_ON_BUILD`; report, dashboard, global search, config and import/export events. [code: app/bundles/FormBundle/EventListener/LeadSubscriber.php:37-88 @7.x] [code: app/bundles/FormBundle/EventListener/CustomFieldSubscriber.php:35-61 @7.x] [code: app/bundles/FormBundle/EventListener/PageSubscriber.php:39-102 @7.x]

## 8. Routes and controllers (`app/bundles/FormBundle/Config/config.php:8-121`)

Admin (login required):

| Route | Path | Controller |
|---|---|---|
| `mautic_form_index` | `/forms/{page}` | `FormController::indexAction` |
| `mautic_form_action` | `/forms/{objectAction}/{objectId}` | `FormController::executeAction` (view, new, edit, clone, preview, delete, batchDelete, batchRebuildHtml) |
| `mautic_formfield_action` | `/forms/field/{objectAction}/{objectId}` | `FieldController` (AJAX modal, session only) |
| `mautic_formaction_action` | `/forms/action/{objectAction}/{objectId}` | `ActionController` (session only) |
| `mautic_form_results` | `/forms/results/{objectId}/{page}` | `ResultController::indexAction` |
| `mautic_form_export` | `/forms/results/{objectId}/export/{format}` | `ResultController::exportAction` (csv default) |
| `mautic_form_results_add_segment` | `/forms/results/{objectId}/add-to-segment` | `ResultController::addToSegmentAction` |
| `mautic_form_results_action` | `/forms/results/{formId}/{objectAction}/{objectId}` | `ResultController::executeAction` |

Admin AJAX (`?action=form:<name>`): `reorderFields`, `reorderActions`, `getFieldsForObject`, `updateFormFields`. [code: app/bundles/FormBundle/Controller/AjaxController.php:34-133 @7.x]

Public (no login):

| Route | Path | Controller |
|---|---|---|
| `mautic_form_postresults` | `/form/submit` (POST only) | `PublicController::submitAction` |
| `mautic_form_postresults_ajax` | `/form/submit/ajax` | `AjaxController::submitAction` → JSON |
| `mautic_form_generateform` | `/form/generate.js` | `PublicController::generateAction` |
| `mautic_form_postmessage` | `/form/message` | `PublicController::messageAction` |
| `mautic_form_preview` | `/form/{id}` | `PublicController::previewAction` (iframe src) |
| `mautic_form_embed` | `/form/embed/{id}` | `PublicController::embedAction` (`?video=1` for video embed) |
| `mautic_form_company_lookup` | `/form/company-lookup/autocomplete` (POST) | `PublicController::lookupCompanyAction` |
| `mautic_form_file_download` | `/forms/results/file/{submissionId}/{field}` | `ResultController::downloadFileAction` |
| `mautic_form_file_download_by_name` | `/forms/results/file/{fieldId}/filename/{fileName}` | `ResultController::downloadFileByFileNameAction` |

API (`/api`): standard entity `forms` → `Api/FormApiController`; `GET /forms/{formId}/submissions`,
`/forms/{formId}/submissions/{submissionId}`, `/forms/{formId}/submissions/contact/{contactId}` → `Api/SubmissionApiController`;
`DELETE /forms/{formId}/fields/delete`, `DELETE /forms/{formId}/actions/delete`. [code: app/bundles/FormBundle/Config/config.php:8-121 @7.x] [code: app/bundles/FormBundle/Controller/Api/FormApiController.php:73-128 @7.x]

Menu item `mautic.form.forms` under Components; category bundle `form`. [code: app/bundles/FormBundle/Config/config.php:123-140 @7.x]

## 9. Public JavaScript and templates

- SDK source `app/assets/js/mautic-form-src.js`, built to `media/js/mautic-form.js`; loader `Resources/views/Builder/_script.html.twig`. [code: app/bundles/FormBundle/Resources/views/Builder/_script.html.twig:1-35 @7.x]
- Callback dispatcher `Form.customCallbackHandler(formId, event, data)` reads `MauticFormCallback[formId][event]`. [code: app/assets/js/mautic-form-src.js:200-213 @7.x]
- Hooks in the source: `onValidate`, `onValidateStart`, `onValidateEnd`, `onValidateField`, `onErrorMark`, `onErrorClear`, `onResponse`, `onResponseStart`, `onResponseEnd`, `onSubmitButtonDisable`, `onSubmitButtonEnable`, `onShowNextPage`, `onShowPreviousPage`, `onMessageSet`. [code: app/assets/js/mautic-form-src.js:200-213 @7.x] [code: app/assets/js/mautic-form-src.js:443 @7.x] [code: app/assets/js/mautic-form-src.js:463 @7.x] [code: app/assets/js/mautic-form-src.js:842 @7.x]
- Templates: `Builder/form.html.twig` (public renderer), `Builder/_style.html.twig`, `Field/*.html.twig`, `messenger.html.twig` (postMessage responder), `Form/details.html.twig` (embed modals), `form.html.twig` (standalone page), `Public/videoembed.html.twig`, `SubscribedEvents/Timeline/index.html.twig`. [code: app/bundles/FormBundle/Resources/views/Builder/form.html.twig:17-139 @7.x] [code: app/bundles/FormBundle/Resources/views/Form/details.html.twig:382-440 @7.x]
- Theme overrides: `themes/<theme>/html/MauticFormBundle/Builder/form.html.twig`, `_style.html.twig`/`style.html.twig`, `Field/<type>.html.twig`; standalone page `@themes/<theme>/html/form.html.twig`. [code: app/bundles/FormBundle/Model/FormModel.php:422-431 @7.x] [code: app/bundles/FormBundle/Controller/PublicController.php:565 @7.x]

## 10. Console commands

| Command | Class | Effect |
|---|---|---|
| `mautic:forms:delete-results-table` | `Command/DeleteOrphanFormResultsTableCommand.php:18-96` | Drops `form_results*` tables that match no form; no options, no lock |
| `mautic:forms:delete-orphan-form-submission-records-from-form-results-table` | `Command/DeleteOrphanSubmissionRecordsFromFormResultsTableCommand.php:17-69` | Deletes results rows without a `form_submissions` row, batches of 5000 |

[code: app/bundles/FormBundle/Command/DeleteOrphanFormResultsTableCommand.php:18-96 @7.x] [code: app/bundles/FormBundle/Command/DeleteOrphanSubmissionRecordsFromFormResultsTableCommand.php:17-69 @7.x]
Neither is scheduled by anything in the repository. [code: app/bundles/FormBundle/Config/services.php:68-71 @7.x]

## 11. Configuration parameters (`app/bundles/FormBundle/Config/config.php:142-150`)

| Parameter | Default | Controls |
|---|---|---|
| `form_upload_dir` | `%mautic.application_dir%/media/files/form` | Upload root |
| `blacklisted_extensions` | `['php','sh']` | Extensions never allowed on a file field |
| `do_not_submit_emails` | `[]` | fnmatch patterns for `donotsubmit` |
| `blocked_free_email_providers` | JSON list `Assets/json/blocked_free_email_providers.json` | Domains for `blockfreeemail` |
| `form_results_data_sources` | `false` | Each results table becomes a report source |
| `successful_submit_action` | `top` | Message/error div position |
| `form_field_autofill` | `false` | Global gate for auto-fill |

Also read: `allowed_extensions`, `max_size` (file-field defaults), `theme`, `site_url`. [code: app/bundles/FormBundle/Config/config.php:142-150 @7.x] [code: app/bundles/FormBundle/Form/Type/FormFieldFileType.php:36-41 @7.x] [code: app/bundles/FormBundle/Form/Type/ConfigFormType.php:32-95 @7.x]

## 12. Permissions (`app/bundles/FormBundle/Security/Permissions/FormPermissions.php:8-39`)

- `form:forms:{viewown,viewother,editown,editother,create,deleteown,deleteother,publishown,publishother,full}`.
- `form:categories:{view,edit,create,delete,full}`.
- `form:export:enable` — needed (or admin) to export results. [code: app/bundles/FormBundle/Controller/ResultController.php:293 @7.x]

Where checked: new needs `create` [code: app/bundles/FormBundle/Controller/FormController.php:302 @7.x]; edit/clone `editown|editother` (clone also `create`) [code: app/bundles/FormBundle/Controller/FormController.php:554-560 @7.x]; builder modals any of `editown|editother|create` [code: app/bundles/FormBundle/Controller/FieldController.php:81-86 @7.x]; results list `viewown|viewother`, result delete `editown|editother` [code: app/bundles/FormBundle/Controller/ResultController.php:94-99 @7.x] [code: app/bundles/FormBundle/Controller/ResultController.php:363 @7.x]; publish toggle read-only without `publishown|publishother` [code: app/bundles/FormBundle/Form/Type/FormType.php:102-124 @7.x].

## 13. Integration with other areas

| Area | Hook | Source |
|---|---|---|
| Campaign decision `form.submit` | real-time on `FORM_ON_SUBMIT` | [code: app/bundles/FormBundle/EventListener/CampaignSubscriber.php:45-100 @7.x] |
| Campaign condition `form.field_value` | queries results table | [code: app/bundles/FormBundle/EventListener/CampaignSubscriber.php:102-139 @7.x] [code: app/bundles/FormBundle/Entity/SubmissionRepository.php:465-510 @7.x] |
| Campaign form source | `MembershipManager::addContact` in `saveSubmission` | [code: app/bundles/FormBundle/Model/SubmissionModel.php:383-389 @7.x] |
| Point action `form.submit` | `PointSubscriber::onFormSubmit` | [code: app/bundles/FormBundle/EventListener/PointSubscriber.php:47-50 @7.x] |
| Webhook `mautic.form_on_submit` | payload sample `Assets/WebhookPayload/form_on_submit.json` | [code: app/bundles/FormBundle/EventListener/WebhookSubscriber.php:44-59 @7.x] |
| Timeline `form.submitted` | `LeadSubscriber` | [code: app/bundles/FormBundle/EventListener/LeadSubscriber.php:37-83 @7.x] |
| Reports `forms`, `form.submissions`, `form.results.*` | `ReportSubscriber` | [code: app/bundles/FormBundle/EventListener/ReportSubscriber.php:24-171 @7.x] |
| Dashboard widgets | `submissions.in.time`, `top.submission.referrers`, `top.submitters` | [code: app/bundles/FormBundle/EventListener/DashboardSubscriber.php:26-28 @7.x] |
| Landing page token `{form=ID}` | `PageSubscriber`, `TokenHelper` | [code: app/bundles/FormBundle/EventListener/PageSubscriber.php:65-102 @7.x] |
| A/B winner `form.submissions` | pages and emails | [code: app/bundles/FormBundle/EventListener/DetermineWinnerSubscriber.php:30-120 @7.x] |

## 14. Tests and fixtures

`app/bundles/FormBundle/Tests/` (about 75 files): `Collection`, `Collector`, `Command`, `Controller` (+`Api`), `Crate`, `DTO`,
`Entity`, `Event`, `EventListener`, `Finder`, `Form`, `Functional`, `Helper`, `Model`, `ProgressiveProfiling`, `Twig`,
`Unit`, `Validator`. Helper traits `Tests/FormTestHelperTrait.php` and `Tests/Model/FormSubmissionTrait.php`; fixtures
`DataFixtures/ORM/LoadFormData.php`, `LoadFormResultData.php`. Codeception: `tests/acceptance/FormActionSendToUserCest.php`.
See test-patterns.md. [code: app/bundles/FormBundle/Tests/FormTestHelperTrait.php:10-95 @7.x]
