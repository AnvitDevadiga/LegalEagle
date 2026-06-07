<div align="center">

```
 ██╗     ███████╗ ██████╗  █████╗ ██╗      ███████╗ █████╗  ██████╗ ██╗     ███████╗
 ██║     ██╔════╝██╔════╝ ██╔══██╗██║      ██╔════╝██╔══██╗██╔════╝ ██║     ██╔════╝
 ██║     █████╗  ██║  ███╗███████║██║      █████╗  ███████║██║  ███╗██║     █████╗
 ██║     ██╔══╝  ██║   ██║██╔══██║██║      ██╔══╝  ██╔══██║██║   ██║██║     ██╔══╝
 ███████╗███████╗╚██████╔╝██║  ██║███████╗ ███████╗██║  ██║╚██████╔╝███████╗███████╗
 ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝
```

### *Offline AI Legal Assistant for Indian Law*

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=for-the-badge&logo=ollama&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35?style=for-the-badge)
![License](https://img.shields.io/badge/License-Academic-green?style=for-the-badge)

<br/>

> **100% Offline · Zero API Cost · Hallucination-Resistant**
>
> *Ask questions about Indian law. Get grounded, cited answers — entirely from a local model.*

</div>

---

## What is Legal Eagle?

Legal Eagle is an **offline RAG system** that lets you query 620+ pages of Indian legal documents — the Constitution, IPC, and Bharatiya Nyaya Sanhita — using a locally running Llama 3 model. No internet calls, no telemetry, no third-party APIs.

The CLI is built in the spirit of modern coding terminals: role-coded panels, streaming markdown answers, syntax-highlighted code blocks, and a live spinner during retrieval.

---

## Screenshots

**Consumer rights query — live session**

![Consumer Rights Query](screenshots/Screenshot_2026-06-07_at_11_09_04.png)

> A real-time query about laptop motherboard fault and Consumer Forum rights — answered with cited sections from BNS and IPC within seconds.

---

**Workplace harassment query — safety-aware response**

![Workplace Harassment Query](screenshots/Screenshot_2026-06-07_at_11_10_27.png)

> Query about workplace sexual harassment triggers both legal citations (POSH Act 2013, IPC Section 354D) and an automatic Safety Notice with emergency helplines.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         app.py (REPL)                       │
│    slash commands · disclaimer gate · safety filter         │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │      LangChain LCEL     │
          │  RunnableParallel       │
          │  context ──► retriever  │
          │  question ──► passthru  │
          └────────┬────────────────┘
                   │
     ┌─────────────▼──────────────┐
     │        retriever.py        │
     │   ChromaDB  ·  MMR  k=5   │
     │   nomic-embed-text         │
     └─────────────┬──────────────┘
                   │
     ┌─────────────▼──────────────┐
     │   legal_db/  (persisted)   │
     │   constitution.pdf  ~250p  │
     │   ipc.pdf           ~190p  │
     │   bns.pdf           ~183p  │
     └────────────────────────────┘
                   │ context
     ┌─────────────▼──────────────┐
     │   Llama 3  (via Ollama)    │
     │   temp=0.1  ·  streaming   │
     └─────────────┬──────────────┘
                   │ tokens
     ┌─────────────▼──────────────┐
     │         ui.py              │
     │  Rich panels · Markdown    │
     │  live spinner · footer     │
     └────────────────────────────┘
```

---

## Legal Coverage

| Document | Coverage | Pages |
|---|---|---|
| Indian Constitution | All Articles + Amendments | ~250 |
| Indian Penal Code (IPC) | All Sections | ~190 |
| Bharatiya Nyaya Sanhita (BNS) | Full Text | ~183 |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | Llama 3 (via Ollama) | Legal reasoning & answer generation |
| **Embeddings** | `nomic-embed-text` | Legal text vectorization |
| **RAG Framework** | LangChain LCEL | Pipeline orchestration |
| **Vector DB** | ChromaDB (persisted locally) | Semantic retrieval |
| **Terminal UI** | `rich` | Panels, markdown, syntax highlighting |
| **Language** | Python 3.11+ | Core implementation |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running

### 1. Clone & setup

```bash
git clone https://github.com/AnvitDevadiga/legal-eagle.git
cd legal-eagle
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Pull models

```bash
ollama pull llama3
ollama pull nomic-embed-text
ollama serve            # keep this terminal running
```

### 3. Build the knowledge base

```bash
# Place PDFs in data/ folder first
python ingest.py            # one-time index build (~2 min)
python ingest.py --rebuild  # delete & reindex from scratch
```

### 4. Launch

```bash
python app.py
```

---

## Example Session

```
╭───────── Legal Eagle ──────────╮
│   model    llama3 (local)      │
│ vectors    legal_db · 2999     │
│   scope    Constitution · IPC  │
│            Bharatiya Nyaya     │
│            Sanhita             │
│ shortcuts  /help /clear /exit  │
╰────────────────────────────────╯

 YOU  What does Article 21 guarantee?

╭─ LEGAL EAGLE ──────────────────────────────────────────────────╮
│                                                                │
│ **Article 21 — Constitution of India**                        │
│                                                                │
│ Article 21 guarantees the protection of life and personal      │
│ liberty. No person shall be deprived of these rights except    │
│ according to procedure established by law.                     │
│                                                                │
│ sources: constitution.pdf · 3 chunks · 1.4s                   │
│ Disclaimer: This is an AI-generated summary. Please verify    │
│ with official legal sources or a licensed practitioner.        │
╰────────────────────────────────────────────────────────────────╯
```

---

## Slash Commands

| Command | Action |
|---|---|
| `/help` | Show all available commands |
| `/clear` | Clear the screen, redraw banner |
| `/sources` | Toggle source citations on/off |
| `/exit` | Quit Legal Eagle |
| `Ctrl+C` | Interrupt a running answer |

---

## Anti-Hallucination Design

```
✓  Answers strictly limited to retrieved legal context
✓  Explicit refusal when information is not in the documents
✓  MMR retrieval — diversified context, no duplicate chunks
✓  Low-temperature LLM config (temp=0.1) — no creative fabrication
✓  Source citation on every response (PDF · chunk count · latency)
✓  Safety Notice auto-appended for sensitive queries (abuse, harassment, etc.)
```

---

## Key Features

**Streaming responses** — answers render token-by-token; start reading immediately, no waiting for full generation.

**Claude Code-style terminal** — color-coded `YOU` / `LEGAL EAGLE` / `SYS` panels, markdown body, syntax-highlighted code blocks, live spinner.

**MMR retrieval** — diversified context (`k=5`, `fetch_k=20`) so multi-section answers cite different Acts/Articles instead of duplicating the same chunk.

**Singleton LLM + embedding clients** — no per-query re-initialisation; warm-up happens at boot, every subsequent query is hot.

**Idempotent ingest** — re-running `python ingest.py` no-ops unless you pass `--rebuild`; PDF loading is parallelised (ThreadPoolExecutor) and embeddings are batched (64/call).

**Safety-aware** — keywords like `abuse`, `assault`, `self-harm` auto-append Indian emergency helplines (112 · Kiran 1800-599-0019 · NCW 181) to every answer.

---

## Project Structure

```
legal-eagle/
│
├── data/
│   ├── constitution.pdf      # Indian Constitution
│   ├── ipc.pdf               # Indian Penal Code
│   └── bns.pdf               # Bharatiya Nyaya Sanhita
│
├── screenshots/
│   ├── Screenshot_2026-06-07_at_11_09_04.png
│   └── Screenshot_2026-06-07_at_11_10_27.png
│
├── ingest.py                 # Builds the Chroma vector store
├── retriever.py              # Lazy singleton retriever (MMR)
├── ui.py                     # Claude Code-style terminal renderer
├── app.py                    # REPL entry point
├── prompts.py                # Prompt templates
├── requirements.txt
└── README.md
```

---

## Roadmap

- [ ] FastAPI web interface with REST endpoints
- [ ] Streamlit UI for non-technical users
- [ ] IPC vs BNS side-by-side comparison mode
- [ ] Page-level source citations
- [ ] Docker deployment
- [ ] Accuracy evaluation benchmark

---

<div align="center">

**Built by [Anvit Devadiga](https://github.com/AnvitDevadiga)**

*AI Engineer · Industrial Domain · Production RAG Systems*

[![GitHub](https://img.shields.io/badge/GitHub-AnvitDevadiga-181717?style=for-the-badge&logo=github)](https://github.com/AnvitDevadiga)
[![Email](https://img.shields.io/badge/Email-anvitdevadiga.in@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:anvitdevadiga.in@gmail.com)

</div>
