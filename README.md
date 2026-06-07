
```markdown
<div align="center">

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗     ███████╗ ██████╗  █████╗ ██╗      ███████╗ █████╗  ██████╗ ██╗     ███████╗
║   ██║     ██╔════╝██╔════╝ ██╔══██╗██║      ██╔════╝██╔══██╗██╔════╝ ██║     ██╔════╝
║   ██║     █████╗  ██║  ███╗███████║██║      █████╗  ███████║██║  ███╗██║     █████╗
║   ██║     ██╔══╝  ██║   ██║██╔══██║██║      ██╔══╝  ██╔══██║██║   ██║██║     ██╔══╝
║   ███████╗███████╗╚██████╔╝██║  ██║███████╗ ███████╗██║  ██║╚██████╔╝███████╗███████╗
║   ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝
║                                                                               ║
║                    🦅  OFFLINE AI LEGAL ASSISTANT FOR INDIA  🦅               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=for-the-badge&logo=ollama&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35?style=for-the-badge)
![License](https://img.shields.io/badge/License-Academic-green?style=for-the-badge)

> **🔒 100% Offline · 💸 Zero API Cost · 🧠 Hallucination‑Resistant**  
> *Ask anything about Indian law. Get grounded, cited answers — entirely from a local Llama 3.*

</div>

---

## 🔥 Why Legal Eagle?

Most “legal AI” tools phone home to ChatGPT or Google – your case strategy, client data, or personal query? **Not here.**  
Legal Eagle runs **entirely on your laptop**, with zero telemetry, zero third‑party APIs, and zero bills.

- ⚡ **Blazing fast RAG** – MMR retrieval + batched embeddings
- 🛡️ **Safety first** – automatic helplines for sensitive queries (abuse, harassment, self‑harm)
- 📚 **620+ pages** of the Constitution, IPC, and Bharatiya Nyaya Sanhita
- 🎨 **Claude‑Code style terminal** – colored panels, live spinner, streaming markdown

---

## 🖥️ Terminal Demo (real output)

```bash
$ python app.py

╭───────── Legal Eagle ──────────╮
│   model    llama3 (local)      │
│ vectors    legal_db · 2999     │
│   scope    Constitution · IPC  │
│            Bharatiya Nyaya     │
│            Sanhita             │
│ shortcuts  /help /clear /exit  │
╰────────────────────────────────╯

> YOU  What does Article 21 guarantee?

╭─ LEGAL EAGLE ──────────────────────────────────────────────────╮
│                                                                │
│ **Article 21 — Constitution of India**                        │
│                                                                │
│ Article 21 guarantees the protection of life and personal      │
│ liberty. No person shall be deprived of these rights except    │
│ according to procedure established by law.                     │
│                                                                │
│ 📄 sources: constitution.pdf · 3 chunks · 1.4s                │
│ ⚖️ Disclaimer: AI‑generated summary. Verify with official     │
│    legal sources or a licensed practitioner.                   │
╰────────────────────────────────────────────────────────────────╯
```

> **Live session screenshots**  
> ![Consumer Rights Query](screenshots/demo-consumer-rights.png)  
> ![Workplace Harassment Query](screenshots/demo-harassment-safety.png)

---

## 🧠 Anti‑Hallucination Arsenal

```
✓  Answers strictly limited to retrieved legal context
✓  Explicit refusal when information is not in the documents
✓  MMR retrieval — diversified context, no duplicate chunks
✓  Low-temperature LLM (temp=0.1) — no creative fabrication
✓  Source citation on every response (PDF · chunk count · latency)
✓  Safety Notice auto-appended for sensitive queries
```

---

## 🏗️ Architecture (as code)

```text
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

## 📜 Legal Coverage

| Document | Coverage | Pages |
|---|---|---|
| Indian Constitution | All Articles + Amendments | ~250 |
| Indian Penal Code (IPC) | All Sections | ~190 |
| Bharatiya Nyaya Sanhita (BNS) | Full Text | ~183 |

---

## 🚀 Quick Start (blood, sweat & 2 minutes)

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) running in background

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
# Place PDFs in data/ first
python ingest.py            # one‑time index build (~2 min)
python ingest.py --rebuild  # nuke & reindex from scratch
```

### 4. Launch the Eagle

```bash
python app.py
```

---

## ⌨️ Slash Commands

| Command | Action |
|---|---|
| `/help` | Show all available commands |
| `/clear` | Clear the screen, redraw banner |
| `/sources` | Toggle source citations on/off |
| `/exit` | Quit Legal Eagle |
| `Ctrl+C` | Interrupt a running answer |

---

## 💎 Features that bleed quality

- **Streaming responses** – tokens render instantly, no waiting.
- **Claude Code‑style terminal** – color‑coded `YOU` / `LEGAL EAGLE` / `SYS` panels.
- **MMR retrieval** – diversified context (`k=5`, `fetch_k=20`), no repetitive chunks.
- **Singleton LLM + embedding clients** – hot cache, zero per‑query overhead.
- **Idempotent ingest** – parallel PDF loading + batched embeddings (64/call).
- **Safety‑aware** – auto‑injects Indian emergency helplines for sensitive keywords.

---

## 📁 Project Structure

```text
legal-eagle/
├── data/                     # PDFs: constitution, ipc, bns
├── screenshots/              # demo images
├── ingest.py                 # Chroma vector store builder
├── retriever.py              # lazy MMR retriever singleton
├── ui.py                     # rich terminal renderer
├── app.py                    # REPL entry point
├── prompts.py                # prompt templates
├── requirements.txt
└── README.md
```

---

## 🗺️ Roadmap

- [ ] FastAPI web interface + REST endpoints
- [ ] Streamlit UI for non‑tech users
- [ ] IPC vs BNS side‑by‑side comparison
- [ ] Page‑level source citations
- [ ] Docker + docker‑compose
- [ ] Accuracy benchmark suite

---

<div align="center">

**Built with 🩸🧠💦 by [Anvit Devadiga](https://github.com/AnvitDevadiga)**  
*AI Engineer · Industrial RAG · Production‑grade systems*

[![GitHub](https://img.shields.io/badge/GitHub-AnvitDevadiga-181717?style=for-the-badge&logo=github)](https://github.com/AnvitDevadiga)
[![Email](https://img.shields.io/badge/Email-anvitdevadiga.in@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:anvitdevadiga.in@gmail.com)

</div>
```
