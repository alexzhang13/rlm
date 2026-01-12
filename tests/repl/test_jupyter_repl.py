import pytest

from rlm.environments.jupyter_repl import JupyterREPL


def test_jupyter_repl_execution(tmp_path):
    pytest.importorskip("IPython")

    repl = JupyterREPL(workdir=str(tmp_path))

    result1 = repl.execute_code("x = 10")
    assert result1.stderr == ""

    result2 = repl.execute_code("import os\ncwd = os.getcwd()")
    assert result2.stderr == ""
    assert repl.locals["cwd"] == str(tmp_path)

    result3 = repl.execute_code("print(x)")
    assert "10" in result3.stdout

    repl.cleanup()
