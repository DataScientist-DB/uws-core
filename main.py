import argparse, sys, yaml, time
from pathlib import Path
from core.helpers import ensure_outdirs, load_env
from core.writer import write_rows
from adapters import indeed, yelp_nextdata, google_maps

ADAPTERS = {
    "indeed": indeed.run,
    "yelp_nextdata": yelp_nextdata.run,
    "google_maps": google_maps.run,
}

def parse_args():
    p = argparse.ArgumentParser(description="Universal Web Scraper")
    p.add_argument("--adapter", required=True, choices=ADAPTERS.keys())
    p.add_argument("--config", required=True, help="Path to YAML config")
    p.add_argument("--outdir", default="out")
    p.add_argument("--headful", action="store_true")
    p.add_argument("--resume-state", action="store_true")
    p.add_argument("--save-html", action="store_true")
    p.add_argument("--max-pages", type=int, default=5)
    p.add_argument("--radius-km", type=float, default=0.0)
    p.add_argument("--location", default="")
    p.add_argument("--industry", default="")
    p.add_argument("--company", default="")
    p.add_argument("--businesses", nargs="*", default=[])
    return p.parse_args()

def main():
    args = parse_args()
    load_env()
    ensure_outdirs(args.outdir)

    with open(args.config, "r") as f:
        cfg = yaml.safe_load(f) or {}

    t0 = time.time()
    rows = ADAPTERS[args.adapter](args, cfg)
    if not rows:
        print("No rows scraped.")
        sys.exit(0)

    out_csv = Path(args.outdir) / f"{args.adapter}_{int(t0)}.csv"
    write_rows(rows, out_csv)
    print(f"✅ Data saved to {out_csv} ({len(rows)} records)")

if __name__ == "__main__":
    main()
