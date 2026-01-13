Demo runner (safe, synthetic data)

How to run (Windows PowerShell):

1. Create and activate a virtual environment (recommended)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Install minimal dev deps (for demo):
   pip install -r requirements.txt
   # or at least:
   pip install python-dotenv requests

3. Run the demo:
   python demo\demo_run.py

What this does:
- Loads sanitized demo seeds from demo/demo_seeds.txt.
- Ensures no WHOIS or Twitter API keys are present in the environment for the demo run.
- Clears any previous scan_state.json to produce a fresh run.
- Runs main.main() with demo seeds injected.

Notes:
- Demo uses synthetic URLs and will not call paid services (WHOIS/Twitter) because demo env vars are cleared.
- To stop the demo early, Ctrl+C in the terminal.
- Do not commit any real API keys; use .env for local development only and keep .env in .gitignore.