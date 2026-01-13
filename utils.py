import typing
from rapidfuzz import fuzz

def is_typosquat(domain: str, official_domains: typing.Iterable[str], threshold: int = 85) -> bool:
    """
    Return True if domain is likely a typosquat of any official domain.
    Uses rapidfuzz.fuzz.ratio (0..100).
    """
    for official in official_domains:
        try:
            if fuzz.ratio(domain, official) > threshold:
                return True
        except Exception:
            # conservative: ignore errors and continue
            continue
    return False