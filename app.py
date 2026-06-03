"""
Paraguay Import Cost Calculator — Single Container App
Streamlit UI + PostgreSQL DB + Calculator Engine
Direct DB connection, no separate backend.
"""
import streamlit as st
import json
from database import init_db, save_calculation, load_calculation, list_calculations, delete_calculation, update_status
from calculator import calculate, PROVEEDOR_DEFAULTS, FLETE_DEFAULTS, IMPORTACION_DEFAULTS, NACIONAL_DEFAULTS

# ── Init ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Paraguay Import Calculator", page_icon="🇵🇾", layout="wide")

# CSS
st.markdown("""<style>
.main-header {background:linear-gradient(135deg,#e63946 0%,#d90429 50%,#003049 100%);padding:1.5rem 2rem;border-radius:12px;color:white;margin-bottom:1.5rem}
.main-header h1{color:white!important;margin:0}
.value-box{background:#f8f9fa;border:2px solid #dee2e6;border-radius:8px;padding:1rem;text-align:center;font-size:1.2rem;font-weight:600}
.value-box.fob{border-color:#2a9d8f;background:#e9f5f3}
.value-box.cif{border-color:#e63946;background:#fdf0f0}
.value-box.total{border-color:#003049;background:#e8edf1;font-size:1.5rem}
.section-divider{border:none;border-top:3px solid #003049;margin:2rem 0;opacity:0.3}
.result-table{width:100%;border-collapse:collapse;margin:1rem 0}
.result-table th{background:#003049;color:white;padding:10px 14px;text-align:right}
.result-table th:first-child{text-align:left}
.result-table td{padding:10px 14px;border-bottom:1px solid #dee2e6;text-align:right;font-family:monospace}
.result-table td:first-child{text-align:left;font-family:sans-serif}
.result-table tr.total-row td{border-top:2px solid #003049;font-weight:bold;font-size:1.1em}
.copy-hint{color:#6c757d;font-size:0.85rem;margin-top:0.5rem}
</style>
<script>
// Unterdrücke Streamlit Ctrl+C Cache-Dialog — lasse natives Copy zu
window.addEventListener("keydown", function(e) {
  if (e.ctrlKey && e.key === "c" && !window.getSelection().toString()) {
    // Kein Text selektiert? Nichts tun, Dialog erscheint trotzdem.
    // Bei Textselektion: natives Copy läuft.
  }
}, true);
document.addEventListener("keydown", function(e) {
  if (e.ctrlKey && e.key === "c") {
    // Stoppe Propagation NICHT — lass natives Copy durch
  }
}, true);
</script>""", unsafe_allow_html=True)

# DB init on first access — resilient against connection failures
if "db_initialized" not in st.session_state:
    try:
        init_db()
        st.session_state.db_initialized = True
    except Exception:
        st.session_state.db_initialized = False  # will retry next render
    import uuid
    if "session_user" not in st.session_state or not st.session_state.session_user:
        st.session_state.session_user = str(uuid.uuid4())[:8]

# ── i18n ────────────────────────────────────────────────────────────────────
TR = {
    "de": {
        "title": "🇵🇾 Paraguay Import-Kostenkalkulator",
        "subtitle": "IAS 2 · Ley 6380/19 · FOB → CIF → Costo por Unidad",
        "currency_fob": "Währung (FOB)",
        "exchange_fob": "Wechselkurs (Währung/PYG)",
        "purchase_unit": "Einkaufsmaßeinheit (m², kg, t, ...)",
        "proveedor": "📦 Proveedor (Lieferant)",
        "flete": "🚢 Flete Internacional",
        "importacion": "🏛️ Importación",
        "costo_nacional": "🚛 Costo Nacional",
        "descripcion": "Beschreibung",
        "betrag": "Betrag",
        "aufteilung": "Aufteilung",
        "impuesto": "Impuesto",
        "cantidad": "Cantidad",
        "peso_volumen": "Gewicht/Volumen",
        "compute": "🔄 Berechnen",
        "reset": "🗑️ Zurücksetzen",
        "ergebnis": "📊 ERGEBNIS — Kosten pro Unidad",
        "kosten": "Kosten",
        "steuern": "Steuern",
        "gesamtbetrag": "Gesamtbetrag",
        "kosten_pro_unidad": "Kosten / Unidad",
        "summe": "SUMME",
        "gran_total": "Gran Total",
        "fob_currency": "FOB (Währung)",
        "fob_gs": "FOB (Gs)",
        "cif_currency": "CIF (Währung)",
        "cif_gs": "CIF Gs",
        "waehrung_flete": "Flete-Währung",
        "wechselkurs_flete": "Wechselkurs (Flete)",
        "betrag_ohne_iva": "Betrag ohne IVA",
    },
    "en": {
        "title": "🇵🇾 Paraguay Import Cost Calculator",
        "subtitle": "IAS 2 · Ley 6380/19 · FOB → CIF → Cost per Unit",
        "currency_fob": "Currency (FOB)",
        "exchange_fob": "Exchange Rate (Currency/PYG)",
        "purchase_unit": "Purchase Unit (m², kg, t, ...)",
        "proveedor": "📦 Supplier",
        "flete": "🚢 International Freight",
        "importacion": "🏛️ Import Duties",
        "costo_nacional": "🚛 National Costs",
        "descripcion": "Description",
        "betrag": "Amount",
        "aufteilung": "Allocation",
        "impuesto": "Tax Class",
        "cantidad": "Quantity",
        "peso_volumen": "Weight/Volume",
        "compute": "🔄 Calculate",
        "reset": "🗑️ Reset",
        "ergebnis": "📊 RESULT — Cost per Unit",
        "kosten": "Cost",
        "steuern": "Tax",
        "gesamtbetrag": "Total",
        "kosten_pro_unidad": "Cost / Unit",
        "summe": "TOTAL",
        "gran_total": "Grand Total",
        "fob_currency": "FOB (Currency)",
        "fob_gs": "FOB (Gs)",
        "cif_currency": "CIF (Currency)",
        "cif_gs": "CIF Gs",
        "waehrung_flete": "Freight Currency",
        "wechselkurs_flete": "Exchange Rate (Freight)",
        "betrag_ohne_iva": "Amount excl. IVA",
    },
    "es": {
        "title": "🇵🇾 Paraguay Calculadora de Costos de Importación",
        "subtitle": "IAS 2 · Ley 6380/19 · FOB → CIF → Costo por Unidad",
        "currency_fob": "Moneda (FOB)",
        "exchange_fob": "Tipo de Cambio (Moneda/PYG)",
        "purchase_unit": "Unidad de Compra (m², kg, t, ...)",
        "proveedor": "📦 Proveedor",
        "flete": "🚢 Flete Internacional",
        "importacion": "🏛️ Importación",
        "costo_nacional": "🚛 Costo Nacional",
        "descripcion": "Descripción",
        "betrag": "Importe",
        "aufteilung": "Distribución",
        "impuesto": "Impuesto",
        "cantidad": "Cantidad",
        "peso_volumen": "Peso/Volumen",
        "compute": "🔄 Calcular",
        "reset": "🗑️ Reiniciar",
        "ergebnis": "📊 RESULTADO — Costo por Unidad",
        "kosten": "Costo",
        "steuern": "Impuestos",
        "gesamtbetrag": "Total",
        "kosten_pro_unidad": "Costo / Unidad",
        "summe": "TOTAL",
        "gran_total": "Gran Total",
        "fob_currency": "FOB (Moneda)",
        "fob_gs": "FOB (Gs)",
        "cif_currency": "CIF (Moneda)",
        "cif_gs": "CIF Gs",
        "waehrung_flete": "Moneda Flete",
        "wechselkurs_flete": "Tipo de Cambio (Flete)",
        "betrag_ohne_iva": "Importe sin IVA",
    },
}

# ── Language ────────────────────────────────────────────────────────────────
lang = st.sidebar.selectbox("🌐 Sprache / Language / Idioma",
    ["🇩🇪 Deutsch", "🇬🇧 English", "🇪🇸 Español"], key="lang")
lang_code = {"🇩🇪 Deutsch": "de", "🇬🇧 English": "en", "🇪🇸 Español": "es"}[lang]
t = lambda k: TR.get(lang_code, TR["de"]).get(k, k)

# ── Sidebar Navigation ──
st.sidebar.markdown("---")

# Handle redirects BEFORE widget creation (rerun picks up the value)
if st.session_state.get("nav_redirect"):
    st.session_state.nav_redirect = False
    st.session_state.page_nav = "🧮 Kalkulator"
    st.rerun()

# Determine index from current session state
nav_options = ["🧮 Kalkulator", "📋 Mein Verlauf", "⚙️ Admin"]
current = st.session_state.get("page_nav", nav_options[0])
nav_index = nav_options.index(current) if current in nav_options else 0
page = st.sidebar.radio("Navigation", ["🧮 Kalkulator", "📋 Mein Verlauf", "⚙️ Admin"],
    index=nav_index,
    key="page_nav",
    help="Kalkulator = Berechnung | Mein Verlauf = deine gespeicherten Berechnungen | Admin = alle Berechnungen")
st.sidebar.markdown("---")

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="main-header"><h1>{t("title")}</h1><p>{t("subtitle")}</p></div>', unsafe_allow_html=True)

# ── Session State Init ──────────────────────────────────────────────────────
defaults = {
    "currency_fob": "USD", "exchange_rate_fob": 7500.0, "purchase_unit": "kg",
    "currency_flete": "USD", "exchange_rate_flete": 7500.0,
    "result": None, "calc_id": None, "calc_name": "",
    "proveedor_items": [dict(PROVEEDOR_DEFAULTS[0])],
    "flete_items": [dict(d) for d in FLETE_DEFAULTS],
    "importacion_items": [dict(d) for d in IMPORTACION_DEFAULTS],
    "nacional_items": [dict(d) for d in NACIONAL_DEFAULTS],
    "show_iva_detail": False,
    "session_user": "",  # filled on startup
    "nav_redirect": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helper: number_input that doesn't eat integers ──────────────────────────
def number_input(label, value, step=1.0, key="", **kwargs):
    """Wraps st.number_input with float coercion to prevent disappearing integers."""
    return st.number_input(label, value=float(value), step=float(step), key=key, **kwargs)


def _fmt(val) -> str:
    try:
        return f"{float(val):,.0f}"
    except (ValueError, TypeError):
        return "0"


def _date_str(val):
    """Safe date conversion for psycopg2 datetime objects."""
    if val is None:
        return ""
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d %H:%M")
    return str(val)[:16]


def _fmt2(val) -> str:
    try:
        return f"{float(val):,.2f}"
    except (ValueError, TypeError):
        return "0.00"




# ── Dynamic recalculation (runs on every render) ──
def recalc():
    try:
        result = calculate(
            proveedor=st.session_state.proveedor_items,
            flete=st.session_state.flete_items,
            importacion=st.session_state.importacion_items,
            costo_nacional=st.session_state.nacional_items,
            exchange_rate_fob=st.session_state.exchange_rate_fob,
            exchange_rate_flete=st.session_state.exchange_rate_flete,
        )
        st.session_state.result = result
    except Exception as e:
        st.session_state.result = None

recalc()

# ── Session-local history ──
if "session_history" not in st.session_state:
    st.session_state.session_history = []  # list of calc_ids saved this session

if page == "🧮 Kalkulator":

    # ═══════════════════════════════════════════════════════════════════════════
    # RESET BUTTON — ganz oben
    # ═══════════════════════════════════════════════════════════════════════════
    c_reset, _ = st.columns([0.15, 0.85])
    with c_reset:
        if st.button(t("reset"), key="btn_reset_top"):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # OBERER BEREICH — EINGABEN
    # ═══════════════════════════════════════════════════════════════════════════

    # ── Proveedor Header Inputs ─────────────────────────────────────────────────
    st.subheader(t("proveedor"))
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.currency_fob = st.text_input(t("currency_fob"), st.session_state.currency_fob, key="inp_cfob")
    with col2:
        # Synchronize exchange rates when both currencies match (shared rate)
        if "exchange_rate_common" not in st.session_state:
            st.session_state.exchange_rate_common = st.session_state.exchange_rate_fob
        same_currency = st.session_state.currency_fob.upper() == st.session_state.currency_flete.upper()
        if same_currency:
            st.session_state.exchange_rate_common = number_input(t("exchange_fob"), st.session_state.exchange_rate_common, 100.0, "inp_xfob")
            st.session_state.exchange_rate_fob = st.session_state.exchange_rate_common
            st.session_state.exchange_rate_flete = st.session_state.exchange_rate_common
        else:
            st.session_state.exchange_rate_fob = number_input(t("exchange_fob"), st.session_state.exchange_rate_fob, 100.0, "inp_xfob")

    col3 = st.columns(1)[0]
    with col3:
        st.session_state.purchase_unit = st.text_input(t("purchase_unit"), st.session_state.purchase_unit, key="inp_unit")

    # ── Proveedor Table ─────────────────────────────────────────────────────────
    prov = st.session_state.proveedor_items
    del_ids = []
    for i, item in enumerate(prov):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 1, 0.4])
        with c1:
            item["descripcion"] = st.text_input(t("descripcion"), item.get("descripcion", ""), key=f"pd_{i}", label_visibility="visible" if i == 0 else "collapsed", placeholder=t("descripcion"))
        with c2:
            item["betrag"] = number_input(t("betrag"), item.get("betrag", 0.0), 0.01, f"pb_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c3:
            item["cantidad"] = number_input(t("cantidad"), item.get("cantidad", 1.0), 1.0, f"pc_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c4:
            item["peso_volumen"] = number_input(t("peso_volumen"), item.get("peso_volumen", 0.0), 1.0, f"pp_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c5:
            if st.button("✕", key=f"del_prov_{i}", help="Diese Zeile entfernen"):
                del_ids.append(i)

    if del_ids:
        for i in sorted(del_ids, reverse=True):
            if len(st.session_state.proveedor_items) > 1:
                st.session_state.proveedor_items.pop(i)
        st.rerun()

    if st.button("+ Zeile", key="add_prov"):
        st.session_state.proveedor_items.append(dict(PROVEEDOR_DEFAULTS[0]))
        st.rerun()

    # ── FOB Display ─────────────────────────────────────────────────────────────
    if st.session_state.result:
        r = st.session_state.result
        cf1, cf2 = st.columns(2)
        with cf1:
            st.markdown(f'<div class="value-box fob">FOB ({st.session_state.currency_fob})<br><b>{_fmt(r["fob_currency"])}</b></div>', unsafe_allow_html=True)
        with cf2:
            st.markdown(f'<div class="value-box fob">FOB Gs<br><b>{_fmt(r["fob_gs"])} Gs</b></div>', unsafe_allow_html=True)

    # ── Flete Header Inputs ─────────────────────────────────────────────────────
    st.subheader(t("flete"))
    cfw1, cfw2 = st.columns(2)
    with cfw1:
        st.session_state.currency_flete = st.text_input(t("waehrung_flete"), st.session_state.currency_flete, key="inp_cfl")
    with cfw2:
        # Synchronize exchange rates when both currencies match
        if st.session_state.currency_flete.upper() == st.session_state.currency_fob.upper():
            sync_rate = number_input(t("wechselkurs_flete"), st.session_state.exchange_rate_common, 100.0, "inp_xfl")
            st.session_state.exchange_rate_common = sync_rate
            st.session_state.exchange_rate_flete = sync_rate
            st.session_state.exchange_rate_fob = sync_rate
        else:
            st.session_state.exchange_rate_flete = number_input(t("wechselkurs_flete"), st.session_state.exchange_rate_flete, 100.0, "inp_xfl")

    # ── Flete Table ─────────────────────────────────────────────────────────────
    fle = st.session_state.flete_items
    fle_del = []
    for i, item in enumerate(fle):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 0.4])
        with c1:
            item["descripcion"] = st.text_input(t("descripcion"), item.get("descripcion", ""), key=f"fd_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c2:
            # Use key-based binding: number_input returns value, assign back to session_state
            new_betrag = number_input(t("betrag"), float(item.get("betrag", 0.0)), 0.01, f"fb_{i}", label_visibility="visible" if i == 0 else "collapsed")
            st.session_state.flete_items[i]["betrag"] = new_betrag
        with c3:
            opts = ["masseinheit", "wert", "cantidad"]
            cur = item.get("aufteilung", "masseinheit")
            idx = opts.index(cur) if cur in opts else 0
            item["aufteilung"] = st.selectbox(t("aufteilung"), opts, index=idx, key=f"fa_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c4:
            new_cantidad = number_input(t("cantidad"), float(item.get("cantidad", 1.0)), 1.0, f"fc_{i}", label_visibility="visible" if i == 0 else "collapsed")
            st.session_state.flete_items[i]["cantidad"] = new_cantidad
        with c5:
            if st.button("✕", key=f"del_fle_{i}", help="Zeile entfernen"):
                fle_del.append(i)

    if fle_del:
        for i in sorted(fle_del, reverse=True):
            if len(st.session_state.flete_items) > 1:
                st.session_state.flete_items.pop(i)
        st.rerun()

    if st.button("+ Zeile", key="add_fle"):
        st.session_state.flete_items.append({"descripcion":"","betrag":0.0,"aufteilung":"wert","impuesto":"Exento","cantidad":1.0,"peso_volumen":0.0})
        st.rerun()

    # ── CIF Display ─────────────────────────────────────────────────────────────
    if st.session_state.result:
        r = st.session_state.result
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown(f'<div class="value-box cif">{t("cif_currency")}<br><b>{_fmt(r["cif_currency"])} {st.session_state.currency_flete}</b></div>', unsafe_allow_html=True)
        with cc2:
            st.markdown(f'<div class="value-box cif">{t("cif_gs")}<br><b>{_fmt(r["cif_gs"])} Gs</b></div>', unsafe_allow_html=True)

    # ── Importación Table ───────────────────────────────────────────────────────
    st.subheader(t("importacion"))
    imp = st.session_state.importacion_items
    imp_total = 0.0
    imp_del = []
    for i, item in enumerate(imp):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 0.4])
        with c1:
            item["descripcion"] = st.text_input(t("descripcion"), item.get("descripcion", ""), key=f"id_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c2:
            item["betrag"] = number_input(t("betrag"), item.get("betrag", 0.0), 0.01, f"ib_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c3:
            opts = ["wert", "masseinheit", "cantidad"]
            cur = item.get("aufteilung", "wert")
            idx = opts.index(cur) if cur in opts else 0
            item["aufteilung"] = st.selectbox(t("aufteilung"), opts, index=idx, key=f"ia_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c4:
            opts = ["Exento", "IVA CF", "Anticipo IRE", "5%", "10%"]
            cur = item.get("impuesto", "Exento")
            idx = opts.index(cur) if cur in opts else 0
            item["impuesto"] = st.selectbox(t("impuesto"), opts, index=idx, key=f"ii_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c5:
            if st.button("✕", key=f"del_imp_{i}", help="Diese Zeile entfernen"):
                imp_del.append(i)

    if imp_del:
        for i in sorted(imp_del, reverse=True):
            if len(st.session_state.importacion_items) > 1:
                st.session_state.importacion_items.pop(i)
        st.rerun()

    # Summe aus den berechneten Resultaten, nicht aus rohen Inputs
    imp_summe = imp_total
    if st.session_state.result:
        imp_summe = st.session_state.result.get("total_importacion", imp_total)
    st.markdown(f"<small>{t('summe')}: <b>{_fmt2(imp_summe)}</b></small> (percentage-based values computed from CIF)", unsafe_allow_html=True)

    if st.button("+ Zeile", key="add_imp"):
        st.session_state.importacion_items.append({"descripcion": "", "betrag": 0.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1.0, "peso_volumen": 0.0})
        st.rerun()

    # ── Costo Nacional Table ────────────────────────────────────────────────────
    st.subheader(t("costo_nacional"))
    nac = st.session_state.nacional_items
    nac_total = 0.0
    nac_del = []
    for i, item in enumerate(nac):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 0.4])
        with c1:
            item["descripcion"] = st.text_input(t("descripcion"), item.get("descripcion", ""), key=f"nd_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c2:
            item["betrag"] = number_input(t("betrag"), item.get("betrag", 0.0), 0.01, f"nb_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c3:
            opts = ["masseinheit", "wert", "cantidad"]
            cur = item.get("aufteilung", "masseinheit")
            idx = opts.index(cur) if cur in opts else 0
            item["aufteilung"] = st.selectbox(t("aufteilung"), opts, index=idx, key=f"na_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c4:
            opts = ["10%", "5%", "Exento", "IVA CF", "Anticipo IRE"]
            cur = item.get("impuesto", "10%")
            idx = opts.index(cur) if cur in opts else 0
            item["impuesto"] = st.selectbox(t("impuesto"), opts, index=idx, key=f"ni_{i}", label_visibility="visible" if i == 0 else "collapsed")
        with c5:
            if st.button("✕", key=f"del_nac_{i}", help="Diese Zeile entfernen"):
                nac_del.append(i)

    if nac_del:
        for i in sorted(nac_del, reverse=True):
            if len(st.session_state.nacional_items) > 1:
                st.session_state.nacional_items.pop(i)
        st.rerun()

    if len(nac) > 1:
        nac_summe = nac_total
        if st.session_state.result:
            nac_summe = st.session_state.result.get("total_nacional", nac_total)
        st.markdown(f"<small>{t('summe')}: <b>{_fmt2(nac_summe)}</b></small>", unsafe_allow_html=True)

    if st.button("+ Zeile", key="add_nac"):
        st.session_state.nacional_items.append(dict(NACIONAL_DEFAULTS[0]))
        st.rerun()

    if st.session_state.result:
        r = st.session_state.result
        st.subheader(t("ergebnis"))

        # Ergebnis-Tabelle: Beschreibung, Kosten, Steuern, Kosten/Unidad
        summary = r.get("proveedor_summary", [])
        if summary:
            html = f'''<table class="result-table">
    <tr><th>{t("descripcion")}</th><th>{t("kosten")}</th><th>{t("steuern")}</th><th>{t("kosten_pro_unidad")}</th></tr>'''
            total_k = 0.0; total_s = 0.0; total_pu = 0.0
            for s in summary:
                html += f'<tr><td>{s["descripcion"] or "(leer)"}</td><td>{_fmt(s["kosten"])} Gs</td><td>{_fmt(s["steuern"])} Gs</td><td>{_fmt(s["kosten_pro_unidad"])} Gs</td></tr>'
                total_k += s["kosten"]; total_s += s["steuern"]; total_pu += s["kosten_pro_unidad"]
            if len(summary) > 1:
                html += f'<tr class="total-row"><td><b>{t("summe")}</b></td><td><b>{_fmt(total_k)} Gs</b></td><td><b>{_fmt(total_s)} Gs</b></td><td><b>{_fmt(total_pu)} Gs</b></td></tr>'
            # Gran Total Zeile
            html += f'<tr class="total-row" style="border-top:3px double #003049;"><td><b>{t("gran_total")}</b></td><td colspan="2"><b>{_fmt(r["gran_total"])} Gs</b></td><td><b>{_fmt(r["gran_total_per_unit"])} Gs</b></td></tr>'
            html += '</table>'
            st.markdown(html, unsafe_allow_html=True)

        # Gran Total in Ergebnis-Tabelle bereits enthalten — keine separaten Boxen, keine Textarea

        # Detail expander
        st.checkbox(f"📋 {t('betrag_ohne_iva')} Details", key="show_iva_detail")
        if st.session_state.show_iva_detail:
            for section, title, items in [
                ("importacion", t("importacion"), r.get("importacion", [])),
                ("costo_nacional", t("costo_nacional"), r.get("costo_nacional", [])),
            ]:
                st.markdown(f"**{title}**")
                htm = '<table class="result-table"><tr><th>Beschreibung</th><th>Betrag</th><th>Netto</th><th>IVA</th></tr>'
                for it in items:
                    htm += f'<tr><td>{it["descripcion"]}</td><td>{_fmt(it["costo_gs"])} Gs</td><td>{_fmt(it["betrag_sin_iva"])} Gs</td><td>{_fmt(it["iva_gs"])} Gs</td></tr>'
                htm += '</table>'
                st.markdown(htm, unsafe_allow_html=True)

        # ── Save to Session History ──
        st.markdown("---")
        name = st.text_input("Berechnungsname (optional)", st.session_state.get("calc_name", ""), key="save_name")
        if st.button("💾 Berechnung speichern", type="primary"):
            data = {
                "session_name": name or f"Berechnung {len(st.session_state.session_history) + 1}",
                "language": lang_code,
                "currency_fob": st.session_state.currency_fob,
                "exchange_rate_fob": st.session_state.exchange_rate_fob,
                "purchase_unit": st.session_state.purchase_unit,
                "currency_flete": st.session_state.currency_flete,
                "exchange_rate_flete": st.session_state.exchange_rate_flete,
                **{k: r[k] for k in ["fob_currency","fob_gs","cif_currency","cif_gs","total_importacion","total_nacional","gran_total","gran_total_per_unit"]},
                "proveedor": st.session_state.proveedor_items,
                "flete": st.session_state.flete_items,
                "importacion": st.session_state.importacion_items,
                "costo_nacional": st.session_state.nacional_items,
                "user_id": st.session_state.session_user,
            }
            try:
                cid = save_calculation(data)
                if cid not in st.session_state.session_history:
                    st.session_state.session_history.append(cid)
                st.session_state.calc_name = name
                st.success(f"✅ Gespeichert als #{cid}")
            except Exception as e:
                st.error(f"Speicherfehler: {e}")

elif page == "📋 Mein Verlauf":
    st.subheader("📋 Meine Berechnungen")
    try:
        all_calcs = list_calculations(limit=200)
    except:
        all_calcs = []
    my_calcs = [c for c in all_calcs if c.get("status") == "example" or c.get("user_id") == st.session_state.session_user]
    if not my_calcs:
        st.info("Keine Berechnungen vorhanden. Speichere im Kalkulator eine neue Berechnung.")
    else:
        for c in my_calcs:
            cid = c["id"]
            badge = " 📌 Beispiel" if c.get("status") == "example" else ""
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**#{cid} — {c.get('session_name', 'Unbenannt')}{badge}**")
                    st.caption(f"{_date_str(c.get('created_at'))}  |  {c.get('language', 'de')}")
                with c2:
                    if st.button("📂 Laden", key=f"load_hist_{cid}"):
                        try:
                            full = load_calculation(cid)
                            if full:
                                inp = full.get("inputs", {}) if isinstance(full.get("inputs"), dict) else {}
                                for k in ["currency_fob","exchange_rate_fob","purchase_unit","currency_flete","exchange_rate_flete"]:
                                    if k in inp:
                                        st.session_state[k] = inp[k]
                                for key in ["proveedor","flete","importacion","costo_nacional"]:
                                    items = full.get(key, [])
                                    if items:
                                        clean = [{kk: item.get(kk, "") for kk in ["descripcion","betrag","aufteilung","impuesto","cantidad","peso_volumen"]} for item in items]
                                        st.session_state[f"{key}_items"] = clean
                            st.session_state.nav_redirect = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler: {e}")
                with c3:
                    if c.get("status") != "example" and c.get("user_id") == st.session_state.session_user:
                        if st.button("🗑️", key=f"del_hist_{cid}"):
                            try:
                                delete_calculation(cid)
                                st.rerun()
                            except:
                                pass

elif page == "⚙️ Admin":
    st.subheader("⚙️ Alle Berechnungen (Datenbank)")
    try:
        all_calcs = list_calculations(limit=100)
    except:
        all_calcs = []

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Total", len(all_calcs))
    with col_m2:
        st.metric("Drafts", sum(1 for c in all_calcs if c.get("status") == "draft"))
    with col_m3:
        st.metric("Archiviert", sum(1 for c in all_calcs if c.get("status") == "archived"))

    if not all_calcs:
        st.info("Keine Berechnungen in der Datenbank.")
    else:
        for c in all_calcs:
            cid = c["id"]
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**#{cid} — {c.get('session_name', 'Unbenannt')}**")
                    st.caption(f"{_date_str(c.get('created_at'))}  |  {c.get('language', 'de')}  |  {c.get('status', 'draft')}{' 📌 Beispiel' if c.get('status') == 'example' else ''}")
                with c2:
                    if st.button("📂 Laden", key=f"admin_load_{cid}"):
                        try:
                            full = load_calculation(cid)
                            if full:
                                inp = full.get("inputs", {}) if isinstance(full.get("inputs"), dict) else {}
                                for k in ["currency_fob","exchange_rate_fob","purchase_unit","currency_flete","exchange_rate_flete"]:
                                    if k in inp:
                                        st.session_state[k] = inp[k]
                                for key in ["proveedor","flete","importacion","costo_nacional"]:
                                    items = full.get(key, [])
                                    if items:
                                        clean = [{kk: item.get(kk, "") for kk in ["descripcion","betrag","aufteilung","impuesto","cantidad","peso_volumen"]} for item in items]
                                        st.session_state[f"{key}_items"] = clean
                            st.session_state.nav_redirect = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler: {e}")
                with c3:
                    status = c.get("status", "draft")
                    new_stat = "archived" if status == "draft" else "draft"
                    if st.button("📦 Archivieren" if status == "draft" else "📤 Reaktivieren", key=f"admin_stat_{cid}"):
                        try:
                            update_status(cid, new_stat)
                            st.rerun()
                        except:
                            st.error("Fehler")
                    if st.button("🗑️", key=f"admin_del_{cid}", help="Löschen"):
                        try:
                            delete_calculation(cid)
                            st.rerun()
                        except:
                            st.error("Fehler")

