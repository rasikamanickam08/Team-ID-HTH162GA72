import re
import fitz
from difflib import SequenceMatcher


# ============================================================
# 1. EXTRACT TEXT FROM PDF
# ============================================================

def extract_pdf_text(pdf_path):
    pages = []

    document = fitz.open(pdf_path)

    for page in document:
        pages.append(page.get_text())

    document.close()

    return "\n".join(pages)


# ============================================================
# 2. EXTRACT REQUIREMENTS FROM REGULATION
# ============================================================

def extract_requirements(text):
    text = re.sub(r"\s+", " ", text)

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    requirements = []

    keywords = [
        "must",
        "shall",
        "required",
        "requirement",
        "should",
        "mandatory",
        "prohibited",
        "retain",
        "protect",
        "encrypt",
        "notify",
        "access",
        "audit"
    ]

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 20:
            continue

        sentence_lower = sentence.lower()

        if any(keyword in sentence_lower for keyword in keywords):

            if sentence not in requirements:
                requirements.append(sentence)

    return requirements


# ============================================================
# 3. CALCULATE SIMILARITY
# ============================================================

def calculate_similarity(requirement, policy_text):

    requirement = requirement.lower()
    policy_text = policy_text.lower()

    # Direct sentence similarity
    similarity = SequenceMatcher(
        None,
        requirement,
        policy_text
    ).ratio()

    # Keyword matching
    requirement_words = set(
        re.findall(r"\b[a-zA-Z]{4,}\b", requirement)
    )

    policy_words = set(
        re.findall(r"\b[a-zA-Z]{4,}\b", policy_text)
    )

    if requirement_words:

        common_words = requirement_words.intersection(policy_words)

        keyword_score = (
            len(common_words) /
            len(requirement_words)
        )

    else:
        keyword_score = 0

    # Combined score
    score = (
        similarity * 0.4 +
        keyword_score * 0.6
    )

    return round(score, 2)


# ============================================================
# 4. ANALYZE COMPLIANCE
# ============================================================

def analyze_compliance(regulation_text, policy_text):

    requirements = extract_requirements(
        regulation_text
    )

    total_requirements = len(requirements)

    fully_compliant = 0
    partially_compliant = 0
    non_compliant = 0

    compliance_results = []

    for requirement in requirements:

        score = calculate_similarity(
            requirement,
            policy_text
        )

        if score >= 0.70:

            status = "Fully Compliant"

            fully_compliant += 1

            risk = "Low"

            action = "No immediate corrective action required."

        elif score >= 0.40:

            status = "Partially Compliant"

            partially_compliant += 1

            risk = "Medium"

            action = (
                "Review the company policy and "
                "add missing regulatory requirements."
            )

        else:

            status = "Non-Compliant"

            non_compliant += 1

            risk = "High"

            action = (
                "Update the company policy to "
                "address this regulatory requirement."
            )

        compliance_results.append({
            "requirement": requirement,
            "status": status,
            "similarity_score": score,
            "risk": risk,
            "corrective_action": action
        })

    # ========================================================
    # OVERALL RISK
    # ========================================================

    if non_compliant > 0:

        overall_risk = "High"

    elif partially_compliant > 0:

        overall_risk = "Medium"

    else:

        overall_risk = "Low"


    # ========================================================
    # OVERALL COMPLIANCE %
    # ========================================================

    if total_requirements > 0:

        compliance_percentage = round(
            (
                (
                    fully_compliant
                    + partially_compliant * 0.5
                )
                / total_requirements
            ) * 100,
            2
        )

    else:

        compliance_percentage = 0


    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "total_requirements": total_requirements,

        "fully_compliant": fully_compliant,

        "partially_compliant": partially_compliant,

        "non_compliant": non_compliant,

        "compliance_percentage": compliance_percentage,

        "overall_risk": overall_risk,

        "compliance": compliance_results
    }