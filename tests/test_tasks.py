import json

import pytest

from rtl_reward_lab.tasks import load_tasks


def test_default_manifest_loads_popcount3():
    tasks = load_tasks()

    assert [t.id for t in tasks] == ["popcount3"]
    task = tasks[0]
    assert task.prompt_path.is_file()
    assert task.reference_path.is_file()
    assert task.test_path.is_file()


def test_missing_referenced_file_raises(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "ghost",
                        "prompt": "does/not/exist_prompt.txt",
                        "reference": "does/not/exist_ref.sv",
                        "test": "does/not/exist_test.sv",
                    }
                ]
            }
        )
    )

    with pytest.raises(FileNotFoundError):
        load_tasks(manifest)


def test_empty_manifest_loads_no_tasks(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}")

    assert load_tasks(manifest) == []
