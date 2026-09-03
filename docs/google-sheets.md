# Google Sheets design

## Built-in layout

For a new month, the application creates a `YYYY-MM` tab with two header rows and one row per calendar day.

| Column | Content |
| --- | --- |
| A | ISO date |
| B | Day of week |
| C | First Bluetooth sighting, treated as arrival |
| D | Latest Bluetooth sighting, treated as departure |
| E | Manual remote-work hours |
| F | Manual break hours |
| G | Calculated hours |
| H | Calculated overtime above eight hours |

Rows use ISO dates and English formula names so behavior is independent of the spreadsheet locale. Times are written with seconds.

## Existing templates

Set `template_sheet_id` only when the template tab is in the same spreadsheet as the attendance data. When the month is missing, the app duplicates that tab and sets `A3` to the first day of the month. The template must keep dates in column A, arrival in C, and departure in D.

## Why there is no shared historical workbook

The workbook linked by the earlier version was inspected read-only. It is a long-lived personal workbook with more than 200 historical monthly tabs and a `YYYY-MM` tab containing broken and inconsistent formula references. Copying the entire workbook would expose unrelated history, and publishing only the tab would preserve those defects.

The built-in generated layout is therefore the reproducible OSS default. A future public visual template should be created as a separate, data-free workbook and tested against the column contract above. Do not make the historical workbook public.
