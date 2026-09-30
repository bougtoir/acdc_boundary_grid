from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIGS = ROOT / "configs"
DATA_RAW = ROOT / "data_raw"
DATA_INTERIM = ROOT / "data_interim"
DATA_PROCESSED = ROOT / "data_processed"
PROVENANCE = ROOT / "provenance"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
TABLES = ROOT / "tables"
REPORTS = ROOT / "reports"
MANUSCRIPT = ROOT / "manuscript"
SUBMISSION = ROOT / "submission"
QC = ROOT / "qc"
HANDOFFS = ROOT / "handoffs"
