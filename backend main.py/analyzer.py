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
    # Clean extra spaces
    text = re.sub(r"\s+", " ", text)

    # Split into sentences
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
        "audit",
        "secure",
        "privacy",
        "record",
        "report",
        "maintain"
    ]

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 20:
            continue

        lower_sentence = sentence.lower()

        if any(keyword in lower_sentence for keyword in keywords):
            requirements.append(sentence)

    # Remove duplicates
    unique_requirements = []

    for requirement in requirements:
        if requirement not in unique_requirements:
            unique_requirements.append(requirement)

    return unique_requirements


# ============================================================
# 3. CALCULATE SIMILARITY
# ============================================================

def calculate_similarity(requirement, policy_text):

    requirement_words = set(
        re.findall(r"\b[a-zA-Z0-9]+\b", requirement.lower())
    )

    policy_words = set(
        re.findall(r"\b[a-zA-Z0-9]+\b", policy_text.lower())
    )

    if not requirement_words:
        return 0.0

    common_words = requirement_words.intersection(policy_words)

    keyword_score = (
        len(common_words) / len(requirement_words)
    )

    # Sequence similarity
    sequence_score = SequenceMatcher(
        None,
        requirement.lower(),
        policy_text.lower()
    ).ratio()

    # Combined score
    score = (
        keyword_score * 0.7
        + sequence_score * 0.3
    )

    return round(score * 100, 2)


# ============================================================
# 4. ANALYZE INDIVIDUAL REQUIREMENT
# ============================================================

def analyze_requirement(requirement, policy_text):

    score = calculate_similarity(
        requirement,
        policy_text
    )

    if score >= 70:

        status = "Fully Compliant"
        risk = "Low"

        action = (
            "Requirement appears to be addressed "
            "in the company policy. Maintain the existing control "
            "and review it periodically."
        )

    elif score >= 40:

        status = "Partially Compliant"
        risk = "Medium"

        action = (
            "Review the company policy and add specific controls "
            "or procedures to fully address this requirement."
        )

    else:

        status = "Non-Compliant"
        risk = "High"

        action = (
            "Create or update a policy control that directly "
            "addresses this regulatory requirement."
        )

    return {
        "requirement": requirement,
        "similarity": score,
        "status": status,
        "risk": risk,
        "corrective_action": action
    }


# ============================================================
# 5. MAIN COMPLIANCE ANALYSIS
# ============================================================

def analyze_compliance(regulation_text, policy_text):

    requirements = extract_requirements(
        regulation_text
    )

    results = []

    for requirement in requirements:

        result = analyze_requirement(
            requirement,
            policy_text
        )

        results.append(result)

    total_requirements = len(results)

    fully_compliant = sum(
        1
        for result in results
        if result["status"] == "Fully Compliant"
    )

    partially_compliant = sum(
        1
        for result in results
        if result["status"] == "Partially Compliant"
    )

    non_compliant = sum(
        1
        for result in results
        if result["status"] == "Non-Compliant"
    )

    # Calculate compliance percentage
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

        compliance_percentage = 0.0

    # Determine overall risk
    if non_compliant > 0:

        overall_risk = "High"

    elif partially_compliant > 0:

        overall_risk = "Medium"

    else:

        overall_risk = "Low"

    return {
        "total_requirements": total_requirements,
        "fully_compliant": fully_compliant,
        "partially_compliant": partially_compliant,
        "non_compliant": non_compliant,
        "compliance_percentage": compliance_percentage,
        "overall_risk": overall_risk,
        "results": results
    }


# ============================================================
# 6. OPTIONAL FUNCTION
# ============================================================
# This is included in case your main.py uses analyze_documents.

def analyze_documents(regulation_path, policy_path):

    regulation_text = extract_pdf_text(
        regulation_path
    )

    policy_text = extract_pdf_text(
        policy_path
    )

    return analyze_compliance(
        regulation_text,
        policy_text
    )