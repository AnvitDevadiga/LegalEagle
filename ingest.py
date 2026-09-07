"""
Ingest legal PDFs into the local Chroma vector store.

Optimisations vs. the original:
  · concurrent PDF loading (ThreadPoolExecutor) — big speedup on multi-PDF runs
  · batched insertion into Chroma — avoids one giant call that can OOM
  · rich progress bars for visibility
  · idempotent: re-running on an existing DB no-ops unless --rebuild
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DB_DIR = APP_DIR / "legal_db"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
BATCH_SIZE = 64

console = Console(highlight=False)


def _load_pdf(path: str, filename: str):
    docs = PyPDFLoader(path).load()
    for d in docs:
        d.metadata["source"] = filename
    return docs


def load_all_pdfs(data_dir: str | Path) -> list:
    pdfs = sorted(f for f in os.listdir(data_dir) if f.lower().endswith(".pdf"))
    if not pdfs:
        console.print(f"[red]No PDFs found in {data_dir}/[/]")
        sys.exit(1)

    docs: list = []
    with Progress(
        SpinnerColumn(style="#d4a657"),
        TextColumn("[bold]loading PDFs[/]"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as bar:
        task = bar.add_task("load", total=len(pdfs))
        with ThreadPoolExecutor(max_workers=min(4, len(pdfs))) as pool:
            futures = {
                pool.submit(_load_pdf, os.path.join(data_dir, f), f): f for f in pdfs
            }
            for fut in as_completed(futures):
                docs.extend(fut.result())
                bar.advance(task)
    return docs


def chunk_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(docs)


def embed_and_store(chunks, db_dir: str | Path):
    embedding = OllamaEmbeddings(model=EMBED_MODEL)
    db = Chroma(persist_directory=str(db_dir), embedding_function=embedding)

    with Progress(
        SpinnerColumn(style="#d4a657"),
        TextColumn("[bold]embedding chunks[/]"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as bar:
        task = bar.add_task("embed", total=len(chunks))
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            db.add_documents(batch)
            bar.advance(task, len(batch))


def vector_store_present(db_dir: str | Path | None = None) -> bool:
    """Return whether a bundled or previously built Chroma store is present."""
    database_file = Path(db_dir or DB_DIR) / "chroma.sqlite3"
    return database_file.is_file() and database_file.stat().st_size > 0


def build_vector_store(*, rebuild: bool = False) -> int:
    """Build the local index and return its passage count.

    This callable entry point lets the Streamlit app repair a missing index on
    first launch without asking the user to run a separate setup command.
    """
    if rebuild and DB_DIR.is_dir():
        console.print(f"[yellow]Removing existing vector store at {DB_DIR}/[/]")
        shutil.rmtree(DB_DIR)

    if vector_store_present():
        console.print(
            f"[green]Vector store already present at {DB_DIR}/.[/] "
            f"Use [bold]--rebuild[/] to reindex."
        )
        return 0

    docs = load_all_pdfs(DATA_DIR)
    console.print(
        f"[dim]loaded {len(docs)} pages across "
        f"{len({d.metadata['source'] for d in docs})} documents[/]"
    )

    chunks = chunk_documents(docs)
    console.print(
        f"[dim]split into {len(chunks)} chunks "
        f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})[/]"
    )
    staging_dir = DB_DIR.with_name(f"{DB_DIR.name}.building")
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    try:
        embed_and_store(chunks, staging_dir)
        if DB_DIR.exists():
            shutil.rmtree(DB_DIR)
        staging_dir.rename(DB_DIR)
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise
    console.print(f"\n[bold #87d787]✓ indexed {len(chunks)} chunks into {DB_DIR}/[/]")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description="Build the Legal Eagle vector store.")
    parser.add_argument("--rebuild", action="store_true",
                        help="Delete the existing DB before ingesting.")
    args = parser.parse_args()

    build_vector_store(rebuild=args.rebuild)


if __name__ == "__main__":
    main()
