# Forms — what the official docs say

URL abbreviations, used only in this paragraph: F = https://docs.mautic.org/en/7.2/components/forms.html. Every
citation below spells out the full URL.

## 1. User docs (docs.mautic.org, Components > Forms)

Form-level options
- Create at Components > Forms > New; set details and the submit action, add fields, add actions, save. [docs: https://docs.mautic.org/en/7.2/components/forms.html#creating-a-new-form]
- All Forms can trigger Campaigns, can use every Form action, and can be a Campaign Contact source. [docs: https://docs.mautic.org/en/7.2/components/forms.html#creating-a-new-form]
- Unpublished Forms are invisible when embedded with JavaScript. Manually copied HTML stays visible, but submissions are refused with an error. Publish at/Unpublish at bound the submission window. [docs: https://docs.mautic.org/en/7.2/components/forms.html#creating-a-new-form]
- Disable search indexing = Yes sends a `noindex` header. [docs: https://docs.mautic.org/en/7.2/components/forms.html#creating-a-new-form]
- Kiosk mode = Yes: no cookies, no IP association ("data entry mode") for shared devices at events. [docs: https://docs.mautic.org/en/7.2/components/forms.html#creating-a-new-form]
- Use Theme style (also called Render style) = Yes applies Theme or Attributes-tab styling; Theme selects one with Form styling (check the Features column). [docs: https://docs.mautic.org/en/7.2/components/forms.html#creating-a-new-form]
- Submissions limit: Maximum submissions (blank = unlimited) and Limit reached message; at the limit the owner is notified; deleting submissions reopens the Form. [docs: https://docs.mautic.org/en/7.2/components/forms.html#submission-limits]
- Successful Submit Action: Remain at Form, Redirect URL, Display message. Placeholders `{contactfield=ALIAS}`, `{formfield=ALIAS}` and `{pagelink=ID}` are replaced at submission. [docs: https://docs.mautic.org/en/7.2/components/forms.html#details]

Fields
- Types: CAPTCHA, Checkbox Group, Date, Date/time, Description, Email, File, HTML area, Hidden, Select: Country, Page break, Number, Password, Phone, Radio group, Rating, Select, Slider, Social login, Text: Short answer, Text: Paragraph, URL. [docs: https://docs.mautic.org/en/7.2/components/forms.html#fields]
- CAPTCHA is a question/answer or a hidden honeypot. It is recommended on every Form. reCAPTCHA comes only through third-party Plugins. Default error: `The answer to "{label}" is incorrect. Please try again`. [docs: https://docs.mautic.org/en/7.2/components/forms.html#captcha]
- Checkbox group can be a single consent checkbox; maps to boolean and select-multiple Contact fields, not select. [docs: https://docs.mautic.org/en/7.2/components/forms.html#fields]
- Email is the default Contact identifier; include at least one Email field. [docs: https://docs.mautic.org/en/7.2/components/forms.html#fields]
- File: limit of 1,000 submissions with the same filename; files can be attached in "Send Form results"; properties allowed extensions, max size, public link, set as profile image. [docs: https://docs.mautic.org/en/7.2/components/forms.html#file]
- Password must not be mapped to the Contact profile; it is for posting to another system. [docs: https://docs.mautic.org/en/7.2/components/forms.html#fields]
- Phone maps to the Phone field and validates international format with a country code. [docs: https://docs.mautic.org/en/7.2/components/forms.html#fields]
- Rating: 1–10 symbols (default 5), symbol choice, colours `#f5b301`/`#cccccc`, no default value. [docs: https://docs.mautic.org/en/7.2/components/forms.html#rating]
- Text: Short answer = 255 characters; Paragraph up to 65,535. [docs: https://docs.mautic.org/en/7.2/components/forms.html#fields]
- Field tabs: General, Mapped field, Validation, Properties, Attributes, Behavior. Save result = No keeps data out of the submissions table but still updates a mapped Contact field. [docs: https://docs.mautic.org/en/7.2/components/forms.html#general]
- Without a mapping, data is not saved to the Contact. [docs: https://docs.mautic.org/en/7.2/components/forms.html#mapped-field]
- Attributes (HTML name, label/input/container attributes) are ignored when Render style is No. [docs: https://docs.mautic.org/en/7.2/components/forms.html#attributes]
- Behavior: Show when value exists (default Yes), Show after X submissions (1–200), Auto-fill data, Read only. Auto-fill only appears when the global "Enable form field auto-fill from contact data" is on. [docs: https://docs.mautic.org/en/7.2/components/forms.html#behavior]

Progressive profiling
- Keep an Email field and the submit button always visible. [docs: https://docs.mautic.org/en/7.2/components/forms.html#configuration-of-progressive-profiling]
- Enabling it disables HTML caching; at most 200 previous submissions are searched; it works on preview, public pages, JS embeds and iframes, not static HTML; kiosk mode turns it off. [docs: https://docs.mautic.org/en/7.2/components/forms.html#limits-of-progressive-profiling]
- "Maximum fields displayed at a time" caps visible fields. [docs: https://docs.mautic.org/en/7.2/components/forms.html#fields]

Actions
- Add to Company's Score; Adjust Contact's Points; Modify Contact's Segments (meant for static Segments); Modify Contact's Tags; Record UTM Tags (of the hosting page); Remove Contact from DNC; Download an Asset (Asset or newest in Category); POST results to another Form (URL, failure emails, auth header, alias mapping); Push Contact to Integration; Send Email to Contact; Send Email to User (tokens resolve with Contact data); Send Form results (To required; tokens available only after fields exist). [docs: https://docs.mautic.org/en/7.2/components/forms.html#form-actions]

Embedding and maintenance
- Shortcodes: Landing Page `{form=ID}`, WordPress `[mautic type="form" id=ID]`, Joomla `{mauticform ID}`, Drupal 7 `{mauticform id=ID width=300px height=300px}`. [docs: https://docs.mautic.org/en/7.2/components/forms.html#shortcodes]
- Embedded (JavaScript, recommended; IFrame needs width/height) stays in sync. Self-hosted = JS once per page + HTML, not updated until re-copied. Snippets use the configured Site URL. [docs: https://docs.mautic.org/en/7.2/components/forms.html#embedded] [docs: https://docs.mautic.org/en/7.2/components/forms.html#self-hosted]
- Conditional fields: parent Select, Select-Multiple or Boolean; child with including/excluding values or Any value. [docs: https://docs.mautic.org/en/7.2/components/forms.html#adding-conditional-fields-to-a-mautic-form]
- Blocked domains in Configuration > Forms (one per line, `*domain` wildcard), applied per Email field by Validation > Domain name submission filter. [docs: https://docs.mautic.org/en/7.2/components/forms.html#blocking-form-submissions-from-specified-domains]
- Cleanup commands `mautic:forms:delete-results-table` and `mautic:forms:delete-orphan-form-submission-records-from-form-results-table` (batches of 5,000). [docs: https://docs.mautic.org/en/7.2/components/forms.html#deleting-orphan-form-results-tables] [docs: https://docs.mautic.org/en/7.2/components/forms.html#deleting-orphan-form-submission-records]

## 2. Theme docs

- `form.html.twig` renders `/form/ID`, Landing Page embeds and iframes, and outputs `message`, `header`, `content`. [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html#twig-files]
- Form styling overrides: `html/MauticFormBundle/Builder/_style.html.twig`, `form.html.twig`, `Field/` templates; point `@MauticForm` includes at `@themes/MyTheme/...`. [devdocs: https://devdocs.mautic.org/en/7.2/themes/forms.html]
- `config.json` `features` may include `form`, which requires `html/form.html.twig`. [devdocs: https://devdocs.mautic.org/en/7.2/themes/getting_started.html#configuration-file]

## 3. Developer docs — Form JS hooks

- Hooks work for manual or automatic embeds, not iframes. Declare `MauticFormCallback` once in the head, then set `MauticFormCallback['<formName>']` before the Form loads. The name is the `data-mautic-form` value. [devdocs: https://devdocs.mautic.org/en/7.2/form_hooks/getting_started.html]
- General hooks: `onSubmitButtonEnable`/`onSubmitButtonDisable` (true skips default), `onShowNextPage`/`onShowPreviousPage(pageNumber)`, `onMessageSet({message,type})`. [devdocs: https://devdocs.mautic.org/en/7.2/form_hooks/general_hooks.html]
- Validation hooks: `onValidate` (true = skip and submit, false = block, null = default), `onValidateStart`, `onValidateEnd(isFormValid)`, `onErrorMark({containerId, valid, validationMessage})`, `onErrorClear(containerId)`. [devdocs: https://devdocs.mautic.org/en/7.2/form_hooks/validation_hooks.html]
- Response hooks: `onResponse(response)` with `download`, `redirect`, `validationErrors`, `errorMessage`, `success`, `successMessage`; `onResponseStart`, `onResponseEnd`. [devdocs: https://devdocs.mautic.org/en/7.2/form_hooks/response_hooks.html]

## 4. Developer docs — plugin extension

- Listen to `FormEvents::FORM_ON_BUILD` (`FormBuilderEvent`). [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms.html]
- `addFormField($id, [...])`: required `label`, `formType`, `template`; optional `help`, `formTypeOptions`, `formTypeCleanMasks`, `formTypeTheme`, `valueFilter`, `valueConstraints`, `builderOptions`. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms.html#form-fields]
- `addSubmitAction($id, [...])`: required `label`, `eventName`; optional `description`, `formType`, `formTypeOptions`, `formTypeCleanMasks`, `formTypeTheme`, `template`, `group`. Use `setPostSubmitCallbackResponse()` or `setPostSubmitCallback()` to act after all actions. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms.html#form-submit-actions]
- `addValidator($id, [...])`: required `eventName`; optional `fieldType`, `formType`; listeners get `ValidationEvent` and call `failedValidation()`. `ON_FORM_VALIDATE` runs for all fields. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms.html#form-validations]
- Symfony form types in plugins: sanitize with `CleanFormSubscriber`; validate with `loadValidatorMetadata`, attributes or `constraints`; 8.0 requires named-argument constraints. [devdocs: https://devdocs.mautic.org/en/7.2/plugin_extensions/forms_advanced.html#data-validation] [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/forms_advanced.html#data-validation]

## 5. REST API docs

| Method | Path | Notes |
|---|---|---|
| GET | `/api/forms/ID` | form with fields and actions |
| GET | `/api/forms` | `searchFilter` (over HTTP the code reads `search` and `published`, not `publishedOnly` [code: app/bundles/ApiBundle/Controller/FetchCommonApiController.php:167,205 @7.x]), `start`, `limit` (30), `orderBy`, `orderByDir`, `publishedOnly`, `minimal` |
| POST | `/api/forms/new` | `name`, `postActionProperty`, `fields`, `actions`; `postAction` (`return`, `redirect`, `message`) |
| PUT/PATCH | `/api/forms/ID/edit` | include field `id` to update; omit to add |
| DELETE | `/api/forms/ID/delete` | |
| DELETE | `/api/forms/ID/fields/delete`, `/api/forms/ID/actions/delete` | arrays of ids |
| GET | `/api/forms/ID/submissions`, `/api/forms/ID/submissions/SID`, `/api/forms/ID/submissions/contact/CID` | read-only |

Source for the table: [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html]
- Field types, field properties and action properties are listed (mirrored in code-map.md). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html#form-field-types] [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html#form-action-types]
- Map with `mappedObject` + `mappedField`; `leadField` still accepted. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html#mapped-fields]
- Creating a Form via API: include a `button` field. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html#create-form]
- 8.0: `formType` removed from responses and ignored on input. [devdocs: https://devdocs.mautic.org/en/8.0/rest_api/forms.html#form-properties]
- Not documented: posting a submission through the API, permissions per endpoint, error formats. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/forms.html]

## 6. Terminology

Use: Form, Form Field, Form action, Successful Submit Action, Kiosk mode, Progressive profiling, Landing Page, Contact,
Company, Segment, Campaign, Theme, Plugin. Embed modes are named Shortcodes, Embedded (Via JavaScript, Via IFrame),
Self-hosted. [docs: https://docs.mautic.org/en/7.2/components/forms.html]

## 7. Documentation gaps

The user docs do not cover form types (now removed), results storage, export, permissions, page-break behaviour, the
JS SDK internals, or Number/Slider settings. The devdocs plugin page has no lifecycle events, Twig guidance or
conditional fields, and was not updated for 8.0 class-name dispatch. [devdocs: https://devdocs.mautic.org/en/8.0/plugin_extensions/forms.html]
