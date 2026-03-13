from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph import add_messages


class FigureData(TypedDict):
    page: int
    base64: str
    ext: str
    caption: str


class PlanModule(TypedDict):
    module_name: str
    description: str
    key_classes: list[str]
    depends_on: list[str]
    paper_reference: str


class Paper2CodeState(TypedDict, total=False):
    run_id: str
    arxiv_url: str
    arxiv_id: str
    pdf_bytes: bytes
    raw_text: str
    figures: list[FigureData]
    paper_meta: dict[str, Any]
    methodology_text: str
    architecture_analysis: str
    implementation_plan: list[PlanModule]
    code_modules: dict[str, str]
    critic_feedback: list[str]
    critic_iterations: int
    current_module_name: str
    test_code: str
    pr_url: str
    run_dir: str
    report: dict[str, Any]
    messages: Annotated[list[Any], add_messages]
