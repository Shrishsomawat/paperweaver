from paper2code.utils import extract_arxiv_id, extract_issues, extract_section, parse_arxiv_metadata


def test_extract_arxiv_id_from_abs_url() -> None:
    assert extract_arxiv_id("https://arxiv.org/abs/1706.03762") == "1706.03762"


def test_extract_section_returns_slice() -> None:
    text = "Intro text Method details here Evaluation details later"
    section = extract_section(text, ["method"], ["evaluation"])
    assert "Method details here" in section
    assert "Evaluation" not in section


def test_extract_issues_parses_bullets() -> None:
    review = """VERDICT: FAIL
ISSUES:
- Wrong tensor shape
- Missing import
SUGGESTIONS:
- Fix shape
"""
    assert extract_issues(review) == ["Wrong tensor shape", "Missing import"]


def test_parse_arxiv_metadata_uses_entry_fields() -> None:
    xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>arXiv Query: search_query=&amp;id_list=1706.03762</title>
  <entry>
    <title>Attention Is All You Need</title>
    <summary>Neural machine translation without recurrence.</summary>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
  </entry>
</feed>
"""
    parsed = parse_arxiv_metadata(xml_text)
    assert parsed["title"] == "Attention Is All You Need"
    assert parsed["abstract"] == "Neural machine translation without recurrence."
    assert parsed["authors"] == ["Ashish Vaswani", "Noam Shazeer"]
