
import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# 教材リスト
c.execute(
    '''
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    '''
)

# 学習セッション履歴
c.execute(
    '''
    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        duration INTEGER,
        FOREIGN KEY (material_id) REFERENCES materials (id)
    )
    '''
)

conn.commit()
conn.close()

print("✅ 'materials' および 'study_sessions' テーブルを作成しました。")
