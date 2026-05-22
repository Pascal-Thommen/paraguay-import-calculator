"""PDF Export for Paraguay Import Calculator."""
from fpdf import FPDF
import pandas as pd
from datetime import datetime


def _translate(key: str, language: str) -> str:
    """Minimal inline translations for PDF labels."""
    tr = {
        "de": {
            "title": "Paraguay Import Calculator",
            "created": "Erstellt",
            "results": "Berechnungsergebnisse",
            "product": "Produkt",
            "qty": "Menge",
            "fob": "FOB (USD)",
            "cif": "CIF (PYG)",
            "dai": "DAI (PYG)",
            "unit_cost": "Stückkosten (PYG)",
            "unit_cost_usd": "Stückkosten (USD)",
            "tax_credit": "Steuerguthaben (PYG)",
            "total_acquisition": "Gesamte Anschaffungskosten (PYG)",
            "page": "Seite",
        },
        "en": {
            "title": "Paraguay Import Calculator",
            "created": "Created",
            "results": "Calculation Results",
            "product": "Product",
            "qty": "Quantity",
            "fob": "FOB (USD)",
            "cif": "CIF (PYG)",
            "dai": "DAI (PYG)",
            "unit_cost": "Unit Cost (PYG)",
            "unit_cost_usd": "Unit Cost (USD)",
            "tax_credit": "Tax Credit (PYG)",
            "total_acquisition": "Total Acquisition Cost (PYG)",
            "page": "Page",
        },
        "es": {
            "title": "Paraguay Import Calculator",
            "created": "Creado",
            "results": "Resultados del Cálculo",
            "product": "Producto",
            "qty": "Cantidad",
            "fob": "FOB (USD)",
            "cif": "CIF (PYG)",
            "dai": "DAI (PYG)",
            "unit_cost": "Costo Unitario (PYG)",
            "unit_cost_usd": "Costo Unitario (USD)",
            "tax_credit": "Crédito Fiscal (PYG)",
            "total_acquisition": "Costo Total de Adquisición (PYG)",
            "page": "Página",
        },
    }
    return tr.get(language, tr["de"]).get(key, key)


def _fmt_pyg(val):
    return f"Gs. {int(round(val)):,}".replace(",", ".")


def _fmt_usd(val):
    return f"USD {val:,.2f}"


def export_to_pdf(results, language="de", filename="calculation.pdf"):
    """Export calculation results as PDF.

    Args:
        results: dict with calculation results (single product) or
                 a pandas DataFrame (multi-product)
        language: "de", "en", or "es"
        filename: output file path

    Returns:
        filename on success
    """
    lang = language if language in ("de", "en", "es") else "de"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, _translate("title", lang), ln=True, align="C")
    pdf.ln(2)

    # Date
    pdf.set_font("Arial", "", 10)
    pdf.cell(
        0,
        8,
        f"{_translate('created', lang)}: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ln=True,
        align="R",
    )
    pdf.ln(5)

    # Results header
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, _translate("results", lang), ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", "", 10)

    # Determine if single or multi-product
    if isinstance(results, pd.DataFrame):
        # Multi-product mode
        headers = [
            _translate("product", lang),
            _translate("qty", lang),
            _translate("fob", lang),
            _translate("cif", lang),
            _translate("dai", lang),
            _translate("unit_cost", lang),
            _translate("tax_credit", lang),
        ]
        col_widths = [50, 15, 30, 30, 30, 35, 35]

        # Table header
        pdf.set_fill_color(30, 60, 114)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 9)
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 8, h, border=1, fill=True, align="C")
        pdf.ln()

        # Table rows
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 9)
        for _, row in results.iterrows():
            vals = [
                str(row.get("Produktname", "-"))[:28],
                str(int(row.get("Menge", 0))),
                f"{row.get('Total_FOB_USD', 0):,.2f}",
                _fmt_pyg(row.get("CIF_PYG", 0)),
                _fmt_pyg(row.get("DAI_PYG", 0)),
                _fmt_pyg(row.get("Stückkosten_PYG", 0)),
                _fmt_pyg(row.get("Total_Tax_Credit_PYG", 0)),
            ]
            for w, v in zip(col_widths, vals):
                pdf.cell(w, 7, v, border=1, align="R" if w > 30 else "L")
            pdf.ln()

        # Totals
        pdf.set_font("Arial", "B", 9)
        pdf.cell(col_widths[0] + col_widths[1] + col_widths[2], 8, "TOTAL", border=1, align="R")
        pdf.cell(col_widths[3], 8, _fmt_pyg(results["CIF_PYG"].sum()), border=1, align="R")
        pdf.cell(col_widths[4], 8, _fmt_pyg(results["DAI_PYG"].sum()), border=1, align="R")
        pdf.cell(col_widths[5], 8, _fmt_pyg(results["Total_Capitalized_PYG"].sum()), border=1, align="R")
        pdf.cell(col_widths[6], 8, _fmt_pyg(results["Total_Tax_Credit_PYG"].sum()), border=1, align="R")
        pdf.ln()
    else:
        # Single-product mode (dict)
        items = [
            ("FOB (USD)", _fmt_usd(results.get("total_fob_usd", 0))),
            ("CIF (PYG)", _fmt_pyg(results.get("cif_pyg", 0))),
            ("DAI (PYG)", _fmt_pyg(results.get("dai_pyg", 0))),
            ("Valoración Aduanera (PYG)", _fmt_pyg(results.get("val_pyg", 0))),
            ("INDI (PYG)", _fmt_pyg(results.get("indi_pyg", 0))),
            ("IVA Importación (PYG)", _fmt_pyg(results.get("iva_importacion", 0))),
            ("Percepción IRE (PYG)", _fmt_pyg(results.get("percepcion_ire", 0))),
            ("Stückkosten (PYG)", _fmt_pyg(results.get("unit_cost_pyg", 0))),
            ("Stückkosten (USD)", _fmt_usd(results.get("unit_cost_usd", 0))),
            ("Steuerguthaben (PYG)", _fmt_pyg(results.get("total_tax_credit", 0))),
            ("Gesamte Anschaffungskosten (PYG)", _fmt_pyg(results.get("total_acquisition_cost", 0))),
        ]
        for key, value in items:
            pdf.cell(90, 8, key, border=1)
            pdf.cell(0, 8, value, border=1, align="R")
            pdf.ln()

    pdf.output(filename)
    return filename
