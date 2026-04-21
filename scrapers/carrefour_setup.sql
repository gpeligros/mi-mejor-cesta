-- carrefour_setup.sql — Tabla precios_carrefour
-- Ejecutar UNA vez en Supabase antes de lanzar scraper_carrefour.py

CREATE TABLE IF NOT EXISTS precios_carrefour (
    id               TEXT PRIMARY KEY,          -- CF-{sku}
    id_api           TEXT NOT NULL UNIQUE,       -- sku interno Carrefour
    nombre_comercial TEXT,
    precio           NUMERIC(10, 2),
    marca            TEXT,
    url              TEXT,
    imagen           TEXT,
    ean              TEXT,
    disponible       BOOLEAN DEFAULT TRUE,
    formato          TEXT,
    actualizado      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_precios_carrefour_actualizado
    ON precios_carrefour (actualizado DESC);
