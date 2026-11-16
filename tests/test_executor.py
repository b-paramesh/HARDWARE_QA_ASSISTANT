from core.executor import run_tool

def test_unknown_tool_rejected():
    result = run_tool("execute_user_shell")
    assert result["ok"] is False
    assert "allow-listed" in result["error"]
