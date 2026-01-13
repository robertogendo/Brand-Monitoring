import subprocess
import json
import logging
import os
import requests
import whois
import datetime
from typing import Iterable, List, Set

def generate_permutations(domain: str) -> set:
    """
    Generate lookalike domains using dnstwist CLI.
    Returns a set of domain names.
    """
    try:
        result = subprocess.run(
            ["dnstwist", "--format", "json", domain],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        return {entry["domain-name"] for entry in data if entry.get("domain-name")}
    except Exception as e:
        logging.warning(f"dnstwist failed for {domain}: {e}")
        return set()

def _simple_variants(domain: str) -> Set[str]:
    """Generate a small set of simple typosquat / suspicious variants for a domain."""
    root = domain.split(".")[0]
    variants = set()
    # common noisy prefixes/suffixes
    for prefix in ("www.", "secure.", "login.", "accounts."):
        variants.add(prefix + domain)
    for suf in ("-secure", "-login", "secure-", "auth"):
        variants.add(f"{root}{suf}.com")
    # homoglyph simple substitution
    variants.add(domain.replace("o", "0"))
    variants.add(domain.replace("l", "1"))
    # missing letter / swapped adjacent
    if len(root) > 2:
        variants.add(root[1:] + "." + domain.split(".",1)[1])
        variants.add(root[:-1] + "." + domain.split(".",1)[1])
        # swap first two chars
        variants.add(root[1] + root[0] + ("." + domain.split(".",1)[1] if "." in domain else ""))
    # ensure base without www
    variants.add(domain)
    return {v for v in variants if v}

def get_suspicious_domains(official_domains: Iterable[str], suspicious_tlds: Iterable[str], whois_api_key: str = None) -> List[str]:
    """
    Discover potentially suspicious domains.
    - Signature accepts optional whois_api_key for backward-compatibility but it is ignored.
    - Uses python-whois to flag newly-registered or missing WHOIS as suspicious.
    - Returns a list of candidate domain names (no scheme).
    """
    candidates = set()
    suspicious_tlds = set(suspicious_tlds or [])
    official_set = set(official_domains or [])

    # generate simple variants for each official domain
    for d in official_set:
        candidates.update(_simple_variants(d))

        # generate domains by combining root label with suspicious TLDs
        parts = d.split(".")
        root = parts[0]
        for t in suspicious_tlds:
            if t.startswith("."):
                candidates.add(f"{root}{t}")
            else:
                candidates.add(f"{root}.{t}")

    results = []
    for dom in sorted(candidates):
        # normalize remove leading www. for whois checks
        check_dom = dom.lstrip("www.")
        if check_dom in official_set:
            continue

        try:
            w = whois.whois(check_dom)
        except Exception as e:
            logging.debug(f"WHOIS lookup failed for {check_dom}: {e}", exc_info=False)
            # if whois failed, consider it suspicious (could be unregistered or private)
            results.append(check_dom)
            continue

        # examine creation date(s)
        created = w.creation_date
        creation_date = None
        if isinstance(created, list):
            creation_date = created[0]
        else:
            creation_date = created

        if creation_date is None:
            # missing creation -> suspicious
            results.append(check_dom)
            continue

        # if creation_date is a string parse attempt
        if isinstance(creation_date, str):
            try:
                creation_date = datetime.datetime.fromisoformat(creation_date)
            except Exception:
                try:
                    creation_date = datetime.datetime.strptime(creation_date, "%Y-%m-%d")
                except Exception:
                    creation_date = None

        if creation_date:
            age_days = (datetime.datetime.utcnow() - creation_date).days
            if age_days < 90:
                results.append(check_dom)
                continue

        # also flag if TLD is in suspicious list
        dom_tld = "." + check_dom.split(".")[-1]
        if dom_tld in suspicious_tlds:
            if check_dom not in results:
                results.append(check_dom)

    # dedupe and return
    return sorted(set(results))

def fetch_new_domains(api_key: str, keyword: str) -> set:
    """
    Fetch newly registered domains containing the keyword using WhoisXML API.
    Returns a set of domain names.
    """
    if not api_key:
        logging.warning("WHOIS API key not set for fetch_new_domains")
        return set()
    url = f"https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey={api_key}&domainName={keyword}&outputFormat=JSON"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Example: adapt parsing as needed for your API plan/response
        if "WhoisRecord" in data and "domainName" in data["WhoisRecord"]:
            return {data["WhoisRecord"]["domainName"]}
        return set()
    except Exception as e:
        logging.warning(f"Failed to fetch new domains for {keyword}: {e}")
        return set()