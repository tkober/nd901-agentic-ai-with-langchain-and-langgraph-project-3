from pathlib import Path
import shutil
import pandas as pd
import os


def rollback_databases() -> None:
    """Delete current DBs and copy backups into place."""

    repo_root = Path(__file__).resolve().parents[1]

    cultpass_dst = repo_root / "starter" / "data" / "external" / "cultpass.db"
    udahub_dst = repo_root / "starter" / "data" / "core" / "udahub.db"

    backup_dir = repo_root / "starter" / "data" / "backup"
    cultpass_src = backup_dir / "cultpass.db"
    udahub_src = backup_dir / "udahub.db"

    if not cultpass_src.exists() or not udahub_src.exists():
        raise FileNotFoundError(
            "Missing backup DB(s) in starter/data/backup. "
            "Expected cultpass.db and udahub.db."
        )

    cultpass_dst.parent.mkdir(parents=True, exist_ok=True)
    udahub_dst.parent.mkdir(parents=True, exist_ok=True)

    if cultpass_dst.exists():
        cultpass_dst.unlink()
    if udahub_dst.exists():
        udahub_dst.unlink()

    shutil.copyfile(cultpass_src, cultpass_dst)
    shutil.copyfile(udahub_src, udahub_dst)


def load_udahub_table(table_name: str) -> pd.DataFrame:
    """Load a table from the udahub.db into a DataFrame."""
    UDAHUB_DB_PATH = os.getenv("UDAHUB_DB_PATH", "sqlite:///data/core/udahub.db")

    db_path = Path(UDAHUB_DB_PATH)
    if not db_path.exists():
        raise FileNotFoundError(
            f"UDAHUB_DB_PATH points to a non-existent file: {db_path}"
        )

    return pd.read_sql_query(f"SELECT * FROM {table_name}", con=UDAHUB_DB_PATH)
