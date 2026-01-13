# Copilot Instructions for Brand Monitoring Project

## Overview
This project is a modular Python system for monitoring brand impersonation and scams across web and social media. It fetches, enriches, scores, and stores findings, with alerting for high-risk cases.

## Architecture & Data Flow
- **main.py** orchestrates the workflow:
  - Seeds URLs and keywords are scanned for brand impersonation.
  - Fetches web content (`fetcher.py`), enriches with WHOIS/SSL (`enrich.py`), scores risk (`scorer.py`), and stores results (`storage.py`).
  - Social media is scanned using `snscrape` via `social.py`.
  - Alerts are sent for high-risk findings (Slack/Teams integration).
- Each module is single-responsibility and stateless except for storage.

## Key Patterns & Conventions
- **Semantic similarity**: Uses `sentence-transformers` for text scoring. See `scorer.py:semantic_similarity`.
- **Visual similarity**: Optional SSIM scoring with OpenCV (`scorer.py:visual_ssim`).
- **Screenshots**: Taken with Selenium Chrome in headless mode (`fetcher.py:take_screenshot`).
- **Enrichment**: WHOIS, SSL, and DNS info via `enrich.py`.
- **Storage**: Results are appended to both Excel and CSV. Excel path is hardcoded in `storage.py`.
- **Alerting**: Slack (main.py) and Teams (alerting.py) supported. Webhook URLs are hardcoded.
- **Social scraping**: Prefers Python API for `snscrape`, falls back to subprocess if needed.
- **Error handling**: Most modules return error dicts instead of raising.

## Developer Workflows
- **Run main workflow**: `python main.py`
- **Dependencies**: Requires `sentence-transformers`, `opencv-python`, `selenium`, `snscrape`, `whois`, `tldextract`, `dnspython`, `pandas`, `openpyxl`.
- **Screenshots**: ChromeDriver must be installed and on PATH.
- **Testing**: No formal test suite; use `Test` for ad hoc checks.
- **Adding new signals**: Add to `scorer.py` and update risk aggregation in `main.py`.

## Integration Points
- **External APIs**: Slack/Teams webhooks, Twitter scraping via `snscrape`.
- **File outputs**: Excel and CSV in project or user directory.
- **No database**: All state is file-based.

## Examples
- To add a new enrichment (e.g., GeoIP), add a function to `enrich.py` and call it from `main.py`.
- To change alerting, update webhook URLs in `alerting.py` or `main.py`.

## File Guide
- `main.py`: Pipeline entrypoint and orchestration
- `fetcher.py`: Web fetching, link extraction, screenshots
- `enrich.py`: WHOIS, SSL, DNS enrichment
- `scorer.py`: Semantic/visual similarity
- `social.py`: Social scraping
- `storage.py`: File-based storage
- `alerting.py`: Teams alerting (Slack in main.py)

---
For questions or unclear patterns, review the relevant module or ask for clarification.
