import csv

def write_rows(rows, path):
    if not rows:
        return
    keys = set()
    for r in rows:
        keys.update(r.keys())
    keys = sorted(keys)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
