"""
KnowledgeRetriever
------------------
Wraps the persisted ChromaDB vector store and exposes a LangChain-compatible
similarity_search() interface, so ResearchAgent can call it without any changes.

Embedding backend (configured via settings.embedding_provider):
  - "sentence_transformers" → all-MiniLM-L6-v2, runs fully offline, 22 MB model
  - "openai"                → text-embedding-3-small (requires OPENAI_API_KEY)

Usage:
    from src.memory.retriever import KnowledgeRetriever
    retriever = KnowledgeRetriever()
    docs = retriever.similarity_search("chest pain and shortness of breath", k=5)
"""

from __future__ import annotations

from typing import Any

from langchain_core.documents import Document

from src.config import settings
from src.observability.logging import get_logger

log = get_logger(__name__)


def _build_embedding_function():
    """
    Build a ChromaDB-compatible embedding function driven by settings.embedding_provider.
    Falls back to sentence-transformers if OpenAI is configured but unavailable.
    """
    provider = settings.embedding_provider.lower()

    if provider == "openai":
        try:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            if not settings.anthropic_api_key:
                # No OpenAI key either — fall through to local
                raise ValueError("No OpenAI API key configured")
            log.info("embedding_fn_init", provider="openai", model=settings.embedding_model)
            return OpenAIEmbeddingFunction(
                api_key=getattr(settings, "openai_api_key", ""),
                model_name=settings.embedding_model,
            )
        except Exception as exc:
            log.warning(
                "embedding_openai_fallback",
                error=str(exc),
                fallback="sentence_transformers",
            )

    # Default / fallback: sentence-transformers (local, free, offline)
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        log.info("embedding_fn_init", provider="sentence_transformers", model=settings.embedding_model)
        return SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is not installed. "
            "Run: pip install sentence-transformers"
        ) from exc


class KnowledgeRetriever:
    """
    ChromaDB-backed knowledge retriever with real semantic embeddings.

    Drop-in replacement for any LangChain vector store — ResearchAgent calls
    similarity_search(query, k) and receives a list of LangChain Documents.

    The underlying ChromaDB collection is created by scripts/seed_knowledge.py.
    Run that script once before starting the API.
    """

    def __init__(self) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("chromadb is not installed. Run: pip install chromadb") from exc

        settings.ensure_dirs()
        persist_dir = str(settings.chroma_persist_dir)

        log.info(
            "knowledge_retriever_init",
            persist_dir=persist_dir,
            collection=settings.chroma_collection_name,
            embedding_model=settings.embedding_model,
        )

        self._ef = _build_embedding_function()
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )

        count = self._collection.count()
        log.info("knowledge_retriever_ready", document_count=count)
        if count == 0:
            log.warning(
                "knowledge_base_empty",
                hint="Run: python scripts/seed_knowledge.py",
            )

    # ── Public interface (LangChain-compatible) ──────────────────────────────

    def similarity_search(self, query: str, k: int | None = None) -> list[Document]:
        """
        Search for the k most semantically similar documents to query.

        Args:
            query: Natural-language search query
            k:     Number of results to return (defaults to settings.chroma_n_results)

        Returns:
            List of LangChain Document objects with page_content and metadata.
            Returns [] gracefully if the collection is empty or ChromaDB errors.
        """
        n = k if k is not None else settings.chroma_n_results
        count = self._collection.count()
        if count == 0:
            log.warning("similarity_search_empty_collection", query=query[:80])
            return []

        # ChromaDB requires n_results <= document count
        n_results = min(n, count)

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            log.error("similarity_search_failed", error=str(exc), query=query[:80])
            return []

        docs: list[Document] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for content, meta, dist in zip(documents, metadatas, distances):
            # Cosine distance → similarity score (1.0 = identical)
            similarity = round(1.0 - dist, 4)
            enriched_meta = {**(meta or {}), "similarity_score": similarity}
            docs.append(Document(page_content=content, metadata=enriched_meta))

        log.debug(
            "similarity_search_done",
            query=query[:80],
            n_results=len(docs),
            top_score=docs[0].metadata.get("similarity_score") if docs else None,
        )
        return docs

    # ── Utility ──────────────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        """
        Return a health summary — used by the /health/knowledge API endpoint.
        """
        try:
            count = self._collection.count()
            # Quick sanity query
            if count > 0:
                test = self._collection.query(
                    query_texts=["emergency chest pain"],
                    n_results=1,
                    include=["metadatas"],
                )
                top = test["metadatas"][0][0] if test["metadatas"] else {}
            else:
                top = {}

            return {
                "status": "ok" if count > 0 else "empty",
                "document_count": count,
                "collection": settings.chroma_collection_name,
                "embedding_model": settings.embedding_model,
                "embedding_provider": settings.embedding_provider,
                "top_result_title": top.get("title", "n/a"),
            }
        except Exception as exc:
            log.error("knowledge_health_check_failed", error=str(exc))
            return {
                "status": "error",
                "error": str(exc),
                "document_count": 0,
            }
