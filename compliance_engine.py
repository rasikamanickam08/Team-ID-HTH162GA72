import ollama


MODEL_NAME = "llama3.2"


def analyze_compliance(regulation_text, company_text):
    """
    Compare regulatory requirements with company policy
    using the Ollama local AI model.
    """

    prompt = f"""
You are an AI Compliance Assistant.

Your job is to compare a regulatory document
with a company's internal policy.

REGULATORY DOCUMENT:
{regulation_text[:12000]}

COMPANY POLICY:
{company_text[:12000]}

Analyze the documents carefully.

Identify:

1. Compliant requirements
2. Partially compliant requirements
3. Non-compliant or missing requirements
4. Compliance risks
5. Recommended corrective actions

For every important finding, explain why you reached
that conclusion.

Do not invent requirements that are not present
in the regulatory document.

Give the answer in a clear and structured format.
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]