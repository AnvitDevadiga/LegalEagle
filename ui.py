"""
Terminal UI for Legal Eagle.

A Claude Code–inspired CLI: muted panels, role-coded prompts, markdown
rendering for assistant output, syntax highlighting for code blocks,
and a live spinner during retrieval/generation.

Pure presentation layer — no business logic.
"""
from __future__ import annotations

import sys
import time
from contextlib import contextmanager
from typing import Iterable, Iterator

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# ---------------------------------------------------------------------------
# Theme — muted amber/cyan palette inspired by Claude Code terminal aesthetic
# ---------------------------------------------------------------------------
THEME = Theme(
    {
        "brand":      "bold #d4a657",       # warm amber  (Legal Eagle accent)
        "brand.dim":  "#8a6d3b",
        "user":       "bold #5fafd7",       # soft cyan
        "user.tag":   "bold black on #5fafd7",
        "assistant":  "#e6e6e6",            # off-white body
        "assistant.tag": "bold black on #87d787",
        "system":     "dim #888888",
        "system.tag": "bold black on #d7af5f",
        "error":      "bold #ff5f5f",
        "muted":      "dim #6c6c6c",
        "rule":       "#3a3a3a",
        "kbd":        "#d4a657 on #1c1c1c",
        "ok":         "#87d787",
    }
)

console = Console(theme=THEME, highlight=False)


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
_BANNER = r"""
 ██╗     ███████╗ ██████╗  █████╗ ██╗      ███████╗ █████╗  ██████╗ ██╗     ███████╗
 ██║     ██╔════╝██╔════╝ ██╔══██╗██║      ██╔════╝██╔══██╗██╔════╝ ██║     ██╔════╝
 ██║     █████╗  ██║  ███╗███████║██║      █████╗  ███████║██║  ███╗██║     █████╗
 ██║     ██╔══╝  ██║   ██║██╔══██║██║      ██╔══╝  ██╔══██║██║   ██║██║     ██╔══╝
 ███████╗███████╗╚██████╔╝██║  ██║███████╗ ███████╗██║  ██║╚██████╔╝███████╗███████╗
 ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝
"""


def render_banner(model: str, db_dir: str, doc_count: int | None) -> None:
    """Print the boot banner — model, vector store, and shortcut hints."""
    console.print(Text(_BANNER, style="brand"))

    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="muted", justify="right")
    meta.add_column(style="assistant")
    meta.add_row("model",   f"[brand]{model}[/]   [muted](local · offline)[/]")
    meta.add_row("vectors", f"{db_dir}" + (f"  [muted]· {doc_count} chunks[/]" if doc_count else ""))
    meta.add_row("scope",   "Constitution of India · IPC · Bharatiya Nyaya Sanhita")
    meta.add_row("shortcuts",
                 "[kbd] /help [/]  [kbd] /clear [/]  [kbd] /exit [/]")

    console.print(Panel(
        Align.left(meta),
        title="[brand]Legal Eagle[/]",
        subtitle="[muted]offline legal assistant[/]",
        border_style="rule",
        padding=(1, 2),
    ))
    console.print()


# ---------------------------------------------------------------------------
# Role-tagged messages
# ---------------------------------------------------------------------------
def system_msg(text: str) -> None:
    console.print(f"[system.tag] SYS [/] [system]{text}[/]")


def error_msg(text: str) -> None:
    console.print(f"[error]✖ {text}[/]")


def ok_msg(text: str) -> None:
    console.print(f"[ok]✓ {text}[/]")


def hint(text: str) -> None:
    console.print(f"[muted]· {text}[/]")


def print_user_echo(text: str) -> None:
    """Echo the user's question in a compact panel above the answer."""
    console.print(Panel(
        Text(text.strip(), style="user"),
        title="[user.tag] YOU [/]",
        title_align="left",
        border_style="rule",
        padding=(0, 1),
    ))


def assistant_panel(body) -> Panel:
    """Wrap any renderable as the assistant's answer panel."""
    return Panel(
        body,
        title="[assistant.tag] LEGAL EAGLE [/]",
        title_align="left",
        border_style="brand.dim",
        padding=(1, 2),
    )


def print_assistant(markdown_text: str, footer: str | None = None) -> None:
    body = Markdown(markdown_text, code_theme="ansi_dark", inline_code_theme="ansi_dark")
    if footer:
        body = Group(body, Text(""), Text(footer, style="muted"))
    console.print(assistant_panel(body))


# ---------------------------------------------------------------------------
# Streaming renderer
# ---------------------------------------------------------------------------
def stream_assistant(token_iter: Iterable[str], footer_fn=None) -> str:
    """
    Render a streaming response as it arrives, inside the assistant panel.

    Tokens accumulate into a buffer that is re-rendered as Markdown ~30fps.
    Returns the full text once the stream completes.
    """
    buffer: list[str] = []
    spinner = Spinner("dots", text=Text(" thinking…", style="muted"), style="brand")

    def renderable():
        if not buffer:
            return assistant_panel(spinner)
        md = Markdown("".join(buffer), code_theme="ansi_dark", inline_code_theme="ansi_dark")
        return assistant_panel(md)

    with Live(renderable(), console=console, refresh_per_second=24, transient=False) as live:
        for tok in token_iter:
            if tok:
                buffer.append(tok)
                live.update(renderable())
        # final paint, optionally with footer
        if footer_fn is not None:
            footer = footer_fn("".join(buffer))
            md = Markdown("".join(buffer), code_theme="ansi_dark", inline_code_theme="ansi_dark")
            live.update(assistant_panel(Group(md, Text(""), Text(footer, style="muted"))))

    return "".join(buffer)


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
def read_query() -> str:
    """Read a multi-line-friendly user query with a styled prompt."""
    console.print()
    console.print("[user.tag] YOU [/]", end=" ")
    try:
        line = input()
    except EOFError:
        return "/exit"
    return line


@contextmanager
def working(label: str = "retrieving relevant statutes") -> Iterator[None]:
    """Context manager: shows a spinner while a block runs."""
    spinner = Spinner("dots", text=Text(f" {label}…", style="muted"), style="brand")
    with Live(spinner, console=console, refresh_per_second=20, transient=True):
        yield


# ---------------------------------------------------------------------------
# Help screen
# ---------------------------------------------------------------------------
def print_help() -> None:
    t = Table(show_header=False, box=None, padding=(0, 2))
    t.add_column(style="brand")
    t.add_column(style="assistant")
    t.add_row("/help",   "show this help")
    t.add_row("/clear",  "clear the screen")
    t.add_row("/sources","toggle source citations after each answer")
    t.add_row("/exit",   "quit Legal Eagle")
    t.add_row("",        "")
    t.add_row("Ctrl+C",  "interrupt a running answer")
    console.print(Panel(t, title="[brand]commands[/]", border_style="rule", padding=(1, 2)))


def clear_screen() -> None:
    console.clear()


def goodbye() -> None:
    console.print()
    console.print("[brand.dim]— closing session. stay lawful. —[/]")
    console.print()
