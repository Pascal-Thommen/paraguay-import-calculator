"""
Paraguay Import Cost Calculator — Core Engine v6.
Pro-Produkt-Aufteilung nach Berechnungsspezifikation.md.

Input:
- products: list[dict] mit name, einkaufspreis, menge, maseinheit
- 4 Kostentabellen: einkauf, flete, importacion, nacional
  Jede Zeile: beschreibung, betrag, impuesto, aufteilung

Output:
- Endtabelle pro Produkt (Name, Kosten pro Unidad, Unidades, Kosten Total, Steuern Total, Total)
- Summenzeile
- Kontrollrechnungen (Σ anteil = 1, kosten + steuern = betrag)
"""
from dataclasses import dataclass, field
from typing import Literal

ImpuestoTyp = Literal["Impuesto", "Anticipo IRE", "IVA CF", "10%", "5%"]
AufteilungTyp = Literal["Wert", "Maßeinheit", "Menge"]


@dataclass
class Product:
    name: str
    einkaufspreis: float
    menge: float
    maseinheit: float


@dataclass
class CostRow:
    beschreibung: str
    betrag: float
    impuesto: str
    aufteilung: str


@dataclass
class ProductShare:
    """Anteil eines Produkts an einer Zeile."""
    product: Product
    anteil: float


@dataclass
class RowResult:
    """Ergebnis einer einzelnen Zeile (Schritt 1)."""
    row: CostRow
    kosten: float
    steuern: float


@dataclass
class ProductRowResult:
    """Ergebnis einer Zeile für ein bestimmtes Produkt (Schritt 3)."""
    product: Product
    row: CostRow
    kosten: float
    steuern: float


@dataclass
class ProductSummary:
    """Aggregation pro Produkt (Schritt 4)."""
    product: Product
    kosten_total: float
    steuern_total: float
    total: float
    kosten_pro_unidad: float


# ── Default-Templates für die 4 Tabellen ──────────────────────────────────

EINKAUF_DEFAULTS: list[dict] = [
    {"beschreibung": "", "betrag": 0.0, "impuesto": "Impuesto", "aufteilung": "Wert"},
]

FLETE_DEFAULTS: list[dict] = [
    {"beschreibung": "Flete internacional", "betrag": 0.0, "impuesto": "Impuesto", "aufteilung": "Maßeinheit"},
    {"beschreibung": "Seguro",              "betrag": 0.0, "impuesto": "Impuesto", "aufteilung": "Wert"},
]

IMPORTACION_DEFAULTS: list[dict] = [
    {"beschreibung": "Derecho Aduanero",              "betrag": 0.14,  "impuesto": "Impuesto",     "aufteilung": "Wert"},
    {"beschreibung": "Servicio de Valoración Aduanera","betrag": 0.0015,"impuesto": "Impuesto",     "aufteilung": "Wert"},
    {"beschreibung": "INDI",                           "betrag": 0.005, "impuesto": "Impuesto",     "aufteilung": "Wert"},
    {"beschreibung": "Percepción de IRE",              "betrag": 0.004, "impuesto": "Anticipo IRE", "aufteilung": "Wert"},
    {"beschreibung": "Impuesto Selectivo al Consumo",  "betrag": 0.01,  "impuesto": "Impuesto",     "aufteilung": "Wert"},
    {"beschreibung": "IVA",                            "betrag": 0.10,  "impuesto": "IVA CF",       "aufteilung": "Wert"},
    {"beschreibung": "Canon Informático Sofía",        "betrag": 50000.0,"impuesto": "Impuesto",    "aufteilung": "Wert"},
    {"beschreibung": "Visación consular",              "betrag": 30000.0,"impuesto": "Impuesto",    "aufteilung": "Wert"},
    {"beschreibung": "Tasa Portuaria",                 "betrag": 0.0,   "impuesto": "10%",          "aufteilung": "Maßeinheit"},
    {"beschreibung": "Fotocopias",                     "betrag": 5000.0, "impuesto": "10%",          "aufteilung": "Wert"},
    {"beschreibung": "Gastos de Estiba/Desestiba",     "betrag": 25000.0,"impuesto": "10%",          "aufteilung": "Maßeinheit"},
    {"beschreibung": "Honorarios del Despachante",     "betrag": 150000.0,"impuesto": "10%",         "aufteilung": "Wert"},
]

NACIONAL_DEFAULTS: list[dict] = [
    {"beschreibung": "Flete aduana deposito", "betrag": 0.0, "impuesto": "10%", "aufteilung": "Maßeinheit"},
]


# ── Hilfsfunktionen ────────────────────────────────────────────────────────

def _split_kosten_steuern(betrag: float, impuesto: str) -> tuple[float, float]:
    """
    Schritt 1: Kosten & Steuern pro Zeile berechnen.
    """
    imp = impuesto.strip()
    if imp == "Impuesto":
        return betrag, 0.0
    if imp == "Anticipo IRE":
        return 0.0, betrag
    if imp == "IVA CF":
        return betrag, 0.0
    if imp == "10%":
        kosten = betrag / 1.10
        steuern = betrag / 11.0
        return kosten, steuern
    if imp == "5%":
        kosten = betrag / 1.05
        steuern = betrag / 21.0
        return kosten, steuern
    # Fallback: alles als Kosten
    return betrag, 0.0


def _compute_anteile(products: list[Product], aufteilung: str) -> list[float]:
    """
    Schritt 2: Anteil pro Produkt berechnen.
    Returns list of anteile (same order as products).
    """
    auf = aufteilung.strip()
    if auf == "Wert":
        total = sum(p.einkaufspreis for p in products)
        if total == 0:
            return [1.0 / len(products) for _ in products]
        return [p.einkaufspreis / total for p in products]
    if auf == "Maßeinheit":
        total = sum(p.maseinheit for p in products)
        if total == 0:
            return [1.0 / len(products) for _ in products]
        return [p.maseinheit / total for p in products]
    if auf == "Menge":
        total = sum(p.menge for p in products)
        if total == 0:
            return [1.0 / len(products) for _ in products]
        return [p.menge / total for p in products]
    # Fallback
    return [1.0 / len(products) for _ in products]


# ── Hauptberechnung ──────────────────────────────────────────────────────────

def calculate(
    products: list[dict],
    einkauf: list[dict],
    flete: list[dict],
    importacion: list[dict],
    nacional: list[dict],
) -> dict:
    """
    Zentrale Berechnungs-Engine v6.

    Returns dict with:
      - endtabelle: list of dicts (Name, Kosten pro Unidad, Unidades, Kosten Total, Steuern Total, Total)
      - summenzeile: dict (Σ Kosten Total, Σ Steuern Total, Σ Total)
      - details: dict with intermediate step data for UI/debugging
      - kontrollrechnung: dict with verification sums
    """
    # ── Normalisiere Produkte ──────────────────────────────────────────────
    prods = [Product(
        name=p.get("name", ""),
        einkaufspreis=float(p.get("einkaufspreis", 0.0)),
        menge=float(p.get("menge", 0.0)),
        maseinheit=float(p.get("maseinheit", 0.0)),
    ) for p in products]

    if not prods:
        return {
            "endtabelle": [],
            "summenzeile": {"Name": "Σ SUMME", "Kosten pro Unidad": None, "Unidades": None, "Kosten Total": 0.0, "Steuern Total": 0.0, "Total": 0.0},
            "details": {},
            "kontrollrechnung": {},
        }

    # ── Globale Werte ──────────────────────────────────────────────────────
    fob = sum(p.einkaufspreis for p in prods)
    summe_menge = sum(p.menge for p in prods)
    summe_maseinheit = sum(p.maseinheit for p in prods)

    # ── Schritt 1+2+3: Alle Zeilen aller Tabellen durchlaufen ──────────────
    all_tables = [
        ("Einkauf", einkauf),
        ("Flete", flete),
        ("Importación", importacion),
        ("Nacional", nacional),
    ]

    # Pro Produkt: Aggregation
    prod_kosten = {p.name: 0.0 for p in prods}
    prod_steuern = {p.name: 0.0 for p in prods}

    step_details: list[dict] = []

    for table_name, rows in all_tables:
        for row_dict in rows:
            row = CostRow(
                beschreibung=row_dict.get("beschreibung", ""),
                betrag=float(row_dict.get("betrag", 0.0)),
                impuesto=row_dict.get("impuesto", "Impuesto"),
                aufteilung=row_dict.get("aufteilung", "Wert"),
            )

            # Schritt 1
            kosten_zeile, steuern_zeile = _split_kosten_steuern(row.betrag, row.impuesto)

            # Schritt 2
            anteile = _compute_anteile(prods, row.aufteilung)

            # Schritt 3
            row_detail = {
                "tabelle": table_name,
                "beschreibung": row.beschreibung,
                "betrag": row.betrag,
                "impuesto": row.impuesto,
                "aufteilung": row.aufteilung,
                "kosten_zeile": kosten_zeile,
                "steuern_zeile": steuern_zeile,
                "anteile": [],
                "produkt_ergebnisse": [],
            }

            for idx, p in enumerate(prods):
                anteil = anteile[idx]
                k_p = kosten_zeile * anteil
                s_p = steuern_zeile * anteil
                prod_kosten[p.name] += k_p
                prod_steuern[p.name] += s_p
                row_detail["anteile"].append({
                    "produkt": p.name,
                    "anteil": anteil,
                })
                row_detail["produkt_ergebnisse"].append({
                    "produkt": p.name,
                    "kosten": k_p,
                    "steuern": s_p,
                })

            step_details.append(row_detail)

    # ── Schritt 4+5: Endtabelle aufbauen ───────────────────────────────────
    endtabelle: list[dict] = []
    sum_kosten = 0.0
    sum_steuern = 0.0
    sum_total = 0.0

    for p in prods:
        k_total = prod_kosten[p.name]
        s_total = prod_steuern[p.name]
        t_total = k_total + s_total
        k_pro_unidad = k_total / p.menge if p.menge > 0 else 0.0

        endtabelle.append({
            "Name": p.name,
            "Kosten pro Unidad": round(k_pro_unidad, 2),
            "Unidades": p.menge,
            "Kosten Total": round(k_total, 2),
            "Steuern Total": round(s_total, 2),
            "Total": round(t_total, 2),
        })

        sum_kosten += k_total
        sum_steuern += s_total
        sum_total += t_total

    summenzeile = {
        "Name": "Σ SUMME",
        "Kosten pro Unidad": None,
        "Unidades": None,
        "Kosten Total": round(sum_kosten, 2),
        "Steuern Total": round(sum_steuern, 2),
        "Total": round(sum_total, 2),
    }

    # ── Kontrollrechnung ───────────────────────────────────────────────────
    # Σ anteil pro Zeile muss 1 sein
    kontroll_anteil_ok = True
    for d in step_details:
        total_anteil = sum(a["anteil"] for a in d["anteile"])
        if abs(total_anteil - 1.0) > 1e-9:
            kontroll_anteil_ok = False

    # kosten + steuern = betrag für 10% und 5%
    kontroll_betrag_ok = True
    for d in step_details:
        imp = d["impuesto"]
        if imp in ("10%", "5%"):
            zeilen_kosten = d["kosten_zeile"]
            zeilen_steuern = d["steuern_zeile"]
            if abs((zeilen_kosten + zeilen_steuern) - d["betrag"]) > 1e-6:
                kontroll_betrag_ok = False

    kontrollrechnung = {
        "summe_anteil_gleich_1": kontroll_anteil_ok,
        "kosten_plus_steuern_gleich_betrag": kontroll_betrag_ok,
        "fob": round(fob, 2),
        "summe_menge": round(summe_menge, 2),
        "summe_maseinheit": round(summe_maseinheit, 2),
    }

    return {
        "endtabelle": endtabelle,
        "summenzeile": summenzeile,
        "details": {
            "produkte": [{"name": p.name, "einkaufspreis": p.einkaufspreis, "menge": p.menge, "maseinheit": p.maseinheit} for p in prods],
            "zeilen_details": step_details,
        },
        "kontrollrechnung": kontrollrechnung,
    }
