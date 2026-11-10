import os
import sqlite3
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from state import AgentState
from tools import run_code_in_sandbox
from memory_manager import get_project_rules, init_db, learn_new_fact

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_prompt(filename):
    path = os.path.join(BASE_DIR, "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_skill(skill_name):
    path = os.path.join(BASE_DIR, "skills", f"{skill_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


gemma = OllamaLLM(model="gemma2:2b", temperature=0.0)
qwen = OllamaLLM(model="qwen2.5-coder:7b", temperature=0.0)
llama = OllamaLLM(model="llama3.1:8b", temperature=0.0)

init_db()
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory_saver = SqliteSaver(conn)


def supervisor_node(state: AgentState):
    print("\n--- Supervisor (Роутинг и Скиллы) ---")
    code = state['code']

    is_code_prompt = f"Это фрагмент исходного кода программы? Ответь только одним словом YES или NO.\nТекст:\n{code}"
    is_code = gemma.invoke(is_code_prompt).strip().upper()
    if "NO" in is_code:
        print("Jev-like Guardrail: Входные данные — не код. Прерывание флоу.")
        return {"messages": ["Supervisor: SKIP"], "review_findings": ["Это не код."], "chosen_model": "none",
                "reflection_count": 0}

    dangerous_keywords = ["SELECT", "execute", "pickle", "os.system", "eval", "exec", "subprocess"]
    is_dangerous = any(word.upper() in code.upper() for word in dangerous_keywords)
    lines_count = len(code.strip().split('\n'))

    if is_dangerous or lines_count > 5:
        chosen_model = "qwen"
        print(f"Роутинг: Опасные паттерны или {lines_count} строк. Выбран Qwen 7B.")
    else:
        chosen_model = "gemma"
        print(f"Роутинг: Тривиальный код. Выбрана Gemma 2B.")

    skill_content = ""
    if "SELECT" in code.upper() or "EXECUTE" in code.upper():
        print("Supervisor: Подгружаем скилл 'sql_injection'")
        skill_content = load_skill("sql_injection")
    elif "pickle" in code or "os.system" in code:
        print("Supervisor: Подгружаем скилл 'pickle_rce'")
        skill_content = load_skill("pickle_rce")

    return {"messages": ["Supervisor: CHECK"], "skill_context": skill_content, "chosen_model": chosen_model,
            "reflection_count": 0, "feedback": ""}


def route_supervisor(state: AgentState):
    if "SKIP" in state.get("messages", []):
        return "report"
    return "reviewer"


def reviewer_node(state: AgentState):
    print("\n--- Reviewer (Поиск уязвимостей) ---")
    rules = get_project_rules()
    skill = state.get("skill_context", "")
    chosen_model = state.get("chosen_model", "qwen")
    feedback = state.get("feedback", "")

    prompt = load_prompt("reviewer.md")

    full_prompt = f"""{prompt}
{rules if rules else "Правил нет."}

{skill if skill else "Нет."}

{feedback if feedback else "Нет фидбэка (первая итерация)."}

Код:
{state['code']}
"""
    result = gemma.invoke(full_prompt) if chosen_model == "gemma" else qwen.invoke(full_prompt)
    print(f"Находки: {result.strip()[:100]}...")

    return {"review_findings": [result.strip()]}


def validator_node(state: AgentState):
    print("\n--- Validator (Кросс-валидация Llama) ---")
    prompt = load_prompt("validator.md")
    findings = state.get('review_findings', [''])[-1]
    current_reflection = state.get("reflection_count", 0)

    validation_prompt = f"""{prompt}
Исходный код:
{state['code']}

Находки Ревьюера:
{findings}
"""
    result = llama.invoke(validation_prompt)
    verdict = result.strip().upper()
    print(f"Вердикт Валидатора: {verdict[:50]}...")

    if "[ЛОЖНОЕ СРАБАТЫВАНИЕ]" in verdict and current_reflection < 1:
        print(f"Валидатор: Ошибка. Отправка на Reflection (Попытка {current_reflection + 1})")
        return {
            "messages": ["Validator: К доработке"],
            "feedback": f"Ты допустил ошибку. Исправь анализ: {result}",
            "reflection_count": current_reflection + 1
        }

    if "[ПОДТВЕРЖДЕНО]" in verdict:
        learned_rule = result.replace("[ПОДТВЕРЖДЕНО]", "").strip()
        msg = learn_new_fact(learned_rule)
        print(f"Память обновлена: {msg}")

    return {"messages": ["Validator: Валидация успешна"], "feedback": "", "reflection_count": current_reflection}


def route_validator(state: AgentState):
    if state.get("messages", []) and "К доработке" in state["messages"][-1]:
        return "reviewer"
    return "sandbox"


def sandbox_node(state: AgentState):
    print("\n--- Sandbox (E2B) ---")
    system_prompt = """Задача: написать локальный Python-скрипт для демонстрации уязвимости.
    Запрещено использовать библиотеку requests, urllib или делать сетевые запросы (интернета нет).
    Если уязвимость связана с SQL (инъекция) — создай тестовую БД sqlite3, таблицу users (name, password), добавь 'admin', 'secret' и вызови функцию.
    Если уязвимость связана с RCE (например, pickle) — попробуй выполнить безопасную команду (например, print("RCE_SUCCESS")).
    Обязательно выведи результат в консоль через print(result).
    Формат: только код Python, без текста."""

    test_prompt = f"{system_prompt}\n\nУязвимый код:\n{state['code']}"
    test_code = qwen.invoke(test_prompt)
    test_code = test_code.replace("```python", "").replace("```", "").strip()

    if "import" in test_code:
        test_code = test_code[test_code.find("import"):]
    elif "def " in test_code:
        test_code = test_code[test_code.find("def "):]

    print(f"Отправляем код в E2B...")
    result = run_code_in_sandbox(test_code)
    print(f"Результат: {result[:100]}...")
    return {"test_code": test_code, "test_results": result}


def report_node(state: AgentState):
    print("\n--- Report ---")
    findings = state.get('review_findings', [''])[-1]  # Берем последнюю актуальную находку
    sandbox_res = state.get('test_results', "Результат не был получен")

    final = f"# Отчет\n\n## Находки:\n{findings}\n\n## Результаты автотестов (E2B):\n{sandbox_res}"
    return {"final_report": final}


workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("validator", validator_node)
workflow.add_node("sandbox", sandbox_node)
workflow.add_node("report", report_node)

workflow.set_entry_point("supervisor")
workflow.add_conditional_edges("supervisor", route_supervisor, {"report": "report", "reviewer": "reviewer"})
workflow.add_edge("reviewer", "validator")
workflow.add_conditional_edges("validator", route_validator, {"reviewer": "reviewer", "sandbox": "sandbox"})
workflow.add_edge("sandbox", "report")
workflow.add_edge("report", END)

app = workflow.compile(checkpointer=memory_saver)

if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from memory_manager import remember_project_rule

    console = Console()

    console.print("[bold cyan]Проверяем/добавляем правило в долгосрочную память...[/bold cyan]")
    remember_project_rule("В этом проекте строго запрещено использовать библиотеку pickle из-за RCE.")

    test_cases = [
        {
            "name": "SQL-инъекция (короткий код)",
            "code": """
def get_user(username):
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return execute(query)
"""
        },
        {
            "name": "Небезопасный pickle (длинный код)",
            "code": """
import pickle
import base64

def load_data(data):
    decoded = base64.b64decode(data)
    return pickle.loads(decoded)

def process_user_input(user_input):
    if user_input:
        return load_data(user_input)
    return None
"""
        }
    ]

    for i, case in enumerate(test_cases, 1):
        console.print(Panel(f"[bold yellow]Тест {i}: {case['name']}[/bold yellow]", expand=False))

        config = {"configurable": {"thread_id": f"test_session_{i}"}}

        result = app.invoke(
            {"code": case["code"], "language": "python", "messages": [], "thread_id": f"test_session_{i}"},
            config=config
        )

        console.print(Panel(result["final_report"], title="[bold green]Финальный отчет агента[/bold green]", border_style="green"))
        console.print("\n")