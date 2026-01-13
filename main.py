# Fetch scam URLs from PhishTank
import requests
import csv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("scan.log"),
        logging.StreamHandler()
    ]
)
import yaml
from rapidfuzz import fuzz
import time
import os
import json
import logging
import threading
import queue as thread_queue
import argparse  # <- ADD THIS MISSING IMPORT
import time
from urllib.parse import urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed  # <- ADD THIS
from dotenv import load_dotenv
# Load environment variables from .env file (local dev only, do not commit .env)
load_dotenv()

# Configure logging (do this once, before other code)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("scan.log"),
        logging.StreamHandler()
    ]
)

# --- Local module imports ---
from fetcher import safe_get, extract_links, take_screenshot
from enrich import whois_info, ssl_info
from scorer import semantic_similarity
from storage import append_findings
from social import run_twitter_search
from discovery import get_suspicious_domains
from utils import is_typosquat
from alerting import send_teams_alert

# Load config with validation
try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    if config is None:
        logging.error("config.yaml is empty or invalid YAML")
        config = {}
except Exception as e:
    logging.error(f"Failed to load config.yaml: {e}", exc_info=True)
    config = {}

# Extract config values with defaults
BRAND_TEMPLATES = config.get("brand_templates", ["BRAND_PLACEHOLDER"])
SEEDS = config.get("seeds", [])
if SEEDS is None:
    SEEDS = []
OFFICIAL_DOMAINS = set(config.get("official_domains", []))
SUSPICIOUS_TLDS = set(config.get("suspicious_tlds", []))
GOOGLE_API_KEY = config.get("google_safe_browsing_api_key", "")

STATE_FILE = "scan_state.json"
MAX_WORKERS = 5

def fetch_phishtank_urls():
    url = "https://data.phishtank.com/data/online-valid.csv"
    response = safe_request(url)
    if response is None:
        logging.error(f"Failed to fetch PhishTank URLs after retries.")
        return []
    scam_urls = set()
    lines = response.text.splitlines()
    reader = csv.DictReader(lines)
    for row in reader:
        scam_urls.add(row['url'])
    return list(scam_urls)
# Advanced suspicious link filtering

def is_suspicious(link):
    from urllib.parse import urlparse
    domain = urlparse(link).netloc
    tld = "." + domain.split(".")[-1]
    if domain in OFFICIAL_DOMAINS:
        return False
    if tld in SUSPICIOUS_TLDS:
        return True
    if "safaricom" in domain or "m-pesa" in domain:
        return True
    return False

# Replace local is_typosquat definition with import from utils
from utils import is_typosquat
# main.py
from fetcher import safe_get, take_screenshot, extract_links
from enrich import whois_info, ssl_info
from social import run_twitter_search
from scorer import semantic_similarity
from storage import append_findings
from alerting import send_teams_alert #unused check later
import requests
import csv
from discovery import get_suspicious_domains
import os
import logging
import sys


def scan_url(url: str, scanned: set, scanned_lock: threading.Lock, q: thread_queue.Queue) -> tuple:
    """Scans a single URL, returns (record, new_links)."""
    logging.info(f"Processing: {url}")
    with scanned_lock:
        if url in scanned:
            logging.info(f"Already scanned: {url}")
            return None, []
        scanned.add(url)
    res = safe_get(url)
    logging.info(f"Fetch result for {url}: {res}")
    if res.get("error"):
        logging.error(f"Fetch error for {url}: {res['error']}")
        return None, []
    title = ""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res["text"], "html.parser")
        title = soup.title.string if soup.title else ""
    except Exception:
        logging.warning(f"Title extraction failed for {url}")
        pass

    # semantic check
    sim = semantic_similarity((title + " " + res["text"])[:4000], BRAND_TEMPLATES)
    # whois, ssl
    domain = url.split("//")[-1].split("/")[0]
    who = whois_info(domain)
    sslc = ssl_info(domain)
    screenshot = take_screenshot(url)

    # visual comparison example (needs a baseline screenshot of brand)
    # visual_score = visual_ssim(screenshot, "baseline_brand.png")
    # combine to risk
    risk_score = (sim * 0.6)  # add other signals

    record = {"url": url, "domain": domain, "title": title, "similarity": sim, "whois": str(who), "ssl": str(sslc), "screenshot": screenshot, "risk": risk_score}
    logging.info(f"Appended finding for {url}: {record}")
    if risk_score > 0.7:
        send_teams_alert(f"High risk detected: {url} (score {risk_score})")

    # Discover new links from the page
    links = extract_links(res["text"], url)
    logging.info(f"Discovered {len(links)} links from {url}")
    new_links = []
    for link in links:
        from urllib.parse import urlparse
        domain = urlparse(link).netloc
        with scanned_lock:
            # Check for suspicious TLD, brand keywords, or typosquatting
            if (
                (is_suspicious(link) or is_typosquat(domain, OFFICIAL_DOMAINS))
                and link not in scanned
            ):
                logging.info(f"Queueing suspicious or typosquat link: {link}")
                q.put(link)
                new_links.append(link)
    return record, new_links

def scan_social(keywords):
    results = []
    for kw in keywords:
        try:
            tweets = run_twitter_search(kw, limit=20)
            logging.info(f"Twitter search returned {len(tweets)} tweets for '{kw}'")
            for t in tweets:
                txt = t.get("content") if isinstance(t, dict) else t.content
                sim = semantic_similarity(txt, BRAND_TEMPLATES)
                if sim > 0.75:
                    results.append({"type": "tweet", "keyword": kw, "text": txt, "score": sim})
                    logging.warning(f"Potential scam tweet found: {txt[:200]}... (score {sim})")
                    send_teams_alert(f"Potential scam tweet found: {txt[:200]}... (score {sim})")
        except Exception as e:
            logging.error(f"Social scraping for '{kw}' skipped due to error: {e}", exc_info=True)
    return results

def safe_request(url, retries=3, delay=2):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; BrandMonitorBot/1.0)'}
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            logging.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(delay)
    logging.error(f"All attempts failed for {url}")
    return None

def load_state():
    """Load intermediate scan state or return fresh state."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            findings = state.get("findings", [])
            scanned = set(state.get("scanned", []))
            queue = state.get("queue", [])
            if not queue:
                queue = list(SEEDS) if SEEDS else []
            logging.info(f"Resuming from saved state: {len(scanned)} scanned, {len(queue)} in queue.")
        except Exception as e:
            logging.error(f"Failed to load state: {e}", exc_info=True)
            findings = []
            scanned = set()
            queue = list(SEEDS) if SEEDS else []
    else:
        findings = []
        scanned = set()
        queue = list(SEEDS) if SEEDS else []
    return findings, scanned, queue

def main():
    """Main pipeline orchestration."""
    findings, scanned, queue_list = load_state()
    scanned_lock = threading.Lock()
    q = thread_queue.Queue()
    
    # Ensure queue_list is not None
    if queue_list is None:
        queue_list = []
    
    for url in queue_list:
        q.put(url)

    # Re-seed the queue if empty
    if q.qsize() == 0:
        logging.info("Queue is empty after loading state. Re-seeding with SEEDS.")
        for url in SEEDS:
            if url not in scanned:
                q.put(url)
        suspicious_domains = get_suspicious_domains(OFFICIAL_DOMAINS, SUSPICIOUS_TLDS)
        for d in suspicious_domains:
            url = f"http://{d}"
            if url not in scanned:
                if is_typosquat(d, OFFICIAL_DOMAINS):
                    logging.info(f"Suspicious typosquat domain detected during re-seed: {d}")
                q.put(url)
        logging.info(f"Queue re-seeded. {q.qsize()} URLs in queue.")

    # Add suspicious domains to the queue
    suspicious_domains = get_suspicious_domains(OFFICIAL_DOMAINS, SUSPICIOUS_TLDS)
    for d in suspicious_domains:
        url = f"http://{d}"
        if url not in scanned and url not in list(q.queue):
            if is_typosquat(d, OFFICIAL_DOMAINS):
                logging.info(f"Suspicious typosquat domain detected: {d}")
            q.put(url)

    # Dynamic link discovery and scam detection (concurrent)
    while not q.empty():
        batch = []
        for _ in range(min(MAX_WORKERS, q.qsize())):
            try:
                batch.append(q.get_nowait())
            except thread_queue.Empty:
                break
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {executor.submit(scan_url, url, scanned, scanned_lock, q): url for url in batch}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    record, _ = future.result()
                    if record:
                        findings.append(record)
                except Exception as exc:
                    logging.error(f"Error processing {url}: {exc}", exc_info=True)
        
        # Save intermediate state after each batch
        with open(STATE_FILE, "w") as f:
            json.dump({"findings": findings, "scanned": list(scanned), "queue": list(q.queue)}, f)
        logging.info(f"Saved intermediate state: {len(scanned)} scanned, {q.qsize()} in queue.")

    # Fetch scam URLs from PhishTank
    try:
        phishtank_urls = fetch_phishtank_urls()
        logging.info(f"Fetched {len(phishtank_urls)} scam URLs from PhishTank.")
        if phishtank_urls:
            SEEDS.extend(phishtank_urls)
    except Exception as e:
        logging.error(f"Failed to fetch PhishTank URLs: {e}", exc_info=True)

    # Social scanning
    social_findings = scan_social(["BRAND_PLACEHOLDER", "m-pesa"])
    if social_findings:
        findings.extend(social_findings)

    # Google Safe Browsing check
    if GOOGLE_API_KEY:
        for finding in findings:
            if finding.get("url") and finding.get("risk", 0) > 0.7:
                url = finding["url"]
                threats = check_google_safe_browsing(GOOGLE_API_KEY, url)
                if threats:
                    logging.warning(f"High-risk URL detected by Google Safe Browsing: {url}")
                    send_teams_alert(f"High-risk URL detected by Google Safe Browsing: {url}")

    # Save findings to Excel and CSV
    written_files = append_findings(findings)
    if written_files:
        logging.info(f"Saved findings files: {written_files}")
    else:
        logging.warning("No findings files were written.")

    # Save final state
    with open(STATE_FILE, "w") as f:
        json.dump({"findings": findings, "scanned": list(scanned), "queue": list(q.queue)}, f)
    logging.info(f"Final state saved: {len(scanned)} scanned, {len(q.queue)} in queue.")

def clear_scan_state():
    """Delete scan_state.json to force fresh run."""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        logging.info("Cleared scan state: scan_state.json deleted.")
    else:
        logging.info("No scan state file to clear.")

def load_api_keys():
    """Read Twitter key from environment."""
    twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN") or os.getenv("TWITTER_BEARER")
    if not twitter_bearer:
        logging.warning("TWITTER_BEARER_TOKEN not set. Social scraping may be limited.")
    else:
        logging.info("TWITTER_BEARER_TOKEN loaded.")
    return twitter_bearer

def _parse_args():
    p = argparse.ArgumentParser(description="Brand monitoring pipeline")
    p.add_argument("--reset", action="store_true", help="Clear scan state before starting")
    return p.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    if args.reset:
        clear_scan_state()
        logging.info("Scan state cleared (--reset). Starting fresh run.")
    else:
        logging.info("Starting without clearing state. Use --reset to clear scan_state.json before run.")
    
    TWITTER_BEARER_TOKEN = load_api_keys()
    main()

