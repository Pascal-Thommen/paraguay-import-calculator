-- Paraguay Import Cost Calculator — PostgreSQL Schema
-- IAS 2 / Ley 6380/19 compliant

CREATE TABLE IF NOT EXISTS calculations (
    id              SERIAL PRIMARY KEY,
    session_name    TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    language        TEXT NOT NULL DEFAULT 'de',
    status          TEXT NOT NULL DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS calc_inputs (
    id                  SERIAL PRIMARY KEY,
    calculation_id      INTEGER NOT NULL REFERENCES calculations(id) ON DELETE CASCADE,
    currency_fob        TEXT NOT NULL DEFAULT 'USD',
    exchange_rate_fob   REAL NOT NULL DEFAULT 7500.0,
    purchase_unit       TEXT NOT NULL DEFAULT 'kg',
    seguro_percent      REAL NOT NULL DEFAULT 2.0,
    currency_flete      TEXT NOT NULL DEFAULT 'USD',
    exchange_rate_flete REAL NOT NULL DEFAULT 7500.0,
    fob_currency        REAL NOT NULL DEFAULT 0.0,
    fob_gs              REAL NOT NULL DEFAULT 0.0,
    seguro_currency     REAL NOT NULL DEFAULT 0.0,
    seguro_gs           REAL NOT NULL DEFAULT 0.0,
    cif_currency        REAL NOT NULL DEFAULT 0.0,
    cif_gs              REAL NOT NULL DEFAULT 0.0,
    total_importacion   REAL NOT NULL DEFAULT 0.0,
    total_nacional      REAL NOT NULL DEFAULT 0.0,
    gran_total          REAL NOT NULL DEFAULT 0.0,
    gran_total_per_unit REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS proveedor_items (
    id              SERIAL PRIMARY KEY,
    calculation_id  INTEGER NOT NULL REFERENCES calculations(id) ON DELETE CASCADE,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    descripcion     TEXT NOT NULL DEFAULT '',
    betrag          REAL NOT NULL DEFAULT 0.0,
    aufteilung      TEXT NOT NULL DEFAULT 'wert',
    impuesto        TEXT NOT NULL DEFAULT 'Exento',
    cantidad        REAL NOT NULL DEFAULT 1.0,
    peso_volumen    REAL NOT NULL DEFAULT 0.0,
    betrag_sin_iva  REAL NOT NULL DEFAULT 0.0,
    costo_gs        REAL NOT NULL DEFAULT 0.0,
    iva_gs          REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS flete_items (
    id              SERIAL PRIMARY KEY,
    calculation_id  INTEGER NOT NULL REFERENCES calculations(id) ON DELETE CASCADE,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    descripcion     TEXT NOT NULL DEFAULT '',
    betrag          REAL NOT NULL DEFAULT 0.0,
    aufteilung      TEXT NOT NULL DEFAULT 'masseinheit',
    impuesto        TEXT NOT NULL DEFAULT 'Exento',
    cantidad        REAL NOT NULL DEFAULT 1.0,
    peso_volumen    REAL NOT NULL DEFAULT 0.0,
    betrag_sin_iva  REAL NOT NULL DEFAULT 0.0,
    costo_gs        REAL NOT NULL DEFAULT 0.0,
    iva_gs          REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS importacion_items (
    id              SERIAL PRIMARY KEY,
    calculation_id  INTEGER NOT NULL REFERENCES calculations(id) ON DELETE CASCADE,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    descripcion     TEXT NOT NULL DEFAULT '',
    betrag          REAL NOT NULL DEFAULT 0.0,
    aufteilung      TEXT NOT NULL DEFAULT 'wert',
    impuesto        TEXT NOT NULL DEFAULT 'Exento',
    cantidad        REAL NOT NULL DEFAULT 1.0,
    peso_volumen    REAL NOT NULL DEFAULT 0.0,
    betrag_sin_iva  REAL NOT NULL DEFAULT 0.0,
    costo_gs        REAL NOT NULL DEFAULT 0.0,
    iva_gs          REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS costo_nacional_items (
    id              SERIAL PRIMARY KEY,
    calculation_id  INTEGER NOT NULL REFERENCES calculations(id) ON DELETE CASCADE,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    descripcion     TEXT NOT NULL DEFAULT '',
    betrag          REAL NOT NULL DEFAULT 0.0,
    aufteilung      TEXT NOT NULL DEFAULT 'masseinheit',
    impuesto        TEXT NOT NULL DEFAULT '10%',
    cantidad        REAL NOT NULL DEFAULT 1.0,
    peso_volumen    REAL NOT NULL DEFAULT 0.0,
    betrag_sin_iva  REAL NOT NULL DEFAULT 0.0,
    costo_gs        REAL NOT NULL DEFAULT 0.0,
    iva_gs          REAL NOT NULL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_calc_updated ON calculations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_proveedor_calc ON proveedor_items(calculation_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_flete_calc ON flete_items(calculation_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_importacion_calc ON importacion_items(calculation_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_nacional_calc ON costo_nacional_items(calculation_id, sort_order);
