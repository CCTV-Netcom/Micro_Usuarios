from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse, urlunparse


def running_in_docker() -> bool:
    return Path("/.dockerenv").exists()


def normalize_local_url_for_container(raw_url: str | None) -> str:
    if not raw_url:
        return raw_url or ""

    if not running_in_docker():
        return raw_url

    parsed = urlparse(raw_url)
    hostname = parsed.hostname

    if hostname not in {"localhost", "127.0.0.1"}:
        return raw_url

    netloc = parsed.netloc.replace(hostname, "host.docker.internal", 1)
    return urlunparse(parsed._replace(netloc=netloc))