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

# ---------- Report generation ----------
gen = ReportGenerator()
report_text = gen.generate_report(context)
# Save report to a file
with open("security_report.md", "w", encoding="utf-8") as f:
    f.write(report_text)

print("✅ Report saved to security_report.md")

# ---------- Audit logging ----------
logger = AuditLogger("audit_log.jsonl")
logger.log_event("anonymizer", "mapping_created", {"entity":"user@domain.com", "token":"user_xxx"})
logger.log_event("analysis", "finding_added", {"id":"F002","desc":"Firewall rule ANY→ANY"})


## Audit Trail




# ---------- Mapping storage ----------
key_str = os.environ.get("AES_KEY", "12345678901234567890123456789012")  # fallback demo key
key = key_str.encode("utf-8")


key = key_str.encode("utf-8")
  # In production: load from KMS or env
store = EncryptedMappingStore(key)
enc = store.encrypt_mapping({"original":"user@domain.com","anonymized":"user_xxx"})
print("Encrypted mapping:", enc)
print("Decrypted mapping:", store.decrypt_mapping(enc))

# ---------- Metrics ----------
#metrics = QualityMetrics()
#metrics.update("anonymization_coverage", 0.95)
#metrics.update("analysis_accuracy", 0.9)
#print("Metrics:", metrics.get_metrics())


 # ------------------- Metrics ------------------------------

metrics = QualityMetrics()  # <--- THIS creates the object

metrics.update("anonymization_coverage", 0.95)   # 95% coverage
metrics.update("reidentification_risk", 0.02)    # 2% risk
metrics.update("analysis_accuracy", 0.9)         # 90% accuracy

print("Updated Metrics:", metrics.get_metrics())

  
#metrics.update("anonymization_coverage", 0.95)  # 95% coverage
#metrics.update("reidentification_risk", 0.02)   # 2% risk
#metrics.update("analysis_accuracy", 0.9)        # 90% accuracy
#Sprint("Updated Metrics:", metrics.get_metrics())


# ---------- Export to PDF without Pandoc ----------
# ---------- Export to PDF (Improved Formatting) ----------
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem

def export_pdf(text, filename="security_report.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=15,
        spaceAfter=10,
    )
    normal_style = styles["Normal"]

    story = []



with open("security_report.md", "w", encoding="utf-8") as f:
    f.write(report_text)
    print("✅ Report saved to security_report.md")
  

with open("security_report.md", "r", encoding="utf-8") as f:
    text = f.read()


# Split report text into sections
for block in text.split("\n\n"):
    if block.startswith("# "):  # Top-level heading
        story.append(Paragraph(block.replace("# ", ""), title_style))
    elif block.startswith("## "):  # Sub-heading
        story.append(Paragraph(block.replace("## ", ""), section_style))
    elif block.startswith("- "):  # Bullet points
        items = [ListItem(Paragraph(line[2:], normal_style)) for line in block.splitlines()]
        story.append(ListFlowable(items, bulletType="bullet"))
    else:  # Normal paragraph
        story.append(Paragraph(block, normal_style))
        story.append(Spacer(1, 12))

doc.build(story)
print(f"✅ PDF report generated: {filename}")















    # Split report text into sections
   # for block in text.split("\n\n"):
       # if block.startswith("# "):  # Top-level heading
       #    story.append(Paragraph(block.replace("# ", ""), title_style))
      #  elif block.startswith("## "):  # Sub-heading
        #    story.append(Paragraph(block.replace("## ", ""), section_style))
        #elif block.startswith("- "):  # Bullet points
         #   items = [ListItem(Paragraph(line[2:], normal_style)) for line in block.splitlines()]
          #  story.append(ListFlowable(items, bulletType="bullet"))
        #else:  # Normal paragraph
         #   story.append(Paragraph(block, normal_style))
          #  story.append(Spacer(1, 12))

    #doc.build(story)
    #Sprint(f"✅ PDF report generated: {filename}")



    # ---------- Report Generation ----------
gen = ReportGenerator()
report_text = gen.generate_report(context)

# Save as Markdown





def export_pdf_from_md(md_text, filename="security_report.pdf"):
    html = markdown(md_text)  # convert Markdown → HTML
    with open(filename, "wb") as f:
        pisa.CreatePDF(html, dest=f)
    print(f"✅ PDF report generated with full Markdown rendering: {filename}")
  


# Call instead of export_pdf
export_pdf_from_md(report_text, "security_report.pdf")



