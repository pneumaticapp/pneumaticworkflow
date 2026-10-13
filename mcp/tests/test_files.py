from urllib.parse import quote

import pytest

from pneumatic_mcp.files import file_id_segment
from pneumatic_mcp.settings import Settings


@pytest.mark.parametrize(
    argnames="file_id",
    argvalues=[
        "NiihssB_Drawing (v2).odg",
        "Схема процесса 日本語.odg",
        "report..v2.pdf",
        " a spaced ID ",
        "é.pdf",
        "e\u0301.pdf",
        "🧪" * 512,
    ],
)
@pytest.mark.parametrize(argnames="suffix", argvalues=["", "/download-ticket"])
def test_file_endpoint__legacy_identity__preserved(file_id: str, suffix: str):

    # arrange
    settings = Settings(file_service_url="http://files/storage-prefix/")
    path = "/mcp/files/" + quote(string=file_id, safe="") + suffix
    expected = "http://files/storage-prefix" + path

    # act
    endpoint = settings.file_endpoint(path=path)

    # assert
    assert endpoint == expected


@pytest.mark.parametrize(
    argnames="file_id",
    argvalues=[
        "",
        "   ",
        ".",
        "..",
        "../secret",
        "folder/file",
        "folder\\file",
        "a?query",
        "a#fragment",
        "%2Fsecret",
        "percent%.pdf",
        "control\x00",
        "control\n",
        "control\x7f",
        "bidi\u202e",
        "line\u2028",
        "paragraph\u2029",
        "surrogate\ud800",
        "x" * 513,
        None,
        7,
        [],
    ],
)
def test_file_id_segment__unsafe_identity__rejected(file_id: object):

    # arrange
    message = "Expected a safe flat file ID"

    # act
    with pytest.raises(ValueError) as ex:
        file_id_segment(value=file_id)

    # assert
    assert str(ex.value) == message


@pytest.mark.parametrize(
    argnames="path",
    argvalues=[
        "/files/safe",
        "/mcp/files/",
        "/mcp/files/../secret",
        "/mcp/files/%2E%2E",
        "/mcp/files/a%2Fb",
        "/mcp/files/a%5Cb",
        "/mcp/files/a%3Fb",
        "/mcp/files/a%23b",
        "/mcp/files/%252e%252e",
        "/mcp/files/raw space",
        "/mcp/files/日本語",
        "/mcp/files/%61",
        "/mcp/files/%c3%a9",
        "/mcp/files/%FF",
        "/mcp/files/%00",
        "/mcp/files/safe?query",
        "/mcp/files/safe#fragment",
        "/mcp/files/safe/download-ticket/extra",
    ],
)
def test_file_endpoint__noncanonical_path__rejected(path: str):

    # arrange
    settings = Settings()
    if path == "/files/safe":
        message = "Expected a delegated file API path"
    elif path in {
        "/mcp/files/raw space",
        "/mcp/files/日本語",
        "/mcp/files/%61",
        "/mcp/files/%c3%a9",
    }:
        message = "Expected a canonical encoded file path"
    elif path == "/mcp/files/%FF":
        message = (
            "'utf-8' codec can't decode byte 0xff in position 0: "
            "invalid start byte"
        )
    else:
        message = "Expected a safe flat file ID"

    # act
    with pytest.raises(ValueError) as ex:
        settings.file_endpoint(path=path)

    # assert
    assert str(ex.value) == message
