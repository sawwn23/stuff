#!/usr/bin/env python3
import time
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests
from requests.auth import HTTPBasicAuth

# ─── CONFIG ────────────────────────────────────────────────────────────────────

# InsightVM console URL (no trailing slash), e.g. "https://insightvm.example.com:3780"
CONSOLE = "https://<your-console>:3780"
API_BASE = f"{CONSOLE}/api/3"

# Credentials: either Basic Auth or API token
USERNAME = "your_username"
PASSWORD = "your_password"
AUTH = HTTPBasicAuth(USERNAME, PASSWORD)

# Only pull severity >= 7 (Critical & High)
MIN_SEVERITY = 7

# Rate‐limit: seconds to sleep between requests to avoid throttling
RATE_LIMIT_S = 0.2

# CSV output path
CSV_PATH = "insightvm_vulns_full.csv"

# ─── LOGGER ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ─── API HELPERS ───────────────────────────────────────────────────────────────

def get_paginated(endpoint: str, params: Dict[str, Any]=None) -> List[Dict[str, Any]]:
    """Fetch all pages from a paginated InsightVM endpoint."""
    url = f"{API_BASE}{endpoint}"
    items = []
    while url:
        log.debug(f"GET {url} params={params}")
        r = requests.get(url, auth=AUTH, headers={"Accept": "application/json"}, params=params)
        r.raise_for_status()
        data = r.json()
        # `resources` holds the array
        items.extend(data.get("resources", []))
        # `next.href` for the next page, if any
        url = data.get("next", {}).get("href")
        # Once we follow a next.href, reset params
        params = None
        time.sleep(RATE_LIMIT_S)
    return items

def get_all_vulns() -> List[Dict[str, Any]]:
    """Retrieve all vulnerabilities, filtered to severity >= MIN_SEVERITY."""
    raw = get_paginated("/vulnerabilities", params={"size": 500})
    filtered = [v for v in raw if v.get("severity", 0) >= MIN_SEVERITY]
    log.info(f"Fetched {len(raw)} total vulns, {len(filtered)} with severity ≥ {MIN_SEVERITY}")
    return filtered

def get_vuln_assets(vuln_id: int) -> List[Dict[str, Any]]:
    return get_paginated(f"/vulnerabilities/{vuln_id}/assets")

def get_vuln_exploit(vuln_id: int) -> Dict[str, Any]:
    url = f"{API_BASE}/vulnerabilities/{vuln_id}/exploit"
    r = requests.get(url, auth=AUTH, headers={"Accept": "application/json"})
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    time.sleep(RATE_LIMIT_S)
    return r.json()

def get_vuln_solutions(vuln_id: int) -> List[Dict[str, Any]]:
    return get_paginated(f"/vulnerabilities/{vuln_id}/solutions")

# ─── DATA TRANSFORM ─────────────────────────────────────────────────────────────

def calculate_fix_time(first_seen: str, last_seen: str) -> Optional[float]:
    """Return hours between first_seen and last_seen ISO8601 strings."""
    try:
        dt1 = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
        dt2 = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
        return round((dt2 - dt1).total_seconds() / 3600, 2)
    except Exception:
        return None

def flatten_records(vulns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """For each vuln, fetch assets/exploit/solutions and flatten into rows."""
    rows = []
    for v in vulns:
        vid     = v["id"]
        cve     = v.get("cve") or ""
        sev     = v.get("severity")
        first   = v.get("firstDiscovered")
        last    = v.get("lastSeen")
        status  = v.get("status")
        fix_hours = calculate_fix_time(first, last) if status == "fixed" else None

        # Fetch related data
        assets    = get_vuln_assets(vid)
        exploit   = get_vuln_exploit(vid)
        solutions = get_vuln_solutions(vid)

        for asset in assets:
            row = {
                "vuln_id": vid,
                "cve": cve,
                "severity": sev,
                "asset_id": asset.get("id"),
                "hostname": asset.get("hostname"),
                "ip": asset.get("ip"),
                "os": asset.get("os"),
                "tags": ";".join(asset.get("tags", [])),
                "first_seen": first,
                "last_seen": last,
                "status": status,
                "fix_time_hours": fix_hours,
                "exploit_module": exploit.get("moduleName"),
                "exploit_reliability": exploit.get("reliability"),
                "solution_count": len(solutions),
                "solutions": " | ".join([sol.get("description","") for sol in solutions])
            }
            rows.append(row)
        log.debug(f"Vuln {vid} → {len(assets)} assets, exploit={bool(exploit)}, sols={len(solutions)}")
    return rows

# ─── CSV EXPORT ────────────────────────────────────────────────────────────────

def write_csv(rows: List[Dict[str, Any]], path: str):
    if not rows:
        log.warning("No rows to write.")
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    log.info(f"Wrote {len(rows)} rows to {path}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    log.info("Starting InsightVM export…")
    vulns = get_all_vulns()
    rows  = flatten_records(vulns)
    write_csv(rows, CSV_PATH)
    log.info("Done.")

if __name__ == "__main__":
    main()
