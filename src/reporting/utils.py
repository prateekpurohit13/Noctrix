from markdown import markdown as md_to_html
from xhtml2pdf import pisa
import os

def export_pdf_from_md(md_text: str, filename: str):
    html = md_to_html(md_text, extensions=["extra", "tables", "toc"])
    css = """
    <style>
      @page { size: A4; margin: 2cm; }
      body { font-family: DejaVu Sans, Arial, Helvetica, sans-serif; font-size: 11px; }
      table { border-collapse: collapse; width: 100%; margin-top: 1em; margin-bottom: 1em; }
      th, td { border: 1px solid #cccccc; padding: 6px; text-align: left; }
      th { background-color: #f2f2f2; }
      h1, h2, h3 { color: #333333; }
      h1 { font-size: 24px; text-align: center; }
      h2 { font-size: 18px; border-bottom: 1px solid #eeeeee; padding-bottom: 5px; }
      h3 { font-size: 14px; }
    </style>
    """
    html_wrapped = f"<html><head>{css}</head><body>{html}</body></html>"
    
    try:
        with open(filename, "wb") as f:
            pisa_status = pisa.CreatePDF(html_wrapped, dest=f)
        
        if pisa_status.err:
            print(f"[ERROR] Failed to create PDF '{filename}'. xhtml2pdf reported errors.")
        else:
            print(f"PDF report generated: {filename}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred during PDF generation for '{filename}': {e}")