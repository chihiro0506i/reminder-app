# Raspberry Pi リマインダーアプリ開発記録

## 🛠 開発目的
Python + Flask + SQLite + APScheduler を用いて、Raspberry Pi 上で常時稼働するリマインダーアプリを構築。学習用を目的とし、Web経由で予定を登録し、指定時刻にメールまたは将来的にLINE通知を行う。

---

## 📁 技術スタック
- **言語**：Python 3
- **Webフレームワーク**：Flask
- **DB**：SQLite3
- **通知方法**：Gmail + アプリパスワード（SMTP）、LINE Notify（検討・終了予定）
- **スケジューリング**：APScheduler
- **デプロイ環境**：Raspberry Pi 5（Debian 12）
- **開発環境**：Windows + VSCode、最終的にPiへSSH転送

---

## 🔄 開発ステップと進捗

### ① 最初の構築（Windows上）
- FlaskでWebアプリ作成（予定登録・表示機能）
- SQLiteで予定保存（DB構造設計とテーブル作成）
- `app.py`：Flaskのメインアプリ
- `scheduler.py`：通知スケジューラ（毎分チェック）

### ② UI改善
- HTMLテンプレート整理（Jinja2）
- Bootstrapでスタイル改善
- カレンダーUI（FullCalendar）で視覚表示
- タグ・カテゴリ機能追加（DBカラム拡張）

### ③ 通知機能実装
- GmailからSMTP通知テスト → 成功
- アプリパスワードを用いたセキュアな認証に対応
- 通知ログをファイル保存（logs/）

### ④ LINE Notify検討
- アカウント作成・LINE Developers登録
- Messaging API設定試行 → サービス終了予定のため保留

### ⑤ Raspberry Pi 環境構築
- Piにreminder-appを転送（SCP）
- 仮想環境構築（venv）
- Flask・APSchedulerインストール
- 外部アクセス用に `host='0.0.0.0'` を設定
- `app.py`と`scheduler.py` を手動で常時起動

---

## 🚀 現在の運用
- LAN内から `http://192.168.11.11:5000` でアクセス可
- Raspberry Pi は HDMIなしでも稼働中
- 予定はPCやスマホから登録、Piが通知処理を担当

---

## ✅ 今後の拡張候補
- Apache2 + mod_wsgi で常時公開
- systemd による自動起動設定
- LINE Bot通知（Messaging APIベース）
- ログイン認証の導入
- 外部アクセス対応（ngrok, Zerotier）

---

_最終更新：2025-05-10 05:03:25_

