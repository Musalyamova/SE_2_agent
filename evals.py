import time
import pandas as pd
from graph import app
from rich.console import Console
from rich.table import Table
from memory_manager import remember_project_rule

console = Console()

remember_project_rule("В этом проекте строго запрещено использовать библиотеку pickle из-за RCE.")

EVAL_CASES = [
    {
        "id": 1,
        "name": "SQL-инъекция",
        "code": """
def get_user(username, password):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchall()
""",
        "expected_vuln": True
    },
    {
        "id": 2,
        "name": "Небезопасный pickle",
        "code": """
import pickle
import base64

def load_data(data):
    decoded = base64.b64decode(data)
    return pickle.loads(decoded)
""",
        "expected_vuln": True
    },
    {
        "id": 3,
        "name": "Безопасный код",
        "code": """
def add(a, b):
    result = a + b
    return result
""",
        "expected_vuln": False
    }
]

results = []
correct_predictions = 0

console.print("[bold yellow]Запуск автоматической оценки (Evals)...[/bold yellow]\n")

for case in EVAL_CASES:
    console.print(f"Выполняется тест: {case['name']}...")

    start_time = time.time()

    config = {"configurable": {"thread_id": f"eval_session_{case['id']}"}}
    result = app.invoke(
        {"code": case["code"], "language": "python", "messages": [], "thread_id": f"eval_session_{case['id']}"},
        config=config
    )

    end_time = time.time()
    latency = end_time - start_time

    findings = result.get("review_findings", [""])[0].lower()
    found_vuln = any(
        word in findings for word in ["уязвим", "инъекц", "rce", "pickle", "ошибк"]) and "не найдено" not in findings

    is_correct = (case["expected_vuln"] == found_vuln)
    if is_correct:
        correct_predictions += 1

    validator_verdict = result.get("messages", [""])[-1]
    is_validated = "подтверждено" in validator_verdict.lower()

    results.append({
        "Тест": case["name"],
        "Ожидаемая уязвимость": "Да" if case["expected_vuln"] else "Нет",
        "Обнаружено агентом": "Да" if found_vuln else "Нет",
        "Вердикт валидатора": "Подтверждено" if is_validated else "Отклонено",
        "Время (сек)": round(latency, 2),
        "Модель": result.get("chosen_model", "unknown")
    })

accuracy = correct_predictions / len(EVAL_CASES)

df = pd.DataFrame(results)
table = Table(title="Результаты тестирования агентной системы")
for col in df.columns:
    table.add_column(col)

for _, row in df.iterrows():
    table.add_row(*[str(val) for val in row.values])

console.print(table)

console.print(f"\n[bold cyan]Итоговые метрики:[/bold cyan]")
console.print(f"Accuracy (Точность классификации): {accuracy:.2%}")
console.print(f"Средняя задержка (Latency): {df['Время (сек)'].mean():.2f} сек.")

df.to_csv("evals_report.csv", index=False, encoding="utf-8")
console.print("\n[green]Данные сохранены в файл evals_report.csv[/green]")