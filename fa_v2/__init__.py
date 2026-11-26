"""FA_V2: fundamental grades for margin lending on HOSE and HNX (companies, brokers, banks)."""
from . import bank, company, security

__version__ = "2.0.0"


def rate_all(folder):
    """Grades of every quarter for the three groups, one frame."""
    import pandas as pd
    keep = ["ticker", "report_date", "group", "exchange", "scale", "health", "profit", "score",
            "grade_score", "grade_held", "grade", "g1", "g2", "lasting_loss", "missing"]
    return pd.concat([m.build(folder).reindex(columns=keep) for m in (company, security, bank)], ignore_index=True)
