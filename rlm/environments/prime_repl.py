from rlm.environments.base_env import IsolatedEnv


class PrimeREPL(IsolatedEnv):
    def __init__(
        self,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        sandbox_name: str | None = None,
        api_key: str | None = None,
        **kwargs,
    ):
        pass

    def setup(self):
        pass

    def load_context(self, context_payload: dict | list | str):
        pass

    def execute_code(self, code: str):
        pass

    def cleanup(self):
        pass
