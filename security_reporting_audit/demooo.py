from src.reporting.generator import ReportGenerator
from src.audit.logger import AuditLogger
from src.audit.storage import EncryptedMappingStore
from src.audit.metrics import QualityMetrics
import os
from markdown import markdown
from xhtml2pdf import pisa
import json


# ---------- Context for report ----------
context = {
    "risks": [
        {"description": "Unpatched VPN gateway", "impact": "High"},
        {"description": "Weak password policy", "impact": "Medium"},
    ],
    "findings": [
        {"id": "F001", "evidence": "user@domain.local (anonymized)", "risk": "High"},
        {"id": "F002", "evidence": "Firewall rule ANY→ANY", "risk": "Critical"},
    ],
    "actions": [
        {"priority": 1, "step": "Patch VPN firmware"},
        {"priority": 2, "step": "Implement strong password policy"},
    ],
    "compliance": [
        {"standard": "NIST CSF", "mapping": "PR.AC-1, PR.AC-5"},
        {"standard": "ISO 27001", "mapping": "A.9.2.1 User Access Management"},
    ]
}

report_text = "<h1 style='text-align: center;'>Security Assessment Bulletin</h1>\n"

# ---------- Report generation ----------
#gen = ReportGenerator()
#report_text = gen.generate_report(context)

# ---------- Manually build the bulletin-style report ----------

report_text = "# Security Assessment Bulletin\n"

# ---------- Manually build improved report ----------
report_text = "# Security Assessment Bulletin\n"

# Executive Summary
report_text += "\n## Executive Summary\n"
report_text += "This section provides a high-level overview of identified risks with a focus on business impact.\n\n"
report_text += """
<table border="1" cellspacing="0" cellpadding="6" width="90%">
  <tr><th>Description</th><th>Business Impact</th></tr>
"""
for risk in context["risks"]:
    report_text += f"<tr><td>{risk['description']}</td><td>{risk['impact']}</td></tr>\n"
report_text += "</table>\n"

# Technical Details with Compliance Mapping
report_text += "\n## Technical Details\n"
report_text += "Detailed findings with anonymized evidence and mapped compliance controls:\n"
report_text += """
<table border="1" cellspacing="0" cellpadding="6" width="100%">
  <tr>
    <th>ID</th><th>Evidence</th><th>Risk</th><th>Mapped Compliance</th>
  </tr>
"""
compliance_map = {
    "F001": "ISO 27001: A.9.2.1",
    "F002": "NIST CSF: PR.AC-1, PR.AC-5"
}
for finding in context["findings"]:
    cid = finding["id"]
    mapping = compliance_map.get(cid, "N/A")
    report_text += f"<tr><td>{cid}</td><td>{finding['evidence']}</td><td>{finding['risk']}</td><td>{mapping}</td></tr>\n"
report_text += "</table>\n"

# Remediation Roadmap as Table
report_text += "\n## Remediation Roadmap\n"
report_text += "Prioritized actions with guidance:\n"
report_text += """
<table border="1" cellspacing="0" cellpadding="6" width="100%">
  <tr>
    <th>Priority</th><th>Action</th><th>Implementation Guidance</th>
  </tr>
"""
guidance_map = {
    "Patch VPN firmware": "Apply the latest vendor firmware update for your VPN device.",
    "Implement strong password policy": "Configure minimum 12-character complex passwords and enforce rotation policies."
}
for action in sorted(context["actions"], key=lambda x: x["priority"]):
    guidance = guidance_map.get(action["step"], "Refer to internal IT policy.")
    report_text += f"<tr><td>{action['priority']}</td><td>{action['step']}</td><td>{guidance}</td></tr>\n"
report_text += "</table>\n"

# Compliance Report (unchanged)
report_text += "\n## Compliance Report\n"
report_text += "Mapping to relevant standards:\n"
report_text += """
<table border="1" cellspacing="0" cellpadding="6" width="80%">
  <tr><th>Standard</th><th>Mapping</th></tr>
"""
for item in context["compliance"]:
    report_text += f"<tr><td>{item['standard']}</td><td>{item['mapping']}</td></tr>\n"
report_text += "</table>\n"


with open("security_report.md", "w", encoding="utf-8") as f:
    f.write(report_text)
print("✅ Report saved to security_report.md")

# ---------- Audit logging ----------
logger = AuditLogger("audit_log.jsonl")
logger.log_event("anonymizer", "mapping_created", {"entity": "user@domain.com", "token": "user_xxx"})
logger.log_event("analysis", "finding_added", {"id": "F002", "desc": "Firewall rule ANY→ANY"})

# ---------- Mapping storage ----------
key_str = os.environ.get("AES_KEY", "12345678901234567890123456789012")  # fallback key
key = key_str.encode("utf-8")
store = EncryptedMappingStore(key)
enc = store.encrypt_mapping({"original": "user@domain.com", "anonymized": "user_xxx"})
print("Encrypted mapping:", enc)
print("Decrypted mapping:", store.decrypt_mapping(enc))

# ---------- Metrics ----------
metrics = QualityMetrics()
metrics.update("anonymization_coverage", 0.95)
metrics.update("reidentification_risk", 0.02)
metrics.update("analysis_accuracy", 0.9)
print("Updated Metrics:", metrics.get_metrics())

# ---------- Export to PDF (Markdown -> PDF) ----------
def export_pdf_from_md(md_text, filename="security_report.pdf"):
    html = markdown(md_text, extensions=["extra", "tables", "toc"])
    with open(filename, "wb") as f:
        pisa.CreatePDF(html, dest=f)
    print(f"✅ PDF report generated with full Markdown rendering: {filename}")


    # ---------- Extend report with Audit Trail + Metrics + Appendices ----------

# Load metrics
metrics_data = metrics.get_metrics()

# Build Audit Trail section in Markdown
audit_section = "<h2 style='text-align: center;'>Audit Trail</h2>\n"
#audit_section = "\n\n# Audit Trail\n"
audit_section += "## Process Logging\n"
audit_section += "- Steps performed during anonymization and analysis were logged.\n"

audit_section += "\n## Transformation Mapping\n"
audit_section += f"- Encrypted mapping: `{enc}`\n"

audit_section += "\n## Decision Rationale\n"
audit_section += "- Certain findings were emphasized due to business impact (e.g., ANY→ANY firewall rule flagged as Critical).\n"

# Metrics table
#audit_section += "\n## Quality Metrics\n"
#audit_section += "| Metric | Value |\n|--------|-------|\n"
#for k, v in metrics_data.items():
 #   audit_section += f"| {k} | {v} |\n"


 # Metrics table (better formatting with HTML)
audit_section += "\n## Quality Metrics\n"
audit_section += """
<table border="1" cellspacing="0" cellpadding="5" width="60%">
  <tr>
    <th align="left">Metric</th>
    <th align="center">Value</th>
  </tr>
"""
for k, v in metrics_data.items():
    audit_section += f"  <tr><td>{k}</td><td align='center'>{v}</td></tr>\n"
audit_section += "</table>\n"


# Appendices
audit_section += "<h2 style='text-align: center;'>Appendices</h2>\n"
#audit_section += "\n# Appendices\n"
audit_section += "## Audit Log Extract (first 5 entries)\n"
with open("audit_log.jsonl", "r", encoding="utf-8") as log_file:
    for i, line in enumerate(log_file):
        if i > 4:
            break
        audit_section += f"- {line.strip()}\n"

audit_section += "\n## References\n"
audit_section += "- NIST Cybersecurity Framework\n"
audit_section += "- ISO 27001:2013 Security Controls\n"

# Append audit section to the original report
report_text += audit_section


export_pdf_from_md(report_text, "security_report.pdf")

#def export_pdf_from_md(md_text, filename="security_report.pdf"):
   # print("✅ PDF report successfully generated and saved as : {filename}")

    # Wrap the markdown content in HTML with embedded CSS
