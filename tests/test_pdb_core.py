from __future__ import annotations

from pdb_cli.core import build_parser


def test_request_parser_exposes_generated_operation_keys() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["request", "volume.cell", "--path", "source=x-ray", "--path", "id=4hhb"]
    )

    assert args.command == "request"
    assert args.operation == "volume.cell"
