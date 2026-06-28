# TVM Solver Agent 📐

A Streamlit-based financial mathematics assistant for Time Value of Money questions. It combines a chat UI with an orchestrator, a TVM specialist subagent, and deterministic math tools for reliable FM calculations.

## Project structure

- [app.py](app.py) — Streamlit app entry point
- [streamlit_app.py](streamlit_app.py) — alternate entry point for Streamlit Cloud
- [agents/orchestrator.py](agents/orchestrator.py) — routes the request and executes tool-based reasoning
- [agents/tvm_subagent.py](agents/tvm_subagent.py) — system prompt for the TVM specialist
- [tools/tool_registry.py](tools/tool_registry.py) — exposes the callable math tools to the agent
- [tools/tvm_math.py](tools/tvm_math.py) — deterministic TVM math backend

## Local development

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GOOGLE_API_KEY="your-key"
streamlit run app.py
```

## Streamlit Cloud deployment

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud and create a new app.
3. Point it at this repository and choose [app.py](app.py) as the main file.
4. Add the following secret under Settings → Secrets:

```toml
GOOGLE_API_KEY = "your-google-key"
```

## Running tests

```bash
python test_tvm_math.py
```

## Sample prompts

- What is the PV of $5,000 due in 8 years at 6% annual?
- Convert 12% nominal monthly to effective annual.
- What rate doubles money in 10 years?
- Find the force of interest equivalent to 8% effective annual.
- A loan of $10,000 today is repaid with $4,000 in 3 years and X in 7 years at 8% annual. Find X.
