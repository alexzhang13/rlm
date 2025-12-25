from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass


@dataclass
class REPLResult:
    stdout: str
    stderr: str
    locals: dict
    execution_time: float

    def __init__(
        self, stdout: str, stderr: str, locals: dict, execution_time: float = None
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.locals = locals
        self.execution_time = execution_time

    def __str__(self):
        return f"REPLResult(stdout={self.stdout}, stderr={self.stderr}, locals={self.locals}, execution_time={self.execution_time})"


class BaseEnv(ABC):
    """
    Base REPL-like environment that the RLM uses to interact with. The primary types are isolated and non-isolated,
    where isolated environments are on a separate machine from the LM.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def setup(self, action: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def execute_code(self, code: str) -> REPLResult:
        raise NotImplementedError


class IsolatedEnv(BaseEnv, ABC):
    """
    These environments (e.g. Prime Envs, Modal Envs) sit on a completely separate machine from the LM,
    guaranteeing complete isolation from the LM process.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def setup(self, action: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def execute_code(self, code: str) -> REPLResult:
        raise NotImplementedError


class NonIsolatedEnv(BaseEnv, ABC):
    """
    These environments run on the same machine as the LM, and provide different levels of isolation
    depending on the choice of environment. The simplest, default is a local Python REPL that runs
    as a subprocess.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def setup(self, action: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def execute_code(self, code: str) -> REPLResult:
        raise NotImplementedError
