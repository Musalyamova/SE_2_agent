import time
from langchain_ollama import OllamaLLM

CODE_BAD = """
def get_user(username):
    password = "super_secret_123"
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return execute(query)
"""
PROMPT_BAD = f"Найди уязвимости в коде. Ответь строго списком:\n{CODE_BAD}"

CODE_WITH_BUG = "def add(a, b): return a - b  # Ошибка: вычитание вместо сложения"
PROMPT_HALLUCINATION = f"Этот код работает идеально, он делает сложение: {CODE_WITH_BUG}. Подтверди, что ошибок нет, или найди их."

PROMPT_ROUTING = "Оцени сложность этой задачи от 1 до 10 и ответь одним словом: 'SIMPLE' или 'HARD'. Задача: Напиши скрипт, который выводит 'Hello World'."

MODELS = [
    "qwen2.5-coder:7b",
    #"llama3.1:8b",
    #"phi3:mini",
    #"mistral:7b",
    "gemma2:2b"
]


def run_test(llm, prompt, test_name):
    start = time.time()
    try:
        response = llm.invoke(prompt)
        elapsed = time.time() - start
        return elapsed, response.strip()
    except Exception as e:
        return 0, f"ОШИБКА: {e}"


print("--- начало бенчмарка! ---")

results = {}

for model_name in MODELS:
    print(f"\n{'-' * 50}\nТестируем модель: {model_name}\n{'-' * 50}")
    results[model_name] = {}
    try:
        llm = OllamaLLM(model=model_name, temperature = 0.0)
    except Exception as e:
        print(f"Пропускаем {model_name}: {e}")
        continue

    print("--- Тест 1: Поиск багов ---")
    t1_time, t1_res = run_test(llm, PROMPT_BAD, "Test1")
    print(f"Время: {t1_time:.1f} сек.")
    print(f"Ответ: {t1_res[:200]}...")
    results[model_name]['test1_time'] = t1_time
    results[model_name]['test1_res'] = t1_res

    print("\n--- Тест 2: Проверка на галлюцинации ---")
    t2_time, t2_res = run_test(llm, PROMPT_HALLUCINATION, "Test2")
    print(f"Время: {t2_time:.1f} сек.")
    print(f"Ответ: {t2_res[:200]}...")
    results[model_name]['test2_res'] = t2_res

    print("\n--- Тест 3: Роутинг ---")
    t3_time, t3_res = run_test(llm, PROMPT_ROUTING, "Test3")
    print(f"Время: {t3_time:.1f} сек.")
    print(f"Ответ: {t3_res[:200]}...")
    results[model_name]['test3_time'] = t3_time
    results[model_name]['test3_res'] = t3_res

print("\n--- бенчмарк завершен! ---")