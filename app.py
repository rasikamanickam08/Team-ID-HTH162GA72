import hashlib
import html

import altair as alt
import pandas as pd
import streamlit as st

from pdf_reader import extract_text
from map import map_requirements, detect_domain, DOMAINS, SEVERITY_RANK
from dlp import scan_text, mask_text

st.set_page_config(
    page_title="COMPLYAI - AI Compliance Command Center",
    page_icon="🛡️",
    layout="wide",
)

# ------------------------------------------------------------------
# LOGIN USERS  (demo only - change these before the demo/submission)
# ------------------------------------------------------------------
def _h(text):
    return hashlib.sha256(text.encode()).hexdigest()


USERS = {
    "admin": _h("admin123"),
    "analyst": _h("analyst123"),
}

# ------------------------------------------------------------------
# COLORS (change here only)
# ------------------------------------------------------------------
COLORS = {
    "Not Compliant": "#2e7d32",      # green
    "Partially Compliant": "#f9a825",  # yellow
    "Fully Compliant": "#c62828",        # red
}
EMOJI = {"Not Compliant": "🟢", "Partially Compliant": "🟡", "Fully Compliant": "🔴"}
SEV_COLORS = {
    "Critical": "#c62828",  # red
    "High": "#ef6c00",      # orange
    "Medium": "#f9a825",    # yellow
    "Low": "#2e7d32",       # green
}
SEV_EMOJI = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}

# ------------------------------------------------------------------
# STYLE
# ------------------------------------------------------------------
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
    .kpi .value {font-size: 40px; font-weight: 800; line-height: 1.2;}
    .section {
        font-size: 18px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
        margin: 26px 0 10px 0; padding-bottom: 6px; border-bottom: 2px solid rgba(128,128,128,.3);
    }
    .gap-row {
        display: flex; align-items: center; gap: 10px; padding: 10px 12px; margin-bottom: 8px;
        border: 1px solid rgba(128,128,128,.3); border-radius: 10px;
    }
    .dot {width: 14px; height: 14px; border-radius: 50%; flex: none;}
    .badge {color: white; padding: 2px 10px; border-radius: 10px; font-size: 12px; margin-left: auto; flex: none;}
    .muted {opacity: .7; font-size: 13px;}
    .filebox {
        display: inline-block; border: 1.5px solid rgba(128,128,128,.5); border-radius: 8px;
        padding: 8px 16px; margin-right: 10px; font-family: monospace;
    }
    .finding {
        border: 1px solid rgba(128,128,128,.3); border-left: 8px solid #c62828;
        border-radius: 10px; padding: 14px 18px; margin-top: 10px;
    }
    .login-title {text-align: center; margin-bottom: 4px;}
    .detect {
        text-align: center; padding: 16px; margin: 16px 0 4px 0; border-radius: 14px;
        border: 2px solid #1976d2; background: rgba(25,118,210,.08);
    }
    .detect .big {font-size: 30px; font-weight: 800; letter-spacing: 2px;}
    </style>
    """,
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


# ------------------------------------------------------------------
# LOGIN PAGE
# ------------------------------------------------------------------
def login_page():
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.write("")
        st.markdown(
            """
            <div class="banner" style="text-align:center">
                <h1>🛡️ COMPLYAI</h1>
                <p>AI Compliance Command Center - sign in to continue</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔐 Login", type="primary")
        if submitted:
            if USERS.get(username.strip()) == _h(password):
                st.session_state.auth = True
                st.session_state.user = username.strip()
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.caption("Demo login: admin / admin123")


if not st.session_state.get("auth"):
    login_page()
    st.stop()

# ------------------------------------------------------------------
# SIDEBAR (after login)
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.get('user', '')}")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.header("⚙️ Settings")
    full_t = st.slider("Fully compliant match (%)", 30, 90, 55, 5)
    part_t = st.slider("Partially compliant match (%)", 10, 60, 30, 5)
    max_req = st.slider("Max requirements to check", 10, 100, 40, 5)
    st.divider()
    st.caption(
        "How it works: the regulation is split into requirements, each one is "
        "matched to the closest clause in the company policy, and the AI gives "
        "a status, risk level and corrective action."
    )

# ------------------------------------------------------------------
# HEADER + UPLOAD
# ------------------------------------------------------------------
st.markdown(
    f"""
    <div class="banner">
        <h1>🛡️ COMPLYAI</h1>
        <p>AI Compliance Command Center. Welcome, {html.escape(st.session_state.get('user', ''))}. Upload any regulation and find policy gaps instantly.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

section("📄 Upload Compliance Documents")
AUTO = "🤖 Auto-detect (AI)"
choice = st.selectbox(
    "Step 1 - Regulation category",
    [AUTO] + [f"{v['emoji']} {k}" for k, v in DOMAINS.items()],
)
domain_choice = "Auto-detect" if choice == AUTO else choice.split(" ", 1)[1]
c1, c2 = st.columns(2)
with c1:
    reg_file = st.file_uploader("Upload Regulation / Standard PDF", type="pdf")
with c2:
    policy_file = st.file_uploader("Upload Company Policy PDF", type="pdf")

for key in ("rows", "reg_name", "policy_name", "domain", "domain_conf", "domain_auto"):
    st.session_state.setdefault(key, None)

ready = reg_file is not None and policy_file is not None
if not ready:
    st.info("Upload both PDFs, then click **Run Intelligent Scan**.")

if st.button("⚡ RUN INTELLIGENT SCAN", type="primary", disabled=not ready):
    with st.spinner("AI is scanning your documents..."):
        reg_text = extract_text(reg_file)
        policy_text = extract_text(policy_file)
        if domain_choice == "Auto-detect":
            domain, conf = detect_domain(reg_text)
            auto = True
        else:
            domain, conf, auto = domain_choice, 100, False
        st.session_state.domain = domain
        st.session_state.domain_conf = conf
        st.session_state.domain_auto = auto
        st.session_state.rows = map_requirements(
            reg_text,
            policy_text,
            domain=domain,
            full_threshold=full_t / 100,
            partial_threshold=part_t / 100,
            max_requirements=max_req,
        )
        st.session_state.reg_name = reg_file.name
        st.session_state.policy_name = policy_file.name

rows = st.session_state.rows

if rows is not None and len(rows) == 0:
    st.warning("No requirements were found. Check that the PDFs contain readable text (not scanned images).")

# ------------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------------
if rows:
    df = pd.DataFrame(rows)
    total = len(df)
    full = int((df["status"] == "Fully Compliant").sum())
    partial = int((df["status"] == "Partially Compliant").sum())
    notc = int((df["status"] == "Not Compliant").sum())
    score = round((full + 0.5 * partial) / total * 100)

    if score >= 75:
        score_color, verdict = "#2e7d32", "Good compliance level"
    elif score >= 40:
        score_color, verdict = "#f9a825", "Needs improvement"
    elif score >= 20:
        score_color, verdict = "#ef6c00", "High risk"
    else:
        score_color, verdict = "#c62828", "Critical risk"

    df["rank"] = df["severity"].map(SEVERITY_RANK)
    gaps = df[df["status"] != "Fully Compliant"].sort_values(["rank", "score"])

    st.markdown(
        f"<span class='filebox'>📄 {html.escape(st.session_state.reg_name or '')}"
        f"<br><small>{total} requirements</small></span>"
        f"<b> VS </b>"
        f"<span class='filebox'>📄 {html.escape(st.session_state.policy_name or '')}"
        f"<br><small>Company policy</small></span>",
        unsafe_allow_html=True,
    )

    dom = st.session_state.domain or "General"
    info = DOMAINS.get(dom, {"emoji": "📘"})
    how = "AI auto-detected" if st.session_state.domain_auto else "Selected by user"
    st.markdown(
        f"<div class='detect'>Regulation Detected<br>"
        f"<span class='big'>{info['emoji']} {html.escape(dom.upper())}</span><br>"
        f"<span class='muted'>{how} · confidence {st.session_state.domain_conf}%</span></div>",
        unsafe_allow_html=True,
    )

    # ---------------- COMPLIANCE HEALTH ----------------
    section("📊 Compliance Health")
    risks = int((df["severity"] == "Critical").sum())
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi(f"Score - {verdict}", f"{score}%", score_color)
    with k2:
        kpi("Compliant", full, COLORS["Fully Compliant"])
    with k3:
        kpi("Partial", partial, COLORS["Partially Compliant"])
    with k4:
        kpi("Non-Compliant", notc, COLORS["Not Compliant"])
    with k5:
        kpi("Critical Risks", risks, SEV_COLORS["High"])
    st.write("")
    st.progress(score / 100)

    # ---------------- TOP GAPS + RISK DISTRIBUTION ----------------
    left, right = st.columns([1.2, 1])
    with left:
        section("🔥 Top Gaps")
        if gaps.empty:
            st.success("No gaps found. All requirements are covered.")
        for _, r in gaps.head(5).iterrows():
            short = r["requirement"][:75] + ("..." if len(r["requirement"]) > 75 else "")
            st.markdown(
                f"<div class='gap-row'>"
                f"<span class='dot' style='background:{SEV_COLORS[r['severity']]}'></span>"
                f"<div><b>{html.escape(r['ref'])}</b><br>"
                f"<span class='muted'>{html.escape(short)}</span></div>"
                f"<span class='badge' style='background:{SEV_COLORS[r['severity']]}'>{r['severity']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    with right:
        section("📈 Risk Distribution")
        order = ["Critical", "High", "Medium"]
        risk_df = pd.DataFrame(
            {"Risk": order, "Count": [int((df["severity"] == s).sum()) for s in order]}
        )
        bar = (
            alt.Chart(risk_df)
            .mark_bar(cornerRadiusEnd=5)
            .encode(
                y=alt.Y("Risk:N", sort=order, title=None),
                x=alt.X("Count:Q", title=None),
                color=alt.Color(
                    "Risk:N",
                    scale=alt.Scale(
                        domain=order, range=[SEV_COLORS[s] for s in order]
                    ),
                    legend=None,
                ),
                tooltip=["Risk", "Count"],
            )
            .properties(height=220)
        )
        st.altair_chart(bar)

    # ---------------- RECOMMENDED ACTIONS ----------------
    section("💡 Recommended Actions")
    if gaps.empty:
        st.success("No actions needed.")
    else:
        for n, (_, a) in enumerate(gaps.drop_duplicates("action").head(3).iterrows(), 1):
            st.markdown(
                f"**{n}.** {a['action']}  \n"
                f"<span class='muted'>{html.escape(a['ref'])} · {a['severity']} · "
                f"owner: {html.escape(a['owner'])} · within {a['deadline_days']} days</span>",
                unsafe_allow_html=True,
            )

    # ---------------- AI GAP HUNTER ----------------
    section("🧠 AI Gap Hunter")
    if gaps.empty:
        st.success("Nothing to hunt. No gaps detected.")
    else:
        hunter = pd.DataFrame(
            {
                "Regulation": gaps["ref"],
                "Company Policy": gaps["policy_ref"],
                "AI Finding": gaps["flag"],
                "Risk": gaps["severity"].map(lambda s: f"{SEV_EMOJI[s]} {s}"),
                "Match %": gaps["score"],
            }
        )
        st.dataframe(hunter, hide_index=True)

        options = [
            f"{i + 1}. {r['ref']} - {r['requirement'][:60]}"
            for i, (_, r) in enumerate(gaps.iterrows())
        ]
        pick = st.selectbox("Select a finding to inspect", options)
        r = gaps.iloc[options.index(pick)]
        st.markdown(
            f"<div class='finding' style='border-left-color:{SEV_COLORS[r['severity']]}'>"
            f"<b>{html.escape(r['ref'])}</b> &nbsp;→&nbsp; "
            f"<b>{html.escape(r['policy_ref'])}</b> &nbsp;→&nbsp; <b>{r['flag']}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("**Why?**")
        st.write(r["explanation"])
        st.markdown("**Regulation says**")
        st.write(r["full_requirement"])
        if r["matched_policy"]:
            st.markdown("**Closest policy clause**")
            st.write(r["matched_policy"])
        st.markdown("**✅ Corrective action**")
        st.info(f"{r['action']}  \n**Deadline:** within {r['deadline_days']} days")

    # ---------------- TABS ----------------
    section("📂 Details")
    t1, t2, t3 = st.tabs(["🛠️ Corrective Actions", "🚩 AI Flags", "📋 All Findings"])

    with t1:
        if gaps.empty:
            st.success("No corrective actions required.")
        else:
            actions = pd.DataFrame(
                {
                    "Priority": gaps["severity"].map(lambda s: f"{SEV_EMOJI[s]} {s}"),
                    "Regulation": gaps["ref"],
                    "Corrective Action": gaps["action"],
                    "Owner": gaps["owner"],
                    "Deadline": gaps["deadline_days"].map(lambda d: f"Within {d} days"),
                }
            )
            st.dataframe(actions, hide_index=True)
            st.download_button(
                "⬇️ Download Action Plan (CSV)",
                actions.to_csv(index=False).encode("utf-8"),
                file_name="corrective_actions.csv",
                mime="text/csv",
            )

    with t2:
        f1, f2, f3 = st.columns(3)
        f1.metric("🔴 Gaps found", notc)
        f2.metric("🟡 Partial matches", partial)
        f3.metric("🚩 Need human review", int(df["review"].sum()))
        flagged = df[(df["status"] != "Fully Compliant") | (df["review"])].sort_values(["rank", "score"])
        for _, r in flagged.head(30).iterrows():
            extra = "  🚩 Borderline match - human review recommended" if r["review"] else ""
            with st.expander(f"{r['flag']}  |  {r['ref']}  |  {r['score']}%{extra}"):
                st.write(r["requirement"])
                st.caption(r["explanation"])

    with t3:
        chosen = st.multiselect(
            "Filter by status", list(COLORS.keys()), default=list(COLORS.keys())
        )
        view = df[df["status"].isin(chosen)]
        table = pd.DataFrame(
            {
                "Status": view["status"].map(lambda s: f"{EMOJI[s]} {s}"),
                "Regulation": view["ref"],
                "Requirement": view["requirement"],
                "Risk": view["severity"],
                "Match %": view["score"],
                "Matched Policy": view["policy_ref"],
            }
        )
        st.dataframe(table, hide_index=True)
        csv_text = df.drop(columns=["rank"]).to_csv(index=False)
        leaks = scan_text(csv_text)
        if leaks:
            st.warning(
                f"🔐 Data Leakage Scan: {len(leaks)} sensitive item(s) found in this report "
                "(for example emails, phone numbers or IDs). Review before sharing."
            )
            st.download_button(
                "🔒 Download MASKED Results (CSV)",
                mask_text(csv_text, leaks).encode("utf-8"),
                file_name="compliance_results_masked.csv",
                mime="text/csv",
            )
        else:
            st.caption("🔐 Data Leakage Scan: no sensitive data found in this report.")
        st.download_button(
            "⬇️ Download All Results (CSV)",
            csv_text.encode("utf-8"),
            file_name="compliance_results.csv",
            mime="text/csv",
        )

    # Optional: report from report_generator.py (ignored if signature differs)
    try:
        from report_generator import generate_report

        report = generate_report(rows)
        if isinstance(report, (bytes, str)):
            st.download_button("📄 Download Report", report, file_name="compliance_report.txt")
    except Exception:
        pass