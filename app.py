import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import re
from helpers import (
    export_to_excel,
    t, check_hs_code,
    load_state, save_state, reset_state, init_defaults,
    DEFAULTS, TRANSLATIONS,
    lookup_hs_product, search_products, list_all_products, get_product_categories,
    calc_single_product, calc_multi_product,
    init_usage_db, log_session, log_calculation, get_admin_stats,
    load_config, save_config, lookup_hs_with_ai, track_ai_tokens, test_ai_connection,
)


# ── Session & Tracking ────────────────────────────
init_usage_db()

if "_session_id" not in st.session_state:
    import uuid
    st.session_state["_session_id"] = str(uuid.uuid4())
    log_session(st.session_state["_session_id"])

# ── AI Auto-Lookup Callback ───────────────────────
def on_product_name_change():
    name = st.session_state.get("p_name", "").strip()
    hs = st.session_state.get("hs_code", "").strip()
    if not name or hs:
        st.session_state["_hs_db_suggestions"] = []
        return
    # DB search for suggestions
    db_matches = search_products(name, limit=8)
    st.session_state["_hs_db_suggestions"] = db_matches
    # If DB has exact name match, auto-fill
    exact = None
    for m in db_matches:
        if m["description"].lower() == name.lower():
            exact = m
            break
    if exact:
        st.session_state.hs_code = exact["hs_code"]
        st.session_state["_hs_source"] = "db"
        st.session_state["_hs_label"] = exact["description"]
        st.session_state.dai_rate = exact.get("default_dai", 6.0)
        st.session_state.p_fob_usd = exact.get("typical_fob_usd", 450.0)
        st.session_state.p_weight = exact.get("typical_weight_kg", 2.5)
        return
    # AI fallback: only fire once per unique name
    last_q = st.session_state.get("_hs_last_ai_query", "")
    if name == last_q:
        return
    st.session_state["_hs_last_ai_query"] = name
    cfg = load_config()
    if cfg.get("ai_provider"):
        ai_result = lookup_hs_with_ai(name, cfg)
        if ai_result and ai_result.get("hs_code"):
            st.session_state.hs_code = ai_result["hs_code"]
            st.session_state["_hs_source"] = "ai"
            st.session_state["_hs_label"] = ai_result.get("explanation", "KI-ermittelt")
            track_ai_tokens(ai_result.get("tokens_used", 0), cfg)


# ============================================================
# ZONE-BASED RATES (DAI by origin, freight by zone & mode)
# ============================================================
ZONE_DAI_RATES = {
    "Mercosur": 0.0,
    "Europa": 14.0,
    "USA": 10.0,
    "Asien": 14.0,
    "Sonstige": 16.0,
}
ZONE_FREIGHT_RATES = {
    "Mercosur": {"sea": 0.30, "air": 2.50},
    "Europa": {"sea": 0.80, "air": 5.00},
    "USA": {"sea": 0.70, "air": 4.00},
    "Asien": {"sea": 0.60, "air": 3.50},
    "Sonstige": {"sea": 0.75, "air": 4.00},
}

# ----------------------------------------------------
# Page Configuration & Styling
# ----------------------------------------------------
st.set_page_config(
    page_title="Import-Kostenkalkulator Paraguay — Zoll & Steuern berechnen",
    page_icon="🇵🇾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Paraguay Import Cost Calculator — IAS 2 compliant landed cost calculation with HS code lookup, DAI, IVA, and customs fees. Kostenlos und werbefrei."
    },
)

# ============================================================
# ADMIN PAGE  (/?admin=true)
# ============================================================
if st.query_params.get("admin") == "true":
    cfg = load_config()
    admin_pw = cfg.get("admin_password", "admin123")

    if "_admin_authed" not in st.session_state:
        pw = st.text_input("Admin-Passwort", type="password", key="admin_pw_input")
        if st.button("Login", key="admin_login_btn", width='stretch'):
            if pw == admin_pw:
                st.session_state["_admin_authed"] = True
                st.rerun()
            else:
                st.error("Falsches Passwort")
        st.stop()

    # ── Admin Dashboard ──────────────────────────
    st.title("🔧 Admin-Dashboard")
    stats = get_admin_stats()
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Sessions", stats["sessions"])
    col_b.metric("Berechnungen", stats["calculations"])
    col_c.metric("KI-Tokens", cfg.get("ai_tokens_used", 0))

    st.markdown("---")
    st.subheader("⚙️ API-Konfiguration")

    with st.form("api_config_form"):
        provider = st.selectbox("KI-Provider", ["", "ollama", "claude"], index=0 if not cfg.get("ai_provider") else ["", "ollama", "claude"].index(cfg.get("ai_provider", "")))
        ollama_endpoint = st.text_input("Ollama Endpoint", value=cfg.get("ollama_endpoint", "http://localhost:11434"))
        ollama_model = st.text_input("Ollama Model", value=cfg.get("ollama_model", "llama3.1:8b"))
        claude_key = st.text_input("Claude API Key", value=cfg.get("claude_api_key", ""), type="password")
        claude_model = st.text_input("Claude Model", value=cfg.get("claude_model", "claude-3-haiku-20240307"))
        new_admin_pw = st.text_input("Admin-Passwort ändern", type="password", placeholder="Leer lassen = unverändert")

        if st.form_submit_button("💾 Speichern & Testen", width='stretch'):
            cfg["ai_provider"] = provider
            cfg["ollama_endpoint"] = ollama_endpoint
            cfg["ollama_model"] = ollama_model
            cfg["claude_api_key"] = claude_key
            cfg["claude_model"] = claude_model
            if new_admin_pw:
                cfg["admin_password"] = new_admin_pw
            save_config(cfg)
            st.success("✅ Konfiguration gespeichert!")
            # Run AI connection test + persist result
            if provider:
                test_result = test_ai_connection(cfg)
                st.session_state["_admin_test_result"] = test_result
                st.session_state["_admin_test_provider"] = provider
            else:
                st.session_state.pop("_admin_test_result", None)
                st.session_state.pop("_admin_test_provider", None)
                st.info("ℹ️ Kein KI-Provider gewählt.")
            cfg["ai_provider"] = provider
            cfg["ollama_endpoint"] = ollama_endpoint
            cfg["ollama_model"] = ollama_model
            cfg["claude_api_key"] = claude_key
            cfg["claude_model"] = claude_model
            if new_admin_pw:
                cfg["admin_password"] = new_admin_pw
            save_config(cfg)
            st.success("Konfiguration gespeichert!")
            

    # ── Connection Status (persistent) ──────────
    _tr = st.session_state.get("_admin_test_result")
    _tp = st.session_state.get("_admin_test_provider")
    if _tr is not None:
        if _tr.get("ok"):
            st.success(f"🟢 {_tp} verbunden: {_tr.get('endpoint', _tr.get('model', _tp))}")
            if "models" in _tr:
                st.caption("Modelle: " + ", ".join(_tr["models"]))
        else:
            st.error(f"🔴 {_tp} fehlgeschlagen: {_tr.get('error', '?')}")
            st.caption(f"Endpoint: {_tr.get('endpoint', _tp)}")

    st.markdown("---")
    st.subheader(f"📊 Letzte {len(stats.get('recent',[]))} Berechnungen")
    if stats.get("recent"):
        df_admin = pd.DataFrame(stats["recent"])
        st.dataframe(df_admin[["calc_at", "product_name", "hs_code", "hs_source", "unit_cost_pyg", "total_cost_pyg"]], width='stretch')
    else:
        st.info("Noch keine Berechnungen.")

    st.stop()


# ── Restore persisted state & set defaults ──────────
load_state()
init_defaults()

# Handle DataFrame restoration from persistence
if "_df_products_records" in st.session_state and "df_products" not in st.session_state:
    try:
        st.session_state.df_products = pd.DataFrame(
            st.session_state["_df_products_records"]
        )
    except Exception:
        pass

if "df_products" not in st.session_state:
    st.session_state.df_products = pd.DataFrame(
        columns=["Produktname", "HS-Code", "Menge",
                 "FOB pro Stk. (USD)", "Gewicht pro Stk. (kg)", "DAI (%)"]
    )

# ── SEO Meta ───────────────────────────────────
st.markdown("""
<meta name="description" content="Paraguay Importkosten-Rechner: Zoll (DAI), IVA, Fracht & Steuern für Importe berechnen. IAS 2 konform. HS-Code-Datenbank mit 176 Produkten. Kostenlos.">
<meta name="keywords" content="Paraguay, Import, Zoll, HS Code, DAI, IVA, Importkosten, Kalkulator">
<meta name="robots" content="index, follow">
<meta property="og:title" content="Import-Kostenkalkulator Paraguay">
<meta property="og:description" content="Berechnen Sie Ihre Importkosten für Paraguay - Zoll, Steuern, Fracht. IAS 2 konform.">
<meta property="og:type" content="website">
""", unsafe_allow_html=True)

# ── Premium CSS
# ── Premium CSS ─────────────────────────────────────
st.markdown("""
<style>
    /* Premium font and backgrounds */
    .main { background-color: #fcfcfd; }

    /* Title banner */
    .title-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.5rem; border-radius: 12px; color: white;
        text-align: center; margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .title-banner h1 {
        margin: 0; font-family: 'Outfit', sans-serif;
        font-weight: 700; font-size: 2.5rem; letter-spacing: -0.5px;
    }
    .title-banner p {
        margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;
    }

    /* Cards */
    .calc-card {
        background-color: white; padding: 1.5rem; border-radius: 10px;
        border: 1px solid #eef2f6; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 1.5rem;
    }
    .card-header {
        font-weight: 600; font-size: 1.2rem; color: #1e3c72;
        margin-bottom: 1rem; border-bottom: 2px solid #f0f4f8;
        padding-bottom: 0.5rem;
    }

    /* Result boxes */
    .box-capitalized {
        background: linear-gradient(180deg, #f8faff 0%, #eff4fc 100%);
        border-left: 5px solid #2a5298; padding: 1.25rem;
        border-radius: 6px; margin-bottom: 1rem;
    }
    .box-credit {
        background: linear-gradient(180deg, #f6fdf9 0%, #eafaf1 100%);
        border-left: 5px solid #27ae60; padding: 1.25rem;
        border-radius: 6px; margin-bottom: 1rem;
    }
    .box-title {
        font-size: 0.9rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.5px; color: #555; margin-bottom: 0.5rem;
    }
    .box-value { font-size: 1.8rem; font-weight: 800; color: #222; }
    .box-sub { font-size: 0.85rem; color: #666; margin-top: 0.25rem; }

    /* ── HS-Code warning tooltip ── */
    .hs-alert {
        position: relative; display: inline-flex; align-items: center;
        cursor: help; margin-top: 4px;
    }
    .hs-alert-icon {
        font-size: 1.4rem; animation: hs-pulse 2s ease-in-out infinite;
    }
    .hs-alert-label {
        font-size: 0.82rem; font-weight: 600; color: #c0392b;
        margin-left: 6px;
    }
    .hs-alert-tooltip {
        visibility: hidden; opacity: 0;
        background: linear-gradient(135deg, #fff8e1 0%, #fff3cd 100%);
        border: 2px solid #e74c3c; border-radius: 10px;
        padding: 14px 18px; position: absolute; z-index: 9999;
        left: 0; top: 32px; width: 400px; max-width: 90vw;
        box-shadow: 0 8px 28px rgba(231,76,60,0.22);
        font-size: 0.84rem; line-height: 1.55; color: #333;
        transition: opacity 0.25s ease, visibility 0.25s ease;
    }
    .hs-alert:hover .hs-alert-tooltip {
        visibility: visible; opacity: 1;
    }
    .hs-alert-authority {
        font-weight: 700; font-size: 0.92rem; color: #c0392b;
        margin-bottom: 6px; border-bottom: 1px solid #e7c6a0;
        padding-bottom: 4px;
    }
    @keyframes hs-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.18); }
    }
/* === Mobile Responsive === */
    @media (max-width: 768px) {
        .title-banner { padding: 1.2rem !important; }
        .title-banner h1 { font-size: 1.4rem !important; }
        .title-banner p { font-size: 0.85rem !important; }
        .calc-card { padding: 0.8rem !important; }
        div[data-testid="column"] { min-width: 100% !important; }
        input[type="number"] { font-size: 16px !important; }
        button { min-height: 44px !important; }
    }
    @media (max-width: 480px) {
        .title-banner h1 { font-size: 1.2rem !important; }
        .box-value { font-size: 1.1rem !important; }
        .stDataFrame { font-size: 0.8rem !important; }
    }
    /* --- DB-loaded / auto-filled fields: gray tint --- */
    input.db-loaded, .db-loaded input {
        background-color: #f0f3f7 !important;
        color: #444 !important;
        border-color: #ccd !important;
    }
    .db-hint {
        font-size: 0.72em;
        color: #999;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Helper formatting functions
# ----------------------------------------------------
def format_pyg(val):
    """Format Paraguayan Guaraní as integer with thousands separators."""
    return f"Gs. {int(round(val)):,}".replace(",", ".")

def format_usd(val):
    """Format US Dollars with two decimal places."""
    return f"USD {val:,.2f}"

# Tooltips (domain-specific, kept inline)
TOOLTIPS = {
    "exchange_rate": "Wechselkurs (PYG/USD) für die Umrechnung aller USD-Beträge.",
    "fob": "Free on Board – reiner Warenwert am Verschiffungshafen (USD).",
    "cif": "Cost, Insurance & Freight – Warenwert inkl. Fracht und Versicherung (PYG). Bemessungsgrundlage für Zölle.",
    "dai": "Derecho Arancelario a la Importación – Importzoll (0–30 % auf CIF). Aktivierungspflichtig nach IAS 2.",
    "valoracion": "Valoración Aduanera – Zollbewertungsgebühr (Standard: 0,5 % des CIF). Aktivierungspflichtig.",
    "indi": "Instituto Paraguayo del Indígena – 7 % auf DAI (Ley 582/80). Aktivierungspflichtig.",
    "canon_sofia": "Nutzungsgebühr IT-Zollsystem SOFIA (fixer Betrag in PYG). Aktivierungspflichtig.",
    "consulado": "Konsulatsgebühren für die Legalisierung von Außenhandelsdokumenten. Aktivierungspflichtig.",
    "tasa_portuaria": "Hafengebühren – Umschlag und Lagerung (ANNP oder privat). Aktivierungspflichtig.",
    "despachante": "Honorare des Zollabfertigers (Despachante). Aktivierungspflichtig. IVA wird herausgerechnet.",
    "inlandstransport": "Frachtkosten Zollhafen → Lager in PYG. Aktivierungspflichtig. IVA wird herausgerechnet.",
    "iva_importacion": "IVA Importación (10 %) – Vorsteuerguthaben (Crédito Fiscal). Darf nach IAS 2.11 NICHT aktiviert werden.",
    "percepcion_ire": "Percepción IRE – Vorauszahlung Einkommensteuer beim Import (meist 0,4 % auf CIF). Steuerguthaben, NICHT aktivierbar.",
}

# ── Banner ──────────────────────────────────────────
st.markdown(f"""
<div class="title-banner">
    <h1>{t('banner_title')}</h1>
    <p>{t('banner_subtitle')}</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Sidebar
# ----------------------------------------------------
st.sidebar.markdown(t("sidebar_global_params"))

# Language selector
st.sidebar.selectbox(
    t("lang_selector"),
    options=["de", "en", "es"],
    format_func=lambda x: {"de": "🇩🇪 Deutsch", "en": "🇬🇧 English", "es": "🇪🇸 Español"}[x],
    key="lang",
)

st.sidebar.selectbox(
    t("zone_label"),
    options=["Mercosur", "Europa", "USA", "Asien", "Sonstige"],
    key="selected_zone",
    help=t("zone_help"),
)
st.sidebar.number_input(
    t("exchange_rate_label"),
    min_value=1.0, step=10.0,
    key="ex_rate",
    help=t("exchange_rate_help"),
)

st.sidebar.number_input(
    t("percepcion_ire_label"),
    min_value=0.0, max_value=10.0, step=0.1,
    key="percepcion_ire_rate",
)

st.sidebar.markdown("---")
st.sidebar.button(t("reset_button"), on_click=reset_state, type="secondary", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.info(t("legal_notice"))

# ── Dynamic Single Page ─────────────────────────────
_is_multi = len(st.session_state.df_products) >= 2

# ====================================================
# PRODUCT TABLE (always visible)
# ====================================================
st.markdown(t("multi_card_header"))

st.markdown(
    f'<div class="calc-card"><div class="card-header">{t("single_card_header")}</div></div>',
    unsafe_allow_html=True,
)

# Single-product fields (hidden when 2+ products)
if not _is_multi:
    col1, col2, col3 = st.columns(3)

    # ── Column 1: Product specs ─────────────────────
    with col1:
        st.markdown(t("col1_header"))

        # ── Product Database Lookup ──────────────────
        with st.expander("📦 Produkt aus Datenbank laden / Load from Database", expanded=False):
            _all_prods = list_all_products()
            if _all_prods:
                _cat_filter = st.selectbox(
                    "Kategorie", options=["Alle"] + get_product_categories(),
                    key="db_cat_filter_v2",
                )
                _filtered = _all_prods if _cat_filter == "Alle" else [p for p in _all_prods if p.get("category") == _cat_filter]
                _prod_opts = [f"{p['description']} ({p['hs_code']})" for p in _filtered]
                _prod_idx = st.selectbox(
                    "Produkt wählen", range(len(_prod_opts)),
                    format_func=lambda i: _prod_opts[i],
                    key="db_prod_idx_v2",
                ) if _prod_opts else None
                if st.button("✅ Daten übernehmen", type="primary", key="db_load_btn", width='stretch'):
                    _p = _filtered[_prod_idx]
                    st.session_state.p_name = _p["description"]
                    st.session_state.hs_code = _p["hs_code"]
                    st.session_state.dai_rate = _p.get("default_dai", 6.0)
                    st.session_state.p_fob_usd = _p.get("typical_fob_usd", 450.0)
                    st.session_state.p_weight = _p.get("typical_weight_kg", 2.5)
                    st.rerun()
            else:
                st.info("Keine Produktdatenbank gefunden.")

        st.text_input(t("product_name_label"), key="p_name")
        st.text_input(t("hs_code_label"), key="hs_code", on_change=on_product_name_change)

        # ── HS Source Badge ──────────────────────
        _src = st.session_state.get("_hs_source", "manual")
        _lbl = st.session_state.get("_hs_label", "")
        if _src == "ai":
            st.caption(f"🤖 KI-ermittelt: {_lbl}")
        elif _src == "db":
            st.caption(f"📦 Datenbank: {_lbl}")
        elif st.session_state.get("hs_code", "").strip():
            st.caption("✏️ Manuell eingetragen")

        # ── HS-Code Autocomplete ──────────────────
        _hs = st.session_state.get("hs_code", "")
        if _hs and len(_hs.strip()) >= 4 and re.fullmatch(r"\d+", _hs.strip()):
            _matches = search_products(_hs.strip(), limit=8)
            if _matches:
                _match_opt = [f"{m['description']} ({m['hs_code']}) | DAI {m['default_dai']}% | ~${m['typical_fob_usd']}" for m in _matches]
                with st.expander(f"🔍 {len(_matches)} Vorschläge für '{_hs.strip()}'", expanded=True):
                    _sel_match = st.selectbox("Passenden Code wählen", _match_opt, key="hs_autocomplete")
                    if _sel_match:
                        _idx = _match_opt.index(_sel_match)
                        _m = _matches[_idx]
                        if st.button("✅ Übernehmen", key="hs_apply", type="primary", width='stretch'):
                            st.session_state.hs_code = _m["hs_code"]
                            st.session_state.p_name = _m["description"]
                            st.session_state.dai_rate = _m.get("default_dai", 6.0)
                            st.session_state.p_fob_usd = _m.get("typical_fob_usd", 450.0)
                            st.session_state.p_weight = _m.get("typical_weight_kg", 2.5)
                            st.rerun()

        # ── DB Suggestions ──────────────────────────
        _sug = st.session_state.get("_hs_db_suggestions", [])
        if _sug:
            with st.expander(f"📋 {len(_sug)} Datenbank-Vorschläge", expanded=False):
                for _s in _sug:
                    _label = f"{_s['description']} ({_s['hs_code']}) — DAI {_s.get('default_dai',0)}%"
                    if st.button(_label, key=f"sug_{_s['hs_code']}", width='stretch'):
                        st.session_state.hs_code = _s["hs_code"]
                        st.session_state.p_name = _s["description"]
                        st.session_state["_hs_source"] = "db"
                        st.session_state["_hs_label"] = _s["description"]
                        st.session_state.dai_rate = _s.get("default_dai", 6.0)
                        st.session_state.p_fob_usd = _s.get("typical_fob_usd", 450.0)
                        st.session_state.p_weight = _s.get("typical_weight_kg", 2.5)
                        st.rerun()

        # HS-Code validation & warning tooltip
        if _hs:
            if not re.fullmatch(r"\d{6,10}", _hs):
                st.warning(t("hs_code_invalid"))
            else:
                _hs_result = check_hs_code(_hs)
                if _hs_result:
                    st.markdown(f"""
                    <div class="hs-alert">
                        <span class="hs-alert-icon">{_hs_result['icon']} ⚠️</span>
                        <span class="hs-alert-label">⬤ {_hs_result['authority']}</span>
                        <div class="hs-alert-tooltip">
                            <div class="hs-alert-authority">🏛️ {_hs_result['authority']}</div>
                            {_hs_result['warning']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.number_input(t("product_qty_label"), min_value=0, step=1, key="p_qty")
        st.number_input(t("fob_price_label"), min_value=0.0, step=1.0, key="p_fob_usd", help=TOOLTIPS["fob"])
        if st.session_state.get("_hs_source") == "db":
            st.caption('<span class="db-hint">DB: {st.session_state.get("hs_code","")}</span>', unsafe_allow_html=True)
        st.number_input(t("product_weight_label"), min_value=0.0, step=0.1, key="p_weight")
        if st.session_state.get("_hs_source") == "db":
            st.caption('<span class="db-hint">DB-Wert</span>', unsafe_allow_html=True)

    # ── Column 2: Logistics ─────────────────────────
    with col2:
        st.markdown(t("col2_header"))
        st.number_input(t("freight_label"), min_value=0.0, step=50.0, key="freight_usd")
        st.number_input(t("insurance_label"), min_value=0.0, step=10.0, key="insurance_usd")
        st.number_input(t("inland_transport_label"), min_value=0.0, step=50000.0, key="inland_pyg", help=TOOLTIPS["inlandstransport"])
        st.checkbox(t("inland_iva_checkbox"), key="inland_iva_incl")

    # ── Column 3: Customs ───────────────────────────
    with col3:
        st.markdown(t("col3_header"))
        zone_dai = ZONE_DAI_RATES.get(st.session_state.get("selected_zone", "Sonstige"), 10.0)
        st.number_input(t("dai_rate_label"), min_value=0.0, max_value=35.0, value=float(zone_dai), step=1.0, key="dai_rate", help=TOOLTIPS["dai"])
        if st.session_state.get("_hs_source") == "db":
            st.caption('<span class="db-hint">DB-Wert</span>', unsafe_allow_html=True)

        # Valoracion Aduanera: 0.5% CIF is legally fixed
        st.markdown("Valoracion Aduanera: **0,5 % des CIF-Werts** \U0001f512 (gesetzlich festgelegt)")
        st.session_state.val_mode = 0
        st.session_state.val_pyg_input = 0.0

        st.number_input(t("indi_rate_label"), min_value=0.0, max_value=10.0, step=0.5, key="indi_rate", help=TOOLTIPS["indi"])
        st.number_input(t("canon_sofia_label"), min_value=0.0, step=10000.0, key="canon_sofia", help=TOOLTIPS["canon_sofia"])
        st.number_input(t("consulado_label"), min_value=0.0, step=10000.0, key="consulado", help=TOOLTIPS["consulado"])
        st.number_input(t("tasa_portuaria_label"), min_value=0.0, step=50000.0, key="tasa_portuaria", help=TOOLTIPS["tasa_portuaria"])
        st.number_input(t("despachante_label"), min_value=0.0, step=50000.0, key="despachante", help=TOOLTIPS["despachante"])
        st.checkbox(t("despachante_iva_checkbox"), key="despachante_iva_incl")
        st.number_input(t("other_costs_label"), min_value=0.0, step=10000.0, key="sonstiges")

    # ── Calculations (delegated to helpers) ─────────
    _params = {
        k: st.session_state.get(k, DEFAULTS.get(k, 0))
        for k in ["p_qty", "p_fob_usd", "p_weight", "freight_usd",
                  "insurance_usd", "inland_pyg", "inland_iva_incl",
                  "dai_rate", "val_mode", "val_pyg_input", "indi_rate",
                  "canon_sofia", "consulado", "tasa_portuaria",
                  "despachante", "despachante_iva_incl", "sonstiges"]
    }
    _r = calc_single_product(_params, st.session_state.ex_rate, st.session_state.percepcion_ire_rate)

    # Log calculation
    log_calculation(
        st.session_state["_session_id"],
        product_name=st.session_state.get("p_name", ""),
        hs_code=st.session_state.get("hs_code", ""),
        hs_source=st.session_state.get("_hs_source", "manual"),
        quantity=st.session_state.get("p_qty", 0),
        fob_usd=st.session_state.get("p_fob_usd", 0),
        weight_kg=st.session_state.get("p_weight", 0),
        dai_pct=st.session_state.get("dai_rate", 0),
        cif_pyg=_r.get("cif_pyg", 0),
        unit_cost_pyg=_r.get("unit_cost_pyg", 0),
        total_cost_pyg=_r.get("total_acquisition_cost", 0),
        tax_credit_pyg=_r.get("total_tax_credit", 0),
    )

    unit_cost_pyg = _r["unit_cost_pyg"]
    unit_cost_usd = _r["unit_cost_usd"]
    total_acquisition_cost = _r["total_acquisition_cost"]
    total_tax_credit = _r["total_tax_credit"]

    # ── Results ─────────────────────────────────────
    st.markdown("---")
    st.markdown(t("results_header"))

    out_col1, out_col2 = st.columns(2)

    with out_col1:
        _sub1 = t("unit_cost_sub").format(usd=format_usd(unit_cost_usd), total=format_pyg(total_acquisition_cost))
        st.markdown(f"""
        <div class="box-capitalized">
        <div class="box-title">{t('unit_cost_title')}</div>
        <div class="box-value">{format_pyg(unit_cost_pyg)}</div>
        <div class="box-sub">{_sub1}</div>
        </div>
        """, unsafe_allow_html=True)

    with out_col2:
        st.markdown(f"""
        <div class="box-credit">
        <div class="box-title">{t('tax_credit_title')}</div>
        <div class="box-value">{format_pyg(total_tax_credit)}</div>
        <div class="box-sub">{t('tax_credit_sub')}</div>
        </div>
        """, unsafe_allow_html=True)


# ====================================================
# MULTI-PRODUCT MODE (2+ products)
# ====================================================
if _is_multi:
    st.markdown(
        f'<div class="calc-card"><div class="card-header">{t("multi_card_header")}</div></div>',
        unsafe_allow_html=True,
    )
    st.write(t("multi_intro"))

    # ── Product table ───────────────────────────────
    st.markdown(t("multi_products_header"))

    # ── DB Quick-Add ──────────────────────────────
    with st.expander("📦 Produkt aus Datenbank hinzufügen", expanded=False):
        _all_prods_m = list_all_products()
        if _all_prods_m:
            _cat_m = st.selectbox(
                "Kategorie", options=["Alle"] + get_product_categories(),
                key="db_multi_cat",
            )
            _filt_m = _all_prods_m if _cat_m == "Alle" else [p for p in _all_prods_m if p.get("category") == _cat_m]
            _opts_m = [f"{p['description']} ({p['hs_code']})" for p in _filt_m]
            _sel_m = st.selectbox(
                "Produkt", _opts_m, key="db_multi_prod",
            ) if _opts_m else None
            col_a, col_b = st.columns(2)
            with col_a:
                _qty_m = st.number_input("Menge", min_value=1, value=1, step=1, key="db_multi_qty")
            with col_b:
                st.write("")
                st.write("")
                if st.button("➕ Zum Import hinzufügen", type="primary", key="db_multi_add", width='stretch'):
                    _p = _filt_m[_opts_m.index(_sel_m)]
                    new_row = pd.DataFrame([{
                        "Produktname": _p["description"],
                        "HS-Code": _p["hs_code"],
                        "Menge": _qty_m,
                        "FOB pro Stk. (USD)": _p.get("typical_fob_usd", 0.0),
                        "Gewicht pro Stk. (kg)": _p.get("typical_weight_kg", 0.0),
                        "DAI (%)": _p.get("default_dai", 6.0),
                    }])
                    st.session_state.df_products = pd.concat(
                        [st.session_state.df_products, new_row], ignore_index=True
                    )
                    st.rerun()
        else:
            st.info("Keine Produktdatenbank gefunden.")

    _col_cfg = {
        "Produktname": st.column_config.TextColumn(t("multi_col_product")),
        "HS-Code": st.column_config.TextColumn(t("multi_col_hscode")),
        "Menge": st.column_config.NumberColumn(t("multi_col_qty"), min_value=0, step=1),
        "FOB pro Stk. (USD)": st.column_config.NumberColumn(t("multi_col_fob"), min_value=0.0, step=1.0),
        "Gewicht pro Stk. (kg)": st.column_config.NumberColumn(t("multi_col_weight"), min_value=0.0, step=0.1),
        "DAI (%)": st.column_config.NumberColumn(t("multi_col_dai"), min_value=0.0, max_value=35.0, step=1.0),
    }

    edited_df = st.data_editor(
        st.session_state.df_products,
        column_config=_col_cfg,
        num_rows="dynamic",
        width='stretch',
        key="prod_editor",
    )
    st.session_state.df_products = edited_df

    # ── Shared costs ────────────────────────────────
    st.markdown("---")
    col_l, col_c, col_k = st.columns(3)

    with col_l:
        st.markdown(t("multi_logistics_header"))
        st.number_input(t("multi_freight_label"), min_value=0.0, step=100.0, key="multi_freight_usd")
        st.number_input(t("multi_insurance_label"), min_value=0.0, step=20.0, key="multi_insurance_usd")
        st.number_input(t("multi_inland_label"), min_value=0.0, step=50000.0, key="multi_inland_pyg")
        st.checkbox(t("multi_inland_iva"), key="multi_inland_iva_incl")

    with col_c:
        st.markdown(t("multi_customs_header"))
        # Valoracion Aduanera: 0.5% CIF is legally fixed
        st.markdown("Valoracion Aduanera: **0,5 % des CIF-Werts** \U0001f512 (gesetzlich festgelegt)")
        st.session_state.multi_val_mode = 0
        st.session_state.multi_val_pyg_manual = 0.0

        st.number_input(t("multi_indi_label"), min_value=0.0, max_value=10.0, step=0.5, key="multi_indi_rate")
        st.number_input(t("multi_canon_label"), min_value=0.0, step=10000.0, key="multi_canon_sofia")
        st.number_input(t("multi_consulado_label"), min_value=0.0, step=20000.0, key="multi_consulado")
        st.number_input(t("multi_tasa_label"), min_value=0.0, step=50000.0, key="multi_tasa_portuaria")

    with col_k:
        st.markdown(t("multi_services_header"))
        st.number_input(t("multi_despachante_label"), min_value=0.0, step=50000.0, key="multi_despachante")
        st.checkbox(t("multi_despachante_iva"), key="multi_despachante_iva_incl")
        st.number_input(t("multi_sonstiges_label"), min_value=0.0, step=10000.0, key="multi_sonstiges")

        st.markdown(t("multi_alloc_header"))
        st.selectbox(
        t("multi_alloc_freight_label"),
        options=[0, 1],
        format_func=lambda x: t("multi_alloc_freight_opt_weight") if x == 0 else t("multi_alloc_freight_opt_value"),
        key="alloc_freight",
        help=t("multi_alloc_freight_help"),
        )
        st.selectbox(
        t("multi_alloc_local_label"),
        options=[0, 1],
        format_func=lambda x: t("multi_alloc_local_opt_value") if x == 0 else t("multi_alloc_local_opt_weight"),
        key="alloc_local",
        help=t("multi_alloc_local_help"),
        )

        # ── Calculations (delegated to helpers) ─────────
    _multi_result = calc_multi_product(
        edited_df,
        st.session_state.ex_rate,
        st.session_state.percepcion_ire_rate,
        st.session_state.multi_freight_usd,
        st.session_state.multi_insurance_usd,
        st.session_state.multi_inland_pyg,
        st.session_state.multi_inland_iva_incl,
        st.session_state.multi_val_mode,
        st.session_state.multi_val_pyg_manual,
        st.session_state.multi_indi_rate,
        st.session_state.multi_canon_sofia,
        st.session_state.multi_consulado,
        st.session_state.multi_tasa_portuaria,
        st.session_state.multi_despachante,
        st.session_state.multi_despachante_iva_incl,
        st.session_state.multi_sonstiges,
        st.session_state.alloc_freight,
        st.session_state.alloc_local,
    )

    if _multi_result is None:
        st.error(t("multi_error_zero"))
    else:
        prods = _multi_result["products_df"]
        total_shipment_cap = _multi_result["total_capitalized"]
        total_shipment_credit = _multi_result["total_tax_credit"]
        m_inland_iva = _multi_result["inland_iva"]
        m_desp_iva = _multi_result["desp_iva"]
        sum_fob_usd = _multi_result["sum_fob_usd"]
        sum_weight_kg = _multi_result["sum_weight_kg"]

        # ── Results ─────────────────────────
        st.markdown("---")
        st.markdown(t("multi_results_header"))

        s1, s2 = st.columns(2)
        with s1:
            _sub_m1 = t("multi_cap_sub").format(usd=format_usd(total_shipment_cap / st.session_state.ex_rate))
            st.markdown(f"""
            <div class="box-capitalized">
                <div class="box-title">{t('multi_cap_title')}</div>
                <div class="box-value">{format_pyg(total_shipment_cap)}</div>
                <div class="box-sub">{_sub_m1}</div>
            </div>
            """, unsafe_allow_html=True)
        with s2:
            _sub_m2 = t("multi_credit_sub").format(
                iva=format_pyg(prods["IVA_Importacion_PYG"].sum()),
                perc=format_pyg(prods["Percepcion_IRE_PYG"].sum()),
                svc=format_pyg(m_inland_iva + m_desp_iva),
            )
            st.markdown(f"""
            <div class="box-credit">
                <div class="box-title">{t('multi_credit_title')}</div>
                <div class="box-value">{format_pyg(total_shipment_credit)}</div>
                <div class="box-sub">{_sub_m2}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── Result table ────────────────────────
        result_display = pd.DataFrame({
            t("res_col_product"): prods["Produktname"],
            t("res_col_qty"): prods["Menge"],
            t("res_col_fob"): prods["Total_FOB_USD"],
            t("res_col_weight"): prods["Total_Weight_kg"].map(lambda x: f"{x:,.1f} kg"),
            t("res_col_cif"): prods["CIF_PYG"],
            t("res_col_dai"): prods["DAI_PYG"],
            t("res_col_other"): prods["Val_PYG"] + prods["INDI_PYG"] + prods["Alloc_Local_PYG"],
            t("res_col_total"): prods["Total_Capitalized_PYG"],
            t("res_col_unit_pyg"): prods["Stückkosten_PYG"],
            t("res_col_unit_usd"): prods["Stückkosten_USD"],
            t("res_col_credit"): prods["Total_Tax_Credit_PYG"],
        })

        def _fmt_pyg(x):
            return f"₲ {int(round(x)):,}".replace(",", ".")

        st.markdown(t("multi_table_header"))
        fmt_dict = {
            t("res_col_fob"): lambda x: f"$ {x:,.2f}",
            t("res_col_cif"): _fmt_pyg,
            t("res_col_dai"): _fmt_pyg,
            t("res_col_other"): _fmt_pyg,
            t("res_col_total"): _fmt_pyg,
            t("res_col_unit_pyg"): _fmt_pyg,
            t("res_col_unit_usd"): lambda x: f"$ {x:,.2f}",
            t("res_col_credit"): _fmt_pyg,
        }
        st.dataframe(
            result_display.style.format(fmt_dict),
            width='stretch',
        )

        # CSV download
        csv_buf = io.StringIO()
        prods.to_csv(csv_buf, index=False, sep=";")
        st.download_button(
            label=t("multi_csv_button"),
            data=csv_buf.getvalue(),
            file_name=t("multi_csv_filename"),
            mime="text/csv",
        )

        # ── Charts ──────────────────────────────
        st.markdown("---")
        ch1, ch2 = st.columns(2)

        with ch1:
            st.markdown(t("multi_chart_products"))
            fig_p, ax_p = plt.subplots(figsize=(6, 6))
            prod_labels = prods["Produktname"].tolist()
            prod_costs = prods["Total_Capitalized_PYG"].tolist()
            labels_w_price = [f"{n} ({format_pyg(c)})" for n, c in zip(prod_labels, prod_costs)]
            fig_p.patch.set_alpha(0.0)
            ax_p.patch.set_alpha(0.0)
            w, _, at = ax_p.pie(
                prod_costs, labels=None, autopct="%1.1f%%",
                startangle=140, textprops=dict(color="w", weight="bold"), pctdistance=0.75,
            )
            ax_p.legend(w, labels_w_price, title=t("multi_legend_products"), loc="center", bbox_to_anchor=(0.5, -0.15))
            st.pyplot(fig_p)

        with ch2:
            st.markdown(t("multi_chart_types"))
            fig_t, ax_t = plt.subplots(figsize=(6, 6))
            fob_all = sum_fob_usd * ex_rate_m
            intl_all = (st.session_state.multi_freight_usd + st.session_state.multi_insurance_usd) * ex_rate_m
            customs_all = (
                prods["DAI_PYG"].sum() + prods["Val_PYG"].sum() + prods["INDI_PYG"].sum()
                + st.session_state.multi_canon_sofia + st.session_state.multi_consulado
                + st.session_state.multi_tasa_portuaria
            )
            local_all = m_desp_netto + st.session_state.multi_sonstiges + m_inland_netto

            ct_labels = [
                f"{t('multi_chart_fob')} ({format_pyg(fob_all)})",
                f"{t('multi_chart_freight')} ({format_pyg(intl_all)})",
                f"{t('multi_chart_customs')} ({format_pyg(customs_all)})",
                f"{t('multi_chart_local')} ({format_pyg(local_all)})",
            ]
            ct_sizes = [fob_all, intl_all, customs_all, local_all]
            ct_colors = ["#1e3c72", "#3a7bd5", "#f39c12", "#7f8c8d"]

            fig_t.patch.set_alpha(0.0)
            ax_t.patch.set_alpha(0.0)
            wt, _, att = ax_t.pie(
                ct_sizes, labels=None, autopct="%1.1f%%",
                startangle=140, colors=ct_colors,
                textprops=dict(color="w", weight="bold"), pctdistance=0.75,
            )
            ax_t.legend(wt, ct_labels, title=t("multi_legend_types"), loc="center", bbox_to_anchor=(0.5, -0.15))
            st.pyplot(fig_t)


# ====================================================
# FOOTER
# ====================================================
st.markdown("---")
st.markdown(t("footer_header"))

info_c1, info_c2 = st.columns(2)
with info_c1:
    st.markdown(f"""
    * 📜 **DAI:** {TOOLTIPS["dai"]}
    * ⚖️ **Valoración Aduanera:** {TOOLTIPS["valoracion"]}
    * 👥 **INDI (Ley 582/80):** {TOOLTIPS["indi"]}
    * 💻 **Canon SOFIA:** {TOOLTIPS["canon_sofia"]}
    """)
with info_c2:
    st.markdown(f"""
    * ⚓ **Tasa Portuaria:** {TOOLTIPS["tasa_portuaria"]}
    * 👔 **Despachante:** {TOOLTIPS["despachante"]}
    * 💰 **IVA Importación (10 %):** {TOOLTIPS["iva_importacion"]}
    * 💵 **Percepción IRE:** {TOOLTIPS["percepcion_ire"]}
    """)

# ====================================================
# PERSIST STATE (runs at end of every script execution)
# ====================================================
save_state()