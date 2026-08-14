import hashlib
import uuid
from collections.abc import Callable, Sequence

import streamlit as st
from cora.app.assembly import App
from cora.domain.chat_result import ChatResult
from cora.domain.errors import AdapterError, CoreError
from cora.domain.trace import TraceStep
from cora.engine.agent import Agent
from cora.engine.knowledge_base import KnowledgeBase
from cora.frontends.streamlit.formatting import (
    ingest_message,
    numbered_sources,
    step_text,
)
from cora.frontends.streamlit.thread import ThreadEntry
from cora.ports.memory import Memory
from streamlit.runtime.uploaded_file_manager import UploadedFile

MAX_INGEST_ATTEMPTS = 2
WORKING = "Working…"
TRACE_LABEL = "How I got there"
REMEMBER_HEADING = "What I remember"
NOTHING_REMEMBERED = "Nothing yet — tell me something about yourself."
FORGET_LABEL = "✕"


def main(app_factory: Callable[[], App]) -> None:
    try:
        app = app_factory()
    except CoreError as error:
        st.error(error.user_message)
        return
    render(app)


def render(app: App) -> None:
    """The sidebar is drawn after the turn, because the turn can change what it says: a
    fact the model remembered belongs in the panel the same run it was kept, not the
    next one the user happens to trigger. Streamlit places it by container, not by
    order, so the screen is unchanged."""
    _thread()
    if prompt := st.chat_input("Ask about your documents"):
        _answer(app.agent, prompt)
    with st.sidebar:
        _documents(app.knowledge_base)
        _memory(app.memory)


def _documents(knowledge_base: KnowledgeBase) -> None:
    st.header("Documents")
    uploaded = st.file_uploader("Add a document", type=["txt", "md", "pdf"])
    _ingest_once(knowledge_base, uploaded)
    for source in knowledge_base.list_sources():
        st.markdown(source)


def _memory(memory: Memory | None) -> None:
    """Forgetting runs as a callback, so the list a rerun draws is the list after the
    click rather than the one that was clicked. A callback's failure has to survive
    into that rerun to be shown at all, which is what `memory_error` carries."""
    if memory is None:
        return
    st.header(REMEMBER_HEADING)
    if failed := st.session_state.pop("memory_error", None):
        st.error(failed)
    try:
        facts = memory.recall()
    except AdapterError as error:
        st.error(error.user_message)
        return
    if not facts:
        st.markdown(NOTHING_REMEMBERED)
        return
    for fact in facts:
        said, forget = st.columns([5, 1])
        said.markdown(fact.text)
        forget.button(
            FORGET_LABEL,
            key=f"forget_{fact.key}",
            help="Forget this",
            on_click=_forgetting(memory.forget, fact.key),
        )
    st.button(
        "Forget everything", key="clear_memory", on_click=_forgetting(memory.clear)
    )


def _forgetting(write: Callable[..., None], *args: str) -> Callable[[], None]:
    """A store that went away takes the panel with it, never the chat: the sidebar is
    where memory is shown, so it is where memory's failures belong."""

    def attempt() -> None:
        try:
            write(*args)
        except AdapterError as error:
            st.session_state.memory_error = error.user_message

    return attempt


def _ingest_once(knowledge_base: KnowledgeBase, uploaded: UploadedFile | None) -> None:
    """Ingest a selection once: Streamlit re-delivers the same file every rerun."""
    if uploaded is None:
        st.session_state.upload_key = None
        st.session_state.upload_attempts = None
        return
    data = uploaded.getvalue()
    key = (uploaded.name, hashlib.sha256(data).hexdigest())
    if key == st.session_state.get("upload_key"):
        return
    attempt = _attempts_on(key) + 1
    settled = _ingest(knowledge_base, data, uploaded.name)
    if settled or attempt >= MAX_INGEST_ATTEMPTS:
        st.session_state.upload_key = key
        st.session_state.upload_attempts = None
    else:
        st.session_state.upload_attempts = (key, attempt)


def _attempts_on(key: tuple[str, str]) -> int:
    tried, count = st.session_state.get("upload_attempts") or (None, 0)
    return count if tried == key else 0


def _ingest(knowledge_base: KnowledgeBase, data: bytes, filename: str) -> bool:
    """Report the outcome; return False when a later attempt could still work."""
    try:
        with st.spinner("Ingesting…"):
            chunks = knowledge_base.add_file(data, filename)
    except AdapterError as error:
        st.error(error.user_message)
        return False
    except CoreError as error:
        st.error(error.user_message)
        return True
    report = st.success if chunks else st.info
    report(ingest_message(filename, chunks))
    return True


def _thread() -> None:
    """The session's thread id names the conversation the agent keeps; what is stored
    here is only what the screen has to redraw."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
    for message in st.session_state.messages:
        _show(message)


def _answer(agent: Agent, prompt: str) -> None:
    _append_and_show({"role": "user", "content": prompt})
    taken: list[TraceStep] = []
    live = st.empty()
    try:
        with live.container(), st.status(WORKING, expanded=True):
            result = agent.answer(prompt, st.session_state.thread_id, _watch(taken))
    except CoreError as error:
        live.empty()
        _append_and_show(
            {"role": "assistant", "error": error.user_message, "trace": taken}
        )
        return
    live.empty()
    _append_and_show(_assistant_message(result))


def _watch(taken: list[TraceStep]) -> Callable[[TraceStep], None]:
    def note(step: TraceStep) -> None:
        taken.append(step)
        _show_step(step)

    return note


def _assistant_message(result: ChatResult) -> ThreadEntry:
    return {
        "role": "assistant",
        "content": result.answer,
        "sources": numbered_sources(result.sources),
        "trace": list(result.trace),
    }


def _append_and_show(message: ThreadEntry) -> None:
    st.session_state.messages.append(message)
    _show(message)


def _show(message: ThreadEntry) -> None:
    with st.chat_message(message["role"]):
        if "error" in message:
            st.error(message["error"])
        else:
            st.markdown(message["content"])
            _expander("Sources", message.get("sources", ()))
        _trace(message.get("trace", ()), failed=_went_wrong(message))


def _went_wrong(message: ThreadEntry) -> bool:
    """A failed step sits inside a collapsed panel, so the panel has to carry the
    news: nothing else above the fold would."""
    if "error" in message:
        return True
    return any(step.failed for step in message.get("trace", ()))


def _trace(steps: Sequence[TraceStep], *, failed: bool) -> None:
    if not steps:
        return
    with st.status(TRACE_LABEL, state="error" if failed else "complete"):
        for step in steps:
            _show_step(step)


def _show_step(step: TraceStep) -> None:
    st.code(step_text(step), language="text")


def _expander(label: str, lines: Sequence[str]) -> None:
    if not lines:
        return
    with st.expander(label):
        for line in lines:
            st.markdown(line)
