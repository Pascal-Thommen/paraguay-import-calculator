"""
Test Suite for Paraguay Import Calculator v5
Tests all critical calculation logic, edge cases, and known bug fixes.
Run: python3 tests/test_calculator.py
"""
import sys
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculator import calculate, PROVEEDOR_DEFAULTS, FLETE_DEFAULTS, IMPORTACION_DEFAULTS, NACIONAL_DEFAULTS


def assert_near(actual, expected, msg, tol=0.01):
    if abs(actual - expected) > tol:
        raise AssertionError(f"{msg}: expected {expected}, got {actual}")


def test_basic_fob_to_cif():
    """FOB $1000 + $100 Flete @ rate 7500 → CIF should be $1100, CIF_Gs = $1100*7500"""
    prov = [{"descripcion": "Producto A", "betrag": 1000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    flete = [{"descripcion": "Flete", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    imp = [{"descripcion": "DAI", "betrag": 14.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    nac = []
    result = calculate(prov, flete, imp, nac, 7500.0, 7500.0)
    assert_near(result["fob_currency"], 1000.0, "FOB currency")
    assert_near(result["fob_gs"], 7_500_000.0, "FOB Gs")
    assert_near(result["cif_gs"], 8_250_000.0, "CIF Gs")  # (1000+100)*7500
    assert_near(result["cif_currency"], 1100.0, "CIF currency")
    assert_near(result["total_importacion"], 1_155_000.0, "Importacion (14% of CIF)")
    assert_near(result["gran_total"], 9_405_000.0, "Gran total")
    print("✓ test_basic_fob_to_cif")


def test_masseinheit_aufteilung():
    """masseinheit: betrag * total_peso * exchange_rate"""
    prov = [{"descripcion": "Producto", "betrag": 500.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 100.0}]
    flete = [{"descripcion": "Flete per kg", "betrag": 5.0, "aufteilung": "masseinheit", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    imp = []
    nac = []
    result = calculate(prov, flete, imp, nac, 7500.0, 7500.0)
    # FOB = 500 * 7500 = 3,750,000
    # Flete = 5 * 100kg * 7500 = 3,750,000
    assert_near(result["flete_total_gs"], 3_750_000.0, "Flete masseinheit")
    assert_near(result["cif_gs"], 3_750_000.0 + 3_750_000.0, "CIF with masseinheit flete")
    assert result["flete"][0]["betrag"] == 500.0, f"Expected betrag=500, got {result['flete'][0]['betrag']}"
    print("✓ test_masseinheit_aufteilung")


def test_cantidad_aufteilung():
    """cantidad: betrag * total_cantidad * exchange_rate"""
    prov = [{"descripcion": "Producto", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 10, "peso_volumen": 0}]
    flete = [{"descripcion": "Flete per unit", "betrag": 2.0, "aufteilung": "cantidad", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    imp = []
    nac = []
    result = calculate(prov, flete, imp, nac, 7500.0, 7500.0)
    assert_near(result["flete_total_gs"], 20.0 * 7500.0, "Flete cantidad")
    print("✓ test_cantidad_aufteilung")


def test_iva_factor():
    """IVA: betrag should be split into sin_iva + iva_gs"""
    prov = [{"descripcion": "Producto", "betrag": 1000.0, "aufteilung": "wert", "impuesto": "10%", "cantidad": 1, "peso_volumen": 0}]
    result = calculate(prov, [], [], [], 7500.0, 7500.0)
    item = result["proveedor"][0]
    expected_sin_iva = round(1000.0 * 7500.0 / 1.10, 2)
    expected_iva = round(1000.0 * 7500.0 - expected_sin_iva, 2)
    assert_near(item["betrag_sin_iva"], expected_sin_iva, "sin_iva")
    assert_near(item["iva_gs"], expected_iva, "iva_gs")
    assert_near(item["costo_gs"], 7_500_000.0, "costo_gs")
    assert_near(item["betrag_sin_iva"] + item["iva_gs"], item["costo_gs"], "sin_iva + iva = total")
    print("✓ test_iva_factor")


def test_seguro_as_normal_flete_line():
    """Seguro is a normal flete line, not double counted. CIF = FOB + all flete lines"""
    prov = [{"descripcion": "Producto", "betrag": 1000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    flete = [
        {"descripcion": "Flete", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0},
        {"descripcion": "Seguro", "betrag": 50.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0},
    ]
    result = calculate(prov, flete, [], [], 7500.0, 7500.0)
    expected_cif = (1000.0 + 100.0 + 50.0) * 7500.0
    assert_near(result["cif_gs"], expected_cif, "CIF with Seguro as flete line")
    assert_near(result["flete_total_gs"], (100.0 + 50.0) * 7500.0, "Flete total")
    # No separate seguro_gs field should exist
    assert "seguro_gs" not in result, "seguro_gs should not exist (no separate seguro)"
    print("✓ test_seguro_as_normal_flete_line")


def test_importacion_percent_of_cif():
    """Importacion items with aufteilung='wert' use percent of CIF"""
    prov = [{"descripcion": "Producto", "betrag": 1000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    flete = [{"descripcion": "Flete", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    imp = [{"descripcion": "DAI", "betrag": 14.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    result = calculate(prov, flete, imp, [], 7500.0, 7500.0)
    cif_gs = result["cif_gs"]
    dai_gs = result["importacion"][0]["costo_gs"]
    expected_dai = cif_gs * 14.0 / 100.0
    assert_near(dai_gs, expected_dai, f"DAI should be 14% of CIF ({cif_gs})")
    print("✓ test_importacion_percent_of_cif")


def test_nacional_masseinheit():
    """Costo nacional with masseinheit uses total_peso"""
    prov = [{"descripcion": "Producto", "betrag": 500.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 50.0}]
    nac = [{"descripcion": "Transport", "betrag": 1000.0, "aufteilung": "masseinheit", "impuesto": "10%", "cantidad": 1, "peso_volumen": 0}]
    result = calculate(prov, [], [], nac, 7500.0, 7500.0)
    expected = 1000.0 * 50.0  # betrag * total_peso (no exchange rate for nacional!)
    assert_near(result["costo_nacional"][0]["costo_gs"], expected, "Nacional masseinheit")
    print("✓ test_nacional_masseinheit")


def test_gran_total_equals_sum():
    """CIF + total_importacion + total_nacional = gran_total"""
    prov = [{"descripcion": "A", "betrag": 100.0, "aufteilung": "wert", "impuesto": "10%", "cantidad": 5, "peso_volumen": 10.0}]
    flete = FLETE_DEFAULTS
    imp = IMPORTACION_DEFAULTS
    nac = NACIONAL_DEFAULTS
    result = calculate(prov, flete, imp, nac, 8000.0, 7800.0)
    expected = result["cif_gs"] + result["total_importacion"] + result["total_nacional"]
    assert_near(result["gran_total"], expected, "gran_total != sum of parts")
    print("✓ test_gran_total_equals_sum")


def test_per_unit_calculation():
    """gran_total_per_unit = gran_total / total_cantidad"""
    prov = [
        {"descripcion": "A", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 10, "peso_volumen": 0},
        {"descripcion": "B", "betrag": 200.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 5, "peso_volumen": 0},
    ]
    result = calculate(prov, [], [], [], 7500.0, 7500.0)
    total_cantidad = 15.0
    expected_per_unit = result["gran_total"] / total_cantidad
    assert_near(result["gran_total_per_unit"], expected_per_unit, "per unit")
    print("✓ test_per_unit_calculation")


def test_empty_lists():
    """Empty lists should not crash"""
    result = calculate([], [], [], [], 7500.0, 7500.0)
    assert_near(result["fob_currency"], 0.0, "empty FOB")
    assert_near(result["cif_gs"], 0.0, "empty CIF")
    assert_near(result["gran_total"], 0.0, "empty gran total")
    print("✓ test_empty_lists")


def test_defaults_load():
    """Default values should be valid and calculable"""
    result = calculate(PROVEEDOR_DEFAULTS, FLETE_DEFAULTS, IMPORTACION_DEFAULTS, NACIONAL_DEFAULTS, 7500.0, 7500.0)
    assert "gran_total" in result
    assert isinstance(result["gran_total"], (int, float))
    print("✓ test_defaults_load")


def test_iva_map_coverage():
    """All IVA variations should return correct rates"""
    from calculator import _iva_factor
    assert_near(_iva_factor("10%"), 0.10, "10%")
    assert_near(_iva_factor("5%"), 0.05, "5%")
    assert_near(_iva_factor("IVA CF"), 0.10, "IVA CF")
    assert_near(_iva_factor("IVA"), 0.10, "IVA")
    assert_near(_iva_factor("Exento"), 0.0, "Exento")
    assert_near(_iva_factor("exento"), 0.0, "exento lowercase")
    assert_near(_iva_factor("  10%  "), 0.10, "10% with spaces")
    print("✓ test_iva_map_coverage")


def test_different_fob_and_flete_rates():
    """FOB rate and Flete rate can differ"""
    prov = [{"descripcion": "Producto", "betrag": 1000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    flete = [{"descripcion": "Flete", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    result = calculate(prov, flete, [], [], 8000.0, 7500.0)
    # FOB in Gs = 1000 * 8000 = 8,000,000
    # Flete in Gs = 100 * 7500 = 750,000
    assert_near(result["fob_gs"], 8_000_000.0, "FOB with different rate")
    assert_near(result["flete_total_gs"], 750_000.0, "Flete with different rate")
    assert_near(result["cif_gs"], 8_750_000.0, "CIF with different rates")
    # CIF currency uses flete rate
    assert_near(result["cif_currency"], 1166.67, "CIF currency at flete rate")
    print("✓ test_different_fob_and_flete_rates")


def test_total_non_fob_costs():
    """total_non_fob_costs = flete_total_gs + total_importacion + total_nacional"""
    prov = [{"descripcion": "Producto", "betrag": 1000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    flete = [{"descripcion": "Flete", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    imp = [{"descripcion": "dai", "betrag": 14.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    nac = [{"descripcion": "Transport", "betrag": 50000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    result = calculate(prov, flete, imp, nac, 7500.0, 7500.0)
    expected = result["flete_total_gs"] + result["total_importacion"] + result["total_nacional"]
    assert_near(result["total_non_fob_costs"], expected, "total_non_fob_costs")
    assert result["total_non_fob_costs"] > 0, "total_non_fob_costs should be positive"
    print("✓ test_total_non_fob_costs")


def test_proveedor_summary_v7_fields():
    """proveedor_summary entries have v7 fields: cantidad, fob_anteil_pct, kosten_anteilig, steuern_anteilig, kosten_pro_einheit"""
    prov = [{"descripcion": "Widget A", "betrag": 1000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 10, "peso_volumen": 0}]
    flete = [{"descripcion": "Flete", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    imp = [{"descripcion": "dai", "betrag": 14.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    nac = [{"descripcion": "Transport", "betrag": 50000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    result = calculate(prov, flete, imp, nac, 7500.0, 7500.0)
    summary = result["proveedor_summary"][0]
    # All v7 fields present
    for field in ["cantidad", "fob_anteil_pct", "kosten_anteilig", "steuern_anteilig", "kosten_pro_einheit"]:
        assert field in summary, f"Missing field: {field}"
    # Legacy fields still present
    for field in ["descripcion", "kosten", "steuern", "gesamtbetrag", "kosten_pro_unidad"]:
        assert field in summary, f"Missing legacy field: {field}"
    assert_near(summary["cantidad"], 10.0, "cantidad")
    # Single product → 100% FOB share
    assert_near(summary["fob_anteil_pct"], 100.0, "fob_anteil_pct")
    print("✓ test_proveedor_summary_v7_fields")


def test_fob_anteil_pct_multiple_products():
    """fob_anteil_pct is proportional to product FOB / total FOB"""
    prov = [
        {"descripcion": "Product A", "betrag": 600.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 6, "peso_volumen": 0},
        {"descripcion": "Product B", "betrag": 400.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 4, "peso_volumen": 0},
    ]
    result = calculate(prov, [], [], [], 7500.0, 7500.0)
    s_a = result["proveedor_summary"][0]
    s_b = result["proveedor_summary"][1]
    assert_near(s_a["fob_anteil_pct"], 60.0, "product A share")
    assert_near(s_b["fob_anteil_pct"], 40.0, "product B share")
    assert_near(s_a["fob_anteil_pct"] + s_b["fob_anteil_pct"], 100.0, "shares sum to 100%")
    print("✓ test_fob_anteil_pct_multiple_products")


def test_kosten_anteilig_gt_fob():
    """kosten_anteilig > FOB alone (includes proportional non-FOB costs)"""
    prov = [{"descripcion": "Widget", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 5, "peso_volumen": 0}]
    flete = [{"descripcion": "Flete", "betrag": 50.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    imp = [{"descripcion": "dai", "betrag": 14.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    nac = [{"descripcion": "Transport", "betrag": 10000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    result = calculate(prov, flete, imp, nac, 7500.0, 7500.0)
    summary = result["proveedor_summary"][0]
    assert summary["kosten_anteilig"] > summary["gesamtbetrag"], \
        f"kosten_anteilig ({summary['kosten_anteilig']}) should exceed FOB ({summary['gesamtbetrag']})"
    print("✓ test_kosten_anteilig_gt_fob")


def test_kosten_pro_einheit():
    """kosten_pro_einheit = kosten_anteilig / cantidad"""
    prov = [{"descripcion": "Widget", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 5, "peso_volumen": 0}]
    flete = [{"descripcion": "Flete", "betrag": 50.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    imp = [{"descripcion": "dai", "betrag": 14.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    nac = [{"descripcion": "Transport", "betrag": 10000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    result = calculate(prov, flete, imp, nac, 7500.0, 7500.0)
    summary = result["proveedor_summary"][0]
    expected = summary["kosten_anteilig"] / summary["cantidad"]
    assert_near(summary["kosten_pro_einheit"], expected, "kosten_pro_einheit")
    print("✓ test_kosten_pro_einheit")


def test_proportional_costs_sum_to_total():
    """Sum of kosten_anteilig across all products = gran_total"""
    prov = [
        {"descripcion": "A", "betrag": 600.0, "aufteilung": "wert", "impuesto": "10%", "cantidad": 3, "peso_volumen": 0},
        {"descripcion": "B", "betrag": 400.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 2, "peso_volumen": 0},
    ]
    flete = [{"descripcion": "Flete", "betrag": 100.0, "aufteilung": "wert", "impuesto": "10%", "cantidad": 1, "peso_volumen": 0}]
    imp = [{"descripcion": "dai", "betrag": 14.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1, "peso_volumen": 0}]
    nac = [{"descripcion": "Transport", "betrag": 10000.0, "aufteilung": "wert", "impuesto": "10%", "cantidad": 1, "peso_volumen": 0}]
    result = calculate(prov, flete, imp, nac, 7500.0, 7500.0)
    sum_kosten = sum(s["kosten_anteilig"] for s in result["proveedor_summary"])
    assert_near(sum_kosten, result["gran_total"], "sum of kosten_anteilig = gran_total")
    print("✓ test_proportional_costs_sum_to_total")


def test_proveedor_summary():
    """proveedor_summary should have correct per-unit costs"""
    prov = [{"descripcion": "Widget", "betrag": 100.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 5, "peso_volumen": 0}]
    result = calculate(prov, [], [], [], 7500.0, 7500.0)
    summary = result["proveedor_summary"][0]
    assert_near(summary["kosten"], 750_000.0, "summary kosten")
    assert_near(summary["gesamtbetrag"], 750_000.0, "summary gesamtbetrag")
    assert_near(summary["kosten_pro_unidad"], 150_000.0, "summary per unit")  # 750000/5
    print("✓ test_proveedor_summary")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Paraguay Import Calculator Tests")
    print("=" * 60)
    tests = [
        test_basic_fob_to_cif,
        test_masseinheit_aufteilung,
        test_cantidad_aufteilung,
        test_iva_factor,
        test_seguro_as_normal_flete_line,
        test_importacion_percent_of_cif,
        test_nacional_masseinheit,
        test_gran_total_equals_sum,
        test_per_unit_calculation,
        test_empty_lists,
        test_defaults_load,
        test_iva_map_coverage,
        test_different_fob_and_flete_rates,
        test_proveedor_summary,
        test_total_non_fob_costs,
        test_proveedor_summary_v7_fields,
        test_fob_anteil_pct_multiple_products,
        test_kosten_anteilig_gt_fob,
        test_kosten_pro_einheit,
        test_proportional_costs_sum_to_total,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"✗ {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: ERROR: {e}")
            failed += 1
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
