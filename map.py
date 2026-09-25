"""
map.py - Multi-domain requirement -> policy mapping engine (COMPLYAI).

* detect_domain(text)  -> auto-detects the regulation domain
* map_requirements(...) -> maps every requirement to the closest policy clause and
  returns status, severity, AI flag, why, domain-specific corrective action,
  suggested owner and deadline.
Pure Python, no extra libraries needed.
"""

import re

STOPWORDS = set(
    """a an the and or of to in on for with by is are was were be been being as at
    from that this these those it its their there which who whom will shall must
    should may can could would not no any all each such than then also into over
    under per via etc have has had other more most""".split()
)

REQUIREMENT_WORDS = (
    "shall", "must", "should", "required", "require", "ensure",
    "mandatory", "obligat", "need to", "responsible for",
)

# "Article 32", "Section 7", "Clause 4" written at the start of a heading
HEAD_PATTERN = re.compile(r"(?:^|(?<=[.;:] ))((?:Article|Section|Clause)\s+\d+[A-Za-z]?)")

CRITICAL_WORDS = (
    "security", "secure", "breach", "unauthori", "safeguard", "sensitive",
    "confidential", "integrity", "safety",
)

# ------------------------------------------------------------------
# DOMAINS - add a new industry by adding one more entry here
# ------------------------------------------------------------------
DOMAINS = {
    "Law & Order": {
        "emoji": "⚖️",
        "owner": "Legal & compliance head",
        "keywords": ["legal", "court", "offence", "offense", "police", "penalt", "criminal",
                     "law enforcement", "ethic", "bribery", "corruption", "whistleblow",
                     "jurisdiction", "liabilit", "investigation", "sanction"],
        "critical": ["bribery", "corruption", "fraud", "criminal", "penalt", "whistleblow"],
        "actions": [
            (("bribery", "corruption", "gift"),
             "Add an anti-bribery and corruption clause with a gifts register and a duty to report."),
            (("whistleblow", "report"),
             "Create a confidential whistleblowing channel with non-retaliation protection."),
            (("investigat", "police", "authorit"),
             "Define how the company cooperates with investigations and law-enforcement requests."),
            (("penalt", "liabil", "sanction"),
             "Document disciplinary measures and liability for breaches of legal duties."),
            (("conduct", "ethic"),
             "Add a code of conduct / ethics clause that every employee must acknowledge."),
        ],
    },
    "Healthcare": {
        "emoji": "🏥",
        "owner": "Clinical governance lead",
        "keywords": ["patient", "hospital", "clinical", "medical", "healthcare", "medicine",
                     "infection", "nurse", "physician", "treatment", "diagnos", "surgery",
                     "pharmac", "hygiene", "sterili", "medication"],
        "critical": ["patient", "emergency", "infection", "medication", "life"],
        "actions": [
            (("patient data", "patient record", "medical record", "confidential"),
             "Update the patient-data handling procedure (access control, consent, secure storage of medical records)."),
            (("training", "competen", "staff"),
             "Add a staff safety and competency training requirement with annual refresher and records."),
            (("emergency", "evacuat", "resuscit"),
             "Review and test the emergency-response policy (roles, drills, escalation)."),
            (("infection", "hygiene", "sterili"),
             "Add infection-control and hygiene procedures with audit checklists."),
            (("medication", "drug", "prescri"),
             "Define medication management rules (prescribing, storage, dispensing, error reporting)."),
        ],
    },
    "Manufacturing": {
        "emoji": "🏭",
        "owner": "EHS / plant safety manager",
        "keywords": ["factory", "machine", "equipment", "worker", "industrial", "hazard",
                     "occupational", "manufactur", "production", "protective", "fire",
                     "ergonom", "chemical", "plant"],
        "critical": ["hazard", "fire", "machine", "chemical", "injur"],
        "actions": [
            (("ppe", "protective"),
             "Mandate protective equipment (PPE) by task and keep issue and inspection records."),
            (("machine", "equipment", "maintenance"),
             "Add machine safety, lockout/tagout and a preventive maintenance schedule."),
            (("hazard", "risk assessment"),
             "Require documented hazard identification and risk assessment before any new process."),
            (("fire", "evacuat"),
             "Add fire safety rules, evacuation drills and extinguisher inspections."),
            (("chemical", "hazardous"),
             "Add hazardous-substance handling, labelling and storage rules."),
        ],
    },
    "Finance": {
        "emoji": "💳",
        "owner": "Chief compliance officer",
        "keywords": ["bank", "financial", "money laundering", "kyc", "credit", "loan",
                     "investment", "capital", "transaction", "payment", "insurance",
                     "securities", "due diligence", "liquidity"],
        "critical": ["money laundering", "fraud", "kyc", "capital", "suspicious"],
        "actions": [
            (("money laundering", "suspicious"),
             "Add AML procedures: suspicious-transaction monitoring and reporting to the regulator."),
            (("kyc", "due diligence", "identity"),
             "Define KYC / customer due diligence checks with a periodic refresh."),
            (("audit", "record"),
             "Require independent audits and retention of financial records for the legal period."),
            (("fraud",),
             "Add fraud prevention and detection controls with an escalation path."),
            (("capital", "liquidity", "reserve"),
             "Define capital and liquidity monitoring thresholds and regulatory reporting."),
        ],
    },
    "Data & Privacy": {
        "emoji": "🔐",
        "owner": "Data protection officer (DPO)",
        "keywords": ["personal data", "data protection", "privacy", "gdpr", "controller",
                     "processor", "data subject", "consent", "supervisory", "pseudonym",
                     "encrypt", "retention"],
        "critical": ["personal data", "consent", "breach", "encrypt", "notif"],
        "actions": [
            (("encrypt", "cryptograph", "pseudonym"),
             "Add an encryption / pseudonymisation clause to the security policy covering data at rest and in transit."),
            (("breach", "incident", "notif"),
             "Define an incident response and breach notification procedure with clear timelines and owners."),
            (("consent",),
             "Document how valid consent is collected, recorded and withdrawn."),
            (("retention", "retain", "erasure", "delete", "storage limitation"),
             "Define data retention periods and a secure deletion procedure."),
            (("data subject", "right of access", "rectification", "portability"),
             "Create a process to handle data subject requests (access, correction, erasure) within the legal time limit."),
            (("processor", "third part", "vendor", "transfer"),
             "Add third-party / processor agreements and cross-border transfer controls to the policy."),
        ],
    },
    "HR & Employment": {
        "emoji": "👥",
        "owner": "HR head",
        "keywords": ["employee", "employment", "labour", "labor", "wage", "leave",
                     "harass", "discriminat", "recruit", "working hours", "termination",
                     "overtime", "grievance", "payroll"],
        "critical": ["harass", "discriminat", "wage", "safety"],
        "actions": [
            (("harass", "discriminat"),
             "Add an anti-harassment and equal-opportunity clause with a complaints committee."),
            (("wage", "salary", "overtime", "working hours"),
             "Document working hours, overtime and wage payment rules as per labour law."),
            (("leave",),
             "Define leave entitlements and the approval process."),
            (("grievance", "complaint"),
             "Create a grievance redressal procedure with response timelines."),
            (("termination", "dismiss"),
             "Define a fair termination and notice procedure."),
        ],
    },
    "Environment": {
        "emoji": "🌱",
        "owner": "Sustainability / EHS officer",
        "keywords": ["environment", "emission", "waste", "pollution", "carbon",
                     "sustainab", "energy", "water", "climate", "hazardous", "recycl",
                     "discharge"],
        "critical": ["hazardous", "pollution", "emission", "discharge"],
        "actions": [
            (("emission", "carbon", "climate"),
             "Add emission monitoring and reduction targets with periodic reporting."),
            (("waste", "recycl", "discharge"),
             "Define waste segregation, disposal and discharge controls with records."),
            (("energy", "water"),
             "Add energy and water usage monitoring with efficiency targets."),
            (("hazardous", "pollution"),
             "Add pollution-control and hazardous-material handling procedures."),
        ],
    },
}

GENERIC_ACTIONS = [
    (("training", "awareness"),
     "Introduce mandatory periodic awareness training and keep attendance records."),
    (("audit", "monitor", "assess", "review"),
     "Schedule periodic audits / risk assessments and record the results."),
    (("officer", "responsib", "accountab"),
     "Assign a named owner and document responsibilities."),
    (("safeguard", "technical", "organisational", "organizational", "measure", "security"),
     "Add technical and organisational safeguards (access control, logging, backups) to the security policy."),
]

DEADLINE_DAYS = {"Critical": 7, "High": 30, "Medium": 60, "Low": 0}
SEVERITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def _clean(text):
    return re.sub(r"\s+", " ", text or "")


def _tokens(text):
    """Lower-case keyword set with very light stemming."""
    out = set()
    for w in re.findall(r"[a-zA-Z]{3,}", text.lower()):
        if w in STOPWORDS:
            continue
        if w.endswith("ies") and len(w) > 5:
            w = w[:-3] + "y"
        elif w.endswith("s") and len(w) > 4:
            w = w[:-1]
        out.add(w)
    return out


def detect_domain(text):
    """Auto-detect the regulation domain. Returns (domain_name, confidence_percent)."""
    low = _clean(text if isinstance(text, str) else str(text or "")).lower()
    scores = {
        name: sum(low.count(k) for k in info["keywords"])
        for name, info in DOMAINS.items()
    }
    total = sum(scores.values())
    if total == 0:
        return "General", 0
    best = max(scores, key=scores.get)
    return best, round(scores[best] / total * 100)


def _split_with_labels(text):
    """Return [(sentence, heading_label)] where heading_label is e.g. 'Article 32'."""
    text = _clean(text)
    heads = [(m.start(), m.group(1)) for m in HEAD_PATTERN.finditer(text)]
    parts = re.split(r"(?<=[.;:!?])\s+(?=[A-Z0-9(])", text)

    items, cursor = [], 0
    for p in parts:
        p = p.strip()
        if len(p) < 30:
            continue
        pos = text.find(p, cursor)
        if pos >= 0:
            cursor = pos + len(p)
        else:
            pos = cursor
        label = ""
        for hp, hl in heads:
            if hp <= pos:
                label = hl
            else:
                break
        items.append((p, label))
    return items


def extract_requirements(reg_text, max_requirements=40):
    """Pick sentences that look like requirements (shall / must / should ...)."""
    items = _split_with_labels(reg_text)
    reqs = [it for it in items if any(k in it[0].lower() for k in REQUIREMENT_WORDS)]
    if len(reqs) < 3:  # fallback if the document uses different wording
        reqs = items
    return reqs[:max_requirements]


def _severity(status, req, domain):
    if status == "Fully Compliant":
        return "Low"
    if status == "Partially Compliant":
        return "Medium"
    low = req.lower()
    words = list(CRITICAL_WORDS) + DOMAINS.get(domain, {}).get("critical", [])
    return "Critical" if any(k in low for k in words) else "High"


def _action(status, req, domain):
    if status == "Fully Compliant":
        return "No action needed. Re-check during the next policy review cycle."
    low = req.lower()
    owner = DOMAINS.get(domain, {}).get("owner", "a named owner")
    candidates = DOMAINS.get(domain, {}).get("actions", []) + GENERIC_ACTIONS
    for keys, action in candidates:
        if any(k in low for k in keys):
            if status == "Partially Compliant":
                return "Strengthen the existing clause: " + action[0].lower() + action[1:]
            return action
    if status == "Partially Compliant":
        return "Strengthen the existing policy clause so it explicitly covers every part of this requirement."
    return f"Add a new policy clause that addresses this requirement and assign it to: {owner}."


def map_requirements(
    reg_text,
    policy_text,
    domain="Auto-detect",
    full_threshold=0.55,
    partial_threshold=0.30,
    max_requirements=40,
):
    """
    Returns a list of dicts with keys:
    domain, ref, requirement, full_requirement, status, severity, flag, review,
    policy_ref, matched_policy, explanation, action, owner, deadline_days, score
    """
    reg_text = reg_text if isinstance(reg_text, str) else str(reg_text or "")
    policy_text = policy_text if isinstance(policy_text, str) else str(policy_text or "")

    if domain == "Auto-detect" or domain is None:
        domain, _ = detect_domain(reg_text)
    owner = DOMAINS.get(domain, {}).get("owner", "Compliance officer")

    reg_items = extract_requirements(reg_text, max_requirements)
    pol_items = _split_with_labels(policy_text)
    pol_sentences = [s for s, _ in pol_items]
    pol_labels = [l for _, l in pol_items]
    pol_tokens = [_tokens(s) for s in pol_sentences]

    results = []
    for n, (req, label) in enumerate(reg_items, 1):
        req_tokens = _tokens(req)
        best_score, best_idx = 0.0, -1

        for idx, p_tokens in enumerate(pol_tokens):
            if not req_tokens or not p_tokens:
                continue
            score = len(req_tokens & p_tokens) / len(req_tokens)
            if score > best_score:
                best_score, best_idx = score, idx

        pct = round(best_score * 100)
        if best_score >= full_threshold:
            status, flag = "Fully Compliant", "🟢 COMPLIANT"
            why = f"The company policy clearly covers this requirement (best match {pct}%)."
        elif best_score >= partial_threshold:
            status, flag = "Partially Compliant", "🟡 PARTIAL MATCH"
            why = f"The policy touches on this requirement (best match {pct}%) but key parts are missing or unclear."
        else:
            status, flag = "Not Compliant", "🔴 GAP FOUND"
            why = (
                "The regulation requires this control, but the company policy does "
                f"not explicitly mention it (best match {pct}%)."
            )

        matched = best_idx >= 0 and best_score >= partial_threshold
        review = (
            abs(best_score - full_threshold) <= 0.05
            or abs(best_score - partial_threshold) <= 0.05
        )
        severity = _severity(status, req, domain)
        title = req if len(req) <= 110 else req[:107] + "..."

        results.append(
            {
                "domain": domain,
                "ref": label or f"Requirement {n}",
                "requirement": title,
                "full_requirement": req,
                "status": status,
                "severity": severity,
                "flag": flag,
                "review": review,
                "policy_ref": (pol_labels[best_idx] or f"Policy clause {best_idx + 1}") if matched else "No matching clause",
                "matched_policy": pol_sentences[best_idx] if matched else "",
                "explanation": why,
                "action": _action(status, req, domain),
                "owner": owner,
                "deadline_days": DEADLINE_DAYS[severity],
                "score": pct,
            }
        )

    return results