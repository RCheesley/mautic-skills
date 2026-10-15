# Forms version notes

## Before 7.x (history only)

- Forms were split into "standalone" and "campaign" types. Only campaign forms could be campaign sources. That split is why `formType` still appears in 7.x payloads, fixtures and API responses. [code: app/bundles/FormBundle/Entity/Form.php:166-172 @7.x] [code: app/bundles/FormBundle/Tests/FormTestHelperTrait.php:22 @7.x]
- `Field::$leadField` was the original mapping column. A code comment says it would be removed "in Mautic 4". It is still persisted and kept in sync with `mappedObject`/`mappedField`. [code: app/bundles/FormBundle/Entity/Field.php:728-746 @7.x] [code: app/bundles/FormBundle/Model/FormModel.php:1085-1098 @7.x]
- From Mautic 5, plugins may drop subscriber and form-type service definitions from `config.php` in favour of autowiring. This affects how `FORM_ON_BUILD` subscribers are registered. [devdocs: https://devdocs.mautic.org/en/7.2/plugins/autowiring.html#remove-commands-subscribers-and-forms]
- The two orphan-cleanup commands arrived in an unspecified earlier release. Since then, deleting submissions in the UI also deletes results rows. [docs: https://docs.mautic.org/en/7.2/components/forms.html#deleting-orphan-form-submission-records]
- The analysis inputs give no other 5.x or 6.x behavioural differences for forms. PR-derived history will be added later.

## 7.0 – 7.2

- 7.1 deprecated form types. `Form::getFormType()`, `setFormType()`, `isStandalone()` and `FormRepository::getFormList($formType)` now trigger deprecations, and removal is planned for 8.0. Every form can be a campaign source. The builder no longer shows a form-type field, and `Mautic.selectFormType` JS is deprecated. [code: app/bundles/FormBundle/Entity/Form.php:778-800 @7.x] [code: app/bundles/FormBundle/Entity/Form.php:853-860 @7.x] [code: app/bundles/FormBundle/Entity/FormRepository.php:61-66 @7.x]
- The 7.2 REST docs still list `formType` (`standalone`/`campaign`) without a deprecation note. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html#form-properties]
- 7.x enables Symfony `framework.validation.enable_attributes`, so plugin entities may use attribute constraints. Core `Form` still uses static `loadValidatorMetadata`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms_advanced.html#using-entity-attribute-constraints] [code: app/bundles/FormBundle/Entity/Form.php:311-324 @7.x]
- 7.2 adds theme `config.json` `tags`. This affects theme packaging, not form rendering. [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html#configuration-file]

## 8.x delta (in development; 7.2.1 not yet merged forward)

Removed
- Form type is gone from the entity, the API, exports and `FormListType`. Migration `Version20260814141635` drops `forms.form_type`. This is the only new 8.x migration. API input `formType` is ignored. [code: app/migrations/Version20260814141635.php @8.x] [PR #17082] [PR #17059] [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/forms.html#form-properties]
- `FormRepository::getFormList()` lost its `$formType` parameter. [PR #17082]
- The core `Controller\FormController` base class is removed. Extend `AbstractFormController` or `AbstractStandardFormController`. `mautic_core_form_action` moves to `LockController`. This is the CoreBundle base class, not FormBundle's own `FormController`. [PR #17481] [devdocs: https://devdocs.mautic.org/en/8.0/plugins/mvc.html#abstractformcontroller-mautic-corebundle-controller-abstractformcontroller]

Events (dispatch by class name, [PR #17223])
- `FORM_ON_SUBMIT`, `FORM_ON_BUILD`, `ON_OBJECT_COLLECT` and `ON_FIELD_COLLECT` are dispatched as `SubmissionEvent::class`, `FormBuilderEvent::class`, `ObjectCollectEvent::class` and `FieldCollectEvent::class`. The constants are kept. That is a trap: a listener keyed on the string constant silently never runs. Subscribe with the class name. [PR #17223]
- `mautic.form_on_submit` stays the persisted webhook event-type identifier. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#form-integration-and-focus-events-dispatched-by-class-name-in-mautic-8]
- The form and field CRUD groups (`FORM_PRE/POST_SAVE`, `FORM_PRE/POST_DELETE`, `FIELD_*`) are still dispatched by string name from `FormModel` and `FieldModel`. Plugin-registered `eventName`s for submit actions and validators also stay strings. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/event_listeners.html#form-integration-and-focus-events-dispatched-by-class-name-in-mautic-8]

Signatures
- `SubmissionEvent` is `final`. `setPostSubmitCallbackResponse()` now requires a `RedirectResponse`; the porting guide calls this the "biggest impact" change for forms. `getPostSubmitPayload()` returns `?array`. [devdocs: https://devdocs.mautic.org/en/8.0/plugins/update_m7_to_m8.html]
- Other signature changes:
  - `Field::setCustomParameters(array)`.
  - `Form\FormController::clearSessionComponents()` is `protected`.
  - `Submission` declares `$deletedId`. [PR #17421]
  - `FormModel` single-parameter methods are typed (`saveEntity(object)`, …). [PR #17365]
- Symfony 8 constraints need named arguments. A Symfony 8 regression returned 500 on submissions with email, url or captcha fields; it is fixed. Check custom constraints in plugins. [PR #17392] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/forms_advanced.html#data-validation]
- Generated aliases are checked against a MySQL+MariaDB `ReservedWords` list. A few aliases that were previously left alone now get a prefix. [PR #17361]

Docs
- The 8.0 devdocs `plugin_extensions/forms.rst` is unchanged and still shows constant-keyed subscriptions. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/forms.html]
- UPGRADE-8.0.md contradicts itself: one entry says the `form_type` column is unchanged, while another entry and the migration drop it. The migration is authoritative. [code: app/migrations/Version20260814141635.php @8.x]
