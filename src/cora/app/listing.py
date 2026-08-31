"""What cora loaded, as a terminal reads it.

Rendered over the app the deployment configured, so what prints is what loaded rather
than what a reader of the manifests would guess. The page reads the same listing over
HTTP — one projection of the registrations, two renderings of it.
"""

from cora.ports.host import Listed

NOTHING = "No plugin is loaded. cora answers as itself."
SYSTEM_WIDE = "system-wide"
"""What a registration carrying no scope is shown as. Spelt out rather than left blank,
because a claim on every turn is a visible act and not a quiet field."""

INDENT = "  "
KIND_WIDTH = 14
NAME_WIDTH = 24


def rendered(plugins: tuple[Listed, ...]) -> str:
    """Every plugin under its source, and every registration under its plugin.

    One line per registration, of one shape whatever kind it is: a fifth kind of
    contribution prints without this being rewritten.
    """
    if not plugins:
        return NOTHING
    return "\n\n".join(_one(plugin) for plugin in plugins)


def _one(plugin: Listed) -> str:
    lines = [f"{plugin.name} — {plugin.source}"]
    lines.extend(
        f"{INDENT}{each.kind:<{KIND_WIDTH}}{each.name:<{NAME_WIDTH}}"
        f"{each.scope or SYSTEM_WIDE}"
        for each in plugin.contributions
    )
    if not plugin.contributions:
        lines.append(f"{INDENT}registers nothing")
    return "\n".join(lines)


def main() -> None:
    """Print the listing for the app this environment describes.

    Raises:
        CoreError: The deployment cannot be assembled — a missing key, or a plugin cora
            will not have. The refusal is the answer, and it names what is wrong.
    """
    from cora.app.assembly import build
    from cora.app.config import Config

    print(rendered(build(Config.from_env()).plugins))


if __name__ == "__main__":
    main()
