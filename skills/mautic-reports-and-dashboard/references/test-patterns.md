# Reports, Dashboard and Stats: test patterns

## Base classes
- Unit tests extend `PHPUnit\Framework\TestCase` [code: app/bundles/ReportBundle/Tests/Builder/MauticReportBuilderTest.php @7.x].
- Functional tests extend `Mautic\CoreBundle\Test\MauticMysqlTestCase`, which sets the PHP timezone to UTC [code: app/bundles/CoreBundle/Test/MauticMysqlTestCase.php:71 @7.x]. Examples include `ReportControllerFunctionalTest`, `ReportApiControllerTest`, `ReportApiDateHandlingTest`, `ReportOnDashboardAsTableFunctionalTest`, both `ExportSchedulerCommandTest`s, `DashboardControllerFunctionalTest` and `Tests/Model/ReportModelTest`.
- `DynamicFiltersTypeIntegrationTest` uses Symfony `TypeTestCase`. `ReportSearchScopeProviderTest` extends `SearchScopeProviderTestCase`.

## Shared helpers
- `app/bundles/ReportBundle/Tests/Functional/AbstractReportSubscriberTestCase.php` provides:
  - `createReport(source, columns, filters, order)`.
  - `verifyReport(id, expectedRows)`, which parses `#reportTable` in the HTML view.
  - `verifyApiReport(id, expectedRows)`.

  It sets `useCleanupRollback=false` and `authenticateApi=true`. Other bundles' context tests extend it.
- `app/bundles/ReportBundle/Tests/Fixtures.php` holds canned `getReportData()` results, headers, aggregated results and a `ReportBuilderEvent` data set (`:12-385`).

## Representative tests (read these first)
| Test | What it shows |
|---|---|
| `app/bundles/ReportBundle/Tests/Builder/MauticReportBuilderTest.php` | Filters, OR groups (`testOrFiltersKeepRemainingAndGroup`), empty values, relative dates (`testRelativeDatetimeEqualityUsesTheWholePeriod`, `testRelativeAnniversary*`), GROUP BY completion (`testGroupByCompletes*`), tags, column sanitisation |
| `app/bundles/ReportBundle/Tests/Controller/ReportControllerFunctionalTest.php` | Create/clone, order, SQL injection, aggregates + totals export (`testEmailReportWithAggregatedColumnsAndTotals`), `testScheduleEdit` matrix (`:380-446`), `testDelayedTransport` (scheduler → email → attachment removal), dynamic filters |
| `app/bundles/ReportBundle/Tests/Functional/Api/ReportApiDateHandlingTest.php` | API dates and timezone offsets |
| `app/bundles/ReportBundle/Tests/Controller/Api/ReportApiControllerTest.php` | `viewown` vs `viewother`, list `select` |
| `app/bundles/ReportBundle/Tests/Unit/Model/ReportModelTest.php` | UI date range normalisation (`testThatGetReportDataUsesCorrectDataRange`) |
| `app/bundles/ReportBundle/Tests/Model/ReportModelTest.php` | ORDER BY sanitisation (`testFormulaColumnOrderUsesFormulaExpression`, `testInvalidOrderColumnIsRemoved`) |
| `app/bundles/ReportBundle/Tests/Crate/ReportDataResultTest.php`, `Tests/Model/CsvExporterTest.php` | Totals across batches, CSV format |
| `app/bundles/ReportBundle/Tests/Model/ReportExporterTest.php`, `Tests/Scheduler/Model/SendScheduleTest.php`, `SchedulerPlannerTest.php`, `Tests/Scheduler/Date/DateBuilderTest.php`, `Tests/Scheduler/Builder/*Test.php`, `Tests/Scheduler/Validator/ScheduleIsValidValidatorTest.php` | Scheduling pipeline |
| `app/bundles/ReportBundle/Tests/Helper/RelativeDateHelperTest.php`, `Tests/Form/DataTransformer/ReportFilterDataTransformerTest.php` | Relative detection, UTC conversion |
| `app/bundles/ReportBundle/Tests/Scheduler/Command/ExportSchedulerCommandTest.php` | `testCommandExecutesNormally`, `testCleanupOnlyDoesNotProcessExports` |
| `app/bundles/DashboardBundle/Tests/Controller/DashboardControllerFunctionalTest.php` | Report, best-hours, segment build time, audit log and upcoming emails widgets |
| `app/bundles/DashboardBundle/Tests/Model/DashboardModelTest.php` | `testGetDefaultFilterFromSession`, `testPopulateWidgetContentCatchesExceptionAndSetsGenericErrorMessage` |
| `app/bundles/DashboardBundle/Tests/Event/WidgetDetailEventTest.php` | Cache key behaviour |
| `app/bundles/StatsBundle/Tests/Aggregate/Collection/CalculatorTest.php`, `CollectorTest.php`, `DAO/StatsDAOTest.php` | Gap filling, UTC bucketing |

[code: app/bundles/ReportBundle/Tests/ @7.x] [code: app/bundles/DashboardBundle/Tests/ @7.x] [code: app/bundles/StatsBundle/Tests/ @7.x]

## What a good regression test asserts
- **Query builder**: the exact WHERE/GROUP BY fragment and bound parameters, for the edge case under test. Typical edges: an empty value, an OR group, `neq` with NULL, a relative period boundary, an anniversary.
- **Context**: the rows returned through both `verifyReport()` and `verifyApiReport()`, including NULL-date rows when `applyDateFilters()` is used.
- **Export**: the header on page 1 only, the totals on the last page only, AVG over all batches, and the "Totals" label.
- **Scheduler**: the scheduler row's `schedule_date` after save, that a NOW Report becomes unscheduled after the command, and that unpublished Reports are skipped but re-planned.
- **Dashboard**: the widget renders for its owner and is denied for another User, a cached flag is set on the second render, and a subscriber exception yields the generic error.
- **Timezones**: set `default_timezone` to a non-UTC zone and assert period edges in UTC (see `ReportApiDateHandlingTest`).

## Skeletons
### New report context (functional)
```php
final class MyContextReportTest extends AbstractReportSubscriberTestCase
{
    public function testRowsAreReturned(): void
    {
        // arrange: persist fixtures (Contacts, hits...) with $this->em, then flush
        $report = $this->createReport('my.context', ['m.id', 'm.date_added'], [
            ['column' => 'm.date_added', 'condition' => 'gte', 'value' => '-7 days', 'glue' => 'and', 'dynamic' => 0],
        ], []);
        $this->verifyReport($report->getId(), [['1', '...']]);
        $this->verifyApiReport($report->getId(), [['id' => '1']]);
    }
}
```
(The helper names come from `AbstractReportSubscriberTestCase`; check their exact signatures in the file before use.)

### Builder unit test
Copy the setup of `MauticReportBuilderTest`: a mocked `Connection` with a real DBAL `QueryBuilder`, a `Report` entity with filters, and a dispatcher stub that sets FROM on `ReportGeneratorEvent`. Then assert `$qb->getSQL()` and `$qb->getParameters()`.

### Scheduler (functional)
Follow `ReportControllerFunctionalTest::testDelayedTransport`:
1. Create a scheduled Report.
2. Wait until its `schedule_date` is due, or set it in the past.
3. Run `$this->testSymfonyCommand('mautic:reports:scheduler', ['--report' => $id])`.
4. Assert the queued email and its attachment, then that the attachment file was removed after the message was handled.

### Widget (functional)
Follow `DashboardControllerFunctionalTest`:
1. Persist a `Widget` with `type`, `params` and `createdBy` set to the test User.
2. Request `/s/dashboard/widget/{id}` with the XHR header.
3. Assert `widgetHtml`.

## Running
- `bin/phpunit app/bundles/ReportBundle/Tests/Builder/MauticReportBuilderTest.php`
- `bin/phpunit --filter testDelayedTransport app/bundles/ReportBundle/Tests/Controller/ReportControllerFunctionalTest.php` (needs the MySQL test DB; see mautic-testing).

## Regression tests worth adding
Rows from the regression catalogue in `references/pr-history.md` with no matching test found by a grep of the 7.x ReportBundle, DashboardBundle and PageBundle tests.

| Behaviour to assert | PR |
|---|---|
| A global `cached_data_timeout` of 0 leaves the widget uncached on the second render | [PR #14467] |
| The tag detail page loads when a Report has an `empty` or `notEmpty` tag filter | [PR #15134] |
| A boolean custom Contact field shows "No" for 0 in the Report table (`normalized_bool`) | [PR #14782] |
| With `csv_always_enclose` on, every CSV cell, including empty ones, is quoted | [PR #7049] |
| The "Most hit email redirects" widget counts hits on the last day of the range and ignores empty filters | [PR #8460] [PR #11086] |
| A boolean filter saves its Yes/No value | [PR #14909] |
| A value stored as `R&R` shows decoded in the table and in CSV | [PR #4088] |
| A Report widget whose Report was deleted renders a "deleted / no data" message | [PR #5196] |

