from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from .cache import ResponseCache, default_response_cache
from .metadata import base_url_for_service, endpoint_docs

QueryParamValue = str | int | float | bool | None

DEFAULT_TIMEOUT_SECONDS = 30.0


class PdbCliError(Exception):
    pass


@dataclass(frozen=True)
class PdbResponse:
    status_code: int
    url: str
    content_type: str
    body: Any
    cached: bool

    def json(self) -> Any:
        if not isinstance(self.body, (dict, list)):
            raise TypeError("response body is not JSON")
        return self.body

    def text(self) -> str:
        if isinstance(self.body, bytes):
            return self.body.decode("utf-8")
        if isinstance(self.body, str):
            return self.body
        return json.dumps(self.body, indent=2, sort_keys=True)


class PdbClient:
    def __init__(
        self,
        *,
        cache: ResponseCache | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        cache_ttl_seconds: float | None = None,
    ) -> None:
        self.cache = cache or default_response_cache()
        self.cache_ttl_seconds = cache_ttl_seconds
        self._http = httpx.Client(timeout=timeout_seconds, transport=transport)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> PdbClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def request(
        self,
        operation_key: str,
        *,
        path_params: Mapping[str, str] | None = None,
        query_params: Mapping[str, QueryParamValue] | None = None,
        body: Any = None,
        use_cache: bool = True,
        refresh: bool = False,
        decode: str = "auto",
    ) -> PdbResponse:
        operation = _resolve_operation(operation_key)
        base_url = base_url_for_service(operation.service)
        path = _render_path(operation.path, path_params or {})
        params = {
            key: value for key, value in dict(query_params or {}).items() if value is not None
        }
        url = f"{base_url}{path}"
        cache_key = self.cache.make_key(
            {
                "method": operation.method,
                "url": url,
                "params": params,
                "body": body,
            }
        )
        if use_cache and not refresh:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return _decode_response(
                    url=url,
                    status_code=200,
                    content_type=_content_type_from_cached_bytes(cached),
                    payload=cached,
                    decode=decode,
                    cached=True,
                )

        response = self._http.request(
            operation.method,
            url,
            params=params,
            json=body if body is not None else None,
        )
        if response.status_code >= 400:
            raise PdbCliError(
                f"{operation.method} {url} failed with {response.status_code}: {response.text}"
            )
        payload = _serialize_response(response)
        if use_cache:
            self.cache.set(cache_key, payload, ttl_seconds=self.cache_ttl_seconds)
        return _decode_response(
            url=str(response.url),
            status_code=response.status_code,
            content_type=response.headers.get("content-type", "application/octet-stream"),
            payload=payload,
            decode=decode,
            cached=False,
        )


def _resolve_operation(operation_key: str) -> Any:
    for endpoint in endpoint_docs():
        if endpoint.operation_key == operation_key:
            return endpoint
    raise PdbCliError(f"unknown operation key: {operation_key}")


def _render_path(path_template: str, path_params: Mapping[str, str]) -> str:
    expected = set(re.findall(r"{([^}]+)}", path_template))
    missing = sorted(expected - set(path_params))
    if missing:
        raise PdbCliError(f"missing path parameters: {', '.join(missing)}")
    path = path_template
    for name in expected:
        path = path.replace(f"{{{name}}}", quote(str(path_params[name]), safe=","))
    return path


def _serialize_response(response: httpx.Response) -> bytes:
    content_type = response.headers.get("content-type", "")
    meta = {"content_type": content_type, "body": response.content.decode("latin1")}
    return json.dumps(meta, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _content_type_from_cached_bytes(payload: bytes) -> str:
    decoded = json.loads(payload.decode("utf-8"))
    return str(decoded["content_type"])


def _decode_response(
    *,
    url: str,
    status_code: int,
    content_type: str,
    payload: bytes,
    decode: str,
    cached: bool,
) -> PdbResponse:
    decoded = json.loads(payload.decode("utf-8"))
    raw = decoded["body"].encode("latin1")
    body: Any
    effective_decode = decode
    if effective_decode == "auto":
        if "json" in content_type:
            effective_decode = "json"
        elif content_type.startswith("text/") or "cif" in content_type:
            effective_decode = "text"
        else:
            effective_decode = "bytes"
    if effective_decode == "json":
        body = json.loads(raw.decode("utf-8"))
    elif effective_decode == "text":
        body = raw.decode("utf-8")
    elif effective_decode == "bytes":
        body = raw
    else:
        raise PdbCliError(f"unsupported decode mode: {decode}")
    return PdbResponse(
        status_code=status_code,
        url=url,
        content_type=content_type,
        body=body,
        cached=cached,
    )
