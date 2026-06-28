import sqlite3
conn = sqlite3.connect(r'E:\元枢法智前端\yuanxing\backend\cases-crawler\data\lexprime.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', cur.fetchall())
for t in ('cases','laws','companies','lawyer_added_cases'):
    try:
        cur.execute(f'SELECT count(*) FROM {t}')
        print(f'{t}:', cur.fetchone()[0])
    except Exception as e:
        print(f'{t}: N/A ({e})')
print('--- sample case ---')
cur.execute('SELECT case_id, case_name, court, cause, year FROM cases LIMIT 3')
for row in cur.fetchall():
    print(row)
print('--- cause categories distribution ---')
cur.execute('SELECT cause_category, count(*) FROM cases GROUP BY cause_category ORDER BY 2 DESC')
for row in cur.fetchall():
    print(row)