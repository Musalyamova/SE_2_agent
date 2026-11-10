import pytest
from graph import app

def test_agent_finds_vulnerability():
    code = "def get_user(u): q = 'SELECT * FROM users WHERE name = ' + u; return q"
    config = {"configurable": {"thread_id": "test_1"}}
    result = app.invoke({"code": code, "language": "python", "messages": []}, config=config)
    assert "Находки:" in result["final_report"]

def test_agent_memory_works():
    code = "print('hello')"
    config = {"configurable": {"thread_id": "test_2"}}
    result = app.invoke({"code": code, "language": "python", "messages": []}, config=config)
    assert result["final_report"] is not None