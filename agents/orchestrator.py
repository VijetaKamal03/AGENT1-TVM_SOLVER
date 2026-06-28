"""
orchestrator.py — Orchestrator Agent

Responsibilities:
  1. Classify incoming user questions (TVM? Out of scope? Clarification needed?)
  2. Route to the appropriate subagent system prompt + tools
  3. Run the agentic tool-use loop (Claude → tool call → result → Claude)
  4. Return the final structured response to the Streamlit UI

Architecture:
  User → Orchestrator → [TVM Subagent system prompt + tools] → tool_registry → tvm_math
                      ↑                                                              ↓
                      └──────────────── result fed back ──────────────────────────────┘
"""

import json
import os
import requests
from tools.tool_registry import TOOLS, dispatch_tool
from agents.tvm_subagent import SYSTEM_PROMPT as TVM_SYSTEM_PROMPT

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
MAX_TOOL_ROUNDS = 10   # safety ceiling on the agentic loop


def _classify_question(user_message: str) -> str:
    """Quick lightweight classification: 'tvm' | 'out_of_scope' | 'general_fm'."""
    msg_lower = user_message.lower()
    tvm_keywords = [
        "present value", "future value", "pv", "fv", "interest rate",
        "compound", "discount", "force of interest", "nominal", "effective",
        "equation of value", "accumulate", "periods", "years", "rate",
        "simple interest", "continuous", "lump sum", "invest", "loan",
        "double", "triple", "repay", "worth", "grow", "δ", "delta",
    ]
    if any(kw in msg_lower for kw in tvm_keywords):
        return "tvm"
    return "tvm"  # default to TVM for now; future: add annuity/bond routing


def run_agent(user_message: str, conversation_history: list[dict]) -> dict:
    """
    Main entry point. Runs the full agentic loop.

    Args:
        user_message:         The latest user message.
        conversation_history: Full prior conversation (list of {role, content} dicts).
                              Do NOT include the new user message — we append it here.

    Returns:
        {
            "response": str,           # Final text answer
            "tool_calls": list[dict],  # Each tool call + result for display
            "error": str | None,
        }
    """
    # Use the Google Generative API (Gemini / text-bison) directly with a Bearer token.
    token = os.getenv("GOOGLE_API_KEY")
    if not token:
        return {"response": "", "tool_calls": [], "error": "GOOGLE_API_KEY not set"}

    system_prompt = TVM_SYSTEM_PROMPT
    # Build a single prompt text from system + history + user message
    messages = conversation_history + [{"role": "user", "content": user_message}]
    prompt_parts = ["SYSTEM: " + system_prompt]
    for m in messages:
        role = m.get("role", "user").upper()
        content = m.get("content", "")
        prompt_parts.append(f"{role}: {content}")
    prompt_text = "\n\n".join(prompt_parts)

    url = "https://generativelanguage.googleapis.com/v1/models/text-bison-001:generate"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "prompt": {"text": prompt_text},
        "maxOutputTokens": 768,
        "temperature": 0.2,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            return {"response": "", "tool_calls": [], "error": f"API error {resp.status_code}: {resp.text}"}
        data = resp.json()
        # Extract text from first candidate
        candidates = data.get("candidates") or []
        if candidates:
            text = candidates[0].get("output", "").strip()
        else:
            text = data.get("output", "") or ""
        return {"response": text, "tool_calls": [], "error": None}
    except Exception as e:
        return {"response": "", "tool_calls": [], "error": str(e)}
