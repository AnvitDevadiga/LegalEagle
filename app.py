"""
Legal Eagle — offline RAG legal assistant.

Claude Code-style terminal:
  · color-coded role tags
  · streaming markdown rendering with syntax-highlighted code blocks
  · live spinner during retrieval/generation
  · slash commands (/help, /clear, /sources, /exit)

Everything runs locally via Ollama. No telemetry, no network calls.
"""
from __future__ import annotations

import sys
import time
from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_ollama import ChatOllama

import ui
from retriever import get_retriever, collection_size

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
LLM_MODEL = "llama3"
TEMPERATURE = 0.1

RESPONSE_DISCLAIMER = (
    "Disclaimer: This is an AI-generated summary. "
    "Please verify with official legal sources or a licensed practitioner."
)

PROMPT = ChatPromptTemplate.from_template("""\
You are Legal Eagle, an AI legal assistant for Indian law.

RULES:
- Answer ONLY using the provided legal context.
- Clearly mention the Act and the Article/Section.
- Do NOT mention document IDs or metadata.
- If information is missing, say:
  "The provided legal documents do not contain this information."
- Format the answer as concise Markdown.
  Use **bold** for the Act/Section heading and bullet points for clauses.

Legal Context:
{context}

Question:
{question}

Answer:
""")


# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _llm() -> ChatOllama:
    return ChatOllama(model=LLM_MODEL, temperature=TEMPERATURE)


def _format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)


@lru_cache(maxsize=1)
def _chain():
    """
    LCEL pipeline. RunnableParallel lets retrieval and the
    question-passthrough run concurrently before the prompt is built.
    """
    retrieve = get_retriever() | RunnableLambda(_format_docs)
    return (
        RunnableParallel(context=retrieve, question=RunnablePassthrough())
        | PROMPT
        | _llm()
        | StrOutputParser()
    )


@lru_cache(maxsize=1)
def _sources_chain():
    """Mirror of _chain that also keeps the raw retrieved docs for citation."""
    retriever = get_retriever()

    def _pack(q: str):
        docs = retriever.invoke(q)
        return {"docs": docs, "context": _format_docs(docs), "question": q}

    return RunnableLambda(_pack)


# ---------------------------------------------------------------------------
# Conversational shortcuts (skip RAG for simple chat)
# ---------------------------------------------------------------------------
_CONVERSATIONAL: dict[str, str] = {
    "hi": "Hello! How can I assist you with legal information today?",
    "hello": "Hello! How can I assist you with legal information today?",
    "hey": "Hello! How can I assist you with legal information today?",
    "thanks": "You're welcome! Feel free to ask me any legal questions.",
    "thank you": "You're welcome! Feel free to ask me any legal questions.",
    "thankyou": "You're welcome! Feel free to ask me any legal questions.",
}


def _conversational_response(query: str) -> str | None:
    normalized = query.strip().lower().rstrip("!.?,")
    return _CONVERSATIONAL.get(normalized)


# ---------------------------------------------------------------------------
# Safety wrapper (append mandatory block for high-risk inputs)
# ---------------------------------------------------------------------------
_HIGH_RISK_KEYWORDS: tuple[str, ...] = (
    "abuse",
    "suicide",
    "self-harm",
    "self harm",
    "harm",
    "violence",
    "assault",
    "kill",
    "threat",
)

SAFETY_BLOCK = """\
---

**Safety Notice**

If you or someone you know is in immediate danger, contact emergency services (**112** in India) or a local crisis helpline. This assistant provides general legal information only and is not a substitute for professional counseling, medical care, or emergency assistance.

**Helplines (India):**
- Kiran Mental Health: 1800-599-0019
- National Domestic Violence: 181
"""


def _needs_safety_block(query: str) -> bool:
    q = query.lower()
    return any(keyword in q for keyword in _HIGH_RISK_KEYWORDS)


def _append_safety_block(text: str) -> str:
    return f"{text.rstrip()}\n\n{SAFETY_BLOCK}"


def _maybe_append_safety_block(query: str, text: str) -> str:
    if _needs_safety_block(query):
        return _append_safety_block(text)
    return text


def _answer_footer(*meta_parts: str) -> str:
    return "   ·   ".join([*meta_parts, RESPONSE_DISCLAIMER])


def show_disclaimer() -> None:
    """Require acknowledgment before the chat session starts."""
    ui.console.print("-" * 60)
    ui.console.print("LEGAL EAGLE: AI LEGAL ASSISTANT")
    ui.console.print(
        "DISCLAIMER: This tool provides general legal information based on "
        "provided documents. It is NOT a substitute for professional "
        "legal advice. Always consult a qualified attorney for specific "
        "legal issues."
    )
    ui.console.print("-" * 60)
    try:
        input("Press Enter to acknowledge and start...")
    except (EOFError, KeyboardInterrupt):
        ui.console.print()
        ui.goodbye()
        sys.exit(0)
    ui.console.print()


# ---------------------------------------------------------------------------
# Answer flow
# ---------------------------------------------------------------------------
def answer_question(query: str, show_sources: bool) -> None:
    ui.print_user_echo(query)

    greeting = _conversational_response(query)
    if greeting is not None:
        ui.print_assistant(
            _maybe_append_safety_block(query, greeting),
            footer=_answer_footer(),
        )
        return

    needs_safety = _needs_safety_block(query)
    started = time.perf_counter()

    if show_sources:
        with ui.working("retrieving relevant statutes"):
            packed = _sources_chain().invoke(query)

        def token_stream():
            yield from (
                _llm()
                .stream(PROMPT.invoke({"context": packed["context"], "question": query}).to_messages())
            )

        def chunks_to_text():
            for chunk in token_stream():
                # ChatOllama streams AIMessageChunk objects
                yield getattr(chunk, "content", "") or ""
            if needs_safety:
                yield "\n\n" + SAFETY_BLOCK

        def footer_fn(full_text: str) -> str:
            elapsed = time.perf_counter() - started
            srcs = sorted({d.metadata.get("source", "unknown") for d in packed["docs"]})
            return _answer_footer(
                f"sources: {', '.join(srcs)}",
                f"{len(packed['docs'])} chunks",
                f"{elapsed:.1f}s",
            )

        ui.stream_assistant(chunks_to_text(), footer_fn=footer_fn)
    else:
        with ui.working("retrieving relevant statutes"):
            pass  # spinner just for UX symmetry; retrieval runs inside stream
        chain = _chain()

        def chunks_to_text():
            for tok in chain.stream(query):
                yield tok if isinstance(tok, str) else getattr(tok, "content", "") or ""
            if needs_safety:
                yield "\n\n" + SAFETY_BLOCK

        def footer_fn(_full_text: str) -> str:
            elapsed = time.perf_counter() - started
            return _answer_footer(f"answered in {elapsed:.1f}s", "local · llama3")

        ui.stream_assistant(chunks_to_text(), footer_fn=footer_fn)


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------
def repl() -> None:
    show_disclaimer()
    ui.render_banner(model=LLM_MODEL, db_dir="legal_db", doc_count=collection_size())
    show_sources = True

    # Warm the singletons silently so the first user query feels snappy.
    try:
        get_retriever()
        _llm()
    except Exception as e:
        ui.error_msg(f"Failed to initialise local models: {e}")
        ui.hint("Is `ollama serve` running?  Did you `ollama pull llama3 nomic-embed-text`?")
        sys.exit(1)

    while True:
        try:
            raw = ui.read_query().strip()
        except KeyboardInterrupt:
            ui.goodbye()
            return

        if not raw:
            continue

        cmd = raw.lower()
        if cmd in ("/exit", "exit", "quit", ":q"):
            ui.goodbye()
            return
        if cmd in ("/help", "help", "?"):
            ui.print_help()
            continue
        if cmd in ("/clear", "clear"):
            ui.clear_screen()
            ui.render_banner(model=LLM_MODEL, db_dir="legal_db", doc_count=collection_size())
            continue
        if cmd == "/sources":
            show_sources = not show_sources
            ui.ok_msg(f"source citations: {'on' if show_sources else 'off'}")
            continue
        if raw.startswith("/"):
            ui.error_msg(f"unknown command: {raw}")
            ui.hint("type /help for the list")
            continue

        try:
            answer_question(raw, show_sources)
        except KeyboardInterrupt:
            ui.system_msg("interrupted")
        except Exception as e:
            ui.error_msg(str(e))


if __name__ == "__main__":
    repl()
