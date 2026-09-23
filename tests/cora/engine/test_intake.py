import pytest

from cora.domain.errors import UploadRefusedError
from cora.engine.events import UNCHECKED_UPLOAD
from cora.engine.intake import Intake
from cora.engine.plugin_set import Registry
from cora.ports.host import (
    HANDLER,
    UPLOADING,
    Extension,
    Handler,
    Registration,
    Subscription,
)
from fakes import FakeFiles, host_for

FIELD = "travel"
PDF = b"%PDF-1.7 maples"


def _subscribed(handle: Handler, scope: str | None = None) -> Registry:
    return Registry(
        (
            Registration(
                module="indexer",
                kind=HANDLER,
                value=Subscription(event=UPLOADING, handle=handle),
                scope=scope,
            ),
        )
    )


def test_an_upload_nobody_hears_is_still_a_file_of_the_field() -> None:
    files = FakeFiles()

    Intake(files=files, registry=Registry()).take(FIELD, "kyoto.pdf", PDF)

    assert files.read_bytes(FIELD, "kyoto.pdf") == PDF
    assert files.names("fitness") == ()


def test_a_handler_is_handed_the_name_and_reads_the_fields_bytes() -> None:
    files = FakeFiles()
    host = host_for("indexer", files=files)
    heard: list[tuple[str, bytes | None]] = []

    def index(name: str) -> None:
        heard.append((name, host.files.read_bytes(name)))

    Intake(files=files, registry=_subscribed(index)).take(FIELD, "kyoto.pdf", PDF)

    assert heard == [("kyoto.pdf", PDF)]


def test_a_sentence_from_a_handler_refuses_the_upload_and_drops_the_file() -> None:
    files = FakeFiles()
    refusing = _subscribed(lambda name: f"cora does not read '{name}'")

    with pytest.raises(UploadRefusedError) as refused:
        Intake(files=files, registry=refusing).take(FIELD, "kyoto.xyz", PDF)

    assert refused.value.user_message == "cora does not read 'kyoto.xyz'"
    assert files.names(FIELD) == ()


def _breaks(name: str) -> None:
    raise RuntimeError("the key is hunter2")


def test_a_handler_that_breaks_refuses_on_coras_wording_and_drops_the_file() -> None:
    files = FakeFiles()

    with pytest.raises(UploadRefusedError) as refused:
        Intake(files=files, registry=_subscribed(_breaks)).take(FIELD, "k.pdf", PDF)

    assert refused.value.user_message == UNCHECKED_UPLOAD
    assert "hunter2" not in refused.value.user_message
    assert files.names(FIELD) == ()


def test_a_handler_under_another_field_does_not_hear_it() -> None:
    files = FakeFiles()
    heard: list[str] = []
    elsewhere = _subscribed(lambda name: heard.append(name), scope="fitness")

    Intake(files=files, registry=elsewhere).take(FIELD, "kyoto.pdf", PDF)

    assert heard == []
    assert files.read_bytes(FIELD, "kyoto.pdf") == PDF


def test_the_listing_shows_an_upload_handler_under_the_events_name() -> None:
    def extend(cora) -> None:
        cora.register_handler(event=UPLOADING, handle=lambda name: None)

    host = host_for("indexer")
    extend(host)

    [listed] = Registry(tuple(host.registered)).listing(
        (Extension(module="indexer", extend=extend),)
    )
    [contributed] = listed.contributions
    assert (contributed.kind, contributed.name, contributed.scope) == (
        HANDLER,
        UPLOADING,
        None,
    )


def test_a_refused_upload_leaves_the_file_that_was_already_there() -> None:
    files = FakeFiles({(FIELD, "plan.md"): "squats on Tuesday"})
    refusing = _subscribed(lambda name: f"cora does not read '{name}'")

    with pytest.raises(UploadRefusedError):
        Intake(files=files, registry=refusing).take(FIELD, "plan.md", PDF)

    assert files.read(FIELD, "plan.md") == "squats on Tuesday"


def test_a_refused_upload_of_a_new_name_leaves_nothing_behind() -> None:
    files = FakeFiles({(FIELD, "plan.md"): "squats on Tuesday"})
    refusing = _subscribed(lambda name: "no")

    with pytest.raises(UploadRefusedError):
        Intake(files=files, registry=refusing).take(FIELD, "kyoto.pdf", PDF)

    assert files.names(FIELD) == ("plan.md",)


def test_a_name_the_field_could_not_keep_is_made_into_one_it_can() -> None:
    files = FakeFiles()

    Intake(files=files).take(FIELD, "report (final), v2.pdf", PDF)

    assert files.names(FIELD) == ("report final v2.pdf",)
    assert files.read_bytes(FIELD, "report final v2.pdf") == PDF


def test_the_handler_is_handed_the_name_the_field_kept() -> None:
    files = FakeFiles()
    heard: list[str] = []

    Intake(files=files, registry=_subscribed(heard.append)).take(
        FIELD, "_draft (1).md", b"x"
    )

    assert heard == ["draft 1.md"]
    assert files.names(FIELD) == ("draft 1.md",)


def test_the_intake_answers_with_the_name_the_field_kept() -> None:
    files = FakeFiles()

    kept = Intake(files=files).take(FIELD, "report (final).pdf", PDF)

    assert kept == "report final.pdf"
    assert files.names(FIELD) == (kept,)
