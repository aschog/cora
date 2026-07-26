import streamlit as st

from cora.app.assembly import App, build
from cora.app.config import Config
from cora.app.ui.chat import main

st.set_page_config(page_title="cora")


@st.cache_resource(show_spinner="Loading the assistant…")
def _real_app() -> App:
    return build(Config.from_env())


main(_real_app)
