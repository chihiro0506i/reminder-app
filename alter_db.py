import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

try:
    c.execute("ALTER TABLE events ADD COLUMN repeat TEXT DEFAULT 'なし'")
    print("✅ カラム 'repeat' を追加しました。")
except sqlite3.OperationalError as e:
    print("⚠️ すでに存在 or エラー：", e)

conn.commit()
conn.close()
