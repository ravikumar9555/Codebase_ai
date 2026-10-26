import pytest
from app.repo_ingest import parse_github_url, chunk_text

def test_parse_github_url():
    assert parse_github_url("https://github.com/fastapi/fastapi") == ("fastapi", "fastapi")

@pytest.mark.parametrize("url", [
    "http://github.com/owner/repo",
    "https://example.com/owner/repo",
    "https://github.com/",
])
def test_reject_invalid_urls(url):
    with pytest.raises(ValueError):
        parse_github_url(url)

def test_chunk_text_has_line_ranges():
    text = "\n".join(f"line {i}" for i in range(1, 25))
    chunks = chunk_text("sample.py", text)
    assert chunks
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] >= chunks[0]["start_line"]
    assert "line 1" in chunks[0]["content"]
