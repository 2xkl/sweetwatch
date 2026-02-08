"""CGM data sources."""

from typing import TYPE_CHECKING

from .base import CGMSource, GlucoseEntry, Trend
from .librelinkup import LibreLinkUpSource
from .nightscout import NightscoutSource

if TYPE_CHECKING:
    from sweetwatch.config import Settings

__all__ = [
    "CGMSource",
    "GlucoseEntry",
    "Trend",
    "NightscoutSource",
    "LibreLinkUpSource",
    "create_source",
]


def create_source(settings: "Settings") -> CGMSource:
    """Create a CGM source based on configuration.

    Args:
        settings: Application settings containing source configuration.

    Returns:
        Configured CGM source instance.

    Raises:
        ValueError: If the configured source type is unknown.
    """
    source_type = settings.cgm_source.lower()

    if source_type == "nightscout":
        if not settings.nightscout_url:
            raise ValueError("NIGHTSCOUT_URL is required when CGM_SOURCE=nightscout")
        return NightscoutSource(
            url=settings.nightscout_url,
            api_secret=settings.nightscout_api_secret,
        )

    if source_type == "librelinkup":
        if not settings.libre_username or not settings.libre_password:
            raise ValueError(
                "LIBRE_USERNAME and LIBRE_PASSWORD are required when CGM_SOURCE=librelinkup"
            )
        return LibreLinkUpSource(
            username=settings.libre_username,
            password=settings.libre_password,
            region=settings.libre_region,
        )

    raise ValueError(f"Unknown CGM source: {source_type}")
