from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from openai import RateLimitError

from paper2code.agents import PipelineAgents
from paper2code.config import Settings
from paper2code.graph import build_graph
from paper2code.llm import GroqLLM
from paper2code.paper_service import PaperService
from paper2code.storage import RunStorage
from paper2code.utils import extract_arxiv_id


class Paper2CodeService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage = RunStorage(settings)
        self.paper_service = PaperService(settings, self.storage)
        self.llm = GroqLLM(settings)
        self.agents = PipelineAgents(
            self.paper_service,
            self.llm,
            self.storage,
            max_critic_iterations=settings.max_critic_iterations,
            max_architecture_figures=settings.max_architecture_figures,
            max_plan_modules=settings.max_plan_modules,
            paper_excerpt_char_limit=settings.paper_excerpt_char_limit,
            planner_methodology_char_limit=settings.planner_methodology_char_limit,
            planner_architecture_char_limit=settings.planner_architecture_char_limit,
            test_code_sample_char_limit=settings.test_code_sample_char_limit,
        )
        self.graph = build_graph(self.agents)

    def run(self, arxiv_url: str) -> dict[str, Any]:
        arxiv_id = extract_arxiv_id(arxiv_url)
        run_id, run_dir = self.storage.create_run_dir(arxiv_id)
        initial_state = {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "arxiv_url": arxiv_url,
            "code_modules": {},
            "critic_feedback": [],
            "critic_iterations": 0,
            "messages": [],
        }
        try:
            result = self.graph.invoke(initial_state)
        except RateLimitError as exc:
            if self.llm.is_token_cap_error(exc):
                report = {
                    "run_id": run_id,
                    "arxiv_id": arxiv_id,
                    "title": "Run stopped due to Groq free-tier token cap",
                    "module_count": 0,
                    "modules": [],
                    "artifact_dir": str(run_dir),
                    "zip_path": str(self.storage.zip_directory(run_dir, run_dir / "artifacts.zip")),
                    "status": "partial",
                    "message": str(exc),
                }
                self.storage.write_json(run_dir / "report.json", report)
                return {
                    "run_id": run_id,
                    "run_dir": str(run_dir),
                    "report": report,
                    "modules": [],
                }
            raise
        zip_path = self.storage.zip_directory(run_dir, run_dir / "artifacts.zip")
        return {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "zip_path": str(zip_path),
            "report": result.get("report", {}),
            "modules": sorted(result.get("code_modules", {}).keys()),
        }

    def open_run_folder(self, run_dir: str) -> None:
        path = Path(run_dir)
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
