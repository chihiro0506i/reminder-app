import sqlite3
import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
import os

# ログ出力用ディレクトリ作成
os.makedirs("logs", exist_ok=True)


def send_email(to_email, subject, body):
    from_email = "reminderbot91@gmail.com"
    app_password = "rcfqecjuyqkcoomg"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(from_email, app_password)
        smtp.send_message(msg)


def get_next_datetime(current_dt, repeat):
    dt = datetime.strptime(current_dt, "%Y-%m-%dT%H:%M")
    if repeat == "毎日":
        return dt + timedelta(days=1)
    elif repeat == "毎週":
        return dt + timedelta(weeks=1)
    elif repeat == "毎月":
        try:
            return dt.replace(month=dt.month + 1)
        except ValueError:
            return dt.replace(month=(dt.month % 12) + 1, day=28)
    return None


def check_and_notify():
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT event_id, title, description, event_datetime, remind_datetime, category, repeat
        FROM events
        WHERE notified = 0 AND remind_datetime <= ?
    """,
        (now,),
    )
    events = c.fetchall()

    for event in events:
        event_id, title, desc, event_dt, remind_dt, category, repeat = event
        subject = f"【予定通知】{title}"
        body = f"予定：{title}\n実行日時：{event_dt}\n備考：{desc}"

        try:
            send_email("chihiro0506i@gmail.com", subject, body)
            with open("logs/notify.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] ✅ 通知済: {title}\n")

            if repeat and repeat != "なし":
                next_event_dt = get_next_datetime(event_dt, repeat)
                next_remind_dt = get_next_datetime(remind_dt, repeat)
                if next_event_dt and next_remind_dt:
                    c.execute(
                        """
                        INSERT INTO events (user_id, title, description, event_datetime, remind_datetime, category, repeat, notified)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                        (
                            1,
                            title,
                            desc,
                            next_event_dt.strftime("%Y-%m-%dT%H:%M"),
                            next_remind_dt.strftime("%Y-%m-%dT%H:%M"),
                            category,
                            repeat,
                        ),
                    )

            # 通知済みのイベントを削除
            c.execute("DELETE FROM events WHERE event_id = ?", (event_id,))

        except Exception as e:
            print(f"❌ 通知失敗: {title} → {e}")
            with open("logs/notify.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] ❌ 通知失敗: {title} → {e}\n")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(check_and_notify, "interval", minutes=1)
    print("🔁 スケジューラ起動中...（毎分チェック）")
    scheduler.start()
