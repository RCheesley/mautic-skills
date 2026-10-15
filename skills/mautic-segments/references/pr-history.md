# Segments — PR history

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
Source: merged pull requests on mautic/mautic for the Segments area, harvested 2026-10-15.
Versions are inferred from the base branch, milestone and merge date. Where a release tag was checked in the 7.x tree, the first tag that contains the merge is used.
Current behaviour is in behaviour.md. This file explains why and when. Where the two disagree, behaviour.md wins.

## 2. Decisions that shaped current behaviour

### Membership model and manual flags
- Membership is a row per Contact in `lead_lists_leads` with `manually_added` and `manually_removed` flags. Manually added Contacts stay even when they no longer match the filters. Why: before this, the rebuild silently removed manual additions; the model copies Campaign membership [PR #123] (v1.0).
- A Segment with no filters gets no Contacts automatically. Only manual additions populate it [PR #123] (v1.0).
- A manually removed Contact is never re-added by the rebuild [PR #1193] (v1.2.3) [PR #4544] (v2.9.2).
- Adding a Contact through a Campaign action sets `manually_added = 1`, even when the rebuild had already added the Contact. Why: the row kept `manually_added = 0`, so a later rebuild could remove a Contact that a Campaign had added on purpose (issue #16473) [PR #16474] (7.x after 7.2.1, unreleased).
- The Campaign condition "Is a member of segment" treats manually removed Contacts as non-members [PR #11782] (v5.0).
- The Campaign "add to / remove from segment" action uses an entity reference for a detached Segment. Why: Doctrine "new entity found through relationship" errors on large instances [PR #13244] (v5.0.3); the same error was first fixed for batch edits in [PR #999] (v1.2.1).
- The segment-change event is dispatched only after the membership rows are persisted. Why: Campaign listeners read stale membership [PR #1017] (v1.2.1).
- A Campaign, Form or Point action that names a deleted Segment is skipped silently [PR #283] (v1.0.3).
- Contact merge tolerates a membership row that already exists [PR #144] (v1.0) [PR #202] (v1.0.1).

### Rebuild command and lifecycle
- The command is `mautic:segments:update` with alias `mautic:segments:rebuild`. The 1.4 rename introduced many synonyms such as `mautic:lists:update`; a reviewer called it "command roulette". Only the two names remain in 7.x [PR #1644] (v1.4).
- `-i`/`--list-id` rebuilds one Segment [PR #1193] (v1.2.3).
- Unpublished Segments are skipped by the rebuild. Why: issue #6698 treated rebuilding them as a bug [PR #6717] (v2.15).
- Rebuild queries were redesigned for large bases (tested on 2 million Contacts) and must never return duplicate Contact IDs [PR #1193] (v1.2.3).
- ORDER BY was dropped from membership queries. Batches work against a fixed pool bounded by the max Contact ID at start. Why: query time on large bases [PR #1290] (v1.2.4).
- A newly qualifying Contact with an ID between existing members must not cause higher-ID members to be removed. Why: removal and re-add reset `date_added` and restarted Segment-triggered Campaigns [PR #2716] (v2.2.1).
- Orphans are removed in batches, not all at once. Why: memory and long queries [PR #6825] (v2.15). Since 5.0 the removal uses `NOT IN` on `lead_lists_leads` (excluding manual adds) instead of a LEFT JOIN on the member query [PR #11583] (v5.0).
- Contact-ID limiters (min/max/single Contact) restrict a rebuild [PR #6600] (v2.15). Batch limiters are also pushed into inner subqueries [PR #11283] (v5.0). An `ids` limiter accepts a set of Contact IDs; core did not use it when added [PR #15629] (v7.1.0).
- Segment SELECT and count queries prefer the read replica [PR #6889] (v2.15). Maintainers use "replica" instead of "slave" [PR #12512].
- `--timing` prints per-Segment build time, and "Total time:" is the sum across Segments [PR #9298] (v3.3) [PR #10208] (v4.1) [PR #11419] (v5.0).
- `-q` prints nothing unless there is an error. Why: cron mails any output (issue #10531) [PR #10533] (v4.0.2).
- With `-i`, a failing or missing Segment returns a non-zero exit code. When rebuilding all Segments, one failure does not stop the others [PR #11439] (v5.0).
- `--exclude` skips Segment IDs. The same option exists on `mautic:campaigns:trigger` and `mautic:campaigns:rebuild` [PR #13383] (v5.1).
- `last_built_date` is set only by a full rebuild, not by ID-range runs. The list warns when it is older than `segment_rebuild_time_warning` hours (default 30) [PR #10772] (v4.2.0).
- `last_built_time` stores the duration of the last full rebuild. The list warns when it exceeds `segment_build_time_warning` seconds (default 30) [PR #11917] (v5.0.0).
- The list shows "Building", "No Contacts", "X Contacts" or "Building (X Contacts)". A Segment needs a rebuild only if it has filters, is published, and was never built or was modified at or after `last_built_date` [PR #14431] (v6.0.0). Unpublished and filterless Segments never show "Building" [PR #14706] (v6.0.0).
- With `--max-contacts`, the count updates after each capped run, and "Building" clears once all matching Contacts are processed. Why: in 7.0 capped runs stuck in "Building" with 0 Contacts shown [PR #17027] (v7.2.0).
- Rebuild membership events carry an explicit date so they can be processed asynchronously. An unbuffered DB connection exists for iterating huge results [PR #12131] (v5.0).
- The rebuild writes "added to segment" and "removed from segment" timeline entries. Why: a regression from #11140 dropped add events [PR #12249] (v5.0).
- Plugins can switch the new-Contact restriction (Contacts created after the rebuild started) without changing the default [PR #12566] (v5.0).
- The webhook subscriber for batch membership changes detaches only the Lead entities it fetched itself. Why: rebuilding 10,000 Contacts ran out of memory. Rejected: detaching in the dispatcher, because later listeners may still need the entities [PR #15881] (v7.0.2).
- Batch segment edits once used a configurable sleep in microseconds [PR #1068] (v1.2.2). Historical: the current `batch_sleep_time` is in seconds (behaviour.md §16.1).

### Segment-membership filters and dependencies
- Membership filters started in 1.2.3 [PR #1193]. In 2.9.1 the referenced Segment's filters were inlined so results did not depend on rebuild order [PR #4482] (v2.9.1) [PR #4529] (v2.9.1). 2.9.2 reworked them to respect manual flags: manually removed Contacts of A do not enter a Segment that includes A, and manually added Contacts of A are excluded from a Segment that excludes A [PR #4544] (v2.9.2).
- Contacts manually added to A count for a Segment that includes A. The query used `IN` instead of `EXISTS` because `EXISTS` was too slow on large databases [PR #6577] (v2.14.2). Since 4.3 Segment subqueries use `EXISTS`/`NOT EXISTS` [PR #10903] (v4.3).
- The include query means "manually added OR not manually removed" [PR #10809] (v4.2.1).
- Leading membership filters keep their stored AND/OR glue [PR #12214] (v5.0). Two membership filters joined by OR give the union [PR #12530] (v5.0).
- Since 7.0 a membership filter reads the referenced Segment's stored rows in `lead_lists_leads`, and the command rebuilds referenced Segments first. Circular and missing references are detected. Why: rebuild time fell from about 673 s to 80 s in test. Superseded: re-running the referenced Segment's filter query. Recorded as a BC break in UPGRADE-7.0.md [PR #15031] (v7.0).
- A Segment can select itself in its own membership filter in the UI (raised in 4.2.1, left out of scope) [PR #10809] (v4.2.1). Since 7.0 circular references are rejected; behaviour.md §11 lists form save, query build and the command [PR #15031] (v7.0).
- A Segment cannot be deleted while another Segment depends on it. In 2.15.1 the check covered only Segments [PR #6566] (v2.15.1). In 7.x a Campaign source also blocks unpublish and delete (behaviour.md §13) [PR #6566].
- Membership filters on company-field Segments must not error [PR #5472] (v2.12.1).

### Filter logic: glue and OR merging
- `A AND B OR C AND D` means `(A AND B) OR (C AND D)`. The UI indents AND rows under the preceding OR. Why: issues #1367 and #1374 [PR #2304] (v2.1.1).
- Company and contact filters share one ordered AND/OR expression. Why: OR between a company filter and a contact filter was impossible [PR #4369] (v2.9.0).
- A plugin filter injected through the filtering event keeps its sibling filters [PR #4886] (v2.10.1). A regexp filter does not invert later filters [PR #4659] (v2.10.0).
- OR-ed `=` filters on the same field are merged into one `IN`. Why: long OR chains made rebuilds slow [PR #11007] (v5.1.0). Numeric and boolean values are no longer cast to float, so the merged `IN` and REGEXP values stay intact [PR #14555] (v6.0.0).
- Date and datetime filters are never merged into `IN`. Why: the date option factory needs string values and threw a TypeError on arrays (e.g. `birthday +1 days`) [PR #15702] (v7.0.1).
- Same-table filters (Visited URL plus Visited URL count) briefly shared one sub-query [PR #7424] (v2.16.1). This was reverted because tag and email-read Segments broke; same-table filters are evaluated independently again [PR #8653] (v2.16.2).

### Operators and NULL semantics
- `!=` includes Contacts whose field is NULL. Operator labels became words in the same change [PR #432] (v1.1).
- "Not like" on a behaviour filter includes Contacts with no activity. Why: "did not visit a page like X" should include Contacts with no page hits. Rejected: inner-join semantics [PR #4228] (v2.9.0).
- `contains`, `startsWith` and `endsWith` were added for Segment and Report filters. Why: regexp is too hard for most users [PR #4274] (v2.9.0). The PR wrapped `like` values in `%` only when the value did not start with `%`; behaviour.md §5 records "unless `%` is already present" [PR #4274].
- Invalid regular expressions are rejected on save instead of failing at rebuild [PR #4659] (v2.10.0). Regexp works on Visited URL [PR #6641] (v2.14.2) [PR #11541] (v4.4.4).
- Lookup-ID fields such as owner offer only `=`, `!=`, `empty`, `!empty`. Why: `owner contains 1` matched users 1, 10, 11 [PR #5134] (v2.11.0). The owner filter stores a user ID [PR #3643] (v2.7.1). The `lookup_id` type is generic [PR #8555] (v3.0.0).
- Multiselect filters compare stored option values, not labels; old Segments had to be re-saved [PR #5533] (v2.13.0). Values with apostrophes match [PR #6306] (v2.14.1) [PR #2342] (v2.1.1). Values with regex metacharacters such as `(` match literally [PR #9376] (v3.2.0) [PR #10218] (v4.2.0).
- Multiselect "exclude" includes Contacts with a NULL or empty value. Why: `NOT REGEXP` dropped NULL rows; maintainers accepted that results change [PR #12906] (v5.1).
- Multiselect fields support `empty`/`!empty` [PR #6684] (v2.14.2). Multiselect and locale filters do not offer `>`/`<` [PR #2713] (v2.2.1).
- Select options with numeric keys match [PR #2145] (v2.1.0). Boolean filters store 0/1, not the label; a migration converted old filters [PR #2995] (v2.3).
- `empty`/`!empty` on foreign-table filters (tags, devices, companies) mean "has no related row" / "has at least one row". Why: `tag empty` matched nobody [PR #11253] (v4.4.1).
- Text fields accept include/exclude with `|`-separated values. Pasting a spreadsheet column converts line breaks to `|` [PR #10256] (v4.1).
- A NULL `properties.filter` is normalised and does not produce `<> Array` SQL [PR #13344] (v5.1).
- Stage `=` uses EXISTS and `!=` uses NOT EXISTS; stage `empty`/`!empty` exist [PR #3890] (v2.9.0) [PR #3989] (v2.8.1).
- Email read count `= 0` matches Contacts with no reads [PR #5043] (v2.11.0).

### Multi-value operators (any of / all of)
- Four operators replaced the ambiguous "including"/"excluding": "including any of" (`in`), "including all of" (`in_all`), "excluding any of" (`!in`), "excluding all of" (`!in_all`). Why: "including" meant "any" for tags but "all" for multiselect. `OperatorOptions::IN`/`NOT_IN` stay as deprecated aliases, so stored `in`/`!in` now mean "any of" [PR #15344] (v7.0.0).
- The new operators also apply in Dynamic Content, email filter matching and the Campaign field-value condition [PR #15344] (v7.0.0).
- Multiselect "including" with several values matches Contacts holding any one of them [PR #15473] (v7.0.0); first fixed for multi-option Contacts in [PR #4097] (v2.9.0).
- "All of" is offered only for multiselect fields. Why: a single-value field cannot hold all of several values, and company select fields threw `Dunno how to handle operator "in_all"` [PR #16012] (v7.1.1). Company multiselect "including any of" now means "any" [PR #16012] (v7.1.1).
- Conflict: [PR #15344] lists tags and Segment membership among the fields with all four operators. behaviour.md §4 shows only `in`/`!in` for `tags`, `leadlist` and `campaign`. behaviour.md wins.

### Date filters
- Values starting with `+` or `-` are relative and evaluated at each rebuild [PR #1587] (v2.0.0). `first day of` and `last day of` phrases are relative too. Why: issue #9636, Contacts never aged out [PR #10822] (v5.1.0).
- `last year`, `this year` and `next year` resolve to year boundaries [PR #5411] (v2.12.1).
- `anniversary` (and legacy `birthday`) matches month and day in any year [PR #4333] (v2.10.0). It accepts an offset such as `anniversary -7 days` [PR #6993] (v2.15.1) [PR #7853] (v2.16.1). It works on datetime fields [PR #13871] (v5.1.1).
- Date filters respect `default_timezone` [PR #7097] (v2.15.1). Datetime columns compare in UTC and date columns in local time. Why: at 22:00 in New York a date of today did not match [PR #7244] (v2.15.2). An empty timezone setting falls back to UTC [PR #14549] (v5.2.3).
- For `yesterday`/`today`/`tomorrow` on datetime fields, `>` and `<=` use 23:59:59 and `>=` and `<` use 00:00:00 [PR #14552] (v6.0.0).
- Date `empty`/`!empty` work on MySQL 8 (no `<> ''` on date columns) [PR #11126] (v4.3).
- Relative values with hours (`-1 hour`) compare with time precision on datetime fields, and the base is the current time. `like`/`!like` still ignore time [PR #16135] (v7.2.0).
- `inLast`/`inNext` take a positive whole-number interval and a unit, are offered in Segments only, and store `{interval, unit}` in `properties.filter` [PR #16574] (v7.2.0).
- "Date modified" is empty for new Contacts until the first update; this was accepted as intended [PR #3216] (v2.6.0).
- Company date filters join the companies table [PR #6675] (v2.14.2).

### Behaviour filters and the filter catalogue
- "Email Received" was relabelled "Email Read", but the stored key `lead_email_received` was kept. Rejected: renaming the key without a migration [PR #2118] (v2.1.1).
- "Read any email (date)" compares the most recent read date per Contact (MAX). Why: "not read in the last 180 days" included Contacts with a recent read [PR #16224] (v7.1.3).
- Behaviour filters are offered only in Segments. Dynamic Content offers contact and company fields only, because its matcher evaluates only those [PR #9260] (v3.3). Tags are available in Dynamic Content [PR #10067] (v4.0).
- Unpublished fields and fields not available for segments are not offered [PR #5906] (v2.13.1). A deleted field must not make a Segment match everyone [PR #3592] (v2.8.0). A missing table (for example a disabled Custom Objects plugin) is logged and handled [PR #13391] (v5.1).
- Legacy filters without `object` default to the contact object [PR #7236] (v2.15.2). Pre-4.2 behaviour filters stored with `object = lead` map to `behaviors` [PR #11003] (v4.2.1).
- The Campaign membership filter counts active membership only [PR #5911] (v2.15).
- Click filters ("Clicked any link from any email/text message", with date variants) and "Unsubscribed SMS – Manual" were added. A date click filter may have an empty date [PR #9852] (v4.3).
- "Subscribed Categories" lists all categories, not the first 10 [PR #9176] (v3.1.1). The asset filter lists all assets [PR #7911] (v2.15).

### Company filters
- Company filters gained two groups: "Contact's primary company" and "Any associated company". "Any associated company" matches when at least one company matches [PR #15800] (7.x after 7.2.1, unreleased).
- A company and a contact field with the same alias are resolved by object [PR #6510] (v2.14.2).

### Counts, charts and caching
- List counts load by AJAX from a count cache [PR #11071] (v4.3). With `update_segment_contact_count_in_background = true` (default false), `lead:list:count-cache-update` recounts [PR #14911] (v7.0.0). The cache moved from the database to the configured cache provider. Why: many small cache queries drove MySQL to 100 % CPU [PR #15554] (v7.0.0).
- The detail chart counts additions from `lead_event_log` only, without a same-day-removal subquery and without double counting [PR #9263] (v3.3) [PR #10432] (v5.1.0). The first-event lookup forces index `IDX_SEARCH` [PR #11766] (v5.0).
- The detail page shows total and active Contacts; active excludes any DNC [PR #15290] (v7.0.0).
- `mautic:segments:stat` lists where published Segments are used [PR #14575] (v6.0.0).
- Contact search `segment:{alias}` uses an `EXISTS` subquery that excludes manually removed rows [PR #9944] (v5.1).

### Lifecycle, preference centre, permissions and API
- "Available in Preference Center" controls what a Contact can change; "Public" controls use by other users [PR #6410] (v2.15). Segments have a public name shown in the preference centre [PR #8238] (v3.2). The preference centre sorts by public name, then ID [PR #15850] (v7.2.0).
- With `delete_segment_in_background = true`, deletion soft-deletes and `mautic:segment:delete` hard-deletes later. Why: deleting a large Segment was slow [PR #15755] (v7.1.0). `LeadList::getDeleted()` was added later [PR #16093] (v7.2.0).
- Cloning creates a unique alias [PR #14828] (v7.0.0).
- A user with "view own" sees their own non-global Segments and global ones [PR #8957] (v3.0.2).
- Segments can have a category; the API returns it and supports `category:{alias}` search [PR #9544] (v3.3) [PR #9869] (v4.0).
- Saving without changes writes no audit-log entry [PR #9801] (v3.3.3). Add, edit and delete are audit-logged [PR #6719] (v2.15).
- Names may contain `<`, `>`, `&` and `'` and are stored verbatim [PR #12025] (v5.0) [PR #14062] (v5.1.1).
- The segment activity report returns the last 30 days when the API call gives no dates [PR #15140] (v7.0).

### Extension points and query architecture
- 2.14 rewrote the builder around `ContactSegmentService`, decorators, per-type query builders and `ContactSegmentFilterDictionary`, using JOINs. Old repository methods were deprecated, not removed [PR #5755] (v2.14.0). New filters must use the new builder [PR #6182] (v2.15.3).
- `LeadListFiltersDecoratorDelegateEvent` lets plugins decorate non-lead filters [PR #10890] (v4.3). `LIST_FILTERS_MERGE` lets plugins merge filters [PR #13276] (v5.1).
- Segment query classes extend Doctrine's classes instead of copying them [PR #12243] (v5.0).
- Filter icons come from `SegmentFilterIconTrait` [PR #15064] (v7.0.0).
- Leaf classes in Segment queries and decorators are `final`; plugins must use composition [PR #16896] (v7.2.0).

## 3. Regression catalogue

| Symptom | Expected behaviour | PR | Version |
|---|---|---|---|
| **Membership** | | | |
| Manually added Contacts removed on rebuild | Manual adds persist regardless of filters | [PR #123] | 1.0 |
| Campaign add kept `manually_added = 0` after an automatic add | Campaign add sets `manually_added = 1` | [PR #16474] | 7.x (unreleased) |
| "Is a member of segment" false branch never taken | Manually removed Contacts are non-members | [PR #11782] | 5.0 |
| Doctrine cascade-persist error in Campaign segment action | Entity reference used; no error | [PR #13244] | 5.0.3 |
| Campaign listener saw stale membership | Event fired after persist | [PR #1017] | 1.2.1 |
| Notice when an action targets a deleted Segment | Action skipped silently | [PR #283] | 1.0.3 |
| **Rebuild** | | | |
| Higher-ID members removed then re-added | No premature removal; `date_added` stable | [PR #2716] | 2.2.1 |
| Unpublished Segments rebuilt | Skipped | [PR #6717] | 2.15 |
| `m:s:u -q` printed output; cron mailed | Silent unless error | [PR #10533] | 4.0.2 |
| `m:s:u -i 999` exited 0 | Non-zero exit | [PR #11439] | 5.0 |
| `last_built_date` never updated | Updated on every full rebuild | [PR #10772] | 4.2.0 |
| No "added to segment" timeline entry | Entry logged on add | [PR #12249] | 5.0 |
| Unpublished Segment stuck on "Building" | No label | [PR #14706] | 6.0.0 |
| `--max-contacts` stuck "Building" with 0 Contacts | Count updates per run; label clears when done | [PR #17027] | 7.2.0 |
| Rebuild of ~10,000 Contacts ran out of memory | Webhook subscriber releases entities it loaded | [PR #15881] | 7.0.2 |
| **Membership filters** | | | |
| Excluding filter correct only after a second run | Order-independent membership filters | [PR #4482], [PR #4544] | 2.9.1/2.9.2 |
| Include query ignored manual flags | Manually added OR not manually removed | [PR #10809] | 4.2.1 |
| Leading membership filters glued with OR | Stored glue respected | [PR #12214] | 5.0 |
| Two membership filters OR-ed gave wrong set | Correct union | [PR #12530] | 5.0 |
| Membership filter on company-field Segment SQL error | Works | [PR #5472] | 2.12.1 |
| **Filter logic** | | | |
| OR/AND groups built wrong SQL | `(A AND B) OR (C AND D)` | [PR #2304] | 2.1.1 |
| Company OR contact filter joined with AND | One ordered expression | [PR #4369] | 2.9.0 |
| Plugin filter dropped sibling filters | Siblings kept | [PR #4886] | 2.10.1 |
| Filter after a regexp inverted | Not inverted; invalid regex rejected on save | [PR #4659] | 2.10.0 |
| `points = 1 OR 2 OR 3` returned one Contact | Proper `IN` list; regex not cast to float | [PR #14555] | 6.0.0 |
| TypeError with OR-ed date `=` filters | Date filters never merged into `IN` | [PR #15702] | 7.0.1 |
| NULL `properties.filter` produced `<> Array` | NULL normalised | [PR #13344] | 5.1 |
| **Operators** | | | |
| `!=` excluded NULL | NULL included | [PR #432] | 1.1 |
| "Visited URL not like" omitted Contacts with no hits | Included | [PR #4228] | 2.9.0 |
| `owner contains 1` matched users 10, 11 | Owner limited to `=`/`!=`/empty/!empty | [PR #5134] | 2.11.0 |
| Multiselect compared labels | Compares values | [PR #5533] | 2.13.0 |
| Multiselect value "First (1)" never matched | Regex characters quoted | [PR #9376], [PR #10218] | 3.2.0/4.2.0 |
| Multiselect exclude dropped NULL Contacts | NULL and empty included | [PR #12906] | 5.1 |
| Multiselect empty/!empty crashed after 2.14 | Works | [PR #6684] | 2.14.2 |
| "Tag empty" matched nobody | Empty = no related row | [PR #11253] | 4.4.1 |
| Visited URL regexp ignored | Regex applied | [PR #11541] | 4.4.4 |
| Boolean filter stored the label and matched all | Stores 0/1 | [PR #2995] | 2.3 |
| Numeric select options did not match | Numeric keys kept | [PR #2145] | 2.1.0 |
| Email read count `= 0` found nobody | Matches zero reads | [PR #5043] | 2.11.0 |
| Stage `!=` returned Contacts in that stage | Excluded | [PR #3989], [PR #3890] | 2.8.1/2.9.0 |
| **Any of / all of** | | | |
| Multiselect "including" dropped single-value holders | Any listed value matches | [PR #15473] | 7.0.0 |
| "Including" meant "any" for tags and "all" for multiselect | Explicit any/all operators | [PR #15344] | 7.0.0 |
| `Dunno how to handle operator "in_all"` on company select | "All of" only on multiselect | [PR #16012] | 7.1.1 |
| Company multiselect "any of" acted like "all of" | Matches any value | [PR #16012] | 7.1.1 |
| **Dates** | | | |
| Date = today missed in a UTC-5 evening | Date fields compared in local time | [PR #7244] | 2.15.2 |
| `default_timezone` ignored | Respected | [PR #7097] | 2.15.1 |
| Empty timezone setting broke relative-date rebuild | Falls back to UTC | [PR #14549] | 5.2.3 |
| "greater than last year" matched nothing | Year keywords resolve to boundaries | [PR #5411] | 2.12.1 |
| Anniversary offsets broken | Restored with tests | [PR #7853] | 2.16.1 |
| Anniversary on datetime never matched | Month-day match | [PR #13871] | 5.1.1 |
| `>`/`<=` with today/yesterday/tomorrow wrong | 23:59:59 / 00:00:00 boundaries | [PR #14552] | 6.0.0 |
| MySQL 8 error 1525 on date empty filter | No `<> ''` on date columns | [PR #11126] | 4.3 |
| Relative date saved as absolute; Contacts never left | Relative values kept | [PR #10822] | 5.1.0 |
| `-1 hour` on datetime added no Contacts | Time precision kept | [PR #16135] | 7.2.0 |
| Company date filter queried the leads table | Joins companies | [PR #6675] | 2.14.2 |
| **Behaviour filters** | | | |
| "Read any email (date) < 180 days ago" included recent readers | Uses MAX read date | [PR #16224] | 7.1.3 |
| Behaviour filters in Dynamic Content did nothing | Not offered there | [PR #9260] | 3.3 |
| Tags missing from Dynamic Content filters | Offered with names | [PR #10067] | 4.0 |
| Deleted custom field made a Segment match all | Filter ignored safely | [PR #3592] | 2.8.0 |
| Disabled Custom Objects table crashed rebuild | Logged and handled | [PR #13391] | 5.1 |
| Pre-4.2 Visited URL filter lost operators | Legacy object mapped | [PR #11003] | 4.2.1 |
| Unpublished fields offered in filters | Hidden | [PR #5906] | 2.13.1 |
| Only 10 categories in category filter | All offered | [PR #9176] | 3.1.1 |
| **Entity, UI, API** | | | |
| "View own" user could not see own Segment | Own and global Segments listed | [PR #8957] | 3.0.2 |
| Clone kept alias and said "Updated" | Unique alias; "Created" | [PR #14828] | 7.0.0 |
| `<` in name or option failed validation | Saves | [PR #12025] | 5.0 |
| `R&D` displayed as `R&#38;D` | Stored verbatim | [PR #14062] | 5.1.1 |
| Audit entry on save without change | No entry | [PR #9801] | 3.3.3 |
| List count stale | Recount instantly or by cron | [PR #14911] | 7.0.0 |
| Segments list "More" category filter returned nothing | Filter matches by the right key | [PR #15598] | 7.1.0 |
| Segment log report API 500 without dates | Defaults to last 30 days | [PR #15140] | 7.0 |
| Chart added Contacts one day early; timeouts | Correct day; no removal subquery | [PR #9263] | 3.3 |
| Chart double-counted additions | Event log only | [PR #10432] | 5.1.0 |

## 4. Feature timeline

| Version | Change | PR |
|---|---|---|
| 1.0–1.4 | Manual membership flags; large-base rebuild with `-i`; page-visited filter; `mautic:segments:update` naming | [PR #123], [PR #1193], [PR #1567], [PR #1644] |
| 2.0–2.3 | Relative dates; stage filter; AND/OR grouping UI; boolean 0/1 | [PR #1587], [PR #1924], [PR #2304], [PR #2995] |
| 2.6–2.8 | Date modified filter; page and email activity filters; Top Segments link | [PR #3216], [PR #3477], [PR #3230] |
| 2.9–2.11 | Device filters; `contains`/`startsWith`/`endsWith`; anniversary; regex validation; lookup_id | [PR #3888], [PR #4274], [PR #4333], [PR #4659], [PR #5134] |
| 2.14 | Builder refactor; UTM filters | [PR #5755], [PR #5886] |
| 2.15 | Campaign membership filter; preference-centre flag; delete guard; audit log; batch removal; replica reads; timezone-aware dates | [PR #5911], [PR #6410], [PR #6566], [PR #6719], [PR #6825], [PR #6889], [PR #7244] |
| 2.16 | Segment stats charts and usage | [PR #7285] |
| 3.0–3.2 | Generic lookup_id; public name | [PR #8555], [PR #8238] |
| 3.3 | Segment categories; build timing | [PR #9544], [PR #9298] |
| 4.0 | Category in API and search; segment activity report | [PR #9869], [PR #8125] |
| 4.1 | Text include/exclude with `\|` values | [PR #10256] |
| 4.2.0 | `last_built_date` and stale warning | [PR #10772] |
| 4.3 | Click filters; EXISTS subqueries; async list counts; decorator delegate event | [PR #9852], [PR #10903], [PR #11071], [PR #10890] |
| 5.0 | `last_built_time` warning; exit codes; timeline add events; unbuffered connection | [PR #11917], [PR #11439], [PR #12249], [PR #12131] |
| 5.1 | OR-merge into `IN`; `--exclude`; `first/last day of`; merge-filters event; multiselect exclude includes NULL | [PR #11007], [PR #13383], [PR #10822], [PR #13276], [PR #12906] |
| 5.2.3 | Empty timezone falls back to UTC | [PR #14549] |
| 6.0.0 | "Building" states; `mautic:segments:stat`; today/tomorrow boundaries | [PR #14431], [PR #14575], [PR #14552] |
| 7.0.0 | Any/all operators; dependency-aware rebuild; background count cache; cache provider; active Contacts; filter icons | [PR #15344], [PR #15031], [PR #14911], [PR #15554], [PR #15290], [PR #15064] |
| 7.0.1–7.0.2 | No `IN` merge for dates; webhook subscriber memory fix | [PR #15702], [PR #15881] |
| 7.1.0 | Background delete; `ids` limiter; list quick filters fixed | [PR #15755], [PR #15629], [PR #15598] |
| 7.1.1 | "All of" only on multiselect | [PR #16012] |
| 7.1.3 | Email read date uses MAX | [PR #16224] |
| 7.2.0 | `inLast`/`inNext`; hour-level relative dates; preference-centre order; `--max-contacts` completion; `final` classes | [PR #16574], [PR #16135], [PR #15850], [PR #17027], [PR #16896] |
| 7.x after 7.2.1 | "Any associated company" filters; Campaign add sets `manually_added` | [PR #15800], [PR #16474] |

## 5. Removed, deprecated, replaced

| What | Replaced by | PR | Version |
|---|---|---|---|
| `mautic:lists:*` and other command synonyms | `mautic:segments:update` (alias `mautic:segments:rebuild`) | [PR #1644] | 1.4 |
| "Email Received" label | "Email Read" label, key `lead_email_received` kept | [PR #2118] | 2.1.1 |
| Boolean label values | 0/1, migration Version20161123225456 | [PR #2995] | 2.3 |
| `LeadListRepository::getLeadsByList()`, `getListFilterExpr` builder | `ContactSegmentService` and query builders | [PR #5755] | 2.14.0 |
| `DateDecorator::getDefaultDate()` | `DateOptionParameters::getDefaultDate()` | [PR #7244] | 2.15.2 |
| Shared same-table sub-queries | Reverted | [PR #8653] | 2.16.2 |
| `LeadListRepository::generateSegmentExpression()` | Removed (dead code), listed in UPGRADE-3.0.md | [PR #8549] | 3.0.0 |
| Behaviour filters in Dynamic Content | Contact and company filters only | [PR #9260] | 3.3 |
| `IN`/`NOT IN` segment subqueries | `EXISTS`/`NOT EXISTS` | [PR #10903] | 4.3 |
| `QueryBuilder::getJoinCondition()`, `replaceJoinCondition()` | Deprecated | [PR #9944] | 5.1 |
| Users LEFT JOIN in the contact list base query | Removed | [PR #13481] | 5.1 |
| `SegmentReferenceFilterQueryBuilder` and re-running the referenced Segment's query | Stored membership via `ForeignValueFilterQueryBuilder`; listed in UPGRADE-7.0.md | [PR #15031] | 7.0 |
| Ambiguous "including"/"excluding" | Any of / all of; `OperatorOptions::IN`/`NOT_IN` deprecated | [PR #15344] | 7.0.0 |
| Database count cache (`CacheStorageHelper`) | `CacheProvider` | [PR #15554] | 7.0.0 |
| "All of" on single-select fields | "Any of" only | [PR #16012] | 7.1.1 |
| Extending Segment query and decorator classes | `final` classes | [PR #16896] | 7.2.0 |

## 6. Maintainer norms for this area
- Stored filter keys are BC. Change the label, not the key, unless a migration and BC code come with it [PR #2118].
- Fixing a stored-data bug needs a migration for existing records [PR #2995] [PR #6410] [PR #8238].
- New Segment filters go into the Segment/Query builder architecture, not the old repository [PR #6182] [PR #6306].
- Segment queries are judged on millions of Contacts or page hits. Performance PRs show before/after SQL and timings [PR #1193] [PR #3477] [PR #9944] [PR #10903] [PR #11766] [PR #15031].
- Behaviour-changing Segment features may wait for acceptance testing on large data sets [PR #3477] [PR #7424].
- A revert that restores known-working behaviour can merge without separate testing [PR #8653].
- Bug fixes need a test that fails without the fix, ideally functional and following the PR's test steps [PR #15702] [PR #13871] [PR #11253] [PR #14706].
- Bug fixes target the current patch branch; enhancements target the next-minor branch. Fixes are merged up by "Merging fixes from X to 7.x" PRs [PR #10904] [PR #16012] [PR #16071].
- Options for large instances go behind config flags that default to the old behaviour [PR #15554] [PR #15755].
- A subscriber must not detach entities passed to it by the event; it may detach entities it fetched itself [PR #15881].
- New entity properties need tested migrations and OpenAPI updates [PR #15755] [PR #11917].
- New commands and filters need user docs [PR #14575] [PR #13383] [PR #10256].
- Production evidence on large instances is accepted for small, well-tested fixes [PR #12530] [PR #15031] [PR #12131].
- Fixes for Custom Objects that cannot be tested in the UI may merge on code review plus PHPUnit tests [PR #13391] [PR #13484] [PR #15253].
- Do not copy Doctrine code; extend it [PR #12243].
- Tests must not define `MAUTIC_TABLE_PREFIX` [PR #11622].

## 7. Open questions
- [PR #15031]: the chunk notes say `ContactSegmentFilterDictionary` was removed. It was not. UPGRADE-7.0.md:62 lists only `SegmentReferenceFilterQueryBuilder`, and the dictionary exists at tags 7.0.0 and 7.2.1 and on the 7.x head [code: UPGRADE-7.0.md:62 @7.x] [code: app/bundles/LeadBundle/Services/ContactSegmentFilterDictionary.php @7.x]. Resolved.
- [PR #14911]: the count-cache command is `lead:list:count-cache-update` (`SegmentCountCacheCommand::COMMAND_NAME`) [code: app/bundles/LeadBundle/Command/SegmentCountCacheCommand.php:22 @7.x]. Resolved.
- [PR #15473], [PR #16474], [PR #15800]: dated by merge date, not the chunk header. #15473 merged 2025-09-05 and first ships in 7.0.0. #16474 merged 2026-09-23 and #15800 merged 2026-10-05; neither is in 7.2.1, so both are unreleased on 7.x [PR #15473] [PR #16474] [PR #15800]. Resolved.
- Conflict with behaviour.md: [PR #15344] says tags and Segment membership get all four any/all operators; behaviour.md §4 offers only `in`/`!in` for them. behaviour.md wins [PR #15344].
- Conflict with behaviour.md: [PR #4274] wraps `like` values unless they start with `%`; behaviour.md §5 says unless `%` is present anywhere. behaviour.md wins [PR #4274].
- Conflict with behaviour.md: [PR #15702] describes OR-merging into `IN` only for 3 or more filters. The current factory groups any stack of two or more after AND handling, and SKILL.md states no threshold. Not verified by a test [PR #15702] [code: app/bundles/LeadBundle/Segment/ContactSegmentFilterFactory.php:161-172 @7.x].
- [PR #1068]: the batch sleep was in microseconds; the current `batch_sleep_time` is in seconds. Historical [PR #1068].
- [PR #16012]: how Segments saved with `in_all` on single-select fields are treated. behaviour.md §4 says `in_all` with more than one value never matches there [PR #16012].
- [PR #15800]: negative operators in "Any associated company" are not spelled out in the PR. behaviour.md §8 says `company_all` never matches Contacts without a company [PR #15800].
- [PR #16224]: the docs title says all behavioural date filters use the latest date; only `lead_email_read_date` is confirmed [PR #16224].
- [PR #16135]: whether a base time of "now" changes day-level relative values such as `-1 day` on datetime fields [PR #16135].
- [PR #16574]: which non-Segment contexts exclude `inLast`/`inNext`; the test step was truncated [PR #16574].
- [PR #11253]: "tag empty" includes anonymous Contacts; whether that is intended generally [PR #11253].
- [PR #10822]: a reviewer saw a relative date stored as absolute and the author could not reproduce it [PR #10822].
- [PR #8745]: a 2020 comment says the Citrix `array_flip` calls broke segment builds; the later fate of that code is unknown [PR #8745].
- [PR #11419]: a reviewer saw a first Segment's time exceed the total; unresolved [PR #11419].
- [PR #3216]: date modified "equals today" only matched with `>=`; deferred [PR #3216].
- [PR #12566]: the option name for the new-Contact restriction is not given [PR #12566].

## 8. Coverage
The inputs cover 204 PRs in 3 chunks: 104 (2015-03 to 2020-04, plus the late merges #8125 and #8238), 80 (2020-05 to 2025-08) and 20 (2025-09 to 2026-10).
Of these, 190 are substantive, 13 are noise and 1 is unclear (#107, title only).
A further 869 noise PRs (dependency bumps, translations, CI) were excluded upstream before chunking.
