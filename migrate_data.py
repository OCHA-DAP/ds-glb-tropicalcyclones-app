import os
import shutil
from pathlib import Path

DATA_DIR = Path(os.getenv("AA_DATA_DIR_NEW"))
IBRACS_PROC_DIR = DATA_DIR / "public" / "processed" / "glb" / "ibtracs"
IBRACS_THRESH_PATH = IBRACS_PROC_DIR / "all_adm0_thresholds.parquet"
IBRACS_WMO_PATH = IBRACS_PROC_DIR / "ibtracs_with_wmo_wind.parquet"

APP_DATA_DIR = Path("data")

paths = [
    IBRACS_THRESH_PATH,
    IBRACS_WMO_PATH,
]


def migrate_data():
    for path in paths:
        shutil.copy(path, APP_DATA_DIR / path.name)


if __name__ == "__main__":
    migrate_data()
