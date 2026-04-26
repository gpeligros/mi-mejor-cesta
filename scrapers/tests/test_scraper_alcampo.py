"""Tests unitarios para scraper_alcampo.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from scraper_alcampo import extract_products_from_html, parse_api_product


# ─── parse_api_product ────────────────────────────────────────────────────────

def test_parse_api_product_completo():
    item = {
        "id":    "123456",
        "name":  "Leche entera 1 L",
        "price": {"value": 1.29, "referencePrice": "1,29 €/L"},
        "brand": {"name": "Celta"},
        "ean":   "8410188012345",
        "image": "https://cdn.alcampo.es/leche.jpg",
        "availability": "inStock",
        "slug":  "leche-entera-1-l",
    }
    result = parse_api_product(item)
    assert result is not None
    assert result["id_api"] == "123456"
    assert result["id"] == "AL-123456"
    assert result["nombre_comercial"] == "Leche entera 1 L"
    assert result["precio"] == 1.29
    assert result["precio_unidad"] == "1,29 €/L"
    assert result["marca"] == "Celta"
    assert result["ean"] == "8410188012345"
    assert result["disponible"] is True


def test_parse_api_product_sin_id_devuelve_none():
    item = {"name": "Sin ID", "price": {"value": 1.0}}
    assert parse_api_product(item) is None


def test_parse_api_product_precio_como_float():
    item = {
        "id":    "99999",
        "name":  "Agua mineral 1.5 L",
        "price": 0.49,
    }
    result = parse_api_product(item)
    assert result is not None
    assert result["precio"] == 0.49


# ─── extract_products_from_html ───────────────────────────────────────────────

def test_extract_from_jsonld_itemlist():
    html = """<html><body>
    <script type="application/ld+json">
    {"@type": "ItemList", "itemListElement": [
        {"url": "https://www.compraonline.alcampo.es/products/leche-entera-1l/654321",
         "item": {
           "@type": "Product",
           "name": "Leche entera 1 L",
           "offers": {"price": "1.29", "availability": "https://schema.org/InStock"},
           "brand": {"name": "Celta"},
           "image": "https://cdn.alcampo.es/leche.jpg"
         }}
    ]}
    </script></body></html>"""
    prods = extract_products_from_html(html)
    assert len(prods) >= 1
    assert prods[0]["id_api"] == "654321"
    assert prods[0]["precio"] == 1.29
    assert prods[0]["id"] == "AL-654321"


def test_extract_from_html_vacio_devuelve_lista_vacia():
    assert extract_products_from_html("") == []
    assert extract_products_from_html(None) == []
