import a_package_that_is_not_installed  # noqa: F401  # ty: ignore[unresolved-import]

from fixture_plugins import make_plugin

PLUGIN = make_plugin()
