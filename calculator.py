"""
Paraguay Import Cost Calculator - Core Engine v5.
PYG-zentrierte Währungslogik. Alle Werte werden über PYG umgerechnet.
CIF in PYG ist die Steuerbemessungsgrundlage. Kein Seguro, kein USD-Referenzkurs.
"""
from dataclasses import dataclass, field

DAI_DEFAULT      = 0.14
INDI_RATE        = 0.005
ISC_RATE         = 0.01
IRE_PERCEPCION   = 0.004
IVA_RATE         = 0.10
VALORACION_RATE  = 0.0015

IMPORTACION_DEFAULTS = [
    {"descripcion": "Derecho Aduanero",              "betrag": 0.0, "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Servicio de Valoración Aduanera","betrag": 0.0, "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "INDI",                           "betrag": 0.0, "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Percepción de IRE",              "betrag": 0.0, "aufteilung": "wert",        "impuesto": "Anticipo IRE", "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Impuesto Selectivo al Consumo",  "betrag": 0.0, "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "IVA",                            "betrag": 0.0, "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Canon Informático Sofía",        "betrag": 0.0, "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Visación consular",              "betrag": 0.0, "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Tasa Portuaria",                 "betrag": 0.0, "aufteilung": "masseinheit", "impuesto": "10%",          "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Fotocopias",                     "betrag": 0.0, "aufteilung": "wert",        "impuesto": "10%",          "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Gastos de Estiba/Desestiba",     "betrag": 0.0, "aufteilung": "masseinheit", "impuesto": "10%",          "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Honorarios del Despachante",     "betrag": 0.0, "aufteilung": "wert",        "impuesto": "10%",          "cantidad": 1, "peso_volumen": 0},
]

FLETE_DEFAULTS = [
    {"descripcion": "Flete internacional", "betrag": 0.0, "aufteilung": "masseinheit", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Seguro",              "betrag": 0.0, "aufteilung": "wert",        "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0},
]

NACIONAL_DEFAULTS = [
    {"descripcion": "Flete aduana deposito", "betrag": 0.0, "aufteilung": "masseinheit", "impuesto": "10%", "cantidad": 1, "peso_volumen": 0},
]

PROVEEDOR_DEFAULTS = [
    {"descripcion": "", "betrag": 0.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1.0, "peso_volumen": 0.0},
]


def _iva_factor(impuesto: str) -> float:
    """Return IVA factor: 0.10 for IVA CF/10%, 0.0 otherwise."""
    imp = impuesto.strip().upper()
    if imp in ("IVA CF", "IVA", "5%", "10%"):
        iva_map = {"IVA CF": IVA_RATE, "IVA": IVA_RATE, "10%": IVA_RATE, "5%": 0.05}
        return iva_map.get(imp, 0.0)
    return 0.0


def calculate(
    proveedor: list[dict],
    flete: list[dict],
    importacion: list[dict],
    costo_nacional: list[dict],
    exchange_rate_fob: float,       # FOB-Währung -> PYG
    exchange_rate_flete: float,     # Flete-Währung -> PYG
) -> dict:
    """
    Zentrale Berechnungs-Engine v5. Alles läuft in PYG.
    CIF = FOB + Flete (kein Seguro). CIF in PYG ist die Steuerbemessungsgrundlage.
    Kein USD-Referenzkurs mehr.
    """
    # ═══════════════════════════════════════════════════════════════════════
    # 1. PROVEEDOR -> FOB
    # ═══════════════════════════════════════════════════════════════════════
    fob_currency = 0.0
    total_cantidad = 0.0
    total_peso = 0.0
    prov_out = []

    for it in proveedor:
        iva_f = _iva_factor(it.get("impuesto", "Exento"))
        cantidad = it.get("cantidad", 1.0)
        # Betrag × Menge in FOB-Währung -> PYG (Brutto inkl. IVA falls vorhanden)
        bruto_pyg = it["betrag"] * cantidad * exchange_rate_fob
        sin_iva = bruto_pyg / (1 + iva_f) if iva_f > 0 else bruto_pyg
        iva_gs = bruto_pyg - sin_iva if iva_f > 0 else 0.0

        fob_currency += it["betrag"] * cantidad
        total_cantidad += it.get("cantidad", 1.0)
        total_peso += it.get("peso_volumen", 0.0)

        prov_out.append({**it,
            "betrag_sin_iva": round(sin_iva, 2),
            "costo_gs": round(bruto_pyg, 2),
            "iva_gs": round(iva_gs, 2),
        })

    # FOB in PYG (Brutto)
    fob_gs = round(fob_currency * exchange_rate_fob, 2)

    # ═══════════════════════════════════════════════════════════════════════
    # 2. FLETE -> CIF
    # ═══════════════════════════════════════════════════════════════════════
    flete_out = []
    flete_total_gs = 0.0

    for it in flete:
        iva_f = _iva_factor(it.get("impuesto", "Exento"))

        if it.get("aufteilung") == "monto":
            betrag_pyg = it["betrag"]          # already PYG
            display_betrag = it["betrag"]
        elif it.get("aufteilung") == "masseinheit":
            betrag_pyg = it["betrag"] * exchange_rate_flete * total_peso
            display_betrag = it["betrag"] * total_peso
        elif it.get("aufteilung") == "cantidad":
            betrag_pyg = it["betrag"] * exchange_rate_flete * total_cantidad
            display_betrag = it["betrag"] * total_cantidad
        else:
            betrag_pyg = it["betrag"] * exchange_rate_flete
            display_betrag = it["betrag"]

        sin_iva = betrag_pyg / (1 + iva_f) if iva_f > 0 else betrag_pyg
        iva_gs = betrag_pyg - sin_iva if iva_f > 0 else 0.0
        flete_total_gs += betrag_pyg

        flete_out.append({**it,
            "betrag": display_betrag,
            "betrag_sin_iva": round(sin_iva, 2),
            "costo_gs": round(betrag_pyg, 2),
            "iva_gs": round(iva_gs, 2),
        })

    # CIF in PYG (Steuerbemessungsgrundlage)
    cif_gs = round(fob_gs + flete_total_gs, 2)
    # CIF in Flete-Währung
    cif_currency = round(cif_gs / exchange_rate_flete, 2) if exchange_rate_flete else 0.0

    # ═══════════════════════════════════════════════════════════════════════
    # 3. IMPORTACION - Zollabgaben
    # ═══════════════════════════════════════════════════════════════════════
    imp_out = []
    total_importacion = 0.0

    for it in importacion:
        iva_f = _iva_factor(it.get("impuesto", "Exento"))
        desc = it["descripcion"].lower()

        # Berechnungsbasis
        if it.get("aufteilung") == "monto":
            base = it["betrag"]          # absolute PYG, no CIF percentage
        elif "derecho aduanero" in desc:
            base = cif_gs * (it["betrag"] / 100)
        elif desc == "dai":
            base = cif_gs * (it["betrag"] / 100)
        elif "servicio de valoracion" in desc:
            base = cif_gs * (it["betrag"] / 100)
        elif desc.startswith("indi"):
            base = cif_gs * (it["betrag"] / 100)
        elif "percepcion" in desc and "ire" in desc:
            base = cif_gs * (it["betrag"] / 100)
        elif "consumo" in desc or desc.startswith("isc"):
            base = cif_gs * (it["betrag"] / 100)
        elif desc == "iva":
            base = cif_gs * (it["betrag"] / 100)
        elif it.get("aufteilung") == "masseinheit":
            base = it["betrag"] * total_peso
        elif it.get("aufteilung") == "cantidad":
            base = it["betrag"] * total_cantidad
        else:
            base = it["betrag"]

        sin_iva = base / (1 + iva_f) if iva_f > 0 else base
        iva_gs = base - sin_iva if iva_f > 0 else 0.0
        total_importacion += base

        imp_out.append({**it,
            "betrag_sin_iva": round(sin_iva, 2),
            "costo_gs": round(base, 2),
            "iva_gs": round(iva_gs, 2),
        })

    # ═══════════════════════════════════════════════════════════════════════
    # 4. COSTO NACIONAL
    # ═══════════════════════════════════════════════════════════════════════
    nac_out = []
    total_nacional = 0.0

    for it in costo_nacional:
        iva_f = _iva_factor(it.get("impuesto", "10%"))

        if it.get("aufteilung") == "masseinheit":
            base = it["betrag"] * total_peso
        elif it.get("aufteilung") == "cantidad":
            base = it["betrag"] * total_cantidad
        else:
            base = it["betrag"]

        sin_iva = base / (1 + iva_f) if iva_f > 0 else base
        iva_gs = base - sin_iva if iva_f > 0 else 0.0
        total_nacional += base

        nac_out.append({**it,
            "betrag_sin_iva": round(sin_iva, 2),
            "costo_gs": round(base, 2),
            "iva_gs": round(iva_gs, 2),
        })

    # ═══════════════════════════════════════════════════════════════════════
    # 5. GRAN TOTAL
    # ═══════════════════════════════════════════════════════════════════════
    total_non_fob_costs = round(flete_total_gs + total_importacion + total_nacional, 2)
    gran_total = round(cif_gs + total_importacion + total_nacional, 2)
    gran_total_per_unit = round(gran_total / total_cantidad, 2) if total_cantidad > 0 else 0.0

    # Sum all non-FOB taxes for proportional distribution
    non_fob_taxes = 0.0
    for line in flete_out:
        non_fob_taxes += line["iva_gs"]
    for line in imp_out:
        non_fob_taxes += line["iva_gs"]
    for line in nac_out:
        non_fob_taxes += line["iva_gs"]

    # ═══════════════════════════════════════════════════════════════════════
    # 6. PROVEEDOR SUMMARY (pro-Produkt Endtabelle)
    # ═══════════════════════════════════════════════════════════════════════
    summary = []
    for it in prov_out:
        net = it["betrag_sin_iva"]     # Preis ohne IVA
        tax = it["iva_gs"]             # IVA-Anteil
        total = it["costo_gs"]         # Bruttopreis (FOB in PYG)
        per_unit = round(net / it.get("cantidad", 1.0), 2) if it.get("cantidad", 1.0) > 0 else 0.0
        prod_cantidad = it.get("cantidad", 1.0)

        # FOB-Anteil: product share of total FOB value
        fob_share = (total / fob_gs) if fob_gs > 0 else 0.0

        # Proportional distribution of non-FOB costs and taxes
        kosten_anteilig = round(total + fob_share * total_non_fob_costs, 2)
        steuern_anteilig = round(tax + fob_share * non_fob_taxes, 2)
        kosten_pro_einheit = round(kosten_anteilig / prod_cantidad, 2) if prod_cantidad > 0 else 0.0

        summary.append({
            "descripcion": it["descripcion"],
            "kosten": net,
            "steuern": tax,
            "gesamtbetrag": total,
            "kosten_pro_unidad": per_unit,
            "cantidad": prod_cantidad,
            "menge": prod_cantidad,
            "fob_anteil_pct": round(fob_share * 100, 2),
            "kosten_anteilig": kosten_anteilig,
            "steuern_anteilig": steuern_anteilig,
            "kosten_pro_einheit": kosten_pro_einheit,
            "totalkosten": kosten_anteilig,
            "total_steuern": steuern_anteilig,
        })

    return {
        "fob_currency": fob_currency,
        "fob_gs": fob_gs,
        "flete_total_gs": flete_total_gs,
        "cif_currency": cif_currency,
        "cif_gs": cif_gs,
        "total_importacion": total_importacion,
        "total_nacional": total_nacional,
        "total_non_fob_costs": total_non_fob_costs,
        "gran_total": gran_total,
        "gran_total_per_unit": gran_total_per_unit,
        "proveedor": prov_out,
        "flete": flete_out,
        "importacion": imp_out,
        "costo_nacional": nac_out,
        "proveedor_summary": summary,
    }
