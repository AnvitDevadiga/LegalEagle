"""
Retriever — singleton ChromaDB + Ollama embeddings.

Lazy-initialised so importing this module is cheap; the heavy
embedding client only spins up the first time `get_retriever()`
is called.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

DB_DIR = "legal_db"
EMBED_MODEL = "nomic-embed-text"

# Retrieval tuning
TOP_K = 5
FETCH_K = 20          # for MMR diversity
MMR_LAMBDA = 0.5      # 0 = max diversity, 1 = max similarity


@lru_cache(maxsize=1)
def _embedding() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=EMBED_MODEL)


@lru_cache(maxsize=1)
def _vectorstore() -> Chroma:
    return Chroma(persist_directory=DB_DIR, embedding_function=_embedding())


@lru_cache(maxsize=1)
def get_retriever():
    """MMR retriever — better coverage across multiple sections/acts."""
    return _vectorstore().as_retriever(
        search_type="mmr",
        search_kwargs={"k": TOP_K, "fetch_k": FETCH_K, "lambda_mult": MMR_LAMBDA},
    )


def collection_size() -> int | None:
    """Best-effort chunk count for the banner. Returns None if unavailable."""
    try:
        return _vectorstore()._collection.count()  # type: ignore[attr-defined]
    except Exception:
        return None


# Backwards-compatible top-level binding (existing imports kept working)
retriever = None  # populated on first access via __getattr__


def __getattr__(name):
    if name == "retriever":
        return get_retriever()
    raise AttributeError(name)
