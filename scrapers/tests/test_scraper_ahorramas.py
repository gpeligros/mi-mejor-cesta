"""Tests unitarios para scraper_ahorramas.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from bs4 import BeautifulSoup
from scraper_ahorramas import parsear_producto, parsear_precio, extract_total_ahorramas


# ─── parsear_precio ───────────────────────────────────────────────────────────

def test_parsear_precio_coma():
    assert parsear_precio("2,99 €") == 2.99

def test_parsear_precio_punto():
    assert parsear_precio("2.99€") == 2.99

def test_parsear_precio_entero():
    assert parsear_precio("3 €") == 3.0

def test_parsear_precio_none():
    assert parsear_precio(None) is None

def test_parsear_precio_vacio():
    assert parsear_precio("") is None


# ─── parsear_producto ─────────────────────────────────────────────────────────

def test_parsear_producto_completo():
    html = """
    <div class="product-tile" data-pid="98765">
        <div class="pdp-link"><a href="/leche-entera-98765.html">Leche entera 1L</a></div>
        <div class="price">
            <span class="sales"><span class="value" content="1.29">1,29 €</span></span>
        </div>
        <div class="price-per-unit">1,29 €/L</div>
        <img src="https://www.ahorramas.com/leche.jpg" />
    </div>"""
    soup = BeautifulSoup(html, "html.parser")
    tile = soup.select_one("[data-pid]")
    result = parsear_producto(tile)
    assert result is not None
    assert result["id_api"] == "98765"
    assert result["nombre_comercial"] == "Leche entera 1L"
    assert result["precio"] == 1.29
    assert result["precio_unidad"] == "1,29 €/L"
    assert result["imagen"] == "https://www.ahorramas.com/leche.jpg"


def test_parsear_producto_sin_nombre_devuelve_none():
    html = '<div class="product-tile" data-pid="11111"><div class="price">1,99 €</div></div>'
    soup = BeautifulSoup(html, "html.parser")
    tile = soup.select_one("[data-pid]")
    assert parsear_producto(tile) is None


def test_parsear_producto_pid_desde_url():
    html = """
    <div class="product-tile">
        <div class="pdp-link"><a href="/galletas-maria-22222.html">Galletas María</a></div>
        <div class="price"><span class="sales"><span class="value">0,85 €</span></span></div>
    </div>"""
    soup = BeautifulSoup(html, "html.parser")
    tile = soup.select_one(".product-tile")
    result = parsear_producto(tile)
    assert result is not None
    assert result["id_api"] == "22222"


# ─── extract_total_ahorramas ──────────────────────────────────────────────────

def test_extract_total_json():
    html = '... "total": 245 ...'
    assert extract_total_ahorramas(html) == 245

def test_extract_total_count():
    html = '... "count":112 ...'
    assert extract_total_ahorramas(html) == 112

def test_extract_total_sin_datos():
    assert extract_total_ahorramas("sin datos") == 0
