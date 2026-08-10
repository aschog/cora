import hashlib
from collections.abc import Callable, Sequence

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from cora.app.assembly import App
from cora.app.ui.formatting import ingest_message, numbered_sources
from cora.app.ui.thread import ThreadEntry, thread_to_turns
from cora.core.errors import AdapterError, CoreError
from cora.core.services.agent import Agent, ChatResult
from cora.core.services.knowledge_base import KnowledgeBase

MAX_INGEST_ATTEMPTS = 2


def main(app_factory: Callable[[], App]) -> None:
    try:
        app = app_factory()
    except CoreError as error:
        st.error(error.user_message)
        return
    render(app)


def render(app: App) -> None:
    with st.sidebar:
        _documents(app.knowledge_base)
    _thread()
    if prompt := st.chat_input("Ask about your documents"):
        _answer(app.agent, prompt)


def _documents(knowledge_base: KnowledgeBase) -> None:
    st.header("Documents")
    uploaded = st.file_uploader("Add a document", type=["txt", "md", "pdf"])
    _ingest_once(knowledge_base, uploaded)
    for source in knowledge_base.list_sources():
        st.markdown(source)


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
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        _show(message)


def _answer(agent: Agent, prompt: str) -> None:
    history = thread_to_turns(st.session_state.messages)
    _append_and_show({"role": "user", "content": prompt})
    try:
        with st.spinner("Thinking…"):
            result = agent.answer(prompt, history)
    except CoreError as error:
        _append_and_show({"role": "assistant", "error": error.user_message})
        return
    _append_and_show(_assistant_message(result))


def _assistant_message(result: ChatResult) -> ThreadEntry:
    return {
        "role": "assistant",
        "content": result.answer,
        "sources": numbered_sources(result.sources),
        "tool_results": [r.render() for r in result.tool_results],
    }


def _append_and_show(message: ThreadEntry) -> None:
    st.session_state.messages.append(message)
    _show(message)


def _show(message: ThreadEntry) -> None:
    with st.chat_message(message["role"]):
        if "error" in message:
            st.error(message["error"])
            return
        st.markdown(message["content"])
        _expander("Sources", message.get("sources", ()))
        _expander("Tool results", message.get("tool_results", ()))


def _expander(label: str, lines: Sequence[str]) -> None:
    if not lines:
        return
    with st.expander(label):
        for line in lines:
            st.markdown(line)
