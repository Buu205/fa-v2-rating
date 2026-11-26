"""Optional: compare a run against saved reference grades.
Set FA_V2_DATA to the input folder and FA_V2_REFERENCE to a CSV with ticker, report_date, group, grade."""
import os

import pandas as pd
import pytest

from fa_v2 import rate_all

DATA, REF = os.environ.get("FA_V2_DATA"), os.environ.get("FA_V2_REFERENCE")


@pytest.mark.skipif(not (DATA and REF), reason="FA_V2_DATA and FA_V2_REFERENCE not set")
def test_grades_match_reference():
    ref = pd.read_csv(REF, parse_dates=["report_date"])
    got = rate_all(DATA)
    m = ref.merge(got, on=["ticker", "report_date", "group"], how="left", suffixes=("_ref", ""))
    diff = m[m.grade_ref.fillna("NR") != m.grade.fillna("NR")]
    assert diff.empty, diff.head(20).to_string()
