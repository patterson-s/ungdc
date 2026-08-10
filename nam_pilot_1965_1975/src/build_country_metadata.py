"""One-off script: build country_metadata.json for RA2's matched-control sampling.

region: taken directly from the corpus's own UN_REGION column (already present).
independence_year: filled from general historical knowledge for states that became
    sovereign in the 20th century (the decolonization/Cold War cohort relevant to NAM
    matching); left null for long-established states where "independence cohort" isn't
    a meaningful covariate (e.g. USA, France, Thailand, Ethiopia).
development_tier: a coarse, LOW-CONFIDENCE proxy (no clean contemporaneous classification
    exists for 1965-1975 -- World Bank tiers and the UN LDC list both postdate or barely
    overlap this period). RA2 must treat this as a weak signal and raise a question rather
    than trust it silently, per nam_discourse_plan.md S5.

Run once from repo root: python nam_pilot_1965_1975/src/build_country_metadata.py
"""
import json
from pathlib import Path

PILOT_DIR = Path(__file__).resolve().parents[1]
SPEECHES_PATH = PILOT_DIR / "data" / "speeches_1965_1975.jsonl"
OUT_PATH = PILOT_DIR / "data" / "country_metadata.json"

# iso -> independence year (20th-century / decolonization-cohort states only)
INDEPENDENCE_YEAR = {
    "AFG": None, "ALB": 1912, "ARE": 1971, "ARG": None, "AUS": None, "AUT": None,
    "BDI": 1962, "BEL": None, "BEN": 1960, "BFA": 1960, "BGD": 1971, "BGR": None,
    "BHR": 1971, "BHS": 1973, "BLR": None, "BOL": None, "BRA": None, "BRB": 1966,
    "BTN": None, "BWA": 1966, "CAF": 1960, "CAN": None, "CHL": None, "CHN": None,
    "CIV": 1960, "CMR": 1960, "COD": 1960, "COG": 1960, "COL": None, "CRI": None,
    "CSK": None, "CUB": 1902, "CYP": 1960, "DDR": 1949, "DEU": 1949, "DNK": None,
    "DOM": None, "DZA": 1962, "ECU": None, "EGY": 1922, "ESP": None, "ETH": None,
    "FIN": 1917, "FJI": 1970, "FRA": None, "GAB": 1960, "GBR": None, "GHA": 1957,
    "GIN": 1958, "GMB": 1965, "GNQ": 1968, "GRC": None, "GRD": 1974, "GTM": None,
    "GUY": 1966, "HND": None, "HTI": None, "HUN": None, "IDN": 1945, "IND": 1947,
    "IRL": 1922, "IRN": None, "IRQ": 1932, "ISL": 1944, "ISR": 1948, "ITA": None,
    "JAM": 1962, "JOR": 1946, "JPN": None, "KEN": 1963, "KHM": 1953, "KWT": 1961,
    "LAO": 1953, "LBN": 1943, "LBR": 1847, "LBY": 1951, "LKA": 1948, "LSO": 1966,
    "LUX": None, "MAR": 1956, "MDG": 1960, "MDV": 1965, "MEX": None, "MLI": 1960,
    "MLT": 1964, "MMR": 1948, "MNG": 1921, "MOZ": 1975, "MRT": 1960, "MUS": 1968,
    "MWI": 1964, "MYS": 1957, "NER": 1960, "NGA": 1960, "NIC": None, "NLD": None,
    "NOR": None, "NPL": None, "NZL": None, "OMN": None, "PAK": 1947, "PAN": None,
    "PER": None, "PHL": 1946, "POL": None, "PRT": None, "PRY": None, "QAT": 1971,
    "ROU": None, "RUS": None, "RWA": 1962, "SAU": 1932, "SDN": 1956, "SEN": 1960,
    "SGP": 1965, "SLE": 1961, "SLV": None, "SOM": 1960, "SWE": None, "SWZ": 1968,
    "SYR": 1946, "TCD": 1960, "TGO": 1960, "THA": None, "TTO": 1962, "TUN": 1956,
    "TUR": None, "TZA": 1964, "UGA": 1962, "UKR": None, "URY": None, "USA": None,
    "VEN": None, "YEM": 1918, "YMD": 1967, "YUG": None, "ZAF": None, "ZMB": 1964,
}

# iso -> coarse development tier (LOW CONFIDENCE, see module docstring)
TIER_OVERRIDE = {
    # high-income / industrialized blocs
    **{iso: "high" for iso in [
        "USA", "CAN", "GBR", "FRA", "DEU", "DDR", "AUT", "BEL", "DNK", "FIN", "ISL",
        "IRL", "ITA", "LUX", "NLD", "NOR", "SWE", "ESP", "PRT", "GRC", "AUS", "NZL",
        "JPN", "ISR",
    ]},
    # oil-wealthy Gulf states (income high even if "development" indicators lag)
    **{iso: "high" for iso in ["KWT", "ARE", "QAT", "BHR", "SAU"]},
    # Soviet bloc / Eastern Europe -- industrialized but non-market; upper-middle proxy
    **{iso: "upper-mid" for iso in ["RUS", "POL", "HUN", "BGR", "ROU", "CSK", "ALB", "BLR", "UKR", "YUG"]},
    # Latin America -- mostly middle-income for the era
    **{iso: "upper-mid" for iso in [
        "ARG", "CHL", "URY", "VEN", "MEX", "BRA", "COL", "CRI", "PAN", "CUB",
    ]},
    "PRY": "lower-mid", "ECU": "lower-mid", "PER": "lower-mid", "BOL": "lower-mid",
    "DOM": "lower-mid", "GTM": "lower-mid", "HND": "lower-mid", "NIC": "lower-mid",
    "SLV": "lower-mid", "JAM": "lower-mid", "TTO": "lower-mid", "GUY": "lower-mid",
    "BRB": "lower-mid", "BHS": "lower-mid", "GRD": "lower-mid", "HTI": "low",
    # Middle East / North Africa non-Gulf
    "EGY": "lower-mid", "DZA": "lower-mid", "MAR": "lower-mid", "TUN": "lower-mid",
    "LBY": "lower-mid", "IRQ": "lower-mid", "SYR": "lower-mid", "LBN": "lower-mid",
    "JOR": "lower-mid", "IRN": "lower-mid", "TUR": "lower-mid", "CYP": "lower-mid",
    "OMN": "lower-mid", "YEM": "low", "YMD": "low",
    # Asia
    "CHN": "low", "IND": "low", "PAK": "low", "BGD": "low", "NPL": "low", "AFG": "low",
    "BTN": "low", "MMR": "lower-mid", "LKA": "lower-mid", "KHM": "lower-mid",
    "LAO": "low", "IDN": "lower-mid", "MYS": "lower-mid", "SGP": "upper-mid",
    "PHL": "lower-mid", "THA": "lower-mid", "MNG": "lower-mid", "MDV": "low",
    "FJI": "lower-mid",
    # Sub-Saharan Africa -- default low/lower-mid (set as fallback below for AFRICA region)
    # ZMB: corpus mislabels UN_REGION as "OTHER" for this period (data quality quirk,
    # confirmed Zambia is Sub-Saharan Africa) -- override directly rather than trust the fallback.
    "ZMB": "low",
}

REGION_TIER_FALLBACK = {
    "AFRICA": "low",
    "ASIAPAC": "lower-mid",
    "GRULAC": "upper-mid",
    "WEOG": "high",
    "EASTEUROPE": "upper-mid",
    "OTHER": None,
}


def main():
    region_by_iso = {}
    with open(SPEECHES_PATH, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            region_by_iso.setdefault(r["iso"], set()).add(r["un_region"])

    out = {}
    unresolved_region = []
    for iso, regions in sorted(region_by_iso.items()):
        regions.discard("")
        region = sorted(regions)[0] if regions else None
        if len(regions) > 1:
            unresolved_region.append((iso, sorted(regions)))
        tier = TIER_OVERRIDE.get(iso) or REGION_TIER_FALLBACK.get(region)
        out[iso] = {
            "region": region,
            "independence_year": INDEPENDENCE_YEAR.get(iso),
            "development_tier": tier,
            "confidence": "low",
        }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)

    missing_tier = [iso for iso, v in out.items() if v["development_tier"] is None]
    print(f"Wrote metadata for {len(out)} countries to {OUT_PATH}")
    if unresolved_region:
        print(f"ISOs with inconsistent UN_REGION across rows (picked first alphabetically): {unresolved_region}")
    if missing_tier:
        print(f"ISOs with no resolvable development_tier: {missing_tier}")


if __name__ == "__main__":
    main()
