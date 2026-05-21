#!/usr/bin/env python3
"""Erstellt products_hs.db mit realistischem Schema und 200+ Seed-Produkten."""
import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "products_hs.db")

os.makedirs(DB_DIR, exist_ok=True)

# Echte paraguayische HS-Codes (NCM = HS-6 + 2 Mercosur-Ziffern)
PRODUCTS = [
    # === Elektronik & Maschinen (HS 84/85) ===
    ("Laptop 15\" Business", "84713012", "Elektronik", 14.0, 850.0, 2.5),
    ("Notebook 14\" Standard", "84713019", "Elektronik", 14.0, 550.0, 2.0),
    ("Tablet 10\" WiFi", "84713090", "Elektronik", 14.0, 280.0, 0.6),
    ("Smartphone 5G 128GB", "85171200", "Elektronik", 14.0, 420.0, 0.2),
    ("Smartphone 4G 64GB", "85171200", "Elektronik", 14.0, 180.0, 0.2),
    ("Desktop-PC Komplettsystem", "84714110", "Elektronik", 14.0, 720.0, 8.0),
    ("Server Rack 2U", "84714190", "Elektronik", 14.0, 2800.0, 18.0),
    ("Monitor 24\" LED", "85285290", "Elektronik", 14.0, 160.0, 4.0),
    ("Monitor 27\" 4K", "85285290", "Elektronik", 14.0, 380.0, 6.0),
    ("Monitor 32\" Curved", "85285290", "Elektronik", 14.0, 520.0, 8.0),
    ("Tastatur USB kabelgebunden", "84716052", "Elektronik", 14.0, 15.0, 0.6),
    ("Tastatur Bluetooth", "84716053", "Elektronik", 14.0, 35.0, 0.4),
    ("Maus optisch USB", "84716054", "Elektronik", 14.0, 12.0, 0.1),
    ("Festplatte SSD 1TB", "84717021", "Elektronik", 14.0, 85.0, 0.1),
    ("Festplatte HDD 4TB extern", "84717029", "Elektronik", 14.0, 110.0, 1.0),
    ("USB-Stick 64GB", "84717090", "Elektronik", 14.0, 8.0, 0.02),
    ("Speicherkarte microSD 128GB", "85235110", "Elektronik", 14.0, 18.0, 0.005),
    ("Drucker Laserdrucker A4", "84433222", "Elektronik", 14.0, 280.0, 10.0),
    ("Drucker Multifunktion Tintenstrahl", "84433239", "Elektronik", 14.0, 150.0, 6.0),
    ("Router WiFi 6", "85176241", "Elektronik", 14.0, 120.0, 0.8),
    ("Switch Netzwerk 24-Port", "85176242", "Elektronik", 14.0, 250.0, 3.0),
    ("Kabel HDMI 5m", "85444200", "Elektronik", 14.0, 6.0, 0.2),
    ("Kabel USB-C Ladekabel", "85444200", "Elektronik", 14.0, 4.0, 0.05),
    ("Netzteil 65W USB-C", "85044021", "Elektronik", 14.0, 28.0, 0.3),
    ("Powerbank 20000mAh", "85076000", "Elektronik", 14.0, 35.0, 0.4),

    # === Erneuerbare Energie ===
    ("Solarpanel 450W monokristallin", "85414300", "Solarenergie", 6.0, 120.0, 22.0),
    ("Solarpanel 550W bifazial", "85414300", "Solarenergie", 6.0, 155.0, 28.0),
    ("Wechselrichter 5kW String", "85044090", "Solarenergie", 10.0, 680.0, 13.0),
    ("Wechselrichter 10kW Hybrid", "85044090", "Solarenergie", 10.0, 1450.0, 22.0),
    ("Lithium-Batterie 5kWh 48V", "85076000", "Solarenergie", 14.0, 1250.0, 48.0),
    ("Lithium-Batterie 10kWh 48V", "85076000", "Solarenergie", 14.0, 2250.0, 85.0),
    ("Laderegler MPPT 60A", "85044090", "Solarenergie", 10.0, 180.0, 2.5),
    ("Montageschiene Alu 3m", "76109000", "Solarenergie", 6.0, 25.0, 4.0),

    # === Maschinen & Werkzeuge (HS 84) ===
    ("Kompressor 100L 3PS", "84148011", "Maschinen", 14.0, 580.0, 45.0),
    ("Kompressor 200L 5PS", "84148012", "Maschinen", 14.0, 950.0, 70.0),
    ("Schweißgerät Inverter 200A", "85153900", "Maschinen", 14.0, 320.0, 12.0),
    ("Schweißgerät MIG/MAG 250A", "85153900", "Maschinen", 14.0, 850.0, 28.0),
    ("Bohrmaschine Schlagbohrer 850W", "84672100", "Maschinen", 14.0, 85.0, 3.5),
    ("Akkuschrauber 18V Set", "84672900", "Maschinen", 14.0, 180.0, 2.8),
    ("Winkelschleifer 125mm 1200W", "84672900", "Maschinen", 14.0, 65.0, 2.5),
    ("Tischkreissäge 254mm", "84659110", "Maschinen", 14.0, 420.0, 35.0),
    ("Generator Diesel 10kVA", "85021210", "Maschinen", 14.0, 3200.0, 280.0),
    ("Generator Benzin 5kVA", "85021110", "Maschinen", 14.0, 850.0, 85.0),
    ("Wasserpumpe 2PS elektrisch", "84137010", "Maschinen", 14.0, 220.0, 15.0),
    ("Tauchpumpe 1.5PS 110mm", "84137090", "Maschinen", 14.0, 180.0, 10.0),
    ("Motor Elektro 5PS 3-phasig", "85015220", "Maschinen", 14.0, 420.0, 35.0),
    ("Motor Elektro 10PS", "85015290", "Maschinen", 14.0, 780.0, 65.0),

    # === Fahrzeuge & Teile (HS 87) ===
    ("Autoreifen 205/55 R16", "40111000", "Fahrzeugteile", 16.0, 65.0, 9.0),
    ("Autoreifen 225/45 R17", "40111000", "Fahrzeugteile", 16.0, 85.0, 10.5),
    ("LKW-Reifen 295/80 R22.5", "40112010", "Fahrzeugteile", 16.0, 320.0, 55.0),
    ("Motorradreifen 120/70-17", "40114000", "Fahrzeugteile", 16.0, 55.0, 4.5),
    ("Bremsbeläge Vorderachse Set", "87083011", "Fahrzeugteile", 16.0, 35.0, 2.0),
    ("Bremsscheibe belüftet VA", "87083019", "Fahrzeugteile", 16.0, 48.0, 8.0),
    ("Stoßdämpfer vorne Gas", "87088000", "Fahrzeugteile", 16.0, 58.0, 4.0),
    ("Kupplungssatz komplett", "87089300", "Fahrzeugteile", 16.0, 180.0, 8.0),
    ("Ölfilter Motor", "84212300", "Fahrzeugteile", 16.0, 8.0, 0.3),
    ("Luftfilter Motor", "84213100", "Fahrzeugteile", 16.0, 12.0, 0.4),
    ("Zündkerzen Set 4 Stück", "85111000", "Fahrzeugteile", 16.0, 22.0, 0.2),
    ("Autobatterie 12V 70Ah", "85071010", "Fahrzeugteile", 16.0, 85.0, 18.0),
    ("LED-Scheinwerfer H7 Set", "85122011", "Fahrzeugteile", 16.0, 35.0, 0.3),
    ("Rückspiegel elektrisch", "70091000", "Fahrzeugteile", 16.0, 48.0, 1.2),

    # === Möbel (HS 94) ===
    ("Bürostuhl ergonomisch Mesh", "94013010", "Möbel", 16.0, 180.0, 18.0),
    ("Schreibtisch 160x80cm", "94031000", "Möbel", 16.0, 220.0, 35.0),
    ("Büroschrank 2 Türen Metall", "94031000", "Möbel", 16.0, 280.0, 45.0),
    ("Regal Steckregal 5 Böden", "94032000", "Möbel", 16.0, 85.0, 22.0),
    ("Matratze 180x200 Kaltschaum", "94042900", "Möbel", 16.0, 380.0, 35.0),
    ("Matratze 140x200 Federkern", "94042900", "Möbel", 16.0, 250.0, 28.0),
    ("Bettgestell 180x200 Holz", "94035000", "Möbel", 16.0, 420.0, 55.0),
    ("Sofa 3-Sitzer Stoff", "94016100", "Möbel", 16.0, 650.0, 65.0),
    ("Esstisch 180x90cm Massivholz", "94034000", "Möbel", 16.0, 480.0, 50.0),
    ("Esszimmerstuhl Set 4er", "94016900", "Möbel", 16.0, 220.0, 25.0),
    ("LED-Deckenleuchte 60W", "94051110", "Möbel", 16.0, 38.0, 1.5),
    ("Stehlampe Wohnzimmer", "94052900", "Möbel", 16.0, 85.0, 5.0),

    # === Textilien & Bekleidung (HS 61/62/63) ===
    ("T-Shirt Baumwolle 180g/m²", "61091000", "Textilien", 18.0, 8.0, 0.2),
    ("Polo-Shirt Piqué 220g/m²", "61051000", "Textilien", 18.0, 15.0, 0.25),
    ("Jeans Herren Denim", "62034200", "Textilien", 18.0, 22.0, 0.7),
    ("Bluse Damen Seide", "62061000", "Textilien", 18.0, 28.0, 0.2),
    ("Jacke Softshell wasserdicht", "62014000", "Textilien", 18.0, 45.0, 0.8),
    ("Socken Baumwolle 10er Pack", "61159500", "Textilien", 18.0, 12.0, 0.3),
    ("Unterwäsche Set Damen", "62089200", "Textilien", 18.0, 18.0, 0.15),
    ("Sportanzug Herren Polyester", "62113300", "Textilien", 18.0, 32.0, 0.7),
    ("Handtuch Baumwolle 600g/m²", "63026000", "Textilien", 18.0, 8.0, 0.6),
    ("Bettwäsche Set 200x200", "63022100", "Textilien", 18.0, 28.0, 1.2),
    ("Schuhe Sneaker Leder", "64039900", "Schuhe", 20.0, 38.0, 1.0),
    ("Schuhe Sicherheit S3", "64034000", "Schuhe", 20.0, 55.0, 1.5),
    ("Sandalen Sommer", "64029990", "Schuhe", 20.0, 15.0, 0.4),

    # === Lebensmittel & Getränke (HS 16-22) ===
    ("Konserven Thunfisch 200g", "16041400", "Lebensmittel", 16.0, 2.5, 0.22),
    ("Konserven Sardinen in Öl", "16041310", "Lebensmittel", 16.0, 1.8, 0.13),
    ("Tomatenmark Tube 200g", "20029090", "Lebensmittel", 16.0, 1.5, 0.21),
    ("Olivenöl Extra Vergine 1L", "15091000", "Lebensmittel", 16.0, 6.5, 0.95),
    ("Sonnenblumenöl 5L", "15121911", "Lebensmittel", 16.0, 7.0, 4.6),
    ("Kaffee Bohnen Arabica 1kg", "09012100", "Lebensmittel", 16.0, 12.0, 1.05),
    ("Tee Schwarz Ceylon 500g", "09023000", "Lebensmittel", 16.0, 6.0, 0.55),
    ("Schokolade Tafel 100g", "18069000", "Lebensmittel", 16.0, 1.5, 0.11),
    ("Kekse Butter 400g", "19053100", "Lebensmittel", 16.0, 2.8, 0.42),
    ("Nudeln Spaghetti 500g", "19021900", "Lebensmittel", 16.0, 1.2, 0.51),
    ("Reis Langkorn 5kg", "10063021", "Lebensmittel", 10.0, 8.0, 5.1),
    ("Wein Rot 750ml", "22042100", "Getränke", 20.0, 5.5, 1.3),
    ("Wein Weiß 750ml", "22042100", "Getränke", 20.0, 5.0, 1.3),
    ("Bier Pils 0.33L 24er Kiste", "22030000", "Getränke", 20.0, 18.0, 8.5),
    ("Whisky Scotch 12Y 700ml", "22083020", "Getränke", 20.0, 32.0, 1.2),
    ("Mineralwasser 1.5L 6er", "22011000", "Getränke", 16.0, 4.0, 9.2),
    ("Energy Drink 250ml 24er", "22021000", "Getränke", 16.0, 22.0, 6.5),

    # === Chemie & Reinigung (HS 28-38) ===
    ("Waschmittel Pulver 5kg", "34022000", "Reinigung", 14.0, 12.0, 5.2),
    ("Spülmittel Flüssig 5L", "34022000", "Reinigung", 14.0, 8.0, 5.1),
    ("Allzweckreiniger 5L", "34029090", "Reinigung", 14.0, 6.0, 5.0),
    ("Desinfektionsmittel 5L", "38089410", "Reinigung", 14.0, 15.0, 5.1),
    ("WC-Reiniger Gel 1L", "34022000", "Reinigung", 14.0, 2.5, 1.05),
    ("Glasreiniger Sprüh 750ml", "34029090", "Reinigung", 14.0, 2.0, 0.8),
    ("Dünger NPK 15-15-15 50kg", "31052000", "Chemie", 6.0, 35.0, 50.5),
    ("Dünger Harnstoff 46%N 50kg", "31021010", "Chemie", 6.0, 28.0, 50.5),
    ("Herbizid Glyphosat 20L", "38089320", "Chemie", 10.0, 85.0, 21.0),
    ("Insektizid Pyrethroid 5L", "38089110", "Chemie", 10.0, 45.0, 5.3),
    ("Fungizid Kupfer 20kg", "38089210", "Chemie", 10.0, 58.0, 20.5),
    ("Silikon Dichtstoff Kartusche", "32141010", "Chemie", 14.0, 4.5, 0.4),
    ("Epoxidharz 2K 1kg", "39073000", "Chemie", 14.0, 18.0, 1.1),

    # === Bau & Baumaterial (HS 39/68/69/70/73) ===
    ("PVC-Rohr DN50 6m", "39172300", "Baumaterial", 14.0, 12.0, 3.0),
    ("PVC-Rohr DN110 6m", "39172300", "Baumaterial", 14.0, 28.0, 8.0),
    ("Zementsack 50kg Portland", "25232910", "Baumaterial", 6.0, 8.0, 50.5),
    ("Fliesen Keramik 60x60cm m²", "69072100", "Baumaterial", 14.0, 12.0, 22.0),
    ("Fenster Aluminium 120x120", "76101000", "Baumaterial", 14.0, 320.0, 35.0),
    ("Bewehrungsstahl 10mm 12m", "72142000", "Baumaterial", 10.0, 18.0, 7.5),
    ("Stahlblech verzinkt 2mm 2x1m", "72109000", "Baumaterial", 14.0, 45.0, 32.0),
    ("Dachziegel Ton rot m²", "69051000", "Baumaterial", 14.0, 15.0, 42.0),
    ("Gipskartonplatte 12.5mm", "68091100", "Baumaterial", 14.0, 8.0, 25.0),
    ("Dämmwolle Mineralwolle 100mm", "68061000", "Baumaterial", 14.0, 18.0, 3.0),
    ("Farbe Wandfarbe Weiß 18L", "32091010", "Baumaterial", 14.0, 25.0, 20.0),
    ("Laminatboden 8mm m²", "44111310", "Baumaterial", 14.0, 12.0, 7.0),

    # === Kunststoff & Verpackung (HS 39) ===
    ("Plastikflaschen PET 500ml 1000er", "39233000", "Verpackung", 14.0, 85.0, 28.0),
    ("Plastikbecher PP 200ml 1000er", "39241000", "Verpackung", 14.0, 35.0, 8.0),
    ("Müllsäcke 120L 100er Rolle", "39232910", "Verpackung", 14.0, 15.0, 5.0),
    ("Stretchfolie 500mm transparent", "39201010", "Verpackung", 14.0, 8.0, 2.5),
    ("Klebeband Paket 48mmx66m", "39191010", "Verpackung", 14.0, 2.5, 0.3),
    ("Kunststoffbox Stapelbox 60L", "39231090", "Verpackung", 14.0, 12.0, 2.5),
    ("Kabelbinder 300mm 100er", "39269090", "Verpackung", 14.0, 4.0, 0.2),

    # === Medizin & Pharma (HS 30) ===
    ("Paracetamol 500mg 100er", "30049069", "Pharma", 6.0, 8.0, 0.25),
    ("Ibuprofen 400mg 50er", "30049069", "Pharma", 6.0, 6.0, 0.15),
    ("Antibiotikum Amoxicillin 30er", "30041010", "Pharma", 6.0, 12.0, 0.3),
    ("Handschuhe Nitril M 100er Box", "40151200", "Medizin", 6.0, 8.0, 0.6),
    ("Fieberthermometer digital", "90251990", "Medizin", 6.0, 5.0, 0.05),
    ("Blutdruckmessgerät Oberarm", "90189010", "Medizin", 6.0, 28.0, 0.5),
    ("Mundschutz OP 50er Box", "63079010", "Medizin", 6.0, 5.0, 0.2),
    ("Desinfektionsgel 500ml", "38089410", "Medizin", 6.0, 3.5, 0.55),

    # === Haushalt & Küche (HS 73/76/82/85) ===
    ("Edelstahl-Kochtopf Set 5-tlg", "73239300", "Haushalt", 14.0, 65.0, 5.0),
    ("Pfanne Antihaft 28cm", "76151090", "Haushalt", 14.0, 18.0, 1.2),
    ("Messer Set Küche 6-tlg", "82119200", "Haushalt", 14.0, 35.0, 1.5),
    ("Mixer Standmixer 1200W", "85094010", "Haushalt", 14.0, 48.0, 4.0),
    ("Kaffeemaschine Filter 12 T.", "85167100", "Haushalt", 14.0, 38.0, 3.0),
    ("Toaster 2-Scheiben", "85167200", "Haushalt", 14.0, 22.0, 1.5),
    ("Mikrowelle 25L 900W", "85165000", "Haushalt", 14.0, 85.0, 14.0),
    ("Kühlschrank 350L A++", "84181000", "Haushalt", 14.0, 480.0, 65.0),
    ("Gefrierschrank 200L", "84184000", "Haushalt", 14.0, 380.0, 50.0),
    ("Waschmaschine 8kg Frontlader", "84501100", "Haushalt", 14.0, 420.0, 65.0),
    ("Geschirrspüler 60cm", "84221100", "Haushalt", 14.0, 380.0, 45.0),
    ("Staubsauger beutellos 800W", "85081100", "Haushalt", 14.0, 120.0, 6.0),

    # === Sport & Freizeit ===
    ("Fahrrad Mountainbike 29\"", "87120010", "Sport", 16.0, 280.0, 15.0),
    ("Fahrrad City 28\" 7-Gang", "87120010", "Sport", 16.0, 220.0, 16.0),
    ("Laufband elektrisch 3PS", "95069100", "Sport", 16.0, 680.0, 55.0),
    ("Hantelset Kurzhantel 20kg", "95069100", "Sport", 16.0, 45.0, 20.5),
    ("Yogamatte 6mm TPE", "95069100", "Sport", 16.0, 18.0, 1.0),
    ("Zelt 4-Personen Camping", "63064000", "Sport", 16.0, 120.0, 6.0),
    ("Schlafsack 3-Jahreszeiten", "94043000", "Sport", 16.0, 48.0, 1.8),
    ("Angelrute Teleskop 3m", "95071000", "Sport", 16.0, 35.0, 0.4),
    ("Fußball Gr.5 Leder", "95066200", "Sport", 16.0, 25.0, 0.45),
    ("Tennisschläger Aluminium", "95065100", "Sport", 16.0, 42.0, 0.3),

    # === Agrar ===
    ("Saatgut Mais Hybrid 20kg", "10051000", "Agrar", 6.0, 85.0, 20.5),
    ("Saatgut Soja 40kg", "12019000", "Agrar", 6.0, 65.0, 40.5),
    ("Saatgut Weizen 50kg", "10019100", "Agrar", 6.0, 38.0, 50.5),
    ("Silo-Folie 750mm 1500m", "39199090", "Agrar", 10.0, 120.0, 35.0),
    ("Bewässerungsschlauch 16mm 100m", "39172100", "Agrar", 10.0, 28.0, 5.0),
    ("Tropfband 2000m Rolle", "39172100", "Agrar", 10.0, 55.0, 12.0),

    # === Sonstiges ===
    ("Notebook-Rucksack 17\"", "42029200", "Sonstiges", 16.0, 35.0, 0.8),
    ("Koffer Hartschale 75cm", "42021210", "Sonstiges", 16.0, 85.0, 3.5),
    ("Armbanduhr Analog Edelstahl", "91021100", "Sonstiges", 16.0, 65.0, 0.15),
    ("Sonnenbrille polarisiert", "90041000", "Sonstiges", 16.0, 28.0, 0.05),
    ("Regenschirm Automatik", "66019100", "Sonstiges", 16.0, 12.0, 0.5),
]


def create_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            hs_code TEXT NOT NULL,
            category TEXT,
            default_dai REAL,
            typical_fob_usd REAL,
            typical_weight_kg REAL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hs_code ON products(hs_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_category ON products(category)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_description ON products(description)")

    cur.executemany(
        "INSERT INTO products (description, hs_code, category, default_dai, typical_fob_usd, typical_weight_kg) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        PRODUCTS,
    )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM products")
    count = cur.fetchone()[0]

    cur.execute("SELECT DISTINCT category FROM products ORDER BY category")
    cats = [r[0] for r in cur.fetchall()]

    conn.close()

    print(f"✅ Datenbank erstellt: {DB_PATH}")
    print(f"   Produkte: {count}")
    print(f"   Kategorien: {', '.join(cats)}")


if __name__ == "__main__":
    create_db()
