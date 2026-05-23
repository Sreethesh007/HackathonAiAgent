"""
src.memory
----------
Knowledge base access layer for the healthcare triage agent.

Main export:
    KnowledgeRetriever — ChromaDB-backed semantic retriever with sentence-transformers embeddings.
"""

from src.memory.retriever import KnowledgeRetriever

__all__ = ["KnowledgeRetriever"]
