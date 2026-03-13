# Paper2Code

Paper2Code is a production-style LangGraph pipeline that turns an arXiv paper into a structured implementation workspace. It fetches the paper, extracts text and figures, analyzes architecture diagrams with a vision model, plans code modules, runs a lightweight coder-critic loop, and writes artifacts into the local `data/` directory.

## Features

- Typed shared state for a 6-stage multi-agent pipeline
- Robust PDF parsing with PyMuPDF
- Figure filtering and vision analysis for architecture diagrams
- Planner and coder-critic loops with configurable retry caps
- Persistent local run artifacts in the folder you selected
- CLI and FastAPI entrypoints
- Basic tests for core utilities and storage
- Free-tier-friendly defaults for Groq

## Project Layout

- `src/paper2code/`: application package
- `data/inputs/`: downloaded source PDFs and extracted metadata
- `data/runs/`: per-run artifacts including code, plans, and reports
- `tests/`: automated tests

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
copy .env.example .env
```

Set `PAPER2CODE_GROQ_API_KEY` in `.env`.

Use Python 3.11-3.13 for the most stable LangGraph compatibility.
If Groq free-tier rate limits are slowing runs down, increase `PAPER2CODE_MIN_LLM_REQUEST_INTERVAL_SECONDS`.
The default configuration is tuned for Groq's free tier by using a smaller text model, fewer critic retries, one architecture figure, and at most four planned modules.

## Run the CLI

```bash
paper2code run https://arxiv.org/abs/1706.03762
```

This writes artifacts to `data/runs/<run_id>/`, creates `artifacts.zip`, and opens the run folder on Windows by default.

To skip auto-opening the folder:

```bash
paper2code run --no-open https://arxiv.org/abs/1706.03762
```

## Run the API

```bash
uvicorn paper2code.api:app --reload
```

POST to `/runs` with:

```json
{
  "arxiv_url": "https://arxiv.org/abs/1706.03762"
}
```

## Run the Streamlit UI

```bash
streamlit run src/paper2code/ui.py
```

The UI lets you launch a run, inspect the report and plan, browse generated code, and download the zipped artifacts.

## Notes

- The LLM-backed stages require a valid Groq-compatible API key.
- The generated code and tests are best treated as a starting point for engineering review.
