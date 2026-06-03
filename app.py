"""
Paraguay Import Cost Calculator v6 — Streamlit UI.
Produkte-Tabelle + 4 Kostentabellen → Endtabelle mit Summenzeile.
"""
import streamlit as st
from calculator import (
    calculate,
    EINKAUF_DEFAULTS,
    FLETE_DEFAULTS,
    IMPORTACION_DEFAULTS,
    NACIONAL_DEFAULTS,
)

# ── Init ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Paraguay Import Calculator", page_icon="🇵🇾", layout="wide")

# CSS
st.markdown("""<style>
.main-header {background:linear-gradient(135deg,#e63946 0%,#d90429 50%,#003049 100%);padding:1.5rem 2rem;border-radius:12px;color:white;margin-bottom:1.5rem}
.main-header h1{color:white!important;margin:0}
.result-table{width:100%;border-collapse:collapse;margin:1rem 0}
.result-table th{background:#003049;color:white;padding:10px 14px;text-align:right}
.result-table th:first-child{text-align:left}
.result-table td{padding:10px 14px;border-bottom:1px solid #dee2e6;text-align:right;font-family:monospace}
.result-table td:first-child{text-align:left;font-family:sans-serif}
.result-table tr.sum-row td{border-top:2px solid #003049;font-weight:bold;font-size:1.1em}
</style>""", unsafe_allow_html=True)

# ── i18n ────────────────────────────────────────────────────────────────────
TR = {
    "de": {
        "title": "🇵🇾 Paraguay Import-Kostenkalkulator",
        "products": "📦 Produkte",
        "name": "Name",
        "einkaufspreis": "Einkaufspreis",
        "menge": "Menge",
        "maseinheit": "Maßeinheit (kg, m², ...)",
        "einkauf": "🏭 Einkauf (Proveedor)",
        "flete": "🚢 Flete + Seguro",
        "importacion": "🏛️ Importación",
        "nacional": "🚛 Ladeinnere Kosten",
        "beschreibung": "Beschreibung",
        "betrag": "Betrag",
        "aufteilung": "Aufteilung",
        "impuesto": "Impuesto",
        "add_row": "+ Zeile",
        "compute": "🔄 Berechnen",
        "reset": "🗑️ Zurücksetzen",
        "endtabelle": "📊 Endtabelle",
        "kosten_pro_unidad": "Kosten / Unidad",
        "unidades": "Unidades",
        "kosten_total": "Kosten Total",
        "steuern_total": "Steuern Total",
        "total": "Total",
        "summe": "Σ SUMME",
        "kontrollrechnung": "📋 Kontrollrechnung",
        "anteil_ok": "Σ Anteil = 1",
        "betrag_ok": "Kosten + Steuern = Betrag",
        "fob": "FOB",
    },
    "en": {
        "title": "🇵🇾 Paraguay Import Cost Calculator",
        "products": "📦 Products",
        "name": "Name",
        "einkaufspreis": "Purchase Price",
        "menge": "Quantity",
        "maseinheit": "Unit (kg, m², ...)",
        "einkauf": "🏭 Supplier",
        "flete": "🚢 Freight + Insurance",
        "importacion": "🏛️ Import Duties",
        "nacional": "🚛 National Costs",
        "beschreibung": "Description",
        "betrag": "Amount",
        "aufteilung": "Allocation",
        "impuesto": "Tax Class",
        "add_row": "+ Row",
        "compute": "🔄 Calculate",
        "reset": "🗑️ Reset",
        "endtabelle": "📊 Result Table",
        "kosten_pro_unidad": "Cost / Unit",
        "unidades": "Units",
        "kosten_total": "Total Cost",
        "steuern_total": "Total Tax",
        "total": "Total",
        "summe": "Σ TOTAL",
        "kontrollrechnung": "📋 Verification",
        "anteil_ok": "Σ Share = 1",
        "betrag_ok": "Cost + Tax = Amount",
        "fob": "FOB",
    },
    "es": {
        "title": "🇵🇾 Paraguay Calculadora de Costos de Importación",
        "products": "📦 Productos",
        "name": "Nombre",
        "einkaufspreis": "Precio de Compra",
        "menge": "Cantidad",
        "maseinheit": "Unidad (kg, m², ...)",
        "einkauf": "🏭 Proveedor",
        "flete": "🚢 Flete + Seguro",
        "importacion": "🏛️ Importación",
        "nacional": "🚛 Costo Nacional",
        "beschreibung": "Descripción",
        "betrag": "Importe",
        "aufteilung": "Distribución",
        "impuesto": "Impuesto",
        "add_row": "+ Fila",
        "compute": "🔄 Calcular",
        "reset": "🗑️ Reiniciar",
        "endtabelle": "📊 Tabla de Resultados",
        "kosten_pro_unidad": "Costo / Unidad",
        "unidades": "Unidades",
        "kosten_total": "Costo Total",
        "steuern_total": "Impuestos Total",
        "total": "Total",
        "summe": "Σ TOTAL",
        "kontrollrechnung": "📋 Verificación",
        "anteil_ok": "Σ Participación = 1",
        "betrag_ok": "Costo + Impuestos = Importe",
        "fob": "FOB",
    },
}

# ── Language ────────────────────────────────────────────────────────────────
lang = st.sidebar.selectbox("🌐 Sprache / Language / Idioma",
    ["🇩🇪 Deutsch", "🇬🇧 English", "🇪🇸 Español"], key="lang")
lang_code = {"🇩🇪 Deutsch": "de", "🇬🇧 English": "en", "🇪🇸 Español": "es"}[lang]
t = lambda k: TR.get(lang_code, TR["de"]).get(k, k)

# ── Defaults ───────────────────────────────────────────────────────────────
defaults = {
    "products": [{"name": "", "einkaufspreis": 0.0, "menge": 1.0, "maseinheit": 1.0}],
    "einkauf_items": [dict(EINKAUF_DEFAULTS[0])],
    "flete_items": [dict(d) for d in FLETE_DEFAULTS],
    "importacion_items": [dict(d) for d in IMPORTACION_DEFAULTS],
    "nacional_items": [dict(d) for d in NACIONAL_DEFAULTS],
    "result": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers ────────────────────────────────────────────────────────────────
def _fmt(val) -> str:
    try:
        return f"{float(val):,.0f}"
    except (ValueError, TypeError):
        return "0"


def _fmt2(val) -> str:
    try:
        return f"{float(val):,.2f}"
    except (ValueError, TypeError):
        return "0.00"


def _number(label, value, step=1.0, key="", **kwargs):
    return st.number_input(label, value=float(value), step=float(step), key=key, **kwargs)


# ── Recalculate ─────────────────────────────────────────────────────────────
def recalc():
    try:
        result = calculate(
            products=st.session_state.products,
            einkauf=st.session_state.einkauf_items,
            flete=st.session_state.flete_items,
            importacion=st.session_state.importacion_items,
            nacional=st.session_state.nacional_items,
        )
        st.session_state.result = result
    except Exception:
        st.session_state.result = None


recalc()

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="main-header"><h1>{t("title")}</h1></div>', unsafe_allow_html=True)

# ── Reset ───────────────────────────────────────────────────────────────────
c_reset, _ = st.columns([0.15, 0.85])
with c_reset:
    if st.button(t("reset"), key="btn_reset"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# PRODUKTE-TABELLE
# ═══════════════════════════════════════════════════════════════════════════
st.subheader(t("products"))

prods = st.session_state.products
prod_del = []

for i, p in enumerate(prods):
    c1, c2, c3, c4, c5 = st.columns([3, 2, 1.5, 1.5, 0.4])
    with c1:
        p["name"] = st.text_input(
            t("name"), p.get("name", ""), key=f"pn_{i}",
            label_visibility="visible" if i == 0 else "collapsed",
            placeholder=t("name"))
    with c2:
        p["einkaufspreis"] = _number(
            t("einkaufspreis"), p.get("einkaufspreis", 0.0), 0.01,
            f"pe_{i}", label_visibility="visible" if i == 0 else "collapsed")
    with c3:
        p["menge"] = _number(
            t("menge"), p.get("menge", 1.0), 1.0,
            f"pm_{i}", label_visibility="visible" if i == 0 else "collapsed")
    with c4:
        p["maseinheit"] = _number(
            t("maseinheit"), p.get("maseinheit", 0.0), 1.0,
            f"pma_{i}", label_visibility="visible" if i == 0 else "collapsed")
    with c5:
        if st.button("✕", key=f"del_prod_{i}", help="Produkt entfernen"):
            prod_del.append(i)

if prod_del:
    for i in sorted(prod_del, reverse=True):
        if len(st.session_state.products) > 1:
            st.session_state.products.pop(i)
    st.rerun()

if st.button(t("add_row"), key="add_prod"):
    st.session_state.products.append({"name": "", "einkaufspreis": 0.0, "menge": 1.0, "maseinheit": 0.0})
    st.rerun()

# ── FOB Display ─────────────────────────────────────────────────────────────
if st.session_state.result:
    kr = st.session_state.result.get("kontrollrechnung", {})
    st.markdown(f"**FOB:** {_fmt2(kr.get('fob', 0))}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# KOSTENTABELLEN (4x)
# ═══════════════════════════════════════════════════════════════════════════
AUFTEILUNG_OPTIONS = ["Wert", "Maßeinheit", "Menge"]
IMPUESTO_OPTIONS = ["Impuesto", "Anticipo IRE", "IVA CF", "10%", "5%"]


def render_cost_table(title_key, session_key, defaults_list):
    """Render a cost table with add/remove rows. Returns nothing (mutates session_state)."""
    st.subheader(t(title_key))
    items = st.session_state[session_key]
    del_ids = []

    for i, item in enumerate(items):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 0.4])
        with c1:
            item["beschreibung"] = st.text_input(
                t("beschreibung"), item.get("beschreibung", ""),
                key=f"{session_key}_d_{i}",
                label_visibility="visible" if i == 0 else "collapsed")
        with c2:
            step = 0.01 if session_key in ("importacion_items",) else 1.0
            item["betrag"] = _number(
                t("betrag"), item.get("betrag", 0.0), step,
                f"{session_key}_b_{i}",
                label_visibility="visible" if i == 0 else "collapsed")
        with c3:
            cur = item.get("aufteilung", "Wert")
            idx = AUFTEILUNG_OPTIONS.index(cur) if cur in AUFTEILUNG_OPTIONS else 0
            item["aufteilung"] = st.selectbox(
                t("aufteilung"), AUFTEILUNG_OPTIONS, index=idx,
                key=f"{session_key}_a_{i}",
                label_visibility="visible" if i == 0 else "collapsed")
        with c4:
            cur = item.get("impuesto", "Impuesto")
            idx = IMPUESTO_OPTIONS.index(cur) if cur in IMPUESTO_OPTIONS else 0
            item["impuesto"] = st.selectbox(
                t("impuesto"), IMPUESTO_OPTIONS, index=idx,
                key=f"{session_key}_i_{i}",
                label_visibility="visible" if i == 0 else "collapsed")
        with c5:
            if st.button("✕", key=f"del_{session_key}_{i}", help="Zeile entfernen"):
                del_ids.append(i)

    if del_ids:
        for i in sorted(del_ids, reverse=True):
            if len(items) > 1:
                items.pop(i)
        st.rerun()

    if st.button(t("add_row"), key=f"add_{session_key}"):
        items.append(dict(defaults_list[0]))
        st.rerun()


render_cost_table("einkauf", "einkauf_items", EINKAUF_DEFAULTS)
render_cost_table("flete", "flete_items", FLETE_DEFAULTS)
render_cost_table("importacion", "importacion_items", IMPORTACION_DEFAULTS)
render_cost_table("nacional", "nacional_items", NACIONAL_DEFAULTS)

# ═══════════════════════════════════════════════════════════════════════════
# ENDTABELLE
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.result:
    r = st.session_state.result
    st.markdown("---")
    st.subheader(t("endtabelle"))

    html = f'''<table class="result-table">
    <tr>
      <th>{t("name")}</th>
      <th>{t("kosten_pro_unidad")}</th>
      <th>{t("unidades")}</th>
      <th>{t("kosten_total")}</th>
      <th>{t("steuern_total")}</th>
      <th>{t("total")}</th>
    </tr>'''

    for row in r.get("endtabelle", []):
        html += f'''<tr>
          <td>{row["Name"] or "(leer)"}</td>
          <td>{_fmt(row["Kosten pro Unidad"])} Gs</td>
          <td>{_fmt(row["Unidades"])}</td>
          <td>{_fmt(row["Kosten Total"])} Gs</td>
          <td>{_fmt(row["Steuern Total"])} Gs</td>
          <td>{_fmt(row["Total"])} Gs</td>
        </tr>'''

    # Summenzeile
    sz = r.get("summenzeile", {})
    html += f'''<tr class="sum-row">
      <td><b>{t("summe")}</b></td>
      <td>—</td>
      <td>—</td>
      <td><b>{_fmt(sz.get("Kosten Total", 0))} Gs</b></td>
      <td><b>{_fmt(sz.get("Steuern Total", 0))} Gs</b></td>
      <td><b>{_fmt(sz.get("Total", 0))} Gs</b></td>
    </tr>'''
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

    # Kontrollrechnung
    with st.expander(t("kontrollrechnung")):
        kr = r.get("kontrollrechnung", {})
        status_ok = "✅" if kr.get("summe_anteil_gleich_1") else "❌"
        st.write(f"{status_ok} {t('anteil_ok')}")
        status_ok2 = "✅" if kr.get("kosten_plus_steuern_gleich_betrag") else "❌"
        st.write(f"{status_ok2} {t('betrag_ok')} (10%/5%)")
        st.write(f"**{t('fob')}:** {_fmt2(kr.get('fob', 0))}")
