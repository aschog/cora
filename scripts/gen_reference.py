from pathlib import Path, PurePosixPath

import mkdocs_gen_files

RENDERED = ("domain", "ports", "engine", "app")
SRC = Path(__file__).parent.parent / "src"


def reference_pages(src: Path) -> list[tuple[tuple[str, ...], PurePosixPath]]:
    found = []
    # Sorted, because mkdocs infers the nav in path order: writing the landing page in
    # any other order would show the reader two orders for one list.
    for package in sorted(RENDERED):
        for module in sorted((src / "cora" / package).rglob("*.py")):
            parts = module.relative_to(src).with_suffix("").parts
            if parts[-1] == "__init__":
                parts = parts[:-1]
            # Every part below `cora`, because the walk is recursive: a module inside a
            # private package is private too, however public its own name.
            if any(part.startswith("_") for part in parts[1:]):
                continue
            found.append((parts, PurePosixPath("api", *parts, "index.md")))
    return found


def write(src: Path) -> None:
    listed = []
    for parts, page in reference_pages(src):
        dotted = ".".join(parts)
        listed.append(f"- [`{dotted}`]({page.relative_to('api')})")
        with mkdocs_gen_files.open(page, "w") as out:
            # Front matter, not a heading: mkdocs takes a page's title from the filename
            # long before mkdocstrings renders one, so without this every page of the
            # reference is titled `Index` in the nav, the tab and the search results.
            print(f"---\ntitle: {dotted}\n---\n", file=out)
            print(f"::: {dotted}", file=out)
    with mkdocs_gen_files.open("api/index.md", "w") as out:
        print("# The modules\n", file=out)
        print("One page per module of the four packages that anything", file=out)
        print("outside the app imports.\n", file=out)
        print("\n".join(listed), file=out)


# mkdocs-gen-files runs this file through runpy, which names it `<run_path>`. A test
# importing it for `reference_pages` must not write into a build that is not running.
if __name__ == "<run_path>":
    write(SRC)
