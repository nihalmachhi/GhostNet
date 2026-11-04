from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ghostnet.core.settings import Settings
from ghostnet.export.csvout import sessions_csv
from ghostnet.export.navigator import navigator_layer
from ghostnet.export.stix import stix_bundle
from ghostnet.pipeline.actors import link_actors
from ghostnet.pipeline.attack_map import map_behavior
from ghostnet.pipeline.sessions import build_sessions
from ghostnet.storage.db import EventStore


def _sessions(store: EventStore) -> list[dict[str, Any]]:
    rows = build_sessions(store.all_events())
    for row in rows:
        row["attack"] = map_behavior(str(row["class_label"]))
    link_actors(rows)
    for row in rows:
        row.pop("events", None)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(prog="ghostnet", description="GhostNet local operations")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("export-checkpoint", "export-navigator", "export-stix", "export-csv", "purge"):
        command = sub.add_parser(name)
        command.add_argument("--database", default="data/ghostnet.sqlite3")
        command.add_argument("--out", default="")
    args = parser.parse_args()
    settings = Settings()
    store = EventStore(args.database, settings.chain_key)
    if args.command == "export-checkpoint":
        payload = store.verify_integrity()["checkpoint"]
    elif args.command == "export-navigator":
        payload = navigator_layer(_sessions(store))
    elif args.command == "export-stix":
        payload = stix_bundle(_sessions(store))
    elif args.command == "export-csv":
        text = sessions_csv(_sessions(store))
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        else:
            print(text)
        return 0
    else:
        print(f"purged {store.purge_old(settings.retention_days)} events")
        return 0
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
