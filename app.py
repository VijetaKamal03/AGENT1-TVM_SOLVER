"""
app.py — TVM Solver Agent (Streamlit UI)

Chat interface → Orchestrator → TVM Subagent → Tools → tvm_math.py
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import run_agent


def _configure_page() -> None:
    st.set_page_config(
        page_title="TVM Solver · FM Agent",
        page_icon="📐",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _render_css() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;500;600&display=swap');

          html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
          }

          .tvm-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
            border-radius: 12px;
            padding: 28px 32px;
            margin-bottom: 24px;
            border-left: 4px solid #38bdf8;
          }
          .tvm-header h1 {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.8rem;
            font-weight: 600;
            color: #f0f9ff;
            margin: 0 0 4px 0;
            letter-spacing: -0.5px;
          }
          .tvm-header p {
            color: #94a3b8;
            margin: 0;
            font-size: 0.9rem;
            font-weight: 300;
          }

          .chat-user {
            background: #1e3a5f;
            border: 1px solid #2d5986;
            border-radius: 12px 12px 2px 12px;
            padding: 14px 18px;
            margin: 8px 0;
            color: #e2e8f0;
            font-size: 0.95rem;
          }
          .chat-assistant {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 12px 12px 12px 2px;
            padding: 14px 18px;
            margin: 8px 0;
            color: #cbd5e1;
            font-size: 0.95rem;
            border-left: 3px solid #38bdf8;
          }

          .tool-badge {
            display: inline-block;
            background: #0c4a6e;
            color: #38bdf8;
            border-radius: 4px;
            padding: 2px 8px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.78rem;
            margin: 2px 0;
          }

          .sidebar-section {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 12px;
          }
          .sidebar-section h4 {
            color: #38bdf8;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 0 0 10px 0;
          }
          .sidebar-section p, .sidebar-section li {
            color: #94a3b8;
            font-size: 0.83rem;
            margin: 4px 0;
          }
          .sidebar-section code {
            background: #1e293b;
            color: #7dd3fc;
            padding: 1px 4px;
            border-radius: 3px;
            font-size: 0.8rem;
          }

          .sign-positive { color: #4ade80; font-weight: 600; }
          .sign-negative { color: #f87171; font-weight: 600; }

          .stTextArea textarea {
            background: #0f172a !important;
            border: 1px solid #1e3a5f !important;
            border-radius: 8px !important;
            color: #e2e8f0 !important;
            font-family: 'Inter', sans-serif !important;
          }

          .stButton > button {
            background: #0369a1 !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
          }
          .stButton > button:hover {
            background: #0284c7 !important;
          }

          #MainMenu {visibility: hidden;}
          footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-section">
              <h4>📐 About</h4>
              <p>An agentic FM solver powered by Claude. Ask any TVM question in plain English.</p>
              <p>Architecture: <strong>Chat UI → Orchestrator → TVM Subagent → Math Tools</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sidebar-section">
              <h4>💱 Sign Convention</h4>
              <p><span class="sign-positive">+ Positive</span> = cash inflow (money received)</p>
              <p><span class="sign-negative">− Negative</span> = cash outflow (money paid out)</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sidebar-section">
              <h4>🧮 Capabilities</h4>
              <ul>
                <li>PV / FV — single lump sums</li>
                <li>Solve for <code>i</code> or <code>n</code></li>
                <li>Nominal ↔ Effective rates</li>
                <li>Force of interest δ</li>
                <li>Discount rates <code>d</code></li>
                <li>Simple & continuous compounding</li>
                <li>Equation of Value</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sidebar-section">
              <h4>💡 Sample Questions</h4>
              <p>• What is the PV of $5,000 in 8 years at 6% annual?</p>
              <p>• Convert 12% nominal monthly to effective annual</p>
              <p>• What rate doubles money in 10 years?</p>
              <p>• Find δ equivalent to 5% effective annual</p>
              <p>• Loan of $10,000 today, repay $4,000 in 3 years and X in 7 years at 8%. Find X.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🗑️ Clear conversation"):
            st.session_state.messages = []
            st.session_state.tool_logs = {}
            st.rerun()


def main() -> None:
    _configure_page()
    _render_css()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "tool_logs" not in st.session_state:
        st.session_state.tool_logs = {}

    _render_sidebar()

    st.markdown(
        """
        <div class="tvm-header">
          <h1>📐 TVM Solver Agent</h1>
          <p>Financial Mathematics · Time Value of Money · SOA FM Exam Topics</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chat_container = st.container()
    with chat_container:
        for idx, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-assistant">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
                if idx in st.session_state.tool_logs and st.session_state.tool_logs[idx]:
                    with st.expander(f"🔧 Tool calls ({len(st.session_state.tool_logs[idx])})", expanded=False):
                        for tc in st.session_state.tool_logs[idx]:
                            st.markdown(f'<span class="tool-badge">{tc["tool"]}</span>', unsafe_allow_html=True)
                            col1, col2 = st.columns(2)
                            with col1:
                                st.caption("Input")
                                st.json(tc["input"])
                            with col2:
                                st.caption("Result")
                                st.json(tc["result"])

    st.markdown("---")

    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_area(
                "Ask a TVM question",
                placeholder="e.g. What is the future value of $2,000 invested today at 7% annual for 15 years?",
                height=80,
                label_visibility="collapsed",
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Solve →", use_container_width=True)

    if submit and user_input.strip():
      if not os.getenv("GOOGLE_API_KEY"):
        st.error("Set GOOGLE_API_KEY in Streamlit Cloud secrets or your shell before asking the agent to solve a problem.")
        return

        user_msg = user_input.strip()
        st.session_state.messages.append({"role": "user", "content": user_msg})

        history = []
        for m in st.session_state.messages[:-1]:
            history.append({"role": m["role"], "content": m["content"]})

        with st.spinner("Reasoning through the problem..."):
            result = run_agent(user_msg, history)

        assistant_msg = result["response"]
        msg_idx = len(st.session_state.messages)

        st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
        st.session_state.tool_logs[msg_idx] = result["tool_calls"]

        if result.get("error"):
            st.error(f"Error: {result['error']}")

        st.rerun()


if __name__ == "__main__":
    main()
