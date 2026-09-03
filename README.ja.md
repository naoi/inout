# In-Out Tracker

[English](README.md)

In-Out Tracker は、Raspberry Pi で動く出退勤記録アプリです。設定した Bluetooth 端末を検出し、その日の最初と最後の検出時刻を Google スプレッドシートへ記録します。端末の検索と登録に使える小さなローカルダッシュボードも含みます。

## iPhone に関する重要な制約

iOS は、iPhone が安定した Bluetooth アドレスを常に送信することを保証しません。通常の iPhone は、検出可能、ペアリング済み、接続中、または対応するビーコンアプリで発信中の場合にしか見つからないことがあります。給与や安全管理に利用する前に、必ず実機で継続検出を確認してください。安定性が必要な場合は専用 BLE ビーコンを推奨します。

## 主な機能

- Python 3.9 以降、BlueZ、Google サービスアカウント認証
- ポーリングごとに 1 回だけ Bluetooth をスキャンし、一時的な未検出を猶予時間で吸収
- クリーンな月次シートの自動生成、または同一ブック内の任意テンプレート複製
- 端末単位のエラー分離、再試行、構造化ログ、検出状態の永続化
- レスポンシブなローカルダッシュボード。localhost 以外ではトークン必須
- systemd、設定検査、テスト、日英ドキュメント

## クイックスタート

Raspberry Pi OS、Bluetooth、Python 3.9 以降、Google Cloud プロジェクト、Google サービスアカウントが必要です。

```bash
git clone https://github.com/naoi/inout.git
cd inout
sudo ./INSTALL.sh
sudoedit /var/lib/inout/config.yaml
sudo -u inout /opt/inout/venv/bin/inout --config /var/lib/inout/config.yaml check-config
sudo systemctl enable --now inout inout-dashboard
```

インストーラーは、設定とアクセス確認が終わるまでサービスを起動しません。

ダッシュボードは Raspberry Pi 上の <http://127.0.0.1:8080> で開きます。別の端末から安全に利用する場合は SSH ポートフォワードを使います。

```bash
ssh -L 8080:127.0.0.1:8080 pi@raspberrypi.local
```

その後、手元のブラウザーで <http://127.0.0.1:8080> を開きます。

## Google スプレッドシートの準備

1. Google Cloud プロジェクトで Google Sheets API を有効にします。
2. サービスアカウントを作り、JSON キーをダウンロードします。
3. 利用者ごとにスプレッドシートを作成します。
4. 各スプレッドシートをサービスアカウントのメールアドレスへ編集者として共有します。
5. JSON キーを `/etc/inout/google-service-account.json` に安全な権限で保存します。
6. [config.example.yaml](config.example.yaml) を `/var/lib/inout/config.yaml` にコピーし、Bluetooth アドレスとスプレッドシート ID を設定します。

アプリは `YYYY-MM` タブを自動生成します。既存レイアウトを使う場合のみ、同じスプレッドシート内のタブ ID を `template_sheet_id` に指定します。新規利用では指定しないことを推奨します。

元プロジェクトから参照されていた履歴用ブックは、多数の過去タブと壊れた数式参照を含むため、公開テンプレートには使いません。詳細は [Google Sheets 設計](docs/google-sheets.ja.md) を参照してください。

## コマンド

```bash
inout --config /var/lib/inout/config.yaml check-config
inout --config /var/lib/inout/config.yaml scan
inout --config /var/lib/inout/config.yaml run --once
inout --config /var/lib/inout/config.yaml run
inout --config /var/lib/inout/config.yaml dashboard
```

## ドキュメント

- [インストールと設定](docs/setup.ja.md)
- [ダッシュボードと端末登録](docs/dashboard.ja.md)
- [Google Sheets のレイアウト](docs/google-sheets.ja.md)
- [トラブルシューティング](docs/troubleshooting.ja.md)
- [セキュリティポリシー](SECURITY.md)
- [コントリビューション](CONTRIBUTING.md)

## 開発

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
```

Bluetooth と Google API は小さなインターフェースに分離しているため、単体テストは実機や認証情報なしで実行できます。

## ライセンス

MIT
