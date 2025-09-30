"""Constants used throughout the adaptive RAG system."""

from typing import Literal


# Binary score constants
class BinaryScore:
    """Binary score values for grading."""

    YES = "yes"
    NO = "no"


# Route decision constants
class RouteDecision:
    """Route decision values for workflow."""

    WEB_SEARCH = "web_search"
    KG_RETRIEVAL = "kg_retrieval"
    QUERY_TRANSFORMATION = "query_transformation"
    ANSWER_GENERATION = "answer_generation"
    USEFUL = "useful"
    NOT_USEFUL = "not_useful"
    NOT_SUPPORTED = "not_supported"


# Log messages
class LogMessages:
    """Standardized log messages."""

    ROUTE_QUESTION = "---ROUTE QUESTION---"
    ROUTE_TO = "---ROUTE QUESTION TO {}---"
    WEB_SEARCH = "---WEB SEARCH---"
    KNOWLEDGE_GRAPH_RETRIEVAL = "---KNOWLEDGE GRAPH RETRIEVAL---"
    ANSWER_GENERATION = "---ANSWER GENERATION---"
    CHECK_DOCUMENT_RELEVANCE = "---CHECK DOCUMENT RELEVANCE TO QUESTION---"
    QUERY_TRANSFORMATION = "---QUERY TRANSFORMATION---"
    ASSESS_GRADED_DOCUMENTS = "---ASSESS GRADED DOCUMENTS---"
    CHECK_HALLUCINATIONS = "---CHECK HALLUCINATIONS---"
    GRADE_RELEVANT = "---GRADE: {} CONTENT RELEVANT---"
    GRADE_NOT_RELEVANT = "---GRADE: {} CONTENT NOT RELEVANT---"
    ERROR_GRADING = "---ERROR GRADING {} CONTENT: {}---"
    ERROR_IN = "---ERROR IN {}: {}---"
    DECISION_ALL_DOCUMENTS_NOT_RELEVANT = (
        "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT, TRANSFORM QUERY---"
    )
    DECISION_GENERATE = "---DECISION: GENERATE---"
    DECISION_GROUNDED = "---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---"
    DECISION_NOT_GROUNDED = (
        "---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---"
    )
    DECISION_ADDRESSES_QUESTION = "---DECISION: GENERATION ADDRESSES QUESTION---"
    DECISION_NOT_ADDRESSES_QUESTION = (
        "---DECISION: GENERATION DOES NOT ADDRESS QUESTION---"
    )
    MAX_RETRIES_REACHED = "---MAX RETRIES REACHED: {}/{}. FALLING BACK TO {}---"
    RETRY_COUNT_INFO = "---RETRY COUNT: {}/{}---"


# Default configuration values
class Defaults:
    """Default configuration values."""

    N_DOCUMENTS = 3
    N_REQUESTS = 3
    MAX_COROUTINES = 1
    MAX_RETRY_COUNT = 3  # Maximum number of query transformation retries

    # Workflow optimization flags
    ENABLE_DOCUMENT_GRADING = True  # Enable nodes and edges grading
    ENABLE_GENERATION_GRADING = True  # Enable hallucination and answer quality checking
