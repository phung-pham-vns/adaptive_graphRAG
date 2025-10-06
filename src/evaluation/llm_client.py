"""LLM client factory and utilities for evaluation."""

from typing import Optional, Dict, Any, List
from openai import OpenAI

from src.evaluation.config import LLMConfig


class EvaluationLLMClient:
    """
    Wrapper around OpenAI client for evaluation tasks.

    This provides a clean interface for evaluation-specific LLM calls
    with proper error handling and retries.
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize the evaluation LLM client.

        Args:
            config: LLM configuration
        """
        self.config = config
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )

    def create_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Create a chat completion with automatic retries.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional model override (defaults to eval_model)
            temperature: Optional temperature override
            max_retries: Maximum number of retry attempts

        Returns:
            The completion content as a string

        Raises:
            Exception: If all retries fail
        """
        model = model or self.config.eval_model
        temperature = (
            temperature if temperature is not None else self.config.temperature
        )

        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=messages,
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Log retry attempt
                    print(f"Attempt {attempt + 1} failed, retrying... Error: {e}")
                    continue
                else:
                    # All retries exhausted
                    raise Exception(
                        f"Failed after {max_retries} attempts: {last_error}"
                    ) from last_error

    def evaluate_with_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Evaluate using system and user prompts.

        Args:
            system_prompt: System prompt for context
            user_prompt: User prompt with evaluation request
            model: Optional model override
            temperature: Optional temperature override

        Returns:
            The evaluation response
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.create_completion(
            messages=messages, model=model, temperature=temperature
        )


def create_llm_client(config: Optional[LLMConfig] = None) -> EvaluationLLMClient:
    """
    Factory function to create an evaluation LLM client.

    Args:
        config: Optional LLM configuration (defaults to standard config)

    Returns:
        EvaluationLLMClient instance
    """
    if config is None:
        config = LLMConfig()
    return EvaluationLLMClient(config)
