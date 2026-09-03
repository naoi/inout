# トラブルシューティング

## `bluetoothctl was not found`

`sudo apt-get install bluez bluetooth` で BlueZ を導入し、`systemctl status bluetooth` を確認します。

## iPhone が一度だけ見つかり、その後は見つからない

多くの iOS 設定で起こり得る動作です。検出テストでは「設定」の Bluetooth 画面を開いたままにします。無人運転では、可能ならペアリングまたは接続を行うか、安定した識別情報を発信する専用 BLE ビーコンを使ってください。検出率を測る前にスキャン頻度だけを上げないでください。

## BlueZ から `Permission denied` が返る

`id inout` でサービスユーザーが `bluetooth` グループに所属していることを確認します。グループを変更した後はサービスを再起動します。

## Google が 403 を返す

Google Sheets API が有効であること、対象スプレッドシートがサービスアカウント JSON の `client_email` に編集者として共有されていることを確認します。その後 `inout ... check-config` を再実行します。

## 今月のタブを作れない

`template_sheet_id` を指定した場合、そのタブ ID が同じスプレッドシート内に存在することを確認します。組み込みのクリーンなレイアウトを使う場合は、この設定を削除します。

## 時刻が記録されない

`journalctl -u inout` で端末単位のエラーを確認します。1 台の Sheets 更新に失敗しても、ほかの端末のスキャンは継続します。次回の検出時に再試行し、C 列は最初に書き込めた時刻を保持し、D 列は更新されます。
