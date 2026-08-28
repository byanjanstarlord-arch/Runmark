"""Contract generation engine synthesizing Runmark contracts from discovered evidence."""

from pathlib import Path

from runmark.contracts.canonicalizer import ContractCanonicalizer
from runmark.contracts.evidence import EvidenceCollector, ProjectEvidence
from runmark.contracts.security import ContractSanitizer
from runmark.contracts.validator import ContractValidator
from runmark.models.contract import (
    ComposeRequirement,
    ContainerContract,
    DependencyContract,
    DockerRequirement,
    EnvironmentContract,
    NetworkContract,
    PlatformContract,
    PortRequirement,
    ProjectContract,
    RunmarkContract,
    ServiceRequirement,
)


class ContractGenerator:
    """Evidence-driven generator for candidate Runmark environment contracts."""

    @classmethod
    def generate(cls, project_root: Path | str) -> tuple[RunmarkContract, ProjectEvidence]:
        """Inspect project manifests, extract evidence, and build a validated, canonical contract."""
        root = Path(project_root).resolve()
        evidence = EvidenceCollector.collect(root)

        # Build domain models
        project_contract = ProjectContract(name=evidence.project_name)

        # Platform default compatibility
        platform_contract = PlatformContract(
            os=["darwin", "linux", "windows"],
            architecture=["amd64", "arm64", "x86_64"],
        )

        # Dependencies
        dep_contract = DependencyContract(
            python=dict(sorted(evidence.dependencies.get("python", {}).items())),
            node=dict(sorted(evidence.dependencies.get("node", {}).items())),
        )

        # Services
        services_dict: dict[str, ServiceRequirement] = {}
        for s_name, s_data in sorted(evidence.services.items()):
            services_dict[s_name] = ServiceRequirement(
                version=s_data.get("version", ">=1.0"),
                required=s_data.get("required", True),
            )

        # Environment
        env_contract = EnvironmentContract(
            required=sorted(set(evidence.required_env_vars)),
            optional=sorted(set(evidence.optional_env_vars)),
        )

        # Network ports
        ports_dict: dict[str, PortRequirement] = {}
        for p_num, p_data in sorted(
            evidence.ports.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0]
        ):
            ports_dict[p_num] = PortRequirement(
                protocol=p_data.get("protocol", "tcp"),
                required=p_data.get("required", True),
            )
        net_contract = NetworkContract(ports=ports_dict)

        # Containers
        docker_req = DockerRequirement(required=True) if evidence.containers.get("docker") else None
        compose_req = (
            ComposeRequirement(required=True) if evidence.containers.get("compose") else None
        )
        containers_contract = ContainerContract(docker=docker_req, compose=compose_req)

        raw_contract = RunmarkContract.model_validate(
            {
                "$schema": "https://runmark.dev/schemas/contract-v1.json",
                "version": 1,
                "project": project_contract,
                "platform": platform_contract,
                "runtime": dict(sorted(evidence.runtimes.items())),
                "dependencies": dep_contract,
                "services": services_dict,
                "environment": env_contract,
                "network": net_contract,
                "containers": containers_contract,
            }
        )

        # 1. Canonicalize structure
        canonical_dict = ContractCanonicalizer.canonicalize(raw_contract)
        canonical_json = ContractCanonicalizer.to_json(raw_contract)

        # 2. Security validation boundary
        ContractSanitizer.scan_raw(canonical_json)

        # 3. JSON Schema & Semantic validation
        ContractValidator.validate(canonical_dict)
        contract = RunmarkContract.model_validate(canonical_dict)
        ContractValidator.validate_semantics(contract)

        return contract, evidence
