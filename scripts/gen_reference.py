from pathlib import Path, PurePosixPath

import mkdocs_gen_files

RENDERED = ("domain", "ports", "engine", "app")
SRC = Path(__file__).parent.parent / "src"


def reference_pages(src: Path) -> list[tuple[tuple[str, ...], PurePosixPath]]:
    found = []
    for package in RENDERED:
        for module in sorted((src / "cora" / package).rglob("*.py")):
            parts = module.relative_to(src).with_suffix("").parts
            if parts[-1] == "__init__":
                parts = parts[:-1]
            elif parts[-1].startswith("_"):
                continue
            found.append((parts, PurePosixPath("api", *parts, "index.md")))
    return found


def write(src: Path) -> None:
    nav = mkdocs_gen_files.Nav()
    for parts, page in reference_pages(src):
        nav[parts] = str(page.relative_to("api"))
        with mkdocs_gen_files.open(page, "w") as out:
            print(f"::: {'.'.join(parts)}", file=out)
    with mkdocs_gen_files.open("api/index.md", "w") as out:
        print("# Reference\n", file=out)
        out.writelines(nav.build_literate_nav())


# mkdocs-gen-files runs this file through runpy, which names it `<run_path>`. A test
# importing it for `reference_pages` must not write into a build that is not running.
if __name__ == "<run_path>":
    write(SRC)
