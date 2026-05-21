import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# ----------------------------------------------------
# Page Configuration & Styling
# ----------------------------------------------------
st.set_page_config(
    page_title="Import-Kostenkalkulator Paraguay",
    page_icon="🇵🇾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS
st.markdown("""
<style>
    /* Premium font and backgrounds */
    .main {
        background-color: #fcfcfd;
    }
    
    /* Title Styling */
    .title-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .title-banner h1 {
        margin: 0;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        letter-spacing: -0.5px;
    }
    .title-banner p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }

    /* Cards for inputs and outputs */
    .calc-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #eef2f6;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        margin-bottom: 1.5rem;
    }
    
    .card-header {
        font-weight: 600;
        font-size: 1.2rem;
        color: #1e3c72;
        margin-bottom: 1rem;
        border-bottom: 2px solid #f0f4f8;
        padding-bottom: 0.5rem;
    }

    /* Cost Capitalized Box vs Tax Credit Box */
    .box-capitalized {
        background: linear-gradient(180deg, #f8faff 0%, #eff4fc 100%);
        border-left: 5px solid #2a5298;
        padding: 1.25rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    
    .box-credit {
        background: linear-gradient(180deg, #f6fdf9 0%, #eafaf1 100%);
        border-left: 5px solid #27ae60;
        padding: 1.25rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    
    .box-title {
        font-size: 0.9rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #555;
        margin-bottom: 0.5rem;
    }
    
    .box-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #222;
    }
    .box-sub {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.25rem;
    }

    /* Tooltip styles */
    .tooltip-icon {
        cursor: help;
        color: #2a5298;
        font-weight: bold;
        margin-left: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Helper Functions
# ----------------------------------------------------
def format_pyg(val):
    """Format Paraguayan Guaraní as integer with thousands separators."""
    return f"Gs. {int(round(val)):,}".replace(",", ".")

def format_usd(val):
    """Format US Dollars with two decimal places."""
    return f"USD {val:,.2f}"

# Tooltips explanations for Paraguayan terms
TOOLTIPS = {
    "exchange_rate": "Wechselkurs (PYG/USD) für die Umrechnung aller USD-Beträge (FOB, Fracht, Versicherung) in die Landeswährung.",
    "fob": "Free on Board: Der reine Warenwert am Verschiffungshafen in USD.",
    "cif": "Cost, Insurance & Freight: Warenwert inkl. internationaler Fracht und Versicherung in PYG. Dient als Bemessungsgrundlage für Zölle.",
    "dai": "Derecho Arancelario a la Importación: Der paraguayische Importzoll (0% bis 30% auf CIF). Laut IAS 2 ein aktivierungspflichtiger Anschaffungsnebenkosten-Bestandteil.",
    "valoracion": "Valoración Aduanera: Zollbewertungsgebühr der Zollbehörde (DNA). Standardmäßig 0,5% des CIF-Werts. Aktivierungspflichtig.",
    "indi": "Instituto Paraguayo del Indígena: Gesetzliche Abgabe von 7% auf den DAI-Zollbetrag (Ley 582/80). Aktivierungspflichtig.",
    "canon_sofia": "Nutzungsgebühr für das staatliche IT-Zollsystem 'SOFIA' (fixer Betrag in PYG pro Zollabfertigung). Aktivierungspflichtig.",
    "consulado": "Konsulatsgebühren: Gebühren für die Legalisierung von Außenhandelsdokumenten. Aktivierungspflichtig.",
    "tasa_portuaria": "Hafengebühren (Tasa Portuaria): Kosten für Umschlag und Lagerung im Hafen (staatlich ANNP oder privat). Aktivierungspflichtig.",
    "despachante": "Honorare für den lizenzierten Zollabfertiger (Despachante de Aduanas). Aktivierungspflichtig. Die enthaltene 10% Mehrwertsteuer (IVA) wird als steuerliches Guthaben herausgerechnet.",
    "inlandstransport": "Inlandstransport: Frachtkosten vom Zollhafen/Flughafen zum eigenen Lager in PYG. Aktivierungspflichtig. Optionale 10% IVA wird herausgerechnet.",
    "iva_importacion": "IVA Importación (10% Mehrwertsteuer auf Importe): Berechnet auf Basis (CIF + DAI + Valoración + INDI + Canon + Hafen + Konsulat). Gilt nach Ley 6380/19 als Vorsteuerguthaben (Crédito Fiscal) und darf gemäß IAS 2.11 NICHT aktiviert werden.",
    "percepcion_ire": "Percepción IRE: Vorauszahlung auf die Einkommensteuer (IRE) beim Import (meist 0,4% auf CIF-Basis). Gilt als steuerliches Guthaben und darf gemäß IAS 2.11 NICHT aktiviert werden."
}

# Banner
st.markdown("""
<div class="title-banner">
    <h1>🇵🇾 Import-Kostenkalkulator Paraguay</h1>
    <p>Rechtskonforme Anschaffungskostenermittlung nach IAS 2 & Ley 6380/19</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Sidebar Inputs (Global Parameters)
# ----------------------------------------------------
st.sidebar.markdown("### ⚙️ Globale Parameter")

ex_rate = st.sidebar.number_input(
    "Wechselkurs (PYG/USD)",
    min_value=1.0,
    value=7000.0,
    step=10.0,
    help=TOOLTIPS["exchange_rate"]
)

percepcion_ire_rate = st.sidebar.number_input(
    "Percepción IRE Satz (%)",
    min_value=0.0,
    max_value=10.0,
    value=0.4,
    step=0.1,
    help=TOOLTIPS["percepcion_ire_rate"] if "percepcion_ire_rate" in TOOLTIPS else TOOLTIPS["percepcion_ire"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Rechtlicher Hinweis (IAS 2 & Ley 6380/19):**\n"
    "Einfuhrumsatzsteuern (IVA Importación) und Vorauszahlungen (Percepción IRE) sind "
    "steuerlich als Guthaben (Crédito Fiscal) abziehbar. "
    "Daher dürfen sie nach internationalem Standard **IAS 2.11** nicht den Anschaffungskosten "
    "zugeschrieben werden, sondern müssen separat ausgewiesen werden."
)

# Create Tabs
tab_single, tab_multi = st.tabs(["📦 Einzelprodukt-Kalkulator", "🗃️ Mehrprodukt-Kalkulator"])

# ====================================================
# TAB 1: EINZELPRODUKT-KALKULATION
# ====================================================
with tab_single:
    st.markdown('<div class="calc-card"><div class="card-header">Kalkulationsdaten für ein einzelnes Produkt</div></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**1. Produktspezifikationen**")
        p_name = st.text_input("Produktname", value="Maschinenteil A")
        p_qty = st.number_input("Menge (Stück)", min_value=1, value=100, step=1)
        p_fob_usd = st.number_input("FOB Einzelpreis (USD)", min_value=0.01, value=50.00, step=1.00, help=TOOLTIPS["fob"])
        p_weight = st.number_input("Gewicht pro Stück (kg)", min_value=0.01, value=2.5, step=0.1)

    with col2:
        st.markdown("**2. Logistik & Transport**")
        freight_usd = st.number_input("Internationale Fracht (USD)", min_value=0.0, value=800.0, step=50.0)
        insurance_usd = st.number_input("Transportversicherung (USD)", min_value=0.0, value=150.0, step=10.0)
        inland_pyg = st.number_input("Inlandstransport (PYG)", min_value=0.0, value=1500000.0, step=50000.0, help=TOOLTIPS["inlandstransport"])
        inland_iva_incl = st.checkbox("Inlandstransport enthält 10% IVA", value=True)

    with col3:
        st.markdown("**3. Zoll & Abfertigung (PYG)**")
        dai_rate = st.number_input("DAI Zollsatz (%)", min_value=0.0, max_value=35.0, value=10.0, step=1.0, help=TOOLTIPS["dai"])
        
        val_mode = st.radio("Valoración Aduanera Gebühr", ["0.5% des CIF-Werts", "Manueller Betrag"], index=0, help=TOOLTIPS["valoracion"])
        if val_mode == "0.5% des CIF-Werts":
            val_pyg_input = 0.0
        else:
            val_pyg_input = st.number_input("Manueller Betrag Valoración (PYG)", min_value=0.0, value=300000.0, step=10000.0)
            
        indi_rate = st.number_input("INDI Satz (% von DAI)", min_value=0.0, max_value=10.0, value=7.0, step=0.5, help=TOOLTIPS["indi"])
        canon_sofia = st.number_input("Canon SOFIA (PYG)", min_value=0.0, value=100000.0, step=10000.0, help=TOOLTIPS["canon_sofia"])
        consulado = st.number_input("Konsulatsgebühren (PYG)", min_value=0.0, value=250000.0, step=10000.0, help=TOOLTIPS["consulado"])
        tasa_portuaria = st.number_input("Hafengebühren (PYG)", min_value=0.0, value=600000.0, step=50000.0, help=TOOLTIPS["tasa_portuaria"])
        
        despachante = st.number_input("Despachante Honorar (PYG)", min_value=0.0, value=1800000.0, step=50000.0, help=TOOLTIPS["despachante"])
        despachante_iva_incl = st.checkbox("Despachante-Honorar enthält 10% IVA", value=True)
        
        sonstiges = st.number_input("Sonstige Nebenkosten (PYG)", min_value=0.0, value=100000.0, step=10000.0)

    # ----------------------------------------------------
    # TAB 1: BERECHNUNGEN (Single Product)
    # ----------------------------------------------------
    total_fob_usd = p_qty * p_fob_usd
    total_fob_pyg = total_fob_usd * ex_rate
    
    # Freight & Insurance
    total_freight_pyg = freight_usd * ex_rate
    total_insurance_pyg = insurance_usd * ex_rate
    
    # CIF Calculation
    cif_usd = total_fob_usd + freight_usd + insurance_usd
    cif_pyg = cif_usd * ex_rate
    
    # Netting Domestic Transport
    if inland_iva_incl:
        inland_netto = inland_pyg / 1.1
        inland_iva = inland_netto * 0.1
    else:
        inland_netto = inland_pyg
        inland_iva = 0.0
        
    # Netting Despachante Broker
    if despachante_iva_incl:
        despachante_netto = despachante / 1.1
        despachante_iva = despachante_netto * 0.1
    else:
        despachante_netto = despachante
        despachante_iva = 0.0

    # Customs Taxes
    dai_pyg = cif_pyg * (dai_rate / 100.0)
    
    if val_mode == "0.5% des CIF-Werts":
        val_pyg = cif_pyg * 0.005
    else:
        val_pyg = val_pyg_input
        
    indi_pyg = dai_pyg * (indi_rate / 100.0)
    
    # Total Capitalized Cost components (IAS 2)
    # Includes: FOB + International Freight + Insurance + DAI + Valoracion + INDI + Canon + Consulate + Port + Net Despachante + Net Inland + Sonstiges
    capitalized_logistics = total_freight_pyg + total_insurance_pyg + inland_netto
    capitalized_customs = dai_pyg + val_pyg + indi_pyg + canon_sofia + consulado + tasa_portuaria + despachante_netto + sonstiges
    total_acquisition_cost = total_fob_pyg + capitalized_logistics + capitalized_customs
    unit_cost_pyg = total_acquisition_cost / p_qty
    unit_cost_usd = unit_cost_pyg / ex_rate
    
    # Tax Credits (Ley 6380/19) - NOT Capitalized
    # Tax base for Customs IVA: CIF + DAI + Valoracion + INDI + Canon + Consulate + Tasa Portuaria
    base_iva_aduana = cif_pyg + dai_pyg + val_pyg + indi_pyg + canon_sofia + consulado + tasa_portuaria
    iva_importacion = base_iva_aduana * 0.10
    
    percepcion_ire = cif_pyg * (percepcion_ire_rate / 100.0)
    
    total_tax_credit = iva_importacion + percepcion_ire + inland_iva + despachante_iva

    # ----------------------------------------------------
    # TAB 1: OUTPUTS
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("### 📊 Kalkulationsergebnisse (Einzelprodukt)")
    
    out_col1, out_col2 = st.columns(2)
    
    with out_col1:
        st.markdown(f"""
        <div class="box-capitalized">
            <div class="box-title">Stückeinstandspreis (IAS 2 aktiviert)</div>
            <div class="box-value">{format_pyg(unit_cost_pyg)}</div>
            <div class="box-sub">Entspricht <b>{format_usd(unit_cost_usd)}</b> pro Stück (Gesamte Anschaffungskosten: {format_pyg(total_acquisition_cost)})</div>
        </div>
        """, unsafe_allow_html=True)
        
    with out_col2:
        st.markdown(f"""
        <div class="box-credit">
            <div class="box-title">Steuerliches Guthaben (Crédito Fiscal - nicht aktiviert)</div>
            <div class="box-value">{format_pyg(total_tax_credit)}</div>
            <div class="box-sub">Wird direkt mit der Steuererklärung verrechnet und mindert nicht die Marge.</div>
        </div>
        """, unsafe_allow_html=True)

    # Detailed Cost Table
    cost_data = {
        "Kostenkomponente": [
            "FOB Warenwert (Netto)",
            "Internationale Fracht",
            "Transportversicherung",
            "Zollgebühr (DAI)",
            "Zollbewertungsgebühr (Valoración)",
            "INDI Abgabe",
            "Canon SOFIA",
            "Konsulatsgebühren",
            "Hafengebühren (Tasa Portuaria)",
            "Zollagent (Despachante Netto)",
            "Inlandstransport (Netto)",
            "Sonstiges",
            "**Summe Anschaffungskosten (Aktiviert)**",
            "Einfuhrumsatzsteuer (IVA Importación 10%)",
            "Percepción IRE (Vorauszahlung)",
            "Zollagent IVA (10%)",
            "Inlandstransport IVA (10%)",
            "**Summe Steuerliches Guthaben (Nicht aktiviert)**"
        ],
        "Betrag (USD)": [
            total_fob_usd,
            freight_usd,
            insurance_usd,
            dai_pyg / ex_rate,
            val_pyg / ex_rate,
            indi_pyg / ex_rate,
            canon_sofia / ex_rate,
            consulado / ex_rate,
            tasa_portuaria / ex_rate,
            despachante_netto / ex_rate,
            inland_netto / ex_rate,
            sonstiges / ex_rate,
            total_acquisition_cost / ex_rate,
            iva_importacion / ex_rate,
            percepcion_ire / ex_rate,
            despachante_iva / ex_rate,
            inland_iva / ex_rate,
            total_tax_credit / ex_rate
        ],
        "Betrag (PYG)": [
            total_fob_pyg,
            total_freight_pyg,
            total_insurance_pyg,
            dai_pyg,
            val_pyg,
            indi_pyg,
            canon_sofia,
            consulado,
            tasa_portuaria,
            despachante_netto,
            inland_netto,
            sonstiges,
            total_acquisition_cost,
            iva_importacion,
            percepcion_ire,
            despachante_iva,
            inland_iva,
            total_tax_credit
        ],
        "Behandlung": [
            "Aktiviert (IAS 2)", "Aktiviert (IAS 2)", "Aktiviert (IAS 2)",
            "Aktiviert (IAS 2)", "Aktiviert (IAS 2)", "Aktiviert (IAS 2)",
            "Aktiviert (IAS 2)", "Aktiviert (IAS 2)", "Aktiviert (IAS 2)",
            "Aktiviert (IAS 2)", "Aktiviert (IAS 2)", "Aktiviert (IAS 2)",
            "**BILANZ (Vorräte)**",
            "Steuerguthaben (Vorsteuer)", "Steuerguthaben (Körperschaftssteuer)",
            "Steuerguthaben (Vorsteuer)", "Steuerguthaben (Vorsteuer)",
            "**STEUERFORDERNIS**"
        ]
    }
    
    df_cost = pd.DataFrame(cost_data)
    
    # Visual Layout below outputs
    disp_col1, disp_col2 = st.columns([3, 2])
    
    with disp_col1:
        st.markdown("**Detaillierter Kostenspiegel**")
        st.dataframe(
            df_cost.style.format({
                "Betrag (USD)": lambda x: f"$ {x:,.2f}",
                "Betrag (PYG)": lambda x: f"₲ {int(round(x)):,}".replace(",", ".")
            }),
            height=660,
            use_container_width=True
        )
        
        # CSV Download Button
        csv_buffer = io.StringIO()
        df_cost.to_csv(csv_buffer, index=False, sep=";")
        st.download_button(
            label="📥 Detaillierte Kalkulation als CSV exportieren",
            data=csv_buffer.getvalue(),
            file_name=f"import_kalkulation_{p_name.replace(' ', '_')}.csv",
            mime="text/csv"
        )

    with disp_col2:
        st.markdown("**Struktur der Anschaffungskosten**")
        
        # Build beautiful chart
        labels = [
            f"FOB Warenwert ({format_pyg(total_fob_pyg)})",
            f"Int. Fracht & Vers. ({format_pyg(total_freight_pyg + total_insurance_pyg)})",
            f"Zoll & Gebühren ({format_pyg(capitalized_customs)})",
            f"Inlandstransport ({format_pyg(inland_netto)})"
        ]
        sizes = [total_fob_pyg, total_freight_pyg + total_insurance_pyg, capitalized_customs, inland_netto]
        colors = ["#1e3c72", "#3a7bd5", "#f39c12", "#e67e22"]
        
        # Filter zero values for better rendering
        filtered_labels = [l for l, s in zip(labels, sizes) if s > 0]
        filtered_sizes = [s for s in sizes if s > 0]
        filtered_colors = [colors[i] for i, s in enumerate(sizes) if s > 0]
        
        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(
            filtered_sizes,
            labels=None,  # We use legend
            autopct="%1.1f%%",
            startangle=140,
            colors=filtered_colors,
            textprops=dict(color="w", weight="bold"),
            pctdistance=0.75
        )
        
        # Transparent background and nice legend
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        
        # Legend with matching colored boxes
        ax.legend(
            wedges,
            filtered_labels,
            title="Kostengruppen",
            loc="center",
            bbox_to_anchor=(0.5, -0.15)
        )
        
        st.pyplot(fig)

# ====================================================
# TAB 2: MEHRPRODUKT-KALKULATION
# ====================================================
with tab_multi:
    st.markdown('<div class="calc-card"><div class="card-header">Mehrprodukt-Importkalkulation mit Kostenschlüsselung</div></div>', unsafe_allow_html=True)
    
    st.write(
        "Geben Sie hier Ihre Produktliste ein. Die Nebenkosten (z.B. Containerfracht) "
        "können Sie im Anschluss wert- (FOB) oder gewichtsbasiert (kg) auf die Produkte verteilen."
    )
    
    # Initialize session state for multi-product if not exists
    if "df_products" not in st.session_state:
        # Default starting values
        st.session_state.df_products = pd.DataFrame([
            {"Produktname": "Wechselrichter 5kW", "Menge": 50, "FOB pro Stk. (USD)": 350.00, "Gewicht pro Stk. (kg)": 22.0, "DAI (%)": 10.0},
            {"Produktname": "Solarpanel 450W", "Menge": 200, "FOB pro Stk. (USD)": 75.00, "Gewicht pro Stk. (kg)": 20.0, "DAI (%)": 6.0},
            {"Produktname": "Lithium-Batterie 10kWh", "Menge": 10, "FOB pro Stk. (USD)": 1800.00, "Gewicht pro Stk. (kg)": 85.0, "DAI (%)": 14.0}
        ])
        
    # Editable Data Frame for Products
    st.markdown("**1. Importierte Produkte**")
    edited_df = st.data_editor(
        st.session_state.df_products,
        num_rows="dynamic",
        use_container_width=True,
        key="prod_editor"
    )
    # Update session state with edits
    st.session_state.df_products = edited_df
    
    # Common Overhead Costs Form
    st.markdown("---")
    st.markdown("**2. Gemeinsame Logistik- und Zollabfertigungskosten (Mehrprodukt)**")
    
    col_l, col_c, col_k = st.columns(3)
    
    with col_l:
        st.markdown("**Logistikkosten (für die Gesamtlieferung)**")
        multi_freight_usd = st.number_input("See-/Luftfracht gesamt (USD)", min_value=0.0, value=3500.0, step=100.0)
        multi_insurance_usd = st.number_input("Versicherung gesamt (USD)", min_value=0.0, value=400.0, step=20.0)
        multi_inland_pyg = st.number_input("Inlandstransport gesamt (PYG)", min_value=0.0, value=3000000.0, step=50000.0)
        multi_inland_iva_incl = st.checkbox("Inlandstransport enthält 10% IVA", value=True, key="m_inland_iva")
        
    with col_c:
        st.markdown("**Gemeinsame Zollgebühren (PYG)**")
        multi_val_mode = st.radio("Valoración Aduanera", ["0.5% des CIF-Werts je Produkt", "Manueller Gesamtbetrag"], index=0, key="m_val_mode")
        if multi_val_mode == "Manueller Gesamtbetrag":
            multi_val_pyg_manual = st.number_input("Gesamt-Valoración (PYG)", min_value=0.0, value=800000.0, step=50000.0)
        else:
            multi_val_pyg_manual = 0.0
            
        multi_indi_rate = st.number_input("INDI Satz (% von DAI)", min_value=0.0, max_value=10.0, value=7.0, step=0.5, key="m_indi_rate")
        multi_canon_sofia = st.number_input("Canon SOFIA gesamt (PYG)", min_value=0.0, value=100000.0, step=10000.0, key="m_canon")
        multi_consulado = st.number_input("Konsulatsgebühren gesamt (PYG)", min_value=0.0, value=500000.0, step=20000.0, key="m_consulado")
        multi_tasa_portuaria = st.number_input("Hafengebühren gesamt (PYG)", min_value=0.0, value=1500000.0, step=50000.0, key="m_tasa_port")
        
    with col_k:
        st.markdown("**Dienstleistungen & Sonstiges**")
        multi_despachante = st.number_input("Despachante Honorar gesamt (PYG)", min_value=0.0, value=2500000.0, step=50000.0, key="m_desp")
        multi_despachante_iva_incl = st.checkbox("Broker-Honorar enthält 10% IVA", value=True, key="m_desp_iva")
        multi_sonstiges = st.number_input("Sonstige Nebenkosten gesamt (PYG)", min_value=0.0, value=300000.0, step=10000.0, key="m_sonst")
        
        st.markdown("**Verteilungsschlüssel (Kostenschlüsselung)**")
        alloc_freight = st.selectbox(
            "Verteilung für Fracht & Versicherung",
            options=["Gewichtsbasiert (kg-Anteil)", "Wertbasiert (FOB-Anteil)"],
            help="Frachtkosten fallen meist volumen- oder gewichtsbezogen an. Versicherung meist wertbezogen."
        )
        alloc_local = st.selectbox(
            "Verteilung für Hafengebühren, Broker, Inlandstransport, etc.",
            options=["Wertbasiert (FOB-Anteil)", "Gewichtsbasiert (kg-Anteil)"],
            help="So werden die fixen lokalen Gebühren auf die Produkte aufgeteilt."
        )

    # ----------------------------------------------------
    # TAB 2: BERECHNUNGEN (Multi-Product)
    # ----------------------------------------------------
    if len(edited_df) == 0:
        st.warning("⚠️ Bitte fügen Sie mindestens ein Produkt in der Tabelle hinzu.")
    else:
        # Netting local services
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

        # Calculate totals per product row
        prods = edited_df.copy()
        
        # Fill missing values
        prods["Produktname"] = prods["Produktname"].fillna("Unbenannt")
        prods["Menge"] = pd.to_numeric(prods["Menge"], errors="coerce").fillna(0).astype(int)
        prods["FOB pro Stk. (USD)"] = pd.to_numeric(prods["FOB pro Stk. (USD)"], errors="coerce").fillna(0.0)
        prods["Gewicht pro Stk. (kg)"] = pd.to_numeric(prods["Gewicht pro Stk. (kg)"], errors="coerce").fillna(0.0)
        prods["DAI (%)"] = pd.to_numeric(prods["DAI (%)"], errors="coerce").fillna(0.0)
        
        # Calculate total FOB and total weight for allocation
        prods["Total_FOB_USD"] = prods["Menge"] * prods["FOB pro Stk. (USD)"]
        prods["Total_Weight_kg"] = prods["Menge"] * prods["Gewicht pro Stk. (kg)"]
        
        sum_fob_usd = prods["Total_FOB_USD"].sum()
        sum_weight_kg = prods["Total_Weight_kg"].sum()
        
        if sum_fob_usd <= 0 or sum_weight_kg <= 0:
            st.error("Gesamt-FOB-Wert und Gesamtgewicht müssen größer als 0 sein.")
        else:
            # Allocation ratios
            prods["FOB_Share"] = prods["Total_FOB_USD"] / sum_fob_usd
            prods["Weight_Share"] = prods["Total_Weight_kg"] / sum_weight_kg
            
            # 1. Allocate Freight & Insurance (USD)
            if "Gewichtsbasiert" in alloc_freight:
                prods["Alloc_Freight_USD"] = multi_freight_usd * prods["Weight_Share"]
                prods["Alloc_Insurance_USD"] = multi_insurance_usd * prods["Weight_Share"]
            else:
                prods["Alloc_Freight_USD"] = multi_freight_usd * prods["FOB_Share"]
                prods["Alloc_Insurance_USD"] = multi_insurance_usd * prods["FOB_Share"]
                
            prods["Alloc_Freight_PYG"] = prods["Alloc_Freight_USD"] * ex_rate
            prods["Alloc_Insurance_PYG"] = prods["Alloc_Insurance_USD"] * ex_rate
            
            # 2. CIF values
            prods["CIF_USD"] = prods["Total_FOB_USD"] + prods["Alloc_Freight_USD"] + prods["Alloc_Insurance_USD"]
            prods["CIF_PYG"] = prods["CIF_USD"] * ex_rate
            
            # 3. Product specific customs duties (DAI, Valoracion, INDI)
            prods["DAI_PYG"] = prods["CIF_PYG"] * (prods["DAI (%)"] / 100.0)
            
            if multi_val_mode == "0.5% des CIF-Werts je Produkt":
                prods["Val_PYG"] = prods["CIF_PYG"] * 0.005
            else:
                # Distribute the manual global valuation
                if "Gewichtsbasiert" in alloc_local:
                    prods["Val_PYG"] = multi_val_pyg_manual * prods["Weight_Share"]
                else:
                    prods["Val_PYG"] = multi_val_pyg_manual * prods["FOB_Share"]
                    
            prods["INDI_PYG"] = prods["DAI_PYG"] * (multi_indi_rate / 100.0)
            
            # 4. Allocate Common local costs (Canon, Consulado, Hafen, Despachante Net, Sonstiges, Inland Net)
            total_common_local_net_pyg = (
                multi_canon_sofia + multi_consulado + multi_tasa_portuaria + 
                m_desp_netto + multi_sonstiges + m_inland_netto
            )
            
            if "Gewichtsbasiert" in alloc_local:
                prods["Alloc_Local_PYG"] = total_common_local_net_pyg * prods["Weight_Share"]
                # For tax base calculation allocation of specific fees:
                prods["Alloc_TaxBase_Fees_PYG"] = (multi_canon_sofia + multi_consulado + multi_tasa_portuaria) * prods["Weight_Share"]
            else:
                prods["Alloc_Local_PYG"] = total_common_local_net_pyg * prods["FOB_Share"]
                prods["Alloc_TaxBase_Fees_PYG"] = (multi_canon_sofia + multi_consulado + multi_tasa_portuaria) * prods["FOB_Share"]
                
            # 5. Total Capitalized Cost & Unit Price
            prods["Total_Capitalized_PYG"] = (
                (prods["Total_FOB_USD"] * ex_rate) + 
                prods["Alloc_Freight_PYG"] + prods["Alloc_Insurance_PYG"] + 
                prods["DAI_PYG"] + prods["Val_PYG"] + prods["INDI_PYG"] + 
                prods["Alloc_Local_PYG"]
            )
            prods["Stückkosten_PYG"] = prods["Total_Capitalized_PYG"] / prods["Menge"]
            prods["Stückkosten_USD"] = prods["Stückkosten_PYG"] / ex_rate
            
            # 6. Tax Credits (IVA Importacion, Percepcion IRE, local IVAs)
            # IVA Base = CIF + DAI + Val + INDI + Allocated (Canon + Consulado + Hafen)
            prods["IVA_Base_PYG"] = (
                prods["CIF_PYG"] + prods["DAI_PYG"] + prods["Val_PYG"] + 
                prods["INDI_PYG"] + prods["Alloc_TaxBase_Fees_PYG"]
            )
            prods["IVA_Importacion_PYG"] = prods["IVA_Base_PYG"] * 0.10
            prods["Percepcion_IRE_PYG"] = prods["CIF_PYG"] * (percepcion_ire_rate / 100.0)
            
            # Allocate local service IVA
            if "Gewichtsbasiert" in alloc_local:
                prods["Alloc_Inland_IVA"] = m_inland_iva * prods["Weight_Share"]
                prods["Alloc_Broker_IVA"] = m_desp_iva * prods["Weight_Share"]
            else:
                prods["Alloc_Inland_IVA"] = m_inland_iva * prods["FOB_Share"]
                prods["Alloc_Broker_IVA"] = m_desp_iva * prods["FOB_Share"]
                
            prods["Total_Tax_Credit_PYG"] = (
                prods["IVA_Importacion_PYG"] + prods["Percepcion_IRE_PYG"] + 
                prods["Alloc_Inland_IVA"] + prods["Alloc_Broker_IVA"]
            )

            # Global Totals for Summary
            total_shipment_capitalized_pyg = prods["Total_Capitalized_PYG"].sum()
            total_shipment_credits_pyg = prods["Total_Tax_Credit_PYG"].sum()

            # ----------------------------------------------------
            # TAB 2: OUTPUTS
            # ----------------------------------------------------
            st.markdown("---")
            st.markdown("### 📊 Gesamtergebnisse (Mehrprodukt-Import)")
            
            sum_col1, sum_col2 = st.columns(2)
            with sum_col1:
                st.markdown(f"""
                <div class="box-capitalized">
                    <div class="box-title">Summe Anschaffungskosten Lieferung (IAS 2 aktiviert)</div>
                    <div class="box-value">{format_pyg(total_shipment_capitalized_pyg)}</div>
                    <div class="box-sub">Entspricht ca. <b>{format_usd(total_shipment_capitalized_pyg / ex_rate)}</b></div>
                </div>
                """, unsafe_allow_html=True)
                
            with sum_col2:
                st.markdown(f"""
                <div class="box-credit">
                    <div class="box-title">Summe Steuerliches Guthaben (Nicht aktiviert)</div>
                    <div class="box-value">{format_pyg(total_shipment_credits_pyg)}</div>
                    <div class="box-sub">Zoll-IVA ({format_pyg(prods['IVA_Importacion_PYG'].sum())}) + Percepción ({format_pyg(prods['Percepcion_IRE_PYG'].sum())}) + Service-IVA ({format_pyg(m_inland_iva + m_desp_iva)})</div>
                </div>
                """, unsafe_allow_html=True)

            # Build Result Table for user display
            result_display = pd.DataFrame({
                "Produkt": prods["Produktname"],
                "Menge": prods["Menge"],
                "FOB USD (Gesamt)": prods["Total_FOB_USD"],
                "Gewicht (Gesamt)": prods["Total_Weight_kg"].map(lambda x: f"{x:,.1f} kg"),
                "Umlage CIF (PYG)": prods["CIF_PYG"],
                "Zoll DAI (PYG)": prods["DAI_PYG"],
                "Andere Nebenk. (PYG)": prods["Val_PYG"] + prods["INDI_PYG"] + prods["Alloc_Local_PYG"],
                "Anschaffungsk. gesamt (PYG)": prods["Total_Capitalized_PYG"],
                "Stückeinstandspreis (PYG)": prods["Stückkosten_PYG"],
                "Stückeinstandspreis (USD)": prods["Stückkosten_USD"],
                "Steuerguthaben (PYG)": prods["Total_Tax_Credit_PYG"]
            })

            st.markdown("**Ergebnis-Übersicht je Produkt**")
            st.dataframe(
                result_display.style.format({
                    "FOB USD (Gesamt)": lambda x: f"$ {x:,.2f}",
                    "Umlage CIF (PYG)": lambda x: f"₲ {int(round(x)):,}".replace(",", "."),
                    "Zoll DAI (PYG)": lambda x: f"₲ {int(round(x)):,}".replace(",", "."),
                    "Andere Nebenk. (PYG)": lambda x: f"₲ {int(round(x)):,}".replace(",", "."),
                    "Anschaffungsk. gesamt (PYG)": lambda x: f"₲ {int(round(x)):,}".replace(",", "."),
                    "Stückeinstandspreis (PYG)": lambda x: f"₲ {int(round(x)):,}".replace(",", "."),
                    "Stückeinstandspreis (USD)": lambda x: f"$ {x:,.2f}",
                    "Steuerguthaben (PYG)": lambda x: f"₲ {int(round(x)):,}".replace(",", ".")
                }),
                use_container_width=True
            )

            # CSV Download for Multi-Product
            csv_buffer_multi = io.StringIO()
            prods.to_csv(csv_buffer_multi, index=False, sep=";")
            
            st.download_button(
                label="📥 Vollständigen Verteilungsbogen als CSV exportieren",
                data=csv_buffer_multi.getvalue(),
                file_name="import_kalkulation_mehrprodukt.csv",
                mime="text/csv"
            )

            # Cost Breakdown Charts (Side-by-side or below)
            st.markdown("---")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("**Verteilung der Anschaffungskosten auf Produkte**")
                fig_p, ax_p = plt.subplots(figsize=(6, 6))
                
                prod_labels = prods["Produktname"].tolist()
                prod_costs = prods["Total_Capitalized_PYG"].tolist()
                
                # Make labels with prices
                prod_labels_with_price = [
                    f"{name} ({format_pyg(cost)})" 
                    for name, cost in zip(prod_labels, prod_costs)
                ]
                
                fig_p.patch.set_alpha(0.0)
                ax_p.patch.set_alpha(0.0)
                
                wedges, texts, autotexts = ax_p.pie(
                    prod_costs,
                    labels=None,
                    autopct="%1.1f%%",
                    startangle=140,
                    textprops=dict(color="w", weight="bold"),
                    pctdistance=0.75
                )
                
                ax_p.legend(
                    wedges,
                    prod_labels_with_price,
                    title="Produkte",
                    loc="center",
                    bbox_to_anchor=(0.5, -0.15)
                )
                st.pyplot(fig_p)

            with chart_col2:
                st.markdown("**Verteilung nach Kostenart (Gesamte Sendung)**")
                fig_t, ax_t = plt.subplots(figsize=(6, 6))
                
                total_fob_all_pyg = sum_fob_usd * ex_rate
                total_intl_log_all_pyg = (multi_freight_usd + multi_insurance_usd) * ex_rate
                total_customs_all_pyg = prods["DAI_PYG"].sum() + prods["Val_PYG"].sum() + prods["INDI_PYG"].sum() + multi_canon_sofia + multi_consulado + multi_tasa_portuaria
                total_local_fees_all_pyg = m_desp_netto + multi_sonstiges + m_inland_netto
                
                cost_type_labels = [
                    f"FOB Warenwert ({format_pyg(total_fob_all_pyg)})",
                    f"Int. Fracht & Vers. ({format_pyg(total_intl_log_all_pyg)})",
                    f"Zoll & Abgaben ({format_pyg(total_customs_all_pyg)})",
                    f"Lokale Logistik/Broker ({format_pyg(total_local_fees_all_pyg)})"
                ]
                cost_type_sizes = [total_fob_all_pyg, total_intl_log_all_pyg, total_customs_all_pyg, total_local_fees_all_pyg]
                cost_type_colors = ["#1e3c72", "#3a7bd5", "#f39c12", "#7f8c8d"]
                
                fig_t.patch.set_alpha(0.0)
                ax_t.patch.set_alpha(0.0)
                
                wedges_t, texts_t, autotexts_t = ax_t.pie(
                    cost_type_sizes,
                    labels=None,
                    autopct="%1.1f%%",
                    startangle=140,
                    colors=cost_type_colors,
                    textprops=dict(color="w", weight="bold"),
                    pctdistance=0.75
                )
                
                ax_t.legend(
                    wedges_t,
                    cost_type_labels,
                    title="Kostengruppen",
                    loc="center",
                    bbox_to_anchor=(0.5, -0.15)
                )
                st.pyplot(fig_t)

# ====================================================
# FOOTER / EXPLANATIONS OF PARAGUAYAN TERMS
# ====================================================
st.markdown("---")
st.markdown("### 📚 Begriffserklärungen & Steuerliche Grundlagen (Paraguay)")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.markdown(f"""
    * 📜 **DAI (Derecho Arancelario a la Importación):** {TOOLTIPS["dai"]}
    * ⚖️ **Valoración Aduanera:** {TOOLTIPS["valoracion"]}
    * 👥 **INDI (Ley 582/80):** {TOOLTIPS["indi"]}
    * 💻 **Canon SOFIA:** {TOOLTIPS["canon_sofia"]}
    """)

with info_col2:
    st.markdown(f"""
    * ⚓ **Tasa Portuaria:** {TOOLTIPS["tasa_portuaria"]}
    * 👔 **Despachante de Aduanas:** {TOOLTIPS["despachante"]}
    * 💰 **IVA Importación (10%):** {TOOLTIPS["iva_importacion"]}
    * 💵 **Percepción IRE (Ley 6380/19):** {TOOLTIPS["percepcion_ire"]}
    """)
