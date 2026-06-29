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
MODEL = "gemini-2.5-flash"
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
    payload = {
        "prompt": {"text": prompt_text},
        "maxOutputTokens": 768,
        "temperature": 0.2,
    }

    def _extract_text_from_response(resp):
        try:
            data = resp.json()
        except Exception:
            return None, f"Non-JSON response (status {resp.status_code}): {resp.text}"
        candidates = data.get("candidates") or []
        if candidates:
            # Newer Generative API returns candidate.output or candidate.content
            first = candidates[0]
            text = first.get("output") or first.get("content") or first.get("text")
            if isinstance(text, dict):
                # some responses nest text
                text = text.get("text") or text.get("content") or str(text)
            return (text or ""), None
        # fallback keys
        if "output" in data and isinstance(data.get("output"), str):
            return data.get("output"), None
        return None, f"No text candidate in JSON response: keys={list(data.keys())}"

    # Decide whether token looks like an OAuth access token (starts with AQ.)
    looks_like_oauth = isinstance(token, str) and token.startswith("AQ.")

    # Try appropriate method(s)
    # 1. If looks like OAuth, try Bearer header first; otherwise try API key query param first.
    methods = []
    if looks_like_oauth:
        methods = ["bearer", "key"]
    else:
        methods = ["key", "bearer"]

    last_error = None
    for method in methods:
        try:
            if method == "bearer":
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
            else:
                # API key as query param
                resp = requests.post(url, params={"key": token}, json=payload, timeout=30)

            if resp.status_code == 200:
                text, extract_err = _extract_text_from_response(resp)
                if extract_err:
                    return {"response": "", "tool_calls": [], "error": extract_err}
                return {"response": text, "tool_calls": [], "error": None}
            else:
                # Record error and try next method
                last_error = f"method={method} status={resp.status_code} body={resp.text}"
                # If 404 or 401, continue to fallback; otherwise keep trying other method
                continue
        except Exception as e:
            last_error = str(e)
            continue

    # All methods exhausted
    return {"response": "", "tool_calls": [], "error": last_error or "Unknown error"}
