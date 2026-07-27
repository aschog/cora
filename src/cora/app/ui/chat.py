import hashlib
from collections.abc import Callable, Sequence
from typing import Any

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from cora.app.assembly import App
from cora.app.ui.formatting import format_tool_result, numbered_sources
from cora.core.errors import CoreError
from cora.core.services.chat_engine import ChatEngine, ChatResult
from cora.core.services.knowledge_base import KnowledgeBase

ThreadEntry = dict[str, Any]


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
        _answer(app.engine, prompt)


def _documents(knowledge_base: KnowledgeBase) -> None:
    st.header("Documents")
    uploaded = st.file_uploader("Add a document", type=["txt", "md", "pdf"])
    _ingest_once(knowledge_base, uploaded)
    for source in knowledge_base.list_sources():
        st.markdown(source)


def _ingest_once(knowledge_base: KnowledgeBase, uploaded: UploadedFile | None) -> None:
    if uploaded is None:
        st.session_state.upload_hash = None
        return
    data = uploaded.getvalue()
    file_hash = hashlib.sha256(data).hexdigest()
    if file_hash == st.session_state.get("upload_hash"):
        return
    st.session_state.upload_hash = file_hash
    try:
        with st.spinner("Ingesting…"):
            chunks = knowledge_base.add_file(data, uploaded.name)
    except CoreError as error:
        st.error(error.user_message)
        return
    if chunks:
        st.success(f"Added {uploaded.name} — {chunks} {_chunks(chunks)}.")
    else:
        st.info(f"{uploaded.name} is already in your knowledge base.")


def _chunks(count: int) -> str:
    return "chunk" if count == 1 else "chunks"


def _thread() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        _show(message)


def _answer(engine: ChatEngine, prompt: str) -> None:
    _append_and_show({"role": "user", "content": prompt})
    try:
        with st.spinner("Thinking…"):
            result = engine.answer(prompt)
    except CoreError as error:
        _append_and_show({"role": "assistant", "error": error.user_message})
        return
    _append_and_show(_assistant_message(result))


def _assistant_message(result: ChatResult) -> ThreadEntry:
    return {
        "role": "assistant",
        "content": result.answer,
        "sources": numbered_sources(result.sources),
        "tool_results": [format_tool_result(r) for r in result.tool_results],
    }


def _append_and_show(message: ThreadEntry) -> None:
    st.session_state.messages.append(message)
    _show(message)


def _show(message: ThreadEntry) -> None:
    with st.chat_message(message["role"]):
        if failure := message.get("error"):
            st.error(failure)
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
