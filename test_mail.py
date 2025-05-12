import smtplib
from email.mime.text import MIMEText


def send_email():
    from_email = "chihiro0506i@gmail.com"
    to_email = "chihiro0506i@gmail.com"
    app_password = "zrbhynyczkidfaoj"  # スペースなし！

    subject = "リマインダー通知テスト"
    body = "これは reminder-app からのテストメールです。"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(from_email, app_password)
            smtp.send_message(msg)
        print("✅ メール送信成功！")
    except Exception as e:
        print("❌ メール送信失敗：", e)


# 関数を呼び出す
send_email()
