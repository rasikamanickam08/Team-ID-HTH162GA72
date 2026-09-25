"""ui.py - shared style + login guard for the COMPLYAI extra pages."""

import html

import streamlit as st


def apply_style():
    st.markdown(
        """
        <style>
        #MainMenu, footer {visibility: hidden;}
        .block-container {padding-top: 1.5rem;}
        .banner {
            background: linear-gradient(90deg, #0d47a1, #1976d2);
            padding: 24px 32px; border-radius: 14px; color: white; margin-bottom: 18px;
        }
        .banner h1 {margin: 0; font-size: 30px; color: white;}
        .banner p {margin: 6px 0 0 0; font-size: 15px; opacity: .9;}
        .kpi {
            border-radius: 14px; padding: 18px 10px; text-align: center; color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,.15);
        }
        .kpi .label {font-size: 13px; letter-spacing: 1px; text-transform: uppercase; opacity: .95;}
        .kpi .value {font-size: 38px; font-weight: 800; line-height: 1.2;}
        .section {
            font-size: 18px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
            margin: 26px 0 10px 0; padding-bottom: 6px; border-bottom: 2px solid rgba(128,128,128,.3);
        }
        .decision {
            border-radius: 14px; padding: 18px 22px; margin: 12px 0; color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,.15);
        }
        .decision h3 {margin: 0 0 6px 0; color: white;}
        .layer {
            border: 1px solid rgba(128,128,128,.35); border-radius: 12px;
            padding: 12px 14px; height: 100%;
        }
        .muted {opacity: .7; font-size: 13px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def banner(title, subtitle):
    st.markdown(
        f"<div class='banner'><h1>{title}</h1><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def kpi(label, value, color):
    st.markdown(
        f"<div class='kpi' style='background:{color}'>"
        f"<div class='label'>{html.escape(str(label))}</div>"
        f"<div class='value'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def section(title):
    st.markdown(f"<div class='section'>{title}</div>", unsafe_allow_html=True)


def read_upload(uploaded):
    """Read text from an uploaded PDF / TXT / CSV / MD file."""
    if uploaded.name.lower().endswith(".pdf"):
        from pdf_reader import extract_text

        text = extract_text(uploaded)
        return text if isinstance(text, str) else str(text or "")
    return uploaded.getvalue().decode("utf-8", errors="ignore")


def require_login():
    """Stop the page unless the user logged in on the main page."""
    if not st.session_state.get("auth"):
        st.warning("🔐 Please login first from the main page (app).")
        try:
            st.page_link("app.py", label="Go to Login", icon="🔐")
        except Exception:
            pass
        st.stop()
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.get('user', '')}")
        if st.button("Logout", key="logout_btn"):
            st.session_state.clear()
            st.rerun()