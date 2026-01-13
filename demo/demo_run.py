import os
import pathlib
import sys

# Ensure project root is importable
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load demo seeds
demo_dir = pathlib.Path(__file__).parent
seeds_file = demo_dir / "demo_seeds.txt"
seeds = []
if seeds_file.exists():
    with seeds_file.open("r", encoding="utf-8") as fh:
        seeds = [line.strip() for line in fh if line.strip()]

# Provide safe demo env values
os.environ.setdefault("BRAND_NAME", "BRAND_PLACEHOLDER")
# unset any sensitive envs to avoid accidental real calls in demo
os.environ.pop("WHOIS_API_KEY", None)
os.environ.pop("TWITTER_BEARER_TOKEN", None)

def run_demo():
    try:
        import main
    except Exception as e:
        print("Failed to import main.py:", e)
        raise

    # Inject demo seeds into the pipeline
    if seeds:
        main.SEEDS = seeds
        print(f"Injected {len(seeds)} demo seed(s) into pipeline.")
    else:
        print("No demo seeds found; using existing SEEDS from config.yaml")

    # Clear previous state for a clean demo run
    try:
        main.clear_scan_state()
    except Exception as e:
        print("clear_scan_state() failed (continuing):", e)

    # Run main pipeline
    try:
        main.main()
    except Exception as e:
        print("Demo run failed:", e)
        raise

if __name__ == "__main__":
    run_demo()