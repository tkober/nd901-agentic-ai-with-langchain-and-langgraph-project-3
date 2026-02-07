from pathlib import Path
import shutil


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
