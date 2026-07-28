from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from app_page import (
    ALERT_INFO,
    ALERT_SUCCESS,
    FILE_CHIP_DELETE,
    FILE_CHIP_NAME,
    sources,
    upload,
    wait_for_rerun,
)

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180)]

SAMPLE = Path(__file__).parents[2] / "samples" / "training-plan.md"


def test_uploading_a_document_confirms_it_and_lists_it(app: Page) -> None:
    upload(app, SAMPLE.name, SAMPLE.read_bytes())

    expect(app.get_by_test_id(FILE_CHIP_NAME)).to_contain_text(SAMPLE.name)
    expect(app.get_by_test_id(ALERT_SUCCESS)).to_contain_text(f"Added {SAMPLE.name}")
    expect(sources(app).filter(has_text=SAMPLE.name)).to_have_count(1)


def test_re_uploading_the_same_document_reports_a_no_op(app: Page) -> None:
    upload(app, SAMPLE.name, SAMPLE.read_bytes())
    expect(app.get_by_test_id(ALERT_SUCCESS)).to_contain_text(f"Added {SAMPLE.name}")

    app.get_by_test_id(FILE_CHIP_DELETE).click()
    wait_for_rerun(app)
    upload(app, SAMPLE.name, SAMPLE.read_bytes())

    expect(app.get_by_test_id(ALERT_INFO)).to_contain_text("already in your knowledge")
