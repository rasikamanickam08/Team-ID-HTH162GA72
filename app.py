import streamlit as st
import os

from pdf_reader import extract_text
from compliance_engine import analyze_compliance
from report_generator import generate_report


st.set_page_config(
    page_title="AI Compliance Assistant",
    page_icon="🛡️",
    layout="wide"
)



st.title("🛡️ AI Compliance Assistant")

st.write(
    "AI-powered compliance checking system for comparing "
    "regulatory requirements with company policies."
)

st.divider()


st.subheader("📄 Upload Compliance Documents")

col1, col2 = st.columns(2)


with col1:

    regulation_file = st.file_uploader(
        "Upload Regulation / Standard PDF",
        type=["pdf"]
    )


with col2:

    company_file = st.file_uploader(
        "Upload Company Policy PDF",
        type=["pdf"]
    )


if regulation_file and company_file:

    st.success(
        "✅ Both documents uploaded successfully!"
    )

    regulation_text = extract_text(
        regulation_file
    )

    company_text = extract_text(
        company_file
    )

    st.divider()

    st.subheader("📋 Document Information")

    info1, info2 = st.columns(2)

    with info1:

        st.write("### 📘 Regulation")
        st.write(regulation_file.name)

        st.write(
            f"Characters extracted: "
            f"{len(regulation_text)}"
        )

    with info2:

        st.write("### 📗 Company Policy")
        st.write(company_file.name)

        st.write(
            f"Characters extracted: "
            f"{len(company_text)}"
        )

    st.divider()

    if st.button(
        "🔍 Analyze Compliance",
        type="primary"
    ):

        with st.spinner(
            "🤖 AI is analyzing the documents..."
        ):

            try:

                analysis = analyze_compliance(
                    regulation_text,
                    company_text
                )

                st.session_state["analysis"] = analysis

            except Exception as error:

                st.error(
                    f"AI analysis failed: {error}"
                )


if "analysis" in st.session_state:

    st.divider()

    st.subheader(
        "🤖 AI Compliance Analysis"
    )

    st.write(
        st.session_state["analysis"]
    )

    st.divider()

    st.subheader(
        "📄 Generate Compliance Report"
    )

    if st.button(
        "Generate PDF Report"
    ):

        os.makedirs(
            "reports",
            exist_ok=True
        )

        report_path = os.path.join(
            "reports",
            "compliance_report.pdf"
        )

        generate_report(
            regulation_file.name,
            company_file.name,
            st.session_state["analysis"],
            report_path
        )

        st.success(
            "✅ Compliance report generated!"
        )

        with open(
            report_path,
            "rb"
        ) as pdf_file:

            st.download_button(
                label="⬇️ Download Compliance Report",
                data=pdf_file,
                file_name="compliance_report.pdf",
                mime="application/pdf"
            )