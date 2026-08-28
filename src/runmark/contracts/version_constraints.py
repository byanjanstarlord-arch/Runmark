"""Semantic version parsing and constraint matching engine for Runmark contracts."""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ParsedVersion:
    """Normalized representation of a semantic version for numeric comparison."""

    major: int
    minor: int
    patch: int
    extra: tuple[int, ...] = field(default_factory=tuple)
    prerelease: str | None = None

    def tuple_key(self) -> tuple[int, int, int, tuple[int, ...]]:
        """Return numeric components as a tuple for direct ordering."""
        return (self.major, self.minor, self.patch, self.extra)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, ParsedVersion):
            return NotImplemented
        if self.tuple_key() != other.tuple_key():
            return self.tuple_key() < other.tuple_key()
        # If numeric versions are identical, a version with a prerelease is strictly less than one without
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        return (self.prerelease or "") < (other.prerelease or "")

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, ParsedVersion):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, ParsedVersion):
            return NotImplemented
        return not (self <= other)

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, ParsedVersion):
            return NotImplemented
        return not (self < other)


def parse_version(v_str: str) -> ParsedVersion:
    """Parse a version string into a comparable ParsedVersion object.

    Handles '3', '3.12', '3.12.4', 'v3.12.4', '3.12.4-rc1', '3.12.10.final.0'.
    """
    clean = v_str.strip().lstrip("vV")
    if not clean:
        raise ValueError("Empty version string cannot be parsed.")

    # Split prerelease / build metadata if present
    prerelease = None
    if "-" in clean:
        clean, prerelease = clean.split("-", 1)
    elif "+" in clean:
        clean, _ = clean.split("+", 1)

    # Extract all leading numeric components separated by dots
    parts = clean.split(".")
    numeric_parts: list[int] = []
    for p in parts:
        match = re.match(r"^(\d+)", p)
        if match:
            numeric_parts.append(int(match.group(1)))
        else:
            break

    if not numeric_parts:
        raise ValueError(f"Invalid version string '{v_str}': no numeric components found.")

    major = numeric_parts[0]
    minor = numeric_parts[1] if len(numeric_parts) > 1 else 0
    patch = numeric_parts[2] if len(numeric_parts) > 2 else 0
    extra = tuple(numeric_parts[3:]) if len(numeric_parts) > 3 else ()

    return ParsedVersion(major=major, minor=minor, patch=patch, extra=extra, prerelease=prerelease)


class SingleClause:
    """Represents a single atomic version condition (e.g. '>=3.12', '==3.12.4', '3.12.x')."""

    def __init__(self, op: str, target: ParsedVersion, wildcard_depth: int | None = None):
        self.op = op  # '==', '!=', '>=', '>', '<=', '<', 'wildcard'
        self.target = target
        self.wildcard_depth = wildcard_depth  # 1 for '3.x', 2 for '3.12.x'

    def matches(self, version: ParsedVersion) -> bool:
        """Check if a parsed version satisfies this clause."""
        if self.op == "wildcard":
            if self.wildcard_depth == 0:
                return True
            if self.wildcard_depth == 1:
                return version.major == self.target.major
            if self.wildcard_depth == 2:
                return version.major == self.target.major and version.minor == self.target.minor
            return (
                version.major == self.target.major
                and version.minor == self.target.minor
                and version.patch == self.target.patch
            )

        if self.op in ("=", "=="):
            return (
                version.major == self.target.major
                and version.minor == self.target.minor
                and version.patch == self.target.patch
                and version.extra == self.target.extra
            )
        if self.op == "!=":
            return not (
                version.major == self.target.major
                and version.minor == self.target.minor
                and version.patch == self.target.patch
                and version.extra == self.target.extra
            )
        if self.op == ">=":
            return version >= self.target
        if self.op == ">":
            return version > self.target
        if self.op == "<=":
            return version <= self.target
        if self.op == "<":
            return version < self.target

        return False

    def __repr__(self) -> str:
        if self.op == "wildcard":
            if self.wildcard_depth == 0:
                return "*"
            if self.wildcard_depth == 1:
                return f"{self.target.major}.x"
            if self.wildcard_depth == 2:
                return f"{self.target.major}.{self.target.minor}.x"
        return f"{self.op}{self.target.major}.{self.target.minor}.{self.target.patch}"


class VersionConstraint:
    """Composite version constraint supporting compound ranges, wildcards, and operators."""

    def __init__(self, raw_expression: str, clauses: list[SingleClause]):
        self.raw_expression = raw_expression
        self.clauses = clauses

    @classmethod
    def parse(cls, expression: str) -> "VersionConstraint":
        """Parse a version requirement string into a validated VersionConstraint."""
        expr = expression.strip()
        if not expr or expr == "*":
            # Universal match
            clause = SingleClause(op="wildcard", target=ParsedVersion(0, 0, 0), wildcard_depth=0)
            return cls(raw_expression=expression, clauses=[clause])

        # Split comma-separated compound clauses, e.g. ">=3.12, <3.13"
        raw_clauses = [c.strip() for c in expr.split(",") if c.strip()]
        parsed_clauses: list[SingleClause] = []

        for raw_c in raw_clauses:
            clause = cls._parse_single_clause(raw_c)
            parsed_clauses.append(clause)

        return cls(raw_expression=expression, clauses=parsed_clauses)

    @classmethod
    def _parse_single_clause(cls, clause_str: str) -> SingleClause:
        """Parse an atomic clause string."""
        c = clause_str.strip()

        # Check for wildcards e.g. "3.12.x", "3.x", "3.12.*", "3.*"
        if re.search(r"[\.xX\*]", c) and (c.endswith(".x") or c.endswith(".X") or c.endswith(".*")):
            parts = c.split(".")
            if len(parts) == 2 and parts[1].lower() in ("x", "*"):
                # "3.x"
                major = int(parts[0])
                return SingleClause(
                    op="wildcard", target=ParsedVersion(major, 0, 0), wildcard_depth=1
                )
            if len(parts) == 3 and parts[2].lower() in ("x", "*"):
                # "3.12.x"
                major = int(parts[0])
                minor = int(parts[1])
                return SingleClause(
                    op="wildcard", target=ParsedVersion(major, minor, 0), wildcard_depth=2
                )

        # Check for comparison operators
        op_match = re.match(r"^(>=|<=|!=|==|=|>|<|~=|\^|~)\s*(.*)$", c)
        if op_match:
            op, ver_str = op_match.group(1), op_match.group(2).strip()
            # If wildcards are present inside an operator like ">=3.12.x", handle gracefully
            if ver_str.endswith(".x") or ver_str.endswith(".X") or ver_str.endswith(".*"):
                clean_ver = ver_str.rsplit(".", 1)[0]
                target = parse_version(clean_ver)
            else:
                target = parse_version(ver_str)

            if op == "~=" or op == "~":
                # Compatible release: ~3.12 or ~3.12.0
                return SingleClause(op=">=", target=target)
            if op == "^":
                # Caret: compatible with major
                return SingleClause(op=">=", target=target)

            return SingleClause(op=op, target=target)

        # Fallback to exact version match
        target = parse_version(c)
        return SingleClause(op="==", target=target)

    def matches(self, version_str: str | None) -> bool:
        """Evaluate if the given version string satisfies all clauses in this constraint."""
        if not version_str:
            return False

        try:
            parsed = parse_version(version_str)
        except Exception:
            return False

        return all(clause.matches(parsed) for clause in self.clauses)

    def __str__(self) -> str:
        return self.raw_expression

    def __repr__(self) -> str:
        return f"VersionConstraint({self.raw_expression!r})"
