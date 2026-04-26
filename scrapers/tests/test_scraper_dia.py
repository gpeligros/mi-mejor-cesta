"""Tests unitarios para scraper_dia.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from scraper_dia import parse_api_product, extract_total_dia


# ─── parse_api_product ────────────────────────────────────────────────────────

def test_parse_api_product_completo():
    item = {
        "sku_id": "12345",
        "display_name": "Leche entera Celta 1 L",
        "prices": {
            "price": 1.29,
            "price_per_unit": 1.29,
            "measure_unit": "LITRO",
        },
        "brand": "Celta",
        "ean": "8410188012345",
        "image": "/images/leche.jpg",
        "url": "/p/leche-celta-1l/12345",
    }
    result = parse_api_product(item)
    assert result is not None
    assert result["id_api"] == "12345"
    assert result["nombre_comercial"] == "Leche entera Celta 1 L"
    assert result["precio"] == 1.29
    assert result["precio_unidad"] == "1.29€/L"
    assert result["marca"] == "Celta"
    assert result["ean"] == "8410188012345"
    assert result["imagen"] == "https://www.dia.es/images/leche.jpg"
    assert result["url"] == "https://www.dia.es/p/leche-celta-1l/12345"
    assert result["disponible"] is True
    assert result["formato"] == "1 L"


def test_parse_api_product_sin_precio_unidad():
    item = {
        "sku_id": "99999",
        "display_name": "Galletas María",
        "prices": {"price": 0.85},
        "brand": "Fontaneda",
    }
    result = parse_api_product(item)
    assert result is not None
    assert result["precio"] == 0.85
    assert result["precio_unidad"] == ""
    assert result["ean"] == ""


def test_parse_api_product_sin_sku_devuelve_none():
    item = {"display_name": "Sin SKU", "prices": {"price": 1.0}}
    assert parse_api_product(item) is None


def test_parse_api_product_kilogramo():
    item = {
        "sku_id": "11111",
        "display_name": "Arroz redondo 1 kg",
        "prices": {
            "price": 0.99,
            "price_per_unit": 0.99,
            "measure_unit": "KILOGRAMO",
        },
        "brand": "DIA",
    }
    result = parse_api_product(item)
    assert result["precio_unidad"] == "0.99€/kg"
    assert result["formato"] == "1 kg"


# ─── extract_total_dia ────────────────────────────────────────────────────────

def test_extract_total_dia_pagination():
    data = {"pagination": {"total_pages": 5, "page": 1}}
    assert extract_total_dia(data) == 5


def test_extract_total_dia_sin_pagination():
    data = {}
    assert extract_total_dia(data) == 1
