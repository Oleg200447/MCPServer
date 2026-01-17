# from app import mcp
from fastmcp import FastMCP


def setup_promts(server:FastMCP):

    @server.prompt
    def refine_query(query: str) -> str:
        """
        Prompt for refining a user query with awareness of effective retrieval query types
        """
        return f"""
    You are an expert in information retrieval over internal corporate documents.

    User query:
    {query}

    Rewrite the user query to be optimal for document search.

    Important context:
    Our search system has been trained using several types of search queries:
    1. Short keyword-style queries (1–3 words)
    2. Natural long phrase queries (4–7 words)
    3. Question-style queries (wh- format, e.g., "What...", "How...", "Why...")
    4. Alternative keyword-style queries
    5. Alternative natural phrase queries

    Among these, natural long phrase queries (4–7 words) often perform especially well.

    Guidelines:
    - Preserve the original intent of the user query
    - Prefer formulations similar to effective training queries
    - Choose the formulation that best fits the user intent and search quality
    - Do not include explanations or multiple variants

    Return a single refined search query.
    """

    @server.prompt
    def extract_query_facts(text: str, query: str) -> str:
        """
        Prompt for extracting query-related facts from a document
        """
        return f"""
    You are an expert at extracting factual information from documents.

    Query:
    {query}

    Document:
    {text}

    Extract ONLY information that directly helps answer the query.
    Rules:
    - Do not summarize the whole document
    - Do not add interpretation
    - Preserve names, dates, numbers, decisions, responsibilities
    - If nothing is relevant, respond with: "No relevant information"

    Return the extracted facts as bullet points.
    """

    @server.prompt
    def validate_relevance(extracted: str, query: str) -> str:
        """
        Prompt for validating relevance of extracted content
        """
        return f"""
    You are evaluating relevance to a query.

    Query:
    {query}

    Extracted information:
    {extracted}

    Is this information useful for answering the query?
    Respond with:
    - Relevant
    - Weakly relevant
    - Not relevant

    Briefly justify your decision.
    """

    @server.prompt
    def synthesize_information(extractions: list[str], query: str) -> str:
        """
        Prompt for synthesizing information from multiple documents
        """
        joined = "\n\n---\n\n".join(extractions)

        return f"""
    You are a senior research analyst.

    Query:
    {query}

    Below are extracted facts from multiple internal documents:
    {joined}

    Synthesize this information into a coherent structured summary.
    Rules:
    - Eliminate duplication
    - Preserve important differences between sources
    - Do not invent missing information
    - Keep the structure clear and logical
    """

    @server.prompt
    def detect_issues(synthesis: str, query: str) -> str:
        """
        Prompt for detecting contradictions and gaps
        """
        return f"""
    You are reviewing synthesized research results.

    Query:
    {query}

    Synthesis:
    {synthesis}

    Identify:
    - Contradictions between sources
    - Missing or unclear information
    - Areas where documents disagree

    If none are found, state that explicitly.
    """

    @server.prompt
    def generate_answer(context: str, query: str) -> str:
        """
        Prompt for generating final user-facing answer
        """
        return f"""
    You are answering a user question based ONLY on provided internal documents.

    Query:
    {query}

    Context:
    {context}

    Rules:
    - Answer clearly and concisely
    - Do not add information not present in the context
    - If the context is insufficient, say so explicitly

    Provide the final answer.
    """