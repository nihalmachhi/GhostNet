from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

CONTROLS = (
    "network_internal",
    "non_root",
    "not_privileged",
    "cap_drop_all",
    "read_only",
    "no_host_mounts",
    "pids_limit",
    "memory_limit",
    "cpu_limit",
    "no_new_privileges",
)


def _is_decoy(service: dict[str, Any]) -> bool:
    labels = service.get("labels", {})
    if isinstance(labels, list):
        labels = dict(item.split("=", 1) for item in labels if "=" in item)
    return labels.get("ghostnet.role") == "decoy"


def check_compose_config(path: str | Path) -> list[str]:
    """Return every failed safety control without starting any container."""
    compose = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    networks = compose.get("networks", {})
    failures: list[str] = []
    decoys = [
        (name, service)
        for name, service in compose.get("services", {}).items()
        if _is_decoy(service)
    ]
    if not decoys:
        return ["no_decoy_services_declared"]
    for name, service in decoys:
        service_networks = service.get("networks", {})
        service_networks = (
            service_networks.keys() if isinstance(service_networks, dict) else service_networks
        )
        if not service_networks or any(
            not networks.get(net, {}).get("internal", False) for net in service_networks
        ):
            failures.append(f"{name}:network_internal")
        user = str(service.get("user", "0")).split(":", 1)[0]
        if user in {"", "0", "root"}:
            failures.append(f"{name}:non_root")
        if service.get("privileged", False):
            failures.append(f"{name}:not_privileged")
        if "ALL" not in [str(cap).upper() for cap in service.get("cap_drop", [])]:
            failures.append(f"{name}:cap_drop_all")
        if not service.get("read_only", False):
            failures.append(f"{name}:read_only")
        for volume in service.get("volumes", []):
            source = (
                volume.get("source") if isinstance(volume, dict) else str(volume).split(":", 1)[0]
            )
            if source and (source.startswith("/") or ":\\" in source or source.startswith(".")):
                failures.append(f"{name}:no_host_mounts")
                break
        if (
            int(
                service.get("pids_limit")
                or service.get("deploy", {}).get("resources", {}).get("limits", {}).get("pids", 0)
                or 0
            )
            <= 0
        ):
            failures.append(f"{name}:pids_limit")
        limits = service.get("deploy", {}).get("resources", {}).get("limits", {})
        if not limits.get("memory"):
            failures.append(f"{name}:memory_limit")
        if not limits.get("cpus"):
            failures.append(f"{name}:cpu_limit")
        if not any(
            "no-new-privileges:true" in str(item).lower()
            for item in service.get("security_opt", [])
        ):
            failures.append(f"{name}:no_new_privileges")
        for port in service.get("ports", []):
            published = port.get("published") if isinstance(port, dict) else str(port).split(":")[0]
            host_ip = (
                port.get("host_ip", "")
                if isinstance(port, dict)
                else (str(port).split(":")[0] if str(port).count(":") >= 2 else "")
            )
            if published and host_ip not in {"127.0.0.1", "::1"}:
                failures.append(f"{name}:loopback_port_binding")
    return sorted(set(failures))


def check_runtime(compose_path: str | Path) -> list[str]:
    """Inspect running Compose decoys through Docker CLI's daemon API and fail closed."""
    command = ["docker", "compose", "-f", str(compose_path), "ps", "-q"]
    try:
        ids = subprocess.run(command, check=True, capture_output=True, text=True).stdout.split()
        if not ids:
            return []
        inspections = subprocess.run(
            ["docker", "inspect", *ids], check=True, capture_output=True, text=True
        )
        containers = json.loads(inspections.stdout) if ids else []
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        return [f"docker_runtime_unavailable:{type(exc).__name__}"]
    failures: list[str] = []
    for container in containers:
        labels = container.get("Config", {}).get("Labels", {})
        if labels.get("ghostnet.role") != "decoy":
            continue
        name = container.get("Name", "unknown").lstrip("/")
        config, host = container.get("Config", {}), container.get("HostConfig", {})
        checks = {
            "non_root": config.get("User") not in {"", "0", "root"},
            "not_privileged": not host.get("Privileged"),
            "cap_drop_all": "ALL" in (host.get("CapDrop") or []),
            "read_only": bool(host.get("ReadonlyRootfs")),
            "no_host_mounts": not any(m.get("Type") == "bind" for m in container.get("Mounts", [])),
            "pids_limit": host.get("PidsLimit", 0) > 0,
            "memory_limit": host.get("Memory", 0) > 0,
            "cpu_limit": host.get("NanoCpus", 0) > 0,
        }
        for control, passed in checks.items():
            if not passed:
                failures.append(f"{name}:{control}")
        for binding in (host.get("PortBindings") or {}).values():
            for published in binding or []:
                if published.get("HostIp") not in {"127.0.0.1", "::1"}:
                    failures.append(f"{name}:loopback_port_binding")
        for network_name in container.get("NetworkSettings", {}).get("Networks", {}):
            result = subprocess.run(
                ["docker", "network", "inspect", network_name], capture_output=True, text=True
            )
            try:
                internal = json.loads(result.stdout)[0].get("Internal", False)
            except (json.JSONDecodeError, IndexError):
                internal = False
            if not internal:
                failures.append(f"{name}:network_internal")
    return sorted(set(failures))


def main() -> int:
    compose_path = Path(__file__).resolve().parents[2] / "docker-compose.yml"
    failures = check_compose_config(compose_path) + check_runtime(compose_path)
    if failures:
        print("Containment FAILED:")
        print("\n".join(f"- {failure}" for failure in sorted(set(failures))))
        return 1
    print("Containment checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
