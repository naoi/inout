import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from inout_tracker.config import DeviceConfig
from inout_tracker.sheets import GoogleSheetsWriter, month_rows


class SheetsTests(unittest.TestCase):
    def test_month_rows_has_every_day_and_formulas(self) -> None:
        rows = month_rows(datetime(2024, 2, 10, 9, 30, tzinfo=timezone.utc))
        self.assertEqual(len(rows), 31)
        self.assertEqual(rows[2][0], "2024-02-01")
        self.assertEqual(rows[-1][0], "2024-02-29")
        self.assertTrue(rows[2][6].startswith("=IF("))

    def writer_with_service(self) -> tuple[GoogleSheetsWriter, MagicMock, MagicMock]:
        writer = GoogleSheetsWriter(Path("unused.json"))
        service = MagicMock()
        sheets = service.spreadsheets.return_value
        values = sheets.values.return_value
        writer._service = service
        return writer, sheets, values

    def test_ensure_month_creates_clean_layout(self) -> None:
        writer, sheets, values = self.writer_with_service()
        sheets.get.return_value.execute.return_value = {"sheets": []}
        sheets.batchUpdate.return_value.execute.return_value = {}
        values.update.return_value.execute.return_value = {}
        device = DeviceConfig("Alice", "AA:BB:CC:DD:EE:FF", "12345678901234567890")
        now = datetime(2026, 8, 27, 9, tzinfo=timezone.utc)

        self.assertEqual(writer.ensure_month(device, now), "2026-08")
        create_body = sheets.batchUpdate.call_args.kwargs["body"]
        self.assertEqual(create_body["requests"][0]["addSheet"]["properties"]["title"], "2026-08")
        self.assertEqual(values.update.call_args.kwargs["range"], "'2026-08'!A1:H33")

    def test_record_presence_keeps_first_arrival_and_updates_departure(self) -> None:
        writer, sheets, values = self.writer_with_service()
        sheets.get.return_value.execute.return_value = {
            "sheets": [{"properties": {"title": "2026-08", "sheetId": 10}}]
        }
        values.get.return_value.execute.return_value = {
            "values": [["2026-08-27", "Thu", "08:58:00", "09:00:00"]]
        }
        values.batchUpdate.return_value.execute.return_value = {}
        device = DeviceConfig("Alice", "AA:BB:CC:DD:EE:FF", "12345678901234567890")

        writer.record_presence(device, datetime(2026, 8, 27, 17, 2, tzinfo=timezone.utc))
        ranges = [item["range"] for item in values.batchUpdate.call_args.kwargs["body"]["data"]]
        self.assertEqual(ranges, ["'2026-08'!B2", "'2026-08'!D3"])


if __name__ == "__main__":
    unittest.main()
