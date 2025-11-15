"""Automates installing HACS into the config directory."""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Protocol
from urllib import request


class Downloader(Protocol):
    """Abstraction to make downloading testable."""

    def fetch(self, url: str) -> bytes:  # pragma: no cover - interface contract
        ...


class HttpDownloader:
    """Downloads bytes over HTTP."""

    def fetch(self, url: str) -> bytes:
        with request.urlopen(url) as response:  # type: ignore[arg-type]
            return response.read()


@dataclass
class HACSInstaller:
    """Install HACS from a GitHub release archive if missing."""

    config_dir: Path
    downloader: Downloader = HttpDownloader()

    def ensure(self, version: str) -> bool:
        hacs_dir = self.config_dir / "custom_components" / "hacs"
        if hacs_dir.exists() and any(hacs_dir.iterdir()):
            return False

        archive_bytes = self.downloader.fetch(self._release_url(version))
        self._extract_hacs(archive_bytes, hacs_dir)
        (self.config_dir / "www" / "community").mkdir(parents=True, exist_ok=True)
        return True

    def _release_url(self, version: str) -> str:
        return f"https://github.com/hacs/integration/releases/download/{version}/hacs.zip"

    def _extract_hacs(self, archive_bytes: bytes, target_dir: Path) -> None:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
            zf.extractall(target_dir)
