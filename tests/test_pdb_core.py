from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdb_cli.core import build_parser, main


def test_request_parser_exposes_generated_operation_keys() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["request", "volume.cell", "--path", "source=x-ray", "--path", "id=4hhb"]
    )

    assert args.command == "request"
    assert args.operation == "volume.cell"


def test_parser_reads_cache_defaults_from_xdg_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_path = tmp_path / "pdb-cli" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '[cache]\nmax_size_gb = 0.75\ndir = "/tmp/pdb-cache"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    args = build_parser().parse_args(
        ["request", "volume.cell", "--path", "source=x-ray", "--path", "id=4hhb"]
    )

    assert args.max_cache_size_gb == 0.75
    assert args.cache_dir == Path("/tmp/pdb-cache")


def test_main_skips_disk_cache_when_default_cache_is_disabled(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class StubClient:
        def __enter__(self) -> StubClient:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def request(self, *_: object, **__: object) -> object:
            return type("Response", (), {"body": {"entry": "4HHB"}})()

    def fail_disk_cache(*_: object, **__: object) -> object:
        raise AssertionError("DiskLRUCache should not be created when cache is disabled")

    monkeypatch.setattr("pdb_cli.core.PdbClient", lambda **_: StubClient())
    monkeypatch.setattr("pdb_cli.core.DiskLRUCache", fail_disk_cache)

    code = main(["request", "data.entry", "--path", "entry_id=4HHB"])

    assert code == 0
    assert json.loads(capsys.readouterr().out) == {"entry": "4HHB"}
