from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

import fitz
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from paper2code.config import Settings
from paper2code.storage import RunStorage
from paper2code.utils import extract_arxiv_id, find_caption, parse_arxiv_metadata, sanitize_filename

logger = logging.getLogger(__name__)


class PaperService:
    def __init__(self, settings: Settings, storage: RunStorage) -> None:
        self.settings = settings
        self.storage = storage

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def fetch_pdf(self, arxiv_url: str) -> tuple[str, bytes]:
        arxiv_id = extract_arxiv_id(arxiv_url)
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        with httpx.Client(timeout=self.settings.request_timeout_seconds, follow_redirects=True) as client:
            response = client.get(pdf_url)
            response.raise_for_status()
        return arxiv_id, response.content

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def fetch_metadata(self, arxiv_id: str) -> dict[str, Any]:
        meta_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
        with httpx.Client(timeout=self.settings.request_timeout_seconds, follow_redirects=True) as client:
            response = client.get(meta_url)
            response.raise_for_status()
        metadata = parse_arxiv_metadata(response.text)
        metadata["arxiv_id"] = arxiv_id
        return metadata

    def parse_pdf(self, pdf_bytes: bytes) -> tuple[str, list[dict[str, Any]]]:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        raw_text_parts: list[str] = []
        figures: list[dict[str, Any]] = []

        for page_num, page in enumerate(doc):
            raw_text_parts.append(page.get_text())
            blocks = page.get_text("blocks")
            for image_index, image_info in enumerate(page.get_images(full=True)):
                xref = image_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                figures.append(
                    {
                        "page": page_num + 1,
                        "base64": base64.b64encode(image_bytes).decode("utf-8"),
                        "ext": base_image.get("ext", "png"),
                        "caption": find_caption(blocks, image_index),
                    }
                )

        return "\n".join(raw_text_parts), figures

    def persist_source_artifacts(
        self,
        *,
        run_dir: Path,
        arxiv_id: str,
        pdf_bytes: bytes,
        metadata: dict[str, Any],
        raw_text: str,
        figures: list[dict[str, Any]],
    ) -> None:
        source_dir = run_dir / "source"
        pdf_path = source_dir / f"{sanitize_filename(arxiv_id)}.pdf"
        self.storage.write_bytes(pdf_path, pdf_bytes)
        self.storage.write_json(source_dir / "metadata.json", metadata)
        self.storage.write_text(source_dir / "paper.txt", raw_text)
        self.storage.write_json(source_dir / "figures.json", figures)
        logger.info("Persisted source artifacts to %s", source_dir)
