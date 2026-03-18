"""
matching_dia_v2.py
Matching DIA → productos_catalogo en dos fases:
  Fase 1: Fuzzy automático (rapidfuzz) — rápido y gratis
  Fase 2: IA con Claude — solo para los dudosos

Uso: python matching_dia_v2.py
"""

import json
import csv
import time
import unicodedata
import urllib.request
import urllib.error
import os
from datetime import datetime

# Cargar .env desde raíz del proyecto (un nivel arriba de scrapers/)
try:
    from dotenv import load_dotenv
    _raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(_raiz, '.env'))
except ImportError:
    pass  # sin dotenv, usar variables de entorno del sistema

# ── CONFIGURACIÓN ─────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "PEGA_AQUI_TU_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "PEGA_AQUI_TU_KEY")

UMBRAL_AUTO    = 82   # ≥82% → match automático
UMBRAL_DUDOSO  = 70   # 70-81% → guardar para IA
# <72% → sin match

BATCH_SUPABASE = 50   # productos por petición PATCH
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M')
# ─────────────────────────────────────────────────────────────

HEADERS_SB = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal",
}

# ══════════════════════════════════════════════════════════════
# SUPABASE HELPERS
# ══════════════════════════════════════════════════════════════

def sb_get(tabla, filtro="", limit=10000):
    url = f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}&limit={limit}"
    req = urllib.request.Request(url, headers=HEADERS_SB)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def sb_patch(tabla, filtro, datos):
    url  = f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}"
    data = json.dumps(datos).encode()
    req  = urllib.request.Request(url, data=data, headers=HEADERS_SB, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


# ══════════════════════════════════════════════════════════════
# NORMALIZACIÓN
# ══════════════════════════════════════════════════════════════

STOP_MARCAS = {
    'hacendado', 'dia lactea', 'dia fruticampo', 'diacol', 'madriz',
    'nativa', 'carrefour', 'milbona', 'freeway', 'snack day',
    'lidl', 'aldi', 'mercadona'
}

STOP_FORMATO = {
    'pack', 'botella', 'brik', 'brick', 'lata', 'bote', 'bolsa', 'caja',
    'sobre', 'tarro', 'bandeja', 'unidad', 'unidades', 'piezas',
    'x 1 l', 'x 2 l', 'x 1l', '1 l', '2 l', '500 ml', '250 ml',
    '200 g', '500 g', '1 kg', '250 g', '100 g', '1kg', '750 ml',
}

def normalizar(nombre):
    """Normaliza nombre para comparar"""
    n = nombre.lower().strip()
    # quitar tildes
    n = ''.join(c for c in unicodedata.normalize('NFD', n)
                if unicodedata.category(c) != 'Mn')
    # quitar marcas blancas
    for m in STOP_MARCAS:
        n = n.replace(m, '')
    # quitar formatos y cantidades
    for f in STOP_FORMATO:
        n = n.replace(f, '')
    # quitar números con unidades: "6 x 1", "330ml", etc
    import re
    n = re.sub(r'\d+\s*x\s*\d+', '', n)
    n = re.sub(r'\d+\s*(ml|cl|l|g|kg|ud|uds)', '', n)
    n = re.sub(r'\s+', ' ', n)
    return n.strip()


# ══════════════════════════════════════════════════════════════
# FASE 1: FUZZY MATCHING
# ══════════════════════════════════════════════════════════════

def fase1_fuzzy(catalogo, precios_dia, matches_existentes):
    """Matching fuzzy entre precios_dia y productos_catalogo"""
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        print("❌ Falta rapidfuzz: pip install rapidfuzz")
        return [], [], []

    print(f"\n{'='*55}")
    print("  FASE 1: FUZZY MATCHING")
    print(f"{'='*55}")

    # IDs de DIA que ya tienen match
    dia_ya_matcheados = set(m['id_dia'] for m in matches_existentes if m.get('id_dia'))
    print(f"  DIA ya matcheados:  {len(dia_ya_matcheados)}")
    print(f"  DIA sin match:      {len([p for p in precios_dia if p['id'] not in dia_ya_matcheados])}")

    # Índice catálogo: nombre_norm → datos
    idx_catalogo = {}
    for p in catalogo:
        norm = normalizar(p['nombre_generico'])
        if norm:
            idx_catalogo[norm] = p
    nombres_catalogo = list(idx_catalogo.keys())

    auto    = []   # ≥ UMBRAL_AUTO
    dudosos = []   # UMBRAL_DUDOSO ≤ score < UMBRAL_AUTO
    sin_match = []

    pendientes = [p for p in precios_dia if p['id'] not in dia_ya_matcheados]
    total = len(pendientes)

    for i, prod_dia in enumerate(pendientes):
        nombre = prod_dia.get('nombre_comercial', '')
        if not nombre:
            continue

        norm_dia = normalizar(nombre)
        if not norm_dia:
            continue

        resultado = process.extractOne(
            norm_dia,
            nombres_catalogo,
            scorer=fuzz.token_sort_ratio
        )

        if resultado:
            mejor_nombre, score, _ = resultado
            prod_catalogo = idx_catalogo[mejor_nombre]
            entry = {
                'id_dia':           prod_dia['id'],
                'nombre_dia':       nombre,
                'id_catalogo':      prod_catalogo['id'],
                'nombre_catalogo':  prod_catalogo['nombre_generico'],
                'score':            round(score, 1),
            }
            if score >= UMBRAL_AUTO:
                auto.append(entry)
            elif score >= UMBRAL_DUDOSO:
                dudosos.append(entry)
            else:
                sin_match.append(prod_dia)
        else:
            sin_match.append(prod_dia)

        if (i + 1) % 500 == 0:
            print(f"  Procesados {i+1}/{total}...", end="\r")

    print(f"\n  ✅ Automáticos (≥{UMBRAL_AUTO}%):     {len(auto)}")
    print(f"  ⚠️  Dudosos ({UMBRAL_DUDOSO}-{UMBRAL_AUTO-1}%):        {len(dudosos)}")
    print(f"  ❌ Sin match (<{UMBRAL_DUDOSO}%):       {len(sin_match)}")

    return auto, dudosos, sin_match


# ══════════════════════════════════════════════════════════════
# FASE 2: IA CON CLAUDE para los dudosos
# ══════════════════════════════════════════════════════════════

def fase2_ia(dudosos, catalogo):
    """Usa Claude para confirmar o rechazar los matches dudosos"""
    print(f"\n{'='*55}")
    print("  FASE 2: IA CON CLAUDE (matches dudosos)")
    print(f"{'='*55}")

    if not dudosos:
        print("  No hay dudosos que procesar.")
        return [], []

    # Índice catálogo por id
    idx_by_id = {p['id']: p for p in catalogo}

    confirmados = []
    rechazados  = []

    # Procesar en grupos de 10 para reducir llamadas a la API
    GRUPO = 10
    total_grupos = (len(dudosos) + GRUPO - 1) // GRUPO

    for g in range(total_grupos):
        grupo = dudosos[g * GRUPO : (g + 1) * GRUPO]

        # Construir prompt con el grupo
        items_texto = "\n".join([
            f"{i+1}. DIA: \"{item['nombre_dia']}\" → CATÁLOGO: \"{item['nombre_catalogo']}\" (score fuzzy: {item['score']}%)"
            for i, item in enumerate(grupo)
        ])

        prompt = f"""Eres un experto en productos de supermercado español.
Analiza si cada par de productos es EL MISMO producto (puede ser distinta marca blanca o formato).

PARES A EVALUAR:
{items_texto}

REGLAS:
- SÍ si son el mismo producto genérico aunque tengan distinta marca blanca (Hacendado vs Dia Láctea)
- SÍ si son el mismo aunque tengan distinto formato/cantidad (1L vs 6x1L)
- NO si son productos distintos (leche entera vs leche desnatada)
- NO si la categoría es diferente (yogur vs bebida láctea)

Responde SOLO con un JSON array, sin markdown:
[{{"num": 1, "match": true}}, {{"num": 2, "match": false}}, ...]"""

        try:
            url = "https://api.anthropic.com/v1/messages"
            body = json.dumps({
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }).encode()

            req = urllib.request.Request(url, data=body, headers={
                "x-api-key":         ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            }, method="POST")

            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.loads(r.read())
                # Anthropic devuelve content[0].text
                texto = resp['content'][0]['text'].strip()
                # Limpiar markdown si lo hay
                if '```' in texto:
                    import re
                    texto = re.sub(r'```(?:json)?', '', texto).strip()
                resultados = json.loads(texto)

            for res in resultados:
                idx = res['num'] - 1
                if 0 <= idx < len(grupo):
                    item = grupo[idx]
                    if res.get('match'):
                        confirmados.append(item)
                    else:
                        rechazados.append(item)

            print(f"  Grupo {g+1}/{total_grupos}: {sum(1 for r in resultados if r.get('match'))} confirmados, {sum(1 for r in resultados if not r.get('match'))} rechazados")
            time.sleep(0.5)  # respetar rate limit

        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode()
            print(f"  ❌ Error grupo {g+1} HTTP {e.code}: {cuerpo[:300]}")
            rechazados.extend(grupo)
        except Exception as e:
            print(f"  ❌ Error grupo {g+1}: {e}")
            rechazados.extend(grupo)

    print(f"\n  ✅ Confirmados por IA:  {len(confirmados)}")
    print(f"  ❌ Rechazados por IA:   {len(rechazados)}")
    return confirmados, rechazados


# ══════════════════════════════════════════════════════════════
# APLICAR MATCHES A SUPABASE
# ══════════════════════════════════════════════════════════════

def aplicar_matches(matches, fuente="fuzzy"):
    """Actualiza productos_match.id_dia en Supabase"""
    print(f"\n  Aplicando {len(matches)} matches ({fuente}) a Supabase...")

    ok = 0
    for m in matches:
        # Buscar o crear fila en productos_match para este id_catalogo
        status, err = sb_patch(
            "productos_match",
            f"id_catalogo=eq.{m['id_catalogo']}",
            {"id_dia": str(m['id_dia'])}
        )
        if status in (200, 204):
            ok += 1
        else:
            print(f"  ⚠️  Error {status} para catalogo {m['id_catalogo']}: {err}")

        if ok % 100 == 0 and ok > 0:
            print(f"  {ok}/{len(matches)}...", end="\r")

    print(f"  ✅ {ok}/{len(matches)} matches aplicados")
    return ok


# ══════════════════════════════════════════════════════════════
# GUARDAR CSVs
# ══════════════════════════════════════════════════════════════

def guardar_csv(datos, nombre_archivo, campos):
    if not datos:
        return
    with open(nombre_archivo, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
        w.writeheader()
        w.writerows(datos)
    print(f"  📄 Guardado: {nombre_archivo} ({len(datos)} filas)")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 55)
    print("  🔗 MATCHING DIA v2 — Fuzzy + IA")
    print("=" * 55)

    if "PEGA_AQUI" in SUPABASE_KEY:
        print("❌ Configura SUPABASE_KEY en el .env o en el script")
        return

    # ── Cargar datos ──────────────────────────────────────────
    print("\n📥 Cargando datos de Supabase...")

    catalogo, _ = None, None
    try:
        catalogo = sb_get("productos_catalogo",
            "select=id,nombre_generico,marca,categoria", 10000)
        print(f"  productos_catalogo:  {len(catalogo)}")
    except Exception as e:
        print(f"❌ Error cargando catálogo: {e}"); return

    try:
        precios_dia = sb_get("precios_dia",
            "select=id,nombre_comercial,marca", 10000)
        print(f"  precios_dia:         {len(precios_dia)}")
    except Exception as e:
        print(f"❌ Error cargando precios_dia: {e}"); return

    try:
        matches_existentes = sb_get("productos_match",
            "id_dia=not.is.null&select=id_catalogo,id_dia", 10000)
        print(f"  matches ya hechos:   {len(matches_existentes)}")
    except Exception as e:
        matches_existentes = []
        print(f"  ⚠️  No se pudieron cargar matches existentes: {e}")

    # ── Fase 1: Fuzzy ─────────────────────────────────────────
    auto, dudosos, sin_match = fase1_fuzzy(catalogo, precios_dia, matches_existentes)

    # Aplicar automáticos
    if auto:
        if input(f"\n  ¿Aplicar {len(auto)} matches automáticos? (s/n): ").strip().lower() == 's':
            aplicar_matches(auto, "fuzzy")
    else:
        print("\n  No hay matches automáticos nuevos.")

    # ── Fase 2: IA para dudosos ───────────────────────────────
    if dudosos:
        usar_ia = input(f"\n  ¿Procesar {len(dudosos)} dudosos con IA? (s/n): ").strip().lower()
        if usar_ia == 's':
            if "PEGA_AQUI" in ANTHROPIC_KEY:
                print("  ❌ Configura ANTHROPIC_API_KEY en .env")
            else:
                confirmados_ia, rechazados_ia = fase2_ia(dudosos, catalogo)
                if confirmados_ia:
                    aplicar_matches(confirmados_ia, "IA")
                # Guardar rechazados por IA
                guardar_csv(
                    rechazados_ia,
                    f"dia_sin_match_ia_{TIMESTAMP}.csv",
                    ['id_dia', 'nombre_dia', 'id_catalogo', 'nombre_catalogo', 'score']
                )
        else:
            # Guardar dudosos para revisión manual
            guardar_csv(
                sorted(dudosos, key=lambda x: -x['score']),
                f"dia_dudosos_{TIMESTAMP}.csv",
                ['score', 'nombre_dia', 'nombre_catalogo', 'id_dia', 'id_catalogo']
            )

    # Guardar sin match
    guardar_csv(
        sin_match,
        f"dia_sin_match_{TIMESTAMP}.csv",
        ['id', 'nombre_comercial', 'marca']
    )

    # ── Resumen final ─────────────────────────────────────────
    print(f"\n{'='*55}")
    print("  RESUMEN FINAL")
    print(f"{'='*55}")
    print(f"  Automáticos aplicados: {len(auto)}")
    print(f"  Dudosos pendientes:    {len(dudosos)}")
    print(f"  Sin match:             {len(sin_match)}")

    try:
        total_con_dia = sb_get("productos_match",
            "id_dia=not.is.null&select=id", 10000)
        print(f"\n  Total matches DIA en BD: {len(total_con_dia)}")
    except:
        pass

    print("\n✅ Matching completado.")


if __name__ == "__main__":
    main()
