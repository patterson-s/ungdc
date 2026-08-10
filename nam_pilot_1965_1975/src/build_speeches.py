"""One-off extraction script: filter the UNGDC corpus to 1965-1975, join the NAM
membership flag, and write the pilot's speeches.jsonl. Run once from repo root:

    python nam_pilot_1965_1975/src/build_speeches.py
"""
import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PILOT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "data" / "ungdc_1946-2022.csv"
MEMBERSHIP_PATH = PILOT_DIR / "data" / "nam_membership.json"
OUT_PATH = PILOT_DIR / "data" / "speeches_1965_1975.jsonl"

YEAR_START, YEAR_END = 1965, 1975


def load_membership():
    with open(MEMBERSHIP_PATH, encoding="utf-8") as f:
        rows = json.load(f)
    by_iso = {}
    for r in rows:
        by_iso.setdefault(r["iso"], []).append(r)
    return by_iso


def nam_flag(by_iso, iso, year):
    for entry in by_iso.get(iso, []):
        if entry["accession_year"] <= year and (
            entry["departure_year"] is None or year < entry["departure_year"]
        ):
            return True
    return False


def main():
    by_iso = load_membership()
    isos_seen = set()
    written = 0
    nam_count = 0
    with open(CSV_PATH, encoding="utf-8", errors="replace") as f_in, open(
        OUT_PATH, "w", encoding="utf-8"
    ) as f_out:
        reader = csv.DictReader(f_in)
        for row in reader:
            try:
                year = int(row["year"])
            except (KeyError, ValueError):
                continue
            if not (YEAR_START <= year <= YEAR_END):
                continue
            iso = (row.get("iso") or "").strip()
            if not iso:
                continue
            is_nam = nam_flag(by_iso, iso, year)
            record = {
                "speech_id": row.get("doc_id", "").strip(),
                "iso": iso,
                "year": year,
                "session": row.get("session", "").strip(),
                "un_region": row.get("UN_REGION", "").strip(),
                "nam_flag": is_nam,
                "body": row.get("text", ""),
            }
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
            nam_count += int(is_nam)
            isos_seen.add(iso)

    print(f"Wrote {written} speech records to {OUT_PATH}")
    print(f"Unique ISO codes: {len(isos_seen)}")
    print(f"NAM-flagged: {nam_count} ({nam_count / written:.1%})  non-NAM: {written - nam_count}")


if __name__ == "__main__":
    main()
