from __future__ import annotations

import json

import httpx

from pdb_cli.client import PdbClient


def test_request_renders_data_entry_path_and_parses_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/rest/v1/core/entry/4HHB"
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"entry": {"id": "4HHB"}},
        )

    transport = httpx.MockTransport(handler)
    with PdbClient(transport=transport) as client:
        response = client.request("data.entry", path_params={"entry_id": "4HHB"})

    assert response.json()["entry"]["id"] == "4HHB"


def test_search_post_submits_json_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/rcsbsearch/v2/query"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["return_type"] == "entry"
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"total_count": 1},
        )

    transport = httpx.MockTransport(handler)
    with PdbClient(transport=transport) as client:
        response = client.request(
            "search.query-post",
            body={
                "query": {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {"value": "hemoglobin"},
                },
                "return_type": "entry",
            },
        )

    assert response.json()["total_count"] == 1


def test_graphql_posts_query_document() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/graphql"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["query"].startswith("{ entry")
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"data": {"entry": {"rcsb_id": "4HHB"}}},
        )

    transport = httpx.MockTransport(handler)
    with PdbClient(transport=transport) as client:
        response = client.request(
            "data.graphql", body={"query": '{ entry(entry_id:"4HHB"){ rcsb_id } }'}
        )

    assert response.json()["data"]["entry"]["rcsb_id"] == "4HHB"
