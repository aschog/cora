"""The site's description, read off `README.md` rather than written into `mkdocs.yml`.

What cora is, the front door says once. `site_description` is the copy of it every
built page carries in its head, and a YAML file cannot read a Markdown one — so this
hook, which MkDocs runs before the build, takes README's opening sentence and sets it.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"


def _opening_sentence() -> str:
    """The first sentence of the paragraph `README.md` opens with, unwrapped."""
    marked = README.read_text().split("[start:what-cora-is] -->", 1)[1]
    paragraph = marked.split("<!--", 1)[0]
    return " ".join(paragraph.split()).split(". ")[0]


def on_config(config):
    config["site_description"] = _opening_sentence()
    return config
