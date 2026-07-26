from typing import Any

import streamlit as st

from cora.app.assembly import App
from cora.app.ui.formatting import format_tool_result, numbered_sources
from cora.core.errors import CoreError
from cora.core.services.chat_engine import ChatResult

Message = dict[str, Any]


def render(app: App) -> None:
    with st.sidebar:
        st.header("Documents")
        uploaded = st.file_uploader("Add a document", type=["txt", "md", "pdf"])
        if uploaded is not None:
            with st.spinner("Ingesting…"):
                app.knowledge_base.add_file(uploaded.getvalue(), uploaded.name)
        for source in app.knowledge_base.list_sources():
            st.markdown(source)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        _show(message)

    if prompt := st.chat_input("Ask about your documents"):
        user: Message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user)
        _show(user)
        try:
            with st.spinner("Thinking…"):
                result = app.engine.answer(prompt)
        except CoreError as error:
            st.error(error.user_message)
        else:
            assistant = _assistant_message(result)
            st.session_state.messages.append(assistant)
            _show(assistant)


def _assistant_message(result: ChatResult) -> Message:
    return {
        "role": "assistant",
        "content": result.answer,
        "sources": numbered_sources(result.sources),
        "tool_results": [format_tool_result(r) for r in result.tool_results],
    }


def _show(message: Message) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for line in message["sources"]:
                    st.markdown(line)
        if message.get("tool_results"):
            with st.expander("Tool results"):
                for line in message["tool_results"]:
                    st.markdown(line)
