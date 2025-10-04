from __future__ import annotations

import os
from typing import Any

from brand_name_gen.utils.env import load_env_from_dotenv, read_dotenv_value


def test_read_dotenv_value_and_load(monkeypatch: Any, tmp_path: Any) -> None:
    cwd = tmp_path
    dotenv = cwd / ".env"
    dotenv.write_text("FOO=bar\nBAZ='quoted'\n# comment\nEMPTY=\n", encoding="utf-8")

    # Change working directory to tmp
    monkeypatch.chdir(cwd)

    # read_dotenv_value does not mutate env
    assert read_dotenv_value("FOO") == "bar"
    assert read_dotenv_value("BAZ") == "quoted"
    assert read_dotenv_value("MISSING") is None

    # Ensure env is clean
    monkeypatch.delenv("FOO", raising=False)
    monkeypatch.delenv("BAZ", raising=False)

    # load_env_from_dotenv populates env without overriding existing values
    os.environ["FOO"] = "existing"
    load_env_from_dotenv()
    assert os.getenv("FOO") == "existing"  # unchanged
    assert os.getenv("BAZ") == "quoted"     # loaded

