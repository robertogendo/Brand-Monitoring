# fetcher.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pathlib, logging

def safe_get(url, timeout=10):
    """Fetch URL with safe error handling."""
    headers = {"User-Agent": "BrandMonitorBot/1.0 (+your-email@example.com)"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        return {"status": r.status_code, "text": r.text, "final_url": r.url, "headers": dict(r.headers)}
    except Exception as e:
        logging.warning(f"safe_get failed for {url}: {e}", exc_info=True)
        return {"error": str(e)}

def extract_links(html, base):
    """Extract all links from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        links.add(urljoin(base, a["href"]))
    return list(links)

def take_screenshot(url: str, out_dir: str = "screenshots", timeout: int = 15) -> str:
    """Take a screenshot of a URL using headless Chrome."""
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = url.replace("://", "_").replace("/", "_").replace("?", "_")
    filename = out_dir / f"{int(time.time())}_{safe_name}.png"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,768")

    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        time.sleep(1)
        driver.save_screenshot(str(filename))
        logging.info(f"Screenshot saved: {filename}")
        return str(filename)
    except Exception as e:
        logging.warning(f"Screenshot failed for {url}: {e}", exc_info=True)
        return ""
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
