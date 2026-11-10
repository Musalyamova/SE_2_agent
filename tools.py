import os
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

load_dotenv()


def run_code_in_sandbox(code: str) -> str:
    try:
        sbx = Sandbox.create()
        execution = sbx.run_code(code)

        stdout = "".join(execution.logs.stdout)
        stderr = "".join(execution.logs.stderr)

        sbx.kill()

        if stderr:
            return f"Ошибка выполнения:\n{stderr}"
        return stdout
    except Exception as e:
        return f"Ошибка sandbox: {e}"