"""
Retriever — singleton ChromaDB + Ollama embeddings.

Lazy-initialised so importing this module is cheap; the heavy
embedding client only spins up the first time `get_retriever()`
is called.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

APP_DIR = Path(__file__).resolve().parent
DB_DIR = APP_DIR / "legal_db"
EMBED_MODEL = "nomic-embed-text"

# Retrieval tuning: four focused passages keep prompts responsive while still
# providing enough context to cross-check nearby provisions.
TOP_K = 4


@lru_cache(maxsize=1)
def _embedding() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=EMBED_MODEL)


@lru_cache(maxsize=1)
def _vectorstore() -> Chroma:
    return Chroma(persist_directory=str(DB_DIR), embedding_function=_embedding())


@lru_cache(maxsize=1)
def get_retriever():
    """Fast similarity retriever for the local legal collection."""
    return _vectorstore().as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )


def _exact_reference_documents(query: str) -> list[Document]:
    """Find cited Articles/Sections lexically so embeddings cannot miss them."""
    lowered = query.lower()
    references: list[tuple[str, str, list[str]]] = []

    for number in re.findall(r"\barticles?\s+(\d+[a-z]?)\b", lowered):
        references.append(("article", number, ["constitution.pdf"]))

    section_sources: list[str]
    if "bns" in lowered or "bharatiya nyaya sanhita" in lowered:
        section_sources = ["bns.pdf"]
    elif "ipc" in lowered or "indian penal code" in lowered:
        section_sources = ["ipc.pdf"]
    else:
        section_sources = ["bns.pdf", "ipc.pdf"]
    for number in re.findall(r"\bsections?\s+(\d+[a-z]?)\b", lowered):
        references.append(("section", number, section_sources))

    documents: list[Document] = []
    collection = _vectorstore()._collection  # type: ignore[attr-defined]
    for kind, number, sources in references:
        candidates: list[tuple[int, int, Document]] = []
        marker = re.compile(rf"(?<!\d){re.escape(number)}\.\s*", re.IGNORECASE)
        for source in sources:
            result = collection.get(
                where={"source": source},
                where_document={"$contains": f"{number}."},
                include=["documents", "metadatas"],
                limit=100,
            )
            for content, metadata in zip(result.get("documents", []), result.get("metadatas", [])):
                match = marker.search(content)
                if not match:
                    continue
                after_marker = content[match.end():]
                # Operative provisions tend to include a dash and complete prose;
                # table-of-contents hits are useful fallbacks but rank lower.
                score = 0
                if "—" in after_marker[:180] or ".—" in after_marker[:180]:
                    score += 4
                if len(after_marker) > 220:
                    score += 2
                page_number = int((metadata or {}).get("page", 10**9))
                candidates.append((score, page_number, Document(page_content=content, metadata=metadata or {})))
        candidates.sort(key=lambda item: (-item[0], item[1]))
        documents.extend(document for _, _, document in candidates[:1])
    return documents


def retrieve_documents(query: str) -> list[Document]:
    """Hybrid retrieval: exact legal references first, then semantic context."""
    exact = _exact_reference_documents(query)
    semantic = get_retriever().invoke(query)
    combined: list[Document] = []
    seen: set[tuple[str, object, str]] = set()
    for document in [*exact, *semantic]:
        key = (
            str(document.metadata.get("source", "")),
            document.metadata.get("page"),
            document.page_content[:120],
        )
        if key not in seen:
            seen.add(key)
            combined.append(document)
    return combined[:5]


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
