from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from paper2code.config import Settings
from paper2code.utils import ensure_parent


class RunStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_run_dir(self, arxiv_id: str) -> tuple[str, Path]:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{arxiv_id}-{timestamp}-{uuid4().hex[:8]}"
        run_dir = self.settings.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_id, run_dir

    def write_bytes(self, path: Path, data: bytes) -> None:
        ensure_parent(path)
        path.write_bytes(data)

    def write_text(self, path: Path, data: str) -> None:
        ensure_parent(path)
        path.write_text(data, encoding="utf-8")

    def write_json(self, path: Path, data: object) -> None:
        ensure_parent(path)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")

    def zip_directory(self, source_dir: Path, destination_zip: Path) -> Path:
        ensure_parent(destination_zip)
        with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in source_dir.rglob("*"):
                if path == destination_zip:
                    continue
                if path.is_file():
                    archive.write(path, arcname=path.relative_to(source_dir))
        return destination_zip
