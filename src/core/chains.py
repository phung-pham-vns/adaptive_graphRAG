"""LLM Chains for Adaptive RAG Workflow.

This module defines the LangChain chains used throughout the adaptive RAG workflow.
Each chain combines a prompt template with an LLM and structured output schema.

Chains are optimized for the durian pest and disease domain with:
- Intelligent routing (KG/Web/LLM Internal)
- Document relevance grading
- Query transformation for better retrieval
- Quality control (hallucination and answer quality checks)
- Domain-specific answer generation

Usage:
    from src.core.chains import question_router, answer_generator
    
    # Route a question
    route = await question_router.ainvoke({"question": "What causes leaf curl?"})
    
    # Generate an answer
    answer = await answer_generator.ainvoke({
        "question": "What causes leaf curl?",
        "context": formatted_context
    })
"""

from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import Runnable

from src.core.prompts import (
    question_routing_prompt,
    retrieval_grading_prompt,
    hallucination_grading_prompt,
    answer_grading_prompt,
    question_rewriting_prompt,
    answer_generation_prompt,
    llm_internal_answer_prompt,
)
from src.core.schema import (
    RouteQuery,
    GradeDocuments,
    GradeHallucinations,
    GradeAnswer,
    QueryRefinement,
    GenerateAnswer,
)
from src.settings import settings


# ============================================================================
# LLM Configuration
# ============================================================================

def create_llm(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
) -> ChatGoogleGenerativeAI:
    """Create a configured LLM instance.
    
    This function provides centralized LLM configuration with optional overrides
    for specific use cases (e.g., lower temperature for grading, higher for generation).
    
    Args:
        temperature: Override default temperature (0.0 = deterministic, 1.0 = creative)
        max_tokens: Override default max tokens
        model: Override default model
        
    Returns:
        Configured ChatGoogleGenerativeAI instance
        
    Example:
        # Default LLM for general use
        llm = create_llm()
        
        # More creative LLM for answer generation
        creative_llm = create_llm(temperature=0.3)
        
        # Deterministic LLM for grading
        grading_llm = create_llm(temperature=0.0)
    """
    return ChatGoogleGenerativeAI(
        model=model or settings.llm.llm_model,
        temperature=temperature if temperature is not None else settings.llm.llm_temperature,
        max_tokens=max_tokens or settings.llm.llm_max_tokens,
        google_api_key=settings.llm.llm_api_key,
    )


# Primary LLM instance for all chains (temperature=0.0 for consistency)
llm = create_llm()

# Alternative: Creative LLM for answer generation (uncomment to use)
# creative_llm = create_llm(temperature=0.3)


# ============================================================================
# Routing Chain
# ============================================================================

question_router: Runnable[dict, RouteQuery] = (
    question_routing_prompt | llm.with_structured_output(RouteQuery)
)
"""Route questions to appropriate data source (KG/Web/LLM Internal).

Input: {"question": str}
Output: RouteQuery with data_source field

Decision Logic:
1. Domain check: Is it about durian pests/diseases?
   - NO → llm_internal
   - YES → Go to step 2
2. Time sensitivity: Does it need latest/recent info?
   - YES → web_search
   - NO → kg_retrieval

Examples:
    >>> route = await question_router.ainvoke({"question": "What causes leaf curl?"})
    >>> route.data_source
    'kg_retrieval'
    
    >>> route = await question_router.ainvoke({"question": "Latest durian disease news?"})
    >>> route.data_source
    'web_search'
    
    >>> route = await question_router.ainvoke({"question": "What is the capital of France?"})
    >>> route.data_source
    'llm_internal'
"""


# ============================================================================
# Document Grading Chain
# ============================================================================

retrieval_grader: Runnable[dict, GradeDocuments] = (
    retrieval_grading_prompt | llm.with_structured_output(GradeDocuments)
)
"""Grade relevance of retrieved documents to the question.

Input: {"question": str, "document": str}
Output: GradeDocuments with binary_score ('yes'/'no')

Grading Criteria:
- 'yes' if document contains relevant information for the question
- 'no' if document is unrelated or not helpful

This chain filters out irrelevant documents before answer generation,
improving answer quality and reducing hallucinations.

Examples:
    >>> grade = await retrieval_grader.ainvoke({
    ...     "question": "What causes durian leaf curl?",
    ...     "document": "Phytoplasma pathogens cause leaf curl disease in durian..."
    ... })
    >>> grade.binary_score
    'yes'
    
    >>> grade = await retrieval_grader.ainvoke({
    ...     "question": "What causes durian leaf curl?",
    ...     "document": "Information about durian fruit harvesting techniques..."
    ... })
    >>> grade.binary_score
    'no'
"""


# ============================================================================
# Hallucination Check Chain
# ============================================================================

hallucination_grader: Runnable[dict, GradeHallucinations] = (
    hallucination_grading_prompt | llm.with_structured_output(GradeHallucinations)
)
"""Check if generated answer is grounded in provided context.

Input: {"documents": str, "generation": str}
Output: GradeHallucinations with binary_score ('yes'/'no')

Purpose:
- Verify that answer claims are supported by the context
- Prevent hallucinations and fabricated information
- Ensure factual accuracy

This chain is optional but recommended for high-stakes applications.

Examples:
    >>> score = await hallucination_grader.ainvoke({
    ...     "documents": "Stem borers attack durian trunks causing damage...",
    ...     "generation": "Stem borers damage durian trunks and should be treated with pesticides."
    ... })
    >>> score.binary_score
    'yes'  # Answer is grounded in context
    
    >>> score = await hallucination_grader.ainvoke({
    ...     "documents": "Stem borers attack durian trunks...",
    ...     "generation": "Leaf curl is caused by viral infections in durian."
    ... })
    >>> score.binary_score
    'no'  # Answer claims not supported by context
"""


# ============================================================================
# Answer Quality Check Chain
# ============================================================================

answer_grader: Runnable[dict, GradeAnswer] = (
    answer_grading_prompt | llm.with_structured_output(GradeAnswer)
)
"""Check if generated answer addresses the question.

Input: {"question": str, "generation": str}
Output: GradeAnswer with binary_score ('yes'/'no')

Purpose:
- Verify answer actually resolves the question
- Detect incomplete or off-topic answers
- Trigger query transformation if answer is insufficient

This chain is optional but improves answer quality by retrying with
refined queries when answers don't address the question.

Examples:
    >>> score = await answer_grader.ainvoke({
    ...     "question": "What causes durian leaf curl?",
    ...     "generation": "Phytoplasma pathogens cause durian leaf curl disease..."
    ... })
    >>> score.binary_score
    'yes'  # Answer addresses the question
    
    >>> score = await answer_grader.ainvoke({
    ...     "question": "What causes durian leaf curl?",
    ...     "generation": "There are many durian diseases affecting trees..."
    ... })
    >>> score.binary_score
    'no'  # Answer is too generic, doesn't address specific question
"""


# ============================================================================
# Query Transformation Chain
# ============================================================================

question_rewriter: Runnable[dict, QueryRefinement] = (
    question_rewriting_prompt | llm.with_structured_output(QueryRefinement)
)
"""Transform queries for better knowledge graph retrieval.

Input: {"question": str}
Output: QueryRefinement with refined_question field

Optimization Strategies:
1. Expand with scientific names and synonyms
2. Add domain context ("durian")
3. Extract key entities (pest/disease names)
4. Use KG-friendly terminology
5. Focus on retrieval-optimized phrasing

This chain improves retrieval results when initial queries are too vague
or don't match knowledge graph entities well.

Examples:
    >>> refined = await question_rewriter.ainvoke({
    ...     "question": "leaf curl"
    ... })
    >>> refined.refined_question
    'durian leaf curl disease symptoms Phytoplasma causes'
    
    >>> refined = await question_rewriter.ainvoke({
    ...     "question": "Why are my leaves dying?"
    ... })
    >>> refined.refined_question
    'durian leaf death causes symptoms disease pest damage'
"""


# ============================================================================
# Answer Generation Chains
# ============================================================================

answer_generator: Runnable[dict, GenerateAnswer] = (
    answer_generation_prompt | llm.with_structured_output(GenerateAnswer)
)
"""Generate answer from context (for domain queries with retrieved context).

Input: {"question": str, "context": str}
Output: GenerateAnswer with answer field

This chain generates answers for durian pest/disease questions using
context retrieved from the knowledge graph or web search.

Answer Characteristics:
- Based on provided context (entities, relationships, web info)
- Domain-specific and actionable
- Concise but comprehensive (3-5 sentences)
- Cites context when possible
- Admits uncertainty when context is insufficient

Examples:
    >>> answer = await answer_generator.ainvoke({
    ...     "question": "What causes durian leaf curl?",
    ...     "context": "Entity 1: Phytoplasma pathogens cause leaf curl..."
    ... })
    >>> answer.answer
    'Durian leaf curl is primarily caused by Phytoplasma pathogens...'
"""

llm_internal_answer_generator: Runnable[dict, GenerateAnswer] = (
    llm_internal_answer_prompt | llm.with_structured_output(GenerateAnswer)
)
"""Generate answer using LLM internal knowledge (for out-of-domain queries).

Input: {"question": str}
Output: GenerateAnswer with answer field

This chain handles out-of-domain questions that are not related to
durian pests/diseases (greetings, general knowledge, etc.).

Answer Characteristics:
- Uses LLM's internal knowledge (no external context)
- Concise (2-3 sentences for simple questions)
- Acknowledges domain boundaries when appropriate
- Friendly for greetings and casual conversation

Examples:
    >>> answer = await llm_internal_answer_generator.ainvoke({
    ...     "question": "Hello, how are you?"
    ... })
    >>> answer.answer
    'Hello! I'm here to help you with durian pest and disease questions...'
    
    >>> answer = await llm_internal_answer_generator.ainvoke({
    ...     "question": "What is the capital of France?"
    ... })
    >>> answer.answer
    'The capital of France is Paris.'
"""


# ============================================================================
# Chain Factory Functions (Advanced Usage)
# ============================================================================

def create_custom_chain(
    prompt,
    output_schema,
    temperature: Optional[float] = None,
) -> Runnable:
    """Create a custom chain with specified configuration.
    
    This factory function allows creating chains with custom configurations
    for specific use cases or experiments.
    
    Args:
        prompt: LangChain prompt template
        output_schema: Pydantic model for structured output
        temperature: LLM temperature override
        
    Returns:
        Configured chain
        
    Example:
        >>> from src.core.prompts import answer_generation_prompt
        >>> from src.core.schema import GenerateAnswer
        >>> 
        >>> # Create more creative answer generator
        >>> creative_generator = create_custom_chain(
        ...     answer_generation_prompt,
        ...     GenerateAnswer,
        ...     temperature=0.7
        ... )
    """
    custom_llm = create_llm(temperature=temperature)
    return prompt | custom_llm.with_structured_output(output_schema)


# ============================================================================
# Chain Registry (for introspection and testing)
# ============================================================================

CHAIN_REGISTRY = {
    "question_router": {
        "chain": question_router,
        "description": "Route questions to KG/Web/LLM Internal",
        "input": {"question": "str"},
        "output": "RouteQuery",
        "use_case": "Intelligent routing based on question type",
    },
    "retrieval_grader": {
        "chain": retrieval_grader,
        "description": "Grade document relevance to question",
        "input": {"question": "str", "document": "str"},
        "output": "GradeDocuments",
        "use_case": "Filter irrelevant documents before answer generation",
    },
    "hallucination_grader": {
        "chain": hallucination_grader,
        "description": "Check if answer is grounded in context",
        "input": {"documents": "str", "generation": "str"},
        "output": "GradeHallucinations",
        "use_case": "Verify answer factuality and prevent hallucinations",
    },
    "answer_grader": {
        "chain": answer_grader,
        "description": "Check if answer addresses the question",
        "input": {"question": "str", "generation": "str"},
        "output": "GradeAnswer",
        "use_case": "Verify answer quality and trigger retries if needed",
    },
    "question_rewriter": {
        "chain": question_rewriter,
        "description": "Transform query for better KG retrieval",
        "input": {"question": "str"},
        "output": "QueryRefinement",
        "use_case": "Optimize queries for knowledge graph entity/relationship retrieval",
    },
    "answer_generator": {
        "chain": answer_generator,
        "description": "Generate answer from context",
        "input": {"question": "str", "context": "str"},
        "output": "GenerateAnswer",
        "use_case": "Domain-specific answer generation with retrieved context",
    },
    "llm_internal_answer_generator": {
        "chain": llm_internal_answer_generator,
        "description": "Generate answer using internal knowledge",
        "input": {"question": "str"},
        "output": "GenerateAnswer",
        "use_case": "Handle out-of-domain and general knowledge questions",
    },
}
"""Registry of all available chains with metadata.

Useful for:
- Documentation generation
- Testing and validation
- Chain introspection
- Dynamic chain selection
"""


def get_chain_info(chain_name: str) -> dict:
    """Get information about a specific chain.
    
    Args:
        chain_name: Name of the chain (e.g., 'question_router')
        
    Returns:
        Dictionary with chain metadata
        
    Example:
        >>> info = get_chain_info("question_router")
        >>> print(info["description"])
        'Route questions to KG/Web/LLM Internal'
    """
    if chain_name not in CHAIN_REGISTRY:
        raise ValueError(f"Chain '{chain_name}' not found. Available: {list(CHAIN_REGISTRY.keys())}")
    return CHAIN_REGISTRY[chain_name]


def list_chains() -> list[str]:
    """List all available chain names.
    
    Returns:
        List of chain names
        
    Example:
        >>> chains = list_chains()
        >>> print(chains)
        ['question_router', 'retrieval_grader', 'hallucination_grader', ...]
    """
    return list(CHAIN_REGISTRY.keys())


# ============================================================================
# Chain Testing Utilities
# ============================================================================

async def test_chain(chain_name: str, test_input: dict) -> dict:
    """Test a chain with sample input.
    
    Useful for debugging and validation.
    
    Args:
        chain_name: Name of the chain to test
        test_input: Input dictionary matching chain's expected input
        
    Returns:
        Chain output
        
    Example:
        >>> result = await test_chain(
        ...     "question_router",
        ...     {"question": "What causes durian leaf curl?"}
        ... )
        >>> print(result.data_source)
        'kg_retrieval'
    """
    chain_info = get_chain_info(chain_name)
    chain = chain_info["chain"]
    return await chain.ainvoke(test_input)


# ============================================================================
# Export All Chains and Utilities
# ============================================================================

__all__ = [
    # Primary chains
    "question_router",
    "retrieval_grader",
    "hallucination_grader",
    "answer_grader",
    "question_rewriter",
    "answer_generator",
    "llm_internal_answer_generator",
    # LLM configuration
    "llm",
    "create_llm",
    # Advanced usage
    "create_custom_chain",
    # Introspection
    "CHAIN_REGISTRY",
    "get_chain_info",
    "list_chains",
    "test_chain",
]
