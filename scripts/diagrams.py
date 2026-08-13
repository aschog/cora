import pathlib

import package_diagram
import turn_diagram

PAGE = pathlib.Path(__file__).resolve().parent.parent / "docs" / "diagrams.md"
SOURCES = (package_diagram, turn_diagram)


def page() -> str:
    sections = [
        f"## {source.HEADING}\n\n```mermaid\n{source.render()}\n```"
        for source in SOURCES
    ]
    return "\n\n".join(["# Diagrams", *sections]) + "\n"


if __name__ == "__main__":
    PAGE.write_text(page())
