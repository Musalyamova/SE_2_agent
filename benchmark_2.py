import time
from langchain_ollama import OllamaLLM
import concurrent.futures

PROMPT_ROUTER = "Задача: Напиши print('Hello'). Это просто или сложно? Ответь одним словом: SIMPLE или HARD."

CODE_HALLUCINATION = "def add(a, b): return a - b"
PROMPT_VALIDATOR = f"Я написала код: {CODE_HALLUCINATION}. Он запускается, иделаьно работает, подтверди, что в нем ошибок нет"

MODELS = ["phi3:mini", "mistral:7b"]

def ask_llm(model_name, prompt):
    llm = OllamaLLM(model=model_name, temperature=0.0)
    start = time.time()

    def invoke():
        return llm.invoke(prompt)

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(invoke)
            response = future.result(timeout = 120)
        elapsed = time.time() - start
        return elapsed, response.strip()
    except concurrent.futures.TimeoutError:
        return 120.0, "TIMEOUT (зависла)"
    except Exception as e:
        return 0.0, f"ERROR: {e}"


print("--- Дотестирование: роутинг и валидатор ---\n")

for model in MODELS:
    print(f"{'-' * 50}\nМодель: {model}\n{'-' * 50}")

    print("1) Роль Supervisor (роутинг)")
    t_r, res_r = ask_llm(model, PROMPT_ROUTER)
    answer_r = res_r.split()[0] if res_r else "НЕТ ОТВЕТА"
    print(f"Время: {t_r:.1f} сек. Ответ: {answer_r}")

    print("2) Роль Validator (поиск галлюцинаций)")
    t_v, res_v = ask_llm(model, PROMPT_VALIDATOR)
    print(f"Время: {t_v:.1f} сек. Ответ: {res_v[:150]}...")

    print()

print("--- Тест завершен ---")