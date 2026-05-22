from fpdf import FPDF
from datetime import datetime
from helpers import t

def export_to_pdf(results, language="de", filename="calculation.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt=t("pdf_title", language), ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(200, 10, txt=f"{t('pdf_date', language)}: {now}", ln=True, align="R")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=t("pdf_results", language) + ":", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    for key, value in results.items():
        pdf.cell(100, 8, txt=str(key), border=1)
        pdf.cell(90, 8, txt=str(value), border=1, align="R")
        pdf.ln()
    pdf.output(filename)
    return filename
