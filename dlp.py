"""
dlp.py - Data Leakage Prevention engine (COMPLYAI).

scan_text(text)  -> list of sensitive findings (type, risk, masked value, line...)
mask_text(text)  -> same text with sensitive values masked
Pure Python, no extra libraries needed.
"""

import re

RISK_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
RISK_COLORS = {
    "Low": "#2e7d32",       # green
    "Medium": "#f9a825",    # yellow
    "High": "#ef6c00",      # orange
    "Critical": "#c62828",  # red
}
RISK_EMOJI = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}

CATEGORY_LABELS = {
    "general": "General information",
    "employee_data": "Employee information",
    "salary_data": "Salary data",
    "financial_data": "Financial data",
    "confidential": "Confidential document",
    "credentials": "Credentials (password / key / token)",
}

SAMPLE_TEXT = """Employee Salary Report - STRICTLY CONFIDENTIAL
Employee ID: EMP1042
Name: Ravi Kumar
PAN: ABCDE1234F
Phone: +91 98765 43210
Email: ravi.kumar@example.com
Salary: Rs. 850000
Bank account number: 123456789012
IFSC: HDFC0001234
Portal password: Ravi@12345
api_key = sk-test1234567890abcdefghijkl
"""


# ------------------------------------------------------------------
# MASKING HELPERS
# ------------------------------------------------------------------
def _keep_last(value, keep=4):
    total = sum(c.isalnum() for c in value)
    out, seen = [], 0
    for c in value:
        if c.isalnum():
            seen += 1
            out.append(c if seen > total - keep else "X")
        else:
            out.append(c)
    return "".join(out)


def _keep4(v):
    return _keep_last(v, 4)


def _keep5(v):
    return _keep_last(v, 5)


def _stars(v):
    return "********"


def _mask_digits(v):
    return re.sub(r"\d", "X", v)


def _mask_email(v):
    local, _, domain = v.partition("@")
    return (local[:1] + "***@" + domain) if local else v


def _luhn(value):
    digits = [int(c) for c in value if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


# ------------------------------------------------------------------
# PATTERNS  (earlier in the list = higher priority when they overlap)
# ------------------------------------------------------------------
PATTERNS = [
    {"name": "Private key", "regex": r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "risk": "Critical",
     "group": 0, "mask": lambda v: "[PRIVATE KEY REMOVED]", "category": "credentials"},
    {"name": "Password", "regex": r"(?i)\b(?:password|passwd|pwd|passcode)\b\s*(?:is|[:=])\s*(\S+)",
     "risk": "Critical", "group": 1, "mask": _stars, "category": "credentials"},
    {"name": "API key / secret token",
     "regex": r"(?i)\b(?:api[_\- ]?key|secret(?:[_\- ]?key)?|access[_\- ]?token|auth[_\- ]?token|token)\b\s*(?:is|[:=])\s*([A-Za-z0-9_\-\./+=]{8,})",
     "risk": "Critical", "group": 1, "mask": _stars, "category": "credentials"},
    {"name": "Cloud / API key",
     "regex": r"\b(?:AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_\-]{30,})\b",
     "risk": "Critical", "group": 0, "mask": _stars, "category": "credentials"},
    {"name": "Credit / debit card", "regex": r"\b(?:\d[ -]?){12,18}\d\b", "risk": "High",
     "group": 0, "mask": _keep4, "validate": _luhn, "category": "financial_data"},
    {"name": "Bank account number",
     "regex": r"(?i)\b(?:account|acct|a/c)\s*(?:no\.?|number|num|#)?\s*(?:is|[:=\-])?\s*(\d{9,18})\b",
     "risk": "High", "group": 1, "mask": _keep4, "category": "financial_data"},
    {"name": "Salary / CTC",
     "regex": r"(?i)\b(?:salary|ctc|compensation|package)\b\s*(?:is|of|[:=\-])?\s*((?:rs\.?|inr|₹|\$)?\s*\d[\d,]{3,})",
     "risk": "High", "group": 1, "mask": _mask_digits, "category": "salary_data"},
    {"name": "PAN number", "regex": r"\b[A-Z]{5}\d{4}[A-Z]\b", "risk": "High",
     "group": 0, "mask": _keep5, "category": "employee_data"},
    {"name": "Aadhaar number",
     "regex": r"(?<!\d)(?<!\d\s)\d{4}\s\d{4}\s\d{4}(?!\s?\d)|(?<!\d)\d{12}(?!\d)",
     "risk": "High", "group": 0, "mask": _keep4, "category": "employee_data"},
    {"name": "IFSC code", "regex": r"\b[A-Z]{4}0[A-Z0-9]{6}\b", "risk": "Medium",
     "group": 0, "mask": _keep4, "category": "financial_data"},
    {"name": "Phone number", "regex": r"(?<!\d)(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)",
     "risk": "Medium", "group": 0, "mask": _keep4, "category": "employee_data"},
    {"name": "Email address", "regex": r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", "risk": "Medium",
     "group": 0, "mask": _mask_email, "category": "employee_data"},
    {"name": "Employee ID",
     "regex": r"(?i)\bemp(?:loyee)?[\s_\-]?(?:id|no|number)\b\s*(?:is|[:=#\-])?\s*([A-Z0-9\-]{3,})",
     "risk": "Medium", "group": 1, "mask": lambda v: _keep_last(v, 3),
     "category": "employee_data"},
    {"name": "Confidential marking",
     "regex": r"(?i)\b(?:strictly confidential|company confidential|proprietary and confidential|internal use only|top secret|trade secret|do not distribute|classified)\b",
     "risk": "High", "group": 0, "mask": None, "category": "confidential"},
]

SUGGESTED_ACTION = {
    "Critical": "Remove now and rotate the secret",
    "High": "Mask before sharing",
    "Medium": "Share only with authorised staff",
}


def scan_text(text):
    """Find sensitive data. Returns findings sorted by position."""
    text = text if isinstance(text, str) else str(text or "")
    cands = []
    for order, p in enumerate(PATTERNS):
        for m in re.finditer(p["regex"], text):
            start, end = m.span(p.get("group", 0))
            if start < 0:
                continue
            value = text[start:end]
            if p.get("validate") and not p["validate"](value):
                continue
            cands.append((-RISK_RANK[p["risk"]], order, -(end - start), start, end, value))

    cands.sort(key=lambda c: c[:5])
    taken, findings = [], []
    for _, order, _, start, end, value in cands:
        if any(start < e and end > s for s, e in taken):
            continue
        taken.append((start, end))
        p = PATTERNS[order]
        masked = p["mask"](value) if p.get("mask") else value
        findings.append(
            {
                "type": p["name"],
                "risk": p["risk"],
                "category": p["category"],
                "value": value,
                "masked": masked,
                "start": start,
                "end": end,
                "line": text.count("\n", 0, start) + 1,
                "action": SUGGESTED_ACTION.get(p["risk"], ""),
                "maskable": bool(p.get("mask")),
            }
        )
    findings.sort(key=lambda f: f["start"])
    return findings


def mask_text(text, findings=None):
    """Return text with every maskable finding replaced by its masked form."""
    text = text if isinstance(text, str) else str(text or "")
    findings = scan_text(text) if findings is None else findings
    for f in sorted(findings, key=lambda f: f["start"], reverse=True):
        if f["maskable"]:
            text = text[: f["start"]] + f["masked"] + text[f["end"]:]
    return text


def overall_risk(findings):
    if not findings:
        return "Low"
    return max((f["risk"] for f in findings), key=lambda r: RISK_RANK[r])


def categories_of(findings):
    """Set of data categories found (used by the sharing permission check)."""
    cats = {f["category"] for f in findings}
    return cats or {"general"}