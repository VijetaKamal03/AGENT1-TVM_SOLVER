"""
tool_registry.py — Defines tool schemas and dispatches calls to tvm_math.py.

Every tool the orchestrator can invoke lives here.
The LLM sees tool descriptions; this file does the actual routing.
"""

import json
from tools.tvm_math import (
    future_value, present_value, solve_rate, solve_periods,
    nominal_to_effective, effective_to_nominal,
    effective_to_force, force_to_effective,
    rate_per_period,
    equation_of_value, solve_unknown_payment,
    fv_continuous, pv_continuous,
    fv_simple, pv_simple,
    discount_rate_from_interest, interest_rate_from_discount,
)

TOOLS = [
    {
        "name": "future_value",
        "description": (
            "Calculate the future value of a single lump sum under compound interest. "
            "FV = PV × (1+i)^n. Sign convention: inflows positive, outflows negative."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pv": {"type": "number", "description": "Present value (negative if outflow)"},
                "i": {"type": "number", "description": "Interest rate per period as a decimal (e.g., 0.05 for 5%)"},
                "n": {"type": "number", "description": "Number of compounding periods"},
            },
            "required": ["pv", "i", "n"],
        },
    },
    {
        "name": "present_value",
        "description": (
            "Calculate the present value of a single future lump sum under compound interest. "
            "PV = FV / (1+i)^n."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "fv": {"type": "number", "description": "Future value"},
                "i": {"type": "number", "description": "Interest rate per period as a decimal"},
                "n": {"type": "number", "description": "Number of compounding periods"},
            },
            "required": ["fv", "i", "n"],
        },
    },
    {
        "name": "solve_rate",
        "description": (
            "Solve for the per-period interest rate given PV, FV, and n. "
            "i = (FV/PV)^(1/n) - 1. "
            "PV and FV must have opposite signs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pv": {"type": "number", "description": "Present value (typically negative)"},
                "fv": {"type": "number", "description": "Future value (typically positive)"},
                "n": {"type": "number", "description": "Number of periods"},
            },
            "required": ["pv", "fv", "n"],
        },
    },
    {
        "name": "solve_periods",
        "description": (
            "Solve for the number of periods given PV, FV, and per-period rate. "
            "n = ln(FV/PV) / ln(1+i). PV and FV must have opposite signs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pv": {"type": "number", "description": "Present value (typically negative)"},
                "fv": {"type": "number", "description": "Future value (typically positive)"},
                "i": {"type": "number", "description": "Interest rate per period as a decimal"},
            },
            "required": ["pv", "fv", "i"],
        },
    },
    {
        "name": "nominal_to_effective",
        "description": (
            "Convert a nominal annual interest rate (compounded m times per year) "
            "to an effective annual rate. i_eff = (1 + i_nom/m)^m - 1."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "i_nominal": {"type": "number", "description": "Nominal annual rate as decimal (e.g., 0.12 for 12%)"},
                "m": {"type": "integer", "description": "Compounding frequency per year (e.g., 12 for monthly)"},
            },
            "required": ["i_nominal", "m"],
        },
    },
    {
        "name": "effective_to_nominal",
        "description": (
            "Convert an effective annual interest rate to a nominal annual rate "
            "compounded m times per year. i_nom = m × ((1+i_eff)^(1/m) - 1)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "i_eff": {"type": "number", "description": "Effective annual rate as decimal"},
                "m": {"type": "integer", "description": "Desired compounding frequency per year"},
            },
            "required": ["i_eff", "m"],
        },
    },
    {
        "name": "effective_to_force",
        "description": (
            "Convert an effective annual interest rate to the force of interest (continuous rate). "
            "δ = ln(1 + i)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "i_eff": {"type": "number", "description": "Effective annual interest rate as decimal"},
            },
            "required": ["i_eff"],
        },
    },
    {
        "name": "force_to_effective",
        "description": (
            "Convert a force of interest (continuous compounding rate δ) "
            "to an effective annual interest rate. i = e^δ - 1."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "delta": {"type": "number", "description": "Force of interest as decimal"},
            },
            "required": ["delta"],
        },
    },
    {
        "name": "equation_of_value",
        "description": (
            "Evaluate the net present/accumulated value of multiple cashflows at a single valuation date. "
            "Used to check if an equation of value is satisfied (result = 0 means balanced). "
            "Provide cashflows as a list of [amount, time] pairs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cashflows": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "prefixItems": [
                            {"type": "number", "description": "Amount (positive=inflow, negative=outflow)"},
                            {"type": "number", "description": "Time in periods"},
                        ],
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "description": "List of [amount, time] pairs",
                },
                "i": {"type": "number", "description": "Effective interest rate per period"},
                "valuation_date": {"type": "number", "description": "Time point to accumulate/discount to (default 0)"},
            },
            "required": ["cashflows", "i"],
        },
    },
    {
        "name": "solve_unknown_payment",
        "description": (
            "Find the unknown payment X at a given time that satisfies the equation of value. "
            "All known cashflows are provided; X balances them."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "known_cashflows": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "prefixItems": [
                            {"type": "number"},
                            {"type": "number"},
                        ],
                    },
                    "description": "Known [amount, time] pairs",
                },
                "unknown_time": {"type": "number", "description": "Time of the unknown payment X"},
                "i": {"type": "number", "description": "Effective rate per period"},
                "valuation_date": {"type": "number", "description": "Valuation date (default 0)"},
            },
            "required": ["known_cashflows", "unknown_time", "i"],
        },
    },
    {
        "name": "fv_continuous",
        "description": "Future value under continuous compounding. FV = PV × e^(δ·t).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pv": {"type": "number", "description": "Present value"},
                "delta": {"type": "number", "description": "Force of interest"},
                "t": {"type": "number", "description": "Time in years"},
            },
            "required": ["pv", "delta", "t"],
        },
    },
    {
        "name": "pv_continuous",
        "description": "Present value under continuous compounding. PV = FV × e^(-δ·t).",
        "input_schema": {
            "type": "object",
            "properties": {
                "fv": {"type": "number", "description": "Future value"},
                "delta": {"type": "number", "description": "Force of interest"},
                "t": {"type": "number", "description": "Time in years"},
            },
            "required": ["fv", "delta", "t"],
        },
    },
    {
        "name": "fv_simple",
        "description": "Future value under simple interest. FV = PV × (1 + i×n).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pv": {"type": "number"},
                "i": {"type": "number", "description": "Simple interest rate per period"},
                "n": {"type": "number", "description": "Number of periods"},
            },
            "required": ["pv", "i", "n"],
        },
    },
    {
        "name": "discount_rate_from_interest",
        "description": "Convert effective annual interest rate i to annual discount rate d. d = i/(1+i).",
        "input_schema": {
            "type": "object",
            "properties": {
                "i": {"type": "number", "description": "Effective annual interest rate as decimal"},
            },
            "required": ["i"],
        },
    },
    {
        "name": "interest_rate_from_discount",
        "description": "Convert annual discount rate d to effective annual interest rate i. i = d/(1-d).",
        "input_schema": {
            "type": "object",
            "properties": {
                "d": {"type": "number", "description": "Annual discount rate as decimal"},
            },
            "required": ["d"],
        },
    },
]


def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call and return the result as a string."""
    try:
        if tool_name == "future_value":
            result = future_value(**tool_input)
            return json.dumps({"future_value": round(result, 6)})

        elif tool_name == "present_value":
            result = present_value(**tool_input)
            return json.dumps({"present_value": round(result, 6)})

        elif tool_name == "solve_rate":
            result = solve_rate(**tool_input)
            return json.dumps({
                "rate_per_period": round(result, 8),
                "rate_per_period_pct": round(result * 100, 6),
            })

        elif tool_name == "solve_periods":
            result = solve_periods(**tool_input)
            return json.dumps({"periods": round(result, 6)})

        elif tool_name == "nominal_to_effective":
            result = nominal_to_effective(**tool_input)
            return json.dumps({
                "effective_annual_rate": round(result, 8),
                "effective_annual_rate_pct": round(result * 100, 6),
            })

        elif tool_name == "effective_to_nominal":
            result = effective_to_nominal(**tool_input)
            return json.dumps({
                "nominal_annual_rate": round(result, 8),
                "nominal_annual_rate_pct": round(result * 100, 6),
            })

        elif tool_name == "effective_to_force":
            result = effective_to_force(**tool_input)
            return json.dumps({"force_of_interest": round(result, 8)})

        elif tool_name == "force_to_effective":
            result = force_to_effective(**tool_input)
            return json.dumps({
                "effective_annual_rate": round(result, 8),
                "effective_annual_rate_pct": round(result * 100, 6),
            })

        elif tool_name == "equation_of_value":
            cashflows = [tuple(x) for x in tool_input["cashflows"]]
            i = tool_input["i"]
            valuation_date = tool_input.get("valuation_date", 0.0)
            result = equation_of_value(cashflows, i, valuation_date)
            return json.dumps({"net_value_at_valuation_date": round(result, 6)})

        elif tool_name == "solve_unknown_payment":
            cashflows = [tuple(x) for x in tool_input["known_cashflows"]]
            result = solve_unknown_payment(
                cashflows,
                tool_input["unknown_time"],
                tool_input["i"],
                tool_input.get("valuation_date", 0.0),
            )
            return json.dumps({"unknown_payment_X": round(result, 6)})

        elif tool_name == "fv_continuous":
            result = fv_continuous(**tool_input)
            return json.dumps({"future_value_continuous": round(result, 6)})

        elif tool_name == "pv_continuous":
            result = pv_continuous(**tool_input)
            return json.dumps({"present_value_continuous": round(result, 6)})

        elif tool_name == "fv_simple":
            result = fv_simple(**tool_input)
            return json.dumps({"future_value_simple": round(result, 6)})

        elif tool_name == "discount_rate_from_interest":
            result = discount_rate_from_interest(**tool_input)
            return json.dumps({
                "discount_rate": round(result, 8),
                "discount_rate_pct": round(result * 100, 6),
            })

        elif tool_name == "interest_rate_from_discount":
            result = interest_rate_from_discount(**tool_input)
            return json.dumps({
                "interest_rate": round(result, 8),
                "interest_rate_pct": round(result * 100, 6),
            })

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})
