"""Every rule of FA_V2 in one place: grades, loan rates, weights, indicators, cutoffs, guards.

Change a rule here, never inside the scoring code. The docs in docs/ quote these values.
"""
from __future__ import annotations

# ---------------------------------------------------------------- grade scale
GRADES = ["A", "B", "C", "D"]
NAMES = {"A": "Safe", "B": "Caution", "C": "Reduce", "D": "High Risk", "E": "Excluded", "NR": "Not Rated"}
LOAN = {"A": 50, "B": 40, "C": 30, "D": 20, "E": 0}   # % of price; NR has no rate (blank, not 0)
RANK = {g: i for i, g in enumerate(GRADES)}

# Only HOSE and HNX names can be margin-lent; UPCoM is neither rated nor used as a peer.
EXCHANGES = ("HOSE", "HNX")

# ---------------------------------------------------------------- percentile points
# Excel PERCENTRANK.INC x 100 inside the quarter, then 4 points from the 90th percentile,
# 3 from the 70th, 2 from the 40th, 1 from the 20th, else 0.
PCT_EDGES = (90, 70, 40, 20)
# Scored on fixed marks instead of a percentile, because most names share the best value:
# 0 loss quarters out of 8 gives 2 points, 1 gives 1 point, 2 or more gives 0.
FIXED_POINTS = {"loss_quarters8": (0, 1)}

# ---------------------------------------------------------------- non-financial companies
COMPANY = {
    "weights": {"scale": 0.50, "health": 0.30, "profit": 0.20},
    # pillar -> [(indicator, higher is better)], equal weight inside a pillar
    "pillars": {
        "scale": [("revenue_ttm", True), ("revenue_steady", True), ("assets_avg4", True)],
        "health": [("fincost_cover", True), ("netdebt_equity", False), ("loss_quarters8", False)],
        "profit": [("roa", True), ("ebit_margin", True)],
    },
    # Scale is ranked against the whole market, except revenue steadiness, which is ranked inside
    # the industry: revenue booked at handover (real estate) is lumpy by accounting, not by risk.
    "industry_ranked": ("revenue_steady",),
    # Fixed cutoffs set from past price falls, half a step (1/60) under the lowest score that earns
    # the grade: A from 1.883, B from 1.650, C from 0.950, below C is D.
    "cuts": ((113 / 60, "A"), (99 / 60, "B"), (57 / 60, "C")),
    "min_industry_peers": 10,          # an ICB level-2 industry smaller than this merges into level 1
    "cover_ceiling": (1.0, 2.0),       # EBIT / finance cost below 2 holds A at B; below 1 for the top 10% by cap
    "ceiling_spared_cap_pct": 0.90,    # top 10% by the quarter's average market cap uses the 1x mark
}

# ---------------------------------------------------------------- securities companies (brokers)
SECURITY = {
    "weights": {"scale": 0.50, "health": 0.30, "profit": 0.20},
    "pillars": {
        "scale": [("assets_avg4", True), ("equity_avg4", True), ("margin_avg4", True)],
        # loans / equity counts as better when higher: it measures how far the firm lives off lending
        "health": [("loan_equity", True), ("fvtpl_share", False), ("liquid", True)],
        "profit": [("roe_min4", True), ("roe", True)],
    },
    "industry_ranked": (),
    "cuts": ((2.31, "A"), (1.50, "B"), (0.90, "C")),
}

# ---------------------------------------------------------------- banks
BANK = {
    # Scale 50%; what is left splits 4:3 between Health and Profit (28.6% and 21.4%)
    "weights": {"scale": 0.50, "health": 0.50 * 4 / 7, "profit": 0.50 * 3 / 7},
    # Scale: share of the industry in the quarter, tiered: top half 4, 25-50% 3, 10-25% 2, bottom 10% 1
    "scale": ("sh_assets", "sh_ppop", "sh_equity"),
    "scale_tiers": (0.10, 0.25, 0.50),
    # Health and Profit: fixed bands, 1 to 4 points (4 = best)
    "bands": {"npl": (1.9, 2.5, 3.5), "g2": (1.5, 2.2, 3.5), "llcr": (42, 51, 67),
              "roe": (4.0, 7.8, 13.4), "roe_min": (-5.3, 0.2, 5.3), "ppop_ta": (0.8, 1.25, 2.1)},
    # VPB and HDB carry consumer-finance books: their NPL and group-2 bands are wider
    "consumer_finance": ("VPB", "HDB"),
    "cf_bands": (3.0, 4.0, 5.5),
    # the base cutoffs 3.25 / 2.75 / 2.25 lowered by 15%: 2.7625 / 2.3375 / 1.9125
    "cuts": ((3.25 * 0.85, "A"), (2.75 * 0.85, "B"), (2.25 * 0.85, "C")),
    # the first quarter with twelve quarters of ROE behind it; stabilisation starts here
    "history_start": "2019-12-31",
}

# ---------------------------------------------------------------- guards and stabilisers
G2_ACCUMULATED_LOSS = 0.5   # accumulated loss from 50% of charter capital excludes the name
HOLD_MARGIN = 0.20          # a one-notch move set by the score alone must clear the cutoff by 0.20
