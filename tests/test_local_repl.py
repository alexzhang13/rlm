import asyncio
from rlm.environments.local_repl import LocalREPL


def test_persistent_execution():
    """Test that variables persist across multiple code executions."""
    repl = LocalREPL()

    # Set a variable
    result1 = asyncio.run(repl.execute_code("x = 42"))
    assert result1.stderr == ""
    assert "x" in repl.locals
    assert repl.locals["x"] == 42

    # Use the variable in a subsequent execution
    result2 = asyncio.run(repl.execute_code("y = x + 8"))
    assert result2.stderr == ""
    assert repl.locals["y"] == 50

    # Print the variable
    result3 = asyncio.run(repl.execute_code("print(y)"))
    assert "50" in result3.stdout

    repl.cleanup()
