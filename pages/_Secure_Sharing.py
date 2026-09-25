from datetime import datetime

import pandas as pd
import streamlit as st

from dlp import (
    CATEGORY_LABELS, RISK_COLORS, RISK_EMOJI, SAMPLE_TEXT,
    categories_of, mask_text, overall_risk, scan_text,
)
from sharing import EMPLOYEES, evaluate, find_approver
from ui import apply_style, banner, read_upload, require_login, section

st.set_page_config(page_title="COMPLYAI - Secure Sharing", page_icon="🔐", layout="wide")
apply_style()
require_login()

banner(
    "🔐 Internal Secure Sharing",
    "Employees can share documents internally. COMPLYAI checks what is inside, "
    "who is receiving it, and whether approval is needed.",
)


# ------------------------------------------------------------------
# SHARED STORE (shared by all logged-in sessions while the server runs)
# ------------------------------------------------------------------
@st.cache_resource
def get_store():
    return {"inbox": [], "approvals": [], "audit": [], "counter": [0]}


store = get_store()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def who(i):
    e = EMPLOYEES[i]
    return f"{e['name']} ({e['department']} · {e['role'].title()})"


def next_id():
    store["counter"][0] += 1
    return store["counter"][0]


def log(action, sender, receiver, doc, risk, decision):
    store["audit"].append(
        {
            "Time": now(),
            "Login user": st.session_state.get("user", ""),
            "Action": action,
            "From": who(sender),
            "To": who(receiver),
            "Document": doc,
            "Risk": risk,
            "Decision": decision,
        }
    )


def deliver(chk, text, via, masked):
    store["inbox"].append(
        {
            "id": next_id(),
            "time": now(),
            "sender": chk["sender"],
            "receiver": chk["receiver"],
            "doc": chk["doc"],
            "text": text,
            "risk": chk["risk"],
            "via": via,
            "masked": masked,
        }
    )


def flash(kind, msg):
    st.session_state.flash = (kind, msg)
    st.rerun()


st.session_state.setdefault("chk", None)
if st.session_state.get("flash"):
    kind, msg = st.session_state.pop("flash")
    getattr(st, kind)(msg)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📤 Smart Share", "✅ Approvals", "📥 Inbox", "🧾 Audit Log"]
)

ids = list(EMPLOYEES.keys())

# ==================================================================
# TAB 1 - SMART SHARE
# ==================================================================
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        sender = st.selectbox("From (sender)", ids, format_func=who, key="sh_sender")
    with c2:
        receiver = st.selectbox("Share with", ids, index=2, format_func=who, key="sh_receiver")

    source = st.radio(
        "Document", ["Upload file", "Paste text", "Use sample document"],
        horizontal=True, key="sh_source",
    )
    doc, text = "", ""
    if source == "Upload file":
        up = st.file_uploader("Select document (PDF / TXT / CSV)", type=["pdf", "txt", "csv", "md"], key="sh_file")
        if up:
            doc, text = up.name, read_upload(up)
    elif source == "Paste text":
        text = st.text_area("Paste document text", height=160, key="sh_text")
        doc = "pasted_text.txt" if text.strip() else ""
    else:
        text, doc = SAMPLE_TEXT, "Employee_Salary_Report.txt"
        st.code(text)

    if st.button("🔍 CHECK PERMISSION", type="primary", disabled=not text.strip(), key="sh_check"):
        findings = scan_text(text)
        cats = categories_of(findings)
        st.session_state.chk = {
            "sender": sender, "receiver": receiver, "doc": doc, "text": text,
            "findings": findings, "cats": cats, "risk": overall_risk(findings),
            "ev": evaluate(sender, receiver, cats),
        }

    chk = st.session_state.chk
    if chk:
        ev, risk, decision = chk["ev"], chk["risk"], chk["ev"]["decision"]
        approver = find_approver(chk["sender"])

        section("🔎 3-layer security check")
        l1, l2, l3 = st.columns(3)
        cat_names = ", ".join(CATEGORY_LABELS[c] for c in sorted(chk["cats"]))
        with l1:
            st.markdown(
                f"<div class='layer'><b>Layer 1 - Sensitive data scan</b><br>"
                f"{len(chk['findings'])} item(s) found<br>"
                f"Risk: {RISK_EMOJI[risk]} <b>{risk}</b><br>"
                f"<span class='muted'>{cat_names}</span></div>",
                unsafe_allow_html=True,
            )
        with l2:
            lines = "".join(
                f"{'✅' if c['ok'] else '❌'} {c['label']}<br>" for c in ev["checks"]
            ) or "-"
            st.markdown(
                f"<div class='layer'><b>Layer 2 - Role-based access</b><br>"
                f"Receiver: {who(chk['receiver'])}<br>{lines}</div>",
                unsafe_allow_html=True,
            )
        with l3:
            if decision == "ALLOWED":
                l3txt = "Not needed"
            elif decision == "APPROVAL_REQUIRED":
                l3txt = f"Approval needed from<br><b>{who(approver) if approver else 'Admin'}</b>"
            else:
                l3txt = "Blocked - mask sensitive data first"
            st.markdown(
                f"<div class='layer'><b>Layer 3 - Approval workflow</b><br>{l3txt}</div>",
                unsafe_allow_html=True,
            )

        if chk["findings"]:
            with st.expander("View detected items (masked)"):
                st.dataframe(
                    pd.DataFrame(
                        {
                            "Type": [f["type"] for f in chk["findings"]],
                            "Risk": [f["risk"] for f in chk["findings"]],
                            "Line": [f["line"] for f in chk["findings"]],
                            "Masked preview": [f["masked"] for f in chk["findings"]],
                        }
                    ),
                    hide_index=True,
                )

        # ---------------- decision card ----------------
        if decision == "ALLOWED":
            st.markdown(
                f"<div class='decision' style='background:#2e7d32'>"
                f"<h3>🟢 Safe to Share Internally</h3>"
                f"Receiver: {who(chk['receiver'])}<br>Sensitivity: {risk}<br>"
                f"Permission: Authorized</div>",
                unsafe_allow_html=True,
            )
            if st.button("🔒 SHARE SECURELY", type="primary", key="btn_share"):
                deliver(chk, chk["text"], "Authorized - direct share", False)
                log("SHARED", chk["sender"], chk["receiver"], chk["doc"], risk, "ALLOWED")
                st.session_state.chk = None
                flash("success", f"✅ Shared securely with {who(chk['receiver'])}. Logged in the audit trail.")

        elif decision == "APPROVAL_REQUIRED":
            reasons = "<br>".join(f"• {c['reason']}" for c in ev["checks"] if not c["ok"])
            st.markdown(
                f"<div class='decision' style='background:#ef6c00'>"
                f"<h3>🟠 Approval Required</h3>{ev['message']}<br>{reasons}</div>",
                unsafe_allow_html=True,
            )
            a1, a2 = st.columns(2)
            if a1.button("📨 REQUEST APPROVAL", type="primary", key="btn_req"):
                store["approvals"].append(
                    {
                        "id": next_id(), "time": now(), "sender": chk["sender"],
                        "receiver": chk["receiver"], "doc": chk["doc"], "text": chk["text"],
                        "risk": risk, "cats": sorted(chk["cats"]), "status": "Pending",
                        "approver": approver, "decided_by": "", "decided_at": "",
                    }
                )
                log("APPROVAL_REQUESTED", chk["sender"], chk["receiver"], chk["doc"], risk, "PENDING")
                st.session_state.chk = None
                flash("info", "📨 Approval request sent. Check the Approvals tab.")
            if a2.button("🛡️ Share masked version instead", key="btn_masked_a"):
                st.session_state.masked_try = True
                st.session_state.masked_try_chk = True

        else:  # BLOCKED
            st.markdown(
                f"<div class='decision' style='background:#c62828'>"
                f"<h3>🔴 Sharing Blocked</h3>{ev['message']}</div>",
                unsafe_allow_html=True,
            )
            if st.button("🛡️ Share masked version instead", key="btn_masked_b"):
                st.session_state.masked_try = True

        # ---------------- masked-share attempt ----------------
        if st.session_state.get("masked_try") and decision != "ALLOWED":
            masked = mask_text(chk["text"], chk["findings"])
            f2 = scan_text(masked)
            ev2 = evaluate(chk["sender"], chk["receiver"], categories_of(f2))
            st.session_state.masked_try = False
            if ev2["decision"] == "ALLOWED":
                deliver(chk, masked, "Masked version shared", True)
                log("SHARED_MASKED", chk["sender"], chk["receiver"], chk["doc"], overall_risk(f2), "ALLOWED")
                st.session_state.chk = None
                flash("success", "🛡️ Masked version shared. Sensitive values were removed before sending.")
            else:
                st.warning("Even the masked version still needs approval (for example it is marked CONFIDENTIAL). Use **Request Approval**.")

# ==================================================================
# TAB 2 - APPROVALS
# ==================================================================
with tab2:
    is_admin = st.session_state.get("user") == "admin"
    if not is_admin:
        st.info("Only the **admin** login can approve or reject requests. You can still see the status.")

    pending = [a for a in store["approvals"] if a["status"] == "Pending"]
    st.subheader(f"Pending requests ({len(pending)})")
    if not pending:
        st.success("No pending approvals.")
    for a in pending:
        with st.expander(f"#{a['id']}  {a['doc']}  |  {who(a['sender'])} → {who(a['receiver'])}"):
            st.write(f"**Risk:** {RISK_EMOJI[a['risk']]} {a['risk']}")
            st.write("**Contains:** " + ", ".join(CATEGORY_LABELS[c] for c in a["cats"]))
            st.write(f"**Approver:** {who(a['approver']) if a['approver'] else 'Admin'}")
            st.code(mask_text(a["text"])[:600])
            if is_admin:
                d1, d2 = st.columns(2)
                if d1.button("✅ Approve", key=f"ap_{a['id']}"):
                    a["status"], a["decided_by"], a["decided_at"] = "Approved", st.session_state.user, now()
                    deliver(
                        {"sender": a["sender"], "receiver": a["receiver"], "doc": a["doc"], "risk": a["risk"]},
                        a["text"], f"Approved by {st.session_state.user}", False,
                    )
                    log("APPROVED", a["sender"], a["receiver"], a["doc"], a["risk"], "APPROVED")
                    flash("success", f"✅ Request #{a['id']} approved and delivered.")
                if d2.button("❌ Reject", key=f"rj_{a['id']}"):
                    a["status"], a["decided_by"], a["decided_at"] = "Rejected", st.session_state.user, now()
                    log("REJECTED", a["sender"], a["receiver"], a["doc"], a["risk"], "REJECTED")
                    flash("warning", f"❌ Request #{a['id']} rejected.")

    history = [a for a in store["approvals"] if a["status"] != "Pending"]
    if history:
        st.subheader("History")
        st.dataframe(
            pd.DataFrame(
                {
                    "ID": [a["id"] for a in history],
                    "Document": [a["doc"] for a in history],
                    "From": [who(a["sender"]) for a in history],
                    "To": [who(a["receiver"]) for a in history],
                    "Status": [a["status"] for a in history],
                    "Decided by": [a["decided_by"] for a in history],
                    "Time": [a["decided_at"] for a in history],
                }
            ),
            hide_index=True,
        )

# ==================================================================
# TAB 3 - INBOX
# ==================================================================
with tab3:
    viewer = st.selectbox("View inbox as", ids, index=2, format_func=who, key="inbox_viewer")
    mine = [m for m in store["inbox"] if m["receiver"] == viewer]
    if not mine:
        st.info("No documents received yet.")
    for m in reversed(mine):
        tag = "🛡️ masked" if m["masked"] else "📄 original"
        with st.expander(f"{m['doc']}  |  from {who(m['sender'])}  |  {m['time']}  |  {tag}"):
            st.caption(f"Delivered via: {m['via']} · Risk: {RISK_EMOJI[m['risk']]} {m['risk']}")
            st.code(m["text"][:1500])
            st.download_button(
                "⬇️ Download", m["text"].encode("utf-8"),
                file_name=m["doc"].rsplit(".", 1)[0] + ".txt", key=f"dl_{m['id']}",
            )

# ==================================================================
# TAB 4 - AUDIT LOG
# ==================================================================
with tab4:
    if not store["audit"]:
        st.info("No activity yet.")
    else:
        audit = pd.DataFrame(store["audit"][::-1])
        st.dataframe(audit, hide_index=True)
        st.download_button(
            "⬇️ Download audit log (CSV)", audit.to_csv(index=False).encode("utf-8"),
            file_name="audit_log.csv", mime="text/csv",
        )

st.caption(
    "Prototype access-control demo. For real deployment add proper authentication (SSO), "
    "encryption, a permanent database for audit logs and a real permission system."
)