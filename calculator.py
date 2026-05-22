"""
calculator.py – IAS 2 konforme Berechnungsfunktionen für Importkosten.

Ausgelagert aus helpers.py im Rahmen von Sprint 0.
"""

from __future__ import annotations

import warnings
from typing import Any

import pandas as pd


# =====================================================================
# Einzelprodukt-Berechnung
# =====================================================================

def calc_single_product(
    params: dict[str, Any],
    ex_rate: float,
    percep_ire_rate: float,
) -> dict[str, float]:
    """Berechnet die Importkosten für ein einzelnes Produkt (IAS 2 konform).

    Die Berechnung berücksichtigt FOB-Wert, Fracht, Versicherung, Inlandtransport,
    Zölle (DAI), VAL, INDI sowie Nebenkosten (Canon, Konsulat, Hafengebühren,
    Spediteur). Der Stückkostenwert wird nach IAS 2 ermittelt, d. h. alle
    zurechenbaren Anschaffungs- und Umladekosten werden aktiviert.

    Args:
        params: Dictionary mit Parametern (siehe Schlüssel unten).
        ex_rate: Wechselkurs PYG/USD.
        percep_ire_rate: IRE-Perception-Rate in Prozent.

    Returns:
        Dictionary mit allen Zwischen- und Endergebnissen (Float-Werte).

    Erwartete Schlüssel in ``params``:
        - p_qty (int): Menge
        - p_fob_usd (float): FOB-Preis pro Stück in USD
        - freight_usd (float): Fracht in USD
        - insurance_usd (float): Versicherung in USD
        - inland_pyg (float): Inlandtransport in PYG
        - inland_iva_incl (bool): Inlandtransport inkl. IVA?
        - dai_rate (float): DAI-Satz in %
        - val_mode (int): 0 = automatisch (0,5 % CIF), sonst manuell
        - val_pyg_input (float): Manueller VAL-Wert in PYG
        - indi_rate (float): INDI-Satz in %
        - canon_sofia (float): Canon Sofia in PYG
        - consulado (float): Konsulatsgebühren in PYG
        - tasa_portuaria (float): Hafengebühren in PYG
        - despachante (float): Spediteur in PYG
        - despachante_iva_incl (bool): Spediteur inkl. IVA?
        - sonstiges (float): Sonstige Kosten in PYG
    """
    p_qty: int = params.get("p_qty", 0)
    p_fob_usd: float = params.get("p_fob_usd", 0.0)
    freight_usd: float = params.get("freight_usd", 0.0)
    insurance_usd: float = params.get("insurance_usd", 0.0)
    inland_pyg: float = params.get("inland_pyg", 0.0)
    inland_iva_incl: bool = params.get("inland_iva_incl", True)
    dai_rate: float = params.get("dai_rate", 0.0)
    val_mode: int = params.get("val_mode", 0)
    val_pyg_input: float = params.get("val_pyg_input", 0.0)
    indi_rate: float = params.get("indi_rate", 0.0)
    canon_sofia: float = params.get("canon_sofia", 0.0)
    consulado: float = params.get("consulado", 0.0)
    tasa_portuaria: float = params.get("tasa_portuaria", 0.0)
    despachante: float = params.get("despachante", 0.0)
    despachante_iva_incl: bool = params.get("despachante_iva_incl", True)
    sonstiges: float = params.get("sonstiges", 0.0)

    total_fob_usd = p_qty * p_fob_usd
    total_fob_pyg = total_fob_usd * ex_rate
    total_freight_pyg = freight_usd * ex_rate
    total_insurance_pyg = insurance_usd * ex_rate

    cif_usd = total_fob_usd + freight_usd + insurance_usd
    cif_pyg = cif_usd * ex_rate

    # Netting Inlandtransport
    if inland_iva_incl:
        inland_netto = inland_pyg / 1.1
        inland_iva = inland_netto * 0.1
    else:
        inland_netto = inland_pyg
        inland_iva = 0.0

    # Netting Spediteur
    if despachante_iva_incl:
        despachante_netto = despachante / 1.1
        despachante_iva = despachante_netto * 0.1
    else:
        despachante_netto = despachante
        despachante_iva = 0.0

    # Zölle und Abgaben
    dai_pyg = cif_pyg * (dai_rate / 100.0)

    if val_mode == 0:
        val_pyg = cif_pyg * 0.005
    else:
        val_pyg = val_pyg_input

    indi_pyg = dai_pyg * (indi_rate / 100.0)

    # Aktivierte Anschaffungskosten (IAS 2)
    capitalized_logistics = total_freight_pyg + total_insurance_pyg + inland_netto
    capitalized_customs = (
        dai_pyg + val_pyg + indi_pyg
        + canon_sofia + consulado + tasa_portuaria + despachante_netto + sonstiges
    )
    total_acquisition_cost = total_fob_pyg + capitalized_logistics + capitalized_customs

    if p_qty > 0:
        unit_cost_pyg = total_acquisition_cost / p_qty
        unit_cost_usd = unit_cost_pyg / ex_rate
    else:
        unit_cost_pyg = 0.0
        unit_cost_usd = 0.0

    # Steuergutschriften (Ley 6380/19) – NICHT aktiviert
    base_iva_aduana = (
        cif_pyg + dai_pyg + val_pyg + indi_pyg
        + canon_sofia + consulado + tasa_portuaria
    )
    iva_importacion = base_iva_aduana * 0.10
    percepcion_ire = cif_pyg * (percep_ire_rate / 100.0)
    total_tax_credit = iva_importacion + percepcion_ire + inland_iva + despachante_iva

    return {
        "total_fob_usd": total_fob_usd,
        "total_fob_pyg": total_fob_pyg,
        "cif_usd": cif_usd,
        "cif_pyg": cif_pyg,
        "inland_netto": inland_netto,
        "inland_iva": inland_iva,
        "despachante_netto": despachante_netto,
        "despachante_iva": despachante_iva,
        "dai_pyg": dai_pyg,
        "val_pyg": val_pyg,
        "indi_pyg": indi_pyg,
        "capitalized_logistics": capitalized_logistics,
        "capitalized_customs": capitalized_customs,
        "total_acquisition_cost": total_acquisition_cost,
        "unit_cost_pyg": unit_cost_pyg,
        "unit_cost_usd": unit_cost_usd,
        "iva_importacion": iva_importacion,
        "percepcion_ire": percepcion_ire,
        "total_tax_credit": total_tax_credit,
        "base_iva_aduana": base_iva_aduana,
    }


# =====================================================================
# Mehrprodukt-Berechnung
# =====================================================================

def calc_multi_product(
    products_df: pd.DataFrame,
    ex_rate: float,
    percep_ire_rate: float,
    multi_freight_usd: float,
    multi_insurance_usd: float,
    multi_inland_pyg: float,
    multi_inland_iva_incl: bool,
    multi_val_mode: int,
    multi_val_pyg_manual: float,
    multi_indi_rate: float,
    multi_canon_sofia: float,
    multi_consulado: float,
    multi_tasa_portuaria: float,
    multi_despachante: float,
    multi_despachante_iva_incl: bool,
    multi_sonstiges: float,
    alloc_freight: int,  # 0 = Gewicht, 1 = Wert
    alloc_local: int,    # 0 = Wert, 1 = Gewicht
) -> dict[str, Any] | None:
    """Berechnet die Importkosten für mehrere Produkte in einer Sendung (IAS 2 konform).

    Gemeinsame Kosten (Fracht, Versicherung, Inlandtransport, Spediteur etc.)
    werden nach Gewicht oder Wert auf die Produkte verteilt.

    Args:
        products_df: DataFrame mit Produktspalten (Produktname, Menge,
            FOB pro Stk. (USD), Gewicht pro Stk. (kg), DAI (%)).
        ex_rate: Wechselkurs PYG/USD.
        percep_ire_rate: IRE-Perception-Rate in Prozent.
        multi_freight_usd: Gesamtfracht in USD.
        multi_insurance_usd: Gesamtversicherung in USD.
        multi_inland_pyg: Gesamt-Inlandtransport in PYG.
        multi_inland_iva_incl: Inlandtransport inkl. IVA?
        multi_val_mode: 0 = automatisch (0,5 % CIF), sonst manuell.
        multi_val_pyg_manual: Manueller VAL-Wert in PYG.
        multi_indi_rate: INDI-Satz in %.
        multi_canon_sofia: Canon Sofia in PYG.
        multi_consulado: Konsulatsgebühren in PYG.
        multi_tasa_portuaria: Hafengebühren in PYG.
        multi_despachante: Spediteur in PYG.
        multi_despachante_iva_incl: Spediteur inkl. IVA?
        multi_sonstiges: Sonstige Kosten in PYG.
        alloc_freight: 0 = Gewicht, 1 = Wert für Fracht/ Versicherung.
        alloc_local: 0 = Wert, 1 = Gewicht für lokale Kosten.

    Returns:
        Dictionary mit angereichertem DataFrame und Summen, oder ``None``
        bei leerem oder ungültigem DataFrame.
    """
    if len(products_df) == 0:
        return None

    # Netting Dienstleistungen
    if multi_inland_iva_incl:
        m_inland_netto = multi_inland_pyg / 1.1
        m_inland_iva = m_inland_netto * 0.1
    else:
        m_inland_netto = multi_inland_pyg
        m_inland_iva = 0.0

    if multi_despachante_iva_incl:
        m_desp_netto = multi_despachante / 1.1
        m_desp_iva = m_desp_netto * 0.1
    else:
        m_desp_netto = multi_despachante
        m_desp_iva = 0.0

    prods = products_df.copy()
    prods["Produktname"] = prods["Produktname"].fillna("-")
    prods["Menge"] = pd.to_numeric(prods["Menge"], errors="coerce").fillna(0).astype(int)
    prods["FOB pro Stk. (USD)"] = pd.to_numeric(prods["FOB pro Stk. (USD)"], errors="coerce").fillna(0.0)
    prods["Gewicht pro Stk. (kg)"] = pd.to_numeric(prods["Gewicht pro Stk. (kg)"], errors="coerce").fillna(0.0)
    prods["DAI (%)"] = pd.to_numeric(prods["DAI (%)"], errors="coerce").fillna(0.0)

    prods["Total_FOB_USD"] = prods["Menge"] * prods["FOB pro Stk. (USD)"]
    prods["Total_Weight_kg"] = prods["Menge"] * prods["Gewicht pro Stk. (kg)"]

    sum_fob_usd = prods["Total_FOB_USD"].sum()
    sum_weight_kg = prods["Total_Weight_kg"].sum()

    if sum_fob_usd <= 0 or sum_weight_kg <= 0:
        return None

    prods["FOB_Share"] = prods["Total_FOB_USD"] / sum_fob_usd
    prods["Weight_Share"] = prods["Total_Weight_kg"] / sum_weight_kg

    # Fracht- & Versicherungsverteilung
    use_weight_freight = alloc_freight == 0
    share_freight = prods["Weight_Share"] if use_weight_freight else prods["FOB_Share"]
    prods["Alloc_Freight_USD"] = multi_freight_usd * share_freight
    prods["Alloc_Insurance_USD"] = multi_insurance_usd * share_freight
    prods["Alloc_Freight_PYG"] = prods["Alloc_Freight_USD"] * ex_rate
    prods["Alloc_Insurance_PYG"] = prods["Alloc_Insurance_USD"] * ex_rate

    # CIF
    prods["CIF_USD"] = prods["Total_FOB_USD"] + prods["Alloc_Freight_USD"] + prods["Alloc_Insurance_USD"]
    prods["CIF_PYG"] = prods["CIF_USD"] * ex_rate

    # Produkt-spezifische Abgaben
    prods["DAI_PYG"] = prods["CIF_PYG"] * (prods["DAI (%)"] / 100.0)

    if multi_val_mode == 0:
        prods["Val_PYG"] = prods["CIF_PYG"] * 0.005
    else:
        use_weight_local = alloc_local == 1
        share_local_val = prods["Weight_Share"] if use_weight_local else prods["FOB_Share"]
        prods["Val_PYG"] = multi_val_pyg_manual * share_local_val

    prods["INDI_PYG"] = prods["DAI_PYG"] * (multi_indi_rate / 100.0)

    # Gemeinsame lokale Kosten verteilen
    total_common_local = (
        multi_canon_sofia + multi_consulado + multi_tasa_portuaria
        + m_desp_netto + multi_sonstiges + m_inland_netto
    )
    use_weight_local = alloc_local == 1
    share_local = prods["Weight_Share"] if use_weight_local else prods["FOB_Share"]
    prods["Alloc_Local_PYG"] = total_common_local * share_local
    prods["Alloc_TaxBase_Fees_PYG"] = (
        multi_canon_sofia + multi_consulado + multi_tasa_portuaria
    ) * share_local

    # Gesamtkosten pro Produkt (IAS 2 aktiviert)
    prods["Total_Capitalized_PYG"] = (
        prods["Total_FOB_USD"] * ex_rate
        + prods["Alloc_Freight_PYG"]
        + prods["Alloc_Insurance_PYG"]
        + prods["DAI_PYG"]
        + prods["Val_PYG"]
        + prods["INDI_PYG"]
        + prods["Alloc_Local_PYG"]
    )
    prods["Stückkosten_PYG"] = prods.apply(
        lambda r: r["Total_Capitalized_PYG"] / r["Menge"] if r["Menge"] > 0 else 0, axis=1
    )
    prods["Stückkosten_USD"] = prods["Stückkosten_PYG"] / ex_rate

    # Steuergutschriften
    prods["IVA_Base_PYG"] = (
        prods["CIF_PYG"] + prods["DAI_PYG"] + prods["Val_PYG"]
        + prods["INDI_PYG"] + prods["Alloc_TaxBase_Fees_PYG"]
    )
    prods["IVA_Importacion_PYG"] = prods["IVA_Base_PYG"] * 0.10
    prods["Percepcion_IRE_PYG"] = prods["CIF_PYG"] * (percep_ire_rate / 100.0)

    prods["Alloc_Inland_IVA"] = m_inland_iva * share_local
    prods["Alloc_Broker_IVA"] = m_desp_iva * share_local

    prods["Total_Tax_Credit_PYG"] = (
        prods["IVA_Importacion_PYG"] + prods["Percepcion_IRE_PYG"]
        + prods["Alloc_Inland_IVA"] + prods["Alloc_Broker_IVA"]
    )

    total_shipment_cap = prods["Total_Capitalized_PYG"].sum()
    total_shipment_credit = prods["Total_Tax_Credit_PYG"].sum()

    return {
        "products_df": prods,
        "total_capitalized": total_shipment_cap,
        "total_tax_credit": total_shipment_credit,
        "inland_iva": m_inland_iva,
        "desp_iva": m_desp_iva,
        "sum_fob_usd": sum_fob_usd,
        "sum_weight_kg": sum_weight_kg,
    }
