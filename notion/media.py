"""Never send private, local or malformed asset URLs to Notion."""
from __future__ import annotations
from ipaddress import ip_address
from urllib.parse import urlsplit

class UnsafeMediaURL(ValueError):
    pass

def require_external_media_url(url: str) -> str:
    if not url:
        raise UnsafeMediaURL("Missing external asset URL")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
    except ValueError as exc:
        raise UnsafeMediaURL("Malformed media URL") from exc
    if parsed.scheme != "https" or not hostname or parsed.username or parsed.password:
        raise UnsafeMediaURL("Only publicly addressed HTTPS URLs are supported")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise UnsafeMediaURL("Local media host is forbidden")
    try:
        if not ip_address(hostname).is_global:
            raise UnsafeMediaURL("Private or reserved network address")
    except ValueError:
        pass  # Ordinary DNS name, not an IP address literal.
    return url
