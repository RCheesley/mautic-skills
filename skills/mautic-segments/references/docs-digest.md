# Segments — documentation digest

Sources:
- User docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html (SEG). The 8.0 version changed only the company-filter section.
- REST: https://devdocs.mautic.org/en/7.2/rest_api/segments.html (RA). Identical in 8.0.
- Search: https://docs.mautic.org/en/7.2/search/search_operators.html.

## Terminology
- Segment = code "lead list" / `LeadList`. Contact = code "lead".
- The REST payloads use `list`/`lists` [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#get-segment].
- "static" Segments have no filters, and "dynamic" Segments have filters [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#static-segments].

## Details tab
The Details tab has these fields [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#creating-a-segment]:
- Name.
- Public name: shown in the Preference Center.
- Description.
- **Visible to other Users**: `isGlobal`.
- **Available in Preference Center**: needs the Segment List slot.
- **Active**: an inactive Segment cannot be used as a filter, a Campaign source or an action target.

## Getting Contacts into a Segment
Static Segments are filled by [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#static-segments]:
- contact-list batch **Change Segments**;
- the Contact **Preference → Segments** dialog;
- the Campaign action, Form action and Point Trigger **Modify Contact's Segments**;
- CSV import into a Segment.

The docs say the Campaign action needs "Public Segment = Yes". This is an unverified label; see SKILL.md Pitfalls [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#using-a-campaign-action].

Dynamic Segments [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters]:
- Filters are on the Filters tab.
- An **Or** starts a new group.
- Rebuilds happen "as often as the Segment cron job fires".
- A failed-rebuild notification appears after a configurable period.

The rebuild adds matching Contacts and removes non-matching ones. Manually added Contacts remain [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#date-options].

"Building (X Contacts)" shows until the build completes [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#viewing-contact-segments].

## Operator labels (UI) → keys (code)
| Docs/UI label | Key |
|---|---|
| Is equal to / Is not equal to | `=` / `!=` |
| Greater than (dates: more recent than) … Less than or equal | `gt gte lt lte` |
| Is empty / Is not empty | `empty` / `!empty` |
| Contains / Doesn't contain | `like` / `!like` |
| In list | `contains` |
| Starts with / Ends with | `startsWith` / `endsWith` |
| Includes any of / Excludes any of | `in` / `!in` |
| Includes all of / Excludes all of | `in_all` / `!in_all` |
| Matches pattern / Does not match pattern | `regexp` / `!regexp` |
| In the last / In the next | `inLast` / `inNext` |

[code: app/bundles/LeadBundle/Translations/en_US/messages.ini:758-781 @7.x] [code: app/bundles/CoreBundle/Translations/en_US/messages.ini:491 @7.x] [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#operators]

## Documented text matching
Documented behaviour [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#matching-part-of-a-string]:
- "contains" honours `%`.
- With no `%`, "contains" behaves like a substring match.
- A `%` in the middle of a value needs no escaping.
- "matches pattern" uses MySQL POSIX regex.

Include/exclude operators accept `|`-separated values [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters].

## Documented select and multiselect operators
Single-select fields (Country, Timezone, Region, Locale, Select) offer [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#operators-for-select-fields]:
- equal / not equal;
- empty / not empty;
- pattern / not pattern;
- includes any / excludes any.

Multiselect offers [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#operators-for-select-fields]:
- includes any / excludes any;
- includes all / excludes all;
- empty / not empty.

## Documented relative dates
Accepted values [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#date-options]:
- Relative: `+1 hour`, `-2 days`, `3 weeks ago`, `+5 months`, `-2 years`.
- Hour units apply to datetime fields.
- Formulas: `birthday`/`anniversary` (with ± modifier), `today`, `tomorrow`, `yesterday`, `this|last|next week|month|year`, `first day of …`, `last day of …`.

"In the last/next X" [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#in-the-last-and-in-the-next]:
- Units: days, months or years.
- Boundaries are whole days.
- The interval must be an integer greater than 0.

Behavioural date filters use the most recent occurrence [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters].

## Company filters
- 7.2 docs: only the primary company is evaluated [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#configuring-segment-filters].
- 8.0 docs: "Contact's primary company" and "Any associated company". Negatives on primary also match Contacts with no primary company. Any-company negatives need one non-matching company. Contacts with no company never match any-company filters [docs: https://docs.mautic.org/en/8.0/segments/manage_segments.html#configuring-segment-filters].
- The 7.x branch, after 7.2.1 and not yet released, implements the 8.0 description [PR #15800] [code: app/bundles/LeadBundle/Segment/Query/Filter/AbstractCompanyRelationValueFilterQueryBuilder.php:15-86 @7.x].

## Deleting
- Deleting or deactivating a Segment that another Segment uses as a filter is blocked (since Mautic 4) [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#deleting-or-deactivating-a-segment].
- To delete many Contacts, use a Campaign with the Segment as source and a Delete contact action [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#delete-all-contacts-in-a-segment].

## Search
- Segment list docs: `ids:`, `is:global`, `name:`, `category:` [docs: https://docs.mautic.org/en/7.2/search/search_operators.html#companies-search-filters].
- Contact list: `segment:{alias}` [docs: https://docs.mautic.org/en/7.2/search/search_operators.html#contacts-search-filters].
- Code also supports `is:published`, `is:unpublished`, `is:mine` and `filters_field:` [code: app/bundles/LeadBundle/Entity/LeadListRepository.php:429-499 @7.x].

## REST (summary)
- Envelope: `list` for one Segment, and `lists` keyed by id for many. List parameters: `search`, `start`, `limit` (30), `orderBy` (snake_case), `orderByDir`, `publishedOnly`, `minimal` [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#list-segments].
- POST `/segments/new` requires `name`. PUT replaces the Segment or creates it. PATCH returns 404 if the Segment is missing [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#edit-segment].
- `POST /segments/ID/contacts/add`: the docs say `contactIds`, but the code reads `ids` [code: app/bundles/LeadBundle/Controller/Api/ListApiController.php:186 @7.x].
- Filter object fields: `object`, `glue`, `field`, `type`, `operator`, `properties.filter`. `inLast`/`inNext` take `{interval, unit}` [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/segments.html#filter-properties].

## Procedures
- Create a Segment: Segments → New → Details → Filters → Save [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#creating-a-segment].
- Export members: View X Contacts → Export to CSV/Excel [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#exporting-contacts-of-a-segment].
- Batch-add Contacts: Contacts list → select → Change Segments [docs: https://docs.mautic.org/en/7.2/segments/manage_segments.html#batch-updating-contacts].
