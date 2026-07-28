from contextlib import suppress

from playwright.sync_api import Locator, Page, expect

# No data-testid is documented by Streamlit and they do churn — stFileUploaderFile*
# became stFileChip* in 1.60 — so every one the suite depends on is named here and
# nowhere else. A Streamlit upgrade is this file to fix.
APP = "stApp"
CHAT_INPUT = "stChatInputTextArea"
CHAT_MESSAGE = "stChatMessage"
EXCEPTION = "stException"
EXPANDER = "stExpander"
FILE_CHIP_NAME = "stFileChipName"
FILE_UPLOAD_INPUT = "stFileUploaderDropzoneInput"
SIDEBAR = "stSidebar"

SCRIPT_STATE = "data-test-script-state"
RERUN_TIMEOUT = 60_000


def wait_for_rerun(page: Page, *, timeout: float = RERUN_TIMEOUT) -> None:
    """Waits for `running` and only then `notRunning`. Waiting for `notRunning`
    alone can pass stalely inside the ~30ms window before Streamlit marks the
    rerun started. A rerun can also finish too fast to be caught mid-flight, so a
    missed `running` is tolerated rather than fatal — the assertions that follow
    are `expect()` calls, which retry, and they are the real barrier."""
    app = page.get_by_test_id(APP)
    with suppress(AssertionError):
        expect(app).to_have_attribute(SCRIPT_STATE, "running", timeout=2_000)
    expect(app).to_have_attribute(SCRIPT_STATE, "notRunning", timeout=timeout)


def ask(page: Page, question: str) -> None:
    page.get_by_test_id(CHAT_INPUT).fill(question)
    page.get_by_test_id(CHAT_INPUT).press("Enter")
    wait_for_rerun(page)


def upload(page: Page, name: str, data: bytes, mime: str = "text/markdown") -> None:
    """set_input_files runs no actionability checks, so it works even when the
    sidebar is collapsed — unlike clicking the dropzone."""
    page.get_by_test_id(FILE_UPLOAD_INPUT).set_input_files(
        files=[{"name": name, "mimeType": mime, "buffer": data}]
    )
    wait_for_rerun(page)


def messages(page: Page) -> Locator:
    return page.get_by_test_id(CHAT_MESSAGE)


def expander(page: Page, label: str) -> Locator:
    return page.get_by_test_id(EXPANDER).filter(has_text=label)
