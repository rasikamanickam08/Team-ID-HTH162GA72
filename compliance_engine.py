import streamlit as st
from compliance_engine import compare_compliance


st.set_page_config(
    page_title="AI Compliance Assistant",
    page_icon="🛡️",
    layout="wide"
)


# -------------------------------
# Custom CSS
# -------------------------------

st.markdown("""
<style>

.compliance-card {
    padding: 20px;
    border-radius: 12px;
    margin: 10px 0px;
    border-left: 7px solid;
}

.red-card {
    background-color: #FEE2E2;
    border-left-color: #DC2626;
}

.yellow-card {
    background-color: #FEF3C7;
    border-left-color: #F59E0B;
}

.green-card {
    background-color: #DCFCE7;
    border-left-color: #16A34A;
}

.status-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-weight: bold;
    display: inline-block;
}

.red-badge {
    background-color: #DC2626;
    color: white;
}

.yellow-badge {
    background-color: #F59E0B;
    color: white;
}

.green-badge {
    background-color: #16A34A;
    color: white;
}

</style>
""", unsafe_allow_html=True)


st.title("🛡️ AI Compliance Assistant")

st.caption(
    "AI-powered regulatory compliance checking "
    "and company policy gap analysis"
)


# -------------------------------
# Upload Documents
# -------------------------------

st.header("📄 Upload Compliance Documents")

col1, col2 = st.columns(2)

with col1:
    regulation_file = st.file_uploader(
        "Upload Regulation / Standard PDF",
        type=["pdf"]
    )

with col2:
    policy_file = st.file_uploader(
        "Upload Company Policy PDF",
        type=["pdf"]
    )


# -------------------------------
# Compare Button
# -------------------------------

if regulation_file and policy_file:

    st.success("Both documents uploaded successfully!")

    if st.button("🔍 Analyze Compliance", type="primary"):

        with st.spinner("AI is comparing regulatory requirements..."):

            # Replace this with your existing PDF extraction functions
            from pdf_reader import extract_text

            regulation_text = extract_text(regulation_file)
            policy_text = extract_text(policy_file)

            result = compare_compliance(
                regulation_text,
                policy_text
            )

            st.session_state["compliance_result"] = result


# -------------------------------
# Display Results
# -------------------------------

if "compliance_result" in st.session_state:

    result = st.session_state["compliance_result"]

    st.divider()

    st.header("📊 Compliance Assessment Dashboard")

    findings = result.get("findings", [])

    total = len(findings)

    fully = sum(
        1 for f in findings
        if f["status"] == "Fully Compliant"
    )

    partially = sum(
        1 for f in findings
        if f["status"] == "Partially Compliant"
    )

    non_compliant = sum(
        1 for f in findings
        if f["status"] == "Non-Compliant"
    )

    # -------------------------------
    # Summary Cards
    # -------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total Requirements", total)

    with c2:
        st.metric("🟢 Fully Compliant", fully)

    with c3:
        st.metric("🟡 Partially Compliant", partially)

    with c4:
        st.metric("🔴 Non-Compliant", non_compliant)

    # -------------------------------
    # Compliance Percentage
    # -------------------------------

    percentage = result.get("compliance_percentage", 0)

    st.subheader("Overall Compliance Score")

    st.progress(
        max(0, min(100, int(percentage))) / 100
    )

    st.metric(
        "Compliance Percentage",
        f"{percentage}%"
    )

    st.info(result.get("overall_summary", ""))

    st.divider()

    # -------------------------------
    # Detailed Findings
    # -------------------------------

    st.header("📋 Detailed Compliance Findings")

    for finding in findings:

        status = finding.get("status", "Non-Compliant")

        if status == "Fully Compliant":

            card_class = "green-card"
            badge_class = "green-badge"
            icon = "🟢"

        elif status == "Partially Compliant":

            card_class = "yellow-card"
            badge_class = "yellow-badge"
            icon = "🟡"

        else:

            card_class = "red-card"
            badge_class = "red-badge"
            icon = "🔴"

        st.markdown(
            f"""
            <div class="compliance-card {card_class}">

                <h3>
                    {icon} {finding.get("requirement_id", "")}
                </h3>

                <span class="status-badge {badge_class}">
                    {status}
                </span>

                <h4>Regulatory Requirement</h4>
                <p>{finding.get("requirement", "")}</p>

                <h4>Policy Reference</h4>
                <p>{finding.get("policy_reference", "Not Found")}</p>

                <h4>AI Explanation</h4>
                <p>{finding.get("explanation", "")}</p>

                <h4>Recommended Action</h4>
                <p>{finding.get("recommendation", "")}</p>

            </div>
            """,
            unsafe_allow_html=True
        )