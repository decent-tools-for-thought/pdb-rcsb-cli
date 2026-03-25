from __future__ import annotations

import json
from typing import Any

from .metadata import OBSERVED_ON, SERVICE_SEMANTICS, collection_summary, filter_endpoint_docs


def render_docs(selector: str, output_format: str) -> str:
    payload = _docs_payload(selector)
    if output_format == "json":
        return json.dumps(payload, indent=2, sort_keys=True)
    return _render_markdown(payload)


def _docs_payload(selector: str) -> dict[str, Any]:
    endpoints = filter_endpoint_docs(selector)
    return {
        "kind": "pdb_cli_endpoint_docs",
        "observed_on": OBSERVED_ON,
        "selector": selector,
        "services": collection_summary(),
        "semantic_model": SERVICE_SEMANTICS,
        "endpoints": [item.to_dict() for item in endpoints],
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# PDB CLI Endpoint Documentation",
        "",
        f"- observed_on: {payload['observed_on']}",
        f"- selector: {payload['selector']}",
        f"- endpoint_count: {len(payload['endpoints'])}",
        "",
        "## Services",
        "",
    ]
    for service in payload["services"]:
        lines.extend(
            [
                f"### {service['name']}",
                "",
                f"- base_url: {service['base_url']}",
                f"- source_url: {service['source_url']}",
                f"- semantic_scope: {service['semantic_scope']}",
                "",
            ]
        )
    for endpoint in payload["endpoints"]:
        lines.extend(
            [
                f"## Endpoint: {endpoint['operation_key']}",
                "",
                f"- service: {endpoint['service']}",
                f"- method: {endpoint['method']}",
                f"- base_url: {endpoint['base_url']}",
                f"- path: {endpoint['path']}",
                f"- semantic_kind: {endpoint['semantic_kind']}",
                f"- semantic_summary: {endpoint['semantic_summary']}",
                f"- summary: {endpoint['summary']}",
                f"- source_url: {endpoint['source_url']}",
                "",
                "### Parameters",
                "",
            ]
        )
        if endpoint["path_parameters"]:
            lines.append("Path parameters:")
            for parameter in endpoint["path_parameters"]:
                lines.append(
                    f"- {parameter['name']}: required={str(parameter['required']).lower()}; "
                    f"type={parameter['schema_type']}; description={parameter['description']}"
                )
        else:
            lines.append("Path parameters: none")
        if endpoint["query_parameters"]:
            lines.append("")
            lines.append("Query parameters:")
            for parameter in endpoint["query_parameters"]:
                lines.append(
                    f"- {parameter['name']}: required={str(parameter['required']).lower()}; "
                    f"type={parameter['schema_type']}; description={parameter['description']}"
                )
        else:
            lines.append("")
            lines.append("Query parameters: none")
        lines.extend(
            [
                "",
                "### Payloads",
                "",
                (
                    "- request_body: "
                    f"required={str(endpoint['request_body_required']).lower()}; "
                    f"content_types={', '.join(endpoint['request_body_content_types']) or 'none'}"
                ),
                (
                    "- response_content_types: "
                    f"{', '.join(endpoint['response_content_types']) or 'unknown'}"
                ),
            ]
        )
        notes = endpoint["notes"]
        lines.extend(["", "### Notes", ""])
        if notes:
            for note in notes:
                lines.append(f"- {note}")
        else:
            lines.append("- none")
        lines.append("")
    return "\n".join(lines)
