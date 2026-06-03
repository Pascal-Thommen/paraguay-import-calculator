"""
Paraguay Import Cost Calculator — Core Engine v4.
PYG-zentrierte Währungslogik. Alle Werte werden über PYG umgerechnet.
CIF in PYG ist die Steuerbemessungsgrundlage.
"""
from dataclasses import dataclass, field

DAI_DEFAULT      = 0.14
INDI_RATE        = 0.005
ISC_RATE         = 0.01
IRE_PERCEPCION   = 0.004
IVA_RATE         = 0.10
VALORACION_RATE  = 0.0015

IMPORTACION_DEFAULTS = [
    {"descripcion": "Derecho Aduanero",              "betrag": DAI_DEFAULT * 100, "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Servicio de Valoración Aduanera","betrag": VALORACION_RATE * 100, "aufteilung": "wert",  "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "INDI",                           "betrag": INDI_RATE * 100,  "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Percepción de IRE",              "betrag": IRE_PERCEPCION * 100, "aufteilung": "wert",    "impuesto": "Anticipo IRE", "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Impuesto Selectivo al Consumo",  "betrag": ISC_RATE * 100,   "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "IVA",                            "betrag": IVA_RATE * 100,   "aufteilung": "wert",        "impuesto": "IVA CF",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Canon Informático Sofía",        "betrag": 50000.0,          "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Visación consular",              "betrag": 30000.0,          "aufteilung": "wert",        "impuesto": "Exento",       "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Tasa Portuaria",                 "betrag": 0.0,              "aufteilung": "masseinheit", "impuesto": "10%",          "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Fotocopias",                     "betrag": 5000.0,           "aufteilung": "wert",        "impuesto": "10%",          "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Gastos de Estiba/Desestiba",     "betrag": 25000.0,          "aufteilung": "masseinheit", "impuesto": "10%",          "cantidad": 1, "peso_volumen": 0},
    {"descripcion": "Honorarios del Despachante",     "betrag": 150000.0,         "aufteilung": "wert",        "impuesto": "10%",          "cantidad": 1, "peso_volumen": 0},
]

FLETE_DEFAULTS = [
    {"descripcion": "Flete internacional", "betrag": 0.0, "aufteilung": "masseinheit", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0},
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
    exchange_rate_fob: float,       # FOB-Währung → PYG
    exchange_rate_flete: float,     # Flete-Währung → PYG
    exchange_rate_usd: float,       # USD → PYG (für CIF-USD-Anzeige)
    seguro_percent: float,
) -> dict:
    """
    Zentrale Berechnungs-Engine. Alles läuft in PYG.
    CIF ist in PYG. CIF USD wird über exchange_rate_usd berechnet.
    """
    # ═══════════════════════════════════════════════════════════════════════
    # 1. PROVEEDOR → FOB
    # ═══════════════════════════════════════════════════════════════════════
    fob_currency = 0.0
    total_cantidad = 0.0
    total_peso = 0.0
    prov_out = []

    for it in proveedor:
        iva_f = _iva_factor(it.get("impuesto", "Exento"))
        # Betrag in FOB-Währung → PYG (Brutto inkl. IVA falls vorhanden)
        bruto_pyg = it["betrag"] * exchange_rate_fob
        sin_iva = bruto_pyg / (1 + iva_f) if iva_f > 0 else bruto_pyg
        iva_gs = bruto_pyg - sin_iva if iva_f > 0 else 0.0

        fob_currency += it["betrag"]
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
    # 2. SEGURO
    # ═══════════════════════════════════════════════════════════════════════
    seguro_currency = round(fob_currency * seguro_percent / 100, 2)
    seguro_gs = round(seguro_currency * exchange_rate_fob, 2)

    # ═══════════════════════════════════════════════════════════════════════
    # 3. FLETE → CIF
    # ═══════════════════════════════════════════════════════════════════════
    flete_out = []
    flete_total_gs = 0.0

    for it in flete:
        iva_f = _iva_factor(it.get("impuesto", "Exento"))

        if it["descripcion"].lower().startswith("seguro"):
            # Insurance is computed separately from seguro_percent (see §2 above).
            # Skip seguro rows here — do NOT add to flete_total_gs.
            # This prevents overwriting any user-entered value AND prevents
            # double-counting insurance in CIF (cif_gs already adds seguro_gs).
            betrag_pyg = 0.0
            display_betrag = 0.0
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
    cif_gs = round(fob_gs + seguro_gs + flete_total_gs, 2)
    # CIF in USD (Referenz)
    cif_usd = round(cif_gs / exchange_rate_usd, 2) if exchange_rate_usd else 0.0

    # ═══════════════════════════════════════════════════════════════════════
    # 4. IMPORTACIÓN — Zollabgaben
    # ═══════════════════════════════════════════════════════════════════════
    imp_out = []
    total_importacion = 0.0

    for it in importacion:
        iva_f = _iva_factor(it.get("impuesto", "Exento"))
        desc = it["descripcion"].lower()

        # Berechnungsbasis
        if "derecho aduanero" in desc:
            base = cif_gs * (it["betrag"] / 100)
        elif "servicio de valoración" in desc:
            base = cif_gs * VALORACION_RATE
        elif desc.startswith("indi"):
            base = cif_gs * INDI_RATE
        elif "percepción" in desc and "ire" in desc:
            base = cif_gs * IRE_PERCEPCION
        elif "consumo" in desc or desc.startswith("isc"):
            base = cif_gs * ISC_RATE
        elif desc == "iva":
            base = cif_gs * IVA_RATE
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
    # 5. COSTO NACIONAL
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
    # 6. GRAN TOTAL
    # ═══════════════════════════════════════════════════════════════════════
    gran_total = round(cif_gs + total_importacion + total_nacional, 2)
    gran_total_per_unit = round(gran_total / total_cantidad, 2) if total_cantidad > 0 else 0.0

    # ═══════════════════════════════════════════════════════════════════════
    # 7. PROVEEDOR SUMMARY (IAS 2 Netto-Preis)
    # ═══════════════════════════════════════════════════════════════════════
    summary = []
    for it in prov_out:
        net = it["betrag_sin_iva"]     # Preis ohne IVA
        tax = it["iva_gs"]             # IVA-Anteil
        total = it["costo_gs"]         # Bruttopreis
        per_unit = round(net / it.get("cantidad", 1.0), 2) if it.get("cantidad", 1.0) > 0 else 0.0
        summary.append({
            "descripcion": it["descripcion"],
            "kosten": net,
            "steuern": tax,
            "gesamtbetrag": total,
            "kosten_pro_unidad": per_unit,
        })

    return {
        "fob_currency": fob_currency,
        "fob_gs": fob_gs,
        "seguro_currency": seguro_currency,
        "seguro_gs": seguro_gs,
        "flete_total_gs": flete_total_gs,
        "cif_usd": cif_usd,
        "cif_gs": cif_gs,
        "total_importacion": total_importacion,
        "total_nacional": total_nacional,
        "gran_total": gran_total,
        "gran_total_per_unit": gran_total_per_unit,
        "proveedor": prov_out,
        "flete": flete_out,
        "importacion": imp_out,
        "costo_nacional": nac_out,
        "proveedor_summary": summary,
    }
