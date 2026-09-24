from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet


def generate_report(
    regulation_name,
    company_name,
    analysis,
    output_path
):
    """
    Generate a PDF compliance report.
    """

    document = SimpleDocTemplate(
        output_path,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "AI Compliance Assistant - Compliance Report",
            styles["Title"]
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            f"<b>Regulation Document:</b> {regulation_name}",
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"<b>Company Policy:</b> {company_name}",
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>AI Compliance Analysis</b>",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 10))

    # Convert line breaks into HTML breaks
    formatted_analysis = analysis.replace(
        "\n",
        "<br/>"
    )

    story.append(
        Paragraph(
            formatted_analysis,
            styles["BodyText"]
        )
    )

    document.build(story)

    return output_path