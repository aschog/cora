from contextlib import suppress

from playwright.sync_api import Locator, Page, expect

# No data-testid is documented by Streamlit and they do churn — stFileUploaderFile*
# became stFileChip* in 1.60 — so every one the suite depends on is named here and
# nowhere else. A Streamlit upgrade is this file to fix.
APP = "stApp"
CHAT_INPUT = "stChatInputTextArea"
CHAT_MESSAGE = "stChatMessage"
EXCEPTION = "stException"
ALERT_ERROR = "stAlertContentError"
ALERT_INFO = "stAlertContentInfo"
ALERT_SUCCESS = "stAlertContentSuccess"
EXPANDER = "stExpander"
EXPANDER_DETAILS = "stExpanderDetails"
FILE_CHIP_DELETE = "stFileChipDeleteBtn"
FILE_CHIP_NAME = "stFileChipName"
FILE_UPLOAD_INPUT = "stFileUploaderDropzoneInput"
MARKDOWN = "stMarkdown"
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


def sources(page: Page) -> Locator:
    """The sidebar's document list. Scoping to markdown blocks is exact: the ingest
    alert is an stAlert, not an stMarkdown, so it cannot be mistaken for a source."""
    return page.get_by_test_id(SIDEBAR).get_by_test_id(MARKDOWN)


def expander(page: Page, label: str) -> Locator:
    return page.get_by_test_id(EXPANDER).filter(has_text=label)


def open_expander(page: Page, label: str) -> Locator:
    """Streamlit expanders start collapsed, and collapsed content reads as empty
    text, so a spec must open one before asserting on what it holds."""
    panel = expander(page, label)
    panel.get_by_text(label).click()
    details = panel.get_by_test_id(EXPANDER_DETAILS)
    expect(details).to_be_visible()
    return details


def messages(page: Page) -> Locator:
    return page.get_by_test_id(CHAT_MESSAGE)
