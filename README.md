# 🦅 Legal Eagle

**Offline RAG legal assistant for Indian law — no cloud, no API keys.**

Searches 620+ bundled pages of the Indian Constitution, IPC, and Bharatiya Nyaya Sanhita and answers questions using Llama 3 via Ollama. The PDFs and ready-to-use search index are included; everything runs on your machine.

---

## Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) installed and running

### 1 — Clone & install

```bash
git clone https://github.com/AnvitDevadiga/LegalEagle.git
cd LegalEagle
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2 — Pull the local models

```bash
ollama pull llama3
ollama pull nomic-embed-text
```

If Ollama is not already running, open the Ollama app or run `ollama serve` in another terminal first.

### 3 — Launch

```bash
python -m streamlit run streamlit_app.py
```

Open **http://localhost:8501**. That is all—the legal documents and search index are already included.

> If the index is ever missing, Legal Eagle rebuilds it automatically from the bundled PDFs on the next launch. No separate ingestion command is required.

### Optional: refresh the legal library

You only need this after replacing or adding PDFs in `data/`:

```bash
python ingest.py --rebuild
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| LLM | Llama 3 via Ollama | Local, zero API cost |
| Embeddings | `nomic-embed-text` | High-quality legal text vectors |
| RAG Framework | LangChain | Composable retrieval pipeline |
| Vector DB | ChromaDB (persisted) | Hybrid exact-reference + semantic retrieval |
| Web UI | Streamlit | Responsive research workspace, live streaming |
| Language | Python 3.11+ | |

---

## Legal Coverage

| Document | Chunks | Pages |
|---|---|---|
| Indian Constitution | 1,453 | 402 |
| Indian Penal Code (IPC) | 791 | 119 |
| Bharatiya Nyaya Sanhita (BNS) | 646 | 102 |
| **Total** | **2,890** | **623** |

---

## Project Structure

```
LegalEagle/
├── data/
│   ├── constitution.pdf
│   ├── ipc.pdf
│   └── bns.pdf
├── assets/
│   ├── courtroom.jpg   ← Offline courtroom artwork
│   ├── eagle-logo.png  ← Brand and assistant emblem
│   └── user-profile.png ← User-message profile medallion
├── .streamlit/
│   └── config.toml     ← Local theme and privacy settings
├── legal_db/              ← Bundled, ready-to-use local search index
├── streamlit_app.py     ← Web UI, safety filter, streaming
├── ingest.py            ← PDF loader, chunker, Chroma embedder
├── retriever.py         ← Cached hybrid legal retriever
├── requirements.txt
└── README.md
```

---

## Product Notes

- **Grounding first** — answers are constrained to retrieved legal context and clearly flag missing coverage
- **Hybrid retrieval** — exact Article/Section lookups are combined with semantic context
- **Low temperature (0.1)** — more consistent local responses
- **Responsive court interface** — keyboard-friendly ChatGPT-style composer and streamed answers
- **Safety filter** — auto-injects helplines for sensitive keywords (abuse, violence, self-harm)
- **Fully offline** — no data leaves your machine
- **Three-step setup** — the PDFs and search index ship with the project; missing indexes self-repair on launch
