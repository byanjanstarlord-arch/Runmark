"""Common enums and base definitions for Runmark models."""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class RunmarkBaseModel(BaseModel):
    """Base model enforcing strict configuration for all Runmark state objects."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class DetectionStatus(str, Enum):
    """Status outcomes for detectors."""

    DETECTED = "detected"
    NOT_FOUND = "not_found"
    NOT_APPLICABLE = "not_applicable"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


class DependencyKind(str, Enum):
    """Kind/scope of dependency."""

    DIRECT = "direct"
    TRANSITIVE = "transitive"
    DEV = "dev"
    PEER = "peer"
    UNKNOWN = "unknown"
