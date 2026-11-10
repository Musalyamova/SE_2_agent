# main.py
import os
from rich.console import Console
from rich.prompt import Prompt
from graph import app
from examples import EXAMPLES

console = Console()


def run():
    console.print("[bold cyan]AI Code Review Agent[/bold cyan]")
    console.print("Выберите пример для проверки:")
    for key, (name, _) in EXAMPLES.items():
        console.print(f"  {key}. {name}")
    console.print("  0. Ввести свой код")

    choice = Prompt.ask("Ваш выбор", choices=["0", "1", "2", "3"], default="1")

    if choice == "0":
        console.print("Введите код (для завершения введите 'END' на новой строке):")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        code = "\n".join(lines)
        case_name = "Пользовательский код"
    else:
        case_name, code = EXAMPLES[choice]

    console.print(f"\n[bold yellow]Запуск проверки: {case_name}[/bold yellow]")

    config = {"configurable": {"thread_id": f"session_{case_name}"}}
    result = app.invoke({"code": code, "language": "python", "messages": []}, config=config)

    console.print("\n[bold green]Результат:[/bold green]")
    console.print(result["final_report"])


if __name__ == "__main__":
    run()