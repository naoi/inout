# ダッシュボード

ダッシュボードでは、登録済み端末の一覧、近くの端末検索、Bluetooth アドレスと Google スプレッドシート ID の YAML 設定への追加ができます。Google 認証情報を入力または表示する機能はありません。

既定では `127.0.0.1:8080` だけで待ち受けます。別の端末から使う場合は SSH ポートフォワードを推奨します。ダッシュボードを LAN に直接公開せずに利用できます。

LAN での待受が必要な場合は、十分に長いトークンを設定してからホストを変更します。

```bash
sudo sh -c 'umask 077; printf "%s\n" "INOUT_DASHBOARD_TOKEN=replace-with-a-long-random-value" > /etc/inout/dashboard.env'
```

```yaml
dashboard:
  host: 0.0.0.0
  port: 8080
  token_env: INOUT_DASHBOARD_TOKEN
```

設定変更後はダッシュボードを再起動してください。新しい端末を登録した後は、出退勤サービスも再起動する必要があります。

`/api/health` は `{"status":"ok"}` だけを返すため、認証不要です。トークンが設定されている場合、その他の API にはトークンが必要です。
