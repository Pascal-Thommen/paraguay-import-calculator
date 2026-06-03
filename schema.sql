-- schema.sql — PostgreSQL Schema v5 for Paraguay Import Calculator
-- Kein seguro_percent, kein seguro_currency, kein seguro_gs, kein cif_usd.

create table if not exists calculations (
    id          serial primary key,
    session_name text not null default '',
    language     text not null default 'de',
    status       text not null default 'draft',
    user_id      text not null default 'anonymous',
    created_at   timestamp with time zone default now(),
    updated_at   timestamp with time zone default now()
);

-- Calculation inputs (v5 — no seguro fields, no cif_usd)
create table if not exists calc_inputs (
    calculation_id         int primary key references calculations(id) on delete cascade,
    currency_fob           text default 'USD',
    exchange_rate_fob      numeric(15,4) default 7500.0,
    purchase_unit          text default 'kg',
    currency_flete         text default 'USD',
    exchange_rate_flete    numeric(15,4) default 7500.0,
    fob_currency           numeric(15,2) default 0.0,
    fob_gs                 numeric(15,2) default 0.0,
    cif_currency           numeric(15,2) default 0.0,
    cif_gs                 numeric(15,2) default 0.0,
    total_importacion      numeric(15,2) default 0.0,
    total_nacional         numeric(15,2) default 0.0,
    gran_total             numeric(15,2) default 0.0,
    gran_total_per_unit    numeric(15,4) default 0.0
);

-- Proveedor line items
create table if not exists proveedor_items (
    id                   serial primary key,
    calculation_id       int references calculations(id) on delete cascade,
    sort_order           int not null default 0,
    descripcion          text default '',
    betrag               numeric(15,2) default 0.0,
    aufteilung           text default 'wert',
    impuesto             text default 'Exento',
    cantidad             numeric(15,2) default 1.0,
    peso_volumen         numeric(15,2) default 0.0,
    betrag_sin_iva       numeric(15,2) default 0.0,
    costo_gs             numeric(15,2) default 0.0,
    iva_gs               numeric(15,2) default 0.0
);

-- Flete line items
create table if not exists flete_items (
    id                   serial primary key,
    calculation_id       int references calculations(id) on delete cascade,
    sort_order           int not null default 0,
    descripcion          text default '',
    betrag               numeric(15,2) default 0.0,
    aufteilung           text default 'masseinheit',
    impuesto             text default 'Exento',
    cantidad             numeric(15,2) default 1.0,
    peso_volumen         numeric(15,2) default 0.0,
    betrag_sin_iva       numeric(15,2) default 0.0,
    costo_gs             numeric(15,2) default 0.0,
    iva_gs               numeric(15,2) default 0.0
);

-- Importación line items
create table if not exists importacion_items (
    id                   serial primary key,
    calculation_id       int references calculations(id) on delete cascade,
    sort_order           int not null default 0,
    descripcion          text default '',
    betrag               numeric(15,2) default 0.0,
    aufteilung           text default 'wert',
    impuesto             text default 'Exento',
    cantidad             numeric(15,2) default 1.0,
    peso_volumen         numeric(15,2) default 0.0,
    betrag_sin_iva       numeric(15,2) default 0.0,
    costo_gs             numeric(15,2) default 0.0,
    iva_gs               numeric(15,2) default 0.0
);

-- Costo Nacional line items
create table if not exists costo_nacional_items (
    id                   serial primary key,
    calculation_id       int references calculations(id) on delete cascade,
    sort_order           int not null default 0,
    descripcion          text default '',
    betrag               numeric(15,2) default 0.0,
    aufteilung           text default 'masseinheit',
    impuesto             text default '10%',
    cantidad             numeric(15,2) default 1.0,
    peso_volumen         numeric(15,2) default 0.0,
    betrag_sin_iva       numeric(15,2) default 0.0,
    costo_gs             numeric(15,2) default 0.0,
    iva_gs               numeric(15,2) default 0.0
);

-- Index for fast querying
CREATE INDEX IF NOT EXISTS idx_calc_user ON calculations(user_id);
CREATE INDEX IF NOT EXISTS idx_calc_status ON calculations(status);
