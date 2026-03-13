from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from paper2code.config import get_settings
from paper2code.logging_utils import configure_logging
from paper2code.service import Paper2CodeService


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    service = Paper2CodeService(settings)

    st.set_page_config(page_title="Paper2Code", page_icon="P", layout="wide")
    st.title("Paper2Code")
    st.caption("Turn an arXiv paper into a local implementation workspace.")

    arxiv_url = st.text_input(
        "arXiv URL",
        value="https://arxiv.org/abs/1706.03762",
        help="Example: https://arxiv.org/abs/1706.03762",
    )

    if st.button("Run Pipeline", type="primary", use_container_width=True):
        with st.status("Running pipeline...", expanded=True) as status:
            st.write("Fetching paper, planning modules, generating code, and exporting artifacts.")
            try:
                result = service.run(arxiv_url)
            except Exception as exc:
                status.update(label="Run failed", state="error")
                st.exception(exc)
                return
            status.update(label="Run completed", state="complete")

        st.subheader("Run Result")
        st.json(result)

        run_dir = Path(result["run_dir"])
        report_path = run_dir / "report.json"
        zip_path = Path(result.get("zip_path", ""))
        plan_path = run_dir / "analysis" / "implementation_plan.json"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Modules", len(result.get("modules", [])))
        with col2:
            st.metric("Run ID", result.get("run_id", ""))
        with col3:
            st.metric("Artifacts", "Ready")

        if report_path.exists():
            st.subheader("Report")
            st.json(json.loads(report_path.read_text(encoding="utf-8")))

        if plan_path.exists():
            st.subheader("Implementation Plan")
            st.json(json.loads(plan_path.read_text(encoding="utf-8")))

        code_dir = run_dir / "generated_code"
        if code_dir.exists():
            st.subheader("Generated Code")
            for code_file in sorted(code_dir.glob("*.py")):
                with st.expander(code_file.name, expanded=False):
                    st.code(code_file.read_text(encoding="utf-8"), language="python")

        if zip_path.exists():
            st.download_button(
                "Download Artifacts ZIP",
                data=zip_path.read_bytes(),
                file_name=zip_path.name,
                mime="application/zip",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
