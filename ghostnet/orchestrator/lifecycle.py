from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ghostnet.orchestrator.containment_check import check_compose_config, check_runtime


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    compose = Path(__file__).resolve().parents[2] / "docker-compose.yml"
    if action == "up":
        failures = check_compose_config(compose)
        if failures:
            print("Refusing to start: " + ", ".join(failures))
            return 2
        runtime_failures = check_runtime(compose)
        if runtime_failures and not all(
            item.startswith("docker_runtime_unavailable") for item in runtime_failures
        ):
            print("Refusing to start: " + ", ".join(runtime_failures))
            return 2
        return subprocess.run(
            ["docker", "compose", "-f", str(compose), "up", "--build", "-d"], check=False
        ).returncode
    if action == "down":
        return subprocess.run(
            ["docker", "compose", "-f", str(compose), "down", "--remove-orphans"], check=False
        ).returncode
    print("Usage: python -m ghostnet.orchestrator.lifecycle [up|down]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
