
import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# ToDoテーブルを新規作成
c.execute(
    '''
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        is_done BOOLEAN DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )
    '''
)

conn.commit()
conn.close()

print("✅ 'todos' テーブルを作成しました。")
