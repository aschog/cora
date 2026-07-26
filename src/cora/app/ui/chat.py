from collections.abc import Sequence
from typing import Any

import streamlit as st

from cora.app.assembly import App
from cora.app.ui.formatting import format_tool_result, numbered_sources
from cora.core.errors import CoreError
from cora.core.services.chat_engine import ChatEngine, ChatResult
from cora.core.services.knowledge_base import KnowledgeBase

Message = dict[str, Any]


def render(app: App) -> None:
    with st.sidebar:
        _documents(app.knowledge_base)
    _thread()
    if prompt := st.chat_input("Ask about your documents"):
        _answer(app.engine, prompt)


def _documents(knowledge_base: KnowledgeBase) -> None:
    st.header("Documents")
    uploaded = st.file_uploader("Add a document", type=["txt", "md", "pdf"])
    if uploaded is not None:
        with st.spinner("Ingesting…"):
            knowledge_base.add_file(uploaded.getvalue(), uploaded.name)
    for source in knowledge_base.list_sources():
        st.markdown(source)


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
        st.error(error.user_message)
        return
    _append_and_show(_assistant_message(result))


def _assistant_message(result: ChatResult) -> Message:
    return {
        "role": "assistant",
        "content": result.answer,
        "sources": numbered_sources(result.sources),
        "tool_results": [format_tool_result(r) for r in result.tool_results],
    }


def _append_and_show(message: Message) -> None:
    st.session_state.messages.append(message)
    _show(message)


def _show(message: Message) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        _expander("Sources", message.get("sources", ()))
        _expander("Tool results", message.get("tool_results", ()))


def _expander(label: str, lines: Sequence[str]) -> None:
    if not lines:
        return
    with st.expander(label):
        for line in lines:
            st.markdown(line)
