"""
pytest tests for calc_single_product() and calc_multi_product() in helpers.py

Covers:
  - calc_single_product:
      • defaults test: verify unit_cost_pyg, cif_pyg, dai_pyg match expected
      • FOB=0: should not crash
      • quantity=1: should work
      • IAS 2: tax_credit not in total_acquisition_cost
      • DAI calc: cif_pyg * (dai_rate/100)
      • IVA: 10% of (CIF+DAI+Val+INDI+Canon+Consulado+Port)
  - calc_multi_product:
      • 1 product as multi: should match single
      • 2 products with allocation
      • weight-based vs value-based allocation difference
"""

import sys
import math
from pathlib import Path

import pandas as pd
import pytest

# Ensure helpers.py is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers import calc_single_product, calc_multi_product


# ============================================================================
# Shared constants
# ============================================================================

EX_RATE = 7700.0
PERCEP_IRE_RATE = 0.4


# ============================================================================
# Fixtures for calc_single_product
# ============================================================================

@pytest.fixture
def default_params():
    """Typical single-product parameters."""
    return {
        "p_qty": 100,
        "p_fob_usd": 450.0,
        "p_weight": 2.5,
        "freight_usd": 3500.0,
        "insurance_usd": 400.0,
        "inland_pyg": 3000000.0,
        "inland_iva_incl": True,
        "dai_rate": 6.0,
        "val_mode": 0,
        "val_pyg_input": 0.0,
        "indi_rate": 7.0,
        "canon_sofia": 100000.0,
        "consulado": 500000.0,
        "tasa_portuaria": 1500000.0,
        "despachante": 2500000.0,
        "despachante_iva_incl": True,
        "sonstiges": 300000.0,
    }


# ============================================================================
# Tests for calc_single_product
# ============================================================================

# --- 1. Defaults test: verify unit_cost_pyg, cif_pyg, dai_pyg match expected ---

def test_defaults_unit_cost_cif_dai(default_params):
    """Verify unit_cost_pyg, cif_pyg, and dai_pyg against hand-computed values."""
    r = calc_single_product(default_params, EX_RATE, PERCEP_IRE_RATE)

    # CIF = (qty * FOB + freight + insurance) * ex_rate
    cif_usd = 100 * 450.0 + 3500.0 + 400.0  # 48900.0
    expected_cif_pyg = cif_usd * EX_RATE     # 376,530,000.0
    assert r["cif_pyg"] == pytest.approx(expected_cif_pyg)

    # DAI = cif_pyg * dai_rate / 100
    expected_dai = expected_cif_pyg * 6.0 / 100.0
    assert r["dai_pyg"] == pytest.approx(expected_dai)

    # Unit cost = total_acquisition_cost / qty
    assert r["unit_cost_pyg"] == pytest.approx(
        r["total_acquisition_cost"] / default_params["p_qty"]
    )
    assert r["unit_cost_pyg"] > 0
    assert r["unit_cost_usd"] == pytest.approx(r["unit_cost_pyg"] / EX_RATE)


# --- 2. FOB=0: should not crash ---

def test_fob_zero_no_crash():
    """FOB=0 must produce valid results without any exception."""
    params = {
        "p_qty": 50,
        "p_fob_usd": 0.0,
        "p_weight": 1.0,
        "freight_usd": 2000.0,
        "insurance_usd": 100.0,
        "inland_pyg": 1000000.0,
        "inland_iva_incl": True,
        "dai_rate": 10.0,
        "val_mode": 0,
        "val_pyg_input": 0.0,
        "indi_rate": 7.0,
        "canon_sofia": 50000.0,
        "consulado": 200000.0,
        "tasa_portuaria": 800000.0,
        "despachante": 1500000.0,
        "despachante_iva_incl": True,
        "sonstiges": 100000.0,
    }

    r = calc_single_product(params, EX_RATE, PERCEP_IRE_RATE)

    # All result keys present
    assert r["total_fob_usd"] == 0.0
    assert r["total_fob_pyg"] == 0.0

    # CIF comes from freight + insurance
    assert r["cif_usd"] == 2100.0
    assert r["cif_pyg"] == pytest.approx(2100.0 * EX_RATE)

    # Unit cost still > 0 (from logistics + customs)
    assert r["unit_cost_pyg"] > 0
    assert r["unit_cost_usd"] > 0

    # Tax credit still computes
    assert r["total_tax_credit"] > 0


# --- 3. Quantity=1: should work ---

def test_quantity_one():
    """Quantity=1: unit cost equals total acquisition cost."""
    params = {
        "p_qty": 1,
        "p_fob_usd": 8000.0,
        "p_weight": 50.0,
        "freight_usd": 500.0,
        "insurance_usd": 50.0,
        "inland_pyg": 500000.0,
        "inland_iva_incl": False,
        "dai_rate": 14.0,
        "val_mode": 0,
        "val_pyg_input": 0.0,
        "indi_rate": 7.0,
        "canon_sofia": 80000.0,
        "consulado": 300000.0,
        "tasa_portuaria": 600000.0,
        "despachante": 1200000.0,
        "despachante_iva_incl": False,
        "sonstiges": 200000.0,
    }

    r = calc_single_product(params, EX_RATE, PERCEP_IRE_RATE)

    assert r["total_fob_usd"] == 8000.0
    assert r["unit_cost_pyg"] == pytest.approx(r["total_acquisition_cost"])
    assert r["unit_cost_pyg"] > 0
    assert r["unit_cost_usd"] == pytest.approx(r["unit_cost_pyg"] / EX_RATE)

    # Quantity=1 with qty=0 should also work as edge
    params_qty0 = dict(params)
    params_qty0["p_qty"] = 0
    r0 = calc_single_product(params_qty0, EX_RATE, PERCEP_IRE_RATE)
    assert r0["unit_cost_pyg"] == 0.0
    assert r0["unit_cost_usd"] == 0.0


# --- 4. IAS 2: tax_credit not in total_acquisition_cost ---

def test_ias2_tax_credit_excluded(default_params):
    """
    total_acquisition_cost must NOT include tax credits.
    Reconstruct it from pre-tax cost components and verify equality.
    """
    r = calc_single_product(default_params, EX_RATE, PERCEP_IRE_RATE)

    # Hand-build the capitalized cost:
    # total_fob_pyg + freight_pyg + insurance_pyg + inland_netto
    # + dai_pyg + val_pyg + indi_pyg + canon_sofia + consulado
    # + tasa_portuaria + despachante_netto + sonstiges
    freight_pyg = default_params["freight_usd"] * EX_RATE
    insurance_pyg = default_params["insurance_usd"] * EX_RATE

    inland_netto = default_params["inland_pyg"] / 1.1  # iva_incl=True
    despachante_netto = default_params["despachante"] / 1.1

    expected_cap = (
        r["total_fob_pyg"]
        + freight_pyg
        + insurance_pyg
        + inland_netto
        + r["dai_pyg"]
        + r["val_pyg"]
        + r["indi_pyg"]
        + default_params["canon_sofia"]
        + default_params["consulado"]
        + default_params["tasa_portuaria"]
        + despachante_netto
        + default_params["sonstiges"]
    )

    assert r["total_acquisition_cost"] == pytest.approx(expected_cap)

    # Tax credit items exist but are NOT embedded in capitalized cost
    assert r["iva_importacion"] > 0
    assert r["percepcion_ire"] > 0
    assert r["total_tax_credit"] > 0

    # total_acquisition_cost + total_tax_credit should be strictly larger
    assert r["total_acquisition_cost"] + r["total_tax_credit"] > r[
        "total_acquisition_cost"
    ]


# --- 5. DAI calc: cif_pyg * (dai_rate / 100) ---

def test_dai_calculation():
    """DAI is exactly cif_pyg * dai_rate / 100."""
    params = {
        "p_qty": 5,
        "p_fob_usd": 2000.0,
        "p_weight": 20.0,
        "freight_usd": 800.0,
        "insurance_usd": 200.0,
        "inland_pyg": 1000000.0,
        "inland_iva_incl": True,
        "dai_rate": 12.0,
        "val_mode": 0,
        "val_pyg_input": 0.0,
        "indi_rate": 7.0,
        "canon_sofia": 80000.0,
        "consulado": 300000.0,
        "tasa_portuaria": 1000000.0,
        "despachante": 1800000.0,
        "despachante_iva_incl": True,
        "sonstiges": 150000.0,
    }

    r = calc_single_product(params, EX_RATE, PERCEP_IRE_RATE)
    expected_dai = r["cif_pyg"] * (params["dai_rate"] / 100.0)
    assert r["dai_pyg"] == pytest.approx(expected_dai)

    # DAI=0 → dai_pyg=0, indi_pyg=0 (INDI is dai_pyg * indi_rate)
    params_zero = dict(params)
    params_zero["dai_rate"] = 0.0
    r_zero = calc_single_product(params_zero, EX_RATE, PERCEP_IRE_RATE)
    assert r_zero["dai_pyg"] == 0.0
    assert r_zero["indi_pyg"] == 0.0


# --- 6. IVA: 10% of (CIF + DAI + Val + INDI + Canon + Consulado + Port) ---

def test_iva_importacion_base():
    """IVA importacion is 10% of the tax base defined by Ley 6380/19."""
    params = {
        "p_qty": 10,
        "p_fob_usd": 3000.0,
        "p_weight": 15.0,
        "freight_usd": 1200.0,
        "insurance_usd": 300.0,
        "inland_pyg": 2000000.0,
        "inland_iva_incl": True,
        "dai_rate": 8.0,
        "val_mode": 0,
        "val_pyg_input": 0.0,
        "indi_rate": 7.0,
        "canon_sofia": 90000.0,
        "consulado": 400000.0,
        "tasa_portuaria": 1200000.0,
        "despachante": 2200000.0,
        "despachante_iva_incl": True,
        "sonstiges": 200000.0,
    }

    r = calc_single_product(params, EX_RATE, PERCEP_IRE_RATE)

    base = (
        r["cif_pyg"]
        + r["dai_pyg"]
        + r["val_pyg"]
        + r["indi_pyg"]
        + params["canon_sofia"]
        + params["consulado"]
        + params["tasa_portuaria"]
    )

    assert r["base_iva_aduana"] == pytest.approx(base)
    assert r["iva_importacion"] == pytest.approx(base * 0.10)

    # Verify inland_netto and despachante_netto are NOT in the IVA base
    iva_if_extra_included = (
        base + r["inland_netto"] + r["despachante_netto"]
    ) * 0.10
    assert r["iva_importacion"] != pytest.approx(iva_if_extra_included, abs=1.0)


# ============================================================================
# Helper to build a minimal multi-product DataFrame
# ============================================================================

def _make_products_df(products):
    """Build a DataFrame from a list of dicts with keys:
        Produktname, Menge, FOB pro Stk. (USD), Gewicht pro Stk. (kg), DAI (%)
    """
    return pd.DataFrame(products)


# ============================================================================
# Fixtures for calc_multi_product
# ============================================================================

@pytest.fixture
def multi_kwargs():
    """Default shared-cost kwargs for calc_multi_product (matching DEFAULTS)."""
    return {
        "multi_freight_usd": 3500.0,
        "multi_insurance_usd": 400.0,
        "multi_inland_pyg": 3000000.0,
        "multi_inland_iva_incl": True,
        "multi_val_mode": 0,
        "multi_val_pyg_manual": 800000.0,
        "multi_indi_rate": 7.0,
        "multi_canon_sofia": 100000.0,
        "multi_consulado": 500000.0,
        "multi_tasa_portuaria": 1500000.0,
        "multi_despachante": 2500000.0,
        "multi_despachante_iva_incl": True,
        "multi_sonstiges": 300000.0,
        "alloc_freight": 0,   # weight-based
        "alloc_local": 0,     # value-based
    }


@pytest.fixture
def single_product_df():
    """One product matching single-product scenario for cross-validation."""
    return _make_products_df(
        [
            {
                "Produktname": "Laptop",
                "Menge": 100,
                "FOB pro Stk. (USD)": 450.0,
                "Gewicht pro Stk. (kg)": 2.5,
                "DAI (%)": 6.0,
            }
        ]
    )


@pytest.fixture
def two_products_df():
    """Two products with different weights, values, and DAI rates."""
    return _make_products_df(
        [
            {
                "Produktname": "Laptop",
                "Menge": 50,
                "FOB pro Stk. (USD)": 800.0,
                "Gewicht pro Stk. (kg)": 2.0,
                "DAI (%)": 10.0,
            },
            {
                "Produktname": "Monitor",
                "Menge": 30,
                "FOB pro Stk. (USD)": 400.0,
                "Gewicht pro Stk. (kg)": 5.0,
                "DAI (%)": 6.0,
            },
        ]
    )


# ============================================================================
# Tests for calc_multi_product
# ============================================================================

# --- 7. 1 product as multi: should match single ---

def test_multi_one_product_matches_single(single_product_df, multi_kwargs):
    """
    When multi-product receives exactly one product with the same params
    as a single-product calculation, the per-product results should match.
    """
    r_multi = calc_multi_product(
        single_product_df.copy(), EX_RATE, PERCEP_IRE_RATE, **multi_kwargs
    )
    assert r_multi is not None

    # Build equivalent single-product params
    single_params = {
        "p_qty": 100,
        "p_fob_usd": 450.0,
        "p_weight": 2.5,
        "freight_usd": multi_kwargs["multi_freight_usd"],
        "insurance_usd": multi_kwargs["multi_insurance_usd"],
        "inland_pyg": multi_kwargs["multi_inland_pyg"],
        "inland_iva_incl": multi_kwargs["multi_inland_iva_incl"],
        "dai_rate": 6.0,
        "val_mode": multi_kwargs["multi_val_mode"],
        "val_pyg_input": multi_kwargs["multi_val_pyg_manual"],
        "indi_rate": multi_kwargs["multi_indi_rate"],
        "canon_sofia": multi_kwargs["multi_canon_sofia"],
        "consulado": multi_kwargs["multi_consulado"],
        "tasa_portuaria": multi_kwargs["multi_tasa_portuaria"],
        "despachante": multi_kwargs["multi_despachante"],
        "despachante_iva_incl": multi_kwargs["multi_despachante_iva_incl"],
        "sonstiges": multi_kwargs["multi_sonstiges"],
    }
    r_single = calc_single_product(single_params, EX_RATE, PERCEP_IRE_RATE)

    prod = r_multi["products_df"].iloc[0]

    # FOB and CIF should match
    assert prod["Total_FOB_USD"] == pytest.approx(r_single["total_fob_usd"])
    assert prod["CIF_PYG"] == pytest.approx(r_single["cif_pyg"])

    # DAI on this product's CIF
    assert prod["DAI_PYG"] == pytest.approx(r_single["dai_pyg"])

    # Total capitalized per product vs single
    assert prod["Total_Capitalized_PYG"] == pytest.approx(
        r_single["total_acquisition_cost"]
    )

    # Unit costs match
    assert prod["Stückkosten_PYG"] == pytest.approx(r_single["unit_cost_pyg"])
    assert prod["Stückkosten_USD"] == pytest.approx(r_single["unit_cost_usd"])

    # Tax credits
    assert prod["IVA_Importacion_PYG"] == pytest.approx(r_single["iva_importacion"])
    assert prod["Total_Tax_Credit_PYG"] == pytest.approx(
        r_single["total_tax_credit"]
    )

    # Summary totals match
    assert r_multi["total_capitalized"] == pytest.approx(
        r_single["total_acquisition_cost"]
    )
    assert r_multi["total_tax_credit"] == pytest.approx(
        r_single["total_tax_credit"]
    )


# --- 8. 2 products with allocation ---

def test_multi_two_products_allocation(two_products_df, multi_kwargs):
    """Two products: allocations should sum to shared totals."""
    r = calc_multi_product(
        two_products_df.copy(), EX_RATE, PERCEP_IRE_RATE, **multi_kwargs
    )
    assert r is not None

    prods = r["products_df"]
    assert len(prods) == 2

    # Freight and insurance allocations must sum to the shared amount
    assert prods["Alloc_Freight_USD"].sum() == pytest.approx(
        multi_kwargs["multi_freight_usd"]
    )
    assert prods["Alloc_Insurance_USD"].sum() == pytest.approx(
        multi_kwargs["multi_insurance_usd"]
    )

    # Per-product totals are > 0
    for _, row in prods.iterrows():
        assert row["Total_FOB_USD"] > 0
        assert row["CIF_PYG"] > 0
        assert row["Stückkosten_PYG"] > 0
        assert row["Total_Tax_Credit_PYG"] >= 0

    # Summary totals > 0
    assert r["total_capitalized"] > 0
    assert r["total_tax_credit"] > 0

    # FOB and weight sums are captured
    assert r["sum_fob_usd"] > 0
    assert r["sum_weight_kg"] > 0


# --- 9. Weight-based vs value-based allocation difference ---

def test_multi_weight_vs_value_allocation(two_products_df, multi_kwargs):
    """Weight-based and value-based allocations produce different per-product results."""
    # Weight-based freight (alloc_freight=0), value-based local (alloc_local=0) – baseline
    kw_weight_freight = dict(multi_kwargs)
    kw_weight_freight["alloc_freight"] = 0  # weight
    kw_weight_freight["alloc_local"] = 0    # value
    r_weight_freight = calc_multi_product(
        two_products_df.copy(), EX_RATE, PERCEP_IRE_RATE, **kw_weight_freight
    )

    # Value-based freight (alloc_freight=1), weight-based local (alloc_local=1)
    kw_value_freight = dict(multi_kwargs)
    kw_value_freight["alloc_freight"] = 1  # value
    kw_value_freight["alloc_local"] = 1    # weight
    r_value_freight = calc_multi_product(
        two_products_df.copy(), EX_RATE, PERCEP_IRE_RATE, **kw_value_freight
    )

    # Allocation shares differ between the two modes
    p1_w = r_weight_freight["products_df"].iloc[0]
    p2_w = r_weight_freight["products_df"].iloc[1]
    p1_v = r_value_freight["products_df"].iloc[0]
    p2_v = r_value_freight["products_df"].iloc[1]

    # Because weight share ≠ value share, per-product allocations differ
    assert p1_w["Alloc_Freight_USD"] != pytest.approx(p1_v["Alloc_Freight_USD"])
    assert p2_w["Alloc_Freight_USD"] != pytest.approx(p2_v["Alloc_Freight_USD"])

    # But totals still sum to the same shared amount
    for col in ["Alloc_Freight_USD", "Alloc_Insurance_USD"]:
        assert r_weight_freight["products_df"][col].sum() == pytest.approx(
            r_value_freight["products_df"][col].sum()
        )

    # When DAI rates differ across products, shifting CIF via allocation changes
    # total DAI → totals differ slightly. That's correct behavior, not a bug.
    # Verify both produce valid, positive totals.
    assert r_weight_freight["total_capitalized"] > 0
    assert r_value_freight["total_capitalized"] > 0
    assert r_weight_freight["total_tax_credit"] > 0
    assert r_value_freight["total_tax_credit"] > 0


# ============================================================================
# Additional edge-case tests
# ============================================================================

def test_multi_empty_df():
    """Empty DataFrame returns None."""
    r = calc_multi_product(
        pd.DataFrame(), EX_RATE, PERCEP_IRE_RATE,
        multi_freight_usd=1000, multi_insurance_usd=100,
        multi_inland_pyg=500000, multi_inland_iva_incl=True,
        multi_val_mode=0, multi_val_pyg_manual=0, multi_indi_rate=7,
        multi_canon_sofia=50000, multi_consulado=200000,
        multi_tasa_portuaria=500000, multi_despachante=1000000,
        multi_despachante_iva_incl=True, multi_sonstiges=100000,
        alloc_freight=0, alloc_local=0,
    )
    assert r is None


def test_multi_zero_fob_returns_none():
    """When sum of FOB <= 0, calc_multi_product returns None."""
    df = _make_products_df(
        [
            {
                "Produktname": "Zero",
                "Menge": 0,
                "FOB pro Stk. (USD)": 0.0,
                "Gewicht pro Stk. (kg)": 0.0,
                "DAI (%)": 0.0,
            }
        ]
    )
    r = calc_multi_product(
        df, EX_RATE, PERCEP_IRE_RATE,
        multi_freight_usd=1000, multi_insurance_usd=100,
        multi_inland_pyg=500000, multi_inland_iva_incl=True,
        multi_val_mode=0, multi_val_pyg_manual=0, multi_indi_rate=7,
        multi_canon_sofia=50000, multi_consulado=200000,
        multi_tasa_portuaria=500000, multi_despachante=1000000,
        multi_despachante_iva_incl=True, multi_sonstiges=100000,
        alloc_freight=0, alloc_local=0,
    )
    assert r is None


def test_single_missing_keys_defaults():
    """Missing keys get defaults (0, 0.0, True). No crash."""
    r = calc_single_product({}, EX_RATE, PERCEP_IRE_RATE)
    assert r["total_fob_usd"] == 0.0
    assert r["unit_cost_pyg"] == 0.0
    assert r["cif_pyg"] == 0.0
    assert r["dai_pyg"] == 0.0
