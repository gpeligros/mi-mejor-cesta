-- historico_precios.sql — Tabla historico_precios (P1 #4, propuesto y aprobado 23/08/2026)
-- Ejecutar UNA vez en el SQL Editor de Supabase antes de activar el registro
-- de histórico en los scrapers (scrapers/historico_precios.py).
--
-- Guarda una fila cada vez que el precio de un producto cambia en algún
-- supermercado. La poblan los scrapers por diff (comparan el precio nuevo
-- contra el que ya había antes de subirlo) — NO hay trigger de BBDD, para
-- que toda la lógica de "cuándo insertar" viva en Python, sea fácil de
-- depurar y tenga --dry-run como el resto de scripts (ver CONTEXTO.md,
-- sección 12, "Reglas de oro").
--
-- Uso previsto: alertas de bajada de precio + gráfico "evolución de precio"
-- del plan Premium (hueco detectado en la auditoría del modal de suscripción).

CREATE TABLE IF NOT EXISTS historico_precios (
    id                BIGSERIAL PRIMARY KEY,
    super             TEXT NOT NULL,               -- 'mercadona' | 'dia' | 'alcampo' | 'ahorramas' | 'carrefour'
    id_producto_super TEXT NOT NULL,               -- id de precios_* (ej. 'ME-1234', 'DI-5678')
    precio            NUMERIC(10, 2) NOT NULL,
    fecha             DATE NOT NULL,               -- fecha en la que se detectó este precio
    creado_en         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Un producto no puede tener dos precios distintos registrados el mismo día
CREATE UNIQUE INDEX IF NOT EXISTS historico_precios_unico_dia
    ON historico_precios (super, id_producto_super, fecha);

-- Consulta habitual: "dame el histórico de este producto en este super, en orden"
CREATE INDEX IF NOT EXISTS historico_precios_por_producto
    ON historico_precios (super, id_producto_super, fecha DESC);
