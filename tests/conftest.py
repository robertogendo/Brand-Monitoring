import os
import sys
import types
import pathlib

# Ensure project root is importable
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Lightweight stubs for external services ---

# 1) scorer (semantic similarity) - fast deterministic stub
fake_scorer = types.SimpleNamespace()
def _fake_semantic_similarity(text, templates):
    text_l = (text or "").lower()
    score = 0.0
    for t in templates or []:
        kw = t.split()[0].lower()
        if kw in text_l:
            score += 1.0
    return min(score / max(1, len(templates or [])), 1.0)
fake_scorer.semantic_similarity = _fake_semantic_similarity
sys.modules.setdefault("scorer", fake_scorer)

# 2) fetcher (web fetching, screenshots, link extraction)
fake_fetcher = types.SimpleNamespace()
def _fake_safe_get(url, timeout=10):
    return {"status": 200, "text": f"Demo content for {url}", "final_url": url, "headers": {}}
def _fake_extract_links(html, base):
    return []
def _fake_take_screenshot(url, out_dir="screenshots", timeout=15):
    return ""
fake_fetcher.safe_get = _fake_safe_get
fake_fetcher.extract_links = _fake_extract_links
fake_fetcher.take_screenshot = _fake_take_screenshot
sys.modules.setdefault("fetcher", fake_fetcher)

# 3) enrich (whois / ssl)
fake_enrich = types.SimpleNamespace()
def _fake_whois_info(domain):
    return {"domain_name": domain, "registrar": "demo", "creation_date": None}
def _fake_ssl_info(domain, port=443, timeout=5.0):
    return {"cert": {"subject": ((("commonName", domain),),)}}
fake_enrich.whois_info = _fake_whois_info
fake_enrich.ssl_info = _fake_ssl_info
sys.modules.setdefault("enrich", fake_enrich)

# 4) social - simple tweet stub
fake_social = types.SimpleNamespace()
def _fake_run_twitter_search(keyword, limit=20):
    if "brand" in (keyword or "").lower() or "placeholder" in (keyword or "").lower():
        return [{"content": "BRAND_PLACEHOLDER is giving away free airtime"}]
    return []
fake_social.run_twitter_search = _fake_run_twitter_search
sys.modules.setdefault("social", fake_social)

# 5) discovery - return sample suspicious domain
fake_discovery = types.SimpleNamespace()
fake_discovery.get_suspicious_domains = lambda official, tlds, *args, **kwargs: ["safaric0m.co.ke"]
sys.modules.setdefault("discovery", fake_discovery)

# 6) storage - append_findings returns file paths
fake_storage = types.SimpleNamespace()
def _fake_append_findings(findings, csv_path=None, excel_path=None):
    return [os.path.abspath(csv_path or "findings_demo.csv")]
fake_storage.append_findings = _fake_append_findings
sys.modules.setdefault("storage", fake_storage)

# 7) alerting (teams/slack) - no-op
fake_alerting = types.SimpleNamespace()
fake_alerting.send_teams_alert = lambda msg: None
fake_alerting.send_slack_alert = lambda msg: None
sys.modules.setdefault("alerting", fake_alerting)

# 8) utils - is_typosquat
fake_utils = types.SimpleNamespace()
def _fake_is_typosquat(domain, official, threshold=85):
    from rapidfuzz import fuzz
    for official_d in official or []:
        if fuzz.ratio(domain, official_d) > threshold:
            return True
    return False
fake_utils.is_typosquat = _fake_is_typosquat
sys.modules.setdefault("utils", fake_utils)

# 9) pytest fixture for demo env
import pytest
@pytest.fixture(autouse=True)
def demo_env(monkeypatch):
    monkeypatch.setenv("BRAND_NAME", os.environ.get("BRAND_NAME", "BRAND_PLACEHOLDER"))
    monkeypatch.delenv("WHOIS_API_KEY", raising=False)
    monkeypatch.delenv("TWITTER_BEARER_TOKEN", raising=False)
    yield