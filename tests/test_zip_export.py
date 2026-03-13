from pathlib import Path

from paper2code.config import Settings
from paper2code.storage import RunStorage


def test_zip_directory_creates_archive(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", output_dir=tmp_path / "runs")
    storage = RunStorage(settings)
    run_dir = tmp_path / "sample_run"
    run_dir.mkdir()
    (run_dir / "report.json").write_text("{}", encoding="utf-8")

    archive_path = storage.zip_directory(run_dir, run_dir / "artifacts.zip")

    assert archive_path.exists()
