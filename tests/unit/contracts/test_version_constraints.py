"""Unit tests for semantic version constraint engine."""

import pytest

from runmark.contracts.version_constraints import (
    VersionConstraint,
    parse_version,
)


class TestVersionParser:
    """Tests for parse_version function."""

    def test_parse_standard_semver(self) -> None:
        v = parse_version("3.12.4")
        assert v.major == 3
        assert v.minor == 12
        assert v.patch == 4
        assert v.prerelease is None

    def test_parse_leading_v(self) -> None:
        v = parse_version("v20.11.0")
        assert v.major == 20
        assert v.minor == 11
        assert v.patch == 0

    def test_parse_partial_versions(self) -> None:
        v1 = parse_version("3")
        assert v1.major == 3
        assert v1.minor == 0
        assert v1.patch == 0

        v2 = parse_version("3.12")
        assert v2.major == 3
        assert v2.minor == 12
        assert v2.patch == 0

    def test_parse_extra_components(self) -> None:
        v = parse_version("3.12.4.1")
        assert v.major == 3
        assert v.minor == 12
        assert v.patch == 4
        assert v.extra == (1,)

    def test_parse_prerelease(self) -> None:
        v = parse_version("3.13.0-rc1")
        assert v.major == 3
        assert v.minor == 13
        assert v.patch == 0
        assert v.prerelease == "rc1"

    def test_parse_invalid_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            parse_version("")

        with pytest.raises(ValueError):
            parse_version("abc")


class TestVersionOrdering:
    """Tests for numerical (non-lexicographical) comparison."""

    def test_numeric_component_comparison(self) -> None:
        # Lexicographically, "3.12.10" < "3.12.4" because '1' < '4'
        # Numerically, 3.12.10 > 3.12.4
        v_low = parse_version("3.12.4")
        v_high = parse_version("3.12.10")

        assert v_high > v_low
        assert v_low < v_high
        assert v_low <= v_high
        assert v_high >= v_low
        assert v_low != v_high

    def test_prerelease_comparison(self) -> None:
        v_rc = parse_version("3.12.0-rc1")
        v_final = parse_version("3.12.0")
        assert v_rc < v_final


class TestVersionConstraintMatching:
    """Tests for VersionConstraint.parse and matching."""

    def test_exact_match(self) -> None:
        vc = VersionConstraint.parse("3.12.4")
        assert vc.matches("3.12.4")
        assert not vc.matches("3.12.5")
        assert not vc.matches("3.11.4")

    def test_wildcards(self) -> None:
        vc_minor = VersionConstraint.parse("3.12.x")
        assert vc_minor.matches("3.12.0")
        assert vc_minor.matches("3.12.4")
        assert vc_minor.matches("3.12.10")
        assert not vc_minor.matches("3.11.4")
        assert not vc_minor.matches("3.13.0")

        vc_major = VersionConstraint.parse("3.x")
        assert vc_major.matches("3.0.0")
        assert vc_major.matches("3.12.4")
        assert not vc_major.matches("4.0.0")

        vc_universal = VersionConstraint.parse("*")
        assert vc_universal.matches("1.0.0")
        assert vc_universal.matches("100.200.300")

    def test_operators(self) -> None:
        vc_gte = VersionConstraint.parse(">=3.12")
        assert vc_gte.matches("3.12.0")
        assert vc_gte.matches("3.12.4")
        assert vc_gte.matches("3.13.0")
        assert not vc_gte.matches("3.11.9")

        vc_gt = VersionConstraint.parse(">3.12.0")
        assert not vc_gt.matches("3.12.0")
        assert vc_gt.matches("3.12.1")

        vc_lte = VersionConstraint.parse("<=3.12.4")
        assert vc_lte.matches("3.12.4")
        assert vc_lte.matches("3.12.0")
        assert not vc_lte.matches("3.12.5")

        vc_lt = VersionConstraint.parse("<4.0")
        assert vc_lt.matches("3.12.4")
        assert not vc_lt.matches("4.0.0")
        assert not vc_lt.matches("4.1.0")

        vc_neq = VersionConstraint.parse("!=3.12.4")
        assert vc_neq.matches("3.12.3")
        assert vc_neq.matches("3.12.5")
        assert not vc_neq.matches("3.12.4")

    def test_compound_ranges(self) -> None:
        vc = VersionConstraint.parse(">=3.11, <3.13")
        assert vc.matches("3.11.0")
        assert vc.matches("3.12.4")
        assert not vc.matches("3.10.9")
        assert not vc.matches("3.13.0")
        assert not vc.matches("3.13.1")

    def test_none_or_unparseable_version(self) -> None:
        vc = VersionConstraint.parse(">=3.12")
        assert not vc.matches(None)
        assert not vc.matches("invalid-version-string")
