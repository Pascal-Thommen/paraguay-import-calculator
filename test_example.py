#!/usr/bin/env python3
"""Verify example calculation matches reference values."""
import sys
sys.path.insert(0, '/opt/data/kanban/boards/import-calculator/workspaces/v5-master')
from calculator import calculate

proveedor = [{"descripcion": "Producto China", "betrag": 150000.0, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1.0, "peso_volumen": 0.0}]

flete = [
    {"descripcion": "Flete maritimo + interno", "betrag": 20250.20, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Seguro",                   "betrag": 6380.00, "aufteilung": "wert", "impuesto": "Exento", "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Flete interno Paraguay",    "betrag": 2200000.00, "aufteilung": "monto", "impuesto": "10%", "cantidad": 1.0, "peso_volumen": 0.0},
]

importacion = [
    {"descripcion": "Derecho Aduanero",               "betrag": 5420750.0,  "aufteilung": "monto", "impuesto": "Exento",       "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Servicio de Valoracion Aduanera","betrag": 1350285.0,  "aufteilung": "monto", "impuesto": "Exento",       "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "INDI",                            "betrag": 217832.0,   "aufteilung": "monto", "impuesto": "Exento",       "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Percepcion de IRE",               "betrag": 3565000.0,  "aufteilung": "monto", "impuesto": "Anticipo IRE", "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Impuesto Selectivo al Consumo",   "betrag": 0.0,        "aufteilung": "monto", "impuesto": "Exento",       "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "IVA",                             "betrag": 122500000.0,"aufteilung": "monto", "impuesto": "IVA CF",       "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Canon Informatico Sofia",         "betrag": 350000.0,   "aufteilung": "monto", "impuesto": "Exento",       "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Visacion consular",               "betrag": 1890301.0,  "aufteilung": "monto", "impuesto": "Exento",       "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Tasa Portuaria",                  "betrag": 1456380.0,  "aufteilung": "monto", "impuesto": "10%",          "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Fotocopias",                      "betrag": 55000.0,    "aufteilung": "monto", "impuesto": "10%",          "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Gastos de Estiba/Desestiba",      "betrag": 1320000.0,  "aufteilung": "monto", "impuesto": "10%",          "cantidad": 1.0, "peso_volumen": 0.0},
    {"descripcion": "Honorarios del Despachante",      "betrag": 3850246.0,  "aufteilung": "monto", "impuesto": "10%",          "cantidad": 1.0, "peso_volumen": 0.0},
]

nacional = [{"descripcion": "Flete aduana deposito", "betrag": 0.0, "aufteilung": "masseinheit", "impuesto": "10%", "cantidad": 1.0, "peso_volumen": 0.0}]

r = calculate(proveedor, flete, importacion, nacional, 8000.0, 8000.0)

print(f"FOB (Gs):      {r['fob_gs']:>18,.0f}   (expected:  1,200,000,000)")
print(f"Flete (Gs):    {r['flete_total_gs']:>18,.0f}   (expected:  ~215,041,600)")
print(f"CIF (Gs):      {r['cif_gs']:>18,.0f}   (expected: ~1,415,041,600)")
print(f"Import (Gs):   {r['total_importacion']:>18,.0f}   (expected:  ~141,975,794)")
print(f"Nacional (Gs): {r['total_nacional']:>18,.0f}")
print(f"Gran Total:    {r['gran_total']:>18,.0f}   (expected: ~1,557,017,394)")

# Manual importacion sum
manual_imp = sum(it["betrag"] for it in importacion)
manual_flete_usd = 20250.20 + 6380.00
manual_flete_pyg = manual_flete_usd * 8000 + 2200000
print(f"\nManual checks:")
print(f"  Flete USD part: {manual_flete_usd:,.2f} USD * 8000 = {manual_flete_usd * 8000:,.0f} PYG")
print(f"  Flete PYG part: 2,200,000 PYG")
print(f"  Flete total:    {manual_flete_pyg:,.0f} PYG")
print(f"  CIF = FOB + Flete = {r['fob_gs'] + r['flete_total_gs']:,.0f} PYG")

print(f"\nImportacion detail:")
for it in r['importacion']:
    print(f"  {it['descripcion']:40s}  costo={it['costo_gs']:>15,.0f}  iva={it['iva_gs']:>12,.0f}")

print(f"\nFlete detail:")
for it in r['flete']:
    print(f"  {it['descripcion']:40s}  costo={it['costo_gs']:>15,.0f}  iva={it['iva_gs']:>12,.0f}")
