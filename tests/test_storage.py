from pathlib import Path

from paper2code.config import Settings
from paper2code.storage import RunStorage


def test_create_run_dir(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", output_dir=tmp_path / "runs")
    storage = RunStorage(settings)
    run_id, run_dir = storage.create_run_dir("1706.03762")
    assert "1706.03762" in run_id
    assert run_dir.exists()
