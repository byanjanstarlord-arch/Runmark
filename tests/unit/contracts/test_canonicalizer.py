"""Unit tests for ContractCanonicalizer."""

from runmark.contracts.canonicalizer import ContractCanonicalizer
from runmark.models.contract import RunmarkContract


class TestContractCanonicalizer:
    """Tests for deterministic canonicalization and fingerprinting."""

    def test_canonical_json_deterministic(self) -> None:
        c1 = RunmarkContract.model_validate(
            {
                "$schema": "https://example.com/schema.json",
                "version": 1,
                "project": {"name": "app"},
                "platform": {"os": ["windows", "linux"], "architecture": ["x86_64", "arm64"]},
                "runtime": {"python": "3.12.x", "node": "20.x"},
                "environment": {"required": ["FOO", "BAR"]},
            }
        )
        c2 = RunmarkContract.model_validate(
            {
                # Different schema URI and different property ordering
                "$schema": "other_schema.json",
                "version": 1,
                "environment": {"required": ["BAR", "FOO"]},
                "runtime": {"node": "20.x", "python": "3.12.x"},
                "platform": {"architecture": ["arm64", "x86_64"], "os": ["linux", "windows"]},
                "project": {"name": "app"},
            }
        )

        canon1 = ContractCanonicalizer.to_canonical_json(c1)
        canon2 = ContractCanonicalizer.to_canonical_json(c2)
        assert canon1 == canon2

        fp1 = ContractCanonicalizer.compute_fingerprint(c1)
        fp2 = ContractCanonicalizer.compute_fingerprint(c2)
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex digest

    def test_fingerprint_changes_on_semantic_difference(self) -> None:
        c1 = RunmarkContract.model_validate({"version": 1, "runtime": {"python": "3.12.x"}})
        c2 = RunmarkContract.model_validate({"version": 1, "runtime": {"python": "3.11.x"}})
        assert ContractCanonicalizer.compute_fingerprint(
            c1
        ) != ContractCanonicalizer.compute_fingerprint(c2)
