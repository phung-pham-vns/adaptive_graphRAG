from typing import Literal
from pydantic import BaseModel, Field
from src.core.tools import Tools


class RouteQuery(BaseModel):
    """Route a user query to the most relevant data_source."""

    data_source: Literal[
        Tools.KG_RETRIEVAL.value, Tools.WEB_SEARCH.value, Tools.LLM_INTERNAL.value, Tools.VLM_INTERNAL.value
    ] = Field(
        description="Route to knowledge graph retrieval for durian pest/disease domain questions, web search for latest pest/disease information, LLM internal knowledge for out-of-domain questions, or VLM internal for image-based questions."
    )


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(description="Documents are relevant: 'yes' or 'no'")


class GradeHallucinations(BaseModel):
    """Binary score for hallucination check in generation."""

    binary_score: str = Field(description="Answer is grounded: 'yes' or 'no'")


class GenerateAnswer(BaseModel):
    """Generate an answer to a question and given context."""

    answer: str = Field(description="Answer to the question and the given context")


class GradeAnswer(BaseModel):
    """Binary score to assess if answer addresses question."""

    binary_score: str = Field(description="Answer addresses question: 'yes' or 'no'")


class QueryRefinement(BaseModel):
    """Refined question for knowledge graph retrieval."""

    refined_question: str = Field(description="Optimized question for retrieval")
