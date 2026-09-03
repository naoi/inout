from __future__ import annotations

import calendar
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DeviceConfig
from .errors import SheetsError


def month_rows(now: datetime) -> list[list[Any]]:
    """Build a compact, locale-independent attendance month."""
    days = calendar.monthrange(now.year, now.month)[1]
    rows: list[list[Any]] = [
        [now.strftime("%Y-%m"), "", "In", "Out", "Remote", "Break", "Hours", "Overtime"],
        ["Last update", now.strftime("%Y-%m-%d %H:%M:%S")],
    ]
    for day in range(1, days + 1):
        row = day + 2
        date = now.replace(day=day)
        rows.append(
            [
                date.strftime("%Y-%m-%d"),
                date.strftime("%a"),
                "",
                "",
                "",
                "",
                f'=IF(AND(C{row}<>"",D{row}<>""),(D{row}-C{row})*24+E{row}-F{row},"")',
                f'=IF(G{row}>8,G{row}-8,"")',
            ]
        )
    return rows


class GoogleSheetsWriter:
    def __init__(self, credentials_file: Path) -> None:
        self.credentials_file = credentials_file
        self._service: Any = None

    @property
    def service(self) -> Any:
        if self._service is None:
            if not self.credentials_file.is_file():
                raise SheetsError(f"Google credentials file not found: {self.credentials_file}")
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build

                credentials = service_account.Credentials.from_service_account_file(
                    str(self.credentials_file),
                    scopes=["https://www.googleapis.com/auth/spreadsheets"],
                )
                self._service = build(
                    "sheets", "v4", credentials=credentials, cache_discovery=False
                )
            except Exception as exc:
                raise SheetsError(f"cannot initialize Google Sheets: {exc}") from exc
        return self._service

    def _sheet_properties(self, spreadsheet_id: str) -> list[dict[str, Any]]:
        try:
            result = (
                self.service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id, fields="sheets.properties")
                .execute()
            )
            return [sheet["properties"] for sheet in result.get("sheets", [])]
        except Exception as exc:
            raise SheetsError(f"cannot read spreadsheet {spreadsheet_id}: {exc}") from exc

    def check_access(self, device: DeviceConfig) -> None:
        self._sheet_properties(device.spreadsheet_id)

    def ensure_month(self, device: DeviceConfig, now: datetime) -> str:
        title = now.strftime("%Y-%m")
        properties = self._sheet_properties(device.spreadsheet_id)
        if any(item.get("title") == title for item in properties):
            return title
        try:
            if device.template_sheet_id is not None:
                if not any(item.get("sheetId") == device.template_sheet_id for item in properties):
                    raise SheetsError(
                        f"template_sheet_id {device.template_sheet_id} does not exist in "
                        f"spreadsheet {device.spreadsheet_id}"
                    )
                request = {
                    "duplicateSheet": {
                        "sourceSheetId": device.template_sheet_id,
                        "insertSheetIndex": 0,
                        "newSheetName": title,
                    }
                }
            else:
                request = {
                    "addSheet": {
                        "properties": {
                            "title": title,
                            "index": 0,
                            "gridProperties": {
                                "rowCount": 40,
                                "columnCount": 8,
                                "frozenRowCount": 2,
                            },
                        }
                    }
                }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=device.spreadsheet_id, body={"requests": [request]}
            ).execute()
            if device.template_sheet_id is None:
                rows = month_rows(now)
                self.service.spreadsheets().values().update(
                    spreadsheetId=device.spreadsheet_id,
                    range=f"'{title}'!A1:H{len(rows)}",
                    valueInputOption="USER_ENTERED",
                    body={"values": rows},
                ).execute()
            else:
                self.service.spreadsheets().values().update(
                    spreadsheetId=device.spreadsheet_id,
                    range=f"'{title}'!A3",
                    valueInputOption="USER_ENTERED",
                    body={"values": [[now.replace(day=1).strftime("%Y-%m-%d")]]},
                ).execute()
        except SheetsError:
            raise
        except Exception as exc:
            raise SheetsError(f"cannot create monthly sheet {title}: {exc}") from exc
        return title

    def record_presence(self, device: DeviceConfig, now: datetime) -> None:
        title = self.ensure_month(device, now)
        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=device.spreadsheet_id, range=f"'{title}'!A3:D40")
                .execute()
            )
            values = result.get("values", [])
            target = now.strftime("%Y-%m-%d")
            index = next(
                (index for index, row in enumerate(values) if row and row[0] == target), None
            )
            if index is None:
                raise SheetsError(f"date {target} was not found in sheet {title}")
            row_number = index + 3
            current = values[index]
            clock = now.strftime("%H:%M:%S")
            data = [
                {"range": f"'{title}'!B2", "values": [[now.strftime("%Y-%m-%d %H:%M:%S")]]},
                {"range": f"'{title}'!D{row_number}", "values": [[clock]]},
            ]
            if len(current) < 3 or not current[2]:
                data.append({"range": f"'{title}'!C{row_number}", "values": [[clock]]})
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=device.spreadsheet_id,
                body={"valueInputOption": "USER_ENTERED", "data": data},
            ).execute()
        except SheetsError:
            raise
        except Exception as exc:
            raise SheetsError(f"cannot record presence for {device.name}: {exc}") from exc
