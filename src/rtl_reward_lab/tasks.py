"""Load trusted task metadata and paths."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parents[2] / "tasks" / "manifest.json"


@dataclasses.dataclass(frozen=True)
class Task:
    """A single trusted evaluation task: its spec and reference artifacts."""

    id: str
    prompt_path: Path
    reference_path: Path
    test_path: Path


def load_tasks(manifest_path: str | Path = DEFAULT_MANIFEST_PATH) -> list[Task]:
    """Load task metadata from the manifest and resolve each entry's paths
    relative to the repository root.

    Raises FileNotFoundError if the manifest or any referenced file is
    missing: tasks are trusted inputs and must exist before any stage
    runs against them.
    """

    manifest_path = Path(manifest_path).resolve()
    repo_root = manifest_path.parents[1]
    data = json.loads(manifest_path.read_text())

    tasks = []
    for entry in data.get("tasks", []):
        prompt_path = repo_root / entry["prompt"]
        reference_path = repo_root / entry["reference"]
        test_path = repo_root / entry["test"]
        for path in (prompt_path, reference_path, test_path):
            if not path.is_file():
                raise FileNotFoundError(f"task {entry['id']!r} references missing file: {path}")
        tasks.append(
            Task(
                id=entry["id"],
                prompt_path=prompt_path,
                reference_path=reference_path,
                test_path=test_path,
            )
        )

    return tasks
