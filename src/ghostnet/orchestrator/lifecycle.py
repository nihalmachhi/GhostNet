from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from ghostnet.orchestrator.containment_check import check_compose_config, check_runtime


def _compose(compose: Path, *args: str) -> int:
    return subprocess.run(["docker", "compose", "-f", str(compose), *args], check=False).returncode


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    compose = Path(__file__).resolve().parents[3] / "docker-compose.yml"
    if action == "up":
        failures = check_compose_config(compose)
        if failures:
            print("Refusing to start: " + ", ".join(failures))
            return 2
        code = _compose(compose, "up", "--build", "-d")
        if code:
            return code
        time.sleep(3)
        runtime_failures = check_runtime(compose)
        if runtime_failures and not all(
            item.startswith("docker_runtime_unavailable") for item in runtime_failures
        ):
            print("Runtime containment failed; stopping the stack: " + ", ".join(runtime_failures))
            _compose(compose, "down", "--remove-orphans")
            return 3
        return 0
    if action == "down":
        return _compose(compose, "down", "--remove-orphans")
    print("Usage: python -m ghostnet.orchestrator.lifecycle [up|down]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
