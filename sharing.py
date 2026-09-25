"""
sharing.py - Internal Secure Sharing rules (COMPLYAI).
3 layers: 1) sensitive data scan (dlp.py)  2) role-based access  3) approval workflow
"""

# Demo employee directory (replace with a real database / SSO in production)
EMPLOYEES = {
    "hr_manager":      {"name": "Priya Nair",    "department": "HR",         "role": "manager"},
    "hr_executive":    {"name": "Arun Kumar",    "department": "HR",         "role": "employee"},
    "finance_manager": {"name": "Meena Iyer",    "department": "Finance",    "role": "manager"},
    "finance_analyst": {"name": "Karthik R",     "department": "Finance",    "role": "employee"},
    "it_engineer":     {"name": "Sanjay M",      "department": "IT",         "role": "employee"},
    "ceo":             {"name": "Rajesh Menon",  "department": "Management", "role": "director"},
    "hr_intern":       {"name": "Divya S",       "department": "HR",         "role": "intern"},
    "it_intern":       {"name": "Vikram P",      "department": "IT",         "role": "intern"},
}

ROLE_LEVEL = {"intern": 1, "employee": 2, "manager": 3, "director": 4}

# data category -> which departments AND minimum role level may receive it
ACCESS_RULES = {
    "general":        {"label": "General information",   "departments": ["HR", "Finance", "IT", "Management"], "min_role": "intern"},
    "employee_data":  {"label": "Employee information",  "departments": ["HR", "Management"],                  "min_role": "employee"},
    "salary_data":    {"label": "Salary data",           "departments": ["HR", "Finance", "Management"],       "min_role": "manager"},
    "financial_data": {"label": "Financial data",        "departments": ["Finance", "Management"],             "min_role": "manager"},
    "confidential":   {"label": "Confidential document", "departments": ["Management"],                        "min_role": "manager"},
}
CATEGORY_ORDER = ["general", "employee_data", "salary_data", "financial_data", "confidential"]


def find_approver(sender_id):
    """Approver = another manager/director in the sender's department, else a director."""
    sender = EMPLOYEES.get(sender_id)
    if not sender:
        return None
    for i, e in EMPLOYEES.items():
        if i != sender_id and e["department"] == sender["department"] and e["role"] in ("manager", "director"):
            return i
    for i, e in EMPLOYEES.items():
        if i != sender_id and e["role"] == "director":
            return i
    return None


def evaluate(sender_id, receiver_id, categories):
    """
    Returns {"decision": ALLOWED | APPROVAL_REQUIRED | BLOCKED, "message": str, "checks": [...]}
    """
    if sender_id not in EMPLOYEES or receiver_id not in EMPLOYEES:
        return {"decision": "BLOCKED", "message": "Employee not found.", "checks": []}
    if sender_id == receiver_id:
        return {"decision": "BLOCKED", "message": "Sender and receiver cannot be the same person.", "checks": []}

    if "credentials" in categories:
        return {
            "decision": "BLOCKED",
            "message": "Passwords, API keys and secret tokens must never be shared inside documents. Mask them first.",
            "checks": [],
        }

    receiver = EMPLOYEES[receiver_id]
    checks = []
    for cat in CATEGORY_ORDER:
        if cat not in categories:
            continue
        rule = ACCESS_RULES[cat]
        dept_ok = receiver["department"] in rule["departments"]
        role_ok = ROLE_LEVEL[receiver["role"]] >= ROLE_LEVEL[rule["min_role"]]
        reason = ""
        if not dept_ok:
            reason = f"{receiver['department']} department is not allowed to access {rule['label'].lower()}."
        elif not role_ok:
            reason = f"{rule['label']} needs at least '{rule['min_role']}' level, receiver is '{receiver['role']}'."
        checks.append({"label": rule["label"], "ok": dept_ok and role_ok, "reason": reason})

    if all(c["ok"] for c in checks):
        return {"decision": "ALLOWED", "message": "Receiver is authorized to access this document.", "checks": checks}
    return {
        "decision": "APPROVAL_REQUIRED",
        "message": "The receiver does not currently have access. Manager / admin approval is required.",
        "checks": checks,
    }