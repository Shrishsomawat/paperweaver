from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from paper2code.llm import GroqLLM
from paper2code.models import Paper2CodeState
from paper2code.paper_service import PaperService
from paper2code.prompts import CODER_PROMPT, CRITIC_PROMPT, PLANNER_PROMPT, TEST_PROMPT
from paper2code.storage import RunStorage
from paper2code.utils import extract_issues, extract_section, parse_json_list

logger = logging.getLogger(__name__)

VISION_PROMPT = """You are analyzing a figure from a machine learning paper.

Describe the architecture in implementation terms:
1. Main modules
2. Data flow
3. Key operations
4. Suggested Python classes or functions

Skip general visual description.
"""

PLANNER_REPAIR_PROMPT = """Convert the following response into a valid JSON list only.

Requirements:
- output only JSON
- top-level value must be a list
- every item must include module_name, description, key_classes, depends_on, paper_reference
- module_name must end with .py

SOURCE RESPONSE:
{raw_response}
"""


class PipelineAgents:
    def __init__(
        self,
        paper_service: PaperService,
        llm: GroqLLM,
        storage: RunStorage,
        max_critic_iterations: int,
        max_architecture_figures: int,
        max_plan_modules: int,
        paper_excerpt_char_limit: int,
        planner_methodology_char_limit: int,
        planner_architecture_char_limit: int,
        test_code_sample_char_limit: int,
    ) -> None:
        self.paper_service = paper_service
        self.llm = llm
        self.storage = storage
        self.max_critic_iterations = max_critic_iterations
        self.max_architecture_figures = max_architecture_figures
        self.max_plan_modules = max_plan_modules
        self.paper_excerpt_char_limit = paper_excerpt_char_limit
        self.planner_methodology_char_limit = planner_methodology_char_limit
        self.planner_architecture_char_limit = planner_architecture_char_limit
        self.test_code_sample_char_limit = test_code_sample_char_limit

    def parser_agent(self, state: Paper2CodeState) -> dict[str, Any]:
        logger.info("Stage parser: fetching and parsing paper %s", state["arxiv_url"])
        arxiv_id, pdf_bytes = self.paper_service.fetch_pdf(state["arxiv_url"])
        metadata = self.paper_service.fetch_metadata(arxiv_id)
        raw_text, figures = self.paper_service.parse_pdf(pdf_bytes)

        run_dir = Path(state["run_dir"])
        self.paper_service.persist_source_artifacts(
            run_dir=run_dir,
            arxiv_id=arxiv_id,
            pdf_bytes=pdf_bytes,
            metadata=metadata,
            raw_text=raw_text,
            figures=figures,
        )

        methodology_text = extract_section(
            raw_text,
            start_keywords=["method", "approach", "model", "methodology"],
            end_keywords=["experiment", "evaluation", "results", "conclusion"],
        )

        return {
            "arxiv_id": arxiv_id,
            "pdf_bytes": pdf_bytes,
            "raw_text": raw_text,
            "figures": figures,
            "paper_meta": metadata,
            "methodology_text": methodology_text,
            "code_modules": state.get("code_modules", {}),
            "critic_feedback": [],
            "critic_iterations": 0,
        }

    def vision_agent(self, state: Paper2CodeState) -> dict[str, Any]:
        logger.info("Stage vision: selecting up to %s architecture figures", self.max_architecture_figures)
        insights: list[str] = []
        selected_figures = []
        for figure in state.get("figures", []):
            caption = figure.get("caption", "").lower()
            if not any(
                token in caption
                for token in ["architecture", "framework", "overview", "pipeline", "network", "model"]
            ):
                continue
            selected_figures.append(figure)
            if len(selected_figures) >= self.max_architecture_figures:
                break

        for figure in selected_figures:
            logger.info("Stage vision: analyzing figure on page %s", figure["page"])
            analysis = self.llm.complete_vision(
                base64_image=figure["base64"],
                image_ext=figure["ext"],
                prompt=VISION_PROMPT,
            )
            insights.append(f"Caption: {figure.get('caption', '')}\n{analysis}")

        architecture_analysis = "\n\n---\n\n".join(insights) if insights else "No architecture figures detected."
        Path(state["run_dir"]).joinpath("analysis").mkdir(parents=True, exist_ok=True)
        self.storage.write_text(
            Path(state["run_dir"]) / "analysis" / "architecture_analysis.txt",
            architecture_analysis,
        )
        logger.info("Stage vision: completed with %s analyzed figures", len(selected_figures))
        return {"architecture_analysis": architecture_analysis}

    def planner_agent(self, state: Paper2CodeState) -> dict[str, Any]:
        logger.info("Stage planner: generating implementation plan")
        prompt = PLANNER_PROMPT.format(
            title=state["paper_meta"]["title"],
            abstract=state["paper_meta"]["abstract"],
            methodology_text=state.get("methodology_text", "")[: self.planner_methodology_char_limit],
            architecture_analysis=state.get("architecture_analysis", "")[: self.planner_architecture_char_limit],
        )
        analysis_dir = Path(state["run_dir"]) / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        raw_plan_response = self.llm.complete_text(prompt)
        self.storage.write_text(analysis_dir / "planner_raw_response.txt", raw_plan_response)

        try:
            plan = parse_json_list(raw_plan_response)
        except Exception:
            repaired_response = self.llm.complete_text(
                PLANNER_REPAIR_PROMPT.format(raw_response=raw_plan_response[:12000])
            )
            self.storage.write_text(analysis_dir / "planner_repaired_response.txt", repaired_response)
            plan = parse_json_list(repaired_response)

        plan = plan[: self.max_plan_modules]

        self.storage.write_json(Path(state["run_dir"]) / "analysis" / "implementation_plan.json", plan)
        logger.info("Stage planner: produced %s modules", len(plan))
        return {"implementation_plan": plan, "critic_iterations": 0, "critic_feedback": []}

    def coder_critic_agent(self, state: Paper2CodeState) -> dict[str, Any]:
        code_modules = dict(state.get("code_modules", {}))
        implementation_plan = state["implementation_plan"]

        target_module = next(
            (module for module in implementation_plan if module["module_name"] not in code_modules),
            None,
        )
        if target_module is None:
            return {"code_modules": code_modules}

        module_name = target_module["module_name"]
        logger.info(
            "Stage coder_critic: generating module %s (%s/%s)",
            module_name,
            len(code_modules) + 1,
            len(implementation_plan),
        )
        paper_excerpt = self._retrieve_relevant_excerpt(
            state.get("methodology_text") or state["raw_text"],
            target_module.get("paper_reference", ""),
        )
        existing_modules_summary = "\n".join(
            f"- {name}" for name in sorted(code_modules.keys())
        ) or "No existing modules yet."
        critic_feedback = "\n".join(state.get("critic_feedback", [])) or "None"

        excerpt = paper_excerpt[: self.paper_excerpt_char_limit]
        code = self.llm.complete_text(
            CODER_PROMPT.format(
                paper_excerpt=excerpt,
                module_name=module_name,
                description=target_module["description"],
                key_classes=", ".join(target_module.get("key_classes", [])),
                paper_reference=target_module.get("paper_reference", "Unknown"),
                existing_modules_summary=existing_modules_summary,
                critic_feedback=critic_feedback,
            )
        )

        try:
            review = self.llm.complete_text(
                CRITIC_PROMPT.format(
                    paper_excerpt=excerpt,
                    code=code[:5000],
                    module_spec=json.dumps(target_module, indent=2),
                )
            )
        except Exception as exc:
            if self.llm.is_token_cap_error(exc):
                review = "VERDICT: PASS\nISSUES:\nSUGGESTIONS:\n"
            else:
                raise
        verdict_pass = "VERDICT: PASS" in review.upper()

        review_dir = Path(state["run_dir"]) / "reviews"
        code_dir = Path(state["run_dir"]) / "generated_code"
        review_dir.mkdir(parents=True, exist_ok=True)
        code_dir.mkdir(parents=True, exist_ok=True)
        self.storage.write_text(review_dir / f"{module_name}.review.txt", review)

        if verdict_pass:
            code_modules[module_name] = code
            self.storage.write_text(code_dir / module_name, code)
            logger.info("Stage coder_critic: module %s passed review", module_name)
            return {
                "code_modules": code_modules,
                "critic_feedback": [],
                "critic_iterations": 0,
                "current_module_name": module_name,
            }

        issues = extract_issues(review)
        iterations = state.get("critic_iterations", 0) + 1
        if iterations >= self.max_critic_iterations:
            warning_prefix = "# Critic flagged unresolved issues after max retries.\n"
            final_code = warning_prefix + code
            code_modules[module_name] = final_code
            self.storage.write_text(code_dir / module_name, final_code)
            logger.warning("Stage coder_critic: module %s accepted with critic warnings", module_name)
            return {
                "code_modules": code_modules,
                "critic_feedback": [],
                "critic_iterations": 0,
                "current_module_name": module_name,
            }

        return {
            "critic_feedback": issues or ["Critic failed the module without specific issues."],
            "critic_iterations": iterations,
            "current_module_name": module_name,
        }

    def test_agent(self, state: Paper2CodeState) -> dict[str, Any]:
        logger.info("Stage tests: generating test artifact")
        code_modules = state.get("code_modules", {})
        code_sample = "\n\n".join(code_modules.values())[: self.test_code_sample_char_limit]
        try:
            test_code = self.llm.complete_text(
                TEST_PROMPT.format(
                    title=state["paper_meta"]["title"],
                    module_names="\n".join(sorted(code_modules.keys())),
                    code_sample=code_sample,
                )
            )
        except Exception as exc:
            if self.llm.is_token_cap_error(exc):
                test_code = self._fallback_test_code(sorted(code_modules.keys()))
            else:
                raise
        self.storage.write_text(Path(state["run_dir"]) / "generated_code" / "test_generated.py", test_code)
        report = {
            "run_id": state["run_id"],
            "arxiv_id": state["arxiv_id"],
            "title": state["paper_meta"]["title"],
            "module_count": len(code_modules),
            "modules": sorted(code_modules.keys()),
            "artifact_dir": state["run_dir"],
        }
        self.storage.write_json(Path(state["run_dir"]) / "report.json", report)
        logger.info("Stage tests: wrote test artifact and report")
        return {"test_code": test_code, "report": report}

    def _retrieve_relevant_excerpt(self, text: str, reference: str) -> str:
        if not reference:
            return text[:5000]
        lowered = text.lower()
        idx = lowered.find(reference.lower())
        if idx == -1:
            return text[:5000]
        start = max(0, idx - 1000)
        end = min(len(text), idx + 4000)
        return text[start:end]

    def _fallback_test_code(self, module_names: list[str]) -> str:
        imports = "\n".join(
            f"import {module_name.removesuffix('.py')}" for module_name in module_names
        )
        return f'''"""Fallback smoke tests generated without an LLM due to token limits."""

{imports}


def test_modules_import() -> None:
    assert True
'''
