# インストールと設定

## Raspberry Pi

サポート中の Raspberry Pi OS を使ってください。インストール前に Bluetooth アダプターを確認します。

```bash
bluetoothctl show
```

`sudo ./INSTALL.sh` を実行します。このスクリプトは必要な OS パッケージだけを導入し、権限を制限した `inout` ユーザー、`/opt/inout` の仮想環境、2 つの systemd ユニットを作ります。OS 全体のアップグレードやアプリの自動起動は行いません。

## Google 認証情報

1. Google Cloud Console で Google Sheets API を有効にします。
2. サービスアカウントと JSON キーを作ります。
3. 対象スプレッドシートをサービスアカウントのメールアドレスへ編集者として共有します。
4. キーを安全な権限で配置します。

```bash
sudo install -m 0640 -o root -g inout downloaded-key.json /etc/inout/google-service-account.json
```

JSON キーは秘密情報です。Git にコミットしないでください。

## 設定

[config.example.yaml](../config.example.yaml) を基に `/var/lib/inout/config.yaml` を編集します。

| 設定 | 意味 |
| --- | --- |
| `polling_interval_seconds` | スキャン完了後から次回までの間隔 |
| `absence_grace_seconds` | 未検出を不在と判定するまでの猶予 |
| `bluetooth_scan_seconds` | BlueZ の 1 回の検索時間 |
| `state_file` | 最終検出状態の保存先 |
| `google.credentials_file` | サービスアカウント JSON のパス |
| `dashboard.host` / `port` | ダッシュボードの待受先。既定は localhost |
| `devices[].address` | 検出対象の安定した Bluetooth アドレス |
| `devices[].spreadsheet_id` | Sheets URL の `/d/` と `/edit` の間の ID |
| `devices[].template_sheet_id` | 同じスプレッドシート内にある任意のテンプレートタブ ID |

サービスを有効にする前に確認します。

```bash
sudo -u inout /opt/inout/venv/bin/inout --config /var/lib/inout/config.yaml check-config
sudo -u inout /opt/inout/venv/bin/inout --config /var/lib/inout/config.yaml scan
sudo -u inout /opt/inout/venv/bin/inout --config /var/lib/inout/config.yaml run --once
sudo systemctl enable --now inout inout-dashboard
```

ログは `journalctl -u inout -f` と `journalctl -u inout-dashboard -f` で確認できます。
