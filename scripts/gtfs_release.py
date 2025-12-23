# scripts/gtfs_release.py
from __future__ import annotations

import os
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
    """
    Download a file from GitHub Release asset (supports private repo via token).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        # GitHub release asset download works well with these headers
        "Accept": "application/octet-stream",
        "User-Agent": "gtfs-dashboard333",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with requests.get(url, stream=True, headers=headers, timeout=timeout, allow_redirects=True) as r:
        # If token missing/invalid for private repo, this will typically be 404.
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)


def _unzip(zip_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)


def ensure_gtfs_from_github_release(
    asset_url: str,
    gtfs_dir: str = "GTFS",
    marker_file: str = "GTFS/.ready",
    cache_zip_path: str = "cache/GTFS.zip",
    token: Optional[str] = None,
    force_redownload: bool = False,
) -> str:
    """
    Ensure GTFS data exists by downloading a GitHub Release asset zip and extracting it.

    - marker_file: existence indicates data is ready (skip download)
    - cache_zip_path: where the downloaded zip is stored
    """
    gtfs_path = Path(gtfs_dir)
    marker_path = Path(marker_file)
    zip_path = Path(cache_zip_path)

    if marker_path.exists() and not force_redownload:
        return f"GTFS already ready (marker found at {marker_path})."

    # Clean marker if force
    if force_redownload and marker_path.exists():
        try:
            marker_path.unlink()
        except Exception:
            pass

    _download_file(asset_url, zip_path, token=token)
    _unzip(zip_path, gtfs_path)

    # Create marker file (and parent dirs) to skip future downloads
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("ok", encoding="utf-8")

    return f"Downloaded and extracted GTFS to '{gtfs_path}'."
