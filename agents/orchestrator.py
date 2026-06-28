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
import anthropic
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
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    # Route to subagent
    topic = _classify_question(user_message)
    system_prompt = TVM_SYSTEM_PROMPT  # expandable: elif topic == "annuity" etc.

    # Build message list
    messages = conversation_history + [{"role": "user", "content": user_message}]

    tool_calls_log = []
    final_response = ""
    error = None

    try:
        for round_num in range(MAX_TOOL_ROUNDS):
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )

            round_text = ""
            tool_use_blocks = []

            for block in response.content:
                if block.type == "text":
                    round_text += block.text
                elif block.type == "tool_use":
                    tool_use_blocks.append(block)

            if response.stop_reason == "end_turn":
                final_response = round_text
                break

            if response.stop_reason == "tool_use" and tool_use_blocks:
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for tool_block in tool_use_blocks:
                    tool_result = dispatch_tool(tool_block.name, tool_block.input)
                    tool_calls_log.append({
                        "tool": tool_block.name,
                        "input": tool_block.input,
                        "result": json.loads(tool_result),
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": tool_result,
                    })

                messages.append({"role": "user", "content": tool_results})

            else:
                final_response = round_text or "I wasn't able to complete the calculation."
                break

        else:
            final_response = "Reached maximum reasoning steps. Please simplify your question."

    except anthropic.APIError as e:
        error = f"API error: {str(e)}"
        final_response = "An error occurred while processing your request."
    except Exception as e:
        error = f"Unexpected error: {str(e)}"
        final_response = "An unexpected error occurred."

    return {
        "response": final_response,
        "tool_calls": tool_calls_log,
        "error": error,
    }
