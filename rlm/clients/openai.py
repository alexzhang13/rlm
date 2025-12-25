from rlm.clients.base_lm import BaseLM

from typing import Dict, Any
import openai


class OpenAIClient(BaseLM):
    """
    LM Client for running models with the OpenAI API.
    """

    def __init__(self, api_key: str, model_name: str, **kwargs):
        super().__init__(**kwargs)

        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name

    def completion(self, prompt: str | Dict[str, Any]) -> str:
        if isinstance(prompt, str):
            prompt = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, Dict[str, Any]):
            prompt = [{"role": "user", "content": prompt["content"]}]
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        return (
            self.client.chat.completions.create(model=self.model_name, messages=prompt)
            .choices[0]
            .message.content
        )

    async def acompletion(self, prompt: str | Dict[str, Any]) -> str:
        if isinstance(prompt, str):
            prompt = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, Dict[str, Any]):
            prompt = [{"role": "user", "content": prompt["content"]}]
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        return (
            await self.client.chat.completions.create(
                model=self.model_name, messages=prompt
            )
            .choices[0]
            .message.content
        )
