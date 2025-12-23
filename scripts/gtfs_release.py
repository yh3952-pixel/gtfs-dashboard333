from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional

import requests


def _download_file(
    url: str,
    out_path: Path,
    token: Optional[str] = None,
    timeout: int = 180,
    chunk_size: int = 1024 * 1024,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "Accept": "application/octet-stream",
        "User-Agent": "gtfs-dashboard333",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with requests.get(url, stream=True, headers=headers, timeout=timeout, allow_redirects=True) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)


def _safe_join(base: Path, rel: Path) -> Path:
    """Prevent zip-slip."""
    dest = (base / rel).resolve()
    base_resolved = base.resolve()
    if not str(dest).startswith(str(base_resolved)):
        raise RuntimeError(f"Unsafe path in zip: {rel}")
    return dest


def _unzip_strip_top_folder(zip_path: Path, out_dir: Path) -> None:
    """
    Extract zip into out_dir, but if all files share a single top-level folder
    (e.g. 'GTFS/...'), strip that folder so we don't end up with out_dir/GTFS/...
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        names = [n for n in z.namelist() if n and not n.endswith("/")]
        if not names:
            return

        # compute top-level folder if uniform
        first_parts = {Path(n).parts[0] for n in names if Path(n).parts}
        strip_one = len(first_parts) == 1
        top = next(iter(first_parts)) if strip_one else None

        for member in z.infolist():
            name = member.filename
            if not name or name.endswith("/"):
                continue

            p = Path(name)

            # strip the single top folder (commonly "GTFS")
            if strip_one and top and p.parts and p.parts[0] == top:
                rel = Path(*p.parts[1:])
            else:
                rel = p

            if not rel.parts:
                continue

            dest = _safe_join(out_dir, rel)
            dest.parent.mkdir(parents=True, exist_ok=True)

            with z.open(member) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst)


def ensure_gtfs_from_github_release(
    asset_url: str,
    gtfs_dir: str = "GTFS",
    marker_file: str = "GTFS/.ready",
    cache_zip_path: str = "cache/GTFS.zip",
    token: Optional[str] = None,
    force_redownload: bool = False,
    clean: bool = True,
) -> str:
    gtfs_path = Path(gtfs_dir)
    marker_path = Path(marker_file)
    zip_path = Path(cache_zip_path)

    if marker_path.exists() and not force_redownload:
        return f"GTFS already ready (marker found at {marker_path})."

    # clean old contents to avoid mixing wrong layouts
    if clean and gtfs_path.exists():
        shutil.rmtree(gtfs_path, ignore_errors=True)
    if marker_path.exists():
        try:
            marker_path.unlink()
        except Exception:
            pass

    _download_file(asset_url, zip_path, token=token)
    _unzip_strip_top_folder(zip_path, gtfs_path)

    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("ok", encoding="utf-8")

    return f"Downloaded and extracted GTFS to '{gtfs_path}'."
