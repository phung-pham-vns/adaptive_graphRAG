from typing import Optional

from ragas import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import AnswerAccuracy

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


class Metrics:
    def __init__(
        self,
        llm_provider: str = "gemini",
        llm_model: str = "gemini-2.5-pro",
        llm_api_key: Optional[str] = None,
    ):
        if llm_provider == "openai":
            llm_judge = LangchainLLMWrapper(
                ChatOpenAI(
                    model=llm_model,
                    temperature=0.0,
                    seed=42,
                )
            )
        elif llm_provider == "gemini":
            llm_judge = LangchainLLMWrapper(
                ChatGoogleGenerativeAI(
                    model=llm_model,
                    temperature=0.0,
                    model_kwargs={"seed": 42},
                    google_api_key=llm_api_key,
                )
            )

        self.answer_accuracy_scorer = AnswerAccuracy(llm=llm_judge)

    def answer_accuracy(self, question: str, reference: str, response: str) -> float:
        score = self.answer_accuracy_scorer.single_turn_score(
            SingleTurnSample(
                user_input=question,
                reference=reference,
                response=response,
            )
        )
        return score


if __name__ == "__main__":
    from src.settings import settings

    metrics = Metrics(
        llm_provider=settings.llm_provider,
        llm_model="gemini-2.5-pro",
        llm_api_key=settings.llm_api_key,
    )
    print(metrics.answer_accuracy("What is the capital of France?", "Paris", "Paris"))
