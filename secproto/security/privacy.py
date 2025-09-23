import re
from typing import List, Dict

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s\-]{7,}\d")
ID_RE = re.compile(r"\b[A-Z]{2}\d{6,}\b")

def should_store(field_name: str, value) -> bool:
    # conservative: allow only known safe fields
    allowed = {"filename","purpose","tenant_id","blob_json","created_at"}
    return field_name in allowed

def verify_anonymization(cleansed_text: str, known_pii: List[str]) -> Dict:
    findings = []
    text = cleansed_text or ""
    for token in known_pii or []:
        if token and token.lower() in text.lower():
            findings.append({"type":"direct_match","value":token})
    # regex sweeps
    for m in EMAIL_RE.findall(text):
        findings.append({"type":"email_pattern","value":m})
    for m in PHONE_RE.findall(text):
        findings.append({"type":"phone_pattern","value":m})
    for m in ID_RE.findall(text):
        findings.append({"type":"id_pattern","value":m})
    return {"ok": len(findings)==0, "findings": findings}
