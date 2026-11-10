import sqlite3

conn = sqlite3.connect('long_term_memory.db')
cursor = conn.cursor()
cursor.execute("SELECT id, kind, content, status FROM facts")
rows = cursor.fetchall()

print(f"{'ID':<5} | {'Тип (Kind)':<15} | {'Правило':<80} | {'Статус'}")
print("-" * 120)
for row in rows:
    print(f"{row[0]:<5} | {row[1]:<15} | {row[2]:<80} | {row[3]}")
conn.close()