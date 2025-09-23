#!/usr/bin/env python3
"""
generate_security_report.py

Self-contained terminal script that:
- Builds an improved security assessment report from context
- Logs auditable events (audit_log.jsonl)
- Stores encrypted transformation mappings (Fernet)
- Tracks simple quality metrics
- Exports final report to security_report.pdf
"""


import os
import json
import datetime
import sys
from getpass import getpass

# External libs
try:
    from markdown import markdown as md_to_html
    from xhtml2pdf import pisa
    from cryptography.fernet import Fernet
except Exception as e:
    print("[ERROR] Missing dependencies. Run: pip install markdown xhtml2pdf cryptography")
    raise

# -------------------------
# Simple Audit Logger
# -------------------------
class AuditLogger:
    def __init__(self, path="audit_log.jsonl"):
        self.path = path
        # Ensure file exists
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                pass

    def log_event(self, component, event_type, details):
        entry = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "component": component,
            "event_type": event_type,
            "details": details
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[AUDIT] {component} | {event_type}")

# -------------------------
# Encrypted Mapping Store (Fernet)
# -------------------------
class EncryptedMappingStore:
    def __init__(self, key: bytes = None, key_env_var: str = "FERNET_KEY"):
        """
        key: optional bytes key for Fernet. If not provided, try env var; if absent, auto-generate and print it.
        """
        self.env_var = key_env_var
        if key is None:
            env = os.environ.get(self.env_var)
            if env:
                key = env.encode("utf-8")
            else:
                # generate a new key and prompt user to save it securely
                key = Fernet.generate_key()
                print("[WARN] No Fernet key found in environment. Generated new key:")
                print(key.decode())
                print("Store this key in the environment variable:", self.env_var)
        self.fernet = Fernet(key)

    def encrypt_mapping(self, mapping_dict):
        plaintext = json.dumps(mapping_dict, ensure_ascii=False).encode("utf-8")
        token = self.fernet.encrypt(plaintext)
        return token.decode("utf-8")

    def decrypt_mapping(self, token_str):
        try:
            plaintext = self.fernet.decrypt(token_str.encode("utf-8"))
            return json.loads(plaintext.decode("utf-8"))
        except Exception as e:
            print("[ERROR] Failed to decrypt mapping:", e)
            return None

# -------------------------
# Quality Metrics
# -------------------------
class QualityMetrics:
    def __init__(self):
        self._metrics = {}

    def update(self, name, value):
        self._metrics[name] = value

    def get_metrics(self):
        return dict(self._metrics)

# -------------------------
# Report generation helpers
# -------------------------
def build_markdown_report(context, encrypted_mapping_token, metrics_data, audit_log_path, audit_excerpt_limit=5):
    """Return a markdown string for the full report."""
    lines = []

    # Executive Summary
    lines.append("<h2 style='font-size: 20px; margin-top: 25px; margin-bottom: 8px;'>Executive Summary</h2>")
    lines.append("<p style='font-size: 15px; margin-top: 0; margin-bottom: 15px;'>This section provides a high-level overview of identified risks with a focus on business impact.</p>")
    # Table: Risks
    lines.append('<table border="1" cellspacing="0" cellpadding="6" width="90%">')
    lines.append("<tr><th>Description</th><th>Business Impact</th></tr>")
    for r in context.get("risks", []):
        desc = r.get("description", "")
        impact = r.get("impact", "")
        lines.append(f"<tr><td>{desc}</td><td>{impact}</td></tr>")
    lines.append("</table>\n")

    # Technical Details
    lines.append("<h2 style='font-size: 20px; margin-top: 25px; margin-bottom: 8px;'>Technical Details</h2>")
    lines.append("<p style='font-size: 15px; margin-top: 0; margin-bottom: 15px;'>Detailed findings with anonymized evidence and mapped compliance controls:</p>")
    lines.append('<table border="1" cellspacing="0" cellpadding="6" width="100%">')
    lines.append("<tr><th>ID</th><th>Evidence</th><th>Risk</th><th>Mapped Compliance</th></tr>")
    compliance_map = context.get("compliance_map", {})
    for f in context.get("findings", []):
        cid = f.get("id", "")
        ev = f.get("evidence", "")
        risk = f.get("risk", "")
        mapping = compliance_map.get(cid, "N/A")
        lines.append(f"<tr><td>{cid}</td><td>{ev}</td><td>{risk}</td><td>{mapping}</td></tr>")
    lines.append("</table>\n")

    # Remediation Roadmap
    lines.append("<h2 style='font-size: 20px; margin-top: 25px; margin-bottom: 8px;'>Remediation Roadmap</h2>")
    lines.append("<p style='font-size: 15px; margin-top: 0; margin-bottom: 15px;'>Prioritized actions with guidance:</p>")
    lines.append('<table border="1" cellspacing="0" cellpadding="6" width="100%">')
    lines.append("<tr><th>Priority</th><th>Action</th><th>Implementation Guidance</th></tr>")
    guidance_map = context.get("guidance_map", {})
    for a in sorted(context.get("actions", []), key=lambda x: x.get("priority", 999)):
        p = a.get("priority", "")
        step = a.get("step", "")
        guidance = guidance_map.get(step, "Refer to internal IT policy.")
        lines.append(f"<tr><td>{p}</td><td>{step}</td><td>{guidance}</td></tr>")
    lines.append("</table>\n")

    # Compliance Report
    lines.append("<h2 style='font-size: 20px; margin-top: 25px; margin-bottom: 8px;'>Compliance Report</h2>")
    lines.append("<p style='font-size: 15px; margin-top: 0; margin-bottom: 15px;'>Mapping to relevant standards:</p>")
    lines.append('<table border="1" cellspacing="0" cellpadding="6" width="80%">')
    lines.append("<tr><th>Standard</th><th>Mapping</th></tr>")
    for item in context.get("compliance", []):
        lines.append(f"<tr><td>{item.get('standard','')}</td><td>{item.get('mapping','')}</td></tr>")
    lines.append("</table>\n")

    # Audit Trail Section
    lines.append("<h2 style='text-align: center; font-size: 20px; margin-top: 30px; margin-bottom: 10px;'>Audit Trail</h2>")
    lines.append("### Process Logging\n")
    lines.append("- Steps performed during anonymization and analysis were logged.\n")
    lines.append("### Transformation Mapping\n")
    lines.append(f"- Encrypted mapping token (store separately for authorized retrieval): `{encrypted_mapping_token}`\n")
    lines.append("### Decision Rationale\n")
    lines.append("- Certain findings were emphasized due to business impact (e.g., ANY→ANY firewall rule flagged as Critical).\n")

    # Quality Metrics (HTML table)
    lines.append("### Quality Metrics\n")
    lines.append('<table border="1" cellspacing="0" cellpadding="5" width="60%">')
    lines.append("<tr><th align='left'>Metric</th><th align='center'>Value</th></tr>")
    for k, v in metrics_data.items():
        lines.append(f"<tr><td>{k}</td><td align='center'>{v}</td></tr>")
    lines.append("</table>\n")

    # Appendices: Audit log extract
    lines.append("<h2 style='text-align: center; font-size: 20px; margin-top: 30px; margin-bottom: 10px;'>Appendices</h2>")

    lines.append("<h2 style='text-align: center; margin-top: 30px; margin-bottom: 15px;'></h2>")
    lines.append("#### Audit Log Extract (first entries)\n")
    if os.path.exists(audit_log_path):
        with open(audit_log_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= audit_excerpt_limit:
                    break
                lines.append(f"- `{line.strip()}`\n")
    else:
        lines.append("- No audit log found.\n")

    # References
    lines.append("## References\n")
    lines.append("- NIST Cybersecurity Framework\n")
    lines.append("- ISO 27001:2013 Security Controls\n")

    return "\n".join(lines)

def export_pdf_from_md(md_text, filename="security_report.pdf"):
    html = md_to_html(md_text, extensions=["extra", "tables", "toc"])
    # Minimal CSS for better PDF rendering
    css = """
    <style>
      body { font-family: DejaVu Sans, Arial, Helvetica, sans-serif; font-size: 12px; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #444; padding: 6px; }
      h1, h2, h3 { text-align: left; }
    </style>
    """
    html_wrapped = "<html><head>" + css + "</head><body>" + html + "</body></html>"
    with open(filename, "wb") as f:
        pisa_status = pisa.CreatePDF(html_wrapped, dest=f)
    if pisa_status.err:
        print("[ERROR] Failed to create PDF. xhtml2pdf reported errors.")
    else:
        print(f"✅ PDF report generated: {filename}")

# -------------------------
# MAIN
# -------------------------
def main():
    # Example context (you can replace / extend this)
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
        ],
        # helpers for table population
        "compliance_map": {
            "F001": "ISO 27001: A.9.2.1",
            "F002": "NIST CSF: PR.AC-1, PR.AC-5"
        },
        "guidance_map": {
            "Patch VPN firmware": "Apply the latest vendor firmware update for your VPN device.",
            "Implement strong password policy": "Configure minimum 12-character complex passwords and enforce rotation policies."
        }
    }

    # Ensure working dir
    cwd = os.getcwd()
    print("Working directory:", cwd)

    # Initialize audit logger
    audit_logger = AuditLogger("audit_log.jsonl")

    # Log some example events (your pipeline would log real events)
    audit_logger.log_event("anonymizer", "mapping_created", {"entity": "user@domain.com", "token": "user_xxx"})
    audit_logger.log_event("analysis", "finding_added", {"id": "F002", "desc": "Firewall rule ANY→ANY"})

    # Key for encrypted mapping: try env var FERNET_KEY, else script will generate & print one
    fernet_env_key = os.environ.get("FERNET_KEY")
    if fernet_env_key:
        key_bytes = fernet_env_key.encode("utf-8")
    else:
        key_bytes = None  # EncryptedMappingStore will generate and print

    store = EncryptedMappingStore(key_bytes)
    enc = store.encrypt_mapping({"original": "user@domain.com", "anonymized": "user_xxx"})
    print("Encrypted mapping token (store safely):", enc)

    # Demonstrate decrypt (only for demo - ensure secure handling in production)
    decrypted = store.decrypt_mapping(enc)
    print("Decrypted mapping (demo):", decrypted)

    # Track quality metrics
    metrics = QualityMetrics()
    metrics.update("anonymization_coverage", 0.95)
    metrics.update("reidentification_risk", 0.02)
    metrics.update("analysis_accuracy", 0.90)

    # Build the markdown report (full)
    md_report = build_markdown_report(
        context=context,
        encrypted_mapping_token=enc,
        metrics_data=metrics.get_metrics(),
        audit_log_path=audit_logger.path,
        audit_excerpt_limit=5
    )

    # Save intermediate markdown and HTML if desired
    with open("security_report.md", "w", encoding="utf-8") as f:
        f.write(md_report)
    print("Saved: security_report.md")

    # Export PDF
    export_pdf_from_md(md_report, filename="security_report.pdf")

    print("\nDone. Files created:")
    for file in ["security_report.md", "security_report.pdf", audit_logger.path]:
        print(" -", os.path.abspath(file))

if __name__ == "__main__":
    main()
