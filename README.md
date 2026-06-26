# TVM Solver Agent 📐

A Financial Mathematics (FM/SOA Exam) agentic solver built with Claude. Ask any TVM question in plain English — the agent reasons through it, calls deterministic math tools, and explains the answer step by step.

## Architecture

```
User (Streamlit Chat UI)
        │
        ▼
┌─────────────────────────────────────┐
│         Orchestrator                │
│  agents/orchestrator.py             │
│  • Classifies question type         │
│  • Routes to subagent system prompt │
│  • Runs the agentic tool-use loop   │
└────────────┬────────────────────────┘
             │  selects system prompt + tools
             ▼
┌─────────────────────────────────────┐
│       TVM Subagent                  │
│  agents/tvm_subagent.py             │
│  • System prompt with FM rules      │
│  • Sign convention enforcement      │
│  • Step-by-step reasoning format    │
└────────────┬────────────────────────┘
             │  tool calls
             ▼
┌─────────────────────────────────────┐
│       Tool Registry                 │
│  tools/tool_registry.py             │
│  • JSON schemas for all 15 tools    │
│  • Dispatches calls to tvm_math.py  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│    Deterministic Math Backend       │
│  tools/tvm_math.py                  │
│  • Pure Python, no LLM              │
│  • Verified against textbook values │
└─────────────────────────────────────┘
```

## File → Concept Map

| File | FM Concept |
|------|-----------|
| `tools/tvm_math.py` → `future_value`, `present_value` | TVM: accumulation factor (1+i)^n |
| `tools/tvm_math.py` → `solve_rate`, `solve_periods` | TVM: solving for unknown i or n |
| `tools/tvm_math.py` → `nominal_to_effective`, `effective_to_nominal` | Rate conversions: i^(m) ↔ i |
| `tools/tvm_math.py` → `effective_to_force`, `force_to_effective` | Force of interest: δ = ln(1+i) |
| `tools/tvm_math.py` → `equation_of_value`, `solve_unknown_payment` | Equation of Value at a common date |
| `tools/tvm_math.py` → `fv_continuous`, `pv_continuous` | Continuous compounding: e^(δt) |
| `tools/tvm_math.py` → `fv_simple`, `pv_simple` | Simple interest: 1 + it |
| `tools/tvm_math.py` → `discount_rate_from_interest` | Discount rates: d = i/(1+i) |
| `agents/tvm_subagent.py` | System prompt = subagent specialization |
| `agents/orchestrator.py` | Agentic loop: Claude → tool → result → Claude |
| `tools/tool_registry.py` | Tool schemas (JSON) + dispatcher |
| `app.py` | Chat interface (Streamlit) |

## Sign Convention

> **Positive (+)** = cash **inflow** (money you receive)  
> **Negative (−)** = cash **outflow** (money you pay out)

This is enforced in the subagent system prompt and respected in all math functions.

## Capabilities (TVM Module)

- **PV / FV** — single lump sums, compound interest
- **Solve for i** — what rate achieves a target growth?
- **Solve for n** — how many periods to reach a target?
- **Rate conversions** — nominal ↔ effective, any compounding frequency
- **Force of interest** δ — continuous compounding equivalent
- **Discount rates** d — d = i/(1+i), i = d/(1-d)
- **Simple interest** — FV = PV(1 + in)
- **Continuous compounding** — FV = PV·e^(δt)
- **Equation of Value** — accumulate/discount multiple cashflows to a common date
- **Unknown payment** — find X that satisfies the equation of value

## Running Tests

```bash
python test_tvm_math.py
# 24/24 tests pass
```

## Local Setup

```bash
pip install anthropic streamlit
export ANTHROPIC_API_KEY=sk-ant-...
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Point to `app.py`
4. Under **Settings → Secrets**, add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
5. Deploy!

## Sample Questions

```
What is the PV of $5,000 due in 8 years at 6% effective annual?
What annual rate doubles money in 10 years?
Convert 12% nominal monthly to effective annual rate.
Find the force of interest equivalent to 8% effective annual.
A loan of $10,000 today is repaid with $4,000 in 3 years and X in 7 years at 8% annual. Find X.
What is the FV of $2,000 under continuous compounding at δ = 0.05 for 5 years?
```

## Coming Soon (one agent at a time)

- [ ] Annuities (level / varying / due)
- [ ] Loans & amortization schedules
- [ ] Refinancing
- [ ] Bonds
