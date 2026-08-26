"""Service detectors package."""

from runmark.detectors.services.postgres import PostgresDetector
from runmark.detectors.services.redis import RedisDetector

__all__ = [
    "PostgresDetector",
    "RedisDetector",
]
