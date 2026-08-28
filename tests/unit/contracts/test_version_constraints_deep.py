"""Deep unit tests for version constraints edge cases and operators."""

from runmark.contracts.version_constraints import (
    ParsedVersion,
    SingleClause,
    VersionConstraint,
    parse_version,
)


class TestVersionConstraintsDeep:
    """Additional edge cases for version constraint engine."""

    def test_tilde_and_caret_expressions(self) -> None:
        vc_tilde = VersionConstraint.parse("~3.12.0")
        assert vc_tilde.matches("3.12.0")
        assert vc_tilde.matches("3.12.4")

        vc_caret = VersionConstraint.parse("^20.0.0")
        assert vc_caret.matches("20.0.0")
        assert vc_caret.matches("20.11.0")

    def test_version_representation(self) -> None:
        vc = VersionConstraint.parse(">=3.12, <3.13")
        assert str(vc) == ">=3.12, <3.13"
        assert repr(vc) == "VersionConstraint('>=3.12, <3.13')"

    def test_single_clause_representations(self) -> None:
        c_star = SingleClause(op="wildcard", target=ParsedVersion(0, 0, 0), wildcard_depth=0)
        assert repr(c_star) == "*"

        c_major = SingleClause(op="wildcard", target=ParsedVersion(3, 0, 0), wildcard_depth=1)
        assert repr(c_major) == "3.x"

        c_minor = SingleClause(op="wildcard", target=ParsedVersion(3, 12, 0), wildcard_depth=2)
        assert repr(c_minor) == "3.12.x"

    def test_prerelease_and_build_metadata(self) -> None:
        v_build = parse_version("1.0.0+20130313144700")
        assert v_build.major == 1
        assert v_build.minor == 0
        assert v_build.patch == 0
