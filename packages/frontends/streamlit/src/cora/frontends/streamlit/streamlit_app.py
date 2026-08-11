import logging

import streamlit as st
from cora.app.assembly import App, build
from cora.app.config import Config
from cora.frontends.streamlit.chat import main

# Streamlit's source watcher probes every module for __path__, which trips
# transformers' lazy imports and logs a warning-level traceback per model
# (torchvision is not installed). Harmless, so keep that logger quiet.
logging.getLogger("streamlit.watcher.local_sources_watcher").setLevel(logging.ERROR)

st.set_page_config(page_title="cora")


@st.cache_resource(show_spinner="Loading the assistant…")
def _real_app() -> App:
    return build(Config.from_env())


main(_real_app)
