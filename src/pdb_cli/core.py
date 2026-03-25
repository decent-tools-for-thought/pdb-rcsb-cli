from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .cache import CacheSettings, DiskLRUCache, create_response_cache, load_cache_settings
from .client import PdbClient, PdbCliError
from .docs import render_docs
from .metadata import available_operation_keys


def build_parser(cache_settings: CacheSettings | None = None) -> argparse.ArgumentParser:
    settings = load_cache_settings() if cache_settings is None else cache_settings
    parser = argparse.ArgumentParser(prog="pdb-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    request_parser = subparsers.add_parser("request", help="Call a documented operation by key")
    request_parser.add_argument("operation", choices=sorted(available_operation_keys()))
    request_parser.add_argument("--path", action="append", default=[], metavar="NAME=VALUE")
    request_parser.add_argument("--query", action="append", default=[], metavar="NAME=VALUE")
    request_parser.add_argument("--body-json", default=None)
    _add_runtime_args(request_parser, settings)
    request_parser.add_argument(
        "--decode", choices=["auto", "json", "text", "bytes"], default="auto"
    )

    search_parser = subparsers.add_parser("search", help="Run a Search API query")
    search_parser.add_argument("--body-json", required=True)
    search_parser.add_argument("--method", choices=["GET", "POST"], default="POST")
    _add_runtime_args(search_parser, settings)
    search_parser.add_argument(
        "--decode", choices=["auto", "json", "text", "bytes"], default="auto"
    )

    graphql_parser = subparsers.add_parser("graphql", help="Run a GraphQL request")
    graphql_parser.add_argument("service", choices=["data", "sequence"])
    graphql_parser.add_argument("query")
    graphql_parser.add_argument("--variables-json", default=None)
    _add_runtime_args(graphql_parser, settings)
    graphql_parser.add_argument(
        "--decode", choices=["auto", "json", "text", "bytes"], default="json"
    )

    alignment_parser = subparsers.add_parser("alignment", help="Work with the alignment API")
    alignment_subparsers = alignment_parser.add_subparsers(dest="alignment_command", required=True)

    alignment_submit = alignment_subparsers.add_parser("submit", help="Submit an alignment job")
    alignment_submit.add_argument("--body-json", required=True)
    _add_runtime_args(alignment_submit, settings)
    alignment_submit.add_argument(
        "--decode", choices=["auto", "json", "text", "bytes"], default="json"
    )

    alignment_results = alignment_subparsers.add_parser(
        "results", help="Fetch alignment job status/results"
    )
    alignment_results.add_argument("uuid")
    _add_runtime_args(alignment_results, settings)
    alignment_results.add_argument(
        "--decode", choices=["auto", "json", "text", "bytes"], default="json"
    )

    docs_parser = subparsers.add_parser(
        "docs",
        help="Show LLM-friendly documentation for the supported RCSB endpoints",
    )
    docs_parser.add_argument("selector", nargs="?", default="all")
    docs_parser.add_argument(
        "--format", dest="output_format", choices=["markdown", "json"], default="markdown"
    )

    cache_parser = subparsers.add_parser("cache", help="Manage the local response cache")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command", required=True)

    cache_stats = cache_subparsers.add_parser("stats", help="Show cache statistics")
    _add_cache_only_args(cache_stats, settings)

    cache_prune = cache_subparsers.add_parser("prune", help="Evict old cache entries")
    _add_cache_only_args(cache_prune, settings)

    cache_clear = cache_subparsers.add_parser("clear", help="Delete all cache entries")
    _add_cache_only_args(cache_clear, settings)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        cache_settings = load_cache_settings()
    except ValueError as error:
        sys.stderr.write(f"error: {error}\n")
        return 2

    parser = build_parser(cache_settings)
    args = parser.parse_args(argv)
    try:
        if args.command == "docs":
            return _run_docs(args)
        if args.command == "cache":
            return _run_cache(args)
        return _run_remote(args)
    except PdbCliError as error:
        parser.exit(status=2, message=f"error: {error}\n")
    return 0


def _run_remote(args: argparse.Namespace) -> int:
    max_bytes = _gigabytes_to_bytes(args.max_cache_size_gb)
    cache = create_response_cache(root=args.cache_dir, max_bytes=max_bytes)
    with PdbClient(cache=cache) as client:
        use_cache = not args.no_cache and max_bytes > 0
        refresh = args.refresh
        decode = getattr(args, "decode", "auto")
        if args.command == "request":
            response = client.request(
                args.operation,
                path_params=_parse_assignments(args.path),
                query_params=_parse_assignments(args.query),
                body=None if args.body_json is None else json.loads(args.body_json),
                use_cache=use_cache,
                refresh=refresh,
                decode=decode,
            )
        elif args.command == "search":
            if args.method == "GET":
                response = client.request(
                    "search.query-get",
                    query_params={"json": args.body_json},
                    use_cache=use_cache,
                    refresh=refresh,
                    decode=decode,
                )
            else:
                response = client.request(
                    "search.query-post",
                    body=json.loads(args.body_json),
                    use_cache=use_cache,
                    refresh=refresh,
                    decode=decode,
                )
        elif args.command == "graphql":
            response = client.request(
                f"{args.service}.graphql",
                body={
                    "query": args.query,
                    **(
                        {}
                        if args.variables_json is None
                        else {"variables": json.loads(args.variables_json)}
                    ),
                },
                use_cache=use_cache,
                refresh=refresh,
                decode=decode,
            )
        elif args.command == "alignment":
            if args.alignment_command == "submit":
                response = client.request(
                    "alignment.submit-post",
                    body=json.loads(args.body_json),
                    use_cache=use_cache,
                    refresh=refresh,
                    decode=decode,
                )
            elif args.alignment_command == "results":
                response = client.request(
                    "alignment.results",
                    query_params={"uuid": args.uuid},
                    use_cache=use_cache,
                    refresh=refresh,
                    decode=decode,
                )
            else:
                raise PdbCliError(f"unsupported alignment command: {args.alignment_command}")
        else:
            raise PdbCliError(f"unsupported command: {args.command}")
    _write_response(response)
    return 0


def _run_cache(args: argparse.Namespace) -> int:
    max_bytes = _gigabytes_to_bytes(args.max_size_gb)
    cache = DiskLRUCache(root=args.cache_dir, max_bytes=max_bytes)
    if args.cache_command == "stats":
        stats = cache.stats()
    elif args.cache_command == "prune":
        stats = cache.prune()
    elif args.cache_command == "clear":
        cache.clear()
        stats = cache.stats()
    else:
        raise PdbCliError(f"unsupported cache command: {args.cache_command}")
    print(
        json.dumps(
            {
                "cache_dir": str(args.cache_dir),
                "entries": stats.entries,
                "total_bytes": stats.total_bytes,
                "max_bytes": stats.max_bytes,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _run_docs(args: argparse.Namespace) -> int:
    print(render_docs(args.selector, args.output_format), end="")
    if args.output_format != "markdown":
        print()
    return 0


def _add_runtime_args(parser: argparse.ArgumentParser, settings: CacheSettings) -> None:
    parser.add_argument("--cache-dir", type=Path, default=settings.cache_dir)
    parser.add_argument(
        "--max-cache-size-gb",
        type=float,
        default=settings.max_size_gb,
    )
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--refresh", action="store_true")


def _add_cache_only_args(parser: argparse.ArgumentParser, settings: CacheSettings) -> None:
    parser.add_argument("--cache-dir", type=Path, default=settings.cache_dir)
    parser.add_argument(
        "--max-size-gb",
        type=float,
        default=settings.max_size_gb,
    )


def _parse_assignments(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise PdbCliError(f"expected NAME=VALUE, got: {value}")
        key, raw = value.split("=", 1)
        parsed[key] = raw
    return parsed


def _write_response(response: Any) -> None:
    body = response.body
    if isinstance(body, bytes):
        sys.stdout.buffer.write(body)
        return
    if isinstance(body, str):
        print(body)
        return
    print(json.dumps(body, indent=2, sort_keys=True))


def _gigabytes_to_bytes(size_gb: float) -> int:
    if size_gb < 0:
        raise PdbCliError("cache size must be non-negative")
    return int(size_gb * 1024**3)
