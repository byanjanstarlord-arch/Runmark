"""Unit tests for environment variable detection and secret handling."""

from pathlib import Path

from runmark.detectors.base import DetectionContext
from runmark.detectors.environment.env import EnvDetector
from runmark.models.common import DetectionStatus

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


def test_env_example_identifies_required_variables():
    detector = EnvDetector()
    context = DetectionContext(
        project_root=FIXTURES_DIR / "python_project",
        environment={},
    )
    res = detector.detect(context)

    assert res.status == DetectionStatus.DETECTED
    vars_map = res.data.variables

    assert "DATABASE_URL" in vars_map
    assert vars_map["DATABASE_URL"].required is True
    assert vars_map["DATABASE_URL"].present is False
    assert vars_map["DATABASE_URL"].secret is True

    assert "STRIPE_SECRET_KEY" in vars_map
    assert vars_map["STRIPE_SECRET_KEY"].required is True
    assert vars_map["STRIPE_SECRET_KEY"].secret is True


def test_existing_variable_detected_as_present():
    detector = EnvDetector()
    env_mock = {
        "DATABASE_URL": "postgres://secret_user:secret_pass@localhost:5432/db",
        "STRIPE_SECRET_KEY": "sk_test_1234567890",
        "DEBUG": "True",
    }
    context = DetectionContext(
        project_root=FIXTURES_DIR / "python_project",
        environment=env_mock,
    )
    res = detector.detect(context)

    assert res.status == DetectionStatus.DETECTED
    vars_map = res.data.variables

    assert vars_map["DATABASE_URL"].present is True
    assert vars_map["STRIPE_SECRET_KEY"].present is True
    assert vars_map["DEBUG"].present is True


def test_missing_required_variable_detected():
    detector = EnvDetector()
    env_mock = {
        "DEBUG": "True",
        # STRIPE_SECRET_KEY and DATABASE_URL are missing!
    }
    context = DetectionContext(
        project_root=FIXTURES_DIR / "python_project",
        environment=env_mock,
    )
    res = detector.detect(context)

    vars_map = res.data.variables
    assert vars_map["STRIPE_SECRET_KEY"].required is True
    assert vars_map["STRIPE_SECRET_KEY"].present is False
