<div align="center">

# pdb-rcsb-cli

[![Release](https://img.shields.io/github/v/release/decent-tools-for-thought/pdb-rcsb-cli?sort=semver&color=0f766e)](https://github.com/decent-tools-for-thought/pdb-rcsb-cli/releases)
![Python](https://img.shields.io/badge/python-3.11%2B-0ea5e9)
![License](https://img.shields.io/badge/license-0BSD-14b8a6)

Command-line client for RCSB PDB documented operation calls, Search API requests, GraphQL queries, alignment jobs, offline docs, and optional local response caching.

</div>

> [!IMPORTANT]
> This codebase is entirely AI-generated. It is useful to me, I hope it might be useful to others, and issues and contributions are welcome.

## Map
- [Install](#install)
- [Functionality](#functionality)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Credits](#credits)

## Install
$$\color{#0EA5E9}Install \space \color{#14B8A6}Tool$$

```bash
uv tool install .   # install the CLI
pdb --help      # inspect the command surface
```

## Functionality
$$\color{#0EA5E9}Documented \space \color{#14B8A6}Calls$$
- `pdb request <operation>`: call any bundled documented operation by operation key.
- `pdb request --path NAME=VALUE --query NAME=VALUE --body-json ...`: fill path parameters, query parameters, and request bodies explicitly.
- The shipped operation catalog covers RCSB PDB data, search, model, volume, sequence, and alignment surfaces.

$$\color{#0EA5E9}Search \space \color{#14B8A6}GraphQL$$
- `pdb search --body-json ...`: run a Search API query.
- `pdb search --method GET|POST`: choose the GET or POST search transport explicitly.
- `pdb graphql data <query>`: run a Data API GraphQL request.
- `pdb graphql sequence <query>`: run a Sequence Coordinates GraphQL request.
- `pdb graphql --variables-json ...`: send GraphQL variables as JSON.

$$\color{#0EA5E9}Alignment \space \color{#14B8A6}Jobs$$
- `pdb alignment submit --body-json ...`: submit a structure-alignment job.
- `pdb alignment results <uuid>`: fetch alignment job status or results by UUID.

$$\color{#0EA5E9}Docs \space \color{#14B8A6}Inspect$$
- `pdb docs [selector]`: print LLM-friendly documentation for the supported RCSB endpoints.
- `pdb docs --format markdown|json`: emit either Markdown or machine-readable JSON.
- `pdb --decode auto|json|text|bytes`: choose response decoding behavior for request, search, GraphQL, and alignment commands.

$$\color{#0EA5E9}Cache \space \color{#14B8A6}Control$$
- `pdb cache stats`: show cache size and entry counts.
- `pdb cache prune --max-size-gb <n>`: evict older cache entries until the cache fits the target cap.
- `pdb cache clear`: remove all cached responses.

## Configuration
$$\color{#0EA5E9}Tune \space \color{#14B8A6}Defaults$$

By default the CLI uses the published RCSB PDB endpoints, leaves response caching disabled, and auto-decodes responses based on content type.

- Use `--decode json|text|bytes` when you want to override automatic response decoding.
- Use `--max-cache-size-gb` with a value greater than `0` to enable local caching.
- Use `--no-cache` or `--refresh` when you want live responses instead of cached ones.

The main environment variables are `PDB_CLI_CACHE_DIR`, `PDB_CLI_CACHE_MAX_BYTES`, `PDB_DATA_BASE_URL`, `PDB_SEARCH_BASE_URL`, `PDB_MODEL_BASE_URL`, `PDB_VOLUME_BASE_URL`, `PDB_SEQUENCE_BASE_URL`, `PDB_ALIGNMENT_BASE_URL`, and `XDG_CACHE_HOME`.

### Config File
$$\color{#0EA5E9}Set \space \color{#14B8A6}Defaults$$

The CLI reads optional defaults from `$XDG_CONFIG_HOME/pdb-rcsb-cli/config.toml`, falling back to `~/.config/pdb-rcsb-cli/config.toml`.

Start from `config/default-config.toml` in this repo. The shipped default keeps caching off:

```toml
[cache]
max_size_gb = 0.0
```

## Quick Start
$$\color{#0EA5E9}Try \space \color{#14B8A6}Browse$$

```bash
pdb request data.entry --path entry_id=4HHB                                         # fetch one entry
pdb request data.polymer-entity --path entry_id=4HHB --path entity_id=1             # fetch one polymer entity
pdb graphql data '{ entry(entry_id: "4HHB") { struct { title } } }'                 # run a GraphQL query
pdb search --body-json '{"query":{"type":"terminal","service":"text","parameters":{"operator":"exact_match","value":"hemoglobin"}},"return_type":"entry"}'
pdb alignment submit --body-json '{"query":{"context":"PDB","structures":[{"entry_id":"4HHB","selection":{"entity_id":"1"}},{"entry_id":"2HHB","selection":{"entity_id":"1"}}],"operator":"jFATCAT-rigid"}}'
pdb docs model --format json                                                        # inspect bundled docs
```

## Credits

This client is built for the RCSB PDB programmatic web APIs and is not affiliated with the RCSB PDB.

Credit goes to the RCSB PDB maintainers for the structural biology data platform, API surfaces, and documentation this tool builds on.
