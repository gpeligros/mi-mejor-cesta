# test_setup.py
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()

def test_playwright():
    print("Testing Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False para ver
        page = browser.new_page()
        page.goto("https://www.google.com")
        print(f"Title: {page.title()}")
        browser.close()
    print("✅ Playwright funciona!")

def test_env():
    print("Testing .env...")
    supabase_url = os.getenv('SUPABASE_URL')
    if supabase_url:
        print(f"✅ SUPABASE_URL: {supabase_url[:30]}...")
    else:
        print("❌ SUPABASE_URL no encontrada")

if __name__ == "__main__":
    test_playwright()
    test_env()