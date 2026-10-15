# Plugin development - pull-request history

Contents: [How to read this file](#how-to-read-this-file) · [Decisions](#decisions-that-shaped-current-behaviour) · [Regression catalogue](#regression-catalogue) · [Feature timeline](#feature-timeline) · [Removed, deprecated, replaced](#removed-deprecated-replaced) · [Maintainer norms](#maintainer-norms-for-this-area) · [Open questions](#open-questions) · [Coverage](#coverage)

## How to read this file
Source: merged pull requests on github.com/mautic/mautic for plugins, the integrations frameworks and the Marketplace, harvested 2026-10-15; this file keeps the items that matter to plugin authors.
Versions are inferred from each PR's base branch and merge date; `~` marks an inference, and versions without `~` were checked against the 7.x release tags.
Current behaviour lives in behaviour.md (code-verified); this file explains why and when it came to be. Sync-engine and CRM behaviour is in mautic-integrations.

## Decisions that shaped current behaviour

### Plugin discovery, naming and the Plugins page
- "Addons" became "Plugins": the `/plugins` directory, the `MauticPlugin\` namespace and the menu use the new name [PR #740] (~v1.2.0). The first attempt moved `/addons` through Composer and namespace tricks and caused redeclared-class errors, so it was replaced by plain support for both directories [PR #740]. BC was kept for the `MauticAddon` prefix and `AddonBundleBase`; only code that hard-coded `/addons` broke [PR #740].
- Every plugin bundle is enabled once it is present; there is no per-bundle enable switch, and an integration is switched on by publishing it [PR #740] (~v1.2.0). The disabled/enabled bundle code was removed to simplify plugin handling [PR #740].
- The Plugins page shows an integration grid: unpublished integrations in grayscale, published ones in colour [PR #740] (~v1.2.0). A plugin with no integration opens an info modal instead of a config form [PR #740]. The grid uses shuffle.js, fixed for 3.x [PR #8313] (~v3.0.0) and re-laid out when the sidebar toggles [PR #8388] (~v3.0.0).
- A plugin whose folder is gone is flagged `is_missing` on reload and hidden from the list; the flag is kept current on every reload [PR #2712] (~v2.2.1). Issue mautic/mautic#1118 reported uninstalled plugins that kept appearing [PR #2712].
- Text after a `\n---\n` separator in a plugin description renders full-width as a secondary description in the plugin modal; Windows line endings work [PR #5794] (~v2.13.0). The separator borrows YAML's document-start syntax; the Zapier plugin needed room for Zap templates [PR #5794].
- The plugin config modal shows the plugin version as a badge next to the title; both PluginBundle and IntegrationsBundle config controllers pass `pluginVersion` [PR #15789] (v7.1.0).
- Core plugins (Twilio, OneSignal) are discovered on Windows too, after a path-separator fix in `IntegrationHelper` [PR #9274] (~v3.1.2).

### Install, reload and update lifecycle
- Install and update are scriptable: `mautic:plugins:install` is an alias of `mautic:plugins:reload` and gives the same result and messages as the UI button, through a shared facade/helper [PR #6201] (~v2.14.0).
- Originally, schema install and update ran from Doctrine metadata through static `onPluginInstall`/`onPluginUpdate` hooks on `PluginBundleBase` [PR #740] (~v1.2.0). In 7.x those hooks are gone: UPGRADE-6.0.md lists their removal in favour of `PluginEvents::ON_PLUGIN_INSTALL`/`ON_PLUGIN_UPDATE` [code: UPGRADE-6.0.md:27-33 @7.x]. The removing PR is not identified in the inputs.
- Installing a custom plugin with entities creates its tables [PR #3310] (~v2.8.2). That fix broke core plugin schema creation during the first Mautic install, and [PR #4178] (~v2.8.2) restored it for core and third-party plugins (issue mautic/mautic#4175).
- Plugin Doctrine migrations load from the plugin's own `Migrations/` directory; a wrong path in `AbstractPluginBundle` had stopped them running [PR #8688] (~v3.0.0).
- `mautic:plugins:reload` runs schema (DDL) statements outside a transaction, because MySQL DDL cannot be rolled back and caused "No active transaction" [PR #13249] (~v5.1.0).
- The plugin migration engine does not commit when the transaction is no longer active, because DDL such as `ALTER TABLE` commits implicitly on PHP 8 with pdo_mysql [PR #14440] (v5.2.2). Mautic has its own engine, so the doctrine/migrations fix had to be mirrored [PR #14440]. A reviewer worried that it "silently does nothing"; the answer was that no error is hidden, only a second commit is avoided [PR #14440].
- A plugin that had no version and now declares one runs its update and migrations on reload [PR #13423] (~v5.1.0).
- Plugin install and update classes (`PluginBundleBase`, `AbstractPluginBundle`, `PluginDatabase`, the install/update events, `ReloadHelper`/`ReloadFacade`, `PluginModel`, the migration engine) receive the DB connection through DI, because `MauticFactory::getDatabase()` was removed [PR #14418] (~v6.0.0). The change was tested with a purpose-built plugin bumped to 1.1.0 and reloaded to prove a column is added [PR #14418].
- `PluginUpdateEvent::getMetadata()` returns `?array`; `null` means the plugin has no entities, matching `PluginInstallEvent` [PR #15951] (v7.0.2). Updating a plugin with no `Entity` directory had thrown a TypeError (issue mautic/mautic#15741) [PR #15951].
- A listener on `PluginEvents::PLUGIN_IS_PUBLISHED_STATE_CHANGING` can veto publishing with `PluginIsPublishedEvent` (`canPublish=false`); the `CanPublish` constraint shows the listener's message [PR #13696] (v7.0.0). Access and refresh tokens are cleared whenever plugin credentials change [PR #13696]. The goal was to block authorising with a user that lacks the required API access [PR #13696].

### Legacy integration framework (`AbstractIntegration`)
- `AbstractIntegration` is deprecated in favour of the IntegrationsBundle, with a docblock saying "To be removed in Mautic 6.0" [PR #11050] (~v4.3). It is still present and still carries that docblock in 7.x [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:54 @7.x]. Legacy plugins are still maintained in 7.2 [PR #16202].
- In 3.0, legacy integration services stopped using `IntegrationPass` setter injection; `AbstractIntegration` takes constructor arguments and integrations must type-hint `TranslatorInterface` [PR #8128] (~v3.0.0). [PR #4063] (~v2.8.2) had first moved integrations to DI services through `IntegrationPass`.
- `UnifiedIntegrationInterface` lets IntegrationsBundle plugins and legacy `AbstractIntegration` plugins share the same Plugins UI, events and helper [PR #8433] (~v3.0.0).
- Saving a plugin integration's config dispatches a `PluginEvents` integration event so listeners can react [PR #2035] (~v2.1.0).
- Required authorisation keys are enforced by form validation; password-type keys are required only when no value is stored yet [PR #1230] (~v1.2.3), and keys are required only when the integration is published [PR #2035] (~v2.1.0).
- `requires_authorization = false` hides the "Authorize App" button, and key fields render only when `getRequiredKeyFields()` is non-empty [PR #8610] [PR #8799] (~v3.0.0). [PR #8610] first hid key fields for OneSignal, Pipedrive, Hubspot and Twilio; [PR #8799] restored them [PR #8799].
- `makeRequest()` originally used Joomla's HTTP library for consistency with other outbound fetches; Guzzle was rejected because 1.x still supported PHP 5.3 [PR #965] (~v1.2.1). On 4.x Guzzle 7, array parameters go as `form_params`, not `body` [PR #10301] (~v4.0.0). A reviewer called that a BC break; the merger ruled it a bug fix because Guzzle had deprecated array bodies in 6.0.1 [PR #10301].
- `encode_parameters => json` sends JSON-encoded parameters as the request body, which restored HubSpot campaign pushes on 4.x [PR #10674] (~v4.1.2).
- `$settings['curl_options']` are merged with `+`, so `CURLOPT_*` keys survive and user options override defaults [PR #5022] (~v2.12.1).
- `decryptApiKeys()` skips keys whose decrypted value is empty instead of dropping all keys; a Yes/No setting set to "No" had wiped every credential [PR #10574] (~v4.2.0).
- Integrations can add tooltips to supported features with `getSupportedFeatureTooltips()` [PR #4077] (~v2.8.2).
- Integration API errors (`ApiErrorException`) create a user notification, linked to the Contact when there is one; code exceptions are only logged [PR #3984] (~v2.8.1).
- Contact values pushed to an integration are HTML-entity-decoded and tag-stripped first, so `McDonald&#39;s` arrives as `McDonald's` [PR #3996] (~v2.8.1).
- Push-to-integration campaign actions receive the current `Event` entity [PR #6638] (~v2.14.2) and the triggering `LeadEventLog` [PR #7131] (~v2.15.1) in the config array.
- `FetchLeadsCommand` checks that the integration really implements `pushLeads` before calling it [PR #4880] (~v2.10.1), and prints clear errors when the integration is missing or unauthorised [PR #5336] (~v2.12.1).
- Authorization header tokens in legacy request logs are replaced by the literal `[REDACTED]` [PR #14277] (v5.2.1). Hashing the token was rejected because a hash does not show that the value was modified [PR #14277]. The rule is still in 7.x [code: app/bundles/PluginBundle/Helper/oAuthHelper.php:221 @7.x].
- The legacy field-mapping AJAX endpoint reads `integration` and `page` from POST with a GET fallback and merges `settings` recursively, so mapping pages 2+ are reachable [PR #16202] (v7.2.0). Issue mautic/mautic#16197 reported the Salesforce paginator stuck on page 1 [PR #16202].

### IntegrationsBundle as a plugin framework
- The standalone `mautic-inc/plugin-integrations` repository became the core `IntegrationsBundle`, with git history kept [PR #8210] (~v3.0.0) and kernel registration fixed in [PR #8223] (~v3.0.0).
- IntegrationsBundle config form templates resolve even when the plugin bundle name is not prefixed with `Mautic` (for example HelloWorld) [PR #8564] (~v3.0.0).
- IntegrationsBundle plugins can be published without any authentication config; enabling a no-key plugin had thrown "Undefined index: apiKeys" [PR #9050] (~v3.1.0).
- Saving integration config calls `isAuthorized()` only when the integration implements `ConfigFormAuthorizeButtonInterface` [PR #9642] (~v3.3.0).
- `IntegrationEvents::INTEGRATION_CONFIG_BEFORE_SAVE` fires after the submitted form is handled, so listeners see the new values [PR #9886] (~v4.0.0). It was labelled a BC break and accepted in the 4.0 beta because no known plugin used it [PR #9886].
- Config forms show validation errors when the integration is published or Authorize was clicked; a required asterisk alone does not validate [PR #10539] (~v4.4.2).
- `ConfigFormNotesInterface` with `ConfigFormNotesTrait` and a `Note` DTO puts notes on the config form [PR #11451] (~v5.0).
- IntegrationsBundle, PluginBundle and MarketplaceBundle views are Twig from 5.0, so plugins that override them must move to Twig [PR #11862] [PR #11960] [PR #11560] (~v5.0).
- `INTEGRATION_CONFIG_ON_GENERATE_AUTH_URL` (`ConfigAuthUrlEvent`) lets a host or plugin rewrite the OAuth2 authorisation URL [PR #13434] (~v5.1.0).
- Classes implementing the IntegrationsBundle integration interfaces are autoconfigured with integration tags, so plugins need not tag them by hand [PR #13521] (~v5.1.0). In 7.x this covers `IntegrationInterface`, `BasicInterface`, `ConfigFormInterface` and `BuilderInterface` only [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:26-33 @7.x].
- The OAuth2 three-legged `HttpFactory` applies `base_uri` from the credentials, so requests can use relative paths [PR #12760] (~v5.1.0).
- The IntegrationsBundle registers a test-only compiler pass (`TestPass`) and an OAuth2 three-legged `HttpFactory` so plugin functional tests can queue mock HTTP responses and assert method, URI and headers [PR #15084] (v7.0.0).
- Plugin authors can filter which Contact and Company field changes are recorded for sync with `INTEGRATION_BEFORE_CONTACT_FIELD_CHANGES` and `INTEGRATION_BEFORE_COMPANY_FIELD_CHANGES` [PR #10512] (~v5.0), and post-process batches with the two `INTEGRATION_BATCH_SYNC_COMPLETED_*` events [PR #11303] (~v5.0). Sync detail is in mautic-integrations.
- 46 IntegrationsBundle services moved from `config.php` definitions to autowired `services.php`; plugin code should reference those services by class name [PR #16781] (~v7.2).

### Code-style rules that change what plugins can extend (7.x)
- `LeadEvent::getLead()` has a native `Lead` return type [PR #13842] (v6.0.0). The PR treated adding a native return type to a non-final public method as a BC break for overriding subclasses, so it waited for a major [PR #13842]. `LeadEvent` is `final` in 6.0.0 and 7.x [code: app/bundles/LeadBundle/Event/LeadEvent.php:10 @7.x].
- Childless IntegrationsBundle DAO/DTO classes (for example `ObjectChangeDAO`, `FieldDAO`, `NotificationDAO`, `DateRange`) became `final` [PR #16888] (v7.2.0). Childless core classes, including bundled integrations such as `OneSignalIntegration`, became `final` with `protected` members made `private` [PR #16902] (v7.2.0). The stated rule is "classes extended or mocked by plugins and tests are left open" [PR #16902]. Both changes are present from the 7.2.0 tag [code: app/bundles/IntegrationsBundle/Sync/DAO/Sync/Order/ObjectChangeDAO.php:10 @7.x] [code: app/bundles/NotificationBundle/Integration/OneSignalIntegration.php:11 @7.x].
- Controllers and models that extend a core base class take their own dependencies through a `#[Required] public function autowire<ClassName>(...)` setter instead of repeating the parent constructor; a PHPStan rule enforces it [PR #16880] (~v7.2). The PR claims no BC break [PR #16880].
- Tagged-service compiler passes are being replaced by `#[AutowireIterator]` constructor arguments [PR #16776] (~v7.2).
- PluginBundle controllers get `PluginModel` by typed injection instead of `getModel('plugin')` [PR #16625] (~v7.2).
- Re-thrown exceptions in MarketplaceBundle and the IntegrationsBundle pass the original as `previous` [PR #16488] (~v7.2).

### Front-end hooks
- Mautic's AJAX page loader triggers the jQuery events `mautic:onPageLoad:before` and `mautic:onPageLoad:after` on the container with `(container, response, inModal)` [PR #15789] (v7.1.0). A reviewer praised them as an extension point that avoids overriding core JS [PR #15789]. They are in 7.x `1a.content.js` [code: app/bundles/CoreBundle/Assets/js/1a.content.js:321,729 @7.x].
- A blocked JS popup shows a "popup blocker" alert instead of a JS error [PR #2326] (~v2.1.1).

### Marketplace installation mechanics
- The Marketplace is a core bundle, not a plugin; the first version was read-only, listing plugins with search, detail view and view/create permissions, and could be switched off by config [PR #9650] (~v4.0.0). Read-only came first because it waited for the 4.x directory structure and Composer 2 [PR #9650].
- Install and remove from the UI or CLI (`mautic:marketplace:install`, `mautic:marketplace:remove`) run Composer in-process, because CLI and web PHP versions differ on many hosts [PR #10518] (~v4.2.0). Bundling `composer.phar` was rejected because a second PHP process may use the wrong PHP [PR #10518]. When `composer_updates` is true, the old self-updater is disabled so the two update paths do not mix [PR #10518].
- The 7.x mechanism: the catalogue comes from the registry API at `https://marketplace.mautic.org/api/registry/v1/packages` [code: app/bundles/MarketplaceBundle/Config/config.php:41-43 @7.x] [code: app/bundles/MarketplaceBundle/Api/Connection.php:35,47 @7.x]. `mautic-plugin` and `mautic-theme` packages install through `ComposerHelper::install()` (in-process `composer require`), and `mautic-resource` packages through `ResourceInstaller` [code: app/bundles/MarketplaceBundle/Command/InstallCommand.php:64-77 @7.x]. The UI install and AJAX actions require `composer_updates` (default false) except for resources; the CLI command has no such check [code: app/bundles/MarketplaceBundle/Controller/Package/InstallController.php:47 @7.x] [code: app/bundles/CoreBundle/Config/config.php:807 @7.x].
- The Marketplace shows the latest stable version (else a dev branch), a display name, issue-tracker and documentation links, and a "Clear cache" action for its 1-hour package cache [PR #11197] (~v4.4.0).
- Package detail pages show the CLI install command, and a failed UI install always returns a JSON error [PR #12529] (~v5.0).
- Marketplace HTML descriptions render with Twig `|purify` [PR #12528] (~v5.0). Marketplace copy is written for marketers and tells them to hand Composer instructions to a developer [PR #13326] (~v5.1.0).

## Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| Deleted plugin still listed | Plugins whose folder is gone are flagged `is_missing` and hidden; reload keeps the flag current | [PR #2712] | ~2.2.1 |
| Custom plugin entities got no tables | Install creates the tables from Doctrine metadata | [PR #3310] | ~2.8.2 |
| Core plugin schema missing after first install | Schema installs for core and third-party plugins | [PR #4178] | ~2.8.2 |
| `onInstall` undefined method on `PluginBundleBase` | Install hook calls resolve without fatals (historical: hooks removed in 6.0) | [PR #1045] | ~1.2.2 |
| Plugin migrations never ran | Migrations load from the plugin's `Migrations/` directory | [PR #8688] | ~3.0.0 |
| "No active transaction" on `mautic:plugins:reload` | DDL runs outside a transaction | [PR #13249] | ~5.1.0 |
| Plugin migrations fail on PHP 8 with "There is no active transaction" | The engine skips commit when DDL already committed | [PR #14440] | 5.2.2 |
| Plugin that gained a version did not update | Empty stored version plus a configured version counts as an update | [PR #13423] | ~5.1.0 |
| Updating a plugin without an `Entity` directory threw a TypeError | Update succeeds; `getMetadata()` returns null | [PR #15951] | 7.0.2 |
| HelloWorld plugin opened an info box instead of a config form | IntegrationsBundle templates resolve for bundles not prefixed `Mautic` | [PR #8564] | ~3.0.0 |
| Enabling a no-auth IntegrationsBundle plugin: "Undefined index: apiKeys" | Plugin publishes without auth config | [PR #9050] | ~3.1.0 |
| Undefined `isAuthorized()` on config save | Called only when `ConfigFormAuthorizeButtonInterface` is implemented | [PR #9642] | ~3.3.0 |
| `INTEGRATION_CONFIG_BEFORE_SAVE` listeners saw old values | Event fires after the form is handled | [PR #9886] | ~4.0.0 |
| Validation ignored for unauthorised IntegrationsBundle integrations | Errors show when published or Authorize is clicked | [PR #10539] | ~4.4.2 |
| Hubspot, Pipedrive, OneSignal, Twilio keys not configurable | Key fields show when required keys exist | [PR #8799] | ~3.0.0 |
| 500 when saving Twilio config on 4.x | Config saves; `PluginController` logs through Mautic's logger | [PR #9840] | ~4.0.0 |
| Yes/No setting "No" wiped all API keys | Only empty keys are skipped | [PR #10574] | ~4.2.0 |
| `curl_options` corrupted by `array_merge` | Options merged with keys preserved | [PR #5022] | ~2.12.1 |
| Guzzle "body as array not supported" for legacy integrations | Array parameters sent as `form_params` | [PR #10301] | ~4.0.0 |
| HubSpot campaign push failed silently | JSON-encoded body sent when `encode_parameters` is `json` | [PR #10674] | ~4.1.2 |
| Fatal `pushLeads` undefined (vTiger, Pipedrive, Hubspot) | Method-exists check before calling | [PR #4880] | ~2.10.1 |
| Sync command printed nothing on error | Clear errors and a list of usable integrations | [PR #5336] | ~2.12.1 |
| `&#39;` sent literally to the integration | Values entity-decoded and tag-stripped before push | [PR #3996] | ~2.8.1 |
| Stale config in cloned campaign push events | The `Event` entity is passed to the integration | [PR #6638] | ~2.14.2 |
| "Call to member getIntegrationObjects() on null" in push-to-integration | `integrationHelper` injected | [PR #13470] | ~5.0.4 |
| Access tokens of legacy plugins written to logs | Authorization header logged as `[REDACTED]` | [PR #14277] | 5.2.1 |
| Plugin settings modal crashed (Twig "filter" on FormView) | Field-mapping template uses no hyphenated variable names | [PR #14361] | 5.2.1 |
| Salesforce field-mapping pages 2+ unreachable | POSTed page and settings honoured; later-page mappings saved | [PR #16202] | 7.2.0 |
| HubSpot contact-matching pagination did nothing | Page changes in the plugin config modal | [PR #15056] | ~7.0 |
| Feature/Auth/Sync tabs double-wrapped and indented | Plugin form type rendered once | [PR #15957] | ~7.2 |
| `jQuery(...).shuffle is not a function` on the Plugins page | Grid works | [PR #8313] | ~3.0.0 |
| Integration mapping block missing on the Contact page in 5.0 | `VIEW_INJECT_CUSTOM_TEMPLATE` dispatched from `CommonController` | [PR #12924] | ~5.0 |
| Marketplace UI install failure returned no error | JSON error returned | [PR #12529] | ~5.0 |
| Marketplace "Clear cache" returned 500 | Page reloads | [PR #12728] | ~5.0 |
| Marketplace pager showed empty pages | Pager respects the limit | [PR #12729] | ~5.0 |
| Marketplace "select all" selected nothing | All visible rows selected | [PR #14413] | 5.2.2 |
| Raw HTML in Marketplace descriptions | Purified HTML rendered | [PR #12528] | ~5.0 |

## Feature timeline

| Version | Change | PR |
|---|---|---|
| ~1.2.x | Plugins replace addons; integration grid; key validation; Joomla HTTP in `makeRequest()` | [PR #740] [PR #965] [PR #1230] |
| ~2.x | Integration save event; feature tooltips; API-error notifications; `curl_options` key-preserving merge; secondary description; `mautic:plugins:install` CLI; Event and log passed to pushes | [PR #2035] [PR #4077] [PR #3984] [PR #5022] [PR #5794] [PR #6201] [PR #6638] [PR #7131] |
| ~3.0.0 | IntegrationsBundle in core; `UnifiedIntegrationInterface`; constructor injection for `AbstractIntegration`; `requires_authorization` | [PR #8210] [PR #8433] [PR #8128] [PR #8610] [PR #8799] |
| ~3.1.0 | Publish IntegrationsBundle plugins without auth | [PR #9050] |
| ~4.0.0 | Marketplace (read-only); `INTEGRATION_CONFIG_BEFORE_SAVE` after form handling; Guzzle `form_params` | [PR #9650] [PR #9886] [PR #10301] |
| ~4.2.0 | Marketplace install/remove via in-process Composer behind `composer_updates` | [PR #10518] |
| ~4.3 | `AbstractIntegration` deprecated | [PR #11050] |
| ~4.4.0 | Marketplace stable-version pick, links, clear cache | [PR #11197] |
| ~5.0 | Twig views for Integrations, Plugin and Marketplace bundles; config-form notes; before-field-change and batch-completed events | [PR #11862] [PR #11960] [PR #11560] [PR #11451] [PR #10512] [PR #11303] |
| ~5.1.0 | Reload DDL outside transactions; unversioned plugin gains a version; auth-URL event; integration autoconfiguration; `base_uri` | [PR #13249] [PR #13423] [PR #13434] [PR #13521] [PR #12760] |
| 5.2.1 | Tokens redacted in legacy request logs | [PR #14277] |
| 5.2.2 | Migration engine tolerates implicit DDL commit | [PR #14440] |
| ~6.0.0 | `MauticFactory::getDatabase()` removed; `FieldModel::getUniqueIdentiferFields()` removed; `LeadEvent::getLead(): Lead` | [PR #14418] [PR #14144] [PR #13842] |
| 7.0.0 | Publish-veto event `PLUGIN_IS_PUBLISHED_STATE_CHANGING`; IntegrationsBundle `TestPass` for HTTP mocking | [PR #13696] [PR #15084] |
| 7.0.2 | `PluginUpdateEvent::getMetadata(): ?array` | [PR #15951] |
| 7.1.0 | Plugin version badge; `mautic:onPageLoad:before/after` JS events | [PR #15789] |
| 7.2.0 | `final` sweep of childless classes; legacy mapping pagination via POST | [PR #16888] [PR #16902] [PR #16202] |
| ~7.2 | `#[Required] autowire*()` rule; `#[AutowireIterator]`; IntegrationsBundle services autowired; exception chaining | [PR #16880] [PR #16776] [PR #16781] [PR #16488] |

## Removed, deprecated, replaced

| What | Replaced by | PR | Version | Note |
|---|---|---|---|---|
| Addons, `AddonBundle`, `/addons` | Plugins, `/plugins` | [PR #740] | ~1.2.0 | BC kept for the `MauticAddon` prefix |
| Per-bundle enable/disable | Publishing the integration | [PR #740] | ~1.2.0 | — |
| `makeRequest()` `stringify_params` | `encode_parameters` / `http_build_query` paths | [PR #881] | added ~1.2.1 | Absent from 7.x and from the 1.2.1, 1.4.1 and 2.0.0 tags; removing PR not identified |
| `PluginBundleBase::onPluginInstall`/`onPluginUpdate` | `PluginEvents::ON_PLUGIN_INSTALL`/`ON_PLUGIN_UPDATE` | [PR #740] (origin) | removed 6.0 | Listed in UPGRADE-6.0.md; removing PR not identified |
| `IntegrationPass` setter injection | Constructor injection | [PR #8128] | ~3.0.0 | Type-hint `TranslatorInterface` |
| `AbstractIntegration` | IntegrationsBundle | [PR #11050] | deprecated ~4.3 | Docblock says removal in 6.0; still in 7.x |
| `IntegrationsBundle/Configuration/PluginConfiguration.php` | Nothing | [PR #11032] | ~5.0 | In UPGRADE-5.0.md |
| PHP templates in Integrations, Plugin and Marketplace bundles | Twig | [PR #11862] [PR #11960] [PR #11560] | ~5.0 | Overrides must move to Twig |
| `EntityManager::clear()` in IntegrationsBundle and PluginBundle | `detach()` on specific entities | [PR #12341] [PR #12342] | ~5.0 | — |
| `MauticFactory::getDatabase()` | DI of the DB connection | [PR #14418] | ~6.0.0 | In UPGRADE-6.0.md |
| `FieldModel::getUniqueIdentiferFields()` | Unique-identifier field lookup | [PR #14144] | ~6.0.0 | In UPGRADE-6.0.md |
| Untyped `LeadEvent::getLead()` | `getLead(): Lead`, class `final` | [PR #13842] | 6.0.0 | Subclasses break |
| Extensible childless DAOs and integration classes | `final` classes | [PR #16888] [PR #16902] | 7.2.0 | Compose instead of extending |
| Parent-constructor forwarding in child controllers | `#[Required] autowire*()` setters | [PR #16880] | ~7.2 | Claimed no BC break |
| Explicit IntegrationsBundle `config.php` services | Autowired `services.php` | [PR #16781] | ~7.2 | Use FQCN ids |

## Maintainer norms for this area
- Keep BC for third-party plugins on renames; deprecated prefixes and base classes stay supported [PR #740].
- Adding a native return type to a non-final public method is a BC break for a major release; new classes, especially DTOs and events, should be `final` [PR #13842] [PR #13696].
- Removed methods must be listed in `UPGRADE-<major>.md` before approval [PR #14144] [PR #14418]. BC breaks must be labelled and documented; a break is acceptable in a major beta if no known plugin uses the API [PR #9886] [PR #11032].
- Plugin-install and integration changes need a real plugin to test, such as a purpose-built test plugin or HelloWorld [PR #14418] [PR #3310] [PR #9796].
- IntegrationsBundle PRs were often merged on code review and unit tests because no public plugin used the framework and the code ran in production at contributor companies [PR #8590] [PR #11252] [PR #11657].
- DDL must not run inside transactions, and upstream Doctrine fixes are mirrored into Mautic's own migration engine [PR #13249] [PR #14440].
- Never log secrets; mark redaction visibly as `[REDACTED]` [PR #14277].
- Integration notifications show API errors only, never code exceptions [PR #3984].
- Re-thrown exceptions chain the previous exception [PR #16488].
- Each bug fix needs a test, and "Steps to test" must be manual UI steps [PR #16202].
- Do not override core JS; prefer core extension points such as the page-load events [PR #15789].
- Bug fixes target the patch branch, features the next minor; there are no back-merges, so a fix for an older line needs its own PR [PR #9096] [PR #11775] [PR #14361].

## Open questions
- Norm exception: [PR #13842] treats changes that break subclasses as major-only, yet [PR #16888] and [PR #16902] made IntegrationsBundle DAOs and bundled integration classes `final` in the 7.2.0 minor. [PR #16902] says classes extended or mocked by plugins stay open, but how third-party extension was assessed is not recorded. The 7.x tree has no UPGRADE-7.2 file that lists the change.
- `AbstractIntegration` says "To be removed in Mautic 6.0" [PR #11050] but is present in 7.x [code: app/bundles/PluginBundle/Integration/AbstractIntegration.php:54 @7.x]. No removal date is set.
- The PR that removed `onPluginInstall`/`onPluginUpdate` is not in the inputs; UPGRADE-6.0.md records the removal [code: UPGRADE-6.0.md:27-28 @7.x]. A test stub still declares `onPluginInstall` [code: app/bundles/PluginBundle/Tests/Helper/PluginBundleBaseStub.php:16 @7.x].
- `stringify_params` [PR #881] appears in no release tag checked, so it may have been renamed before release; the removing PR is not identified.
- Marketplace source: [PR #9650] and [PR #10518] used Packagist and a GitHub allowlist. 7.x reads the registry at marketplace.mautic.org and has no allowlist code in MarketplaceBundle [code: app/bundles/MarketplaceBundle/Config/config.php:41-43 @7.x]. The PR that switched source is not in the inputs.
- [PR #10518] gates install/remove behind `composer_updates`; in 7.x only the UI and AJAX controllers check it, not `mautic:marketplace:install` [code: app/bundles/MarketplaceBundle/Controller/Package/InstallController.php:47 @7.x]. Whether the CLI was ever gated is not recorded.
- [PR #13521] says integration classes are autoconfigured, but `mautic.sync_integration` and `mautic.authentication_integration` are still tagged by hand in 7.x [code: app/bundles/IntegrationsBundle/DependencyInjection/IntegrationsExtension.php:26-33 @7.x]. This matches behaviour.md; the PR describes partial coverage.
- [PR #4063] broke a third-party SSO plugin ("Undefined index: GithubAuth"); whether that was a BC break was never settled before [PR #8128] removed `IntegrationPass`.
- [PR #16776]: which PluginBundle or IntegrationsBundle compiler passes were converted is not visible in the notes.
- No conflicts with behaviour.md were found: B58, B61-B62, B74 and B99-B100 match the PR history [PR #13249] [PR #14440] [PR #15951] [PR #10518].

## Coverage
The integrations, plugins and Marketplace area has 221 merged PRs in three chunks (#740 to #16905, 2015-08 to 2026-08).
Chunk 1 has 104 PRs (97 substantive), chunk 2 has 83 (74 substantive), chunk 3 has 34 (22 substantive, 10 refactor-only, 2 noise).
This file keeps the plugin-development and Marketplace-installation items; sync-engine and CRM items are in mautic-integrations.
A further 869 noise PRs across all areas were excluded upstream before chunking.
