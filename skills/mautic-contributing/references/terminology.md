# Mautic terminology and writing style (full tables)

Sources: the Vale configuration shared by the user and developer documentation repositories. FeatureList and the Google
rules are byte-identical in `mautic/user-documentation` and `mautic/developer-documentation-new`, branches 7.2 and 8.0.
- FeatureList: [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]
- Google rules: [docs: https://github.com/mautic/user-documentation/tree/7.2/.github/styles/Google]
- Accept lists: [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt]
  [docs: https://github.com/mautic/developer-documentation-new/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt]
- Vale config: [docs: https://github.com/mautic/user-documentation/blob/7.2/.vale.ini]

## Contents
1. How to apply these rules (code vs prose)
2. Rule set in force
3. Mautic feature names and rejected terms (FeatureList, 62 swaps)
4. General word substitutions (Google WordList, 72 swaps)
5. Accepted vocabulary (235 entries)
6. Preferred product, feature and UI names as used in practice
7. Conflicts and gaps

## 1. How to apply these rules (code vs prose)
- Prose (docs, PR descriptions, test steps, en_US UI strings): use the preferred forms below. "Contact", never "Lead";
  "Segment", never "list". [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]
- Code identifiers keep their historical names: `LeadBundle`, `Lead` entity, `leads` table, `LeadList` (Segment),
  `lead_lists` table, `Page` (Landing Page), `DynamicContent`. Do not rename identifiers to match prose terms; that is a
  BC break (see behaviour.md A.8). [code: app/bundles/LeadBundle/ @7.x]
- Vale runs only in the documentation repositories. The core repository's CI has no Vale job, so en_US INI strings are
  not linted automatically; apply the rules by hand. [code: .github/workflows/tests.yml:181-316 @7.x]
- The dev-docs 8.0 accept list adds `LeadBundle` (the only 8.0 vocabulary change).
  [docs: https://github.com/mautic/developer-documentation-new/blob/8.0/.github/styles/config/vocabularies/Mautic/accept.txt]

## 2. Rule set in force
- Styles applied: `Vale` (built-in spelling against the vocabulary), `Google`, `Mautic`. Minimum level: suggestion. [docs: https://github.com/mautic/user-documentation/blob/7.2/.vale.ini]
- Vocabulary `Mautic`: `accept.txt` only (no `reject.txt`). Accepted terms are exempt from spelling and capitalisation flags. [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt] [docs: https://github.com/mautic/developer-documentation-new/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt]
- Mautic feature names are capitalised as proper nouns: `Mautic.FeatureList` suggests the capitalised form whenever a lower-case feature word appears. It also maps **lead → Contact**, **page → Landing Page**, **dwc → Dynamic Content**, **publish → Activate or Turn On**, **unpublish → Deactivate or Turn Off**, **published → Active or Available**, **unpublished → Unavailable or Deactivated**. [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]
- Google style rules (all identical in both repos): American spelling (flags `-nise`/`-logue`); no "will" (warning); no first person (I, me, my) or "we/us/let's"; contractions encouraged (suggestion); no Latin abbreviations (e.g. → "for example", i.e. → "that is"; error); Oxford comma; no exclamation points; no ellipses; em dash without spaces and no en dash; sentence-case headings without trailing period (exceptions: Azure, CLI, Code, Cosmos, Docker, Emmet, I, Kubernetes, Linux, macOS, Marketplace, MongoDB, REPL, Studio, TypeScript, URLs, Visual, VS, Windows); spell out ordinals (no 1st/2nd); no `(s)` optional plurals; date format "July 31, 2016"; "AM"/"PM" with a preceding space; non-breaking space between number and unit; one space between sentences; commas and periods inside quotes; no periods in acronyms; no "from/between" with numeric ranges; avoid passive voice (suggestion); spell out unfamiliar acronyms (exceptions include API, CLI, CSS, CSV, HTML, HTTP(S), JSON, PDF, PHP, POST, SQL and others); avoid gendered terms (he/she, s/he; GenderBias swaps); no internet slang (tl;dr, ymmv, rtfm, imo, fwiw); colons followed by lower case; semicolons and parentheses used judiciously. [docs: https://github.com/mautic/user-documentation/tree/7.2/.github/styles/Google]
- Note the conflicts. The Vale vocabulary itself contains `Company(ies)` and `Contribution(s)`, which `Google.OptionalPlurals` would otherwise flag. `Google.WordList` maps `CLI` → "command-line tool" while `CLI` is in the user `accept.txt`. Google.Spelling demands American spelling, while several KB articles use British spelling (organisation, behaviour). [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt] [docs: https://github.com/mautic/user-documentation/tree/7.2/.github/styles/Google]


## 3. Mautic feature names and rejected terms (FeatureList, 62 swaps; case-insensitive match; level suggestion)
[docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]

| # | Lower-case / non-preferred form (case-insensitive match) | Use instead | Rule |
|---|---|---|---|
| 1 | asset | Asset | Mautic.FeatureList (suggestion) |
| 2 | assets | Assets | Mautic.FeatureList (suggestion) |
| 3 | campaign | Campaign | Mautic.FeatureList (suggestion) |
| 4 | campaigns | Campaigns | Mautic.FeatureList (suggestion) |
| 5 | category | Category | Mautic.FeatureList (suggestion) |
| 6 | categories | Categories | Mautic.FeatureList (suggestion) |
| 7 | channel | Channel | Mautic.FeatureList (suggestion) |
| 8 | channels | Channels | Mautic.FeatureList (suggestion) |
| 9 | companies | Companies | Mautic.FeatureList (suggestion) |
| 10 | company | Company | Mautic.FeatureList (suggestion) |
| 11 | component | Component | Mautic.FeatureList (suggestion) |
| 12 | components | Components | Mautic.FeatureList (suggestion) |
| 13 | contact | Contact | Mautic.FeatureList (suggestion) |
| 14 | contacts | Contacts | Mautic.FeatureList (suggestion) |
| 15 | custom field | Custom Field | Mautic.FeatureList (suggestion) |
| 16 | custom fields | Custom Fields | Mautic.FeatureList (suggestion) |
| 17 | dwc | Dynamic Content | Mautic.FeatureList (suggestion) |
| 18 | dynamic content | Dynamic Content | Mautic.FeatureList (suggestion) |
| 19 | email | Email | Mautic.FeatureList (suggestion) |
| 20 | emails | Emails | Mautic.FeatureList (suggestion) |
| 21 | focus item | Focus Item | Mautic.FeatureList (suggestion) |
| 22 | focus items | Focus Items | Mautic.FeatureList (suggestion) |
| 23 | form | Form | Mautic.FeatureList (suggestion) |
| 24 | form field | Form Field | Mautic.FeatureList (suggestion) |
| 25 | form fields | Form Fields | Mautic.FeatureList (suggestion) |
| 26 | forms | Forms | Mautic.FeatureList (suggestion) |
| 27 | integration | Integration | Mautic.FeatureList (suggestion) |
| 28 | integrations | Integrations | Mautic.FeatureList (suggestion) |
| 29 | landing page | Landing Page | Mautic.FeatureList (suggestion) |
| 30 | landing pages | Landing Pages | Mautic.FeatureList (suggestion) |
| 31 | lead | Contact | Mautic.FeatureList (suggestion) |
| 32 | leads | Contacts | Mautic.FeatureList (suggestion) |
| 33 | marketing message | Marketing Message | Mautic.FeatureList (suggestion) |
| 34 | marketing messages | Marketing Messages | Mautic.FeatureList (suggestion) |
| 35 | mautic | Mautic | Mautic.FeatureList (suggestion) |
| 36 | page | Landing Page | Mautic.FeatureList (suggestion) |
| 37 | pages | Landing Pages | Mautic.FeatureList (suggestion) |
| 38 | point actions | Point Actions | Mautic.FeatureList (suggestion) |
| 39 | point triggers | Point Triggers | Mautic.FeatureList (suggestion) |
| 40 | points | Points | Mautic.FeatureList (suggestion) |
| 41 | point group | Point Group | Mautic.FeatureList (suggestion) |
| 42 | point groups | Point Groups | Mautic.FeatureList (suggestion) |
| 43 | plugin | Plugin | Mautic.FeatureList (suggestion) |
| 44 | plugins | Plugins | Mautic.FeatureList (suggestion) |
| 45 | publish | Activate or Turn On | Mautic.FeatureList (suggestion) |
| 46 | published | Active or Available | Mautic.FeatureList (suggestion) |
| 47 | report | Report | Mautic.FeatureList (suggestion) |
| 48 | reports | Reports | Mautic.FeatureList (suggestion) |
| 49 | role | Role | Mautic.FeatureList (suggestion) |
| 50 | roles | Roles | Mautic.FeatureList (suggestion) |
| 51 | segment | Segment | Mautic.FeatureList (suggestion) |
| 52 | segments | Segments | Mautic.FeatureList (suggestion) |
| 53 | stage | Stage | Mautic.FeatureList (suggestion) |
| 54 | stages | Stages | Mautic.FeatureList (suggestion) |
| 55 | theme | Theme | Mautic.FeatureList (suggestion) |
| 56 | themes | Themes | Mautic.FeatureList (suggestion) |
| 57 | unpublish | Deactivate or Turn Off | Mautic.FeatureList (suggestion) |
| 58 | unpublished | Unavailable or Deactivated | Mautic.FeatureList (suggestion) |
| 59 | user | User | Mautic.FeatureList (suggestion) |
| 60 | users | Users | Mautic.FeatureList (suggestion) |
| 61 | webhook | Webhook | Mautic.FeatureList (suggestion) |
| 62 | webhooks | Webhooks | Mautic.FeatureList (suggestion) |

## 4. General word substitutions (Google WordList, 72 swaps; case-sensitive; level warning)
[docs: https://github.com/mautic/user-documentation/tree/7.2/.github/styles/Google]

| # | Avoid (regex, case-sensitive) | Use instead | Rule |
|---|---|---|---|
| 1 | `'(?:API Console\|dev\|developer) key'` | API key | Google.WordList (warning) |
| 2 | `'(?:cell ?phone\|smart ?phone)'` | phone or mobile phone | Google.WordList (warning) |
| 3 | `'(?:dev\|developer\|APIs) console'` | API console | Google.WordList (warning) |
| 4 | `'(?:e-mail\|E-mail)'` | email | Google.WordList (warning) |
| 5 | `'(?:file ?path\|path ?name)'` | path | Google.WordList (warning) |
| 6 | `'(?:kill\|terminate\|abort)'` | stop or exit or cancel or end | Google.WordList (warning) |
| 7 | `'(?:OAuth ?2\|Oauth)'` | OAuth 2.0 | Google.WordList (warning) |
| 8 | `'(?:ok\|Okay)'` | OK or okay | Google.WordList (warning) |
| 9 | `'(?:WiFi\|wifi)'` | Wi-Fi | Google.WordList (warning) |
| 10 | `'[\.]+apk'` | APK | Google.WordList (warning) |
| 11 | `'3\-D'` | 3D | Google.WordList (warning) |
| 12 | `'Google (?:I\-O\|IO)'` | Google I/O | Google.WordList (warning) |
| 13 | `'tap (?:&\|and) hold'` | touch & hold | Google.WordList (warning) |
| 14 | `'un(?:check\|select)'` | clear | Google.WordList (warning) |
| 15 | `above` | preceding | Google.WordList (warning) |
| 16 | `account name` | username | Google.WordList (warning) |
| 17 | `action bar` | app bar | Google.WordList (warning) |
| 18 | `admin` | administrator | Google.WordList (warning) |
| 19 | `Ajax` | AJAX | Google.WordList (warning) |
| 20 | `Android device` | Android-powered device | Google.WordList (warning) |
| 21 | `android` | Android | Google.WordList (warning) |
| 22 | `API explorer` | APIs Explorer | Google.WordList (warning) |
| 23 | `application` | app | Google.WordList (warning) |
| 24 | `approx\.` | approximately | Google.WordList (warning) |
| 25 | `authN` | authentication | Google.WordList (warning) |
| 26 | `authZ` | authorization | Google.WordList (warning) |
| 27 | `autoupdate` | automatically update | Google.WordList (warning) |
| 28 | `cellular data` | mobile data | Google.WordList (warning) |
| 29 | `cellular network` | mobile network | Google.WordList (warning) |
| 30 | `chapter` | documents or pages or sections | Google.WordList (warning) |
| 31 | `check box` | checkbox | Google.WordList (warning) |
| 32 | `check` | select | Google.WordList (warning) |
| 33 | `CLI` | command-line tool | Google.WordList (warning) |
| 34 | `click on` | click or click in | Google.WordList (warning) |
| 35 | `Cloud` | Google Cloud Platform or GCP | Google.WordList (warning) |
| 36 | `Container Engine` | Kubernetes Engine | Google.WordList (warning) |
| 37 | `content type` | media type | Google.WordList (warning) |
| 38 | `curated roles` | predefined roles | Google.WordList (warning) |
| 39 | `data are` | data is | Google.WordList (warning) |
| 40 | `Developers Console` | Google API Console or API Console | Google.WordList (warning) |
| 41 | `disabled?` | turn off or off | Google.WordList (warning) |
| 42 | `ephemeral IP address` | ephemeral external IP address | Google.WordList (warning) |
| 43 | `fewer data` | less data | Google.WordList (warning) |
| 44 | `file name` | filename | Google.WordList (warning) |
| 45 | `firewalls` | firewall rules | Google.WordList (warning) |
| 46 | `functionality` | capability or feature | Google.WordList (warning) |
| 47 | `Google account` | Google Account | Google.WordList (warning) |
| 48 | `Google accounts` | Google Accounts | Google.WordList (warning) |
| 49 | `Googling` | search with Google | Google.WordList (warning) |
| 50 | `grayed-out` | unavailable | Google.WordList (warning) |
| 51 | `HTTPs` | HTTPS | Google.WordList (warning) |
| 52 | `in order to` | to | Google.WordList (warning) |
| 53 | `ingest` | import or load | Google.WordList (warning) |
| 54 | `k8s` | Kubernetes | Google.WordList (warning) |
| 55 | `long press` | touch & hold | Google.WordList (warning) |
| 56 | `network IP address` | internal IP address | Google.WordList (warning) |
| 57 | `omnibox` | address bar | Google.WordList (warning) |
| 58 | `open-source` | open source | Google.WordList (warning) |
| 59 | `overview screen` | recents screen | Google.WordList (warning) |
| 60 | `regex` | regular expression | Google.WordList (warning) |
| 61 | `SHA1` | SHA-1 or HAS-SHA1 | Google.WordList (warning) |
| 62 | `sign into` | sign in to | Google.WordList (warning) |
| 63 | `sign-?on` | single sign-on | Google.WordList (warning) |
| 64 | `static IP address` | static external IP address | Google.WordList (warning) |
| 65 | `stylesheet` | style sheet | Google.WordList (warning) |
| 66 | `synch` | sync | Google.WordList (warning) |
| 67 | `tablename` | table name | Google.WordList (warning) |
| 68 | `tablet` | device | Google.WordList (warning) |
| 69 | `touch` | tap | Google.WordList (warning) |
| 70 | `url` | URL | Google.WordList (warning) |
| 71 | `vs\.` | versus | Google.WordList (warning) |
| 72 | `World Wide Web` | web | Google.WordList (warning) |

## 5. Accepted vocabulary (235 entries; exact spelling and case; entries are Vale regexes)
User docs 7.2 and 8.0 are identical (168 entries); dev docs 188 (7.2) and 189 (8.0). Accepted terms are exempt from
spelling and capitalisation flags.
[docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt]
[docs: https://github.com/mautic/developer-documentation-new/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt]

| # | Accepted term (exact form) | User docs 7.2 = 8.0 | Dev docs 7.2 | Dev docs 8.0 |
|---|---|---|---|---|
| 1 | AJAX | yes | yes | yes |
| 2 | allowlist | yes | yes | yes |
| 3 | Amazon SES | yes | yes | yes |
| 4 | Ameling | yes | yes | yes |
| 5 | ascenders | - | yes | yes |
| 6 | autoconfiguration | - | yes | yes |
| 7 | autoconfigure | - | yes | yes |
| 8 | autoconfigured | - | yes | yes |
| 9 | Autoloader | yes | yes | yes |
| 10 | autoloader | yes | yes | yes |
| 11 | autowire | - | yes | yes |
| 12 | Autowired | yes | yes | yes |
| 13 | autowired | yes | yes | yes |
| 14 | autowires | - | yes | yes |
| 15 | Autowiring | - | yes | yes |
| 16 | autowiring | - | yes | yes |
| 17 | AWS | yes | - | - |
| 18 | Azure | yes | - | - |
| 19 | bcc | yes | yes | yes |
| 20 | Beanstalkd | yes | yes | yes |
| 21 | Bing | yes | yes | yes |
| 22 | Bingbot | yes | - | - |
| 23 | bitwise | yes | yes | yes |
| 24 | blocklist | yes | yes | yes |
| 25 | boolean | yes | yes | yes |
| 26 | booleans | yes | yes | yes |
| 27 | CASL | yes | - | - |
| 28 | cc | yes | yes | yes |
| 29 | CCPA | yes | yes | yes |
| 30 | Citrix | yes | yes | yes |
| 31 | CKEditor | yes | - | - |
| 32 | Clearbit | yes | yes | yes |
| 33 | CLI | yes | - | - |
| 34 | Clickthrough | yes | - | - |
| 35 | CloudAMQP | yes | yes | yes |
| 36 | CMS | yes | - | - |
| 37 | Codeception | - | yes | yes |
| 38 | Codecov | - | yes | yes |
| 39 | codespace | - | yes | yes |
| 40 | Codespaces | - | yes | yes |
| 41 | Company(ies) | yes | yes | yes |
| 42 | Composability | - | yes | yes |
| 43 | Composer | yes | yes | yes |
| 44 | Config | - | yes | yes |
| 45 | config | yes | yes | yes |
| 46 | configurator | yes | yes | yes |
| 47 | ConnectWise | yes | yes | yes |
| 48 | Contact Points | - | yes | yes |
| 49 | Continuous Integration | - | yes | yes |
| 50 | Contribution(s) | yes | yes | yes |
| 51 | CORS | yes | yes | yes |
| 52 | cPanel | yes | - | - |
| 53 | CPC | yes | - | - |
| 54 | CRM | yes | yes | yes |
| 55 | Cron | yes | yes | yes |
| 56 | cron | yes | yes | yes |
| 57 | CSR | yes | - | - |
| 58 | CTRL | yes | yes | yes |
| 59 | Custom Fields | yes | - | - |
| 60 | datetime | - | yes | yes |
| 61 | DBAL | - | yes | yes |
| 62 | DDEV | yes | yes | yes |
| 63 | DNC | yes | yes | yes |
| 64 | Do Not Contact | yes | yes | yes |
| 65 | Dripflow | yes | yes | yes |
| 66 | DSN | yes | - | - |
| 67 | DTO | - | yes | yes |
| 68 | DWC | yes | - | - |
| 69 | Dynamic Web Content | yes | yes | yes |
| 70 | Esbonio | - | yes | yes |
| 71 | FALSE | yes | yes | yes |
| 72 | false | - | yes | yes |
| 73 | Figma | yes | - | - |
| 74 | Firewalls | - | yes | yes |
| 75 | firewalls | - | yes | yes |
| 76 | Focus Item | yes | yes | yes |
| 77 | Focus Items | yes | yes | yes |
| 78 | Froala | yes | yes | yes |
| 79 | Froogaloop | yes | yes | yes |
| 80 | FTP | yes | - | - |
| 81 | gcm | yes | yes | yes |
| 82 | GDPR | yes | - | - |
| 83 | GIF | yes | yes | yes |
| 84 | GitBook | yes | yes | yes |
| 85 | GitHub | yes | yes | yes |
| 86 | Gitpod | yes | yes | yes |
| 87 | GMail | yes | yes | yes |
| 88 | Googlebot | yes | - | - |
| 89 | GrapesJS Builder | - | yes | yes |
| 90 | Grav | yes | yes | yes |
| 91 | Gravatar | yes | yes | yes |
| 92 | Hammerschmied | yes | yes | yes |
| 93 | href | yes | yes | yes |
| 94 | HTML | yes | yes | yes |
| 95 | html | - | yes | yes |
| 96 | http | yes | yes | yes |
| 97 | HTTPS | - | yes | yes |
| 98 | https | yes | yes | yes |
| 99 | HubSpot | yes | yes | yes |
| 100 | iContact | yes | - | - |
| 101 | IDP | yes | yes | yes |
| 102 | IIS | yes | - | - |
| 103 | IMAP | yes | yes | yes |
| 104 | Importmap | - | yes | yes |
| 105 | infographics | yes | yes | yes |
| 106 | Initialisms | - | yes | yes |
| 107 | initialisms | - | yes | yes |
| 108 | IPs | yes | - | - |
| 109 | ISO | - | yes | yes |
| 110 | JavaScript | yes | yes | yes |
| 111 | Joomla | yes | yes | yes |
| 112 | Joomla! | yes | - | - |
| 113 | JPEG | yes | - | - |
| 114 | JPG | yes | - | - |
| 115 | jQuery | - | yes | yes |
| 116 | LeadBundle | - | - | yes |
| 117 | Legacy Builder | - | yes | yes |
| 118 | Libre | yes | yes | yes |
| 119 | Licensor | yes | yes | yes |
| 120 | LinkedIn | yes | yes | yes |
| 121 | MailChimp | yes | - | - |
| 122 | Mailjet | yes | yes | yes |
| 123 | Marketing Messages | yes | yes | yes |
| 124 | Matomo | yes | - | - |
| 125 | Mautic | yes | yes | yes |
| 126 | MaxMind | yes | yes | yes |
| 127 | middleware | - | yes | yes |
| 128 | Middlewares | yes | yes | yes |
| 129 | middlewares | yes | yes | yes |
| 130 | MIME | yes | - | - |
| 131 | MJML | yes | yes | yes |
| 132 | MMS | yes | yes | yes |
| 133 | MQL | yes | - | - |
| 134 | MQLs | yes | - | - |
| 135 | Multiselect | yes | yes | yes |
| 136 | multiselect | yes | yes | yes |
| 137 | MVC | - | yes | yes |
| 138 | MVP | yes | yes | yes |
| 139 | mysqldump | yes | yes | yes |
| 140 | Namespace | yes | yes | yes |
| 141 | namespace | yes | yes | yes |
| 142 | Nano | yes | - | - |
| 143 | nano | yes | - | - |
| 144 | NGINX | yes | - | - |
| 145 | Node.js | - | yes | yes |
| 146 | noindex | yes | yes | yes |
| 147 | OAuth | yes | yes | yes |
| 148 | OAuth1a | - | yes | yes |
| 149 | OAuth2 | - | yes | yes |
| 150 | Packagist | yes | yes | yes |
| 151 | PATCH | yes | yes | yes |
| 152 | patch | yes | yes | yes |
| 153 | Photoshop | yes | - | - |
| 154 | PHP | yes | yes | yes |
| 155 | PhpStorm | - | yes | yes |
| 156 | PHPUnit.xml | - | yes | yes |
| 157 | Pipedrive | yes | yes | yes |
| 158 | Piwik | yes | yes | yes |
| 159 | Plugin | - | yes | yes |
| 160 | Plugins | - | yes | yes |
| 161 | PNG | yes | - | - |
| 162 | POST | yes | yes | yes |
| 163 | post | yes | yes | yes |
| 164 | prefetch | yes | - | - |
| 165 | prerender | yes | - | - |
| 166 | ProTip | - | yes | yes |
| 167 | ProTips | - | yes | yes |
| 168 | PUT | yes | yes | yes |
| 169 | PyCharm | - | yes | yes |
| 170 | Rackspace | yes | yes | yes |
| 171 | Rahul | - | yes | yes |
| 172 | Read the Docs | - | yes | yes |
| 173 | rebase | - | yes | yes |
| 174 | Remarketing | yes | yes | yes |
| 175 | Report Email | - | yes | yes |
| 176 | REST | yes | yes | yes |
| 177 | RFC | yes | - | - |
| 178 | RST | - | yes | yes |
| 179 | Salesforce | yes | yes | yes |
| 180 | SAML | yes | yes | yes |
| 181 | Schimpf | yes | yes | yes |
| 182 | SCP | yes | yes | yes |
| 183 | Segment Email | - | yes | yes |
| 184 | SendGrid | yes | yes | yes |
| 185 | SES | yes | yes | yes |
| 186 | SFTP | - | yes | yes |
| 187 | SHA | - | yes | yes |
| 188 | Shinde | - | yes | yes |
| 189 | Shortcode | yes | - | - |
| 190 | shortcode | yes | - | - |
| 191 | Shortcodes | yes | - | - |
| 192 | shortcodes | yes | - | - |
| 193 | SMS | yes | yes | yes |
| 194 | SMTP | yes | yes | yes |
| 195 | SNS | yes | yes | yes |
| 196 | spacebar | yes | - | - |
| 197 | SparkPost | yes | yes | yes |
| 198 | SSO | yes | yes | yes |
| 199 | strikethrough | yes | - | - |
| 200 | sublicense | yes | yes | yes |
| 201 | SugarCRM | yes | yes | yes |
| 202 | Suhosin | yes | yes | yes |
| 203 | Symfony | yes | yes | yes |
| 204 | Themes | - | yes | yes |
| 205 | themes | - | yes | yes |
| 206 | timeframe | - | yes | yes |
| 207 | TLS | yes | - | - |
| 208 | Todo | yes | yes | yes |
| 209 | tooltip | - | yes | yes |
| 210 | Transifex | yes | yes | yes |
| 211 | Translator | - | yes | yes |
| 212 | TRUE | yes | yes | yes |
| 213 | true | - | yes | yes |
| 214 | TTL | - | yes | yes |
| 215 | Twilio | yes | yes | yes |
| 216 | unassign | yes | yes | yes |
| 217 | uncategorized | yes | - | - |
| 218 | Unpublish | yes | yes | yes |
| 219 | unpublish | yes | yes | yes |
| 220 | unsubscription | - | yes | yes |
| 221 | URIs | - | yes | yes |
| 222 | URL | yes | yes | yes |
| 223 | URLs | yes | yes | yes |
| 224 | US | - | yes | yes |
| 225 | UTM | yes | yes | yes |
| 226 | VIP | yes | - | - |
| 227 | Vtiger | yes | yes | yes |
| 228 | Webhooks | - | yes | yes |
| 229 | Webmecanik | yes | yes | yes |
| 230 | WSL | - | yes | yes |
| 231 | www | yes | yes | yes |
| 232 | XPath | - | yes | yes |
| 233 | YAML | yes | yes | yes |
| 234 | Zapier | yes | yes | yes |

## 6. Preferred product, feature and UI names as used in practice
Usage observed in the docs and KB (not Vale rules). Source key: FeatureList / accept lists as above; KB articles at kb.mautic.org.

| Term (preferred form) | Avoid / older form | Notes and evidence |
|---|---|---|
| Mautic | mautic, MAUTIC | FeatureList enforces it [FeatureList] |
| Contact | Lead, lead | FeatureList lead→Contact; older KB articles still say "leads" [FeatureList] [kb: https://kb.mautic.org/article/working-with-forms-in-mautic.html] |
| Visitor / unidentified visitor (anonymous Contact) | anonymous lead | Docs anchor "visitors-formerly-anonymous-leads" [kb: https://kb.mautic.org/article/how-to-grow-your-community-with-mautic.html] |
| Segment (static / dynamic, "filter-based") | List, contact list | [FeatureList] [kb: https://kb.mautic.org/article/what-is-the-difference-between-a-static-and-dynamic-segment-in-mautic.html] |
| Segment Email (marketing, send once) / Template Email (transactional) | Broadcast, list email | "Segment Email" is in the dev accept list [dev accept.txt] [kb: https://kb.mautic.org/article/how-to-set-up-a-newsletter-campaign-in-mautic.html] |
| Campaign, Campaign Builder, Contact Source, Decision, Action, Condition, Jump to Event | Workflow (HubSpot term) | [kb: https://kb.mautic.org/article/creating-campaigns.html] [kb: https://kb.mautic.org/article/how-to-migrate-from-hubspot-to-mautic.html] |
| Landing Page | page | FeatureList page→Landing Page [FeatureList] |
| Form: Campaign Form / Standalone Form; Form Field; Form Action; Successful Submit Action; Kiosk mode | — | [kb: https://kb.mautic.org/article/working-with-forms-in-mautic.html] [kb: https://kb.mautic.org/article/lead-scoring-best-practices-with-mautic.html] |
| Focus Item(s) | popup | In accept.txt [user accept.txt] [kb: https://kb.mautic.org/article/how-to-capture-email-addresses-using-an-exit-intent-popup.html] |
| Dynamic Web Content (DWC) / Dynamic Content | dwc | Accept list: "Dynamic Web Content", "DWC"; FeatureList: dwc→Dynamic Content [user accept.txt] [FeatureList] |
| Marketing Messages | — | [user accept.txt] [kb: https://kb.mautic.org/article/creating-campaigns.html] |
| Asset, Point Actions, Point Triggers, Point Group, Points, Stage, Category, Channel, Component, Report, Role, User, Theme, Webhook, Plugin, Integration, Custom Fields, Company | lower-case forms | [FeatureList] |
| Do Not Contact (DNC) | blacklist | Accept list; also allowlist and blocklist (not whitelist or blacklist) [user accept.txt] |
| Activate / Turn On; Deactivate / Turn Off; Active / Available; Unavailable | publish / unpublish / published / unpublished | FeatureList (UI still says Published in places) [FeatureList] |
| GrapesJS Builder / Legacy Builder | "the builder" | Dev accept list [dev accept.txt] |
| Contact Points | — | Dev accept list [dev accept.txt] |
| Report Email | — | Dev accept list [dev accept.txt] |
| Mautibot | — | Error-page mascot [kb: https://kb.mautic.org/article/troubleshooting-the-site-is-currently-offline-due-to-encountering-an-error-in-mautic.html] [kb: https://kb.mautic.org/article/how-to-test-emails-in-mautic.html] |
| Configuration > Email Settings / Tracking settings / API Settings / Asset Settings; Settings > API Credentials; System Info > Error Log | — | UI paths [kb: https://kb.mautic.org/article/what-is-mautic-039%3bs-api.html] [kb: https://kb.mautic.org/article/how-to-set-up-a-staging-server-to-test-new-mautic-releases.html] |
| Preference Center (US spelling) | Preference Centre | [kb: https://kb.mautic.org/article/how-to-set-up-a-newsletter-campaign-in-mautic.html] |
| email (no hyphen) | e-mail, E-mail | WordList [Google WordList] |
| Amazon SES, SendGrid, Mailjet, SparkPost, HubSpot, Salesforce, SugarCRM, Vtiger, Pipedrive, Zoho, Twilio, GitHub, Gitpod, DDEV, CKEditor, MJML, Symfony, JavaScript, NGINX, cPanel, GMail, MailChimp, OAuth, OAuth2/OAuth1a | — | Exact capitalisation from accept.txt [user accept.txt] [dev accept.txt] |
| Campaign Studio | — | Acquia product name leaked into the KB; not a Mautic term [kb: https://kb.mautic.org/article/creating-campaigns.html] |

## 7. Conflicts and gaps
- The vocabulary contains `Company(ies)` and `Contribution(s)`, which `Google.OptionalPlurals` would otherwise flag.
  [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt]
- `Google.WordList` maps `CLI` → "command-line tool", while `CLI` is in the user `accept.txt`.
  [docs: https://github.com/mautic/user-documentation/tree/7.2/.github/styles/Google]
- `Google.Spelling` demands American spelling; several KB articles use British spelling (organisation, behaviour).
  [docs: https://github.com/mautic/user-documentation/tree/7.2/.github/styles/Google]
- FeatureList prefers Activate/Deactivate, but the UI still says "Published" in places. In manual test steps, quote the
  label exactly as the screen shows it. [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/Mautic/FeatureList.yml]
- There is no `reject.txt`; rejected terms come only from FeatureList and WordList.
  [docs: https://github.com/mautic/user-documentation/blob/7.2/.vale.ini]
- No vocabulary entry exists for several current terms ("Point Group" appears only in FeatureList; "Project", "GrapesJS"
  alone, "Mailpit", "Messenger" have none); their spelling is unspecified.
  [docs: https://github.com/mautic/user-documentation/blob/7.2/.github/styles/config/vocabularies/Mautic/accept.txt]
- The repository style guide (`style-guide.md`) is a 4-line stub; the fuller writing guide is
  contribute.mautic.org/education-team/technical-writing-styleguide (not digested).
  [docs: https://github.com/mautic/user-documentation/blob/7.2/style-guide.md]
  [kb: https://kb.mautic.org/article/how-to-contribute-to-the-knowledge-base.html]
