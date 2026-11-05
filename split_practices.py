import csv
import datetime as dt
import os
import re
import sys

import pdfplumber

SEASON_START = dt.date(2026, 8, 24)
SEASON_END = dt.date(2026, 12, 31)
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
HEADER_RE = re.compile(r"Week\s+(\d+)\s+(\w+day)\b(.*)", re.I)
DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2,4})")
JUNK = ("GTSC Fall 2026 Practices", "Back to top")


def clean(text):
    lines = [l.rstrip() for l in (text or "").replace("​", "").splitlines()]
    lines = [l for l in lines if l.strip() and not any(j in l for j in JUNK)]
    return "\n".join(lines).strip()


def slug(text):
    s = re.sub(r"\(.*?\)", "", text.lower())
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:40] or "group"


def parse_header(text):
    m = HEADER_RE.search(text)
    if not m:
        return None
    week, day, rest = int(m.group(1)), m.group(2).lower(), m.group(3)
    stated = None
    d = DATE_RE.search(rest)
    if d:
        mo, da, yr = map(int, d.groups())
        yr = yr + 2000 if yr < 100 else yr
        try:
            stated = dt.date(yr, mo, da)
        except ValueError:
            pass
    return {"week": week, "day": day, "stated": stated, "line": m.group(0).strip()}


def resolve_date(h, prev):
    weekday = DAYS.index(h["day"])
    s = h["stated"]
    if s and SEASON_START <= s <= SEASON_END and s.weekday() == weekday and (prev is None or s > prev):
        return s, None
    if prev is None:
        guess = SEASON_START + dt.timedelta(weeks=h["week"] - 1, days=weekday)
    else:
        guess = prev + dt.timedelta(days=1)
        while guess.weekday() != weekday:
            guess += dt.timedelta(days=1)
    return guess, f"date fixed: header said '{h['line']}', using {guess}"


def split_page(page):
    tables = page.find_tables()
    if not tables:
        return [("all_groups", clean(page.extract_text()))]

    table = tables[0]
    rows = table.extract()
    ncols = max(len(r) for r in rows)
    groups = []
    for c in range(ncols):
        cells = [clean(r[c]) if c < len(r) else "" for r in rows]
        cells = [x for x in cells if x and not HEADER_RE.match(x)]
        if not cells:
            continue
        label, body = cells[0], "\n\n".join(cells[1:])
        if "\n" in label:
            label, rest = label.split("\n", 1)
            body = rest + ("\n\n" + body if body else "")
        groups.append((label.strip(), body.strip()))

    outside = page.outside_bbox(table.bbox).extract_text()
    extra = clean(HEADER_RE.sub("", outside or ""))
    if extra:
        groups = [(g, b + "\n\n[Page notes]\n" + extra) for g, b in groups]
    return groups


def main(pdf_path, out_dir="chunks"):
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    prev = None
    with pdfplumber.open(pdf_path) as pdf:
        for num, page in enumerate(pdf.pages, 1):
            h = parse_header(page.extract_text() or "")
            if not h:
                print(f"page {num}: no practice header, skipped")
                continue
            date, warning = resolve_date(h, prev)
            prev = date
            if warning:
                print(f"page {num}: {warning}")

            used = set()
            for label, body in split_page(page):
                if not body:
                    continue
                name = f"{date}_{slug(label)}"
                while name in used:
                    name += "_2"
                used.add(name)
                path = os.path.join(out_dir, name + ".txt")
                with open(path, "w") as f:
                    f.write(f"DATE: {date}\nGROUP: {label}\nSOURCE: {h['line']} (page {num})\n\n{body}\n")
                manifest.append({"file": path, "date": str(date), "group": label,
                                 "page": num, "chars": len(body), "date_note": warning or ""})

    with open(os.path.join(out_dir, "manifest.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0]))
        w.writeheader()
        w.writerows(manifest)
    print(f"\n{len(manifest)} chunks written to {out_dir}/")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "GTSC_2026-27_Official_Practice_Doc.pdf")
