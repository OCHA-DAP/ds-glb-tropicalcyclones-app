import os
import shutil
from pathlib import Path

OLD_DATA_DIR = Path(os.getenv("AA_DATA_DIR", "default"))
DATA_DIR = Path(os.getenv("AA_DATA_DIR_NEW", "default"))
IBRACS_PROC_DIR = DATA_DIR / "public" / "processed" / "glb" / "ibtracs"
IBRACS_THRESH_PATH = IBRACS_PROC_DIR / "all_adm0_thresholds.parquet"
IBRACS_WMO_PATH = IBRACS_PROC_DIR / "ibtracs_with_wmo_wind.parquet"
GAUL0_PATH = (
    OLD_DATA_DIR
    / "public"
    / "raw"
    / "glb"
    / "asap"
    / "reference_data"
    / "gaul0_asap_v04"
)
EMDAT_PROC_PATH = (
    DATA_DIR
    / "private"
    / "processed"
    / "glb"
    / "emdat"
    / "emdat-tropicalcyclone-2000-2022-processed-sids.csv"
)

APP_DATA_DIR = Path("data")

paths = [IBRACS_THRESH_PATH, IBRACS_WMO_PATH, GAUL0_PATH, EMDAT_PROC_PATH]


def migrate_data():
    for path in paths:
        if path.is_dir():
            shutil.copytree(path, APP_DATA_DIR / path.name, dirs_exist_ok=True)
        else:
            shutil.copy(path, APP_DATA_DIR / path.name)


if __name__ == "__main__":
    migrate_data()
