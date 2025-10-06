from openai import OpenAI
from src.settings import settings

llm_client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

system_prompt = """You are an expert professor in agricultural science with extensive knowledge of pest management and crop protection. You are grading answers based on accuracy, completeness, and relevance to the reference answer, focusing on key agricultural practices and terminology. Determine if the predicted answer aligns with the reference answer. Respond with exactly one word: CORRECT if fully accurate and complete, INCORRECT if missing critical elements or incorrect. For partially correct answers, default to INCORRECT unless all essential steps or concepts match."""

prompt_template = """
Question:
{question}

Reference Answer (ground truth):
{reference_answer}

Predicted Answer:
{response}

Evaluation Instruction: Compare the predicted answer to the reference answer, focusing on essential agricultural steps, accuracy of pest management techniques, and completeness. Respond with exactly one word: CORRECT or INCORRECT.
"""


def correctness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    try:
        user_prompt = prompt_template.format(
            question=inputs["question"],
            reference_answer=reference_outputs["answer"],
            response=outputs["response"],
        )
        response = llm_client.chat.completions.create(
            model="gemini-2.5-pro",  # Strongest model for evaluation,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content
        is_incorrect = "INCORRECT" in content

        return {
            "key": "correctness",
            "score": 0 if is_incorrect else 1,
            "comment": content,
        }
    except Exception as e:
        print(f"Error in correctness_evaluator: {e}")
        return {"key": "correctness", "score": 0, "comment": f"Evaluation error: {e}"}


if __name__ == "__main__":
    print(
        correctness_evaluator(
            {"question": "Benomyl, how use?"},
            {
                "response": "Benomyl is a fungicide used to prevent and control Anthracnose, pink disease outbreaks, and Powdery Mildew in Durian. To control Rust Spot and Algal Spot Disease, spray Benomyl all over the plant, and for leaf blight and anthracnose, spray the entire canopy every 7-10 days."
            },
            {
                "answer": "Benomyl is sprayed over the leaves and canopy every 7-10 days for Leaf blight disease."
            },
        )
    )
