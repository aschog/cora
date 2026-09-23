from cora.domain.errors import CoreError, PluginLoadError


def test_base_error_exposes_user_presentable_message() -> None:
    error = CoreError("Something went wrong. Please try again.")

    assert error.user_message == "Something went wrong. Please try again."


def test_plugin_load_error_names_plugin_and_reason() -> None:
    error = PluginLoadError("fitness", "the plugin module could not be imported")

    assert issubclass(PluginLoadError, CoreError)
    assert "fitness" in error.user_message
    assert "could not be imported" in error.user_message


def test_an_error_names_no_step_until_a_step_is_named() -> None:
    assert CoreError("Something went wrong. Please try again.").step == ""
