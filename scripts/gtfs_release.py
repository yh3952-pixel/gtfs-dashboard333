# scripts/gtfs_release.py
from __future__ import annotations

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


def _zip_top_level_dirs(z: zipfile.ZipFile) -> set[str]:
    """
    返回 zip 顶层目录集合（例如 {'GTFS'} 或 {'subway','LIRR',...}）
    """
    tops = set()
    for name in z.namelist():
        if not name or name.startswith("__MACOSX/"):
            continue
        parts = name.split("/")
        if parts and parts[0]:
            tops.add(parts[0])
    return tops


def _looks_like_multi_feed_root(p: Path) -> bool:
    """
    判定目录 p 是否像你的“多子目录 GTFS 根”：
    - 存在 subway/ 或 LIRR/ 或 MNR/
    - 或存在任意 bus_*/routes.txt
    """
    if (p / "subway").is_dir() or (p / "LIRR").is_dir() or (p / "MNR").is_dir():
        return True
    for d in p.glob("bus_*"):
        if d.is_dir() and (d / "routes.txt").exists():
            return True
    return False


def _clean_dir(p: Path) -> None:
    if not p.exists():
        return
    for item in p.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def _unzip_preserve_structure(zip_path: Path, out_dir: Path, clean: bool = True) -> None:
    """
    只去掉 zip 最外层“单一容器目录”（常见为 GTFS/），但保留 subway/LIRR/MNR/bus_* 结构。
    - 如果 zip 顶层就是 subway/LIRR/bus_*，则直接解压到 out_dir
    - 如果 zip 顶层只有一个目录（如 GTFS/），则解压到 out_dir 并去掉该外层目录
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if clean:
        _clean_dir(out_dir)

    tmp = out_dir / "__tmp_unzip__"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(tmp)
        tops = _zip_top_level_dirs(z)

    # 情况 A：zip 顶层就是多个 feed 目录（subway/LIRR/bus_*）
    # 直接把 tmp 下的内容搬到 out_dir
    if len(tops) != 1:
        for item in tmp.iterdir():
            shutil.move(str(item), str(out_dir / item.name))
        shutil.rmtree(tmp)
        return

    # 情况 B：zip 顶层只有一个容器目录（例如 GTFS/）
    container = tmp / next(iter(tops))
    if not container.exists() or not container.is_dir():
        # 理论上不会发生，兜底
        for item in tmp.iterdir():
            shutil.move(str(item), str(out_dir / item.name))
        shutil.rmtree(tmp)
        return

    # 把 container 里面的内容搬到 out_dir（保留子目录结构）
    for item in container.iterdir():
        shutil.move(str(item), str(out_dir / item.name))

    shutil.rmtree(tmp)


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

    if force_redownload and marker_path.exists():
        try:
            marker_path.unlink()
        except Exception:
            pass

    _download_file(asset_url, zip_path, token=token)
    _unzip_preserve_structure(zip_path, gtfs_path, clean=clean)

    # 校验结构：必须是多-feed结构
    if not _looks_like_multi_feed_root(gtfs_path):
        raise RuntimeError(
            f"GTFS extracted but structure is not multi-feed under '{gtfs_path}'. "
            f"Expected folders like subway/LIRR/MNR/bus_*."
        )

    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("ok", encoding="utf-8")

    return f"Downloaded and extracted GTFS to '{gtfs_path}'."
