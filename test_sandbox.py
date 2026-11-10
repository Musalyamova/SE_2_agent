import os
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

load_dotenv()


if not os.getenv("E2B_API_KEY"):
    print("Ошибка: ключ E2B_API_KEY не найден в .env")
else:
    print("Ключ найден, подключаемся к песочнице")
    try:
        sbx = Sandbox.create()
        print("Песочница создана!")

        execution = sbx.run_code("print('Хелоу из облачной песочницы!')")
        print("Результат:", "".join(execution.logs.stdout))

        sbx.kill()
        print("Песочница закрыта")
    except Exception as e:
        print(f"Ошибка подключения: {e}")