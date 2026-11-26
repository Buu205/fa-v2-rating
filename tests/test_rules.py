"""Rules of FA_V2 that must not drift. Runs without any data file."""
import numpy as np
import pandas as pd

from fa_v2 import bank, rules, scoring


def test_grade_scale_and_loan_rates():
    assert rules.GRADES == ["A", "B", "C", "D"]
    assert rules.LOAN == {"A": 50, "B": 40, "C": 30, "D": 20, "E": 0}


def test_weights_add_to_one():
    for m in (rules.COMPANY, rules.SECURITY, rules.BANK):
        assert abs(sum(m["weights"].values()) - 1) < 1e-12


def test_percentile_points_on_90_70_40_20():
    pts = scoring.edge_points(pd.Series([95, 90, 70, 40, 20, 5, np.nan]))
    assert pts.iloc[:6].tolist() == [4, 4, 3, 2, 1, 0] and pd.isna(pts.iloc[6])


def test_percentrank_inc_matches_excel():
    assert np.allclose(scoring.percentrank_inc(pd.Series([10, 20, 20, 40])), [0, 100 / 3, 100 / 3, 100])


def test_cutoffs_and_blank_score_is_not_rated():
    cuts = rules.COMPANY["cuts"]
    got = scoring.grade_of(pd.Series([1.90, 1.88, 1.65, 0.95, 0.94, np.nan]), cuts).tolist()
    assert got == ["A", "B", "B", "C", "D", "NR"]


def test_g1_one_notch_down_no_better_than_c():
    g = scoring.guard_g1(pd.Series(["A", "B", "C", "D", "NR"]), pd.Series([True] * 5))
    assert g.tolist() == ["C", "C", "D", "D", "NR"]


def test_g2_capital_impaired():
    hit = scoring.capital_impaired(pd.Series([-1.0, 100, 100]), pd.Series([0.0, -50, -49]), pd.Series([100.0, 100, 100]))
    assert hit.tolist() == [True, True, False]


def test_excluded_overrides_not_rated():
    g = scoring.exclude(pd.Series(["A", "NR", "B"]), pd.Series([True, True, None]))
    assert g.tolist() == ["E", "E", "B"]


def test_cover_ceiling_spares_top_ten_percent_above_once():
    g = scoring.cover_ceiling(pd.Series(["A", "A", "A", "B"]), pd.Series([1.5, 1.5, 0.5, 0.5]), pd.Series([0.5, 0.95, 0.95, 0.5]))
    assert g.tolist() == ["B", "A", "B", "B"]


def test_hold_band_keeps_grade_near_cutoff():
    cuts = ((2.0, "A"), (1.0, "B"), (0.5, "C"))
    df = pd.DataFrame({"ticker": ["X"] * 4, "report_date": pd.date_range("2025-03-31", periods=4, freq="QE")})
    score = pd.Series([2.5, 1.9, 1.7, 2.1])
    held = scoring.hold_band(df, scoring.grade_of(score, cuts), score, cuts)
    assert held.tolist() == ["A", "A", "B", "B"]   # 1.9 is within 0.20 of 2.0; 1.7 is not; 2.1 is not 0.20 above


def test_fixed_points_for_loss_quarters():
    F = pd.DataFrame({"report_date": pd.Timestamp("2025-03-31"), "loss_quarters8": [0, 1, 2, np.nan]})
    assert scoring.indicator_points(F, "loss_quarters8", False).tolist()[:3] == [2, 1, 0]


def test_bank_bands_and_consumer_finance():
    assert bank.band(1.5, rules.BANK["bands"]["npl"], False) == 4
    assert bank.band(3.0, rules.BANK["bands"]["npl"], False) == 2
    assert bank.band(2.9, rules.BANK["cf_bands"], False) == 4   # VPB/HDB: 2.9% NPL still scores full
    assert [round(c, 4) for c, _ in rules.BANK["cuts"]] == [2.7625, 2.3375, 1.9125]
