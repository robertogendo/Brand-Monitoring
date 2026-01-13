# enrich.py
import whois
import ssl, socket
import tldextract
import dns.resolver
import os
import requests
import logging


def whois_info(domain):
    WHOIS_API_KEY = os.getenv("WHOIS_API_KEY")
    if not WHOIS_API_KEY:
        logging.warning("WHOIS API key not set")
        return {"error": "WHOIS API key not set"}
    url = f"https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey={WHOIS_API_KEY}&domainName={domain}&outputFormat=JSON"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.warning(f"WHOIS API unreachable: {e}")
        return {"error": f"WHOIS API unreachable: {e}"}

def ssl_info(domain, port=443):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, port))
            cert = s.getpeercert()
            return {"subject": cert.get("subject"), "issuer": cert.get("issuer"), "notAfter": cert.get("notAfter")}
    except Exception as e:
        return {"error": str(e)}

def dns_a(domain):
    try:
        answers = dns.resolver.resolve(domain, 'A')
        return [str(r) for r in answers]
    except Exception as e:
        return []
