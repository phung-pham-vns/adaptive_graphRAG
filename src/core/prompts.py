from langchain import hub
from langchain_core.prompts import ChatPromptTemplate


question_routing_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert at routing a user question to the most appropriate source:
            
            1. **kg_retrieval**: Use for questions about durian pests and diseases that require domain-specific knowledge (symptoms, treatments, identification, etc.)
            2. **web_search**: Use for questions about durian pests/diseases that need only latest/recent information or updates
            3. **llm_internal**: Use for questions that are NOT related to durian, pests, or diseases (general questions, greetings, other topics)

            Examples:
            
            Question: What are the latest news about durian pest and disease?
            Answer: web_search
            
            Question: The latest way to treat durian pest and disease?
            Answer: web_search

            Question: My young durian leaves are curling and look scorched at the edges—could that be leafhopper damage and what should I do first?
            Answer: kg_retrieval

            Question: There's fine sawdust-like powder on my durian trunk—what borer could it be and what's the first step?
            Answer: kg_retrieval
            
            Question: What is the capital of France?
            Answer: llm_internal
            
            Question: How do I cook pasta?
            Answer: llm_internal
            
            Question: Hello, how are you?
            Answer: llm_internal
            
            Question: Tell me about machine learning
            Answer: llm_internal
            """,
        ),
        (
            "human",
            "{question}",
        ),
    ]
)

retrieval_grading_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a grader assessing relevance of a retrieved document to a user question. If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. It does not need to be stringent. Give a binary score 'yes' or 'no'.""",
        ),
        (
            "human",
            "Retrieved document: \n\n {document} \n\n User question: {question}",
        ),
    ]
)

hallucination_grading_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a grader assessing whether an LLM generation is grounded in a set of facts. Give a binary score 'yes' or 'no'. 'Yes' means the answer is supported by the facts.""",
        ),
        (
            "human",
            "Set of facts: \n\n {documents} \n\n LLM generation: {generation}",
        ),
    ]
)

answer_grading_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a grader assessing whether an answer resolves a question. Give a binary score 'yes' or 'no'. 'Yes' means the answer resolves the question.",
        ),
        (
            "human",
            "User question: \n\n {question} \n\n LLM generation: {generation}",
        ),
    ]
)

question_rewriting_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a question re-writer that optimizes an input question for knowledge graph retrieval. Reason about the underlying semantic intent/meaning.""",
        ),
        (
            "human",
            "Initial question: \n\n {question} \n Formulate an improved question.",
        ),
    ]
)

answer_generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.""",
        ),
        (
            "human",
            "Question: {question}\nContext: {context}\nAnswer:",
        ),
    ]
)

llm_internal_answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI assistant. Answer the user's question using your internal knowledge. Be concise, accurate, and helpful. If the question is a greeting, respond politely. If you don't know the answer, say so honestly.""",
        ),
        (
            "human",
            "Question: {question}\nAnswer:",
        ),
    ]
)
