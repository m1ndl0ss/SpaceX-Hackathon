from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_PATH = PACKAGE_ROOT / "context" / "benelux.json"
ARTIFACTS_DIR = PACKAGE_ROOT / "artifacts"
BOOSTERS_DIR = ARTIFACTS_DIR / "boosters"
DATA_DIR = PACKAGE_ROOT / "data"
GBIF_DIR = DATA_DIR / "gbif"
ROADKILL_DIR = DATA_DIR / "roadkill"
PROCESSED_DIR = DATA_DIR / "processed"
DEFAULT_WAREHOUSE_DIR = PACKAGE_ROOT.parent.parent / "data"
WAREHOUSE_DIR = DEFAULT_WAREHOUSE_DIR
WAREHOUSE_FALLBACK_DIR = PACKAGE_ROOT.parent.parent / "data" / "raw"


def ensure_data_dirs() -> None:
    for path in (GBIF_DIR, ROADKILL_DIR, PROCESSED_DIR, BOOSTERS_DIR, ARTIFACTS_DIR):
        path.mkdir(parents=True, exist_ok=True)
