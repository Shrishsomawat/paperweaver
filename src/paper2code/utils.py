from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def extract_arxiv_id(arxiv_url: str) -> str:
    parsed = urlparse(arxiv_url)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        raise ValueError(f"Invalid arXiv URL: {arxiv_url}")
    return parts[-1].replace(".pdf", "")


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_")


def extract_section(text: str, start_keywords: list[str], end_keywords: list[str]) -> str:
    lowered = text.lower()
    start_index = 0
    end_index = len(text)

    for keyword in start_keywords:
        idx = lowered.find(keyword.lower())
        if idx != -1:
            start_index = idx
            break

    for keyword in end_keywords:
        idx = lowered.find(keyword.lower(), start_index + 1)
        if idx != -1:
            end_index = idx
            break

    return text[start_index:end_index].strip()


def find_caption(blocks: list[tuple[Any, ...]], image_index: int) -> str:
    window = blocks[max(0, image_index - 2) : image_index + 3]
    for block in window:
        text = str(block[4]).strip()
        if re.match(r"^(figure|fig\.)\s*\d+", text, flags=re.IGNORECASE):
            return text
    for block in window:
        text = str(block[4]).strip()
        if any(token in text.lower() for token in ["architecture", "framework", "pipeline"]):
            return text
    return ""


def parse_arxiv_metadata(xml_text: str) -> dict[str, Any]:
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    entry = root.find("atom:entry", namespace)
    if entry is None:
        raise ValueError("No entry found in arXiv metadata response")

    title = entry.findtext("atom:title", default="", namespaces=namespace)
    summary = entry.findtext("atom:summary", default="", namespaces=namespace)
    authors = [
        clean_xml_text(author.text or "")
        for author in entry.findall("atom:author/atom:name", namespace)
        if author.text
    ]
    return {
        "title": clean_xml_text(title or "Unknown Title"),
        "abstract": clean_xml_text(summary),
        "authors": authors,
    }


def clean_xml_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_json_list(raw: str) -> list[dict[str, Any]]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    if not cleaned.startswith("["):
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

    parsed = json.loads(cleaned)
    if not isinstance(parsed, list):
        raise ValueError("Expected JSON list")
    return parsed


def extract_issues(review_text: str) -> list[str]:
    lines = [line.strip() for line in review_text.splitlines()]
    issues: list[str] = []
    in_issues = False
    for line in lines:
        upper = line.upper()
        if upper.startswith("ISSUES"):
            in_issues = True
            continue
        if upper.startswith("SUGGESTIONS"):
            break
        if in_issues and line.startswith("-"):
            issues.append(line[1:].strip())
    return issues


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
