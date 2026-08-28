"""Integration tests for contract evaluation determinism over repeated iterations."""

import json
from pathlib import Path

from typer.testing import CliRunner

from runmark.cli.app import app
from runmark.contracts.canonicalizer import ContractCanonicalizer
from runmark.contracts.evaluator import ContractEvaluator
from runmark.contracts.parser import ContractParser
from runmark.core.scanner import Scanner

runner = CliRunner()


def test_100_runs_determinism(tmp_path: Path) -> None:
    contract_data = {
        "version": 1,
        "project": {"name": "deterministic-test"},
        "platform": {
            "os": ["linux", "windows", "darwin"],
            "architecture": ["x86_64", "amd64", "arm64"],
        },
        "runtime": {"python": ">=3.8"},
        "services": {"postgresql": {"version": ">=14", "required": False}},
        "environment": {"optional": ["TEST_OPT_VAR"]},
    }
    contract_file = tmp_path / "runmark.json"
    contract_file.write_text(json.dumps(contract_data), encoding="utf-8")

    contract = ContractParser.parse_file(contract_file)
    baseline_fingerprint = ContractCanonicalizer.compute_fingerprint(contract)
    baseline_canonical = ContractCanonicalizer.to_canonical_json(contract)

    # Pre-scan once for evaluator loop
    scanner = Scanner(tmp_path)
    state = scanner.scan()
    baseline_eval = ContractEvaluator.evaluate(contract, state)
    baseline_eval_json = baseline_eval.model_dump_json()

    for _ in range(100):
        # 1. Canonicalizer determinism
        iter_fp = ContractCanonicalizer.compute_fingerprint(contract)
        iter_canon = ContractCanonicalizer.to_canonical_json(contract)
        assert iter_fp == baseline_fingerprint
        assert iter_canon == baseline_canonical

        # 2. Evaluator determinism
        iter_eval = ContractEvaluator.evaluate(contract, state)
        assert iter_eval.model_dump_json() == baseline_eval_json

    # 3. CLI execution determinism
    for _ in range(3):
        res = runner.invoke(app, ["check", "--path", str(tmp_path), "--json"])
        assert res.exit_code == 0
        parsed = json.loads(res.stdout)
        assert parsed["status"] == "PASS"
