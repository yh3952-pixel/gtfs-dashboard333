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
    """
    Download a file from GitHub Release asset (supports private repo via token).
    """
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


def _find_zip_root_with_signals(z: zipfile.ZipFile) -> Path:
    """
    在 zip 内定位“GTFS 根目录”：
    - 以 routes.txt 或 subway/routes.txt 等信号文件为锚
    - 返回该锚所在的父目录（即根目录）
    """
    names = [n for n in z.namelist() if not n.endswith("/")]
    # 优先 routes.txt
    for n in names:
        if n.endswith("routes.txt"):
            return Path(n).parent
    # 其次 stops.txt
    for n in names:
        if n.endswith("stops.txt"):
            return Path(n).parent
    # 找不到就认为 zip 顶层
    return Path("")


def _unzip_flatten(zip_path: Path, out_dir: Path, clean: bool = True) -> None:
    """
    解压并“扁平化”：
    - 如果 zip 内部带顶层 GTFS/，会把 GTFS/ 下的内容搬到 out_dir
    - 最终 out_dir 下应直接出现 subway/LIRR/MNR/bus_* 或 routes.txt 等
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # 清理旧数据（避免混杂）
    if clean and out_dir.exists():
        for item in out_dir.iterdir():
            # 保留 marker 由上层控制，这里全清
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    tmp = out_dir / "__tmp_unzip__"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(tmp)

        zip_root = _find_zip_root_with_signals(z)  # e.g. "GTFS/subway" -> parent "GTFS"
        src_root = (tmp / zip_root).resolve()

        # 如果定位到的是 subway 这一层（例如 .../GTFS/subway），再往上一层到包含多个子目录的根
        # 我们希望根目录下包含 subway/LIRR/MNR/bus_* 或 routes.txt
        # 若 src_root 本身就是 subway 目录，则取它的父目录
        if src_root.name.lower() == "subway":
            src_root = src_root.parent

        # 扁平化：把 src_root 下内容全部搬到 out_dir
        for item in src_root.iterdir():
            dest = out_dir / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))

    shutil.rmtree(tmp)


def _looks_like_gtfs_root(p: Path) -> bool:
    """
    判断 out_dir 是否像 GTFS 根目录：
    - 有 subway/LIRR/MNR 任一子目录
    - 或直接包含 routes.txt / stops.txt（某些数据包不分子目录）
    """
    if (p / "subway").exists():
        return True
    if (p / "LIRR").exists() or (p / "MNR").exists():
        return True
    if (p / "routes.txt").exists() and (p / "stops.txt").exists():
        return True
    return False


def ensure_gtfs_from_github_release(
    asset_url: str,
    gtfs_dir: str = "GTFS",
    marker_file: str = "GTFS/.ready",
    cache_zip_path: str = "cache/GTFS.zip",
    token: Optional[str] = None,
    force_redownload: bool = False,
    clean: bool = True,
) -> str:
    """
    Ensure GTFS data exists by downloading a GitHub Release asset zip and extracting it.

    Improvements vs old version:
    - unzip with flatten to avoid GTFS/GTFS nesting
    - optional clean to avoid mixing old/new files
    - validate structure before writing marker
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
    _unzip_flatten(zip_path, gtfs_path, clean=clean)

    # Validate before marking ready
    if not _looks_like_gtfs_root(gtfs_path):
        # 不要写 marker，让上层能重试/报错
        raise RuntimeError(
            f"GTFS extracted but layout invalid under '{gtfs_path}'. "
            f"Expected 'subway/' or 'routes.txt'. Please check your zip structure."
        )

    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("ok", encoding="utf-8")

    return f"Downloaded, flattened, and extracted GTFS to '{gtfs_path}'."
