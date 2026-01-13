# storage.py
import os
import json
import logging
from datetime import datetime

try:
    import pandas as pd
except Exception:
    pd = None
    logging.warning("pandas not available - append_findings will fallback to CSV simple write. Install pandas & openpyxl for Excel output.")

def append_findings(findings, csv_path=None, excel_path=None):
    """
    Persist findings to CSV and Excel (if pandas available).
    Returns list of written absolute file paths.
    """
    if not findings:
        logging.info("append_findings: no findings to write.")
        return []

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    if csv_path is None:
        csv_path = f"findings_{ts}.csv"
    if excel_path is None:
        excel_path = f"findings_{ts}.xlsx"

    written = []
    try:
        serializable = []
        for f in findings:
            row = {}
            for k, v in f.items():
                if isinstance(v, (str, int, float, bool)) or v is None:
                    row[k] = v
                else:
                    try:
                        row[k] = json.dumps(v, default=str, ensure_ascii=False)
                    except Exception:
                        row[k] = str(v)
            serializable.append(row)

        if pd is None:
            import csv as _csv
            keys = sorted({k for r in serializable for k in r.keys()})
            with open(csv_path, "w", encoding="utf-8", newline="") as fh:
                writer = _csv.DictWriter(fh, fieldnames=keys)
                writer.writeheader()
                writer.writerows(serializable)
        else:
            df = pd.DataFrame(serializable)
            df.to_csv(csv_path, index=False, encoding="utf-8")

        written.append(os.path.abspath(csv_path))
        logging.info(f"append_findings: wrote CSV -> {os.path.abspath(csv_path)}")

        if pd is not None:
            try:
                df.to_excel(excel_path, index=False, engine="openpyxl")
                written.append(os.path.abspath(excel_path))
                logging.info(f"append_findings: wrote Excel -> {os.path.abspath(excel_path)}")
            except Exception as e:
                logging.warning(f"append_findings: failed to write Excel ({excel_path}): {e}", exc_info=True)

    except Exception as e:
        logging.error(f"append_findings: failed to persist findings: {e}", exc_info=True)

    return written
