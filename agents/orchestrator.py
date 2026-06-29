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
    # Use the Google Generative API (Gemini) directly with an API key.
    token = os.getenv("GOOGLE_API_KEY")
    if not token:
        return {"response": "", "tool_calls": [], "error": "GOOGLE_API_KEY not set"}

    system_prompt = TVM_SYSTEM_PROMPT
    # Build messages in the correct format for Gemini API
    messages = conversation_history + [{"role": "user", "content": user_message}]

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={token}"
    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": m.get("role", "user"),
                "parts": [{"text": m.get("content", "")}]
            }
            for m in messages
        ],
        "generation_config": {
            "maxOutputTokens": MAX_TOKENS,
            "temperature": 0.2,
        },
    }

    def _extract_text_from_response(resp):
        try:
            data = resp.json()
        except Exception:
            return None, f"Non-JSON response (status {resp.status_code}): {resp.text}"
        
        # Gemini API response format
        candidates = data.get("candidates") or []
        if candidates:
            first = candidates[0]
            content = first.get("content", {})
            parts = content.get("parts", [])
            if parts:
                text = parts[0].get("text")
                return text or "", None
        
        return None, f"No text candidate in JSON response: {data}"

    # Make the API request
    try:
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if resp.status_code == 200:
            text, extract_err = _extract_text_from_response(resp)
            if extract_err:
                return {"response": "", "tool_calls": [], "error": extract_err}
            return {"response": text, "tool_calls": [], "error": None}
        else:
            return {"response": "", "tool_calls": [], "error": f"API returned status {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"response": "", "tool_calls": [], "error": str(e)}
