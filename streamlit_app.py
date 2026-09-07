"""Legal Eagle — private, offline legal research for Indian law."""
from __future__ import annotations

import base64
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import streamlit as st
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from ollama import Client

from retriever import collection_size, retrieve_documents


APP_DIR = Path(__file__).resolve().parent
COURT_IMAGE = APP_DIR / "assets" / "courtroom.jpg"
EAGLE_LOGO = APP_DIR / "assets" / "eagle-logo.png"
USER_PROFILE = APP_DIR / "assets" / "user-profile.png"
VECTOR_DB_FILE = APP_DIR / "legal_db" / "chroma.sqlite3"
LLM_MODEL = "llama3"
EMBED_MODEL = "nomic-embed-text"
MAX_MESSAGES = 30

RESPONSE_DISCLAIMER = (
    "AI-generated legal information. Verify material conclusions against the "
    "official text or with a qualified advocate."
)

_CONVERSATIONAL = {
    "hi": "Hello. What would you like to understand about Indian law?",
    "hello": "Hello. What would you like to understand about Indian law?",
    "hey": "Hello. What would you like to understand about Indian law?",
    "thanks": "You’re welcome. Ask another question whenever you’re ready.",
    "thank you": "You’re welcome. Ask another question whenever you’re ready.",
    "thankyou": "You’re welcome. Ask another question whenever you’re ready.",
}

_HIGH_RISK_KEYWORDS = (
    "abuse", "suicide", "self-harm", "self harm", "violence", "assault",
    "kill", "threat",
)

SAFETY_BLOCK = """### Immediate safety support

If you or someone else is in immediate danger, call **112** in India.

- KIRAN mental health helpline: **1800-599-0019**
- Women’s helpline: **181**

This assistant cannot provide emergency, medical, or crisis support."""


st.set_page_config(
    page_title="Legal Eagle · Offline Indian Law Research",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Legal Eagle is a private, fully offline Indian-law research assistant."
    },
)


STYLES = """
<style>
:root {
  --court-ink: #201718;
  --court-muted: #746a67;
  --court-canvas: #f4f0e8;
  --court-paper: #fdfcf9;
  --court-rule: #ddd3c5;
  --court-wine: #641f29;
  --court-wine-dark: #421419;
  --court-green: #173f34;
  --court-brass: #a97828;
  --court-brass-soft: #d9bd83;
}

html, body, [class*="st-"] {
  font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  color: var(--court-ink);
  background:
    radial-gradient(circle at 82% 5%, rgba(169,120,40,.13), transparent 34rem),
    radial-gradient(circle at 18% 88%, rgba(100,31,41,.065), transparent 31rem),
    linear-gradient(145deg, #f8f4ec 0%, #eee7db 52%, #f7f2e9 100%);
}
#MainMenu, footer,
[data-testid="stToolbar"],
[data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stHeader"] {
  display:block !important; height:3.35rem !important; min-height:3.35rem !important;
  background:transparent !important; pointer-events:none !important;
}
[data-testid="collapsedControl"] {
  display:block !important; visibility:visible !important; opacity:1 !important;
  position:fixed !important; top:.8rem !important; left:.8rem !important;
  z-index:9999 !important; pointer-events:auto !important;
}
.block-container { max-width: 940px; padding: 1.25rem 2rem 7.5rem; }

/* Sidebar: dark timber and oxblood, like a court brief rather than a dashboard. */
[data-testid="stSidebar"] {
  background: linear-gradient(165deg, #281719 0%, #170e0f 58%, #111916 100%);
  border-right: 1px solid #3a2928;
}
[data-testid="stSidebar"] > div:first-child { padding-top: .65rem; }
[data-testid="stSidebar"] * { color: #f5efe5; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: #bfb3a7 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.09); }
[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"] button {
  color: var(--court-wine-dark) !important;
  background: #f8f4ec !important;
  border: 1px solid #d5c9b8 !important;
  border-radius: 50% !important;
}
[data-testid="stSidebarHeader"] { min-height: 2.5rem; }
[data-testid="stSidebarCollapseButton"] {
  display:block !important; visibility:visible !important; opacity:1 !important;
  position:absolute !important; top:.72rem !important; right:.72rem !important; z-index:9999 !important;
}
[data-testid="stSidebarCollapseButton"] button {
  display:grid !important; place-items:center !important; width:2rem !important; height:2rem !important;
  min-height:2rem !important; padding:0 !important; box-shadow:0 4px 14px rgba(0,0,0,.22) !important;
}

.brand { display: flex; align-items: center; gap: .8rem; padding: .15rem 0 1rem; }
.brand-seal {
  width: 2.55rem; height: 2.55rem; display: grid; place-items: center; flex: 0 0 auto;
  border-radius: 50%; border: 1px solid rgba(217,189,131,.7); object-fit:cover;
  box-shadow: inset 0 0 0 3px rgba(39,21,22,.30), 0 4px 14px rgba(0,0,0,.2);
}
.brand-name { font-family: Georgia, "Times New Roman", serif; font-size: 1.16rem; font-weight: 700; }
.brand-note { color: #bfb3a7 !important; font-size: .76rem; letter-spacing: .035em; margin-top: .08rem; }
.sidebar-label { color: #d8bd89 !important; font-size: .72rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .5rem; }
.library-row { display: flex; align-items: center; gap: .55rem; margin: .52rem 0; font-size: .86rem; color: #e9dfd2 !important; }
.library-dot { width: .42rem; height: .42rem; background: #bd8e42; border-radius: 50%; flex: 0 0 auto; }
.local-chip {
  display: flex; gap: .55rem; align-items: center; margin: .75rem 0 0;
  padding: .62rem .72rem; border-radius: .65rem; background: rgba(37,105,77,.18);
  border: 1px solid rgba(127,190,159,.18); color: #c9e4d6 !important; font-size: .79rem;
}
.local-dot { width: .45rem; height: .45rem; border-radius: 50%; background: #5fc08e; box-shadow: 0 0 0 4px rgba(95,192,142,.10); }
[data-testid="stSidebar"] .stButton button {
  min-height: 2.55rem; border-radius: .65rem; background: rgba(255,255,255,.055);
  border: 1px solid rgba(255,255,255,.12); color: #f4eee5; font-weight: 650;
}
[data-testid="stSidebar"] .stButton button:hover { background: rgba(255,255,255,.10); border-color: rgba(217,189,131,.45); }
[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: rgba(255,255,255,.035); border-color: rgba(255,255,255,.10);
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary * { color:#d8cec2 !important; }
[data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
  color:#d8bd89 !important; font-size:0 !important; width:1rem; overflow:hidden;
}
[data-testid="stExpander"] summary [data-testid="stIconMaterial"]::before {
  content:"›"; font:700 1.05rem/1 Georgia,serif;
}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] {
  font-size:0 !important; width:1rem; overflow:hidden;
}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"]::before {
  content:"‹"; font:700 1.1rem/1 Georgia,serif;
}
[data-testid="collapsedControl"] [data-testid="stIconMaterial"] {
  font-size:0 !important; width:1rem; overflow:hidden;
}
[data-testid="collapsedControl"] [data-testid="stIconMaterial"]::before {
  content:"›"; font:700 1.1rem/1 Georgia,serif;
}
[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display:none !important; }

/* Compact product masthead. */
.masthead { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.35rem 0 1rem; border-bottom:1px solid var(--court-rule); margin-bottom:1rem; }
.masthead-title { font-family:Georgia,"Times New Roman",serif; font-size:1.22rem; font-weight:700; letter-spacing:-.015em; }
.masthead-badge { white-space:nowrap; color:var(--court-green); border:1px solid #bad0c3; background:#eaf1ec; border-radius:999px; padding:.35rem .62rem; font-size:.75rem; font-weight:700; }

/* Courtroom welcome panel. */
.court-hero {
  min-height: 245px; display:flex; align-items:flex-end; position:relative; overflow:hidden;
  border-radius: 1rem; border: 1px solid #c8b89e; background-position:center 44%; background-size:cover;
  box-shadow: 0 18px 44px rgba(47,30,24,.12);
}
.court-hero::after { content:""; position:absolute; inset:0; background:linear-gradient(180deg,rgba(17,12,10,.04) 12%,rgba(20,13,12,.90) 100%); }
.court-copy { position:relative; z-index:1; max-width:650px; padding:1.45rem 1.6rem; color:#fffaf1; }
.court-kicker { color:#e0bd79; font-size:.72rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.32rem; }
.court-title { font-family:Georgia,"Times New Roman",serif; font-size:clamp(1.75rem,4vw,2.6rem); line-height:1.04; font-weight:700; letter-spacing:-.025em; }
.court-subtitle { color:#e7ddd0; font-size:.91rem; line-height:1.5; margin-top:.48rem; max-width:575px; }

.prompt-label { display:flex; align-items:baseline; justify-content:space-between; gap:1rem; margin:1.55rem 0 .75rem; }
.prompt-label strong { font-family:Georgia,"Times New Roman",serif; font-size:1.04rem; }
.prompt-label span { color:var(--court-muted); font-size:.78rem; }
.prompt-grid { display:grid; grid-template-columns:1fr 1fr; gap:.65rem; }

/* ChatGPT-like conversation: assistant on the page, user in a compact bubble. */
[data-testid="stChatMessage"] {
  background: transparent; border: 0; border-radius: 0; padding: 1.1rem .15rem;
  margin: 0; box-shadow: none; border-bottom: 1px solid var(--court-rule);
}
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] {
  border: 1px solid #d1c4b1; box-shadow: 0 2px 7px rgba(55,35,27,.08);
}
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"] { background:#efe7da; }
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] { background:var(--court-wine); color:white; }
[data-testid="stChatMessageContent"] { font-size:1rem; line-height:1.72; }
[data-testid="stChatMessageContent"] h3 { font-family:Georgia,"Times New Roman",serif; font-size:1.03rem; margin-top:1.2rem; color:var(--court-wine); }
[data-testid="stChatMessageContent"] strong { color:#312121; }

/* Composer: persistent, roomy, and visually quiet. Native Enter/Shift+Enter behavior is retained. */
[data-testid="stBottom"] {
  background:linear-gradient(180deg,rgba(235,228,215,.84) 0%,#eee7db 38%,#eee7db 100%) !important;
  box-shadow:none !important;
}
[data-testid="stBottomBlockContainer"] {
  background:transparent !important; box-shadow:none !important;
  padding-top:.55rem !important; padding-bottom:.7rem !important;
}
[data-testid="stChatInput"] { background:transparent !important; padding-top:0 !important; }
[data-testid="stChatInput"] > div {
  background:#fffdf8; border:1px solid #cbbca5; border-radius:1rem;
  box-shadow:0 12px 32px rgba(48,29,23,.13), inset 0 0 0 1px rgba(255,255,255,.7);
}
[data-testid="stChatInput"] > div:focus-within { border-color:var(--court-wine); box-shadow:0 12px 32px rgba(48,29,23,.13),0 0 0 3px rgba(100,31,41,.09); }
[data-testid="stChatInput"] textarea { min-height:3.25rem; padding-top:.9rem; color:var(--court-ink); caret-color:var(--court-wine); }
[data-testid="stChatInput"] button { color:var(--court-wine); }

.stButton button { min-height:3.15rem; border-radius:.72rem; border:1px solid #d7cbb9; background:#fdfbf6; color:#332627; font-weight:600; text-align:left; padding:.55rem .8rem; }
.stButton button:hover { border-color:var(--court-wine); color:var(--court-wine); background:#fff; }
.stButton button:focus-visible { outline:3px solid rgba(100,31,41,.18); outline-offset:2px; }
[data-testid="stExpander"] { border:1px solid var(--court-rule); background:#faf7f1; border-radius:.7rem; }
[data-testid="stChatMessage"] [data-testid="stExpander"] { max-width:14rem; }
[data-testid="stChatMessage"] [data-testid="stExpander"] summary { min-height:2.5rem; padding-top:.5rem; padding-bottom:.5rem; }
[data-testid="stAlert"] { border-radius:.75rem; }
.answer-meta { color:var(--court-muted); font-size:.75rem; line-height:1.45; margin-top:.85rem; }
.retrieval-note { color:var(--court-muted); font-size:.82rem; padding:.35rem 0; }
blockquote { border-left:3px solid var(--court-brass) !important; background:#f7f0e3; padding:.7rem 1rem; }

@media (max-width: 760px) {
  .block-container { padding: .8rem 1rem 6.8rem; }
  .court-hero { min-height:220px; border-radius:.8rem; }
  .court-copy { padding:1.15rem 1.1rem; }
  .court-subtitle { font-size:.86rem; }
  .prompt-grid { grid-template-columns:1fr; }
  .prompt-label span { display:none; }
  [data-testid="stChatMessage"] { padding:.9rem 0; }
}
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)


def _install_sidebar_toggle() -> None:
    """Install an offline-safe sidebar control that survives responsive layouts."""
    st.html(
        """
        <script>
        (() => {
          const doc = window.document;
          const root = doc.body;
          let style = doc.getElementById("legal-eagle-sidebar-style");
          if (!style) {
            style = doc.createElement("style");
            style.id = "legal-eagle-sidebar-style";
            style.textContent = `
              body.le-sidebar-forced [data-testid="stSidebar"] {
                display: block !important;
                visibility: visible !important;
                transform: translateX(0) !important;
                left: 0 !important;
                width: 19rem !important;
                min-width: 19rem !important;
                max-width: 85vw !important;
                z-index: 9998 !important;
                box-shadow: 18px 0 50px rgba(13,8,9,.34) !important;
              }
              body.le-sidebar-forced [data-testid="stSidebarContent"] {
                width: 100% !important;
                min-width: 0 !important;
              }
              #legal-eagle-sidebar-toggle {
                position: fixed; top: 12px; left: 12px; z-index: 10001;
                width: 34px; height: 34px; display: grid; place-items: center;
                padding: 0; border-radius: 50%; cursor: pointer;
                color: #641f29; background: #fffaf1; border: 1px solid #cbbca5;
                box-shadow: 0 5px 16px rgba(38,22,19,.18);
                font: 700 18px/1 Georgia, serif;
              }
              #legal-eagle-sidebar-toggle:hover { background: #fff; border-color: #641f29; }
              #legal-eagle-sidebar-toggle:focus-visible { outline: 3px solid rgba(100,31,41,.22); outline-offset: 2px; }
            `;
            doc.head.appendChild(style);
          }

          let button = doc.getElementById("legal-eagle-sidebar-toggle");
          if (!button) {
            button = doc.createElement("button");
            button.id = "legal-eagle-sidebar-toggle";
            button.type = "button";
            root.appendChild(button);
          }

          const sync = () => {
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            if (!sidebar) return;
            const rect = sidebar.getBoundingClientRect();
            const forced = root.classList.contains("le-sidebar-forced");
            const visible = forced || (rect.right > 40 && rect.left > -40);
            button.textContent = visible ? "‹" : "☰";
            button.setAttribute("aria-label", visible ? "Hide navigation" : "Show navigation");
            button.title = visible ? "Hide navigation" : "Show navigation";
            button.style.left = visible ? `${Math.max(12, rect.width - 48)}px` : "12px";
          };

          button.onclick = () => {
            if (root.classList.contains("le-sidebar-forced")) {
              root.classList.remove("le-sidebar-forced");
            } else {
              const sidebar = doc.querySelector('[data-testid="stSidebar"]');
              const rect = sidebar ? sidebar.getBoundingClientRect() : {right: 0, left: -999};
              if (sidebar && rect.right > 40 && rect.left > -40) {
                const nativeClose = sidebar.querySelector('[data-testid="stSidebarCollapseButton"] button');
                if (nativeClose) nativeClose.click();
                else root.classList.add("le-sidebar-forced");
              } else {
                root.classList.add("le-sidebar-forced");
              }
            }
            window.setTimeout(sync, 180);
          };

          sync();
          window.setTimeout(sync, 250);
          window.addEventListener("resize", sync, {passive: true});
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


_install_sidebar_toggle()


PROMPT = ChatPromptTemplate.from_template("""\
You are Legal Eagle, an Indian-law research assistant. Answer only from the supplied context.

Write like a careful legal researcher speaking to a non-lawyer:
- Give the direct answer first.
- Name the relevant Act and Article or Section whenever the context supports it.
- Clearly distinguish the IPC from the BNS when both appear.
- Explain legal language in plain English without becoming casual.
- Do not invent procedures, remedies, facts, or citations.
- If the context is insufficient, identify exactly what the local library cannot establish.
- Use short paragraphs and bullets where helpful. Do not repeat the question.
- Keep routine answers under 250 words.
- Never include an empty or inapplicable section, and never write "None" as a section answer.

Formatting for this question:
{format_instruction}

Legal context:
{context}

Question:
{question}

Answer:
""")


@lru_cache(maxsize=1)
def _llm() -> ChatOllama:
    """Keep the local model warm between prompts to reduce repeat latency."""
    return ChatOllama(
        model=LLM_MODEL,
        temperature=0.1,
        num_ctx=4096,
        num_predict=450,
        keep_alive="30m",
    )


@st.cache_data(show_spinner=False, max_entries=48)
def _retrieve(query: str) -> list[Document]:
    """Cache repeated research questions without sending anything off-device."""
    return retrieve_documents(query)


@st.cache_data(show_spinner=False)
def _image_data_uri(path: str) -> str:
    image_path = Path(path)
    data = image_path.read_bytes()
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


@st.cache_data(show_spinner=False, ttl=5)
def system_status() -> tuple[bool, str]:
    """Verify the daemon and required models once per app process."""
    try:
        installed = {
            model.model.split(":", 1)[0]
            for model in Client().list().models
            if model.model
        }
        missing = sorted({LLM_MODEL, EMBED_MODEL} - installed)
        if missing:
            return False, "Missing local model(s): " + ", ".join(missing)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _conversational_response(query: str) -> str | None:
    return _CONVERSATIONAL.get(query.strip().lower().rstrip("!.?,"))


def _needs_safety_block(query: str) -> bool:
    lowered = query.lower()
    return any(keyword in lowered for keyword in _HIGH_RISK_KEYWORDS)


def _stream(messages, include_safety: bool) -> Iterator[str]:
    for chunk in _llm().stream(messages):
        token = getattr(chunk, "content", "") or ""
        if token:
            yield token
    if include_safety:
        yield "\n\n" + SAFETY_BLOCK


def _format_instruction(query: str) -> str:
    """Keep explanatory answers lean; add action steps only when requested."""
    asks_for_action = bool(
        re.search(
            r"\b(what (?:can|should) i do|how (?:do|can) i|procedure|file|"
            r"approach|remed(?:y|ies)|next steps?)\b",
            query.lower(),
        )
    )
    if asks_for_action:
        return (
            "Use ### Applicable law and ### In plain terms. Add ### Practical next steps "
            "only if those steps are explicitly supported by the context."
        )
    return (
        "Use exactly two headings: ### Applicable law and ### In plain terms. "
        "Do not include practical steps or a limitations section."
    )


def source_citations(documents: list[Document]) -> list[str]:
    grouped: dict[str, set[str]] = {}
    for document in documents:
        source = Path(str(document.metadata.get("source", "Local legal document"))).name
        raw_page = document.metadata.get("page_label")
        if raw_page is None:
            raw_page = int(document.metadata.get("page", 0)) + 1
        grouped.setdefault(source, set()).add(str(raw_page))

    citations = []
    for source, pages in sorted(grouped.items()):
        ordered = sorted(pages, key=lambda value: int(value) if value.isdigit() else 10**9)
        citations.append(f"**{source}** — " + ", ".join(f"p. {page}" for page in ordered))
    return citations


def render_sources(sources: list[str]) -> None:
    if not sources:
        return
    with st.expander(f"Sources · {len(sources)}"):
        for source in sources:
            st.markdown(f"- {source}")


def render_sidebar(doc_count: int | None) -> bool:
    with st.sidebar:
        logo_uri = _image_data_uri(str(EAGLE_LOGO))
        st.markdown(
            f'<div class="brand"><img class="brand-seal" src="{logo_uri}" alt="Eagle emblem"><div>'
            '<div class="brand-name">Legal Eagle</div>'
            '<div class="brand-note">INDIAN LAW · OFFLINE</div></div></div>',
            unsafe_allow_html=True,
        )
        if st.button("＋  New Case", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown('<div class="sidebar-label">The library</div>', unsafe_allow_html=True)
        for title in ("Constitution of India", "Indian Penal Code", "Bharatiya Nyaya Sanhita"):
            st.markdown(f'<div class="library-row"><span class="library-dot"></span>{title}</div>', unsafe_allow_html=True)

        st.markdown("---")
        show_sources = st.toggle(
            "Show source pages",
            value=True,
            help="Show the local documents and pages used to prepare each answer.",
        )
        st.markdown(
            f'<div class="local-chip"><span class="local-dot"></span>'
            f'<span>Local engine ready · {doc_count or 0:,} passages</span></div>',
            unsafe_allow_html=True,
        )
        with st.expander("About this research tool"):
            st.caption(RESPONSE_DISCLAIMER)
            st.caption("Coverage is limited to the documents listed above. Nothing is uploaded.")
    return show_sources


def render_masthead() -> None:
    st.markdown(
        '<div class="masthead"><div class="masthead-title">Legal Eagle</div>'
        '<div class="masthead-badge">● Private on-device session</div></div>',
        unsafe_allow_html=True,
    )


def _queue_query(query: str) -> None:
    st.session_state.pending_query = query


def render_empty_state() -> None:
    image_uri = _image_data_uri(str(COURT_IMAGE))
    st.markdown(
        f'<div class="court-hero" style="background-image:url(\'{image_uri}\')">'
        '<div class="court-copy"><div class="court-kicker">The court is in session</div>'
        '<div class="court-title">Research Indian law with clarity.</div>'
        '<div class="court-subtitle">Ask in plain language. Legal Eagle examines the authorities '
        'stored on this computer and gives you a focused, traceable answer.</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="prompt-label"><strong>Begin with a question</strong>'
        '<span>Enter to send · Shift + Enter for a new line</span></div>',
        unsafe_allow_html=True,
    )
    suggestions = [
        "What protection does Article 21 provide?",
        "Explain the BNS right of private defence.",
        "Distinguish culpable homicide from murder.",
        "What remedies exist for a fundamental-rights violation?",
    ]
    left, right = st.columns(2)
    for index, suggestion in enumerate(suggestions):
        with left if index % 2 == 0 else right:
            st.button(
                suggestion,
                key=f"suggestion_{index}",
                use_container_width=True,
                on_click=_queue_query,
                args=(suggestion,),
            )


def render_history() -> None:
    for message in st.session_state.messages:
        avatar = str(USER_PROFILE) if message["role"] == "user" else str(EAGLE_LOGO)
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_sources(message.get("sources", []))
                if message.get("meta"):
                    st.markdown(f'<div class="answer-meta">{message["meta"]}</div>', unsafe_allow_html=True)


def run_query(query: str, show_sources: bool) -> None:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar=str(USER_PROFILE)):
        st.markdown(query)

    with st.chat_message("assistant", avatar=str(EAGLE_LOGO)):
        greeting = _conversational_response(query)
        if greeting is not None:
            response = greeting
            sources: list[str] = []
            elapsed = 0.0
        else:
            started = time.perf_counter()
            research_note = st.empty()
            research_note.markdown('<div class="retrieval-note">Reviewing the local authorities…</div>', unsafe_allow_html=True)
            try:
                documents = _retrieve(query)
                research_note.empty()
                if not documents:
                    response = (
                        "The local library did not return enough material to answer that question. "
                        "Try naming the Act, Article, or Section you want to research."
                    )
                    st.markdown(response)
                    sources = []
                else:
                    context = "\n\n".join(document.page_content for document in documents)
                    messages = PROMPT.invoke(
                        {
                            "context": context,
                            "question": query,
                            "format_instruction": _format_instruction(query),
                        }
                    ).to_messages()
                    response = st.write_stream(_stream(messages, _needs_safety_block(query)))
                    sources = source_citations(documents) if show_sources else []
                elapsed = time.perf_counter() - started
            except Exception:
                research_note.empty()
                st.error("The local model stopped before it could finish the answer.", icon="⚠️")
                st.caption("Confirm that Ollama is running, then submit the question again.")
                st.session_state.messages.pop()
                return

        render_sources(sources)
        meta = "" if elapsed == 0 else f"Prepared locally in {elapsed:.1f}s · {RESPONSE_DISCLAIMER}"
        if meta:
            st.markdown(f'<div class="answer-meta">{meta}</div>', unsafe_allow_html=True)

    st.session_state.messages.append(
        {"role": "assistant", "content": response, "sources": sources, "meta": meta}
    )
    st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]


def render_setup_state(error_detail: str) -> None:
    st.markdown('<div class="masthead-badge">● Local setup required</div>', unsafe_allow_html=True)
    st.title("The local research engine is offline")
    st.markdown(
        "Legal Eagle cannot reach Ollama or one of its models. Start the engine, "
        "then reload this page. Your documents remain on this computer."
    )
    st.code("ollama serve\nollama pull llama3\nollama pull nomic-embed-text", language="bash")
    with st.expander("Technical details"):
        st.code(error_detail or "No additional details were returned.")


def ensure_local_library() -> bool:
    """Repair a missing bundled index automatically on first launch."""
    if VECTOR_DB_FILE.is_file() and VECTOR_DB_FILE.stat().st_size > 0:
        return True

    st.title("Preparing your private legal library")
    st.markdown(
        "The prebuilt index is missing, so Legal Eagle is creating it from the "
        "included Constitution, IPC, and BNS documents. This happens only once."
    )
    with st.status("Indexing the included legal authorities…", expanded=True) as status:
        st.write("Reading the bundled PDFs and creating local search passages.")
        try:
            # Keep PDF tooling out of the normal startup path. It is loaded only
            # when a clone genuinely needs its bundled index repaired.
            from ingest import build_vector_store

            build_vector_store()
        except Exception as exc:
            status.update(label="The legal library could not be prepared", state="error")
            st.error("Confirm that Ollama is running and reload the page.")
            with st.expander("Technical details"):
                st.code(str(exc))
            return False
        status.update(label="Your legal library is ready", state="complete")

    st.rerun()
    return True


def main() -> None:
    st.session_state.setdefault("messages", [])
    ready, error_detail = system_status()
    if not ready:
        render_setup_state(error_detail)
        st.stop()
    if not ensure_local_library():
        st.stop()

    passage_count = collection_size()
    if passage_count in (None, 0):
        st.error("The bundled legal library is unreadable. Delete legal_db and reload to rebuild it.")
        st.stop()

    show_sources = render_sidebar(passage_count)
    render_masthead()

    # Render the native composer before the content decision. Streamlit pins it to
    # the viewport bottom, while this ordering prevents the empty state flashing
    # above a newly submitted question.
    typed_query = st.chat_input(
        "Ask about the Constitution, IPC, or BNS…",
        key="legal_query",
        max_chars=2000,
    )
    query = st.session_state.pop("pending_query", None) or typed_query

    render_history()
    if query and query.strip():
        run_query(query.strip(), show_sources)
    elif not st.session_state.messages:
        render_empty_state()


if __name__ == "__main__":
    main()
