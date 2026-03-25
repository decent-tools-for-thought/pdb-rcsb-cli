from __future__ import annotations

import json

from pdb_cli.docs import render_docs


def test_render_docs_json_for_model_service() -> None:
    payload = json.loads(render_docs("model", "json"))

    assert payload["kind"] == "pdb_cli_endpoint_docs"
    assert payload["observed_on"] == "2026-03-24"
    assert payload["selector"] == "model"
    assert any(item["operation_key"] == "model.full" for item in payload["endpoints"])


def test_render_docs_markdown_mentions_sequence_semantics() -> None:
    rendered = render_docs("sequence", "markdown")

    assert "# PDB CLI Endpoint Documentation" in rendered
    assert "## Endpoint: sequence.graphql" in rendered
    assert "alignment` and `annotations`" in rendered
