import unittest
from pdf_export import export_to_pdf
import os


class TestPDFExport(unittest.TestCase):
    def test_pdf_export_basic(self):
        results = {"FOB": 1000, "CIF": 1250, "DAI": 175}
        filename = export_to_pdf(results, language="de", filename="/tmp/test_export.pdf")
        self.assertTrue(os.path.exists(filename))
        self.assertGreater(os.path.getsize(filename), 0)
        os.remove(filename)

    def test_pdf_export_single_product_results(self):
        """Test with realistic single-product calculation results."""
        results = {
            "total_fob_usd": 45000.0,
            "total_fob_pyg": 346500000.0,
            "cif_usd": 48900.0,
            "cif_pyg": 376530000.0,
            "inland_netto": 2727272.73,
            "inland_iva": 272727.27,
            "despachante_netto": 2272727.27,
            "despachante_iva": 227272.73,
            "dai_pyg": 22591800.0,
            "val_pyg": 1882650.0,
            "indi_pyg": 1581426.0,
            "capitalized_logistics": 349053545.45,
            "capitalized_customs": 30253703.27,
            "total_acquisition_cost": 725807248.72,
            "unit_cost_pyg": 7258072.49,
            "unit_cost_usd": 942.61,
            "iva_importacion": 40099887.6,
            "percepcion_ire": 1506120.0,
            "total_tax_credit": 42107007.6,
            "base_iva_aduana": 400998876.0,
        }
        for lang in ("de", "en", "es"):
            filename = export_to_pdf(results, language=lang, filename=f"/tmp/test_single_{lang}.pdf")
            self.assertTrue(os.path.exists(filename))
            self.assertGreater(os.path.getsize(filename), 0)
            os.remove(filename)

    def test_pdf_export_multi_product_results(self):
        """Test with realistic multi-product DataFrame."""
        import pandas as pd

        prods = pd.DataFrame({
            "Produktname": ["Laptop", "Monitor"],
            "Menge": [10, 5],
            "Total_FOB_USD": [4500.0, 2000.0],
            "Total_Weight_kg": [25.0, 50.0],
            "CIF_PYG": [37653000.0, 16734666.67],
            "DAI_PYG": [2259180.0, 1004080.0],
            "Val_PYG": [188265.0, 83673.33],
            "INDI_PYG": [158142.6, 70285.6],
            "Alloc_Local_PYG": [500000.0, 250000.0],
            "Total_Capitalized_PYG": [40720587.6, 18082705.6],
            "Stückkosten_PYG": [4072058.76, 3616541.12],
            "Stückkosten_USD": [528.84, 469.68],
            "IVA_Importacion_PYG": [4014358.56, 1782923.76],
            "Percepcion_IRE_PYG": [150612.0, 66938.67],
            "Alloc_Inland_IVA": [10000.0, 5000.0],
            "Alloc_Broker_IVA": [8000.0, 4000.0],
            "Total_Tax_Credit_PYG": [4182970.56, 1858862.43],
        })
        for lang in ("de", "en", "es"):
            filename = export_to_pdf(prods, language=lang, filename=f"/tmp/test_multi_{lang}.pdf")
            self.assertTrue(os.path.exists(filename))
            self.assertGreater(os.path.getsize(filename), 0)
            os.remove(filename)

    def test_pdf_export_invalid_language_fallback(self):
        """Invalid language should fall back to German."""
        results = {"FOB": 1000, "CIF": 1250, "DAI": 175}
        filename = export_to_pdf(results, language="fr", filename="/tmp/test_lang.pdf")
        self.assertTrue(os.path.exists(filename))
        self.assertGreater(os.path.getsize(filename), 0)
        os.remove(filename)


if __name__ == "__main__":
    unittest.main()
