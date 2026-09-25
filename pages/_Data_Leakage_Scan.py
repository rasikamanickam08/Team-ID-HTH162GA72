import html

import pandas as pd
import streamlit as st

from dlp import (
    RISK_COLORS, RISK_EMOJI, SAMPLE_TEXT,
    mask_text, overall_risk, scan_text,
)
from ui import apply_style, banner, kpi, read_upload, require_login, section

st.set_page_config(page_title="COMPLYAI - Data Leakage Scan", page_icon="🔐", layout="wide")
apply_style()
require_login()

banner(
    "🔐 Data Leakage Protection Scan",
    "Scan any document before sharing. COMPLYAI detects PAN, phone, bank details, "
    "passwords, API keys and confidential information.",
)

for key in ("dlp", "dlp_action"):
    st.session_state.setdefault(key, None)

# ------------------------------------------------------------------
# INPUT
# ------------------------------------------------------------------
section("📄 Document to scan")
source = st.radio(
    "Source", ["Upload file", "Paste text", "Use sample document"], horizontal=True
)
doc_name, text = "", ""
if source == "Upload file":
    up = st.file_uploader("Upload document (PDF / TXT / CSV)", type=["pdf", "txt", "csv", "md"])
    if up:
        doc_name, text = up.name, read_upload(up)
elif source == "Paste text":
    text = st.text_area("Paste document text", height=200)
    doc_name = "pasted_text.txt" if text.strip() else ""
else:
    text, doc_name = SAMPLE_TEXT, "sample_salary_report.txt"
    st.code(text)

if st.button("🔍 RUN DATA LEAKAGE SCAN", type="primary", disabled=not text.strip()):
    st.session_state.dlp = {"name": doc_name, "text": text, "findings": scan_text(text)}
    st.session_state.dlp_action = None

res = st.session_state.dlp

# ------------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------------
if res:
    findings, text, doc_name = res["findings"], res["text"], res["name"]
    risk = overall_risk(findings)
    n = len(findings)

    section("🛡️ Scan result")
    if n == 0:
        st.success(f"🟢 Low risk - no sensitive information found in **{doc_name}**. Safe to share.")
    else:
        msg = f"⚠️ **Sensitive Information Detected** - {n} confidential item(s) found in **{doc_name}**. Please review before sharing."
        (st.error if risk == "Critical" else st.warning)(msg)

        counts = {r: sum(f["risk"] == r for f in findings) for r in RISK_COLORS}
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            kpi(f"Overall Risk", f"{RISK_EMOJI[risk]} {risk}", RISK_COLORS[risk])
        with k2:
            kpi("Critical", counts["Critical"], RISK_COLORS["Critical"])
        with k3:
            kpi("High", counts["High"], RISK_COLORS["High"])
        with k4:
            kpi("Medium", counts["Medium"], RISK_COLORS["Medium"])
        st.caption("🟢 Low = normal information · 🟡 Medium = employee information · 🟠 High = financial / confidential · 🔴 Critical = password, API key, secret token")

        table = pd.DataFrame(
            {
                "#": range(1, n + 1),
                "Type": [f["type"] for f in findings],
                "Risk": [f"{RISK_EMOJI[f['risk']]} {f['risk']}" for f in findings],
                "Line": [f["line"] for f in findings],
                "Detected (masked preview)": [f["masked"] for f in findings],
                "Suggested action": [f["action"] for f in findings],
            }
        )
        st.dataframe(table, hide_index=True)

        # ---- 3 actions ----
        b1, b2, b3 = st.columns(3)
        if b1.button("🔒 Mask Data"):
            st.session_state.dlp_action = "mask"
        if b2.button("👁️ Review"):
            st.session_state.dlp_action = "review"
        if b3.button("❌ Cancel Sharing"):
            st.session_state.dlp_action = "cancel"

        act = st.session_state.dlp_action

        if act == "mask":
            masked = mask_text(text, findings)
            done = sum(f["maskable"] for f in findings)
            st.success(f"🔒 {done} sensitive item(s) masked. The original values will not leak.")
            ba = pd.DataFrame(
                {
                    "Type": [f["type"] for f in findings if f["maskable"]],
                    "Before": [
                        "[hidden]" if f["risk"] == "Critical" else f["value"]
                        for f in findings if f["maskable"]
                    ],
                    "After": [f["masked"] for f in findings if f["maskable"]],
                }
            )
            st.dataframe(ba, hide_index=True)
            st.text_area("Masked document (safe to share)", masked, height=220)
            st.download_button(
                "⬇️ Download masked document (.txt)",
                masked.encode("utf-8"),
                file_name="masked_" + doc_name.rsplit(".", 1)[0] + ".txt",
                mime="text/plain",
            )
            if any(not f["maskable"] for f in findings):
                st.info("Some items (like 'CONFIDENTIAL' markings) are not masked. Share only with authorised staff.")

        elif act == "review":
            show = st.checkbox("Show original values (off = masked)", value=False)
            lines = text.split("\n")
            for i, f in enumerate(findings, 1):
                line = lines[f["line"] - 1] if f["line"] - 1 < len(lines) else ""
                if not show:
                    line = line.replace(f["value"], f["masked"])
                with st.expander(f"{RISK_EMOJI[f['risk']]} {i}. {f['type']}  (line {f['line']})"):
                    st.code(line[:300])
                    st.caption(f"Suggested action: {f['action']}")

        elif act == "cancel":
            st.error("❌ Sharing cancelled. Nothing was shared.")